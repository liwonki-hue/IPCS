import streamlit as st
import os

# [1] 페이지 기본 설정 및 보안 설정
st.set_page_config(
    page_title="EPC Integrated Management System",
    page_icon="🏭",
    layout="wide"
)

# 사이드바 메뉴 숨기기 및 스타일 커스텀
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        .main-title { font-size: 42px; font-weight: 800; color: #1E3A8A; margin-bottom: 20px; }
        .module-card { border-radius: 10px; padding: 20px; border: 1px solid #E2E8F0; background-color: #F8FAFC; }
    </style>
""", unsafe_allow_html=True)

def check_file_path(path):
    """모듈 접근 전 파일 존재 여부 검증"""
    return os.path.exists(path)

def main():
    # 상단 헤더
    st.markdown('<div class="main-title">🚀 EPC Project Integrated Portal</div>', unsafe_allow_html=True)
    st.markdown("""
        본 시스템은 **Engineering(설계) - Procurement(조달) - Construction(시공)** 데이터의 무결성을 보장하며,
        통합된 마스터 정보를 기반으로 실시간 프로젝트 진척률과 자재 수불 현황을 모니터링합니다.
    """)
    st.divider()

    # 시스템 섹션 (3컬럼 레이아웃)
    col1, col2, col3 = st.columns(3)

    # 1. Drawing Control (도면 관리)
    with col1:
        st.markdown('<div class="module-card">', unsafe_allow_html=True)
        st.subheader("📐 Drawing Control")
        st.write("**Engineering Data Management**")
        st.info("- ISO Drawing 최신 리비전 마스터 관리\n- 설계 변경(Revision Up) 이력 추적\n- 시공 데이터 대조용 기준 정보 제공")
        
        path_dwg = "drawing_control/doc_control.py"
        if st.button("Access Drawing Module", use_container_width=True, key="btn_dwg"):
            if check_file_path(path_dwg):
                st.switch_page(path_dwg)
            else:
                st.error(f"Error: {path_dwg} 파일을 찾을 수 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. Material Control (자재 관리 - 복구된 항목)
    with col2:
        st.markdown('<div class="module-card">', unsafe_allow_html=True)
        st.subheader("📦 Material Control")
        st.write("**Procurement & Inventory**")
        st.success("- Ident Code 기반 자재 입출고 이력\n- 도면별 소요 자재 준비성(Readiness) 평가\n- 실시간 재고 및 부족분(Shortage) 분석")
        
        path_mat = "material_control/material_app.py"
        if st.button("Access Material Module", use_container_width=True, key="btn_mat"):
            if check_file_path(path_mat):
                st.switch_page(path_mat)
            else:
                st.error(f"Error: {path_mat} 파일을 찾을 수 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. Construction Control (시공 관리)
    with col3:
        st.markdown('<div class="module-card">', unsafe_allow_html=True)
        st.subheader("🏗️ Construction Control")
        st.write("**Piping Installation Progress**")
        st.warning("- ISO Drawing별 Welding 실적 업데이트\n- Dia-inch 기반 정량적 공정률 산출\n- 설계 리비전 불일치 경고 로직")
        
        path_const = "construction_control/const_app.py"
        if st.button("Access Construction Module", use_container_width=True, key="btn_const"):
            if check_file_path(path_const):
                st.switch_page(path_const)
            else:
                st.error(f"Error: {path_const} 파일을 찾을 수 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    # 하단 정보 및 상태
    st.divider()
    foot_l, foot_r = st.columns(2)
    with foot_l:
        st.caption("Current Operating Environment: GitHub Server / Python 3.10")
        st.caption(f"Working Directory: {os.getcwd()}")
    with foot_r:
        st.markdown("<div style='text-align: right;'><small>© 2026 EPC Digital Transformation Project Team</small></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
