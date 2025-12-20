# -*- coding: utf-8 -*-
"""
Segment Mode Comparator

고정/반-동적/동적 분할 모드별 성능을 비교하는 리포트를 생성합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from .segmentation import SegmentConfig
from .filter_evaluator import FilterEvaluatorConfig
from .combination_optimizer import CombinationOptimizerConfig
from .phase2_runner import run_phase2, Phase2RunnerConfig
from .segment_outputs import save_segment_mode_comparison


@dataclass
class SegmentModeComparisonConfig:
    output_dir: str = 'backtester/segment_outputs'
    prefix: Optional[str] = None
    modes: Iterable[str] = ('fixed', 'semi', 'dynamic', 'time_only')
    enable_optuna: bool = False


def run_segment_mode_comparison(
    detail_path: str,
    seg_config: Optional[SegmentConfig] = None,
    filter_config: Optional[FilterEvaluatorConfig] = None,
    combo_config: Optional[CombinationOptimizerConfig] = None,
    runner_config: Optional[SegmentModeComparisonConfig] = None,
) -> dict:
    runner_config = runner_config or SegmentModeComparisonConfig()
    detail_path = Path(detail_path).expanduser().resolve()

    output_prefix = runner_config.prefix or _build_prefix(detail_path.name)
    rows = []
    mode_results = {}

    for mode in runner_config.modes:
        mode_name = str(mode)
        cfg = _clone_segment_config(seg_config)
        cfg.dynamic_mode = mode_name

        phase2_result = run_phase2(
            str(detail_path),
            seg_config=cfg,
            filter_config=filter_config,
            combo_config=combo_config,
            runner_config=Phase2RunnerConfig(
                output_dir=runner_config.output_dir,
                prefix=f"{output_prefix}_{mode_name}",
                enable_optuna=runner_config.enable_optuna,
            ),
        )

        mode_results[mode_name] = phase2_result
        row = _build_row(mode_name, phase2_result)
        rows.append(row)

    df_comp = pd.DataFrame(rows)
    comparison_path = save_segment_mode_comparison(
        df_comp, runner_config.output_dir, output_prefix
    )

    return {
        'comparison_path': comparison_path,
        'mode_results': mode_results,
        'rows': len(df_comp),
    }


def _build_prefix(filename: str) -> str:
    if filename.endswith('_detail.csv'):
        return filename.replace('_detail.csv', '')
    return filename.replace('.csv', '')


def _clone_segment_config(seg_config: Optional[SegmentConfig]) -> SegmentConfig:
    base = seg_config or SegmentConfig()
    return SegmentConfig(
        market_cap_ranges=dict(base.market_cap_ranges),
        time_ranges=dict(base.time_ranges),
        min_trades=dict(base.min_trades),
        max_exclusion=dict(base.max_exclusion),
        validation=dict(base.validation),
        dynamic_mode=base.dynamic_mode,
        dynamic_market_cap_quantiles=tuple(base.dynamic_market_cap_quantiles),
        dynamic_time_quantiles=tuple(base.dynamic_time_quantiles),
        dynamic_min_samples=base.dynamic_min_samples,
    )


def _build_row(mode: str, result: dict) -> dict:
    row = {
        'mode': mode,
        'summary_path': result.get('summary_path'),
        'ranges_path': result.get('ranges_path'),
        'global_combo_path': result.get('global_combo_path'),
        'local_combo_path': result.get('local_combo_path'),
        'filters_path': result.get('filters_path'),
    }

    combo_path = result.get('global_combo_path')
    if combo_path and Path(combo_path).exists():
        try:
            df_combo = pd.read_csv(combo_path, encoding='utf-8-sig')
            if not df_combo.empty:
                combo = df_combo.iloc[0]
                row.update({
                    'total_improvement': combo.get('total_improvement'),
                    'remaining_trades': combo.get('remaining_trades'),
                    'remaining_ratio': combo.get('remaining_ratio'),
                    'mdd_won': combo.get('mdd_won'),
                    'mdd_pct': combo.get('mdd_pct'),
                    'profit_volatility': combo.get('profit_volatility'),
                    'return_volatility': combo.get('return_volatility'),
                })
        except Exception:
            pass

    return row


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m backtester.segment_analysis.segment_mode_comparator <detail.csv>")

    result = run_segment_mode_comparison(sys.argv[1])
    print(f"[ModeCompare] CSV: {result['comparison_path']}")
