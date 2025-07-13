# 조건식 (Condition) - RSI 다층 필터링 전략

- STOM 주식 자동거래에 사용하기 위한 분봉 기반 조건식 문서
- Back_Testing_Guideline_Min.md 에 있는 조건식을 사용하여 만든 조건식
- 아이디어.md의 "RSI 다층 필터링 전략"을 분봉 변수로 구현

## 목차
- [조건식 (Condition) - RSI 다층 필터링 전략](#조건식-condition---rsi-다층-필터링-전략)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - RSI 다층 필터링](#condition---rsi-다층-필터링)
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

이 문서는 분봉 데이터를 활용한 RSI 다층 필터링 전략을 구현합니다. 여러 시간 프레임의 RSI를 활용하여 정확한 매수/매도 신호를 포착하고, 과매수/과매도 상황을 정밀하게 분석합니다.

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 분봉 데이터 기반 주식 거래의 자동화를 목표로 합니다.
- 다양한 기간의 RSI 지표를 조합하여 신호의 신뢰성을 높입니다.
- 최적화 조건식은 변수의 범위를 설정하여 최적의 매수/매도 시점을 찾습니다.

### 저장 이름 규칙

- `C_MIN_RSI_MULTI_B`: RSI 다층 필터링 매수 조건식
- `C_MIN_RSI_MULTI_S`: RSI 다층 필터링 매도 조건식
- `C_MIN_RSI_MULTI_BO`: RSI 다층 필터링 매수 최적화 조건식
- `C_MIN_RSI_MULTI_SO`: RSI 다층 필터링 매도 최적화 조건식

---

# Condition - RSI 다층 필터링

## 조건식

### 매수 조건식

```python
# RSI 다층 필터링 변수 계산
RSI_5 = RSI(5)      # 단기 RSI
RSI_14 = RSI(14)    # 표준 RSI
RSI_21 = RSI(21)    # 장기 RSI

# RSI 추세 분석
RSI_5_이전 = RSI_N(5, 1)
RSI_14_이전 = RSI_N(14, 1)
RSI_21_이전 = RSI_N(21, 1)

# 상대 강도 분석
RSI_상승추세 = (RSI_5 > RSI_5_이전) and (RSI_14 > RSI_14_이전)
RSI_발산체크 = abs(RSI_5 - RSI_14) < 15  # RSI 발산 방지

# 공통 선결 조건
if not (시분 >= 930 and 시분 <= 1500):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (0.5 < 등락율 <= 29.0):
    매수 = False
elif not (시가총액 >= 300):  # 300억원 이상
    매수 = False

# RSI 기본 조건 (과매도 상태에서 반등)
elif not (25 <= RSI_5 <= 45):  # 단기 RSI 과매도 구간에서 반등
    매수 = False
elif not (30 <= RSI_14 <= 50):  # 표준 RSI 과매도 구간에서 반등
    매수 = False
elif not (35 <= RSI_21 <= 55):  # 장기 RSI 중립 구간
    매수 = False

# RSI 층별 필터링
elif not RSI_상승추세:  # RSI 상승 추세 확인
    매수 = False
elif not RSI_발산체크:  # RSI 발산 방지
    매수 = False
elif not (RSI_5 > RSI_5_이전 + 2):  # 단기 RSI 명확한 상승
    매수 = False

# 추가 기술적 지표 확인
elif not (MACDH > 0):  # MACD 히스토그램 양수
    매수 = False
elif not (현재가 > 이동평균(20)):  # 20분봉 이동평균선 위
    매수 = False

# 거래량 및 가격 조건
elif not (분당거래대금 >= 분당거래대금평균(20) * 1.5):
    매수 = False
elif not (체결강도 >= 110):
    매수 = False
elif not (현재가 >= 최고분봉고가(10) * 1.01):  # 10분봉 최고가 돌파
    매수 = False

# 위험 요소 체크
elif not (회전율 > 0.3):  # 유동성 확인
    매수 = False
elif 라운드피겨위5호가이내:  # 라운드피겨 근처 제외
    매수 = False

# 특별 RSI 패턴 확인 (황금 교차 패턴)
RSI_황금교차 = (RSI_5 > RSI_14) and (RSI_N(5, 1) <= RSI_N(14, 1))
if RSI_황금교차 and RSI_5 < 60:  # 과매수 구간 제외
    매수 = True
elif not 매수:
    매수 = False

# 최종 매수 실행
if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식

```python
# RSI 다층 분석 변수
RSI_5 = RSI(5)
RSI_14 = RSI(14)
RSI_21 = RSI(21)

RSI_5_이전 = RSI_N(5, 1)
RSI_14_이전 = RSI_N(14, 1)

# 상한가 근접 매도
if 등락율 > 28.0:
    매도 = True

# RSI 과매수 매도 신호
elif RSI_5 > 80:  # 단기 RSI 과매수
    매도 = True
elif RSI_14 > 75:  # 표준 RSI 과매수
    매도 = True
elif RSI_21 > 70:  # 장기 RSI 과매수
    매도 = True

# RSI 하락 전환 신호
elif (RSI_5 < RSI_5_이전 - 3) and (RSI_14 < RSI_14_이전 - 2):  # RSI 급락
    매도 = True

# RSI 데드크로스 패턴
elif (RSI_5 < RSI_14) and (RSI_N(5, 1) >= RSI_N(14, 1)) and RSI_5 > 50:
    매도 = True

# 수익률 기반 매도
elif 수익률 >= 7.0:  # 고수익 실현
    매도 = True
elif 수익률 <= -2.5:  # 손절매
    매도 = True

# 추적 손절
elif 최고수익률 >= 4.0 and (최고수익률 - 수익률) >= 2.5:
    매도 = True

# 시간 기반 매도
elif 보유시간 >= 300:  # 5시간 이상 보유
    매도 = True

# 기술적 지표 매도 신호
elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):  # MACD 데드크로스
    매도 = True
elif 현재가 < 이동평균(20) and 이동평균(20) < 이동평균(20, 1):
    매도 = True

# 거래량 감소 신호
elif 분당거래대금 < 분당거래대금평균(10) * 0.4:
    매도 = True
elif 체결강도 < 90 and 분당매도수량 > 분당매수수량 * 1.8:
    매도 = True

# 최종 매도 실행
if 매도:
    self.Sell(종목코드, 종목명, 보유수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

## 최적화 조건식

### 매수 최적화 조건식

```python
# 최적화 변수들
RSI_5_하한 = self.vars[0]    # RSI 5 하한
RSI_5_상한 = self.vars[1]    # RSI 5 상한
RSI_14_하한 = self.vars[2]   # RSI 14 하한
RSI_14_상한 = self.vars[3]   # RSI 14 상한
RSI_21_하한 = self.vars[4]   # RSI 21 하한
RSI_21_상한 = self.vars[5]   # RSI 21 상한
거래대금배수 = self.vars[6]   # 거래대금 배수
체결강도기준 = self.vars[7]   # 체결강도 기준
RSI_상승폭 = self.vars[8]    # RSI 상승폭 기준
RSI_발산임계 = self.vars[9]  # RSI 발산 임계값

# RSI 계산
RSI_5 = RSI(5)
RSI_14 = RSI(14)
RSI_21 = RSI(21)

RSI_5_이전 = RSI_N(5, 1)
RSI_14_이전 = RSI_N(14, 1)
RSI_21_이전 = RSI_N(21, 1)

# RSI 추세 및 발산 분석
RSI_상승추세 = (RSI_5 > RSI_5_이전) and (RSI_14 > RSI_14_이전)
RSI_발산체크 = abs(RSI_5 - RSI_14) < RSI_발산임계

# 공통 선결 조건
if not (시분 >= 930 and 시분 <= 1500):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not (0.5 < 등락율 <= 29.0):
    매수 = False
elif not (시가총액 >= 300):
    매수 = False

# 최적화된 RSI 조건
elif not (RSI_5_하한 <= RSI_5 <= RSI_5_상한):
    매수 = False
elif not (RSI_14_하한 <= RSI_14 <= RSI_14_상한):
    매수 = False
elif not (RSI_21_하한 <= RSI_21 <= RSI_21_상한):
    매수 = False

# 최적화된 RSI 필터링
elif not RSI_상승추세:
    매수 = False
elif not RSI_발산체크:
    매수 = False
elif not (RSI_5 > RSI_5_이전 + RSI_상승폭):
    매수 = False

# 최적화된 기술적 지표
elif not (MACDH > 0):
    매수 = False
elif not (현재가 > 이동평균(20)):
    매수 = False

# 최적화된 거래량 조건
elif not (분당거래대금 >= 분당거래대금평균(20) * 거래대금배수):
    매수 = False
elif not (체결강도 >= 체결강도기준):
    매수 = False
elif not (현재가 >= 최고분봉고가(10) * 1.01):
    매수 = False
elif not (회전율 > 0.3):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# RSI 황금교차 패턴
RSI_황금교차 = (RSI_5 > RSI_14) and (RSI_N(5, 1) <= RSI_N(14, 1))
if RSI_황금교차 and RSI_5 < 60:
    매수 = True
elif not 매수:
    매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매수 최적화 범위

```python
self.vars[0] = [[20, 35, 5], 25]           # RSI_5_하한
self.vars[1] = [[40, 55, 5], 45]           # RSI_5_상한
self.vars[2] = [[25, 40, 5], 30]           # RSI_14_하한
self.vars[3] = [[45, 60, 5], 50]           # RSI_14_상한
self.vars[4] = [[30, 45, 5], 35]           # RSI_21_하한
self.vars[5] = [[50, 65, 5], 55]           # RSI_21_상한
self.vars[6] = [[1.2, 2.0, 0.2], 1.5]     # 거래대금배수
self.vars[7] = [[100, 130, 10], 110]       # 체결강도기준
self.vars[8] = [[1, 4, 1], 2]              # RSI_상승폭
self.vars[9] = [[10, 25, 5], 15]           # RSI_발산임계
```

### 매도 최적화 조건식

```python
# 최적화 변수들
RSI_5_과매수 = self.vars[0]    # RSI 5 과매수 기준
RSI_14_과매수 = self.vars[1]   # RSI 14 과매수 기준
RSI_21_과매수 = self.vars[2]   # RSI 21 과매수 기준
RSI_급락폭_5 = self.vars[3]    # RSI 5 급락폭
RSI_급락폭_14 = self.vars[4]   # RSI 14 급락폭
수익실현기준 = self.vars[5]     # 수익 실현 기준
손절기준 = self.vars[6]        # 손절 기준
추적손절기준 = self.vars[7]    # 추적 손절 기준
보유시간기준 = self.vars[8]    # 보유시간 기준

# RSI 계산
RSI_5 = RSI(5)
RSI_14 = RSI(14)
RSI_21 = RSI(21)
RSI_5_이전 = RSI_N(5, 1)
RSI_14_이전 = RSI_N(14, 1)

# 상한가 근접 매도
if 등락율 > 28.0:
    매도 = True

# 최적화된 RSI 과매수 매도
elif RSI_5 > RSI_5_과매수:
    매도 = True
elif RSI_14 > RSI_14_과매수:
    매도 = True
elif RSI_21 > RSI_21_과매수:
    매도 = True

# 최적화된 RSI 하락 신호
elif (RSI_5 < RSI_5_이전 - RSI_급락폭_5) and (RSI_14 < RSI_14_이전 - RSI_급락폭_14):
    매도 = True

# RSI 데드크로스 패턴
elif (RSI_5 < RSI_14) and (RSI_N(5, 1) >= RSI_N(14, 1)) and RSI_5 > 50:
    매도 = True

# 최적화된 수익률 기반 매도
elif 수익률 >= 수익실현기준:
    매도 = True
elif 수익률 <= -손절기준:
    매도 = True
elif 최고수익률 >= 4.0 and (최고수익률 - 수익률) >= 추적손절기준:
    매도 = True

# 최적화된 시간 매도
elif 보유시간 >= 보유시간기준:
    매도 = True

# 기타 매도 신호
elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
    매도 = True
elif 현재가 < 이동평균(20) and 이동평균(20) < 이동평균(20, 1):
    매도 = True
elif 분당거래대금 < 분당거래대금평균(10) * 0.4:
    매도 = True
elif 체결강도 < 90 and 분당매도수량 > 분당매수수량 * 1.8:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 보유수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 최적화 범위

```python
self.vars[0] = [[75, 85, 2], 80]           # RSI_5_과매수
self.vars[1] = [[70, 80, 2], 75]           # RSI_14_과매수
self.vars[2] = [[65, 75, 2], 70]           # RSI_21_과매수
self.vars[3] = [[2, 5, 1], 3]              # RSI_급락폭_5
self.vars[4] = [[1, 4, 1], 2]              # RSI_급락폭_14
self.vars[5] = [[5.0, 10.0, 1.0], 7.0]    # 수익실현기준
self.vars[6] = [[2.0, 4.0, 0.5], 2.5]     # 손절기준
self.vars[7] = [[2.0, 4.0, 0.5], 2.5]     # 추적손절기준
self.vars[8] = [[240, 420, 60], 300]       # 보유시간기준
```

### 매수 매도 최적화 범위

```python
# 매수 최적화 범위
self.vars[0] = [[20, 35, 5], 25]           # RSI_5_하한
self.vars[1] = [[40, 55, 5], 45]           # RSI_5_상한
self.vars[2] = [[25, 40, 5], 30]           # RSI_14_하한
self.vars[3] = [[45, 60, 5], 50]           # RSI_14_상한
self.vars[4] = [[30, 45, 5], 35]           # RSI_21_하한
self.vars[5] = [[50, 65, 5], 55]           # RSI_21_상한
self.vars[6] = [[1.2, 2.0, 0.2], 1.5]     # 거래대금배수
self.vars[7] = [[100, 130, 10], 110]       # 체결강도기준
self.vars[8] = [[1, 4, 1], 2]              # RSI_상승폭
self.vars[9] = [[10, 25, 5], 15]           # RSI_발산임계

# 매도 최적화 범위
self.vars[10] = [[75, 85, 2], 80]          # RSI_5_과매수
self.vars[11] = [[70, 80, 2], 75]          # RSI_14_과매수
self.vars[12] = [[65, 75, 2], 70]          # RSI_21_과매수
self.vars[13] = [[2, 5, 1], 3]             # RSI_급락폭_5
self.vars[14] = [[1, 4, 1], 2]             # RSI_급락폭_14
self.vars[15] = [[5.0, 10.0, 1.0], 7.0]   # 수익실현기준
self.vars[16] = [[2.0, 4.0, 0.5], 2.5]    # 손절기준
self.vars[17] = [[2.0, 4.0, 0.5], 2.5]    # 추적손절기준
self.vars[18] = [[240, 420, 60], 300]      # 보유시간기준
```

### GA 최적화 범위

```python
# 매수 GA 최적화 범위
self.vars[0] = [[20, 25, 30, 35], 25]                    # RSI_5_하한
self.vars[1] = [[40, 45, 50, 55], 45]                    # RSI_5_상한
self.vars[2] = [[25, 30, 35, 40], 30]                    # RSI_14_하한
self.vars[3] = [[45, 50, 55, 60], 50]                    # RSI_14_상한
self.vars[4] = [[30, 35, 40, 45], 35]                    # RSI_21_하한
self.vars[5] = [[50, 55, 60, 65], 55]                    # RSI_21_상한
self.vars[6] = [[1.2, 1.4, 1.6, 1.8, 2.0], 1.5]        # 거래대금배수
self.vars[7] = [[100, 110, 120, 130], 110]               # 체결강도기준
self.vars[8] = [[1, 2, 3, 4], 2]                         # RSI_상승폭
self.vars[9] = [[10, 15, 20, 25], 15]                    # RSI_발산임계

# 매도 GA 최적화 범위
self.vars[10] = [[75, 78, 80, 82, 85], 80]               # RSI_5_과매수
self.vars[11] = [[70, 72, 75, 77, 80], 75]               # RSI_14_과매수
self.vars[12] = [[65, 67, 70, 72, 75], 70]               # RSI_21_과매수
self.vars[13] = [[2, 3, 4, 5], 3]                        # RSI_급락폭_5
self.vars[14] = [[1, 2, 3, 4], 2]                        # RSI_급락폭_14
self.vars[15] = [[5.0, 6.0, 7.0, 8.0, 9.0, 10.0], 7.0] # 수익실현기준
self.vars[16] = [[2.0, 2.5, 3.0, 3.5, 4.0], 2.5]       # 손절기준
self.vars[17] = [[2.0, 2.5, 3.0, 3.5, 4.0], 2.5]       # 추적손절기준
self.vars[18] = [[240, 270, 300, 330, 360, 390, 420], 300] # 보유시간기준