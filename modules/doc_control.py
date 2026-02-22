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
    """최신 리비전 정보를 논리적으로 추출합니다 (Remark 제외)."""
    revisions = [
        ('3rd REV', '3rd DATE'), 
        ('2nd REV', '2nd DATE'), 
        ('1st REV', '1st DATE')
    ]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def apply_professional_style():
    """Compact UI 스타일 적용"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 2.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 15px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 8px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase; }
        
        /* 버튼 스타일 복구 및 우측 정렬 보조 */
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 4px !important; border: 1px solid #dde3ec !important;
            height: 28px !important; font-size: 11px !important; font-weight: 600 !important;
            padding: 0px 8px !important; line-height: 1 !important;
        }
        div.stButton > button[kind="primary"] { background-color: #1657d0 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

def upload_to_github(file_name, file_content):
    """GitHub API 파일 업로드 로직"""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{PDF_STORAGE_PATH}/{file_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    payload = {"message": f"Sync {file_name}", "content": base64.b64encode(file_content).decode('utf-8')}
    if sha: payload["sha"] = sha
    return requests.put(url, headers=headers, json=payload).status_code in [200, 201]

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
                    upload_to_github(f.name, f.getvalue())
        st.success("Sync Completed.")
        if st.button("Close"): st.rerun()

@st.dialog("Import Master File")
def show_import_dialog():
    uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'])
    if uploaded_file and st.button("Apply & Save", type="primary", use_container_width=True):
        pd.read_excel(uploaded_file, sheet_name='DRAWING LIST').to_excel(DB_PATH, index=False)
        st.rerun()

@st.dialog("Resolve Duplicates")
def show_duplicate_dialog(df_dups):
    st.dataframe(df_dups, use_container_width=True, hide_index=True)
    if st.button("Remove Duplicates", type="primary", use_container_width=True):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
        df_raw.drop_duplicates(subset=['DWG. NO.'], keep='first').to_excel(DB_PATH, index=False)
        st.rerun()

def render_drawing_table(display_df, tab_name):
    # --- 0. Duplicate Warning (Tabs와 Filter 사이 고정) ---
    dups = display_df[display_df.duplicated(subset=['DWG. NO.'], keep=False)]
    if not dups.empty:
        c1, c2 = st.columns([8, 2])
        c1.error(f"⚠️ Duplicate Warning: {len(dups)} redundant records detected.")
        if c2.button("Resolve", key=f"dup_{tab_name}", use_container_width=True): show_duplicate_dialog(dups)

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

    # --- 3. Action Toolbar (버튼 우측 정렬 복구) ---
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([8, 1.5, 1.5, 1.5, 1.5, 1.5]) # 좌측 여백 늘려 버튼을 우측으로 밀어냄
    t_cols[0].markdown(f"**Total: {len(df):,} records**")
    
    if t_cols[1].button("📁 Import", key=f"imp_{tab_name}", use_container_width=True): show_import_dialog()
    if t_cols[2].button("📄 PDF", key=f"pdf_{tab_name}", use_container_width=True): show_pdf_sync_dialog(display_df)
    
    export_out = BytesIO()
    with pd.ExcelWriter(export_out) as writer: df.drop(columns=['Drawing']).to_excel(writer, index=False)
    t_cols[3].download_button("📤 Export", data=export_out.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    t_cols[4].button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # --- 4. Data Viewport (컬럼 길이 조정) ---
    base_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{PDF_STORAGE_PATH}"
    df['Drawing'] = df.apply(lambda x: f"{base_url}/{x['DWG. NO.']}_{x['Rev']}.pdf", axis=1)

    st.dataframe(
        df, use_container_width=True, hide_index=True, height=550,
        column_config={
            "Drawing": st.column_config.LinkColumn("Drawing", width=50, display_text="📄 View"), # 축소
            "Category": st.column_config.TextColumn("Category", width=70),
            "Area": st.column_config.TextColumn("Area", width=70),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=70),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width=450), # 대폭 확장
            "Rev": st.column_config.TextColumn("Rev", width=60),
            "Date": st.column_config.TextColumn("Date", width=90),
            "Status": st.column_config.TextColumn("Status", width=60) # 축소
        }
    )

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Plant Drawing Integrated System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database file not found.")
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
            "Rev": l_rev, 
            "Date": l_date,
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
