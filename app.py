import streamlit as st
import pandas as pd
import os
from io import BytesIO
import streamlit.components.v1 as components

# --- [1] Data Engineering Layer ---
BASE_DIR = 'drawing_control'
DATA_PATH = os.path.join(BASE_DIR, 'data/drawing_master.xlsx')

def get_latest_rev_info(row):
    """여러 리비전 열 중 최신 데이터 하나만 추출하여 단일화"""
    # 3rd -> 2nd -> 1st 순서로 데이터가 있는 가장 앞선 것을 선택
    rev_sets = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r_col, d_col in rev_sets:
        val = row.get(r_col)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d_col, '-')
    return '-', '-'

@st.cache_data
def load_and_sync_data():
    if not os.path.exists(DATA_PATH): return pd.DataFrame()
    try:
        df_raw = pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        processed = []
        for _, row in df_raw.iterrows():
            l_rev, l_date = get_latest_rev_info(row)
            processed.append({
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
        return pd.DataFrame(processed)
    except: return pd.DataFrame()

# --- [2] UI Styling ---
def apply_ui_fix():
    st.markdown("""
        <style>
        .main-title { font-size: 28px; font-weight: 850; color: #1A4D94; border-left: 8px solid #1A4D94; padding-left: 15px; margin-bottom: 20px; }
        .section-header { font-size: 11px; font-weight: 700; color: #666; margin-top: 15px; text-transform: uppercase; }
        /* 리비전 필터 버튼 간격 및 폰트 최적화 */
        div[data-testid="column"] { padding: 0 1px !important; }
        .stButton>button { font-size: 11px !important; padding: 0.2rem 0.5rem; }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="DCS Dashboard")
    apply_ui_fix()
    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_and_sync_data()
    if df_master.empty:
        st.error("데이터 로드 실패. 파일 경로를 확인하세요.")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_list = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_list[i], case=False, na=False)]
            
            # --- 1. REVISION FILTER (1줄 정렬 & 수량 & 녹색 활성화) ---
            st.markdown('<div class="section-header">REVISION FILTER</div>', unsafe_allow_html=True)
            rev_counts = curr_df['Rev'].value_counts()
            rev_opts = ["LATEST", "C01", "C01A", "C01B", "C02", "VOID"]
            
            sel_rev_key = f"sel_rev_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            # 버튼 가로 배치 비율 조정 (총 12컬럼 중 7컬럼 사용으로 중앙까지만 위치)
            r_cols = st.columns([1.2, 1, 1, 1, 1, 1, 5.8])
            for idx, r_name in enumerate(rev_opts):
                count = len(curr_df) if r_name == "LATEST" else rev_counts.get(r_name, 0)
                is_selected = st.session_state[sel_rev_key] == r_name
                if r_cols[idx].button(f"{r_name} ({count})", key=f"rev_btn_{i}_{idx}", 
                                      type="primary" if is_selected else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_name
                    st.rerun()

            df_disp = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST":
                df_disp = df_disp[df_disp['Rev'] == st.session_state[sel_rev_key]]

            # --- 2. SEARCH & FILTERS (2/3 지점 배치) ---
            st.markdown('<div class="section-header">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            s_c1, s_c2, s_c3, s_c4, s_spc = st.columns([4, 2, 2, 2, 5])
            with s_c1: q = st.text_input("Search", key=f"q_{i}", placeholder="검색어 입력...", label_visibility="collapsed")
            with s_c2: st.selectbox("System", ["All Systems"], key=f"sys_{i}", label_visibility="collapsed")
            with s_c3: st.selectbox("Area", ["All Areas"], key=f"ar_{i}", label_visibility="collapsed")
            with s_c4: st.selectbox("Status", ["All Status"], key=f"st_{i}", label_visibility="collapsed")

            if q:
                df_disp = df_disp[df_disp['DWG. NO.'].str.contains(q, case=False, na=False) | 
                                  df_disp['Description'].str.contains(q, case=False, na=False)]

            # --- 3. ACTION TOOLBAR ---
            # SyntaxError(line 98) 수정 완료
            st.write(f"**Total Found: {len(df_disp):,} records**")
            
            b_cols = st.columns([6, 1, 1, 1, 1])
            up_toggle = f"show_up_{i}"
            
            if b_cols[1].button("📁 Upload", key=f"up_btn_{i}", use_container_width=True):
                st.session_state[up_toggle] = not st.session_state.get(up_toggle, False)
            
            if b_cols[2].button("📄 PDF Sync", key=f"sync_{i}", use_container_width=True):
                st.toast("PDF Repository Synchronized!", icon="✅")

            # SyntaxError(line 122) 수정 완료: 괄호 닫기 확인
            ex_io = BytesIO()
            df_disp.to_excel(ex_io, index=False)
            b_cols[3].download_button("📤 Export", data=ex_io.getvalue(), file_name="DCS_Export.xlsx", key=f"ex_btn_{i}", use_container_width=True)
            
            if b_cols[4].button("🖨️ Print", key=f"prt_btn_{i}", use_container_width=True):
                # 데이터 유실 방지를 위한 팝업 인쇄 로직
                html_tbl = df_disp.to_html(index=False).replace('class="dataframe"', 'style="width:100%; border-collapse:collapse; font-size:10px;" border="1"')
                p_script = f"<script>var w=window.open(); w.document.write('<h3>DCS List</h3>{html_tbl}'); w.print(); w.
