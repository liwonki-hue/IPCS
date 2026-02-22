import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

DB_PATH = 'data/drawing_master.xlsx'
ITEMS_PER_PAGE = 30 

def apply_professional_style():
    st.markdown("""
        <style>
        .main-title { font-size: 22px !important; font-weight: 800; color: #1657d0; margin-bottom: 15px; }
        .section-label { font-size: 11px; font-weight: 700; color: #6b7a90; margin-bottom: 10px; text-transform: uppercase; }
        /* 버튼 스타일 조정 */
        div.stButton > button { height: 35px !important; font-size: 13px !important; padding: 0 10px !important; }
        .page-info { font-size: 14px; font-weight: 700; text-align: center; color: #1657d0; line-height: 35px; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(df, tab_name):
    """image_4b31a5.png의 레이아웃을 정확히 복구"""
    if df.empty:
        st.info(f"{tab_name} 데이터가 없습니다.")
        return

    # 1. SEARCH & FILTERS
    st.markdown("<div class='section-label'>SEARCH & MULTI-FILTERS</div>", unsafe_allow_html=True)
    f_cols = st.columns([3, 2, 2, 2, 2])
    with f_cols[0]: search = st.text_input("Search", key=f"s_{tab_name}", placeholder="No. or Title...")
    with f_cols[1]: sys_list = ["All"] + sorted(df['SYSTEM'].unique().tolist())
    sel_sys = f_cols[1].selectbox("System", sys_list, key=f"sys_{tab_name}")
    with f_cols[2]: area_list = ["All"] + sorted(df['Area'].unique().tolist())
    sel_area = f_cols[2].selectbox("Area", area_list, key=f"area_{tab_name}")
    with f_cols[3]: rev_list = ["All"] + sorted(df['Rev'].unique().tolist())
    sel_rev = f_cols[3].selectbox("Revision", rev_list, key=f"rev_{tab_name}")
    with f_cols[4]: stat_list = ["All"] + sorted(df['Status'].unique().tolist())
    sel_stat = f_cols[4].selectbox("Status", stat_list, key=f"stat_{tab_name}")

    # 필터링 적용
    f_df = df.copy()
    if search:
        f_df = f_df[f_df['DWG. NO.'].str.contains(search, case=False, na=False) | 
                    f_df['Description'].str.contains(search, case=False, na=False)]
    if sel_sys != "All": f_df = f_df[f_df['SYSTEM'] == sel_sys]
    if sel_area != "All": f_df = f_df[f_df['Area'] == sel_area]
    if sel_rev != "All": f_df = f_df[f_df['Rev'] == sel_rev]
    if sel_stat != "All": f_df = f_df[f_df['Status'] == sel_stat]

    # 2. STATS & ACTIONS (중복 체크 위치 및 버튼 아이콘 복구)
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    stats_col, actions_col = st.columns([7, 3])
    
    with stats_col:
        s_left, s_right = st.columns([2, 6])
        with s_left:
            st.markdown(f"**Total Records: {len(f_df):,}**")
        with s_right:
            # 중복 체크 메시지 창 위치 (Total Records 옆)
            dup_count = f_df['DWG. NO.'].duplicated().sum()
            if dup_count > 0:
                st.warning(f"⚠️ {dup_count} Duplicates Found", icon=None)
            else:
                st.success("✅ No Duplicates", icon=None)

    with actions_col:
        # 버튼 아이콘 및 텍스트 변경
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Upload", key=f"up_{tab_name}")
        with b2: st.button("📄 PDF", key=f"pdf_{tab_name}")
        with b3: st.button("📤 Export", key=f"ex_{tab_name}")
        with b4: st.button("🖨️ Print", key=f"prt_{tab_name}")

    # 3. DATA TABLE (Remark 컬럼 간격 확대)
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

    if not os.path.exists(DB_PATH):
        st.error("데이터 파일을 찾을 수 없습니다.")
        return

    # 데이터 로드 및 초기화 (KeyError 방지)
    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
    # 필요한 컬럼이 없을 경우를 대비해 기본값 설정 로직 포함
    p_data = []
    for _, row in df_raw.iterrows():
        p_data.append({
            "Category": str(row.get('Category', '-')),
            "Area": str(row.get('Area', '-')),
            "SYSTEM": str(row.get('SYSTEM', '-')),
            "DWG. NO.": str(row.get('DWG. NO.', '-')),
            "Description": str(row.get('DRAWING TITLE', '-')),
            "Rev": str(row.get('Rev', '-')),
            "Status": str(row.get('Status', '-')),
            "Remark": str(row.get('Remark', '-'))
        })
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    with tabs[0]: render_drawing_table(master_df, "Master")
    with tabs[1]: render_drawing_table(master_df[master_df['Category'].str.contains('ISO', case=False, na=False)], "ISO")
    with tabs[2]: render_drawing_table(master_df[master_df['Category'].str.contains('Support', case=False, na=False)], "Support")
    with tabs[3]: render_drawing_table(master_df[master_df['Category'].str.contains('Valve', case=False, na=False)], "Valve")
    with tabs[4]: 
        spec_df = master_df[master_df['Category'].str.contains('Specialty|Speciality', case=False, na=False)]
        render_drawing_table(spec_df, "Specialty")
