import streamlit as st
import pandas as pd
import os
import math
import base64
from io import BytesIO

# --- 1. 환경 설정 및 데이터 로드 ---
DB_PATH = 'data/drawing_master.xlsx'
ITEMS_PER_PAGE = 30 

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
            "Drawing": row.get('Drawing', row.get('DRAWING', '-'))
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

# --- 2. 강력한 인쇄 기능 (iframe 주입 방식) ---
def execute_print_v3(df, title):
    table_html = df.drop(columns=['Drawing'], errors='ignore').to_html(index=False)
    html_content = f"""
    <html><head><title>{title}</title><style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
    th, td {{ border: 1px solid #444; padding: 4px; text-align: left; }}
    th {{ background: #eee; font-weight: bold; }}
    </style></head><body><h3>{title}</h3>{table_html}</body></html>
    """
    b64_html = base64.b64encode(html_content.encode()).decode()
    # 팝업 차단을 피하기 위해 iframe 로드 후 자동 인쇄 트리거
    inject_js = f"""
    <iframe id="print_frame" style="display:none;" src="data:text/html;base64,{b64_html}"></iframe>
    <script>
        var frame = document.getElementById('print_frame');
        frame.onload = function() {{
            frame.contentWindow.focus();
            frame.contentWindow.print();
        }};
    </script>
    """
    st.components.v1.html(inject_js, height=0)

# --- 3. UI 컴포넌트 ---
@st.dialog("📤 Upload Master Drawing List")
def upload_modal():
    file = st.file_uploader("XLSX 파일 선택", type=["xlsx"], label_visibility="collapsed")
    if file:
        if st.button("Save & Apply", type="primary", use_container_width=True):
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            with open(DB_PATH, "wb") as f: f.write(file.getbuffer())
            st.cache_data.clear()
            st.success("데이터가 성공적으로 업데이트되었습니다.")
            st.rerun()

def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # CSS: 타이틀 위치 하향(5rem) 및 스타일 최적화
    st.markdown("""
        <style>
        .block-container { padding-top: 5rem !important; } 
        .main-title { font-size: 32px; font-weight: 850; color: #1A4D94; margin-bottom: 5px; }
        .sub-caption { font-size: 14px; color: #666; margin-bottom: 30px; }
        div[data-testid="stButton"] button[kind="primary"] { background-color: #28a745 !important; border-color: #28a745 !important; }
        .section-label { font-size: 11px; font-weight: 700; color: #444; margin: 15px 0 5px 0; text-transform: uppercase; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>Document Control System</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-caption'>Engineering Document & Drawing Management Dashboard</div>", unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.warning("데이터가 존재하지 않습니다. 파일을 업로드해 주세요.")
        if st.button("📁 Upload File"): upload_modal()
        return

    tab_list = ["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"]
    tabs = st.tabs(tab_list)

    for i, tab in enumerate(tabs):
        with tab:
            # 탭별 데이터 필터링
            cat_name = tab_list[i].split(" ")[1]
            df_tab = df_master if i == 0 else df_master[df_master['Category'].str.contains(cat_name, case=False, na=False)]
            
            # REVISION FILTER
            st.markdown("<p class='section-label'>REVISION FILTER</p>", unsafe_allow_html=True)
            rev_options = ["LATEST"] + sorted([r for r in df_tab['Rev'].unique() if pd.notna(r) and r != "-"])
            
            # 필터 상태 관리
            sel_rev_key = f"rev_state_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns([1.2]*7 + [4.6])
            for idx, r_val in enumerate(rev_options[:7]):
                count = len(df_tab) if r_val == "LATEST" else len(df_tab[df_tab['Rev'] == r_val])
                if r_cols[idx].button(f"{r_val} ({count})", key=f"rev_{i}_{idx}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.session_state[f"pg_{i}"] = 1
                    st.rerun()

            # SEARCH & ACTIONS
            st.markdown("<p class='section-label'>SEARCH & ACTIONS</p>", unsafe_allow_html=True)
            df_filt = df_tab.copy()
            if st.session_state[sel_rev_key] != "LATEST": df_filt = df_filt[df_filt['Rev'] == st.session_state[sel_rev_key]]
            
            s_col, b_col = st.columns([6, 4])
            q = s_col.text_input("검색어 입력", placeholder="DWG NO. 또는 Description 검색...", key=f"q_{i}", label_visibility="collapsed")
            if q: df_filt = df_filt[df_filt['DWG. NO.'].str.contains(q, case=False) | df_filt['Description'].str.contains(q, case=False)]
            
            a_cols = b_col.columns(4)
            if a_cols[0].button("📁 Upload", key=f"up_{i}", use_container_width=True): upload_modal()
            if a_cols[1].button("📄 Sync", key=f"sy_{i}", use_container_width=True): st.toast("Synced.")
            
            out = BytesIO()
            df_filt.to_excel(out, index=False)
            a_cols[2].download_button("📤 Export", data=out.getvalue(), file_name=f"{cat_name}.xlsx", key=f"ex_{i}", use_container_width=True)
            
            if a_cols[3].button("🖨️ Print", key=f"pr_{i}", use_container_width=True):
                execute_print_v3(df_filt, f"Drawing List - {cat_name}")

            # --- 4. 페이지네이션 핵심 로직 (30줄 제한) ---
            total_rows = len(df_filt)
            total_pages = max(1, math.ceil(total_rows / ITEMS_PER_PAGE))
            
            pg_key = f"pg_{i}"
            if pg_key not in st.session_state: st.session_state[pg_key] = 1
            
            start_idx = (st.session_state[pg_key] - 1) * ITEMS_PER_PAGE
            end_idx = min(start_idx + ITEMS_PER_PAGE, total_rows)
            df_paged = df_filt.iloc[start_idx:end_idx]

            st.dataframe(
                df_paged, use_container_width=True, hide_index=True, height=750,
                column_config={"Drawing": st.column_config.LinkColumn("View", display_text="🔗 View")}
            )

            # 페이지 네비게이터 (하단 배치)
            p_cols = st.columns([8.5, 0.5, 0.5, 0.5])
            p_cols[1].markdown(f"**{st.session_state[pg_key]}** / {total_pages}")
            if p_cols[2].button("Prev", key=f"prev_{i}", disabled=(st.session_state[pg_key] == 1)):
                st.session_state[pg_key] -= 1
                st.rerun()
            if p_cols[3].button("Next", key=f"next_{i}", disabled=(st.session_state[pg_key] == total_pages)):
                st.session_state[pg_key] += 1
                st.rerun()

if __name__ == "__main__":
    main()
