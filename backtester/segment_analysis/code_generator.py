# -*- coding: utf-8 -*-
"""
Segment Code Generator

세그먼트별 최적 조합을 조건식 코드로 변환합니다.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

from .segmentation import SegmentConfig
from backtester.output_paths import build_backtesting_output_path


# =============================================================================
# 세그먼트 필터 중복 삽입 방지 헬퍼 함수
# =============================================================================

# 세그먼트 필터 마커 목록 (감지용)
_SEGMENT_FILTER_MARKERS = [
    '# === 세그먼트 필터',           # 세그먼트 필터 블록 시작
    '# 세그먼트 필터 조건식',        # 세그먼트 필터 조건식 주석
    '필터통과 = False',              # 세그먼트 필터 초기화
    '세그먼트 전체 제외',            # 세그먼트 전체 제외 주석
    '매수 = 매수 and 필터통과',      # 세그먼트 필터 반영
    '[대형주_T',                     # 세그먼트 분할 주석
    '[중형주_T',
    '[소형주_T',
    '[초소형주_T',
    '# 최종 매수 조건식_filtered',   # [2026-01-06 추가] 메타데이터 헤더 감지
]

# 세그먼트 필터 블록 시작/끝 마커 (제거용)
# [2026-01-06 버그 수정] 메타데이터 헤더도 제거 대상에 포함
_SEGMENT_BLOCK_START_MARKERS = [
    '# === 세그먼트 필터 (자동 생성) ===',
    '# === Segment filter runtime mapping',
    '# 세그먼트 필터 조건식 (자동 생성)',
    '# 최종 매수 조건식_filtered',   # 메타데이터 헤더 시작
    '# === 매수 조건식 (세그먼트 필터 반영) ===',  # build_segment_final_code 헤더
]

_SEGMENT_BLOCK_END_MARKERS = [
    '# === 세그먼트 필터 반영 ===',
    '매수 = 매수 and 필터통과',
    '매수 = 필터통과',
]


def _has_existing_segment_filter(buy_lines: List[str]) -> bool:
    """
    buy_lines에 이미 세그먼트 필터 코드가 포함되어 있는지 확인합니다.

    [2026-01-06 추가]
    - 목적: 세그먼트 필터 중복 삽입 방지
    - Filter 백테스트 시 기존 필터를 감지하여 교체 로직 적용

    Args:
        buy_lines: 매수 조건식 코드 라인 리스트

    Returns:
        True if segment filter markers are found
    """
    if not buy_lines:
        return False

    text = '\n'.join(buy_lines)
    return any(marker in text for marker in _SEGMENT_FILTER_MARKERS)


def _extract_original_buy_code(buy_lines: List[str]) -> List[str]:
    """
    기존 세그먼트 필터 코드를 제거하고 원본 매수 조건식만 추출합니다.

    [2026-01-06 추가]
    - 목적: 세그먼트 필터 교체 시 원본 코드 추출
    - 세그먼트 필터 블록(시작~끝)을 찾아 제거

    세그먼트 필터 블록 구조:
    ```
    # === 세그먼트 필터 (자동 생성) ===     <- 시작 마커
    # === Segment filter runtime mapping ...
    ... (필터 코드) ...
    # === 세그먼트 필터 반영 ===            <- 끝 마커
    try:
        매수 = 매수 and 필터통과
    except NameError:
        매수 = 필터통과
    ```

    Args:
        buy_lines: 세그먼트 필터가 포함된 매수 조건식 코드 라인 리스트

    Returns:
        세그먼트 필터가 제거된 원본 매수 조건식 코드 라인 리스트
    """
    if not buy_lines:
        return []

    # 세그먼트 필터가 없으면 그대로 반환
    if not _has_existing_segment_filter(buy_lines):
        return buy_lines

    result = []
    in_segment_block = False
    skip_until_empty_or_code = False

    for i, line in enumerate(buy_lines):
        stripped = line.strip()

        # 세그먼트 블록 시작 감지
        if any(marker in stripped for marker in _SEGMENT_BLOCK_START_MARKERS):
            in_segment_block = True
            continue

        # 세그먼트 블록 끝 감지
        if in_segment_block:
            # "매수 = 필터통과" 이후의 빈 줄까지 스킵
            if any(marker in stripped for marker in _SEGMENT_BLOCK_END_MARKERS):
                skip_until_empty_or_code = True
                continue

            if skip_until_empty_or_code:
                # try/except 블록도 스킵
                if stripped.startswith('try:') or stripped.startswith('except') or stripped == '매수 = 필터통과':
                    continue
                # 빈 줄이면 블록 종료
                if not stripped:
                    in_segment_block = False
                    skip_until_empty_or_code = False
                    continue
                # 새로운 코드가 시작되면 블록 종료
                if not stripped.startswith('#') and '=' in stripped:
                    in_segment_block = False
                    skip_until_empty_or_code = False
                    result.append(line)
                    continue

            continue

        # 세그먼트 필터 관련 라인 스킵 (블록 외부)
        if any(marker in stripped for marker in ['# 세그먼트 필터 조건식', '필터통과 = False', '필터통과 = True']):
            # 단독 라인인 경우 스킵
            if stripped == '필터통과 = False' or stripped == '필터통과 = True':
                continue

        # [2026-01-06 버그 수정] 메타데이터 헤더 라인 스킵
        # segment_code_final.txt의 상단 메타데이터 라인들을 제거
        metadata_markers = [
            '# 최종 매수 조건식_filtered',
            '# 생성 시각:',
            '# save_file_name:',
            '# 매수 조건식:',
            '# 매도 조건식:',
            '# 세그먼트 코드:',
            '# 전역 조합:',
            '# 세그먼트 수:',
            '# runtime mapping:',
            '# === 예상 성과',
            '# 원본 거래 수:',
            '# 예상 잔여 거래:',
            '# 예상 개선금액:',
            '# 예상 최종 수익금:',
        ]
        if any(stripped.startswith(marker) for marker in metadata_markers):
            continue

        # 세그먼트 분할 주석 스킵
        if stripped.startswith('# [') and any(seg in stripped for seg in ['대형주_T', '중형주_T', '소형주_T', '초소형주_T']):
            in_segment_block = True
            continue

        # 일반 라인은 결과에 추가
        result.append(line)

    # 연속된 빈 줄 정리
    cleaned = []
    prev_empty = False
    for line in result:
        is_empty = not line.strip()
        if is_empty and prev_empty:
            continue
        cleaned.append(line)
        prev_empty = is_empty

    return cleaned


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
    expected_results: Optional[dict] = None,
) -> Tuple[List[str], Dict[str, int]]:
    """
    매수 조건식 + 세그먼트 필터 조건식을 합쳐 바로 사용할 수 있는 최종 코드 블록 생성.

    Args:
        expected_results: 예상 결과 정보 (선택)
            - total_trades: 원본 거래 수
            - remaining_trades: 예상 잔여 거래 수
            - remaining_ratio: 예상 잔여 비율
            - expected_improvement: 예상 개선금액
            - expected_profit: 예상 최종 수익금
    """
    summary = {
        'segments': int((code_summary or {}).get('segments', 0) or 0),
        'filters': int((code_summary or {}).get('filters', 0) or 0),
        'injected': 0,
    }

    # 예상 결과 정보 추출
    exp = expected_results or {}
    total_trades = exp.get('total_trades', 0)
    remaining_trades = exp.get('remaining_trades', 0)
    remaining_ratio = exp.get('remaining_ratio', 0)
    expected_improvement = exp.get('expected_improvement', 0)
    expected_profit = exp.get('expected_profit', 0)

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
    header.append("# runtime mapping: included (buy-time)")

    # 예상 성과 정보 추가
    if total_trades > 0 or remaining_trades > 0 or expected_improvement != 0:
        header.append("#")
        header.append("# === 예상 성과 (세그먼트 필터 적용 시) ===")
        if total_trades > 0:
            header.append(f"# 원본 거래 수: {total_trades:,}건")
        if remaining_trades > 0:
            ratio_pct = remaining_ratio * 100 if remaining_ratio < 1 else remaining_ratio
            header.append(f"# 예상 잔여 거래: {remaining_trades:,}건 ({ratio_pct:.1f}%)")
        if expected_improvement != 0:
            sign = '+' if expected_improvement > 0 else ''
            header.append(f"# 예상 개선금액: {sign}{int(expected_improvement):,}원")
        if expected_profit != 0:
            sign = '+' if expected_profit > 0 else ''
            header.append(f"# 예상 최종 수익금: {sign}{int(expected_profit):,}원")
        header.append("#")

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
    """
    매수 조건식에 세그먼트 필터를 삽입합니다.

    [2026-01-06 버그 수정] 세그먼트 필터 중복 삽입 방지
    - 기존: buy_lines에 세그먼트 필터가 있어도 무조건 추가 (중복 발생)
    - 수정: 기존 세그먼트 필터가 있으면 먼저 제거 후 새 필터 삽입 (교체)

    동작 방식:
    1. buy_lines에 기존 세그먼트 필터가 있는지 확인
    2. 있으면 _extract_original_buy_code()로 원본 코드 추출
    3. 원본 코드에 새 세그먼트 필터 삽입

    Args:
        buy_lines: 매수 조건식 코드 라인 리스트
        segment_code_lines: 삽입할 세그먼트 필터 코드 라인 리스트

    Returns:
        (합쳐진 코드 라인 리스트, 삽입 성공 여부)
    """
    if not buy_lines:
        return buy_lines, False

    # [2026-01-06 추가] 기존 세그먼트 필터 감지 및 제거 (교체 로직)
    working_lines = buy_lines
    if _has_existing_segment_filter(buy_lines):
        print("[Segment Code Generator] 기존 세그먼트 필터 감지됨 - 제거 후 새 필터로 교체")
        working_lines = _extract_original_buy_code(buy_lines)
        if not working_lines:
            print("[Segment Code Generator] 원본 코드 추출 실패 - 전체 코드 사용")
            working_lines = buy_lines

    # "if 매수:" 라인 찾기
    last_idx = None
    for idx, line in enumerate(working_lines):
        if re.match(r'^\s*if\s+매수\s*:', line):
            last_idx = idx

    if last_idx is None:
        # "if 매수:" 라인이 없으면 끝에 추가 (fallback)
        fallback = list(working_lines)
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

    # 세그먼트 필터 블록 생성
    injected_block = ["", "# === 세그먼트 필터 (자동 생성) ==="]
    injected_block.extend(segment_code_lines)
    injected_block.append("")
    injected_block.append("# === 세그먼트 필터 반영 ===")
    injected_block.append("try:")
    injected_block.append("    매수 = 매수 and 필터통과")
    injected_block.append("except NameError:")
    injected_block.append("    매수 = 필터통과")
    injected_block.append("")

    # "if 매수:" 라인 앞에 세그먼트 필터 삽입
    new_lines = []
    new_lines.extend(working_lines[:last_idx])
    new_lines.extend(injected_block)
    new_lines.extend(working_lines[last_idx:])
    return new_lines, True


def _inject_segment_runtime_preamble(segment_code_lines: List[str], timeframe: str = 'tick') -> List[str]:
    """세그먼트 코드에 런타임 preamble을 주입합니다.
    
    Args:
        segment_code_lines: 세그먼트 코드 라인
        timeframe: 'tick' 또는 'min' (2026-01-07 추가)
    
    Returns:
        런타임 preamble이 주입된 코드 라인
    """
    if not segment_code_lines:
        return segment_code_lines
    marker = "# === Segment filter runtime mapping"
    if any(line.strip().startswith(marker) for line in segment_code_lines):
        return segment_code_lines
    lines: List[str] = []
    used_vars = _extract_segment_used_variables(segment_code_lines)
    lines.extend(_build_segment_runtime_preamble(used_vars, timeframe=timeframe))
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
    seen = set()
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


def _build_segment_runtime_preamble(used_vars: Optional[List[str]] = None, timeframe: str = 'tick') -> List[str]:
    """세그먼트 런타임 preamble을 생성합니다.
    
    Args:
        used_vars: 사용된 변수 목록
        timeframe: 'tick' 또는 'min' (2026-01-07 추가)
    
    Returns:
        런타임 preamble 라인 리스트
    """
    blocks = _get_segment_runtime_blocks(timeframe=timeframe)
    used_vars = used_vars or []
    needed = _resolve_runtime_dependencies(set(used_vars), blocks)

    lines: List[str] = []
    lines.append("# === Segment filter runtime mapping (buy-time) ===")
    lines.extend(_format_var_comment("used vars (segment filter)", used_vars))
    lines.append("# Derived metrics for segment filter evaluation")

    group_headers = {
        "snapshot": "# Snapshot mappings for buy-time columns",
    }
    added_groups = set()
    for block in blocks:
        if not (needed & block["names"]):
            continue
        group = block.get("group")
        if group and group not in added_groups:
            lines.append("")
            lines.append(group_headers.get(group, f"# {group}"))
            added_groups.add(group)
        lines.extend(block["lines"])

    return lines


def _format_var_comment(label: str, values: List[str], chunk_size: int = 6) -> List[str]:
    if not values:
        return [f"# {label}: (none)"]
    lines = []
    chunk: List[str] = []
    for val in values:
        chunk.append(val)
        if len(chunk) >= chunk_size:
            prefix = f"# {label}: " if not lines else "# "
            lines.append(prefix + ", ".join(chunk))
            chunk = []
    if chunk:
        prefix = f"# {label}: " if not lines else "# "
        lines.append(prefix + ", ".join(chunk))
    return lines


def _resolve_runtime_dependencies(
    used: set,
    blocks: List[Dict[str, object]],
) -> set:
    needed = set(used)
    changed = True
    while changed:
        changed = False
        for block in blocks:
            if not (needed & block["names"]):
                continue
            for dep in block["deps"]:
                if dep not in needed:
                    needed.add(dep)
                    changed = True
    return needed


def _get_segment_runtime_blocks(timeframe: str = 'tick') -> List[Dict[str, object]]:
    """세그먼트 분석을 위한 런타임 변수 블록을 생성합니다.
    
    [2026-01-07 개선] 타임프레임별 변수 분리:
    - 틱 모드: 초당매수수량, 초당매도수량, 초당거래대금 사용
    - 분봉 모드: 분당매수수량, 분당매도수량, 분당거래대금 사용
    - 변환 금지: 초당* = 분당*/60 같은 변환은 하지 않음
    
    Args:
        timeframe: 'tick' 또는 'min' (기본값: 'tick')
    
    Returns:
        List of runtime blocks for segment analysis
    """
    blocks: List[Dict[str, object]] = []

    def add_block(names, deps, lines, group=None):
        name_set = {names} if isinstance(names, str) else set(names)
        dep_set = set(deps or [])
        block = {"names": name_set, "deps": dep_set, "lines": list(lines)}
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

    # === 타임프레임별 변수 블록 분기 (2026-01-07) ===
    # [핵심 원칙] 분봉 모드에서는 분당* 변수만 사용, 틱 모드에서는 초당* 변수만 사용
    
    if timeframe == 'tick':
        # === TICK MODE: 초당* 변수 사용 (틱 엔진에서 직접 정의됨) ===
        add_block(
            "초당매수수량",
            [],  # 틱 엔진에서 직접 정의되므로 의존성 없음
            try_assign("초당매수수량", "초당매수수량", "0"),
        )
        add_block(
            "초당매도수량",
            [],
            try_assign("초당매도수량", "초당매도수량", "0"),
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
            "매수초당매수수량",
            ["초당매수수량"],
            ["매수초당매수수량 = 초당매수수량"],
        )
        add_block(
            "매수초당매도수량",
            ["초당매도수량"],
            ["매수초당매도수량 = 초당매도수량"],
        )
        add_block(
            "초당순매수비율",
            ["매수초당매수수량", "매수초당매도수량"],
            [
                "초당순매수비율 = (매수초당매수수량 / (매수초당매수수량 + 매수초당매도수량)) * 100 "
                "if (매수초당매수수량 + 매수초당매도수량) > 0 else 50"
            ],
        )
        add_block(
            "매수초당거래대금",
            [],  # 틱 엔진에서 직접 정의
            try_assign("매수초당거래대금", "초당거래대금", "0"),
        )
    else:
        # === MIN MODE: 분당* 변수 사용 (분봉 엔진에서 직접 정의됨) ===
        # 초당* 변수로의 변환 금지! 분당* 변수를 그대로 사용
        add_block(
            "분당매수수량",
            [],  # 분봉 엔진에서 직접 정의되므로 의존성 없음
            try_assign("분당매수수량", "분당매수수량", "0"),
        )
        add_block(
            "분당매도수량",
            [],
            try_assign("분당매도수량", "분당매도수량", "0"),
        )
        add_block(
            "분당매도_매수_비율",
            ["분당매도수량", "분당매수수량"],
            ["분당매도_매수_비율 = 분당매도수량 / (분당매수수량 + 1e-6)"],
        )
        add_block(
            "분당매수_매도_비율",
            ["분당매수수량", "분당매도수량"],
            ["분당매수_매도_비율 = 분당매수수량 / (분당매도수량 + 1e-6)"],
        )
        add_block(
            "분당순매수수량",
            ["분당매수수량", "분당매도수량"],
            ["분당순매수수량 = 분당매수수량 - 분당매도수량"],
        )
        add_block(
            "분당순매수금액",
            ["분당순매수수량", "현재가"],
            ["분당순매수금액 = 분당순매수수량 * 현재가 / 1_000_000"],
        )
        add_block(
            "매수분당매수수량",
            ["분당매수수량"],
            ["매수분당매수수량 = 분당매수수량"],
        )
        add_block(
            "매수분당매도수량",
            ["분당매도수량"],
            ["매수분당매도수량 = 분당매도수량"],
        )
        add_block(
            "분당순매수비율",
            ["매수분당매수수량", "매수분당매도수량"],
            [
                "분당순매수비율 = (매수분당매수수량 / (매수분당매수수량 + 매수분당매도수량)) * 100 "
                "if (매수분당매수수량 + 매수분당매도수량) > 0 else 50"
            ],
        )
        add_block(
            "매수분당거래대금",
            [],  # 분봉 엔진에서 직접 정의
            try_assign("매수분당거래대금", "분당거래대금", "0"),
        )
    add_block(
        "매수스프레드",
        ["매도호가1", "매수호가1"],
        ["매수스프레드 = ((매도호가1 - 매수호가1) / 매수호가1) * 100 if 매수호가1 > 0 else 0"],
    )
    add_block(
        "매수호가잔량비",
        ["매수총잔량", "매도총잔량"],
        ["매수호가잔량비 = (매수총잔량 / (매도총잔량 + 1e-6)) * 100"],
    )
    add_block(
        "매도호가잔량비",
        ["매도총잔량", "매수총잔량"],
        ["매도호가잔량비 = (매도총잔량 / (매수총잔량 + 1e-6)) * 100"],
    )
    add_block(
        "매수변동폭",
        ["고가", "저가"],
        ["매수변동폭 = 고가 - 저가"],
    )
    add_block(
        "매수변동폭비율",
        ["고가", "저가"],
        ["매수변동폭비율 = ((고가 - 저가) / 저가) * 100 if 저가 > 0 else 0"],
    )
    add_block(
        "현재가_고저범위_위치",
        ["현재가", "고가", "저가"],
        ["현재가_고저범위_위치 = (현재가 - 저가) / (고가 - 저가 + 1e-6) * 100"],
    )
    
    # 타임프레임별 매수수량_매도총잔량_비율 블록 (2026-01-07)
    if timeframe == 'tick':
        add_block(
            "초당매수수량_매도총잔량_비율",
            ["초당매수수량", "매도총잔량"],
            ["초당매수수량_매도총잔량_비율 = (초당매수수량 / (매도총잔량 + 1e-6)) * 100"],
        )
    else:
        add_block(
            "분당매수수량_매도총잔량_비율",
            ["분당매수수량", "매도총잔량"],
            ["분당매수수량_매도총잔량_비율 = (분당매수수량 / (매도총잔량 + 1e-6)) * 100"],
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

    add_block("매수매수호가1", ["매수호가1"], ["매수매수호가1 = 매수호가1"], group="snapshot")
    add_block("매수매도호가1", ["매도호가1"], ["매수매도호가1 = 매도호가1"], group="snapshot")
    add_block("매수매수총잔량", ["매수총잔량"], ["매수매수총잔량 = 매수총잔량"], group="snapshot")
    add_block("매수매도총잔량", ["매도총잔량"], ["매수매도총잔량 = 매도총잔량"], group="snapshot")
    add_block("매수전일비", ["전일비"], ["매수전일비 = 전일비"], group="snapshot")
    add_block("매수전일동시간비", ["전일동시간비"], ["매수전일동시간비 = 전일동시간비"], group="snapshot")
    add_block("매수체결강도", ["체결강도"], ["매수체결강도 = 체결강도"], group="snapshot")
    add_block("매수등락율", ["등락율"], ["매수등락율 = 등락율"], group="snapshot")
    add_block("매수시가등락율", ["시가등락율"], ["매수시가등락율 = 시가등락율"], group="snapshot")
    add_block("매수회전율", ["회전율"], ["매수회전율 = 회전율"], group="snapshot")
    add_block("매수당일거래대금", ["당일거래대금"], ["매수당일거래대금 = 당일거래대금"], group="snapshot")
    add_block("매수고가", ["고가"], ["매수고가 = 고가"], group="snapshot")
    add_block("매수저가", ["저가"], ["매수저가 = 저가"], group="snapshot")
    add_block("매수고저평균대비등락율", ["고저평균대비등락율"], ["매수고저평균대비등락율 = 고저평균대비등락율"], group="snapshot")
    add_block("매수시가", ["시가"], ["매수시가 = 시가"], group="snapshot")
    
    # 타임프레임별 거래대금_당일비중 블록 (2026-01-07)
    if timeframe == 'tick':
        add_block(
            "매수초당거래대금_당일비중",
            ["매수초당거래대금", "매수당일거래대금"],
            [
                "매수초당거래대금_당일비중 = (매수초당거래대금 / (매수당일거래대금 + 1e-6)) * 10000 "
                "if 매수당일거래대금 > 0 else 0"
            ],
            group="snapshot",
        )
        add_block(
            "초당거래대금_당일비중",
            ["매수초당거래대금_당일비중"],
            ["초당거래대금_당일비중 = 매수초당거래대금_당일비중"],
            group="snapshot",
        )
    else:
        add_block(
            "매수분당거래대금_당일비중",
            ["매수분당거래대금", "매수당일거래대금"],
            [
                "매수분당거래대금_당일비중 = (매수분당거래대금 / (매수당일거래대금 + 1e-6)) * 10000 "
                "if 매수당일거래대금 > 0 else 0"
            ],
            group="snapshot",
        )
        add_block(
            "분당거래대금_당일비중",
            ["매수분당거래대금_당일비중"],
            ["분당거래대금_당일비중 = 매수분당거래대금_당일비중"],
            group="snapshot",
        )
    
    add_block("매수가", ["현재가"], ["매수가 = 현재가"], group="snapshot")
    add_block(
        "매수금액",
        ["현재가", "매수수량"],
        try_assign("매수금액", "현재가 * 매수수량", "0"),
        group="snapshot",
    )
    
    # 타임프레임별 매수수량_매도총잔량_비율 snapshot 블록 (2026-01-07)
    if timeframe == 'tick':
        add_block(
            "매수초당매수수량_매수매도총잔량_비율",
            ["매수초당매수수량", "매수매도총잔량"],
            ["매수초당매수수량_매수매도총잔량_비율 = (매수초당매수수량 / (매수매도총잔량 + 1e-6)) * 100"],
            group="snapshot",
        )
    else:
        add_block(
            "매수분당매수수량_매수매도총잔량_비율",
            ["매수분당매수수량", "매수매도총잔량"],
            ["매수분당매수수량_매수매도총잔량_비율 = (매수분당매수수량 / (매수매도총잔량 + 1e-6)) * 100"],
            group="snapshot",
        )
    add_block(
        "매수매도총잔량_매수매수총잔량_비율",
        ["매수매도총잔량", "매수매수총잔량"],
        ["매수매도총잔량_매수매수총잔량_비율 = (매수매도총잔량 / 매수매수총잔량) if 매수매수총잔량 > 0 else 0"],
        group="snapshot",
    )
    add_block(
        "매수매수총잔량_매수매도총잔량_비율",
        ["매수매수총잔량", "매수매도총잔량"],
        ["매수매수총잔량_매수매도총잔량_비율 = (매수매수총잔량 / 매수매도총잔량) if 매수매도총잔량 > 0 else 0"],
        group="snapshot",
    )
    add_block(
        "매도잔량_매수잔량_비율",
        ["매수매도총잔량_매수매수총잔량_비율"],
        ["매도잔량_매수잔량_비율 = 매수매도총잔량_매수매수총잔량_비율"],
        group="snapshot",
    )
    add_block(
        "매수잔량_매도잔량_비율",
        ["매수매수총잔량_매수매도총잔량_비율"],
        ["매수잔량_매도잔량_비율 = 매수매수총잔량_매수매도총잔량_비율"],
        group="snapshot",
    )
    add_block(
        ["매수시", "매수분", "매수초", "매수시간"],
        ["시분초"],
        [
            "try:",
            "    _t = 시분초",
            "    매수시 = _t // 10000",
            "    매수분 = (_t // 100) % 100",
            "    매수초 = _t % 100",
            "    매수시간 = _t",
            "except NameError:",
            "    매수시 = 0",
            "    매수분 = 0",
            "    매수초 = 0",
            "    매수시간 = 0",
        ],
    )
    add_block(
        "매수일자",
        [],
        [
            "try:",
            "    _index_val = str(self.index)",
            "    매수일자 = int(_index_val[:8]) if len(_index_val) >= 8 else 0",
            "except (NameError, AttributeError):",
            "    매수일자 = 0",
        ],
    )
    add_block(
        "거래품질점수",
        ["매수체결강도", "매수호가잔량비", "시가총액", "매수등락율", "매수스프레드"],
        [
            "",
            "# Trade quality score (approx, buy-time only)",
            "거래품질점수 = 50",
            "if 매수체결강도 >= 120: 거래품질점수 += 10",
            "if 매수체결강도 >= 150: 거래품질점수 += 10",
            "if 매수호가잔량비 >= 100: 거래품질점수 += 10",
            "if 시가총액 >= 1000 and 시가총액 <= 10000: 거래품질점수 += 10",
            "if 매수등락율 >= 25: 거래품질점수 -= 15",
            "if 매수등락율 >= 30: 거래품질점수 -= 10",
            "if 매수스프레드 >= 0.5: 거래품질점수 -= 10",
            "거래품질점수 = max(0, min(100, 거래품질점수))",
        ],
    )
    add_block(
        ["위험도점수", "매수매도위험도점수"],
        [
            "매수등락율", "매수체결강도", "매수당일거래대금", "시가총액",
            "매수호가잔량비", "매수스프레드", "매수회전율", "매수변동폭비율",
        ],
        [
            "",
            "# Risk score (approx, buy-time only)",
            "위험도점수 = 0",
            "if 매수등락율 >= 20: 위험도점수 += 20",
            "if 매수등락율 >= 25: 위험도점수 += 10",
            "if 매수등락율 >= 30: 위험도점수 += 10",
            "if 매수체결강도 < 80: 위험도점수 += 15",
            "if 매수체결강도 < 60: 위험도점수 += 10",
            "if 매수체결강도 >= 150: 위험도점수 += 10",
            "if 매수체결강도 >= 200: 위험도점수 += 10",
            "if 매수체결강도 >= 250: 위험도점수 += 10",
            "if 매수당일거래대금 / 100 < 50: 위험도점수 += 15",
            "if 매수당일거래대금 / 100 < 100: 위험도점수 += 10",
            "if 시가총액 < 1000: 위험도점수 += 15",
            "if 시가총액 < 5000: 위험도점수 += 10",
            "if 매수호가잔량비 < 90: 위험도점수 += 10",
            "if 매수호가잔량비 < 70: 위험도점수 += 15",
            "if 매수스프레드 >= 0.5: 위험도점수 += 10",
            "if 매수스프레드 >= 1.0: 위험도점수 += 10",
            "if 매수회전율 < 10: 위험도점수 += 5",
            "if 매수회전율 < 5: 위험도점수 += 10",
            "if 매수변동폭비율 >= 7.5: 위험도점수 += 10",
            "if 매수변동폭비율 >= 10: 위험도점수 += 10",
            "if 매수변동폭비율 >= 15: 위험도점수 += 10",
            "위험도점수 = min(100, 위험도점수)",
            "매수매도위험도점수 = 위험도점수",
        ],
    )
    add_block(
        "모멘텀점수",
        ["매수등락율", "매수체결강도"],
        [
            "",
            "# Momentum score (approx using fixed scales)",
            "try:",
            "    _등락율_norm = 매수등락율 / 10",
            "except NameError:",
            "    _등락율_norm = 0",
            "try:",
            "    _체결강도_norm = (매수체결강도 - 100) / 50",
            "except NameError:",
            "    _체결강도_norm = 0",
            "모멘텀점수 = round((_등락율_norm * 0.4 + _체결강도_norm * 0.6) * 10, 2)",
        ],
    )

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
    try:
        v = float(value)
    except Exception:
        return str(value)

    if v.is_integer():
        return str(int(v))

    text = format(v, ".17g")
    if text == "-0":
        text = "0"
    return text


def _split_segment_id(segment_id: str) -> Tuple[str, str]:
    if '_' not in segment_id:
        return segment_id, ''
    cap_label, time_label = segment_id.split('_', 1)
    return cap_label, time_label


# =============================================================================
# 일반 필터 조건식 생성 함수 (2026-01-06 추가)
# =============================================================================

def _detect_timeframe_from_name(name: str) -> str:
    """파일명에서 타임프레임을 감지합니다.
    
    Args:
        name: 파일명 또는 전략명
    
    Returns:
        'tick' 또는 'min'
    """
    if not name:
        return 'tick'
    name_lower = name.lower()
    if 'tick' in name_lower or '_t_' in name_lower:
        return 'tick'
    elif 'min' in name_lower or '_m_' in name_lower:
        return 'min'
    return 'tick'  # 기본값


def build_filter_final_code(
    buystg_text: Optional[str],
    sellstg_text: Optional[str],
    generated_code: Optional[dict],
    buystg_name: Optional[str] = None,
    sellstg_name: Optional[str] = None,
    save_file_name: Optional[str] = None,
    timeframe: Optional[str] = None,
) -> Tuple[List[str], Dict[str, int]]:
    """
    매수 조건식 + 일반 필터 조건식을 합쳐 바로 사용할 수 있는 최종 코드 블록 생성.

    [2026-01-06 추가]
    - segment_code_final.txt와 유사한 형태로 filter_code_final.txt 생성
    - GenerateFilterCode()의 결과를 매수 조건식에 통합
    - runtime mapping 포함 (모멘텀점수, 위험도점수 등 파생 변수 정의)
    
    [2026-01-07 개선]
    - timeframe 파라미터 추가: 분봉 모드에서는 분당* 변수 직접 사용

    Args:
        buystg_text: 원본 매수 조건식 코드
        sellstg_text: 원본 매도 조건식 코드
        generated_code: GenerateFilterCode()의 반환값
        buystg_name: 매수 조건식 이름
        sellstg_name: 매도 조건식 이름
        save_file_name: 저장 파일명 (헤더용)
        timeframe: 'tick' 또는 'min' (None이면 save_file_name에서 자동 감지)

    Returns:
        (최종 코드 라인 리스트, 요약 정보)
    """
    summary = {
        'total_filters': 0,
        'total_improvement': 0,
        'injected': 0,
    }
    
    # 타임프레임 감지 (2026-01-07)
    if timeframe is None:
        timeframe = _detect_timeframe_from_name(save_file_name or '')

    if not isinstance(generated_code, dict):
        return [], summary

    buy_conditions = generated_code.get('buy_conditions') or []
    individual_conditions = generated_code.get('individual_conditions') or []
    combine_steps = generated_code.get('combine_steps') or []
    code_summary = generated_code.get('summary') or {}

    if not buy_conditions:
        return [], summary

    summary['total_filters'] = len(individual_conditions)
    summary['total_improvement'] = int(code_summary.get('total_improvement_combined', 0) or 0)

    # 필터 조건에서 사용된 변수 추출
    filter_code_lines = []
    for cond in individual_conditions:
        filter_code = cond.get('조건코드', '')
        if filter_code:
            filter_code_lines.append(filter_code)
    used_vars = _extract_segment_used_variables(filter_code_lines)

    # 헤더 생성
    header = []
    header.append("# 최종 매수 조건식_filtered (일반 필터 반영)")
    header.append(f"# 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if save_file_name:
        header.append(f"# save_file_name: {save_file_name}")
    if buystg_name:
        header.append(f"# 매수 조건식: {buystg_name}")
    if sellstg_name:
        header.append(f"# 매도 조건식: {sellstg_name}")
    header.append(f"# 필터 수: {summary['total_filters']}")
    header.append(f"# 예상 개선금액: {summary['total_improvement']:,}원")
    header.append("# runtime mapping: included (buy-time)")
    header.append("")

    # 필터 요약 정보
    header.append("# === 적용된 필터 목록 ===")
    for i, cond in enumerate(individual_conditions, 1):
        header.append(f"# {i}. {cond.get('필터명', 'N/A')}: 개선 {cond.get('수익개선', 0):,}원, 제외 {cond.get('제외율', 0)}%")
    header.append("")

    # 조합 단계 정보
    if combine_steps:
        header.append("# === 필터 조합 단계 ===")
        for step in combine_steps:
            header.append(f"# {step.get('순서', '')}. {step.get('필터명', '')}: "
                         f"+{step.get('추가개선(중복반영)', 0):,}원 → 누적 {step.get('누적수익금', 0):,}원")
        header.append("")

    # 매수 조건식 처리
    buy_lines = _normalize_code_lines(buystg_text)
    sell_lines = _normalize_code_lines(sellstg_text)

    # Runtime mapping 생성 (필터에서 사용된 파생 변수 정의)
    # 타임프레임별로 올바른 변수 블록 사용 (2026-01-07)
    runtime_preamble = _build_segment_runtime_preamble(used_vars, timeframe=timeframe)

    # 필터 조건 블록 생성
    filter_block = []
    filter_block.append("")
    filter_block.append("# === 일반 필터 (자동 생성) ===")
    filter_block.append("# 각 필터는 '해당 조건이면 매수하지 않음(제외)'을 의미합니다.")
    filter_block.append("# 여러 필터를 함께 쓴다는 것은: (필터1 통과) AND (필터2 통과) AND ... 입니다.")
    filter_block.append("")

    # Runtime mapping 추가 (파생 변수 정의)
    if runtime_preamble:
        filter_block.extend(runtime_preamble)
        filter_block.append("")

    for cond in individual_conditions:
        filter_name = cond.get('필터명', 'N/A')
        filter_code = cond.get('조건코드', '')
        improvement = cond.get('수익개선', 0)
        exclusion = cond.get('제외율', 0)

        filter_block.append(f"# [{filter_name}] 개선: {improvement:,}원, 제외: {exclusion}%")
        if filter_code:
            # not (조건) 형태로 변환 - 조건에 해당하면 제외
            filter_block.append(f"if {filter_code}:")
            filter_block.append(f"    매수 = False")
        filter_block.append("")

    filter_block.append("# === 일반 필터 반영 완료 ===")
    filter_block.append("")

    # "if 매수:" 라인 찾기 및 필터 삽입
    last_idx = None
    for idx, line in enumerate(buy_lines):
        if re.match(r'^\s*if\s+매수\s*:', line):
            last_idx = idx

    if last_idx is None:
        # "if 매수:" 라인이 없으면 끝에 추가
        combined_buy = list(buy_lines)
        combined_buy.extend(filter_block)
        summary['injected'] = 0
    else:
        # "if 매수:" 라인 앞에 필터 삽입
        combined_buy = []
        combined_buy.extend(buy_lines[:last_idx])
        combined_buy.extend(filter_block)
        combined_buy.extend(buy_lines[last_idx:])
        summary['injected'] = 1

    # 최종 라인 조합
    lines = []
    lines.extend(header)
    lines.append("# === 매수 조건식 (일반 필터 반영) ===")
    lines.extend(combined_buy)

    if sell_lines:
        lines.append("")
        lines.append("# === 매도 조건식 (원본 유지) ===")
        lines.extend(sell_lines)

    lines.append("")
    lines.append("# 일반 필터가 적용된 최종 조건식 파일입니다.")
    lines.append("# 세그먼트 필터와 함께 사용하려면 segment_code_final.txt를 참조하세요.")

    return lines, summary


def save_filter_code_final(code_lines: List[str], output_dir: str, prefix: str) -> Optional[str]:
    """
    일반 필터 최종 조건식 파일을 저장합니다.

    [2026-01-06 추가]
    - segment_code_final.txt와 유사한 형태로 filter_code_final.txt 저장

    Args:
        code_lines: 조건식 코드 라인 리스트
        output_dir: 출력 디렉토리
        prefix: 파일명 접두사

    Returns:
        저장된 파일 경로 또는 None
    """
    if not code_lines:
        return None
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    code_path = build_backtesting_output_path(prefix, "_filter_code_final.txt", output_dir=path)
    code_path.write_text("\n".join(code_lines), encoding='utf-8-sig')
    return str(code_path)
