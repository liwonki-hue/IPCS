import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO
from fpdf import FPDF

# --- 1. 데이터 처리 엔진 ---
DB_PATH = 'data/drawing_master.xlsx'
ROWS_PER_PAGE = 30

def get_latest_rev_info(row):
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def process_raw_df(df_raw):
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), 
            "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', row.get('Description', '-')),
            "Rev": l_rev, "Date": l_date, "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'),
            "Link": row.get('Link', None)
        })
    return pd.DataFrame(p_data)

@st.cache_data
def load_data():
    if os.path.exists(DB_PATH):
        try:
            df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            return process_raw_df(df_raw)
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- 2. PDF 생성 엔진 (A4 가로 규격) ---
def create_pdf_report(df, title):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, title, ln=True, align='L')
    pdf.ln(5)
    
    # 헤더 설정
    pdf.set_font("Arial", 'B', 8)
    cols = ["Category", "Area", "SYSTEM", "DWG. NO.", "Description", "Rev", "Date", "Status"]
    col_widths = [20, 18, 25, 45, 95, 12, 22, 20]
    
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 8, col, border=1, align='C')
    pdf.ln()
    
    # 데이터 행 추가
    pdf.set_font("Arial", '', 7)
    for _, row in df.iterrows():
        for i, col in enumerate(cols):
            text = str(row.get(col, '-'))
            pdf.cell(col_widths[i], 7, text[:55], border=1) 
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. UI 렌더링 ---
def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # CSS: 타이틀 위치 유지 및 서브 캡션 제거 스타일
    st.markdown("""
        <style>
        .block-container { padding-top: 6rem !important; }
        .main-title { 
            font-size: 36px; font-weight: 900; color: #1A4D94; 
            margin-bottom: 2rem; border-left: 10px solid #1A4D94; padding-left: 20px; 
        }
        .section-label { font-size: 13px; font-weight: 700; color: #444; margin: 15px 0 5px 0; }
        div[data-testid="stButton"] button[kind="primary"] { background-color: #28a745 !important; }
        </style>
    """, unsafe_allow_html=True)

    # 1. Title (현재 위치 유지)
    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.warning("Data file not found.")
        return

    # Tabs
    tab_titles = ["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"]
    tabs = st.tabs(tab_titles)

    for i, tab in enumerate(tabs):
        with tab:
            tab_name = tab_titles[i].split(" ")[1]
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_name, case=False, na=False)]
            
            # 2. REVISION FILTER (원래 레이아웃 복구)
            st.markdown('<div class="section-label">REVISION FILTER</div>', unsafe_allow_html=True)
            rev_opts = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            
            sel_rev_key = f"rev_v7_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns(len(rev_opts[:8]) + 1)
            for idx, r_val in enumerate(rev_opts[:8]):
                count = len(curr_df) if r_val == "LATEST" else len(curr_df[curr_df['Rev'] == r_val])
                if r_cols[idx].button(f"{r_val} ({count})", key=f"btn_v7_{i}_{idx}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.rerun()

            # 필터링 로직
            df_filt = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": 
                df_filt =
