# ICOS (Iterative Condition Optimization System) Phase 3-6 개선 마스터 플랜

## 문서 정보

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-01-20 |
| 브랜치 | `feature/icos-phase3-6-improvements` |
| 상위 브랜치 | `feature/icos-complete-implementation` |
| 예상 작업 범위 | 17개 파일 (~7,765줄) 수정/추가 |

---

## 1. 개요

ICOS Phase 3-6 개선 작업을 위한 체계적인 개발 계획입니다.

### 1.1 현재 상태 (Phase 1-2 완료)

| Phase | 상태 | 설명 |
|-------|------|------|
| Phase 1 | 완료 | Core Stability - 기본 프레임워크, 백테스트 엔진 통합 |
| Phase 2 | 완료 | Enhanced Logging - 상세 로깅, 진행상황 UI 업데이트 |
| Phase 3 | 진행중 | Analysis Improvement - 분석 고도화 |
| Phase 4 | 계획 | Advanced Optimization - 고급 최적화 |
| Phase 5 | 계획 | UI/UX Enhancement - UI 개선 |
| Phase 6 | 계획 | Integration & Automation - 통합/자동화 |

### 1.2 목표

1. **분석 정확도 향상**: 손실 패턴 탐지 알고리즘 고도화
2. **과적합 방지**: Walk-Forward 검증, 과적합 감지 메커니즘
3. **사용성 개선**: 실시간 모니터링, 일시정지/재개 기능
4. **자동화 강화**: 스케줄러, 텔레그램 알림 통합

---

## 2. Phase 3: Analysis Improvement (분석 고도화)

### 2.1 analyzer.py 수정 (750줄 → ~950줄)

#### 추가할 메서드

```python
# 1. 시간대 패턴 분석 강화
def _analyze_time_patterns_advanced(self, df_tsg, loss_mask, total_loss_count):
    """
    고급 시간대 패턴 분석:
    - 5분 단위 세분화 분석 (기존 1시간 → 5분)
    - 요일별 패턴 분석 (월~금)
    - 장 시작/종료 세션 분석 (09:00-09:30, 15:00-15:30)
    - 점심 시간대 분석 (12:00-13:00)
    """

# 2. 복합 조건 패턴 탐지
def _analyze_compound_patterns(self, df_tsg, loss_mask, total_loss_count):
    """
    복합 조건 패턴 탐지:
    - 시간+가격 복합 패턴 (예: 10시 AND 등락율>20%)
    - 거래량+체결강도 복합 패턴
    - 호가잔량비+스프레드 복합 패턴
    - 최대 2-3개 조건 조합
    """

# 3. 신뢰도 스코어링 개선
def _calculate_pattern_confidence_advanced(self, ...):
    """
    고급 신뢰도 계산:
    - 카이제곱 검정 기반 통계적 유의성 (scipy.stats.chi2_contingency)
    - Cohen's h 효과 크기 (비율 차이의 효과 크기)
    - 표본 적정성 점수 (n≥30 기준)
    - 다중 검정 보정 (Bonferroni/FDR)
    """
```

#### 수정 사항

| 기존 메서드 | 변경 내용 |
|------------|----------|
| `_analyze_time_patterns` | 5분 단위 세분화, 요일 분석 추가 |
| `_analyze_threshold_patterns` | 분위수 세분화 (10개 → 20개) |
| `_analyze_loss_patterns` | 복합 패턴 분석 호출 추가 |
| `_calculate_pattern_confidence` | 카이제곱 검정 추가 |

### 2.2 filter_generator.py 수정 (506줄 → ~650줄)

#### 추가할 메서드

```python
# 1. 상관관계 기반 중복 필터 제거
def _remove_correlated_filters(self, candidates, threshold=0.7):
    """
    상관관계 분석으로 중복 필터 제거:
    - 동일 컬럼 기반 필터 그룹화
    - 조건 겹침 정도 계산
    - 상관계수 > threshold인 경우 상위 점수 필터만 유지
    """

# 2. 필터 시너지 분석
def _analyze_filter_synergy(self, candidates, df_tsg):
    """
    필터 조합 시너지 효과 계산:
    - 개별 필터 효과 vs 조합 효과 비교
    - 시너지 점수 = 조합 효과 / (개별 효과 합)
    - 시너지 > 1.0이면 긍정적 상호작용
    """

# 3. 우선순위 기반 선택
def _select_by_priority(self, candidates, max_count):
    """
    우선순위 기반 필터 선택:
    - CRITICAL > HIGH > MEDIUM > LOW > EXPERIMENTAL
    - 각 우선순위 내에서 점수 순 정렬
    - 다양성 보장 (동일 컬럼 필터 최대 2개)
    """
```

#### 수정 사항

| 기존 메서드 | 변경 내용 |
|------------|----------|
| `generate` | 상관관계 필터링, 시너지 분석 추가 |
| `_deduplicate` | 상관관계 기반 제거로 강화 |
| `_calculate_score` | 시너지 점수 반영 |

### 2.3 condition_builder.py 수정 (522줄 → ~700줄)

#### 추가할 메서드

```python
# 1. AND/OR 조합 최적화
def build_optimized_combinations(self, buystg, filters, strategy='greedy'):
    """
    AND/OR 조합 최적화:
    - strategy='greedy': 탐욕적 접근 (순차 추가)
    - strategy='exhaustive': 완전 탐색 (2^n 조합)
    - strategy='genetic': 유전 알고리즘 (대규모)

    각 조합의 예상 효과 계산 후 최적 조합 선택
    """

# 2. 임계값 자동 조정
def _auto_adjust_threshold(self, df_tsg, column, initial_threshold, direction):
    """
    임계값 자동 조정:
    - ±30% 범위 내 탐색
    - 10단계 그리드 서치
    - 손실률 최소화 임계값 선택
    - 샘플 수 최소 30개 유지
    """

# 3. 필터 충돌 감지
def _detect_filter_conflicts(self, filters):
    """
    필터 충돌 감지:
    - 상반된 조건 감지 (예: X > 10 AND X < 5)
    - 완전 포함 관계 감지 (예: X > 5 AND X > 3)
    - 충돌 시 우선순위 높은 필터 유지
    """
```

---

## 3. Phase 4: Advanced Optimization (고급 최적화)

### 3.1 overfitting_guard.py (신규 생성, ~200줄)

```python
"""
과적합 감지 및 방지 모듈.

기능:
1. Train/Test 성능 차이 모니터링
2. 과적합 경고 및 알림
3. 조기 종료 권고
"""

@dataclass
class OverfitMetrics:
    train_profit: float
    test_profit: float
    train_win_rate: float
    test_win_rate: float
    profit_gap: float  # 수익금 차이 비율
    win_rate_gap: float  # 승률 차이
    is_overfitting: bool
    severity: str  # 'low', 'medium', 'high'
    recommendation: str

class OverfittingGuard:
    """과적합 감지기."""

    def __init__(self, config: IterativeConfig):
        self.max_gap_threshold = config.validation.max_train_test_gap

    def check(self, train_metrics, test_metrics) -> OverfitMetrics:
        """과적합 여부 확인."""

    def get_recommendation(self, metrics: OverfitMetrics) -> str:
        """과적합 대응 권고사항 반환."""

    def should_stop_early(self, history: List[OverfitMetrics]) -> bool:
        """조기 종료 여부 판단."""
```

### 3.2 integrated_optimizer.py (신규 생성, ~300줄)

```python
"""
통합 최적화기 모듈.

Grid Search, Genetic Algorithm, Bayesian 최적화를 통합 관리.
ICOS와 연동하여 필터 파라미터 자동 튜닝.
"""

class IntegratedOptimizer:
    """통합 최적화기."""

    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.optimizers = {
            OptimizationMethod.GRID_SEARCH: GridSearchOptimizer(),
            OptimizationMethod.GENETIC: GeneticOptimizer(),
            OptimizationMethod.BAYESIAN: BayesianOptimizer(),
        }

    def optimize(self, filters: List[FilterCandidate],
                 df_tsg: pd.DataFrame) -> List[FilterCandidate]:
        """필터 파라미터 최적화."""

    def _optimize_single_filter(self, filter: FilterCandidate,
                                 df_tsg: pd.DataFrame) -> FilterCandidate:
        """단일 필터 임계값 최적화."""

    def get_optimal_combination(self, filters: List[FilterCandidate],
                                 max_size: int = 3) -> List[FilterCandidate]:
        """최적 필터 조합 탐색."""
```

### 3.3 runner.py 수정 (866줄 → ~1,100줄)

#### 추가할 기능

```python
# 1. Walk-Forward 검증 자동화
def _run_with_walk_forward_validation(self, buystg, sellstg, params):
    """
    Walk-Forward 검증:
    - 전체 기간을 n_folds로 분할
    - 각 fold에서 train/test 분리
    - 모든 fold의 test 성과 평균 계산
    - Train vs Test 성능 차이 모니터링
    """

# 2. 과적합 감지 연동
def _check_overfitting(self, iteration_result):
    """
    OverfittingGuard 연동:
    - 매 반복마다 과적합 체크
    - 심각도에 따른 경고 로그
    - 조기 종료 조건 확인
    """

# 3. 일시정지/재개 기능
def request_pause(self):
    """일시정지 요청."""
    self._pause_requested = True

def request_stop(self):
    """중지 요청."""
    self._stop_requested = True

def resume(self):
    """재개."""
    self._pause_requested = False

def _save_checkpoint(self):
    """현재 상태 체크포인트 저장."""
```

---

## 4. Phase 5: UI/UX Enhancement (UI 개선)

### 4.1 set_dialog_icos.py 수정 (722줄 → ~900줄)

#### 추가할 UI 컴포넌트

```python
# 1. 진행 현황 차트 (pyqtgraph)
self.ui.icos_progress_chart = pg.PlotWidget(...)
# - X축: 반복 번호
# - Y축 (좌): 수익금 (파란색 라인)
# - Y축 (우): 승률 (녹색 라인)
# - 실시간 업데이트

# 2. 필터 효과 테이블
self.ui.icos_filter_table = QTableWidget(...)
# 컬럼: 반복, 필터명, 적용전 수익금, 적용후 수익금, 개선율, 신뢰도

# 3. 일시정지/재개 버튼
self.ui.icos_pause_button = QPushButton('일시정지')
self.ui.icos_pause_button.clicked.connect(self._on_pause_clicked)

self.ui.icos_resume_button = QPushButton('재개')
self.ui.icos_resume_button.clicked.connect(self._on_resume_clicked)
self.ui.icos_resume_button.setEnabled(False)

# 4. 예상 완료 시간 표시
self.ui.icos_eta_label = QLabel('예상 완료: --:--:--')
```

#### 레이아웃 변경

| 영역 | 변경 내용 |
|------|----------|
| 상단 | 진행 차트 추가 (높이 150px) |
| 중단 | 필터 효과 테이블 추가 |
| 하단 | 일시정지/재개 버튼 추가 |
| 우측 | ETA 표시 라벨 추가 |

### 4.2 runner.py UI 업데이트 추가

```python
# UI 진행상황 업데이트
def _update_ui_progress(self, iteration_result):
    """UI 진행상황 업데이트."""
    if self.qlist and len(self.qlist) > 0:
        windowQ = self.qlist[0]
        # 차트 데이터 전송
        windowQ.put(('icos_chart_update', {
            'iteration': iteration_result.iteration,
            'profit': iteration_result.metrics.get('total_profit', 0),
            'win_rate': iteration_result.metrics.get('win_rate', 0),
        }))
        # 테이블 데이터 전송
        windowQ.put(('icos_table_update', {
            'filters': [f.to_dict() for f in iteration_result.applied_filters],
        }))

def _estimate_remaining_time(self):
    """남은 시간 예측."""
    if self.현재반복 == 0:
        return "계산 중..."
    elapsed = (datetime.now() - self._start_time).total_seconds()
    avg_per_iter = elapsed / (self.현재반복 + 1)
    remaining = (self.config.max_iterations - self.현재반복 - 1) * avg_per_iter
    return self._format_duration(remaining)
```

---

## 5. Phase 6: Integration & Automation (통합/자동화)

### 5.1 scheduler.py (신규 생성, ~150줄)

```python
"""
ICOS 자동 스케줄링 모듈.

기능:
1. 주기적 ICOS 실행 스케줄링
2. 조건 기반 트리거 (수익률 하락 시 등)
3. 배치 실행 (여러 전략 순차 실행)
"""

from dataclasses import dataclass
from typing import List, Callable, Optional
from datetime import datetime, timedelta
import threading

@dataclass
class ScheduleConfig:
    """스케줄 설정."""
    strategy_name: str
    interval: timedelta  # 실행 간격
    enabled: bool = True
    last_run: Optional[datetime] = None
    trigger_condition: Optional[Callable] = None  # 조건부 트리거

class ICOSScheduler:
    """ICOS 스케줄러."""

    def __init__(self, optimizer_factory: Callable):
        self.optimizer_factory = optimizer_factory
        self.schedules: List[ScheduleConfig] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def add_schedule(self, config: ScheduleConfig):
        """스케줄 추가."""
        self.schedules.append(config)

    def remove_schedule(self, strategy_name: str):
        """스케줄 제거."""
        self.schedules = [s for s in self.schedules
                         if s.strategy_name != strategy_name]

    def start(self):
        """스케줄러 시작."""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop)
        self._thread.start()

    def stop(self):
        """스케줄러 중지."""
        self._running = False
        if self._thread:
            self._thread.join()

    def _run_loop(self):
        """스케줄 실행 루프."""
        while self._running:
            for schedule in self.schedules:
                if self._should_run(schedule):
                    self._execute(schedule)
            time.sleep(60)  # 1분 대기

    def _should_run(self, schedule: ScheduleConfig) -> bool:
        """실행 여부 판단."""
        if not schedule.enabled:
            return False
        if schedule.last_run is None:
            return True
        if datetime.now() - schedule.last_run >= schedule.interval:
            if schedule.trigger_condition:
                return schedule.trigger_condition()
            return True
        return False

    def _execute(self, schedule: ScheduleConfig):
        """스케줄 실행."""
        optimizer = self.optimizer_factory(schedule.strategy_name)
        result = optimizer.run()
        schedule.last_run = datetime.now()
        self._send_notification(schedule.strategy_name, result)
```

### 5.2 텔레그램 알림 강화 (runner.py)

```python
def _send_telegram_summary(self, result):
    """상세 ICOS 완료 알림."""
    if not self.config.telegram_notify or not self.qlist:
        return

    # 텔레그램 큐 (qlist[3])
    teleQ = self.qlist[3]

    # 요약 메시지 생성
    message = self._format_telegram_message(result)

    # 전송
    teleQ.put(('telegram', message))

def _format_telegram_message(self, result) -> str:
    """텔레그램 메시지 포맷."""
    lines = [
        "═══ ICOS 완료 알림 ═══",
        f"",
        f"🎯 전략: {self.backtest_params.get('strategy_name', 'Unknown')}",
        f"⏱️ 실행 시간: {result.total_execution_time:.1f}초",
        f"🔄 반복 횟수: {result.num_iterations}회",
        f"📈 개선율: {result.total_improvement:.2%}",
        f"",
        f"━━━ 성과 변화 ━━━",
    ]

    if result.initial_metrics and result.final_metrics:
        init = result.initial_metrics
        final = result.final_metrics
        lines.extend([
            f"수익금: {init.get('total_profit', 0):,.0f} → {final.get('total_profit', 0):,.0f}",
            f"승률: {init.get('win_rate', 0):.1f}% → {final.get('win_rate', 0):.1f}%",
            f"MDD: {init.get('max_drawdown', 0):.1f}% → {final.get('max_drawdown', 0):.1f}%",
        ])

    lines.extend([
        f"",
        f"📋 종료 사유: {result.convergence_reason}",
        f"",
        f"═══════════════════",
    ])

    return "\n".join(lines)
```

---

## 6. 파일별 수정 요약

### 6.1 수정 파일 (6개)

| 파일 | 현재 | 예상 | 주요 변경 |
|------|------|------|----------|
| `analyzer.py` | 750줄 | ~950줄 | 시간대 패턴 강화, 복합 패턴, 신뢰도 개선 |
| `filter_generator.py` | 506줄 | ~650줄 | 상관관계 제거, 시너지 분석, 우선순위 선택 |
| `condition_builder.py` | 522줄 | ~700줄 | AND/OR 최적화, 임계값 자동 조정 |
| `runner.py` | 866줄 | ~1,100줄 | Walk-Forward, 과적합 체크, 일시정지/재개 |
| `set_dialog_icos.py` | 722줄 | ~900줄 | 진행 차트, 필터 테이블, 버튼 추가 |
| `AGENTS.md (iterative_optimizer)` | 222줄 | ~400줄 | Phase 3-6 상세 문서화 |

### 6.2 신규 파일 (3개)

| 파일 | 예상 라인 | 목적 |
|------|----------|------|
| `overfitting_guard.py` | ~200줄 | 과적합 감지/방지 |
| `optimization/integrated_optimizer.py` | ~300줄 | 통합 최적화기 |
| `scheduler.py` | ~150줄 | 자동 스케줄링 |

---

## 7. 개발 순서

### Step 1: 문서 준비 (완료)
1. ✅ `feature/icos-phase3-6-improvements` 브랜치 생성
2. ✅ 이 문서 (`20260120_ICOS_Phase3-6_Master_Plan.md`) 생성
3. `AGENTS.md` 파일들 업데이트
4. `CLAUDE.md`에 ICOS 섹션 추가

### Step 2: Phase 3 구현
1. `analyzer.py` - 패턴 분석 고도화
2. `filter_generator.py` - 필터 생성 개선
3. `condition_builder.py` - 조건식 빌더 강화
4. 단위 테스트 작성 및 검증

### Step 3: Phase 4 구현
1. `overfitting_guard.py` 신규 생성
2. `integrated_optimizer.py` 신규 생성
3. `runner.py` - Walk-Forward 검증 통합
4. 통합 테스트

### Step 4: Phase 5 구현
1. `set_dialog_icos.py` - UI 컴포넌트 추가
2. `runner.py` - 일시정지/재개, UI 업데이트
3. UI 동작 테스트

### Step 5: Phase 6 구현
1. `scheduler.py` 신규 생성
2. 텔레그램 알림 강화
3. 전체 통합 테스트

### Step 6: 최종 검증 및 커밋
1. 전체 기능 테스트
2. 문서 최종 확인
3. 커밋 및 PR

---

## 8. 검증 계획

### 8.1 단위 테스트

```bash
# Phase 3 테스트
pytest tests/test_analyzer_enhanced.py
pytest tests/test_filter_generator_enhanced.py
pytest tests/test_condition_builder_enhanced.py

# Phase 4 테스트
pytest tests/test_overfitting_guard.py
pytest tests/test_integrated_optimizer.py
```

### 8.2 통합 테스트

```bash
# 전체 ICOS 사이클 테스트
pytest tests/test_icos_integration.py

# UI 테스트 (수동)
python stom.py → Alt-I → ICOS 실행 → 진행 확인
```

### 8.3 성능 기준

| 지표 | 목표 |
|------|------|
| 단일 반복 시간 | < 60초 |
| 메모리 사용량 | < 2GB |
| 패턴 탐지 정확도 | > 80% |
| 필터 개선 효과 | > 10% |

---

## 9. 핵심 파일 경로

```
C:\System_Trading\STOM\STOM_V1\
├── backtester/iterative_optimizer/
│   ├── analyzer.py              # Phase 3 주요 수정
│   ├── filter_generator.py      # Phase 3 주요 수정
│   ├── condition_builder.py     # Phase 3 주요 수정
│   ├── runner.py                # Phase 4-5 주요 수정
│   ├── overfitting_guard.py     # Phase 4 신규 생성
│   ├── scheduler.py             # Phase 6 신규 생성
│   ├── AGENTS.md                # 문서 업데이트
│   └── optimization/
│       └── integrated_optimizer.py  # Phase 4 신규 생성
├── ui/
│   └── set_dialog_icos.py       # Phase 5 주요 수정
├── docs/Study/Development/
│   └── 20260120_ICOS_Phase3-6_Master_Plan.md  # 이 문서
├── backtester/AGENTS.md         # 문서 업데이트
└── CLAUDE.md                    # ICOS 섹션 추가
```

---

## 10. 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2026-01-20 | 1.0 | 초기 계획 수립 |

---

## 관련 문서

- [ICOS 기존 구현 계획](20260114_ICOS_Complete_Implementation_Plan.md)
- [ICOS Dialog Enhancement Plan](20260113_ICOS_Dialog_Enhancement_Plan.md)
- [ICOS AGENTS.md](../../backtester/iterative_optimizer/AGENTS.md)
- [Backtester AGENTS.md](../../backtester/AGENTS.md)
