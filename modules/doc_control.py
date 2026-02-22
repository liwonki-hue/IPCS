import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Configuration
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """Extracts the latest revision information logically."""
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
    """Applies compact UI and professional modal design."""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 2.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 15px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 8px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase; }
        
        /* Widget reduction style */
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
        
        /* Warning message box */
        .duplicate-warning {
            padding: 10px; background-color: #fff4f4; border: 1px solid #ffcdd2;
            border-radius: 4px; color: #c62828; font-size: 13px; font-weight: 600;
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Duplicate Drawing Management")
def show_duplicate_dialog(df_duplicates):
    """Displays duplicate records and provides cleanup functionality."""
    st.warning(f"Total {len(df_duplicates)} duplicate records detected based on DWG. NO.")
    st.dataframe(df_duplicates, use_container_width=True, hide_index=True)
    
    st.info("Clicking 'Remove Duplicates' will retain the first occurrence and delete others from the master file.")
    
    if st.button("Confirm & Remove Duplicates", type="primary", use_container_width=True):
        try:
            # Load raw data to ensure absolute cleanup
            df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
            df_cleaned = df_raw.drop_duplicates(subset=['DWG. NO.'], keep='first')
            
            # Save back to Database
            df_cleaned.to_excel(DB_PATH, sheet_name='DRAWING LIST', index=False)
            
            st.success("Duplicates removed successfully.")
            st.rerun()
        except Exception as e:
            st.error(f"Execution Error: {str(e)}")

def render_drawing_table(display_df, tab_name):
    # --- 0. Duplicate Check (Placed between Tab and Revision Filter) ---
    duplicates = display_df[display_df.duplicated(subset=['DWG. NO.'], keep=False)]
    if not duplicates.empty:
        col_msg, col_btn = st.columns([8, 2])
        with col_msg:
            st.error(f"⚠️ **Duplicate Warning**: {len(duplicates)} records with redundant Drawing Numbers found.")
        with col_btn:
            if st.button("Manage Duplicates", key=f"btn_dup_{tab_name}", use_container_width=True):
                show_duplicate_dialog(duplicates)

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

    # --- 2. Search & Area Filters ---
    st.markdown("<div class='section-label'>Search & Filters</div>", unsafe_allow_html=True)
    f_cols = st.columns([4, 2, 2, 2, 10])
    with f_cols[0]:
        search_term = st.text_input("Search", key=f"search_{tab_name}", placeholder="DWG. No. or Title...")
    with f_cols[1]:
        sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]:
        sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]:
        sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # Filtering Logic
    filtered_df = display_df.copy()
    if sel_sys != "All": filtered_df = filtered_df[filtered_df['SYSTEM'] == sel_sys]
    if sel_area != "All": filtered_df = filtered_df[filtered_df['Area'] == sel_area]
    if sel_stat != "All": filtered_df = filtered_df[filtered_df['Status'] == sel_stat]
    if st.session_state[filter_key] != "LATEST": filtered_df = filtered_df[filtered_df['Rev'] == st.session_state[filter_key]]
    if search_term:
        filtered_df = filtered_df[filtered_df['DWG. NO.'].str.contains(search_term, case=False, na=False) | 
                                  filtered_df['Description'].str.contains(search_term, case=False, na=False)]

    # --- 3. Action Toolbar ---
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    with t_cols[0]:
        st.markdown(f"<span style='font-size:13px; font-weight:700;'>Total: {len(filtered_df):,} records</span>", unsafe_allow_html=True)
    
    with t_cols[2]: 
        if st.button("📁 Upload", key=f"btn_up_{tab_name}", use_container_width=True):
            show_upload_dialog()

    with t_cols[3]: st.button("📄 PDF", key=f"pdf_{tab_name}", use_container_width=True)
    with t_cols[4]:
        export_out = BytesIO()
        with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    with t_cols[5]: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # --- 4. Data Viewport ---
    st.dataframe(
        filtered_df, use_container_width=True, hide_index=True, height=550,
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

@st.dialog("Upload Master File")
def show_upload_dialog():
    """Restores the upload interface as a dialog."""
    st.write("Please upload a new Drawing Master file.")
    uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'])
    
    if uploaded_file:
        st.info("File ready. Click 'Apply & Save' to finalize.")
        if st.button("Apply & Save", type="primary", use_container_width=True):
            try:
                df_upload = pd.read_excel(uploaded_file, sheet_name='DRAWING LIST')
                df_upload.to_excel(DB_PATH, sheet_name='DRAWING LIST', index=False)
                st.success("Database synchronized successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database missing. Please contact administrator.")
        return

    # Data Loading
    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
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
    with tabs[4]: render_drawing_table(master_df[master_df['Category'].str.contains('Specialty|Speciality', case=False, na=False)], "Specialty")

if __name__ == "__main__":
    show_doc_control()
