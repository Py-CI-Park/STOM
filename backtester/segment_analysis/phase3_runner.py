# -*- coding: utf-8 -*-
"""
Phase 3 Runner

검증(워크포워드) + 시각화(히트맵/효율 차트) 산출물 생성.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from .segmentation import SegmentBuilder, SegmentConfig
from .filter_evaluator import FilterEvaluator, FilterEvaluatorConfig
from .validation import StabilityValidationConfig, validate_filter_stability
from .segment_outputs import (
    build_segment_summary,
    save_segment_summary,
    save_segment_filters,
    save_segment_validation,
)
from .segment_visualizer import plot_segment_heatmap, plot_filter_efficiency


@dataclass
class Phase3RunnerConfig:
    output_dir: str = 'backtester/segment_outputs'
    prefix: Optional[str] = None


def run_phase3(
    detail_path: str,
    seg_config: Optional[SegmentConfig] = None,
    filter_config: Optional[FilterEvaluatorConfig] = None,
    validation_config: Optional[StabilityValidationConfig] = None,
    runner_config: Optional[Phase3RunnerConfig] = None,
) -> dict:
    runner_config = runner_config or Phase3RunnerConfig()
    detail_path = Path(detail_path).expanduser().resolve()
    df_detail = pd.read_csv(detail_path, encoding='utf-8-sig')

    builder = SegmentBuilder(seg_config)
    segments = builder.build_segments(df_detail)

    output_prefix = runner_config.prefix or _build_prefix(detail_path.name)
    output_dir = Path(runner_config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_df = build_segment_summary(segments, builder.out_of_range)
    summary_path = save_segment_summary(summary_df, runner_config.output_dir, output_prefix)

    evaluator = FilterEvaluator(filter_config)
    filters_df = evaluator.evaluate_all_segments(segments)
    filters_path = save_segment_filters(filters_df, runner_config.output_dir, output_prefix)

    candidates_by_segment = {seg_id: [] for seg_id in segments.keys()}
    if filters_df is not None and not filters_df.empty:
        for row in filters_df.to_dict(orient='records'):
            seg_id = row.get('segment_id')
            if seg_id in candidates_by_segment:
                candidates_by_segment[seg_id].append(row)

    validation_config = validation_config or StabilityValidationConfig()
    validation_df = validate_filter_stability(segments, candidates_by_segment, validation_config)
    validation_path = save_segment_validation(validation_df, runner_config.output_dir, output_prefix)

    heatmap_path = plot_segment_heatmap(
        summary_df, str(output_dir / f"{output_prefix}_segment_heatmap.png")
    )
    efficiency_path = plot_filter_efficiency(
        filters_df, str(output_dir / f"{output_prefix}_filter_efficiency.png")
    )

    return {
        'summary_path': summary_path,
        'filters_path': filters_path,
        'validation_path': validation_path,
        'heatmap_path': heatmap_path,
        'efficiency_path': efficiency_path,
    }


def _build_prefix(filename: str) -> str:
    if filename.endswith('_detail.csv'):
        return filename.replace('_detail.csv', '')
    return filename.replace('.csv', '')


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m backtester.segment_analysis.phase3_runner <detail.csv>")

    result = run_phase3(sys.argv[1])
    print(f"[Phase3] Summary: {result['summary_path']}")
    print(f"[Phase3] Filters: {result['filters_path']}")
    print(f"[Phase3] Validation: {result['validation_path']}")
    print(f"[Phase3] Heatmap: {result['heatmap_path']}")
    print(f"[Phase3] Efficiency: {result['efficiency_path']}")
