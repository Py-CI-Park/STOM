# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
- [Condition - Min ADX TrendStrength](#condition---min-adx-trendstrength)
  - [전략 개요](#전략-개요)
  - [조건식](#조건식)
  - [최적화 조건식](#최적화-조건식)
  - [조건식 개선 방향 연구](#조건식-개선-방향-연구)
  - [태그](#태그)

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **ADX 추세 강도 전략**을 정의한다.

- **대상 시간 구간**: 09:00 ~ 15:18 (장 전체)
- **대상 종목**: 가격대 1,000~50,000원, 시가총액 조건
- **전략 타입**: ADX 추세 강도 기반 방향성 전략
- **핵심 변수**: ADX, PLUS_DI, MINUS_DI, 방향성 명확도
- **업데이트 이력**:
  - 초기 문서 작성: ADX 추세 강도 전략

## 소개

이 문서는 STOM 주식 자동거래 시스템에서 ADX 추세 강도 전략(ADX Trend Strength Strategy)을 위한 조건식을 제공합니다. ADX 지표를 활용하여 강한 추세를 식별하고 +DI/-DI 방향성을 확인하여 진입하는 전략입니다.

## 가이드라인

- 모든 조건식은 Python 스타일의 의사코드로 작성되어 있으며, STOM 백테스터가 인식하는 변수/함수 규칙을 따릅니다.

---

# Condition - Min ADX TrendStrength

## 전략 개요

ADX 추세 강도 전략은 ADX 지표로 강한 추세를 식별합니다:

- ADX > 25 (강한 추세)
- +DI > -DI (상승 추세)
- ADX 상승 중 확인
- 추세 지속성 평가

## 조건식

### 매수 조건식

```python
# ================================
#  공통 계산 지표
# ================================
강한추세여부          = (ADX > 25)
상승방향여부          = (PLUS_DI > MINUS_DI)
방향성명확여부        = (PLUS_DI - MINUS_DI > 5)
ADX상승여부           = (ADX > ADX_N(1) and ADX_N(1) > ADX_N(2))
추세강화여부          = (강한추세여부 and 상승방향여부 and ADX상승여부)
가격정배열여부        = (현재가 > 이동평균(5) > 이동평균(20))
거래량동반여부        = (분당거래대금 > 분당거래대금평균(20) * 1.3)

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

# 추세 강화 확인
elif not 추세강화여부:
    매수 = False

# 방향성 명확 확인
elif not 방향성명확여부:
    매수 = False

# 가격 정배열 확인
elif not 가격정배열여부:
    매수 = False

# 거래량 동반 확인
elif not 거래량동반여부:
    매수 = False

# 시가총액별 세부 조건
elif 시가총액 < 3000:
    if not (ADX > 30):
        매수 = False
    elif not (PLUS_DI - MINUS_DI > 8):
        매수 = False
    elif not (체결강도 >= 115):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
    elif not (RSI > 50 and RSI < 75):
        매수 = False
    elif not (현재가 > (고가 - (고가 - 저가) * 0.30)):
        매수 = False
elif 시가총액 < 5000:
    if not (ADX > 27):
        매수 = False
    elif not (PLUS_DI - MINUS_DI > 6):
        매수 = False
    elif not (체결강도 >= 110):
        매수 = False
    elif not (회전율 > 1.2):
        매수 = False
    elif not (RSI > 48 and RSI < 70):
        매수 = False
    elif not (현재가 > (고가 - (고가 - 저가) * 0.35)):
        매수 = False
else:
    if not (ADX > 25):
        매수 = False
    elif not (PLUS_DI - MINUS_DI > 5):
        매수 = False
    elif not (체결강도 >= 105):
        매수 = False
    elif not (회전율 > 1.0):
        매수 = False
    elif not (RSI > 45 and RSI < 70):
        매수 = False
    elif not (현재가 > (고가 - (고가 - 저가) * 0.40)):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식

```python
# ================================
#  공통 계산 지표
# ================================
추세약화여부          = (ADX < 20 or ADX < ADX_N(1))
방향전환신호          = (PLUS_DI < MINUS_DI)
급락신호              = (PLUS_DI - MINUS_DI < -5)

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 3.5 or 수익률 <= -2.0:
    매도 = True
elif 최고수익률 > 4.5 and 최고수익률 * 0.70 >= 수익률:
    매도 = True
elif 보유시간 > 2400:  # 40분
    매도 = True
elif 추세약화여부:
    매도 = True
elif 방향전환신호:
    매도 = True
elif 급락신호:
    매도 = True
elif 체결강도 < 95:
    매도 = True
elif RSI < 40:
    매도 = True
elif 현재가 < 이동평균(5):
    매도 = True
elif 시분초 >= 145500:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

## 최적화 조건식

### 매수 최적화 조건식 - C_M_ADX_BO

```python
강한추세여부          = (ADX > self.vars[1])
상승방향여부          = (PLUS_DI > MINUS_DI)
방향성명확여부        = (PLUS_DI - MINUS_DI > self.vars[2])
ADX상승여부           = (ADX > ADX_N(1) and ADX_N(1) > ADX_N(2))
추세강화여부          = (강한추세여부 and 상승방향여부 and ADX상승여부)
가격정배열여부        = (현재가 > 이동평균(5) > 이동평균(20))
거래량동반여부        = (분당거래대금 > 분당거래대금평균(20) * self.vars[3])

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
elif not 추세강화여부:
    매수 = False
elif not 방향성명확여부:
    매수 = False
elif not 가격정배열여부:
    매수 = False
elif not 거래량동반여부:
    매수 = False

elif 시가총액 < 3000:
    if not (ADX > self.vars[4]):
        매수 = False
    elif not (PLUS_DI - MINUS_DI > self.vars[5]):
        매수 = False
    elif not (체결강도 >= self.vars[6]):
        매수 = False
    elif not (회전율 > self.vars[7]):
        매수 = False
    elif not (RSI > self.vars[8] and RSI < self.vars[9]):
        매수 = False
    elif not (현재가 > (고가 - (고가 - 저가) * self.vars[10] / 100)):
        매수 = False
elif 시가총액 < 5000:
    if not (ADX > self.vars[11]):
        매수 = False
    elif not (PLUS_DI - MINUS_DI > self.vars[12]):
        매수 = False
    elif not (체결강도 >= self.vars[13]):
        매수 = False
    elif not (회전율 > self.vars[14]):
        매수 = False
    elif not (RSI > self.vars[15] and RSI < self.vars[16]):
        매수 = False
    elif not (현재가 > (고가 - (고가 - 저가) * self.vars[17] / 100)):
        매수 = False
else:
    if not (ADX > self.vars[18]):
        매수 = False
    elif not (PLUS_DI - MINUS_DI > self.vars[19]):
        매수 = False
    elif not (체결강도 >= self.vars[20]):
        매수 = False
    elif not (회전율 > self.vars[21]):
        매수 = False
    elif not (RSI > self.vars[22] and RSI < self.vars[23]):
        매수 = False
    elif not (현재가 > (고가 - (고가 - 저가) * self.vars[24] / 100)):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매수 최적화 범위 - C_M_ADX_BOR

```python
# 공통
self.vars[1]  = [[20, 30, 5], 25]                    # ADX 임계값
self.vars[2]  = [[3, 7, 2], 5]                       # DI 차이 임계
self.vars[3]  = [[1.2, 1.4, 0.1], 1.3]               # 거래량 동반 비율

# 시가총액 < 3000
self.vars[4]  = [[25, 35, 5], 30]                    # ADX 하한
self.vars[5]  = [[6, 10, 2], 8]                      # DI 차이 하한
self.vars[6]  = [[110, 120, 5], 115]                 # 체결강도 하한
self.vars[7]  = [[1.2, 1.8, 0.3], 1.5]               # 회전율 하한
self.vars[8]  = [[45, 55, 5], 50]                    # RSI 하한
self.vars[9]  = [[70, 80, 5], 75]                    # RSI 상한
self.vars[10] = [[25, 35, 5], 30]                    # 고가 근접도(%)

# 시가총액 < 5000
self.vars[11] = [[22, 32, 5], 27]                    # ADX 하한
self.vars[12] = [[4, 8, 2], 6]                       # DI 차이 하한
self.vars[13] = [[105, 115, 5], 110]                 # 체결강도 하한
self.vars[14] = [[1.0, 1.4, 0.2], 1.2]               # 회전율 하한
self.vars[15] = [[43, 53, 5], 48]                    # RSI 하한
self.vars[16] = [[65, 75, 5], 70]                    # RSI 상한
self.vars[17] = [[30, 40, 5], 35]                    # 고가 근접도(%)

# 시가총액 >= 5000
self.vars[18] = [[20, 30, 5], 25]                    # ADX 하한
self.vars[19] = [[3, 7, 2], 5]                       # DI 차이 하한
self.vars[20] = [[100, 110, 5], 105]                 # 체결강도 하한
self.vars[21] = [[0.8, 1.2, 0.2], 1.0]               # 회전율 하한
self.vars[22] = [[40, 50, 5], 45]                    # RSI 하한
self.vars[23] = [[65, 75, 5], 70]                    # RSI 상한
self.vars[24] = [[35, 45, 5], 40]                    # 고가 근접도(%)
```

### 매도 최적화 조건식 - C_M_ADX_SO

```python
추세약화여부          = (ADX < self.vars[26] or ADX < ADX_N(1))
방향전환신호          = (PLUS_DI < MINUS_DI)
급락신호              = (PLUS_DI - MINUS_DI < -self.vars[27])

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= self.vars[28] or 수익률 <= self.vars[29]:
    매도 = True
elif 최고수익률 > self.vars[30] and 최고수익률 * self.vars[31] >= 수익률:
    매도 = True
elif 보유시간 > self.vars[32]:
    매도 = True
elif 추세약화여부:
    매도 = True
elif 방향전환신호:
    매도 = True
elif 급락신호:
    매도 = True
elif 체결강도 < self.vars[33]:
    매도 = True
elif RSI < self.vars[34]:
    매도 = True
elif 현재가 < 이동평균(5):
    매도 = True
elif 시분초 >= 145500:
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

### 매도 최적화 범위 - C_M_ADX_SOR

```python
self.vars[26] = [[15, 25, 5], 20]                    # ADX 약화 임계
self.vars[27] = [[3, 7, 2], 5]                       # 급락 DI 차이
self.vars[28] = [[3.0, 4.0, 0.5], 3.5]               # 목표 수익 실현(%)
self.vars[29] = [[-2.5, -1.5, 0.5], -2.0]            # 최대 손실 컷(%)
self.vars[30] = [[4.0, 5.0, 0.5], 4.5]               # 최고수익률 기준값(%)
self.vars[31] = [[0.65, 0.75, 0.05], 0.70]           # 트레일링 보정 비율
self.vars[32] = [[2100, 2700, 300], 2400]            # 최대 보유시간(초)
self.vars[33] = [[90, 100, 5], 95]                   # 체결강도 하한
self.vars[34] = [[35, 45, 5], 40]                    # RSI 하한
```

### 매수·매도 통합 최적화 범위 - C_M_ADX_OR_Min

핵심 변수만 선별하여 통합 최적화 수행

```python
# 매수 핵심 변수 (BOR에서 선별)
self.vars[1]  = [[20, 30, 5], 25]                    # ADX 임계값
self.vars[2]  = [[3, 7, 2], 5]                       # DI 차이 임계
self.vars[3]  = [[1.2, 1.4, 0.1], 1.3]               # 거래량 동반 비율

# 시가총액 < 3000 핵심
self.vars[4]  = [[25, 35, 5], 30]                    # ADX 하한
self.vars[6]  = [[110, 120, 5], 115]                 # 체결강도 하한
self.vars[8]  = [[45, 55, 5], 50]                    # RSI 하한

# 매도 핵심 변수 (SOR에서 선별)
self.vars[28] = [[3.0, 4.0, 0.5], 3.5]               # 목표 수익 실현(%)
self.vars[29] = [[-2.5, -1.5, 0.5], -2.0]            # 최대 손실 컷(%)
self.vars[31] = [[0.65, 0.75, 0.05], 0.70]           # 트레일링 보정 비율
self.vars[32] = [[2100, 2700, 300], 2400]            # 최대 보유시간(초)

# 총 경우의 수: 3 × 3 × 3 × 3 × 3 × 3 × 2 × 3 × 3 × 3 = 354,294
```

### GA 최적화 범위 - C_M_ADX_GAR

```python
# 매수 조건
self.vars[1]  = [20, 30]                             # ADX 임계값
self.vars[2]  = [3, 7]                               # DI 차이 임계
self.vars[3]  = [1.2, 1.4]                           # 거래량 동반 비율

# 시가총액 < 3000
self.vars[4]  = [25, 35]                             # ADX 하한
self.vars[5]  = [6, 10]                              # DI 차이 하한
self.vars[6]  = [110, 120]                           # 체결강도 하한
self.vars[7]  = [1.2, 1.8]                           # 회전율 하한
self.vars[8]  = [45, 55]                             # RSI 하한
self.vars[9]  = [70, 80]                             # RSI 상한
self.vars[10] = [25, 35]                             # 고가 근접도(%)

# 시가총액 < 5000
self.vars[11] = [22, 32]                             # ADX 하한
self.vars[12] = [4, 8]                               # DI 차이 하한
self.vars[13] = [105, 115]                           # 체결강도 하한
self.vars[14] = [1.0, 1.4]                           # 회전율 하한
self.vars[15] = [43, 53]                             # RSI 하한
self.vars[16] = [65, 75]                             # RSI 상한
self.vars[17] = [30, 40]                             # 고가 근접도(%)

# 시가총액 >= 5000
self.vars[18] = [20, 30]                             # ADX 하한
self.vars[19] = [3, 7]                               # DI 차이 하한
self.vars[20] = [100, 110]                           # 체결강도 하한
self.vars[21] = [0.8, 1.2]                           # 회전율 하한
self.vars[22] = [40, 50]                             # RSI 하한
self.vars[23] = [65, 75]                             # RSI 상한
self.vars[24] = [35, 45]                             # 고가 근접도(%)

# 매도 조건
self.vars[26] = [15, 25]                             # ADX 약화 임계
self.vars[27] = [3, 7]                               # 급락 DI 차이
self.vars[28] = [3.0, 4.0]                           # 목표 수익 실현(%)
self.vars[29] = [-2.5, -1.5]                         # 최대 손실 컷(%)
self.vars[30] = [4.0, 5.0]                           # 최고수익률 기준값(%)
self.vars[31] = [0.65, 0.75]                         # 트레일링 보정 비율
self.vars[32] = [2100, 2700]                         # 최대 보유시간(초)
self.vars[33] = [90, 100]                            # 체결강도 하한
self.vars[34] = [35, 45]                             # RSI 하한
```

---

## 조건식 개선 방향 연구

1) **ADX 기간 최적화**
   - 기본 14일 vs 다른 기간
   - 시장 변동성에 따른 조정
   - 종목별 최적 기간 탐색

2) **DI 크로스오버 활용**
   - +DI/-DI 교차 시점 포착
   - 교차 후 지속 시간 확인
   - 교차 강도 측정

3) **추세 지속성 평가**
   - ADX 상승 지속 기간
   - 추세 강도 변화율
   - 추세 피로도 측정

4) **다중 시간프레임 분석**
   - 상위 TF ADX 확인
   - 하위 TF 진입 타이밍
   - TF 간 ADX 정렬

5) **리스크 관리**
   - ADX < 20 추세 약화 청산
   - DI 방향 전환 즉시 청산
   - 트레일링 스톱 (최고수익의 70%)

## 태그
- #주식트레이딩
- #분봉트레이딩
- #매수조건
- #매도조건
- #최적화
- #ADX지표
- #추세강도
- #방향성지표
- #리스크관리
