"""
반복적 조건식 개선 시스템 (ICOS) - 유전 알고리즘 최적화.

Iterative Condition Optimization System - Genetic Algorithm Optimizer.

이 모듈은 유전 알고리즘을 통한 필터 조합 최적화를 구현합니다.
선택, 교차, 변이를 통해 최적의 필터 조합을 진화시킵니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import random
import copy
import numpy as np

from .base import (
    BaseOptimizer,
    OptimizationResult,
    OptimizationTrial,
    OptimizationStatus,
)
from ..config import IterativeConfig
from ..data_types import FilterCandidate


@dataclass
class GeneticConfig:
    """유전 알고리즘 설정.

    Attributes:
        population_size: 개체군 크기
        n_generations: 세대 수
        crossover_rate: 교차 확률
        mutation_rate: 변이 확률
        elite_ratio: 엘리트 비율 (다음 세대로 그대로 전달)
        tournament_size: 토너먼트 선택 크기
        early_stop_generations: 개선 없이 N세대 시 조기 종료
    """
    population_size: int = 50
    n_generations: int = 20
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    elite_ratio: float = 0.1
    tournament_size: int = 3
    early_stop_generations: int = 5


@dataclass
class Individual:
    """개체 (필터 조합 + 파라미터).

    Attributes:
        filter_mask: 필터 선택 마스크 (boolean 리스트)
        parameters: 파라미터 값 딕셔너리
        fitness: 적합도 점수
        metrics: 평가 메트릭
    """
    filter_mask: List[bool]
    parameters: Dict[str, float]
    fitness: float = 0.0
    metrics: Dict[str, float] = field(default_factory=dict)

    def get_selected_filters(
        self,
        all_filters: List[FilterCandidate],
    ) -> List[FilterCandidate]:
        """선택된 필터 반환."""
        return [
            f for f, selected in zip(all_filters, self.filter_mask)
            if selected
        ]

    def copy(self) -> 'Individual':
        """개체 복사."""
        return Individual(
            filter_mask=self.filter_mask.copy(),
            parameters=self.parameters.copy(),
            fitness=self.fitness,
            metrics=self.metrics.copy(),
        )


class GeneticOptimizer(BaseOptimizer):
    """유전 알고리즘 최적화기.

    선택, 교차, 변이 연산을 통해 최적의 필터 조합을 진화시킵니다.

    장점:
    - 큰 탐색 공간에서 효율적
    - 지역 최적해에 빠지지 않음
    - 병렬화 가능

    단점:
    - 하이퍼파라미터 튜닝 필요
    - 수렴 보장이 없음
    - 재현성을 위해 시드 관리 필요

    Attributes:
        config: ICOS 설정
        ga_config: 유전 알고리즘 설정

    Example:
        >>> optimizer = GeneticOptimizer(config)
        >>> result = optimizer.optimize(
        ...     filters=filter_candidates,
        ...     search_space={'threshold': (0.5, 2.0)},
        ... )
    """

    def __init__(
        self,
        config: IterativeConfig,
        ga_config: Optional[GeneticConfig] = None,
    ):
        """GeneticOptimizer 초기화.

        Args:
            config: ICOS 설정
            ga_config: 유전 알고리즘 설정
        """
        super().__init__(config)
        self.ga_config = ga_config or GeneticConfig(
            population_size=config.optimization.population_size,
            n_generations=config.optimization.n_generations,
        )
        self._all_filters: List[FilterCandidate] = []
        self._param_ranges: Dict[str, Tuple[float, float]] = {}

    def get_name(self) -> str:
        """알고리즘 이름 반환."""
        return "GeneticAlgorithm"

    def optimize(
        self,
        filters: List[FilterCandidate],
        search_space: Dict[str, Any],
        **kwargs,
    ) -> OptimizationResult:
        """유전 알고리즘 최적화 실행.

        Args:
            filters: 필터 후보 목록
            search_space: 탐색 공간 정의
                - 'parameter_ranges': Dict[str, Tuple[min, max]]
                - 'min_filters': 최소 필터 수
                - 'max_filters': 최대 필터 수
            **kwargs: 추가 옵션
                - 'verbose': 상세 로그 여부
                - 'seed': 랜덤 시드

        Returns:
            OptimizationResult: 최적화 결과
        """
        start_time = datetime.now()
        verbose = kwargs.get('verbose', self.config.verbose)
        seed = kwargs.get('seed', None)

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.reset()
        self._status = OptimizationStatus.RUNNING
        self._all_filters = filters
        self._param_ranges = search_space.get('parameter_ranges', {})

        min_filters = search_space.get('min_filters', 1)
        max_filters = search_space.get('max_filters', min(len(filters), 5))

        if verbose:
            print(f"[GA] 시작: {len(filters)}개 필터, "
                  f"{self.ga_config.n_generations}세대, "
                  f"개체수 {self.ga_config.population_size}")

        try:
            # 초기 개체군 생성
            population = self._initialize_population(
                len(filters), min_filters, max_filters
            )

            # 초기 평가
            trial_id = 0
            for ind in population:
                trial_id = self._evaluate_individual(ind, trial_id)

            # 세대별 진화
            best_fitness_history = []
            no_improve_generations = 0
            prev_best_fitness = float('-inf')

            for generation in range(self.ga_config.n_generations):
                # 선택, 교차, 변이
                new_population = self._evolve(population)

                # 새 개체 평가
                for ind in new_population:
                    if ind.fitness == 0.0:  # 미평가 개체만
                        trial_id = self._evaluate_individual(ind, trial_id)

                population = new_population
                best_fitness = max(ind.fitness for ind in population)
                best_fitness_history.append(best_fitness)

                # 조기 종료 체크
                if best_fitness > prev_best_fitness:
                    prev_best_fitness = best_fitness
                    no_improve_generations = 0
                else:
                    no_improve_generations += 1

                if no_improve_generations >= self.ga_config.early_stop_generations:
                    if verbose:
                        print(f"[GA] 조기 종료: {no_improve_generations}세대 연속 미개선")
                    self._status = OptimizationStatus.EARLY_STOPPED
                    break

                if verbose and (generation + 1) % 5 == 0:
                    avg_fitness = np.mean([ind.fitness for ind in population])
                    print(f"[GA] 세대 {generation + 1}/{self.ga_config.n_generations}: "
                          f"최고 {best_fitness:,.0f}, 평균 {avg_fitness:,.0f}")

            if self._status != OptimizationStatus.EARLY_STOPPED:
                self._status = OptimizationStatus.COMPLETED

        except Exception as e:
            self._status = OptimizationStatus.FAILED
            if verbose:
                print(f"[GA] 실패: {e}")

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        if verbose:
            print(f"[GA] 완료: {len(self._trials)}개 시도, "
                  f"최고 점수: {self._best_score:,.0f}, "
                  f"시간: {execution_time:.1f}초")

        return self._create_result(
            execution_time=execution_time,
            metadata={
                'algorithm': 'genetic',
                'population_size': self.ga_config.population_size,
                'n_generations': self.ga_config.n_generations,
                'fitness_history': best_fitness_history if 'best_fitness_history' in dir() else [],
            }
        )

    def _initialize_population(
        self,
        n_filters: int,
        min_filters: int,
        max_filters: int,
    ) -> List[Individual]:
        """초기 개체군 생성.

        Args:
            n_filters: 전체 필터 수
            min_filters: 최소 선택 필터 수
            max_filters: 최대 선택 필터 수

        Returns:
            초기 개체 리스트
        """
        population = []

        for _ in range(self.ga_config.population_size):
            # 필터 선택 수 결정
            n_selected = random.randint(min_filters, max_filters)

            # 랜덤 필터 마스크 생성
            filter_mask = [False] * n_filters
            selected_indices = random.sample(range(n_filters), n_selected)
            for idx in selected_indices:
                filter_mask[idx] = True

            # 랜덤 파라미터 생성
            parameters = {}
            for param_name, (min_val, max_val) in self._param_ranges.items():
                parameters[param_name] = random.uniform(min_val, max_val)

            population.append(Individual(
                filter_mask=filter_mask,
                parameters=parameters,
            ))

        return population

    def _evaluate_individual(
        self,
        individual: Individual,
        trial_id: int,
    ) -> int:
        """개체 평가.

        Args:
            individual: 평가할 개체
            trial_id: 시도 ID

        Returns:
            다음 시도 ID
        """
        selected_filters = individual.get_selected_filters(self._all_filters)

        if not selected_filters:
            individual.fitness = float('-inf')
            return trial_id

        try:
            metrics = self._evaluate(selected_filters, individual.parameters)
            individual.metrics = metrics
            individual.fitness = self._calculate_score(metrics)

            self._create_trial(
                trial_id=trial_id,
                filters=selected_filters,
                parameters=individual.parameters,
                metrics=metrics,
            )
            return trial_id + 1

        except Exception:
            individual.fitness = float('-inf')
            return trial_id

    def _evolve(self, population: List[Individual]) -> List[Individual]:
        """한 세대 진화.

        Args:
            population: 현재 개체군

        Returns:
            다음 세대 개체군
        """
        new_population = []

        # 정렬
        sorted_pop = sorted(population, key=lambda x: x.fitness, reverse=True)

        # 엘리트 보존
        n_elite = int(self.ga_config.population_size * self.ga_config.elite_ratio)
        for i in range(n_elite):
            new_population.append(sorted_pop[i].copy())

        # 나머지 개체 생성
        while len(new_population) < self.ga_config.population_size:
            # 부모 선택 (토너먼트)
            parent1 = self._tournament_selection(population)
            parent2 = self._tournament_selection(population)

            # 교차
            if random.random() < self.ga_config.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            # 변이
            if random.random() < self.ga_config.mutation_rate:
                self._mutate(child1)
            if random.random() < self.ga_config.mutation_rate:
                self._mutate(child2)

            # 적합도 초기화 (재평가 필요)
            child1.fitness = 0.0
            child2.fitness = 0.0

            new_population.append(child1)
            if len(new_population) < self.ga_config.population_size:
                new_population.append(child2)

        return new_population

    def _tournament_selection(self, population: List[Individual]) -> Individual:
        """토너먼트 선택.

        Args:
            population: 개체군

        Returns:
            선택된 개체
        """
        tournament = random.sample(population, min(self.ga_config.tournament_size, len(population)))
        return max(tournament, key=lambda x: x.fitness)

    def _crossover(
        self,
        parent1: Individual,
        parent2: Individual,
    ) -> Tuple[Individual, Individual]:
        """교차 연산.

        Args:
            parent1: 부모 1
            parent2: 부모 2

        Returns:
            (자녀 1, 자녀 2)
        """
        n_filters = len(parent1.filter_mask)

        # 필터 마스크 교차 (단일점)
        crossover_point = random.randint(1, n_filters - 1)

        child1_mask = parent1.filter_mask[:crossover_point] + parent2.filter_mask[crossover_point:]
        child2_mask = parent2.filter_mask[:crossover_point] + parent1.filter_mask[crossover_point:]

        # 최소 1개 필터 보장
        if not any(child1_mask):
            child1_mask[random.randint(0, n_filters - 1)] = True
        if not any(child2_mask):
            child2_mask[random.randint(0, n_filters - 1)] = True

        # 파라미터 교차 (산술 평균)
        child1_params = {}
        child2_params = {}
        alpha = random.random()

        for param_name in parent1.parameters:
            p1_val = parent1.parameters[param_name]
            p2_val = parent2.parameters[param_name]
            child1_params[param_name] = alpha * p1_val + (1 - alpha) * p2_val
            child2_params[param_name] = (1 - alpha) * p1_val + alpha * p2_val

        return (
            Individual(filter_mask=child1_mask, parameters=child1_params),
            Individual(filter_mask=child2_mask, parameters=child2_params),
        )

    def _mutate(self, individual: Individual) -> None:
        """변이 연산 (in-place).

        Args:
            individual: 변이시킬 개체
        """
        n_filters = len(individual.filter_mask)

        # 필터 마스크 변이 (랜덤 비트 플립)
        for i in range(n_filters):
            if random.random() < 0.1:  # 10% 확률로 각 비트 플립
                individual.filter_mask[i] = not individual.filter_mask[i]

        # 최소 1개 필터 보장
        if not any(individual.filter_mask):
            individual.filter_mask[random.randint(0, n_filters - 1)] = True

        # 파라미터 변이 (가우시안 노이즈)
        for param_name, (min_val, max_val) in self._param_ranges.items():
            if param_name in individual.parameters:
                noise = random.gauss(0, (max_val - min_val) * 0.1)
                new_val = individual.parameters[param_name] + noise
                individual.parameters[param_name] = max(min_val, min(max_val, new_val))

    def get_ga_summary(self) -> Dict[str, Any]:
        """유전 알고리즘 요약 정보 반환."""
        return {
            'population_size': self.ga_config.population_size,
            'n_generations': self.ga_config.n_generations,
            'crossover_rate': self.ga_config.crossover_rate,
            'mutation_rate': self.ga_config.mutation_rate,
            'total_trials': len(self._trials),
            'best_score': self._best_score,
        }
