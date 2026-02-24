import streamlit as st
import os

# 페이지 기본 설정 (전문적인 느낌을 위해 Wide 모드 및 테마 설정)
st.set_page_config(
    page_title="EPC Integrated Management System",
    page_icon="🏗️",
    layout="wide"
)

def main_portal():
    # 상단 헤더 섹션
    st.title("🚀 EPC Project Integrated Control Portal")
    st.markdown("""
    본 시스템은 EPC 플랜트 프로젝트의 성과 극대화를 위해 설계, 조달, 시공 데이터를 통합 관리하는 플랫폼입니다. 
    각 모듈은 독립적인 데이터 저장소를 참조하며, 실시간 데이터 동기화를 통해 의사결정을 지원합니다.
    """)
    st.divider()

    # 시스템 선택 섹션 (3컬럼 레이아웃)
    col1, col2, col3 = st.columns(3)

    # 1. 도면 관리 시스템 (Drawing Control)
    with col1:
        st.subheader("📐 Drawing Control")
        st.info("Design & Revision Management")
        st.write("""
        - ISO Drawing 최신 리비전 관리
        - 설계 도면 배포 및 승인 현황 추적
        - Engineering Milestone 제어
        """)
        # drawing_control/doc_control.py로 연결 (Streamlit의 페이지 전환 기능)
        if st.button("Access Drawing System", use_container_width=True):
            if os.path.exists("drawing_control/doc_control.py"):
                st.switch_page("drawing_control/doc_control.py")
            else:
                st.error("도면 관리 시스템 파일을 찾을 수 없습니다.")

    # 2. 시공 관리 시스템 (Construction Control)
    with col2:
        st.subheader("🏗️ Construction")
        st.success("Piping Welding & Progress")
        st.write("""
        - ISO별 Joint Welding 실적 관리
        - Dia-inch 기반 실시간 공정률 산출
        - 설계 리비전 정합성 자동 검증
        """)
        # construction_control/const_app.py로 연결
        if st.button("Access Construction System", use_container_width=True):
            if os.path.exists("construction_control/const_app.py"):
                st.switch_page("construction_control/const_app.py")
            else:
                st.error("시공 관리 시스템 파일을 찾을 수 없습니다.")

    # 3. 자재 관리 시스템 (Material - 향후 확장 가능)
    with col3:
        st.subheader("📦 Material Mgmt")
        st.warning("Procurement & Inventory")
        st.write("""
        - MTO 기반 자재 수불 관리
        - 창고 재고 및 Shortage 분석
        - 시공 준비성(Readiness) 평가
        """)
        st.button("Under Development", disabled=True, use_container_width=True)

    # 하단 풋터 및 상태 표시
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.caption("© 2026 EPC Plant Project Team. All rights reserved.")
    with c2:
        st.caption("System Status: All Modules Operational")

if __name__ == "__main__":
    main_portal()
