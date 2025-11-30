# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성한 Min 조건식
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
- [Condition - Min RSI Oversold](#condition---min-rsi-oversold)
  - [전략 개요](#전략-개요)
  - [조건식](#조건식)
  - [최적화 조건식](#최적화-조건식)
  - [조건식 개선 방향 연구](#조건식-개선-방향-연구)
  - [태그](#태그)

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **장중(09:30~15:00) RSI 과매도 반등 전략**을 정의한다.

- **대상 시간 구간**: 09:30:00 ~ 15:00:00 (장중)
- **대상 종목**: 관심종목, 시가총액 차등 (3,000억 기준), 가격대 1,000원~50,000원
- **전략 타입**: RSI 과매도 반등 + 스토캐스틱 확인 (RSI Oversold)
- **핵심 변수**: RSI, STOCHSK, STOCHSD, 이동평균(20), 체결강도, 분당거래대금
- **업데이트 이력**:
  - 초기 문서 작성

## 소개

이 문서는 STOM 주식 자동거래 시스템에서 RSI 과매도 반등 전략(RSI Oversold Rebound)을 위한 조건식과 최적화 범위를 제공합니다. RSI가 과매도 구간에 진입한 후 반등하는 패턴을 포착하는 평균 회귀 전략입니다.

## 가이드라인

- 모든 조건식은 Python 스타일의 의사코드로 작성되어 있으며, STOM 백테스터가 인식하는 변수/함수 규칙을 따릅니다.

---

# Condition - Min RSI Oversold

## 전략 개요

RSI 과매도 반등 전략은 단기 과매도 구간에서의 반등을 포착합니다. 주요 특징:

- RSI 30 이하 진입 후 35 이상 반등
- 스토캐스틱 확인으로 신호 강화
- 가격이 이동평균 위에 위치
- 거래량 증가 확인

## 조건식

### 매수 조건식 - C_M_RSO_B

```python
RSI_반등여부          = (RSI_N(1) <= 30 and RSI > 35)
스토캐스틱_반등여부  = (STOCHSK > STOCHSD and STOCHSK_N(1) <= STOCHSD_N(1))
이평위치여부          = (현재가 > 이동평균(20))
거래량증가여부        = (분당거래대금 > 분당거래대금평균(20) * 1.3)

매수 = True

if not (관심종목 == 1):
    매수 = False
elif not (93000 <= 시분초 <= 150000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not RSI_반등여부:
    매수 = False
elif not 스토캐스틱_반등여부:
    매수 = False
elif not 이평위치여부:
    매수 = False
elif not 거래량증가여부:
    매수 = False
elif 시가총액 < 3000:
    if not (-3.0 < 등락율 <= 12.0):
        매수 = False
    elif not (체결강도 >= 110):
        매수 = False
else:
    if not (-2.0 < 등락율 <= 10.0):
        매수 = False
    elif not (체결강도 >= 100):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식 - C_M_RSO_S

```python
RSI_과매수여부        = (RSI > 70)
스토캐스틱_과매수여부 = (STOCHSK > 80)

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 3.0 or 수익률 <= -2.0:
    매도 = True
elif 최고수익률 > 4.0 and 최고수익률 * 0.65 >= 수익률:
    매도 = True
elif 보유시간 > 120:
    매도 = True
elif RSI_과매수여부:
    매도 = True
elif 스토캐스틱_과매수여부:
    매도 = True
elif 현재가 < 이동평균(20):
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

## 최적화 조건식

### 매수 최적화 조건식 - C_M_RSO_BO

```python
RSI_반등여부          = (RSI_N(1) <= self.vars[1] and RSI > self.vars[2])
스토캐스틱_반등여부  = (STOCHSK > STOCHSD and STOCHSK_N(1) <= STOCHSD_N(1))
이평위치여부          = (현재가 > 이동평균(20))
거래량증가여부        = (분당거래대금 > 분당거래대금평균(20) * self.vars[3])

매수 = True

if not (관심종목 == 1):
    매수 = False
elif not (93000 <= 시분초 <= 150000):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False
elif not RSI_반등여부:
    매수 = False
elif not 스토캐스틱_반등여부:
    매수 = False
elif not 이평위치여부:
    매수 = False
elif not 거래량증가여부:
    매수 = False
elif 시가총액 < 3000:
    if not (self.vars[4] < 등락율 <= self.vars[5]):
        매수 = False
    elif not (체결강도 >= self.vars[6]):
        매수 = False
else:
    if not (self.vars[7] < 등락율 <= self.vars[8]):
        매수 = False
    elif not (체결강도 >= self.vars[9]):
        매수 = False

if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매수 최적화 범위 - C_M_RSO_BOR

```python
self.vars[1]  = [[25, 35, 5], 30]                    # RSI 과매도 상한
self.vars[2]  = [[30, 40, 5], 35]                    # RSI 반등 하한
self.vars[3]  = [[1.2, 1.4, 0.1], 1.3]               # 거래량 증가 비율
self.vars[4]  = [[-4.0, -2.0, 1.0], -3.0]            # 등락율 하한 (시총<3000)
self.vars[5]  = [[10.0, 14.0, 2.0], 12.0]            # 등락율 상한
self.vars[6]  = [[100, 120, 10], 110]                # 체결강도 하한
self.vars[7]  = [[-3.0, -1.0, 1.0], -2.0]            # 등락율 하한 (시총>=3000)
self.vars[8]  = [[8.0, 12.0, 2.0], 10.0]             # 등락율 상한
self.vars[9]  = [[90, 110, 10], 100]                 # 체결강도 하한
```

### 매도 최적화 조건식 - C_M_RSO_SO

```python
RSI_과매수여부        = (RSI > self.vars[10])
스토캐스틱_과매수여부 = (STOCHSK > self.vars[11])

매도 = False

if 등락율 > 29.5:
    매도 = True
elif 수익률 >= self.vars[12] or 수익률 <= self.vars[13]:
    매도 = True
elif 최고수익률 > self.vars[14] and 최고수익률 * self.vars[15] >= 수익률:
    매도 = True
elif 보유시간 > self.vars[16]:
    매도 = True
elif RSI_과매수여부:
    매도 = True
elif 스토캐스틱_과매수여부:
    매도 = True
elif 현재가 < 이동평균(20):
    매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

### 매도 최적화 범위 - C_M_RSO_SOR

```python
self.vars[10] = [[65, 75, 5], 70]                    # RSI 과매수 임계
self.vars[11] = [[75, 85, 5], 80]                    # 스토캐스틱 과매수 임계
self.vars[12] = [[2.5, 3.5, 0.5], 3.0]               # 목표 수익 실현
self.vars[13] = [[-2.5, -1.5, 0.5], -2.0]            # 최대 손실 컷
self.vars[14] = [[3.5, 4.5, 0.5], 4.0]               # 최고수익률 기준값
self.vars[15] = [[0.60, 0.70, 0.05], 0.65]           # 트레일링 보정 비율
self.vars[16] = [[90, 150, 30], 120]                 # 최대 보유시간(분)
```

### 매수·매도 통합 최적화 범위 - C_M_RSO_OR_Min

핵심 변수만 선별하여 통합 최적화 수행

```python
# 매수 핵심 변수 (BOR에서 선별)
self.vars[1]  = [[25, 35, 5], 30]                    # RSI 과매도 상한
self.vars[2]  = [[30, 40, 5], 35]                    # RSI 반등 하한
self.vars[3]  = [[1.2, 1.4, 0.1], 1.3]               # 거래량 증가 비율

# 시가총액 < 3000 핵심
self.vars[6]  = [[100, 120, 10], 110]                # 체결강도 하한

# 매도 핵심 변수 (SOR에서 선별)
self.vars[10] = [[65, 75, 5], 70]                    # RSI 과매수 임계
self.vars[12] = [[2.5, 3.5, 0.5], 3.0]               # 목표 수익 실현
self.vars[13] = [[-2.5, -1.5, 0.5], -2.0]            # 최대 손실 컷
self.vars[15] = [[0.60, 0.70, 0.05], 0.65]           # 트레일링 보정 비율

# 총 경우의 수: 3 × 3 × 3 × 3 × 3 × 2 × 3 × 3 = 13,122
```

### GA 최적화 범위 - C_M_RSO_GAR

```python
self.vars[1]  = [[25, 30, 35], 30]
self.vars[2]  = [[30, 35, 40], 35]
self.vars[3]  = [[1.2, 1.3, 1.4], 1.3]
self.vars[10] = [[65, 70, 75], 70]
self.vars[11] = [[75, 80, 85], 80]
self.vars[12] = [[2.5, 3.0, 3.5], 3.0]
self.vars[13] = [[-2.5, -2.0, -1.5], -2.0]
```

---

## 조건식 개선 방향 연구

1) **RSI 다이버전스 확인**
   - 가격 저점과 RSI 저점 비교
   - 다이버전스 발생 시 신호 강화

2) **연속 과매도 확인**
   - 2~3분봉 연속 RSI 30 이하
   - 더 강한 반등 가능성

3) **MFI 추가**
   - Money Flow Index로 자금 흐름 확인
   - RSI와 MFI 동시 과매도 시 진입

4) **WILLR 추가**
   - Williams %R로 추가 확인
   - 다중 지표 확인으로 신뢰도 향상

5) **손절 강화**
   - RSI 30 재진입 시 즉시 청산
   - 추가 하락 방지

## 태그
- #주식트레이딩
- #분봉트레이딩
- #매수조건
- #매도조건
- #최적화
- #유전알고리즘
- #파이썬
- #트레이딩로직
- #RSI
- #스토캐스틱
- #평균회귀전략
- #과매도반등
- #리스크관리
