import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- [1] Data Processing Logic ---
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """최신 리비전 정보를 탐색하여 반환합니다."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def process_raw_df(df_raw):
    """Excel 로우 데이터를 표준 데이터 프레임으로 변환합니다."""
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), 
            "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', row.get('Description', '-')),
            "Rev": l_rev, 
            "Date": l_date, 
            "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'),
            "Drawing": row.get('Drawing', row.get('DRAWING', row.get('Link', None)))
        })
    return pd.DataFrame(p_data)

@st.cache_data
def load_data():
    """데이터 로드 및 캐싱 처리"""
    if os.path.exists(DB_PATH):
        try:
            df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            return process_raw_df(df_raw)
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- [2] Presentation Layer ---
def main():
    st.set_page_config(layout="wide", page_title="DCS Dashboard")

    # CSS SyntaxError(따옴표 미종결) 방지를 위한 엄격한 스타일링 적용
    st.markdown("""
        <style>
        .main-title { 
            font-size: 32px; font-weight: 850; color: #1A4D94; 
            border-left: 8px solid #1A4D94; padding-left: 15px; margin-bottom: 20px;
        }
        .section-header {
            font-size: 13px; font-weight: 700; color: #666; margin: 25px 0 10px 0; text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.error("데이터 소스를 로드할 수 없습니다. 'data/drawing_master.xlsx' 경로를 확인하십시오.")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # --- [Revision Filter with Count] ---
            st.markdown('<div class="section-header">REVISION FILTER</div>', unsafe_allow_html=True)
            rev_counts = curr_df['Rev'].value_counts()
            unique_revs = sorted([str(r) for r in curr_df['Rev'].unique() if pd.notna(r) and str(r).strip() != "-"])
            
            # 버튼 옵션 구성 (명칭 및 수량 결합)
            rev_opts = [("LATEST", len(curr_df))] + [(r, rev_counts.get(r, 0)) for r in unique_revs]
            
            sel_rev_key = f"rev_state_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns(len(rev_opts[:7]) + 1)
            for idx, (r_name, r_count) in enumerate(rev_opts[:7]):
                btn_label = f"{r_name} ({r_count})"
                is_selected = st.session_state[sel_rev_key] == r_name
                if r_cols[idx].button(btn_label, key=f"btn_{i}_{idx}", 
                                      type="primary" if is_selected else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_name
                    st.rerun()

            df_filt = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": 
                df_filt = df_filt[df_filt['Rev'] == st.session_state[sel_rev_key]]
            
            # --- [Search & Dynamic Filters] ---
            st.markdown('<div class="section-header">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            sys_list = ["All Systems"] + sorted([str(x) for x in curr_df['SYSTEM'].unique() if pd.notna(x) and str(x).strip() not in ('', '-')])
            area_list = ["All Areas"] + sorted([str(x) for x in curr_df['Area'].unique() if pd.notna(x) and str(x).strip() not in ('', '-')])
            
            s_col1, s_col2, s_col3, s_col4 = st.columns([4, 2, 2, 2])
            q = s_col1.text_input("Search", key=f"q_{i}", placeholder="Search...", label_visibility="collapsed")
            sel_sys = s_col2.selectbox("System", sys_list, key=f"sys_{i}", label_visibility="collapsed")
            sel_area = s_col3.selectbox("Area", area_list, key=f"area_{i}", label_visibility="collapsed")
            sel_stat = s_col4.selectbox("Status", ["All Status"] + list(curr_df['Status'].unique()), key=f"stat_{i}", label_visibility="collapsed")
            
            if q: df_filt = df_filt[df_filt['DWG. NO.'].str.contains(q, case=False, na=False) | df_filt['Description'].str.contains(q, case=False, na=False)]
            if sel_sys != "All Systems": df_filt = df_filt[df_filt['SYSTEM'] == sel_sys]
            if sel_area != "All Areas": df_filt = df_filt[df_filt['Area'] == sel_area]
            
            # --- [Action Toolbar] ---
            t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([6, 1, 1, 1, 1])
            t_col1.write(f"**Total Found: {len(df_filt):,} records**")
            t_col2.button("📁 Upload", key=f"up_{i}", use_container_width=True)
            t_col3.button("📄 PDF Sync", key=f"sync_{i}", use_container_width=True)
            
            ex_io = BytesIO()
            df_filt.to_excel(ex_io, index=False)
            t_col4.download_button("📤 Export", data=ex_io.getvalue(), file_name=f"{tab_names[i]}.xlsx", key=f"ex_{i}", use_container_width=True)
            t_col5.button("🖨️ Print", key=f"prt_{i}", use_container_width=True)

            # --- [Data Table with View Icon] ---
            st.dataframe(
                df_filt, 
                use_container_width=True, 
                hide_index=True, 
                height=500,
                column_config={
                    "Drawing": st.column_config.LinkColumn(
                        "View",
                        display_text="🔍 View",
                        help="클릭하면 도면 파일을 확인합니다."
                    )
                }
            )

if __name__ == "__main__":
    main()
