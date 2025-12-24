# -*- coding: utf-8 -*-
"""
Multi-Objective Optimizer (Pareto)

전역 조합 후보에 대해 다목적 지표를 계산하고 Pareto front를 산출합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .risk_metrics import summarize_risk


@dataclass
class MultiObjectiveConfig:
    min_remaining_ratio: float = 0.15
    max_candidates: int = 50


def evaluate_candidates(
    segments: Dict[str, pd.DataFrame],
    candidates: List[dict],
    total_trades: int,
    config: Optional[MultiObjectiveConfig] = None,
) -> pd.DataFrame:
    config = config or MultiObjectiveConfig()
    rows: List[dict] = []

    for idx, state in enumerate(candidates[:config.max_candidates], start=1):
        combo_map = state.get('combination') or {}
        excluded_trades = int(state.get('excluded_trades', 0) or 0)
        remaining_trades = max(0, total_trades - excluded_trades)
        remaining_ratio = remaining_trades / max(1, total_trades)
        if remaining_ratio < config.min_remaining_ratio:
            continue

        filtered_df = _apply_global_combination(segments, combo_map)
        risk = summarize_risk(filtered_df)

        rows.append({
            'combo_id': idx,
            'segments': ",".join(sorted(combo_map.keys())),
            'filters': _format_global_filters(combo_map),
            'total_improvement': float(state.get('score', 0) or 0),
            'remaining_trades': remaining_trades,
            'remaining_ratio': remaining_ratio,
            'mdd_won': risk.get('mdd_won'),
            'mdd_pct': risk.get('mdd_pct'),
            'profit_volatility': risk.get('profit_volatility'),
            'return_volatility': risk.get('return_volatility'),
            'segment_count': len(combo_map),
            'filter_count': _count_filters(combo_map),
        })

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def build_pareto_front(candidates_df: pd.DataFrame) -> pd.DataFrame:
    if candidates_df is None or candidates_df.empty:
        return pd.DataFrame()

    records = candidates_df.to_dict(orient='records')
    keep = []
    for i, a in enumerate(records):
        dominated = False
        for j, b in enumerate(records):
            if i == j:
                continue
            if _dominates(b, a):
                dominated = True
                break
        if not dominated:
            keep.append(a)

    if not keep:
        return pd.DataFrame()
    df = pd.DataFrame(keep)
    df = df.sort_values(['total_improvement', 'remaining_ratio'], ascending=[False, False])
    return df.reset_index(drop=True)


def _dominates(a: dict, b: dict) -> bool:
    a_profit = _safe_max(a.get('total_improvement'))
    b_profit = _safe_max(b.get('total_improvement'))
    a_remain = _safe_max(a.get('remaining_ratio'))
    b_remain = _safe_max(b.get('remaining_ratio'))
    a_mdd = _safe_min(a.get('mdd_pct'))
    b_mdd = _safe_min(b.get('mdd_pct'))
    a_vol = _safe_min(a.get('profit_volatility'))
    b_vol = _safe_min(b.get('profit_volatility'))

    better_or_equal = (
        a_profit >= b_profit and
        a_remain >= b_remain and
        a_mdd <= b_mdd and
        a_vol <= b_vol
    )
    strictly_better = (
        a_profit > b_profit or
        a_remain > b_remain or
        a_mdd < b_mdd or
        a_vol < b_vol
    )
    return better_or_equal and strictly_better


def _apply_global_combination(segments: Dict[str, pd.DataFrame],
                              combo_map: Dict[str, dict]) -> pd.DataFrame:
    if not segments or not combo_map:
        return pd.DataFrame()

    filtered_parts = []
    for seg_id, seg_df in segments.items():
        combo = combo_map.get(seg_id)
        if combo is None or seg_df is None or seg_df.empty:
            continue
        if combo.get('exclude_segment'):
            continue
        filters = combo.get('filters') or []
        seg_filtered = _apply_filters(seg_df, filters)
        if not seg_filtered.empty:
            filtered_parts.append(seg_filtered)

    if not filtered_parts:
        return pd.DataFrame()

    filtered_df = pd.concat(filtered_parts, axis=0)
    return _sort_detail_df(filtered_df)


def _apply_filters(seg_df: pd.DataFrame, filters: list) -> pd.DataFrame:
    if not filters:
        return seg_df.copy()
    mask = pd.Series(True, index=seg_df.index)
    for flt in filters:
        column = flt.get('column')
        threshold = flt.get('threshold')
        direction = flt.get('direction')
        if column is None or column not in seg_df.columns:
            continue
        values = pd.to_numeric(seg_df[column], errors='coerce')
        if direction == 'less':
            cond = values >= threshold
        else:
            cond = values < threshold
        mask &= cond.fillna(False)
    return seg_df.loc[mask].copy()


def _sort_detail_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if '매수시간' in df.columns:
        return df.sort_values('매수시간')
    if all(c in df.columns for c in ('매수일자', '매수시', '매수분', '매수초')):
        try:
            sort_key = (
                pd.to_numeric(df['매수일자'], errors='coerce').fillna(0).astype(int) * 1000000 +
                pd.to_numeric(df['매수시'], errors='coerce').fillna(0).astype(int) * 10000 +
                pd.to_numeric(df['매수분'], errors='coerce').fillna(0).astype(int) * 100 +
                pd.to_numeric(df['매수초'], errors='coerce').fillna(0).astype(int)
            )
            return df.assign(_sort_key=sort_key).sort_values('_sort_key').drop(columns=['_sort_key'])
        except Exception:
            return df
    return df


def _format_global_filters(combo_map: Dict[str, dict]) -> str:
    parts = []
    for seg_id, combo in combo_map.items():
        if combo.get('exclude_segment'):
            parts.append(f"{seg_id}: (segment_excluded)")
            continue
        names = []
        for flt in combo.get('filters', []):
            name = flt.get('filter_name') or ''
            if name:
                names.append(name)
        label = " | ".join(names) if names else "(no_filter)"
        parts.append(f"{seg_id}: {label}")
    return " / ".join(parts)


def _count_filters(combo_map: Dict[str, dict]) -> int:
    total = 0
    for combo in combo_map.values():
        total += len(combo.get('filters') or [])
    return total


def _safe_max(value: Optional[float]) -> float:
    try:
        v = float(value)
        if np.isnan(v):
            return float('-inf')
        return v
    except Exception:
        return float('-inf')


def _safe_min(value: Optional[float]) -> float:
    try:
        v = float(value)
        if np.isnan(v):
            return float('inf')
        return v
    except Exception:
        return float('inf')
