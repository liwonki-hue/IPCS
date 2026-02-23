import streamlit as st
import pandas as pd
import os
import math
import base64
from io import BytesIO

# --- 1. 환경 설정 및 데이터 처리 ---
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

# --- 2. [강력 해결] 인쇄 기능 (Base64 Iframe 주입 방식) ---
def execute_print_v5(df, title):
    """팝업 차단 설정을 무시하고 현재 창 내에서 인쇄를 실행"""
    table_html = df.drop(columns=['Link'], errors='ignore').to_html(index=False)
    html_content = f"""
    <html><head><meta charset="utf-8"><title>{title}</title><style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
    th, td {{ border: 1px solid #444; padding: 4px; text-align: left; }}
    th {{ background: #eee; font-weight: bold; }}
    </style></head><body><h3>{title}</h3>{table_html}</body></html>
    """
    b64_html = base64.b64encode(html_content.encode('utf-8')).decode()
    
    # iframe 로드 즉시 focus 및 print 호출
    inject_js = f"""
    <iframe id="pdf_print_frame" style="display:none;" src="data:text/html;base64,{b64_html}"></iframe>
    <script>
        const frame = document.getElementById('pdf_print_frame');
        frame.onload = function() {{
            frame.contentWindow.focus();
            frame.contentWindow.print();
        }};
    </script>
    """
    st.components.v1.html(inject_js, height=0)

# --- 3. UI 컴포넌트 ---
@st.dialog("📤 Update Drawing List")
def upload_modal():
    file = st.file_uploader("XLSX 파일 선택", type=["xlsx"], label_visibility="collapsed")
    if file:
        if st.button("Save & Refresh", type="primary", use_container_width=True):
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            with open(DB_PATH, "wb") as f: f.write(file.getbuffer())
            st.cache_data.clear()
            st.success("데이터가 업데이트되었습니다.")
            st.rerun()

# --- 4. 메인 대시보드 ---
def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # CSS: 타이틀 하향 배치 (padding-top: 6rem) 및 스타일 최적화
    st.markdown("""
        <style>
        .block-container { padding-top: 6rem !important; } 
        .main-title { font-size: 34px; font-weight: 850; color: #1A4D94; margin-bottom: 2px; }
        .sub-caption { font-size: 14px; color: #666; margin-bottom: 30px; }
        div[data-testid="stButton"] button[kind="primary"] { background-color: #28a745 !important; border-color: #28a745 !important; }
        .section-label { font-size: 11px; font-weight: 700; color: #444; margin: 15px 0 5px 0; text-transform: uppercase; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>Document Control System</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-caption'>Engineering Document & Drawing Management Dashboard</div>", unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.info("데이터가 없습니다. 파일을 업로드해 주세요.")
        if st.button("📁 Start Upload"): upload_modal()
        return

    tab_list = ["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"]
    tabs = st.tabs(tab_list)

    for i, tab in enumerate(tabs):
        with tab:
            cat_tag = tab_list[i].split(" ")[1]
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(cat_tag, case=False, na=False)]
            
            # 1. Revision Filter
            st.markdown("<p class='section-label'>REVISION FILTER</p>", unsafe_allow_html=True)
            rev_opts = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            
            sel_rev_key = f"active_rev_tab_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns([1.2]*7 + [4.6])
            for idx, r_val in enumerate(rev_opts[:7]):
                count = len(curr_df) if r_val == "LATEST" else len(curr_df[curr_df['Rev'] == r_val])
                if r_cols[idx].button(f"{r_val} ({count})", key=f"rev_tab_{i}_idx_{idx}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.session_state[f"page_idx_{i}"] = 1
                    st.rerun()

            # 2. Search & Toolbar
            st.markdown("<p class='section-label'>ACTIONS & SEARCH</p>", unsafe_allow_html=True)
            df_filt = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": 
                df_filt = df_filt[df_filt['Rev'] == st.session_state[sel_rev_key]]
            
            q_col, a_col1, a_col2, a_col3 = st.columns([7, 1, 1, 1])
            q = q_col.text_input("Search", placeholder="DWG No. or Description", key=f"search_tab_{i}", label_visibility="collapsed")
            if q: 
                df_filt = df_filt[df_filt['DWG. NO.'].str.contains(q, case=False) | df_filt['Description'].str.contains(q, case=False)]
            
            if a_col1.button("📁 Upload", key=f"up_tab_{i}", use_container_width=True): upload_modal()
            
            exp_io = BytesIO()
            df_filt.to_excel(exp_io, index=False)
            a_col2.download_button("📤 Export", data=exp_io.getvalue(), file_name=f"{cat_tag}_List.xlsx", key=f"exp_tab_{i}", use_container_width=True)
            
            if a_col3.button("🖨️ Print", key=f"prt_tab_{i}", use_container_width=True):
                execute_print_v5(df_filt, f"Drawing List - {cat_tag}")

            # 3. 페이지네이션 (30행 제한)
            total_rows = len(df_filt)
            total_pages = max(1, math.ceil(total_rows / ROWS_PER_PAGE))
            pg_key = f"page_idx_{i}"
            if pg_key not in st.session_state: st.session_state[pg_key] = 1
            
            start_idx = (st.session_state[pg_key] - 1) * ROWS_PER_PAGE
            df_paged = df_filt.iloc[start_idx : start_idx + ROWS_PER_PAGE]

            st.dataframe(df_paged, use_container_width=True, hide_index=True, height=750)

            # 하단 페이지 컨트롤러
            if total_pages > 1:
                p_cols = st.columns([8.5, 0.5, 0.5, 0.5])
                p_cols[1].markdown(f"<div style='margin-top:10px;'>{st.session_state[pg_key]} / {total_pages}</div>", unsafe_allow_html=True)
                if p_cols[2].button("◀", key=f"prev_btn_{i}", disabled=(st.session_state[pg_key] == 1)):
                    st.session_state[pg_key] -= 1
                    st.rerun()
                if p_cols[3].button("▶", key=f"next_btn_{i}", disabled=(st.session_state[pg_key] == total_pages)):
                    st.session_state[pg_key] += 1
                    st.rerun()

if __name__ == "__main__":
    main()
