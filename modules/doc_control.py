import streamlit as st
import pandas as pd
import os
import requests
import base64
from io import BytesIO

# --- Configuration & Secrets ---
DB_PATH = 'data/drawing_master.xlsx'
# Streamlit Cloud의 Settings > Secrets에 아래 정보를 설정해야 합니다.
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "")
PDF_STORAGE_PATH = "data/pdf_store"  # GitHub 내 도면 저장 폴더

def get_latest_rev_info(row):
    """최신 리비전 정보를 논리적으로 추출합니다."""
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
    """Compact UI 및 전문적인 시각적 레이아웃 적용"""
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

def upload_to_github(file_name, file_content):
    """GitHub API를 통해 파일을 레포지토리에 커밋합니다."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{PDF_STORAGE_PATH}/{file_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # 기존 파일 존재 여부 확인 (업데이트용 SHA 획득)
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None

    payload = {
        "message": f"System: Sync Drawing {file_name}",
        "content": base64.b64encode(file_content).decode('utf-8')
    }
    if sha: payload["sha"] = sha
    
    put_res = requests.put(url, headers=headers, json=payload)
    return put_res.status_code in [200, 201]

@st.dialog("PDF Drawing Synchronization")
def show_pdf_sync_dialog(master_df):
    """파일명 매칭 및 GitHub 자동 업로드 다이얼로그"""
    st.write("파일명 규칙: **[DWG-NO]_[REV].pdf** (예: A100_0.pdf)")
    files = st.file_uploader("Upload PDF Drawings", type=['pdf'], accept_multiple_files=True)
    
    if files and st.button("Start Auto-Matching & Sync", type="primary", use_container_width=True):
        valid_pairs = set(zip(master_df['DWG. NO.'].astype(str), master_df['Rev'].astype(str)))
        for f in files:
            name_only = os.path.splitext(f.name)[0]
            if "_" in name_only:
                d_no, rev = name_only.rsplit("_", 1)
                if (d_no, rev) in valid_pairs:
                    if upload_to_github(f.name, f.getvalue()):
                        st.toast(f"✅ Synced: {f.name}")
                    else: st.error(f"❌ GitHub Fail: {f.name}")
                else: st.warning(f"⚠️ No Match in List: {f.name}")
            else: st.error(f"❗ Format Error: {f.name}")
        st.success("Process Completed.")
        if st.button("Close"): st.rerun()

@st.dialog("Manage Duplicates")
def show_duplicate_dialog(df_dups):
    """중복 도면 제거 다이얼로그"""
    st.dataframe(df_dups, use_container_width=True, hide_index=True)
    if st.button("Remove Duplicates & Keep First", type="primary", use_container_width=True):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
        df_raw.drop_duplicates(subset=['DWG. NO.'], keep='first').to_excel(DB_PATH, index=False)
        st.rerun()

def render_drawing_table(display_df, tab_name):
    # --- 0. Duplicate Check Message ---
    dups = display_df[display_df.duplicated(subset=['DWG. NO.'], keep=False)]
    if not dups.empty:
        c1, c2 = st.columns([8, 2])
        c1.error(f"⚠️ **Duplicate Warning**: {len(dups)} redundant records detected.")
        if c2.button("Resolve", key=f"dup_btn_{tab_name}", use_container_width=True):
            show_duplicate_dialog(dups)

    # --- 1. Revision Filter ---
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    filter_key = f"sel_rev_{tab_name}"
    if filter_key not in st.session_state: st.session_state[filter_key] = "LATEST"
    
    rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    revs_to_show = rev_list[:7]
    r_cols = st.columns([1] * len(revs_to_show) + [max(1, 14 - len(revs_to_show))])
    
    for i, rev in enumerate(revs_to_show):
        count = len(display_df) if rev == "LATEST" else display_df['Rev'].value_counts().get(rev, 0)
        with r_cols[i]:
            if st.button(f"{rev}\n({count})", key=f"btn_{tab_name}_{rev}", 
                        type="primary" if st.session_state[filter_key] == rev else "secondary", use_container_width=True):
                st.session_state[filter_key] = rev
                st.rerun()

    # --- 2. Search & Filters ---
    st.markdown("<div class='section-label'>Search & Filters</div>", unsafe_allow_html=True)
    f_cols = st.columns([4, 2, 2, 2, 10])
    with f_cols[0]: search_term = st.text_input("Search", key=f"search_{tab_name}", placeholder="DWG. No. or Title...")
    with f_cols[1]: sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]: sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]: sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # Logic
    filtered_df = display_df.copy()
    if sel_sys != "All": filtered_df = filtered_df[filtered_df['SYSTEM'] == sel_sys]
    if sel_area != "All": filtered_df = filtered_df[filtered_df['Area'] == sel_area]
    if sel_stat != "All": filtered_df = filtered_df[filtered_df['Status'] == sel_stat]
    if st.session_state[filter_key] != "LATEST": filtered_df = filtered_df[filtered_df['Rev'] == st.session_state[filter_key]]
    if search_term:
        filtered_df = filtered_df[filtered_df['DWG. NO.'].astype(str).str.contains(search_term, case=False, na=False) | 
                                  filtered_df['Description'].astype(str).str.contains(search_term, case=False, na=False)]

    # --- 3. URL Generation for PDF View ---
    # GitHub Raw URL 형식으로 링크 컬럼 생성
    base_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{PDF_STORAGE_PATH}"
    filtered_df['Drawing'] = filtered_df.apply(lambda x: f"{base_url}/{x['DWG. NO.']}_{x['Rev']}.pdf", axis=1)

    # --- 4. Action Toolbar ---
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    with t_cols[0]: st.markdown(f"<span style='font-size:13px; font-weight:700;'>Total: {len(filtered_df):,} records</span>", unsafe_allow_html=True)
    with t_cols[3]: 
        if st.button("📄 PDF Sync", key=f"pdf_sync_{tab_name}", use_container_width=True):
            show_pdf_sync_dialog(display_df)
    
    # --- 5. Data Viewport with LinkColumn ---
    st.dataframe(
        filtered_df, use_container_width=True, hide_index=True, height=500,
        column_config={
            "Drawing": st.column_config.LinkColumn("Drawing", help="Click to open PDF", display_text="📄 View"),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Rev": st.column_config.TextColumn("Rev", width=60),
            "Date": st.column_config.TextColumn("Date", width=90),
            "Status": st.column_config.TextColumn("Status", width=70)
        }
    )

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Plant Drawing Integrated System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database (drawing_master.xlsx) not found.")
        return

    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'), "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', '-'), "Rev": l_rev, "Date": l_date,
            "Status": row.get('Status', '-'), "Remark": l_rem
        })
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    categories = ["", "ISO", "Support", "Valve", "Specialty|Speciality"]
    for i, tab in enumerate(tabs):
        with tab:
            if i == 0: render_drawing_table(master_df, "Master")
            else: render_drawing_table(master_df[master_df['Category'].str.contains(categories[i], case=False, na=False)], tab_name=categories[i])

if __name__ == "__main__":
    show_doc_control()
