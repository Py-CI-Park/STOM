# -*- coding: utf-8 -*-
"""
Segment Filter Evaluator

세그먼트별로 필터 후보(임계값 기반)를 평가하고,
통계적 유의성/제외율/효율 지표를 계산합니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backtester.analysis.metric_registry import BUY_TIME_FILTER_COLUMNS, ANALYSIS_ONLY_COLUMNS

try:
    from scipy import stats
except Exception:  # pragma: no cover - optional dependency
    stats = None


@dataclass
class FilterEvaluatorConfig:
    """
    필터 평가 설정
    """

    p_threshold: float = 0.05
    effect_threshold: float = 0.2
    max_exclusion: float = 0.85
    min_trades: int = 15
    min_improvement: float = 0.0
    top_k: int = 50
    quantiles: Tuple[float, ...] = (0.05, 0.1, 0.2, 0.8, 0.9, 0.95)
    allow_ml_filters: bool = True

    include_columns: Optional[List[str]] = None
    exclude_prefixes: Tuple[str, ...] = ('매도', 'S_')

    exclude_patterns: Tuple[str, ...] = (
        '수익금', '수익률', '손실', '이익', '보유시간', '매수일자',
        '매수시간', '매수금액', '변화', '추세', '연속이익', '연속손실', '리스크조정수익률',
        '합계', '누적', '매수매도위험도점수',
    )
    explicit_buy_columns: Tuple[str, ...] = tuple(BUY_TIME_FILTER_COLUMNS)
    analysis_only_columns: Tuple[str, ...] = tuple(ANALYSIS_ONLY_COLUMNS)
    extra_columns: Tuple[str, ...] = (
        '시가총액', '모멘텀점수', '거래품질점수', '위험도점수', '타이밍점수'
    )


class FilterEvaluator:
    """
    세그먼트별 필터 후보 평가
    """

    def __init__(self, config: Optional[FilterEvaluatorConfig] = None):
        self.config = config or FilterEvaluatorConfig()

    def _detect_timeframe(self, columns: List[str]) -> str:
        if any('분당' in col for col in columns):
            return 'min'
        return 'tick'

    def _map_buy_column(self, col: str, column_set: set) -> str:
        if col.startswith('B_'):
            return col
        if col.startswith('매수'):
            alias = f"B_{col[2:]}"
            if alias in column_set:
                return alias
        else:
            alias = f"B_{col}"
            if alias in column_set:
                return alias
        return col

    def _normalize_col_for_patterns(self, col: str) -> str:
        if col.startswith('B_'):
            return f"매수{col[2:]}"
        if col.startswith('S_'):
            return f"매도{col[2:]}"
        return col

    def evaluate_segment(self, segment_df: pd.DataFrame, segment_id: str) -> List[dict]:

        if segment_df.empty or '수익금' not in segment_df.columns:
            return []

        total_profit = pd.to_numeric(segment_df['수익금'], errors='coerce').fillna(0).sum()
        total_trades = len(segment_df)
        if total_trades < self.config.min_trades:
            return []

        candidates: List[dict] = []
        for col in self._select_columns(segment_df):
            values = pd.to_numeric(segment_df[col], errors='coerce')
            valid = values.notna()
            if valid.sum() < self.config.min_trades:
                continue

            unique_vals = values[valid].unique()
            if len(unique_vals) < 5:
                continue

            thresholds = values[valid].quantile(self.config.quantiles).round(4).dropna().unique()
            for thr in sorted(set(thresholds)):

                for direction in ('less', 'greater'):
                    result = self._evaluate_threshold(
                        segment_df,
                        values,
                        threshold=thr,
                        direction=direction,
                        total_profit=total_profit,
                        total_trades=total_trades,
                    )
                    if result is None:
                        continue
                    result.update({
                        'segment_id': segment_id,
                        'column': col,
                        'filter_name': self._format_filter_name(col, thr, direction),
                        'threshold': float(thr),
                        'direction': direction,
                    })
                    candidates.append(result)

        candidates.sort(key=lambda x: x['efficiency'], reverse=True)
        return candidates[:self.config.top_k]

    def evaluate_all_segments(self, segments: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        rows: List[dict] = []
        for seg_id, seg_df in segments.items():
            rows.extend(self.evaluate_segment(seg_df, seg_id))
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)

    def _evaluate_threshold(
        self,
        segment_df: pd.DataFrame,
        values: pd.Series,
        threshold: float,
        direction: str,
        total_profit: float,
        total_trades: int,
    ) -> Optional[dict]:
        if direction == 'less':
            keep_mask = values >= threshold
        else:
            keep_mask = values < threshold

        remaining = segment_df[keep_mask]
        filtered_out = segment_df[~keep_mask]

        remaining_trades = len(remaining)
        if remaining_trades < self.config.min_trades:
            return None

        exclusion_ratio = 1.0 - (remaining_trades / max(1, total_trades))
        if exclusion_ratio > self.config.max_exclusion:
            return None

        remaining_profit = pd.to_numeric(remaining['수익금'], errors='coerce').fillna(0).sum()
        improvement = remaining_profit - total_profit
        if improvement <= self.config.min_improvement:
            return None

        p_value, effect_size = self._calc_stats(filtered_out, remaining)
        if stats is not None:
            if p_value >= self.config.p_threshold:
                return None
            if abs(effect_size) < self.config.effect_threshold:
                return None
        elif p_value >= 1.0:
            effect_size = 0.0

        efficiency = improvement / max(1.0, exclusion_ratio * 100.0)

        return {
            'improvement': float(improvement),
            'exclusion_ratio': float(exclusion_ratio),
            'p_value': float(p_value),
            'effect_size': float(effect_size),
            'efficiency': float(efficiency),
            'stability_score': 0.0,
        }

    def _calc_stats(self, filtered_out: pd.DataFrame, remaining: pd.DataFrame) -> Tuple[float, float]:
        if stats is None:
            return 1.0, 0.0

        if len(filtered_out) < 2 or len(remaining) < 2:
            return 1.0, 0.0

        group1 = pd.to_numeric(filtered_out['수익금'], errors='coerce').dropna().to_numpy(dtype=np.float64)
        group2 = pd.to_numeric(remaining['수익금'], errors='coerce').dropna().to_numpy(dtype=np.float64)
        if group1.size < 2 or group2.size < 2:
            return 1.0, 0.0

        t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)
        pooled_std = np.sqrt((np.var(group1) + np.var(group2)) / 2)
        effect_size = (np.mean(group1) - np.mean(group2)) / pooled_std if pooled_std > 0 else 0.0
        return round(float(p_value), 4), round(float(effect_size), 3)

    def _select_columns(self, df: pd.DataFrame) -> List[str]:
        df_cols = list(df.columns)
        col_set = set(df_cols)
        timeframe = self._detect_timeframe(df_cols)
        ignore_seconds = timeframe == 'min'

        def _should_skip(col: str) -> bool:
            return ignore_seconds and '초당' in col

        def _add(col: str, feature_columns: List[str], seen: set) -> None:
            if not col or col not in col_set:
                return
            if _should_skip(col):
                return
            if not pd.api.types.is_numeric_dtype(df[col]):
                return
            if self._should_exclude(col):
                return
            if col in seen:
                return
            seen.add(col)
            feature_columns.append(col)

        if self.config.include_columns:
            feature_columns: List[str] = []
            seen: set = set()
            for col in self.config.include_columns:
                mapped = col.replace('초당', '분당') if ignore_seconds else col
                mapped = self._map_buy_column(mapped, col_set)
                _add(mapped, feature_columns, seen)
            return feature_columns

        feature_columns: List[str] = []
        seen: set = set()

        # 1) 명시적 매수 컬럼 우선 추가
        for col in self.config.explicit_buy_columns:
            mapped = col.replace('초당', '분당') if ignore_seconds else col
            mapped = self._map_buy_column(mapped, col_set)
            _add(mapped, feature_columns, seen)

        # 2) 매수/ B_ 접두 컬럼 추가
        for col in df_cols:
            if col.startswith('매수') or col.startswith('B_'):
                mapped = self._map_buy_column(col, col_set)
                _add(mapped, feature_columns, seen)

        # 3) 추가 컬럼
        for col in self.config.extra_columns:
            _add(col, feature_columns, seen)

        # 4) ML 컬럼
        if self.config.allow_ml_filters:
            for col in df_cols:
                if col in seen:
                    continue
                if not str(col).endswith('_ML'):
                    continue
                if _should_skip(col):
                    continue
                if not pd.api.types.is_numeric_dtype(df[col]):
                    continue
                seen.add(col)
                feature_columns.append(col)

        return feature_columns


    def _should_exclude(self, col: str) -> bool:
        base_col = self._normalize_col_for_patterns(col)
        col_lower = base_col.lower()
        for pattern in self.config.exclude_patterns:
            if pattern.lower() in col_lower:
                return True

        if base_col in self.config.analysis_only_columns:
            return True

        if not self.config.allow_ml_filters and '_ml' in col_lower:
            return True

        if base_col in self.config.explicit_buy_columns:
            return False

        if any(base_col.startswith(prefix) for prefix in self.config.exclude_prefixes):
            return True

        return False


    def _format_filter_name(self, column: str, threshold: float, direction: str) -> str:
        suffix = '미만 제외' if direction == 'less' else '이상 제외'
        if '시가총액' in column:
            label = f"{threshold:.0f}억"
        elif abs(threshold) >= 1000:
            label = f"{threshold:.0f}"
        elif abs(threshold) >= 10:
            label = f"{threshold:.2f}"
        else:
            label = f"{threshold:.3f}"
        return f"{column} {label} {suffix}"
