# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import json
import shutil


@dataclass(frozen=True)
class OutputAliasRule:
    suffix: str
    prefix: str
    label: str
    category: str
    order: int


_ALIAS_RULES: List[OutputAliasRule] = [
    OutputAliasRule('_report.txt', '0', 'report', 'summary', 1),
    OutputAliasRule('_condition_study.md', '0', 'condition_study', 'summary', 2),
    OutputAliasRule('_segment_summary_full.txt', '3-9', 'segment_summary_full', 'segment', 390),
    OutputAliasRule('_detail.csv', '1-1', 'detail', 'detail', 110),
    OutputAliasRule('_detail_filtered.csv', '1-2', 'detail_filtered', 'detail', 120),
    OutputAliasRule('_detail_segment.csv', '1-3', 'detail_segment', 'detail', 130),
    OutputAliasRule('_summary.csv', '1-4', 'summary_csv', 'detail', 140),
    OutputAliasRule('_filter.csv', '2-1', 'filter', 'filter', 210),
    OutputAliasRule('_filter_combinations.csv', '2-2', 'filter_combinations', 'filter', 220),
    OutputAliasRule('_filter_stability.csv', '2-3', 'filter_stability', 'filter', 230),
    OutputAliasRule('_filter_lookahead.csv', '2-4', 'filter_lookahead', 'filter', 240),
    OutputAliasRule('_optimal_thresholds.csv', '2-5', 'optimal_thresholds', 'filter', 250),
    OutputAliasRule('_filter_verification.csv', '2-6', 'filter_verification', 'filter', 260),
    OutputAliasRule('_segment_summary.csv', '3-1', 'segment_summary', 'segment', 310),
    OutputAliasRule('_segment_filters.csv', '3-2', 'segment_filters', 'segment', 320),
    OutputAliasRule('_segment_local_combos.csv', '3-3', 'segment_local_combos', 'segment', 330),
    OutputAliasRule('_segment_combos.csv', '3-4', 'segment_combos', 'segment', 340),
    OutputAliasRule('_segment_ranges.csv', '3-5', 'segment_ranges', 'segment', 350),
    OutputAliasRule('_segment_code.txt', '3-6', 'segment_code', 'segment', 360),
    OutputAliasRule('_segment_code_final.txt', '3-7', 'segment_code_final', 'segment', 370),
    OutputAliasRule('_segment_validation.csv', '3-8', 'segment_validation', 'segment', 380),
    OutputAliasRule('_segment_template_comparison.csv', '3-10', 'segment_template_comparison', 'segment', 395),
    OutputAliasRule('_segment_mode_comparison.csv', '3-11', 'segment_mode_comparison', 'segment', 396),
    OutputAliasRule('_segment_thresholds.csv', '3-12', 'segment_thresholds', 'segment', 397),
    OutputAliasRule('_pareto_front.csv', '3-13', 'pareto_front', 'segment', 398),
    OutputAliasRule('_advanced_optuna.csv', '3-14', 'advanced_optuna', 'segment', 399),
    OutputAliasRule('_nsga2_front.csv', '3-15', 'nsga2_front', 'segment', 400),
    OutputAliasRule('_decision_score.csv', '3-16', 'decision_score', 'segment', 410),
    OutputAliasRule('_segment_verification.csv', '3-17', 'segment_verification', 'segment', 420),
    OutputAliasRule('_analysis.png', '4-2', 'analysis_chart', 'image', 420),
    OutputAliasRule('_comparison.png', '4-3', 'comparison_chart', 'image', 430),
    OutputAliasRule('_enhanced.png', '4-1', 'enhanced_chart', 'image', 410),
    OutputAliasRule('_segment_heatmap.png', '4-4', 'segment_heatmap', 'image', 440),
    OutputAliasRule('_filter_efficiency.png', '4-5', 'filter_efficiency', 'image', 450),
    OutputAliasRule('_segment_filtered.png', '4-6', 'segment_filtered', 'image', 460),
    OutputAliasRule('_segment_filtered_.png', '4-7', 'segment_filtered_summary', 'image', 470),
    OutputAliasRule('_filtered.png', '4-8', 'filtered', 'image', 480),
    OutputAliasRule('_filtered_.png', '4-9', 'filtered_summary', 'image', 490),
    OutputAliasRule('_.png', '4-10', 'extra_chart', 'image', 495),
    OutputAliasRule('.png', '4-11', 'main_chart', 'image', 500),
]


def build_output_manifest(
    output_dir: Path,
    save_file_name: str,
    *,
    enable_alias: bool = True,
    alias_mode: str = 'hardlink',
) -> Optional[Path]:
    output_dir = Path(output_dir)
    if not output_dir.exists() or not save_file_name:
        return None

    entries = []
    for file_path in output_dir.iterdir():
        if not file_path.is_file():
            continue
        rule = _match_rule(file_path.name, save_file_name)
        if rule is None:
            continue

        new_name = f"{rule.prefix}_{save_file_name}{rule.suffix}"
        alias_path = output_dir / new_name
        alias_action = None
        if enable_alias:
            alias_action = _ensure_alias(file_path, alias_path, alias_mode)

        entries.append(_build_entry(
            file_path,
            alias_path if enable_alias else None,
            rule,
            alias_action,
        ))

    entries.sort(key=lambda x: (x.get('order', 0), x.get('legacy_name', '')))

    manifest = {
        'save_file_name': save_file_name,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'alias_mode': alias_mode,
        'alias_enabled': bool(enable_alias),
        'entries': entries,
    }

    manifest_path = output_dir / f"0_{save_file_name}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8-sig')
    return manifest_path


def _match_rule(filename: str, save_file_name: str) -> Optional[OutputAliasRule]:
    if not filename.startswith(save_file_name):
        return None
    for rule in _ALIAS_RULES:
        if filename == f"{save_file_name}{rule.suffix}":
            return rule
    return None


def _ensure_alias(src: Path, dst: Path, mode: str) -> str:
    if src.resolve() == dst.resolve():
        return 'same'
    if dst.exists():
        return 'exists'

    dst.parent.mkdir(parents=True, exist_ok=True)
    if mode == 'none':
        return 'skipped'

    if mode == 'hardlink':
        try:
            dst.link_to(src)
            return 'hardlink'
        except Exception:
            pass

    try:
        shutil.copy2(src, dst)
        return 'copy'
    except Exception:
        return 'failed'


def _build_entry(
    legacy_path: Path,
    alias_path: Optional[Path],
    rule: OutputAliasRule,
    alias_action: Optional[str],
) -> Dict[str, object]:
    try:
        stat = legacy_path.stat()
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        size = None
        mtime = None

    return {
        'category': rule.category,
        'label': rule.label,
        'order': rule.order,
        'legacy_name': legacy_path.name,
        'legacy_path': str(legacy_path),
        'alias_name': alias_path.name if alias_path else None,
        'alias_path': str(alias_path) if alias_path else None,
        'alias_action': alias_action,
        'size': size,
        'mtime': mtime,
    }
