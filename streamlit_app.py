import streamlit as st
from datetime import datetime, time, date
import pytz
import pandas as pd

st.set_page_config(page_title="화사한 하루", layout="wide")

def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    * { font-family: 'Pretendard', sans-serif !important; }

    /* 상단 탭 디자인 강조 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        background-color: #FAFAFB;
        border-radius: 8px;
        border: 1px solid #E2D5F1;
        font-weight: 600;
        color: #582C83;
        font-size: 0.85rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #582C83 !important;
        color: white !important;
    }

    /* 제목 글씨 크기 및 위치 정돈 */
    .app-title {
        font-size: 1.56rem !important;
        color: #582C83 !important;
        font-weight: 700 !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.6rem !important;
        line-height: 1.4 !important;
    }
    .section-title {
        font-size: 1.26rem !important;
        color: #582C83 !important;
        font-weight: 600 !important;
        margin-top: 0.6rem !important;
        margin-bottom: 1.0rem !important;
        line-height: 1.4 !important;
    }
    
    div[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    div[data-testid="stForm"] {
        padding: 0.8rem !important;
        border-radius: 10px !important;
        border: 1px solid #E2D5F1 !important;
        background-color: #FAFAFB !important;
    }
    
    label, div[data-testid="stWidgetLabel"] { 
        font-size: 0.78rem !important; 
        font-weight: 600 !important; 
        margin-bottom: 2px !important; 
    }

    /* 픽업/접수 일시 가로 정렬 및 수직 센터 맞춤 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        align-items: flex-end !important;
    }
    div[data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    
    .stTextInput input, .stSelectbox select, .stNumberInput input, .stDateInput input, .stTimeInput input {
        min-height: 38px !important;
        height: 38px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-title">💐 화사한 하루 고객 & 주문 관리</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📝 신규 주문", 
    "📋 주문 목록 & 달력", 
    "🎂 고객 관리", 
    "🔔 알림 현황", 
    "📥 데이터 백업"
])

with tab1:
    st.markdown('<div class="section-title">📝 신규 주문 및 고객 등록</div>', unsafe_allow_html=True)
    now_kst = get_kst_now()

    with st.form("main_form"):
        c1, c2 = st.columns(2)
        with c1: st.text_input("고객 성명 *")
        with c2: st.text_input("휴대폰 번호", value="010-")
        
        c3, c4 = st.columns(2)
        with c3: st.selectbox("주문 상품명 *", ["꽃다발", "꽃바구니", "기타"])
        with c4: st.number_input("결제 금액 (원)", value=55000)
        
        p1, p2, p3 = st.columns([2.2, 1, 1.4])
        with p1: st.date_input("픽업 일시 *", now_kst.date(), key="p_date")
        with p2: st.selectbox(" ", ["AM", "PM"], index=1, key="p_period", label_visibility="collapsed")
        with p3: st.time_input(" ", time(14, 0), key="p_time", label_visibility="collapsed")
        
        curr_hour_24 = now_kst.hour
        is_pm = curr_hour_24 >= 12
        curr_hour_12 = curr_hour_24 if curr_hour_24 <= 12 else curr_hour_24 - 12
        curr_hour_12 = 12 if curr_hour_12 == 0 else curr_hour_12
        
        o1, o2, o3 = st.columns([2.2, 1, 1.4])
        with o1: st.date_input("접수 일시 *", now_kst.date(), key="o_date")
        with o2: st.selectbox("  ", ["AM", "PM"], index=1 if is_pm else 0, key="o_period", label_visibility="collapsed")
        with o3: st.time_input("  ", time(curr_hour_12, now_kst.minute), key="o_time", label_visibility="collapsed")
        
        st.selectbox("결제내역 *", ["네이버", "전화", "입금", "현금"])
        st.text_area("고객 요구사항 / 메모", height=70)
        
        st.form_submit_button("🌸 주문 저장하기", use_container_width=True)

with tab2:
    st.markdown('<div class="section-title">📋 전체 주문 목록 & 캘린더 뷰</div>', unsafe_allow_html=True)
    
    # 캘린더와 목록을 보기 좋게 분리
    col_cal, col_list = st.columns([1, 1.2])
    with col_cal:
        st.subheader("📅 픽업 캘린더")
        selected_date = st.date_input("날짜 선택", date.today(), label_visibility="collapsed")
        st.info(f"📌 **{selected_date}** 픽업 예정 주문이 아래에 표시됩니다.")
        
    with col_list:
        st.subheader("📋 주문 내역 상세")
        sample_data = pd.DataFrame({
            "고객명": ["김화사", "이플라워"],
            "연락처": ["010-1234-5678", "010-9876-5432"],
            "상품": ["꽃다발", "꽃바구니"],
            "픽업시간": ["PM 14:00", "PM 13:00"],
            "금액": ["55,000원", "70,000원"]
        })
        st.dataframe(sample_data, use_container_width=True)

with tab3:
    st.markdown('<div class="section-title">🎂 고객 관리</div>', unsafe_allow_html=True)
    st.text_input("🔍 등록된 고객 검색", placeholder="고객 이름 또는 연락처 검색")
    customer_data = pd.DataFrame({
        "고객명": ["김화사", "이플라워"],
        "연락처": ["010-1234-5678", "010-9876-5432"],
        "총 주문 횟수": [3, 1],
        "최근 주문일": ["2026-08-14", "2026-08-14"]
    })
    st.dataframe(customer_data, use_container_width=True)

with tab4:
    st.markdown('<div class="section-title">🔔 알림 발송 현황</div>', unsafe_allow_html=True)
    st.info("픽업 안내 및 기념일 알림 발송 내역을 관리하는 공간입니다.")

with tab5:
    st.markdown('<div class="section-title">📥 데이터 CSV 백업</div>', unsafe_allow_html=True)
    st.write("저장된 전체 주문 및 고객 데이터를 CSV 파일로 다운로드합니다.")
    st.download_button("📂 전체 데이터 CSV 다운로드", data="sample,csv,data", file_name="order_backup.csv", use_container_width=True)
