import numpy as np
import pandas as pd

try:
    from numba import njit
    NUMBA_AVAILABLE = True
except Exception:
    NUMBA_AVAILABLE = False

    def njit(*_args, **_kwargs):
        def _wrap(func):
            return func
        return _wrap


@njit(cache=True)
def calculate_mdd_from_cumsum(cumsum: np.ndarray, seed: float) -> float:
    if cumsum.size == 0:
        return 0.0
    peak = cumsum[0]
    max_drawdown = 0.0
    for i in range(1, cumsum.size):
        if cumsum[i] > peak:
            peak = cumsum[i]
        drawdown = peak - cumsum[i]
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    if peak + seed <= 0:
        return 0.0
    return abs(max_drawdown) / (peak + seed) * 100.0

def CalculateDerivedMetrics(df_tsg):
    """
    매수/매도 시점 간 파생 지표를 계산합니다.

    Returns:
        DataFrame with added derived metrics
    """
    df = df_tsg.copy()

    # === 1) 매수 시점 위험도 점수 (0-100, LOOKAHEAD-FREE) ===
    # - 필터 분석은 "매수를 안 하는 조건(진입 회피)"을 찾는 것이므로,
    #   매도 시점 정보(매도등락율/변화량/보유시간 등)를 사용하면 룩어헤드가 됩니다.
    # - 위험도점수는 매수 시점에서 알 수 있는 정보만으로 계산합니다.
    df['위험도점수'] = 0

    if '매수등락율' in df.columns:
        buy_ret = pd.to_numeric(df['매수등락율'], errors='coerce')
        df.loc[buy_ret >= 20, '위험도점수'] += 20
        df.loc[buy_ret >= 25, '위험도점수'] += 10
        df.loc[buy_ret >= 30, '위험도점수'] += 10

    if '매수체결강도' in df.columns:
        buy_power = pd.to_numeric(df['매수체결강도'], errors='coerce')
        df.loc[buy_power < 80, '위험도점수'] += 15
        df.loc[buy_power < 60, '위험도점수'] += 10
        # 과열(초고 체결강도)도 사후 분석에서 손실로 이어지는 경우가 있어 별도 가중(룩어헤드 없음)
        df.loc[buy_power >= 150, '위험도점수'] += 10
        df.loc[buy_power >= 200, '위험도점수'] += 10
        df.loc[buy_power >= 250, '위험도점수'] += 10

    if '매수당일거래대금' in df.columns:
        trade_money_raw = pd.to_numeric(df['매수당일거래대금'], errors='coerce')
        # STOM: 당일거래대금 단위 = 백만 → 억 환산(÷100)
        trade_money_eok = trade_money_raw / 100.0
        df.loc[trade_money_eok < 50, '위험도점수'] += 15
        df.loc[trade_money_eok < 100, '위험도점수'] += 10

    if '시가총액' in df.columns:
        mcap = pd.to_numeric(df['시가총액'], errors='coerce')
        df.loc[mcap < 1000, '위험도점수'] += 15
        df.loc[mcap < 5000, '위험도점수'] += 10

    if '매수호가잔량비' in df.columns:
        hoga = pd.to_numeric(df['매수호가잔량비'], errors='coerce')
        df.loc[hoga < 90, '위험도점수'] += 10
        df.loc[hoga < 70, '위험도점수'] += 15

    if '매수스프레드' in df.columns:
        spread = pd.to_numeric(df['매수스프레드'], errors='coerce')
        df.loc[spread >= 0.5, '위험도점수'] += 10
        df.loc[spread >= 1.0, '위험도점수'] += 10

    # 유동성(회전율) 기반 위험도(룩어헤드 없음)
    if '매수회전율' in df.columns:
        turn = pd.to_numeric(df['매수회전율'], errors='coerce')
        df.loc[turn < 10, '위험도점수'] += 5
        df.loc[turn < 5, '위험도점수'] += 10

    # 매수 변동폭(고가-저가) 기반 변동성(%)이 있으면 반영
    if '매수변동폭비율' in df.columns:
        vol_pct = pd.to_numeric(df['매수변동폭비율'], errors='coerce')
        # 과도한 변동성은 손실 확률이 높아지는 경향이 있어 가중(룩어헤드 없음)
        df.loc[vol_pct >= 7.5, '위험도점수'] += 10
        df.loc[vol_pct >= 10, '위험도점수'] += 10
        df.loc[vol_pct >= 15, '위험도점수'] += 10

    df['위험도점수'] = df['위험도점수'].clip(0, 100)

    # === 2) 매도 시점 데이터 기반 파생지표(진단용) ===
    sell_columns = ['매도등락율', '매도체결강도', '매도당일거래대금', '매도전일비', '매도회전율', '매도호가잔량비']
    has_sell_data = all(col in df.columns for col in sell_columns)

    if has_sell_data:
        # === 변화량 지표 (매도 - 매수) ===
        df['등락율변화'] = df['매도등락율'] - df['매수등락율']
        df['체결강도변화'] = df['매도체결강도'] - df['매수체결강도']
        df['전일비변화'] = df['매도전일비'] - df['매수전일비']
        df['회전율변화'] = df['매도회전율'] - df['매수회전율']
        df['호가잔량비변화'] = df['매도호가잔량비'] - df['매수호가잔량비']

        # === 변화율 지표 (매도 / 매수) ===
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

        # === 추세 판단 지표 ===
        df['등락추세'] = df['등락율변화'].apply(lambda x: '상승' if x > 0 else ('하락' if x < 0 else '유지'))
        df['체결강도추세'] = df['체결강도변화'].apply(lambda x: '강화' if x > 10 else ('약화' if x < -10 else '유지'))
        df['거래량추세'] = df['거래대금변화율'].apply(lambda x: '증가' if x > 1.2 else ('감소' if x < 0.8 else '유지'))

        # === 위험 신호 지표 (매도-매수 기반, 진단용) ===
        df['급락신호'] = (df['등락율변화'] < -3) & (df['체결강도변화'] < -20)
        df['매도세증가'] = df['호가잔량비변화'] < -0.2
        df['거래량급감'] = df['거래대금변화율'] < 0.5

        # === 매수/매도 위험도 점수 (0-100, 사후 진단용) ===
        # - 매도 시점 정보(매도-매수 변화량 등)를 포함하는 위험도 점수입니다.
        # - "매수 진입 필터"로 쓰면 룩어헤드가 되므로, 비교/진단 차트용으로만 사용합니다.
        df['매수매도위험도점수'] = 0
        df.loc[df['등락율변화'] < -2, '매수매도위험도점수'] += 20
        df.loc[df['체결강도변화'] < -15, '매수매도위험도점수'] += 20
        df.loc[df['호가잔량비변화'] < -0.3, '매수매도위험도점수'] += 20
        df.loc[df['거래대금변화율'] < 0.6, '매수매도위험도점수'] += 20
        if '매수등락율' in df.columns:
            buy_ret = pd.to_numeric(df['매수등락율'], errors='coerce')
            df.loc[buy_ret > 20, '매수매도위험도점수'] += 20
        df['매수매도위험도점수'] = df['매수매도위험도점수'].clip(0, 100)

    return df


def AnalyzeFilterEffects(df_tsg):
    """
    조건별 필터 적용 시 예상 효과를 분석합니다.

    Args:
        df_tsg: 파생 지표가 포함된 DataFrame

    Returns:
        list: 필터 효과 분석 결과
    """
    filter_results = []
    total_profit = df_tsg['수익금'].sum()
    total_trades = len(df_tsg)

    if total_trades == 0:
        return filter_results

    # === 필터 조건 정의 ===
    filter_conditions = []

    # 1. 시간대 필터
    if '매수시' in df_tsg.columns:
        for hour in df_tsg['매수시'].unique():
            filter_conditions.append({
                '필터명': f'시간대 {hour}시 제외',
                '조건': df_tsg['매수시'] == hour,
                '분류': '시간대'
            })

    # 2. 등락율 구간 필터
    if '매수등락율' in df_tsg.columns:
        filter_conditions.extend([
            {'필터명': '매수등락율 25% 이상 제외', '조건': df_tsg['매수등락율'] >= 25, '분류': '등락율'},
            {'필터명': '매수등락율 20% 이상 제외', '조건': df_tsg['매수등락율'] >= 20, '분류': '등락율'},
            {'필터명': '매수등락율 5% 미만 제외', '조건': df_tsg['매수등락율'] < 5, '분류': '등락율'},
        ])

    # 3. 체결강도 필터
    if '매수체결강도' in df_tsg.columns:
        filter_conditions.extend([
            {'필터명': '매수체결강도 80 미만 제외', '조건': df_tsg['매수체결강도'] < 80, '분류': '체결강도'},
            {'필터명': '매수체결강도 200 이상 제외', '조건': df_tsg['매수체결강도'] >= 200, '분류': '체결강도'},
        ])

    # 4. (룩어헤드 제거) 매도-매수 변화량/급락신호 기반 필터는 제외
    # - 등락율변화/체결강도변화/거래대금변화율/급락신호 등은 매도 시점 정보가 포함된
    #   "사후 확정 지표"이므로, 매수 진입 필터 추천에는 사용하지 않습니다.

    if '위험도점수' in df_tsg.columns:
        filter_conditions.extend([
            {'필터명': '매수 위험도점수 60점 이상 제외', '조건': df_tsg['위험도점수'] >= 60, '분류': '위험신호'},
            {'필터명': '매수 위험도점수 40점 이상 제외', '조건': df_tsg['위험도점수'] >= 40, '분류': '위험신호'},
        ])

    # 5. 보유시간 필터
    # - 보유시간은 매도 조건(SL/TP 등)의 결과로 결정되는 값이어서,
    #   "매수 시점 필터"로 쓰기 어렵기 때문에 필터 분석에서는 제외합니다.

    # 6. 시가총액 필터
    if '시가총액' in df_tsg.columns:
        filter_conditions.extend([
            {'필터명': '매수시가총액 1000억 미만 제외', '조건': df_tsg['시가총액'] < 1000, '분류': '시가총액'},
            {'필터명': '매수시가총액 3000억 미만 제외', '조건': df_tsg['시가총액'] < 3000, '분류': '시가총액'},
            {'필터명': '매수시가총액 1조 이상 제외', '조건': df_tsg['시가총액'] >= 10000, '분류': '시가총액'},
        ])

    # === 각 필터 효과 계산 ===
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

            # 필터 적용 시 수익 개선 효과 (제외된 거래가 손실이면 양수)
            improvement = -filtered_profit

            filter_results.append({
                '분류': fc['분류'],
                '필터명': fc['필터명'],
                '제외거래수': filtered_count,
                '제외비율': round(filtered_count / total_trades * 100, 1),
                '제외거래수익금': int(filtered_profit),
                '잔여거래수': remaining_count,
                '잔여거래수익금': int(remaining_profit),
                '수익개선금액': int(improvement),
                '제외거래승률': round((filtered_out['수익금'] > 0).mean() * 100, 1) if len(filtered_out) > 0 else 0,
                '잔여거래승률': round((remaining['수익금'] > 0).mean() * 100, 1) if len(remaining) > 0 else 0,
                '적용권장': '★★★' if improvement > total_profit * 0.1 else ('★★' if improvement > 0 else ''),
            })
        except:
            continue

    return filter_results


# ============================================================================
# [2025-12-09] 매수/매도 시점 비교 분석 차트 (11개 차트)
# ============================================================================

