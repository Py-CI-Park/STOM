# -*- coding: utf-8 -*-
"""
Phase 2 Runner

세그먼트 분할 + 필터 후보 + 조합 최적화 + (옵션) Optuna 임계값 최적화.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from backtester.output_manifest import strip_numeric_prefix
from .segmentation import SegmentBuilder, SegmentConfig, normalize_segment_columns

from .filter_evaluator import FilterEvaluator, FilterEvaluatorConfig
from .combination_optimizer import (
    CombinationOptimizerConfig,
    generate_local_combinations,
    optimize_global_combination,
)
from .threshold_optimizer import ThresholdOptimizerConfig, optimize_thresholds
from .code_generator import build_segment_filter_code, save_segment_code
from .segment_outputs import (
    build_segment_summary,
    resolve_segment_output_dir,
    save_segment_summary,
    save_segment_filters,
    build_local_combos_df,
    save_segment_local_combos,
    build_global_combo_df,
    save_segment_combos,
    save_segment_thresholds,
    save_segment_ranges,
)
from .risk_metrics import summarize_risk


@dataclass
class Phase2RunnerConfig:
    output_dir: Optional[str] = None
    prefix: Optional[str] = None
    enable_optuna: bool = False


def run_phase2(
    detail_path: str,
    seg_config: Optional[SegmentConfig] = None,
    filter_config: Optional[FilterEvaluatorConfig] = None,
    combo_config: Optional[CombinationOptimizerConfig] = None,
    threshold_config: Optional[ThresholdOptimizerConfig] = None,
    runner_config: Optional[Phase2RunnerConfig] = None,
) -> dict:
    runner_config = runner_config or Phase2RunnerConfig()
    detail_path = Path(detail_path).expanduser().resolve()
    df_detail = pd.read_csv(detail_path, encoding='utf-8-sig')
    df_detail = normalize_segment_columns(df_detail)
    output_dir = resolve_segment_output_dir(detail_path, runner_config.output_dir)


    builder = SegmentBuilder(seg_config)
    segments = builder.build_segments(df_detail)
    total_trades = sum(len(seg) for seg in segments.values())

    output_prefix = runner_config.prefix or _build_prefix(detail_path.name)

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

    combo_config = combo_config or CombinationOptimizerConfig()
    segment_combos = {}
    for seg_id, seg_df in segments.items():
        candidates = candidates_by_segment.get(seg_id, [])
        segment_combos[seg_id] = generate_local_combinations(seg_df, candidates, combo_config)

    local_combo_df = build_local_combos_df(segment_combos)
    local_combo_path = save_segment_local_combos(local_combo_df, output_dir, output_prefix)

    global_best = optimize_global_combination(segment_combos, total_trades, combo_config)

    # [2026-01-01 추가] global_best에 ranges_path 저장
    # - 목적: 필터 적용 시 동일한 세그먼트 경계 사용
    # - 효과: combos.csv 예측값과 실제 적용값 일치
    if global_best and isinstance(global_best, dict):
        global_best['ranges_path'] = ranges_path

    filtered_df = _apply_global_combination(segments, global_best)
    risk_metrics = summarize_risk(filtered_df)
    global_combo_df = build_global_combo_df(global_best, total_trades, risk_metrics=risk_metrics)
    global_combo_path = save_segment_combos(global_combo_df, output_dir, output_prefix)

    segment_code_path = None
    segment_code_summary = None
    if global_best:
        code_lines, code_summary = build_segment_filter_code(
            global_best,
            seg_config,
            runtime_market_cap_ranges=builder.runtime_market_cap_ranges,
            runtime_time_ranges=builder.runtime_time_ranges,
        )
        segment_code_summary = code_summary
        segment_code_path = save_segment_code(code_lines, output_dir, output_prefix)

    thresholds_path = None
    if runner_config.enable_optuna:
        threshold_config = threshold_config or ThresholdOptimizerConfig()
        threshold_rows = []
        for seg_id, seg_df in segments.items():
            cols = [c.get('column') for c in candidates_by_segment.get(seg_id, []) if c.get('column')]
            cols = sorted(set(cols))
            if not cols:
                continue
            result = optimize_thresholds(seg_df, cols, threshold_config)
            if result is None:
                continue
            threshold_rows.append({
                'segment_id': seg_id,
                'best_value': result.get('best_value'),
                'best_params': result.get('best_params'),
                'n_trials': result.get('n_trials'),
            })

        if threshold_rows:
            thresholds_df = pd.DataFrame(threshold_rows)
            thresholds_path = save_segment_thresholds(
                thresholds_df, output_dir, output_prefix
            )

    return {
        'summary_path': summary_path,
        'ranges_path': ranges_path,
        'filters_path': filters_path,
        'local_combo_path': local_combo_path,
        'global_combo_path': global_combo_path,
        'thresholds_path': thresholds_path,
        'segment_code_path': segment_code_path,
        'segment_code_summary': segment_code_summary,
        'global_best': global_best,
    }


def _build_prefix(filename: str) -> str:
    filename = strip_numeric_prefix(filename)
    if filename.endswith('_detail.csv'):
        return filename.replace('_detail.csv', '')
    return filename.replace('.csv', '')


def _apply_global_combination(segments: dict, global_best: Optional[dict]) -> pd.DataFrame:
    if not isinstance(global_best, dict) or not isinstance(segments, dict):
        return pd.DataFrame()
    combo_map = global_best.get('combination')
    if not isinstance(combo_map, dict):
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


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m backtester.segment_analysis.phase2_runner <detail.csv> [--optuna]")

    enable_optuna = '--optuna' in sys.argv
    result = run_phase2(sys.argv[1], runner_config=Phase2RunnerConfig(enable_optuna=enable_optuna))

    print(f"[Phase2] Summary: {result['summary_path']}")
    print(f"[Phase2] Filters: {result['filters_path']}")
    print(f"[Phase2] Local combos: {result['local_combo_path']}")
    print(f"[Phase2] Global combo: {result['global_combo_path']}")
    if result.get('segment_code_path'):
        print(f"[Phase2] Segment code: {result['segment_code_path']}")
    if enable_optuna:
        print(f"[Phase2] Thresholds: {result['thresholds_path']}")
