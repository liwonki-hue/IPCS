import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Configuration
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """최신 리비전 정보를 논리적으로 추출합니다."""
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
    """Compact UI 및 전문적인 엔지니어링 툴 스타일 적용"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 1.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .main-title { font-size: 22px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 15px !important; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 8px; text-transform: uppercase; }
        
        /* 위젯 및 버튼 스타일 최적화 */
        div.stButton > button {
            border-radius: 4px !important; 
            height: 32px !important; font-size: 13px !important; font-weight: 600 !important;
            padding: 0px 12px !important;
        }
        div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            min-height: 32px !important; height: 32px !important; font-size: 13px !important;
        }
        /* 알림창 간격 조정 */
        .stAlert { padding: 8px 16px !important; min-height: 32px !important; }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Upload Master File")
def show_upload_dialog():
    """업로드 팝업 인터페이스"""
    st.write("새로운 Drawing Master 파일을 업로드하십시오.")
    uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'])
    
    if uploaded_file:
        st.info("파일이 준비되었습니다. 'Apply & Save'를 눌러 확정하십시오.")
        if st.button("Apply & Save", type="primary", use_container_width=True):
            try:
                df_upload = pd.read_excel(uploaded_file, sheet_name='DRAWING LIST')
                df_upload.to_excel(DB_PATH, sheet_name='DRAWING LIST', index=False)
                st.success("데이터가 성공적으로 업데이트되었습니다.")
                st.rerun()
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")

def render_drawing_table(display_df, tab_name):
    # --- 1. SEARCH & FILTERS (Layout 복구) ---
    st.markdown("<div class='section-label'>SEARCH & MULTI-FILTERS</div>", unsafe_allow_html=True)
    f_cols = st.columns([3, 2, 2, 2, 2])
    with f_cols[0]:
        search_term = st.text_input("Search", key=f"s_{tab_name}", placeholder="No. or Title...")
    with f_cols[1]:
        sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]:
        sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]:
        # Revision 필터를 Selectbox로 통합하여 공간 확보
        sel_rev = st.selectbox("Revision", ["All"] + sorted([r for r in display_df['Rev'].unique() if r != "-"]), key=f"rev_{tab_name}")
    with f_cols[4]:
        sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # Filtering Logic
    filtered_df = display_df.copy()
    if sel_sys != "All": filtered_df = filtered_df[filtered_df['SYSTEM'] == sel_sys]
    if sel_area != "All": filtered_df = filtered_df[filtered_df['Area'] == sel_area]
    if sel_rev != "All": filtered_df = filtered_df[filtered_df['Rev'] == sel_rev]
    if sel_stat != "All": filtered_df = filtered_df[filtered_df['Status'] == sel_stat]
    if search_term:
        filtered_df = filtered_df[filtered_df['DWG. NO.'].str.contains(search_term, case=False, na=False) | 
                                  filtered_df['Description'].str.contains(search_term, case=False, na=False)]

    # --- 2. STATISTICS & ACTIONS (중복 체크 알림창 복구) ---
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    stat_col, action_col = st.columns([7, 3])
    
    with stat_col:
        s_left, s_right = st.columns([2, 5])
        with s_left:
            st.markdown(f"<div style='line-height:40px;'><span style='font-size:14px; font-weight:700;'>Total Records: {len(filtered_df):,}</span></div>", unsafe_allow_html=True)
        with s_right:
            # 중복 검사 및 알림창 출력
            dup_count = filtered_df['DWG. NO.'].duplicated().sum()
            if dup_count > 0:
                st.warning(f"⚠️ {dup_count} Duplicates Found", icon=None)
            else:
                st.success("✅ No Duplicates", icon=None)

    with action_col:
        b1, b2, b3, b4 = st.columns(4)
        with b1: 
            if st.button("📁 Upload", key=f"up_{tab_name}"): show_upload_dialog()
        with b2: st.button("📄 PDF", key=f"pdf_{tab_name}")
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False)
            st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}")
        with b4: st.button("🖨️ Print", key=f"prt_{tab_name}")

    # --- 3. DATA VIEWPORT (Remark 컬럼 너비 확장) ---
    st.dataframe(
        filtered_df, use_container_width=True, hide_index=True, height=600,
        column_config={
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Remark": st.column_config.TextColumn("Remark", width="large"), # 비고란 가독성 확보
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width="small"),
            "Rev": st.column_config.TextColumn("Rev", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small")
        }
    )

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database missing. Please contact admin.")
        return

    # 데이터 로딩 및 전처리 (KeyError 방지)
    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": str(row.get('Category', '-')), 
            "Area": str(row.get('Area', row.get('AREA', '-'))), 
            "SYSTEM": str(row.get('SYSTEM', '-')),
            "DWG. NO.": str(row.get('DWG. NO.', '-')), 
            "Description": str(row.get('DRAWING TITLE', '-')),
            "Rev": l_rev, "Date": l_date, "Hold": str(row.get('HOLD Y/N', 'N')),
            "Status": str(row.get('Status', '-')), "Remark": l_rem
        })
    master_df = pd.DataFrame(p_data)

    # 탭 구성
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    with tabs[0]: render_drawing_table(master_df, "Master")
    with tabs[1]: render_drawing_table(master_df[master_df['Category'].str.contains('ISO', case=False, na=False)], "ISO")
    with tabs[2]: render_drawing_table(master_df[master_df['Category'].str.contains('Support', case=False, na=False)], "Support")
    with tabs[3]: render_drawing_table(master_df[master_df['Category'].str.contains('Valve', case=False, na=False)], "Valve")
    with tabs[4]: render_drawing_table(master_df[master_df['Category'].str.contains('Specialty|Speciality', case=False, na=False)], "Specialty")
