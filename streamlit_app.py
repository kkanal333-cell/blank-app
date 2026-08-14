import streamlit as st
import pandas as pd
from datetime import datetime, time
import pytz
import calendar
from supabase import create_client

# 1. Supabase 연결 설정
@st.cache_resource
def init_connection():
    # Streamlit Cloud의 Secrets에 설정된 값을 가져옵니다.
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# 2. 데이터 가져오기/저장 함수
def fetch_data():
    response = supabase.table("orders").select("*").execute()
    return response.data

st.set_page_config(page_title="화사한 하루", layout="wide")

st.sidebar.markdown("### 💐 화사한 하루 (DB연동)")
menu = st.sidebar.radio("메뉴 선택", ["신규 주문", "전체 주문 목록 & 달력"])

st.title("💐 화사한 하루 고객 & 주문 관리")

if menu == "신규 주문":
    with st.form("new_order"):
        c1, c2 = st.columns(2)
        with c1: name = st.text_input("고객 성명")
        with c2: phone = st.text_input("전화번호")
        p_date = st.date_input("픽업 일자")
        p_time = st.time_input("픽업 시간")
        pay = st.selectbox("결제내역", ["네이버", "전화", "입금", "카드"])
        
        if st.form_submit_button("저장"):
            supabase.table("orders").insert({
                "고객성명": name,
                "휴대폰번호": phone,
                "픽업일자": str(p_date),
                "픽업일시": f"{p_date} {p_time}",
                "결제내역": pay
            }).execute()
            st.success("DB에 저장되었습니다!")
            st.rerun()

elif menu == "전체 주문 목록 & 달력":
    data = fetch_data()
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df)
        
        # 삭제 예시
        del_id = st.text_input("삭제할 ID 입력")
        if st.button("삭제"):
            supabase.table("orders").delete().eq("id", del_id).execute()
            st.rerun()
