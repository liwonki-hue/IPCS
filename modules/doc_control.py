import streamlit as st
import pandas as pd
import os
import base64

# 파일 경로 설정
DB_PATH = 'data/drawing_master.xlsx'
PDF_PATH = 'data/drawings/'

def show_doc_control():
    st.title("📂 도면 관리 시스템 (ISO Drawing Control)")

    # 1. 파일 존재 여부 확인
    if not os.path.exists(DB_PATH):
        st.error(f"⚠️ '{DB_PATH}' 파일을 찾을 수 없습니다. data 폴더에 파일을 업로드해 주세요.")
        return

    # 2. 엑셀 데이터 로드
    try:
        # DRAWING LIST 시트를 읽어옵니다.
        df = pd.read_excel(DB_PATH, sheet_name='DRAWING LIST', engine='openpyxl')
    except Exception as e:
        st.error(f"엑셀 파일을 읽는 중 오류가 발생했습니다: {e}")
        return

    # 3. 상단 필터 레이아웃 (Area, System, Bore)
    st.subheader("🔍 도면 검색 및 필터링")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        areas = sorted(df['AREA'].unique()) if 'AREA' in df.columns else []
        sel_area = st.multiselect("영역(AREA) 선택", options=areas)
    with col2:
        systems = sorted(df['SYSTEM'].unique()) if 'SYSTEM' in df.columns else []
        sel_system = st.multiselect("시스템(SYSTEM) 선택", options=systems)
    with col3:
        bores = sorted(df['BORE'].unique()) if 'BORE' in df.columns else []
        sel_bore = st.multiselect("관경(BORE) 선택", options=bores)

    # 필터 적용
    filtered_df = df.copy()
    if sel_area:
        filtered_df = filtered_df[filtered_df['AREA'].isin(sel_area)]
    if sel_system:
        filtered_df = filtered_df[filtered_df['SYSTEM'].isin(sel_system)]
    if sel_bore:
        filtered_df = filtered_df[filtered_df['BORE'].isin(sel_bore)]

    # 4. 도면 리스트 표시 및 선택
    st.write(f"조회된 도면 수: {len(filtered_df)} 매")
    
    # 리스트에서 도면을 선택하면 아래에 뷰어가 나타나게 함
    selected_row = st.selectbox("상세 보기 및 PDF 열람 (도면 번호를 선택하세요)", 
                                 filtered_df['DWG. NO.'], index=None, placeholder="도면을 선택하십시오.")

    if selected_row:
        doc_info = filtered_df[filtered_df['DWG. NO.'] == selected_row].iloc[0]
        
        # 상세 정보 표시
        c_info1, c_info2 = st.columns(2)
        with c_info1:
            st.info(f"**도면명:** {doc_info['DRAWING TITLE']}")
            st.write(f"**상태:** {doc_info['Status']}")
        with c_info2:
            # 2nd REV가 있으면 그것을 최신 리비전으로 간주 (데이터 구조에 맞춤)
            latest_rev = doc_info['2nd REV'] if pd.notna(doc_info['2nd REV']) else doc_info['1st REV']
            st.write(f"**최신 리비전:** {latest_rev}")

        # PDF 뷰어 연동
        pdf_file = f"{selected_row}_{latest_rev}.pdf"
        full_pdf_path = os.path.join(PDF_PATH, pdf_file)
        
        if os.path.exists(full_pdf_path):
            with open(full_pdf_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.warning(f"⚠️ 도면 파일({pdf_file})이 {PDF_PATH} 폴더에 없습니다.")

    # 전체 표 보기
    with st.expander("전체 마스터 리스트 데이터 보기"):
        st.dataframe(filtered_df, use_container_width=True)
