# 반복적 조건식 개선 시스템 (ICOS) 가능성 분석 보고서

> **Iterative Condition Optimization System (ICOS) Feasibility Study**
> **작성일**: 2026-01-12
> **버전**: 1.0
> **브랜치**: feature/iterative-condition-optimizer

---

## 1. Executive Summary (요약)

### 1.1 배경
세그먼트 필터 연구 과정에서 **포트폴리오 동적 효과**로 인한 **40-70% 예측-실제 괴리**가 발견되었다.
이는 구조적 한계로, 코드 수정만으로는 해결이 불가능하다.

### 1.2 결론
세그먼트 필터를 "정확한 예측" 도구가 아닌 **"개선 가이드"**로 재정의하고,
**반복적 백테스팅**을 통해 실제 효과를 직접 검증하는 새로운 접근 방식을 제안한다.

### 1.3 핵심 차별점

| 기존 방식 | 새로운 방식 (ICOS) |
|-----------|-------------------|
| 예측 기반 필터 적용 | 실제 백테스팅으로 효과 검증 |
| 단일 실행 | 반복적 개선 (수렴까지) |
| 예측값과 실제값 괴리 | 실제 결과만 사용 |
| 복잡한 주입 로직 | 단순한 조건식 수정 |

---

## 2. 문제 정의 (Problem Statement)

### 2.1 세그먼트 필터의 구조적 한계

#### 포트폴리오 동적 효과 (Portfolio Dynamic Effect)
```
[원본 백테스트]              [필터 적용 후]
거래 A (09:30) → 차단        매수 취소
거래 B (10:00) → 통과        → 예산 여유 발생
거래 C (10:30) → 통과        → 새로운 거래 D 발생!
                              (원본에는 없던 거래)
```

**결과**: 차단된 거래로 인해 포트폴리오 상태가 변하고, 이로 인해 원본에 없던 새로운 거래가 발생.
예측은 "원본 기준"이지만 실제는 "변경된 포트폴리오 기준"으로 동작.

#### 정량적 분석 결과

| 필터 유형 | 예측 차단 | 실제 차단 | 괴리율 |
|-----------|-----------|-----------|--------|
| 거래대금 필터 | 1,247건 | 534건 | 57% |
| 체결강도 필터 | 892건 | 312건 | 65% |
| 시간대 필터 | 2,103건 | 1,891건 | 10% |
| 세그먼트 조합 | 3,421건 | 2,045건 | 40% |

**시간대 필터**만 낮은 괴리율을 보이는 이유: 조건 자체가 독립적 (포트폴리오 무관)

### 2.2 기존 시도 및 실패 원인

#### Solution A: 매수조건 앞 삽입
- **시도**: 세그먼트 필터를 기존 조건 앞에 배치
- **결과**: 포트폴리오 동적 효과 미해결

#### Solution B: 세그먼트 우선 적용
- **시도**: `filter_first` 파라미터로 선제 차단
- **결과**: 여전히 차단 후 새 거래 발생

#### Solution C: 정확한 예측 모드
- **시도**: 모든 틱에서 세그먼트 평가
- **결과**: 복잡도만 증가, 근본 문제 미해결

### 2.3 핵심 통찰

> **"예측의 정확도를 높이려는 시도 자체가 잘못된 접근이었다."**
>
> 세그먼트 필터는 "이 조건을 추가하면 어떤 거래가 차단될지" 예측하는 도구가 아니라,
> "이 조건을 추가하면 전체 성과가 어떻게 변하는지" 직접 측정하는 도구여야 한다.

---

## 3. 제안 솔루션 (Proposed Solution)

### 3.1 ICOS (Iterative Condition Optimization System) 개요

**핵심 원리**: 예측 대신 실측

```
┌─────────────────────────────────────────────────────────────────┐
│                    반복적 조건식 개선 시스템 (ICOS)               │
└─────────────────────────────────────────────────────────────────┘

[1] 기존 조건식으로 백테스트 실행
         │
         ▼
[2] 결과 분석 (손실 거래 패턴 추출)
         │
         ▼
[3] 필터 조건 후보 생성
         │
         ▼
[4] 필터 적용한 새 조건식 생성
         │
         ▼
[5] 새 조건식으로 백테스트 재실행
         │
         ▼
[6] 결과 비교 (이전 vs 현재)
         │
         ▼
[7] 수렴 판정
    ├─ 개선 < threshold → 종료
    └─ 그 외 → [2]로 반복
         │
         ▼
[최종] 최적화된 조건식 출력
```

### 3.2 예측 vs 실측 비교

#### 기존 방식 (예측 기반)
```python
# 원본 백테스트 실행
original_result = backtest(buystg_original)

# 세그먼트 분석으로 차단 대상 "예측"
predicted_blocked = segment_analysis(original_result)  # ← 예측

# 필터 적용 후 결과 "추정"
estimated_result = estimate_filtered_result(original_result, predicted_blocked)
# ↑ 포트폴리오 동적 효과로 인해 40-70% 오차 발생
```

#### 새로운 방식 (실측 기반)
```python
# 기존 조건식으로 백테스트
current_result = backtest(buystg_current)

# 결과 분석으로 필터 후보 생성
filter_candidates = analyze_loss_patterns(current_result)

# 필터 적용한 새 조건식 생성
buystg_new = apply_filter(buystg_current, filter_candidates[0])

# 새 조건식으로 백테스트 "실행" (예측이 아닌 실측!)
new_result = backtest(buystg_new)  # ← 실제 실행

# 실제 결과 비교
improvement = compare(current_result, new_result)
# ↑ 100% 정확한 비교 (둘 다 실제 실행 결과)
```

### 3.3 핵심 장점

1. **정확성**: 예측이 아닌 실측으로 100% 정확한 효과 측정
2. **단순성**: 복잡한 주입 로직 불필요, 단순히 조건식만 수정
3. **반복성**: 수렴까지 자동 반복으로 최적 조건식 탐색
4. **확장성**: 다양한 최적화 알고리즘 (GA, Optuna 등) 연동 가능
5. **검증성**: Walk-Forward 검증으로 오버피팅 방지

---

## 4. 시스템 아키텍처 (System Architecture)

### 4.1 디렉토리 구조

```
backtester/
├── iterative_optimizer/           # 신규 모듈
│   ├── __init__.py               # 패키지 초기화 및 public API
│   ├── config.py                 # 설정 dataclass (IterativeConfig)
│   ├── runner.py                 # 메인 오케스트레이터 (IterativeOptimizer)
│   ├── analyzer.py               # 결과 분석기 (ResultAnalyzer)
│   ├── filter_generator.py       # 필터 생성기 (FilterGenerator)
│   ├── condition_builder.py      # 조건식 빌더 (ConditionBuilder)
│   ├── storage.py                # 저장/로드 (IterationStorage)
│   ├── comparator.py             # 비교 평가 (ResultComparator)
│   ├── convergence.py            # 수렴 판정 (ConvergenceChecker)
│   └── optimization/             # 최적화 알고리즘 (옵션)
│       ├── __init__.py
│       ├── base.py               # 추상 베이스 클래스
│       ├── grid_search.py        # 그리드 서치
│       ├── genetic.py            # 유전 알고리즘
│       ├── bayesian.py           # Optuna 래퍼
│       └── walk_forward.py       # Walk-Forward 검증
```

### 4.2 클래스 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                     IterativeOptimizer                          │
│ ─────────────────────────────────────────────────────────────── │
│ + config: IterativeConfig                                       │
│ + analyzer: ResultAnalyzer                                      │
│ + generator: FilterGenerator                                    │
│ + builder: ConditionBuilder                                     │
│ + storage: IterationStorage                                     │
│ + comparator: ResultComparator                                  │
│ + convergence: ConvergenceChecker                              │
│ ─────────────────────────────────────────────────────────────── │
│ + run(buystg, sellstg) → IterativeResult                       │
│ + run_single_iteration() → IterationResult                     │
│ - _execute_backtest(buystg) → BacktestResult                   │
└─────────────────────────────────────────────────────────────────┘
         │ uses
         ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   ResultAnalyzer    │  │   FilterGenerator   │  │  ConditionBuilder   │
│ ─────────────────── │  │ ─────────────────── │  │ ─────────────────── │
│ + analyze(df_tsg)   │  │ + generate(analysis)│  │ + build(buystg,     │
│   → AnalysisResult  │  │   → List[Filter]    │  │         filters)    │
│                     │  │                     │  │   → str             │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

### 4.3 데이터 흐름

```
                    ┌─────────────┐
                    │  buystg     │
                    │  (초기)     │
                    └──────┬──────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Iteration Loop                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │  Backtest   │───▶│  Analyzer   │───▶│  Generator  │              │
│  │  Engine     │    │             │    │             │              │
│  └─────────────┘    └─────────────┘    └─────────────┘              │
│        ▲                                      │                      │
│        │                                      ▼                      │
│        │            ┌─────────────┐    ┌─────────────┐              │
│        │            │  Comparator │◀───│   Builder   │              │
│        │            │             │    │             │              │
│        │            └──────┬──────┘    └─────────────┘              │
│        │                   │                                         │
│        │                   ▼                                         │
│        │            ┌─────────────┐                                  │
│        └────────────│ Convergence │                                  │
│           (반복)    │   Checker   │                                  │
│                     └──────┬──────┘                                  │
│                            │ (수렴 시 탈출)                          │
└────────────────────────────┼─────────────────────────────────────────┘
                             ▼
                    ┌─────────────┐
                    │  buystg     │
                    │  (최종)     │
                    └─────────────┘
```

---

## 5. 기존 시스템 통합 (Integration)

### 5.1 멀티코어 백테스팅 호환

기존 백테스팅 시스템의 멀티코어 처리를 그대로 활용한다.

```python
# backtester/backtest.py의 기존 구조
class Total:
    def __init__(self, qlist: list):
        self.backQ = qlist[7]  # 백테스팅 큐
        # ...

    def MainLoop(self, beq: list, ticker_list: list, ...):
        # 멀티프로세스 병렬 처리
        for ticker in ticker_list:
            beq[i].put(ticker)  # 백엔진 큐에 작업 전달

# ICOS에서 기존 시스템 재사용
class IterativeOptimizer:
    def _execute_backtest(self, buystg: str) -> BacktestResult:
        """기존 백테스팅 시스템 활용"""
        # 기존 Total 클래스의 멀티코어 처리 재사용
        # beq (백엔진 큐) 활용
        pass
```

### 5.2 기존 분석 도구 활용

```python
# 기존 강화 분석 모듈 재사용
from backtester.analysis_enhanced.runner import RunEnhancedAnalysis

class ResultAnalyzer:
    def analyze(self, df_tsg: pd.DataFrame) -> AnalysisResult:
        """기존 분석 도구 활용"""
        # 기존 세그먼트 분석 결과를 "가이드"로만 활용
        # 실제 효과는 ICOS의 반복 백테스팅으로 검증
        pass
```

### 5.3 코드 생성 재사용

```python
# 기존 코드 생성기 일부 재사용
from backtester.segment_analysis.code_generator import (
    _build_segment_condition,  # 세그먼트 조건 생성
    _inject_segment_filter,     # 필터 삽입 (단순 버전만)
)

class ConditionBuilder:
    def build(self, buystg: str, filters: List[Filter]) -> str:
        """기존 코드 생성 로직 활용 (단순화)"""
        # 복잡한 주입 로직 제거, 단순 조건 추가만
        pass
```

---

## 6. 개발 단계 (Development Phases)

### Phase 1: 핵심 인프라 (Core Infrastructure)

**목표**: 기본 구조 및 설정 시스템 구축

**산출물**:
- `config.py`: IterativeConfig dataclass
- `runner.py`: IterativeOptimizer 스켈레톤
- `__init__.py`: Public API 정의

**검증**: 단위 테스트 통과

### Phase 2: 분석 및 생성 (Analysis & Generation)

**목표**: 결과 분석 및 필터 생성 기능 구현

**산출물**:
- `analyzer.py`: ResultAnalyzer 구현
- `filter_generator.py`: FilterGenerator 구현

**검증**: 실제 백테스트 데이터로 테스트

### Phase 3: 조건식 빌드 및 저장 (Build & Storage)

**목표**: 새 조건식 생성 및 이력 저장 기능 구현

**산출물**:
- `condition_builder.py`: ConditionBuilder 구현
- `storage.py`: IterationStorage 구현

**검증**: 생성된 조건식 문법 검증

### Phase 4: 비교 및 수렴 (Compare & Converge)

**목표**: 결과 비교 및 수렴 판정 기능 구현

**산출물**:
- `comparator.py`: ResultComparator 구현
- `convergence.py`: ConvergenceChecker 구현

**검증**: 3회 반복 실행 테스트

### Phase 5: 최적화 알고리즘 (Optimization)

**목표**: 고급 최적화 알고리즘 연동

**산출물**:
- `optimization/grid_search.py`
- `optimization/genetic.py`
- `optimization/bayesian.py`
- `optimization/walk_forward.py`

**검증**: Walk-Forward 5-fold 검증

### Phase 6: UI 통합 (UI Integration)

**목표**: 기존 UI에 ICOS 기능 통합

**산출물**:
- UI 버튼 및 옵션 추가
- 진행 상황 표시
- 결과 리포트 표시

**검증**: 사용자 수동 테스트

---

## 7. 리스크 분석 (Risk Analysis)

### 7.1 기술적 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 백테스트 반복으로 인한 시간 증가 | 높음 | 중간 | 멀티코어 활용, 캐싱 |
| 오버피팅 | 중간 | 높음 | Walk-Forward 검증 필수화 |
| 필터 조합 폭발 | 중간 | 중간 | Top-K 필터만 적용 |
| 수렴 실패 | 낮음 | 중간 | 최대 반복 횟수 제한 |

### 7.2 운영적 리스크

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| 기존 시스템 호환성 문제 | 중간 | 높음 | 철저한 통합 테스트 |
| 사용자 학습 곡선 | 중간 | 낮음 | 상세 문서화 |
| 유지보수 복잡도 증가 | 낮음 | 중간 | 모듈화, 단일 책임 원칙 |

### 7.3 완화 전략

1. **점진적 개발**: Phase별 검증 후 다음 단계 진행
2. **모듈화**: 각 컴포넌트 독립적으로 테스트 가능
3. **문서화**: 모든 설계 결정 문서화
4. **롤백 계획**: 문제 발생 시 기존 시스템으로 복귀 가능

---

## 8. 성공 기준 (Success Criteria)

### 8.1 기능적 기준

- [ ] 반복 백테스팅 정상 동작 (3회 이상)
- [ ] 필터 적용 후 조건식 문법 검증 통과
- [ ] 결과 비교 및 수렴 판정 정상 동작
- [ ] Walk-Forward 검증 구현

### 8.2 성능 기준

- [ ] 단일 반복 시간: 기존 백테스트 대비 1.5배 이내
- [ ] 메모리 사용량: 기존 대비 2배 이내
- [ ] 멀티코어 활용률: 80% 이상

### 8.3 품질 기준

- [ ] 코드 커버리지: 80% 이상
- [ ] 문서화: 모든 public API에 docstring
- [ ] 린트 통과: flake8, mypy

### 8.4 비즈니스 기준

- [ ] 조건식 개선 후 수익률 향상 (검증용 데이터)
- [ ] 오버피팅 지표: 학습/검증 성능 차이 < 20%

---

## 9. 결론 및 권장사항

### 9.1 결론

**ICOS는 기술적으로 실현 가능하며, 기존 세그먼트 필터의 구조적 한계를 극복할 수 있다.**

핵심 차별점:
1. 예측 → 실측으로 전환하여 정확성 확보
2. 기존 멀티코어 시스템 재활용으로 성능 유지
3. 모듈화 설계로 유지보수성 확보

### 9.2 권장사항

1. **Phase 1부터 시작**: config.py, runner.py 스켈레톤 구현
2. **단계별 검증**: 각 Phase 완료 후 충분한 테스트
3. **문서 기반 개발**: 설계 결정 및 변경 사항 문서화
4. **오버피팅 경계**: Walk-Forward 검증 필수화

### 9.3 다음 단계

1. ✅ 브랜치 정리 완료 (`feature/iterative-condition-optimizer`)
2. ✅ 가능성 분석 문서 작성 (본 문서)
3. ⏳ Phase 1 구현 시작 (`config.py`, `runner.py`)

---

## 부록 A: 참고 문서

- `docs/Study/SystemAnalysis/20260108_Segment_Filter_Prediction_vs_Actual_Discrepancy_Analysis.md`
- `docs/Study/ResearchReports/2026-01-10_Backtesting_Analysis_Methodology_Research.md`
- `docs/Study/Guides/Segment_Filter_Daily_Block_Implementation_Guide.md`

## 부록 B: 코드 설계 원칙

### Pythonic 설계

```python
# 좋은 예: 명확한 타입 힌트, docstring, 단일 책임
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class IterativeConfig:
    """반복적 조건식 개선 시스템 설정.

    Attributes:
        enabled: 시스템 활성화 여부
        max_iterations: 최대 반복 횟수
        convergence_threshold: 수렴 판정 임계값 (개선율)
    """
    enabled: bool = False
    max_iterations: int = 5
    convergence_threshold: float = 0.05  # 5% 이하 개선 시 수렴
```

### 기존 패턴 준수

```python
# STOM 프로젝트 패턴: 한국어 변수명, 큐 기반 통신
class IterativeOptimizer:
    def __init__(self, qlist: list, config: IterativeConfig):
        self.windowQ = qlist[0]  # 메인 윈도우 큐
        self.backQ = qlist[7]    # 백테스팅 큐
        self.config = config

        # 한국어 변수명 (STOM 패턴)
        self.현재반복 = 0
        self.최종결과 = None
```
