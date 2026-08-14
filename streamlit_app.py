import streamlit as st
from datetime import datetime, time, date
import pytz
import pandas as pd

st.set_page_config(page_title="화사한 하루", layout="wide")

def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

if 'orders' not in st.session_state:
    st.session_state.orders = [
        {
            "고객성명": "김화사",
            "휴대폰번호": "010-1234-5678",
            "주문상품명": "꽃다발",
            "결제금액": 55000,
            "픽업일시": "2026-08-14 PM 14:00",
            "접수일시": "2026-08-14 16:04",
            "결제내역": "네이버",
            "메모": "예쁘게 만들어주세요"
        }
    ]

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    * { font-family: 'Pretendard', sans-serif !important; }

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
    "📋 전체 주문 목록 & 달력", 
    "🎂 고객 관리", 
    "🔔 알림 현황", 
    "📥 데이터 백업"
])

with tab1:
    st.markdown('<div class="section-title">📝 신규 주문 및 고객 등록</div>', unsafe_allow_html=True)
    now_kst = get_kst_now()

    curr_hour_24 = now_kst.hour
    is_pm = curr_hour_24 >= 12
    curr_hour_12 = curr_hour_24 if curr_hour_24 <= 12 else curr_hour_24 - 12
    curr_hour_12 = 12 if curr_hour_12 == 0 else curr_hour_12

    with st.form("main_form"):
        c1, c2 = st.columns(2)
        with c1: cust_name = st.text_input("고객 성명 *")
        with c2: cust_phone = st.text_input("휴대폰 번호", value="010-")
        
        c3, c4 = st.columns(2)
        with c3: prod_name = st.selectbox("주문 상품명 *", ["꽃다발", "꽃바구니", "기타"])
        with c4: prod_price = st.number_input("결제 금액 (원)", value=55000)
        
        p1, p2, p3 = st.columns([2.2, 1, 1.4])
        with p1: p_date = st.date_input("픽업 일시 *", now_kst.date(), key="p_date")
        with p2: p_period = st.selectbox(" ", ["AM", "PM"], index=1, key="p_period", label_visibility="collapsed")
        with p3: p_time = st.time_input(" ", time(14, 0), key="p_time", label_visibility="collapsed")
        
        o1, o2, o3 = st.columns([2.2, 1, 1.4])
        with o1: o_date = st.date_input("접수 일시 *", now_kst.date(), key="o_date")
        with o2: o_period = st.selectbox("  ", ["AM", "PM"], index=1 if is_pm else 0, key="o_period", label_visibility="collapsed")
        with o3: o_time = st.time_input("  ", time(curr_hour_12, now_kst.minute), key="o_time", label_visibility="collapsed")
        
        pay_method = st.selectbox("결제내역 *", ["네이버", "전화", "입금", "현금"])
        memo = st.text_area("고객 요구사항 / 메모", height=70)
        
        submitted = st.form_submit_button("🌸 주문 저장하기", use_container_width=True)
        if submitted:
            if not cust_name:
                st.warning("고객 성명을 입력해주세요.")
            else:
                new_order = {
                    "고객성명": cust_name,
                    "휴대폰번호": cust_phone,
                    "주문상품명": prod_name,
                    "결제금액": prod_price,
                    "픽업일시": f"{p_date} {p_period} {p_time.strftime('%H:%M')}",
                    "접수일시": f"{o_date} {o_time.strftime('%H:%M')}",
                    "결제내역": pay_method,
                    "메모": memo
                }
                st.session_state.orders.append(new_order)
                st.success(f"'{cust_name}'님의 주문이 성공적으로 저장되었습니다!")

with tab2:
    st.markdown('<div class="section-title">📋 전체 주문 목록 & 달력</div>', unsafe_allow_html=True)
    col_cal, col_list = st.columns([1, 1.3])
    with col_cal:
        st.subheader("📅 날짜 선택 캘린더")
        cal_date = st.date_input("달력 날짜 선택", date.today(), key="calendar_view_date")
        st.info(f"📌 선택하신 **{cal_date}** 일자의 픽업 주문을 확인합니다.")
        
    with col_list:
        st.subheader("📋 전체 주문 내역")
        df_orders = pd.DataFrame(st.session_state.orders)
        st.dataframe(df_orders, use_container_width=True)

with tab3:
    st.markdown('<div class="section-title">🎂 고객 관리</div>', unsafe_allow_html=True)
    st.text_input("🔍 등록된 고객 검색", placeholder="고객 이름 또는 연락처 검색")
    if st.session_state.orders:
        df_cust = pd.DataFrame(st.session_state.orders)[["고객성명", "휴대폰번호", "주문상품명", "접수일시"]]
        st.dataframe(df_cust, use_container_width=True)
    else:
        st.info("등록된 고객 정보가 없습니다.")

with tab4:
    st.markdown('<div class="section-title">🔔 알림 발송 현황</div>', unsafe_allow_html=True)
    st.info("픽업 안내 및 기념일 알림 발송 내역을 관리하는 공간입니다.")

with tab5:
    st.markdown('<div class="section-title">📥 데이터 CSV 백업</div>', unsafe_allow_html=True)
    st.write("저장된 전체 주문 및 고객 데이터를 CSV 파일로 다운로드합니다.")
    if st.session_state.orders:
        df_csv = pd.DataFrame(st.session_state.orders)
        csv_data = df_csv.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📂 전체 데이터 CSV 다운로드", 
            data=csv_data, 
            file_name="order_backup.csv", 
            mime="text/csv",
            use_container_width=True
        )
