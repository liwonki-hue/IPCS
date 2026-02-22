# EPC Piping Material Master System

Streamlit 기반 배관 자재 통합 관리 시스템

## 설치 및 실행

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 앱 실행
```bash
streamlit run app.py
```

### 3. 서버 배포 (background)
```bash
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

## 디렉토리 구조
```
piping_app/
├── app.py                      # 메인 Streamlit 앱
├── requirements.txt
├── README.md
└── data/
    ├── master_v5.json          # PFS/BGS 마스터 데이터 (읽기 전용)
    ├── iso_bom_compact.json    # ISO BOM 데이터 2,529 도면 (읽기 전용)
    ├── receiving_data.json     # 초기 입고 데이터
    ├── receiving_live.json     # 실시간 입고 데이터 (앱이 자동 생성)
    ├── iso_edits.json          # ISO List 수정 내역 (앱이 자동 생성)
    └── issue_log.json          # 불출 이력 (앱이 자동 생성)
```

## 탭 기능 설명

### 📊 SUMMARY
- KPI 카드: Design Total / Received / Issued / Stock / Coverage%
- PF(Piping & Fitting) / BG(Bolt & Gasket) 구분
- Category / Item / Material 필터
- Progress bar로 입고율 표시
- Excel 내보내기

### 📋 ISO LIST
- 2,529 ISO 도면 × 7,492 BOM 항목
- System / Area / Category / ISO Drawing 필터
- Pipe: MM → M 변환 (소수점 올림)
- 수량/Remark 편집 가능 (st.data_editor)
- **Save Changes** → Summary Design Qty 즉시 반영
- Import/Export Excel (첨부 이미지 형식)
- 신규 Row 추가

### 📃 MASTER LIST
- PF/BG 탭 구분
- **Category 컬럼**: Pipe / Fitting / Flange / Valve / Specialty / Other
- Category / Item / Material 필터
- Excel 내보내기

### 📦 RECEIVING
- 891개 초기 입고 레코드
- Shipment / Packing List 필터
- Excel Import (Receiving.xlsx 형식)
- Row 추가/수정/삭제
- **Save Changes** → 재고 현황 즉시 반영

### 📤 ISSUE
- System → Area → ISO Drawing 계층적 선택
- BOM Table 14컬럼 표시
  - Unit/Area / ISO Drawing / Category / Material Code / Item
  - Spec / Size / Rating / End Type / UOM
  - Design / BOM Qty / Rcv Qty / **Issue Qty** (입력) / Balance
- **FIFO**: 가장 오래된 입고 배치부터 선입선출
- **Material Issue Slip 생성**: HTML 다운로드 → 브라우저에서 인쇄
  - 상단: ISO Drawing No. 강조 표시
  - 하단: Packing List 컬럼 (FIFO 순서)
- Issue Log 관리 (삭제/재출력)

## 데이터 흐름
```
receiving_live.json
       ↓
  store {mc5: {r, i}}
       ↓
  Summary KPIs / Balance 계산

iso_edits.json
       ↓
  ISO List 수량 오버라이드
       ↓
  Summary Design Qty 갱신

issue_log.json
       ↓
  FIFO issued qty 반영
  → store.i 증가
  → Balance, Stock 감소
```

## 요구사항
- Python 3.10+
- streamlit >= 1.32.0
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- xlsxwriter >= 3.1.0
