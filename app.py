import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- 1. 기본 설정 및 데이터 로드 ---
DB_PATH = 'data/drawing_master.xlsx'

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

# --- 2. 기능 로직 (인쇄 및 저장) ---
def execute_print(df, title):
    table_html = df.to_html(index=False, border=1)
    print_script = f"""
    <script>
    var printWin = window.open('', '', 'width=1200,height=900');
    printWin.document.write('<html><head><title>Print</title>');
    printWin.document.write('<style>body{{font-family:sans-serif;padding:20px;}} table{{width:100%;border-collapse:collapse;font-size:9px;}} th,td{{border:1px solid #ccc;padding:4px;}} th{{background:#f2f2f2;}}</style>');
    printWin.document.write('</head><body><h2>{title}</h2>{table_html.replace("'", "\\'").replace("\\n", "")}</body></html>');
    printWin.document.close();
    setTimeout(function(){{ printWin.print(); printWin.close(); }}, 500);
    </script>
    """
    st.components.v1.html(print_script, height=0)

@st.dialog("Upload Drawing List")
def upload_modal():
    st.write("새로운 마스터 리스트(XLSX)를 업로드하십시오.")
    uploaded_file = st.file_uploader("파일 선택", type=["xlsx"], label_visibility="collapsed")
    if uploaded_file:
        if st.button("Save & Apply", type="primary", use_container_width=True):
            new_df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            new_df_raw.to_excel(DB_PATH, index=False, sheet_name='DRAWING LIST')
            st.session_state.master_df = process_raw_df(new_df_raw)
            st.rerun()

# --- 3. UI 스타일 및 렌더링 ---
def apply_original_style():
    st.markdown("""
        <style>
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 25px; }
        .section-label { font-size: 10px !important; font-weight: 700; color: #6b7a90; margin-top: 15px; margin-bottom: 5px; text-transform: uppercase; }
        /* 버튼 디자인 복구 */
        div.stButton > button { border-radius: 4px !important; height: 32px !important; }
        div.stButton > button[kind="primary"] { background-color: #28a745 !important; border: 1px solid #dc3545 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

def render_tab_content(display_df, tab_name):
    # 중복 체크 알림 복구
    duplicates = display_df[display_df.duplicated(['DWG. NO.'], keep=False)]
    if not duplicates.empty:
        st.warning(f"⚠️ Duplicate Warning: {len(duplicates)} redundant records detected in this category.")

    # REVISION FILTER
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    f_key = f"rev_{tab_name}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    r_cols = st.columns([1.5, 1, 1, 1, 1, 1, 7.5])
    for i, rev in enumerate(rev_list[:6]):
        count = len(display_df) if rev == "LATEST" else (display_df['Rev'] == rev).sum()
        label = f"{rev} ({count})" if rev == "LATEST" else rev
        with r_cols[i]:
            if st.button(label, key=f"bt_{tab_name}_{rev}", type="primary" if st.session_state[f_key] == rev else "secondary", use_container_width=True):
                st.session_state[f_key] = rev
                st.rerun()

    # SEARCH & TOOLBAR
    st.markdown("<div class='section-label'>SEARCH & FILTERS</div>", unsafe_allow_html=True)
    df = display_df.copy()
    if st.session_state[f_key] != "LATEST": df = df[df['Rev'] == st.session_state[f_key]]

    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    t_cols[0].markdown(f"**Total: {len(df):,} records**")
    with t_cols[4]:
        if st.button("📁 Upload", key=f"up_{tab_name}", use_container_width=True): upload_modal()
    with t_cols[5]:
        if st.button("🖨️ Print", key=f"pr_{tab_name}", use_container_width=True): execute_print(df, tab_name)

    st.dataframe(df, use_container_width=True, hide_index=True, height=750)

def main():
    st.set_page_config(layout="wide", page_title="Plant Drawing Integrated System")
    apply_original_style()
    st.markdown("<div class='main-title'>Plant Drawing Integrated System</div>", unsafe_allow_html=True)
    
    master_df = load_master_data()
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]
    
    for i, tab in enumerate(tabs):
        with tab:
            f_df = master_df if i == 0 else master_df[master_df['Category'].str.contains(tab_names[i], case=False, na=False)]
            render_tab_content(f_df, tab_names[i])

if __name__ == "__main__":
    main()
