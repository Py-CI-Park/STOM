# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from scipy import stats

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
