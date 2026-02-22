import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="Piping Material Master", layout="wide")

# 2. 화면 제목
st.title("🏗️ Piping Material Master System")

# 3. 사이드바 - 파일 업로드
with st.sidebar:
    st.header("📂 데이터 관리")
    uploaded_file = st.file_uploader("자재 마스터 엑셀(XLSX) 업로드", type=['xlsx'])
    st.info("파일을 업로드하면 시스템이 자동으로 분석을 시작합니다.")

# 4. 데이터 처리 로직
if uploaded_file is not None:
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(uploaded_file)
        
        # [중요] 모든 열 이름의 공백을 제거하고 대문자로 변환 (이름 불일치 방지)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 현재 엑셀의 열 이름을 화면에 작게 표시 (확인용)
        with st.expander("📌 시스템이 인식한 엑셀 열 목록 확인"):
            st.write(list(df.columns))

        # 필수 열 존재 여부 체크 (기존 HTML 기반 필드명)
        # 만약 엑셀의 열 이름이 다르다면 아래 ["BOM Qty", "RCV Qty"] 부분을 수정해야 합니다.
        required_cols = ["BOM Qty", "RCV Qty"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if not missing_cols:
            # 기본 계산 수행
            df['ISS Qty'] = df.get('ISS Qty', 0).fillna(0)
            df['Balance'] = df['RCV Qty'] - df['ISS Qty']
            
            # 대시보드 출력
            m1, m2, m3 = st.columns(3)
            m1.metric("전체 아이템 수", f"{len(df):,}")
            m2.metric("전체 BOM 수량", f"{df['BOM Qty'].sum():,.0f}")
            m3.metric("현재 잔량(Balance)", f"{df['Balance'].sum():,.0f}")

            # 데이터 테이블 표시
            st.subheader("📋 자재 마스터 리스트")
            st.dataframe(df, use_container_width=True)
        else:
            st.error(f"⚠️ 엑셀 파일에 필수 정보가 부족합니다: {missing_cols}")
            st.warning("엑셀 첫 줄의 제목이 'BOM Qty', 'RCV Qty'인지 확인해 주세요.")

    except Exception as e:
        st.error(f"❌ 파일을 읽는 중 예상치 못한 오류가 발생했습니다: {e}")

else:
    # 파일 업로드 전 초기 화면
    st.info("왼쪽 사이드바에서 엑셀 파일을 업로드하여 개발을 계속 진행하세요.")
    st.markdown("""
    **현재 개발 상태:**
    - 파이썬 환경 구축 완료
    - GitHub 서버 연동 완료
    - 데이터 로딩 대기 중
    """)
