# 조건식 (Condition) - 분봉(Minute) 기반

- STOM 주식 자동거래에 사용하기 위한 분봉 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
- [Condition - Min MACD GoldenCross](#condition---min-macd-goldencross)
  - [전략 개요](#전략-개요)
  - [조건식](#조건식)
  - [최적화 조건식](#최적화-조건식)
  - [조건식 개선 방향 연구](#조건식-개선-방향-연구)
  - [태그](#태그)

## 소개

이 문서는 STOM 주식 자동거래 시스템에서 MACD 골든크로스 전략(MACD Golden Cross)을 위한 조건식과 최적화 범위를 제공합니다. MACD가 시그널선을 상향 돌파하는 순간을 포착하여 매수하는 추세 전환 전략입니다.

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **MACD 골든크로스 기반 추세 전환 포착 전략**을 정의한다.

- **대상 시간 구간**: 09:30:00 ~ 15:00:00 (장중 전체)
- **대상 종목**: 시가총액 3,000억 미만, 가격대 1,000원~50,000원
- **전략 타입**: MACD 골든크로스 추세 전환 (Trend Reversal)
- **핵심 변수**: MACD, MACDS, MACDH, RSI, 이동평균(20), 체결강도, 분당거래대금
- **업데이트 이력**:
  - 초기 문서 작성

## 가이드라인

- 모든 조건식은 Python 스타일의 의사코드로 작성되어 있으며, STOM 백테스터가 인식하는 변수/함수 규칙을 따릅니다.

---

# Condition - Min MACD GoldenCross

## 전략 개요

MACD 골든크로스 전략은 추세 전환의 초기를 포착합니다. 주요 특징:

- MACD가 시그널선을 상향 돌파
- MACD 히스토그램 0 이상
- RSI가 중립 구간 (40~70)
- 가격이 이동평균선 위에 위치

## 조건식

### 매수 조건식 - C_M_MGC_B

```python
MACD_골든크로스여부   = (MACD > MACDS and MACD_N(1) <= MACDS_N(1))
히스토그램_양수여부  = (MACDH > 0)
RSI_중립여부         = (40 <= RSI <= 70)
이평위치여부         = (현재가 > 이동평균(20))
거래량확인여부       = (분당거래대금 > 분당거래대금평균(20) * 1.1)

매수 = True

if not (관심종목 == 1):
    매수 = False
elif not (93000 <= 시분초 <= 150000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not MACD_골든크로스여부:
    매수 = False
elif not 히스토그램_양수여부:
    매수 = False
elif not RSI_중립여부:
    매수 = False
elif not 이평위치여부:
    매수 = False
elif not 거래량확인여부:
    매수 = False
elif 시가총액 < 3000:
    if not (0.5 < 등락율 <= 15.0):
        매수 = False
    elif not (체결강도 >= 110):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
else:
    if not (0.3 < 등락율 <= 12.0):
        매수 = False
    elif not (체결강도 >= 100):
        매수 = False
    elif not (회전율 > 1.0):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식 - C_M_MGC_S

```python
MACD_데드크로스여부   = (MACD < MACDS and MACD_N(1) >= MACDS_N(1))
히스토그램_음수여부  = (MACDH < 0)

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 4.0 or 수익률 <= -2.5:
    매도 = True
elif 최고수익률 > 5.0 and 최고수익률 * 0.60 >= 수익률:
    매도 = True
elif 보유시간 > 150:
    매도 = True
elif MACD_데드크로스여부:
    매도 = True
elif 히스토그램_음수여부 and 현재가 < 이동평균(20):
    매도 = True
elif 등락율각도(10) < -5:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

## 최적화 조건식

### 매수 최적화 조건식 - C_M_MGC_BO

```python
MACD_골든크로스여부   = (MACD > MACDS and MACD_N(1) <= MACDS_N(1))
히스토그램_양수여부  = (MACDH > self.vars[1])
RSI_중립여부         = (self.vars[2] <= RSI <= self.vars[3])
이평위치여부         = (현재가 > 이동평균(20))
거래량확인여부       = (분당거래대금 > 분당거래대금평균(20) * self.vars[4])

매수 = True

if not (관심종목 == 1):
    매수 = False
elif not (93000 <= 시분초 <= 150000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not MACD_골든크로스여부:
    매수 = False
elif not 히스토그램_양수여부:
    매수 = False
elif not RSI_중립여부:
    매수 = False
elif not 이평위치여부:
    매수 = False
elif not 거래량확인여부:
    매수 = False
elif 시가총액 < 3000:
    if not (self.vars[5] < 등락율 <= self.vars[6]):
        매수 = False
    elif not (체결강도 >= self.vars[7]):
        매수 = False
    elif not (회전율 > self.vars[8]):
        매수 = False
else:
    if not (self.vars[9] < 등락율 <= self.vars[10]):
        매수 = False
    elif not (체결강도 >= self.vars[11]):
        매수 = False
    elif not (회전율 > self.vars[12]):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매수 최적화 범위 - C_M_MGC_BOR

```python
self.vars[1]  = [[-5, 5, 5], 0]                      # 히스토그램 하한
self.vars[2]  = [[35, 45, 5], 40]                    # RSI 하한
self.vars[3]  = [[65, 75, 5], 70]                    # RSI 상한
self.vars[4]  = [[1.0, 1.2, 0.1], 1.1]               # 거래량 비율
self.vars[5]  = [[0.3, 0.7, 0.2], 0.5]               # 등락율 하한 (시총<3000)
self.vars[6]  = [[13.0, 17.0, 2.0], 15.0]            # 등락율 상한
self.vars[7]  = [[100, 120, 10], 110]                # 체결강도 하한
self.vars[8]  = [[1.2, 1.8, 0.3], 1.5]               # 회전율 하한
self.vars[9]  = [[0.2, 0.4, 0.1], 0.3]               # 등락율 하한 (시총>=3000)
self.vars[10] = [[10.0, 14.0, 2.0], 12.0]            # 등락율 상한
self.vars[11] = [[90, 110, 10], 100]                 # 체결강도 하한
self.vars[12] = [[0.8, 1.2, 0.2], 1.0]               # 회전율 하한
```

### 매도 최적화 조건식 - C_M_MGC_SO

```python
MACD_데드크로스여부   = (MACD < MACDS and MACD_N(1) >= MACDS_N(1))
히스토그램_음수여부  = (MACDH < self.vars[14])

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= self.vars[15] or 수익률 <= self.vars[16]:
    매도 = True
elif 최고수익률 > self.vars[17] and 최고수익률 * self.vars[18] >= 수익률:
    매도 = True
elif 보유시간 > self.vars[19]:
    매도 = True
elif MACD_데드크로스여부:
    매도 = True
elif 히스토그램_음수여부 and 현재가 < 이동평균(20):
    매도 = True
elif 등락율각도(10) < -self.vars[20]:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

### 매도 최적화 범위 - C_M_MGC_SOR

```python
self.vars[14] = [[-5, 5, 5], 0]                      # 히스토그램 상한
self.vars[15] = [[3.5, 4.5, 0.5], 4.0]               # 목표 수익 실현
self.vars[16] = [[-3.0, -2.0, 0.5], -2.5]            # 최대 손실 컷
self.vars[17] = [[4.5, 5.5, 0.5], 5.0]               # 최고수익률 기준값
self.vars[18] = [[0.55, 0.65, 0.05], 0.60]           # 트레일링 보정 비율
self.vars[19] = [[120, 180, 30], 150]                # 최대 보유시간(분)
self.vars[20] = [[4, 6, 1], 5]                       # 등락율각도 하락 임계
```

### GA 최적화 범위 - C_M_MGC_GAR

```python
self.vars[1]  = [[-5, 0, 5], 0]
self.vars[2]  = [[35, 40, 45], 40]
self.vars[3]  = [[65, 70, 75], 70]
self.vars[4]  = [[1.0, 1.1, 1.2], 1.1]
self.vars[15] = [[3.5, 4.0, 4.5], 4.0]
self.vars[16] = [[-3.0, -2.5, -2.0], -2.5]
self.vars[18] = [[0.55, 0.60, 0.65], 0.60]
```

---

## 조건식 개선 방향 연구

1) **MACD 0선 확인**
   - MACD가 0선 위/아래 위치 확인
   - 0선 위에서 골든크로스 시 신호 강화

2) **히스토그램 증가 확인**
   - 히스토그램이 연속 증가 중
   - 추세 강화 확인

3) **PPO 추가**
   - Percentage Price Oscillator 확인
   - MACD와 PPO 동시 골든크로스

4) **APO 추가**
   - Absolute Price Oscillator 확인
   - 다중 지표 교차 확인

5) **가짜 크로스 필터링**
   - 골든크로스 후 N분간 유지 확인
   - 단기 반전 필터링

## 태그
- #주식트레이딩
- #분봉트레이딩
- #매수조건
- #매도조건
- #최적화
- #유전알고리즘
- #파이썬
- #트레이딩로직
- #MACD
- #골든크로스
- #추세전환전략
- #리스크관리
