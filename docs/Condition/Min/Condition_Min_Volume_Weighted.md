# 조건식 - 거래량 가중 전략

## 소개
**조건식 이름**: 거래량 가중 전략
**거래 시간**: 900 ~ 1518
**목표**: 거래량 급증과 OBV 활용

## 조건식

### 매수 조건식
```python
# 거래량 분석
거래량비율 = 분당거래대금 / (분당거래대금평균(30) or 1)
누적거래량비율 = (누적분당매수수량(10) - 누적분당매도수량(10)) / (누적분당매수수량(10) + 누적분당매도수량(10) or 1)

# OBV 추세
OBV상승 = (OBV > OBV_N(1) > OBV_N(2) > OBV_N(3))
OBV급증 = (OBV > OBV_N(1) * 1.05)

if not (900 <= 시분초 <= 1518):
    매수 = False
elif not (1200 < 현재가 <= 50000):
    매수 = False
elif not (1.3 < 등락율 <= 27.5):
    매수 = False
elif not (거래량비율 > 2.0):
    매수 = False
elif not OBV상승:
    매수 = False

elif 시가총액 < 1500:
    if not (누적거래량비율 > 0.15):
        매수 = False
    elif not OBV급증:
        매수 = False
    elif not (AD > AD_N(1)):
        매수 = False
    elif not (MFI > 35 and MFI < 70):
        매수 = False
    elif not (RSI > 46 and RSI < 67):
        매수 = False
    elif not (체결강도 > 132):
        매수 = False
    elif not (전일비 > 37):
        매수 = False
    elif not (등락율각도(16) > 5):
        매수 = False
    elif not (최고분당매수수량(20) * 2.2 > 최고분당매도수량(20)):
        매수 = False

elif 시가총액 < 3000:
    if not (누적거래량비율 > 0.12):
        매수 = False
    elif not OBV급증:
        매수 = False
    elif not (AD > AD_N(1)):
        매수 = False
    elif not (MFI > 37 and MFI < 70):
        매수 = False
    elif not (RSI > 47 and RSI < 67):
        매수 = False
    elif not (체결강도 > 128):
        매수 = False
    elif not (전일비 > 41):
        매수 = False
    elif not (등락율각도(16) > 6):
        매수 = False
    elif not (최고분당매수수량(20) * 2.0 > 최고분당매도수량(20)):
        매수 = False

else:
    if not (누적거래량비율 > 0.10):
        매수 = False
    elif not OBV급증:
        매수 = False
    elif not (AD > AD_N(1)):
        매수 = False
    elif not (MFI > 39 and MFI < 70):
        매수 = False
    elif not (RSI > 48 and RSI < 67):
        매수 = False
    elif not (체결강도 > 124):
        매수 = False
    elif not (전일비 > 46):
        매수 = False
    elif not (등락율각도(16) > 7):
        매수 = False
    elif not (최고분당매수수량(20) * 1.8 > 최고분당매도수량(20)):
        매수 = False
```

### 매도 조건식
```python
# 거래량 감소
거래량감소 = (분당거래대금 < 분당거래대금평균(30) * 0.6)
OBV하락 = (OBV < OBV_N(1) < OBV_N(2))
누적매도우위 = (누적분당매도수량(10) > 누적분당매수수량(10) * 1.3)

if 등락율 > 29.9:
    매도 = True
elif 수익률 >= 6.0:
    매도 = True
elif 수익률 <= -2.2:
    매도 = True
elif 최고수익률 - 수익률 >= 4.0:
    매도 = True
elif 보유시간 > 150:
    매도 = True

elif 시가총액 < 1500:
    if 거래량감소 and OBV하락:
        매도 = True
    elif 누적매도우위:
        매도 = True
    elif AD < AD_N(1) < AD_N(2):
        매도 = True
    elif MFI < 25:
        매도 = True

elif 시가총액 < 3000:
    if 거래량감소 and OBV하락:
        매도 = True
    elif 누적매도우위:
        매도 = True
    elif AD < AD_N(1) < AD_N(2):
        매도 = True
    elif MFI < 27:
        매도 = True

else:
    if 거래량감소 and OBV하락:
        매도 = True
    elif 누적매도우위:
        매도 = True
    elif AD < AD_N(1) < AD_N(2):
        매도 = True
    elif MFI < 30:
        매도 = True
```

## 최적화 범위
```python
# BOR
self.vars[0] = [[900, 1800, 450], 1200]
self.vars[1] = [[40000, 60000, 10000], 50000]
self.vars[2] = [[0.9, 2.1, 0.4], 1.3]
self.vars[3] = [[25.5, 29.5, 2.0], 27.5]
self.vars[4] = [[1000, 2000, 500], 1500]
self.vars[5] = [[1.6, 2.8, 0.4], 2.0]
self.vars[6] = [[0.08, 0.22, 0.04], 0.15]
self.vars[7] = [[1.03, 1.08, 0.02], 1.05]
self.vars[8] = [[30, 45, 5], 35]
self.vars[9] = [[65, 75, 5], 70]
self.vars[10] = [[41, 56, 5], 46]
self.vars[11] = [[62, 72, 5], 67]
self.vars[12] = [[122, 147, 5], 132]
self.vars[13] = [[32, 62, 10], 37]
self.vars[14] = [[4, 9, 1], 5]
self.vars[15] = [[1.6, 2.8, 0.4], 2.2]

# SOR
self.vars[16] = [[29.4, 30.0, 0.3], 29.9]
self.vars[17] = [[4.5, 8.0, 1.0], 6.0]
self.vars[18] = [[-3.3, -1.5, 0.5], -2.2]
self.vars[19] = [[3.2, 5.5, 0.5], 4.0]
self.vars[20] = [[130, 190, 20], 150]
self.vars[21] = [[0.4, 0.8, 0.1], 0.6]
self.vars[22] = [[1.2, 1.6, 0.2], 1.3]
self.vars[23] = [[20, 35, 5], 25]

# GAR
self.vars[0] = [[900, 1200, 1800], 1200]
self.vars[1] = [[40000, 50000, 60000], 50000]
self.vars[2] = [[0.9, 1.3, 1.7, 2.1], 1.3]
self.vars[3] = [[25.5, 27.5, 29.5], 27.5]
self.vars[4] = [[1000, 1500, 2000], 1500]
self.vars[5] = [[1.6, 2.0, 2.4, 2.8], 2.0]
self.vars[6] = [[0.08, 0.12, 0.15, 0.18, 0.22], 0.15]
self.vars[7] = [[1.03, 1.05, 1.07, 1.08], 1.05]
self.vars[8] = [[30, 35, 40, 45], 35]
self.vars[9] = [[65, 70, 75], 70]
self.vars[10] = [[41, 46, 51, 56], 46]
self.vars[11] = [[62, 67, 72], 67]
self.vars[12] = [[122, 127, 132, 137, 142, 147], 132]
self.vars[13] = [[32, 37, 41, 46, 52, 62], 37]
self.vars[14] = [[4, 5, 6, 7, 8, 9], 5]
self.vars[15] = [[1.6, 2.0, 2.2, 2.4, 2.8], 2.2]
self.vars[16] = [[29.4, 29.7, 29.9, 30.0], 29.9]
self.vars[17] = [[4.5, 5.5, 6.0, 7.0, 8.0], 6.0]
self.vars[18] = [[-3.3, -2.9, -2.5, -2.2, -1.9, -1.5], -2.2]
self.vars[19] = [[3.2, 3.6, 4.0, 4.5, 5.0, 5.5], 4.0]
self.vars[20] = [[130, 150, 170, 190], 150]
self.vars[21] = [[0.4, 0.5, 0.6, 0.7, 0.8], 0.6]
self.vars[22] = [[1.2, 1.3, 1.4, 1.5, 1.6], 1.3]
self.vars[23] = [[20, 25, 30, 35], 25]
```

## 태그
`#분봉전략` `#거래량가중` `#OBV` `#AD` `#900-1518` `#MFI` `#최적화`
