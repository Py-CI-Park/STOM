# 조건식 - ATR 돌파 전략

## 목차
- [소개](#소개)
- [전략 개요](#전략-개요)
- [조건식](#조건식)
- [최적화 조건식](#최적화-조건식)
- [태그](#태그)

---

## 소개

**조건식 이름**: ATR 돌파 전략 (ATR Breakout Strategy)
**타입**: 분봉 데이터 기반 변동성 돌파 전략
**거래 시간**: 900 ~ 1518 (09:00 ~ 15:18)
**목표**: ATR 기반 변동성 확대 구간 포착

---

## 전략 개요

### 핵심 아이디어
Average True Range(ATR)를 활용하여 변동성이 확대되는 구간을 포착합니다. ATR이 평균보다 크고, 현재가가 ATR 범위를 돌파할 때 진입합니다.

### 주요 특징
1. **ATR 변동성 분석**: ATR 값의 증가 확인
2. **가격 돌파**: 고가 + ATR 돌파 신호
3. **거래량 확인**: 분당거래대금 급증 동반
4. **기술적 지표 보조**: RSI, MACD 결합

---

## 조건식

### 매수 조건식

```python
ATR배율 = ATR / (이동평균(60) * 0.01 or 1)
ATR증가율 = ATR / ATR_N(1)
돌파가격 = 최고분봉고가(20, 1) + ATR * 0.5

if not (900 <= 시분초 <= 1518):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (0.8 < 등락율 <= 25.0):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False

elif 시가총액 < 1500:
    if not (ATR배율 > 2.0):
        매수 = False
    elif not (ATR증가율 > 1.2):
        매수 = False
    elif not (현재가 > 돌파가격):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(30) * 2.0):
        매수 = False
    elif not (RSI > 50 and RSI < 70):
        매수 = False
    elif not (MACD > MACDS):
        매수 = False
    elif not (체결강도 > 130):
        매수 = False
    elif not (전일비 > 30):
        매수 = False
    elif not (당일거래대금 > 10 * 100):
        매수 = False
    elif not (등락율각도(10) > 3):
        매수 = False

elif 시가총액 < 3000:
    if not (ATR배율 > 1.8):
        매수 = False
    elif not (ATR증가율 > 1.15):
        매수 = False
    elif not (현재가 > 돌파가격):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.8):
        매수 = False
    elif not (RSI > 50 and RSI < 70):
        매수 = False
    elif not (MACD > MACDS):
        매수 = False
    elif not (체결강도 > 125):
        매수 = False
    elif not (전일비 > 35):
        매수 = False
    elif not (당일거래대금 > 30 * 100):
        매수 = False
    elif not (등락율각도(10) > 4):
        매수 = False

else:
    if not (ATR배율 > 1.6):
        매수 = False
    elif not (ATR증가율 > 1.12):
        매수 = False
    elif not (현재가 > 돌파가격):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.6):
        매수 = False
    elif not (RSI > 50 and RSI < 70):
        매수 = False
    elif not (MACD > MACDS):
        매수 = False
    elif not (체결강도 > 120):
        매수 = False
    elif not (전일비 > 40):
        매수 = False
    elif not (당일거래대금 > 50 * 100):
        매수 = False
    elif not (등락율각도(10) > 5):
        매수 = False
```

### 매도 조건식

```python
ATR하한 = 현재가 - ATR * 1.5

if 등락율 > 29.0:
    매도 = True
elif 수익률 >= 4.0:
    매도 = True
elif 수익률 <= -3.5:
    매도 = True
elif 최고수익률 - 수익률 >= 2.5:
    매도 = True
elif 보유시간 > 120:  # 2시간
    매도 = True

elif 시가총액 < 1500:
    if 현재가 < ATR하한:
        매도 = True
    elif RSI > 75:
        매도 = True
    elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    elif 체결강도 < 80:
        매도 = True

elif 시가총액 < 3000:
    if 현재가 < ATR하한:
        매도 = True
    elif RSI > 73:
        매도 = True
    elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    elif 체결강도 < 85:
        매도 = True

else:
    if 현재가 < ATR하한:
        매도 = True
    elif RSI > 70:
        매도 = True
    elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    elif 체결강도 < 90:
        매도 = True
```

---

## 최적화 조건식

### 매수 최적화 조건식

```python
ATR배율 = ATR / (이동평균(60) * 0.01 or 1)
ATR증가율 = ATR / ATR_N(1)
돌파가격 = 최고분봉고가(20, 1) + ATR * self.vars[5]

if not (900 <= 시분초 <= 1518):
    매수 = False
elif not (self.vars[0] < 현재가 <= self.vars[1]):
    매수 = False
elif not (self.vars[2] < 등락율 <= self.vars[3]):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 시가총액 < self.vars[4]:
    if not (ATR배율 > self.vars[6]):
        매수 = False
    elif not (ATR증가율 > self.vars[7]):
        매수 = False
    elif not (현재가 > 돌파가격):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(30) * self.vars[8]):
        매수 = False
    elif not (RSI > self.vars[9] and RSI < self.vars[10]):
        매수 = False
    elif not (MACD > MACDS):
        매수 = False
    elif not (체결강도 > self.vars[11]):
        매수 = False
    elif not (전일비 > self.vars[12]):
        매수 = False
    elif not (당일거래대금 > self.vars[13] * 100):
        매수 = False
    elif not (등락율각도(10) > self.vars[14]):
        매수 = False
```

### 매수 최적화 범위 (BOR)

```python
self.vars[0] = [[500, 1500, 500], 1000]
self.vars[1] = [[40000, 60000, 10000], 50000]
self.vars[2] = [[0.5, 1.5, 0.5], 0.8]
self.vars[3] = [[23.0, 27.0, 2.0], 25.0]
self.vars[4] = [[1000, 2000, 500], 1500]
self.vars[5] = [[0.3, 0.7, 0.1], 0.5]
self.vars[6] = [[1.5, 2.5, 0.5], 2.0]
self.vars[7] = [[1.1, 1.3, 0.05], 1.2]
self.vars[8] = [[1.5, 2.5, 0.5], 2.0]
self.vars[9] = [[45, 55, 5], 50]
self.vars[10] = [[65, 75, 5], 70]
self.vars[11] = [[115, 145, 10], 130]
self.vars[12] = [[25, 45, 5], 30]
self.vars[13] = [[5, 20, 5], 10]
self.vars[14] = [[2, 6, 1], 3]
```

### 매도 최적화 조건식

```python
ATR하한 = 현재가 - ATR * self.vars[19]

if 등락율 > self.vars[15]:
    매도 = True
elif 수익률 >= self.vars[16]:
    매도 = True
elif 수익률 <= self.vars[17]:
    매도 = True
elif 최고수익률 - 수익률 >= self.vars[18]:
    매도 = True
elif 보유시간 > self.vars[20]:
    매도 = True
elif 시가총액 < self.vars[4]:
    if 현재가 < ATR하한:
        매도 = True
    elif RSI > self.vars[21]:
        매도 = True
    elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    elif 체결강도 < self.vars[22]:
        매도 = True
```

### 매도 최적화 범위 (SOR)

```python
self.vars[15] = [[28.0, 29.5, 0.5], 29.0]
self.vars[16] = [[2.5, 6.0, 1.0], 4.0]
self.vars[17] = [[-5.0, -2.0, 1.0], -3.5]
self.vars[18] = [[1.5, 4.0, 0.5], 2.5]
self.vars[19] = [[1.0, 2.0, 0.5], 1.5]
self.vars[20] = [[90, 180, 30], 120]
self.vars[21] = [[70, 80, 5], 75]
self.vars[22] = [[70, 100, 10], 80]
```

### 통합 최적화 범위 (OR)

```python
# 매수 조건
self.vars[0] = [[500, 1500, 500], 1000]
self.vars[1] = [[40000, 60000, 10000], 50000]
self.vars[2] = [[0.5, 1.5, 0.5], 0.8]
self.vars[3] = [[23.0, 27.0, 2.0], 25.0]
self.vars[4] = [[1000, 2000, 500], 1500]
self.vars[5] = [[0.3, 0.7, 0.1], 0.5]
self.vars[6] = [[1.5, 2.5, 0.5], 2.0]
self.vars[7] = [[1.1, 1.3, 0.05], 1.2]
self.vars[8] = [[1.5, 2.5, 0.5], 2.0]
self.vars[9] = [[45, 55, 5], 50]
self.vars[10] = [[65, 75, 5], 70]
self.vars[11] = [[115, 145, 10], 130]
self.vars[12] = [[25, 45, 5], 30]
self.vars[13] = [[5, 20, 5], 10]
self.vars[14] = [[2, 6, 1], 3]

# 매도 조건
self.vars[15] = [[28.0, 29.5, 0.5], 29.0]
self.vars[16] = [[2.5, 6.0, 1.0], 4.0]
self.vars[17] = [[-5.0, -2.0, 1.0], -3.5]
self.vars[18] = [[1.5, 4.0, 0.5], 2.5]
self.vars[19] = [[1.0, 2.0, 0.5], 1.5]
self.vars[20] = [[90, 180, 30], 120]
self.vars[21] = [[70, 80, 5], 75]
self.vars[22] = [[70, 100, 10], 80]
```

### GA 최적화 범위 (GAR)

```python
self.vars[0] = [[500, 1000, 1500], 1000]
self.vars[1] = [[40000, 50000, 60000], 50000]
self.vars[2] = [[0.5, 0.8, 1.0, 1.5], 0.8]
self.vars[3] = [[23.0, 25.0, 27.0], 25.0]
self.vars[4] = [[1000, 1500, 2000], 1500]
self.vars[5] = [[0.3, 0.4, 0.5, 0.6, 0.7], 0.5]
self.vars[6] = [[1.5, 2.0, 2.5], 2.0]
self.vars[7] = [[1.1, 1.15, 1.2, 1.25, 1.3], 1.2]
self.vars[8] = [[1.5, 2.0, 2.5], 2.0]
self.vars[9] = [[45, 50, 55], 50]
self.vars[10] = [[65, 70, 75], 70]
self.vars[11] = [[115, 130, 145], 130]
self.vars[12] = [[25, 30, 35, 40, 45], 30]
self.vars[13] = [[5, 10, 15, 20], 10]
self.vars[14] = [[2, 3, 4, 5, 6], 3]
self.vars[15] = [[28.0, 28.5, 29.0, 29.5], 29.0]
self.vars[16] = [[2.5, 3.0, 4.0, 5.0, 6.0], 4.0]
self.vars[17] = [[-5.0, -4.0, -3.5, -3.0, -2.0], -3.5]
self.vars[18] = [[1.5, 2.0, 2.5, 3.0, 3.5, 4.0], 2.5]
self.vars[19] = [[1.0, 1.5, 2.0], 1.5]
self.vars[20] = [[90, 120, 150, 180], 120]
self.vars[21] = [[70, 75, 80], 75]
self.vars[22] = [[70, 80, 90, 100], 80]
```

---

## 태그

`#분봉전략` `#ATR` `#변동성돌파` `#900-1518` `#기술적지표` `#최적화`
