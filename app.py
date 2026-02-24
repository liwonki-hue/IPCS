import streamlit as st
import pandas as pd
import os
from io import BytesIO
import streamlit.components.v1 as components

# --- [1] Configuration & Path ---
BASE_DIR = 'drawing_control'
DATA_PATH = os.path.join(BASE_DIR, 'data/drawing_master.xlsx')

@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        try:
            return pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- [2] UI Styling ---
def apply_custom_style():
    st.markdown("""
        <style>
        .main-title { font-size: 30px; font-weight: 850; color: #1A4D94; border-left: 8px solid #1A4D94; padding-left: 15px; margin-bottom: 25px; }
        .section-header { font-size: 12px; font-weight: 700; color: #666; margin: 20px 0 8px 0; text-transform: uppercase; }
        /* 버튼 가로 여백 최소화 */
        div[data-testid="column"] { padding: 0 5px !important; }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="IPCS - Document Control")
    apply_custom_style()

    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df = load_data()
    if df.empty:
        st.error("Data source not found. Please check 'drawing_master.xlsx'.")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    
    for i, tab in enumerate(tabs):
        with tab:
            # --- 1. REVISION FILTER (화면 중앙까지만 배치) ---
            st.markdown('<div class="section-header">REVISION FILTER</div>', unsafe_allow_html=True)
            
            # 버튼들이 중앙까지만 오도록 비율 설정 (총 합 12 중 7 사용)
            r_cols = st.columns([1, 1, 1, 1, 1, 1, 6])
            rev_list = ["LATEST", "C01", "C01A", "C01B", "C02", "VOID"]
            
            sel_rev_key = f"sel_rev_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"

            for idx, r_name in enumerate(rev_list):
                is_active = st.session_state[sel_rev_key] == r_name
                if r_cols[idx].button(r_name, key=f"rev_btn_{i}_{idx}", 
                                      type="primary" if is_active else "secondary", 
                                      use_container_width=True):
                    st.session_state[sel_rev_key] = r_name
                    st.rerun()

            # --- 2. SEARCH & FILTERS (화면 2/3 지점까지만 배치) ---
            st.markdown('<div class="section-header">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            # 총 합 15 중 10 사용 (약 66%)
            s_col1, s_col2, s_col3, s_col4, s_spacer = st.columns([4, 2, 2, 2, 5])
            
            with s_col1: st.text_input("Search", key=f"q_{i}", placeholder="Search...", label_visibility="collapsed")
            with s_col2: st.selectbox("System", ["All Systems"], key=f"sys_{i}", label_visibility="collapsed")
            with s_col3: st.selectbox("Area", ["All Areas"], key=f"area_{i}", label_visibility="collapsed")
            with s_col4: st.selectbox("Status", ["All Status"], key=f"stat_{i}", label_visibility="collapsed")

            # --- 3. ACTION TOOLBAR ---
            st.write(f"**Total Found: {len(df):,} records**")
            b_cols = st.columns([6, 1, 1, 1, 1])
            
            # Upload 토글 상태 관리
            up_key = f"show_upload_{i}"
            if b_cols[1].button("📁 Upload", key=f"up_btn_{i}", use_container_width=True):
                st.session_state[up_key] = not st.session_state.get(up_key, False)

            # PDF Sync 버튼 (동작 시뮬레이션)
            if b_cols[2].button("📄 PDF Sync", key=f"sync_{i}", use_container_width=True):
                st.success("PDF Repository Synchronized Successfully!")

            # Export & Print
            b_cols[3].button("📤 Export", key=f"ex_{i}", use_container_width=True)
            if b_cols[4].button("🖨️ Print", key=f"prt_{i}", use_container_width=True):
                components.html("<script>window.parent.print();</script>", height=0)

            # --- 4. IMPROVED UPLOAD INTERFACE (Drag & Drop + Save) ---
            if st.session_state.get(up_key, False):
                with st.container(border=True):
                    st.info("최신 Drawing List(Excel)를 아래 영역에 드래그하여 업로드하십시오.")
                    uploaded_file = st.file_uploader("Choose a file", type=['xlsx'], key=f"file_drop_{i}", label_visibility="collapsed")
                    
                    if uploaded_file:
                        st.success(f"File '{uploaded_file.name}' ready to be processed.")
                        u_col1, u_col2 = st.columns([2, 8])
                        if u_col1.button("💾 Save & Change", key=f"save_btn_{i}", type="primary", use_container_width=True):
                            # 실제 저장 로직 (데이터 덮어쓰기 등) 시뮬레이션
                            st.toast("Data has been updated successfully!", icon="💾")
                            st.session_state[up_key] = False # 업로드 창 닫기
                            st.rerun()

            # --- 5. DATA TABLE (🔍 View 아이콘 적용) ---
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True, 
                height=500,
                column_config={
                    "Drawing": st.column_config.LinkColumn("View", display_text="🔍 View")
                }
            )

if __name__ == "__main__":
    main()
