import streamlit as st
import pandas as pd
import os
from io import BytesIO

# File Path Settings
DB_PATH = 'data/drawing_master.xlsx'

def apply_fixed_button_ui():
    """버튼 내 글자 겹침 방지를 위한 초소형 폰트 및 간격 최적화 CSS"""
    st.markdown("""
        <style>
        :root { color-scheme: light only !important; }
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #f7f9fc !important;
            color: #0d1826 !important;
        }
        .block-container { padding: 0.3rem 1.5rem !important; }
        [data-testid="stHeader"] { display: none !important; }
        
        /* 1. 섹션 레이블 및 타이틀 */
        .main-title { font-size: 18px !important; font-weight: 800; color: #1657d0; margin-bottom: 3px; }
        .section-label { font-size: 9px !important; font-weight: 700; color: #8a94a6; text-transform: uppercase; }

        /* 2. Revision Filter 버튼 (글자 겹침 해결 핵심) */
        div.stButton > button {
            border-radius: 2px; border: 1px solid #dde3ec;
            background-color: white; color: #374559;
            height: 22px !important; /* 높이 유지 */
            
            /* 폰트 사이즈를 8.5px로 정밀 축소하여 겹침 방지 */
            font-size: 8.5px !important; 
            font-weight: 600 !important;
            
            padding: 0 2px !important;
            line-height: 22px !important; /* 높이와 일치시켜 세로 중앙 정렬 */
            letter-spacing: -0.6px !important; /* 자간 압축으로 너비 확보 */
            white-space: nowrap !important; /* 자동 줄바꿈 방지 */
            overflow: hidden !important;
        }
        div.stButton > button[kind="primary"] { background-color: #0c7a3d !important; color: white !important; }

        /* 3. Search & Filter (22px 동일 높이) */
        div[data-baseweb="select"], div[data-baseweb="base-input"], input {
            min-height: 22px !important; height: 22px !important; 
            font-size: 9px !important; 
        }

        /* 4. 표 데이터 18px 및 가운데 정렬 유지 */
        div[data-testid="stDataFrame"] [role="gridcell"] div {
            font-size: 18px !important;
            text-align: center !important;
            justify-content: center !important;
            display: flex !important;
            align-items: center !important;
        }
        div[data-testid="stDataFrame"] [role="columnheader"] p {
            font-size: 18px !important;
            font-weight: 800 !important;
            text-align: center !important;
            justify-content: center !important;
        }
        </style>
    """, unsafe_allow_html=True)

def show_doc_control():
    apply_fixed_button_ui()
    st.markdown("<div class='main-title'>Drawing Control System</div>", unsafe_allow_html=True)

    # 데이터 로드 (생략된 기존 로직 사용)
    # ... (데이터 처리 및 f_df 생성 부분) ...

    # [1] Revision Filter (18열 배치로 버튼 가로폭 확보)
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    rev_counts = f_df['Rev'].value_counts()
    target_revs = ["LATEST"] + sorted([r for r in f_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    # 세션 상태 초기화
    if 'sel_rev' not in st.session_state: st.session_state.sel_rev = "LATEST"
    
    # 버튼 배치를 14~16열 정도로 조정하여 개별 버튼의 최소 너비 확보
    rev_cols = st.columns(14) 
    for i, rev in enumerate(target_revs[:14]):
        count = len(f_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        is_active = st.session_state.sel_rev == rev
        
        # 버튼 텍스트를 한 줄로 결합 (공백 제거)
        btn_label = f"{rev}({count})"
        
        if rev_cols[i].button(btn_label, key=f"r_{rev}", type="primary" if is_active else "secondary", use_container_width=True):
            st.session_state.sel_rev = rev
            st.rerun()

    # [2] Search & Filter
    st.markdown("<div style='margin-top:3px;' class='section-label'>Search & Filter</div>", unsafe_allow_html=True)
    # ... (기존 필터 로직 동일) ...

    # [3] Action Toolbar (Upload, PDF, Ex, Prt)
    # 폰트 8.5px 적용으로 글자 깨짐 방지
    # ... (기존 버튼 로직 동일) ...

    # [4] Table (18px 유지)
    st.dataframe(
        work_df[["Category", "DWG. NO.", "Description", "Rev", "Date", "Hold", "Status", "Remark"]],
        use_container_width=True, 
        hide_index=True, 
        height=820
    )
