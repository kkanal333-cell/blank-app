import streamlit as st
from datetime import datetime, time
import pytz
import streamlit.components.v1 as components

st.set_page_config(page_title="화사한 하루", layout="wide", initial_sidebar_state="expanded")

def get_kst_now():
    return datetime.now(pytz.timezone('Asia/Seoul'))

# 모바일에서 메뉴 터치 시 사이드바가 확실히 닫히도록 개선된 스크립트
mobile_auto_close_script = """
<script>
    function handleMobileSidebar() {
        const doc = window.parent.document;
        // 모바일 화면(1024px 미만)일 때만 작동
        if (window.parent.innerWidth < 1024) {
            const sidebar = doc.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                const radios = sidebar.querySelectorAll('label');
                radios.forEach(label => {
                    if (!label.dataset.mobileCloseBound) {
                        label.dataset.mobileCloseBound = 'true';
                        label.addEventListener('click', () => {
                            setTimeout(() => {
                                const closeBtn = doc.querySelector('[data-testid="collapsedControl"]');
                                if (closeBtn) {
                                    closeBtn.click();
                                } else {
                                    const overlay = doc.querySelector('[data-testid="stSidebarOverlay"]');
                                    if (overlay) overlay.click();
                                }
                            }, 150);
                        });
                    }
                });
            }
        }
        
        // 깨진 텍스트 정리
        const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while (node = walker.nextNode()) {
            if (node.nodeValue && node.nodeValue.includes('keyboard_double')) {
                node.nodeValue = '';
            }
        }
    }
    const observer = new MutationObserver(handleMobileSidebar);
    observer.observe(window.parent.document.body, { childList: true, subtree: true });
    setInterval(handleMobileSidebar, 200);
</script>
"""
components.html(mobile_auto_close_script, height=0, width=0)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    * { font-family: 'Pretendard', sans-serif !important; }

    /* 제목 글씨 크기 및 위치 정돈 */
    .app-title {
        font-size: 1.56rem !important;
        color: #582C83 !important;
        font-weight: 700 !important;
        margin-top: 0.2rem !important;
        margin-bottom: 0.6rem !important;
        line-height: 1.4 !important;
    }
    .section-title {
        font-size: 1.26rem !important;
        color: #582C83 !important;
        font-weight: 600 !important;
        margin-top: 0.6rem !important;
        margin-bottom: 1.0rem !important;
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

    /* 픽업/접수 일시 가로 정렬 및 수직 센터 맞춤 */
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

with st.sidebar:
    st.title("📌 메뉴")
    menu = st.radio("이동할 메뉴를 선택하세요", [
        "📝 신규 주문 및 고객 등록", 
        "📋 전체 주문 목록 & 달력", 
        "🎂 고객 관리", 
        "🔔 알림 발송 현황", 
        "📥 데이터 CSV 백업"
    ])

st.markdown('<div class="app-title">💐 화사한 하루 고객 & 주문 관리</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📝 신규 주문 및 고객 등록</div>', unsafe_allow_html=True)

now_kst = get_kst_now()

with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1: st.text_input("고객 성명 *")
    with c2: st.text_input("휴대폰 번호", value="010-")
    
    c3, c4 = st.columns(2)
    with c3: st.selectbox("주문 상품명 *", ["꽃다발", "꽃바구니", "기타"])
    with c4: st.number_input("결제 금액 (원)", value=55000)
    
    # 픽업 일시
    p1, p2, p3 = st.columns([2.2, 1, 1.4])
    with p1: st.date_input("픽업 일시 *", now_kst.date(), key="p_date")
    with p2: st.selectbox(" ", ["AM", "PM"], index=1, key="p_period", label_visibility="collapsed")
    with p3: st.time_input(" ", time(14, 0), key="p_time", label_visibility="collapsed")
    
    # 접수 일시 (현재 KST 시간 반영)
    curr_hour_24 = now_kst.hour
    is_pm = curr_hour_24 >= 12
    curr_hour_12 = curr_hour_24 if curr_hour_24 <= 12 else curr_hour_24 - 12
    curr_hour_12 = 12 if curr_hour_12 == 0 else curr_hour_12
    
    o1, o2, o3 = st.columns([2.2, 1, 1.4])
    with o1: st.date_input("접수 일시 *", now_kst.date(), key="o_date")
    with o2: st.selectbox("  ", ["AM", "PM"], index=1 if is_pm else 0, key="o_period", label_visibility="collapsed")
    with o3: st.time_input("  ", time(curr_hour_12, now_kst.minute), key="o_time", label_visibility="collapsed")
    
    st.selectbox("결제내역 *", ["네이버", "전화", "입금", "현금"])
    st.text_area("고객 요구사항 / 메모", height=70)
    
    st.form_submit_button("🌸 주문 저장하기", use_container_width=True)
