# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성한 Min 조건식
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - RSI Oversold Rebound](#condition---rsi-oversold-rebound)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **장중 전체(09:00~15:18) RSI 과매도 반등 전략**을 정의한다.

- **대상 시간 구간**: 09:00:00 ~ 15:18:00 (장중 전체)
- **대상 종목**: 가격대 2,000원~50,000원, 등락율 -8~12%
- **전략 타입**: RSI 과매도 탈출 반등 포착 (RSI Oversold Rebound)
- **핵심 변수**: RSI, MACD, 이동평균(20), 체결강도, 분당거래대금
- **업데이트 이력**:
  - 초기 문서 작성

## 소개

이 문서는 전체 거래시간 09:00~15:18 구간에서 RSI 과매도 구간 탈출을 노리는 분봉 전략입니다.
RSI가 30 이하로 과매도된 종목이 반등할 때 진입하여 단기 반등 수익을 추구합니다.

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.
- 분봉 데이터 기반으로 900~1518 (09:00~15:18) 시간에만 거래합니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `ROR`: RSI Oversold Rebound를 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.
   - `M`: Min (분봉) 조건식을 의미합니다.

2. **예시**:
   - `C_ROR_M_B`: RSI Oversold Rebound 분봉 매수 조건식
   - `C_ROR_M_S`: RSI Oversold Rebound 분봉 매도 조건식

---

# Condition - RSI Oversold Rebound

## 조건식

### 매수 조건식

```python
# RSI 과매도 반등 전략 (09:00 ~ 15:18)

# 시간 조건
if not (90000 <= 시분초 <= 151800):
    매수 = False

# 데이터 충분성 확인 (RSI 계산을 위해)
elif not (데이터길이 > 20):
    매수 = False

# 가격 및 등락율 조건
elif not (2000 < 현재가 <= 50000):
    매수 = False
elif not (-8.0 < 등락율 <= 12.0):
    매수 = False

# VI 제외
elif not (현재가 < VI아래5호가):
    매수 = False

# RSI 과매도 탈출 조건 (핵심)
# 1) 이전 봉에서 RSI 과매도 구간
elif not (RSI_N(1) < 30):
    매수 = False

# 2) 현재 RSI 상승 중 (반등 시작)
elif not (RSI > RSI_N(1)):
    매수 = False
elif not (30 < RSI < 50):
    매수 = False

# 3) RSI 2분봉 연속 상승
elif not (RSI_N(1) > RSI_N(2)):
    매수 = False

# 분봉 패턴 조건
elif not (현재가 > 분봉시가):
    매수 = False
elif not (분봉고가 > 분봉저가 * 1.01):
    매수 = False

# 체결강도 조건
elif not (체결강도 > 105):
    매수 = False
elif not (체결강도 > 체결강도N(1)):
    매수 = False

# 거래량 조건
elif not (분당거래대금 > 분당거래대금평균(20)):
    매수 = False

# 저가 근처 확인 (반등 가능성)
elif not (현재가 > 저가 and 현재가 < 저가 * 1.05):
    매수 = False

# 시가총액별 세분화 조건
elif 시가총액 < 2000:
    # 소형주
    if not (분당매수수량 > 분당매도수량 * 1.5):
        매수 = False
    elif not (체결강도평균(10) > 95):
        매수 = False
    elif not (당일거래대금 > 30 * 100):
        매수 = False
    elif not (회전율 > 2):
        매수 = False
    elif not (전일비 > 40):
        매수 = False
    elif not (고저평균대비등락율 < 5):
        매수 = False
    elif not (매수총잔량 > 매도총잔량):
        매수 = False

elif 시가총액 < 5000:
    # 중형주
    if not (분당매수수량 > 분당매도수량 * 1.3):
        매수 = False
    elif not (체결강도평균(10) > 100):
        매수 = False
    elif not (당일거래대금 > 80 * 100):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
    elif not (전일비 > 35):
        매수 = False
    elif not (고저평균대비등락율 < 4):
        매수 = False
    elif not (매수총잔량 > 매도총잔량 * 0.9):
        매수 = False

else:
    # 대형주
    if not (분당매수수량 > 분당매도수량 * 1.2):
        매수 = False
    elif not (체결강도평균(10) > 105):
        매수 = False
    elif not (당일거래대금 > 150 * 100):
        매수 = False
    elif not (회전율 > 1.2):
        매수 = False
    elif not (전일비 > 30):
        매수 = False
    elif not (고저평균대비등락율 < 3):
        매수 = False
    elif not (매수총잔량 > 매도총잔량 * 0.8):
        매수 = False

# 최종 매수 실행
if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식

```python
# RSI 정상 회복 및 익절 전략
if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 3.0:
    매도 = True
elif 수익률 <= -2.5:
    매도 = True
elif 최고수익률 - 수익률 >= 2.0:
    매도 = True
elif 보유시간 > 150:  # 150분 (2.5시간) 초과 보유 시 청산
    매도 = True

# RSI 중립 회복 (핵심 익절 조건)
elif RSI > 60:
    if 수익률 > 1.0:
        매도 = True

# RSI 하락 전환
elif RSI < RSI_N(1) and RSI_N(1) < RSI_N(2):
    if 수익률 > 0.5:
        매도 = True

# RSI 재과매도 진입 (추가 하락 가능성)
elif RSI < 35:
    매도 = True

# 체결강도 약화
elif 체결강도 < 95:
    매도 = True

# 분봉 음봉 전환
elif 현재가 < 분봉시가:
    if 수익률 > 0.8:
        매도 = True

# 거래량 급감
elif 분당거래대금 < 분당거래대금평균(15) * 0.6:
    if 수익률 > 0:
        매도 = True

# 시가총액별 세분화 매도 조건
elif 시가총액 < 2000:
    # 소형주: 빠른 청산
    if 1.2 <= 수익률 < 3.0 and 분당매도수량 > 분당매수수량 * 1.7:
        매도 = True
    elif 고저평균대비등락율 > 3:
        매도 = True

elif 시가총액 < 5000:
    # 중형주
    if 1.2 <= 수익률 < 3.0 and 분당매도수량 > 분당매수수량 * 1.5:
        매도 = True
    elif 고저평균대비등락율 > 2.5:
        매도 = True

else:
    # 대형주
    if 1.2 <= 수익률 < 3.0 and 분당매도수량 > 분당매수수량 * 1.4:
        매도 = True
    elif 고저평균대비등락율 > 2:
        매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

---

**Last Update: 2025-01-18**
