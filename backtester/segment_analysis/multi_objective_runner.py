# -*- coding: utf-8 -*-
"""
Multi-Objective Runner

세그먼트 후보 조합에서 Pareto front를 계산합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from backtester.output_manifest import strip_numeric_prefix
from .segmentation import SegmentBuilder, SegmentConfig
from .filter_evaluator import FilterEvaluator, FilterEvaluatorConfig
from .combination_optimizer import (
    CombinationOptimizerConfig,
    generate_local_combinations,
    collect_global_combinations,
)
from .multi_objective import MultiObjectiveConfig, evaluate_candidates, build_pareto_front
from .segment_outputs import resolve_segment_output_dir, save_pareto_front, save_segment_ranges
from .segment_visualizer import plot_pareto_front


@dataclass
class MultiObjectiveRunnerConfig:
    output_dir: Optional[str] = None
    prefix: Optional[str] = None


def run_multi_objective(
    detail_path: str,
    seg_config: Optional[SegmentConfig] = None,
    filter_config: Optional[FilterEvaluatorConfig] = None,
    combo_config: Optional[CombinationOptimizerConfig] = None,
    multi_config: Optional[MultiObjectiveConfig] = None,
    runner_config: Optional[MultiObjectiveRunnerConfig] = None,
) -> dict:
    runner_config = runner_config or MultiObjectiveRunnerConfig()
    detail_path = Path(detail_path).expanduser().resolve()
    df_detail = pd.read_csv(detail_path, encoding='utf-8-sig')
    output_dir = resolve_segment_output_dir(detail_path, runner_config.output_dir)

    builder = SegmentBuilder(seg_config)
    segments = builder.build_segments(df_detail)
    total_trades = sum(len(seg) for seg in segments.values())
    ranges_df = builder.get_range_summary_df()

    evaluator = FilterEvaluator(filter_config)
    filters_df = evaluator.evaluate_all_segments(segments)

    candidates_by_segment = {seg_id: [] for seg_id in segments.keys()}
    if filters_df is not None and not filters_df.empty:
        for row in filters_df.to_dict(orient='records'):
            seg_id = row.get('segment_id')
            if seg_id in candidates_by_segment:
                candidates_by_segment[seg_id].append(row)

    combo_config = combo_config or CombinationOptimizerConfig()
    segment_combos = {}
    for seg_id, seg_df in segments.items():
        candidates = candidates_by_segment.get(seg_id, [])
        segment_combos[seg_id] = generate_local_combinations(seg_df, candidates, combo_config)

    global_candidates = collect_global_combinations(
        segment_combos, total_trades, combo_config
    )

    multi_config = multi_config or MultiObjectiveConfig()
    candidates_df = evaluate_candidates(segments, global_candidates, total_trades, multi_config)
    pareto_df = build_pareto_front(candidates_df)

    output_prefix = runner_config.prefix or _build_prefix(detail_path.name)
    save_segment_ranges(ranges_df, output_dir, output_prefix)
    pareto_path = save_pareto_front(pareto_df, output_dir, output_prefix)
    pareto_plot_path = plot_pareto_front(
        pareto_df, str(Path(output_dir) / f"{output_prefix}_pareto_front.png")
    )

    return {
        'pareto_path': pareto_path,
        'pareto_plot_path': pareto_plot_path,
        'candidate_count': len(candidates_df) if candidates_df is not None else 0,
        'pareto_count': len(pareto_df) if pareto_df is not None else 0,
    }


def _build_prefix(filename: str) -> str:
    filename = strip_numeric_prefix(filename)
    if filename.endswith('_detail.csv'):
        return filename.replace('_detail.csv', '')
    return filename.replace('.csv', '')


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m backtester.segment_analysis.multi_objective_runner <detail.csv>")

    result = run_multi_objective(sys.argv[1])
    print(f"[Multi] Pareto CSV: {result['pareto_path']}")
    print(f"[Multi] Pareto Plot: {result['pareto_plot_path']}")
