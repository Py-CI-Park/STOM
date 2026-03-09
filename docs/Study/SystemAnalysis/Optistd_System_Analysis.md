# OPTISTD (최적화 기준값) 시스템 전체 분석

**작성일**: 2025-11-29
**파일**: `backtester/back_static.py`, `optimiz.py`
**목적**: 교차검증 최적화 시스템의 완전한 이해 및 개선
---

## 📋 목차
1. [OPTISTD의 14가지 종류와 계산식](#1-optistd의-14가지-종류와-계산식)
2. [STD_LIST (제한 조건) 구조](#2-std_list-제한-조건-구조)
3. [RESULT (백테스팅 결과) 구조](#3-result-백테스팅-결과-구조)
4. [TRAIN / VALID / TOTAL / TEST 차이점](#4-train--valid--total--test-차이점)
5. [교차검증 MERGE 계산 방식](#5-교차검증-merge-계산-방식)
6. [문제의 근본 원인](#6-문제의-근본-원인)
7. [해결 방안 비교](#7-해결-방안-비교)
---

## 1. OPTISTD의 14가지 종류와 계산식

### 1.1 단순 기준값 (Simple Standards)
**파일**: `backtester/back_static.py:486-514`, `ui/set_text.py:1-14`
```python
TG (Total Gain - 수익금합계)
= tsg (int)
→ 사용 예: 절대 수익금 중심 최적화
TP (Total Profit % - 수익률합계)
= tpp (float)
→ 사용 예: 수익률 중심 최적화 (자본 규모 무관)
TPI (Trading Performance Index - 매매성능지수)
= wr / 100 * (1 + appp / ampp)
# appp = 평균이익수익률, ampp = 평균손실수익률
→ 사용 예: 위험 대비 성과 평가
CAGR (Compound Annual Growth Rate - 연간예상수익률)
= tpp / day_count * (250 or 365)
→ 사용 예: 장기 성장성 평가
```

### 1.2 금액 기반 복합 기준값 (Gain-based Complex)
```python
GM (Gain / MDD)
= tsg / mdd_
→ 사용 예: 낙폭 대비 수익금 비율
G2M (Gain² / MDD / Betting)
= tsg * tsg / mdd_ / betting
→ 사용 예: 수익금 제곱으로 높은 수익 강조
GAM (Gain × Average Profit / MDD)
= tsg * app / mdd_
→ 사용 예: 평균 수익률과 총 수익 동시 고려
GWM (Gain × Win Rate / MDD / 100)
= tsg * wr / mdd_ / 100
→ 사용 예: 승률과 수익금 균형
GTM (Gain × APP × WR × TPI × CAGR / MDD / 10000)
= tsg * app * wr * tpi * cagr / mdd_ / 10000
→ 사용 예: 종합 성능 지표 (모든 요소 고려)
```

### 1.3 비율 기반 복합 기준값 (Profit-based Complex)
```python
PM (Profit / MDD)
= tpp / mdd
→ 사용 예: 낙폭 대비 수익률 (샤프 비율 유사)
P2M (Profit² / MDD / 100)
= tpp * tpp / mdd / 100
→ 사용 예: 높은 수익률 강조
PAM (Profit × Average Profit / MDD)
= tpp * app / mdd
→ 사용 예: 일관된 수익률 선호
PWM (Profit × Win Rate / MDD / 100)
= tpp * wr / mdd / 100
→ 사용 예: 승률 중시 전략
PTM (Profit × APP × WR × TPI × CAGR / MDD / 10000)
= tpp * app * wr * tpi * cagr / mdd / 10000
→ 사용 예: 종합 성능 지표 (비율 기반)
```
---

## 2. STD_LIST (제한 조건) 구조

### 2.1 std_list의 14개 값
**파일**: `backtester/back_static.py:477`
```python
std_list = [
    mdd_low,   mdd_high,   # 인덱스 0,1   최대낙폭률 범위
    mhct_low,  mhct_high,  # 인덱스 2,3   보유종목수 범위
    wr_low,    wr_high,    # 인덱스 4,5   승률 범위
    ap_low,    ap_high,    # 인덱스 6,7   평균수익률 범위
    atc_low,   atc_high,   # 인덱스 8,9   일평균거래횟수 범위 ⭐
    cagr_low,  cagr_high,  # 인덱스 10,11 연간예상수익률 범위
    tpi_low,   tpi_high    # 인덱스 12,13 매매성능지수 범위
]
```

### 2.2 기본값
**파일**: `utility/database_check.py:92`
```python
기본값 문자열:
'0.0;1000.0;0;100.0;0.0;100.0;-10.0;10.0;0.0;100.0;-10000.0;10000.0;0.0;10.0'
파싱된 값:
- 최대낙폭률:     0.0 ~ 1000.0 %
- 보유종목수:     0 ~ 100 개
- 승률:           0.0 ~ 100.0 %
- 평균수익률:     -10.0 ~ 10.0 %
- 일평균거래횟수: 0.0 ~ 100.0 회  ⭐⭐⭐
- 연간예상수익률: -10000.0 ~ 10000.0 %
- 매매성능지수:   0.0 ~ 10.0
```

### 2.3 제한 조건 체크 로직
**파일**: `backtester/back_static.py:479-480`
```python
std_true = (
    mdd_low  <= mdd  <= mdd_high  and   # 최대낙폭률
    mhct_low <= mhct <= mhct_high and   # 보유종목수
    wr_low   <= wr   <= wr_high   and   # 승률
    ap_low   <= app  <= ap_high   and   # 평균수익률
    atc_low  <= atc  <= atc_high  and   # 일평균거래횟수 ⭐
    cagr_low <= cagr <= cagr_high and   # 연간예상수익률
    tpi_low  <= tpi  <= tpi_high        # 매매성능지수
)
# 모든 조건을 AND로 연결 → 하나라도 불만족 시 False
# std_true = False → std_false_point (-2,222,222,222) 반환
```
---

## 3. RESULT (백테스팅 결과) 구조

### 3.1 GetBackResult 반환값 (15개)
**파일**: `backtester/back_static.py:837-868`
```python
result = (
    tc,    # 인덱스 0:  거래횟수 (Trade Count)
    atc,   # 인덱스 1:  일평균거래횟수 (Average Trade Count) ⭐
    pc,    # 인덱스 2:  익절 횟수 (Profit Count)
    mc,    # 인덱스 3:  손절 횟수 (Minus Count)
    wr,    # 인덱스 4:  승률 (Win Rate %)
    ah,    # 인덱스 5:  평균보유기간 (Average Holding seconds)
    app,   # 인덱스 6:  평균수익률 (Average Profit %)
    tpp,   # 인덱스 7:  수익률합계 (Total Profit %)
    tsg,   # 인덱스 8:  수익금합계 (Total Sum Gain)
    mhct,  # 인덱스 9:  최대보유종목수 (Max Holding Count)
    seed,  # 인덱스 10: 필요자금 (Seed money)
    cagr,  # 인덱스 11: 연간예상수익률 (CAGR %)
    tpi,   # 인덱스 12: 매매성능지수 (TPI)
    mdd,   # 인덱스 13: 최대낙폭률 (MDD %)
    mdd_   # 인덱스 14: 최대낙폭금액 (MDD amount)
)
```

### 3.2 핵심 계산식
**파일**: `backtester/back_static.py:847-867`
```python
tc   = len(arry_tsg)  # 총 거래 횟수
atc  = round(tc / day_count, 1)  # 일평균 거래횟수 ⭐
pc   = len(arry_p)  # 수익 거래 수 (arry_p = arry_tsg[arry_tsg[:, 3] >= 0])
mc   = len(arry_m)  # 손실 거래 수 (arry_m = arry_tsg[arry_tsg[:, 3] < 0])
wr   = round(pc / tc * 100, 2)  # 승률 = 익절횟수 / 총거래횟수 × 100
ah   = round(arry_tsg[:, 0].sum() / tc, 2)  # 평균 보유시간
app  = round(arry_tsg[:, 2].sum() / tc, 2)  # 평균 수익률
tsg  = int(arry_tsg[:, 3].sum())  # 수익금 합계
# 상위 1% 이상값 제외하고 최대값 계산 (이상치 제거)
mhct = int(arry_bct[int(len(arry_bct) * 0.01):, 1].max())  # 최대 보유수
seed = int(arry_bct[int(len(arry_bct) * 0.01):, 2].max())  # 최대 필요자금
tpp  = round(tsg / seed * 100, 2)  # 수익률 합계
cagr = round(tpp / day_count * (250 or 365), 2)  # 연간 예상 수익률
tpi  = round(wr / 100 * (1 + appp / ampp), 2)  # 매매성능지수
```
---

## 4. TRAIN / VALID / TOTAL / TEST 차이점

### 4.1 데이터 분할 방식
**파일**: `backtester/optimiz.py:577-619`
```
학습기간 (TRAIN): 20주
검증기간 (VALID): 4주
확인기간 (TEST):  2주
총 기간:         26주
시간축: [과거] ←──────────────────────────→ [현재]
        ├──────────────────┬────────┬─────┤
        │   TRAIN (20주)   │VALID(4)│TEST │
        └──────────────────┴────────┴─────┘
```

### 4.2 교차검증 (Cross Validation) 분할
**파일**: `backtester/optimiz.py:580-586`
```python
# 학습: 20주, 검증: 4주인 경우
# 분할 수 = int(20 / 4) + 1 = 6개
시간축: [과거] ←────────────────────────→ [현재]
VALID1: [────────────────────][VALID1 4주]
        TRAIN1 (나머지)
VALID2: [────────────][VALID2 4주][────]
        TRAIN2 (나머지)
VALID3: [────────][VALID3 4주][────────]
        TRAIN3 (나머지)
...
VALID6: [VALID6 4주][────────────────────]
        TRAIN6 (나머지)
# 각 VALID마다 TRAIN = 전체 - VALID 기간
# 최근 데이터일수록 높은 가중치 부여
```

### 4.3 각 구분의 처리 방식

#### ✅ TRAIN 데이터 (학습 데이터)
**파일**: `backtester/back_static.py:484-514`
```python
if 'TRAIN' in pre_text or 'TOTAL' in pre_text:
    if optistd == 'TP':
        std = tpp if std_true else std_false_point
특징:
✅ std_list 제한 조건 적용
✅ 조건 불만족 시: std = -2,222,222,222
✅ 조건 만족 시: 실제 기준값 반환
```

#### ⚠️ VALID 데이터 (검증 데이터) - 수정됨 (2025-11-29)
**파일**: `backtester/back_static.py:515-545`
```python
# 수정 전 (버그):
else:  # VALID 데이터
    if optistd == 'TP':
        std = tpp  # ❌ 제한 조건 체크 없음!!!
# 수정 후 (Fix):
else:  # VALID 데이터
    if optistd == 'TP':
        std = tpp if std_true else std_false_point  # ✅ 제한 조건 적용
현재 상태 (2025-11-29 이후):
✅ std_list 제한 조건 적용
✅ 조건 불만족 시: std = -2,222,222,222
✅ TRAIN과 동일한 검증 로직
```

#### ✅ TOTAL 데이터 (전체 데이터)
```python
if 'TRAIN' in pre_text or 'TOTAL' in pre_text:
    # TRAIN과 동일한 처리
특징:
✅ TRAIN과 동일한 처리
✅ 제한 조건 적용
```

#### 📊 TEST 데이터 (확인 데이터)
**파일**: `backtester/back_static.py:404-406`
```python
if gubun == '최적화테스트':
    text2, std = GetText2('TEST', optistd, std_list, betting, dict_train)
특징:
- VALID와 동일한 처리
- 참고용 데이터 (최종 검증)
- 현재는 제한 조건 적용됨 (2025-11-29 수정 반영)
```
---

## 5. 교차검증 MERGE 계산 방식

### 5.1 기본 곱셈 방식
**파일**: `backtester/back_static.py:454-473`
```python
def GetOptiValidStd(train_data, valid_data, optistd, betting, exponential):
    """
    교차검증 결과 통합 계산
    Args:
        train_data: TRAIN 기준값 리스트
        valid_data: VALID 기준값 리스트
        optistd: 최적화 기준 (TP, TG 등)
        betting: 배팅 금액
        exponential: 가중치 사용 여부
    Returns:
        통합 기준값 (MERGE)
    """
    count = len(train_data)  # 검증 분할 수
    std = 0
    for i in range(count):
        # 가중치 적용 (최근 데이터에 높은 가중치)
        ex = (count - i) * 2 / count  # 최근 데이터 선호
        # TRAIN × VALID (또는 가중치 적용)
        if exponential and count > 1:
            std_ = train_data[i] * valid_data[i] * ex
        else:
            std_ = train_data[i] * valid_data[i]
        # 음수 처리 (둘 다 음수면 빼기)
        if train_data[i] < 0 and valid_data[i] < 0:
            std = std - std_
        else:
            std = std + std_
    # 평균 계산
    if optistd == 'TG':
        std = round(std / count / betting, 2)
    else:
        std = round(std / count, 2)
    return std
```

### 5.2 가중치 예제 (exponential=True)
**파일**: `backtester/back_static.py:457-467`
```python
"""
가중치(exponential) 예제
최근 데이터일수록 높은 가중치 (시간 감쇠)
"""
10개 분할: 2.00, 1.80, 1.60, 1.40, 1.20, 1.00, 0.80, 0.60, 0.40, 0.20
8개 분할:  2.00, 1.75, 1.50, 1.25, 1.00, 0.75, 0.50, 0.25
7개 분할:  2.00, 1.71, 1.42, 1.14, 0.86, 0.57, 0.29
6개 분할:  2.00, 1.66, 1.33, 1.00, 0.66, 0.33
5개 분할:  2.00, 1.60, 1.20, 0.80, 0.40
4개 분할:  2.00, 1.50, 1.00, 0.50
3개 분할:  2.00, 1.33, 0.66
2개 분할:  2.00, 1.00
1개 분할:  1.00 (가중치 없음)
# 계산 예시 (6개 분할, exponential=True):
MERGE = (TRAIN1×VALID1×2.00 + TRAIN2×VALID2×1.66 + ... + TRAIN6×VALID6×0.33) / 6
```
---

## 6. 문제의 근본 원인

### 6.1 코드 레벨 문제 (수정됨 2025-11-29)
**파일**: `backtester/back_static.py:476-545`
```python
def GetOptiStdText(optistd, std_list, betting, result, pre_text):
    # std_true 계산 (7가지 조건)
    std_true = (
        mdd_low  <= mdd  <= mdd_high  and
        mhct_low <= mhct <= mhct_high and
        wr_low   <= wr   <= wr_high   and
        ap_low   <= app  <= ap_high   and
        atc_low  <= atc  <= atc_high  and   # ⭐ 일평균거래횟수
        cagr_low <= cagr <= cagr_high and
        tpi_low  <= tpi  <= tpi_high
    )
    std_false_point = -2_222_222_222
    if tc > 0:
        # ✅ TRAIN과 TOTAL: 제한 조건 적용
        if 'TRAIN' in pre_text or 'TOTAL' in pre_text:
            if optistd == 'TP':
                std = tpp if std_true else std_false_point
        # ✅ VALID와 TEST: 제한 조건 적용 (수정됨)
        else:
            if optistd == 'TP':
                std = tpp if std_true else std_false_point  # 수정됨!
```

### 6.2 과거 문제 시나리오 (2025-11-29 이전)

#### 시나리오 A: 극단적 거래 횟수
```
일평균거래횟수 범위 설정: 5 ~ 20회
[수정 전 동작]
TRAIN1: atc=15 (범위 내), TP=50  → std=50 ✅
VALID1: atc=0.3 (범위 밖!), TP=80 → std=80 ❌ (체크 안함)
MERGE1: 50 × 80 = 4,000
TRAIN2: atc=12 (범위 내), TP=60  → std=60 ✅
VALID2: atc=18 (범위 내), TP=65  → std=65 ✅
MERGE2: 60 × 65 = 3,900
❌ 결과: 일평균 0.3회 전략이 최고 점수 획득!
[수정 후 동작]
TRAIN1: atc=15 (범위 내), TP=50  → std=50 ✅
VALID1: atc=0.3 (범위 밖!), TP=80 → std=-2,222,222,222 ✅
MERGE1: 50 × -2,222,222,222 = -111,111,111,100 (매우 낮은 점수)
TRAIN2: atc=12 (범위 내), TP=60  → std=60 ✅
VALID2: atc=18 (범위 내), TP=65  → std=65 ✅
MERGE2: 60 × 65 = 3,900
✅ 결과: 균형잡힌 전략이 최고 점수 획득!
```

#### 시나리오 B: 음수 역전
```
[수정 전 동작]
TRAIN: 조건 불만족 → std = -2,222,222,222
VALID: TP = -5 (손실) → std = -5 (체크 안함)
곱셈: -2,222,222,222 × -5 = 11,111,111,110 (막대한 양수!)
❌ 손실 전략이 높은 점수 획득
[수정 후 동작]
TRAIN: 조건 불만족 → std = -2,222,222,222
VALID: TP = -5 (손실) → std = -2,222,222,222 (체크 적용)
곱셈: -2,222,222,222 × -2,222,222,222 = 매우 큰 양수이지만,
      둘 다 음수이므로 std = std - std_ (빼기) 처리
✅ 손실 전략이 낮은 점수 획득
```

### 6.3 과거 설계 의도 추측
**왜 이런 버그가 있었나?**
1. **VALID는 "참고용"**: VALID를 보조 지표로 생각
2. **TRAIN만 검증**: TRAIN만 엄격히 체크하면 충분하다고 판단
3. **곱셈 필터링 기대**: VALID 극단값도 TRAIN과 곱하면 걸러질 것으로 예상
4. **단순 실수**: 코드 작성 시 누락
**실제 문제:**
- TRAIN × VALID 곱셈 구조에서 VALID의 극단값이 **증폭**됨
- 교차검증에서 여러 VALID 중 **하나만 극단값**이어도 전체 MERGE 왜곡
- 음수 × 음수 = 양수로 인한 역전 현상
---

## 7. 해결 방안 비교

### 방안 1: VALID에도 동일한 제한 적용 ✅ (적용됨)
**파일**: `backtester/back_static.py:515-545`
```python
# 수정 내용
else:  # VALID/TEST 데이터
    if 'P' in optistd:
        if optistd == 'TP':
            std = tpp if std_true else std_false_point  # 추가됨
        elif optistd == 'TPI':
            std = tpi if std_true else std_false_point  # 추가됨
        # ... 모든 optistd 케이스에 적용 ...
    elif 'G' in optistd:
        if optistd == 'TG':
            std = tsg if std_true else std_false_point  # 추가됨
        # ... 모든 optistd 케이스에 적용 ...
```
**장점:**
- ✅ 근본적 해결
- ✅ 일관된 검증 로직
- ✅ UI 설정값 완전 반영
- ✅ 극단값 증폭 방지
- ✅ 음수 역전 방지
**단점:**
- ⚠️ 기존 결과와 달라질 수 있음 (더 엄격한 필터링)
**적용 상태:** ✅ **2025-11-29 적용 완료**
---

### 방안 2: MERGE 계산 시 비정상 값 필터링 (미적용)
```python
# backtester/back_static.py:470 라인 수정
for i in range(count):
    # 극단값 제외
    if abs(train_data[i]) > 1_000_000_000 or abs(valid_data[i]) > 1_000_000_000:
        std_ = -999_999_999  # 페널티
    else:
        std_ = train_data[i] * valid_data[i] * ex
```
**장점:**
- 최소 변경
- 음수 역전 방지
**단점:**
- 임시방편
- 근본 원인 미해결
- 매직 넘버 사용
**적용 여부:** ❌ 방안 1로 근본 해결
---

### 방안 3: MERGE 계산 전 VALID 검증 (미적용)
```python
# backtester/back_static.py:385-392에 추가
for k, v in tuple_valid:
    text2, std = GetText2(f'VALID{k + 1}', optistd, std_list, betting, v)
    # 제한 조건 재검사
    if std == v[7] or std == v[8]:  # tpp or tsg
        tc, atc, ... = v
        if not (atc_low <= atc <= atc_high):
            std = -2_222_222_222
    valid_data.append(std)
```
**장점:**
- 검증 로직 분리
- 역사적 데이터 보존 가능
**단점:**
- 복잡도 증가
- 코드 중복
**적용 여부:** ❌ 방안 1이 더 깔끔함
---

## 📊 적용 결과 요약

### 수정 전 (2025-11-29 이전)
```
TRAIN 데이터: ✅ 7가지 제한 조건 체크
VALID 데이터: ❌ 제한 조건 체크 없음
TEST 데이터:  ❌ 제한 조건 체크 없음
TOTAL 데이터: ✅ 7가지 제한 조건 체크
문제점:
- 일평균거래횟수 0.5회 전략도 높은 점수 획득 가능
- 극단적인 값을 가진 VALID 결과가 MERGE 점수 왜곡
- 음수 × 음수 = 양수로 인한 역전 현상
```

### 수정 후 (2025-11-29 이후)
```
TRAIN 데이터: ✅ 7가지 제한 조건 체크
VALID 데이터: ✅ 7가지 제한 조건 체크 (수정됨)
TEST 데이터:  ✅ 7가지 제한 조건 체크 (수정됨)
TOTAL 데이터: ✅ 7가지 제한 조건 체크
개선 사항:
✅ 모든 데이터에 동일한 제한 조건 적용
✅ 일평균거래횟수 범위 벗어나면 자동 제외
✅ 균형잡힌 전략만 최적화 대상으로 선정
✅ 극단값 증폭 방지
✅ 음수 역전 방지
```
---

## 💡 실전 활용 가이드

### 1. 최적화 기준값 선택 가이드
```python
# 안정적인 수익 추구
optistd = 'PM'  # Profit / MDD - 낙폭 대비 수익률
# 높은 수익률 추구 (위험 감수)
optistd = 'P2M'  # Profit² / MDD - 높은 수익 강조
# 종합 성능 중시
optistd = 'PTM'  # 모든 지표 종합
# 절대 수익금 중시
optistd = 'TG'  # Total Gain
# 장기 투자
optistd = 'CAGR'  # 연간 예상 수익률
```

### 2. 제한 조건 설정 가이드
```python
# 보수적 설정 (안정성 중시)
일평균거래횟수: 10.0 ~ 30.0  # 과도한 거래 방지
승률:          50.0 ~ 80.0  # 최소 50% 이상
최대낙폭률:    0.0 ~ 20.0   # 낙폭 20% 이내
# 공격적 설정 (수익 중시)
일평균거래횟수: 5.0 ~ 100.0  # 넓은 범위
승률:          30.0 ~ 100.0  # 낮은 승률도 허용
최대낙폭률:    0.0 ~ 50.0   # 높은 낙폭 허용
```

### 3. 교차검증 설정 가이드
```python
# 단순 검증 (빠름)
학습기간: 20주
검증기간: 4주
확인기간: 2주
교차검증: OFF  # 'V' 사용
# 교차검증 (정밀)
학습기간: 20주
검증기간: 4주  # 20/4 = 5개 분할
확인기간: 2주
교차검증: ON  # 'VC' 사용
가중치: ON  # exponential=True
```
---

## 🔍 관련 파일
- `backtester/back_static.py:476-575` - GetOptiStdText 함수
- `backtester/back_static.py:454-473` - GetOptiValidStd 함수
- `backtester/back_static.py:837-868` - GetBackResult 함수
- `backtester/optimiz.py:189-194` - 교차검증 가중치 설정
- `ui/set_dialog_etc.py:312-338` - OPTIMIZ STD LIMIT 대화상자
- `ui/set_text.py:1-14` - optistd 설명 텍스트
- `utility/database_check.py:88-93` - 기본 제한 조건 설정
---

## 📚 참고 자료

### 커밋 이력
- `a29ef07`: fix: 교차검증 최적화 시 VALID 데이터에 제한 조건 적용 (2025-11-29)

### 업데이트 이력
- `_update.txt:1550-1556`: 최적화 기준값 제한 설정 추가 (2022-11-05)
- `_update.txt:235-241`: 최적화 기준값 제한 불만족 시 처리 개선 (2024-05-18)
---

**문서 버전**: 1.0
**최종 수정**: 2025-11-29
**작성자**: Claude (AI Assistant)
