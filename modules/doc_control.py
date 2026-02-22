import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Configuration
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    for r, d, m in [('3rd REV', '3rd DATE', '3rd REMARK'), 
                    ('2nd REV', '2nd DATE', '2nd REMARK'), 
                    ('1st REV', '1st DATE', '1st REMARK')]:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            rem = row.get(m, "")
            rem = "" if pd.isna(rem) or str(rem).lower() == "none" else str(rem)
            return val, row.get(d, '-'), rem
    return '-', '-', ''

def apply_professional_style():
    """위젯의 크기와 높이를 1단계 축소하고, UI 붕괴를 막기 위한 간소화된 CSS를 적용합니다."""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 2.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        
        /* 메인 타이틀 고정 */
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 15px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 8px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase; }
        
        /* 1단계 작게: 버튼 (Revision, Toolbar 공통) */
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 4px !important; border: 1px solid #dde3ec !important;
            height: 28px !important; min-height: 28px !important; 
            font-size: 11px !important; font-weight: 600 !important;
            padding: 0px 8px !important; line-height: 1 !important;
        }
        div.stButton > button[kind="primary"] { background-color: #1657d0 !important; color: white !important; }
        
        /* 1단계 작게: Search 및 Selectbox (높이 및 텍스트) */
        div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            min-height: 30px !important; height: 30px !important; font-size: 12px !important;
        }
        .stSelectbox label, .stTextInput label { font-size: 11px !important; margin-bottom: 2px !important; font-weight: 700 !important; }
        
        /* 표 내부 가독성 */
        div[data-testid="stDataFrame"] [role="gridcell"] { white-space: normal !important; word-wrap: break-word !important; line-height: 1.3 !important; }
        div[data-testid="stDataFrame"] [role="gridcell"] div { font-size: 13px !important; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(display_df, tab_name):
    """단일 계층 컬럼 구조를 사용하여 왼쪽 1/2 정렬 및 레이아웃을 구성합니다."""
    
    # -----------------------------------------------------------------
    # 1. Revision Filter (가상 분할을 통해 왼쪽 절반만 차지하도록 강제)
    # -----------------------------------------------------------------
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    filter_key = f"sel_rev_{tab_name}"
    if filter_key not in st.session_state: st.session_state[filter_key] = "LATEST"
    
    rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    revs_to_show = rev_list[:7]
    
    # 버튼 개수만큼 1의 비율을 주고, 나머지 빈 공간(오른쪽)에 큰 비율을 할당 (중첩 컬럼 방지)
    r_cols = st.columns([1] * len(revs_to_show) + [max(1, 14 - len(revs_to_show))])
    
    for i, rev in enumerate(revs_to_show):
        count = len(display_df) if rev == "LATEST" else display_df['Rev'].value_counts().get(rev, 0)
        with r_cols[i]:
            if st.button(f"{rev}\n({count})", key=f"btn_{tab_name}_{rev}", type="primary" if st.session_state[filter_key] == rev else "secondary", use_container_width=True):
                st.session_state[filter_key] = rev
                st.rerun()

    # -----------------------------------------------------------------
    # 2. Search & Data Filters (Search 왼쪽에 배치, 전체는 화면 왼쪽 절반)
    # -----------------------------------------------------------------
    st.markdown("<div class='section-label'>Search & Filters</div>", unsafe_allow_html=True)
    
    # 비율: Search(4) | System(2) | Area(2) | Status(2) | Empty Space(10)
    # 합산 20 기준, 필터 영역이 정확히 왼쪽 1/2(10/20)을 차지하고, Search가 가장 넓은 비율을 갖습니다.
    f_cols = st.columns([4, 2, 2, 2, 10])
    
    with f_cols[0]:
        search_term = st.text_input("Search", key=f"search_{tab_name}", placeholder="DWG No. or Title...")
    with f_cols[1]:
        sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]:
        sel_area = st.selectbox("Area/Cat", ["All"] + sorted(display_df['Category'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]:
        sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # --- Filtering Logic ---
    filtered_df = display_df.copy()
    if sel_sys != "All": filtered_df = filtered_df[filtered_df['SYSTEM'] == sel_sys]
    if sel_area != "All": filtered_df = filtered_df[filtered_df['Category'] == sel_area]
    if sel_stat != "All": filtered_df = filtered_df[filtered_df['Status'] == sel_stat]
    if st.session_state[filter_key] != "LATEST": filtered_df = filtered_df[filtered_df['Rev'] == st.session_state[filter_key]]
    if search_term:
        filtered_df = filtered_df[filtered_df['DWG. NO.'].str.contains(search_term, case=False, na=False) | 
                                  filtered_df['Description'].str.contains(search_term, case=False, na=False)]

    # -----------------------------------------------------------------
    # 3. Action Toolbar (중첩 없이 단일 배열로 재구성)
    # -----------------------------------------------------------------
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    
    # 비율: Info(3) | 빈공간(5) | Upload(1) | PDF(1) | Export(1) | Print(1)
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    
    with t_cols[0]:
        st.markdown(f"<span style='font-size:13px; font-weight:700;'>Total: {len(filtered_df):,} records</span>", unsafe_allow_html=True)
    with t_cols[2]: st.button("📁 Upload", key=f"up_{tab_name}", use_container_width=True)
    with t_cols[3]: st.button("📄 PDF", key=f"pdf_{tab_name}", use_container_width=True)
    with t_cols[4]:
        export_out = BytesIO()
        with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False)
        st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
    with t_cols[5]: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # -----------------------------------------------------------------
    # 4. Data Viewport
    # -----------------------------------------------------------------
    st.dataframe(
        filtered_df, use_container_width=True, hide_index=True, height=580,
        column_config={
            "Category": st.column_config.TextColumn("Category", width=70),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=70),
            "Hold": st.column_config.TextColumn("Hold", width=50),
            "Status": st.column_config.TextColumn("Status", width=70),
            "Rev": st.column_config.TextColumn("Rev", width=60),
            "Date": st.column_config.TextColumn("Date", width=90),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Remark": st.column_config.TextColumn("Remark", width="medium")
        }
    )

def show_doc_control():
    # CSS 적용
    apply_professional_style()
    
    # 타이틀 고정 위치
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database file missing.")
        return

    # 데이터 로드
    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date, "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'), "Remark": l_rem
        })
    master_df = pd.DataFrame(p_data)

    # 탭 네비게이터가 타이틀 바로 아래에 정상 생성됨
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    
    with tabs[0]: render_drawing_table(master_df, "Master")
    with tabs[1]: render_drawing_table(master_df[master_df['Category'].str.contains('ISO', case=False, na=False)], "ISO")
    with tabs[2]: render_drawing_table(master_df[master_df['Category'].str.contains('Support', case=False, na=False)], "Support")
    with tabs[3]: render_drawing_table(master_df[master_df['Category'].str.contains('Valve', case=False, na=False)], "Valve")
    with tabs[4]: render_drawing_table(master_df[master_df['Category'].str.contains('Specialty|Speciality', case=False, na=False)], "Specialty")
