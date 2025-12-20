# -*- coding: utf-8 -*-
"""
Risk Metrics Helpers

세그먼트 조합 적용 결과에 대한 리스크 지표(MDD/변동성)를 계산합니다.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


def compute_cum_profit(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce').fillna(0.0)
    return values.cumsum()


def compute_mdd(cum_profit: pd.Series) -> Tuple[float, float]:
    """
    최대 낙폭(MDD)을 계산합니다.
    - mdd_won: 최대 낙폭(원)
    - mdd_pct: 피크 대비 낙폭 비율(%)
    """
    if cum_profit.empty:
        return 0.0, 0.0

    peak = cum_profit.cummax()
    drawdown = peak - cum_profit
    mdd_won = float(drawdown.max() or 0.0)
    peak_value = float(peak.max() or 0.0)
    denom = max(1.0, abs(peak_value))
    mdd_pct = (mdd_won / denom) * 100.0
    return mdd_won, mdd_pct


def compute_volatility(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors='coerce')
    if values.notna().sum() < 2:
        return 0.0
    return float(values.std())


def summarize_risk(df: pd.DataFrame) -> Dict[str, Optional[float]]:
    """
    detail.csv 기반 리스크 요약 계산.
    - 수익금 기준 MDD/변동성
    - 수익률 변동성(있을 경우)
    """
    if df is None or df.empty:
        return {
            'mdd_won': 0.0,
            'mdd_pct': 0.0,
            'profit_volatility': 0.0,
            'return_volatility': None,
        }

    profit_series = pd.to_numeric(df.get('수익금'), errors='coerce').fillna(0.0)
    cum_profit = compute_cum_profit(profit_series)
    mdd_won, mdd_pct = compute_mdd(cum_profit)

    return_vol = None
    if '수익률' in df.columns:
        return_vol = compute_volatility(df['수익률'])

    return {
        'mdd_won': mdd_won,
        'mdd_pct': mdd_pct,
        'profit_volatility': compute_volatility(profit_series),
        'return_volatility': return_vol,
    }
