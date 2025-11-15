## 코드맵(최소 모듈 구성)

- `research/data_loader.py`
  - load_symbol_df(db_path, symbol, start, end) -> pd.DataFrame
  - make_panel(df_dict: symbol→df, freq: 'tick'|'min') -> pd.DataFrame/polars
- `research/features.py`
  - build_features(df, config) -> df_feat
  - minimal set: 수익률/변동성/오더북 불균형/체결강도 추세(윈도우 20~120)
- `research/labeling.py`
  - make_return_label(df, horizon_s, fee_bps) -> y_cls(0/1), y_reg
- `research/backtest_wrapper.py`
  - run_backtest(params, universe, period, costs) -> metrics(dict)
  - required metrics: sharpe, cagr, mdd, winrate, avg_pl, turnover
- `research/optimize_condition.py`
  - search_with_optuna(objective_cfg, n_trials, n_jobs) -> study/best
- `research/models/tabular.py`
  - train_xgb(X, y, cfg) -> booster, metrics
  - infer_xgb(booster, X) -> proba/pred
- `research/eval.py`
  - walk_forward_eval(pipeline, splits, costs) -> report(dict)
  - generate_report(artifacts_dir, metrics, plots)
- `research/train_tabular.py`
  - end-to-end: load → feature → label → split → train → eval → report
- `research/conf/`
  - hydra yaml: paths/db, symbols, dates, costs, feature/label params, CV, search space

### 상호작용 다이어그램(요약)
- CLI → `train_tabular.py`
  → `data_loader` → `features` → `labeling`
  → `tabular.train` → `eval.walk_forward_eval`
  → (옵션) `optimize_condition`가 backtest 래퍼 호출

### 기존 자산 연결
- 백테스터: `backtester/optimiz_genetic_algorithm.py`, `backtester/backtest.py` 등
- 가이드: [Back_Testing_Guideline_Tick.md](mdc:Guideline/Back_Testing_Guideline_Tick.md), [Back_Testing_Guideline_Min.md](mdc:Idea/Back_Testing_Guideline_Min.md)
