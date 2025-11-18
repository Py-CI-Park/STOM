# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Min.md 가이드라인 반영

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
- [Condition - Min MultiIndicator Composite](#condition---min-multiindicator-composite)
  - [전략 개요](#전략-개요)
  - [조건식](#조건식)
  - [최적화 조건식](#최적화-조건식)
  - [조건식 개선 방향 연구](#조건식-개선-방향-연구)
  - [태그](#태그)

## 소개

이 문서는 STOM 주식 자동거래 시스템에서 다중 지표 복합 전략(Multi-Indicator Composite Strategy)을 위한 조건식을 제공합니다. 여러 기술적 지표를 종합적으로 활용하여 신호 신뢰도를 높이는 전략입니다.

## 가이드라인

- 모든 조건식은 Python 스타일의 의사코드로 작성되어 있으며, STOM 백테스터가 인식하는 변수/함수 규칙을 따릅니다.

---

# Condition - Min MultiIndicator Composite

## 전략 개요

다중 지표 복합 전략은 여러 기술적 지표의 합의를 통해 진입합니다:

- 추세 지표: 이동평균 정배열, SAR
- 모멘텀 지표: RSI, MACD, Stochastic
- 변동성 지표: Bollinger Band
- 거래량 지표: 거래량 증가, 체결강도
- 5개 이상의 지표가 매수 신호를 보일 때 진입

## 조건식

### 매수 조건식

```python
# ================================
#  공통 계산 지표
# ================================
# 추세 지표 신호
MA정배열신호          = 1 if (이동평균(5) > 이동평균(20) > 이동평균(60)) else 0
SAR상승신호           = 1 if (현재가 > SAR) else 0

# 모멘텀 지표 신호
RSI상승신호           = 1 if (40 < RSI < 70 and RSI > RSI_N(1)) else 0
MACD골든크로스신호    = 1 if (MACD > MACDS and MACD_N(1) <= MACDS_N(1)) else 0
MACD상승신호          = 1 if (MACD > 0 and MACD > MACD_N(1)) else 0
스토캐스틱상승신호    = 1 if (STOCH_K > STOCH_D and STOCH_K < 80) else 0

# 변동성 지표 신호
볼린저하단반등신호    = 1 if (현재가 > BBL and 현재가N(1) <= BBL) else 0
볼린저중심돌파신호    = 1 if (현재가 > BBM and 현재가N(1) <= BBM) else 0

# 거래량 지표 신호
거래량증가신호        = 1 if (분당거래대금 > 분당거래대금평균(20) * 1.5) else 0
체결강도신호          = 1 if (체결강도 >= 110) else 0

# 가격 패턴 신호
상승패턴신호          = 1 if (현재가 > 현재가N(1) and 현재가N(1) > 현재가N(2)) else 0
고가근접신호          = 1 if (현재가 > (고가 - (고가 - 저가) * 0.30)) else 0

# 신호 점수 집계
총신호점수            = (MA정배열신호 + SAR상승신호 + RSI상승신호 + MACD골든크로스신호 +
                         MACD상승신호 + 스토캐스틱상승신호 + 볼린저하단반등신호 + 볼린저중심돌파신호 +
                         거래량증가신호 + 체결강도신호 + 상승패턴신호 + 고가근접신호)

매수 = True

# 공통 필터
if not (관심종목 == 1):
    매수 = False
elif not (90500 <= 시분초 <= 143000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# 필수 신호 확인 (MA정배열, 거래량증가 필수)
elif not (MA정배열신호 == 1 and 거래량증가신호 == 1):
    매수 = False

# 시가총액별 세부 조건
elif 시가총액 < 3000:
    if not (총신호점수 >= 8):  # 12점 만점 중 8점 이상
        매수 = False
    elif not (체결강도 >= 115):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
    elif not (등락율 > -5.0 and 등락율 < 25.0):
        매수 = False
elif 시가총액 < 5000:
    if not (총신호점수 >= 7):  # 12점 만점 중 7점 이상
        매수 = False
    elif not (체결강도 >= 110):
        매수 = False
    elif not (회전율 > 1.2):
        매수 = False
    elif not (등락율 > -5.0 and 등락율 < 25.0):
        매수 = False
else:
    if not (총신호점수 >= 6):  # 12점 만점 중 6점 이상
        매수 = False
    elif not (체결강도 >= 105):
        매수 = False
    elif not (회전율 > 1.0):
        매수 = False
    elif not (등락율 > -5.0 and 등락율 < 25.0):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식

```python
# ================================
#  공통 계산 지표
# ================================
# 약세 신호 집계
MA역배열신호          = 1 if (현재가 < 이동평균(5)) else 0
SAR하락신호           = 1 if (현재가 < SAR) else 0
RSI과매수신호         = 1 if (RSI > 75) else 0
MACD데드크로스신호    = 1 if (MACD < MACDS and MACD_N(1) >= MACDS_N(1)) else 0
스토캐스틱하락신호    = 1 if (STOCH_K < STOCH_D and STOCH_K > 20) else 0
볼린저상단이탈신호    = 1 if (현재가 < BBU and 현재가N(1) >= BBU) else 0
체결강도약화신호      = 1 if (체결강도 < 95) else 0
하락패턴신호          = 1 if (현재가 < 현재가N(1) and 현재가N(1) < 현재가N(2)) else 0

총약세신호            = (MA역배열신호 + SAR하락신호 + RSI과매수신호 + MACD데드크로스신호 +
                         스토캐스틱하락신호 + 볼린저상단이탈신호 + 체결강도약화신호 + 하락패턴신호)

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 4.0 or 수익률 <= -2.0:
    매도 = True
elif 최고수익률 > 5.0 and 최고수익률 * 0.70 >= 수익률:
    매도 = True
elif 보유시간 > 2400:  # 40분
    매도 = True
elif 총약세신호 >= 4:  # 8점 만점 중 4점 이상
    매도 = True
elif MA역배열신호 == 1 and 보유시간 > 300:  # 5분 이후 MA 이탈
    매도 = True
elif MACD데드크로스신호 == 1:
    매도 = True
elif 시분초 >= 145500:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

## 최적화 조건식

### 매수 최적화 조건식 - C_M_MIC_BO

```python
# 추세 지표 신호
MA정배열신호          = 1 if (이동평균(5) > 이동평균(20) > 이동평균(60)) else 0
SAR상승신호           = 1 if (현재가 > SAR) else 0

# 모멘텀 지표 신호
RSI상승신호           = 1 if (self.vars[1] < RSI < self.vars[2] and RSI > RSI_N(1)) else 0
MACD골든크로스신호    = 1 if (MACD > MACDS and MACD_N(1) <= MACDS_N(1)) else 0
MACD상승신호          = 1 if (MACD > 0 and MACD > MACD_N(1)) else 0
스토캐스틱상승신호    = 1 if (STOCH_K > STOCH_D and STOCH_K < self.vars[3]) else 0

# 변동성 지표 신호
볼린저하단반등신호    = 1 if (현재가 > BBL and 현재가N(1) <= BBL) else 0
볼린저중심돌파신호    = 1 if (현재가 > BBM and 현재가N(1) <= BBM) else 0

# 거래량 지표 신호
거래량증가신호        = 1 if (분당거래대금 > 분당거래대금평균(20) * self.vars[4]) else 0
체결강도신호          = 1 if (체결강도 >= self.vars[5]) else 0

# 가격 패턴 신호
상승패턴신호          = 1 if (현재가 > 현재가N(1) and 현재가N(1) > 현재가N(2)) else 0
고가근접신호          = 1 if (현재가 > (고가 - (고가 - 저가) * self.vars[6] / 100)) else 0

총신호점수            = (MA정배열신호 + SAR상승신호 + RSI상승신호 + MACD골든크로스신호 +
                         MACD상승신호 + 스토캐스틱상승신호 + 볼린저하단반등신호 + 볼린저중심돌파신호 +
                         거래량증가신호 + 체결강도신호 + 상승패턴신호 + 고가근접신호)

매수 = True

if not (관심종목 == 1):
    매수 = False
elif not (90500 <= 시분초 <= 143000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False
elif not (MA정배열신호 == 1 and 거래량증가신호 == 1):
    매수 = False

elif 시가총액 < 3000:
    if not (총신호점수 >= self.vars[7]):
        매수 = False
    elif not (체결강도 >= self.vars[8]):
        매수 = False
    elif not (회전율 > self.vars[9]):
        매수 = False
    elif not (등락율 > self.vars[10] and 등락율 < self.vars[11]):
        매수 = False
elif 시가총액 < 5000:
    if not (총신호점수 >= self.vars[12]):
        매수 = False
    elif not (체결강도 >= self.vars[13]):
        매수 = False
    elif not (회전율 > self.vars[14]):
        매수 = False
    elif not (등락율 > self.vars[15] and 등락율 < self.vars[16]):
        매수 = False
else:
    if not (총신호점수 >= self.vars[17]):
        매수 = False
    elif not (체결강도 >= self.vars[18]):
        매수 = False
    elif not (회전율 > self.vars[19]):
        매수 = False
    elif not (등락율 > self.vars[20] and 등락율 < self.vars[21]):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매수 최적화 범위 - C_M_MIC_BOR

```python
# 공통
self.vars[1]  = [[35, 45, 5], 40]                    # RSI 하한
self.vars[2]  = [[65, 75, 5], 70]                    # RSI 상한
self.vars[3]  = [[75, 85, 5], 80]                    # STOCH_K 상한
self.vars[4]  = [[1.3, 1.7, 0.2], 1.5]               # 거래량 증가 비율
self.vars[5]  = [[105, 115, 5], 110]                 # 체결강도 하한
self.vars[6]  = [[25, 35, 5], 30]                    # 고가 근접도(%)

# 시가총액 < 3000
self.vars[7]  = [[7, 9, 1], 8]                       # 총신호점수 하한
self.vars[8]  = [[110, 120, 5], 115]                 # 체결강도 하한
self.vars[9]  = [[1.2, 1.8, 0.3], 1.5]               # 회전율 하한
self.vars[10] = [[-6, -4, 1], -5]                    # 등락율 하한(%)
self.vars[11] = [[23, 27, 2], 25]                    # 등락율 상한(%)

# 시가총액 < 5000
self.vars[12] = [[6, 8, 1], 7]                       # 총신호점수 하한
self.vars[13] = [[105, 115, 5], 110]                 # 체결강도 하한
self.vars[14] = [[1.0, 1.4, 0.2], 1.2]               # 회전율 하한
self.vars[15] = [[-6, -4, 1], -5]                    # 등락율 하한(%)
self.vars[16] = [[23, 27, 2], 25]                    # 등락율 상한(%)

# 시가총액 >= 5000
self.vars[17] = [[5, 7, 1], 6]                       # 총신호점수 하한
self.vars[18] = [[100, 110, 5], 105]                 # 체결강도 하한
self.vars[19] = [[0.8, 1.2, 0.2], 1.0]               # 회전율 하한
self.vars[20] = [[-6, -4, 1], -5]                    # 등락율 하한(%)
self.vars[21] = [[23, 27, 2], 25]                    # 등락율 상한(%)
```

### 매도 최적화 조건식 - C_M_MIC_SO

```python
MA역배열신호          = 1 if (현재가 < 이동평균(5)) else 0
SAR하락신호           = 1 if (현재가 < SAR) else 0
RSI과매수신호         = 1 if (RSI > self.vars[23]) else 0
MACD데드크로스신호    = 1 if (MACD < MACDS and MACD_N(1) >= MACDS_N(1)) else 0
스토캐스틱하락신호    = 1 if (STOCH_K < STOCH_D and STOCH_K > 20) else 0
볼린저상단이탈신호    = 1 if (현재가 < BBU and 현재가N(1) >= BBU) else 0
체결강도약화신호      = 1 if (체결강도 < self.vars[24]) else 0
하락패턴신호          = 1 if (현재가 < 현재가N(1) and 현재가N(1) < 현재가N(2)) else 0

총약세신호            = (MA역배열신호 + SAR하락신호 + RSI과매수신호 + MACD데드크로스신호 +
                         스토캐스틱하락신호 + 볼린저상단이탈신호 + 체결강도약화신호 + 하락패턴신호)

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= self.vars[25] or 수익률 <= self.vars[26]:
    매도 = True
elif 최고수익률 > self.vars[27] and 최고수익률 * self.vars[28] >= 수익률:
    매도 = True
elif 보유시간 > self.vars[29]:
    매도 = True
elif 총약세신호 >= self.vars[30]:
    매도 = True
elif MA역배열신호 == 1 and 보유시간 > self.vars[31]:
    매도 = True
elif MACD데드크로스신호 == 1:
    매도 = True
elif 시분초 >= 145500:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

### 매도 최적화 범위 - C_M_MIC_SOR

```python
self.vars[23] = [[70, 80, 5], 75]                    # RSI 과매수 임계
self.vars[24] = [[90, 100, 5], 95]                   # 체결강도 하한
self.vars[25] = [[3.5, 4.5, 0.5], 4.0]               # 목표 수익 실현(%)
self.vars[26] = [[-2.5, -1.5, 0.5], -2.0]            # 최대 손실 컷(%)
self.vars[27] = [[4.5, 5.5, 0.5], 5.0]               # 최고수익률 기준값(%)
self.vars[28] = [[0.65, 0.75, 0.05], 0.70]           # 트레일링 보정 비율
self.vars[29] = [[2100, 2700, 300], 2400]            # 최대 보유시간(초)
self.vars[30] = [[3, 5, 1], 4]                       # 약세신호 임계
self.vars[31] = [[240, 360, 60], 300]                # MA이탈 확인 시간(초)
```

### GA 최적화 범위 - C_M_MIC_GAR

```python
# 매수 조건
self.vars[1]  = [35, 45]                             # RSI 하한
self.vars[2]  = [65, 75]                             # RSI 상한
self.vars[3]  = [75, 85]                             # STOCH_K 상한
self.vars[4]  = [1.3, 1.7]                           # 거래량 증가 비율
self.vars[5]  = [105, 115]                           # 체결강도 하한
self.vars[6]  = [25, 35]                             # 고가 근접도(%)

# 시가총액 < 3000
self.vars[7]  = [7, 9]                               # 총신호점수 하한
self.vars[8]  = [110, 120]                           # 체결강도 하한
self.vars[9]  = [1.2, 1.8]                           # 회전율 하한
self.vars[10] = [-6, -4]                             # 등락율 하한(%)
self.vars[11] = [23, 27]                             # 등락율 상한(%)

# 시가총액 < 5000
self.vars[12] = [6, 8]                               # 총신호점수 하한
self.vars[13] = [105, 115]                           # 체결강도 하한
self.vars[14] = [1.0, 1.4]                           # 회전율 하한
self.vars[15] = [-6, -4]                             # 등락율 하한(%)
self.vars[16] = [23, 27]                             # 등락율 상한(%)

# 시가총액 >= 5000
self.vars[17] = [5, 7]                               # 총신호점수 하한
self.vars[18] = [100, 110]                           # 체결강도 하한
self.vars[19] = [0.8, 1.2]                           # 회전율 하한
self.vars[20] = [-6, -4]                             # 등락율 하한(%)
self.vars[21] = [23, 27]                             # 등락율 상한(%)

# 매도 조건
self.vars[23] = [70, 80]                             # RSI 과매수 임계
self.vars[24] = [90, 100]                            # 체결강도 하한
self.vars[25] = [3.5, 4.5]                           # 목표 수익 실현(%)
self.vars[26] = [-2.5, -1.5]                         # 최대 손실 컷(%)
self.vars[27] = [4.5, 5.5]                           # 최고수익률 기준값(%)
self.vars[28] = [0.65, 0.75]                         # 트레일링 보정 비율
self.vars[29] = [2100, 2700]                         # 최대 보유시간(초)
self.vars[30] = [3, 5]                               # 약세신호 임계
self.vars[31] = [240, 360]                           # MA이탈 확인 시간(초)
```

---

## 조건식 개선 방향 연구

1) **지표 가중치 최적화**
   - 각 지표별 신뢰도 평가
   - 시장 상황별 가중치 조정
   - 머신러닝 기반 가중치 학습

2) **신호 합의 메커니즘**
   - 필수 지표 vs 선택 지표
   - 다수결 vs 가중평균
   - 부정 신호 처리 방법

3) **지표 간 상관관계 분석**
   - 중복 신호 제거
   - 독립적 지표 조합
   - 상호 보완적 지표 선택

4) **동적 임계값 조정**
   - 시장 변동성 기반 조정
   - 과거 성과 기반 조정
   - 적응형 임계값 시스템

5) **리스크 관리**
   - 약세 신호 4개 이상 청산
   - MACD 데드크로스 즉시 청산
   - 트레일링 스톱 (최고수익의 70%)

## 태그
- #주식트레이딩
- #분봉트레이딩
- #매수조건
- #매도조건
- #최적화
- #다중지표
- #복합전략
- #신호합의
- #리스크관리
