# -*- coding: utf-8 -*-
"""
Segment Output Helpers

세그먼트 요약/필터 결과를 CSV로 저장합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from backtester.output_paths import build_backtesting_output_path
from backtester.analysis_enhanced.utils import round_dataframe_floats, DEFAULT_DECIMAL_PLACES

def resolve_segment_output_dir(detail_path: Path, output_dir: Optional[str]) -> str:
    if output_dir:
        return str(output_dir)
    try:
        return str(Path(detail_path).expanduser().resolve().parent)
    except Exception:
        return 'backtester/segment_outputs'


def build_segment_summary(
    segments: Dict[str, pd.DataFrame],
    out_of_range: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    rows = []
    for seg_id, df in segments.items():
        rows.append(_summarize_segment(seg_id, df))

    if out_of_range is not None and not out_of_range.empty:
        rows.append(_summarize_segment('Out_of_Range', out_of_range))

    return pd.DataFrame(rows)


def save_segment_summary(df_summary: pd.DataFrame, output_dir: str, prefix: str) -> str:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    summary_path = build_backtesting_output_path(prefix, "_segment_summary.csv", output_dir=path)
    # [2026-01-07] 소수점 4자리 제한 적용
    df_rounded = round_dataframe_floats(df_summary, decimals=DEFAULT_DECIMAL_PLACES)
    df_rounded.to_csv(summary_path, index=False, encoding='utf-8-sig')
    return str(summary_path)


def save_segment_filters(df_filters: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_filters is None or df_filters.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    filter_path = build_backtesting_output_path(prefix, "_segment_filters.csv", output_dir=path)
    # [2026-01-07] 소수점 4자리 제한 적용
    df_rounded = round_dataframe_floats(df_filters, decimals=DEFAULT_DECIMAL_PLACES)
    df_rounded.to_csv(filter_path, index=False, encoding='utf-8-sig')
    return str(filter_path)


def build_local_combos_df(segment_combos: Dict[str, List[dict]]) -> pd.DataFrame:
    rows = []
    for seg_id, combos in segment_combos.items():
        for rank, combo in enumerate(combos, start=1):
            if combo.get('exclude_segment'):
                filters_text = '세그먼트 전체 제외'
            else:
                filters_text = _format_filters(combo.get('filters', []))
            rows.append({
                'segment_id': seg_id,
                'combo_rank': rank,
                'filters': filters_text,
                'improvement': combo.get('improvement', 0),
                'remaining_trades': combo.get('remaining_trades', 0),
                'exclusion_ratio': combo.get('exclusion_ratio', 0),
            })
    return pd.DataFrame(rows)


def save_segment_local_combos(df_local: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_local is None or df_local.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    combo_path = build_backtesting_output_path(prefix, "_segment_local_combos.csv", output_dir=path)
    # [2026-01-07] 소수점 4자리 제한 적용
    df_rounded = round_dataframe_floats(df_local, decimals=DEFAULT_DECIMAL_PLACES)
    df_rounded.to_csv(combo_path, index=False, encoding='utf-8-sig')
    return str(combo_path)


def build_global_combo_df(global_best: Optional[dict], total_trades: int,
                          risk_metrics: Optional[Dict[str, float]] = None) -> pd.DataFrame:
    if not global_best:
        return pd.DataFrame()
    remaining_trades = total_trades - int(global_best.get('excluded_trades', 0))
    remaining_ratio = remaining_trades / max(1, total_trades)
    score = float(global_best.get('score', 0))
    validation_score = score / max(1.0, (1.0 - remaining_ratio) * 100.0)

    filters = _format_global_filters(global_best.get('combination', {}))

    row = {
        'combo_id': 1,
        'segments': ",".join(sorted(global_best.get('combination', {}).keys())),
        'filters': filters,
        'total_improvement': score,
        'remaining_trades': remaining_trades,
        'remaining_ratio': remaining_ratio,
        'validation_score': validation_score,
    }

    if isinstance(risk_metrics, dict):
        row.update({
            'mdd_won': risk_metrics.get('mdd_won'),
            'mdd_pct': risk_metrics.get('mdd_pct'),
            'profit_volatility': risk_metrics.get('profit_volatility'),
            'return_volatility': risk_metrics.get('return_volatility'),
        })

    return pd.DataFrame([row])


def save_segment_combos(df_combos: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_combos is None or df_combos.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    combo_path = build_backtesting_output_path(prefix, "_segment_combos.csv", output_dir=path)
    # [2026-01-07] 소수점 4자리 제한 적용
    df_rounded = round_dataframe_floats(df_combos, decimals=DEFAULT_DECIMAL_PLACES)
    df_rounded.to_csv(combo_path, index=False, encoding='utf-8-sig')
    return str(combo_path)


def save_segment_thresholds(df_thresholds: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_thresholds is None or df_thresholds.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    threshold_path = build_backtesting_output_path(prefix, "_segment_thresholds.csv", output_dir=path)
    df_thresholds.to_csv(threshold_path, index=False, encoding='utf-8-sig')
    return str(threshold_path)


def save_segment_validation(df_validation: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_validation is None or df_validation.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    validation_path = build_backtesting_output_path(prefix, "_segment_validation.csv", output_dir=path)
    df_validation.to_csv(validation_path, index=False, encoding='utf-8-sig')
    return str(validation_path)


def save_segment_ranges(df_ranges: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_ranges is None or df_ranges.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    range_path = build_backtesting_output_path(prefix, "_segment_ranges.csv", output_dir=path)
    # [2026-01-07] 소수점 4자리 제한 적용
    df_rounded = round_dataframe_floats(df_ranges, decimals=DEFAULT_DECIMAL_PLACES)
    df_rounded.to_csv(range_path, index=False, encoding='utf-8-sig')
    return str(range_path)


def save_pareto_front(df_pareto: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_pareto is None or df_pareto.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    pareto_path = build_backtesting_output_path(prefix, "_pareto_front.csv", output_dir=path)
    df_pareto.to_csv(pareto_path, index=False, encoding='utf-8-sig')
    return str(pareto_path)


def save_segment_mode_comparison(df_comp: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_comp is None or df_comp.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    comp_path = build_backtesting_output_path(prefix, "_segment_mode_comparison.csv", output_dir=path)
    df_comp.to_csv(comp_path, index=False, encoding='utf-8-sig')
    return str(comp_path)


def save_segment_template_comparison(df_comp: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_comp is None or df_comp.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    comp_path = build_backtesting_output_path(prefix, "_segment_template_comparison.csv", output_dir=path)
    df_comp.to_csv(comp_path, index=False, encoding='utf-8-sig')
    return str(comp_path)


def save_advanced_optuna_result(df_result: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_result is None or df_result.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    optuna_path = build_backtesting_output_path(prefix, "_advanced_optuna.csv", output_dir=path)
    df_result.to_csv(optuna_path, index=False, encoding='utf-8-sig')
    return str(optuna_path)


def save_nsga2_front(df_front: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_front is None or df_front.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    nsga2_path = build_backtesting_output_path(prefix, "_nsga2_front.csv", output_dir=path)
    df_front.to_csv(nsga2_path, index=False, encoding='utf-8-sig')
    return str(nsga2_path)


def save_decision_report(df_score: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_score is None or df_score.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    score_path = build_backtesting_output_path(prefix, "_decision_score.csv", output_dir=path)
    df_score.to_csv(score_path, index=False, encoding='utf-8-sig')
    return str(score_path)


def _summarize_segment(segment_id: str, df: pd.DataFrame) -> dict:
    trades = len(df)
    profit = _sum_safe(df, '수익금')
    winrate = _winrate_safe(df)
    avg_return = _mean_safe(df, '수익률')
    std_return = _std_safe(df, '수익률')
    sharpe = avg_return / std_return if std_return and std_return > 0 else np.nan

    return {
        'segment_id': segment_id,
        'trades': trades,
        'profit': profit,
        'winrate': winrate,
        'avg_return': avg_return,
        'std_return': std_return,
        'sharpe': sharpe,
    }


def _sum_safe(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns:
        return 0.0
    return float(pd.to_numeric(df[column], errors='coerce').fillna(0).sum())


def _mean_safe(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns:
        return np.nan
    series = pd.to_numeric(df[column], errors='coerce')
    return float(series.mean()) if series.notna().any() else np.nan


def _std_safe(df: pd.DataFrame, column: str) -> float:
    if column not in df.columns:
        return np.nan
    series = pd.to_numeric(df[column], errors='coerce')
    return float(series.std()) if series.notna().any() else np.nan


def _winrate_safe(df: pd.DataFrame) -> float:
    if '수익금' not in df.columns:
        return np.nan
    profit = pd.to_numeric(df['수익금'], errors='coerce')
    if profit.notna().sum() == 0:
        return np.nan
    return float((profit > 0).mean() * 100.0)


def _format_filters(filters: List[dict]) -> str:
    names = []
    for item in filters:
        name = item.get('filter_name') or ''
        if name:
            names.append(name)
    return " | ".join(names)


def _format_global_filters(combo_map: Dict[str, dict]) -> str:
    parts = []
    for seg_id, combo in combo_map.items():
        if combo.get('exclude_segment'):
            parts.append(f"{seg_id}: (segment_excluded)")
            continue
        names = _format_filters(combo.get('filters', []))
        parts.append(f"{seg_id}: {names}" if names else f"{seg_id}: (no_filter)")
    return " / ".join(parts)
