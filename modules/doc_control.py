import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- Configuration ---
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """최신 리비전 정보를 논리적으로 추출합니다 (Remark 제외)."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def apply_professional_style():
    """Compact UI 및 버튼 정렬 최적화 스타일 적용"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 2.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 15px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 8px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase; }
        
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 4px !important; border: 1px solid #dde3ec !important;
            height: 28px !important; font-size: 11px !important; font-weight: 600 !important;
            padding: 0px 8px !important; line-height: 1 !important;
        }
        div.stButton > button[kind="primary"] { background-color: #1657d0 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Resolve Duplicates")
def show_duplicate_dialog(df_dups):
    """중복 데이터를 확인하고 정리하는 다이얼로그"""
    st.write("아래 중복된 DWG. NO. 항목들을 검토하십시오.")
    st.dataframe(df_dups, use_container_width=True, hide_index=True)
    if st.button("Remove Duplicates & Save", type="primary", use_container_width=True):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
        df_raw.drop_duplicates(subset=['DWG. NO.'], keep='first').to_excel(DB_PATH, index=False)
        st.success("중복이 제거되었습니다.")
        st.rerun()

def render_drawing_table(display_df, tab_name):
    # --- 0. Duplicate Warning 복구 ---
    dups = display_df[display_df.duplicated(subset=['DWG. NO.'], keep=False)]
    if not dups.empty:
        c1, c2 = st.columns([8, 2])
        with c1:
            st.error(f"⚠️ Duplicate Warning: {len(dups)} redundant records detected.")
        with c2:
            if st.button("Resolve", key=f"dup_{tab_name}", use_container_width=True):
                show_duplicate_dialog(dups)

    # --- 1. Revision Filter (수량 표시) ---
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    f_key = f"sel_rev_{tab_name}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    rev_counts = display_df['Rev'].value_counts()
    rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    r_cols = st.columns([1] * 7 + [7])
    for i, rev in enumerate(rev_list[:7]):
        count = len(display_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        with r_cols[i]:
            if st.button(f"{rev}\n({count})", key=f"btn_{tab_name}_{rev}", 
                        type="primary" if st.session_state[f_key] == rev else "secondary", use_container_width=True):
                st.session_state[f_key] = rev
                st.rerun()

    # --- 2. Search & Filters ---
    st.markdown("<div class='section-label'>Search & Filters</div>", unsafe_allow_html=True)
    f_cols = st.columns([4, 2, 2, 2, 10])
    search_term = f_cols[0].text_input("Search", key=f"sch_{tab_name}", placeholder="DWG No. or Title...")
    sel_sys = f_cols[1].selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    sel_area = f_cols[2].selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    sel_stat = f_cols[3].selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 필터링 로직
    df = display_df.copy()
    if sel_sys != "All": df = df[df['SYSTEM'] == sel_sys]
    if sel_area != "All": df = df[df['Area'] == sel_area]
    if sel_stat != "All": df = df[df['Status'] == sel_stat]
    if st.session_state[f_key] != "LATEST": df = df[df['Rev'] == st.session_state[f_key]]
    if search_term:
        df = df[df['DWG. NO.'].astype(str).str.contains(search_term, case=False) | df['Description'].astype(str).str.contains(search_term, case=False)]

    # --- 3. Action Toolbar (우측 끝으로 완전 이동) ---
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    # 첫 번째 컬럼 비율을 15로 높여 버튼 5개를 우측 끝으로 밀착시킴
    t_cols = st.columns([15, 1.5, 1.5, 1.5, 1.5, 1.5]) 
    t_cols[0].markdown(f"**Total: {len(df):,} records**")
    
    with t_cols[1]: st.button("📁 Import", key=f"imp_{tab_name}", use_container_width=True)
    with t_cols[2]: st.button("📄 PDF", key=f"pdf_{tab_name}", use_container_width=True)
    with t_cols[3]:
        export_out = BytesIO()
        with pd.ExcelWriter(export_out) as writer: df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    with t_cols[4]: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # --- 4. Data Viewport (컬럼 최적화 및 Remark 삭제) ---
    # Drawing 컬럼은 URL 기반 가상 컬럼으로 생성 (이미지 예시 참고)
    df['Drawing'] = "📄 View" 

    st.dataframe(
        df, use_container_width=True, hide_index=True, height=550,
        column_config={
            "Drawing": st.column_config.TextColumn("Drawing", width=50), # 축소
            "Category": st.column_config.TextColumn("Category", width=70),
            "Area": st.column_config.TextColumn("Area", width=80),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=80),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width=650), # 대폭 확장
            "Rev": st.column_config.TextColumn("Rev", width=60),
            "Date": st.column_config.TextColumn("Date", width=90),
            "Status": st.column_config.TextColumn("Status", width=50) # 축소
        }
    )

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Plant Drawing Integrated System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database missing.")
        return

    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), 
            "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date,
            "Status": row.get('Status', '-')
        })
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_cats = ["", "ISO", "Support", "Valve", "Specialty"]
    for i, tab in enumerate(tabs):
        with tab:
            if i == 0: render_drawing_table(master_df, "Master")
            else: render_drawing_table(master_df[master_df['Category'].str.contains(tab_cats[i], case=False, na=False)], tab_cats[i])

if __name__ == "__main__":
    show_doc_control()
