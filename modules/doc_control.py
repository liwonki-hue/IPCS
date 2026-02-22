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

def apply_professional_layout():
    """Restores the UI layout, ensuring title visibility and green theme."""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding: 1.5rem 2.0rem !important; background-color: #ffffff !important; }
        
        /* Fixed Title Style */
        .main-title { 
            font-size: 24px !important; font-weight: 800; color: #1657d0 !important; 
            margin-bottom: 12px !important; display: block !important; 
            border-bottom: 1.5px solid #f0f2f6; padding-bottom: 8px;
        }
        
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; text-transform: uppercase; margin-bottom: 6px; }

        /* Button & Filter Design (Fixed width to prevent oversized buttons) */
        div.stButton > button {
            border-radius: 4px; border: 1px solid #dde3ec;
            height: 28px !important; font-size: 11px !important; font-weight: 600 !important;
            padding: 0 10px !important;
        }
        
        /* Revision Filter specific sizing: Limit button stretch */
        [data-testid="column"] div.stButton > button {
            max-width: 120px !important; 
        }

        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }

        /* DataFrame Table Customization (18px) */
        div[data-testid="stDataFrame"] [role="gridcell"] div { font-size: 18px !important; }
        div[data-testid="stDataFrame"] [role="columnheader"] p { font-size: 18px !important; font-weight: 800 !important; }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Update Master Database")
def open_upload_dialog():
    st.info("Select the latest Excel file to update the database.")
    new_file = st.file_uploader("Upload File", type=['xlsx'], key="modal_uploader_v2")
    if new_file:
        with open(DB_PATH, "wb") as f:
            f.write(new_file.getbuffer())
        st.success("Database updated.")
        if st.button("Apply & Close"):
            st.rerun()

def show_doc_control():
    apply_professional_layout()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Fatal Error: 'drawing_master.xlsx' not found.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    
    # Duplicate Warning
    dup_nos = df[df.duplicated(subset=['DWG. NO.'], keep=False)]['DWG. NO.'].unique()
    if len(dup_nos) > 0:
        st.warning(f"⚠️ Duplicate Drawing No. Detected: {', '.join(map(str, dup_nos))}")

    p_data = []
    for _, row in df.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'), "Rev": l_rev, "Date": l_date,
            "Hold": row.get('HOLD Y/N', 'N'), "Status": row.get('Status', '-'),
            "Remark": l_rem, "AREA": row.get('AREA', '-'), "SYSTEM": row.get('SYSTEM', '-')
        })
    f_df = pd.DataFrame(p_data)

    # --- [수정] Revision Filter (화면 왼쪽 절반만 차지하도록 제한) ---
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    # 화면을 1:1로 나누어 왼쪽 컬럼만 사용
    filter_area, spacer = st.columns([1, 1]) 
    with filter_area:
        rev_cols = st.columns(len(target_revs[:8])) # 한 줄에 최대 8개까지만 배치
        for i, rev in enumerate(target_revs[:8]):
            count = len(f_df) if rev == "LATEST" else f_df['Rev'].value_counts().get(rev, 0)
            if rev_cols[i].button(f"{rev}({count})", key=f"r_{rev}", 
                                  type="primary" if st.session_state.sel_rev == rev else "secondary", 
                                  use_container_width=True):
                st.session_state.sel_rev = rev
                st.rerun()

    # Search & Filter
    st.markdown("<div class='section-label' style='margin-top:10px;'>SEARCH & FILTER</div>", unsafe_allow_html=True)
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
    with s1: search_q = st.text_input("S", placeholder="🔍 Search Drawing...", label_visibility="collapsed")
    with s2: a_sel = st.multiselect("A", options=sorted(work_df['AREA'].unique()), placeholder="Area", label_visibility="collapsed")
    with s3: y_sel = st.multiselect("Y", options=sorted(work_df['SYSTEM'].unique()), placeholder="System", label_visibility="collapsed")
    with s4: t_sel = st.multiselect("T", options=sorted(work_df['Status'].unique()), placeholder="Status", label_visibility="collapsed")

    if search_q: work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | work_df['Description'].str.contains(search_q, case=False, na=False)]
    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]

    # Action Toolbar
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    res_col, btn_col = st.columns([6, 4])
    with res_col:
        st.markdown(f"<div style='font-size:14px; font-weight:600;'>Total Count: {len(work_df):,} items</div>", unsafe_allow_html=True)
    
    with btn_col:
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("📁 Up", use_container_width=True):
                open_upload_dialog()
        with b2: st.button("📄 PDF", use_container_width=True)
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                work_df.to_excel(writer, index=False)
            st.download_button("📤 Ex", data=export_out.getvalue(), file_name="Dwg_Master_Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Prt", use_container_width=True)

    # Main Data Table
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, hide_index=True, height=750
    )
