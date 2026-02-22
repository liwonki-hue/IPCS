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

def apply_fixed_header_ui():
    """타이틀 가시성 확보 및 UI 테마 고정"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        /* 상단 여백 확보 및 배경색 고정 */
        .block-container { padding: 1.0rem 2.0rem !important; background-color: #f7f9fc !important; }
        
        /* Title: 강제 노출 및 위치 고정 */
        .main-title { 
            font-size: 24px !important; font-weight: 800; color: #1657d0 !important; 
            margin: 0 0 10px 0 !important; display: block !important;
            line-height: 1.2 !important;
        }
        
        /* Alert Box: 타이틀 아래로 간격 조정 */
        .stAlert { margin-top: 5px !important; margin-bottom: 15px !important; border-radius: 4px !important; }

        /* Button & Filter: 전문적인 디자인 유지 */
        div.stButton > button {
            border-radius: 3px; border: 1px solid #dde3ec;
            height: 32px !important; font-size: 11px !important; font-weight: 600 !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }

        /* Table Font: 18px Center */
        div[data-testid="stDataFrame"] [role="gridcell"] div { font-size: 18px !important; }
        div[data-testid="stDataFrame"] [role="columnheader"] p { font-size: 18px !important; font-weight: 800 !important; }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Upload Master Database")
def show_upload_dialog():
    """업로드 전용 별도 팝업 창"""
    st.write("Please select the updated Excel file (.xlsx) to refresh the database.")
    new_file = st.file_uploader("Drag and drop file here", type=['xlsx'], key="modal_uploader")
    
    if new_file:
        try:
            with open(DB_PATH, "wb") as f:
                f.write(new_file.getbuffer())
            st.success("Database successfully updated!")
            if st.button("Close and Refresh"):
                st.rerun()
        except Exception as e:
            st.error(f"Upload Error: {e}")

def show_doc_control():
    # 1. UI 및 타이틀 렌더링 (최우선 순위)
    apply_fixed_header_ui()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    # 2. 데이터 로드 및 중복 검사
    if not os.path.exists(DB_PATH):
        st.error("Error: Database file (drawing_master.xlsx) not found.")
        return

    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    
    # 중복 도면 번호 알림 (타이틀 바로 아래 배치)
    dup_nos = df[df.duplicated(subset=['DWG. NO.'], keep=False)]['DWG. NO.'].unique()
    if len(dup_nos) > 0:
        st.warning(f"⚠️ Duplicate Drawing No. Detected: {', '.join(map(str, dup_nos))}")

    # 데이터 정제 (f_df 생성)
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

    # 3. Revision Filter
    st.markdown("<div style='font-size:11px; font-weight:700; color:#6b7a90; margin-bottom:5px;'>REVISION FILTER</div>", unsafe_allow_html=True)
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    rev_cols = st.columns(12)
    for i, rev in enumerate(target_revs[:12]):
        count = len(f_df) if rev == "LATEST" else f_df['Rev'].value_counts().get(rev, 0)
        if rev_cols[i].button(f"{rev}({count})", key=f"r_{rev}", type="primary" if st.session_state.sel_rev == rev else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # 4. Search & Filter
    st.markdown("<div style='font-size:11px; font-weight:700; color:#6b7a90; margin-top:10px;'>SEARCH & FILTER</div>", unsafe_allow_html=True)
    work_df = f_df.copy()
    if st.session_state.sel_rev != "LATEST":
        work_df = work_df[work_df['Rev'] == st.session_state.sel_rev]

    s1, s2, s3, s4 = st.columns([4, 2, 2, 2])
    with s1: search_q = st.text_input("S", placeholder="🔍 Search Drawing...", label_visibility="collapsed")
    with s2: a_sel = st.multiselect("A", options=sorted(work_df['AREA'].unique()), placeholder="Area", label_visibility="collapsed")
    with s3: y_sel = st.multiselect("Y", options=sorted(work_df['SYSTEM'].unique()), placeholder="System", label_visibility="collapsed")
    with s4: t_sel = st.multiselect("T", options=sorted(work_df['Status'].unique()), placeholder="Status", label_visibility="collapsed")

    # Filter Logic
    if a_sel: work_df = work_df[work_df['AREA'].isin(a_sel)]
    if y_sel: work_df = work_df[work_df['SYSTEM'].isin(y_sel)]
    if t_sel: work_df = work_df[work_df['Status'].isin(t_sel)]
    if search_q: work_df = work_df[work_df['DWG. NO.'].str.contains(search_q, case=False, na=False) | work_df['Description'].str.contains(search_q, case=False, na=False)]

    # 5. Action Toolbar (Upload Modal Trigger)
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
    res_col, btn_col = st.columns([6, 4])
    with res_col:
        st.markdown(f"<div style='font-size:14px; font-weight:600; color:#374559;'>Total Count: {len(work_df):,}</div>", unsafe_allow_html=True)
    
    with btn_col:
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            # 클릭 시 별도의 다이얼로그(팝업) 창 호출
            if st.button("📁 Up", use_container_width=True):
                show_upload_dialog()
        with b2: st.button("📄 PDF", use_container_width=True)
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                work_df.to_excel(writer, index=False)
            st.download_button("📤 Ex", data=export_out.getvalue(), file_name="Dwg_Master_Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Prt", use_container_width=True)

    # 6. Main Data Table (18px)
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, hide_index=True, height=750
    )
