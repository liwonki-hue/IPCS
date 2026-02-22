import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Configuration
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
    """최신 리비전 정보를 추출합니다."""
    for r, d, m in [('3rd REV', '3rd DATE', '3rd REMARK'), 
                    ('2nd REV', '2nd DATE', '2nd REMARK'), 
                    ('1st REV', '1st DATE', '1st REMARK')]:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            rem = row.get(m, "")
            rem = "" if pd.isna(rem) or str(rem).lower() == "none" else str(rem)
            return val, row.get(d, '-'), rem
    return '-', '-', ''

def apply_professional_style():
    """전문적인 스타일 및 테이블 줄바꿈 설정을 적용합니다."""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* 탭 스타일 조정 */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            height: 40px; white-space: pre; background-color: #f8f9fb;
            border-radius: 4px 4px 0 0; padding: 0 20px; font-weight: 600;
        }
        .stTabs [aria-selected="true"] { background-color: #1657d0 !important; color: white !important; }

        /* 버튼 디자인 */
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 4px; border: 1px solid #dde3ec;
            height: 32px !important; font-size: 12px !important; font-weight: 600 !important;
            padding: 0 10px !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }
        
        /* 표 내부 줄바꿈 및 가독성 */
        div[data-testid="stDataFrame"] [role="gridcell"] {
            white-space: normal !important;
            word-wrap: break-word !important;
            line-height: 1.4 !important;
        }
        div[data-testid="stDataFrame"] [role="gridcell"] div { font-size: 15px !important; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(display_df, tab_name):
    """공통 테이블 및 필터 렌더링 함수"""
    # 1. Revision Filter (왼쪽 1/2 배치)
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    filter_key = f"sel_rev_{tab_name}"
    if filter_key not in st.session_state: st.session_state[filter_key] = "LATEST"
    
    rev_outer_col, _ = st.columns([1, 1]) 
    with rev_outer_col:
        rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
        rev_inner_cols = st.columns(len(rev_list[:7]))
        for i, rev in enumerate(rev_list[:7]):
            count = len(display_df) if rev == "LATEST" else display_df['Rev'].value_counts().get(rev, 0)
            if rev_inner_cols[i].button(f"{rev}({count})", key=f"btn_{tab_name}_{rev}", 
                                        type="primary" if st.session_state[filter_key] == rev else "secondary", 
                                        use_container_width=True):
                st.session_state[filter_key] = rev
                st.rerun()

    # 필터 적용
    final_df = display_df if st.session_state[filter_key] == "LATEST" else display_df[display_df['Rev'] == st.session_state[filter_key]]

    # 2. Action Toolbar
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    info_col, btn_area = st.columns([2, 1])
    with info_col:
        st.markdown(f"**Total: {len(final_df):,} records** ({tab_name})")
    
    with btn_area:
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Upload Excel", key=f"up_{tab_name}", use_container_width=True)
        with b2: st.button("📄 PDF", key=f"pdf_{tab_name}", use_container_width=True)
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False)
            st.download_button("📤 Export Excel", data=export_out.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
        with b4: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # 3. Data Viewport
    st.dataframe(
        final_df, 
        use_container_width=True, 
        hide_index=True, 
        height=650,
        column_config={
            "Category": st.column_config.TextColumn("Category", width=70),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=70),
            "Hold": st.column_config.TextColumn("Hold", width=50),
            "Status": st.column_config.TextColumn("Status", width=70),
            "Rev": st.column_config.TextColumn("Rev", width=60),
            "Date": st.column_config.TextColumn("Date", width=90),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"),
            "Remark": st.column_config.TextColumn("Remark", width="medium")
        }
    )

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("데이터베이스를 찾을 수 없습니다.")
        return

    # 데이터 로드 및 전처리
    df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'),
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date,
            "Hold": row.get('HOLD Y/N', 'N'), "Status": row.get('Status', '-'),
            "Remark": l_rem
        })
    master_df = pd.DataFrame(p_data)

    # 탭 구성
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])

    with tabs[0]: # Master
        render_drawing_table(master_df, "Master")

    with tabs[1]: # ISO
        iso_df = master_df[master_df['Category'].str.contains('ISO', case=False, na=False)]
        render_drawing_table(iso_df, "ISO")

    with tabs[2]: # Support
        sup_df = master_df[master_df['Category'].str.contains('Support', case=False, na=False)]
        render_drawing_table(sup_df, "Support")

    with tabs[3]: # Valve
        val_df = master_df[master_df['Category'].str.contains('Valve', case=False, na=False)]
        render_drawing_table(val_df, "Valve")

    with tabs[4]: # Specialty
        spec_df = master_df[master_df['Category'].str.contains('Specialty|Speciality', case=False, na=False)]
        render_drawing_table(spec_df, "Specialty")
