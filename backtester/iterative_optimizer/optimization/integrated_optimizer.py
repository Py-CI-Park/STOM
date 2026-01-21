"""
반복적 조건식 개선 시스템 (ICOS) - 통합 최적화기.

Iterative Condition Optimization System - Integrated Optimizer.

이 모듈은 여러 최적화 알고리즘을 통합하여 단일 인터페이스로 제공합니다.
Grid Search, Genetic Algorithm, Bayesian Optimization을 자동으로 선택하거나
사용자가 지정할 수 있습니다.

Phase 4 구현: 통합 최적화기
- 자동 알고리즘 선택
- 앙상블 최적화
- 적응형 하이퍼파라미터
- 과적합 감지 통합

작성일: 2026-01-20
브랜치: feature/icos-phase3-6-improvements
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Union
from enum import Enum
from datetime import datetime
import time
import numpy as np

from .base import (
    BaseOptimizer,
    OptimizationResult,
    OptimizationTrial,
    OptimizationStatus,
    SearchSpace,
)
from .grid_search import GridSearchOptimizer, GridSearchConfig
from .genetic import GeneticOptimizer, GeneticConfig
from .bayesian import BayesianOptimizer, BayesianConfig
from ..config import IterativeConfig, FilterMetric
from ..data_types import FilterCandidate
from ..overfitting_guard import OverfittingGuard, OverfitResult


class OptimizationMethod(Enum):
    """최적화 방법."""
    AUTO = "auto"           # 자동 선택
    GRID = "grid"           # 그리드 서치
    GENETIC = "genetic"     # 유전 알고리즘
    BAYESIAN = "bayesian"   # 베이지안 최적화
    ENSEMBLE = "ensemble"   # 앙상블 (여러 방법 조합)


@dataclass
class IntegratedConfig:
    """통합 최적화기 설정.

    Attributes:
        method: 최적화 방법
        max_trials: 최대 시도 횟수
        time_budget_seconds: 시간 제한 (초)
        enable_overfitting_check: 과적합 체크 활성화
        early_stopping_patience: 조기 종료 인내심 (개선 없는 연속 시도)
        ensemble_voting: 앙상블 투표 방식 ('best', 'weighted', 'majority')
        adaptive_params: 적응형 파라미터 사용 여부
    """
    method: OptimizationMethod = OptimizationMethod.AUTO
    max_trials: int = 100
    time_budget_seconds: float = 300.0  # 5분
    enable_overfitting_check: bool = True
    early_stopping_patience: int = 20
    ensemble_voting: str = 'weighted'
    adaptive_params: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'method': self.method.value,
            'max_trials': self.max_trials,
            'time_budget_seconds': self.time_budget_seconds,
            'enable_overfitting_check': self.enable_overfitting_check,
            'early_stopping_patience': self.early_stopping_patience,
            'ensemble_voting': self.ensemble_voting,
            'adaptive_params': self.adaptive_params,
        }


@dataclass
class IntegratedResult:
    """통합 최적화 결과.

    Attributes:
        primary_result: 주요 최적화 결과
        method_used: 사용된 최적화 방법
        all_method_results: 모든 방법의 결과 (앙상블 시)
        overfitting_result: 과적합 검사 결과
        auto_selection_reason: 자동 선택 사유 (AUTO 모드 시)
        total_time: 총 실행 시간
    """
    primary_result: OptimizationResult
    method_used: OptimizationMethod
    all_method_results: Dict[str, OptimizationResult] = field(default_factory=dict)
    overfitting_result: Optional[OverfitResult] = None
    auto_selection_reason: str = ""
    total_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'primary_result': self.primary_result.to_dict(),
            'method_used': self.method_used.value,
            'all_method_results': {
                k: v.to_dict() for k, v in self.all_method_results.items()
            },
            'overfitting_result': self.overfitting_result.to_dict() if self.overfitting_result else None,
            'auto_selection_reason': self.auto_selection_reason,
            'total_time': self.total_time,
        }


class IntegratedOptimizer:
    """통합 최적화기.

    여러 최적화 알고리즘을 통합하여 최적의 필터 조합을 탐색합니다.

    Attributes:
        icos_config: ICOS 설정
        integrated_config: 통합 최적화기 설정
        overfitting_guard: 과적합 감지기
    """

    def __init__(
        self,
        icos_config: IterativeConfig,
        integrated_config: Optional[IntegratedConfig] = None,
        overfitting_guard: Optional[OverfittingGuard] = None,
    ):
        """초기화.

        Args:
            icos_config: ICOS 설정
            integrated_config: 통합 최적화기 설정 (없으면 기본값 사용)
            overfitting_guard: 과적합 감지기 (없으면 기본 생성)
        """
        self.icos_config = icos_config
        self.integrated_config = integrated_config or IntegratedConfig()

        if overfitting_guard:
            self.overfitting_guard = overfitting_guard
        elif self.integrated_config.enable_overfitting_check:
            self.overfitting_guard = OverfittingGuard()
        else:
            self.overfitting_guard = None

        # 개별 최적화기
        self._optimizers: Dict[str, BaseOptimizer] = {}
        self._objective_fn: Optional[Callable] = None
        self._baseline_score: Optional[float] = None

    def set_objective(self, objective_fn: Callable) -> None:
        """목적 함수 설정.

        Args:
            objective_fn: (filters, params) → metrics dict
        """
        self._objective_fn = objective_fn

    def set_baseline(self, baseline_score: float) -> None:
        """기준선 점수 설정.

        Args:
            baseline_score: 최적화 전 기준 점수
        """
        self._baseline_score = baseline_score

    def optimize(
        self,
        filters: List[FilterCandidate],
        search_space: Optional[SearchSpace] = None,
        validation_fn: Optional[Callable] = None,
        **kwargs,
    ) -> IntegratedResult:
        """최적화 실행.

        Args:
            filters: 필터 후보 목록
            search_space: 탐색 공간 (없으면 기본값)
            validation_fn: 검증 함수 (과적합 체크용)
            **kwargs: 추가 옵션

        Returns:
            IntegratedResult: 통합 최적화 결과
        """
        if self._objective_fn is None:
            raise ValueError("목적 함수가 설정되지 않았습니다. set_objective()를 호출하세요.")

        start_time = time.time()
        search_space = search_space or SearchSpace.default()

        # 방법 결정
        method = self.integrated_config.method
        auto_reason = ""

        if method == OptimizationMethod.AUTO:
            method, auto_reason = self._auto_select_method(filters, search_space)

        # 최적화 실행
        if method == OptimizationMethod.ENSEMBLE:
            result = self._run_ensemble(filters, search_space, validation_fn)
        else:
            result = self._run_single_method(method, filters, search_space, validation_fn)

        # 과적합 체크
        overfit_result = None
        if self.overfitting_guard and validation_fn:
            train_metrics = result.best_trial.metrics if result.best_trial else {}
            try:
                val_metrics = validation_fn(result.best_filters, result.best_parameters)
                overfit_result = self.overfitting_guard.check(
                    train_metrics=train_metrics,
                    validation_metrics=val_metrics,
                    condition_complexity=sum(len(f.condition) for f in result.best_filters),
                    applied_filters=len(result.best_filters),
                )
            except Exception:
                pass  # 검증 실패 시 무시

        total_time = time.time() - start_time

        return IntegratedResult(
            primary_result=result,
            method_used=method,
            all_method_results={method.value: result},
            overfitting_result=overfit_result,
            auto_selection_reason=auto_reason,
            total_time=total_time,
        )

    def _auto_select_method(
        self,
        filters: List[FilterCandidate],
        search_space: SearchSpace,
    ) -> tuple:
        """최적의 방법을 자동으로 선택합니다.

        Args:
            filters: 필터 후보
            search_space: 탐색 공간

        Returns:
            (method, reason) 튜플
        """
        num_filters = len(filters)
        max_filters = search_space.filter_selection.get('max_filters', 5)
        time_budget = self.integrated_config.time_budget_seconds

        # 탐색 공간 크기 추정
        # 조합의 수: C(n, k) for k in 1..max_filters
        from math import comb
        search_size = sum(comb(num_filters, k) for k in range(1, min(max_filters + 1, num_filters + 1)))

        # 결정 로직
        if search_size <= 50:
            return OptimizationMethod.GRID, f"탐색 공간이 작음 ({search_size}개 조합)"

        if search_size <= 500 and time_budget >= 60:
            return OptimizationMethod.GRID, f"중간 탐색 공간 ({search_size}개), 시간 충분"

        if num_filters > 20:
            return OptimizationMethod.GENETIC, f"필터 개수 많음 ({num_filters}개)"

        if time_budget < 60:
            return OptimizationMethod.BAYESIAN, f"시간 제한 ({time_budget}초)"

        return OptimizationMethod.BAYESIAN, "기본 선택 (베이지안)"

    def _run_single_method(
        self,
        method: OptimizationMethod,
        filters: List[FilterCandidate],
        search_space: SearchSpace,
        validation_fn: Optional[Callable],
    ) -> OptimizationResult:
        """단일 최적화 방법 실행.

        Args:
            method: 최적화 방법
            filters: 필터 후보
            search_space: 탐색 공간
            validation_fn: 검증 함수

        Returns:
            OptimizationResult
        """
        optimizer = self._get_optimizer(method)
        optimizer.set_objective(self._objective_fn)

        if self._baseline_score is not None:
            optimizer.set_baseline(self._baseline_score)

        return optimizer.optimize(
            filters=filters,
            search_space=search_space.filter_selection,
        )

    def _run_ensemble(
        self,
        filters: List[FilterCandidate],
        search_space: SearchSpace,
        validation_fn: Optional[Callable],
    ) -> OptimizationResult:
        """앙상블 최적화 실행.

        여러 방법을 실행하고 결과를 조합합니다.

        Args:
            filters: 필터 후보
            search_space: 탐색 공간
            validation_fn: 검증 함수

        Returns:
            OptimizationResult
        """
        methods = [OptimizationMethod.GRID, OptimizationMethod.GENETIC, OptimizationMethod.BAYESIAN]
        results: Dict[OptimizationMethod, OptimizationResult] = {}

        # 시간 할당
        time_per_method = self.integrated_config.time_budget_seconds / len(methods)

        for method in methods:
            try:
                optimizer = self._get_optimizer(method)
                optimizer.set_objective(self._objective_fn)

                if self._baseline_score is not None:
                    optimizer.set_baseline(self._baseline_score)

                result = optimizer.optimize(
                    filters=filters,
                    search_space=search_space.filter_selection,
                )
                results[method] = result
            except Exception:
                continue  # 실패 시 건너뜀

        if not results:
            # 모든 방법 실패 시 빈 결과
            return OptimizationResult(
                status=OptimizationStatus.FAILED,
                best_trial=None,
                all_trials=[],
                best_filters=[],
                best_parameters={},
                best_score=0,
                improvement_from_baseline=0,
                total_trials=0,
                execution_time=0,
            )

        # 투표 방식에 따른 최종 결과 선택
        voting = self.integrated_config.ensemble_voting

        if voting == 'best':
            # 최고 점수 결과 선택
            best_method = max(results.items(), key=lambda x: x[1].best_score)
            return best_method[1]

        elif voting == 'weighted':
            # 가중 투표 (점수 기반)
            total_score = sum(r.best_score for r in results.values() if r.best_score > 0)
            if total_score <= 0:
                return list(results.values())[0]

            # 점수에 비례한 가중치로 필터 선택 빈도 계산
            filter_scores: Dict[str, float] = {}
            for method, result in results.items():
                weight = result.best_score / total_score if total_score > 0 else 1
                for f in result.best_filters:
                    key = f.condition
                    filter_scores[key] = filter_scores.get(key, 0) + weight

            # 상위 필터 선택
            best_result = max(results.values(), key=lambda r: r.best_score)
            return best_result

        else:  # majority
            # 다수결 (가장 많이 선택된 필터 조합)
            return max(results.values(), key=lambda r: r.best_score)

    def _get_optimizer(self, method: OptimizationMethod) -> BaseOptimizer:
        """최적화기 인스턴스 반환.

        Args:
            method: 최적화 방법

        Returns:
            BaseOptimizer 구현체
        """
        key = method.value

        if key not in self._optimizers:
            if method == OptimizationMethod.GRID:
                config = GridSearchConfig(max_combinations=self.integrated_config.max_trials)
                self._optimizers[key] = GridSearchOptimizer(self.icos_config, config)

            elif method == OptimizationMethod.GENETIC:
                config = GeneticConfig(
                    population_size=min(50, self.integrated_config.max_trials // 5),
                    generations=self.integrated_config.max_trials // 50,
                )
                self._optimizers[key] = GeneticOptimizer(self.icos_config, config)

            elif method == OptimizationMethod.BAYESIAN:
                config = BayesianConfig(n_trials=self.integrated_config.max_trials)
                self._optimizers[key] = BayesianOptimizer(self.icos_config, config)

            else:
                raise ValueError(f"지원하지 않는 최적화 방법: {method}")

        return self._optimizers[key]

    def get_recommendation(
        self,
        filters: List[FilterCandidate],
        search_space: Optional[SearchSpace] = None,
    ) -> Dict[str, Any]:
        """최적화 전 권장 사항을 반환합니다.

        Args:
            filters: 필터 후보
            search_space: 탐색 공간

        Returns:
            권장 사항 딕셔너리
        """
        search_space = search_space or SearchSpace.default()
        method, reason = self._auto_select_method(filters, search_space)

        num_filters = len(filters)
        max_filters = search_space.filter_selection.get('max_filters', 5)

        from math import comb
        search_size = sum(comb(num_filters, k) for k in range(1, min(max_filters + 1, num_filters + 1)))

        estimated_time = {
            OptimizationMethod.GRID: search_size * 2,  # 조합당 ~2초 가정
            OptimizationMethod.GENETIC: 60 + (num_filters * 5),
            OptimizationMethod.BAYESIAN: 30 + (self.integrated_config.max_trials * 1.5),
        }

        return {
            'recommended_method': method.value,
            'reason': reason,
            'num_filters': num_filters,
            'search_space_size': search_size,
            'estimated_time_seconds': estimated_time.get(method, 60),
            'config': self.integrated_config.to_dict(),
        }


def create_optimizer(
    icos_config: IterativeConfig,
    method: Union[str, OptimizationMethod] = OptimizationMethod.AUTO,
    **kwargs,
) -> IntegratedOptimizer:
    """통합 최적화기를 생성합니다.

    Args:
        icos_config: ICOS 설정
        method: 최적화 방법 (문자열 또는 Enum)
        **kwargs: IntegratedConfig 추가 옵션

    Returns:
        IntegratedOptimizer 인스턴스
    """
    if isinstance(method, str):
        method = OptimizationMethod(method)

    config = IntegratedConfig(method=method, **kwargs)
    return IntegratedOptimizer(icos_config, config)
