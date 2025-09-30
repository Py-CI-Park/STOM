# 시초 급등 주식 매수/매도 전략 조건식

## 목차
- [소개](#소개)
- [가이드라인](#가이드라인)
  - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - 시초 급등 주식 전략](#condition---시초-급등-주식-전략)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)
  - [최적화 조건식](#최적화-조건식)
    - [매수 최적화 조건식](#매수-최적화-조건식)
    - [매수 최적화 범위](#매수-최적화-범위)
    - [매도 최적화 조건식](#매도-최적화-조건식)
    - [매도 최적화 범위](#매도-최적화-범위)

## 소개
이 문서는 분봉 데이터를 활용하여 장 초반(09:00~10:30) 시초 급등 주 Ascendancy 주식 종목을 포착하고 단기 수익을 목표로 하는 매수/매도 전략을 구현합니다. 시초 급등 주식은 장 시작 후 강한 상승 모멘텀을 보이는 종목으로, 높은 거래량과 체결강도를 동반하며 단기적인 가격 변동성을 활용한 트레이딩에 적합합니다. 이 전략은 **RSI**, **MACD**, **볼린저밴드**, **거래량**, **체결강도** 등 다양한 지표를 조합하여 신뢰성 있는 매수 신호를 생성하고, 빠른 수익 실현과 손실 관리를 위한 매도 조건을 제공합니다.

## 가이드라인
- 모든 조건식은 Python으로 작성되며, 분봉 데이터 기반 주식 거래의 자동화를 목표로 합니다.
- **Back_Testing_Guideline_Min.md**의 변수 사용법을 엄격히 준수합니다.
- 장 초반(09:00~10:30)에 특화된 조건을 적용하여 시초 급등 주식의 특성을 반영합니다.
- 다중 지표를 활용하여 거짓 신호를 최소화하고, 빠른 매도 조건을 통해 리스크를 관리합니다.

### 저장 이름 규칙
- `C_MIN_OPEN_SURGE_B`: 시초 급등 주식 매수 조건식
- `C_MIN_OPEN_SURGE_S`: 시초 급등 주식 매도 조건식
- `C_MIN_OPEN_SURGE_BO`: 시초 급등 주식 매수 최적화 조건식
- `C_MIN_OPEN_SURGE_SO`: 시초 급등 주식 매도 최적화 조건식

---

## Condition - 시초 급등 주식 전략

### 조건식

#### 매수 조건식
```python
# =============================================================================
# 시초 급등 주식 매수 조건식
# 작성일: 2025-07-13
# 기반: Back_Testing_Guideline_Min.md 변수 사용법 준수
# 설명: 장 초반(09:00~10:30) 급등 주식 포착을 위한 매수 조건
# =============================================================================

# 시간 조건 (09:00:00 ~ 10:30:00)
opening_session = (시분초 >= 90000 and 시분초 <= 103000)

# 기본 변수 정의
현재가격 = 현재가
이전가격 = 현재가N(1)
분봉시가 = 분봉시가
등락율 = 등락율
분당거래대금 = 분당거래대금
분당거래대금평균5분 = 분당거래대금평균(5)
체결강도 = 체결강도
이동평균5 = 이동평균(5)
이동평균10 = 이동평균(10)
볼린저상단 = BBU
볼린저중단 = BBM
볼린저하단 = BBL
볼린저위치 = (현재가 - 볼린저하단) / (볼린저상단 - 볼린저하단) if (볼린저상단 - 볼린저하단) != 0 else 0
갭등락율계산 = ((분봉시가 - 시가) / 시가) * 100 if 시가 != 0 else 0

# 기술적 지표 변수
RSI현재 = RSI
RSI이전 = RSI_N(1)
MACD현재 = MACD
MACD신호 = MACDS
MACD히스토그램 = MACDH

# 초기 매수 플래그 설정
buy = True

# =============================================================================
# 시장 상황 및 기본 조건 검증
# =============================================================================

# 시간 조건
if not opening_session:
    buy = False

# 가격 범위 조건 (1,000원 ~ 50,000원)
elif not (1000 <= 현재가 <= 50000):
    buy = False

# 등락율 조건 (2.0% ~ 29.0%)
elif not (2.0 <= 등락율 <= 29.0):
    buy = False

# 갭 등락율 조건 (0.5% 이상)
elif not (갭등락율계산 >= 0.5):
    buy = False

# 시가총액 조건 (300억원 이상)
elif not (시가총액 >= 300):
    buy = False

# 유동성 조건 (당일거래대금 50억원 이상)
elif not (당일거래대금 >= 500):
    buy = False

# =============================================================================
# 기술적 분석 신호 생성
# =============================================================================

# 신호 점수 시스템 (최대 100점)
signal_score = 0

# 1. 급등 모멘텀 확인 (최대 30점)
momentum_score = 0
if 등락율 >= 3.0:  # 3% 이상 급등
    momentum_score += 10
if 현재가 > 분봉시가 * 1.03:  # 시가 대비 3% 이상 상승
    momentum_score += 10
if 현재가 > 최고분봉고가(5) * 1.005:  # 5분봉 고가 돌파
    momentum_score += 10

signal_score += momentum_score

# 2. 거래량 및 체결강도 분석 (최대 30점)
volume_score = 0
if 분당거래대금 >= 분당거래대금평균5분 * 2.0:  # 거래량 2배 이상 급증
    volume_score += 15
if 체결강도 >= 130:  # 강한 매수 우세
    volume_score += 15

signal_score += volume_score

# 3. RSI 신호 분석 (최대 20점)
rsi_score = 0
if 40 <= RSI현재 <= 75:  # RSI 과매수 방지
    rsi_score += 10
if RSI현재 > RSI이전:  # RSI 상승
    rsi_score += 10

signal_score += rsi_score

# 4. MACD 신호 분석 (최대 20점)
macd_score = 0
if MACD현재 > MACD신호:  # MACD 골든크로스
    macd_score += 10
if MACD히스토그램 > 0:  # 히스토그램 양수
    macd_score += 10

signal_score += macd_score

# =============================================================================
# 추가 필터링 조건
# =============================================================================

# 기본 신호 점수 조건 (70점 이상)
elif signal_score < 70:
    buy = False

# 이동평균 정배열 확인
elif not (이동평균5 > 이동평균10 and 현재가 > 이동평균5):
    buy = False

# 볼린저밴드 위치 확인
elif not (0.2 <= 볼린저위치 <= 0.8):
    buy = False

# 회전율 조건 (활발한 거래 확인)
elif not (회전율 >= 0.5):
    buy = False

# 라운드피겨 회피
elif 라운드피겨위5호가이내:
    buy = False

# =============================================================================
# 최종 매수 실행
# =============================================================================

# 최종 매수 실행 (매수 = True로 설정)
else:
    매수 = True
```

#### 매도 조건식
```python
# =============================================================================
# 시초 급등 주식 매도 조건식
# 작성일: 2025-07-13
# 기반: Back_Testing_Guideline_Min.md 변수 사용법 준수
# 설명: 빠른 수익 실현과 손실 관리를 위한 매도 조건
# =============================================================================

# 현재 수익률 및 보유 정보
현재수익률 = 수익률
최고수익률 = 최고수익률
보유시간분 = 보유시간
현재보유수량 = 보유수량

# 기술적 지표
RSI현재 = RSI
MACD현재 = MACD
MACD신호 = MACDS
이동평균5 = 이동평균(5)
이동평균10 = 이동평균(10)
볼린저상단 = BBU
볼린저중단 = BBM

# 거래량 및 시장 상황
분당거래대금 = 분당거래대금
분당거래대금평균10분 = 분당거래대금평균(10)
체결강도 = 체결강도

# 초기 매도 플래그 설정
sell = False
sell_reason = ""

# =============================================================================
# 수익실현 및 손절매 조건
# =============================================================================

# 상한가 근접 매도 (28% 이상)
if 등락율 >= 28.0:
    매도 = True
    매도사유 = "near_upper_limit"

# 목표 수익률 달성 (4% 이상)
elif 현재수익률 >= 4.0:
    매도 = True
    매도사유 = "target_return"

# 손절매 (-2% 이하)
elif 현재수익률 <= -2.0:
    매도 = True
    매도사유 = "stop_loss"

# 추적 손절매 (최고 수익률 대비 하락)
elif 최고수익률 >= 3.0 and (최고수익률 - 현재수익률) >= 1.5:
    매도 = True
    매도사유 = "trailing_stop"

# =============================================================================
# 시간 기반 매도 조건
# =============================================================================

# 보유시간 초과 (60분 이상)
elif 보유시간분 >= 60:
    매도 = True
    매도사유 = "time_exit"

# 장 초반 종료 시 매도 (10:30:00)
elif 시분초 >= 103000:
    매도 = True
    매도사유 = "opening_session_end"

# =============================================================================
# 기술적 지표 기반 매도 신호
# =============================================================================

# RSI 과매수 신호
elif RSI현재 >= 75:
    매도 = True
    매도사유 = "rsi_overbought"

# MACD 데드크로스
elif MACD현재 < MACD신호:
    매도 = True
    매도사유 = "macd_dead_cross"

# 볼린저밴드 상단 이탈 후 하락
elif 현재가 < 볼린저상단 and 현재가N(1) >= BBU_N(1):
    매도 = True
    매도사유 = "bollinger_upper_break"

# 이동평균선 하향 이탈
elif 현재가 < 이동평균5 and 이동평균5 < 이동평균10:
    매도 = True
    매도사유 = "ma_break"

# =============================================================================
# 거래량 및 시장 상황 기반 매도
# =============================================================================

# 거래량 급감 신호
elif 분당거래대금 < 분당거래대금평균10분 * 0.5:
    매도 = True
    매도사유 = "volume_drop"

# 체결강도 약화
elif 체결강도 < 80:
    매도 = True
    매도사유 = "trade_strength_weak"

# =============================================================================
# 최종 매도 실행
# =============================================================================

# 최종 매도 실행 (매도 = True로 설정)
if 매도:
    매도 = True
```

### 최적화 조건식

#### 매수 최적화 조건식
```python
# =============================================================================
# 시초 급등 주식 매수 최적화 조건식
# 작성일: 2025-07-13
# =============================================================================

# 최적화 변수 정의
signal_score_threshold = self.vars[0]  # 신호 점수 임계값
min_change_rate = self.vars[1]        # 최소 등락율
volume_value_multiplier = self.vars[2] # 거래대금 배수
trade_strength_threshold = self.vars[3] # 체결강도 임계값
rsi_lower = self.vars[4]              # RSI 하한
rsi_upper = self.vars[5]              # RSI 상한
open_price_ratio = self.vars[6]       # 시가 대비 상승 비율

# 기본 변수 정의
current_price = current_price
open_price = open_price
change_rate = change_rate
volume_value_per_min = volume_value_per_min
avg_volume_value_5min = avg_volume_value_per_min(5)
trade_strength = trade_strength
rsi_current = rsi(14)
rsi_previous = rsi_n(14, 1)
macd_current = macd(12, 26, 9)
macd_signal = macd_signal(12, 26, 9)
ma5 = moving_average(5)
ma10 = moving_average(10)
bb_position = (current_price - bollinger_lower(20, 2)) / (bollinger_upper(20, 2) - bollinger_lower(20, 2))
gap_change_rate = ((open_price - previous_close_price) / previous_close_price) * 100

# 초기 매수 플래그 설정
buy = True

# 기본 조건
if not (time_hhmmss >= 90000 and time_hhmmss <= 103000):
    buy = False
if not (1000 <= current_price <= 50000):
    buy = False
if not (change_rate >= min_change_rate):
    buy = False

# 갭등락율 조건 추가
elif not (갭등락율계산 >= 0.5):
    buy = False
elif not (시가총액 >= 300):
    buy = False

# 최적화된 신호 분석
signal_score = 0

# 모멘텀 신호
if 등락율 >= min_change_rate + 1.0:
    signal_score += 30
if 현재가 > 분봉시가 * open_price_ratio:
    signal_score += 20

# 거래량 및 체결강도 신호
if 분당거래대금 >= 분당거래대금평균5분 * volume_value_multiplier:
    signal_score += 20
if 체결강도 >= trade_strength_threshold:
    signal_score += 10

# RSI 신호
if rsi_lower <= RSI현재 <= rsi_upper:
    signal_score += 10

# 최적화된 조건 적용
if signal_score < signal_score_threshold:
    buy = False
elif not (이동평균5 > 이동평균10 and 현재가 > 이동평균5):
    buy = False
elif not (0.2 <= 볼린저위치 <= 0.8):
    buy = False
elif not (회전율 >= 0.5):
    buy = False
elif 라운드피겨위5호가이내:
    buy = False

# 최종 매수 실행 (매수 = True로 설정)
else:
    매수 = True
```

#### 매수 최적화 범위
```python
self.vars[0] = [[60, 70, 80], 70]            # signal_score_threshold
self.vars[1] = [[2.0, 3.0, 4.0], 2.0]        # min_change_rate
self.vars[2] = [[1.5, 2.0, 2.5], 2.0]        # volume_value_multiplier
self.vars[3] = [[120, 130, 140], 130]        # trade_strength_threshold
self.vars[4] = [[35, 40, 45], 40]            # rsi_lower
self.vars[5] = [[70, 75, 80], 75]            # rsi_upper
self.vars[6] = [[1.02, 1.03, 1.04], 1.03]   # open_price_ratio
```

#### 매도 최적화 조건식
```python
# =============================================================================
# 시초 급등 주식 매도 최적화 조건식
# 작성일: 2025-07-13
# =============================================================================

# 최적화 변수 정의
target_return = self.vars[0]         # 목표 수익률
stop_loss_return = self.vars[1]      # 손절매 수익률
trailing_stop_base = self.vars[2]    # 추적손절 기준
trailing_stop_range = self.vars[3]   # 추적손절 하락폭
max_holding_time = self.vars[4]      # 최대 보유시간
rsi_overbought = self.vars[5]        # RSI 과매수 기준

# 기본 변수
현재수익률 = 수익률
최고수익률 = 최고수익률
보유시간분 = 보유시간
RSI현재 = RSI
MACD현재 = MACD
MACD신호 = MACDS
이동평균5 = 이동평균(5)
이동평균10 = 이동평균(10)
분당거래대금 = 분당거래대금
분당거래대금평균10분 = 분당거래대금평균(10)
체결강도 = 체결강도

# 초기 매도 플래그 설정
sell = False
sell_reason = ""

# 최적화된 매도 조건
if 등락율 >= 28.0:
    매도 = True
    매도사유 = "near_upper_limit"
elif 현재수익률 >= target_return:
    매도 = True
    매도사유 = "target_return"
elif 현재수익률 <= stop_loss_return:
    매도 = True
    매도사유 = "stop_loss"
elif 최고수익률 >= trailing_stop_base and (최고수익률 - 현재수익률) >= trailing_stop_range:
    매도 = True
    매도사유 = "trailing_stop"
elif 보유시간분 >= max_holding_time:
    매도 = True
    매도사유 = "time_exit"
elif 시분초 >= 103000:
    매도 = True
    매도사유 = "opening_session_end"
elif RSI현재 >= rsi_overbought:
    매도 = True
    매도사유 = "rsi_overbought"
elif MACD현재 < MACD신호:
    매도 = True
    매도사유 = "macd_dead_cross"
elif 분당거래대금 < 분당거래대금평균10분 * 0.5:
    매도 = True
    매도사유 = "volume_drop"

# 최종 매도 실행 (매도 = True로 설정)
if 매도:
    매도 = True
```

#### 매도 최적화 범위
```python
self.vars[0] = [[3.0, 4.0, 5.0], 4.0]        # target_return
self.vars[1] = [[-3.0, -2.0, -1.5], -2.0]    # stop_loss_return
self.vars[2] = [[2.5, 3.0, 3.5], 3.0]        # trailing_stop_base
self.vars[3] = [[1.0, 1.5, 2.0], 1.5]        # trailing_stop_range
self.vars[4] = [[30, 60, 90], 60]           # max_holding_time (min)
self.vars[5] = [[70, 75, 80], 75]           # rsi_overbought
```

---

**작성일: 2025-07-13**  
**문서버전: 1.2**  
**준수기준: Back_Testing_Guideline_Min.md**

**Knowledge Tags**:  
- #TradingStrategy  
- #StockTrading  
- #MinuteData  
- #OpeningSurge  
- #TechnicalAnalysis  
- #RiskManagement  
- #Optimization  
- #ErrorFix