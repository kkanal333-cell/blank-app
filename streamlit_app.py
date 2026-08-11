import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# 페이지 기본 설정 (모바일/태블릿 반응형)
st.set_page_config(page_title="꽃집 고객/주문 관리 시스템", page_icon="💐", layout="wide")

# DB 연결 및 테이블 생성 함수
def init_db():
    conn = sqlite3.connect('flower_shop.db', check_same_thread=False)
    c = conn.cursor()
    
    # 고객 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            anniversary TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 주문 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product TEXT NOT NULL,
            price INTEGER DEFAULT 0,
            pickup_datetime TEXT NOT NULL,
            status TEXT DEFAULT '예약완료',
            notified_1day INTEGER DEFAULT 0,
            notified_1hour INTEGER DEFAULT 0,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# 메인 타이틀
st.title("💐 Flower Shop CRM & 픽업 알림")

# 사이드바 메뉴
menu = st.sidebar.radio("메뉴 선택", ["📝 신규 주문 등록", "📅 픽업 일정 확인", "👥 고객 DB & 마케팅", "🔔 알림 발송 현황"])

# 1. 신규 주문 등록
if menu == "📝 신규 주문 등록":
    st.subheader("📝 신규 주문 및 고객 등록")
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("고객 이름 *")
        phone = st.text_input("휴대폰 번호 (예: 010-1234-5678) *")
        anniversary = st.date_input("주요 기념일 (선택)", value=None)
        customer_notes = st.text_area("고객 메모 (선호하는 꽃/색상 등)")
        
    with col2:
        product = st.text_input("주문 상품명 (예: 생일 축하 꽃다발) *")
        price = st.number_input("결제 금액 (원)", step=1000, value=50000)
        pickup_date = st.date_input("픽업 날짜 *", value=datetime.today())
        pickup_time = st.time_input("픽업 시간 *", value=datetime.now().time())
        
    if st.button("주문 저장하기", type="primary"):
        if not name or not phone or not product:
            st.error("이름, 휴대폰 번호, 주문 상품명은 필수 입력 항목입니다.")
        else:
            c = conn.cursor()
            # 고객 정보 존재 여부 확인
            c.execute("SELECT id FROM customers WHERE phone = ?", (phone,))
            customer = c.fetchone()
            
            anniversary_str = anniversary.strftime("%m-%d") if anniversary else ""
            
            if not customer:
                c.execute("INSERT INTO customers (name, phone, anniversary, notes) VALUES (?, ?, ?, ?)",
                          (name, phone, anniversary_str, customer_notes))
                customer_id = c.lastrowid
            else:
                customer_id = customer[0]
                if customer_notes:
                    c.execute("UPDATE customers SET notes = ? WHERE id = ?", (customer_notes, customer_id))
            
            # 주문 정보 등록
            pickup_datetime_str = f"{pickup_date} {pickup_time.strftime('%H:%M:%S')}"
            c.execute("INSERT INTO orders (customer_id, product, price, pickup_datetime) VALUES (?, ?, ?, ?)",
                      (customer_id, product, price, pickup_datetime_str))
            
            conn.commit()
            st.success(f"✅ {name}님의 주문이 성공적으로 등록되었습니다!")

# 2. 픽업 일정 확인
elif menu == "📅 픽업 일정 확인":
    st.subheader("📅 픽업 일정 조회")
    
    selected_date = st.date_input("조회할 날짜 선택", value=datetime.today())
    date_str = selected_date.strftime("%Y-%m-%d")
    
    df = pd.read_sql_query(f'''
        SELECT o.id as 주문번호, c.name as 고객명, c.phone as 연락처, o.product as 상품명, 
               o.price as 금액, TIME(o.pickup_datetime) as 픽업시간, o.status as 상태
        FROM orders o JOIN customers c ON o.customer_id = c.id
        WHERE DATE(o.pickup_datetime) = '{date_str}'
        ORDER BY o.pickup_datetime ASC
    ''', conn)
    
    if len(df) > 0:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("해당 날짜에 예정된 픽업 건이 없습니다.")

# 3. 고객 DB & 마케팅
elif menu == "👥 고객 DB & 마케팅":
    st.subheader("👥 고객 정보 및 과거 구매 이력")
    
    search_query = st.text_input("고객 이름 또는 전화번호 검색")
    
    if search_query:
        customers_df = pd.read_sql_query(f'''
            SELECT id, name as 이름, phone as 연락처, anniversary as 기념일, notes as 메모, created_at as 등록일
            FROM customers
            WHERE name LIKE '%{search_query}%' OR phone LIKE '%{search_query}%'
        ''', conn)
        
        st.write("🔍 검색 결과:")
        st.dataframe(customers_df, use_container_width=True)
        
        if len(customers_df) > 0:
            selected_cust_id = customers_df.iloc[0]['id']
            st.markdown("---")
            st.subheader(f"📦 {customers_df.iloc[0]['이름']} 님의 과거 주문 내역")
            orders_history = pd.read_sql_query(f'''
                SELECT product as 상품명, price as 금액, pickup_datetime as 픽업일시, status as 상태
                FROM orders WHERE customer_id = {selected_cust_id}
                ORDER BY pickup_datetime DESC
            ''', conn)
            st.dataframe(orders_history, use_container_width=True)
    else:
        # 전체 고객 목록 및 다가오는 기념일 조회
        st.subheader("🎉 이번 달 기념일이 있는 고객 목록")
        today_month = datetime.now().strftime("%m")
        anniversary_df = pd.read_sql_query(f'''
            SELECT name as 이름, phone as 연락처, anniversary as 기념일, notes as 메모
            FROM customers WHERE anniversary LIKE '{today_month}-%'
        ''', conn)
        
        if len(anniversary_df) > 0:
            st.dataframe(anniversary_df, use_container_width=True)
            st.caption("💡 이 고객분들께 단체 할인/기념일 안내 문자를 보내 마케팅을 진행할 수 있습니다.")
        else:
            st.write("이번 달 기념일 등록 고객이 없습니다.")

# 4. 알림 발송 현황 (픽업 1일 전 / 1시간 전)
elif menu == "🔔 알림 발송 현황":
    st.subheader("🔔 자동 발송 예정 알림 대상")
    
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    
    st.markdown("##### 📌 24시간 이내 픽업 예정 (1일 전 알림 대상)")
    df_1day = pd.read_sql_query(f'''
        SELECT o.id, c.name as 고객명, c.phone as 연락처, o.product as 상품명, o.pickup_datetime as 픽업일시
        FROM orders o JOIN customers c ON o.customer_id = c.id
        WHERE o.notified_1day = 0 AND o.pickup_datetime BETWEEN '{now.strftime("%Y-%m-%d %H:%M:%S")}' AND '{tomorrow.strftime("%Y-%m-%d %H:%M:%S")}'
    ''', conn)
    
    st.dataframe(df_1day, use_container_width=True)