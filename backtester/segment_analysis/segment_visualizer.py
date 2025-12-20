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

    matrix = create_segment_matrix_view(summary_df)
    if matrix.empty:
        return None

    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(matrix.values, cmap='YlGnBu', aspect='auto')
    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels(matrix.columns, rotation=0)
    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index)
    ax.set_title('Segment Heatmap (Trades)')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    for i, row in enumerate(matrix.values):
        for j, val in enumerate(row):
            ax.text(j, i, f"{int(val):,}", ha='center', va='center', fontsize=8)

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
