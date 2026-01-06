# -*- coding: utf-8 -*-
"""
강화된 백테스팅 분석 로거 모듈

백테스팅 분석 파이프라인의 모든 과정을 상세하게 기록합니다.
- 파이프라인 단계별 진입/완료 시간
- 필터 선택/제외 결정 및 사유
- 세그먼트 분할 기준 및 경계값
- 변수 매핑 로그
- 조건식 생성 과정

생성 일자: 2026-01-06
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class PipelineStep:
    """파이프라인 단계 정보"""
    step_num: int
    total_steps: int
    name: str
    description: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_s: float = 0.0
    status: str = "pending"  # pending, in_progress, completed, failed
    metrics: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass
class FilterDecision:
    """필터 선택/제외 결정 기록"""
    filter_name: str
    selected: bool
    reason: str
    improvement: int = 0
    exclude_ratio: float = 0.0
    p_value: Optional[float] = None
    cohens_d: Optional[float] = None
    is_significant: bool = False
    is_stable: bool = False
    stability_score: Optional[float] = None
    # 추가 상세 필드 (2026-01-06)
    threshold: Optional[float] = None
    direction: Optional[str] = None  # 'less' or 'greater'
    original_trades: int = 0
    remaining_trades: int = 0
    original_profit: int = 0
    remaining_profit: int = 0
    apply_code: Optional[str] = None
    condition_expr: Optional[str] = None


@dataclass
class SegmentDefinition:
    """세그먼트 정의 기록"""
    segment_id: str
    cap_label: str
    time_label: str
    cap_range: tuple
    time_range: tuple
    trade_count: int
    profit: int = 0
    win_rate: float = 0.0
    filters_applied: List[str] = field(default_factory=list)


class AnalysisLogger:
    """
    백테스팅 분석 과정을 상세하게 기록하는 로거
    
    사용법:
        logger = AnalysisLogger(output_dir, save_file_name)
        logger.start_pipeline(total_steps=12)
        
        logger.log_step_start(1, "강화 파생 지표 계산")
        # ... 작업 수행 ...
        logger.log_step_complete(1, metrics={"컬럼수": 50})
        
        logger.log_filter_decision(...)
        logger.log_segment_definition(...)
        
        logger.save()
    """
    
    # 파이프라인 단계 정의 (기본값)
    # 개선된 3단계 파이프라인:
    # - Phase A (Step 1-9): 일반 필터 분석 (전체 데이터)
    # - Phase B (Step 10-11): 결과 저장 및 시각화
    # - Phase C (Step 12): 세그먼트 결정 및 세그먼트별 조건식 생성
    DEFAULT_PIPELINE_STEPS = [
        # === Phase A: 일반 필터 분석 ===
        (1, "강화 파생 지표 계산", "CalculateEnhancedDerivedMetrics"),
        (2, "ML 위험도 예측", "PredictRiskWithML"),
        (3, "필터 효과 분석", "AnalyzeFilterEffectsEnhanced"),
        (4, "최적 임계값 탐색", "FindAllOptimalThresholds"),
        (5, "필터 조합 분석", "AnalyzeFilterCombinations"),
        (6, "ML 특성 중요도 분석", "AnalyzeFeatureImportance"),
        (7, "필터 안정성 검증", "AnalyzeFilterStability"),
        (8, "조건식 코드 생성", "GenerateFilterCode"),
        (9, "일반 필터 조건식 파일 생성", "build_filter_final_code"),
        # === Phase B: 결과 저장 ===
        (10, "CSV 파일 저장", "SaveCSVFiles"),
        (11, "차트 생성", "PltEnhancedAnalysisCharts"),
        # === Phase C: 세그먼트 분석 ===
        (12, "세그먼트 분석", "SegmentAnalysis"),
    ]
    
    # 파이프라인 Phase 정의
    PIPELINE_PHASES = {
        'A': {'name': '일반 필터 분석', 'steps': (1, 9), 'description': '전체 데이터 기반 필터 분석'},
        'B': {'name': '결과 저장', 'steps': (10, 11), 'description': 'CSV/차트 저장'},
        'C': {'name': '세그먼트 분석', 'steps': (12, 12), 'description': '세그먼트 결정 및 세그먼트별 조건식'},
    }
    
    def __init__(self, output_dir: str, save_file_name: str, teleQ=None):
        """
        Args:
            output_dir: 출력 디렉토리 경로
            save_file_name: 저장 파일명 (prefix)
            teleQ: 텔레그램 메시지 큐 (선택)
        """
        self.output_dir = Path(output_dir)
        self.save_file_name = save_file_name
        self.teleQ = teleQ
        
        # 로그 파일 경로
        self.log_path = self.output_dir / f"{save_file_name}_analysis_log.txt"
        
        # 시작 시간
        self.start_time = datetime.now()
        self.start_perf = time.perf_counter()
        
        # 파이프라인 단계
        self.pipeline_steps: Dict[int, PipelineStep] = {}
        self.total_steps = 0
        self.current_step = 0
        
        # 필터 결정 기록
        self.filter_decisions: List[FilterDecision] = []
        
        # 세그먼트 정의 기록
        self.segment_definitions: List[SegmentDefinition] = []
        
        # 일반 로그 섹션
        self.sections: List[Dict[str, Any]] = []
        
        # 변수 매핑 로그
        self.variable_mappings: List[Dict[str, str]] = []
        
        # 조건식 생성 로그
        self.code_generation_logs: List[str] = []
        
        # 경고/에러 메시지
        self.warnings: List[str] = []
        self.errors: List[str] = []
        
        # 초기화 로그
        self._log_init()
    
    def _log_init(self):
        """초기화 로그 기록"""
        self.sections.append({
            "title": "분석 시작",
            "timestamp": self.start_time.isoformat(),
            "content": {
                "save_file_name": self.save_file_name,
                "output_dir": str(self.output_dir),
                "log_path": str(self.log_path),
            }
        })
    
    def start_pipeline(self, total_steps: int = 12, custom_steps: List[tuple] = None):
        """
        파이프라인 시작
        
        Args:
            total_steps: 총 단계 수
            custom_steps: 커스텀 단계 정의 [(step_num, name, description), ...]
        """
        self.total_steps = total_steps
        steps = custom_steps or self.DEFAULT_PIPELINE_STEPS[:total_steps]
        
        for step_num, name, desc in steps:
            self.pipeline_steps[step_num] = PipelineStep(
                step_num=step_num,
                total_steps=total_steps,
                name=name,
                description=desc,
            )
    
    def log_step_start(self, step_num: int, description: str = None, send_telegram: bool = True):
        """
        파이프라인 단계 시작 기록
        
        Args:
            step_num: 단계 번호
            description: 추가 설명 (선택)
            send_telegram: 텔레그램 메시지 전송 여부
        """
        self.current_step = step_num
        
        if step_num not in self.pipeline_steps:
            self.pipeline_steps[step_num] = PipelineStep(
                step_num=step_num,
                total_steps=self.total_steps,
                name=f"Step {step_num}",
                description=description or "",
            )
        
        step = self.pipeline_steps[step_num]
        step.start_time = time.perf_counter()
        step.status = "in_progress"
        
        if description:
            step.description = description
        
        # 진행률 메시지
        progress_msg = f"[{step_num}/{self.total_steps}] {step.name} 시작..."
        print(progress_msg)
        
        if send_telegram and self.teleQ is not None:
            try:
                self.teleQ.put(progress_msg)
            except Exception:
                pass
        
        # Phase 전환 로깅
        self._check_and_log_phase_transition(step_num)
    
    def _check_and_log_phase_transition(self, step_num: int):
        """Phase 전환을 감지하고 로깅"""
        for phase_id, phase_info in self.PIPELINE_PHASES.items():
            start_step, end_step = phase_info['steps']
            if step_num == start_step:
                phase_msg = (
                    f"\n{'='*60}\n"
                    f"[Phase {phase_id}] {phase_info['name']}\n"
                    f"  {phase_info['description']}\n"
                    f"  Steps: {start_step}-{end_step}\n"
                    f"{'='*60}"
                )
                print(phase_msg)
                self.log_code_generation(f"Phase {phase_id} 시작: {phase_info['name']}")
                break
    
    def log_phase_summary(self):
        """전체 파이프라인 Phase 요약 로깅"""
        lines = [
            "",
            "=" * 60,
            "파이프라인 Phase 요약",
            "=" * 60,
        ]
        
        for phase_id, phase_info in self.PIPELINE_PHASES.items():
            start_step, end_step = phase_info['steps']
            
            # 해당 Phase의 단계들 상태 집계
            phase_steps = [self.pipeline_steps.get(i) for i in range(start_step, end_step + 1)]
            completed = sum(1 for s in phase_steps if s and s.status == 'completed')
            total = end_step - start_step + 1
            total_time = sum(s.duration_s for s in phase_steps if s and s.duration_s > 0)
            
            status = "✓" if completed == total else "○"
            lines.append(f"  [{status}] Phase {phase_id}: {phase_info['name']}")
            lines.append(f"      Steps {start_step}-{end_step}: {completed}/{total} 완료, {total_time:.2f}s")
        
        lines.append("=" * 60)
        
        summary = "\n".join(lines)
        print(summary)
        return summary
    
    def log_step_complete(
        self,
        step_num: int,
        metrics: Dict[str, Any] = None,
        notes: List[str] = None,
        send_telegram: bool = False
    ):
        """
        파이프라인 단계 완료 기록
        
        Args:
            step_num: 단계 번호
            metrics: 단계 결과 메트릭
            notes: 추가 노트
            send_telegram: 텔레그램 메시지 전송 여부
        """
        if step_num not in self.pipeline_steps:
            return
        
        step = self.pipeline_steps[step_num]
        step.end_time = time.perf_counter()
        step.duration_s = round(step.end_time - step.start_time, 4)
        step.status = "completed"
        
        if metrics:
            step.metrics.update(metrics)
        if notes:
            step.notes.extend(notes)
        
        # 완료 메시지
        complete_msg = f"[{step_num}/{self.total_steps}] {step.name} 완료 ({step.duration_s:.2f}s)"
        print(complete_msg)
        
        if send_telegram and self.teleQ is not None:
            try:
                self.teleQ.put(complete_msg)
            except Exception:
                pass
    
    def log_step_failed(self, step_num: int, error: str, send_telegram: bool = True):
        """
        파이프라인 단계 실패 기록
        
        Args:
            step_num: 단계 번호
            error: 에러 메시지
            send_telegram: 텔레그램 메시지 전송 여부
        """
        if step_num not in self.pipeline_steps:
            return
        
        step = self.pipeline_steps[step_num]
        step.end_time = time.perf_counter()
        step.duration_s = round(step.end_time - step.start_time, 4)
        step.status = "failed"
        step.notes.append(f"ERROR: {error}")
        
        self.errors.append(f"[Step {step_num}] {step.name}: {error}")
        
        # 실패 메시지
        fail_msg = f"[{step_num}/{self.total_steps}] {step.name} 실패: {error}"
        print(fail_msg)
        
        if send_telegram and self.teleQ is not None:
            try:
                self.teleQ.put(fail_msg)
            except Exception:
                pass
    
    def log_section(self, title: str, content: Dict[str, Any], notes: List[str] = None):
        """
        일반 섹션 로그 기록
        
        Args:
            title: 섹션 제목
            content: 섹션 내용 (딕셔너리)
            notes: 추가 노트
        """
        section = {
            "title": title,
            "timestamp": datetime.now().isoformat(),
            "content": content,
        }
        if notes:
            section["notes"] = notes
        
        self.sections.append(section)
    
    def log_filter_decision(
        self,
        filter_name: str,
        selected: bool,
        reason: str,
        improvement: int = 0,
        exclude_ratio: float = 0.0,
        p_value: float = None,
        cohens_d: float = None,
        is_significant: bool = False,
        is_stable: bool = False,
        stability_score: float = None,
        threshold: float = None,
        direction: str = None,
        original_trades: int = 0,
        remaining_trades: int = 0,
        original_profit: int = 0,
        remaining_profit: int = 0,
        apply_code: str = None,
        condition_expr: str = None,
    ):
        """
        필터 선택/제외 결정 기록 (상세 정보 포함)
        
        Args:
            filter_name: 필터명
            selected: 선택 여부
            reason: 결정 사유
            improvement: 수익 개선 금액
            exclude_ratio: 제외 비율 (0-1)
            p_value: p-value (통계적 유의성)
            cohens_d: Cohen's d (효과 크기)
            is_significant: 통계적 유의 여부
            is_stable: 기간별 안정성 여부
            stability_score: 안정성 점수
            threshold: 필터 임계값
            direction: 필터 방향 ('less' or 'greater')
            original_trades: 원본 거래 수
            remaining_trades: 필터 후 잔여 거래 수
            original_profit: 원본 수익금
            remaining_profit: 필터 후 수익금
            apply_code: 적용 코드 (예: 'and 등락율 < 25')
            condition_expr: 조건 표현식
        """
        decision = FilterDecision(
            filter_name=filter_name,
            selected=selected,
            reason=reason,
            improvement=improvement,
            exclude_ratio=exclude_ratio,
            p_value=p_value,
            cohens_d=cohens_d,
            is_significant=is_significant,
            is_stable=is_stable,
            stability_score=stability_score,
            threshold=threshold,
            direction=direction,
            original_trades=original_trades,
            remaining_trades=remaining_trades,
            original_profit=original_profit,
            remaining_profit=remaining_profit,
            apply_code=apply_code,
            condition_expr=condition_expr,
        )
        self.filter_decisions.append(decision)
    
    def log_filter_decisions_from_results(self, filter_results: List[Dict], total_trades: int = 0, total_profit: int = 0):
        """
        필터 분석 결과에서 결정 로그 일괄 생성 (상세 필드 포함)
        
        Args:
            filter_results: AnalyzeFilterEffectsEnhanced() 결과
            total_trades: 전체 거래 수 (원본)
            total_profit: 전체 수익금 (원본)
        """
        if not filter_results:
            return
        
        for f in filter_results:
            try:
                filter_name = f.get('필터명', 'Unknown')
                improvement = int(f.get('수익개선금액', 0) or 0)
                exclude_ratio = float(f.get('제외비율', 0) or 0) / 100.0
                p_value = f.get('p값')
                cohens_d = f.get('효과크기')
                is_significant = f.get('유의함') == '예'
                recommend = f.get('적용권장', '')
                
                # 추가 상세 필드 추출
                condition_expr = f.get('조건식', '')
                apply_code = f.get('적용코드', '')
                excluded_trades = int(f.get('제외거래수', 0) or 0)
                remaining_trades = int(f.get('잔여거래수', 0) or 0)
                excluded_profit = int(f.get('제외거래수익금', 0) or 0)
                remaining_profit = int(f.get('잔여거래수익금', 0) or 0)
                effect_interpretation = f.get('효과해석', '')
                confidence_interval = f.get('신뢰구간', None)
                
                # 필터 방향 추론 (조건식에서)
                direction = None
                threshold = None
                if condition_expr:
                    if '>=' in condition_expr:
                        direction = 'greater'
                    elif '<' in condition_expr:
                        direction = 'less'
                    # 임계값 추출 시도
                    import re
                    match = re.search(r'([<>=]+)\s*([\d.]+)', condition_expr)
                    if match:
                        try:
                            threshold = float(match.group(2))
                        except:
                            pass
                
                # 선택 여부 결정 (개선 > 0 && 유의함)
                selected = improvement > 0 and is_significant
                
                # 상세 사유 생성
                reasons = []
                if improvement > 0:
                    reasons.append(f"개선 +{improvement:,}원")
                else:
                    reasons.append(f"개선 {improvement:,}원 (음수/무효)")
                
                if is_significant:
                    reasons.append(f"통계적 유의 (p={p_value:.4f})" if isinstance(p_value, float) else f"통계적 유의 (p={p_value})")
                else:
                    reasons.append(f"통계적 비유의 (p={p_value:.4f})" if isinstance(p_value, float) else f"통계적 비유의 (p={p_value})")
                
                if effect_interpretation:
                    reasons.append(f"효과: {effect_interpretation}")
                
                if recommend:
                    reasons.append(f"권장: {recommend}")
                
                reason = " | ".join(reasons)
                
                self.log_filter_decision(
                    filter_name=filter_name,
                    selected=selected,
                    reason=reason,
                    improvement=improvement,
                    exclude_ratio=exclude_ratio,
                    p_value=p_value,
                    cohens_d=cohens_d,
                    is_significant=is_significant,
                    threshold=threshold,
                    direction=direction,
                    original_trades=total_trades or (excluded_trades + remaining_trades),
                    remaining_trades=remaining_trades,
                    original_profit=total_profit or (excluded_profit + remaining_profit),
                    remaining_profit=remaining_profit,
                    apply_code=apply_code,
                    condition_expr=condition_expr,
                )
            except Exception:
                continue
    
    def log_segment_definition(
        self,
        segment_id: str,
        cap_label: str,
        time_label: str,
        cap_range: tuple,
        time_range: tuple,
        trade_count: int,
        profit: int = 0,
        win_rate: float = 0.0,
        filters_applied: List[str] = None,
    ):
        """
        세그먼트 정의 기록
        
        Args:
            segment_id: 세그먼트 ID (예: "대형주_T1")
            cap_label: 시가총액 라벨 (예: "대형주")
            time_label: 시간대 라벨 (예: "T1")
            cap_range: 시가총액 범위 (min, max)
            time_range: 시간 범위 (start, end)
            trade_count: 거래 수
            profit: 수익금
            win_rate: 승률
            filters_applied: 적용된 필터 목록
        """
        segment = SegmentDefinition(
            segment_id=segment_id,
            cap_label=cap_label,
            time_label=time_label,
            cap_range=cap_range,
            time_range=time_range,
            trade_count=trade_count,
            profit=profit,
            win_rate=win_rate,
            filters_applied=filters_applied or [],
        )
        self.segment_definitions.append(segment)
    
    def log_variable_mapping(self, original: str, mapped: str, context: str = ""):
        """
        변수 매핑 기록
        
        Args:
            original: 원본 변수명
            mapped: 매핑된 변수명
            context: 컨텍스트/출처
        """
        self.variable_mappings.append({
            "original": original,
            "mapped": mapped,
            "context": context,
            "timestamp": datetime.now().isoformat(),
        })
    
    def log_code_generation(self, message: str):
        """
        조건식 생성 과정 로그
        
        Args:
            message: 로그 메시지
        """
        self.code_generation_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def log_warning(self, message: str):
        """경고 메시지 기록"""
        self.warnings.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def log_error(self, message: str):
        """에러 메시지 기록"""
        self.errors.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def log_threshold_calculation(
        self,
        column: str,
        direction: str,
        optimal_threshold: float,
        improvement: int,
        excluded_count: int,
        total_count: int,
        percentile: float = 0.0,
    ):
        """
        최적 임계값 탐색 과정 기록
        
        Args:
            column: 분석 대상 컬럼명
            direction: 'less' 또는 'greater'
            optimal_threshold: 찾아낸 최적 임계값
            improvement: 수익 개선 금액
            excluded_count: 제외되는 거래 수
            total_count: 전체 거래 수
            percentile: 임계값의 백분위 위치
        """
        dir_text = "미만 제외" if direction == 'less' else "이상 제외"
        exclude_ratio = excluded_count / total_count * 100 if total_count > 0 else 0
        
        msg = (
            f"임계값 탐색: {column}\n"
            f"  방향: {dir_text}\n"
            f"  최적값: {optimal_threshold} (백분위: {percentile:.1f}%)\n"
            f"  제외: {excluded_count:,}건/{total_count:,}건 ({exclude_ratio:.1f}%)\n"
            f"  개선: {improvement:+,}원"
        )
        self.log_code_generation(msg)
    
    def log_segment_boundary_calculation(
        self,
        segment_type: str,
        mode: str,
        boundaries: List[tuple],
        trade_distribution: Dict[str, int] = None,
    ):
        """
        세그먼트 경계 계산 과정 기록
        
        Args:
            segment_type: 'cap' (시가총액) 또는 'time' (시간대)
            mode: 'dynamic' 또는 'fixed'
            boundaries: [(label, min, max), ...] 형태의 경계 리스트
            trade_distribution: 세그먼트별 거래 수 분포
        """
        type_text = "시가총액" if segment_type == 'cap' else "시간대"
        mode_text = "동적(분위수)" if mode == 'dynamic' else "고정(사용자정의)"
        
        lines = [
            f"세그먼트 경계 계산: {type_text}",
            f"  모드: {mode_text}",
            f"  경계:",
        ]
        
        for label, min_val, max_val in boundaries:
            if segment_type == 'cap':
                lines.append(f"    {label}: {min_val:,.0f}억 ~ {max_val:,.0f}억")
            else:
                lines.append(f"    {label}: {min_val} ~ {max_val}")
            
            if trade_distribution and label in trade_distribution:
                lines.append(f"      거래수: {trade_distribution[label]:,}건")
        
        self.log_code_generation("\n".join(lines))
    
    def log_combination_evaluation(
        self,
        filter_names: List[str],
        individual_improvements: List[int],
        combined_improvement: int,
        synergy: int,
        synergy_ratio: float,
        excluded_ratio: float,
        recommendation: str,
    ):
        """
        필터 조합 평가 결과 기록
        
        Args:
            filter_names: 조합된 필터명 리스트
            individual_improvements: 개별 필터 개선 금액 리스트
            combined_improvement: 조합 적용 시 개선 금액
            synergy: 시너지 효과 금액 (조합 - 개별 합)
            synergy_ratio: 시너지 비율 (%)
            excluded_ratio: 조합 적용 시 제외 비율 (%)
            recommendation: 권장 등급 (★★★ 등)
        """
        individual_sum = sum(individual_improvements)
        
        lines = [
            f"필터 조합 평가: {' + '.join(filter_names)}",
            f"  개별 개선 합: {individual_sum:+,}원",
            f"  조합 개선: {combined_improvement:+,}원",
            f"  시너지: {synergy:+,}원 ({synergy_ratio:+.1f}%)",
            f"  제외율: {excluded_ratio:.1f}%",
            f"  권장: {recommendation}" if recommendation else "",
        ]
        
        self.log_code_generation("\n".join([l for l in lines if l]))
    
    def log_filter_stability_result(
        self,
        filter_name: str,
        period_results: List[Dict[str, Any]],
        consistency_score: float,
        is_stable: bool,
    ):
        """
        필터 안정성 검증 결과 기록
        
        Args:
            filter_name: 필터명
            period_results: 기간별 결과 [{period, improvement, win_rate}, ...]
            consistency_score: 일관성 점수 (0-100)
            is_stable: 안정적 여부
        """
        stable_text = "안정" if is_stable else "불안정"
        
        lines = [
            f"필터 안정성: {filter_name}",
            f"  일관성 점수: {consistency_score:.1f}점 [{stable_text}]",
            f"  기간별 결과:",
        ]
        
        for pr in period_results:
            period = pr.get('period', '?')
            improvement = pr.get('improvement', 0)
            win_rate = pr.get('win_rate', 0)
            sign = "+" if improvement > 0 else ""
            lines.append(f"    {period}: {sign}{improvement:,}원, 승률 {win_rate:.1f}%")
        
        self.log_code_generation("\n".join(lines))
    
    def get_summary(self) -> Dict[str, Any]:
        """분석 요약 반환"""
        end_time = datetime.now()
        total_duration = time.perf_counter() - self.start_perf
        
        # 단계별 상태 집계
        step_stats = {"completed": 0, "failed": 0, "pending": 0, "in_progress": 0}
        for step in self.pipeline_steps.values():
            step_stats[step.status] = step_stats.get(step.status, 0) + 1
        
        # 필터 선택 집계
        selected_filters = [f for f in self.filter_decisions if f.selected]
        rejected_filters = [f for f in self.filter_decisions if not f.selected]
        
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_s": round(total_duration, 2),
            "total_steps": self.total_steps,
            "step_stats": step_stats,
            "filter_decisions": {
                "total": len(self.filter_decisions),
                "selected": len(selected_filters),
                "rejected": len(rejected_filters),
            },
            "segment_definitions": len(self.segment_definitions),
            "variable_mappings": len(self.variable_mappings),
            "warnings": len(self.warnings),
            "errors": len(self.errors),
        }
    
    def _format_filter_decision(self, d: FilterDecision) -> str:
        """필터 결정을 문자열로 포맷 (상세 정보 포함)"""
        status = "✓ 선택" if d.selected else "✗ 제외"
        lines = [
            f"  ┌─ {d.filter_name}: [{status}]",
            f"  │  사유: {d.reason}",
        ]
        
        # 거래 수 변화
        if d.original_trades > 0:
            lines.append(f"  │  거래수: {d.original_trades:,}건 → {d.remaining_trades:,}건 (제외율 {d.exclude_ratio*100:.1f}%)")
        else:
            lines.append(f"  │  제외율: {d.exclude_ratio*100:.1f}%")
        
        # 수익 변화
        if d.original_profit != 0 or d.remaining_profit != 0:
            lines.append(f"  │  수익금: {d.original_profit:,}원 → {d.remaining_profit:,}원 (개선 {d.improvement:+,}원)")
        else:
            lines.append(f"  │  개선: {d.improvement:+,}원")
        
        # 통계적 유의성
        if d.p_value is not None:
            p_str = f"{d.p_value:.4f}" if isinstance(d.p_value, float) else str(d.p_value)
            d_str = f"{d.cohens_d:.3f}" if isinstance(d.cohens_d, float) else str(d.cohens_d)
            sig_mark = "✓" if d.is_significant else "✗"
            lines.append(f"  │  통계: p={p_str}, Cohen's d={d_str} [{sig_mark} {'유의' if d.is_significant else '비유의'}]")
        
        # 안정성 점수
        if d.stability_score is not None:
            stable_mark = "✓" if d.is_stable else "✗"
            lines.append(f"  │  안정성: {d.stability_score:.1f}점 [{stable_mark} {'안정' if d.is_stable else '불안정'}]")
        
        # 임계값 및 방향
        if d.threshold is not None:
            dir_text = "미만 제외" if d.direction == 'less' else "이상 제외" if d.direction == 'greater' else ""
            lines.append(f"  │  임계값: {d.threshold} ({dir_text})")
        
        # 적용 코드 (있으면)
        if d.apply_code:
            lines.append(f"  │  적용코드: {d.apply_code}")
        
        # 조건식 (있으면)
        if d.condition_expr:
            # 긴 조건식은 줄여서 표시
            expr_display = d.condition_expr if len(d.condition_expr) <= 60 else d.condition_expr[:57] + "..."
            lines.append(f"  │  조건식: {expr_display}")
        
        lines.append(f"  └─")
        return "\n".join(lines)
    
    def _format_segment_definition(self, s: SegmentDefinition) -> str:
        """세그먼트 정의를 문자열로 포맷"""
        cap_min, cap_max = s.cap_range
        time_start, time_end = s.time_range
        
        lines = [
            f"  - {s.segment_id}:",
            f"    시가총액: {s.cap_label} ({cap_min:,.0f}억 ~ {cap_max:,.0f}억)",
            f"    시간대: {s.time_label} ({time_start} ~ {time_end})",
            f"    거래수: {s.trade_count:,}건, 수익: {s.profit:,}원, 승률: {s.win_rate:.1f}%",
        ]
        if s.filters_applied:
            lines.append(f"    적용 필터: {', '.join(s.filters_applied)}")
        return "\n".join(lines)
    
    def _format_pipeline_step(self, step: PipelineStep) -> str:
        """파이프라인 단계를 문자열로 포맷"""
        status_emoji = {
            "completed": "OK",
            "failed": "FAIL",
            "in_progress": "...",
            "pending": "-",
        }
        status = status_emoji.get(step.status, step.status)
        
        lines = [
            f"  [{step.step_num}/{step.total_steps}] {step.name} [{status}]",
            f"    설명: {step.description}",
            f"    소요시간: {step.duration_s:.2f}s",
        ]
        
        if step.metrics:
            metrics_str = ", ".join(f"{k}={v}" for k, v in step.metrics.items())
            lines.append(f"    메트릭: {metrics_str}")
        
        if step.notes:
            for note in step.notes:
                lines.append(f"    - {note}")
        
        return "\n".join(lines)
    
    def save(self) -> Optional[str]:
        """
        로그 파일 저장
        
        Returns:
            저장된 파일 경로 또는 None (실패 시)
        """
        try:
            summary = self.get_summary()
            
            lines = []
            lines.append("=" * 80)
            lines.append("강화된 백테스팅 분석 로그")
            lines.append("=" * 80)
            lines.append("")
            
            # 요약 정보
            lines.append("## 분석 요약")
            lines.append(f"시작: {summary['start_time']}")
            lines.append(f"종료: {summary['end_time']}")
            lines.append(f"총 소요 시간: {summary['total_duration_s']:.2f}초")
            lines.append(f"전략명: {self.save_file_name}")
            lines.append(f"출력 디렉토리: {self.output_dir}")
            lines.append("")
            
            # 파이프라인 Phase 요약 (개선된 3단계 구조)
            lines.append("## 파이프라인 Phase 요약")
            lines.append("```")
            lines.append("개선된 파이프라인 흐름:")
            lines.append("  Phase A: 일반 필터 분석 (전체 데이터)")
            lines.append("      ↓")
            lines.append("  Phase B: 결과 저장 (CSV/차트)")
            lines.append("      ↓")
            lines.append("  Phase C: 세그먼트 분석 → 세그먼트별 조건식 생성")
            lines.append("```")
            lines.append("")
            
            for phase_id, phase_info in self.PIPELINE_PHASES.items():
                start_step, end_step = phase_info['steps']
                phase_steps = [self.pipeline_steps.get(i) for i in range(start_step, end_step + 1)]
                completed = sum(1 for s in phase_steps if s and s.status == 'completed')
                total = end_step - start_step + 1
                total_time = sum(s.duration_s for s in phase_steps if s and s.duration_s > 0)
                status = "✓" if completed == total else "○"
                lines.append(f"  [{status}] Phase {phase_id}: {phase_info['name']}")
                lines.append(f"      Steps {start_step}-{end_step}: {completed}/{total} 완료, {total_time:.2f}s")
            lines.append("")
            
            # 단계별 상태
            lines.append("## 파이프라인 단계 상태")
            lines.append(f"완료: {summary['step_stats']['completed']}/{summary['total_steps']}")
            lines.append(f"실패: {summary['step_stats']['failed']}")
            lines.append("")
            
            # 파이프라인 상세
            lines.append("### 파이프라인 상세")
            for step_num in sorted(self.pipeline_steps.keys()):
                step = self.pipeline_steps[step_num]
                lines.append(self._format_pipeline_step(step))
                lines.append("")
            
            # 필터 결정
            lines.append("-" * 80)
            lines.append("## 필터 결정 로그")
            lines.append(f"총 필터: {summary['filter_decisions']['total']}개")
            lines.append(f"선택: {summary['filter_decisions']['selected']}개")
            lines.append(f"제외: {summary['filter_decisions']['rejected']}개")
            lines.append("")
            
            if self.filter_decisions:
                lines.append("### 선택된 필터")
                for d in self.filter_decisions:
                    if d.selected:
                        lines.append(self._format_filter_decision(d))
                        lines.append("")
                
                lines.append("### 제외된 필터")
                for d in self.filter_decisions:
                    if not d.selected:
                        lines.append(self._format_filter_decision(d))
                        lines.append("")
            
            # 세그먼트 정의
            if self.segment_definitions:
                lines.append("-" * 80)
                lines.append("## 세그먼트 정의")
                lines.append(f"총 세그먼트: {len(self.segment_definitions)}개")
                lines.append("")
                
                for s in self.segment_definitions:
                    lines.append(self._format_segment_definition(s))
                    lines.append("")
            
            # 변수 매핑
            if self.variable_mappings:
                lines.append("-" * 80)
                lines.append("## 변수 매핑 로그")
                for m in self.variable_mappings:
                    lines.append(f"  {m['original']} -> {m['mapped']} ({m['context']})")
                lines.append("")
            
            # 조건식 생성 로그
            if self.code_generation_logs:
                lines.append("-" * 80)
                lines.append("## 조건식 생성 로그")
                for log in self.code_generation_logs:
                    lines.append(f"  {log}")
                lines.append("")
            
            # 일반 섹션
            if self.sections:
                lines.append("-" * 80)
                lines.append("## 추가 섹션")
                for section in self.sections:
                    lines.append(f"### {section['title']} ({section['timestamp']})")
                    for k, v in section.get('content', {}).items():
                        lines.append(f"  {k}: {v}")
                    if section.get('notes'):
                        for note in section['notes']:
                            lines.append(f"  - {note}")
                    lines.append("")
            
            # 경고/에러
            if self.warnings:
                lines.append("-" * 80)
                lines.append("## 경고")
                for w in self.warnings:
                    lines.append(f"  [WARN] {w}")
                lines.append("")
            
            if self.errors:
                lines.append("-" * 80)
                lines.append("## 에러")
                for e in self.errors:
                    lines.append(f"  [ERROR] {e}")
                lines.append("")
            
            lines.append("=" * 80)
            lines.append("분석 로그 종료")
            lines.append("=" * 80)
            
            # 파일 저장
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.log_path.write_text("\n".join(lines), encoding='utf-8-sig')
            
            print(f"[Analysis Logger] 로그 파일 저장: {self.log_path}")
            return str(self.log_path)
            
        except Exception as e:
            print(f"[Analysis Logger] 로그 저장 실패: {e}")
            return None
    
    def send_progress_summary(self, current_step: int = None, custom_message: str = None):
        """
        진행 상황 요약을 텔레그램으로 전송
        
        Args:
            current_step: 현재 단계 (None이면 전체 요약)
            custom_message: 커스텀 메시지 (선택)
        """
        if self.teleQ is None:
            return
        
        try:
            if custom_message:
                self.teleQ.put(custom_message)
                return
            
            if current_step is not None:
                step = self.pipeline_steps.get(current_step)
                if step:
                    msg = f"[{current_step}/{self.total_steps}] {step.name}"
                    if step.status == "completed":
                        msg += f" 완료 ({step.duration_s:.1f}s)"
                    elif step.status == "in_progress":
                        msg += " 진행 중..."
                    elif step.status == "failed":
                        msg += " 실패"
                    self.teleQ.put(msg)
            else:
                # 전체 요약
                summary = self.get_summary()
                msg = (
                    f"분석 진행 상황:\n"
                    f"- 완료: {summary['step_stats']['completed']}/{summary['total_steps']}\n"
                    f"- 소요시간: {summary['total_duration_s']:.1f}초\n"
                    f"- 필터 선택: {summary['filter_decisions']['selected']}/{summary['filter_decisions']['total']}"
                )
                self.teleQ.put(msg)
        except Exception:
            pass
    
    def send_phase_notification(self, phase_id: str, status: str = 'start'):
        """
        Phase 전환 알림을 텔레그램으로 전송
        
        Args:
            phase_id: 'A', 'B', 또는 'C'
            status: 'start' 또는 'complete'
        """
        if self.teleQ is None:
            return
        
        phase_info = self.PIPELINE_PHASES.get(phase_id)
        if not phase_info:
            return
        
        try:
            if status == 'start':
                msg = f"📊 [Phase {phase_id}] {phase_info['name']} 시작\n└ {phase_info['description']}"
            else:
                start_step, end_step = phase_info['steps']
                phase_steps = [self.pipeline_steps.get(i) for i in range(start_step, end_step + 1)]
                total_time = sum(s.duration_s for s in phase_steps if s and s.duration_s > 0)
                msg = f"✅ [Phase {phase_id}] {phase_info['name']} 완료 ({total_time:.1f}s)"
            
            self.teleQ.put(msg)
        except Exception:
            pass
    
    def send_filter_summary(self, top_n: int = 5):
        """
        상위 필터 결정 요약을 텔레그램으로 전송
        
        Args:
            top_n: 표시할 상위 필터 수
        """
        if self.teleQ is None or not self.filter_decisions:
            return
        
        try:
            # 선택된 필터 중 개선금액 상위 N개
            selected = sorted(
                [f for f in self.filter_decisions if f.selected],
                key=lambda x: x.improvement,
                reverse=True
            )[:top_n]
            
            if not selected:
                return
            
            lines = ["📈 선택된 필터 TOP5:"]
            total_improvement = 0
            for f in selected:
                imp_str = f"+{f.improvement:,}원" if f.improvement > 0 else f"{f.improvement:,}원"
                lines.append(f"  • {f.filter_name}: {imp_str}")
                total_improvement += f.improvement
            
            lines.append(f"└ 총 개선: {total_improvement:+,}원")
            
            self.teleQ.put("\n".join(lines))
        except Exception:
            pass
    
    def send_pipeline_complete(self):
        """
        파이프라인 완료 요약을 텔레그램으로 전송
        """
        if self.teleQ is None:
            return
        
        try:
            summary = self.get_summary()
            
            # Phase별 시간
            phase_times = {}
            for phase_id, phase_info in self.PIPELINE_PHASES.items():
                start_step, end_step = phase_info['steps']
                phase_steps = [self.pipeline_steps.get(i) for i in range(start_step, end_step + 1)]
                phase_times[phase_id] = sum(s.duration_s for s in phase_steps if s and s.duration_s > 0)
            
            lines = [
                "🏁 강화 분석 완료",
                f"  총 소요시간: {summary['total_duration_s']:.1f}초",
                f"  ├ Phase A (일반필터): {phase_times.get('A', 0):.1f}s",
                f"  ├ Phase B (저장): {phase_times.get('B', 0):.1f}s",
                f"  └ Phase C (세그먼트): {phase_times.get('C', 0):.1f}s",
                "",
                f"📊 필터: {summary['filter_decisions']['selected']}/{summary['filter_decisions']['total']} 선택",
                f"📁 세그먼트: {summary['segment_definitions']}개",
            ]
            
            if summary['errors']:
                lines.append(f"⚠️ 에러: {summary['errors']}개")
            
            self.teleQ.put("\n".join(lines))
        except Exception:
            pass


def create_analysis_logger(
    output_dir: str,
    save_file_name: str,
    teleQ=None,
    total_steps: int = 12
) -> AnalysisLogger:
    """
    분석 로거 생성 헬퍼 함수
    
    Args:
        output_dir: 출력 디렉토리
        save_file_name: 저장 파일명
        teleQ: 텔레그램 큐 (선택)
        total_steps: 총 단계 수
    
    Returns:
        초기화된 AnalysisLogger 인스턴스
    """
    logger = AnalysisLogger(output_dir, save_file_name, teleQ)
    logger.start_pipeline(total_steps)
    return logger
