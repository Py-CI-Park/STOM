import math
import random
import re
from datetime import datetime
from traceback import print_exc
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import font_manager, gridspec
from utility.static import strp_time, strf_time
from backtester.output_paths import ensure_backtesting_output_dir
from backtester.analysis.text_utils import _format_progress_logs, _extract_strategy_block_lines

try:
    from backtester.back_analysis_enhanced import ComputeStrategyKey
    ENHANCED_ANALYSIS_AVAILABLE = True
except ImportError:
    ENHANCED_ANALYSIS_AVAILABLE = False


def _parse_number(text):
    if text is None:
        return None
    try:
        return int(str(text).replace(',', '').strip())
    except Exception:
        return None


def _extract_int(pattern, text):
    if not text:
        return None
    match = re.search(pattern, text)
    if not match:
        return None
    return _parse_number(match.group(1))


def _extract_unit(label_text):
    if not label_text:
        return None
    match = re.search(r'종목당 배팅금액\s*[0-9,]+([A-Za-z가-힣]+)', label_text)
    if match:
        return match.group(1).strip()
    match = re.search(r'필요자금\s*[0-9,]+([A-Za-z가-힣]+)', label_text)
    if match:
        return match.group(1).strip()
    return None


def _normalize_time_value(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None, None
    if isinstance(value, (pd.Timestamp, datetime)):
        digits = value.strftime('%Y%m%d%H%M%S')
        return int(digits), len(digits)
    text = str(value).strip()
    if not text:
        return None, None
    digits = re.sub(r'\D', '', text)
    if not digits:
        return None, None
    return int(digits), len(digits)


def _get_trade_timestamp(row, time_col):
    val_int, val_len = _normalize_time_value(row.get(time_col) if time_col in row else None)
    if val_int is None:
        return None

    if val_len is not None and val_len <= 6:
        date_val, date_len = _normalize_time_value(row.get('매수일자') if '매수일자' in row else None)
        if date_val is not None and date_len is not None and date_len >= 8:
            time_str = str(val_int).zfill(6)
            return int(f"{date_val}{time_str}")
    return val_int


def _infer_day_count(df, fallback_text=None):
    if df is not None and not df.empty:
        if '매수일자' in df.columns:
            try:
                return int(pd.to_numeric(df['매수일자'], errors='coerce').dropna().nunique())
            except Exception:
                pass
        if '매수시간' in df.columns:
            try:
                digits = pd.to_numeric(df['매수시간'], errors='coerce').dropna().astype(int)
                if not digits.empty:
                    dates = digits.astype(str).str.slice(0, 8)
                    return int(dates.nunique())
            except Exception:
                pass

    if fallback_text:
        return _extract_int(r'거래일수\s*:\s*([0-9]+)', fallback_text)
    return None


def _calc_mdd(profits, seed):
    if profits is None or profits.empty:
        return 0.0
    try:
        cum = profits.cumsum().to_numpy(dtype=np.float64)
        if len(cum) == 0:
            return 0.0
        peak = np.maximum.accumulate(cum)
        drawdown = peak - cum
        lower = int(np.argmax(drawdown))
        if lower <= 0:
            return 0.0
        upper = int(np.argmax(cum[:lower + 1]))
        denom = float(cum[upper]) + float(seed)
        if denom == 0:
            return 0.0
        return round(abs(cum[upper] - cum[lower]) / denom * 100, 2)
    except Exception:
        return 0.0


def _annotate_profit_extremes(ax, x_values, profits, unit):
    if profits is None:
        return
    try:
        arr = np.asarray(profits, dtype=np.float64)
    except Exception:
        return
    if arr.size == 0:
        return
    x_vals = np.asarray(list(x_values)) if isinstance(x_values, range) else np.asarray(x_values)
    if x_vals.size != arr.size:
        x_vals = np.arange(arr.size)

    max_profit = float(np.nanmax(arr))
    if max_profit > 0:
        idx = int(np.nanargmax(arr))
        x = x_vals[idx]
        ax.scatter([x], [max_profit], color='red', zorder=5)
        ax.annotate(
            f'최대 이익 {int(max_profit):,}{unit}',
            xy=(x, max_profit),
            xytext=(0, 12),
            textcoords='offset points',
            ha='center',
            fontsize=8,
            color='red',
            arrowprops=dict(arrowstyle='->', color='red', lw=0.8),
        )

    min_profit = float(np.nanmin(arr))
    if min_profit < 0:
        idx = int(np.nanargmin(arr))
        x = x_vals[idx]
        ax.scatter([x], [min_profit], color='blue', zorder=5)
        ax.annotate(
            f'최대 손실 {int(abs(min_profit)):,}{unit}',
            xy=(x, min_profit),
            xytext=(0, -14),
            textcoords='offset points',
            ha='center',
            fontsize=8,
            color='blue',
            arrowprops=dict(arrowstyle='->', color='blue', lw=0.8),
        )


def _annotate_holdings_extremes(ax, x_values, holdings, unit):
    if holdings is None:
        return
    try:
        arr = np.asarray(holdings, dtype=np.float64)
    except Exception:
        return
    if arr.size == 0:
        return
    x_vals = np.asarray(list(x_values)) if isinstance(x_values, range) else np.asarray(x_values)
    if x_vals.size != arr.size:
        x_vals = np.arange(arr.size)

    max_val = float(np.nanmax(arr))
    min_val = float(np.nanmin(arr))
    if max_val > 0:
        idx = int(np.nanargmax(arr))
        x = x_vals[idx]
        ax.scatter([x], [max_val], color='green', zorder=5)
        ax.annotate(
            f'최대 보유 {int(max_val):,}{unit}',
            xy=(x, max_val),
            xytext=(0, 12),
            textcoords='offset points',
            ha='center',
            fontsize=8,
            color='green',
            arrowprops=dict(arrowstyle='->', color='green', lw=0.8),
        )

    if min_val >= 0 and min_val != max_val:
        idx = int(np.nanargmin(arr))
        x = x_vals[idx]
        ax.scatter([x], [min_val], color='blue', zorder=5)
        ax.annotate(
            f'최소 보유 {int(min_val):,}{unit}',
            xy=(x, min_val),
            xytext=(0, -12),
            textcoords='offset points',
            ha='center',
            fontsize=8,
            color='blue',
            arrowprops=dict(arrowstyle='->', color='blue', lw=0.8),
        )


def _collect_trade_events(df):
    if df is None or df.empty or '매수금액' not in df.columns:
        return []

    has_sell_time = '매도시간' in df.columns
    events = []
    for _, row in df.iterrows():
        buy_time = _get_trade_timestamp(row, '매수시간')
        sell_time = _get_trade_timestamp(row, '매도시간') if has_sell_time else None
        if buy_time is None:
            continue
        if sell_time is None or sell_time < buy_time:
            sell_time = buy_time

        amount_raw = row.get('매수금액')
        if isinstance(amount_raw, str):
            amount_raw = amount_raw.replace(',', '')
        amount = pd.to_numeric(amount_raw, errors='coerce')
        try:
            amount = float(amount)
        except Exception:
            amount = 0.0
        if amount <= 0:
            continue

        events.append((buy_time, 0, amount, 1))
        events.append((sell_time, 1, -amount, -1))

    return events


def _estimate_capital_stats(df):
    events = _collect_trade_events(df)
    if not events:
        return None, None

    events.sort(key=lambda x: (x[0], x[1]))
    current_amount = 0.0
    current_count = 0
    max_amount = 0.0
    max_count = 0
    for _, _, delta_amount, delta_count in events:
        current_amount += delta_amount
        current_count += delta_count
        if current_amount > max_amount:
            max_amount = current_amount
        if current_count > max_count:
            max_count = current_count
    return max_amount, max_count


def _build_holdings_timeseries(df):
    events = _collect_trade_events(df)
    if not events:
        return None

    events.sort(key=lambda x: (x[0], x[1]))
    timestamps = []
    amounts = []
    counts = []
    current_amount = 0.0
    current_count = 0
    for timestamp, _, delta_amount, delta_count in events:
        current_amount += delta_amount
        current_count += delta_count
        timestamps.append(timestamp)
        amounts.append(current_amount)
        counts.append(current_count)

    series = pd.DataFrame({
        'timestamp': timestamps,
        'holding_amount': amounts,
        'holding_count': counts,
    })
    if series.empty:
        return None
    return series.groupby('timestamp', sort=True).last().reset_index()


def _build_daily_holdings_summary(df, amount_mode: str = 'sum'):
    holdings = _build_holdings_timeseries(df)
    if holdings is None or holdings.empty:
        return None

    timestamps = pd.to_numeric(holdings['timestamp'], errors='coerce')
    timestamps = timestamps.dropna().astype(int)
    if timestamps.empty:
        return None

    date_str = timestamps.astype(str).str.slice(0, 8)
    if date_str.str.len().min() < 8:
        return None

    summary = holdings.loc[timestamps.index].copy()
    summary['date'] = date_str.values
    summary['holding_amount'] = pd.to_numeric(summary['holding_amount'], errors='coerce').fillna(0)
    summary['holding_count'] = pd.to_numeric(summary['holding_count'], errors='coerce').fillna(0)

    if amount_mode not in ('sum', 'max'):
        amount_mode = 'sum'
    amount_agg = 'sum' if amount_mode == 'sum' else 'max'
    daily = summary.groupby('date', sort=True).agg({
        'holding_amount': amount_agg,
        'holding_count': 'max',
    })
    return daily.reset_index()


def _estimate_max_daily_trades(df):
    if df is None or df.empty:
        return 0

    daily = _build_daily_holdings_summary(df, amount_mode='max')
    if daily is not None and not daily.empty:
        max_count = pd.to_numeric(daily['holding_count'], errors='coerce').dropna()
        if not max_count.empty:
            return int(max_count.max())

    if '매수일자' in df.columns:
        dates = pd.to_numeric(df['매수일자'], errors='coerce').dropna()
        if not dates.empty:
            return int(dates.value_counts().max())

    if '매수시간' in df.columns:
        digits = pd.to_numeric(df['매수시간'], errors='coerce').dropna().astype(int)
        if not digits.empty:
            date_str = digits.astype(str).str.slice(0, 8)
            counts = date_str.value_counts()
            if not counts.empty:
                return int(counts.max())

    return 0


def _build_filtered_info_lines(df_all, df_filtered, back_text, label_text, seed):
    lines = []
    if back_text:
        lines.append(back_text)

    if df_filtered is None or df_filtered.empty:
        if label_text:
            lines.append(label_text)
        return lines

    day_count = _infer_day_count(df_filtered, fallback_text=back_text) or _infer_day_count(df_all) or 0
    betting = _extract_int(r'종목당 배팅금액\s*([0-9,]+)', label_text or '') or 0
    seed_from_label = _extract_int(r'필요자금\s*([0-9,]+)', label_text or '')
    seed_value = _parse_number(seed) if seed is not None else None
    if seed_value is None or seed_value <= 0:
        seed_value = seed_from_label if seed_from_label is not None else betting

    unit = _extract_unit(label_text or '') or '원'
    year_days = 365 if unit.upper() == 'USDT' else 250

    daily_summary = _build_daily_holdings_summary(df_filtered, amount_mode='max')
    max_daily_holdings = 0
    daily_amount_max = 0.0
    if daily_summary is not None and not daily_summary.empty:
        max_daily_holdings = int(
            pd.to_numeric(daily_summary['holding_count'], errors='coerce').fillna(0).max()
        )
        daily_amount_max = float(
            pd.to_numeric(daily_summary['holding_amount'], errors='coerce').fillna(0).max()
        )
    if max_daily_holdings <= 0:
        max_daily_holdings = _estimate_max_daily_trades(df_filtered)

    daily_capital = float(betting) * float(max_daily_holdings) if betting and max_daily_holdings else 0.0

    capital, max_holdings = _estimate_capital_stats(df_filtered)
    if capital is None or capital <= 0:
        if daily_amount_max > 0:
            capital = daily_amount_max
        elif daily_capital > 0:
            capital = daily_capital
        else:
            capital = float(seed_value) if seed_value else float(betting or 1)
    if daily_capital > 0:
        capital = daily_capital
    if max_holdings is None:
        max_holdings = _extract_int(r'적정최대보유종목수\s*([0-9]+)', label_text or '') or 0

    if '수익금' in df_filtered.columns:
        profit = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0)
    else:
        profit = pd.Series(0, index=df_filtered.index, dtype='float64')
    if '수익률' in df_filtered.columns:
        returns = pd.to_numeric(df_filtered['수익률'], errors='coerce').fillna(0)
    else:
        returns = pd.Series(0, index=df_filtered.index, dtype='float64')
    if '보유시간' in df_filtered.columns:
        holding = pd.to_numeric(df_filtered['보유시간'], errors='coerce').fillna(0)
    else:
        holding = pd.Series(0, index=df_filtered.index, dtype='float64')

    tc = int(len(df_filtered))
    atc = round(tc / day_count, 1) if day_count else 0
    pc = int((profit >= 0).sum())
    mc = int((profit < 0).sum())
    wr = round((pc / tc) * 100, 2) if tc else 0.0
    ah = round(float(holding.sum()) / tc, 2) if tc else 0.0
    app = round(float(returns.sum()) / tc, 2) if tc else 0.0
    tsg = int(profit.sum())
    appp = float(returns[profit >= 0].mean()) if pc else 0.0
    ampp = abs(float(returns[profit < 0].mean())) if mc else 0.0
    tpi = round(wr / 100 * (1 + appp / ampp), 2) if ampp != 0 else 1.0

    tpp = round(tsg / capital * 100, 2) if capital else 0.0
    cagr = round(tpp / day_count * year_days, 2) if day_count else 0.0
    mdd = _calc_mdd(profit, capital)

    daily_capital_text = (
        f", 일최대거래종목수 기준 필요자금 {daily_capital:,.0f}{unit}" if daily_capital > 0 else ""
    )

    label = (
        f'종목당 배팅금액 {int(betting):,}{unit}, 필요자금 {float(capital):,.0f}{unit}'
        f'{daily_capital_text}\n'
        f'거래횟수 {tc}회, 일평균거래횟수 {atc}회, 일최대거래종목수 {max_daily_holdings}개, 적정최대보유종목수 {max_holdings}개, 평균보유기간 {ah:.2f}초\n'
        f'익절 {pc}회, 손절 {mc}회, 승률 {wr:.2f}%, 평균수익률 {app:.2f}%, 수익률합계 {tpp:.2f}%, '
        f'최대낙폭률 {mdd:.2f}%, 수익금합계 {tsg:,}{unit}, 매매성능지수 {tpi:.2f}, 연간예상수익률 {cagr:.2f}%'
    )
    lines.append(label)
    return lines

def PltFilterAppliedPreviewCharts(df_all: pd.DataFrame, df_filtered: pd.DataFrame,
                                    save_file_name: str, backname: str, seed: int,
                                    generated_code: dict = None,
                                    buystg: str = None, sellstg: str = None,
                                    file_tag: str = '',
                                    segment_combo_map: dict = None,
                                    back_text: str = None,
                                    label_text: str = None):
    """
    자동 생성 필터(generated_code)를 적용한 결과를 2개의 png로 저장합니다.
    - {전략명}{_tag}_filtered.png
    - {전략명}{_tag}_filtered_.png

    2025-12-20 개선: 필터 적용 후 거래가 0건이어도 경고 차트를 생성합니다.
    """
    if df_all is None:
        return None, None
    if len(df_all) < 1:
        return None, None
    if '수익금' not in df_all.columns:
        return None, None

    tag = f"_{file_tag}" if file_tag else ""
    output_dir = ensure_backtesting_output_dir(save_file_name)

    # 2025-12-20: 필터 적용 후 거래 0~1건인 경우 경고 차트 생성
    if df_filtered is None or len(df_filtered) < 2 or '수익금' not in df_filtered.columns:
        # 폰트(한글) 설정
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_family = font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_family
            plt.rcParams['font.sans-serif'] = [font_family]
        except Exception:
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        total_profit = int(pd.to_numeric(df_all.get('수익금'), errors='coerce').fillna(0).sum())
        total_trades = len(df_all)
        remaining = len(df_filtered) if isinstance(df_filtered, pd.DataFrame) else 0
        exclusion_ratio = 0.0 if total_trades == 0 else (1.0 - (remaining / total_trades))

        fig, ax = plt.subplots(figsize=(12, 8))
        warning_text = (
            f"⚠️ 필터 적용 결과: 거래가 부족합니다 (0~1건)\n\n"
            f"• 원본 거래: {total_trades:,}건\n"
            f"• 원본 수익금: {total_profit:,}원\n"
            f"• 필터 후: {remaining:,}건 (제외율 {exclusion_ratio*100:.1f}%)\n\n"
            f"💡 필터 조건이 너무 엄격하거나 데이터가 적습니다.\n"
            f"   FILTER_MAX_EXCLUSION_RATIO (기본값 85%)를 확인하세요.\n"
            f"   FILTER_MIN_REMAINING_TRADES (기본값 30) 또는 데이터 샘플 규모를 확인하세요.\n"
            f"   다른 필터 조합을 시도해 보세요.\n\n"
            f"🔧 back_analysis_enhanced.py에서 다음 상수를 조정할 수 있습니다:\n"
            f"   - FILTER_MAX_EXCLUSION_RATIO: 최대 제외율 (기본 0.85)\n"
            f"   - FILTER_MIN_REMAINING_TRADES: 최소 잔여 거래 수 (기본 30)"
        )

        ax.text(0.5, 0.5, warning_text, ha='center', va='center', fontsize=13,
                transform=ax.transAxes,
                bbox=dict(facecolor='lightyellow', edgecolor='orange', alpha=0.9, linewidth=2))
        ax.set_title(f'{backname} - 필터 적용 결과 경고 (거래 0건)', fontsize=14, color='red')
        ax.axis('off')

        path_main = str(output_dir / f"{save_file_name}{tag}_filtered.png")
        plt.savefig(path_main, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        return path_main, None

    # 폰트(한글) 설정
    font_path = 'C:/Windows/Fonts/malgun.ttf'
    try:
        font_family = font_manager.FontProperties(fname=font_path).get_name()
        plt.rcParams['font.family'] = font_family
        plt.rcParams['font.sans-serif'] = [font_family]
    except Exception:
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    total_profit = float(pd.to_numeric(df_all['수익금'], errors='coerce').fillna(0).sum())
    filtered_profit = float(pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0).sum())
    improvement = filtered_profit - total_profit
    excluded_ratio = (1.0 - (len(df_filtered) / max(1, len(df_all)))) * 100.0
    is_segment = file_tag == 'segment' or isinstance(segment_combo_map, dict)

    avg_return_all = None
    avg_return_filt = None
    if '수익률' in df_all.columns and '수익률' in df_filtered.columns:
        avg_return_all = float(pd.to_numeric(df_all['수익률'], errors='coerce').fillna(0).mean())
        avg_return_filt = float(pd.to_numeric(df_filtered['수익률'], errors='coerce').fillna(0).mean())

    unit_label = _extract_unit(label_text or '') or '원'

    # ===== 1) filtered.png (수익곡선 요약) =====
    path_main = str(output_dir / f"{save_file_name}{tag}_filtered.png")
    fig = plt.figure(figsize=(12, 10))
    gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[1, 3])

    use_dates = False
    dates = None
    base_cum = None
    filt_cum = None

    ax0 = fig.add_subplot(gs[0])
    daily_all = _build_daily_holdings_summary(df_all, amount_mode='max')
    daily_filt = _build_daily_holdings_summary(df_filtered, amount_mode='max')
    has_holdings = (daily_all is not None and not daily_all.empty) or (daily_filt is not None and not daily_filt.empty)

    if has_holdings:
        date_set = set()
        if daily_all is not None and not daily_all.empty:
            date_set.update(daily_all['date'].astype(str).tolist())
        if daily_filt is not None and not daily_filt.empty:
            date_set.update(daily_filt['date'].astype(str).tolist())
        dates = sorted(date_set)

        base_map = {}
        if daily_all is not None and not daily_all.empty:
            base_map = dict(zip(daily_all['date'].astype(str), daily_all['holding_amount']))
        filt_map = {}
        if daily_filt is not None and not daily_filt.empty:
            filt_map = dict(zip(daily_filt['date'].astype(str), daily_filt['holding_amount']))

        x = list(range(len(dates)))
        base_vals = [float(base_map.get(d, 0) or 0) for d in dates]
        filt_vals = [float(filt_map.get(d, 0) or 0) for d in dates]

        filt_label = '세그먼트 필터 보유금액' if is_segment else '필터 보유금액'
        if any(base_vals):
            ax0.plot(x, base_vals, linewidth=1.2, label='기준 보유금액', color='gray', alpha=0.7)
        if any(filt_vals):
            ax0.plot(x, filt_vals, linewidth=2.2, label=filt_label, color='green')

        ax0.set_title('보유금액(원) - 일별 최대')
        ax0.set_ylabel('보유금액(원)')
        tick_step = max(1, int(len(dates) / 10))
        ax0.set_xticks(list(range(0, len(dates), tick_step)))
        ax0.set_xticklabels([str(d) for d in dates][::tick_step], rotation=45, ha='right', fontsize=8)
        ax0.legend(loc='best')
        ax0.grid()
        if any(filt_vals):
            _annotate_holdings_extremes(ax0, x, filt_vals, unit_label)
    else:
        if is_segment:
            ax0.text(0.5, 0.5, '보유금액 데이터 없음', ha='center', va='center', transform=ax0.transAxes)
            ax0.axis('off')
        else:
            try:
                if '매수일자' in df_all.columns and '매수일자' in df_filtered.columns:
                    base_profit_daily = pd.to_numeric(df_all['수익금'], errors='coerce').fillna(0).groupby(df_all['매수일자']).sum()
                    filt_profit_daily = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0).groupby(df_filtered['매수일자']).sum()
                    dates = sorted(set(base_profit_daily.index.tolist()) | set(filt_profit_daily.index.tolist()))
                    base_profit_daily = base_profit_daily.reindex(dates, fill_value=0)
                    filt_profit_daily = filt_profit_daily.reindex(dates, fill_value=0)
                    base_cum = base_profit_daily.cumsum()
                    filt_cum = filt_profit_daily.cumsum()
                    use_dates = True
            except Exception:
                use_dates = False

            if not use_dates:
                base_cum = pd.to_numeric(df_all['수익금'], errors='coerce').fillna(0).cumsum()
                filt_cum = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0).cumsum()
                ax0.plot(range(len(base_cum)), base_cum, linewidth=1.2, label='기준(전체)', color='gray', alpha=0.8)
                ax0.plot(range(len(filt_cum)), filt_cum, linewidth=2.2, label='필터 적용', color='orange')
                ax0.set_title('누적 수익금(원)')
            else:
                x = np.arange(len(dates))
                ax0.plot(x, base_cum.values, linewidth=1.2, label='기준(전체)', color='gray', alpha=0.8)
                ax0.plot(x, filt_cum.values, linewidth=2.2, label='필터 적용', color='orange')
                ax0.set_title('누적 수익금(원) - 일자 기준')
                tick_step = max(1, int(len(dates) / 10))
                ax0.set_xticks(list(x[::tick_step]))
                ax0.set_xticklabels([str(d) for d in dates][::tick_step], rotation=45, ha='right', fontsize=8)
            ax0.legend(loc='best')
            ax0.grid()

    info_lines = _build_filtered_info_lines(df_all, df_filtered, back_text, label_text, seed)
    if info_lines:
        ax0.set_xlabel("\n" + "\n".join(info_lines), fontsize=9)

    if filt_cum is None:
        use_dates = False
        dates = None
        try:
            if '매수일자' in df_filtered.columns:
                filt_profit_daily = (
                    pd.to_numeric(df_filtered['수익금'], errors='coerce')
                    .fillna(0)
                    .groupby(df_filtered['매수일자'])
                    .sum()
                )
                dates = sorted(filt_profit_daily.index.tolist())
                filt_cum = filt_profit_daily.cumsum()
                use_dates = True
        except Exception:
            use_dates = False

        if not use_dates:
            filt_cum = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0).cumsum()

    ax1 = fig.add_subplot(gs[1])
    if not use_dates:
        profits = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0)
        x = range(len(profits))
        ax1.bar(x, profits.clip(lower=0), label='이익금액', color='r', alpha=0.7)
        ax1.bar(x, profits.clip(upper=0), label='손실금액', color='b', alpha=0.7)
        ax1.plot(range(len(filt_cum)), filt_cum, linewidth=2.0, label='누적(필터)', color='orange')
        _annotate_profit_extremes(ax1, x, profits, unit_label)
        ax1.set_xlabel('거래 순번(필터 적용 후)')
    else:
        profits = filt_cum.diff().fillna(filt_cum.iloc[0])
        x = np.arange(len(dates))
        ax1.bar(x, profits.clip(lower=0).values, label='이익금액', color='r', alpha=0.7)
        ax1.bar(x, profits.clip(upper=0).values, label='손실금액', color='b', alpha=0.7)
        ax1.plot(x, filt_cum.values, linewidth=2.0, label='누적(필터)', color='orange')
        _annotate_profit_extremes(ax1, x, profits, unit_label)
        ax1.set_xlabel('매수일자')
        tick_step = max(1, int(len(dates) / 10))
        ax1.set_xticks(list(x[::tick_step]))
        ax1.set_xticklabels([str(d) for d in dates][::tick_step], rotation=45, ha='right', fontsize=8)
    ax1.set_ylabel('수익금(원)')
    ax1.legend(loc='upper left')
    ax1.grid()
    summary_lines = [
        "=== 세그먼트 필터 적용 요약 ===" if is_segment else "=== 필터 적용 요약 ===",
        f"- 거래수: {len(df_all):,} → {len(df_filtered):,} (제외 {excluded_ratio:.1f}%)",
        f"- 수익금: {int(total_profit):,}원 → {int(filtered_profit):,}원 (개선 {int(improvement):+,}원)",
    ]
    if avg_return_all is not None and avg_return_filt is not None:
        summary_lines.append(
            f"- 평균 수익률: {avg_return_all:.4f}% → {avg_return_filt:.4f}% ({avg_return_filt - avg_return_all:+.4f}%)"
        )
    if isinstance(generated_code, dict) and generated_code.get('summary'):
        s = generated_code.get('summary') or {}
        try:
            summary_lines.append(f"- 자동 생성 필터: {int(s.get('total_filters', 0) or 0):,}개")
            summary_lines.append(f"- 예상 총 개선(동시 적용): {int(s.get('total_improvement_combined', s.get('total_improvement_naive', 0)) or 0):,}원")
        except Exception:
            pass
    if is_segment and isinstance(segment_combo_map, dict) and segment_combo_map:
        def _format_segment_combo_lines(combo_map, max_lines=12, max_len=90):
            lines = []
            for seg_id in sorted(combo_map.keys()):
                combo = combo_map.get(seg_id) or {}
                if combo.get('exclude_segment'):
                    line = f"{seg_id}: 전체 제외"
                else:
                    filters = combo.get('filters') or []
                    names = []
                    for flt in filters:
                        name = flt.get('filter_name') or flt.get('name') or ''
                        if not name:
                            col = flt.get('column')
                            threshold = flt.get('threshold')
                            direction = flt.get('direction')
                            if col and threshold is not None and direction in ('less', 'greater'):
                                op = ">=" if direction == 'less' else "<"
                                name = f"{col} {op} {threshold}"
                        if name:
                            names.append(str(name))
                    if names:
                        line = f"{seg_id}: " + " | ".join(names)
                    else:
                        line = f"{seg_id}: (필터 없음)"
                if len(line) > max_len:
                    line = line[: max_len - 3] + "..."
                lines.append(line)
                if len(lines) >= max_lines:
                    break
            remaining = max(0, len(combo_map) - max_lines)
            return lines, remaining

        seg_lines, seg_remaining = _format_segment_combo_lines(segment_combo_map)
        summary_lines.append("- 세그먼트 필터 조합(요약):")
        summary_lines.extend([f"  {ln}" for ln in seg_lines])
        if seg_remaining > 0:
            summary_lines.append(f"  ... 외 {seg_remaining}개")
        summary_lines.append("  (상세: *_segment_code.txt, *_segment_combos.csv)")
    if isinstance(generated_code, dict) and generated_code.get('buy_conditions'):
        summary_lines.append("- 적용 조건(일부):")
        for ln in (generated_code.get('buy_conditions') or [])[:5]:
            summary_lines.append(f"  {str(ln).strip()}")

    if not is_segment:
        buy_block = _extract_strategy_block_lines(buystg, start_marker='if 매수:', end_marker='if 매도:', max_lines=6)
        sell_block = _extract_strategy_block_lines(sellstg, start_marker='if 매도:', end_marker=None, max_lines=6)
        if buy_block or sell_block:
            summary_lines.append("- 조건식(일부):")
            if buy_block:
                summary_lines.append("  [매수]")
                summary_lines.extend([f"    {ln}" for ln in buy_block])
            if sell_block:
                summary_lines.append("  [매도]")
                summary_lines.extend([f"    {ln}" for ln in sell_block])

    fig.suptitle(f'{backname} 필터 적용 결과 - {save_file_name}', fontsize=14, fontweight='bold')
    fig.text(0.01, 0.01, "\n".join(summary_lines), fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.5))

    plt.tight_layout(rect=(0, 0.05, 1, 0.96))
    plt.savefig(path_main, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    # ===== 2) filtered_.png (분포/단계 요약) =====
    path_sub = str(output_dir / f"{save_file_name}{tag}_filtered_.png")
    fig = plt.figure(figsize=(12, 10))
    gs = gridspec.GridSpec(nrows=2, ncols=2, figure=fig, hspace=0.35, wspace=0.25)

    # (1) 누적 수익률(%) - 일자 기준(가능하면 매수일자 사용)
    ax = fig.add_subplot(gs[0, 0])
    if '매수일자' in df_all.columns and '매수일자' in df_filtered.columns:
        base_profit_daily = pd.to_numeric(df_all['수익금'], errors='coerce').fillna(0).groupby(df_all['매수일자']).sum()
        filt_profit_daily = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0).groupby(df_filtered['매수일자']).sum()
        dates = sorted(set(base_profit_daily.index.tolist()) | set(filt_profit_daily.index.tolist()))
        base_profit_daily = base_profit_daily.reindex(dates, fill_value=0)
        filt_profit_daily = filt_profit_daily.reindex(dates, fill_value=0)

        base_daily = base_profit_daily.cumsum()
        filt_daily = filt_profit_daily.cumsum()
        x = np.arange(len(dates))
        if seed:
            base_daily_pct = (base_daily + float(seed)) / float(seed) * 100 - 100
            filt_daily_pct = (filt_daily + float(seed)) / float(seed) * 100 - 100
            ax.plot(x, base_daily_pct.values, label='기준(%)', color='gray', linewidth=1.2)
            ax.plot(x, filt_daily_pct.values, label='필터(%)', color='orange', linewidth=2.0)
            ax.set_ylabel('누적 수익률(%)')
        else:
            ax.plot(x, base_daily.values, label='기준(원)', color='gray', linewidth=1.2)
            ax.plot(x, filt_daily.values, label='필터(원)', color='orange', linewidth=2.0)
            ax.set_ylabel('누적 수익금(원)')
        ax.set_title('일자별 누적 성과(필터 적용 비교)')
        ax.set_xlabel('매수일자')
        tick_step = max(1, int(len(dates) / 10))
        ax.set_xticks(list(x[::tick_step]))
        ax.set_xticklabels([str(d) for d in dates][::tick_step], rotation=45, ha='right', fontsize=8)
    else:
        ax.text(0.5, 0.5, '매수일자 컬럼 없음', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')
    ax.legend(loc='best')
    ax.grid()

    ax = fig.add_subplot(gs[0, 1])
    ax2 = ax.twinx()
    steps = (generated_code or {}).get('combine_steps') or []
    if steps:
        x = list(range(1, len(steps) + 1))
        cum_imp = [float(st.get('누적개선(동시적용)', 0) or 0) for st in steps]
        ex_pct = [float(st.get('누적제외비율', 0) or 0) for st in steps]
        ax.plot(x, cum_imp, 'o-', color='green', linewidth=2.0, markersize=4, label='누적개선(원)')
        ax2.plot(x, ex_pct, 's--', color='red', linewidth=1.5, markersize=4, label='누적제외(%)')
        ax.set_title('필터 조합 적용 단계별 누적개선/제외비율')
        ax.set_xlabel('단계')
        ax.set_ylabel('누적개선(원)', color='green')
        ax2.set_ylabel('누적제외(%)', color='red')
        ax.grid()
    else:
        if '수익률' in df_all.columns and '수익률' in df_filtered.columns:
            base_returns = pd.to_numeric(df_all['수익률'], errors='coerce').fillna(0)
            filt_returns = pd.to_numeric(df_filtered['수익률'], errors='coerce').fillna(0)
            bins = 30
            ax.hist(base_returns, bins=bins, alpha=0.4, label='기준', color='gray')
            ax.hist(filt_returns, bins=bins, alpha=0.7, label='필터', color='orange')
            ax.axvline(x=0, color='black', linewidth=0.8)
            ax.set_title('수익률 분포(필터 전/후)')
            ax.set_xlabel('수익률(%)')
            ax.set_ylabel('거래수')
            ax.legend(loc='best')
            ax.grid(axis='y', alpha=0.3)
        else:
            base_profit = pd.to_numeric(df_all['수익금'], errors='coerce').fillna(0)
            filt_profit = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0)
            base_counts = [int((base_profit > 0).sum()), int((base_profit <= 0).sum())]
            filt_counts = [int((filt_profit > 0).sum()), int((filt_profit <= 0).sum())]
            x = np.arange(2)
            ax.bar(x - 0.2, base_counts, width=0.4, label='기준', color='gray', alpha=0.6)
            ax.bar(x + 0.2, filt_counts, width=0.4, label='필터', color='orange', alpha=0.8)
            ax.set_xticks(x)
            ax.set_xticklabels(['이익', '손실'])
            ax.set_title('이익/손실 거래수 비교')
            ax.set_ylabel('거래수')
            ax.legend(loc='best')
            ax.grid(axis='y', alpha=0.3)

    # (3) 시간대별 수익금
    ax = fig.add_subplot(gs[1, 0])
    if '매수시' in df_all.columns and '매수시' in df_filtered.columns:
        base_by_hour = df_all.groupby('매수시')['수익금'].sum()
        filt_by_hour = df_filtered.groupby('매수시')['수익금'].sum()
        hours = sorted(set(base_by_hour.index.tolist()) | set(filt_by_hour.index.tolist()))
        base_vals = [float(base_by_hour.get(h, 0) or 0) for h in hours]
        filt_vals = [float(filt_by_hour.get(h, 0) or 0) for h in hours]
        x = np.arange(len(hours))
        ax.bar(x - 0.2, base_vals, width=0.4, label='기준', color='gray', alpha=0.6)
        ax.bar(x + 0.2, filt_vals, width=0.4, label='필터', color='orange', alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([str(h) for h in hours], rotation=0, fontsize=8)
        ax.set_title('시간대별 수익금(매수시 기준)')
        ax.axhline(y=0, color='black', linewidth=0.8)
        ax.legend(loc='best')
        ax.grid(axis='y')
    else:
        ax.text(0.5, 0.5, '매수시 컬럼 없음', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')

    # (4) 요일별 수익금
    ax = fig.add_subplot(gs[1, 1])
    if '매수일자' in df_all.columns and '매수일자' in df_filtered.columns:
        base_dates = pd.to_datetime(df_all['매수일자'].astype(str), format='%Y%m%d', errors='coerce')
        filt_dates = pd.to_datetime(df_filtered['매수일자'].astype(str), format='%Y%m%d', errors='coerce')

        base_tmp = df_all.copy()
        base_tmp['_wd'] = base_dates.dt.weekday
        filt_tmp = df_filtered.copy()
        filt_tmp['_wd'] = filt_dates.dt.weekday

        base_wd = pd.to_numeric(base_tmp['수익금'], errors='coerce').fillna(0).groupby(base_tmp['_wd']).sum()
        filt_wd = pd.to_numeric(filt_tmp['수익금'], errors='coerce').fillna(0).groupby(filt_tmp['_wd']).sum()
        wds = sorted(set(base_wd.index.tolist()) | set(filt_wd.index.tolist()))
        labels_map = ['월', '화', '수', '목', '금', '토', '일']
        labels = [labels_map[int(w)] if (w is not None and 0 <= int(w) <= 6) else str(w) for w in wds]
        x = np.arange(len(wds))
        base_vals = [float(base_wd.get(w, 0) or 0) for w in wds]
        filt_vals = [float(filt_wd.get(w, 0) or 0) for w in wds]
        ax.bar(x - 0.2, base_vals, width=0.4, label='기준', color='gray', alpha=0.6)
        ax.bar(x + 0.2, filt_vals, width=0.4, label='필터', color='orange', alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_title('요일별 수익금(매수일자 기준)')
        ax.axhline(y=0, color='black', linewidth=0.8)
        ax.legend(loc='best')
        ax.grid(axis='y')
    else:
        ax.text(0.5, 0.5, '매수일자 컬럼 없음', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')

    fig.suptitle(f'{backname} 필터 적용 분포/단계 요약 - {save_file_name}', fontsize=14, fontweight='bold')
    plt.savefig(path_sub, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    return path_main, path_sub


def PltShow(gubun, teleQ, df_tsg, df_bct, dict_cn, seed, mdd, startday, endday, starttime, endtime, df_kp_, df_kd_, list_days,
            backname, back_text, label_text, save_file_name, schedul, plotgraph, buy_vars=None, sell_vars=None,
            buystg=None, sellstg=None, buystg_name=None, sellstg_name=None, ml_train_mode='train', progress_logs=None):
    output_dir = ensure_backtesting_output_dir(save_file_name)
    df_tsg['수익금합계020'] = df_tsg['수익금합계'].rolling(window=20).mean().round(2)
    df_tsg['수익금합계060'] = df_tsg['수익금합계'].rolling(window=60).mean().round(2)
    df_tsg['수익금합계120'] = df_tsg['수익금합계'].rolling(window=120).mean().round(2)
    df_tsg['수익금합계240'] = df_tsg['수익금합계'].rolling(window=240).mean().round(2)
    df_tsg['수익금합계480'] = df_tsg['수익금합계'].rolling(window=480).mean().round(2)

    profit_values = df_tsg['수익금'].to_numpy(dtype=np.float64)
    df_tsg['이익금액'] = np.where(profit_values >= 0, profit_values, 0)
    df_tsg['손실금액'] = np.where(profit_values < 0, profit_values, 0)

    # 거래가 매우 많으면(예: 60,000건) 차트 렌더링/강화분석 시간이 길어 텔레그램 알림이 늦어질 수 있어,
    # 우선 "진행 중" 메시지를 먼저 전송합니다.
    if teleQ is not None:
        try:
            lines = []
            has_condition = bool(buystg_name or sellstg_name or buystg or sellstg)
            if has_condition:
                sk_short = 'N/A'
                try:
                    if ENHANCED_ANALYSIS_AVAILABLE and (buystg or sellstg):
                        sk = ComputeStrategyKey(buystg=buystg, sellstg=sellstg)
                        if sk:
                            sk_short = (str(sk)[:12] + '...') if len(str(sk)) > 12 else str(sk)
                except Exception:
                    sk_short = 'N/A'

                is_opt = bool(backname and ('최적화' in str(backname)))
                buy_label = "매수 최적화 조건식" if is_opt else "매수 조건식"
                sell_label = "매도 최적화 조건식" if is_opt else "매도 조건식"
                buy_name = buystg_name if buystg_name else 'N/A'
                sell_name = sellstg_name if sellstg_name else 'N/A'

                lines.append("매수/매도 조건식(이름):")
                lines.append(f"- 전략키: {sk_short}")
                lines.append(f"- {buy_label}: {buy_name}")
                lines.append(f"- {sell_label}: {sell_name}")
                lines.append("- 상세 설명/코드/산출물: report.txt 및 models/strategy_code.txt 참고")

            if progress_logs:
                if lines:
                    lines.append("")
                lines.append("백테스트 진행 로그:")
                lines.extend(_format_progress_logs(progress_logs))

            if lines:
                teleQ.put("\n".join(lines))
            teleQ.put(f'{backname} {save_file_name.split("_")[1]} 분석/차트 생성 중... (거래 {len(df_tsg):,}회)')
        except:
            pass
    sig_list = df_tsg['수익금'].to_list()
    mdd_list = []
    for i in range(30):
        random.shuffle(sig_list)
        df_tsg[f'수익금{i}'] = sig_list
        df_tsg[f'수익금합계{i}'] = df_tsg[f'수익금{i}'].cumsum()
        df_tsg.drop(columns=[f'수익금{i}'], inplace=True)
        try:
            array = np.array(df_tsg[f'수익금합계{i}'], dtype=np.float64)
            lower = np.argmax(np.maximum.accumulate(array) - array)
            upper = np.argmax(array[:lower])
            mdd_ = round(abs(array[upper] - array[lower]) / (array[upper] + seed) * 100, 2)
        except:
            mdd_ = 0.
        mdd_list.append(mdd_)

    is_min = len(str(endtime)) < 5
    df_sg = df_tsg[['수익금']].copy()
    df_sg['일자'] = df_sg.index
    df_sg['일자'] = df_sg['일자'].apply(lambda x: strp_time('%Y%m%d%H%M%S' if not is_min else '%Y%m%d%H%M', x))
    df_sg = df_sg.set_index('일자')

    df_ts = df_sg.resample('D').sum()
    df_ts['수익금합계'] = df_ts['수익금'].cumsum()
    df_ts['수익금합계'] = ((df_ts['수익금합계'] + seed) / seed - 1) * 100

    df_kp, df_kd, df_bc = None, None, None
    if dict_cn is not None:
        df_kp = df_kp_[(df_kp_['index'] >= str(startday)) & (df_kp_['index'] <= str(endday))].copy()
        df_kd = df_kd_[(df_kd_['index'] >= str(startday)) & (df_kd_['index'] <= str(endday))].copy()
        df_kp['종가'] = (df_kp['종가'] / df_kp['종가'].iloc[0] - 1) * 100
        df_kd['종가'] = (df_kd['종가'] / df_kd['종가'].iloc[0] - 1) * 100
        df_kp['일자'] = df_kp['index'].apply(lambda x: strp_time('%Y%m%d', x))
        df_kd['일자'] = df_kd['index'].apply(lambda x: strp_time('%Y%m%d', x))
        df_kp.drop(columns=['index'], inplace=True)
        df_kd.drop(columns=['index'], inplace=True)
        df_kp.set_index('일자', inplace=True)
        df_kd.set_index('일자', inplace=True)
    else:
        df_bc = pyupbit.get_ohlcv()
        df_bc['일자'] = df_bc.index
        startday = strp_time('%Y%m%d', str(startday))
        endday = strp_time('%Y%m%d%H%M%S', str(endday) + '235959')
        df_bc = df_bc[(df_bc['일자'] >= startday) & (df_bc['일자'] <= endday)]
        df_bc['close'] = (df_bc['close'] / df_bc['close'].iloc[0] - 1) * 100

    df_st = df_tsg[['수익금']].copy()
    df_st['시간'] = df_st.index
    df_st['시간'] = df_st['시간'].apply(lambda x: strp_time('%H%M%S' if not is_min else '%H%M', x[8:]))
    df_st.set_index('시간', inplace=True)
    if not is_min:
        start_time = strp_time('%H%M%S', str(starttime).zfill(6))
        end_time = strp_time('%H%M%S', str(endtime).zfill(6))
    else:
        start_time = strp_time('%H%M', str(starttime).zfill(4))
        end_time = strp_time('%H%M', str(endtime).zfill(4))
    total_sec = (end_time - start_time).total_seconds()
    df_st = df_st.resample(f'{total_sec / 600 if total_sec >= 1800 else 3}min').sum()
    df_st['시간'] = df_st.index
    df_st['시간'] = df_st['시간'].apply(lambda x: strf_time('%H%M%S' if not is_min else '%H%M', x))
    if not is_min:
        df_st['시간'] = df_st['시간'].apply(lambda x: f'{x[:2]}:{x[2:4]}:{x[4:]}')
    else:
        df_st['시간'] = df_st['시간'].apply(lambda x: f'{x[:2]}:{x[2:]}')
    df_st.set_index('시간', inplace=True)
    df_st['이익금액'] = df_st['수익금'].apply(lambda x: x if x >= 0 else 0)
    df_st['손실금액'] = df_st['수익금'].apply(lambda x: x if x < 0 else 0)

    df_wt = df_tsg[['수익금']].copy()
    df_wt['요일'] = df_wt.index
    df_wt['요일'] = df_wt['요일'].apply(lambda x: strp_time('%Y%m%d%H%M%S' if not is_min else '%Y%m%d%H%M', x).weekday())
    sum_0 = df_wt[df_wt['요일'] == 0]['수익금'].sum()
    sum_1 = df_wt[df_wt['요일'] == 1]['수익금'].sum()
    sum_2 = df_wt[df_wt['요일'] == 2]['수익금'].sum()
    sum_3 = df_wt[df_wt['요일'] == 3]['수익금'].sum()
    sum_4 = df_wt[df_wt['요일'] == 4]['수익금'].sum()
    wt_index = ['월', '화', '수', '목', '금']
    wt_data = [sum_0, sum_1, sum_2, sum_3, sum_4]
    if dict_cn is None:
        sum_5 = df_wt[df_wt['요일'] == 5]['수익금'].sum()
        sum_6 = df_wt[df_wt['요일'] == 6]['수익금'].sum()
        wt_index += ['토', '일']
        wt_data += [sum_5, sum_6]
    wt_datap, wt_datam = [], []
    for data in wt_data:
        if data >= 0:
            wt_datap.append(data)
            wt_datam.append(0)
        else:
            wt_datap.append(0)
            wt_datam.append(data)

    df_tsg['index'] = df_tsg.index
    if not is_min:
        df_tsg['index'] = df_tsg['index'].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:12]}:{x[12:14]}')
    else:
        df_tsg['index'] = df_tsg['index'].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:]}')
    df_tsg.set_index('index', inplace=True)

    endx_list = None
    if gubun == '최적화':
        if not is_min:
            endx_list = [df_tsg[df_tsg['매도시간'] < list_days[2][0] * 1000000 + 240000].index[-1]]
        else:
            endx_list = [df_tsg[df_tsg['매도시간'] < list_days[2][0] * 10000 + 2400].index[-1]]
        if list_days[1] is not None:
            for vsday, _, _ in list_days[1]:
                if not is_min:
                    df_tsg_ = df_tsg[df_tsg['매도시간'] < vsday * 1000000]
                else:
                    df_tsg_ = df_tsg[df_tsg['매도시간'] < vsday * 10000]
                if len(df_tsg_) > 0:
                    endx_list.append(df_tsg_.index[-1])

    font_name = 'C:/Windows/Fonts/malgun.ttf'
    font_family = font_manager.FontProperties(fname=font_name).get_name()
    plt.rcParams['font.family'] = font_family
    plt.rcParams['axes.unicode_minus'] = False

    plt.figure(f'{backname} 부가정보', figsize=(12, 10))
    gs = gridspec.GridSpec(nrows=2, ncols=2, height_ratios=[1, 1])
    # noinspection PyTypeChecker
    plt.subplot(gs[0])
    for i in range(30):
        plt.plot(df_tsg.index, df_tsg[f'수익금합계{i}'], linewidth=0.5, label=f'MDD {mdd_list[i]}%')
    plt.plot(df_tsg.index, df_tsg['수익금합계'], linewidth=2, label=f'MDD {mdd}%', color='orange')
    max_mdd = max(mdd_list)
    min_mdd = min(mdd_list)
    avg_mdd = round(sum(mdd_list) / len(mdd_list), 2)
    plt.title(f'Max MDD [{max_mdd}%] | Min MDD [{min_mdd}%] | Avg MDD [{avg_mdd}%]')
    count = int(len(df_tsg) / 15) if int(len(df_tsg) / 15) >= 1 else 1
    plt.xticks(list(df_tsg.index[::count]), rotation=45)
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[1])
    plt.plot(df_ts.index, df_ts['수익금합계'], linewidth=2, label='수익률', color='orange')
    if dict_cn is not None:
        plt.plot(df_kp.index, df_kp['종가'], linewidth=0.5, label='코스피', color='r')
        plt.plot(df_kd.index, df_kd['종가'], linewidth=0.5, label='코스닥', color='b')
    else:
        plt.plot(df_bc.index, df_bc['close'], linewidth=0.5, label='KRW-BTC', color='r')
    plt.title('지수비교' if dict_cn is not None else 'BTC비교')
    count = int(len(df_ts) / 20) if int(len(df_ts) / 20) >= 1 else 1
    plt.xticks(list(df_ts.index[::count]), rotation=45)
    plt.legend(loc='best')
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[2])
    plt.bar(df_st.index, df_st['이익금액'], label='이익금액', color='r')
    plt.bar(df_st.index, df_st['손실금액'], label='손실금액', color='b')
    plt.title('시간별 수익금')
    plt.xticks(list(df_st.index), rotation=45)
    plt.legend(loc='best')
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[3])
    plt.bar(wt_index, wt_datap, label='이익금액', color='r')
    plt.bar(wt_index, wt_datam, label='손실금액', color='b')
    plt.title('요일별 수익금')
    plt.xticks(wt_index)
    plt.legend(loc='best')
    plt.grid()
    plt.tight_layout()
    plt.savefig(str(output_dir / f"{save_file_name}_.png"))

    if buy_vars is None:
        plt.figure(f'{backname} 결과', figsize=(12, 10))
    else:
        plt.figure(f'{backname} 결과', figsize=(12, 12))
    gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[1, 4])
    # noinspection PyTypeChecker
    plt.subplot(gs[0])
    plt.plot(df_bct.index, df_bct['보유금액'], label='보유금액', color='g')
    plt.xticks([])
    if buy_vars is None:
        plt.xlabel('\n' + back_text + '\n' + label_text)
    else:
        plt.xlabel('\n' + back_text + '\n' + label_text + '\n\n' + buy_vars + '\n\n' + sell_vars)
    plt.legend(loc='best')
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[1])
    n_trades = len(df_tsg)
    max_plot_points = 5000
    if n_trades > max_plot_points:
        # 대용량 데이터에서는 bar/scatter 렌더링이 매우 느려지므로, 표시용으로만 구간 집계/샘플링합니다.
        step = int(math.ceil(n_trades / max_plot_points))
        start_idx = np.arange(0, n_trades, step, dtype=np.int64)
        end_idx = np.minimum(start_idx + step - 1, n_trades - 1)
        x = np.arange(len(end_idx))

        profit_bar = np.add.reduceat(df_tsg['이익금액'].to_numpy(dtype=np.float64), start_idx)
        loss_bar = np.add.reduceat(df_tsg['손실금액'].to_numpy(dtype=np.float64), start_idx)

        plt.bar(x, profit_bar, label=f'이익금액(집계:{step}건)', color='r')
        plt.bar(x, loss_bar, label=f'손실금액(집계:{step}건)', color='b')

        def _sample(col: str):
            return df_tsg[col].to_numpy(dtype=np.float64)[end_idx]

        plt.plot(x, _sample('수익금합계480'), linewidth=0.5, label='수익금합계480', color='k')
        plt.plot(x, _sample('수익금합계240'), linewidth=0.5, label='수익금합계240', color='gray')
        plt.plot(x, _sample('수익금합계120'), linewidth=0.5, label='수익금합계120', color='b')
        plt.plot(x, _sample('수익금합계060'), linewidth=0.5, label='수익금합계60', color='g')
        plt.plot(x, _sample('수익금합계020'), linewidth=0.5, label='수익금합계20', color='r')
        plt.plot(x, _sample('수익금합계'), linewidth=2, label='수익금합계', color='orange')

        if gubun == '최적화':
            for i, endx in enumerate(endx_list):
                try:
                    pos_full = df_tsg.index.get_loc(endx)
                    pos = int(pos_full / step)
                    plt.axvline(x=pos, color='red' if i == 0 else 'green', linestyle='--')
                except:
                    continue
            try:
                pos0_full = df_tsg.index.get_loc(endx_list[0])
                pos0 = int(pos0_full / step)
                plt.axvspan(pos0, x[-1], facecolor='gray', alpha=0.1)
            except:
                pass

        tick_step = max(1, int(len(x) / 20))
        tick_positions = list(x[::tick_step])
        tick_labels = [str(v) for v in df_tsg.index[end_idx][::tick_step]]
        plt.xticks(tick_positions, tick_labels, rotation=45)
    else:
        plt.bar(df_tsg.index, df_tsg['이익금액'], label='이익금액', color='r')
        plt.bar(df_tsg.index, df_tsg['손실금액'], label='손실금액', color='b')
        plt.plot(df_tsg.index, df_tsg['수익금합계480'], linewidth=0.5, label='수익금합계480', color='k')
        plt.plot(df_tsg.index, df_tsg['수익금합계240'], linewidth=0.5, label='수익금합계240', color='gray')
        plt.plot(df_tsg.index, df_tsg['수익금합계120'], linewidth=0.5, label='수익금합계120', color='b')
        plt.plot(df_tsg.index, df_tsg['수익금합계060'], linewidth=0.5, label='수익금합계60', color='g')
        plt.plot(df_tsg.index, df_tsg['수익금합계020'], linewidth=0.5, label='수익금합계20', color='r')
        plt.plot(df_tsg.index, df_tsg['수익금합계'], linewidth=2, label='수익금합계', color='orange')
        if gubun == '최적화':
            for i, endx in enumerate(endx_list):
                plt.axvline(x=endx, color='red' if i == 0 else 'green', linestyle='--')
            plt.axvspan(endx_list[0], df_tsg.index[-1], facecolor='gray', alpha=0.1)
        count = int(len(df_tsg) / 20) if int(len(df_tsg) / 20) >= 1 else 1
        plt.xticks(list(df_tsg.index[::count]), rotation=45)
    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.savefig(str(output_dir / f"{save_file_name}.png"))

    teleQ.put(f'{backname} {save_file_name.split("_")[1]} 완료.')
    teleQ.put(str(output_dir / f"{save_file_name}_.png"))
    teleQ.put(str(output_dir / f"{save_file_name}.png"))

    # [2025-12-08] 분석 차트 생성 및 텔레그램 전송 (8개 기본 분석 차트)
    PltAnalysisCharts(df_tsg, save_file_name, teleQ)

    # [2025-12-09] 매수/매도 비교 분석 및 CSV 출력
    # - 강화 분석을 사용할 경우: detail/filter CSV는 강화 분석 결과로 통합(중복 생성 방지)
    # NOTE: avoid circular import by resolving RunFullAnalysis lazily.
    try:
        from backtester.back_static import RunFullAnalysis
    except Exception as e:
        raise ImportError(f"RunFullAnalysis import failed: {e}")

    full_result = RunFullAnalysis(
        df_tsg,
        save_file_name,
        teleQ,
        export_detail=not ENHANCED_ANALYSIS_AVAILABLE,
        export_summary=True,
        export_filter=not ENHANCED_ANALYSIS_AVAILABLE,
        include_filter_recommendations=True
    )

    # [2025-12-10] 강화된 분석 실행 (14개 ML/통계 분석 차트)
    enhanced_result = None
    enhanced_error = None
    enhanced_available = ENHANCED_ANALYSIS_AVAILABLE
    if enhanced_available:
        try:
            from backtester.back_analysis_enhanced import RunEnhancedAnalysis
        except Exception as e:
            enhanced_error = e
            enhanced_available = False

    if enhanced_available:
        try:
            try:
                from backtester.back_static import (
                    SEGMENT_ANALYSIS_MODE,
                    SEGMENT_ANALYSIS_OPTUNA,
                    SEGMENT_ANALYSIS_TEMPLATE_COMPARE,
                )
            except Exception:
                SEGMENT_ANALYSIS_MODE = 'phase2+3'
                SEGMENT_ANALYSIS_OPTUNA = False
                SEGMENT_ANALYSIS_TEMPLATE_COMPARE = True

            enhanced_result = RunEnhancedAnalysis(
                df_tsg,
                save_file_name,
                teleQ,
                buystg=buystg,
                sellstg=sellstg,
                buystg_name=buystg_name,
                sellstg_name=sellstg_name,
                backname=backname,
                ml_train_mode=ml_train_mode,
                send_condition_summary=False,
                segment_analysis_mode=SEGMENT_ANALYSIS_MODE,
                segment_output_dir=str(output_dir),
                segment_optuna=SEGMENT_ANALYSIS_OPTUNA,
                segment_template_compare=SEGMENT_ANALYSIS_TEMPLATE_COMPARE,
            )

            try:
                from backtester.back_static import (
                    _build_filter_mask_from_generated_code,
                    _build_segment_mask_from_global_best,
                )
            except Exception:
                _build_filter_mask_from_generated_code = None
                _build_segment_mask_from_global_best = None

            # [2025-12-19] 자동 생성 필터 조합 적용 미리보기 차트(2개) 생성/전송
            try:
                if teleQ is not None and enhanced_result:
                    gen = enhanced_result.get('generated_code')
                    df_enh = enhanced_result.get('enhanced_df')
                    if isinstance(gen, dict) and isinstance(df_enh, pd.DataFrame) and not df_enh.empty:
                        if _build_filter_mask_from_generated_code is None:
                            if teleQ is not None:
                                teleQ.put("Filter preview skipped: helper load failed")
                            mask_info = {'mask': None, 'error': 'helper_missing'}
                        else:
                            mask_info = _build_filter_mask_from_generated_code(df_enh, gen)
                        if mask_info and mask_info.get('mask') is not None:
                            df_filt = df_enh[mask_info['mask']].copy()

                            try:
                                total_profit = int(pd.to_numeric(df_enh['수익금'], errors='coerce').fillna(0).sum())
                                filt_profit = int(pd.to_numeric(df_filt['수익금'], errors='coerce').fillna(0).sum())
                                ex_pct = (1.0 - (len(df_filt) / max(1, len(df_enh)))) * 100.0
                                teleQ.put(
                                    "필터 적용 미리보기:\n"
                                    f"- 거래수: {len(df_enh):,} → {len(df_filt):,} (제외 {ex_pct:.1f}%)\n"
                                    f"- 수익금: {total_profit:,}원 → {filt_profit:,}원 ({(filt_profit-total_profit):+,}원)\n"
                                    "- 이미지: 필터 적용 미리보기 2종 전송"
                                )
                            except Exception:
                                pass

                            p_main, p_sub = PltFilterAppliedPreviewCharts(
                                df_enh,
                                df_filt,
                                save_file_name=save_file_name,
                                backname=backname,
                                seed=seed,
                                generated_code=gen,
                                buystg=buystg,
                                sellstg=sellstg,
                                back_text=back_text,
                                label_text=label_text,
                            )
                            if p_sub:
                                teleQ.put(p_sub)
                            if p_main:
                                teleQ.put(p_main)
                            if not p_main and not p_sub:
                                teleQ.put("필터 적용 미리보기: 이미지 생성 실패(경로 없음)")
                        else:
                            err = mask_info.get('error') if isinstance(mask_info, dict) else 'N/A'
                            failed_expr = mask_info.get('failed_expr') if isinstance(mask_info, dict) else None
                            msg = "필터 적용 미리보기: 마스크 생성 실패"
                            if err:
                                msg += f"\n- 오류: {err}"
                            if failed_expr:
                                msg += f"\n- 실패 조건식: {failed_expr}"
                            teleQ.put(msg)
            except Exception as e:
                if teleQ is not None:
                    teleQ.put(f"필터 적용 미리보기: 생성 오류 - {e}")
                print_exc()

            # [2025-12-20] 세그먼트 필터 조합 적용 미리보기 차트(2개) 생성/전송
            try:
                if teleQ is not None and enhanced_result:
                    seg_outputs = enhanced_result.get('segment_outputs') or {}
                    phase2 = seg_outputs.get('phase2') or {}
                    global_best = phase2.get('global_best')
                    df_enh = enhanced_result.get('enhanced_df')
                    if isinstance(global_best, dict) and isinstance(df_enh, pd.DataFrame) and not df_enh.empty:
                        if _build_segment_mask_from_global_best is None:
                            if teleQ is not None:
                                teleQ.put("Segment preview skipped: helper load failed")
                            seg_mask_info = {'mask': None, 'error': 'helper_missing'}
                        else:
                            seg_mask_info = _build_segment_mask_from_global_best(df_enh, global_best)
                        if seg_mask_info and seg_mask_info.get('mask') is not None:
                            df_seg_filt = df_enh[seg_mask_info['mask']].copy()
                            try:
                                total_profit = int(pd.to_numeric(df_enh['수익금'], errors='coerce').fillna(0).sum())
                                filt_profit = int(pd.to_numeric(df_seg_filt['수익금'], errors='coerce').fillna(0).sum())
                                ex_pct = (1.0 - (len(df_seg_filt) / max(1, len(df_enh)))) * 100.0
                                combo_map = global_best.get('combination') or {}
                                total_filters = sum(len(v.get('filters') or []) for v in combo_map.values())
                                excluded_segments = sum(1 for v in combo_map.values() if v.get('exclude_segment'))
                                filter_segments = sum(1 for v in combo_map.values() if v.get('filters'))
                                no_filter_segments = max(0, len(combo_map) - filter_segments - excluded_segments)
                                seg_lines = [
                                    "세그먼트 필터 적용 미리보기:",
                                    f"- 구간/필터: {len(combo_map):,}구간, 필터 {total_filters:,}개",
                                    "- 적용 방식: 시가총액/시간 구간 분리 → 구간별 필터 AND 적용",
                                    f"- 구간 상태: 필터적용 {filter_segments:,}구간, 무필터 {no_filter_segments:,}구간, 전체제외 {excluded_segments:,}구간",
                                    f"- 거래수: {len(df_enh):,} → {len(df_seg_filt):,} (제외 {ex_pct:.1f}%)",
                                    f"- 수익금: {total_profit:,}원 → {filt_profit:,}원 ({(filt_profit-total_profit):+,}원)",
                                ]

                                out_range = int(seg_mask_info.get('out_of_range_trades', 0) or 0)
                                if out_range > 0:
                                    seg_lines.append(f"- 구간 외 거래: {out_range:,}건")

                                miss_cols = seg_mask_info.get('missing_columns') or []
                                if miss_cols:
                                    sample = ", ".join(miss_cols[:5])
                                    tail = "..." if len(miss_cols) > 5 else ""
                                    seg_lines.append(f"- 누락 컬럼: {sample}{tail}")

                                file_refs = []
                                for key in ('segment_code_path', 'global_combo_path', 'local_combo_path',
                                            'filters_path', 'ranges_path', 'summary_path'):
                                    p = phase2.get(key)
                                    if p:
                                        try:
                                            file_refs.append(Path(p).name)
                                        except Exception:
                                            file_refs.append(str(p))
                                if file_refs:
                                    seg_lines.append("- 상세 파일: " + ", ".join(file_refs[:6]))
                                    if len(file_refs) > 6:
                                        seg_lines.append(f"- 상세 파일 추가: 외 {len(file_refs) - 6}개")

                                seg_lines.append("- 이미지: 세그먼트 필터 미리보기 2종 전송")
                                teleQ.put("\n".join(seg_lines))
                            except Exception:
                                pass

                            p_main, p_sub = PltFilterAppliedPreviewCharts(
                                df_enh,
                                df_seg_filt,
                                save_file_name=save_file_name,
                                backname=f"{backname} 세그먼트" if backname else "세그먼트",
                                seed=seed,
                                generated_code=None,
                                buystg=buystg,
                                sellstg=sellstg,
                                file_tag='segment',
                                segment_combo_map=combo_map,
                                back_text=back_text,
                                label_text=label_text,
                            )
                            if p_sub:
                                teleQ.put(p_sub)
                            if p_main:
                                teleQ.put(p_main)
                            if not p_main and not p_sub:
                                teleQ.put("세그먼트 필터 미리보기: 이미지 생성 실패(경로 없음)")
                        else:
                            err = seg_mask_info.get('error') if isinstance(seg_mask_info, dict) else 'N/A'
                            msg = "세그먼트 필터 미리보기: 마스크 생성 실패"
                            if err:
                                msg += f"\n- 오류: {err}"
                            teleQ.put(msg)
                    else:
                        msg_lines = ["세그먼트 필터 미리보기: 전역 조합(global_best) 없음"]
                        if not isinstance(df_enh, pd.DataFrame) or df_enh.empty:
                            msg_lines.append("- 강화 분석 데이터가 없거나 비어있어 미리보기를 건너뜀")
                        else:
                            msg_lines.append("- 전역 조합 생성 실패로 세그먼트 필터 적용 미리보기 생략")
                            msg_lines.append("- 가능한 원인: 세그먼트별 유효 필터/조합 부족, 제외율/최소거래수 제약")
                            msg_lines.append("- 확인 파일: *_segment_filters.csv, *_segment_local_combos.csv, *_segment_summary.csv")
                            msg_lines.append("- 조정 후보: min_trades/max_exclusion, max_filters_per_segment/beam_width")
                        teleQ.put("\n".join(msg_lines))
            except Exception as e:
                if teleQ is not None:
                    teleQ.put(f"세그먼트 필터 미리보기: 생성 오류 - {e}")
                print_exc()
        except Exception as e:
            enhanced_error = e
            print_exc()
            # 강화 분석 실패 시: 기본 detail/filter CSV를 생성해 결과 보존
            try:
                from backtester.analysis.exports import ExportBacktestCSV
                from backtester.analysis.metrics import CalculateDerivedMetrics, AnalyzeFilterEffects
                ExportBacktestCSV(
                    df_tsg,
                    save_file_name,
                    teleQ,
                    write_detail=True,
                    write_summary=False,
                    write_filter=True
                )
                if teleQ is not None:
                    already_sent = bool(full_result and full_result.get('recommendations'))
                    if not already_sent:
                        df_fallback = CalculateDerivedMetrics(df_tsg)
                        filter_results = AnalyzeFilterEffects(df_fallback)
                        top_filters = [f for f in filter_results if f.get('적용권장', '').count('★') >= 2]
                        recs = [
                            f"[{f['분류']}] {f['필터명']}: 수익개선 {f['수익개선금액']:,}원 예상"
                            for f in top_filters[:5]
                        ]
                        if recs:
                            teleQ.put("📊 필터 추천:\n" + "\n".join(recs))
            except:
                print_exc()

    # [2025-12-14] 산출물 메타 리포트(txt) 저장
    try:
        from backtester.back_static import WriteGraphOutputReport
    except Exception as e:
        raise ImportError(f"WriteGraphOutputReport import failed: {e}")

    WriteGraphOutputReport(
        save_file_name=save_file_name,
        df_tsg=df_tsg,
        backname=backname,
        seed=seed,
        mdd=mdd,
        startday=startday,
        endday=endday,
        starttime=starttime,
        endtime=endtime,
        buy_vars=buy_vars,
        sell_vars=sell_vars,
        buystg=buystg,
        sellstg=sellstg,
        full_result=full_result,
        enhanced_result=enhanced_result,
        enhanced_error=enhanced_error
    )

    if not schedul and not plotgraph:
        plt.show()


def PltAnalysisCharts(df_tsg, save_file_name, teleQ):
    """
    확장된 상세기록 데이터를 기반으로 분석 차트를 생성하고 텔레그램으로 전송

    Args:
        df_tsg: 확장된 상세기록 DataFrame (50개 컬럼)
        save_file_name: 저장 파일명
        teleQ: 텔레그램 전송 큐

    차트 목록:
        1. 시간대별 수익금 분포
        2. 등락율 구간별 수익금 분포
        3. 체결강도 구간별 수익금 분포 + 승률
        4. 거래대금 구간별 수익금 분포
        5. 시가총액 구간별 수익금 분포
        6. 보유시간 구간별 수익금 분포
        7. 변수 간 상관관계 히트맵
        8. 등락율 vs 수익률 산점도 + 추세선
    """
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

    # 확장 컬럼 존재 여부 확인
    extended_columns = ['매수시', '매수등락율', '매수체결강도', '매수당일거래대금', '시가총액']
    has_extended = all(col in df_tsg.columns for col in extended_columns)

    if not has_extended or len(df_tsg) < 5:
        return  # 데이터가 부족하거나 확장 컬럼이 없으면 건너뜀

    try:
        # 차트용 복사본 (원본 df_tsg에 임시 컬럼 추가되는 부작용 방지)
        df_tsg = df_tsg.copy()
        from matplotlib.ticker import MaxNLocator, AutoMinorLocator

        # 한글 폰트 설정 (개선된 버전)
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_family = font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_family
            plt.rcParams['font.sans-serif'] = [font_family]
        except:
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # x축 라벨/히트맵 글자 겹침 방지를 위해 세로 여백을 늘립니다.
        fig = plt.figure(figsize=(16, 22))
        fig.suptitle(f'백테스팅 분석 차트 - {save_file_name}', fontsize=14, fontweight='bold')

        gs = gridspec.GridSpec(4, 2, figure=fig, hspace=0.45, wspace=0.25)

        # 색상 정의
        color_profit = '#2ECC71'  # 녹색 (이익)
        color_loss = '#E74C3C'    # 빨간색 (손실)
        color_bar = '#3498DB'     # 파란색

        # ============ Chart 1: 매수 시각별(분 단위) 수익 분포 ============
        ax1 = fig.add_subplot(gs[0, 0])
        if '매수시' in df_tsg.columns and '매수분' in df_tsg.columns:
            hour = df_tsg['매수시'].fillna(0).astype(int).astype(str).str.zfill(2)
            minute = df_tsg['매수분'].fillna(0).astype(int).astype(str).str.zfill(2)
            df_tsg['매수시각'] = hour + ':' + minute
            df_time = df_tsg.groupby('매수시각', observed=True).agg({
                '수익금': 'sum',
                '수익률': 'mean',
                '종목명': 'count'
            }).reset_index()
            df_time.columns = ['매수시각', '수익금', '평균수익률', '거래횟수']
            df_time = df_time.sort_values('매수시각')

            x_pos = range(len(df_time))
            colors = [color_profit if x >= 0 else color_loss for x in df_time['수익금']]
            bars = ax1.bar(x_pos, df_time['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
            ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax1.set_xlabel('매수 시각 (HH:MM)')
            ax1.set_ylabel('총 수익금')
            ax1.set_title('매수 시각별 수익금 분포(분 단위) + 거래횟수')

            ax1_twin = ax1.twinx()
            ax1_twin.plot(x_pos, df_time['거래횟수'], 'o-', color='orange', linewidth=1.5, markersize=4)
            ax1_twin.set_ylabel('거래횟수', color='orange')
            ax1_twin.tick_params(axis='y', labelcolor='orange')

            tick_step = max(1, int(len(df_time) / 12))
            ax1.set_xticks(list(range(0, len(df_time), tick_step)))
            ax1.set_xticklabels(df_time['매수시각'].iloc[::tick_step], rotation=45, ha='right', fontsize=8)

            if len(df_time) <= 25:
                for bar, val in zip(bars, df_time['수익금']):
                    if abs(val) > 0:
                        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                                 f'{val/10000:.0f}만', ha='center',
                                 va='bottom' if val >= 0 else 'top', fontsize=7)
        else:
            df_hour = df_tsg.groupby('매수시').agg({'수익금': 'sum', '수익률': 'mean'}).reset_index()
            colors = [color_profit if x >= 0 else color_loss for x in df_hour['수익금']]
            bars = ax1.bar(df_hour['매수시'], df_hour['수익금'], color=colors, alpha=0.8, edgecolor='black',
                           linewidth=0.5)
            ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax1.set_xlabel('매수 시간대 (시)')
            ax1.set_ylabel('총 수익금')
            ax1.set_title('시간대별 수익금 분포')
            ax1.set_xticks(range(9, 16))
            for bar, val in zip(bars, df_hour['수익금']):
                if abs(val) > 0:
                    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                             f'{val/10000:.0f}만', ha='center',
                             va='bottom' if val >= 0 else 'top', fontsize=8)

        # ============ Chart 2: 등락율별 수익 분포 ============
        ax2 = fig.add_subplot(gs[0, 1])
        bins = [0, 5, 10, 15, 20, 30, 100]
        labels = ['0-5%', '5-10%', '10-15%', '15-20%', '20-30%', '30%+']
        df_tsg['등락율구간'] = pd.cut(df_tsg['매수등락율'], bins=bins, labels=labels, right=False)
        df_rate = df_tsg.groupby('등락율구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_rate.columns = ['등락율구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_rate))
        colors = [color_profit if x >= 0 else color_loss for x in df_rate['수익금']]
        ax2.bar(x, df_rate['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.set_xlabel('매수 등락율 구간')
        ax2.set_ylabel('총 수익금')
        ax2.set_title('등락율 구간별 수익금 분포')
        ax2.set_xticks(x)
        ax2.set_xticklabels(df_rate['등락율구간'], rotation=45, ha='right')

        # 거래횟수 표시
        ax2_twin = ax2.twinx()
        ax2_twin.plot(x, df_rate['거래횟수'], 'o-', color='orange', linewidth=2, markersize=6, label='거래횟수')
        ax2_twin.set_ylabel('거래횟수', color='orange')
        ax2_twin.tick_params(axis='y', labelcolor='orange')

        # ============ Chart 3: 체결강도별 수익 분포 ============
        ax3 = fig.add_subplot(gs[1, 0])
        bins_ch = [0, 80, 100, 120, 150, 200, 500]
        labels_ch = ['~80', '80-100', '100-120', '120-150', '150-200', '200+']
        df_tsg['체결강도구간'] = pd.cut(df_tsg['매수체결강도'], bins=bins_ch, labels=labels_ch, right=False)
        df_ch = df_tsg.groupby('체결강도구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_ch.columns = ['체결강도구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_ch))
        colors = [color_profit if x >= 0 else color_loss for x in df_ch['수익금']]
        ax3.bar(x, df_ch['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax3.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax3.set_xlabel('매수 체결강도 구간')
        ax3.set_ylabel('총 수익금')
        ax3.set_title('체결강도 구간별 수익금 분포')
        ax3.set_xticks(x)
        ax3.set_xticklabels(df_ch['체결강도구간'], rotation=45, ha='right')

        # 승률 계산 및 표시
        ax3_twin = ax3.twinx()
        win_rates = []
        for grp in df_ch['체결강도구간']:
            grp_data = df_tsg[df_tsg['체결강도구간'] == grp]
            if len(grp_data) > 0:
                wr = (grp_data['수익금'] > 0).sum() / len(grp_data) * 100
                win_rates.append(wr)
            else:
                win_rates.append(0)
        ax3_twin.plot(x, win_rates, 's--', color='purple', linewidth=2, markersize=6, label='승률')
        ax3_twin.set_ylabel('승률 (%)', color='purple')
        ax3_twin.tick_params(axis='y', labelcolor='purple')
        ax3_twin.set_ylim(0, 100)

        # ============ Chart 4: 거래대금별 수익 분포 ============
        ax4 = fig.add_subplot(gs[1, 1])
        money_series = df_tsg['매수당일거래대금'].dropna()
        # STOM 백테스팅 상세 테이블의 당일거래대금 단위는 "백만"입니다.
        # (예: 10,000 = 100억, 1,000,000 = 1조)
        money_unit = '백만'

        if money_unit == '백만':
            # 기본 분할(억/조 단위로 읽기 쉽게 라벨링, 실제 데이터 단위는 백만)
            max_val = float(money_series.max()) if len(money_series) > 0 else 0.0
            # (백만) 단위: 500=5억, 5,000=50억, 1,000,000=1조
            base_edges = [0, 500, 1000, 2000, 3000, 5000, 7000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]

            edges = [e for e in base_edges if e < max_val]
            # 상단 구간 보정(최대값을 포함하도록 마지막 경계 추가)
            next_edge = next((e for e in base_edges if e >= max_val), None)
            if next_edge is not None:
                edges.append(next_edge)
            else:
                # 1조 이상인 경우: 1조(=1,000,000백만) 단위로 확장
                max_jo = int(math.ceil(max_val / 1000000)) if max_val > 0 else 1
                step_jo = 1  # 1조 단위 고정(요구사항: 1조 이상은 1조 단위)
                step = step_jo * 1000000
                edges = [e for e in edges if e < 1000000]
                for e in range(1000000, (max_jo + step_jo) * 1000000, step):
                    edges.append(e)

            edges = sorted(set(edges))
            if not edges or edges[0] != 0:
                edges = [0] + edges
            edges.append(float('inf'))

            def _fmt_money_million(x):
                if x >= 1000000:
                    return f"{int(round(x / 1000000))}조"
                return f"{int(round(x / 100))}억"

            labels = []
            for i in range(len(edges) - 1):
                lo, hi = edges[i], edges[i + 1]
                if hi == float('inf'):
                    labels.append(f"{_fmt_money_million(lo)}+")
                elif lo == 0:
                    labels.append(f"~{_fmt_money_million(hi)}")
                else:
                    labels.append(f"{_fmt_money_million(lo)}-{_fmt_money_million(hi)}")

            df_tsg['거래대금구간'] = pd.cut(df_tsg['매수당일거래대금'], bins=edges, labels=labels, right=False)
        df_money = df_tsg.groupby('거래대금구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_money.columns = ['거래대금구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_money))
        colors = [color_profit if x >= 0 else color_loss for x in df_money['수익금']]
        ax4.bar(x, df_money['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax4.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax4.set_xlabel('매수 당일거래대금 구간(라벨: 억/조)')
        ax4.set_ylabel('총 수익금')
        if money_unit == '백만':
            ax4.set_title('거래대금 구간별 수익금 분포 (원본 단위: 백만, 라벨: 억/조)')
        else:
            ax4.set_title('거래대금 구간별 수익금 분포 (단위: 억/조)')
        tick_step = max(1, int(math.ceil(len(df_money) / 8)))
        ax4.set_xticks(list(range(0, len(df_money), tick_step)))
        ax4.set_xticklabels([str(v) for v in df_money['거래대금구간'].iloc[::tick_step]],
                            rotation=30, ha='right', fontsize=8)

        # ============ Chart 5: 시가총액별 수익 분포 ============
        ax5 = fig.add_subplot(gs[2, 0])
        cap_series = df_tsg['시가총액'].dropna()
        cap_max = float(cap_series.max()) if len(cap_series) > 0 else 0.0

        # 1조(=10,000억) 미만: 100억 단위로 구간 생성 (요구사항)
        # 1조 이상: 1조 단위로 구간 확장 (요구사항)
        cap_edges = []
        if cap_max <= 0:
            cap_edges = [0, float('inf')]
        elif cap_max < 10000:
            cap_max_rounded = int(math.ceil(cap_max / 100.0) * 100)
            cap_edges = list(range(0, cap_max_rounded + 100, 100))
            cap_edges.append(float('inf'))
        else:
            base_cap_edges = list(range(0, 10000 + 100, 100))  # 0~1조 미만 100억 단위
            cap_edges = [e for e in base_cap_edges if e < 10000]
            max_jo = int(math.ceil(cap_max / 10000)) if cap_max > 0 else 1
            for e in range(10000, (max_jo + 1) * 10000, 10000):
                cap_edges.append(e)
            cap_edges.append(float('inf'))

        cap_edges = sorted(set(cap_edges))

        def _fmt_cap_eok(x):
            # x: 억 단위
            # - 1조 미만: 억 단위로 명확히 표기(라벨 길이/가독성 고려)
            # - 1조 이상: 조 단위로 표기
            if x >= 10000:
                return f"{int(round(x / 10000))}조"
            return f"{int(round(x))}억"

        cap_labels = []
        for i in range(len(cap_edges) - 1):
            lo, hi = cap_edges[i], cap_edges[i + 1]
            if hi == float('inf'):
                cap_labels.append(f"{_fmt_cap_eok(lo)}+")
            elif lo == 0:
                cap_labels.append(f"~{_fmt_cap_eok(hi)}")
            else:
                cap_labels.append(f"{_fmt_cap_eok(lo)}-{_fmt_cap_eok(hi)}")

        df_tsg['시총구간'] = pd.cut(df_tsg['시가총액'], bins=cap_edges, labels=cap_labels, right=False)
        df_cap = df_tsg.groupby('시총구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_cap.columns = ['시총구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_cap))
        colors = [color_profit if x >= 0 else color_loss for x in df_cap['수익금']]
        ax5.bar(x, df_cap['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax5.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax5.set_xlabel('시가총액 구간 (단위: 억, 1조+는 조)')
        ax5.set_ylabel('총 수익금')
        ax5.set_title('시가총액 구간별 수익금 분포')
        tick_step = max(1, int(math.ceil(len(df_cap) / 8)))
        ax5.set_xticks(list(range(0, len(df_cap), tick_step)))
        ax5.set_xticklabels([str(v) for v in df_cap['시총구간'].iloc[::tick_step]],
                            rotation=30, ha='right', fontsize=8)

        # ============ Chart 6: 보유시간별 수익 분포 ============
        ax6 = fig.add_subplot(gs[2, 1])
        df_tsg['보유시간구간'] = pd.cut(df_tsg['보유시간'],
                                      bins=[0, 60, 180, 300, 600, 1800, float('inf')],
                                      labels=['~1분', '1-3분', '3-5분', '5-10분', '10-30분', '30분+'])
        df_hold = df_tsg.groupby('보유시간구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_hold.columns = ['보유시간구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_hold))
        colors = [color_profit if x >= 0 else color_loss for x in df_hold['수익금']]
        ax6.bar(x, df_hold['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax6.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax6.set_xlabel('보유시간 구간')
        ax6.set_ylabel('총 수익금')
        ax6.set_title('보유시간 구간별 수익금 분포')
        ax6.set_xticks(x)
        ax6.set_xticklabels(df_hold['보유시간구간'], rotation=45, ha='right')

        # ============ Chart 7: 상관관계 히트맵 ============
        ax7 = fig.add_subplot(gs[3, 0])
        corr_columns = ['수익률', '매수등락율', '매수체결강도', '매수회전율', '매수전일비', '보유시간']
        available_cols = [col for col in corr_columns if col in df_tsg.columns]

        if len(available_cols) >= 3:
            col_display = {
                '수익률': '수익률',
                '매수등락율': '매수등락',
                '매수체결강도': '매수체결',
                '매수회전율': '매수회전',
                '매수전일비': '매수전일',
                '보유시간': '보유시간',
            }
            display_labels = [col_display.get(c, c) for c in available_cols]
            df_corr = df_tsg[available_cols].corr()
            im = ax7.imshow(df_corr.values, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
            ax7.set_xticks(range(len(available_cols)))
            ax7.set_yticks(range(len(available_cols)))
            ax7.set_xticklabels(display_labels, rotation=30, ha='right', fontsize=8)
            ax7.set_yticklabels(display_labels, fontsize=8)
            ax7.set_title('변수 간 상관관계')
            ax7.xaxis.set_minor_locator(AutoMinorLocator(2))
            ax7.yaxis.set_minor_locator(AutoMinorLocator(2))

            for i in range(len(available_cols)):
                for j in range(len(available_cols)):
                    text = ax7.text(j, i, f'{df_corr.values[i, j]:.2f}',
                                   ha='center', va='center', color='black', fontsize=8)

            plt.colorbar(im, ax=ax7, shrink=0.8)

        # ============ Chart 8: 산점도 (등락율 vs 수익률) ============
        ax8 = fig.add_subplot(gs[3, 1])
        df_scatter = df_tsg
        if len(df_tsg) > 20000:
            # 산점도는 대용량에서 렌더링 시간이 급증하므로 샘플링(표시용) 처리
            df_scatter = df_tsg.sample(n=20000, random_state=42)
        colors = np.where(df_scatter['수익률'].to_numpy(dtype=np.float64) >= 0, color_profit, color_loss)
        ax8.scatter(df_scatter['매수등락율'], df_scatter['수익률'], c=colors, alpha=0.5, s=20, edgecolors='none')
        ax8.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax8.axvline(x=df_tsg['매수등락율'].mean(), color='blue', linestyle=':', linewidth=0.8, alpha=0.5)
        ax8.set_xlabel('매수 등락율 (%)')
        ax8.set_ylabel('수익률 (%)')
        ax8.set_title('등락율 vs 수익률 산점도')

        # 추세선 추가
        if len(df_scatter) > 10:
            z = np.polyfit(df_scatter['매수등락율'], df_scatter['수익률'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(df_scatter['매수등락율'].min(), df_scatter['매수등락율'].max(), 100)
            ax8.plot(x_line, p(x_line), 'b--', linewidth=1, alpha=0.7, label=f'추세선')
            ax8.legend(fontsize=8)

        # 저장 및 전송
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.tight_layout(rect=[0, 0.03, 1, 0.97])

        output_dir = ensure_backtesting_output_dir(save_file_name)
        analysis_path = str(output_dir / f"{save_file_name}_analysis.png")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.savefig(analysis_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        # 텔레그램 전송
        if teleQ is not None:
            teleQ.put(analysis_path)

    except Exception as e:
        print_exc()
        try:
            plt.close('all')
        except:
            pass


# ============================================================================
# [2025-12-09] 백테스팅 데이터 분석 및 필터링을 위한 함수들
# ============================================================================

def PltBuySellComparison_Legacy(df_tsg, save_file_name, teleQ=None):
    """
    매수/매도 시점 비교 분석 차트를 생성합니다.

    Args:
        df_tsg: 백테스팅 결과 DataFrame (파생 지표 포함)
        save_file_name: 저장 파일명
        teleQ: 텔레그램 전송 큐

    차트 목록:
        1. 등락율 변화 vs 수익률 (사분면 분석)
        2. 체결강도 변화 vs 수익률
        3. 매수 vs 매도 등락율 비교 (대각선)
        4. 위험도 점수별 수익금 분포
        5. 등락추세별 수익금
        6. 체결강도추세별 수익금
        7. 필터 효과 파레토 차트
        8. 손실/이익 거래 특성 비교
        9. 추세 조합별 히트맵
        10. 시간대별 추세 변화
        11. 거래대금 변화율별 수익금
    """
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

    # 매도 시점 데이터 확인
    required_cols = ['매도등락율', '매도체결강도', '등락율변화', '체결강도변화']
    if not all(col in df_tsg.columns for col in required_cols):
        return

    if len(df_tsg) < 5:
        return

    try:
        # 한글 폰트 설정 (개선된 버전)
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_family = font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_family
            plt.rcParams['font.sans-serif'] = [font_family]
        except:
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        fig = plt.figure(figsize=(20, 16))
        fig.suptitle(f'매수/매도 시점 비교 분석 - {save_file_name}', fontsize=14, fontweight='bold')

        gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.35, wspace=0.3)

        color_profit = '#2ECC71'
        color_loss = '#E74C3C'
        color_neutral = '#3498DB'

        # === Chart 1: 등락율 변화 vs 수익률 ===
        ax1 = fig.add_subplot(gs[0, 0])
        colors = [color_profit if x >= 0 else color_loss for x in df_tsg['수익률']]
        ax1.scatter(df_tsg['등락율변화'], df_tsg['수익률'], c=colors, alpha=0.5, s=25)
        ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax1.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
        ax1.set_xlabel('등락율 변화 (매도-매수) %')
        ax1.set_ylabel('수익률 (%)')
        ax1.set_title('등락율 변화 vs 수익률')

        # 사분면 라벨
        ax1.text(0.95, 0.95, '상승+이익', transform=ax1.transAxes, ha='right', va='top', fontsize=8, color='green')
        ax1.text(0.05, 0.95, '하락+이익', transform=ax1.transAxes, ha='left', va='top', fontsize=8, color='blue')
        ax1.text(0.95, 0.05, '상승+손실', transform=ax1.transAxes, ha='right', va='bottom', fontsize=8, color='orange')
        ax1.text(0.05, 0.05, '하락+손실', transform=ax1.transAxes, ha='left', va='bottom', fontsize=8, color='red')

        # === Chart 2: 체결강도 변화 vs 수익률 ===
        ax2 = fig.add_subplot(gs[0, 1])
        colors = [color_profit if x >= 0 else color_loss for x in df_tsg['수익률']]
        ax2.scatter(df_tsg['체결강도변화'], df_tsg['수익률'], c=colors, alpha=0.5, s=25)
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.set_xlabel('체결강도 변화 (매도-매수)')
        ax2.set_ylabel('수익률 (%)')
        ax2.set_title('체결강도 변화 vs 수익률')

        # === Chart 3: 매수 vs 매도 등락율 비교 ===
        ax3 = fig.add_subplot(gs[0, 2])
        colors = [color_profit if x >= 0 else color_loss for x in df_tsg['수익률']]
        ax3.scatter(df_tsg['매수등락율'], df_tsg['매도등락율'], c=colors, alpha=0.5, s=25)
        max_val = max(df_tsg['매수등락율'].max(), df_tsg['매도등락율'].max())
        min_val = min(df_tsg['매수등락율'].min(), df_tsg['매도등락율'].min())
        ax3.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=1, alpha=0.5, label='변화없음')
        ax3.set_xlabel('매수 등락율 (%)')
        ax3.set_ylabel('매도 등락율 (%)')
        ax3.set_title('매수 vs 매도 등락율')
        ax3.legend(fontsize=8)

        # === Chart 4: 위험도 점수 분포 ===
        ax4 = fig.add_subplot(gs[1, 0])
        if '위험도점수' in df_tsg.columns:
            risk_bins = [0, 20, 40, 60, 80, 100]
            risk_labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
            df_tsg['위험도구간'] = pd.cut(df_tsg['위험도점수'], bins=risk_bins, labels=risk_labels, right=False)

            risk_profit = df_tsg.groupby('위험도구간', observed=True)['수익금'].sum()
            colors = [color_profit if x >= 0 else color_loss for x in risk_profit]
            risk_profit.plot(kind='bar', ax=ax4, color=colors, edgecolor='black', linewidth=0.5)
            ax4.set_xlabel('위험도 점수 구간')
            ax4.set_ylabel('총 수익금')
            ax4.set_title('위험도 점수별 수익금 분포')
            ax4.tick_params(axis='x', rotation=45)
            ax4.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

        # === Chart 5: 등락추세별 수익 분포 ===
        ax5 = fig.add_subplot(gs[1, 1])
        if '등락추세' in df_tsg.columns:
            trend_profit = df_tsg.groupby('등락추세')['수익금'].sum()
            trend_count = df_tsg.groupby('등락추세').size()
            colors = [color_profit if trend_profit.get(x, 0) >= 0 else color_loss for x in trend_profit.index]
            bars = ax5.bar(trend_profit.index, trend_profit.values, color=colors, edgecolor='black', linewidth=0.5)
            ax5.set_xlabel('등락 추세')
            ax5.set_ylabel('총 수익금')
            ax5.set_title('등락추세별 수익금')
            ax5.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

            for bar, cnt in zip(bars, trend_count):
                ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=9)

        # === Chart 6: 체결강도추세별 수익 분포 ===
        ax6 = fig.add_subplot(gs[1, 2])
        if '체결강도추세' in df_tsg.columns:
            ch_trend_profit = df_tsg.groupby('체결강도추세')['수익금'].sum()
            ch_trend_count = df_tsg.groupby('체결강도추세').size()
            colors = [color_profit if ch_trend_profit.get(x, 0) >= 0 else color_loss for x in ch_trend_profit.index]
            bars = ax6.bar(ch_trend_profit.index, ch_trend_profit.values, color=colors, edgecolor='black', linewidth=0.5)
            ax6.set_xlabel('체결강도 추세')
            ax6.set_ylabel('총 수익금')
            ax6.set_title('체결강도추세별 수익금')
            ax6.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

            for bar, cnt in zip(bars, ch_trend_count):
                ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=9)

        # === Chart 7: 필터 효과 파레토 차트 ===
        ax7 = fig.add_subplot(gs[2, :2])
        filter_results = AnalyzeFilterEffects(df_tsg)
        if filter_results:
            df_filter = pd.DataFrame(filter_results)
            df_filter = df_filter[df_filter['수익개선금액'] > 0].nlargest(15, '수익개선금액')

            if len(df_filter) > 0:
                x_pos = range(len(df_filter))
                bars = ax7.bar(x_pos, df_filter['수익개선금액'], color=color_profit, edgecolor='black', linewidth=0.5)
                ax7.set_xticks(x_pos)
                ax7.set_xticklabels(df_filter['필터명'], rotation=45, ha='right', fontsize=8)
                ax7.set_ylabel('수익 개선 금액')
                ax7.set_title('필터 적용 시 예상 수익 개선 효과 (Top 15)')

                cumsum = df_filter['수익개선금액'].cumsum()
                cumsum_pct = cumsum / cumsum.iloc[-1] * 100
                ax7_twin = ax7.twinx()
                ax7_twin.plot(x_pos, cumsum_pct, 'ro-', markersize=4, linewidth=1.5)
                ax7_twin.set_ylabel('누적 비율 (%)', color='red')
                ax7_twin.tick_params(axis='y', labelcolor='red')
                ax7_twin.set_ylim(0, 110)

        # === Chart 8: 손실 거래 특성 분석 ===
        ax8 = fig.add_subplot(gs[2, 2])
        loss_trades = df_tsg[df_tsg['수익금'] < 0]
        profit_trades = df_tsg[df_tsg['수익금'] >= 0]

        if len(loss_trades) > 0 and len(profit_trades) > 0:
            compare_cols = ['매수등락율', '매수체결강도', '보유시간']
            available_cols = [c for c in compare_cols if c in df_tsg.columns]

            if available_cols:
                loss_means = [loss_trades[c].mean() for c in available_cols]
                profit_means = [profit_trades[c].mean() for c in available_cols]

                x = np.arange(len(available_cols))
                width = 0.35
                ax8.bar(x - width/2, loss_means, width, label='손실거래', color=color_loss, alpha=0.8)
                ax8.bar(x + width/2, profit_means, width, label='이익거래', color=color_profit, alpha=0.8)
                ax8.set_xticks(x)
                ax8.set_xticklabels(available_cols, rotation=45, ha='right')
                ax8.set_ylabel('평균값')
                ax8.set_title('손실/이익 거래 특성 비교')
                ax8.legend(fontsize=9)

        # === Chart 9: 조건 조합 히트맵 ===
        ax9 = fig.add_subplot(gs[3, 0])
        if '등락추세' in df_tsg.columns and '체결강도추세' in df_tsg.columns:
            pivot = df_tsg.pivot_table(values='수익금', index='등락추세', columns='체결강도추세', aggfunc='sum', fill_value=0)
            im = ax9.imshow(pivot.values, cmap='RdYlGn', aspect='auto')
            ax9.set_xticks(range(len(pivot.columns)))
            ax9.set_yticks(range(len(pivot.index)))
            ax9.set_xticklabels(pivot.columns, fontsize=9)
            ax9.set_yticklabels(pivot.index, fontsize=9)
            ax9.set_xlabel('체결강도 추세')
            ax9.set_ylabel('등락 추세')
            ax9.set_title('추세 조합별 수익금')

            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    val = pivot.values[i, j]
                    text_color = 'white' if abs(val) > pivot.values.max() * 0.5 else 'black'
                    ax9.text(j, i, f'{val/10000:.0f}만', ha='center', va='center', fontsize=8, color=text_color)

            plt.colorbar(im, ax=ax9, shrink=0.8)

        # === Chart 10: 시간대별 매수/매도 추세 변화 ===
        ax10 = fig.add_subplot(gs[3, 1])
        if '매수시' in df_tsg.columns and '등락율변화' in df_tsg.columns:
            hourly_change = df_tsg.groupby('매수시').agg({
                '등락율변화': 'mean',
                '체결강도변화': 'mean',
                '수익금': 'sum'
            })
            x = hourly_change.index
            ax10.bar(x, hourly_change['수익금'], alpha=0.3, color=color_neutral, label='수익금')
            ax10_twin = ax10.twinx()
            ax10_twin.plot(x, hourly_change['등락율변화'], 'g-o', markersize=4, label='등락율변화', linewidth=1.5)
            ax10_twin.plot(x, hourly_change['체결강도변화'] / 10, 'r-s', markersize=4, label='체결강도변화/10', linewidth=1.5)
            ax10.set_xlabel('매수 시간대')
            ax10.set_ylabel('총 수익금')
            ax10_twin.set_ylabel('변화량')
            ax10.set_title('시간대별 추세 변화')
            ax10_twin.legend(loc='upper right', fontsize=8)
            ax10.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)

        # === Chart 11: 거래대금 변화율 분포 ===
        ax11 = fig.add_subplot(gs[3, 2])
        if '거래대금변화율' in df_tsg.columns:
            bins_vol = [0, 0.5, 0.8, 1.0, 1.2, 1.5, 100]
            labels_vol = ['~50%', '50-80%', '80-100%', '100-120%', '120-150%', '150%+']
            df_tsg['거래대금변화구간'] = pd.cut(df_tsg['거래대금변화율'], bins=bins_vol, labels=labels_vol, right=False)

            vol_stats = df_tsg.groupby('거래대금변화구간', observed=True).agg({
                '수익금': 'sum',
                '수익률': 'mean'
            })

            x = range(len(vol_stats))
            colors = [color_profit if x >= 0 else color_loss for x in vol_stats['수익금']]
            bars = ax11.bar(x, vol_stats['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax11.set_xticks(x)
            ax11.set_xticklabels(vol_stats.index, rotation=45, ha='right')
            ax11.set_xlabel('거래대금 변화율')
            ax11.set_ylabel('총 수익금')
            ax11.set_title('거래대금 변화율별 수익금')
            ax11.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

        # 저장 및 전송
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.tight_layout(rect=[0, 0.02, 1, 0.97])

        output_dir = ensure_backtesting_output_dir(save_file_name)
        comparison_path = str(output_dir / f"{save_file_name}_comparison.png")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.savefig(comparison_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if teleQ is not None:
            teleQ.put(comparison_path)

    except Exception as e:
        print_exc()
        try:
            plt.close('all')
        except:
            pass


def PltBuySellComparison(df_tsg, save_file_name, teleQ=None):
    """
    매수/매도 시점 비교 분석 차트를 생성합니다.

    목적:
        - 매수/매도 시점 변화(매도-매수)와 수익률 관계를 파악
        - 손실/이익 거래의 특징 차이를 비교해 매도/필터 개선 근거 제공

    차트 구성 (중복 최소화):
        1) 등락율 변화 vs 수익률
        2) 체결강도 변화 vs 수익률
        3) 매수 vs 매도 등락율
        4) 매수시점 위험도 점수별 수익금 분포
        5) 등락추세별 수익금(거래수)
        6) 체결강도추세별 수익금(거래수)
        7) 등락추세×체결강도추세 조합별 수익금 히트맵
        8) 손실/이익 거래 특성 비교(매수단/보유시간)
        9) 손실/이익 거래 변화량 비교(매도-매수)
        10) 3D 히트맵: 매수시간×시가총액 → 평균 수익률
        11) 보유시간 vs 수익률 산점도(분 단위)
    """
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

    # 매도 시점 데이터 확인
    required_cols = ['매도등락율', '매도체결강도', '등락율변화', '체결강도변화']
    if not all(col in df_tsg.columns for col in required_cols):
        return

    if len(df_tsg) < 5:
        return

    try:
        df_tsg = df_tsg.copy()
        from matplotlib.ticker import MaxNLocator, AutoMinorLocator

        # 한글 폰트 설정 (개선된 버전)
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_family = font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_family
            plt.rcParams['font.sans-serif'] = [font_family]
        except:
            plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        fig = plt.figure(figsize=(22, 26))
        fig.suptitle(f'매수/매도 시점 비교 분석 - {save_file_name}', fontsize=14, fontweight='bold')
        gs = gridspec.GridSpec(5, 3, figure=fig, hspace=0.55, wspace=0.32)

        color_profit = '#2ECC71'
        color_loss = '#E74C3C'
        color_neutral = '#3498DB'
        df_scatter = df_tsg
        if len(df_tsg) > 20000:
            # 산점도는 대용량에서 렌더링 시간이 급증하므로 샘플링(표시용) 처리
            df_scatter = df_tsg.sample(n=20000, random_state=42)

        # === Chart 1: 등락율 변화 vs 수익률 ===
        ax1 = fig.add_subplot(gs[0, 0])
        colors = np.where(df_scatter['수익률'].to_numpy(dtype=np.float64) >= 0, color_profit, color_loss)
        ax1.scatter(df_scatter['등락율변화'], df_scatter['수익률'], c=colors, alpha=0.5, s=25, edgecolors='none')
        ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax1.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
        ax1.set_xlabel('등락율 변화 (매도-매수) %')
        ax1.set_ylabel('수익률 (%)')
        ax1.set_title('등락율 변화 vs 수익률')
        ax1.xaxis.set_major_locator(MaxNLocator(nbins=9))
        ax1.yaxis.set_major_locator(MaxNLocator(nbins=9))
        ax1.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax1.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax1.grid(True, which='both', alpha=0.25)

        # 사분면 라벨
        ax1.text(0.95, 0.95, '상승+이익', transform=ax1.transAxes, ha='right', va='top', fontsize=8, color='green')
        ax1.text(0.05, 0.95, '하락+이익', transform=ax1.transAxes, ha='left', va='top', fontsize=8, color='blue')
        ax1.text(0.95, 0.05, '상승+손실', transform=ax1.transAxes, ha='right', va='bottom', fontsize=8, color='orange')
        ax1.text(0.05, 0.05, '하락+손실', transform=ax1.transAxes, ha='left', va='bottom', fontsize=8, color='red')

        # === Chart 2: 체결강도 변화 vs 수익률 ===
        ax2 = fig.add_subplot(gs[0, 1])
        colors = np.where(df_scatter['수익률'].to_numpy(dtype=np.float64) >= 0, color_profit, color_loss)
        ax2.scatter(df_scatter['체결강도변화'], df_scatter['수익률'], c=colors, alpha=0.5, s=25, edgecolors='none')
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.set_xlabel('체결강도 변화 (매도-매수)')
        ax2.set_ylabel('수익률 (%)')
        ax2.set_title('체결강도 변화 vs 수익률')
        ax2.xaxis.set_major_locator(MaxNLocator(nbins=9))
        ax2.yaxis.set_major_locator(MaxNLocator(nbins=9))
        ax2.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax2.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax2.grid(True, which='both', alpha=0.25)

        # === Chart 3: 매수 vs 매도 등락율 비교 ===
        ax3 = fig.add_subplot(gs[0, 2])
        colors = np.where(df_scatter['수익률'].to_numpy(dtype=np.float64) >= 0, color_profit, color_loss)
        ax3.scatter(df_scatter['매수등락율'], df_scatter['매도등락율'], c=colors, alpha=0.5, s=25, edgecolors='none')
        max_val = max(df_tsg['매수등락율'].max(), df_tsg['매도등락율'].max())
        min_val = min(df_tsg['매수등락율'].min(), df_tsg['매도등락율'].min())
        ax3.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=1, alpha=0.5, label='변화없음')
        ax3.set_xlabel('매수 등락율 (%)')
        ax3.set_ylabel('매도 등락율 (%)')
        ax3.set_title('매수 vs 매도 등락율')
        ax3.legend(fontsize=8)
        ax3.xaxis.set_major_locator(MaxNLocator(nbins=9))
        ax3.yaxis.set_major_locator(MaxNLocator(nbins=9))
        ax3.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax3.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax3.grid(True, which='both', alpha=0.25)

        # === Chart 4: 위험도 점수별 수익금 분포(매수시점) ===
        ax4 = fig.add_subplot(gs[1, 0])
        if '위험도점수' in df_tsg.columns:
            risk_bins = [0, 20, 40, 60, 80, 100]
            risk_labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
            df_tsg['위험도구간'] = pd.cut(df_tsg['위험도점수'], bins=risk_bins, labels=risk_labels, right=False)
            df_risk = df_tsg.groupby('위험도구간', observed=True).agg({'수익금': 'sum', '종목명': 'count'}).reset_index()
            df_risk.columns = ['위험도구간', '수익금', '거래횟수']

            x_pos = range(len(df_risk))
            colors = [color_profit if x >= 0 else color_loss for x in df_risk['수익금']]
            bars = ax4.bar(x_pos, df_risk['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax4.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax4.set_xticks(x_pos)
            ax4.set_xticklabels(df_risk['위험도구간'], rotation=45, ha='right', fontsize=9)
            ax4.set_xlabel('매수 위험도 점수 구간')
            ax4.set_ylabel('총 수익금')
            ax4.set_title('매수 위험도 점수별 수익금 분포')
            for bar, cnt in zip(bars, df_risk['거래횟수']):
                ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f'n={int(cnt)}', ha='center',
                         va='bottom' if bar.get_height() >= 0 else 'top', fontsize=8)
        else:
            ax4.text(0.5, 0.5, '위험도점수 컬럼 없음', ha='center', va='center', fontsize=12, transform=ax4.transAxes)
            ax4.axis('off')

        # === Chart 5: 등락추세별 수익금 ===
        ax5 = fig.add_subplot(gs[1, 1])
        if '등락추세' in df_tsg.columns:
            trend_profit = df_tsg.groupby('등락추세')['수익금'].sum()
            trend_count = df_tsg.groupby('등락추세').size()
            colors = [color_profit if trend_profit.get(x, 0) >= 0 else color_loss for x in trend_profit.index]
            bars = ax5.bar(trend_profit.index, trend_profit.values, color=colors, edgecolor='black', linewidth=0.5)
            ax5.set_xlabel('등락 추세')
            ax5.set_ylabel('총 수익금')
            ax5.set_title('등락추세별 수익금')
            ax5.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

            for bar, cnt in zip(bars, trend_count):
                ax5.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=9)

        # === Chart 6: 체결강도추세별 수익금 ===
        ax6 = fig.add_subplot(gs[1, 2])
        if '체결강도추세' in df_tsg.columns:
            ch_trend_profit = df_tsg.groupby('체결강도추세')['수익금'].sum()
            ch_trend_count = df_tsg.groupby('체결강도추세').size()
            colors = [color_profit if ch_trend_profit.get(x, 0) >= 0 else color_loss for x in ch_trend_profit.index]
            bars = ax6.bar(ch_trend_profit.index, ch_trend_profit.values, color=colors, edgecolor='black', linewidth=0.5)
            ax6.set_xlabel('체결강도 추세')
            ax6.set_ylabel('총 수익금')
            ax6.set_title('체결강도추세별 수익금')
            ax6.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

            for bar, cnt in zip(bars, ch_trend_count):
                ax6.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=9)

        # === Chart 7: 추세 조합 히트맵 ===
        ax7 = fig.add_subplot(gs[2, 0])
        if '등락추세' in df_tsg.columns and '체결강도추세' in df_tsg.columns:
            pivot = df_tsg.pivot_table(values='수익금', index='등락추세', columns='체결강도추세',
                                       aggfunc='sum', fill_value=0)
            im = ax7.imshow(pivot.values, cmap='RdYlGn', aspect='auto')
            ax7.set_xticks(range(len(pivot.columns)))
            ax7.set_yticks(range(len(pivot.index)))
            ax7.set_xticklabels(pivot.columns, fontsize=9)
            ax7.set_yticklabels(pivot.index, fontsize=9)
            ax7.set_xlabel('체결강도 추세')
            ax7.set_ylabel('등락 추세')
            ax7.set_title('추세 조합별 수익금')

            vmax = float(np.max(np.abs(pivot.values))) if pivot.size else 0
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    val = pivot.values[i, j]
                    text_color = 'white' if vmax and abs(val) > vmax * 0.5 else 'black'
                    ax7.text(j, i, f'{val/10000:.0f}만', ha='center', va='center', fontsize=8, color=text_color)

            plt.colorbar(im, ax=ax7, shrink=0.8)

        loss_trades = df_tsg[df_tsg['수익금'] < 0]
        profit_trades = df_tsg[df_tsg['수익금'] >= 0]

        # === Chart 8: 손실/이익 거래 특성 비교 (매수/보유) ===
        ax8 = fig.add_subplot(gs[2, 1])
        if len(loss_trades) > 0 and len(profit_trades) > 0:
            compare_specs = []
            if '매수등락율' in df_tsg.columns:
                compare_specs.append(('매수등락율', '매수등락율(%)', 1.0))
            if '매수체결강도' in df_tsg.columns:
                compare_specs.append(('매수체결강도', '매수체결강도', 1.0))
            if '위험도점수' in df_tsg.columns:
                compare_specs.append(('위험도점수', '매수 위험도점수', 1.0))
            if '보유시간' in df_tsg.columns:
                compare_specs.append(('보유시간', '보유시간(분)', 1.0 / 60.0))

            if compare_specs:
                loss_means = [loss_trades[c].mean() * scale for c, _, scale in compare_specs]
                profit_means = [profit_trades[c].mean() * scale for c, _, scale in compare_specs]

                x = np.arange(len(compare_specs))
                width = 0.35
                ax8.bar(x - width/2, loss_means, width, label='손실거래', color=color_loss, alpha=0.8)
                ax8.bar(x + width/2, profit_means, width, label='이익거래', color=color_profit, alpha=0.8)
                ax8.set_xticks(x)
                ax8.set_xticklabels([label for _, label, _ in compare_specs], rotation=45, ha='right', fontsize=9)
                ax8.set_ylabel('평균값')
                ax8.set_title('손실/이익 거래 특성 비교 (매수/보유)')
                ax8.legend(fontsize=9)

        # === Chart 9: 손실/이익 거래 변화량 비교 (매도-매수) ===
        ax9 = fig.add_subplot(gs[2, 2])
        if len(loss_trades) > 0 and len(profit_trades) > 0:
            compare_cols = ['등락율변화', '체결강도변화', '거래대금변화율', '호가잔량비변화', '매수매도위험도점수']
            available_cols = [c for c in compare_cols if c in df_tsg.columns]
            if available_cols:
                loss_means = [loss_trades[c].mean() for c in available_cols]
                profit_means = [profit_trades[c].mean() for c in available_cols]

                x = np.arange(len(available_cols))
                width = 0.35
                ax9.bar(x - width/2, loss_means, width, label='손실거래', color=color_loss, alpha=0.8)
                ax9.bar(x + width/2, profit_means, width, label='이익거래', color=color_profit, alpha=0.8)
                ax9.set_xticks(x)
                ax9.set_xticklabels(available_cols, rotation=45, ha='right', fontsize=9)
                ax9.set_ylabel('평균값')
                ax9.set_title('손실/이익 거래 변화량 비교 (매도-매수)')
                ax9.legend(fontsize=9)

        # === Chart 10: 3D 히트맵(매수시간×시가총액 → 평균 수익률) ===
        ax10 = fig.add_subplot(gs[3, :])
        try:
            required_heat_cols = {'시가총액', '수익률'}
            has_time_cols = {'매수시', '매수분'}.issubset(df_tsg.columns)
            if required_heat_cols.issubset(df_tsg.columns) and has_time_cols:
                from matplotlib.colors import TwoSlopeNorm

                df_heat = df_tsg[['매수시', '매수분', '시가총액', '수익률']].copy()
                if '매수초' in df_tsg.columns:
                    df_heat['매수초'] = df_tsg['매수초']
                else:
                    df_heat['매수초'] = 0

                hour = pd.to_numeric(df_heat['매수시'], errors='coerce').fillna(0).astype(int)
                minute = pd.to_numeric(df_heat['매수분'], errors='coerce').fillna(0).astype(int)
                second = pd.to_numeric(df_heat['매수초'], errors='coerce').fillna(0).astype(int)
                minute_of_day = (hour * 60 + minute + (second / 60.0)).astype(float)

                min_val = float(np.nanmin(minute_of_day.to_numpy(dtype=np.float64)))
                max_val = float(np.nanmax(minute_of_day.to_numpy(dtype=np.float64)))
                span = max_val - min_val

                desired_bins = 18
                raw_step = max(1, int(np.ceil(span / max(desired_bins, 1)))) if span > 0 else 5
                step_candidates = [1, 2, 5, 10, 15, 30, 60]
                step = next((c for c in step_candidates if c >= raw_step), step_candidates[-1])
                start = float(np.floor(min_val / step) * step)
                end = float(np.ceil(max_val / step) * step)
                if end <= start:
                    end = start + step
                bins = np.arange(start, end + step, step, dtype=float)
                if len(bins) < 3:
                    bins = np.array([start, start + step, start + 2 * step], dtype=float)

                time_labels = [f"{int(t // 60):02d}:{int(t % 60):02d}" for t in bins[:-1]]
                df_heat['매수시간구간'] = pd.cut(minute_of_day, bins=bins, labels=time_labels, right=False, include_lowest=True)

                mcap = pd.to_numeric(df_heat['시가총액'], errors='coerce')
                mcap_bins = [0, 500, 1000, 2000, 3000, 5000, 10000, 20000, 50000, np.inf]
                mcap_labels = ['~500억', '500-1000억', '1000-2000억', '2000-3000억', '3000-5000억',
                               '0.5-1조', '1-2조', '2-5조', '5조+']
                df_heat['시총구간_3D'] = pd.cut(mcap, bins=mcap_bins, labels=mcap_labels, right=False, include_lowest=True)

                df_heat = df_heat.dropna(subset=['매수시간구간', '시총구간_3D'])
                if len(df_heat) >= 10:
                    pivot = df_heat.pivot_table(values='수익률', index='시총구간_3D', columns='매수시간구간',
                                                aggfunc='mean', observed=True)
                    pivot_count = df_heat.pivot_table(values='수익률', index='시총구간_3D', columns='매수시간구간',
                                                      aggfunc='size', fill_value=0, observed=True)

                    pivot = pivot.reindex(index=mcap_labels, columns=time_labels).dropna(axis=0, how='all').dropna(axis=1, how='all')
                    pivot_count = pivot_count.reindex(index=pivot.index, columns=pivot.columns)

                    if pivot.size > 0:
                        data = pivot.to_numpy(dtype=np.float64)
                        data_masked = np.ma.masked_invalid(data)

                        abs_max = float(np.nanpercentile(np.abs(data), 95)) if np.isfinite(data).any() else 1.0
                        abs_max = max(abs_max, 0.5)
                        norm = TwoSlopeNorm(vcenter=0.0, vmin=-abs_max, vmax=abs_max)

                        cmap = plt.get_cmap('RdYlGn').copy()
                        cmap.set_bad(color='#F2F2F2')

                        im = ax10.imshow(data_masked, cmap=cmap, norm=norm, aspect='auto', interpolation='nearest')
                        ax10.set_title('3D 히트맵: 매수시간×시가총액 → 평균 수익률(%)')
                        ax10.set_xlabel('매수시간(시:분, 구간)')
                        ax10.set_ylabel('시가총액 구간')

                        xcnt = len(pivot.columns)
                        ycnt = len(pivot.index)
                        x_step = max(1, int(np.ceil(xcnt / 20)))
                        ax10.set_xticks(np.arange(0, xcnt, x_step))
                        ax10.set_xticklabels([pivot.columns[i] for i in range(0, xcnt, x_step)],
                                             rotation=45, ha='right', fontsize=8)
                        ax10.set_yticks(np.arange(ycnt))
                        ax10.set_yticklabels(pivot.index, fontsize=9)
                        ax10.grid(False)

                        cbar = plt.colorbar(im, ax=ax10, shrink=0.9, pad=0.02)
                        cbar.set_label('평균 수익률(%)', fontsize=9)

                        if ycnt <= 9 and xcnt <= 18:
                            for yi in range(ycnt):
                                for xi in range(xcnt):
                                    v = data[yi, xi]
                                    n_raw = pivot_count.iat[yi, xi] if pivot_count is not None else 0
                                    try:
                                        n = int(n_raw) if np.isfinite(n_raw) else 0
                                    except Exception:
                                        n = 0
                                    if not np.isfinite(v) or n <= 0:
                                        continue
                                    txt_color = 'white' if abs(v) > abs_max * 0.5 else 'black'
                                    ax10.text(xi, yi, f"{v:.1f}\n(n={n})", ha='center', va='center', fontsize=7, color=txt_color)
                    else:
                        ax10.text(0.5, 0.5, '3D 히트맵 데이터 부족', ha='center', va='center', fontsize=12, transform=ax10.transAxes)
                        ax10.axis('off')
                else:
                    ax10.text(0.5, 0.5, '3D 히트맵 데이터 부족', ha='center', va='center', fontsize=12, transform=ax10.transAxes)
                    ax10.axis('off')
            else:
                ax10.text(0.5, 0.5, '3D 히트맵 생성 불가(시가총액/매수시간 컬럼 부족)', ha='center', va='center', fontsize=11, transform=ax10.transAxes)
                ax10.axis('off')
        except Exception:
            ax10.text(0.5, 0.5, '3D 히트맵 생성 중 오류', ha='center', va='center', fontsize=11, transform=ax10.transAxes)
            ax10.axis('off')

        # === Chart 11: 보유시간 vs 수익률 (분 단위) ===
        ax11 = fig.add_subplot(gs[4, :])
        if '보유시간' in df_tsg.columns:
            plot_df = df_scatter if '보유시간' in df_scatter.columns else df_tsg
            colors = np.where(plot_df['수익률'].to_numpy(dtype=np.float64) >= 0, color_profit, color_loss)
            hold_minutes = plot_df['보유시간'] / 60.0
            ax11.scatter(hold_minutes, plot_df['수익률'], c=colors, alpha=0.5, s=25, edgecolors='none')
            ax11.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax11.set_xlabel('보유시간(분)')
            ax11.set_ylabel('수익률(%)')
            ax11.set_title('보유시간 vs 수익률')
            ax11.xaxis.set_major_locator(MaxNLocator(nbins=12))
            ax11.xaxis.set_minor_locator(AutoMinorLocator(2))
            ax11.yaxis.set_major_locator(MaxNLocator(nbins=10))
            ax11.yaxis.set_minor_locator(AutoMinorLocator(2))
            ax11.grid(True, which='both', alpha=0.25)

        # 저장 및 전송
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.tight_layout(rect=[0, 0.02, 1, 0.97])

        output_dir = ensure_backtesting_output_dir(save_file_name)
        comparison_path = str(output_dir / f"{save_file_name}_comparison.png")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.savefig(comparison_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if teleQ is not None:
            teleQ.put(comparison_path)

    except Exception as e:
        print_exc()
        try:
            plt.close('all')
        except:
            pass
