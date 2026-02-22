import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# --- 기본 설정 ---
DB_PATH = 'data/drawing_master.xlsx'
ITEMS_PER_PAGE = 30 

def apply_professional_style():
    """기존의 정돈된 엔지니어링 툴 스타일 적용"""
    st.markdown("""
        <style>
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0; margin-bottom: 20px; }
        .section-label { font-size: 11px; font-weight: 700; color: #6b7a90; margin-bottom: 8px; text-transform: uppercase; }
        div.stButton > button { height: 35px !important; font-size: 14px !important; }
        .page-info { font-size: 14px; font-weight: 700; text-align: center; color: #1657d0; line-height: 35px; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(display_df, tab_name):
    # --- 1. SEARCH & FILTERS ---
    st.markdown("<div class='section-label'>SEARCH & MULTI-FILTERS</div>", unsafe_allow_html=True)
    f_cols = st.columns([3, 2, 2, 2, 2])
    with f_cols[0]: search_term = st.text_input("Search", key=f"search_{tab_name}", placeholder="No. or Title...")
    with f_cols[1]: sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]: sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]: 
        revs = ["All"] + sorted(display_df['Rev'].unique().tolist()) if 'Rev' in display_df.columns else ["All"]
        sel_rev = st.selectbox("Revision", revs, key=f"rev_{tab_name}")
    with f_cols[4]: sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 필터 적용
    f_df = display_df.copy()
    if search_term:
        f_df = f_df[f_df['DWG. NO.'].astype(str).str.contains(search_term, case=False, na=False) | 
                    f_df['Description'].astype(str).str.contains(search_term, case=False, na=False)]
    if sel_sys != "All": f_df = f_df[f_df['SYSTEM'] == sel_sys]
    if sel_area != "All": f_df = f_df[f_df['Area'] == sel_area]
    if 'Rev' in f_df.columns and sel_rev != "All": f_df = f_df[f_df['Rev'] == sel_rev]
    if sel_stat != "All": f_df = f_df[f_df['Status'] == sel_stat]

    # --- 2. STATISTICS & ACTIONS (image_4b31a5 복구) ---
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    info_col, action_col = st.columns([7, 3])
    
    with info_col:
        stat_l, stat_r = st.columns([2, 5])
        with stat_l:
            st.markdown(f"**Total Records: {len(f_df):,}**")
        with stat_r:
            # 중복 검사 메시지 창 위치 복구
            dup_count = f_df['DWG. NO.'].duplicated().sum()
            if dup_count > 0:
                st.warning(f"⚠️ {dup_count} Duplicates Found", icon=None)
            else:
                st.success("✅ No Duplicates", icon=None)

    with action_col:
        # 버튼 아이콘 및 명칭 복구
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Upload", key=f"up_{tab_name}")
        with b2: st.button("📄 PDF", key=f"pdf_{tab_name}")
        with b3:
            export_data = BytesIO()
            with pd.ExcelWriter(export_data) as writer: f_df.to_excel(writer, index=False)
            st.download_button("📤 Export", data=export_data.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}")
        with b4: st.button("🖨️ Print", key=f"prt_{tab_name}")

    # --- 3. DATA TABLE (컬럼 너비 최적화) ---
    total_pages = max(1, math.ceil(len(f_df) / ITEMS_PER_PAGE))
    page_key = f"page_{tab_name}"
    if page_key not in st.session_state: st.session_state[page_key] = 1
    
    start_idx = (st.session_state[page_key] - 1) * ITEMS_PER_PAGE
    
    st.dataframe(
        f_df.iloc[start_idx : start_idx + ITEMS_PER_PAGE], 
        use_container_width=True, 
        hide_index=True, 
        height=1050,
        column_config={
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Remark": st.column_config.TextColumn("Remark", width="large"), # Remark 너비 확보
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium")
        }
    )

    # --- 4. NAVIGATION ---
    st.markdown("---")
    _, n_c, _ = st.columns([5, 2, 5])
    with n_c:
        p_prev, p_txt, p_next = st.columns([1, 2, 1])
        with p_prev:
            if st.button("«", key=f"prev_{tab_name}", disabled=(st.session_state[page_key] == 1)):
                st.session_state[page_key] -= 1
                st.rerun()
        with p_txt:
            st.markdown(f"<div class='page-info'>{st.session_state[page_key]} / {total_pages}</div>", unsafe_allow_html=True)
        with p_next:
            if st.button("»", key=f"next_{tab_name}", disabled=(st.session_state[page_key] == total_pages)):
                st.session_state[page_key] += 1
                st.rerun()

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)
    # 이후 데이터 로드 및 탭 렌더링 로직 (생략)
