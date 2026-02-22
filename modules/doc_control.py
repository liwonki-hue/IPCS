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
    """최신 리비전 추출 및 None 공란 처리"""
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
    """HTML 원본보다 더 컴팩트한 Micro-UI 스타일 적용"""
    st.markdown("""
        <style>
        /* 1. Force Light Mode & Base Font */
        :root { color-scheme: light only !important; }
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f7f9fc !important;
            color: #0d1826 !important;
            font-size: 11px !important;
        }
        
        /* 2. Remove Extra Spaces */
        .block-container { padding: 0.8rem 2rem !important; }
        [data-testid="stHeader"] { display: none !important; }
        div[data-testid="stVerticalBlock"] > div { gap: 0.2rem !important; }

        /* 3. Title (Professional) */
        .main-title { 
            font-size: 24px !important; font-weight: 800; color: #1657d0; 
            margin-bottom: 12px; letter-spacing: -0.8px; 
        }

        /* 4. Section Labels (Ultra Small) */
        .section-label { 
            font-size: 10px !important; font-weight: 700; color: #6b7a90; 
            text-transform: uppercase; margin-bottom: 2px; margin-top: 8px;
        }

        /* 5. Revision Buttons (2단계 더 작게 - Micro Size) */
        div.stButton > button {
            border-radius: 3px; border: 1px solid #dde3ec;
            background-color: white; color: #374559;
            height: 28px !important; font-size: 10px !important; padding: 0 4px !important;
            line-height: 1.1;
        }
        /* Active State (Green) */
        div.stButton > button[kind="primary"] {
            background-color: #0c7a3d !important; color: white !important; border: none !important;
        }

        /* 6. Toolbar Buttons (Right Aligned & Icon Style) */
        .action-toolbar .stButton > button {
            height: 26px !important; font-size: 10px !important; font-weight: 600 !important;
            border: 1px solid #c4cdd8 !important; background-color: #ffffff !important;
            display: flex; align-items: center; justify-content: center;
        }
        
        /* 7. Inputs & Selectors (2단계 축소) */
        div[data-baseweb="select"], div[data-baseweb="base-input"], input {
            min-height: 26px !important; height: 26px !important; font-size: 11px !important;
        }
        .stMultiSelect span { font-size: 10px !important; padding: 0 2px !important; }
        
        /* 8. Table Style */
        .stDataFrame { border: 1px solid #dde3ec !important; }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_ultra_compact_ui()
    
    # [Title]
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

    # [SECTION 1] Revision Filter (Micro Layout)
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_counts = f_df['Rev'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    # 버튼 사이 간격을 최소화하기 위해 많은 컬럼 할당
    rev_cols = st.columns(15) 
    for i, rev in enumerate(target_revs[:15]):
        count = len(f_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        if rev_cols[i].button(f"{rev}\n{count}", key=f"r_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # [SECTION 2] Search & Filter (Micro Size)
    st.markdown("<div class='section-label'>Search & Filter</div>", unsafe_allow_html=True)
    
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    with st.container():
        # Search(Long) + All Area + All System + All Status
        s1, s2, s3, s4 = st.columns([5, 2, 2, 2])
        with s1: search_q = st.text_input("S", placeholder="🔍 Search DWG. NO. or Description...", label_visibility="collapsed")
        with s2: a_sel = st.multiselect("A", options=sorted(work_df['AREA'].unique()), placeholder="All AREA", label_visibility="collapsed")
        with s3: y_sel = st.multiselect("Y", options=sorted(work_df['SYSTEM'].unique()), placeholder="All SYSTEM", label_visibility="collapsed")
        with s4: t_sel = st.multiselect("T", options=sorted(work_df['Status'].unique()), placeholder="All STATUS", label_visibility="collapsed")

    # Filter Logic
    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]
    if search_q: work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | work_df['Description'].str.contains(search_q, case=False, na=False)]

    # [SECTION 3] Result Info & Icon Buttons (Right Aligned)
    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
    res_col, btn_col = st.columns([5, 5])
    
    with res_col:
        st.markdown(f"<div style='font-size:11px; color:#6b7a90; padding-top:8px;'>Results: <b>{len(work_df):,}</b> drawings · Latest status · sorted by DWG. NO.</div>", unsafe_allow_html=True)
    
    with btn_col:
        # 우측 정렬을 위한 툴바 컨테이너
        st.markdown("<div class='action-toolbar'>", unsafe_allow_html=True)
        b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
        with b1: st.button("📁 Upload Excel", key="up_ex", use_container_width=True)
        with b2: st.button("📄 Upload PDF", key="up_pdf", use_container_width=True)
        with b3:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as wr: work_df.to_excel(wr, index=False)
            st.download_button("📤 Export Excel", data=out.getvalue(), file_name="Dwg_Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Print List", key="prt_ls", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # [SECTION 4] Main Table (Remark fully optimized)
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, hide_index=True, height=550,
        column_config={
            "Remark": st.column_config.TextColumn("Remark", width="large"),
            "Description": st.column_config.TextColumn("Description", width="medium"),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Rev": st.column_config.TextColumn("Rev", width="small")
        }
    )

    # [SECTION 5] Micro Pagination
    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)
    rows_per_page = 50
    total_pages = max((len(work_df) // rows_per_page) + (1 if len(work_df) % rows_per_page > 0 else 0), 1)
    if 'curr_pg' not in st.session_state: st.session_state.curr_pg = 1

    n1, n2, n3 = st.columns([3, 4, 3])
    with n1: st.caption(f"Showing {((st.session_state.curr_pg-1)*rows_per_page)+1} to {min(st.session_state.curr_pg*rows_per_page, len(work_df))}")
    with n2:
        m1, m2, m3 = st.columns([1, 1, 1])
        if m1.button("◀ Prev", key="p_v") and st.session_state.curr_pg > 1:
            st.session_state.curr_pg -= 1
            st.rerun()
        m2.markdown(f"<p style='text-align:center; font-size:11px; font-weight:700; padding-top:4px;'>{st.session_state.curr_pg} / {total_pages}</p>", unsafe_allow_html=True)
        if m3.button("Next ▶", key="n_x") and st.session_state.curr_pg < total_pages:
            st.session_state.curr_pg += 1
            st.rerun()
