"""
반복적 조건식 개선 시스템 (ICOS) - 베이지안 최적화.

Iterative Condition Optimization System - Bayesian Optimizer.

이 모듈은 Optuna를 활용한 베이지안 최적화를 구현합니다.
TPE (Tree-structured Parzen Estimator) 알고리즘을 사용합니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
import warnings

try:
    import optuna
    from optuna.samplers import TPESampler
    from optuna.pruners import MedianPruner
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    warnings.warn("Optuna가 설치되지 않았습니다. BayesianOptimizer를 사용하려면 optuna를 설치하세요.")

from .base import (
    BaseOptimizer,
    OptimizationResult,
    OptimizationTrial,
    OptimizationStatus,
)
from ..config import IterativeConfig
from ..data_types import FilterCandidate


@dataclass
class BayesianConfig:
    """베이지안 최적화 설정.

    Attributes:
        n_trials: 시도 횟수
        timeout: 타임아웃 (초, None이면 무제한)
        n_startup_trials: 초기 랜덤 탐색 횟수
        n_warmup_steps: 웜업 스텝 수
        multivariate: 다변량 TPE 사용 여부
        show_progress_bar: 진행 바 표시 여부
        use_pruner: 조기 중단 pruner 사용 여부
    """
    n_trials: int = 100
    timeout: Optional[float] = None
    n_startup_trials: int = 10
    n_warmup_steps: int = 5
    multivariate: bool = True
    show_progress_bar: bool = False
    use_pruner: bool = False


class BayesianOptimizer(BaseOptimizer):
    """베이지안 최적화기 (Optuna 래퍼).

    TPE (Tree-structured Parzen Estimator)를 사용한 베이지안 최적화입니다.

    장점:
    - 샘플 효율성이 높음
    - 연속/이산 파라미터 모두 지원
    - 조건부 파라미터 지원
    - 분산 최적화 지원

    단점:
    - Optuna 라이브러리 필요
    - 일부 경우 랜덤 서치보다 느릴 수 있음

    Attributes:
        config: ICOS 설정
        bayesian_config: 베이지안 최적화 설정

    Example:
        >>> optimizer = BayesianOptimizer(config)
        >>> result = optimizer.optimize(
        ...     filters=filter_candidates,
        ...     search_space={'threshold': (0.5, 2.0)},
        ... )
    """

    def __init__(
        self,
        config: IterativeConfig,
        bayesian_config: Optional[BayesianConfig] = None,
    ):
        """BayesianOptimizer 초기화.

        Args:
            config: ICOS 설정
            bayesian_config: 베이지안 최적화 설정
        """
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna가 필요합니다. pip install optuna 로 설치하세요.")

        super().__init__(config)
        self.bayesian_config = bayesian_config or BayesianConfig(
            n_trials=config.optimization.n_trials
        )
        self._study: Optional['optuna.Study'] = None
        self._all_filters: List[FilterCandidate] = []
        self._param_ranges: Dict[str, Any] = {}
        self._filter_selection_config: Dict[str, Any] = {}

    def get_name(self) -> str:
        """알고리즘 이름 반환."""
        return "Bayesian (Optuna TPE)"

    def optimize(
        self,
        filters: List[FilterCandidate],
        search_space: Dict[str, Any],
        **kwargs,
    ) -> OptimizationResult:
        """베이지안 최적화 실행.

        Args:
            filters: 필터 후보 목록
            search_space: 탐색 공간 정의
                - 'parameter_ranges': Dict[str, Tuple[min, max] or List[values]]
                - 'min_filters': 최소 필터 수
                - 'max_filters': 최대 필터 수
            **kwargs: 추가 옵션
                - 'verbose': 상세 로그 여부
                - 'study_name': Optuna 스터디 이름

        Returns:
            OptimizationResult: 최적화 결과
        """
        start_time = datetime.now()
        verbose = kwargs.get('verbose', self.config.verbose)
        study_name = kwargs.get('study_name', 'icos_optimization')

        self.reset()
        self._status = OptimizationStatus.RUNNING
        self._all_filters = filters
        self._param_ranges = search_space.get('parameter_ranges', {})
        self._filter_selection_config = {
            'min_filters': search_space.get('min_filters', 1),
            'max_filters': search_space.get('max_filters', min(len(filters), 5)),
        }

        if verbose:
            print(f"[Optuna] 시작: {len(filters)}개 필터, "
                  f"{self.bayesian_config.n_trials}회 시도")

        # Optuna 로깅 제어
        if not verbose:
            optuna.logging.set_verbosity(optuna.logging.WARNING)

        try:
            # Sampler 설정
            sampler = TPESampler(
                n_startup_trials=self.bayesian_config.n_startup_trials,
                multivariate=self.bayesian_config.multivariate,
            )

            # Pruner 설정 (선택적)
            pruner = MedianPruner(
                n_startup_trials=self.bayesian_config.n_startup_trials,
                n_warmup_steps=self.bayesian_config.n_warmup_steps,
            ) if self.bayesian_config.use_pruner else None

            # Study 생성
            self._study = optuna.create_study(
                study_name=study_name,
                direction='maximize',
                sampler=sampler,
                pruner=pruner,
            )

            # 최적화 실행
            self._study.optimize(
                self._objective,
                n_trials=self.bayesian_config.n_trials,
                timeout=self.bayesian_config.timeout,
                show_progress_bar=self.bayesian_config.show_progress_bar,
                callbacks=[self._trial_callback] if verbose else None,
            )

            self._status = OptimizationStatus.COMPLETED

        except Exception as e:
            self._status = OptimizationStatus.FAILED
            if verbose:
                print(f"[Optuna] 실패: {e}")

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        if verbose:
            print(f"[Optuna] 완료: {len(self._trials)}개 시도, "
                  f"최고 점수: {self._best_score:,.0f}, "
                  f"시간: {execution_time:.1f}초")

        return self._create_result(
            execution_time=execution_time,
            metadata={
                'algorithm': 'bayesian_optuna',
                'n_trials': self.bayesian_config.n_trials,
                'best_params': self._study.best_params if self._study else {},
            }
        )

    def _objective(self, trial: 'optuna.Trial') -> float:
        """Optuna 목적 함수.

        Args:
            trial: Optuna Trial 객체

        Returns:
            점수 (최대화)
        """
        n_filters = len(self._all_filters)
        min_f = self._filter_selection_config['min_filters']
        max_f = self._filter_selection_config['max_filters']

        # 필터 수 선택
        n_selected = trial.suggest_int('n_filters', min_f, max_f)

        # 개별 필터 선택
        selected_indices = []
        for i in range(n_selected):
            # 이미 선택된 것 제외하고 선택
            available = [j for j in range(n_filters) if j not in selected_indices]
            if not available:
                break
            idx = trial.suggest_categorical(f'filter_{i}', available)
            selected_indices.append(idx)

        selected_filters = [self._all_filters[i] for i in selected_indices]

        if not selected_filters:
            return float('-inf')

        # 파라미터 샘플링
        parameters = {}
        for param_name, param_range in self._param_ranges.items():
            if isinstance(param_range, tuple) and len(param_range) == 2:
                # 연속 파라미터
                parameters[param_name] = trial.suggest_float(
                    param_name, param_range[0], param_range[1]
                )
            elif isinstance(param_range, list):
                # 이산 파라미터
                parameters[param_name] = trial.suggest_categorical(param_name, param_range)
            else:
                # 정수 파라미터
                parameters[param_name] = trial.suggest_int(
                    param_name, int(param_range[0]), int(param_range[1])
                )

        # 평가
        try:
            metrics = self._evaluate(selected_filters, parameters)
            score = self._calculate_score(metrics)

            self._create_trial(
                trial_id=trial.number,
                filters=selected_filters,
                parameters=parameters,
                metrics=metrics,
            )

            return score

        except Exception:
            return float('-inf')

    def _trial_callback(
        self,
        study: 'optuna.Study',
        trial: 'optuna.trial.FrozenTrial',
    ) -> None:
        """시도 완료 콜백.

        Args:
            study: Optuna Study
            trial: 완료된 Trial
        """
        if trial.number % 10 == 0:
            print(f"[Optuna] Trial {trial.number}: "
                  f"score={trial.value:,.0f}, "
                  f"best={study.best_value:,.0f}")

    def get_study(self) -> Optional['optuna.Study']:
        """Optuna Study 객체 반환."""
        return self._study

    def get_importance(self) -> Dict[str, float]:
        """파라미터 중요도 반환.

        Returns:
            파라미터별 중요도 딕셔너리
        """
        if self._study is None or len(self._study.trials) < 10:
            return {}

        try:
            importance = optuna.importance.get_param_importances(self._study)
            return dict(importance)
        except Exception:
            return {}

    def get_bayesian_summary(self) -> Dict[str, Any]:
        """베이지안 최적화 요약 정보 반환."""
        summary = {
            'n_trials': self.bayesian_config.n_trials,
            'total_completed': len(self._trials),
            'best_score': self._best_score,
        }

        if self._study is not None:
            summary['best_params'] = self._study.best_params
            summary['param_importance'] = self.get_importance()

        return summary
