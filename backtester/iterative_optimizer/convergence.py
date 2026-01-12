"""
반복적 조건식 개선 시스템 (ICOS) - 수렴 판정기.

Iterative Condition Optimization System - Convergence Checker.

이 모듈은 반복 최적화의 수렴 여부를 판정합니다.
세 가지 수렴 판정 방법을 지원합니다:
- IMPROVEMENT_RATE: 개선율이 임계값 이하일 때 수렴
- ABSOLUTE_CHANGE: 절대 변화량이 임계값 이하일 때 수렴
- CONSECUTIVE_NO_IMPROVE: 연속 미개선 횟수가 임계값 이상일 때 수렴

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from .config import IterativeConfig, ConvergenceConfig, ConvergenceMethod, FilterMetric
from .data_types import IterationResult
from .comparator import ResultComparator, ComparisonResult


class ConvergenceReason(Enum):
    """수렴 사유 열거형."""
    NOT_CONVERGED = "not_converged"
    IMPROVEMENT_RATE_BELOW_THRESHOLD = "improvement_rate_below_threshold"
    ABSOLUTE_CHANGE_BELOW_THRESHOLD = "absolute_change_below_threshold"
    CONSECUTIVE_NO_IMPROVE_EXCEEDED = "consecutive_no_improve_exceeded"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    MIN_ITERATIONS_NOT_MET = "min_iterations_not_met"
    EARLY_STOPPING = "early_stopping"


@dataclass
class ConvergenceResult:
    """수렴 판정 결과.

    Attributes:
        is_converged: 수렴 여부
        reason: 수렴/미수렴 사유
        method_used: 사용된 수렴 판정 방법
        iterations_completed: 완료된 반복 횟수
        iterations_since_improvement: 마지막 개선 이후 반복 횟수
        last_improvement_rate: 마지막 개선율
        total_improvement_rate: 초기 대비 총 개선율
        details: 추가 상세 정보
    """
    is_converged: bool
    reason: ConvergenceReason
    method_used: ConvergenceMethod
    iterations_completed: int
    iterations_since_improvement: int = 0
    last_improvement_rate: float = 0.0
    total_improvement_rate: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'is_converged': self.is_converged,
            'reason': self.reason.value,
            'method_used': self.method_used.value,
            'iterations_completed': self.iterations_completed,
            'iterations_since_improvement': self.iterations_since_improvement,
            'last_improvement_rate': self.last_improvement_rate,
            'total_improvement_rate': self.total_improvement_rate,
            'details': self.details,
        }

    @property
    def reason_description(self) -> str:
        """사유에 대한 한국어 설명 반환."""
        descriptions = {
            ConvergenceReason.NOT_CONVERGED: "아직 수렴하지 않음",
            ConvergenceReason.IMPROVEMENT_RATE_BELOW_THRESHOLD:
                f"개선율({self.last_improvement_rate:.1%})이 임계값 이하",
            ConvergenceReason.ABSOLUTE_CHANGE_BELOW_THRESHOLD:
                "절대 변화량이 임계값 이하",
            ConvergenceReason.CONSECUTIVE_NO_IMPROVE_EXCEEDED:
                f"연속 {self.iterations_since_improvement}회 미개선",
            ConvergenceReason.MAX_ITERATIONS_REACHED:
                f"최대 반복 횟수({self.iterations_completed}회) 도달",
            ConvergenceReason.MIN_ITERATIONS_NOT_MET:
                "최소 반복 횟수 미충족",
            ConvergenceReason.EARLY_STOPPING:
                "조기 종료 조건 충족",
        }
        return descriptions.get(self.reason, "알 수 없는 사유")


class ConvergenceChecker:
    """수렴 판정기.

    반복 최적화의 수렴 여부를 판정합니다.

    Attributes:
        config: ICOS 설정
        comparator: 결과 비교기

    Example:
        >>> checker = ConvergenceChecker(config)
        >>> result = checker.check(iterations)
        >>> if result.is_converged:
        ...     print(f"수렴 완료: {result.reason_description}")
    """

    def __init__(self, config: IterativeConfig):
        """ConvergenceChecker 초기화.

        Args:
            config: ICOS 설정
        """
        self.config = config
        self.comparator = ResultComparator(config)

        # 내부 상태
        self._consecutive_no_improve_count = 0
        self._last_best_value: Optional[float] = None
        self._comparison_history: List[ComparisonResult] = []

    def reset(self) -> None:
        """내부 상태 초기화."""
        self._consecutive_no_improve_count = 0
        self._last_best_value = None
        self._comparison_history = []

    def check(
        self,
        iterations: List[IterationResult],
        force_check: bool = False,
    ) -> ConvergenceResult:
        """수렴 여부 판정.

        Args:
            iterations: 반복 결과 목록
            force_check: 최소 반복 횟수 무시 여부

        Returns:
            ConvergenceResult: 수렴 판정 결과
        """
        conv_config = self.config.convergence
        n_iterations = len(iterations)

        # 반복 결과가 없거나 1개만 있으면 수렴 불가
        if n_iterations < 2:
            return ConvergenceResult(
                is_converged=False,
                reason=ConvergenceReason.MIN_ITERATIONS_NOT_MET,
                method_used=conv_config.method,
                iterations_completed=n_iterations,
            )

        # 최소 반복 횟수 체크
        if not force_check and n_iterations < conv_config.min_iterations:
            return ConvergenceResult(
                is_converged=False,
                reason=ConvergenceReason.MIN_ITERATIONS_NOT_MET,
                method_used=conv_config.method,
                iterations_completed=n_iterations,
            )

        # 가장 최근 두 반복 비교
        prev_iter = iterations[-2]
        curr_iter = iterations[-1]
        comparison = self.comparator.compare(prev_iter, curr_iter)
        self._comparison_history.append(comparison)

        # 총 개선율 계산
        total_improvement = self.comparator.calculate_total_improvement(
            iterations[0], iterations[-1]
        )

        # 수렴 판정 방법에 따라 분기
        if conv_config.method == ConvergenceMethod.IMPROVEMENT_RATE:
            return self._check_improvement_rate(
                iterations, comparison, total_improvement, conv_config
            )
        elif conv_config.method == ConvergenceMethod.ABSOLUTE_CHANGE:
            return self._check_absolute_change(
                iterations, comparison, total_improvement, conv_config
            )
        elif conv_config.method == ConvergenceMethod.CONSECUTIVE_NO_IMPROVE:
            return self._check_consecutive_no_improve(
                iterations, comparison, total_improvement, conv_config
            )
        else:
            # 기본: 개선율 기반
            return self._check_improvement_rate(
                iterations, comparison, total_improvement, conv_config
            )

    def _check_improvement_rate(
        self,
        iterations: List[IterationResult],
        comparison: ComparisonResult,
        total_improvement: float,
        conv_config: ConvergenceConfig,
    ) -> ConvergenceResult:
        """개선율 기반 수렴 판정.

        Args:
            iterations: 반복 결과 목록
            comparison: 최근 비교 결과
            total_improvement: 총 개선율
            conv_config: 수렴 설정

        Returns:
            ConvergenceResult: 수렴 판정 결과
        """
        # 타겟 메트릭 개선율 확인
        if comparison.target_metric_comparison:
            improvement_rate = abs(comparison.target_metric_comparison.percent_change)
        else:
            improvement_rate = abs(comparison.improvement_score)

        # 연속 미개선 카운트 업데이트
        if comparison.overall_improved:
            self._consecutive_no_improve_count = 0
        else:
            self._consecutive_no_improve_count += 1

        # 수렴 판정: 개선율이 임계값 이하
        is_converged = improvement_rate < conv_config.threshold

        if is_converged:
            reason = ConvergenceReason.IMPROVEMENT_RATE_BELOW_THRESHOLD
        else:
            reason = ConvergenceReason.NOT_CONVERGED

        return ConvergenceResult(
            is_converged=is_converged,
            reason=reason,
            method_used=ConvergenceMethod.IMPROVEMENT_RATE,
            iterations_completed=len(iterations),
            iterations_since_improvement=self._consecutive_no_improve_count,
            last_improvement_rate=improvement_rate,
            total_improvement_rate=total_improvement,
            details={
                'threshold': conv_config.threshold,
                'comparison_summary': comparison.summary,
                'improved_metrics': comparison.get_improved_metrics(),
                'degraded_metrics': comparison.get_degraded_metrics(),
            }
        )

    def _check_absolute_change(
        self,
        iterations: List[IterationResult],
        comparison: ComparisonResult,
        total_improvement: float,
        conv_config: ConvergenceConfig,
    ) -> ConvergenceResult:
        """절대 변화량 기반 수렴 판정.

        Args:
            iterations: 반복 결과 목록
            comparison: 최근 비교 결과
            total_improvement: 총 개선율
            conv_config: 수렴 설정

        Returns:
            ConvergenceResult: 수렴 판정 결과
        """
        # 타겟 메트릭 절대 변화량 확인
        if comparison.target_metric_comparison:
            absolute_change = abs(comparison.target_metric_comparison.absolute_change)
            improvement_rate = abs(comparison.target_metric_comparison.percent_change)
        else:
            # 타겟 메트릭이 없으면 총 수익금 사용
            profit_metrics = ['total_profit', '수익금']
            absolute_change = 0.0
            for metric in profit_metrics:
                if metric in comparison.metric_comparisons:
                    absolute_change = abs(
                        comparison.metric_comparisons[metric].absolute_change
                    )
                    break
            improvement_rate = abs(comparison.improvement_score)

        # 연속 미개선 카운트 업데이트
        if comparison.overall_improved:
            self._consecutive_no_improve_count = 0
        else:
            self._consecutive_no_improve_count += 1

        # 수렴 판정: 절대 변화량이 임계값 이하
        is_converged = absolute_change < conv_config.threshold

        if is_converged:
            reason = ConvergenceReason.ABSOLUTE_CHANGE_BELOW_THRESHOLD
        else:
            reason = ConvergenceReason.NOT_CONVERGED

        return ConvergenceResult(
            is_converged=is_converged,
            reason=reason,
            method_used=ConvergenceMethod.ABSOLUTE_CHANGE,
            iterations_completed=len(iterations),
            iterations_since_improvement=self._consecutive_no_improve_count,
            last_improvement_rate=improvement_rate,
            total_improvement_rate=total_improvement,
            details={
                'threshold': conv_config.threshold,
                'absolute_change': absolute_change,
                'comparison_summary': comparison.summary,
            }
        )

    def _check_consecutive_no_improve(
        self,
        iterations: List[IterationResult],
        comparison: ComparisonResult,
        total_improvement: float,
        conv_config: ConvergenceConfig,
    ) -> ConvergenceResult:
        """연속 미개선 횟수 기반 수렴 판정.

        Args:
            iterations: 반복 결과 목록
            comparison: 최근 비교 결과
            total_improvement: 총 개선율
            conv_config: 수렴 설정

        Returns:
            ConvergenceResult: 수렴 판정 결과
        """
        # 연속 미개선 카운트 업데이트
        if comparison.overall_improved:
            self._consecutive_no_improve_count = 0
        else:
            self._consecutive_no_improve_count += 1

        # 개선율 계산
        if comparison.target_metric_comparison:
            improvement_rate = abs(comparison.target_metric_comparison.percent_change)
        else:
            improvement_rate = abs(comparison.improvement_score)

        # 수렴 판정: 연속 미개선 횟수가 임계값 이상
        # threshold는 정수로 해석 (예: 3.0 → 3회)
        threshold_count = int(conv_config.threshold)
        is_converged = self._consecutive_no_improve_count >= threshold_count

        if is_converged:
            reason = ConvergenceReason.CONSECUTIVE_NO_IMPROVE_EXCEEDED
        else:
            reason = ConvergenceReason.NOT_CONVERGED

        return ConvergenceResult(
            is_converged=is_converged,
            reason=reason,
            method_used=ConvergenceMethod.CONSECUTIVE_NO_IMPROVE,
            iterations_completed=len(iterations),
            iterations_since_improvement=self._consecutive_no_improve_count,
            last_improvement_rate=improvement_rate,
            total_improvement_rate=total_improvement,
            details={
                'threshold_count': threshold_count,
                'current_count': self._consecutive_no_improve_count,
                'comparison_summary': comparison.summary,
            }
        )

    def check_max_iterations(
        self,
        iterations: List[IterationResult],
        max_iterations: int,
    ) -> ConvergenceResult:
        """최대 반복 횟수 도달 여부 확인.

        Args:
            iterations: 반복 결과 목록
            max_iterations: 최대 반복 횟수

        Returns:
            ConvergenceResult: 수렴 판정 결과
        """
        n_iterations = len(iterations)
        is_converged = n_iterations >= max_iterations

        # 총 개선율 계산
        if n_iterations >= 2:
            total_improvement = self.comparator.calculate_total_improvement(
                iterations[0], iterations[-1]
            )
            # 마지막 비교
            comparison = self.comparator.compare(iterations[-2], iterations[-1])
            if comparison.target_metric_comparison:
                last_improvement_rate = abs(
                    comparison.target_metric_comparison.percent_change
                )
            else:
                last_improvement_rate = abs(comparison.improvement_score)
        else:
            total_improvement = 0.0
            last_improvement_rate = 0.0

        return ConvergenceResult(
            is_converged=is_converged,
            reason=(ConvergenceReason.MAX_ITERATIONS_REACHED
                    if is_converged else ConvergenceReason.NOT_CONVERGED),
            method_used=self.config.convergence.method,
            iterations_completed=n_iterations,
            iterations_since_improvement=self._consecutive_no_improve_count,
            last_improvement_rate=last_improvement_rate,
            total_improvement_rate=total_improvement,
            details={
                'max_iterations': max_iterations,
            }
        )

    def should_early_stop(
        self,
        iterations: List[IterationResult],
        degradation_threshold: float = -0.2,
    ) -> bool:
        """조기 종료 조건 확인.

        성과가 크게 악화되면 조기 종료를 권장합니다.

        Args:
            iterations: 반복 결과 목록
            degradation_threshold: 악화 임계값 (기본 -20%)

        Returns:
            조기 종료 권장 여부
        """
        if len(iterations) < 2:
            return False

        # 초기 대비 현재 성과 비교
        total_improvement = self.comparator.calculate_total_improvement(
            iterations[0], iterations[-1]
        )

        # 성과가 크게 악화되면 조기 종료 권장
        return total_improvement < degradation_threshold

    def get_comparison_history(self) -> List[ComparisonResult]:
        """비교 이력 반환.

        Returns:
            비교 결과 목록
        """
        return self._comparison_history.copy()

    def get_summary(self, iterations: List[IterationResult]) -> str:
        """수렴 상태 요약 문자열 생성.

        Args:
            iterations: 반복 결과 목록

        Returns:
            요약 문자열
        """
        if not iterations:
            return "반복 결과 없음"

        result = self.check(iterations)

        lines = [
            "=" * 50,
            "수렴 판정 요약",
            "=" * 50,
            f"완료된 반복: {result.iterations_completed}회",
            f"수렴 여부: {'예' if result.is_converged else '아니오'}",
            f"사유: {result.reason_description}",
            f"판정 방법: {result.method_used.value}",
            f"마지막 개선율: {result.last_improvement_rate:.2%}",
            f"총 개선율: {result.total_improvement_rate:.2%}",
        ]

        if result.iterations_since_improvement > 0:
            lines.append(
                f"연속 미개선: {result.iterations_since_improvement}회"
            )

        lines.append("=" * 50)

        return '\n'.join(lines)
