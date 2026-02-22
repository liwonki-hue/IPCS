import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Piping Material Management", layout="wide")

# 2. 데이터 처리 함수 (오류 방지 로직 포함)
def process_data(uploaded_file):
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(uploaded_file)
        
        # 필수 컬럼 계산 (기존 HTML 로직 이식)
        # 엑셀의 컬럼명이 코드와 일치하는지 확인이 필요합니다.
        if 'BOM Qty' in df.columns and 'RCV Qty' in df.columns:
            df['Balance'] = df['RCV Qty'] - df.get('ISS Qty', 0)
            df['Progress'] = (df['RCV Qty'] / df['BOM Qty'] * 100).fillna(0)
        return df
    except Exception as e:
        st.error(f"파일 처리 중 오류 발생: {e}")
        return None

# 3. 메인 화면 구성
st.title("🏗️ Piping Material Master (Python v1.0)")

# 사이드바에서 파일 업로드 받기
with st.sidebar:
    st.header("Data Upload")
    uploaded_file = st.file_uploader("자재 마스터 엑셀 파일을 선택하세요", type=['xlsx'])

# 4. 데이터가 업로드되었을 때만 화면 출력
if uploaded_file is not None:
    df = process_data(uploaded_file)
    
    if df is not None:
        # 상단 요약 지표
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Items", f"{len(df):,}")
        c2.metric("Total BOM", f"{df['BOM Qty'].sum():,.0f}")
        c3.metric("Balance", f"{df['Balance'].sum():,.0f}")

        # 탭 구성
        tab1, tab2 = st.tabs(["📊 Dashboard", "🔍 Master List"])
        
        with tab1:
            if 'Category' in df.columns:
                fig = px.bar(df, x='Category', y=['BOM Qty', 'RCV Qty'], barmode='group')
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.dataframe(df, use_container_width=True)
else:
    # 파일이 없을 때 보여줄 안내 문구
    st.info("👋 시스템을 시작하려면 왼쪽 사이드바에서 '자재 마스터 엑셀 파일'을 업로드해 주세요.")
    st.image("https://via.placeholder.com/800x200.png?text=Waiting+for+Excel+Data+Upload", use_column_width=True)
