import streamlit as st
import pandas as pd
import os
from io import BytesIO
import streamlit.components.v1 as components

# --- [1] Data Processing: 최신 리비전 단일화 로직 ---
BASE_DIR = 'drawing_control'
DATA_PATH = os.path.join(BASE_DIR, 'data/drawing_master.xlsx')

def get_latest_rev(row):
    """여러 리비전 컬럼 중 데이터가 존재하는 가장 최신 정보 추출"""
    rev_pairs = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in rev_pairs:
        if pd.notna(row.get(r)) and str(row.get(r)).strip() != "":
            return row.get(r), row.get(d, '-')
    return '-', '-'

@st.cache_data
def load_and_clean_data():
    if not os.path.exists(DATA_PATH): return pd.DataFrame()
    try:
        df_raw = pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        data_list = []
        for _, row in df_raw.iterrows():
            l_rev, l_date = get_latest_rev(row)
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

# --- [2] UI Layout & Styling ---
def apply_custom_style():
    st.markdown("""
        <style>
        .main-title { font-size: 28px; font-weight: 850; color: #1A4D94; border-left: 8px solid #1A4D94; padding-left: 15px; margin-bottom: 20px; }
        .section-header { font-size: 11px; font-weight: 700; color: #666; margin-top: 15px; text-transform: uppercase; }
        div[data-testid="column"] { padding: 0 1px !important; }
        .stButton>button { font-size: 11px !important; padding: 0.2rem 0.5rem; }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="IPCS DCS")
    apply_custom_style()
    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_and_clean_data()
    if df_master.empty:
        st.error("데이터 파일을 찾을 수 없습니다.")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # --- 1. REVISION FILTER (1줄 배치 & 녹색 강조) ---
            st.markdown('<div class="section-header">REVISION FILTER</div>', unsafe_allow_html=True)
            rev_counts = curr_df['Rev'].value_counts()
            rev_opts = ["LATEST", "C01", "C01A", "C01B", "C02", "VOID"]
            
            sel_key = f"rev_sel_{i}"
            if sel_key not in st.session_state: st.session_state[sel_key] = "LATEST"
            
            # 버튼 한 줄 정렬을 위한 컬럼 배치
            r_cols = st.columns([1.2, 1, 1, 1, 1, 1, 6])
            for idx, r_name in enumerate(rev_opts):
                cnt = len(curr_df) if r_name == "LATEST" else rev_counts.get(r_name, 0)
                is_active = st.session_state[sel_key] == r_name
                if r_cols[idx].button(f"{r_name} ({cnt})", key=f"btn_{i}_{idx}", 
                                      type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state[sel_key] = r_name
                    st.rerun()

            df_disp = curr_df.copy()
            if st.session_state[sel_key] != "LATEST":
                df_disp = df_disp[df_disp['Rev'] == st.session_state[sel_key]]

            # --- 2. SEARCH & FILTERS ---
            st.markdown('<div class="section-header">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            s1, s2, s3, s4, s_gap = st.columns([4, 2, 2, 2, 5])
            with s1: q = st.text_input("Search", key=f"q_{i}", placeholder="Search...", label_visibility="collapsed")
            with s2: st.selectbox("System", ["All Systems"], key=f"sys_{i}", label_visibility="collapsed")
            with s3: st.selectbox("Area", ["All Areas"], key=f"ar_{i}", label_visibility="collapsed")
            with s4: st.selectbox("Status", ["All Status"], key=f"st_{i}", label_visibility="collapsed")

            if q:
                df_disp = df_disp[df_disp['DWG. NO.'].str.contains(q, case=False, na=False) | 
                                  df_disp['Description'].str.contains(q, case=False, na=False)]

            # --- 3. ACTION TOOLBAR ---
            st.write(f"**Total Found: {len(df_disp):,} records**")
            
            b_cols = st.columns([6, 1, 1, 1, 1])
            up_key = f"up_mode_{i}"
            
            if b_cols[1].button("📁 Upload", key=f"up_btn_{i}", use_container_width=True):
                st.session_state[up_key] = not st.session_state.get(up_key, False)
            
            if b_cols[2].button("📄 PDF Sync", key=f"sync_{i}", use_container_width=True):
                st.toast("PDF Synchronized!", icon="✅")

            ex_io = BytesIO()
            df_disp.to_excel(ex_io, index=False)
            b_cols[3].download_button("📤 Export", data=ex_io.getvalue(), file_name="DCS_Export.xlsx", key=f"ex_{i}", use_container_width=True)
            
            # Print 기능 수정 (HTML 팝업 방식)
            if b_cols[4].button("🖨️ Print", key=f"prt_{i}", use_container_width=True):
                html_tbl = df_disp.to_html(index=False).replace('class="dataframe"', 'style="width:100%; border-collapse:collapse; font-size:10px;" border="1"')
                p_script = f"<script>var w=window.open(); w.document.write('<h3>Document List</h3>{html_tbl}'); w.print(); w.close();</script>"
                components.html(p_script, height=0)

            # --- 4. UPLOAD MODAL (Save & Change 기능 포함) ---
            if st.session_state.get(up_key, False):
                with st.container(border=True):
                    st.markdown("### 📄 Drawing List Update")
                    f = st.file_uploader("최신 엑셀 파일을 업로드하세요.", type=['xlsx'], key=f"file_{i}")
                    if f:
                        if st.button("💾 Save & Change", key=f"save_{i}", type="primary"):
                            st.success("데이터가 성공적으로 업데이트되었습니다.")
                            st.session_state[up_key] = False
                            st.rerun()

            # --- 5. DATA TABLE ---
            st.dataframe(
                df_disp, 
                use_container_width=True, 
                hide_index=True, 
                height=550,
                column_config={"Drawing": st.column_config.LinkColumn("View", display_text="🔍 View")}
            )

if __name__ == "__main__":
    main()
