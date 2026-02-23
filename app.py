import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- 1. 데이터 처리 로직 ---
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
        try:
            df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            return process_raw_df(df_raw)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- 2. 개선된 인쇄 기능 (안정성 강화) ---
def execute_print(df, title):
    """HTML 테이블을 생성하여 브라우저 인쇄 창을 강제 호출"""
    table_html = df.drop(columns=['Link'], errors='ignore').to_html(index=False)
    # 팝업 차단을 최소화하기 위한 인라인 스크립트 방식
    html_content = f"""
    <html><head><title>{title}</title><style>
    body {{ font-family: 'Segoe UI', sans-serif; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    th, td {{ border: 1px solid #444; padding: 6px; text-align: left; }}
    th {{ background: #f2f2f2; font-weight: bold; }}
    </style></head><body>
    <h2 style='color:#1A4D94;'>{title}</h2>
    {table_html}
    <script>
        window.onload = function() {{ 
            window.print(); 
            setTimeout(function() {{ window.close(); }}, 100); 
        }}
    </script>
    </body></html>
    """
    st.components.v1.html(f"<script>var w=window.open(); w.document.write(`{html_content}`); w.document.close();</script>", height=0)

# --- 3. UI 설정 및 메인 로직 ---
def main():
    st.set_page_config(layout="wide", page_title="Document Control System")
    
    # CSS: 타이틀 위치 조정 및 버튼 색상
    st.markdown("""
        <style>
        /* 타이틀 위치 상단 여백 확보 */
        .block-container { padding-top: 3rem !important; }
        .main-title { font-size: 34px; font-weight: 850; color: #1A4D94; margin-bottom: 5px; margin-top: -10px; }
        .sub-caption { font-size: 13px; color: #666; margin-bottom: 25px; }
        
        /* Revision Filter 버튼 (선택 시 녹색) */
        div[data-testid="stButton"] button[kind="primary"] { background-color: #28a745 !important; border-color: #28a745 !important; color: white !important; }
        
        /* 필터 섹션 겹침 방지 여백 */
        .section-label { font-size: 11px; font-weight: 700; color: #444; margin: 18px 0 8px 0; text-transform: uppercase; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='main-title'>Document Control System</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-caption'>Engineering Document & Drawing Management Dashboard</div>", unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.info("데이터가 없습니다. 파일을 업로드해 주세요.")
        return

    # A. 중복 검사 (필요 시 노출)
    dups = df_master[df_master.duplicated('DWG. NO.', keep=False)]
    if not dups.empty:
        with st.expander(f"⚠️ Duplicate Drawing Detection ({len(dups)} issues found)", expanded=False):
            st.dataframe(dups.sort_values('DWG. NO.'), use_container_width=True)

    # B. 메인 탭 (중복 Key 에러 방지를 위해 enumerate 사용)
    tab_list = ["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"]
    tabs = st.tabs(tab_list)

    for i, tab in enumerate(tabs):
        with tab:
            # 카테고리 필터링
            cat_name = tab_list[i].split(" ")[1]
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(cat_name, case=False, na=False)]
            
            # 1. Revision Filter (수량 표기 포함)
            st.markdown("<p class='section-label'>REVISION FILTER</p>", unsafe_allow_html=True)
            rev_counts = curr_df['Rev'].value_counts()
            total_count = len(curr_df)
            
            # 버튼에 표시될 텍스트 리스트 구성
            rev_opts = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            r_cols = st.columns([1.2]*7 + [4.6]) # 버튼 폭 조절
            
            sel_rev_key = f"sel_rev_tab_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            for idx, r_val in enumerate(rev_opts[:7]):
                # 수량 계산
                label_count = total_count if r_val == "LATEST" else rev_counts.get(r_val, 0)
                btn_label = f"{r_val} ({label_count})"
                
                if r_cols[idx].button(btn_label, key=f"rev_btn_{i}_{idx}", 
                                      type="primary" if st.session_state[sel_rev_key] == r_val else "secondary",
                                      use_container_width=True):
                    st.session_state[sel_rev_key] = r_val
                    st.rerun()

            # 2. Search & Filters (중간 배치)
            st.markdown("<p class='section-label'>SEARCH & FILTERS</p>", unsafe_allow_html=True)
            f_cols = st.columns([2.5, 1.2, 1.2, 1.2, 5.9])
            q = f_cols[0].text_input("Search", placeholder="DWG No. or Description", key=f"search_input_{i}", label_visibility="collapsed")
            f_sys = f_cols[1].selectbox("System", ["All Systems"] + sorted(curr_df['SYSTEM'].unique().tolist()), key=f"sys_sel_{i}", label_visibility="collapsed")
            f_area = f_cols[2].selectbox("Area", ["All Areas"] + sorted(curr_df['Area'].unique().tolist()), key=f"area_sel_{i}", label_visibility="collapsed")
            f_stat = f_cols[3].selectbox("Status", ["All Status"] + sorted(curr_df['Status'].unique().tolist()), key=f"stat_sel_{i}", label_visibility="collapsed")

            # 필터 적용
            df_disp = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": 
                df_disp = df_disp[df_disp['Rev'] == st.session_state[sel_rev_key]]
            if q: 
                df_disp = df_disp[df_disp['DWG. NO.'].str.contains(q, case=False) | df_disp['Description'].str.contains(q, case=False)]
            if f_sys != "All Systems": df_disp = df_disp[df_disp['SYSTEM'] == f_sys]
            if f_area != "All Areas": df_disp = df_disp[df_disp['Area'] == f_area]
            if f_stat != "All Status": df_disp = df_disp[df_disp['Status'] == f_stat]

            # 3. Action Toolbar (고유 Key 부여)
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            a_cols = st.columns([7, 1, 1, 1, 1])
            a_cols[0].markdown(f"**Total Found: {len(df_disp):,} items**")
            
            # 버튼마다 고유한 key=f"..._{i}" 부여하여 DuplicateElementId 방지
            if a_cols[1].button("📁 Upload", key=f"upload_act_{i}", use_container_width=True):
                st.toast("Upload Modal can be linked here.")
            
            if a_cols[2].button("📄 PDF Sync", key=f"sync_act_{i}", use_container_width=True):
                st.success("Synchronized.")

            exp_out = BytesIO()
            df_disp.to_excel(exp_out, index=False)
            a_cols[3].download_button("📤 Export", data=exp_out.getvalue(), file_name=f"{cat_name}_list.xlsx", key=f"export_act_{i}", use_container_width=True)
            
            if a_cols[4].button("🖨️ Print", key=f"print_act_{i}", use_container_width=True):
                execute_print(df_disp, f"Drawing Control List - {cat_name}")

            # 4. Drawing List Table
            st.dataframe(
                df_disp,
                use_container_width=True, hide_index=True, height=600,
                column_config={
                    "Link": st.column_config.LinkColumn("Drawing View", display_text="🔗 View"),
                    "Description": st.column_config.TextColumn("Description", width="large"),
                    "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium")
                }
            )

if __name__ == "__main__":
    main()
