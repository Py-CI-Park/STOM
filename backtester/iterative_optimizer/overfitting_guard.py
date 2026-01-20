"""
반복적 조건식 개선 시스템 (ICOS) - 과적합 감지 및 방지 모듈.

Iterative Condition Optimization System - Overfitting Guard.

이 모듈은 ICOS 최적화 과정에서 과적합을 감지하고 방지하는 기능을 제공합니다.
훈련/검증 성능 차이, 복잡도 패널티, 안정성 분석 등을 수행합니다.

Phase 4 구현: 과적합 감지/방지
- 훈련/검증 성능 갭 분석
- 복잡도 기반 패널티 계산
- 파라미터 민감도 분석
- 조기 경보 시스템

작성일: 2026-01-20
브랜치: feature/icos-phase3-6-improvements
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
import numpy as np
import pandas as pd
import warnings


class OverfitSeverity(Enum):
    """과적합 심각도 수준."""
    NONE = "none"           # 과적합 없음
    LOW = "low"             # 경미한 과적합 징후
    MEDIUM = "medium"       # 중간 수준 과적합
    HIGH = "high"           # 심각한 과적합
    CRITICAL = "critical"   # 매우 심각한 과적합


@dataclass
class OverfitMetrics:
    """과적합 탐지 메트릭.

    Attributes:
        train_validation_gap: 훈련-검증 성능 차이 (훈련이 높으면 양수)
        complexity_score: 조건식 복잡도 점수 (0.0 ~ 1.0)
        stability_score: 성능 안정성 점수 (0.0 ~ 1.0, 높을수록 안정)
        improvement_efficiency: 개선 효율성 (복잡도 대비 개선율)
        iteration_variance: 반복간 성능 분산
        filter_correlation: 필터간 상관관계 (높으면 중복 가능성)
    """
    train_validation_gap: float = 0.0
    complexity_score: float = 0.0
    stability_score: float = 1.0
    improvement_efficiency: float = 1.0
    iteration_variance: float = 0.0
    filter_correlation: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """딕셔너리로 변환."""
        return {
            'train_validation_gap': self.train_validation_gap,
            'complexity_score': self.complexity_score,
            'stability_score': self.stability_score,
            'improvement_efficiency': self.improvement_efficiency,
            'iteration_variance': self.iteration_variance,
            'filter_correlation': self.filter_correlation,
        }


@dataclass
class OverfitResult:
    """과적합 탐지 결과.

    Attributes:
        is_overfitting: 과적합 여부
        severity: 과적합 심각도
        metrics: 상세 메트릭
        warnings: 경고 메시지 목록
        recommendations: 권장 조치 목록
        confidence: 탐지 신뢰도 (0.0 ~ 1.0)
        should_stop: 즉시 중단 권장 여부
    """
    is_overfitting: bool = False
    severity: OverfitSeverity = OverfitSeverity.NONE
    metrics: OverfitMetrics = field(default_factory=OverfitMetrics)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    should_stop: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'is_overfitting': self.is_overfitting,
            'severity': self.severity.value,
            'metrics': self.metrics.to_dict(),
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'confidence': self.confidence,
            'should_stop': self.should_stop,
            'timestamp': self.timestamp.isoformat(),
        }


class OverfittingGuard:
    """과적합 감지 및 방지 클래스.

    ICOS 최적화 과정에서 과적합을 모니터링하고 경고합니다.

    Attributes:
        gap_threshold: 훈련-검증 갭 임계값 (기본 0.15 = 15%)
        complexity_threshold: 복잡도 임계값 (기본 0.7)
        stability_threshold: 안정성 임계값 (기본 0.5)
        variance_threshold: 분산 임계값 (기본 0.3)
        history: 과적합 탐지 이력
    """

    def __init__(
        self,
        gap_threshold: float = 0.15,
        complexity_threshold: float = 0.7,
        stability_threshold: float = 0.5,
        variance_threshold: float = 0.3,
        min_iterations_for_analysis: int = 3,
    ):
        """초기화.

        Args:
            gap_threshold: 훈련-검증 갭 허용 임계값
            complexity_threshold: 복잡도 허용 임계값
            stability_threshold: 최소 안정성 임계값
            variance_threshold: 최대 분산 허용 임계값
            min_iterations_for_analysis: 분석을 위한 최소 반복 횟수
        """
        self.gap_threshold = gap_threshold
        self.complexity_threshold = complexity_threshold
        self.stability_threshold = stability_threshold
        self.variance_threshold = variance_threshold
        self.min_iterations_for_analysis = min_iterations_for_analysis

        self.history: List[OverfitResult] = []
        self._iteration_metrics: List[Dict[str, float]] = []

    def check(
        self,
        train_metrics: Dict[str, float],
        validation_metrics: Optional[Dict[str, float]] = None,
        condition_complexity: int = 0,
        applied_filters: int = 0,
        iteration_history: Optional[List[Dict[str, float]]] = None,
    ) -> OverfitResult:
        """과적합 여부를 검사합니다.

        Args:
            train_metrics: 훈련 데이터 성능 지표
            validation_metrics: 검증 데이터 성능 지표 (없으면 gap 분석 스킵)
            condition_complexity: 조건식 복잡도 (조건 개수 또는 문자열 길이)
            applied_filters: 적용된 필터 개수
            iteration_history: 이전 반복들의 메트릭 이력

        Returns:
            OverfitResult: 과적합 탐지 결과
        """
        warnings_list = []
        recommendations = []

        # 메트릭 수집
        if iteration_history:
            self._iteration_metrics = iteration_history
        if train_metrics:
            self._iteration_metrics.append(train_metrics)

        # 1. 훈련-검증 갭 분석
        gap = self._calculate_train_validation_gap(train_metrics, validation_metrics)
        if gap > self.gap_threshold:
            warnings_list.append(
                f"훈련-검증 성능 갭 {gap:.1%}이(가) 임계값 {self.gap_threshold:.1%}를 초과합니다."
            )
            recommendations.append("검증 데이터 비율을 늘리거나 필터 개수를 줄이세요.")

        # 2. 복잡도 분석
        complexity = self._calculate_complexity_score(condition_complexity, applied_filters)
        if complexity > self.complexity_threshold:
            warnings_list.append(
                f"조건식 복잡도 {complexity:.2f}이(가) 임계값 {self.complexity_threshold:.2f}를 초과합니다."
            )
            recommendations.append("더 단순한 필터 조합을 사용하세요.")

        # 3. 안정성 분석
        stability = self._calculate_stability_score()
        if stability < self.stability_threshold:
            warnings_list.append(
                f"성능 안정성 {stability:.2f}이(가) 임계값 {self.stability_threshold:.2f} 미만입니다."
            )
            recommendations.append("더 많은 훈련 데이터를 사용하거나 반복 횟수를 줄이세요.")

        # 4. 분산 분석
        variance = self._calculate_iteration_variance()
        if variance > self.variance_threshold:
            warnings_list.append(
                f"반복간 성능 분산 {variance:.3f}이(가) 임계값 {self.variance_threshold:.3f}를 초과합니다."
            )
            recommendations.append("수렴 기준을 완화하거나 학습률을 낮추세요.")

        # 5. 개선 효율성 분석
        efficiency = self._calculate_improvement_efficiency(train_metrics, complexity)

        # 6. 필터 상관관계 (간접 추정)
        filter_corr = self._estimate_filter_correlation(applied_filters)

        # 메트릭 생성
        metrics = OverfitMetrics(
            train_validation_gap=gap,
            complexity_score=complexity,
            stability_score=stability,
            improvement_efficiency=efficiency,
            iteration_variance=variance,
            filter_correlation=filter_corr,
        )

        # 과적합 여부 및 심각도 판정
        is_overfitting, severity = self._determine_overfit_severity(metrics)

        # 즉시 중단 여부
        should_stop = severity in [OverfitSeverity.HIGH, OverfitSeverity.CRITICAL]

        # 신뢰도 계산
        confidence = self._calculate_confidence(metrics)

        result = OverfitResult(
            is_overfitting=is_overfitting,
            severity=severity,
            metrics=metrics,
            warnings=warnings_list,
            recommendations=recommendations,
            confidence=confidence,
            should_stop=should_stop,
        )

        self.history.append(result)
        return result

    def _calculate_train_validation_gap(
        self,
        train_metrics: Dict[str, float],
        validation_metrics: Optional[Dict[str, float]],
    ) -> float:
        """훈련-검증 성능 갭을 계산합니다."""
        if validation_metrics is None:
            return 0.0

        # 수익금 기준 갭 계산
        train_profit = train_metrics.get('수익금', train_metrics.get('profit', 0))
        val_profit = validation_metrics.get('수익금', validation_metrics.get('profit', 0))

        if train_profit == 0:
            return 0.0

        # 훈련이 더 좋으면 양수 (과적합 징후)
        gap = (train_profit - val_profit) / abs(train_profit) if train_profit != 0 else 0
        return max(0.0, gap)  # 음수는 0으로 (검증이 더 좋은 경우)

    def _calculate_complexity_score(
        self,
        condition_complexity: int,
        applied_filters: int,
    ) -> float:
        """조건식 복잡도 점수를 계산합니다."""
        # 기본 복잡도: 조건 길이 또는 필터 개수 기반
        # 적정 필터 개수를 5개로 가정
        filter_score = min(1.0, applied_filters / 10.0)

        # 조건 복잡도 (문자열 길이 기준, 1000자를 상한으로)
        complexity_score = min(1.0, condition_complexity / 1000.0)

        # 가중 평균
        return 0.6 * filter_score + 0.4 * complexity_score

    def _calculate_stability_score(self) -> float:
        """성능 안정성 점수를 계산합니다."""
        if len(self._iteration_metrics) < self.min_iterations_for_analysis:
            return 1.0  # 데이터 부족시 안정적으로 가정

        # 최근 N개 반복의 수익금 추출
        profits = []
        for m in self._iteration_metrics[-10:]:  # 최근 10개
            profit = m.get('수익금', m.get('profit', 0))
            profits.append(profit)

        if len(profits) < 2:
            return 1.0

        profits = np.array(profits)
        mean_profit = np.mean(profits)
        std_profit = np.std(profits)

        if mean_profit == 0:
            return 0.5

        # 변동계수 (CV) 기반 안정성: CV가 낮을수록 안정
        cv = abs(std_profit / mean_profit) if mean_profit != 0 else 0
        stability = max(0.0, 1.0 - cv)

        return stability

    def _calculate_iteration_variance(self) -> float:
        """반복간 성능 분산을 계산합니다."""
        if len(self._iteration_metrics) < self.min_iterations_for_analysis:
            return 0.0

        # 연속 반복간 수익금 변화율
        changes = []
        for i in range(1, min(len(self._iteration_metrics), 10)):
            prev_profit = self._iteration_metrics[i-1].get('수익금', 0)
            curr_profit = self._iteration_metrics[i].get('수익금', 0)

            if prev_profit != 0:
                change = abs((curr_profit - prev_profit) / prev_profit)
                changes.append(change)

        if not changes:
            return 0.0

        return float(np.var(changes))

    def _calculate_improvement_efficiency(
        self,
        current_metrics: Dict[str, float],
        complexity: float,
    ) -> float:
        """개선 효율성을 계산합니다 (복잡도 대비 개선율)."""
        if len(self._iteration_metrics) < 2:
            return 1.0

        initial_profit = self._iteration_metrics[0].get('수익금', 0)
        current_profit = current_metrics.get('수익금', current_metrics.get('profit', 0))

        if initial_profit == 0:
            return 1.0

        improvement = (current_profit - initial_profit) / abs(initial_profit)

        # 복잡도가 높을수록 효율성 감소
        if complexity > 0:
            efficiency = improvement / complexity
        else:
            efficiency = improvement

        # 정규화 (0~2 범위로)
        return min(2.0, max(0.0, efficiency + 1.0))

    def _estimate_filter_correlation(self, applied_filters: int) -> float:
        """필터 상관관계를 추정합니다 (간접 추정)."""
        # 필터가 많을수록 상관관계 가능성 증가
        # 이상적: 5개 이하
        if applied_filters <= 3:
            return 0.1
        elif applied_filters <= 5:
            return 0.3
        elif applied_filters <= 8:
            return 0.5
        else:
            return min(0.9, 0.5 + (applied_filters - 8) * 0.05)

    def _determine_overfit_severity(
        self,
        metrics: OverfitMetrics,
    ) -> Tuple[bool, OverfitSeverity]:
        """과적합 여부와 심각도를 판정합니다."""
        # 점수 계산 (0~1, 높을수록 과적합 심각)
        score = 0.0

        # 갭 점수 (가장 중요)
        if metrics.train_validation_gap > 0:
            gap_score = min(1.0, metrics.train_validation_gap / 0.3)
            score += gap_score * 0.35

        # 복잡도 점수
        complexity_score = metrics.complexity_score
        score += complexity_score * 0.25

        # 불안정성 점수
        instability_score = 1.0 - metrics.stability_score
        score += instability_score * 0.20

        # 분산 점수
        variance_score = min(1.0, metrics.iteration_variance / 0.5)
        score += variance_score * 0.10

        # 비효율성 점수
        if metrics.improvement_efficiency < 1.0:
            inefficiency_score = 1.0 - metrics.improvement_efficiency
            score += inefficiency_score * 0.10

        # 심각도 결정
        if score < 0.2:
            return False, OverfitSeverity.NONE
        elif score < 0.4:
            return True, OverfitSeverity.LOW
        elif score < 0.6:
            return True, OverfitSeverity.MEDIUM
        elif score < 0.8:
            return True, OverfitSeverity.HIGH
        else:
            return True, OverfitSeverity.CRITICAL

    def _calculate_confidence(self, metrics: OverfitMetrics) -> float:
        """탐지 신뢰도를 계산합니다."""
        # 데이터가 많을수록 신뢰도 증가
        data_factor = min(1.0, len(self._iteration_metrics) / 10.0)

        # 메트릭의 일관성
        consistency = 0.5
        if len(self.history) >= 2:
            recent_severities = [h.severity for h in self.history[-3:]]
            if len(set(recent_severities)) == 1:
                consistency = 0.9  # 일관된 결과

        return data_factor * 0.6 + consistency * 0.4

    def get_summary(self) -> Dict[str, Any]:
        """과적합 감지 요약을 반환합니다."""
        if not self.history:
            return {'status': 'no_analysis', 'checks': 0}

        latest = self.history[-1]
        severities = [h.severity for h in self.history]

        return {
            'status': 'analyzed',
            'checks': len(self.history),
            'latest_severity': latest.severity.value,
            'is_overfitting': latest.is_overfitting,
            'should_stop': latest.should_stop,
            'high_severity_count': sum(1 for s in severities
                                        if s in [OverfitSeverity.HIGH, OverfitSeverity.CRITICAL]),
            'warnings': latest.warnings,
            'recommendations': latest.recommendations,
        }

    def reset(self):
        """상태를 초기화합니다."""
        self.history.clear()
        self._iteration_metrics.clear()

    def get_trend(self) -> str:
        """과적합 추세를 반환합니다."""
        if len(self.history) < 3:
            return "insufficient_data"

        # 최근 3개의 심각도 점수화
        severity_scores = {
            OverfitSeverity.NONE: 0,
            OverfitSeverity.LOW: 1,
            OverfitSeverity.MEDIUM: 2,
            OverfitSeverity.HIGH: 3,
            OverfitSeverity.CRITICAL: 4,
        }

        recent = [severity_scores[h.severity] for h in self.history[-3:]]

        # 추세 판단
        if recent[-1] > recent[0]:
            return "worsening"
        elif recent[-1] < recent[0]:
            return "improving"
        else:
            return "stable"


def create_default_guard() -> OverfittingGuard:
    """기본 설정의 과적합 감지기를 생성합니다."""
    return OverfittingGuard(
        gap_threshold=0.15,
        complexity_threshold=0.7,
        stability_threshold=0.5,
        variance_threshold=0.3,
        min_iterations_for_analysis=3,
    )


def create_strict_guard() -> OverfittingGuard:
    """엄격한 설정의 과적합 감지기를 생성합니다."""
    return OverfittingGuard(
        gap_threshold=0.10,
        complexity_threshold=0.5,
        stability_threshold=0.6,
        variance_threshold=0.2,
        min_iterations_for_analysis=2,
    )


def create_relaxed_guard() -> OverfittingGuard:
    """완화된 설정의 과적합 감지기를 생성합니다."""
    return OverfittingGuard(
        gap_threshold=0.25,
        complexity_threshold=0.85,
        stability_threshold=0.4,
        variance_threshold=0.5,
        min_iterations_for_analysis=5,
    )
