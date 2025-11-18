# 조건식 (Condition)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- Back_Testing_Guideline_Min.md 에 있는 조건식을 사용하여 만든 조건식

## 목차
- [조건식 (Condition)](#조건식-condition)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - Bollinger Reversal](#condition---bollinger-reversal)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 소개

이 문서는 전체 거래시간 09:00~15:18 구간에서 볼린저밴드 하단 터치 후 반등을 노리는 분봉 전략입니다.
볼린저밴드 하단에서 지지를 받고 반등하는 패턴을 포착하여 저점 매수를 시도합니다.

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.
- 분봉 데이터 기반으로 900~1518 (09:00~15:18) 시간에만 거래합니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `BBR`: Bollinger Band Reversal을 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.
   - `M`: Min (분봉) 조건식을 의미합니다.

2. **예시**:
   - `C_BBR_M_B`: Bollinger Reversal 분봉 매수 조건식
   - `C_BBR_M_S`: Bollinger Reversal 분봉 매도 조건식

---

# Condition - Bollinger Reversal

## 조건식

### 매수 조건식

```python
# 볼린저밴드 반전 전략 (09:00 ~ 15:18)

# 시간 조건
if not (90000 <= 시분초 <= 151800):
    매수 = False

# 데이터 충분성 확인 (볼린저밴드 계산을 위해)
elif not (데이터길이 > 30):
    매수 = False

# 가격 및 등락율 조건
elif not (2000 < 현재가 <= 50000):
    매수 = False
elif not (-5.0 < 등락율 <= 15.0):
    매수 = False

# VI 제외
elif not (현재가 < VI아래5호가):
    매수 = False

# 볼린저밴드 하단 터치 후 반등 조건 (핵심)
# 1) 이전 봉에서 하단 터치
elif not (분봉저가N(1) <= BBL_N(1)):
    매수 = False

# 2) 현재 봉에서 하단 위로 반등
elif not (현재가 > BBL):
    매수 = False
elif not (현재가 > 분봉시가):
    매수 = False

# 3) 볼린저밴드 폭 확인 (변동성 있어야 함)
elif not ((BBU - BBL) / BBM > 0.04):
    매수 = False

# RSI 과매도 조건
elif not (RSI_N(1) < 35):
    매수 = False
elif not (RSI > RSI_N(1)):
    매수 = False

# 체결강도 조건
elif not (체결강도 > 110):
    매수 = False
elif not (체결강도 > 체결강도N(1)):
    매수 = False

# 거래량 조건
elif not (분당거래대금 > 분당거래대금평균(20)):
    매수 = False

# 시가총액별 세분화 조건
elif 시가총액 < 2500:
    # 소형주
    if not (분당매수수량 > 분당매도수량 * 1.3):
        매수 = False
    elif not (체결강도평균(10) > 95):
        매수 = False
    elif not (당일거래대금 > 30 * 100):
        매수 = False
    elif not (회전율 > 2):
        매수 = False
    elif not (전일비 > 50):
        매수 = False
    elif not (현재가 > BBL * 1.005):
        매수 = False

else:
    # 중대형주
    if not (분당매수수량 > 분당매도수량):
        매수 = False
    elif not (체결강도평균(10) > 100):
        매수 = False
    elif not (당일거래대금 > 80 * 100):
        매수 = False
    elif not (회전율 > 1.5):
        매수 = False
    elif not (전일비 > 40):
        매수 = False
    elif not (현재가 > BBL * 1.003):
        매수 = False

# 최종 매수 실행
if 매수:
    self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)
```

### 매도 조건식

```python
# 볼린저밴드 상단 도달 및 익절 전략
if 등락율 > 29.5:
    매도 = True
elif 수익률 >= 3.5:
    매도 = True
elif 수익률 <= -2.5:
    매도 = True
elif 최고수익률 - 수익률 >= 2.5:
    매도 = True
elif 보유시간 > 180:  # 180분 (3시간) 초과 보유 시 청산
    매도 = True

# 볼린저밴드 상단 도달 (핵심 익절 조건)
elif 현재가 >= BBU * 0.995:
    if 수익률 > 1.0:
        매도 = True

# 볼린저밴드 중심선 하향 이탈
elif 현재가 < BBM and 현재가N(1) >= BBM_N(1):
    if 수익률 > 0.5:
        매도 = True

# RSI 과매수 조건
elif RSI > 70:
    if 수익률 > 1.5:
        매도 = True

# 체결강도 약화
elif 체결강도 < 95:
    매도 = True

# 분봉 음봉 전환
elif 현재가 < 분봉시가 and 분봉시가N(1) < 현재가N(1):
    if 수익률 > 0.8:
        매도 = True

# 시가총액별 세분화 매도 조건
elif 시가총액 < 2500:
    # 소형주: 빠른 청산
    if 1.5 <= 수익률 < 3.5 and 분당매도수량 > 분당매수수량 * 1.6:
        매도 = True
    elif 현재가 < 이동평균(20) and 수익률 > 0.8:
        매도 = True

else:
    # 중대형주
    if 1.5 <= 수익률 < 3.5 and 분당매도수량 > 분당매수수량 * 1.4:
        매도 = True
    elif 현재가 < 이동평균(20) and 수익률 > 1.0:
        매도 = True

if 매도:
    self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)
```

---

**Last Update: 2025-01-18**
