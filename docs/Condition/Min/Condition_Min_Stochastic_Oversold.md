# 조건식 - 스토캐스틱 과매도 반등 전략 (분봉)

- STOM 주식 자동거래에 사용하기 위한 분봉 데이터 조건식 문서
- Back_Testing_Guideline_Min.md 에 있는 조건식을 사용하여 만든 조건식

## 목차
- [조건식 - 스토캐스틱 과매도 반등 전략 (분봉)](#조건식---스토캐스틱-과매도-반등-전략-분봉)
  - [목차](#목차)
  - [소개](#소개)
  - [전략 개요](#전략-개요)
  - [조건식](#조건식)
    - [매수 조건식 - C\_M\_STOCH\_OS\_B](#매수-조건식---c_m_stoch_os_b)
    - [매도 조건식 - C\_M\_STOCH\_OS\_S](#매도-조건식---c_m_stoch_os_s)
  - [최적화 조건식](#최적화-조건식)
    - [매수 최적화 조건식 - C\_M\_STOCH\_OS\_BO](#매수-최적화-조건식---c_m_stoch_os_bo)
    - [매수 최적화 범위 - C\_M\_STOCH\_OS\_BOR](#매수-최적화-범위---c_m_stoch_os_bor)
    - [매도 최적화 조건식 - C\_M\_STOCH\_OS\_SO](#매도-최적화-조건식---c_m_stoch_os_so)
    - [매도 최적화 범위 - C\_M\_STOCH\_OS\_SOR](#매도-최적화-범위---c_m_stoch_os_sor)
    - [매수 매도 통합 최적화 범위 - C\_M\_STOCH\_OS\_OR](#매수-매도-통합-최적화-범위---c_m_stoch_os_or)
    - [GA 최적화 범위 - C\_M\_STOCH\_OS\_GAR](#ga-최적화-범위---c_m_stoch_os_gar)

## 소개

이 문서는 스토캐스틱 지표의 과매도 구간에서 반등을 포착하는 분봉 기반 전략입니다.
Stochastic %K와 %D가 과매도 구간에서 골든크로스하는 시점을 진입 신호로 활용합니다.

## 전략 개요

**핵심 아이디어**:
1. Stochastic %K가 과매도 구간(20 이하)에서 상승 전환
2. %K가 %D를 상향 돌파하는 골든크로스 확인
3. RSI 과매도 영역 탈출 동반
4. 분당거래대금 증가 확인

**적용 대상**:
- 시가총액 1000억~3000억 중소형주
- 등락율 -5% ~ +15% 범위

## 조건식

### 매수 조건식 - C_M_STOCH_OS_B

```python
분당순매수금액 = (분당매수수량 - 분당매도수량) * 현재가 / 1_000_000

# 시간대 제한
if not (93000 <= 시분초 < 145000):
    매수 = False

# 가격 및 등락율 범위
elif not (2000 < 현재가 <= 20000):
    매수 = False
elif not (-5.0 < 등락율 <= 15.0):
    매수 = False

# VI 조건
elif not (현재가 < VI아래5호가):
    매수 = False

# 스토캐스틱 과매도 조건
elif not (STOCHSK_N(1) <= 20):
    매수 = False
elif not (STOCHSK > STOCHSK_N(1)):
    매수 = False

# 스토캐스틱 골든크로스
elif not (STOCHSK_N(1) <= STOCHSD_N(1) and STOCHSK > STOCHSD):
    매수 = False

# RSI 과매도 탈출
elif not (RSI_N(1) < 35 and RSI > 35):
    매수 = False

# 분당거래대금 증가
elif not (분당거래대금 > 분당거래대금평균(30)):
    매수 = False

# 체결강도 조건
elif not (체결강도 > 110):
    매수 = False

# 호가창 조건
elif not (분당매수수량 > 분당매도수량):
    매수 = False
elif not (매수총잔량 > 매도총잔량 * 0.8):
    매수 = False

# 시가총액별 조건
elif 시가총액 < 1000:
    if not (전일비 > 50):
        매수 = False
    elif not (회전율 > 2.0):
        매수 = False
    elif not (분당순매수금액 > 15):
        매수 = False
    elif not (이동평균(60) > 이동평균(60, 1)):
        매수 = False

elif 시가총액 < 3000:
    if not (전일비 > 35):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
    elif not (분당순매수금액 > 25):
        매수 = False
    elif not (이동평균(60) > 이동평균(60, 1)):
        매수 = False

else:
    if not (전일비 > 25):
        매수 = False
    elif not (회전율 > 1.0):
        매수 = False
    elif not (분당순매수금액 > 40):
        매수 = False
    elif not (이동평균(60) > 이동평균(60, 1)):
        매수 = False
```

### 매도 조건식 - C_M_STOCH_OS_S

```python
# 상한가 근접
if 등락율 > 29.5:
    매도 = True

# 이익실현
elif 수익률 >= 3.5:
    매도 = True

# 손절
elif 수익률 <= -2.0:
    매도 = True

# 고점 대비 하락
elif 최고수익률 - 수익률 >= 2.0:
    매도 = True

# 스토캐스틱 과매수
elif STOCHSK > 80 and 수익률 > 1.0:
    매도 = True

# 스토캐스틱 데드크로스
elif STOCHSK_N(1) >= STOCHSD_N(1) and STOCHSK < STOCHSD and 수익률 > 0.5:
    매도 = True

# RSI 과매수
elif RSI > 70 and 수익률 > 0.8:
    매도 = True

# 보유시간 제한
elif 보유시간 > 180:
    매도 = True

# 시가총액별 매도 조건
elif 시가총액 < 3000:
    # 체결강도 하락
    if 체결강도 < 체결강도평균(30) - 20 and 수익률 > 0.3:
        매도 = True
    # 이동평균 하향 돌파
    elif 현재가_N(1) >= 이동평균(20, 1) and 현재가 < 이동평균(20) and 수익률 > 1.0:
        매도 = True
    # 매도세 우위
    elif (분당매도수량 - 분당매수수량) >= 매수총잔량 * 0.6 and 수익률 > 0:
        매도 = True

else:
    # 체결강도 하락
    if 체결강도 < 체결강도평균(30) - 15 and 수익률 > 0.3:
        매도 = True
    # 이동평균 하향 돌파
    elif 현재가_N(1) >= 이동평균(20, 1) and 현재가 < 이동평균(20) and 수익률 > 1.0:
        매도 = True
    # 매도세 우위
    elif (분당매도수량 - 분당매수수량) >= 매수총잔량 * 0.5 and 수익률 > 0:
        매도 = True
```

## 최적화 조건식

### 매수 최적화 조건식 - C_M_STOCH_OS_BO

```python
분당순매수금액 = (분당매수수량 - 분당매도수량) * 현재가 / 1_000_000

if not (93000 <= 시분초 < 145000):
    매수 = False
elif not (self.vars[0] < 현재가 <= self.vars[1]):
    매수 = False
elif not (self.vars[2] < 등락율 <= self.vars[3]):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif not (STOCHSK_N(1) <= self.vars[4]):
    매수 = False
elif not (STOCHSK > STOCHSK_N(1)):
    매수 = False
elif not (STOCHSK_N(1) <= STOCHSD_N(1) and STOCHSK > STOCHSD):
    매수 = False
elif not (RSI_N(1) < self.vars[5] and RSI > self.vars[5]):
    매수 = False
elif not (분당거래대금 > 분당거래대금평균(30)):
    매수 = False
elif not (체결강도 > self.vars[6]):
    매수 = False
elif not (분당매수수량 > 분당매도수량):
    매수 = False
elif 시가총액 < self.vars[7]:
    if not (전일비 > self.vars[8]):
        매수 = False
    elif not (회전율 > self.vars[9]):
        매수 = False
    elif not (분당순매수금액 > self.vars[10]):
        매수 = False
```

### 매수 최적화 범위 - C_M_STOCH_OS_BOR

```python
self.vars[0] = [[1500, 2500, 250], 2000]      # 현재가 하한
self.vars[1] = [[18000, 22000, 1000], 20000]  # 현재가 상한
self.vars[2] = [[-7.0, -3.0, 1.0], -5.0]      # 등락율 하한
self.vars[3] = [[13.0, 17.0, 1.0], 15.0]      # 등락율 상한
self.vars[4] = [[18, 22, 1], 20]              # 스토캐스틱 과매도 기준
self.vars[5] = [[33, 37, 1], 35]              # RSI 과매도 기준
self.vars[6] = [[105, 115, 2.5], 110]         # 체결강도
self.vars[7] = [[800, 1200, 100], 1000]       # 시가총액 기준
self.vars[8] = [[40, 60, 5], 50]              # 전일비
self.vars[9] = [[1.5, 2.5, 0.25], 2.0]        # 회전율
self.vars[10] = [[10, 20, 2.5], 15]           # 분당순매수금액
```

### 매도 최적화 조건식 - C_M_STOCH_OS_SO

```python
if 등락율 > 29.5:
    매도 = True
elif 수익률 >= self.vars[20]:
    매도 = True
elif 수익률 <= self.vars[21]:
    매도 = True
elif 최고수익률 - 수익률 >= self.vars[22]:
    매도 = True
elif STOCHSK > self.vars[23] and 수익률 > 1.0:
    매도 = True
elif RSI > self.vars[24] and 수익률 > 0.8:
    매도 = True
elif 보유시간 > self.vars[25]:
    매도 = True
```

### 매도 최적화 범위 - C_M_STOCH_OS_SOR

```python
self.vars[20] = [[3.0, 4.0, 0.25], 3.5]       # 목표 수익률
self.vars[21] = [[-2.5, -1.5, 0.25], -2.0]    # 손절 수익률
self.vars[22] = [[1.5, 2.5, 0.25], 2.0]       # 고점 대비 하락폭
self.vars[23] = [[75, 85, 2.5], 80]           # 스토캐스틱 과매수 기준
self.vars[24] = [[68, 72, 1], 70]             # RSI 과매수 기준
self.vars[25] = [[150, 210, 15], 180]         # 보유시간 제한
```

### 매수 매도 통합 최적화 범위 - C_M_STOCH_OS_OR

```python
# 매수 변수
self.vars[0] = [[1500, 2500, 250], 2000]
self.vars[1] = [[18000, 22000, 1000], 20000]
self.vars[2] = [[-7.0, -3.0, 1.0], -5.0]
self.vars[3] = [[13.0, 17.0, 1.0], 15.0]
self.vars[4] = [[18, 22, 1], 20]
self.vars[5] = [[33, 37, 1], 35]
self.vars[6] = [[105, 115, 2.5], 110]
self.vars[7] = [[800, 1200, 100], 1000]
self.vars[8] = [[40, 60, 5], 50]
self.vars[9] = [[1.5, 2.5, 0.25], 2.0]
self.vars[10] = [[10, 20, 2.5], 15]

# 매도 변수
self.vars[20] = [[3.0, 4.0, 0.25], 3.5]
self.vars[21] = [[-2.5, -1.5, 0.25], -2.0]
self.vars[22] = [[1.5, 2.5, 0.25], 2.0]
self.vars[23] = [[75, 85, 2.5], 80]
self.vars[24] = [[68, 72, 1], 70]
self.vars[25] = [[150, 210, 15], 180]
```

### GA 최적화 범위 - C_M_STOCH_OS_GAR

```python
# 매수 변수
self.vars[0] = [[1500, 1750, 2000, 2250, 2500], 2000]
self.vars[1] = [[18000, 19000, 20000, 21000, 22000], 20000]
self.vars[2] = [[-7.0, -6.0, -5.0, -4.0, -3.0], -5.0]
self.vars[3] = [[13.0, 14.0, 15.0, 16.0, 17.0], 15.0]
self.vars[4] = [[18, 19, 20, 21, 22], 20]
self.vars[5] = [[33, 34, 35, 36, 37], 35]
self.vars[6] = [[105, 107.5, 110, 112.5, 115], 110]
self.vars[7] = [[800, 900, 1000, 1100, 1200], 1000]
self.vars[8] = [[40, 45, 50, 55, 60], 50]
self.vars[9] = [[1.5, 1.75, 2.0, 2.25, 2.5], 2.0]
self.vars[10] = [[10, 12.5, 15, 17.5, 20], 15]

# 매도 변수
self.vars[20] = [[3.0, 3.25, 3.5, 3.75, 4.0], 3.5]
self.vars[21] = [[-2.5, -2.25, -2.0, -1.75, -1.5], -2.0]
self.vars[22] = [[1.5, 1.75, 2.0, 2.25, 2.5], 2.0]
self.vars[23] = [[75, 77.5, 80, 82.5, 85], 80]
self.vars[24] = [[68, 69, 70, 71, 72], 70]
self.vars[25] = [[150, 165, 180, 195, 210], 180]
```
