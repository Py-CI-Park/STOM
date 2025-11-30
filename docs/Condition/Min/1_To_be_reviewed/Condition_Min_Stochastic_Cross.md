# 조건식 - 스토캐스틱 크로스 전략

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 소개

**조건식 이름**: 스토캐스틱 크로스 전략 (Stochastic Cross Strategy)

이 문서는 스토캐스틱 지표의 과매도 구간 골든크로스를 포착하는 전략을 설명합니다.

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **스토캐스틱 크로스 전략**을 정의한다.

- **대상 시간 구간**: 09:00:00 ~ 15:18:00 (장 전체)
- **대상 종목**: 시가총액 차등 기준 (1,500억, 3,000억)
- **전략 타입**: 분봉 기반 스토캐스틱 골든크로스 전략
- **핵심 변수**: STOCHSK, STOCHSD, RSI, MACD, 분당거래대금
- **업데이트 이력**:
  - 초기 문서 작성: 스토캐스틱 크로스 전략

## 조건식

### 매수 조건식
```python
스토캐스틱상승 = (STOCHSK > STOCHSD and STOCHSK_N(1) <= STOCHSD_N(1))
과매도구간 = (STOCHSK_N(1) < 25 and STOCHSD_N(1) < 28)

if not (900 <= 시분초 <= 1518):
    매수 = False
elif not (1200 < 현재가 <= 45000):
    매수 = False
elif not (0.6 < 등락율 <= 24.0):
    매수 = False
elif not 스토캐스틱상승:
    매수 = False
elif not 과매도구간:
    매수 = False
elif 시가총액 < 1500:
    if not (RSI > 35 and RSI < 65):
        매수 = False
    elif not (MACD_N(1) < MACDS_N(1)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(25) * 1.5):
        매수 = False
    elif not (체결강도 > 120):
        매수 = False
    elif not (전일비 > 25):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
elif 시가총액 < 3000:
    if not (RSI > 38 and RSI < 65):
        매수 = False
    elif not (MACD_N(1) < MACDS_N(1)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(25) * 1.4):
        매수 = False
    elif not (체결강도 > 118):
        매수 = False
    elif not (전일비 > 30):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
else:
    if not (RSI > 40 and RSI < 65):
        매수 = False
    elif not (MACD_N(1) < MACDS_N(1)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(25) * 1.3):
        매수 = False
    elif not (체결강도 > 115):
        매수 = False
    elif not (전일비 > 35):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
```

### 매도 조건식
```python
스토캐스틱하락 = (STOCHSK < STOCHSD and STOCHSK_N(1) >= STOCHSD_N(1))
과매수구간 = (STOCHSK > 75 and STOCHSD > 72)

if 등락율 > 29.1:
    매도 = True
elif 수익률 >= 3.8:
    매도 = True
elif 수익률 <= -3.2:
    매도 = True
elif 최고수익률 - 수익률 >= 2.3:
    매도 = True
elif 보유시간 > 100:
    매도 = True
elif 스토캐스틱하락 and 과매수구간:
    매도 = True
elif RSI > 72:
    매도 = True
```

## 최적화 조건식

### 매수 최적화 조건식 - C_SC_M_BO

```python
스토캐스틱상승 = (STOCHSK > STOCHSD and STOCHSK_N(1) <= STOCHSD_N(1))
과매도구간 = (STOCHSK_N(1) < self.vars[5] and STOCHSD_N(1) < self.vars[6])  # 과매도 기준 최적화

if not (900 <= 시분초 <= 1518):
    매수 = False
elif not (self.vars[0] < 현재가 <= self.vars[1]):    # 현재가 범위 최적화
    매수 = False
elif not (self.vars[2] < 등락율 <= self.vars[3]):     # 등락율 범위 최적화
    매수 = False
elif not 스토캐스틱상승:
    매수 = False
elif not 과매도구간:
    매수 = False
elif 시가총액 < 1500:
    if not (RSI > self.vars[7] and RSI < self.vars[8]):  # RSI 범위 최적화
        매수 = False
    elif not (MACD_N(1) < MACDS_N(1)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(25) * self.vars[9]):  # 분당거래대금/평균 배수 최적화
        매수 = False
    elif not (체결강도 > self.vars[10]):  # 체결강도 최적화
        매수 = False
    elif not (전일비 > self.vars[11]):  # 전일비 최적화
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
elif 시가총액 < 3000:
    if not (RSI > 38 and RSI < self.vars[8]):
        매수 = False
    elif not (MACD_N(1) < MACDS_N(1)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(25) * 1.4):
        매수 = False
    elif not (체결강도 > 118):
        매수 = False
    elif not (전일비 > 30):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
else:
    if not (RSI > 40 and RSI < self.vars[8]):
        매수 = False
    elif not (MACD_N(1) < MACDS_N(1)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(25) * 1.3):
        매수 = False
    elif not (체결강도 > 115):
        매수 = False
    elif not (전일비 > 35):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
```

### 매도 최적화 조건식 - C_SC_M_SO

```python
스토캐스틱하락 = (STOCHSK < STOCHSD and STOCHSK_N(1) >= STOCHSD_N(1))
과매수구간 = (STOCHSK > self.vars[17] and STOCHSD > self.vars[18])  # 과매수 기준 최적화

if 등락율 > self.vars[12]:  # 최대 등락율 최적화
    매도 = True
elif 수익률 >= self.vars[13]:  # 목표 수익률 최적화
    매도 = True
elif 수익률 <= self.vars[14]:  # 손절 수익률 최적화
    매도 = True
elif 최고수익률 - 수익률 >= self.vars[15]:  # 고점 대비 하락폭 최적화
    매도 = True
elif 보유시간 > self.vars[16]:  # 보유시간 제한 최적화
    매도 = True
elif 스토캐스틱하락 and 과매수구간:
    매도 = True
elif RSI > self.vars[19]:  # RSI 과매수 기준 최적화
    매도 = True
```

### 매수·매도 통합 최적화 범위 - C_SC_M_OR

```python
# BOR 핵심 변수 (7개)
self.vars[0] = [[800, 1200, 1800], 1200]          # 현재가 하한
self.vars[1] = [[35000, 45000, 55000], 45000]     # 현재가 상한
self.vars[2] = [[0.3, 0.6, 1.2], 0.6]             # 등락율 하한
self.vars[3] = [[22.0, 24.0, 26.0], 24.0]         # 등락율 상한
self.vars[5] = [[20, 25, 30], 25]                 # STOCHSK 과매도 기준
self.vars[7] = [[30, 35, 45], 35]                 # RSI 하한
self.vars[10] = [[110, 120, 135], 120]            # 체결강도

# SOR 핵심 변수 (3개)
self.vars[13] = [[2.5, 3.8, 5.5], 3.8]            # 목표 수익률
self.vars[14] = [[-4.5, -3.2, -2.0], -3.2]        # 손절 수익률
self.vars[16] = [[80, 100, 140], 100]             # 보유시간 제한

# 총 경우의 수: 3 × 3 × 3 × 3 × 3 × 3 × 3 × 3 × 3 × 3 = 59,049
```

### 매수 최적화 범위 - C_SC_M_BOR

```python
self.vars[0] = [[800, 1800, 500], 1200]
self.vars[1] = [[35000, 55000, 10000], 45000]
self.vars[2] = [[0.3, 1.2, 0.3], 0.6]
self.vars[3] = [[22.0, 26.0, 2.0], 24.0]
self.vars[4] = [[1000, 2000, 500], 1500]
self.vars[5] = [[20, 30, 5], 25]
self.vars[6] = [[23, 33, 5], 28]
self.vars[7] = [[30, 45, 5], 35]
self.vars[8] = [[60, 70, 5], 65]
self.vars[9] = [[1.2, 1.8, 0.2], 1.5]
self.vars[10] = [[110, 135, 5], 120]
self.vars[11] = [[20, 40, 5], 25]
```

### 매도 최적화 범위 - C_SC_M_SOR

```python
self.vars[12] = [[28.5, 29.5, 0.5], 29.1]
self.vars[13] = [[2.5, 5.5, 1.0], 3.8]
self.vars[14] = [[-4.5, -2.0, 0.5], -3.2]
self.vars[15] = [[1.5, 3.5, 0.5], 2.3]
self.vars[16] = [[80, 140, 20], 100]
self.vars[17] = [[70, 80, 5], 75]
self.vars[18] = [[67, 77, 5], 72]
self.vars[19] = [[67, 77, 5], 72]
```

### 유전 알고리즘 범위 - C_SC_M_GAR

```python
self.vars[0] = [[800, 1200, 1800], 1200]
self.vars[1] = [[35000, 45000, 55000], 45000]
self.vars[2] = [[0.3, 0.6, 0.9, 1.2], 0.6]
self.vars[3] = [[22.0, 24.0, 26.0], 24.0]
self.vars[4] = [[1000, 1500, 2000], 1500]
self.vars[5] = [[20, 25, 30], 25]
self.vars[6] = [[23, 28, 33], 28]
self.vars[7] = [[30, 35, 40, 45], 35]
self.vars[8] = [[60, 65, 70], 65]
self.vars[9] = [[1.2, 1.4, 1.5, 1.6, 1.8], 1.5]
self.vars[10] = [[110, 120, 130, 135], 120]
self.vars[11] = [[20, 25, 30, 35, 40], 25]
self.vars[12] = [[28.5, 29.0, 29.1, 29.5], 29.1]
self.vars[13] = [[2.5, 3.0, 3.8, 4.5, 5.5], 3.8]
self.vars[14] = [[-4.5, -4.0, -3.5, -3.2, -2.5, -2.0], -3.2]
self.vars[15] = [[1.5, 2.0, 2.3, 2.8, 3.0, 3.5], 2.3]
self.vars[16] = [[80, 100, 120, 140], 100]
self.vars[17] = [[70, 75, 80], 75]
self.vars[18] = [[67, 72, 77], 72]
self.vars[19] = [[67, 72, 77], 72]
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


## 태그
`#분봉전략` `#Stochastic` `#크로스` `#900-1518` `#과매도반전` `#최적화`
