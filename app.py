import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# --- 1. 데이터 로드 및 전처리 ---
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
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

# --- 2. 기능 구현 (Upload & Print) ---

@st.dialog("📤 Upload Master Drawing List")
def upload_modal():
    st.write("새로운 엑셀 파일을 드래그하여 업로드하세요.")
    file = st.file_uploader("Choose XLSX file", type=["xlsx"], label_visibility="collapsed")
    if file:
        if st.button("Save & Apply", type="primary", use_container_width=True):
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            with open(DB_PATH, "wb") as f:
                f.write(file.getbuffer())
            st.cache_data.clear() # 캐시 초기화
            st.success("데이터가 성공적으로 업데이트되었습니다.")
            st.rerun()

def execute_print(df, title):
    table_html = df.drop(columns=['Link'], errors='ignore').to_html(index=False)
    print_js = f"""
    <script>
    var w = window.open();
    w.document.write('<html><head><title>{title}</title>');
    w.document.write('<style>body{{font-family:sans-serif;padding:20px;}} table{{width:100%;border-collapse:collapse;font-size:10px;}} th,td{{border:1px solid #444;padding:4px;text-align:left;}} th{{background:#eee;}}</style>');
    w.document.write('</head><body><h3>{title}</h3>{table_html.replace("'", "\\'").replace("\\n", "")}</body></html>');
    w.document.close();
    w.focus();
    w.print();
    w.close();
    </script>
    """
    st.components.v1.html(print_js, height=0)

# --- 3. UI 렌더링 ---

def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # CSS 설정
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; }
        .main-title { font-size: 32px; font-weight: 850; color: #1A4D94; margin-bottom: 0px; }
        .sub-caption { font-size: 13px; color: #666; margin-bottom: 20px; }
        /* Revision 버튼: 선택 시 녹색(Green) */
        div[data-testid="stButton"] button[kind="primary"] { background-color: #28a745 !important; border-color: #28a745 !important; }
        .section-label { font-size: 11px; font-weight: 700; color: #444; margin: 15px 0 5px 0; text-transform: uppercase; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>Document Control System</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-caption'>Engineering Document & Drawing Management Dashboard</div>", unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.info("No data available. Please use the Upload button.")
        if st.button("📁 First Time Upload"): upload_modal()
        return

    # A. 중복 검사 (Expander)
    dups = df_master[df_master.duplicated('DWG. NO.', keep=False)]
    if not dups.empty:
        with st.expander(f"⚠️ Duplicate Drawing Detection ({len(dups)} issues found)", expanded=False):
            st.dataframe(dups.sort_values('DWG. NO.'), use_container_width=True)

    # B. 메인 탭
    tab_list = ["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"]
    tabs = st.tabs(tab_list)

    for i, tab in enumerate(tabs):
        with tab:
            # 카테고리 필터링
            cat_tag = tab_list[i].split(" ")[1]
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(cat_tag, case=False, na=False)]
            
            # 1. Revision Filter (수량 포함 + 녹색 강조)
            st.markdown("<p class='section-label'>REVISION FILTER</p>", unsafe_allow_html=True)
            rev_counts = curr_df['Rev'].value_counts()
            rev_opts = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            
            sel_rev_key = f"active_rev_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns([1.2]*7 + [4.6])
            for idx, r_val in enumerate(rev_opts[:7]):
                count = len(curr_df) if r_val == "LATEST" else rev_counts.get(r_val, 0)
                if r_cols[idx].button(f"{r_val} ({count})", key=f"rev_b_{i}_{idx}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary",
                                      use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.rerun()

            # 2. Search & Multi-Filters
            st.markdown("<p class='section-label'>SEARCH & FILTERS</p>", unsafe_allow_html=True)
            f_cols = st.columns([2.5, 1.2, 1.2, 1.2, 5.9])
            q = f_cols[0].text_input("Search", placeholder="DWG No. or Description", key=f"q_in_{i}", label_visibility="collapsed")
            f_sys = f_cols[1].selectbox("System", ["All Systems"] + sorted(curr_df['SYSTEM'].unique().tolist()), key=f"sys_s_{i}", label_visibility="collapsed")
            f_area = f_cols[2].selectbox("Area", ["All Areas"] + sorted(curr_df['Area'].unique().tolist()), key=f"area_s_{i}", label_visibility="collapsed")
            f_stat = f_cols[3].selectbox("Status", ["All Status"] + sorted(curr_df['Status'].unique().tolist()), key=f"stat_s_{i}", label_visibility="collapsed")

            # 필터링 로직
            df_filt = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": df_filt = df_filt[df_filt['Rev'] == st.session_state[sel_rev_key]]
            if q: df_filt = df_filt[df_filt['DWG. NO.'].str.contains(q, case=False) | df_filt['Description'].str.contains(q, case=False)]
            if f_sys != "All Systems": df_filt = df_filt[df_filt['SYSTEM'] == f_sys]
            if f_area != "All Areas": df_filt = df_filt[df_filt['Area'] == f_area]
            if f_stat != "All Status": df_filt = df_filt[df_filt['Status'] == f_stat]

            # 3. Action Buttons
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            a_cols = st.columns([7, 1, 1, 1, 1])
            a_cols[0].markdown(f"**Total Found: {len(df_filt):,} items**")
            
            if a_cols[1].button("📁 Upload", key=f"up_btn_tab_{i}", use_container_width=True): upload_modal()
            if a_cols[2].button("📄 PDF Sync", key=f"sync_btn_tab_{i}", use_container_width=True): st.success("Synced.")
            
            exp_io = BytesIO()
            df_filt.to_excel(exp_io, index=False)
            a_cols[3].download_button("📤 Export", data=exp_io.getvalue(), file_name="export.xlsx", key=f"exp_btn_tab_{i}", use_container_width=True)
            
            if a_cols[4].button("🖨️ Print", key=f"prt_btn_tab_{i}", use_container_width=True):
                execute_print(df_filt, f"Drawing List - {cat_tag}")

            # 4. 페이지네이션 (30줄)
            total_pages = math.ceil(len(df_filt) / ROWS_PER_PAGE)
            curr_p_key = f"curr_page_{i}"
            if curr_p_key not in st.session_state: st.session_state[curr_p_key] = 1
            
            start_idx = (st.session_state[curr_p_key] - 1) * ROWS_PER_PAGE
            end_idx = start_idx + ROWS_PER_PAGE
            df_paged = df_filt.iloc[start_idx:end_idx]

            # 데이터 테이블
            st.dataframe(
                df_paged, use_container_width=True, hide_index=True, height=750,
                column_config={
                    "Link": st.column_config.LinkColumn("View", display_text="🔗 View"),
                    "Description": st.column_config.TextColumn("Description", width="large")
                }
            )

            # 하단 페이지 컨트롤러
            if total_pages > 1:
                p_cols = st.columns([8, 1, 1, 1, 1])
                p_cols[1].write(f"Page {st.session_state[curr_p_key]} of {total_pages}")
                if p_cols[2].button("Prev", key=f"prev_{i}", disabled=(st.session_state[curr_p_key] == 1)):
                    st.session_state[curr_p_key] -= 1
                    st.rerun()
                if p_cols[3].button("Next", key=f"next_{i}", disabled=(st.session_state[curr_p_key] == total_pages)):
                    st.session_state[curr_p_key] += 1
                    st.rerun()

if __name__ == "__main__":
    main()
