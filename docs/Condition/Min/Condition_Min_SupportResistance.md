# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Min.md 가이드라인 반영

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
- [Condition - Min SupportResistance](#condition---min-supportresistance)
  - [전략 개요](#전략-개요)
  - [조건식](#조건식)
  - [최적화 조건식](#최적화-조건식)
  - [조건식 개선 방향 연구](#조건식-개선-방향-연구)
  - [태그](#태그)

## 소개

이 문서는 STOM 주식 자동거래 시스템에서 지지/저항 레벨 전략(Support/Resistance Level Strategy)을 위한 조건식을 제공합니다. 과거 가격 데이터를 분석하여 주요 지지/저항 레벨을 식별하고 반등/돌파 패턴을 포착하는 전략입니다.

## 가이드라인

- 모든 조건식은 Python 스타일의 의사코드로 작성되어 있으며, STOM 백테스터가 인식하는 변수/함수 규칙을 따릅니다.

---

# Condition - Min SupportResistance

## 전략 개요

지지/저항 레벨 전략은 주요 가격 레벨에서의 반응을 포착합니다:

- 최근 60분 고가/저가를 지지/저항 레벨로 설정
- 지지선 근처 반등 포착 (하단 3% 이내)
- 반등 신호 확인 (가격, 거래량, 지표)
- 저항선 돌파 시 추가 상승 기대

## 조건식

### 매수 조건식

```python
# ================================
#  공통 계산 지표
# ================================
지지레벨              = 최저현재가(60) if 데이터길이 > 60 else 저가
저항레벨              = 최고현재가(60) if 데이터길이 > 60 else 고가
중간레벨              = (지지레벨 + 저항레벨) / 2

# 지지선 근처 여부 (지지레벨 대비 +0~3% 범위)
지지선근처여부        = (지지레벨 <= 현재가 <= 지지레벨 * 1.03)

# 지지선 반등 확인 (이전 분봉에서 지지선 터치 or 이탈)
지지선터치여부        = (현재가N(1) <= 지지레벨 * 1.01 or 저가N(1) <= 지지레벨)

# 반등 신호
반등신호              = (현재가 > 현재가N(1) and 현재가 > 지지레벨 * 1.005)
연속상승여부          = (현재가 > 현재가N(1) and 현재가N(1) >= 현재가N(2))

# 거래량 및 지표 확인
거래량증가여부        = (분당거래대금 > 분당거래대금평균(20) * 1.5)
매수세우위여부        = (분당매수수량 > 분당매도수량 * 1.5)
RSI반등여부           = (RSI > 40 and RSI < 70 and RSI > RSI_N(1))

# 추가 확인 지표
체결강도강함여부      = (체결강도 >= 110)
이동평균지지여부      = (현재가 > 이동평균(20))

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

# 지지선 근처 확인
elif not 지지선근처여부:
    매수 = False

# 지지선 터치 확인
elif not 지지선터치여부:
    매수 = False

# 반등 신호 확인
elif not 반등신호:
    매수 = False

# 거래량 증가 확인
elif not 거래량증가여부:
    매수 = False

# 매수세 우위 확인
elif not 매수세우위여부:
    매수 = False

# RSI 반등 확인
elif not RSI반등여부:
    매수 = False

# 시가총액별 세부 조건
elif 시가총액 < 3000:
    if not (체결강도 >= 115):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
    elif not 이동평균지지여부:
        매수 = False
    elif not 연속상승여부:
        매수 = False
    elif not (STOCH_K > 20 and STOCH_K < 80):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * 1.8):
        매수 = False
elif 시가총액 < 5000:
    if not (체결강도 >= 110):
        매수 = False
    elif not (회전율 > 1.2):
        매수 = False
    elif not 이동평균지지여부:
        매수 = False
    elif not 연속상승여부:
        매수 = False
    elif not (STOCH_K > 20 and STOCH_K < 75):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * 1.6):
        매수 = False
else:
    if not (체결강도 >= 105):
        매수 = False
    elif not (회전율 > 1.0):
        매수 = False
    elif not 이동평균지지여부:
        매수 = False
    elif not (STOCH_K > 20 and STOCH_K < 70):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * 1.5):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식

```python
# ================================
#  공통 계산 지표
# ================================
저항레벨              = 최고현재가(60) if 데이터길이 > 60 else 고가
지지레벨              = 최저현재가(60) if 데이터길이 > 60 else 저가

# 저항선 근처 도달 (저항레벨 대비 -2% 이내)
저항선근처여부        = (현재가 >= 저항레벨 * 0.98)

# 지지선 이탈 신호
지지선이탈여부        = (현재가 < 지지레벨 * 0.98)

# 반등 실패 신호
반등실패신호          = (현재가 < 현재가N(1) and 현재가N(1) < 현재가N(2))

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 3.5 or 수익률 <= -2.0:
    매도 = True
elif 최고수익률 > 4.5 and 최고수익률 * 0.70 >= 수익률:
    매도 = True
elif 보유시간 > 1800:  # 30분
    매도 = True
elif 저항선근처여부 and 보유시간 > 300:  # 5분 이후 저항선 근처
    매도 = True
elif 지지선이탈여부:
    매도 = True
elif 반등실패신호:
    매도 = True
elif 체결강도 < 95:
    매도 = True
elif RSI < 35:
    매도 = True
elif STOCH_K < STOCH_D and STOCH_K < 20:
    매도 = True
elif 시분초 >= 145500:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

## 최적화 조건식

### 매수 최적화 조건식 - C_M_SR_BO

```python
지지레벨              = 최저현재가(60) if 데이터길이 > 60 else 저가
저항레벨              = 최고현재가(60) if 데이터길이 > 60 else 고가
중간레벨              = (지지레벨 + 저항레벨) / 2

지지선근처여부        = (지지레벨 <= 현재가 <= 지지레벨 * (1 + self.vars[1] / 100))
지지선터치여부        = (현재가N(1) <= 지지레벨 * (1 + self.vars[2] / 100) or 저가N(1) <= 지지레벨)
반등신호              = (현재가 > 현재가N(1) and 현재가 > 지지레벨 * (1 + self.vars[3] / 100))
연속상승여부          = (현재가 > 현재가N(1) and 현재가N(1) >= 현재가N(2))

거래량증가여부        = (분당거래대금 > 분당거래대금평균(20) * self.vars[4])
매수세우위여부        = (분당매수수량 > 분당매도수량 * self.vars[5])
RSI반등여부           = (RSI > self.vars[6] and RSI < self.vars[7] and RSI > RSI_N(1))

체결강도강함여부      = (체결강도 >= self.vars[8])
이동평균지지여부      = (현재가 > 이동평균(20))

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
elif not 지지선근처여부:
    매수 = False
elif not 지지선터치여부:
    매수 = False
elif not 반등신호:
    매수 = False
elif not 거래량증가여부:
    매수 = False
elif not 매수세우위여부:
    매수 = False
elif not RSI반등여부:
    매수 = False

elif 시가총액 < 3000:
    if not (체결강도 >= self.vars[9]):
        매수 = False
    elif not (회전율 > self.vars[10]):
        매수 = False
    elif not 이동평균지지여부:
        매수 = False
    elif not 연속상승여부:
        매수 = False
    elif not (STOCH_K > self.vars[11] and STOCH_K < self.vars[12]):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * self.vars[13]):
        매수 = False
elif 시가총액 < 5000:
    if not (체결강도 >= self.vars[14]):
        매수 = False
    elif not (회전율 > self.vars[15]):
        매수 = False
    elif not 이동평균지지여부:
        매수 = False
    elif not 연속상승여부:
        매수 = False
    elif not (STOCH_K > self.vars[16] and STOCH_K < self.vars[17]):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * self.vars[18]):
        매수 = False
else:
    if not (체결강도 >= self.vars[19]):
        매수 = False
    elif not (회전율 > self.vars[20]):
        매수 = False
    elif not 이동평균지지여부:
        매수 = False
    elif not (STOCH_K > self.vars[21] and STOCH_K < self.vars[22]):
        매수 = False
    elif not (분당거래대금 > 분당거래대금평균(20) * self.vars[23]):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매수 최적화 범위 - C_M_SR_BOR

```python
# 공통
self.vars[1]  = [[2.5, 3.5, 0.5], 3.0]               # 지지선 근처 범위(%)
self.vars[2]  = [[0.8, 1.2, 0.2], 1.0]               # 지지선 터치 범위(%)
self.vars[3]  = [[0.3, 0.7, 0.2], 0.5]               # 반등 확인 범위(%)
self.vars[4]  = [[1.3, 1.7, 0.2], 1.5]               # 거래량 증가 비율
self.vars[5]  = [[1.3, 1.7, 0.2], 1.5]               # 매수세 우위 비율
self.vars[6]  = [[35, 45, 5], 40]                    # RSI 하한
self.vars[7]  = [[65, 75, 5], 70]                    # RSI 상한
self.vars[8]  = [[105, 115, 5], 110]                 # 체결강도 하한

# 시가총액 < 3000
self.vars[9]  = [[110, 120, 5], 115]                 # 체결강도 하한
self.vars[10] = [[1.2, 1.8, 0.3], 1.5]               # 회전율 하한
self.vars[11] = [[15, 25, 5], 20]                    # STOCH_K 하한
self.vars[12] = [[75, 85, 5], 80]                    # STOCH_K 상한
self.vars[13] = [[1.5, 2.1, 0.3], 1.8]               # 거래대금 비율

# 시가총액 < 5000
self.vars[14] = [[105, 115, 5], 110]                 # 체결강도 하한
self.vars[15] = [[1.0, 1.4, 0.2], 1.2]               # 회전율 하한
self.vars[16] = [[15, 25, 5], 20]                    # STOCH_K 하한
self.vars[17] = [[70, 80, 5], 75]                    # STOCH_K 상한
self.vars[18] = [[1.3, 1.9, 0.3], 1.6]               # 거래대금 비율

# 시가총액 >= 5000
self.vars[19] = [[100, 110, 5], 105]                 # 체결강도 하한
self.vars[20] = [[0.8, 1.2, 0.2], 1.0]               # 회전율 하한
self.vars[21] = [[15, 25, 5], 20]                    # STOCH_K 하한
self.vars[22] = [[65, 75, 5], 70]                    # STOCH_K 상한
self.vars[23] = [[1.2, 1.8, 0.3], 1.5]               # 거래대금 비율
```

### 매도 최적화 조건식 - C_M_SR_SO

```python
저항레벨              = 최고현재가(60) if 데이터길이 > 60 else 고가
지지레벨              = 최저현재가(60) if 데이터길이 > 60 else 저가

저항선근처여부        = (현재가 >= 저항레벨 * (1 - self.vars[25] / 100))
지지선이탈여부        = (현재가 < 지지레벨 * (1 - self.vars[26] / 100))
반등실패신호          = (현재가 < 현재가N(1) and 현재가N(1) < 현재가N(2))

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= self.vars[27] or 수익률 <= self.vars[28]:
    매도 = True
elif 최고수익률 > self.vars[29] and 최고수익률 * self.vars[30] >= 수익률:
    매도 = True
elif 보유시간 > self.vars[31]:
    매도 = True
elif 저항선근처여부 and 보유시간 > self.vars[32]:
    매도 = True
elif 지지선이탈여부:
    매도 = True
elif 반등실패신호:
    매도 = True
elif 체결강도 < self.vars[33]:
    매도 = True
elif RSI < self.vars[34]:
    매도 = True
elif STOCH_K < STOCH_D and STOCH_K < self.vars[35]:
    매도 = True
elif 시분초 >= 145500:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

### 매도 최적화 범위 - C_M_SR_SOR

```python
self.vars[25] = [[1.5, 2.5, 0.5], 2.0]               # 저항선 근처 범위(%)
self.vars[26] = [[1.5, 2.5, 0.5], 2.0]               # 지지선 이탈 범위(%)
self.vars[27] = [[3.0, 4.0, 0.5], 3.5]               # 목표 수익 실현(%)
self.vars[28] = [[-2.5, -1.5, 0.5], -2.0]            # 최대 손실 컷(%)
self.vars[29] = [[4.0, 5.0, 0.5], 4.5]               # 최고수익률 기준값(%)
self.vars[30] = [[0.65, 0.75, 0.05], 0.70]           # 트레일링 보정 비율
self.vars[31] = [[1500, 2100, 300], 1800]            # 최대 보유시간(초)
self.vars[32] = [[240, 360, 60], 300]                # 저항선 확인 시간(초)
self.vars[33] = [[90, 100, 5], 95]                   # 체결강도 하한
self.vars[34] = [[30, 40, 5], 35]                    # RSI 하한
self.vars[35] = [[15, 25, 5], 20]                    # STOCH_K 하한
```

### GA 최적화 범위 - C_M_SR_GAR

```python
# 매수 조건
self.vars[1]  = [2.5, 3.5]                           # 지지선 근처 범위(%)
self.vars[2]  = [0.8, 1.2]                           # 지지선 터치 범위(%)
self.vars[3]  = [0.3, 0.7]                           # 반등 확인 범위(%)
self.vars[4]  = [1.3, 1.7]                           # 거래량 증가 비율
self.vars[5]  = [1.3, 1.7]                           # 매수세 우위 비율
self.vars[6]  = [35, 45]                             # RSI 하한
self.vars[7]  = [65, 75]                             # RSI 상한
self.vars[8]  = [105, 115]                           # 체결강도 하한

# 시가총액 < 3000
self.vars[9]  = [110, 120]                           # 체결강도 하한
self.vars[10] = [1.2, 1.8]                           # 회전율 하한
self.vars[11] = [15, 25]                             # STOCH_K 하한
self.vars[12] = [75, 85]                             # STOCH_K 상한
self.vars[13] = [1.5, 2.1]                           # 거래대금 비율

# 시가총액 < 5000
self.vars[14] = [105, 115]                           # 체결강도 하한
self.vars[15] = [1.0, 1.4]                           # 회전율 하한
self.vars[16] = [15, 25]                             # STOCH_K 하한
self.vars[17] = [70, 80]                             # STOCH_K 상한
self.vars[18] = [1.3, 1.9]                           # 거래대금 비율

# 시가총액 >= 5000
self.vars[19] = [100, 110]                           # 체결강도 하한
self.vars[20] = [0.8, 1.2]                           # 회전율 하한
self.vars[21] = [15, 25]                             # STOCH_K 하한
self.vars[22] = [65, 75]                             # STOCH_K 상한
self.vars[23] = [1.2, 1.8]                           # 거래대금 비율

# 매도 조건
self.vars[25] = [1.5, 2.5]                           # 저항선 근처 범위(%)
self.vars[26] = [1.5, 2.5]                           # 지지선 이탈 범위(%)
self.vars[27] = [3.0, 4.0]                           # 목표 수익 실현(%)
self.vars[28] = [-2.5, -1.5]                         # 최대 손실 컷(%)
self.vars[29] = [4.0, 5.0]                           # 최고수익률 기준값(%)
self.vars[30] = [0.65, 0.75]                         # 트레일링 보정 비율
self.vars[31] = [1500, 2100]                         # 최대 보유시간(초)
self.vars[32] = [240, 360]                           # 저항선 확인 시간(초)
self.vars[33] = [90, 100]                            # 체결강도 하한
self.vars[34] = [30, 40]                             # RSI 하한
self.vars[35] = [15, 25]                             # STOCH_K 하한
```

---

## 조건식 개선 방향 연구

1) **동적 레벨 식별**
   - Swing High/Low 포인트 자동 식별
   - 여러 시간프레임 레벨 종합
   - 레벨 강도 평가 (터치 횟수, 반응 강도)

2) **레벨 신뢰도 평가**
   - 과거 반응 이력 분석
   - 터치 횟수와 반등 성공률
   - 거래량 프로파일 분석

3) **반등/돌파 판별**
   - False breakout 필터링
   - 돌파 후 재테스트 패턴
   - 반등 강도 측정

4) **다중 레벨 관리**
   - 주요 레벨과 부차 레벨 구분
   - 레벨 간 거리 고려
   - 레벨 클러스터 분석

5) **리스크 관리**
   - 지지선 이탈 즉시 청산
   - 저항선 근처 이익 실현
   - 트레일링 스톱 (최고수익의 70%)

## 태그
- #주식트레이딩
- #분봉트레이딩
- #매수조건
- #매도조건
- #최적화
- #지지저항
- #레벨트레이딩
- #프라이스액션
- #리스크관리
