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
    """원시 데이터를 시스템 규격에 맞게 변환합니다."""
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
    """세션에 데이터가 있으면 그대로 사용하고, 없으면 파일에서 로드합니다."""
    if 'master_df' not in st.session_state:
        if os.path.exists(DB_PATH):
            df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            st.session_state.master_df = process_raw_df(df_raw)
        else:
            st.session_state.master_df = pd.DataFrame()
    return st.session_state.master_df

# --- 2. [수정] Modal Upload Dialog (파일 저장 로직 추가) ---
@st.dialog("Upload Drawing List")
def upload_modal():
    st.write("새로운 마스터 리스트 파일을 업로드하여 DB를 갱신합니다.")
    uploaded_file = st.file_uploader("파일 선택", type=["xlsx"], label_visibility="collapsed")
    
    if uploaded_file:
        st.info(f"선택된 파일: {uploaded_file.name}")
        
        if st.button("Save & Apply", type="primary", use_container_width=True):
            try:
                # 1. 엑셀 파일 데이터 읽기
                new_df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
                
                # 2. [핵심] 실제 로컬 파일에 저장 (Overwrite)
                # 'data' 디렉토리가 없는 경우를 대비해 생성 시도
                os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
                new_df_raw.to_excel(DB_PATH, index=False, sheet_name='DRAWING LIST', engine='openpyxl')
                
                # 3. 세션 메모리 갱신
                st.session_state.master_df = process_raw_df(new_df_raw)
                
                st.success("데이터베이스 파일이 성공적으로 업데이트되었습니다.")
                st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {e}")

def apply_professional_style():
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 2.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase; }
        
        /* 버튼 및 리비전 필터 디자인 */
        div.stButton > button { border-radius: 4px !important; white-space: nowrap !important; }
        div.stButton > button[kind="primary"] { 
            background-color: #28a745 !important; color: white !important; 
            border: 1.5px solid #dc3545 !important; height: 32px !important;
        }
        /* 페이지네이션 소형화 */
        .nav-btn > div > div > button { height: 24px !important; min-height: 24px !important; width: 32px !important; font-size: 11px !important; }
        </style>
    """, unsafe_allow_html=True)

# --- 3. Core Rendering (기존 구조 유지) ---
def render_drawing_table(display_df, tab_name):
    # 중복 경고 복구
    duplicates = display_df[display_df.duplicated(['DWG. NO.'], keep=False)]
    if not duplicates.empty:
        st.error(f"⚠️ Duplicate Warning: {len(duplicates)} redundant records detected in this category.")

    # REVISION FILTER (LATEST 단일 줄 표시 유지)
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

    # SEARCH & FILTERS
    st.markdown("<div class='section-label'>SEARCH & FILTERS</div>", unsafe_allow_html=True)
    sf_cols = st.columns([4, 2, 2, 2, 6])
    search_query = sf_cols[0].text_input("Search", key=f"q_{tab_name}", placeholder="DWG No. or Title...")
    sel_sys = sf_cols[1].selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    sel_area = sf_cols[2].selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    sel_stat = sf_cols[3].selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 필터링 및 테이블 출력
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
        df.to_excel(export_out, index=False, engine='openpyxl')
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    with t_cols[5]: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # DataFrame & Pagination
    total_records = len(df)
    p_key = f"page_{tab_name}"
    if p_key not in st.session_state: st.session_state[p_key] = 1
    start_idx = (st.session_state[p_key] - 1) * ITEMS_PER_PAGE
    st.dataframe(df.iloc[start_idx : start_idx + ITEMS_PER_PAGE], use_container_width=True, hide_index=True, height=800)

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
