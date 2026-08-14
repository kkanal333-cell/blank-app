import streamlit as st
from datetime import datetime, time

st.set_page_config(page_title="화사한 하루", layout="wide")

# 더 강력하게 폰트와 스타일을 주입 (위치 조정)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 폰트 및 테마 색상 강제 지정 */
    * {
        font-family: 'Pretendard', sans-serif !important;
    }
    
    /* 보라색 포인트 색상 적용 */
    h1, h2 { color: #582C83 !important; }
    
    div[data-testid="stForm"] {
        border: 2px solid #E2D5F1 !important;
        border-radius: 15px !important;
        background-color: #FAFAFB !important;
    }
    
    /* 버튼 보라색 고정 */
    button[kind="primary"] {
        background-color: #582C83 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("💐 화사한 하루 고객 & 주문 관리")
st.header("📝 신규 주문 및 고객 등록")

with st.form("main_form"):
    c1, c2 = st.columns(2)
    c1.text_input("고객 성명 *")
    c2.text_input("휴대폰 번호", value="010-")
    
    c3, c4 = st.columns(2)
    c3.selectbox("주문 상품명 *", ["꽃다발", "꽃바구니", "기타"])
    c4.number_input("결제 금액 (원)", value=55000)
    
    # 픽업/접수 입력
    p1, p2, p3 = st.columns([2, 1, 1.5])
    p1.date_input("픽업 일시 *")
    p2.selectbox(" ", ["AM", "PM"], key="p_period")
    p3.time_input(" ", time(14, 0), key="p_time")
    
    o1, o2, o3 = st.columns([2, 1, 1.5])
    o1.date_input("접수 일시 *")
    o2.selectbox("  ", ["AM", "PM"], key="o_period")
    o3.time_input("  ", datetime.now().time(), key="o_time")
    
    st.selectbox("결제내역 *", ["네이버", "전화", "입금", "현금"])
    st.text_area("고객 요구사항 / 메모")
    
    st.form_submit_button("🌸 주문 저장하기", use_container_width=True)
