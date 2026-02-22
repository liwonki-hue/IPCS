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
    """기존 로직: 최신 리비전 정보를 추출하며 Remark를 포함합니다."""
    revisions = [
        ('3rd REV', '3rd DATE', '3rd REMARK'), 
        ('2nd REV', '2nd DATE', '2nd REMARK'), 
        ('1st REV', '1st DATE', '1st REMARK')
    ]
    for r, d, m in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            rem = row.get(m, "")
            rem = "" if pd.isna(rem) or str(rem).lower() == "none" else str(rem)
            return val, row.get(d, '-'), rem
    return '-', '-', ''

def apply_professional_style():
    """기존 스타일 복구: Compact UI 및 Modal 디자인 적용."""
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
        div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            min-height: 30px !important; height: 30px !important; font-size: 12px !important;
        }
        .stSelectbox label, .stTextInput label { font-size: 11px !important; margin-bottom: 2px !important; font-weight: 700 !important; }
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

@st.dialog("PDF Drawing Sync")
def show_pdf_sync_dialog(master_df):
    """새로운 기능: PDF 도면 업로드 팝업"""
    st.write("파일명 규칙: **[DWG-NO]_[REV].pdf**")
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

@st.dialog("Upload Master File")
def show_upload_dialog():
    """기존 업로드 다이얼로그"""
    st.write("새로운 Drawing Master 파일을 업로드하십시오.")
    uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'])
    if uploaded_file and st.button("Apply & Save", type="primary", use_container_width=True):
        df_upload = pd.read_excel(uploaded_file, sheet_name='DRAWING LIST')
        df_upload.to_excel(DB_PATH, sheet_name='DRAWING LIST', index=False)
        st.success("Database Synchronized.")
        st.rerun()

def render_drawing_table(display_df, tab_name):
    # --- 1. Revision Filter (기존 레이아웃) ---
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    f_key = f"sel_rev_{tab_name}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    revs_to_show = rev_list[:7]
    r_cols = st.columns([1] * len(revs_to_show) + [max(1, 14 - len(revs_to_show))])
    
    for i, rev in enumerate(revs_to_show):
        count = len(display_df) if rev == "LATEST" else display_df['Rev'].value_counts().get(rev, 0)
        with r_cols[i]:
            if st.button(f"{rev}\n({count})", key=f"btn_{tab_name}_{rev}", 
                        type="primary" if st.session_state[f_key] == rev else "secondary", use_container_width=True):
                st.session_state[f_key] = rev
                st.rerun()

    # --- 2. Search & Filters (기존 레이아웃) ---
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
        df = df[df['DWG. NO.'].str.contains(search_term, case=False, na=False) | df['Description'].str.contains(search_term, case=False, na=False)]

    # --- 3. Action Toolbar (기존 버튼 위치 유지 + PDF 팝업 연결) ---
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    t_cols[0].markdown(f"**Total: {len(df):,} records**")
    
    with t_cols[2]:
        if st.button("📁 Upload", key=f"up_{tab_name}", use_container_width=True): show_upload_dialog()
    with t_cols[3]:
        if st.button("📄 PDF", key=f"pdf_{tab_name}", use_container_width=True): show_pdf_sync_dialog(display_df)
    with t_cols[4]:
        export_out = BytesIO()
        with pd.ExcelWriter(export_out) as writer: df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    with t_cols[5]: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # --- 4. Data Viewport (기존 컬럼 구성 복구) ---
    st.dataframe(
        df, use_container_width=True, hide_index=True, height=550,
        column_config={
            "Category": st.column_config.TextColumn("Category", width=70),
            "Area": st.column_config.TextColumn("Area", width=70),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=70),
            "Hold": st.column_config.TextColumn("Hold", width=50),
            "Status": st.column_config.TextColumn("Status", width=70),
            "Rev": st.column_config.TextColumn("Rev", width=60),
            "Date": st.column_config.TextColumn("Date", width=90),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Remark": st.column_config.TextColumn("Remark", width="medium")
        }
    )

def show_doc_control():
    """메인 레이아웃 실행 함수"""
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database missing.")
        return

    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), 
            "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date, "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'), "Remark": l_rem
        })
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    with tabs[0]: render_drawing_table(master_df, "Master")
    with tabs[1]: render_drawing_table(master_df[master_df['Category'].str.contains('ISO', case=False, na=False)], "ISO")
    with tabs[2]: render_drawing_table(master_df[master_df['Category'].str.contains('Support', case=False, na=False)], "Support")
    with tabs[3]: render_drawing_table(master_df[master_df['Category'].str.contains('Valve', case=False, na=False)], "Valve")
    with tabs[4]: render_drawing_table(master_df[master_df['Category'].str.contains('Specialty', case=False, na=False)], "Specialty")

# --- 실행부 (누락 주의) ---
if __name__ == "__main__":
    show_doc_control()
