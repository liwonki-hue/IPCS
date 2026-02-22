import streamlit as st
import pandas as pd
import os
import base64

# File Path Settings
DB_PATH = 'data/drawing_master.xlsx'
PDF_PATH = 'data/drawings/'

def get_latest_rev_info(row):
    """
    Extracts the most recent revision and date.
    Logic: Checks 3rd -> 2nd -> 1st Rev columns.
    """
    if pd.notna(row.get('3rd REV')) and str(row.get('3rd REV')).strip() != "":
        return row['3rd REV'], row.get('3rd DATE', '-')
    elif pd.notna(row.get('2nd REV')) and str(row.get('2nd REV')).strip() != "":
        return row['2nd REV'], row.get('2nd DATE', '-')
    else:
        return row.get('1st REV', '-'), row.get('1st DATE', '-')

def show_doc_control():
    # 1. Main Title (Updated as requested)
    st.markdown("<h1 style='text-align: center;'>Drawing Control System</h1>", unsafe_allow_html=True)
    st.write("---")

    # 2. Load Excel Data
    if not os.path.exists(DB_PATH):
        st.error(f"⚠️ Master File not found: {DB_PATH}")
        return

    try:
        # Load the specific sheet 'DRAWING LIST'
        df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return

    # 3. Filtering Section (Full Width Layout)
    st.subheader("🔍 Filtering & Search")
    f1, f2, f3, f4 = st.columns(4)
    
    with f1:
        areas = sorted(df['AREA'].unique()) if 'AREA' in df.columns else []
        sel_area = st.multiselect("Area", options=areas)
    with f2:
        systems = sorted(df['SYSTEM'].unique()) if 'SYSTEM' in df.columns else []
        sel_system = st.multiselect("System", options=systems)
    with f3:
        bores = sorted(df['BORE'].unique()) if 'BORE' in df.columns else []
        sel_bore = st.multiselect("Bore Size", options=bores)
    with f4:
        search_no = st.text_input("DWG. NO. Search")

    # Applying Filters
    filtered_df = df.copy()
    if sel_area: filtered_df = filtered_df[filtered_df['AREA'].isin(sel_area)]
    if sel_system: filtered_df = filtered_df[filtered_df['SYSTEM'].isin(sel_system)]
    if sel_bore: filtered_df = filtered_df[filtered_df['BORE'].isin(sel_bore)]
    if search_no: filtered_df = filtered_df[filtered_df['DWG. NO.'].str.contains(search_no, case=False, na=False)]

    # 4. Data Processing (Keeping only requested columns)
    display_list = []
    for _, row in filtered_df.iterrows():
        latest_rev, issue_date = get_latest_rev_info(row)
        display_list.append({
            "DWG. NO.": row.get('DWG. NO.'),
            "Latest Revision": latest_rev,
            "Issue Date": issue_date,
            "Hold Y/N": row.get('HOLD Y/N'),
            "Status": row.get('Status'),
            "Category": row.get('Category'),
            "Description": row.get('DRAWING TITLE')
        })
    
    final_display_df = pd.DataFrame(display_list)

    # 5. Dashboard View
    st.write(f"**Search Result:** {len(final_display_df)} drawings")
    
    # Selecting a Drawing for PDF Viewer
    selected_dwg = st.selectbox("Select a Drawing to Open PDF Viewer", 
                                 final_display_df['DWG. NO.'], 
                                 index=None, 
                                 placeholder="Choose a Drawing Number...")

    if selected_dwg:
        doc_info = final_display_df[final_display_df['DWG. NO.'] == selected_dwg].iloc[0]
        
        # Summary Header (Information Bar)
        st.info(f"📄 **Viewing:** {selected_dwg} | **Rev:** {doc_info['Latest Revision']} | **Status:** {doc_info['Status']} | **Hold:** {doc_info['Hold Y/N']}")

        # PDF Viewer
        pdf_filename = f"{selected_dwg}_{doc_info['Latest Revision']}.pdf"
        full_pdf_path = os.path.join(PDF_PATH, pdf_filename)
        
        if os.path.exists(full_pdf_path):
            with open(full_pdf_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="1000" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ PDF File Not Found: {pdf_filename}")

    # 6. Master Table (Requested Columns Only, Wide View)
    st.markdown("### Drawing Master Status")
    st.dataframe(
        final_display_df[["DWG. NO.", "Latest Revision", "Issue Date", "Hold Y/N", "Status", "Category"]], 
        use_container_width=True, 
        hide_index=True
    )
