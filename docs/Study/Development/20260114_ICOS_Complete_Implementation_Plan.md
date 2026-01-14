# ICOS 완전 구현 계획서

> **작성일**: 2026-01-14
> **목적**: ICOS(Iterative Condition Optimization System) 핵심 기능 완전 구현
> **브랜치**: `feature/icos-complete-implementation`
> **최종 목표**: 백테스팅 반복 실행을 통한 최적 조건식 자동 발견

---

## 1. 현재 상태 분석

### 1.1 ICOS 모듈 구현 현황

| 파일 | 구현 상태 | 설명 |
|------|----------|------|
| `config.py` | ✅ 완료 | 설정 dataclass 정의 |
| `data_types.py` | ✅ 완료 | 데이터 타입 정의 |
| `analyzer.py` | ⚠️ 부분 | 빈 데이터 시 스킵 |
| `filter_generator.py` | ⚠️ 부분 | 분석 결과 없이 동작 불가 |
| `condition_builder.py` | ⚠️ 부분 | 필터 없이 동작 불가 |
| `comparator.py` | ✅ 완료 | 비교 로직 구현됨 |
| `convergence.py` | ✅ 완료 | 수렴 판정 로직 구현됨 |
| `storage.py` | ✅ 완료 | 저장/로드 구현됨 |
| **`runner.py`** | ❌ **스켈레톤** | **`_execute_backtest()` 미구현** |

### 1.2 핵심 미구현 기능: `_execute_backtest()`

```python
# backtester/iterative_optimizer/runner.py (Lines 370-404)
def _execute_backtest(self, buystg, sellstg, params):
    """백테스트 실행 - 현재 스켈레톤 상태"""

    # TODO: Phase 2에서 기존 백테스팅 시스템과 연동 구현
    self._log("    (스켈레톤: 실제 백테스트 미실행)")

    return {
        'df_tsg': pd.DataFrame(),  # ← 빈 DataFrame 반환!
        'metrics': {
            'total_profit': 0.0,   # ← 더미 메트릭!
            'win_rate': 0.0,
            'trade_count': 0,
            ...
        },
    }
```

**문제점**: 빈 DataFrame 반환 → 분석 불가 → 필터 생성 불가 → 반복 무의미

### 1.3 기존 백테스팅 시스템 구조

```
백테스트 실행 흐름:
┌─────────────────────────────────────────────────────────────────┐
│ ui_button_clicked_sd.py::백테스트_버튼_클릭()                      │
│     ↓                                                           │
│ BackTest 클래스 생성 (backtest.py:258)                           │
│     ↓                                                           │
│ BackTest.Start() - 초기화, 데이터 로드                            │
│     ├─ DB에서 buystg, sellstg 조회                               │
│     ├─ df_mt (기간 데이터) 생성                                   │
│     ├─ arry_bct (보유종목수 배열) 생성                             │
│     └─ beq_list로 백엔진들에 데이터 전송                           │
│     ↓                                                           │
│ Total 프로세스 생성 (backtest.py:18)                              │
│     └─ Total.MainLoop() - 결과 수집 루프                          │
│         ├─ '백테완료' 메시지 수신 (beq → tq)                       │
│         ├─ '백테결과' 메시지 수신 → Report() 호출                   │
│         └─ PltShow() - 텔레그램 전송, 분석 파이프라인               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 핵심 큐 통신 구조

```python
# 주요 큐 (qlist 인덱스)
windowQ   [0]  - 메인 윈도우 UI 업데이트
soundQ    [1]  - 사운드 알림
queryQ    [2]  - 데이터베이스 작업
teleQ     [3]  - 텔레그램 전송
chartQ    [4]  - 차트 업데이트
backQ     [7]  - 백테스팅 입력

# 백테스팅 전용 큐
beq_list  - 백엔진 큐 리스트 (멀티코어 병렬 처리)
bstq_list - 백테스트 통계 큐 리스트
tq        - Total 클래스 통신 큐
```

---

## 2. 개발 목표 및 전략

### 2.1 최종 목표

**백테스팅 → 분석 → 필터 생성 → 조건식 개선 → 재백테스팅 → 수렴 시 종료**

```
┌─────────────────────────────────────────────────────────────────┐
│                    ICOS 완전 자동화 흐름                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [1] 사용자가 Alt+I에서 ICOS 활성화 + 설정                        │
│      ↓                                                          │
│  [2] 백테스트 버튼 클릭                                           │
│      ↓                                                          │
│  [3] ICOS 모드 감지 → IterativeOptimizer.run() 호출              │
│      ↓                                                          │
│  [4] 반복 루프 시작                                               │
│      │                                                          │
│      ├─[4.1] _execute_backtest() - 실제 백테스트 실행            │
│      │       (기존 BackTest/Total 시스템 활용)                    │
│      │                                                          │
│      ├─[4.2] _analyze_result() - 결과 분석                       │
│      │       (손실 패턴, 세그먼트 분석)                            │
│      │                                                          │
│      ├─[4.3] _generate_filters() - 필터 후보 생성                │
│      │       (통계적 유의성 검증)                                  │
│      │                                                          │
│      ├─[4.4] _build_new_condition() - 새 조건식 빌드             │
│      │       (필터를 buystg에 삽입)                               │
│      │                                                          │
│      └─[4.5] _check_convergence() - 수렴 판정                    │
│              (개선율 < 임계값 → 종료)                              │
│      ↓                                                          │
│  [5] 최종 결과 반환 + 텔레그램 알림                                │
│      - 최적화된 buystg                                           │
│      - 반복 기록                                                  │
│      - 개선율 리포트                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 개발 전략

**핵심 원칙**: 기존 코드 최대한 재사용, 최소 변경으로 최대 효과

1. **기존 백테스팅 시스템과 동기식 통합**
   - 멀티프로세스 구조를 유지하되, ICOS에서 동기적으로 결과 대기
   - 새로운 프로세스 생성 대신 기존 큐 구조 활용

2. **점진적 구현**
   - Phase 1: `_execute_backtest()` 핵심 기능 구현
   - Phase 2: UI 분리 (분석 설정 / ICOS 설정)
   - Phase 3: 통합 워크플로우 연결
   - Phase 4: 테스트 및 검증

---

## 3. 상세 구현 계획

### 3.1 Phase 1: `_execute_backtest()` 핵심 구현

#### 3.1.1 접근 방식 선택

**Option A: 동기식 백테스트 실행 (권장)**
- 기존 `backengine_*.py`의 로직을 직접 호출
- 멀티프로세스 대신 단일 프로세스에서 순차 실행
- 장점: 구현 간단, ICOS 루프와 자연스럽게 통합
- 단점: 속도 저하 (멀티코어 미사용)

**Option B: 비동기식 백테스트 실행**
- 기존 BackTest/Total 클래스 재사용
- 큐를 통해 결과 대기
- 장점: 멀티코어 활용
- 단점: 복잡한 동기화 필요

**선택: Option A + 최적화**
- 초기 구현은 동기식으로 시작
- 각 반복당 1회 백테스트만 필요하므로 속도 저하 감수 가능
- 추후 필요시 멀티스레딩 추가

#### 3.1.2 구현 코드 설계

```python
# backtester/iterative_optimizer/runner.py

def _execute_backtest(
    self,
    buystg: str,
    sellstg: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """백테스트 실행 - 실제 구현.

    기존 백테스팅 시스템의 핵심 로직을 직접 호출하여
    동기적으로 백테스트를 실행합니다.
    """
    from backtester.backengine_kiwoom_tick import BackEngine
    from backtester.back_static import GetBackResult, GetResultDataframe, AddMdd

    # 1. 파라미터 추출
    ui_gubun = params.get('ui_gubun', 'S')
    betting = params.get('betting', 1000000)
    startday = params.get('startday')
    endday = params.get('endday')
    starttime = params.get('starttime')
    endtime = params.get('endtime')
    avgtime = params.get('avgtime', 9)

    # 2. 데이터베이스에서 기간 데이터 로드
    db = self._get_backtest_db(ui_gubun, params.get('timeframe', 'tick'))
    df_mt = self._load_period_data(db, startday, endday, starttime, endtime)

    if df_mt.empty:
        self._log("    (데이터 없음)")
        return {'df_tsg': pd.DataFrame(), 'metrics': {}}

    # 3. 백엔진 실행 (동기식)
    engine = BackEngine(
        buystg=buystg,
        sellstg=sellstg,
        betting=betting,
        avgtime=avgtime,
        df_mt=df_mt,
        ui_gubun=ui_gubun,
    )
    list_tsg, arry_bct = engine.run()

    # 4. 결과 데이터프레임 생성
    if not list_tsg:
        return {'df_tsg': pd.DataFrame(), 'metrics': {}}

    df_tsg, df_bct = GetResultDataframe(ui_gubun, list_tsg, arry_bct)

    # 5. 메트릭 계산
    day_count = len(df_mt['일자'].unique())
    arry_tsg = np.array(df_tsg[['보유시간', '매도시간', '수익률', '수익금', '수익금합계']], dtype='float64')
    result = GetBackResult(arry_tsg, arry_bct, betting, ui_gubun, day_count)
    result = AddMdd(arry_tsg, result)

    tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi, mdd, mdd_ = result

    metrics = {
        'total_profit': tsg,
        'win_rate': wr,
        'trade_count': tc,
        'profit_factor': pc / max(mc, 1),
        'max_drawdown': mdd,
        'avg_profit_rate': app,
        'cagr': cagr,
        'tpi': tpi,
    }

    return {
        'df_tsg': df_tsg,
        'metrics': metrics,
        'df_bct': df_bct,
    }
```

#### 3.1.3 BackEngine 동기식 래퍼 클래스

```python
# backtester/iterative_optimizer/backtest_sync.py (신규)

"""
ICOS를 위한 동기식 백테스트 실행기.

기존 멀티프로세스 백테스팅 시스템을 동기적으로 래핑하여
ICOS 반복 루프에서 사용할 수 있게 합니다.
"""

import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List

from utility.setting import (
    DB_STOCK_BACK_TICK, DB_STOCK_BACK_MIN,
    DB_COIN_BACK_TICK, DB_COIN_BACK_MIN,
    DICT_SET,
)
from backtester.back_static import (
    GetMoneytopQuery, GetBackResult, GetResultDataframe, AddMdd
)


class SyncBacktestRunner:
    """동기식 백테스트 실행기.

    ICOS 반복 루프에서 사용하기 위한 동기적 백테스트 실행기입니다.
    기존 백엔진의 핵심 로직을 재사용합니다.
    """

    def __init__(
        self,
        ui_gubun: str = 'S',
        timeframe: str = 'tick',
        dict_cn: Optional[Dict[str, str]] = None,
    ):
        """초기화.

        Args:
            ui_gubun: UI 구분 ('S': 주식, 'C': 코인, 'CF': 코인선물)
            timeframe: 타임프레임 ('tick' 또는 'min')
            dict_cn: 종목코드-종목명 딕셔너리
        """
        self.ui_gubun = ui_gubun
        self.timeframe = timeframe
        self.dict_cn = dict_cn or {}
        self.dict_set = DICT_SET

    def _get_db_path(self) -> str:
        """백테스트 데이터베이스 경로 반환."""
        if self.ui_gubun == 'S':
            return DB_STOCK_BACK_TICK if self.timeframe == 'tick' else DB_STOCK_BACK_MIN
        else:
            return DB_COIN_BACK_TICK if self.timeframe == 'tick' else DB_COIN_BACK_MIN

    def _load_period_data(
        self,
        startday: int,
        endday: int,
        starttime: int,
        endtime: int,
    ) -> pd.DataFrame:
        """기간 데이터 로드."""
        db = self._get_db_path()
        con = sqlite3.connect(db)
        query = GetMoneytopQuery(self.ui_gubun, startday, endday, starttime, endtime)
        df_mt = pd.read_sql(query, con)
        con.close()

        if len(df_mt) > 0:
            df_mt['일자'] = df_mt['index'].apply(lambda x: int(str(x)[:8]))

        return df_mt

    def run(
        self,
        buystg: str,
        sellstg: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """백테스트 실행.

        Args:
            buystg: 매수 조건식
            sellstg: 매도 조건식
            params: 백테스트 파라미터
                - betting: 배팅금액
                - startday: 시작일 (YYYYMMDD)
                - endday: 종료일 (YYYYMMDD)
                - starttime: 시작시간 (HHMMSS)
                - endtime: 종료시간 (HHMMSS)
                - avgtime: 평균값 계산 틱수

        Returns:
            백테스트 결과:
                - df_tsg: 거래 상세 DataFrame
                - metrics: 성과 지표 딕셔너리
                - df_bct: 보유종목수 DataFrame
        """
        betting = params.get('betting', 1000000)
        startday = params.get('startday')
        endday = params.get('endday')
        starttime = params.get('starttime', 90000)
        endtime = params.get('endtime', 153000)
        avgtime = params.get('avgtime', 9)

        # 1. 기간 데이터 로드
        df_mt = self._load_period_data(startday, endday, starttime, endtime)

        if df_mt.empty:
            return self._empty_result()

        # 2. 보유종목수 배열 초기화
        arry_bct = np.zeros((len(df_mt), 3), dtype='float64')
        arry_bct[:, 0] = df_mt['index'].values

        # 3. 백엔진 실행 (동기식)
        list_tsg = self._run_backengine(
            buystg=buystg,
            sellstg=sellstg,
            betting=betting,
            avgtime=avgtime,
            df_mt=df_mt,
            arry_bct=arry_bct,
        )

        if not list_tsg:
            return self._empty_result()

        # 4. 결과 처리
        df_tsg, df_bct = GetResultDataframe(self.ui_gubun, list_tsg, arry_bct)
        day_count = len(df_mt['일자'].unique())

        # 5. 메트릭 계산
        arry_tsg = np.array(
            df_tsg[['보유시간', '매도시간', '수익률', '수익금', '수익금합계']],
            dtype='float64'
        )
        arry_bct_sorted = np.sort(arry_bct, axis=0)[::-1]
        result = GetBackResult(arry_tsg, arry_bct_sorted, betting, self.ui_gubun, day_count)
        result = AddMdd(arry_tsg, result)

        tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi, mdd, mdd_ = result

        metrics = {
            'total_profit': float(tsg),
            'win_rate': float(wr),
            'trade_count': int(tc),
            'avg_trade_count': float(atc),
            'profit_count': int(pc),
            'loss_count': int(mc),
            'profit_factor': float(pc / max(mc, 1)),
            'max_drawdown': float(mdd),
            'avg_profit_rate': float(app),
            'total_profit_rate': float(tpp),
            'avg_hold_time': float(ah),
            'max_hold_count': int(mhct),
            'required_seed': float(seed),
            'cagr': float(cagr),
            'tpi': float(tpi),
            'day_count': int(day_count),
        }

        return {
            'df_tsg': df_tsg,
            'df_bct': df_bct,
            'metrics': metrics,
        }

    def _run_backengine(
        self,
        buystg: str,
        sellstg: str,
        betting: float,
        avgtime: int,
        df_mt: pd.DataFrame,
        arry_bct: np.ndarray,
    ) -> List:
        """백엔진 핵심 로직 실행.

        기존 backengine_*_*.py의 핵심 로직을 동기적으로 실행합니다.
        """
        # 동적 임포트 (순환 임포트 방지)
        if self.ui_gubun == 'S':
            if self.timeframe == 'tick':
                from backtester.backengine_kiwoom_tick import BackEngineKiwoom as Engine
            else:
                from backtester.backengine_kiwoom_min import BackEngineKiwoom as Engine
        else:
            if self.timeframe == 'tick':
                from backtester.backengine_upbit_tick import BackEngineUpbit as Engine
            else:
                from backtester.backengine_upbit_min import BackEngineUpbit as Engine

        # 백엔진 인스턴스 생성 및 실행
        engine = Engine(
            qlist=None,  # 큐 없이 동기 모드
            bstq=None,
            tq=None,
            back_count=1,
            back_queue_num=0,
        )

        # 조건식 설정
        engine.buystg = buystg
        engine.sellstg = sellstg
        engine.betting = betting
        engine.avgtime = avgtime

        # 데이터 설정
        engine.df_mt = df_mt
        engine.arry_bct = arry_bct

        # 백테스트 실행 (동기)
        list_tsg = engine.BackTesting()

        return list_tsg

    def _empty_result(self) -> Dict[str, Any]:
        """빈 결과 반환."""
        return {
            'df_tsg': pd.DataFrame(),
            'df_bct': pd.DataFrame(),
            'metrics': {
                'total_profit': 0.0,
                'win_rate': 0.0,
                'trade_count': 0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
            },
        }
```

### 3.2 Phase 2: Alt+I 다이얼로그 UI 분리

#### 3.2.1 UI 구조 변경

```
┌─────────────────────────────────────────────────────────────────┐
│              백테스팅 상세 설정 (Alt+I)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ┌─── 📊 백테스팅 결과 분석 ────────────────────────────────────┐ │
│ │                                                              │ │
│ │ ☑ 분석 활성화                                                │ │
│ │                                                              │ │
│ │ ┌─ Phase A: 필터 분석 ─────────────────────────────────────┐ │ │
│ │ │ ☑ 필터 효과 분석     ☑ 최적 임계값 분석                    │ │ │
│ │ │ ☐ 필터 조합 분석     ☐ 필터 안정성 분석                    │ │ │
│ │ │ ☑ 코드 생성                                              │ │ │
│ │ └──────────────────────────────────────────────────────────┘ │ │
│ │                                                              │ │
│ │ ┌─ Phase B: ML 분석 ───────────────────────────────────────┐ │ │
│ │ │ ☐ 리스크 예측        ☐ 특성 중요도 분석                    │ │ │
│ │ │ 모드: ○ 학습  ○ 예측                                      │ │ │
│ │ └──────────────────────────────────────────────────────────┘ │ │
│ │                                                              │ │
│ │ ┌─ Phase C: 세그먼트 분석 ─────────────────────────────────┐ │ │
│ │ │ ☑ 세그먼트 분석       ☐ Optuna 최적화                     │ │ │
│ │ │ ☐ 템플릿 비교         ☑ 자동 저장                         │ │ │
│ │ └──────────────────────────────────────────────────────────┘ │ │
│ │                                                              │ │
│ │ 알림 수준: [상세 ▼]                                          │ │
│ │                                                              │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─── 🔄 ICOS (반복 조건식 최적화) ─────────────────────────────┐ │
│ │                                                              │ │
│ │ ☐ ICOS 활성화                                                │ │
│ │                                                              │ │
│ │ 최대 반복 횟수:     [5  ▼]                                    │ │
│ │ 수렴 임계값 (%):    [5  ▼]                                    │ │
│ │ 최적화 지표:        [수익금 ▼]                                │ │
│ │ 최적화 방법:        [Greedy ▼]                                │ │
│ │                                                              │ │
│ │ ⚠️ ICOS 활성화 시 백테스트가 자동으로 반복됩니다.             │ │
│ │                                                              │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                 │
│                    [저장]     [취소]                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.2.2 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `ui/set_dialog_icos.py` | UI 위젯 구조 변경 (분석/ICOS 분리) |
| `ui/ui_button_clicked_icos.py` | 설정 수집/적용 로직 분리 |

### 3.3 Phase 3: 통합 워크플로우

#### 3.3.1 백테스트 버튼 클릭 흐름 수정

```python
# ui/ui_button_clicked_sd.py

def 백테스트_버튼_클릭(self):
    """백테스트 버튼 클릭 핸들러.

    ICOS 활성화 여부에 따라 분기:
    - ICOS OFF: 기존 단일 백테스트 실행
    - ICOS ON: 반복 최적화 워크플로우 실행
    """
    # 조건식 및 파라미터 수집
    buystg, sellstg, params = self._collect_backtest_params()

    # ICOS 설정 확인
    icos_config = get_icos_config(self)

    if icos_config.get('enabled', False):
        # ICOS 모드: 반복 최적화 실행
        self._run_icos_workflow(buystg, sellstg, params, icos_config)
    else:
        # 기존 모드: 단일 백테스트 실행
        self._run_single_backtest(buystg, sellstg, params)

def _run_icos_workflow(self, buystg, sellstg, params, icos_config):
    """ICOS 반복 최적화 워크플로우 실행."""
    from backtester.iterative_optimizer import IterativeOptimizer, IterativeConfig

    # IterativeConfig 생성
    config = IterativeConfig(
        enabled=True,
        max_iterations=icos_config.get('max_iterations', 5),
        convergence_threshold=icos_config.get('convergence_threshold', 5) / 100,
        # ... 기타 설정
    )

    # 오케스트레이터 생성 및 실행
    optimizer = IterativeOptimizer(
        config=config,
        qlist=self.qlist,
        backtest_params=params,
    )

    # 비동기 실행 (별도 스레드)
    self._start_icos_thread(optimizer, buystg, sellstg, params)
```

### 3.4 Phase 4: 테스트 및 검증

#### 3.4.1 테스트 시나리오

| 시나리오 | 설명 | 예상 결과 |
|---------|------|----------|
| T1 | ICOS OFF + 분석 OFF | 기본 백테스트, 이미지 2장 |
| T2 | ICOS OFF + 분석 ON | 기본 백테스트 + 12단계 분석 |
| T3 | ICOS ON + 분석 OFF | 반복 백테스트, 최종 결과만 |
| T4 | ICOS ON + 분석 ON | 반복 백테스트 + 각 반복 분석 |
| T5 | 빈 데이터 | 적절한 에러 메시지 |
| T6 | 조기 수렴 | 임계값 도달 시 정상 종료 |
| T7 | 최대 반복 도달 | 최대 횟수 후 종료 |

---

## 4. 파일 변경 목록

### 4.1 신규 생성

| 파일 | 설명 |
|------|------|
| `backtester/iterative_optimizer/backtest_sync.py` | 동기식 백테스트 실행기 |

### 4.2 수정

| 파일 | 변경 내용 |
|------|----------|
| `backtester/iterative_optimizer/runner.py` | `_execute_backtest()` 실제 구현 |
| `ui/set_dialog_icos.py` | UI 구조 변경 (분석/ICOS 분리) |
| `ui/ui_button_clicked_icos.py` | 설정 수집 로직 분리 |
| `ui/ui_button_clicked_sd.py` | ICOS 워크플로우 연동 |

### 4.3 참조 (수정 없음)

| 파일 | 참조 목적 |
|------|----------|
| `backtester/backtest.py` | 기존 백테스팅 흐름 이해 |
| `backtester/back_static.py` | 유틸리티 함수 재사용 |
| `backtester/backengine_*.py` | 백엔진 로직 참조 |
| `backtester/analysis_enhanced/runner.py` | 분석 파이프라인 연동 |

---

## 5. 개발 일정

| Phase | 작업 | 예상 작업량 |
|-------|------|------------|
| 1 | `_execute_backtest()` 핵심 구현 | 중 |
| 2 | Alt+I UI 분리 | 소 |
| 3 | 통합 워크플로우 연결 | 중 |
| 4 | 테스트 및 검증 | 소 |

---

## 6. 리스크 및 대응

### 6.1 기술적 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 동기식 백테스트 속도 저하 | 중 | 캐싱, 필요시 멀티스레딩 |
| 기존 코드 호환성 | 고 | 철저한 테스트 |
| 메모리 사용량 증가 | 중 | 반복 결과 선택적 저장 |

### 6.2 품질 보장

- 각 Phase별 단위 테스트
- 기존 기능 회귀 테스트
- 코드 리뷰 체크리스트:
  - [ ] 기존 패턴 준수 (한국어 변수명, 큐 통신)
  - [ ] 에러 처리 완비
  - [ ] 로깅 충분
  - [ ] 문서화 완료

---

## 7. 결론

본 계획서는 ICOS의 핵심 미구현 기능인 `_execute_backtest()`를 완전히 구현하고,
Alt+I 다이얼로그를 분석/ICOS 섹션으로 분리하며,
백테스트 버튼 클릭 시 ICOS 워크플로우가 자동으로 실행되도록 하는 것을 목표로 합니다.

**핵심 원칙**:
1. 기존 코드 최대한 재사용
2. 최소 변경으로 최대 효과
3. 점진적 구현 및 검증
4. STOM 프로젝트 코딩 컨벤션 준수

**최종 결과물**:
- 반복적 조건식 개선을 통한 자동 최적화 기능
- 분석 설정과 ICOS 설정의 독립적 제어
- 텔레그램을 통한 진행 상황 및 결과 알림
