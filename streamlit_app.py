import streamlit as st
import pandas as pd
from datetime import datetime, time
import pytz
from sqlalchemy import create_engine, text
from streamlit_calendar import calendar

# 페이지 기본 설정
st.set_page_config(page_title="화사한 하루 - 고객/주문 관리", layout="wide", page_icon="💐")

# 스타일 설정
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    /* 아이콘 폰트 깨짐 방지 */
    [class*="material-symbols"], [class*="MaterialIcons"], i {
        font-family: 'Material Symbols Outlined', 'Material Icons' !important;
    }
    
    /* 기본 폰트 설정 */
    html, body, [class*="css"], .stMarkdown, p, div, span, button, input, select {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }

    /* Form 내부 요소 간 위아래 여백 극소화 */
    div[data-testid="stForm"] {
        padding: 0.5rem !important;
    }
    
    /* 세로 블록 간격 축소 (PC/모바일 공통) */
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.2rem !important;
    }

    .element-container {
        margin-bottom: 0.1rem !important;
    }

    /* 입력 폼 라벨 하단 간격 극소화 */
    label, div[data-testid="stWidgetLabel"] {
        margin-bottom: 0px !important;
        padding-bottom: 2px !important;
        font-size: 0.88rem !important;
    }

    /* 모바일 및 PC 공통: 컬럼 간 좌우 여백 축소하여 한 줄에 맞춤 */
    [data-testid="column"] {
        padding-left: 2px !important;
        padding-right: 2px !important;
    }

    /* === PC 화면 전용 (769px 이상) === */
    @media (min-width: 769px) {
        .main .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
            max-width: 100% !important;
        }
        h1 {
            font-size: 2.1rem !important;
            font-weight: 700 !important;
            color: #582C83 !important;
            margin-bottom: 0.8rem !important;
        }
        h2 {
            font-size: 1.4rem !important;
            font-weight: 600 !important;
            color: #2D3748 !important;
        }
    }

    /* === 모바일 전용 (768px 이하) === */
    @media (max-width: 768px) {
        header[data-testid="stHeader"] {
            height: 2.2rem !important;
            min-height: 2.2rem !important;
            background: transparent !important;
            padding: 0.2rem 0.5rem 0 0.5rem !important;
        }

        .main .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 0.3rem !important;
            padding-right: 0.3rem !important;
            margin-top: 0rem !important;
        }

        h1 {
            font-size: 1.25rem !important;
            font-weight: 700 !important;
            color: #582C83 !important;
            margin-top: 0 !important;
            margin-bottom: 0.3rem !important;
            line-height: 1.2 !important;
        }

        h2 {
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            color: #2D3748 !important;
            margin-top: 0.2rem !important;
            margin-bottom: 0.2rem !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 2px !important;
        }
    }

    /* 공통 버튼 스타일 */
    .stButton>button {
        border-radius: 8px !important;
        background-color: #F3EEF9 !important;
        color: #582C83 !important;
        border: 1px solid #E2D5F1 !important;
        font-weight: 600 !important;
    }

    .fc-toolbar-title {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

# 12시간제 AM/PM 과 time 입력값을 결합해 24시간제 time 객체 생성
def parse_time_with_period(period, t_val):
    hour = t_val.hour
    minute = t_val.minute
    if period == "PM" or period == "오후":
        if hour < 12:
            hour += 12
    elif period == "AM" or period == "오전":
        if hour == 12:
            hour = 0
    return time(hour, minute)

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

if engine:
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50);"))
            conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS memo TEXT;"))
            conn.commit()
    except Exception as e:
        pass

st.title("💐 화사한 하루 고객 & 주문 관리")

PAYMENT_OPTIONS = ["네이버", "전화", "입금", "현금", "미결제"]
PRODUCT_OPTIONS = ["꽃다발", "꽃바구니", "햇살콘플라워", "꽃묶음", "식물", "용품", "시즌한정", "기타"]

menu_options = [
    "📝 신규 주문 및 고객 등록", 
    "📋 전체 주문 목록 & 달력", 
    "🎂 고객 관리", 
    "🔔 알림 발송 현황", 
    "📥 데이터 CSV 백업"
]

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
                product_name = st.selectbox("주문 상품명 *", PRODUCT_OPTIONS)
                amount = st.number_input("결제 금액 (원)", min_value=0, step=5000, value=55000)
                payment_method = st.selectbox("결제내역 *", PAYMENT_OPTIONS)
                
            with col2:
                # 접수 일시 (날짜 | AM/PM | 시간 타이핑을 한 행에 구성)
                st.markdown("<label style='font-size:0.88rem;'>접수 일시 *</label>", unsafe_allow_html=True)
                t_col1, t_col2, t_col3 = st.columns([2.2, 1.2, 2.0])
                with t_col1:
                    order_date = st.date_input("접수 날짜", now_kst.date(), label_visibility="collapsed")
                with t_col2:
                    order_period = st.selectbox("접수 AM/PM", ["AM", "PM"], index=0 if now_kst.hour < 12 else 1, label_visibility="collapsed")
                with t_col3:
                    curr_12h = now_kst.hour if now_kst.hour <= 12 else now_kst.hour - 12
                    curr_12h = 12 if curr_12h == 0 else curr_12h
                    order_time_input = st.time_input("접수 시간", time(curr_12h, now_kst.minute), label_visibility="collapsed")
                
                # 픽업 일시 (날짜 | AM/PM | 시간 타이핑을 한 행에 구성)
                st.markdown("<label style='font-size:0.88rem;'>픽업 일시 *</label>", unsafe_allow_html=True)
                p_col1, p_col2, p_col3 = st.columns([2.2, 1.2, 2.0])
                with p_col1:
                    pickup_date = st.date_input("픽업 날짜", now_kst.date(), label_visibility="collapsed")
                with p_col2:
                    pickup_period = st.selectbox("픽업 AM/PM", ["PM", "AM"], index=0, label_visibility="collapsed")
                with p_col3:
                    pickup_time_input = st.time_input("픽업 시간", time(2, 0), label_visibility="collapsed")
                    
                memo = st.text_area("고객 요구사항 / 메모", placeholder="요구사항이나 특이사항을 적어주세요.", height=85)
            
            submit = st.form_submit_button("🌸 주문 저장하기", use_container_width=True)
            if submit:
                if not customer_name:
                    st.warning("고객 이름은 필수 입력 항목입니다.")
                else:
                    try:
                        order_time = parse_time_with_period(order_period, order_time_input)
                        pickup_time = parse_time_with_period(pickup_period, pickup_time_input)
                        
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
                                INSERT INTO orders (customer_id, product_name, product, amount, pickup_datetime, status, payment_method, memo, created_at)
                                VALUES (:cid, :pn, :p, :am, :pdt, :st, :pm, :memo, :cat)
                            """), {
                                "cid": customer_id,
                                "pn": product_name,
                                "p": product_name,
                                "am": int(amount),
                                "pdt": pickup_datetime,
                                "st": payment_method,
                                "pm": payment_method,
                                "memo": memo,
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
                    COALESCE(o.payment_method, o.status, '입금') as payment_method,
                    o.memo as memo,
                    o.customer_id as customer_id
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                ORDER BY o.id DESC
            """
            df_orders = pd.read_sql(query, engine)
            
            def get_pastel_color(pm):
                if pm == '네이버': return "#E0F2FE"
                elif pm == '전화': return "#E9D8FD"
                elif pm == '입금': return "#DCFCE7"
                elif pm == '현금': return "#FEF08A"
                else: return "#FEE2E2"

            tab1, tab2 = st.tabs(["📅 픽업 달력", "📊 전체 주문 목록"])

            # --- [TAB 1] 픽업 달력 ---
            with tab1:
                st.caption("💡 달력 날짜나 주문을 터치하시면 해당 날짜의 픽업 주문 리스트가 나타납니다.")
                
                calendar_events = []
                for _, row in df_orders.iterrows():
                    if pd.notnull(row['pickup_datetime']):
                        p_dt = pd.to_datetime(row['pickup_datetime'])
                        pm = row['payment_method'] or "입금"
                        color = get_pastel_color(pm)
                        calendar_events.append({
                            "id": str(int(row['id'])),
                            "title": f"[{pm}] {row['customer_name']} - {row['product_name']}",
                            "start": p_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                            "backgroundColor": color,
                            "borderColor": color,
                            "textColor": "#2D3748"
                        })
                
                calendar_options = {
                    "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
                    "initialView": "dayGridMonth",
                    "height": 520,
                    "selectable": True
                }
                
                cal_res = calendar(events=calendar_events, options=calendar_options, key="pickup_calendar_v19")
                
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
                            'pickup_datetime': '픽업일시', 'payment_method': '결제내역', 'memo': '메모'
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
                                
                                curr_prod = str(cal_selected_row['product_name'] or "")
                                curr_prod_idx = PRODUCT_OPTIONS.index(curr_prod) if curr_prod in PRODUCT_OPTIONS else PRODUCT_OPTIONS.index("기타")
                                edit_product = st.selectbox("상품명", PRODUCT_OPTIONS, index=curr_prod_idx)
                                edit_amount = st.number_input("금액 (원)", min_value=0, step=5000, value=int(cal_selected_row['amount'] or 55000))
                                
                                curr_pm = cal_selected_row['payment_method']
                                curr_pm_idx = PAYMENT_OPTIONS.index(curr_pm) if curr_pm in PAYMENT_OPTIONS else 0
                                edit_pm = st.selectbox("결제내역", PAYMENT_OPTIONS, index=curr_pm_idx)

                            with col2:
                                # 접수 일시
                                st.markdown("<label style='font-size:0.88rem;'>접수 일시</label>", unsafe_allow_html=True)
                                tc1, tc2, tc3 = st.columns([2.2, 1.2, 2.0])
                                with tc1: edit_order_date = st.date_input("접수 날짜", value=c_cat.date(), label_visibility="collapsed")
                                with tc2: edit_order_period = st.selectbox("접수 AM/PM", ["AM", "PM"], index=0 if c_cat.hour < 12 else 1, key="e_o_p_cal", label_visibility="collapsed")
                                with tc3: 
                                    c_h = c_cat.hour if c_cat.hour <= 12 else c_cat.hour - 12
                                    c_h = 12 if c_h == 0 else c_h
                                    edit_order_time_inp = st.time_input("접수 시간", value=time(c_h, c_cat.minute), key="e_o_t_cal", label_visibility="collapsed")

                                # 픽업 일시
                                st.markdown("<label style='font-size:0.88rem;'>픽업 일시</label>", unsafe_allow_html=True)
                                pc1, pc2, pc3 = st.columns([2.2, 1.2, 2.0])
                                with pc1: edit_pickup_date = st.date_input("픽업 날짜", value=c_pdt.date(), label_visibility="collapsed")
                                with pc2: edit_pickup_period = st.selectbox("픽업 AM/PM", ["AM", "PM"], index=0 if c_pdt.hour < 12 else 1, key="e_p_p_cal", label_visibility="collapsed")
                                with pc3:
                                    p_h = c_pdt.hour if c_pdt.hour <= 12 else c_pdt.hour - 12
                                    p_h = 12 if p_h == 0 else p_h
                                    edit_pickup_time_inp = st.time_input("픽업 시간", value=time(p_h, c_pdt.minute), key="e_p_t_cal", label_visibility="collapsed")

                                edit_memo = st.text_area("고객 요구사항 / 메모", value=str(cal_selected_row['memo'] or ""), height=85)
                            
                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1: update_btn = st.form_submit_button("💾 수정사항 저장", use_container_width=True)
                            with btn_col2: delete_btn = st.form_submit_button("🗑️ 주문 삭제", use_container_width=True)
                            
                            if update_btn:
                                try:
                                    edit_order_time = parse_time_with_period(edit_order_period, edit_order_time_inp)
                                    edit_pickup_time = parse_time_with_period(edit_pickup_period, edit_pickup_time_inp)
                                    
                                    edit_cat = datetime.combine(edit_order_date, edit_order_time)
                                    edit_pdt = datetime.combine(edit_pickup_date, edit_pickup_time)
                                    cid = int(cal_selected_row['customer_id']) if pd.notnull(cal_selected_row['customer_id']) else None
                                    
                                    with engine.connect() as conn:
                                        if cid:
                                            conn.execute(text("UPDATE customers SET name=:n, phone=:p WHERE id=:id"), {"n": edit_name, "p": edit_phone, "id": cid})
                                        
                                        conn.execute(text("""
                                            UPDATE orders 
                                            SET product_name=:pn, product=:pn, amount=:am, pickup_datetime=:pdt, status=:st, payment_method=:pm, memo=:memo, created_at=:cat
                                            WHERE id=:id
                                        """), {"pn": edit_product, "am": int(edit_amount), "pdt": edit_pdt, "st": edit_pm, "pm": edit_pm, "memo": edit_memo, "cat": edit_cat, "id": int(chosen_cal_id)})
                                        conn.commit()
                                    st.success(f"수정이 완료되었습니다. ({chosen_cal_id}번 주문)")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"수정 실패: {e}")
                                
                            if delete_btn:
                                try:
                                    with engine.connect() as conn:
                                        conn.execute(text("DELETE FROM orders WHERE id=:id"), {"id": int(chosen_cal_id)})
                                        conn.commit()
                                    st.warning(f"삭제가 완료되었습니다. ({chosen_cal_id}번 주문)")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"삭제 실패: {e}")
                    else:
                        st.info(f"{clicked_date_str}에는 예정된 픽업 주문이 없습니다.")
                else:
                    st.info("👆 달력에서 특정 날짜나 주문을 선택해 보세요.")

            # --- [TAB 2] 전체 주문 목록 ---
            with tab2:
                st.subheader("📊 전체 주문 목록")
                
                display_df = df_orders.rename(columns={
                    'id': '주문ID', 'customer_name': '고객명', 'phone': '연락처',
                    'product_name': '상품명', 'amount': '금액', 'created_at': '접수일시',
                    'pickup_datetime': '픽업일시', 'payment_method': '결제내역', 'memo': '메모'
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
                            
                            curr_prod = str(selected_row['product_name'] or "")
                            curr_prod_idx = PRODUCT_OPTIONS.index(curr_prod) if curr_prod in PRODUCT_OPTIONS else PRODUCT_OPTIONS.index("기타")
                            edit_product = st.selectbox("상품명", PRODUCT_OPTIONS, index=curr_prod_idx)
                            edit_amount = st.number_input("금액 (원)", min_value=0, step=5000, value=int(selected_row['amount'] or 55000))
                            
                            curr_pm = selected_row['payment_method']
                            curr_pm_idx = PAYMENT_OPTIONS.index(curr_pm) if curr_pm in PAYMENT_OPTIONS else 0
                            edit_pm = st.selectbox("결제내역", PAYMENT_OPTIONS, index=curr_pm_idx)

                        with col2:
                            # 접수 일시
                            st.markdown("<label style='font-size:0.88rem;'>접수 일시</label>", unsafe_allow_html=True)
                            tc1, tc2, tc3 = st.columns([2.2, 1.2, 2.0])
                            with tc1: edit_order_date = st.date_input("접수 날짜", value=curr_cat.date(), label_visibility="collapsed")
                            with tc2: edit_order_period = st.selectbox("접수 AM/PM", ["AM", "PM"], index=0 if curr_cat.hour < 12 else 1, key="e_o_p_all", label_visibility="collapsed")
                            with tc3: 
                                c_h = curr_cat.hour if curr_cat.hour <= 12 else curr_cat.hour - 12
                                c_h = 12 if c_h == 0 else c_h
                                edit_order_time_inp = st.time_input("접수 시간", value=time(c_h, curr_cat.minute), key="e_o_t_all", label_visibility="collapsed")

                            # 픽업 일시
                            st.markdown("<label style='font-size:0.88rem;'>픽업 일시</label>", unsafe_allow_html=True)
                            pc1, pc2, pc3 = st.columns([2.2, 1.2, 2.0])
                            with pc1: edit_pickup_date = st.date_input("픽업 날짜", value=curr_pdt.date(), label_visibility="collapsed")
                            with pc2: edit_pickup_period = st.selectbox("픽업 AM/PM", ["AM", "PM"], index=0 if curr_pdt.hour < 12 else 1, key="e_p_p_all", label_visibility="collapsed")
                            with pc3:
                                p_h = curr_pdt.hour if curr_pdt.hour <= 12 else curr_pdt.hour - 12
                                p_h = 12 if p_h == 0 else p_h
                                edit_pickup_time_inp = st.time_input("픽업 시간", value=time(p_h, curr_pdt.minute), key="e_p_t_all", label_visibility="collapsed")

                            edit_memo = st.text_area("고객 요구사항 / 메모", value=str(selected_row['memo'] or ""), height=85)
                        
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1: update_btn = st.form_submit_button("💾 수정사항 저장", use_container_width=True)
                        with btn_col2: delete_btn = st.form_submit_button("🗑️ 주문 삭제", use_container_width=True)
                        
                        if update_btn:
                            try:
                                edit_order_time = parse_time_with_period(edit_order_period, edit_order_time_inp)
                                edit_pickup_time = parse_time_with_period(edit_pickup_period, edit_pickup_time_inp)
                                
                                edit_cat = datetime.combine(edit_order_date, edit_order_time)
                                edit_pdt = datetime.combine(edit_pickup_date, edit_pickup_time)
                                cid = int(selected_row['customer_id']) if pd.notnull(selected_row['customer_id']) else None
                                
                                with engine.connect() as conn:
                                    if cid:
                                        conn.execute(text("UPDATE customers SET name=:n, phone=:p WHERE id=:id"), {"n": edit_name, "p": edit_phone, "id": cid})
                                    
                                    conn.execute(text("""
                                        UPDATE orders 
                                        SET product_name=:pn, product=:pn, amount=:am, pickup_datetime=:pdt, status=:st, payment_method=:pm, memo=:memo, created_at=:cat
                                        WHERE id=:id
                                    """), {"pn": edit_product, "am": int(edit_amount), "pdt": edit_pdt, "st": edit_pm, "pm": edit_pm, "memo": edit_memo, "cat": edit_cat, "id": int(chosen_id)})
                                    conn.commit()
                                st.success("수정이 완료되었습니다.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"수정 실패: {e}")
                            
                        if delete_btn:
                            try:
                                with engine.connect() as conn:
                                    conn.execute(text("DELETE FROM orders WHERE id=:id"), {"id": int(chosen_id)})
                                    conn.commit()
                                st.warning("삭제가 완료되었습니다.")
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
                    o.created_at as 접수일시, o.pickup_datetime as 픽업일시, COALESCE(o.payment_method, o.status) as 결제내역, o.memo as 메모
                FROM orders o LEFT JOIN customers c ON o.customer_id = c.id
                ORDER BY o.pickup_datetime ASC
            """
            df_upcoming = pd.read_sql(query, engine)
            st.subheader("📌 전체 픽업/배송 알림 현황")
            if not df_upcoming.empty:
                st.dataframe(df_upcoming, use_container_width=True)
            else:
                st.info("현재 등록된 픽업/배송 주문이 없습니다.")
            st.info("💡 카카오 알림톡(솔라피) 연동 대기 중입니다.")
        except Exception as e:
            st.error(f"알림 현황 조회 실패: {e}")

    # 5. 데이터 CSV 백업 및 불러오기 (복원)
    elif menu == "📥 데이터 CSV 백업":
        st.header("📥 데이터 CSV 백업 및 불러오기 (복원)")
        
        tab_export, tab_import = st.tabs(["📤 데이터 내보내기 (백업)", "📥 데이터 불러오기 (복원)"])
        
        with tab_export:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("1. 전체 주문 내역 백업")
                try:
                    df_orders = pd.read_sql("""
                        SELECT o.id as 주문ID, c.name as 고객명, c.phone as 연락처, o.product_name as 상품명, 
                               o.amount as 결제금액, o.created_at as 접수일시, o.pickup_datetime as 픽업일시, 
                               COALESCE(o.payment_method, o.status) as 결제내역, o.memo as 메모
                        FROM orders o LEFT JOIN customers c ON o.customer_id = c.id ORDER BY o.id DESC
                    """, engine)
                    if not df_orders.empty:
                        csv_orders = df_orders.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                        st.download_button("📥 주문 내역 CSV 다운로드", data=csv_orders, file_name="화사한하루_주문내역백업.csv", mime="text/csv", use_container_width=True)
                    else:
                        st.info("등록된 주문 내역이 없습니다.")
                except Exception as e:
                    st.error(f"오류: {e}")

            with col2:
                st.subheader("2. 전체 고객 목록 백업")
                try:
                    df_customers = pd.read_sql("SELECT id as ID, name as 고객명, phone as 연락처 FROM customers ORDER BY id DESC", engine)
                    if not df_customers.empty:
                        csv_customers = df_customers.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                        st.download_button("📥 고객 목록 CSV 다운로드", data=csv_customers, file_name="화사한하루_고객목록백업.csv", mime="text/csv", use_container_width=True)
                    else:
                        st.info("등록된 고객 정보가 없습니다.")
                except Exception as e:
                    st.error(f"오류: {e}")

        with tab_import:
            st.subheader("📥 기존 CSV 백업 파일 불러오기")
            st.caption("⚠️ 업로드한 CSV 파일의 데이터가 DB에 반영되며, 기존 달력 및 목록에 자동으로 즉시 업데이트됩니다.")
            
            upload_type = st.radio("불러올 데이터 유형을 선택하세요", ["주문 내역 CSV", "고객 목록 CSV"], horizontal=True)
            uploaded_file = st.file_uploader("CSV 파일을 선택하세요", type=["csv"])
            
            if uploaded_file is not None:
                try:
                    df_upload = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                    st.write("📋 **불러온 파일 미리보기:**")
                    st.dataframe(df_upload.head(5), use_container_width=True)
                    
                    if st.button("🚀 데이터 DB에 적용하기", use_container_width=True):
                        with engine.connect() as conn:
                            success_cnt = 0
                            
                            if upload_type == "고객 목록 CSV":
                                for _, row in df_upload.iterrows():
                                    c_name = str(row.get('고객명', '')).strip()
                                    c_phone = str(row.get('연락처', '')).strip() if pd.notnull(row.get('연락처')) else ""
                                    if c_name and c_name != 'nan':
                                        res = conn.execute(text("SELECT id FROM customers WHERE name=:n AND phone=:p LIMIT 1"), {"n": c_name, "p": c_phone}).fetchone()
                                        if not res:
                                            conn.execute(text("INSERT INTO customers (name, phone) VALUES (:n, :p)"), {"n": c_name, "p": c_phone})
                                            success_cnt += 1
                                conn.commit()
                                st.success(f"🎉 총 {success_cnt}명의 신규 고객 데이터가 추가되었습니다!")

                            elif upload_type == "주문 내역 CSV":
                                for _, row in df_upload.iterrows():
                                    c_name = str(row.get('고객명', '')).strip()
                                    c_phone = str(row.get('연락처', '')).strip() if pd.notnull(row.get('연락처')) else ""
                                    p_name = str(row.get('상품명', '')).strip()
                                    
                                    if c_name and p_name and c_name != 'nan' and p_name != 'nan':
                                        res = conn.execute(text("SELECT id FROM customers WHERE name=:n AND phone=:p LIMIT 1"), {"n": c_name, "p": c_phone}).fetchone()
                                        if res:
                                            cid = int(res[0])
                                        else:
                                            ins_res = conn.execute(text("INSERT INTO customers (name, phone) VALUES (:n, :p) RETURNING id"), {"n": c_name, "p": c_phone})
                                            cid = int(ins_res.fetchone()[0])
                                        
                                        amount = int(row.get('결제금액', 55000)) if pd.notnull(row.get('결제금액')) else 55000
                                        pm = str(row.get('결제내역', row.get('상태', '입금')))
                                        if pm not in PAYMENT_OPTIONS:
                                            pm = '입금'
                                        memo_val = str(row.get('메모', '')) if pd.notnull(row.get('메모')) else ""
                                        
                                        created_at = pd.to_datetime(row.get('접수일시')).to_pydatetime() if pd.notnull(row.get('접수일시')) else get_kst_now()
                                        pickup_dt = pd.to_datetime(row.get('픽업일시')).to_pydatetime() if pd.notnull(row.get('픽업일시')) else get_kst_now()
                                        
                                        conn.execute(text("""
                                            INSERT INTO orders (customer_id, product_name, product, amount, pickup_datetime, status, payment_method, memo, created_at)
                                            VALUES (:cid, :pn, :p, :am, :pdt, :st, :pm, :memo, :cat)
                                        """), {
                                            "cid": cid, "pn": p_name, "p": p_name,
                                            "am": amount, "pdt": pickup_dt, "st": pm, "pm": pm, "memo": memo_val, "cat": created_at
                                        })
                                        success_cnt += 1
                                conn.commit()
                                st.success(f"🎉 총 {success_cnt}건의 주문 데이터가 추가 및 달력에 적용되었습니다!")
                                
                        st.rerun()

                except Exception as e:
                    st.error(f"CSV 파일 처리 중 오류가 발생했습니다: {e}")
