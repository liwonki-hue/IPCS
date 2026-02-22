import streamlit as st
import streamlit.components.v1 as components

# 1. 페이지 설정 (화면을 넓게 사용)
st.set_page_config(page_title="Piping Material Master", layout="wide")

# 2. HTML 파일 읽기
# GitHub 저장소에 'Piping_Material_Master_File_2.html' 파일이 함께 있어야 합니다.
def load_html():
    try:
        with open("Piping_Material_Master_File_2.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h3>HTML 파일을 찾을 수 없습니다. GitHub 저장소에 파일을 업로드했는지 확인해주세요.</h3>"

html_content = load_html()

# 3. 화면에 HTML 표시
# 너비(width)와 높이(height)는 필요에 따라 조절 가능합니다.
st.markdown("### 🏗️ Piping Material Management System (Legacy Mode)")
components.html(html_content, height=900, scrolling=True)
