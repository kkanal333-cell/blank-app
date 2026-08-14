import streamlit as st
import pandas as pd
from datetime import datetime, time
import pytz
from sqlalchemy import create_engine, text
from streamlit_calendar import calendar

# 페이지 기본 설정
st.set_page_config(page_title="화사한 하루 - 고객/주문 관리", layout="wide", page_icon="💐")

# 세련된 Pretendard 고딕 폰트 및 소프트 파스텔 CSS 적용
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    /* 모바일/PC 사이드바 버튼 및 토글 항상 보이도록 강제 지정 */
    [data-testid="stSidebarNav"] {
        display: block !important;
    }
    
    /* 깔끔한 모던 고딕 폰트 전면 적용 */
    html, body, [class*="css"], .stMarkdown, p, div, span, button, input, select {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', 'Segoe UI', 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif !important;
        color: #2D3748;
    }

    /* 제목 크기 단정하게 축소 */
    h1 {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #582C83 !important; /* 간판 딥 퍼플 포인트 */
        margin-bottom: 0.8rem !important;
    }
    h2 {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #4A5568 !important;
        margin-top: 0.8rem !important;
    }
    h3 {
        font-size: 1.0rem !important;
        font-weight: 600 !important;
        color: #4A5568 !important;
    }

    /* 소프트 파스텔 버튼 스타일 */
    .stButton>button {
        border-radius: 8px !important;
        background-color: #F3EEF9 !important;
        color: #582C83 !important;
        border: 1px solid #E2D5F1 !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #E2D5F1 !important;
        border-color: #D1BCED !important;
        color: #3D1C5C !important;
    }

    /* 달력 커스텀 (소프트 파스텔 톤) */
    .fc-button-primary {
        background-color: #F3EEF9 !important;
        border-color: #E2D5F1 !important;
        color: #582C83 !important;
        box-shadow: none !important;
        text-transform: capitalize !important;
        border-radius: 6px !important;
    }
    .fc-button-primary:hover {
        background-color: #E2D5F1 !important;
        border-color: #D1BCED !important;
        color: #3D1C5C !important;
    }
    .fc-toolbar-title {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #4A5568 !important;
    }
    .fc-theme-standard td, .fc-theme-standard th {
        border-color: #EDF2F7 !important;
    }
    .fc-day-today {
        background-color: #FAF5FF !important;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [aria-selected="true"] {
        color: #582C83 !important;
        font-weight: bold;
        border-bottom: 2px solid #582C83 !important;
    }
</style>
""", unsafe_allow_html=True)

def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

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

st.title("💐 화사한 하루 고객 & 주문 관리")

# 메뉴 목록 정의
menu_options = [
    "📝 신규 주문 및 고객 등록", 
    "📋 전체 주문 목록 & 달력", 
    "🎂 고객 관리", 
    "🔔 알림 발송 현황", 
    "📥 데이터 CSV 백업"
]

# 좌측 사이드바 전용 라디오 버튼 메뉴
with st.sidebar:
    st.title("📌 메뉴")
    menu = st.radio("이동할 메뉴를 선택하세요", menu_options, key="sidebar_main_menu")

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
                                customer_id = int(res[0])
                            else:
                                ins_res = conn.execute(text("INSERT INTO customers (name, phone) VALUES (:n, :p) RETURNING id"), {"n": customer_name, "p": phone})
                                customer_id = int(ins_res.fetchone()[0])
                            
                            conn.execute(text("""
                                INSERT INTO orders (customer_id, product_name, product, amount, pickup_datetime, status, created_at)
                                VALUES (:cid, :pn, :p, :am, :pdt, :st, :cat)
                            """), {
                                "cid": customer_id,
                                "pn": product_name,
                                "p": product_name,
                                "am": int(amount),
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
        st.header("📋 주문 내역 및 픽업 달력")

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
            
            def get_pastel_color(status):
                if status == '접수': return "#E2E8F0"
                elif status == '제작중': return "#E9D8FD"
                elif status == '배송중': return "#E0F2FE"
                elif status == '완료': return "#DCFCE7"
                else: return "#F1F5F9"

            tab1, tab2 = st.tabs(["📅 픽업 달력", "📊 전체 주문 목록"])

            # --- [TAB 1] 픽업 달력 ---
            with tab1:
                st.caption("💡 달력 날짜나 주문을 터치하시면 해당 날짜의 픽업 주문 리스트가 나타납니다.")
                
                calendar_events = []
                for _, row in df_orders.iterrows():
                    if pd.notnull(row['pickup_datetime']):
                        p_dt = pd.to_datetime(row['pickup_datetime'])
                        color = get_pastel_color(row['status'])
                        calendar_events.append({
                            "id": str(int(row['id'])),
                            "title": f"[{row['status']}] {row['customer_name']} - {row['product_name']}",
                            "start": p_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                            "backgroundColor": color,
                            "borderColor": color,
                            "textColor": "#2D3748"
                        })
                
                calendar_options = {
                    "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
                    "initialView": "dayGridMonth",
                    "height": 580,
                    "selectable": True
                }
                
                cal_res = calendar(events=calendar_events, options=calendar_options, key="pickup_calendar_v10")
                
                clicked_date_str = None
                if cal_res and cal_res.get("dateClick"):
                    raw_date_str = cal_res["dateClick"]["date"]
                    dt_obj = pd.to_datetime(raw_date_str).tz_convert("Asia/Seoul") if "T" in raw_date_str else pd.to_datetime(raw_date_str)
                    clicked_date_str = dt_obj.strftime("%Y-%m-%d")
                elif cal_res and cal_res.get("eventClick"):
                    evt_start = cal_res["eventClick"]["event"]["start"]
                    dt_obj = pd.to_datetime(evt_start).tz_convert("Asia/Seoul") if "T" in evt_start else pd.to_datetime(evt_start)
                    clicked_date_str = dt_obj.strftime("%Y-%m-%d")

                st.markdown("---")
                
                if clicked_date_str:
                    st.subheader(f"📌 {clicked_date_str} 픽업 주문 목록")
                    
                    df_orders_temp = df_orders.copy()
                    df_orders_temp['pickup_date_only'] = pd.to_datetime(df_orders_temp['pickup_datetime']).dt.strftime('%Y-%m-%d')
                    day_orders = df_orders_temp[df_orders_temp['pickup_date_only'] == clicked_date_str]
                    
                    if not day_orders.empty:
                        disp_day_df = day_orders.rename(columns={
                            'id': '주문ID', 'customer_name': '고객명', 'phone': '연락처',
                            'product_name': '상품명', 'amount': '금액', 'created_at': '접수일시',
                            'pickup_datetime': '픽업일시', 'status': '상태'
                        }).drop(columns=['customer_id', 'pickup_date_only'], errors='ignore')
                        
                        st.dataframe(disp_day_df, use_container_width=True)

                        st.markdown("---")
                        st.subheader(f"✏️ {clicked_date_str} 주문 수정 및 삭제")
                        
                        day_order_ids = [int(x) for x in day_orders['id'].tolist()]
                        chosen_cal_id = st.selectbox("수정/삭제할 주문 번호(ID) 선택", day_order_ids, key="cal_tab_selectbox")
                        
                        cal_selected_row = day_orders[day_orders['id'] == chosen_cal_id].iloc[0]
                        now_kst = get_kst_now()
                        c_cat = pd.to_datetime(cal_selected_row['created_at']) if pd.notnull(cal_selected_row['created_at']) else now_kst
                        c_pdt = pd.to_datetime(cal_selected_row['pickup_datetime']) if pd.notnull(cal_selected_row['pickup_datetime']) else now_kst
                        
                        with st.form("edit_cal_order_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                edit_name = st.text_input("고객명", value=str(cal_selected_row['customer_name'] or ""))
                                edit_phone = st.text_input("연락처", value=str(cal_selected_row['phone'] or ""))
                                edit_product = st.text_input("상품명", value=str(cal_selected_row['product_name'] or ""))
                                edit_amount = st.number_input("금액 (원)", min_value=0, step=1000, value=int(cal_selected_row['amount'] or 0))
                            with col2:
                                sub_col1, sub_col2 = st.columns(2)
                                with sub_col1: edit_order_date = st.date_input("접수 날짜", value=c_cat.date())
                                with sub_col2: edit_order_time = st.time_input("접수 시간", value=c_cat.time())
                                sub_col3, sub_col4 = st.columns(2)
                                with sub_col3: edit_pickup_date = st.date_input("픽업 날짜", value=c_pdt.date())
                                with sub_col4: edit_pickup_time = st.time_input("픽업 시간", value=c_pdt.time())
                                
                                status_list = ["접수", "제작중", "배송중", "완료", "취소"]
                                curr_status = cal_selected_row['status']
                                curr_status_idx = status_list.index(curr_status) if curr_status in status_list else 0
                                edit_status = st.selectbox("상태", status_list, index=curr_status_idx)
                            
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1: update_btn = st.form_submit_button("💾 수정사항 저장", use_container_width=True)
                            with btn_col2: delete_btn = st.form_submit_button("🗑️ 주문 삭제", use_container_width=True)
                            
                            if update_btn:
                                try:
                                    edit_cat = datetime.combine(edit_order_date, edit_order_time)
                                    edit_pdt = datetime.combine(edit_pickup_date, edit_pickup_time)
                                    cid = int(cal_selected_row['customer_id']) if pd.notnull(cal_selected_row['customer_id']) else None
                                    
                                    with engine.connect() as conn:
                                        if cid:
                                            conn.execute(text("UPDATE customers SET name=:n, phone=:p WHERE id=:id"), {"n": edit_name, "p": edit_phone, "id": cid})
                                        
                                        conn.execute(text("""
                                            UPDATE orders 
                                            SET product_name=:pn, product=:pn, amount=:am, pickup_datetime=:pdt, status=:st, created_at=:cat
                                            WHERE id=:id
                                        """), {"pn": edit_product, "am": int(edit_amount), "pdt": edit_pdt, "st": edit_status, "cat": edit_cat, "id": int(chosen_cal_id)})
                                        conn.commit()
                                    st.success(f"수정이 완료되었습니다. ({chosen_cal_id}번 주문)")
                                except Exception as e:
                                    st.error(f"수정 실패: {e}")
                                
                            if delete_btn:
                                try:
                                    with engine.connect() as conn:
                                        conn.execute(text("DELETE FROM orders WHERE id=:id"), {"id": int(chosen_cal_id)})
                                        conn.commit()
                                    st.warning(f"삭제가 완료되었습니다. ({chosen_cal_id}번 주문)")
                                except Exception as e:
                                    st.error(f"삭제 실패: {e}")
                    else:
                        st.info(f"{clicked_date_str}에는 예정된 픽업 주문이 없습니다.")
                else:
                    st.info("👆 달력에서 특정 날짜나 주문을 선택해 보세요.")

            # --- [TAB 2] 전체 주문 목록 및 수정/삭제 ---
            with tab2:
                st.subheader("📊 전체 주문 목록")
                
                display_df = df_orders.rename(columns={
                    'id': '주문ID', 'customer_name': '고객명', 'phone': '연락처',
                    'product_name': '상품명', 'amount': '금액', 'created_at': '접수일시',
                    'pickup_datetime': '픽업일시', 'status': '상태'
                }).drop(columns=['customer_id'], errors='ignore')
                
                event = st.dataframe(
                    display_df, 
                    use_container_width=True,
                    selection_mode="single-row",
                    on_select="rerun",
                    key="all_orders_dataframe"
                )
                
                order_ids = [int(x) for x in df_orders['id'].tolist()]
                
                if event and event.get("selection") and event["selection"].get("rows"):
                    rows = event["selection"]["rows"]
                    if len(rows) > 0:
                        clicked_idx = rows[0]
                        if clicked_idx < len(df_orders):
                            new_sel_id = int(df_orders.iloc[clicked_idx]['id'])
                            if st.session_state.get("all_tab_selectbox") != new_sel_id:
                                st.session_state["all_tab_selectbox"] = new_sel_id
                                st.rerun()

                if not df_orders.empty:
                    st.markdown("---")
                    
                    if "all_tab_selectbox" not in st.session_state or st.session_state["all_tab_selectbox"] not in order_ids:
                        st.session_state["all_tab_selectbox"] = order_ids[0]
                    
                    chosen_id = st.selectbox(
                        "수정 또는 삭제할 주문 번호(ID) 선택", 
                        order_ids, 
                        key="all_tab_selectbox"
                    )
                    
                    st.subheader(f"✏️ [{chosen_id}번] 주문 수정 및 삭제")
                    
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
                            with sub_col1: edit_order_date = st.date_input("접수 날짜", value=curr_cat.date())
                            with sub_col2: edit_order_time = st.time_input("접수 시간", value=curr_cat.time())
                            sub_col3, sub_col4 = st.columns(2)
                            with sub_col3: edit_pickup_date = st.date_input("픽업 날짜", value=curr_pdt.date())
                            with sub_col4: edit_pickup_time = st.time_input("픽업 시간", value=curr_pdt.time())
                            
                            status_list = ["접수", "제작중", "배송중", "완료", "취소"]
                            curr_status = selected_row['status']
                            curr_status_idx = status_list.index(curr_status) if curr_status in status_list else 0
                            edit_status = st.selectbox("상태", status_list, index=curr_status_idx)
                        
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1: update_btn = st.form_submit_button("💾 수정사항 저장", use_container_width=True)
                        with btn_col2: delete_btn = st.form_submit_button("🗑️ 주문 삭제", use_container_width=True)
                        
                        if update_btn:
                            try:
                                edit_cat = datetime.combine(edit_order_date, edit_order_time)
                                edit_pdt = datetime.combine(edit_pickup_date, edit_pickup_time)
                                cid = int(selected_row['customer_id']) if pd.notnull(selected_row['customer_id']) else None
                                
                                with engine.connect() as conn:
                                    if cid:
                                        conn.execute(text("UPDATE customers SET name=:n, phone=:p WHERE id=:id"), {"n": edit_name, "p": edit_phone, "id": cid})
                                    
                                    conn.execute(text("""
                                        UPDATE orders 
                                        SET product_name=:pn, product=:pn, amount=:am, pickup_datetime=:pdt, status=:st, created_at=:cat
                                        WHERE id=:id
                                    """), {"pn": edit_product, "am": int(edit_amount), "pdt": edit_pdt, "st": edit_status, "cat": edit_cat, "id": int(chosen_id)})
                                    conn.commit()
                                st.success("수정이 완료되었습니다.")
                            except Exception as e:
                                st.error(f"수정 실패: {e}")
                            
                        if delete_btn:
                            try:
                                with engine.connect() as conn:
                                    conn.execute(text("DELETE FROM orders WHERE id=:id"), {"id": int(chosen_id)})
                                    conn.commit()
                                st.warning("삭제가 완료되었습니다.")
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
                    o.id as 주문ID, c.name as 고객명, c.phone as 연락처, o.product_name as 상품명,
                    o.created_at as 접수일시, o.pickup_datetime as 픽업일시, o.status as 상태
                FROM orders o LEFT JOIN customers c ON o.customer_id = c.id
                WHERE o.status NOT IN ('완료', '취소') ORDER BY o.pickup_datetime ASC
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
                    SELECT o.id as 주문ID, c.name as 고객명, c.phone as 연락처, o.product_name as 상품명, o.amount as 결제금액, o.created_at as 접수일시, o.pickup_datetime as 픽업일시, o.status as 상태
                    FROM orders o LEFT JOIN customers c ON o.customer_id = c.id ORDER BY o.id DESC
                """, engine)
                if not df_orders.empty:
                    csv_orders = df_orders.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button("📥 주문 내역 엑셀다운로드", data=csv_orders, file_name="화사한하루_주문내역백업.csv", mime="text/csv", use_container_width=True)
                else:
                    st.info("등록된 주문 내역이 없습니다.")
            except Exception as e:
                st.error(f"오류: {e}")

        with col2:
            st.subheader("2. 전체 고객 목록")
            try:
                df_customers = pd.read_sql("SELECT id as ID, name as 고객명, phone as 연락처 FROM customers ORDER BY id DESC", engine)
                if not df_customers.empty:
                    csv_customers = df_customers.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button("📥 고객 목록 엑셀다운로드", data=csv_customers, file_name="화사한하루_고객목록백업.csv", mime="text/csv", use_container_width=True)
                else:
                    st.info("등록된 고객 정보가 없습니다.")
            except Exception as e:
                st.error(f"오류: {e}")