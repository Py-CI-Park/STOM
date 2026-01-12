"""
반복적 조건식 개선 시스템 (ICOS) - 최적화 기본 클래스.

Iterative Condition Optimization System - Optimization Base Classes.

이 모듈은 최적화 알고리즘의 추상 베이스 클래스를 정의합니다.
모든 최적화 알고리즘은 이 클래스를 상속받아 구현됩니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Tuple
from enum import Enum
import pandas as pd

from ..config import IterativeConfig, FilterMetric
from ..data_types import FilterCandidate, IterationResult


class OptimizationStatus(Enum):
    """최적화 상태."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EARLY_STOPPED = "early_stopped"


@dataclass
class OptimizationTrial:
    """단일 최적화 시도 결과.

    Attributes:
        trial_id: 시도 ID
        filters: 적용된 필터 목록
        parameters: 사용된 파라미터 (필터별 threshold 등)
        metrics: 결과 메트릭
        score: 최종 점수
        is_best: 현재까지 최고 성과 여부
    """
    trial_id: int
    filters: List[FilterCandidate]
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    score: float
    is_best: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'trial_id': self.trial_id,
            'filters': [
                {'condition': f.condition, 'description': f.description}
                for f in self.filters
            ],
            'parameters': self.parameters,
            'metrics': self.metrics,
            'score': self.score,
            'is_best': self.is_best,
        }


@dataclass
class OptimizationResult:
    """최적화 결과.

    Attributes:
        status: 최적화 상태
        best_trial: 최고 성과 시도
        all_trials: 모든 시도 목록
        best_filters: 최적 필터 조합
        best_parameters: 최적 파라미터
        best_score: 최고 점수
        improvement_from_baseline: 기준선 대비 개선율
        total_trials: 총 시도 횟수
        execution_time: 실행 시간 (초)
        convergence_history: 수렴 이력 (trial_id → score)
        metadata: 추가 메타데이터
    """
    status: OptimizationStatus
    best_trial: Optional[OptimizationTrial]
    all_trials: List[OptimizationTrial]
    best_filters: List[FilterCandidate]
    best_parameters: Dict[str, Any]
    best_score: float
    improvement_from_baseline: float
    total_trials: int
    execution_time: float
    convergence_history: List[Tuple[int, float]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'status': self.status.value,
            'best_trial': self.best_trial.to_dict() if self.best_trial else None,
            'all_trials': [t.to_dict() for t in self.all_trials],
            'best_filters': [
                {'condition': f.condition, 'description': f.description}
                for f in self.best_filters
            ],
            'best_parameters': self.best_parameters,
            'best_score': self.best_score,
            'improvement_from_baseline': self.improvement_from_baseline,
            'total_trials': self.total_trials,
            'execution_time': self.execution_time,
            'convergence_history': self.convergence_history,
            'metadata': self.metadata,
        }

    def get_top_trials(self, n: int = 10) -> List[OptimizationTrial]:
        """상위 N개 시도 반환."""
        sorted_trials = sorted(
            self.all_trials,
            key=lambda t: t.score,
            reverse=True
        )
        return sorted_trials[:n]


class BaseOptimizer(ABC):
    """최적화 알고리즘 추상 베이스 클래스.

    모든 최적화 알고리즘은 이 클래스를 상속받아 구현합니다.

    Attributes:
        config: ICOS 설정
        objective_fn: 목적 함수 (필터 → 메트릭)
        baseline_score: 기준선 점수 (최적화 전)

    Example:
        >>> class MyOptimizer(BaseOptimizer):
        ...     def optimize(self, filters, search_space):
        ...         # 구현
        ...         pass
    """

    def __init__(
        self,
        config: IterativeConfig,
        objective_fn: Optional[Callable] = None,
    ):
        """BaseOptimizer 초기화.

        Args:
            config: ICOS 설정
            objective_fn: 목적 함수 (filters, params) → metrics dict
        """
        self.config = config
        self.objective_fn = objective_fn
        self.baseline_score: Optional[float] = None

        # 내부 상태
        self._status = OptimizationStatus.NOT_STARTED
        self._trials: List[OptimizationTrial] = []
        self._best_trial: Optional[OptimizationTrial] = None
        self._best_score = float('-inf')
        self._convergence_history: List[Tuple[int, float]] = []

    @property
    def status(self) -> OptimizationStatus:
        """현재 상태 반환."""
        return self._status

    @property
    def best_score(self) -> float:
        """최고 점수 반환."""
        return self._best_score

    @abstractmethod
    def optimize(
        self,
        filters: List[FilterCandidate],
        search_space: Dict[str, Any],
        **kwargs,
    ) -> OptimizationResult:
        """최적화 실행.

        Args:
            filters: 필터 후보 목록
            search_space: 탐색 공간 정의
            **kwargs: 추가 옵션

        Returns:
            OptimizationResult: 최적화 결과
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """알고리즘 이름 반환."""
        pass

    def set_objective(self, objective_fn: Callable) -> None:
        """목적 함수 설정.

        Args:
            objective_fn: (filters, params) → metrics dict
        """
        self.objective_fn = objective_fn

    def set_baseline(self, baseline_score: float) -> None:
        """기준선 점수 설정.

        Args:
            baseline_score: 최적화 전 기준 점수
        """
        self.baseline_score = baseline_score

    def _evaluate(
        self,
        filters: List[FilterCandidate],
        parameters: Dict[str, Any],
    ) -> Dict[str, float]:
        """목적 함수 평가.

        Args:
            filters: 적용할 필터 목록
            parameters: 필터 파라미터

        Returns:
            메트릭 딕셔너리

        Raises:
            ValueError: 목적 함수가 설정되지 않은 경우
        """
        if self.objective_fn is None:
            raise ValueError("목적 함수가 설정되지 않았습니다. set_objective()를 호출하세요.")

        return self.objective_fn(filters, parameters)

    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        """메트릭에서 점수 계산.

        타겟 메트릭을 기반으로 최적화 점수를 계산합니다.

        Args:
            metrics: 메트릭 딕셔너리

        Returns:
            점수
        """
        target = self.config.filter_generation.target_metric

        # FilterMetric에 따른 메트릭 키 매핑
        metric_mapping = {
            FilterMetric.PROFIT: 'total_profit',
            FilterMetric.WIN_RATE: 'win_rate',
            FilterMetric.PROFIT_FACTOR: 'profit_factor',
            FilterMetric.SHARPE: 'sharpe_ratio',
            FilterMetric.MDD: 'max_drawdown',
            FilterMetric.COMBINED: None,  # 복합 점수
        }

        if target == FilterMetric.COMBINED:
            # 복합 점수: 수익금 * 승률 / (1 + MDD)
            profit = metrics.get('total_profit', 0)
            win_rate = metrics.get('win_rate', 0)
            mdd = abs(metrics.get('max_drawdown', 0.1))
            return profit * win_rate / (1 + mdd)

        metric_key = metric_mapping.get(target, 'total_profit')
        score = metrics.get(metric_key, 0)

        # MDD는 낮을수록 좋음
        if target == FilterMetric.MDD:
            score = -score

        return score

    def _create_trial(
        self,
        trial_id: int,
        filters: List[FilterCandidate],
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
    ) -> OptimizationTrial:
        """시도 결과 생성.

        Args:
            trial_id: 시도 ID
            filters: 적용된 필터
            parameters: 사용된 파라미터
            metrics: 결과 메트릭

        Returns:
            OptimizationTrial: 시도 결과
        """
        score = self._calculate_score(metrics)
        is_best = score > self._best_score

        if is_best:
            self._best_score = score
            self._best_trial = None  # 아래에서 설정

        trial = OptimizationTrial(
            trial_id=trial_id,
            filters=filters,
            parameters=parameters,
            metrics=metrics,
            score=score,
            is_best=is_best,
        )

        if is_best:
            self._best_trial = trial

        self._trials.append(trial)
        self._convergence_history.append((trial_id, self._best_score))

        return trial

    def _create_result(
        self,
        execution_time: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OptimizationResult:
        """최적화 결과 생성.

        Args:
            execution_time: 실행 시간
            metadata: 추가 메타데이터

        Returns:
            OptimizationResult: 최적화 결과
        """
        improvement = 0.0
        if self.baseline_score is not None and self.baseline_score != 0:
            improvement = (self._best_score - self.baseline_score) / abs(self.baseline_score)

        return OptimizationResult(
            status=self._status,
            best_trial=self._best_trial,
            all_trials=self._trials.copy(),
            best_filters=self._best_trial.filters if self._best_trial else [],
            best_parameters=self._best_trial.parameters if self._best_trial else {},
            best_score=self._best_score,
            improvement_from_baseline=improvement,
            total_trials=len(self._trials),
            execution_time=execution_time,
            convergence_history=self._convergence_history.copy(),
            metadata=metadata or {},
        )

    def reset(self) -> None:
        """내부 상태 초기화."""
        self._status = OptimizationStatus.NOT_STARTED
        self._trials = []
        self._best_trial = None
        self._best_score = float('-inf')
        self._convergence_history = []


@dataclass
class SearchSpace:
    """탐색 공간 정의.

    Attributes:
        filter_selection: 필터 선택 관련 설정
        parameter_ranges: 파라미터 범위 정의
        constraints: 제약 조건
    """
    filter_selection: Dict[str, Any] = field(default_factory=dict)
    parameter_ranges: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    constraints: List[Callable] = field(default_factory=list)

    @classmethod
    def default(cls) -> 'SearchSpace':
        """기본 탐색 공간 생성."""
        return cls(
            filter_selection={
                'min_filters': 1,
                'max_filters': 5,
                'allow_duplicates': False,
            },
            parameter_ranges={
                'threshold_multiplier': (0.5, 2.0),
                'lookback_period': (5, 50),
            },
            constraints=[],
        )
