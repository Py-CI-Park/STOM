## 실험관리/평가

### 관리
- MLflow: params/metrics/artifacts 기록, run_name=cfg.hash
- Hydra: `conf/`에서 경로/데이터/피처/레이블/탐색/평가 설정 통합

### 평가
- 워크포워드 3분할 + OOS 1분할
- 메트릭: Sharpe, Sortino, Calmar, MDD, Turnover, Winrate, Trades
- 비용/슬리피지 반영, 민감도 분석(비용±25%)

### 리포트 자동화
- 표: 폴드별/평균 메트릭
- 그래프: 에쿼티 커브, 드로우다운, 파라미터-샤프 맵
- 요약: 베스트 파라미터, 리스크 포인트, 재현성 체크

### 재현성
- 시드 고정, 버전 핀(패키지/드라이버), 데이터 스냅샷 경로 기록
