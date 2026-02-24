import streamlit as st
import pandas as pd
import os
from io import BytesIO

# --- [1] Data Engineering & Management Layer ---
# GitHub 서버 구조 반영 (drawing_control 폴더 기준)
BASE_DIR = 'drawing_control'
DATA_PATH = os.path.join(BASE_DIR, 'data/drawing_master.xlsx')

def get_latest_rev_info(row):
    """최신 리비전 및 날짜 정보를 순차적으로 탐색하여 추출합니다."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def process_master_df(df_raw):
    """Excel 데이터를 표준화된 스키마로 가공 및 정제합니다."""
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', 'Master'),
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
def load_unified_data():
    """변경된 서버 구조에서 통합 데이터를 로드하고 캐싱합니다."""
    if os.path.exists(DATA_PATH):
        try:
            # 원본 이미지의 'DRAWING LIST' 시트 이름 반영
            df_raw = pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            return process_master_df(df_raw)
        except Exception as e:
            st.error(f"Data Load Error: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# --- [2] Presentation & Interaction Layer ---
def main():
    st.set_page_config(layout="wide", page_title="DCS & Construction Manager")

    # 원본 디자인 정밀 복구를 위한 CSS 스타일 정의
    st.markdown("""
        <style>
        .main-title { 
            font-size: 32px; font-weight: 850; color: #1A4D94; 
            border-left: 8px solid #1A4D94; padding-left: 15px; margin-bottom: 20px;
        }
        .section-header {
            font-size: 13px; font-weight: 700; color: #666; margin: 25px 0 10px 0; text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_unified_data()
    if df_master.empty:
        st.warning(f"서버 구조를 확인하십시오. 경로: {DATA_PATH}")
        return

    # 탭 메뉴 구성
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            # 카테고리별 필터링 (Master는 전체 표시)
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # --- REVISION FILTER (수량 표시 기능) ---
            st.markdown('<div class="section-header">REVISION FILTER</div>', unsafe_allow_html=True)
            rev_counts = curr_df['Rev'].value_counts()
            unique_revs = sorted([str(r) for r in curr_df['Rev'].unique() if pd.notna(r) and str(r).strip() != "-"])
            
            # 버튼 라벨에 수량 결합 (예: LATEST (3807))
            rev_opts = [("LATEST", len(curr_df))] + [(r, rev_counts.get(r, 0)) for r in unique_revs]
            
            sel_rev_key = f"rev_v_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            r_cols = st.columns(len(rev_opts[:7]) + 1)
            for idx, (r_name, r_count) in enumerate(rev_opts[:7]):
                btn_label = f"{r_name} ({r_count})"
                is_selected = st.session_state[sel_rev_key] == r_name
                if r_cols[idx].button(btn_label, key=f"btn_{i}_{idx}", 
                                      type="primary" if is_selected else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_name
                    st.rerun()

            df_filt = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST": 
                df_filt = df_filt[df_filt['Rev'] == st.session_state[sel_rev_key]]
            
            # --- SEARCH & FILTERS ---
            st.markdown('<div class="section-header">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            sys_list = ["All Systems"] + sorted([str(x) for x in curr_df['SYSTEM'].unique() if pd.notna(x) and str(x).strip() != ""])
            area_list = ["All Areas"] + sorted([str(x) for x in curr_df['Area'].unique() if pd.notna(x) and str(x).strip() != ""])
            
            s_col1, s_col2, s_col3, s_col4 = st.columns([4, 2, 2, 2])
            q = s_col1.text_input("Search", key=f"q_{i}", placeholder="Search...", label_visibility="collapsed")
            sel_sys = s_col2.selectbox("System", sys_list, key=f"sys_{i}", label_visibility="collapsed")
            sel_area = s_col3.selectbox("Area", area_list, key=f"area_{i}", label_visibility="collapsed")
            sel_stat = s_col4.selectbox("Status", ["All Status"] + list(curr_df['Status'].unique()), key=f"stat_{i}", label_visibility="collapsed")
            
            # 필터 로직 적용
            if q: df_filt = df_filt[df_filt['DWG. NO.'].str.contains(q, case=False, na=False) | df_filt['Description'].str.contains(q, case=False, na=False)]
            if sel_sys != "All Systems": df_filt = df_filt[df_filt['SYSTEM'] == sel_sys]
            if sel_area != "All Areas": df_filt = df_filt[df_filt['Area'] == sel_area]
            if sel_stat != "All Status": df_filt = df_filt[df_filt['Status'] == sel_stat]
            
            # --- ACTION TOOLBAR ---
            st.write(f"**Total Found: {len(df_filt):,} records**")
            b_cols = st.columns([6, 1, 1, 1, 1])
            b_cols[1].button("📁 Upload", key=f"up_{i}", use_container_width=True)
            b_cols[2].button("📄 PDF Sync", key=f"sync_{i}", use_container_width=True)
            
            ex_io = BytesIO()
            df_filt.to_excel(ex_io, index=False)
            b_cols[3].download_button("📤 Export", data=ex_io.getvalue(), file_name=f"{tab_names[i]}.xlsx", key=f"ex_{i}", use_container_width=True)
            b_cols[4].button("🖨️ Print", key=f"prt_{i}", use_container_width=True)

            # --- DATA TABLE (🔍 View 아이콘 복구) ---
            st.dataframe(
                df_filt, 
                use_container_width=True, 
                hide_index=True, 
                height=550,
                column_config={
                    "Drawing": st.column_config.LinkColumn(
                        "View",
                        display_text="🔍 View",
                        help="클릭하여 도면 파일을 확인하십시오."
                    )
                }
            )

if __name__ == "__main__":
    main()
