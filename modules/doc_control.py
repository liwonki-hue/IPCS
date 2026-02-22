import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# --- 1. Configuration & Data Loading ---
DB_PATH = 'data/drawing_master.xlsx'
ITEMS_PER_PAGE = 30 

def get_latest_rev_info(row):
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def process_raw_df(df_raw):
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date = get_latest_rev_info(row)
        p_data.append({
            "Drawing": f"https://sharepoint-link/view?id={row.get('DWG. NO.')}",
            "Category": row.get('Category', '-'), 
            "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date, "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-')
        })
    return pd.DataFrame(p_data)

def load_master_data():
    if 'master_df' not in st.session_state:
        if os.path.exists(DB_PATH):
            df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            st.session_state.master_df = process_raw_df(df_raw)
        else:
            st.session_state.master_df = pd.DataFrame()
    return st.session_state.master_df

@st.dialog("Upload Drawing List")
def upload_modal():
    st.write("새로운 마스터 리스트 파일을 업로드하여 DB를 갱신합니다.")
    uploaded_file = st.file_uploader("파일 선택", type=["xlsx"], label_visibility="collapsed")
    if uploaded_file:
        if st.button("Save & Apply", type="primary", use_container_width=True):
            new_df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            new_df_raw.to_excel(DB_PATH, index=False, sheet_name='DRAWING LIST')
            st.session_state.master_df = process_raw_df(new_df_raw)
            st.rerun()

def apply_professional_style():
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 2.5rem !important; }
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px !important; }
        
        /* 인쇄 시 불필요한 요소 숨기기 설정 */
        @media print {
            header, [data-testid="stSidebar"], .stButton, .stDownloadButton, 
            [data-testid="stHeader"], .section-label, [data-testid="stForm"],
            div[data-testid="stVerticalBlock"] > div:has(input),
            div[data-testid="stVerticalBlock"] > div:has(select) {
                display: none !important;
            }
            .main-title { display: block !important; text-align: center; font-size: 20pt !important; }
            .stDataFrame { width: 100% !important; height: auto !important; }
        }
        
        div.stButton > button { border-radius: 4px !important; }
        div.stButton > button[kind="primary"] { 
            background-color: #28a745 !important; color: white !important; 
            border: 1.5px solid #dc3545 !important; height: 32px !important;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 2. Core Rendering ---
def render_drawing_table(display_df, tab_name):
    # Revision Filter
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    f_key = f"sel_rev_{tab_name}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    rev_counts = display_df['Rev'].value_counts()
    rev_options = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    r_cols = st.columns([1.5, 1, 1, 1, 1, 1, 7.5]) 
    
    for i, rev in enumerate(rev_options[:6]):
        count = len(display_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        with r_cols[i]:
            if st.button(f"{rev} ({count})", key=f"btn_{tab_name}_{rev}", 
                        type="primary" if st.session_state[f_key] == rev else "secondary", use_container_width=True):
                st.session_state[f_key] = rev
                st.rerun()

    # Search & Filters
    st.markdown("<div class='section-label'>SEARCH & FILTERS</div>", unsafe_allow_html=True)
    sf_cols = st.columns([4, 2, 2, 2, 6])
    search_query = sf_cols[0].text_input("Search", key=f"q_{tab_name}")
    sel_sys = sf_cols[1].selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    sel_area = sf_cols[2].selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    sel_stat = sf_cols[3].selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 필터링
    df = display_df.copy()
    if st.session_state[f_key] != "LATEST": df = df[df['Rev'] == st.session_state[f_key]]
    if search_query:
        df = df[df['DWG. NO.'].str.contains(search_query, case=False, na=False) | 
                df['Description'].str.contains(search_query, case=False, na=False)]
    if sel_sys != "All": df = df[df['SYSTEM'] == sel_sys]
    if sel_area != "All": df = df[df['Area'] == sel_area]
    if sel_stat != "All": df = df[df['Status'] == sel_stat]

    # Action Toolbar
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    t_cols[0].markdown(f"**Total: {len(df):,} records**")
    
    with t_cols[2]: 
        if st.button("📁 Upload", key=f"btn_up_{tab_name}", use_container_width=True):
            upload_modal()
    with t_cols[3]: st.button("📄 PDF Sync", key=f"pdf_{tab_name}", use_container_width=True)
    with t_cols[4]:
        export_out = BytesIO()
        df.to_excel(export_out, index=False)
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    
    # 3. [복구 및 활성화] Print 버튼 로직
    with t_cols[5]:
        if st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True):
            st.components.v1.html("<script>window.print();</script>", height=0)

    st.dataframe(df, use_container_width=True, hide_index=True, height=800)

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)
    master_df = load_master_data()
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]
    for i, tab in enumerate(tabs):
        with tab:
            render_drawing_table(master_df if i == 0 else master_df[master_df['Category'].str.contains(tab_names[i], case=False, na=False)], tab_names[i])

if __name__ == "__main__":
    show_doc_control()
