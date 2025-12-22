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
    exclude_prefixes: Tuple[str, ...] = ('매도',)
    exclude_patterns: Tuple[str, ...] = (
        '수익금', '수익률', '손실', '이익', '보유시간', '매수일자',
        '변화', '추세', '연속이익', '연속손실', '리스크조정수익률',
        '합계', '누적', '매수매도위험도점수',
    )
    explicit_buy_columns: Tuple[str, ...] = (
        '매수등락율', '매수시가등락율', '매수당일거래대금', '매수체결강도',
        '매수전일비', '매수회전율', '매수전일동시간비', '매수고가', '매수저가',
        '매수고저평균대비등락율', '매수매도총잔량', '매수매수총잔량',
        '매수호가잔량비', '매수매도호가1', '매수매수호가1', '매수스프레드',
        '매수초당매수수량', '매수초당매도수량', '매수초당거래대금',
        '시가총액', '매수가', '매수시', '매수분', '매수초',
        '모멘텀점수', '매수변동폭', '매수변동폭비율', '거래품질점수',
        '초당매수수량_매도총잔량_비율', '매도잔량_매수잔량_비율',
        '매수잔량_매도잔량_비율', '초당매도_매수_비율', '초당매수_매도_비율',
        '현재가_고저범위_위치', '초당거래대금_당일비중',
        '초당순매수수량', '초당순매수금액', '초당순매수비율',
    )
    extra_columns: Tuple[str, ...] = (
        '시가총액', '모멘텀점수', '거래품질점수', '위험도점수', '타이밍점수'
    )


class FilterEvaluator:
    """
    세그먼트별 필터 후보 평가
    """

    def __init__(self, config: Optional[FilterEvaluatorConfig] = None):
        self.config = config or FilterEvaluatorConfig()

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

            thresholds = values[valid].quantile(self.config.quantiles).dropna().unique()
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
        if self.config.include_columns:
            return [c for c in self.config.include_columns if c in df.columns]

        feature_columns: List[str] = []
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue
            if self._should_exclude(col):
                continue
            if col in self.config.explicit_buy_columns or col.startswith('매수'):
                feature_columns.append(col)

        for col in self.config.extra_columns:
            if col in df.columns and col not in feature_columns:
                feature_columns.append(col)

        return feature_columns

    def _should_exclude(self, col: str) -> bool:
        if any(col.startswith(prefix) for prefix in self.config.exclude_prefixes):
            return True

        col_lower = col.lower()
        for pattern in self.config.exclude_patterns:
            if pattern.lower() in col_lower:
                return True

        if not self.config.allow_ml_filters and '_ml' in col_lower:
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
