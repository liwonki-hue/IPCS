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

# --- 2. PDF 출력 엔진 (A4 Landscape) ---
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

    # Title 적용 (Sub-caption 없이 단독 배치)
    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.info("No data found. Please upload drawing list.")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # 1. REVISION FILTER (녹색 버튼 적용)
            st.markdown('<div class="section-label">Revision Filter</div>', unsafe_allow_html=True)
            rev_opts = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            
            sel_rev_key = f"rev_v10_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns(len(rev_opts[:7]) + 1)
            for idx, r_val in enumerate(rev_opts[:7]):
                count = len(curr_df) if r_val == "LATEST" else len(curr_df[curr_df['Rev'] == r_val])
                if r_cols[idx].button(f"{r_val} ({count})", key=f"btn_v10_{i}_{idx}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.rerun()

            # 필터링 로직 (SyntaxError 수정 완료)
            df_filt = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": 
                df_filt = df_filt[df_filt['Rev'] == st.session_state[sel_rev_key]]
            
            # 2. SEARCH & FILTERS (4단 레이아웃 복구)
            st.markdown('<div class="section-label">Search & Filters</div>', unsafe_allow_html=True)
            s_col1, s_col2, s_col3, s_col4 = st.columns([4, 2, 2, 2])
            q = s_col1.text_input("DWG No. or Description", key=f"q_v10_{i}", label_visibility="collapsed", placeholder="Search...")
            s_col2.selectbox("All Systems", ["All Systems"], key=f"sys_v10_{i}", label_visibility="collapsed")
            s_col3.selectbox("All Areas", ["All Areas"], key=f"area_v10_{i}", label_visibility="collapsed")
            s_col4.selectbox("All Status", ["All Status"], key=f"stat_v10_{i}", label_visibility="collapsed")
            
            if q: 
                df_filt = df_filt[df_filt['DWG. NO.'].str.contains(q, case=False) | df_filt['Description'].str.contains(q, case=False)]
            
            # 3. ACTION TOOLBAR (4버튼 구성 및 PDF 인쇄 적용)
            st.write("")
            b_cols = st.columns([6, 1, 1, 1, 1])
            with b_cols[1]: st.button("📁 Upload", key=f"up_v10_{i}", use_container_width=True)
            with b_cols[2]: st.button("📄 PDF Sync", key=f"sync_v10_{i}", use_container_width=True)
            
            # Export
            ex_io = BytesIO()
            df_filt.to_excel(ex_io, index=False)
            b_cols[3].download_button("📤 Export", data=ex_io.getvalue(), file_name=f"{tab_names[i]}.xlsx", key=f"ex_v10_{i}", use_container_width=True)
            
            # Print (PDF 생성 및 다운로드 방식)
            pdf_bytes = generate_pdf_report(df_filt, f"Document Control List - {tab_names[i]}")
            b_cols[4].download_button("🖨️ Print", data=pdf_bytes, file_name=f"Print_{tab_names[i]}.pdf", mime="application/pdf", key=f"prt_v10_{i}", use_container_width=True)

            # 4. DATA TABLE (30행 제한)
            pg_key = f"pg_v10_{i}"
            if pg_key not in st.session_state: st.session_state[pg_key] = 1
            total_pages = max(1, math.ceil(len(df_filt) / ROWS_PER_PAGE))
            
            start_idx = (st.session_state[pg_key] - 1) * ROWS_PER_PAGE
            st.dataframe(df_filt.iloc[start_idx : start_idx + ROWS_PER_PAGE], use_container_width=True, hide_index=True, height=750)

            # Pagination
            if total_pages > 1:
                p_left, p_mid, p_right = st.columns([9, 0.5, 0.5])
                if p_mid.button("◀", key=f"prev_v10_{i}"):
                    st.session_state[pg_key] = max(1, st.session_state[pg_key]-1); st.rerun()
                if p_right.button("▶", key=f"next_v10_{i}"):
                    st.session_state[pg_key] = min(total_pages, st.session_state[pg_key]+1); st.rerun()

if __name__ == "__main__":
    main()
