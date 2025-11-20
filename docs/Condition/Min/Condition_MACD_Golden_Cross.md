# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - MACD Golden Cross](#condition---macd-golden-cross)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 소개

이 문서는 09:30~15:00 구간에서 MACD 골든크로스를 활용한 추세 추종 분봉 전략입니다.
MACD 선이 시그널선을 상향 돌파하는 골든크로스 시점에 진입하여 상승 추세를 따라갑니다.

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **MACD Golden Cross (MACD 골든크로스 전략)**을 정의한다.

- **대상 시간 구간**: 09:30:00 ~ 15:00:00
- **대상 종목**: 시가총액 2,000억 차등 기준
- **전략 타입**: 분봉 기반 MACD 골든크로스 추세 추종 전략
- **핵심 변수**: MACD, MACD Signal, 분당거래대금, 체결강도
- **업데이트 이력**:
  - 초기 문서 작성: MACD 골든크로스 전략

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.
- 분봉 데이터 기반으로 900~1518 (09:00~15:18) 시간에만 거래합니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `MGC`: MACD Golden Cross를 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.
   - `M`: Min (분봉) 조건식을 의미합니다.

2. **예시**:
   - `C_MGC_M_B`: MACD Golden Cross 분봉 매수 조건식
   - `C_MGC_M_S`: MACD Golden Cross 분봉 매도 조건식

---

# Condition - MACD Golden Cross

## 조건식

### 매수 조건식

```python
# MACD 골든크로스 추세 전략 (09:30 ~ 15:00)

# 시간 조건
if not (93000 <= 시분초 <= 150000):
    매수 = False

# 데이터 충분성 확인 (MACD 계산을 위해)
elif not (데이터길이 > 40):
    매수 = False

# 가격 및 등락율 조건
elif not (2000 < 현재가 <= 50000):
    매수 = False
elif not (0.5 < 등락율 <= 18.0):
    매수 = False

# VI 및 라운드피겨 제외
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# MACD 골든크로스 조건 (핵심)
# 1) 현재 MACD > MACDS (골든크로스 발생)
elif not (MACD > MACDS):
    매수 = False

# 2) 이전 봉에서 MACD <= MACDS (크로스 시점 포착)
elif not (MACD_N(1) <= MACDS_N(1)):
    매수 = False

# 3) MACD 히스토그램 양전환
elif not (MACDH > 0):
    매수 = False
elif not (MACDH > MACDH_N(1)):
    매수 = False

# 4) MACD가 0선 근처 또는 상승 중
elif not (MACD > -50):
    매수 = False

# RSI 조건 (과매도 구간 탈출)
elif not (40 < RSI < 70):
    매수 = False
elif not (RSI > RSI_N(1)):
    매수 = False

# 이동평균 조건 (상승 추세)
elif not (이동평균(20) > 이동평균(20, 1)):
    매수 = False
elif not (현재가 > 이동평균(20)):
    매수 = False

# 거래량 조건
elif not (분당거래대금 > 분당거래대금평균(30)):
    매수 = False

# 체결강도 조건
elif not (체결강도 > 110):
    매수 = False

# 시가총액별 세분화 조건
elif 시가총액 < 2500:
    # 소형주
    if not (분당매수수량 > 분당매도수량 * 1.4):
        매수 = False
    elif not (등락율각도(15) > 5):
        매수 = False
    elif not (당일거래대금 > 40 * 100):
        매수 = False
    elif not (전일비 > 60):
        매수 = False
    elif not (회전율 > 2):
        매수 = False
    elif not (현재가 > 분봉시가):
        매수 = False
    elif not (분봉고가 > 분봉고가N(1)):
        매수 = False

else:
    # 중대형주
    if not (분당매수수량 > 분당매도수량 * 1.2):
        매수 = False
    elif not (등락율각도(15) > 3):
        매수 = False
    elif not (당일거래대금 > 100 * 100):
        매수 = False
    elif not (전일비 > 50):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
    elif not (현재가 > 분봉시가):
        매수 = False
    elif not (분봉고가 > 분봉고가N(1)):
        매수 = False

# 최종 매수 실행
if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식

```python
# MACD 데드크로스 및 익절 전략
if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 5.0:
    매도 = True
elif 수익률 <= -3.0:
    매도 = True
elif 최고수익률 - 수익률 >= 3.5:
    매도 = True
elif 보유시간 > 240:  # 240분 (4시간) 초과 보유 시 청산
    매도 = True

# MACD 데드크로스 조건 (핵심 매도 조건)
elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
    if 수익률 > 0.5:
        매도 = True

# MACD 히스토그램 음전환
elif MACDH < 0 and MACDH_N(1) >= 0:
    if 수익률 > 1.0:
        매도 = True

# MACD 하락 추세
elif MACD < MACD_N(1) and MACD_N(1) < MACD_N(2):
    if 수익률 > 1.5:
        매도 = True

# RSI 과매수 조건
elif RSI > 75:
    if 수익률 > 2.0:
        매도 = True

# 이동평균 이탈
elif 현재가 < 이동평균(20) and 현재가N(1) >= 이동평균(20, 1):
    if 수익률 > 1.0:
        매도 = True

# 체결강도 약화
elif 체결강도 < 95:
    매도 = True

# 시가총액별 세분화 매도 조건
elif 시가총액 < 2500:
    # 소형주: 빠른 청산
    if 2.0 <= 수익률 < 5.0 and 분당매도수량 > 분당매수수량 * 1.7:
        매도 = True
    elif 등락율각도(15) < 2:
        매도 = True
    elif 분당거래대금 < 분당거래대금평균(20) * 0.6:
        매도 = True

else:
    # 중대형주
    if 2.0 <= 수익률 < 5.0 and 분당매도수량 > 분당매수수량 * 1.5:
        매도 = True
    elif 등락율각도(15) < 1:
        매도 = True
    elif 분당거래대금 < 분당거래대금평균(20) * 0.7:
        매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

---

**Last Update: 2025-01-18**
