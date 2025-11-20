# 조건식 - CCI 극단값 반전 전략

- STOM 주식 자동거래에 사용하기 위한 분봉 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **CCI 극단값 반전 전략**을 정의한다.

- **대상 시간 구간**: 09:00 ~ 15:18 (장 전체)
- **대상 종목**: 가격대 950~42,000원, 시가총액 차등 (1,500억/3,000억 기준)
- **전략 타입**: CCI 과매도 극단값 반등 포착 전략
- **핵심 변수**: CCI, RSI, 분당거래대금, 체결강도, 등락율각도
- **업데이트 이력**:
  - 초기 문서 작성: CCI 극단값 반전 전략

## 소개
**조건식 이름**: CCI 극단값 반전 전략
**거래 시간**: 900 ~ 1518
**목표**: CCI 과매도 극단값에서 반등 포착

## 조건식

### 매수 조건식
```python
CCI반등 = (CCI > -100 and CCI_N(1) < -100)
CCI상승 = (CCI > CCI_N(1) > CCI_N(2))

if not (900 <= 시분초 <= 1518):
    매수 = False
elif not (950 < 현재가 <= 42000):
    매수 = False
elif not (0.7 < 등락율 <= 26.0):
    매수 = False
elif not (CCI_N(1) < -150):
    매수 = False
elif not CCI반등:
    매수 = False
elif 시가총액 < 1500:
    if not CCI상승:
        매수 = False
    elif not (RSI > 30 and RSI < 60):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(28) * 1.6):
        매수 = False
    elif not (체결강도 > 125):
        매수 = False
    elif not (전일비 > 28):
        매수 = False
    elif not (등락율각도(12) > 2):
        매수 = False
elif 시가총액 < 3000:
    if not CCI상승:
        매수 = False
    elif not (RSI > 32 and RSI < 60):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(28) * 1.5):
        매수 = False
    elif not (체결강도 > 122):
        매수 = False
    elif not (전일비 > 32):
        매수 = False
    elif not (등락율각도(12) > 3):
        매수 = False
else:
    if not CCI상승:
        매수 = False
    elif not (RSI > 35 and RSI < 60):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(28) * 1.4):
        매수 = False
    elif not (체결강도 > 118):
        매수 = False
    elif not (전일비 > 37):
        매수 = False
    elif not (등락율각도(12) > 4):
        매수 = False
```

### 매도 조건식
```python
CCI과매수 = (CCI > 150)
CCI하락전환 = (CCI < CCI_N(1) < CCI_N(2))

if 등락율 > 29.2:
    매도 = True
elif 수익률 >= 4.2:
    매도 = True
elif 수익률 <= -3.0:
    매도 = True
elif 최고수익률 - 수익률 >= 2.6:
    매도 = True
elif 보유시간 > 110:
    매도 = True
elif CCI과매수 and CCI하락전환:
    매도 = True
elif CCI < -100 and CCI_N(1) >= -100:
    매도 = True
```

## 최적화 범위
```python
# BOR
self.vars[0] = [[700, 1400, 350], 950]
self.vars[1] = [[32000, 52000, 10000], 42000]
self.vars[2] = [[0.4, 1.4, 0.5], 0.7]
self.vars[3] = [[24.0, 28.0, 2.0], 26.0]
self.vars[4] = [[1000, 2000, 500], 1500]
self.vars[5] = [[-180, -120, 20], -150]
self.vars[6] = [[-120, -80, 20], -100]
self.vars[7] = [[25, 40, 5], 30]
self.vars[8] = [[55, 65, 5], 60]
self.vars[9] = [[1.3, 1.9, 0.2], 1.6]
self.vars[10] = [[115, 140, 5], 125]
self.vars[11] = [[23, 42, 5], 28]
self.vars[12] = [[1, 5, 1], 2]

# SOR
self.vars[13] = [[28.7, 29.5, 0.4], 29.2]
self.vars[14] = [[2.8, 6.0, 1.0], 4.2]
self.vars[15] = [[-4.2, -2.2, 0.5], -3.0]
self.vars[16] = [[1.8, 3.8, 0.5], 2.6]
self.vars[17] = [[90, 150, 20], 110]
self.vars[18] = [[130, 180, 25], 150]

# GAR
self.vars[0] = [[700, 950, 1400], 950]
self.vars[1] = [[32000, 42000, 52000], 42000]
self.vars[2] = [[0.4, 0.7, 1.0, 1.4], 0.7]
self.vars[3] = [[24.0, 26.0, 28.0], 26.0]
self.vars[4] = [[1000, 1500, 2000], 1500]
self.vars[5] = [[-180, -160, -150, -140, -120], -150]
self.vars[6] = [[-120, -100, -80], -100]
self.vars[7] = [[25, 30, 35, 40], 30]
self.vars[8] = [[55, 60, 65], 60]
self.vars[9] = [[1.3, 1.4, 1.5, 1.6, 1.7, 1.9], 1.6]
self.vars[10] = [[115, 125, 135, 140], 125]
self.vars[11] = [[23, 28, 33, 37, 42], 28]
self.vars[12] = [[1, 2, 3, 4, 5], 2]
self.vars[13] = [[28.7, 29.0, 29.2, 29.5], 29.2]
self.vars[14] = [[2.8, 3.5, 4.2, 5.0, 6.0], 4.2]
self.vars[15] = [[-4.2, -3.8, -3.5, -3.0, -2.7, -2.2], -3.0]
self.vars[16] = [[1.8, 2.2, 2.6, 3.0, 3.5, 3.8], 2.6]
self.vars[17] = [[90, 110, 130, 150], 110]
self.vars[18] = [[130, 150, 165, 180], 150]
```

## 태그
`#분봉전략` `#CCI` `#극단값반전` `#900-1518` `#과매도` `#최적화`
