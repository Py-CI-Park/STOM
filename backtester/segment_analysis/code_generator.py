# -*- coding: utf-8 -*-
"""
Segment Code Generator

세그먼트별 최적 조합을 조건식 코드로 변환합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .segmentation import SegmentConfig


def build_segment_filter_code(
    global_best: Optional[dict],
    seg_config: Optional[SegmentConfig] = None,
) -> Tuple[List[str], Dict[str, int]]:
    if not isinstance(global_best, dict):
        return [], {}

    combo_map = global_best.get('combination')
    if not isinstance(combo_map, dict) or not combo_map:
        return [], {}

    seg_config = seg_config or SegmentConfig()

    lines: List[str] = []
    lines.append("# 세그먼트 필터 조건식 (자동 생성)")
    lines.append("# 시분초는 매수시간(HHMMSS) 기준으로 계산 필요")
    lines.append("필터통과 = False")
    lines.append("")

    total_filters = 0
    total_segments = 0

    for seg_id in sorted(combo_map.keys()):
        combo = combo_map.get(seg_id) or {}
        filters = combo.get('filters') or []

        total_segments += 1
        total_filters += len(filters)

        seg_condition = _build_segment_condition(seg_id, seg_config)
        lines.append(f"# [{seg_id}]")
        if seg_condition:
            lines.append(f"if {seg_condition}:")
        else:
            lines.append("if True:")

        if combo.get('exclude_segment'):
            lines.append("    필터통과 = False  # 세그먼트 전체 제외")
            lines.append("")
            continue

        if filters:
            conditions = []
            for flt in filters:
                cond = _build_filter_condition(flt)
                if cond:
                    conditions.append(cond)

            if conditions:
                lines.append("    if (" + " and ".join(conditions) + "):")
                lines.append("        필터통과 = True")
            else:
                lines.append("    필터통과 = True")
        else:
            lines.append("    필터통과 = True  # 필터 없음")

        lines.append("")

    summary = {
        'segments': total_segments,
        'filters': total_filters,
    }
    return lines, summary


def save_segment_code(code_lines: List[str], output_dir: str, prefix: str) -> Optional[str]:
    if not code_lines:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    code_path = path / f"{prefix}_segment_code.txt"
    code_path.write_text("\n".join(code_lines), encoding='utf-8-sig')
    return str(code_path)


def _build_segment_condition(seg_id: str, config: SegmentConfig) -> Optional[str]:
    if not seg_id or seg_id == 'Out_of_Range':
        return None

    cap_label, time_label = _split_segment_id(seg_id)
    cap_range = config.market_cap_ranges.get(cap_label)
    time_range = config.time_ranges.get(time_label)
    if not cap_range or not time_range:
        return None

    cap_min, cap_max = cap_range
    time_min, time_max = time_range

    cap_cond = _build_range_condition('시가총액', cap_min, cap_max)
    time_cond = _build_range_condition('시분초', time_min, time_max)
    if not cap_cond or not time_cond:
        return None

    return f"({cap_cond} and {time_cond})"


def _build_filter_condition(candidate: dict) -> Optional[str]:
    if not isinstance(candidate, dict):
        return None
    column = candidate.get('column')
    threshold = candidate.get('threshold')
    direction = candidate.get('direction')
    if not column or threshold is None or direction not in ('less', 'greater'):
        return None

    op = ">=" if direction == 'less' else "<"
    value_text = _format_value(threshold)
    return f"({column} {op} {value_text})"


def _build_range_condition(name: str, min_value: float, max_value: float) -> Optional[str]:
    if max_value == float('inf'):
        return f"{name} >= {_format_value(min_value)}"
    return f"{name} >= {_format_value(min_value)} and {name} < {_format_value(max_value)}"


def _format_value(value: float) -> str:
    try:
        v = float(value)
    except Exception:
        return str(value)

    if v.is_integer():
        return str(int(v))

    if abs(v) >= 100:
        text = f"{v:.2f}"
    elif abs(v) >= 1:
        text = f"{v:.4f}"
    else:
        text = f"{v:.6f}"

    return text.rstrip('0').rstrip('.')


def _split_segment_id(segment_id: str) -> Tuple[str, str]:
    if '_' not in segment_id:
        return segment_id, ''
    cap_label, time_label = segment_id.split('_', 1)
    return cap_label, time_label
