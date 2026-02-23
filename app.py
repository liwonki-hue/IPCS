import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO
from fpdf import FPDF

# --- 1. 데이터 처리 로직 ---
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

# --- 2. PDF 생성 함수 (인쇄 기능 대체) ---
def create_pdf(df, title):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(5)
    
    # 헤더 설정
    pdf.set_font("Arial", 'B', 8)
    cols = ["Category", "Area", "SYSTEM", "DWG. NO.", "Description", "Rev", "Date", "Status"]
    col_widths = [20, 20, 30, 50, 80, 15, 25, 25]
    
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 8, col, border=1, align='C')
    pdf.ln()
    
    # 데이터 행 추가
    pdf.set_font("Arial", '', 7)
    for _, row in df.iterrows():
        for i, col in enumerate(cols):
            text = str(row.get(col, '-'))
            pdf.cell(col_widths[i], 7, text[:45], border=1) # 텍스트 오버플로 방지
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 3. 메인 인터페이스 ---
def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # CSS: 서브 캡션 제거 및 타이틀 위치 강제 조정
    st.markdown("""
        <style>
        /* 화면 상단 여백 확보 */
        .block-container { 
            padding-top: 6rem !important; 
            max-width: 95%;
        }
        /* 타이틀 스타일: 서브 캡션 없이 단독 배치 */
        .main-title { 
            font-size: 38px; 
            font-weight: 900; 
            color: #1A4D94; 
            margin-bottom: 40px; 
            border-left: 10px solid #1A4D94;
            padding-left: 20px;
        }
        /* 버튼 스타일 */
        div[data-testid="stButton"] button { border-radius: 4px; }
        div[data-testid="stButton"] button[kind="primary"] { background-color: #28a745 !important; }
        </style>
    """, unsafe_allow_html=True)

    # 1. Title 적용 (Sub-caption 제거 및 위치 조정)
    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.error("데이터 파일이 없거나 형식이 잘못되었습니다.")
        return

    tab_titles = ["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"]
    tabs = st.tabs(tab_titles)

    for i, tab in enumerate(tabs):
        with tab:
            tab_name = tab_titles[i].split(" ")[1]
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_name, case=False, na=False)]
            
            # Revision Filter
            rev_opts = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            sel_rev_key = f"rev_v6_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns([1.2]*len(rev_opts[:8]) + [1])
            for idx, r_val in enumerate(rev_opts[:8]):
                count = len(curr_df) if r_val == "LATEST" else len(curr_df[curr_df['Rev'] == r_val])
                if r_cols[idx].button(f"{r_val} ({count})", key=f"btn_v6_{i}_{idx}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.rerun()

            # 필터링 및 검색
            df_filt = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": 
                df_filt = df_filt[df_filt['Rev'] == st.session_state[sel_rev_key]]
            
            st.write("---")
            q_col, a_col_pdf, a_col_excel = st.columns([7, 1.5, 1.5])
            q = q_col.text_input("Search", placeholder="DWG No. or Description", key=f"q_v6_{i}", label_visibility="collapsed")
            if q: 
                df_filt = df_filt[df_filt['DWG. NO.'].str.contains(q, case=False) | df_filt['Description'].str.contains(q, case=False)]
            
            # 2. PDF 출력 기능 (Download Button으로 구현)
            pdf_data = create_pdf(df_filt, f"Document Control List - {tab_name}")
            a_col_pdf.download_button(
                label="🖨️ Print to PDF",
                data=pdf_data,
                file_name=f"{tab_name}_List.pdf",
                mime="application/pdf",
                key=f"pdf_v6_{i}",
                use_container_width=True
            )
            
            exp_io = BytesIO()
            df_filt.to_excel(exp_io, index=False)
            a_col_excel.download_button("📤 Export Excel", data=exp_io.getvalue(), file_name=f"{tab_name}.xlsx", key=f"ex_v6_{i}", use_container_width=True)

            # 3. 30행 페이지네이션
            total_rows = len(df_filt)
            total_pages = max(1, math.ceil(total_rows / ROWS_PER_PAGE))
            pg_key = f"pg_v6_{i}"
            if pg_key not in st.session_state: st.session_state[pg_key] = 1
            
            start_idx = (st.session_state[pg_key] - 1) * ROWS_PER_PAGE
            st.dataframe(df_filt.iloc[start_idx : start_idx + ROWS_PER_PAGE], use_container_width=True, hide_index=True, height=750)

            # 페이지 네비게이터
            if total_pages > 1:
                p_left, p_mid, p_right = st.columns([9, 0.5, 0.5])
                if p_mid.button("◀", key=f"prev_v6_{i}"):
                    st.session_state[pg_key] = max(1, st.session_state[pg_key]-1)
                    st.rerun()
                if p_right.button("▶", key=f"next_v6_{i}"):
                    st.session_state[pg_key] = min(total_pages, st.session_state[pg_key]+1)
                    st.rerun()
                st.info(f"Page {st.session_state[pg_key]} of {total_pages} (Total {total_rows} records)")

if __name__ == "__main__":
    main()
