import streamlit as st
import pandas as pd
import os
import base64
from io import BytesIO

# File Path Settings
DB_PATH = 'data/drawing_master.xlsx'
PDF_PATH = 'data/drawings/'

def get_latest_rev_info(row):
    """
    Extracts the most recent revision, date, and remark.
    Checks in order: 3rd -> 2nd -> 1st.
    """
    if pd.notna(row.get('3rd REV')) and str(row.get('3rd REV')).strip() != "":
        return row['3rd REV'], row.get('3rd DATE', '-'), row.get('3rd REMARK', '-')
    elif pd.notna(row.get('2nd REV')) and str(row.get('2nd REV')).strip() != "":
        return row['2nd REV'], row.get('2nd DATE', '-'), row.get('2nd REMARK', '-')
    else:
        return row.get('1st REV', '-'), row.get('1st DATE', '-'), row.get('1st REMARK', '-')

def show_doc_control():
    # 1. Page Header
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

    # 2. Filters (4 Columns)
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        sel_area = st.multiselect("Area", options=sorted(df['AREA'].unique() if 'AREA' in df.columns else []))
    with f2:
        sel_system = st.multiselect("System", options=sorted(df['SYSTEM'].unique() if 'SYSTEM' in df.columns else []))
    with f3:
        sel_bore = st.multiselect("Bore Size", options=sorted(df['BORE'].unique() if 'BORE' in df.columns else []))
    with f4:
        search_no = st.text_input("DWG. NO. Search")

    # Apply Filtering
    f_df = df.copy()
    if sel_area: f_df = f_df[f_df['AREA'].isin(sel_area)]
    if sel_system: f_df = f_df[f_df['SYSTEM'].isin(sel_system)]
    if sel_bore: f_df = f_df[f_df['BORE'].isin(sel_bore)]
    if search_no: f_df = f_df[f_df['DWG. NO.'].str.contains(search_no, case=False, na=False)]

    # 3. Data Re-structuring
    data_list = []
    for _, row in f_df.iterrows():
        l_rev, l_date, l_remark = get_latest_rev_info(row)
        data_list.append({
            "Category": row.get('Category', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'),
            "Latest Revision": l_rev,
            "Issue Date": l_date,
            "Hold Y/N": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'),
            "Latest Remark": l_remark,
            "Description": row.get('DRAWING TITLE', '-')
        })
    
    res_df = pd.DataFrame(data_list)

    # 4. Export & Print Section
    st.subheader("📊 Drawing Master Status")
    e1, e2 = st.columns([8, 2])
    with e2:
        # Excel Export Logic
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            res_df.to_excel(writer, index=False, sheet_name='Drawing_Status')
        processed_data = output.getvalue()
        st.download_button(
            label="📥 Export to Excel",
            data=processed_data,
            file_name=f"Drawing_Status_{sel_area}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # 5. Pagination (50 rows per page)
    rows_per_page = 50
    total_pages = (len(res_df) // rows_per_page) + (1 if len(res_df) % rows_per_page > 0 else 0)
    
    if total_pages > 0:
        p1, p2 = st.columns([2, 8])
        with p1:
            current_page = st.number_input(f"Page (1-{total_pages})", min_value=1, max_value=total_pages, value=1)
        
        start_idx = (current_page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page
        page_df = res_df.iloc[start_idx:end_idx]

        # 6. Center Alignment Styling & Display
        # Column order: Category, DWG. NO., Latest Revision, Issue Date, Hold Y/N, Status, Latest Remark
        display_cols = ["Category", "DWG. NO.", "Latest Revision", "Issue Date", "Hold Y/N", "Status", "Latest Remark"]
        
        st.dataframe(
            page_df[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Category": st.column_config.Column(width="small"),
                "Hold Y/N": st.column_config.Column(width="small"),
            }
        )
        st.caption(f"Showing {start_idx+1} to {min(end_idx, len(res_df))} of {len(res_df)} drawings")
    else:
        st.warning("No data found matching the filters.")

    # 7. PDF Viewer (Optional selectbox)
    st.write("---")
    view_dwg = st.selectbox("Select Drawing for PDF Viewer", res_df['DWG. NO.'].unique(), index=None)
    if view_dwg:
        target = res_df[res_df['DWG. NO.'] == view_dwg].iloc[0]
        pdf_file = f"{view_dwg}_{target['Latest Revision']}.pdf"
        p_path = os.path.join(PDF_PATH, pdf_file)
        if os.path.exists(p_path):
            with open(p_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="1000"></iframe>', unsafe_allow_html=True)
        else:
            st.error(f"File not found: {pdf_file}")
