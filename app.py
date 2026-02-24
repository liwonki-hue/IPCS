import streamlit as st
import os

st.set_page_config(page_title="EPC Integrated Portal", layout="wide")

# 사이드바 메뉴 자동 생성 방지 및 UI 커스텀
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        .stButton>button { height: 100px; font-size: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

def main():
    st.title("🏗️ EPC Project Integrated Control Center")
    st.write("모듈을 선택하면 해당 관리 시스템으로 즉시 연결됩니다.")
    st.divider()

    col1, col2, col3 = st.columns(3)

    # 버튼 클릭 시 st.switch_page 호출
    # 경로는 반드시 "pages/파일명.py" 형태여야 합니다.
    with col1:
        if st.button("📐 DRAWING\nCONTROL", use_container_width=True):
            st.switch_page("pages/1_Drawing_Control.py")

    with col2:
        if st.button("📦 MATERIAL\nCONTROL", use_container_width=True):
            st.switch_page("pages/2_Material_Control.py")

    with col3:
        if st.button("🏗️ CONSTRUCTION\nCONTROL", use_container_width=True):
            st.switch_page("pages/3_Construction.py")

    # 진단용 로그 (접속 불가가 지속될 경우 확인용)
    with st.expander("System Path Check"):
        st.write("Current Root:", os.getcwd())
        if os.path.exists("pages"):
            st.write("Available Pages:", os.listdir("pages"))
        else:
            st.error("'pages' 폴더가 루트 디렉토리에 존재하지 않습니다.")

if __name__ == "__main__":
    main()
