# 조건식 (Condition) - Volume Price Trend Strategy (분봉)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 목차
- [조건식 (Condition) - Volume Price Trend Strategy (분봉)](#조건식-condition---volume-price-trend-strategy-분봉)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - Volume Price Trend](#condition---volume-price-trend)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 소개

이 문서는 **거래량-가격 추세 전략(Volume Price Trend Strategy)**을 설명합니다. 거래량과 가격의 상관관계를 분석하여 진짜 추세와 거짓 추세를 구분하고, 거래량이 뒷받침하는 상승 추세에 진입하는 전략입니다.

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **Volume Price Trend Strategy (거래량-가격 추세 전략)**을 정의한다.

- **대상 시간 구간**: 09:00:00 ~ 15:18:00 (장 전체)
- **대상 종목**: 시가총액 2,000억 차등 기준
- **전략 타입**: 분봉 기반 거래량-가격 추세 전략
- **핵심 변수**: OBV, AD, ADOSC, 분당거래대금
- **업데이트 이력**:
  - 초기 문서 작성: 거래량-가격 추세 전략

### 전략 개요
- **거래 시간**: 900 ~ 1518 (9시 ~ 15시 18분)
- **목표**: 거래량 동반 상승 추세 포착
- **핵심 지표**: OBV, AD, ADOSC, 분당거래대금
- **리스크 관리**: 거래량 이탈 시 빠른 청산

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.
- 가격 상승과 거래량 증가가 동반되어야 합니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `VPT`: Volume Price Trend를 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.

2. **예시**:
   - `C_VPT_B`: 거래량-가격 추세 전략의 매수 조건식
   - `C_VPT_S`: 거래량-가격 추세 전략의 매도 조건식

---

# Condition - Volume Price Trend

## 조건식

### 매수 조건식

```python
# Volume Price Trend Strategy - 거래량 동반 상승 추세 포착 전략
# 거래 시간: 900 ~ 1518 (9시 ~ 15시 18분)

매수 = False

# 시간 제한: 정규 장 시간만 거래
if not (90000 <= 시분초 <= 151800):
    매수 = False

# 기본 필터링
elif not (1600 < 현재가 <= 54000):
    매수 = False
elif not (1.0 < 등락율 <= 28.5):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# 충분한 데이터 확보
elif not (데이터길이 > 75):
    매수 = False

# 시가총액별 조건
elif 시가총액 < 4500:
    # 소형주 (4500억 미만)
    # OBV (On Balance Volume) 상승
    if not (OBV > OBV_N(1)):
        매수 = False
    elif not (OBV > OBV_N(5)):
        매수 = False
    # AD (Accumulation/Distribution) 상승
    elif not (AD > AD_N(1)):
        매수 = False
    elif not (AD > AD_N(3)):
        매수 = False
    # ADOSC (A/D Oscillator) 양수
    elif not (ADOSC > 0):
        매수 = False
    elif not (ADOSC > ADOSC_N(1)):
        매수 = False
    # 가격 상승 중
    elif not (현재가 > 현재가N(1)):
        매수 = False
    elif not (현재가 > 현재가N(3)):
        매수 = False
    # 분당거래대금 급증
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.5):
        매수 = False
    elif not (분당거래대금 > 분당거래대금N(1)):
        매수 = False
    elif not (분당거래대금평균(20) > 분당거래대금평균(20, 1)):
        매수 = False
    # 누적분당매수수량 우위
    elif not (누적분당매수수량(30) > 누적분당매도수량(30) * 1.4):
        매수 = False
    # 체결강도
    elif not (체결강도 > 125):
        매수 = False
    elif not (체결강도평균(20) > 115):
        매수 = False
    elif not (최고체결강도(30) > 최고체결강도(30, 1)):
        매수 = False
    # MFI (Money Flow Index) 상승
    elif not (MFI > 40):
        매수 = False
    elif not (MFI > MFI_N(1)):
        매수 = False
    # 분봉 양봉 + 거래량
    elif not (현재가 > 분봉시가):
        매수 = False
    elif not (분봉고가 > 분봉고가N(1)):
        매수 = False
    # 전일비, 전일동시간비
    elif not (전일비 > 100):
        매수 = False
    elif not (전일동시간비 > 130):
        매수 = False
    # 회전율
    elif not (회전율 > 1.3):
        매수 = False
    # 당일거래대금
    elif not (당일거래대금 > 25 * 100):
        매수 = False
    # 등락율각도
    elif not (등락율각도(30) > 5):
        매수 = False
    # RSI 중립 ~ 상승
    elif not (40 < RSI < 75):
        매수 = False

else:
    # 중대형주 (4500억 이상)
    # OBV (On Balance Volume) 상승
    if not (OBV > OBV_N(1)):
        매수 = False
    elif not (OBV > OBV_N(5)):
        매수 = False
    # AD (Accumulation/Distribution) 상승
    elif not (AD > AD_N(1)):
        매수 = False
    elif not (AD > AD_N(3)):
        매수 = False
    # ADOSC (A/D Oscillator) 양수
    elif not (ADOSC > 0):
        매수 = False
    elif not (ADOSC > ADOSC_N(1)):
        매수 = False
    # 가격 상승 중
    elif not (현재가 > 현재가N(1)):
        매수 = False
    elif not (현재가 > 현재가N(3)):
        매수 = False
    # 분당거래대금 급증
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.3):
        매수 = False
    elif not (분당거래대금 > 분당거래대금N(1)):
        매수 = False
    elif not (분당거래대금평균(20) > 분당거래대금평균(20, 1)):
        매수 = False
    # 누적분당매수수량 우위
    elif not (누적분당매수수량(30) > 누적분당매도수량(30) * 1.3):
        매수 = False
    # 체결강도
    elif not (체결강도 > 118):
        매수 = False
    elif not (체결강도평균(20) > 110):
        매수 = False
    elif not (최고체결강도(30) > 최고체결강도(30, 1)):
        매수 = False
    # MFI (Money Flow Index) 상승
    elif not (MFI > 43):
        매수 = False
    elif not (MFI > MFI_N(1)):
        매수 = False
    # 분봉 양봉 + 거래량
    elif not (현재가 > 분봉시가):
        매수 = False
    elif not (분봉고가 > 분봉고가N(1)):
        매수 = False
    # 전일비, 전일동시간비
    elif not (전일비 > 75):
        매수 = False
    elif not (전일동시간비 > 100):
        매수 = False
    # 회전율
    elif not (회전율 > 0.85):
        매수 = False
    # 당일거래대금
    elif not (당일거래대금 > 120 * 100):
        매수 = False
    # 등락율각도
    elif not (등락율각도(30) > 6):
        매수 = False
    # RSI 중립 ~ 상승
    elif not (43 < RSI < 73):
        매수 = False
```

### 매도 조건식

```python
# Volume Price Trend Strategy - 거래량 이탈 감지 매도 전략

매도 = False

# 상한가 근접 시 매도
if 등락율 > 29.5:
    매도 = True

# 수익률 기준 매도
elif 수익률 >= 6.8:
    매도 = True
elif 수익률 <= -3.0:
    매도 = True

# 최고수익률 대비 하락 시 매도
elif 최고수익률 >= 8.5 and 수익률 < 최고수익률 - 3.2:
    매도 = True

# 시가총액별 매도 조건
elif 시가총액 < 4500:
    # 소형주 매도 조건
    # OBV 하락 (거래량 이탈)
    if OBV < OBV_N(1) and OBV_N(1) < OBV_N(2):
        매도 = True
    # AD 하락
    elif AD < AD_N(1) and AD_N(1) < AD_N(2):
        매도 = True
    # ADOSC 음수 전환
    elif ADOSC < 0 and ADOSC_N(1) >= 0:
        매도 = True
    elif ADOSC < ADOSC_N(1) and ADOSC_N(1) < ADOSC_N(2):
        매도 = True
    # 가격 하락 + 거래량 감소 (위험 신호)
    elif 현재가 < 현재가N(1) and 분당거래대금 < 분당거래대금N(1):
        매도 = True
    # 분당거래대금 급감
    elif 분당거래대금 < 분당거래대금평균(30) * 0.7:
        매도 = True
    elif 분당거래대금평균(20) < 분당거래대금평균(20, 1):
        매도 = True
    # 누적분당매도수량 우위
    elif 누적분당매도수량(20) > 누적분당매수수량(20) * 1.3:
        매도 = True
    # 체결강도 급락
    elif 체결강도 < 90:
        매도 = True
    elif 체결강도평균(20) < 100 and 체결강도평균(20) < 체결강도평균(20, 1):
        매도 = True
    # MFI 하락
    elif MFI < MFI_N(1) and MFI_N(1) < MFI_N(2):
        매도 = True
    elif MFI < 35:
        매도 = True
    # 분봉 음봉 연속
    elif 현재가 < 분봉시가 and 현재가N(1) < 분봉시가N(1):
        매도 = True
    # 이동평균선 이탈
    elif 현재가 < 이동평균(20):
        매도 = True
    # MACD 데드크로스
    elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    # RSI 과매수
    elif RSI > 76:
        매도 = True
    # 등락율각도 하락
    elif 등락율각도(30) < 2:
        매도 = True
    # 시간 기준
    elif 보유시간 > 115:  # 115분 이상 보유 시 매도
        매도 = True

else:
    # 중대형주 매도 조건
    # OBV 하락 (거래량 이탈)
    if OBV < OBV_N(1) and OBV_N(1) < OBV_N(2):
        매도 = True
    # AD 하락
    elif AD < AD_N(1) and AD_N(1) < AD_N(2):
        매도 = True
    # ADOSC 음수 전환
    elif ADOSC < 0 and ADOSC_N(1) >= 0:
        매도 = True
    elif ADOSC < ADOSC_N(1) and ADOSC_N(1) < ADOSC_N(2):
        매도 = True
    # 가격 하락 + 거래량 감소 (위험 신호)
    elif 현재가 < 현재가N(1) and 분당거래대금 < 분당거래대금N(1):
        매도 = True
    # 분당거래대금 급감
    elif 분당거래대금 < 분당거래대금평균(30) * 0.75:
        매도 = True
    elif 분당거래대금평균(20) < 분당거래대금평균(20, 1):
        매도 = True
    # 누적분당매도수량 우위
    elif 누적분당매도수량(20) > 누적분당매수수량(20) * 1.25:
        매도 = True
    # 체결강도 급락
    elif 체결강도 < 94:
        매도 = True
    elif 체결강도평균(20) < 103 and 체결강도평균(20) < 체결강도평균(20, 1):
        매도 = True
    # MFI 하락
    elif MFI < MFI_N(1) and MFI_N(1) < MFI_N(2):
        매도 = True
    elif MFI < 38:
        매도 = True
    # 분봉 음봉 연속
    elif 현재가 < 분봉시가 and 현재가N(1) < 분봉시가N(1):
        매도 = True
    # 이동평균선 이탈
    elif 현재가 < 이동평균(20):
        매도 = True
    # MACD 데드크로스
    elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    # RSI 과매수
    elif RSI > 74:
        매도 = True
    # 등락율각도 하락
    elif 등락율각도(30) < 3:
        매도 = True
    # 시간 기준
    elif 보유시간 > 170:  # 170분 이상 보유 시 매도
        매도 = True
```

---

**Last Update: 2025-01-18**
