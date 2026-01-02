# -*- coding: utf-8 -*-
"""
Segment Summary Report

세그먼트 템플릿 비교 결과와 세그먼트 상세 산출물을 묶어
종합 요약 텍스트 리포트를 생성합니다.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from backtester.output_paths import build_backtesting_output_path


def write_segment_summary_report(output_dir: str, prefix: str, segment_outputs: dict) -> Optional[str]:
    if not output_dir or not prefix:
        return None
    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    report_path = build_backtesting_output_path(prefix, "_segment_summary_full.txt", output_dir=output_path)

    phase2 = (segment_outputs or {}).get('phase2') or {}
    phase3 = (segment_outputs or {}).get('phase3') or {}
    template_comp = (segment_outputs or {}).get('template_comparison') or {}

    comp_path = template_comp.get('comparison_path')
    comp_df = _read_csv_safe(comp_path)

    lines: list[str] = []
    lines.append("=== Segment Summary Report ===")
    lines.append(f"- 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- prefix: {prefix}")
    if comp_path:
        lines.append(f"- 템플릿 비교 파일: {comp_path}")
    lines.append("")

    lines.extend(_build_template_explain_lines())

    best_row = None
    if not comp_df.empty:
        lines.append("")
        lines.append("[템플릿 비교 요약]")
        lines.extend(_summarize_template_table(comp_df))
        best_row = _pick_best_template(comp_df)
    else:
        lines.append("[템플릿 비교 요약]")
        lines.append("- 템플릿 비교 CSV가 없거나 비어 있습니다.")

    detail_paths = _resolve_detail_paths(best_row, phase2, phase3)
    lines.append("")
    lines.append("[세그먼트 상세 파일 안내]")
    lines.extend(_describe_detail_paths(detail_paths))

    ranges_df = _read_csv_safe(detail_paths.get('ranges_path'))
    if not ranges_df.empty:
        lines.append("")
        lines.append("[세그먼트 구간 정의]")
        lines.extend(_summarize_ranges(ranges_df))

    summary_df = _read_csv_safe(detail_paths.get('summary_path'))
    if not summary_df.empty:
        lines.append("")
        lines.append("[세그먼트 요약]")
        lines.extend(_summarize_segment_summary(summary_df))

    filters_df = _read_csv_safe(detail_paths.get('filters_path'))
    if not filters_df.empty:
        lines.append("")
        lines.append("[세그먼트별 필터 상위]")
        lines.extend(_summarize_filters(filters_df, max_per_segment=5))

    local_df = _read_csv_safe(detail_paths.get('local_combo_path'))
    if not local_df.empty:
        lines.append("")
        lines.append("[세그먼트별 로컬 조합 상위]")
        lines.extend(_summarize_local_combos(local_df, max_per_segment=3))

    global_df = _read_csv_safe(detail_paths.get('global_combo_path'))
    if not global_df.empty:
        lines.append("")
        lines.append("[전역 조합 요약]")
        lines.extend(_summarize_global_combo(global_df))

    report_path.write_text("\n".join(lines), encoding='utf-8-sig')
    return str(report_path)


def _build_template_explain_lines() -> list[str]:
    lines = []
    lines.append("[템플릿 비교 해석]")
    lines.append("- 템플릿 비교 CSV는 시간/시총 세그먼트 조합별 전역 조합 성과를 요약합니다.")
    lines.append("- score는 개선금액/잔여비율/MDD/변동성/복잡도(세그먼트 수) 가중치를 합산한 점수입니다.")
    lines.append("- eligible은 최소 잔여비율/개선금액 기준을 만족하는 템플릿을 의미합니다.")
    return lines


def _summarize_template_table(df: pd.DataFrame) -> list[str]:
    lines = []
    table = df.copy()
    if 'score' in table.columns:
        table = table.sort_values('score', ascending=False)
    else:
        table = table.sort_values('total_improvement', ascending=False)

    lines.append("- 상위 템플릿:")
    for idx, (_, row) in enumerate(table.head(5).iterrows(), start=1):
        template = row.get('template', 'N/A')
        variant = row.get('variant', '')
        dyn_mode = row.get('dynamic_mode') or ''
        segments = _fmt_int(row.get('segment_count'))
        improvement = _fmt_signed(row.get('total_improvement'))
        remaining = _fmt_pct(row.get('remaining_ratio'))
        mdd = _fmt_pct(row.get('mdd_pct'))
        score = _fmt_float(row.get('score'))
        label = f"{template}/{variant}"
        if dyn_mode:
            label += f"({dyn_mode})"
        lines.append(
            f"  {idx}) {label} | 세그 {segments} | 개선 {improvement} | 잔여 {remaining} | MDD {mdd} | score {score}"
        )
    return lines


def _pick_best_template(df: pd.DataFrame) -> Optional[pd.Series]:
    if df is None or df.empty:
        return None
    if 'score' in df.columns:
        df = df.sort_values('score', ascending=False)
    elif 'total_improvement' in df.columns:
        df = df.sort_values('total_improvement', ascending=False)
    return df.iloc[0]


def _resolve_detail_paths(best_row: Optional[pd.Series], phase2: dict, phase3: dict) -> dict:
    paths = {
        'summary_path': None,
        'filters_path': None,
        'local_combo_path': None,
        'global_combo_path': None,
        'ranges_path': None,
        'segment_code_path': None,
        'segment_code_final_path': None,
        'thresholds_path': None,
    }

    if best_row is not None:
        for key in ('summary_path', 'filters_path', 'local_combo_path',
                    'global_combo_path', 'ranges_path'):
            if key in best_row:
                paths[key] = best_row.get(key)

    # fallback: base phase2/phase3 산출물
    paths['summary_path'] = paths['summary_path'] or phase3.get('summary_path') or phase2.get('summary_path')
    paths['filters_path'] = paths['filters_path'] or phase2.get('filters_path') or phase3.get('filters_path')
    paths['local_combo_path'] = paths['local_combo_path'] or phase2.get('local_combo_path')
    paths['global_combo_path'] = paths['global_combo_path'] or phase2.get('global_combo_path')
    paths['ranges_path'] = paths['ranges_path'] or phase2.get('ranges_path') or phase3.get('ranges_path')
    paths['segment_code_path'] = phase2.get('segment_code_path')
    paths['segment_code_final_path'] = phase2.get('segment_code_final_path')
    paths['thresholds_path'] = phase2.get('thresholds_path')
    return paths


def _describe_detail_paths(paths: dict) -> list[str]:
    labels = {
        'summary_path': '세그먼트 요약',
        'filters_path': '세그먼트 필터 후보',
        'local_combo_path': '세그먼트 로컬 조합',
        'global_combo_path': '전역 조합 요약',
        'ranges_path': '세그먼트 구간 정의',
        'segment_code_path': '세그먼트 조건식 코드',
        'segment_code_final_path': '세그먼트 최종 조건식 코드(매수조건 통합)',
        'thresholds_path': 'Optuna 임계값 결과',
    }
    lines = []
    for key, label in labels.items():
        path = paths.get(key)
        if path:
            lines.append(f"- {label}: {path}")
        else:
            lines.append(f"- {label}: 없음")
    return lines


def _summarize_ranges(df_ranges: pd.DataFrame) -> list[str]:
    lines = []
    df = df_ranges.copy()
    for range_type in ('market_cap', 'time'):
        sub = df[df['range_type'] == range_type]
        if sub.empty:
            continue
        label = "시가총액" if range_type == 'market_cap' else "시간"
        lines.append(f"- {label} 구간:")
        for _, row in sub.iterrows():
            name = row.get('label')
            min_v = row.get('min')
            max_v = row.get('max')
            source = row.get('source')
            if pd.isna(max_v):
                desc = f"{_fmt_num(min_v)} 이상"
            else:
                desc = f"{_fmt_num(min_v)} ~ {_fmt_num(max_v)}"
            tail = f" ({source})" if source else ""
            lines.append(f"  - {name}: {desc}{tail}")
    return lines


def _summarize_segment_summary(df_summary: pd.DataFrame) -> list[str]:
    lines = []
    df = df_summary.copy()
    total_trades = int(df['trades'].sum()) if 'trades' in df.columns else 0
    lines.append(f"- 총 거래수: {total_trades:,}건")

    out_row = df[df['segment_id'] == 'Out_of_Range']
    if not out_row.empty and total_trades > 0:
        out_trades = int(out_row.iloc[0].get('trades', 0) or 0)
        lines.append(f"- 구간 외 거래: {out_trades:,}건 ({out_trades / total_trades * 100:.1f}%)")

    df_main = df[df['segment_id'] != 'Out_of_Range']
    if not df_main.empty:
        top_profit = df_main.sort_values('profit', ascending=False).head(3)
        worst_profit = df_main.sort_values('profit', ascending=True).head(3)
        lines.append("- 수익 상위 세그먼트:")
        for _, row in top_profit.iterrows():
            lines.append(f"  - {row.get('segment_id')}: {_fmt_signed(row.get('profit'))}")
        lines.append("- 수익 하위 세그먼트:")
        for _, row in worst_profit.iterrows():
            lines.append(f"  - {row.get('segment_id')}: {_fmt_signed(row.get('profit'))}")
    return lines


def _summarize_filters(df_filters: pd.DataFrame, max_per_segment: int = 5) -> list[str]:
    lines = []
    df = df_filters.copy()
    if 'efficiency' in df.columns:
        df['efficiency'] = pd.to_numeric(df['efficiency'], errors='coerce').fillna(0.0)
    df['improvement'] = pd.to_numeric(df.get('improvement'), errors='coerce').fillna(0.0)

    for seg_id in sorted(df['segment_id'].dropna().unique()):
        seg_df = df[df['segment_id'] == seg_id]
        if seg_df.empty:
            continue
        if 'efficiency' in seg_df.columns:
            seg_df = seg_df.sort_values(['efficiency', 'improvement'], ascending=[False, False])
        else:
            seg_df = seg_df.sort_values('improvement', ascending=False)

        lines.append(f"- {seg_id}:")
        for _, row in seg_df.head(max_per_segment).iterrows():
            fname = row.get('filter_name') or row.get('column')
            improvement = _fmt_signed(row.get('improvement'))
            exclusion = _fmt_pct(row.get('exclusion_ratio'))
            p_value = _fmt_float(row.get('p_value'), digits=4)
            effect = _fmt_float(row.get('effect_size'), digits=3)
            lines.append(
                f"  - {fname}: 개선 {improvement}, 제외 {exclusion}, p={p_value}, 효과 {effect}"
            )
    return lines


def _summarize_local_combos(df_local: pd.DataFrame, max_per_segment: int = 3) -> list[str]:
    lines = []
    df = df_local.copy()
    for seg_id in sorted(df['segment_id'].dropna().unique()):
        seg_df = df[df['segment_id'] == seg_id]
        if seg_df.empty:
            continue
        seg_df = seg_df.sort_values(['improvement', 'combo_rank'], ascending=[False, True])
        lines.append(f"- {seg_id}:")
        for _, row in seg_df.head(max_per_segment).iterrows():
            filters = row.get('filters') or ''
            improvement = _fmt_signed(row.get('improvement'))
            remaining = _fmt_int(row.get('remaining_trades'))
            exclusion = _fmt_pct(row.get('exclusion_ratio'))
            lines.append(
                f"  - #{row.get('combo_rank')}: {filters} | 개선 {improvement} | 잔여 {remaining}건 | 제외 {exclusion}"
            )
    return lines


def _summarize_global_combo(df_combo: pd.DataFrame) -> list[str]:
    lines = []
    row = df_combo.iloc[0]
    lines.append(f"- 개선금액: {_fmt_signed(row.get('total_improvement'))}")
    lines.append(f"- 잔여비율: {_fmt_pct(row.get('remaining_ratio'))}")
    lines.append(f"- MDD(%): {_fmt_pct(row.get('mdd_pct'))}")
    lines.append(f"- 변동성(수익금): {_fmt_float(row.get('profit_volatility'))}")
    filters = row.get('filters')
    if isinstance(filters, str) and filters:
        if len(filters) > 240:
            filters = filters[:237] + "..."
        lines.append(f"- 필터 조합: {filters}")
    return lines


def _read_csv_safe(path: Optional[str]) -> pd.DataFrame:
    if not path:
        return pd.DataFrame()
    p = Path(str(path))
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p, encoding='utf-8-sig')
    except Exception:
        return pd.DataFrame()


def _fmt_int(value: object) -> str:
    try:
        return f"{int(float(value)):,}"
    except Exception:
        return "N/A"


def _fmt_signed(value: object) -> str:
    try:
        v = float(value)
    except Exception:
        return "N/A"
    sign = "+" if v >= 0 else ""
    return f"{sign}{int(v):,}원"


def _fmt_pct(value: object) -> str:
    try:
        v = float(value)
    except Exception:
        return "N/A"
    if v > 1.5:
        return f"{v:.2f}%"
    return f"{v * 100:.2f}%"


def _fmt_float(value: object, digits: int = 2) -> str:
    try:
        v = float(value)
    except Exception:
        return "N/A"
    return f"{v:.{digits}f}"


def _fmt_num(value: object) -> str:
    try:
        v = float(value)
    except Exception:
        return "N/A"
    if v.is_integer():
        return f"{int(v):,}"
    return f"{v:,.2f}"
