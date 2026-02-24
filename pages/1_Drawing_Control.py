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
import math
from io import BytesIO

# --- 1. 기본 설정 및 데이터 로드 ---
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

# --- 2. [복구] 모달 업로드 & 파일 실제 저장 ---
@st.dialog("Upload Drawing List")
def upload_modal():
    st.write("새로운 마스터 리스트 파일을 업로드하여 DB를 갱신합니다.")
    uploaded_file = st.file_uploader("파일 선택", type=["xlsx"], label_visibility="collapsed")
    if uploaded_file:
        if st.button("Save & Apply", type="primary", use_container_width=True):
            try:
                new_df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
                os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
                # 물리적 파일 저장 (Overwrite)
                new_df_raw.to_excel(DB_PATH, index=False, sheet_name='DRAWING LIST')
                # 세션 데이터 즉시 갱신
                st.session_state.master_df = process_raw_df(new_df_raw)
                st.toast("Data Saved Successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Save Failed: {e}")

# --- 3. [개선] 인쇄 기능 (HTML 테이블 변환 방식) ---
def execute_print(df, title):
    # 인쇄 시 리스트가 안보이는 현상을 해결하기 위해 정적 HTML 생성
    table_html = df.to_html(index=False, border=1)
    print_script = f"""
    <script>
    var printWin = window.open('', '', 'width=1200,height=900');
    printWin.document.write('<html><head><title>Print List</title>');
    printWin.document.write('<style>body{{font-family:sans-serif;padding:20px;}} table{{width:100%;border-collapse:collapse;font-size:10px;}} th,td{{border:1px solid #ccc;padding:5px;text-align:left;}} th{{background:#f2f2f2;}}</style>');
    printWin.document.write('</head><body>');
    printWin.document.write('<h2>{title}</h2>');
    printWin.document.write('{table_html.replace("'", "\\'").replace("\\n", "")}');
    printWin.document.write('</body></html>');
    printWin.document.close();
    setTimeout(function(){{ printWin.print(); printWin.close(); }}, 500);
    </script>
    """
    st.components.v1.html(print_script, height=0)

# --- 4. UI 렌더링 ---
def apply_style():
    st.markdown("""
        <style>
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px !important; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; }
        div.stButton > button[kind="primary"] { background-color: #28a745 !important; color: white !important; height: 32px !important; }
        </style>
    """, unsafe_allow_html=True)

def render_table(display_df, tab_name):
    # Revision Filter (LATEST 단일 줄 유지)
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    f_key = f"sel_rev_{tab_name}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    rev_options = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    r_cols = st.columns([1.5, 1, 1, 1, 1, 1, 7.5])
    for i, rev in enumerate(rev_options[:6]):
        with r_cols[i]:
            if st.button(rev, key=f"b_{tab_name}_{rev}", type="primary" if st.session_state[f_key] == rev else "secondary", use_container_width=True):
                st.session_state[f_key] = rev
                st.rerun()

    # Search & Action Toolbar
    df = display_df.copy()
    if st.session_state[f_key] != "LATEST": df = df[df['Rev'] == st.session_state[f_key]]
    
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    t_cols[0].markdown(f"**Total: {len(df):,} records**")
    with t_cols[2]:
        if st.button("📁 Upload", key=f"up_{tab_name}", use_container_width=True): upload_modal()
    with t_cols[5]:
        if st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True):
            execute_print(df, f"Drawing Control System - {tab_name}")

    st.dataframe(df, use_container_width=True, hide_index=True, height=800)

def main():
    apply_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)
    master_df = load_master_data()
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]
    for i, tab in enumerate(tabs):
        with tab:
            render_table(master_df if i == 0 else master_df[master_df['Category'].str.contains(tab_names[i], case=False, na=False)], tab_names[i])

if __name__ == "__main__":
    main()
