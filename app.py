import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 레이아웃 및 테마 설정
st.set_page_config(
    page_title="Piping Material Management System",
    page_icon="🏗️",
    layout="wide"
)

# 2. 데이터 처리 함수
def process_material_data(df):
    # 기존 HTML의 로직을 반영한 계산식
    if 'BOM Qty' in df.columns and 'RCV Qty' in df.columns:
        df['Balance'] = df['RCV Qty'] - df.get('ISS Qty', 0)
        df['RCV %'] = (df['RCV Qty'] / df['BOM Qty'] * 100).round(1)
    return df

# 3. 메인 화면 구성
st.title("🏗️ Piping Material Master")

# 사이드바에서 파일 업로드
st.sidebar.header("📁 Data Management")
uploaded_file = st.sidebar.file_uploader("자재 마스터 엑셀(XLSX) 업로드", type=["xlsx"])

if uploaded_file:
    try:
        # 데이터 로드
        df = pd.read_excel(uploaded_file)
        df = process_material_data(df)

        # 상단 요약 지표
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Items", f"{len(df):,}")
        m2.metric("Total BOM", f"{df['BOM Qty'].sum():,.0f}")
        m3.metric("Received", f"{df['RCV Qty'].sum():,.0f}")
        m4.metric("Shortage", f"{df['Balance'].sum():,.0f}")

        # 탭 메뉴
        tab1, tab2 = st.tabs(["📊 Dashboard", "🔍 Master List"])

        with tab1:
            if 'Category' in df.columns:
                fig = px.bar(df, x='Category', y=['BOM Qty', 'RCV Qty'], barmode='group')
                st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.dataframe(df, use_container_width=True)
            
    except Exception as e:
        st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")
else:
    st.info("왼쪽 사이드바에서 엑셀 파일을 업로드해 주세요.")
