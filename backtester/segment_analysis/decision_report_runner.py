# -*- coding: utf-8 -*-
"""
Decision Report Runner

산출물 기반 의사결정 리포트를 자동 생성합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import json
import pandas as pd

from .segment_outputs import save_decision_report


@dataclass
class DecisionReportConfig:
    output_dir: str = 'backtester/segment_outputs'
    prefix: Optional[str] = None
    min_remaining_ratio: float = 0.2
    max_mdd_increase_pp: float = 20.0
    min_improvement: float = 0.0
    top_n_candidates: int = 3


def run_decision_report(detail_path: str, config: Optional[DecisionReportConfig] = None) -> dict:
    config = config or DecisionReportConfig()
    detail_path = Path(detail_path).expanduser().resolve()
    output_prefix = config.prefix or _build_prefix(detail_path.name)
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = _resolve_sources(output_dir, output_prefix)
    mode_df = _read_csv_safe(sources.get('mode_comparison'))
    pareto_df = _read_csv_safe(sources.get('pareto_front'))
    optuna_df = _read_csv_safe(sources.get('advanced_optuna'))
    nsga_df = _read_csv_safe(sources.get('nsga2_front'))
    ranges_df = _read_csv_safe(sources.get('segment_ranges'))

    decision = _decide_mode(mode_df, config)
    rationale = _build_rationale(decision, mode_df, config)
    candidate_summary = _summarize_candidates(pareto_df, optuna_df, nsga_df, config)

    md_path = output_dir / f"{output_prefix}_decision_report.md"
    json_path = output_dir / f"{output_prefix}_decision_report.json"
    score_path = None
    score_df = decision.get('ranking_df')
    if isinstance(score_df, pd.DataFrame) and not score_df.empty:
        score_path = save_decision_report(score_df, str(output_dir), output_prefix)

    md_text = _build_markdown(
        prefix=output_prefix,
        sources=sources,
        decision=decision,
        rationale=rationale,
        candidate_summary=candidate_summary,
        config=config,
    )
    md_path.write_text(md_text, encoding='utf-8-sig')

    payload = {
        'prefix': output_prefix,
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'decision': {
            'recommended_mode': decision.get('recommended_mode'),
            'status': decision.get('status'),
            'metrics': decision.get('metrics'),
        },
        'criteria': {
            'min_remaining_ratio': config.min_remaining_ratio,
            'max_mdd_increase_pp': config.max_mdd_increase_pp,
            'min_improvement': config.min_improvement,
        },
        'sources': sources,
        'candidates': candidate_summary,
    }

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8-sig')

    return {
        'decision_report': str(md_path),
        'decision_json': str(json_path),
        'decision_score': score_path,
        'recommended_mode': decision.get('recommended_mode'),
        'status': decision.get('status'),
    }


def _resolve_sources(output_dir: Path, prefix: str) -> dict:
    def _p(name: str) -> str:
        return str(output_dir / f"{prefix}_{name}")

    return {
        'mode_comparison': _p("segment_mode_comparison.csv"),
        'pareto_front': _p("pareto_front.csv"),
        'advanced_optuna': _p("advanced_optuna.csv"),
        'nsga2_front': _p("nsga2_front.csv"),
        'segment_ranges': _p("segment_ranges.csv"),
    }


def _read_csv_safe(path_str: Optional[str]) -> pd.DataFrame:
    if not path_str:
        return pd.DataFrame()
    path = Path(path_str)
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding='utf-8-sig')
    except Exception:
        return pd.DataFrame()


def _decide_mode(mode_df: pd.DataFrame, config: DecisionReportConfig) -> dict:
    if mode_df is None or mode_df.empty:
        return {
            'recommended_mode': None,
            'status': 'no_data',
            'metrics': {},
            'ranking_df': pd.DataFrame(),
        }

    df = mode_df.copy()
    df['total_improvement'] = pd.to_numeric(df.get('total_improvement'), errors='coerce').fillna(0.0)
    df['remaining_ratio'] = pd.to_numeric(df.get('remaining_ratio'), errors='coerce').fillna(0.0)
    df['mdd_pct'] = pd.to_numeric(df.get('mdd_pct'), errors='coerce').fillna(0.0)
    df['profit_volatility'] = pd.to_numeric(df.get('profit_volatility'), errors='coerce').fillna(0.0)

    baseline = df[df['mode'] == 'fixed']
    baseline_mdd = float(baseline['mdd_pct'].iloc[0]) if not baseline.empty else None

    df['eligible'] = (
        (df['total_improvement'] > config.min_improvement) &
        (df['remaining_ratio'] >= config.min_remaining_ratio)
    )

    if baseline_mdd is not None:
        df['mdd_risk'] = df['mdd_pct'] > (baseline_mdd + config.max_mdd_increase_pp)
    else:
        df['mdd_risk'] = False

    df['score'] = _score_rows(df)
    ranking = df.sort_values(['eligible', 'mdd_risk', 'score'], ascending=[False, True, False])

    best = ranking[ranking['eligible']]
    if baseline_mdd is not None:
        best = best[~best['mdd_risk']]
    if best.empty:
        best = ranking.head(1)
        status = 'fallback'
    else:
        status = 'selected'

    rec = best.iloc[0]
    metrics = {
        'total_improvement': float(rec.get('total_improvement', 0.0)),
        'remaining_ratio': float(rec.get('remaining_ratio', 0.0)),
        'mdd_pct': float(rec.get('mdd_pct', 0.0)),
        'profit_volatility': float(rec.get('profit_volatility', 0.0)),
    }

    return {
        'recommended_mode': rec.get('mode'),
        'status': status,
        'metrics': metrics,
        'ranking_df': ranking.reset_index(drop=True),
    }


def _score_rows(df: pd.DataFrame) -> pd.Series:
    profit_norm = _normalize_series(df['total_improvement'])
    remain_norm = _normalize_series(df['remaining_ratio'])
    mdd_norm = 1.0 - _normalize_series(df['mdd_pct'])
    vol_norm = 1.0 - _normalize_series(df['profit_volatility'])
    return profit_norm * 0.4 + remain_norm * 0.3 + mdd_norm * 0.2 + vol_norm * 0.1


def _normalize_series(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce').fillna(0.0)
    min_v = float(values.min())
    max_v = float(values.max())
    if max_v == min_v:
        return pd.Series([0.0] * len(values), index=values.index)
    return (values - min_v) / (max_v - min_v)


def _build_rationale(decision: dict, mode_df: pd.DataFrame, config: DecisionReportConfig) -> list[str]:
    lines = []
    rec = decision.get('recommended_mode')
    status = decision.get('status')
    metrics = decision.get('metrics') or {}

    if status == 'no_data':
        return ["비교 데이터가 없어 의사결정을 수행할 수 없습니다."]

    lines.append(f"- 추천 모드: {rec} (status={status})")
    lines.append(f"- 개선금액: {int(metrics.get('total_improvement', 0)):,}원")
    lines.append(f"- 잔여비율: {metrics.get('remaining_ratio', 0):.2f}")
    lines.append(f"- MDD(%): {metrics.get('mdd_pct', 0):.2f}")
    lines.append(f"- 변동성(수익금): {metrics.get('profit_volatility', 0):.2f}")

    if mode_df is not None and not mode_df.empty and 'mode' in mode_df.columns:
        fixed = mode_df[mode_df['mode'] == 'fixed']
        if not fixed.empty:
            base_mdd = float(pd.to_numeric(fixed['mdd_pct'], errors='coerce').fillna(0.0).iloc[0])
            lines.append(f"- 기준(fixed) MDD: {base_mdd:.2f} (허용 +{config.max_mdd_increase_pp:.1f}p)")

    lines.append(f"- 기준: remaining_ratio ≥ {config.min_remaining_ratio:.2f}")
    return lines


def _summarize_candidates(
    pareto_df: pd.DataFrame,
    optuna_df: pd.DataFrame,
    nsga_df: pd.DataFrame,
    config: DecisionReportConfig,
) -> dict:
    summary = {}

    if pareto_df is not None and not pareto_df.empty:
        top = pareto_df.sort_values('total_improvement', ascending=False).head(config.top_n_candidates)
        summary['pareto_top'] = top[['combo_id', 'total_improvement', 'remaining_ratio', 'mdd_pct']].to_dict(orient='records')

    if optuna_df is not None and not optuna_df.empty:
        row = optuna_df.iloc[0].to_dict()
        summary['optuna_best'] = {
            'combo_id': row.get('combo_id'),
            'total_improvement': row.get('total_improvement'),
            'remaining_ratio': row.get('remaining_ratio'),
            'mdd_pct': row.get('mdd_pct'),
            'weights': {
                'w_profit': row.get('w_profit'),
                'w_remain': row.get('w_remain'),
                'w_mdd': row.get('w_mdd'),
                'w_vol': row.get('w_vol'),
            },
        }

    if nsga_df is not None and not nsga_df.empty:
        top = nsga_df.sort_values('total_improvement', ascending=False).head(config.top_n_candidates)
        summary['nsga2_top'] = top[['combo_id', 'total_improvement', 'remaining_ratio', 'mdd_pct']].to_dict(orient='records')

    return summary


def _build_markdown(
    prefix: str,
    sources: dict,
    decision: dict,
    rationale: list[str],
    candidate_summary: dict,
    config: DecisionReportConfig,
) -> str:
    lines = []
    lines.append(f"# 세그먼트 의사결정 리포트 ({prefix})")
    lines.append("")
    lines.append(f"- 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 기준: 개선금액>{config.min_improvement}, 잔여비율≥{config.min_remaining_ratio}, MDD 허용 +{config.max_mdd_increase_pp}p")
    lines.append("")

    lines.append("## 1) 입력 산출물")
    for key, path in sources.items():
        lines.append(f"- {key}: {path}")

    lines.append("")
    lines.append("## 2) 추천 결과")
    if decision.get('status') == 'no_data':
        lines.append("- 비교 데이터가 없어 추천을 수행하지 못했습니다.")
    else:
        lines.extend(rationale)

    lines.append("")
    lines.append("## 3) 후보 요약")
    if not candidate_summary:
        lines.append("- 후보 산출물이 없습니다.")
    else:
        if 'pareto_top' in candidate_summary:
            lines.append("- Pareto Top:")
            for row in candidate_summary['pareto_top']:
                lines.append(f"  - {row}")
        if 'optuna_best' in candidate_summary:
            lines.append(f"- Optuna Best: {candidate_summary['optuna_best']}")
        if 'nsga2_top' in candidate_summary:
            lines.append("- NSGA-II Top:")
            for row in candidate_summary['nsga2_top']:
                lines.append(f"  - {row}")

    lines.append("")
    lines.append("## 4) 의사결정 메모")
    lines.append("- 비교 결과를 운영 적용 전 검증환경에서 재확인하세요.")
    lines.append("- 분할 구간 급변 시 해석 가능성이 저하될 수 있습니다.")
    return "\n".join(lines)


def _build_prefix(filename: str) -> str:
    if filename.endswith('_detail.csv'):
        return filename.replace('_detail.csv', '')
    return filename.replace('.csv', '')


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m backtester.segment_analysis.decision_report_runner <detail.csv>")

    result = run_decision_report(sys.argv[1])
    print(f"[Decision] Report: {result['decision_report']}")
