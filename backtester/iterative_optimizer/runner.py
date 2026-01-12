"""
반복적 조건식 개선 시스템 (ICOS) 메인 오케스트레이터.

Iterative Condition Optimization System Main Orchestrator.

이 모듈은 ICOS의 핵심 실행 로직을 담당합니다.
기존 백테스팅 시스템과 통합하여 반복적 조건식 개선을 수행합니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import json
import pandas as pd
import numpy as np

from .config import (
    IterativeConfig,
    ConvergenceMethod,
    FilterMetric,
    OptimizationMethod,
)


@dataclass
class FilterCandidate:
    """필터 후보.

    생성된 필터 조건의 정보를 담는 데이터 클래스입니다.

    Attributes:
        condition: 필터 조건 문자열 (Python 표현식)
        description: 필터 설명 (사람이 읽을 수 있는 형태)
        source: 필터 생성 소스 ('segment_analysis', 'loss_pattern', 등)
        expected_impact: 예상 영향도 (0.0 ~ 1.0)
        metadata: 추가 메타데이터
    """
    condition: str
    description: str
    source: str = "unknown"
    expected_impact: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IterationResult:
    """단일 반복 결과.

    하나의 반복 사이클 결과를 담는 데이터 클래스입니다.

    Attributes:
        iteration: 반복 번호 (0-indexed)
        buystg: 사용된 매수 조건식
        sellstg: 사용된 매도 조건식
        applied_filters: 적용된 필터 목록
        metrics: 백테스트 결과 지표
        df_tsg: 거래 상세 데이터프레임 (옵션)
        execution_time: 실행 시간 (초)
        timestamp: 완료 시각
    """
    iteration: int
    buystg: str
    sellstg: str
    applied_filters: List[FilterCandidate]
    metrics: Dict[str, float]
    df_tsg: Optional[pd.DataFrame] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화용)."""
        return {
            'iteration': self.iteration,
            'buystg': self.buystg[:200] + '...' if len(self.buystg) > 200 else self.buystg,
            'sellstg': self.sellstg[:200] + '...' if len(self.sellstg) > 200 else self.sellstg,
            'applied_filters': [
                {
                    'condition': f.condition,
                    'description': f.description,
                    'source': f.source,
                }
                for f in self.applied_filters
            ],
            'metrics': self.metrics,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat(),
        }


@dataclass
class IterativeResult:
    """전체 반복 최적화 결과.

    ICOS 실행의 최종 결과를 담는 데이터 클래스입니다.

    Attributes:
        success: 성공 여부
        final_buystg: 최종 최적화된 매수 조건식
        final_sellstg: 최종 매도 조건식
        iterations: 각 반복 결과 목록
        convergence_reason: 수렴/종료 사유
        total_improvement: 전체 개선율 (초기 대비)
        total_execution_time: 총 실행 시간 (초)
        config: 사용된 설정
        error_message: 에러 발생 시 메시지
    """
    success: bool
    final_buystg: str
    final_sellstg: str
    iterations: List[IterationResult]
    convergence_reason: str
    total_improvement: float
    total_execution_time: float
    config: IterativeConfig
    error_message: Optional[str] = None

    @property
    def num_iterations(self) -> int:
        """실행된 반복 횟수."""
        return len(self.iterations)

    @property
    def initial_metrics(self) -> Optional[Dict[str, float]]:
        """초기 메트릭."""
        return self.iterations[0].metrics if self.iterations else None

    @property
    def final_metrics(self) -> Optional[Dict[str, float]]:
        """최종 메트릭."""
        return self.iterations[-1].metrics if self.iterations else None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화용)."""
        return {
            'success': self.success,
            'final_buystg': self.final_buystg[:500] + '...' if len(self.final_buystg) > 500 else self.final_buystg,
            'final_sellstg': self.final_sellstg[:500] + '...' if len(self.final_sellstg) > 500 else self.final_sellstg,
            'iterations': [it.to_dict() for it in self.iterations],
            'convergence_reason': self.convergence_reason,
            'total_improvement': self.total_improvement,
            'total_execution_time': self.total_execution_time,
            'num_iterations': self.num_iterations,
            'config': self.config.to_dict(),
            'error_message': self.error_message,
        }

    def save_report(self, path: Path) -> None:
        """리포트를 JSON 파일로 저장."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)


class IterativeOptimizer:
    """반복적 조건식 개선 오케스트레이터.

    ICOS의 메인 클래스로, 반복적 백테스팅과 조건식 개선을 조율합니다.
    기존 백테스팅 시스템의 멀티코어 처리를 활용합니다.

    Attributes:
        config: ICOS 설정
        qlist: 프로세스 간 통신 큐 리스트 (옵션)
        backtest_params: 백테스트 파라미터 (옵션)

    Example:
        >>> config = IterativeConfig(enabled=True, max_iterations=5)
        >>> optimizer = IterativeOptimizer(config)
        >>> result = optimizer.run(buystg, sellstg, backtest_params)
    """

    def __init__(
        self,
        config: IterativeConfig,
        qlist: Optional[list] = None,
        backtest_params: Optional[Dict[str, Any]] = None,
    ):
        """IterativeOptimizer 초기화.

        Args:
            config: ICOS 설정
            qlist: 프로세스 간 통신 큐 리스트 (기존 시스템과 통합 시 필요)
            backtest_params: 백테스트 기본 파라미터
        """
        self.config = config
        self.qlist = qlist
        self.backtest_params = backtest_params or {}

        # 컴포넌트들 (Phase 2-4에서 구현)
        self._analyzer = None       # ResultAnalyzer
        self._generator = None      # FilterGenerator
        self._builder = None        # ConditionBuilder
        self._storage = None        # IterationStorage
        self._comparator = None     # ResultComparator
        self._convergence = None    # ConvergenceChecker

        # STOM 패턴: 한국어 상태 변수
        self.현재반복 = 0
        self.반복결과목록: List[IterationResult] = []
        self.수렴여부 = False
        self.수렴사유 = ""

        # 로깅
        self._logs: List[str] = []

    def _log(self, message: str) -> None:
        """로그 메시지 추가."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self._logs.append(log_entry)
        if self.config.verbose:
            print(log_entry)

    def run(
        self,
        buystg: str,
        sellstg: str,
        backtest_params: Optional[Dict[str, Any]] = None,
    ) -> IterativeResult:
        """반복적 조건식 개선 실행.

        메인 실행 메서드입니다. 조건식을 반복적으로 개선하여 최적화된 결과를 반환합니다.

        Args:
            buystg: 초기 매수 조건식
            sellstg: 매도 조건식
            backtest_params: 백테스트 파라미터 (None이면 초기화 시 설정 사용)

        Returns:
            IterativeResult: 최적화 결과

        Raises:
            ValueError: 설정이 비활성화된 경우
        """
        if not self.config.enabled:
            return IterativeResult(
                success=False,
                final_buystg=buystg,
                final_sellstg=sellstg,
                iterations=[],
                convergence_reason="ICOS가 비활성화됨",
                total_improvement=0.0,
                total_execution_time=0.0,
                config=self.config,
                error_message="config.enabled가 False입니다.",
            )

        params = {**self.backtest_params, **(backtest_params or {})}
        start_time = datetime.now()

        self._log(f"ICOS 시작: max_iterations={self.config.max_iterations}")
        self._log(f"초기 buystg 길이: {len(buystg)} 문자")

        # 상태 초기화
        self.현재반복 = 0
        self.반복결과목록 = []
        self.수렴여부 = False
        self.수렴사유 = ""

        current_buystg = buystg
        current_sellstg = sellstg

        try:
            # 반복 루프
            while self.현재반복 < self.config.max_iterations and not self.수렴여부:
                self._log(f"=== 반복 {self.현재반복 + 1}/{self.config.max_iterations} 시작 ===")

                # 단일 반복 실행
                iteration_result = self._run_single_iteration(
                    iteration=self.현재반복,
                    buystg=current_buystg,
                    sellstg=current_sellstg,
                    params=params,
                )
                self.반복결과목록.append(iteration_result)

                # 수렴 판정
                if self._check_convergence():
                    self.수렴여부 = True
                    self._log(f"수렴 조건 충족: {self.수렴사유}")
                    break

                # 다음 반복을 위한 조건식 업데이트
                current_buystg = iteration_result.buystg
                self.현재반복 += 1

            # 최대 반복 도달
            if not self.수렴여부:
                self.수렴사유 = f"최대 반복 횟수 도달 ({self.config.max_iterations})"

            # 전체 개선율 계산
            total_improvement = self._calculate_total_improvement()

            end_time = datetime.now()
            total_execution_time = (end_time - start_time).total_seconds()

            self._log(f"ICOS 완료: {len(self.반복결과목록)}회 반복, 총 {total_execution_time:.1f}초")
            self._log(f"전체 개선율: {total_improvement:.2%}")

            return IterativeResult(
                success=True,
                final_buystg=current_buystg,
                final_sellstg=current_sellstg,
                iterations=self.반복결과목록,
                convergence_reason=self.수렴사유,
                total_improvement=total_improvement,
                total_execution_time=total_execution_time,
                config=self.config,
            )

        except Exception as e:
            self._log(f"ICOS 오류 발생: {e}")
            end_time = datetime.now()
            return IterativeResult(
                success=False,
                final_buystg=current_buystg,
                final_sellstg=current_sellstg,
                iterations=self.반복결과목록,
                convergence_reason="오류 발생",
                total_improvement=0.0,
                total_execution_time=(end_time - start_time).total_seconds(),
                config=self.config,
                error_message=str(e),
            )

    def _run_single_iteration(
        self,
        iteration: int,
        buystg: str,
        sellstg: str,
        params: Dict[str, Any],
    ) -> IterationResult:
        """단일 반복 사이클 실행.

        1. 백테스트 실행
        2. 결과 분석
        3. 필터 생성
        4. 새 조건식 빌드

        Args:
            iteration: 반복 번호
            buystg: 현재 매수 조건식
            sellstg: 매도 조건식
            params: 백테스트 파라미터

        Returns:
            IterationResult: 반복 결과
        """
        start_time = datetime.now()
        applied_filters: List[FilterCandidate] = []

        # Step 1: 백테스트 실행
        self._log(f"  [1/4] 백테스트 실행 중...")
        backtest_result = self._execute_backtest(buystg, sellstg, params)
        metrics = backtest_result.get('metrics', {})
        df_tsg = backtest_result.get('df_tsg')

        self._log(f"  백테스트 완료: 거래 {len(df_tsg) if df_tsg is not None else 0}건")

        # Step 2: 결과 분석 (Phase 2에서 구현)
        self._log(f"  [2/4] 결과 분석 중...")
        analysis = self._analyze_result(df_tsg, metrics)

        # Step 3: 필터 생성 (Phase 2에서 구현)
        self._log(f"  [3/4] 필터 생성 중...")
        filter_candidates = self._generate_filters(analysis)

        # Step 4: 새 조건식 빌드 (Phase 3에서 구현)
        if filter_candidates and iteration < self.config.max_iterations - 1:
            self._log(f"  [4/4] 조건식 빌드 중...")
            new_buystg, applied = self._build_new_condition(buystg, filter_candidates)
            applied_filters = applied
        else:
            new_buystg = buystg

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        self._log(f"  반복 {iteration + 1} 완료: {execution_time:.1f}초, 필터 {len(applied_filters)}개 적용")

        return IterationResult(
            iteration=iteration,
            buystg=new_buystg,
            sellstg=sellstg,
            applied_filters=applied_filters,
            metrics=metrics,
            df_tsg=df_tsg if self.config.storage.save_iterations else None,
            execution_time=execution_time,
        )

    def _execute_backtest(
        self,
        buystg: str,
        sellstg: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """백테스트 실행.

        기존 백테스팅 시스템을 활용하여 백테스트를 실행합니다.
        Phase 2에서 실제 연동 구현 예정.

        Args:
            buystg: 매수 조건식
            sellstg: 매도 조건식
            params: 백테스트 파라미터

        Returns:
            백테스트 결과 딕셔너리:
            - 'df_tsg': 거래 상세 DataFrame
            - 'metrics': 성과 지표 딕셔너리
        """
        # TODO: Phase 2에서 기존 백테스팅 시스템과 연동 구현
        # 현재는 스켈레톤 - 빈 결과 반환
        self._log("    (스켈레톤: 실제 백테스트 미실행)")

        return {
            'df_tsg': pd.DataFrame(),
            'metrics': {
                'total_profit': 0.0,
                'win_rate': 0.0,
                'trade_count': 0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
            },
        }

    def _analyze_result(
        self,
        df_tsg: Optional[pd.DataFrame],
        metrics: Dict[str, float],
    ) -> Dict[str, Any]:
        """결과 분석.

        백테스트 결과를 분석하여 필터 생성에 필요한 정보를 추출합니다.
        Phase 2에서 ResultAnalyzer로 구현 예정.

        Args:
            df_tsg: 거래 상세 DataFrame
            metrics: 성과 지표

        Returns:
            분석 결과 딕셔너리
        """
        # TODO: Phase 2에서 ResultAnalyzer 구현
        self._log("    (스켈레톤: 실제 분석 미실행)")

        return {
            'loss_patterns': [],
            'segment_analysis': None,
            'feature_importance': {},
        }

    def _generate_filters(
        self,
        analysis: Dict[str, Any],
    ) -> List[FilterCandidate]:
        """필터 생성.

        분석 결과를 바탕으로 필터 후보를 생성합니다.
        Phase 2에서 FilterGenerator로 구현 예정.

        Args:
            analysis: 분석 결과

        Returns:
            필터 후보 목록
        """
        # TODO: Phase 2에서 FilterGenerator 구현
        self._log("    (스켈레톤: 실제 필터 생성 미실행)")

        return []

    def _build_new_condition(
        self,
        buystg: str,
        filters: List[FilterCandidate],
    ) -> Tuple[str, List[FilterCandidate]]:
        """새 조건식 빌드.

        기존 조건식에 필터를 적용하여 새 조건식을 생성합니다.
        Phase 3에서 ConditionBuilder로 구현 예정.

        Args:
            buystg: 기존 매수 조건식
            filters: 적용할 필터 목록

        Returns:
            (새 조건식, 실제 적용된 필터 목록)
        """
        # TODO: Phase 3에서 ConditionBuilder 구현
        self._log("    (스켈레톤: 실제 조건식 빌드 미실행)")

        return buystg, []

    def _check_convergence(self) -> bool:
        """수렴 판정.

        현재까지의 반복 결과를 바탕으로 수렴 여부를 판정합니다.
        Phase 4에서 ConvergenceChecker로 구현 예정.

        Returns:
            수렴 여부
        """
        # 최소 반복 횟수 체크
        if len(self.반복결과목록) < self.config.convergence.min_iterations:
            return False

        # TODO: Phase 4에서 ConvergenceChecker 구현
        # 현재는 간단한 로직만 구현

        if len(self.반복결과목록) < 2:
            return False

        # 이전 결과와 현재 결과 비교
        prev_metrics = self.반복결과목록[-2].metrics
        curr_metrics = self.반복결과목록[-1].metrics

        # 메인 메트릭 기준 개선율 계산
        target_metric = self.config.filter_generation.target_metric
        metric_key = self._get_metric_key(target_metric)

        prev_value = prev_metrics.get(metric_key, 0)
        curr_value = curr_metrics.get(metric_key, 0)

        if prev_value == 0:
            return False

        improvement_rate = abs(curr_value - prev_value) / abs(prev_value)

        if self.config.convergence.method == ConvergenceMethod.IMPROVEMENT_RATE:
            if improvement_rate < self.config.convergence.threshold:
                self.수렴사유 = f"개선율 {improvement_rate:.2%} < 임계값 {self.config.convergence.threshold:.2%}"
                return True

        return False

    def _calculate_total_improvement(self) -> float:
        """전체 개선율 계산.

        초기 결과 대비 최종 결과의 개선율을 계산합니다.

        Returns:
            개선율 (0.0 ~ ∞)
        """
        if len(self.반복결과목록) < 2:
            return 0.0

        initial_metrics = self.반복결과목록[0].metrics
        final_metrics = self.반복결과목록[-1].metrics

        target_metric = self.config.filter_generation.target_metric
        metric_key = self._get_metric_key(target_metric)

        initial_value = initial_metrics.get(metric_key, 0)
        final_value = final_metrics.get(metric_key, 0)

        if initial_value == 0:
            return 0.0

        return (final_value - initial_value) / abs(initial_value)

    def _get_metric_key(self, metric: FilterMetric) -> str:
        """FilterMetric을 실제 메트릭 키로 변환."""
        mapping = {
            FilterMetric.PROFIT: 'total_profit',
            FilterMetric.WIN_RATE: 'win_rate',
            FilterMetric.PROFIT_FACTOR: 'profit_factor',
            FilterMetric.SHARPE: 'sharpe_ratio',
            FilterMetric.MDD: 'max_drawdown',
            FilterMetric.COMBINED: 'total_profit',  # 기본값으로 수익 사용
        }
        return mapping.get(metric, 'total_profit')

    def get_logs(self) -> List[str]:
        """실행 로그 반환."""
        return self._logs.copy()
