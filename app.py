import streamlit as st
import os

st.set_page_config(page_title="EPC Integrated Portal", layout="wide")

# 사이드바 제거 및 스타일 설정
st.markdown("<style>[data-testid='stSidebarNav'] {display: none;}</style>", unsafe_allow_html=True)

def navigate_to(page_path):
    """경로 유효성 검사 후 페이지 전환"""
    # 1. 파일 존재 여부 확인
    if os.path.exists(page_path):
        try:
            st.switch_page(page_path)
        except Exception as e:
            st.error(f"시스템 전환 중 오류가 발생했습니다: {e}")
    else:
        st.error(f"접근 불가: '{page_path}' 파일을 찾을 수 없습니다.")
        st.info(f"현재 작업 디렉토리: {os.getcwd()}")
        st.info(f"폴더 내 파일 목록: {os.listdir(os.path.dirname(page_path) if os.path.dirname(page_path) else '.')}")

# --- UI 레이아웃 ---
st.title("🏗️ EPC Project Control Center")
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📐 Drawing")
    # 경로를 명확하게 지정 (상대 경로의 시작점 확인)
    if st.button("Open Drawing System", use_container_width=True):
        navigate_to("drawing_control/doc_control.py")

with col2:
    st.subheader("📦 Material")
    if st.button("Open Material System", use_container_width=True):
        navigate_to("material_control/material_app.py")

with col3:
    st.subheader("🏗️ Construction")
    if st.button("Open Construction System", use_container_width=True):
        navigate_to("construction_control/const_app.py")
