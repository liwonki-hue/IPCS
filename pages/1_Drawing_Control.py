import streamlit as st
import pandas as pd
import os

# 데이터 경로 설정 (상위 폴더의 data_storage 참조)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data_storage", "drawing_master.xlsx")

st.title("📐 Drawing Master Control")

if st.sidebar.button("🏠 Back to Portal"):
    st.switch_page("app.py")

@st.cache_data
def load_drawing_master():
    if os.path.exists(DATA_PATH):
        return pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST')
    return None

df = load_drawing_master()

if df is not None:
    st.subheader("Latest Drawing Revision Status")
    st.dataframe(df, use_container_width=True)
else:
    st.error("Drawing Master 파일을 찾을 수 없습니다. data_storage 폴더를 확인하세요.")
