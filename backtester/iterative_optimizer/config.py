"""
반복적 조건식 개선 시스템 (ICOS) 설정 모듈.

Iterative Condition Optimization System Configuration.

이 모듈은 ICOS의 모든 설정을 관리하는 dataclass들을 정의합니다.
Pythonic한 설계와 타입 힌트를 통해 가독성과 유지보수성을 확보합니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from pathlib import Path


class OptimizationMethod(Enum):
    """최적화 방법 열거형.

    - NONE: 최적화 없이 반복만 수행
    - GRID_SEARCH: 그리드 서치로 파라미터 탐색
    - GENETIC: 유전 알고리즘으로 필터 조합 진화
    - BAYESIAN: Optuna 베이지안 최적화
    """
    NONE = "none"
    GRID_SEARCH = "grid_search"
    GENETIC = "genetic"
    BAYESIAN = "bayesian"


class ConvergenceMethod(Enum):
    """수렴 판정 방법 열거형.

    - IMPROVEMENT_RATE: 개선율 기반 (개선율 < threshold 시 수렴)
    - ABSOLUTE_CHANGE: 절대 변화량 기반
    - CONSECUTIVE_NO_IMPROVE: 연속 미개선 횟수 기반
    """
    IMPROVEMENT_RATE = "improvement_rate"
    ABSOLUTE_CHANGE = "absolute_change"
    CONSECUTIVE_NO_IMPROVE = "consecutive_no_improve"


class FilterMetric(Enum):
    """필터 평가 지표 열거형.

    - PROFIT: 총 수익금
    - WIN_RATE: 승률
    - PROFIT_FACTOR: 손익비
    - SHARPE: 샤프 비율
    - MDD: 최대 낙폭 (낮을수록 좋음)
    - COMBINED: 복합 점수
    """
    PROFIT = "profit"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    SHARPE = "sharpe"
    MDD = "mdd"
    COMBINED = "combined"


@dataclass
class ConvergenceConfig:
    """수렴 판정 설정.

    Attributes:
        method: 수렴 판정 방법
        threshold: 수렴 임계값 (method에 따라 해석이 다름)
            - IMPROVEMENT_RATE: 개선율 (기본 0.05 = 5%)
            - ABSOLUTE_CHANGE: 절대 변화량 (기본 10000원)
            - CONSECUTIVE_NO_IMPROVE: 연속 미개선 횟수 (기본 3회)
        min_iterations: 최소 반복 횟수 (수렴 판정 전 최소 실행)
    """
    method: ConvergenceMethod = ConvergenceMethod.IMPROVEMENT_RATE
    threshold: float = 0.05
    min_iterations: int = 2


@dataclass
class FilterGenerationConfig:
    """필터 생성 설정.

    Attributes:
        max_filters_per_iteration: 반복당 생성할 최대 필터 수
        min_sample_size: 필터 생성에 필요한 최소 샘플 수
        target_metric: 필터 평가 기준 지표
        use_segment_analysis: 세그먼트 분석 결과를 가이드로 활용 여부
        segment_analysis_mode: 세그먼트 분석 모드 ('phase2+3' 등)
    """
    max_filters_per_iteration: int = 3
    min_sample_size: int = 30
    target_metric: FilterMetric = FilterMetric.COMBINED
    use_segment_analysis: bool = True
    segment_analysis_mode: str = "phase2+3"


@dataclass
class OptimizationConfig:
    """최적화 알고리즘 설정.

    Attributes:
        method: 최적화 방법
        n_trials: Optuna 시도 횟수 (BAYESIAN 전용)
        population_size: 유전 알고리즘 개체 수 (GENETIC 전용)
        n_generations: 유전 알고리즘 세대 수 (GENETIC 전용)
        grid_resolution: 그리드 서치 해상도 (GRID_SEARCH 전용)
    """
    method: OptimizationMethod = OptimizationMethod.NONE
    n_trials: int = 100
    population_size: int = 50
    n_generations: int = 20
    grid_resolution: int = 10


@dataclass
class ValidationConfig:
    """검증 설정 (오버피팅 방지).

    Attributes:
        enable_walk_forward: Walk-Forward 검증 활성화
        n_folds: Walk-Forward 폴드 수
        train_ratio: 학습 데이터 비율
        max_train_test_gap: 허용 가능한 학습/검증 성능 차이 비율
    """
    enable_walk_forward: bool = False
    n_folds: int = 5
    train_ratio: float = 0.7
    max_train_test_gap: float = 0.2  # 20% 이상 차이나면 오버피팅 경고


@dataclass
class StorageConfig:
    """저장 설정.

    Attributes:
        save_iterations: 각 반복 결과 저장 여부
        output_dir: 결과 저장 디렉토리 (None이면 기본값 사용)
        save_intermediate_buystg: 중간 조건식 저장 여부
        export_report: 최종 리포트 생성 여부
    """
    save_iterations: bool = True
    output_dir: Optional[Path] = None
    save_intermediate_buystg: bool = False
    export_report: bool = True


@dataclass
class IterativeConfig:
    """반복적 조건식 개선 시스템 메인 설정.

    ICOS의 모든 설정을 포함하는 최상위 설정 클래스입니다.
    기본값은 보수적으로 설정되어 있으며, 필요에 따라 조정 가능합니다.

    Attributes:
        enabled: 시스템 활성화 여부
        max_iterations: 최대 반복 횟수
        convergence: 수렴 판정 설정
        filter_generation: 필터 생성 설정
        optimization: 최적화 알고리즘 설정
        validation: 검증 설정
        storage: 저장 설정
        verbose: 상세 로그 출력 여부
        telegram_notify: 텔레그램 알림 활성화 여부

    Example:
        >>> config = IterativeConfig(
        ...     enabled=True,
        ...     max_iterations=10,
        ...     convergence=ConvergenceConfig(threshold=0.03),
        ... )
        >>> optimizer = IterativeOptimizer(config)
        >>> result = optimizer.run(buystg, sellstg)
    """
    enabled: bool = False
    max_iterations: int = 5
    convergence: ConvergenceConfig = field(default_factory=ConvergenceConfig)
    filter_generation: FilterGenerationConfig = field(default_factory=FilterGenerationConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    verbose: bool = True
    telegram_notify: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환.

        JSON 직렬화나 로깅에 유용합니다.

        Returns:
            설정 값들을 담은 딕셔너리
        """
        return {
            'enabled': self.enabled,
            'max_iterations': self.max_iterations,
            'convergence': {
                'method': self.convergence.method.value,
                'threshold': self.convergence.threshold,
                'min_iterations': self.convergence.min_iterations,
            },
            'filter_generation': {
                'max_filters_per_iteration': self.filter_generation.max_filters_per_iteration,
                'min_sample_size': self.filter_generation.min_sample_size,
                'target_metric': self.filter_generation.target_metric.value,
                'use_segment_analysis': self.filter_generation.use_segment_analysis,
            },
            'optimization': {
                'method': self.optimization.method.value,
                'n_trials': self.optimization.n_trials,
                'population_size': self.optimization.population_size,
                'n_generations': self.optimization.n_generations,
            },
            'validation': {
                'enable_walk_forward': self.validation.enable_walk_forward,
                'n_folds': self.validation.n_folds,
                'train_ratio': self.validation.train_ratio,
                'max_train_test_gap': self.validation.max_train_test_gap,
            },
            'storage': {
                'save_iterations': self.storage.save_iterations,
                'output_dir': str(self.storage.output_dir) if self.storage.output_dir else None,
                'save_intermediate_buystg': self.storage.save_intermediate_buystg,
                'export_report': self.storage.export_report,
            },
            'verbose': self.verbose,
            'telegram_notify': self.telegram_notify,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IterativeConfig':
        """딕셔너리에서 설정 생성.

        JSON 역직렬화나 설정 파일 로드에 유용합니다.

        Args:
            data: 설정 값들을 담은 딕셔너리

        Returns:
            IterativeConfig 인스턴스
        """
        convergence_data = data.get('convergence', {})
        filter_gen_data = data.get('filter_generation', {})
        opt_data = data.get('optimization', {})
        val_data = data.get('validation', {})
        storage_data = data.get('storage', {})

        return cls(
            enabled=data.get('enabled', False),
            max_iterations=data.get('max_iterations', 5),
            convergence=ConvergenceConfig(
                method=ConvergenceMethod(convergence_data.get('method', 'improvement_rate')),
                threshold=convergence_data.get('threshold', 0.05),
                min_iterations=convergence_data.get('min_iterations', 2),
            ),
            filter_generation=FilterGenerationConfig(
                max_filters_per_iteration=filter_gen_data.get('max_filters_per_iteration', 3),
                min_sample_size=filter_gen_data.get('min_sample_size', 30),
                target_metric=FilterMetric(filter_gen_data.get('target_metric', 'combined')),
                use_segment_analysis=filter_gen_data.get('use_segment_analysis', True),
            ),
            optimization=OptimizationConfig(
                method=OptimizationMethod(opt_data.get('method', 'none')),
                n_trials=opt_data.get('n_trials', 100),
                population_size=opt_data.get('population_size', 50),
                n_generations=opt_data.get('n_generations', 20),
            ),
            validation=ValidationConfig(
                enable_walk_forward=val_data.get('enable_walk_forward', False),
                n_folds=val_data.get('n_folds', 5),
                train_ratio=val_data.get('train_ratio', 0.7),
                max_train_test_gap=val_data.get('max_train_test_gap', 0.2),
            ),
            storage=StorageConfig(
                save_iterations=storage_data.get('save_iterations', True),
                output_dir=Path(storage_data['output_dir']) if storage_data.get('output_dir') else None,
                save_intermediate_buystg=storage_data.get('save_intermediate_buystg', False),
                export_report=storage_data.get('export_report', True),
            ),
            verbose=data.get('verbose', True),
            telegram_notify=data.get('telegram_notify', False),
        )


# 프리셋 설정들
PRESET_CONSERVATIVE = IterativeConfig(
    enabled=True,
    max_iterations=3,
    convergence=ConvergenceConfig(threshold=0.05, min_iterations=2),
    filter_generation=FilterGenerationConfig(max_filters_per_iteration=2),
    validation=ValidationConfig(enable_walk_forward=True),
)

PRESET_AGGRESSIVE = IterativeConfig(
    enabled=True,
    max_iterations=10,
    convergence=ConvergenceConfig(threshold=0.02, min_iterations=3),
    filter_generation=FilterGenerationConfig(max_filters_per_iteration=5),
    optimization=OptimizationConfig(method=OptimizationMethod.BAYESIAN),
    validation=ValidationConfig(enable_walk_forward=True, n_folds=7),
)

PRESET_QUICK_TEST = IterativeConfig(
    enabled=True,
    max_iterations=2,
    convergence=ConvergenceConfig(threshold=0.10, min_iterations=1),
    filter_generation=FilterGenerationConfig(max_filters_per_iteration=1),
    storage=StorageConfig(save_iterations=False, export_report=False),
    verbose=True,
)
