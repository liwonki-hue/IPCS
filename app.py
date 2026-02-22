import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 레이아웃 설정 (전체 화면 사용)
st.set_page_config(page_title="Piping Material Master", layout="wide")

# 2. 화면 상단 여백 제거 스타일
st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 0rem; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 및 계산 함수
def load_and_calculate(file):
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(file)
        
        # 컬럼 이름의 공백 제거 (에러 방지)
        df.columns = [c.strip() for c in df.columns]
        
        # 필수 계산 로직 (기존 HTML의 JS 수식 이식)
        # 엑셀에 해당 컬럼명이 있는지 확인 후 계산
        if 'BOM Qty' in df.columns and 'RCV Qty' in df.columns:
            df['ISS Qty'] = df.get('ISS Qty', 0).fillna(0) # 출고량 없으면 0으로 채움
            df['Balance'] = df['RCV Qty'] - df['ISS Qty']
            df['Progress'] = (df['RCV Qty'] / df['BOM Qty'] * 100).round(1)
        
        return df
    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
        return None

# 4. 메인 화면 구성
st.title("🏗️ Piping Material Master System")

# 사이드바: 파일 업로드 섹션
with st.sidebar:
    st.header("📂 데이터 업로드")
    uploaded_file = st.file_uploader("자재 마스터 엑셀(XLSX)을 선택하세요", type=['xlsx'])
    st.divider()
    st.info("기존 HTML 프로그램에서 사용하던 엑셀 파일을 그대로 업로드하시면 됩니다.")

# 5. 실행 로직 (파일 존재 여부에 따른 조건부 실행)
if uploaded_file is not None:
    # 파일이 있을 때만 아래 코드 실행 (에러 방지 핵심)
    df = load_and_calculate(uploaded_file)
    
    if df is not None:
        # 상단 핵심 지표(Metrics)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Items", f"{len(df):,}")
        m2.metric("Total BOM", f"{df['BOM Qty'].sum():,.0f}")
        m3.metric("Received", f"{df['RCV Qty'].sum():,.0f}")
        m4.metric("Balance", f"{df['Balance'].sum():,.0f}")

        # 탭 메뉴 구성
        tab1, tab2 = st.tabs(["📊 대시보드", "🔍 마스터 리스트"])
        
        with tab1:
            st.subheader("Category별 자재 현황")
            if 'Category' in df.columns:
                fig = px.bar(df, x='Category', y=['BOM Qty', 'RCV Qty'], barmode='group')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("'Category' 컬럼을 찾을 수 없습니다.")

        with tab2:
            st.subheader("상세 자재 마스터")
            # 검색창 추가
            search = st.text_input("ISO Drawing 또는 Material Code 검색")
            if search:
                df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)]
            st.dataframe(df, use_container_width=True, height=600)

else:
    # 파일이 업로드되지 않았을 때 표시될 초기 화면
    st.warning("⚠️ 왼쪽 사이드바에서 엑셀 파일을 업로드해 주세요.")
    st.write("---")
    st.markdown("""
    ### 시스템 사용 방법
    1. 왼쪽의 **[Browse files]** 버튼을 클릭합니다.
    2. 관리 중인 **자재 마스터 엑셀 파일**을 선택합니다.
    3. 시스템이 자동으로 데이터를 분석하여 대시보드를 생성합니다.
    """)
