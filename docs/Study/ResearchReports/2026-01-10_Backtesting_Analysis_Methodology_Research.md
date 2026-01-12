# 백테스팅 결과 분석 방법론 연구

> **작성일**: 2026-01-10
> **버전**: 2.0 (고도화 및 확장)
> **목적**: 백테스팅 결과를 분석하여 우수한 조건식을 찾는 체계적 방법론 정립
> **관련 브랜치**: `feature/enhanced-buy-condition-generator`
> **작성자**: AI Assistant (Sisyphus)

---

## 목차

### Part I: 기초 방법론
1. [연구 배경 및 문제 인식](#1-연구-배경-및-문제-인식)
2. [기존 연구 요약 및 참조](#2-기존-연구-요약-및-참조)
3. [방법론 A: 시가총액만 분리 (고도화)](#3-방법론-a-시가총액만-분리-고도화)
4. [방법론 B: 필터 전용 접근 (고도화)](#4-방법론-b-필터-전용-접근-고도화)
5. [방법론 C: 새로운 조건식 발굴 (고도화)](#5-방법론-c-새로운-조건식-발굴-고도화)

### Part II: 혁신 방법론
6. [방법론 D: 손실 패턴 역분석](#6-방법론-d-손실-패턴-역분석)
7. [방법론 E: 시장 레짐 기반 접근](#7-방법론-e-시장-레짐-기반-접근)
8. [방법론 F: 클러스터링 기반 접근](#8-방법론-f-클러스터링-기반-접근)
9. [방법론 G: 변수 상호작용 분석](#9-방법론-g-변수-상호작용-분석)
10. [방법론 H: 적응형/동적 조건식](#10-방법론-h-적응형동적-조건식)

### Part III: 고급 방법론
11. [방법론 I: 인과 추론 기반](#11-방법론-i-인과-추론-기반)
12. [방법론 J: 앙상블 조건식](#12-방법론-j-앙상블-조건식)
13. [방법론 K: 강화학습 기반](#13-방법론-k-강화학습-기반)

### Part IV: 통합 및 적용
14. [방법론 비교 및 선택 가이드](#14-방법론-비교-및-선택-가이드)
15. [실무 적용 로드맵](#15-실무-적용-로드맵)
16. [결론 및 권장사항](#16-결론-및-권장사항)

---

# Part I: 기초 방법론

## 1. 연구 배경 및 문제 인식

### 1.1 문제 정의

기존 세그먼트 필터 분석의 구조적 한계가 발견되었습니다:

```
[세그먼트 필터의 예측-실제 괴리]

원본 백테스트: 5,087건 거래
예측 (필터 적용 시): 1,497건
실제 (필터 적용 후): 1,121건

괴리 원인: 포트폴리오 동적 효과
- 예측: 원본 거래만 분석
- 실제: 차단된 거래가 새로운 거래를 유발
- 결과: 예측과 실제가 구조적으로 다름
```

### 1.2 핵심 한계점

| 한계점 | 설명 | 영향 |
|--------|------|------|
| **포트폴리오 동적 효과** | 거래 차단 → 포트폴리오 변화 → 새 거래 발생 | 예측 불가능한 거래 출현 |
| **대체 매수 현상** | 09:30 차단 → 10:00에 새 거래 | 오히려 손실 증가 가능 |
| **시간대×시총 세그먼트 복잡도** | 20개 세그먼트 → 과적합 위험 | 실전 성능 저하 |
| **당일 재매수 차단 효과** | 차단 시점에 따라 결과 변동 | 예측 정확도 한계 |

### 1.3 연구 목표 (확장)

기존 세그먼트 필터의 한계를 인식하고, **다양한 관점**에서 조건식을 개선하는 방법론 정립:

**기초 방법론 (A-C)**: 세그먼트/필터 기반 개선
**혁신 방법론 (D-H)**: 새로운 분석 관점 도입
**고급 방법론 (I-K)**: AI/ML 기반 고도화

---

## 2. 기존 연구 요약 및 참조

### 2.1 참조 문서 맵

```
본 문서 (v2.0)
    │
    ├─→ [A] 세그먼트 필터 예측-실제 괴리 분석
    │       └─→ docs/Study/SystemAnalysis/20260108_Segment_Filter_Prediction_vs_Actual_Discrepancy_Analysis.md
    │           • 괴리 원인: 포트폴리오 동적 효과
    │           • 대체 매수 현상 발견
    │           • 결론: 세그먼트 필터는 "참고용"
    │
    ├─→ [B] 세그먼트 필터 최적화 연구
    │       └─→ docs/Study/ResearchReports/2025-12-20_Segmented_Filter_Optimization_Research.md
    │           • 시가총액×시간 구간 분할 전략
    │           • 2단계 계층적 최적화 (Greedy + Beam Search)
    │           • Walk-Forward 검증 구현
    │           • 다목적 최적화 (NSGA-II)
    │
    ├─→ [C] 오버피팅 위험 평가 연구
    │       └─→ docs/Study/ResearchReports/2025-12-29_Overfitting_Risk_Assessment_Filter_Segment_Analysis.md
    │           • 6가지 오버피팅 판단 지표
    │           • 다중 비교 보정 (Bonferroni, FDR)
    │           • Walk-Forward Analysis 권장
    │           • 제외율 상한 50% 권장
    │
    └─→ [D] AI/ML 기반 조건식 발굴 연구
            └─→ docs/Study/ResearchReports/Research_Report_Automated_Condition_Finding.md
                • Feature Importance (XGBoost, SHAP)
                • Genetic Programming (DEAP)
                • LLM 기반 조건식 생성
                • Bayesian Optimization (Optuna)
```

### 2.2 핵심 교훈 정리

| 교훈 | 내용 | 시사점 |
|------|------|--------|
| **세그먼트 분할 ≠ 정확도** | 예측-실제 37% 오차 | 분할 수 최소화 |
| **제외율 상한 필요** | 70% 이상 → 오버피팅 | 50% 이하 유지 |
| **복잡도 vs 성능** | 필터 7개 → 실전 -1.2% | 단순 전략 우선 |
| **Walk-Forward 필수** | 저하율 40% 초과 → 위험 | 모든 방법론에 적용 |

---

## 3. 방법론 A: 시가총액만 분리 (고도화)

### 3.1 핵심 개념

**기본 아이디어**: 시간대 분리를 제거하고 시가총액만으로 세그먼트 단순화

```
기존 세그먼트: 시가총액(4) × 시간대(5) = 20개
방법론 A:     시가총액(3~4) × 시간대(1) = 3~4개
```

### 3.2 고도화: 동적 분위수 기반 구간 설정

**문제점**: 고정 시가총액 구간은 시장 상황 변화를 반영하지 못함

**해결책**: 데이터 분포 기반 동적 구간 설정

```python
# 고도화 A-1: 동적 분위수 기반 세그먼트

class DynamicMarketCapSegmenter:
    """
    데이터 분포 기반으로 시가총액 구간을 동적으로 설정
    """

    def __init__(self, n_segments=4, min_samples_per_segment=200):
        self.n_segments = n_segments
        self.min_samples = min_samples_per_segment
        self.boundaries = None

    def fit(self, df_detail):
        """Walk-Forward 각 구간의 Train 데이터로 구간 설정"""
        market_caps = df_detail['시가총액'].values

        # 균등 분위수로 초기 경계 설정
        quantiles = np.linspace(0, 1, self.n_segments + 1)
        self.boundaries = np.percentile(market_caps, quantiles * 100)

        # 최소 샘플 수 확보를 위한 구간 병합
        self._merge_small_segments(df_detail)

        return self

    def _merge_small_segments(self, df_detail):
        """샘플 부족 세그먼트 자동 병합"""
        while True:
            segment_sizes = self._count_segments(df_detail)
            small_segments = [i for i, size in enumerate(segment_sizes)
                              if size < self.min_samples]

            if not small_segments:
                break

            # 가장 작은 세그먼트를 인접 세그먼트와 병합
            idx = small_segments[0]
            self._merge_adjacent(idx)

    def transform(self, df_detail):
        """시가총액 기반 세그먼트 라벨 할당"""
        labels = pd.cut(
            df_detail['시가총액'],
            bins=self.boundaries,
            labels=[f'S{i+1}' for i in range(len(self.boundaries)-1)]
        )
        return labels

    def get_segment_report(self, df_detail):
        """세그먼트별 통계 리포트"""
        labels = self.transform(df_detail)

        report = []
        for seg in labels.unique():
            seg_data = df_detail[labels == seg]
            report.append({
                'segment': seg,
                'count': len(seg_data),
                'cap_min': seg_data['시가총액'].min(),
                'cap_max': seg_data['시가총액'].max(),
                'profit_sum': seg_data['수익금'].sum(),
                'win_rate': (seg_data['수익금'] > 0).mean()
            })

        return pd.DataFrame(report)
```

### 3.3 고도화: 계층적 필터 선택

**문제점**: 세그먼트별로 독립적으로 필터를 선택하면 일관성 부족

**해결책**: 전체 → 세그먼트 순으로 계층적 필터 선택

```python
# 고도화 A-2: 계층적 필터 선택

def hierarchical_filter_selection(df_detail, segments, max_global=2, max_local=1):
    """
    계층적 필터 선택:
    1. 전체 데이터에서 유효한 "글로벌 필터" 선택
    2. 각 세그먼트에서 추가 "로컬 필터" 선택

    장점:
    - 전체적으로 유효한 필터 보장
    - 세그먼트별 추가 최적화
    - 복잡도 제한 (최대 3개 필터)
    """

    # Step 1: 글로벌 필터 선택 (전체 데이터)
    global_filters = evaluate_filters(
        df_detail,
        max_exclusion=0.3,  # 전체 제외율 30% 이하
        top_k=max_global
    )

    # 글로벌 필터 적용
    global_mask = apply_filters(df_detail, global_filters)
    df_filtered = df_detail[global_mask]

    # Step 2: 세그먼트별 로컬 필터 선택
    local_filters = {}

    for seg_name, seg_mask in segments.items():
        seg_data = df_filtered[seg_mask]

        if len(seg_data) < 200:
            local_filters[seg_name] = []
            continue

        # 글로벌 필터와 중복되지 않는 필터만 선택
        seg_filters = evaluate_filters(
            seg_data,
            max_exclusion=0.2,  # 세그먼트 내 추가 제외 20% 이하
            exclude_columns=[f['column'] for f in global_filters],
            top_k=max_local
        )

        local_filters[seg_name] = seg_filters

    return {
        'global': global_filters,
        'local': local_filters,
        'total_complexity': max_global + max_local  # 최대 3개
    }
```

### 3.4 고도화: 세그먼트 성과 균형 검증

```python
# 고도화 A-3: 세그먼트 성과 균형 검증

def validate_segment_balance(df_detail, segments, filters_result):
    """
    세그먼트 간 성과 균형 검증

    불균형 징후:
    - 특정 세그먼트에 수익 집중
    - 세그먼트 간 성과 편차 > 3배
    - 일부 세그먼트 음수 수익
    """

    results = {}

    for seg_name, seg_mask in segments.items():
        seg_data = df_detail[seg_mask]

        # 필터 적용
        global_mask = apply_filters(seg_data, filters_result['global'])
        local_mask = apply_filters(seg_data, filters_result['local'].get(seg_name, []))
        final_mask = global_mask & local_mask

        filtered_data = seg_data[final_mask]

        results[seg_name] = {
            'original_count': len(seg_data),
            'filtered_count': len(filtered_data),
            'original_profit': seg_data['수익금'].sum(),
            'filtered_profit': filtered_data['수익금'].sum(),
            'improvement': filtered_data['수익금'].sum() - seg_data['수익금'].sum()
        }

    # 균형 지표 계산
    improvements = [r['improvement'] for r in results.values()]
    max_improvement = max(improvements)
    min_improvement = min(improvements)

    balance_score = {
        'max_min_ratio': max_improvement / min_improvement if min_improvement > 0 else float('inf'),
        'std_improvement': np.std(improvements),
        'all_positive': all(imp > 0 for imp in improvements),
        'is_balanced': abs(max_improvement / min_improvement) < 3 if min_improvement != 0 else False
    }

    return results, balance_score
```

---

## 4. 방법론 B: 필터 전용 접근 (고도화)

### 4.1 핵심 개념

**기본 아이디어**: 세그먼트 분리 없이 전체 데이터에 필터만 적용

### 4.2 고도화: 필터 상호작용 분석

**문제점**: 개별 필터는 유효하지만 조합 시 시너지가 음수일 수 있음

**해결책**: 필터 간 상호작용 효과 사전 분석

```python
# 고도화 B-1: 필터 상호작용 매트릭스

def analyze_filter_interactions(df_detail, filter_candidates):
    """
    필터 간 상호작용 분석

    측정 지표:
    - 중복 제외율: 두 필터가 동일 거래를 제외하는 비율
    - 시너지 효과: (조합 개선) - (개별 개선 합)
    - 독립성 점수: 1 - 중복 제외율
    """

    n_filters = len(filter_candidates)

    # 각 필터의 제외 마스크 생성
    masks = {}
    for f in filter_candidates:
        masks[f['name']] = create_filter_mask(df_detail, f)

    # 상호작용 매트릭스
    interaction_matrix = np.zeros((n_filters, n_filters))
    synergy_matrix = np.zeros((n_filters, n_filters))

    for i, f1 in enumerate(filter_candidates):
        for j, f2 in enumerate(filter_candidates):
            if i >= j:
                continue

            mask1 = masks[f1['name']]
            mask2 = masks[f2['name']]

            # 중복 제외율 (Jaccard 유사도)
            excluded_both = (~mask1) & (~mask2)
            excluded_any = (~mask1) | (~mask2)
            overlap = excluded_both.sum() / excluded_any.sum() if excluded_any.sum() > 0 else 0

            interaction_matrix[i, j] = overlap
            interaction_matrix[j, i] = overlap

            # 시너지 효과
            individual_imp = (
                df_detail[mask1]['수익금'].sum() - df_detail['수익금'].sum() +
                df_detail[mask2]['수익금'].sum() - df_detail['수익금'].sum()
            )
            combined_mask = mask1 & mask2
            combined_imp = df_detail[combined_mask]['수익금'].sum() - df_detail['수익금'].sum()
            synergy = combined_imp - individual_imp

            synergy_matrix[i, j] = synergy
            synergy_matrix[j, i] = synergy

    return {
        'overlap_matrix': interaction_matrix,
        'synergy_matrix': synergy_matrix,
        'best_combinations': find_best_combinations(synergy_matrix, filter_candidates)
    }

def find_best_combinations(synergy_matrix, filters, max_filters=3):
    """시너지가 양수인 최적 조합 탐색"""
    from itertools import combinations

    best_combos = []

    for r in range(2, max_filters + 1):
        for combo in combinations(range(len(filters)), r):
            total_synergy = sum(
                synergy_matrix[i, j]
                for i, j in combinations(combo, 2)
            )

            if total_synergy > 0:
                best_combos.append({
                    'filters': [filters[i]['name'] for i in combo],
                    'synergy': total_synergy
                })

    return sorted(best_combos, key=lambda x: x['synergy'], reverse=True)[:5]
```

### 4.3 고도화: VIF (Variance Inflation Factor) 검증

**문제점**: 유사한 필터를 중복 적용하면 효과가 중복됨

**해결책**: 다중공선성 검사로 독립적인 필터만 선택

```python
# 고도화 B-2: VIF 기반 필터 독립성 검증

from statsmodels.stats.outliers_influence import variance_inflation_factor

def validate_filter_independence(df_detail, filter_columns, max_vif=5.0):
    """
    VIF(Variance Inflation Factor)를 사용한 필터 독립성 검증

    VIF 해석:
    - VIF < 5: 독립적 (사용 가능)
    - 5 <= VIF < 10: 중복 가능성 (주의)
    - VIF >= 10: 심각한 중복 (제거 필요)
    """

    # 필터 관련 컬럼만 추출
    X = df_detail[filter_columns].copy()
    X = X.fillna(0)

    # 표준화
    X = (X - X.mean()) / X.std()

    # VIF 계산
    vif_data = []
    for i, col in enumerate(filter_columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data.append({
            'column': col,
            'vif': vif,
            'status': 'OK' if vif < 5 else 'WARNING' if vif < 10 else 'REMOVE'
        })

    # 높은 VIF 필터 순차 제거
    selected_columns = filter_columns.copy()

    while True:
        vif_values = [
            variance_inflation_factor(X[selected_columns].values, i)
            for i in range(len(selected_columns))
        ]

        max_vif_idx = np.argmax(vif_values)

        if vif_values[max_vif_idx] <= max_vif:
            break

        removed = selected_columns.pop(max_vif_idx)
        print(f"Removed {removed} (VIF={vif_values[max_vif_idx]:.2f})")

    return {
        'vif_report': pd.DataFrame(vif_data),
        'selected_columns': selected_columns,
        'removed_columns': list(set(filter_columns) - set(selected_columns))
    }
```

### 4.4 고도화: 필터 효율 지표

**문제점**: 단순히 개선 금액만으로 필터를 평가하면 제외율을 무시함

**해결책**: 효율 지표 = 개선금액 / 제외율

```python
# 고도화 B-3: 필터 효율 지표

def calculate_filter_efficiency(df_detail, filters):
    """
    필터 효율 지표 계산

    효율 = 개선금액 / 제외율

    해석:
    - 효율 높음: 적은 거래 제외로 큰 개선
    - 효율 낮음: 많은 거래 제외로 작은 개선
    """

    results = []

    for f in filters:
        mask = create_filter_mask(df_detail, f)

        excluded = (~mask).sum() / len(df_detail)
        improvement = df_detail[mask]['수익금'].sum() - df_detail['수익금'].sum()

        # 효율 지표들
        efficiency_per_exclusion = improvement / excluded if excluded > 0 else 0
        improvement_ratio = improvement / abs(df_detail['수익금'].sum()) if df_detail['수익금'].sum() != 0 else 0

        # Sharpe-like ratio: 평균 개선 / 개선 변동성
        remaining_profits = df_detail[mask]['수익금']
        excluded_profits = df_detail[~mask]['수익금']
        sharpe_like = (remaining_profits.mean() - excluded_profits.mean()) / remaining_profits.std() if remaining_profits.std() > 0 else 0

        results.append({
            'filter': f['name'],
            'improvement': improvement,
            'exclusion_rate': excluded,
            'efficiency': efficiency_per_exclusion,
            'improvement_ratio': improvement_ratio,
            'sharpe_like': sharpe_like,
            'composite_score': (
                0.4 * (improvement / 1e9) +  # 개선금액 (10억 단위)
                0.3 * (1 - excluded) +       # 잔여율
                0.3 * sharpe_like            # Sharpe-like
            )
        })

    return pd.DataFrame(results).sort_values('composite_score', ascending=False)
```

---

## 5. 방법론 C: 새로운 조건식 발굴 (고도화)

### 5.1 핵심 개념

**기본 아이디어**: 기존 조건식 개선이 아닌, 완전히 새로운 조건식 발굴

### 5.2 고도화: 다중 모델 앙상블 Feature Importance

**문제점**: 단일 모델의 Feature Importance는 모델에 따라 다름

**해결책**: 여러 모델의 결과를 종합

```python
# 고도화 C-1: 앙상블 Feature Importance

def ensemble_feature_importance(df_detail, feature_cols, target='수익여부'):
    """
    여러 모델의 Feature Importance를 종합

    사용 모델:
    1. XGBoost (트리 기반)
    2. LightGBM (트리 기반)
    3. Random Forest (트리 기반)
    4. Logistic Regression (선형)
    5. Permutation Importance (모델 무관)
    """

    from xgboost import XGBClassifier
    from lightgbm import LGBMClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.inspection import permutation_importance
    from sklearn.preprocessing import StandardScaler

    # 데이터 준비
    X = df_detail[feature_cols].fillna(0)
    y = (df_detail['수익금'] > 0).astype(int)

    # 표준화 (Logistic Regression용)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    importance_results = {}

    # 1. XGBoost
    xgb = XGBClassifier(n_estimators=100, max_depth=5, random_state=42)
    xgb.fit(X, y)
    importance_results['xgboost'] = dict(zip(feature_cols, xgb.feature_importances_))

    # 2. LightGBM
    lgbm = LGBMClassifier(n_estimators=100, max_depth=5, random_state=42, verbose=-1)
    lgbm.fit(X, y)
    importance_results['lightgbm'] = dict(zip(feature_cols, lgbm.feature_importances_))

    # 3. Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    rf.fit(X, y)
    importance_results['random_forest'] = dict(zip(feature_cols, rf.feature_importances_))

    # 4. Logistic Regression (절대값 계수)
    lr = LogisticRegression(random_state=42, max_iter=1000)
    lr.fit(X_scaled, y)
    importance_results['logistic'] = dict(zip(feature_cols, np.abs(lr.coef_[0])))

    # 5. Permutation Importance (XGBoost 기준)
    perm_imp = permutation_importance(xgb, X, y, n_repeats=10, random_state=42)
    importance_results['permutation'] = dict(zip(feature_cols, perm_imp.importances_mean))

    # 종합 (Rank 기반 평균)
    ranks = {}
    for col in feature_cols:
        ranks[col] = []
        for method, imp_dict in importance_results.items():
            # 각 방법에서의 순위 계산
            sorted_features = sorted(imp_dict.keys(), key=lambda x: imp_dict[x], reverse=True)
            rank = sorted_features.index(col) + 1
            ranks[col].append(rank)

    # 평균 순위로 최종 순위 결정
    final_ranking = sorted(ranks.keys(), key=lambda x: np.mean(ranks[x]))

    return {
        'individual_importance': importance_results,
        'rank_by_feature': {col: np.mean(ranks[col]) for col in feature_cols},
        'final_ranking': final_ranking[:10],  # Top 10
        'consensus_features': [col for col in final_ranking[:5]]  # Top 5 (합의)
    }
```

### 5.3 고도화: 결정 트리 기반 자동 규칙 추출

**문제점**: Feature Importance는 중요 변수를 알려주지만 임계값은 알려주지 않음

**해결책**: 결정 트리에서 직접 규칙 추출

```python
# 고도화 C-2: 결정 트리 기반 규칙 추출

from sklearn.tree import DecisionTreeClassifier, export_text

def extract_rules_from_tree(df_detail, feature_cols, max_depth=4, min_samples_leaf=200):
    """
    결정 트리에서 거래 조건식 자동 추출

    장점:
    - 해석 가능한 if-then 규칙
    - 임계값 자동 결정
    - 과적합 방지 (max_depth 제한)
    """

    X = df_detail[feature_cols].fillna(0)
    y = (df_detail['수익금'] > 0).astype(int)

    # 얕은 결정 트리 학습
    tree = DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=42
    )
    tree.fit(X, y)

    # 텍스트 규칙 추출
    tree_rules = export_text(tree, feature_names=feature_cols)

    # 수익 거래 리프 노드 경로 추출
    profitable_paths = extract_profitable_paths(tree, X, y, feature_cols)

    # Python 조건식으로 변환
    conditions = []
    for path in profitable_paths:
        condition = ' and '.join([
            f"({node['feature']} {node['operator']} {node['threshold']:.4f})"
            for node in path['nodes']
        ])
        conditions.append({
            'condition': condition,
            'samples': path['samples'],
            'win_rate': path['win_rate'],
            'avg_profit': path['avg_profit']
        })

    return {
        'tree_rules_text': tree_rules,
        'profitable_conditions': conditions,
        'best_condition': max(conditions, key=lambda x: x['win_rate'] * x['samples']) if conditions else None
    }

def extract_profitable_paths(tree, X, y, feature_names):
    """결정 트리에서 수익 비율이 높은 경로 추출"""

    from sklearn.tree import _tree

    paths = []

    def recurse(node, path):
        if tree.tree_.feature[node] == _tree.TREE_UNDEFINED:
            # 리프 노드
            samples = tree.tree_.n_node_samples[node]
            class_counts = tree.tree_.value[node][0]
            win_rate = class_counts[1] / class_counts.sum()

            if win_rate > 0.5 and samples >= 100:  # 승률 50% 이상, 샘플 100건 이상
                paths.append({
                    'nodes': path.copy(),
                    'samples': samples,
                    'win_rate': win_rate,
                    'avg_profit': 0  # 추후 계산
                })
            return

        feature = feature_names[tree.tree_.feature[node]]
        threshold = tree.tree_.threshold[node]

        # 왼쪽 (<=)
        path.append({'feature': feature, 'operator': '<=', 'threshold': threshold})
        recurse(tree.tree_.children_left[node], path)
        path.pop()

        # 오른쪽 (>)
        path.append({'feature': feature, 'operator': '>', 'threshold': threshold})
        recurse(tree.tree_.children_right[node], path)
        path.pop()

    recurse(0, [])
    return paths
```

### 5.4 고도화: Symbolic Regression (더 해석 가능한 GP)

```python
# 고도화 C-3: Symbolic Regression

def symbolic_regression_condition(df_detail, feature_cols, target_col='수익금'):
    """
    Symbolic Regression으로 수학적 조건식 발견

    예시 결과:
    수익금 ~ f(시가총액, 체결강도, 스프레드)
    """

    try:
        from gplearn.genetic import SymbolicRegressor
    except ImportError:
        print("gplearn 설치 필요: pip install gplearn")
        return None

    X = df_detail[feature_cols].fillna(0).values
    y = df_detail[target_col].values

    # Symbolic Regressor 설정
    est_gp = SymbolicRegressor(
        population_size=1000,
        generations=20,
        tournament_size=20,
        stopping_criteria=0.01,
        max_samples=0.9,
        parsimony_coefficient=0.01,  # 복잡도 페널티
        function_set=['add', 'sub', 'mul', 'div', 'sqrt', 'log', 'abs'],
        random_state=42,
        n_jobs=-1
    )

    est_gp.fit(X, y)

    return {
        'formula': str(est_gp._program),
        'score': est_gp.score(X, y),
        'complexity': len(est_gp._program)
    }
```

---

# Part II: 혁신 방법론

## 6. 방법론 D: 손실 패턴 역분석

### 6.1 핵심 개념

**역발상**: 수익 거래를 찾는 대신, **손실 거래의 패턴**을 먼저 파악하고 제외

```
기존 접근: 수익 거래 특성 → 매수 조건
방법론 D:  손실 거래 특성 → 제외 조건 → 남은 것이 매수
```

### 6.2 근거

**왜 손실 패턴이 더 명확할 수 있는가?**

1. **손실 거래는 공통 패턴이 더 명확**: 극단적인 변동성, 낮은 유동성, 과열 신호 등
2. **수익 거래는 다양한 이유로 성공**: 패턴화하기 어려움
3. **네거티브 스크리닝이 더 안정적**: "이것은 피해라"가 "이것을 사라"보다 명확

### 6.3 구현 설계

```python
# 방법론 D: 손실 패턴 역분석

class LossPatternAnalyzer:
    """
    손실 거래의 공통 패턴을 분석하여 제외 조건 도출
    """

    def __init__(self, loss_threshold=-100000):
        self.loss_threshold = loss_threshold  # 손실 거래 기준 (예: -10만원)

    def analyze(self, df_detail, feature_cols):
        """
        손실 거래 패턴 분석

        프로세스:
        1. 큰 손실 거래 식별
        2. 손실 거래의 공통 특성 추출
        3. 손실 패턴 클러스터링
        4. 각 클러스터의 제외 규칙 생성
        """

        # 손실 거래 vs 비손실 거래 분리
        is_loss = df_detail['수익금'] < self.loss_threshold
        loss_trades = df_detail[is_loss]
        other_trades = df_detail[~is_loss]

        # 통계적 차이 분석
        pattern_analysis = {}

        for col in feature_cols:
            loss_mean = loss_trades[col].mean()
            other_mean = other_trades[col].mean()

            # t-test
            from scipy.stats import ttest_ind
            stat, pval = ttest_ind(loss_trades[col].dropna(), other_trades[col].dropna())

            # 효과 크기 (Cohen's d)
            pooled_std = np.sqrt((loss_trades[col].var() + other_trades[col].var()) / 2)
            cohens_d = (loss_mean - other_mean) / pooled_std if pooled_std > 0 else 0

            pattern_analysis[col] = {
                'loss_mean': loss_mean,
                'other_mean': other_mean,
                'difference': loss_mean - other_mean,
                'p_value': pval,
                'cohens_d': cohens_d,
                'is_significant': pval < 0.01 and abs(cohens_d) > 0.3
            }

        # 유의미한 패턴만 추출
        significant_patterns = {
            col: data for col, data in pattern_analysis.items()
            if data['is_significant']
        }

        # 제외 규칙 생성
        exclusion_rules = self._generate_exclusion_rules(
            loss_trades, other_trades, significant_patterns
        )

        return {
            'loss_count': len(loss_trades),
            'loss_ratio': len(loss_trades) / len(df_detail),
            'total_loss': loss_trades['수익금'].sum(),
            'pattern_analysis': pattern_analysis,
            'significant_patterns': significant_patterns,
            'exclusion_rules': exclusion_rules
        }

    def _generate_exclusion_rules(self, loss_trades, other_trades, patterns):
        """유의미한 패턴에서 제외 규칙 생성"""

        rules = []

        for col, data in patterns.items():
            if data['difference'] > 0:
                # 손실 거래가 더 높은 값 → 상한 제한
                threshold = loss_trades[col].quantile(0.25)  # 손실 거래의 25% 분위수
                rules.append({
                    'column': col,
                    'operator': '<',
                    'threshold': threshold,
                    'rationale': f"손실 거래의 {col}이 평균적으로 높음"
                })
            else:
                # 손실 거래가 더 낮은 값 → 하한 제한
                threshold = loss_trades[col].quantile(0.75)  # 손실 거래의 75% 분위수
                rules.append({
                    'column': col,
                    'operator': '>',
                    'threshold': threshold,
                    'rationale': f"손실 거래의 {col}이 평균적으로 낮음"
                })

        return rules

    def validate_exclusion_rules(self, df_detail, rules):
        """제외 규칙의 효과 검증"""

        mask = pd.Series([True] * len(df_detail))

        for rule in rules:
            if rule['operator'] == '<':
                mask &= df_detail[rule['column']] < rule['threshold']
            else:
                mask &= df_detail[rule['column']] > rule['threshold']

        original_profit = df_detail['수익금'].sum()
        filtered_profit = df_detail[mask]['수익금'].sum()
        excluded_profit = df_detail[~mask]['수익금'].sum()

        return {
            'exclusion_rate': (~mask).sum() / len(df_detail),
            'original_profit': original_profit,
            'filtered_profit': filtered_profit,
            'excluded_profit': excluded_profit,
            'improvement': filtered_profit - original_profit,
            'rules_applied': len(rules)
        }
```

### 6.4 고급 기법: 극단 손실 클러스터링

```python
# 고도화 D-1: 극단 손실 클러스터 분석

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

def cluster_extreme_losses(df_detail, feature_cols, loss_percentile=10):
    """
    극단적 손실 거래를 클러스터링하여 패턴별 제외 규칙 생성

    장점:
    - 다양한 손실 패턴을 구분
    - 패턴별로 다른 제외 규칙 적용 가능
    - 드문 극단 사례도 포착
    """

    # 극단 손실 거래 추출
    threshold = df_detail['수익금'].quantile(loss_percentile / 100)
    extreme_losses = df_detail[df_detail['수익금'] <= threshold].copy()

    # 특성 스케일링
    X = extreme_losses[feature_cols].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # DBSCAN 클러스터링
    clustering = DBSCAN(eps=0.5, min_samples=50)
    extreme_losses['cluster'] = clustering.fit_predict(X_scaled)

    # 클러스터별 프로파일
    cluster_profiles = []

    for cluster_id in extreme_losses['cluster'].unique():
        if cluster_id == -1:  # 노이즈
            continue

        cluster_data = extreme_losses[extreme_losses['cluster'] == cluster_id]

        profile = {
            'cluster_id': cluster_id,
            'size': len(cluster_data),
            'total_loss': cluster_data['수익금'].sum(),
            'features': {}
        }

        for col in feature_cols:
            profile['features'][col] = {
                'mean': cluster_data[col].mean(),
                'std': cluster_data[col].std(),
                'q25': cluster_data[col].quantile(0.25),
                'q75': cluster_data[col].quantile(0.75)
            }

        cluster_profiles.append(profile)

    return {
        'n_clusters': len(cluster_profiles),
        'cluster_profiles': cluster_profiles,
        'noise_ratio': (extreme_losses['cluster'] == -1).mean()
    }
```

---

## 7. 방법론 E: 시장 레짐 기반 접근

### 7.1 핵심 개념

**핵심 아이디어**: 시장 상황(레짐)에 따라 다른 조건식 적용

```
시장 상황:
- 상승장 (Bull Market): 적극적 매수 조건
- 하락장 (Bear Market): 보수적 매수 조건 또는 매수 중단
- 횡보장 (Sideways): 특정 패턴에만 매수
```

### 7.2 근거

**왜 레짐별 조건이 필요한가?**

1. **같은 신호도 레짐에 따라 의미가 다름**: 상승장의 눌림목 vs 하락장의 눌림목
2. **최적 전략이 레짐마다 다름**: 상승장 추세추종 vs 횡보장 평균회귀
3. **리스크 관리 차별화**: 하락장에서는 더 보수적으로

### 7.3 구현 설계

```python
# 방법론 E: 시장 레짐 기반 접근

class MarketRegimeAnalyzer:
    """
    시장 레짐을 감지하고 레짐별 최적 조건을 분석
    """

    def __init__(self):
        self.regimes = ['bull', 'bear', 'sideways']

    def detect_regime(self, df_detail, lookback_days=20):
        """
        시장 레짐 감지

        방법:
        1. KOSPI/KOSDAQ 지수 추세 (이동평균 기울기)
        2. VIX/변동성 지표
        3. 시장 전체 거래량
        """

        # 일별 집계
        daily_stats = df_detail.groupby('매수일자').agg({
            '수익금': 'sum',
            '종목코드': 'count',
            '등락율': 'mean'
        }).rename(columns={'종목코드': 'trade_count'})

        # 이동평균
        daily_stats['ma_profit'] = daily_stats['수익금'].rolling(lookback_days).mean()
        daily_stats['ma_return'] = daily_stats['등락율'].rolling(lookback_days).mean()

        # 레짐 판단
        def classify_regime(row):
            if pd.isna(row['ma_return']):
                return 'unknown'

            if row['ma_return'] > 2:  # 평균 수익률 2% 이상
                return 'bull'
            elif row['ma_return'] < -2:  # 평균 수익률 -2% 이하
                return 'bear'
            else:
                return 'sideways'

        daily_stats['regime'] = daily_stats.apply(classify_regime, axis=1)

        # 거래별 레짐 할당
        df_with_regime = df_detail.merge(
            daily_stats[['regime']],
            left_on='매수일자',
            right_index=True,
            how='left'
        )

        return df_with_regime, daily_stats

    def analyze_by_regime(self, df_detail, feature_cols):
        """레짐별 특성 분석"""

        df_with_regime, _ = self.detect_regime(df_detail)

        results = {}

        for regime in self.regimes:
            regime_data = df_with_regime[df_with_regime['regime'] == regime]

            if len(regime_data) < 100:
                results[regime] = {'status': 'insufficient_data'}
                continue

            results[regime] = {
                'count': len(regime_data),
                'total_profit': regime_data['수익금'].sum(),
                'win_rate': (regime_data['수익금'] > 0).mean(),
                'avg_profit': regime_data['수익금'].mean(),
                'best_filters': self._find_best_filters(regime_data, feature_cols)
            }

        return results

    def _find_best_filters(self, regime_data, feature_cols, top_k=3):
        """레짐별 최적 필터 탐색"""

        # 수익 vs 손실 거래 비교
        winners = regime_data[regime_data['수익금'] > 0]
        losers = regime_data[regime_data['수익금'] <= 0]

        filter_scores = []

        for col in feature_cols:
            if winners[col].std() == 0:
                continue

            # 차이 점수
            diff = abs(winners[col].mean() - losers[col].mean()) / regime_data[col].std()

            filter_scores.append({
                'column': col,
                'winner_mean': winners[col].mean(),
                'loser_mean': losers[col].mean(),
                'separation_score': diff
            })

        return sorted(filter_scores, key=lambda x: x['separation_score'], reverse=True)[:top_k]

    def generate_regime_conditions(self, analysis_results):
        """레짐별 조건식 생성"""

        conditions = {}

        for regime, data in analysis_results.items():
            if data.get('status') == 'insufficient_data':
                conditions[regime] = "# 데이터 부족으로 조건 생성 불가"
                continue

            if regime == 'bull':
                # 상승장: 추세추종 + 적극 매수
                conditions[regime] = self._generate_aggressive_condition(data)
            elif regime == 'bear':
                # 하락장: 보수적 + 강한 신호만
                conditions[regime] = self._generate_conservative_condition(data)
            else:
                # 횡보장: 평균회귀 + 중립적
                conditions[regime] = self._generate_neutral_condition(data)

        return conditions

    def _generate_aggressive_condition(self, data):
        filters = data['best_filters']
        if not filters:
            return "# 필터 없음"

        conditions = []
        for f in filters:
            if f['winner_mean'] > f['loser_mean']:
                conditions.append(f"{f['column']} >= {f['winner_mean']:.2f}")
            else:
                conditions.append(f"{f['column']} <= {f['winner_mean']:.2f}")

        return " and ".join(conditions)

    def _generate_conservative_condition(self, data):
        # 하락장에서는 더 엄격한 조건
        filters = data['best_filters']
        if not filters:
            return "# 필터 없음"

        conditions = []
        for f in filters:
            # 상위 25% 분위수 사용 (더 엄격)
            if f['winner_mean'] > f['loser_mean']:
                conditions.append(f"{f['column']} >= {f['winner_mean'] * 1.2:.2f}")
            else:
                conditions.append(f"{f['column']} <= {f['winner_mean'] * 0.8:.2f}")

        return " and ".join(conditions)

    def _generate_neutral_condition(self, data):
        return self._generate_aggressive_condition(data)  # 기본 조건
```

### 7.4 고급 기법: Hidden Markov Model 레짐 감지

```python
# 고도화 E-1: HMM 기반 레짐 감지

def hmm_regime_detection(daily_returns, n_regimes=3):
    """
    Hidden Markov Model로 시장 레짐 감지

    장점:
    - 확률적 레짐 전환 모델링
    - 미래 레짐 확률 예측
    - 잠재 상태 자동 학습
    """

    try:
        from hmmlearn.hmm import GaussianHMM
    except ImportError:
        print("hmmlearn 설치 필요: pip install hmmlearn")
        return None

    # 데이터 준비
    X = np.array(daily_returns).reshape(-1, 1)

    # HMM 학습
    model = GaussianHMM(
        n_components=n_regimes,
        covariance_type="full",
        n_iter=1000,
        random_state=42
    )
    model.fit(X)

    # 레짐 예측
    regimes = model.predict(X)

    # 레짐 해석 (평균 수익률 기준 정렬)
    regime_means = [X[regimes == i].mean() for i in range(n_regimes)]
    regime_order = np.argsort(regime_means)  # 낮은 → 높은 순서

    regime_labels = {
        regime_order[0]: 'bear',
        regime_order[1]: 'sideways',
        regime_order[2]: 'bull'
    }

    named_regimes = [regime_labels[r] for r in regimes]

    return {
        'regimes': named_regimes,
        'transition_matrix': model.transmat_,
        'regime_means': {regime_labels[i]: regime_means[i] for i in range(n_regimes)},
        'current_regime': named_regimes[-1],
        'regime_probs': model.predict_proba(X[-1:])
    }
```

---

## 8. 방법론 F: 클러스터링 기반 접근

### 8.1 핵심 개념

**핵심 아이디어**: 거래를 클러스터링하여 수익 클러스터의 특성 파악

```
프로세스:
1. 모든 거래를 특성 기반으로 클러스터링
2. 각 클러스터의 수익성 분석
3. 수익성 높은 클러스터의 특성 → 매수 조건
4. 수익성 낮은 클러스터 → 제외 조건
```

### 8.2 근거

**왜 클러스터링이 유용한가?**

1. **비지도 학습**: 라벨 없이 자연스러운 그룹 발견
2. **다차원 패턴**: 여러 변수의 조합 효과 포착
3. **세그먼트 자동 발견**: 수동 세그먼트 정의 불필요

### 8.3 구현 설계

```python
# 방법론 F: 클러스터링 기반 접근

from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

class ClusterBasedAnalyzer:
    """
    거래를 클러스터링하여 수익/손실 패턴 발견
    """

    def __init__(self, n_clusters=8, method='kmeans'):
        self.n_clusters = n_clusters
        self.method = method
        self.scaler = StandardScaler()
        self.model = None

    def fit_predict(self, df_detail, feature_cols):
        """클러스터링 수행"""

        X = df_detail[feature_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X)

        if self.method == 'kmeans':
            self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        elif self.method == 'dbscan':
            self.model = DBSCAN(eps=0.5, min_samples=50)

        clusters = self.model.fit_predict(X_scaled)

        return clusters

    def analyze_clusters(self, df_detail, feature_cols):
        """클러스터별 수익성 분석"""

        df_detail = df_detail.copy()
        df_detail['cluster'] = self.fit_predict(df_detail, feature_cols)

        cluster_stats = []

        for cluster_id in sorted(df_detail['cluster'].unique()):
            if cluster_id == -1:  # DBSCAN 노이즈
                continue

            cluster_data = df_detail[df_detail['cluster'] == cluster_id]

            stats = {
                'cluster_id': cluster_id,
                'count': len(cluster_data),
                'total_profit': cluster_data['수익금'].sum(),
                'avg_profit': cluster_data['수익금'].mean(),
                'win_rate': (cluster_data['수익금'] > 0).mean(),
                'profit_std': cluster_data['수익금'].std(),
                'sharpe': cluster_data['수익금'].mean() / cluster_data['수익금'].std() if cluster_data['수익금'].std() > 0 else 0
            }

            # 클러스터 중심 (대표 특성)
            for col in feature_cols:
                stats[f'{col}_mean'] = cluster_data[col].mean()

            cluster_stats.append(stats)

        return pd.DataFrame(cluster_stats)

    def identify_profitable_clusters(self, cluster_stats, min_win_rate=0.5, min_count=100):
        """수익성 높은 클러스터 식별"""

        profitable = cluster_stats[
            (cluster_stats['win_rate'] >= min_win_rate) &
            (cluster_stats['count'] >= min_count) &
            (cluster_stats['avg_profit'] > 0)
        ]

        return profitable.sort_values('sharpe', ascending=False)

    def generate_cluster_conditions(self, df_detail, feature_cols, cluster_stats):
        """수익 클러스터의 조건 생성"""

        profitable_clusters = self.identify_profitable_clusters(cluster_stats)

        conditions = []

        for _, cluster in profitable_clusters.iterrows():
            cluster_id = cluster['cluster_id']
            cluster_data = df_detail[df_detail['cluster'] == cluster_id]

            # 각 특성의 범위 추출
            condition_parts = []
            for col in feature_cols:
                q25 = cluster_data[col].quantile(0.25)
                q75 = cluster_data[col].quantile(0.75)
                condition_parts.append({
                    'column': col,
                    'min': q25,
                    'max': q75
                })

            conditions.append({
                'cluster_id': cluster_id,
                'win_rate': cluster['win_rate'],
                'sharpe': cluster['sharpe'],
                'conditions': condition_parts
            })

        return conditions

    def visualize_clusters(self, df_detail, feature_cols, output_path=None):
        """클러스터 시각화 (PCA 2D)"""

        import matplotlib.pyplot as plt

        X = df_detail[feature_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X)

        # PCA로 2D 축소
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)

        clusters = df_detail['cluster'] if 'cluster' in df_detail.columns else self.fit_predict(df_detail, feature_cols)

        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap='tab10', alpha=0.5)
        plt.colorbar(scatter, label='Cluster')
        plt.xlabel('PC1')
        plt.ylabel('PC2')
        plt.title('Trade Clusters (PCA Visualization)')

        if output_path:
            plt.savefig(output_path, dpi=150, bbox_inches='tight')

        return plt
```

### 8.4 고급 기법: 계층적 클러스터링 + 덴드로그램

```python
# 고도화 F-1: 계층적 클러스터링

from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist

def hierarchical_clustering_analysis(df_detail, feature_cols, max_clusters=10):
    """
    계층적 클러스터링으로 자연스러운 그룹 발견

    장점:
    - 클러스터 수를 사전에 지정할 필요 없음
    - 덴드로그램으로 계층 구조 시각화
    - 다양한 수준의 세분화 가능
    """

    X = df_detail[feature_cols].fillna(0)
    X_scaled = StandardScaler().fit_transform(X)

    # 계층적 클러스터링
    linkage_matrix = linkage(X_scaled, method='ward')

    # 최적 클러스터 수 결정 (Elbow Method)
    inertias = []
    for k in range(2, max_clusters + 1):
        labels = fcluster(linkage_matrix, k, criterion='maxclust')

        # Within-cluster sum of squares
        inertia = 0
        for cluster_id in range(1, k + 1):
            cluster_data = X_scaled[labels == cluster_id]
            if len(cluster_data) > 0:
                centroid = cluster_data.mean(axis=0)
                inertia += ((cluster_data - centroid) ** 2).sum()

        inertias.append(inertia)

    # Elbow 찾기 (간단한 방법)
    diffs = np.diff(inertias)
    elbow_k = np.argmax(diffs > diffs.mean()) + 3  # +3 because of diff and 2-based indexing

    # 최종 클러스터 할당
    final_labels = fcluster(linkage_matrix, elbow_k, criterion='maxclust')

    return {
        'linkage_matrix': linkage_matrix,
        'optimal_k': elbow_k,
        'labels': final_labels,
        'inertias': inertias
    }
```

---

## 9. 방법론 G: 변수 상호작용 분석

### 9.1 핵심 개념

**핵심 아이디어**: 단일 변수가 아닌 **변수 간 상호작용** 효과 분석

```
기존: 시가총액 > 2000 AND 체결강도 > 80
방법론 G: 시가총액 × 체결강도의 상호작용 효과 → 새로운 조건 발견
```

### 9.2 근거

**왜 상호작용이 중요한가?**

1. **비선형 관계**: 시가총액이 클 때만 체결강도가 의미있을 수 있음
2. **조건부 효과**: A가 참일 때만 B가 유효
3. **시너지/상쇄 효과**: 개별로는 유의미하지 않지만 조합하면 유의미

### 9.3 구현 설계

```python
# 방법론 G: 변수 상호작용 분석

from sklearn.preprocessing import PolynomialFeatures
from itertools import combinations

class InteractionAnalyzer:
    """
    변수 간 상호작용 효과 분석
    """

    def __init__(self, max_interaction_order=2):
        self.max_order = max_interaction_order

    def analyze_pairwise_interactions(self, df_detail, feature_cols, target='수익금'):
        """
        모든 변수 쌍의 상호작용 효과 분석
        """

        interactions = []

        for col1, col2 in combinations(feature_cols, 2):
            # 상호작용 변수 생성
            interaction = df_detail[col1] * df_detail[col2]
            interaction_name = f"{col1}_x_{col2}"

            # 상호작용 효과 측정
            from sklearn.linear_model import LinearRegression

            # 개별 효과
            X_individual = df_detail[[col1, col2]]
            y = df_detail[target]

            model_individual = LinearRegression()
            model_individual.fit(X_individual.fillna(0), y)
            r2_individual = model_individual.score(X_individual.fillna(0), y)

            # 상호작용 포함
            X_interaction = df_detail[[col1, col2]].copy()
            X_interaction[interaction_name] = interaction

            model_interaction = LinearRegression()
            model_interaction.fit(X_interaction.fillna(0), y)
            r2_interaction = model_interaction.score(X_interaction.fillna(0), y)

            # 상호작용 기여도
            interaction_contribution = r2_interaction - r2_individual

            interactions.append({
                'var1': col1,
                'var2': col2,
                'interaction_name': interaction_name,
                'r2_individual': r2_individual,
                'r2_with_interaction': r2_interaction,
                'interaction_contribution': interaction_contribution,
                'interaction_coef': model_interaction.coef_[-1]
            })

        return pd.DataFrame(interactions).sort_values('interaction_contribution', ascending=False)

    def discover_conditional_effects(self, df_detail, feature_cols):
        """
        조건부 효과 발견: A가 참일 때만 B가 유효
        """

        conditional_effects = []

        for col_condition, col_effect in combinations(feature_cols, 2):
            # 조건 변수를 중앙값으로 분할
            median = df_detail[col_condition].median()

            # High group과 Low group에서 효과 변수의 영향 비교
            high_group = df_detail[df_detail[col_condition] >= median]
            low_group = df_detail[df_detail[col_condition] < median]

            # 각 그룹에서 효과 변수와 수익금의 상관관계
            corr_high = high_group[col_effect].corr(high_group['수익금'])
            corr_low = low_group[col_effect].corr(low_group['수익금'])

            # 차이가 크면 조건부 효과 존재
            corr_diff = abs(corr_high - corr_low)

            if corr_diff > 0.1:  # 상관계수 차이 0.1 이상
                conditional_effects.append({
                    'condition_var': col_condition,
                    'effect_var': col_effect,
                    'corr_when_high': corr_high,
                    'corr_when_low': corr_low,
                    'corr_difference': corr_diff,
                    'condition_threshold': median,
                    'stronger_in': 'high' if abs(corr_high) > abs(corr_low) else 'low'
                })

        return pd.DataFrame(conditional_effects).sort_values('corr_difference', ascending=False)

    def generate_interaction_conditions(self, interaction_results, conditional_results, top_k=5):
        """상호작용 기반 조건식 생성"""

        conditions = []

        # 상호작용 기반 조건
        for _, row in interaction_results.head(top_k).iterrows():
            if row['interaction_coef'] > 0:
                # 양의 상호작용: 둘 다 높을 때 좋음
                conditions.append({
                    'type': 'interaction_positive',
                    'condition': f"({row['var1']} > median_{row['var1']}) and ({row['var2']} > median_{row['var2']})",
                    'contribution': row['interaction_contribution']
                })
            else:
                # 음의 상호작용: 하나만 높을 때 좋음
                conditions.append({
                    'type': 'interaction_negative',
                    'condition': f"({row['var1']} > median_{row['var1']}) xor ({row['var2']} > median_{row['var2']})",
                    'contribution': row['interaction_contribution']
                })

        # 조건부 효과 기반 조건
        for _, row in conditional_results.head(top_k).iterrows():
            if row['stronger_in'] == 'high':
                conditions.append({
                    'type': 'conditional',
                    'condition': f"if ({row['condition_var']} >= {row['condition_threshold']:.2f}): use {row['effect_var']}",
                    'contribution': row['corr_difference']
                })

        return conditions
```

---

## 10. 방법론 H: 적응형/동적 조건식

### 10.1 핵심 개념

**핵심 아이디어**: 시장 상황에 따라 조건식의 **파라미터를 자동 조정**

```
정적 조건: 시가총액 >= 2000
적응형:    시가총액 >= f(시장변동성, 최근거래량)
```

### 10.2 근거

**왜 적응형이 필요한가?**

1. **시장 변화 대응**: 고정 임계값은 시장 변화에 둔감
2. **최적 임계값의 시변성**: 2022년 최적 ≠ 2025년 최적
3. **리스크 관리**: 변동성 높을 때 자동으로 보수적으로

### 10.3 구현 설계

```python
# 방법론 H: 적응형 조건식

class AdaptiveConditionGenerator:
    """
    시장 상황에 따라 조건 파라미터를 자동 조정
    """

    def __init__(self, lookback_days=20, update_frequency='weekly'):
        self.lookback = lookback_days
        self.update_freq = update_frequency
        self.current_params = {}

    def calculate_market_context(self, df_daily_market):
        """
        시장 컨텍스트 계산

        지표:
        - volatility: 최근 변동성
        - trend: 최근 추세 (이동평균 기울기)
        - volume: 최근 거래량 수준
        """

        context = {}

        # 변동성 (표준편차)
        context['volatility'] = df_daily_market['return'].rolling(self.lookback).std().iloc[-1]

        # 추세 (선형 회귀 기울기)
        recent = df_daily_market['close'].tail(self.lookback)
        x = np.arange(len(recent))
        slope, _ = np.polyfit(x, recent.values, 1)
        context['trend'] = slope / recent.mean()  # 정규화

        # 거래량 수준 (최근 vs 장기 평균)
        recent_vol = df_daily_market['volume'].tail(self.lookback).mean()
        long_vol = df_daily_market['volume'].tail(60).mean()
        context['volume_ratio'] = recent_vol / long_vol

        return context

    def adjust_thresholds(self, base_thresholds, context):
        """
        시장 컨텍스트에 따라 임계값 조정

        규칙:
        - 고변동성 → 더 엄격한 조건 (임계값 상향)
        - 하락 추세 → 더 보수적 (제외 범위 확대)
        - 저거래량 → 유동성 기준 상향
        """

        adjusted = base_thresholds.copy()

        # 변동성 조정
        vol_multiplier = 1 + (context['volatility'] - 0.02) * 5  # 기준 변동성 2%
        vol_multiplier = np.clip(vol_multiplier, 0.8, 1.5)

        if '시가총액' in adjusted:
            adjusted['시가총액'] *= vol_multiplier

        # 추세 조정
        if context['trend'] < -0.01:  # 하락 추세
            # 더 보수적으로
            if '체결강도' in adjusted:
                adjusted['체결강도']['min'] *= 1.2
                adjusted['체결강도']['max'] *= 0.9

        # 거래량 조정
        if context['volume_ratio'] < 0.8:  # 저거래량
            if '거래대금' in adjusted:
                adjusted['거래대금'] *= 1.3

        return adjusted

    def generate_adaptive_code(self, base_condition, adaptation_rules):
        """
        적응형 조건식 코드 생성
        """

        code = f"""
# 적응형 조건식 (자동 생성)
# 기본 조건: {base_condition}
# 생성 시간: {datetime.now()}

def get_adaptive_threshold(base_value, context):
    '''시장 컨텍스트에 따라 임계값 조정'''

    # 변동성 조정
    vol_adj = 1 + (context['volatility'] - 0.02) * 5
    vol_adj = max(0.8, min(1.5, vol_adj))

    # 추세 조정
    trend_adj = 1.0
    if context['trend'] < -0.01:
        trend_adj = 1.2  # 하락시 더 엄격

    return base_value * vol_adj * trend_adj

# 조건 적용
context = calculate_current_context()

if 시가총액 >= get_adaptive_threshold({base_condition['시가총액']}, context):
    if 체결강도 >= get_adaptive_threshold({base_condition['체결강도']['min']}, context):
        if 체결강도 <= get_adaptive_threshold({base_condition['체결강도']['max']}, context):
            매수 = True
"""
        return code

    def backtest_adaptive_vs_static(self, df_detail, base_thresholds, context_history):
        """
        적응형 vs 정적 조건 성능 비교
        """

        results = {
            'static': {'trades': 0, 'profit': 0, 'win_rate': 0},
            'adaptive': {'trades': 0, 'profit': 0, 'win_rate': 0}
        }

        for date in df_detail['매수일자'].unique():
            day_data = df_detail[df_detail['매수일자'] == date]

            # 해당 일자의 컨텍스트
            context = context_history.get(date, {'volatility': 0.02, 'trend': 0, 'volume_ratio': 1})

            # 정적 조건 적용
            static_mask = self._apply_thresholds(day_data, base_thresholds)
            results['static']['trades'] += static_mask.sum()
            results['static']['profit'] += day_data[static_mask]['수익금'].sum()

            # 적응형 조건 적용
            adjusted = self.adjust_thresholds(base_thresholds, context)
            adaptive_mask = self._apply_thresholds(day_data, adjusted)
            results['adaptive']['trades'] += adaptive_mask.sum()
            results['adaptive']['profit'] += day_data[adaptive_mask]['수익금'].sum()

        return results
```

---

# Part III: 고급 방법론

## 11. 방법론 I: 인과 추론 기반

### 11.1 핵심 개념

**핵심 아이디어**: 상관관계가 아닌 **인과관계** 기반 조건 발견

```
상관관계: 체결강도 높음 ↔ 수익 높음
인과관계: 체결강도 높음 → 수익 높음 (정말?)
         또는 제3의 변수(시장 관심)가 둘 다 영향?
```

### 11.2 근거

**왜 인과 추론이 필요한가?**

1. **허위 상관 제거**: 우연의 일치나 공통 원인으로 인한 상관 제거
2. **개입 효과 예측**: "이 조건을 적용하면" 결과가 어떻게 변할지 예측
3. **강건한 전략**: 시장 구조 변화에도 유효한 조건

### 11.3 구현 설계

```python
# 방법론 I: 인과 추론 기반

class CausalAnalyzer:
    """
    인과 추론을 통한 조건 발굴
    """

    def __init__(self):
        self.causal_graph = None

    def discover_causal_structure(self, df_detail, feature_cols, target='수익금'):
        """
        인과 구조 발견 (PC Algorithm 또는 GES)
        """

        try:
            from causallearn.search.ConstraintBased.PC import pc
            from causallearn.utils.cit import fisherz
        except ImportError:
            print("causal-learn 설치 필요: pip install causal-learn")
            return None

        # 데이터 준비
        all_cols = feature_cols + [target]
        data = df_detail[all_cols].fillna(0).values

        # PC Algorithm으로 인과 그래프 발견
        cg = pc(data, 0.05, fisherz, True, 0, -1)

        # 그래프 해석
        self.causal_graph = cg.G.graph

        # 타겟에 직접 영향을 주는 변수 식별
        target_idx = len(feature_cols)
        direct_causes = []

        for i, col in enumerate(feature_cols):
            if self.causal_graph[i, target_idx] != 0:
                direct_causes.append({
                    'variable': col,
                    'edge_type': self._interpret_edge(self.causal_graph[i, target_idx])
                })

        return {
            'graph': self.causal_graph,
            'direct_causes': direct_causes,
            'feature_names': feature_cols
        }

    def _interpret_edge(self, edge_value):
        """엣지 타입 해석"""
        if edge_value == -1:
            return 'directed'  # 원인 → 결과
        elif edge_value == 1:
            return 'reverse'   # 결과 → 원인 (또는 미확정)
        else:
            return 'undirected'

    def estimate_causal_effect(self, df_detail, treatment_col, outcome_col='수익금',
                               confounders=None):
        """
        인과 효과 추정 (Propensity Score Matching)
        """

        from sklearn.linear_model import LogisticRegression
        from sklearn.neighbors import NearestNeighbors

        # 처치 변수 이진화 (중앙값 기준)
        treatment = (df_detail[treatment_col] > df_detail[treatment_col].median()).astype(int)

        # Propensity Score 계산
        if confounders:
            X = df_detail[confounders].fillna(0)
        else:
            X = df_detail.drop(columns=[treatment_col, outcome_col]).select_dtypes(include=[np.number]).fillna(0)

        ps_model = LogisticRegression(max_iter=1000)
        ps_model.fit(X, treatment)
        propensity_scores = ps_model.predict_proba(X)[:, 1]

        # 매칭
        treated = df_detail[treatment == 1]
        control = df_detail[treatment == 0]

        # 처치군의 매칭된 대조군 찾기
        nn = NearestNeighbors(n_neighbors=1, metric='euclidean')
        nn.fit(propensity_scores[treatment == 0].reshape(-1, 1))

        matched_indices = nn.kneighbors(
            propensity_scores[treatment == 1].reshape(-1, 1),
            return_distance=False
        ).flatten()

        matched_control = control.iloc[matched_indices]

        # 인과 효과 (ATT: Average Treatment Effect on Treated)
        att = treated[outcome_col].mean() - matched_control[outcome_col].mean()

        return {
            'treatment_variable': treatment_col,
            'ATT': att,
            'treated_mean': treated[outcome_col].mean(),
            'matched_control_mean': matched_control[outcome_col].mean(),
            'n_treated': len(treated),
            'n_control': len(matched_control)
        }

    def generate_causal_conditions(self, causal_results):
        """인과관계 기반 조건 생성"""

        conditions = []

        for cause in causal_results['direct_causes']:
            if cause['edge_type'] == 'directed':
                # 직접적 원인 변수만 사용
                conditions.append({
                    'variable': cause['variable'],
                    'type': 'causal',
                    'confidence': 'high'
                })

        return conditions
```

---

## 12. 방법론 J: 앙상블 조건식

### 12.1 핵심 개념

**핵심 아이디어**: 여러 조건식을 결합하여 더 강건한 신호 생성

```
단일 조건: if 조건A: 매수
앙상블:    if (조건A.score + 조건B.score + 조건C.score) / 3 > threshold: 매수
```

### 12.2 구현 설계

```python
# 방법론 J: 앙상블 조건식

class EnsembleConditionGenerator:
    """
    여러 조건식을 앙상블로 결합
    """

    def __init__(self, voting_method='weighted'):
        self.voting_method = voting_method  # 'majority', 'weighted', 'stacking'
        self.conditions = []
        self.weights = []

    def add_condition(self, condition_func, weight=1.0, name='unnamed'):
        """조건식 추가"""
        self.conditions.append({
            'func': condition_func,
            'weight': weight,
            'name': name
        })

    def train_weights(self, df_detail):
        """
        각 조건의 최적 가중치 학습
        """

        from scipy.optimize import minimize

        # 각 조건의 신호 생성
        signals = np.zeros((len(df_detail), len(self.conditions)))

        for i, cond in enumerate(self.conditions):
            signals[:, i] = df_detail.apply(cond['func'], axis=1).astype(float)

        # 목표: 수익금 최대화
        y = df_detail['수익금'].values

        def objective(weights):
            # 가중 평균 신호
            ensemble_signal = (signals * weights).sum(axis=1) / weights.sum()
            # 신호 > 0.5인 경우만 매수
            mask = ensemble_signal > 0.5
            return -y[mask].sum()  # 음수 (최소화 → 최대화)

        # 초기 가중치
        x0 = np.ones(len(self.conditions))

        # 최적화 (가중치 >= 0 제약)
        bounds = [(0, 10) for _ in range(len(self.conditions))]
        result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')

        # 가중치 정규화
        self.weights = result.x / result.x.sum()

        for i, cond in enumerate(self.conditions):
            cond['weight'] = self.weights[i]

        return self.weights

    def predict(self, row):
        """앙상블 예측"""

        if self.voting_method == 'majority':
            votes = sum(1 for cond in self.conditions if cond['func'](row))
            return votes > len(self.conditions) / 2

        elif self.voting_method == 'weighted':
            score = sum(
                cond['weight'] * cond['func'](row)
                for cond in self.conditions
            )
            total_weight = sum(cond['weight'] for cond in self.conditions)
            return score / total_weight > 0.5

        else:
            raise ValueError(f"Unknown voting method: {self.voting_method}")

    def generate_ensemble_code(self):
        """앙상블 조건식 코드 생성"""

        code = """
# 앙상블 조건식 (자동 생성)

# 개별 조건 함수들
"""
        for i, cond in enumerate(self.conditions):
            code += f"""
def condition_{i}():
    '''
    {cond['name']}
    가중치: {cond['weight']:.3f}
    '''
    # 조건 로직 삽입
    return True  # placeholder
"""

        code += f"""
# 앙상블 예측
def ensemble_predict():
    weights = {list(self.weights)}
    conditions = [condition_{i}() for i in range({len(self.conditions)})]

    score = sum(w * c for w, c in zip(weights, conditions))
    return score > 0.5

매수 = ensemble_predict()
"""
        return code
```

---

## 13. 방법론 K: 강화학습 기반

### 13.1 핵심 개념

**핵심 아이디어**: 에이전트가 시장과 상호작용하며 **최적 행동(매수/관망)** 학습

```
상태 (State):  현재 시장 상황 (변수들)
행동 (Action): 매수 / 관망
보상 (Reward): 수익금
정책 (Policy): 상태 → 최적 행동 매핑
```

### 13.2 구현 설계

```python
# 방법론 K: 강화학습 기반

class TradingRLAgent:
    """
    강화학습으로 매수 조건 학습
    """

    def __init__(self, state_dim, action_dim=2):
        self.state_dim = state_dim
        self.action_dim = action_dim  # 0: 관망, 1: 매수

        # Q-Network (간단한 DQN)
        self.q_network = self._build_network()
        self.target_network = self._build_network()
        self.memory = []

    def _build_network(self):
        """Q-Network 구축"""
        try:
            import torch
            import torch.nn as nn
        except ImportError:
            print("PyTorch 설치 필요")
            return None

        return nn.Sequential(
            nn.Linear(self.state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, self.action_dim)
        )

    def get_state(self, row, feature_cols):
        """관측 상태 생성"""
        return np.array([row[col] for col in feature_cols])

    def choose_action(self, state, epsilon=0.1):
        """ε-greedy 행동 선택"""
        if np.random.random() < epsilon:
            return np.random.randint(self.action_dim)

        import torch
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.q_network(state_tensor)
        return q_values.argmax().item()

    def train(self, df_detail, feature_cols, episodes=100):
        """에피소드 기반 학습"""

        import torch
        import torch.optim as optim

        optimizer = optim.Adam(self.q_network.parameters(), lr=0.001)

        for episode in range(episodes):
            total_reward = 0

            for idx, row in df_detail.iterrows():
                state = self.get_state(row, feature_cols)
                action = self.choose_action(state, epsilon=max(0.1, 1 - episode/50))

                # 실제 수익금을 보상으로
                if action == 1:  # 매수
                    reward = row['수익금'] / 1e6  # 스케일링
                else:
                    reward = 0

                total_reward += reward

                # 경험 저장 (간단한 버전)
                self.memory.append((state, action, reward))

            # 배치 학습
            if len(self.memory) > 1000:
                self._train_batch(optimizer)

            if episode % 10 == 0:
                print(f"Episode {episode}, Total Reward: {total_reward:.2f}")

        return self

    def _train_batch(self, optimizer, batch_size=64, gamma=0.99):
        """미니배치 학습"""

        import torch
        import torch.nn.functional as F

        # 랜덤 샘플링
        indices = np.random.choice(len(self.memory), min(batch_size, len(self.memory)), replace=False)
        batch = [self.memory[i] for i in indices]

        states = torch.FloatTensor([b[0] for b in batch])
        actions = torch.LongTensor([b[1] for b in batch])
        rewards = torch.FloatTensor([b[2] for b in batch])

        # 현재 Q값
        current_q = self.q_network(states).gather(1, actions.unsqueeze(1))

        # 타겟 Q값 (단순화: 즉시 보상만)
        target_q = rewards.unsqueeze(1)

        # 손실 계산 및 역전파
        loss = F.mse_loss(current_q, target_q)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    def extract_policy(self, feature_cols, threshold=0.6):
        """학습된 정책을 규칙으로 변환 (근사)"""

        # 다양한 상태에서 행동 결정을 분석하여 규칙 추출
        # (실제로는 더 정교한 방법 필요)

        import torch

        # 샘플 상태 생성
        n_samples = 1000
        states = np.random.randn(n_samples, self.state_dim)

        with torch.no_grad():
            q_values = self.q_network(torch.FloatTensor(states))
            actions = q_values.argmax(dim=1).numpy()
            buy_probs = (q_values[:, 1] > q_values[:, 0]).float().numpy()

        # 매수 확률이 높은 상태의 특성 분석
        buy_states = states[buy_probs > threshold]

        # 각 특성의 평균값 → 조건으로 변환
        conditions = {}
        for i, col in enumerate(feature_cols):
            conditions[col] = {
                'mean': buy_states[:, i].mean(),
                'std': buy_states[:, i].std()
            }

        return conditions
```

---

# Part IV: 통합 및 적용

## 14. 방법론 비교 및 선택 가이드

### 14.1 종합 비교표

| 방법론 | 복잡도 | 해석 가능성 | 과적합 위험 | 구현 난이도 | 권장 상황 |
|--------|--------|-------------|-------------|-------------|-----------|
| **A: 시총만** | 낮음 | 높음 | 낮음 | 쉬움 | 세그먼트 단순화 |
| **B: 필터만** | 낮음 | 높음 | 낮음 | 쉬움 | 빠른 개선 |
| **C: 새 조건식** | 중간 | 중간 | 중간 | 중간 | 변수 발굴 |
| **D: 손실 역분석** | 중간 | 높음 | 낮음 | 중간 | 손실 패턴 파악 |
| **E: 레짐 기반** | 중간 | 중간 | 중간 | 중간 | 시장 상황 적응 |
| **F: 클러스터링** | 중간 | 중간 | 중간 | 중간 | 패턴 발견 |
| **G: 상호작용** | 높음 | 중간 | 중간 | 중간 | 조건부 효과 |
| **H: 적응형** | 높음 | 낮음 | 높음 | 어려움 | 동적 조정 |
| **I: 인과 추론** | 높음 | 높음 | 낮음 | 어려움 | 강건한 조건 |
| **J: 앙상블** | 중간 | 중간 | 낮음 | 중간 | 안정성 향상 |
| **K: 강화학습** | 높음 | 낮음 | 높음 | 어려움 | 실험적 탐색 |

### 14.2 권장 조합 패턴

```
패턴 1: 보수적 접근 (안정성 우선)
├── 방법론 B (필터만) - 기본
├── 방법론 D (손실 역분석) - 보완
└── 방법론 J (앙상블) - 안정화

패턴 2: 적응적 접근 (시장 대응)
├── 방법론 E (레짐 기반) - 시장 판단
├── 방법론 H (적응형) - 파라미터 조정
└── 방법론 A (시총만) - 세그먼트

패턴 3: 탐색적 접근 (새 패턴 발굴)
├── 방법론 F (클러스터링) - 패턴 발견
├── 방법론 G (상호작용) - 조건부 효과
└── 방법론 C (새 조건식) - 구체화

패턴 4: 고급 연구 접근
├── 방법론 I (인과 추론) - 진짜 원인
├── 방법론 K (강화학습) - 실험
└── 방법론 J (앙상블) - 통합
```

---

## 15. 실무 적용 로드맵

### 15.1 단기 (1-2주): 기초 방법론

```
Week 1:
□ 방법론 B (필터만) 적용
□ 방법론 D (손실 역분석) 적용
□ 두 결과 비교 및 교차 검증

Week 2:
□ Walk-Forward 검증
□ 최종 필터 선정
□ 조건식 업데이트
```

### 15.2 중기 (1개월): 혁신 방법론

```
Week 3-4:
□ 방법론 E (레짐 기반) 구현
□ 방법론 F (클러스터링) 분석
□ 패턴별 조건 도출

Week 5-6:
□ 방법론 G (상호작용) 분석
□ 조건부 효과 발견
□ 통합 조건식 생성
```

### 15.3 장기 (2-3개월): 고급 방법론

```
Month 2:
□ 방법론 I (인과 추론) 환경 구축
□ 방법론 J (앙상블) 프레임워크
□ 기본 모델 학습

Month 3:
□ 방법론 K (강화학습) 실험
□ 모든 방법론 결과 통합
□ 최종 시스템 구축
```

---

## 16. 결론 및 권장사항

### 16.1 핵심 결론

1. **다양한 관점이 필요**: 단일 방법론으로는 한계
2. **단순함이 힘**: 복잡한 방법보다 단순한 방법이 실전에서 더 안정적
3. **손실 패턴이 핵심**: 수익 패턴보다 손실 패턴이 더 명확
4. **시장 적응 필요**: 정적 조건보다 적응형 조건이 장기적으로 유리
5. **앙상블이 안정적**: 여러 조건을 결합하면 개별 조건보다 안정적

### 16.2 권장 시작점

**초보자/빠른 결과**: 방법론 B + D
**중급/균형**: 방법론 A + E + J
**고급/연구**: 방법론 I + K

### 16.3 주의사항

```
✅ DO:
- 모든 방법론에 Walk-Forward 검증 적용
- 손실 패턴을 먼저 분석
- 단순한 방법부터 시작
- 결과 문서화 및 버전 관리

❌ DON'T:
- 복잡한 방법론부터 시작
- 검증 없이 실전 적용
- 과적합 위험 무시
- 단일 방법론에 의존
```

---

## 참조 문서

| 문서 | 경로 | 핵심 내용 |
|------|------|-----------|
| 세그먼트 괴리 분석 | `docs/Study/SystemAnalysis/20260108_Segment_Filter_Prediction_vs_Actual_Discrepancy_Analysis.md` | 포트폴리오 동적 효과, 대체 매수 |
| 세그먼트 최적화 연구 | `docs/Study/ResearchReports/2025-12-20_Segmented_Filter_Optimization_Research.md` | 분할 전략, 조합 최적화 |
| 오버피팅 위험 평가 | `docs/Study/ResearchReports/2025-12-29_Overfitting_Risk_Assessment_Filter_Segment_Analysis.md` | 6가지 지표, 예방 방법 |
| AI/ML 조건식 발굴 | `docs/Study/ResearchReports/Research_Report_Automated_Condition_Finding.md` | Feature Importance, GP |

---

**문서 메타데이터**:
- 최종 업데이트: 2026-01-10
- 문서 버전: 2.0 (고도화 및 확장)
- 작성자: AI Assistant (Sisyphus)
- 검토자: -
- 다음 검토 예정일: 2026-02-10 (1개월 후)

---

**변경 이력**:
- 2026-01-10 v2.0: 대폭 확장 - 11개 방법론으로 확대, 고급 기법 추가
- 2026-01-10 v1.0: 초안 작성 (A-C 3개 방법론)
