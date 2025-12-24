# -*- coding: utf-8 -*-
"""
Threshold Optimizer (Optuna)

세그먼트별 임계값 최적화를 수행합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

try:
    import optuna
except Exception:  # pragma: no cover - optional dependency
    optuna = None


@dataclass
class ThresholdOptimizerConfig:
    n_trials: int = 50
    min_trades_per_segment: int = 30
    min_remaining_ratio: float = 0.15
    quantile_low: float = 0.05
    quantile_high: float = 0.95
    seed: int = 42


def optimize_thresholds(
    segment_df: pd.DataFrame,
    filter_columns: List[str],
    config: Optional[ThresholdOptimizerConfig] = None,
) -> Optional[dict]:
    if optuna is None:
        return None

    if segment_df.empty or '수익금' not in segment_df.columns:
        return None

    config = config or ThresholdOptimizerConfig()
    total_profit = pd.to_numeric(segment_df['수익금'], errors='coerce').fillna(0).sum()
    total_trades = len(segment_df)

    if total_trades < config.min_trades_per_segment:
        return None

    valid_columns = [c for c in filter_columns if c in segment_df.columns]
    if not valid_columns:
        return None

    quantile_bounds = {}
    for col in valid_columns:
        series = pd.to_numeric(segment_df[col], errors='coerce').dropna()
        if series.empty:
            continue
        low = series.quantile(config.quantile_low)
        high = series.quantile(config.quantile_high)
        if low == high:
            continue
        quantile_bounds[col] = (float(low), float(high))

    if not quantile_bounds:
        return None

    def objective(trial):
        mask = pd.Series([True] * len(segment_df), index=segment_df.index)
        for col, (low, high) in quantile_bounds.items():
            threshold = trial.suggest_float(f'{col}_threshold', low, high)
            direction = trial.suggest_categorical(f'{col}_direction', ['less', 'greater'])
            use_filter = trial.suggest_categorical(f'{col}_use', [True, False])

            if not use_filter:
                continue

            values = pd.to_numeric(segment_df[col], errors='coerce')
            if direction == 'less':
                mask &= values >= threshold
            else:
                mask &= values < threshold

        remaining = segment_df[mask]
        remaining_trades = len(remaining)
        if remaining_trades < config.min_trades_per_segment:
            return float('-inf')

        remaining_ratio = remaining_trades / max(1, total_trades)
        if remaining_ratio < config.min_remaining_ratio:
            return float('-inf')

        remaining_profit = pd.to_numeric(remaining['수익금'], errors='coerce').fillna(0).sum()
        improvement = remaining_profit - total_profit
        return float(improvement)

    study = optuna.create_study(
        direction='maximize',
        sampler=optuna.samplers.TPESampler(seed=config.seed),
        pruner=optuna.pruners.MedianPruner(),
    )
    study.optimize(objective, n_trials=config.n_trials, n_jobs=1)

    best_params = study.best_params if study.best_trial else {}
    best_value = study.best_value if study.best_trial else None

    return {
        'best_value': best_value,
        'best_params': best_params,
        'n_trials': config.n_trials,
    }
