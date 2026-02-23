import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- [1. 기본 설정 및 데이터 로직] ---
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
            "Link": row.get('Link', None) # PDF 연동 시 URL이 들어갈 컬럼
        })
    return pd.DataFrame(p_data)

@st.cache_data
def load_master_data():
    if os.path.exists(DB_PATH):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        return process_raw_df(df_raw)
    return pd.DataFrame()

# --- [2. 전문적 UI 스타일링] ---
def apply_pro_style():
    st.markdown("""
        <style>
        /* 화면 여백 및 배경 */
        .block-container { padding-top: 1.5rem !important; padding-bottom: 0rem !important; }
        
        /* 세련된 블루 타이틀 */
        .main-title { font-size: 34px; font-weight: 850; color: #1A4D94; margin-bottom: 5px; letter-spacing: -1px; }
        .sub-title { font-size: 13px; color: #666; margin-bottom: 20px; }

        /* 컴팩트 Revision 버튼 (크기 및 간격 축소) */
        div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"] button {
            padding: 2px 8px !important;
            height: 26px !important;
            min-height: 26px !important;
            font-size: 12px !important;
            border-radius: 4px !important;
        }

        /* Input 창 높이 축소 */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            min-height: 30px !important; height: 30px !important; font-size: 13px !important;
        }
        
        /* 섹션 라벨 정렬 */
        .section-label { font-size: 11px; font-weight: 700; color: #555; margin-bottom: -15px; }
        </style>
    """, unsafe_allow_html=True)

# --- [3. 인쇄 기능] ---
def execute_print_view(df, title):
    table_html = df.drop(columns=['Link']).to_html(index=False)
    html_content = f"""
    <html><head><title>{title}</title><style>
    table {{ width: 100%; border-collapse: collapse; font-size: 10px; font-family: sans-serif; }}
    th, td {{ border: 1px solid #333; padding: 4px; text-align: left; }}
    th {{ background: #eee; }}
    </style></head><body><h3>{title}</h3>{table_html}
    <script>window.print();</script></body></html>
    """
    st.components.v1.html(f"<script>var w=window.open(); w.document.write(`{html_content}`); w.document.close();</script>", height=0)

# --- [4. 메인 UI] ---
def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    apply_pro_style()

    st.markdown("<div class='main-title'>Document Control System</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Engineering Document & Drawing Management Dashboard</div>", unsafe_allow_html=True)

    master_df = load_master_data()
    if master_df.empty:
        st.info("No Master Data. Please check data/drawing_master.xlsx")
        return

    # A. 도면 중복 검사 (Expander)
    dups = master_df[master_df.duplicated('DWG. NO.', keep=False)]
    if not dups.empty:
        with st.expander(f"⚠️ Duplicate Drawing Detection ({len(dups)} issues found)", expanded=False):
            st.dataframe(dups.sort_values('DWG. NO.'), use_container_width=True, height=150)

    # B. 메인 탭 구성
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = master_df if i == 0 else master_df[master_df['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # 1. Revision Filter (Compact Layout)
            st.markdown("<p class='section-label'>REVISION FILTER</p>", unsafe_allow_html=True)
            revs = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            r_cols = st.columns([0.8] * 8 + [4]) # 버튼 간격을 좁게 배치
            
            sel_rev_key = f"rev_sel_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"

            for idx, r_val in enumerate(revs[:8]):
                if r_cols[idx].button(r_val, key=f"btn_{i}_{r_val}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary",
                                      use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.rerun()

            # 2. Search & Multi-Filters (중간까지만 배치)
            st.markdown("<p class='section-label'>SEARCH & FILTERS</p>", unsafe_allow_html=True)
            f_cols = st.columns([2.5, 1.2, 1.2, 1.2, 5.9]) # 검색창과 필터 3개를 합쳐서 약 60% 비중 차지
            
            q_search = f_cols[0].text_input("Search", placeholder="DWG No. or Title", label_visibility="collapsed", key=f"q_{i}")
            f_sys = f_cols[1].selectbox("System", ["All Systems"] + sorted(curr_df['SYSTEM'].unique().tolist()), label_visibility="collapsed", key=f"sys_{i}")
            f_area = f_cols[2].selectbox("Area", ["All Areas"] + sorted(curr_df['Area'].unique().tolist()), label_visibility="collapsed", key=f"area_{i}")
            f_stat = f_cols[3].selectbox("Status", ["All Status"] + sorted(curr_df['Status'].unique().tolist()), label_visibility="collapsed", key=f"stat_{i}")

            # 데이터 필터링 로직
            df_final = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": df_final = df_final[df_final['Rev'] == st.session_state[sel_rev_key]]
            if q_search: df_final = df_final[df_final['DWG. NO.'].str.contains(q_search, case=False) | df_final['Description'].str.contains(q_search, case=False)]
            if f_sys != "All Systems": df_final = df_final[df_final['SYSTEM'] == f_sys]
            if f_area != "All Areas": df_final = df_final[df_final['Area'] == f_area]
            if f_stat != "All Status": df_final = df_final[df_final['Status'] == f_stat]

            # 3. Action Buttons (컴팩트 높이 유지)
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            a_cols = st.columns([7, 1, 1, 1, 1])
            a_cols[0].markdown(f"**Total Found: {len(df_final):,} items**")
            
            with a_cols[1]: st.button("📁 Upload", key=f"up_{i}", use_container_width=True)
            with a_cols[2]:
                if st.button("📄 PDF Sync", key=f"sync_{i}", use_container_width=True):
                    st.success("Synchronized with Server.")
            with a_cols[3]:
                out = BytesIO()
                df_final.to_excel(out, index=False)
                st.download_button("📤 Export", data=out.getvalue(), file_name="export.xlsx", use_container_width=True)
            with a_cols[4]:
                if st.button("🖨️ Print", key=f"pr_{i}", use_container_width=True):
                    execute_print_view(df_final, f"Document List - {tab_names[i]}")

            # 4. Drawing List Table (아이콘 링크 설정)
            st.dataframe(
                df_final,
                use_container_width=True,
                hide_index=True,
                height=600,
                column_config={
                    "Link": st.column_config.LinkColumn(
                        "Drawing View",
                        help="Click to open PDF",
                        display_text="🔗 View" # 링크 값이 있을 때만 아이콘 활성화
                    ),
                    "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
                    "Description": st.column_config.TextColumn("Description", width="large")
                }
            )

if __name__ == "__main__":
    main()
