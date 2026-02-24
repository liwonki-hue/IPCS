import os
import pandas as pd

# [중요] 현재 파일(pages/xx.py) 위치를 기준으로 상위 폴더(root)의 데이터 폴더 탐색
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 각 모듈별 데이터 경로 정의 (구조에 맞춰 수정)
DRAWING_DATA_PATH = os.path.join(BASE_DIR, 'drawing_control', 'data', 'drawing_master.xlsx')
MATERIAL_DATA_PATH = os.path.join(BASE_DIR, 'material_control', 'data', 'material_master.xlsx')
PIPING_DATA_PATH = os.path.join(BASE_DIR, 'construction_control', 'data', 'piping_master.xlsx')


import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 경로 설정 (상대 경로 기준) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PIPING_PATH = os.path.join(DATA_DIR, "piping_master.xlsx")
DRAWING_PATH = os.path.join(DATA_DIR, "drawing_master.xlsx")

def load_piping_data():
    """시공 및 설계 마스터 데이터 병합 로드"""
    if not os.path.exists(PIPING_PATH) or not os.path.exists(DRAWING_PATH):
        st.error("⚠️ 'data' 폴더 내 마스터 파일(piping/drawing)을 확인하십시오.")
        return None

    p_df = pd.read_excel(PIPING_PATH)
    d_df = pd.read_excel(DRAWING_PATH)
    
    # ISO_Drawing 기준으로 최신 리비전(Current_Rev) 정보를 Piping 데이터에 병합
    return p_df.merge(d_df[['ISO_Drawing', 'Current_Rev']], on='ISO_Drawing', how='left')

def save_performance(original_df):
    """실적 업데이트 후 파일 저장"""
    original_df.to_excel(PIPING_PATH, index=False)

def main():
    st.set_page_config(page_title="Construction Management", layout="wide")
    st.title("🏗️ Piping Construction Control Center")
    st.info(f"📍 Data Location: {DATA_DIR}")

    df = load_piping_data()
    if df is None: return

    # --- 1. KPI Dashboard ---
    total_inch = df['Size'].sum()
    done_inch = df['Done_Inch'].sum()
    progress = (done_inch / total_inch * 100) if total_inch > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Scope", f"{total_inch:,.1f} inch")
    col2.metric("Welding Progress", f"{progress:.2f}%")
    
    mismatch_count = df[df['Applied_Rev'] != df['Current_Rev']].shape[0]
    if mismatch_count > 0:
        col3.warning(f"Revision Mismatch: {mismatch_count} 건")
    else:
        col3.success("All Revisions Synced")

    st.divider()

    # --- 2. Welding 실적 입력 ---
    with st.expander("📝 Welding 실적 업데이트", expanded=True):
        # 아직 완료되지 않은 Joint만 필터링
        pending = df[df['Status'] != 'Completed']
        
        if not pending.empty:
            with st.form("input_form"):
                # ISO + Joint 복합키로 선택
                selection = st.selectbox(
                    "Select Target ISO & Joint",
                    pending.apply(lambda x: f"{x['ISO_Drawing']} | {x['Joint_No']} ({x['Size']} inch)", axis=1)
                )
                date_val = st.date_input("Work Date", datetime.now())
                
                if st.form_submit_button("Update Performance"):
                    iso_id = selection.split(" | ")[0]
                    joint_id = selection.split(" | ")[1].split(" (")[0]
                    
                    # 데이터 프레임 업데이트 로직
                    target_mask = (df['ISO_Drawing'] == iso_id) & (df['Joint_No'] == joint_id)
                    df.loc[target_mask, 'Welding_Date'] = date_val.strftime('%Y-%m-%d')
                    df.loc[target_mask, 'Status'] = 'Completed'
                    df.loc[target_mask, 'Done_Inch'] = df.loc[target_mask, 'Size']
                    
                    # 병합된 컬럼(Current_Rev)을 제외하고 원본 구조로 저장
                    save_cols = [c for c in df.columns if c != 'Current_Rev']
                    save_performance(df[save_cols])
                    
                    st.success(f"Successfully Updated: {iso_id}-{joint_id}")
                    st.rerun()
        else:
            st.info("진행 중인 모든 Welding 작업이 완료되었습니다.")

    # --- 3. 실적 데이터 그리드 ---
    st.subheader("Piping Construction Lead Sheet")
    
    def highlight_status(row):
        """Revision 불일치(Red) 및 완료(Blue) 행 스타일링"""
        if row['Applied_Rev'] != row['Current_Rev']:
            return ['background-color: #ffcccc'] * len(row)
        elif row['Status'] == 'Completed':
            return ['background-color: #e6f3ff'] * len(row)
        return [''] * len(row)

    st.dataframe(
        df.style.apply(highlight_status, axis=1)
                .format({'Size': '{:.1f}', 'Done_Inch': '{:.1f}'}),
        use_container_width=True
    )

if __name__ == "__main__":
    main()
