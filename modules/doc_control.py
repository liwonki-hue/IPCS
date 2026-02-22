import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# Configuration
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
    """위젯 높이를 극소화(Ultra-Compact)하여 수직 공간을 최적화합니다."""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        /* 전체 컨테이너 여백 상단 축소 */
        .block-container { padding-top: 1.5rem !important; padding-bottom: 0rem !important; }
        
        .main-title { font-size: 20px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 8px !important; }
        .section-label { font-size: 10px !important; font-weight: 700; color: #6b7a90; margin-top: 4px; margin-bottom: 2px; text-transform: uppercase; }
        
        /* 버튼 높이 추가 축소 (28px -> 24px) */
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 2px !important;
            height: 24px !important; min-height: 24px !important;
            font-size: 10.5px !important; padding: 0px 5px !important;
        }
        
        /* 입력창 및 셀렉트박스 높이 추가 축소 (30px -> 26px) */
        div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            min-height: 26px !important; height: 26px !important; font-size: 11px !important;
        }
        
        /* 레이블 간격 축소 */
        .stSelectbox label, .stTextInput label { font-size: 10px !important; margin-bottom: 0px !important; }
        
        /* 위젯 간 간격(Gap) 축소 */
        [data-testid="stVerticalBlock"] { gap: 0.3rem !important; }
        
        /* 페이지 네비게이터 텍스트 크기 축소 */
        .page-info { font-size: 11px; font-weight: 600; line-height: 24px; }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Upload Master File")
def show_upload_dialog():
    st.write("Drawing Master 파일을 업로드하십시오.")
    uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'])
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
    # --- 1. Revision Filter (높이 축소) ---
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    filter_key = f"sel_rev_{tab_name}"
    if filter_key not in st.session_state: st.session_state[filter_key] = "LATEST"
    
    rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    revs_to_show = rev_list[:7]
    r_cols = st.columns([1] * len(revs_to_show) + [max(1, 14 - len(revs_to_show))])
    for i, rev in enumerate(revs_to_show):
        with r_cols[i]:
            if st.button(f"{rev}", key=f"btn_{tab_name}_{rev}", 
                        type="primary" if st.session_state[filter_key] == rev else "secondary", use_container_width=True):
                st.session_state[filter_key] = rev
                st.rerun()

    # --- 2. Search & Filters (높이 축소) ---
    st.markdown("<div class='section-label'>Search & Filters</div>", unsafe_allow_html=True)
    f_cols = st.columns([4, 2, 2, 2, 10])
    with f_cols[0]: search_term = st.text_input("Search", key=f"search_{tab_name}", label_visibility="collapsed")
    with f_cols[1]: sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}", label_visibility="collapsed")
    with f_cols[2]: sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}", label_visibility="collapsed")
    with f_cols[3]: sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}", label_visibility="collapsed")

    # 필터링 로직
    f_df = display_df.copy()
    if sel_sys != "All": f_df = f_df[f_df['SYSTEM'] == sel_sys]
    if sel_area != "All": f_df = f_df[f_df['Area'] == sel_area]
    if sel_stat != "All": f_df = f_df[f_df['Status'] == sel_stat]
    if st.session_state[filter_key] != "LATEST": f_df = f_df[f_df['Rev'] == st.session_state[filter_key]]
    if search_term:
        f_df = f_df[f_df['DWG. NO.'].str.contains(search_term, case=False, na=False) | f_df['Description'].str.contains(search_term, case=False, na=False)]

    # --- 3. Pagination & Toolbar (한 줄 배치로 높이 최적화) ---
    total_rows = len(f_df)
    total_pages = max(1, math.ceil(total_rows / ITEMS_PER_PAGE))
    page_key = f"page_{tab_name}"
    if page_key not in st.session_state: st.session_state[page_key] = 1
    
    st.markdown("<div style='margin-top:5px;'></div>", unsafe_allow_html=True)
    nav_col, info_col, btn_col = st.columns([3, 3, 6])
    
    with nav_col:
        p1, p2, p3 = st.columns([1, 2, 1])
        with p1: 
            if st.button("«", key=f"prev_{tab_name}", disabled=(st.session_state[page_key] == 1)):
                st.session_state[page_key] -= 1
                st.rerun()
        with p2: st.markdown(f"<div class='page-info'>{st.session_state[page_key]} / {total_pages}</div>", unsafe_allow_html=True)
        with p3: 
            if st.button("»", key=f"next_{tab_name}", disabled=(st.session_state[page_key] == total_pages)):
                st.session_state[page_key] += 1
                st.rerun()
    
    with info_col:
        st.markdown(f"<div class='page-info' style='color:#6b7a90;'>Total {total_rows:,}</div>", unsafe_allow_html=True)

    with btn_col:
        b1, b2, b3, b4 = st.columns(4)
        with b1: 
            if st.button("📁 Upload", key=f"up_{tab_name}"): show_upload_dialog()
        with b2: st.button("📄 PDF", key=f"pdf_{tab_name}")
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                f_df.to_excel(writer, index=False)
            st.download_button("📤 Export", data=export_out.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}")
        with b4: st.button("🖨️ Print", key=f"prt_{tab_name}")

    # 데이터 슬라이싱 및 출력
    start_idx = (st.session_state[page_key] - 1) * ITEMS_PER_PAGE
    paged_df = f_df.iloc[start_idx : start_idx + ITEMS_PER_PAGE]
    st.dataframe(paged_df, use_container_width=True, hide_index=True, height=1050)

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database missing.")
        return

    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    p_data = [{
        "Category": row.get('Category', '-'), 
        "Area": row.get('Area', row.get('AREA', '-')), 
        "SYSTEM": row.get('SYSTEM', '-'),
        "DWG. NO.": row.get('DWG. NO.', '-'), 
        "Description": row.get('DRAWING TITLE', '-'),
        "Rev": get_latest_rev_info(row)[0], 
        "Date": get_latest_rev_info(row)[1], 
        "Hold": row.get('HOLD Y/N', 'N'),
        "Status": row.get('Status', '-'), 
        "Remark": get_latest_rev_info(row)[2]
    } for _, row in df_raw.iterrows()]
    master_df = pd.DataFrame(p_data)

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    for i, tab in enumerate(tabs):
        with tab:
            if i == 0: render_drawing_table(master_df, "Master")
            else:
                cat_map = ["ISO", "Support", "Valve", "Specialty"]
                render_drawing_table(master_df[master_df['Category'].str.contains(cat_map[i-1], case=False, na=False)], cat_map[i-1])
