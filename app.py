import streamlit as st
import os
import pandas as pd
from modules.doc_control import show_doc_control

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="IPCS 2026 | Engineering Document Control",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Professional UI Styling ---
def apply_global_style():
    st.markdown("""
        <style>
        /* Sidebar 및 메인 컨테이너 간격 최적화 */
        .block-container { padding-top: 1.5rem !important; }
        [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #e6e9ef; }
        
        /* 버튼 공통 스타일 */
        div.stButton > button {
            border-radius: 4px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        /* 테이블 텍스트 가독성 향상 */
        [data-testid="stDataFrame"] { border: 1px solid #e6e9ef; border-radius: 4px; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. Session State Management ---
if 'menu' not in st.session_state:
    st.session_state.menu = "Drawing Control"

# --- 4. Sidebar Navigation ---
def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='color: #1657d0; margin-bottom: 0;'>IPCS 2026</h2>", unsafe_allow_html=True)
        st.caption("Integrated Project Control System")
        st.divider()
        
        # Navigation Buttons
        if st.button("📊 Project Dashboard", use_container_width=True):
            st.session_state.menu = "Dashboard"
            st.rerun()
            
        if st.button("📂 Drawing Control", 
                     use_container_width=True, 
                     type="primary" if st.session_state.menu == "Drawing Control" else "secondary"):
            st.session_state.menu = "Drawing Control"
            st.rerun()
            
        if st.button("📦 Material Control", use_container_width=True):
            st.session_state.menu = "Material Control"
            st.rerun()
            
        if st.button("⚙️ System Settings", use_container_width=True):
            st.session_state.menu = "Settings"
            st.rerun()

        # 하단 정보 (AttributeError 방지를 위해 st.spacer 대신 HTML 사용)
        st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
        st.divider()
        st.caption("Current User: Administrator")
        st.caption("Last Update: 2026-02-23")

# --- 5. Main Execution Logic ---
def main():
    apply_global_style()
    render_sidebar()

    # Route to selected module
    if st.session_state.menu == "Drawing Control":
        # modules/doc_control.py 내의 함수 호출
        try:
            show_doc_control()
        except NameError as e:
            st.error(f"Internal function error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            
    elif st.session_state.menu == "Dashboard":
        st.title("Project Dashboard")
        st.info("준비 중인 모듈입니다.")
        
    elif st.session_state.menu == "Material Control":
        st.title("Material Control")
        st.info("준비 중인 모듈입니다.")
        
    elif st.session_state.menu == "Settings":
        st.title("System Settings")
        st.write("환경 설정을 관리합니다.")

if __name__ == "__main__":
    main()
