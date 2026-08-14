import streamlit as st
from datetime import datetime, time

st.set_page_config(page_title="화사한 하루", layout="wide")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    * {
        font-family: 'Pretendard', sans-serif !important;
    }
    
    /* 1. 제목 글씨 크기 20% 확대 및 행간 50% 넓히기 */
    .app-title {
        font-size: 1.56rem !important; /* 1.3rem의 약 20% 증가 */
        color: #582C83 !important;
        font-weight: 700 !important;
        margin-bottom: 0.6rem !important; /* 행간 50% 넓힘 */
        line-height: 1.4 !important;
    }
    .section-title {
        font-size: 1.26rem !important; /* 1.05rem의 약 20% 증가 */
        color: #582C83 !important;
        font-weight: 600 !important;
        margin-top: 0.6rem !important;
        margin-bottom: 1.0rem !important; /* 행간 50% 넓힘 */
        line-height: 1.4 !important;
    }
    
    /* 2. 폼 및 위젯 간격 */
    div[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    div[data-testid="stForm"] {
        padding: 0.8rem !important;
        border-radius: 10px !important;
        border: 1px solid #E2D5F1 !important;
        background-color: #FAFAFB !important;
    }
    
    /* 3. 라벨 스타일 */
    label, div[data-testid="stWidgetLabel"] { 
        font-size: 0.78rem !important; 
        font-weight: 600 !important; 
        margin-bottom: 2px !important; 
    }

    /* 4. 픽업/접수 일시 가로 정렬 및 수직 센터 완벽 맞춤 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        align-items: flex-end !important; /* 하단 기준 정렬로 높이 맞춤 */
    }
    div[data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    
    /* 입력창 및 셀렉트박스 높이/패딩 통일로 어긋남 방지 */
    .stTextInput input, .stSelectbox select, .stNumberInput input, .stDateInput input, .stTimeInput input {
        min-height: 38px !important;
        height: 38px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

# 크기와 행간이 조절된 제목 영역
st.markdown('<div class="app-title">💐 화사한 하루 고객 & 주문 관리</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📝 신규 주문 및 고객 등록</div>', unsafe_allow_html=True)

with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1: st.text_input("고객 성명 *")
    with c2: st.text_input("휴대폰 번호", value="010-")
    
    c3, c4 = st.columns(2)
    with c3: st.selectbox("주문 상품명 *", ["꽃다발", "꽃바구니", "기타"])
    with c4: st.number_input("결제 금액 (원)", value=55000)
    
    # 픽업 일시 (완벽하게 수직 정렬된 가로 한 줄)
    p1, p2, p3 = st.columns([2.2, 1, 1.4])
    with p1: st.date_input("픽업 일시 *", key="p_date")
    with p2: st.selectbox(" ", ["AM", "PM"], key="p_period", label_visibility="collapsed")
    with p3: st.time_input(" ", time(14, 0), key="p_time", label_visibility="collapsed")
    
    # 접수 일시 (완벽하게 수직 정렬된 가로 한 줄)
    o1, o2, o3 = st.columns([2.2, 1, 1.4])
    with o1: st.date_input("접수 일시 *", key="o_date")
    with o2: st.selectbox("  ", ["AM", "PM"], key="o_period", label_visibility="collapsed")
    with o3: st.time_input("  ", datetime.now().time(), key="o_time", label_visibility="collapsed")
    
    st.selectbox("결제내역 *", ["네이버", "전화", "입금", "현금"])
    st.text_area("고객 요구사항 / 메모", height=70)
    
    st.form_submit_button("🌸 주문 저장하기", use_container_width=True)
