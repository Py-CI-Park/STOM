# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from itertools import combinations

from backtester.analysis.metric_registry import ANALYSIS_ONLY_COLUMNS, BUY_TIME_FILTER_COLUMNS

from .config import (
    FILTER_MAX_EXCLUSION_RATIO,
    FILTER_MIN_REMAINING_TRADES,
)
from .stats import (
    CalculateStatisticalSignificance,
    CalculateEffectSizeInterpretation,
)
from .thresholds import (
    FindOptimalThresholds,
    FindOptimalRangeThresholds,
)

def AnalyzeFilterCombinations(df_tsg, single_filters=None, max_filters=3, top_n=10):
    """
    필터 조합의 시너지 효과를 분석합니다.

    Args:
        df_tsg: DataFrame
        max_filters: 최대 조합 필터 수 (2 또는 3)
        top_n: 분석할 상위 단일 필터 수

    Returns:
        list: 필터 조합 분석 결과
    """
    # 먼저 단일 필터 분석(이미 계산된 결과가 있으면 재사용)
    if single_filters is None:
        single_filters = AnalyzeFilterEffectsEnhanced(df_tsg)

    if not single_filters:
        return []

    # 상위 필터만 조합 분석 (계산량 제한)
    top_filters = [f for f in single_filters if f['수익개선금액'] > 0][:top_n]

    if len(top_filters) < 2:
        return []

    total_trades = len(df_tsg)
    profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)

    # 조건식은 조합 루프에서 반복 eval 되면 비용이 커서, 상위 필터에 대해서만 미리 평가해둡니다.
    safe_globals = {"__builtins__": {}}
    safe_locals = {"df_tsg": df_tsg, "np": np, "pd": pd}
    cond_arrays = []
    for f in top_filters:
        try:
            cond_expr = f.get('조건식')
            if not cond_expr:
                cond_arrays.append(None)
                continue
            cond = eval(cond_expr, safe_globals, safe_locals)
            cond_arr = cond.to_numpy(dtype=bool) if hasattr(cond, 'to_numpy') else np.asarray(cond, dtype=bool)
            cond_arrays.append(cond_arr)
        except:
            cond_arrays.append(None)

    combination_results = []

    # 2개 필터 조합
    for f1, f2 in combinations(range(len(top_filters)), 2):
        filter1 = top_filters[f1]
        filter2 = top_filters[f2]

        try:
            cond1 = cond_arrays[f1]
            cond2 = cond_arrays[f2]
            if cond1 is None or cond2 is None:
                continue

            combined_condition = cond1 | cond2  # OR 조건 (둘 중 하나라도 해당되면 제외)
            excluded_count = int(np.sum(combined_condition))
            remaining_count = total_trades - excluded_count
            if excluded_count == 0 or remaining_count == 0:
                continue

            improvement = -float(np.sum(profit_arr[combined_condition]))
            excluded_ratio = excluded_count / total_trades * 100

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
                '잔여승률': round((profit_arr[~combined_condition] > 0).mean() * 100, 1),
                '잔여거래수': remaining_count,
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
                cond1 = cond_arrays[f1]
                cond2 = cond_arrays[f2]
                cond3 = cond_arrays[f3]
                if cond1 is None or cond2 is None or cond3 is None:
                    continue

                combined_condition = cond1 | cond2 | cond3

                excluded_count = int(np.sum(combined_condition))
                remaining_count = total_trades - excluded_count
                if excluded_count == 0 or remaining_count == 0:
                    continue

                improvement = -float(np.sum(profit_arr[combined_condition]))
                excluded_ratio = excluded_count / total_trades * 100

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
                    '잔여승률': round((profit_arr[~combined_condition] > 0).mean() * 100, 1),
                    '잔여거래수': remaining_count,
                    '권장': '★★★' if synergy_ratio > 20 else ('★★' if synergy_ratio > 0 else ''),
                })
            except:
                continue

    # 조합 적용 시 개선금액 기준 정렬(내림차순)
    # - "현재 조건식에 불필요한 조건"을 찾기 위해, 최종 개선 효과가 큰 조합을 상단에 배치
    combination_results.sort(
        key=lambda x: (x.get('조합개선', 0), x.get('시너지효과', 0), x.get('시너지비율', 0)),
        reverse=True
    )

    return combination_results

def AnalyzeFilterEffectsEnhanced(df_tsg, allow_ml_filters: bool = True):
    """
    강화된 필터 효과 분석 (통계적 유의성 + 동적 임계값 포함)

    Args:
        df_tsg: DataFrame
        allow_ml_filters: True면 *_ML 컬럼(B_손실확률_ML/B_위험도_ML 등)도 필터 후보로 포함합니다.


    Returns:
        list: 필터 효과 분석 결과 (통계 검정 결과 포함)
    """
    filter_results = []
    total_profit = df_tsg['수익금'].sum()
    total_trades = len(df_tsg)

    if total_trades == 0:
        return filter_results

    profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)
    return_arr = df_tsg['수익률'].to_numpy(dtype=np.float64) if '수익률' in df_tsg.columns else None

    # === 필터 조건 정의 (조건식 포함) ===
    filter_conditions = []

    def _fmt_eok_to_korean(value_eok):
        """
        억 단위 숫자를 사람이 읽기 쉬운 라벨로 변환합니다.
        - 1조(=10,000억) 미만: 억 단위
        - 1조 이상: 조 단위(정수)
        """
        try:
            v = float(value_eok)
        except:
            return str(value_eok)
        if v >= 10000:
            return f"{int(round(v / 10000))}조"
        return f"{int(round(v))}억"

    def _detect_trade_money_unit(series):
        # STOM: 당일거래대금 단위는 "백만"으로 고정(요구사항).
        return '백만'

    # 1. 시간대 필터
    if 'B_시' in df_tsg.columns:
        for hour in sorted(df_tsg['B_시'].unique()):
            filter_conditions.append({
                '필터명': f'시간대 {hour}시 제외',
                '조건': df_tsg['B_시'] == hour,
                '조건식': f"df_tsg['B_시'] == {hour}",
                '분류': '시간대',
                '코드': f'B_시 != {hour}'
            })

    # 2. 전 컬럼 스캔: "매수 시점에 알 수 있는 변수" 중심으로 동적 임계값/범위 필터 탐색
    # - 목적: 매수시점 모든 변수(가능한 범위)를 검토하고, 개선 효과가 큰 필터를 추천
    # - 원칙(룩어헤드 방지): 매도* / 변화량(*변화, *변화율) / 보유시간 / 수익결과 기반 컬럼은 제외

    trade_money_unit = _detect_trade_money_unit(df_tsg['B_당일거래대금']) if 'B_당일거래대금' in df_tsg.columns else '백만'

    def _fmt_number(v, decimals=2):
        try:
            x = float(v)
        except Exception:
            return str(v)
        if abs(x - round(x)) < 1e-9:
            return f"{int(round(x))}"
        if abs(x) >= 1000:
            return f"{x:,.0f}"
        s = f"{x:.{decimals}f}"
        return s.rstrip('0').rstrip('.')

    def _fmt_trade_money(raw_value):
        # raw_value: df_tsg['B_당일거래대금'] 원본 단위(권장: 백만)
        try:
            rv = float(raw_value)
        except Exception:
            return str(raw_value)
        eok = rv / 100.0 if trade_money_unit == '백만' else rv
        return _fmt_eok_to_korean(eok)

    def _categorize(col: str) -> str:
        if col == '시가총액':
            return '시가총액'
        if '위험도' in col:
            return '위험신호'
        if '품질' in col:
            return '품질'
        if '모멘텀' in col:
            return '모멘텀'
        if '등락' in col:
            return '등락율'
        if '체결강도' in col:
            return '체결강도'
        if '거래대금' in col:
            return '거래대금'
        if '회전율' in col:
            return '회전율'
        if '전일' in col:
            return '전일비'
        if '스프레드' in col:
            return '스프레드'
        if '호가' in col or '잔량' in col:
            return '호가'
        if '초당' in col:
            return '초당'
        return '기타'

    def _is_buytime_candidate(col: str) -> bool:
        # "매도"로 시작하더라도, 매수 시점 호가/잔량에서 파생된 변수는 예외적으로 허용합니다.
        # (예: B_매도잔량_매수잔량_비율 = 매수 시점의 매도/매수 잔량 비율)
        allow_sellside_buytime_cols = {
            'B_매도잔량_매수잔량_비율',
            '매도잔량_매수잔량_비율',
        }
        explicit_excludes = {
            'S_당일거래대금_매수매도_비율',
            'B_금액',
            'B_매수금액',
            '매수금액',
        }
        if col in ANALYSIS_ONLY_COLUMNS:
            return False
        if col in explicit_excludes:
            return False
        if col.endswith('_ML'):
            return bool(allow_ml_filters)
        if col in (
            '수익금', '수익률', '보유시간',
            'B_시간', 'S_시간', 'B_일자', 'B_추가매수시간', 'S_조건',
            '매수시간', '매도시간', '매수일자', '추가매수시간', '매도조건',
        ):
            return False
        if col.startswith('S_') and col not in allow_sellside_buytime_cols:
            return False
        if col.startswith('매도') and col not in allow_sellside_buytime_cols:
            return False
        if col.startswith('수익금'):
            return False
        if col in (
            '이익금액', '손실금액', '이익여부',
            'B_시간대평균수익률', 'B_타이밍점수', 'B_리스크조정수익률',
            '연속이익', '연속손실', 'B_매수매도위험도점수',
        ):
            return False
        if '매도시' in col:
            return False
        if '변화' in col:
            return False
        # 시간 컬럼은 별도(시간대 필터)로 처리
        if col in ('B_시', 'B_분', 'B_초', '매수시', '매수분', '매수초'):
            return False
        if col.startswith('매수'):
            return True
        if col in BUY_TIME_FILTER_COLUMNS:
            return True
        return False

    candidate_cols = []
    for col in df_tsg.columns:
        col = str(col)
        if (not allow_ml_filters) and col.endswith('_ML'):
            continue
        if not _is_buytime_candidate(col):
            continue
        try:
            if not pd.api.types.is_numeric_dtype(df_tsg[col]):
                continue
        except Exception:
            continue
        candidate_cols.append(col)

    # 컬럼별로 최적 임계값(less/greater) + 범위 필터를 제한적으로 추가
    for col in sorted(candidate_cols):
        try:
            col_series = df_tsg[col]
            if col_series.notna().sum() < 50:
                continue
            if col_series.nunique(dropna=True) < 5:
                continue

            category = _categorize(col)

            # 1) 단일 임계값(미만 제외 / 이상 제외)
            for direction in ('less', 'greater'):
                res = FindOptimalThresholds(df_tsg, col, direction=direction, n_splits=20)
                if not res or res.get('improvement', 0) <= 0:
                    continue

                thr = float(res.get('optimal_threshold'))
                col_arr = col_series.to_numpy(dtype=np.float64)

                if direction == 'less':
                    cond_arr = col_arr < thr
                    cond_expr = f"df_tsg['{col}'] < {round(thr, 6)}"
                    keep_code = f"({col} >= {round(thr, 6)})"
                    suffix = '미만 제외'
                else:
                    cond_arr = col_arr >= thr
                    cond_expr = f"df_tsg['{col}'] >= {round(thr, 6)}"
                    keep_code = f"({col} < {round(thr, 6)})"
                    suffix = '이상 제외'

                if col == 'B_당일거래대금':
                    thr_label = _fmt_trade_money(thr)
                    name = f"B_당일거래대금 {thr_label} {suffix}"
                    keep_code = f"{keep_code}  # 단위:{trade_money_unit}(≈{thr_label})"
                elif col == '시가총액':
                    name = f"시가총액 {_fmt_eok_to_korean(thr)} {suffix}"
                elif col == 'B_위험도점수':
                    name = f"B_위험도점수 {thr:.0f}점 {suffix}"
                elif col == 'B_거래품질점수':
                    name = f"B_거래품질점수 {thr:.0f}점 {suffix}"
                else:
                    name = f"{col} {_fmt_number(thr)} {suffix}"

                filter_conditions.append({
                    '필터명': name,
                    '조건': cond_arr,
                    '조건식': cond_expr,
                    '분류': category,
                    '코드': keep_code,
                    '탐색기반': f"최적임계({direction})",
                })

            # 2) 범위 필터(하한/상한): outside(범위 밖 제외) / inside(구간 제외)
            for mode in ('outside', 'inside'):
                r = FindOptimalRangeThresholds(df_tsg, col, mode=mode, n_bins=10, max_excluded_ratio=80)
                if not r or r.get('improvement', 0) <= 0:
                    continue

                low = float(r['low'])
                high = float(r['high'])
                col_arr = col_series.to_numpy(dtype=np.float64)
                finite = col_arr[np.isfinite(col_arr)]
                if len(finite) == 0:
                    continue
                col_min = float(np.min(finite))
                col_max = float(np.max(finite))
                # 양쪽 경계가 모두 "내부"에 있어야 진짜 범위 필터(= one-sided 중복 방지)
                eps = 1e-12
                if not (low > col_min + eps and high < col_max - eps):
                    continue

                if mode == 'outside':
                    # 범위 밖 제외 → 범위 안에서만 매수
                    cond_arr = (col_arr < low) | (col_arr >= high)
                    cond_expr = f"(df_tsg['{col}'] < {round(low, 6)}) | (df_tsg['{col}'] >= {round(high, 6)})"
                    keep_code = f"(({col} >= {round(low, 6)}) and ({col} < {round(high, 6)}))"
                    suffix = '범위 밖 제외(범위만 매수)'
                else:
                    # 범위 안 제외 → 특정 구간 회피
                    cond_arr = (col_arr >= low) & (col_arr < high)
                    cond_expr = f"(df_tsg['{col}'] >= {round(low, 6)}) & (df_tsg['{col}'] < {round(high, 6)})"
                    keep_code = f"(({col} < {round(low, 6)}) or ({col} >= {round(high, 6)}))"
                    suffix = '구간 제외'

                if col == 'B_당일거래대금':
                    lo_label = _fmt_trade_money(low)
                    hi_label = _fmt_trade_money(high)
                    name = f"B_당일거래대금 {lo_label}~{hi_label} {suffix}"
                    keep_code = f"{keep_code}  # 단위:{trade_money_unit}(≈{lo_label}~{hi_label})"
                elif col == '시가총액':
                    name = f"시가총액 {_fmt_eok_to_korean(low)}~{_fmt_eok_to_korean(high)} {suffix}"
                elif col == 'B_위험도점수':
                    name = f"B_위험도점수 {low:.0f}~{high:.0f} {suffix}"
                else:
                    name = f"{col} {_fmt_number(low)}~{_fmt_number(high)} {suffix}"

                filter_conditions.append({
                    '필터명': name,
                    '조건': cond_arr,
                    '조건식': cond_expr,
                    '분류': category,
                    '코드': keep_code,
                    '탐색기반': f"범위({mode})",
                })
        except Exception:
            continue

    # (룩어헤드 제거) 급락신호/매도-매수 변화량 기반 지표는 매도 시점 확정 정보이므로
    # "매수 진입 필터" 추천 대상에서 제외합니다.

    # === 각 필터 효과 계산 (통계 검정 포함) ===
    for fc in filter_conditions:
        try:
            cond = fc['조건']
            cond_arr = cond.to_numpy(dtype=bool) if hasattr(cond, 'to_numpy') else np.asarray(cond, dtype=bool)
            filtered_count = int(np.sum(cond_arr))
            remaining_count = total_trades - filtered_count

            if filtered_count == 0 or remaining_count == 0:
                continue

            filtered_profit = float(np.sum(profit_arr[cond_arr]))
            remaining_profit = float(total_profit - filtered_profit)

            improvement = -filtered_profit

            # 통계적 유의성 검증
            stat_result = CalculateStatisticalSignificance(profit_arr[cond_arr], profit_arr[~cond_arr])
            effect_interpretation = CalculateEffectSizeInterpretation(stat_result['effect_size'])

            # 제외 거래의 특성 분석
            if return_arr is not None:
                filtered_avg_profit = float(np.nanmean(return_arr[cond_arr])) if filtered_count > 0 else 0.0
                remaining_avg_profit = float(np.nanmean(return_arr[~cond_arr])) if remaining_count > 0 else 0.0
            else:
                filtered_avg_profit = 0.0
                remaining_avg_profit = 0.0

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
                '제외거래승률': round((profit_arr[cond_arr] > 0).mean() * 100, 1) if filtered_count > 0 else 0.0,
                '잔여거래승률': round((profit_arr[~cond_arr] > 0).mean() * 100, 1) if remaining_count > 0 else 0.0,
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

def AnalyzeFilterEffectsLookahead(df_tsg):
    """
    (진단용) 매도 시점 확정 정보까지 포함한 필터 효과 분석.

    중요:
    - 이 분석은 매도 시점 데이터/변화량/보유시간 등 룩어헤드가 포함될 수 있으므로,
      실거래용 "매수 진입 필터 추천/자동 조건식 생성"에는 사용하지 않습니다.
    - 목적은 '손실 거래에서 사후적으로 어떤 지표가 같이 나왔는지'를 빠르게 파악하기 위함입니다.
    """
    filter_results = []
    if df_tsg is None or len(df_tsg) == 0:
        return filter_results
    if '수익금' not in df_tsg.columns:
        return filter_results

    total_trades = int(len(df_tsg))
    total_profit = float(df_tsg['수익금'].sum())
    profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)
    return_arr = df_tsg['수익률'].to_numpy(dtype=np.float64) if '수익률' in df_tsg.columns else None

    def _fmt_eok_to_korean(value_eok):
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
    if 'S_당일거래대금' in df_tsg.columns:
        trade_money_unit = _detect_trade_money_unit(df_tsg['S_당일거래대금'])
    elif 'B_당일거래대금' in df_tsg.columns:
        trade_money_unit = _detect_trade_money_unit(df_tsg['B_당일거래대금'])
    else:
        trade_money_unit = '백만'

    def _fmt_trade_money(raw_value):
        try:
            rv = float(raw_value)
        except Exception:
            return str(raw_value)
        eok = rv / 100.0 if trade_money_unit == '백만' else rv
        return _fmt_eok_to_korean(eok)

    # 사후 진단용으로 의미 있는 대표 컬럼만 선정(과도한 계산/과적합 방지)
    candidate_cols = [
        # 매도 확정 정보/변화량
        'B_매수매도위험도점수', '보유시간',
        '등락율변화', '체결강도변화', '거래대금변화율', '체결강도변화율', '호가잔량비변화',
        '급락신호', '매도세증가', '거래량급감',
        # 매도 시점 스냅샷
        'S_등락율', 'S_체결강도', 'S_당일거래대금', 'S_전일비', 'S_회전율', 'S_호가잔량비', 'S_스프레드',
    ]

    filter_conditions = []
    for col in candidate_cols:
        if col not in df_tsg.columns:
            continue
        s = df_tsg[col]

        # bool/flag 컬럼은 True 제외만 검사
        if pd.api.types.is_bool_dtype(s) or str(s.dtype) == 'bool':
            cond_arr = s.to_numpy(dtype=bool)
            excluded_count = int(np.sum(cond_arr))
            if excluded_count == 0 or excluded_count == total_trades:
                continue
            filter_conditions.append({
                '필터명': f"{col} True 제외(사후진단)",
                '조건': cond_arr,
                '조건식': f"df_tsg['{col}'] == True",
                '분류': '사후진단',
                '코드': f"# (진단용) {col} == True 제외",
            })
            continue

        if not pd.api.types.is_numeric_dtype(s):
            continue

        # one-sided 임계값(미만/이상)만(사후진단이므로 단순/빠르게)
        for direction in ('less', 'greater'):
            res = FindOptimalThresholds(df_tsg, col, direction=direction, n_splits=20)
            if not res or res.get('improvement', 0) <= 0:
                continue

            thr = float(res.get('optimal_threshold'))
            col_arr = s.to_numpy(dtype=np.float64)

            if direction == 'less':
                cond_arr = col_arr < thr
                cond_expr = f"df_tsg['{col}'] < {round(thr, 6)}"
                keep_code = f"({col} >= {round(thr, 6)})"
                suffix = '미만 제외'
            else:
                cond_arr = col_arr >= thr
                cond_expr = f"df_tsg['{col}'] >= {round(thr, 6)}"
                keep_code = f"({col} < {round(thr, 6)})"
                suffix = '이상 제외'

            if col in ('B_당일거래대금', 'S_당일거래대금'):
                thr_label = _fmt_trade_money(thr)
                name = f"{col} {thr_label} {suffix}(사후진단)"
                keep_code = f"{keep_code}  # 단위:{trade_money_unit}(≈{thr_label})"
            elif col == '시가총액':
                name = f"{col} {_fmt_eok_to_korean(thr)} {suffix}(사후진단)"
            else:
                name = f"{col} {thr:.2f} {suffix}(사후진단)"

            filter_conditions.append({
                '필터명': name,
                '조건': cond_arr,
                '조건식': cond_expr,
                '분류': '사후진단',
                '코드': keep_code,
            })

    for fc in filter_conditions:
        try:
            cond_arr = fc['조건']
            cond_arr = cond_arr.to_numpy(dtype=bool) if hasattr(cond_arr, 'to_numpy') else np.asarray(cond_arr, dtype=bool)
            filtered_count = int(np.sum(cond_arr))
            remaining_count = total_trades - filtered_count
            if filtered_count == 0 or remaining_count == 0:
                continue

            filtered_profit = float(np.sum(profit_arr[cond_arr]))
            remaining_profit = float(total_profit - filtered_profit)
            improvement = -filtered_profit

            # 통계 검정(가능하면 동일 포맷 유지)
            stat_result = CalculateStatisticalSignificance(profit_arr[cond_arr], profit_arr[~cond_arr])
            effect_interpretation = CalculateEffectSizeInterpretation(stat_result['effect_size'])

            if return_arr is not None:
                filtered_avg_profit = float(np.nanmean(return_arr[cond_arr])) if filtered_count > 0 else 0.0
                remaining_avg_profit = float(np.nanmean(return_arr[~cond_arr])) if remaining_count > 0 else 0.0
            else:
                filtered_avg_profit = 0.0
                remaining_avg_profit = 0.0

            filter_results.append({
                '분류': fc.get('분류', '사후진단'),
                '필터명': fc.get('필터명', ''),
                '조건식': fc.get('조건식', ''),
                '적용코드': fc.get('코드', ''),
                '제외거래수': filtered_count,
                '제외비율': round(filtered_count / total_trades * 100, 1),
                '제외거래수익금': int(filtered_profit),
                '제외평균수익률': round(filtered_avg_profit, 2),
                '잔여거래수': remaining_count,
                '잔여거래수익금': int(remaining_profit),
                '잔여평균수익률': round(remaining_avg_profit, 2),
                '수익개선금액': int(improvement),
                '제외거래승률': round((profit_arr[cond_arr] > 0).mean() * 100, 1) if filtered_count > 0 else 0.0,
                '잔여거래승률': round((profit_arr[~cond_arr] > 0).mean() * 100, 1) if remaining_count > 0 else 0.0,
                't통계량': stat_result['t_stat'],
                'p값': stat_result['p_value'],
                '효과크기': stat_result['effect_size'],
                '효과해석': effect_interpretation,
                '신뢰구간': stat_result['confidence_interval'],
                '유의함': '예' if stat_result['significant'] else '아니오',
                '적용권장': '※진단용(룩어헤드)',
            })
        except Exception:
            continue

    filter_results.sort(key=lambda x: x.get('수익개선금액', 0), reverse=True)
    return filter_results

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
        ('B_등락율 >= 20', lambda df: df['B_등락율'] >= 20, '등락율'),
        ('B_체결강도 < 80', lambda df: df['B_체결강도'] < 80, '체결강도'),
    ]

    if '시가총액' in df_tsg.columns:
        key_filters.append(('시가총액 < 1000', lambda df: df['시가총액'] < 1000, '시가총액'))

    if 'B_위험도점수' in df_tsg.columns:
        key_filters.append(('B_위험도점수 >= 50', lambda df: df['B_위험도점수'] >= 50, '위험도'))

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

def GenerateFilterCode(filter_results, df_tsg=None, top_n=5, allow_ml_filters: bool = True):
    """
    필터 분석 결과를 바탕으로 실제 적용 가능한 조건식 코드를 생성합니다.

    Args:
        filter_results: 필터 분석 결과 리스트
        df_tsg: (선택) 원본 DataFrame. 전달되면 "동시 적용(중복 반영)" 기준으로
                예상 총 개선/누적 제외비율/추가 개선(증분)을 계산합니다.
        top_n: 상위 N개 필터(최대)
        allow_ml_filters: False면 *_ML 필터는 코드 생성에서 제외합니다.

    Returns:
        dict: 코드 생성 결과
            - buy_conditions: 매수 조건 코드
            - filter_conditions: 필터 조건 코드
            - full_code: 전체 조건식 코드
    """
    if not filter_results:
        return None

    filtered = list(filter_results)
    excluded_ml_count = 0
    if not allow_ml_filters:
        filtered_no_ml = []
        for f in filtered:
            text = f"{f.get('필터명', '')} {f.get('조건식', '')} {f.get('적용코드', '')}"
            if '_ML' in str(text):
                excluded_ml_count += 1
                continue
            filtered_no_ml.append(f)
        filtered = filtered_no_ml

    # 기본 후보: 개선(+) + 적용코드/조건식이 있는 항목
    candidates = [
        f for f in filtered
        if f.get('수익개선금액', 0) > 0 and f.get('적용코드') and f.get('조건식')
    ]

    if not candidates:
        return None

    # df_tsg가 있으면 "동시 적용(OR 제외)" 기준으로 중복/상쇄를 반영한 그리디 조합을 만듭니다.
    selected = []
    combine_steps = []
    combined_improvement = None
    naive_sum = 0

    if df_tsg is not None and '수익금' in df_tsg.columns and len(df_tsg) > 0:
        try:
            total_trades = int(len(df_tsg))
            profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)
            base_profit = float(np.sum(profit_arr))
            return_arr = None
            if '수익률' in df_tsg.columns:
                return_arr = pd.to_numeric(df_tsg['수익률'], errors='coerce').fillna(0).to_numpy(dtype=np.float64)

            safe_globals = {"__builtins__": {}}
            safe_locals = {"df_tsg": df_tsg, "np": np, "pd": pd}

            cand_masks = []
            for f in candidates:
                cond_expr = f.get('조건식', '')
                cond = eval(cond_expr, safe_globals, safe_locals)
                cond_arr = cond.to_numpy(dtype=bool) if hasattr(cond, 'to_numpy') else np.asarray(cond, dtype=bool)
                if len(cond_arr) != total_trades:
                    cand_masks.append(None)
                else:
                    cand_masks.append(cond_arr)

            excluded_mask = np.zeros(total_trades, dtype=bool)
            cum_impr = 0.0
            chosen_idx = set()

            # 2025-12-20: 제외율/잔여거래 제한을 적용하여 100% 제외 방지
            max_exclusion_ratio = FILTER_MAX_EXCLUSION_RATIO  # 기본값 0.85
            # 작은 샘플에서도 필터 조합을 시도할 수 있도록, "전체의 15%"와 "기본 30건" 중 더 작은 값을 사용
            dynamic_min_remaining = max(1, min(int(total_trades * 0.15), FILTER_MIN_REMAINING_TRADES))

            max_steps = min(int(top_n), len(candidates))
            for step in range(max_steps):
                best_i = None
                best_inc = 0.0

                for i, (f, mask) in enumerate(zip(candidates, cand_masks)):
                    if i in chosen_idx or mask is None:
                        continue

                    # 2025-12-20: 새 필터 추가 시 제외율/잔여거래 제한 체크
                    new_excluded_mask = excluded_mask | mask
                    new_excluded_count = int(np.sum(new_excluded_mask))
                    new_remaining_count = total_trades - new_excluded_count
                    new_exclusion_ratio = new_excluded_count / total_trades

                    # 제외율이 MAX를 초과하면 이 필터는 선택하지 않음
                    if new_exclusion_ratio > max_exclusion_ratio:
                        continue
                    # 잔여 거래 수가 MIN 미만이면 이 필터는 선택하지 않음
                    if new_remaining_count < dynamic_min_remaining:
                        continue

                    add_mask = mask & (~excluded_mask)
                    inc = -float(np.sum(profit_arr[add_mask]))
                    if inc > best_inc:
                        best_inc = inc
                        best_i = i

                if best_i is None or best_inc <= 0:
                    break

                chosen_idx.add(best_i)
                excluded_mask |= cand_masks[best_i]
                cum_impr += best_inc

                excluded_count = int(np.sum(excluded_mask))
                remaining_count = total_trades - excluded_count
                remaining_winrate = float((profit_arr[~excluded_mask] > 0).mean() * 100) if remaining_count > 0 else 0.0
                remaining_return = None
                if return_arr is not None and remaining_count > 0:
                    remaining_return = float(np.mean(return_arr[~excluded_mask]))

                selected.append(candidates[best_i])
                combine_steps.append({
                    '순서': step + 1,
                    '필터명': candidates[best_i].get('필터명', ''),
                    '조건코드': candidates[best_i].get('적용코드', ''),
                    '개별개선': int(candidates[best_i].get('수익개선금액', 0)),
                    '추가개선(중복반영)': int(best_inc),
                    '누적개선(동시적용)': int(cum_impr),
                    '누적수익금': int(base_profit + cum_impr),
                    '누적제외비율': round(excluded_count / total_trades * 100, 1),
                    '잔여거래수': int(remaining_count),
                    '잔여승률': round(remaining_winrate, 1),
                    '잔여평균수익률': round(remaining_return, 2) if remaining_return is not None else None,
                })

            combined_improvement = int(cum_impr)
            naive_sum = int(sum(f.get('수익개선금액', 0) for f in selected))
        except Exception:
            selected = []
            combine_steps = []
            combined_improvement = None
            naive_sum = 0

    # fallback: df_tsg가 없으면 단순히 상위 N개(개별개선 기준)를 사용
    if not selected:
        selected = candidates[:top_n]
        naive_sum = int(sum(f.get('수익개선금액', 0) for f in selected))
        combined_improvement = naive_sum

    # 카테고리별 조건 분류
    conditions_by_category = {}
    for f in selected:
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
    code_lines.append("#")
    code_lines.append("# [조합 방식 설명]")
    code_lines.append("# - 각 필터는 '해당 조건이면 매수하지 않음(제외)'을 의미합니다.")
    code_lines.append("# - 여러 필터를 함께 쓴다는 것은: (필터1 통과) AND (필터2 통과) AND ... 로 해석됩니다.")
    code_lines.append("#   즉, 제외 조건 기준으로 보면 (제외1) OR (제외2) OR ... 입니다.")
    if combined_improvement is not None:
        overlap_loss = int(naive_sum - combined_improvement)
        code_lines.append("#")
        code_lines.append(f"# 예상 총 개선(동시 적용/중복 반영): {combined_improvement:,}원")
        code_lines.append(f"# 개별 개선 합(단순 합산): {naive_sum:,}원")
        code_lines.append(f"# 중복/상쇄(합산-동시적용): {overlap_loss:,}원")

    # 개별 조건식
    individual_conditions = []
    for f in selected:
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
        'combine_steps': combine_steps,
        'summary': {
            'total_filters': len(selected),
            'total_improvement_combined': int(combined_improvement) if combined_improvement is not None else int(naive_sum),
            'total_improvement_naive': int(naive_sum),
            'overlap_loss': int(naive_sum - (combined_improvement if combined_improvement is not None else naive_sum)),
            'categories': list(conditions_by_category.keys()),
            'allow_ml_filters': bool(allow_ml_filters),
            'excluded_ml_filters': int(excluded_ml_count),
        }
    }
