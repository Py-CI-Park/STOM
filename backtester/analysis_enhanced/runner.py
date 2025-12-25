# -*- coding: utf-8 -*-
import time
from pathlib import Path
from traceback import print_exc

import pandas as pd

from backtester.output_paths import ensure_backtesting_output_dir
from backtester.detail_schema import reorder_detail_columns
from .metrics import CalculateEnhancedDerivedMetrics
from .ml import (
    AssessMlReliability,
    AnalyzeFeatureImportance,
    PredictRiskWithML,
)
from .thresholds import FindAllOptimalThresholds
from .filters import (
    AnalyzeFilterCombinations,
    AnalyzeFilterEffectsEnhanced,
    AnalyzeFilterEffectsLookahead,
    AnalyzeFilterStability,
    GenerateFilterCode,
)
from .plotting import PltEnhancedAnalysisCharts
from .utils import ComputeStrategyKey

def RunEnhancedAnalysis(df_tsg, save_file_name, teleQ=None, buystg=None, sellstg=None,
                        buystg_name=None, sellstg_name=None, backname=None,
                        ml_train_mode: str = 'train', send_condition_summary: bool = True,
                        segment_analysis_mode: str = 'off',
                        segment_output_dir: str | None = None,
                        segment_optuna: bool = False,
                        segment_template_compare: bool = False):
    """
    강화된 전체 분석을 실행합니다.

    기능:
    1. 강화된 파생 지표 계산
    2. 통계적 유의성 검증 포함 필터 분석
    3. 최적 임계값 탐색
    4. 필터 조합 분석
    5. ML 기반 특성 중요도
    6. 기간별 필터 안정성
    7. 조건식 코드 자동 생성
    8. 강화된 시각화
    9. 세그먼트 분석(Phase2/3) 통합(옵션)

    Returns:
        dict: 분석 결과 요약
    """
    result = {
        'enhanced_df': None,
        'filter_results': [],
        'filter_results_lookahead': [],
        'optimal_thresholds': [],
        'filter_combinations': [],
        'feature_importance': None,
        'filter_stability': [],
        'generated_code': None,
        'charts': [],
        'recommendations': [],
        'csv_files': [],
        'ml_prediction_stats': None,  # NEW: ML 예측 통계
        'ml_reliability': None,       # NEW: ML 신뢰도/게이트 결과
        'segment_outputs': None,      # NEW: 세그먼트 분석 산출물
    }

    try:
        # 1. 강화된 파생 지표 계산
        df_enhanced = CalculateEnhancedDerivedMetrics(df_tsg)
        
        # 1.5. ML 기반 위험도 예측 (NEW)
        # - 손실확률_ML: ML이 예측한 손실 확률 (0~1)
        # - 위험도_ML: ML 기반 위험도 점수 (0~100)
        # - 예측매수매도위험도점수_ML: 매수 시점 변수로 예측한 매수매도위험도점수(0~100)
        # - detail.csv에 추가하여 실제 매수매도위험도점수와 비교 가능
        df_enhanced, ml_prediction_stats = PredictRiskWithML(
            df_enhanced,
            save_file_name=save_file_name,
            buystg=buystg,
            sellstg=sellstg,
            train_mode=ml_train_mode
        )
        result['ml_prediction_stats'] = ml_prediction_stats

        ml_reliability = AssessMlReliability(ml_prediction_stats)
        result['ml_reliability'] = ml_reliability
        allow_ml_filters = bool((ml_reliability or {}).get('allow_ml_filters', False))
        try:
            if isinstance(ml_prediction_stats, dict):
                ml_prediction_stats['reliability'] = ml_reliability
        except Exception:
            pass
        
        result['enhanced_df'] = df_enhanced

        # 2. 강화된 필터 효과 분석 (통계 검정 포함)
        filter_results = AnalyzeFilterEffectsEnhanced(df_enhanced, allow_ml_filters=allow_ml_filters)
        result['filter_results'] = filter_results

        # 2-1. (진단용) 룩어헤드 포함 필터 효과 분석
        filter_results_lookahead = AnalyzeFilterEffectsLookahead(df_enhanced)
        result['filter_results_lookahead'] = filter_results_lookahead

        # 3. 최적 임계값 탐색
        optimal_thresholds = FindAllOptimalThresholds(df_enhanced)
        result['optimal_thresholds'] = optimal_thresholds

        # 4. 필터 조합 분석 (단일 필터 결과 재사용으로 중복 계산 제거)
        filter_combinations = AnalyzeFilterCombinations(df_enhanced, single_filters=filter_results)
        result['filter_combinations'] = filter_combinations

        # 5. ML 특성 중요도
        feature_importance = AnalyzeFeatureImportance(df_enhanced)
        result['feature_importance'] = feature_importance

        # 6. 필터 안정성 검증
        filter_stability = AnalyzeFilterStability(df_enhanced)
        result['filter_stability'] = filter_stability

        # 7. 조건식 코드 생성
        generated_code = GenerateFilterCode(filter_results, df_tsg=df_enhanced, allow_ml_filters=allow_ml_filters)
        result['generated_code'] = generated_code

        # 8. CSV 파일 저장
        # 상세 거래 기록 (강화 분석 사용 시: detail.csv로 통합하여 중복 생성 방지)
        # - 손실확률_ML, 위험도_ML, 예측매수매도위험도점수_ML 컬럼이 포함되어 비교 가능
        output_dir = ensure_backtesting_output_dir(save_file_name)
        detail_path = str(output_dir / f"{save_file_name}_detail.csv")
        df_enhanced_out = reorder_detail_columns(df_enhanced)
        df_enhanced_out.to_csv(detail_path, encoding='utf-8-sig', index=True)
        result['csv_files'].append(detail_path)

        # 필터 분석 결과
        if filter_results:
            # 강화 분석 사용 시: filter.csv로 통합하여 중복 생성 방지
            filter_path = str(output_dir / f"{save_file_name}_filter.csv")
            pd.DataFrame(filter_results).to_csv(filter_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(filter_path)

        # (진단용) 룩어헤드 포함 필터 분석 결과
        if filter_results_lookahead:
            lookahead_path = str(output_dir / f"{save_file_name}_filter_lookahead.csv")
            pd.DataFrame(filter_results_lookahead).to_csv(lookahead_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(lookahead_path)

        # 최적 임계값
        if optimal_thresholds:
            threshold_path = str(output_dir / f"{save_file_name}_optimal_thresholds.csv")
            pd.DataFrame(optimal_thresholds).to_csv(threshold_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(threshold_path)

        # 필터 조합
        if filter_combinations:
            combo_path = str(output_dir / f"{save_file_name}_filter_combinations.csv")
            df_combo = pd.DataFrame(filter_combinations)
            if '조합개선' in df_combo.columns:
                sort_cols = ['조합개선']
                sort_asc = [False]
                if '시너지효과' in df_combo.columns:
                    sort_cols.append('시너지효과')
                    sort_asc.append(False)
                df_combo = df_combo.sort_values(sort_cols, ascending=sort_asc)

            df_combo = df_combo.rename(columns={
                '조합유형': '조합유형(필터개수)',
                '개별개선합': '개별개선합(원=각필터단독개선합)',
                '조합개선': '조합개선(원=조합적용개선금액)',
                '시너지효과': '시너지효과(원=조합개선-개별개선합)',
                '시너지비율': '시너지비율(%=시너지효과/개별개선합)',
                '제외비율': '제외비율(%=조합적용시제외)',
                '잔여승률': '잔여승률(%=조합적용후)',
                '잔여거래수': '잔여거래수(건)',
                '권장': '권장(시너지기준)'
            })

            df_combo.to_csv(combo_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(combo_path)

        # 필터 안정성
        if filter_stability:
            stability_path = str(output_dir / f"{save_file_name}_filter_stability.csv")
            pd.DataFrame(filter_stability).to_csv(stability_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(stability_path)

        # 9. 강화된 차트 생성
        chart_path = PltEnhancedAnalysisCharts(
            df_enhanced,
            save_file_name,
            teleQ,
            filter_results=filter_results,
            filter_results_lookahead=filter_results_lookahead,
            feature_importance=feature_importance,
            optimal_thresholds=optimal_thresholds,
            filter_combinations=filter_combinations,
            filter_stability=filter_stability,
            generated_code=generated_code,
            buystg=buystg,
            sellstg=sellstg
        )
        if chart_path:
            result['charts'].append(chart_path)

        # 9-1. 세그먼트 분석(옵션)
        segment_outputs = None
        if segment_analysis_mode and str(segment_analysis_mode).lower() not in ('off', 'false', 'none'):
            try:
                from backtester.segment_analysis.phase2_runner import run_phase2, Phase2RunnerConfig
                from backtester.segment_analysis.phase3_runner import run_phase3, Phase3RunnerConfig
                from backtester.segment_analysis.filter_evaluator import FilterEvaluatorConfig
                from backtester.segment_analysis.segment_template_comparator import (
                    run_segment_template_comparison,
                    SegmentTemplateComparisonConfig,
                )

                mode = str(segment_analysis_mode).lower()
                segment_output_base = segment_output_dir or str(output_dir)
                filter_config = FilterEvaluatorConfig(allow_ml_filters=allow_ml_filters)
                segment_outputs = {}
                segment_timing = {}
                segment_start = time.perf_counter()

                if mode in ('phase2', 'phase2+3', 'phase2_phase3', 'all', 'auto'):
                    t0 = time.perf_counter()
                    segment_outputs['phase2'] = run_phase2(
                        detail_path,
                        filter_config=filter_config,
                        runner_config=Phase2RunnerConfig(
                            output_dir=segment_output_base,
                            prefix=save_file_name,
                            enable_optuna=segment_optuna
                        )
                    )
                    segment_timing['phase2_s'] = round(time.perf_counter() - t0, 4)

                if mode in ('phase3', 'phase2+3', 'phase2_phase3', 'all', 'auto'):
                    t0 = time.perf_counter()
                    segment_outputs['phase3'] = run_phase3(
                        detail_path,
                        filter_config=filter_config,
                        runner_config=Phase3RunnerConfig(
                            output_dir=segment_output_base,
                            prefix=save_file_name
                        )
                    )
                    segment_timing['phase3_s'] = round(time.perf_counter() - t0, 4)

                if segment_template_compare and mode in ('phase2', 'phase2+3', 'phase2_phase3', 'all', 'auto', 'compare', 'template'):
                    t0 = time.perf_counter()
                    segment_outputs['template_comparison'] = run_segment_template_comparison(
                        detail_path,
                        filter_config=filter_config,
                        runner_config=SegmentTemplateComparisonConfig(
                            output_dir=segment_output_base,
                            prefix=save_file_name,
                            max_templates=4,
                            top_n_dynamic=1,
                            enable_dynamic_expansion=True,
                            enable_optuna=segment_optuna,
                        ),
                    )
                    segment_timing['template_s'] = round(time.perf_counter() - t0, 4)

                segment_timing['total_s'] = round(time.perf_counter() - segment_start, 4)
                segment_outputs['timing'] = segment_timing

                try:
                    from backtester.segment_analysis.segment_summary_report import write_segment_summary_report

                    summary_path = write_segment_summary_report(
                        segment_output_base,
                        save_file_name,
                        segment_outputs,
                    )
                    if summary_path:
                        segment_outputs['summary_report_path'] = summary_path
                except Exception:
                    print_exc()
            except Exception:
                print_exc()

        result['segment_outputs'] = segment_outputs

        # 10. 추천 메시지 생성
        recommendations = []

        # 통계적으로 유의한 필터
        filter_results_safe = filter_results or []
        filter_combinations_safe = filter_combinations or []
        filter_stability_safe = filter_stability or []

        significant_filters = [
            f for f in filter_results_safe
            if f.get('유의함') == '예' and float(f.get('수익개선금액', 0) or 0) > 0
        ][:3]
        for f in significant_filters:
            try:
                recommendations.append(
                    f"[통계적 유의] {f.get('필터명', '')}: +{int(f.get('수익개선금액', 0) or 0):,}원 (p={f.get('p값', 'N/A')})"
                )
            except Exception:
                continue

        # 시너지 높은 조합
        high_synergy = [c for c in filter_combinations_safe if float(c.get('시너지비율', 0) or 0) > 10][:2]
        for c in high_synergy:
            try:
                recommendations.append(
                    f"[조합추천] {str(c.get('필터1', ''))[:15]} + {str(c.get('필터2', ''))[:15]}: "
                    f"시너지 +{int(c.get('시너지효과', 0) or 0):,}원"
                )
            except Exception:
                continue

        # 안정적인 필터
        stable_filters = [
            f for f in filter_stability_safe
            if f.get('안정성등급') == '안정' and float(f.get('평균개선', 0) or 0) > 0
        ][:2]
        for f in stable_filters:
            try:
                recommendations.append(
                    f"[안정성] {f.get('필터명', '')}: 일관성 {f.get('일관성점수', 'N/A')}점"
                )
            except Exception:
                continue

        result['recommendations'] = recommendations

        # 11. 텔레그램 전송
        if teleQ is not None:
            def _safe_put(text: str):
                try:
                    teleQ.put(text)
                except Exception:
                    pass

            # 매수/매도 조건식(이름만)
            if send_condition_summary:
                try:
                    if buystg_name or sellstg_name or buystg or sellstg:
                        sk = None
                        try:
                            if isinstance(ml_prediction_stats, dict):
                                sk = ml_prediction_stats.get('strategy_key')
                        except Exception:
                            sk = None
                        if not sk:
                            sk = ComputeStrategyKey(buystg=buystg, sellstg=sellstg)

                        sk_short = (str(sk)[:12] + '...') if sk else 'N/A'
                        is_opt = bool(backname and ('최적화' in str(backname)))
                        buy_label = "매수 최적화 조건식" if is_opt else "매수 조건식"
                        sell_label = "매도 최적화 조건식" if is_opt else "매도 조건식"

                        buy_name = buystg_name if buystg_name else 'N/A'
                        sell_name = sellstg_name if sellstg_name else 'N/A'

                        lines = []
                        lines.append("매수/매도 조건식(이름):")
                        lines.append(f"- 전략키: {sk_short}")
                        lines.append(f"- {buy_label}: {buy_name}")
                        lines.append(f"- {sell_label}: {sell_name}")
                        lines.append("- 전체 원문/산출물 목록은 report.txt 및 models/strategy_code.txt 참고")
                        _safe_put("\n".join(lines))
                except Exception:
                    pass

            # ML 예측 통계 메시지 (NEW)
            if ml_prediction_stats:
                ml_lines = []
                ml_lines.append("머신러닝 변수 예측 결과:")
                ml_lines.append(f"- 모델: {ml_prediction_stats.get('model_type', 'N/A')}")
                ml_lines.append(
                    f"- 테스트(AUC/F1/BA): "
                    f"{ml_prediction_stats.get('test_auc', 'N/A')}% / "
                    f"{ml_prediction_stats.get('test_f1', 'N/A')}% / "
                    f"{ml_prediction_stats.get('test_balanced_accuracy', 'N/A')}%"
                )
                ml_lines.append(f"- 사용 피처: {ml_prediction_stats.get('total_features', 0)}개")
                ml_lines.append("- 예측 변수: 손실확률_ML, 위험도_ML, 예측매수매도위험도점수_ML")

                # 소요 시간(학습/예측/저장) 요약
                try:
                    tinfo = ml_prediction_stats.get('timing') if isinstance(ml_prediction_stats, dict) else None
                    if isinstance(tinfo, dict):
                        def _fmt_sec(v):
                            try:
                                return f"{float(v):.2f}s"
                            except Exception:
                                return str(v)

                        total_s = tinfo.get('total_s')
                        parts = []
                        if tinfo.get('load_latest_s') is not None:
                            parts.append(f"load { _fmt_sec(tinfo.get('load_latest_s')) }")
                        if tinfo.get('train_classifiers_s') is not None:
                            parts.append(f"train { _fmt_sec(tinfo.get('train_classifiers_s')) }")
                        if tinfo.get('predict_all_s') is not None:
                            parts.append(f"predict { _fmt_sec(tinfo.get('predict_all_s')) }")
                        if tinfo.get('save_bundle_s') is not None:
                            parts.append(f"save { _fmt_sec(tinfo.get('save_bundle_s')) }")
                        if total_s is not None:
                            if parts:
                                ml_lines.append(f"- 소요 시간: {_fmt_sec(total_s)} ({', '.join(parts)})")
                            else:
                                ml_lines.append(f"- 소요 시간: {_fmt_sec(total_s)}")
                except Exception:
                    pass

                # ML 신뢰도(게이트) 결과: 기준 미달이면 *_ML 필터 자동 생성/추천에서 제외
                try:
                    rel = None
                    if isinstance(ml_prediction_stats, dict):
                        rel = ml_prediction_stats.get('reliability')
                    if not isinstance(rel, dict):
                        rel = result.get('ml_reliability') if isinstance(result, dict) else None
                    if isinstance(rel, dict):
                        allow_ml = bool(rel.get('allow_ml_filters', False))
                        crit = rel.get('criteria') or {}
                        crit_txt = (
                            f"AUC≥{crit.get('min_test_auc')}%, "
                            f"F1≥{crit.get('min_test_f1')}%, "
                            f"BA≥{crit.get('min_test_balanced_accuracy')}%"
                        )
                        ml_lines.append(f"- 신뢰도 판정: {'PASS' if allow_ml else 'FAIL'} ({crit_txt})")
                        if not allow_ml:
                            reasons = rel.get('reasons') or []
                            for r in reasons[:2]:
                                ml_lines.append(f"  - {r}")
                            ml_lines.append("- *_ML 기반 필터: 자동 생성/추천에서 제외됨")
                except Exception:
                    pass
                 
                # 상관관계 정보
                corr_actual = ml_prediction_stats.get('correlation_with_actual_risk')
                corr_rule = ml_prediction_stats.get('correlation_with_rule_risk')
                if corr_actual is not None:
                    ml_lines.append(f"- 실제 매수매도위험도 상관: {corr_actual}%")
                if corr_rule is not None:
                    ml_lines.append(f"- 규칙기반 위험도점수 상관: {corr_rule}%")

                # 매수매도위험도 회귀 예측(룩어헤드 위험도 점수 근사)
                risk_reg = ml_prediction_stats.get('risk_regression') if isinstance(ml_prediction_stats, dict) else None
                if isinstance(risk_reg, dict) and risk_reg.get('best_model'):
                    corr_txt = f", 상관 {risk_reg.get('test_corr')}%" if risk_reg.get('test_corr') is not None else ""
                    ml_lines.append(
                        f"- 매수매도위험도 예측(회귀): MAE {risk_reg.get('test_mae', 'N/A')}점, "
                        f"R2 {risk_reg.get('test_r2', 'N/A')}{corr_txt} ({risk_reg.get('best_model')})"
                    )

                # 모델 저장 정보
                artifacts = ml_prediction_stats.get('artifacts') if isinstance(ml_prediction_stats, dict) else None
                if isinstance(artifacts, dict):
                    sk = ml_prediction_stats.get('strategy_key') or artifacts.get('strategy_key')
                    sk_short = (str(sk)[:12] + '...') if sk else 'N/A'
                    if artifacts.get('saved'):
                        ml_lines.append(f"- 모델 저장: 성공 (전략키 {sk_short})")
                        p = artifacts.get('latest_bundle_path') or artifacts.get('run_bundle_path')
                        if p:
                            try:
                                ml_lines.append(f"- 모델 파일: {Path(p).name}")
                            except Exception:
                                pass
                    else:
                        err = artifacts.get('error')
                        ml_lines.append(f"- 모델 저장: 실패/미수행 ({err})" if err else "- 모델 저장: 실패/미수행")
                
                # 주요 피처
                top_features = ml_prediction_stats.get('top_features', [])[:5]
                if top_features:
                    ml_lines.append("- 주요 피처(중요도):")
                    for feat, imp in top_features:
                        ml_lines.append(f"  - {feat}: {imp:.3f}")
                
                ml_lines.append("- detail.csv에 '손실확률_ML', '위험도_ML', '예측매수매도위험도점수_ML' 컬럼 추가됨")
                
                _safe_put("\n".join(ml_lines))

            # 요약 메시지
            if recommendations:
                msg = "강화된 필터 분석 결과:\n\n" + "\n".join(recommendations)
                _safe_put(msg)
            else:
                # 추천 메시지가 비어 있어도 "왜 비었는지" 요약을 보내도록 보강
                try:
                    pos_filters = sum(1 for f in filter_results_safe if float(f.get('수익개선금액', 0) or 0) > 0)
                    sig_pos_filters = sum(
                        1 for f in filter_results_safe
                        if f.get('유의함') == '예' and float(f.get('수익개선금액', 0) or 0) > 0
                    )
                except Exception:
                    pos_filters = 0
                    sig_pos_filters = 0

                msg = (
                    "강화된 필터 분석 결과:\n"
                    "- 추천 조건을 만족하는 항목이 없어 요약만 전송합니다.\n"
                    f"- 필터 결과: 총 {len(filter_results_safe):,}개 (개선(+) {pos_filters:,}개, 유의(+) {sig_pos_filters:,}개)\n"
                    f"- 조합 분석: {len(filter_combinations_safe):,}개\n"
                    f"- 안정성 분석: {len(filter_stability_safe):,}개\n"
                    f"- 코드 생성: {'가능' if (generated_code and generated_code.get('summary')) else '불가'}"
                )
                _safe_put(msg)

            # 조건식 코드
            if generated_code and generated_code.get('summary'):
                summary = generated_code.get('summary', {})
                total_filters = int(summary.get('total_filters', 0))
                total_impr = int(summary.get('total_improvement_combined', summary.get('total_improvement_naive', 0)))
                naive_impr = int(summary.get('total_improvement_naive', total_impr))
                overlap_loss = int(summary.get('overlap_loss', naive_impr - total_impr))
                allow_ml_filters_summary = summary.get('allow_ml_filters')
                excluded_ml_filters_summary = int(summary.get('excluded_ml_filters', 0) or 0)
 
                lines = []
                lines.append("자동 생성 필터 코드(요약):")
                lines.append(f"- 총 {total_filters}개 필터 (조합: AND, 즉 '모든 조건을 만족해야 매수')")
                lines.append(f"- 예상 총 개선(동시 적용/중복 반영): {total_impr:,}원")
                if total_filters > 0:
                    lines.append(f"- 개별개선합(단순 합산): {naive_impr:,}원, 중복/상쇄: {overlap_loss:+,}원")
                if allow_ml_filters_summary is not None:
                    lines.append(
                        f"- ML 필터 사용: {'허용' if bool(allow_ml_filters_summary) else '금지'}"
                        + (f" (제외 {excluded_ml_filters_summary}개)" if excluded_ml_filters_summary > 0 else "")
                    )
 
                steps = generated_code.get('combine_steps') or []
                if steps:
                    lines.append("- 적용 순서(추가개선→누적개선, 누적수익금, 누적제외%):")
                    for st in steps[: min(8, len(steps))]:
                        cum_profit_val = st.get('누적수익금')
                        cum_profit_text = f"{int(cum_profit_val):,}원" if cum_profit_val is not None else "N/A"
                        lines.append(
                            f"  {st.get('순서', '')}. {str(st.get('필터명', ''))[:18]}: "
                            f"+{int(st.get('추가개선(중복반영)', 0)):,} → 누적 +{int(st.get('누적개선(동시적용)', 0)):,} "
                            f"(누적 수익금 {cum_profit_text}) "
                            f"(제외 {st.get('누적제외비율', 0)}%)"
                        )

                buy_lines = generated_code.get('buy_conditions') or []
                if buy_lines:
                    lines.append("- 조합 코드(기존 매수조건에 AND 추가):")
                    for l in buy_lines[: min(8, len(buy_lines))]:
                        lines.append(f"  {l.strip()}")
                    lines.append("- 전체 설명/코드/산출물 목록은 report.txt 참고")

                _safe_put("\n".join(lines))
            else:
                # 코드가 생성되지 않더라도 원인을 파악할 수 있도록 요약 메시지 전송
                try:
                    candidate_count = sum(
                        1 for f in filter_results_safe
                        if float(f.get('수익개선금액', 0) or 0) > 0 and f.get('적용코드') and f.get('조건식')
                    )
                    pos_count = sum(1 for f in filter_results_safe if float(f.get('수익개선금액', 0) or 0) > 0)
                except Exception:
                    candidate_count = 0
                    pos_count = 0

                msg = (
                    "자동 생성 필터 코드(요약):\n"
                    "- 생성 불가 또는 후보 없음\n"
                    f"- 개선(+) 필터: {pos_count:,}개\n"
                    f"- 코드 생성 후보(개선(+) + 적용코드 + 조건식): {candidate_count:,}개\n"
                    "- filter.csv를 확인해 적용코드/조건식 유무를 점검하세요."
                )
                _safe_put(msg)

            # 세그먼트 분석 리포트(옵션)
            segment_outputs = result.get('segment_outputs') if isinstance(result, dict) else None
            if segment_outputs:
                try:
                    seg_lines = ["세그먼트 분석 결과:"]
                    phase2 = segment_outputs.get('phase2') or {}
                    phase3 = segment_outputs.get('phase3') or {}
                    template_comp = segment_outputs.get('template_comparison') or {}
                    timing = segment_outputs.get('timing') or {}

                    code_summary = phase2.get('segment_code_summary') or {}
                    if code_summary:
                        seg_lines.append(
                            f"- 조건식 요약: {code_summary.get('segments', 0)}구간, "
                            f"필터 {code_summary.get('filters', 0)}개"
                        )

                    combo_path = phase2.get('global_combo_path')
                    if combo_path and Path(combo_path).exists():
                        try:
                            df_combo = pd.read_csv(combo_path, encoding='utf-8-sig')
                            if not df_combo.empty:
                                row = df_combo.iloc[0]
                                total_impr = int(row.get('total_improvement', 0) or 0)
                                remaining_trades = int(row.get('remaining_trades', 0) or 0)
                                remaining_ratio = float(row.get('remaining_ratio', 0) or 0)
                                seg_lines.append(
                                    f"- 전역 조합 개선: {total_impr:+,}원, "
                                    f"잔여 {remaining_trades:,}건 ({remaining_ratio * 100:.1f}%)"
                                )
                        except Exception:
                            pass

                    summary_path = phase3.get('summary_path') or phase2.get('summary_path')
                    if summary_path and Path(summary_path).exists():
                        try:
                            df_summary = pd.read_csv(summary_path, encoding='utf-8-sig')
                            if not df_summary.empty and 'trades' in df_summary.columns:
                                total_trades = int(df_summary['trades'].sum())
                                out_row = df_summary[df_summary['segment_id'] == 'Out_of_Range']
                                if not out_row.empty and total_trades > 0:
                                    out_trades = int(out_row.iloc[0].get('trades', 0) or 0)
                                    seg_lines.append(
                                        f"- 구간 외 거래: {out_trades:,}건 ({out_trades / total_trades * 100:.1f}%)"
                                    )
                                if 'profit' in df_summary.columns:
                                    df_main = df_summary[df_summary['segment_id'] != 'Out_of_Range']
                                    top_rows = df_main.sort_values('profit', ascending=False).head(2)
                                    if not top_rows.empty:
                                        tops = []
                                        for _, row in top_rows.iterrows():
                                            seg_id = row.get('segment_id')
                                            profit = int(row.get('profit', 0) or 0)
                                            if seg_id:
                                                tops.append(f"{seg_id}({profit:,}원)")
                                        if tops:
                                            seg_lines.append("- 상위 세그먼트: " + ", ".join(tops))
                        except Exception:
                            pass

                    comp_path = template_comp.get('comparison_path')
                    if comp_path and Path(comp_path).exists():
                        try:
                            df_comp = pd.read_csv(comp_path, encoding='utf-8-sig')
                            if not df_comp.empty:
                                df_rank = df_comp.copy()
                                if 'score' in df_rank.columns:
                                    df_rank = df_rank.sort_values(['score'], ascending=[False])
                                best = df_rank.iloc[0]
                                seg_lines.append(
                                    f"- 템플릿 비교: {Path(comp_path).name} (최상: {best.get('template', 'N/A')})"
                                )
                        except Exception:
                            seg_lines.append(f"- 템플릿 비교: {Path(comp_path).name}")

                    summary_path = segment_outputs.get('summary_report_path')
                    if summary_path:
                        try:
                            seg_lines.append(f"- 종합 요약: {Path(summary_path).name}")
                        except Exception:
                            seg_lines.append(f"- 종합 요약: {summary_path}")

                    if timing:
                        def _fmt_sec(v):
                            try:
                                return f"{float(v):.2f}s"
                            except Exception:
                                return str(v)

                        total_s = timing.get('total_s')
                        parts = []
                        if timing.get('phase2_s') is not None:
                            parts.append(f"phase2 {_fmt_sec(timing.get('phase2_s'))}")
                        if timing.get('phase3_s') is not None:
                            parts.append(f"phase3 {_fmt_sec(timing.get('phase3_s'))}")
                        if timing.get('template_s') is not None:
                            parts.append(f"template {_fmt_sec(timing.get('template_s'))}")
                        if total_s is not None:
                            if parts:
                                seg_lines.append(f"- 세그먼트 분석 소요 시간: {_fmt_sec(total_s)} ({', '.join(parts)})")
                            else:
                                seg_lines.append(f"- 세그먼트 분석 소요 시간: {_fmt_sec(total_s)}")
                        elif parts:
                            seg_lines.append(f"- 세그먼트 분석 소요 시간: {', '.join(parts)}")

                    _safe_put("\n".join(seg_lines))

                    for key in ('heatmap_path', 'efficiency_path'):
                        p = phase3.get(key)
                        if p and Path(p).exists():
                            teleQ.put(str(Path(p)))
                except Exception:
                    pass

    except Exception as e:
        print_exc()

    return result
