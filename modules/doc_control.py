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
    if pd.notna(row.get('3rd REV')) and str(row.get('3rd REV')).strip() != "":
        return row['3rd REV'], row.get('3rd DATE', '-'), row.get('3rd REMARK', '-')
    elif pd.notna(row.get('2nd REV')) and str(row.get('2nd REV')).strip() != "":
        return row['2nd REV'], row.get('2nd DATE', '-'), row.get('2nd REMARK', '-')
    else:
        return row.get('1st REV', '-'), row.get('1st DATE', '-'), row.get('1st REMARK', '-')

def apply_custom_css():
    st.markdown("""
        <style>
        /* Main Font & Background */
        .main { background-color: #f7f9fc; }
        
        /* Summary Card Style */
        .stButton button {
            border-radius: 8px;
            height: 60px;
            border: 1px solid #dde3ec;
            background-color: white;
            transition: all 0.3s;
        }
        .stButton button:hover {
            border-color: #1657d0;
            color: #1657d0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        /* Filter Section Styling */
        div[data-testid="stExpander"] { border: none; box-shadow: none; }
        .stMultiSelect label, .stTextInput label { font-size: 13px !important; color: #6b7a90; }
        
        /* Table Styling */
        .stDataFrame { border: 1px solid #dde3ec; border-radius: 10px; }
        
        /* Metric / Summary Text */
        .summary-box {
            text-align: center;
            padding: 10px;
            border-radius: 10px;
            background: white;
            border: 1px solid #dde3ec;
        }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_custom_css()
    
    # 1. Title Header
    st.markdown("<h2 style='text-align: left; color: #0d1826; font-weight: 700; margin-bottom: 20px;'>ISO Drawing Master List</h2>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("⚠️ Master File not found.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')

    # Data Processing
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

    # --- SECTION 1: Revision Summary (Compact Cards) ---
    rev_counts = full_df['Latest Revision'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in full_df['Latest Revision'].unique() if pd.notna(r) and r != ""])
    
    if 'sel_rev_btn' not in st.session_state: st.session_state.sel_rev_btn = "LATEST"
    
    # 가로로 콤팩트하게 배치 (최대 8개까지 한 줄 배치)
    rev_cols = st.columns(len(target_revs))
    for i, rev in enumerate(target_revs):
        count = len(full_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        btn_type = "primary" if st.session_state.sel_rev_btn == rev else "secondary"
        if rev_cols[i].button(f"**{rev}**\n{count}", key=f"rev_{rev}", use_container_width=True, type=btn_type):
            st.session_state.sel_rev_btn = rev
            st.rerun()

    # --- SECTION 2: Search & Filter (One Line Layout) ---
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    with st.container():
        f1, f2, f3, f4 = st.columns([1.5, 1.5, 1.5, 2.5])
        with f1: sel_area = st.multiselect("Area", options=sorted(full_df['AREA'].unique()))
        with f2: sel_system = st.multiselect("System", options=sorted(full_df['SYSTEM'].unique()))
        with f3: sel_status = st.multiselect("Status", options=sorted(full_df['Status'].unique()))
        with f4: search_no = st.text_input("DWG. NO.", placeholder="Search Drawing Number...")

    # Filter Application
    f_df = full_df.copy()
    if st.session_state.sel_rev_btn != "LATEST": f_df = f_df[f_df['Latest Revision'] == st.session_state.sel_rev_btn]
    if sel_area: f_df = f_df[f_df['AREA'].isin(sel_area)]
    if sel_system: f_df = f_df[f_df['SYSTEM'].isin(sel_system)]
    if sel_status: f_df = f_df[f_df['Status'].isin(sel_status)]
    if search_no: f_df = f_df[f_df['DWG. NO.'].str.contains(search_no, case=False, na=False)]

    # --- SECTION 3: Function Action Buttons (Styled as HTML) ---
    st.markdown("<div style='margin-top: 10px; margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    act1, act2, act3, act4, empty = st.columns([1.2, 1.2, 1.2, 1.2, 4])
    with act1:
        st.file_uploader("Upload Excel", type=['xlsx'], label_visibility="collapsed")
        st.button("📁 Upload", use_container_width=True)
    with act2:
        st.button("📄 PDF Reg.", use_container_width=True)
    with act3:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            f_df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=output.getvalue(), file_name="Dwg_Export.xlsx", use_container_width=True)
    with act4:
        st.button("🖨️ Print", use_container_width=True)

    # --- SECTION 4: Drawing Master Status Table ---
    rows_per_page = 50
    total_pages = max((len(f_df) // rows_per_page) + (1 if len(f_df) % rows_per_page > 0 else 0), 1)
    if 'current_page' not in st.session_state: st.session_state.current_page = 1

    start_idx = (st.session_state.current_page - 1) * rows_per_page
    page_df = f_df.iloc[start_idx : start_idx + rows_per_page]

    st.dataframe(
        page_df[["Category", "DWG. NO.", "Description", "Latest Revision", "Issue Date", "Hold Y/N", "Status", "Latest Remark"]],
        use_container_width=True, hide_index=True, height=600
    )

    # --- SECTION 5: HTML Style Bottom Navigator ---
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    n1, n2, n3 = st.columns([3, 4, 3])
    with n1:
        st.markdown(f"<p style='color: #6b7a90; font-size: 14px;'>Total <b>{len(f_df)}</b> records found</p>", unsafe_allow_html=True)
    with n2:
        # 콤팩트한 페이지네이터
        sub_n1, sub_n2, sub_n3 = st.columns([2, 1, 2])
        if sub_n1.button("PREV") and st.session_state.current_page > 1:
            st.session_state.current_page -= 1
            st.rerun()
        sub_n2.markdown(f"<p style='text-align:center; font-weight:bold; padding-top:10px;'>{st.session_state.current_page} / {total_pages}</p>", unsafe_allow_html=True)
        if sub_n3.button("NEXT") and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
            st.rerun()
    with n3:
        st.markdown(f"<p style='text-align: right; color: #6b7a90; font-size: 14px;'>Showing {start_idx+1}-{min(start_idx+rows_per_page, len(f_df))}</p>", unsafe_allow_html=True)

    # --- SECTION 6: Quick PDF Viewer (Bottom) ---
    st.write("---")
    view_col1, view_col2 = st.columns([3, 7])
    with view_col1:
        view_dwg = st.selectbox("Quick View PDF", f_df['DWG. NO.'].unique(), index=None)
    
    if view_dwg:
        target = f_df[f_df['DWG. NO.'] == view_dwg].iloc[0]
        pdf_file = f"{view_dwg}_{target['Latest Revision']}.pdf"
        p_path = os.path.join(PDF_PATH, pdf_file)
        if os.path.exists(p_path):
            with open(p_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800"></iframe>', unsafe_allow_html=True)
