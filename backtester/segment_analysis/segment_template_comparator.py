# -*- coding: utf-8 -*-
"""
Segment Template Comparator

시간/시가총액 세그먼트 템플릿을 여러 개 비교하여
가장 타당한 분할 구성을 찾습니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
import re

import pandas as pd

from .segmentation import SegmentConfig
from .filter_evaluator import FilterEvaluatorConfig
from .combination_optimizer import CombinationOptimizerConfig
from .phase2_runner import run_phase2, Phase2RunnerConfig
from .segment_outputs import resolve_segment_output_dir, save_segment_template_comparison
from backtester.output_paths import get_legacy_graph_dir


@dataclass
class SegmentTemplate:
    name: str
    market_cap_ranges: Dict[str, Tuple[float, float]]
    time_ranges: Dict[str, Tuple[int, int]]
    description: str = ""

    def segment_count(self) -> int:
        return len(self.market_cap_ranges) * len(self.time_ranges)

    def cap_count(self) -> int:
        return len(self.market_cap_ranges)

    def time_count(self) -> int:
        return len(self.time_ranges)

    def to_config(self, base: Optional[SegmentConfig] = None) -> SegmentConfig:
        cfg = base or SegmentConfig()
        return SegmentConfig(
            market_cap_ranges=dict(self.market_cap_ranges),
            time_ranges=dict(self.time_ranges),
            min_trades=dict(cfg.min_trades),
            max_exclusion=dict(cfg.max_exclusion),
            validation=dict(cfg.validation),
            dynamic_mode='fixed',
            dynamic_market_cap_quantiles=tuple(cfg.dynamic_market_cap_quantiles),
            dynamic_time_quantiles=tuple(cfg.dynamic_time_quantiles),
            dynamic_min_samples=cfg.dynamic_min_samples,
        )


@dataclass
class SegmentTemplateScoreConfig:
    min_remaining_ratio: float = 0.2
    min_improvement: float = 0.0
    weight_improvement: float = 0.45
    weight_remaining: float = 0.25
    weight_mdd: float = 0.2
    weight_volatility: float = 0.1
    weight_complexity: float = 0.05


@dataclass
class SegmentTemplateComparisonConfig:
    output_dir: Optional[str] = None
    prefix: Optional[str] = None
    max_templates: int = 8
    enable_optuna: bool = False
    enable_dynamic_expansion: bool = True
    dynamic_modes: Iterable[str] = ('semi', 'time_only')
    top_n_dynamic: int = 2
    score_config: SegmentTemplateScoreConfig = field(default_factory=SegmentTemplateScoreConfig)


def run_segment_template_comparison(
    detail_path: str,
    seg_config: Optional[SegmentConfig] = None,
    filter_config: Optional[FilterEvaluatorConfig] = None,
    combo_config: Optional[CombinationOptimizerConfig] = None,
    runner_config: Optional[SegmentTemplateComparisonConfig] = None,
    templates: Optional[List[SegmentTemplate]] = None,
) -> dict:
    runner_config = runner_config or SegmentTemplateComparisonConfig()
    detail_path = Path(detail_path).expanduser().resolve()
    output_dir = resolve_segment_output_dir(detail_path, runner_config.output_dir)
    output_prefix = runner_config.prefix or _build_prefix(detail_path.name)
    base_cfg = seg_config or SegmentConfig()

    templates = templates or build_default_templates()
    templates = templates[: runner_config.max_templates] if runner_config.max_templates else templates

    global_stats = _load_global_filter_stats(detail_path, output_prefix)
    rows = []
    results = {}

    for tmpl in templates:
        result = _run_template_phase2(
            detail_path,
            output_prefix,
            output_dir,
            tmpl,
            base_cfg,
            filter_config,
            combo_config,
            runner_config,
            variant='fixed',
        )
        row = _build_row(tmpl, result, global_stats, variant='fixed')
        rows.append(row)
        results[f"{tmpl.name}:fixed"] = result

    df = pd.DataFrame(rows)
    if not df.empty:
        df = _apply_scores(df, runner_config.score_config)

    if runner_config.enable_dynamic_expansion and not df.empty:
        df, results = _expand_dynamic_variants(
            df,
            results,
            detail_path,
            output_prefix,
            output_dir,
            templates,
            base_cfg,
            filter_config,
            combo_config,
            runner_config,
            global_stats,
        )

    comparison_path = save_segment_template_comparison(
        df, output_dir, output_prefix
    )

    return {
        'comparison_path': comparison_path,
        'rows': len(df),
        'results': results,
    }


def build_default_templates() -> List[SegmentTemplate]:
    time_4 = {
        'T1_090000_090500': (90000, 90500),
        'T2_090500_091000': (90500, 91000),
        'T3_091000_091500': (91000, 91500),
        'T4_091500_092000': (91500, 92000),
    }
    time_5 = {
        'T1_090000_090300': (90000, 90300),
        'T2_090300_090600': (90300, 90600),
        'T3_090600_091000': (90600, 91000),
        'T4_091000_091500': (91000, 91500),
        'T5_091500_092000': (91500, 92000),
    }
    time_3 = {
        'T1_090000_090700': (90000, 90700),
        'T2_090700_091300': (90700, 91300),
        'T3_091300_092000': (91300, 92000),
    }

    cap_3 = {
        '소형주': (0, 3000),
        '중형주': (3000, 10000),
        '대형주': (10000, float('inf')),
    }
    cap_2 = {
        '중소형주': (0, 5000),
        '대형주': (5000, float('inf')),
    }
    cap_4 = {
        '초소형주': (0, 1500),
        '소형주': (1500, 3000),
        '중형주': (3000, 7000),
        '대형주': (7000, float('inf')),
    }

    return [
        SegmentTemplate(
            name='T4C3_base',
            market_cap_ranges=cap_3,
            time_ranges=time_4,
            description='기본 3시총 × 4시간',
        ),
        SegmentTemplate(
            name='T5C3_time5',
            market_cap_ranges=cap_3,
            time_ranges=time_5,
            description='시간 5분할 × 시총 3구간',
        ),
        SegmentTemplate(
            name='T3C3_time3',
            market_cap_ranges=cap_3,
            time_ranges=time_3,
            description='시간 3분할 × 시총 3구간',
        ),
        SegmentTemplate(
            name='T4C2_cap2',
            market_cap_ranges=cap_2,
            time_ranges=time_4,
            description='시총 2구간 × 시간 4구간',
        ),
        SegmentTemplate(
            name='T4C4_cap4',
            market_cap_ranges=cap_4,
            time_ranges=time_4,
            description='시총 4구간 × 시간 4구간',
        ),
    ]


def _run_template_phase2(
    detail_path: Path,
    output_prefix: str,
    output_dir: str,
    template: SegmentTemplate,
    base_cfg: SegmentConfig,
    filter_config: Optional[FilterEvaluatorConfig],
    combo_config: Optional[CombinationOptimizerConfig],
    runner_config: SegmentTemplateComparisonConfig,
    variant: str,
    dynamic_mode: Optional[str] = None,
) -> dict:
    cfg = template.to_config(base_cfg)
    if dynamic_mode:
        cfg.dynamic_mode = dynamic_mode

    suffix = _safe_name(template.name)
    variant_tag = _safe_name(variant)
    if dynamic_mode:
        variant_tag = _safe_name(f"{variant}_{dynamic_mode}")

    prefix = f"{output_prefix}_tmpl_{suffix}_{variant_tag}"
    return run_phase2(
        str(detail_path),
        seg_config=cfg,
        filter_config=filter_config,
        combo_config=combo_config,
        runner_config=Phase2RunnerConfig(
            output_dir=output_dir,
            prefix=prefix,
            enable_optuna=runner_config.enable_optuna,
        ),
    )


def _build_row(
    template: SegmentTemplate,
    result: dict,
    global_stats: Optional[dict],
    variant: str,
    dynamic_mode: Optional[str] = None,
) -> dict:
    row = {
        'template': template.name,
        'variant': variant,
        'dynamic_mode': dynamic_mode,
        'segment_count': template.segment_count(),
        'cap_count': template.cap_count(),
        'time_count': template.time_count(),
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
                    'validation_score': combo.get('validation_score'),
                    'mdd_won': combo.get('mdd_won'),
                    'mdd_pct': combo.get('mdd_pct'),
                    'profit_volatility': combo.get('profit_volatility'),
                    'return_volatility': combo.get('return_volatility'),
                })
        except Exception:
            pass

    _apply_global_comparison(row, global_stats)
    return row


def _apply_scores(df: pd.DataFrame, score_cfg: SegmentTemplateScoreConfig) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    data = df.copy()
    data['total_improvement'] = pd.to_numeric(data.get('total_improvement'), errors='coerce').fillna(0.0)
    data['remaining_ratio'] = pd.to_numeric(data.get('remaining_ratio'), errors='coerce').fillna(0.0)
    data['mdd_pct'] = pd.to_numeric(data.get('mdd_pct'), errors='coerce').fillna(0.0)
    data['profit_volatility'] = pd.to_numeric(data.get('profit_volatility'), errors='coerce').fillna(0.0)
    data['segment_count'] = pd.to_numeric(data.get('segment_count'), errors='coerce').fillna(0.0)

    data['eligible'] = (
        (data['total_improvement'] > score_cfg.min_improvement) &
        (data['remaining_ratio'] >= score_cfg.min_remaining_ratio)
    )

    norm_impr = _normalize_series(data['total_improvement'])
    norm_rem = _normalize_series(data['remaining_ratio'])
    norm_mdd = _normalize_series(data['mdd_pct'])
    norm_vol = _normalize_series(data['profit_volatility'])
    norm_comp = _normalize_series(data['segment_count'])

    score = (
        norm_impr * score_cfg.weight_improvement
        + norm_rem * score_cfg.weight_remaining
        + (1.0 - norm_mdd) * score_cfg.weight_mdd
        + (1.0 - norm_vol) * score_cfg.weight_volatility
        - norm_comp * score_cfg.weight_complexity
    )
    data['score'] = score
    return data


def _expand_dynamic_variants(
    df: pd.DataFrame,
    results: dict,
    detail_path: Path,
    output_prefix: str,
    output_dir: str,
    templates: List[SegmentTemplate],
    base_cfg: SegmentConfig,
    filter_config: Optional[FilterEvaluatorConfig],
    combo_config: Optional[CombinationOptimizerConfig],
    runner_config: SegmentTemplateComparisonConfig,
    global_stats: Optional[dict],
) -> Tuple[pd.DataFrame, dict]:
    if df.empty:
        return df, results

    ranked = df.sort_values(['eligible', 'score'], ascending=[False, False])
    top_rows = ranked.head(max(1, runner_config.top_n_dynamic))
    top_template_names = set(top_rows['template'].astype(str).tolist())

    template_map = {t.name: t for t in templates}
    dynamic_rows = []

    for tmpl_name in top_template_names:
        tmpl = template_map.get(tmpl_name)
        if tmpl is None:
            continue
        for mode in runner_config.dynamic_modes:
            mode_name = str(mode)
            if _requires_four_time_ranges(mode_name) and tmpl.time_count() != 4:
                continue
            result = _run_template_phase2(
                detail_path,
                output_prefix,
                output_dir,
                tmpl,
                base_cfg,
                filter_config,
                combo_config,
                runner_config,
                variant='dynamic',
                dynamic_mode=mode_name,
            )
            row = _build_row(tmpl, result, global_stats, variant='dynamic', dynamic_mode=mode_name)
            dynamic_rows.append(row)
            results[f"{tmpl.name}:dynamic:{mode_name}"] = result

    if dynamic_rows:
        df_all = pd.concat([df, pd.DataFrame(dynamic_rows)], axis=0, ignore_index=True)
        df_all = _apply_scores(df_all, runner_config.score_config)
        return df_all, results

    return df, results


def _requires_four_time_ranges(mode: str) -> bool:
    return mode in ('time_only', 'dynamic')


def _build_prefix(filename: str) -> str:
    if filename.endswith('_detail.csv'):
        return filename.replace('_detail.csv', '')
    return filename.replace('.csv', '')


def _safe_name(text: str) -> str:
    cleaned = re.sub(r'[^0-9a-zA-Z_]+', '_', str(text))
    return cleaned.strip('_') or 'template'


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


def _normalize_series(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce').fillna(0.0)
    min_v = float(values.min())
    max_v = float(values.max())
    if max_v == min_v:
        return pd.Series([0.0] * len(values), index=values.index)
    return (values - min_v) / (max_v - min_v)


def _to_float(value: object) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m backtester.segment_analysis.segment_template_comparator <detail.csv>")

    result = run_segment_template_comparison(sys.argv[1])
    print(f"[TemplateCompare] CSV: {result['comparison_path']}")
