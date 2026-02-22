import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Configuration
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    for r, d, m in [('3rd REV', '3rd DATE', '3rd REMARK'), 
                    ('2nd REV', '2nd DATE', '2nd REMARK'), 
                    ('1st REV', '1st DATE', '1st REMARK')]:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            rem = row.get(m, "")
            rem = "" if pd.isna(rem) or str(rem).lower() == "none" else str(rem)
            return val, row.get(d, '-'), rem
    return '-', '-', ''

def apply_compact_ui():
    """상단 타이틀 고정 및 버튼 컴팩트 레이아웃 적용"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding: 3rem 2rem 1rem 2rem !important; }

        /* Title: Sticky Header */
        .header-container {
            position: fixed; top: 0; left: 0; right: 0;
            background: white; z-index: 1000;
            padding: 10px 2rem; border-bottom: 2px solid #f0f2f6;
        }
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; margin: 0; }
        
        /* Section Labels */
        .section-label { font-size: 10px !important; font-weight: 700; color: #6b7a90; margin-bottom: 5px; }

        /* Buttons: Compact Style */
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 4px; border: 1px solid #dde3ec;
            height: 28px !important; font-size: 10px !important; font-weight: 600 !important;
            padding: 0 5px !important; white-space: nowrap !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }

        /* Table Font (18px) */
        div[data-testid="stDataFrame"] [role="gridcell"] div { font-size: 18px !important; }
        div[data-testid="stDataFrame"] [role="columnheader"] p { font-size: 18px !important; font-weight: 800 !important; }
        </style>
        <div class="header-container"><div class="main-title">Drawing Control System</div></div>
    """, unsafe_allow_html=True)

@st.dialog("Upload Master Database")
def open_upload_dialog():
    st.info("Select the latest Excel file (.xlsx) to update the database.")
    new_file = st.file_uploader("Drag and drop file here", type=['xlsx'], key="modal_uploader_v4")
    if new_file:
        with open(DB_PATH, "wb") as f:
            f.write(new_file.getbuffer())
        st.success("Database Updated Successfully!")
        if st.button("Apply & Close"):
            st.rerun()

def show_doc_control():
    apply_compact_ui()

    if not os.path.exists(DB_PATH):
        st.error("Database file not found.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    
    # 1. Validation (Warning positioned below Title)
    dup_nos = df[df.duplicated(subset=['DWG. NO.'], keep=False)]['DWG. NO.'].unique()
    if len(dup_nos) > 0:
        st.warning(f"⚠️ Duplicate Drawing No. Detected: {', '.join(map(str, dup_nos))}")

    # 2. Data Preparation
    p_data = []
    for _, row in df.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'), "Rev": l_rev, "Date": l_date,
            "Hold": row.get('HOLD Y/N', 'N'), "Status": row.get('Status', '-'),
            "Remark": l_rem, "AREA": row.get('AREA', '-'), "SYSTEM": row.get('SYSTEM', '-')
        })
    f_df = pd.DataFrame(p_data)

    # 3. Revision Filter (Limited to Left 50%)
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    rev_area, _ = st.columns([1, 1])
    with rev_area:
        rev_cols = st.columns(len(target_revs[:7]))
        for i, rev in enumerate(target_revs[:7]):
            count = len(f_df) if rev == "LATEST" else f_df['Rev'].value_counts().get(rev, 0)
            if rev_cols[i].button(f"{rev}({count})", key=f"r_{rev}", 
                                  type="primary" if st.session_state.sel_rev == rev else "secondary", 
                                  use_container_width=True):
                st.session_state.sel_rev = rev
                st.rerun()

    # 4. Search & Filter
    st.markdown("<div class='section-label' style='margin-top:10px;'>SEARCH & FILTER</div>", unsafe_allow_html=True)
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
    with s1: search_q = st.text_input("S", placeholder="🔍 Search Drawing...", label_visibility="collapsed")
    with s2: a_sel = st.multiselect("A", options=sorted(work_df['AREA'].unique()), placeholder="Area", label_visibility="collapsed")
    with s3: y_sel = st.multiselect("Y", options=sorted(work_df['SYSTEM'].unique()), placeholder="System", label_visibility="collapsed")
    with s4: t_sel = st.multiselect("T", options=sorted(work_df['Status'].unique()), placeholder="Status", label_visibility="collapsed")

    if search_q: work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | work_df['Description'].str.contains(search_q, case=False, na=False)]
    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]

    # 5. Action Toolbar (Buttons restricted to 1/3 width)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    res_col, btn_area = st.columns([2, 1]) # [2:1] 비율로 버튼 영역을 1/3로 제한
    
    with res_col:
        st.markdown(f"<div style='font-size:13px; font-weight:600; padding-top:5px;'>Total: {len(work_df):,} items</div>", unsafe_allow_html=True)
    
    with btn_area:
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("📁 Upload Excel", use_container_width=True): open_upload_dialog()
        with b2:
            st.button("📄 PDF", use_container_width=True)
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                work_df.to_excel(writer, index=False)
            st.download_button("📤 Export Excel", data=export_out.getvalue(), file_name="Dwg_Master.xlsx", use_container_width=True)
        with b4:
            st.button("🖨️ Print", use_container_width=True)

    # 6. Main Data Table
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, hide_index=True, height=750
    )
