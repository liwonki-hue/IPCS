import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# --- Configuration & Paths ---
DB_PATH = 'data/drawing_master.xlsx'
ITEMS_PER_PAGE = 30 

def get_latest_rev_info(row):
    """최신 Revision 정보를 안전하게 추출"""
    revisions = [
        ('3rd REV', '3rd DATE', '3rd REMARK'), 
        ('2nd REV', '2nd DATE', '2nd REMARK'), 
        ('1st REV', '1st DATE', '1st REMARK')
    ]
    for r, d, m in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            rem = row.get(m, "")
            rem = "" if pd.isna(rem) or str(rem).lower() == "none" else str(rem)
            return val, row.get(d, '-'), rem
    return '-', '-', ''

def apply_professional_style():
    """기존의 정돈된 레이아웃 스타일 복구"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 1.5rem !important; }
        .main-title { font-size: 22px !important; font-weight: 800; color: #1657d0; margin-bottom: 15px; border-bottom: 2px solid #f0f2f6; padding-bottom: 5px; }
        .section-label { font-size: 11px; font-weight: 700; color: #6b7a90; margin-bottom: 5px; text-transform: uppercase; }
        div.stButton > button { height: 32px !important; font-size: 12px !important; font-weight: 600; }
        .page-info { font-size: 13px; font-weight: 700; text-align: center; color: #1657d0; line-height: 32px; }
        /* 테이블 높이 최적화 */
        [data-testid="stDataFrame"] { border: 1px solid #e6e9ef; border-radius: 4px; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(display_df, tab_name):
    """복구된 레이아웃: 필터 -> 중복체크/액션 -> 테이블 -> 하단 네비게이션"""
    
    # --- 1. SEARCH & FILTERS (Revision Filter 포함) ---
    st.markdown("<div class='section-label'>Search & Multi-Filters</div>", unsafe_allow_html=True)
    f_cols = st.columns([3, 2, 2, 2, 2, 5])
    with f_cols[0]: 
        search_term = st.text_input("Search", key=f"search_{tab_name}", placeholder="No. or Title...")
    with f_cols[1]: 
        sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]: 
        sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]: 
        # 복구: Revision Filter (Rev 기준 필터링)
        sel_rev = st.selectbox("Revision", ["All"] + sorted(display_df['Rev'].unique().tolist()), key=f"rev_{tab_name}")
    with f_cols[4]: 
        sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 데이터 필터링 적용
    f_df = display_df.copy()
    if sel_sys != "All": f_df = f_df[f_df['SYSTEM'] == sel_sys]
    if sel_area != "All": f_df = f_df[f_df['Area'] == sel_area]
    if sel_rev != "All": f_df = f_df[f_df['Rev'] == sel_rev]
    if sel_stat != "All": f_df = f_df[f_df['Status'] == sel_stat]
    if search_term:
        f_df = f_df[f_df['DWG. NO.'].str.contains(search_term, case=False, na=False) | 
                    f_df['Description'].str.contains(search_term, case=False, na=False)]

    # --- 2. 중복 검사 및 액션 툴바 복구 ---
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([3, 3, 2, 1, 1, 1, 1])
    
    with t_cols[0]: 
        st.markdown(f"**Total Records: {len(f_df):,}**")
    
    with t_cols[1]:
        # 복구: 중복 검사 로직 (DWG No. 중복 확인)
        dup_count = f_df['DWG. NO.'].duplicated().sum()
        if dup_count > 0:
            st.warning(f"⚠️ {dup_count} Duplicates Found")
        else:
            st.success("✅ No Duplicates")

    # 액션 버튼들
    with t_cols[3]: st.button("📁 Upload", key=f"up_{tab_name}")
    with t_cols[4]: st.button("📄 PDF", key=f"pdf_{tab_name}")
    with t_cols[5]:
        export_out = BytesIO()
        with pd.ExcelWriter(export_out) as writer: f_df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}")
    with t_cols[6]: st.button("🖨️ Print", key=f"prt_{tab_name}")

    # --- 3. DATA TABLE (30줄 고정) ---
    total_pages = max(1, math.ceil(len(f_df) / ITEMS_PER_PAGE))
    page_key = f"page_{tab_name}"
    if page_key not in st.session_state: st.session_state[page_key] = 1
    
    start_idx = (st.session_state[page_key] - 1) * ITEMS_PER_PAGE
    st.dataframe(f_df.iloc[start_idx : start_idx + ITEMS_PER_PAGE], use_container_width=True, hide_index=True, height=1050)

    # --- 4. NAVIGATION (하단 배치) ---
    st.markdown("---")
    n_left, n_center, n_right = st.columns([5, 2, 5])
    with n_center:
        btn_prev, info_txt, btn_next = st.columns([1, 2, 1])
        with btn_prev:
            if st.button("«", key=f"btn_prev_{tab_name}", disabled=(st.session_state[page_key] == 1)):
                st.session_state[page_key] -= 1
                st.rerun()
        with info_txt:
            st.markdown(f"<div class='page-info'>{st.session_state[page_key]} / {total_pages}</div>", unsafe_allow_html=True)
        with btn_next:
            if st.button("»", key=f"btn_next_{tab_name}", disabled=(st.session_state[page_key] == total_pages)):
                st.session_state[page_key] += 1
                st.rerun()

def show_doc_control():
    """메인 호출부"""
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("데이터 파일을 찾을 수 없습니다.")
        return

    # 데이터 로드 및 전처리 (Rev 정보 포함)
    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), 
            "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, 
            "Date": l_date, 
            "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'), 
            "Remark": l_rem
        })
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    
    # 각 탭별 안전한 필터링 호출
    tab_configs = [
        (tabs[0], master_df, "Master"),
        (tabs[1], master_df[master_df['Category'].str.contains('ISO', case=False, na=False)], "ISO"),
        (tabs[2], master_df[master_df['Category'].str.contains('Support', case=False, na=False)], "Support"),
        (tabs[3], master_df[master_df['Category'].str.contains('Valve', case=False, na=False)], "Valve"),
        (tabs[4], master_df[master_df['Category'].str.contains('Specialty|Speciality', case=False, na=False)], "Specialty")
    ]

    for tab, df, name in tab_configs:
        with tab:
            render_drawing_table(df, name)
