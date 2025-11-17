# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Min.md 가이드라인 반영

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
- [Condition - Min Trend Following](#condition---min-trend-following)
  - [전략 개요](#전략-개요)
  - [조건식](#조건식)
  - [최적화 조건식](#최적화-조건식)
  - [조건식 개선 방향 연구](#조건식-개선-방향-연구)
  - [태그](#태그)

## 소개

이 문서는 STOM 주식 자동거래 시스템에서 추세 추종 전략(Trend Following)을 위한 조건식과 최적화 범위를 제공합니다. 명확한 상승 추세를 확인하고 추세 방향으로 진입하는 전략입니다.

## 가이드라인

- 모든 조건식은 Python 스타일의 의사코드로 작성되어 있으며, STOM 백테스터가 인식하는 변수/함수 규칙을 따릅니다.

---

# Condition - Min Trend Following

## 전략 개요

추세 추종 전략은 강한 추세를 확인하고 추세 방향으로 진입합니다. 주요 특징:

- ADX로 추세 강도 확인 (사용 가능 시)
- 이동평균선 정배열 확인
- Parabolic SAR 추세 방향 일치
- 등락율 각도 지속적 상승

## 조건식

### 매수 조건식 - C_M_TF_B

```python
정배열여부            = (이동평균(5) > 이동평균(20) > 이동평균(60))
SAR_추세여부         = (현재가 > SAR)
각도_상승여부        = (등락율각도(20) > 2 and 당일거래대금각도(20) > 1)
가격위치여부         = (현재가 > 이동평균(5))
거래량지속여부       = (분당거래대금평균(10) > 분당거래대금평균(20) * 0.9)

매수 = True

if not (관심종목 == 1):
    매수 = False
elif not (93000 <= 시분초 <= 150000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not 정배열여부:
    매수 = False
elif not SAR_추세여부:
    매수 = False
elif not 각도_상승여부:
    매수 = False
elif not 가격위치여부:
    매수 = False
elif not 거래량지속여부:
    매수 = False
elif 시가총액 < 3000:
    if not (1.0 < 등락율 <= 18.0):
        매수 = False
    elif not (체결강도 >= 120):
        매수 = False
    elif not (회전율 > 2.0):
        매수 = False
    elif not (전일비 > 70):
        매수 = False
else:
    if not (0.8 < 등락율 <= 15.0):
        매수 = False
    elif not (체결강도 >= 110):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
    elif not (전일비 > 50):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식 - C_M_TF_S

```python
정배열이탈여부        = (이동평균(5) <= 이동평균(20))
SAR_역전여부         = (현재가 < SAR and 현재가N(1) >= SAR_N(1))
각도_하락여부        = (등락율각도(10) < -3)

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 5.0 or 수익률 <= -3.0:
    매도 = True
elif 최고수익률 > 6.0 and 최고수익률 * 0.55 >= 수익률:
    매도 = True
elif 보유시간 > 240:  # 240분 (4시간)
    매도 = True
elif 정배열이탈여부:
    매도 = True
elif SAR_역전여부:
    매도 = True
elif 각도_하락여부:
    매도 = True
elif 현재가 < 이동평균(20):
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

## 최적화 조건식

### 매수 최적화 조건식 - C_M_TF_BO

```python
정배열여부            = (이동평균(5) > 이동평균(20) > 이동평균(60))
SAR_추세여부         = (현재가 > SAR)
각도_상승여부        = (등락율각도(20) > self.vars[1] and 당일거래대금각도(20) > self.vars[2])
가격위치여부         = (현재가 > 이동평균(5))
거래량지속여부       = (분당거래대금평균(10) > 분당거래대금평균(20) * self.vars[3])

매수 = True

if not (관심종목 == 1):
    매수 = False
elif not (93000 <= 시분초 <= 150000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not 정배열여부:
    매수 = False
elif not SAR_추세여부:
    매수 = False
elif not 각도_상승여부:
    매수 = False
elif not 가격위치여부:
    매수 = False
elif not 거래량지속여부:
    매수 = False
elif 시가총액 < 3000:
    if not (self.vars[4] < 등락율 <= self.vars[5]):
        매수 = False
    elif not (체결강도 >= self.vars[6]):
        매수 = False
    elif not (회전율 > self.vars[7]):
        매수 = False
    elif not (전일비 > self.vars[8]):
        매수 = False
else:
    if not (self.vars[9] < 등락율 <= self.vars[10]):
        매수 = False
    elif not (체결강도 >= self.vars[11]):
        매수 = False
    elif not (회전율 > self.vars[12]):
        매수 = False
    elif not (전일비 > self.vars[13]):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매수 최적화 범위 - C_M_TF_BOR

```python
self.vars[1]  = [[1, 3, 1], 2]                       # 등락율각도 하한
self.vars[2]  = [[0, 2, 1], 1]                       # 거래대금각도 하한
self.vars[3]  = [[0.85, 0.95, 0.05], 0.90]           # 거래량 지속 비율
self.vars[4]  = [[0.8, 1.2, 0.2], 1.0]               # 등락율 하한 (시총<3000)
self.vars[5]  = [[16.0, 20.0, 2.0], 18.0]            # 등락율 상한
self.vars[6]  = [[110, 130, 10], 120]                # 체결강도 하한
self.vars[7]  = [[1.7, 2.3, 0.3], 2.0]               # 회전율 하한
self.vars[8]  = [[60, 80, 10], 70]                   # 전일비 하한
self.vars[9]  = [[0.6, 1.0, 0.2], 0.8]               # 등락율 하한 (시총>=3000)
self.vars[10] = [[13.0, 17.0, 2.0], 15.0]            # 등락율 상한
self.vars[11] = [[100, 120, 10], 110]                # 체결강도 하한
self.vars[12] = [[1.2, 1.8, 0.3], 1.5]               # 회전율 하한
self.vars[13] = [[40, 60, 10], 50]                   # 전일비 하한
```

### 매도 최적화 조건식 - C_M_TF_SO

```python
정배열이탈여부        = (이동평균(5) <= 이동평균(20))
SAR_역전여부         = (현재가 < SAR and 현재가N(1) >= SAR_N(1))
각도_하락여부        = (등락율각도(10) < -self.vars[15])

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= self.vars[16] or 수익률 <= self.vars[17]:
    매도 = True
elif 최고수익률 > self.vars[18] and 최고수익률 * self.vars[19] >= 수익률:
    매도 = True
elif 보유시간 > self.vars[20]:
    매도 = True
elif 정배열이탈여부:
    매도 = True
elif SAR_역전여부:
    매도 = True
elif 각도_하락여부:
    매도 = True
elif 현재가 < 이동평균(20):
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

### 매도 최적화 범위 - C_M_TF_SOR

```python
self.vars[15] = [[2, 4, 1], 3]                       # 각도 하락 임계
self.vars[16] = [[4.5, 5.5, 0.5], 5.0]               # 목표 수익 실현
self.vars[17] = [[-3.5, -2.5, 0.5], -3.0]            # 최대 손실 컷
self.vars[18] = [[5.5, 6.5, 0.5], 6.0]               # 최고수익률 기준값
self.vars[19] = [[0.50, 0.60, 0.05], 0.55]           # 트레일링 보정 비율
self.vars[20] = [[210, 270, 30], 240]                # 최대 보유시간(분)
```

### GA 최적화 범위 - C_M_TF_GAR

```python
self.vars[1]  = [[1, 2, 3], 2]
self.vars[2]  = [[0, 1, 2], 1]
self.vars[3]  = [[0.85, 0.90, 0.95], 0.90]
self.vars[4]  = [[0.8, 1.0, 1.2], 1.0]
self.vars[5]  = [[16.0, 18.0, 20.0], 18.0]
self.vars[6]  = [[110, 120, 130], 120]
self.vars[16] = [[4.5, 5.0, 5.5], 5.0]
self.vars[17] = [[-3.5, -3.0, -2.5], -3.0]
self.vars[19] = [[0.50, 0.55, 0.60], 0.55]
```

---

## 조건식 개선 방향 연구

1) **ATR 기반 변동성 확인**
   - Average True Range로 변동성 측정
   - 적정 변동성 구간에서만 진입

2) **추세 강도 측정**
   - DI+와 DI- 차이로 추세 강도 계산
   - 강한 추세에서만 진입

3) **CCI 추가**
   - Commodity Channel Index 확인
   - CCI와 추세 방향 일치 시 진입

4) **되돌림 진입**
   - 추세 유지 중 이평선 터치 시 재진입
   - 추세 내 조정 활용

5) **트레일링 스톱 강화**
   - SAR을 트레일링 스톱으로 활용
   - SAR 역전 즉시 청산

## 태그
- #주식트레이딩
- #분봉트레이딩
- #매수조건
- #매도조건
- #최적화
- #유전알고리즘
- #파이썬
- #트레이딩로직
- #추세추종전략
- #이동평균선
- #ParabolicSAR
- #장기보유전략
- #리스크관리
