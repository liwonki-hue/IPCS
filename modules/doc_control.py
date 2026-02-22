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
    for r, d, m in [('3rd REV', '3rd DATE', '3rd REMARK'), ('2nd REV', '2nd DATE', '2nd REMARK'), ('1st REV', '1st DATE', '1st REMARK')]:
        if pd.notna(row.get(r)) and str(row.get(r)).strip() != "":
            return row[r], row.get(d, '-'), row.get(m, '-')
    return '-', '-', '-'

def apply_html_style():
    """HTML 소스의 색상 및 간격을 그대로 반영"""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .block-container { padding: 1.5rem 2rem !important; background-color: #f7f9fc; }
        
        /* 제목 스타일 고정 */
        .main-title { font-size: 22px; font-weight: 700; color: #0d1826; margin-bottom: 20px; }
        
        /* 섹션 헤더 스타일 */
        .section-label { font-size: 13px; font-weight: 600; color: #6b7a90; margin-bottom: 8px; }

        /* Revision 버튼 스타일 (HTML Green 반영) */
        div.stButton > button {
            border-radius: 4px; border: 1px solid #dde3ec;
            background-color: white; color: #374559;
            height: 42px; font-size: 12px !important; line-height: 1.2;
            transition: all 0.2s ease;
        }
        /* 선택된(Active) 리비전 버튼: HTML과 동일한 녹색 */
        div.stButton > button[kind="primary"] {
            background-color: #0c7a3d !important; color: white !important; border: none !important;
        }

        /* 툴바 버튼 (Action Buttons) */
        .action-row .stButton > button {
            height: 30px !important; font-size: 11px !important; background-color: #ffffff;
            border: 1px solid #c4cdd8; color: #374559; padding: 0 10px;
        }
        
        /* 결과 요약 텍스트 */
        .result-info { font-size: 13px; color: #6b7a90; padding-top: 8px; }
        
        /* 하단 네비게이션 */
        .nav-btn .stButton > button { height: 28px !important; padding: 0 5px !important; }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_html_style()
    
    # 1. Page Title
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("drawing_master.xlsx file is missing in data folder.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')

    # Data Processing
    processed = []
    for _, row in df.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        processed.append({
            "Category": row.get('Category', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'),
            "Latest Revision": l_rev, "Issue Date": l_date,
            "Hold": row.get('HOLD Y/N', 'N'), "Status": row.get('Status', '-'),
            "Remark": l_rem, "AREA": row.get('AREA', '-'), "SYSTEM": row.get('SYSTEM', '-')
        })
    full_df = pd.DataFrame(processed)

    # --- [SECTION 1] Revision Filter ---
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_counts = full_df['Latest Revision'].value_counts()
    unique_revs = sorted([r for r in full_df['Latest Revision'].unique() if pd.notna(r) and r != ""])
    target_revs = ["LATEST"] + unique_revs
    
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    # 컴팩트한 가로 배치 (HTML 스타일)
    rev_cols = st.columns(len(target_revs) + (8 - len(target_revs))) # 남은 공간 확보
    for i, rev in enumerate(target_revs):
        count = len(full_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        if rev_cols[i].button(f"{rev}\n{count}", key=f"rev_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # --- [SECTION 2] Search & Filter ---
    st.markdown("<div style='margin-top:20px;' class='section-label'>Search & Filter</div>", unsafe_allow_html=True)
    
    f_df = full_df.copy()
    if st.session_state.sel_rev != "LATEST":
        f_df = f_df[f_df['Latest Revision'] == st.session_state.sel_rev]

    # HTML 요구사항: Search(Long) -> AREA -> SYSTEM -> STATUS
    with st.container():
        s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
        with s1: search_no = st.text_input("Search", placeholder="Search by DWG. NO. or Description...", label_visibility="collapsed")
        with s2: sel_area = st.multiselect("All AREA", options=sorted(f_df['AREA'].unique()), label_visibility="collapsed")
        with s3: sel_system = st.multiselect("All SYSTEM", options=sorted(f_df['SYSTEM'].unique()), label_visibility="collapsed")
        with s4: sel_status = st.multiselect("All STATUS", options=sorted(f_df['Status'].unique()), label_visibility="collapsed")

    # Filter Logic
    if sel_area: f_df = f_df[f_df['AREA'].isin(sel_area)]
    if sel_system: f_df = f_df[f_df['SYSTEM'].isin(sel_system)]
    if sel_status: f_df = f_df[f_df['Status'].isin(sel_status)]
    if search_no: 
        f_df = f_df[f_df['DWG. NO.'].str.contains(search_no, case=False, na=False) | 
                    f_df['Description'].str.contains(search_no, case=False, na=False)]

    # --- [SECTION 3] Results Info & Action Toolbar ---
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    res_col, act_col = st.columns([5, 5])
    
    with res_col:
        st.markdown(f"<div class='result-info'>Results: <b>{len(f_df):,}</b> drawings · Latest status · sorted by DWG. NO.</div>", unsafe_allow_html=True)
    
    with act_col:
        st.markdown("<div class='action-row'>", unsafe_allow_html=True)
        a1, a2, a3, a4, a5 = st.columns([1, 1, 1, 1, 1])
        with a1: st.button("📁 Upload", key="up")
        with a2: st.button("📄 PDF Reg", key="pdf")
        with a3:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as wr: f_df.to_excel(wr, index=False)
            st.download_button("📤 Export", data=out.getvalue(), file_name="Dwg_Export.xlsx")
        with a4: st.button("🖨️ Print", key="prt")
        with a5: 
            if st.button("🔄 Refresh"): st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- [SECTION 4] Data Table (Compact Height) ---
    st.dataframe(
        f_df[["Category", "DWG. NO.", "Description", "Latest Revision", "Issue Date", "Hold", "Status", "Remark"]],
        use_container_width=True, hide_index=True, height=500
    )

    # --- [SECTION 5] HTML Style Pagination ---
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    rows_per_page = 50
    total_pages = max((len(f_df) // rows_per_page) + (1 if len(f_df) % rows_per_page > 0 else 0), 1)
    if 'curr_pg' not in st.session_state: st.session_state.curr_pg = 1

    p_left, p_mid, p_right = st.columns([3, 4, 3])
    with p_left: st.markdown(f"<p class='result-info'>Showing {((st.session_state.curr_pg-1)*rows_per_page)+1} to {min(st.session_state.curr_pg*rows_per_page, len(f_df))}</p>", unsafe_allow_html=True)
    with p_mid:
        st.markdown("<div class='nav-btn'>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns([1, 2, 1])
        if m1.button("◀ Prev") and st.session_state.curr_pg > 1:
            st.session_state.curr_pg -= 1
            st.rerun()
        m2.markdown(f"<p style='text-align:center; font-size:13px; font-weight:700; padding-top:5px;'>{st.session_state.curr_pg} / {total_pages}</p>", unsafe_allow_html=True)
        if m3.button("Next ▶") and st.session_state.curr_pg < total_pages:
            st.session_state.curr_pg += 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
