# 조건식 (Condition) - Moving Average Convergence Strategy (분봉)

- STOM 주식 자동거래에 사용하기 위한 조건식 문서
- [[Back_Testing_Guideline_Min]] 을(를) 기반으로 작성한 Min 조건식
- [[Condition_Document_Template_Guideline]] 을(를) 바탕으로 템플릿 구조를 적용한 문서

## 목차
- [조건식 (Condition) - Moving Average Convergence Strategy (분봉)](#조건식-condition---moving-average-convergence-strategy-분봉)
  - [목차](#목차)
  - [소개](#소개)
  - [가이드라인](#가이드라인)
    - [저장 이름 규칙](#저장-이름-규칙)
- [Condition - MA Convergence](#condition---ma-convergence)
  - [조건식](#조건식)
    - [매수 조건식](#매수-조건식)
    - [매도 조건식](#매도-조건식)

## 개요

본 문서는 STOM 주식 자동거래 시스템에서 **장중 전체(09:00~15:18) 이동평균선 수렴/발산 전략**을 정의한다.

- **대상 시간 구간**: 09:00:00 ~ 15:18:00 (장중 전체)
- **대상 종목**: 가격대 1,800원~52,000원, 등락율 1.2~28.5%
- **전략 타입**: 이동평균선 정배열 + 골든크로스 포착 (MA Convergence)
- **핵심 변수**: 이동평균(5/20/60), KAMA, APO, 체결강도, 분당거래대금
- **업데이트 이력**:
  - 초기 문서 작성

## 소개

이 문서는 **이동평균선 수렴/발산 전략(Moving Average Convergence Strategy)**을 설명합니다. 단기, 중기, 장기 이동평균선의 배열과 골든크로스를 확인하여 강한 추세를 포착하는 전략입니다.

### 전략 개요
- **거래 시간**: 900 ~ 1518 (9시 ~ 15시 18분)
- **목표**: 이동평균선 정배열 + 골든크로스
- **핵심 지표**: 이동평균(5, 20, 60), KAMA, APO
- **리스크 관리**: 추세 전환 시 빠른 청산

## 가이드라인

- 모든 조건식은 Python으로 작성되어 있으며, 주식 거래의 자동화를 목표로 합니다.
- 각 조건식은 특정 조건을 만족할 때 매수 또는 매도를 실행합니다.
- 다중 이동평균선을 활용한 추세 확인이 핵심입니다.

### 저장 이름 규칙

1. **기본 규칙**:
   - `C`: Condition을 의미합니다.
   - `MAC`: Moving Average Convergence를 의미합니다.
   - `B`: 매수 조건식을 의미합니다.
   - `S`: 매도 조건식을 의미합니다.

2. **예시**:
   - `C_MAC_B`: 이동평균선 수렴 전략의 매수 조건식
   - `C_MAC_S`: 이동평균선 수렴 전략의 매도 조건식

---

# Condition - MA Convergence

## 조건식

### 매수 조건식

```python
# Moving Average Convergence Strategy - 이동평균선 정배열 포착 전략
# 거래 시간: 900 ~ 1518 (9시 ~ 15시 18분)

매수 = False

# 시간 제한: 정규 장 시간만 거래
if not (90000 <= 시분초 <= 151800):
    매수 = False

# 기본 필터링
elif not (1800 < 현재가 <= 52000):
    매수 = False
elif not (1.2 < 등락율 <= 28.5):
    매수 = False
elif not (현재가 < VI아래5호가):
    매수 = False
elif 라운드피겨위5호가이내:
    매수 = False

# 충분한 데이터 확보
elif not (데이터길이 > 65):
    매수 = False

# 시가총액별 조건
elif 시가총액 < 4200:
    # 소형주 (4200억 미만)
    # 이동평균선 정배열 (골든크로스 패턴)
    if not (이동평균(5) > 이동평균(20)):
        매수 = False
    elif not (이동평균(20) > 이동평균(60)):
        매수 = False
    elif not (이동평균(5) > 이동평균(60)):
        매수 = False
    # 이동평균선 상향
    elif not (이동평균(5) > 이동평균(5, 1)):
        매수 = False
    elif not (이동평균(20) > 이동평균(20, 1)):
        매수 = False
    elif not (이동평균(60) > 이동평균(60, 1)):
        매수 = False
    # 골든크로스 확인 (단기선이 중기선 상향 돌파)
    elif not (이동평균(5) > 이동평균(20) and 이동평균(5, 1) <= 이동평균(20, 1)):
        매수 = False
    # 현재가 > 이동평균선
    elif not (현재가 > 이동평균(5)):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
    # KAMA (적응형 이동평균) 상향
    elif not (KAMA > KAMA_N(1)):
        매수 = False
    elif not (현재가 > KAMA):
        매수 = False
    # APO (절대 가격 오실레이터) 양수
    elif not (APO > 0):
        매수 = False
    elif not (APO > APO_N(1)):
        매수 = False
    # PPO (백분율 가격 오실레이터) 양수
    elif not (PPO > 0):
        매수 = False
    # 체결강도
    elif not (체결강도 > 120):
        매수 = False
    elif not (체결강도평균(20) > 110):
        매수 = False
    # 분당거래대금 증가
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.2):
        매수 = False
    # 분봉 양봉
    elif not (현재가 > 분봉시가):
        매수 = False
    # 거래 활성도
    elif not (당일거래대금 > 22 * 100):
        매수 = False
    elif not (전일비 > 85):
        매수 = False
    elif not (회전율 > 1.1):
        매수 = False
    # RSI 중립 ~ 상승
    elif not (45 < RSI < 72):
        매수 = False

else:
    # 중대형주 (4200억 이상)
    # 이동평균선 정배열 (골든크로스 패턴)
    if not (이동평균(5) > 이동평균(20)):
        매수 = False
    elif not (이동평균(20) > 이동평균(60)):
        매수 = False
    elif not (이동평균(5) > 이동평균(60)):
        매수 = False
    # 이동평균선 상향
    elif not (이동평균(5) > 이동평균(5, 1)):
        매수 = False
    elif not (이동평균(20) > 이동평균(20, 1)):
        매수 = False
    elif not (이동평균(60) > 이동평균(60, 1)):
        매수 = False
    # 골든크로스 확인 (단기선이 중기선 상향 돌파)
    elif not (이동평균(5) > 이동평균(20) and 이동평균(5, 1) <= 이동평균(20, 1)):
        매수 = False
    # 현재가 > 이동평균선
    elif not (현재가 > 이동평균(5)):
        매수 = False
    elif not (현재가 > 이동평균(20)):
        매수 = False
    # KAMA (적응형 이동평균) 상향
    elif not (KAMA > KAMA_N(1)):
        매수 = False
    elif not (현재가 > KAMA):
        매수 = False
    # APO (절대 가격 오실레이터) 양수
    elif not (APO > 0):
        매수 = False
    elif not (APO > APO_N(1)):
        매수 = False
    # PPO (백분율 가격 오실레이터) 양수
    elif not (PPO > 0):
        매수 = False
    # 체결강도
    elif not (체결강도 > 115):
        매수 = False
    elif not (체결강도평균(20) > 107):
        매수 = False
    # 분당거래대금 증가
    elif not (분당거래대금 > 분당거래대금평균(30) * 1.15):
        매수 = False
    # 분봉 양봉
    elif not (현재가 > 분봉시가):
        매수 = False
    # 거래 활성도
    elif not (당일거래대금 > 110 * 100):
        매수 = False
    elif not (전일비 > 65):
        매수 = False
    elif not (회전율 > 0.75):
        매수 = False
    # RSI 중립 ~ 상승
    elif not (48 < RSI < 70):
        매수 = False
```

### 매도 조건식

```python
# Moving Average Convergence Strategy - 이동평균선 역배열 감지 매도 전략

매도 = False

# 상한가 근접 시 매도
if 등락율 > 29.5:
    매도 = True

# 수익률 기준 매도
elif 수익률 >= 7.0:
    매도 = True
elif 수익률 <= -2.8:
    매도 = True

# 최고수익률 대비 하락 시 매도
elif 최고수익률 >= 8.0 and 수익률 < 최고수익률 - 3.0:
    매도 = True

# 시가총액별 매도 조건
elif 시가총액 < 4200:
    # 소형주 매도 조건
    # 이동평균선 역배열 (데드크로스)
    if 이동평균(5) < 이동평균(20) and 이동평균(5, 1) >= 이동평균(20, 1):
        매도 = True
    # 이동평균선 정배열 붕괴
    elif 이동평균(20) < 이동평균(60):
        매도 = True
    # 이동평균선 하향
    elif 이동평균(5) < 이동평균(5, 1) and 이동평균(20) < 이동평균(20, 1):
        매도 = True
    # 현재가 < 이동평균선 (이탈)
    elif 현재가 < 이동평균(5) and 현재가N(1) >= 이동평균(5, 1):
        매도 = True
    elif 현재가 < 이동평균(20):
        매도 = True
    # KAMA 하향
    elif KAMA < KAMA_N(1) and KAMA_N(1) < KAMA_N(2):
        매도 = True
    elif 현재가 < KAMA:
        매도 = True
    # APO 음수 전환
    elif APO < 0 and APO_N(1) >= 0:
        매도 = True
    elif APO < APO_N(1) and APO_N(1) < APO_N(2):
        매도 = True
    # PPO 음수 전환
    elif PPO < 0:
        매도 = True
    # 체결강도 약화
    elif 체결강도 < 93:
        매도 = True
    # RSI 과매수
    elif RSI > 73:
        매도 = True
    # MACD 데드크로스
    elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    # 시간 기준
    elif 보유시간 > 130:  # 130분 이상 보유 시 매도
        매도 = True

else:
    # 중대형주 매도 조건
    # 이동평균선 역배열 (데드크로스)
    if 이동평균(5) < 이동평균(20) and 이동평균(5, 1) >= 이동평균(20, 1):
        매도 = True
    # 이동평균선 정배열 붕괴
    elif 이동평균(20) < 이동평균(60):
        매도 = True
    # 이동평균선 하향
    elif 이동평균(5) < 이동평균(5, 1) and 이동평균(20) < 이동평균(20, 1):
        매도 = True
    # 현재가 < 이동평균선 (이탈)
    elif 현재가 < 이동평균(5) and 현재가N(1) >= 이동평균(5, 1):
        매도 = True
    elif 현재가 < 이동평균(20):
        매도 = True
    # KAMA 하향
    elif KAMA < KAMA_N(1) and KAMA_N(1) < KAMA_N(2):
        매도 = True
    elif 현재가 < KAMA:
        매도 = True
    # APO 음수 전환
    elif APO < 0 and APO_N(1) >= 0:
        매도 = True
    elif APO < APO_N(1) and APO_N(1) < APO_N(2):
        매도 = True
    # PPO 음수 전환
    elif PPO < 0:
        매도 = True
    # 체결강도 약화
    elif 체결강도 < 97:
        매도 = True
    # RSI 과매수
    elif RSI > 71:
        매도 = True
    # MACD 데드크로스
    elif MACD < MACDS and MACD_N(1) >= MACDS_N(1):
        매도 = True
    # 시간 기준
    elif 보유시간 > 190:  # 190분 이상 보유 시 매도
        매도 = True
```

---

**Last Update: 2025-01-18**

## 조건식 개선 방향 연구

### 1. 추가 지표 활용 연구

**우선순위: 높음**
- **TA-Lib 지표 조합 확대**
  - ADX (추세 강도) + DMI (방향성) 조합
  - Ichimoku Cloud (일목균형표) 활용
  - 구현 난이도: 중

- **변동성 지표 추가**
  - ATR (Average True Range) 기반 손절폭 설정
  - Bollinger Band Width로 변동성 확대 구간 포착
  - 구현 난이도: 낮음

### 2. 시간대별 전략 세분화 연구

**우선순위: 높음**
- **장 시간대별 분봉 전략 차등화**
  - 09:00-10:00: 5분봉 전략
  - 10:00-14:00: 10분봉 전략
  - 14:00-15:00: 3분봉 전략
  - 구현 난이도: 중

### 3. 매도 조건 고도화 연구

**우선순위: 높음**
- **TA-Lib 매도 신호 강화**
  - MACD 데드크로스 + RSI 과매수 조합
  - Stochastic %K/%D 하향 교차 시 매도
  - 구현 난이도: 낮음

- **이동평균선 이탈 기반 매도**
  - 5MA 하향 돌파 시 경고
  - 20MA 하향 돌파 시 청산
  - 구현 난이도: 낮음

### 4. 리스크 관리 강화 연구

**우선순위: 높음**
- **다중 시간프레임 분석**
  - 1분봉 + 5분봉 + 10분봉 동시 확인
  - 상위 시간프레임 추세와 부합 시만 진입
  - 구현 난이도: 중

- **거래량 프로파일 분석**
  - 가격대별 거래량 분포 확인
  - 고거래량 구간 지지/저항 활용
  - 구현 난이도: 높음

### 5. 최적화 전략 개선 연구

**우선순위: 중간**
- **TA-Lib 파라미터 최적화**
  - RSI 기간: 14 → 10~20 범위 탐색
  - MACD (12,26,9) → (8,17,9) 등 변형 테스트
  - 구현 난이도: 중

- **기계학습 기반 지표 가중치 최적화**
  - 각 TA-Lib 지표의 예측력 평가
  - 가중치 동적 조정
  - 구현 난이도: 높음

### 구현 우선순위

1. **1단계 (즉시 구현)**:
   - 변동성 지표 추가 (ATR, BB Width)
   - TA-Lib 매도 신호 강화
   - 이동평균선 이탈 기반 매도

2. **2단계 (1개월 내)**:
   - TA-Lib 지표 조합 확대 (ADX, DMI, Ichimoku)
   - 시간대별 분봉 전략 차등화
   - 다중 시간프레임 분석

3. **3단계 (3개월 내)**:
   - TA-Lib 파라미터 최적화
   - 거래량 프로파일 분석
   - 기계학습 기반 최적화

