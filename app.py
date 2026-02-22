import streamlit as st
import pandas as pd
import io
import re

st.set_page_config(page_title="Piping Material Master System", layout="wide")

def clean_column_names(df):
    """컬럼명 내의 줄바꿈, 특수문자 제거 및 표준화"""
    df.columns = [re.sub(r'[\r\n\t]', ' ', str(col)).strip() for col in df.columns]
    return df

def find_header_and_load(file):
    """데이터가 시작되는 정확한 헤더 행을 찾아 로드"""
    content = file.read()
    file.seek(0)
    
    # CSV와 Excel 처리 분기
    if file.name.endswith('.csv'):
        df_temp = pd.read_csv(io.BytesIO(content), nrows=20, header=None)
    else:
        df_temp = pd.read_excel(io.BytesIO(content), nrows=20, header=None)
    
    # 'ITEM' 또는 'ISO DWG NO' 또는 'PipeSize'가 포함된 행을 헤더로 간주
    header_idx = 0
    for i, row in df_temp.iterrows():
        row_str = " ".join(row.astype(str))
        if any(key in row_str for key in ['ITEM', 'ISO DWG NO', 'PipeSize', 'Items']):
            header_idx = i
            break
    
    file.seek(0)
    if file.name.endswith('.csv'):
        return pd.read_csv(file, skiprows=header_idx)
    return pd.read_excel(file, skiprows=header_idx)

def generate_mat_code(row):
    """가이드 포맷: [ITEM]-[SIZE]-[THICK/RATING]-[MATL]"""
    # 1. ITEM 추출
    item = str(row.get('ITEM', row.get('Items', 'UNKNOWN'))).strip()
    
    # 2. SIZE 추출
    size = str(row.get('SIZE', row.get('PipeSize', '0'))).strip()
    
    # 3. THICK / RATING 추출
    thick = str(row.get('THICK', row.get('BoltSize (inch)', '0'))).strip()
    
    # 4. MATERIAL 추출
    matl = str(row.get('MATL1', row.get('Description', 'UNKNOWN'))).strip()
    if len(matl) > 20: matl = matl[:20] # 너무 긴 설명은 생략
    
    # 코드 생성 및 정규화 (공백 제거, 대문자)
    code = f"{item}-{size}-{thick}-{matl}"
    return re.sub(r'[^a-zA-Z0-9-]', '_', code).upper()

# --- UI 부분 ---
st.title("🏗️ Piping Material Master & Code Generator")

with st.sidebar:
    st.header("📂 BOM 파일 업로드")
    uploaded_files = st.file_uploader(
        "BOM 파일들을 선택하세요 (SB, Large Bore 등)", 
        type=['xlsx', 'xls', 'csv'], 
        accept_multiple_files=True
    )

if uploaded_files:
    all_masters = []
    
    for f in uploaded_files:
        try:
            df = find_header_and_load(f)
            df = clean_column_names(df)
            
            # 수량 컬럼 찾기 (Q'TY 또는 Quantity...)
            qty_col = next((c for c in df.columns if 'Q\'TY' in c or 'Quantity' in c or 'Q.TY' in c), None)
            
            if qty_col:
                df['Material Code'] = df.apply(generate_mat_code, axis=1)
                df['Standard Qty'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
                
                # 필요한 컬럼만 추출
                master_part = df[['Material Code', 'Standard Qty', 'ITEM' if 'ITEM' in df.columns else 'Items']]
                all_masters.append(master_part)
        except Exception as e:
            st.error(f"{f.name} 처리 중 에러: {e}")

    if all_masters:
        final_df = pd.concat(all_masters, ignore_index=True)
        
        # Material Code 기준 병합 및 수량 합산
        master_table = final_df.groupby('Material Code').agg({
            'Standard Qty': 'sum'
        }).reset_index()
        
        st.subheader("✅ 생성된 Material Master (통합 결과)")
        st.metric("총 고유 자재 품목", f"{len(master_table):,} EA")
        st.dataframe(master_table, use_container_width=True)
        
        # 다운로드 버튼
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            master_table.to_excel(writer, index=False)
        st.download_button("📥 통합 마스터 다운로드 (Excel)", output.getvalue(), "Material_Master.xlsx")
else:
    st.info("BOM 파일들을 업로드하면 가이드에 맞춰 Material Code가 생성됩니다.")
