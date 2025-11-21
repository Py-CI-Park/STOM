# 조건식 - MFI 자금흐름 전략

- STOM 주식 자동거래에 사용하기 위한 분봉 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **MFI 자금흐름 전략**을 정의한다.

- **대상 시간 구간**: 09:00 ~ 15:18 (장 전체)
- **대상 종목**: 가격대 1,050~47,000원, 시가총액 차등 (1,500억/3,000억 기준)
- **전략 타입**: MFI 기반 자금 유입 감지 및 모멘텀 전략
- **핵심 변수**: MFI, OBV, 분당매수수량, 분당거래대금, 체결강도
- **업데이트 이력**:
  - 초기 문서 작성: MFI 자금흐름 전략

## 소개
**조건식 이름**: MFI 자금흐름 전략
**거래 시간**: 900 ~ 1518
**목표**: MFI 기반 자금 유입 감지

## 조건식

### 매수 조건식
```python
MFI상승 = (MFI > MFI_N(1) > MFI_N(2))
MFI과매도탈출 = (MFI > 25 and MFI_N(1) < 22)

if not (900 <= 시분초 <= 1518):
    매수 = False
elif not (1050 < 현재가 <= 47000):
    매수 = False
elif not (0.9 < 등락율 <= 25.5):
    매수 = False
elif not MFI상승:
    매수 = False
elif not (MFI > 20 and MFI < 65):
    매수 = False
elif 시가총액 < 1500:
    if not MFI과매도탈출:
        매수 = False
    elif not (OBV > OBV_N(1)):
        매수 = False
    elif not (분당매수수량 > 분당매도수량 * 1.4):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(26) * 1.7):
        매수 = False
    elif not (체결강도 > 128):
        매수 = False
    elif not (전일비 > 32):
        매수 = False
    elif not (RSI > 42):
        매수 = False
elif 시가총액 < 3000:
    if not MFI과매도탈출:
        매수 = False
    elif not (OBV > OBV_N(1)):
        매수 = False
    elif not (분당매수수량 > 분당매도수량 * 1.3):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(26) * 1.6):
        매수 = False
    elif not (체결강도 > 124):
        매수 = False
    elif not (전일비 > 37):
        매수 = False
    elif not (RSI > 44):
        매수 = False
else:
    if not MFI과매도탈출:
        매수 = False
    elif not (OBV > OBV_N(1)):
        매수 = False
    elif not (분당매수수량 > 분당매도수량 * 1.2):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(26) * 1.5):
        매수 = False
    elif not (체결강도 > 120):
        매수 = False
    elif not (전일비 > 42):
        매수 = False
    elif not (RSI > 46):
        매수 = False
```

### 매도 조건식
```python
MFI하락 = (MFI < MFI_N(1) < MFI_N(2))
MFI과매수진입 = (MFI > 78)

if 등락율 > 29.3:
    매도 = True
elif 수익률 >= 4.5:
    매도 = True
elif 수익률 <= -2.9:
    매도 = True
elif 최고수익률 - 수익률 >= 2.8:
    매도 = True
elif 보유시간 > 115:
    매도 = True
elif MFI하락 and MFI과매수진입:
    매도 = True
elif OBV < OBV_N(1) < OBV_N(2):
    if 분당매도수량 > 분당매수수량 * 1.5:
        매도 = True
```

## 최적화 범위
```python
# BOR
self.vars[0] = [[750, 1600, 425], 1050]
self.vars[1] = [[37000, 57000, 10000], 47000]
self.vars[2] = [[0.5, 1.7, 0.4], 0.9]
self.vars[3] = [[23.5, 27.5, 2.0], 25.5]
self.vars[4] = [[1000, 2000, 500], 1500]
self.vars[5] = [[18, 28, 5], 25]
self.vars[6] = [[18, 27, 3], 22]
self.vars[7] = [[15, 25, 5], 20]
self.vars[8] = [[60, 70, 5], 65]
self.vars[9] = [[1.1, 1.6, 0.1], 1.4]
self.vars[10] = [[1.4, 2.0, 0.2], 1.7]
self.vars[11] = [[118, 143, 5], 128]
self.vars[12] = [[27, 52, 5], 32]
self.vars[13] = [[37, 51, 4], 42]

# SOR
self.vars[14] = [[28.8, 29.5, 0.35], 29.3]
self.vars[15] = [[3.0, 6.5, 1.0], 4.5]
self.vars[16] = [[-4.0, -2.2, 0.5], -2.9]
self.vars[17] = [[2.0, 4.0, 0.5], 2.8]
self.vars[18] = [[95, 155, 20], 115]
self.vars[19] = [[73, 83, 5], 78]
self.vars[20] = [[1.3, 1.8, 0.1], 1.5]

# GAR
self.vars[0] = [[750, 1050, 1600], 1050]
self.vars[1] = [[37000, 47000, 57000], 47000]
self.vars[2] = [[0.5, 0.9, 1.3, 1.7], 0.9]
self.vars[3] = [[23.5, 25.5, 27.5], 25.5]
self.vars[4] = [[1000, 1500, 2000], 1500]
self.vars[5] = [[18, 23, 25, 28], 25]
self.vars[6] = [[18, 20, 22, 24, 27], 22]
self.vars[7] = [[15, 20, 25], 20]
self.vars[8] = [[60, 65, 70], 65]
self.vars[9] = [[1.1, 1.2, 1.3, 1.4, 1.5, 1.6], 1.4]
self.vars[10] = [[1.4, 1.5, 1.6, 1.7, 1.8, 2.0], 1.7]
self.vars[11] = [[118, 123, 128, 133, 138, 143], 128]
self.vars[12] = [[27, 32, 37, 42, 47, 52], 32]
self.vars[13] = [[37, 40, 42, 45, 48, 51], 42]
self.vars[14] = [[28.8, 29.0, 29.3, 29.5], 29.3]
self.vars[15] = [[3.0, 4.0, 4.5, 5.5, 6.5], 4.5]
self.vars[16] = [[-4.0, -3.5, -3.0, -2.9, -2.5, -2.2], -2.9]
self.vars[17] = [[2.0, 2.5, 2.8, 3.2, 3.5, 4.0], 2.8]
self.vars[18] = [[95, 115, 135, 155], 115]
self.vars[19] = [[73, 76, 78, 80, 83], 78]
self.vars[20] = [[1.3, 1.4, 1.5, 1.6, 1.7, 1.8], 1.5]
```

## 태그
`#분봉전략` `#MFI` `#자금흐름` `#900-1518` `#OBV` `#최적화`
