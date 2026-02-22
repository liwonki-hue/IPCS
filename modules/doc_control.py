import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# 설정
DB_PATH = 'data/drawing_master.xlsx'
ITEMS_PER_PAGE = 30 

def get_latest_rev_info(row):
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
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 2rem !important; }
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 10px; border-bottom: 2px solid #f0f2f6; padding-bottom: 8px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase; }
        div.stButton > button { height: 28px !important; font-size: 11px !important; font-weight: 600 !important; }
        .page-info { font-size: 13px; font-weight: 700; text-align: center; line-height: 28px; color: #1657d0; }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Upload Master File")
def show_upload_dialog():
    st.write("Drawing Master 파일을 업로드하십시오.")
    uploaded_file = st.file_uploader("Choose XLSX file", type=['xlsx'])
    if uploaded_file:
        if st.button("Apply & Save", type="primary", use_container_width=True):
            try:
                df_upload = pd.read_excel(uploaded_file, sheet_name='DRAWING LIST')
                df_upload.to_excel(DB_PATH, sheet_name='DRAWING LIST', index=False)
                st.success("데이터 업데이트 완료")
                st.rerun()
            except Exception as e:
                st.error(f"오류: {str(e)}")

def render_drawing_table(display_df, tab_name):
    # --- 1. 상단 필터 ---
    st.markdown("<div class='section-label'>Search & Filters</div>", unsafe_allow_html=True)
    f_cols = st.columns([4, 2, 2, 2, 10])
    with f_cols[0]: search_term = st.text_input("Search", key=f"search_{tab_name}", placeholder="DWG No. or Title...")
    with f_cols[1]: sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]: sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]: sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 필터링 적용
    f_df = display_df.copy()
    if sel_sys != "All": f_df = f_df[f_df['SYSTEM'] == sel_sys]
    if sel_area != "All": f_df = f_df[f_df['Area'] == sel_area]
    if sel_stat != "All": f_df = f_df[f_df['Status'] == sel_stat]
    if search_term:
        f_df = f_df[f_df['DWG. NO.'].str.contains(search_term, case=False, na=False) | f_df['Description'].str.contains(search_term, case=False, na=False)]

    # --- 2. 액션 툴바 ---
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    with t_cols[0]: st.markdown(f"**Total: {len(f_df):,} records**")
    with t_cols[2]: 
        if st.button("📁 Upload", key=f"up_{tab_name}"): show_upload_dialog()
    with t_cols[3]: st.button("📄 PDF", key=f"pdf_{tab_name}")
    with t_cols[4]:
        export_out = BytesIO()
        with pd.ExcelWriter(export_out) as writer: f_df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}")
    with t_cols[5]: st.button("🖨️ Print", key=f"prt_{tab_name}")

    # --- 3. 데이터 테이블 (30줄) ---
    total_pages = max(1, math.ceil(len(f_df) / ITEMS_PER_PAGE))
    page_key = f"page_{tab_name}"
    if page_key not in st.session_state: st.session_state[page_key] = 1
    
    start_idx = (st.session_state[page_key] - 1) * ITEMS_PER_PAGE
    st.dataframe(f_df.iloc[start_idx : start_idx + ITEMS_PER_PAGE], use_container_width=True, hide_index=True, height=1050)

    # --- 4. 하단 네비게이션 ---
    st.markdown("---")
    n_col1, n_col2, n_col3 = st.columns([5, 2, 5])
    with n_col2:
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
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Excel Database not found.")
        return

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
            "Rev": l_rev, "Date": l_date, "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'), "Remark": l_rem
        })
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    
    # 각 탭별 렌더링 (괄호 에러 방지를 위해 필터 데이터를 변수로 사전 선언)
    with tabs[0]: 
        render_drawing_table(master_df, "Master")
    
    with tabs[1]: 
        df_iso = master_df[master_df['Category'].str.contains('ISO', case=False, na=False)]
        render_drawing_table(df_iso, "ISO")
    
    with tabs[2]: 
        df_supp = master_df[master_df['Category'].str.contains('Support', case=False, na=False)]
        render_drawing_table(df_supp, "Support")
    
    with tabs[3]: 
        df_valve = master_df[master_df['Category'].str.contains('Valve', case=False, na=False)]
        render_drawing_table(df_valve, "Valve")
    
    with tabs[4]: 
        # 170번 라인 에러 지점: 변수 분리 및 괄호 마감 확인
        df_spec = master_df[master_df['Category'].str.contains('Specialty|Speciality', case=False, na=False)]
        render_drawing_table(df_spec, "Specialty")
