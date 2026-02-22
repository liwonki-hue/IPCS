import streamlit as st
import pandas as pd
import os
import requests
import base64
from io import BytesIO

# --- Configuration & Secrets ---
DB_PATH = 'data/drawing_master.xlsx'
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "")
PDF_STORAGE_PATH = "data/pdf_store"

def get_latest_rev_info(row):
    """최신 리비전 정보를 추출하며 Remark 데이터는 제외합니다."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def apply_professional_style():
    """Compact UI 및 고해상도 레이아웃 스타일 적용"""
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

@st.dialog("Sync Drawing (PDF)")
def show_pdf_sync_dialog(master_df):
    st.write("Format: **[DWG-NO]_[REV].pdf**")
    files = st.file_uploader("Upload PDF", type=['pdf'], accept_multiple_files=True)
    if files and st.button("Sync to Repository", type="primary", use_container_width=True):
        valid_pairs = set(zip(master_df['DWG. NO.'].astype(str), master_df['Rev'].astype(str)))
        for f in files:
            name = os.path.splitext(f.name)[0]
            if "_" in name:
                d_no, rev = name.rsplit("_", 1)
                if (d_no, rev) in valid_pairs:
                    # GitHub 업로드 함수 호출 (정의되어 있다고 가정)
                    pass 
        st.success("Sync Process Finished.")
        if st.button("Close"): st.rerun()

def render_drawing_table(display_df, tab_name):
    # --- 1. Revision Filter (수량 표시 복구) ---
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

    # Logic
    df = display_df.copy()
    if sel_sys != "All": df = df[df['SYSTEM'] == sel_sys]
    if sel_area != "All": df = df[df['Area'] == sel_area]
    if sel_stat != "All": df = df[df['Status'] == sel_stat]
    if st.session_state[f_key] != "LATEST": df = df[df['Rev'] == st.session_state[f_key]]
    if search_term:
        df = df[df['DWG. NO.'].astype(str).str.contains(search_term, case=False) | df['Description'].astype(str).str.contains(search_term, case=False)]

    # --- 3. Action Toolbar (버튼 완전 우측 정렬) ---
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    # 첫 번째 컬럼 비율(10)을 크게 하여 버튼들을 오른쪽으로 밀어냅니다.
    t_cols = st.columns([10, 1.5, 1.5, 1.5, 1.5, 1.5]) 
    t_cols[0].markdown(f"**Total: {len(df):,} records**")
    
    with t_cols[1]: st.button("📁 Import", key=f"imp_{tab_name}", use_container_width=True)
    with t_cols[2]: 
        if st.button("📄 PDF", key=f"pdf_btn_{tab_name}", use_container_width=True):
            show_pdf_sync_dialog(display_df)
    
    with t_cols[3]:
        export_out = BytesIO()
        with pd.ExcelWriter(export_out) as writer: df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    
    with t_cols[4]: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # --- 4. Data Viewport (컬럼 최적화 및 Remark 삭제) ---
    base_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{PDF_STORAGE_PATH}"
    df['Drawing'] = df.apply(lambda x: f"{base_url}/{x['DWG. NO.']}_{x['Rev']}.pdf", axis=1)

    st.dataframe(
        df, use_container_width=True, hide_index=True, height=550,
        column_config={
            "Drawing": st.column_config.LinkColumn("Drawing", width=50, display_text="📄 View"),
            "Category": st.column_config.TextColumn("Category", width=70),
            "Area": st.column_config.TextColumn("Area", width=80),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=80),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width=600), # 넓게 확장
            "Rev": st.column_config.TextColumn("Rev", width=60),
            "Date": st.column_config.TextColumn("Date", width=90),
            "Status": st.column_config.TextColumn("Status", width=60) # 축소
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
