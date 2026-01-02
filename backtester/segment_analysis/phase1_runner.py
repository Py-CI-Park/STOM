# -*- coding: utf-8 -*-
"""
Phase 1 Runner

세그먼트 분할 + 필터 평가 + 기본 산출물 생성.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from backtester.output_manifest import strip_numeric_prefix
from .segmentation import SegmentBuilder, SegmentConfig
from .filter_evaluator import FilterEvaluator, FilterEvaluatorConfig
from .segment_outputs import (
    build_segment_summary,
    resolve_segment_output_dir,
    save_segment_summary,
    save_segment_filters,
    save_segment_ranges,
)


@dataclass
class Phase1RunnerConfig:
    output_dir: Optional[str] = None
    prefix: Optional[str] = None


def run_phase1(
    detail_path: str,
    seg_config: Optional[SegmentConfig] = None,
    filter_config: Optional[FilterEvaluatorConfig] = None,
    runner_config: Optional[Phase1RunnerConfig] = None,
) -> Tuple[str, Optional[str]]:
    runner_config = runner_config or Phase1RunnerConfig()
    detail_path = Path(detail_path).expanduser().resolve()
    df_detail = pd.read_csv(detail_path, encoding='utf-8-sig')
    output_dir = resolve_segment_output_dir(detail_path, runner_config.output_dir)

    builder = SegmentBuilder(seg_config)
    segments = builder.build_segments(df_detail)

    summary_df = build_segment_summary(segments, builder.out_of_range)
    output_prefix = runner_config.prefix or _build_prefix(detail_path.name)
    summary_path = save_segment_summary(summary_df, output_dir, output_prefix)
    ranges_df = builder.get_range_summary_df()
    save_segment_ranges(ranges_df, output_dir, output_prefix)

    evaluator = FilterEvaluator(filter_config)
    filters_df = evaluator.evaluate_all_segments(segments)
    filters_path = save_segment_filters(filters_df, output_dir, output_prefix)

    return summary_path, filters_path


def _build_prefix(filename: str) -> str:
    filename = strip_numeric_prefix(filename)
    if filename.endswith('_detail.csv'):
        return filename.replace('_detail.csv', '')
    return filename.replace('.csv', '')


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m backtester.segment_analysis.phase1_runner <detail.csv>")

    summary_path, filters_path = run_phase1(sys.argv[1])
    print(f"[Phase1] Summary: {summary_path}")
    if filters_path:
        print(f"[Phase1] Filters: {filters_path}")
    else:
        print("[Phase1] Filters: (empty)")
