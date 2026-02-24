import streamlit as st
import pandas as pd
import os
from io import BytesIO
import streamlit.components.v1 as components

# --- [1] Configuration & Data Engineering ---
BASE_DIR = 'drawing_control'
DATA_PATH = os.path.join(BASE_DIR, 'data/drawing_master.xlsx')

@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        try:
            df = pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            # 기본 컬럼 정규화 (사용자 화면 기반)
            if 'Rev' not in df.columns: df['Rev'] = '-'
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- [2] UI Styling & Print Engine ---
def apply_ui_enhancements():
    # 인쇄 시 테이블만 깨끗하게 나오도록 하는 CSS 및 메인 디자인
    st.markdown("""
        <style>
        .main-title { font-size: 30px; font-weight: 850; color: #1A4D94; border-left: 8px solid #1A4D94; padding-left: 15px; margin-bottom: 25px; }
        .section-header { font-size: 12px; font-weight: 700; color: #666; margin: 20px 0 8px 0; text-transform: uppercase; }
        
        /* 인쇄 최적화: 버튼 및 필터 제외, 테이블만 출력 시도 */
        @media print {
            .stButton, .stTabs, .section-header, .main-title { display: none !important; }
            .stDataFrame { width: 100% !important; }
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="IPCS - Document Control")
    apply_ui_enhancements()

    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.error("데이터를 불러올 수 없습니다. 경로를 확인하십시오.")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            # 1. REVISION FILTER (수량 복구 및 녹색 강조)
            st.markdown('<div class="section-header">REVISION FILTER</div>', unsafe_allow_html=True)
            
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # 수량 집계 로직
            rev_counts = curr_df['Rev'].value_counts()
            rev_list = ["LATEST", "C01", "C01A", "C01B", "C02", "VOID"]
            
            sel_rev_key = f"sel_rev_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"

            # 중앙까지만 배치 (7개 컬럼 사용)
            r_cols = st.columns([1, 1, 1, 1, 1, 1, 6])
            for idx, r_name in enumerate(rev_list):
                count = len(curr_df) if r_name == "LATEST" else rev_counts.get(r_name, 0)
                btn_label = f"{r_name} ({count})"
                
                is_active = st.session_state[sel_rev_key] == r_name
                if r_cols[idx].button(btn_label, key=f"rev_{i}_{idx}", 
                                      type="primary" if is_active else "secondary", 
                                      use_container_width=True):
                    st.session_state[sel_rev_key] = r_name
                    st.rerun()

            # --- 데이터 필터링 적용 ---
            df_display = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST":
                df_display = df_display[df_display['Rev'] == st.session_state[sel_rev_key]]

            # 2. SEARCH & FILTERS (화면 2/3 지점 배치)
            st.markdown('<div class="section-header">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            s_col1, s_col2, s_col3, s_col4, s_spacer = st.columns([4, 2, 2, 2, 5])
            
            with s_col1: q = st.text_input("Search", key=f"q_{i}", placeholder="검색어 입력...", label_visibility="collapsed")
            with s_col2: st.selectbox("System", ["All Systems"], key=f"sys_{i}", label_visibility="collapsed")
            with s_col3: st.selectbox("Area", ["All Areas"], key=f"area_{i}", label_visibility="collapsed")
            with s_col4: st.selectbox("Status", ["All Status"], key=f"stat_{i}", label_visibility="collapsed")

            if q:
                df_display = df_display[df_display['DWG. NO.'].str.contains(q, case=False, na=False) | 
                                        df_display['Description'].str.contains(q, case=False, na=False)]

            # 3. ACTION TOOLBAR
            st.write(f"**
