import streamlit as st
from datetime import datetime, time, date
import pytz
import pandas as pd
import calendar

st.set_page_config(page_title="화사한 하루", layout="wide")

def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

if 'orders' not in st.session_state:
    st.session_state.orders = [
        {
            "고객성명": "김화사",
            "휴대폰번호": "010-1234-5678",
            "주문상품명": "꽃다발",
            "결제금액": 55000,
            "픽업일자": "2026-08-14",
            "픽업일시": "2026-08-14 PM 14:00",
            "접수일시": "2026-08-14 16:04",
            "결제내역": "네이버",
            "메모": "예쁘게 만들어주세요"
        }
    ]

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }

    .app-title {
        font-size: 1.56rem !important;
        color: #582C83 !important;
        font-weight: 700 !important;
        margin-top: -1.0rem !important;
        margin-bottom: 0.6rem !important;
        line-height: 1.4 !important;
    }
    .section-title {
        font-size: 1.26rem !important;
        color: #582C83 !important;
        font-weight: 600 !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.8rem !important;
        line-height: 1.4 !important;
    }
    
    div[data-testid="stVerticalBlock"] { gap: 0.4rem !important; }
    div[data-testid="stForm"] {
        padding: 0.8rem !important;
        border-radius: 10px !important;
        border: 1px solid #E2D5F1 !important;
        background-color: #FAFAFB !important;
    }
    
    label, div[data-testid="stWidgetLabel"] { 
        font-size: 0.78rem !important; 
        font-weight: 600 !important; 
        margin-bottom: 2px !important; 
    }

    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        align-items: flex-end !important;
    }
    div[data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    
    .stTextInput input, .stSelectbox select, .stNumberInput input, .stDateInput input, .stTimeInput input {
        min-height: 38px !important;
        height: 38px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 💐 화사한 하루")
menu = st.sidebar.radio(
    "메뉴 선택", 
    ["신규 주문", "전체 주문 목록 & 달력", "고객 관리", "알림 현황", "데이터 백업"],
    label_visibility="collapsed"
)

st.markdown('<div class="app-title">💐 화사한 하루 고객 & 주문 관리</div>', unsafe_allow_html=True)

if menu == "신규 주문":
    st.markdown('<div class="section-title">📝 신규 주문 및 고객 등록</div>', unsafe_allow_html=True)
    now_kst = get_kst_now()

    curr_hour_24 = now_kst.hour
    is_pm = curr_hour_24 >= 12
    curr_hour_12 = curr_hour_24 if curr_hour_24 <= 12 else curr_hour_24 - 12
    curr_hour_12 = 12 if curr_hour_12 == 0 else curr_hour_12

    with st.form("main_form"):
        c1, c2 = st.columns(2)
        with c1: cust_name = st.text_input("고객 성명 *")
        with c2: cust_phone = st.text_input("휴대폰 번호", value="010-")
        
        c3, c4 = st.columns(2)
        with c3: prod_name = st.selectbox("주문 상품명 *", ["꽃다발", "꽃바구니", "용돈박스", "화분", "근조화환", "축하화환", "기타"])
        with c4: prod_price = st.number_input("결제 금액 (원)", value=55000, step=1000)
        
        p1, p2, p3 = st.columns([2.2, 1, 1.4])
        with p1: p_date = st.date_input("픽업 일시 *", now_kst.date(), key="p_date")
        with p2: p_period = st.selectbox(" ", ["AM", "PM"], index=1, key="p_period", label_visibility="collapsed")
        with p3: p_time = st.time_input(" ", time(14, 0), key="p_time", label_visibility="collapsed")
        
        o1, o2, o3 = st.columns([2.2, 1, 1.4])
        with o1: o_date = st.date_input("접수 일시 *", now_kst.date(), key="o_date")
        with o2: o_period = st.selectbox("  ", ["AM", "PM"], index=1 if is_pm else 0, key="o_period", label_visibility="collapsed")
        with o3: o_time = st.time_input("  ", time(curr_hour_12, now_kst.minute), key="o_time", label_visibility="collapsed")
        
        pay_method = st.selectbox("결제내역 *", ["네이버", "전화", "입금", "현금", "카드"])
        memo = st.text_area("고객 요구사항 / 메모", height=70)
        
        submitted = st.form_submit_button("🌸 주문 저장하기", use_container_width=True)
        if submitted:
            if not cust_name:
                st.warning("고객 성명을 입력해주세요.")
            else:
                new_order = {
                    "고객성명": cust_name,
                    "휴대폰번호": cust_phone,
                    "주문상품명": prod_name,
                    "결제금액": prod_price,
                    "픽업일자": str(p_date),
                    "픽업일시": f"{p_date} {p_period} {p_time.strftime('%H:%M')}",
                    "접수일시": f"{o_date} {o_time.strftime('%H:%M')}",
                    "결제내역": pay_method,
                    "메모": memo
                }
                st.session_state.orders.append(new_order)
                st.success(f"'{cust_name}'님의 주문이 성공적으로 저장되었습니다!")

elif menu == "전체 주문 목록 & 달력":
    st.markdown('<div class="section-title">📋 전체 주문 목록 & 월간 캘린더 및 수정</div>', unsafe_allow_html=True)
    
    if st.session_state.orders:
        df_orders = pd.DataFrame(st.session_state.orders)
        
        col_y, col_m = st.columns(2)
        with col_y:
            sel_year = st.selectbox("연도 선택", [2025, 2026, 2027], index=1)
        with col_m:
            sel_month = st.selectbox("월 선택", list(range(1, 13)), index=get_kst_now().month - 1)
            
        st.write(f"### 📅 {sel_year}년 {sel_month}월 캘린더 뷰")
        
        cal = calendar.monthcalendar(sel_year, sel_month)
        week_days = ["월", "화", "수", "목", "금", "토", "일"]
        
        cols = st.columns(7)
        for i, day_name in enumerate(week_days):
            cols[i].markdown(f"<div style='text-align: center; font-weight: bold; color: #582C83;'>{day_name}</div>", unsafe_allow_html=True)
            
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day == 0:
                        st.write("")
                    else:
                        date_str = f"{sel_year}-{sel_month:02d}-{day:02d}"
                        matched = df_orders[df_orders['픽업일자'] == date_str]
                        count = len(matched)
                        
                        if count > 0:
                            if st.button(f"📌 {day}일 ({count})", key=f"cal_{date_str}", use_container_width=True):
                                st.session_state['selected_cal_date'] = date_str
                        else:
                            st.markdown(f"<div style='text-align: center; padding: 8px; color: #aaa; font-size: 0.8rem;'>{day}</div>", unsafe_allow_html=True)
                            
        st.divider()
        st.subheader("📋 전체 주문 상세 내역 및 수정/삭제")
        
        if 'selected_cal_date' in st.session_state and st.session_state['selected_cal_date']:
            sel_date = st.session_state['selected_cal_date']
            st.info(f"🔍 현재 **{sel_date}** 픽업 주문 내역을 필터링하여 표시 중입니다.")
            filtered_df = df_orders[df_orders['픽업일자'] == sel_date]
            st.dataframe(filtered_df, use_container_width=True)
            if st.button("전체 주문 목록 보기"):
                del st.session_state['selected_cal_date']
                st.rerun()
        else:
            st.dataframe(df_orders, use_container_width=True)
            
        st.divider()
        st.markdown("#### ✏️ 주문 수정 및 삭제 관리")
        order_options = [f"{idx}: {o['고객성명']} ({o['주문상품명']} - {o['픽업일시']})" for idx, o in enumerate(st.session_state.orders)]
        selected_order_str = st.selectbox("수정 또는 삭제할 주문 선택", order_options)
        
        if selected_order_str:
            selected_idx = int(selected_order_str.split(":")[0])
            target_order = st.session_state.orders[selected_idx]
            
            product_list = ["꽃다발", "꽃바구니", "용돈박스", "화분", "근조화환", "축하화환", "기타"]
            p_idx = product_list.index(target_order["주문상품명"]) if target_order["주문상품명"] in product_list else 0
            
            pay_list = ["네이버", "전화", "입금", "현금", "카드"]
            pay_idx = pay_list.index(target_order["결제내역"]) if target_order["결제내역"] in pay_list else 0

            with st.form("edit_form"):
                st.write(f"**[ {target_order['고객성명']}님 주문 수정 ]**")
                
                e1, e2 = st.columns(2)
                with e1: e_name = st.text_input("고객 성명", value=target_order["고객성명"])
                with e2: e_phone = st.text_input("휴대폰 번호", value=target_order["휴대폰번호"])
                
                e3, e4 = st.columns(2)
                with e3: e_prod = st.selectbox("주문 상품명", product_list, index=p_idx)
                with e4: e_price = st.number_input("결제 금액 (원)", value=int(target_order["결제금액"]), step=1000)
                
                try:
                    p_date_str, p_rest = target_order["픽업일시"].split(" ", 1)
                    default_p_date = datetime.strptime(p_date_str, "%Y-%m-%d").date()
                except:
                    default_p_date = now_kst.date()

                ep1, ep2, ep3 = st.columns([2.2, 1, 1.4])
                with ep1: e_p_date = st.date_input("픽업 일자", value=default_p_date)
                with ep2: e_p_period = st.selectbox("픽업 오전오후", ["AM", "PM"], index=1 if "PM" in target_order["픽업일시"] else 0)
                with ep3: e_p_time = st.time_input("픽업 시간", value=time(14, 0))

                try:
                    o_date_str, o_time_str = target_order["접수일시"].split(" ", 1)
                    default_o_date = datetime.strptime(o_date_str, "%Y-%m-%d").date()
                    default_o_time = datetime.strptime(o_time_str, "%H:%M").time()
                except:
                    default_o_date = now_kst.date()
                    default_o_time = now_kst.time()

                eo1, eo2 = st.columns(2)
                with eo1: e_o_date = st.date_input("접수 일자", value=default_o_date)
                with eo2: e_o_time = st.time_input("접수 시간", value=default_o_time)

                e_pay = st.selectbox("결제내역", pay_list, index=pay_idx)
                e_memo = st.text_area("메모", value=target_order["메모"])
                
                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    update_btn = st.form_submit_button("💾 수정사항 저장", use_container_width=True)
                with col_sub2:
                    delete_btn = st.form_submit_button("🗑️ 주문 삭제", use_container_width=True)
                    
                if update_btn:
                    st.session_state.orders[selected_idx].update({
                        "고객성명": e_name,
                        "휴대폰번호": e_phone,
                        "주문상품명": e_prod,
                        "결제금액": e_price,
                        "픽업일자": str(e_p_date),
                        "픽업일시": f"{e_p_date} {e_p_period} {e_p_time.strftime('%H:%M')}",
                        "접수일시": f"{e_o_date} {e_o_time.strftime('%H:%M')}",
                        "결제내역": e_pay,
                        "메모": e_memo
                    })
                    st.success("주문 정보가 성공적으로 수정되었습니다!")
                    st.rerun()
                    
                if delete_btn:
                    del st.session_state.orders[selected_idx]
                    st.warning("선택하신 주문이 삭제되었습니다.")
                    st.rerun()
    else:
        st.info("등록된 주문 내역이 없습니다. '신규 주문' 메뉴에서 첫 주문을 등록해 보세요!")

elif menu == "고객 관리":
    st.markdown('<div class="section-title">🎂 고객 관리</div>', unsafe_allow_html=True)
    if st.session_state.orders:
        df_cust = pd.DataFrame(st.session_state.orders)[["고객성명", "휴대폰번호", "주문상품명", "결제금액", "접수일시"]]
        st.dataframe(df_cust, use_container_width=True)
    else:
        st.info("등록된 고객 정보가 없습니다.")

elif menu == "알림 현황":
    st.markdown('<div class="section-title">🔔 알림 발송 현황</div>', unsafe_allow_html=True)
    st.info("픽업 안내 및 기념일 알림 발송 내역을 관리하는 공간입니다.")

elif menu == "데이터 백업":
    st.markdown('<div class="section-title">📥 데이터 CSV 백업</div>', unsafe_allow_html=True)
    st.write("저장된 전체 주문 및 고객 데이터를 CSV 파일로 다운로드합니다.")
    if st.session_state.orders:
        df_csv = pd.DataFrame(st.session_state.orders)
        csv_data = df_csv.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📂 전체 데이터 CSV 다운로드", 
            data=csv_data, 
            file_name="order_backup.csv", 
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("다운로드할 데이터가 없습니다.")
