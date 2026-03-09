# 머신러닝 모델 개선 스터디 (Backtester)

## 목적

- 강화 분석에서 생성되는 `*_ML` 컬럼(예: `손실확률_ML`, `위험도_ML`, `예측매수매도위험도점수_ML`)의 **신뢰도**를 높이고,
  **실거래/자동 필터 적용 시 리스크를 통제**하기 위한 스터디 노트입니다.
- 모델 성능이 낮을 때는 ML 필터를 자동으로 차단(게이트)하여, “겉보기 개선(백테 최적화)”이 실전에서 재현되지 않는 문제를 줄이는 것이 목표입니다.

## 현재 구현 요약(코드 기준)

- **분류(손실확률)**:
  - 타겟: `y = (수익금 <= 0)` (손실=1, 이익=0)
  - 모델: `RandomForestClassifier` + `GradientBoostingClassifier` 앙상블(확률 평균)
  - 불균형 대응:
    - RF: `class_weight='balanced'`
    - GB: `compute_sample_weight('balanced')`를 `fit(..., sample_weight=...)`로 반영
- **회귀(매수매도위험도점수 근사)**:
  - 타겟: `매수매도위험도점수` (룩어헤드 포함 “사후 점수”를 매수 시점 변수로 근사)
  - 모델 후보: `RandomForestRegressor` vs `MLPRegressor` 중 MAE 기준 선택
- **피처 선택 원칙(룩어헤드 방지)**:
  - 매수 시점에 확정 가능한 숫자형 컬럼을 중심으로 선택
  - 결과/사후 컬럼(수익*, 매도*, 변화*, 보유시간 등)은 제외
- **산출 컬럼**:
  - `손실확률_ML` (0~1)
  - `위험도_ML` (0~100, `손실확률_ML*100`)
  - `예측매수매도위험도점수_ML` (0~100)

## 모델 저장/재사용(재현)

- 전략키(`strategy_key`): 매수/매도 조건식 원문을 정규화 후 sha256 해시로 생성
- 저장 위치(예시): `backtester/models/strategies/{strategy_key}/`
  - `latest_ml_bundle.joblib`: 해당 전략키의 최신 번들(재현에 주로 사용)
  - `runs/`: 실행별 번들 누적 보관
  - `strategy_code.txt`: 전략키를 만든 매수/매도 조건식 원문(최초 1회 기록)

## ML 신뢰도 게이트(필터에서 *_ML 사용 조건)

- 기준(기본값): `backtester/back_analysis_enhanced.py`의 `ML_RELIABILITY_CRITERIA`
  - `AUC >= 55%`
  - `F1(macro) >= 50%`
  - `Balanced Accuracy >= 55%`
- 동작:
  - **FAIL(기준 미달)**: 자동 필터 분석/코드 생성에서 `*_ML` 컬럼 **사용 금지**
    - `AnalyzeFilterEffectsEnhanced(..., allow_ml_filters=False)`
    - `GenerateFilterCode(..., allow_ml_filters=False)`
  - **PASS**: `*_ML` 컬럼도 필터 후보로 포함
- 확인 위치:
  - 텔레그램 메시지 `ML 위험도 예측 결과`에 PASS/FAIL 및 기준/사유가 함께 출력
  - `{save_file_name}_report.txt`의 `ML 모델 정보` 섹션에 동일 정보가 출력

## 소요 시간(운영/튜닝)

- `PredictRiskWithML()`은 단계별 타임을 `timing` 딕셔너리로 수집합니다.
  - 예: `total_s`, `train_classifiers_s`, `predict_all_s`, `save_bundle_s`, `load_latest_s` 등
- 텔레그램/리포트에 “총 소요 시간 + 주요 단계(load/train/predict/save)”가 출력됩니다.

## 개선 방향 체크리스트(연구)

### 1) 데이터/검증(가장 중요)

- **시계열 분할**: `TimeSeriesSplit` / Walk-forward로 “미래 구간” 검증(랜덤 분할보다 실전 친화)
- **누수(Leakage) 점검**: 매도 시점/사후 계산 컬럼이 학습 피처로 들어가지 않는지 지속 검증
- **라벨 정의 재검토**: 손실=1 기준(`수익금<=0`)이 적절한지, `수익률` 기준/수수료 반영 등 재정의 가능

### 2) 피처/스키마 관리

- `feature_schema_hash` 기반으로 스키마 변경을 감지하고, 재학습/백업 정책을 명확화
- 결측/이상치 처리 규칙(중앙값/clip/로그변환 등) 정립

### 3) 모델/확률 품질

- **확률 보정(Calibration)**: Platt/Isotonic으로 `손실확률_ML`의 확률 해석 품질 개선
- **임계값 최적화**: “분류 판정 임계값(0.5)”을 전략 목적(손실 회피/수익 극대화)에 맞게 튜닝
- **베이스라인 비교**: Dummy/규칙기반 점수와 비교하여 “실제 개선”인지 확인

### 4) 운영/재현성

- `train` vs `load_latest` 운영 정책 확정(재현성 우선이면 `load_latest` 권장)
- 성능/데이터 분포 변화(드리프트) 감지 지표 추가(AUC 하락, 피처 분포 변화 등)

## 관련 코드 위치

- `backtester/back_analysis_enhanced.py`
  - `PredictRiskWithML()`: 학습/예측/저장 + 타이밍 수집
  - `AssessMlReliability()`, `ML_RELIABILITY_CRITERIA`: 신뢰도 기준/게이트
  - `AnalyzeFilterEffectsEnhanced(..., allow_ml_filters=...)`: ML 필터 포함 여부 제어
  - `GenerateFilterCode(..., allow_ml_filters=...)`: ML 필터 코드 생성 제어
- `backtester/back_static.py`
  - `WriteGraphOutputReport()`: 리포트에 ML 성능/타이밍/게이트/코드 요약 기록

