import streamlit as st
import pandas as pd
import os
from modules.doc_control import show_doc_control

# --- 1. Page Configuration & Professional Styling ---
st.set_page_config(
    page_title="IPCS - Integrated Project Control System",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_global_css():
    st.markdown("""
        <style>
        /* Sidebar styling for professional look */
        [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; }
        .st-emotion-cache-16idsys p { font-size: 14px; font-weight: 500; }
        /* Main Title Styling */
        .app-header { font-size: 20px; font-weight: 800; color: #1657d0; padding: 10px 0; border-bottom: 2px solid #1657d0; margin-bottom: 20px; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. Session State Management ---
if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"

# --- 3. Sidebar Navigation ---
with st.sidebar:
    st.markdown("<div style='padding: 10px 0;'><h2 style='color:#1657d0;'>IPCS 2026</h2></div>", unsafe_allow_html=True)
    st.divider()
    
    # Navigation Buttons
    if st.button("📊 Project Dashboard", use_container_width=True, type="secondary" if st.session_state.menu != "Dashboard" else "primary"):
        st.session_state.menu = "Dashboard"
        st.rerun()
        
    if st.button("📂 Drawing Control", use_container_width=True, type="secondary" if st.session_state.menu != "Drawing Control" else "primary"):
        st.session_state.menu = "Drawing Control"
        st.rerun()
        
    if st.button("📦 Material Control", use_container_width=True, type="secondary" if st.session_state.menu != "Material Control" else "primary"):
        st.session_state.menu = "Material Control"
        st.rerun()

    st.spacer(10)
    st.caption("System Version: 2.1.0 (2026)")

# --- 4. Main Content Router ---
apply_global_css()

def main():
    if st.session_state.menu == "Dashboard":
        render_dashboard()
        
    elif st.session_state.menu == "Drawing Control":
        # Drawing Control 모듈 진입 (에러가 발생했던 구역)
        # 괄호 및 문법 오류를 방지하기 위해 로직은 modules/doc_control.py 내부에서 처리합니다.
        show_doc_control()
        
    elif st.session_state.menu == "Material Control":
        render_material_control()

# --- 5. Module Renderers (Placeholders) ---
def render_dashboard():
    st.markdown("<div class='app-header'>Project Management Dashboard</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Progress", "76.5%", "+2.1%")
    col2.metric("Total Drawings", "1,240 EA", "15 EA")
    col3.metric("Material Readiness", "92.0%", "Stable")
    
    st.info("실시간 프로젝트 데이터 요약 화면입니다.")

def render_material_control():
    st.markdown("<div class='app-header'>Material Control System</div>", unsafe_allow_html=True)
    st.warning("Material Control 모듈은 현재 개발 중입니다.")

# --- 6. Program Execution ---
if __name__ == "__main__":
    main()
