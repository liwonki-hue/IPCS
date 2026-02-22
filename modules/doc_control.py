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
    """기존 레이아웃 스타일 및 줄바꿈 설정을 적용합니다."""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        .block-container { padding-top: 5rem !important; padding-left: 1.5rem !important; padding-right: 1.5rem !important; }
        .main-title { font-size: 26px !important; font-weight: 800; color: #1657d0 !important; margin-bottom: 20px !important; border-bottom: 2px solid #f0f2f6; padding-bottom: 10px; }
        .section-label { font-size: 11px !important; font-weight: 700; color: #6b7a90; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* 버튼 스타일 유지 */
        div.stButton > button, div.stDownloadButton > button {
            border-radius: 4px; border: 1px solid #dde3ec;
            height: 32px !important; font-size: 12px !important; font-weight: 600 !important;
            padding: 0 10px !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }
        
        /* 표 내부 줄바꿈 및 폰트 설정 */
        div[data-testid="stDataFrame"] [role="gridcell"] {
            white-space: normal !important;
            word-wrap: break-word !important;
            line-height: 1.4 !important;
        }
        div[data-testid="stDataFrame"] [role="gridcell"] div { font-size: 15px !important; }
        div[data-testid="stDataFrame"] [role="columnheader"] p { font-size: 15px !important; font-weight: 800 !important; }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Manage Duplicates")
def open_duplicate_manager(df):
    """중복 데이터 관리 팝업 창입니다."""
    dup_mask = df.duplicated(subset=['DWG. NO.'], keep=False)
    dupes = df[dup_mask].sort_values('DWG. NO.')
    st.write(f"현재 **{len(dupes)}**개의 중복 항목이 발견되었습니다.")
    st.dataframe(dupes[['Category', 'SYSTEM', 'DWG. NO.', 'Status']], use_container_width=True, hide_index=True)
    st.warning("중복 제거 시 가장 마지막(최신) 데이터만 남게 됩니다.")
    if st.button("Confirm & Purge Duplicates", type="primary", use_container_width=True):
        clean_df = df.drop_duplicates(subset=['DWG. NO.'], keep='last')
        with pd.ExcelWriter(DB_PATH, engine='openpyxl') as writer:
            clean_df.to_excel(writer, sheet_name='DRAWING LIST', index=False)
        st.success("중복 제거가 완료되었습니다.")
        st.rerun()

def show_doc_control():
    apply_professional_style()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    if not os.path.exists(DB_PATH):
        st.error("데이터베이스 파일을 찾을 수 없습니다.")
        return

    # 데이터 로드
    df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    
    # 1. 중복 알림 및 팝업 버튼 (기존 레이아웃 복구)
    dup_list = df[df.duplicated(subset=['DWG. NO.'], keep=False)]['DWG. NO.'].unique()
    if len(dup_list) > 0:
        c1, c2 = st.columns([8, 2])
        with c1:
            st.warning(f"⚠️ Duplicate DWG. NO. detected ({len(dup_list)} cases)")
        with c2:
            if st.button("🛠️ Manage Duplicates", use_container_width=True):
                open_duplicate_manager(df)

    # 데이터 변환
    p_data = []
    for _, row in df.iterrows():
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
    f_df = pd.DataFrame(p_data)

    # 2. Revision Filter (기존 레이아웃 복구)
    st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    rev_list = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    rev_cols = st.columns(len(rev_list[:8])) # 상위 8개 리비전 표시
    for i, rev in enumerate(rev_list[:8]):
        count = len(f_df) if rev == "LATEST" else f_df['Rev'].value_counts().get(rev, 0)
        if rev_cols[i].button(f"{rev}({count})", key=f"rev_{rev}", 
                              type="primary" if st.session_state.sel_rev == rev else "secondary", 
                              use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # 필터 적용
    display_df = f_df if st.session_state.sel_rev == "LATEST" else f_df[f_df['Rev'] == st.session_state.sel_rev]

    # 3. Action Toolbar (버튼 레이아웃)
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    info_col, btn_area = st.columns([2, 1])
    with info_col:
        st.markdown(f"**Total Count: {len(display_df):,} records** (Filter: {st.session_state.sel_rev})")
    
    with btn_area:
        b1, b2, b3, b4 = st.columns(4)
        with b1: st.button("📁 Up", use_container_width=True)
        with b2: st.button("📄 PDF", use_container_width=True)
        with b3:
            export_out = BytesIO()
            with pd.ExcelWriter(export_out, engine='openpyxl') as writer:
                display_df.to_excel(writer, index=False)
            st.download_button("📤 Ex", data=export_out.getvalue(), file_name="Dwg_Export.xlsx", use_container_width=True)
        with b4: st.button("🖨️ Prt", use_container_width=True)

    # 4. Data Viewport (컬럼 간격 최적화 유지)
    st.dataframe(
        display_df, 
        use_container_width=True, 
        hide_index=True, 
        height=700,
        column_config={
            "Category": st.column_config.TextColumn("Category", width=80),
            "SYSTEM": st.column_config.TextColumn("SYSTEM", width=80),
            "Hold": st.column_config.TextColumn("Hold", width=60),
            "Status": st.column_config.TextColumn("Status", width=80),
            "Rev": st.column_config.TextColumn("Rev", width=70),
            "Date": st.column_config.TextColumn("Date", width=100),
            "DWG. NO.": st.column_config.TextColumn("DWG. NO.", width="medium"),
            "Description": st.column_config.TextColumn("Description", width="large"), # 최대 너비
            "Remark": st.column_config.TextColumn("Remark", width="medium")           # 줄바꿈 적용
        }
    )
