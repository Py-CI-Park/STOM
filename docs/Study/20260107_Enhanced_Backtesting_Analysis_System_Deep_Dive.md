# 강화된 백테스팅 분석 시스템 심층 분석

## 문서 정보
- **작성일**: 2026-01-07
- **버전**: 1.0
- **목적**: 백테스팅 강화 분석 시스템의 구조 변화, 데이터 흐름, 변수 매핑 체계를 분석하고, 세그먼트 필터 분석 결과와 실제 적용 시 불일치 원인을 규명
- **기준 커밋**: `12d4a1226fe9d075c6d81e1752b0a398d0553f6f` (강화 기능 없음) → 현재 HEAD
- **관련 문서**: 
  - `20260106_Segment_Filter_Variable_Definition_Study.md`
  - `docs/Study/Guides/New_Metrics_Development_Process_Guide.md`

---

## 1. 시스템 구조 변화 개요

### 1.1 과거 구조 (12d4a12 커밋 기준)

```
backtester/
├── back_static.py              # 유틸리티 함수 (GetResultDataframe, PltShow 등)
├── back_subtotal.py            # 서브토탈 계산
├── backengine_kiwoom_*.py      # 백테스팅 엔진 (12개)
├── backtest.py                 # 오케스트레이터
├── optimiz.py                  # 그리드 서치 최적화
└── optimiz_genetic_algorithm.py # 유전 알고리즘 최적화
```

**특징**:
- 총 37개 파일
- 분석 로직이 `back_static.py`에 통합
- 파생 지표 계산 없음 (원본 데이터만 기록)
- 세그먼트 분석 기능 없음

### 1.2 현재 구조 (강화된 분석 시스템)

```
backtester/
├── analysis/                        # [NEW] 분석 모듈 분리
│   ├── exports.py                   # CSV 내보내기
│   ├── metrics_base.py              # 기본 파생 지표
│   ├── plotting.py                  # 차트 생성
│   ├── results.py                   # DataFrame 생성
│   └── output_config.py             # 출력 설정
│
├── analysis_enhanced/               # [NEW] 강화된 분석
│   ├── runner.py                    # 오케스트레이터 (1,200+ 라인)
│   ├── metrics_enhanced.py          # 강화된 파생 지표 (445 라인)
│   ├── filters.py                   # 필터 분석
│   ├── stats.py                     # 통계 검정
│   ├── ml.py                        # ML 예측
│   ├── analysis_logger.py           # 텔레그램 로거 (1,171 라인)
│   ├── ensemble_filter.py           # 앙상블 필터
│   ├── feature_selection.py         # 특성 선택
│   └── validation_enhanced.py       # 검증 로직
│
├── segment_analysis/                # [NEW] 세그먼트 분석
│   ├── code_generator.py            # 조건식 코드 생성 (870+ 라인)
│   ├── segment_apply.py             # 세그먼트 마스크 적용
│   ├── phase2_runner.py             # Phase 2 실행
│   ├── phase3_runner.py             # Phase 3 실행
│   ├── segmentation.py              # 세그먼트 분할 로직
│   ├── filter_evaluator.py          # 필터 평가
│   ├── combination_optimizer.py     # 조합 최적화
│   └── validation.py                # 검증 로직
│
├── detail_schema.py                 # [NEW] 컬럼 스키마 정의
├── output_manifest.py               # [NEW] 출력 파일 관리
└── output_paths.py                  # [NEW] 출력 경로 관리
```

**특징**:
- 총 80+ 파일 (2배 이상 증가)
- 관심사 분리 (analysis, analysis_enhanced, segment_analysis)
- 93개 이상의 파생 지표 자동 계산
- 세그먼트 기반 필터 최적화 지원
- ML 예측 모델 통합

---

## 2. 추가된 데이터/컬럼 체계

### 2.1 detail.csv 컬럼 진화

#### 과거 (12d4a12)
```python
# utility/setting.py 기준
columns_bt = [
    '종목명', '매수시간', '매도시간', '보유시간', '수익률', '수익금', '수익금합계',
    '매수등락율', '매도등락율', '매수체결강도', '매도체결강도', ...
]
# 약 50개 기본 컬럼
```

#### 현재 (강화 분석)
```python
# backtester/detail_schema.py + metrics_enhanced.py 기준
# 기본 컬럼 + 파생 지표 = 93개 이상

# 변화량 지표 (5개)
'등락율변화', '체결강도변화', '전일비변화', '회전율변화', '호가잔량비변화'

# 변화율 지표 (2개)
'거래대금변화율', '체결강도변화율'

# 품질/위험 점수 (5개)
'거래품질점수', '위험도점수', '모멘텀점수', '매수매도위험도점수', '리스크조정수익률'

# 비율 조합 지표 (12개)
'초당매수수량_매도총잔량_비율', '매도잔량_매수잔량_비율', '매수잔량_매도잔량_비율',
'초당매도_매수_비율', '초당매수_매도_비율', '현재가_고저범위_위치',
'초당거래대금_당일비중', '초당순매수수량', '초당순매수금액', '초당순매수비율',
'당일거래대금_전틱분봉_비율', '당일거래대금_5틱분봉평균_비율'

# ML 예측 지표 (3개)
'손실확률_ML', '위험도_ML', '예측매수매도위험도점수_ML'
```

### 2.2 컬럼 명명 규칙

| 접두사 | 의미 | 예시 | 생성 위치 |
|--------|------|------|-----------|
| `매수*` | 매수 시점 스냅샷 | `매수등락율`, `매수체결강도` | `backengine_*.py` |
| `매도*` | 매도 시점 스냅샷 | `매도등락율`, `매도체결강도` | `backengine_*.py` |
| `*변화` | 매도-매수 차이 | `등락율변화`, `체결강도변화` | `metrics_enhanced.py` |
| `*변화율` | 매도/매수 비율 | `거래대금변화율` | `metrics_enhanced.py` |
| `*점수` | 복합 계산 점수 | `위험도점수`, `거래품질점수` | `metrics_enhanced.py` |
| `*_ML` | ML 예측값 | `손실확률_ML` | `ml.py` |

### 2.3 파생 지표 계산 로직 위치

| 지표 카테고리 | 파일 | 함수 | 라인 범위 |
|--------------|------|------|-----------|
| 기본 파생 | `analysis/metrics_base.py` | `CalculateDerivedMetrics` | - |
| 강화 파생 | `analysis_enhanced/metrics_enhanced.py` | `CalculateEnhancedDerivedMetrics` | 61-445 |
| ML 예측 | `analysis_enhanced/ml.py` | `PredictLossRisk` | - |

---

## 3. 런타임 변수 매핑 체계

### 3.1 두 가지 실행 환경의 차이

백테스팅 분석 시스템에는 **두 가지 근본적으로 다른 실행 환경**이 존재합니다:

| 항목 | 내부 검증 (DataFrame 기반) | 실제 실행 (exec 기반) |
|------|---------------------------|----------------------|
| **데이터 소스** | `detail.csv` DataFrame | `self.arry_data` 배열 |
| **변수 조회** | `df['컬럼명']` | 로컬 변수 직접 참조 |
| **파생 지표** | `metrics_enhanced.py`에서 계산 | `code_generator.py` 런타임 매핑 |
| **실행 시점** | 백테스트 완료 후 분석 시 | 백테스트 실행 중 |
| **정확도** | 정확함 (완전한 데이터) | 근사치 (런타임 재계산) |

### 3.2 런타임 매핑 블록 (code_generator.py)

세그먼트 필터가 실제 백테스팅 엔진에서 실행될 때, `code_generator.py`의 `_get_segment_runtime_blocks()` 함수가 필요한 변수를 런타임에 계산합니다.

#### 핵심 매핑 블록 (49개)

```python
# 파생 계산 변수 (try/except 패턴)
add_block(
    "초당매수수량",
    ["분당매수수량"],  # 의존성
    try_assign("초당매수수량", "분당매수수량 / 60", "0"),
)

# 스냅샷 매핑 변수 (단순 별칭)
add_block("매수체결강도", ["체결강도"], ["매수체결강도 = 체결강도"], group="snapshot")

# 복합 점수 계산
add_block(
    "위험도점수",
    ["매수등락율", "매수체결강도", "매수당일거래대금", "시가총액", ...],
    [
        "위험도점수 = 0",
        "if 매수등락율 >= 20: 위험도점수 += 20",
        # ... (18개 조건)
        "위험도점수 = min(100, 위험도점수)",
    ],
)
```

### 3.3 변수 가용성 매트릭스

| 변수명 | backengine (Tick) | backengine (Min) | code_generator 매핑 | detail.csv |
|--------|-------------------|------------------|---------------------|------------|
| `현재가` | ✅ 직접 | ✅ 직접 | ✅ snapshot | ✅ `매수가` |
| `시가총액` | ✅ 직접 | ✅ 직접 | ❌ (직접 사용) | ✅ 직접 |
| `초당매수수량` | ✅ 직접 | ❌ 없음 | ✅ `분당/60` | ✅ `매수초당매수수량` |
| `분당매수수량` | ❌ 없음 | ✅ 직접 | - | ❌ 없음 |
| `위험도점수` | ❌ 없음 | ❌ 없음 | ✅ 복합 계산 | ✅ 계산됨 |
| `거래품질점수` | ❌ 없음 | ❌ 없음 | ✅ 복합 계산 | ✅ 계산됨 |

---

## 4. 세그먼트 필터 분석 → 실제 적용 불일치 원인

### 4.1 확인된 문제점

#### 문제 1: 틱 엔진에서 `초당*` 변수 덮어쓰기 위험 ⚠️

**현상**: 
- 틱 엔진에서는 `초당매수수량`이 직접 정의됨 (`self.arry_data`에서 언패킹)
- `code_generator.py`는 `분당매수수량 / 60`으로 재계산 시도
- `try/except`에서 `분당매수수량`이 없으면 `초당매수수량 = 0` 설정

**코드** (`code_generator.py` Line 595-599):
```python
add_block(
    "초당매수수량",
    ["분당매수수량"],
    try_assign("초당매수수량", "분당매수수량 / 60", "0"),  # ← 틱에서 0으로 덮어쓰기!
)
```

**영향**: 틱 백테스트 시 세그먼트 필터에서 `초당매수수량` 관련 조건이 모두 `0`으로 평가됨

**해결 방안**:
```python
# 수정된 매핑 블록
add_block(
    "초당매수수량",
    ["분당매수수량"],
    [
        "try:",
        "    if '초당매수수량' not in dir():",  # 기존 변수 확인
        "        초당매수수량 = 분당매수수량 / 60",
        "except NameError:",
        "    pass  # 이미 정의된 경우 유지",
    ],
)
```

#### 문제 2: 파생 지표 계산식 미세 차이

**현상**:
- `metrics_enhanced.py`와 `code_generator.py`의 동일 지표 계산식이 소수점 단위에서 차이

**예시 - 위험도점수**:

`metrics_enhanced.py` (Line 157-215):
```python
# 1) 과열(추격 매수) 위험
df.loc[buy_ret >= 20, '위험도점수'] += 20
df.loc[buy_ret >= 25, '위험도점수'] += 10
df.loc[buy_ret >= 30, '위험도점수'] += 10

# 2) 매수체결강도 약세 위험  
df.loc[buy_power < 80, '위험도점수'] += 15
df.loc[buy_power < 60, '위험도점수'] += 10
# ... (8가지 조건)
```

`code_generator.py` (Line 818-852):
```python
"if 매수등락율 >= 20: 위험도점수 += 20",
"if 매수등락율 >= 25: 위험도점수 += 10",
"if 매수등락율 >= 30: 위험도점수 += 10",
"if 매수체결강도 < 80: 위험도점수 += 15",
"if 매수체결강도 < 60: 위험도점수 += 10",
# ... 동일하지만 조건 분기가 벡터화 vs if문으로 다름
```

**영향**: 극단적인 케이스에서 ±2점 차이 발생 가능 → 경계값 근처 거래에서 필터 결과 차이

#### 문제 3: 세그먼트 경계 동적 vs 고정

**과거 문제** (해결됨):
- `SegmentBuilder`가 매번 분위수(quantile) 재계산
- 분석 시점과 적용 시점의 데이터가 다르면 경계가 달라짐

**해결책** (`back_static.py`):
```python
def _load_segment_config_from_ranges(ranges_path: str) -> SegmentConfig:
    """ranges.csv에서 고정 경계값 로드"""
    df = pd.read_csv(ranges_path)
    # ... fixed 모드로 정확한 경계 사용
    return SegmentConfig(mode='fixed', ...)
```

#### 문제 4: Lookahead 데이터 사용

**현상**:
- `detail.csv`에는 매도 시점 정보 포함 (`매수매도위험도점수` 등)
- 실제 실행 시에는 매수 시점 변수만 사용 가능

**영향**: 매도 시점 정보를 활용한 필터 조건은 내부 검증과 실제 실행에서 완전히 다른 결과

### 4.2 불일치 정도 예측

| 원인 | 영향도 | 현재 상태 |
|------|--------|----------|
| 세그먼트 경계 불일치 | 🔴 높음 | ✅ 해결됨 (ranges.csv 고정) |
| if/elif 논리 구조 | 🟠 중간 | ✅ 해결됨 (elif 구조) |
| 틱 엔진 변수 덮어쓰기 | 🔴 높음 | ⚠️ 미해결 |
| 파생 지표 계산 차이 | 🟡 낮음 | ⚠️ 주의 필요 |
| Lookahead 데이터 | 🟠 중간 | ⚠️ 설계 한계 |

---

## 5. 코드 흐름 다이어그램

### 5.1 분석 파이프라인

```
백테스트 완료
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  RunEnhancedAnalysis() - analysis_enhanced/runner.py        │
├─────────────────────────────────────────────────────────────┤
│  1. GetResultDataframe() → 원본 DataFrame 생성              │
│  2. CalculateEnhancedDerivedMetrics() → 93개+ 파생 지표 추가│
│  3. Phase 2: 세그먼트 분석 (시가총액 × 시간대)              │
│  4. Phase 3: 필터 조합 최적화                               │
│  5. Template Comparison: 최적 템플릿 선택                   │
│  6. code_generator.py → segment_code_final.txt 생성         │
│  7. segment_verification.csv → 예측 vs 실제 비교            │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  출력 파일 (backtester/backtesting_output/{전략명}/)        │
├─────────────────────────────────────────────────────────────┤
│  • {전략명}_detail.csv          : 거래 상세 + 파생 지표     │
│  • {전략명}_filter.csv          : 필터 분석 결과            │
│  • {전략명}_combos.csv          : 최적 필터 조합            │
│  • {전략명}_segment_code.txt    : 필터 블록만               │
│  • {전략명}_segment_code_final.txt: 완성된 전략 코드        │
│  • {전략명}_segment_verification.csv: 검증 결과             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 런타임 매핑 흐름

```
segment_code_final.txt 로드
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Strategy() 함수 내부 - backengine_kiwoom_tick.py           │
├─────────────────────────────────────────────────────────────┤
│  1. self.arry_data에서 변수 언패킹                          │
│     → 현재가, 등락율, 체결강도, 시가총액, 초당매수수량 등   │
│                                                             │
│  2. 런타임 매핑 프리앰블 실행                               │
│     → 매수등락율 = 등락율                                   │
│     → 매수체결강도 = 체결강도                               │
│     → 위험도점수 = (복합 계산)                              │
│                                                             │
│  3. 세그먼트 필터 조건 평가                                 │
│     → if 시가총액 >= 6000 and 시분초 >= 90000 and ...       │
│     → 필터통과 = (조건 결과)                                │
│                                                             │
│  4. 매수 신호와 필터 결합                                   │
│     → 매수 = 매수 and 필터통과                              │
│                                                             │
│  5. exec(self.buystg) 실행                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 개선 방안 및 권장사항

### 6.1 긴급 수정 필요 (P0)

#### 틱 엔진 변수 덮어쓰기 방지

**파일**: `backtester/segment_analysis/code_generator.py`
**위치**: `_get_segment_runtime_blocks()` 함수 (Line 576-871)

```python
# 수정 전
add_block(
    "초당매수수량",
    ["분당매수수량"],
    try_assign("초당매수수량", "분당매수수량 / 60", "0"),
)

# 수정 후
add_block(
    "초당매수수량",
    ["분당매수수량"],
    [
        "# 틱 엔진: 초당매수수량이 이미 존재하면 유지",
        "try:",
        "    if '초당매수수량' not in dir() or 초당매수수량 == 0:",
        "        초당매수수량 = 분당매수수량 / 60",
        "except NameError:",
        "    초당매수수량 = 0",
    ],
)
```

### 6.2 단기 개선 (P1)

#### 파생 지표 계산 통합

현재 두 곳에서 동일 지표를 다르게 계산하고 있어 유지보수와 일관성 문제 발생.

**제안**: 공통 계산 로직을 별도 모듈로 추출

```python
# backtester/common/derived_metrics.py (신규)
def calc_risk_score(등락율, 체결강도, 당일거래대금, 시가총액, ...):
    """통합 위험도점수 계산 - DataFrame과 스칼라 모두 지원"""
    score = 0
    # ... 공통 로직
    return score
```

### 6.3 중기 개선 (P2)

#### 검증 자동화 시스템

```python
# 신규 기능: segment_verification_enhanced.py
def verify_filter_consistency(
    df_detail: pd.DataFrame,
    segment_code_path: str,
    tolerance: float = 0.01,
) -> Dict:
    """
    내부 검증 결과와 실제 실행 결과의 일관성 자동 검증
    
    Returns:
        {
            'match_ratio': float,  # 일치 비율
            'discrepancies': List[Dict],  # 불일치 케이스
            'root_causes': List[str],  # 추정 원인
        }
    """
```

---

## 7. 핵심 파일 레퍼런스

| 파일 | 역할 | 핵심 함수/클래스 |
|------|------|-----------------|
| `analysis_enhanced/runner.py` | 분석 오케스트레이션 | `RunEnhancedAnalysis()` |
| `analysis_enhanced/metrics_enhanced.py` | 파생 지표 계산 | `CalculateEnhancedDerivedMetrics()` |
| `segment_analysis/code_generator.py` | 조건식 코드 생성 | `build_segment_final_code()`, `_get_segment_runtime_blocks()` |
| `segment_analysis/segment_apply.py` | DataFrame 마스크 생성 | `build_segment_mask_from_global_best()` |
| `backengine_kiwoom_tick.py` | 틱 백테스팅 엔진 | `Strategy()` (Line 432-738) |
| `backengine_kiwoom_min.py` | 분봉 백테스팅 엔진 | `Strategy()` (상속) |
| `detail_schema.py` | 컬럼 스키마 관리 | `reorder_detail_columns()` |

---

## 8. 결론

### 8.1 현재 시스템 강점

1. **체계적인 분석 파이프라인**: 93개+ 파생 지표 자동 계산
2. **세그먼트 기반 최적화**: 시가총액 × 시간대별 맞춤 필터
3. **자동 코드 생성**: 분석 결과를 실행 가능한 조건식으로 변환
4. **검증 체계**: `segment_verification.csv`로 예측 vs 실제 비교

### 8.2 주요 개선 필요 영역

1. **틱 엔진 호환성**: `초당*` 변수 매핑 로직 수정 필요
2. **계산 로직 통합**: 두 곳의 파생 지표 계산 일원화
3. **자동 검증 강화**: 불일치 발생 시 자동 경고 시스템

### 8.3 예상 불일치율

현재 시스템에서 세그먼트 필터 분석 결과와 실제 적용 결과의 예상 불일치율:

| 엔진 타입 | 예상 불일치율 | 주요 원인 |
|----------|--------------|----------|
| 분봉 (Min) | 1-3% | 파생 지표 계산 미세 차이 |
| 틱 (Tick) | 10-30% | `초당*` 변수 덮어쓰기 + 계산 차이 |

**권장 조치**: 틱 엔진 변수 매핑 수정 후 불일치율 1-3%로 통일 가능

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0 | 2026-01-07 | 초안 작성 |
