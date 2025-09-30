## 최적화/탐색 설계

### 목적함수
- 목표: `Sharpe - λ·Turnover - μ·MDD` 최대화 (λ, μ는 설정값)
- 평가: 워크포워드 평균 성과 사용(각 폴드 backtest → 평균)

### 탐색 엔진
- 기본: Optuna(TPE) + 조기중단
- 보완: CMA-ES/GA(필요 시) — 탐색 종료 후 국소 탐색(반경 축소)

### 검색 공간 예시
- `ma_short: 5~40`, `ma_long: 20~120`, `rsi_buy: 20~50`, `rsi_sell: 50~80`
- `vol_window: 20~120`, `imbalance_th: 0.1~0.6`

### 제약/유효성
- `ma_short < ma_long`
- Turnover 상한, 트레이드 수 하한(통계적 유의성)

### 병렬화
- n_jobs=4~8, 각 트라이얼 별 심볼 샘플링 시드 고정

### 로깅
- MLflow: trial params, metrics, artifacts(에쿼티, 파라미터-샤프 맵)

### 산출물
- best_params.json, best_report.md, search_space.yaml
