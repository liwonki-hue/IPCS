import streamlit as st
import pandas as pd
import os
import math
import base64
from io import BytesIO

# --- 1. 데이터 로직 ---
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

# --- 2. [완전 해결] 인쇄 기능 (Hidden Iframe Injector) ---
def execute_print_final(df, title):
    """팝업 설정을 무시하고 인쇄를 트리거하는 가장 안정적인 방식"""
    table_html = df.drop(columns=['Link'], errors='ignore').to_html(index=False)
    # UTF-8 보장을 위해 HTML 구조 개선
    full_html = f"""
    <html><head><meta charset="utf-8"><style>
    body {{ font-family: 'Malgun Gothic', sans-serif; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
    th, td {{ border: 1px solid #333; padding: 4px; text-align: left; }}
    th {{ background: #eee; font-weight: bold; }}
    </style></head><body><h3>{title}</h3>{table_html}</body></html>
    """
    b64_content = base64.b64encode(full_html.encode('utf-8')).decode()
    
    # 별도 창 없이 현재 앱 내부에 숨겨진 iframe으로 인쇄 명령 전달
    components_script = f"""
    <iframe id="print_frame_final" style="display:none;" src="data:text/html;base64,{b64_content}"></iframe>
    <script>
        const frame = document.getElementById('print_frame_final');
        frame.onload = function() {{
            frame.contentWindow.focus();
            frame.contentWindow.print();
        }};
    </script>
    """
    st.components.v1.html(components_script, height=0)

# --- 3. 메인 인터페이스 ---
def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # 화면 레이아웃 보정 (padding-top 상향 및 타이틀 위치 고정)
    st.markdown("""
        <style>
        .block-container { padding-top: 10rem !important; } 
        .main-header { position: relative; margin-bottom: 2rem; }
        .main-title { font-size: 36px; font-weight: 900; color: #1A4D94; line-height: 1.2; }
        .sub-caption { font-size: 14px; color: #666; }
        div[data-testid="stButton"] button[kind="primary"] { background-color: #28a745 !important; }
        </style>
    """, unsafe_allow_html=True)

    # 헤더 섹션
    st.markdown("""
        <div class="main-header">
            <div class="main-title">Document Control System</div>
               </div>
    """, unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.warning("데이터 파일(drawing_master.xlsx)을 찾을 수 없습니다.")
        return

    tab_titles = ["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"]
    tabs = st.tabs(tab_titles)

    for i, tab in enumerate(tabs):
        with tab:
            tab_name = tab_titles[i].split(" ")[1]
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_name, case=False, na=False)]
            
            # 1. Revision Filter
            st.caption("REVISION FILTER")
            rev_opts = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            
            sel_rev_key = f"rev_state_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns([1.2]*len(rev_opts[:8]) + [1])
            for idx, r_val in enumerate(rev_opts[:8]):
                count = len(curr_df) if r_val == "LATEST" else len(curr_df[curr_df['Rev'] == r_val])
                if r_cols[idx].button(f"{r_val} ({count})", key=f"btn_rev_{i}_{idx}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.rerun()

            # 2. Search & Toolbar
            df_filt = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": 
                df_filt = df_filt[df_filt['Rev'] == st.session_state[sel_rev_key]]
            
            st.write("---")
            q_col, a_col1, a_col2 = st.columns([7, 1.5, 1.5])
            q = q_col.text_input("Search", placeholder="DWG No. or Description", key=f"q_input_{i}", label_visibility="collapsed")
            if q: 
                df_filt = df_filt[df_filt['DWG. NO.'].str.contains(q, case=False) | df_filt['Description'].str.contains(q, case=False)]
            
            # 3. Action Buttons (Print 기능 포함)
            if a_col1.button("🖨️ Print List", key=f"print_act_{i}", use_container_width=True):
                execute_print_final(df_filt, f"Drawing List - {tab_name}")
            
            exp_io = BytesIO()
            df_filt.to_excel(exp_io, index=False)
            a_col2.download_button("📤 Export Excel", data=exp_io.getvalue(), file_name=f"{tab_name}.xlsx", key=f"exp_act_{i}", use_container_width=True)

            # 4. 30행 페이지네이션
            total_rows = len(df_filt)
            total_pages = max(1, math.ceil(total_rows / ROWS_PER_PAGE))
            pg_key = f"pg_num_{i}"
            if pg_key not in st.session_state: st.session_state[pg_key] = 1
            
            start_idx = (st.session_state[pg_key] - 1) * ROWS_PER_PAGE
            st.dataframe(df_filt.iloc[start_idx : start_idx + ROWS_PER_PAGE], use_container_width=True, hide_index=True, height=750)

            # 페이지 컨트롤러
            if total_pages > 1:
                p_left, p_mid, p_right = st.columns([9, 0.5, 0.5])
                p_mid.button("◀", key=f"prev_{i}", on_click=lambda: st.session_state.update({pg_key: max(1, st.session_state[pg_key]-1)}))
                p_right.button("▶", key=f"next_{i}", on_click=lambda: st.session_state.update({pg_key: min(total_pages, st.session_state[pg_key]+1)}))
                st.info(f"Page {st.session_state[pg_key]} of {total_pages} (Total {total_rows} records)")

if __name__ == "__main__":
    main()
