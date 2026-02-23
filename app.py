import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO
from fpdf import FPDF

# --- [1] Data Processing Layer ---
DB_PATH = 'data/drawing_master.xlsx'
ROWS_PER_PAGE = 30

def get_latest_rev_info(row):
    """추출 로직: 3rd -> 2nd -> 1st 순으로 유효한 리비전 데이터 탐색"""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def process_raw_df(df_raw):
    """DataFrame 정규화: 컬럼명 매핑 및 도면 링크 데이터 처리"""
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), 
            "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', row.get('Description', '-')),
            "Rev": l_rev, 
            "Date": l_date, 
            "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'),
            "Drawing": row.get('Drawing', row.get('DRAWING', row.get('Link', None)))
        })
    return pd.DataFrame(p_data)

@st.cache_data
def load_data():
    """파일 I/O 최적화: 엑셀 데이터를 로드하고 메모리에 캐싱"""
    if os.path.exists(DB_PATH):
        try:
            df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            return process_raw_df(df_raw)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# --- [2] PDF Generation Engine ---
def generate_pdf_report(df, title):
    """PDF 출력: A4 가로(Landscape) 규격의 기술 보고서 생성"""
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
            val = str(row.get(col, '-'))[:50]
            pdf.cell(widths[i], 7, val, border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- [3] Presentation Layer (UI) ---
def main():
    st.set_page_config(layout="wide", page_title="DCS Dashboard")
    
    # CSS Injection: UI 일관성 유지
    st.markdown("""
        <style>
        .main-title { font-size: 32px; font-weight: 850; color: #1A4D94; border-left: 10px solid #1A4D94; padding-left: 20px; margin-bottom: 25px; }
        .stButton button[kind="primary"] { background-color: #28a745 !important; border-color: #28a745 !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.error("Data integrity error: 'data/drawing_master.xlsx' 파일을 확인하십시오.")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            # 1. 탭별 Category 필터링
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # 2. Revision Filter Section
            st.markdown("### Revision Selection")
            rev_opts = ["LATEST"] + sorted([str(r) for r in curr_df['Rev'].unique() if pd.notna(r) and str(r).strip() != "-"])
            
            sel_rev_key = f"rev_v_f_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns(len(rev_opts[:7]) + 1)
            for idx, r_val in enumerate(rev_opts[:7]):
                if r_cols[idx].button(f"{r_val}", key=f"btn_f_{i}_{idx}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.rerun()

            df_filt = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": 
                df_filt = df_filt[df_filt['Rev'] == st.session_state[sel_rev_key]]
            
            # 3. Search & Cross-Filters Section
            st.markdown("---")
            # 동적 고유값 추출 로직 (필터 리스트 복구의 핵심)
            sys_list = ["All Systems"] + sorted([str(x) for x in curr_df['SYSTEM'].unique() if pd.notna(x) and str(x).strip() not in ('', '-')])
            area_list = ["All Areas"] + sorted([str(x) for x in curr_df['Area'].unique() if pd.notna(x) and str(x).strip() not in ('', '-')])
            stat_list = ["All Status"] + sorted([str(x) for x in curr_df['Status'].unique() if pd.notna(x) and str(x).strip() not in ('', '-')])
            
            s_col1, s_col2, s_col3, s_col4 = st.columns([4, 2, 2, 2])
            q = s_col1.text_input("DWG No. / Description", key=f"q_f_{i}", placeholder="검색어 입력...", label_visibility="collapsed")
            sel_sys = s_col2.selectbox("System", sys_list, key=f"sys_f_{i}", label_visibility="collapsed")
            sel_area = s_col3.selectbox("Area", area_list, key=f"area_f_{i}", label_visibility="collapsed")
            sel_stat = s_col4.selectbox("Status", stat_list, key=f"stat_f_{i}", label_visibility="collapsed")
            
            # 다중 조건 필터링 파이프라인
            if q: 
                df_filt = df_filt[df_filt['DWG. NO.'].str.contains(q, case=False, na=False) | df_filt['Description'].str.contains(q, case=False, na=False)]
            if sel_sys != "All Systems": df_filt = df_filt[df_filt['SYSTEM'] == sel_sys]
            if sel_area != "All Areas": df_filt = df_filt[df_filt['Area'] == sel_area]
            if sel_stat != "All Status": df_filt = df_filt[df_filt['Status'] == sel_stat]
            
            # 4. Action Toolbar & Data Display
            st.write(f"**Filtered Results: {len(df_filt):,}**")
            b_cols = st.columns([6, 1, 1, 1, 1])
            
            with b_cols[3]:
                ex_io = BytesIO()
                df_filt.to_excel(ex_io, index=False)
                st.download_button("📤 Export", data=ex_io.getvalue(), file_name=f"{tab_names[i]}_list.xlsx", key=f"ex_f_{i}", use_container_width=True)
            with b_cols[4]:
                pdf_bytes = generate_pdf_report(df_filt, f"Technical Drawing List - {tab_names[i]}")
                st.download_button("🖨️ Print", data=pdf_bytes, file_name=f"Report_{tab_names[i]}.pdf", mime="application/pdf", key=f"prt_f_{i}", use_container_width=True)

            # Data Table: LinkColumn 기반의 View 아이콘 구현
            st.dataframe(
                df_filt, 
                use_container_width=True, 
                hide_index=True, 
                height=600,
                column_config={
                    "Drawing": st.column_config.LinkColumn(
                        "View",
                        help="도면 파일을 확인하려면 클릭하십시오.",
                        display_text="🔍 View" 
                    )
                }
            )

if __name__ == "__main__":
    main()
