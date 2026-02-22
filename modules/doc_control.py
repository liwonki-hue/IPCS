import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- 1. Configuration ---
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """최신 리비전 정보를 추출합니다 (Remark 제외)."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def apply_professional_style():
    """전문적인 스타일 적용 및 녹색 포인트 컬러 설정"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        /* 메인 컬러를 녹색(#28a745)으로 지정 */
        .stApp { --primary-color: #28a745 !important; }
        .block-container { padding-top: 2.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        
        /* 타이틀 스타일 */
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 15px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 8px; }
        
        /* 섹션 레이블 스타일 */
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase; }
        
        /* 버튼 스타일 조정 (Primary 선택 시 녹색 적용) */
        div.stButton > button { border-radius: 4px !important; height: 32px !important; font-size: 11px !important; font-weight: 600 !important; line-height: 1.2 !important; }
        div.stButton > button[kind="primary"] { background-color: #28a745 !important; color: white !important; border: none !important; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. Core Rendering Function ---
def render_drawing_table(display_df, tab_name):
    # [복구 및 색상 적용] Revision Filter
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    f_key = f"sel_rev_{tab_name}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    rev_counts = display_df['Rev'].value_counts()
    unique_revs = sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    rev_options = ["LATEST"] + unique_revs
    
    r_cols = st.columns([1] * 7 + [7])
    for i, rev in enumerate(rev_options[:7]):
        count = len(display_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        with r_cols[i]:
            # 선택 시 녹색(Primary)으로 표시됨
            if st.button(f"{rev}\n({count})", key=f"btn_{tab_name}_{rev}", 
                        type="primary" if st.session_state[f_key] == rev else "secondary", use_container_width=True):
                st.session_state[f_key] = rev
                st.rerun()

    # [복구] Search & Filters
    st.markdown("<div class='section-label'>Search & Filters</div>", unsafe_allow_html=True)
    sf_cols = st.columns([4, 2, 2, 2, 6])
    search_query = sf_cols[0].text_input("Search", key=f"q_{tab_name}", placeholder="DWG No. or Title...")
    sel_sys = sf_cols[1].selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    sel_area = sf_cols[2].selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    sel_stat = sf_cols[3].selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 필터링 로직
    df = display_df.copy()
    if st.session_state[f_key] != "LATEST":
        df = df[df['Rev'] == st.session_state[f_key]]
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
    with t_cols[2]: st.button("📁 Upload", key=f"up_{tab_name}", use_container_width=True)
    with t_cols[3]: st.button("📄 PDF Sync", key=f"pdf_{tab_name}", use_container_width=True)
    with t_cols[4]:
        export_out = BytesIO()
        df.to_excel(export_out, index=False, engine='openpyxl')
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    with t_cols[5]: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # Data Viewport (Drawing 맨 오른쪽 배치)
    st.dataframe(
        df, use_container_width=True, hide_index=True, height=550,
        column_config={
            "Category": st.column_config.TextColumn("Category", width=70),
            "Area": st.column_config.TextColumn("Area", width=70),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=70),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Rev": st.column_config.TextColumn("Rev", width=60),
            "Date": st.column_config.TextColumn("Date", width=90),
            "Hold": st.column_config.TextColumn("Hold", width=50),
            "Status": st.column_config.TextColumn("Status", width=70),
            "Drawing": st.column_config.LinkColumn("Drawing", width=70, display_text="📄 View")
        }
    )

def show_doc_control():
    apply_professional_style()
    # [변경] 메인 타이틀 수정
    st.markdown("<div class='main-title'>Document Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database missing.")
        return

    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
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
            "Status": row.get('Status', '-'),
            "Drawing": f"https://your-sharepoint-link.com/view?id={row.get('DWG. NO.')}" 
        })
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]
    
    for i, tab in enumerate(tabs):
        with tab:
            if i == 0: render_drawing_table(master_df, tab_names[i])
            else:
                filtered = master_df[master_df['Category'].str.contains(tab_names[i], case=False, na=False)]
                render_drawing_table(filtered, tab_names[i])

if __name__ == "__main__":
    show_doc_control()
