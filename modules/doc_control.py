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
    """상단 가독성 확보 및 컴팩트 버튼 스타일 CSS"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 5rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; }
        .section-label { font-size: 10px !important; font-weight: 700; color: #6b7a90; margin-bottom: 5px; text-transform: uppercase; }
        
        /* Buttons Style */
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 4px; border: 1px solid #dde3ec;
            height: 30px !important; font-size: 10px !important; font-weight: 600 !important;
            padding: 0 4px !important; white-space: nowrap !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }
        
        /* Table Font (18px) */
        div[data-testid="stDataFrame"] [role="gridcell"] div { font-size: 18px !important; }
        div[data-testid="stDataFrame"] [role="columnheader"] p { font-size: 18px !important; font-weight: 800 !important; }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Manage Duplicates")
def open_duplicate_manager(df):
    """중복 도면 검토 및 삭제 다이얼로그"""
    dup_mask = df.duplicated(subset=['DWG. NO.'], keep=False)
    dupes = df[dup_mask].sort_values('DWG. NO.')
    
    st.write(f"총 **{len(dupes)}**개의 중복 데이터가 발견되었습니다.")
    st.dataframe(dupes[['Category', 'SYSTEM', 'DWG. NO.', 'Status']], use_container_width=True, hide_index=True)
    
    st.warning("중복 삭제 시, 동일 번호 중 '가장 아래(최신)'에 위치한 행만 남기고 나머지는 영구 삭제됩니다.")
    if st.button("Confirm & Clean Duplicates", type="primary", use_container_width=True):
        clean_df = df.drop_duplicates(subset=['DWG. NO.'], keep='last')
        with pd.ExcelWriter(DB_PATH, engine='openpyxl') as writer:
            clean_df.to_excel(writer, sheet_name='DRAWING LIST', index=False)
        st.success("Duplicates removed successfully.")
        st.rerun()

@st.dialog("Upload & Merge Database")
def open_upload_dialog():
    st.info("새로운 서포트 도면을 업로드하여 병합하거나 전체를 교체할 수 있습니다.")
    upload_mode = st.radio("Upload Mode", ["Append (추가)", "Replace (교체)"], horizontal=True)
    new_file = st.file_uploader("Choose Excel File", type=['xlsx'])

    if new_file:
        new_df = pd.read_excel(new_file, sheet_name='DRAWING LIST')
        if upload_mode == "Append (추가)" and os.path.exists(DB_PATH):
            old_df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST')
            final_df = pd.concat([old_df, new_df], ignore_index=True)
        else:
            final_df = new_df
        
        with pd.ExcelWriter(DB_PATH, engine='openpyxl') as writer:
            final_df.to_excel(writer, sheet_name='DRAWING LIST', index=False)
        st.success("Upload Completed.")
        st.rerun()

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("Database file not found.")
        return

    # 1. 데이터 로드 및 중복 검사
    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    dup_list = df[df.duplicated(subset=['DWG. NO.'], keep=False)]['DWG. NO.'].unique()

    if len(dup_list) > 0:
        c1, c2 = st.columns([8, 2])
        with c1:
            st.warning(f"⚠️ 중복 도면 번호 검출 ({len(dup_list)}건): {', '.join(map(str, dup_list[:3]))}...")
        with c2:
            if st.button("🛠️ 중복 관리/삭제", use_container_width=True):
                open_duplicate_manager(df)

    # 2. 데이터 가공 (컬럼 재배치 포함)
    p_data = []
    for _, row in df.iterrows():
        l_rev, l_date, l_rem = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'),
            "SYSTEM": row.get('SYSTEM', '-'),  # 요청에 따라 Category 다음으로 이동
            "DWG. NO.": row.get('DWG. NO.', '-'),
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev,
            "Date": l_date,
            "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'),
            "Remark": l_rem,
            "AREA": row.get('AREA', '-')
        })
    f_df = pd.DataFrame(p_data)

    # 3. UI - Revision Filter
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    rev_area, _ = st.columns([1, 1])
    with rev_area:
        target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
        rev_cols = st.columns(len(target_revs[:7]))
        for i, rev in enumerate(target_revs[:7]):
            count = len(f_df) if rev == "LATEST" else f_df['Rev'].value_counts().get(rev, 0)
            if rev_cols[i].button(f"{rev}({count})", key=f"r_{rev}", 
                                  type="primary" if st.session_state.sel_rev == rev else "secondary", 
                                  use_container_width=True):
                st.session_state.sel_rev = rev
                st.rerun()

    # 4. Action Toolbar & Data Table
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    res_col, btn_area = st.columns([2, 1])
    
    with res_col:
        st.markdown(f"<div style='font-size:13px; font-weight:600; padding-top:8px;'>Total Count: {len(f_df):,} items</div>", unsafe_allow_html=True)
    
    with btn_area:
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("📁 Upload Excel", use_container_width=True): open_upload_dialog()
        with b2: st.button("📄 PDF", use_container_width=True)
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                f_df.to_excel(writer, index=False)
            st.download_button("📤 Export Excel", data=export_out.getvalue(), file_name="Dwg_Master.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Print", use_container_width=True)

    # 컬럼 순서 최종 정의 (Category -> SYSTEM -> DWG. NO.)
    display_cols = ["Category", "SYSTEM", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]
    st.dataframe(f_df[display_cols], use_container_width=True, hide_index=True, height=700)
