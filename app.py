import streamlit as st
import pandas as pd
import os
from io import BytesIO
import streamlit.components.v1 as components

# --- [1] Data Engineering Layer ---
BASE_DIR = 'drawing_control'
DATA_PATH = os.path.join(BASE_DIR, 'data/drawing_master.xlsx')

@st.cache_data
def load_unified_data():
    if os.path.exists(DATA_PATH):
        try:
            df_raw = pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            # 기존 데이터 가공 로직 포함 (생략 가능 시 생략)
            return df_raw 
        except Exception as e:
            st.error(f"Data Load Error: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# --- [2] UI & Logic Layer ---
def main():
    st.set_page_config(layout="wide", page_title="DCS Dashboard")

    # 브라우저 출력 JS (Print 기능)
    components.html("<script>function printPage() { window.print(); }</script>", height=0)

    # CSS: 버튼 간격 및 타이틀 스타일
    st.markdown("""
        <style>
        .main-title { font-size: 30px; font-weight: 850; color: #1A4D94; border-left: 8px solid #1A4D94; padding-left: 15px; margin-bottom: 20px; }
        .section-header { font-size: 12px; font-weight: 700; color: #666; margin: 20px 0 10px 0; text-transform: uppercase; letter-spacing: 1px; }
        /* 버튼 간격 미세 조정 */
        .stButton>button { margin-right: 5px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_unified_data()
    if df_master.empty:
        st.warning(f"데이터 파일을 찾을 수 없습니다: {DATA_PATH}")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = df_master # 실제 환경에선 카테고리 필터 적용
            
            # --- 1. REVISION FILTER (화면 중앙까지만 위치) ---
            st.markdown('<div class="section-header">REVISION FILTER</div>', unsafe_allow_html=True)
            rev_counts = curr_df['Rev'].value_counts() if 'Rev' in curr_df else {}
            unique_revs = ["C01", "C01A", "C01B", "C02", "VOID"] # 예시 리스트
            rev_opts = [("LATEST", len(curr_df))] + [(r, rev_counts.get(r, 0)) for r in unique_revs]
            
            sel_rev_key = f"rev_v_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"
            
            # 총 12컬럼 중 7컬럼만 사용하여 중앙까지만 배치
            r_cols = st.columns([1, 1, 1, 1, 1, 1, 1, 5]) 
            for idx, (r_name, r_count) in enumerate(rev_opts[:7]):
                btn_label = f"{r_name}\n({r_count})"
                # 선택된 버튼은 녹색(Primary)으로 표시
                is_selected = st.session_state[sel_rev_key] == r_name
                if r_cols[idx].button(btn_label, key=f"btn_{i}_{idx}", 
                                      type="primary" if is_selected else "secondary", 
                                      use_container_width=True):
                    st.session_state[sel_rev_key] = r_name
                    st.rerun()

            # --- 2. SEARCH & FILTERS (화면 2/3 지점까지만 위치) ---
            st.markdown('<div class="section-header">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            # 컬럼 비율 조정을 통해 우측 여백 확보 (4+2+2+2 = 10, 나머지 5는 여백)
            s_col1, s_col2, s_col3, s_col4, s_spacer = st.columns([4, 2, 2, 2, 5])
            
            with s_col1: q = st.text_input("Search", key=f"q_{i}", placeholder="Search...", label_visibility="collapsed")
            with s_col2: sel_sys = st.selectbox("System", ["All Systems"], key=f"sys_{i}", label_visibility="collapsed")
            with s_col3: sel_area = st.selectbox("Area", ["All Areas"], key=f"area_{i}", label_visibility="collapsed")
            with s_col4: sel_stat = st.selectbox("Status", ["All Status"], key=f"stat_{i}", label_visibility="collapsed")
            
            # --- 3. ACTION TOOLBAR & WORKING BUTTONS ---
            st.write(f"**Total Found: {len(curr_df):,} records**")
            b_cols = st.columns([6, 1, 1, 1, 1])
            
            # [Upload 버튼 작동 방식 개선]
            if b_cols[1].button("📁 Upload", key=f"up_btn_{i}", use_container_width=True):
                st.session_state[f"show_up_{i}"] = not st.session_state.get(f"show_up_{i}", False)
            
            # [PDF Sync 버튼 작동 시뮬레이션]
            if b_cols[2].button("📄 PDF Sync", key=f"sync_btn_{i}", use_container_width=True):
                st.toast("Scanning PDF repository... Sync completed!", icon="✅")
            
            # Export 및 Print
            ex_io = BytesIO()
            curr_df.to_excel(ex_io, index=False)
            b_cols[3].download_button("📤 Export", data=ex_io.getvalue(), file_name="export.xlsx", key=f"ex_{i}", use_container_width=True)
            
            if b_cols[4].button("🖨️ Print", key=f"prt_{i}", use_container_width=True):
                components.html("<script>window.parent.print();</script>", height=0)

            # 업로드 창 활성화 시 표시
            if st.session_state.get(f"show_up_{i}", False):
                st.file_uploader("최신 Drawing List(Excel)를 업로드하세요.", type=['xlsx'], key=f"uploader_{i}")

            # --- 4. DATA TABLE ---
            st.dataframe(
                curr_df, 
                use_container_width=True, 
                hide_index=True, 
                height=500,
                column_config={
                    "Drawing": st.column_config.LinkColumn("View", display_text="🔍 View")
                }
            )

if __name__ == "__main__":
    main()
