import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO
from fpdf import FPDF

# --- 1. Data Processing Engine ---
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
            "Drawing": row.get('Drawing', row.get('DRAWING', row.get('Link', None)))
        })
    return pd.DataFrame(p_data)

@st.cache_data
def load_data():
    if os.path.exists(DB_PATH):
        try:
            df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            return process_raw_df(df_raw)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# --- 2. PDF Export Engine ---
def generate_pdf_report(df, title):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, title, ln=True, align='L')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 8)
    cols = ["Category", "Area", "SYSTEM", "DWG. NO.", "Description", "Rev", "Date", "Status"]
    widths = [20, 20, 30, 45, 90, 15, 25, 25]
    for i, col in enumerate(cols):
        pdf.cell(widths[i], 8, col, border=1, align='C')
    pdf.ln()
    
    pdf.set_font("Arial", '', 7)
    for _, row in df.iterrows():
        for i, col in enumerate(cols):
            pdf.cell(widths[i], 7, str(row.get(col, '-'))[:50], border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. UI Rendering ---
def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # CSS: Style Definitions
    st.
