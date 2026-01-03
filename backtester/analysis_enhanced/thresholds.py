# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd

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
    profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)
    col_arr = df_tsg[column].to_numpy(dtype=np.float64)

    for threshold in thresholds:
        if direction == 'less':
            condition = col_arr < threshold
        else:
            condition = col_arr >= threshold

        excluded_count = int(np.sum(condition))
        remaining_count = total_trades - excluded_count
        if excluded_count == 0 or remaining_count == 0:
            continue

        excluded_profit = float(np.sum(profit_arr[condition]))
        improvement = -excluded_profit
        excluded_ratio = excluded_count / total_trades * 100
        remaining_winrate = (profit_arr[~condition] > 0).mean() * 100

        # 효율성 점수: 수익개선 / 제외거래수 (제외 거래당 개선 효과)
        efficiency = improvement / excluded_count if excluded_count > 0 else 0

        results.append({
            'threshold': round(threshold, 2),
            'improvement': int(improvement),
            'excluded_ratio': round(excluded_ratio, 1),
            'excluded_count': excluded_count,
            'remaining_count': remaining_count,
            'remaining_winrate': round(remaining_winrate, 1),
            'efficiency': round(efficiency, 0)
        })

    if not results:
        return None

    # 최적 임계값 선택 (수익개선 × 효율성 가중)
    df_results = pd.DataFrame(results)

    # 제외 비율이 너무 큰 경우(거의 거래를 안 하는 케이스)는 과적합/왜곡 위험이 커서 제한
    # - 기존 50% 제한은 "좋은 구간만 남기는" 범위 필터를 놓치는 경우가 있어 80%로 완화
    df_valid = df_results[df_results['excluded_ratio'] <= 80]

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

def FindOptimalRangeThresholds(df_tsg, column, mode='outside', n_bins=10, max_excluded_ratio=80):
    """
    특정 컬럼에 대해 "범위(구간)" 기반 필터를 탐색합니다.

    mode:
        - 'outside': 범위 밖 제외(= 범위 안에서만 매수)  → excluded = (x < low) or (x >= high)
        - 'inside' : 범위 안 제외(= 특정 구간만 회피)     → excluded = (low <= x < high)
    """
    if column not in df_tsg.columns:
        return None

    try:
        s = df_tsg[column]
        if not pd.api.types.is_numeric_dtype(s):
            return None
        values = s.dropna().to_numpy(dtype=np.float64)
    except Exception:
        return None

    if len(values) < 50:
        return None

    # 분위수 기반 경계값 생성(중복 제거)
    percentiles = np.linspace(0, 100, n_bins + 1)
    try:
        edges = np.nanpercentile(values, percentiles)
        edges = np.unique(edges)
    except Exception:
        return None

    if len(edges) < 4:
        return None

    # 전체 배열(NaN 포함)로 bin index 생성
    col_arr = df_tsg[column].to_numpy(dtype=np.float64)
    profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)
    total_profit = float(np.nansum(profit_arr))
    total_trades = int(len(col_arr))

    # NaN은 bin=-1로 처리
    valid_mask = np.isfinite(col_arr)
    valid_vals = col_arr[valid_mask]
    if len(valid_vals) == 0:
        return None

    # bin: 0..k-2 (edges 길이 k)
    # bins: [edges[i], edges[i+1]) 형태로 맞추기 위해 side='right'를 사용(경계값은 상위 bin으로)
    bin_idx = np.searchsorted(edges[1:-1], valid_vals, side='right')
    bin_count = int(len(edges) - 1)
    counts = np.bincount(bin_idx, minlength=bin_count).astype(np.int64)
    profit_sums = np.bincount(bin_idx, weights=profit_arr[valid_mask], minlength=bin_count).astype(np.float64)
    win_counts = np.bincount(bin_idx, weights=(profit_arr[valid_mask] > 0).astype(np.int64), minlength=bin_count).astype(np.int64)

    # prefix sums for O(k^2) interval evaluation
    pc = np.concatenate(([0], np.cumsum(counts)))
    pp = np.concatenate(([0.0], np.cumsum(profit_sums)))
    pw = np.concatenate(([0], np.cumsum(win_counts)))

    best = None
    k = bin_count

    for i in range(k):
        for j in range(i, k):
            low = float(edges[i])
            high = float(edges[j + 1]) if (j + 1) < len(edges) else float(edges[-1])
            if not np.isfinite(low) or not np.isfinite(high) or high <= low:
                continue

            in_count = int(pc[j + 1] - pc[i])
            if in_count <= 0:
                continue

            in_profit = float(pp[j + 1] - pp[i])
            in_wins = int(pw[j + 1] - pw[i])

            if mode == 'inside':
                excluded_count = in_count
                excluded_profit = in_profit
                remaining_count = total_trades - excluded_count
                remaining_wins = int(np.sum(profit_arr > 0)) - in_wins
            else:
                # outside
                excluded_count = total_trades - in_count
                excluded_profit = total_profit - in_profit
                remaining_count = in_count
                remaining_wins = in_wins

            if excluded_count <= 0 or remaining_count <= 0:
                continue

            excluded_ratio = excluded_count / total_trades * 100
            if excluded_ratio > max_excluded_ratio:
                continue

            improvement = -excluded_profit
            if improvement <= 0:
                continue

            remaining_winrate = (remaining_wins / remaining_count * 100.0) if remaining_count > 0 else 0.0
            efficiency = improvement / excluded_count if excluded_count > 0 else 0.0

            candidate = {
                'column': column,
                'direction': 'range',
                'mode': mode,
                'low': round(low, 6),
                'high': round(high, 6),
                'improvement': int(improvement),
                'excluded_ratio': round(excluded_ratio, 1),
                'excluded_count': int(excluded_count),
                'remaining_winrate': round(remaining_winrate, 1),
                'efficiency': round(efficiency, 0),
            }

            if best is None:
                best = candidate
                continue

            # 우선순위: 효율성 → 개선금액(동률 시)
            if candidate['efficiency'] > best.get('efficiency', 0):
                best = candidate
            elif candidate['efficiency'] == best.get('efficiency', 0) and candidate['improvement'] > best.get('improvement', 0):
                best = candidate

    return best

def FindAllOptimalThresholds(df_tsg):
    """
    모든 주요 컬럼에 대해 최적 임계값을 탐색합니다.

    Returns:
        list: 각 컬럼별 최적 임계값 정보
    """
    results = []

    def _fmt_eok_to_korean(value_eok):
        """
        억 단위 숫자를 사람이 읽기 쉬운 라벨로 변환합니다.
        - 1조(=10,000억) 미만: 억 단위
        - 1조 이상: 조 단위(정수)
        """
        try:
            v = float(value_eok)
        except Exception:
            return str(value_eok)
        if v >= 10000:
            return f"{int(round(v / 10000))}조"
        return f"{int(round(v))}억"

    def _detect_trade_money_unit(series):
        # STOM: 당일거래대금 단위는 "백만"으로 고정(요구사항).
        return '백만'

    trade_money_unit = None
    if 'B_당일거래대금' in df_tsg.columns:
        trade_money_unit = _detect_trade_money_unit(df_tsg['B_당일거래대금'])

    # 분석할 컬럼과 방향 정의
    columns_config = [
        ('B_등락율', 'greater', 'B_등락율 {:.0f}% 이상 제외'),
        ('B_등락율', 'less', 'B_등락율 {:.0f}% 미만 제외'),
        ('B_체결강도', 'less', 'B_체결강도 {:.0f} 미만 제외'),
        ('B_체결강도', 'greater', 'B_체결강도 {:.0f} 이상 제외'),
        ('B_당일거래대금', 'less', 'B_당일거래대금 {:.0f}억 미만 제외'),
        ('시가총액', 'less', '시가총액 {:.0f}억 미만 제외'),
        ('시가총액', 'greater', '시가총액 {:.0f}억 이상 제외'),
        ('B_호가잔량비', 'less', 'B_호가잔량비 {:.0f}% 미만 제외'),
        ('B_스프레드', 'greater', 'B_스프레드 {:.2f}% 이상 제외'),
    ]

    # 파생 지표도 분석
    if 'B_위험도점수' in df_tsg.columns:
        columns_config.append(('B_위험도점수', 'greater', 'B_위험도점수 {:.0f}점 이상 제외'))

    if 'B_거래품질점수' in df_tsg.columns:
        columns_config.append(('B_거래품질점수', 'less', 'B_거래품질점수 {:.0f}점 미만 제외'))

    if 'B_모멘텀점수' in df_tsg.columns:
        columns_config.append(('B_모멘텀점수', 'less', 'B_모멘텀점수 {:.1f} 미만 제외'))


    for column, direction, name_template in columns_config:
        result = FindOptimalThresholds(df_tsg, column, direction)
        if result and result['improvement'] > 0:
            raw_thr = result.get('optimal_threshold')
            result['임계값(원본)'] = raw_thr

            # 표시용 라벨 정리(단위/스케일 혼동 방지)
            if column == 'B_당일거래대금':
                unit = trade_money_unit or '백만'
                try:
                    thr_eok = float(raw_thr) / 100.0 if unit == '백만' else float(raw_thr)
                except Exception:
                    thr_eok = raw_thr
                result['임계값(표시)'] = _fmt_eok_to_korean(thr_eok)
                result['원본단위'] = unit
                result['필터명'] = f"B_당일거래대금 {result['임계값(표시)']} 미만 제외"
            elif column == '시가총액':
                try:
                    thr_eok = float(raw_thr)
                except Exception:
                    thr_eok = raw_thr
                result['임계값(표시)'] = _fmt_eok_to_korean(thr_eok)
                suffix = '미만 제외' if direction == 'less' else '이상 제외'
                result['필터명'] = f"시가총액 {result['임계값(표시)']} {suffix}"

            else:
                result['필터명'] = name_template.format(raw_thr)
            results.append(result)

    # 수익 개선금액 기준 정렬
    results.sort(key=lambda x: x['improvement'], reverse=True)

    return results
