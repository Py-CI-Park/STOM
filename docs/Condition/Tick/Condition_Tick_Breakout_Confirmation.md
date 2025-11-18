# 조건식 (Condition) - Breakout Confirmation Strategy

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Tick.md에 있는 조건식을 사용하여 만든 조건식

## 목차
- [조건식 (Condition) - Breakout Confirmation Strategy](#조건식-condition---breakout-confirmation-strategy)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - Breakout Confirmation](#condition---breakout-confirmation)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 소개

이 문서는 **돌파 확인 전략(Breakout Confirmation Strategy)**을 설명합니다. 장 초반(09:00:00 ~ 09:20:00) 고가를 돌파하는 움직임을 확인하고, 거래량을 동반한 진짜 돌파인지 확인 후 진입하는 전략입니다.

### 전략 개요
- **거래 시간**: 90000 ~ 92000 (9시 ~ 9시 20분)
- **목표**: 고가 돌파 + 거래량 확인
- **핵심 지표**: 최고현재가, 초당거래대금, 체결강도 변화
- **리스크 관리**: 거짓 돌파 필터링

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.
- 돌파 신호의 진위를 거래량과 체결강도로 확인합니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `BC`: Breakout Confirmation을 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.

2. **예시**:
   - `C_BC_B`: 돌파 확인 전략의 매수 조건식
   - `C_BC_S`: 돌파 확인 전략의 매도 조건식

---

# Condition - Breakout Confirmation

## 조건식

### 매수 조건식

```python
# Breakout Confirmation Strategy - 고가 돌파 확인 전략
# 거래 시간: 90000 ~ 92000 (9시 ~ 9시 20분)

매수 = False

# 시간 제한: 장 초반 20분만 거래
if not (90000 <= 시분초 < 92000):
    매수 = False

# 기본 필터링
elif not (1800 < 현재가 <= 42000):
    매수 = False
elif not (2.0 < 등락율 <= 29.0):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# 충분한 데이터 확보 (최소 60틱)
elif not (데이터길이 > 60):
    매수 = False

# 시가총액별 조건
elif 시가총액 < 3200:
    # 소형주 (3200억 미만)
    # 고가 돌파 확인
    if not (현재가 >= 최고현재가(60, 1)):
        매수 = False
    elif not (현재가 > 현재가N(1)):
        매수 = False
    elif not (현재가 >= 고가):
        매수 = False
    # 거래량 동반 확인
    elif not (초당거래대금 > 초당거래대금평균(60) * 2.5):
        매수 = False
    elif not (초당거래대금 > 초당거래대금N(1)):
        매수 = False
    elif not (초당거래대금평균(30) > 초당거래대금평균(30, 1)):
        매수 = False
    # 체결강도 동반 상승
    elif not (체결강도 > 145):
        매수 = False
    elif not (체결강도 > 체결강도N(1)):
        매수 = False
    elif not (체결강도평균(30) > 체결강도평균(30, 1)):
        매수 = False
    elif not (최고체결강도(30) > 최고체결강도(30, 1)):
        매수 = False
    # 매수 우위 확인
    elif not (누적초당매수수량(30) > 누적초당매도수량(30) * 1.7):
        매수 = False
    elif not (최고초당매수수량(30) > 최고초당매도수량(30) * 2.2):
        매수 = False
    # 지속적인 상승 각도
    elif not (등락율각도(30) > 8):
        매수 = False
    elif not (등락율각도(30) > 등락율각도(30, 1)):
        매수 = False
    # 거래 활성도
    elif not (전일비 > 160):
        매수 = False
    elif not (전일동시간비 > 200):
        매수 = False
    elif not (회전율 > 2.2):
        매수 = False
    # 당일거래대금
    elif not (당일거래대금 > 15 * 100):
        매수 = False
    # 호가 압력
    elif not (매수총잔량 > 매도총잔량 * 1.2):
        매수 = False

else:
    # 중대형주 (3200억 이상)
    # 고가 돌파 확인
    if not (현재가 >= 최고현재가(60, 1)):
        매수 = False
    elif not (현재가 > 현재가N(1)):
        매수 = False
    elif not (현재가 >= 고가):
        매수 = False
    # 거래량 동반 확인
    elif not (초당거래대금 > 초당거래대금평균(60) * 2.0):
        매수 = False
    elif not (초당거래대금 > 초당거래대금N(1)):
        매수 = False
    elif not (초당거래대금평균(30) > 초당거래대금평균(30, 1)):
        매수 = False
    # 체결강도 동반 상승
    elif not (체결강도 > 133):
        매수 = False
    elif not (체결강도 > 체결강도N(1)):
        매수 = False
    elif not (체결강도평균(30) > 체결강도평균(30, 1)):
        매수 = False
    elif not (최고체결강도(30) > 최고체결강도(30, 1)):
        매수 = False
    # 매수 우위 확인
    elif not (누적초당매수수량(30) > 누적초당매도수량(30) * 1.5):
        매수 = False
    elif not (최고초당매수수량(30) > 최고초당매도수량(30) * 1.8):
        매수 = False
    # 지속적인 상승 각도
    elif not (등락율각도(30) > 10):
        매수 = False
    elif not (등락율각도(30) > 등락율각도(30, 1)):
        매수 = False
    # 거래 활성도
    elif not (전일비 > 120):
        매수 = False
    elif not (전일동시간비 > 150):
        매수 = False
    elif not (회전율 > 1.6):
        매수 = False
    # 당일거래대금
    elif not (당일거래대금 > 70 * 100):
        매수 = False
    # 호가 압력
    elif not (매수총잔량 > 매도총잔량):
        매수 = False
```

### 매도 조건식

```python
# Breakout Confirmation Strategy - 돌파 실패 감지 매도 전략

매도 = False

# 상한가 근접 시 매도
if 등락율 > 29.5:
    매도 = True

# 수익률 기준 매도
elif 수익률 >= 4.5:
    매도 = True
elif 수익률 <= -2.5:
    매도 = True

# 최고수익률 대비 하락 시 매도
elif 최고수익률 >= 5.5 and 수익률 < 최고수익률 - 2.0:
    매도 = True

# 시가총액별 매도 조건
elif 시가총액 < 3200:
    # 소형주 매도 조건 - 돌파 실패 감지
    # 고가 대비 하락
    if 현재가 < 고가 * 0.97 and (초당매도수량 - 초당매수수량) >= 매수총잔량 * 30 / 100:
        매도 = True
    # 연속 하락 (돌파 실패)
    elif 현재가 < 현재가N(1) and 현재가N(1) < 현재가N(2) and 현재가N(2) < 현재가N(3):
        매도 = True
    # 체결강도 급락
    elif 체결강도 < 100 and 체결강도평균(30) < 체결강도평균(30, 1):
        매도 = True
    elif 체결강도 < 체결강도N(1) and 체결강도N(1) < 체결강도N(2):
        매도 = True
    # 초당거래대금 급감
    elif 초당거래대금 < 초당거래대금평균(30) * 0.8:
        매도 = True
    elif 초당거래대금평균(30) < 초당거래대금평균(30, 1):
        매도 = True
    # 등락율 각도 하락
    elif 등락율각도(30) < 5 and 등락율각도(30) < 등락율각도(30, 1):
        매도 = True
    elif 등락율각도(30) < 0:
        매도 = True
    # 매도 우위
    elif (초당매도수량 - 초당매수수량) >= 매수총잔량 * 45 / 100:
        매도 = True
    # 호가 역전
    elif 매도총잔량 > 매수총잔량 * 1.35:
        매도 = True
    # 시간 기준
    elif 보유시간 > 660:  # 11분 이상 보유 시 매도
        매도 = True

else:
    # 중대형주 매도 조건 - 돌파 실패 감지
    # 고가 대비 하락
    if 현재가 < 고가 * 0.975 and (초당매도수량 - 초당매수수량) >= 매수총잔량 * 40 / 100:
        매도 = True
    # 연속 하락 (돌파 실패)
    elif 현재가 < 현재가N(1) and 현재가N(1) < 현재가N(2) and 현재가N(2) < 현재가N(3):
        매도 = True
    # 체결강도 급락
    elif 체결강도 < 108 and 체결강도평균(30) < 체결강도평균(30, 1):
        매도 = True
    elif 체결강도 < 체결강도N(1) and 체결강도N(1) < 체결강도N(2):
        매도 = True
    # 초당거래대금 급감
    elif 초당거래대금 < 초당거래대금평균(30) * 0.85:
        매도 = True
    elif 초당거래대금평균(30) < 초당거래대금평균(30, 1):
        매도 = True
    # 등락율 각도 하락
    elif 등락율각도(30) < 7 and 등락율각도(30) < 등락율각도(30, 1):
        매도 = True
    elif 등락율각도(30) < 2:
        매도 = True
    # 매도 우위
    elif (초당매도수량 - 초당매수수량) >= 매수총잔량 * 50 / 100:
        매도 = True
    # 호가 역전
    elif 매도총잔량 > 매수총잔량 * 1.25:
        매도 = True
    # 시간 기준
    elif 보유시간 > 840:  # 14분 이상 보유 시 매도
        매도 = True
```

---

**Last Update: 2025-01-18**
