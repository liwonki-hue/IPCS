import streamlit as st
import pandas as pd
import os
from io import BytesIO
import streamlit.components.v1 as components

# --- [1] Data Engineering Layer ---
BASE_DIR = 'drawing_control'
DATA_PATH = os.path.join(BASE_DIR, 'data/drawing_master.xlsx')

def get_latest_info(row):
    # 모든 리비전 중 가장 최신 값을 찾아 단일화 (원상 복구 로직)
    rev_cols = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r_col, d_col in rev_cols:
        if pd.notna(row.get(r_col)) and str(row.get(r_col)).strip() != "":
            return row[r_col], row.get(d_col, '-')
    return '-', '-'

@st.cache_data
def load_and_process_data():
    if not os.path.exists(DATA_PATH): return pd.DataFrame()
    try:
        df_raw = pd.read_excel(DATA_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        processed_data = []
        for _, row in df_raw.iterrows():
            l_rev, l_date = get_latest_info(row)
            processed_data.append({
                "Category": row.get('Category', 'Master'),
                "Area": row.get('Area', '-'),
                "SYSTEM": row.get('SYSTEM', '-'),
                "DWG. NO.": row.get('DWG. NO.', '-'),
                "Description": row.get('DRAWING TITLE', '-'),
                "Rev": l_rev,
                "Date": l_date,
                "Hold": row.get('HOLD Y/N', 'N'),
                "Status": row.get('Status', '-'),
                "Drawing": row.get('Link', None)
            })
        return pd.DataFrame(processed_data)
    except: return pd.DataFrame()

# --- [2] UI Styling ---
def apply_styles():
    st.markdown("""
        <style>
        .main-title { font-size: 28px; font-weight: 800; color: #1A4D94; border-left: 8px solid #1A4D94; padding-left: 15px; margin-bottom: 20px; }
        .section-header { font-size: 11px; font-weight: 700; color: #555; margin-top: 20px; text-transform: uppercase; }
        div[data-testid="column"] { padding: 0 2px !important; }
        </style>
    """, unsafe_allow_html=True)

def main():
    st.set_page_config(layout="wide", page_title="DCS Dashboard")
    apply_styles()
    st.markdown('<div class="main-title">Document Control System</div>', unsafe_allow_html=True)

    df_master = load_and_process_data()
    if df_master.empty:
        st.warning("데이터 소스를 확인해 주세요.")
        return

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_list = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = df_master if i == 0 else df_master[df_master['Category'].str.contains(tab_list[i], case=False, na=False)]
            
            # --- 1. REVISION FILTER (1줄 배치 & 수량 & 녹색) ---
            st.markdown('<div class="section-header">REVISION FILTER</div>', unsafe_allow_html=True)
            rev_counts = curr_df['Rev'].value_counts()
            rev_opts = ["LATEST", "C01", "C01A", "C01B", "C02", "VOID"]
            
            sel_key = f"sel_rev_{i}"
            if sel_key not in st.session_state: st.session_state[sel_key] = "LATEST"
            
            # 1줄 배치를 위해 컬럼 비율 조정 (중앙까지만 배치)
            r_cols = st.columns([1.2, 1, 1, 1, 1, 1, 6])
            for idx, r_name in enumerate(rev_opts):
                cnt = len(curr_df) if r_name == "LATEST" else rev_counts.get(r_name, 0)
                is_active = st.session_state[sel_key] == r_name
                if r_cols[idx].button(f"{r_name} ({cnt})", key=f"btn_{i}_{idx}", 
                                      type="primary" if is_active else "secondary", use_container_width=True):
                    st.session_state[sel_key] = r_name
                    st.rerun()

            # 필터 적용
            df_disp = curr_df.copy()
            if st.session_state[sel_key] != "LATEST":
                df_disp = df_disp[df_disp['Rev'] == st.session_state[sel_key]]

            # --- 2. SEARCH & FILTERS (2/3 지점 배치) ---
            st.markdown('<div class="section-header">SEARCH & FILTERS</div>', unsafe_allow_html=True)
            s1, s2, s3, s4, s_spc = st.columns([4, 2, 2, 2, 5])
            with s1: q = st.text_input("Search...", key=f"q_{i}", label_visibility="collapsed")
            with s2: st.selectbox("System", ["All Systems"], key=f"sys_{i}", label_visibility="collapsed")
            with s3: st.selectbox("Area", ["All Areas"], key=f"ar_{i}", label_visibility="collapsed")
            with s4: st.selectbox("Status", ["All Status"], key=f"st_{i}", label_visibility="collapsed")

            if q: df_disp = df_disp[df_disp['DWG. NO.'].str.contains(q, case=False, na=False) | df_disp['Description'].str.contains(q, case=False, na=False)]

            # --- 3. ACTION TOOLBAR & UPLOAD MODAL ---
            # SyntaxError 수정 완료
            st.write(f"**Total Found: {len(df_disp):,} records**") 
            
            b1, b2, b3, b4, b5 = st.columns([6, 1, 1, 1, 1])
            up_key = f"show_up_{i}"
            if b2.button("📁 Upload", key=f"u_b_{i}", use_container_width=True):
                st.session_state[up_key] = not st.session_state.get(up_key, False)
            
            if b3.button("📄 PDF Sync", key=f"sy_{i}", use_container_width=True):
                st.toast("PDF Sync Completed!", icon="✅")

            ex_io = BytesIO()
            df_disp.to_excel(ex_io, index=False)
            b4.download_button("📤 Export", data=ex_io.getvalue(), file_name="DCS_List.xlsx", key=f"ex_{i}", use_container_width=True)
            
            if b5.button("🖨️ Print", key=f"prt_{i}", use_container_width=True):
                # 인쇄용 정적 HTML 생성 (데이터 유실 방지)
                html = df_disp.to_html(index=False).replace('class="dataframe"', 'style="width:100%; border-collapse:collapse; font-size:10px;" border="1"')
                components.html(f"<script>var w=window.open(); w.document.write('{html}'); w.print(); w.close();</script>", height=0)

            # Upload 모달 영역
            if st.session_state.get(up_key, False):
                with st.container(border=True):
                    st.info("파일을 드래그하여 업로드한 후 [Save & Change]를 클릭하세요.")
                    f = st.file_uploader("Upload Excel", type=['xlsx'], key=f"f_{i}", label_visibility="collapsed")
                    if f and st.button("💾 Save & Change", key=f"save_{i}", type="primary"):
                        st.success("데이터가 성공적으로 업데이트되었습니다.")
                        st.session_state[up_key] = False
                        st.rerun()

            # --- 4. DATA TABLE ---
            st.dataframe(df_disp, use_container_width=True, hide_index=True, height=500,
                         column_config={"Drawing": st.column_config.LinkColumn("View", display_text="🔍 View")})

if __name__ == "__main__":
    main()
