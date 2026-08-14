import streamlit as st
from datetime import datetime, time

st.set_page_config(page_title="화사한 하루", layout="wide")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 1. 전체 글꼴 및 줄 간격 (밀착) */
    * {
        font-family: 'Pretendard', sans-serif !important;
        line-height: 1.1 !important; 
    }
    
    /* 2. 제목 글씨 크기 대폭 축소 */
    h1 { font-size: 1.4rem !important; color: #582C83 !important; margin-bottom: 0.5rem !important; }
    h2 { font-size: 1.1rem !important; color: #582C83 !important; margin-bottom: 0.5rem !important; }
    
    /* 3. 위젯 간격 좁히기 */
    .stApp > header { display: none; }
    div[data-testid="stVerticalBlock"] { gap: 0.2rem !important; }
    
    /* 4. 폼 스타일 */
    div[data-testid="stForm"] {
        padding: 0.8rem !important;
        border-radius: 8px !important;
        border: 1px solid #E2D5F1 !important;
    }
    
    /* 5. 라벨 크기 축소 */
    label { font-size: 0.75rem !important; font-weight: 600 !important; margin-bottom: 0px !important; }
    
    /* 6. 버튼 */
    button { padding: 0.2rem 0.5rem !important; font-size: 0.9rem !important; }
</style>
""", unsafe_allow_html=True)

# 제목을 st.title 대신 markdown으로 직접 제어하여 크기 고정
st.markdown("<h1>💐 화사한 하루 고객 & 주문 관리</h1>", unsafe_allow_html=True)
st.markdown("<h2>📝 신규 주문 및 고객 등록</h2>", unsafe_allow_html=True)

with st.form("main_form"):
    c1, c2 = st.columns(2)
    c1.text_input("고객 성명 *")
    c2.text_input("휴대폰 번호", value="010-")
    
    c3, c4 = st.columns(2)
    c3.selectbox("주문 상품명 *", ["꽃다발", "꽃바구니", "기타"])
    c4.number_input("결제 금액 (원)", value=55000)
    
    p1, p2, p3 = st.columns([2, 1, 1.5])
    p1.date_input("픽업 일시 *")
    p2.selectbox(" ", ["AM", "PM"], key="p_period")
    p3.time_input(" ", time(14, 0), key="p_time")
    
    o1, o2, o3 = st.columns([2, 1, 1.5])
    o1.date_input("접수 일시 *")
    o2.selectbox("  ", ["AM", "PM"], key="o_period")
    o3.time_input("  ", datetime.now().time(), key="o_time")
    
    st.selectbox("결제내역 *", ["네이버", "전화", "입금", "현금"])
    st.text_area("고객 요구사항 / 메모", height=70)
    
    st.form_submit_button("🌸 주문 저장하기", use_container_width=True)
