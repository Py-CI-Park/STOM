# ICOS 파이프라인 분석 및 통합 계획

> **작성일**: 2026-01-15
> **브랜치**: feature/iterative-condition-optimizer
> **목적**: ICOS(반복적 조건식 개선 시스템) 현황 분석 및 통합 방안 수립

---

## 1. 프로젝트 목표 재확인

### 1.1 최종 목적

**"매수/매도 조건식을 사용하여 백테스팅을 진행하고, 그 조건식 결과를 분석하여 개선하면서 iteration 반복을 통해 조건식을 스스로 수정하여 좋은 백테스팅 결과를 찾아내는 시스템"**

### 1.2 기대 효과

```
초기 조건식 → 백테스트 → 분석 → 필터 생성 → 조건식 수정 → 재백테스트 → ... → 최적화된 조건식
     ↑                                                              ↓
     └──────────────────── 반복 (수렴까지) ────────────────────────┘
```

---

## 2. 현재 시스템 아키텍처

### 2.1 백테스팅 실행 흐름 (일반 백테스트 버튼)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        일반 백테스트 실행 흐름                              │
└─────────────────────────────────────────────────────────────────────────────┘

사용자 액션: 스케줄러 다이얼로그에서 "백테스트" 버튼 클릭
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ sdbutton_clicked_02(ui)                                                     │
│ 파일: ui/ui_button_clicked_sd.py:282                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. 중복 실행 확인 (BacktestProcessAlive)                                    │
│ 2. 백테엔진 시작 여부 확인                                                  │
│ 3. 스케줄 카운터 증가 (back_scount)                                         │
│ 4. 활성화된 체크박스 찾기                                                   │
│ 5. back_name = "백테스트" 확인                                              │
│                              │                                              │
│    ┌─────────────────────────┴─────────────────────────┐                    │
│    │         ICOS 활성화 여부 체크                      │                    │
│    │         _check_icos_enabled(ui)                   │                    │
│    │         파일: ui_button_clicked_sd.py:313         │                    │
│    └─────────────────────────┬─────────────────────────┘                    │
│                              │                                              │
│              ┌───────────────┴───────────────┐                              │
│              ▼                               ▼                              │
│    ┌─────────────────┐            ┌─────────────────┐                       │
│    │ ICOS 비활성화   │            │ ICOS 활성화     │                       │
│    │ (icos_enabled   │            │ (icos_enabled   │                       │
│    │  = False)       │            │  = True)        │                       │
│    └────────┬────────┘            └────────┬────────┘                       │
│             │                              │                                │
│             ▼                              ▼                                │
│    ┌─────────────────┐            ┌─────────────────────────┐               │
│    │ 기존 BackTest   │            │ _run_icos_backtest()    │               │
│    │ 프로세스 실행   │            │ ICOS 모드 실행          │               │
│    │ :347-375        │            │ :344                    │               │
│    └─────────────────┘            └─────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 기존 BackTest 프로세스 상세 흐름

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    기존 BackTest 프로세스 흐름                              │
└─────────────────────────────────────────────────────────────────────────────┘

sdbutton_clicked_02 (icos_enabled = False 경로)
    │
    ├─ 1. backQ.put((betting, avgtime, ...))     # 파라미터 전송
    │
    ├─ 2. back_eques[].put(('백테유형', '백테스트'))   # 유형 설정
    │
    └─ 3. Process(target=BackTest, args=(...)).start()
           │
           ▼
    ┌───────────────────────────────────────────────────────────────────┐
    │ BackTest 클래스 (backtester/backtest.py:258)                      │
    ├───────────────────────────────────────────────────────────────────┤
    │ __init__()                                                        │
    │   ├─ 큐 할당: wq, bq, sq, tq, lq, teleQ, beq_list, bstq_list     │
    │   └─ Start() 호출                                                 │
    │                                                                   │
    │ Start() (line 274)                                                │
    │   ├─ 1. backQ.get() → 파라미터 추출                              │
    │   ├─ 2. GetMoneytopQuery() → 시장 데이터 SQL 쿼리                │
    │   ├─ 3. pd.read_sql() → df_mt 로드                               │
    │   ├─ 4. Total 프로세스 생성 (결과 수집기)                        │
    │   │      └─ Process(target=Total, args=(...)).start()            │
    │   └─ 5. BackEngine들에게 명령 전송                               │
    │          ├─ beq_list[i].put(('백테정보', ...))                   │
    │          └─ beq_list[i].put(('백테시작', 2))                     │
    └───────────────────────────────────────────────────────────────────┘
           │
           ▼ (병렬 실행)
    ┌───────────────────────────────────────────────────────────────────┐
    │ BackEngine 프로세스들 (12개 병렬)                                 │
    │ 파일: backtester/backengine_*_*.py                                │
    ├───────────────────────────────────────────────────────────────────┤
    │ MainLoop():                                                       │
    │   ├─ beq.get() 대기                                              │
    │   ├─ '백테정보' → 조건식 컴파일 (GetBuyStg, GetSellStg)          │
    │   ├─ '백테시작' → 시뮬레이션 실행                                │
    │   │   ├─ DataLoad() - 틱/분봉 데이터 로드                        │
    │   │   └─ CodeLoop() - 조건식 평가 및 거래 시뮬레이션             │
    │   └─ tq.put(('백테완료',)) → Total에 완료 신호                   │
    └───────────────────────────────────────────────────────────────────┘
           │
           ▼
    ┌───────────────────────────────────────────────────────────────────┐
    │ Total 클래스 (backtester/backtest.py:18)                          │
    ├───────────────────────────────────────────────────────────────────┤
    │ MainLoop() (line 63):                                             │
    │   ├─ '백테완료' (bc++) → 모든 엔진 완료 시 '분리집계' 명령       │
    │   ├─ '집계완료' (sc++) → '결과분리' 명령                         │
    │   ├─ '분리완료' (sc++) → '결과전송' 명령                         │
    │   └─ '백테결과' → Report() 호출                                  │
    │                                                                   │
    │ Report() (line 166):                                              │
    │   ├─ GetResultDataframe() → df_tsg 생성                          │
    │   ├─ GetBackResult() → 15개 성과 지표 계산                       │
    │   ├─ DB 저장 (df.to_sql, df_tsg.to_sql)                          │
    │   ├─ PltShow() → 그래프 생성/저장                                │
    │   └─ ★ RunEnhancedAnalysis() 호출 (분석 파이프라인)              │
    └───────────────────────────────────────────────────────────────────┘
```

### 2.3 분석 파이프라인 (RunEnhancedAnalysis)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    분석 파이프라인 12단계                                   │
│            파일: backtester/analysis_enhanced/runner.py:412                 │
└─────────────────────────────────────────────────────────────────────────────┘

RunEnhancedAnalysis(df_tsg, save_file_name, teleQ, analysis_config)
    │
    ├─ Step 1: CalculateEnhancedDerivedMetrics()
    │          → df_tsg에 파생 지표 추가 (df_enhanced)
    │
    ├─ Step 2: PredictRiskWithML()
    │          → ML 위험도 예측 (손실확률_ML, 위험도_ML)
    │
    ├─ Step 3: AnalyzeFilterEffectsEnhanced()
    │          → 단일 필터 효과 분석 + OOS 검증
    │          → filter_results 리스트 생성
    │
    ├─ Step 3-1: AnalyzeFilterEffectsLookahead()
    │            → 미래정보 활용 시 성능 비교 (참고용)
    │
    ├─ Step 4: FindAllOptimalThresholds()
    │          → 각 필터의 최적 임계값 탐색
    │
    ├─ Step 5: AnalyzeFilterCombinations()
    │          → 필터 조합 분석 (시너지 효과)
    │
    ├─ Step 6: AnalyzeFeatureImportance()
    │          → ML 특성 중요도 분석
    │
    ├─ Step 7: AnalyzeFilterStability()
    │          → 필터 시간 안정성 검증
    │
    ├─ Step 8: GenerateFilterCode()
    │          → Python 조건식 코드 자동 생성
    │
    ├─ Step 9: PltEnhancedAnalysisCharts()
    │          → 분석 결과 시각화
    │
    ├─ Step 10: 세그먼트 분석 (선택)
    │           → run_phase2(), run_segment_template_comparison()
    │
    ├─ Step 11: 결과 저장 (CSV, JSON)
    │
    └─ Step 12: 분석 로그 저장
```

---

## 3. ICOS 모듈 구조

### 3.1 ICOS 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ICOS 모듈 구조                                           │
│            디렉토리: backtester/iterative_optimizer/                        │
└─────────────────────────────────────────────────────────────────────────────┘

backtester/iterative_optimizer/
├── __init__.py (201줄)              # 패키지 API
├── config.py (309줄)                # 설정 클래스 ✅ 완료
├── data_types.py (81줄)             # 데이터 클래스 ✅ 완료
├── runner.py (583줄)                # 메인 오케스트레이터 ⚠️ 70%
├── analyzer.py (720줄)              # 결과 분석기 ✅ 완료
├── filter_generator.py (505줄)      # 필터 생성 ✅ 완료
├── condition_builder.py (521줄)     # 조건식 빌드 ✅ 완료
├── storage.py (537줄)               # 저장/로드 ✅ 완료
├── comparator.py (494줄)            # 비교기 ✅ 완료
├── convergence.py (482줄)           # 수렴 판정 ✅ 완료
├── backtest_sync.py                 # 동기식 백테스트 러너 ⚠️ 미완성
└── optimization/                    # 최적화 알고리즘 ⚠️ 50%
    ├── base.py (384줄)
    ├── grid_search.py (274줄)
    ├── genetic.py (465줄)
    ├── bayesian.py (321줄)
    └── walk_forward.py (521줄)
```

### 3.2 ICOS 실행 흐름 (현재 구현 상태)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ICOS 실행 흐름 (현재 구현)                               │
└─────────────────────────────────────────────────────────────────────────────┘

sdbutton_clicked_02() (icos_enabled = True 경로)
    │
    └─→ _run_icos_backtest()
        파일: ui/ui_button_clicked_sd.py:64-219
        │
        ├─ 1. ICOS 프로세스 중복 확인
        ├─ 2. ICOS 설정 수집 (_collect_icos_config)
        ├─ 3. 백테스트 파라미터 구성
        ├─ 4. dict_cn 검증 (백테엔진 시작 필수)
        └─ 5. Process(target=_run_icos_process, ...).start()
               │
               ▼
        ┌───────────────────────────────────────────────────────────────┐
        │ _run_icos_process()                                           │
        │ 파일: ui/ui_button_clicked_icos.py:586-634                    │
        ├───────────────────────────────────────────────────────────────┤
        │ 1. IterativeConfig.from_dict(config_dict)                     │
        │ 2. IterativeOptimizer(config, qlist, backtest_params)         │
        │ 3. result = optimizer.run(buystg, sellstg, params)            │
        │ 4. windowQ에 결과 전송                                        │
        └───────────────────────────────────────────────────────────────┘
               │
               ▼
        ┌───────────────────────────────────────────────────────────────┐
        │ IterativeOptimizer.run()                                      │
        │ 파일: backtester/iterative_optimizer/runner.py:214            │
        ├───────────────────────────────────────────────────────────────┤
        │ 반복 루프:                                                    │
        │ while 현재반복 < max_iterations and not 수렴여부:             │
        │   │                                                           │
        │   ├─ [1/4] _execute_backtest() ⚠️ 스켈레톤                    │
        │   │        → 빈 df_tsg, 0 metrics 반환                       │
        │   │        → TODO: 기존 BackEngine 연동                      │
        │   │                                                           │
        │   ├─ [2/4] _analyze_result() ✅ 구현됨                        │
        │   │        → ResultAnalyzer.analyze(df_tsg)                  │
        │   │                                                           │
        │   ├─ [3/4] _generate_filters() ✅ 구현됨                      │
        │   │        → FilterGenerator.generate(analysis)              │
        │   │                                                           │
        │   ├─ [4/4] _build_new_condition() ✅ 구현됨                   │
        │   │        → ConditionBuilder.build(buystg, filters)         │
        │   │                                                           │
        │   └─ _check_convergence() ✅ 구현됨                           │
        │      → ConvergenceChecker.check(반복결과목록)                │
        │                                                               │
        └─ return IterativeResult(success, final_buystg, ...)          │
        └───────────────────────────────────────────────────────────────┘
```

---

## 4. 현재 문제점 분석

### 4.1 핵심 문제: `_execute_backtest()` 미구현

```python
# 파일: backtester/iterative_optimizer/runner.py:370-404

def _execute_backtest(self, buystg: str, sellstg: str, params: dict) -> dict:
    """백테스트 실행.

    ⚠️ 현재: 스켈레톤 상태 - 빈 결과 반환
    TODO: Phase 2에서 기존 백테스팅 시스템 연동
    """
    # 현재 구현: 빈 결과 반환
    return {
        'df_tsg': pd.DataFrame(),  # 빈 DataFrame
        'metrics': {
            'total_profit': 0,
            'win_rate': 0,
            'trade_count': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
        },
        'execution_time': 0,
    }
```

**결과**: ICOS가 실행되더라도 실제 백테스트가 수행되지 않음

### 4.2 문제 영향 분석

```
ICOS 시작 → _execute_backtest() 호출 → 빈 DataFrame 반환
                                              │
                                              ▼
                                       _analyze_result()
                                              │
                                              ▼
                                   빈 데이터로 분석 시도
                                              │
                                              ▼
                                       분석 실패 또는
                                       무의미한 결과
                                              │
                                              ▼
                                   필터 생성 불가 또는
                                   잘못된 필터 생성
                                              │
                                              ▼
                                   조건식 개선 없음
                                              │
                                              ▼
                                   ★ ICOS 목적 달성 불가
```

### 4.3 현재 흐름의 연결 끊김 지점

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         연결 끊김 지점 분석                                 │
└─────────────────────────────────────────────────────────────────────────────┘

기존 백테스팅 시스템:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ BackTest     │───→│ BackEngine   │───→│ Total.Report │
│ (오케스트레이터)│    │ (12개 병렬)   │    │ (결과 수집)  │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                                               ▼
                                    ┌──────────────────┐
                                    │ df_tsg 생성      │
                                    │ (거래 상세 DF)    │
                                    └──────────────────┘
                                               │
                                               ▼
                                    ┌──────────────────┐
                                    │ RunEnhanced      │
                                    │ Analysis()       │
                                    │ (분석 파이프라인) │
                                    └──────────────────┘
                                               │
                            ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─
                            │    연결 끊김      │                  │
                            ▼                  ▼                  ▼
ICOS 시스템:
┌──────────────────────────────────────────────────────────────────────────┐
│ IterativeOptimizer                                                       │
│                                                                          │
│   _execute_backtest() ─────── ✗ 연결 안됨 ─────── BackEngine            │
│          │                                                               │
│          ▼                                                               │
│   빈 df_tsg 반환                                                         │
│          │                                                               │
│          ▼                                                               │
│   _analyze_result() ────── 분석 모듈은 준비됨 ────── ResultAnalyzer     │
│          │                                                               │
│          ▼                                                               │
│   _generate_filters() ─── 필터 생성 모듈 준비됨 ─── FilterGenerator     │
│          │                                                               │
│          ▼                                                               │
│   _build_new_condition() ─ 조건식 빌더 준비됨 ── ConditionBuilder       │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 해결 방안

### 5.1 방안 A: SyncBacktestRunner 완성 (권장)

**개념**: ICOS 전용 동기식 백테스트 러너를 완성하여 기존 BackEngine과 동일한 결과를 생성

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    방안 A: SyncBacktestRunner 완성                          │
└─────────────────────────────────────────────────────────────────────────────┘

_execute_backtest()
    │
    └─→ SyncBacktestRunner(backtest_params)
        │
        ├─ 1. 조건식 컴파일 (GetBuyStg, GetSellStg)
        │      → 기존 back_static.py 함수 재사용
        │
        ├─ 2. 시장 데이터 로드
        │      → GetMoneytopQuery() 재사용
        │
        ├─ 3. 거래 시뮬레이션 (단일 프로세스)
        │      → BackEngine의 CodeLoop 로직 추출
        │      → 멀티프로세스 대신 단일 프로세스로 실행
        │
        ├─ 4. 결과 집계
        │      → GetResultDataframe() 재사용
        │      → GetBackResult() 재사용
        │
        └─ 5. 반환: {'df_tsg': df, 'metrics': {...}}
```

**장점**:
- 기존 코드 재사용 최대화
- 단일 프로세스로 간단한 디버깅
- ICOS 반복에 최적화된 구조

**단점**:
- 멀티코어 활용 불가 (속도 저하)
- 일부 코드 추출 필요

### 5.2 방안 B: 기존 BackTest 프로세스 연동

**개념**: 기존 BackTest 프로세스를 호출하고 결과를 수신

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    방안 B: 기존 BackTest 연동                               │
└─────────────────────────────────────────────────────────────────────────────┘

_execute_backtest()
    │
    ├─ 1. 임시 큐 생성
    │      tempQ = Queue()
    │
    ├─ 2. BackTest 프로세스 시작
    │      Process(target=BackTest, args=(..., tempQ)).start()
    │
    ├─ 3. 결과 대기
    │      result = tempQ.get(timeout=...)
    │
    └─ 4. 결과 반환
           return {'df_tsg': result['df_tsg'], ...}
```

**장점**:
- 기존 시스템 완전 재사용
- 멀티코어 활용 가능

**단점**:
- 프로세스 간 통신 복잡
- 동기화 문제 가능성
- 반복마다 프로세스 생성 오버헤드

### 5.3 방안 C: 하이브리드 접근

**개념**: 첫 번째 백테스트는 기존 시스템, 이후 반복은 SyncBacktestRunner

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    방안 C: 하이브리드 접근                                  │
└─────────────────────────────────────────────────────────────────────────────┘

반복 0 (초기):
    │
    └─→ 기존 BackTest 시스템 사용
        │
        └─→ df_tsg 저장 (캐싱)
            │
            └─→ 분석 파이프라인 결과 활용

반복 1+ (이후):
    │
    └─→ SyncBacktestRunner 사용 (필터 적용된 조건식)
        │
        └─→ 빠른 단일 프로세스 실행
```

**장점**:
- 초기 백테스트는 정확하고 빠름 (멀티코어)
- 이후 반복은 가벼움

**단점**:
- 두 시스템 유지 필요
- 결과 일관성 검증 필요

---

## 6. 권장 해결 방안 (방안 A 상세)

### 6.1 SyncBacktestRunner 구현 계획

```python
# 파일: backtester/iterative_optimizer/backtest_sync.py

class SyncBacktestRunner:
    """ICOS용 동기식 백테스트 러너.

    기존 BackEngine 로직을 단일 프로세스로 실행합니다.
    ICOS 반복 최적화에서 빠른 피드백을 위해 설계되었습니다.
    """

    def __init__(self, params: dict, windowQ=None):
        """초기화.

        Args:
            params: 백테스트 파라미터
                - gubun: 'S'(주식) or 'C'(업비트) or 'CF'(바이낸스)
                - startday, endday, starttime, endtime
                - betting, avgtime
                - dict_cn: 종목코드 → 종목명 맵
            windowQ: UI 메시지 큐 (선택)
        """
        self.params = params
        self.windowQ = windowQ

    def run(self, buystg: str, sellstg: str) -> dict:
        """백테스트 실행.

        Returns:
            {
                'df_tsg': DataFrame,  # 거래 상세
                'metrics': dict,      # 성과 지표
                'execution_time': float,
            }
        """
        start_time = time.time()

        # 1. 조건식 컴파일
        buystg_code, indistg_code = GetBuyStg(
            buystg, self.params['gubun'],
            self.params['avgtime'],
            'backtest'
        )
        sellstg_code = GetSellStg(
            sellstg, self.params['gubun'],
            self.params['avgtime'],
            'backtest'
        )

        # 2. 데이터 로드
        # ... (기존 코드 활용)

        # 3. 거래 시뮬레이션
        list_tsg = self._simulate_trades(buystg_code, sellstg_code)

        # 4. 결과 집계
        df_tsg = self._create_result_dataframe(list_tsg)
        metrics = self._calculate_metrics(df_tsg)

        return {
            'df_tsg': df_tsg,
            'metrics': metrics,
            'execution_time': time.time() - start_time,
        }
```

### 6.2 구현 단계

```
Phase 1: 기초 구조 (1-2일)
├─ SyncBacktestRunner 클래스 스켈레톤
├─ 조건식 컴파일 연동 (GetBuyStg, GetSellStg)
└─ 기본 파라미터 처리

Phase 2: 데이터 로드 (1일)
├─ GetMoneytopQuery 연동
├─ 틱/분봉 데이터 로드
└─ dict_cn 활용

Phase 3: 거래 시뮬레이션 (2-3일)
├─ BackEngine의 CodeLoop 로직 추출
├─ 단일 프로세스 실행 구조
└─ 거래 상세 데이터 생성

Phase 4: 결과 집계 (1일)
├─ GetResultDataframe 연동
├─ GetBackResult 연동
└─ metrics 계산

Phase 5: 통합 테스트 (1-2일)
├─ ICOS runner.py와 연동
├─ 기존 백테스트 결과와 비교 검증
└─ 성능 측정
```

### 6.3 runner.py 수정 계획

```python
# 파일: backtester/iterative_optimizer/runner.py

def _execute_backtest(self, buystg: str, sellstg: str, params: dict) -> dict:
    """백테스트 실행.

    ★ 수정된 구현 (SyncBacktestRunner 연동)
    """
    try:
        # SyncBacktestRunner 사용
        from .backtest_sync import SyncBacktestRunner

        runner = SyncBacktestRunner(
            params=self.backtest_params,
            windowQ=self.windowQ,
        )

        result = runner.run(buystg, sellstg)

        self._log(f'백테스트 완료: {result["metrics"]["trade_count"]}건 거래, '
                  f'{result["execution_time"]:.1f}초 소요')

        return result

    except Exception as e:
        self._log(f'백테스트 오류: {str(e)}', level='error')
        return {
            'df_tsg': pd.DataFrame(),
            'metrics': {'total_profit': 0, ...},
            'execution_time': 0,
            'error': str(e),
        }
```

---

## 7. 구현 완성도 현황

### 7.1 모듈별 완성도

| 모듈 | 파일 | 라인 | 상태 | 완성도 | 우선순위 |
|------|------|------|------|--------|----------|
| config | config.py | 309 | ✅ 완료 | 100% | - |
| data_types | data_types.py | 81 | ✅ 완료 | 100% | - |
| runner | runner.py | 583 | ⚠️ 부분 | 70% | **P0** |
| backtest_sync | backtest_sync.py | ~300 | ⚠️ 미완성 | 20% | **P0** |
| analyzer | analyzer.py | 720 | ✅ 완료 | 100% | - |
| filter_generator | filter_generator.py | 505 | ✅ 완료 | 100% | - |
| condition_builder | condition_builder.py | 521 | ✅ 완료 | 100% | - |
| storage | storage.py | 537 | ✅ 완료 | 100% | - |
| comparator | comparator.py | 494 | ✅ 완료 | 100% | - |
| convergence | convergence.py | 482 | ✅ 완료 | 100% | - |
| optimization/* | - | ~2000 | ⚠️ 부분 | 50% | P2 |

### 7.2 핵심 TODO

```
★ P0 (필수 - ICOS 작동을 위해):
[ ] SyncBacktestRunner._simulate_trades() 구현
[ ] SyncBacktestRunner._create_result_dataframe() 구현
[ ] runner._execute_backtest() 연동

P1 (중요 - 품질 향상):
[ ] 백테스트 결과 검증 (기존 시스템과 비교)
[ ] 에러 처리 강화
[ ] 로깅 개선

P2 (권장 - 기능 확장):
[ ] GridSearchOptimizer 완성
[ ] GeneticOptimizer 완성
[ ] BayesianOptimizer 완성
[ ] WalkForwardValidator 완성
```

---

## 8. UI 연동 현황

### 8.1 Alt+I 다이얼로그 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Alt+I 다이얼로그 구조                                    │
│            파일: ui/set_dialog_icos.py                                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ 백테스팅 결과 분석 / ICOS 설정                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ┌───────────────────────────────┐ ┌───────────────────────────────┐        │
│ │ 백테스팅 결과 분석            │ │ ICOS 반복 최적화              │        │
│ │ (✅ 완전 작동)                 │ │ (⚠️ 설정만 가능)               │        │
│ ├───────────────────────────────┤ ├───────────────────────────────┤        │
│ │ [✓] 분석 활성화               │ │ [✓] ICOS 활성화               │        │
│ │                               │ │                               │        │
│ │ Phase A: 필터 분석            │ │ 최대 반복: [5  ]              │        │
│ │ [✓] 필터 효과                 │ │ 수렴 기준: [5  ] %            │        │
│ │ [✓] 최적 임계값               │ │                               │        │
│ │ [✓] 필터 조합                 │ │ 최적화 기준:                  │        │
│ │ [✓] 안정성 검증               │ │ [수익금    ▼]                │        │
│ │ [✓] 조건식 생성               │ │                               │        │
│ │                               │ │ 최적화 방법:                  │        │
│ │ ML 분석                       │ │ [그리드서치 ▼]               │        │
│ │ [✓] 위험도 예측               │ │                               │        │
│ │ [✓] 특성 중요도               │ │ ⚠️ "백테스트" 유형에서만      │        │
│ │ 모드: [학습 ▼]               │ │    작동합니다.                │        │
│ │                               │ │                               │        │
│ │ Phase C: 세그먼트 분석        │ │                               │        │
│ │ [✓] 세그먼트 분석             │ │                               │        │
│ │ [✓] Optuna 최적화             │ │                               │        │
│ │ [✓] 템플릿 비교               │ │                               │        │
│ │ [✓] 자동 저장                 │ │                               │        │
│ └───────────────────────────────┘ └───────────────────────────────┘        │
│                                                                             │
│ [저장] [로딩] [기본값 복원]                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 설정 파일 구조

```json
// 파일: _database/icos_analysis_config.json
{
  "analysis": {
    "enabled": true,
    "filter_analysis": {
      "filter_effects": true,
      "optimal_thresholds": true,
      "filter_combinations": true,
      "filter_stability": true,
      "generate_code": true
    },
    "ml_analysis": {
      "risk_prediction": true,
      "feature_importance": true,
      "mode": "train"
    },
    "segment_analysis": {
      "enabled": true,
      "optuna": true,
      "template_compare": true,
      "auto_save": true
    },
    "notification": {
      "level": "detailed"
    }
  },
  "icos": {
    "enabled": true,           // ★ 활성화 시 ICOS 모드로 전환
    "max_iterations": 5,
    "convergence_threshold": 5.0,
    "optimization_metric": "profit",
    "optimization_method": "grid_search"
  }
}
```

---

## 9. 테스트 계획

### 9.1 단위 테스트

```python
# tests/test_icos_sync_backtest.py

def test_sync_backtest_runner_initialization():
    """SyncBacktestRunner 초기화 테스트."""
    params = {
        'gubun': 'S',
        'startday': 20240101,
        'endday': 20241231,
        # ...
    }
    runner = SyncBacktestRunner(params)
    assert runner.params == params

def test_sync_backtest_runner_execution():
    """SyncBacktestRunner 실행 테스트."""
    # ... 실제 데이터로 테스트

def test_icos_iteration_cycle():
    """ICOS 단일 반복 사이클 테스트."""
    # 백테스트 → 분석 → 필터 생성 → 조건식 빌드
```

### 9.2 통합 테스트

```
1. 기존 백테스트와 결과 비교
   - 동일한 조건식, 동일한 기간
   - df_tsg 컬럼 및 값 비교
   - metrics 값 비교 (허용 오차 1% 이내)

2. ICOS 반복 사이클 테스트
   - 3회 반복 실행
   - 각 반복에서 조건식 변경 확인
   - 수렴 판정 확인

3. UI 연동 테스트
   - Alt+I 설정 변경 후 저장/로딩
   - ICOS 활성화 후 백테스트 버튼 클릭
   - 로그 출력 확인
```

---

## 10. 결론 및 다음 단계

### 10.1 현재 상태 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| UI 설정 | ✅ 완료 | Alt+I 다이얼로그 작동 |
| 설정 저장/로딩 | ✅ 완료 | JSON 파일 저장 |
| ICOS 활성화 감지 | ✅ 완료 | `_check_icos_enabled()` |
| ICOS 프로세스 시작 | ✅ 완료 | `_run_icos_backtest()` |
| 분석 모듈 | ✅ 완료 | ResultAnalyzer |
| 필터 생성 | ✅ 완료 | FilterGenerator |
| 조건식 빌드 | ✅ 완료 | ConditionBuilder |
| 수렴 판정 | ✅ 완료 | ConvergenceChecker |
| **백테스트 연동** | ❌ **미완성** | `_execute_backtest()` 스켈레톤 |

### 10.2 즉시 실행 필요 작업

```
★ 핵심 작업 (ICOS 작동을 위한 필수 조건):

1. SyncBacktestRunner 완성
   - 거래 시뮬레이션 로직 구현
   - 결과 DataFrame 생성
   - 성과 지표 계산

2. runner._execute_backtest() 연동
   - SyncBacktestRunner 호출
   - 결과 반환 구조 맞추기

3. 통합 테스트
   - 기존 백테스트 결과와 비교
   - ICOS 반복 사이클 검증
```

### 10.3 예상 일정

```
Phase 1: SyncBacktestRunner 완성 ─────── 3-5일
Phase 2: runner 연동 및 테스트 ─────── 1-2일
Phase 3: UI 개선 및 문서화 ─────────── 1일
─────────────────────────────────────────
총 예상: 5-8일
```

---

## 부록 A: 코드 참조

### A.1 핵심 파일 위치

| 파일 | 경로 | 주요 함수/클래스 |
|------|------|-----------------|
| 백테스트 버튼 | ui/ui_button_clicked_sd.py | sdbutton_clicked_02() |
| ICOS 체크 | ui/ui_button_clicked_sd.py | _check_icos_enabled() |
| ICOS 실행 | ui/ui_button_clicked_sd.py | _run_icos_backtest() |
| ICOS 프로세스 | ui/ui_button_clicked_icos.py | _run_icos_process() |
| ICOS 오케스트레이터 | backtester/iterative_optimizer/runner.py | IterativeOptimizer |
| 동기식 러너 | backtester/iterative_optimizer/backtest_sync.py | SyncBacktestRunner |
| 기존 BackTest | backtester/backtest.py | BackTest, Total |
| 분석 파이프라인 | backtester/analysis_enhanced/runner.py | RunEnhancedAnalysis() |

### A.2 설정 파일

| 파일 | 경로 | 용도 |
|------|------|------|
| ICOS 설정 | _database/icos_analysis_config.json | ICOS 및 분석 설정 |
| ICOS 결과 | _database/icos_results/ | 반복 결과 저장 |

---

**문서 작성 완료**: 2026-01-15
**작성자**: Claude Code Assistant
**브랜치**: feature/iterative-condition-optimizer
