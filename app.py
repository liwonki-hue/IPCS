import streamlit as st
import os

# [1] 페이지 설정
st.set_page_config(page_title="EPC Integrated Portal", layout="wide")

# 사이드바 자동 생성 메뉴 숨기기 (포털 느낌 강조)
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        .module-btn { height: 120px !important; font-size: 20px !important; }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("🏗️ EPC Project Integrated Control Center")
    st.markdown("---")
    
    st.subheader("실행할 관리 모듈을 선택하십시오.")
    
    col1, col2, col3 = st.columns(3)

    # st.switch_page 경로는 반드시 "pages/파일명.py"여야 합니다.
    with col1:
        st.info("📐 **ENGINEERING**")
        if st.button("Drawing Control\n(ISO & Rev)", use_container_width=True):
            st.switch_page("pages/1_Drawing_Control.py")

    with col2:
        st.success("📦 **PROCUREMENT**")
        if st.button("Material Control\n(Inventory & MTO)", use_container_width=True):
            st.switch_page("pages/2_Material_Control.py")

    with col3:
        st.warning("🏗️ **CONSTRUCTION**")
        if st.button("Construction Control\n(Welding & Dia-inch)", use_container_width=True):
            st.switch_page("pages/3_Construction.py")

    # 진단 도구: 접속 안 될 때 서버 상태 확인용
    st.markdown("---")
    with st.expander("🔍 System Diagnostics (Click here if Access Fails)"):
        st.write(f"Current Path: {os.getcwd()}")
        if os.path.exists("pages"):
            st.write("Available Pages in /pages folder:", os.listdir("pages"))
        else:
            st.error("'pages' 폴더가 존재하지 않습니다. 폴더명을 확인하세요.")

if __name__ == "__main__":
    main()
