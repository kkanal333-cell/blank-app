import streamlit as st
from datetime import datetime, time

st.set_page_config(page_title="화사한 하루", layout="wide")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    /* 1. 전체 글꼴 및 초밀착 줄 간격 */
    * {
        font-family: 'Pretendard', sans-serif !important;
        line-height: 1.15 !important; 
    }
    
    /* 2. 제목 글씨 크기 축소 */
    h1 { font-size: 1.3rem !important; color: #582C83 !important; margin-bottom: 0.3rem !important; padding: 0 !important; }
    h2 { font-size: 1.0rem !important; color: #582C83 !important; margin-bottom: 0.3rem !important; padding: 0 !important; }
    
    /* 3. 위젯 및 폼 간격 대폭 압축 */
    div[data-testid="stVerticalBlock"] { gap: 0.1rem !important; }
    div[data-testid="stForm"] {
        padding: 0.6rem !important;
        border-radius: 8px !important;
        border: 1px solid #E2D5F1 !important;
    }
    
    /* 4. 라벨 크기 */
    label, div[data-testid="stWidgetLabel"] { 
        font-size: 0.75rem !important; 
        font-weight: 600 !important; 
        margin-bottom: 0px !important; 
        padding-bottom: 0px !important;
    }

    /* 5. 모바일 세로 화면 대응: 픽업/접수 일시를 무조건 가로 한 줄로 강제 배치 */
    @media (max-width: 768px) {
        /* 스트림릿의 컬럼들을 가로로 나란히 강제 정렬 */
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 4px !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            flex: 1 1 0% !important;
            min-width: 0 !important;
        }
    }
    
    /* 6. 입력창 및 버튼 여백 최소화 */
    .stTextInput input, .stSelectbox select, .stNumberInput input, .stDateInput input, .stTimeInput input {
        padding-top: 2px !important;
        padding-bottom: 2px !important;
        min-height: 32px !important;
    }
    button { padding: 0.2rem 0.5rem !important; font-size: 0.85rem !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>💐 화사한 하루 고객 & 주문 관리</h1>", unsafe_allow_html=True)
st.markdown("<h2>📝 신규 주문 및 고객 등록</h2>", unsafe_allow_html=True)

with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1: st.text_input("고객 성명 *")
    with c2: st.text_input("휴대폰 번호", value="010-")
    
    c3, c4 = st.columns(2)
    with c3: st.selectbox("주문 상품명 *", ["꽃다발", "꽃바구니", "기타"])
    with c4: st.number_input("결제 금액 (원)", value=55000)
    
    # 픽업 일시 (모바일/PC 모두 가로 한 줄 유지)
    p1, p2, p3 = st.columns([2.2, 1, 1.4])
    with p1: st.date_input("픽업 일시 *", key="p_date")
    with p2: st.selectbox(" ", ["AM", "PM"], key="p_period", label_visibility="collapsed")
    with p3: st.time_input(" ", time(14, 0), key="p_time", label_visibility="collapsed")
    
    # 접수 일시 (모바일/PC 모두 가로 한 줄 유지)
    o1, o2, o3 = st.columns([2.2, 1, 1.4])
    with o1: st.date_input("접수 일시 *", key="o_date")
    with o2: st.selectbox("  ", ["AM", "PM"], key="o_period", label_visibility="collapsed")
    with o3: st.time_input("  ", datetime.now().time(), key="o_time", label_visibility="collapsed")
    
    st.selectbox("결제내역 *", ["네이버", "전화", "입금", "현금"])
    st.text_area("고객 요구사항 / 메모", height=60)
    
    st.form_submit_button("🌸 주문 저장하기", use_container_width=True)
