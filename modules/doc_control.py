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
    """Applies global CSS for text wrapping and compact layout."""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 15px !important; }
        
        /* Table Cell Text Wrapping */
        div[data-testid="stDataFrame"] [role="gridcell"] {
            white-space: normal !important;
            word-wrap: break-word !important;
            line-height: 1.2 !important;
        }
        div[data-testid="stDataFrame"] [role="gridcell"] div { font-size: 15px !important; }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Manage Duplicates")
def open_duplicate_manager(df):
    dup_mask = df.duplicated(subset=['DWG. NO.'], keep=False)
    dupes = df[dup_mask].sort_values('DWG. NO.')
    st.write(f"Identified **{len(dupes)}** duplicate entries.")
    st.dataframe(dupes[['Category', 'SYSTEM', 'DWG. NO.', 'Status']], use_container_width=True, hide_index=True)
    if st.button("Purge Duplicates", type="primary", use_container_width=True):
        clean_df = df.drop_duplicates(subset=['DWG. NO.'], keep='last')
        with pd.ExcelWriter(DB_PATH, engine='openpyxl') as writer:
            clean_df.to_excel(writer, sheet_name='DRAWING LIST', index=False)
        st.success("Duplicates removed.")
        st.rerun()

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error(f"Database file not found at {DB_PATH}")
        return

    # Load Data
    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    
    # Check Duplicates for UI Warning
    dup_list = df[df.duplicated(subset=['DWG. NO.'], keep=False)]['DWG. NO.'].unique()
    if len(dup_list) > 0:
        c1, c2 = st.columns([8, 2])
        with c1: st.warning(f"⚠️ Duplicate DWG. NO. detected ({len(dup_list)} cases)")
        with c2: 
            if st.button("🛠️ Manage Duplicates", use_container_width=True): open_duplicate_manager(df)

    # Data Transformation
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
            "Remark": l_rem
        })
    f_df = pd.DataFrame(p_data)

    # Toolbar
    res_col, btn_area = st.columns([2, 1])
    with res_col: st.info(f"Total: {len(f_df):,} records")
    with btn_area:
        # Simplified buttons for the example
        st.button("📁 Upload", use_container_width=True)

    # --- [ 핵심 수정부: 컬럼 간격 최적화 ] ---
    st.dataframe(
        f_df, 
        use_container_width=True, 
        hide_index=True, 
        height=800,
        column_config={
            "Category": st.column_config.TextColumn("Category", width=80), # 간격 축소
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=80),     # 간격 축소
            "Hold": st.column_config.TextColumn("Hold", width=60),         # 간격 최소화
            "Status": st.column_config.TextColumn("Status", width=80),     # 간격 축소
            "Rev": st.column_config.TextColumn("Rev", width=70),
            "Date": st.column_config.TextColumn("Date", width=100),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"), # 최대 확장
            "Remark": st.column_config.TextColumn("Remark", width="medium")           # 줄바꿈 적용됨
        }
    )
