import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- 1. 기본 설정 및 데이터 로드 로직 ---
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """행 데이터에서 최신 리비전 정보를 추출합니다."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def process_raw_df(df_raw):
    """업로드된 원시 엑셀 데이터를 시스템 규격으로 가공합니다."""
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
    """데이터베이스 파일에서 마스터 리스트를 로드합니다."""
    if 'master_df' not in st.session_state:
        if os.path.exists(DB_PATH):
            df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            st.session_state.master_df = process_raw_df(df_raw)
        else:
            st.session_state.master_df = pd.DataFrame()
    return st.session_state.master_df

# --- 2. 인쇄 및 업로드 기능 ---
def execute_print(df, title):
    """필터링된 데이터를 정적 HTML 테이블로 변환하여 인쇄창을 엽니다."""
    table_html = df.to_html(index=False, border=1)
    print_script = f"""
    <script>
    var printWin = window.open('', '', 'width=1200,height=900');
    printWin.document.write('<html><head><title>Print List</title>');
    printWin.document.write('<style>body{{font-family:sans-serif;padding:20px;}} table{{width:100%;border-collapse:collapse;font-size:9px;}} th,td{{border:1px solid #ccc;padding:4px;text-align:left;}} th{{background:#f2f2f2;}}</style>');
    printWin.document.write('</head><body>');
    printWin.document.write('<h2>{title}</h2>');
    printWin.document.write('{table_html.replace("'", "\\'").replace("\\n", "")}');
    printWin.document.write('</body></html>');
    printWin.document.close();
    setTimeout(function(){{ printWin.print(); printWin.close(); }}, 500);
    </script>
    """
    st.components.v1.html(print_script, height=0)

@st.dialog("Upload Drawing List")
def upload_modal():
    """파일 업로드 및 물리적 저장 기능을 제공하는 모달창입니다."""
    st.write("새로운 마스터 리스트(XLSX)를 업로드하십시오.")
    uploaded_file = st.file_uploader("파일 선택", type=["xlsx"], label_visibility="collapsed")
    if uploaded_file:
        if st.button("Save & Apply", type="primary", use_container_width=True):
            try:
                new_df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
                os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
                new_df_raw.to_excel(DB_PATH, index=False, sheet_name='DRAWING LIST') # 파일 저장
                st.session_state.master_df = process_raw_df(new_df_raw) # 메모리 갱신
                st.toast("Database Updated Successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

# --- 3. 메인 UI 렌더링 ---
def apply_custom_style():
    st.markdown("""
        <style>
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; }
        div.stButton > button[kind="primary"] { background-color: #28a745 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

def render_table_section(display_df, tab_name):
    # 리비전 필터
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    f_key = f"sel_rev_{tab_name}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    rev_options = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    r_cols = st.columns([1.5, 1, 1, 1, 1, 1, 7.5])
    for i, rev in enumerate(rev_options[:6]):
        with r_cols[i]:
            if st.button(rev, key=f"btn_{tab_name}_{rev}", type="primary" if st.session_state[f_key] == rev else "secondary", use_container_width=True):
                st.session_state[f_key] = rev
                st.rerun()

    # 데이터 필터링
    df = display_df.copy()
    if st.session_state[f_key] != "LATEST":
        df = df[df['Rev'] == st.session_state[f_key]]

    # 툴바 (업로드 및 인쇄)
    st.write("")
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    t_cols[0].markdown(f"**Total: {len(df):,} records**")
    
    with t_cols[2]:
        if st.button("📁 Upload", key=f"up_{tab_name}", use_container_width=True):
            upload_modal()
    with t_cols[5]:
        if st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True):
            execute_print(df, f"Drawing Control System - {tab_name}")

    st.dataframe(df, use_container_width=True, hide_index=True, height=800)

def main():
    st.set_page_config(layout="wide", page_title="Drawing Control System")
    apply_custom_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True) # 타이틀 복구
    
    master_df = load_master_data()
    tab_list = ["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"]
    tabs = st.tabs(tab_list)
    
    for i, tab in enumerate(tabs):
        with tab:
            category_name = tab_list[i].split(" ")[1]
            # 카테고리별 필터링 (Master 탭 제외)
            filtered_df = master_df if i == 0 else master_df[master_df['Category'].str.contains(category_name, case=False, na=False)]
            render_table_section(filtered_df, category_name)

if __name__ == "__main__":
    main()
