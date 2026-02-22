import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 시스템 설정 및 디자인
st.set_page_config(page_title="Piping Material Master System", layout="wide")

# 기존 HTML의 핵심 색상과 스타일을 CSS로 정의 (깔끔한 UI 유지)
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; border: 1px solid #d1dce8; padding: 20px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #f0f4f8; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 처리 엔진 (기존 복잡한 JS 로직을 대체)
def calculate_material(df):
    # 자재 계산 로직: 입고량, 출고량, 잔량 계산
    df['Balance'] = df['RCV Qty'] - df.get('ISS Qty', 0)
    df['Progress'] = (df['RCV Qty'] / df['BOM Qty'] * 100).fillna(0)
    return df

# 3. 사이드바 - 제어판
with st.sidebar:
    st.header("⚙️ System Control")
    uploaded_file = st.file_uploader("자재 마스터 엑셀 업로드", type=['xlsx'])
    st.info("여기에 자재 정보를 업데이트하면 전체 대시보드가 즉시 갱신됩니다.")

# 4. 메인 화면 로직
if uploaded_file:
    # 데이터 로드
    df = pd.read_excel(uploaded_file)
    df = calculate_material(df)

    st.title("🏗️ Piping Material Management")

    # 상단 요약 카드 (기존 HTML의 Stats Card 대체)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Items", f"{len(df):,}")
    c2.metric("Total BOM", f"{df['BOM Qty'].sum():,.0f}")
    c3.metric("Received", f"{df['RCV Qty'].sum():,.0f}")
    c4.metric("Balance", f"{df['Balance'].sum():,.0f}", delta="-Shortage")

    # 탭 메뉴 구성 (기존 HTML의 Tab 기능 대체)
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 Master List", "📦 Issue Tracking"])

    with tab1:
        st.subheader("Material Progress by Category")
        fig = px.bar(df, x='Category', y=['BOM Qty', 'RCV Qty'], barmode='group', color_discrete_sequence=['#1e6ee8', '#0f9b6c'])
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Detailed Material Master")
        # 검색 필터 추가
        search = st.text_input("ISO 또는 Material Code 검색")
        filtered_df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)]
        st.dataframe(filtered_df, use_container_width=True, height=600)

    with tab3:
        st.subheader("Issue & Logistics")
        st.write("출고 관리 및 현장 인도 현황")
        # 데이터 편집 기능을 통해 직접 수정 가능 (기존 HTML에 없는 강력한 기능)
        st.data_editor(df[['ISO', 'Material Code', 'Size', 'BOM Qty', 'ISS Qty']], use_container_width=True)

else:
    st.warning("👈 사이드바에서 자재 마스터 파일을 업로드하여 개발을 진행하세요.")
