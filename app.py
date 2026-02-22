import streamlit as st
from modules.doc_control import show_doc_control

# 1. 페이지 설정
st.set_page_config(page_title="IPCS - Piping Control System", layout="wide")

# 2. 메뉴 선택 상태 관리
if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"

# 3. 사이드바 메뉴 (라디오 버튼과 세션 상태 동기화)
st.sidebar.title("IPCS Navigation")
choice = st.sidebar.radio("Go to Module", 
    ["Dashboard", "Document Control", "Material Control", "Construction Control", "Test Control"],
    index=["Dashboard", "Document Control", "Material Control", "Construction Control", "Test Control"].index(st.session_state.menu)
)

# 사이드바에서 메뉴를 직접 바꾸면 세션 상태도 업데이트
if choice != st.session_state.menu:
    st.session_state.menu = choice
    st.rerun()

# 4. 화면 출력 로직
if st.session_state.menu == "Dashboard":
    st.markdown("<h1 style='text-align: center;'>INTEGRATED PIPING CONTROL SYSTEM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>(IPCS) Dashboard</p>", unsafe_allow_html=True)
    st.write("---")

    # 2x2 버튼 레이아웃
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Document Control", use_container_width=True, type="primary"):
            st.session_state.menu = "Document Control"
            st.rerun()
        if st.button("Construction Control", use_container_width=True):
            st.session_state.menu = "Construction Control"
            st.rerun()

    with col2:
        if st.button("Material Control", use_container_width=True):
            st.session_state.menu = "Material Control"
            st.rerun()
        if st.button("Test Control", use_container_width=True):
            st.session_state.menu = "Test Control"
            st.rerun()

elif st.session_state.menu == "Document Control":
    # 📂 도면 관리 모듈 호출
    show_doc_control()

else:
    st.title(f"📂 {st.session_state.menu}")
    st.info("이 모듈은 현재 개발 중입니다.")
    if st.button("홈으로 돌아가기"):
        st.session_state.menu = "Dashboard"
        st.rerun()
