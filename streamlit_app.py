import streamlit as st
import pandas as pd
from datetime import datetime, time
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
        st.header("📝 신규 주문 및 고객 등록")
        
        # 현재 시각 구하기
        now = datetime.now()
        
        with st.form("order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("고객 이름 *")
                phone = st.text_input("휴대폰 번호")
                product_name = st.text_input("주문 상품명 *")
                amount = st.number_input("결제 금액 (원)", min_value=0, step=1000, value=50000)
                
            with col2:
                # 📅 접수 날짜/시간 (기본값: 현재 날짜 및 현재 시간)
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    order_date = st.date_input("접수 날짜", now.date())
                with sub_col2:
                    order_time = st.time_input("접수 시간", now.time())
                
                # 🚚 픽업/배송 날짜/시간
                sub_col3, sub_col4 = st.columns(2)
                with sub_col3:
                    pickup_date = st.date_input("픽업 날짜", now.date())
                with sub_col4:
                    pickup_time = st.time_input("픽업 시간", time(14, 0)) # 기본 오후 2시
                    
                status = st.selectbox("상태", ["접수", "제작중", "배송중", "완료", "취소"])
            
            submit = st.form_submit_button("주문 저장하기", use_container_width=True)
            if submit:
                if not customer_name or not product_name:
                    st.warning("고객 이름과 주문 상품명은 필수 입력 항목입니다.")
                else:
                    try:
                        # 접수 및 픽업 Datetime 결합
                        order_datetime = datetime.combine(order_date, order_time)
                        pickup_datetime = datetime.combine(pickup_date, pickup_time)
                        
                        with engine.connect() as conn:
                            # 1. 고객 확인 및 추가
                            res = conn.execute(text("SELECT id FROM customers WHERE name = :n AND phone = :p LIMIT 1"), {"n": customer_name, "p": phone}).fetchone()
                            if res:
                                customer_id = res[0]
                            else:
                                ins_res = conn.execute(text("INSERT INTO customers (name, phone) VALUES (:n, :p) RETURNING id"), {"n": customer_name, "p": phone})
                                customer_id = ins_res.fetchone()[0]
                            
                            # 2. 주문 등록 (created_at에 접수일시 반영)
                            conn.execute(text("""
                                INSERT INTO orders (customer_id, product_name, product, amount, pickup_datetime, status, created_at)
                                VALUES (:cid, :pn, :p, :am, :pdt, :st, :cat)
                            """), {
                                "cid": customer_id,
                                "pn": product_name,
                                "p": product_name,
                                "am": amount,
                                "pdt": pickup_datetime,
                                "st": status,
                                "cat": order_datetime
                            })
                            conn.commit()
                        st.success(f"'{customer_name}'님의 주문이 성공적으로 저장되었습니다!")
                    except Exception as e:
                        st.error(f"저장 실패: {e}")

    # 2. 주문 내역 관리 (수정/삭제)
    elif menu == "📋 주문 내역 관리 (수정/삭제)":
        st.header("📋 전체 주문 내역 및 수정/삭제")
        
        try:
            query = """
                SELECT 
                    o.id as 주문ID,
                    c.name as 고객명,
                    c.phone as 연락처,
                    o.product_name as 상품명,
                    o.amount as 금액,
                    o.created_at as 접수일시,
                    o.pickup_datetime as 픽업일시,
                    o.status as 상태,
                    o.customer_id
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                ORDER BY o.id DESC
            """
            df_orders = pd.read_sql(query, engine)
            
            display_df = df_orders.drop(columns=['customer_id'], errors='ignore')
            st.dataframe(display_df, use_container_width=True)
            
            if not df_orders.empty:
                st.markdown("---")
                st.subheader("✏️ 주문 수정 및 삭제")
                
                order_ids = df_orders['주문ID'].tolist()
                selected_id = st.selectbox("수정 또는 삭제할 주문 번호(ID) 선택", order_ids)
                
                selected_row = df_orders[df_orders['주문ID'] == selected_id].iloc[0]
                
                curr_cat = pd.to_datetime(selected_row['접수일시']) if pd.notnull(selected_row['접수일시']) else datetime.now()
                curr_pdt = pd.to_datetime(selected_row['픽업일시']) if pd.notnull(selected_row['픽업일시']) else datetime.now()
                
                with st.form("edit_order_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input("고객명", value=str(selected_row['고객명'] or ""))
                        edit_phone = st.text_input("연락처", value=str(selected_row['연락처'] or ""))
                        edit_product = st.text_input("상품명", value=str(selected_row['상품명'] or ""))
                        edit_amount = st.number_input("금액 (원)", min_value=0, step=1000, value=int(selected_row['금액'] or 0))
                    with col2:
                        sub_col1, sub_col2 = st.columns(2)
                        with sub_col1:
                            edit_order_date = st.date_input("접수 날짜", value=curr_cat.date())
                        with sub_col2:
                            edit_order_time = st.time_input("접수 시간", value=curr_cat.time())
                            
                        sub_col3, sub_col4 = st.columns(2)
                        with sub_col3:
                            edit_pickup_date = st.date_input("픽업 날짜", value=curr_pdt.date())
                        with sub_col4:
                            edit_pickup_time = st.time_input("픽업 시간", value=curr_pdt.time())
                        
                        status_list = ["접수", "제작중", "배송중", "완료", "취소"]
                        curr_status = selected_row['상태']
                        curr_status_idx = status_list.index(curr_status) if curr_status in status_list else 0
                        edit_status = st.selectbox("상태", status_list, index=curr_status_idx)
                    
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        update_btn = st.form_submit_button("💾 수정사항 저장", use_container_width=True)
                    with btn_col2:
                        delete_btn = st.form_submit_button("🗑️ 주문 삭제", use_container_width=True)
                    
                    if update_btn:
                        try:
                            edit_cat = datetime.combine(edit_order_date, edit_order_time)
                            edit_pdt = datetime.combine(edit_pickup_date, edit_pickup_time)
                            cid = selected_row['customer_id']
                            
                            with engine.connect() as conn:
                                if pd.notnull(cid):
                                    conn.execute(text("UPDATE customers SET name=:n, phone=:p WHERE id=:id"), {"n": edit_name, "p": edit_phone, "id": cid})
                                
                                conn.execute(text("""
                                    UPDATE orders 
                                    SET product_name=:pn, product=:pn, amount=:am, pickup_datetime=:pdt, status=:st, created_at=:cat
                                    WHERE id=:id
                                """), {"pn": edit_product, "am": edit_amount, "pdt": edit_pdt, "st": edit_status, "cat": edit_cat, "id": selected_id})
                                conn.commit()
                            st.success(f"{selected_id}번 주문이 성공적으로 수정되었습니다!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"수정 실패: {e}")
                        
                    if delete_btn:
                        try:
                            with engine.connect() as conn:
                                conn.execute(text("DELETE FROM orders WHERE id=:id"), {"id": selected_id})
                                conn.commit()
                            st.warning(f"{selected_id}번 주문이 삭제되었습니다.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 실패: {e}")
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
            st.error(f"고객 목록 조회 실패: {e}")

    # 4. 알림 발송 현황
    elif menu == "🔔 알림 발송 현황":
        st.header("🔔 픽업/배송 알림 발송 현황")
        
        try:
            query = """
                SELECT 
                    o.id as 주문ID,
                    c.name as 고객명,
                    c.phone as 연락처,
                    o.product_name as 상품명,
                    o.created_at as 접수일시,
                    o.pickup_datetime as 픽업일시,
                    o.status as 상태
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                WHERE o.status NOT IN ('완료', '취소')
                ORDER BY o.pickup_datetime ASC
            """
            df_upcoming = pd.read_sql(query, engine)
            st.subheader("📌 픽업/배송 대기 목록")
            if not df_upcoming.empty:
                st.dataframe(df_upcoming, use_container_width=True)
            else:
                st.info("현재 대기 중인 픽업/배송 알림이 없습니다.")
            st.info("💡 카카오 알림톡(솔라피) 연동 대기 중입니다.")
        except Exception as e:
            st.error(f"알림 현황 조회 실패: {e}")

    # 5. 데이터 CSV 백업
    elif menu == "📥 데이터 CSV 백업":
        st.header("📥 데이터 CSV 백업 (엑셀 저장)")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. 전체 주문 내역")
            try:
                df_orders = pd.read_sql("""
                    SELECT o.id, c.name as customer_name, c.phone, o.product_name, o.amount, o.created_at as order_datetime, o.pickup_datetime, o.status
                    FROM orders o LEFT JOIN customers c ON o.customer_id = c.id ORDER BY o.id DESC
                """, engine)
                if not df_orders.empty:
                    csv_orders = df_orders.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button("📥 주문 내역 엑셀다운로드", data=csv_orders, file_name="orders_backup.csv", mime="text/csv", use_container_width=True)
                else:
                    st.info("등록된 주문 내역이 없습니다.")
            except Exception as e:
                st.error(f"오류: {e}")

        with col2:
            st.subheader("2. 전체 고객 목록")
            try:
                df_customers = pd.read_sql("SELECT * FROM customers ORDER BY id DESC", engine)
                if not df_customers.empty:
                    csv_customers = df_customers.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button("📥 고객 목록 엑셀다운로드", data=csv_customers, file_name="customers_backup.csv", mime="text/csv", use_container_width=True)
                else:
                    st.info("등록된 고객 정보가 없습니다.")
            except Exception as e:
                st.error(f"오류: {e}")
