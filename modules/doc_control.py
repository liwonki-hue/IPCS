import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# Configuration
DB_PATH = 'data/drawing_master.xlsx'
ITEMS_PER_PAGE = 30  # 페이지당 출력 행 수 고정

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
        .block-container { padding-top: 2.5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 15px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 8px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 10px; margin-bottom: 4px; text-transform: uppercase; }
        
        /* 버튼 및 입력창 1단계 축소 */
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 4px !important; border: 1px solid #dde3ec !important;
            height: 28px !important; font-size: 11px !important; font-weight: 600 !important;
            padding: 0px 8px !important; line-height: 1 !important;
        }
        div.stButton > button[kind="primary"] { background-color: #1657d0 !important; color: white !important; }
        div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            min-height: 30px !important; height: 30px !important; font-size: 12px !important;
        }
        
        /* 페이지 네비게이터 전용 스타일 */
        .page-info { font-size: 12px; font-weight: 600; text-align: center; line-height: 28px; }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Upload Master File")
def show_upload_dialog():
    st.write("새로운 Drawing Master 파일을 업로드하십시오.")
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
    # --- 1. Revision Filter ---
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

    # --- 2. Search & Filters ---
    st.markdown("<div class='section-label'>Search & Filters</div>", unsafe_allow_html=True)
    f_cols = st.columns([4, 2, 2, 2, 10])
    with f_cols[0]: search_term = st.text_input("Search", key=f"search_{tab_name}")
    with f_cols[1]: sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]: sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]: sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    # 필터링 로직
    f_df = display_df.copy()
    if sel_sys != "All": f_df = f_df[f_df['SYSTEM'] == sel_sys]
    if sel_area != "All": f_df = f_df[f_df['Area'] == sel_area]
    if sel_stat != "All": f_df = f_df[f_df['Status'] == sel_stat]
    if st.session_state[filter_key] != "LATEST": f_df = f_df[f_df['Rev'] == st.session_state[filter_key]]
    if search_term:
        f_df = f_df[f_df['DWG. NO.'].str.contains(search_term, case=False, na=False) | f_df['Description'].str.contains(search_term, case=False, na=False)]

    # --- 3. Pagination Control (페이지 네비게이터 추가) ---
    total_rows = len(f_df)
    total_pages = max(1, math.ceil(total_rows / ITEMS_PER_PAGE))
    
    page_key = f"page_{tab_name}"
    if page_key not in st.session_state: st.session_state[page_key] = 1
    
    # 페이지 범위 초과 방지
    if st.session_state[page_key] > total_pages: st.session_state[page_key] = total_pages

    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    nav_col, _, btn_col = st.columns([4, 4, 4])
    
    with nav_col:
        p1, p2, p3, p4 = st.columns([1, 2, 2, 1])
        with p1: 
            if st.button("«", key=f"prev_{tab_name}", disabled=(st.session_state[page_key] == 1)):
                st.session_state[page_key] -= 1
                st.rerun()
        with p2:
            st.markdown(f"<div class='page-info'>Page {st.session_state[page_key]} of {total_pages}</div>", unsafe_allow_html=True)
        with p3:
            st.markdown(f"<div class='page-info' style='color:#6b7a90;'>(Total {total_rows:,})</div>", unsafe_allow_html=True)
        with p4:
            if st.button("»", key=f"next_{tab_name}", disabled=(st.session_state[page_key] == total_pages)):
                st.session_state[page_key] += 1
                st.rerun()

    # --- 4. Action Toolbar ---
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

    # 데이터 슬라이싱 (30줄 고정)
    start_idx = (st.session_state[page_key] - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    paged_df = f_df.iloc[start_idx:end_idx]

    # --- 5. Data Viewport ---
    st.dataframe(paged_df, use_container_width=True, hide_index=True, height=1050) # 30줄 출력을 위해 높이 조정

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database missing.")
        return

    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
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
    with tabs[0]: render_drawing_table(master_df, "Master")
    with tabs[1]: render_drawing_table(master_df[master_df['Category'].str.contains('ISO', case=False, na=False)], "ISO")
    with tabs[2]: render_drawing_table(master_df[master_df['Category'].str.contains('Support', case=False, na=False)], "Support")
    with tabs[3]: render_drawing_table(master_df[master_df['Category'].str.contains('Valve', case=False, na=False)], "Valve")
    with tabs[4]: render_drawing_table(master_df[master_df['Category'].str.contains('Specialty|Speciality', case=False, na=False)], "Specialty")
