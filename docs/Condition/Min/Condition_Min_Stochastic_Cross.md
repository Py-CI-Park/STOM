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

## 최적화 범위
```python
# BOR
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

# SOR
self.vars[12] = [[28.5, 29.5, 0.5], 29.1]
self.vars[13] = [[2.5, 5.5, 1.0], 3.8]
self.vars[14] = [[-4.5, -2.0, 0.5], -3.2]
self.vars[15] = [[1.5, 3.5, 0.5], 2.3]
self.vars[16] = [[80, 140, 20], 100]
self.vars[17] = [[70, 80, 5], 75]
self.vars[18] = [[67, 77, 5], 72]
self.vars[19] = [[67, 77, 5], 72]

# GAR
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

## 태그
`#분봉전략` `#Stochastic` `#크로스` `#900-1518` `#과매도반전` `#최적화`
