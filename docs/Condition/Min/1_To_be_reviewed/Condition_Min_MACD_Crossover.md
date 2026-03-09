# 조건식 (Condition) - MACD Crossover Strategy (분봉)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 목차
- [조건식 (Condition) - MACD Crossover Strategy (분봉)](#조건식-condition---macd-crossover-strategy-분봉)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - MACD Crossover](#condition---macd-crossover)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **MACD 크로스오버 전략**을 정의한다.

- **대상 시간 구간**: 09:00 ~ 15:18 (장 전체)
- **대상 종목**: 전 종목 대상
- **전략 타입**: MACD 골든크로스/데드크로스 전략
- **핵심 변수**: MACD, MACDS, MACDH, RSI
- **업데이트 이력**:
  - 초기 문서 작성: MACD 크로스오버 전략

## 소개

이 문서는 **MACD 크로스오버 전략(MACD Crossover Strategy)**을 설명합니다. 분봉 데이터에서 MACD와 시그널 라인의 골든크로스를 포착하여 매수하고, 데드크로스 발생 시 매도하는 전략입니다.

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.
- 분봉 데이터 기반으로 1분 단위 캔들스틱 데이터를 분석합니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `MACD`: MACD Crossover를 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.

2. **예시**:
   - `C_MACD_B`: MACD 크로스오버 전략의 매수 조건식
   - `C_MACD_S`: MACD 크로스오버 전략의 매도 조건식

---

# Condition - MACD Crossover

## 조건식

### 매수 조건식

```python
# MACD Crossover Strategy - MACD 골든크로스 포착 전략
# 거래 시간: 900 ~ 1518 (9시 ~ 15시 18분)

매수 = False

# 시간 제한: 정규 장 시간만 거래
if not (90000 <= 시분초 <= 151800):
    매수 = False

# 기본 필터링
elif not (2000 < 현재가 <= 50000):
    매수 = False
elif not (1.0 < 등락율 <= 28.0):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# 충분한 데이터 확보
elif not (데이터길이 > 60):
    매수 = False

# 시가총액별 조건
elif 시가총액 < 4000:
    # 소형주 (4000억 미만)
    # MACD 골든크로스 확인
    if not (MACD > MACDS and MACD_N(1) <= MACDS_N(1)):
        매수 = False
    # MACD 히스토그램 양수 전환
    elif not (MACDH > 0 and MACDH_N(1) <= 0):
        매수 = False
    # MACD 상승 추세
    elif not (MACD > MACD_N(1)):
        매수 = False
    # RSI 과매도 구간 탈출
    elif not (30 < RSI < 70):
        매수 = False
    elif not (RSI > RSI_N(1)):
        매수 = False
    # 이동평균선 정배열
    elif not (이동평균(20) > 이동평균(60)):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
    # 분당거래대금 증가
    elif not (분당거래대금 > 분당거래대금평균(30)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금N(1)):
        매수 = False
    # 체결강도
    elif not (체결강도 > 115):
        매수 = False
    elif not (체결강도평균(20) > 105):
        매수 = False
    # 분봉 양봉 확인
    elif not (현재가 > 분봉시가):
        매수 = False
    elif not (분봉고가 > 분봉고가N(1)):
        매수 = False
    # 거래 활성도
    elif not (당일거래대금 > 20 * 100):
        매수 = False
    elif not (전일비 > 80):
        매수 = False
    elif not (회전율 > 1.0):
        매수 = False
    # 등락율 각도
    elif not (등락율각도(30) > 3):
        매수 = False

else:
    # 중대형주 (4000억 이상)
    # MACD 골든크로스 확인
    if not (MACD > MACDS and MACD_N(1) <= MACDS_N(1)):
        매수 = False
    # MACD 히스토그램 양수 전환
    elif not (MACDH > 0 and MACDH_N(1) <= 0):
        매수 = False
    # MACD 상승 추세
    elif not (MACD > MACD_N(1)):
        매수 = False
    # RSI 과매도 구간 탈출
    elif not (35 < RSI < 68):
        매수 = False
    elif not (RSI > RSI_N(1)):
        매수 = False
    # 이동평균선 정배열
    elif not (이동평균(20) > 이동평균(60)):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
    # 분당거래대금 증가
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.1):
        매수 = False
    elif not (분당거래대금 > 분당거래대금N(1)):
        매수 = False
    # 체결강도
    elif not (체결강도 > 110):
        매수 = False
    elif not (체결강도평균(20) > 103):
        매수 = False
    # 분봉 양봉 확인
    elif not (현재가 > 분봉시가):
        매수 = False
    elif not (분봉고가 > 분봉고가N(1)):
        매수 = False
    # 거래 활성도
    elif not (당일거래대금 > 100 * 100):
        매수 = False
    elif not (전일비 > 60):
        매수 = False
    elif not (회전율 > 0.7):
        매수 = False
    # 등락율 각도
    elif not (등락율각도(30) > 4):
        매수 = False
```

### 매도 조건식

```python
# MACD Crossover Strategy - MACD 데드크로스 감지 매도 전략

매도 = False

# 상한가 근접 시 매도
if 등락율 > 29.5:
    매도 = True

# 수익률 기준 매도
elif 수익률 >= 6.0:
    매도 = True
elif 수익률 <= -3.0:
    매도 = True

# 최고수익률 대비 하락 시 매도
elif 최고수익률 >= 7.0 and 수익률 < 최고수익률 - 3.0:
    매도 = True

# 시가총액별 매도 조건
elif 시가총액 < 4000:
    # 소형주 매도 조건
    # MACD 데드크로스
    if MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    # MACD 히스토그램 음수 전환
    elif MACDH < 0 and MACDH_N(1) >= 0:
        매도 = True
    # MACD 하락 추세
    elif MACD < MACD_N(1) and MACD_N(1) < MACD_N(2):
        매도 = True
    # RSI 과매수 구간
    elif RSI > 75:
        매도 = True
    elif RSI < RSI_N(1) and RSI_N(1) < RSI_N(2):
        매도 = True
    # 이동평균선 이탈
    elif 현재가 < 이동평균(20) and 현재가N(1) >= 이동평균(20, 1):
        매도 = True
    elif 이동평균(20) < 이동평균(60):
        매도 = True
    # 체결강도 약화
    elif 체결강도 < 90 and 체결강도평균(20) < 95:
        매도 = True
    # 분봉 음봉 연속
    elif 현재가 < 분봉시가 and 현재가N(1) < 분봉시가N(1):
        매도 = True
    # 등락율 각도 하락
    elif 등락율각도(30) < 0:
        매도 = True
    # 시간 기준
    elif 보유시간 > 120:  # 2시간 이상 보유 시 매도
        매도 = True

else:
    # 중대형주 매도 조건
    # MACD 데드크로스
    if MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    # MACD 히스토그램 음수 전환
    elif MACDH < 0 and MACDH_N(1) >= 0:
        매도 = True
    # MACD 하락 추세
    elif MACD < MACD_N(1) and MACD_N(1) < MACD_N(2):
        매도 = True
    # RSI 과매수 구간
    elif RSI > 72:
        매도 = True
    elif RSI < RSI_N(1) and RSI_N(1) < RSI_N(2):
        매도 = True
    # 이동평균선 이탈
    elif 현재가 < 이동평균(20) and 현재가N(1) >= 이동평균(20, 1):
        매도 = True
    elif 이동평균(20) < 이동평균(60):
        매도 = True
    # 체결강도 약화
    elif 체결강도 < 95 and 체결강도평균(20) < 98:
        매도 = True
    # 분봉 음봉 연속
    elif 현재가 < 분봉시가 and 현재가N(1) < 분봉시가N(1):
        매도 = True
    # 등락율 각도 하락
    elif 등락율각도(30) < 2:
        매도 = True
    # 시간 기준
    elif 보유시간 > 180:  # 3시간 이상 보유 시 매도
        매도 = True
```

---

**Last Update: 2025-01-18**



---

## 최적화 조건식

## BO (Buy Optimization)

```python
# 기본 매수 조건을 self.vars로 변환
# 주요 변수만 최적화 대상으로 선정
# self.vars[0] 사용 - 값: 0.7
# self.vars[1] 사용 - 값: 1.0
# self.vars[2] 사용 - 값: 1.1
# self.vars[3] 사용 - 값: 3
# self.vars[4] 사용 - 값: 4
# self.vars[5] 사용 - 값: 20
# self.vars[6] 사용 - 값: 28.0
# self.vars[7] 사용 - 값: 30
# self.vars[8] 사용 - 값: 35
# self.vars[9] 사용 - 값: 60
```

## BOR (Buy Optimization Range)

```python
self.vars[0] = [[0.5, 0.9, 0.1], 0.7]  # 비율 (0.7)
self.vars[1] = [[1.0, 1.0, 1.0], 1.0]  # 카운트 (1.0)
self.vars[2] = [[1.0, 1.0, 1.0], 1.1]  # 카운트 (1.1)
self.vars[3] = [[2, 3, 1], 3]  # 카운트 (3)
self.vars[4] = [[2, 5, 1], 4]  # 카운트 (4)
self.vars[5] = [[14, 26, 5], 20]  # 임계값 (20)
self.vars[6] = [[19.0, 36.0, 5.0], 28.0]  # 임계값 (28.0)
self.vars[7] = [[21, 39, 5], 30]  # 임계값 (30)
self.vars[8] = [[24, 45, 5], 35]  # 임계값 (35)
self.vars[9] = [[42, 78, 5], 60]  # 임계값 (60)
self.vars[10] = [[47, 88, 5], 68]  # 임계값 (68)
self.vars[11] = [[49, 91, 5], 70]  # 임계값 (70)
self.vars[12] = [[56, 104, 5], 80]  # 임계값 (80)
self.vars[13] = [[70, 130, 100], 100]  # 금액 (100)
self.vars[14] = [[72, 133, 100], 103]  # 금액 (103)
self.vars[15] = [[73, 136, 100], 105]  # 금액 (105)
self.vars[16] = [[77, 143, 100], 110]  # 금액 (110)
self.vars[17] = [[80, 149, 100], 115]  # 금액 (115)
self.vars[18] = [[1400, 2600, 1000], 2000]  # 대금 (2000)
self.vars[19] = [[2800, 5200, 1000], 4000]  # 대금 (4000)
```

## SO (Sell Optimization)

```python
# 기본 매도 조건을 self.vars로 변환
# 주요 변수만 최적화 대상으로 선정
# self.vars[20] 사용 - 값: 1
# self.vars[21] 사용 - 값: 2
# self.vars[22] 사용 - 값: 3.0
# self.vars[23] 사용 - 값: 6.0
# self.vars[24] 사용 - 값: 7.0
# self.vars[25] 사용 - 값: 20
# self.vars[26] 사용 - 값: 29.5
# self.vars[27] 사용 - 값: 30
# self.vars[28] 사용 - 값: 60
# self.vars[29] 사용 - 값: 72
```

## SOR (Sell Optimization Range)

```python
self.vars[20] = [[1, 1, 1], 1]  # 카운트 (1)
self.vars[21] = [[1, 2, 1], 2]  # 카운트 (2)
self.vars[22] = [[2.0, 3.0, 1.0], 3.0]  # 카운트 (3.0)
self.vars[23] = [[4.0, 7.0, 1.0], 6.0]  # 카운트 (6.0)
self.vars[24] = [[4.0, 9.0, 1.0], 7.0]  # 카운트 (7.0)
self.vars[25] = [[14, 26, 5], 20]  # 임계값 (20)
self.vars[26] = [[20.0, 38.0, 5.0], 29.5]  # 임계값 (29.5)
self.vars[27] = [[21, 39, 5], 30]  # 임계값 (30)
self.vars[28] = [[42, 78, 5], 60]  # 임계값 (60)
self.vars[29] = [[50, 93, 5], 72]  # 임계값 (72)
self.vars[30] = [[52, 97, 5], 75]  # 임계값 (75)
self.vars[31] = [[62, 117, 5], 90]  # 임계값 (90)
```

## OR (Optimum Range)

핵심 변수만 선별하여 최적화 (최대 10개)

```python
self.vars[0] = [[1, 1, 1], 1]  # 카운트 (1)
self.vars[1] = [[1, 2, 1], 2]  # 카운트 (2)
self.vars[2] = [[2.0, 3.0, 1.0], 3.0]  # 카운트 (3.0)
self.vars[3] = [[4.0, 7.0, 1.0], 6.0]  # 카운트 (6.0)
self.vars[4] = [[4.0, 9.0, 1.0], 7.0]  # 카운트 (7.0)
self.vars[5] = [[14, 26, 5], 20]  # 임계값 (20)
self.vars[6] = [[0.5, 0.9, 0.1], 0.7]  # 비율 (0.7)
self.vars[7] = [[1.0, 1.0, 1.0], 1.0]  # 카운트 (1.0)
self.vars[8] = [[1.0, 1.0, 1.0], 1.1]  # 카운트 (1.1)
self.vars[9] = [[2, 3, 1], 3]  # 카운트 (3)
```

**예상 경우의 수**: 약 10,000,000,000

## GAR (Genetic Algorithm Range)

```python
self.vars[0] = [[1, 1]]  # 카운트 (1)
self.vars[1] = [[1, 2], 2]  # 카운트 (2)
self.vars[2] = [[2.0, 3.0, 1.0], 3.0]  # 카운트 (3.0)
self.vars[3] = [[4.0, 7.0, 1.0], 6.0]  # 카운트 (6.0)
self.vars[4] = [[4.0, 9.0, 1.0], 7.0]  # 카운트 (7.0)
self.vars[5] = [[14, 26], 20]  # 임계값 (20)
self.vars[6] = [[0.5, 0.9], 0.7]  # 비율 (0.7)
self.vars[7] = [[1.0, 1.0, 1.0], 1.0]  # 카운트 (1.0)
self.vars[8] = [[1.0, 1.0, 1.0], 1.1]  # 카운트 (1.1)
self.vars[9] = [[2, 3], 3]  # 카운트 (3)
```

## 조건식 개선 방향 연구

### 1. 추가 지표 활용 연구

**우선순위: 높음**
- **TA-Lib 지표 조합 확대**
  - ADX (추세 강도) + DMI (방향성) 조합
  - Ichimoku Cloud (일목균형표) 활용
  - 구현 난이도: 중

- **변동성 지표 추가**
  - ATR (Average True Range) 기반 손절폭 설정
  - Bollinger Band Width로 변동성 확대 구간 포착
  - 구현 난이도: 낮음

### 2. 시간대별 전략 세분화 연구

**우선순위: 높음**
- **장 시간대별 분봉 전략 차등화**
  - 09:00-10:00: 5분봉 전략
  - 10:00-14:00: 10분봉 전략
  - 14:00-15:00: 3분봉 전략
  - 구현 난이도: 중

### 3. 매도 조건 고도화 연구

**우선순위: 높음**
- **TA-Lib 매도 신호 강화**
  - MACD 데드크로스 + RSI 과매수 조합
  - Stochastic %K/%D 하향 교차 시 매도
  - 구현 난이도: 낮음

- **이동평균선 이탈 기반 매도**
  - 5MA 하향 돌파 시 경고
  - 20MA 하향 돌파 시 청산
  - 구현 난이도: 낮음

### 4. 리스크 관리 강화 연구

**우선순위: 높음**
- **다중 시간프레임 분석**
  - 1분봉 + 5분봉 + 10분봉 동시 확인
  - 상위 시간프레임 추세와 부합 시만 진입
  - 구현 난이도: 중

- **거래량 프로파일 분석**
  - 가격대별 거래량 분포 확인
  - 고거래량 구간 지지/저항 활용
  - 구현 난이도: 높음

### 5. 최적화 전략 개선 연구

**우선순위: 중간**
- **TA-Lib 파라미터 최적화**
  - RSI 기간: 14 → 10~20 범위 탐색
  - MACD (12,26,9) → (8,17,9) 등 변형 테스트
  - 구현 난이도: 중

- **기계학습 기반 지표 가중치 최적화**
  - 각 TA-Lib 지표의 예측력 평가
  - 가중치 동적 조정
  - 구현 난이도: 높음

### 구현 우선순위

1. **1단계 (즉시 구현)**:
   - 변동성 지표 추가 (ATR, BB Width)
   - TA-Lib 매도 신호 강화
   - 이동평균선 이탈 기반 매도

2. **2단계 (1개월 내)**:
   - TA-Lib 지표 조합 확대 (ADX, DMI, Ichimoku)
   - 시간대별 분봉 전략 차등화
   - 다중 시간프레임 분석

3. **3단계 (3개월 내)**:
   - TA-Lib 파라미터 최적화
   - 거래량 프로파일 분석
   - 기계학습 기반 최적화

