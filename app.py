import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- 1. 기본 설정 및 데이터 처리 ---
DB_PATH = 'data/drawing_master.xlsx'

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

def load_data():
    if os.path.exists(DB_PATH):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        return process_raw_df(df_raw)
    return pd.DataFrame()

# --- 2. [신규] Upload 모달 창 ---
@st.dialog("Upload Master Drawing List")
def upload_drawing_modal():
    st.write("새로운 마스터 리스트(xlsx) 파일을 드래그하여 업로드하세요.")
    file = st.file_uploader("Choose a file", type=["xlsx"], label_visibility="collapsed")
    
    if file:
        if st.button("Save & Apply", type="primary", use_container_width=True):
            try:
                # 파일 물리적 저장
                os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
                with open(DB_PATH, "wb") as f:
                    f.write(file.getbuffer())
                st.success("파일이 성공적으로 저장되었습니다. 데이터를 갱신합니다.")
                st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")

# --- 3. [복구] 인쇄 기능 ---
def execute_print(df, title):
    table_html = df.drop(columns=['Link']).to_html(index=False)
    html_content = f"""
    <html><head><title>{title}</title><style>
    body {{ font-family: sans-serif; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    th, td {{ border: 1px solid #444; padding: 6px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    </style></head><body><h3>{title}</h3>{table_html}
    <script>window.onload = function() {{ window.print(); window.close(); }}</script></body></html>
    """
    # 팝업 차단 회피를 위한 스크립트
    st.components.v1.html(f"<script>var w=window.open(); w.document.write(`{html_content}`); w.document.close();</script>", height=0)

# --- 4. UI 스타일 및 메인 로직 ---
def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # CSS: 버튼 색상(녹색) 및 간격 최적화
    st.markdown("""
        <style>
        .block-container { padding-top: 1.5rem !important; }
        .main-title { font-size: 32px; font-weight: 850; color: #1A4D94; margin-bottom: 2px; }
        /* Revision Filter 버튼 색상 변경 (Primary=Green) */
        div[data-testid="stButton"] button[kind="primary"] { background-color: #28a745 !important; border-color: #28a745 !important; color: white !important; }
        /* 컴팩트 스타일 */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] { min-height: 32px !important; height: 32px !important; }
        .section-label { font-size: 12px; font-weight: 700; color: #444; margin: 15px 0 5px 0; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>Document Control System</div>", unsafe_allow_html=True)
    st.caption("Engineering Document & Drawing Management Dashboard")

    df_master = load_data()
    if df_master.empty:
        st.warning("데이터가 없습니다. 상단 Upload 버튼을 이용해 파일을 업로드해 주세요.")
        if st.button("📁 Upload Drawing List"): upload_drawing_modal()
        return

    # A. 중복 검사 패널
    dups = df_master[df_master.duplicated('DWG. NO.', keep=False)]
    if not dups.empty:
        with st.expander(f"⚠️ Duplicate Drawing Detection ({len(dups)} issues found)", expanded=False):
            st.dataframe(dups.sort_values('DWG. NO.'), use_container_width=True)

    # B. 메인 탭
    tab_list = ["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"]
    tabs = st.tabs(tab_list)

    for i, tab in enumerate(tabs):
        with tab:
            cat_name = tab_list[i].split(" ")[1]
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(cat_name, case=False, na=False)]
            
            # 1. Revision Filter (녹색 테마)
            st.markdown("<p class='section-label'>REVISION FILTER</p>", unsafe_allow_html=True)
            rev_opts = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            r_cols = st.columns([1]*8 + [4])
            
            sel_rev_key = f"sel_rev_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            for idx, r_val in enumerate(rev_opts[:8]):
                if r_cols[idx].button(r_val, key=f"r_{i}_{r_val}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary",
                                      use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.rerun()

            # 2. Search & Filters (컴팩트 레이아웃)
            st.markdown("<p class='section-label'>SEARCH & FILTERS</p>", unsafe_allow_html=True)
            f_cols = st.columns([2.5, 1.2, 1.2, 1.2, 5.9])
            q = f_cols[0].text_input("Search", placeholder="DWG No. or Description", key=f"q_{i}", label_visibility="collapsed")
            f_sys = f_cols[1].selectbox("System", ["All Systems"] + sorted(curr_df['SYSTEM'].unique().tolist()), key=f"s_{i}", label_visibility="collapsed")
            f_area = f_cols[2].selectbox("Area", ["All Areas"] + sorted(curr_df['Area'].unique().tolist()), key=f"a_{i}", label_visibility="collapsed")
            f_stat = f_cols[3].selectbox("Status", ["All Status"] + sorted(curr_df['Status'].unique().tolist()), key=f"st_{i}", label_visibility="collapsed")

            # 필터 로직 적용
            df_disp = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": df_disp = df_disp[df_disp['Rev'] == st.session_state[sel_rev_key]]
            if q: df_disp = df_disp[df_disp['DWG. NO.'].str.contains(q, case=False) | df_disp['Description'].str.contains(q, case=False)]
            if f_sys != "All Systems": df_disp = df_disp[df_disp['SYSTEM'] == f_sys]
            if f_area != "All Areas": df_disp = df_disp[df_disp['Area'] == f_area]
            if f_stat != "All Status": df_disp = df_disp[df_disp['Status'] == f_stat]

            # 3. Action Buttons
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            a_cols = st.columns([7, 1, 1, 1, 1])
            a_cols[0].markdown(f"**Total Found: {len(df_disp):,} items**")
            
            if a_cols[1].button("📁 Upload", key=f"up_btn_{i}", use_container_width=True): upload_drawing_modal()
            if a_cols[2].button("📄 PDF Sync", key=f"sync_btn_{i}", use_container_width=True): st.success("Synced.")
            
            exp_out = BytesIO()
            df_disp.to_excel(exp_out, index=False)
            a_cols[3].download_button("📤 Export", data=exp_out.getvalue(), file_name="drawing_list.xlsx", use_container_width=True)
            
            if a_cols[4].button("🖨️ Print", key=f"prt_btn_{i}", use_container_width=True):
                execute_print(df_disp, f"Drawing List - {cat_name}")

            # 4. 데이터 리스트 (아이콘 뷰 적용)
            st.dataframe(
                df_disp,
                use_container_width=True, hide_index=True, height=600,
                column_config={
                    "Link": st.column_config.LinkColumn("Drawing View", display_text="🔗 View"),
                    "Description": st.column_config.TextColumn("Description", width="large")
                }
            )

if __name__ == "__main__":
    main()
