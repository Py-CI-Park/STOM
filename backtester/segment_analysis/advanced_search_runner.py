# -*- coding: utf-8 -*-
"""
Advanced Search Runner

Optuna 가중치 탐색 및 NSGA-II(옵션) 기반 고급 탐색을 실행합니다.
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
from .segment_outputs import (
    resolve_segment_output_dir,
    save_pareto_front,
    save_advanced_optuna_result,
    save_nsga2_front,
    save_segment_ranges,
)
from .segment_visualizer import plot_pareto_front


@dataclass
class AdvancedSearchRunnerConfig:
    output_dir: Optional[str] = None
    prefix: Optional[str] = None
    enable_optuna: bool = True
    enable_nsga2: bool = True
    optuna_trials: int = 80
    candidate_limit: int = 60


def run_advanced_search(
    detail_path: str,
    seg_config: Optional[SegmentConfig] = None,
    filter_config: Optional[FilterEvaluatorConfig] = None,
    combo_config: Optional[CombinationOptimizerConfig] = None,
    multi_config: Optional[MultiObjectiveConfig] = None,
    runner_config: Optional[AdvancedSearchRunnerConfig] = None,
) -> dict:
    runner_config = runner_config or AdvancedSearchRunnerConfig()
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
        segment_combos, total_trades, combo_config, top_n=runner_config.candidate_limit
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

    optuna_path = None
    if runner_config.enable_optuna:
        optuna_path = _run_optuna_weight_search(
            candidates_df,
            output_dir,
            output_prefix,
            runner_config.optuna_trials,
        )

    nsga2_path = None
    if runner_config.enable_nsga2:
        nsga2_path = _run_nsga2_search(candidates_df, output_dir, output_prefix)

    return {
        'pareto_path': pareto_path,
        'pareto_plot_path': pareto_plot_path,
        'optuna_path': optuna_path,
        'nsga2_path': nsga2_path,
        'candidate_count': len(candidates_df) if candidates_df is not None else 0,
        'pareto_count': len(pareto_df) if pareto_df is not None else 0,
    }


def _run_optuna_weight_search(
    candidates_df: pd.DataFrame,
    output_dir: str,
    prefix: str,
    n_trials: int,
) -> Optional[str]:
    if candidates_df is None or candidates_df.empty:
        return None

    try:
        import optuna
    except Exception:
        return None

    df = candidates_df.copy()
    df = _normalize_objectives(df)
    if df.empty:
        return None

    def objective(trial):
        w_profit = trial.suggest_float('w_profit', 0.1, 1.0)
        w_remain = trial.suggest_float('w_remain', 0.1, 1.0)
        w_mdd = trial.suggest_float('w_mdd', 0.1, 1.0)
        w_vol = trial.suggest_float('w_vol', 0.1, 1.0)
        weights = _normalize_weights([w_profit, w_remain, w_mdd, w_vol])

        score = (
            df['profit_norm'] * weights[0]
            + df['remain_norm'] * weights[1]
            + df['mdd_norm'] * weights[2]
            + df['vol_norm'] * weights[3]
        )
        best = score.max()
        return float(best)

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials)

    best_params = study.best_params or {}
    weights = _normalize_weights([
        best_params.get('w_profit', 1.0),
        best_params.get('w_remain', 1.0),
        best_params.get('w_mdd', 1.0),
        best_params.get('w_vol', 1.0),
    ])
    score = (
        df['profit_norm'] * weights[0]
        + df['remain_norm'] * weights[1]
        + df['mdd_norm'] * weights[2]
        + df['vol_norm'] * weights[3]
    )
    idx = int(score.idxmax())
    best_row = candidates_df.loc[idx].to_dict()
    best_row.update({
        'w_profit': weights[0],
        'w_remain': weights[1],
        'w_mdd': weights[2],
        'w_vol': weights[3],
        'weighted_score': float(score.max()),
        'method': 'optuna_weight',
        'n_trials': n_trials,
    })

    df_out = pd.DataFrame([best_row])
    return save_advanced_optuna_result(df_out, output_dir, prefix)


def _run_nsga2_search(
    candidates_df: pd.DataFrame,
    output_dir: str,
    prefix: str,
) -> Optional[str]:
    if candidates_df is None or candidates_df.empty:
        return None

    try:
        import pymoo  # noqa: F401
    except Exception:
        df_out = build_pareto_front(candidates_df)
        if not df_out.empty:
            df_out = df_out.copy()
            df_out['method'] = 'pareto_fallback'
        return save_nsga2_front(df_out, output_dir, prefix)

    df_out = build_pareto_front(candidates_df)
    if not df_out.empty:
        df_out = df_out.copy()
        df_out['method'] = 'nsga2_ready'
    return save_nsga2_front(df_out, output_dir, prefix)


def _normalize_objectives(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['profit_norm'] = _normalize_series(df.get('total_improvement'))
    df['remain_norm'] = _normalize_series(df.get('remaining_ratio'))
    df['mdd_norm'] = 1.0 - _normalize_series(df.get('mdd_pct'))
    df['vol_norm'] = 1.0 - _normalize_series(df.get('profit_volatility'))
    return df


def _normalize_series(series: Optional[pd.Series]) -> pd.Series:
    if series is None:
        return pd.Series(dtype=float)
    values = pd.to_numeric(series, errors='coerce').fillna(0.0)
    min_v = float(values.min())
    max_v = float(values.max())
    if max_v == min_v:
        return pd.Series([0.0] * len(values), index=values.index)
    return (values - min_v) / (max_v - min_v)


def _normalize_weights(weights: list[float]) -> list[float]:
    total = sum(weights)
    if total <= 0:
        return [0.25, 0.25, 0.25, 0.25]
    return [w / total for w in weights]


def _build_prefix(filename: str) -> str:
    filename = strip_numeric_prefix(filename)
    if filename.endswith('_detail.csv'):
        return filename.replace('_detail.csv', '')
    return filename.replace('.csv', '')


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m backtester.segment_analysis.advanced_search_runner <detail.csv>")

    result = run_advanced_search(sys.argv[1])
    print(f"[Advanced] Pareto CSV: {result['pareto_path']}")
    print(f"[Advanced] Pareto Plot: {result['pareto_plot_path']}")
    print(f"[Advanced] Optuna: {result['optuna_path']}")
    print(f"[Advanced] NSGA2: {result['nsga2_path']}")
