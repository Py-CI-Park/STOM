# 조건식 - ROC 모멘텀 전략

## 소개
**조건식 이름**: ROC 모멘텀 전략
**거래 시간**: 900 ~ 1518
**목표**: ROC 가속도로 가격 모멘텀 포착

## 조건식

### 매수 조건식
```python
ROC상승 = (ROC > ROC_N(1) > ROC_N(2))
ROC양전환 = (ROC > 0 and ROC_N(1) < 0)

if not (900 <= 시분초 <= 1518):
    매수 = False
elif not (1000 < 현재가 <= 48000):
    매수 = False
elif not (1.1 < 등락율 <= 26.3):
    매수 = False
elif not ROC상승:
    매수 = False
elif not (ROC > 0):
    매수 = False
elif 시가총액 < 1500:
    if not (ROC > 2.0):
        매수 = False
    elif not (MOM > 0):
        매수 = False
    elif not (RSI > 48 and RSI < 66):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(29) * 1.65):
        매수 = False
    elif not (체결강도 > 129):
        매수 = False
    elif not (전일비 > 33):
        매수 = False
    elif not (등락율각도(13) > 4):
        매수 = False
elif 시가총액 < 3000:
    if not (ROC > 1.8):
        매수 = False
    elif not (MOM > 0):
        매수 = False
    elif not (RSI > 49 and RSI < 66):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(29) * 1.55):
        매수 = False
    elif not (체결강도 > 125):
        매수 = False
    elif not (전일비 > 38):
        매수 = False
    elif not (등락율각도(13) > 5):
        매수 = False
else:
    if not (ROC > 1.6):
        매수 = False
    elif not (MOM > 0):
        매수 = False
    elif not (RSI > 50 and RSI < 66):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(29) * 1.48):
        매수 = False
    elif not (체결강도 > 122):
        매수 = False
    elif not (전일비 > 43):
        매수 = False
    elif not (등락율각도(13) > 6):
        매수 = False
```

### 매도 조건식
```python
ROC하락 = (ROC < ROC_N(1) < ROC_N(2))
ROC음전환 = (ROC < 0 and ROC_N(1) > 0)

if 등락율 > 29.6:
    매도 = True
elif 수익률 >= 5.3:
    매도 = True
elif 수익률 <= -2.5:
    매도 = True
elif 최고수익률 - 수익률 >= 3.4:
    매도 = True
elif 보유시간 > 135:
    매도 = True
elif ROC음전환:
    매도 = True
elif ROC하락:
    if ROC < -1.0:
        매도 = True
elif MOM < 0 and MOM_N(1) >= 0:
    매도 = True
```

## 최적화 범위
```python
# BOR
self.vars[0] = [[700, 1500, 400], 1000]
self.vars[1] = [[38000, 58000, 10000], 48000]
self.vars[2] = [[0.7, 1.9, 0.4], 1.1]
self.vars[3] = [[24.3, 28.3, 2.0], 26.3]
self.vars[4] = [[1000, 2000, 500], 1500]
self.vars[5] = [[1.4, 2.8, 0.4], 2.0]
self.vars[6] = [[43, 58, 5], 48]
self.vars[7] = [[61, 71, 5], 66]
self.vars[8] = [[1.35, 1.95, 0.2], 1.65]
self.vars[9] = [[119, 144, 5], 129]
self.vars[10] = [[28, 53, 5], 33]
self.vars[11] = [[3, 7, 1], 4]

# SOR
self.vars[12] = [[29.1, 29.7, 0.3], 29.6]
self.vars[13] = [[3.8, 7.3, 1.0], 5.3]
self.vars[14] = [[-3.6, -1.8, 0.5], -2.5]
self.vars[15] = [[2.6, 4.8, 0.5], 3.4]
self.vars[16] = [[115, 175, 20], 135]
self.vars[17] = [[-1.5, -0.5, 0.5], -1.0]

# GAR
self.vars[0] = [[700, 1000, 1500], 1000]
self.vars[1] = [[38000, 48000, 58000], 48000]
self.vars[2] = [[0.7, 1.1, 1.5, 1.9], 1.1]
self.vars[3] = [[24.3, 26.3, 28.3], 26.3]
self.vars[4] = [[1000, 1500, 2000], 1500]
self.vars[5] = [[1.4, 1.8, 2.0, 2.4, 2.8], 2.0]
self.vars[6] = [[43, 48, 53, 58], 48]
self.vars[7] = [[61, 66, 71], 66]
self.vars[8] = [[1.35, 1.5, 1.65, 1.8, 1.95], 1.65]
self.vars[9] = [[119, 124, 129, 134, 139, 144], 129]
self.vars[10] = [[28, 33, 38, 43, 48, 53], 33]
self.vars[11] = [[3, 4, 5, 6, 7], 4]
self.vars[12] = [[29.1, 29.4, 29.6, 29.7], 29.6]
self.vars[13] = [[3.8, 4.5, 5.3, 6.2, 7.3], 5.3]
self.vars[14] = [[-3.6, -3.2, -2.8, -2.5, -2.2, -1.8], -2.5]
self.vars[15] = [[2.6, 3.0, 3.4, 3.9, 4.4, 4.8], 3.4]
self.vars[16] = [[115, 135, 155, 175], 135]
self.vars[17] = [[-1.5, -1.0, -0.5], -1.0]
```

## 태그
`#분봉전략` `#ROC` `#모멘텀가속` `#900-1518` `#MOM` `#최적화`
