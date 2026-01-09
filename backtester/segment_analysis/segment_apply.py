# -*- coding: utf-8 -*-
"""
세그먼트 필터 적용 모듈

[2026-01-07 개선]
- 필터 적용 전 내부 검증 기능 추가
- 누락 변수 상세 로깅
- 예측-실제 불일치 진단 기능

이 모듈은 세그먼트 분석 결과(global_best)를 DataFrame에 적용하여
필터 통과 마스크를 생성합니다.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .segmentation import SegmentBuilder, SegmentConfig

# 로거 설정
logger = logging.getLogger(__name__)


def load_segment_config_from_ranges(global_best: dict) -> SegmentConfig:
    """
    global_best에 저장된 ranges_path를 로드하여 고정 모드 SegmentConfig를 생성합니다.
    """
    ranges_path = global_best.get('ranges_path') if isinstance(global_best, dict) else None
    if not ranges_path or not Path(ranges_path).exists():
        return SegmentConfig()

    try:
        df_ranges = pd.read_csv(ranges_path, encoding='utf-8-sig')
        market_cap_ranges: Dict[str, tuple[float, float]] = {}
        time_ranges: Dict[str, tuple[int, int]] = {}

        for _, row in df_ranges.iterrows():
            range_type = row.get('range_type')
            label = row.get('label')
            min_val = row.get('min')
            max_val = row.get('max')

            if pd.isna(max_val):
                max_val = float('inf')

            if range_type == 'market_cap':
                market_cap_ranges[str(label)] = (float(min_val), float(max_val))
            elif range_type == 'time':
                time_ranges[str(label)] = (int(min_val), int(max_val))

        return SegmentConfig(
            dynamic_mode='fixed',
            market_cap_ranges=market_cap_ranges,
            time_ranges=time_ranges,
        )
    except Exception:
        return SegmentConfig()


def build_segment_mask_from_global_best(df: pd.DataFrame, global_best: dict) -> Dict[str, object]:
    """
    세그먼트 전역 조합(global_best)을 이용해 df에서 통과 마스크를 생성합니다.
    """
    result = {
        'mask': None,
        'error': None,
        'segment_trades': {},
        'missing_columns': [],
        'out_of_range_trades': 0,
    }
    if not isinstance(df, pd.DataFrame) or df.empty:
        result['error'] = 'df가 비어있음'
        return result
    if not isinstance(global_best, dict):
        result['error'] = 'global_best가 dict가 아님'
        return result

    combo_map = global_best.get('combination')
    if not isinstance(combo_map, dict) or not combo_map:
        result['error'] = 'combination 없음'
        return result

    try:
        row_col = '__row_pos__'
        if row_col in df.columns:
            idx = 1
            while f"{row_col}{idx}" in df.columns:
                idx += 1
            row_col = f"{row_col}{idx}"

        df_work = df.copy()
        df_work[row_col] = np.arange(len(df_work))

        seg_config = load_segment_config_from_ranges(global_best)
        builder = SegmentBuilder(seg_config)
        segments = builder.build_segments(df_work)
    except Exception as e:
        result['error'] = f"세그먼트 분할 실패: {e}"
        return result

    mask = np.zeros(len(df_work), dtype=bool)
    missing = set()

    for seg_id, seg_df in segments.items():
        combo = combo_map.get(seg_id)
        if combo is None:
            continue
        if combo.get('exclude_segment'):
            result['segment_trades'][seg_id] = 0
            continue
        filters = combo.get('filters') or []
        seg_mask = np.ones(len(seg_df), dtype=bool)

        for flt in filters:
            column = flt.get('column')
            threshold = flt.get('threshold')
            direction = flt.get('direction')
            if column is None or column not in seg_df.columns:
                if column:
                    missing.add(column)
                continue

            values = pd.to_numeric(seg_df[column], errors='coerce')
            if direction == 'less':
                cond = values >= threshold
            else:
                cond = values < threshold
            seg_mask &= cond.fillna(False).to_numpy(dtype=bool)

        row_positions = seg_df[row_col].to_numpy(dtype=int, copy=False)
        mask[row_positions] = seg_mask
        result['segment_trades'][seg_id] = int(seg_mask.sum())

    if hasattr(builder, 'out_of_range') and isinstance(builder.out_of_range, pd.DataFrame):
        result['out_of_range_trades'] = int(len(builder.out_of_range))

    result['mask'] = mask
    result['missing_columns'] = sorted(missing)
    return result


def validate_segment_filter_consistency(
    df: pd.DataFrame,
    global_best: dict,
    expected_remaining: Optional[int] = None,
    tolerance: float = 0.05,
) -> Dict[str, object]:
    """
    세그먼트 필터 적용 전 일관성을 검증합니다.
    
    [2026-01-07 신규 추가]
    - 목적: 예측-실제 불일치 사전 방지
    - 기능: 필터 적용 결과와 예상 결과 비교
    
    Args:
        df: 백테스팅 결과 DataFrame
        global_best: 세그먼트 분석 결과
        expected_remaining: 예상 필터 통과 거래 수 (combos.csv의 remaining_trades)
        tolerance: 허용 오차율 (기본 5%)
    
    Returns:
        dict: 검증 결과
            - is_valid: 일관성 여부
            - actual_remaining: 실제 필터 통과 수
            - expected_remaining: 예상 필터 통과 수
            - difference: 차이 (actual - expected)
            - difference_ratio: 차이 비율
            - missing_columns: 누락된 컬럼 목록
            - segment_summary: 세그먼트별 통과 수
            - warnings: 경고 메시지 목록
    """
    result = {
        'is_valid': False,
        'actual_remaining': 0,
        'expected_remaining': expected_remaining,
        'difference': 0,
        'difference_ratio': 0.0,
        'missing_columns': [],
        'segment_summary': {},
        'warnings': [],
    }
    
    # 필터 적용
    mask_result = build_segment_mask_from_global_best(df, global_best)
    
    if mask_result.get('error'):
        result['warnings'].append(f"필터 적용 실패: {mask_result['error']}")
        return result
    
    mask = mask_result.get('mask')
    if mask is None:
        result['warnings'].append("마스크 생성 실패")
        return result
    
    actual_remaining = int(np.sum(mask))
    result['actual_remaining'] = actual_remaining
    result['segment_summary'] = mask_result.get('segment_trades', {})
    result['missing_columns'] = mask_result.get('missing_columns', [])
    
    # 누락 컬럼 경고
    if result['missing_columns']:
        result['warnings'].append(
            f"누락된 컬럼 {len(result['missing_columns'])}개: {', '.join(result['missing_columns'][:5])}"
            + ("..." if len(result['missing_columns']) > 5 else "")
        )
    
    # 예상값이 있으면 비교
    if expected_remaining is not None and expected_remaining > 0:
        result['difference'] = actual_remaining - expected_remaining
        result['difference_ratio'] = result['difference'] / expected_remaining
        
        if abs(result['difference_ratio']) <= tolerance:
            result['is_valid'] = True
        else:
            result['warnings'].append(
                f"예측-실제 불일치: 예상 {expected_remaining}개, "
                f"실제 {actual_remaining}개 (차이 {result['difference']:+d}, {result['difference_ratio']:+.1%})"
            )
    else:
        # 예상값 없으면 일단 유효
        result['is_valid'] = True
    
    # 로깅
    if result['warnings']:
        for warning in result['warnings']:
            logger.warning(warning)
    
    return result


def build_accurate_segment_mask(
    df: pd.DataFrame,
    global_best: dict,
    date_col: str = '매수일자',
    time_col: str = '매수시간',
    code_col: str = '종목코드',
) -> Dict[str, object]:
    """
    당일 재매수 차단을 시뮬레이션하여 정확한 세그먼트 필터 마스크를 생성합니다.

    [2026-01-10 신규 추가]
    - 목적: 예측과 실제 백테스팅 결과 일치
    - 핵심: 거래를 시간순으로 처리하며 당일 차단을 시뮬레이션

    기존 build_segment_mask_from_global_best()와의 차이:
    - 기존: 각 거래를 독립적으로 평가 (당일 차단 고려 안 함)
    - 신규: 거래를 시간순으로 처리, 당일 차단 시뮬레이션

    동작 방식:
    1. 거래를 날짜+시간 순으로 정렬
    2. 각 거래에 대해:
       a. 해당 종목이 오늘 이미 차단되었는지 확인
       b. 차단되지 않았으면 세그먼트 필터 평가
       c. 세그먼트 필터 실패 시 당일 차단 목록에 추가
    3. 최종 통과 마스크 반환

    Args:
        df: 백테스팅 결과 DataFrame (detail.csv)
        global_best: 세그먼트 분석 결과
        date_col: 날짜 컬럼명 (기본값: '매수일자')
        time_col: 시간 컬럼명 (기본값: '매수시간')
        code_col: 종목코드 컬럼명 (기본값: '종목코드')

    Returns:
        dict: 결과 정보
            - mask: 통과 마스크 (원본 df 순서 기준)
            - error: 에러 메시지 (있는 경우)
            - segment_trades: 세그먼트별 통과 거래 수
            - missing_columns: 누락된 컬럼 목록
            - daily_blocks: 당일 차단 발생 횟수
            - blocked_by_daily: 당일 차단으로 제외된 거래 수
    """
    result = {
        'mask': None,
        'error': None,
        'segment_trades': {},
        'missing_columns': [],
        'daily_blocks': 0,
        'blocked_by_daily': 0,
    }

    if not isinstance(df, pd.DataFrame) or df.empty:
        result['error'] = 'df가 비어있음'
        return result
    if not isinstance(global_best, dict):
        result['error'] = 'global_best가 dict가 아님'
        return result

    combo_map = global_best.get('combination')
    if not isinstance(combo_map, dict) or not combo_map:
        result['error'] = 'combination 없음'
        return result

    # 필요한 컬럼 확인
    required_cols = [date_col, time_col, code_col]
    missing_required = [c for c in required_cols if c not in df.columns]
    if missing_required:
        result['error'] = f"필수 컬럼 누락: {missing_required}"
        return result

    try:
        # 원본 인덱스 저장
        df_work = df.copy()
        df_work['__orig_idx__'] = np.arange(len(df_work))

        # 날짜+시간으로 정렬
        # 날짜와 시간 컬럼을 결합하여 정렬 키 생성
        df_work['__sort_key__'] = (
            df_work[date_col].astype(str) + '_' +
            df_work[time_col].astype(str).str.zfill(6)
        )
        df_sorted = df_work.sort_values('__sort_key__').reset_index(drop=True)

        # 세그먼트 설정 로드
        seg_config = load_segment_config_from_ranges(global_best)
        builder = SegmentBuilder(seg_config)

        # 전체 데이터에 대해 세그먼트 할당
        segments = builder.build_segments(df_sorted)

        # 세그먼트별 필터 통과 마스크 미리 계산
        segment_masks = {}
        missing = set()

        for seg_id, seg_df in segments.items():
            combo = combo_map.get(seg_id)
            if combo is None:
                segment_masks[seg_id] = (seg_df.index.tolist(), np.ones(len(seg_df), dtype=bool))
                continue
            if combo.get('exclude_segment'):
                segment_masks[seg_id] = (seg_df.index.tolist(), np.zeros(len(seg_df), dtype=bool))
                continue

            filters = combo.get('filters') or []
            seg_mask = np.ones(len(seg_df), dtype=bool)

            for flt in filters:
                column = flt.get('column')
                threshold = flt.get('threshold')
                direction = flt.get('direction')
                if column is None or column not in seg_df.columns:
                    if column:
                        missing.add(column)
                    continue

                values = pd.to_numeric(seg_df[column], errors='coerce')
                if direction == 'less':
                    cond = values >= threshold
                else:
                    cond = values < threshold
                seg_mask &= cond.fillna(False).to_numpy(dtype=bool)

            segment_masks[seg_id] = (seg_df.index.tolist(), seg_mask)

        result['missing_columns'] = sorted(missing)

        # 행 인덱스 → 세그먼트 필터 통과 여부 매핑
        row_to_filter_pass = {}
        for seg_id, (indices, seg_mask) in segment_masks.items():
            for i, idx in enumerate(indices):
                row_to_filter_pass[idx] = seg_mask[i]

        # 시간순으로 처리하며 당일 차단 시뮬레이션
        daily_blocked: Dict[Tuple[str, str], int] = {}  # (종목코드, 날짜) → 차단된 시간
        final_mask_sorted = np.zeros(len(df_sorted), dtype=bool)
        daily_blocks_count = 0
        blocked_by_daily_count = 0

        for row_idx in range(len(df_sorted)):
            row = df_sorted.iloc[row_idx]
            code = str(row[code_col])
            date = str(row[date_col])

            block_key = (code, date)

            # 1. 이미 당일 차단된 종목인지 확인
            if block_key in daily_blocked:
                blocked_by_daily_count += 1
                final_mask_sorted[row_idx] = False
                continue

            # 2. 세그먼트 필터 통과 여부 확인
            filter_passed = row_to_filter_pass.get(row_idx, False)

            if filter_passed:
                # 세그먼트 필터 통과 → 거래 허용
                final_mask_sorted[row_idx] = True
            else:
                # 세그먼트 필터 실패 → 당일 차단 기록
                final_mask_sorted[row_idx] = False
                daily_blocked[block_key] = int(row[time_col]) if pd.notna(row[time_col]) else 0
                daily_blocks_count += 1

        # 원본 순서로 마스크 복원
        orig_indices = df_sorted['__orig_idx__'].to_numpy(dtype=int)
        final_mask = np.zeros(len(df), dtype=bool)
        for i, orig_idx in enumerate(orig_indices):
            final_mask[orig_idx] = final_mask_sorted[i]

        result['mask'] = final_mask
        result['daily_blocks'] = daily_blocks_count
        result['blocked_by_daily'] = blocked_by_daily_count

        # 세그먼트별 통과 수 계산 (원본 순서 기준)
        for seg_id, (indices, _) in segment_masks.items():
            # indices는 df_sorted 기준, 원본 df 기준으로 변환 필요
            orig_idx_for_seg = [orig_indices[i] for i in indices if i < len(orig_indices)]
            passed_count = sum(1 for oi in orig_idx_for_seg if final_mask[oi])
            result['segment_trades'][seg_id] = passed_count

    except Exception as e:
        result['error'] = f"정확한 마스크 생성 실패: {e}"
        logger.exception(f"build_accurate_segment_mask 오류: {e}")

    return result


def get_filter_diagnostic_info(
    df: pd.DataFrame,
    global_best: dict,
) -> Dict[str, object]:
    """
    세그먼트 필터 진단 정보를 생성합니다.
    
    [2026-01-07 신규 추가]
    - 목적: 문제 발생 시 상세 진단 정보 제공
    
    Args:
        df: 백테스팅 결과 DataFrame
        global_best: 세그먼트 분석 결과
    
    Returns:
        dict: 진단 정보
            - total_trades: 전체 거래 수
            - segment_distribution: 세그먼트별 거래 분포
            - filter_coverage: 필터가 사용하는 컬럼의 가용성
            - ranges_path_valid: ranges.csv 경로 유효성
            - config_mode: SegmentConfig 모드 (fixed/dynamic/semi)
    """
    result = {
        'total_trades': len(df) if isinstance(df, pd.DataFrame) else 0,
        'segment_distribution': {},
        'filter_coverage': {},
        'ranges_path_valid': False,
        'config_mode': 'unknown',
    }
    
    if not isinstance(global_best, dict):
        return result
    
    # ranges.csv 경로 확인
    ranges_path = global_best.get('ranges_path')
    if ranges_path and Path(ranges_path).exists():
        result['ranges_path_valid'] = True
    
    # SegmentConfig 로드
    seg_config = load_segment_config_from_ranges(global_best)
    result['config_mode'] = seg_config.dynamic_mode if hasattr(seg_config, 'dynamic_mode') else 'unknown'
    
    # 필터가 사용하는 컬럼 가용성 확인
    combo_map = global_best.get('combination', {})
    required_columns = set()
    
    for combo in combo_map.values():
        if isinstance(combo, dict):
            for flt in combo.get('filters', []):
                if isinstance(flt, dict) and flt.get('column'):
                    required_columns.add(flt['column'])
    
    if isinstance(df, pd.DataFrame):
        for col in required_columns:
            result['filter_coverage'][col] = col in df.columns
    
    return result
