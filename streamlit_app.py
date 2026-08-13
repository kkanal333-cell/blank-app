import calendar
from datetime import datetime, timedelta
import re
import pandas as pd
import pytz
import sqlite3
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="꽃집 고객/주문 관리 시스템", page_icon="💐", layout="wide"
)

# 🇰🇷 한국 표준시(KST) 시간 설정
KST = pytz.timezone("Asia/Seoul")


def get_kst_today():
    return datetime.now(KST).date()


# 한국 기준 오늘 날짜
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


# DB 연결 및 보정
def init_db():
    conn = sqlite3.connect("flower_shop.db", check_same_thread=False)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            anniversary TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product_name TEXT,
            product TEXT,
            amount INTEGER DEFAULT 0,
            pickup_datetime TEXT NOT NULL,
            status TEXT DEFAULT '접수',
            notified_1day INTEGER DEFAULT 0,
            notified_1hour INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    """)

    c.execute("PRAGMA table_info(orders)")
    columns = [col[1] for col in c.fetchall()]

    if "product_name" not in columns:
        c.execute(
            "ALTER TABLE orders ADD COLUMN product_name TEXT DEFAULT ''"
        )
    if "product" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN product TEXT DEFAULT ''")
    if "amount" not in columns:
        c.execute("ALTER TABLE orders ADD COLUMN amount INTEGER DEFAULT 0")

    conn.commit()
    return conn


conn = init_db()

st.title("💐 Flower Shop CRM & 픽업 알림")

# 사이드바 메뉴
st.sidebar.markdown("### 📌 메뉴 목록")
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
            # 한국 기준 오늘 날짜 자동 적용
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
                    c = conn.cursor()
                    c.execute(
                        "SELECT id FROM customers WHERE phone = ?",
                        (formatted_phone,),
                    )
                    row = c.fetchone()

                    if row:
                        customer_id = row[0]
                        c.execute(
                            "UPDATE customers SET name=?, anniversary=?, notes=? WHERE id=?",
                            (name, anniversary, notes, customer_id),
                        )
                    else:
                        c.execute(
                            "INSERT INTO customers (name, phone, anniversary, notes) VALUES (?, ?, ?, ?)",
                            (name, formatted_phone, anniversary, notes),
                        )
                        customer_id = c.lastrowid

                    pickup_datetime_str = f"{pickup_date} {pickup_time.strftime('%H:%M:%S')}"
                    c.execute(
                        """
                        INSERT INTO orders (customer_id, product_name, product, amount, pickup_datetime) 
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            customer_id,
                            product_name,
                            product_name,
                            amount,
                            pickup_datetime_str,
                        ),
                    )

                    conn.commit()
                    st.success(
                        f"[{name}] ({formatted_phone}) 님의 주문이 성공적으로 저장되었습니다!"
                    )

                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")

# 2. 픽업 일정 확인 (모바일 완전 최적화 UI)
elif menu == "📅 픽업 일정 확인 (달력)":
    st.subheader("📅 픽업 일정 확인")

    # 선택한 날짜 세션 초기화
    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = today

    # 상단 날짜 이동 및 선택 컨트롤
    col_date, col_today_btn = st.columns([3, 1])

    with col_date:
        selected_date = st.date_input(
            "📅 확인하고 싶은 날짜를 선택하세요",
            value=st.session_state["selected_date"],
            key="pickup_date_picker",
        )
        st.session_state["selected_date"] = selected_date

    with col_today_btn:
        st.write("")  # 여백 맞춤
        st.write("")
        if st.button("오늘 날짜로 이동", use_container_width=True):
            st.session_state["selected_date"] = today
            st.rerun()

    # 해당 월의 전체 주문 데이터 가져오기
    year, month = selected_date.year, selected_date.month
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day} 23:59:59"

    try:
        df_month = pd.read_sql_query(
            f"""
            SELECT o.id, c.name as 고객명, c.phone as 연락처, 
                   COALESCE(NULLIF(o.product_name, ''), o.product, '') as 상품명, 
                   o.amount as 금액, o.pickup_datetime, o.status as 상태
            FROM orders o JOIN customers c ON o.customer_id = c.id
            WHERE o.pickup_datetime BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY o.pickup_datetime ASC
        """,
            conn,
        )
    except Exception:
        df_month = pd.DataFrame()

    counts_by_date = {}
    if not df_month.empty and "pickup_datetime" in df_month.columns:
        df_month["날짜"] = pd.to_datetime(df_month["pickup_datetime"]).dt.date
        counts_by_date = (
            df_month.groupby("날짜").size().to_dict()
        )

    # 📌 깔끔한 월간 현황 요약 요약표 (깨짐 없는 HTML 표)
    st.markdown(
        f"#### 🗓️ {year}년 {month}월 픽업 현황 요약 (오늘: {today.strftime('%m월 %d일')})"
    )

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdatescalendar(year, month)

    html_code = """
    <style>
        .cal-table { width: 100%; border-collapse: collapse; text-align: center; }
        .cal-table th { background-color: #f0f2f6; padding: 6px; font-size: 13px; border: 1px solid #ddd; }
        .cal-table td { width: 14.28%; height: 42px; vertical-align: top; border: 1px solid #eee; padding: 2px; font-size: 12px; }
        .is-today { background-color: #ffeeb3 !important; font-weight: bold; }
        .is-selected { border: 2px solid #ff4b4b !important; font-weight: bold; }
        .badge { background-color: #ff4b4b; color: white; border-radius: 6px; padding: 1px 3px; font-size: 10px; }
        .other-m { color: #ccc; }
    </style>
    <table class="cal-table">
        <thead><tr>
            <th style="color:red;">일</th><th>월</th><th>화</th><th>수</th><th>목</th><th>금</th><th style="color:blue;">토</th>
        </tr></thead><tbody>
    """

    for week in month_days:
        html_code += "<tr>"
        for day in week:
            if day.month == month:
                count = counts_by_date.get(day, 0)
                badge = (
                    f'<br><span class="badge">{count}건</span>'
                    if count > 0
                    else ""
                )

                classes = []
                if day == today:
                    classes.append("is-today")
                if day == selected_date:
                    classes.append("is-selected")

                class_attr = (
                    f'class="{" ".join(classes)}"' if classes else ""
                )
                html_code += f"<td {class_attr}>{day.day}{badge}</td>"
            else:
                html_code += f'<td class="other-m">{day.day}</td>'
        html_code += "</tr>"
    html_code += "</tbody></table>"

    st.markdown(html_code, unsafe_allow_html=True)
    st.write("")

    # 📋 선택된 날짜 상세 내역 리스트
    st.write("---")
    st.markdown(
        f"### 📋 {selected_date.strftime('%Y년 %m월 %d일')} 픽업 상세 리스트"
    )

    if not df_month.empty and "날짜" in df_month.columns:
        df_selected = df_month[df_month["날짜"] == selected_date]
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
                f"{selected_date.strftime('%m월 %d일')}에 예정된 픽업 건이 없습니다."
            )
    else:
        st.info("예정된 픽업 건이 없습니다.")

# 3. 기념일 고객 관리
elif menu == "🎉 기념일 고객 관리":
    st.subheader("🎉 이달의 기념일 고객")

    current_month_str = datetime.now(KST).strftime("%m")
    try:
        df_customers = pd.read_sql_query(
            "SELECT name as 고객명, phone as 연락처, anniversary as 기념일, notes as 메모 FROM customers",
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
        df_1day = pd.read_sql_query(
            f"""
            SELECT o.id, c.name as 고객명, c.phone as 연락처, o.pickup_datetime as 픽업일시
            FROM orders o JOIN customers c ON o.customer_id = c.id
            WHERE o.notified_1day = 0 AND o.pickup_datetime BETWEEN '{now.strftime('%Y-%m-%d %H:%M:%S')}' AND '{tomorrow.strftime('%Y-%m-%d %H:%M:%S')}'
        """,
            conn,
        )
        st.dataframe(df_1day, use_container_width=True)
    except Exception:
        st.write("현재 발송 대상 알림이 없습니다.")