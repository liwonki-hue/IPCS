import streamlit as st
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data_storage", "material_master.xlsx")

st.title("📦 Material & Inventory Control")

if st.sidebar.button("🏠 Back to Portal"):
    st.switch_page("app.py")

if os.path.exists(DATA_PATH):
    df_mat = pd.read_excel(DATA_PATH)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Items", f"{len(df_mat)} EA")
    m2.metric("In-Stock", f"{len(df_mat[df_mat['Stock'] > 0])} EA")
    m3.metric("Shortage", f"{len(df_mat[df_mat['Stock'] < 0])} EA", delta_color="inverse")
    
    st.divider()
    st.dataframe(df_mat, use_container_width=True)
else:
    st.warning("자재 마스터 데이터 파일이 없습니다.")
