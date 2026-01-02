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

    OutputAliasRule('_detail.csv', '1-1', 'detail', 'basic', 110),
    OutputAliasRule('_summary.csv', '1-2', 'summary_csv', 'basic', 120),
    OutputAliasRule('_analysis.png', '1-3', 'analysis_chart', 'basic', 130),
    OutputAliasRule('_comparison.png', '1-4', 'comparison_chart', 'basic', 140),
    OutputAliasRule('.png', '1-5', 'main_chart', 'basic', 150),
    OutputAliasRule('_.png', '1-6', 'main_chart_summary', 'basic', 160),

    OutputAliasRule('_detail_filtered.csv', '2-1', 'detail_filtered', 'filter', 210),
    OutputAliasRule('_filter.csv', '2-2', 'filter', 'filter', 220),
    OutputAliasRule('_filter_combinations.csv', '2-3', 'filter_combinations', 'filter', 230),
    OutputAliasRule('_filter_stability.csv', '2-4', 'filter_stability', 'filter', 240),
    OutputAliasRule('_filter_lookahead.csv', '2-5', 'filter_lookahead', 'filter', 250),
    OutputAliasRule('_optimal_thresholds.csv', '2-6', 'optimal_thresholds', 'filter', 260),
    OutputAliasRule('_filter_verification.csv', '2-7', 'filter_verification', 'filter', 270),
    OutputAliasRule('_enhanced.png', '2-8', 'enhanced_chart', 'filter', 280),
    OutputAliasRule('_filter_efficiency.png', '2-9', 'filter_efficiency', 'filter', 290),
    OutputAliasRule('_filtered.png', '2-10', 'filtered', 'filter', 300),
    OutputAliasRule('_filtered_.png', '2-11', 'filtered_summary', 'filter', 310),

    OutputAliasRule('_detail_segment.csv', '3-1', 'detail_segment', 'segment', 310),
    OutputAliasRule('_segment_summary.csv', '3-2', 'segment_summary', 'segment', 320),
    OutputAliasRule('_segment_filters.csv', '3-3', 'segment_filters', 'segment', 330),
    OutputAliasRule('_segment_local_combos.csv', '3-4', 'segment_local_combos', 'segment', 340),
    OutputAliasRule('_segment_combos.csv', '3-5', 'segment_combos', 'segment', 350),
    OutputAliasRule('_segment_ranges.csv', '3-6', 'segment_ranges', 'segment', 360),
    OutputAliasRule('_segment_code.txt', '3-7', 'segment_code', 'segment', 370),
    OutputAliasRule('_segment_code_final.txt', '3-8', 'segment_code_final', 'segment', 380),
    OutputAliasRule('_segment_validation.csv', '3-9', 'segment_validation', 'segment', 390),
    OutputAliasRule('_segment_summary_full.txt', '3-10', 'segment_summary_full', 'segment', 400),
    OutputAliasRule('_segment_template_comparison.csv', '3-11', 'segment_template_comparison', 'segment', 410),
    OutputAliasRule('_segment_mode_comparison.csv', '3-12', 'segment_mode_comparison', 'segment', 420),
    OutputAliasRule('_segment_thresholds.csv', '3-13', 'segment_thresholds', 'segment', 430),
    OutputAliasRule('_pareto_front.csv', '3-14', 'pareto_front', 'segment', 440),
    OutputAliasRule('_advanced_optuna.csv', '3-15', 'advanced_optuna', 'segment', 450),
    OutputAliasRule('_nsga2_front.csv', '3-16', 'nsga2_front', 'segment', 460),
    OutputAliasRule('_decision_score.csv', '3-17', 'decision_score', 'segment', 470),
    OutputAliasRule('_segment_verification.csv', '3-18', 'segment_verification', 'segment', 480),
    OutputAliasRule('_segment_heatmap.png', '3-19', 'segment_heatmap', 'segment', 490),
    OutputAliasRule('_segment_filtered.png', '3-20', 'segment_filtered', 'segment', 500),
    OutputAliasRule('_segment_filtered_.png', '3-21', 'segment_filtered_summary', 'segment', 510),
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
    rule = _match_rule_by_suffix(suffix)
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


def _match_rule_by_suffix(suffix: str) -> Optional[OutputAliasRule]:
    for rule in _ALIAS_RULES:
        if rule.suffix == suffix:
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
