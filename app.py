import streamlit as st
import streamlit.components.v1 as components
import os

# 1. 페이지를 전체 화면(Wide) 모드로 강제 설정하고 여백을 줄이는 CSS 주입
st.set_page_config(page_title="Piping Material Master", layout="wide")

# Streamlit 기본 여백(Padding)을 최소화하는 CSS
st.markdown("""
    <style>
    .reportview-container .main .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    iframe {
        width: 100%;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. HTML 파일 로드
file_name = "Piping_Material_Master_File_2.html"

if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        html_string = f.read()
    
    # 3. HTML 표시 (너비는 꽉 차게, 높이는 충분히 크게 설정)
    # height 값을 1500~2000 정도로 높여서 스크롤 불편을 최소화하세요.
    components.html(
        html_string,
        height=1800, 
        scrolling=True
    )
else:
    st.error(f"❌ 파일을 찾을 수 없습니다: {file_name}")
