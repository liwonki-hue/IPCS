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
    """3rd -> 2nd -> 1st 순서로 최신 리비전 정보 추출"""
    if pd.notna(row.get('3rd REV')) and str(row.get('3rd REV')).strip() != "":
        return row['3rd REV'], row.get('3rd DATE', '-'), row.get('3rd REMARK', '-')
    elif pd.notna(row.get('2nd REV')) and str(row.get('2nd REV')).strip() != "":
        return row['2nd REV'], row.get('2nd DATE', '-'), row.get('2nd REMARK', '-')
    else:
        return row.get('1st REV', '-'), row.get('1st DATE', '-'), row.get('1st REMARK', '-')

def show_doc_control():
    st.markdown("<h1 style='text-align: center; color: #1657d0;'>Drawing Control System</h1>", unsafe_allow_html=True)
    st.write("---")

    if not os.path.exists(DB_PATH):
        st.error("⚠️ Master File not found. Please upload 'drawing_master.xlsx' to data folder.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')

    # Data Pre-processing
    processed_data = []
    for _, row in df.iterrows():
        l_rev, l_date, l_remark = get_latest_rev_info(row)
        processed_data.append({
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
    full_df = pd.DataFrame(processed_data)

    # --- SECTION 1: Revision Summary Cards ---
    st.markdown("### Revision Summary")
    rev_counts = full_df['Latest Revision'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in full_df['Latest Revision'].unique() if pd.notna(r) and r != ""])
    
    if 'sel_rev_btn' not in st.session_state: st.session_state.sel_rev_btn = "LATEST"
    
    rev_cols = st.columns(len(target_revs))
    for i, rev in enumerate(target_revs):
        count = len(full_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        if rev_cols[i].button(f"{rev}\n{count}", use_container_width=True, type="primary" if st.session_state.sel_rev_btn == rev else "secondary"):
            st.session_state.sel_rev_btn = rev

    # --- SECTION 2: Search & Filter (Area / System / Status) ---
    st.write("---")
    with st.container():
        c1, c2, c3, c4 = st.columns([2, 2, 2, 4])
        with c1: sel_area = st.multiselect("Area", options=sorted(full_df['AREA'].unique()))
        with c2: sel_system = st.multiselect("System", options=sorted(full_df['SYSTEM'].unique()))
        with c3: sel_status = st.multiselect("Status", options=sorted(full_df['Status'].unique()))
        with c4: search_no = st.text_input("Search DWG. NO.", placeholder="Enter Drawing Number...")

    # Filter Application
    f_df = full_df.copy()
    if st.session_state.sel_rev_btn != "LATEST": f_df = f_df[f_df['Latest Revision'] == st.session_state.sel_rev_btn]
    if sel_area: f_df = f_df[f_df['AREA'].isin(sel_area)]
    if sel_system: f_df = f_df[f_df['SYSTEM'].isin(sel_system)]
    if sel_status: f_df = f_df[f_df['Status'].isin(sel_status)]
    if search_no: f_df = f_df[f_df['DWG. NO.'].str.contains(search_no, case=False, na=False)]

    # --- SECTION 3: Function Buttons (Upload / Export / Print) ---
    st.write("")
    b1, b2, b3, b4, b5 = st.columns([2, 2, 2, 2, 2])
    with b1:
        if st.button("📁 Upload Excel", use_container_width=True): st.info("Excel Upload Triggered")
    with b2:
        if st.button("📄 PDF Registration", use_container_width=True): st.info("PDF Registration Triggered")
    with b3:
        # Excel Export
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            f_df.to_excel(writer, index=False, sheet_name='Drawing_Status')
        st.download_button("📤 Export Excel", data=output.getvalue(), file_name=f"Dwg_Status_{datetime.now().strftime('%y%m%d')}.xlsx", use_container_width=True)
    with b4:
        st.button("🖨️ Print List", use_container_width=True)
    with b5:
        if st.button("🔄 Refresh Data", use_container_width=True): st.rerun()

    # --- SECTION 4: Drawing Master Status Table (Full Width) ---
    st.markdown(f"#### Drawing Master Status (Filter: {st.session_state.sel_rev_btn})")
    
    rows_per_page = 50
    total_pages = max((len(f_df) // rows_per_page) + (1 if len(f_df) % rows_per_page > 0 else 0), 1)
    
    # Page Display
    start_idx = (st.session_state.get('current_page', 1) - 1) * rows_per_page
    page_df = f_df.iloc[start_idx : start_idx + rows_per_page]

    st.dataframe(
        page_df[["Category", "DWG. NO.", "Description", "Latest Revision", "Issue Date", "Hold Y/N", "Status", "Latest Remark"]],
        use_container_width=True, hide_index=True
    )

    # --- SECTION 5: Bottom Navigation (Pagination) ---
    n1, n2, n3 = st.columns([3, 4, 3])
    with n1: st.write(f"Total: {len(f_df)} Records")
    with n2:
        if 'current_page' not in st.session_state: st.session_state.current_page = 1
        st.session_state.current_page = st.number_input(f"Page (Max {total_pages})", min_value=1, max_value=total_pages, value=st.session_state.current_page)
    with n3:
        st.write(f"Showing {start_idx+1} to {min(start_idx+rows_per_page, len(f_df))}")

    # --- SECTION 6: PDF Viewer Selector ---
    st.write("---")
    view_dwg = st.selectbox("Quick View PDF", f_df['DWG. NO.'].unique(), index=None, placeholder="Select DWG NO to view PDF...")
    if view_dwg:
        target = f_df[f_df['DWG. NO.'] == view_dwg].iloc[0]
        pdf_file = f"{view_dwg}_{target['Latest Revision']}.pdf"
        p_path = os.path.join(PDF_PATH, pdf_file)
        if os.path.exists(p_path):
            with open(p_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800"></iframe>', unsafe_allow_html=True)
        else:
            st.warning(f"File not found: {pdf_file}")
