"""
반복적 조건식 개선 시스템 (ICOS) - 결과 비교기.

Iterative Condition Optimization System - Result Comparator.

이 모듈은 반복 간 결과를 비교하고 개선율을 계산합니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

from .config import IterativeConfig, FilterMetric
from .data_types import IterationResult


class ImprovementDirection(Enum):
    """개선 방향 열거형.

    - HIGHER_IS_BETTER: 값이 높을수록 좋음 (수익, 승률 등)
    - LOWER_IS_BETTER: 값이 낮을수록 좋음 (MDD, 손실 등)
    """
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


@dataclass
class MetricComparison:
    """단일 메트릭 비교 결과.

    Attributes:
        metric_name: 메트릭 이름
        previous_value: 이전 값
        current_value: 현재 값
        absolute_change: 절대 변화량
        percent_change: 퍼센트 변화율
        direction: 개선 방향
        improved: 개선 여부
    """
    metric_name: str
    previous_value: float
    current_value: float
    absolute_change: float
    percent_change: float
    direction: ImprovementDirection
    improved: bool

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'metric_name': self.metric_name,
            'previous_value': self.previous_value,
            'current_value': self.current_value,
            'absolute_change': self.absolute_change,
            'percent_change': self.percent_change,
            'direction': self.direction.value,
            'improved': self.improved,
        }


@dataclass
class ComparisonResult:
    """반복 비교 결과.

    Attributes:
        previous_iteration: 이전 반복 번호
        current_iteration: 현재 반복 번호
        metric_comparisons: 각 메트릭별 비교 결과
        target_metric_comparison: 타겟 메트릭 비교 결과
        overall_improved: 전체적으로 개선되었는지 여부
        improvement_score: 종합 개선 점수 (-1.0 ~ 1.0)
        summary: 요약 문자열
    """
    previous_iteration: int
    current_iteration: int
    metric_comparisons: Dict[str, MetricComparison]
    target_metric_comparison: Optional[MetricComparison]
    overall_improved: bool
    improvement_score: float
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'previous_iteration': self.previous_iteration,
            'current_iteration': self.current_iteration,
            'metric_comparisons': {
                k: v.to_dict() for k, v in self.metric_comparisons.items()
            },
            'target_metric_comparison': (
                self.target_metric_comparison.to_dict()
                if self.target_metric_comparison else None
            ),
            'overall_improved': self.overall_improved,
            'improvement_score': self.improvement_score,
            'summary': self.summary,
        }

    def get_improved_metrics(self) -> List[str]:
        """개선된 메트릭 목록 반환."""
        return [
            name for name, comp in self.metric_comparisons.items()
            if comp.improved
        ]

    def get_degraded_metrics(self) -> List[str]:
        """악화된 메트릭 목록 반환."""
        return [
            name for name, comp in self.metric_comparisons.items()
            if not comp.improved and comp.absolute_change != 0
        ]


class ResultComparator:
    """결과 비교기.

    반복 간 백테스트 결과를 비교하고 개선율을 계산합니다.

    Attributes:
        config: ICOS 설정

    Example:
        >>> comparator = ResultComparator(config)
        >>> result = comparator.compare(prev_iteration, curr_iteration)
        >>> print(f"개선 여부: {result.overall_improved}")
    """

    # 메트릭별 개선 방향 정의
    METRIC_DIRECTIONS = {
        'total_profit': ImprovementDirection.HIGHER_IS_BETTER,
        'win_rate': ImprovementDirection.HIGHER_IS_BETTER,
        'profit_factor': ImprovementDirection.HIGHER_IS_BETTER,
        'sharpe_ratio': ImprovementDirection.HIGHER_IS_BETTER,
        'trade_count': ImprovementDirection.HIGHER_IS_BETTER,  # 일반적으로 더 많은 거래가 좋음
        'avg_profit': ImprovementDirection.HIGHER_IS_BETTER,
        'max_profit': ImprovementDirection.HIGHER_IS_BETTER,
        'max_drawdown': ImprovementDirection.LOWER_IS_BETTER,  # MDD는 낮을수록 좋음
        'avg_loss': ImprovementDirection.LOWER_IS_BETTER,  # 평균 손실은 낮을수록 좋음 (절대값)
        'max_loss': ImprovementDirection.LOWER_IS_BETTER,  # 최대 손실은 낮을수록 좋음
        'total_loss': ImprovementDirection.LOWER_IS_BETTER,  # 총 손실은 낮을수록 좋음 (절대값)
        # STOM 한국어 메트릭
        '수익금': ImprovementDirection.HIGHER_IS_BETTER,
        '승률': ImprovementDirection.HIGHER_IS_BETTER,
        '손익비': ImprovementDirection.HIGHER_IS_BETTER,
        '거래횟수': ImprovementDirection.HIGHER_IS_BETTER,
        '최대낙폭': ImprovementDirection.LOWER_IS_BETTER,
    }

    # FilterMetric을 실제 메트릭 키로 매핑
    FILTER_METRIC_MAPPING = {
        FilterMetric.PROFIT: 'total_profit',
        FilterMetric.WIN_RATE: 'win_rate',
        FilterMetric.PROFIT_FACTOR: 'profit_factor',
        FilterMetric.SHARPE: 'sharpe_ratio',
        FilterMetric.MDD: 'max_drawdown',
        FilterMetric.COMBINED: 'total_profit',  # 기본값
    }

    def __init__(self, config: IterativeConfig):
        """ResultComparator 초기화.

        Args:
            config: ICOS 설정
        """
        self.config = config

    def compare(
        self,
        previous: IterationResult,
        current: IterationResult,
    ) -> ComparisonResult:
        """두 반복 결과 비교.

        Args:
            previous: 이전 반복 결과
            current: 현재 반복 결과

        Returns:
            ComparisonResult: 비교 결과
        """
        prev_metrics = previous.metrics
        curr_metrics = current.metrics

        # 각 메트릭 비교
        metric_comparisons = {}
        for metric_name in set(prev_metrics.keys()) | set(curr_metrics.keys()):
            prev_value = prev_metrics.get(metric_name, 0.0)
            curr_value = curr_metrics.get(metric_name, 0.0)

            comparison = self._compare_metric(metric_name, prev_value, curr_value)
            metric_comparisons[metric_name] = comparison

        # 타겟 메트릭 비교
        target_metric = self.config.filter_generation.target_metric
        target_key = self.FILTER_METRIC_MAPPING.get(target_metric, 'total_profit')
        target_comparison = metric_comparisons.get(target_key)

        # 종합 개선 여부 판정
        overall_improved = self._evaluate_overall_improvement(
            metric_comparisons, target_comparison
        )

        # 개선 점수 계산
        improvement_score = self._calculate_improvement_score(metric_comparisons)

        # 요약 생성
        summary = self._generate_summary(
            previous.iteration, current.iteration,
            metric_comparisons, target_comparison, overall_improved
        )

        return ComparisonResult(
            previous_iteration=previous.iteration,
            current_iteration=current.iteration,
            metric_comparisons=metric_comparisons,
            target_metric_comparison=target_comparison,
            overall_improved=overall_improved,
            improvement_score=improvement_score,
            summary=summary,
        )

    def compare_metrics(
        self,
        prev_metrics: Dict[str, float],
        curr_metrics: Dict[str, float],
    ) -> Dict[str, MetricComparison]:
        """메트릭 딕셔너리 직접 비교.

        Args:
            prev_metrics: 이전 메트릭
            curr_metrics: 현재 메트릭

        Returns:
            메트릭별 비교 결과
        """
        comparisons = {}
        for metric_name in set(prev_metrics.keys()) | set(curr_metrics.keys()):
            prev_value = prev_metrics.get(metric_name, 0.0)
            curr_value = curr_metrics.get(metric_name, 0.0)
            comparisons[metric_name] = self._compare_metric(
                metric_name, prev_value, curr_value
            )
        return comparisons

    def _compare_metric(
        self,
        metric_name: str,
        prev_value: float,
        curr_value: float,
    ) -> MetricComparison:
        """단일 메트릭 비교.

        Args:
            metric_name: 메트릭 이름
            prev_value: 이전 값
            curr_value: 현재 값

        Returns:
            MetricComparison: 비교 결과
        """
        # 개선 방향 결정 (기본값: 높을수록 좋음)
        direction = self.METRIC_DIRECTIONS.get(
            metric_name,
            ImprovementDirection.HIGHER_IS_BETTER
        )

        # 절대 변화량
        absolute_change = curr_value - prev_value

        # 퍼센트 변화율 (0 나눗셈 방지)
        if prev_value != 0:
            percent_change = (curr_value - prev_value) / abs(prev_value)
        else:
            percent_change = 0.0 if curr_value == 0 else (1.0 if curr_value > 0 else -1.0)

        # 개선 여부 판정
        if direction == ImprovementDirection.HIGHER_IS_BETTER:
            improved = curr_value > prev_value
        else:  # LOWER_IS_BETTER
            improved = curr_value < prev_value

        return MetricComparison(
            metric_name=metric_name,
            previous_value=prev_value,
            current_value=curr_value,
            absolute_change=absolute_change,
            percent_change=percent_change,
            direction=direction,
            improved=improved,
        )

    def _evaluate_overall_improvement(
        self,
        metric_comparisons: Dict[str, MetricComparison],
        target_comparison: Optional[MetricComparison],
    ) -> bool:
        """전체적인 개선 여부 판정.

        타겟 메트릭이 개선되었으면 True, 그렇지 않으면
        다른 주요 메트릭들의 개선 여부를 종합 판단합니다.

        Args:
            metric_comparisons: 메트릭별 비교 결과
            target_comparison: 타겟 메트릭 비교 결과

        Returns:
            전체 개선 여부
        """
        # 타겟 메트릭이 있으면 우선 참조
        if target_comparison:
            return target_comparison.improved

        # 타겟 메트릭이 없으면 주요 메트릭 중 과반수 개선 체크
        key_metrics = ['total_profit', 'win_rate', 'profit_factor', '수익금', '승률']
        improved_count = 0
        total_count = 0

        for metric in key_metrics:
            if metric in metric_comparisons:
                total_count += 1
                if metric_comparisons[metric].improved:
                    improved_count += 1

        return improved_count > total_count / 2 if total_count > 0 else False

    def _calculate_improvement_score(
        self,
        metric_comparisons: Dict[str, MetricComparison],
    ) -> float:
        """종합 개선 점수 계산.

        각 메트릭의 퍼센트 변화율을 가중 평균하여 점수를 계산합니다.

        Args:
            metric_comparisons: 메트릭별 비교 결과

        Returns:
            개선 점수 (-1.0 ~ 1.0, 0보다 크면 개선)
        """
        weights = {
            'total_profit': 0.4,
            '수익금': 0.4,
            'win_rate': 0.2,
            '승률': 0.2,
            'profit_factor': 0.2,
            '손익비': 0.2,
            'max_drawdown': 0.1,
            '최대낙폭': 0.1,
            'sharpe_ratio': 0.1,
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for metric_name, comparison in metric_comparisons.items():
            weight = weights.get(metric_name, 0.05)

            # 방향에 따라 점수 부호 조정
            if comparison.direction == ImprovementDirection.LOWER_IS_BETTER:
                # MDD 등은 감소가 좋으므로 부호 반전
                score = -comparison.percent_change
            else:
                score = comparison.percent_change

            # 극단적인 값 클리핑 (-1 ~ 1)
            score = max(-1.0, min(1.0, score))

            weighted_sum += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight

    def _generate_summary(
        self,
        prev_iter: int,
        curr_iter: int,
        metric_comparisons: Dict[str, MetricComparison],
        target_comparison: Optional[MetricComparison],
        overall_improved: bool,
    ) -> str:
        """비교 요약 문자열 생성.

        Args:
            prev_iter: 이전 반복 번호
            curr_iter: 현재 반복 번호
            metric_comparisons: 메트릭별 비교 결과
            target_comparison: 타겟 메트릭 비교 결과
            overall_improved: 전체 개선 여부

        Returns:
            요약 문자열
        """
        lines = [
            f"반복 {prev_iter + 1} → {curr_iter + 1} 비교:",
            f"  전체 개선: {'예' if overall_improved else '아니오'}",
        ]

        if target_comparison:
            direction_sign = "+" if target_comparison.improved else ""
            lines.append(
                f"  타겟 메트릭 ({target_comparison.metric_name}): "
                f"{target_comparison.previous_value:,.2f} → "
                f"{target_comparison.current_value:,.2f} "
                f"({direction_sign}{target_comparison.percent_change:.1%})"
            )

        # 개선/악화된 메트릭 요약
        improved = [
            name for name, comp in metric_comparisons.items()
            if comp.improved and comp.absolute_change != 0
        ]
        degraded = [
            name for name, comp in metric_comparisons.items()
            if not comp.improved and comp.absolute_change != 0
        ]

        if improved:
            lines.append(f"  개선된 메트릭: {', '.join(improved[:5])}")
        if degraded:
            lines.append(f"  악화된 메트릭: {', '.join(degraded[:5])}")

        return '\n'.join(lines)

    def get_best_iteration(
        self,
        iterations: List[IterationResult],
        metric: Optional[FilterMetric] = None,
    ) -> Tuple[int, IterationResult]:
        """최고 성과 반복 찾기.

        Args:
            iterations: 반복 결과 목록
            metric: 비교할 메트릭 (None이면 설정의 타겟 메트릭 사용)

        Returns:
            (반복 인덱스, 반복 결과)
        """
        if not iterations:
            raise ValueError("빈 반복 목록")

        target = metric or self.config.filter_generation.target_metric
        metric_key = self.FILTER_METRIC_MAPPING.get(target, 'total_profit')
        direction = self.METRIC_DIRECTIONS.get(
            metric_key,
            ImprovementDirection.HIGHER_IS_BETTER
        )

        best_idx = 0
        best_value = iterations[0].metrics.get(metric_key, 0.0)

        for i, iteration in enumerate(iterations[1:], 1):
            value = iteration.metrics.get(metric_key, 0.0)

            if direction == ImprovementDirection.HIGHER_IS_BETTER:
                if value > best_value:
                    best_idx = i
                    best_value = value
            else:
                if value < best_value:
                    best_idx = i
                    best_value = value

        return best_idx, iterations[best_idx]

    def calculate_total_improvement(
        self,
        initial: IterationResult,
        final: IterationResult,
    ) -> float:
        """초기 대비 최종 개선율 계산.

        Args:
            initial: 초기 반복 결과
            final: 최종 반복 결과

        Returns:
            개선율 (퍼센트)
        """
        target_metric = self.config.filter_generation.target_metric
        metric_key = self.FILTER_METRIC_MAPPING.get(target_metric, 'total_profit')

        initial_value = initial.metrics.get(metric_key, 0.0)
        final_value = final.metrics.get(metric_key, 0.0)

        if initial_value == 0:
            return 0.0 if final_value == 0 else (1.0 if final_value > 0 else -1.0)

        return (final_value - initial_value) / abs(initial_value)
