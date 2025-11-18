# 조건식 (Condition) - RSI Divergence Strategy (분봉)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Min.md에 있는 조건식을 사용하여 만든 조건식

## 목차
- [조건식 (Condition) - RSI Divergence Strategy (분봉)](#조건식-condition---rsi-divergence-strategy-분봉)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - RSI Divergence](#condition---rsi-divergence)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 소개

이 문서는 **RSI 다이버전스 전략(RSI Divergence Strategy)**을 설명합니다. 가격과 RSI의 괴리(다이버전스)를 감지하여 반전 지점을 포착하는 전략입니다.

### 전략 개요
- **거래 시간**: 900 ~ 1518 (9시 ~ 15시 18분)
- **목표**: RSI 강세 다이버전스 포착
- **핵심 지표**: RSI, 가격 추세, 스토캐스틱
- **리스크 관리**: 과매도 구간에서 반전 신호 확인

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.
- 다이버전스는 가격 저점과 RSI 저점의 불일치를 의미합니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `RSID`: RSI Divergence를 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.

2. **예시**:
   - `C_RSID_B`: RSI 다이버전스 전략의 매수 조건식
   - `C_RSID_S`: RSI 다이버전스 전략의 매도 조건식

---

# Condition - RSI Divergence

## 조건식

### 매수 조건식

```python
# RSI Divergence Strategy - RSI 강세 다이버전스 포착 전략
# 거래 시간: 900 ~ 1518 (9시 ~ 15시 18분)

매수 = False

# 시간 제한: 정규 장 시간만 거래
if not (90000 <= 시분초 <= 151800):
    매수 = False

# 기본 필터링
elif not (1500 < 현재가 <= 48000):
    매수 = False
elif not (0.5 < 등락율 <= 28.0):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# 충분한 데이터 확보
elif not (데이터길이 > 80):
    매수 = False

# 시가총액별 조건
elif 시가총액 < 3800:
    # 소형주 (3800억 미만)
    # RSI 과매도 구간에서 반등
    if not (RSI_N(1) < 35 and RSI > 35):
        매수 = False
    elif not (RSI > RSI_N(1) and RSI_N(1) > RSI_N(2)):
        매수 = False
    # 강세 다이버전스: 가격 저점 하향, RSI 저점 상향
    # 현재가가 과거보다 낮지만 RSI는 과거보다 높음
    elif not (현재가 < 최저현재가(30, 10) and RSI > 25):
        매수 = False
    # 스토캐스틱 과매도 탈출
    elif not (STOCHSK > 20 and STOCHSK_N(1) <= 20):
        매수 = False
    elif not (STOCHSK > STOCHSD):
        매수 = False
    # MFI (Money Flow Index) 확인
    elif not (MFI > MFI_N(1)):
        매수 = False
    elif not (MFI > 25):
        매수 = False
    # CCI 과매도 탈출
    elif not (CCI > CCI_N(1)):
        매수 = False
    # 체결강도 회복
    elif not (체결강도 > 110):
        매수 = False
    elif not (체결강도평균(20) > 체결강도평균(20, 1)):
        매수 = False
    # 분당거래대금 증가
    elif not (분당거래대금 > 분당거래대금평균(30)):
        매수 = False
    # 가격 반등 신호
    elif not (현재가 > 현재가N(1)):
        매수 = False
    elif not (현재가 > 분봉시가):
        매수 = False
    # 거래 활성도
    elif not (당일거래대금 > 15 * 100):
        매수 = False
    elif not (전일비 > 70):
        매수 = False
    # 볼린저밴드 하단 반등
    elif not (현재가 > BBL):
        매수 = False
    elif not (현재가_N(1) <= BBL_N(1)):
        매수 = False

else:
    # 중대형주 (3800억 이상)
    # RSI 과매도 구간에서 반등
    if not (RSI_N(1) < 38 and RSI > 38):
        매수 = False
    elif not (RSI > RSI_N(1) and RSI_N(1) > RSI_N(2)):
        매수 = False
    # 강세 다이버전스: 가격 저점 하향, RSI 저점 상향
    elif not (현재가 < 최저현재가(30, 10) and RSI > 28):
        매수 = False
    # 스토캐스틱 과매도 탈출
    elif not (STOCHSK > 23 and STOCHSK_N(1) <= 23):
        매수 = False
    elif not (STOCHSK > STOCHSD):
        매수 = False
    # MFI (Money Flow Index) 확인
    elif not (MFI > MFI_N(1)):
        매수 = False
    elif not (MFI > 28):
        매수 = False
    # CCI 과매도 탈출
    elif not (CCI > CCI_N(1)):
        매수 = False
    # 체결강도 회복
    elif not (체결강도 > 107):
        매수 = False
    elif not (체결강도평균(20) > 체결강도평균(20, 1)):
        매수 = False
    # 분당거래대금 증가
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.05):
        매수 = False
    # 가격 반등 신호
    elif not (현재가 > 현재가N(1)):
        매수 = False
    elif not (현재가 > 분봉시가):
        매수 = False
    # 거래 활성도
    elif not (당일거래대금 > 80 * 100):
        매수 = False
    elif not (전일비 > 55):
        매수 = False
    # 볼린저밴드 하단 반등
    elif not (현재가 > BBL):
        매수 = False
    elif not (현재가_N(1) <= BBL_N(1)):
        매수 = False
```

### 매도 조건식

```python
# RSI Divergence Strategy - RSI 과매수 및 약세 다이버전스 감지 매도 전략

매도 = False

# 상한가 근접 시 매도
if 등락율 > 29.5:
    매도 = True

# 수익률 기준 매도
elif 수익률 >= 5.5:
    매도 = True
elif 수익률 <= -2.5:
    매도 = True

# 최고수익률 대비 하락 시 매도
elif 최고수익률 >= 6.5 and 수익률 < 최고수익률 - 2.5:
    매도 = True

# 시가총액별 매도 조건
elif 시가총액 < 3800:
    # 소형주 매도 조건
    # RSI 과매수 구간
    if RSI > 75:
        매도 = True
    elif RSI_N(1) > 70 and RSI < 70:
        매도 = True
    # RSI 하락 추세
    elif RSI < RSI_N(1) and RSI_N(1) < RSI_N(2):
        매도 = True
    # 약세 다이버전스: 가격 고점 상향, RSI 고점 하향
    elif 현재가 > 최고현재가(30, 10) and RSI < 75:
        if RSI < RSI_N(10):
            매도 = True
    # 스토캐스틱 과매수
    elif STOCHSK > 85:
        매도 = True
    elif STOCHSK < STOCHSD and STOCHSK_N(1) >= STOCHSD_N(1):
        매도 = True
    # MFI 과매수
    elif MFI > 78:
        매도 = True
    elif MFI < MFI_N(1) and MFI_N(1) < MFI_N(2):
        매도 = True
    # CCI 과매수
    elif CCI > 150 and CCI < CCI_N(1):
        매도 = True
    # 체결강도 약화
    elif 체결강도 < 88:
        매도 = True
    # 볼린저밴드 상단 이탈
    elif 현재가 > BBU_N(1) and 현재가 < BBU:
        매도 = True
    # 이동평균선 이탈
    elif 현재가 < 이동평균(20):
        매도 = True
    # 시간 기준
    elif 보유시간 > 100:  # 100분 이상 보유 시 매도
        매도 = True

else:
    # 중대형주 매도 조건
    # RSI 과매수 구간
    if RSI > 72:
        매도 = True
    elif RSI_N(1) > 68 and RSI < 68:
        매도 = True
    # RSI 하락 추세
    elif RSI < RSI_N(1) and RSI_N(1) < RSI_N(2):
        매도 = True
    # 약세 다이버전스: 가격 고점 상향, RSI 고점 하향
    elif 현재가 > 최고현재가(30, 10) and RSI < 72:
        if RSI < RSI_N(10):
            매도 = True
    # 스토캐스틱 과매수
    elif STOCHSK > 82:
        매도 = True
    elif STOCHSK < STOCHSD and STOCHSK_N(1) >= STOCHSD_N(1):
        매도 = True
    # MFI 과매수
    elif MFI > 75:
        매도 = True
    elif MFI < MFI_N(1) and MFI_N(1) < MFI_N(2):
        매도 = True
    # CCI 과매수
    elif CCI > 140 and CCI < CCI_N(1):
        매도 = True
    # 체결강도 약화
    elif 체결강도 < 92:
        매도 = True
    # 볼린저밴드 상단 이탈
    elif 현재가 > BBU_N(1) and 현재가 < BBU:
        매도 = True
    # 이동평균선 이탈
    elif 현재가 < 이동평균(20):
        매도 = True
    # 시간 기준
    elif 보유시간 > 150:  # 150분 이상 보유 시 매도
        매도 = True
```

---

**Last Update: 2025-01-18**
