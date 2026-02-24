import streamlit as st
import os

# [필독] set_page_config는 오직 메인 app.py 최상단에만 위치해야 함
st.set_page_config(page_title="EPC Integrated Portal", layout="wide")

# 사이드바 자동 메뉴 숨기기 및 스타일링
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        .main-title { font-size: 38px; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 30px; }
        .stButton>button { height: 120px; font-size: 20px; font-weight: bold; border-radius: 12px; }
    </style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<p class="main-title">🏗️ EPC Project Integrated Control Portal</p>', unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("📐 **Engineering**")
        if st.button("Drawing & Rev.\nControl", use_container_width=True):
            st.switch_page("pages/1_Drawing_Control.py")

    with col2:
        st.success("📦 **Procurement**")
        if st.button("Material & Stock\nControl", use_container_width=True):
            st.switch_page("pages/2_Material_Control.py")

    with col3:
        st.warning("🏗️ **Construction**")
        if st.button("Construction\nProgress", use_container_width=True):
            st.switch_page("pages/3_Construction.py")

    st.divider()
    st.caption(f"System Operational | Working Dir: {os.getcwd()}")

if __name__ == "__main__":
    main()
