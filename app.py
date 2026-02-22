import streamlit as st
import pandas as pd

# 페이지 기본 설정
st.set_page_config(
    page_title="IPCS - Integrated Piping Control System",
    page_icon="🏗️",
    layout="wide"
)

# 세션 상태 초기화 (메뉴 선택 관리)
if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"

def set_menu(menu_name):
    st.session_state.menu = menu_name

# --- 메인 대시보드 화면 ---
def show_dashboard():
    st.markdown("<h1 style='text-align: center;'>INTEGRATED PIPING CONTROL SYSTEM</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>(IPCS) Dashboard</p>", unsafe_allow_html=True)
    st.write("---")

    # 2x2 그리드 레이아웃 (제시된 이미지 UI 재현)
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Document Control", use_container_width=True, type="secondary"):
            set_menu("Document Control")
        if st.button("Construction Control", use_container_width=True, type="secondary"):
            set_menu("Construction Control")

    with col2:
        if st.button("Material Control", use_container_width=True, type="secondary"):
            set_menu("Material Control")
        if st.button("Test Control", use_container_width=True, type="secondary"):
            set_menu("Test Control")

# --- 도면 관리 모듈 (Document Control) ---
def show_doc_control():
    st.header("📂 Document Control System")
    st.info("EPC 도면의 리비전 관리 및 최신본 배포 현황을 관리합니다.")
    
    # 상단 탭 구분
    tab1, tab2 = st.tabs(["Drawing Register", "Status Summary"])
    
    with tab1:
        # 신규 도면 업로드 영역
        with st.expander("Update New Drawing / Revision"):
            c1, c2, c3 = st.columns([2, 1, 1])
            doc_no = c1.text_input("Drawing Number (e.g., ISO-10-001)")
            rev = c2.selectbox("Revision", ["0", "1", "2", "3", "A", "B"])
            category = c3.selectbox("Type", ["P&ID", "ISO", "GA", "Support"])
            
            uploaded_file = st.file_uploader("Upload PDF File", type=["pdf"])
            if st.button("Register Document"):
                st.success(f"Success: {doc_no} Rev.{rev} has been updated.")

    with tab2:
        # 도면 마스터 리스트 표시 (샘플 데이터)
        data = {
            "Drawing No": ["ISO-P-001", "ISO-P-002", "PID-01-100"],
            "Description": ["Steam Line 10\"", "Condensate Line 4\"", "Overall P&ID"],
            "Rev": ["1", "0", "A"],
            "Status": ["IFC", "IFC", "IFD"],
            "Last Updated": ["2026-02-15", "2026-02-20", "2026-02-22"]
        }
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

# --- 사이드바 네비게이션 ---
st.sidebar.title("IPCS Navigation")
if st.sidebar.button("🏠 Home Dashboard"):
    set_menu("Dashboard")

st.sidebar.markdown("---")
selected_option = st.sidebar.radio("Go to Module", 
    ["Dashboard", "Document Control", "Material Control", "Construction Control", "Test Control"],
    index=["Dashboard", "Document Control", "Material Control", "Construction Control", "Test Control"].index(st.session_state.menu))

# 로직 연결
if selected_option == "Dashboard":
    show_dashboard()
elif selected_option == "Document Control":
    show_doc_control()
else:
    st.warning(f"{selected_option} 모듈은 현재 개발 중입니다.")
