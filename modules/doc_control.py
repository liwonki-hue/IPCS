import streamlit as st
import pandas as pd
import os
import requests
import base64
from io import BytesIO

# --- 1. Configuration & Initial Setup ---
DB_PATH = 'data/drawing_master.xlsx'
# GitHub 설정을 st.secrets에 등록하거나 필요 시 직접 입력하십시오.
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "")
PDF_STORAGE_PATH = "data/pdf_store"

def get_latest_rev_info(row):
    """최신 리비전 정보를 추출하며 Remark는 제외합니다."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def upload_to_github(file_name, file_content):
    """GitHub API를 통해 PDF 파일을 업로드합니다."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{PDF_STORAGE_PATH}/{file_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    payload = {"message": f"Sync {file_name}", "content": base64.b64encode(file_content).decode('utf-8')}
    if sha: payload["sha"] = sha
    return requests.put(url, headers=headers, json=payload).status_code in [200, 201]

# --- 2. Dialogs (Popups) ---
@st.dialog("PDF Drawing Sync")
def show_pdf_upload_dialog(master_df):
    """PDF 업로드 및 동기화 팝업"""
    st.write("Format: **[DWG-NO]_[REV].pdf**")
    uploaded_files = st.file_uploader("PDF 선택", type=['pdf'], accept_multiple_files=True)
    if uploaded_files and st.button("Sync to Repository", type="primary", use_container_width=True):
        valid_pairs = set(zip(master_df['DWG. NO.'].astype(str), master_df['Rev'].astype(str)))
        for f in uploaded_files:
            name = os.path.splitext(f.name)[0]
            if "_" in name:
                d_no, rev = name.rsplit("_", 1)
                if (d_no, rev) in valid_pairs:
                    upload_to_github(f.name, f.getvalue())
        st.success("동기화 완료")
        if st.button("Close"): st.rerun()

@st.dialog("Resolve Duplicates")
def show_duplicate_dialog(df_dups):
    st.dataframe(df_dups, use_container_width=True, hide_index=True)
    if st.button("Remove Duplicates", type="primary", use_container_width=True):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
        df_raw.drop_duplicates(subset=['DWG. NO.'], keep='first').to_excel(DB_PATH, index=False)
        st.rerun()

# --- 3. UI Rendering ---
def apply_professional_style():
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 2rem !important; }
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; border-bottom: 2px solid #f0f2f6; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; }
        div.stButton > button { border-radius: 4px !important; height: 28px !important; font-size: 11px !important; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(display_df, tab_name):
    # 중복 경고 복구
    dups = display_df[display_df.duplicated(subset=['DWG. NO.'], keep=False)]
    if not dups.empty:
        c1, c2 = st.columns([8, 2])
        c1.error(f"⚠️ {len(dups)} redundant records detected.")
        if c2.button("Resolve", key=f"dup_{tab_name}"): show_duplicate_dialog(dups)

    # 리비전 필터 (수량 복구)
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_counts = display_df['Rev'].value_counts()
    rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    r_cols = st.columns([1] * 7 + [7])
    for i, rev in enumerate(rev_list[:7]):
        count = len(display_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        with r_cols[i]:
            st.button(f"{rev}\n({count})", key=f"btn_{tab_name}_{rev}", use_container_width=True)

    # 액션 버튼 (우측 정렬)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([12, 1.5, 1.5, 1.5, 1.5, 1.5])
    t_cols[0].markdown(f"**Total: {len(display_df):,} records**")
    with t_cols[2]:
        if st.button("📄 PDF", key=f"pdf_btn_{tab_name}", use_container_width=True):
            show_pdf_upload_dialog(display_df)
    
    # 데이터 테이블 (Description 확장, Drawing/Status 축소)
    st.dataframe(
        display_df, use_container_width=True, hide_index=True, height=500,
        column_config={
            "Drawing": st.column_config.LinkColumn("Drawing", width=50),
            "Description": st.column_config.TextColumn("Description", width=600),
            "Status": st.column_config.TextColumn("Status", width=60)
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
            "Area": row.get('Area', '-'), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date, "Status": row.get('Status', '-')
        })
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]
    for i, tab in enumerate(tabs):
        with tab:
            if i == 0: render_drawing_table(master_df, tab_names[i])
            else: render_drawing_table(master_df[master_df['Category'].str.contains(tab_names[i], na=False)], tab_names[i])

# --- 4. Main Execution ---
if __name__ == "__main__":
    show_doc_control()
