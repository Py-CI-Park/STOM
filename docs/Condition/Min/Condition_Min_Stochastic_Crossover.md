# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Min.md 가이드라인 반영

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
- [Condition - Min Stochastic Crossover](#condition---min-stochastic-crossover)
  - [전략 개요](#전략-개요)
  - [조건식](#조건식)
  - [최적화 조건식](#최적화-조건식)
  - [조건식 개선 방향 연구](#조건식-개선-방향-연구)
  - [태그](#태그)

## 소개

이 문서는 STOM 주식 자동거래 시스템에서 스토캐스틱 교차 전략(Stochastic Crossover Strategy)을 위한 조건식을 제공합니다. 스토캐스틱 지표의 %K와 %D 라인 교차를 활용한 모멘텀 매매 전략입니다.

## 가이드라인

- 모든 조건식은 Python 스타일의 의사코드로 작성되어 있으며, STOM 백테스터가 인식하는 변수/함수 규칙을 따릅니다.

---

# Condition - Min Stochastic Crossover

## 전략 개요

스토캐스틱 교차 전략은 %K와 %D 라인의 골든크로스를 포착합니다:

- 과매도 구간(%K < 20) 확인
- %K가 %D를 상향 돌파
- 상승 모멘텀 확인
- RSI 보조 지표 활용

## 조건식

### 매수 조건식

```python
# ================================
#  공통 계산 지표
# ================================
스토캐스틱골든크로스여부 = (STOCH_K > STOCH_D and STOCH_K_N(1) <= STOCH_D_N(1))
과매도구간여부        = (STOCH_K_N(1) < 20 and STOCH_D_N(1) < 25)
상승모멘텀여부        = (STOCH_K > STOCH_K_N(1) and STOCH_K_N(1) > STOCH_K_N(2))
RSI상승여부           = (RSI > 40 and RSI < 70)
가격상승여부          = (현재가 > 현재가N(1) and 현재가N(1) > 현재가N(2))
거래량증가여부        = (분당거래대금 > 분당거래대금평균(20) * 1.3)

매수 = True

# 공통 필터
if not (관심종목 == 1):
    매수 = False
elif not (90500 <= 시분초 <= 143000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# 스토캐스틱 골든크로스 확인
elif not 스토캐스틱골든크로스여부:
    매수 = False

# 과매도 구간 확인
elif not 과매도구간여부:
    매수 = False

# 상승 모멘텀 확인
elif not 상승모멘텀여부:
    매수 = False

# RSI 상승 확인
elif not RSI상승여부:
    매수 = False

# 가격 상승 확인
elif not 가격상승여부:
    매수 = False

# 거래량 증가 확인
elif not 거래량증가여부:
    매수 = False

# 시가총액별 세부 조건
elif 시가총액 < 3000:
    if not (체결강도 >= 115):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
    elif not (현재가 > 이동평균(5)):
        매수 = False
    elif not (이동평균(5) > 이동평균(20)):
        매수 = False
    elif not (STOCH_K < 50):  # 50 이하에서 진입
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * 1.5):
        매수 = False
elif 시가총액 < 5000:
    if not (체결강도 >= 110):
        매수 = False
    elif not (회전율 > 1.2):
        매수 = False
    elif not (현재가 > 이동평균(5)):
        매수 = False
    elif not (이동평균(5) > 이동평균(20)):
        매수 = False
    elif not (STOCH_K < 55):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * 1.4):
        매수 = False
else:
    if not (체결강도 >= 105):
        매수 = False
    elif not (회전율 > 1.0):
        매수 = False
    elif not (현재가 > 이동평균(5)):
        매수 = False
    elif not (이동평균(5) > 이동평균(20)):
        매수 = False
    elif not (STOCH_K < 60):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * 1.3):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식

```python
# ================================
#  공통 계산 지표
# ================================
스토캐스틱데드크로스여부 = (STOCH_K < STOCH_D and STOCH_K_N(1) >= STOCH_D_N(1))
과매수구간여부        = (STOCH_K > 80 or STOCH_D > 80)
RSI과매수여부         = (RSI > 75)

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 3.0 or 수익률 <= -2.0:
    매도 = True
elif 최고수익률 > 4.0 and 최고수익률 * 0.70 >= 수익률:
    매도 = True
elif 보유시간 > 1800:  # 30분
    매도 = True
elif 스토캐스틱데드크로스여부:
    매도 = True
elif 과매수구간여부 and 보유시간 > 300:  # 5분 이후 과매수
    매도 = True
elif RSI과매수여부:
    매도 = True
elif 체결강도 < 95:
    매도 = True
elif 시분초 >= 145500:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

## 최적화 조건식

### 매수 최적화 조건식 - C_M_SC_BO

```python
스토캐스틱골든크로스여부 = (STOCH_K > STOCH_D and STOCH_K_N(1) <= STOCH_D_N(1))
과매도구간여부        = (STOCH_K_N(1) < self.vars[1] and STOCH_D_N(1) < self.vars[2])
상승모멘텀여부        = (STOCH_K > STOCH_K_N(1) and STOCH_K_N(1) > STOCH_K_N(2))
RSI상승여부           = (RSI > self.vars[3] and RSI < self.vars[4])
가격상승여부          = (현재가 > 현재가N(1) and 현재가N(1) > 현재가N(2))
거래량증가여부        = (분당거래대금 > 분당거래대금평균(20) * self.vars[5])

매수 = True

if not (관심종목 == 1):
    매수 = False
elif not (90500 <= 시분초 <= 143000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False
elif not 스토캐스틱골든크로스여부:
    매수 = False
elif not 과매도구간여부:
    매수 = False
elif not 상승모멘텀여부:
    매수 = False
elif not RSI상승여부:
    매수 = False
elif not 가격상승여부:
    매수 = False
elif not 거래량증가여부:
    매수 = False

elif 시가총액 < 3000:
    if not (체결강도 >= self.vars[6]):
        매수 = False
    elif not (회전율 > self.vars[7]):
        매수 = False
    elif not (현재가 > 이동평균(5)):
        매수 = False
    elif not (이동평균(5) > 이동평균(20)):
        매수 = False
    elif not (STOCH_K < self.vars[8]):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * self.vars[9]):
        매수 = False
elif 시가총액 < 5000:
    if not (체결강도 >= self.vars[10]):
        매수 = False
    elif not (회전율 > self.vars[11]):
        매수 = False
    elif not (현재가 > 이동평균(5)):
        매수 = False
    elif not (이동평균(5) > 이동평균(20)):
        매수 = False
    elif not (STOCH_K < self.vars[12]):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * self.vars[13]):
        매수 = False
else:
    if not (체결강도 >= self.vars[14]):
        매수 = False
    elif not (회전율 > self.vars[15]):
        매수 = False
    elif not (현재가 > 이동평균(5)):
        매수 = False
    elif not (이동평균(5) > 이동평균(20)):
        매수 = False
    elif not (STOCH_K < self.vars[16]):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * self.vars[17]):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매수 최적화 범위 - C_M_SC_BOR

```python
# 공통
self.vars[1]  = [[15, 25, 5], 20]                    # %K 과매도 임계
self.vars[2]  = [[20, 30, 5], 25]                    # %D 과매도 임계
self.vars[3]  = [[35, 45, 5], 40]                    # RSI 하한
self.vars[4]  = [[65, 75, 5], 70]                    # RSI 상한
self.vars[5]  = [[1.2, 1.4, 0.1], 1.3]               # 거래량 증가 비율

# 시가총액 < 3000
self.vars[6]  = [[110, 120, 5], 115]                 # 체결강도 하한
self.vars[7]  = [[1.2, 1.8, 0.3], 1.5]               # 회전율 하한
self.vars[8]  = [[45, 55, 5], 50]                    # STOCH_K 상한
self.vars[9]  = [[1.3, 1.7, 0.2], 1.5]               # 거래대금 비율

# 시가총액 < 5000
self.vars[10] = [[105, 115, 5], 110]                 # 체결강도 하한
self.vars[11] = [[1.0, 1.4, 0.2], 1.2]               # 회전율 하한
self.vars[12] = [[50, 60, 5], 55]                    # STOCH_K 상한
self.vars[13] = [[1.2, 1.6, 0.2], 1.4]               # 거래대금 비율

# 시가총액 >= 5000
self.vars[14] = [[100, 110, 5], 105]                 # 체결강도 하한
self.vars[15] = [[0.8, 1.2, 0.2], 1.0]               # 회전율 하한
self.vars[16] = [[55, 65, 5], 60]                    # STOCH_K 상한
self.vars[17] = [[1.1, 1.5, 0.2], 1.3]               # 거래대금 비율
```

### 매도 최적화 조건식 - C_M_SC_SO

```python
스토캐스틱데드크로스여부 = (STOCH_K < STOCH_D and STOCH_K_N(1) >= STOCH_D_N(1))
과매수구간여부        = (STOCH_K > self.vars[19] or STOCH_D > self.vars[20])
RSI과매수여부         = (RSI > self.vars[21])

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= self.vars[22] or 수익률 <= self.vars[23]:
    매도 = True
elif 최고수익률 > self.vars[24] and 최고수익률 * self.vars[25] >= 수익률:
    매도 = True
elif 보유시간 > self.vars[26]:
    매도 = True
elif 스토캐스틱데드크로스여부:
    매도 = True
elif 과매수구간여부 and 보유시간 > self.vars[27]:
    매도 = True
elif RSI과매수여부:
    매도 = True
elif 체결강도 < self.vars[28]:
    매도 = True
elif 시분초 >= 145500:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

### 매도 최적화 범위 - C_M_SC_SOR

```python
self.vars[19] = [[75, 85, 5], 80]                    # STOCH_K 과매수 임계
self.vars[20] = [[75, 85, 5], 80]                    # STOCH_D 과매수 임계
self.vars[21] = [[70, 80, 5], 75]                    # RSI 과매수 임계
self.vars[22] = [[2.5, 3.5, 0.5], 3.0]               # 목표 수익 실현(%)
self.vars[23] = [[-2.5, -1.5, 0.5], -2.0]            # 최대 손실 컷(%)
self.vars[24] = [[3.5, 4.5, 0.5], 4.0]               # 최고수익률 기준값(%)
self.vars[25] = [[0.65, 0.75, 0.05], 0.70]           # 트레일링 보정 비율
self.vars[26] = [[1500, 2100, 300], 1800]            # 최대 보유시간(초)
self.vars[27] = [[240, 360, 60], 300]                # 과매수 확인 시간(초)
self.vars[28] = [[90, 100, 5], 95]                   # 체결강도 하한
```

### GA 최적화 범위 - C_M_SC_GAR

```python
# 매수 조건
self.vars[1]  = [15, 25]                             # %K 과매도 임계
self.vars[2]  = [20, 30]                             # %D 과매도 임계
self.vars[3]  = [35, 45]                             # RSI 하한
self.vars[4]  = [65, 75]                             # RSI 상한
self.vars[5]  = [1.2, 1.4]                           # 거래량 증가 비율

# 시가총액 < 3000
self.vars[6]  = [110, 120]                           # 체결강도 하한
self.vars[7]  = [1.2, 1.8]                           # 회전율 하한
self.vars[8]  = [45, 55]                             # STOCH_K 상한
self.vars[9]  = [1.3, 1.7]                           # 거래대금 비율

# 시가총액 < 5000
self.vars[10] = [105, 115]                           # 체결강도 하한
self.vars[11] = [1.0, 1.4]                           # 회전율 하한
self.vars[12] = [50, 60]                             # STOCH_K 상한
self.vars[13] = [1.2, 1.6]                           # 거래대금 비율

# 시가총액 >= 5000
self.vars[14] = [100, 110]                           # 체결강도 하한
self.vars[15] = [0.8, 1.2]                           # 회전율 하한
self.vars[16] = [55, 65]                             # STOCH_K 상한
self.vars[17] = [1.1, 1.5]                           # 거래대금 비율

# 매도 조건
self.vars[19] = [75, 85]                             # STOCH_K 과매수 임계
self.vars[20] = [75, 85]                             # STOCH_D 과매수 임계
self.vars[21] = [70, 80]                             # RSI 과매수 임계
self.vars[22] = [2.5, 3.5]                           # 목표 수익 실현(%)
self.vars[23] = [-2.5, -1.5]                         # 최대 손실 컷(%)
self.vars[24] = [3.5, 4.5]                           # 최고수익률 기준값(%)
self.vars[25] = [0.65, 0.75]                         # 트레일링 보정 비율
self.vars[26] = [1500, 2100]                         # 최대 보유시간(초)
self.vars[27] = [240, 360]                           # 과매수 확인 시간(초)
self.vars[28] = [90, 100]                            # 체결강도 하한
```

---

## 조건식 개선 방향 연구

1) **스토캐스틱 매개변수 최적화**
   - %K, %D 기간 조정
   - Slow vs Fast Stochastic 비교
   - 민감도 조정

2) **다이버전스 패턴 활용**
   - 가격과 STOCH 방향 불일치
   - Bullish/Bearish Divergence
   - Hidden Divergence

3) **다중 시간프레임 확인**
   - 상위 시간프레임 추세 확인
   - 하위 시간프레임 진입 타이밍
   - 시간프레임 정렬 전략

4) **과매도/과매수 구간 정의**
   - 종목별 최적 임계값
   - 시장 상황별 조정
   - 역사적 데이터 기반 조정

5) **리스크 관리**
   - 데드크로스 즉시 청산
   - 과매수 구간 청산 (5분 이후)
   - RSI 과매수 즉시 청산

## 태그
- #주식트레이딩
- #분봉트레이딩
- #매수조건
- #매도조건
- #최적화
- #스토캐스틱
- #모멘텀지표
- #오실레이터
- #리스크관리
