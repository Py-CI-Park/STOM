# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Min.md 가이드라인 반영

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - Min BBand Reversal](#condition---min-bband-reversal)
  - [전략 개요](#전략-개요)
  - [조건식](#조건식)
    - [매수 조건식 - C_M_BBR_B](#매수-조건식---c_m_bbr_b)
    - [매도 조건식 - C_M_BBR_S](#매도-조건식---c_m_bbr_s)
  - [최적화 조건식](#최적화-조건식)
    - [매수 최적화 조건식 - C_M_BBR_BO](#매수-최적화-조건식---c_m_bbr_bo)
    - [매수 최적화 범위 - C_M_BBR_BOR](#매수-최적화-범위---c_m_bbr_bor)
    - [매도 최적화 조건식 - C_M_BBR_SO](#매도-최적화-조건식---c_m_bbr_so)
    - [매도 최적화 범위 - C_M_BBR_SOR](#매도-최적화-범위---c_m_bbr_sor)
    - [GA 최적화 범위 - C_M_BBR_GAR](#ga-최적화-범위---c_m_bbr_gar)
  - [조건식 개선 방향 연구](#조건식-개선-방향-연구)
  - [태그](#태그)

## 소개

이 문서는 STOM 주식 자동거래 시스템에서 볼린저밴드 반전 전략(Bollinger Band Reversal)을 위한 조건식과 최적화 범위를 제공합니다. 볼린저밴드 하단을 터치한 후 반등하는 패턴을 포착하여 매수하는 전략입니다.

## 가이드라인

- 모든 조건식은 Python 스타일의 의사코드로 작성되어 있으며, STOM 백테스터가 인식하는 변수/함수 규칙을 따릅니다.
- 최적화 조건식은 `self.vars[i]`로 치환하여 탐색 범위를 별도로 정의합니다.
- 최적화 범위 포맷: `self.vars[정수] = [[시작값, 종료값, 간격], 최적값]`
- 변수/함수 표기 및 사용 규칙은 Back_Testing_Guideline_Min.md를 따릅니다.

### 저장 이름 규칙

1. 기본 규칙:
   - `C`: Condition
   - `M`: Min (분봉)
   - `BBR`: Bollinger Band Reversal
   - `B`/`S`: 매수/매도 조건식
   - `BO`/`SO`: 매수/매도 최적화 조건식
   - `BOR`/`SOR`: 매수/매도 최적화 범위
   - `GAR`: GA 최적화 범위

---

# Condition - Min BBand Reversal

## 전략 개요

볼린저밴드 반전 전략은 과매도 구간에서의 반등을 포착하는 평균 회귀 전략입니다. 주요 특징:

- 볼린저밴드 하단(BBL) 터치 후 반등
- RSI 과매도 확인으로 신호 강화
- 체결강도 회복 확인
- 분당 거래대금 증가 확인

## 조건식

### 매수 조건식 - C_M_BBR_B

```python
# ================================
#  공통 계산 지표
# ================================
BBL_터치여부          = (현재가N(1) <= BBL_N(1) and 현재가 > BBL)
RSI_과매도여부        = (RSI_N(1) < 30 and RSI > 35)
체결강도회복여부      = (체결강도 > 체결강도N(1) and 체결강도 > 100)
거래대금증가여부      = (분당거래대금 > 분당거래대금평균(20) * 1.2)

# ================================
#  매수 조건
# ================================
매수 = True

# 공통 필터
if not (관심종목 == 1):
    매수 = False
elif not (93000 <= 시분초 <= 150000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# 볼린저밴드 하단 터치 후 반등
elif not BBL_터치여부:
    매수 = False

# RSI 과매도 확인
elif not RSI_과매도여부:
    매수 = False

# 체결강도 회복 확인
elif not 체결강도회복여부:
    매수 = False

# 거래대금 증가 확인
elif not 거래대금증가여부:
    매수 = False

# 시가총액별 세부 조건
elif 시가총액 < 3000:
    if not (-5.0 < 등락율 <= 15.0):
        매수 = False
    elif not (분봉고가 > 분봉시가):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
    elif not (전일비 > 50):
        매수 = False
    elif not (체결강도 >= 110 and 체결강도 <= 400):
        매수 = False
    elif not (분당매수수량 > 분당매도수량 * 1.2):
        매수 = False
    elif not (등락율각도(20) > 0):
        매수 = False
    elif not (당일거래대금 > 100 * 100):
        매수 = False
elif 시가총액 < 5000:
    if not (-4.0 < 등락율 <= 12.0):
        매수 = False
    elif not (분봉고가 > 분봉시가):
        매수 = False
    elif not (회전율 > 1.0):
        매수 = False
    elif not (전일비 > 40):
        매수 = False
    elif not (체결강도 >= 100 and 체결강도 <= 400):
        매수 = False
    elif not (분당매수수량 > 분당매도수량 * 1.1):
        매수 = False
    elif not (등락율각도(20) > 0):
        매수 = False
    elif not (당일거래대금 > 150 * 100):
        매수 = False
else:
    if not (-3.0 < 등락율 <= 10.0):
        매수 = False
    elif not (분봉고가 > 분봉시가):
        매수 = False
    elif not (회전율 > 0.8):
        매수 = False
    elif not (전일비 > 30):
        매수 = False
    elif not (체결강도 >= 90 and 체결강도 <= 400):
        매수 = False
    elif not (분당매수수량 > 분당매도수량 * 1.05):
        매수 = False
    elif not (등락율각도(20) > 0):
        매수 = False
    elif not (당일거래대금 > 200 * 100):
        매수 = False

# ================================
#  매수 호출
# ================================
if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식 - C_M_BBR_S

```python
# ================================
#  공통 계산 지표
# ================================
BBU_터치여부          = (현재가 >= BBU)
RSI_과매수여부        = (RSI > 70)
중간선이탈여부        = (현재가 < BBM and 현재가N(1) >= BBM_N(1))

매도 = False

# 상한가 부근 안전장치
if 등락율 > 29.5:
    매도 = True

# 손절 및 목표가 도달
elif 수익률 >= 3.0 or 수익률 <= -2.0:
    매도 = True

# 트레일링 스톱
elif 최고수익률 > 4.0 and 최고수익률 * 0.65 >= 수익률:
    매도 = True

# 보유시간 기반 청산
elif 보유시간 > 120:  # 120분 (2시간)
    매도 = True

# 볼린저밴드 상단 터치
elif BBU_터치여부:
    매도 = True

# RSI 과매수
elif RSI_과매수여부:
    매도 = True

# 중간선 하향 이탈
elif 중간선이탈여부:
    매도 = True

# 등락율 각도 하락
elif 등락율각도(10) < -3:
    매도 = True

# 체결강도 약화
elif 체결강도 < 체결강도평균(10) * 0.75:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

## 최적화 조건식

### 매수 최적화 조건식 - C_M_BBR_BO

```python
# ================================
#  공통 계산 지표
# ================================
BBL_터치여부          = (현재가N(1) <= BBL_N(1) and 현재가 > BBL)
RSI_과매도여부        = (RSI_N(1) < self.vars[1] and RSI > self.vars[2])
체결강도회복여부      = (체결강도 > 체결강도N(1) and 체결강도 > self.vars[3])
거래대금증가여부      = (분당거래대금 > 분당거래대금평균(20) * self.vars[4])

매수 = True

if not (관심종목 == 1):
    매수 = False
elif not (93000 <= 시분초 <= 150000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False
elif not BBL_터치여부:
    매수 = False
elif not RSI_과매도여부:
    매수 = False
elif not 체결강도회복여부:
    매수 = False
elif not 거래대금증가여부:
    매수 = False

elif 시가총액 < 3000:
    if not (self.vars[5] < 등락율 <= self.vars[6]):
        매수 = False
    elif not (분봉고가 > 분봉시가):
        매수 = False
    elif not (회전율 > self.vars[7]):
        매수 = False
    elif not (전일비 > self.vars[8]):
        매수 = False
    elif not (체결강도 >= self.vars[9] and 체결강도 <= 400):
        매수 = False
    elif not (분당매수수량 > 분당매도수량 * self.vars[10]):
        매수 = False
    elif not (등락율각도(20) > self.vars[11]):
        매수 = False
    elif not (당일거래대금 > self.vars[12] * 100):
        매수 = False

elif 시가총액 < 5000:
    if not (self.vars[13] < 등락율 <= self.vars[14]):
        매수 = False
    elif not (분봉고가 > 분봉시가):
        매수 = False
    elif not (회전율 > self.vars[15]):
        매수 = False
    elif not (전일비 > self.vars[16]):
        매수 = False
    elif not (체결강도 >= self.vars[17] and 체결강도 <= 400):
        매수 = False
    elif not (분당매수수량 > 분당매도수량 * self.vars[18]):
        매수 = False
    elif not (등락율각도(20) > self.vars[19]):
        매수 = False
    elif not (당일거래대금 > self.vars[20] * 100):
        매수 = False

else:
    if not (self.vars[21] < 등락율 <= self.vars[22]):
        매수 = False
    elif not (분봉고가 > 분봉시가):
        매수 = False
    elif not (회전율 > self.vars[23]):
        매수 = False
    elif not (전일비 > self.vars[24]):
        매수 = False
    elif not (체결강도 >= self.vars[25] and 체결강도 <= 400):
        매수 = False
    elif not (분당매수수량 > 분당매도수량 * self.vars[26]):
        매수 = False
    elif not (등락율각도(20) > self.vars[27]):
        매수 = False
    elif not (당일거래대금 > self.vars[28] * 100):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매수 최적화 범위 - C_M_BBR_BOR

```python
# 공통
self.vars[1]  = [[25, 35, 5], 30]                    # RSI 과매도 상한
self.vars[2]  = [[30, 40, 5], 35]                    # RSI 반등 하한
self.vars[3]  = [[90, 110, 10], 100]                 # 체결강도 회복 기준
self.vars[4]  = [[1.1, 1.3, 0.1], 1.2]               # 거래대금 증가 비율

# 시가총액 < 3000
self.vars[5]  = [[-6.0, -4.0, 1.0], -5.0]            # 등락율 하한
self.vars[6]  = [[13.0, 17.0, 2.0], 15.0]            # 등락율 상한
self.vars[7]  = [[1.2, 1.8, 0.3], 1.5]               # 회전율 하한
self.vars[8]  = [[40, 60, 10], 50]                   # 전일비 하한
self.vars[9]  = [[100, 120, 10], 110]                # 체결강도 하한
self.vars[10] = [[1.1, 1.3, 0.1], 1.2]               # 분당매수/매도 비율
self.vars[11] = [[-2, 2, 1], 0]                      # 등락율각도 하한
self.vars[12] = [[80, 120, 20], 100]                 # 당일거래대금(백만)

# 시가총액 < 5000
self.vars[13] = [[-5.0, -3.0, 1.0], -4.0]            # 등락율 하한
self.vars[14] = [[10.0, 14.0, 2.0], 12.0]            # 등락율 상한
self.vars[15] = [[0.8, 1.2, 0.2], 1.0]               # 회전율 하한
self.vars[16] = [[30, 50, 10], 40]                   # 전일비 하한
self.vars[17] = [[90, 110, 10], 100]                 # 체결강도 하한
self.vars[18] = [[1.0, 1.2, 0.1], 1.1]               # 분당매수/매도 비율
self.vars[19] = [[-2, 2, 1], 0]                      # 등락율각도 하한
self.vars[20] = [[130, 170, 20], 150]                # 당일거래대금(백만)

# 시가총액 >= 5000
self.vars[21] = [[-4.0, -2.0, 1.0], -3.0]            # 등락율 하한
self.vars[22] = [[8.0, 12.0, 2.0], 10.0]             # 등락율 상한
self.vars[23] = [[0.6, 1.0, 0.2], 0.8]               # 회전율 하한
self.vars[24] = [[25, 35, 5], 30]                    # 전일비 하한
self.vars[25] = [[80, 100, 10], 90]                  # 체결강도 하한
self.vars[26] = [[1.00, 1.10, 0.05], 1.05]           # 분당매수/매도 비율
self.vars[27] = [[-2, 2, 1], 0]                      # 등락율각도 하한
self.vars[28] = [[180, 220, 20], 200]                # 당일거래대금(백만)
```

### 매도 최적화 조건식 - C_M_BBR_SO

```python
BBU_터치여부          = (현재가 >= BBU)
RSI_과매수여부        = (RSI > self.vars[29])
중간선이탈여부        = (현재가 < BBM and 현재가N(1) >= BBM_N(1))

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= self.vars[30] or 수익률 <= self.vars[31]:
    매도 = True
elif 최고수익률 > self.vars[32] and 최고수익률 * self.vars[33] >= 수익률:
    매도 = True
elif 보유시간 > self.vars[34]:
    매도 = True
elif BBU_터치여부:
    매도 = True
elif RSI_과매수여부:
    매도 = True
elif 중간선이탈여부:
    매도 = True
elif 등락율각도(10) < -self.vars[35]:
    매도 = True
elif 체결강도 < 체결강도평균(10) * self.vars[36]:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

### 매도 최적화 범위 - C_M_BBR_SOR

```python
self.vars[29] = [[65, 75, 5], 70]                    # RSI 과매수 임계
self.vars[30] = [[2.5, 3.5, 0.5], 3.0]               # 목표 수익 실현
self.vars[31] = [[-2.5, -1.5, 0.5], -2.0]            # 최대 손실 컷
self.vars[32] = [[3.5, 4.5, 0.5], 4.0]               # 최고수익률 기준값
self.vars[33] = [[0.60, 0.70, 0.05], 0.65]           # 트레일링 보정 비율
self.vars[34] = [[90, 150, 30], 120]                 # 최대 보유시간(분)
self.vars[35] = [[2, 4, 1], 3]                       # 등락율각도 하락 임계
self.vars[36] = [[0.70, 0.80, 0.05], 0.75]           # 체결강도 약화 비율
```

### GA 최적화 범위 - C_M_BBR_GAR

```python
# 공통
self.vars[1]  = [[25, 30, 35], 30]
self.vars[2]  = [[30, 35, 40], 35]
self.vars[3]  = [[90, 100, 110], 100]
self.vars[4]  = [[1.1, 1.2, 1.3], 1.2]

# 시가총액 < 3000
self.vars[5]  = [[-6.0, -5.0, -4.0], -5.0]
self.vars[6]  = [[13.0, 15.0, 17.0], 15.0]
self.vars[9]  = [[100, 110, 120], 110]

# 시가총액 < 5000
self.vars[13] = [[-5.0, -4.0, -3.0], -4.0]
self.vars[14] = [[10.0, 12.0, 14.0], 12.0]
self.vars[17] = [[90, 100, 110], 100]

# 시가총액 >= 5000
self.vars[21] = [[-4.0, -3.0, -2.0], -3.0]
self.vars[22] = [[8.0, 10.0, 12.0], 10.0]
self.vars[25] = [[80, 90, 100], 90]

# 매도
self.vars[29] = [[65, 70, 75], 70]
self.vars[30] = [[2.5, 3.0, 3.5], 3.0]
self.vars[31] = [[-2.5, -2.0, -1.5], -2.0]
self.vars[33] = [[0.60, 0.65, 0.70], 0.65]
```

---

## 조건식 개선 방향 연구

1) **볼린저밴드 폭 확인**
   - 밴드 폭이 일정 수준 이상일 때만 진입
   - 변동성 확인

2) **다중 터치 패턴**
   - 연속 2회 터치 후 반등 패턴
   - 더 강한 지지 확인

3) **거래량 프로파일**
   - 밴드 하단에서 거래량 증가 확인
   - 매집 패턴 확인

4) **시간대별 차등 적용**
   - 장 초반: 더 보수적
   - 장 중반: 표준 적용
   - 장 마감 전: 진입 금지

5) **손절 강화**
   - BBL 재이탈 시 즉시 청산
   - RSI 30 재진입 시 청산

## 태그
- #주식트레이딩
- #분봉트레이딩
- #매수조건
- #매도조건
- #최적화
- #유전알고리즘
- #파이썬
- #트레이딩로직
- #볼린저밴드
- #평균회귀전략
- #RSI
- #리스크관리
