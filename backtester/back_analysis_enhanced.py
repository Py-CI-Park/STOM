# -*- coding: utf-8 -*-
"""
[2025-12-10] 백테스팅 결과 분석 강화 모듈

기능:
1. 통계적 유의성 검증 (t-test, 효과 크기)
2. 필터 조합 분석 (시너지 효과)
3. ML 기반 특성 중요도 분석
4. 동적 최적 임계값 탐색
5. 조건식 코드 자동 생성
6. 기간별 필터 안정성 검증

Author: Claude
Date: 2025-12-10
"""

import warnings
import numpy as np
import pandas as pd
from scipy import stats
from itertools import combinations
from traceback import print_exc
from matplotlib import pyplot as plt
from matplotlib import font_manager, gridspec
from utility.setting import GRAPH_PATH

# [2025-12-10] matplotlib 한글 폰트 경고 억제
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')


# ============================================================================
# 1. 통계적 유의성 검증
# ============================================================================

def CalculateStatisticalSignificance(filtered_out, remaining):
    """
    필터 효과의 통계적 유의성을 계산합니다.

    Args:
        filtered_out: 제외되는 거래 DataFrame
        remaining: 남는 거래 DataFrame

    Returns:
        dict: 통계 검정 결과
            - t_stat: t-통계량
            - p_value: p-값
            - effect_size: Cohen's d 효과 크기
            - confidence_interval: 95% 신뢰구간
            - significant: 유의한지 여부 (p < 0.05)
    """
    result = {
        't_stat': 0,
        'p_value': 1.0,
        'effect_size': 0,
        'confidence_interval': (0, 0),
        'significant': False
    }

    if len(filtered_out) < 2 or len(remaining) < 2:
        return result

    try:
        # 두 그룹의 수익금
        group1 = filtered_out['수익금'].values
        group2 = remaining['수익금'].values

        # Welch's t-test (등분산 가정하지 않음)
        t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)

        # Cohen's d 효과 크기
        pooled_std = np.sqrt((np.var(group1) + np.var(group2)) / 2)
        if pooled_std > 0:
            effect_size = (np.mean(group1) - np.mean(group2)) / pooled_std
        else:
            effect_size = 0

        # 95% 신뢰구간 (평균 차이에 대한)
        mean_diff = np.mean(group1) - np.mean(group2)
        se = np.sqrt(np.var(group1)/len(group1) + np.var(group2)/len(group2))
        ci_low = mean_diff - 1.96 * se
        ci_high = mean_diff + 1.96 * se

        result = {
            't_stat': round(t_stat, 3),
            'p_value': round(p_value, 4),
            'effect_size': round(effect_size, 3),
            'confidence_interval': (round(ci_low, 0), round(ci_high, 0)),
            'significant': p_value < 0.05
        }
    except:
        pass

    return result


def CalculateEffectSizeInterpretation(effect_size):
    """
    Cohen's d 효과 크기를 해석합니다.

    Returns:
        str: 효과 크기 해석 (작음/중간/큼/매우큼)
    """
    abs_effect = abs(effect_size)
    if abs_effect < 0.2:
        return '무시'
    elif abs_effect < 0.5:
        return '작음'
    elif abs_effect < 0.8:
        return '중간'
    elif abs_effect < 1.2:
        return '큼'
    else:
        return '매우큼'


# ============================================================================
# 2. 강화된 파생 지표 계산
# ============================================================================

def CalculateEnhancedDerivedMetrics(df_tsg):
    """
    강화된 파생 지표를 계산합니다.

    기존 지표 + 추가 지표:
    - 모멘텀 지표
    - 변동성 지표
    - 연속 손익 패턴
    - 리스크 조정 수익률
    - 시장 타이밍 점수

    Args:
        df_tsg: 백테스팅 결과 DataFrame

    Returns:
        DataFrame: 강화된 파생 지표가 추가된 DataFrame
    """
    df = df_tsg.copy()

    # 기존 매도 시점 컬럼 확인
    sell_columns = ['매도등락율', '매도체결강도', '매도당일거래대금', '매도전일비', '매도회전율', '매도호가잔량비']
    has_sell_data = all(col in df.columns for col in sell_columns)

    if has_sell_data:
        # === 1. 변화량 지표 (매도 - 매수) ===
        df['등락율변화'] = df['매도등락율'] - df['매수등락율']
        df['체결강도변화'] = df['매도체결강도'] - df['매수체결강도']
        df['전일비변화'] = df['매도전일비'] - df['매수전일비']
        df['회전율변화'] = df['매도회전율'] - df['매수회전율']
        df['호가잔량비변화'] = df['매도호가잔량비'] - df['매수호가잔량비']

        # === 2. 변화율 지표 (매도 / 매수) ===
        df['거래대금변화율'] = np.where(
            df['매수당일거래대금'] > 0,
            df['매도당일거래대금'] / df['매수당일거래대금'],
            1.0
        )
        df['체결강도변화율'] = np.where(
            df['매수체결강도'] > 0,
            df['매도체결강도'] / df['매수체결강도'],
            1.0
        )

        # === 3. 추세 판단 지표 ===
        df['등락추세'] = df['등락율변화'].apply(lambda x: '상승' if x > 0 else ('하락' if x < 0 else '유지'))
        df['체결강도추세'] = df['체결강도변화'].apply(lambda x: '강화' if x > 10 else ('약화' if x < -10 else '유지'))
        df['거래량추세'] = df['거래대금변화율'].apply(lambda x: '증가' if x > 1.2 else ('감소' if x < 0.8 else '유지'))

        # === 4. 위험 신호 지표 ===
        df['급락신호'] = (df['등락율변화'] < -3) & (df['체결강도변화'] < -20)
        df['매도세증가'] = df['호가잔량비변화'] < -0.2
        df['거래량급감'] = df['거래대금변화율'] < 0.5

        # === 5. 강화된 위험도 점수 (0-100) ===
        df['위험도점수'] = 0
        df.loc[df['등락율변화'] < -2, '위험도점수'] += 15
        df.loc[df['등락율변화'] < -5, '위험도점수'] += 10  # 추가 가중치
        df.loc[df['체결강도변화'] < -15, '위험도점수'] += 15
        df.loc[df['체결강도변화'] < -30, '위험도점수'] += 10  # 추가 가중치
        df.loc[df['호가잔량비변화'] < -0.3, '위험도점수'] += 15
        df.loc[df['거래대금변화율'] < 0.6, '위험도점수'] += 15
        df.loc[df['매수등락율'] > 20, '위험도점수'] += 10
        df.loc[df['매수등락율'] > 25, '위험도점수'] += 10  # 추가 가중치

    # === 6. 모멘텀 점수 (NEW) ===
    if '매수등락율' in df.columns and '매수체결강도' in df.columns:
        # 등락율과 체결강도를 정규화하여 모멘텀 점수 계산
        등락율_norm = (df['매수등락율'] - df['매수등락율'].mean()) / (df['매수등락율'].std() + 0.001)
        체결강도_norm = (df['매수체결강도'] - 100) / 50  # 100을 기준으로 정규화
        df['모멘텀점수'] = round((등락율_norm * 0.4 + 체결강도_norm * 0.6) * 10, 2)

    # === 7. 변동성 지표 (NEW) ===
    if '매수고가' in df.columns and '매수저가' in df.columns:
        df['매수변동폭'] = df['매수고가'] - df['매수저가']
        df['매수변동폭비율'] = np.where(
            df['매수저가'] > 0,
            (df['매수고가'] - df['매수저가']) / df['매수저가'] * 100,
            0
        )

    if has_sell_data and '매도고가' in df.columns:
        df['매도변동폭비율'] = np.where(
            df['매도저가'] > 0,
            (df['매도고가'] - df['매도저가']) / df['매도저가'] * 100,
            0
        )
        df['변동성변화'] = df['매도변동폭비율'] - df['매수변동폭비율']

    # === 8. 시장 타이밍 점수 (NEW) ===
    if '매수시' in df.columns:
        # 시간대별 평균 수익률을 기반으로 타이밍 점수 계산
        hour_profit = df.groupby('매수시')['수익률'].mean()
        df['시간대평균수익률'] = df['매수시'].map(hour_profit)
        df['타이밍점수'] = round((df['시간대평균수익률'] - df['시간대평균수익률'].mean()) /
                               (df['시간대평균수익률'].std() + 0.001) * 10, 2)

    # === 9. 연속 손익 패턴 (NEW) ===
    df['이익여부'] = (df['수익금'] > 0).astype(int)
    df['연속이익'] = 0
    df['연속손실'] = 0

    consecutive_win = 0
    consecutive_loss = 0
    for i in range(len(df)):
        if df.iloc[i]['이익여부'] == 1:
            consecutive_win += 1
            consecutive_loss = 0
        else:
            consecutive_loss += 1
            consecutive_win = 0
        df.iloc[i, df.columns.get_loc('연속이익')] = consecutive_win
        df.iloc[i, df.columns.get_loc('연속손실')] = consecutive_loss

    # === 10. 리스크 조정 점수 (NEW) ===
    if '매수등락율' in df.columns and '보유시간' in df.columns:
        # 수익률 / (위험 요소들의 가중 합)
        risk_factor = (df['매수등락율'].abs() / 10 +
                       df['보유시간'] / 300 +
                       1)  # 최소값 보장
        df['리스크조정수익률'] = round(df['수익률'] / risk_factor, 4)

    # === 11. 스프레드 영향도 (NEW) ===
    if '매수스프레드' in df.columns:
        df['스프레드영향'] = np.where(
            df['매수스프레드'] > 0.5, '높음',
            np.where(df['매수스프레드'] > 0.2, '중간', '낮음')
        )

    # === 12. 거래 품질 점수 (NEW) - 종합 점수 ===
    df['거래품질점수'] = 50  # 기본값

    # 긍정적 요소 가산
    if '매수체결강도' in df.columns:
        df.loc[df['매수체결강도'] >= 120, '거래품질점수'] += 10
        df.loc[df['매수체결강도'] >= 150, '거래품질점수'] += 10

    if '매수호가잔량비' in df.columns:
        df.loc[df['매수호가잔량비'] >= 100, '거래품질점수'] += 10

    if '시가총액' in df.columns:
        df.loc[(df['시가총액'] >= 1000) & (df['시가총액'] <= 10000), '거래품질점수'] += 10

    # 부정적 요소 감산
    if '매수등락율' in df.columns:
        df.loc[df['매수등락율'] >= 25, '거래품질점수'] -= 15
        df.loc[df['매수등락율'] >= 30, '거래품질점수'] -= 10

    if '매수스프레드' in df.columns:
        df.loc[df['매수스프레드'] >= 0.5, '거래품질점수'] -= 10

    df['거래품질점수'] = df['거래품질점수'].clip(0, 100)

    return df


# ============================================================================
# 3. 동적 최적 임계값 탐색
# ============================================================================

def FindOptimalThresholds(df_tsg, column, direction='less', n_splits=20):
    """
    특정 컬럼에 대해 최적의 필터 임계값을 탐색합니다.

    Args:
        df_tsg: DataFrame
        column: 분석할 컬럼명
        direction: 'less' (미만 제외) 또는 'greater' (이상 제외)
        n_splits: 분할 수

    Returns:
        dict: 최적 임계값 정보
            - optimal_threshold: 최적 임계값
            - improvement: 수익 개선 금액
            - excluded_ratio: 제외 비율
            - all_thresholds: 모든 임계값 결과
    """
    if column not in df_tsg.columns:
        return None

    values = df_tsg[column].dropna()
    if len(values) < 10:
        return None

    # 분위수 기반 임계값 생성
    percentiles = np.linspace(5, 95, n_splits)
    thresholds = np.percentile(values, percentiles)

    results = []
    total_profit = df_tsg['수익금'].sum()
    total_trades = len(df_tsg)

    for threshold in thresholds:
        if direction == 'less':
            condition = df_tsg[column] < threshold
        else:
            condition = df_tsg[column] >= threshold

        filtered_out = df_tsg[condition]
        remaining = df_tsg[~condition]

        if len(filtered_out) == 0 or len(remaining) == 0:
            continue

        improvement = -filtered_out['수익금'].sum()
        excluded_ratio = len(filtered_out) / total_trades * 100
        remaining_winrate = (remaining['수익금'] > 0).mean() * 100

        # 효율성 점수: 수익개선 / 제외거래수 (제외 거래당 개선 효과)
        efficiency = improvement / len(filtered_out) if len(filtered_out) > 0 else 0

        results.append({
            'threshold': round(threshold, 2),
            'improvement': int(improvement),
            'excluded_ratio': round(excluded_ratio, 1),
            'excluded_count': len(filtered_out),
            'remaining_count': len(remaining),
            'remaining_winrate': round(remaining_winrate, 1),
            'efficiency': round(efficiency, 0)
        })

    if not results:
        return None

    # 최적 임계값 선택 (수익개선 × 효율성 가중)
    df_results = pd.DataFrame(results)

    # 제외 비율이 50% 이하인 것만 고려
    df_valid = df_results[df_results['excluded_ratio'] <= 50]

    if len(df_valid) == 0:
        return None

    # 수익개선이 양수인 것 중 효율성이 가장 높은 것
    df_positive = df_valid[df_valid['improvement'] > 0]

    if len(df_positive) > 0:
        best_idx = df_positive['efficiency'].idxmax()
        best = df_positive.loc[best_idx]
    else:
        best = df_valid.loc[df_valid['improvement'].idxmax()]

    return {
        'column': column,
        'direction': direction,
        'optimal_threshold': best['threshold'],
        'improvement': best['improvement'],
        'excluded_ratio': best['excluded_ratio'],
        'excluded_count': best['excluded_count'],
        'remaining_winrate': best['remaining_winrate'],
        'efficiency': best['efficiency'],
        'all_thresholds': results
    }


def FindAllOptimalThresholds(df_tsg):
    """
    모든 주요 컬럼에 대해 최적 임계값을 탐색합니다.

    Returns:
        list: 각 컬럼별 최적 임계값 정보
    """
    results = []

    # 분석할 컬럼과 방향 정의
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
    ]

    # 파생 지표도 분석
    if '위험도점수' in df_tsg.columns:
        columns_config.append(('위험도점수', 'greater', '위험도 {:.0f}점 이상 제외'))

    if '거래품질점수' in df_tsg.columns:
        columns_config.append(('거래품질점수', 'less', '거래품질 {:.0f}점 미만 제외'))

    if '모멘텀점수' in df_tsg.columns:
        columns_config.append(('모멘텀점수', 'less', '모멘텀 {:.1f} 미만 제외'))

    for column, direction, name_template in columns_config:
        result = FindOptimalThresholds(df_tsg, column, direction)
        if result and result['improvement'] > 0:
            result['필터명'] = name_template.format(result['optimal_threshold'])
            results.append(result)

    # 수익 개선금액 기준 정렬
    results.sort(key=lambda x: x['improvement'], reverse=True)

    return results


# ============================================================================
# 4. 필터 조합 분석
# ============================================================================

def AnalyzeFilterCombinations(df_tsg, max_filters=3, top_n=10):
    """
    필터 조합의 시너지 효과를 분석합니다.

    Args:
        df_tsg: DataFrame
        max_filters: 최대 조합 필터 수 (2 또는 3)
        top_n: 분석할 상위 단일 필터 수

    Returns:
        list: 필터 조합 분석 결과
    """
    # 먼저 단일 필터 분석
    single_filters = AnalyzeFilterEffectsEnhanced(df_tsg)

    if not single_filters:
        return []

    # 상위 필터만 조합 분석 (계산량 제한)
    top_filters = [f for f in single_filters if f['수익개선금액'] > 0][:top_n]

    if len(top_filters) < 2:
        return []

    total_profit = df_tsg['수익금'].sum()
    total_trades = len(df_tsg)

    combination_results = []

    # 2개 필터 조합
    for f1, f2 in combinations(range(len(top_filters)), 2):
        filter1 = top_filters[f1]
        filter2 = top_filters[f2]

        try:
            # 조합 조건 생성
            cond1 = eval(filter1['조건식']) if '조건식' in filter1 else None
            cond2 = eval(filter2['조건식']) if '조건식' in filter2 else None

            if cond1 is None or cond2 is None:
                continue

            combined_condition = cond1 | cond2  # OR 조건 (둘 중 하나라도 해당되면 제외)

            filtered_out = df_tsg[combined_condition]
            remaining = df_tsg[~combined_condition]

            if len(filtered_out) == 0 or len(remaining) == 0:
                continue

            improvement = -filtered_out['수익금'].sum()
            excluded_ratio = len(filtered_out) / total_trades * 100

            # 시너지 효과 계산 (조합 개선 - 개별 개선 합)
            individual_sum = filter1['수익개선금액'] + filter2['수익개선금액']
            synergy = improvement - individual_sum
            synergy_ratio = synergy / individual_sum * 100 if individual_sum > 0 else 0

            combination_results.append({
                '조합유형': '2개 조합',
                '필터1': filter1['필터명'],
                '필터2': filter2['필터명'],
                '필터3': '',
                '개별개선합': int(individual_sum),
                '조합개선': int(improvement),
                '시너지효과': int(synergy),
                '시너지비율': round(synergy_ratio, 1),
                '제외비율': round(excluded_ratio, 1),
                '잔여승률': round((remaining['수익금'] > 0).mean() * 100, 1),
                '잔여거래수': len(remaining),
                '권장': '★★★' if synergy_ratio > 20 else ('★★' if synergy_ratio > 0 else ''),
            })
        except:
            continue

    # 3개 필터 조합 (상위 5개만)
    if max_filters >= 3 and len(top_filters) >= 3:
        for f1, f2, f3 in combinations(range(min(5, len(top_filters))), 3):
            filter1 = top_filters[f1]
            filter2 = top_filters[f2]
            filter3 = top_filters[f3]

            try:
                cond1 = eval(filter1['조건식']) if '조건식' in filter1 else None
                cond2 = eval(filter2['조건식']) if '조건식' in filter2 else None
                cond3 = eval(filter3['조건식']) if '조건식' in filter3 else None

                if cond1 is None or cond2 is None or cond3 is None:
                    continue

                combined_condition = cond1 | cond2 | cond3

                filtered_out = df_tsg[combined_condition]
                remaining = df_tsg[~combined_condition]

                if len(filtered_out) == 0 or len(remaining) == 0:
                    continue

                improvement = -filtered_out['수익금'].sum()
                excluded_ratio = len(filtered_out) / total_trades * 100

                individual_sum = filter1['수익개선금액'] + filter2['수익개선금액'] + filter3['수익개선금액']
                synergy = improvement - individual_sum
                synergy_ratio = synergy / individual_sum * 100 if individual_sum > 0 else 0

                combination_results.append({
                    '조합유형': '3개 조합',
                    '필터1': filter1['필터명'],
                    '필터2': filter2['필터명'],
                    '필터3': filter3['필터명'],
                    '개별개선합': int(individual_sum),
                    '조합개선': int(improvement),
                    '시너지효과': int(synergy),
                    '시너지비율': round(synergy_ratio, 1),
                    '제외비율': round(excluded_ratio, 1),
                    '잔여승률': round((remaining['수익금'] > 0).mean() * 100, 1),
                    '잔여거래수': len(remaining),
                    '권장': '★★★' if synergy_ratio > 20 else ('★★' if synergy_ratio > 0 else ''),
                })
            except:
                continue

    # 시너지 효과 기준 정렬
    combination_results.sort(key=lambda x: x['시너지효과'], reverse=True)

    return combination_results


# ============================================================================
# 5. 강화된 필터 효과 분석
# ============================================================================

def AnalyzeFilterEffectsEnhanced(df_tsg):
    """
    강화된 필터 효과 분석 (통계적 유의성 + 동적 임계값 포함)

    Returns:
        list: 필터 효과 분석 결과 (통계 검정 결과 포함)
    """
    filter_results = []
    total_profit = df_tsg['수익금'].sum()
    total_trades = len(df_tsg)

    if total_trades == 0:
        return filter_results

    # === 필터 조건 정의 (조건식 포함) ===
    filter_conditions = []

    # 1. 시간대 필터
    if '매수시' in df_tsg.columns:
        for hour in sorted(df_tsg['매수시'].unique()):
            filter_conditions.append({
                '필터명': f'시간대 {hour}시 제외',
                '조건': df_tsg['매수시'] == hour,
                '조건식': f"df_tsg['매수시'] == {hour}",
                '분류': '시간대',
                '코드': f'매수시 != {hour}'
            })

    # 2. 등락율 필터 (다양한 임계값)
    if '매수등락율' in df_tsg.columns:
        for threshold in [5, 10, 15, 20, 25, 30]:
            filter_conditions.append({
                '필터명': f'등락율 {threshold}% 이상 제외',
                '조건': df_tsg['매수등락율'] >= threshold,
                '조건식': f"df_tsg['매수등락율'] >= {threshold}",
                '분류': '등락율',
                '코드': f'등락율 < {threshold}'
            })
        for threshold in [3, 5, 7, 10]:
            filter_conditions.append({
                '필터명': f'등락율 {threshold}% 미만 제외',
                '조건': df_tsg['매수등락율'] < threshold,
                '조건식': f"df_tsg['매수등락율'] < {threshold}",
                '분류': '등락율',
                '코드': f'등락율 >= {threshold}'
            })

    # 3. 체결강도 필터
    if '매수체결강도' in df_tsg.columns:
        for threshold in [70, 80, 90, 100]:
            filter_conditions.append({
                '필터명': f'체결강도 {threshold} 미만 제외',
                '조건': df_tsg['매수체결강도'] < threshold,
                '조건식': f"df_tsg['매수체결강도'] < {threshold}",
                '분류': '체결강도',
                '코드': f'체결강도 >= {threshold}'
            })
        for threshold in [150, 200, 250]:
            filter_conditions.append({
                '필터명': f'체결강도 {threshold} 이상 제외',
                '조건': df_tsg['매수체결강도'] >= threshold,
                '조건식': f"df_tsg['매수체결강도'] >= {threshold}",
                '분류': '체결강도',
                '코드': f'체결강도 < {threshold}'
            })

    # 4. 거래대금 필터
    if '매수당일거래대금' in df_tsg.columns:
        for threshold in [50, 100, 200, 500]:
            filter_conditions.append({
                '필터명': f'거래대금 {threshold}억 미만 제외',
                '조건': df_tsg['매수당일거래대금'] < threshold,
                '조건식': f"df_tsg['매수당일거래대금'] < {threshold}",
                '분류': '거래대금',
                '코드': f'당일거래대금 >= {threshold}'
            })

    # 5. 시가총액 필터
    if '시가총액' in df_tsg.columns:
        for threshold in [500, 1000, 2000, 3000, 5000]:
            filter_conditions.append({
                '필터명': f'시가총액 {threshold}억 미만 제외',
                '조건': df_tsg['시가총액'] < threshold,
                '조건식': f"df_tsg['시가총액'] < {threshold}",
                '분류': '시가총액',
                '코드': f'시가총액 >= {threshold}'
            })
        for threshold in [10000, 20000, 50000]:
            filter_conditions.append({
                '필터명': f'시가총액 {threshold}억 이상 제외',
                '조건': df_tsg['시가총액'] >= threshold,
                '조건식': f"df_tsg['시가총액'] >= {threshold}",
                '분류': '시가총액',
                '코드': f'시가총액 < {threshold}'
            })

    # 6. 보유시간 필터
    for threshold in [10, 30, 60, 120, 300]:
        filter_conditions.append({
            '필터명': f'보유시간 {threshold}초 미만 제외',
            '조건': df_tsg['보유시간'] < threshold,
            '조건식': f"df_tsg['보유시간'] < {threshold}",
            '분류': '보유시간',
            '코드': f'# 보유시간 {threshold}초 이상 유지'
        })
    for threshold in [600, 1200, 1800, 3600]:
        filter_conditions.append({
            '필터명': f'보유시간 {threshold}초 이상 제외',
            '조건': df_tsg['보유시간'] >= threshold,
            '조건식': f"df_tsg['보유시간'] >= {threshold}",
            '분류': '보유시간',
            '코드': f'# 보유시간 {threshold}초 전에 청산'
        })

    # 7. 호가 관련 필터
    if '매수호가잔량비' in df_tsg.columns:
        for threshold in [50, 70, 90, 100]:
            filter_conditions.append({
                '필터명': f'호가잔량비 {threshold}% 미만 제외',
                '조건': df_tsg['매수호가잔량비'] < threshold,
                '조건식': f"df_tsg['매수호가잔량비'] < {threshold}",
                '분류': '호가',
                '코드': f'매수총잔량 / 매도총잔량 * 100 >= {threshold}'
            })

    if '매수스프레드' in df_tsg.columns:
        for threshold in [0.2, 0.3, 0.5, 1.0]:
            filter_conditions.append({
                '필터명': f'스프레드 {threshold}% 이상 제외',
                '조건': df_tsg['매수스프레드'] >= threshold,
                '조건식': f"df_tsg['매수스프레드'] >= {threshold}",
                '분류': '호가',
                '코드': f'스프레드 < {threshold}'
            })

    # 8. 파생 지표 필터
    if '위험도점수' in df_tsg.columns:
        for threshold in [30, 40, 50, 60, 70]:
            filter_conditions.append({
                '필터명': f'위험도 {threshold}점 이상 제외',
                '조건': df_tsg['위험도점수'] >= threshold,
                '조건식': f"df_tsg['위험도점수'] >= {threshold}",
                '분류': '위험신호',
                '코드': f'# 위험도 {threshold}점 미만만 매수'
            })

    if '거래품질점수' in df_tsg.columns:
        for threshold in [30, 40, 50]:
            filter_conditions.append({
                '필터명': f'거래품질 {threshold}점 미만 제외',
                '조건': df_tsg['거래품질점수'] < threshold,
                '조건식': f"df_tsg['거래품질점수'] < {threshold}",
                '분류': '품질',
                '코드': f'# 거래품질 {threshold}점 이상만 매수'
            })

    if '급락신호' in df_tsg.columns:
        filter_conditions.append({
            '필터명': '급락신호 발생 제외',
            '조건': df_tsg['급락신호'] == True,
            '조건식': "df_tsg['급락신호'] == True",
            '분류': '위험신호',
            '코드': '# 급락신호 종목 제외'
        })

    # === 각 필터 효과 계산 (통계 검정 포함) ===
    for fc in filter_conditions:
        try:
            filtered_out = df_tsg[fc['조건']]
            remaining = df_tsg[~fc['조건']]

            if len(filtered_out) == 0:
                continue

            filtered_profit = filtered_out['수익금'].sum()
            remaining_profit = remaining['수익금'].sum()
            filtered_count = len(filtered_out)
            remaining_count = len(remaining)

            improvement = -filtered_profit

            # 통계적 유의성 검증
            stat_result = CalculateStatisticalSignificance(filtered_out, remaining)
            effect_interpretation = CalculateEffectSizeInterpretation(stat_result['effect_size'])

            # 제외 거래의 특성 분석
            filtered_avg_profit = filtered_out['수익률'].mean() if len(filtered_out) > 0 else 0
            remaining_avg_profit = remaining['수익률'].mean() if len(remaining) > 0 else 0

            # 권장 등급 (개선된 로직)
            if improvement > total_profit * 0.15 and stat_result['significant']:
                rating = '★★★'
            elif improvement > total_profit * 0.05 and stat_result['p_value'] < 0.1:
                rating = '★★'
            elif improvement > 0:
                rating = '★'
            else:
                rating = ''

            filter_results.append({
                '분류': fc['분류'],
                '필터명': fc['필터명'],
                '조건식': fc['조건식'],
                '적용코드': fc['코드'],
                '제외거래수': filtered_count,
                '제외비율': round(filtered_count / total_trades * 100, 1),
                '제외거래수익금': int(filtered_profit),
                '제외평균수익률': round(filtered_avg_profit, 2),
                '잔여거래수': remaining_count,
                '잔여거래수익금': int(remaining_profit),
                '잔여평균수익률': round(remaining_avg_profit, 2),
                '수익개선금액': int(improvement),
                '제외거래승률': round((filtered_out['수익금'] > 0).mean() * 100, 1),
                '잔여거래승률': round((remaining['수익금'] > 0).mean() * 100, 1),
                't통계량': stat_result['t_stat'],
                'p값': stat_result['p_value'],
                '효과크기': stat_result['effect_size'],
                '효과해석': effect_interpretation,
                '신뢰구간': stat_result['confidence_interval'],
                '유의함': '예' if stat_result['significant'] else '아니오',
                '적용권장': rating,
            })
        except:
            continue

    # 수익개선금액 기준 정렬
    filter_results.sort(key=lambda x: x['수익개선금액'], reverse=True)

    return filter_results


# ============================================================================
# 6. ML 기반 특성 중요도 분석
# ============================================================================

def AnalyzeFeatureImportance(df_tsg):
    """
    Decision Tree를 사용하여 특성 중요도를 분석합니다.

    Returns:
        dict: 특성 중요도 분석 결과
            - feature_importance: 특성별 중요도
            - top_features: 상위 특성
            - decision_rules: 주요 분기 규칙
    """
    try:
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return None

    # 분석에 사용할 특성 선택
    feature_columns = [
        '매수등락율', '매수체결강도', '매수당일거래대금', '매수전일비',
        '매수회전율', '시가총액', '보유시간', '매수호가잔량비'
    ]

    available_features = [col for col in feature_columns if col in df_tsg.columns]

    if len(available_features) < 3:
        return None

    # 타겟 변수: 이익 여부
    df_analysis = df_tsg[available_features + ['수익금']].dropna()

    if len(df_analysis) < 50:
        return None

    X = df_analysis[available_features]
    y = (df_analysis['수익금'] > 0).astype(int)

    # 표준화
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Decision Tree 학습
    clf = DecisionTreeClassifier(max_depth=4, min_samples_leaf=10, random_state=42)
    clf.fit(X_scaled, y)

    # 특성 중요도
    importance = dict(zip(available_features, clf.feature_importances_))
    importance_sorted = sorted(importance.items(), key=lambda x: x[1], reverse=True)

    # 분기 규칙 추출 (간략화)
    tree = clf.tree_
    rules = []

    def extract_rules(node_id, depth, prefix=""):
        if tree.feature[node_id] != -2:  # 내부 노드
            feature_name = available_features[tree.feature[node_id]]
            threshold = tree.threshold[node_id]

            # 원래 스케일로 변환
            feature_idx = available_features.index(feature_name)
            original_threshold = threshold * scaler.scale_[feature_idx] + scaler.mean_[feature_idx]

            if depth <= 2:  # 상위 2레벨만
                left_samples = tree.n_node_samples[tree.children_left[node_id]]
                right_samples = tree.n_node_samples[tree.children_right[node_id]]

                left_value = tree.value[tree.children_left[node_id]][0]
                right_value = tree.value[tree.children_right[node_id]][0]

                left_win_rate = left_value[1] / (left_value[0] + left_value[1]) * 100 if (left_value[0] + left_value[1]) > 0 else 0
                right_win_rate = right_value[1] / (right_value[0] + right_value[1]) * 100 if (right_value[0] + right_value[1]) > 0 else 0

                rules.append({
                    'depth': depth,
                    'feature': feature_name,
                    'threshold': round(original_threshold, 2),
                    'left_samples': left_samples,
                    'right_samples': right_samples,
                    'left_win_rate': round(left_win_rate, 1),
                    'right_win_rate': round(right_win_rate, 1),
                    'rule': f"{feature_name} < {original_threshold:.1f}: 승률 {left_win_rate:.1f}% (n={left_samples})"
                })

                extract_rules(tree.children_left[node_id], depth + 1, prefix + "L")
                extract_rules(tree.children_right[node_id], depth + 1, prefix + "R")

    extract_rules(0, 0)

    return {
        'feature_importance': importance_sorted,
        'top_features': importance_sorted[:5],
        'decision_rules': rules[:10],
        'model_accuracy': round(clf.score(X_scaled, y) * 100, 1)
    }


# ============================================================================
# 7. 기간별 필터 안정성 검증
# ============================================================================

def AnalyzeFilterStability(df_tsg, n_periods=5):
    """
    필터 효과의 시간적 안정성을 검증합니다.

    Args:
        df_tsg: DataFrame
        n_periods: 분할 기간 수

    Returns:
        list: 필터별 안정성 분석 결과
    """
    if len(df_tsg) < n_periods * 20:
        return []

    # 인덱스로 기간 분할
    period_size = len(df_tsg) // n_periods
    periods = []
    for i in range(n_periods):
        start_idx = i * period_size
        end_idx = start_idx + period_size if i < n_periods - 1 else len(df_tsg)
        periods.append(df_tsg.iloc[start_idx:end_idx])

    # 주요 필터만 안정성 분석
    key_filters = [
        ('매수등락율 >= 20', lambda df: df['매수등락율'] >= 20, '등락율'),
        ('매수체결강도 < 80', lambda df: df['매수체결강도'] < 80, '체결강도'),
        ('보유시간 < 60', lambda df: df['보유시간'] < 60, '보유시간'),
    ]

    if '시가총액' in df_tsg.columns:
        key_filters.append(('시가총액 < 1000', lambda df: df['시가총액'] < 1000, '시가총액'))

    if '위험도점수' in df_tsg.columns:
        key_filters.append(('위험도점수 >= 50', lambda df: df['위험도점수'] >= 50, '위험도'))

    stability_results = []

    for filter_name, filter_func, category in key_filters:
        try:
            if filter_name.split()[0] not in df_tsg.columns:
                continue

            period_improvements = []

            for period_df in periods:
                condition = filter_func(period_df)
                filtered_out = period_df[condition]
                improvement = -filtered_out['수익금'].sum() if len(filtered_out) > 0 else 0
                period_improvements.append(improvement)

            # 안정성 지표 계산
            improvements = np.array(period_improvements)
            mean_improvement = np.mean(improvements)
            std_improvement = np.std(improvements)
            positive_periods = sum(1 for x in improvements if x > 0)

            # 일관성 점수 (0-100)
            # 모든 기간에서 양수이고 변동성이 낮을수록 높음
            consistency_score = (positive_periods / n_periods) * 50
            if mean_improvement > 0 and std_improvement > 0:
                cv = std_improvement / mean_improvement  # 변동계수
                consistency_score += max(0, 50 - cv * 50)

            stability_results.append({
                '분류': category,
                '필터명': filter_name,
                '평균개선': int(mean_improvement),
                '표준편차': int(std_improvement),
                '양수기간수': positive_periods,
                '총기간수': n_periods,
                '일관성점수': round(consistency_score, 1),
                '기간별개선': [int(x) for x in period_improvements],
                '안정성등급': '안정' if consistency_score >= 70 else ('보통' if consistency_score >= 40 else '불안정'),
            })
        except:
            continue

    stability_results.sort(key=lambda x: x['일관성점수'], reverse=True)
    return stability_results


# ============================================================================
# 8. 조건식 코드 자동 생성
# ============================================================================

def GenerateFilterCode(filter_results, top_n=5):
    """
    필터 분석 결과를 바탕으로 실제 적용 가능한 조건식 코드를 생성합니다.

    Args:
        filter_results: 필터 분석 결과 리스트
        top_n: 상위 N개 필터

    Returns:
        dict: 코드 생성 결과
            - buy_conditions: 매수 조건 코드
            - filter_conditions: 필터 조건 코드
            - full_code: 전체 조건식 코드
    """
    if not filter_results:
        return None

    top_filters = [f for f in filter_results if f['수익개선금액'] > 0][:top_n]

    if not top_filters:
        return None

    # 카테고리별 조건 분류
    conditions_by_category = {}
    for f in top_filters:
        category = f['분류']
        if category not in conditions_by_category:
            conditions_by_category[category] = []
        conditions_by_category[category].append(f)

    # 코드 생성
    code_lines = []
    code_lines.append("# ===== 자동 생성된 필터 조건 (백테스팅 분석 기반) =====")
    code_lines.append("")

    # 매수 조건에 추가할 필터
    buy_filter_lines = []

    for category, filters in conditions_by_category.items():
        code_lines.append(f"# [{category}] 필터")

        for f in filters:
            code_lines.append(f"# - {f['필터명']}: 수익개선 {f['수익개선금액']:,}원, 제외율 {f['제외비율']}%")

            # 조건식을 실제 코드로 변환
            if '적용코드' in f and f['적용코드']:
                buy_filter_lines.append(f"    and {f['적용코드']}")

        code_lines.append("")

    # 전체 매수 조건 예시
    code_lines.append("# ===== 적용 예시 =====")
    code_lines.append("# 기존 매수 조건에 다음 필터를 AND 조건으로 추가:")
    code_lines.append("#")
    code_lines.append("# if 기존매수조건")
    for line in buy_filter_lines:
        code_lines.append(f"#{line}")
    code_lines.append("#     매수 = True")

    # 개별 조건식
    individual_conditions = []
    for f in top_filters:
        if '적용코드' in f:
            individual_conditions.append({
                '필터명': f['필터명'],
                '조건코드': f['적용코드'],
                '수익개선': f['수익개선금액'],
                '제외율': f['제외비율']
            })

    return {
        'code_text': '\n'.join(code_lines),
        'buy_conditions': buy_filter_lines,
        'individual_conditions': individual_conditions,
        'summary': {
            'total_filters': len(top_filters),
            'total_improvement': sum(f['수익개선금액'] for f in top_filters),
            'categories': list(conditions_by_category.keys())
        }
    }


# ============================================================================
# 9. 강화된 시각화 차트
# ============================================================================

def PltEnhancedAnalysisCharts(df_tsg, save_file_name, teleQ, filter_results=None, feature_importance=None):
    """
    강화된 분석 차트를 생성합니다.

    신규 차트:
    - 필터 효과 통계 요약 테이블
    - 특성 중요도 막대 차트
    - 최적 임계값 탐색 결과
    - 필터 조합 시너지 히트맵
    """
    if len(df_tsg) < 5:
        return

    try:
        # [2025-12-10] 한글 폰트 설정 (back_static.py와 동일한 방식)
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_family = font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_family
            plt.rcParams['font.sans-serif'] = [font_family]
        except:
            # Fallback: 기본 설정
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']

        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['axes.grid'] = True

        fig = plt.figure(figsize=(20, 24))
        fig.suptitle(f'강화된 백테스팅 분석 - {save_file_name}', fontsize=16, fontweight='bold')

        gs = gridspec.GridSpec(5, 3, figure=fig, hspace=0.4, wspace=0.3)

        color_profit = '#2ECC71'
        color_loss = '#E74C3C'
        color_neutral = '#3498DB'

        # ============ Chart 1: 필터 효과 순위 ============
        ax1 = fig.add_subplot(gs[0, :2])
        if filter_results and len(filter_results) > 0:
            top_10 = [f for f in filter_results if f['수익개선금액'] > 0][:10]
            if top_10:
                names = [f['필터명'][:20] for f in top_10]
                improvements = [f['수익개선금액'] for f in top_10]
                colors = [color_profit for _ in improvements]

                y_pos = range(len(names))
                ax1.barh(y_pos, improvements, color=colors, edgecolor='black', linewidth=0.5)
                ax1.set_yticks(y_pos)
                ax1.set_yticklabels(names, fontsize=9)
                ax1.set_xlabel('수익 개선 금액')
                ax1.set_title('Top 10 필터 효과 (수익개선 기준)')

                # 값 표시
                for i, v in enumerate(improvements):
                    ax1.text(v + max(improvements) * 0.01, i, f'{v:,}원', va='center', fontsize=8)

                ax1.invert_yaxis()

        # ============ Chart 2: 통계적 유의성 요약 ============
        ax2 = fig.add_subplot(gs[0, 2])
        if filter_results and len(filter_results) > 0:
            significant_count = sum(1 for f in filter_results if f.get('유의함') == '예')
            total_count = len(filter_results)

            sizes = [significant_count, total_count - significant_count]
            labels = [f'유의함\n({significant_count})', f'비유의\n({total_count - significant_count})']
            colors = [color_profit, '#CCCCCC']

            ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax2.set_title('필터 통계적 유의성 분포')

        # ============ Chart 3: 특성 중요도 ============
        ax3 = fig.add_subplot(gs[1, 0])
        if feature_importance and 'feature_importance' in feature_importance:
            fi = feature_importance['feature_importance'][:8]
            names = [x[0] for x in fi]
            values = [x[1] for x in fi]

            y_pos = range(len(names))
            ax3.barh(y_pos, values, color=color_neutral, edgecolor='black', linewidth=0.5)
            ax3.set_yticks(y_pos)
            ax3.set_yticklabels(names, fontsize=9)
            ax3.set_xlabel('중요도')
            ax3.set_title(f'ML 특성 중요도 (정확도: {feature_importance.get("model_accuracy", 0)}%)')
            ax3.invert_yaxis()

        # ============ Chart 4: 효과 크기 분포 ============
        ax4 = fig.add_subplot(gs[1, 1])
        if filter_results and len(filter_results) > 0:
            effect_sizes = [f['효과크기'] for f in filter_results if '효과크기' in f]
            if effect_sizes:
                ax4.hist(effect_sizes, bins=20, color=color_neutral, edgecolor='black', alpha=0.7)
                ax4.axvline(x=0.2, color='orange', linestyle='--', label='작은 효과')
                ax4.axvline(x=0.5, color='red', linestyle='--', label='중간 효과')
                ax4.axvline(x=0.8, color='purple', linestyle='--', label='큰 효과')
                ax4.set_xlabel('Cohen\'s d 효과 크기')
                ax4.set_ylabel('필터 수')
                ax4.set_title('필터 효과 크기 분포')
                ax4.legend(fontsize=8)

        # ============ Chart 5: 제외비율 vs 수익개선 ============
        ax5 = fig.add_subplot(gs[1, 2])
        if filter_results and len(filter_results) > 0:
            excluded_ratios = [f['제외비율'] for f in filter_results]
            improvements = [f['수익개선금액'] for f in filter_results]
            colors = [color_profit if imp > 0 else color_loss for imp in improvements]

            ax5.scatter(excluded_ratios, improvements, c=colors, alpha=0.6, s=50)
            ax5.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax5.set_xlabel('제외 비율 (%)')
            ax5.set_ylabel('수익 개선 금액')
            ax5.set_title('제외비율 vs 수익개선 트레이드오프')

        # ============ Chart 6-8: 기존 분석 차트 (시간대, 등락율, 체결강도) ============
        # 시간대별
        ax6 = fig.add_subplot(gs[2, 0])
        if '매수시' in df_tsg.columns:
            df_hour = df_tsg.groupby('매수시').agg({'수익금': 'sum', '수익률': 'mean'}).reset_index()
            colors = [color_profit if x >= 0 else color_loss for x in df_hour['수익금']]
            ax6.bar(df_hour['매수시'], df_hour['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax6.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax6.set_xlabel('매수 시간대')
            ax6.set_ylabel('총 수익금')
            ax6.set_title('시간대별 수익금')

        # 등락율별
        ax7 = fig.add_subplot(gs[2, 1])
        if '매수등락율' in df_tsg.columns:
            bins = [0, 5, 10, 15, 20, 25, 30, 100]
            labels = ['0-5', '5-10', '10-15', '15-20', '20-25', '25-30', '30+']
            df_tsg['등락율구간'] = pd.cut(df_tsg['매수등락율'], bins=bins, labels=labels, right=False)
            df_rate = df_tsg.groupby('등락율구간', observed=True).agg({'수익금': 'sum'}).reset_index()
            colors = [color_profit if x >= 0 else color_loss for x in df_rate['수익금']]
            ax7.bar(range(len(df_rate)), df_rate['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax7.set_xticks(range(len(df_rate)))
            ax7.set_xticklabels(df_rate['등락율구간'], rotation=45)
            ax7.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax7.set_xlabel('등락율 구간 (%)')
            ax7.set_ylabel('총 수익금')
            ax7.set_title('등락율별 수익금')

        # 체결강도별
        ax8 = fig.add_subplot(gs[2, 2])
        if '매수체결강도' in df_tsg.columns:
            bins = [0, 80, 100, 120, 150, 200, 500]
            labels = ['~80', '80-100', '100-120', '120-150', '150-200', '200+']
            df_tsg['체결강도구간'] = pd.cut(df_tsg['매수체결강도'], bins=bins, labels=labels, right=False)
            df_ch = df_tsg.groupby('체결강도구간', observed=True).agg({'수익금': 'sum'}).reset_index()
            colors = [color_profit if x >= 0 else color_loss for x in df_ch['수익금']]
            ax8.bar(range(len(df_ch)), df_ch['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax8.set_xticks(range(len(df_ch)))
            ax8.set_xticklabels(df_ch['체결강도구간'], rotation=45)
            ax8.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax8.set_xlabel('체결강도 구간')
            ax8.set_ylabel('총 수익금')
            ax8.set_title('체결강도별 수익금')

        # ============ Chart 9: 거래품질점수별 수익금 ============
        ax9 = fig.add_subplot(gs[3, 0])
        if '거래품질점수' in df_tsg.columns:
            bins = [0, 30, 40, 50, 60, 70, 100]
            labels = ['~30', '30-40', '40-50', '50-60', '60-70', '70+']
            df_tsg['품질구간'] = pd.cut(df_tsg['거래품질점수'], bins=bins, labels=labels, right=False)
            df_qual = df_tsg.groupby('품질구간', observed=True).agg({'수익금': 'sum', '종목명': 'count'}).reset_index()
            df_qual.columns = ['품질구간', '수익금', '거래수']
            colors = [color_profit if x >= 0 else color_loss for x in df_qual['수익금']]
            bars = ax9.bar(range(len(df_qual)), df_qual['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax9.set_xticks(range(len(df_qual)))
            ax9.set_xticklabels(df_qual['품질구간'], rotation=45)
            ax9.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax9.set_xlabel('거래품질 점수')
            ax9.set_ylabel('총 수익금')
            ax9.set_title('거래품질 점수별 수익금 (NEW)')

            # 거래수 표시
            for i, (bar, cnt) in enumerate(zip(bars, df_qual['거래수'])):
                ax9.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=8)

        # ============ Chart 10: 위험도점수별 수익금 ============
        ax10 = fig.add_subplot(gs[3, 1])
        if '위험도점수' in df_tsg.columns:
            bins = [0, 20, 40, 60, 80, 100]
            labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
            df_tsg['위험도구간'] = pd.cut(df_tsg['위험도점수'], bins=bins, labels=labels, right=False)
            df_risk = df_tsg.groupby('위험도구간', observed=True).agg({'수익금': 'sum', '종목명': 'count'}).reset_index()
            df_risk.columns = ['위험도구간', '수익금', '거래수']
            colors = [color_profit if x >= 0 else color_loss for x in df_risk['수익금']]
            bars = ax10.bar(range(len(df_risk)), df_risk['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax10.set_xticks(range(len(df_risk)))
            ax10.set_xticklabels(df_risk['위험도구간'], rotation=45)
            ax10.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax10.set_xlabel('위험도 점수')
            ax10.set_ylabel('총 수익금')
            ax10.set_title('위험도 점수별 수익금 (ENHANCED)')

        # ============ Chart 11: 리스크조정수익률 분포 ============
        ax11 = fig.add_subplot(gs[3, 2])
        if '리스크조정수익률' in df_tsg.columns:
            profit_trades = df_tsg[df_tsg['수익금'] > 0]['리스크조정수익률']
            loss_trades = df_tsg[df_tsg['수익금'] <= 0]['리스크조정수익률']

            ax11.hist(profit_trades, bins=30, alpha=0.6, color=color_profit, label='이익 거래', edgecolor='black')
            ax11.hist(loss_trades, bins=30, alpha=0.6, color=color_loss, label='손실 거래', edgecolor='black')
            ax11.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
            ax11.set_xlabel('리스크 조정 수익률')
            ax11.set_ylabel('거래 수')
            ax11.set_title('리스크 조정 수익률 분포 (NEW)')
            ax11.legend(fontsize=9)

        # ============ Chart 12: 상관관계 히트맵 ============
        ax12 = fig.add_subplot(gs[4, 0])
        corr_columns = ['수익률', '매수등락율', '매수체결강도', '매수회전율', '보유시간']
        if '거래품질점수' in df_tsg.columns:
            corr_columns.append('거래품질점수')
        available_cols = [col for col in corr_columns if col in df_tsg.columns]

        if len(available_cols) >= 3:
            df_corr = df_tsg[available_cols].corr()
            im = ax12.imshow(df_corr.values, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
            ax12.set_xticks(range(len(available_cols)))
            ax12.set_yticks(range(len(available_cols)))
            ax12.set_xticklabels(available_cols, rotation=45, ha='right', fontsize=8)
            ax12.set_yticklabels(available_cols, fontsize=8)
            ax12.set_title('변수 간 상관관계')

            for i in range(len(available_cols)):
                for j in range(len(available_cols)):
                    ax12.text(j, i, f'{df_corr.values[i, j]:.2f}', ha='center', va='center', fontsize=7)

            plt.colorbar(im, ax=ax12, shrink=0.8)

        # ============ Chart 13: 손실/이익 거래 특성 비교 ============
        ax13 = fig.add_subplot(gs[4, 1])
        loss_trades = df_tsg[df_tsg['수익금'] < 0]
        profit_trades = df_tsg[df_tsg['수익금'] >= 0]

        compare_cols = ['매수등락율', '매수체결강도', '보유시간']
        if '거래품질점수' in df_tsg.columns:
            compare_cols.append('거래품질점수')
        available_cols = [c for c in compare_cols if c in df_tsg.columns]

        if len(available_cols) > 0 and len(loss_trades) > 0 and len(profit_trades) > 0:
            loss_means = [loss_trades[c].mean() for c in available_cols]
            profit_means = [profit_trades[c].mean() for c in available_cols]

            x = np.arange(len(available_cols))
            width = 0.35
            ax13.bar(x - width/2, loss_means, width, label='손실거래', color=color_loss, alpha=0.8)
            ax13.bar(x + width/2, profit_means, width, label='이익거래', color=color_profit, alpha=0.8)
            ax13.set_xticks(x)
            ax13.set_xticklabels(available_cols, rotation=45, ha='right', fontsize=9)
            ax13.set_ylabel('평균값')
            ax13.set_title('손실/이익 거래 특성 비교')
            ax13.legend(fontsize=9)

        # ============ Chart 14: 요약 통계 텍스트 ============
        ax14 = fig.add_subplot(gs[4, 2])
        ax14.axis('off')

        total_trades = len(df_tsg)
        total_profit = df_tsg['수익금'].sum()
        win_rate = (df_tsg['수익금'] > 0).mean() * 100
        avg_profit = df_tsg['수익률'].mean()

        summary_text = f"""
        === 분석 요약 ===

        총 거래 수: {total_trades:,}
        총 수익금: {total_profit:,}원
        승률: {win_rate:.1f}%
        평균 수익률: {avg_profit:.2f}%

        === 주요 발견 ===
        """

        if filter_results:
            top_filter = filter_results[0] if filter_results else None
            if top_filter and top_filter['수익개선금액'] > 0:
                summary_text += f"""
        최적 필터: {top_filter['필터명'][:25]}
        예상 개선: {top_filter['수익개선금액']:,}원
        통계적 유의성: {top_filter.get('유의함', 'N/A')}
                """

        if feature_importance:
            top_feature = feature_importance['top_features'][0] if feature_importance.get('top_features') else None
            if top_feature:
                summary_text += f"""
        가장 중요한 변수: {top_feature[0]}
        중요도: {top_feature[1]:.3f}
                """

        ax14.text(0.1, 0.9, summary_text, transform=ax14.transAxes, fontsize=10,
                 verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        # 저장 및 전송
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.tight_layout(rect=[0, 0.02, 1, 0.97])

        analysis_path = f"{GRAPH_PATH}/{save_file_name}_enhanced.png"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.savefig(analysis_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if teleQ is not None:
            teleQ.put(analysis_path)

        return analysis_path

    except Exception as e:
        print_exc()
        try:
            plt.close('all')
        except:
            pass
        return None


# ============================================================================
# 10. 전체 강화 분석 실행
# ============================================================================

def RunEnhancedAnalysis(df_tsg, save_file_name, teleQ=None):
    """
    강화된 전체 분석을 실행합니다.

    기능:
    1. 강화된 파생 지표 계산
    2. 통계적 유의성 검증 포함 필터 분석
    3. 최적 임계값 탐색
    4. 필터 조합 분석
    5. ML 기반 특성 중요도
    6. 기간별 필터 안정성
    7. 조건식 코드 자동 생성
    8. 강화된 시각화

    Returns:
        dict: 분석 결과 요약
    """
    result = {
        'enhanced_df': None,
        'filter_results': [],
        'optimal_thresholds': [],
        'filter_combinations': [],
        'feature_importance': None,
        'filter_stability': [],
        'generated_code': None,
        'charts': [],
        'recommendations': [],
        'csv_files': []
    }

    try:
        # 1. 강화된 파생 지표 계산
        df_enhanced = CalculateEnhancedDerivedMetrics(df_tsg)
        result['enhanced_df'] = df_enhanced

        # 2. 강화된 필터 효과 분석 (통계 검정 포함)
        filter_results = AnalyzeFilterEffectsEnhanced(df_enhanced)
        result['filter_results'] = filter_results

        # 3. 최적 임계값 탐색
        optimal_thresholds = FindAllOptimalThresholds(df_enhanced)
        result['optimal_thresholds'] = optimal_thresholds

        # 4. 필터 조합 분석
        filter_combinations = AnalyzeFilterCombinations(df_enhanced)
        result['filter_combinations'] = filter_combinations

        # 5. ML 특성 중요도
        feature_importance = AnalyzeFeatureImportance(df_enhanced)
        result['feature_importance'] = feature_importance

        # 6. 필터 안정성 검증
        filter_stability = AnalyzeFilterStability(df_enhanced)
        result['filter_stability'] = filter_stability

        # 7. 조건식 코드 생성
        generated_code = GenerateFilterCode(filter_results)
        result['generated_code'] = generated_code

        # 8. CSV 파일 저장
        # 상세 거래 기록
        detail_path = f"{GRAPH_PATH}/{save_file_name}_enhanced_detail.csv"
        df_enhanced.to_csv(detail_path, encoding='utf-8-sig', index=True)
        result['csv_files'].append(detail_path)

        # 필터 분석 결과
        if filter_results:
            filter_path = f"{GRAPH_PATH}/{save_file_name}_filter_analysis.csv"
            pd.DataFrame(filter_results).to_csv(filter_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(filter_path)

        # 최적 임계값
        if optimal_thresholds:
            threshold_path = f"{GRAPH_PATH}/{save_file_name}_optimal_thresholds.csv"
            pd.DataFrame(optimal_thresholds).to_csv(threshold_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(threshold_path)

        # 필터 조합
        if filter_combinations:
            combo_path = f"{GRAPH_PATH}/{save_file_name}_filter_combinations.csv"
            pd.DataFrame(filter_combinations).to_csv(combo_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(combo_path)

        # 필터 안정성
        if filter_stability:
            stability_path = f"{GRAPH_PATH}/{save_file_name}_filter_stability.csv"
            pd.DataFrame(filter_stability).to_csv(stability_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(stability_path)

        # 9. 강화된 차트 생성
        chart_path = PltEnhancedAnalysisCharts(df_enhanced, save_file_name, teleQ, filter_results, feature_importance)
        if chart_path:
            result['charts'].append(chart_path)

        # 10. 추천 메시지 생성
        recommendations = []

        # 통계적으로 유의한 필터
        significant_filters = [f for f in filter_results if f.get('유의함') == '예' and f['수익개선금액'] > 0][:3]
        for f in significant_filters:
            recommendations.append(f"[통계적 유의] {f['필터명']}: +{f['수익개선금액']:,}원 (p={f['p값']})")

        # 시너지 높은 조합
        high_synergy = [c for c in filter_combinations if c['시너지비율'] > 10][:2]
        for c in high_synergy:
            recommendations.append(f"[조합추천] {c['필터1'][:15]} + {c['필터2'][:15]}: 시너지 +{c['시너지효과']:,}원")

        # 안정적인 필터
        stable_filters = [f for f in filter_stability if f['안정성등급'] == '안정' and f['평균개선'] > 0][:2]
        for f in stable_filters:
            recommendations.append(f"[안정성] {f['필터명']}: 일관성 {f['일관성점수']}점")

        result['recommendations'] = recommendations

        # 11. 텔레그램 전송
        if teleQ is not None:
            # 요약 메시지
            if recommendations:
                msg = "📊 강화된 필터 분석 결과:\n\n" + "\n".join(recommendations)
                teleQ.put(msg)

            # 조건식 코드
            if generated_code and generated_code.get('summary'):
                code_msg = f"💡 자동 생성 필터 코드:\n총 {generated_code['summary']['total_filters']}개 필터\n예상 총 개선: {generated_code['summary']['total_improvement']:,}원"
                teleQ.put(code_msg)

    except Exception as e:
        print_exc()

    return result
