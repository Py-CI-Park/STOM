# -*- coding: utf-8 -*-
"""
Combination Optimizer

세그먼트별 필터 후보를 조합하고, 전역 최적 조합을 탐색합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .validation import ConstraintConfig, validate_segment_combo, validate_global_state


@dataclass
class CombinationOptimizerConfig(ConstraintConfig):
    max_filters_per_segment: int = 2
    max_candidates_per_segment: int = 20
    beam_width: int = 20


def generate_local_combinations(
    segment_df: pd.DataFrame,
    candidates: List[dict],
    config: Optional[CombinationOptimizerConfig] = None,
) -> List[dict]:
    config = config or CombinationOptimizerConfig()
    if segment_df.empty or '수익금' not in segment_df.columns:
        return []

    total_trades = len(segment_df)
    total_profit = pd.to_numeric(segment_df['수익금'], errors='coerce').fillna(0).sum()

    local_candidates = candidates[:config.max_candidates_per_segment]
    masks = [apply_filter_mask(segment_df, c) for c in local_candidates]

    combos: List[dict] = [{
        'filters': [],
        'improvement': 0.0,
        'excluded_trades': 0,
        'remaining_trades': total_trades,
        'exclusion_ratio': 0.0,
        'label': 'no_filter',
    }]

    for r in range(1, config.max_filters_per_segment + 1):
        for idxs in combinations(range(len(local_candidates)), r):
            mask = np.ones(total_trades, dtype=bool)
            for idx in idxs:
                mask &= masks[idx]

            remaining_trades = int(mask.sum())
            excluded_trades = total_trades - remaining_trades
            exclusion_ratio = excluded_trades / max(1, total_trades)
            if not validate_segment_combo(remaining_trades, exclusion_ratio, config):
                continue

            remaining_profit = pd.to_numeric(segment_df.loc[mask, '수익금'],
                                             errors='coerce').fillna(0).sum()
            improvement = remaining_profit - total_profit
            if improvement <= 0:
                continue

            combo_filters = [_compact_filter(local_candidates[i]) for i in idxs]
            combos.append({
                'filters': combo_filters,
                'improvement': float(improvement),
                'excluded_trades': excluded_trades,
                'remaining_trades': remaining_trades,
                'exclusion_ratio': exclusion_ratio,
            })

    combos.sort(key=lambda x: x['improvement'], reverse=True)
    return combos[:config.beam_width]


def optimize_global_combination(
    segment_combos: Dict[str, List[dict]],
    total_trades: int,
    config: Optional[CombinationOptimizerConfig] = None,
) -> Optional[dict]:
    config = config or CombinationOptimizerConfig()
    beam = [{
        'combination': {},
        'score': 0.0,
        'excluded_trades': 0,
    }]

    for seg_id in sorted(segment_combos.keys()):
        new_beam: List[dict] = []
        for state in beam:
            for combo in segment_combos[seg_id]:
                new_excluded = state['excluded_trades'] + combo['excluded_trades']
                if not validate_global_state(new_excluded, total_trades, config):
                    continue

                new_state = {
                    'combination': {**state['combination'], seg_id: combo},
                    'score': state['score'] + combo['improvement'],
                    'excluded_trades': new_excluded,
                }
                new_beam.append(new_state)

        new_beam.sort(key=lambda x: x['score'], reverse=True)
        beam = new_beam[:config.beam_width]

    return beam[0] if beam else None


def apply_filter_mask(df: pd.DataFrame, candidate: dict) -> np.ndarray:
    column = candidate.get('column')
    threshold = candidate.get('threshold')
    direction = candidate.get('direction')

    if column is None or column not in df.columns:
        return np.ones(len(df), dtype=bool)

    values = pd.to_numeric(df[column], errors='coerce')
    if direction == 'less':
        return (values >= threshold).to_numpy(dtype=bool)
    return (values < threshold).to_numpy(dtype=bool)


def _compact_filter(candidate: dict) -> dict:
    return {
        'column': candidate.get('column'),
        'threshold': candidate.get('threshold'),
        'direction': candidate.get('direction'),
        'filter_name': candidate.get('filter_name'),
    }
