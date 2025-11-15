## 백테스터 래퍼 설계

### 목적
- 조건 파라미터를 입력 받아 내부 백테스터를 호출하고 표준화된 성과 지표를 반환

### 시그니처
```python
run_backtest(
  params: dict,              # 조건 파라미터(ex. MA윈도우, RSI 임계값 등)
  universe: list[str],       # 심볼 목록
  period: dict,              # {start: 'YYYYMMDD', end: 'YYYYMMDD'}
  costs: dict                # {fee_bps: float, slippage_bps: float}
) -> dict                    # {sharpe, cagr, mdd, winrate, avg_pl, turnover}
```

### 구현 포인트
- 기존 엔진 함수/스크립트 래핑: 입력 매핑(params→내부 조건식 변수)
- 비용/슬리피지/체결확률(선택) 반영 옵션
- 예외/타임아웃 처리, 결과 파싱 표준화

### 검증
- 동일 입력 반복 호출 시 ±1% 이내 지표 일치
- 기간/심볼 변환 오류, 빈 데이터 처리

### 사용 예
- Optuna 목적함수 내부에서 호출하여 Sharpe 최적화
- 워크포워드 각 폴드별로 독립 호출 후 평균/분산 집계
