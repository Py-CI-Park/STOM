# -*- coding: utf-8 -*-
"""
Segment Visualization Helpers

세그먼트 히트맵/필터 효율 차트를 생성합니다.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - optional dependency
    plt = None

from .segmentation import create_segment_matrix_view


def plot_segment_heatmap(summary_df: pd.DataFrame, output_path: str) -> Optional[str]:
    if plt is None or summary_df is None or summary_df.empty:
        return None

    df = summary_df.copy()
    df = df[df['segment_id'] != 'Out_of_Range']
    if df.empty:
        return None

    df['cap'] = df['segment_id'].astype(str).str.split('_', n=1).str[0]
    df['time_label'] = df['segment_id'].astype(str).str.split('_', n=1).str[1]

    trades = df.pivot_table(index='cap', columns='time_label', values='trades', fill_value=0)
    profits = df.pivot_table(index='cap', columns='time_label', values='profit', fill_value=0)

    row_order = _sort_cap_labels(trades.index.tolist())
    if row_order:
        trades = trades.reindex(index=row_order)
        profits = profits.reindex(index=row_order)

    col_order = _sort_time_labels(trades.columns.tolist())
    trades = trades.reindex(columns=col_order)
    profits = profits.reindex(columns=col_order)

    vmax = max(abs(profits.max().max()), abs(profits.min().min()))
    if vmax == 0:
        vmax = 1.0

    col_count = max(1, len(profits.columns))
    row_count = max(1, len(profits.index))
    fig_width = max(7.5, min(18.0, 0.6 * col_count))
    fig_height = max(4.5, min(10.0, 0.35 * row_count))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    im = ax.imshow(profits.values, cmap='RdYlGn', aspect='auto', vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(len(profits.columns)))
    rotation = 0
    ha = 'center'
    font_size = 8
    if col_count >= 14:
        rotation = 90
        ha = 'center'
        font_size = 7
    elif col_count >= 9:
        rotation = 45
        ha = 'right'
        font_size = 7
    ax.set_xticklabels(profits.columns, rotation=rotation, ha=ha, fontsize=font_size)
    ax.set_yticks(range(len(profits.index)))
    ax.set_yticklabels(profits.index, fontsize=9)
    ax.set_title('Segment Heatmap (Profit color / Trades text)')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='Profit')

    for i, cap in enumerate(profits.index):
        for j, label in enumerate(profits.columns):
            trade_val = int(trades.loc[cap, label]) if label in trades.columns else 0
            profit_val = float(profits.loc[cap, label]) if label in profits.columns else 0.0
            text = f"T:{trade_val:,}\nP:{_fmt_profit(profit_val)}"
            ax.text(j, i, text, ha='center', va='center', fontsize=7)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_filter_efficiency(filters_df: pd.DataFrame, output_path: str, top_n: int = 20) -> Optional[str]:
    if plt is None or filters_df is None or filters_df.empty:
        return None

    df = filters_df.copy()
    if 'efficiency' not in df.columns:
        return None

    df = df.sort_values('efficiency', ascending=False).head(top_n)
    if df.empty:
        return None

    labels = df['filter_name'].astype(str).tolist()
    values = df['efficiency'].astype(float).tolist()

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(range(len(labels)), values, color='#2E8B57')
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel('Efficiency')
    ax.set_title('Top Filter Efficiency')

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def _sort_time_labels(labels: list[str]) -> list[str]:
    def _extract_start(label: str) -> int:
        parts = str(label).split('_')
        if len(parts) >= 2 and parts[1].isdigit():
            return int(parts[1])
        if len(parts) >= 3 and parts[2].isdigit():
            return int(parts[2])
        return 0

    return sorted(labels, key=_extract_start)


def _sort_cap_labels(labels: list[str]) -> list[str]:
    priority = ['초소형주', '소형주', '중소형주', '중형주', '중대형주', '대형주']
    ordered = [name for name in priority if name in labels]
    rest = sorted([name for name in labels if name not in ordered])
    return ordered + rest


def _fmt_profit(value: float) -> str:
    try:
        v = float(value)
    except Exception:
        return "0"
    sign = "+" if v >= 0 else ""
    if abs(v) >= 100000000:
        return f"{sign}{v/100000000:.1f}억"
    return f"{sign}{v:,.0f}"


def plot_pareto_front(pareto_df: pd.DataFrame, output_path: str) -> Optional[str]:
    if plt is None or pareto_df is None or pareto_df.empty:
        return None

    if 'remaining_ratio' not in pareto_df.columns or 'total_improvement' not in pareto_df.columns:
        return None

    x = pareto_df['remaining_ratio'].astype(float).to_numpy()
    y = pareto_df['total_improvement'].astype(float).to_numpy()
    color = None
    if 'mdd_pct' in pareto_df.columns:
        color = pareto_df['mdd_pct'].astype(float).to_numpy()

    fig, ax = plt.subplots(figsize=(6, 4))
    if color is not None:
        sc = ax.scatter(x, y, c=color, cmap='viridis', alpha=0.8)
        fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04, label='MDD(%)')
    else:
        ax.scatter(x, y, color='#1f77b4', alpha=0.8)

    ax.set_xlabel('Remaining Ratio')
    ax.set_ylabel('Total Improvement')
    ax.set_title('Pareto Front (Multi-Objective)')
    ax.grid(True, linestyle='--', alpha=0.4)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
