import streamlit as st
from modules.doc_control import show_doc_control

# 페이지 구성 설정
st.set_page_config(
    page_title="IPCS 2026 | Engineering Document Control",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 관리 (메뉴 전환)
if 'menu' not in st.session_state:
    st.session_state.menu = "Drawing Control"

# 사이드바 레이아웃
with st.sidebar:
    st.markdown("<h2 style='color: #1657d0;'>IPCS 2026</h2>", unsafe_allow_html=True)
    st.divider()
    
    # 메뉴 버튼 (선택된 메뉴 강조 스타일)
    if st.button("📂 Drawing Control", use_container_width=True, 
                 type="primary" if st.session_state.menu == "Drawing Control" else "secondary"):
        st.session_state.menu = "Drawing Control"
        st.rerun()

    # 하단 정보 (st.spacer 대신 HTML 간격 사용으로 AttributeError 방지)
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    st.divider()
    st.caption("v2.1.0 Stable | Administrator")

# 메인 기능 실행
if st.session_state.menu == "Drawing Control":
    show_doc_control()
