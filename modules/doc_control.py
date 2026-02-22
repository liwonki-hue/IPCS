import streamlit as st
import pandas as pd
import os
from io import BytesIO

# File Path Settings
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """최신 리비전 정보를 추출하며 None/NaN은 공란으로 처리"""
    for r, d, m in [('3rd REV', '3rd DATE', '3rd REMARK'), 
                    ('2nd REV', '2nd DATE', '2nd REMARK'), 
                    ('1st REV', '1st DATE', '1st REMARK')]:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            rem = row.get(m, "")
            rem = "" if pd.isna(rem) or str(rem).lower() == "none" else str(rem)
            return val, row.get(d, '-'), rem
    return '-', '-', ''

def apply_ultra_large_ui():
    """데이터 20px 상향 및 완벽한 가운데 정렬을 위한 CSS"""
    st.markdown("""
        <style>
        /* 1. 기본 테마 강제 및 배경 */
        :root { color-scheme: light only !important; }
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f7f9fc !important;
            color: #0d1826 !important;
        }
        .block-container { padding: 1.5rem 2.5rem !important; }
        [data-testid="stHeader"] { display: none !important; }
        
        /* 2. 제목 및 섹션 레이블 상향 */
        .main-title { font-size: 32px !important; font-weight: 800; color: #1657d0; margin-bottom: 20px; }
        .section-label { font-size: 15px !important; font-weight: 700; color: #6b7a90; text-transform: uppercase; margin-bottom: 10px; }

        /* 3. 표 내부 데이터 20px 및 가운데 정렬 강제 */
        [data-testid="stDataFrame"] div[role="gridcell"] > div {
            font-size: 20px !important;
            font-weight: 500 !important;
            justify-content: center !important;
            text-align: center !important;
            line-height: 1.5 !important;
        }
        
        /* 4. 컬럼 헤더 20px 및 가운데 정렬 강제 */
        div[data-testid="stDataFrame"] div[role="columnheader"] p {
            font-size: 20px !important;
            font-weight: 900 !important;
            color: #1a2a3a !important;
            text-align: center !important;
            justify-content: center !important;
            width: 100%;
        }

        /* 5. 컨트롤 컴포넌트 크기 리사이징 (42px) */
        div.stButton > button {
            border-radius: 6px; border: 1px solid #dde3ec;
            background-color: white; color: #374559;
            height: 42px !important; font-size: 16px !important; padding: 0 18px !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }

        div[data-baseweb="select"], div[data-baseweb="base-input"], input {
            min-height: 42px !important; height: 42px !important; font-size: 16px !important;
        }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_ultra_large_ui()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Excel database file not found.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')

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
    
    rev_cols = st.columns(10)
    for i, rev in enumerate(target_revs[:10]):
        count = len(f_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        if rev_cols[i].button(f"{rev}\n{count}", key=f"r_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # [2] Search & Filter
    st.markdown("<div style='margin-top:20px;' class='section-label'>Search & Filter</div>", unsafe_allow_html=True)
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    with st.container():
        s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
        with s1: search_q = st.text_input("Search", placeholder="🔍 Search drawing...", label_visibility="collapsed")
        with s2: a_sel = st.multiselect("Area", options=sorted(work_df['AREA'].unique()), placeholder="Area", label_visibility="collapsed")
        with s3: y_sel = st.multiselect("System", options=sorted(work_df['SYSTEM'].unique()), placeholder="System", label_visibility="collapsed")
        with s4: t_sel = st.multiselect("Status", options=sorted(work_df['Status'].unique()), placeholder="Status", label_visibility="collapsed")

    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]
    if search_q: 
        work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | 
                          work_df['Description'].str.contains(search_q, case=False, na=False)]

    # [3] Action Toolbar
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    res_col, btn_col = st.columns([4, 6])
    with res_col:
        st.markdown(f"<div style='font-size:18px; color:#6b7a90; padding-top:12px;'>Results: <b>{len(work_df):,}</b></div>", unsafe_allow_html=True)
    with btn_col:
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Upload", use_container_width=True)
        with b2: st.button("📄 PDF", use_container_width=True)
        with b3:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as wr: work_df.to_excel(wr, index=False)
            st.download_button("📤 Export", data=out.getvalue(), file_name="Dwg_Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Print", use_container_width=True)

    # [4] Table (20px, Center, Description Max)
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, 
        hide_index=True, 
        height=800, # 폰트가 커짐에 따라 높이 충분히 확보
        column_config={
            "Category": st.column_config.TextColumn("Cat.", width="small"),
            "DWG. NO.": st.column_config.TextColumn("Drawing No.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="max"),
            "Rev": st.column_config.TextColumn("Rev", width="small"),
            "Date": st.column_config.TextColumn("Date", width="small"),
            "Hold": st.column_config.TextColumn("H", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Remark": st.column_config.TextColumn("Remark", width="large")
        }
    )
