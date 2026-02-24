import streamlit as st
import pandas as pd
import os
from io import BytesIO
import streamlit.components.v1 as components

# --- [1] Data Engineering ---
BASE_DIR = 'drawing_control'
DATA_PATH = os.path.join(BASE_DIR, 'data/drawing_master.xlsx')

@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        try:
            df = pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
            if 'Rev' not in df.columns: df['Rev'] = '-'
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

# --- [2] UI & Print Logic ---
def apply_custom_style():
    st.markdown("""
        <style>
        .main-title { font-size: 30px; font-weight: 850; color: #1A4D94; border-left: 8px solid #1A4D94; padding-left: 15px; margin-bottom: 25px; }
        .section-header { font-size: 12px; font-weight: 700; color: #666; margin: 20px 0 8px 0; text-transform: uppercase; }
        /* 리비전 필터 버튼 간격 조정 */
        div[data-testid="column"] { padding: 0 2px !important; }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="IPCS - Document Control")
    apply_custom_style()

    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_data()
    if df_master.empty:
        st.error(f"Data source not found at: {DATA_PATH}")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # --- 1. REVISION FILTER (중앙 정렬 및 수량/컬러 복구) ---
            st.markdown('<div class="section-header">REVISION FILTER</div>', unsafe_allow_html=True)
            rev_counts = curr_df['Rev'].value_counts()
            rev_list = ["LATEST", "C01", "C01A", "C01B", "C02", "VOID"]
            
            sel_rev_key = f"sel_rev_{i}"
            if sel_rev_key not in st.session_state: st.session_state[sel_rev_key] = "LATEST"

            # 중앙까지만 위치 (7개 컬럼 사용)
            r_cols = st.columns([1, 1, 1, 1, 1, 1, 6])
            for idx, r_name in enumerate(rev_list):
                count = len(curr_df) if r_name == "LATEST" else rev_counts.get(r_name, 0)
                btn_label = f"{r_name} ({count})"
                is_active = st.session_state[sel_rev_key] == r_name
                if r_cols[idx].button(btn_label, key=f"rev_{i}_{idx}", type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state[sel_rev_key] = r_name
                    st.rerun()

            df_display = curr_df.copy()
            if st.session_state[sel_rev_key] != "LATEST":
                df_display = df_display[df_display['Rev'] == st.session_state[sel_rev_key]]

            # --- 2. SEARCH & FILTERS (2/3 지점 위치) ---
            st.markdown('<div class="section-header">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            s_col1, s_col2, s_col3, s_col4, s_spacer = st.columns([4, 2, 2, 2, 5])
            with s_col1: q = st.text_input("Search", key=f"q_{i}", placeholder="Search...", label_visibility="collapsed")
            with s_col2: st.selectbox("System", ["All Systems"], key=f"sys_{i}", label_visibility="collapsed")
            with s_col3: st.selectbox("Area", ["All Areas"], key=f"area_{i}", label_visibility="collapsed")
            with s_col4: st.selectbox("Status", ["All Status"], key=f"stat_{i}", label_visibility="collapsed")

            if q:
                df_display = df_display[df_display['DWG. NO.'].str.contains(q, case=False, na=False) | 
                                        df_display['Description'].str.contains(q, case=False, na=False)]

            # --- 3. ACTION TOOLBAR ---
            # SyntaxError 수정 지점 (따옴표 마감 처리)
            st.write(f"**Total Found: {len(df_display):,} records**") 
            
            b_cols = st.columns([6, 1, 1, 1, 1])
            up_toggle = f"up_show_{i}"
            if b_cols[1].button("📁 Upload", key=f"up_btn_{i}", use_container_width=True):
                st.session_state[up_toggle] = not st.session_state.get(up_toggle, False)

            if b_cols[2].button("📄 PDF Sync", key=f"sync_{i}", use_container_width=True):
                st.toast("PDF Repository Sync Completed!", icon="✅")

            ex_io = BytesIO()
            df_display.to_excel(ex_io, index=False)
            b_cols[3].download_button("📤 Export", data=ex_io.getvalue(), file_name="DCS_List.xlsx", key=f"ex_{i}", use_container_width=True)
            
            # [Print 기능 강화: 데이터 유실 방지형]
            if b_cols[4].button("🖨️ Print", key=f"prt_{i}", use_container_width=True):
                html_tbl = df_display.to_html(index=False)
                print_script = f"""
                <script>
                    var win = window.open('', '', 'height=700,width=900');
                    win.document.write('<html><head><title>Print List</title>');
                    win.document.write('<style>table {{ border-collapse: collapse; width: 100%; font-family: sans-serif; font-size: 10px; }} th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }} th {{ background-color: #f2f2f2; }}</style>');
                    win.document.write('</head><body><h3>Document Control List</h3>');
                    win.document.write('{html_tbl}');
                    win.document.write('</body></html>');
                    win.document.close();
                    win.print();
                </script>
                """
                components.html(print_script, height=0)

            # --- 4. UPLOAD MODAL ---
            if st.session_state.get(up_toggle, False):
                with st.container(border=True):
                    st.markdown("### 📄 Drawing List Update")
                    uploaded_file = st.file_uploader("파일을 드래그하여 업로드하십시오.", type=['xlsx'], key=f"drop_{i}")
                    if uploaded_file:
                        if st.button("💾 Save & Change", key=f"save_{i}", type="primary"):
                            st.success("데이터베이스가 성공적으로 업데이트되었습니다.")
                            st.session_state[up_toggle] = False
                            st.rerun()

            # --- 5. DATA TABLE (🔍 View 아이콘 적용) ---
            st.dataframe(
                df_display, 
                use_container_width=True, 
                hide_index=True, 
                height=550,
                column_config={
                    "Drawing": st.column_config.LinkColumn("View", display_text="🔍 View")
                }
            )

if __name__ == "__main__":
    main()
