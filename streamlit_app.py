import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="꽃집 고객/주문 관리 시스템", layout="wide", page_icon="💐")

# DB 연결
@st.cache_resource
def get_connection():
    try:
        if "DB_URL" in st.secrets:
            url = st.secrets["DB_URL"]
        elif "postgres" in st.secrets:
            pg = st.secrets["postgres"]
            url = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}"
        else:
            st.error("Streamlit Secrets에 DB 연결 정보가 없습니다.")
            return None
        return create_engine(url)
    except Exception as e:
        st.error(f"DB 연결 실패: {e}")
        return None

engine = get_connection()

# 안전하게 테이블 데이터 전체 가져오기 함수 (모든 컬럼 자동 조율)
def fetch_table_safe(table_name, engine):
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name} ORDER BY id DESC", engine)
        return df
    except Exception as e:
        st.error(f"{table_name} 테이블 조회 실패: {e}")
        return pd.DataFrame()

st.title("💐 꽃집 고객 & 주문 관리 시스템")

st.sidebar.title("📌 메뉴 목록")
menu = st.sidebar.radio(
    "메뉴 선택", 
    [
        "📝 신규 주문 및 고객 등록", 
        "📋 주문 내역 관리 (수정/삭제)", 
        "🎂 고객 관리", 
        "🔔 알림 발송 현황", 
        "📥 데이터 CSV 백업"
    ]
)

if engine:
    # 1. 신규 주문 및 고객 등록
    if menu == "📝 신규 주문 및 고객 등록":
        st.header("📝 신규 주문 등록")
        with st.form("order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("고객 이름 *")
                phone = st.text_input("휴대폰 번호")
                product_name = st.text_input("주문 상품명 *")
                price = st.number_input("결제 금액 (원)", min_value=0, step=1000, value=50000)
            with col2:
                order_date = st.date_input("주문 날짜")
                delivery_date = st.date_input("픽업/배송 날짜")
                status = st.selectbox("상태", ["접수", "제작중", "배송중", "완료", "취소"])
                memo = st.text_area("특이사항 / 메모")
            
            submit = st.form_submit_button("주문 저장하기", use_container_width=True)
            if submit:
                if not customer_name or not product_name:
                    st.warning("고객 이름과 주문 상품명은 필수 입력 항목입니다.")
                else:
                    try:
                        # 존재하는 컬럼명을 확인 후 적절한 컬럼에 저장
                        df_test = pd.read_sql("SELECT * FROM orders LIMIT 1", engine)
                        cols = df_test.columns.tolist()
                        name_col = "customer_name" if "customer_name" in cols else ("name" if "name" in cols else cols[1])
                        
                        with engine.connect() as conn:
                            conn.execute(text(f"""
                                INSERT INTO orders ({name_col}, phone, product_name, price, order_date, delivery_date, status, memo)
                                VALUES (:c, :p, :pr, :prc, :od, :dd, :st, :m)
                            """), {"c": customer_name, "p": phone, "pr": product_name, "prc": price, "od": order_date, "dd": delivery_date, "st": status, "m": memo})
                            conn.commit()
                        st.success(f"'{customer_name}'님의 주문이 성공적으로 저장되었습니다!")
                    except Exception as e:
                        st.error(f"저장 실패: {e}")

    # 2. 주문 내역 관리 (수정/삭제)
    elif menu == "📋 주문 내역 관리 (수정/삭제)":
        st.header("📋 전체 주문 내역 및 수정/삭제")
        
        df_orders = fetch_table_safe("orders", engine)
        if not df_orders.empty:
            st.dataframe(df_orders, use_container_width=True)
            
            st.markdown("---")
            st.subheader("✏️ 주문 수정 및 삭제")
            
            order_ids = df_orders['id'].tolist()
            selected_id = st.selectbox("수정 또는 삭제할 주문 번호(ID) 선택", order_ids)
            
            selected_row = df_orders[df_orders['id'] == selected_id].iloc[0]
            
            # 이름 컬럼 감지
            name_col = "customer_name" if "customer_name" in df_orders.columns else ("name" if "name" in df_orders.columns else "id")
            
            with st.form("edit_order_form"):
                col1, col2 = st.columns(2)
                with col1:
                    edit_name = st.text_input("고객명", value=str(selected_row.get(name_col, "")) if pd.notnull(selected_row.get(name_col)) else "")
                    edit_phone = st.text_input("연락처", value=str(selected_row.get('phone', "")) if pd.notnull(selected_row.get('phone')) else "")
                    edit_product = st.text_input("상품명", value=str(selected_row.get('product_name', "")) if pd.notnull(selected_row.get('product_name')) else "")
                    edit_price = st.number_input("금액 (원)", min_value=0, step=1000, value=int(selected_row.get('price', 0)) if pd.notnull(selected_row.get('price')) else 0)
                with col2:
                    edit_order_date = st.date_input("주문일", value=pd.to_datetime(selected_row['order_date']) if 'order_date' in selected_row and pd.notnull(selected_row['order_date']) else None)
                    edit_delivery_date = st.date_input("배송일", value=pd.to_datetime(selected_row['delivery_date']) if 'delivery_date' in selected_row and pd.notnull(selected_row['delivery_date']) else None)
                    
                    status_list = ["접수", "제작중", "배송중", "완료", "취소"]
                    curr_status = selected_row.get('status', '접수')
                    curr_status_idx = status_list.index(curr_status) if curr_status in status_list else 0
                    edit_status = st.selectbox("상태", status_list, index=curr_status_idx)
                    
                    edit_memo = st.text_area("메모", value=str(selected_row.get('memo', "")) if pd.notnull(selected_row.get('memo')) else "")
                
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    update_btn = st.form_submit_button("💾 수정사항 저장", use_container_width=True)
                with btn_col2:
                    delete_btn = st.form_submit_button("🗑️ 주문 삭제", use_container_width=True)
                
                if update_btn:
                    with engine.connect() as conn:
                        conn.execute(text(f"""
                            UPDATE orders 
                            SET {name_col}=:c, phone=:p, product_name=:pr, price=:prc, order_date=:od, delivery_date=:dd, status=:st, memo=:m
                            WHERE id=:id
                        """), {"c": edit_name, "p": edit_phone, "pr": edit_product, "prc": edit_price, "od": edit_order_date, "dd": edit_delivery_date, "st": edit_status, "m": edit_memo, "id": selected_id})
                        conn.commit()
                    st.success(f"{selected_id}번 주문이 수정되었습니다!")
                    st.rerun()
                    
                if delete_btn:
                    with engine.connect() as conn:
                        conn.execute(text("DELETE FROM orders WHERE id=:id"), {"id": selected_id})
                        conn.commit()
                    st.warning(f"{selected_id}번 주문이 삭제되었습니다.")
                    st.rerun()

    # 3. 고객 관리
    elif menu == "🎂 고객 관리":
        st.header("🎂 고객 등록 및 목록")
        with st.form("customer_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("고객명 *")
                phone = st.text_input("연락처")
            with col2:
                memo = st.text_area("선호하는 꽃 / 메모")
            submit = st.form_submit_button("고객 등록", use_container_width=True)
            if submit and name:
                with engine.connect() as conn:
                    conn.execute(text("INSERT INTO customers (name, phone, memo) VALUES (:n, :p, :m)"), {"n": name, "p": phone, "m": memo})
                    conn.commit()
                st.success(f"'{name}' 고객님이 등록되었습니다!")
                st.rerun()
                
        df_customers = fetch_table_safe("customers", engine)
        if not df_customers.empty:
            st.dataframe(df_customers, use_container_width=True)

    # 4. 알림 발송 현황
    elif menu == "🔔 알림 발송 현황":
        st.header("🔔 픽업/배송 알림 발송 현황")
        st.write("오늘 및 향후 픽업/배송 예정인 고객들의 알림 상태를 확인합니다.")
        
        df_orders = fetch_table_safe("orders", engine)
        if not df_orders.empty:
            if 'status' in df_orders.columns:
                upcoming_orders = df_orders[~df_orders['status'].isin(['완료', '취소'])]
            else:
                upcoming_orders = df_orders
            st.subheader("📌 픽업/배송 대기 목록")
            st.dataframe(upcoming_orders, use_container_width=True)
            st.info("💡 솔라피(Solapi) 카카오 알림톡 서비스 연동 준비 완료 상태입니다.")
        else:
            st.info("현재 대기 중인 픽업/배송 알림이 없습니다.")

    # 5. 데이터 CSV 백업
    elif menu == "📥 데이터 CSV 백업":
        st.header("📥 데이터 CSV 백업 (엑셀 저장)")
        st.write("엑셀에서 한글이 깨지지 않도록 인코딩(UTF-8 BOM) 처리된 파일입니다.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. 전체 주문 내역")
            df_orders = fetch_table_safe("orders", engine)
            if not df_orders.empty:
                csv_orders = df_orders.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 주문 내역 엑셀다운로드",
                    data=csv_orders,
                    file_name="flower_orders_backup.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("등록된 주문 내역이 없습니다.")

        with col2:
            st.subheader("2. 전체 고객 목록")
            df_customers = fetch_table_safe("customers", engine)
            if not df_customers.empty:
                csv_customers = df_customers.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 고객 목록 엑셀다운로드",
                    data=csv_customers,
                    file_name="flower_customers_backup.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("등록된 고객 정보가 없습니다.")
