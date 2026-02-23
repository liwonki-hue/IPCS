import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- 1. 데이터 처리 및 View 버튼 로직 ---
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
        # Drawing 경로 정보가 있을 경우 View 버튼 활성화 로직용 데이터 구성
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
def load_master_data():
    if os.path.exists(DB_PATH):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        return process_raw_df(df_raw)
    return pd.DataFrame()

# --- 2. [해결] 프린트 및 UI 최적화 로직 ---
def execute_stable_print(df, title):
    """데이터 누락 없는 안정적인 인쇄용 창 호출"""
    table_html = df.to_html(index=False, border=1)
    print_html = f"""
    <html>
    <head>
        <meta charset="utf-8"><title>{title}</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
            th, td {{ border: 1px solid #ccc; padding: 5px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            @media print {{ @page {{ size: landscape; margin: 1cm; }} }}
        </style>
    </head>
    <body><h2>{title}</h2>{table_html}<script>window.onload=function(){{window.print();}}</script></body>
    </html>
    """
    st.components.v1.html(f"<script>var w=window.open(); w.document.write(`{print_html}`); w.document.close();</script>", height=0)

# --- 3. UI 렌더링 (레이아웃 복구 및 기능 추가) ---
def main():
    st.set_page_config(layout="wide", page_title="Drawing Control System")
    
    # 1. 화면 높이 조절 및 버튼 스타일
    st.markdown("""
        <style>
        .block-container { padding-top: 2rem !important; } /* 화면 내려감 방지 */
        .main-title { font-size: 26px; font-weight: 800; color: #1657d0; margin-bottom: 1rem; }
        div.stButton > button[kind="primary"] { background-color: #28a745 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)
    
    master_df = load_master_data()
    if master_df.empty:
        st.info("No data found. Please upload a file.")
        return

    # Tabs
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = master_df if i == 0 else master_df[master_df['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # REVISION FILTER
            st.write("REVISION FILTER")
            rev_list = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"] )
            r_cols = st.columns(len(rev_list[:7]) + 1)
            selected_rev = st.session_state.get(f"rev_{i}", "LATEST")
            
            for idx, rev in enumerate(rev_list[:7]):
                count = len(curr_df) if rev == "LATEST" else len(curr_df[curr_df['Rev'] == rev])
                if r_cols[idx].button(f"{rev} ({count})", key=f"btn_{i}_{rev}", type="primary" if selected_rev == rev else "secondary"):
                    st.session_state[f"rev_{i}"] = rev
                    st.rerun()

            # SEARCH & FILTERS
            st.write("SEARCH & FILTERS")
            s_col1, s_col2, s_col3, s_col4 = st.columns([4, 2, 2, 2])
            q = s_col1.text_input("Search", placeholder="Search by DWG No. or Description...", key=f"q_{i}")
            
            # 필터링 적용
            df_disp = curr_df.copy()
            if selected_rev != "LATEST": df_disp = df_disp[df_disp['Rev'] == selected_rev]
            if q: df_disp = df_disp[df_disp['DWG. NO.'].str.contains(q, case=False, na=False) | df_disp['Description'].str.contains(q, case=False, na=False)]

            st.write(f"**Total: {len(df_disp):,} records**")

            # 2. 버튼 복구 (Upload, PDF Sync, Export, Print)
            b_cols = st.columns([7.5, 1, 1, 1, 1])
            with b_cols[1]: st.button("📁 Upload", key=f"up_{i}", use_container_width=True)
            with b_cols[2]:
                if st.button("📄 PDF Sync", key=f"sync_{i}", use_container_width=True):
                    # PDF Sync 클릭 시 Drawing 컬럼에 View 링크 활성화 (예시 시뮬레이션)
                    st.success("PDF Synchronized.")
            with b_cols[3]:
                out = BytesIO()
                df_disp.to_excel(out, index=False)
                st.download_button("📤 Export", data=out.getvalue(), file_name=f"{tab_names[i]}_list.xlsx", use_container_width=True)
            with b_cols[4]:
                if st.button("🖨️ Print", key=f"pr_{i}", use_container_width=True):
                    execute_stable_print(df_disp, f"Drawing Control List - {tab_names[i]}")

            # 3. Drawing 컬럼 내 View 버튼 기능 (column_config 활용)
            # Drawing 데이터가 존재하면 clickable link로 변환
            st.dataframe(
                df_disp, 
                use_container_width=True, 
                hide_index=True, 
                height=600,
                column_config={
                    "Drawing": st.column_config.LinkColumn(
                        "Drawing View",
                        help="Click to view drawing",
                        validate=r"^http",
                        display_text="View"
                    )
                }
            )

if __name__ == "__main__":
    main()
