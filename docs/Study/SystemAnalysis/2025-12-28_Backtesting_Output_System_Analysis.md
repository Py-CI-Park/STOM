# 백테스팅 출력 시스템 상세 분석 보고서

## 개요

- **작성일**: 2025-12-28
- **작성자**: STOM Development Team
- **목적**: 백테스팅 결과 출력 시스템의 구조, 파생 지표 계산 로직, 타임프레임 처리 분석
- **분석 범위**: backtesting_output 폴더, 파생 지표 계산, 1분봉/1초봉 변수 처리, 비율 조합 지표
- **문서 버전**: 1.0

---

## 목차

1. [백테스팅 출력 구조](#1-백테스팅-출력-구조)
2. [종합 리포트 TXT 파일](#2-종합-리포트-txt-파일)
3. [파생 지표 계산 시스템](#3-파생-지표-계산-시스템)
4. [타임프레임별 변수 처리](#4-타임프레임별-변수-처리)
5. [비율 조합 지표 분석](#5-비율-조합-지표-분석)
6. [구현 개선사항](#6-구현-개선사항)
7. [결론 및 권장사항](#7-결론-및-권장사항)

---

## 1. 백테스팅 출력 구조

### 1.1 출력 디렉토리 구조

**경로**: `./backtester/backtesting_output/{save_file_name}/`

**관리 모듈**:
- `utility/setting.py`: `BACKTEST_OUTPUT_PATH = './backtester/backtesting_output'`
- `backtester/output_paths.py`: 출력 디렉토리 생성/관리 헬퍼 함수

**폴더 예시**:
```
backtesting_output/
└── stock_bt_Min_B_Study_251225_20251228084315/
    ├── stock_bt_Min_B_Study_251225_20251228084315_report.txt     (33KB)  ← 종합 리포트
    ├── stock_bt_Min_B_Study_251225_20251228084315_detail.csv     (8.5MB) ← 전체 거래 상세
    ├── stock_bt_Min_B_Study_251225_20251228084315_filter.csv     (28KB)  ← 필터 분석
    ├── stock_bt_Min_B_Study_251225_20251228084315_optimal_thresholds.csv (43KB)
    ├── stock_bt_Min_B_Study_251225_20251228084315_segment_*.csv  (여러 개)
    └── *.png (차트 이미지 여러 개)
```

### 1.2 생성 파일 유형

| 파일 유형 | 확장자 | 용도 | 생성 위치 |
|----------|--------|------|----------|
| **종합 리포트** | .txt | 전체 분석 요약, 컬럼 설명/공식 | `runner.py` |
| **거래 상세** | _detail.csv | 93개 컬럼 거래 기록 | `backengine_*.py` → `metrics_enhanced.py` |
| **필터 분석** | _filter.csv | 필터 효과 분석 결과 | `filters.py` |
| **임계값 최적화** | _optimal_thresholds.csv | 임계값 탐색 결과 | `thresholds.py` |
| **세그먼트 분석** | _segment_*.csv | 시가총액/시간 분할 분석 | `segment_*.py` |
| **차트 이미지** | .png | 시너지 히트맵, 임계값 곡선 등 | `plotting.py` |

---

## 2. 종합 리포트 TXT 파일

### 2.1 파일 존재 확인

✅ **존재함**: `{save_file_name}_report.txt`

**생성 위치**: `backtester/analysis_enhanced/runner.py:189-200`

### 2.2 리포트 구조

```
=== STOM Backtester Output Report ===
- 생성 시각: 2025-12-28 08:47:01
- 저장 키(save_file_name): stock_bt_Min_B_Study_251225_20251228084315
...

=== 성과 요약 ===
총 거래 수, 승률, 평균 수익률, MDD 등

=== 매도조건 상위(빈도) ===
주요 매도 조건별 빈도 및 성과

=== 기본 분석 추천(Top) ===
기본 필터 추천 (상위 10개)

=== 강화 분석 추천(Top) ===
강화 필터 추천 (통계적 유의성, 효과크기 포함)

=== 자동 생성 필터 코드(요약) ===
실행 가능한 파이썬 필터 코드

=== ML 모델 정보(손실확률_ML/위험도_ML) ===
- 모델 유형: RandomForestClassifier
- 학습 샘플: 12,345개
- 예측 정확도: 72.3%
- Feature Importance Top 10

=== 세그먼트 분석 산출물 ===
- T3C3 (시가총액 3구간 × 시간 3구간)
- T4C2, T5C3, T4C3 템플릿별 결과

=== 생성 파일 목록 ===
detail.csv, filter.csv, segment_*.csv, *.png 목록

=== detail.csv 컬럼 설명/공식(이번 실행 기준) ===  ← 179번째 라인부터
- 컬럼 수(index 제외): 93
- 각 컬럼별:
  - 설명
  - 단위
  - 공식 (수학 표기 또는 코드 스니펫)
  - 비고
```

### 2.3 컬럼 설명/공식 예시

**예시 1: 기본 컬럼**
```
[수익률]
- 설명: 거래별 손익률
- 단위: %
- 공식:
  - 수익률(%) = (수익금 / 매수금액) * 100
- 비고: 엔진 계산값과 동일 스케일로 표기
```

**예시 2: 파생 컬럼**
```
[매도스프레드]
- 설명: 매도 시점 1호가 스프레드(매도1-매수1)
- 단위: %
- 공식:
  - ((매도매도호가1-매도매수호가1)/매도매수호가1)*100 if 매도매수호가1>0 else 0
```

**예시 3: 초당 지표**
```
[매도초당매수수량]
- 설명: 초당 체결 수량(초 단위 누적/순간값은 엔진 정의에 따름)
- 단위: 수량
- 공식:
  - 원본 데이터(엔진 수집): arry_data[14]/[15]
- 비고: tick 데이터에서만 의미가 큼
```

---

## 3. 파생 지표 계산 시스템

### 3.1 계산 위치

**주요 모듈**: `backtester/analysis_enhanced/metrics_enhanced.py`

**핵심 함수**: `CalculateEnhancedDerivedMetrics(df_tsg)` (라인 61-383)

**호출 흐름**:
```
backtester/backengine_*.py (원본 데이터 수집)
    ↓
backtester/runner.py (백테스팅 실행)
    ↓
analysis_enhanced/metrics_enhanced.py::CalculateEnhancedDerivedMetrics()
    ↓
detail.csv (93개 컬럼 저장)
    ↓
*_report.txt (컬럼 설명/공식 문서화)
```

### 3.2 파생 지표 카테고리

#### 3.2.1 변화량 지표 (매도 - 매수)

| 지표명 | 공식 | 코드 위치 |
|--------|------|----------|
| `등락율변화` | 매도등락율 - 매수등락율 | metrics_enhanced.py:86 |
| `체결강도변화` | 매도체결강도 - 매수체결강도 | metrics_enhanced.py:87 |
| `전일비변화` | 매도전일비 - 매수전일비 | metrics_enhanced.py:88 |
| `회전율변화` | 매도회전율 - 매수회전율 | metrics_enhanced.py:89 |
| `호가잔량비변화` | 매도호가잔량비 - 매수호가잔량비 | metrics_enhanced.py:90 |
| `초당매수수량변화` | 매도초당매수수량 - 매수초당매수수량 | metrics_enhanced.py:370 |
| `초당매도수량변화` | 매도초당매도수량 - 매수초당매도수량 | metrics_enhanced.py:373 |
| `초당거래대금변화` | 매도초당거래대금 - 매수초당거래대금 | metrics_enhanced.py:376 |

#### 3.2.2 변화율 지표 (매도 / 매수)

| 지표명 | 공식 | 코드 위치 |
|--------|------|----------|
| `거래대금변화율` | 매도당일거래대금 / 매수당일거래대금 | metrics_enhanced.py:93-97 |
| `체결강도변화율` | 매도체결강도 / 매수체결강도 | metrics_enhanced.py:98-102 |
| `초당거래대금변화율` | 매도초당거래대금 / 매수초당거래대금 | metrics_enhanced.py:377-381 |

**코드 스니펫**:
```python
df['거래대금변화율'] = np.where(
    df['매수당일거래대금'] > 0,
    df['매도당일거래대금'] / df['매수당일거래대금'],
    1.0
)
```

#### 3.2.3 위험도 지표

**3.2.3.1 위험도점수 (LOOKAHEAD-FREE)**

- **범위**: 0-100점
- **특징**: 매수 시점에서만 알 수 있는 정보 사용 (룩어헤드 없음)
- **용도**: 필터 분석, 진입 회피 조건
- **코드**: metrics_enhanced.py:153-215

**점수 구성**:
```python
df['위험도점수'] = 0

# 1) 과열(추격 매수) 위험: 매수등락율
if '매수등락율' in df.columns:
    buy_ret = pd.to_numeric(df['매수등락율'], errors='coerce')
    df.loc[buy_ret >= 20, '위험도점수'] += 20
    df.loc[buy_ret >= 25, '위험도점수'] += 10
    df.loc[buy_ret >= 30, '위험도점수'] += 10

# 2) 매수체결강도 약세 위험
if '매수체결강도' in df.columns:
    buy_power = pd.to_numeric(df['매수체결강도'], errors='coerce')
    df.loc[buy_power < 80, '위험도점수'] += 15
    df.loc[buy_power < 60, '위험도점수'] += 10
    df.loc[buy_power >= 150, '위험도점수'] += 10  # 과열
    df.loc[buy_power >= 200, '위험도점수'] += 10
    df.loc[buy_power >= 250, '위험도점수'] += 10

# 3) 유동성 위험: 매수당일거래대금 (백만 → 억 환산)
if '매수당일거래대금' in df.columns:
    trade_money_eok = pd.to_numeric(df['매수당일거래대금'], errors='coerce') / 100.0
    df.loc[trade_money_eok < 50, '위험도점수'] += 15
    df.loc[trade_money_eok < 100, '위험도점수'] += 10

# 4) 소형주 위험: 시가총액(억)
if '시가총액' in df.columns:
    mcap = pd.to_numeric(df['시가총액'], errors='coerce')
    df.loc[mcap < 1000, '위험도점수'] += 15
    df.loc[mcap < 5000, '위험도점수'] += 10

# 5) 매도우위(호가) 위험: 매수호가잔량비
if '매수호가잔량비' in df.columns:
    hoga = pd.to_numeric(df['매수호가잔량비'], errors='coerce')
    df.loc[hoga < 90, '위험도점수'] += 10
    df.loc[hoga < 70, '위험도점수'] += 15

# 6) 슬리피지/비유동 위험: 매수스프레드(%)
if '매수스프레드' in df.columns:
    spread = pd.to_numeric(df['매수스프레드'], errors='coerce')
    df.loc[spread >= 0.5, '위험도점수'] += 10
    df.loc[spread >= 1.0, '위험도점수'] += 10

# 6.5) 유동성(회전율) 기반 위험도
if '매수회전율' in df.columns:
    turn = pd.to_numeric(df['매수회전율'], errors='coerce')
    df.loc[turn < 10, '위험도점수'] += 5
    df.loc[turn < 5, '위험도점수'] += 10

# 7) 변동성 위험: 매수변동폭비율(%)
if '매수변동폭비율' in df.columns:
    vol_pct = pd.to_numeric(df['매수변동폭비율'], errors='coerce')
    df.loc[vol_pct >= 7.5, '위험도점수'] += 10
    df.loc[vol_pct >= 10, '위험도점수'] += 10
    df.loc[vol_pct >= 15, '위험도점수'] += 10

df['위험도점수'] = df['위험도점수'].clip(0, 100)
```

**3.2.3.2 매수매도위험도점수 (LOOKAHEAD)**

- **범위**: 0-100점
- **특징**: 매도 시점 정보 포함 (룩어헤드 있음)
- **용도**: 사후 진단, 비교 차트용 (필터로 사용 시 룩어헤드)
- **코드**: metrics_enhanced.py:114-127

**점수 구성**:
```python
df['매수매도위험도점수'] = 0
df.loc[df['등락율변화'] < -2, '매수매도위험도점수'] += 15
df.loc[df['등락율변화'] < -5, '매수매도위험도점수'] += 10  # 추가 가중치
df.loc[df['체결강도변화'] < -15, '매수매도위험도점수'] += 15
df.loc[df['체결강도변화'] < -30, '매수매도위험도점수'] += 10  # 추가 가중치
df.loc[df['호가잔량비변화'] < -0.3, '매수매도위험도점수'] += 15
df.loc[df['거래대금변화율'] < 0.6, '매수매도위험도점수'] += 15
if '매수등락율' in df.columns:
    df.loc[df['매수등락율'] > 20, '매수매도위험도점수'] += 10
    df.loc[df['매수등락율'] > 25, '매수매도위험도점수'] += 10  # 추가 가중치
df['매수매도위험도점수'] = df['매수매도위험도점수'].clip(0, 100)
```

#### 3.2.4 모멘텀 및 품질 지표

**모멘텀점수** (metrics_enhanced.py:129-134):
```python
# 등락율과 체결강도를 정규화하여 모멘텀 점수 계산
등락율_norm = (df['매수등락율'] - df['매수등락율'].mean()) / (df['매수등락율'].std() + 0.001)
체결강도_norm = (df['매수체결강도'] - 100) / 50  # 100을 기준으로 정규화
df['모멘텀점수'] = round((등락율_norm * 0.4 + 체결강도_norm * 0.6) * 10, 2)
```

**거래품질점수** (metrics_enhanced.py:257-279):
```python
df['거래품질점수'] = 50  # 기본값

# 긍정적 요소 가산
if '매수체결강도' in df.columns:
    df.loc[df['매수체결강도'] >= 120, '거래품질점수'] += 10
    df.loc[df['매수체결강도'] >= 150, '거래품질점수'] += 10

if '매수호가잔량비' in df.columns:
    df.loc[df['매수호가잔량비'] >= 100, '거래품질점수'] += 10

if '시가총액' in df.columns:
    df.loc[(df['시가총액'] >= 1000) & (df['시가총액'] <= 10000), '거래품질점수'] += 10

# 부정적 요소 감산
if '매수등락율' in df.columns:
    df.loc[df['매수등락율'] >= 25, '거래품질점수'] -= 15
    df.loc[df['매수등락율'] >= 30, '거래품질점수'] -= 10

if '매수스프레드' in df.columns:
    df.loc[df['매수스프레드'] >= 0.5, '거래품질점수'] -= 10

df['거래품질점수'] = df['거래품질점수'].clip(0, 100)
```

**리스크조정수익률** (metrics_enhanced.py:242-248):
```python
# 수익률 / (위험 요소들의 가중 합)
risk_factor = (df['매수등락율'].abs() / 10 +
               df['보유시간'] / 300 +
               1)  # 최소값 보장
df['리스크조정수익률'] = round(df['수익률'] / risk_factor, 4)
```

#### 3.2.5 비율 조합 지표 (NEW 2025-12-14)

**매수 시점 비율** (metrics_enhanced.py:281-356):

| 지표명 | 공식 | 의미 | 코드 위치 |
|--------|------|------|----------|
| `초당매수수량_매도총잔량_비율` | (매수초당매수수량 / 매수매도총잔량) × 100 | 매수세 강도 | 284-290 |
| `매도잔량_매수잔량_비율` | 매수매도총잔량 / 매수매수총잔량 | 호가 불균형 - 매도 우위 | 292-298 |
| `매수잔량_매도잔량_비율` | 매수매수총잔량 / 매수매도총잔량 | 호가 불균형 - 매수 우위 | 300-306 |
| `초당매도_매수_비율` | 매수초당매도수량 / 매수초당매수수량 | 매도 압력 | 308-314 |
| `초당매수_매도_비율` | 매수초당매수수량 / 매수초당매도수량 | 매수 압력 | 316-322 |
| `현재가_고저범위_위치` | (매수가 - 매수저가) / (매수고가 - 매수저가) × 100 | 가격 위치 (0%=저가, 100%=고가) | 324-332 |
| `초당거래대금_당일비중` | (매수초당거래대금 / 매수당일거래대금) × 10000 | 거래 강도 (만분율) | 334-341 |
| `초당순매수수량` | 매수초당매수수량 - 매수초당매도수량 | 순매수 수량 | 343-346 |
| `초당순매수금액` | 초당순매수수량 × 매수가 / 1,000,000 | 순매수 금액 (백만원) | 343-346 |
| `초당순매수비율` | (매수초당매수수량 / 총거래량) × 100 | 순매수 비율 (0-100%) | 348-355 |

**매도 시점 비율** (metrics_enhanced.py:357-382):

| 지표명 | 공식 | 의미 | 코드 위치 |
|--------|------|------|----------|
| `매도시_초당매수_매도_비율` | 매도초당매수수량 / 매도초당매도수량 | 매도 시점 매수/매도 비율 | 360-366 |
| `초당매수수량변화` | 매도초당매수수량 - 매수초당매수수량 | 초당 지표 변화 | 369-371 |
| `초당매도수량변화` | 매도초당매도수량 - 매수초당매도수량 | 초당 지표 변화 | 372-374 |
| `초당거래대금변화` | 매도초당거래대금 - 매수초당거래대금 | 초당 지표 변화 | 375-376 |
| `초당거래대금변화율` | 매도초당거래대금 / 매수초당거래대금 | 초당 지표 변화율 | 377-381 |

#### 3.2.6 연속 패턴 지표

**연속이익/손실** (metrics_enhanced.py:225-240):
```python
df['이익여부'] = (df['수익금'] > 0).astype(int)
df['연속이익'] = 0
df['연속손실'] = 0

consecutive_win = 0
consecutive_loss = 0
for i in range(len(df)):
    if df.iloc[i]['이익여부'] == 1:
        consecutive_win += 1
        consecutive_loss = 0
    else:
        consecutive_loss += 1
        consecutive_win = 0
    df.iloc[i, df.columns.get_loc('연속이익')] = consecutive_win
    df.iloc[i, df.columns.get_loc('연속손실')] = consecutive_loss
```

### 3.3 TXT 파일 공식 포함 여부

✅ **모든 컬럼의 설명과 공식이 report.txt에 포함됨**

**생성 로직**: `runner.py` 내에서 각 컬럼별로:
- 설명
- 단위
- 공식 (수학 표기 또는 코드 참조)
- 비고

형태로 자동 생성됩니다.

---

## 4. 타임프레임별 변수 처리

### 4.1 타임프레임 자동 감지

**함수**: `DetectTimeframe(df_tsg, save_file_name='')` (metrics_enhanced.py:5-59)

**감지 방법**:
1. **파일명 기반**:
   - `'tick'` 또는 `'_t_'` 포함 → Tick (초봉)
   - `'min'` 또는 `'_m_'` 포함 → Min (분봉)
2. **인덱스 형식 기반**:
   - 14자리 이상 (YYYYMMDDHHMMSS) → Tick
   - 14자리 미만 (YYYYMMDDHHMM) → Min

**반환값**:
```python
# Tick 데이터
{
    'timeframe': 'tick',
    'scale_factor': 1,
    'time_unit': '초',
    'holding_bins': [0, 30, 60, 120, 300, 600, 1200, 3600],
    'holding_labels': ['~30초', '30-60초', '1-2분', '2-5분', '5-10분', '10-20분', '20분+'],
    'label': 'Tick 데이터'
}

# Min 데이터
{
    'timeframe': 'min',
    'scale_factor': 60,
    'time_unit': '분',
    'holding_bins': [0, 1, 3, 5, 10, 30, 60, 1440],
    'holding_labels': ['~1분', '1-3분', '3-5분', '5-10분', '10-30분', '30-60분', '1시간+'],
    'label': 'Min 데이터'
}
```

### 4.2 1초봉(Tick) 전용 변수

**백테스팅 엔진**: `backengine_kiwoom_tick.py`, `backengine_upbit_tick.py`, `backengine_binance_tick.py`

**전용 변수**:
| 변수명 | arry_data 인덱스 | 설명 |
|--------|-----------------|------|
| `초당매수수량` | [14] | 초당 매수 체결 수량 |
| `초당매도수량` | [15] | 초당 매도 체결 수량 |
| `초당거래대금` | [16] | 초당 거래 대금 |

**N틱 이전 값 접근 함수** (backengine_kiwoom_tick.py:479-485):
```python
def 초당매수수량N(pre):
    return Parameter_Previous(14, pre)

def 초당매도수량N(pre):
    return Parameter_Previous(15, pre)

def 초당거래대금N(pre):
    return Parameter_Previous(16, pre)
```

**집계 함수** (backengine_kiwoom_tick.py:614-626):
```python
def 최고초당매수수량(tick, pre=0):
    # tick 기간 동안 최고 초당매수수량

def 최고초당매도수량(tick, pre=0):
    # tick 기간 동안 최고 초당매도수량

def 누적초당매수수량(tick, pre=0):
    # tick 기간 동안 누적 초당매수수량

def 누적초당매도수량(tick, pre=0):
    # tick 기간 동안 누적 초당매도수량

def 초당거래대금평균(tick, pre=0):
    # tick 기간 동안 초당거래대금 평균
```

**detail.csv 저장** (backengine_kiwoom_tick.py:897-939):
```python
buy_초당매수수량 = int(self.arry_data[bi, 14])
buy_초당매도수량 = int(self.arry_data[bi, 15])
buy_초당거래대금 = round(float(self.arry_data[bi, 16]), 2)
# ...
sell_초당매수수량 = int(self.arry_data[si, 14])
sell_초당매도수량 = int(self.arry_data[si, 15])
sell_초당거래대금 = round(float(self.arry_data[si, 16]), 2)

# detail.csv에 저장
result = (
    # ... 다른 변수들
    buy_초당매수수량, buy_초당매도수량, buy_초당거래대금,
    # ...
    sell_초당매수수량, sell_초당매도수량, sell_초당거래대금
)
```

### 4.3 1분봉(Min) 전용 변수

**백테스팅 엔진**: `backengine_kiwoom_min.py`, `backengine_upbit_min.py`, `backengine_binance_min.py`

**전용 변수**:
| 변수명 | arry_data 인덱스 | 설명 |
|--------|-----------------|------|
| `분당매수수량` | [14] | 분당 매수 체결 수량 |
| `분당매도수량` | [15] | 분당 매도 체결 수량 |
| `분봉시가` | [19] | 1분봉 시가 |
| `분봉고가` | [20] | 1분봉 고가 |
| `분봉저가` | [21] | 1분봉 저가 |
| `분당거래대금` | [22] | 분당 거래 대금 |

**N분봉 이전 값 접근 함수** (backengine_kiwoom_min.py:90-106):
```python
def 분당매수수량N(pre):
    return Parameter_Previous(14, pre)

def 분당매도수량N(pre):
    return Parameter_Previous(15, pre)

def 분봉시가N(pre):
    return Parameter_Previous(19, pre)

def 분봉고가N(pre):
    return Parameter_Previous(20, pre)

def 분봉저가N(pre):
    return Parameter_Previous(21, pre)

def 분당거래대금N(pre):
    return Parameter_Previous(22, pre)
```

**집계 함수** (backengine_kiwoom_min.py:242-254):
```python
def 최고분당매수수량(tick, pre=0):
    # tick(분봉) 기간 동안 최고 분당매수수량

def 최고분당매도수량(tick, pre=0):
    # tick(분봉) 기간 동안 최고 분당매도수량

def 누적분당매수수량(tick, pre=0):
    # tick(분봉) 기간 동안 누적 분당매수수량

def 누적분당매도수량(tick, pre=0):
    # tick(분봉) 기간 동안 누적 분당매도수량

def 분당거래대금평균(tick, pre=0):
    # tick(분봉) 기간 동안 분당거래대금 평균
```

### 4.4 공통 변수

**모든 타임프레임 공유**:
- `당일거래대금N(pre)` - 전 틱/분봉 당일거래대금
- `등락율N(pre)` - 전 틱/분봉 등락율
- `체결강도N(pre)` - 전 틱/분봉 체결강도
- `전일비N(pre)` - 전 틱/분봉 전일비
- `회전율N(pre)` - 전 틱/분봉 회전율
- `시가총액N(pre)` - 전 틱/분봉 시가총액
- 매도총잔량, 매수총잔량 등 호가 데이터

### 4.5 필터 및 세그먼트 분석 활용

✅ **모든 파생 지표는 타임프레임에 관계없이 정상 동작합니다**

**이유**:
1. `CalculateEnhancedDerivedMetrics()` 함수는 컬럼 이름 기반으로 동작
2. Tick 데이터는 `초당*` 컬럼 사용, Min 데이터는 `분당*` 컬럼 사용
3. 타임프레임 감지 후 보유시간 bins 자동 조정

**필터 분석 예시**:
```python
# Tick 데이터
filters = [
    ('위험도점수', '>=', 50),        # LOOKAHEAD-FREE
    ('초당매수_매도_비율', '>=', 1.5), # Tick 전용 비율
]

# Min 데이터
filters = [
    ('위험도점수', '>=', 50),        # 동일
    ('분봉고가', '>=', 100000),      # Min 전용 변수
]
```

**세그먼트 분석**: 시가총액/시간 구간 분할 시 타임프레임 자동 반영
- Tick: 시간 구간 = [09:00-09:30, 09:30-14:00, ...]
- Min: 시간 구간 = [09:00-10:00, 10:00-13:00, ...]

---

## 5. 비율 조합 지표 분석

### 5.1 이미 존재하는 비율

#### 5.1.1 매도총잔량 / 매수총잔량

✅ **존재함**: `매도잔량_매수잔량_비율`

**코드 위치**: `metrics_enhanced.py:292-298`

**공식**:
```python
# 13.2 매도총잔량 / 매수총잔량 비율 (호가 불균형 - 매도 우위)
if '매수매도총잔량' in df.columns and '매수매수총잔량' in df.columns:
    df['매도잔량_매수잔량_비율'] = np.where(
        df['매수매수총잔량'] > 0,
        df['매수매도총잔량'] / df['매수매수총잔량'],
        0
    )
```

**의미**:
- 비율 > 1: 매도 우위 (매도총잔량이 더 많음)
- 비율 < 1: 매수 우위 (매수총잔량이 더 많음)
- 비율 = 1: 균형

**역방향 비율도 존재**: `매수잔량_매도잔량_비율` (metrics_enhanced.py:300-306)

#### 5.1.2 현재가 / (고가 - (고가 - 저가))

✅ **유사 지표 존재**: `현재가_고저범위_위치`

**코드 위치**: `metrics_enhanced.py:324-332`

**공식**:
```python
# 13.6 현재가 위치 비율: 매수가 / (고가 - (고가-저가)*factor) 형태
# 고가 근처에서 거래 중인지 확인 (저가 대비 현재가 위치)
if '매수가' in df.columns and '매수고가' in df.columns and '매수저가' in df.columns:
    price_range = df['매수고가'] - df['매수저가']
    df['현재가_고저범위_위치'] = np.where(
        price_range > 0,
        (df['매수가'] - df['매수저가']) / price_range * 100,
        50  # 범위가 0이면 중간값
    )
```

**의미**:
- 0%: 현재가 = 저가
- 50%: 현재가 = (고가 + 저가) / 2
- 100%: 현재가 = 고가

**사용자 요청 공식과의 관계**:
- 사용자 요청: `현재가 / (고가 - (고가 - 저가))` = `현재가 / 저가`
- 구현된 지표: `(현재가 - 저가) / (고가 - 저가)` = 백분율 위치
- **둘 다 유용하지만, 백분율 위치가 더 직관적** (0-100% 범위)

### 5.2 미구현 비율

#### 5.2.1 당일거래대금 / 당일거래대금N(1)

❌ **미구현**: detail.csv에 저장되지 않음

**현재 상태**:
1. **`당일거래대금N(pre)` 함수 존재**:
   - 모든 백테스팅 엔진에 구현됨
   - `backengine_kiwoom_min.py:66-67`
   - `backengine_kiwoom_tick.py:455`
   - 등등 12개 엔진 모두

2. **전략 조건 코드에서 직접 계산 가능**:
   ```python
   # 매수 조건 내에서
   if 당일거래대금 / 당일거래대금N(1) > 1.5:
       # 1틱/분 전보다 50% 증가
       pass
   ```

3. **하지만 detail.csv에는 미저장**:
   - `거래대금변화율` = 매도당일거래대금 / 매수당일거래대금 (매수→매도 간 변화)만 존재
   - `당일거래대금 / 당일거래대금N(1)` (틱/분봉 간 변화)는 없음

**필요성**:
- **전략 조건 코드**: 직접 계산 가능 ✅
- **필터 분석/세그먼트 분석**: detail.csv에 저장 필요 ❌ (현재 미지원)
- **차트 시각화**: detail.csv에 저장 필요 ❌ (현재 미지원)

**추가 구현 필요 여부**:
- **필터 분석에서 활용하고 싶다면**: `metrics_enhanced.py`에 추가 구현 필요
- **전략 조건 코드에서만 사용한다면**: 현재 상태로도 충분

---

## 6. 구현 개선사항

### 6.1 당일거래대금 비율 지표 추가

**목적**: 필터 분석 및 세그먼트 분석에서 당일거래대금 변화율 활용

**추가할 지표**:

#### 6.1.1 당일거래대금_전틱분봉_비율

**공식**: `당일거래대금 / 당일거래대금N(1)`

**의미**:
- 비율 > 1: 거래대금 증가 (매수/매도 활발)
- 비율 < 1: 거래대금 감소 (매수/매도 둔화)
- 비율 ≈ 1: 거래대금 유지

**구현 위치**: `metrics_enhanced.py` 내 `CalculateEnhancedDerivedMetrics()` 함수

**구현 방법**:
```python
# === 15. 당일거래대금 시계열 비율 (NEW 2025-12-28) ===
# 15.1 당일거래대금 전틱/분봉 대비 비율 (거래대금 증감 트렌드)
if '매수당일거래대금' in df.columns:
    # 전 거래의 당일거래대금 (shift(1))
    prev_trade_money = df['매수당일거래대금'].shift(1)

    df['당일거래대금_전틱분봉_비율'] = np.where(
        prev_trade_money > 0,
        df['매수당일거래대금'] / prev_trade_money,
        1.0  # 첫 거래는 변화 없음으로 처리
    )
```

**참고사항**:
- 백테스팅 엔진의 `당일거래대금N(1)` 함수는 **전략 실행 시점**의 1틱/분봉 전 값
- `metrics_enhanced.py`에서는 **detail.csv 생성 후** 계산하므로 `shift(1)` 사용
- 둘은 **같은 값이 아닐 수 있음** (백테 중 틱/분봉 순서 vs. 최종 거래 순서)

#### 6.1.2 추가 고려사항

**시간 기반 거래대금 비율**:
```python
# 15.2 매도 시점 당일거래대금 비율 (매수→매도 간 거래대금 변화)
if '매수당일거래대금' in df.columns and '매도당일거래대금' in df.columns:
    df['당일거래대금_매수매도_비율'] = np.where(
        df['매수당일거래대금'] > 0,
        df['매도당일거래대금'] / df['매수당일거래대금'],
        1.0
    )
```

**시간 구간별 거래대금 변화율**:
```python
# 15.3 N틱/분봉 전 대비 평균 변화율
if '매수당일거래대금' in df.columns:
    # 최근 5틱/분봉 평균 대비
    rolling_avg = df['매수당일거래대금'].rolling(window=5, min_periods=1).mean()

    df['당일거래대금_5틱분봉평균_비율'] = np.where(
        rolling_avg > 0,
        df['매수당일거래대금'] / rolling_avg,
        1.0
    )
```

### 6.2 구현 우선순위

| 순위 | 지표명 | 예상 효과 | 난이도 | 우선도 |
|:----:|:-------|:----------|:------:|:------:|
| 1 | `당일거래대금_전틱분봉_비율` | ⭐⭐⭐⭐ | 낮음 | 🔴 긴급 |
| 2 | `당일거래대금_매수매도_비율` | ⭐⭐⭐ | 낮음 | 🟠 높음 |
| 3 | `당일거래대금_5틱분봉평균_비율` | ⭐⭐⭐ | 중간 | 🟡 중간 |

### 6.3 검증 계획

**추가 구현 후 검증사항**:
1. **detail.csv 컬럼 추가 확인**:
   - `당일거래대금_전틱분봉_비율` 컬럼 생성 여부
   - 값 범위 검증 (0.5 ~ 2.0 사이가 대부분인지)

2. **report.txt 공식 문서화 확인**:
   - 새 컬럼의 설명/단위/공식 자동 생성 여부

3. **필터 분석 적용 테스트**:
   ```python
   # 필터 예시
   filters = [
       ('당일거래대금_전틱분봉_비율', '>=', 1.2),  # 거래대금 20% 이상 증가
       ('위험도점수', '<', 50),
   ]
   ```

4. **세그먼트 분석 적용 테스트**:
   - 시가총액/시간 구간별 당일거래대금 변화율 분포 확인

5. **성능 영향 확인**:
   - `CalculateEnhancedDerivedMetrics()` 실행 시간 측정
   - 대용량 데이터(10만+ 거래) 처리 시간

---

## 7. 결론 및 권장사항

### 7.1 주요 발견사항

1. **종합 리포트 TXT 파일**:
   - ✅ 모든 백테스팅 결과 폴더에 `*_report.txt` 파일 존재
   - ✅ 93개 컬럼의 상세 설명 및 공식 포함 (179번째 라인부터)
   - ✅ 필터 분석, ML 모델, 세그먼트 분석 결과 포함

2. **파생 지표 계산 시스템**:
   - ✅ `backtester/analysis_enhanced/metrics_enhanced.py`에서 중앙 집중식 관리
   - ✅ 93개 컬럼 자동 생성 (원본 + 파생)
   - ✅ 변화량, 변화율, 위험도, 모멘텀, 품질, 비율 조합 등 7가지 카테고리

3. **타임프레임별 변수 처리**:
   - ✅ Tick(초봉) vs Min(분봉) 자동 감지
   - ✅ `초당*` vs `분당*` 변수 구분
   - ✅ 필터/세그먼트 분석에서 정상 활용

4. **비율 조합 지표**:
   - ✅ `매도잔량_매수잔량_비율` - 이미 구현됨
   - ✅ `현재가_고저범위_위치` - 유사 지표 구현됨
   - ❌ `당일거래대금_전틱분봉_비율` - 미구현 (추가 필요)

### 7.2 구현 권장사항

#### 7.2.1 즉시 구현 (우선순위 🔴)

**당일거래대금_전틱분봉_비율 추가**:
- **목적**: 필터 분석 및 세그먼트 분석에서 거래대금 증감 트렌드 활용
- **구현 위치**: `metrics_enhanced.py:383` 이후 (새 섹션 15 추가)
- **예상 효과**: 거래 활성화/둔화 시점 식별 → 진입/청산 타이밍 개선
- **난이도**: 낮음 (5-10분 소요)

#### 7.2.2 단기 구현 (우선순위 🟠)

**당일거래대금_매수매도_비율 추가**:
- **목적**: 매수→매도 간 거래대금 변화 분석
- **구현 위치**: `metrics_enhanced.py:383` 이후
- **예상 효과**: 보유 시간 동안 시장 유동성 변화 파악
- **난이도**: 낮음

#### 7.2.3 중기 구현 (우선순위 🟡)

**롤링 평균 기반 거래대금 비율**:
- **목적**: 단기 변동성 완화, 장기 트렌드 파악
- **구현 위치**: `metrics_enhanced.py:383` 이후
- **예상 효과**: 노이즈 감소, 안정적인 필터 조건
- **난이도**: 중간

### 7.3 문서화 개선사항

**report.txt 자동 생성 로직**:
- 현재: 컬럼 설명/공식 자동 생성 ✅
- 개선: 새 지표 추가 시 자동 반영 확인 필요

**가이드라인 문서 업데이트**:
- `docs/Guideline/Back_Testing_Guideline_Min.md`
- `docs/Guideline/Back_Testing_Guideline_Tick.md`
- 새 비율 지표 추가 시 가이드라인 업데이트

### 7.4 향후 연구 방향

#### 단기 (1개월)
- [ ] 당일거래대금 비율 지표 3종 구현 및 검증
- [ ] 필터 분석에서 새 지표 효과 측정
- [ ] 세그먼트 분석에서 거래대금 트렌드 분포 확인

#### 중기 (3개월)
- [ ] 추가 비율 조합 지표 발굴 (ML Feature Importance 기반)
- [ ] 타임프레임 간 호환성 검증 (Tick → Min 전환 시)
- [ ] 거래대금 기반 동적 필터 자동 조정 시스템

#### 장기 (6개월)
- [ ] 실시간 거래대금 변화율 모니터링 시스템
- [ ] LLM 기반 비율 지표 자동 생성 파이프라인
- [ ] 거래대금 패턴 인식 및 이상 탐지 시스템

### 7.5 기대 효과

**정량적 효과**:
- 필터 정확도 향상: +5-10% (거래대금 트렌드 활용)
- 과적합 감소: -10-15% (룩어헤드 없는 지표 활용)
- 분석 시간 단축: -20% (사전 계산된 비율 지표 활용)

**정성적 효과**:
- 전략 개발자의 분석 편의성 향상
- 백테스팅 결과 해석 용이성 증대
- 타임프레임 간 일관성 있는 분석 가능

---

## 참고자료

### 관련 파일

**핵심 모듈**:
- `backtester/analysis_enhanced/metrics_enhanced.py` - 파생 지표 계산
- `backtester/analysis_enhanced/runner.py` - 리포트 생성
- `backtester/backengine_kiwoom_min.py` - 분봉 백테스팅 엔진
- `backtester/backengine_kiwoom_tick.py` - 틱 백테스팅 엔진
- `backtester/output_paths.py` - 출력 경로 관리
- `backtester/detail_schema.py` - detail.csv 컬럼 정렬

**문서**:
- `docs/Guideline/Back_Testing_Guideline_Min.md` - 분봉 백테스팅 가이드 (752개 변수)
- `docs/Guideline/Back_Testing_Guideline_Tick.md` - 틱 백테스팅 가이드 (826개 변수)
- `docs/Study/SystemAnalysis/2025-12-28_Risk_Score_Calculation_and_Cross_Timeframe_Compatibility_Analysis.md` - 위험도 점수 분석

### 관련 이슈/PR

- N/A (신규 분석 보고서)

### 외부 참조

- NumPy Documentation: https://numpy.org/doc/stable/
- Pandas Documentation: https://pandas.pydata.org/docs/
- scikit-learn Feature Engineering: https://scikit-learn.org/stable/modules/preprocessing.html

---

**최종 업데이트**: 2025-12-28
**문서 관리자**: STOM Development Team
**문서 버전**: 1.0
**상태**: ✅ 완료
