import streamlit as st
import pandas as pd
import os
from io import BytesIO

# 1. 경로 및 설정
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """최신 리비전 정보 추출 및 결합"""
    for r, d, m in [('3rd REV', '3rd DATE', '3rd REMARK'), 
                    ('2nd REV', '2nd DATE', '2nd REMARK'), 
                    ('1st REV', '1st DATE', '1st REMARK')]:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            rem = row.get(m, "")
            rem = "" if pd.isna(rem) or str(rem).lower() == "none" else str(rem)
            return val, row.get(d, '-'), rem
    return '-', '-', ''

def validate_drawing_data(df):
    """데이터 정합성 검증: 중복 체크 및 필수 항목 검사"""
    errors = []
    # 중복 DWG. NO. 체크
    duplicate_mask = df.duplicated(subset=['DWG. NO.'], keep=False)
    if duplicate_mask.any():
        dup_nos = df.loc[duplicate_mask, 'DWG. NO.'].unique().tolist()
        errors.append(f"❌ 중복 도면 번호 검출: {', '.join(map(str, dup_nos))}")
    # 필수 항목 결측치 체크
    for col in ['DWG. NO.', 'DRAWING TITLE']:
        if df[col].isnull().any():
            errors.append(f"⚠️ '{col}' 항목에 빈 값이 존재합니다.")
    return errors

def apply_ultimate_micro_ui():
    """초소형 버튼 UI 및 18px 데이터 폰트 설정 CSS"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding: 0.3rem 1.5rem !important; }
        [data-testid="stHeader"] { display: none !important; }
        
        .main-title { font-size: 18px !important; font-weight: 800; color: #1657d0; margin-bottom: 3px; }
        .section-label { font-size: 9px !important; font-weight: 700; color: #8a94a6; text-transform: uppercase; }

        /* Micro 버튼 및 Uploader 스타일 */
        div.stButton > button, div[data-testid="stFileUploader"] section {
            border-radius: 2px; border: 1px solid #dde3ec;
            height: 22px !important; font-size: 7.8px !important; 
            font-weight: 700 !important; padding: 0 2px !important;
            letter-spacing: -0.7px !important; white-space: nowrap !important;
        }
        
        /* 테이블 내부 18px 및 가운데 정렬 */
        div[data-testid="stDataFrame"] [role="gridcell"] div {
            font-size: 18px !important; text-align: center !important;
            justify-content: center !important; display: flex !important; align-items: center !important;
        }
        div[data-testid="stDataFrame"] [role="columnheader"] p {
            font-size: 18px !important; font-weight: 800 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_ultimate_micro_ui()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    # [Step 1] 데이터 로드 및 NameError 방지
    if not os.path.exists(DB_PATH):
        st.error("데이터베이스 파일을 찾을 수 없습니다.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    
    # 데이터 검증 실행
    v_errors = validate_drawing_data(df)
    if v_errors:
        with st.expander("🔍 데이터 검증 알림", expanded=True):
            for err in v_errors: st.warning(err)

    # 데이터 정제 (f_df 생성)
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

    # [Step 2] Revision Filter (Micro 버튼)
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_counts = f_df['Rev'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    rev_cols = st.columns(14)
    for i, rev in enumerate(target_revs[:14]):
        count = len(f_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        if rev_cols[i].button(f"{rev}({count})", key=f"r_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # [Step 3] Search & Filter
    st.markdown("<div style='margin-top:3px;' class='section-label'>Search & Filter</div>", unsafe_allow_html=True)
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
    with s1: search_q = st.text_input("S", placeholder="🔍 Search...", label_visibility="collapsed")
    with s2: a_sel = st.multiselect("A", options=sorted(work_df['AREA'].unique()), placeholder="Area", label_visibility="collapsed")
    with s3: y_sel = st.multiselect("Y", options=sorted(work_df['SYSTEM'].unique()), placeholder="System", label_visibility="collapsed")
    with s4: t_sel = st.multiselect("T", options=sorted(work_df['Status'].unique()), placeholder="Status", label_visibility="collapsed")

    # 검색 필터링 로직
    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]
    if search_q: work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | work_df['Description'].str.contains(search_q, case=False, na=False)]

    # [Step 4] Action Toolbar (실제 업로드 기능 구현)
    st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
    res_col, btn_col = st.columns([6, 4])
    with res_col:
        st.markdown(f"<div style='font-size:11px; color:#5c6773; font-weight:600;'>Total: {len(work_df):,}</div>", unsafe_allow_html=True)
    
    with btn_col:
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            # 실제 파일 업로드 로직 (기존 DB 파일을 교체)
            uploaded_file = st.file_uploader("Up", type=['xlsx'], key="db_upload", label_visibility="collapsed")
            if uploaded_file is not None:
                with open(DB_PATH, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Updated")
                st.rerun()
        with b2: st.button("📄 PDF", use_container_width=True)
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                work_df.to_excel(writer, index=False)
            st.download_button("📤 Ex", data=export_out.getvalue(), file_name="Dwg_Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Prt", use_container_width=True)

    # [Step 5] Table (18px, Center)
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, hide_index=True, height=750,
        column_config={"Description": st.column_config.TextColumn("Description", width="max")}
    )
