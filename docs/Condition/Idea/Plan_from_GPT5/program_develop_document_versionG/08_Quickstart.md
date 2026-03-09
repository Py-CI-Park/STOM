## 퀵스타트

1) 설정
- DB 경로/심볼/기간/비용 설정: `research/conf/config.yaml`

2) 베이스라인 실행
```bash
# (예시) 탭уляр 파이프라인
python -m research.train_tabular +experiment=baseline \
  paths.db=./Deep_Data/stock.sqlite \
  data.symbols='["005930","000660"]' \
  data.start=20240101 data.end=20241231 \
  costs.fee_bps=5 costs.slippage_bps=5
```

3) 최적화 실행
```bash
python -m research.optimize_condition n_trials=300 n_jobs=4 \
  search_space=@conf/search_space.yaml \
  period.start=20240101 period.end=20241231
```

4) 리포트 확인
- `artifacts/last_run/` 내 `report.md`, `equity.png`, `sharpe_map.png`

5) 백테스터 검증
- `research/backtest_wrapper.py` 사용, 베스트 파라미터로 워크포워드 재평가

참조: [Condition_Survey_ML_DL_Plan.md](mdc:Idea/Condition_Survey_ML_DL_Plan.md)
