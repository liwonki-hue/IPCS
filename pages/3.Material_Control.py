import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 경로 설정 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MASTER_PATH = os.path.join(DATA_DIR, "material_master.xlsx")
LOG_PATH = os.path.join(DATA_DIR, "material_transaction_log.xlsx")

def init_data():
    """데이터 파일이 없을 경우 초기화"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # 트랜잭션 로그 파일(입출고 기록)이 없으면 생성
    if not os.path.exists(LOG_PATH):
        df_log = pd.DataFrame(columns=['Date', 'Type', 'Ident_Code', 'Qty', 'Drawing_No', 'Remark'])
        df_log.to_excel(LOG_PATH, index=False)

def load_data():
    if not os.path.exists(MASTER_PATH):
        st.error("⚠️ 'material_master.xlsx' 파일이 data 폴더에 존재하지 않습니다.")
        return None, None
    
    master = pd.read_excel(MASTER_PATH)
    log = pd.read_excel(LOG_PATH)
    return master, log

def save_log(df):
    df.to_excel(LOG_PATH, index=False)

def run_material_app():
    st.set_page_config(page_title="Material Control System", layout="wide")
    st.title("📦 Material Control & Inventory System")
    st.info(f"📍 Storage: {DATA_DIR}")

    init_data()
    master_df, log_df = load_data()
    
    if master_df is None: return

    # --- 1. 상단 현황 요약 (Summary) ---
    # 입고량 합계
    in_sum = log_df[log_df['Type'] == 'IN'].groupby('Ident_Code')['Qty'].sum()
    # 출고량 합계
    out_sum = log_df[log_df['Type'] == 'OUT'].groupby('Ident_Code')['Qty'].sum()
    
    # 마스터 데이터에 현황 병합
    status_df = master_df.copy()
    status_df['Received'] = status_df['Ident_Code'].map(in_sum).fillna(0)
    status_df['Issued'] = status_df['Ident_Code'].map(out_sum).fillna(0)
    status_df['Stock'] = status_df['Received'] - status_df['Issued']
    status_df['Shortage'] = (status_df['Total_Req'] - status_df['Received']).clip(lower=0)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Req. Items", f"{len(status_df)} EA")
    m2.metric("Total Received", f"{int(status_df['Received'].sum())} EA")
    m3.metric("Current Stock", f"{int(status_df['Stock'].sum())} EA")
    m4.metric("Critical Shortage", f"{int(status_df['Shortage'].sum())} EA", delta_color="inverse")

    st.divider()

    # --- 2. 입/출고 입력 섹션 ---
    tab1, tab2, tab3 = st.tabs(["📊 Inventory Status", "📥 Receiving (입고)", "📤 Issuance (출고)"])

    with tab2:
        st.subheader("Material Receiving Report (MRR)")
        with st.form("in_form"):
            in_date = st.date_input("Receiving Date", datetime.now())
            in_code = st.selectbox("Select Ident Code", master_df['Ident_Code'].unique(), key="in_code")
            in_qty = st.number_input("Quantity", min_value=1, step=1)
            in_remark = st.text_input("Heat No / Remark")
            if st.form_submit_button("Confirm Receiving"):
                new_log = pd.DataFrame([[in_date, 'IN', in_code, in_qty, "-", in_remark]], 
                                     columns=log_df.columns)
                save_log(pd.concat([log_df, new_log], ignore_index=True))
                st.success(f"입고 완료: {in_code}")
                st.rerun()

    with tab3:
        st.subheader("Material Issuance Note (MIN)")
        with st.form("out_form"):
            out_date = st.date_input("Issuance Date", datetime.now())
            out_code = st.selectbox("Select Ident Code", master_df['Ident_Code'].unique(), key="out_code")
            out_dwg = st.text_input("Target ISO Drawing No")
            out_qty = st.number_input("Quantity", min_value=1, step=1)
            
            # 현재고 확인 로직
            current_inv = status_df[status_df['Ident_Code'] == out_code]['Stock'].values[0]
            
            if st.form_submit_button("Confirm Issuance"):
                if current_inv < out_qty:
                    st.error(f"재고 부족! (현재고: {current_inv})")
                else:
                    new_log = pd.DataFrame([[out_date, 'OUT', out_code, out_qty, out_dwg, "Site Issuance"]], 
                                         columns=log_df.columns)
                    save_log(pd.concat([log_df, new_log], ignore_index=True))
                    st.success(f"출고 완료: {out_code} to {out_dwg}")
                    st.rerun()

    with tab1:
        st.subheader("Global Inventory Balance")
        
        # 부족분 하이라이트 스타일링
        def highlight_shortage(s):
            return ['background-color: #ffcccc' if v > 0 else '' for v in s]

        st.dataframe(
            status_df.style.apply(highlight_shortage, subset=['Shortage']),
            use_container_width=True
        )

if __name__ == "__main__":
    run_material_app()
