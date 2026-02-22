import streamlit as st
import pandas as pd
import math
from io import BytesIO

DB_PATH = 'data/drawing_master.xlsx'
ITEMS_PER_PAGE = 30

def apply_professional_style():
    st.markdown("""
        <style>
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0; margin-bottom: 20px; }
        .section-label { font-size: 11px; font-weight: 700; color: #6b7a90; margin-bottom: 8px; text-transform: uppercase; }
        div.stButton > button { height: 35px !important; font-size: 14px !important; }
        .page-info { font-size: 14px; font-weight: 700; text-align: center; color: #1657d0; line-height: 35px; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(display_df, tab_name):
    # 1. Search & Filters
    st.markdown("<div class='section-label'>SEARCH & MULTI-FILTERS</div>", unsafe_allow_html=True)
    f_cols = st.columns([3, 2, 2, 2, 2])
    with f_cols[0]: search_term = st.text_input("Search", key=f"s_{tab_name}", placeholder="No. or Title...")
    with f_cols[1]: sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]: sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]: sel_rev = st.selectbox("Revision", ["All"] + sorted(display_df['Rev'].unique().tolist()), key=f"rev_{tab_name}")
    with f_cols[4]: sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 데이터 필터링 로직 (생략 - 기존과 동일)
    f_df = display_df.copy() # 실제 구현 시 필터 조건 적용 필요

    # 2. Statistics & Duplicate Check & Buttons (중복 검사 창 위치 복구)
    st.write("")
    info_col, action_col = st.columns([7, 3])
    
    with info_col:
        stat_l, stat_r = st.columns([2, 5])
        with stat_l:
            st.markdown(f"**Total Records: {len(f_df):,}**")
        with stat_r:
            dup_count = f_df['DWG. NO.'].duplicated().sum()
            if dup_count > 0:
                st.warning(f"⚠️ {dup_count} Duplicates Found", icon=None)
            else:
                st.success("✅ No Duplicates", icon=None)

    with action_col:
        # 버튼 아이콘 및 텍스트 복구
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Upload", key=f"up_{tab_name}")
        with b2: st.button("📄 PDF", key=f"pdf_{tab_name}")
        with b3: st.button("📤 Export", key=f"ex_{tab_name}")
        with b4: st.button("🖨️ Print", key=f"prt_{tab_name}")

    # 3. Data Table (Remark 컬럼 너비 확보)
    st.dataframe(
        f_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Remark": st.column_config.TextColumn("Remark", width="large"), # 간격 확대
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium")
        }
    )

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)
    
    # 데이터 로드 로직 (사용자 환경에 맞춰 구현)
    # 예시 데이터프레임 생성 (실제 운영 시에는 Excel 로드)
    # master_df = pd.read_excel(DB_PATH)
    
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    
    # 탭별 렌더링 (괄호 닫힘 주의)
    with tabs[0]: render_drawing_table(pd.DataFrame(), "Master")
    with tabs[1]: render_drawing_table(pd.DataFrame(), "ISO")
    with tabs[2]: render_drawing_table(pd.DataFrame(), "Support")
    with tabs[3]: render_drawing_table(pd.DataFrame(), "Valve")
    with tabs[4]: render_drawing_table(pd.DataFrame(), "Specialty")
