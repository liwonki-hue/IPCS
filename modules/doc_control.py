import streamlit as st
import pandas as pd
import os
from io import BytesIO

# ---------------------------------------------------------
# 1. Configuration & Data Logic
# ---------------------------------------------------------
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """Extracts the most recent revision data logically."""
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
    """Enhanced CSS for button layout and text wrapping."""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 10px; }
        
        /* Compact Button Styling for Action Bar */
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 4px; border: 1px solid #dde3ec;
            height: 32px !important; font-size: 11px !important; font-weight: 600 !important;
            padding: 0 10px !important;
        }
        
        /* Table Cell Text Wrapping for Description & Remark */
        div[data-testid="stDataFrame"] [role="gridcell"] {
            white-space: normal !important;
            word-wrap: break-word !important;
            line-height: 1.3 !important;
        }
        div[data-testid="stDataFrame"] [role="gridcell"] div { font-size: 15px !important; }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Main View Function
# ---------------------------------------------------------
def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error(f"Database Error: '{DB_PATH}' not found.")
        return

    # Load and Process Data
    try:
        df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    except Exception as e:
        st.error(f"Excel Read Error: {e}")
        return

    # Process revision data
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

    # ---------------------------------------------------------
    # 3. Action Toolbar (1-Line Layout)
    # ---------------------------------------------------------
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    
    # Header Info & Action Buttons on one line
    info_col, btn1, btn2, btn3, btn4 = st.columns([4, 1, 1, 1, 1])
    
    with info_col:
        st.markdown(f"<div style='padding-top:5px;'><b>Total Count: {len(f_df):,} records</b></div>", unsafe_allow_html=True)
    
    with btn1:
        st.button("📁 Upload", use_container_width=True)
    with btn2:
        st.button("📄 PDF", use_container_width=True)
    with btn3:
        export_out = BytesIO()
        with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
            f_df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=export_out.getvalue(), file_name="Dwg_Master.xlsx", use_container_width=True)
    with btn4:
        st.button("🖨️ Print", use_container_width=True)

    # ---------------------------------------------------------
    # 4. Data Viewport (Optimized Column Gaps)
    # ---------------------------------------------------------
    st.dataframe(
        f_df, 
        use_container_width=True, 
        hide_index=True, 
        height=750,
        column_config={
            # Small widths for short text columns to maximize Description area
            "Category": st.column_config.TextColumn("Category", width=80),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=80),
            "Hold": st.column_config.TextColumn("Hold", width=60),
            "Status": st.column_config.TextColumn("Status", width=80),
            "Rev": st.column_config.TextColumn("Rev", width=70),
            "Date": st.column_config.TextColumn("Date", width=100),
            
            # Larger widths for content-heavy columns
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Remark": st.column_config.TextColumn("Remark", width="medium")
        }
    )
