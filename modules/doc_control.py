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
    """최신 리비전 정보를 컴팩트하게 추출"""
    for rev_col, date_col, remark_col in [('3rd REV', '3rd DATE', '3rd REMARK'), 
                                          ('2nd REV', '2nd DATE', '2nd REMARK'), 
                                          ('1st REV', '1st DATE', '1st REMARK')]:
        val = row.get(rev_col)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(date_col, '-'), row.get(remark_col, '-')
    return '-', '-', '-'

def apply_enhanced_ui():
    """HTML의 세련된 느낌을 위한 Custom CSS"""
    st.markdown("""
        <style>
        /* 기본 여백 제거 및 배경색 조정 */
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        .stApp { background-color: #f7f9fc; }
        
        /* Revision Summary 버튼 스타일 (작고 세련되게) */
        div.stButton > button {
            border-radius: 4px;
            padding: 2px 10px;
            height: auto;
            min-height: 45px;
            font-size: 12px !important;
            border: 1px solid #dde3ec;
            background-color: #ffffff;
            line-height: 1.2;
        }
        
        /* 기능 버튼 스타일 (Toolbar 느낌) */
        .action-btn div.stButton > button {
            height: 32px !important;
            min-height: 32px !important;
            font-size: 13px !important;
            background-color: #f0f4f9;
        }

        /* 텍스트 스타일 */
        h2 { font-size: 1.5rem !important; font-weight: 700 !important; color: #0d1826; }
        .stMultiSelect, .stTextInput, .stSelectbox { font-size: 12px !important; }
        label { font-size: 12px !important; font-weight: 600 !important; color: #6b7a90 !important; }
        
        /* 페이지네이터 텍스트 */
        .nav-text { font-size: 13px; color: #374559; padding-top: 8px; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_enhanced_ui()
    
    # Header Section
    st.markdown("<h2>Drawing Control System</h2>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Master File is missing.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')

    # Data Processing (Cache-like logic)
    processed = []
    for _, row in df.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        processed.append({
            "Category": row.get('Category', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'),
            "Latest Revision": l_rev,
            "Issue Date": l_date,
            "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'),
            "Remark": l_rem,
            "AREA": row.get('AREA', '-'),
            "SYSTEM": row.get('SYSTEM', '-')
        })
    full_df = pd.DataFrame(processed)

    # --- [1] Revision Summary Section (Compact) ---
    rev_counts = full_df['Latest Revision'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in full_df['Latest Revision'].unique() if pd.notna(r) and r != ""])
    
    if 'sel_rev_btn' not in st.session_state: st.session_state.sel_rev_btn = "LATEST"
    
    # HTML처럼 콤팩트하게 한 줄 배치
    rev_cols = st.columns(len(target_revs))
    for i, rev in enumerate(target_revs):
        count = len(full_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev_btn == rev
        if rev_cols[i].button(f"**{rev}**\n{count}", key=f"btn_{rev}", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.sel_rev_btn = rev
            st.rerun()

    # --- [2] Search & Filter Section (Clean Row) ---
    st.markdown("<div style='margin-top: -10px;'></div>", unsafe_allow_html=True)
    f_df = full_df.copy()
    if st.session_state.sel_rev_btn != "LATEST":
        f_df = f_df[f_df['Latest Revision'] == st.session_state.sel_rev_btn]

    with st.container():
        c1, c2, c3, c4 = st.columns([1.5, 1.5, 1.5, 3])
        with c1: sel_area = st.multiselect("Area", options=sorted(f_df['AREA'].unique()))
        with c2: sel_system = st.multiselect("System", options=sorted(f_df['SYSTEM'].unique()))
        with c3: sel_status = st.multiselect("Status", options=sorted(f_df['Status'].unique()))
        with c4: search_no = st.text_input("Search DWG. NO.", placeholder="Drawing No...")

    if sel_area: f_df = f_df[f_df['AREA'].isin(sel_area)]
    if sel_system: f_df = f_df[f_df['SYSTEM'].isin(sel_system)]
    if sel_status: f_df = f_df[f_df['Status'].isin(sel_status)]
    if search_no: f_df = f_df[f_df['DWG. NO.'].str.contains(search_no, case=False, na=False)]

    # --- [3] Toolbar (Action Buttons) ---
    st.markdown("<div class='action-btn'>", unsafe_allow_html=True)
    t1, t2, t3, t4, t5, empty = st.columns([1, 1, 1, 1, 1, 4])
    with t1: st.button("📁 Upload", use_container_width=True)
    with t2: st.button("📄 PDF Reg", use_container_width=True)
    with t3:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            f_df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=output.getvalue(), file_name="Export.xlsx", use_container_width=True)
    with t4: st.button("🖨️ Print", use_container_width=True)
    with t5: 
        if st.button("🔄 Refresh", use_container_width=True): st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # --- [4] Drawing Master Table ---
    rows_per_page = 50
    total_pages = max((len(f_df) // rows_per_page) + (1 if len(f_df) % rows_per_page > 0 else 0), 1)
    if 'curr_pg' not in st.session_state: st.session_state.curr_pg = 1

    start_idx = (st.session_state.curr_pg - 1) * rows_per_page
    st.dataframe(
        f_df.iloc[start_idx : start_idx + rows_per_page][["Category", "DWG. NO.", "Description", "Latest Revision", "Issue Date", "Hold", "Status", "Remark"]],
        use_container_width=True, hide_index=True, height=550
    )

    # --- [5] Pagination (HTML Style Bottom) ---
    n1, n2, n3 = st.columns([3, 4, 3])
    with n1: st.markdown(f"<p class='nav-text' style='text-align:left;'>Total: <b>{len(f_df)}</b></p>", unsafe_allow_html=True)
    with n2:
        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])
        if p_col1.button("◀", key="prev") and st.session_state.curr_pg > 1:
            st.session_state.curr_pg -= 1
            st.rerun()
        p_col2.markdown(f"<p class='nav-text'>Page <b>{st.session_state.curr_pg}</b> / {total_pages}</p>", unsafe_allow_html=True)
        if p_col3.button("▶", key="next") and st.session_state.curr_pg < total_pages:
            st.session_state.curr_pg += 1
            st.rerun()
    with n3: st.markdown(f"<p class='nav-text' style='text-align:right;'>Showing {start_idx+1}-{min(start_idx+rows_per_page, len(f_df))}</p>", unsafe_allow_html=True)

    # --- [6] Quick Viewer ---
    st.write("---")
    view_dwg = st.selectbox("Quick PDF View", f_df['DWG. NO.'].unique(), index=None, placeholder="Select a drawing...")
    if view_dwg:
        target = f_df[f_df['DWG. NO.'] == view_dwg].iloc[0]
        pdf_file = f"{view_dwg}_{target['Latest Revision']}.pdf"
        p_path = os.path.join(PDF_PATH, pdf_file)
        if os.path.exists(p_path):
            with open(p_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="800"></iframe>', unsafe_allow_html=True)
