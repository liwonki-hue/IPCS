import streamlit as st
import streamlit.components.v1 as components
import os

# 1. 페이지 설정: 화면을 꽉 차게 설정
st.set_page_config(page_title="Piping Material Master", layout="wide")

# 2. HTML 파일 존재 여부 확인 및 로드
file_name = "Piping_Material_Master_File_2.html"

if os.path.exists(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        html_string = f.read()
    
    # 3. HTML 렌더링
    # 기존 HTML의 JS가 작동하려면 충분한 높이(height)가 필요합니다.
    st.markdown("### 🏗️ Piping Material Master System")
    
    # components.html을 통해 HTML 소스를 직접 웹에 주입합니다.
    components.html(
        html_string,
        height=1200,   # 화면 높이에 맞춰 조정하세요
        scrolling=True # 내부 스크롤 허용
    )
else:
    st.error(f"❌ 파일을 찾을 수 없습니다: {file_name}")
    st.info("GitHub 저장소에 HTML 파일이 업로드되었는지, 파일 이름이 정확한지 확인해 주세요.")
