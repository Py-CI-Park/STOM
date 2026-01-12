"""
반복적 조건식 개선 시스템 (ICOS) - 그리드 서치 최적화.

Iterative Condition Optimization System - Grid Search Optimizer.

이 모듈은 그리드 서치를 통한 필터 파라미터 최적화를 구현합니다.
모든 파라미터 조합을 체계적으로 탐색합니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple, Iterator
from datetime import datetime
import itertools
import numpy as np

from .base import (
    BaseOptimizer,
    OptimizationResult,
    OptimizationTrial,
    OptimizationStatus,
    SearchSpace,
)
from ..config import IterativeConfig
from ..data_types import FilterCandidate


@dataclass
class GridSearchConfig:
    """그리드 서치 설정.

    Attributes:
        resolution: 각 파라미터의 그리드 해상도
        max_combinations: 최대 조합 수 (None이면 무제한)
        parallel_evaluation: 병렬 평가 여부
        early_stop_no_improve: 개선 없이 연속 N번 시 조기 종료
    """
    resolution: int = 10
    max_combinations: Optional[int] = None
    parallel_evaluation: bool = False
    early_stop_no_improve: int = 100


class GridSearchOptimizer(BaseOptimizer):
    """그리드 서치 최적화기.

    모든 파라미터 조합을 체계적으로 탐색하여 최적의 필터 조합을 찾습니다.

    장점:
    - 모든 조합을 탐색하므로 전역 최적해 보장 (이산 공간에서)
    - 구현이 간단하고 이해하기 쉬움
    - 결과 재현성 보장

    단점:
    - 차원의 저주 - 파라미터가 많으면 조합 수 폭발
    - 연속 파라미터 공간에서 비효율적

    Attributes:
        config: ICOS 설정
        grid_config: 그리드 서치 설정

    Example:
        >>> optimizer = GridSearchOptimizer(config)
        >>> result = optimizer.optimize(
        ...     filters=filter_candidates,
        ...     search_space={'threshold': (0.5, 2.0)},
        ... )
    """

    def __init__(
        self,
        config: IterativeConfig,
        grid_config: Optional[GridSearchConfig] = None,
    ):
        """GridSearchOptimizer 초기화.

        Args:
            config: ICOS 설정
            grid_config: 그리드 서치 설정
        """
        super().__init__(config)
        self.grid_config = grid_config or GridSearchConfig(
            resolution=config.optimization.grid_resolution
        )

    def get_name(self) -> str:
        """알고리즘 이름 반환."""
        return "GridSearch"

    def optimize(
        self,
        filters: List[FilterCandidate],
        search_space: Dict[str, Any],
        **kwargs,
    ) -> OptimizationResult:
        """그리드 서치 최적화 실행.

        Args:
            filters: 필터 후보 목록
            search_space: 탐색 공간 정의
                - 'parameter_ranges': Dict[str, Tuple[min, max]]
                - 'filter_counts': Tuple[min, max] 적용할 필터 수 범위
            **kwargs: 추가 옵션
                - 'verbose': 상세 로그 여부

        Returns:
            OptimizationResult: 최적화 결과
        """
        start_time = datetime.now()
        verbose = kwargs.get('verbose', self.config.verbose)

        self.reset()
        self._status = OptimizationStatus.RUNNING

        if verbose:
            print(f"[GridSearch] 시작: {len(filters)}개 필터")

        try:
            # 탐색 공간 구성
            param_ranges = search_space.get('parameter_ranges', {})
            filter_counts = search_space.get('filter_counts', (1, min(len(filters), 3)))

            # 그리드 생성
            grid_points = self._generate_grid(param_ranges)
            filter_combinations = self._generate_filter_combinations(
                filters, filter_counts[0], filter_counts[1]
            )

            total_combinations = len(grid_points) * len(filter_combinations)

            if verbose:
                print(f"[GridSearch] 파라미터 조합: {len(grid_points)}개")
                print(f"[GridSearch] 필터 조합: {len(filter_combinations)}개")
                print(f"[GridSearch] 총 조합: {total_combinations}개")

            # 최대 조합 수 제한
            if self.grid_config.max_combinations:
                if total_combinations > self.grid_config.max_combinations:
                    if verbose:
                        print(f"[GridSearch] 조합 수 제한: {self.grid_config.max_combinations}개")
                    total_combinations = self.grid_config.max_combinations

            # 그리드 탐색
            trial_id = 0
            no_improve_count = 0
            prev_best = float('-inf')

            for filter_combo in filter_combinations:
                for params in grid_points:
                    if self.grid_config.max_combinations and trial_id >= self.grid_config.max_combinations:
                        break

                    # 평가
                    try:
                        metrics = self._evaluate(list(filter_combo), params)
                        trial = self._create_trial(trial_id, list(filter_combo), params, metrics)

                        # 조기 종료 체크
                        if trial.score > prev_best:
                            prev_best = trial.score
                            no_improve_count = 0
                        else:
                            no_improve_count += 1

                        if no_improve_count >= self.grid_config.early_stop_no_improve:
                            if verbose:
                                print(f"[GridSearch] 조기 종료: {no_improve_count}회 연속 미개선")
                            self._status = OptimizationStatus.EARLY_STOPPED
                            break

                    except Exception as e:
                        if verbose:
                            print(f"[GridSearch] 평가 오류 (trial {trial_id}): {e}")

                    trial_id += 1

                    # 진행 상황 출력
                    if verbose and trial_id % 50 == 0:
                        print(f"[GridSearch] 진행: {trial_id}/{total_combinations} "
                              f"(최고: {self._best_score:,.0f})")

                if self._status == OptimizationStatus.EARLY_STOPPED:
                    break

            if self._status != OptimizationStatus.EARLY_STOPPED:
                self._status = OptimizationStatus.COMPLETED

        except Exception as e:
            self._status = OptimizationStatus.FAILED
            if verbose:
                print(f"[GridSearch] 실패: {e}")

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        if verbose:
            print(f"[GridSearch] 완료: {len(self._trials)}개 시도, "
                  f"최고 점수: {self._best_score:,.0f}, "
                  f"시간: {execution_time:.1f}초")

        return self._create_result(
            execution_time=execution_time,
            metadata={
                'algorithm': 'grid_search',
                'resolution': self.grid_config.resolution,
                'total_grid_points': len(grid_points) if 'grid_points' in dir() else 0,
            }
        )

    def _generate_grid(
        self,
        param_ranges: Dict[str, Tuple[float, float]],
    ) -> List[Dict[str, float]]:
        """파라미터 그리드 생성.

        Args:
            param_ranges: 파라미터 범위 딕셔너리

        Returns:
            파라미터 조합 리스트
        """
        if not param_ranges:
            return [{}]

        # 각 파라미터에 대해 그리드 포인트 생성
        param_grids = {}
        for param_name, (min_val, max_val) in param_ranges.items():
            param_grids[param_name] = np.linspace(
                min_val, max_val, self.grid_config.resolution
            ).tolist()

        # 모든 조합 생성
        param_names = list(param_grids.keys())
        param_values = [param_grids[name] for name in param_names]

        grid_points = []
        for combo in itertools.product(*param_values):
            grid_points.append(dict(zip(param_names, combo)))

        return grid_points

    def _generate_filter_combinations(
        self,
        filters: List[FilterCandidate],
        min_count: int,
        max_count: int,
    ) -> List[Tuple[FilterCandidate, ...]]:
        """필터 조합 생성.

        Args:
            filters: 필터 목록
            min_count: 최소 필터 수
            max_count: 최대 필터 수

        Returns:
            필터 조합 리스트
        """
        combinations = []
        for count in range(min_count, max_count + 1):
            for combo in itertools.combinations(filters, count):
                combinations.append(combo)
        return combinations

    def get_grid_summary(self) -> Dict[str, Any]:
        """그리드 서치 요약 정보 반환."""
        return {
            'resolution': self.grid_config.resolution,
            'max_combinations': self.grid_config.max_combinations,
            'total_trials': len(self._trials),
            'best_score': self._best_score,
            'convergence_history': self._convergence_history,
        }
