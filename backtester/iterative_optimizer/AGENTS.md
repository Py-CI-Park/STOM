<!-- Parent: ../AGENTS.md -->
# backtester/iterative_optimizer

## Purpose
Parameter tuning and iterative optimization system (ICOS - Iterative Condition Optimization System). Solves prediction-reality gap by using actual backtests instead of ML predictions for progressive strategy refinement.

## Complete Pipeline Architecture

### ICOS vs Existing Analysis Pipeline Comparison

ICOS와 기존 백테스팅 분석 파이프라인은 **서로 다른 목적**을 가지며, **독립적으로 동작**하지만 선택적으로 연동될 수 있습니다.

| 구분 | ICOS (Iterative Optimizer) | 기존 분석 (RunEnhancedAnalysis) |
|------|---------------------------|-------------------------------|
| **목적** | 조건식 자동 개선/반복 최적화 | 백테스트 결과 분석/시각화 |
| **트리거** | Alt-I "ICOS 활성화" + 백테스트 버튼 | Alt-I "분석 활성화" + 백테스트 완료 |
| **분석기** | `analyzer.py` (ResultAnalyzer) | `analysis_enhanced/filters.py` |
| **출력** | 개선된 buystg 코드 | 필터 추천 리포트/차트 |
| **반복** | 최대 20회 자동 반복 | 1회성 분석 |
| **독립성** | Alt-I 분석 설정과 무관 | ICOS 설정과 무관 |

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ICOS Pipeline (Iterative Optimization)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [백테스트 버튼 클릭]                                                         │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────────┐                                                        │
│  │ backtest_icos.py │  ICOSBackTest 클래스                                   │
│  │ (진입점)          │  - IterativeOptimizer 생성                             │
│  └────────┬─────────┘  - UI 진행상황 업데이트 (windowQ)                       │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                        │
│  │    runner.py     │  IterativeOptimizer.run()                              │
│  │  (메인 오케스트레이터) │  - 4단계 반복 사이클 관리                              │
│  └────────┬─────────┘  - 수렴 체크 및 종료 조건 판단                           │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐             │
│  │                  4-Step Iteration Cycle                     │             │
│  │                                                             │             │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │             │
│  │  │ Step 1      │    │ Step 2      │    │ Step 3      │      │             │
│  │  │ Backtest    │───▶│ Analyze     │───▶│ Generate    │      │             │
│  │  │             │    │             │    │ Filters     │      │             │
│  │  │backtest_sync│    │ analyzer.py │    │filter_gen.py│      │             │
│  │  │    .py      │    │             │    │             │      │             │
│  │  └─────────────┘    └─────────────┘    └─────────────┘      │             │
│  │         │                                    │               │             │
│  │         │                                    ▼               │             │
│  │         │           ┌─────────────────────────────┐         │             │
│  │         │           │ Step 4: Build Condition      │         │             │
│  │         │           │ condition_builder.py         │         │             │
│  │         │           │ - 필터 → buystg 코드 삽입     │         │             │
│  │         │           └─────────────────────────────┘         │             │
│  │         │                        │                          │             │
│  │         └────────────────────────┼──────────────────────────┘             │
│  │                                  │                                        │
│  │         ┌────────────────────────┼────────────────────────────┐           │
│  │         │                        ▼                            │           │
│  │         │           ┌─────────────────────────────┐           │           │
│  │         │           │ Convergence Check            │           │           │
│  │         │           │ convergence.py               │           │           │
│  │         │           │ - plateau: 개선 정체 감지     │           │           │
│  │         │           │ - threshold: 목표 도달 확인   │           │           │
│  │         │           └─────────────────────────────┘           │           │
│  │         │                        │                            │           │
│  │         │         ┌──────────────┴──────────────┐             │           │
│  │         │         │                             │             │           │
│  │         │    [수렴 안됨]                    [수렴됨]           │           │
│  │         │         │                             │             │           │
│  │         │         ▼                             ▼             │           │
│  │         │   다음 반복 시작               최종 결과 반환        │           │
│  │         │   (new_buystg 사용)           (IterativeResult)     │           │
│  │         │                                                     │           │
│  │         └─────────────────────────────────────────────────────┘           │
│  │                                                                           │
│  └───────────────────────────────────────────────────────────────────────────┘
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                기존 분석 파이프라인 (RunEnhancedAnalysis)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [백테스트 완료]                                                              │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────────────┐                                                    │
│  │ back_static.py       │  PltShow() 호출                                    │
│  │ (결과 시각화)         │  - Alt-I "분석 활성화" 확인                         │
│  └────────┬─────────────┘                                                    │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────────┐                                                    │
│  │ back_analysis_       │  RunEnhancedAnalysis()                             │
│  │ enhanced.py          │  - 필터 효과 분석                                   │
│  └────────┬─────────────┘  - 임계값 탐색                                      │
│           │                - 조합 분석                                        │
│           ▼                - 안정성 검증                                      │
│  ┌──────────────────────┐                                                    │
│  │ analysis_enhanced/   │  AnalyzeFilterEffectsEnhanced()                    │
│  │ filters.py           │  - 통계적 유의성 검정                                │
│  └────────┬─────────────┘  - 최적 임계값 계산                                  │
│           │                - 필터 코드 생성                                    │
│           ▼                                                                  │
│  ┌──────────────────────┐                                                    │
│  │ 분석 결과 출력        │  - PNG 차트 저장                                    │
│  │ (1회성)              │  - 필터 추천 리포트                                  │
│  └──────────────────────┘  - 조건식 코드 제안                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      선택적 연동 (Optional Integration)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ICOS의 ResultAnalyzer는 기존 analysis_enhanced 모듈을 선택적으로 활용 가능:   │
│                                                                              │
│  ┌───────────────────┐         ┌───────────────────────────────────┐         │
│  │ analyzer.py       │ ──────▶ │ _run_enhanced_analysis()          │         │
│  │ ResultAnalyzer    │ 선택적   │ analysis_enhanced/filters.py 호출 │         │
│  └───────────────────┘ 호출    └───────────────────────────────────┘         │
│                                                                              │
│  활용 시점: ICOS가 더 정교한 필터 분석이 필요할 때                              │
│  독립성: 기본적으로 ICOS는 자체 분석 로직 사용                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Detail

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Step-by-Step Component Interactions                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ 1. SyncBacktestRunner._execute() (backtest_sync.py:971 lines)               │
│    ├─ _load_strategy_from_db(): DB에서 전략 코드 로드                         │
│    ├─ _strip_condition_name(): 조건명 prefix 제거                            │
│    ├─ _strategy(): 전체 지표 함수 내장 (현재가N, 등락율N, 체결강도N...)         │
│    └─ 반환: df_tsg (거래내역), metrics (성과지표)                              │
│                                                                              │
│ 2. ResultAnalyzer.analyze() (analyzer.py:750 lines)                         │
│    ├─ ANALYSIS_COLUMNS: columns_bt 기반 분석 대상 컬럼                        │
│    ├─ _analyze_loss_patterns(): 손실 패턴 탐지                               │
│    │   ├─ TIME_BASED: 시간대별 손실 패턴                                     │
│    │   ├─ THRESHOLD_BELOW: 특정 값 미만 시 손실                              │
│    │   ├─ THRESHOLD_ABOVE: 특정 값 이상 시 손실                              │
│    │   └─ RANGE_INSIDE: 특정 범위 내 손실                                    │
│    ├─ _run_enhanced_analysis(): (선택적) analysis_enhanced 연동              │
│    └─ 반환: AnalysisResult (loss_patterns, feature_importances)             │
│                                                                              │
│ 3. FilterGenerator.generate() (filter_generator.py:506 lines)               │
│    ├─ 점수 계산: total_score = (improvement×0.4 + confidence×0.3            │
│    │                           + stability×0.2 + coverage×0.1)              │
│    ├─ 우선순위: CRITICAL > HIGH > MEDIUM > LOW > EXPERIMENTAL                │
│    ├─ 패턴→필터 변환: _create_time_filter, _create_threshold_filter...        │
│    └─ 반환: List[FilterCandidate]                                            │
│                                                                              │
│ 4. ConditionBuilder.build() (condition_builder.py:522 lines)                │
│    ├─ 마커: # === ICOS 필터 시작/끝 ===                                       │
│    ├─ Preamble 생성: 파생 변수 계산 코드                                      │
│    │   예: 거래품질점수 = (체결강도×0.3 + 호가잔량비×0.2 + ...)               │
│    ├─ Filter Block 생성: 각 필터를 if 조건으로 변환                           │
│    ├─ 주입 위치: "if 매수:" 라인 직전                                         │
│    └─ 반환: new_buystg (필터가 삽입된 새 조건식)                               │
│                                                                              │
│ 5. ConvergenceChecker.check() (convergence.py)                              │
│    ├─ plateau: 최근 N회 개선율이 임계값 미만                                  │
│    ├─ threshold: 목표 수익률/승률 도달                                        │
│    ├─ combined: plateau AND threshold                                        │
│    └─ 반환: (수렴여부: bool, 사유: str)                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Key Files

### Core System (Phase 1-7)
- `__init__.py` - Package API and version (v0.7.0)
- `config.py` - Configuration classes and presets (conservative, aggressive, quick)
- `data_types.py` - Common data structures (FilterCandidate, IterationResult)
- `runner.py` - Main orchestrator (IterativeOptimizer, IterativeResult) - **866 lines**

### Analysis & Generation (Phase 2)
- `analyzer.py` - ResultAnalyzer for loss pattern detection - **750 lines**
  - ICOS 전용 분석기 (Alt-I 설정과 무관)
  - ANALYSIS_COLUMNS는 columns_bt와 일치해야 함
  - 선택적으로 analysis_enhanced 모듈 연동 가능
- `filter_generator.py` - FilterGenerator with priority scoring - **506 lines**
  - 손실 패턴 → FilterCandidate 변환
  - 4가지 점수 기반 우선순위 산정

### Condition Building (Phase 3)
- `condition_builder.py` - ConditionBuilder for strategy code generation - **522 lines**
  - 필터 마커로 중복 삽입 방지
  - "if 매수:" 직전에 필터 블록 주입
- `storage.py` - IterationStorage for persistence

### Comparison & Convergence (Phase 4)
- `comparator.py` - ResultComparator for metric comparison
- `convergence.py` - ConvergenceChecker for stopping criteria

### Synchronous Execution (Phase 7)
- `backtest_sync.py` - SyncBacktestRunner for multicore backtest integration - **971 lines**
  - 동기식 단일 프로세스 백테스트 실행
  - 전체 지표 함수 내장 (현재가N, 등락율N, 체결강도N 등)
  - DB에서 전략 로드 시 조건명 prefix 제거

### Integration
- `backtest_icos.py` (in parent directory) - Main ICOS orchestration with existing backtest engine

## Subdirectories
- `optimization/` - Optimization algorithms
  - `base.py` - BaseOptimizer abstract class
  - `grid_search.py` - GridSearchOptimizer
  - `genetic.py` - GeneticOptimizer
  - `bayesian.py` - BayesianOptimizer
  - `walk_forward.py` - WalkForwardValidator
  - `__init__.py` - Exports all optimizers

## For AI Agents
When working with iterative optimization:

### System Philosophy
- **Measurement over Prediction**: Real backtests replace ML filter predictions
- **Iterative Refinement**: Convergence through repeated testing
- **Integration**: Works with existing multicore backtest infrastructure
- **Modularity**: Each component independently testable

### Usage Pattern
```python
from backtester.iterative_optimizer import IterativeOptimizer, IterativeConfig

config = IterativeConfig(
    enabled=True,
    max_iterations=5,
    convergence_method="plateau",
)
optimizer = IterativeOptimizer(config)
result = optimizer.run(buystg, sellstg)

if result.success:
    print(f"Improvement: {result.total_improvement:.2%}")
    print(f"Final strategy: {result.final_buystg[:100]}...")
```

### Phase Workflow
1. **Phase 1**: Config & Runner setup
2. **Phase 2**: Analyze baseline → Generate filter candidates
3. **Phase 3**: Build new conditions → Store iterations
4. **Phase 4**: Compare results → Check convergence
5. **Phase 5**: Advanced optimization (Grid/GA/Bayesian)
6. **Phase 6**: Walk-forward validation
7. **Phase 7**: Synchronous backtest execution

### Configuration
Three presets available:
- `PRESET_CONSERVATIVE` - Safe, fewer iterations
- `PRESET_AGGRESSIVE` - Maximum optimization
- `PRESET_QUICK_TEST` - Fast development testing

### Convergence Methods
- `plateau` - Stop when improvement stalls
- `threshold` - Stop at target improvement level
- `combined` - Use both criteria

### Optimization Methods
- `grid_search` - Exhaustive parameter search
- `genetic` - Evolutionary algorithm
- `bayesian` - Probabilistic optimization
- `walk_forward` - Time-series validation

### Filter Metrics
- `win_rate` - 승률 (win rate)
- `profit_factor` - 수익률 (profit rate)
- `sharpe` - Sharpe ratio
- `mdd` - Maximum drawdown

### Storage
- Results saved to `_icos_results/` directory
- JSON metadata with full configuration
- Iteration history for analysis
- Generated code saved to `.txt` files

### Integration Points
- `SyncBacktestRunner` bridges to multicore backtester
- Compatible with existing strategy format
- Uses same database schema (`strategy.db`)
- Outputs to `backtesting_output/` directory

## Dependencies
- numpy/pandas - Data processing
- optuna - Bayesian optimization
- All dependencies from `backtester/analysis/`
- Multicore backtesting system (via `SyncBacktestRunner`)

## Important Notes

### Analysis Independence
- **ICOS Analyzer vs Alt-I Settings**: ICOS의 `ResultAnalyzer`는 Alt-I 메뉴의 "분석 활성화" 설정과 **완전히 독립적**입니다.
  - Alt-I 메뉴의 `analysis_enabled`는 `backtester/analysis/plotting.py`의 `RunEnhancedAnalysis`만 제어
  - ICOS는 자체 `analyzer.py`를 사용하여 손실 패턴 분석 수행
  - 두 시스템은 서로 영향을 주지 않음

### Column Alignment (2026-01-20 Fix)
- `analyzer.py`의 `ANALYSIS_COLUMNS`는 `utility/setting.py`의 `columns_bt`와 일치해야 함
- 실제 df_tsg DataFrame 컬럼명 사용 필요 (예: '매수등락율', '매수체결강도', '시가총액' 등)
- 존재하지 않는 컬럼 (예: '모멘텀점수', '거래품질점수') 사용 시 분석 실패

## Known Issues & Fixes

### "분석할 손실 패턴 없음" 문제 (2026-01-20)
- **원인**: `ANALYSIS_COLUMNS`에 df_tsg에 존재하지 않는 컬럼명 사용
- **해결**: `columns_bt` 기반으로 실제 컬럼명으로 교체
- **추가 조치**: `min_confidence` 임계값 0.3 → 0.2로 하향 (더 많은 패턴 포착)
- **디버그 로그**: `_analyze_loss_patterns`에 상세 로그 추가

## Development Roadmap

### Phase 1: Core Stability (Completed)
- [x] 기본 ICOS 프레임워크 구축
- [x] 백테스트 엔진 통합
- [x] Alt-I 설정 UI 구현
- [x] 컬럼명 정합성 수정

### Phase 2: Enhanced Logging (Completed - 2026-01-20)
- [x] 반복 백테스트 결과 상세 로깅 (요약 → 전체 정보)
- [x] 분석 결과 디버그 로깅 추가
- [x] 진행상황 실시간 UI 업데이트

### Phase 3: Analysis Improvement (In Progress)
- [ ] 손실 패턴 탐지 알고리즘 고도화
  - [ ] 시간대별 패턴 분석 강화
  - [ ] 다중 조건 복합 패턴 탐지
  - [ ] 패턴 신뢰도 스코어링 개선
- [ ] 필터 후보 생성 로직 개선
  - [ ] 우선순위 기반 필터 선택
  - [ ] 상관관계 기반 중복 필터 제거
- [ ] 조건식 빌더 강화
  - [ ] AND/OR 조합 최적화
  - [ ] 파라미터 범위 자동 조정

### Phase 4: Advanced Optimization (Planned)
- [ ] 유전 알고리즘 파라미터 튜닝 연동
- [ ] 베이지안 최적화 통합 강화
- [ ] Walk-Forward 검증 자동화
- [ ] 과적합 방지 메커니즘

### Phase 5: UI/UX Enhancement (Planned)
- [ ] Alt-I 메뉴 개선
  - [ ] 분석 결과 시각화 (차트/그래프)
  - [ ] 반복별 개선율 추이 그래프
  - [ ] 필터 효과 히트맵
- [ ] 실시간 진행상황 모니터링
  - [ ] 예상 완료 시간 표시
  - [ ] 중간 중단/재개 기능
- [ ] 결과 내보내기
  - [ ] Excel/CSV 내보내기
  - [ ] 조건문서 자동 업데이트

### Phase 6: Integration & Automation (Future)
- [ ] 스케줄러 연동 (자동 ICOS 실행)
- [ ] 텔레그램 상세 알림 통합
- [ ] 이전 ICOS 결과 비교 분석
- [ ] 전략 버전 관리 시스템

## Alt-I Menu Configuration

### Current Features (set_dialog_icos.py)
| 섹션 | 옵션 | 설명 |
|------|------|------|
| 백테스팅 결과 분석 | 분석 활성화 | `RunEnhancedAnalysis` 제어 (ICOS와 무관) |
| Phase A | 필터 효과 분석 | 통계적 유의성 검정 |
| Phase A | 최적 임계값 탐색 | 그리드 서치 방식 |
| Phase A | 필터 조합 분석 | 상호작용 효과 분석 |
| Phase A | 필터 안정성 검증 | 시간대별 일관성 확인 |
| Phase A | 필터 조건식 자동 생성 | Python 코드 변환 |
| ML 분석 | ML 위험도 예측 | XGBoost 모델 |
| ML 분석 | ML 특성 중요도 | 변수별 순위 표시 |
| Phase C | 세그먼트 분석 | 시간대/요일/가격대별 성과 |
| Phase C | Optuna 최적화 | 베이지안 파라미터 탐색 |
| ICOS | ICOS 활성화 | 반복 조건식 개선 |
| ICOS | 최대 반복 | 1~20회 (권장 3~5회) |
| ICOS | 수렴 기준 | 개선율 임계값 (%) |
| ICOS | 최적화 기준 | 수익금/승률/수익팩터/샤프비율/MDD/복합점수 |
| ICOS | 최적화 방법 | 그리드서치/유전알고리즘/베이지안 |

### Improvement Opportunities
1. **분석 결과 시각화**: 현재 텍스트 로그만 표시 → 차트/그래프 추가
2. **프리셋 저장/로드**: 자주 사용하는 설정 조합 저장 기능
3. **배치 실행**: 여러 전략 순차 ICOS 실행
4. **히스토리 뷰어**: 과거 ICOS 실행 결과 조회
5. **조건문서 연동**: ICOS 결과를 /docs/Condition/ 문서에 자동 반영

## Branch Information
- Development branch: `feature/icos-complete-implementation`
- Current version: 0.7.1
- Author: STOM Development Team
- Created: 2026-01-12
- Last Updated: 2026-01-20
