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
    resolve_segment_output_dir,
    save_segment_summary,
    save_segment_filters,
    save_segment_validation,
    save_segment_ranges,
)
from .segment_visualizer import plot_segment_heatmap, plot_filter_efficiency


@dataclass
class Phase3RunnerConfig:
    output_dir: Optional[str] = None
    prefix: Optional[str] = None


def run_phase3(
    detail_path: str,
    seg_config: Optional[SegmentConfig] = None,
    filter_config: Optional[FilterEvaluatorConfig] = None,
    validation_config: Optional[StabilityValidationConfig] = None,
    runner_config: Optional[Phase3RunnerConfig] = None,
    global_best: Optional[dict] = None,
    buystg_name: Optional[str] = None,
    sellstg_name: Optional[str] = None,
    save_file_name: Optional[str] = None,
) -> dict:
    runner_config = runner_config or Phase3RunnerConfig()
    detail_path = Path(detail_path).expanduser().resolve()
    df_detail = pd.read_csv(detail_path, encoding='utf-8-sig')
    output_dir = resolve_segment_output_dir(detail_path, runner_config.output_dir)

    builder = SegmentBuilder(seg_config)
    segments = builder.build_segments(df_detail)

    output_prefix = runner_config.prefix or _build_prefix(detail_path.name)
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    summary_df = build_segment_summary(segments, builder.out_of_range)
    summary_path = save_segment_summary(summary_df, output_dir, output_prefix)
    ranges_df = builder.get_range_summary_df()
    ranges_path = save_segment_ranges(ranges_df, output_dir, output_prefix)

    evaluator = FilterEvaluator(filter_config)
    filters_df = evaluator.evaluate_all_segments(segments)
    filters_path = save_segment_filters(filters_df, output_dir, output_prefix)

    candidates_by_segment = {seg_id: [] for seg_id in segments.keys()}
    if filters_df is not None and not filters_df.empty:
        for row in filters_df.to_dict(orient='records'):
            seg_id = row.get('segment_id')
            if seg_id in candidates_by_segment:
                candidates_by_segment[seg_id].append(row)

    validation_config = validation_config or StabilityValidationConfig()
    validation_df = validate_filter_stability(segments, candidates_by_segment, validation_config)
    validation_path = save_segment_validation(validation_df, output_dir, output_prefix)

    filtered_summary_df = _build_filtered_segment_summary(segments, filters_df, global_best)

    memo_name = save_file_name or output_prefix
    heatmap_path = plot_segment_heatmap(
        summary_df,
        str(output_dir_path / f"{output_prefix}_segment_heatmap.png"),
        filtered_summary_df=filtered_summary_df,
        ranges_df=ranges_df,
        buystg_name=buystg_name,
        sellstg_name=sellstg_name,
        save_file_name=memo_name,
    )
    efficiency_path = plot_filter_efficiency(
        filters_df,
        str(output_dir_path / f"{output_prefix}_filter_efficiency.png"),
        buystg_name=buystg_name,
        sellstg_name=sellstg_name,
        save_file_name=memo_name,
    )

    return {
        'summary_path': summary_path,
        'ranges_path': ranges_path,
        'filters_path': filters_path,
        'validation_path': validation_path,
        'heatmap_path': heatmap_path,
        'efficiency_path': efficiency_path,
    }


def _build_filtered_segment_summary(
    segments: dict,
    filters_df: pd.DataFrame,
    global_best: Optional[dict] = None,
) -> pd.DataFrame:
    if not isinstance(segments, dict) or not segments:
        return pd.DataFrame()
    if isinstance(global_best, dict):
        combo_map = global_best.get('combination')
        if isinstance(combo_map, dict) and combo_map:
            filtered_segments = {}
            for seg_id, seg_df in segments.items():
                combo = combo_map.get(seg_id)
                if combo is None or combo.get('exclude_segment'):
                    filtered_segments[seg_id] = seg_df.iloc[0:0].copy()
                    continue
                filters = combo.get('filters') or []
                filtered_segments[seg_id] = _apply_filters(seg_df, filters)
            return build_segment_summary(filtered_segments)

    if filters_df is None or filters_df.empty:
        return build_segment_summary(segments)

    df = filters_df.copy()
    if 'segment_id' not in df.columns:
        return build_segment_summary(segments)

    df['efficiency'] = pd.to_numeric(df.get('efficiency'), errors='coerce').fillna(0)
    df['improvement'] = pd.to_numeric(df.get('improvement'), errors='coerce').fillna(0)
    df = df.sort_values(['segment_id', 'efficiency', 'improvement'], ascending=[True, False, False])

    best_filters = {}
    for seg_id, seg_rows in df.groupby('segment_id', sort=False):
        row = seg_rows.iloc[0].to_dict()
        best_filters[seg_id] = row

    filtered_segments = {}
    for seg_id, seg_df in segments.items():
        if seg_df is None or seg_df.empty:
            filtered_segments[seg_id] = seg_df
            continue
        best = best_filters.get(seg_id)
        if best:
            filtered_segments[seg_id] = _apply_filters(seg_df, [best])
        else:
            filtered_segments[seg_id] = seg_df.copy()

    return build_segment_summary(filtered_segments)


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
