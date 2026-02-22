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

def apply_strict_html_theme():
    """라이트 테마 강제 및 모든 다크모드 요소 덮어쓰기 (CSS Injection)"""
    st.markdown("""
        <style>
        /* 1. Force Light Theme */
        :root { color-scheme: light only !important; }
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f7f9fc !important;
            color: #0d1826 !important;
        }
        
        /* 2. Remove Streamlit Default Overlays */
        [data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
        .block-container { padding: 1rem 2.5rem !important; max-width: 100% !important; }

        /* 3. Title Style */
        .main-title { 
            font-size: 28px !important; 
            font-weight: 800 !important; 
            color: #1657d0 !important; 
            margin-bottom: 20px !important;
            letter-spacing: -0.5px;
        }

        /* 4. Section Label (Compact) */
        .section-label { font-size: 11px; font-weight: 700; color: #6b7a90; text-transform: uppercase; margin-bottom: 4px; }

        /* 5. Revision Buttons (Micro Size) */
        div.stButton > button {
            border-radius: 4px; border: 1px solid #dde3ec;
            background-color: white; color: #374559;
            height: 34px !important; font-size: 11px !important; padding: 0 8px !important;
        }
        /* Active Revision (HTML Green) */
        div.stButton > button[kind="primary"] {
            background-color: #0c7a3d !important; color: white !important; border: none !important;
            box-shadow: 0 2px 4px rgba(12, 122, 61, 0.2);
        }

        /* 6. Toolbar Buttons (Right Aligned Icons) */
        .action-row div.stButton > button {
            height: 28px !important; font-size: 11px !important; font-weight: 600 !important;
            border: 1px solid #c4cdd8 !important; background-color: #ffffff !important;
            padding: 0 10px !important; color: #374559 !important;
        }
        .action-row div.stButton > button:hover { border-color: #1657d0 !important; color: #1657d0 !important; }

        /* 7. Filtering Input Compactness */
        div[data-baseweb="select"] { min-height: 32px !important; font-size: 12px !important; }
        input { height: 32px !important; font-size: 12px !important; }
        
        /* 8. Dataframe Header Styling */
        .stDataFrame { border: 1px solid #dde3ec !important; border-radius: 6px !important; }
        
        /* Pagination Navigator */
        .nav-btn .stButton > button { height: 26px !important; min-width: 60px !important; font-size: 10px !important; }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_strict_html_theme()
    
    # [1] Header
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Data file missing.")
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

    # [2] Revision Filter Section (Compact)
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_counts = f_df['Rev'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    # 콤팩트한 12컬럼 레이아웃 활용
    rev_cols = st.columns(12)
    for i, rev in enumerate(target_revs[:12]):
        count = len(f_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        if rev_cols[i].button(f"{rev}\n{count}", key=f"r_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # [3] Search & Filter Section (Small Size)
    st.markdown("<div style='margin-top:10px;' class='section-label'>Search & Filter</div>", unsafe_allow_html=True)
    
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    with st.container():
        s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
        with s1: search_q = st.text_input("S", placeholder="🔍 Search DWG. NO. or Description...", label_visibility="collapsed")
        with s2: a_sel = st.multiselect("A", options=sorted(work_df['AREA'].unique()), placeholder="All AREA", label_visibility="collapsed")
        with s3: y_sel = st.multiselect("Y", options=sorted(work_df['SYSTEM'].unique()), placeholder="All SYSTEM", label_visibility="collapsed")
        with s4: t_sel = st.multiselect("T", options=sorted(work_df['Status'].unique()), placeholder="All STATUS", label_visibility="collapsed")

    # Filtering Logic
    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]
    if search_q: work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | work_df['Description'].str.contains(search_q, case=False, na=False)]

    # [4] Results Summary & Action Buttons (Right Aligned Icons)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    res_col, btn_col = st.columns([5, 5])
    
    with res_col:
        st.markdown(f"<div style='font-size:12px; color:#6b7a90; padding-top:10px;'>Results: <b>{len(work_df):,}</b> drawings · Latest status · Sorted by DWG. NO.</div>", unsafe_allow_html=True)
    
    with btn_col:
        st.markdown("<div class='action-row'>", unsafe_allow_html=True)
        # 아이콘이 포함된 버튼 (우측 배치)
        a1, a2, a3, a4 = st.columns(4)
        with a1: st.button("📁 Excel", key="up", use_container_width=True)
        with a2: st.button("📄 PDF", key="pdf", use_container_width=True)
        with a3:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as wr: work_df.to_excel(wr, index=False)
            st.download_button("📤 Export", data=out.getvalue(), file_name="Dwg_Export.xlsx", use_container_width=True)
        with a4: st.button("🖨️ Print", key="prt", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # [5] Data Table (Remark Fully Visible)
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, hide_index=True, height=520,
        column_config={
            "Remark": st.column_config.TextColumn("Remark", width="large"),
            "Description": st.column_config.TextColumn("Description", width="medium"),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Rev": st.column_config.TextColumn("Rev", width="small")
        }
    )

    # [6] Pagination (Bottom Center)
    rows_per_page = 50
    total_pages = max((len(work_df) // rows_per_page) + (1 if len(work_df) % rows_per_page > 0 else 0), 1)
    if 'curr_pg' not in st.session_state: st.session_state.curr_pg = 1

    n1, n2, n3 = st.columns([3, 4, 3])
    with n1: st.caption(f"Showing {((st.session_state.curr_pg-1)*rows_per_page)+1} to {min(st.session_state.curr_pg*rows_per_page, len(work_df))}")
    with n2:
        st.markdown("<div class='nav-btn'>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns([1, 1, 1])
        if m1.button("◀", key="prev") and st.session_state.curr_pg > 1:
            st.session_state.curr_pg -= 1
            st.rerun()
        m2.markdown(f"<p style='text-align:center; font-size:12px; font-weight:700; padding-top:4px;'>{st.session_state.curr_pg} / {total_pages}</p>", unsafe_allow_html=True)
        if m3.button("▶", key="next") and st.session_state.curr_pg < total_pages:
            st.session_state.curr_pg += 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
