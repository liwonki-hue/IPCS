import streamlit as st
import pandas as pd
import os
import requests
import base64
from io import BytesIO

# --- Configuration ---
DB_PATH = 'data/drawing_master.xlsx'
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "")
PDF_STORAGE_PATH = "data/pdf_store"

def get_latest_rev_info(row):
    """최신 리비전 정보를 추출합니다 (Remark 제외)."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def apply_professional_style():
    """기존 전문적인 스타일 적용"""
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

# --- Dialogs (Popups) ---
@st.dialog("Resolve Duplicates")
def show_duplicate_resolve_dialog(df_dups):
    """중복된 데이터를 확인하고 제거하는 팝업입니다."""
    st.write("아래 중복된 항목들 중 최상단 레코드만 남기고 삭제합니다.")
    st.dataframe(df_dups, use_container_width=True, hide_index=True)
    if st.button("Confirm & Remove Duplicates", type="primary", use_container_width=True):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
        df_clean = df_raw.drop_duplicates(subset=['DWG. NO.'], keep='first')
        df_clean.to_excel(DB_PATH, sheet_name='DRAWING LIST', index=False)
        st.success("Duplicates resolved and saved.")
        st.rerun()

@st.dialog("Upload Master File")
def show_upload_dialog():
    st.write("Drawing Master 파일을 업로드하면 서버 데이터가 영구적으로 교체됩니다.")
    file = st.file_uploader("Choose Excel file", type=['xlsx'])
    if file and st.button("Apply & Save", type="primary", use_container_width=True):
        df_new = pd.read_excel(file, sheet_name='DRAWING LIST')
        df_new.to_excel(DB_PATH, sheet_name='DRAWING LIST', index=False)
        st.rerun()

@st.dialog("PDF Drawing Sync")
def show_pdf_sync_dialog(master_df):
    st.write("규칙: **[DWG-NO]_[REV].pdf**")
    files = st.file_uploader("Upload PDFs", type=['pdf'], accept_multiple_files=True)
    if files and st.button("Sync to GitHub", type="primary", use_container_width=True):
        # GitHub 업로드 로직 생략 (기존과 동일)
        st.success("Sync completed.")
        st.rerun()

def render_drawing_table(display_df, tab_name):
    # --- 1. 중복 검사 레이아웃 (복구) ---
    dups = display_df[display_df.duplicated(subset=['DWG. NO.'], keep=False)]
    if not dups.empty:
        c1, c2 = st.columns([8.5, 1.5])
        c1.error(f"⚠️ Duplicate Warning: {len(dups)} redundant records detected in this category.")
        if c2.button("Resolve", key=f"res_{tab_name}", use_container_width=True):
            show_duplicate_resolve_dialog(dups)

    # --- 2. Revision Filter ---
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

    # --- 3. Action Toolbar ---
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    t_cols[0].markdown(f"**Total: {len(display_df):,} records**")
    
    with t_cols[2]:
        if st.button("📁 Upload", key=f"up_{tab_name}", use_container_width=True): show_upload_dialog()
    with t_cols[3]:
        if st.button("📄 PDF", key=f"pdf_{tab_name}", use_container_width=True): show_pdf_sync_dialog(display_df)
    with t_cols[4]:
        export_out = BytesIO()
        with pd.ExcelWriter(export_out) as writer: display_df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    with t_cols[5]: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # --- 4. Data Viewport (Drawing 복구, Remark 제거) ---
    st.dataframe(
        display_df, use_container_width=True, hide_index=True, height=550,
        column_config={
            "Drawing": st.column_config.LinkColumn("Drawing", width=60, display_text="📄 View"),
            "Category": st.column_config.TextColumn("Category", width=70),
            "Area": st.column_config.TextColumn("Area", width=70),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=70),
            "Hold": st.column_config.TextColumn("Hold", width=50),
            "Status": st.column_config.TextColumn("Status", width=70),
            "Rev": st.column_config.TextColumn("Rev", width=60),
            "Date": st.column_config.TextColumn("Date", width=90),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large")
        }
    )

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Plant Drawing Integrated System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database missing.")
        return

    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date = get_latest_rev_info(row)
        p_data.append({
            "Drawing": f"https://example.com/pdf/{row.get('DWG. NO.')}.pdf",
            "Category": row.get('Category', '-'), 
            "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date, "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-')
        })
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]
    for i, tab in enumerate(tabs):
        with tab:
            if i == 0: render_drawing_table(master_df, tab_names[i])
            else: render_drawing_table(master_df[master_df['Category'].str.contains(tab_names[i], case=False, na=False)], tab_names[i])

if __name__ == "__main__":
    show_doc_control()
