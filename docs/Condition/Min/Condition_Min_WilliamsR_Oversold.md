# 조건식 - Williams %R 과매도 전략

## 소개
**조건식 이름**: Williams %R 과매도 전략
**거래 시간**: 900 ~ 1518
**목표**: WILLR 과매도 구간 반등 포착

## 조건식

### 매수 조건식
```python
WILLR반등 = (WILLR > -85 and WILLR_N(1) < -88)
WILLR과매도 = (WILLR_N(1) < -80)

if not (900 <= 시분초 <= 1518):
    매수 = False
elif not (900 < 현재가 <= 46000):
    매수 = False
elif not (0.85 < 등락율 <= 25.8):
    매수 = False
elif not WILLR반등:
    매수 = False
elif not WILLR과매도:
    매수 = False
elif 시가총액 < 1500:
    if not (WILLR > WILLR_N(1) > WILLR_N(2)):
        매수 = False
    elif not (RSI > 38 and RSI < 62):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(24) * 1.55):
        매수 = False
    elif not (체결강도 > 127):
        매수 = False
    elif not (전일비 > 27):
        매수 = False
    elif not (현재가 > 분봉시가):
        매수 = False
elif 시가총액 < 3000:
    if not (WILLR > WILLR_N(1) > WILLR_N(2)):
        매수 = False
    elif not (RSI > 40 and RSI < 62):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(24) * 1.45):
        매수 = False
    elif not (체결강도 > 124):
        매수 = False
    elif not (전일비 > 31):
        매수 = False
    elif not (현재가 > 분봉시가):
        매수 = False
else:
    if not (WILLR > WILLR_N(1) > WILLR_N(2)):
        매수 = False
    elif not (RSI > 42 and RSI < 62):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(24) * 1.38):
        매수 = False
    elif not (체결강도 > 121):
        매수 = False
    elif not (전일비 > 36):
        매수 = False
    elif not (현재가 > 분봉시가):
        매수 = False
```

### 매도 조건식
```python
WILLR과매수 = (WILLR > -12)

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 5.0:
    매도 = True
elif 수익률 <= -2.6:
    매도 = True
elif 최고수익률 - 수익률 >= 3.2:
    매도 = True
elif 보유시간 > 130:
    매도 = True
elif WILLR과매수:
    if WILLR < WILLR_N(1):
        매도 = True
elif WILLR < WILLR_N(1) < WILLR_N(2):
    if RSI > 71:
        매도 = True
```

## 최적화 범위
```python
# BOR
self.vars[0] = [[650, 1350, 350], 900]
self.vars[1] = [[36000, 56000, 10000], 46000]
self.vars[2] = [[0.5, 1.65, 0.45], 0.85]
self.vars[3] = [[23.8, 27.8, 2.0], 25.8]
self.vars[4] = [[1000, 2000, 500], 1500]
self.vars[5] = [[-92, -78, 4], -85]
self.vars[6] = [[-94, -82, 4], -88]
self.vars[7] = [[-88, -72, 4], -80]
self.vars[8] = [[33, 48, 5], 38]
self.vars[9] = [[57, 67, 5], 62]
self.vars[10] = [[1.3, 1.85, 0.15], 1.55]
self.vars[11] = [[117, 142, 5], 127]
self.vars[12] = [[22, 46, 6], 27]

# SOR
self.vars[13] = [[29.0, 29.6, 0.3], 29.5]
self.vars[14] = [[3.5, 7.0, 1.0], 5.0]
self.vars[15] = [[-3.7, -1.9, 0.5], -2.6]
self.vars[16] = [[2.4, 4.6, 0.5], 3.2]
self.vars[17] = [[110, 170, 20], 130]
self.vars[18] = [[-18, -6, 3], -12]
self.vars[19] = [[66, 76, 5], 71]

# GAR
self.vars[0] = [[650, 900, 1350], 900]
self.vars[1] = [[36000, 46000, 56000], 46000]
self.vars[2] = [[0.5, 0.85, 1.2, 1.65], 0.85]
self.vars[3] = [[23.8, 25.8, 27.8], 25.8]
self.vars[4] = [[1000, 1500, 2000], 1500]
self.vars[5] = [[-92, -88, -85, -82, -78], -85]
self.vars[6] = [[-94, -90, -88, -86, -82], -88]
self.vars[7] = [[-88, -84, -80, -76, -72], -80]
self.vars[8] = [[33, 38, 43, 48], 38]
self.vars[9] = [[57, 62, 67], 62]
self.vars[10] = [[1.3, 1.4, 1.5, 1.55, 1.7, 1.85], 1.55]
self.vars[11] = [[117, 122, 127, 132, 137, 142], 127]
self.vars[12] = [[22, 27, 31, 36, 41, 46], 27]
self.vars[13] = [[29.0, 29.2, 29.5, 29.6], 29.5]
self.vars[14] = [[3.5, 4.2, 5.0, 6.0, 7.0], 5.0]
self.vars[15] = [[-3.7, -3.2, -2.9, -2.6, -2.3, -1.9], -2.6]
self.vars[16] = [[2.4, 2.8, 3.2, 3.8, 4.2, 4.6], 3.2]
self.vars[17] = [[110, 130, 150, 170], 130]
self.vars[18] = [[-18, -15, -12, -9, -6], -12]
self.vars[19] = [[66, 69, 71, 73, 76], 71]
```

## 태그
`#분봉전략` `#WilliamsR` `#과매도반등` `#900-1518` `#WILLR` `#최적화`
