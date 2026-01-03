# -*- coding: utf-8 -*-
"""
Segment Visualization Helpers

세그먼트 히트맵/필터 효율 차트를 생성합니다.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from utility.mpl_setup import ensure_mpl_font
from backtester.analysis.memo_utils import build_strategy_memo_text, add_memo_box

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - optional dependency
    plt = None

from .segmentation import create_segment_matrix_view


def _ensure_korean_font():
    if plt is None:
        return
    ensure_mpl_font()


def plot_segment_heatmap(
    summary_df: pd.DataFrame,
    output_path: str,
    filtered_summary_df: Optional[pd.DataFrame] = None,
    ranges_df: Optional[pd.DataFrame] = None,
    buystg_name: Optional[str] = None,
    sellstg_name: Optional[str] = None,
    save_file_name: Optional[str] = None,
) -> Optional[str]:
    if plt is None or summary_df is None or summary_df.empty:
        return None

    _ensure_korean_font()

    def _prepare_heatmap(df: pd.DataFrame,
                         row_order: Optional[list] = None,
                         col_order: Optional[list] = None):
        data = df.copy()
        data = data[data['segment_id'] != 'Out_of_Range']
        if data.empty:
            return None, None, row_order, col_order

        data['cap'] = data['segment_id'].astype(str).str.split('_', n=1).str[0]
        data['time_label'] = data['segment_id'].astype(str).str.split('_', n=1).str[1]

        trades = data.pivot_table(index='cap', columns='time_label', values='trades', fill_value=0)
        profits = data.pivot_table(index='cap', columns='time_label', values='profit', fill_value=0)

        if row_order is None:
            row_order = _sort_cap_labels(trades.index.tolist())
        if row_order:
            trades = trades.reindex(index=row_order)
            profits = profits.reindex(index=row_order)

        if col_order is None:
            col_order = _sort_time_labels(trades.columns.tolist())
        if col_order:
            trades = trades.reindex(columns=col_order)
            profits = profits.reindex(columns=col_order)

        return trades, profits, row_order, col_order

    trades_base, profits_base, row_order, col_order = _prepare_heatmap(summary_df)
    if profits_base is None or trades_base is None:
        return None

    trades_filt = None
    profits_filt = None
    if filtered_summary_df is not None and not filtered_summary_df.empty:
        trades_filt, profits_filt, _, _ = _prepare_heatmap(
            filtered_summary_df, row_order=row_order, col_order=col_order
        )

    def _format_cap_range(min_v, max_v) -> Optional[str]:
        try:
            min_val = float(min_v) if min_v is not None else None
        except Exception:
            min_val = None
        try:
            max_val = float(max_v) if max_v is not None else None
        except Exception:
            max_val = None

        if min_val is None and max_val is None:
            return None
        if max_val is None or pd.isna(max_val):
            return f"{int(round(min_val)):,}억 이상"
        if min_val is None or pd.isna(min_val):
            return f"{int(round(max_val)):,}억 이하"
        return f"{int(round(min_val)):,}~{int(round(max_val)):,}억"

    cap_range_map = {}
    if ranges_df is not None and not ranges_df.empty:
        try:
            df_ranges = ranges_df.copy()
            df_ranges = df_ranges[df_ranges['range_type'] == 'market_cap']
            for _, row in df_ranges.iterrows():
                label = str(row.get('label', '')).strip()
                if not label:
                    continue
                cap_range_map[label] = _format_cap_range(row.get('min'), row.get('max'))
        except Exception:
            cap_range_map = {}

    def _draw_heatmap(ax, profits, trades, title: str, vmax_override=None):
        if vmax_override is not None:
            vmax = vmax_override
        else:
            vmax = max(abs(profits.max().max()), abs(profits.min().min()))
            if vmax == 0:
                vmax = 1.0

        col_count = max(1, len(profits.columns))
        row_count = max(1, len(profits.index))
        cell_count = col_count * row_count

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
        if cap_range_map:
            display_labels = []
            for cap_label in profits.index:
                range_text = cap_range_map.get(str(cap_label))
                if range_text:
                    display_labels.append(f"{cap_label}\n({range_text})")
                else:
                    display_labels.append(str(cap_label))
            ax.set_yticklabels(display_labels, fontsize=8)
        else:
            ax.set_yticklabels(profits.index, fontsize=9)
        ax.set_title(title)

        text_font = 7
        if col_count >= 12 or row_count >= 8:
            text_font = 6
        if col_count >= 16 or row_count >= 12:
            text_font = 5
        compact_text = cell_count >= 80 or col_count >= 10 or row_count >= 8
        text_rotation = 0
        if compact_text:
            text_rotation = 45 if col_count < 16 else 90

        for i, cap in enumerate(profits.index):
            for j, label in enumerate(profits.columns):
                trade_val = int(trades.loc[cap, label]) if label in trades.columns else 0
                profit_val = float(profits.loc[cap, label]) if label in profits.columns else 0.0
                if compact_text:
                    text = f"{trade_val:,}\n{_fmt_profit(profit_val)}"
                else:
                    text = f"T:{trade_val:,}\nP:{_fmt_profit(profit_val)}"
                ax.text(j, i, text, ha='center', va='center', fontsize=text_font, rotation=text_rotation)

        total_profit = float(profits.to_numpy(dtype=float).sum())
        ax.text(
            0.02,
            0.98,
            f"Profit 합계: {_fmt_profit(total_profit)}",
            transform=ax.transAxes,
            ha='left',
            va='top',
            fontsize=8,
            bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='gray', alpha=0.85),
        )

        return im

    col_count = max(1, len(profits_base.columns))
    row_count = max(1, len(profits_base.index))
    fig_width = max(7.5, min(18.0, 0.6 * col_count))
    base_height = max(4.5, min(10.0, 0.35 * row_count))
    nrows = 2 if profits_filt is not None and trades_filt is not None else 1
    fig_height = base_height * nrows

    memo_text = build_strategy_memo_text(
        buystg_name,
        sellstg_name,
        save_file_name or output_path,
    )

    # 2025-01-03: 히트맵 동적 범위 통일 - 필터 적용 전후 비교를 위해 동일한 scale 사용
    # 기준과 필터 적용 데이터 중 최대 절대값을 사용하여 color scale 통일
    vmax_global = max(abs(profits_base.max().max()), abs(profits_base.min().min()))
    if profits_filt is not None:
        vmax_filt = max(abs(profits_filt.max().max()), abs(profits_filt.min().min()))
        vmax_global = max(vmax_global, vmax_filt)
    if vmax_global == 0:
        vmax_global = 1.0

    fig, axes = plt.subplots(nrows=nrows, ncols=1, figsize=(fig_width, fig_height))
    if nrows == 1:
        axes = [axes]

    im = _draw_heatmap(axes[0], profits_base, trades_base, 'Segment Heatmap (기준)', vmax_override=vmax_global)
    fig.colorbar(im, ax=axes[0], fraction=0.046, pad=0.04, label='Profit')

    if nrows == 2 and profits_filt is not None and trades_filt is not None:
        im2 = _draw_heatmap(axes[1], profits_filt, trades_filt, 'Segment Heatmap (필터 적용)', vmax_override=vmax_global)
        fig.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04, label='Profit')

    add_memo_box(fig, memo_text)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_filter_efficiency(filters_df: pd.DataFrame, output_path: str, top_n: int = 20,
                           buystg_name: Optional[str] = None,
                           sellstg_name: Optional[str] = None,
                           save_file_name: Optional[str] = None) -> Optional[str]:
    if plt is None or filters_df is None or filters_df.empty:
        return None

    _ensure_korean_font()

    df = filters_df.copy()
    if 'efficiency' not in df.columns:
        return None

    df = df.sort_values('efficiency', ascending=False).head(top_n)
    if df.empty:
        return None

    labels = df['filter_name'].astype(str).tolist()
    values = df['efficiency'].astype(float).tolist()

    memo_text = build_strategy_memo_text(
        buystg_name,
        sellstg_name,
        save_file_name or output_path,
    )

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(range(len(labels)), values, color='#2E8B57')
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel('Efficiency')
    ax.set_title('Top Filter Efficiency')

    add_memo_box(fig, memo_text)
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
    sign = "+" if v >= 0 else "-"
    abs_v = abs(v)
    if abs_v >= 100000000:
        return f"{sign}{abs_v/100000000:.1f}억"
    if abs_v >= 10000:
        return f"{sign}{abs_v/10000:.1f}만"
    return f"{sign}{abs_v:,.0f}"


def plot_pareto_front(pareto_df: pd.DataFrame, output_path: str) -> Optional[str]:
    if plt is None or pareto_df is None or pareto_df.empty:
        return None

    if 'remaining_ratio' not in pareto_df.columns or 'total_improvement' not in pareto_df.columns:
        return None

    _ensure_korean_font()

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
