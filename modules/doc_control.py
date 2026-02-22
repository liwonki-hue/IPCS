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
    """원시 데이터를 시스템 가공 규격에 맞게 변환합니다."""
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

# --- 2. [복구] Modal Upload Dialog ---
@st.dialog("Upload Drawing List")
def upload_modal():
    st.write("새로운 마스터 리스트 파일을 드래그하여 업로드하십시오.")
    uploaded_file = st.file_uploader("파일 선택", type=["xlsx"], label_visibility="collapsed")
    
    if uploaded_file:
        st.info(f"업로드 준비 완료: {uploaded_file.name}")
        # 파일을 로드만 하고, Save & Apply 버튼을 눌러야 최종 반영
        if st.button("Save & Apply", type="primary", use_container_width=True):
            new_df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
            st.session_state.master_df = process_raw_df(new_df_raw)
            st.toast("데이터가 성공적으로 업데이트되었습니다.")
            st.rerun()

def apply_professional_style():
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 2.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        /* 타이틀 스타일 */
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase; }
        
        /* 버튼 공통 스타일 및 리비전 필터 단일 줄 유지 */
        div.stButton > button { border-radius: 4px !important; white-space: nowrap !important; }
        div.stButton > button[kind="primary"] { 
            background-color: #28a745 !important; color: white !important; 
            border: 1.5px solid #dc3545 !important; height: 32px !important;
        }
        
        /* 네비게이터 소형화 */
        .nav-btn > div > div > button { height: 24px !important; min-height: 24px !important; width: 32px !important; font-size: 11px !important; padding: 0 !important; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. Core Rendering ---
def render_drawing_table(display_df, tab_name):
    # 1. Duplicate Warning Layout
    duplicates = display_df[display_df.duplicated(['DWG. NO.'], keep=False)]
    if not duplicates.empty:
        col_w, col_r = st.columns([8, 1])
        with col_w:
            st.error(f"⚠️ Duplicate Warning: {len(duplicates)} redundant records detected in this category.")
        with col_r:
            st.button("Resolve", key=f"res_{tab_name}", use_container_width=True)

    # 2. Revision Filter (LATEST 버튼 단일 줄 최적화)
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
                st.session_state[f"page_{tab_name}"] = 1
                st.rerun()

    # 3. Search & Filters
    st.markdown("<div class='section-label'>SEARCH & FILTERS</div>", unsafe_allow_html=True)
    sf_cols = st.columns([4, 2, 2, 2, 6])
    search_query = sf_cols[0].text_input("Search", key=f"q_{tab_name}", placeholder="DWG No. or Title...")
    sel_sys = sf_cols[1].selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    sel_area = sf_cols[2].selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    sel_stat = sf_cols[3].selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 데이터 필터링
    df = display_df.copy()
    if st.session_state[f_key] != "LATEST": df = df[df['Rev'] == st.session_state[f_key]]
    if search_query:
        df = df[df['DWG. NO.'].str.contains(search_query, case=False, na=False) | 
                df['Description'].str.contains(search_query, case=False, na=False)]
    if sel_sys != "All": df = df[df['SYSTEM'] == sel_sys]
    if sel_area != "All": df = df[df['Area'] == sel_area]
    if sel_stat != "All": df = df[df['Status'] == sel_stat]

    # 4. Action Toolbar (Upload 버튼 기능 복구)
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    t_cols[0].markdown(f"**Total: {len(df):,} records**")
    
    with t_cols[2]: 
        if st.button("📁 Upload", key=f"btn_up_{tab_name}", use_container_width=True):
            upload_modal()

    with t_cols[3]: st.button("📄 PDF Sync", key=f"pdf_{tab_name}", use_container_width=True)
    with t_cols[4]:
        export_out = BytesIO()
        df.to_excel(export_out, index=False, engine='openpyxl')
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    with t_cols[5]: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # 5. Table View & Navigator
    total_records = len(df)
    total_pages = math.ceil(total_records / ITEMS_PER_PAGE)
    p_key = f"page_{tab_name}"
    if p_key not in st.session_state: st.session_state[p_key] = 1
    
    start_idx = (st.session_state[p_key] - 1) * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_records)
    paginated_df = df.iloc[start_idx:end_idx]

    st.dataframe(paginated_df, use_container_width=True, hide_index=True, height=1000)

    # 하단 네비게이터 (소형 디자인 유지)
    if total_pages > 1:
        st.write("") 
        nav_cols = st.columns([3, 0.3, 0.3, 0.3, 0.3, 0.3, 3, 1.5])
        page_range = range(max(1, st.session_state[p_key]-1), min(total_pages+1, st.session_state[p_key]+2))
        for idx, p_num in enumerate(page_range):
            with nav_cols[idx + 2]:
                st.markdown('<div class="nav-btn">', unsafe_allow_html=True)
                if st.button(str(p_num), key=f"p_{tab_name}_{p_num}", 
                             type="primary" if p_num == st.session_state[p_key] else "secondary"):
                    st.session_state[p_key] = p_num
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        with nav_cols[7]:
            st.markdown(f"<div style='text-align:right; font-size:12px; color:#666;'>{start_idx + 1}-{end_idx} / {total_records:,}</div>", unsafe_allow_html=True)

def show_doc_control():
    apply_professional_style()
    # 타이틀 복구
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)
    master_df = load_master_data()
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]
    for i, tab in enumerate(tabs):
        with tab:
            render_drawing_table(master_df if i == 0 else master_df[master_df['Category'].str.contains(tab_names[i], case=False, na=False)], tab_names[i])

if __name__ == "__main__":
    show_doc_control()
