# -*- coding: utf-8 -*-
"""
Segment Mode Comparator

고정/반-동적/동적 분할 모드별 성능을 비교하는 리포트를 생성합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
import re

import pandas as pd

from backtester.output_manifest import strip_numeric_prefix
from .segmentation import SegmentConfig
from .filter_evaluator import FilterEvaluatorConfig
from .combination_optimizer import CombinationOptimizerConfig
from .phase2_runner import run_phase2, Phase2RunnerConfig
from .segment_outputs import resolve_segment_output_dir, save_segment_mode_comparison
from backtester.output_paths import get_legacy_graph_dir


@dataclass
class SegmentModeComparisonConfig:
    output_dir: Optional[str] = None
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
    output_dir = resolve_segment_output_dir(detail_path, runner_config.output_dir)

    output_prefix = runner_config.prefix or _build_prefix(detail_path.name)
    global_stats = _load_global_filter_stats(detail_path, output_prefix)
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
                output_dir=output_dir,
                prefix=f"{output_prefix}_{mode_name}",
                enable_optuna=runner_config.enable_optuna,
            ),
        )

        mode_results[mode_name] = phase2_result
        row = _build_row(mode_name, phase2_result, global_stats)
        rows.append(row)

    df_comp = pd.DataFrame(rows)
    comparison_path = save_segment_mode_comparison(
        df_comp, output_dir, output_prefix
    )

    return {
        'comparison_path': comparison_path,
        'mode_results': mode_results,
        'rows': len(df_comp),
    }


def _build_prefix(filename: str) -> str:
    filename = strip_numeric_prefix(filename)
    if filename.endswith('_detail.csv'):
        return filename.replace('_detail.csv', '')
    return filename.replace('.csv', '')


def _clone_segment_config(seg_config: Optional[SegmentConfig]) -> SegmentConfig:
    base = seg_config or SegmentConfig()
    return SegmentConfig(
        market_cap_ranges=dict(base.market_cap_ranges),
        time_ranges=dict(base.time_ranges),
        time_segment_target_minutes=base.time_segment_target_minutes,
        time_segment_min_count=base.time_segment_min_count,
        time_segment_max_count=base.time_segment_max_count,
        min_trades=dict(base.min_trades),
        max_exclusion=dict(base.max_exclusion),
        validation=dict(base.validation),
        dynamic_mode=base.dynamic_mode,
        auto_dynamic_market_cap=base.auto_dynamic_market_cap,
        dynamic_market_cap_quantiles=tuple(base.dynamic_market_cap_quantiles),
        dynamic_time_quantiles=tuple(base.dynamic_time_quantiles),
        dynamic_min_samples=base.dynamic_min_samples,
    )


def _build_row(mode: str, result: dict, global_stats: Optional[dict] = None) -> dict:
    row = {
        'mode': mode,
        'summary_path': result.get('summary_path'),
        'ranges_path': result.get('ranges_path'),
        'global_combo_path': result.get('global_combo_path'),
        'local_combo_path': result.get('local_combo_path'),
        'filters_path': result.get('filters_path'),
    }

    if isinstance(global_stats, dict) and global_stats:
        row.update(global_stats)

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

    _apply_global_comparison(row, global_stats)
    return row


def _load_global_filter_stats(detail_path: Path, prefix: str) -> dict:
    report_path = _find_global_report_path(detail_path, prefix)
    if report_path is None:
        return {}
    return _parse_global_filter_report(report_path)


def _find_global_report_path(detail_path: Path, prefix: str) -> Optional[Path]:
    candidate = detail_path.with_name(f"{prefix}_report.txt")
    if candidate.exists():
        return candidate
    fallback = get_legacy_graph_dir() / f"{prefix}_report.txt"
    if fallback.exists():
        return fallback
    return None


def _parse_global_filter_report(report_path: Path) -> dict:
    try:
        text = report_path.read_text(encoding='utf-8-sig', errors='ignore')
    except Exception:
        return {}

    improvement = None
    exclusion_ratio = None
    filter_count = None
    in_apply_block = False

    for line in text.splitlines():
        if '필터 수' in line:
            match = re.search(r'필터 수:\s*(\d+)', line)
            if match:
                filter_count = int(match.group(1))

        if '예상 총 개선' in line:
            match = re.search(r'예상 총 개선[^:]*:\s*([+-]?[0-9,]+)원', line)
            if match:
                improvement = float(match.group(1).replace(',', ''))

        if line.strip().startswith('[적용 순서'):
            in_apply_block = True
            continue

        if in_apply_block:
            if line.strip().startswith('[') and not line.strip().startswith('[적용 순서'):
                in_apply_block = False
            match = re.search(r'제외\s*([0-9.]+)%', line)
            if match:
                exclusion_ratio = float(match.group(1)) / 100.0

    if exclusion_ratio is None:
        for line in text.splitlines():
            match = re.search(r'제외\s*([0-9.]+)%', line)
            if match:
                exclusion_ratio = float(match.group(1)) / 100.0

    remaining_ratio = None
    if exclusion_ratio is not None:
        remaining_ratio = 1.0 - exclusion_ratio

    stats = {}
    if improvement is not None:
        stats['global_filter_improvement'] = improvement
    if exclusion_ratio is not None:
        stats['global_filter_exclusion_ratio'] = exclusion_ratio
    if remaining_ratio is not None:
        stats['global_filter_remaining_ratio'] = remaining_ratio
    if filter_count is not None:
        stats['global_filter_count'] = filter_count
    stats['global_filter_report_path'] = str(report_path)
    return stats


def _apply_global_comparison(row: dict, global_stats: Optional[dict]) -> None:
    if not isinstance(global_stats, dict) or not global_stats:
        return
    total_improvement = _to_float(row.get('total_improvement'))
    remaining_ratio = _to_float(row.get('remaining_ratio'))
    global_improvement = _to_float(global_stats.get('global_filter_improvement'))
    global_remaining = _to_float(global_stats.get('global_filter_remaining_ratio'))

    if total_improvement is not None and global_improvement is not None:
        row['improvement_vs_global'] = total_improvement - global_improvement
    if remaining_ratio is not None and global_remaining is not None:
        row['remaining_ratio_vs_global'] = remaining_ratio - global_remaining


def _to_float(value: object) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m backtester.segment_analysis.segment_mode_comparator <detail.csv>")

    result = run_segment_mode_comparison(sys.argv[1])
    print(f"[ModeCompare] CSV: {result['comparison_path']}")
