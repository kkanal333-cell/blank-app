import streamlit as st
import pandas as pd
import re
from datetime import datetime, time, timedelta
import pytz
from sqlalchemy import create_engine, text
from streamlit_calendar import calendar

# 페이지 기본 설정
st.set_page_config(page_title="화사한 하루 - 고객/주문 관리", layout="wide", page_icon="💐")

# 스타일 설정: 이전의 안정적인 폰트/크기로 복원 및 모바일 대응 플렉스 레이아웃
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    html, body, [class*="css"], .stMarkdown, p, div, span, button, input, select {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }

    div[data-testid="stForm"] {
        padding: 1.2rem !important;
        border-radius: 12px !important;
    }
    
    div[data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }

    label, div[data-testid="stWidgetLabel"] {
        margin-bottom: 2px !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #4A5568 !important;
    }

    .custom-row-label {
        margin-top: 8px !important;
        margin-bottom: 2px !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #4A5568 !important;
        display: block !important;
    }

    .datetime-inline-wrapper {
        display: flex !important;
        flex-direction: row !important;
        gap: 6px !important;
        width: 100% !important;
        align-items: center !important;
    }
    
    .datetime-inline-wrapper > div {
        min-width: 0 !important;
    }

    .stButton>button {
        border-radius: 8px !important;
        background-color: #F3EEF9 !important;
        color: #582C83 !important;
        border: 1px solid #E2D5F1 !important;
        font-weight: 600 !important;
        margin-top: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

def parse_time_with_period(period, t_val):
    hour = t_val.hour
    minute = t_val.minute
    if period == "PM" or period == "오후":
        if hour < 12:
            hour += 12
    elif period == "AM" or period == "오전":
        if hour == 12:
            hour = 0
    return time(hour, minute)

# 휴대폰 번호 자동 하이픈 포맷팅 함수
def format_phone(phone_number):
    numbers = re.sub(r'[^0-9]', '', phone_number)
    if not numbers.startswith('010'):
        if numbers.startswith('0'):
            numbers = '010' + numbers[1:]
        else:
            numbers = '010' + numbers
    if len(numbers) > 11:
        numbers = numbers[:11]
        
    if len(numbers) >= 7:
        return f"{numbers[:3]}-{numbers[3:7]}-{numbers[7:]}"
    elif len(numbers) >= 4:
        return f"{numbers[:3]}-{numbers[3:]}"
    else:
        return numbers

@st.cache_resource
def get_connection():
    try:
        if "DB_URL" in st.secrets:
            url = st.secrets["DB_URL"]
        elif "postgres" in st.secrets:
            pg = st.secrets["postgres"]
            url = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}"
        else:
            return create_engine("sqlite:///orders.db")
        return create_engine(url)
    except Exception as e:
        return None

engine = get_connection()

if engine:
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50);"))
            conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS memo TEXT;"))
            conn.commit()
    except Exception as e:
        pass

st.title("💐 화사한 하루 고객 & 주문 관리")

PAYMENT_OPTIONS = ["네이버", "전화", "입금", "현금", "미결제"]
PRODUCT_OPTIONS = ["꽃다발", "꽃바구니", "햇살콘플라워", "꽃묶음", "식물", "용품", "시즌한정", "기타"]

menu_options = [
    "📝 신규 주문 및 고객 등록", 
    "📋 전체 주문 목록 & 달력", 
    "🎂 고객 관리", 
    "🔔 알림 발송 현황", 
    "📥 데이터 CSV 백업"
]

with st.sidebar:
    st.title("📌 메뉴")
    menu = st.radio("이동할 메뉴를 선택하세요", menu_options, key="sidebar_main_menu")

if engine:
    if menu == "📝 신규 주문 및 고객 등록":
        st.header("📝 신규 주문 및 고객 등록")
        now_kst = get_kst_now()
        
        with st.form("order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("고객 성명 *")
            with col2:
                phone_input = st.text_input("휴대폰 번호", value="010-", placeholder="010-0000-0000")
            
            col3, col4 = st.columns(2)
            with col3:
                product_name = st.selectbox("주문 상품명 *", PRODUCT_OPTIONS)
            with col4:
                amount = st.number_input("결제 금액 (원)", min_value=0, step=5000, value=55000)
            
            st.markdown('<div class="custom-row-label">픽업 일시 *</div>', unsafe_allow_html=True)
            st.markdown('<div class="datetime-inline-wrapper">', unsafe_allow_html=True)
            p_col1, p_col2, p_col3 = st.columns([2.2, 1, 1.3])
            with p_col1:
                pickup_date = st.date_input("픽업 날짜", now_kst.date(), label_visibility="collapsed", key="reg_p_date")
            with p_col2:
                pickup_period = st.selectbox("픽업 AM/PM", ["PM", "AM"], index=0, label_visibility="collapsed", key="reg_p_period")
            with p_col3:
                pickup_time_input = st.time_input("픽업 시간", time(2, 0), label_visibility="collapsed", key="reg_p_time")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="custom-row-label">접수 일시 *</div>', unsafe_allow_html=True)
            st.markdown('<div class="datetime-inline-wrapper">', unsafe_allow_html=True)
            o_col1, o_col2, o_col3 = st.columns([2.2, 1, 1.3])
            with o_col1:
                order_date = st.date_input("접수 날짜", now_kst.date(), label_visibility="collapsed", key="reg_o_date")
            with o_col2:
                order_period = st.selectbox("접수 AM/PM", ["AM", "PM"], index=0 if now_kst.hour < 12 else 1, label_visibility="collapsed", key="reg_o_period")
            with o_col3:
                curr_12h = now_kst.hour if now_kst.hour <= 12 else now_kst.hour - 12
                curr_12h = 12 if curr_12h == 0 else curr_12h
                order_time_input = st.time_input("접수 시간", time(curr_12h, now_kst.minute), label_visibility="collapsed", key="reg_o_time")
            st.markdown('</div>', unsafe_allow_html=True)
            
            payment_method = st.selectbox("결제내역 *", PAYMENT_OPTIONS)
            memo = st.text_area("고객 요구사항 / 메모", placeholder="요구사항이나 특이사항을 적어주세요.", height=85)
            
            submit = st.form_submit_button("🌸 주문 저장하기", use_container_width=True)
            if submit:
                if not customer_name:
                    st.warning("고객 성명은 필수 입력 항목입니다.")
                else:
                    try:
                        formatted_phone = format_phone(phone_input)
                        order_time = parse_time_with_period(order_period, order_time_input)
                        pickup_time = parse_time_with_period(pickup_period, pickup_time_input)
                        
                        order_datetime = datetime.combine(order_date, order_time)
                        pickup_datetime = datetime.combine(pickup_date, pickup_time)
                        
                        with engine.connect() as conn:
                            res = conn.execute(text("SELECT id FROM customers WHERE name = :n AND phone = :p LIMIT 1"), {"n": customer_name, "p": formatted_phone}).fetchone()
                            if res:
                                customer_id = int(res[0])
                            else:
                                ins_res = conn.execute(text("INSERT INTO customers (name, phone) VALUES (:n, :p) RETURNING id"), {"n": customer_name, "p": formatted_phone})
                                customer_id = int(ins_res.fetchone()[0])
                            
                            conn.execute(text("""
                                INSERT INTO orders (customer_id, product_name, product, amount, pickup_datetime, status, payment_method, memo, created_at)
                                VALUES (:cid, :pn, :p, :am, :pdt, :st, :pm, :memo, :cat)
                            """), {
                                "cid": customer_id,
                                "pn": product_name,
                                "p": product_name,
                                "am": int(amount),
                                "pdt": pickup_datetime,
                                "st": payment_method,
                                "pm": payment_method,
                                "memo": memo,
                                "cat": order_datetime
                            })
                            conn.commit()
                        st.success(f"'{customer_name}'님의 주문이 성공적으로 저장되었습니다!")
                    except Exception as e:
                        st.error(f"저장 실패: {e}")

    elif menu == "📋 전체 주문 목록 & 달력":
        st.header("📋 주문 내역 및 픽업 달력")
        try:
            query = """
                SELECT 
                    o.id as id, c.name as customer_name, c.phone as phone,
                    o.product_name as product_name, o.amount as amount,
                    o.created_at as created_at, o.pickup_datetime as pickup_datetime,
                    COALESCE(o.payment_method, o.status, '입금') as payment_method,
                    o.memo as memo, o.customer_id as customer_id
                FROM orders o LEFT JOIN customers c ON o.customer_id = c.id
                ORDER BY o.id DESC
            """
            df_orders = pd.read_sql(query, engine)
            
            def get_pastel_color(pm):
                if pm == '네이버': return "#E0F2FE"
                elif pm == '전화': return "#E9D8FD"
                elif pm == '입금': return "#DCFCE7"
                elif pm == '현금': return "#FEF08A"
                else: return "#FEE2E2"

            tab1, tab2 = st.tabs(["📅 픽업 달력", "📊 전체 주문 목록"])

            with tab1:
                calendar_events = []
                for _, row in df_orders.iterrows():
                    if pd.notnull(row['pickup_datetime']):
                        p_dt = pd.to_datetime(row['pickup_datetime'])
                        pm = row['payment_method'] or "입금"
                        color = get_pastel_color(pm)
                        calendar_events.append({
                            "id": str(int(row['id'])),
                            "title": f"[{pm}] {row['customer_name']} - {row['product_name']}",
                            "start": p_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                            "backgroundColor": color, "borderColor": color, "textColor": "#2D3748"
                        })
                
                cal_res = calendar(events=calendar_events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": ""}, "initialView": "dayGridMonth", "height": 500}, key="calendar_v3")
                
                clicked_date_str = None
                if cal_res and cal_res.get("dateClick"):
                    raw_date_str = cal_res["dateClick"]["date"]
                    clicked_date_str = str(raw_date_str)[:10]
                elif cal_res and cal_res.get("eventClick"):
                    evt_start = cal_res["eventClick"]["event"]["start"]
                    clicked_date_str = str(evt_start)[:10]

                if clicked_date_str:
                    st.subheader(f"📌 {clicked_date_str} 픽업 주문 목록")
                    df_orders_temp = df_orders.copy()
                    df_orders_temp['pickup_date_only'] = pd.to_datetime(df_orders_temp['pickup_datetime']).dt.strftime('%Y-%m-%d')
                    day_orders = df_orders_temp[df_orders_temp['pickup_date_only'] == clicked_date_str]
                    if not day_orders.empty:
                        disp_day_df = day_orders.rename(columns={
                            'id': '주문ID', 'customer_name': '고객명', 'phone': '연락처',
                            'product_name': '상품명', 'amount': '금액', 'created_at': '접수일시',
                            'pickup_datetime': '픽업일시', 'payment_method': '결제내역', 'memo': '메모'
                        }).drop(columns=['customer_id', 'pickup_date_only'], errors='ignore')
                        st.dataframe(disp_day_df, use_container_width=True)
                    else:
                        st.info(f"{clicked_date_str}에 예정된 픽업 주문이 없습니다.")

            with tab2:
                display_df = df_orders.rename(columns={
                    'id': '주문ID', 'customer_name': '고객명', 'phone': '연락처',
                    'product_name': '상품명', 'amount': '금액', 'created_at': '접수일시',
                    'pickup_datetime': '픽업일시', 'payment_method': '결제내역', 'memo': '메모'
                }).drop(columns=['customer_id'], errors='ignore')
                st.dataframe(display_df, use_container_width=True)
        except Exception as e:
            st.error(f"목록 조회 오류: {e}")

    elif menu == "🎂 고객 관리":
        st.header("🎂 고객 등록 및 목록")
        try:
            df_customers = pd.read_sql("SELECT id as ID, name as 고객명, phone as 연락처 FROM customers ORDER BY id DESC", engine)
            st.dataframe(df_customers, use_container_width=True)
        except Exception as e:
            st.error(f"고객 조회 실패: {e}")

    elif menu == "🔔 알림 발송 현황":
        st.header("🔔 픽업/배송 알림 발송 현황")
        st.info("카카오 알림톡 연동 대기 중입니다.")

    elif menu == "📥 데이터 CSV 백업":
        st.header("📥 데이터 CSV 백업 및 불러오기")
        try:
            df_orders = pd.read_sql("SELECT * FROM orders", engine)
            if not df_orders.empty:
                csv = df_orders.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 주문 내역 CSV 다운로드", data=csv, file_name="orders_backup.csv", mime="text/csv")
        except Exception as e:
            st.error(f"백업 오류: {e}")
