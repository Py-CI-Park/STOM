## 모델 베이스라인(최소)

### Tabular (권장 시작점)
- 모델: XGBoost GPU(`tree_method=gpu_hist`)
- 입력: 최소 피처셋(모멘텀/변동성/체결강도/오더북 불균형)
- 출력: 상승확률 p (분류)
- 임계값: F1/PR-AUC 최대 또는 유틸리티 기반 임계값(거래비용 반영)

#### 핵심 하이퍼파라미터
- `max_depth, learning_rate, n_estimators, subsample, colsample_bytree`

### Sequence (선택)
- LSTM(1~2 layer, hidden 128), 입력 창 60~300, AMP 활용
- 정책: `p>τ AND expected_r>0` 시 진입

### 해석
- 중요도/SHAP summary, PDP/ICE로 임계값 감도 확인

### 산출물
- `models/tabular.pkl`, `reports/feature_importance.png`, `reports/shap_summary.png`
