## 조건식 연구를 위한 ML/DL 통합 설계안 (STOM)

본 문서는 STOM의 주식 틱/분 DB와 기존 백테스터를 활용해 조건식 연구를 머신러닝/딥러닝 기반으로 고도화하는 실무형 설계안입니다. 목표는 조건식 변수의 수익 기여를 체계적으로 분석하고, GPU 자원을 활용해 빠르게 탐색·최적화·해석하는 것입니다.

- 참고 문서: [Back_Testing_Guideline_Tick.md](mdc:Guideline/Back_Testing_Guideline_Tick.md), [Back_Testing_Guideline_Min.md](mdc:Guideline/Back_Testing_Guideline_Min.md)
- 조건 예시: `Condition/` 하위의 `condition*.md`
- 데이터 구조 개요: [Condition_Survey_Idea.md](mdc:Idea/Condition_Survey_Idea.md)

---

### 1) 목표와 핵심 전략

- 조건식 변수(윈도우, 임계값, 조합)의 “수익률 영향”을 정량화
  - ML 해석(Feature importance, SHAP, PDP/ICE)으로 변수 민감도와 상호작용 파악
- 백테스트-최적화 루프 자동화
  - `백테스터(기존)` ←→ `최적화 엔진(Optuna/GA/CMA-ES)` ←→ `실험관리(MLflow/W&B)`
- 딥러닝 기반 시퀀스 모델로 “조건이 잡지 못하는” 시그널 보강
  - TCN/LSTM/Transformer로 시계열 창(window) 입력 → 목표(Label) 예측 → 정책(진입/청산) 연계
- 현실적 평가: 거래비용·슬리피지·체결확률 반영, 워크포워드/퍼지드 CV로 과최적화 억제

---

### 2) 데이터 로더 설계 (SQLite, 테이블=종목코드)

- 공통 스키마로 통합 로딩: 테이블명(종목코드) 단위로 기간 필터링, 컬럼 표준화
- `index`는 `yyyymmddhhmmss` → 타임스탬프로 변환, 정렬·중복 제거
- 틱/분 데이터 모두 지원. 분 데이터는 리샘플/집계 함수로 일관 처리

```python
# 예시 스니펫: 단일 종목, 기간 로딩 (개념 예시)
import sqlite3
import pandas as pd


def load_symbol_df(db_path: str, symbol: str, start: str, end: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM '{symbol}' WHERE index BETWEEN {start} AND {end} ORDER BY index ASC"  # index: yyyymmddhhmmss
    df = pd.read_sql_query(query, conn)
    conn.close()
    # 타입 변환 및 시간 처리
    df['ts'] = pd.to_datetime(df['index'], format='%Y%m%d%H%M%S')
    df = df.drop_duplicates(subset=['ts']).set_index('ts')
    return df
```

---

### 3) 레이블링(타깃) 설계

- 단순 수익률 레이블
  - 분류: \(y = 1_{(r_{t\to t+H} - c) > 0}\), 회귀: \(r_{t\to t+H} - c\) (c=거래비용)
  - H: 10초/30초/1분/5분 등 다중 수평선(horizon)
- 트리플 배리어(Lopez de Prado)
  - 상·하 수익 임계 + 최대 보유기간 → 이벤트 종료 시점/결과 산출
- 이벤트 기반 레이블
  - 조건식 트리거 시점만 샘플링(메타라벨링), 비트리거 구간은 다운샘플/무시
- 클래스 불균형 대책: class weight, focal loss, 임계값 이동, 커스텀 유틸리티(Sharpe 가중)

---

### 4) 데이터 분할과 검증

- 워크포워드 검증(rolling window): 훈련→검증→테스트 순차 이동
- 퍼지드 K-Fold + 엠바고(embargo)로 누수 방지 (인접 구간 상관 제거)
- 종목 간 스플릿: 종목 홀드아웃 테스트 세트 구성(범용성 확인)

---

### 5) 특징 공학(Feature Engineering)

- 기본 가격·거래 특성: 수익률(틱/분), 로그수익률, 고저폭, ATR, 변동성(실현변동성), 거래대금·체결강도 추세
- 호가/잔량 마이크로구조: 오더북 불균형(매수·매도 잔량/합), 스프레드, 체결 편향, 라운드 피겨 근접도
- 모멘텀/역추세: 이동평균, RSI, Stoch, MACD 등 [TA-Lib](mdc:utility/TA_Lib-0.4.25-cp311-cp311-win_amd64.whl) 활용
- 윈도우 파생: 최근 N틱/분 집계(평균, 표준편차, 최대·최소, 누적합, 상승/하락 카운트)
- 정규화: 종목별 스케일 표준화(특히 호가/잔량), 리샘플/정렬 일관성 유지
- 누수 방지: 미래 정보 사용 금지, 시점별 피처는 철저히 과거 데이터만

---

### 6) 모델링 전략(탭уляр + 시퀀스)

- 빠른 베이스라인(탭уляр)
  - LightGBM/XGBoost GPU로 중요도·성능 빠른 확인, Grid/BO 탐색과 궁합 좋음
- 시퀀스 딥러닝(Pytorch/Lightning)
  - 입력: [batch, window, features]
  - TCN(Temporal ConvNet), LSTM/GRU, Transformer(로컬 어텐션/Informer류)
  - 손실: BCEWithLogits(분류), MSE/Huber(회귀), 비용·턴오버 패널티를 커스텀 로스에 포함 가능
- 멀티헤드 예측: 상승확률 p와 기대수익 r을 동시 예측 → 정책에서 결합

```python
# 예시 스니펫: 간단 LSTM 분류 골격(개념 예시)
import torch
import torch.nn as nn


class LSTMClassifier(nn.Module):
    def __init__(self, num_features: int, hidden_size: int = 128):
        super().__init__()
        self.lstm = nn.LSTM(input_size=num_features, hidden_size=hidden_size, batch_first=True)
        self.head = nn.Linear(hidden_size, 1)

    def forward(self, x):  # x: [B, T, F]
        out, _ = self.lstm(x)
        logits = self.head(out[:, -1])
        return logits
```

---

### 7) 조건식 최적화(블랙박스) + 메타모델

- 블랙박스 최적화
  - 목적함수: 백테스터 실행 → 샤프/수익률-드로우다운 페널티 최대화
  - 도구: Optuna(TPE), CMA-ES, Differential Evolution, 유전알고리즘(기존 `backtester/optimiz_genetic_algorithm.py` 연계)
- 메타모델(대체모델)
  - 파라미터→성과(Sharpe, CAGR, MDD)를 예측하는 회귀모델을 학습하여 탐색 가속화
  - 중요 파라미터/상호작용 파악 및 범위 축소에 활용

```python
# 예시 스니펫: Optuna로 조건 파라미터 탐색(개념 예시)
import optuna


def objective(trial):
    params = {
        'ma_short': trial.suggest_int('ma_short', 5, 40),
        'ma_long': trial.suggest_int('ma_long', 20, 120),
        'rsi_th_buy': trial.suggest_int('rsi_th_buy', 20, 50),
        'rsi_th_sell': trial.suggest_int('rsi_th_sell', 50, 80),
    }
    # NOTE: 실제 구현 시 기존 백테스터 엔진을 함수로 래핑하여 호출
    # (수익률, 샤프 비율 등 성과 지표 계산)
    sharpe = run_backtest_and_return_sharpe(params)  # 사용자 구현 필요
    return sharpe

study = optuna.create_study(direction='maximize')
# study.optimize(objective, n_trials=200)
```

---

### 8) 해석: 변수 영향과 규칙화

- SHAP(트리/탭уляр), Gradient SHAP/Integrated Gradients(딥러닝)
- PDP/ICE로 단일 변수/쌍 변수의 민감도 곡선 시각화
- 규칙 압축: Symbolic Regression(PySR)로 해석 가능한 조건식 자동 도출(선택)

---

### 9) 오프라인 정책 평가 및 리스크 반영

- 거래비용·슬리피지·체결확률·최소호가·호가단위 반영
- 포지션 제한·손익 제한·최대 드로우다운 제한 정책 시뮬레이션
- OOS 기간(미사용 기간/종목) 성능 검증, 라이트닝 메트릭(Sharpe, Sortino, Calmar, Turnover 등)

---

### 10) 실험 관리·재현성

- MLflow/W&B로 파라미터·지표·아티팩트(그래프/모델) 기록
- 시드 고정, 환경 캡처(requirements, CUDA info), 설정은 YAML(Hydra)로 관리
- 결과 리포트 템플릿 자동 생성(표·그래프)

---

### 11) GPU 활용 지침(Windows)

- 탭уляр: XGBoost/LightGBM GPU(‘gpu_hist’, ‘device=gpu’)로 수십~수백 배 가속 가능
- 딥러닝: PyTorch CUDA, Mixed Precision(amp) 활성화, 큰 배치는 Gradient Accumulation 사용
- 데이터: Dataloader pinned memory, prefetch, Arrow/Feather 캐시로 I/O 병목 감소

---

### 12) 기존 백테스터와의 연결 방식

1. 백테스터 래퍼 함수 정의
   - 입력: 조건 파라미터 dict, 심볼 리스트, 기간, 수수료/슬리피지 등
   - 출력: 성과 지표 dict(Sharpe, CAGR, MDD, 승률, 평균손익, Turnover)
2. 최적화 루프에서 래퍼 호출(병렬 가능 시 멀티프로세싱)
3. 모델 예측과 정책 연계
   - 예측 p/r을 임계값 정책으로 변환 → 백테스터로 승격

---

### 13) 추천 디렉터리(연구 코드)

```
research/
  data_loader.py       # SQLite 로더/전처리
  features.py          # 피처 생성(틱/분 공용)
  labeling.py          # 레이블링(단순/트리플 배리어/메타)
  backtest_wrapper.py  # 기존 엔진 호출 래퍼
  optimize_condition.py# Optuna/GA/CMA-ES
  models/
    tabular.py         # XGB/LGBM 래퍼
    sequence.py        # LSTM/TCN/Transformer
  train_tabular.py     # 탭уляр 학습 스크립트
  train_sequence.py    # 딥러닝 학습 스크립트
  eval.py              # 워크포워드/리포팅
  conf/                # Hydra YAML
```

---

### 14) 빠른 시작(권장 프로빙 시나리오)

1. 탭уляр 베이스라인(XGBoost GPU)
   - 피처: 모멘텀/변동성/체결강도/오더북 불균형(최근 20~120틱/분 집계)
   - 레이블: H=1,3,5분 수익률>비용 분류
   - 목적: AUC/PR-AUC 및 중요도·SHAP으로 “유효 변수” 1차 선별
2. 블랙박스 최적화(조건 파라미터)
   - 목적함수: Walk-Forward Sharpe – λ·Turnover – μ·MDD
   - 탐색: Optuna 200~500 trials(조기중단)
3. 시퀀스 모델(LSTM/TCN)
   - 입력 창: 60~300틱/분, 피처 50~200개
   - 정책: p>τ AND r_pred>0 → 진입, 미충족 시 패스

---

### 15) 산출물·리포팅 템플릿

- 테이블: 기간별 Sharpe/CAGR/MDD/Turnover, 트레이드 수, 승률, 기대손익
- 그래프: 에쿼티 커브, 드로우다운, 중요도/SHAP Summary, PDP/ICE, 파라미터-Sharpe 맵
- 마크다운 보고서 자동 생성 → `Condition/` 내 후보 조건식 초안 반영

---

### 16) 구현 로드맵(요약)

- 주차1: 로더·라벨링·CV·기본 피처·탭уляр 베이스라인, SHAP/PDP
- 주차2: 백테스터 래퍼 + Optuna 탐색, 보고서 자동화
- 주차3: 시퀀스 모델 1차(창/피처 스윕), 정책 연계
- 주차4: 정교화(비용/체결확률/제약), 종목 홀드아웃·OOS, 최종 규칙화

---

### 17) 주의사항(핵심 체크리스트)

- 데이터 누수 방지(파생·라벨·정규화 모두 과거 한정)
- 평가는 반드시 워크포워드·OOS 포함, 단일 구간 최적화 금지
- 비용·슬리피지·호가단위·체결확률 보수적으로 가정
- 높은 샤프보다 재현성과 안정성(턴오버·거래횟수·슬리피지 민감도)을 우선

---

필요 시 위 설계를 기반으로 `research/` 스켈레톤 코드와 백테스터 래퍼를 바로 추가 구현해 드리겠습니다.
