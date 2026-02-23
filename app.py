import streamlit as st
import pandas as pd
import os
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- [Configuration] ---
DB_PATH = 'data/drawing_master.xlsx'
GDRIVE_FOLDER_ID = 'YOUR_GOOGLE_DRIVE_FOLDER_ID' # 구글 드라이브 폴더 ID 입력
CREDENTIALS_FILE = 'credentials.json' # GCP 서비스 계정 키 파일 경로

st.set_page_config(layout="wide", page_title="Document Control System")

# --- [CSS Styling] ---
def apply_compact_style():
    st.markdown("""
        <style>
        /* 기본 여백 축소 */
        .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; }
        
        /* 메인 타이틀 */
        .main-title { font-size: 32px; font-weight: 800; color: #1657d0; margin-bottom: 10px; border-bottom: 2px solid #1657d0; padding-bottom: 5px; }
        
        /* 버튼 및 폼 요소 컴팩트화 */
        div[data-testid="stButton"] button {
            padding: 0.2rem 0.5rem; font-size: 13px; min-height: 32px; height: 32px;
        }
        div[data-testid="stButton"] button[kind="primary"] { background-color: #28a745 !important; color: white !important; }
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            min-height: 32px !important; height: 32px !important; font-size: 13px !important;
        }
        
        /* 섹션 라벨 폰트 축소 */
        .section-label { font-size: 12px; font-weight: 700; color: #495057; margin-bottom: -10px; margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)

# --- [Data Processing Functions] ---
def get_latest_rev_info(row):
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def process_raw_df(df_raw):
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), 
            "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', row.get('Description', '-')),
            "Rev": l_rev,
            "Date": l_date, 
            "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-'),
            "Drawing Link": row.get('Drawing Link', None) # PDF Link Column
        })
    return pd.DataFrame(p_data)

@st.cache_data(show_spinner=False)
def load_master_data():
    if os.path.exists(DB_PATH):
        df_raw = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
        return process_raw_df(df_raw)
    return pd.DataFrame()

# --- [Google Drive Sync Logic] ---
def sync_with_google_drive(df):
    """
    GCP 서비스 계정을 사용하여 드라이브 폴더 내 파일 목록을 조회하고,
    DWG.NO 및 Rev 가 일치하는 파일의 웹뷰 링크를 DataFrame에 매핑합니다.
    (파일명 규칙 예시: DWG-1234_C01A.pdf)
    """
    if not os.path.exists(CREDENTIALS_FILE):
        st.error("Google Drive API Credentials(credentials.json)이 누락되었습니다.")
        return df

    try:
        credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
        service = build('drive', 'v3', credentials=credentials)
        
        # 특정 폴더 내 PDF 파일만 조회
        query = f"'{GDRIVE_FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name, webViewLink)").execute()
        files = results.get('files', [])

        if not files:
            st.warning("Google Drive 폴더에 조회된 파일이 없습니다.")
            return df

        # 매핑 로직 구축
        for file in files:
            file_name = file['name'].replace('.pdf', '')
            # 가정: 파일명이 '도면번호_리비전' 형태로 저장됨 (예: CCP-W-B028-PI-140-AS-002-1_C01A)
            if '_' in file_name:
                dwg_no, rev_no = file_name.rsplit('_', 1)
                
                # 데이터프레임 내 일치 조건 검색 및 업데이트
                mask = (df['DWG. NO.'] == dwg_no) & (df['Rev'] == rev_no)
                df.loc[mask, 'Drawing Link'] = file['webViewLink']
                
        st.success("Google Drive PDF 도면 연동이 성공적으로 완료되었습니다.")
        return df

    except Exception as e:
        st.error(f"Google Drive 동기화 중 오류 발생: {e}")
        return df

# --- [Print & Export] ---
def execute_stable_print(df, title):
    table_html = df.drop(columns=['Drawing Link']).to_html(index=False, border=1)
    print_html = f"""
    <html><head><meta charset="utf-8"><title>{title}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; padding: 20px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
        th, td {{ border: 1px solid #ddd; padding: 6px; text-align: left; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
    </style>
    </head><body><h2>{title}</h2>{table_html}<script>window.onload=function(){{window.print(); window.close();}}</script></body></html>
    """
    st.components.v1.html(f"<script>var w=window.open(); w.document.write(`{print_html}`); w.document.close();</script>", height=0)

# --- [Main UI Rendering] ---
def main():
    apply_compact_style()
    st.markdown("<div class='main-title'>Document Control System</div>", unsafe_allow_html=True)
    
    if 'master_df' not in st.session_state:
        st.session_state.master_df = load_master_data()
        
    master_df = st.session_state.master_df
    if master_df.empty:
        st.info("데이터가 없습니다. Master 파일을 업로드해 주세요.")
        return

    # --- [도면 중복 검사 패널] ---
    with st.expander("🔍 도면 중복 검사 (Duplicate Drawing Check)", expanded=False):
        dup_df = master_df[master_df.duplicated(subset=['DWG. NO.'], keep=False)].sort_values(by='DWG. NO.')
        if not dup_df.empty:
            st.warning(f"총 {len(dup_df)}건의 중복 도면 번호가 발견되었습니다.")
            st.dataframe(dup_df[['DWG. NO.', 'Description', 'Rev', 'Category']], height=200, use_container_width=True)
        else:
            st.success("중복된 도면 번호가 없습니다.")

    # --- [Tabs] ---
    tabs = st.tabs(["📊 Master", "📐 ISO", "🏗️ Support", "🔧 Valve", "🌟 Specialty"])
    tab_names = ["Master", "ISO", "Support", "Valve", "Specialty"]

    for i, tab in enumerate(tabs):
        with tab:
            curr_df = master_df if i == 0 else master_df[master_df['Category'].str.contains(tab_names[i], case=False, na=False)]
            
            # 1. Revision Filter (Compact)
            st.markdown("<div class='section-label'>REVISION FILTER</div>", unsafe_allow_html=True)
            rev_list = ["LATEST"] + sorted([r for r in curr_df['Rev'].unique() if pd.notna(r) and r != "-"])
            r_cols = st.columns(len(rev_list[:8]) + 4) # 버튼 폭 조절을 위한 빈 컬럼 추가
            
            f_key = f"rev_{i}"
            selected_rev = st.session_state.get(f_key, "LATEST")
            
            for idx, rev in enumerate(rev_list[:8]):
                if r_cols[idx].button(rev, key=f"btn_{i}_{rev}", type="primary" if selected_rev == rev else "secondary"):
                    st.session_state[f_key] = rev
                    st.rerun()

            # 2. Search & Filters (화면 중간까지만 배치)
            st.markdown("<div class='section-label'>SEARCH & FILTER</div>", unsafe_allow_html=True)
            # 비율: [검색(3), 시스템(1.5), 구역(1.5), 상태(1.5), 우측여백(4.5)]
            s_cols = st.columns([3, 1.5, 1.5, 1.5, 4.5], gap="small") 
            
            q = s_cols[0].text_input("Search", placeholder="DWG No. or Description...", key=f"q_{i}", label_visibility="collapsed")
            sys_opts = ["All"] + sorted(curr_df['SYSTEM'].astype(str).unique().tolist())
            sel_sys = s_cols[1].selectbox("System", sys_opts, key=f"sys_{i}", label_visibility="collapsed")
            
            area_opts = ["All"] + sorted(curr_df['Area'].astype(str).unique().tolist())
            sel_area = s_cols[2].selectbox("Area", area_opts, key=f"area_{i}", label_visibility="collapsed")
            
            status_opts = ["All"] + sorted(curr_df['Status'].astype(str).unique().tolist())
            sel_status = s_cols[3].selectbox("Status", status_opts, key=f"stat_{i}", label_visibility="collapsed")

            # --- [필터링 적용] ---
            df_disp = curr_df.copy()
            if selected_rev != "LATEST": df_disp = df_disp[df_disp['Rev'] == selected_rev]
            if q: df_disp = df_disp[df_disp['DWG. NO.'].str.contains(q, case=False, na=False) | df_disp['Description'].str.contains(q, case=False, na=False)]
            if sel_sys != "All": df_disp = df_disp[df_disp['SYSTEM'] == sel_sys]
            if sel_area != "All": df_disp = df_disp[df_disp['Area'] == sel_area]
            if sel_status != "All": df_disp = df_disp[df_disp['Status'] == sel_status]

            # 3. Action Buttons & Total Count
            st.markdown("<br>", unsafe_allow_html=True)
            a_cols = st.columns([6, 1.5, 1.5, 1.5, 1.5])
            a_cols[0].markdown(f"<span style='font-weight:bold; font-size:14px; color:#333;'>Total: {len(df_disp):,} records</span>", unsafe_allow_html=True)
            
            with a_cols[1]: 
                if st.button("📁 Upload", key=f"up_{i}", use_container_width=True):
                    st.info("Upload Modal 구현부입니다.") # Upload Modal 로직 재활용 가능
            with a_cols[2]:
                if st.button("📄 PDF Sync", key=f"sync_{i}", use_container_width=True):
                    with st.spinner("Google Drive 동기화 중..."):
                        # 구글 드라이브 동기화 함수 호출 및 세션 스테이트 반영
                        st.session_state.master_df = sync_with_google_drive(st.session_state.master_df)
                        st.rerun()
            with a_cols[3]:
                out = BytesIO()
                df_disp.drop(columns=['Drawing Link'], errors='ignore').to_excel(out, index=False)
                st.download_button("📤 Export", data=out.getvalue(), file_name=f"{tab_names[i]}_list.xlsx", use_container_width=True)
            with a_cols[4]:
                if st.button("🖨️ Print", key=f"pr_{i}", use_container_width=True):
                    execute_stable_print(df_disp, f"Document Control List - {tab_names[i]}")

            # 4. Dataframe Rendering (Drawing View 처리)
            st.dataframe(
                df_disp, 
                use_container_width=True, 
                hide_index=True, 
                height=550,
                column_config={
                    "Drawing Link": st.column_config.LinkColumn(
                        "Drawing View",
                        help="클릭 시 PDF 도면을 조회합니다.",
                        validate=r"^http",
                        display_text="🔗 View" # 링크가 존재할 경우에만 🔗 View 텍스트가 활성화됨
                    )
                }
            )

if __name__ == "__main__":
    main()
