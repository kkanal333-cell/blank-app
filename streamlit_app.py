import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from sqlalchemy import create_engine, text
from streamlit_calendar import calendar

st.set_page_config(page_title="화사한 하루", layout="wide", page_icon="💐")
st.title("💐 화사한 하루")

engine = create_engine("sqlite:///orders.db")
with engine.connect() as conn:
    conn.execute(text("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT)"))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, 
            product_name TEXT, amount INTEGER, pickup_datetime DATETIME, 
            payment_method TEXT, memo TEXT
        )
    """))
    conn.commit()

try:
    df = pd.read_sql("SELECT o.*, c.name as customer_name FROM orders o LEFT JOIN customers c ON o.customer_id = c.id", engine)
except:
    df = pd.DataFrame()

events = []
if not df.empty:
    for _, row in df.iterrows():
        if pd.notnull(row['pickup_datetime']):
            events.append({
                "id": str(row['id']),
                "title": f"{row['customer_name']}({row['product_name']})",
                "start": pd.to_datetime(row['pickup_datetime']).strftime("%Y-%m-%dT%H:%M:%S"),
                "backgroundColor": "#FFC0CB"
            })

cal_res = calendar(events=events, options={"initialView": "dayGridMonth", "selectable": True})

if cal_res and "dateClick" in cal_res:
    st.session_state.selected_date = cal_res["dateClick"]["dateStr"]

if "selected_date" in st.session_state:
    st.subheader(f"📅 {st.session_state.selected_date} 주문 리스트")
    
    if not df.empty:
        df['date_only'] = pd.to_datetime(df['pickup_datetime']).dt.strftime('%Y-%m-%d')
        day_df = df[df['date_only'] == st.session_state.selected_date]
        
        if not day_df.empty:
            for _, r in day_df.iterrows():
                with st.expander(f"{r['customer_name']}님 - {r['product_name']} ({pd.to_datetime(r['pickup_datetime']).strftime('%H:%M')})"):
                    st.write(f"금액: {r['amount']:,}원")
                    with st.form(f"edit_{r['id']}"):
                        new_name = st.text_input("고객명 수정", value=r['customer_name'])
                        new_prod = st.text_input("상품명 수정", value=r['product_name'])
                        if st.form_submit_button("💾 수정 저장"):
                            with engine.connect() as conn:
                                conn.execute(text("UPDATE customers SET name=:n WHERE id=:cid"), {"n": new_name, "cid": int(r['customer_id'])})
                                conn.execute(text("UPDATE orders SET product_name=:p WHERE id=:oid"), {"p": new_prod, "oid": int(r['id'])})
                                conn.commit()
                            st.success("수정 완료!")
                            st.rerun()
        else:
            st.info("해당 날짜에 주문이 없습니다.")
    else:
        st.info("등록된 주문 데이터가 없습니다.")