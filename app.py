import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="꽃집 고객/주문 관리 시스템", layout="wide", page_icon="💐")

# DB 연결 (Streamlit Secrets에서 정보 읽기)
@st.cache_resource
def get_connection():
    try:
        url = f"postgresql://{st.secrets['postgres']['user']}:{st.secrets['postgres']['password']}@{st.secrets['postgres']['host']}:{st.secrets['postgres']['port']}/{st.secrets['postgres']['dbname']}"
        return create_engine(url)
    except Exception as e:
        st.error(f"DB 연결 실패: {e}")
        return None

engine = get_connection()

# 데이터베이스 테이블 자동 생성
if engine:
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                phone VARCHAR(50),
                memo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                customer_name VARCHAR(100),
                phone VARCHAR(50),
                product_name VARCHAR(100),
                price INT,
                order_date DATE,
                delivery_date DATE,
                status VARCHAR(50),
                memo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

st.title("💐 꽃집 고객 & 주문 관리 시스템")

menu = st.sidebar.selectbox("메뉴 선택", ["주문 관리", "고객 관리", "데이터 백업 (CSV)"])

if engine:
    if menu == "주문 관리":
        st.header("📝 주문 관리")
        
        # 주문 입력 폼
        with st.form("order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("고객명")
                phone = st.text_input("연락처")
                product_name = st.text_input("상품명 (예: 장미 꽃다발)")
                price = st.number_input("금액 (원)", min_value=0, step=1000)
            with col2:
                order_date = st.date_input("주문일")
                delivery_date = st.date_input("픽업/배송일")
                status = st.selectbox("상태", ["접수", "제작중", "배송중", "완료", "취소"])
                memo = st.text_area("메모")
            
            submit = st.form_submit_button("주문 등록")
            if submit and customer_name:
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO orders (customer_name, phone, product_name, price, order_date, delivery_date, status, memo)
                        VALUES (:c, :p, :pr, :prc, :od, :dd, :st, :m)
                    """), {"c": customer_name, "p": phone, "pr": product_name, "prc": price, "od": order_date, "dd": delivery_date, "st": status, "m": memo})
                    conn.commit()
                st.success(f"'{customer_name}'님의 주문이 등록되었습니다!")
                st.rerun()

        st.subheader("📋 주문 내역 목록")
        df_orders = pd.read_sql("SELECT id as 주문번호, customer_name as 고객명, phone as 연락처, product_name as 상품명, price as 금액, order_date as 주문일, delivery_date as 배송일, status as 상태, memo as 메모 FROM orders ORDER BY id DESC", engine)
        st.dataframe(df_orders, use_container_width=True)

    elif menu == "고객 관리":
        st.header("👤 고객 관리")
        
        with st.form("customer_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("고객명")
                phone = st.text_input("연락처")
            with col2:
                memo = st.text_area("고객 특성/선호 꽃 메모")
            
            submit = st.form_submit_button("고객 등록")
            if submit and name:
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO customers (name, phone, memo)
                        VALUES (:n, :p, :m)
                    """), {"n": name, "p": phone, "m": memo})
                    conn.commit()
                st.success(f"'{name}' 고객님이 등록되었습니다!")
                st.rerun()

        st.subheader("📋 전체 고객 목록")
        df_customers = pd.read_sql("SELECT id as 고객번호, name as 고객명, phone as 연락처, memo as 메모, created_at as 등록일 FROM customers ORDER BY id DESC", engine)
        st.dataframe(df_customers, use_container_width=True)

    elif menu == "데이터 백업 (CSV)":
        st.header("📥 데이터 CSV 백업 (엑셀 저장)")
        st.write("데이터베이스에 저장된 모든 고객 및 주문 내역을 엑셀(CSV) 파일로 다운로드합니다.")

        st.subheader("1. 주문 내역 다운로드")
        df_orders = pd.read_sql("SELECT * FROM orders ORDER BY id DESC", engine)
        if not df_orders.empty:
            csv_orders = df_orders.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 전체 주문 내역 CSV 다운로드",
                data=csv_orders,
                file_name="flower_orders_backup.csv",
                mime="text/csv"
            )
        else:
            st.info("등록된 주문 내역이 없습니다.")

        st.subheader("2. 고객 목록 다운로드")
        df_customers = pd.read_sql("SELECT * FROM customers ORDER BY id DESC", engine)
        if not df_customers.empty:
            csv_customers = df_customers.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 전체 고객 목록 CSV 다운로드",
                data=csv_customers,
                file_name="flower_customers_backup.csv",
                mime="text/csv"
            )
        else:
            st.info("등록된 고객 정보가 없습니다.")
