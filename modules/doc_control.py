import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Configuration
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """Extracts the most recent revision data from the document control records."""
    for r, d, m in [('3rd REV', '3rd DATE', '3rd REMARK'), 
                    ('2nd REV', '2nd DATE', '2nd REMARK'), 
                    ('1st REV', '1st DATE', '1st REMARK')]:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            rem = row.get(m, "")
            rem = "" if pd.isna(rem) or str(rem).lower() == "none" else str(rem)
            return val, row.get(d, '-'), rem
    return '-', '-', ''

def apply_professional_style():
    """Applies global CSS for fixed headers, compact buttons, and table typography."""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 5rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; }
        .section-label { font-size: 10px !important; font-weight: 700; color: #6b7a90; margin-bottom: 5px; text-transform: uppercase; }
        
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 4px; border: 1px solid #dde3ec;
            height: 30px !important; font-size: 10px !important; font-weight: 600 !important;
            padding: 0 4px !important; white-space: nowrap !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }
        
        /* Force text wrapping in dataframe cells for better visibility of remarks */
        div[data-testid="stDataFrame"] [role="gridcell"] div { 
            font-size: 18px !important; 
            white-space: normal !important; 
            line-height: 1.2 !important; 
        }
        div[data-testid="stDataFrame"] [role="columnheader"] p { font-size: 18px !important; font-weight: 800 !important; }
        </style>
    """, unsafe_allow_html=True)

# [Dialog functions for Duplicates and Upload remain identical to the previous version...]
@st.dialog("Duplicate Management")
def open_duplicate_manager(df):
    dup_mask = df.duplicated(subset=['DWG. NO.'], keep=False)
    dupes = df[dup_mask].sort_values('DWG. NO.')
    st.write(f"Total **{len(dupes)}** duplicate entries identified.")
    st.dataframe(dupes[['Category', 'SYSTEM', 'DWG. NO.', 'Status']], use_container_width=True, hide_index=True)
    st.warning("Action Required: Cleaning duplicates will retain only the 'latest' entry (bottom-most).")
    if st.button("Confirm & Purge Duplicates", type="primary", use_container_width=True):
        clean_df = df.drop_duplicates(subset=['DWG. NO.'], keep='last')
        with pd.ExcelWriter(DB_PATH, engine='openpyxl') as writer:
            clean_df.to_excel(writer, sheet_name='DRAWING LIST', index=False)
        st.success("Database optimization complete.")
        st.rerun()

@st.dialog("Upload & Merge Database")
def open_upload_dialog():
    st.info("Upload new support drawings to integrate with the master list.")
    upload_mode = st.radio("Upload Mode", ["Append (Merge)", "Replace (Overwrite)"], horizontal=True)
    new_file = st.file_uploader("Select Excel File", type=['xlsx'])
    if new_file:
        new_df = pd.read_excel(new_file, sheet_name='DRAWING LIST')
        if upload_mode == "Append (Merge)" and os.path.exists(DB_PATH):
            old_df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
            final_df = pd.concat([old_df, new_df], ignore_index=True)
        else:
            final_df = new_df
        with pd.ExcelWriter(DB_PATH, engine='openpyxl') as writer:
            final_df.to_excel(writer, sheet_name='DRAWING LIST', index=False)
        st.success("Upload Completed.")
        if st.button("Apply & Close"): st.rerun()

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("System Error: 'drawing_master.xlsx' not detected.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    dup_list = df[df.duplicated(subset=['DWG. NO.'], keep=False)]['DWG. NO.'].unique()

    if len(dup_list) > 0:
        c1, c2 = st.columns([7, 3])
        with c1: st.warning(f"⚠️ Duplicate Drawing No. Detected ({len(dup_list)} cases)")
        with c2: 
            if st.button("🛠️ Manage Duplicates", use_container_width=True): open_duplicate_manager(df)

    p_data = []
    for _, row in df.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'),
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date,
            "Hold": row.get('HOLD Y/N', 'N'), "Status": row.get('Status', '-'),
            "Remark": l_rem, "AREA": row.get('AREA', '-')
        })
    f_df = pd.DataFrame(p_data)

    # UI - Revision Filter
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    rev_area, _ = st.columns([1, 1])
    with rev_area:
        target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
        rev_cols = st.columns(len(target_revs[:7]))
        for i, rev in enumerate(target_revs[:7]):
            count = len(f_df) if rev == "LATEST" else f_df['Rev'].value_counts().get(rev, 0)
            if rev_cols[i].button(f"{rev}({count})", key=f"r_{rev}", 
                                  type="primary" if st.session_state.sel_rev == rev else "secondary", 
                                  use_container_width=True):
                st.session_state.sel_rev = rev
                st.rerun()

    # Action Toolbar
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    res_col, btn_area = st.columns([2, 1])
    with res_col: st.markdown(f"<div style='font-size:13px; font-weight:600; padding-top:8px;'>Total: {len(f_df):,} records</div>", unsafe_allow_html=True)
    with btn_area:
        b1, b2, b3, b4 = st.columns(4)
        with b1: 
            if st.button("📁 Upload", use_container_width=True): open_upload_dialog()
        with b2: st.button("📄 PDF", use_container_width=True)
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer: f_df.to_excel(writer, index=False)
            st.download_button("📤 Export", data=export_out.getvalue(), file_name="Dwg_Master_Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Print", use_container_width=True)

    # --- [Key Fix] Data Viewport with Column Configuration ---
    display_cols = ["Category", "SYSTEM", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]
    
    st.dataframe(
        f_df[display_cols], 
        use_container_width=True, 
        hide_index=True, 
        height=700,
        column_config={
            "Remark": st.column_config.TextColumn(
                "Remark",
                width="large",      # Increases the width of the column
                help="Latest Revision Remark"
            ),
            "Description": st.column_config.TextColumn(
                "Description",
                width="medium"
            ),
            "DWG. NO.": st.column_config.TextColumn(
                "DWG. NO.",
                width="medium"
            )
        }
    )
