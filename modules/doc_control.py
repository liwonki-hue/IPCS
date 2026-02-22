import streamlit as st
import pandas as pd
import os
import base64
from io import BytesIO
from datetime import datetime

# File Path Settings
DB_PATH = 'data/drawing_master.xlsx'
PDF_PATH = 'data/drawings/'

def get_latest_rev_info(row):
    """Checks 3rd -> 2nd -> 1st Rev columns for latest info."""
    if pd.notna(row.get('3rd REV')) and str(row.get('3rd REV')).strip() != "":
        return row['3rd REV'], row.get('3rd DATE', '-'), row.get('3rd REMARK', '-')
    elif pd.notna(row.get('2nd REV')) and str(row.get('2nd REV')).strip() != "":
        return row['2nd REV'], row.get('2nd DATE', '-'), row.get('2nd REMARK', '-')
    else:
        return row.get('1st REV', '-'), row.get('1st DATE', '-'), row.get('1st REMARK', '-')

def show_doc_control():
    # 1. Main Header
    st.markdown("<h1 style='text-align: center;'>Drawing Control System</h1>", unsafe_allow_html=True)
    st.write("---")

    if not os.path.exists(DB_PATH):
        st.error(f"⚠️ Master File not found: {DB_PATH}")
        return

    try:
        df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return

    # 2. Pre-processing for Revision Summary
    processed_list = []
    for _, row in df.iterrows():
        l_rev, l_date, l_remark = get_latest_rev_info(row)
        processed_list.append({
            "Category": row.get('Category', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'),
            "Latest Revision": l_rev,
            "Issue Date": l_date,
            "Hold Y/N": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'),
            "Latest Remark": l_remark,
            "AREA": row.get('AREA', '-'),
            "SYSTEM": row.get('SYSTEM', '-'),
            "BORE": row.get('BORE', '-')
        })
    full_df = pd.DataFrame(processed_list)

    # --- 3. Revision Summary Cards (Buttons) ---
    st.subheader("Revision Summary")
    rev_counts = full_df['Latest Revision'].value_counts()
    all_count = len(full_df)
    
    # Define target revisions for buttons (LATEST + Main Revisions)
    target_revs = ["LATEST"] + sorted([r for r in full_df['Latest Revision'].unique() if pd.notna(r) and r != ""])
    
    cols = st.columns(len(target_revs))
    
    # Session State for Revision Filtering
    if 'sel_rev_btn' not in st.session_state:
        st.session_state.sel_rev_btn = "LATEST"

    for i, rev_name in enumerate(target_revs):
        count = all_count if rev_name == "LATEST" else rev_counts.get(rev_name, 0)
        label = f"{rev_name}\n({count})"
        if cols[i].button(label, use_container_width=True, type="primary" if st.session_state.sel_rev_btn == rev_name else "secondary"):
            st.session_state.sel_rev_btn = rev_name

    # 4. Filters (Mid Section)
    st.write("---")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        sel_area = st.multiselect("Area", options=sorted(full_df['AREA'].unique()))
    with f2:
        sel_system = st.multiselect("System", options=sorted(full_df['SYSTEM'].unique()))
    with f3:
        sel_bore = st.multiselect("Bore Size", options=sorted(full_df['BORE'].unique()))
    with f4:
        search_no = st.text_input("DWG. NO. Search")

    # Apply Filtering Logic
    f_df = full_df.copy()
    # 1st: Filter by Revision Button
    if st.session_state.sel_rev_btn != "LATEST":
        f_df = f_df[f_df['Latest Revision'] == st.session_state.sel_rev_btn]
    
    # 2nd: Filter by Dropdowns
    if sel_area: f_df = f_df[f_df['AREA'].isin(sel_area)]
    if sel_system: f_df = f_df[f_df['SYSTEM'].isin(sel_system)]
    if sel_bore: f_df = f_df[f_df['BORE'].isin(sel_bore)]
    if search_no: f_df = f_df[f_df['DWG. NO.'].str.contains(search_no, case=False, na=False)]

    # 5. Drawing Master Status Table
    st.markdown(f"### Drawing Master Status - Filtered by [{st.session_state.sel_rev_btn}]")
    
    # Display the Table
    rows_per_page = 50
    total_pages = max((len(f_df) // rows_per_page) + (1 if len(f_df) % rows_per_page > 0 else 0), 1)
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1

    start_idx = (st.session_state.current_page - 1) * rows_per_page
    page_df = f_df.iloc[start_idx : start_idx + rows_per_page]

    # Show Table (Wide Layout)
    st.dataframe(
        page_df[["Category", "DWG. NO.", "Description", "Latest Revision", "Issue Date", "Hold Y/N", "Status", "Latest Remark"]],
        use_container_width=True,
        hide_index=True
    )

    # 6. Bottom Navigation (Pagination & Export)
    b1, b2, b3 = st.columns([2, 5, 3])
    with b1:
        st.write(f"Showing {start_idx+1}-{min(start_idx + rows_per_page, len(f_df))} of {len(f_df)}")
    with b2:
        st.session_state.current_page = st.number_input(f"Page Selection (Total {total_pages})", min_value=1, max_value=total_pages, value=st.session_state.current_page)
    with b3:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            f_df.to_excel(writer, index=False, sheet_name='Drawing_Status')
        st.download_button(label="📥 Export to Excel", data=output.getvalue(), file_name=f"IPCS_Export_{datetime.now().strftime('%y%m%d')}.xlsx", use_container_width=True)

    # 7. PDF Viewer Selectbox (Bottom)
    st.write("---")
    view_dwg = st.selectbox("Select Drawing to Open PDF", f_df['DWG. NO.'].unique(), index=None)
    if view_dwg:
        target = f_df[f_df['DWG. NO.'] == view_dwg].iloc[0]
        pdf_file = f"{view_dwg}_{target['Latest Revision']}.pdf"
        p_path = os.path.join(PDF_PATH, pdf_file)
        if os.path.exists(p_path):
            with open(p_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800"></iframe>', unsafe_allow_html=True)
        else:
            st.error(f"PDF File Not Found: {pdf_file}")
