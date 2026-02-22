import streamlit as st
import pandas as pd
import os

DB_PATH = 'data/drawing_master.xlsx'

def apply_custom_style():
    """전문적인 엔지니어링 툴 느낌의 CSS 적용"""
    st.markdown("""
        <style>
        .block-container { padding-top: 1.5rem !important; }
        .main-title { font-size: 24px; font-weight: 800; color: #1657d0; margin-bottom: 20px; }
        .section-label { font-size: 11px; font-weight: 700; color: #6b7a90; margin-bottom: 10px; text-transform: uppercase; }
        div.stButton > button { height: 35px !important; font-size: 14px !important; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(df, tab_name):
    """image_4b31a5.png 레이아웃 재현"""
    # 1. SEARCH & FILTERS (한 줄 배치)
    st.markdown("<div class='section-label'>SEARCH & MULTI-FILTERS</div>", unsafe_allow_html=True)
    f_cols = st.columns([3, 2, 2, 2, 2])
    with f_cols[0]: search = st.text_input("Search", key=f"s_{tab_name}", placeholder="No. or Title...")
    with f_cols[1]: sel_sys = st.selectbox("System", ["All"] + sorted(df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]: sel_area = st.selectbox("Area", ["All"] + sorted(df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]: sel_rev = st.selectbox("Revision", ["All"] + sorted(df['Rev'].unique().tolist()), key=f"rev_{tab_name}")
    with f_cols[4]: sel_stat = st.selectbox("Status", ["All"] + sorted(df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 데이터 필터링 로직
    f_df = df.copy()
    if search:
        f_df = f_df[f_df['DWG. NO.'].str.contains(search, case=False, na=False) | 
                    f_df['Description'].str.contains(search, case=False, na=False)]
    if sel_sys != "All": f_df = f_df[f_df['SYSTEM'] == sel_sys]
    if sel_area != "All": f_df = f_df[f_df['Area'] == sel_area]
    if sel_rev != "All": f_df = f_df[f_df['Rev'] == sel_rev]
    if sel_stat != "All": f_df = f_df[f_df['Status'] == sel_stat]

    # 2. STATISTICS & ACTIONS (중복 체크 메시지 및 버튼 복구)
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    stat_col, action_col = st.columns([7, 3])
    
    with stat_col:
        s_left, s_right = st.columns([2, 5])
        with s_left:
            st.markdown(f"**Total Records: {len(f_df):,}**")
        with s_right:
            # 중복 체크 메시지 (Total Records 우측 배치)
            dup_count = f_df['DWG. NO.'].duplicated().sum()
            if dup_count > 0:
                st.warning(f"⚠️ {dup_count} Duplicates Found", icon=None)
            else:
                st.success("✅ No Duplicates", icon=None)

    with action_col:
        # 버튼 아이콘 및 텍스트 원복
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Upload", key=f"up_{tab_name}")
        with b2: st.button("📄 PDF", key=f"pdf_{tab_name}")
        with b3: st.button("📤 Export", key=f"ex_{tab_name}")
        with b4: st.button("🖨️ Print", key=f"prt_{tab_name}")

    # 3. DATA TABLE (Remark 컬럼 너비 대폭 확대)
    st.dataframe(
        f_df, 
        use_container_width=True, 
        hide_index=True,
        height=800,
        column_config={
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Remark": st.column_config.TextColumn("Remark", width="large"), # 가독성 확보를 위한 너비 설정
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width="small")
        }
    )

def show_doc_control():
    apply_custom_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    # 데이터 로드 (에러 방지를 위한 예외 처리 포함)
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at {DB_PATH}")
        return

    # 엑셀 로드 및 컬럼 전처리
    raw_df = pd.read_excel(DB_PATH)
    master_df = raw_df.rename(columns={
        'DRAWING TITLE': 'Description',
        'DWG. NO.': 'DWG. NO.', # 명시적 매핑
        'Category': 'Category'
    }).fillna('-')

    # 탭 구성 (아이콘 포함)
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    
    with tabs[0]: 
        render_drawing_table(master_df, "Master")
    with tabs[1]: 
        render_drawing_table(master_df[master_df['Category'].str.contains('ISO', case=False)], "ISO")
    with tabs[2]: 
        render_drawing_table(master_df[master_df['Category'].str.contains('Support', case=False)], "Support")
    with tabs[3]: 
        render_drawing_table(master_df[master_df['Category'].str.contains('Valve', case=False)], "Valve")
    with tabs[4]: 
        # Specialty 괄호 누락 버그 수정 완료
        spec_df = master_df[master_df['Category'].str.contains('Specialty|Speciality', case=False)]
        render_drawing_table(spec_df, "Specialty")
