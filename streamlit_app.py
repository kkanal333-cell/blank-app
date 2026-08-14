import streamlit as st
import pandas as pd
from datetime import datetime, time
import pytz
from sqlalchemy import create_engine, text
from streamlit_calendar import calendar

# 브라우저 탭 타이틀 & 파스텔 테마 스타일 설정
st.set_page_config(page_title="화사한 하루 - 고객/주문 관리 시스템", layout="wide", page_icon="💐")

# 파스텔 / 보라 톤 CSS 스타일링
st.markdown("""
<style>
    /* 메인 타이틀 파스텔 보라 포인트 */
    h1 {
        color: #6B46C1 !important;
    }
    h2, h3 {
        color: #805AD5 !important;
    }
    /* 버튼 및 강조 요소 은은한 보라 스타일 */
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #D6BCFA;
    }
</style>
""", unsafe_allow_html=True)

# 대한민국 한국 표준시(KST) 설정
def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

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

st.title("💐 화사한 하루 고객 & 주문 관리 시스템")

st.sidebar.title("📌 메뉴 목록")
menu = st.sidebar.radio(
    "메뉴 선택", 
    [
        "📝 신규 주문 및 고객 등록", 
        "📋 전체 주문 목록 & 달력", 
        "🎂 고객 관리", 
        "🔔 알림 발송 현황", 
        "📥 데이터 CSV 백업"
    ]
)

if engine:
    # 1. 신규 주문 및 고객 등록
    if menu == "📝 신규 주문 및 고객 등록":
        st.header("📝 신규 주문 및 고객 등록")
        
        now_kst = get_kst_now()
        
        with st.form("order_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("고객 이름 *")
                phone = st.text_input("휴대폰 번호")
                product_name = st.text_input("주문 상품명 *")
                amount = st.number_input("결제 금액 (원)", min_value=0, step=1000, value=50000)
                
            with col2:
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    order_date = st.date_input("접수 날짜", now_kst.date())
                with sub_col2:
                    order_time = st.time_input("접수 시간", now_kst.time())
                
                sub_col3, sub_col4 = st.columns(2)
                with sub_col3:
                    pickup_date = st.date_input("픽업 날짜", now_kst.date())
                with sub_col4:
                    pickup_time = st.time_input("픽업 시간", time(14, 0))
                    
                status = st.selectbox("상태", ["접수", "제작중", "배송중", "완료", "취소"])
            
            submit = st.form_submit_button("🌸 주문 저장하기", use_container_width=True)
            if submit:
                if not customer_name or not product_name:
                    st.warning("고객 이름과 주문 상품명은 필수 입력 항목입니다.")
                else:
                    try:
                        order_datetime = datetime.combine(order_date, order_time)
                        pickup_datetime = datetime.combine(pickup_date, pickup_time)
                        
                        with engine.connect() as conn:
                            res = conn.execute(text("SELECT id FROM customers WHERE name = :n AND phone = :p LIMIT 1"), {"n": customer_name, "p": phone}).fetchone()
                            if res:
                                customer_id = res[0]
                            else:
                                ins_res = conn.execute(text("INSERT INTO customers (name, phone) VALUES (:n, :p) RETURNING id"), {"n": customer_name, "p": phone})
                                customer_id = ins_res.fetchone()[0]
                            
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

    # 2. 주문 내역 관리 및 달력
    elif menu == "📋 전체 주문 목록 & 달력":
        st.header("📋 전체 주문 내역 및 픽업 달력")
        
        try:
            query = """
                SELECT 
                    o.id as id,
                    c.name as customer_name,
                    c.phone as phone,
                    o.product_name as product_name,
                    o.amount as amount,
                    o.created_at as created_at,
                    o.pickup_datetime as pickup_datetime,
                    o.status as status,
                    o.customer_id as customer_id
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                ORDER BY o.id DESC
            """
            df_orders = pd.read_sql(query, engine)
            
            # 파스텔 톤 상태별 칼라 맵핑
            def get_pastel_color(status):
                if status == '접수':
                    return "#9FA8DA"  # 라벤더 블루
                elif status == '제작중':
                    return "#CE93D8"  # 소프트 퍼플/핑크
                elif status == '배송중':
                    return "#80DEEA"  # Soft 파스텔 민트
                elif status == '완료':
                    return "#A5D6A7"  # Soft 파스텔 그린
                else:
                    return "#B0BEC5"  # Soft 세이지 그레이

            # 메뉴 내부 탭 분리: [1] 📅 픽업 달력  [2] 📊 전체 주문 목록
            tab1, tab2 = st.tabs(["📅 픽업 달력", "📊 전체 주문 목록"])

            # --- [TAB 1] 픽업 달력 ---
            with tab1:
                st.caption("💡 달력에서 날짜를 클릭하면 아래에 해당 날짜의 픽업 주문만 정렬되어 나타납니다.")
                
                calendar_events = []
                for _, row in df_orders.iterrows():
                    if pd.notnull(row['pickup_datetime']):
                        p_dt = pd.to_datetime(row['pickup_datetime'])
                        color = get_pastel_color(row['status'])
                        calendar_events.append({
                            "title": f"[{row['status']}] {row['customer_name']} - {row['product_name']}",
                            "start": p_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                            "backgroundColor": color,
                            "borderColor": color,
                            "textColor": "#2C3E50"
                        })
                
                calendar_options = {
                    "headerToolbar": {
                        "left": "prev,next today",
                        "center": "title",
                        "right": "" # month/week/day 삭제
                    },
                    "initialView": "dayGridMonth",
                    "height": 620,
                    "selectable": True
                }
                
                cal_res = calendar(events=calendar_events, options=calendar_options, key="pickup_calendar_v2")
                
                clicked_date_str = None
                if cal_res and cal_res.get("dateClick"):
                    raw_date_str = cal_res["dateClick"]["date"]
                    # ISO 날짜 파싱 후 한국 시간(KST) 기준으로 보정
                    if "T" in raw_date_str:
                        dt_obj = pd.to_datetime(raw_date_str).tz_convert("Asia/Seoul")
                    else:
                        dt_obj = pd.to_datetime(raw_date_str)
                    clicked_date_str = dt_obj.strftime("%Y-%m-%d")

                st.markdown("---")
                
                if clicked_date_str:
                    st.subheader(f"📌 {clicked_date_str} 픽업 주문 리스트")
                    
                    df_orders_temp = df_orders.copy()
                    df_orders_temp['pickup_date_only'] = pd.to_datetime(df_orders_temp['pickup_datetime']).dt.strftime('%Y-%m-%d')
                    day_orders = df_orders_temp[df_orders_temp['pickup_date_only'] == clicked_date_str]
                    
                    if not day_orders.empty:
                        disp_day_df = day_orders.rename(columns={
                            'id': '주문ID',
                            'customer_name': '고객명',
                            'phone': '연락처',
                            'product_name': '상품명',
                            'amount': '금액',
                            'created_at': '접수일시',
                            'pickup_datetime': '픽업일시',
                            'status': '상태'
                        }).drop(columns=['customer_id', 'pickup_date_only'], errors='ignore')
                        
                        st.dataframe(disp_day_df, use_container_width=True)
                    else:
                        st.info(f"{clicked_date_str}에는 예정된 픽업 주문이 없습니다.")
                else:
                    st.info("👆 달력에서 특정 날짜를 클릭하시면 해당 날짜의 픽업 주문 리스트가 여기에 표시됩니다.")

            # --- [TAB 2] 전체 주문 목록 및 수정/삭제 ---
            with tab2:
                st.subheader("📊 전체 주문 목록")
                
                display_df = df_orders.rename(columns={
                    'id': '주문ID',
                    'customer_name': '고객명',
                    'phone': '연락처',
                    'product_name': '상품명',
                    'amount': '금액',
                    'created_at': '접수일시',
                    'pickup_datetime': '픽업일시',
                    'status': '상태'
                }).drop(columns=['customer_id'], errors='ignore')
                
                event = st.dataframe(
                    display_df, 
                    use_container_width=True,
                    selection_mode="single-row",
                    on_select="rerun"
                )
                
                selected_id = None
                if event and event.get("selection") and event["selection"].get("rows"):
                    selected_row_index = event["selection"]["rows"][0]
                    if selected_row_index < len(df_orders):
                        selected_id = df_orders.iloc[selected_row_index]['id']

                # 주문 수정 및 삭제 폼
                if not df_orders.empty:
                    st.markdown("---")
                    st.subheader("✏️ 주문 수정 및 삭제")
                    
                    order_ids = df_orders['id'].tolist()
                    default_index = order_ids.index(selected_id) if (selected_id is not None and selected_id in order_ids) else 0
                    chosen_id = st.selectbox("수정 또는 삭제할 주문 번호(ID) 선택", order_ids, index=default_index)
                    
                    selected_row = df_orders[df_orders['id'] == chosen_id].iloc[0]
                    
                    now_kst = get_kst_now()
                    curr_cat = pd.to_datetime(selected_row['created_at']) if pd.notnull(selected_row['created_at']) else now_kst
                    curr_pdt = pd.to_datetime(selected_row['pickup_datetime']) if pd.notnull(selected_row['pickup_datetime']) else now_kst
                    
                    with st.form("edit_order_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_name = st.text_input("고객명", value=str(selected_row['customer_name'] or ""))
                            edit_phone = st.text_input("연락처", value=str(selected_row['phone'] or ""))
                            edit_product = st.text_input("상품명", value=str(selected_row['product_name'] or ""))
                            edit_amount = st.number_input("금액 (원)", min_value=0, step=1000, value=int(selected_row['amount'] or 0))
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
                            curr_status = selected_row['status']
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
                                    """), {"pn": edit_product, "am": edit_amount, "pdt": edit_pdt, "st": edit_status, "cat": edit_cat, "id": chosen_id})
                                    conn.commit()
                                st.success(f"{chosen_id}번 주문이 성공적으로 수정되었습니다!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"수정 실패: {e}")
                            
                        if delete_btn:
                            try:
                                with engine.connect() as conn:
                                    conn.execute(text("DELETE FROM orders WHERE id=:id"), {"id": chosen_id})
                                    conn.commit()
                                st.warning(f"{chosen_id}번 주문이 삭제되었습니다.")
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
                st.info("💡 추가 고객 정보 관리 항목 준비 중입니다.")
            submit = st.form_submit_button("고객 등록", use_container_width=True)
            if submit and name:
                with engine.connect() as conn:
                    conn.execute(text("INSERT INTO customers (name, phone) VALUES (:n, :p)"), {"n": name, "p": phone})
                    conn.commit()
                st.success(f"'{name}' 고객님이 등록되었습니다!")
                st.rerun()
                
        try:
            df_customers = pd.read_sql("SELECT id as ID, name as 고객명, phone as 연락처 FROM customers ORDER BY id DESC", engine)
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
                    st.download_button("📥 주문 내역 엑셀다운로드", data=csv_orders, file_name="hasahan_orders_backup.csv", mime="text/csv", use_container_width=True)
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
                    st.download_button("📥 고객 목록 엑셀다운로드", data=csv_customers, file_name="hasahan_customers_backup.csv", mime="text/csv", use_container_width=True)
                else:
                    st.info("등록된 고객 정보가 없습니다.")
            except Exception as e:
                st.error(f"오류: {e}")
