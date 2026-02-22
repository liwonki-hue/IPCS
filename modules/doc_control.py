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

def apply_ultimate_compact_ui():
    """버튼 폰트 2단계 추가 축소 (최종 Micro 사이즈) 및 데이터 18px 유지"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f7f9fc !important;
            color: #0d1826 !important;
        }
        .block-container { padding: 0.3rem 1.5rem !important; } /* 상단 여백 최소화 */
        [data-testid="stHeader"] { display: none !important; }
        
        /* 1. 타이틀 영역 */
        .main-title { font-size: 18px !important; font-weight: 800; color: #1657d0; margin-bottom: 3px; }
        .section-label { 
            font-size: 9px !important; 
            font-weight: 700; color: #8a94a6; text-transform: uppercase; margin-bottom: 2px; 
        }

        /* 2. 버튼 2단계 추가 축소 (최종: 폰트 9px~10px, 높이 22px) */
        div.stButton > button {
            border-radius: 2px; border: 1px solid #dde3ec;
            background-color: white; color: #374559;
            height: 22px !important; /* 버튼 높이 최소화 */
            font-size: 9px !important; /* 폰트 2단계 추가 축소 */
            padding: 0 3px !important;
            min-width: unset !important;
            line-height: 1 !important;
            letter-spacing: -0.5px !important; /* 좁은 공간 효율성 */
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }

        /* 3. Search & Filter 입력창 높이 동기화 (22px) */
        div[data-baseweb="select"], div[data-baseweb="base-input"], input {
            min-height: 22px !important; height: 22px !important; 
            font-size: 10px !important; 
        }

        /* 4. 표(st.dataframe) 내부 데이터 18px 고정 (요청 사항 유지) */
        div[data-testid="stDataFrame"] [role="gridcell"] div {
            font-size: 18px !important;
            text-align: center !important;
            justify-content: center !important;
            display: flex !important;
            align-items: center !important;
        }
        div[data-testid="stDataFrame"] [role="columnheader"] p {
            font-size: 18px !important;
            font-weight: 800 !important;
            text-align: center !important;
            justify-content: center !important;
        }
        
        /* 5. 결과 정보 요약 */
        .result-info { font-size: 11px; color: #5c6773; font-weight: 600; padding-top: 2px; }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_ultimate_compact_ui()
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

    # [1] Revision Filter (Ultimate Micro: 22px Height / 9px Font)
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_counts = f_df['Rev'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    rev_cols = st.columns(18) # 한 줄에 더 많이 배치하여 공간 절약
    for i, rev in enumerate(target_revs[:18]):
        count = len(f_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        btn_label = f"{rev}({count})"
        if rev_cols[i].button(btn_label, key=f"r_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # [2] Search & Filter (Ultimate Micro)
    st.markdown("<div style='margin-top:3px;' class='section-label'>Search & Filter</div>", unsafe_allow_html=True)
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    with st.container():
        s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
        with s1: search_q = st.text_input("S", placeholder="🔍 Search...", label_visibility="collapsed")
        with s2: a_sel = st.multiselect("A", options=sorted(work_df['AREA'].unique()), placeholder="Area", label_visibility="collapsed")
        with s3: y_sel = st.multiselect("Y", options=sorted(work_df['SYSTEM'].unique()), placeholder="System", label_visibility="collapsed")
        with s4: t_sel = st.multiselect("T", options=sorted(work_df['Status'].unique()), placeholder="Status", label_visibility="collapsed")

    # 필터 로직 생략 (동일)
    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]
    if search_q: 
        work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | 
                          work_df['Description'].str.contains(search_q, case=False, na=False)]

    # [3] Action Toolbar (Ultimate Micro)
    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
    res_col, btn_col = st.columns([7, 3])
    with res_col:
        st.markdown(f"<div class='result-info'>Total: {len(work_df):,}</div>", unsafe_allow_html=True)
    with btn_col:
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Up", use_container_width=True)
        with b2: st.button("📄 PDF", use_container_width=True)
        with b3:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as wr: work_df.to_excel(wr, index=False)
            st.download_button("📤 Ex", data=out.getvalue(), file_name="Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Prt", use_container_width=True)

    # [4] Table (18px, Center)
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, 
        hide_index=True, 
        height=820, # 컨트롤 영역 축소로 인한 테이블 영역 확장
        column_config={
            "Description": st.column_config.TextColumn("Description", width="max")
        }
    )
