import streamlit as st
import os

# 1. 페이지 설정 (최상단에 위치)
st.set_page_config(
    page_title="EPC Integrated Management System",
    page_icon="🏭",
    layout="wide"
)

def main():
    # 사이드바 메뉴 숨기기 (깔끔한 포털 UI를 위함)
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

    # 헤더 섹션
    st.title("🚀 EPC Project Integrated Portal")
    st.markdown("---")
    
    st.subheader("시스템을 선택해 주십시오")
    st.write("설계(Drawing)부터 시공(Construction)까지 데이터의 연속성을 보장합니다.")

    # 시스템 선택 카드 (2컬럼)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 📐 Drawing Control System
        **[Engineering & Document Management]**
        * 최신 리비전(Revision) 마스터 관리
        * 도면 승인 및 배포 이력 추적
        * 시공 모듈용 리비전 데이터 공급
        """)
        # drawing_control 폴더 내 doc_control.py 실행
        if st.button("Access Drawing Module", use_container_width=True, key="btn_dwg"):
            st.switch_page("drawing_control/doc_control.py")

    with col2:
        st.markdown("""
        ### 🏗️ Piping Construction Control
        **[Field Installation & Progress]**
        * ISO Drawing별 Joint Welding 관리
        * Dia-inch 기반 실시간 공정률 산출
        * 설계 리비전 불일치(Mismatch) 자동 감지
        """)
        # construction_control 폴더 내 const_app.py 실행
        if st.button("Access Construction Module", use_container_width=True, key="btn_const"):
            st.switch_page("construction_control/const_app.py")

    # 하단 상태창
    st.markdown("---")
    st.caption("📍 Root Path: " + os.getcwd())
    st.caption("© 2026 EPC Plant Project Digital Transformation Team")

if __name__ == "__main__":
    main()
