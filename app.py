import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# --- 1. 데이터 로드 엔진 ---
DB_PATH = 'data/drawing_master.xlsx'
ROWS_PER_PAGE = 30

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
            "Rev": l_rev, "Date": l_date, "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'),
            "Link": row.get('Link', None)
        })
    return pd.DataFrame(p_data)

@st.cache_data
def load_data():
    if os.path.exists(DB_PATH):
        try:
            df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            return process_raw_df(df_raw)
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- 2. 안정적인 인쇄 스크립트 ---
def execute_print(df, title):
    table_html = df.to_html(index=False, border=1)
    print_html = f"<html><head><style>body{{font-family:sans-serif;font-size:10px;}}table{{width:100%;border-collapse:collapse;}}th,td{{border:1px solid #ccc;padding:5px;}}</style></head><body><h2>{title}</h2>{table_html}<script>window.print();</script></body></html>"
    st.components.v1.html(f"<script>var w=window.open(); w.document.write(`{print_html}`); w.document.close();</script>", height=0)

# --- 3. UI 구성 (레이아웃 복구) ---
def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # CSS: 타이틀 위치 유지 및 스타일 정의
    st.markdown("""
        <style>
        .block-container { padding-top: 5rem !important; }
        .main-title { 
            font-size: 32px; font-weight: 800; color: #1A4D94; 
            margin-bottom: 1.5rem; border-left: 8px solid #1A4D94; padding-left: 15px; 
        }
        .section-label { font-size: 12px; font-weight: 700; color: #555; margin: 20px 0 8px 0; text-transform: uppercase; }
        div[data-testid="stButton"] button { height: 35px !important; }
        </style>
    """, unsafe_allow_html=True)

    # 타이틀 (사용자 선호 위치 유지)
    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.info("데이터 파일이 없습니다. 파일을 업로드해 주세요.")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # [복구] REVISION FILTER 섹션
            st.markdown('<div class="section-label">REVISION FILTER</div>', unsafe_allow_html=True)
            rev_opts = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            
            sel_rev_key = f"rev_v8_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns(len(rev_opts[:7]) + 1)
            for idx, r_val in enumerate(rev_opts[:7]):
                count = len(curr_df) if r_val == "LATEST" else len(curr_df[curr_df['Rev'] == r_val])
                if r_cols[idx].button(f"{r_val} ({count})", key=f"btn_v8_{i}_{idx}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.rerun()

            # [에러 수정] 필터링 로직 (Line 123 대응)
            df_filt = curr_df.copy() 
            if st.session_state[sel_rev_key] != "LATEST": 
                df_filt = df_filt[df_filt['Rev'] == st.session_state[sel_rev_key]]
            
            # [복구] SEARCH & FILTERS 섹션 (4단 구성)
            st.markdown('<div class="section-label">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            s_col1, s_col2, s_col3, s_col4 = st.columns([4, 2, 2, 2])
            q = s_col1.text_input("DWG No. or Description", placeholder="Search...", key=f"q_v8_{i}", label_visibility="collapsed")
            s_col2.selectbox("All Systems", ["All Systems"], key=f"sys_{i}", label_visibility="collapsed")
            s_col3.selectbox("All Areas", ["All Areas"], key=f"area_{i}", label_visibility="collapsed")
            s_col4.selectbox("All Status", ["All Status"], key=f"stat_{i}", label_visibility="collapsed")
            
            if q: 
                df_filt = df_filt[df_filt['DWG. NO.'].str.contains(q, case=False) | df_filt['Description'].str.contains(q, case=False)]
            
            st.write(f"**Total Found: {len(df_filt):,} records**")

            # [복구] 액션 툴바 (4버튼 구성)
            b_cols = st.columns([6, 1, 1, 1, 1])
            with b_cols[1]: st.button("📁 Upload", key=f"up_v8_{i}", use_container_width=True)
            with b_cols[2]: st.button("📄 PDF Sync", key=f"sync_v8_{i}", use_container_width=True)
            
            # Export
            ex_io = BytesIO()
            df_filt.to_excel(ex_io, index=False)
            b_cols[3].download_button("📤 Export", data=ex_io.getvalue(), file_name=f"{tab_names[i]}.xlsx", key=f"ex_v8_{i}", use_container_width=True)
            
            # Print
            if b_cols[4].button("🖨️ Print", key=f"prt_v8_{i}", use_container_width=True):
                execute_print(df_filt, f"Document Control List - {tab_names[i]}")

            # 4. 데이터프레임
            st.dataframe(df_filt, use_container_width=True, hide_index=True, height=700)

if __name__ == "__main__":
    main()
