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
from .data_types import FilterCandidate, IterationResult
from .analyzer import ResultAnalyzer, AnalysisResult
from .filter_generator import FilterGenerator
from .condition_builder import ConditionBuilder, BuildResult
from .storage import IterationStorage
from .comparator import ResultComparator, ComparisonResult
from .convergence import ConvergenceChecker, ConvergenceResult, ConvergenceReason
from .backtest_sync import SyncBacktestRunner


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

        # 컴포넌트들 초기화
        self._analyzer = ResultAnalyzer(config)
        self._generator = FilterGenerator(config)
        self._builder = ConditionBuilder(config)
        self._storage = IterationStorage(config) if config.storage.save_iterations else None
        self._comparator = ResultComparator(config)
        self._convergence = ConvergenceChecker(config)

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

        # 저장소 세션 초기화
        if self._storage:
            session_id = self._storage.initialize_session()
            self._log(f"저장소 세션 초기화: {session_id}")

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

                # 반복 결과 저장
                if self._storage:
                    self._storage.save_iteration(
                        iteration=self.현재반복,
                        metrics=iteration_result.metrics,
                        buystg=iteration_result.buystg,
                        sellstg=iteration_result.sellstg,
                        applied_filters=[
                            {
                                'condition': f.condition,
                                'description': f.description,
                                'source': f.source,
                                'expected_impact': f.expected_impact,
                            }
                            for f in iteration_result.applied_filters
                        ],
                        execution_time=iteration_result.execution_time,
                    )

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

            # 최종 결과 저장
            if self._storage:
                self._storage.save_final_result(
                    final_buystg=current_buystg,
                    final_sellstg=current_sellstg,
                    total_improvement=total_improvement,
                    convergence_reason=self.수렴사유,
                    total_execution_time=total_execution_time,
                )
                self._log(f"최종 결과 저장 완료: {self._storage.get_session_path()}")

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

        SyncBacktestRunner를 사용하여 동기식 백테스트를 실행합니다.

        Args:
            buystg: 매수 조건식
            sellstg: 매도 조건식
            params: 백테스트 파라미터
                - betting: 배팅금액
                - startday: 시작일 (YYYYMMDD)
                - endday: 종료일 (YYYYMMDD)
                - starttime: 시작시간 (HHMMSS)
                - endtime: 종료시간 (HHMMSS)
                - avgtime: 평균값 계산 틱수
                - code_list: 종목코드 리스트
                - dict_cn: 종목코드-종목명 딕셔너리

        Returns:
            백테스트 결과 딕셔너리:
            - 'df_tsg': 거래 상세 DataFrame
            - 'metrics': 성과 지표 딕셔너리
            - 'execution_time': 실행 시간 (초)
        """
        # UI 구분 결정 (params에서 가져오거나 기본값 사용)
        ui_gubun = params.get('ui_gubun', 'S')
        timeframe = params.get('timeframe', 'tick')

        # SyncBacktestRunner 생성 및 실행
        runner = SyncBacktestRunner(
            ui_gubun=ui_gubun,
            timeframe=timeframe,
            dict_cn=params.get('dict_cn', {}),
            verbose=self.config.verbose,
        )

        self._log(f"    백테스트 실행 중...")

        try:
            result = runner.run(buystg, sellstg, params)

            if result['df_tsg'].empty:
                self._log("    백테스트 결과: 거래 없음")
            else:
                metrics = result['metrics']
                self._log(
                    f"    백테스트 완료: 거래 {metrics.get('trade_count', 0)}건, "
                    f"수익금 {metrics.get('total_profit', 0):,.0f}원, "
                    f"승률 {metrics.get('win_rate', 0):.1f}%, "
                    f"실행시간 {result.get('execution_time', 0):.1f}초"
                )

            return result

        except Exception as e:
            self._log(f"    백테스트 실행 오류: {str(e)}")
            return {
                'df_tsg': pd.DataFrame(),
                'df_bct': pd.DataFrame(),
                'metrics': {
                    'total_profit': 0.0,
                    'win_rate': 0.0,
                    'trade_count': 0,
                    'avg_trade_count': 0.0,
                    'profit_count': 0,
                    'loss_count': 0,
                    'profit_factor': 0.0,
                    'max_drawdown': 0.0,
                    'avg_profit_rate': 0.0,
                    'total_profit_rate': 0.0,
                    'avg_hold_time': 0.0,
                    'max_hold_count': 0,
                    'required_seed': 0.0,
                    'cagr': 0.0,
                    'tpi': 0.0,
                    'day_count': 0,
                },
                'execution_time': 0.0,
            }

    def _analyze_result(
        self,
        df_tsg: Optional[pd.DataFrame],
        metrics: Dict[str, float],
    ) -> AnalysisResult:
        """결과 분석.

        백테스트 결과를 분석하여 필터 생성에 필요한 정보를 추출합니다.
        ResultAnalyzer를 사용하여 손실 패턴과 특징 중요도를 분석합니다.

        Args:
            df_tsg: 거래 상세 DataFrame
            metrics: 성과 지표

        Returns:
            AnalysisResult: 분석 결과
        """
        if df_tsg is None or df_tsg.empty:
            self._log("    (df_tsg가 비어있음 - 분석 스킵)")
            return self._analyzer._empty_result()

        # ResultAnalyzer를 사용하여 분석 수행
        use_enhanced = self.config.filter_generation.use_segment_analysis
        analysis = self._analyzer.analyze(
            df_tsg,
            use_enhanced=use_enhanced,
            use_ml=False,  # ML은 Phase 5에서 활성화
        )

        # 분석 결과 로그
        self._log(f"    분석 완료: 손실패턴 {len(analysis.loss_patterns)}개, "
                  f"특징 {len(analysis.feature_importances)}개")

        if analysis.loss_patterns:
            top_pattern = analysis.get_top_patterns(1)[0]
            self._log(f"    상위 손실패턴: {top_pattern.description} "
                      f"(손실 {top_pattern.total_loss:,.0f}원)")

        return analysis

    def _generate_filters(
        self,
        analysis: AnalysisResult,
    ) -> List[FilterCandidate]:
        """필터 생성.

        분석 결과를 바탕으로 필터 후보를 생성합니다.
        FilterGenerator를 사용하여 우선순위가 높은 필터를 선택합니다.

        Args:
            analysis: AnalysisResult 분석 결과

        Returns:
            필터 후보 목록
        """
        # 빈 분석 결과 체크
        if not analysis.loss_patterns:
            self._log("    (손실 패턴 없음 - 필터 생성 스킵)")
            return []

        # FilterGenerator를 사용하여 필터 후보 생성
        filters = self._generator.generate(analysis)

        # 필터 유효성 검증
        valid_filters: List[FilterCandidate] = []
        for f in filters:
            is_valid, error_msg = self._generator.validate_filter(f)
            if is_valid:
                valid_filters.append(f)
            else:
                self._log(f"    필터 검증 실패: {f.description} - {error_msg}")

        # 결과 로그
        self._log(f"    필터 생성 완료: {len(valid_filters)}개")
        for i, f in enumerate(valid_filters[:3]):  # 상위 3개만 로그
            self._log(f"      [{i+1}] {f.description} (영향도 {f.expected_impact:.2f})")

        return valid_filters

    def _build_new_condition(
        self,
        buystg: str,
        filters: List[FilterCandidate],
    ) -> Tuple[str, List[FilterCandidate]]:
        """새 조건식 빌드.

        기존 조건식에 필터를 적용하여 새 조건식을 생성합니다.
        ConditionBuilder를 사용하여 필터를 조건식에 삽입합니다.

        Args:
            buystg: 기존 매수 조건식
            filters: 적용할 필터 목록

        Returns:
            (새 조건식, 실제 적용된 필터 목록)
        """
        if not filters:
            return buystg, []

        # ConditionBuilder를 사용하여 조건식 빌드
        build_result = self._builder.build(buystg, filters)

        if build_result.success:
            self._log(f"    조건식 빌드 성공: {len(build_result.applied_filters)}개 필터 적용")
            if build_result.used_variables:
                self._log(f"    사용된 변수: {', '.join(sorted(build_result.used_variables))}")
            return build_result.new_buystg, build_result.applied_filters
        else:
            self._log(f"    조건식 빌드 실패: {build_result.error_message}")
            return buystg, []

    def _check_convergence(self) -> bool:
        """수렴 판정.

        ConvergenceChecker를 사용하여 현재까지의 반복 결과를 바탕으로
        수렴 여부를 판정합니다.

        Returns:
            수렴 여부
        """
        # 최소 반복 횟수 체크
        if len(self.반복결과목록) < self.config.convergence.min_iterations:
            return False

        if len(self.반복결과목록) < 2:
            return False

        # ConvergenceChecker를 사용하여 수렴 판정
        result = self._convergence.check(self.반복결과목록)

        if result.is_converged:
            self.수렴사유 = result.reason_description
            self._log(f"    수렴 판정: {result.reason_description}")
            self._log(f"    마지막 개선율: {result.last_improvement_rate:.2%}")
            self._log(f"    총 개선율: {result.total_improvement_rate:.2%}")
            return True

        # 조기 종료 조건 확인
        if self._convergence.should_early_stop(self.반복결과목록):
            self.수렴사유 = "조기 종료: 성과 악화 감지"
            self._log(f"    조기 종료 조건 충족")
            return True

        return False

    def _calculate_total_improvement(self) -> float:
        """전체 개선율 계산.

        ResultComparator를 사용하여 초기 결과 대비 최종 결과의
        개선율을 계산합니다.

        Returns:
            개선율 (0.0 ~ ∞)
        """
        if len(self.반복결과목록) < 2:
            return 0.0

        # ResultComparator를 사용하여 총 개선율 계산
        return self._comparator.calculate_total_improvement(
            self.반복결과목록[0],
            self.반복결과목록[-1],
        )

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
