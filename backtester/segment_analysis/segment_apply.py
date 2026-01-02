# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .segmentation import SegmentBuilder, SegmentConfig


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
