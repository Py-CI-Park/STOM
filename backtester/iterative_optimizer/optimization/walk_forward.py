"""
반복적 조건식 개선 시스템 (ICOS) - Walk-Forward 검증.

Iterative Condition Optimization System - Walk-Forward Validation.

이 모듈은 오버피팅 방지를 위한 Walk-Forward 검증을 구현합니다.
학습/검증 데이터를 시간순으로 분할하여 전진적으로 검증합니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Tuple
from datetime import datetime
from enum import Enum
import numpy as np
import pandas as pd

from .base import OptimizationResult, OptimizationStatus
from ..config import IterativeConfig, ValidationConfig
from ..data_types import FilterCandidate


class OverfitLevel(Enum):
    """오버피팅 수준."""
    NONE = "none"              # 0-10% 차이
    LOW = "low"                # 10-20% 차이
    MODERATE = "moderate"      # 20-30% 차이
    HIGH = "high"              # 30-50% 차이
    SEVERE = "severe"          # 50%+ 차이


@dataclass
class FoldResult:
    """단일 폴드 결과.

    Attributes:
        fold_id: 폴드 번호 (0-indexed)
        train_start: 학습 시작 시점
        train_end: 학습 종료 시점
        test_start: 테스트 시작 시점
        test_end: 테스트 종료 시점
        train_metrics: 학습 메트릭
        test_metrics: 테스트 메트릭
        train_score: 학습 점수
        test_score: 테스트 점수
        overfitting_ratio: 오버피팅 비율 ((train - test) / train)
        best_filters: 이 폴드에서 선택된 최적 필터
        best_parameters: 이 폴드에서 선택된 최적 파라미터
    """
    fold_id: int
    train_start: Any
    train_end: Any
    test_start: Any
    test_end: Any
    train_metrics: Dict[str, float]
    test_metrics: Dict[str, float]
    train_score: float
    test_score: float
    overfitting_ratio: float
    best_filters: List[FilterCandidate] = field(default_factory=list)
    best_parameters: Dict[str, Any] = field(default_factory=dict)

    @property
    def overfit_level(self) -> OverfitLevel:
        """오버피팅 수준 반환."""
        ratio = abs(self.overfitting_ratio)
        if ratio < 0.1:
            return OverfitLevel.NONE
        elif ratio < 0.2:
            return OverfitLevel.LOW
        elif ratio < 0.3:
            return OverfitLevel.MODERATE
        elif ratio < 0.5:
            return OverfitLevel.HIGH
        else:
            return OverfitLevel.SEVERE

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'fold_id': self.fold_id,
            'train_start': str(self.train_start),
            'train_end': str(self.train_end),
            'test_start': str(self.test_start),
            'test_end': str(self.test_end),
            'train_metrics': self.train_metrics,
            'test_metrics': self.test_metrics,
            'train_score': self.train_score,
            'test_score': self.test_score,
            'overfitting_ratio': self.overfitting_ratio,
            'overfit_level': self.overfit_level.value,
        }


@dataclass
class WalkForwardResult:
    """Walk-Forward 검증 결과.

    Attributes:
        status: 검증 상태
        fold_results: 각 폴드 결과
        avg_train_score: 평균 학습 점수
        avg_test_score: 평균 테스트 점수
        avg_overfitting_ratio: 평균 오버피팅 비율
        overall_overfit_level: 전체 오버피팅 수준
        is_acceptable: 오버피팅이 허용 범위 내인지
        best_consistent_filters: 폴드 간 일관된 최적 필터
        robustness_score: 견고성 점수 (0-1, 높을수록 안정)
        execution_time: 실행 시간 (초)
        metadata: 추가 메타데이터
    """
    status: OptimizationStatus
    fold_results: List[FoldResult]
    avg_train_score: float
    avg_test_score: float
    avg_overfitting_ratio: float
    overall_overfit_level: OverfitLevel
    is_acceptable: bool
    best_consistent_filters: List[FilterCandidate]
    robustness_score: float
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def n_folds(self) -> int:
        """폴드 수."""
        return len(self.fold_results)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'status': self.status.value,
            'fold_results': [f.to_dict() for f in self.fold_results],
            'avg_train_score': self.avg_train_score,
            'avg_test_score': self.avg_test_score,
            'avg_overfitting_ratio': self.avg_overfitting_ratio,
            'overall_overfit_level': self.overall_overfit_level.value,
            'is_acceptable': self.is_acceptable,
            'best_consistent_filters': [
                {'condition': f.condition, 'description': f.description}
                for f in self.best_consistent_filters
            ],
            'robustness_score': self.robustness_score,
            'n_folds': self.n_folds,
            'execution_time': self.execution_time,
            'metadata': self.metadata,
        }

    def get_summary(self) -> str:
        """요약 문자열 반환."""
        lines = [
            "=" * 50,
            "Walk-Forward 검증 결과",
            "=" * 50,
            f"폴드 수: {self.n_folds}",
            f"평균 학습 점수: {self.avg_train_score:,.0f}",
            f"평균 테스트 점수: {self.avg_test_score:,.0f}",
            f"평균 오버피팅 비율: {self.avg_overfitting_ratio:.1%}",
            f"전체 오버피팅 수준: {self.overall_overfit_level.value}",
            f"견고성 점수: {self.robustness_score:.2f}",
            f"허용 여부: {'예' if self.is_acceptable else '아니오'}",
            "=" * 50,
        ]
        return '\n'.join(lines)


class WalkForwardValidator:
    """Walk-Forward 검증기.

    시간순 데이터 분할을 통해 전진적으로 검증합니다.

    검증 방식:
    ```
    전체 데이터: [========================================]

    Fold 1: [Train  ][Test ]
    Fold 2:      [Train  ][Test ]
    Fold 3:           [Train  ][Test ]
    Fold 4:                [Train  ][Test ]
    Fold 5:                     [Train  ][Test ]
    ```

    Attributes:
        config: ICOS 설정
        validation_config: 검증 설정

    Example:
        >>> validator = WalkForwardValidator(config)
        >>> result = validator.validate(
        ...     data_dates=date_range,
        ...     optimize_fn=my_optimizer,
        ...     evaluate_fn=my_evaluator,
        ... )
    """

    def __init__(
        self,
        config: IterativeConfig,
        validation_config: Optional[ValidationConfig] = None,
    ):
        """WalkForwardValidator 초기화.

        Args:
            config: ICOS 설정
            validation_config: 검증 설정 (None이면 config에서 가져옴)
        """
        self.config = config
        self.validation_config = validation_config or config.validation

    def validate(
        self,
        data_dates: List[Any],
        optimize_fn: Callable[[List[Any], Dict], OptimizationResult],
        evaluate_fn: Callable[[List[Any], List[FilterCandidate], Dict], Dict[str, float]],
        filters: List[FilterCandidate],
        search_space: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> WalkForwardResult:
        """Walk-Forward 검증 실행.

        Args:
            data_dates: 전체 데이터 날짜 리스트 (시간순)
            optimize_fn: 최적화 함수 (train_dates, search_space) → OptimizationResult
            evaluate_fn: 평가 함수 (test_dates, filters, params) → metrics
            filters: 필터 후보
            search_space: 탐색 공간
            **kwargs: 추가 옵션
                - 'verbose': 상세 로그 여부

        Returns:
            WalkForwardResult: 검증 결과
        """
        start_time = datetime.now()
        verbose = kwargs.get('verbose', self.config.verbose)

        if verbose:
            print(f"[WF] 시작: {self.validation_config.n_folds} 폴드, "
                  f"학습 비율 {self.validation_config.train_ratio:.0%}")

        # 폴드 생성
        folds = self._create_folds(data_dates)
        fold_results: List[FoldResult] = []

        try:
            for fold_id, (train_dates, test_dates) in enumerate(folds):
                if verbose:
                    print(f"[WF] 폴드 {fold_id + 1}/{len(folds)} 처리 중...")

                # 학습 데이터로 최적화
                opt_result = optimize_fn(train_dates, search_space or {})

                if opt_result.status != OptimizationStatus.COMPLETED:
                    if verbose:
                        print(f"  최적화 실패: {opt_result.status.value}")
                    continue

                # 테스트 데이터로 평가
                test_metrics = evaluate_fn(
                    test_dates,
                    opt_result.best_filters,
                    opt_result.best_parameters,
                )

                # 학습 데이터로 재평가 (비교용)
                train_metrics = evaluate_fn(
                    train_dates,
                    opt_result.best_filters,
                    opt_result.best_parameters,
                )

                # 점수 계산
                train_score = self._calculate_score(train_metrics)
                test_score = self._calculate_score(test_metrics)

                # 오버피팅 비율 계산
                if train_score != 0:
                    overfit_ratio = (train_score - test_score) / abs(train_score)
                else:
                    overfit_ratio = 0.0

                fold_results.append(FoldResult(
                    fold_id=fold_id,
                    train_start=train_dates[0] if train_dates else None,
                    train_end=train_dates[-1] if train_dates else None,
                    test_start=test_dates[0] if test_dates else None,
                    test_end=test_dates[-1] if test_dates else None,
                    train_metrics=train_metrics,
                    test_metrics=test_metrics,
                    train_score=train_score,
                    test_score=test_score,
                    overfitting_ratio=overfit_ratio,
                    best_filters=opt_result.best_filters,
                    best_parameters=opt_result.best_parameters,
                ))

                if verbose:
                    print(f"  학습: {train_score:,.0f}, 테스트: {test_score:,.0f}, "
                          f"오버피팅: {overfit_ratio:.1%}")

        except Exception as e:
            if verbose:
                print(f"[WF] 오류: {e}")

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        # 결과 종합
        result = self._aggregate_results(fold_results, execution_time)

        if verbose:
            print(f"[WF] 완료: {result.n_folds}개 폴드, "
                  f"평균 오버피팅: {result.avg_overfitting_ratio:.1%}, "
                  f"허용: {'예' if result.is_acceptable else '아니오'}")

        return result

    def _create_folds(
        self,
        data_dates: List[Any],
    ) -> List[Tuple[List[Any], List[Any]]]:
        """데이터를 폴드로 분할.

        Args:
            data_dates: 전체 날짜 리스트

        Returns:
            (train_dates, test_dates) 튜플 리스트
        """
        n_folds = self.validation_config.n_folds
        train_ratio = self.validation_config.train_ratio
        n_total = len(data_dates)

        # 각 폴드의 크기 계산
        fold_size = n_total // (n_folds + 1)
        train_size = int(fold_size * (1 + train_ratio))
        test_size = fold_size

        folds = []
        for i in range(n_folds):
            start_idx = i * fold_size

            # 학습 데이터
            train_end_idx = min(start_idx + train_size, n_total - test_size)
            train_dates = data_dates[start_idx:train_end_idx]

            # 테스트 데이터 (학습 직후)
            test_start_idx = train_end_idx
            test_end_idx = min(test_start_idx + test_size, n_total)
            test_dates = data_dates[test_start_idx:test_end_idx]

            if train_dates and test_dates:
                folds.append((train_dates, test_dates))

        return folds

    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        """메트릭에서 점수 계산."""
        from ..config import FilterMetric

        target = self.config.filter_generation.target_metric

        metric_mapping = {
            FilterMetric.PROFIT: 'total_profit',
            FilterMetric.WIN_RATE: 'win_rate',
            FilterMetric.PROFIT_FACTOR: 'profit_factor',
            FilterMetric.SHARPE: 'sharpe_ratio',
            FilterMetric.MDD: 'max_drawdown',
            FilterMetric.COMBINED: None,
        }

        if target == FilterMetric.COMBINED:
            profit = metrics.get('total_profit', 0)
            win_rate = metrics.get('win_rate', 0)
            mdd = abs(metrics.get('max_drawdown', 0.1))
            return profit * win_rate / (1 + mdd)

        metric_key = metric_mapping.get(target, 'total_profit')
        score = metrics.get(metric_key, 0)

        if target == FilterMetric.MDD:
            score = -score

        return score

    def _aggregate_results(
        self,
        fold_results: List[FoldResult],
        execution_time: float,
    ) -> WalkForwardResult:
        """폴드 결과 종합.

        Args:
            fold_results: 폴드별 결과
            execution_time: 실행 시간

        Returns:
            WalkForwardResult: 종합 결과
        """
        if not fold_results:
            return WalkForwardResult(
                status=OptimizationStatus.FAILED,
                fold_results=[],
                avg_train_score=0,
                avg_test_score=0,
                avg_overfitting_ratio=0,
                overall_overfit_level=OverfitLevel.NONE,
                is_acceptable=False,
                best_consistent_filters=[],
                robustness_score=0,
                execution_time=execution_time,
            )

        # 평균 계산
        avg_train = np.mean([f.train_score for f in fold_results])
        avg_test = np.mean([f.test_score for f in fold_results])
        avg_overfit = np.mean([f.overfitting_ratio for f in fold_results])

        # 전체 오버피팅 수준
        if abs(avg_overfit) < 0.1:
            overall_level = OverfitLevel.NONE
        elif abs(avg_overfit) < 0.2:
            overall_level = OverfitLevel.LOW
        elif abs(avg_overfit) < 0.3:
            overall_level = OverfitLevel.MODERATE
        elif abs(avg_overfit) < 0.5:
            overall_level = OverfitLevel.HIGH
        else:
            overall_level = OverfitLevel.SEVERE

        # 허용 여부 판정
        max_gap = self.validation_config.max_train_test_gap
        is_acceptable = abs(avg_overfit) <= max_gap

        # 일관된 필터 찾기
        consistent_filters = self._find_consistent_filters(fold_results)

        # 견고성 점수 계산
        robustness = self._calculate_robustness(fold_results)

        return WalkForwardResult(
            status=OptimizationStatus.COMPLETED,
            fold_results=fold_results,
            avg_train_score=float(avg_train),
            avg_test_score=float(avg_test),
            avg_overfitting_ratio=float(avg_overfit),
            overall_overfit_level=overall_level,
            is_acceptable=is_acceptable,
            best_consistent_filters=consistent_filters,
            robustness_score=robustness,
            execution_time=execution_time,
        )

    def _find_consistent_filters(
        self,
        fold_results: List[FoldResult],
    ) -> List[FilterCandidate]:
        """폴드 간 일관된 필터 찾기.

        여러 폴드에서 공통으로 선택된 필터를 반환합니다.

        Args:
            fold_results: 폴드 결과

        Returns:
            일관된 필터 리스트
        """
        if not fold_results:
            return []

        # 각 필터의 출현 횟수 카운트
        filter_counts: Dict[str, Tuple[FilterCandidate, int]] = {}

        for fold in fold_results:
            for f in fold.best_filters:
                key = f.condition
                if key in filter_counts:
                    _, count = filter_counts[key]
                    filter_counts[key] = (f, count + 1)
                else:
                    filter_counts[key] = (f, 1)

        # 과반수 이상 폴드에서 선택된 필터
        threshold = len(fold_results) / 2
        consistent = [
            f for f, count in filter_counts.values()
            if count >= threshold
        ]

        return consistent

    def _calculate_robustness(self, fold_results: List[FoldResult]) -> float:
        """견고성 점수 계산.

        폴드 간 성능 일관성을 측정합니다.

        Args:
            fold_results: 폴드 결과

        Returns:
            견고성 점수 (0-1)
        """
        if len(fold_results) < 2:
            return 0.0

        test_scores = [f.test_score for f in fold_results]

        # 변동 계수 (CV) 기반 점수
        mean_score = np.mean(test_scores)
        std_score = np.std(test_scores)

        if mean_score == 0:
            return 0.0

        cv = std_score / abs(mean_score)

        # CV가 낮을수록 견고성 높음 (0~1로 변환)
        robustness = max(0, 1 - cv)

        return float(robustness)
