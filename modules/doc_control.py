import streamlit as st
import pandas as pd
import os
from io import BytesIO

# File Path Settings
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """최신 리비전 정보 추출 로직"""
    for r, d, m in [('3rd REV', '3rd DATE', '3rd REMARK'), 
                    ('2nd REV', '2nd DATE', '2nd REMARK'), 
                    ('1st REV', '1st DATE', '1st REMARK')]:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            rem = row.get(m, "")
            rem = "" if pd.isna(rem) or str(rem).lower() == "none" else str(rem)
            return val, row.get(d, '-'), rem
    return '-', '-', ''

def apply_final_micro_ui():
    """버튼 내 글자 겹침 방지를 위한 초정밀 CSS"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f7f9fc !important;
            color: #0d1826 !important;
        }
        .block-container { padding: 0.3rem 1.5rem !important; }
        [data-testid="stHeader"] { display: none !important; }
        
        .main-title { font-size: 18px !important; font-weight: 800; color: #1657d0; margin-bottom: 3px; }
        .section-label { font-size: 9px !important; font-weight: 700; color: #8a94a6; text-transform: uppercase; }

        /* 버튼 내 글자 겹침 방지 핵심 설정 */
        div.stButton > button {
            border-radius: 2px; border: 1px solid #dde3ec;
            background-color: white; color: #374559;
            height: 22px !important;
            /* 폰트를 7.8px로 축소하여 LATEST(3807)이 한 줄에 나오도록 유도 */
            font-size: 7.8px !important; 
            font-weight: 700 !important;
            padding: 0 2px !important;
            line-height: 22px !important;
            letter-spacing: -0.7px !important; /* 자간을 더 압축 */
            white-space: nowrap !important;    /* 절대 줄바꿈 금지 */
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }

        /* 데이터 테이블 18px 유지 */
        div[data-testid="stDataFrame"] [role="gridcell"] div {
            font-size: 18px !important;
            text-align: center !important;
            justify-content: center !important;
            display: flex !important;
            align-items: center !important;
        }
        div[data-testid="stDataFrame"] [role="columnheader"] p {
            font-size: 18px !important;
            font-weight: 800 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_final_micro_ui()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Excel database not found.")
        return

    # [중요] f_df 정의 위치를 상단으로 이동하여 NameError 방지
    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    p_data = []
    for _, row in df.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date,
            "Hold": row.get('HOLD Y/N', 'N'), "Status": row.get('Status', '-'),
            "Remark": l_rem, "AREA": row.get('AREA', '-'), "SYSTEM": row.get('SYSTEM', '-')
        })
    f_df = pd.DataFrame(p_data) # 변수 정의 완료

    # Revision Filter 영역
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_counts = f_df['Rev'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    # 버튼 가로폭 확보를 위해 컬럼 수를 12개로 약간 조정 (개별 너비 증가)
    rev_cols = st.columns(12) 
    for i, rev in enumerate(target_revs[:12]):
        count = len(f_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        btn_label = f"{rev}({count})"
        if rev_cols[i].button(btn_label, key=f"r_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # Search & Filter 및 Table 영역 (이후 로직 동일)
    # ...
