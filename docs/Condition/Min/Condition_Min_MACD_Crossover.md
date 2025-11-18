# 조건식 (Condition) - MACD Crossover Strategy (분봉)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Min.md에 있는 조건식을 사용하여 만든 조건식

## 목차
- [조건식 (Condition) - MACD Crossover Strategy (분봉)](#조건식-condition---macd-crossover-strategy-분봉)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - MACD Crossover](#condition---macd-crossover)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 소개

이 문서는 **MACD 크로스오버 전략(MACD Crossover Strategy)**을 설명합니다. 분봉 데이터에서 MACD와 시그널 라인의 골든크로스를 포착하여 매수하고, 데드크로스 발생 시 매도하는 전략입니다.

### 전략 개요
- **거래 시간**: 900 ~ 1518 (9시 ~ 15시 18분)
- **목표**: MACD 골든크로스 포착
- **핵심 지표**: MACD, MACDS, MACDH, RSI
- **리스크 관리**: 기술적 지표 확인 후 진입

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.
- 분봉 데이터 기반으로 1분 단위 캔들스틱 데이터를 분석합니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `MACD`: MACD Crossover를 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.

2. **예시**:
   - `C_MACD_B`: MACD 크로스오버 전략의 매수 조건식
   - `C_MACD_S`: MACD 크로스오버 전략의 매도 조건식

---

# Condition - MACD Crossover

## 조건식

### 매수 조건식

```python
# MACD Crossover Strategy - MACD 골든크로스 포착 전략
# 거래 시간: 900 ~ 1518 (9시 ~ 15시 18분)

매수 = False

# 시간 제한: 정규 장 시간만 거래
if not (90000 <= 시분초 <= 151800):
    매수 = False

# 기본 필터링
elif not (2000 < 현재가 <= 50000):
    매수 = False
elif not (1.0 < 등락율 <= 28.0):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# 충분한 데이터 확보
elif not (데이터길이 > 60):
    매수 = False

# 시가총액별 조건
elif 시가총액 < 4000:
    # 소형주 (4000억 미만)
    # MACD 골든크로스 확인
    if not (MACD > MACDS and MACD_N(1) <= MACDS_N(1)):
        매수 = False
    # MACD 히스토그램 양수 전환
    elif not (MACDH > 0 and MACDH_N(1) <= 0):
        매수 = False
    # MACD 상승 추세
    elif not (MACD > MACD_N(1)):
        매수 = False
    # RSI 과매도 구간 탈출
    elif not (30 < RSI < 70):
        매수 = False
    elif not (RSI > RSI_N(1)):
        매수 = False
    # 이동평균선 정배열
    elif not (이동평균(20) > 이동평균(60)):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
    # 분당거래대금 증가
    elif not (분당거래대금 > 분당거래대금평균(30)):
        매수 = False
    elif not (분당거래대금 > 분당거래대금N(1)):
        매수 = False
    # 체결강도
    elif not (체결강도 > 115):
        매수 = False
    elif not (체결강도평균(20) > 105):
        매수 = False
    # 분봉 양봉 확인
    elif not (현재가 > 분봉시가):
        매수 = False
    elif not (분봉고가 > 분봉고가N(1)):
        매수 = False
    # 거래 활성도
    elif not (당일거래대금 > 20 * 100):
        매수 = False
    elif not (전일비 > 80):
        매수 = False
    elif not (회전율 > 1.0):
        매수 = False
    # 등락율 각도
    elif not (등락율각도(30) > 3):
        매수 = False

else:
    # 중대형주 (4000억 이상)
    # MACD 골든크로스 확인
    if not (MACD > MACDS and MACD_N(1) <= MACDS_N(1)):
        매수 = False
    # MACD 히스토그램 양수 전환
    elif not (MACDH > 0 and MACDH_N(1) <= 0):
        매수 = False
    # MACD 상승 추세
    elif not (MACD > MACD_N(1)):
        매수 = False
    # RSI 과매도 구간 탈출
    elif not (35 < RSI < 68):
        매수 = False
    elif not (RSI > RSI_N(1)):
        매수 = False
    # 이동평균선 정배열
    elif not (이동평균(20) > 이동평균(60)):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
    # 분당거래대금 증가
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.1):
        매수 = False
    elif not (분당거래대금 > 분당거래대금N(1)):
        매수 = False
    # 체결강도
    elif not (체결강도 > 110):
        매수 = False
    elif not (체결강도평균(20) > 103):
        매수 = False
    # 분봉 양봉 확인
    elif not (현재가 > 분봉시가):
        매수 = False
    elif not (분봉고가 > 분봉고가N(1)):
        매수 = False
    # 거래 활성도
    elif not (당일거래대금 > 100 * 100):
        매수 = False
    elif not (전일비 > 60):
        매수 = False
    elif not (회전율 > 0.7):
        매수 = False
    # 등락율 각도
    elif not (등락율각도(30) > 4):
        매수 = False
```

### 매도 조건식

```python
# MACD Crossover Strategy - MACD 데드크로스 감지 매도 전략

매도 = False

# 상한가 근접 시 매도
if 등락율 > 29.5:
    매도 = True

# 수익률 기준 매도
elif 수익률 >= 6.0:
    매도 = True
elif 수익률 <= -3.0:
    매도 = True

# 최고수익률 대비 하락 시 매도
elif 최고수익률 >= 7.0 and 수익률 < 최고수익률 - 3.0:
    매도 = True

# 시가총액별 매도 조건
elif 시가총액 < 4000:
    # 소형주 매도 조건
    # MACD 데드크로스
    if MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    # MACD 히스토그램 음수 전환
    elif MACDH < 0 and MACDH_N(1) >= 0:
        매도 = True
    # MACD 하락 추세
    elif MACD < MACD_N(1) and MACD_N(1) < MACD_N(2):
        매도 = True
    # RSI 과매수 구간
    elif RSI > 75:
        매도 = True
    elif RSI < RSI_N(1) and RSI_N(1) < RSI_N(2):
        매도 = True
    # 이동평균선 이탈
    elif 현재가 < 이동평균(20) and 현재가N(1) >= 이동평균(20, 1):
        매도 = True
    elif 이동평균(20) < 이동평균(60):
        매도 = True
    # 체결강도 약화
    elif 체결강도 < 90 and 체결강도평균(20) < 95:
        매도 = True
    # 분봉 음봉 연속
    elif 현재가 < 분봉시가 and 현재가N(1) < 분봉시가N(1):
        매도 = True
    # 등락율 각도 하락
    elif 등락율각도(30) < 0:
        매도 = True
    # 시간 기준
    elif 보유시간 > 120:  # 2시간 이상 보유 시 매도
        매도 = True

else:
    # 중대형주 매도 조건
    # MACD 데드크로스
    if MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    # MACD 히스토그램 음수 전환
    elif MACDH < 0 and MACDH_N(1) >= 0:
        매도 = True
    # MACD 하락 추세
    elif MACD < MACD_N(1) and MACD_N(1) < MACD_N(2):
        매도 = True
    # RSI 과매수 구간
    elif RSI > 72:
        매도 = True
    elif RSI < RSI_N(1) and RSI_N(1) < RSI_N(2):
        매도 = True
    # 이동평균선 이탈
    elif 현재가 < 이동평균(20) and 현재가N(1) >= 이동평균(20, 1):
        매도 = True
    elif 이동평균(20) < 이동평균(60):
        매도 = True
    # 체결강도 약화
    elif 체결강도 < 95 and 체결강도평균(20) < 98:
        매도 = True
    # 분봉 음봉 연속
    elif 현재가 < 분봉시가 and 현재가N(1) < 분봉시가N(1):
        매도 = True
    # 등락율 각도 하락
    elif 등락율각도(30) < 2:
        매도 = True
    # 시간 기준
    elif 보유시간 > 180:  # 3시간 이상 보유 시 매도
        매도 = True
```

---

**Last Update: 2025-01-18**
