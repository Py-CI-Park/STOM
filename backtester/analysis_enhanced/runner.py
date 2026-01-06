# -*- coding: utf-8 -*-
import time
from pathlib import Path
from traceback import print_exc

import pandas as pd

from backtester.output_paths import ensure_backtesting_output_dir, build_backtesting_output_path
from backtester.analysis.output_config import get_backtesting_output_config
from backtester.detail_schema import reorder_detail_columns
from .metrics_enhanced import CalculateEnhancedDerivedMetrics
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
from backtester.segment_analysis.code_generator import (
    build_filter_final_code,
    save_filter_code_final,
)
from .analysis_logger import create_analysis_logger, AnalysisLogger

# === 강화된 필터 검증 모듈 (v1.0) ===
from .stats import apply_multiple_testing_correction, get_correction_summary
from .validation_enhanced import (
    PurgedWalkForwardConfig,
    validate_filters_batch,
    get_cv_summary,
)
from .feature_selection import (
    greedy_select_diverse_filters,
    remove_redundant_filters,
    filter_by_mutual_information,
    get_feature_selection_summary,
)
from .ensemble_filter import (
    EnsembleConfig,
    run_ensemble_filter_analysis,
    get_ensemble_summary,
    convert_ensemble_results_to_filter_results,
)


# =============================================================================
# 세그먼트 분석 헬퍼 함수
# =============================================================================

def _has_segment_filter_in_buystg(buystg: str) -> bool:
    """
    buystg 문자열에 이미 세그먼트 필터 코드가 포함되어 있는지 확인합니다.

    [2026-01-06 버그 수정]
    - 문제: Filter 백테스트 시 원본 백테스트의 segment_code_final.txt가 buystg에 이미 포함됨
    - 결과: RunEnhancedAnalysis()가 세그먼트 분석을 다시 실행하여 새 필터가 추가로 삽입됨
    - 증상: segment_code_final.txt에 두 개의 세그먼트 필터가 연속 배치됨
            (T3C3_time3 + T5C3_time5 = 517줄, 원본은 302줄)
    - 해결: buystg에 세그먼트 필터 마커가 있으면 세그먼트 분석 건너뛰기

    [2026-01-06 추가 강화]
    - 더 많은 마커 추가 (segment_code_final.txt 실제 내용 기반)
    - 공백 정규화 처리 (탭/공백 차이 무시)
    - 디버그 로깅 추가

    Args:
        buystg: 매수 조건식 문자열

    Returns:
        True if segment filter markers are found, False otherwise
    """
    if not buystg:
        return False

    # 공백 정규화: 연속 공백을 단일 공백으로, 탭을 공백으로 변환
    normalized_buystg = ' '.join(buystg.split())

    # 세그먼트 필터 코드에 사용되는 마커들
    # segment_code_final.txt의 실제 구조 기반으로 선정 (더 많은 변형 포함)
    segment_markers = [
        # === 헤더 마커 ===
        '# === 세그먼트 필터',           # segment_code_final.txt 헤더 (여러 변형 매칭)
        '세그먼트 필터 반영',            # 헤더 내 반영 구문
        '# 세그먼트 코드:',              # segment_code_final.txt 헤더
        '최종 매수 조건식_filtered',     # segment_code_final.txt 첫 줄
        '# 세그먼트 필터 조건식',        # 세그먼트 필터 조건식 시작 주석

        # === 필터 로직 마커 ===
        '필터통과 = False',              # 세그먼트 필터 조건식 (공백 포함)
        '필터통과 = True',               # 세그먼트 필터 조건식 (공백 포함)
        '필터통과=False',                # 세그먼트 필터 조건식 (공백 없음)
        '필터통과=True',                 # 세그먼트 필터 조건식 (공백 없음)

        # === 세그먼트 제외/반영 마커 ===
        '세그먼트 전체 제외',            # 세그먼트 전체 제외 주석
        '매수 = 매수 and 필터통과',      # 최종 조건 합성 (공백 포함)
        '매수=매수 and 필터통과',        # 최종 조건 합성 (일부 공백 없음)

        # === 세그먼트 분할 마커 (시가총액/시간 기반) ===
        '[대형주_T',                     # 세그먼트 주석 (대형주)
        '[중형주_T',                     # 세그먼트 주석 (중형주)
        '[소형주_T',                     # 세그먼트 주석 (소형주)
        '[초소형주_T',                   # 세그먼트 주석 (초소형주)
    ]

    # 원본 문자열에서 마커 검색
    for marker in segment_markers:
        if marker in buystg:
            print(f"[Segment Filter Detection] 마커 감지됨: '{marker}'")
            return True

    # 정규화된 문자열에서 마커 검색 (공백 차이 무시)
    normalized_markers = [
        '필터통과 = False',
        '필터통과 = True',
        '매수 = 매수 and 필터통과',
    ]
    for marker in normalized_markers:
        normalized_marker = ' '.join(marker.split())
        if normalized_marker in normalized_buystg:
            print(f"[Segment Filter Detection] 정규화 마커 감지됨: '{marker}'")
            return True

    # 디버그: 감지 실패 시 buystg 일부 출력 (첫 500자)
    if len(buystg) > 100:
        print(f"[Segment Filter Detection] 마커 미감지. buystg 길이: {len(buystg)}")
        print(f"[Segment Filter Detection] buystg 시작 500자: {buystg[:500]}")

    return False


def _resolve_best_template_segment_code(
    template_comparison: dict,
    base_phase2: dict,
) -> tuple[str | None, dict | None, str]:
    """
    세그먼트 최종 조건식 생성에 사용할 segment_code_path를 결정합니다.

    [우선순위]
    1. 템플릿 비교 결과가 있고, 최상위 템플릿의 segment_code_path가 존재하면 사용
    2. 그렇지 않으면 base phase2의 segment_code_path 사용 (하위 호환성)

    [중요 배경 - 2025-12-31 버그 수정]
    - 기존 코드는 항상 base phase2의 segment_code_path를 사용
    - base phase2는 기본 SegmentConfig(고정 범위)로 실행됨
    - 템플릿 비교에서 최상위로 선정된 템플릿은 동적 범위(quantile)를 사용할 수 있음
    - 예: 동적 범위 대형주 >= 6,432억 vs 고정 범위 대형주 >= 10,000억
    - 이 불일치로 인해 세그먼트 필터가 잘못된 거래에 적용되어 기대 성과와 실제 성과가 크게 다름

    Args:
        template_comparison: run_segment_template_comparison() 반환값
            - 'comparison_path': 템플릿 비교 CSV 경로
            - 'results': {template_key: phase2_result} 딕셔너리
        base_phase2: run_phase2() 반환값 (기본 phase2 결과)

    Returns:
        tuple: (segment_code_path, source_phase2_result, source_description)
            - segment_code_path: 사용할 segment_code.txt 경로
            - source_phase2_result: 해당 phase2 결과 딕셔너리
            - source_description: 출처 설명 문자열 (로깅/디버깅용)
    """
    # 기본값: base phase2 사용
    fallback_path = base_phase2.get('segment_code_path') if isinstance(base_phase2, dict) else None
    fallback_result = base_phase2
    fallback_desc = "base_phase2 (기본 SegmentConfig)"

    # 템플릿 비교 결과가 없으면 기본값 반환
    if not isinstance(template_comparison, dict):
        return fallback_path, fallback_result, fallback_desc

    comparison_path = template_comparison.get('comparison_path')
    results = template_comparison.get('results')

    if not comparison_path or not isinstance(results, dict) or not results:
        return fallback_path, fallback_result, fallback_desc

    # 템플릿 비교 CSV에서 최상위 템플릿 식별
    best_template_key = _find_best_template_key_from_csv(comparison_path, results)

    if not best_template_key:
        return fallback_path, fallback_result, fallback_desc

    # 최상위 템플릿의 phase2 결과에서 segment_code_path 추출
    best_result = results.get(best_template_key)
    if not isinstance(best_result, dict):
        return fallback_path, fallback_result, fallback_desc

    best_segment_code_path = best_result.get('segment_code_path')
    if not best_segment_code_path or not Path(best_segment_code_path).exists():
        return fallback_path, fallback_result, fallback_desc

    # 최상위 템플릿의 segment_code_path 반환
    source_desc = f"best_template: {best_template_key}"
    return best_segment_code_path, best_result, source_desc


def _find_best_template_key_from_csv(comparison_csv_path: str, results: dict) -> str | None:
    """
    템플릿 비교 CSV에서 최상위 score를 가진 템플릿의 key를 찾습니다.

    Args:
        comparison_csv_path: 템플릿 비교 CSV 파일 경로
        results: {template_key: phase2_result} 딕셔너리

    Returns:
        최상위 템플릿의 key (예: "T3C3_time3:dynamic:semi") 또는 None
    """
    try:
        df = pd.read_csv(comparison_csv_path, encoding='utf-8-sig')
        if df.empty:
            return None

        # score 컬럼으로 정렬하여 최상위 행 선택
        if 'score' in df.columns:
            df = df.sort_values('score', ascending=False)
        elif 'total_improvement' in df.columns:
            df = df.sort_values('total_improvement', ascending=False)
        else:
            return None

        best_row = df.iloc[0]

        # 템플릿 key 구성: template:variant 또는 template:variant:dynamic_mode
        template_name = str(best_row.get('template', '')).strip()
        variant = str(best_row.get('variant', 'fixed')).strip()
        dynamic_mode = best_row.get('dynamic_mode')

        if not template_name:
            return None

        # results 딕셔너리의 key 형식과 매칭
        # 가능한 key 형식:
        #   - "{template}:fixed"
        #   - "{template}:dynamic:{mode}"
        if variant == 'dynamic' and dynamic_mode and str(dynamic_mode).lower() not in ('nan', 'none', ''):
            candidate_key = f"{template_name}:dynamic:{dynamic_mode}"
        else:
            candidate_key = f"{template_name}:{variant}"

        # 정확히 매칭되는 key가 있는지 확인
        if candidate_key in results:
            return candidate_key

        # 대소문자/공백 차이로 매칭 안 될 수 있으므로 유사 매칭 시도
        candidate_lower = candidate_key.lower().replace(' ', '_')
        for key in results.keys():
            if key.lower().replace(' ', '_') == candidate_lower:
                return key

        return None

    except Exception:
        return None

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
        'analysis_log_path': None,    # NEW: 분석 로그 파일 경로
    }

    # 분석 로거 초기화
    output_dir = ensure_backtesting_output_dir(save_file_name)
    analysis_logger = create_analysis_logger(
        output_dir=str(output_dir),
        save_file_name=save_file_name,
        teleQ=teleQ,
        total_steps=12
    )

    try:
        # === Phase A 시작: 일반 필터 분석 ===
        analysis_logger.send_phase_notification('A', 'start')
        
        # 1. 강화된 파생 지표 계산
        analysis_logger.log_step_start(1, "강화 파생 지표 계산 (CalculateEnhancedDerivedMetrics)")
        df_enhanced = CalculateEnhancedDerivedMetrics(df_tsg)
        analysis_logger.log_step_complete(1, metrics={
            "원본_행수": len(df_tsg),
            "강화_컬럼수": len(df_enhanced.columns),
        })
        
        # 2. ML 기반 위험도 예측 (NEW)
        # - 손실확률_ML: ML이 예측한 손실 확률 (0~1)
        # - 위험도_ML: ML 기반 위험도 점수 (0~100)
        # - 예측매수매도위험도점수_ML: 매수 시점 변수로 예측한 매수매도위험도점수(0~100)
        # - detail.csv에 추가하여 실제 매수매도위험도점수와 비교 가능
        analysis_logger.log_step_start(2, "ML 위험도 예측 (PredictRiskWithML)")
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
        analysis_logger.log_step_complete(2, metrics={
            "ML_모델": ml_prediction_stats.get('model_type') if ml_prediction_stats else None,
            "AUC": ml_prediction_stats.get('test_auc') if ml_prediction_stats else None,
            "신뢰도_PASS": allow_ml_filters,
        })

        # 3. 강화된 필터 효과 분석 (통계 검정 포함)
        analysis_logger.log_step_start(3, "필터 효과 분석 (AnalyzeFilterEffectsEnhanced)")
        filter_results = AnalyzeFilterEffectsEnhanced(df_enhanced, allow_ml_filters=allow_ml_filters)
        result['filter_results'] = filter_results
        
        # 필터 결정 로그 기록 (상세 정보 포함)
        total_trades = len(df_enhanced)
        total_profit = int(df_enhanced['수익금'].sum()) if '수익금' in df_enhanced.columns else 0
        analysis_logger.log_filter_decisions_from_results(
            filter_results, 
            total_trades=total_trades, 
            total_profit=total_profit
        )
        
        analysis_logger.log_step_complete(3, metrics={
            "총_필터수": len(filter_results) if filter_results else 0,
            "개선_필터수": len([f for f in (filter_results or []) if (f.get('수익개선금액', 0) or 0) > 0]),
            "총_거래수": total_trades,
            "총_수익금": total_profit,
        })

        # 3-1. (진단용) 룩어헤드 포함 필터 효과 분석
        filter_results_lookahead = AnalyzeFilterEffectsLookahead(df_enhanced)
        result['filter_results_lookahead'] = filter_results_lookahead

        # 3-2. 강화된 필터 검증 (v1.0): OOS 검증 + 다양성 선택 + 앙상블
        # - OOS 검증: Purged Walk-Forward CV로 Out-of-Sample 성능 추정
        # - 다양성 선택: 상관관계 기반 중복 필터 제거
        # - 앙상블: Bootstrap 투표로 견고한 필터 식별
        try:
            # OOS 검증 (상위 20개 필터만)
            if filter_results and len(df_enhanced) >= 200:
                cv_config = PurgedWalkForwardConfig(n_splits=5, min_trades_per_fold=30)
                filter_results = validate_filters_batch(df_enhanced, filter_results, cv_config, top_n=20)
                cv_summary = get_cv_summary(filter_results)
                result['cv_summary'] = cv_summary
                
                # 다양성 기반 선택 (상위 30개 중 중복 제거)
                filter_results = remove_redundant_filters(filter_results, df_enhanced, correlation_threshold=0.8)
                
                analysis_logger.log_info(
                    f"[OOS 검증] 검증 {cv_summary.get('validated_count', 0)}개, "
                    f"견고 {cv_summary.get('robust_count', 0)}개 "
                    f"(일반화율 평균 {cv_summary.get('avg_generalization_ratio', 0):.1f}%)"
                )
        except Exception as e:
            analysis_logger.log_warning(f"강화 검증 스킵: {e}")

        # 4. 최적 임계값 탐색
        analysis_logger.log_step_start(4, "최적 임계값 탐색 (FindAllOptimalThresholds)")
        optimal_thresholds = FindAllOptimalThresholds(df_enhanced)
        result['optimal_thresholds'] = optimal_thresholds
        analysis_logger.log_step_complete(4, metrics={
            "임계값_수": len(optimal_thresholds) if optimal_thresholds else 0,
        })

        # 5. 필터 조합 분석 (단일 필터 결과 재사용으로 중복 계산 제거)
        analysis_logger.log_step_start(5, "필터 조합 분석 (AnalyzeFilterCombinations)")
        filter_combinations = AnalyzeFilterCombinations(df_enhanced, single_filters=filter_results)
        result['filter_combinations'] = filter_combinations
        
        # 상위 조합 로깅 (최대 5개)
        for combo in (filter_combinations or [])[:5]:
            filter_names = [combo.get('필터1', ''), combo.get('필터2', '')]
            if combo.get('필터3'):
                filter_names.append(combo.get('필터3'))
            filter_names = [f for f in filter_names if f]
            
            analysis_logger.log_combination_evaluation(
                filter_names=filter_names,
                individual_improvements=[],  # 개별 개선금액은 결과에 없음
                combined_improvement=int(combo.get('조합개선', 0) or 0),
                synergy=int(combo.get('시너지효과', 0) or 0),
                synergy_ratio=float(combo.get('시너지비율', 0) or 0),
                excluded_ratio=float(combo.get('제외비율', 0) or 0),
                recommendation=combo.get('권장', ''),
            )
        
        analysis_logger.log_step_complete(5, metrics={
            "조합_수": len(filter_combinations) if filter_combinations else 0,
            "시너지_조합수": len([c for c in (filter_combinations or []) if (c.get('시너지효과', 0) or 0) > 0]),
        })

        # 6. ML 특성 중요도
        analysis_logger.log_step_start(6, "ML 특성 중요도 (AnalyzeFeatureImportance)")
        feature_importance = AnalyzeFeatureImportance(df_enhanced)
        result['feature_importance'] = feature_importance
        analysis_logger.log_step_complete(6, metrics={
            "피처_수": len(feature_importance) if feature_importance else 0,
        })

        # 7. 필터 안정성 검증
        analysis_logger.log_step_start(7, "필터 안정성 검증 (AnalyzeFilterStability)")
        filter_stability = AnalyzeFilterStability(df_enhanced)
        result['filter_stability'] = filter_stability
        
        # 안정성 결과 로깅
        for fs in (filter_stability or []):
            period_results = []
            period_improvements = fs.get('기간별개선', [])
            for i, imp in enumerate(period_improvements):
                period_results.append({
                    'period': f'P{i+1}',
                    'improvement': imp,
                    'win_rate': 0,  # 승률 정보는 현재 없음
                })
            
            analysis_logger.log_filter_stability_result(
                filter_name=fs.get('필터명', ''),
                period_results=period_results,
                consistency_score=float(fs.get('일관성점수', 0) or 0),
                is_stable=fs.get('안정성등급') == '안정',
            )
        
        analysis_logger.log_step_complete(7, metrics={
            "안정_필터수": len([f for f in (filter_stability or []) if f.get('안정성등급') == '안정']),
            "보통_필터수": len([f for f in (filter_stability or []) if f.get('안정성등급') == '보통']),
            "불안정_필터수": len([f for f in (filter_stability or []) if f.get('안정성등급') == '불안정']),
        })

        # 8. 조건식 코드 생성
        analysis_logger.log_step_start(8, "조건식 코드 생성 (GenerateFilterCode)")
        generated_code = GenerateFilterCode(filter_results, df_tsg=df_enhanced, allow_ml_filters=allow_ml_filters)
        result['generated_code'] = generated_code
        analysis_logger.log_step_complete(8, metrics={
            "생성_필터수": generated_code.get('summary', {}).get('total_filters', 0) if generated_code else 0,
            "예상_개선": generated_code.get('summary', {}).get('total_improvement_combined', 0) if generated_code else 0,
        })

        # 9. 일반 필터 조건식 파일 생성 (filter_code_final.txt)
        # [2026-01-06 추가] segment_code_final.txt와 유사하게 일반 필터도 최종 조건식 파일 생성
        analysis_logger.log_step_start(9, "일반 필터 조건식 파일 생성 (build_filter_final_code)")
        try:
            if generated_code:
                filter_final_output_dir = ensure_backtesting_output_dir(save_file_name)
                filter_final_lines, filter_final_summary = build_filter_final_code(
                    buystg_text=buystg,
                    sellstg_text=sellstg,
                    generated_code=generated_code,
                    buystg_name=buystg_name,
                    sellstg_name=sellstg_name,
                    save_file_name=save_file_name,
                )
                
                if filter_final_lines:
                    filter_code_path = save_filter_code_final(
                        filter_final_lines,
                        str(filter_final_output_dir),
                        save_file_name
                    )
                    if filter_code_path:
                        result['filter_code_final_path'] = filter_code_path
                        analysis_logger.log_code_generation(f"일반 필터 조건식 파일 생성: {filter_code_path}")
                        print(f"[Enhanced Analysis] 일반 필터 조건식 파일 생성: {filter_code_path}")
                        print(f"  - 필터 수: {filter_final_summary.get('total_filters', 0)}")
                        print(f"  - 예상 개선: {filter_final_summary.get('total_improvement', 0):,}원")
            analysis_logger.log_step_complete(9, metrics={
                "파일_생성": bool(result.get('filter_code_final_path')),
            })
        except Exception as e:
            analysis_logger.log_step_failed(9, str(e))
            print(f"[Enhanced Analysis] 일반 필터 조건식 파일 생성 실패: {e}")
            print_exc()
        
        # === Phase A 완료, Phase B 시작: 결과 저장 ===
        analysis_logger.send_phase_notification('A', 'complete')
        analysis_logger.send_filter_summary()  # 상위 필터 요약 전송
        analysis_logger.send_phase_notification('B', 'start')

        # 10. CSV 파일 저장
        analysis_logger.log_step_start(10, "CSV 파일 저장")
        # 상세 거래 기록 (강화 분석 사용 시: detail.csv로 통합하여 중복 생성 방지)
        # - 손실확률_ML, 위험도_ML, 예측매수매도위험도점수_ML 컬럼이 포함되어 비교 가능
        # output_dir는 이미 로거 초기화 시 설정됨
        output_cfg = get_backtesting_output_config()
        csv_chunk_size = output_cfg.get('csv_chunk_size') if output_cfg.get('enable_csv_parallel') else None
        detail_path = str(build_backtesting_output_path(save_file_name, "_detail.csv", output_dir=output_dir))
        df_enhanced_out = reorder_detail_columns(df_enhanced)
        df_enhanced_out.to_csv(detail_path, encoding='utf-8-sig', index=True)
        result['csv_files'].append(detail_path)

        # 필터 분석 결과
        if filter_results:
            # 강화 분석 사용 시: filter.csv로 통합하여 중복 생성 방지
            filter_path = str(build_backtesting_output_path(save_file_name, "_filter.csv", output_dir=output_dir))
            pd.DataFrame(filter_results).to_csv(filter_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(filter_path)

        # (진단용) 룩어헤드 포함 필터 분석 결과
        if filter_results_lookahead:
            lookahead_path = str(build_backtesting_output_path(save_file_name, "_filter_lookahead.csv", output_dir=output_dir))
            pd.DataFrame(filter_results_lookahead).to_csv(lookahead_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(lookahead_path)

        # 최적 임계값
        if optimal_thresholds:
            threshold_path = str(build_backtesting_output_path(save_file_name, "_optimal_thresholds.csv", output_dir=output_dir))
            pd.DataFrame(optimal_thresholds).to_csv(threshold_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(threshold_path)

        # 필터 조합
        if filter_combinations:
            combo_path = str(build_backtesting_output_path(save_file_name, "_filter_combinations.csv", output_dir=output_dir))
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
            stability_path = str(build_backtesting_output_path(save_file_name, "_filter_stability.csv", output_dir=output_dir))
            pd.DataFrame(filter_stability).to_csv(stability_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(stability_path)
        
        analysis_logger.log_step_complete(10, metrics={
            "CSV_파일수": len(result['csv_files']),
        })

        # 11. 강화된 차트 생성
        analysis_logger.log_step_start(11, "강화된 차트 생성 (PltEnhancedAnalysisCharts)")
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
            sellstg=sellstg,
            buystg_name=buystg_name,
            sellstg_name=sellstg_name,
        )
        if chart_path:
            result['charts'].append(chart_path)
        analysis_logger.log_step_complete(11, metrics={
            "차트_생성": bool(chart_path),
        })
        
        # === Phase B 완료, Phase C 시작: 세그먼트 분석 ===
        analysis_logger.send_phase_notification('B', 'complete')
        analysis_logger.send_phase_notification('C', 'start')

        # 12. 세그먼트 분석(옵션)
        analysis_logger.log_step_start(12, "세그먼트 분석 (Phase2/3)")
        # [2026-01-06 리팩토링] 세그먼트 분석 항상 실행 + 중복 방지는 code_generator.py에서 처리
        #
        # 동작 방식:
        # 1. 세그먼트 분석(Phase2/3)은 항상 실행 - 일반 필터의 고도화 단계로 함께 진행
        # 2. buystg에 기존 세그먼트 필터가 있으면 경고 로그 출력
        # 3. 최종 코드 생성 시 code_generator.py가 기존 필터를 감지하여 교체(replace)
        #    - _has_existing_segment_filter(): 기존 필터 감지
        #    - _extract_original_buy_code(): 원본 코드 추출 (기존 필터 제거)
        #    - _inject_segment_filter_into_buy_lines(): 새 필터 삽입
        #
        # 결과: 기존 필터가 있어도 최신 세그먼트 분석 결과로 교체됨
        segment_outputs = None

        # 기존 세그먼트 필터 감지 (경고용)
        has_existing_filter = _has_segment_filter_in_buystg(buystg)
        if has_existing_filter:
            print(f"[Segment Analysis] buystg에 기존 세그먼트 필터 감지됨 - 최신 분석 결과로 교체 예정")
            if teleQ is not None:
                teleQ.put("[세그먼트 분석] 기존 세그먼트 필터 감지됨 - 최신 분석 결과로 교체됩니다")

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
                    phase2_result = segment_outputs.get('phase2') if isinstance(segment_outputs, dict) else None
                    global_best = phase2_result.get('global_best') if isinstance(phase2_result, dict) else None
                    segment_outputs['phase3'] = run_phase3(
                        detail_path,
                        filter_config=filter_config,
                        runner_config=Phase3RunnerConfig(
                            output_dir=segment_output_base,
                            prefix=save_file_name
                        ),
                        global_best=global_best,
                        buystg_name=buystg_name,
                        sellstg_name=sellstg_name,
                        save_file_name=save_file_name,
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

                # ===============================================================
                # 최종 매수 조건식(세그먼트 필터 반영) 생성
                # ===============================================================
                # [2025-12-31 버그 수정]
                # - 기존: 항상 base phase2의 segment_code 사용 (고정 시가총액 범위)
                # - 수정: 템플릿 비교 결과가 있으면 최상위 템플릿의 segment_code 사용
                #
                # [중요]
                # 템플릿 비교에서 동적(dynamic) 모드가 최상위로 선정된 경우,
                # 해당 템플릿은 데이터 분포 기반 quantile로 시가총액 범위를 계산함.
                # 예: 동적 범위 (대형주 >= 6,432억) vs 고정 범위 (대형주 >= 10,000억)
                # 이 범위가 일치해야 세그먼트 필터가 올바른 거래에 적용됨.
                # ===============================================================
                try:
                    from backtester.segment_analysis.code_generator import (
                        build_segment_final_code,
                        save_segment_code_final,
                    )

                    # 최상위 템플릿의 segment_code_path 결정
                    base_phase2 = segment_outputs.get('phase2') if isinstance(segment_outputs, dict) else None
                    template_comparison = segment_outputs.get('template_comparison') if isinstance(segment_outputs, dict) else None

                    segment_code_path, source_phase2, source_desc = _resolve_best_template_segment_code(
                        template_comparison=template_comparison,
                        base_phase2=base_phase2,
                    )

                    if segment_code_path and Path(segment_code_path).exists():
                        # 로깅: 어떤 segment_code가 사용되는지 기록
                        print(f"[Segment Code Final] 출처: {source_desc}")
                        print(f"[Segment Code Final] 경로: {segment_code_path}")

                        seg_lines = Path(segment_code_path).read_text(encoding='utf-8-sig').splitlines()

                        # source_phase2에서 global_combo_path와 code_summary 추출
                        global_combo_path = source_phase2.get('global_combo_path') if isinstance(source_phase2, dict) else None
                        code_summary = source_phase2.get('segment_code_summary') if isinstance(source_phase2, dict) else None

                        final_lines, final_summary = build_segment_final_code(
                            buystg_text=buystg,
                            sellstg_text=sellstg,
                            segment_code_lines=seg_lines,
                            buystg_name=buystg_name,
                            sellstg_name=sellstg_name,
                            segment_code_path=segment_code_path,
                            global_combo_path=global_combo_path,
                            code_summary=code_summary,
                            save_file_name=save_file_name,
                        )
                        final_path = save_segment_code_final(final_lines, segment_output_base, save_file_name)

                        if final_path:
                            # 결과를 base phase2에 저장 (하위 호환성 - 기존 코드가 phase2에서 결과를 찾음)
                            if isinstance(base_phase2, dict):
                                base_phase2['segment_code_final_path'] = final_path
                                base_phase2['segment_code_final_summary'] = final_summary
                                base_phase2['segment_code_final_source'] = source_desc

                            if teleQ is not None:
                                teleQ.put(f"최종 작성 업데이트 된 조건식 파일: {final_path}")
                                teleQ.put(f"[세그먼트 코드 출처: {source_desc}]")
                except Exception:
                    print_exc()

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
        
        # 세그먼트 분석 단계 완료 로그
        if segment_outputs and isinstance(segment_outputs, dict):
            seg_timing = segment_outputs.get('timing', {})
            analysis_logger.log_step_complete(12, metrics={
                "세그먼트_분석_완료": True,
                "phase2_시간": seg_timing.get('phase2_s'),
                "phase3_시간": seg_timing.get('phase3_s'),
                "template_시간": seg_timing.get('template_s'),
            })
        else:
            analysis_logger.log_step_complete(12, metrics={
                "세그먼트_분석_완료": False,
                "사유": "세그먼트 분석 비활성화 또는 결과 없음",
            })

        # Phase C 완료 알림
        analysis_logger.send_phase_notification('C', 'complete')

        # 필터/세그먼트 적용 detail.csv 생성 (검증/비교용)
        try:
            if isinstance(df_enhanced, pd.DataFrame) and not df_enhanced.empty:
                from backtester.analysis.filter_apply import build_filter_mask_from_generated_code
                mask_info = build_filter_mask_from_generated_code(df_enhanced, generated_code)
                if mask_info and mask_info.get('mask') is not None:
                    df_filtered = df_enhanced[mask_info['mask']].copy()
                    filtered_path = str(build_backtesting_output_path(save_file_name, "_detail_filtered.csv", output_dir=output_dir))
                    df_filtered_out = reorder_detail_columns(df_filtered)
                    df_filtered_out.to_csv(
                        filtered_path,
                        encoding='utf-8-sig',
                        index=True,
                        chunksize=csv_chunk_size,
                    )
                    result['csv_files'].append(filtered_path)

                    try:
                        total_trades = int(len(df_enhanced))
                        remaining_trades = int(len(df_filtered))
                        remaining_ratio = remaining_trades / max(1, total_trades)
                        total_profit = int(pd.to_numeric(df_enhanced['수익금'], errors='coerce').fillna(0).sum())
                        remaining_profit = int(pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0).sum())
                        improvement = remaining_profit - total_profit
                        expected_improvement = None
                        if isinstance(generated_code, dict):
                            summary = generated_code.get('summary') or {}
                            expected_improvement = summary.get('total_improvement_combined')

                        verify_row = {
                            'total_trades': total_trades,
                            'remaining_trades': remaining_trades,
                            'remaining_ratio': round(remaining_ratio, 6),
                            'total_profit': total_profit,
                            'remaining_profit': remaining_profit,
                            'improvement': improvement,
                            'expected_improvement': expected_improvement,
                        }
                        verify_path = str(build_backtesting_output_path(save_file_name, "_filter_verification.csv", output_dir=output_dir))
                        pd.DataFrame([verify_row]).to_csv(verify_path, encoding='utf-8-sig', index=False)
                        result['csv_files'].append(verify_path)
                    except Exception:
                        pass
        except Exception:
            pass

        try:
            if isinstance(df_enhanced, pd.DataFrame) and not df_enhanced.empty and isinstance(segment_outputs, dict):
                from backtester.segment_analysis.segment_apply import build_segment_mask_from_global_best

                base_phase2 = segment_outputs.get('phase2') if isinstance(segment_outputs, dict) else None
                template_comparison = segment_outputs.get('template_comparison') if isinstance(segment_outputs, dict) else None

                _, source_phase2, source_desc = _resolve_best_template_segment_code(
                    template_comparison=template_comparison,
                    base_phase2=base_phase2,
                )
                segment_global_best = source_phase2.get('global_best') if isinstance(source_phase2, dict) else None

                if isinstance(segment_global_best, dict):
                    seg_mask_info = build_segment_mask_from_global_best(df_enhanced, segment_global_best)
                    if seg_mask_info and seg_mask_info.get('mask') is not None:
                        df_segment = df_enhanced[seg_mask_info['mask']].copy()
                        segment_path = str(build_backtesting_output_path(save_file_name, "_detail_segment.csv", output_dir=output_dir))
                        df_segment_out = reorder_detail_columns(df_segment)
                        df_segment_out.to_csv(
                            segment_path,
                            encoding='utf-8-sig',
                            index=True,
                            chunksize=csv_chunk_size,
                        )
                        result['csv_files'].append(segment_path)

                        try:
                            total_trades = int(len(df_enhanced))
                            remaining_trades = int(len(df_segment))
                            remaining_ratio = remaining_trades / max(1, total_trades)
                            total_profit = int(pd.to_numeric(df_enhanced['수익금'], errors='coerce').fillna(0).sum())
                            remaining_profit = int(pd.to_numeric(df_segment['수익금'], errors='coerce').fillna(0).sum())
                            improvement = remaining_profit - total_profit

                            expected_remaining = None
                            expected_ratio = None
                            expected_improvement = None
                            global_combo_path = source_phase2.get('global_combo_path') if isinstance(source_phase2, dict) else None
                            if global_combo_path and Path(global_combo_path).exists():
                                df_combo = pd.read_csv(global_combo_path, encoding='utf-8-sig')
                                if not df_combo.empty:
                                    row = df_combo.iloc[0]
                                    expected_remaining = row.get('remaining_trades')
                                    expected_ratio = row.get('remaining_ratio')
                                    expected_improvement = row.get('total_improvement')

                            verify_row = {
                                'total_trades': total_trades,
                                'remaining_trades': remaining_trades,
                                'remaining_ratio': round(remaining_ratio, 6),
                                'total_profit': total_profit,
                                'remaining_profit': remaining_profit,
                                'improvement': improvement,
                                'expected_remaining_trades': expected_remaining,
                                'expected_remaining_ratio': expected_ratio,
                                'expected_improvement': expected_improvement,
                                'segment_source': source_desc,
                                'missing_columns': ",".join(seg_mask_info.get('missing_columns') or []),
                                'out_of_range_trades': int(seg_mask_info.get('out_of_range_trades', 0) or 0),
                            }
                            verify_path = str(build_backtesting_output_path(save_file_name, "_segment_verification.csv", output_dir=output_dir))
                            pd.DataFrame([verify_row]).to_csv(verify_path, encoding='utf-8-sig', index=False)
                            result['csv_files'].append(verify_path)
                        except Exception:
                            pass
        except Exception:
            pass

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

        # OOS 검증 통과 필터 (v1.0)
        oos_robust_filters = [
            f for f in filter_results_safe
            if f.get('OOS_견고') == '예' and float(f.get('수익개선금액', 0) or 0) > 0
        ][:2]
        for f in oos_robust_filters:
            try:
                recommendations.append(
                    f"[OOS견고] {f.get('필터명', '')}: 일반화 {f.get('일반화비율', 0)}% "
                    f"(+{int(f.get('OOS_평균개선', 0) or 0):,}원)"
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

            # OOS 검증 요약 메시지 (v1.0)
            cv_summary = result.get('cv_summary')
            if cv_summary and cv_summary.get('validated_count', 0) > 0:
                oos_lines = []
                oos_lines.append("OOS 검증 결과 (과적합 방지):")
                oos_lines.append(f"- 검증 필터: {cv_summary.get('validated_count', 0)}개")
                oos_lines.append(f"- OOS 견고: {cv_summary.get('robust_count', 0)}개 ({cv_summary.get('robust_ratio', 0):.1f}%)")
                oos_lines.append(f"- 평균 일반화율: {cv_summary.get('avg_generalization_ratio', 0):.1f}%")
                top_robust = cv_summary.get('top_robust_filters', [])[:3]
                if top_robust:
                    oos_lines.append(f"- 상위 견고 필터: {', '.join(str(f)[:20] for f in top_robust)}")
                _safe_put("\n".join(oos_lines))

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
        analysis_logger.log_error(f"분석 중 예외 발생: {e}")
        print_exc()

    # 분석 로그 저장
    try:
        log_path = analysis_logger.save()
        if log_path:
            result['analysis_log_path'] = log_path
            print(f"[Enhanced Analysis] 분석 로그 저장: {log_path}")
    except Exception as e:
        print(f"[Enhanced Analysis] 분석 로그 저장 실패: {e}")

    # 파이프라인 완료 알림 (텔레그램)
    analysis_logger.send_pipeline_complete()

    return result
