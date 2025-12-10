# 텔레그램 추가 차트 시스템 분석 문서 (v2.0)

**문서 버전**: v2.0 (강화된 분석 기능 포함)
**작성일**: 2025-12-10
**대상 브랜치**: `feature/backtesting_result_update`
**관련 파일**:
- `backtester/back_static.py` - 메인 분석 호출
- `backtester/back_analysis_enhanced.py` - 강화된 분석 모듈 (NEW)

---

## 1. 개요

### 1.1 목적

백테스팅 결과에서 매수/매도 시점의 상세 시장 데이터를 분석하여 다음 정보를 텔레그램으로 전송합니다:

1. **기본 분석 차트**: 시간대별, 등락율별, 체결강도별 수익 분포 시각화
2. **강화된 필터 분석**: 통계적 유의성 검증 + 효과 크기 측정 (NEW)
3. **필터 조합 분석**: 다중 필터 시너지 효과 분석 (NEW)
4. **ML 특성 중요도**: Decision Tree 기반 변수 중요도 (NEW)
5. **동적 임계값 탐색**: 최적 필터 임계값 자동 탐색 (NEW)
6. **필터 안정성 검증**: 기간별 일관성 분석 (NEW)
7. **조건식 코드 생성**: 실제 적용 가능한 코드 자동 생성 (NEW)

### 1.2 v2.0 주요 개선 사항

| 영역 | v1.0 | v2.0 |
|------|------|------|
| **필터 분석** | 단일 필터만 분석 | 필터 조합 시너지 분석 |
| **통계 검증** | 없음 | t-test, Cohen's d, 신뢰구간 |
| **특성 분석** | 상관관계만 | ML 기반 특성 중요도 |
| **임계값** | 고정값 | 동적 최적값 탐색 |
| **안정성** | 없음 | 기간별 일관성 검증 |
| **코드 생성** | 없음 | 조건식 자동 생성 |
| **파생 지표** | 10개 | 20개 (모멘텀, 거래품질 등) |

### 1.3 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                     백테스팅 엔진 (BackEngine)                        │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  CalculationEyun()                                          │    │
│  │  • 매수 시점 시장 데이터 수집 (20개 컬럼)                      │    │
│  │  • 매도 시점 시장 데이터 수집 (16개 컬럼)                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      결과 처리 (back_static.py)                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  PltShow()                                                  │    │
│  │  └─→ RunEnhancedAnalysis() [NEW - back_analysis_enhanced.py]│    │
│  │       │                                                     │    │
│  │       ├─→ CalculateEnhancedDerivedMetrics()                │    │
│  │       │   • 모멘텀 점수, 거래품질 점수 등 20개 파생 지표      │    │
│  │       │                                                     │    │
│  │       ├─→ AnalyzeFilterEffectsEnhanced()                   │    │
│  │       │   • t-test, Cohen's d, 95% 신뢰구간                 │    │
│  │       │                                                     │    │
│  │       ├─→ FindAllOptimalThresholds()                       │    │
│  │       │   • 분위수 기반 최적 임계값 탐색                      │    │
│  │       │                                                     │    │
│  │       ├─→ AnalyzeFilterCombinations()                      │    │
│  │       │   • 2-3개 필터 조합 시너지 분석                      │    │
│  │       │                                                     │    │
│  │       ├─→ AnalyzeFeatureImportance()                       │    │
│  │       │   • Decision Tree 기반 Gini 중요도                  │    │
│  │       │                                                     │    │
│  │       ├─→ AnalyzeFilterStability()                         │    │
│  │       │   • 5개 기간 분할 일관성 검증                        │    │
│  │       │                                                     │    │
│  │       ├─→ GenerateFilterCode()                             │    │
│  │       │   • 조건식 코드 자동 생성                            │    │
│  │       │                                                     │    │
│  │       └─→ PltEnhancedAnalysisCharts()                      │    │
│  │           • 14개 강화된 시각화 차트                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       텔레그램 전송 (teleQ)                          │
│  • 이미지 1: {전략명}.png              (기본 수익곡선)               │
│  • 이미지 2: {전략명}_.png             (부가정보)                    │
│  • 이미지 3: {전략명}_enhanced.png     (강화된 분석 - 14개 차트) NEW │
│  • 텍스트: 통계적 유의 필터 추천                                     │
│  • 텍스트: 조합 필터 추천                                            │
│  • 텍스트: 자동 생성 조건식 코드                                     │
│  • CSV 5개: 상세분석, 필터분석, 임계값, 조합, 안정성                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 강화된 파생 지표 (CalculateEnhancedDerivedMetrics)

### 2.1 함수 개요

파일: `backtester/back_analysis_enhanced.py`

```python
def CalculateEnhancedDerivedMetrics(df_tsg):
    """
    강화된 파생 지표를 계산합니다.

    기존 10개 + 신규 10개 = 총 20개 파생 지표
    """
```

### 2.2 신규 파생 지표

#### 모멘텀 점수 (NEW)

```python
# 등락율과 체결강도를 정규화하여 모멘텀 점수 계산
등락율_norm = (df['매수등락율'] - df['매수등락율'].mean()) / df['매수등락율'].std()
체결강도_norm = (df['매수체결강도'] - 100) / 50  # 100을 기준으로 정규화
df['모멘텀점수'] = round((등락율_norm * 0.4 + 체결강도_norm * 0.6) * 10, 2)
```

**해석**:
- 양수: 상승 모멘텀
- 음수: 하락 모멘텀
- 절대값이 클수록 강한 모멘텀

#### 변동성 지표 (NEW)

```python
df['매수변동폭비율'] = (df['매수고가'] - df['매수저가']) / df['매수저가'] * 100
df['매도변동폭비율'] = (df['매도고가'] - df['매도저가']) / df['매도저가'] * 100
df['변동성변화'] = df['매도변동폭비율'] - df['매수변동폭비율']
```

**해석**:
- 양수: 보유 중 변동성 증가 (위험 증가)
- 음수: 보유 중 변동성 감소 (안정화)

#### 거래 품질 점수 (NEW)

```python
df['거래품질점수'] = 50  # 기본값

# 긍정적 요소 가산
df.loc[df['매수체결강도'] >= 120, '거래품질점수'] += 10
df.loc[df['매수체결강도'] >= 150, '거래품질점수'] += 10
df.loc[df['매수호가잔량비'] >= 100, '거래품질점수'] += 10
df.loc[(df['시가총액'] >= 1000) & (df['시가총액'] <= 10000), '거래품질점수'] += 10

# 부정적 요소 감산
df.loc[df['매수등락율'] >= 25, '거래품질점수'] -= 15
df.loc[df['매수등락율'] >= 30, '거래품질점수'] -= 10
df.loc[df['매수스프레드'] >= 0.5, '거래품질점수'] -= 10

df['거래품질점수'] = df['거래품질점수'].clip(0, 100)
```

**해석**:
- 0-30점: 낮은 품질 (피해야 할 거래)
- 30-50점: 보통 품질
- 50-70점: 좋은 품질
- 70-100점: 우수한 품질

#### 리스크 조정 수익률 (NEW)

```python
# 수익률을 위험 요소로 나누어 조정
risk_factor = (df['매수등락율'].abs() / 10 + df['보유시간'] / 300 + 1)
df['리스크조정수익률'] = round(df['수익률'] / risk_factor, 4)
```

**해석**:
- 같은 수익률이라도 위험이 낮을수록 높은 값
- Sharpe Ratio와 유사한 개념

#### 시간대 타이밍 점수 (NEW)

```python
# 시간대별 평균 수익률 기반 타이밍 점수
hour_profit = df.groupby('매수시')['수익률'].mean()
df['시간대평균수익률'] = df['매수시'].map(hour_profit)
df['타이밍점수'] = (df['시간대평균수익률'] - mean) / std * 10
```

**해석**:
- 양수: 유리한 시간대에 매수
- 음수: 불리한 시간대에 매수

### 2.3 전체 파생 지표 목록

| 번호 | 지표명 | 유형 | 설명 |
|------|--------|------|------|
| 1 | 등락율변화 | 변화량 | 매도등락율 - 매수등락율 |
| 2 | 체결강도변화 | 변화량 | 매도체결강도 - 매수체결강도 |
| 3 | 전일비변화 | 변화량 | 매도전일비 - 매수전일비 |
| 4 | 회전율변화 | 변화량 | 매도회전율 - 매수회전율 |
| 5 | 호가잔량비변화 | 변화량 | 매도호가잔량비 - 매수호가잔량비 |
| 6 | 거래대금변화율 | 변화율 | 매도거래대금 / 매수거래대금 |
| 7 | 체결강도변화율 | 변화율 | 매도체결강도 / 매수체결강도 |
| 8 | 등락추세 | 범주형 | 상승/하락/유지 |
| 9 | 체결강도추세 | 범주형 | 강화/약화/유지 |
| 10 | 거래량추세 | 범주형 | 증가/감소/유지 |
| 11 | 급락신호 | 불리언 | 등락율↓3% AND 체결강도↓20 |
| 12 | 매도세증가 | 불리언 | 호가잔량비↓0.2 |
| 13 | 거래량급감 | 불리언 | 거래대금변화율 < 0.5 |
| 14 | 위험도점수 | 0-100점 | 종합 위험 점수 (강화됨) |
| 15 | **모멘텀점수** | 연속값 | 등락율+체결강도 정규화 (NEW) |
| 16 | **매수변동폭비율** | % | 고가-저가 비율 (NEW) |
| 17 | **변동성변화** | % | 매도-매수 변동성 차이 (NEW) |
| 18 | **타이밍점수** | 연속값 | 시간대별 수익률 기반 (NEW) |
| 19 | **리스크조정수익률** | % | 위험조정 수익률 (NEW) |
| 20 | **거래품질점수** | 0-100점 | 종합 품질 점수 (NEW) |

---

## 3. 통계적 유의성 검증 (CalculateStatisticalSignificance)

### 3.1 함수 개요

파일: `backtester/back_analysis_enhanced.py`

```python
def CalculateStatisticalSignificance(filtered_out, remaining):
    """
    필터 효과의 통계적 유의성을 계산합니다.

    Returns:
        dict: {
            't_stat': t-통계량,
            'p_value': p-값,
            'effect_size': Cohen's d,
            'confidence_interval': 95% 신뢰구간,
            'significant': p < 0.05 여부
        }
    """
```

### 3.2 통계 검정 방법

#### Welch's t-test

```python
# 두 그룹 (제외 거래 vs 남은 거래)의 수익금 차이 검정
t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)
```

**해석**:
- p < 0.05: 통계적으로 유의한 차이 존재
- p < 0.01: 매우 유의한 차이
- p >= 0.05: 우연에 의한 차이일 가능성

#### Cohen's d 효과 크기

```python
pooled_std = np.sqrt((np.var(group1) + np.var(group2)) / 2)
effect_size = (np.mean(group1) - np.mean(group2)) / pooled_std
```

**해석 기준**:

| 효과 크기 | Cohen's d | 의미 |
|-----------|-----------|------|
| 무시 | < 0.2 | 실질적 차이 없음 |
| 작음 | 0.2 - 0.5 | 작은 효과 |
| 중간 | 0.5 - 0.8 | 중간 효과 |
| 큼 | 0.8 - 1.2 | 큰 효과 |
| 매우 큼 | > 1.2 | 매우 큰 효과 |

#### 95% 신뢰구간

```python
mean_diff = np.mean(group1) - np.mean(group2)
se = np.sqrt(np.var(group1)/len(group1) + np.var(group2)/len(group2))
ci_low = mean_diff - 1.96 * se
ci_high = mean_diff + 1.96 * se
```

**해석**:
- 신뢰구간이 0을 포함하지 않으면 유의한 차이
- 구간이 좁을수록 추정 정확도 높음

### 3.3 권장 등급 개선

```python
# v2.0 개선된 권장 등급 로직
if improvement > total_profit * 0.15 and significant:
    rating = '★★★'  # 강력 추천 (유의하고 개선율 15% 이상)
elif improvement > total_profit * 0.05 and p_value < 0.1:
    rating = '★★'   # 추천 (약간 유의하고 개선율 5% 이상)
elif improvement > 0:
    rating = '★'    # 고려 (개선 있음)
else:
    rating = ''     # 비추천
```

---

## 4. 동적 최적 임계값 탐색 (FindOptimalThresholds)

### 4.1 함수 개요

```python
def FindOptimalThresholds(df_tsg, column, direction='less', n_splits=20):
    """
    특정 컬럼에 대해 최적의 필터 임계값을 탐색합니다.

    Args:
        column: 분석할 컬럼 (예: '매수등락율')
        direction: 'less' (미만 제외) 또는 'greater' (이상 제외)
        n_splits: 분할 수 (기본 20개 분위수)

    Returns:
        최적 임계값 및 효과 정보
    """
```

### 4.2 알고리즘

```python
# 1. 분위수 기반 임계값 생성 (5% ~ 95%)
percentiles = np.linspace(5, 95, n_splits)
thresholds = np.percentile(values, percentiles)

# 2. 각 임계값에 대해 수익 개선 효과 계산
for threshold in thresholds:
    if direction == 'less':
        condition = df_tsg[column] < threshold
    else:
        condition = df_tsg[column] >= threshold

    improvement = -filtered_out['수익금'].sum()
    efficiency = improvement / len(filtered_out)  # 거래당 효율

# 3. 최적 임계값 선택 (제외비율 50% 이하에서 효율 최대)
best = df_valid[df_valid['efficiency'] == df_valid['efficiency'].max()]
```

### 4.3 분석 대상 컬럼

```python
columns_config = [
    ('매수등락율', 'greater', '등락율 {:.0f}% 이상 제외'),
    ('매수등락율', 'less', '등락율 {:.0f}% 미만 제외'),
    ('매수체결강도', 'less', '체결강도 {:.0f} 미만 제외'),
    ('매수체결강도', 'greater', '체결강도 {:.0f} 이상 제외'),
    ('매수당일거래대금', 'less', '거래대금 {:.0f}억 미만 제외'),
    ('시가총액', 'less', '시가총액 {:.0f}억 미만 제외'),
    ('시가총액', 'greater', '시가총액 {:.0f}억 이상 제외'),
    ('보유시간', 'less', '보유시간 {:.0f}초 미만 제외'),
    ('보유시간', 'greater', '보유시간 {:.0f}초 이상 제외'),
    ('매수호가잔량비', 'less', '호가잔량비 {:.0f}% 미만 제외'),
    ('매수스프레드', 'greater', '스프레드 {:.2f}% 이상 제외'),
    ('위험도점수', 'greater', '위험도 {:.0f}점 이상 제외'),
    ('거래품질점수', 'less', '거래품질 {:.0f}점 미만 제외'),
]
```

### 4.4 출력 예시

```csv
column,direction,optimal_threshold,improvement,excluded_ratio,efficiency
매수등락율,greater,22.5,1250000,8.5,147059
매수체결강도,less,85,890000,6.2,143548
시가총액,less,850,720000,5.8,124138
```

---

## 5. 필터 조합 분석 (AnalyzeFilterCombinations)

### 5.1 함수 개요

```python
def AnalyzeFilterCombinations(df_tsg, max_filters=3, top_n=10):
    """
    필터 조합의 시너지 효과를 분석합니다.

    시너지 = 조합 개선 - 개별 개선 합
    - 양수 시너지: 조합이 개별보다 효과적
    - 음수 시너지: 중복 효과로 비효율
    """
```

### 5.2 시너지 효과 계산

```python
# OR 조건으로 조합 (둘 중 하나라도 해당되면 제외)
combined_condition = cond1 | cond2

filtered_out = df_tsg[combined_condition]
improvement = -filtered_out['수익금'].sum()

# 시너지 = 조합 효과 - 개별 효과 합
individual_sum = filter1['improvement'] + filter2['improvement']
synergy = improvement - individual_sum
synergy_ratio = synergy / individual_sum * 100
```

### 5.3 해석

| 시너지 비율 | 의미 | 권장 |
|-------------|------|------|
| > 20% | 강한 시너지 (상호 보완) | ★★★ |
| 0 ~ 20% | 약한 시너지 | ★★ |
| < 0% | 중복 효과 (비효율) | 비추천 |

### 5.4 출력 예시

```csv
조합유형,필터1,필터2,개별개선합,조합개선,시너지효과,시너지비율,권장
2개 조합,등락율 25% 이상 제외,체결강도 80 미만 제외,1250000,1580000,330000,26.4%,★★★
2개 조합,시간대 14시 제외,보유시간 30초 미만 제외,890000,920000,30000,3.4%,★★
```

---

## 6. ML 특성 중요도 (AnalyzeFeatureImportance)

### 6.1 함수 개요

```python
def AnalyzeFeatureImportance(df_tsg):
    """
    Decision Tree를 사용하여 특성 중요도를 분석합니다.

    Returns:
        feature_importance: Gini 중요도 순위
        decision_rules: 주요 분기 규칙
        model_accuracy: 모델 정확도
    """
```

### 6.2 알고리즘

```python
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler

# 특성 선택
feature_columns = [
    '매수등락율', '매수체결강도', '매수당일거래대금', '매수전일비',
    '매수회전율', '시가총액', '보유시간', '매수호가잔량비'
]

# 타겟: 이익 여부 (이진 분류)
y = (df_tsg['수익금'] > 0).astype(int)

# Decision Tree 학습
clf = DecisionTreeClassifier(max_depth=4, min_samples_leaf=10)
clf.fit(X_scaled, y)

# Gini 중요도 추출
importance = dict(zip(feature_columns, clf.feature_importances_))
```

### 6.3 분기 규칙 추출

```python
# 상위 2레벨의 분기 규칙 추출
rules = [{
    'feature': '매수등락율',
    'threshold': 18.5,
    'left_win_rate': 62.3,   # 18.5% 미만
    'right_win_rate': 41.2,  # 18.5% 이상
    'rule': '매수등락율 < 18.5: 승률 62.3%'
}]
```

### 6.4 출력 예시

```
=== ML 특성 중요도 (정확도: 65.2%) ===

1. 매수등락율     : 0.285 ████████████████████
2. 매수체결강도   : 0.198 ██████████████
3. 보유시간       : 0.156 ███████████
4. 시가총액       : 0.142 ██████████
5. 매수당일거래대금: 0.089 ██████
```

---

## 7. 필터 안정성 검증 (AnalyzeFilterStability)

### 7.1 함수 개요

```python
def AnalyzeFilterStability(df_tsg, n_periods=5):
    """
    필터 효과의 시간적 안정성을 검증합니다.

    Args:
        n_periods: 분할 기간 수 (기본 5개)

    Returns:
        일관성 점수 및 안정성 등급
    """
```

### 7.2 안정성 점수 계산

```python
# 5개 기간으로 분할하여 각 기간별 필터 효과 계산
for period_df in periods:
    improvement = -filtered_out['수익금'].sum()
    period_improvements.append(improvement)

# 일관성 점수 계산
positive_periods = sum(1 for x in improvements if x > 0)
consistency_score = (positive_periods / n_periods) * 50

# 변동계수 반영
if mean_improvement > 0:
    cv = std_improvement / mean_improvement
    consistency_score += max(0, 50 - cv * 50)
```

### 7.3 안정성 등급

| 일관성 점수 | 등급 | 의미 |
|-------------|------|------|
| >= 70 | 안정 | 모든 기간에서 일관된 효과 |
| 40-70 | 보통 | 대부분 기간에서 효과 있음 |
| < 40 | 불안정 | 기간별 변동 큼 (신뢰도 낮음) |

### 7.4 출력 예시

```csv
분류,필터명,평균개선,표준편차,양수기간수,일관성점수,안정성등급
등락율,매수등락율 >= 20,285000,42000,5,82.5,안정
체결강도,매수체결강도 < 80,180000,95000,4,58.3,보통
보유시간,보유시간 < 60,120000,180000,3,35.2,불안정
```

---

## 8. 조건식 코드 자동 생성 (GenerateFilterCode)

### 8.1 함수 개요

```python
def GenerateFilterCode(filter_results, top_n=5):
    """
    필터 분석 결과를 실제 적용 가능한 조건식 코드로 변환합니다.

    Returns:
        code_text: 주석 포함 코드 텍스트
        buy_conditions: 매수 조건 리스트
        individual_conditions: 개별 조건 상세
    """
```

### 8.2 생성 코드 예시

```python
# ===== 자동 생성된 필터 조건 (백테스팅 분석 기반) =====

# [등락율] 필터
# - 등락율 22% 이상 제외: 수익개선 1,250,000원, 제외율 8.5%

# [체결강도] 필터
# - 체결강도 85 미만 제외: 수익개선 890,000원, 제외율 6.2%

# [시가총액] 필터
# - 시가총액 850억 미만 제외: 수익개선 720,000원, 제외율 5.8%

# ===== 적용 예시 =====
# 기존 매수 조건에 다음 필터를 AND 조건으로 추가:
#
# if 기존매수조건
#     and 등락율 < 22
#     and 체결강도 >= 85
#     and 시가총액 >= 850
#     매수 = True
```

---

## 9. 강화된 시각화 차트 (PltEnhancedAnalysisCharts)

### 9.1 생성되는 14개 차트

| 위치 | 차트명 | 설명 |
|------|--------|------|
| gs[0,0:2] | 필터 효과 순위 | Top 10 필터 수평 막대 그래프 |
| gs[0,2] | 통계적 유의성 분포 | 유의/비유의 파이 차트 |
| gs[1,0] | ML 특성 중요도 | Gini 중요도 막대 그래프 |
| gs[1,1] | 효과 크기 분포 | Cohen's d 히스토그램 |
| gs[1,2] | 제외비율 vs 수익개선 | 트레이드오프 산점도 |
| gs[2,0] | 시간대별 수익금 | 시간대별 막대 그래프 |
| gs[2,1] | 등락율별 수익금 | 등락율 구간별 막대 그래프 |
| gs[2,2] | 체결강도별 수익금 | 체결강도 구간별 막대 그래프 |
| gs[3,0] | **거래품질 점수별** | 품질 점수 구간별 (NEW) |
| gs[3,1] | **위험도 점수별** | 위험도 구간별 (ENHANCED) |
| gs[3,2] | **리스크조정수익률 분포** | 분포 히스토그램 (NEW) |
| gs[4,0] | 상관관계 히트맵 | 변수간 상관계수 |
| gs[4,1] | 손실/이익 특성 비교 | 그룹별 평균 비교 |
| gs[4,2] | 분석 요약 | 텍스트 요약 정보 |

### 9.2 출력 파일

```
파일: backtester/graph/{전략명}_enhanced.png
크기: 20x24 인치 (2400x2880 픽셀)
해상도: 120 DPI
```

---

## 10. CSV 출력 파일

### 10.1 생성되는 5개 CSV 파일

| 파일명 | 내용 | 행 수 |
|--------|------|-------|
| `{전략명}_enhanced_detail.csv` | 전체 거래 상세 + 20개 파생지표 | 거래 수 |
| `{전략명}_filter_analysis.csv` | 강화된 필터 분석 (통계 포함) | 필터 수 |
| `{전략명}_optimal_thresholds.csv` | 최적 임계값 탐색 결과 | 컬럼 수 × 2 |
| `{전략명}_filter_combinations.csv` | 필터 조합 시너지 분석 | 조합 수 |
| `{전략명}_filter_stability.csv` | 기간별 필터 안정성 | 주요 필터 수 |

### 10.2 filter_analysis.csv 컬럼

```csv
분류,필터명,조건식,적용코드,제외거래수,제외비율,제외거래수익금,
제외평균수익률,잔여거래수,잔여거래수익금,잔여평균수익률,수익개선금액,
제외거래승률,잔여거래승률,t통계량,p값,효과크기,효과해석,
신뢰구간,유의함,적용권장
```

---

## 11. 텔레그램 전송 내용

### 11.1 전송 순서 (v2.0)

1. **텍스트**: `"{전략명} {날짜} 완료."`
2. **이미지**: `{전략명}_.png` (부가정보 차트)
3. **이미지**: `{전략명}.png` (수익곡선 차트)
4. **이미지**: `{전략명}_enhanced.png` (강화된 분석 차트 - 14개) **NEW**
5. **텍스트**: 통계적 유의 필터 추천 **NEW**
6. **텍스트**: 조합 필터 추천 **NEW**
7. **텍스트**: 자동 생성 조건식 요약 **NEW**

### 11.2 메시지 예시 (v2.0)

```
📊 강화된 필터 분석 결과:

[통계적 유의] 등락율 22% 이상 제외: +1,250,000원 (p=0.008)
[통계적 유의] 체결강도 85 미만 제외: +890,000원 (p=0.023)
[조합추천] 등락율 22% 이상 + 체결강도 85 미만: 시너지 +330,000원
[안정성] 등락율 >= 20: 일관성 82.5점

💡 자동 생성 필터 코드:
총 3개 필터
예상 총 개선: 2,860,000원
```

---

## 12. 전략 개선 프로세스 (v2.0)

### 12.1 분석 기반 의사결정 흐름

```
1. 백테스팅 실행
     │
     ▼
2. 강화된 분석 결과 확인
     │
     ├── 📊 통계적 유의성 확인
     │    • p < 0.05 필터만 신뢰
     │    • 효과 크기 '중간' 이상 권장
     │
     ├── 🔗 필터 조합 시너지 확인
     │    • 시너지 비율 > 20% 조합 우선
     │    • 중복 효과 조합 피하기
     │
     ├── 📈 ML 특성 중요도 확인
     │    • 중요도 높은 변수 필터 우선
     │    • 분기 규칙 참고
     │
     ├── ⏱️ 필터 안정성 확인
     │    • '안정' 등급 필터만 적용
     │    • '불안정' 필터는 추가 검증
     │
     ▼
3. 자동 생성 코드 활용
     │
     ├── 조건식 복사/붙여넣기
     │
     ▼
4. 재백테스팅
     │
     ▼
5. 개선 효과 검증
```

### 12.2 신뢰도 높은 필터 선택 기준

**적용 추천 조건 (모두 충족 시)**:
- ✅ 통계적으로 유의함 (p < 0.05)
- ✅ 효과 크기 '중간' 이상 (Cohen's d > 0.5)
- ✅ 안정성 등급 '안정' (일관성 > 70)
- ✅ 제외 비율 30% 이하 (거래 기회 유지)
- ✅ 수익 개선 > 총수익 × 5%

---

## 13. 관련 파일 요약 (v2.0)

| 파일 | 함수/클래스 | 역할 |
|------|------------|------|
| `back_static.py` | `PltShow()` | 메인 차트 생성 + 강화 분석 호출 |
| `back_analysis_enhanced.py` | `CalculateEnhancedDerivedMetrics()` | 20개 파생 지표 계산 |
| `back_analysis_enhanced.py` | `CalculateStatisticalSignificance()` | t-test, Cohen's d |
| `back_analysis_enhanced.py` | `AnalyzeFilterEffectsEnhanced()` | 통계 포함 필터 분석 |
| `back_analysis_enhanced.py` | `FindOptimalThresholds()` | 최적 임계값 탐색 |
| `back_analysis_enhanced.py` | `FindAllOptimalThresholds()` | 모든 컬럼 임계값 탐색 |
| `back_analysis_enhanced.py` | `AnalyzeFilterCombinations()` | 필터 조합 시너지 |
| `back_analysis_enhanced.py` | `AnalyzeFeatureImportance()` | ML 특성 중요도 |
| `back_analysis_enhanced.py` | `AnalyzeFilterStability()` | 기간별 안정성 |
| `back_analysis_enhanced.py` | `GenerateFilterCode()` | 조건식 코드 생성 |
| `back_analysis_enhanced.py` | `PltEnhancedAnalysisCharts()` | 14개 강화 차트 |
| `back_analysis_enhanced.py` | `RunEnhancedAnalysis()` | 전체 강화 분석 실행 |

---

## 부록 A: 의존성 요구사항

```python
# 기본 (기존)
numpy
pandas
matplotlib

# 통계 (NEW)
scipy  # t-test, 정규분포

# 머신러닝 (NEW - 선택적)
scikit-learn  # DecisionTreeClassifier, StandardScaler
```

---

## 부록 B: 성능 고려사항

| 분석 단계 | 시간 복잡도 | 예상 시간 (1000거래) |
|-----------|-------------|---------------------|
| 파생 지표 계산 | O(n) | < 1초 |
| 단일 필터 분석 | O(n × m) | 2-3초 |
| 최적 임계값 탐색 | O(n × m × 20) | 5-10초 |
| 필터 조합 분석 | O(n × C(m,2)) | 10-20초 |
| ML 특성 중요도 | O(n × log n) | 2-3초 |
| 안정성 분석 | O(n × m × 5) | 5-10초 |
| 차트 생성 | O(n) | 3-5초 |
| **총 시간** | - | **약 30-50초** |

---

## 부록 C: 버전 히스토리

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| v1.0 | 2025-12-09 | 초기 문서 (기본 분석) |
| v2.0 | 2025-12-10 | 강화된 분석 기능 추가 |

---

*문서 끝*
