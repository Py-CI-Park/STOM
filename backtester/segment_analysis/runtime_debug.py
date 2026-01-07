# -*- coding: utf-8 -*-
"""
런타임 검증 로깅 유틸리티

[2026-01-07 신규 추가]
- 목적: exec() 실행 시 변수 값 로깅 및 검증
- 사용: 세그먼트 필터 적용 시 변수 스냅샷 캡처

Usage:
    from backtester.segment_analysis.runtime_debug import (
        RuntimeDebugger,
        create_debug_preamble,
        parse_debug_log,
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

logger = logging.getLogger(__name__)


# =============================================================================
# 디버그 설정
# =============================================================================

@dataclass
class RuntimeDebugConfig:
    """런타임 디버그 설정"""
    enabled: bool = False
    log_path: Optional[str] = None
    log_variables: List[str] = field(default_factory=lambda: [
        '시분초', '시가총액', '현재가', '등락율', '체결강도',
        '매수등락율', '매수체결강도', '필터통과',
        '위험도점수', '거래품질점수', '모멘텀점수',
    ])
    max_entries: int = 1000
    log_on_filter_pass: bool = True
    log_on_filter_fail: bool = False


# 전역 디버그 설정
_DEBUG_CONFIG = RuntimeDebugConfig()
_DEBUG_ENTRIES: List[Dict[str, Any]] = []


def set_runtime_debug_config(config: RuntimeDebugConfig) -> None:
    """런타임 디버그 설정을 변경합니다."""
    global _DEBUG_CONFIG
    _DEBUG_CONFIG = config


def get_runtime_debug_config() -> RuntimeDebugConfig:
    """현재 런타임 디버그 설정을 반환합니다."""
    return _DEBUG_CONFIG


# =============================================================================
# 디버그 로깅 함수
# =============================================================================

def log_runtime_snapshot(
    locals_dict: Dict[str, Any],
    filter_result: bool,
    segment_id: str = '',
    extra_info: Optional[Dict[str, Any]] = None,
) -> None:
    """
    런타임 변수 스냅샷을 로깅합니다.
    
    Args:
        locals_dict: 로컬 변수 딕셔너리 (locals())
        filter_result: 필터통과 결과 (True/False)
        segment_id: 세그먼트 ID
        extra_info: 추가 정보
    """
    if not _DEBUG_CONFIG.enabled:
        return
    
    if filter_result and not _DEBUG_CONFIG.log_on_filter_pass:
        return
    if not filter_result and not _DEBUG_CONFIG.log_on_filter_fail:
        return
    
    if len(_DEBUG_ENTRIES) >= _DEBUG_CONFIG.max_entries:
        return  # 최대 엔트리 초과
    
    entry = {
        'timestamp': datetime.now().isoformat(),
        'segment_id': segment_id,
        'filter_result': filter_result,
        'variables': {},
    }
    
    for var_name in _DEBUG_CONFIG.log_variables:
        if var_name in locals_dict:
            value = locals_dict[var_name]
            # 숫자형만 저장 (메모리 절약)
            if isinstance(value, (int, float, bool)):
                entry['variables'][var_name] = value
            else:
                entry['variables'][var_name] = str(value)[:50]
    
    if extra_info:
        entry['extra'] = extra_info
    
    _DEBUG_ENTRIES.append(entry)


def get_debug_entries() -> List[Dict[str, Any]]:
    """수집된 디버그 엔트리를 반환합니다."""
    return _DEBUG_ENTRIES.copy()


def clear_debug_entries() -> None:
    """디버그 엔트리를 초기화합니다."""
    global _DEBUG_ENTRIES
    _DEBUG_ENTRIES = []


def save_debug_log(output_path: str) -> str:
    """
    디버그 로그를 파일로 저장합니다.
    
    Args:
        output_path: 출력 파일 경로
        
    Returns:
        저장된 파일 경로
    """
    import json
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({
            'config': {
                'enabled': _DEBUG_CONFIG.enabled,
                'log_variables': _DEBUG_CONFIG.log_variables,
            },
            'entries': _DEBUG_ENTRIES,
            'summary': {
                'total_entries': len(_DEBUG_ENTRIES),
                'filter_pass_count': sum(1 for e in _DEBUG_ENTRIES if e.get('filter_result')),
                'filter_fail_count': sum(1 for e in _DEBUG_ENTRIES if not e.get('filter_result')),
            },
        }, f, ensure_ascii=False, indent=2)
    
    return str(path)


# =============================================================================
# 디버그 프리앰블 생성
# =============================================================================

def create_debug_preamble(
    variables_to_log: Optional[List[str]] = None,
    segment_id: str = '',
) -> List[str]:
    """
    exec() 코드에 삽입할 디버그 프리앰블을 생성합니다.
    
    세그먼트 필터 코드 실행 직전에 삽입하여
    변수 상태를 캡처합니다.
    
    Args:
        variables_to_log: 로깅할 변수 목록
        segment_id: 세그먼트 ID
    
    Returns:
        프리앰블 코드 라인 리스트
    """
    variables = variables_to_log or [
        '시분초', '시가총액', '현재가', '등락율', '체결강도',
        '매수등락율', '매수체결강도',
    ]
    
    lines = [
        "",
        "# === Runtime Debug Snapshot ===",
        "try:",
        "    from backtester.segment_analysis.runtime_debug import log_runtime_snapshot, get_runtime_debug_config",
        "    if get_runtime_debug_config().enabled:",
        "        _debug_vars = {}",
    ]
    
    for var in variables:
        lines.append(f"        try: _debug_vars['{var}'] = {var}")
        lines.append(f"        except NameError: pass")
    
    lines.extend([
        f"        log_runtime_snapshot(_debug_vars, 필터통과 if '필터통과' in dir() else False, '{segment_id}')",
        "except Exception:",
        "    pass",
        "# === End Debug Snapshot ===",
        "",
    ])
    
    return lines


# =============================================================================
# 디버그 로그 분석
# =============================================================================

def analyze_debug_log(entries: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    디버그 로그를 분석하여 요약 통계를 반환합니다.
    
    Args:
        entries: 분석할 엔트리 리스트 (None이면 전역 엔트리 사용)
    
    Returns:
        분석 결과 딕셔너리
    """
    entries = entries or _DEBUG_ENTRIES
    
    if not entries:
        return {'error': '디버그 엔트리가 없습니다'}
    
    import numpy as np
    
    result = {
        'total_entries': len(entries),
        'filter_pass_count': 0,
        'filter_fail_count': 0,
        'variable_stats': {},
        'segment_distribution': {},
    }
    
    # 필터 결과 집계
    for entry in entries:
        if entry.get('filter_result'):
            result['filter_pass_count'] += 1
        else:
            result['filter_fail_count'] += 1
        
        # 세그먼트 분포
        seg_id = entry.get('segment_id', 'unknown')
        if seg_id not in result['segment_distribution']:
            result['segment_distribution'][seg_id] = {'pass': 0, 'fail': 0}
        if entry.get('filter_result'):
            result['segment_distribution'][seg_id]['pass'] += 1
        else:
            result['segment_distribution'][seg_id]['fail'] += 1
    
    # 변수별 통계
    all_vars: Set[str] = set()
    for entry in entries:
        all_vars.update(entry.get('variables', {}).keys())
    
    for var in all_vars:
        values = []
        for entry in entries:
            val = entry.get('variables', {}).get(var)
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                values.append(val)
        
        if values:
            arr = np.array(values)
            result['variable_stats'][var] = {
                'count': len(values),
                'mean': float(np.mean(arr)),
                'std': float(np.std(arr)),
                'min': float(np.min(arr)),
                'max': float(np.max(arr)),
            }
    
    return result


def compare_expected_vs_actual(
    expected_filter_count: int,
    entries: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    예상 필터 통과 수와 실제 결과를 비교합니다.
    
    Args:
        expected_filter_count: 예상 필터 통과 거래 수
        entries: 디버그 엔트리 (None이면 전역 사용)
    
    Returns:
        비교 결과
    """
    entries = entries or _DEBUG_ENTRIES
    
    actual_pass_count = sum(1 for e in entries if e.get('filter_result'))
    actual_fail_count = len(entries) - actual_pass_count
    
    diff = actual_pass_count - expected_filter_count
    diff_ratio = diff / expected_filter_count if expected_filter_count > 0 else 0
    
    return {
        'expected': expected_filter_count,
        'actual_pass': actual_pass_count,
        'actual_fail': actual_fail_count,
        'difference': diff,
        'difference_ratio': diff_ratio,
        'is_match': abs(diff_ratio) <= 0.05,  # 5% 허용 오차
        'severity': 'OK' if abs(diff_ratio) <= 0.05 else ('WARN' if abs(diff_ratio) <= 0.2 else 'CRITICAL'),
    }


# =============================================================================
# 편의 함수
# =============================================================================

def enable_runtime_debug(
    log_variables: Optional[List[str]] = None,
    log_path: Optional[str] = None,
    log_on_filter_pass: bool = True,
    log_on_filter_fail: bool = True,
    max_entries: int = 1000,
) -> None:
    """
    런타임 디버그를 활성화합니다.
    
    Usage:
        enable_runtime_debug(log_path='debug_log.json')
        # ... 백테스트 실행 ...
        save_debug_log('debug_log.json')
    """
    global _DEBUG_CONFIG
    _DEBUG_CONFIG = RuntimeDebugConfig(
        enabled=True,
        log_path=log_path,
        log_variables=log_variables or _DEBUG_CONFIG.log_variables,
        log_on_filter_pass=log_on_filter_pass,
        log_on_filter_fail=log_on_filter_fail,
        max_entries=max_entries,
    )
    clear_debug_entries()
    logger.info(f"런타임 디버그 활성화: 변수 {len(_DEBUG_CONFIG.log_variables)}개, 최대 {max_entries}개 엔트리")


def disable_runtime_debug() -> None:
    """런타임 디버그를 비활성화합니다."""
    global _DEBUG_CONFIG
    _DEBUG_CONFIG = RuntimeDebugConfig(enabled=False)
    logger.info("런타임 디버그 비활성화")
