import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# --- 1. Configuration ---
DB_PATH = 'data/drawing_master.xlsx'
ITEMS_PER_PAGE = 30  # 한 페이지당 표시할 레코드 수

def get_latest_rev_info(row):
    """최신 리비전 정보를 추출합니다."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def apply_professional_style():
    """전문적인 스타일 및 네비게이터 디자인 적용"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .stApp { --primary-color: #28a745 !important; }
        .block-container { padding-top: 2.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 15px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 8px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase; }
        
        /* 버튼 및 네비게이터 스타일 */
        div.stButton > button { border-radius: 4px !important; height: 32px !important; font-size: 11px !important; font-weight: 600 !important; }
        div.stButton > button[kind="primary"] { background-color: #28a745 !important; color: white !important; }
        
        /* 페이지 네비게이터 레이아웃 */
        .nav-container { display: flex; align-items: center; justify-content: center; gap: 5px; margin-top: 20px; font-size: 13px; }
        </style>
    """, unsafe_allow_html=True)

# --- 2. Table & Pagination Rendering ---
def render_drawing_table(display_df, tab_name):
    # [기존 유지] Revision Filter
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    f_key = f"sel_rev_{tab_name}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    rev_counts = display_df['Rev'].value_counts()
    rev_options = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    r_cols = st.columns([1] * 7 + [7])
    for i, rev in enumerate(rev_options[:7]):
        count = len(display_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        with r_cols[i]:
            if st.button(f"{rev}\n({count})", key=f"btn_{tab_name}_{rev}", 
                        type="primary" if st.session_state[f_key] == rev else "secondary", use_container_width=True):
                st.session_state[f_key] = rev
                st.session_state[f"page_{tab_name}"] = 1  # 필터 변경 시 1페이지로 리셋
                st.rerun()

    # [기존 유지] Search & Filters
    st.markdown("<div class='section-label'>Search & Filters</div>", unsafe_allow_html=True)
    sf_cols = st.columns([4, 2, 2, 2, 6])
    search_query = sf_cols[0].text_input("Search", key=f"q_{tab_name}", placeholder="DWG No. or Title...")
    sel_sys = sf_cols[1].selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    sel_area = sf_cols[2].selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    sel_stat = sf_cols[3].selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 데이터 필터링 로직
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

    # --- Pagination Logic ---
    total_records = len(df)
    total_pages = math.ceil(total_records / ITEMS_PER_PAGE)
    p_key = f"page_{tab_name}"
    if p_key not in st.session_state: st.session_state[p_key] = 1
    
    start_idx = (st.session_state[p_key] - 1) * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_records)
    paginated_df = df.iloc[start_idx:end_idx]

    # [구성 유지] Data Viewport (Drawing 맨 오른쪽)
    st.dataframe(
        paginated_df, use_container_width=True, hide_index=True, height=1100, # 30줄 표시를 위해 높이 조절
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

    # [추가] Page Navigator (이미지 형식 적용)
    if total_pages > 0:
        st.markdown("---")
        nav_cols = st.columns([1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 2])
        
        # 이전 페이지 버튼
        with nav_cols[1]:
            if st.button("<", key=f"prev_{tab_name}", disabled=(st.session_state[p_key] == 1)):
                st.session_state[p_key] -= 1
                st.rerun()
        
        # 페이지 번호 표시 (최대 5개 표시 예시)
        for i in range(max(1, st.session_state[p_key]-2), min(total_pages+1, st.session_state[p_key]+3)):
            with nav_cols[i - max(1, st.session_state[p_key]-2) + 2]:
                if st.button(str(i), key=f"p_{tab_name}_{i}", 
                             type="primary" if i == st.session_state[p_key] else "secondary"):
                    st.session_state[p_key] = i
                    st.rerun()
        
        # 다음 페이지 버튼
        with nav_cols[7]:
            if st.button(">", key=f"next_{tab_name}", disabled=(st.session_state[p_key] == total_pages)):
                st.session_state[p_key] += 1
                st.rerun()
        
        # 현재 범위 정보 표시
        with nav_cols[8]:
            st.write(f"{start_idx + 1}-{end_idx} / {total_records}")

def show_doc_control():
    apply_professional_style()
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
    for i, tab in enumerate(tabs):
        tab_name = ["Master", "ISO", "Support", "Valve", "Specialty"][i]
        with tab:
            if i == 0: render_drawing_table(master_df, tab_name)
            else:
                filtered = master_df[master_df['Category'].str.contains(tab_name, case=False, na=False)]
                render_drawing_table(filtered, tab_name)

if __name__ == "__main__":
    show_doc_control()
