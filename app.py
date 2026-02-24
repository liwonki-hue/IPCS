import streamlit as st
import pandas as pd
import os
from io import BytesIO
import streamlit.components.v1 as components

# --- [1] Data Processing: 최신 리비전 1개만 추출하는 로직 ---
BASE_DIR = 'drawing_control'
DATA_PATH = os.path.join(BASE_DIR, 'data/drawing_master.xlsx')

def get_latest_info(row):
    """리비전 열들을 검사하여 가장 최신(3rd > 2nd > 1st) 정보를 반환"""
    # 원본 엑셀의 컬럼명에 맞춰 조정 (필요 시 수정)
    rev_map = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r_col, d_col in rev_map:
        val = row.get(r_col)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d_col, '-')
    return '-', '-'

@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH): return pd.DataFrame()
    try:
        df_raw = pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        processed = []
        for _, row in df_raw.iterrows():
            rev, date = get_latest_info(row)
            processed.append({
                "Category": row.get('Category', 'Master'),
                "Area": row.get('Area', '-'),
                "SYSTEM": row.get('SYSTEM', '-'),
                "DWG. NO.": row.get('DWG. NO.', '-'),
                "Description": row.get('DRAWING TITLE', '-'),
                "Rev": rev,
                "Date": date,
                "Hold": row.get('HOLD Y/N', 'N'),
                "Status": row.get('Status', '-'),
                "Drawing": row.get('Link', None)
            })
        return pd.DataFrame(processed)
    except: return pd.DataFrame()

# --- [2] UI & CSS 정밀 설정 ---
def apply_style():
    st.markdown("""
        <style>
        .main-title { font-size: 26px; font-weight: 800; color: #1A4D94; border-left: 6px solid #1A4D94; padding-left: 12px; margin-bottom: 20px; }
        .section-label { font-size: 11px; font-weight: 700; color: #888; margin: 10px 0 5px 0; }
        /* 버튼 간격 및 폰트 최적화 */
        div[data-testid="column"] { padding: 0 2px !important; }
        button[kind="secondary"], button[kind="primary"] { font-size: 11px !important; height: 32px !important; }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="IPCS DCS")
    apply_style()
    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.warning("데이터 파일이 없거나 형식이 잘못되었습니다.")
        return

    # 탭 구성
    tab_titles = ["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"]
    tabs = st.tabs(tab_titles)
    categories = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for idx, tab in enumerate(tabs):
        with tab:
            # 카테고리 필터링
            target_df = df_master if idx == 0 else df_master[df_master['Category'].str.contains(categories[idx], case=False, na=False)]
            
            # --- 1. REVISION SELECTION (1줄 정렬) ---
            st.markdown('<div class="section-label">REVISION SELECTION</div>', unsafe_allow_html=True)
            rev_list = ["LATEST", "C01", "C01A", "C01B", "C02", "VOID"]
            
            s_key = f"sel_rev_{idx}"
            if s_key not in st.session_state: st.session_state[s_key] = "LATEST"
            
            # 7개 열로 나누어 버튼 배치 (밀림 방지)
            r_cols = st.columns([1, 1, 1, 1, 1, 1, 5])
            for r_idx, r_name in enumerate(rev_list):
                # 선택된 버튼은 primary(녹색 계열) 표시
                is_active = st.session_state[s_key] == r_name
                if r_cols[r_idx].button(r_name, key=f"btn_{idx}_{r_idx}", type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state[s_key] = r_name
                    st.rerun()

            # 데이터 필터 적용
            df_view = target_df.copy()
            if st.session_state[s_key] != "LATEST":
                df_view = df_view[df_view['Rev'] == st.session_state[s_key]]

            # --- 2. SEARCH & FILTERS ---
            st.markdown('<div class="section-label">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            f1, f2, f3, f4, f_sp = st.columns([4, 2, 2, 2, 4])
            with f1: q
