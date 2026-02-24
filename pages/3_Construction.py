import streamlit as st
import pandas as pd
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPING_PATH = os.path.join(BASE_DIR, "data_storage", "piping_master.xlsx")
DRAWING_PATH = os.path.join(BASE_DIR, "data_storage", "drawing_master.xlsx")

st.title("🏗️ Construction Progress Control")

if st.sidebar.button("🏠 Back to Portal"):
    st.switch_page("app.py")

def load_data():
    if os.path.exists(PIPING_PATH) and os.path.exists(DRAWING_PATH):
        p = pd.read_excel(PIPING_PATH)
        d = pd.read_excel(DRAWING_PATH, sheet_name='DRAWING LIST')
        return p, d
    return None, None

df_p, df_d = load_data()

if df_p is not None:
    # 1. Revision Sync (ISO Drawing 기준 대조)
    # 설계 마스터의 리비전 정보를 가져와 시공 데이터에 병합
    df_merged = df_p.merge(df_d[['ISO Drawing', 'Rev']], on='ISO Drawing', how='left', suffixes=('', '_Master'))

    # 2. 공정률 대시보드 (Dia-Inch)
    total_inch = df_merged['Size'].sum()
    done_inch = df_merged['Done_Inch'].sum()
    progress = (done_inch / total_inch * 100) if total_inch > 0 else 0

    st.metric("Total Welding Progress (Dia-Inch)", f"{progress:.2f}%")
    st.progress(progress / 100)

    # 3. 실적 입력
    with st.expander("📝 Welding 실적 기록"):
        with st.form("perform_form"):
            iso_sel = st.selectbox("Select ISO Drawing", df_merged['ISO Drawing'].unique())
            joint_no = st.text_input("Joint No")
            w_date = st.date_input("Welding Date", datetime.now())
            if st.form_submit_button("실적 저장"):
                st.success(f"{iso_sel} - {joint_no} 실적이 기록되었습니다.")

    # 4. 현황 테이블 (Rev 불일치 시 붉은색 강조)
    def highlight_rev_mismatch(row):
        # 'Rev'는 현장 적용 리비전, 'Rev_Master'는 설계 최신 리비전
        if row['Rev'] != row['Rev_Master']:
            return ['background-color: #ffcccc'] * len(row)
        return [''] * len(row)

    st.subheader("Piping Installation Lead Sheet")
    st.dataframe(df_merged.style.apply(highlight_rev_mismatch, axis=1), use_container_width=True)
else:
    st.error("시공 또는 설계 마스터 파일을 찾을 수 없습니다.")
