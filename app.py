import streamlit as st
import os

# 페이지 설정
st.set_page_config(page_title="IPCS 2026", layout="wide")

# 모듈 로드
try:
    from modules.doc_control import show_doc_control
except ImportError as e:
    st.error(f"모듈 로드 실패: {e}")

# 세션 상태 초기화
if 'menu' not in st.session_state:
    st.session_state.menu = "Drawing Control"

# 사이드바 구성
with st.sidebar:
    st.title("IPCS 2026")
    st.divider()
    if st.button("📂 Drawing Control", use_container_width=True, type="primary" if st.session_state.menu == "Drawing Control" else "secondary"):
        st.session_state.menu = "Drawing Control"
        st.rerun()
    
    # st.spacer 대신 HTML로 간격 조절
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    st.caption("System Version: v2.1.0")

# 메인 화면 실행
if st.session_state.menu == "Drawing Control":
    show_doc_control()
