import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- 1. Configuration ---
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """최신 리비전 및 날짜 정보를 추출합니다 (Remark 제외)."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def apply_professional_style():
    """전문적인 Compact UI 스타일 적용"""
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

# --- 2. Dialogs ---
@st.dialog("Resolve Duplicates")
def show_duplicate_resolve_dialog(df_dups):
    st.write("중복된 항목 중 최상단 레코드만 남기고 정합성을 확보합니다.")
    st.dataframe(df_dups, use_container_width=True, hide_index=True)
    if st.button("Confirm & Remove", type="primary", use_container_width=True):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        df_clean = df_raw.drop_duplicates(subset=['DWG. NO.'], keep='first')
        df_clean.to_excel(DB_PATH, sheet_name='DRAWING LIST', index=False, engine='openpyxl')
        st.rerun()

@st.dialog("Upload Master File")
def show_upload_dialog():
    st.write("새로운 Drawing Master 파일을 업로드하십시오.")
    uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'])
    if uploaded_file and st.button("Apply & Save", type="primary", use_container_width=True):
        df_new = pd.read_excel(uploaded_file, sheet_name='DRAWING LIST', engine='openpyxl')
        df_new.to_excel(DB_PATH, sheet_name='DRAWING LIST', index=False, engine='openpyxl')
        st.rerun()

# --- 3. UI Rendering ---
def render_drawing_table(display_df, tab_name):
    # 중복 검사 레이아웃 (복구)
    dups = display_df[display_df.duplicated(subset=['DWG. NO.'], keep=False)]
    if not dups.empty:
        c1, c2 = st.columns([8.5, 1.5])
        c1.error(f"⚠️ Duplicate Warning: {len(dups)} redundant records detected in this category.")
        if c2.button("Resolve", key=f"res_{tab_name}", use_container_width=True):
            show_duplicate_resolve_dialog(dups)

    # Revision Filter
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    f_key = f"sel_rev_{tab_name}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    r_cols = st.columns([1] * 7 + [7])
    for i, rev in enumerate(rev_list[:7]):
        count = len(display_df) if rev == "LATEST" else display_df['Rev'].value_counts().get(rev, 0)
        with r_cols[i]:
            if st.button(f"{rev}\n({count})", key=f"btn_{tab_name}_{rev}", 
                        type="primary" if st.session_state[f_key] == rev else "secondary", use_container_width=True):
                st.session_state[f_key] = rev
                st.rerun()

    # Action Toolbar
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    t_cols[0].markdown(f"**Total: {len(display_df):,} records**")
    with t_cols[2]:
        if st.button("📁 Upload", key=f"up_{tab_name}", use_container_width=True): show_upload_dialog()
    with t_cols[3]: st.button("📄 PDF Sync", key=f"pdf_{tab_name}", use_container_width=True)
    with t_cols[4]:
        export_out = BytesIO()
        display_df.to_excel(export_out, index=False, engine='openpyxl')
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    with t_cols[5]: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # Data Viewport (Drawing 컬럼을 맨 뒤로 배치)
    st.dataframe(
        display_df, use_container_width=True, hide_index=True, height=550,
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
    st.markdown("<div class='main-title'>Plant Drawing Integrated System</div>", unsafe_allow_html=True)

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
            "Drawing": f"https://example.com/view/{row.get('DWG. NO.')}" # 예시 경로
        })
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    with tabs[0]: render_drawing_table(master_df, "Master")
    with tabs[1]: render_drawing_table(master_df[master_df['Category'].str.contains('ISO', na=False)], "ISO")
    with tabs[2]: render_drawing_table(master_df[master_df['Category'].str.contains('Support', na=False)], "Support")
    with tabs[3]: render_drawing_table(master_df[master_df['Category'].str.contains('Valve', na=False)], "Valve")
    with tabs[4]: render_drawing_table(master_df[master_df['Category'].str.contains('Specialty', na=False)], "Specialty")

if __name__ == "__main__":
    show_doc_control()
