import streamlit as st
import pandas as pd
import os
from io import BytesIO
import streamlit.components.v1 as components

# --- [1] Data Engineering Layer ---
BASE_DIR = 'drawing_control'
DATA_PATH = os.path.join(BASE_DIR, 'data/drawing_master.xlsx')

def get_latest_info(row):
    """여러 리비전 컬럼 중 가장 최신 정보를 추출하여 단일화 (원상 복구)"""
    rev_pairs = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in rev_pairs:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

@st.cache_data
def load_processed_data():
    if not os.path.exists(DATA_PATH): return pd.DataFrame()
    try:
        df_raw = pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        data_list = []
        for _, row in df_raw.iterrows():
            l_rev, l_date = get_latest_info(row)
            data_list.append({
                "Category": row.get('Category', 'Master'),
                "Area": row.get('Area', '-'),
                "SYSTEM": row.get('SYSTEM', '-'),
                "DWG. NO.": row.get('DWG. NO.', '-'),
                "Description": row.get('DRAWING TITLE', '-'),
                "Rev": l_rev,
                "Date": l_date,
                "Hold": row.get('HOLD Y/N', 'N'),
                "Status": row.get('Status', '-'),
                "Drawing": row.get('Link', None)
            })
        return pd.DataFrame(data_list)
    except: return pd.DataFrame()

# --- [2] UI Enhancement ---
def apply_custom_ui():
    st.markdown("""
        <style>
        .main-title { font-size: 30px; font-weight: 850; color: #1A4D94; border-left: 8px solid #1A4D94; padding-left: 15px; margin-bottom: 25px; }
        .section-header { font-size: 11px; font-weight: 700; color: #666; margin: 20px 0 10px 0; text-transform: uppercase; letter-spacing: 0.5px; }
        /* 버튼 간격 및 정렬 최적화 */
        div[data-testid="column"] { padding: 0 1px !important; }
        div.stButton > button { font-size: 12px !important; }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="IPCS Document Control")
    apply_custom_ui()
    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_processed_data()
    if df_master.empty:
        st.warning(f"데이터 파일 로드 실패: {DATA_PATH}")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # --- 1. REVISION FILTER (1줄 배치 & 녹색 강조) ---
            st.markdown('<div class="section-header">REVISION FILTER</div>', unsafe_allow_html=True)
            counts = curr_df['Rev'].value_counts()
            rev_list = ["LATEST", "C01", "C01A", "C01B", "C02", "VOID"]
            
            sel_key = f"rev_state_{i}"
            if sel_key not in st.session_state: st.session_state[sel_key] = "LATEST"
            
            # 7개 컬럼으로 쪼개어 중앙까지만 배치 (2줄 방지)
            r_cols = st.columns([1.2, 1, 1, 1, 1, 1, 6])
            for idx, r_name in enumerate(rev_list):
                btn_count = len(curr_df) if r_name == "LATEST" else counts.get(r_name, 0)
                is_active = st.session_state[sel_key] == r_name
                if r_cols[idx].button(f"{r_name} ({btn_count})", key=f"r_b_{i}_{idx}", 
                                      type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state[sel_key] = r_name
                    st.rerun()

            # 필터링 로직
            df_disp = curr_df.copy()
            if st.session_state[sel_key] != "LATEST":
                df_disp = df_disp[df_disp['Rev'] == st.session_state[sel_key]]

            # --- 2. SEARCH & FILTERS (2/3 지점 위치) ---
            st.markdown('<div class="section-header">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            s1, s2, s3, s4, s_spacer = st.columns([4, 2, 2, 2, 5])
            with s1: q = st.text_input("Search", key=f"q_{i}", placeholder="Search...", label_visibility="collapsed")
            with s2: st.selectbox("System", ["All Systems"], key=f"sys_{i}", label_visibility="collapsed")
            with s3: st.selectbox("Area", ["All Areas"], key=f"ar_{i}", label_visibility="collapsed")
            with s4: st.selectbox("Status", ["All Status"], key=f"st_{i}", label_visibility="collapsed")

            if q:
                df_disp = df_disp[df_disp['DWG. NO.'].str.contains(q, case=False, na=False) | 
                                  df_disp['Description'].str.contains(q, case=False, na=False)]

            # --- 3. ACTION TOOLBAR ---
            # image_6e6678 에러 해결: 따옴표 완벽 종결
            st.write(f"**Total Found: {len(df_disp):,} records**")
            
            b_cols = st.columns([6, 1, 1, 1, 1])
            up_key = f"up_toggle_{i}"
            
            if b_cols[1].button("📁 Upload", key=f"up_b_{i}", use_container_width=True):
                st.session_state[up_key] = not st.session_state.get(up_key, False)
            
            if b_cols[2].button("📄 PDF Sync", key=f"sync_{i}", use_container_width=True):
                st.toast("PDF Sync Completed!", icon="✅")

            ex_io = BytesIO()
            df_disp.to_excel(ex_io, index=False)
            b_cols[3].download_button("📤 Export", data=ex_io.getvalue(), file_name="DCS_Export.xlsx",
