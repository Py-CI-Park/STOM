# 조건식 (Condition) - Bollinger Band Squeeze Strategy (분봉)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Min.md에 있는 조건식을 사용하여 만든 조건식

## 목차
- [조건식 (Condition) - Bollinger Band Squeeze Strategy (분봉)](#조건식-condition---bollinger-band-squeeze-strategy-분봉)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - Bollinger Squeeze](#condition---bollinger-squeeze)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 소개

이 문서는 **볼린저밴드 압축 전략(Bollinger Band Squeeze Strategy)**을 설명합니다. 볼린저밴드가 압축된 후 확장되는 시점을 포착하여 변동성 증가에 따른 추세 발생을 노리는 전략입니다.

### 전략 개요
- **거래 시간**: 900 ~ 1518 (9시 ~ 15시 18분)
- **목표**: 볼린저밴드 압축 후 확장 포착
- **핵심 지표**: BBU, BBM, BBL, ATR, 변동성
- **리스크 관리**: 변동성 확대 시점 진입

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.
- 볼린저밴드 폭이 좁아진 후 넓어지는 시점이 중요합니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `BBS`: Bollinger Band Squeeze를 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.

2. **예시**:
   - `C_BBS_B`: 볼린저밴드 압축 전략의 매수 조건식
   - `C_BBS_S`: 볼린저밴드 압축 전략의 매도 조건식

---

# Condition - Bollinger Squeeze

## 조건식

### 매수 조건식

```python
# Bollinger Band Squeeze Strategy - 볼린저밴드 압축 후 확장 포착 전략
# 거래 시간: 900 ~ 1518 (9시 ~ 15시 18분)

매수 = False

# 볼린저밴드 폭 계산
밴드폭 = (BBU - BBL) / BBM * 100
밴드폭N1 = (BBU_N(1) - BBL_N(1)) / BBM_N(1) * 100
밴드폭N2 = (BBU_N(2) - BBL_N(2)) / BBM_N(2) * 100

# 시간 제한: 정규 장 시간만 거래
if not (90000 <= 시분초 <= 151800):
    매수 = False

# 기본 필터링
elif not (2200 < 현재가 <= 46000):
    매수 = False
elif not (0.8 < 등락율 <= 28.0):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# 충분한 데이터 확보
elif not (데이터길이 > 70):
    매수 = False

# 시가총액별 조건
elif 시가총액 < 3600:
    # 소형주 (3600억 미만)
    # 볼린저밴드 압축 후 확장
    if not (밴드폭 > 밴드폭N1 and 밴드폭N1 > 밴드폭N2):
        매수 = False
    # 밴드 하단 근처에서 상승
    elif not (현재가_N(1) <= BBL_N(1) * 1.01):
        매수 = False
    elif not (현재가 > BBL):
        매수 = False
    elif not (현재가 > BBL * 1.002):
        매수 = False
    # 볼린저밴드 중심선 돌파
    elif not (현재가 > BBM):
        매수 = False
    # ATR (변동성) 증가
    elif not (ATR > ATR_N(1)):
        매수 = False
    # 가격 상승 중
    elif not (현재가 > 현재가N(1)):
        매수 = False
    elif not (현재가 > 분봉시가):
        매수 = False
    # 체결강도
    elif not (체결강도 > 118):
        매수 = False
    elif not (체결강도평균(20) > 108):
        매수 = False
    # 분당거래대금 증가
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.3):
        매수 = False
    # MOM (모멘텀) 양수
    elif not (MOM > 0):
        매수 = False
    elif not (MOM > MOM_N(1)):
        매수 = False
    # ROC (변화율) 양수
    elif not (ROC > 0):
        매수 = False
    # 이동평균선 상향
    elif not (이동평균(20) > 이동평균(20, 1)):
        매수 = False
    # 거래 활성도
    elif not (당일거래대금 > 18 * 100):
        매수 = False
    elif not (전일비 > 75):
        매수 = False
    elif not (회전율 > 0.9):
        매수 = False

else:
    # 중대형주 (3600억 이상)
    # 볼린저밴드 압축 후 확장
    if not (밴드폭 > 밴드폭N1 and 밴드폭N1 > 밴드폭N2):
        매수 = False
    # 밴드 하단 근처에서 상승
    elif not (현재가_N(1) <= BBL_N(1) * 1.015):
        매수 = False
    elif not (현재가 > BBL):
        매수 = False
    elif not (현재가 > BBL * 1.003):
        매수 = False
    # 볼린저밴드 중심선 돌파
    elif not (현재가 > BBM):
        매수 = False
    # ATR (변동성) 증가
    elif not (ATR > ATR_N(1)):
        매수 = False
    # 가격 상승 중
    elif not (현재가 > 현재가N(1)):
        매수 = False
    elif not (현재가 > 분봉시가):
        매수 = False
    # 체결강도
    elif not (체결강도 > 113):
        매수 = False
    elif not (체결강도평균(20) > 105):
        매수 = False
    # 분당거래대금 증가
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.2):
        매수 = False
    # MOM (모멘텀) 양수
    elif not (MOM > 0):
        매수 = False
    elif not (MOM > MOM_N(1)):
        매수 = False
    # ROC (변화율) 양수
    elif not (ROC > 0):
        매수 = False
    # 이동평균선 상향
    elif not (이동평균(20) > 이동평균(20, 1)):
        매수 = False
    # 거래 활성도
    elif not (당일거래대금 > 90 * 100):
        매수 = False
    elif not (전일비 > 58):
        매수 = False
    elif not (회전율 > 0.65):
        매수 = False
```

### 매도 조건식

```python
# Bollinger Band Squeeze Strategy - 볼린저밴드 상단 도달 매도 전략

매도 = False

# 상한가 근접 시 매도
if 등락율 > 29.5:
    매도 = True

# 수익률 기준 매도
elif 수익률 >= 6.5:
    매도 = True
elif 수익률 <= -2.8:
    매도 = True

# 최고수익률 대비 하락 시 매도
elif 최고수익률 >= 7.5 and 수익률 < 최고수익률 - 2.8:
    매도 = True

# 시가총액별 매도 조건
elif 시가총액 < 3600:
    # 소형주 매도 조건
    # 볼린저밴드 상단 도달 후 이탈
    if 현재가_N(1) >= BBU_N(1) * 0.998 and 현재가 < BBU * 0.995:
        매도 = True
    # 볼린저밴드 상단 돌파 후 하락
    elif 현재가 > BBU and 현재가 < 현재가N(1):
        매도 = True
    # 볼린저밴드 중심선 이탈
    elif 현재가 < BBM and 현재가N(1) >= BBM_N(1):
        매도 = True
    # ATR 급증 후 감소 (변동성 축소)
    elif ATR < ATR_N(1) and ATR_N(1) < ATR_N(2):
        if 현재가 < 현재가N(1):
            매도 = True
    # MOM (모멘텀) 음수 전환
    elif MOM < 0 and MOM_N(1) >= 0:
        매도 = True
    # ROC 음수 전환
    elif ROC < 0 and ROC_N(1) >= 0:
        매도 = True
    # 체결강도 약화
    elif 체결강도 < 95:
        매도 = True
    # 이동평균선 이탈
    elif 현재가 < 이동평균(20):
        매도 = True
    # MACD 데드크로스
    elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    # 시간 기준
    elif 보유시간 > 110:  # 110분 이상 보유 시 매도
        매도 = True

else:
    # 중대형주 매도 조건
    # 볼린저밴드 상단 도달 후 이탈
    if 현재가_N(1) >= BBU_N(1) * 0.999 and 현재가 < BBU * 0.997:
        매도 = True
    # 볼린저밴드 상단 돌파 후 하락
    elif 현재가 > BBU and 현재가 < 현재가N(1):
        매도 = True
    # 볼린저밴드 중심선 이탈
    elif 현재가 < BBM and 현재가N(1) >= BBM_N(1):
        매도 = True
    # ATR 급증 후 감소 (변동성 축소)
    elif ATR < ATR_N(1) and ATR_N(1) < ATR_N(2):
        if 현재가 < 현재가N(1):
            매도 = True
    # MOM (모멘텀) 음수 전환
    elif MOM < 0 and MOM_N(1) >= 0:
        매도 = True
    # ROC 음수 전환
    elif ROC < 0 and ROC_N(1) >= 0:
        매도 = True
    # 체결강도 약화
    elif 체결강도 < 98:
        매도 = True
    # 이동평균선 이탈
    elif 현재가 < 이동평균(20):
        매도 = True
    # MACD 데드크로스
    elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    # 시간 기준
    elif 보유시간 > 165:  # 165분 이상 보유 시 매도
        매도 = True
```

---

**Last Update: 2025-01-18**
