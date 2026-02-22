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

def apply_fixed_professional_ui():
    """레이아웃 사이즈 복구 및 테마 컬러 고정 (Green Theme)"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding: 1.0rem 2.0rem !important; }
        
        /* Title Size Recovery (24px) */
        .main-title { font-size: 24px !important; font-weight: 800; color: #1657d0; margin-bottom: 12px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; text-transform: uppercase; margin-bottom: 5px; }

        /* Button Style & Color (Green #0c7a3d) */
        div.stButton > button {
            border-radius: 3px; border: 1px solid #dde3ec;
            height: 30px !important; font-size: 12px !important; font-weight: 600 !important;
        }
        /* Selected Filter Color: Reset from Red to Green */
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; border: none !important; }

        /* Table Data Style (18px, Center) */
        div[data-testid="stDataFrame"] [role="gridcell"] div {
            font-size: 18px !important; text-align: center !important;
            justify-content: center !important; display: flex !important; align-items: center !important;
        }
        div[data-testid="stDataFrame"] [role="columnheader"] p {
            font-size: 18px !important; font-weight: 800 !important;
        }
        
        /* Uploader Compact View */
        div[data-testid="stFileUploader"] { padding-bottom: 0px !important; }
        div[data-testid="stFileUploader"] section { padding: 0 !important; min-height: 30px !important; }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_fixed_professional_ui()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    # 1. Data Loading
    if not os.path.exists(DB_PATH):
        st.error("Error: Database file not found.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    
    # 2. Validation (English Message)
    dup_nos = df[df.duplicated(subset=['DWG. NO.'], keep=False)]['DWG. NO.'].unique()
    if len(dup_nos) > 0:
        st.warning(f"⚠️ Duplicate Drawing No. Detected: {', '.join(map(str, dup_nos))}")

    p_data = []
    for _, row in df.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date,
            "Hold": row.get('HOLD Y/N', 'N'), "Status": row.get('Status', '-'),
            "Remark": l_rem, "AREA": row.get('AREA', '-'), "SYSTEM": row.get('SYSTEM', '-')
        })
    f_df = pd.DataFrame(p_data)

    # 3. Revision Filter (Micro buttons)
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    rev_counts = f_df['Rev'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    rev_cols = st.columns(12)
    for i, rev in enumerate(target_revs[:12]):
        count = len(f_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        if rev_cols[i].button(f"{rev}({count})", key=f"r_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # 4. Search & Filter
    st.markdown("<div style='margin-top:8px;' class='section-label'>Search & Filter</div>", unsafe_allow_html=True)
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
    with s1: search_q = st.text_input("S", placeholder="🔍 Search Drawing...", label_visibility="collapsed")
    with s2: a_sel = st.multiselect("A", options=sorted(work_df['AREA'].unique()), placeholder="Area", label_visibility="collapsed")
    with s3: y_sel = st.multiselect("Y", options=sorted(work_df['SYSTEM'].unique()), placeholder="System", label_visibility="collapsed")
    with s4: t_sel = st.multiselect("T", options=sorted(work_df['Status'].unique()), placeholder="Status", label_visibility="collapsed")

    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]
    if search_q: work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | work_df['Description'].str.contains(search_q, case=False, na=False)]

    # 5. Action Toolbar (Upload Stability Enhancement)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    res_col, btn_col = st.columns([6, 4])
    with res_col:
        st.markdown(f"<div style='font-size:14px; font-weight:600; color:#374559;'>Total: {len(work_df):,} items</div>", unsafe_allow_html=True)
    
    with btn_col:
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            # Infinite Loop Fix: Unique key with file_uploader
            uploaded_file = st.file_uploader("Up", type=['xlsx'], key="db_uploader_final", label_visibility="collapsed")
            if uploaded_file is not None:
                with open(DB_PATH, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                # Success Notification
                st.toast("✅ Database Successfully Updated!")
                # Immediate Rerun to clear uploader state
                st.rerun()
        with b2: st.button("📄 PDF", use_container_width=True)
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                work_df.to_excel(writer, index=False)
            st.download_button("📤 Ex", data=export_out.getvalue(), file_name="Dwg_Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Prt", use_container_width=True)

    # 6. Main Data Table
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, hide_index=True, height=720,
        column_config={"Description": st.column_config.TextColumn("Description", width="max")}
    )
