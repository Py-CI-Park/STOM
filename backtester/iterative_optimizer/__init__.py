"""
반복적 조건식 개선 시스템 (ICOS)

Iterative Condition Optimization System

세그먼트 필터의 예측-실제 괴리 문제를 해결하기 위해 설계된 시스템입니다.
예측 대신 실측(반복 백테스팅)을 통해 조건식을 점진적으로 개선합니다.

주요 특징:
- 예측 → 실측: 필터 효과를 예측하지 않고 실제 백테스트로 검증
- 반복적 개선: 수렴할 때까지 자동으로 반복 실행
- 기존 시스템 통합: 멀티코어 백테스팅 시스템과 호환
- 모듈화 설계: 각 컴포넌트 독립적으로 테스트 가능

사용 예시:
    >>> from backtester.iterative_optimizer import IterativeOptimizer, IterativeConfig
    >>>
    >>> config = IterativeConfig(
    ...     enabled=True,
    ...     max_iterations=5,
    ... )
    >>> optimizer = IterativeOptimizer(config)
    >>> result = optimizer.run(buystg, sellstg)
    >>>
    >>> if result.success:
    ...     print(f"최적화 완료: {result.total_improvement:.2%} 개선")
    ...     print(f"최종 조건식: {result.final_buystg[:100]}...")

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

__version__ = "0.1.0"
__author__ = "STOM Development Team"

# 설정 클래스
from .config import (
    IterativeConfig,
    ConvergenceConfig,
    FilterGenerationConfig,
    OptimizationConfig,
    ValidationConfig,
    StorageConfig,
    ConvergenceMethod,
    OptimizationMethod,
    FilterMetric,
    # 프리셋
    PRESET_CONSERVATIVE,
    PRESET_AGGRESSIVE,
    PRESET_QUICK_TEST,
)

# 데이터 클래스
from .runner import (
    FilterCandidate,
    IterationResult,
    IterativeResult,
)

# 메인 오케스트레이터
from .runner import IterativeOptimizer

# Public API
__all__ = [
    # 버전 정보
    "__version__",
    "__author__",
    # 메인 클래스
    "IterativeOptimizer",
    # 설정 클래스
    "IterativeConfig",
    "ConvergenceConfig",
    "FilterGenerationConfig",
    "OptimizationConfig",
    "ValidationConfig",
    "StorageConfig",
    # 열거형
    "ConvergenceMethod",
    "OptimizationMethod",
    "FilterMetric",
    # 데이터 클래스
    "FilterCandidate",
    "IterationResult",
    "IterativeResult",
    # 프리셋
    "PRESET_CONSERVATIVE",
    "PRESET_AGGRESSIVE",
    "PRESET_QUICK_TEST",
]
