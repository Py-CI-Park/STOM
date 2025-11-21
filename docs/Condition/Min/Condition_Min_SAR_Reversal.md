# 조건식 - Parabolic SAR 반전 전략

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 소개

**조건식 이름**: Parabolic SAR 반전 전략

이 문서는 Parabolic SAR 지표의 반전점에서 추세 전환을 포착하는 전략을 설명합니다.

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **Parabolic SAR Reversal (SAR 반전 전략)**을 정의한다.

- **대상 시간 구간**: 09:00:00 ~ 15:18:00 (장 전체)
- **대상 종목**: 시가총액 차등 기준 (1,500억, 3,000억)
- **전략 타입**: 분봉 기반 SAR 반전 포착 전략
- **핵심 변수**: Parabolic SAR, RSI, MACD, 분당거래대금
- **업데이트 이력**:
  - 초기 문서 작성: Parabolic SAR 반전 전략

## 조건식

### 매수 조건식
```python
SAR상향돌파 = (현재가 > SAR and 현재가N(1) <= SAR_N(1))
SAR하락추세 = (SAR_N(1) > 현재가N(1))

if not (900 <= 시분초 <= 1518):
    매수 = False
elif not (1100 < 현재가 <= 44000):
    매수 = False
elif not (1.0 < 등락율 <= 24.5):
    매수 = False
elif not SAR상향돌파:
    매수 = False
elif not SAR하락추세:
    매수 = False
elif 시가총액 < 1500:
    if not (RSI > 45 and RSI < 68):
        매수 = False
    elif not (MACD > MACD_N(1)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(27) * 1.5):
        매수 = False
    elif not (체결강도 > 126):
        매수 = False
    elif not (전일비 > 30):
        매수 = False
    elif not (등락율각도(11) > 3):
        매수 = False
elif 시가총액 < 3000:
    if not (RSI > 47 and RSI < 68):
        매수 = False
    elif not (MACD > MACD_N(1)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(27) * 1.4):
        매수 = False
    elif not (체결강도 > 123):
        매수 = False
    elif not (전일비 > 34):
        매수 = False
    elif not (등락율각도(11) > 4):
        매수 = False
else:
    if not (RSI > 48 and RSI < 68):
        매수 = False
    elif not (MACD > MACD_N(1)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(27) * 1.3):
        매수 = False
    elif not (체결강도 > 119):
        매수 = False
    elif not (전일비 > 39):
        매수 = False
    elif not (등락율각도(11) > 5):
        매수 = False
```

### 매도 조건식
```python
SAR하향돌파 = (현재가 < SAR and 현재가N(1) >= SAR_N(1))

if 등락율 > 29.4:
    매도 = True
elif 수익률 >= 4.8:
    매도 = True
elif 수익률 <= -2.7:
    매도 = True
elif 최고수익률 - 수익률 >= 3.0:
    매도 = True
elif 보유시간 > 125:
    매도 = True
elif SAR하향돌파:
    매도 = True
elif RSI > 74:
    매도 = True
```

## 최적화 범위
```python
# BOR
self.vars[0] = [[800, 1600, 400], 1100]
self.vars[1] = [[34000, 54000, 10000], 44000]
self.vars[2] = [[0.6, 1.8, 0.4], 1.0]
self.vars[3] = [[22.5, 26.5, 2.0], 24.5]
self.vars[4] = [[1000, 2000, 500], 1500]
self.vars[5] = [[40, 55, 5], 45]
self.vars[6] = [[63, 73, 5], 68]
self.vars[7] = [[1.2, 1.8, 0.2], 1.5]
self.vars[8] = [[116, 141, 5], 126]
self.vars[9] = [[25, 45, 5], 30]
self.vars[10] = [[2, 6, 1], 3]

# SOR
self.vars[11] = [[28.9, 29.5, 0.3], 29.4]
self.vars[12] = [[3.2, 6.8, 1.0], 4.8]
self.vars[13] = [[-3.9, -2.0, 0.5], -2.7]
self.vars[14] = [[2.2, 4.2, 0.5], 3.0]
self.vars[15] = [[105, 165, 20], 125]
self.vars[16] = [[69, 79, 5], 74]

# GAR
self.vars[0] = [[800, 1100, 1600], 1100]
self.vars[1] = [[34000, 44000, 54000], 44000]
self.vars[2] = [[0.6, 1.0, 1.4, 1.8], 1.0]
self.vars[3] = [[22.5, 24.5, 26.5], 24.5]
self.vars[4] = [[1000, 1500, 2000], 1500]
self.vars[5] = [[40, 45, 50, 55], 45]
self.vars[6] = [[63, 68, 73], 68]
self.vars[7] = [[1.2, 1.3, 1.4, 1.5, 1.6, 1.8], 1.5]
self.vars[8] = [[116, 121, 126, 131, 136, 141], 126]
self.vars[9] = [[25, 30, 35, 40, 45], 30]
self.vars[10] = [[2, 3, 4, 5, 6], 3]
self.vars[11] = [[28.9, 29.2, 29.4, 29.5], 29.4]
self.vars[12] = [[3.2, 4.0, 4.8, 5.5, 6.8], 4.8]
self.vars[13] = [[-3.9, -3.5, -3.0, -2.7, -2.5, -2.0], -2.7]
self.vars[14] = [[2.2, 2.6, 3.0, 3.5, 4.0, 4.2], 3.0]
self.vars[15] = [[105, 125, 145, 165], 125]
self.vars[16] = [[69, 72, 74, 76, 79], 74]
```

## 태그
`#분봉전략` `#SAR` `#추세반전` `#900-1518` `#ParabolicSAR` `#최적화`
