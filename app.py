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
            "Drawing": row.get('Drawing', row.get('DRAWING', '-')) # Status 다음 마지막 위치 고정
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

# --- 2. [핵심] 인쇄 전용 HTML 생성 로직 ---
def generate_print_html(df, title):
    table_html = df.to_html(index=False, border=1)
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            h2 {{ color: #1657d0; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
            th, td {{ border: 1px solid #ccc; padding: 5px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            @media print {{ @page {{ size: landscape; margin: 1cm; }} }}
        </style>
    </head>
    <body>
        <h2>{title}</h2>
        {table_html}
        <script>window.onload = function() {{ window.print(); }}</script>
    </body>
    </html>
    """
    return html_content.encode('utf-8')

# --- 3. UI 스타일 및 렌더링 ---
def apply_styles():
    st.markdown("""
        <style>
        .main-title { font-size: 28px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 25px !important; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 20px; margin-bottom: 8px; text-transform: uppercase; }
        div.stButton > button[kind="primary"] { 
            background-color: #28a745 !important; 
            color: white !important; 
            border: none !important;
        }
        div.stButton > button { border-radius: 4px !important; }
        </style>
    """, unsafe_allow_html=True)

def render_content(base_df, tab_id):
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True) # 타이틀 복구
    
    # 중복 경고 표시 유지
    dupes = base_df[base_df.duplicated(['DWG. NO.'], keep=False)]
    if not dupes.empty:
        st.warning(f"⚠️ Duplicate Warning: {len(dupes)} redundant records detected.")

    # REVISION FILTER
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    f_key = f"rev_{tab_id}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    rev_list = ["LATEST"] + sorted([r for r in base_df['Rev'].unique() if pd.notna(r) and r != "-"])
    r_cols = st.columns([1.5, 1, 1, 1, 1, 1, 7.5])
    for i, r in enumerate(rev_list[:6]):
        cnt = len(base_df) if r == "LATEST" else (base_df['Rev'] == r).sum()
        with r_cols[i]:
            if st.button(f"{r} ({cnt})", key=f"bt_{tab_id}_{r}", type="primary" if st.session_state[f_key] == r else "secondary", use_container_width=True):
                st.session_state[f_key] = r
                st.rerun()

    # SEARCH & FILTERS
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

    st.markdown(f"**Total: {len(df):,} records**")
    
    # 버튼 영역
    t_cols = st.columns([8.5, 1, 1, 1, 1])
    with t_cols[1]:
        st.button("📁 Upload", key=f"up_{tab_id}", use_container_width=True)
    with t_cols[2]:
        st.button("📄 PDF Sync", key=f"sync_{tab_id}", use_container_width=True)
    with t_cols[3]:
        out = BytesIO()
        df.to_excel(out, index=False)
        st.download_button("📤 Export", data=out.getvalue(), file_name=f"{tab_id}_list.xlsx", key=f"ex_{tab_id}", use_container_width=True)
    with t_cols[4]:
        # [최종 해결책] HTML 파일 다운로드 방식의 인쇄
        print_html = generate_print_html(df, f"Drawing Control List - {tab_id}")
        st.download_button("🖨️ Print", data=print_html, file_name=f"print_{tab_id}.html", mime="text/html", key=f"pr_{tab_id}", use_container_width=True)

    # 테이블 렌더링
    st.dataframe(df, use_container_width=True, hide_index=True, height=700)

def main():
    st.set_page_config(layout="wide", page_title="Drawing Control System")
    apply_styles()
    master_df = load_master_data()
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    names = ["Master", "ISO", "Support", "Valve", "Specialty"]
    for i, tab in enumerate(tabs):
        with tab:
            f_df = master_df if i == 0 else master_df[master_df['Category'].str.contains(names[i], case=False, na=False)]
            render_content(f_df, names[i])

if __name__ == "__main__":
    main()
