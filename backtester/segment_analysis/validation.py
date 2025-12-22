# -*- coding: utf-8 -*-
"""
Constraint Validation Helpers

세그먼트/전역 제약 조건을 검증합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class ConstraintConfig:
    min_trades_per_segment: int = 30
    max_exclusion_per_segment: float = 0.85
    max_exclusion_global: float = 0.90
    min_total_trades: Optional[int] = None


def validate_segment_combo(remaining_trades: int, exclusion_ratio: float, config: ConstraintConfig) -> bool:
    if remaining_trades < config.min_trades_per_segment:
        return False
    if exclusion_ratio > config.max_exclusion_per_segment:
        return False
    return True


@dataclass
class StabilityValidationConfig:
    min_splits: int = 3
    min_trades_per_split: int = 30
    date_column: Optional[str] = None


def validate_filter_stability(
    segments: Dict[str, pd.DataFrame],
    candidates_by_segment: Dict[str, List[dict]],
    config: Optional[StabilityValidationConfig] = None,
) -> pd.DataFrame:
    config = config or StabilityValidationConfig()
    rows = []

    for seg_id, seg_df in segments.items():
        candidates = candidates_by_segment.get(seg_id, [])
        if not candidates:
            continue

        top = candidates[0]
        date_series = _get_date_series(seg_df, config.date_column)
        if date_series.empty:
            continue

        splits = _build_walk_forward_splits(date_series, config.min_splits)
        for idx, (train_mask, test_mask) in enumerate(splits, start=1):
            train_df = seg_df[train_mask]
            test_df = seg_df[test_mask]

            if len(train_df) < config.min_trades_per_split or len(test_df) < config.min_trades_per_split:
                continue

            in_perf = _calc_filter_improvement(train_df, top)
            out_perf = _calc_filter_improvement(test_df, top)
            stability_ratio = _safe_ratio(out_perf, in_perf)
            overfit_risk = max(0.0, 1.0 - max(0.0, stability_ratio))

            rows.append({
                'period': f'WF{idx}',
                'segment_id': seg_id,
                'in_sample_perf': in_perf,
                'out_sample_perf': out_perf,
                'stability_ratio': stability_ratio,
                'overfitting_risk': overfit_risk,
            })

    return pd.DataFrame(rows)


def _get_date_series(df: pd.DataFrame, date_column: Optional[str]) -> pd.Series:
    if date_column and date_column in df.columns:
        raw = df[date_column]
    elif '매수일자' in df.columns:
        raw = df['매수일자']
    elif '매수시간' in df.columns:
        raw = df['매수시간']
    else:
        return pd.Series(dtype='datetime64[ns]')

    text = pd.to_numeric(raw, errors='coerce').fillna(0).astype(int).astype(str)
    dates = text.str.slice(0, 8)
    parsed = pd.to_datetime(dates, format='%Y%m%d', errors='coerce')
    return parsed


def _build_walk_forward_splits(date_series: pd.Series, min_splits: int) -> List[Tuple[pd.Series, pd.Series]]:
    valid = date_series.dropna()
    if valid.empty:
        return []

    df = pd.DataFrame({'date': valid})
    df = df.sort_values('date')
    unique_dates = df['date'].dropna().unique()
    if len(unique_dates) < min_splits + 1:
        return []

    split_size = max(1, len(unique_dates) // (min_splits + 1))
    splits = []
    for i in range(min_splits):
        train_end = (i + 1) * split_size
        test_end = min(len(unique_dates), train_end + split_size)
        if test_end <= train_end:
            break

        train_dates = set(unique_dates[:train_end])
        test_dates = set(unique_dates[train_end:test_end])
        train_mask = date_series.isin(train_dates)
        test_mask = date_series.isin(test_dates)
        splits.append((train_mask, test_mask))

    return splits


def _calc_filter_improvement(df: pd.DataFrame, candidate: dict) -> float:
    if df.empty or '수익금' not in df.columns:
        return 0.0

    total_profit = pd.to_numeric(df['수익금'], errors='coerce').fillna(0).sum()
    mask = _apply_filter_mask(df, candidate)
    filtered_profit = pd.to_numeric(df.loc[mask, '수익금'], errors='coerce').fillna(0).sum()
    return float(filtered_profit - total_profit)


def _safe_ratio(out_perf: float, in_perf: float) -> float:
    if in_perf == 0:
        return 0.0
    return float(out_perf / in_perf)


def _apply_filter_mask(df: pd.DataFrame, candidate: dict) -> pd.Series:
    column = candidate.get('column')
    threshold = candidate.get('threshold')
    direction = candidate.get('direction')

    if column is None or column not in df.columns:
        return pd.Series([True] * len(df), index=df.index)

    values = pd.to_numeric(df[column], errors='coerce')
    if direction == 'less':
        return values >= threshold
    return values < threshold


def validate_global_state(excluded_trades: int, total_trades: int, config: ConstraintConfig) -> bool:
    excluded_ratio = excluded_trades / max(1, total_trades)
    if excluded_ratio > config.max_exclusion_global:
        return False
    if config.min_total_trades is not None and (total_trades - excluded_trades) < config.min_total_trades:
        return False
    return True
