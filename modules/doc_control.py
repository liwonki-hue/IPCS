import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Configuration
DB_PATH = 'data/drawing_master.xlsx'

def get_latest_rev_info(row):
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
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-top: 15px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* Input & Selectbox Label styling */
        .stSelectbox label, .stTextInput label { font-size: 12px !important; font-weight: 700 !important; color: #4a5568 !important; }
        
        /* DataFrame Wrapping and Sizing */
        div[data-testid="stDataFrame"] [role="gridcell"] {
            white-space: normal !important;
            word-wrap: break-word !important;
            line-height: 1.4 !important;
        }
        div[data-testid="stDataFrame"] [role="gridcell"] div { font-size: 14px !important; }
        </style>
    """, unsafe_allow_html=True)

def render_drawing_table(display_df, tab_name):
    """Search 필터가 가장 왼쪽에 오도록 강제 정렬합니다."""
    
    # 1. Revision Filter (Upper Section)
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_outer_col, _ = st.columns([1, 1])
    with rev_outer_col:
        filter_key = f"sel_rev_{tab_name}"
        if filter_key not in st.session_state: st.session_state[filter_key] = "LATEST"
        
        rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
        rev_inner_cols = st.columns(len(rev_list[:7]))
        for i, rev in enumerate(rev_list[:7]):
            count = len(display_df) if rev == "LATEST" else display_df['Rev'].value_counts().get(rev, 0)
            if rev_inner_cols[i].button(f"{rev}({count})", key=f"btn_{tab_name}_{rev}", 
                                        type="primary" if st.session_state[filter_key] == rev else "secondary", 
                                        use_container_width=True):
                st.session_state[filter_key] = rev
                st.rerun()

    # 2. Search & Data Filters (Lower Section - horizontal alignment)
    st.markdown("<div class='section-label'>Filters & Search</div>", unsafe_allow_html=True)
    
    # 화면 왼쪽 절반을 다시 쪼개서 배치 (Search: 4, 나머지 필터: 각 2)
    filter_area_col, _ = st.columns([1, 1])
    with filter_area_col:
        # 이 내부에서 다시 columns를 나누어 Search를 가장 왼쪽으로 배치
        s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
        with s1:
            search_term = st.text_input("Search", key=f"search_{tab_name}", placeholder="DWG No. or Title...")
        with s2:
            systems = ["All"] + sorted(display_df['SYSTEM'].unique().tolist())
            sel_sys = st.selectbox("System", systems, key=f"sys_{tab_name}")
        with s3:
            areas = ["All"] + sorted(display_df['Category'].unique().tolist())
            sel_area = st.selectbox("Area/Cat", areas, key=f"area_{tab_name}")
        with s4:
            stats = ["All"] + sorted(display_df['Status'].unique().tolist())
            sel_stat = st.selectbox("Status", stats, key=f"stat_{tab_name}")

    # --- Filtering Logic ---
    filtered_df = display_df.copy()
    if sel_sys != "All": filtered_df = filtered_df[filtered_df['SYSTEM'] == sel_sys]
    if sel_area != "All": filtered_df = filtered_df[filtered_df['Category'] == sel_area]
    if sel_stat != "All": filtered_df = filtered_df[filtered_df['Status'] == sel_stat]
    if st.session_state[filter_key] != "LATEST":
        filtered_df = filtered_df[filtered_df['Rev'] == st.session_state[filter_key]]
    if search_term:
        filtered_df = filtered_df[
            filtered_df['DWG. NO.'].str.contains(search_term, case=False, na=False) |
            filtered_df['Description'].str.contains(search_term, case=False, na=False)
        ]

    # 3. Action Toolbar
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    info_col, btn_area = st.columns([2, 1])
    with info_col:
        st.markdown(f"**Total: {len(filtered_df):,} records**")
    
    with btn_area:
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Upload Excel", key=f"up_{tab_name}", use_container_width=True)
        with b2: st.button("📄 PDF", key=f"pdf_{tab_name}", use_container_width=True)
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False)
            st.download_button("📤 Export Excel", data=export_out.getvalue(), file_name=f"Dwg_{tab_name}.xlsx", key=f"ex_{tab_name}", use_container_width=True)
        with b4: st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True)

    # 4. Data Viewport
    st.dataframe(
        filtered_df, 
        use_container_width=True, 
        hide_index=True, 
        height=620,
        column_config={
            "Category": st.column_config.TextColumn("Category", width=80),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=80),
            "Hold": st.column_config.TextColumn("Hold", width=50),
            "Status": st.column_config.TextColumn("Status", width=80),
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
        st.error("Database file missing.")
        return

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

    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    with tabs[0]: render_drawing_table(master_df, "Master")
    with tabs[1]: render_drawing_table(master_df[master_df['Category'].str.contains('ISO', case=False, na=False)], "ISO")
    with tabs[2]: render_drawing_table(master_df[master_df['Category'].str.contains('Support', case=False, na=False)], "Support")
    with tabs[3]: render_drawing_table(master_df[master_df['Category'].str.contains('Valve', case=False, na=False)], "Valve")
    with tabs[4]: render_drawing_table(master_df[master_df['Category'].str.contains('Specialty|Speciality', case=False, na=False)], "Specialty")
