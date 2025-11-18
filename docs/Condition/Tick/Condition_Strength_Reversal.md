# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Tick.md 에 있는 조건식을 사용하여 만든 조건식

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - Strength Reversal](#condition---strength-reversal)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 소개

이 문서는 장초 09:05:00~09:10:00 구간에서 체결강도의 역전 패턴을 감지하여 반등 매매를 수행하는 전략입니다.
체결강도가 일시적으로 하락한 후 다시 상승 전환할 때 진입하여 반등 수익을 노립니다.

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `SR`: Strength Reversal을 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.

2. **예시**:
   - `C_SR_B`: Strength Reversal 매수 조건식
   - `C_SR_S`: Strength Reversal 매도 조건식

---

# Condition - Strength Reversal

## 조건식

### 매수 조건식

```python
# 체결강도 역전 전략 (09:05:00 ~ 09:10:00)

# 시간 조건
if not (90500 <= 시분초 <= 91000):
    매수 = False

# 가격 및 등락율 조건
elif not (1500 < 현재가 <= 40000):
    매수 = False
elif not (1.5 < 등락율 <= 18.0):
    매수 = False

# VI 제외
elif not (현재가 < VI아래5호가):
    매수 = False

# 체결강도 역전 패턴 감지
# 1) 최근 30틱 중 체결강도가 최저점을 찍었다가 상승 중
elif not (최저체결강도(30) < 80):
    매수 = False
elif not (체결강도 > 최저체결강도(30) * 1.3):
    매수 = False
elif not (체결강도 > 체결강도N(1) and 체결강도N(1) > 체결강도N(2)):
    매수 = False

# 거래대금 조건
elif not (초당거래대금 > 초당거래대금평균(60)):
    매수 = False

# 등락율 각도 조건 (하락 후 반등)
elif not (-5 < 등락율각도(30) < 20):
    매수 = False
elif not (등락율각도(30) > 등락율각도(30, 1)):
    매수 = False

# 시가총액별 조건
elif 시가총액 < 2500:
    # 소형주
    if not (초당매수수량 > 초당매도수량):
        매수 = False
    elif not (매수총잔량 > 매도총잔량):
        매수 = False
    elif not (전일비 > 50):
        매수 = False
    elif not (당일거래대금 > 20 * 100):
        매수 = False
    elif not (현재가 > 저가 * 1.02):
        매수 = False
    elif not (체결강도평균(10) > 90):
        매수 = False

else:
    # 중대형주
    if not (초당매수수량 > 초당매도수량 * 0.8):
        매수 = False
    elif not (매수총잔량 > 매도총잔량 * 0.9):
        매수 = False
    elif not (전일비 > 40):
        매수 = False
    elif not (당일거래대금 > 50 * 100):
        매수 = False
    elif not (현재가 > 저가 * 1.015):
        매수 = False
    elif not (체결강도평균(10) > 95):
        매수 = False

# 최종 매수 실행
if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식

```python
# 반등 익절 및 재하락 방어 전략
if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 2.5:
    매도 = True
elif 수익률 <= -2.5:
    매도 = True
elif 최고수익률 - 수익률 >= 1.8:
    매도 = True
elif 보유시간 > 180:  # 3분 초과 보유 시 청산
    매도 = True

# 체결강도 재하락 감지
elif 체결강도 < 80:
    매도 = True
elif 체결강도N(1) > 체결강도N(2) and 체결강도 < 체결강도N(1):
    if 수익률 > 0.5:
        매도 = True

# 시가총액별 세분화 매도 조건
elif 시가총액 < 2500:
    # 소형주: 빠른 청산
    if 0.8 <= 수익률 < 2.5 and 초당매도수량 > 초당매수수량 * 1.5:
        매도 = True
    elif 등락율각도(20) < 0:
        매도 = True

else:
    # 중대형주
    if 0.8 <= 수익률 < 2.5 and 초당매도수량 > 초당매수수량 * 1.3:
        매도 = True
    elif 등락율각도(20) < -3:
        매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

---

**Last Update: 2025-01-18**
