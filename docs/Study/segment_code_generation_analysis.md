# 세그먼트 코드 생성 과정 분석 및 런타임 불일치 해결 방안

**작성일:** 2025-01-03  
**목적:** `*_segment_code.txt` 생성 과정을 상세 분석하고, 매수 조건식과의 불일치 문제 원인 파악 및 해결 방안 제시

---

## 1. 개요

### 1.1 문제 정의
- **현상:** 백테스터에서 생성된 세그먼트 필터 조건식(`*_segment_code.txt`)을 실시간 매수 조건식에 적용 시 동작 불일치 발생
- **핵심 원인:** 백테스트 시점 컬럼명과 실시간 런타임 컬럼명 간의 차이
- **영향 범위:** 세그먼트 필터의 실효성 저하, 예상 수익과 실제 수익 간 괴리

### 1.2 세그먼트 분석 파이프라인 구조
```
┌─────────────────────────────────────────────────────────────────┐
│ Phase 1: 데이터 준비                                             │
│  - detail.csv 로드 및 정규화                                     │
│  - normalize_segment_columns() 호출 → B_/S_ 접두사 표준화       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 2: 세그먼트 분석 (run_phase2)                             │
│  1. SegmentBuilder.build_segments()                             │
│     - 시가총액/시간 기준으로 데이터 분할                         │
│     - runtime_market_cap_ranges, runtime_time_ranges 저장       │
│                                                                  │
│  2. FilterEvaluator.evaluate_all_segments()                     │
│     - 각 세그먼트별 필터 후보 평가                               │
│     - 백테스트 컬럼명(B_등락율, B_체결강도 등) 기준 분석         │
│     - 출력: *_segment_filters.csv                               │
│                                                                  │
│  3. CombinationOptimizer.optimize_global_combination()          │
│     - 세그먼트별 필터 조합 최적화                                │
│     - global_best 구조 생성 (아래 상세)                         │
│                                                                  │
│  4. build_segment_filter_code()                                 │
│     - global_best → Python 조건식 변환                          │
│     - 출력: *_segment_code.txt                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Phase 3: 최종 코드 통합 (runner.py)                             │
│  - build_segment_final_code()                                   │
│  - 매수 조건식 + 세그먼트 필터 병합                              │
│  - 런타임 매핑 코드 주입 (_inject_segment_runtime_preamble)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. `*_segment_filters.csv` 생성 과정

### 2.1 FilterEvaluator 동작 원리
**파일:** `backtester/segment_analysis/filter_evaluator.py`

#### 2.1.1 컬럼 선택 로직
```python
def _select_columns(self, df: pd.DataFrame) -> List[str]:
    # 1. 명시적 매수 컬럼 (BUY_TIME_FILTER_COLUMNS)
    explicit_buy_columns = ['B_등락율', 'B_체결강도', 'B_당일거래대금', ...]
    
    # 2. 매수/B_ 접두사 컬럼 자동 탐지
    for col in df.columns:
        if col.startswith('매수') or col.startswith('B_'):
            feature_columns.append(col)
    
    # 3. 추가 컬럼 (시가총액, 모멘텀점수 등)
    # 4. ML 컬럼 (allow_ml_filters=True 시)
```

#### 2.1.2 필터 후보 평가 과정
```python
for col in selected_columns:
    values = df[col]
    thresholds = values.quantile([0.05, 0.1, 0.2, 0.8, 0.9, 0.95])
    
    for threshold in thresholds:
        for direction in ('less', 'greater'):
            # 'less': value >= threshold 인 거래만 유지 (threshold 미만 제외)
            # 'greater': value < threshold 인 거래만 유지 (threshold 이상 제외)
            
            remaining_profit = calc_profit(keep_mask)
            improvement = remaining_profit - total_profit
            
            if improvement > 0 and passes_statistical_test:
                candidates.append({
                    'column': col,              # 예: 'B_등락율'
                    'threshold': threshold,     # 예: 5.5
                    'direction': direction,     # 예: 'less'
                    'improvement': improvement,
                    'exclusion_ratio': ...,
                    'efficiency': ...,
                })
```

#### 2.1.3 출력 예시 (`*_segment_filters.csv`)
| segment_id | column | threshold | direction | improvement | filter_name |
|------------|--------|-----------|-----------|-------------|-------------|
| 중형주_09_10 | B_등락율 | 5.5 | less | 150000 | B_등락율 5.50 미만 제외 |
| 중형주_09_10 | B_체결강도 | 80 | greater | 120000 | B_체결강도 80 이상 제외 |

**핵심:** CSV에는 **백테스트 컬럼명 (B_등락율)** 이 저장됨

---

## 3. `*_segment_code.txt` 생성 과정

### 3.1 데이터 흐름
```
segment_filters.csv
       ↓
CombinationOptimizer.optimize_global_combination()
       ↓
global_best 구조 생성
       ↓
build_segment_filter_code(global_best, runtime_ranges)
       ↓
*_segment_code.txt
```

### 3.2 global_best 구조
```python
global_best = {
    'combination': {
        '중형주_09_10': {
            'filters': [
                {
                    'column': 'B_등락율',     # ← 백테스트 컬럼명
                    'threshold': 5.5,
                    'direction': 'less',
                    'filter_name': 'B_등락율 5.50 미만 제외'
                },
                {
                    'column': 'B_체결강도',
                    'threshold': 80,
                    'direction': 'greater',
                }
            ],
            'improvement': 270000,
            'remaining_trades': 45,
        },
        '대형주_14_15': { ... }
    },
    'score': 500000,
    'excluded_trades': 120,
}
```

### 3.3 코드 생성 로직
**파일:** `backtester/segment_analysis/code_generator.py`

#### 3.3.1 핵심 함수
```python
def build_segment_filter_code(
    global_best: dict,
    seg_config: SegmentConfig,
    runtime_market_cap_ranges: Dict[str, Tuple[float, float]],
    runtime_time_ranges: Dict[str, Tuple[int, int]],
) -> Tuple[List[str], Dict[str, int]]:
    
    for seg_id in sorted(combo_map.keys()):
        # 1. 세그먼트 조건 생성
        seg_condition = _build_segment_condition(seg_id, cap_ranges, time_ranges)
        # 예: "(시가총액 >= 1000 and 시가총액 < 5000 and 시분초 >= 90000 and 시분초 < 100000)"
        
        # 2. 필터 조건 생성
        for flt in filters:
            cond = _build_filter_condition(flt)
            # 예: "(B_등락율 >= 5.5)" ← 백테스트 컬럼명 그대로 사용
            conditions.append(cond)
        
        # 3. 코드 조립
        lines.append(f"if {seg_condition}:")
        lines.append(f"    if ({' and '.join(conditions)}):")
        lines.append(f"        필터통과 = True")
```

#### 3.3.2 _build_filter_condition 상세
```python
def _build_filter_condition(candidate: dict) -> Optional[str]:
    column = candidate.get('column')       # 예: 'B_등락율'
    threshold = candidate.get('threshold') # 예: 5.5
    direction = candidate.get('direction') # 예: 'less'
    
    # direction='less': 해당 값 미만을 제외 → 유지 조건은 >= threshold
    # direction='greater': 해당 값 이상을 제외 → 유지 조건은 < threshold
    op = ">=" if direction == 'less' else "<"
    
    return f"({column} {op} {threshold})"
    # 결과: "(B_등락율 >= 5.5)"
```

### 3.4 생성된 코드 예시
```python
# 세그먼트 필터 조건식 (자동 생성)
# 시분초는 매수시간(HHMMSS) 기준으로 계산 필요
필터통과 = False

# [중형주_09_10]
if (시가총액 >= 1000 and 시가총액 < 5000 and 시분초 >= 90000 and 시분초 < 100000):
    if (B_등락율 >= 5.5 and B_체결강도 < 80):
        필터통과 = True

# [대형주_14_15]
elif (시가총액 >= 5000 and 시분초 >= 140000 and 시분초 < 150000):
    if (B_당일거래대금 >= 50000):
        필터통과 = True
```

**문제점:** 
- 조건식에 `B_등락율`, `B_체결강도` 등 백테스트 컬럼명이 그대로 사용됨
- 실시간 엔진에는 이러한 컬럼이 존재하지 않음 → NameError 또는 조건 불일치

---

## 4. 런타임 불일치 문제 분석

### 4.1 백테스트 vs 실시간 컬럼명 차이

| 백테스트 (detail.csv) | 실시간 엔진 | 설명 |
|----------------------|------------|------|
| `B_등락율` | `등락율` | B_ 접두사 없음 |
| `B_체결강도` | `체결강도` | B_ 접두사 없음 |
| `B_당일거래대금` | `당일거래대금` | B_ 접두사 없음 |
| `B_초당매수수량` | `초당매수수량` (분봉: 없음) | 초당/분당 timeframe 차이 |
| `B_분당매수수량` | (tick봉: 없음) | 초당/분당 timeframe 차이 |
| `B_매수총잔량_B_매도총잔량_비율` | 계산 필요 | 파생 지표 |
| `시가총액` | `시가총액` | ✅ 동일 |
| `시분초` | `시분초` | ✅ 동일 |

### 4.2 현재 해결 메커니즘: 런타임 매핑

**파일:** `code_generator.py` - `_inject_segment_runtime_preamble()`

#### 4.2.1 동작 원리
```python
# 1. 세그먼트 코드에서 사용된 변수 추출
used_vars = _extract_segment_used_variables(segment_code_lines)
# 예: ['B_등락율', 'B_체결강도', 'B_초당매수수량', ...]

# 2. 런타임 매핑 블록 선택
blocks = _get_segment_runtime_blocks()
needed = _resolve_runtime_dependencies(used_vars, blocks)

# 3. 매핑 코드 생성
lines = []
lines.append("# === Segment filter runtime mapping (buy-time) ===")
lines.append("B_등락율 = 등락율")
lines.append("B_체결강도 = 체결강도")
lines.append("try:")
lines.append("    B_초당매수수량 = 초당매수수량")
lines.append("except NameError:")
lines.append("    B_초당매수수량 = 분당매수수량")
```

#### 4.2.2 _get_segment_runtime_blocks 예시
```python
def _get_segment_runtime_blocks():
    blocks = []
    
    # Snapshot 매핑 (B_ prefix)
    add_block("B_등락율", ["등락율"], ["B_등락율 = 등락율"], group="snapshot")
    add_block("B_체결강도", ["체결강도"], ["B_체결강도 = 체결강도"], group="snapshot")
    add_block("B_가", ["현재가"], ["B_가 = 현재가"], group="snapshot")
    
    # 초당/분당 매핑 (timeframe fallback)
    add_block(
        "B_초당매수수량",
        ["초당매수수량", "분당매수수량"],
        [
            "try:",
            "    B_초당매수수량 = 초당매수수량",
            "except NameError:",
            "    B_초당매수수량 = 분당매수수량",
        ],
    )
    
    # 파생 지표 계산
    add_block(
        "B_매수총잔량_B_매도총잔량_비율",
        ["B_매수총잔량", "B_매도총잔량"],
        ["B_매수총잔량_B_매도총잔량_비율 = (B_매수총잔량 / B_매도총잔량) if B_매도총잔량 > 0 else 0"],
    )
    
    return blocks
```

### 4.3 런타임 매핑의 한계

#### 4.3.1 누락 가능성
- **문제:** 새로운 컬럼이 필터로 선택될 경우 런타임 블록에 정의되지 않았을 수 있음
- **증상:** `NameError: name 'B_XXX' is not defined`
- **예시:** ML 컬럼 (`B_손실확률_ML`), 새로 추가된 파생 지표

#### 4.3.2 계산 로직 불일치
- **문제:** 백테스트와 실시간에서 파생 지표 계산 방식이 다를 수 있음
- **예시:** `거래품질점수`, `위험도점수` - 백테스트는 후처리 계산, 실시간은 근사 계산
- **결과:** 같은 threshold라도 실제 필터링 결과가 다름

#### 4.3.3 Timeframe 차이
- **문제:** tick봉 백테스트 → 분봉 실전 적용 시 초당/분당 데이터 불일치
- **예시:** `B_초당매수수량` 조건 → 분봉에는 `분당매수수량`만 존재
- **해결:** fallback 로직 있으나 데이터 해상도 차이로 정확도 저하

---

## 5. 불일치 원인 정리

### 5.1 설계 구조적 원인

#### 원인 1: 필터 평가 단계에서 백테스ト 컬럼명 사용
- **위치:** `filter_evaluator.py` - `evaluate_segment()`
- **동작:** `detail.csv`의 B_ 접두사 컬럼을 그대로 사용
- **문제:** 코드 생성 시 실시간 컬럼명으로 변환되지 않음

#### 원인 2: 코드 생성 단계에서 직접 변환 없음
- **위치:** `code_generator.py` - `_build_filter_condition()`
- **동작:** `candidate['column']` 값을 그대로 코드에 삽입
- **문제:** 백테스트 컬럼명(B_등락율) → 실시간 컬럼명(등락율) 변환 없음

#### 원인 3: 런타임 매핑의 사후 보정 방식
- **위치:** `code_generator.py` - `_inject_segment_runtime_preamble()`
- **동작:** 생성된 코드 앞에 매핑 코드를 주입하여 사후 보정
- **문제:** 누락 가능성, 계산 로직 불일치, 유지보수 부담

### 5.2 근본 원인 다이어그램
```
[FilterEvaluator]
   ↓ 백테스트 컬럼명 (B_등락율)
[segment_filters.csv]
   ↓ 그대로 전달
[CombinationOptimizer]
   ↓ 그대로 전달
[global_best.combination[seg_id].filters[].column]
   ↓ 그대로 사용
[_build_filter_condition()] → "(B_등락율 >= 5.5)"
   ↓
[*_segment_code.txt] ← 백테스트 컬럼명 포함
   ↓
[런타임 매핑 주입] ← 사후 보정 (불완전)
   ↓
[실시간 엔진] ← NameError 또는 계산 불일치
```

---

## 6. 해결 방안

### 6.1 단기 해결책: 런타임 매핑 블록 보강

#### 방안 A: 자동 매핑 블록 생성
```python
def _generate_runtime_mapping_for_all_buy_columns():
    """
    BUY_TIME_FILTER_COLUMNS의 모든 B_ 컬럼에 대해 자동으로 매핑 블록 생성
    """
    from backtester.analysis.metric_registry import BUY_TIME_FILTER_COLUMNS
    
    blocks = []
    for col in BUY_TIME_FILTER_COLUMNS:
        if col.startswith('B_'):
            base_name = col[2:]  # B_ 제거
            blocks.append({
                'names': {col},
                'deps': {base_name},
                'lines': [f"{col} = {base_name}"],
                'group': 'auto_snapshot'
            })
    return blocks
```

**장점:**
- 구현 간단
- 기존 코드 최소 변경

**단점:**
- 근본 해결 아님
- ML 컬럼, 파생 지표는 여전히 수동 추가 필요

#### 방안 B: 필터 검증 단계 추가
```python
def validate_filter_columns_before_code_gen(global_best):
    """
    코드 생성 전 모든 필터 컬럼이 런타임 블록에 정의되어 있는지 검증
    """
    runtime_blocks = _get_segment_runtime_blocks()
    defined_vars = set()
    for block in runtime_blocks:
        defined_vars.update(block['names'])
    
    for seg_id, combo in global_best['combination'].items():
        for flt in combo.get('filters', []):
            col = flt['column']
            if col not in defined_vars:
                warnings.warn(f"Missing runtime mapping for column: {col}")
                # 자동 생성 또는 에러 발생
```

### 6.2 중장기 해결책: 컬럼명 정규화

#### 방안 C: 필터 평가 시 실시간 컬럼명 사용
```python
# filter_evaluator.py 수정
def evaluate_segment(self, segment_df: pd.DataFrame, segment_id: str):
    for col in self._select_columns(segment_df):
        # 백테스트 컬럼명 → 실시간 컬럼명 변환
        runtime_col = self._to_runtime_column(col)
        
        # ... 평가 로직 ...
        
        candidates.append({
            'column': runtime_col,  # ← 실시간 컬럼명 저장
            'backtest_column': col, # ← 참조용
            ...
        })

def _to_runtime_column(self, col: str) -> str:
    """백테스트 컬럼명 → 실시간 컬럼명 변환"""
    if col.startswith('B_'):
        return col[2:]  # B_등락율 → 등락율
    if col.startswith('S_'):
        return col[2:]  # S_등락율 → (매도 컬럼, 제외됨)
    return col
```

**장점:**
- 근본적 해결
- 런타임 매핑 불필요
- 코드 가독성 향상

**단점:**
- 영향 범위 큼 (필터 평가, 조합 최적화, 코드 생성 전체 수정)
- 기존 CSV 파일과 호환성 고려 필요

#### 방안 D: 이중 컬럼 저장
```python
# global_best 구조 확장
{
    'column': '등락율',          # 실시간 컬럼명 (코드 생성용)
    'backtest_column': 'B_등락율', # 백테스트 컬럼명 (검증/로깅용)
    'threshold': 5.5,
    'direction': 'less',
}
```

**장점:**
- 하위 호환성 유지
- 디버깅/검증 용이

**단점:**
- 데이터 중복
- 구현 복잡도 증가

### 6.3 종합 추천 방안

#### Phase 1: 즉시 적용 (안전성 확보)
1. **런타임 블록 검증 추가** (방안 B)
   - 코드 생성 전 누락된 컬럼 경고
   - 자동 기본 매핑 생성 (`B_XXX = XXX`)

2. **자동 매핑 블록 확장** (방안 A)
   - `BUY_TIME_FILTER_COLUMNS` 전체 자동 매핑
   - ML 컬럼 패턴 매칭 추가 (`*_ML`)

#### Phase 2: 중기 개선 (근본 해결)
3. **컬럼명 정규화** (방안 C)
   - 필터 평가 단계부터 실시간 컬럼명 사용
   - 이중 컬럼 저장 (방안 D) 병행

4. **테스트 강화**
   - 세그먼트 코드 실행 가능성 검증 (exec 테스트)
   - 런타임 변수 존재 여부 체크

---

## 7. 구현 우선순위

### 7.1 High Priority (1주 이내)
1. ✅ **런타임 매핑 블록 자동 생성** (`_generate_runtime_mapping_for_all_buy_columns`)
2. ✅ **필터 컬럼 검증 로직 추가** (`validate_filter_columns_before_code_gen`)
3. ⚠️ **ML 컬럼 런타임 매핑 추가** (손실확률_ML, 위험도_ML 등)

### 7.2 Medium Priority (2-4주)
4. **컬럼명 정규화 적용** (`_to_runtime_column` 구현 및 통합)
5. **세그먼트 코드 실행 테스트 자동화**
6. **문서 업데이트** (사용자 가이드, 런타임 매핑 설명)

### 7.3 Low Priority (장기)
7. **파생 지표 계산 로직 통일** (백테스트 ↔ 실시간)
8. **Timeframe 자동 감지 및 변환** (초당 ↔ 분당)

---

## 8. 결론

### 8.1 핵심 발견 사항
1. **segment_filters.csv는 백테스트 컬럼명을 기반으로 생성됨**
2. **segment_code.txt는 filters.csv의 컬럼명을 그대로 사용하여 코드 변환**
3. **런타임 매핑은 사후 보정 방식이며, 누락 가능성과 불일치 위험 존재**

### 8.2 불일치 문제의 본질
- **설계 시점:** 백테스트 분석 최적화에 초점 (B_ 접두사 표준화)
- **운영 시점:** 실시간 엔진 적용 시 컬럼명 불일치 발생
- **보정 메커니즘:** 런타임 매핑 주입 (불완전, 유지보수 부담)

### 8.3 권장 조치
1. **즉시:** 런타임 블록 검증 및 자동 확장 적용
2. **중기:** 컬럼명 정규화를 통한 근본 해결
3. **장기:** 백테스트-실시간 간 로직 완전 통일

---

## 부록 A: 주요 함수 참조

### A.1 세그먼트 코드 생성 관련
| 함수 | 파일 | 역할 |
|------|------|------|
| `build_segment_filter_code()` | code_generator.py | global_best → 조건식 변환 |
| `_build_segment_condition()` | code_generator.py | 세그먼트 범위 조건 생성 |
| `_build_filter_condition()` | code_generator.py | 필터 임계값 조건 생성 |
| `_inject_segment_runtime_preamble()` | code_generator.py | 런타임 매핑 주입 |
| `_get_segment_runtime_blocks()` | code_generator.py | 매핑 블록 정의 |

### A.2 필터 평가 관련
| 함수 | 파일 | 역할 |
|------|------|------|
| `evaluate_all_segments()` | filter_evaluator.py | 전체 세그먼트 필터 평가 |
| `evaluate_segment()` | filter_evaluator.py | 단일 세그먼트 필터 평가 |
| `_select_columns()` | filter_evaluator.py | 평가 대상 컬럼 선택 |
| `_evaluate_threshold()` | filter_evaluator.py | 임계값 효과 측정 |

### A.3 조합 최적화 관련
| 함수 | 파일 | 역할 |
|------|------|------|
| `optimize_global_combination()` | combination_optimizer.py | 전역 최적 조합 탐색 |
| `generate_local_combinations()` | combination_optimizer.py | 세그먼트별 필터 조합 |

---

## 부록 B: 런타임 매핑 블록 전체 목록

현재 `_get_segment_runtime_blocks()`에 정의된 주요 매핑:

### B.1 Snapshot 매핑 (단순 B_ 제거)
```
B_등락율 = 등락율
B_체결강도 = 체결강도
B_당일거래대금 = 당일거래대금
B_회전율 = 회전율
B_고가 = 고가
B_저가 = 저가
B_시가 = 시가
B_가 = 현재가
```

### B.2 Timeframe Fallback 매핑
```
B_초당매수수량 = 초당매수수량 (fallback: 분당매수수량)
B_초당매도수량 = 초당매도수량 (fallback: 분당매도수량)
B_초당거래대금 = 초당거래대금 (fallback: 분당거래대금)
```

### B.3 파생 지표 계산
```
B_스프레드 = ((매도호가1 - 매수호가1) / 매수호가1) * 100
B_호가잔량비 = (매수총잔량 / 매도총잔량) * 100
B_변동폭 = 고가 - 저가
거래품질점수 = (체결강도, 호가잔량비 등 기반 계산)
위험도점수 = (등락율, 변동폭 등 기반 계산)
```

### B.4 누락 가능 항목 (수동 추가 필요)
- ML 컬럼: `B_손실확률_ML`, `B_위험도_ML`, `B_예측매수매도위험도점수_ML`
- 복합 파생 지표: `B_모멘텀점수`, `B_타이밍점수`
- 새로 추가된 컬럼

---

**작성자:** Sisyphus (AI Agent)  
**검토 필요:** 컬럼명 정규화 적용 시 영향 범위 상세 검토, 실시간 테스트 환경 구축
