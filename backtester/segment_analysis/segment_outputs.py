# -*- coding: utf-8 -*-
"""
Segment Output Helpers

세그먼트 요약/필터 결과를 CSV로 저장합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd


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
    summary_path = path / f"{prefix}_segment_summary.csv"
    df_summary.to_csv(summary_path, index=False, encoding='utf-8-sig')
    return str(summary_path)


def save_segment_filters(df_filters: pd.DataFrame, output_dir: str, prefix: str) -> Optional[str]:
    if df_filters is None or df_filters.empty:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    filter_path = path / f"{prefix}_segment_filters.csv"
    df_filters.to_csv(filter_path, index=False, encoding='utf-8-sig')
    return str(filter_path)


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
