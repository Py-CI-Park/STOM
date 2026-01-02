# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import json
import re
import shutil


@dataclass(frozen=True)
class OutputAliasRule:
    suffix: str
    prefix: str
    label: str
    category: str
    order: int


_ALIAS_RULES: List[OutputAliasRule] = [
    OutputAliasRule('_manifest.json', '0-0', 'manifest', 'summary', 5),
    OutputAliasRule('_report.txt', '0-1', 'report', 'summary', 10),
    OutputAliasRule('_condition_study.md', '0-2', 'condition_study', 'summary', 20),

    OutputAliasRule('_summary.csv', '1-1', 'summary_csv', 'basic', 110),
    OutputAliasRule('_detail.csv', '1-2', 'detail', 'basic', 120),
    OutputAliasRule('.png', '1-21', 'main_chart', 'basic', 1210),
    OutputAliasRule('_.png', '1-22', 'main_chart_summary', 'basic', 1220),
    OutputAliasRule('_analysis.png', '1-23', 'analysis_chart', 'basic', 1230),
    OutputAliasRule('_comparison.png', '1-24', 'comparison_chart', 'basic', 1240),

    OutputAliasRule('_filter.csv', '2-1', 'filter', 'filter', 210),
    OutputAliasRule('_detail_filtered.csv', '2-2', 'detail_filtered', 'filter', 220),
    OutputAliasRule('_filter_combinations.csv', '2-3', 'filter_combinations', 'filter', 230),
    OutputAliasRule('_filter_stability.csv', '2-4', 'filter_stability', 'filter', 240),
    OutputAliasRule('_filter_lookahead.csv', '2-5', 'filter_lookahead', 'filter', 250),
    OutputAliasRule('_optimal_thresholds.csv', '2-6', 'optimal_thresholds', 'filter', 260),
    OutputAliasRule('_filter_verification.csv', '2-7', 'filter_verification', 'filter', 270),
    OutputAliasRule('_enhanced.png', '2-21', 'enhanced_chart', 'filter', 2210),
    OutputAliasRule('_filter_efficiency.png', '2-22', 'filter_efficiency', 'filter', 2220),
    OutputAliasRule('_filtered.png', '2-23', 'filtered', 'filter', 2230),
    OutputAliasRule('_filtered_.png', '2-24', 'filtered_summary', 'filter', 2240),

    OutputAliasRule('_segment_summary.csv', '3-1', 'segment_summary', 'segment', 310),
    OutputAliasRule('_segment_summary_full.txt', '3-2', 'segment_summary_full', 'segment', 320),
    OutputAliasRule('_detail_segment.csv', '3-3', 'detail_segment', 'segment', 330),
    OutputAliasRule('_segment_filters.csv', '3-4', 'segment_filters', 'segment', 340),
    OutputAliasRule('_segment_combos.csv', '3-5', 'segment_combos', 'segment', 350),
    OutputAliasRule('_segment_ranges.csv', '3-6', 'segment_ranges', 'segment', 360),
    OutputAliasRule('_segment_code.txt', '3-7', 'segment_code', 'segment', 370),
    OutputAliasRule('_segment_code_final.txt', '3-8', 'segment_code_final', 'segment', 380),
    OutputAliasRule('_segment_validation.csv', '3-9', 'segment_validation', 'segment', 390),
    OutputAliasRule('_segment_verification.csv', '3-10', 'segment_verification', 'segment', 400),
    OutputAliasRule('_segment_local_combos.csv', '3-11', 'segment_local_combos', 'segment', 3110),
    OutputAliasRule('_segment_template_comparison.csv', '3-12', 'segment_template_comparison', 'segment', 3120),
    OutputAliasRule('_segment_mode_comparison.csv', '3-13', 'segment_mode_comparison', 'segment', 3130),
    OutputAliasRule('_segment_thresholds.csv', '3-14', 'segment_thresholds', 'segment', 3140),
    OutputAliasRule('_pareto_front.csv', '3-15', 'pareto_front', 'segment', 3150),
    OutputAliasRule('_advanced_optuna.csv', '3-16', 'advanced_optuna', 'segment', 3160),
    OutputAliasRule('_nsga2_front.csv', '3-17', 'nsga2_front', 'segment', 3170),
    OutputAliasRule('_decision_score.csv', '3-18', 'decision_score', 'segment', 3180),
    OutputAliasRule('_segment_heatmap.png', '3-21', 'segment_heatmap', 'segment', 3210),
    OutputAliasRule('_segment_filtered.png', '3-22', 'segment_filtered', 'segment', 3220),
    OutputAliasRule('_segment_filtered_.png', '3-23', 'segment_filtered_summary', 'segment', 3230),
]

_TEMPLATE_RULES: List[OutputAliasRule] = [
    OutputAliasRule('_segment_summary.csv', '3-51', 'segment_summary', 'segment', 3510),
    OutputAliasRule('_segment_filters.csv', '3-52', 'segment_filters', 'segment', 3520),
    OutputAliasRule('_segment_combos.csv', '3-53', 'segment_combos', 'segment', 3530),
    OutputAliasRule('_segment_ranges.csv', '3-54', 'segment_ranges', 'segment', 3540),
    OutputAliasRule('_segment_code.txt', '3-55', 'segment_code', 'segment', 3550),
    OutputAliasRule('_segment_local_combos.csv', '3-56', 'segment_local_combos', 'segment', 3560),
    OutputAliasRule('_segment_thresholds.csv', '3-57', 'segment_thresholds', 'segment', 3570),
]


def build_output_manifest(
    output_dir: Path,
    save_file_name: str,
    *,
    enable_alias: bool = True,
    alias_mode: str = 'hardlink',
    alias_dir: Optional[str] = None,
    cleanup_legacy: bool = False,
) -> Optional[Path]:
    output_dir = Path(output_dir)
    if not output_dir.exists() or not save_file_name:
        return None

    entries = []
    alias_root = output_dir / alias_dir if alias_dir else output_dir
    for file_path in list(output_dir.iterdir()):
        if not file_path.is_file():
            continue
        rule = _match_rule(file_path.name, save_file_name)
        if rule is None:
            continue

        new_name = f"{rule.prefix}_{save_file_name}{rule.suffix}"
        alias_path = alias_root / new_name
        alias_action = None
        if enable_alias:
            alias_action = _ensure_alias(file_path, alias_path, alias_mode)

        legacy_deleted = False
        if cleanup_legacy and enable_alias:
            if alias_path.exists():
                try:
                    if alias_path.resolve() != file_path.resolve():
                        file_path.unlink()
                        legacy_deleted = True
                except Exception:
                    legacy_deleted = False

        entries.append(_build_entry(
            file_path,
            alias_path if enable_alias else None,
            rule,
            alias_action,
            legacy_deleted,
        ))

    entries.sort(key=lambda x: (x.get('order', 0), x.get('legacy_name', '')))

    manifest = {
        'save_file_name': save_file_name,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'alias_mode': alias_mode,
        'alias_enabled': bool(enable_alias),
        'alias_dir': alias_dir,
        'cleanup_legacy': bool(cleanup_legacy),
        'entries': entries,
    }

    manifest_path = build_numbered_path(output_dir, save_file_name, "_manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8-sig')
    return manifest_path


def build_numbered_filename(prefix: str, suffix: str) -> str:
    rules = _TEMPLATE_RULES if _is_template_prefix(prefix) else _ALIAS_RULES
    rule = _match_rule_by_suffix(suffix, rules=rules)
    if rule is None:
        return f"{prefix}{suffix}"
    return f"{rule.prefix}_{prefix}{rule.suffix}"


def build_numbered_path(output_dir: Path, prefix: str, suffix: str) -> Path:
    return Path(output_dir) / build_numbered_filename(prefix, suffix)


def strip_numeric_prefix(name: str) -> str:
    return re.sub(r"^\d[\d-]*_", "", name or "")


def resolve_alias_for_legacy_path(
    legacy_path: Path | str,
    alias_dir: Optional[str] = None,
) -> Optional[Path]:
    try:
        legacy = Path(legacy_path)
    except Exception:
        return None

    if not legacy.name:
        return None
    output_dir = legacy.parent
    save_file_name = output_dir.name
    rule = _match_rule(legacy.name, save_file_name)
    if rule is None:
        return None

    alias_root = output_dir / alias_dir if alias_dir else output_dir
    alias_path = alias_root / f"{rule.prefix}_{save_file_name}{rule.suffix}"
    if alias_path.exists():
        return alias_path
    return None


def _match_rule(filename: str, save_file_name: str) -> Optional[OutputAliasRule]:
    if filename == save_file_name:
        return None
    for rule in _ALIAS_RULES:
        if filename == f"{save_file_name}{rule.suffix}":
            return rule
        if filename == f"{rule.prefix}_{save_file_name}{rule.suffix}":
            return rule
    return None


def _match_rule_by_suffix(suffix: str, *, rules: Optional[Iterable[OutputAliasRule]] = None) -> Optional[OutputAliasRule]:
    rule_list = list(rules) if rules is not None else _ALIAS_RULES
    for rule in rule_list:
        if rule.suffix == suffix:
            return rule
    return None


def _is_template_prefix(prefix: str) -> bool:
    return '_tmpl_' in (prefix or '')


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
    legacy_deleted: bool,
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
        'legacy_deleted': legacy_deleted,
        'size': size,
        'mtime': mtime,
    }
