# -*- coding: utf-8 -*-
"""
Statistical Analysis Module

통계적 유의성 검정 및 다중 검정 보정 기능을 제공합니다.
"""

from typing import List, Dict, Optional, Literal
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


# =============================================================================
# 다중 검정 보정 (Multiple Testing Correction)
# =============================================================================

def apply_multiple_testing_correction(
    filter_results: List[Dict],
    method: Literal['bonferroni', 'holm', 'fdr_bh', 'none'] = 'bonferroni',
    alpha: float = 0.05,
) -> List[Dict]:
    """
    다중 가설 검정에 대한 p-값 보정을 적용합니다.

    필터를 여러 개 동시에 테스트할 때 false positive 가능성이 증가합니다.
    이 함수는 p-값을 보정하여 실제로 유의미한 필터만 선택되도록 합니다.

    Methods:
    - bonferroni: 가장 보수적. p_adj = p * n_tests. False positive 최소화.
    - holm: Step-down 방식. Bonferroni보다 덜 보수적이면서 FWER 제어.
    - fdr_bh: Benjamini-Hochberg FDR 제어. 가장 관대. 탐색적 분석에 적합.
    - none: 보정 없음 (기존 동작 유지)

    Args:
        filter_results: 필터 분석 결과 리스트. 각 dict에 'p값' 키 필요.
        method: 보정 방법 ('bonferroni' | 'holm' | 'fdr_bh' | 'none')
        alpha: 유의 수준 (기본값 0.05)

    Returns:
        보정된 필터 결과 리스트. 각 dict에 'p값_adjusted', '유의함_adjusted' 추가.

    Example:
        >>> results = [{'필터명': 'A', 'p값': 0.01}, {'필터명': 'B', 'p값': 0.04}]
        >>> corrected = apply_multiple_testing_correction(results, method='bonferroni')
        >>> # 2개 테스트 시: A의 p_adj=0.02 (유의), B의 p_adj=0.08 (비유의)
    """
    if method == 'none' or not filter_results:
        return filter_results

    # p값이 있는 필터만 추출
    p_values = []
    p_indices = []
    for i, f in enumerate(filter_results):
        p = f.get('p값')
        if p is not None and not np.isnan(p):
            p_values.append(float(p))
            p_indices.append(i)

    n_tests = len(p_values)
    if n_tests == 0:
        return filter_results

    # 보정 적용
    adjusted = _apply_correction(p_values, method, n_tests)

    # 결과 업데이트
    for idx, p_adj in zip(p_indices, adjusted):
        filter_results[idx]['p값_adjusted'] = round(p_adj, 6)
        filter_results[idx]['유의함_adjusted'] = '예' if p_adj < alpha else '아니오'
        filter_results[idx]['보정방법'] = method
        filter_results[idx]['검정수'] = n_tests

    return filter_results


def _apply_correction(p_values: List[float], method: str, n_tests: int) -> List[float]:
    """
    실제 p-값 보정을 수행합니다.
    """
    p_arr = np.array(p_values)

    if method == 'bonferroni':
        # 가장 보수적: p * n
        adjusted = np.minimum(1.0, p_arr * n_tests)

    elif method == 'holm':
        # Holm step-down: 정렬 후 순위별 보정
        sorted_idx = np.argsort(p_arr)
        adjusted = np.zeros(n_tests)
        cummax = 0.0
        for rank, idx in enumerate(sorted_idx):
            adj_p = p_arr[idx] * (n_tests - rank)
            cummax = max(cummax, adj_p)  # monotonicity 보장
            adjusted[idx] = min(1.0, cummax)

    elif method == 'fdr_bh':
        # Benjamini-Hochberg FDR 제어
        sorted_idx = np.argsort(p_arr)
        adjusted = np.zeros(n_tests)
        cummin = 1.0
        for rank in range(n_tests - 1, -1, -1):
            idx = sorted_idx[rank]
            adj_p = p_arr[idx] * n_tests / (rank + 1)
            cummin = min(cummin, adj_p)  # monotonicity 보장
            adjusted[idx] = min(1.0, cummin)

    else:
        adjusted = p_arr  # no correction

    return adjusted.tolist()


def get_correction_summary(filter_results: List[Dict]) -> Dict:
    """
    다중 검정 보정 적용 결과 요약을 반환합니다.

    Args:
        filter_results: 보정이 적용된 필터 결과 리스트

    Returns:
        dict: 요약 정보
            - total_tests: 총 검정 수
            - significant_before: 보정 전 유의한 필터 수
            - significant_after: 보정 후 유의한 필터 수
            - false_discovery_reduction: 감소된 false discovery 수
            - method: 사용된 보정 방법
    """
    if not filter_results:
        return {}

    method = filter_results[0].get('보정방법', 'none')
    n_tests = filter_results[0].get('검정수', len(filter_results))

    sig_before = sum(1 for f in filter_results if f.get('유의함') == '예')
    sig_after = sum(1 for f in filter_results if f.get('유의함_adjusted') == '예')

    return {
        'total_tests': n_tests,
        'significant_before': sig_before,
        'significant_after': sig_after,
        'false_discovery_reduction': sig_before - sig_after,
        'reduction_rate': round((sig_before - sig_after) / max(1, sig_before) * 100, 1),
        'method': method,
    }


# =============================================================================
# 통계적 유의성 검정
# =============================================================================

def CalculateStatisticalSignificance(filtered_out, remaining):
    """
    필터 효과의 통계적 유의성을 계산합니다.

    Args:
        filtered_out: 제외되는 거래 DataFrame 또는 수익금 배열/시리즈
        remaining: 남는 거래 DataFrame 또는 수익금 배열/시리즈

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
        def _to_profit_array(obj):
            if isinstance(obj, pd.DataFrame):
                if '수익금' in obj.columns:
                    return obj['수익금'].to_numpy(dtype=np.float64)
                return obj.to_numpy(dtype=np.float64).reshape(-1)
            if isinstance(obj, pd.Series):
                return obj.to_numpy(dtype=np.float64)
            return np.asarray(obj, dtype=np.float64)

        # 두 그룹의 수익금
        group1 = _to_profit_array(filtered_out)
        group2 = _to_profit_array(remaining)

        if group1.size < 2 or group2.size < 2:
            return result

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
