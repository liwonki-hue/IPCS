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
            "Status": row.get('Status', '-')
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

# --- 2. PDF 출력 엔진 (A4 가로 모드) ---
def generate_pdf_report(df, title):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, title, ln=True, align='L')
    pdf.ln(5)
    
    # Header
    pdf.set_font("Arial", 'B', 8)
    cols = ["Category", "Area", "SYSTEM", "DWG. NO.", "Description", "Rev", "Date", "Status"]
    widths = [20, 20, 30, 45, 90, 15, 25, 25]
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 8, col, border=1, align='C')
    pdf.ln()
    
    # Body
    pdf.set_font("Arial", '', 7)
    for _, row in df.iterrows():
        for i, col in enumerate(cols):
            pdf.cell(widths[i], 7, str(row.get(col, '-'))[:50], border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. UI 렌더링 ---
def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # CSS: 타이틀 위치 고정 및 선택 버튼 녹색 지정
    st.markdown("""
        <style>
        .block-container { padding-top: 6rem !important; }
        .main-title { 
            font-size: 34px; font-weight: 850; color: #1A4D94; 
            margin-bottom: 2.5rem; border-left: 10px solid #1A4D94; padding-left: 20px; 
        }
        /* 선택된 리비전 버튼을 녹색으로 변경 */
        div[data-testid="stButton"] button[kind="primary"] {
            background-color: #28a745 !important;
            border-color: #28a745 !important;
            color: white !important;
        }
        .section-label { font-size: 12px; font-weight: 700; color: #444; margin: 15px 0 8px 0; text-transform: uppercase; }
        </style>
    """, unsafe_allow_html=True)

    # Title 적용
    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.info("No data found. Please upload drawing list.")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(
