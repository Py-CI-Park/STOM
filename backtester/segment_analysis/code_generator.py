# -*- coding: utf-8 -*-
"""
Segment Code Generator

세그먼트별 최적 조합을 조건식 코드로 변환합니다.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple, Any, Set

from .segmentation import SegmentConfig
from backtester.output_paths import build_backtesting_output_path


def build_segment_filter_code(
    global_best: Optional[dict],
    seg_config: Optional[SegmentConfig] = None,
    runtime_market_cap_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    runtime_time_ranges: Optional[Dict[str, Tuple[int, int]]] = None,
) -> Tuple[List[str], Dict[str, int]]:
    if not isinstance(global_best, dict):
        return [], {}

    combo_map = global_best.get('combination')
    if not isinstance(combo_map, dict) or not combo_map:
        return [], {}

    seg_config = seg_config or SegmentConfig()
    cap_ranges = runtime_market_cap_ranges or seg_config.market_cap_ranges
    time_ranges = runtime_time_ranges or seg_config.time_ranges

    lines: List[str] = []
    lines.append("# 세그먼트 필터 조건식 (자동 생성)")
    lines.append("# 시분초는 매수시간(HHMMSS) 기준으로 계산 필요")
    lines.append("필터통과 = False")
    lines.append("")

    total_filters = 0
    total_segments = 0

    for i, seg_id in enumerate(sorted(combo_map.keys())):
        combo = combo_map.get(seg_id) or {}
        filters = combo.get('filters') or []

        total_segments += 1
        total_filters += len(filters)

        seg_condition = _build_segment_condition(seg_id, cap_ranges, time_ranges)

        # [2025-12-31 버그 수정] 세그먼트 필터 OR 논리 → 상호 배타적 처리
        # - 기존: 모든 세그먼트가 "if"로 시작 → OR 논리 (60% 통과)
        # - 수정: 첫 번째는 "if", 나머지는 "elif" → 각 거래는 하나의 세그먼트만 적용 (27% 통과)
        if_keyword = "if" if i == 0 else "elif"

        lines.append(f"# [{seg_id}]")
        if seg_condition:
            lines.append(f"{if_keyword} {seg_condition}:")
        else:
            lines.append(f"{if_keyword} True:")

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
    code_path = build_backtesting_output_path(prefix, "_segment_code.txt", output_dir=path)
    code_path.write_text("\n".join(code_lines), encoding='utf-8-sig')
    return str(code_path)


def save_segment_code_final(code_lines: List[str], output_dir: str, prefix: str) -> Optional[str]:
    if not code_lines:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    code_path = build_backtesting_output_path(prefix, "_segment_code_final.txt", output_dir=path)
    code_path.write_text("\n".join(code_lines), encoding='utf-8-sig')
    return str(code_path)


def build_segment_final_code(
    buystg_text: Optional[str],
    sellstg_text: Optional[str],
    segment_code_lines: List[str],
    buystg_name: Optional[str] = None,
    sellstg_name: Optional[str] = None,
    segment_code_path: Optional[str] = None,
    global_combo_path: Optional[str] = None,
    code_summary: Optional[dict] = None,
    save_file_name: Optional[str] = None,
    segment_results: Optional[dict] = None,
) -> Tuple[List[str], Dict[str, int]]:
    """
    매수 조건식 + 세그먼트 필터 조건식을 합쳐 바로 사용할 수 있는 최종 코드 블록 생성.
    """
    summary = {
        'segments': int((code_summary or {}).get('segments', 0) or 0),
        'filters': int((code_summary or {}).get('filters', 0) or 0),
        'injected': 0,
    }

    header = []
    header.append("# 최종 매수 조건식_filtered (세그먼트 필터 반영)")
    header.append(f"# 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if save_file_name:
        header.append(f"# save_file_name: {save_file_name}")
    if buystg_name:
        header.append(f"# 매수 조건식: {buystg_name}")
    if sellstg_name:
        header.append(f"# 매도 조건식: {sellstg_name}")
    if segment_code_path:
        header.append(f"# 세그먼트 코드: {segment_code_path}")
    if global_combo_path:
        header.append(f"# 전역 조합: {global_combo_path}")
    if summary['segments'] or summary['filters']:
        header.append(f"# 세그먼트 수: {summary['segments']} / 필터 수: {summary['filters']}")
    
    # 세그먼트 결과 정보 추가
    if segment_results:
        header.append("#")
        header.append("# === 예상 세그먼트 결과 ===")
        if 'total_improvement' in segment_results:
            improvement = segment_results['total_improvement']
            header.append(f"# 개선금액: {improvement:,.0f}원")
        if 'remaining_trades' in segment_results:
            count = segment_results['remaining_trades']
            header.append(f"# 잔여 거래수: {count:,}건")
        if 'remaining_ratio' in segment_results:
            ratio = segment_results['remaining_ratio']
            ratio_pct = ratio * 100 if ratio <= 1 else ratio
            header.append(f"# 잔여 비율: {ratio_pct:.1f}%")
        if 'validation_score' in segment_results:
            vscore = segment_results['validation_score']
            header.append(f"# validation_score: {vscore:.3f}")
        if 'mdd_pct' in segment_results:
            mdd_pct = segment_results['mdd_pct']
            mdd_pct = mdd_pct * 100 if mdd_pct <= 1 else mdd_pct
            header.append(f"# 예상 MDD: {mdd_pct:.2f}%")
        if 'profit_volatility' in segment_results:
            pvol = segment_results['profit_volatility']
            header.append(f"# 수익 변동성: {pvol:.3f}")
        if 'return_volatility' in segment_results:
            rvol = segment_results['return_volatility']
            header.append(f"# 수익률 변동성: {rvol:.3f}")
        if 'total_profit' in segment_results:
            profit = segment_results['total_profit']
            header.append(f"# 예상 총 수익: {profit:,.0f}원")
        if 'trade_count' in segment_results:
            count = segment_results['trade_count']
            header.append(f"# 예상 거래 수: {count:,}건")
        if 'win_rate' in segment_results:
            win_rate = segment_results['win_rate']
            header.append(f"# 예상 승률: {win_rate:.1f}%")
        if 'avg_profit_per_trade' in segment_results:
            avg = segment_results['avg_profit_per_trade']
            header.append(f"# 평균 수익/거래: {avg:,.0f}원")
        if 'pass_rate' in segment_results:
            pass_rate = segment_results['pass_rate']
            header.append(f"# 필터 통과율: {pass_rate:.1f}%")

    header.append("# runtime mapping: included (buy-time)")
    header.append("")

    buy_lines = _normalize_code_lines(buystg_text)
    sell_lines = _normalize_code_lines(sellstg_text)

    segment_runtime_lines = _inject_segment_runtime_preamble(segment_code_lines)
    combined_buy, injected = _inject_segment_filter_into_buy_lines(
        buy_lines,
        segment_runtime_lines,
    )
    summary['injected'] = 1 if injected else 0

    lines = []
    lines.extend(header)
    if combined_buy:
        lines.append("# === 매수 조건식 (세그먼트 필터 반영) ===")
        lines.extend(combined_buy)
    else:
        lines.append("# [경고] 원본 매수 조건식을 찾을 수 없습니다.")
        lines.append("# 아래 세그먼트 필터 코드를 매수 조건식과 함께 사용하세요.")
        lines.extend(segment_code_lines)

    if sell_lines:
        lines.append("")
        lines.append("# === 매도 조건식 (원본 유지) ===")
        lines.extend(sell_lines)

    lines.append("")
    lines.append("# 최종 작성 업데이트 된 조건식 파일입니다.")
    return lines, summary


def _normalize_code_lines(code_text: Optional[str]) -> List[str]:
    if not code_text:
        return []
    if isinstance(code_text, str):
        return code_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return [str(code_text)]


def _inject_segment_filter_into_buy_lines(
    buy_lines: List[str],
    segment_code_lines: List[str],
) -> Tuple[List[str], bool]:
    if not buy_lines:
        return buy_lines, False

    last_idx = None
    for idx, line in enumerate(buy_lines):
        if re.match(r'^\s*if\s+매수\s*:', line):
            last_idx = idx

    if last_idx is None:
        fallback = list(buy_lines)
        fallback.append("")
        fallback.append("# === 세그먼트 필터 (자동 생성) ===")
        fallback.extend(segment_code_lines)
        fallback.append("")
        fallback.append("# === 세그먼트 필터 반영 ===")
        fallback.append("try:")
        fallback.append("    매수 = 매수 and 필터통과")
        fallback.append("except NameError:")
        fallback.append("    매수 = 필터통과")
        return fallback, False

    injected_block = ["", "# === 세그먼트 필터 (자동 생성) ==="]
    injected_block.extend(segment_code_lines)
    injected_block.append("")
    injected_block.append("# === 세그먼트 필터 반영 ===")
    injected_block.append("try:")
    injected_block.append("    매수 = 매수 and 필터통과")
    injected_block.append("except NameError:")
    injected_block.append("    매수 = 필터통과")
    injected_block.append("")

    new_lines = []
    new_lines.extend(buy_lines[:last_idx])
    new_lines.extend(injected_block)
    new_lines.extend(buy_lines[last_idx:])
    return new_lines, True


def _inject_segment_runtime_preamble(segment_code_lines: List[str]) -> List[str]:
    if not segment_code_lines:
        return segment_code_lines
    marker = "# === Segment filter runtime mapping"
    if any(line.strip().startswith(marker) for line in segment_code_lines):
        return segment_code_lines
    lines: List[str] = []
    used_vars = _extract_segment_used_variables(segment_code_lines)
    lines.extend(_build_segment_runtime_preamble(used_vars))
    lines.append("")
    lines.extend(segment_code_lines)
    return lines


_SEGMENT_FILTER_TOKEN_RE = re.compile(r"[A-Za-z_가-힣][A-Za-z0-9_가-힣]*")
_SEGMENT_FILTER_KEYWORDS = {
    "if", "elif", "else", "and", "or", "not", "True", "False", "None",
    "try", "except", "in", "is", "self", "필터통과",
}
_SEGMENT_FILTER_IGNORE = {"e"}


def _extract_segment_used_variables(segment_code_lines: List[str]) -> List[str]:
    used: List[str] = []
    seen: Set[str] = set()
    for line in segment_code_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for token in _SEGMENT_FILTER_TOKEN_RE.findall(line):
            if token in _SEGMENT_FILTER_KEYWORDS or token in _SEGMENT_FILTER_IGNORE:
                continue
            if token[0].isdigit():
                continue
            if token in seen:
                continue
            seen.add(token)
            used.append(token)
    return used


def _build_segment_runtime_preamble(used_vars: Optional[List[str]] = None) -> List[str]:
    blocks = _get_segment_runtime_blocks()
    used_vars = used_vars or []
    needed = _resolve_runtime_dependencies(set(used_vars), blocks)

    lines: List[str] = []
    lines.append("# === Segment filter runtime mapping (buy-time) ===")
    lines.extend(_format_var_comment("used vars (segment filter)", used_vars))
    lines.append("# Derived metrics for segment filter evaluation")

    group_headers = {
        "snapshot": "# Snapshot mappings for buy-time columns",
    }
    added_groups: Set[str] = set()
    for block in blocks:
        block_names = block.get("names", set())
        if not isinstance(block_names, set):
            block_names = set()
        if not (needed & block_names):
            continue
        group = block.get("group")
        if group and group not in added_groups:
            lines.append("")
            lines.append(group_headers.get(group, f"# {group}"))
            added_groups.add(group)
        block_lines = block.get("lines", [])
        if isinstance(block_lines, list):
            lines.extend(block_lines)

    return lines


def _format_var_comment(label: str, values: List[str], chunk_size: int = 6) -> List[str]:
    if not values:
        return [f"# {label}: (none)"]
    lines = []
    lines.append(f"# {label} (총 {len(values)}개):")
    
    # 변수를 번호와 함께 나열
    for idx, val in enumerate(values, 1):
        lines.append(f"# 변수 {idx}: {val}")
    
    return lines


def _resolve_runtime_dependencies(
    used: Set[str],
    blocks: List[Dict[str, Any]],
) -> Set[str]:
    needed: Set[str] = set(used)
    changed = True
    while changed:
        changed = False
        for block in blocks:
            block_names = block.get("names", set())
            block_deps = block.get("deps", set())
            if not isinstance(block_names, set):
                block_names = set()
            if not isinstance(block_deps, set):
                block_deps = set()
            if not (needed & block_names):
                continue
            for dep in block_deps:
                if dep not in needed:
                    needed.add(dep)
                    changed = True
    return needed


def _get_segment_runtime_blocks() -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []

    def add_block(names: Any, deps: Any, lines: Any, group: Optional[str] = None) -> None:
        name_set: Set[str] = {names} if isinstance(names, str) else set(names)
        dep_set: Set[str] = set(deps or [])
        block: Dict[str, Any] = {"names": name_set, "deps": dep_set, "lines": list(lines)}
        if group:
            block["group"] = group
        blocks.append(block)

    def try_assign(name: str, expr: str, fallback: str, except_clause: str = "except NameError:") -> List[str]:
        return [
            "try:",
            f"    {name} = {expr}",
            except_clause,
            f"    {name} = {fallback}",
        ]

    # 초당/분당 매핑: 초당 값이 없으면 분당 값 사용 (스케일 변환 없음)
    add_block(
        "초당매수수량",
        ["분당매수수량"],
        [
            "try:",
            "    초당매수수량",
            "except NameError:",
            "    try:",
            "        초당매수수량 = 분당매수수량",
            "    except NameError:",
            "        초당매수수량 = 0",
        ],
    )
    add_block(
        "초당매도수량",
        ["분당매도수량"],
        [
            "try:",
            "    초당매도수량",
            "except NameError:",
            "    try:",
            "        초당매도수량 = 분당매도수량",
            "    except NameError:",
            "        초당매도수량 = 0",
        ],
    )
    add_block(
        "초당매도_매수_비율",
        ["초당매도수량", "초당매수수량"],
        ["초당매도_매수_비율 = 초당매도수량 / (초당매수수량 + 1e-6)"],
    )
    add_block(
        "초당매수_매도_비율",
        ["초당매수수량", "초당매도수량"],
        ["초당매수_매도_비율 = 초당매수수량 / (초당매도수량 + 1e-6)"],
    )
    add_block(
        "B_초당매도_매수_비율",
        ["초당매도_매수_비율"],
        ["B_초당매도_매수_비율 = 초당매도_매수_비율"],
    )
    add_block(
        "B_초당매수_매도_비율",
        ["초당매수_매도_비율"],
        ["B_초당매수_매도_비율 = 초당매수_매도_비율"],
    )
    add_block(
        "분당매도_매수_비율",
        ["초당매도_매수_비율"],
        ["분당매도_매수_비율 = 초당매도_매수_비율"],
    )
    add_block(
        "분당매수_매도_비율",
        ["초당매수_매도_비율"],
        ["분당매수_매도_비율 = 초당매수_매도_비율"],
    )
    add_block(
        "B_분당매도_매수_비율",
        ["분당매도_매수_비율"],
        ["B_분당매도_매수_비율 = 분당매도_매수_비율"],
    )
    add_block(
        "B_분당매수_매도_비율",
        ["분당매수_매도_비율"],
        ["B_분당매수_매도_비율 = 분당매수_매도_비율"],
    )
    add_block(
        "초당순매수수량",
        ["초당매수수량", "초당매도수량"],
        ["초당순매수수량 = 초당매수수량 - 초당매도수량"],
    )
    add_block(
        "초당순매수금액",
        ["초당순매수수량", "현재가"],
        ["초당순매수금액 = 초당순매수수량 * 현재가 / 1_000_000"],
    )
    add_block(
        "B_초당매수수량",
        ["초당매수수량"],
        ["B_초당매수수량 = 초당매수수량"],
    )
    add_block(
        "B_초당매도수량",
        ["초당매도수량"],
        ["B_초당매도수량 = 초당매도수량"],
    )
    add_block(
        "B_분당매수수량",
        ["분당매수수량", "초당매수수량"],
        [
            "try:",
            "    B_분당매수수량 = 분당매수수량",
            "except NameError:",
            "    try:",
            "        B_분당매수수량 = 초당매수수량",
            "    except NameError:",
            "        B_분당매수수량 = 0",
        ],
    )
    add_block(
        "B_분당매도수량",
        ["분당매도수량", "초당매도수량"],
        [
            "try:",
            "    B_분당매도수량 = 분당매도수량",
            "except NameError:",
            "    try:",
            "        B_분당매도수량 = 초당매도수량",
            "    except NameError:",
            "        B_분당매도수량 = 0",
        ],
    )
    add_block(
        "초당순매수비율",
        ["B_초당매수수량", "B_초당매도수량"],
        [
            "초당순매수비율 = (B_초당매수수량 / (B_초당매수수량 + B_초당매도수량)) * 100 "
            "if (B_초당매수수량 + B_초당매도수량) > 0 else 50"
        ],
    )
    add_block(
        "B_초당순매수수량",
        ["초당순매수수량"],
        ["B_초당순매수수량 = 초당순매수수량"],
    )
    add_block(
        "B_초당순매수금액",
        ["초당순매수금액"],
        ["B_초당순매수금액 = 초당순매수금액"],
    )
    add_block(
        "B_초당순매수비율",
        ["초당순매수비율"],
        ["B_초당순매수비율 = 초당순매수비율"],
    )
    add_block(
        "분당순매수수량",
        ["초당순매수수량"],
        ["분당순매수수량 = 초당순매수수량"],
    )
    add_block(
        "분당순매수금액",
        ["초당순매수금액"],
        ["분당순매수금액 = 초당순매수금액"],
    )
    add_block(
        "분당순매수비율",
        ["초당순매수비율"],
        ["분당순매수비율 = 초당순매수비율"],
    )
    add_block(
        "B_분당순매수수량",
        ["분당순매수수량"],
        ["B_분당순매수수량 = 분당순매수수량"],
    )
    add_block(
        "B_분당순매수금액",
        ["분당순매수금액"],
        ["B_분당순매수금액 = 분당순매수금액"],
    )
    add_block(
        "B_분당순매수비율",
        ["분당순매수비율"],
        ["B_분당순매수비율 = 분당순매수비율"],
    )
    # 초당/분당 거래대금 매핑 (초당 값이 없으면 분당 값 사용)
    add_block(
        "B_초당거래대금",
        ["초당거래대금", "분당거래대금"],
        [
            "try:",
            "    B_초당거래대금 = 초당거래대금",
            "except NameError:",
            "    try:",
            "        B_초당거래대금 = 분당거래대금",
            "    except NameError:",
            "        B_초당거래대금 = 0",
        ],
    )
    add_block(
        "B_스프레드",
        ["매도호가1", "매수호가1"],
        ["B_스프레드 = ((매도호가1 - 매수호가1) / 매수호가1) * 100 if 매수호가1 > 0 else 0"],
    )
    add_block(
        "B_호가잔량비",
        ["매수총잔량", "매도총잔량"],
        ["B_호가잔량비 = (매수총잔량 / (매도총잔량 + 1e-6)) * 100"],
    )
    add_block(
        "매도호가잔량비",
        ["매도총잔량", "매수총잔량"],
        ["매도호가잔량비 = (매도총잔량 / (매수총잔량 + 1e-6)) * 100"],
    )
    add_block(
        "B_변동폭",
        ["고가", "저가"],
        ["B_변동폭 = 고가 - 저가"],
    )
    add_block(
        "B_변동폭비율",
        ["고가", "저가"],
        ["B_변동폭비율 = ((고가 - 저가) / 저가) * 100 if 저가 > 0 else 0"],
    )
    add_block(
        "현재가_고저범위_위치",
        ["현재가", "고가", "저가"],
        ["현재가_고저범위_위치 = (현재가 - 저가) / (고가 - 저가 + 1e-6) * 100"],
    )
    add_block(
        "B_현재가_고저범위_위치",
        ["현재가_고저범위_위치"],
        ["B_현재가_고저범위_위치 = 현재가_고저범위_위치"],
    )
    add_block(
        "초당매수수량_매도총잔량_비율",
        ["초당매수수량", "매도총잔량"],
        ["초당매수수량_매도총잔량_비율 = (초당매수수량 / (매도총잔량 + 1e-6)) * 100"],
    )
    add_block(
        "B_초당매수수량_매도총잔량_비율",
        ["초당매수수량_매도총잔량_비율"],
        ["B_초당매수수량_매도총잔량_비율 = 초당매수수량_매도총잔량_비율"],
    )
    add_block(
        "분당매수수량_매도총잔량_비율",
        ["초당매수수량_매도총잔량_비율"],
        ["분당매수수량_매도총잔량_비율 = 초당매수수량_매도총잔량_비율"],
    )
    add_block(
        "B_분당매수수량_매도총잔량_비율",
        ["분당매수수량_매도총잔량_비율"],
        ["B_분당매수수량_매도총잔량_비율 = 분당매수수량_매도총잔량_비율"],
    )
    add_block(
        "당일거래대금_전틱분봉_비율",
        ["당일거래대금"],
        [
            "try:",
            "    _prev_trade = 당일거래대금N(1)",
            "    당일거래대금_전틱분봉_비율 = 당일거래대금 / (_prev_trade + 1e-6) if _prev_trade > 0 else 0.0",
            "except (NameError, TypeError):",
            "    당일거래대금_전틱분봉_비율 = 0.0",
        ],
    )
    add_block(
        "당일거래대금_5틱분봉평균_비율",
        ["당일거래대금"],
        [
            "try:",
            "    _trade_avg = (당일거래대금 + 당일거래대금N(1) + 당일거래대금N(2) + 당일거래대금N(3) + 당일거래대금N(4)) / 5",
            "    당일거래대금_5틱분봉평균_비율 = 당일거래대금 / (_trade_avg + 1e-6) if _trade_avg > 0 else 0.0",
            "except (NameError, TypeError):",
            "    당일거래대금_5틱분봉평균_비율 = 0.0",
        ],
    )

    # Snapshot mappings with B_ prefix
    add_block("B_매수호가1", ["매수호가1"], ["B_매수호가1 = 매수호가1"], group="snapshot")
    add_block("B_매도호가1", ["매도호가1"], ["B_매도호가1 = 매도호가1"], group="snapshot")
    add_block("B_매수총잔량", ["매수총잔량"], ["B_매수총잔량 = 매수총잔량"], group="snapshot")
    add_block("B_매도총잔량", ["매도총잔량"], ["B_매도총잔량 = 매도총잔량"], group="snapshot")
    add_block("B_전일비", ["전일비"], ["B_전일비 = 전일비"], group="snapshot")
    add_block("B_전일동시간비", ["전일동시간비"], ["B_전일동시간비 = 전일동시간비"], group="snapshot")
    add_block("B_체결강도", ["체결강도"], ["B_체결강도 = 체결강도"], group="snapshot")
    add_block("B_등락율", ["등락율"], ["B_등락율 = 등락율"], group="snapshot")
    add_block("B_시가등락율", ["시가등락율"], ["B_시가등락율 = 시가등락율"], group="snapshot")
    add_block("B_회전율", ["회전율"], ["B_회전율 = 회전율"], group="snapshot")
    add_block("B_당일거래대금", ["당일거래대금"], ["B_당일거래대금 = 당일거래대금"], group="snapshot")
    add_block("B_고가", ["고가"], ["B_고가 = 고가"], group="snapshot")
    add_block("B_저가", ["저가"], ["B_저가 = 저가"], group="snapshot")
    add_block("B_고저평균대비등락율", ["고저평균대비등락율"], ["B_고저평균대비등락율 = 고저평균대비등락율"], group="snapshot")
    add_block("B_시가", ["시가"], ["B_시가 = 시가"], group="snapshot")
    add_block(
        "B_초당거래대금_당일비중",
        ["B_초당거래대금", "B_당일거래대금"],
        [
            "B_초당거래대금_당일비중 = (B_초당거래대금 / (B_당일거래대금 + 1e-6)) * 10000 "
            "if B_당일거래대금 > 0 else 0"
        ],
        group="snapshot",
    )
    add_block(
        "초당거래대금_당일비중",
        ["B_초당거래대금_당일비중"],
        ["초당거래대금_당일비중 = B_초당거래대금_당일비중"],
        group="snapshot",
    )
    add_block(
        "분당거래대금_당일비중",
        ["초당거래대금_당일비중"],
        ["분당거래대금_당일비중 = 초당거래대금_당일비중"],
        group="snapshot",
    )
    add_block(
        "B_분당거래대금_당일비중",
        ["분당거래대금_당일비중"],
        ["B_분당거래대금_당일비중 = 분당거래대금_당일비중"],
        group="snapshot",
    )
    add_block("B_가", ["현재가"], ["B_가 = 현재가"], group="snapshot")
    add_block(
        "B_매수금액",
        ["현재가", "매수수량"],
        try_assign("B_매수금액", "현재가 * 매수수량", "0"),
        group="snapshot",
    )
    add_block(
        "B_초당매수수량_B_매도총잔량_비율",
        ["B_초당매수수량", "B_매도총잔량"],
        ["B_초당매수수량_B_매도총잔량_비율 = (B_초당매수수량 / (B_매도총잔량 + 1e-6)) * 100"],
        group="snapshot",
    )
    add_block(
        "B_매도총잔량_B_매수총잔량_비율",
        ["B_매도총잔량", "B_매수총잔량"],
        ["B_매도총잔량_B_매수총잔량_비율 = (B_매도총잔량 / B_매수총잔량) if B_매수총잔량 > 0 else 0"],
        group="snapshot",
    )
    add_block(
        "B_매수총잔량_B_매도총잔량_비율",
        ["B_매수총잔량", "B_매도총잔량"],
        ["B_매수총잔량_B_매도총잔량_비율 = (B_매수총잔량 / B_매도총잔량) if B_매도총잔량 > 0 else 0"],
        group="snapshot",
    )
    add_block(
        "매도잔량_매수잔량_비율",
        ["B_매도총잔량_B_매수총잔량_비율"],
        ["매도잔량_매수잔량_비율 = B_매도총잔량_B_매수총잔량_비율"],
        group="snapshot",
    )
    add_block(
        "매수잔량_매도잔량_비율",
        ["B_매수총잔량_B_매도총잔량_비율"],
        ["매수잔량_매도잔량_비율 = B_매수총잔량_B_매도총잔량_비율"],
        group="snapshot",
    )
    add_block(
        ["B_시", "B_분", "B_초", "B_시간"],
        ["시분초"],
        [
            "try:",
            "    _t = 시분초",
            "    B_시 = _t // 10000",
            "    B_분 = (_t // 100) % 100",
            "    B_초 = _t % 100",
            "    B_시간 = _t",
            "except NameError:",
            "    B_시 = 0",
            "    B_분 = 0",
            "    B_초 = 0",
            "    B_시간 = 0",
        ],
    )
    add_block(
        "B_일자",
        [],
        [
            "try:",
            "    _index_val = str(self.index)",
            "    B_일자 = int(_index_val[:8]) if len(_index_val) >= 8 else 0",
            "except (NameError, AttributeError):",
            "    B_일자 = 0",
        ],
    )
    add_block(
        "거래품질점수",
        ["B_체결강도", "B_호가잔량비", "시가총액", "B_등락율", "B_스프레드"],
        [
            "",
            "# Trade quality score (approx, buy-time only)",
            "거래품질점수 = 50",
            "if B_체결강도 >= 120: 거래품질점수 += 10",
            "if B_체결강도 >= 150: 거래품질점수 += 10",
            "if B_호가잔량비 >= 100: 거래품질점수 += 10",
            "if 시가총액 >= 1000 and 시가총액 <= 10000: 거래품질점수 += 10",
            "if B_등락율 >= 25: 거래품질점수 -= 15",
            "if B_등락율 >= 30: 거래품질점수 -= 10",
            "if B_스프레드 >= 0.5: 거래품질점수 -= 10",
            "거래품질점수 = max(0, min(100, 거래품질점수))",
        ],
    )
    add_block(
        ["위험도점수", "B_위험도점수"],
        [
            "B_등락율", "B_체결강도", "B_당일거래대금", "시가총액",
            "B_호가잔량비", "B_스프레드", "B_회전율", "B_변동폭비율",
        ],
        [
            "",
            "# Risk score (approx, buy-time only)",
            "위험도점수 = 0",
            "if B_등락율 >= 20: 위험도점수 += 20",
            "if B_등락율 >= 25: 위험도점수 += 10",
            "if B_등락율 >= 30: 위험도점수 += 10",
            "if B_체결강도 < 80: 위험도점수 += 15",
            "if B_체결강도 < 60: 위험도점수 += 10",
            "if B_체결강도 >= 150: 위험도점수 += 10",
            "if B_체결강도 >= 200: 위험도점수 += 10",
            "if B_체결강도 >= 250: 위험도점수 += 10",
            "if B_당일거래대금 / 100 < 50: 위험도점수 += 15",
            "if B_당일거래대금 / 100 < 100: 위험도점수 += 10",
            "if 시가총액 < 1000: 위험도점수 += 15",
            "if 시가총액 < 5000: 위험도점수 += 10",
            "if B_호가잔량비 < 90: 위험도점수 += 10",
            "if B_호가잔량비 < 70: 위험도점수 += 15",
            "if B_스프레드 >= 0.5: 위험도점수 += 10",
            "if B_스프레드 >= 1.0: 위험도점수 += 10",
            "if B_회전율 < 10: 위험도점수 += 5",
            "if B_회전율 < 5: 위험도점수 += 10",
            "if B_변동폭비율 >= 7.5: 위험도점수 += 10",
            "if B_변동폭비율 >= 10: 위험도점수 += 10",
            "if B_변동폭비율 >= 15: 위험도점수 += 10",
            "위험도점수 = min(100, 위험도점수)",
            "B_위험도점수 = 위험도점수",
        ],
    )
    add_block(
        "모멘텀점수",
        ["B_등락율", "B_체결강도"],
        [
            "",
            "# Momentum score (approx using fixed scales)",
            "try:",
            "    _등락율_norm = B_등락율 / 10",
            "except NameError:",
            "    _등락율_norm = 0",
            "try:",
            "    _체결강도_norm = (B_체결강도 - 100) / 50",
            "except NameError:",
            "    _체결강도_norm = 0",
            "모멘텀점수 = round((_등락율_norm * 0.4 + _체결강도_norm * 0.6) * 10, 2)",
        ],
    )

    # 하위 호환성을 위한 매수 prefix 변수 (B_ 접두사로 대체)
    add_block("매수스프레드", ["B_스프레드"], ["매수스프레드 = B_스프레드"], group="snapshot")
    add_block("매수호가잔량비", ["B_호가잔량비"], ["매수호가잔량비 = B_호가잔량비"], group="snapshot")
    add_block("매수변동폭", ["B_변동폭"], ["매수변동폭 = B_변동폭"], group="snapshot")
    add_block("매수변동폭비율", ["B_변동폭비율"], ["매수변동폭비율 = B_변동폭비율"], group="snapshot")
    add_block("매수초당거래대금", ["B_초당거래대금"], ["매수초당거래대금 = B_초당거래대금"], group="snapshot")
    add_block("매수초당매수수량", ["B_초당매수수량"], ["매수초당매수수량 = B_초당매수수량"], group="snapshot")
    add_block("매수초당매도수량", ["B_초당매도수량"], ["매수초당매도수량 = B_초당매도수량"], group="snapshot")
    add_block("매수매수호가1", ["B_매수호가1"], ["매수매수호가1 = B_매수호가1"], group="snapshot")
    add_block("매수매도호가1", ["B_매도호가1"], ["매수매도호가1 = B_매도호가1"], group="snapshot")
    add_block("매수매수총잔량", ["B_매수총잔량"], ["매수매수총잔량 = B_매수총잔량"], group="snapshot")
    add_block("매수매도총잔량", ["B_매도총잔량"], ["매수매도총잔량 = B_매도총잔량"], group="snapshot")
    add_block("매수전일비", ["B_전일비"], ["매수전일비 = B_전일비"], group="snapshot")
    add_block("매수전일동시간비", ["B_전일동시간비"], ["매수전일동시간비 = B_전일동시간비"], group="snapshot")
    add_block("매수체결강도", ["B_체결강도"], ["매수체결강도 = B_체결강도"], group="snapshot")
    add_block("매수등락율", ["B_등락율"], ["매수등락율 = B_등락율"], group="snapshot")
    add_block("매수시가등락율", ["B_시가등락율"], ["매수시가등락율 = B_시가등락율"], group="snapshot")
    add_block("매수회전율", ["B_회전율"], ["매수회전율 = B_회전율"], group="snapshot")
    add_block("매수당일거래대금", ["B_당일거래대금"], ["매수당일거래대금 = B_당일거래대금"], group="snapshot")
    add_block("매수고가", ["B_고가"], ["매수고가 = B_고가"], group="snapshot")
    add_block("매수저가", ["B_저가"], ["매수저가 = B_저가"], group="snapshot")
    add_block("매수고저평균대비등락율", ["B_고저평균대비등락율"], ["매수고저평균대비등락율 = B_고저평균대비등락율"], group="snapshot")
    add_block("매수시가", ["B_시가"], ["매수시가 = B_시가"], group="snapshot")
    add_block("매수가", ["B_가"], ["매수가 = B_가"], group="snapshot")
    add_block("매수금액", ["B_매수금액"], ["매수금액 = B_매수금액"], group="snapshot")
    add_block("매수시", ["B_시"], ["매수시 = B_시"], group="snapshot")
    add_block("매수분", ["B_분"], ["매수분 = B_분"], group="snapshot")
    add_block("매수초", ["B_초"], ["매수초 = B_초"], group="snapshot")
    add_block("매수시간", ["B_시간"], ["매수시간 = B_시간"], group="snapshot")
    add_block("매수일자", ["B_일자"], ["매수일자 = B_일자"], group="snapshot")
    add_block("매수매도위험도점수", ["B_매수매도위험도점수"], ["매수매도위험도점수 = B_매수매도위험도점수"], group="snapshot")

    return blocks


def _build_segment_condition(
    seg_id: str,
    cap_ranges: Dict[str, Tuple[float, float]],
    time_ranges: Dict[str, Tuple[int, int]],
) -> Optional[str]:
    if not seg_id or seg_id == 'Out_of_Range':
        return None

    cap_label, time_label = _split_segment_id(seg_id)
    cap_range = cap_ranges.get(cap_label)
    time_range = time_ranges.get(time_label)
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
    """
    소수점을 최대 4자리로 제한하여 반환.
    """
    try:
        v = float(value)
    except Exception:
        return str(value)

    if v.is_integer():
        return str(int(v))

    # 소수점 4자리로 제한 (끝의 0은 제거)
    text = format(round(v, 4), ".4f").rstrip('0').rstrip('.')
    if text == "-0":
        text = "0"
    return text


def _split_segment_id(segment_id: str) -> Tuple[str, str]:
    if '_' not in segment_id:
        return segment_id, ''
    cap_label, time_label = segment_id.split('_', 1)
    return cap_label, time_label
