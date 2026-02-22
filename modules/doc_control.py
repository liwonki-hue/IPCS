import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# --- Configuration ---
DB_PATH = 'data/drawing_master.xlsx'
ITEMS_PER_PAGE = 30 

def apply_professional_style():
    """기존의 넓고 정돈된 레이아웃 및 폰트 스타일 복구"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 1.5rem !important; max-width: 95% !important; }
        .main-title { font-size: 22px !important; font-weight: 800; color: #1657d0; margin-bottom: 20px; }
        .section-label { font-size: 11px; font-weight: 700; color: #6b7a90; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* 버튼 및 텍스트 정렬 최적화 */
        div.stButton > button { 
            width: 100%;
            height: 35px !important; 
            font-size: 13px !important; 
            font-weight: 600 !important;
            border-radius: 6px !important;
        }
        .page-info { font-size: 14px; font-weight: 700; text-align: center; color: #1657d0; line-height: 35px; }
        
        /* 테이블 내부 텍스트 가독성 (Remark 등 긴 텍스트 대비) */
        [data-testid="stDataFrame"] { border: 1px solid #e6e9ef; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(display_df, tab_name):
    """기존 레이아웃 복구: 필터 1라인 -> (통계/중복체크/액션) 2라인 -> 테이블 -> 네비게이션"""
    
    # --- 1. SEARCH & FILTERS (기존 상단 배치) ---
    st.markdown("<div class='section-label'>Search & Multi-Filters</div>", unsafe_allow_html=True)
    f_cols = st.columns([3, 2, 2, 2, 2])
    with f_cols[0]: search_term = st.text_input("Search", key=f"search_{tab_name}", placeholder="No. or Title...")
    with f_cols[1]: sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]: sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]: sel_rev = st.selectbox("Revision", ["All"] + sorted(display_df['Rev'].unique().tolist() if 'Rev' in display_df.columns else []), key=f"rev_{tab_name}")
    with f_cols[4]: sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 필터링 로직
    f_df = display_df.copy()
    if sel_sys != "All": f_df = f_df[f_df['SYSTEM'] == sel_sys]
    if sel_area != "All": f_df = f_df[f_df['Area'] == sel_area]
    if sel_rev != "All": f_df = f_df[f_df['Rev'] == sel_rev]
    if sel_stat != "All": f_df = f_df[f_df['Status'] == sel_stat]
    if search_term:
        f_df = f_df[f_df['DWG. NO.'].astype(str).str.contains(search_term, case=False, na=False) | 
                    f_df['Description'].astype(str).str.contains(search_term, case=False, na=False)]

    # --- 2. STATISTICS, DUPLICATE CHECK & ACTIONS (기존 위치 및 간격 복구) ---
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    
    # 상단 정보 및 액션 버튼 레이아웃 비율 조정 (기존 image_4b31a5.png 참조)
    info_col, action_col = st.columns([7, 3])
    
    with info_col:
        # 가로 정렬을 위한 내부 컬럼
        stat_left, stat_right = st.columns([2, 5])
        with stat_left:
            st.markdown(f"**Total Records: {len(f_df):,}**")
        with stat_right:
            # 중복 검사 메시지 창 위치 복구
            dup_count = f_df['DWG. NO.'].duplicated().sum()
            if dup_count > 0:
                st.warning(f"⚠️ {dup_count} Duplicates Found", icon=None)
            else:
                st.success("✅ No Duplicates", icon=None)

    with action_col:
        # 버튼 아이콘 및 텍스트 복구 (기존 스타일)
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Upload", key=f"up_{tab_name}")
        with b2: st.button("📄 PDF", key=f"pdf_{tab_name}")
        with b3: 
            export_out = BytesIO()
            with pd.ExcelWriter(export_out) as writer: f_df.to_excel(writer, index=False)
            st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}")
        with b4: st.button("🖨️ Print", key=f"prt_{tab_name}")

    # --- 3. DATA TABLE (컬럼 너비 최적화: Remark 가독성 확보) ---
    total_pages = max(1, math.ceil(len(f_df) / ITEMS_PER_PAGE))
    page_key = f"page_{tab_name}"
    if page_key not in st.session_state: st.session_state[page_key] = 1
    
    start_idx = (st.session_state[page_key] - 1) * ITEMS_PER_PAGE
    paged_df = f_df.iloc[start_idx : start_idx + ITEMS_PER_PAGE]

    # Remark 등 긴 텍스트 컬럼 너비 지정
    st.dataframe(
        paged_df, 
        use_container_width=True, 
        hide_index=True, 
        height=1050,
        column_config={
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Remark": st.column_config.TextColumn("Remark", width="large"), # Remark 간격 대폭 확대
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium")
        }
    )

    # --- 4. NAVIGATION (최하단 고정) ---
    st.markdown("---")
    _, nav_center, _ = st.columns([5, 2, 5])
    with nav_center:
        p_prev, p_txt, p_next = st.columns([1, 2, 1])
        with p_prev:
            if st.button("«", key=f"p_prev_{tab_name}", disabled=(st.session_state[page_key] == 1)):
                st.session_state[page_key] -= 1
                st.rerun()
        with p_txt:
            st.markdown(f"<div class='page-info'>{st.session_state[page_key]} / {total_pages}</div>", unsafe_allow_html=True)
        with p_next:
            if st.button("»", key=f"p_next_{tab_name}", disabled=(st.session_state[page_key] == total_pages)):
                st.session_state[page_key] += 1
                st.rerun()
