import streamlit as st
import streamlit.components.v1 as components
import os

# 1. 페이지 설정
st.set_page_config(page_title="Piping Material Master", layout="wide")

# 2. 화면의 모든 여백을 강제로 0으로 만드는 강력한 스타일 주입
st.markdown("""
    <style>
        /* 상단 바 및 메뉴 제거 */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 전체 컨테이너 여백 제거 */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
        }
        
        /* 컴포넌트 간격 제거 */
        .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

# 3. HTML 파일 로드
file_name = "Piping_Material_Master_File_2.html"

if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        html_string = f.read()
    
    # 4. 너비 100% 및 가변 높이 설정
    # 높이가 여전히 부족하다면 2000 이상으로 키워보세요.
    components.html(
        html_string,
        height=2000, 
        scrolling=True
    )
else:
    st.error(f"❌ 파일을 찾을 수 없습니다: {file_name}")
