import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# --- Configuration ---
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
        .block-container { padding-top: 1.5rem !important; max-width: 98% !important; }
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0; margin-bottom: 15px; }
        .section-label { font-size: 11px; font-weight: 700; color: #6b7a90; margin-bottom: 8px; text-transform: uppercase; }
        div.stButton > button { height: 35px !important; font-size: 14px !important; }
        .page-info { font-size: 14px; font-weight: 700; text-align: center; color: #1657d0; line-height: 35px; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(display_df, tab_name):
    # --- 1. SEARCH & MULTI-FILTERS (기존 구조) ---
    st.markdown("<div class='section-label'>Search & Multi-Filters</div>", unsafe_allow_html=True)
    f_cols = st.columns([3, 2, 2, 2, 2])
    with f_cols[0]: search_term = st.text_input("Search", key=f"search_{tab_name}", placeholder="No. or Title...")
    with f_cols[1]: sel_sys = st.selectbox("System", ["All"] + sorted(display_df['SYSTEM'].unique().tolist()), key=f"sys_{tab_name}")
    with f_cols[2]: sel_area = st.selectbox("Area", ["All"] + sorted(display_df['Area'].unique().tolist()), key=f"area_{tab_name}")
    with f_cols[3]: sel_rev = st.selectbox("Revision", ["All"] + sorted(display_df['Rev'].unique().tolist()), key=f"rev_{tab_name}")
    with f_cols[4]: sel_stat = st.selectbox("Status", ["All"] + sorted(display_df['Status'].unique().tolist()), key=f"stat_{tab_name}")

    f_df = display_df.copy()
    if sel_sys != "All": f_df = f_df[f_df['SYSTEM'] == sel_sys]
    if sel_area != "All": f_df = f_df[f_df['Area'] == sel_area]
    if sel_rev != "All": f_df = f_df[f_df['Rev'] == sel_rev]
    if sel_stat != "All": f_df = f_df[f_df['Status'] == sel_stat]
    if search_term:
        f_df = f_df[f_df['DWG. NO.'].astype(str).str.contains(search_term, case=False, na=False) | 
                    f_df['Description'].astype(str).str.contains(search_term, case=False, na=False)]

    # --- 2. STATISTICS & DUPLICATE CHECK (image_4b31a5 복구) ---
    st.write("") # 간격 조절
    top_col1, top_col2 = st.columns([7, 3])
    
    with top_col1:
        stat_cols = st.columns([2, 5])
        with stat_cols[0]:
            st.markdown(f"**Total Records: {len(f_df):,}**")
        with stat_cols[1]:
            # 중복 검사 메시지 창 위치 및 스타일 복구
            dup_count = f_df['DWG. NO.'].duplicated().sum()
            if dup_count > 0:
                st.warning(f"⚠️ {dup_count} Duplicates Found")
            else:
                st.success("✅ No Duplicates")

    with top_col2:
        # 버튼 아이콘 및 텍스트 복구
        b_cols = st.columns(4)
        with b_cols[0]: st.button("📁 Upload", key=f"up_{tab_name}")
        with b_cols[1]: st.button("📄 PDF", key=f"pdf_{tab_name}")
        with b_cols[2]:
            buf = BytesIO()
            with pd.ExcelWriter(buf) as writer: f_df.to_excel(writer, index=False)
            st.download_button("📤 Export", data=buf.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}")
        with b_cols[3]: st.button("🖨️ Print", key=f"prt_{tab_name}")

    # --- 3. DATA TABLE (Remark 컬럼 너비 확보) ---
    total_pages = max(1, math.ceil(len(f_df) / ITEMS_PER_PAGE))
    page_key = f"page_{tab_name}"
    if page_key not in st.session_state: st.session
