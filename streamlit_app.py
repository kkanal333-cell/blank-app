import streamlit as st
from datetime import datetime, time
import pytz
import pandas as pd
import calendar
from supabase import create_client

# Supabase 연결 설정 (환경변수에서 로드)
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

st.set_page_config(page_title="화사한 하루", layout="wide")

def get_orders_from_db():
    response = supabase.table("orders").select("*").execute()
    return response.data

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .app-title { font-size: 1.56rem !important; color: #582C83 !important; font-weight: 700 !important; }
    .section-title { font-size: 1.26rem !important; color: #582C83 !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 💐 화사한 하루 (DB 연동 모드)")
menu = st.sidebar.radio("메뉴 선택", ["신규 주문", "전체 주문 목록 & 달력", "고객 관리", "데이터 백업"])

st.markdown('<div class="app-title">💐 화사한 하루 고객 & 주문 관리</div>', unsafe_allow_html=True)

# 데이터 로드
orders_data = get_orders_from_db()

if menu == "신규 주문":
    st.markdown('<div class="section-title">📝 신규 주문 등록</div>', unsafe_allow_html=True)
    with st.form("new_order_form"):
        c1, c2 = st.columns(2)
        with c1: cust_name = st.text_input("고객 성명 *")
        with c2: cust_phone = st.text_input("휴대폰 번호", "010-")
        
        c3, c4 = st.columns(2)
        with c3: prod_name = st.selectbox("상품명", ["꽃다발", "꽃바구니", "용돈박스", "화분", "기타"])
        with c4: prod_price = st.number_input("결제 금액", value=55000)
        
        p_date = st.date_input("픽업 일자")
        p_time = st.time_input("픽업 시간")
        pay_method = st.selectbox("결제내역", ["네이버", "전화", "입금", "현금", "카드"])
        memo = st.text_area("메모")
        
        if st.form_submit_button("저장"):
            supabase.table("orders").insert({
                "고객성명": cust_name, "휴대폰번호": cust_phone, "주문상품명": prod_name,
                "결제금액": prod_price, "픽업일자": str(p_date), "픽업일시": f"{p_date} {p_time}",
                "결제내역": pay_method, "메모": memo
            }).execute()
            st.success("저장 완료!")
            st.rerun()

elif menu == "전체 주문 목록 & 달력":
    if orders_data:
        df = pd.DataFrame(orders_data)
        st.dataframe(df, use_container_width=True)
        # 수정/삭제 로직도 동일하게 DB 연동으로 처리
        st.markdown("#### ✏️ 주문 수정 및 삭제")
        order_options = [f"{o['id']}: {o['고객성명']} ({o['주문상품명']})" for o in orders_data]
        sel_order = st.selectbox("주문 선택", order_options)
        if sel_order:
            order_id = sel_order.split(":")[0]
            if st.button("삭제"):
                supabase.table("orders").delete().eq("id", order_id).execute()
                st.rerun()
