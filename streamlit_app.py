import streamlit as st
import pandas as pd
import re
from datetime import datetime, time
import pytz
from sqlalchemy import create_engine, text
from streamlit_calendar import calendar

# 페이지 기본 설정
st.set_page_config(page_title="화사한 하루 - 고객/주문 관리", layout="wide", page_icon="💐")

# 스타일 복구: 이전의 보라색 테마와 폰트 크기 스타일 적용
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [class*="css"], .stMarkdown, p, div, span, button, input, select {
        font-family: 'Pretendard', sans-serif !important;
    }

    div[data-testid="stForm"] {
        padding: 1.2rem !important;
        border-radius: 12px !important;
    }

    label, div[data-testid="stWidgetLabel"] {
        font-size: 0.85rem !important;
        color: #4A5568 !important;
        font-weight: 600 !important;
    }

    /* 버튼 스타일 (보라톤 유지) */
    .stButton>button {
        border-radius: 8px !important;
        background-color: #F3EEF9 !important;
        color: #582C83 !important;
        border: 1px solid #E2D5F1 !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

def parse_time_with_period(period, t_val):
    hour = t_val.hour
    minute = t_val.minute
    if period == "PM" or period == "오후":
        if hour < 12: hour += 12
    elif period == "AM" or period == "오전":
        if hour == 12: hour = 0
    return time(hour, minute)

def format_phone(phone_number):
    numbers = re.sub(r'[^0-9]', '', phone_number)
    if not numbers.startswith('010'): numbers = '010' + numbers[1:] if numbers.startswith('0') else '010' + numbers
    if len(numbers) > 11: numbers = numbers[:11]
    return f"{numbers[:3]}-{numbers[3:7]}-{numbers[7:]}" if len(numbers) >= 7 else numbers

@st.cache_resource
def get_connection():
    try:
        return create_engine("sqlite:///orders.db")
    except: return None

engine = get_connection()
st.title("💐 화사한 하루 고객 & 주문 관리")

menu = st.sidebar.radio("📌 메뉴", ["📝 신규 주문 및 고객 등록", "📋 전체 주문 목록 & 달력", "🎂 고객 관리", "🔔 알림 발송 현황", "📥 데이터 CSV 백업"])

if menu == "📝 신규 주문 및 고객 등록":
    st.header("📝 신규 주문 및 고객 등록")
    now_kst = get_kst_now()
    with st.form("order_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        customer_name = col1.text_input("고객 성명 *")
        phone_input = col2.text_input("휴대폰 번호", value="010-")
        
        col3, col4 = st.columns(2)
        product_name = col3.selectbox("주문 상품명 *", ["꽃다발", "꽃바구니", "햇살콘플라워", "기타"])
        amount = col4.number_input("결제 금액 (원)", value=55000)
        
        # 일시 항목 (기본 스트림릿 컬럼 방식 사용 - 모바일 최적화)
        p1, p2, p3 = st.columns([2, 1, 1.5])
        pickup_date = p1.date_input("픽업 일시 *", now_kst.date())
        pickup_period = p2.selectbox(" ", ["AM", "PM"], index=1)
        pickup_time = p3.time_input(" ", time(14, 0))
        
        o1, o2, o3 = st.columns([2, 1, 1.5])
        order_date = o1.date_input("접수 일시 *", now_kst.date())
        order_period = o2.selectbox("  ", ["AM", "PM"], index=1)
        order_time = o3.time_input("  ", now_kst.time())
        
        payment_method = st.selectbox("결제내역 *", ["네이버", "전화", "입금", "현금"])
        memo = st.text_area("고객 요구사항 / 메모")
        
        if st.form_submit_button("🌸 주문 저장하기", use_container_width=True):
            st.success("주문이 저장되었습니다!")

elif menu == "📋 전체 주문 목록 & 달력":
    st.header("📋 주문 내역")
    # 달력 및 목록 표시 로직
    st.info("데이터를 불러오는 중입니다...")

elif menu == "🎂 고객 관리":
    st.header("🎂 고객 관리")

