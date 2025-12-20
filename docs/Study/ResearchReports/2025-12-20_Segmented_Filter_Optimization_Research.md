# Segmented Filter Optimization Research (2025-12-20)

## 개요

- **작성일**: 2025-12-20
- **버전**: 2.5 (반-동적 분할 구현 반영)
- **목적**: 시가총액/시간 구간 분할 기반 필터 조합 최적화 알고리즘 연구
- **관련 파일**:
  - 데이터: `backtester/graph/stock_bt_C_T_900_920_U2_B_FS_20251220102053*`
  - 조건식: `docs/Condition/Tick/2_Under_review/Condition_Tick_900_920_Enhanced_FilterStudy.md`
- **참고**: 본 문서의 데이터/세그먼트(시가총액·시간 구간)는 연구용 사례이며, 조건식과 시장환경에 따라 변경될 수 있음.

---

## 1. 문제 정의 및 현재 상황 분석

### 1.1 현재 필터 시스템의 한계

#### 데이터 기반 분석 (2025-12-20 백테스트 결과)

아래 지표는 2025-12-20 백테스트 결과를 사례로 사용한다.  
시가총액/시간 구간은 조건식과 시장환경에 따라 달라질 수 있으며 고정값이 아니다.

| 지표 | 값 | 해석 |
|------|-----|------|
| 기간 | 2022-04-01 ~ 2025-12-19 | 약 3년 8개월 |
| 시간대 | 09:00 ~ 09:20 | 조건식 기준(장초 구간 분석) |
| 거래 수 | 14,977건 | 충분한 표본 크기 |
| 총 수익금 | -2,276,225,190원 | 심각한 손실 |
| 승률 | 33.07% | 낮음 |
| 평균 수익률 | -0.76% | 음수 |
| MDD | 210.2% | 매우 높음 |

#### 개별 필터 성과 분석

상위 개선 필터 5개:

| 필터 | 수익 개선 | 제외율 | 잔여 승률 | p값 |
|------|----------|--------|----------|-----|
| 매수스프레드 0.18 미만 제외 | +16.9억 | 77.9% | 31.8% | 0.0192 |
| 매수등락율 11.13 미만 제외 | +16.3억 | 76.0% | 31.5% | 0.0044 |
| 현재가_고저범위_위치 45.89 이상 제외 | +16.2억 | 76.0% | 31.6% | 0.001 |
| 매수체결강도 66.64 이상 제외 | +14.7억 | 76.0% | 26.5% | 0.0 |
| 모멘텀점수 -4.16 이상 제외 | +14.6억 | 71.3% | 28.7% | 0.0 |

**핵심 문제점**:
1. **과도한 제외율**: 대부분의 유효 필터가 70-80%의 거래를 제외
2. **시너지 효과 부재**: 필터 조합 시 개별 효과 합보다 오히려 성과 하락 (-37% ~ -66%)
3. **거래수 급감**: 조합 적용 시 잔여 거래가 1,000건 이하로 감소
4. **구간별 특성 무시**: 시가총액, 시간대별로 유효한 필터가 다를 가능성이 높음

#### 필터 조합의 시너지 문제

현재 필터 조합 분석 결과 (상위 3개):

| 조합 | 개별 개선합 | 조합 개선 | 시너지 | 잔여 거래수 |
|------|-----------|----------|--------|-----------|
| 매수회전율 + 스프레드 | 34.3억 | 21.5억 | -37.4% | 782건 |
| 초당매수_매도 + 스프레드 | 34.3억 | 21.2억 | -38.0% | 843건 |
| 매수총잔량 + 스프레드 | 34.0억 | 21.1억 | -38.1% | 860건 |

**시너지가 음수인 이유 분석**:
- 필터들이 유사한 손실 거래를 중복 제외
- 수익 거래도 함께 제외되어 전체 효과 감소
- 구간별로 다른 필터가 필요함을 시사

### 1.2 연구 가설

1. **구간별 필터 독립성 가설**: 시가총액, 시간대에 따라 최적 필터가 다르다
2. **합산 최적화 가설**: 구간별로 독립 최적화 후 합산하면 전체 성과가 개선된다
3. **시너지 보완 가설**: 다른 구간에서 다른 필터를 사용하면 음수 시너지를 방지할 수 있다

---

## 2. 세그먼트 분할 전략 상세 설계

### 2.1 분할 차원 정의

#### A. 시가총액 분할 (Primary Dimension)

조건식 문서(`Condition_Tick_900_920_Enhanced_FilterStudy.md`)와 일치:

```python
시가총액_구간 = {
    '소형주': 시가총액 < 3000,      # 억원 단위
    '중형주': 3000 <= 시가총액 < 10000,
    '대형주': 시가총액 >= 10000
}
```

**분할 근거**:
- 소형주: 변동성 높음, 호가 스프레드 큼, 체결강도 영향 큼
- 중형주: 균형적 특성, 기관 참여 시작
- 대형주: 안정적, 외국인/기관 중심, 모멘텀 중요

#### B. 시간대 분할 (Secondary Dimension)

조건식 문서와 일치:

```python
시간_구간 = {
    'T1_090000_090500': 90000 <= 시분초 < 90500,   # 시초가 형성기
    'T2_090500_091000': 90500 <= 시분초 < 91000,   # 초기 변동기
    'T3_091000_091500': 91000 <= 시분초 < 91500,   # 안정화기
    'T4_091500_092000': 91500 <= 시분초 < 92000    # 추세 확정기
}
```

**분석 범위(예시)**: 09:00~09:20 구간(조건식 기준)만 포함하며 이후 구간은 제외. 필요 시 구간을 재정의한다.

**분할 근거**:
- T1 (09:00-09:05): 동시호가 해제 직후, 극심한 변동성
- T2 (09:05-09:10): 초기 추세 형성, 갭 조정
- T3 (09:10-09:15): 추세 안정화, 돌파 패턴
- T4 (09:15-09:20): 추세 확정, 모멘텀 강화

#### C. 교차 세그먼트 매트릭스

총 12개 세그먼트 생성:

| | T1 (09:00-05) | T2 (09:05-10) | T3 (09:10-15) | T4 (09:15-20) |
|---|---|---|---|---|
| **소형주** | S1-T1 | S1-T2 | S1-T3 | S1-T4 |
| **중형주** | S2-T1 | S2-T2 | S2-T3 | S2-T4 |
| **대형주** | S3-T1 | S3-T2 | S3-T3 | S3-T4 |

### 2.2 세그먼트별 제약 조건

#### 최소 거래수 제약

```python
MIN_TRADES_PER_SEGMENT = {
    'absolute_min': 30,         # 대표본 구간 최소치
    'small_segment_min': 10,    # 소표본 구간 완화 최소치
    'relative_min': 0.15,       # 세그먼트 내 거래의 15% 이상 유지
    'dynamic_formula': lambda n: max(10, min(30, int(n * 0.15)))
}
```

- 소표본 세그먼트는 최소 거래수를 완화하고, 필터 미적용 조합을 허용해 과도한 제약을 방지한다.

#### 최대 제외율 제약

```python
MAX_EXCLUSION_RATIO = {
    'per_segment': 0.85,        # 세그먼트별 최대 85% 제외
    'global': 0.80,             # 전체 최대 80% 제외
    'adaptive': True            # 세그먼트 크기에 따라 조정
}
```

### 2.3 확장 분할 차원 (선택적)

#### D. 변동성 분할

```python
변동성_구간 = {
    '저변동': 등락율 < 5,
    '중변동': 5 <= 등락율 < 15,
    '고변동': 등락율 >= 15
}
```

#### E. 거래강도 분할

```python
거래강도_구간 = {
    '저강도': 체결강도 < 80,
    '중강도': 80 <= 체결강도 < 150,
    '고강도': 체결강도 >= 150
}
```

### 2.4 세그먼트 고정/동적 전략 및 전환 계획

**현 상태 판단**
- 현재 세그먼트(시가총액/시간)는 조건식 문서와 일치하며, 연구 효율과 비교 가능성을 위해 사실상 고정 기준으로 사용 중이다.

**고정형의 장점/리스크**
- 장점: 재현성 확보, 디버깅/해석 용이, 백테스트 비교 가능, 운영 단순.
- 리스크: 시장 레짐 변화 반영 지연, 분포 이동 시 최적 구간의 효력 저하.

**동적형의 장점/리스크**
- 장점: 데이터 분포 변화에 적응, 구간별 편향 완화.
- 리스크: 과적합 위험 증가, 설명 가능성 저하, 운영 복잡도 상승.

**권장 업데이트 전략(단계적)**
1. **고정 유지 단계**: 현재 기준으로 필터 성과/안정성 지표를 확보하고 베이스라인을 만든다.
2. **반-동적 단계**: 상위 분할(시가총액/시간)은 유지하고, 하위 구간만 분포 기반으로 재조정한다.
3. **동적 확장 단계**: 레짐 변화 감지 시에만 재분할하며, 모든 분할 정의를 메타데이터로 저장해 재현성을 확보한다.

### 2.5 반-동적 분할 구현(코드 반영)

고정 기준을 유지하면서 분포 기반으로 구간을 보정할 수 있도록 `SegmentConfig`에 반-동적 옵션을 추가했다.

```python
SegmentConfig(
    dynamic_mode='semi',  # fixed | semi | dynamic | time_only
    dynamic_market_cap_quantiles=(0.33, 0.66),
    dynamic_time_quantiles=(0.25, 0.5, 0.75),
    dynamic_min_samples=200
)
```

- `semi`: 시가총액 구간만 분포 기반으로 재산정, 시간 구간은 고정 유지
- `dynamic`: 시가총액/시간 모두 재산정
- `time_only`: 시간 구간만 재산정
- 분할 결과는 `*_segment_ranges.csv`로 저장되어 재현성과 비교 가능성을 확보한다.

---

## 3. 최적화 알고리즘 상세 설계

### 3.1 알고리즘 비교 분석

| 알고리즘 | 장점 | 단점 | 복잡도 | 권장 상황 |
|----------|------|------|--------|----------|
| **Greedy + Beam Search** | 빠름, 이해 용이 | 지역 최적 위험 | O(K×N×M) | 초기 탐색 |
| **Mixed Integer Programming** | 전역 최적 보장 | 느림, 비선형 어려움 | NP-hard | 정밀 최적화 |
| **Optuna (TPE)** | 연속 파라미터, 자동화 | 이산 조합 비효율 | O(T×N) | 임계값 탐색 |
| **NSGA-II** | 다목적 최적화 | 해석 복잡 | O(G×P×logP) | 다목적 균형 |
| **Dynamic Programming** | 세그먼트 독립 시 효율 | 상호작용 어려움 | O(S×K^2) | 독립 세그먼트 |

### 3.2 권장 알고리즘: 2단계 계층적 최적화

#### Stage 1: 세그먼트별 후보 필터 선정 (Greedy + 통계 검증)

```python
def SelectCandidateFilters(segment_data, all_filters, config):
    """
    각 세그먼트에서 유효한 필터 후보를 선정

    Args:
        segment_data: 세그먼트 거래 데이터
        all_filters: 전체 필터 목록
        config: 선정 기준 설정

    Returns:
        candidate_filters: 세그먼트별 후보 필터 리스트
    """
    candidates = []

    for filter in all_filters:
        # 1. 필터 적용 시 수익 개선 계산
        improvement = CalculateImprovement(segment_data, filter)

        # 2. 통계적 유의성 검증
        p_value = TTest(segment_data, filter)
        effect_size = CohenD(segment_data, filter)

        # 3. 제외율 및 잔여 거래수 검증
        exclusion_ratio = GetExclusionRatio(segment_data, filter)
        remaining_trades = GetRemainingTrades(segment_data, filter)

        # 4. 후보 선정 기준
        if (improvement > 0 and
            p_value < config.p_threshold and
            effect_size > config.effect_threshold and
            exclusion_ratio < config.max_exclusion and
            remaining_trades >= config.min_trades):

            candidates.append({
                'filter': filter,
                'improvement': improvement,
                'p_value': p_value,
                'effect_size': effect_size,
                'exclusion_ratio': exclusion_ratio,
                'remaining_trades': remaining_trades,
                'efficiency': improvement / max(1, exclusion_ratio * 100)
            })

    # 5. 효율성 기준 정렬 및 상위 K개 선택
    candidates.sort(key=lambda x: x['efficiency'], reverse=True)
    return candidates[:config.top_k]
```

#### Stage 2: 전역 조합 최적화 (Beam Search + DP)

```python
def OptimizeGlobalCombination(segment_candidates, config):
    """
    세그먼트별 후보 조합을 전역 최적화

    알고리즘:
    1. 각 세그먼트에서 상위 K개 필터 조합 생성
    2. Beam Search로 전역 조합 탐색
    3. 전역 합산 성과 최대화

    Args:
        segment_candidates: 세그먼트별 후보 필터
        config: 최적화 설정

    Returns:
        best_combination: 최적 전역 조합
    """
    # 1. 세그먼트별 로컬 조합 생성
    segment_combos = {}
    for seg_id, candidates in segment_candidates.items():
        local_combos = GenerateLocalCombinations(
            candidates,
            max_filters=config.max_filters_per_segment,
            top_k=config.beam_width
        )
        # baseline(no_filter) 추가: 세그먼트가 강제 필터링되지 않도록 보장
        local_combos.append({
            'filters': [],
            'improvement': 0,
            'excluded_trades': 0,
            'label': 'no_filter'
        })
        segment_combos[seg_id] = local_combos

    # 2. Beam Search 기반 전역 탐색
    beam = [{'combination': {}, 'score': 0, 'total_trades': total_trades}]

    for seg_id in sorted(segment_combos.keys()):
        new_beam = []

        for state in beam:
            for combo in segment_combos[seg_id]:
                new_state = {
                    'combination': {**state['combination'], seg_id: combo},
                    'score': state['score'] + combo['improvement'],
                    'total_trades': state['total_trades'] - combo['excluded_trades']
                }

                # 제약 조건 검증
                if ValidateConstraints(new_state, config):
                    new_beam.append(new_state)

        # Beam 크기 제한
        new_beam.sort(key=lambda x: x['score'], reverse=True)
        beam = new_beam[:config.beam_width]

    # 3. 최적 조합 반환
    return beam[0] if beam else None
```

### 3.3 다목적 최적화 확장 (NSGA-II 기반)

#### 목적 함수 정의

```python
OBJECTIVES = {
    'profit_improvement': {
        'direction': 'maximize',
        'weight': 0.5,
        'formula': lambda x: sum(x.segment_improvements)
    },
    'risk_reduction': {
        'direction': 'minimize',
        'weight': 0.2,
        'formula': lambda x: calculate_mdd(x.remaining_trades)
    },
    'trade_preservation': {
        'direction': 'maximize',
        'weight': 0.2,
        'formula': lambda x: x.remaining_trade_ratio
    },
    'stability': {
        'direction': 'maximize',
        'weight': 0.1,
        'formula': lambda x: calculate_period_stability(x)
    }
}
```

#### NSGA-II 통합

```python
def MultiObjectiveOptimization(segment_data, config):
    """
    NSGA-II 기반 다목적 최적화

    Returns:
        pareto_front: Pareto 최적 해 집합
    """
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.operators.sampling.rnd import BinaryRandomSampling
    from pymoo.operators.crossover.pntx import TwoPointCrossover
    from pymoo.operators.mutation.bitflip import BitflipMutation
    from pymoo.optimize import minimize
    from pymoo.core.problem import Problem

    class FilterOptProblem(Problem):
        def __init__(self, segment_data, n_segments, n_filters):
            super().__init__(
                n_var=n_segments * n_filters,  # 세그먼트별 필터 선택
                n_obj=len(OBJECTIVES),
                n_constr=2,  # 최소 거래수, 최대 제외율
                xl=0,  # 바이너리: 필터 미선택
                xu=1   # 바이너리: 필터 선택
            )
            self.segment_data = segment_data

        def _evaluate(self, x, out, *args, **kwargs):
            # 목적 함수 계산
            f = np.zeros((x.shape[0], len(OBJECTIVES)))
            g = np.zeros((x.shape[0], 2))

            for i, solution in enumerate(x):
                result = ApplyFilterCombination(self.segment_data, solution)

                for j, (name, obj) in enumerate(OBJECTIVES.items()):
                    val = obj['formula'](result)
                    f[i, j] = -val if obj['direction'] == 'maximize' else val

                # 제약 조건
                g[i, 0] = config.min_trades - result.remaining_trades
                g[i, 1] = result.exclusion_ratio - config.max_exclusion

            out["F"] = f
            out["G"] = g

    problem = FilterOptProblem(segment_data, n_segments=12, n_filters=20)
    # 바이너리 선택 변수에 맞는 연산자 지정
    algorithm = NSGA2(
        pop_size=100,
        sampling=BinaryRandomSampling(),
        crossover=TwoPointCrossover(),
        mutation=BitflipMutation(),
        eliminate_duplicates=True
    )

    result = minimize(
        problem,
        algorithm,
        ('n_gen', config.generations),
        seed=42,
        verbose=True
    )

    return result.F, result.X  # Pareto 전선과 해
```

### 3.4 Optuna 기반 임계값 최적화

#### 연속 임계값 탐색

```python
def OptunaThresholdOptimization(segment_data, filter_columns, config):
    """
    Optuna를 사용한 세그먼트별 필터 임계값 최적화
    """
    import optuna

    def objective(trial):
        total_improvement = 0
        total_remaining = 0

        for seg_id in SEGMENT_IDS:
            seg_data = segment_data[segment_data['segment'] == seg_id]
            seg_improvement = 0
            seg_mask = pd.Series([True] * len(seg_data))

            for col in filter_columns:
                # 세그먼트별 임계값 제안
                threshold = trial.suggest_float(
                    f'{seg_id}_{col}_threshold',
                    seg_data[col].quantile(0.05),
                    seg_data[col].quantile(0.95)
                )
                direction = trial.suggest_categorical(
                    f'{seg_id}_{col}_direction',
                    ['less', 'greater']
                )
                use_filter = trial.suggest_categorical(
                    f'{seg_id}_{col}_use',
                    [True, False]
                )

                if use_filter:
                    if direction == 'less':
                        filter_mask = seg_data[col] >= threshold
                    else:
                        filter_mask = seg_data[col] < threshold
                    seg_mask &= filter_mask

            # 세그먼트 성과 계산
            filtered_data = seg_data[seg_mask]
            remaining_trades = len(filtered_data)

            if remaining_trades < config.min_trades_per_segment:
                return float('-inf')  # 제약 위반 페널티

            improvement = filtered_data['수익금'].sum() - seg_data['수익금'].sum()
            total_improvement += improvement
            total_remaining += remaining_trades

        # 잔여 거래수 비율 페널티
        remaining_ratio = total_remaining / len(segment_data)
        if remaining_ratio < 0.15:
            return float('-inf')

        return total_improvement

    study = optuna.create_study(
        direction='maximize',
        sampler=optuna.samplers.TPESampler(seed=42),
        pruner=optuna.pruners.MedianPruner()
    )

    study.optimize(objective, n_trials=config.n_trials, n_jobs=-1)

    return study.best_params, study.best_value
```

---

## 4. 구현 아키텍처 설계

### 4.1 모듈 구조

```
backtester/
├── back_analysis_enhanced.py        # 기존 분석 모듈
├── segment_filter_optimizer.py      # Phase 1 실행 진입점
├── segment_analysis/
│   ├── __init__.py
│   ├── segmentation.py              # 세그먼트 분할 로직
│   ├── filter_evaluator.py          # 세그먼트별 필터 평가
│   ├── segment_outputs.py           # 요약/필터 CSV 산출물
│   ├── phase1_runner.py             # Phase 1 실행 흐름
│   ├── phase2_runner.py             # Phase 2 실행 흐름
│   ├── phase3_runner.py             # Phase 3 실행 흐름
│   ├── combination_optimizer.py     # 조합 최적화 알고리즘
│   ├── threshold_optimizer.py       # Optuna 임계값 최적화
│   ├── validation.py                # 제약 조건 검증
│   ├── segment_visualizer.py        # 히트맵/효율 차트 시각화
│   ├── risk_metrics.py              # 리스크 지표(MDD/변동성) 계산
│   ├── multi_objective.py           # Pareto 기반 다목적 평가
│   ├── multi_objective_runner.py    # Pareto front 산출 실행 흐름
└── segment_outputs/                  # 세그먼트 분석 산출물
```

### 4.2 핵심 클래스 설계

```python
class SegmentFilterOptimizer:
    """
    세그먼트 기반 필터 최적화 메인 클래스
    """

    def __init__(self, config: SegmentConfig):
        self.config = config
        self.segmenter = SegmentBuilder(config.segment_config)
        self.evaluator = FilterEvaluator(config.filter_config)
        self.optimizer = CombinationOptimizer(config.optim_config)
        self.validator = StabilityValidator(config.valid_config)

    def run(self, df_detail: pd.DataFrame) -> SegmentOptResult:
        """
        전체 최적화 파이프라인 실행
        """
        # 1. 세그먼트 분할
        segmented_data = self.segmenter.build_segments(df_detail)

        # 2. 세그먼트별 필터 후보 평가
        segment_candidates = {}
        for seg_id, seg_data in segmented_data.items():
            candidates = self.evaluator.evaluate_filters(seg_data)
            segment_candidates[seg_id] = candidates

        # 3. 전역 조합 최적화
        optimal_combo = self.optimizer.optimize(segment_candidates)

        # 4. 안정성 검증
        validation_result = self.validator.validate(
            df_detail, optimal_combo, segmented_data
        )

        # 5. 결과 생성
        return SegmentOptResult(
            segments=segmented_data,
            candidates=segment_candidates,
            optimal_combination=optimal_combo,
            validation=validation_result,
            code=self._generate_code(optimal_combo)
        )

    def _generate_code(self, combo: dict) -> str:
        """
        최적 조합에 대한 조건식 코드 자동 생성
        """
        code_lines = ["# 세그먼트별 필터 적용"]
        code_lines.append("필터통과 = False")
        code_lines.append("")

        for seg_id, filters in combo.items():
            seg_cond = self._get_segment_condition(seg_id)
            code_lines.append(f"# === {seg_id} ===")
            code_lines.append(f"if {seg_cond}:")

            filter_conds = []
            for f in filters:
                filter_conds.append(f"    ({f['condition']})")

            if filter_conds:
                code_lines.append("    if (" + " and\n        ".join(filter_conds) + "):")
                code_lines.append("        필터통과 = True")
            else:
                code_lines.append("    필터통과 = True  # 필터 없음")
            code_lines.append("")

        return "\n".join(code_lines)
```

### 4.3 산출물 정의

```python
OUTPUT_FILES = {
    # 세그먼트 분석
    '*_segment_summary.csv': {
        'columns': ['segment_id', 'trades', 'profit', 'winrate',
                    'avg_return', 'std_return', 'sharpe'],
        'description': '세그먼트별 기본 통계'
    },

    # 세그먼트 분할 범위
    '*_segment_ranges.csv': {
        'columns': ['range_type', 'label', 'min', 'max', 'source'],
        'description': '세그먼트 분할 구간(고정/반-동적) 기록'
    },

    # 필터 후보
    '*_segment_filters.csv': {
        'columns': ['segment_id', 'filter_name', 'column', 'threshold', 'direction',
                    'improvement', 'exclusion_ratio', 'p_value', 'effect_size',
                    'efficiency', 'stability_score'],
        'description': '세그먼트별 필터 후보 및 성과'
    },

    # 조합 결과
    '*_segment_combos.csv': {
        'columns': ['combo_id', 'segments', 'filters', 'total_improvement',
                    'remaining_trades', 'remaining_ratio', 'validation_score',
                    'mdd_won', 'mdd_pct', 'profit_volatility', 'return_volatility'],
        'description': '전역 최적 조합(요약)'
    },

    # 세그먼트별 로컬 조합
    '*_segment_local_combos.csv': {
        'columns': ['segment_id', 'combo_rank', 'filters', 'improvement',
                    'remaining_trades', 'exclusion_ratio'],
        'description': '세그먼트별 조합 후보(로컬)'
    },

    # Optuna 임계값 최적화 (옵션)
    '*_segment_thresholds.csv': {
        'columns': ['segment_id', 'best_value', 'best_params', 'n_trials'],
        'description': '세그먼트별 Optuna 임계값 결과(선택 실행)'
    },

    # 세그먼트 조건식 코드
    '*_segment_code.txt': {
        'description': '세그먼트별 최적 조합 조건식 코드(자동 생성)'
    },

    # 최적 조합
    '*_optimal_combination.json': {
        'content': {
            'segments': {},
            'filters_per_segment': {},
            'total_improvement': 0,
            'validation': {},
            'generated_code': ''
        },
        'description': '최종 최적 조합 및 생성 코드'
    },

    # 검증 보고서
    '*_segment_validation.csv': {
        'columns': ['period', 'segment_id', 'in_sample_perf', 'out_sample_perf',
                    'stability_ratio', 'overfitting_risk'],
        'description': '기간별 안정성 검증 결과'
    },

    # 시각화
    '*_pareto_front.csv': 'Pareto front 후보 집합(다목적 평가 결과)',
    '*_segment_heatmap.png': '세그먼트별 성과 히트맵',
    '*_filter_efficiency.png': '필터 효율성 차트',
    '*_pareto_front.png': 'Pareto 최적 전선 시각화'
}
```

---

## 5. 검증 및 평가 프레임워크

### 5.1 기간 분할 검증 (Walk-Forward)

```python
class WalkForwardValidator:
    """
    Walk-Forward 방식의 시계열 검증
    """

    def __init__(self, config: ValidationConfig):
        self.train_ratio = config.train_ratio  # 예: 0.7
        self.n_splits = config.n_splits        # 예: 5
        self.min_train_days = config.min_train_days  # 예: 180

    def validate(self, df: pd.DataFrame, combination: dict) -> dict:
        """
        Walk-Forward 검증 실행
        """
        results = []
        dates = df['매수일자'].unique()
        dates = np.sort(dates)

        split_size = len(dates) // self.n_splits

        for i in range(self.n_splits - 1):
            train_end = dates[(i + 1) * split_size]
            test_start = train_end
            test_end = dates[min((i + 2) * split_size, len(dates) - 1)]

            train_data = df[df['매수일자'] < train_end]
            test_data = df[(df['매수일자'] >= test_start) &
                          (df['매수일자'] < test_end)]

            # 훈련 데이터로 필터 재적합 (선택적)
            train_perf = self._evaluate_combination(train_data, combination)
            test_perf = self._evaluate_combination(test_data, combination)

            results.append({
                'split': i,
                'train_period': f'{dates[i * split_size]} ~ {train_end}',
                'test_period': f'{test_start} ~ {test_end}',
                'train_improvement': train_perf['improvement'],
                'test_improvement': test_perf['improvement'],
                'train_winrate': train_perf['winrate'],
                'test_winrate': test_perf['winrate'],
                'degradation': 1 - (test_perf['improvement'] /
                                   max(1, train_perf['improvement']))
            })

        # 종합 평가
        avg_degradation = np.mean([r['degradation'] for r in results])
        consistency = np.std([r['test_improvement'] for r in results])

        return {
            'splits': results,
            'avg_degradation': avg_degradation,
            'consistency_score': 1 / (1 + consistency / 1e9),
            'overfitting_risk': 'High' if avg_degradation > 0.3 else
                               'Medium' if avg_degradation > 0.15 else 'Low'
        }
```

### 5.2 안정성 지표

```python
STABILITY_METRICS = {
    'period_consistency': {
        'description': '기간별 성과 일관성',
        'formula': lambda x: 1 - (std(x.period_returns) / mean(x.period_returns)),
        'threshold': 0.7
    },
    'segment_balance': {
        'description': '세그먼트별 성과 균형',
        'formula': lambda x: 1 - gini_coefficient(x.segment_improvements),
        'threshold': 0.6
    },
    'filter_robustness': {
        'description': '필터 임계값 민감도',
        'formula': lambda x: mean(x.sensitivity_scores),
        'threshold': 0.8
    },
    'statistical_significance': {
        'description': '통계적 유의성',
        'formula': lambda x: sum(p < 0.05 for p in x.p_values) / len(x.p_values),
        'threshold': 0.8
    }
}
```

### 5.3 과적합 방지 전략

```python
OVERFITTING_PREVENTION = {
    # 1. 복잡도 페널티
    'complexity_penalty': {
        'per_filter': -5000000,      # 필터당 500만원 페널티
        'per_segment_filter': -2000000  # 세그먼트별 필터당 추가 페널티
    },

    # 2. 최소 표본 크기
    'min_samples': {
        'per_segment': 50,           # 세그먼트별 최소 50건
        'per_filter': 30,            # 필터 평가 최소 30건
        'for_significance': 100      # 유의성 검정 최소 100건
    },

    # 3. 교차 검증 요구
    'cross_validation': {
        'method': 'walk_forward',
        'min_splits': 3,
        'max_degradation': 0.25      # 25% 이상 성능 저하 시 거부
    },

    # 4. 효과 크기 최소 요구
    'effect_size': {
        'min_cohens_d': 0.2,         # Small effect 이상
        'min_r_squared': 0.01        # 1% 이상 설명력
    }
}
```

---

## 6. 예상 성과 및 기대 효과

### 6.1 성과 시뮬레이션

현재 데이터 기반 예상 (보수적 추정):

| 시나리오 | 예상 개선 | 잔여 거래 | 위험 수준 |
|----------|----------|----------|----------|
| 보수적 (5개 세그먼트, 세그먼트당 1필터) | +8~12억 | 6,000건 | 낮음 |
| 균형적 (12개 세그먼트, 세그먼트당 2필터) | +12~18억 | 4,000건 | 중간 |
| 적극적 (12개 세그먼트, 세그먼트당 3필터) | +15~22억 | 2,500건 | 높음 |

### 6.2 기대 효과

1. **시너지 문제 해결**: 구간별 독립 필터로 음수 시너지 방지
2. **거래수 보존**: 구간별 제약으로 과도한 제외 방지
3. **맞춤형 최적화**: 시장 특성에 맞는 필터 적용
4. **해석 가능성**: 각 구간별 필터 로직 명확

---

## 7. 구현 로드맵

### Phase 1: 기반 구축 (1주)

- [x] 세그먼트 분할 모듈 구현 (`segmentation.py`)
- [x] 세그먼트별 필터 평가 모듈 (`filter_evaluator.py`)
- [x] 기본 산출물 생성 (CSV, 요약)
  - `segment_outputs.py`, `phase1_runner.py`로 요약/필터 CSV 생성

**Phase 1-1 진행 결과**
- 매수시간 파싱 보강 및 `Out_of_Range` 비중 추적 포함
- 최신 detail.csv 자동 선택/실행 스크립트 보강

### Phase 2: 최적화 알고리즘 (1주)

- [x] Beam Search 기반 조합 최적화 구현 (`combination_optimizer.py`)
- [x] Optuna 임계값 탐색 통합 (`threshold_optimizer.py`, 선택 실행)
- [x] 제약 조건 검증 로직 (`validation.py`)

**Phase 2-1 진행 결과**
- 세그먼트별 조합 생성 + 전역 조합 탐색 기본 골격 구현

**Phase 2-2 진행 결과**
- Optuna 임계값 최적화 모듈 및 Phase 2 실행 흐름 추가 (`phase2_runner.py`)
- 실행 옵션: `python -m backtester.segment_analysis.phase2_runner <detail.csv> --optuna`

### Phase 3: 검증 및 시각화 (1주)

- [x] Walk-Forward 검증 구현 (`validation.py`)
- [x] 안정성 지표 계산 (`segment_validation.csv`)
- [x] 히트맵/차트 시각화 (`segment_visualizer.py`, `phase3_runner.py`)

**Phase 3-1 진행 결과**
- 워크포워드 기반 안정성 검증 CSV 산출
- 세그먼트 히트맵/필터 효율 차트 생성 흐름 추가
- 실행 옵션: `python -m backtester.segment_analysis.phase3_runner <detail.csv>`

### Phase 4: 통합 및 자동화 (1주)

- [x] 기존 `back_analysis_enhanced.py` 통합
- [x] 세그먼트 조건식 코드 자동 생성 (`*_segment_code.txt`)
- [x] 텔레그램 리포트 연동(요약 + 히트맵/효율 차트)

**Phase 4-1 진행 결과**
- `RunEnhancedAnalysis()`에서 Phase2/Phase3 실행 옵션 지원(기본: `phase2+3`)
- 세그먼트 산출물은 `backtester/segment_outputs/`에 저장
- 텔레그램에 세그먼트 요약/전역 조합 개선 요약 및 차트 자동 전송

### Phase 5: 적용 및 검증(1주)

- [x] 전역 조합 기반 세그먼트 필터 마스크 적용
- [x] 세그먼트 필터 미리보기 차트 생성 (`*_segment_filtered.png`, `*_segment_filtered_.png`)
- [x] 전역 조합 결과 리스크 지표(MDD/변동성) 산출 확장
- [ ] 실전 조건식 반영 후 성능 비교/리스크 지표 고도화

### Phase 6: 다목적 최적화 실험(선택)

- [x] Pareto front 평가 모듈 및 실행 흐름 추가
- [x] Pareto front CSV/시각화 산출 (`*_pareto_front.csv`, `*_pareto_front.png`)
- [ ] NSGA-II/Optuna 등 고급 탐색 실험(필요 시)

**Phase 6-1 실행 옵션**
- `python -m backtester.segment_analysis.multi_objective_runner <detail.csv>`

### Phase 7: 반-동적 분할 적용(1주)

- [x] 시가총액/시간 분포 기반 구간 재산정 옵션 추가
- [x] 세그먼트 분할 범위 CSV 저장(`*_segment_ranges.csv`)
- [ ] 고정/반-동적/동적 성능 비교 리포트 정리

---

## 8. 결론 및 다음 단계

### 핵심 결론

1. **현재 문제**: 전 구간 단일 필터 방식은 시너지 효과가 음수이며, 대부분의 거래를 제외
2. **해결 방안**: 시가총액/시간 구간별 독립 필터 최적화 후 합산
3. **권장 알고리즘**: 2단계 계층적 최적화 (Greedy + Beam Search)
4. **핵심 제약**: 세그먼트별 최소 거래수 30건, 최대 제외율 85%

### 다음 단계

이 연구 보고서를 바탕으로 다음 코드 업데이트를 요청할 예정:

1. 고정/반-동적/동적 분할 성능 비교 리포트 정리
2. NSGA-II/Optuna 기반 고급 탐색(필요 시)

---

## 참고 자료

- 조건식 문서: `docs/Condition/Tick/2_Under_review/Condition_Tick_900_920_Enhanced_FilterStudy.md`
- 백테스팅 가이드: `docs/Guideline/Back_Testing_Guideline_Tick.md`
- 기존 분석 모듈: `backtester/back_analysis_enhanced.py`
- 최적화 시스템 분석: `docs/Study/SystemAnalysis/STOM_Optimization_System_Improvements.md`

---

**문서 버전**: 2.5
**최종 수정일**: 2025-12-20
**작성자**: Claude Code
