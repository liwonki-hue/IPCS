import streamlit as st
import pandas as pd
import os
import math
from io import BytesIO

# ... (기존 설정 및 데이터 로드 로직 동일) ...

def get_latest_rev_info(row):
    revisions = [('3rd REV', '3rd DATE'), ('2nd REV', '2nd DATE'), ('1st REV', '1st DATE')]
    for r, d in revisions:
        val = row.get(r)
        if pd.notna(val) and str(val).strip() != "":
            return val, row.get(d, '-')
    return '-', '-'

def process_raw_df(df_raw):
    p_data = []
    for _, row in df_raw.iterrows():
        l_rev, l_date = get_latest_rev_info(row)
        p_data.append({
            "Category": row.get('Category', '-'), 
            "Area": row.get('Area', row.get('AREA', '-')), 
            "SYSTEM": row.get('SYSTEM', '-'),
            "DWG. NO.": row.get('DWG. NO.', '-'), 
            "Description": row.get('DRAWING TITLE', '-'),
            "Rev": l_rev, "Date": l_date, "Hold": row.get('HOLD Y/N', 'N'),
            "Status": row.get('Status', '-')
        })
    return pd.DataFrame(p_data)

# --- [신규] 인쇄 전용 자바스크립트 함수 ---
def execute_print(df, title):
    """필터링된 데이터를 HTML 테이블로 변환하여 인쇄창을 엽니다."""
    # HTML 테이블 생성
    table_html = df.to_html(index=False, border=1, classes='print-table')
    
    print_script = f"""
    <script>
    var printWin = window.open('', '', 'width=1000,height=800');
    printWin.document.write('<html><head><title>Print Drawing List</title>');
    printWin.document.write('<style>');
    printWin.document.write('body {{ font-family: Arial, sans-serif; padding: 20px; }}');
    printWin.document.write('h2 {{ color: #1657d0; text-align: center; }}');
    printWin.document.write('.print-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10px; }}');
    printWin.document.write('.print-table th {{ background-color: #f2f2f2; padding: 8px; text-align: left; border: 1px solid #ccc; }}');
    printWin.document.write('.print-table td {{ padding: 6px; border: 1px solid #ccc; }}');
    printWin.document.write('</style></head><body>');
    printWin.document.write('<h2>{title}</h2>');
    printWin.document.write('{table_html.replace("'", "\\'").replace("\\n", "")}');
    printWin.document.write('</body></html>');
    printWin.document.close();
    printWin.focus();
    setTimeout(function() {{ printWin.print(); printWin.close(); }}, 500);
    </script>
    """
    st.components.v1.html(print_script, height=0)

# ... (기존 필터 로직 동일) ...

def render_drawing_table(display_df, tab_name):
    # (검색 및 필터링 레이아웃 생략 - 기존 코드 유지)
    
    # [필터링 수행 결과 df 생성 부분]
    df = display_df.copy()
    # ... 필터링 로직 수행 ...

    # Action Toolbar
    st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
    t_cols = st.columns([3, 5, 1, 1, 1, 1])
    
    # (Upload, Sync, Export 버튼 생략)
    
    # 3. [개선] Print 버튼
    with t_cols[5]:
        if st.button("🖨️ Print", key=f"prt_{tab_name}", use_container_width=True):
            # 필터링된 현재 데이터셋(df)을 인쇄 함수로 전달
            execute_print(df, f"Drawing Control System - {tab_name}")

    # 메인 화면용 테이블 출력
    st.dataframe(df, use_container_width=True, hide_index=True, height=800)

# ... (나머지 show_doc_control 로직 동일) ...
