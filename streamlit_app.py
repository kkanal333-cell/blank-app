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

# DB 컬럼 동적 조회 함수 (customer_name vs name 호환)
def get_orders_df(engine):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='orders'"))
        cols = [row[0] for row in result.fetchall()]
    
    name_col = "customer_name" if "customer_name" in cols else "name"
    query = f"SELECT id, {name_col} as 고객명, phone as 연락처, product_name as 상품명, price as 금액, order_date as 주문일, delivery_date as 배송일, status as 상태, memo as 메모 FROM orders ORDER BY id DESC"
    return pd.read_sql(query, engine), name_col

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
                        _, name_col = get_orders_df(engine)
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
        
        try:
            df_orders, name_col = get_orders_df(engine)
            st.dataframe(df_orders, use_container_width=True)
            
            if not df_orders.empty:
                st.markdown("---")
                st.subheader("✏️ 주문 수정 및 삭제")
                
                order_ids = df_orders['id'].tolist()
                selected_id = st.selectbox("수정 또는 삭제할 주문 번호(ID) 선택", order_ids)
                
                selected_row = df_orders[df_orders['id'] == selected_id].iloc[0]
                
                with st.form("edit_order_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input("고객명", value=selected_row['고객명'] or "")
                        edit_phone = st.text_input("연락처", value=selected_row['연락처'] or "")
                        edit_product = st.text_input("상품명", value=selected_row['상품명'] or "")
                        edit_price = st.number_input("금액 (원)", min_value=0, step=1000, value=int(selected_row['금액'] or 0))
                    with col2:
                        edit_order_date = st.date_input("주문일", value=pd.to_datetime(selected_row['주문일']) if pd.notnull(selected_row['주문일']) else None)
                        edit_delivery_date = st.date_input("배송일", value=pd.to_datetime(selected_row['배송일']) if pd.notnull(selected_row['배송일']) else None)
                        
                        status_list = ["접수", "제작중", "배송중", "완료", "취소"]
                        curr_status_idx = status_list.index(selected_row['상태']) if selected_row['상태'] in status_list else 0
                        edit_status = st.selectbox("상태", status_list, index=curr_status_idx)
                        
                        edit_memo = st.text_area("메모", value=selected_row['메모'] or "")
                    
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
        except Exception as e:
            st.error(f"주문 목록을 가져오는 중 오류가 발생했습니다: {e}")

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
                
        try:
            df_customers = pd.read_sql("SELECT id, name as 고객명, phone as 연락처, memo as 메모 FROM customers ORDER BY id DESC", engine)
            st.dataframe(df_customers, use_container_width=True)
        except Exception as e:
            st.error(f"고객 목록을 가져오는 중 오류가 발생했습니다: {e}")

    # 4. 알림 발송 현황 (복원 완료!)
    elif menu == "🔔 알림 발송 현황":
        st.header("🔔 픽업/배송 알림 발송 현황")
        st.write("오늘 및 향후 픽업/배송 예정인 고객들의 알림 상태를 확인합니다.")
        
        try:
            df_orders, _ = get_orders_df(engine)
            if not df_orders.empty:
                # 상태가 완료/취소가 아닌 내역 필터링
                upcoming_orders = df_orders[~df_orders['상태'].isin(['완료', '취소'])]
                st.subheader("📌 픽업/배송 대기 목록")
                st.dataframe(upcoming_orders, use_container_width=True)
                
                st.info("💡 솔라피(Solapi) 카카오 알림톡 서비스 연동 준비 완료 상태입니다.")
            else:
                st.info("현재 대기 중인 픽업/배송 알림이 없습니다.")
        except Exception as e:
            st.error(f"알림 현황을 불러오는 중 오류가 발생했습니다: {e}")

    # 5. 데이터 CSV 백업
    elif menu == "📥 데이터 CSV 백업":
        st.header("📥 데이터 CSV 백업 (엑셀 저장)")
        st.write("엑셀에서 한글이 깨지지 않도록 인코딩(UTF-8 BOM) 처리된 파일입니다.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. 전체 주문 내역")
            try:
                df_orders = pd.read_sql("SELECT * FROM orders ORDER BY id DESC", engine)
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
            except Exception as e:
                st.error(f"오류 발생: {e}")

        with col2:
            st.subheader("2. 전체 고객 목록")
            try:
                df_customers = pd.read_sql("SELECT * FROM customers ORDER BY id DESC", engine)
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
            except Exception as e:
                st.error(f"오류 발생: {e}")
