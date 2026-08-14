import streamlit as st
import pandas as pd
import re
from datetime import datetime, time, timedelta
import pytz
from sqlalchemy import create_engine, text
from streamlit_calendar import calendar

# 페이지 기본 설정
st.set_page_config(page_title="화사한 하루 - 고객/주문 관리", layout="wide", page_icon="💐")

# 스타일 설정
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"], .stMarkdown, p, div, span, button, input, select {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    div[data-testid="stForm"] { padding: 1.2rem !important; border-radius: 12px !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
    label, div[data-testid="stWidgetLabel"] { margin-bottom: 2px !important; font-size: 0.88rem !important; font-weight: 600 !important; color: #4A5568 !important; }
    .custom-row-label { margin-top: 8px !important; margin-bottom: 2px !important; font-size: 0.88rem !important; font-weight: 600 !important; color: #4A5568 !important; display: block !important; }
    .datetime-inline-wrapper { display: flex !important; flex-direction: row !important; gap: 6px !important; width: 100% !important; align-items: center !important; }
    .stButton>button { border-radius: 8px !important; background-color: #F3EEF9 !important; color: #582C83 !important; border: 1px solid #E2D5F1 !important; font-weight: 600 !important; margin-top: 10px !important; }
</style>
""", unsafe_allow_html=True)

def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

def parse_time_with_period(period, t_val):
    hour = t_val.hour
    minute = t_val.minute
    if period in ["PM", "오후"]:
        if hour < 12: hour += 12
    elif period in ["AM", "오전"]:
        if hour == 12: hour = 0
    return time(hour, minute)

def format_phone(phone_number):
    numbers = re.sub(r'[^0-9]', '', phone_number)
    if not numbers.startswith('010'):
        numbers = '010' + numbers[1:] if numbers.startswith('0') else '010' + numbers
    if len(numbers) > 11: numbers = numbers[:11]
    return f"{numbers[:3]}-{numbers[3:7]}-{numbers[7:]}" if len(numbers) >= 7 else numbers

@st.cache_resource
def get_connection():
    try:
        if "DB_URL" in st.secrets: url = st.secrets["DB_URL"]
        else: return create_engine("sqlite:///orders.db")
        return create_engine(url)
    except: return None

engine = get_connection()

st.title("💐 화사한 하루 고객 & 주문 관리")
menu = st.sidebar.radio("📌 메뉴", ["📝 신규 주문 및 고객 등록", "📋 전체 주문 목록 & 달력", "🎂 고객 관리", "🔔 알림 발송 현황", "📥 데이터 CSV 백업"])

if menu == "📝 신규 주문 및 고객 등록":
    st.header("📝 신규 주문 및 고객 등록")
    with st.form("order_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        customer_name = col1.text_input("고객 성명 *")
        phone_input = col2.text_input("휴대폰 번호", value="010-")
        col3, col4 = st.columns(2)
        product_name = col3.selectbox("주문 상품명 *", ["꽃다발", "꽃바구니", "햇살콘플라워", "꽃묶음", "식물", "용품", "시즌한정", "기타"])
        amount = col4.number_input("결제 금액 (원)", min_value=0, step=5000, value=55000)
        
        st.markdown('<div class="custom-row-label">픽업 일시 *</div>', unsafe_allow_html=True)
        p_col1, p_col2, p_col3 = st.columns([2.2, 1, 1.3])
        pickup_date = p_col1.date_input("픽업 날짜", get_kst_now().date(), label_visibility="collapsed")
        pickup_period = p_col2.selectbox("픽업 AM/PM", ["PM", "AM"], label_visibility="collapsed")
        pickup_time_input = p_col3.time_input("픽업 시간", time(2, 0), label_visibility="collapsed")
        
        if st.form_submit_button("🌸 주문 저장하기", use_container_width=True):
            if not customer_name: st.warning("고객 성명을 입력하세요.")
            else:
                p_dt = datetime.combine(pickup_date, parse_time_with_period(pickup_period, pickup_time_input))
                with engine.connect() as conn:
                    conn.execute(text("INSERT INTO orders (customer_id, product_name, amount, pickup_datetime, created_at) VALUES (1, :pn, :am, :pdt, :cat)"), 
                                 {"pn": product_name, "am": amount, "pdt": p_dt, "cat": get_kst_now()})
                    conn.commit()
                st.success("저장되었습니다!")

elif menu == "📋 전체 주문 목록 & 달력":
    st.header("📋 주문 내역 및 픽업 달력")
    df = pd.read_sql("SELECT id, customer_name, product_name, pickup_datetime, payment_method FROM orders", engine)
    
    tab1, tab2 = st.tabs(["📅 픽업 달력", "📊 전체 주문 목록"])
    with tab1:
        events = []
        for _, row in df.iterrows():
            if pd.notnull(row['pickup_datetime']):
                events.append({
                    "id": str(row['id']),
                    "title": f"{row['customer_name']}-{row['product_name']}",
                    "start": pd.to_datetime(row['pickup_datetime']).strftime("%Y-%m-%dT%H:%M:%S")
                })
        
        cal_res = calendar(events=events, options={"initialView": "dayGridMonth"})
        
        # 클릭된 날짜 처리 (KST 기준 오프셋 보정)
        clicked_date = None
        if cal_res and ("dateClick" in cal_res or "eventClick" in cal_res):
            raw_date = cal_res["dateClick"]["date"] if "dateClick" in cal_res else cal_res["eventClick"]["event"]["start"]
            # 문자열 날짜를 파싱하여 KST 적용 후 날짜만 추출
            clicked_date = pd.to_datetime(raw_date).tz_localize(None).strftime("%Y-%m-%d")
        
        if clicked_date:
            st.subheader(f"📌 {clicked_date} 픽업 목록")
            filtered = df[pd.to_datetime(df['pickup_datetime']).dt.strftime('%Y-%m-%d') == clicked_date]
            st.dataframe(filtered)
