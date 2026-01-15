# ICOS 구현 실행 계획

> **작성일**: 2026-01-15
> **목적**: ICOS 핵심 문제 해결 및 구현 완성을 위한 실행 계획
> **참조 문서**: 20260115_ICOS_Pipeline_Analysis_and_Integration_Plan.md

---

## 1. 핵심 문제 요약

### 1.1 현재 상태

**ICOS가 작동하지 않는 이유**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ★ 핵심 병목 지점 ★                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  IterativeOptimizer._execute_backtest()                        │
│  파일: backtester/iterative_optimizer/runner.py:370-404        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 현재 구현:                                               │   │
│  │   return {                                              │   │
│  │       'df_tsg': pd.DataFrame(),  # 빈 DataFrame        │   │
│  │       'metrics': {...0값들...},  # 모두 0               │   │
│  │   }                                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  결과: ICOS가 실행되어도 실제 백테스트가 수행되지 않음         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 영향 체인

```
빈 df_tsg 반환
      │
      ▼
ResultAnalyzer.analyze() → 빈 데이터 분석 → 무의미한 결과
      │
      ▼
FilterGenerator.generate() → 필터 생성 실패 또는 잘못된 필터
      │
      ▼
ConditionBuilder.build() → 조건식 개선 없음
      │
      ▼
★ ICOS 목표 달성 불가 ★
```

---

## 2. 해결 방안: SyncBacktestRunner 구현

### 2.1 구현 범위

```
backtester/iterative_optimizer/backtest_sync.py
├─ SyncBacktestRunner 클래스
│  ├─ __init__(params, windowQ)
│  ├─ run(buystg, sellstg) → dict
│  ├─ _compile_conditions() - 조건식 컴파일
│  ├─ _load_market_data() - 시장 데이터 로드
│  ├─ _simulate_trades() - 거래 시뮬레이션 ★ 핵심
│  ├─ _create_result_dataframe() - 결과 DataFrame 생성
│  └─ _calculate_metrics() - 성과 지표 계산
```

### 2.2 재사용할 기존 코드

| 기능 | 기존 파일 | 함수/클래스 |
|------|----------|------------|
| 조건식 컴파일 | backtester/back_static.py | GetBuyStg(), GetSellStg() |
| 데이터 쿼리 | backtester/back_static.py | GetMoneytopQuery() |
| 결과 DataFrame | backtester/back_static.py | GetResultDataframe() |
| 성과 지표 | backtester/back_static.py | GetBackResult() |
| 거래 시뮬레이션 | backtester/backengine_*.py | CodeLoop() 로직 참조 |

### 2.3 구현 순서

```
Step 1: 조건식 컴파일 연동 (0.5일)
────────────────────────────────────
├─ GetBuyStg() 호출
├─ GetSellStg() 호출
└─ indistg 처리

Step 2: 데이터 로드 (0.5일)
────────────────────────────────────
├─ GetMoneytopQuery() 호출
├─ pd.read_sql() 실행
└─ 틱/분봉 데이터 구조 맞추기

Step 3: 거래 시뮬레이션 (2-3일) ★ 핵심
────────────────────────────────────
├─ BackEngine.CodeLoop() 분석
├─ 단일 프로세스 버전 구현
├─ 조건식 평가 로직
├─ 매수/매도 시뮬레이션
└─ 거래 목록 생성

Step 4: 결과 집계 (0.5일)
────────────────────────────────────
├─ GetResultDataframe() 호출
├─ GetBackResult() 호출
└─ metrics 구조 맞추기

Step 5: runner.py 연동 (0.5일)
────────────────────────────────────
├─ _execute_backtest() 수정
├─ SyncBacktestRunner 호출
└─ 예외 처리
```

---

## 3. 상세 구현 가이드

### 3.1 SyncBacktestRunner 클래스 골격

```python
# backtester/iterative_optimizer/backtest_sync.py

"""ICOS용 동기식 백테스트 러너.

기존 멀티프로세스 백테스팅 시스템을 단일 프로세스로 실행하여
ICOS 반복 최적화에서 빠른 피드백을 제공합니다.

작성일: 2026-01-15
브랜치: feature/iterative-condition-optimizer
"""

import time
import pandas as pd
from typing import Dict, Optional, Tuple, List

# 기존 모듈 재사용
from backtester.back_static import (
    GetBuyStg,
    GetSellStg,
    GetMoneytopQuery,
    GetResultDataframe,
    GetBackResult,
)


class SyncBacktestRunner:
    """ICOS용 동기식 백테스트 러너.

    Attributes:
        params: 백테스트 파라미터
        windowQ: UI 메시지 큐 (선택)

    Example:
        >>> runner = SyncBacktestRunner(params, windowQ)
        >>> result = runner.run(buystg, sellstg)
        >>> df_tsg = result['df_tsg']
        >>> metrics = result['metrics']
    """

    def __init__(self, params: dict, windowQ=None):
        """초기화.

        Args:
            params: 백테스트 파라미터
                - gubun: 'S'(주식) or 'C'(업비트) or 'CF'(바이낸스)
                - startday, endday: 시작/종료일 (int, YYYYMMDD)
                - starttime, endtime: 시작/종료시간 (int, HHMM)
                - betting: 베팅금액 (int)
                - avgtime: 평균값틱수 (int)
                - dict_cn: 종목코드 → 종목명 맵 (dict)
                - code_list: 종목코드 리스트 (list)
            windowQ: UI 메시지 큐 (선택)
        """
        self.params = params
        self.windowQ = windowQ

        # 내부 상태
        self.buystg_code = None
        self.sellstg_code = None
        self.indistg_code = None
        self.df_market = None

    def run(self, buystg: str, sellstg: str) -> dict:
        """백테스트 실행.

        Args:
            buystg: 매수 조건식 (조건식 이름 또는 코드)
            sellstg: 매도 조건식 (조건식 이름 또는 코드)

        Returns:
            {
                'df_tsg': DataFrame,  # 거래 상세
                'metrics': {
                    'total_profit': float,
                    'win_rate': float,
                    'trade_count': int,
                    'profit_factor': float,
                    'max_drawdown': float,
                },
                'execution_time': float,
                'error': Optional[str],
            }
        """
        start_time = time.time()

        try:
            # 1. 조건식 컴파일
            self._compile_conditions(buystg, sellstg)

            # 2. 시장 데이터 로드
            self._load_market_data()

            # 3. 거래 시뮬레이션
            list_tsg = self._simulate_trades()

            # 4. 결과 DataFrame 생성
            df_tsg = self._create_result_dataframe(list_tsg)

            # 5. 성과 지표 계산
            metrics = self._calculate_metrics(df_tsg)

            return {
                'df_tsg': df_tsg,
                'metrics': metrics,
                'execution_time': time.time() - start_time,
                'error': None,
            }

        except Exception as e:
            return {
                'df_tsg': pd.DataFrame(),
                'metrics': {
                    'total_profit': 0,
                    'win_rate': 0,
                    'trade_count': 0,
                    'profit_factor': 0,
                    'max_drawdown': 0,
                },
                'execution_time': time.time() - start_time,
                'error': str(e),
            }

    def _compile_conditions(self, buystg: str, sellstg: str):
        """조건식 컴파일.

        기존 GetBuyStg, GetSellStg 함수를 활용합니다.
        """
        gubun = self.params['gubun']
        avgtime = self.params['avgtime']

        # 매수 조건식 컴파일
        self.buystg_code, self.indistg_code = GetBuyStg(
            buystg, gubun, avgtime, 'backtest'
        )

        # 매도 조건식 컴파일
        self.sellstg_code = GetSellStg(
            sellstg, gubun, avgtime, 'backtest'
        )

    def _load_market_data(self):
        """시장 데이터 로드.

        기존 GetMoneytopQuery 함수를 활용합니다.
        """
        # TODO: 구현
        pass

    def _simulate_trades(self) -> List[tuple]:
        """거래 시뮬레이션.

        BackEngine의 CodeLoop 로직을 단일 프로세스로 실행합니다.

        Returns:
            거래 목록 (list of tuples)
        """
        # TODO: 구현 - BackEngine.CodeLoop() 참조
        list_tsg = []
        return list_tsg

    def _create_result_dataframe(self, list_tsg: List[tuple]) -> pd.DataFrame:
        """결과 DataFrame 생성.

        기존 GetResultDataframe 함수를 활용합니다.
        """
        # TODO: 구현
        return pd.DataFrame()

    def _calculate_metrics(self, df_tsg: pd.DataFrame) -> dict:
        """성과 지표 계산.

        기존 GetBackResult 함수를 활용합니다.
        """
        if df_tsg.empty:
            return {
                'total_profit': 0,
                'win_rate': 0,
                'trade_count': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
            }

        # TODO: GetBackResult 호출 및 결과 변환
        return {
            'total_profit': 0,
            'win_rate': 0,
            'trade_count': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
        }
```

### 3.2 runner.py 수정 내용

```python
# backtester/iterative_optimizer/runner.py

# 기존 _execute_backtest() 수정

def _execute_backtest(self, buystg: str, sellstg: str, params: dict) -> dict:
    """백테스트 실행.

    SyncBacktestRunner를 사용하여 단일 프로세스로 백테스트를 실행합니다.

    Args:
        buystg: 매수 조건식
        sellstg: 매도 조건식
        params: 백테스트 파라미터

    Returns:
        {
            'df_tsg': DataFrame,
            'metrics': dict,
            'execution_time': float,
        }
    """
    try:
        from .backtest_sync import SyncBacktestRunner

        self._log(f'백테스트 시작: {buystg[:50]}...')

        runner = SyncBacktestRunner(
            params=self.backtest_params,
            windowQ=self.windowQ,
        )

        result = runner.run(buystg, sellstg)

        if result.get('error'):
            self._log(f'백테스트 오류: {result["error"]}', level='error')
        else:
            self._log(
                f'백테스트 완료: {result["metrics"]["trade_count"]}건, '
                f'수익: {result["metrics"]["total_profit"]:,.0f}원, '
                f'{result["execution_time"]:.1f}초'
            )

        return result

    except Exception as e:
        self._log(f'백테스트 실행 실패: {str(e)}', level='error')
        return {
            'df_tsg': pd.DataFrame(),
            'metrics': {
                'total_profit': 0,
                'win_rate': 0,
                'trade_count': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
            },
            'execution_time': 0,
            'error': str(e),
        }
```

---

## 4. 검증 계획

### 4.1 단계별 검증

```
Step 1 검증: 조건식 컴파일
─────────────────────────────
테스트 코드:
    buystg_code, indistg = GetBuyStg('test', 'S', 10, 'backtest')
    assert buystg_code is not None
    assert callable(buystg_code)  # 또는 컴파일된 코드 확인

Step 2 검증: 데이터 로드
─────────────────────────────
테스트 코드:
    df = runner._load_market_data()
    assert not df.empty
    assert '종목코드' in df.columns

Step 3 검증: 거래 시뮬레이션
─────────────────────────────
테스트 코드:
    list_tsg = runner._simulate_trades()
    assert isinstance(list_tsg, list)
    # 기존 BackTest 결과와 비교

Step 4 검증: 결과 일치
─────────────────────────────
테스트 코드:
    # 동일 조건으로 기존 BackTest 실행
    # SyncBacktestRunner 결과와 비교
    # 오차율 1% 이내 확인
```

### 4.2 통합 테스트

```python
# tests/test_icos_integration.py

def test_icos_full_cycle():
    """ICOS 전체 사이클 테스트."""
    from backtester.iterative_optimizer import (
        IterativeOptimizer,
        IterativeConfig,
    )

    # 설정
    config = IterativeConfig(
        enabled=True,
        max_iterations=3,
        convergence_threshold=5.0,
    )

    # 파라미터
    backtest_params = {
        'gubun': 'S',
        'startday': 20240101,
        'endday': 20240131,
        # ...
    }

    # 실행
    optimizer = IterativeOptimizer(config, backtest_params=backtest_params)
    result = optimizer.run(
        buystg='테스트조건',
        sellstg='테스트매도',
        backtest_params=backtest_params
    )

    # 검증
    assert result.success or result.error_message
    assert result.num_iterations >= 1
    assert result.final_buystg is not None
```

---

## 5. 예상 일정

| 단계 | 작업 | 예상 소요 | 산출물 |
|------|------|----------|--------|
| 1 | 조건식 컴파일 연동 | 0.5일 | _compile_conditions() |
| 2 | 데이터 로드 연동 | 0.5일 | _load_market_data() |
| 3 | 거래 시뮬레이션 | 2-3일 | _simulate_trades() |
| 4 | 결과 집계 | 0.5일 | _create_result_dataframe(), _calculate_metrics() |
| 5 | runner.py 연동 | 0.5일 | _execute_backtest() 수정 |
| 6 | 통합 테스트 | 1일 | 테스트 코드 |
| **합계** | | **5-6일** | |

---

## 6. 리스크 및 완화 방안

### 6.1 기술적 리스크

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| BackEngine 로직 복잡성 | 구현 지연 | 핵심 로직만 추출, 단순화 |
| 데이터 구조 불일치 | 결과 오류 | 기존 함수 최대 재사용 |
| 메모리 사용량 | 성능 저하 | 데이터 청킹, 불필요한 복사 제거 |
| 기존 시스템과 결과 차이 | 신뢰성 문제 | 철저한 비교 테스트 |

### 6.2 완화 전략

```
1. 점진적 구현
   - 각 단계별로 검증 후 다음 단계 진행
   - 문제 발생 시 빠른 롤백 가능

2. 기존 코드 최대 활용
   - GetBuyStg, GetSellStg 등 검증된 함수 재사용
   - 새로운 로직은 최소화

3. 비교 테스트 자동화
   - 동일 조건에서 기존 BackTest와 결과 비교
   - CI/CD에 통합
```

---

## 7. 성공 기준

### 7.1 기능적 기준

- [ ] ICOS 활성화 시 실제 백테스트 실행됨
- [ ] df_tsg가 유효한 거래 데이터를 포함함
- [ ] metrics가 정확한 성과 지표를 반환함
- [ ] 반복마다 조건식이 개선됨
- [ ] 수렴 조건 도달 시 정상 종료됨

### 7.2 품질 기준

- [ ] 기존 BackTest 결과와 1% 이내 오차
- [ ] 메모리 사용량 기존 대비 50% 이하
- [ ] 단일 반복 실행 시간 30초 이내
- [ ] 예외 발생 시 적절한 에러 메시지

### 7.3 사용성 기준

- [ ] Alt+I에서 ICOS 활성화 후 백테스트 버튼 클릭으로 실행
- [ ] 로그 창에 ICOS 진행 상황 표시
- [ ] 완료 후 최종 조건식 저장/표시

---

## 8. 다음 단계 (구현 시작)

### 8.1 즉시 실행 작업

```bash
# 1. backtest_sync.py 파일 생성/업데이트
# 2. SyncBacktestRunner 클래스 구현 시작
# 3. 조건식 컴파일 연동부터 진행
```

### 8.2 첫 번째 커밋 목표

```
feat(icos): SyncBacktestRunner 조건식 컴파일 연동

## 구현 내용
- SyncBacktestRunner 클래스 기본 구조
- _compile_conditions() 메서드 구현
- GetBuyStg, GetSellStg 연동

## 다음 단계
- _load_market_data() 구현
- _simulate_trades() 구현
```

---

**문서 작성 완료**: 2026-01-15
**작성자**: Claude Code Assistant
**브랜치**: feature/iterative-condition-optimizer
