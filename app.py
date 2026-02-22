import streamlit as st
import pandas as pd
import io

# 1. 페이지 설정
st.set_page_config(page_title="Piping Material Master Generator", layout="wide")

# 2. Material Code 생성 함수 (가이드 포맷 적용)
def generate_material_code(row, item_type='PIPE'):
    # 공통 요소 추출 및 클렌징
    size = str(row.get('SIZE', row.get('PipeSize', ''))).strip()
    matl = str(row.get('MATL1', row.get('Items', 'UNKNOWN'))).strip()
    
    if item_type == 'PIPE':
        item = str(row.get('ITEM', 'UNKNOWN')).strip()
        rating = str(row.get('THICK', '0')).strip()
    else:  # Bolt & Gasket류
        item = "BOLT_GASKET"
        rating = str(row.get('BoltSize (inch)', '0')).strip()

    # Format: [ITEM]-[SIZE]-[RATING/THICK]-[MATL] 기반 조합
    # 특수문자 및 공백 제거 처리
    code = f"{item}-{size}-{rating}-{matl}".replace(" ", "").upper()
    return code

# 3. 데이터 통합 처리 로직
def process_multiple_boms(uploaded_files):
    combined_list = []
    
    for uploaded_file in uploaded_files:
        # 파일 확장자에 따른 읽기 방식 선택
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # 컬럼명 정리 (공백 제거)
        df.columns = [str(c).strip() for c in df.columns]
        
        # 데이터 유형 판별 및 코드 생성
        if 'ITEM' in df.columns: # Piping & Fitting 타입
            df['Material Code'] = df.apply(lambda r: generate_material_code(r, 'PIPE'), axis=1)
            df['BOM Qty'] = df.get('Q\'TY', 0)
        elif 'PipeSize' in df.columns: # Bolt & Gasket 타입
            df['Material Code'] = df.apply(lambda r: generate_material_code(r, 'BOLT'), axis=1)
            df['BOM Qty'] = df.get('Quantity (M, Ea)', 0)
            df['ITEM'] = df.get('Items', 'Bolt/Gasket')

        # 필요한 표준 컬럼만 선택하여 통합 리스트에 추가
        std_cols = ['Material Code', 'ITEM', 'SIZE', 'BOM Qty', 'ISO DWG NO']
        existing_std = [c for c in std_cols if c in df.columns]
        combined_list.append(df[existing_std])

    if not combined_list:
        return None

    # 전체 데이터 병합
    full_df = pd.concat(combined_list, ignore_index=True)
    
    # Material Code 기준 그룹화 (최종 마스터 생성)
    master_df = full_df.groupby('Material Code').agg({
        'ITEM': 'first',
        'SIZE': 'first',
        'BOM Qty': 'sum'
    }).reset_index()
    
    return master_df

# 4. 메인 화면 UI
st.title("🏗️ Material Master & Code Generator")
st.markdown("---")

with st.sidebar:
    st.header("📂 BOM 파일 업로드")
    # 여러 파일을 동시에 올릴 수 있도록 설정
    uploaded_files = st.file_uploader(
        "SB BOM 및 LARGE BORE BOM 파일들을 모두 선택하세요", 
        type=['xlsx', 'xls', 'csv'], 
        accept_multiple_files=True
    )
    st.info("파이프, 피팅, 볼트, 가스켓 파일을 동시에 업로드하여 통합할 수 있습니다.")

if uploaded_files:
    with st.spinner('마스터 코드를 생성하고 데이터를 통합 중입니다...'):
        master_data = process_multiple_boms(uploaded_files)
        
        if master_data is not None:
            # 상단 요약 정보
            st.subheader("📊 Material Master 요약")
            col1, col2, col3 = st.columns(3)
            col1.metric("총 고유 자재수", f"{len(master_data):,} EA")
            col2.metric("총 설계 수량(BOM)", f"{master_data['BOM Qty'].sum():,.0f}")
            
            # 결과 테이블 출력
            st.subheader("📋 생성된 Material Master (가이드 포맷 적용)")
            st.dataframe(master_data, use_container_width=True, height=500)
            
            # 엑셀 다운로드 기능
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                master_data.to_excel(writer, index=False, sheet_name='Master')
            
            st.download_button(
                label="📥 생성된 Material Master 다운로드 (Excel)",
                data=output.getvalue(),
                file_name="Material_Master_Output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.warning("👈 왼쪽 사이드바에서 분석할 BOM 파일들을 업로드해 주세요.")
