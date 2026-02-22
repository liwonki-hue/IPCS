import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime

# 경로 설정
DB_PATH_XLSX = 'data/drawing_master.xlsx'
PDF_STORAGE_PATH = 'data/drawings/'

if not os.path.exists(PDF_STORAGE_PATH):
    os.makedirs(PDF_STORAGE_PATH)

def load_data():
    if os.path.exists(DB_PATH_XLSX):
        return pd.read_excel(DB_PATH_XLSX, engine='openpyxl')
    return pd.DataFrame()

def save_data(df):
    df.to_excel(DB_PATH_XLSX, index=False, engine='openpyxl')

def generate_unique_id(df):
    """ISO Drawing No와 Sheet를 결합하여 고유 ID 생성 (Construction Control용)"""
    if 'ISO Drawing' in df.columns and 'Sheet' in df.columns:
        df['ISO_DWG_ID'] = df['ISO Drawing'].astype(str) + "-" + df['Sheet'].astype(str)
    return df

def display_pdf(file_path):
    """PDF 파일을 Base64로 인코딩하여 iframe으로 출력"""
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("파일을 찾을 수 없습니다. 경로를 확인하십시오.")

def show_doc_control():
    st.header("📂 Advanced Document Control")
    df = load_data()

    if not df.empty:
        df = generate_unique_id(df)

    tab1, tab2 = st.tabs(["🔍 Drawing List & Viewer", "📥 Batch Update (Excel)"])

    with tab1:
        if df.empty:
            st.info("등록된 데이터가 없습니다. Batch Update 탭에서 엑셀 파일을 업로드하십시오.")
        else:
            # --- 실무형 다중 필터링 ---
            st.markdown("#### 🔍 Filtering Options")
            c1, c2, c3 = st.columns(3)
            with c1:
                sel_area = st.multiselect("Area", options=sorted(df['Area'].dropna().unique()))
            with c2:
                sel_sys = st.multiselect("System", options=sorted(df['System'].dropna().unique()))
            with c3:
                sel_bore = st.multiselect("Bore Size", options=sorted(df['Bore'].dropna().unique()))

            # 필터 로직
            filtered_df = df.copy()
            if sel_area: filtered_df = filtered_df[filtered_df['Area'].isin(sel_area)]
            if sel_sys: filtered_df = filtered_df[filtered_df['System'].isin(sel_sys)]
            if sel_bore: filtered_df = filtered_df[filtered_df['Bore'].isin(sel_bore)]

            st.write(f"**Total Found: {len(filtered_df)} items**")
            
            # --- 리스트 및 뷰어 레이아웃 ---
            col_list, col_view = st.columns([1, 1.5])
            
            with col_list:
                # 데이터프레임에서 행 선택
                selected_event = st.dataframe(
                    filtered_df[['ISO_DWG_ID', 'Area', 'System', 'Rev.']],
                    use_container_width=True,
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single"
                )
            
            with col_view:
                if selected_event and selected_event['selection']['rows']:
                    row_idx = selected_event['selection']['rows'][0]
                    selected_doc = filtered_df.iloc[row_idx]
                    
                    st.success(f"Selected: {selected_doc['ISO_DWG_ID']}")
                    
                    # 파일 경로 매핑 (파일이 저장되어 있다는 가정 하에)
                    # 파일명 규칙: ISO_DWG_ID_Rev.pdf
                    pdf_filename = f"{selected_doc['ISO_DWG_ID']}_Rev{selected_doc['Rev.']}.pdf"
                    file_path = os.path.join(PDF_STORAGE_PATH, pdf_filename)
                    
                    if os.path.exists(file_path):
                        display_pdf(file_path)
                    else:
                        st.info(f"파일 대기 중: {pdf_filename} 파일을 {PDF_STORAGE_PATH}에 업로드하십시오.")

    with tab2:
        st.subheader("Batch Update via Master Excel")
        st.markdown("수정하신 `ISO_DWG_MASTER_LIST_220226(Rev.1).xlsx` 파일을 업로드하십시오.")
        
        uploaded_file = st.file_uploader("Upload Master List", type=['xlsx'])
        
        if uploaded_file:
            try:
                # DRAWING LIST 시트 로드
                new_df = pd.read_excel(uploaded_file, sheet_name='DRAWING LIST', engine='openpyxl')
                
                # 필수 필드 확인 (Area, System, Bore 포함)
                required = ["Area", "System", "Bore", "ISO Drawing", "Sheet", "Rev."]
                if all(col in new_df.columns for col in required):
                    st.success("양식 검증 완료")
                    st.dataframe(new_df.head(), use_container_width=True)
                    
                    if st.button("Confirm & Overwrite Database"):
                        new_df['Update Date'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        save_data(new_df)
                        st.success("데이터베이스 업데이트가 완료되었습니다.")
                        st.rerun()
                else:
                    st.error(f"필수 컬럼이 부족합니다. 다음 컬럼을 포함하십시오: {required}")
            except Exception as e:
                st.error(f"오류 발생: {e}")
