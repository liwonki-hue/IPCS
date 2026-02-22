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

def apply_precise_font_ui():
    """필터 14px, 데이터 18px 강제 적용을 위한 CSS 보강"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f7f9fc !important;
            color: #0d1826 !important;
        }
        .block-container { padding: 1.2rem 2.5rem !important; }
        [data-testid="stHeader"] { display: none !important; }
        
        /* 1. 타이틀 및 섹션 레이블 */
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0; margin-bottom: 12px; }
        .section-label { 
            font-size: 13px !important; 
            font-weight: 700; color: #6b7a90; text-transform: uppercase; margin-bottom: 6px; 
        }

        /* 2. 필터 영역 (버튼 및 입력창 14px 적용) */
        div.stButton > button {
            border-radius: 4px; border: 1px solid #dde3ec;
            background-color: white; color: #374559;
            height: 36px !important; 
            font-size: 14px !important; /* 필터 버튼 14px */
            font-weight: 600 !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }

        div[data-baseweb="select"], div[data-baseweb="base-input"], input {
            min-height: 34px !important; height: 34px !important; 
            font-size: 14px !important; /* 입력창/검색창 폰트 14px */
        }
        .stMultiSelect span { font-size: 13px !important; }

        /* 3. 표(st.dataframe) 내부 데이터 18px 강제 적용 */
        /* 셀 데이터 정렬 및 크기 */
        div[data-testid="stDataFrame"] [role="gridcell"] div {
            font-size: 18px !important; /* 데이터 폰트 18px */
            text-align: center !important;
            justify-content: center !important;
            display: flex !important;
            align-items: center !important;
        }
        
        /* 컬럼 헤더 정렬 및 크기 */
        div[data-testid="stDataFrame"] [role="columnheader"] p {
            font-size: 18px !important; /* 헤더 폰트 18px */
            font-weight: 800 !important;
            text-align: center !important;
            justify-content: center !important;
            width: 100%;
        }
        
        /* 4. 결과 요약 텍스트 */
        .result-text { font-size: 15px; color: #374559; font-weight: 600; padding-top: 8px; }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_precise_font_ui()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at: {DB_PATH}")
        return

    # 데이터 로드
    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')

    # 데이터 전처리
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

    # [1] Revision Filter (14px)
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_counts = f_df['Rev'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    rev_cols = st.columns(10)
    for i, rev in enumerate(target_revs[:10]):
        count = len(f_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        if rev_cols[i].button(f"{rev}\n({count})", key=f"r_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # [2] Search & Filter (14px)
    st.markdown("<div style='margin-top:15px;' class='section-label'>Search & Filter</div>", unsafe_allow_html=True)
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    with st.container():
        s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
        with s1: search_q = st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed")
        with s2: a_sel = st.multiselect("Area", options=sorted(work_df['AREA'].unique()), placeholder="Area", label_visibility="collapsed")
        with s3: y_sel = st.multiselect("System", options=sorted(work_df['SYSTEM'].unique()), placeholder="System", label_visibility="collapsed")
        with s4: t_sel = st.multiselect("Status", options=sorted(work_df['Status'].unique()), placeholder="Status", label_visibility="collapsed")

    # Filter Logic
    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]
    if search_q: 
        work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | 
                          work_df['Description'].str.contains(search_q, case=False, na=False)]

    # [3] Action Toolbar
    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    res_col, btn_col = st.columns([4, 6])
    with res_col:
        st.markdown(f"<div class='result-text'>Total: {len(work_df):,} items</div>", unsafe_allow_html=True)
    with btn_col:
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Upload", use_container_width=True)
        with b2: st.button("📄 PDF", use_container_width=True)
        with b3:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as wr: work_df.to_excel(wr, index=False)
            st.download_button("📤 Export", data=out.getvalue(), file_name="Dwg_Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Print", use_container_width=True)

    # [4] Table (18px, Center Alignment, Description Max)
    # 폰트 변경이 안 되는 문제를 방지하기 위해 column_config 내 타입 지정을 명확히 함
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, 
        hide_index=True, 
        height=750,
        column_config={
            "Description": st.column_config.TextColumn("Description", width="max"),
            "Remark": st.column_config.TextColumn("Remark", width="large"),
            "DWG. NO.": st.column_config.TextColumn("Drawing No.", width="medium")
        }
    )
