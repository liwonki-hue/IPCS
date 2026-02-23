import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- 1. 데이터 처리 로직 ---
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
            "Description": row.get('DRAWING TITLE', row.get('Description', '-')),
            "Rev": l_rev,
            "Date": l_date, 
            "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'),
            "Drawing": row.get('Drawing', row.get('DRAWING', '-'))
        })
    return pd.DataFrame(p_data)

@st.cache_data
def load_data_from_disk():
    if os.path.exists(DB_PATH):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        return process_raw_df(df_raw)
    return pd.DataFrame()

def load_master_data():
    if 'master_df' not in st.session_state or st.session_state.get('needs_refresh'):
        st.session_state.master_df = load_data_from_disk()
        st.session_state.needs_refresh = False
    return st.session_state.master_df

# --- 2. 개선된 프린트 로직 (Iframe 방식) ---
def execute_print(df, title):
    """팝업 차단을 피하기 위해 보이지 않는 iframe을 생성하여 인쇄를 실행합니다."""
    table_html = df.to_html(index=False, border=1)
    
    # HTML 및 스타일 정의
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
            th, td {{ border: 1px solid #ccc; padding: 5px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            h2 {{ text-align: center; color: #1657d0; }}
        </style>
    </head>
    <body>
        <h2>{title}</h2>
        {table_html}
    </body>
    </html>
    """
    
    # JavaScript를 사용하여 iframe을 통한 인쇄 실행
    # 홑따옴표/줄바꿈 처리를 위해 escape 처리
    escaped_html = html_content.replace("'", "\\'").replace("\n", " ")
    
    print_js = f"""
    <script>
    function printData() {{
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
        const pri = iframe.contentWindow;
        pri.document.open();
        pri.document.write('{escaped_html}');
        pri.document.close();
        
        iframe.onload = function() {{
            pri.focus();
            pri.print();
            setTimeout(() => {{ document.body.removeChild(iframe); }}, 1000);
        }};
    }}
    printData();
    </script>
    """
    st.components.v1.html(print_js, height=0)

@st.dialog("Upload Drawing List")
def upload_modal():
    uploaded_file = st.file_uploader("파일 선택", type=["xlsx"], label_visibility="collapsed")
    if uploaded_file:
        if st.button("Save & Apply", type="primary", use_container_width=True):
            new_df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            new_df_raw.to_excel(DB_PATH, index=False, sheet_name='DRAWING LIST')
            st.cache_data.clear()
            st.session_state.needs_refresh = True 
            st.rerun()

# --- 3. UI 렌더링 ---
def apply_styles():
    st.markdown("""
        <style>
        .block-container {{ padding-top: 3.5rem !important; }}
        .main-title {{ font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px !important; }}
        .section-label {{ font-size: 10px !important; font-weight: 700; color: #6b7a90; margin-top: 15px; margin-bottom: 5px; text-transform: uppercase; }}
        div.stButton > button {{ border-radius: 4px !important; height: 32px !important; }}
        div.stButton > button[kind="primary"] {{ background-color: #28a745 !important; border: 1.5px solid #dc3545 !important; color: white !important; }}
        </style>
    """, unsafe_allow_html=True)

def render_content(base_df, tab_id):
    dupes = base_df[base_df.duplicated(['DWG. NO.'], keep=False)]
    if not dupes.empty:
        st.warning(f"⚠️ Duplicate Warning: {len(dupes)} redundant records detected in this category.")

    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    f_key = f"rev_{tab_id}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    revs = ["LATEST"] + sorted([r for r in base_df['Rev'].unique() if pd.notna(r) and r != "-"])
    r_cols = st.columns([1.5, 1, 1, 1, 1, 1, 7.5])
    for i, r in enumerate(revs[:6]):
        cnt = len(base_df) if r == "LATEST" else (base_df['Rev'] == r).sum()
        with r_cols[i]:
            if st.button(f"{r} ({cnt})", key=f"bt_{tab_id}_{r}", type="primary" if st.session_state[f_key] == r else "secondary", use_container_width=True):
                st.session_state[f_key] = r
                st.rerun()

    st.markdown("<div class='section-label'>SEARCH & FILTERS</div>", unsafe_allow_html=True)
    sf_cols = st.columns([4, 2, 2, 2, 6])
    q = sf_cols[0].text_input("Search", key=f"q_{tab_id}", placeholder="Search by DWG No. or Description...")
    sys = sf_cols[1].selectbox("System", ["All"] + sorted(base_df['SYSTEM'].unique().tolist()), key=f"s_{tab_id}")
    area = sf_cols[2].selectbox("Area", ["All"] + sorted(base_df['Area'].unique().tolist()), key=f"a_{tab_id}")
    stat = sf_cols[3].selectbox("Status", ["All"] + sorted(base_df['Status'].unique().tolist()), key=f"st_{tab_id}")

    df = base_df.copy()
    if st.session_state[f_key] != "LATEST": df = df[df['Rev'] == st.session_state[f_key]]
    if q: df = df[df['DWG. NO.'].str.contains(q, case=False, na=False) | df['Description'].str.contains(q, case=False, na=False)]
    if sys != "All": df = df[df['SYSTEM'] == sys]
    if area != "All": df = df[df['Area'] == area]
    if stat != "All": df = df[df['Status'] == stat]

    st.write("")
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    t_cols[0].markdown(f"**Total: {len(df):,} records**")
    with t_cols[2]:
        if st.button("📁 Upload", key=f"up_{tab_id}", use_container_width=True): upload_modal()
    with t_cols[3]:
        st.button("📄 PDF Sync", key=f"sync_{tab_id}", use_container_width=True)
    with t_cols[4]:
        out = BytesIO()
        df.to_excel(out, index=False)
        st.download_button("📤 Export", data=out.getvalue(), file_name=f"{tab_id}_list.xlsx", key=f"ex_{tab_id}", use_container_width=True)
    with t_cols[5]:
        if st.button("🖨️ Print", key=f"pr_{tab_id}", use_container_width=True): 
            execute_print(df, f"Drawing Control System - {tab_id}")

    st.dataframe(df, use_container_width=True, hide_index=True, height=700)
    st.markdown(f"<div style='text-align:right; font-size:12px; color:#666;'>1-30 / {len(df)}</div>", unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="Drawing Control System")
    apply_styles()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)
    
    master_df = load_master_data()
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    names = ["Master", "ISO", "Support", "Valve", "Specialty"]
    
    for i, tab in enumerate(tabs):
        with tab:
            f_df = master_df if i == 0 else master_df[master_df['Category'].str.contains(names[i], case=False, na=False)]
            render_content(f_df, names[i])

if __name__ == "__main__":
    main()
