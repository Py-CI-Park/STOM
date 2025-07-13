# 조건식 (Condition) - MACD 정밀 신호 체계

- STOM 주식 자동거래에 사용하기 위한 분봉 기반 조건식 문서
- Back_Testing_Guideline_Min.md 에 있는 조건식을 사용하여 만든 조건식
- 아이디어.md의 "MACD 정밀 신호 체계"를 분봉 변수로 구현

## 목차
- [조건식 (Condition) - MACD 정밀 신호 체계](#조건식-condition---macd-정밀-신호-체계)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - MACD 정밀 신호](#condition---macd-정밀-신호)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)
  - [최적화 조건식](#최적화-조건식)
    - [매수 최적화 조건식](#매수-최적화-조건식)
    - [매수 최적화 범위](#매수-최적화-범위)
    - [매도 최적화 조건식](#매도-최적화-조건식)
    - [매도 최적화 범위](#매도-최적화-범위)
    - [매수 매도 최적화 범위](#매수-매도-최적화-범위)
    - [GA 최적화 범위](#ga-최적화-범위)

## 소개

이 문서는 분봉 데이터를 활용한 MACD 정밀 신호 체계를 구현합니다. MACD 라인, 시그널 라인, 히스토그램을 종합적으로 분석하여 매매 신호의 정확도를 극대화합니다.

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 분봉 데이터 기반 주식 거래의 자동화를 목표로 합니다.
- MACD의 다양한 구성 요소를 활용하여 매매 시점을 정밀하게 판단합니다.
- 최적화 조건식은 변수의 범위를 설정하여 최적의 매수/매도 시점을 찾습니다.

### 저장 이름 규칙

- `C_MIN_MACD_PREC_B`: MACD 정밀 신호 매수 조건식
- `C_MIN_MACD_PREC_S`: MACD 정밀 신호 매도 조건식
- `C_MIN_MACD_PREC_BO`: MACD 정밀 신호 매수 최적화 조건식
- `C_MIN_MACD_PREC_SO`: MACD 정밀 신호 매도 최적화 조건식

---

# Condition - MACD 정밀 신호

## 조건식

### 매수 조건식

```python
# MACD 정밀 신호 변수 계산
MACD_현재 = MACD
MACD_신호 = MACDS
MACD_히스토그램 = MACDH

# 이전 값들
MACD_이전 = MACD_N(1)
MACD_신호_이전 = MACDS_N(1)
MACD_히스토그램_이전 = MACDH_N(1)

# MACD 더블 확인 (2분봉 전과 3분봉 전)
MACD_2전 = MACD_N(2)
MACD_신호_2전 = MACDS_N(2)
MACD_히스토그램_2전 = MACDH_N(2)

# MACD 패턴 분석
MACD_황금교차 = (MACD_현재 > MACD_신호) and (MACD_이전 <= MACD_신호_이전)
MACD_상승추세 = (MACD_현재 > MACD_이전) and (MACD_신호 > MACD_신호_이전)
MACD_히스토그램_증가 = MACD_히스토그램 > MACD_히스토그램_이전
MACD_제로라인_돌파 = (MACD_현재 > 0) and (MACD_이전 <= 0)

# 공통 선결 조건
if not (시분 >= 930 and 시분 <= 1500):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (0.5 < 등락율 <= 29.0):
    매수 = False
elif not (시가총액 >= 300):  # 300억원 이상
    매수 = False

# MACD 기본 조건
elif not (MACD_현재 > MACD_이전):  # MACD 상승
    매수 = False
elif not (MACD_히스토그램 > 0):  # 히스토그램 양수
    매수 = False
elif not MACD_히스토그램_증가:  # 히스토그램 증가
    매수 = False

# MACD 정밀 필터링
elif not (MACD_현재 > MACD_신호 * 1.001):  # MACD가 시그널보다 확실히 위
    매수 = False
elif MACD_현재 > 0.5:  # MACD 과매수 방지
    매수 = False
elif not (abs(MACD_현재) > abs(MACD_이전) * 1.05):  # MACD 확실한 강화
    매수 = False

# 추가 기술적 지표 확인
elif not (RSI(14) >= 35 and RSI(14) <= 65):  # RSI 중립 구간
    매수 = False
elif not (현재가 > 이동평균(20)):  # 20분봉 이동평균선 위
    매수 = False

# 거래량 및 강도 조건
elif not (분당거래대금 >= 분당거래대금평균(20) * 1.3):
    매수 = False
elif not (체결강도 >= 105):
    매수 = False
elif not (분당매수량 > 분당매도량):  # 매수 우세
    매수 = False

# 가격 모멘텀 확인
elif not (현재가 >= 최고분봉고가(10) * 0.995):  # 10분봉 고가 근처
    매수 = False
elif not (현재가 > 시가 * 1.005):  # 시가 대비 상승
    매수 = False

# 위험 요소 체크
elif not (회전율 > 0.2):  # 유동성 확인
    매수 = False
elif 라운드피겨위5호가이내:  # 라운드피겨 근처 제외
    매수 = False

# MACD 특별 패턴 확인
# 1. 황금교차 패턴
if MACD_황금교차 and MACD_히스토그램 > 0:
    매수 = True
# 2. 제로라인 돌파 패턴
elif MACD_제로라인_돌파 and MACD_히스토그램_증가:
    매수 = True
# 3. 다이버전스 후 반등 패턴
elif (MACD_현재 > MACD_2전) and (MACD_히스토그램 > MACD_히스토그램_2전) and (MACD_현재 < 0):
    매수 = True
elif not 매수:
    매수 = False

# 최종 매수 실행
if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식

```python
# MACD 정밀 신호 변수
MACD_현재 = MACD
MACD_신호 = MACDS
MACD_히스토그램 = MACDH

MACD_이전 = MACD_N(1)
MACD_신호_이전 = MACDS_N(1)
MACD_히스토그램_이전 = MACDH_N(1)

# MACD 패턴 분석
MACD_데드크로스 = (MACD_현재 < MACD_신호) and (MACD_이전 >= MACD_신호_이전)
MACD_하락추세 = (MACD_현재 < MACD_이전) and (MACD_신호 < MACD_신호_이전)
MACD_히스토그램_감소 = MACD_히스토그램 < MACD_히스토그램_이전
MACD_제로라인_하향돌파 = (MACD_현재 < 0) and (MACD_이전 >= 0)

# 상한가 근접 매도
if 등락율 > 28.0:
    매도 = True

# MACD 매도 신호
elif MACD_데드크로스:  # MACD 데드크로스
    매도 = True
elif MACD_제로라인_하향돌파:  # 제로라인 하향 돌파
    매도 = True
elif (MACD_히스토그램 < 0) and MACD_히스토그램_감소:  # 히스토그램 음수 & 감소
    매도 = True

# MACD 과매수 신호
elif MACD_현재 > 0.8:  # MACD 과매수
    매도 = True
elif (MACD_현재 < MACD_이전 * 0.95) and MACD_현재 > 0:  # MACD 급락
    매도 = True

# MACD 추세 전환 신호
elif (MACD_현재 < MACD_신호) and (MACD_히스토그램 < MACD_히스토그램_이전 * 0.8):
    매도 = True

# 수익률 기반 매도
elif 수익률 >= 6.0:  # 고수익 실현
    매도 = True
elif 수익률 <= -2.0:  # 손절매
    매도 = True

# MACD 기반 추적 손절 (MACD가 약화되면 빠른 매도)
elif 최고수익률 >= 3.0 and (최고수익률 - 수익률) >= 1.5 and MACD_히스토그램 < 0:
    매도 = True

# 시간 기반 매도
elif 보유시간 >= 240:  # 4시간 이상 보유
    매도 = True

# 추가 기술적 지표 매도 신호
elif RSI(14) > 75:  # RSI 과매수
    매도 = True
elif 현재가 < 이동평균(20) and 이동평균(20) < 이동평균(20, 1):
    매도 = True

# 거래량 기반 매도 신호
elif 분당거래대금 < 분당거래대금평균(10) * 0.5:
    매도 = True
elif 체결강도 < 85 and 분당매도수량 > 분당매수수량 * 2.0:
    매도 = True

# MACD 발산 매도 (가격은 상승하지만 MACD는 하락)
elif (현재가 > 현재가_N(5)) and (MACD_현재 < MACD_N(5)) and 수익률 > 2.0:
    매도 = True

# 최종 매도 실행
if 매도:
    self.Sell(종목코드, 종목명, 보유수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

## 최적화 조건식

### 매수 최적화 조건식

```python
# 최적화 변수들
MACD_신호비율 = self.vars[0]    # MACD/시그널 비율
MACD_과매수한계 = self.vars[1]   # MACD 과매수 한계
MACD_강화비율 = self.vars[2]     # MACD 강화 비율
RSI_하한 = self.vars[3]          # RSI 하한
RSI_상한 = self.vars[4]          # RSI 상한
거래대금배수 = self.vars[5]       # 거래대금 배수
체결강도기준 = self.vars[6]       # 체결강도 기준
고가근접비율 = self.vars[7]       # 고가 근접 비율
시가상승비율 = self.vars[8]       # 시가 상승 비율

# MACD 계산
MACD_현재 = MACD
MACD_신호 = MACDS
MACD_히스토그램 = MACDH

MACD_이전 = MACD_N(1)
MACD_신호_이전 = MACDS_N(1)
MACD_히스토그램_이전 = MACDH_N(1)
MACD_2전 = MACD_N(2)
MACD_히스토그램_2전 = MACDH_N(2)

# MACD 패턴 분석
MACD_황금교차 = (MACD_현재 > MACD_신호) and (MACD_이전 <= MACD_신호_이전)
MACD_히스토그램_증가 = MACD_히스토그램 > MACD_히스토그램_이전
MACD_제로라인_돌파 = (MACD_현재 > 0) and (MACD_이전 <= 0)

# 공통 선결 조건
if not (시분 >= 930 and 시분 <= 1500):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (0.5 < 등락율 <= 29.0):
    매수 = False
elif not (시가총액 >= 300):
    매수 = False

# 최적화된 MACD 조건
elif not (MACD_현재 > MACD_이전):
    매수 = False
elif not (MACD_히스토그램 > 0):
    매수 = False
elif not MACD_히스토그램_증가:
    매수 = False
elif not (MACD_현재 > MACD_신호 * MACD_신호비율):
    매수 = False
elif MACD_현재 > MACD_과매수한계:
    매수 = False
elif not (abs(MACD_현재) > abs(MACD_이전) * MACD_강화비율):
    매수 = False

# 최적화된 기술적 지표
elif not (RSI(14) >= RSI_하한 and RSI(14) <= RSI_상한):
    매수 = False
elif not (현재가 > 이동평균(20)):
    매수 = False

# 최적화된 거래량 조건
elif not (분당거래대금 >= 분당거래대금평균(20) * 거래대금배수):
    매수 = False
elif not (체결강도 >= 체결강도기준):
    매수 = False
elif not (분당매수량 > 분당매도량):
    매수 = False

# 최적화된 가격 조건
elif not (현재가 >= 최고분봉고가(10) * 고가근접비율):
    매수 = False
elif not (현재가 > 시가 * 시가상승비율):
    매수 = False
elif not (회전율 > 0.2):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# MACD 패턴 확인
if MACD_황금교차 and MACD_히스토그램 > 0:
    매수 = True
elif MACD_제로라인_돌파 and MACD_히스토그램_증가:
    매수 = True
elif (MACD_현재 > MACD_2전) and (MACD_히스토그램 > MACD_히스토그램_2전) and (MACD_현재 < 0):
    매수 = True
elif not 매수:
    매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매수 최적화 범위

```python
self.vars[0] = [[1.001, 1.010, 0.002], 1.001]    # MACD_신호비율
self.vars[1] = [[0.3, 0.8, 0.1], 0.5]            # MACD_과매수한계
self.vars[2] = [[1.02, 1.15, 0.02], 1.05]        # MACD_강화비율
self.vars[3] = [[30, 45, 5], 35]                  # RSI_하한
self.vars[4] = [[60, 75, 5], 65]                  # RSI_상한
self.vars[5] = [[1.1, 1.8, 0.1], 1.3]            # 거래대금배수
self.vars[6] = [[100, 120, 5], 105]               # 체결강도기준
self.vars[7] = [[0.990, 1.000, 0.002], 0.995]    # 고가근접비율
self.vars[8] = [[1.002, 1.015, 0.002], 1.005]    # 시가상승비율
```

### 매도 최적화 조건식

```python
# 최적화 변수들
MACD_과매수기준 = self.vars[0]    # MACD 과매수 기준
MACD_급락비율 = self.vars[1]      # MACD 급락 비율
히스토그램_급락비율 = self.vars[2] # 히스토그램 급락 비율
수익실현기준 = self.vars[3]       # 수익 실현 기준
손절기준 = self.vars[4]          # 손절 기준
추적손절기준 = self.vars[5]      # 추적 손절 기준
보유시간기준 = self.vars[6]      # 보유시간 기준
RSI_과매수기준 = self.vars[7]     # RSI 과매수 기준

# MACD 계산
MACD_현재 = MACD
MACD_신호 = MACDS
MACD_히스토그램 = MACDH
MACD_이전 = MACD_N(1)
MACD_신호_이전 = MACDS_N(1)
MACD_히스토그램_이전 = MACDH_N(1)

# MACD 패턴 분석
MACD_데드크로스 = (MACD_현재 < MACD_신호) and (MACD_이전 >= MACD_신호_이전)
MACD_제로라인_하향돌파 = (MACD_현재 < 0) and (MACD_이전 >= 0)

# 상한가 근접 매도
if 등락율 > 28.0:
    매도 = True

# 최적화된 MACD 매도 신호
elif MACD_데드크로스:
    매도 = True
elif MACD_제로라인_하향돌파:
    매도 = True
elif (MACD_히스토그램 < 0) and (MACD_히스토그램 < MACD_히스토그램_이전):
    매도 = True
elif MACD_현재 > MACD_과매수기준:
    매도 = True
elif (MACD_현재 < MACD_이전 * MACD_급락비율) and MACD_현재 > 0:
    매도 = True
elif (MACD_현재 < MACD_신호) and (MACD_히스토그램 < MACD_히스토그램_이전 * 히스토그램_급락비율):
    매도 = True

# 최적화된 수익률 매도
elif 수익률 >= 수익실현기준:
    매도 = True
elif 수익률 <= -손절기준:
    매도 = True
elif 최고수익률 >= 3.0 and (최고수익률 - 수익률) >= 추적손절기준 and MACD_히스토그램 < 0:
    매도 = True

# 최적화된 시간 매도
elif 보유시간 >= 보유시간기준:
    매도 = True

# 기타 최적화된 매도 신호
elif RSI(14) > RSI_과매수기준:
    매도 = True
elif 현재가 < 이동평균(20) and 이동평균(20) < 이동평균(20, 1):
    매도 = True
elif 분당거래대금 < 분당거래대금평균(10) * 0.5:
    매도 = True
elif 체결강도 < 85 and 분당매도수량 > 분당매수수량 * 2.0:
    매도 = True
elif (현재가 > 현재가_N(5)) and (MACD_현재 < MACD_N(5)) and 수익률 > 2.0:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 보유수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 최적화 범위

```python
self.vars[0] = [[0.6, 1.0, 0.1], 0.8]          # MACD_과매수기준
self.vars[1] = [[0.90, 0.98, 0.02], 0.95]      # MACD_급락비율
self.vars[2] = [[0.70, 0.90, 0.05], 0.8]       # 히스토그램_급락비율
self.vars[3] = [[4.0, 8.0, 1.0], 6.0]          # 수익실현기준
self.vars[4] = [[1.5, 3.0, 0.5], 2.0]          # 손절기준
self.vars[5] = [[1.0, 2.5, 0.5], 1.5]          # 추적손절기준
self.vars[6] = [[180, 300, 30], 240]            # 보유시간기준
self.vars[7] = [[70, 80, 2], 75]                # RSI_과매수기준
```

### 매수 매도 최적화 범위

```python
# 매수 최적화 범위
self.vars[0] = [[1.001, 1.010, 0.002], 1.001]    # MACD_신호비율
self.vars[1] = [[0.3, 0.8, 0.1], 0.5]            # MACD_과매수한계
self.vars[2] = [[1.02, 1.15, 0.02], 1.05]        # MACD_강화비율
self.vars[3] = [[30, 45, 5], 35]                  # RSI_하한
self.vars[4] = [[60, 75, 5], 65]                  # RSI_상한
self.vars[5] = [[1.1, 1.8, 0.1], 1.3]            # 거래대금배수
self.vars[6] = [[100, 120, 5], 105]               # 체결강도기준
self.vars[7] = [[0.990, 1.000, 0.002], 0.995]    # 고가근접비율
self.vars[8] = [[1.002, 1.015, 0.002], 1.005]    # 시가상승비율

# 매도 최적화 범위
self.vars[9] = [[0.6, 1.0, 0.1], 0.8]            # MACD_과매수기준
self.vars[10] = [[0.90, 0.98, 0.02], 0.95]       # MACD_급락비율
self.vars[11] = [[0.70, 0.90, 0.05], 0.8]        # 히스토그램_급락비율
self.vars[12] = [[4.0, 8.0, 1.0], 6.0]           # 수익실현기준
self.vars[13] = [[1.5, 3.0, 0.5], 2.0]           # 손절기준
self.vars[14] = [[1.0, 2.5, 0.5], 1.5]           # 추적손절기준
self.vars[15] = [[180, 300, 30], 240]             # 보유시간기준
self.vars[16] = [[70, 80, 2], 75]                 # RSI_과매수기준
```

### GA 최적화 범위

```python
# 매수 GA 최적화 범위
self.vars[0] = [[1.001, 1.003, 1.005, 1.008, 1.010], 1.001]      # MACD_신호비율
self.vars[1] = [[0.3, 0.4, 0.5, 0.6, 0.7, 0.8], 0.5]             # MACD_과매수한계
self.vars[2] = [[1.02, 1.05, 1.08, 1.10, 1.12, 1.15], 1.05]      # MACD_강화비율
self.vars[3] = [[30, 35, 40, 45], 35]                             # RSI_하한
self.vars[4] = [[60, 65, 70, 75], 65]                             # RSI_상한
self.vars[5] = [[1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8], 1.3]  # 거래대금배수
self.vars[6] = [[100, 105, 110, 115, 120], 105]                   # 체결강도기준
self.vars[7] = [[0.990, 0.993, 0.995, 0.997, 1.000], 0.995]      # 고가근접비율
self.vars[8] = [[1.002, 1.005, 1.008, 1.010, 1.012, 1.015], 1.005] # 시가상승비율

# 매도 GA 최적화 범위
self.vars[9] = [[0.6, 0.7, 0.8, 0.9, 1.0], 0.8]                  # MACD_과매수기준
self.vars[10] = [[0.90, 0.92, 0.94, 0.95, 0.96, 0.98], 0.95]     # MACD_급락비율
self.vars[11] = [[0.70, 0.75, 0.80, 0.85, 0.90], 0.8]            # 히스토그램_급락비율
self.vars[12] = [[4.0, 5.0, 6.0, 7.0, 8.0], 6.0]                 # 수익실현기준
self.vars[13] = [[1.5, 2.0, 2.5, 3.0], 2.0]                      # 손절기준
self.vars[14] = [[1.0, 1.5, 2.0, 2.5], 1.5]                      # 추적손절기준
self.vars[15] = [[180, 210, 240, 270, 300], 240]                  # 보유시간기준
self.vars[16] = [[70, 72, 75, 77, 80], 75]                        # RSI_과매수기준