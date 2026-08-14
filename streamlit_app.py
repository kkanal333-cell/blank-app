import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "sqlalchemy", "psycopg2-binary"])
import calendar
import datetime
from datetime import datetime, timedelta, timezone
import os
import re
import pandas as pd
from sqlalchemy import create_engine, text
import streamlit as st
import streamlit.components.v1 as components

# 페이지 기본 설정
st.set_page_config(
    page_title="꽃집 고객/주문 관리 시스템", page_icon="💐", layout="wide"
)

# 🇰🇷 한국 표준시(KST) 시간 설정
KST = timezone(timedelta(hours=9))


def get_kst_today():
    return datetime.now(KST).date()


today = get_kst_today()


# 전화번호 하이픈(-) 자동 변환 함수
def format_phone(phone_str):
    nums = re.sub(r"\D", "", phone_str)
    if len(nums) == 11:
        return f"{nums[:3]}-{nums[3:7]}-{nums[7:]}"
    elif len(nums) == 10:
        if nums.startswith("02"):
            return f"{nums[:2]}-{nums[2:6]}-{nums[6:]}"
        else:
            return f"{nums[:3]}-{nums[3:6]}-{nums[6:]}"
    elif len(nums) == 8:
        return f"{nums[:4]}-{nums[4:]}"
    return phone_str


# 🗄️ Supabase / SQLAlchemy DB 엔진 연결
@st.cache_resource
def get_db_engine():
    if "DB_URL" in st.secrets:
        db_url = st.secrets["DB_URL"]
    else:
        # 로컬 테스트용 SQLite Fallback
        db_url = "sqlite:///flower_shop.db"

    # PostgreSQL 연결 시 sslmode 설정 및 postgresql:// 프로토콜 보정
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return create_engine(db_url, pool_pre_ping=True)


engine = get_db_engine()


# DB 테이블 자동 생성 및 초기화
def init_db():
    with engine.begin() as conn:
        # 고객 테이블
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(50) UNIQUE NOT NULL,
                anniversary VARCHAR(100),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        )

        # 주문 테이블
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
                product_name TEXT,
                product TEXT,
                amount INTEGER DEFAULT 0,
                pickup_datetime VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT '접수',
                notified_1day INTEGER DEFAULT 0,
                notified_1hour INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        )


init_db()

st.title("💐 Flower Shop CRM & 픽업 알림")

# 📌 사이드바 메뉴 및 모바일 자동 닫기 구현
st.sidebar.markdown("### 📌 메뉴 목록")

if "prev_menu" not in st.session_state:
    st.session_state["prev_menu"] = "📝 신규 주문 및 고객 등록"

menu = st.sidebar.radio(
    "메뉴 이동",
    [
        "📝 신규 주문 및 고객 등록",
        "📅 픽업 일정 확인 (달력)",
        "🎉 기념일 고객 관리",
        "🔔 알림 발송 현황",
    ],
    label_visibility="collapsed",
)

if menu != st.session_state["prev_menu"]:
    st.session_state["prev_menu"] = menu
    components.html(
        """
        <script>
            const closeBtn = window.parent.document.querySelector('button[data-testid="stSidebarCollapseButton"]');
            if (closeBtn) {
                closeBtn.click();
            }
        </script>
        """,
        height=0,
        width=0,
    )

# 1. 신규 주문 및 고객 등록
if menu == "📝 신규 주문 및 고객 등록":
    st.subheader("📝 신규 주문 및 고객 등록")

    with st.form("order_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("고객 이름 *")
            phone_input = st.text_input(
                "휴대폰 번호 (하이픈 없이 입력 가능) *"
            )
            anniversary = st.text_input("주요 기념일 (선택, 예: 05-08 어버이날)")

        with col2:
            product_name = st.text_input(
                "주문 상품명 (예: 생일 축하 꽃다발) *"
            )
            amount = st.number_input("결제 금액 (원)", step=10000, value=50000)
            pickup_date = st.date_input("픽업 날짜 *", value=today)
            pickup_time = st.time_input("픽업 시간 *")

        notes = st.text_area("고객 특이사항 / 메모")
        submitted = st.form_submit_button("주문 저장하기")

        if submitted:
            if not name or not phone_input or not product_name:
                st.error("이름, 휴대폰 번호, 상품명은 필수 입력 항목입니다.")
            else:
                formatted_phone = format_phone(phone_input)
                try:
                    with engine.begin() as conn:
                        # 고객 조회
                        result = conn.execute(
                            text(
                                "SELECT id FROM customers WHERE phone = :phone"
                            ),
                            {"phone": formatted_phone},
                        ).fetchone()

                        if result:
                            customer_id = result[0]
                            conn.execute(
                                text(
                                    "UPDATE customers SET name=:name, anniversary=:anniversary, notes=:notes WHERE id=:id"
                                ),
                                {
                                    "name": name,
                                    "anniversary": anniversary,
                                    "notes": notes,
                                    "id": customer_id,
                                },
                            )
                        else:
                            ins_res = conn.execute(
                                text(
                                    "INSERT INTO customers (name, phone, anniversary, notes) VALUES (:name, :phone, :anniversary, :notes) RETURNING id"
                                ),
                                {
                                    "name": name,
                                    "phone": formatted_phone,
                                    "anniversary": anniversary,
                                    "notes": notes,
                                },
                            )
                            customer_id = ins_res.fetchone()[0]

                        pickup_datetime_str = f"{pickup_date} {pickup_time.strftime('%H:%M:%S')}"
                        conn.execute(
                            text("""
                            INSERT INTO orders (customer_id, product_name, product, amount, pickup_datetime) 
                            VALUES (:customer_id, :product_name, :product, :amount, :pickup_datetime)
                        """),
                            {
                                "customer_id": customer_id,
                                "product_name": product_name,
                                "product": product_name,
                                "amount": amount,
                                "pickup_datetime": pickup_datetime_str,
                            },
                        )

                    st.success(
                        f"[{name}] ({formatted_phone}) 님의 주문이 영구 데이터베이스에 성공적으로 저장되었습니다!"
                    )

                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")

# 2. 픽업 일정 확인 (달력)
elif menu == "📅 픽업 일정 확인 (달력)":
    st.subheader("📅 픽업 일정 확인")

    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = today

    current_selected = st.session_state["selected_date"]
    year, month = current_selected.year, current_selected.month

    # 상단 날짜 선택 및 오늘 버튼
    col_date, col_today = st.columns([3, 1])

    with col_date:

        def on_picker_change():
            st.session_state["selected_date"] = st.session_state[
                "temp_date_picker"
            ]

        st.date_input(
            "📅 확인하고 싶은 날짜를 선택하세요",
            value=st.session_state["selected_date"],
            key="temp_date_picker",
            on_change=on_picker_change,
        )

    with col_today:
        st.write("")
        st.write("")
        if st.button("오늘 날짜로 이동", use_container_width=True):
            st.session_state["selected_date"] = today
            st.rerun()

    # 월 이동 컨트롤
    col_prev, col_title, col_next = st.columns([1.2, 3, 1.2])

    with col_prev:
        if st.button("◀ 이전달", use_container_width=True):
            first_day_curr = datetime(
                year, month, 1, tzinfo=KST
            ) - timedelta(days=1)
            st.session_state["selected_date"] = first_day_curr.date()
            st.rerun()

    with col_title:
        st.markdown(
            f"<h4 style='text-align: center; margin: 0; padding-top: 4px; font-size: 15px;'>🗓️ {year}년 {month}월 (오늘: {today.strftime('%m/%d')})</h4>",
            unsafe_allow_html=True,
        )

    with col_next:
        if st.button("다음달 ▶", use_container_width=True):
            last_day_curr = calendar.monthrange(year, month)[1]
            next_month_day = datetime(
                year, month, last_day_curr, tzinfo=KST
            ) + timedelta(days=1)
            st.session_state["selected_date"] = next_month_day.date()
            st.rerun()

    # 월 주문 데이터 로드
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day} 23:59:59"

    try:
        query = text("""
            SELECT o.id, c.name as 고객명, c.phone as 연락처, 
                   COALESCE(NULLIF(o.product_name, ''), o.product, '') as 상품명, 
                   o.amount as 금액, o.pickup_datetime, o.status as 상태
            FROM orders o JOIN customers c ON o.customer_id = c.id
            WHERE o.pickup_datetime BETWEEN :start_date AND :end_date
            ORDER BY o.pickup_datetime ASC
        """)
        with engine.connect() as conn:
            df_month = pd.read_sql_query(
                query,
                conn,
                params={"start_date": start_date, "end_date": end_date},
            )
    except Exception:
        df_month = pd.DataFrame()

    counts_by_date = {}
    if not df_month.empty and "pickup_datetime" in df_month.columns:
        df_month["날짜"] = pd.to_datetime(df_month["pickup_datetime"]).dt.date
        counts_by_date = (
            df_month.groupby("날짜").size().to_dict()
        )

    # 기본 그리드 CSS
    st.markdown(
        """
        <style>
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 2px !important;
        }
        
        [data-testid="stHorizontalBlock"] > div {
            min-width: 0 !important;
            flex: 1 1 0% !important;
            padding: 0px !important;
            margin: 0px !important;
        }

        [data-testid="stHorizontalBlock"] button {
            padding: 2px 0px !important;
            min-height: 38px !important;
            height: 38px !important;
            font-size: 11px !important;
            line-height: 1.1 !important;
            border-radius: 4px !important;
            margin: 0px !important;
            width: 100% !important;
        }

        .cal-header {
            text-align: center;
            font-weight: bold;
            font-size: 12px;
            padding: 4px 0;
            background-color: #f0f2f6;
            border-radius: 4px;
            margin-bottom: 3px;
        }

        div[data-testid="element-container"] {
            margin-bottom: 0px !important;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # 요일 헤더
    days_name = ["일", "월", "화", "수", "목", "금", "토"]
    cols_h = st.columns(7)
    for i, h in enumerate(days_name):
        color = "red" if i == 0 else ("blue" if i == 6 else "#333333")
        cols_h[i].markdown(
            f"<div class='cal-header' style='color:{color};'>{h}</div>",
            unsafe_allow_html=True,
        )

    # 달력 그리드 생성
    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdatescalendar(year, month)

    pickup_button_keys = []
    selected_button_key = f"d_{st.session_state['selected_date']}"

    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day.month == month:
                count = counts_by_date.get(day, 0)
                btn_key = f"d_{day}"

                if count > 0:
                    label = f"{day.day} ({count})"
                    pickup_button_keys.append(btn_key)
                else:
                    label = f"{day.day}"

                with cols[i]:
                    if st.button(label, key=btn_key, use_container_width=True):
                        st.session_state["selected_date"] = day
                        st.rerun()
            else:
                cols[i].write("")

    # 🎨 픽업 날짜(핑크색) 및 선택 날짜(파란색) 동적 CSS 적용
    dynamic_css = "<style>\n"

    for p_key in pickup_button_keys:
        dynamic_css += f"""
        div[data-testid="stButton"] > button[key="{p_key}"],
        button[aria-label*="{p_key}"],
        div.st-key-{p_key} button {{
            background-color: #ff6b81 !important;
            color: white !important;
            border: 1px solid #ff4757 !important;
            font-weight: bold !important;
        }}
        """

    dynamic_css += f"""
    div[data-testid="stButton"] > button[key="{selected_button_key}"],
    button[aria-label*="{selected_button_key}"],
    div.st-key-{selected_button_key} button {{
        background-color: #1f77b4 !important;
        color: white !important;
        border: 1px solid #0056b3 !important;
        font-weight: bold !important;
    }}
    </style>
    """

    st.markdown(dynamic_css, unsafe_allow_html=True)

    # 📋 선택된 날짜 상세 내역 리스트
    st.write("---")
    st.markdown(
        f"### 📋 {st.session_state['selected_date'].strftime('%Y년 %m월 %d일')} 픽업 상세 리스트"
    )

    if not df_month.empty and "날짜" in df_month.columns:
        df_selected = df_month[
            df_month["날짜"] == st.session_state["selected_date"]
        ]
        if not df_selected.empty:
            show_cols = [
                col
                for col in [
                    "pickup_datetime",
                    "고객명",
                    "연락처",
                    "상품명",
                    "금액",
                    "상태",
                ]
                if col in df_selected.columns
            ]
            st.dataframe(df_selected[show_cols], use_container_width=True)
        else:
            st.info(
                f"{st.session_state['selected_date'].strftime('%m월 %d일')}에 예정된 픽업 건이 없습니다."
            )
    else:
        st.info("예정된 픽업 건이 없습니다.")

# 3. 기념일 고객 관리
elif menu == "🎉 기념일 고객 관리":
    st.subheader("🎉 이달의 기념일 고객")

    current_month_str = datetime.now(KST).strftime("%m")
    try:
        with engine.connect() as conn:
            df_customers = pd.read_sql_query(
                text(
                    "SELECT name as 고객명, phone as 연락처, anniversary as 기념일, notes as 메모 FROM customers"
                ),
                conn,
            )
        anniversary_df = df_customers[
            df_customers["기념일"].str.contains(
                f"^{current_month_str}|-{current_month_str}-", na=False
            )
        ]
        if len(anniversary_df) > 0:
            st.dataframe(anniversary_df, use_container_width=True)
        else:
            st.write("이번 달 기념일 등록 고객이 없습니다.")
    except Exception:
        st.write("등록된 고객 정보가 없습니다.")

# 4. 알림 발송 현황
elif menu == "🔔 알림 발송 현황":
    st.subheader("🔔 자동 발송 예정 알림 대상")

    now = datetime.now(KST)
    tomorrow = now + timedelta(days=1)

    st.markdown("##### 📌 24시간 이내 픽업 예정 (1일 전 알림 대상)")
    try:
        query = text("""
            SELECT o.id, c.name as 고객명, c.phone as 연락처, o.pickup_datetime as 픽업일시
            FROM orders o JOIN customers c ON o.customer_id = c.id
            WHERE o.notified_1day = 0 AND o.pickup_datetime BETWEEN :now_str AND :tomorrow_str
        """)
        with engine.connect() as conn:
            df_1day = pd.read_sql_query(
                query,
                conn,
                params={
                    "now_str": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "tomorrow_str": tomorrow.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
        st.dataframe(df_1day, use_container_width=True)
    except Exception:
        st.write("현재 발송 대상 알림이 없습니다.") 