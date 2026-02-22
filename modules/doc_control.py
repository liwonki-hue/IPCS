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
    """최신 리비전 추출 및 None/NaN 공란 처리"""
    for r, d, m in [('3rd REV', '3rd DATE', '3rd REMARK'), 
                    ('2nd REV', '2nd DATE', '2nd REMARK'), 
                    ('1st REV', '1st DATE', '1st REMARK')]:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            rem = row.get(m, "")
            rem = "" if pd.isna(rem) or str(rem).lower() == "none" else str(rem)
            return val, row.get(d, '-'), rem
    return '-', '-', ''

def apply_ultra_compact_ui():
    """강제 라이트 모드 및 Micro-UI 정밀 조정"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f7f9fc !important;
            color: #0d1826 !important;
            font-size: 11px !important;
        }
        .block-container { padding: 0.8rem 2rem !important; }
        [data-testid="stHeader"] { display: none !important; }
        
        /* 제목 스타일 */
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0; margin-bottom: 12px; }

        /* 섹션 레이블 */
        .section-label { font-size: 10px !important; font-weight: 700; color: #6b7a90; text-transform: uppercase; margin-bottom: 2px; }

        /* 버튼 Micro Size (2단계 축소) */
        div.stButton > button {
            border-radius: 3px; border: 1px solid #dde3ec;
            background-color: white; color: #374559;
            height: 26px !important; font-size: 10px !important; padding: 0 6px !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; border: none !important; }

        /* 입력창 Micro Size */
        div[data-baseweb="select"], div[data-baseweb="base-input"], input {
            min-height: 24px !important; height: 24px !important; font-size: 11px !important;
        }

        /* 툴바 정렬 */
        .action-toolbar .stButton > button { height: 24px !important; font-size: 10px !important; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_ultra_compact_ui()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Data file not found.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')

    # Data Sync
    p_data = []
    for _, row in df.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date,
            "Hold": row.get('HOLD Y/N', 'N'), "Status": row.get('Status', '-'),
            "Remark": l_rem, "AREA": row.get('AREA', '-'), "SYSTEM": row.get('SYSTEM', '-')
        })
    f_df = pd.DataFrame(p_data)

    # [1] Revision Filter
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_counts = f_df['Rev'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    rev_cols = st.columns(15) 
    for i, rev in enumerate(target_revs[:15]):
        count = len(f_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        if rev_cols[i].button(f"{rev}\n{count}", key=f"r_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # [2] Search & Filter
    st.markdown("<div class='section-label'>Search & Filter</div>", unsafe_allow_html=True)
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    with st.container():
        s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
        with s1: search_q = st.text_input("S", placeholder="🔍 Search...", label_visibility="collapsed")
        with s2: a_sel = st.multiselect("A", options=sorted(work_df['AREA'].unique()), placeholder="Area", label_visibility="collapsed")
        with s3: y_sel = st.multiselect("Y", options=sorted(work_df['SYSTEM'].unique()), placeholder="System", label_visibility="collapsed")
        with s4: t_sel = st.multiselect("T", options=sorted(work_df['Status'].unique()), placeholder="Status", label_visibility="collapsed")

    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]
    if search_q: work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | work_df['Description'].str.contains(search_q, case=False, na=False)]

    # [3] Action Toolbar
    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
    res_col, btn_col = st.columns([4, 6])
    with res_col:
        st.markdown(f"<div style='font-size:11px; color:#6b7a90; padding-top:8px;'>Results: <b>{len(work_df):,}</b> drawings</div>", unsafe_allow_html=True)
    with btn_col:
        st.markdown("<div class='action-toolbar'>", unsafe_allow_html=True)
        b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
        with b1: st.button("📁 Upload Excel", use_container_width=True)
        with b2: st.button("📄 Upload PDF", use_container_width=True)
        with b3:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as wr: work_df.to_excel(wr, index=False)
            st.download_button("📤 Export Excel", data=out.getvalue(), file_name="Dwg_Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Print List", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # [4] Data Table (Center Alignment & Width Optimization)
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, 
        hide_index=True, 
        height=600,
        column_config={
            "Category": st.column_config.TextColumn("Cat.", width="small", help="Category", validate=None),
            "DWG. NO.": st.column_config.TextColumn("Drawing No.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="max"), # 최대 너비로 설정
            "Rev": st.column_config.TextColumn("Rev", width="small"),
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Hold": st.column_config.TextColumn("H", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Remark": st.column_config.TextColumn("Remark", width="large")
        }
    )

    # [5] Pagination (Micro)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    rows_per_page = 50
    total_pages = max((len(work_df) // rows_per_page) + (1 if len(work_df) % rows_per_page > 0 else 0), 1)
    if 'curr_pg' not in st.session_state: st.session_state.curr_pg = 1
    n1, n2, n3 = st.columns([4, 2, 4])
    with n2:
        m1, m2, m3 = st.columns([1, 2, 1])
        if m1.button("◀", key="p_v") and st.session_state.curr_pg > 1:
            st.session_state.curr_pg -= 1
            st.rerun()
        m2.markdown(f"<p style='text-align:center; font-size:11px; font-weight:700; padding-top:4px;'>{st.session_state.curr_pg}/{total_pages}</p>", unsafe_allow_html=True)
        if m3.button("▶", key="n_x") and st.session_state.curr_pg < total_pages:
            st.session_state.curr_pg += 1
            st.rerun()
