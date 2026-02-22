import streamlit as st
import os

# 페이지 설정
st.set_page_config(page_title="IPCS", layout="wide")

# 모듈 로드 (에러 방지를 위해 try-except 사용)
try:
    from modules.doc_control import show_doc_control
except ImportError:
    st.error("모듈 로드 실패: modules/doc_control.py 파일의 문법을 확인하세요.")

# 사이드바 메뉴 관리
if 'menu' not in st.session_state:
    st.session_state.menu = "Drawing Control"

with st.sidebar:
    st.markdown("### IPCS 2026")
    st.divider()
    if st.button("📂 Drawing Control", use_container_width=True, type="primary" if st.session_state.menu == "Drawing Control" else "secondary"):
        st.session_state.menu = "Drawing Control"
        st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True) # st.spacer 대신 HTML 사용
    st.caption("v2.1.0 Stable")

# 메인 화면 실행
if st.session_state.menu == "Drawing Control":
    show_doc_control()
