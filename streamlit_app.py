import calendar
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="꽃집 고객/주문 관리 시스템", page_icon="💐", layout="wide"
)


# DB 연결 및 테이블 생성 함수
def init_db():
    conn = sqlite3.connect("flower_shop.db", check_same_thread=False)
    c = conn.cursor()

    # 고객 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            anniversary TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 주문 테이블
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product_name TEXT NOT NULL,
            amount INTEGER NOT NULL,
            pickup_datetime TEXT NOT NULL,
            status TEXT DEFAULT '접수',
            notified_1day INTEGER DEFAULT 0,
            notified_1hour INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    """)
    conn.commit()
    return conn


conn = init_db()

st.title("💐 Flower Shop CRM & 픽업 알림")

# 사이드바 메뉴
menu = st.sidebar.selectbox(
    "메뉴 선택",
    [
        "📝 신규 주문 및 고객 등록",
        "📅 픽업 일정 확인 (달력)",
        "🎉 기념일 고객 관리",
        "🔔 알림 발송 현황",
    ],
)

# 1. 신규 주문 및 고객 등록
if menu == "📝 신규 주문 및 고객 등록":
    st.subheader("📝 신규 주문 및 고객 등록")

    with st.form("order_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("고객 이름 *")
            phone = st.text_input("휴대폰 번호 (예: 010-1234-5678) *")
            anniversary = st.text_input("주요 기념일 (선택, 예: 05-08 어버이날)")

        with col2:
            product_name = st.text_input(
                "주문 상품명 (예: 생일 축하 꽃다발) *"
            )
            amount = st.number_input("결제 금액 (원)", step=10000, value=50000)
            pickup_date = st.date_input("픽업 날짜 *")
            pickup_time = st.time_input("픽업 시간 *")

        notes = st.text_area("고객 특이사항 / 메모")
        submitted = st.form_submit_button("주문 저장하기")

        if submitted:
            if not name or not phone or not product_name:
                st.error("이름, 휴대폰 번호, 상품명은 필수 입력 항목입니다.")
            else:
                c = conn.cursor()
                # 고객 정보 저장 (기존 고객이면 ID만 가져옴)
                c.execute(
                    "INSERT OR IGNORE INTO customers (name, phone, anniversary, notes) VALUES (?, ?, ?, ?)",
                    (name, phone, anniversary, notes),
                )
                c.execute(
                    "SELECT id FROM customers WHERE phone = ?", (phone,)
                )
                customer_id = c.fetchone()[0]

                # 주문 정보 저장
                pickup_datetime_str = (
                    f"{pickup_date} {pickup_time.strftime('%H:%M:%S')}"
                )
                c.execute(
                    "INSERT INTO orders (customer_id, product_name, amount, pickup_datetime) VALUES (?, ?, ?, ?)",
                    (customer_id, product_name, amount, pickup_datetime_str),
                )
                conn.commit()
                st.success(
                    f"[{name}] 님의 주문이 성공적으로 등록되었습니다!"
                )

# 2. 픽업 일정 확인 (월간 달력 UI)
elif menu == "📅 픽업 일정 확인 (달력)":
    st.subheader("📅 월간 픽업 달력")

    # 월 선택
    today = datetime.now()
    col_y, col_m = st.columns(2)
    with col_y:
        year = st.number_input(
            "연도", min_value=2024, max_value=2030, value=today.year
        )
    with col_m:
        month = st.number_input(
            "월", min_value=1, max_value=12, value=today.month
        )

    # 해당 월의 주문 데이터 조회
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day} 23:59:59"

    df_month = pd.read_sql_query(
        f"""
        SELECT o.id, c.name as 고객명, c.phone as 연락처, o.product_name as 상품명, 
               o.amount as 금액, o.pickup_datetime as 픽업일시, o.status as 상태
        FROM orders o JOIN customers c ON o.customer_id = c.id
        WHERE o.pickup_datetime BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY o.pickup_datetime ASC
    """,
        conn,
    )

    # 일별 건수 집계
    if not df_month.empty:
        df_month["날짜"] = pd.to_datetime(df_month["픽업일시"]).dt.date
        counts_by_date = (
            df_month.groupby("날짜").size().to_dict()
        )
    else:
        counts_by_date = {}

    st.write("---")

    # 주 단위 달력 렌더링
    cal = calendar.Calendar(firstweekday=6)  # 일요일 시작
    month_days = cal.monthdatescalendar(year, month)

    cols_header = st.columns(7)
    days_name = ["일", "월", "화", "수", "목", "금", "토"]
    for idx, day_name in enumerate(days_name):
        cols_header[idx].markdown(
            f"<h4 style='text-align: center;'>{day_name}</h4>",
            unsafe_allow_html=True,
        )

    # 세션 상태로 클릭한 날짜 관리
    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = today.date()

    for week in month_days:
        cols = st.columns(7)
        for idx, day in enumerate(week):
            if day.month == month:
                count = counts_by_date.get(day, 0)
                label = f"{day.day}일"
                if count > 0:
                    label += f" ({count}건)"

                # 버튼 클릭 시 해당 날짜 선택
                if cols[idx].button(
                    label,
                    key=str(day),
                    type="primary" if count > 0 else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["selected_date"] = day
            else:
                cols[idx].write("")

    st.write("---")

    # 선택된 날짜 상세 목록 출력
    selected_date = st.session_state["selected_date"]
    st.markdown(f"### 📋 {selected_date.strftime('%Y년 %m월 %d일')} 픽업 리스트")

    df_selected = df_month[df_month["날짜"] == selected_date] if not df_month.empty else pd.DataFrame()

    if not df_selected.empty:
        st.dataframe(
            df_selected[
                ["픽업일시", "고객명", "연락처", "상품명", "금액", "상태"]
            ],
            use_container_width=True,
        )
    else:
        st.info("해당 날짜에 예정된 픽업 건이 없습니다.")

# 3. 기념일 고객 관리
elif menu == "🎉 기념일 고객 관리":
    st.subheader("🎉 이달의 기념일 고객")

    current_month_str = datetime.now().strftime("%m")
    df_customers = pd.read_sql_query(
        "SELECT name as 고객명, phone as 연락처, anniversary as 기념일, notes as 메모 FROM customers",
        conn,
    )

    anniversary_df = df_customers[
        df_customers["기념일"].str.contains(
            f"^{current_month_str}|-{current_month_str}-", na=False
        )
    ]

    if len(anniversary_df) > 0:
        st.dataframe(anniversary_df, use_container_width=True)
    else:
        st.write("이번 달 기념일 등록 고객이 없습니다.")

# 4. 알림 발송 현황
elif menu == "🔔 알림 발송 현황":
    st.subheader("🔔 자동 발송 예정 알림 대상")

    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    st.markdown("##### 📌 24시간 이내 픽업 예정 (1일 전 알림 대상)")
    df_1day = pd.read_sql_query(
        f"""
        SELECT o.id, c.name as 고객명, c.phone as 연락처, o.product_name as 상품명, o.pickup_datetime as 픽업일시
        FROM orders o JOIN customers c ON o.customer_id = c.id
        WHERE o.notified_1day = 0 AND o.pickup_datetime BETWEEN '{now.strftime('%Y-%m-%d %H:%M:%S')}' AND '{tomorrow.strftime('%Y-%m-%d %H:%M:%S')}'
    """,
        conn,
    )

    st.dataframe(df_1day, use_container_width=True)