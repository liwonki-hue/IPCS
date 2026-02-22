import streamlit as st
import pandas as pd
import os
import requests
import base64
from io import BytesIO

# --- Configuration & Secrets ---
DB_PATH = 'data/drawing_master.xlsx'
# GitHub 설정을 st.secrets 또는 직접 입력으로 관리하십시오.
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "") # 예: "user/repo"
PDF_STORAGE_PATH = "data/pdf_store"

def get_latest_rev_info(row):
    """최신 리비전 정보를 추출하며 Remark는 제외합니다."""
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def upload_to_github(file_name, file_content):
    """GitHub API를 사용하여 PDF 파일을 저장소에 업로드합니다."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{PDF_STORAGE_PATH}/{file_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 기존 파일 SHA 확인 (업데이트 대응)
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": f"Upload Drawing PDF: {file_name}",
        "content": base64.b64encode(file_content).decode('utf-8')
    }
    if sha:
        payload["sha"] = sha
        
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code in [200, 201]

@st.dialog("PDF Drawing Sync")
def show_pdf_upload_dialog(master_df):
    """PDF 파일을 업로드하고 GitHub와 동기화하는 팝업 화면입니다."""
    st.write("파일명 규칙: **[DWG-NO]_[REV].pdf** (예: CCP-W-B028_C01A.pdf)")
    uploaded_files = st.file_uploader("PDF 도면 선택", type=['pdf'], accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Sync to Repository", type="primary", use_container_width=True):
            # 마스터 데이터와 대조하여 유효성 검사
            valid_pairs = set(zip(master_df['DWG. NO.'].astype(str), master_df['Rev'].astype(str)))
            
            success_count = 0
            for f in uploaded_files:
                name_without_ext = os.path.splitext(f.name)[0]
                if "_" in name_without_ext:
                    d_no, rev = name_without_ext.rsplit("_", 1)
                    if (d_no, rev) in valid_pairs:
                        if upload_to_github(f.name, f.getvalue()):
                            st.toast(f"✅ {f.name} 동기화 완료")
                            success_count += 1
                    else:
                        st.warning(f"⚠️ {f.name}: 마스터 리스트와 일치하는 DWG No/Rev가 없습니다.")
            
            if success_count > 0:
                st.success(f"{success_count}개의 도면이 성공적으로 업로드되었습니다.")
                if st.button("Close"): st.rerun()

def render_drawing_table(display_df, tab_name):
    # --- Duplicate Warning ---
    dups = display_df[display_df.duplicated(subset=['DWG. NO.'], keep=False)]
    if not dups.empty:
        c1, c2 = st.columns([8, 2])
        c1.error(f"⚠️ Duplicate Warning: {len(dups)} redundant records detected.")
        # Resolve 버튼 생략 (필요시 추가)

    # --- 1. Revision Filter (수량 복구) ---
    st.markdown("<div class='section-label'>Revision Filter</div>", unsafe_allow_html=True)
    f_key = f"sel_rev_{tab_name}"
    if f_key not in st.session_state: st.session_state[f_key] = "LATEST"
    
    rev_counts = display_df['Rev'].value_counts()
    rev_list = ["LATEST"] + sorted([r for r in display_df['Rev'].unique() if pd.notna(r) and r != "-"])
    
    r_cols = st.columns([1] * 7 + [7])
    for i, rev in enumerate(rev_list[:7]):
        count = len(display_df) if rev == "LATEST" else rev_counts.get(rev, 0)
        with r_cols[i]:
            if st.button(f"{rev}\n({count})", key=f"btn_{tab_name}_{rev}", 
                        type="primary" if st.session_state[f_key] == rev else "secondary", use_container_width=True):
                st.session_state[f_key] = rev
                st.rerun()

    # --- 2. Action Toolbar (우측 정렬 강화) ---
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([12, 1.5, 1.5, 1.5, 1.5, 1.5]) 
    t_cols[0].markdown(f"**Total: {len(display_df):,} records**")
    
    with t_cols[2]:
        if st.button("📄 PDF", key=f"pdf_btn_{tab_name}", use_container_width=True):
            show_pdf_upload_dialog(display_df)
    
    # Import, Export, Print 버튼 등은 기존 로직 유지 (생략)

    # --- 3. Data Viewport (컬럼 최적화) ---
    st.dataframe(
        display_df, use_container_width=True, hide_index=True, height=550,
        column_config={
            "Drawing": st.column_config.LinkColumn("Drawing", width=50, display_text="📄 View"),
            "Description": st.column_config.TextColumn("Description", width=600),
            "Status": st.column_config.TextColumn("Status", width=60)
        }
    )

def show_doc_control():
    # 스타일 적용 및 탭 구성 로직 (생략 - 기존 코드 유지)
    pass

if __name__ == "__main__":
    # 실행 로직
    pass
