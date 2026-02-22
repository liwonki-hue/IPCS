import streamlit as st
import pandas as pd
import os
from modules.doc_control import show_doc_control

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="IPCS - Integrated Project Control System",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Global CSS Styling ---
def apply_global_css():
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { background-color: #f8f9fa; border-right: 1px solid #dee2e6; }
        .app-header { font-size: 20px; font-weight: 800; color: #1657d0; padding: 10px 0; border-bottom: 2px solid #1657d0; margin-bottom: 20px; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. Session State & Sidebar Navigation ---
if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"

apply_global_css()

with st.sidebar:
    st.markdown("<div style='padding: 10px 0;'><h2 style='color:#1657d0;'>IPCS 2026</h2></div>", unsafe_allow_html=True)
    st.divider()
    
    # Navigation Buttons
    if st.button("📊 Project Dashboard", use_container_width=True, type="primary" if st.session_state.menu == "Dashboard" else "secondary"):
        st.session_state.menu = "Dashboard"
        st.rerun()
        
    if st.button("📂 Drawing Control", use_container_width=True, type="primary" if st.session_state.menu == "Drawing Control" else "secondary"):
        st.session_state.menu = "Drawing Control"
        st.rerun()
        
    if st.button("📦 Material Control", use_container_width=True, type="primary" if st.session_state.menu == "Material Control" else "secondary"):
        st.session_state.menu = "Material Control"
        st.rerun()

    # AttributeError 수정: st.spacer 대신 st.markdown 혹은 st.container 사용
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("System Version: 2.1.0 (2026)")

# --- 4. Main Content Router ---
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

# 메인 실행 로직
if st.session_state.menu == "Dashboard":
    render_dashboard()
elif st.session_state.menu == "Drawing Control":
    # 별도의 탭 구성 없이 모듈 내부에서 탭과 테이블(하단 네비게이션 포함)을 렌더링하도록 호출
    show_doc_control()
elif st.session_state.menu == "Material Control":
    render_material_control()
