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
import time

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

# STOM UI 색상 코드
UI_COLOR_INFO = '#45cdf7'      # 청록색 - 정보
UI_COLOR_SUCCESS = '#6eff6e'   # 녹색 - 성공
UI_COLOR_WARNING = '#f78645'   # 주황색 - 경고
UI_COLOR_ERROR = '#ff0000'     # 빨간색 - 에러
UI_COLOR_GRAY = '#cccccc'      # 회색 - 일반
UI_COLOR_YELLOW = '#ffff00'    # 노란색 - 강조
UI_COLOR_HIGHLIGHT = '#00ffff' # 시안 - 하이라이트


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

        # UI 연동 (STOM 패턴)
        self._ui_gubun = 'S'  # 기본값: 주식
        self._start_time: Optional[datetime] = None  # datetime 객체로 변경 (UI 호환성)
        self._total_steps = 0
        self._current_step = 0

    def _get_ui_num(self, key: str) -> float:
        """UI 번호 가져오기.

        Args:
            key: '백테스트' 또는 '백테바'

        Returns:
            해당 UI 번호
        """
        ui_num_map = {
            ('S', '백테스트'): 6,
            ('C', '백테스트'): 7,
            ('S', '백테바'): 8,
            ('C', '백테바'): 9,
        }
        return ui_num_map.get((self._ui_gubun, key), 6)

    def _send_ui_log(self, message: str, color: str = UI_COLOR_INFO) -> None:
        """UI 로그 전송 (windowQ 사용).

        Args:
            message: 로그 메시지
            color: HTML 색상 코드
        """
        if self.qlist and len(self.qlist) > 0:
            windowQ = self.qlist[0]
            ui_num = self._get_ui_num('백테스트')
            formatted_msg = f'<font color={color}>[ICOS] {message}</font>'
            windowQ.put((ui_num, formatted_msg))

    def _update_progress_bar(self, current: int, total: int) -> None:
        """진행률 바 업데이트.

        Args:
            current: 현재 진행 단계
            total: 전체 단계 수
        """
        if self.qlist and len(self.qlist) > 0:
            windowQ = self.qlist[0]
            ui_num = self._get_ui_num('백테바')
            windowQ.put((ui_num, current, total, self._start_time))

    def _format_metrics(self, metrics: Dict[str, float], prefix: str = '') -> str:
        """메트릭을 STOM 형식 문자열로 변환.

        STOM 형식: TC[n] ATC[n] MH[n] WR[%] MDD[%] CAGR[n] TPI[n] TG[n]

        Args:
            metrics: 메트릭 딕셔너리
            prefix: 접두어 (선택)

        Returns:
            포맷된 문자열
        """
        tc = metrics.get('trade_count', 0)
        atc = metrics.get('avg_trade_count', 0)
        mh = metrics.get('max_hold_count', 0)
        wr = metrics.get('win_rate', 0)
        mdd = metrics.get('max_drawdown', 0)
        cagr = metrics.get('cagr', 0)
        tpi = metrics.get('tpi', 0)
        tg = metrics.get('total_profit', 0)

        result = f"TC[{tc}] ATC[{atc:.1f}] MH[{mh}] WR[{wr:.1f}%] MDD[{mdd:.1f}%] TG[{tg:,.0f}]"
        if prefix:
            result = f"{prefix} {result}"
        return result

    def _format_metrics_comparison(
        self,
        prev_metrics: Dict[str, float],
        curr_metrics: Dict[str, float]
    ) -> str:
        """두 메트릭 간 비교 문자열 생성.

        Args:
            prev_metrics: 이전 메트릭
            curr_metrics: 현재 메트릭

        Returns:
            비교 문자열 (개선/악화 표시)
        """
        comparisons = []

        # 수익금 비교
        prev_profit = prev_metrics.get('total_profit', 0)
        curr_profit = curr_metrics.get('total_profit', 0)
        diff_profit = curr_profit - prev_profit
        sign = '+' if diff_profit >= 0 else ''
        comparisons.append(f"수익금:{sign}{diff_profit:,.0f}")

        # 승률 비교
        prev_wr = prev_metrics.get('win_rate', 0)
        curr_wr = curr_metrics.get('win_rate', 0)
        diff_wr = curr_wr - prev_wr
        sign = '+' if diff_wr >= 0 else ''
        comparisons.append(f"승률:{sign}{diff_wr:.1f}%p")

        # MDD 비교 (낮을수록 좋음)
        prev_mdd = prev_metrics.get('max_drawdown', 0)
        curr_mdd = curr_metrics.get('max_drawdown', 0)
        diff_mdd = curr_mdd - prev_mdd
        sign = '+' if diff_mdd >= 0 else ''  # MDD는 낮을수록 좋으므로 부호 반대로 표시
        comparisons.append(f"MDD:{sign}{diff_mdd:.1f}%p")

        return " | ".join(comparisons)

    def _calculate_eta(self, current_iteration: int, total_iterations: int) -> str:
        """예상 완료 시간(ETA) 계산.

        Args:
            current_iteration: 현재 반복 번호 (0-based)
            total_iterations: 총 반복 횟수

        Returns:
            ETA 문자열
        """
        if self._start_time is None or current_iteration == 0:
            return "계산 중..."

        # datetime 객체에서 경과 시간 계산
        elapsed = (datetime.now() - self._start_time).total_seconds()
        avg_time_per_iteration = elapsed / (current_iteration + 1)
        remaining_iterations = total_iterations - current_iteration - 1
        eta_seconds = avg_time_per_iteration * remaining_iterations

        if eta_seconds < 60:
            return f"{eta_seconds:.0f}초"
        elif eta_seconds < 3600:
            return f"{eta_seconds / 60:.1f}분"
        else:
            return f"{eta_seconds / 3600:.1f}시간"

    def _log(self, message: str, color: str = UI_COLOR_GRAY, send_to_ui: bool = True) -> None:
        """로그 메시지 추가 및 UI 전송.

        Args:
            message: 로그 메시지
            color: UI 색상 (기본: 회색)
            send_to_ui: UI로 전송 여부
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self._logs.append(log_entry)
        if self.config.verbose:
            print(log_entry)

        # UI로 로그 전송
        if send_to_ui:
            self._send_ui_log(message, color)

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

        # UI 구분 설정 (S=주식, C=코인)
        self._ui_gubun = params.get('ui_gubun', 'S')
        self._start_time = start_time  # datetime 객체 사용 (UI 진행률 바 호환)
        self._total_steps = self.config.max_iterations * 4  # 4단계/반복

        # 시작 로그 (강조)
        self._log(
            f"═══ ICOS 시작 ═══ 최대 {self.config.max_iterations}회 반복",
            UI_COLOR_HIGHLIGHT
        )
        self._log(f"초기 buystg 길이: {len(buystg)} 문자", UI_COLOR_GRAY)

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
                # ETA 계산 및 표시
                eta = self._calculate_eta(self.현재반복, self.config.max_iterations)
                self._log(
                    f"━━━ 반복 {self.현재반복 + 1}/{self.config.max_iterations} 시작 ━━━ (ETA: {eta})",
                    UI_COLOR_INFO
                )

                # 진행률 바 업데이트 (반복 시작)
                progress_base = self.현재반복 * 4
                self._update_progress_bar(progress_base, self._total_steps)

                # 단일 반복 실행
                iteration_result = self._run_single_iteration(
                    iteration=self.현재반복,
                    buystg=current_buystg,
                    sellstg=current_sellstg,
                    params=params,
                )
                self.반복결과목록.append(iteration_result)

                # 반복 결과 메트릭 로그 (성과 요약)
                metrics_str = self._format_metrics(iteration_result.metrics)
                self._log(f"  ▶ 성과: {metrics_str}", UI_COLOR_SUCCESS)

                # 이전 반복과 비교 (2번째 반복부터)
                if len(self.반복결과목록) >= 2:
                    prev_metrics = self.반복결과목록[-2].metrics
                    curr_metrics = iteration_result.metrics
                    comparison_str = self._format_metrics_comparison(prev_metrics, curr_metrics)
                    # 개선 여부에 따라 색상 결정
                    is_improved = curr_metrics.get('total_profit', 0) >= prev_metrics.get('total_profit', 0)
                    color = UI_COLOR_SUCCESS if is_improved else UI_COLOR_WARNING
                    self._log(f"  ▷ 변화: {comparison_str}", color)

                # 과적합 경고 체크 (기본 루프에도 추가)
                overfitting_warning = self._check_overfitting_warning(iteration_result)
                if overfitting_warning:
                    self._log(f"  ⚠️ {overfitting_warning}", UI_COLOR_WARNING)

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
                    self._log(f"★ 수렴 조건 충족: {self.수렴사유}", UI_COLOR_YELLOW)
                    break

                # 다음 반복을 위한 조건식 업데이트
                current_buystg = iteration_result.buystg
                self.현재반복 += 1

            # 최대 반복 도달
            if not self.수렴여부:
                self.수렴사유 = f"최대 반복 횟수 도달 ({self.config.max_iterations})"
                self._log(f"최대 반복 횟수({self.config.max_iterations})에 도달", UI_COLOR_WARNING)

            # 전체 개선율 계산
            total_improvement = self._calculate_total_improvement()

            end_time = datetime.now()
            total_execution_time = (end_time - start_time).total_seconds()

            # 완료 로그 (강조)
            self._log(
                f"═══ ICOS 완료 ═══ {len(self.반복결과목록)}회 반복, 총 {total_execution_time:.1f}초",
                UI_COLOR_HIGHLIGHT
            )

            # 전체 개선율 표시 (색상 분기)
            improvement_color = UI_COLOR_SUCCESS if total_improvement >= 0 else UI_COLOR_ERROR
            self._log(f"전체 개선율: {total_improvement:.2%}", improvement_color)

            # 초기 vs 최종 메트릭 비교
            if len(self.반복결과목록) >= 2:
                initial_metrics = self.반복결과목록[0].metrics
                final_metrics = self.반복결과목록[-1].metrics
                self._log(f"  초기: {self._format_metrics(initial_metrics)}", UI_COLOR_GRAY)
                self._log(f"  최종: {self._format_metrics(final_metrics)}", UI_COLOR_SUCCESS)
                comparison = self._format_metrics_comparison(initial_metrics, final_metrics)
                self._log(f"  총변화: {comparison}", improvement_color)

            # 진행률 바 완료
            self._update_progress_bar(self._total_steps, self._total_steps)

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
            self._log(f"✖ ICOS 오류 발생: {e}", UI_COLOR_ERROR)
            end_time = datetime.now()
            # 진행률 바 리셋
            self._update_progress_bar(0, 1)
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
        iter_start_time = datetime.now()
        applied_filters: List[FilterCandidate] = []

        # 진행률 계산 기준
        progress_base = iteration * 4

        # Step 1: 백테스트 실행
        self._log(f"  [1/4] 백테스트 실행 중...", UI_COLOR_GRAY, send_to_ui=True)
        self._update_progress_bar(progress_base + 1, self._total_steps)
        backtest_result = self._execute_backtest(buystg, sellstg, params)
        metrics = backtest_result.get('metrics', {})
        df_tsg = backtest_result.get('df_tsg')

        trade_count = len(df_tsg) if df_tsg is not None and not df_tsg.empty else 0
        exec_time = backtest_result.get('execution_time', 0)
        self._log(f"  백테스트 완료: 거래 {trade_count}건, {exec_time:.1f}초", UI_COLOR_GRAY, send_to_ui=True)

        # Step 2: 결과 분석
        self._log(f"  [2/4] 결과 분석 중...", UI_COLOR_GRAY, send_to_ui=True)
        self._update_progress_bar(progress_base + 2, self._total_steps)
        analysis = self._analyze_result(df_tsg, metrics)

        # Step 3: 필터 생성
        self._log(f"  [3/4] 필터 생성 중...", UI_COLOR_GRAY, send_to_ui=True)
        self._update_progress_bar(progress_base + 3, self._total_steps)
        filter_candidates = self._generate_filters(analysis)

        # Step 4: 새 조건식 빌드
        self._update_progress_bar(progress_base + 4, self._total_steps)
        if filter_candidates and iteration < self.config.max_iterations - 1:
            self._log(f"  [4/4] 조건식 빌드 중...", UI_COLOR_GRAY, send_to_ui=True)
            new_buystg, applied = self._build_new_condition(buystg, filter_candidates)
            applied_filters = applied
        else:
            self._log(f"  [4/4] 조건식 빌드 스킵 (최종 반복)", UI_COLOR_GRAY, send_to_ui=True)
            new_buystg = buystg

        end_time = datetime.now()
        execution_time = (end_time - iter_start_time).total_seconds()

        # 반복 완료 로그
        filter_msg = f"필터 {len(applied_filters)}개 적용" if applied_filters else "필터 없음"
        self._log(
            f"  반복 {iteration + 1} 완료: {execution_time:.1f}초, {filter_msg}",
            UI_COLOR_INFO
        )

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

        # windowQ 추출 (UI 로그 전송용)
        windowQ = self.qlist[0] if self.qlist and len(self.qlist) > 0 else None

        # SyncBacktestRunner 생성 및 실행
        runner = SyncBacktestRunner(
            ui_gubun=ui_gubun,
            timeframe=timeframe,
            dict_cn=params.get('dict_cn', {}),
            verbose=self.config.verbose,
            windowQ=windowQ,  # UI 로그 전송용
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

    def _check_overfitting_warning(self, iteration_result: IterationResult) -> Optional[str]:
        """과적합 경고 체크 (기본 루프용).

        간단한 휴리스틱 기반 과적합 경고를 생성합니다.
        Enhanced 버전의 OverfittingGuard보다 가볍지만 기본 경고 제공.

        Args:
            iteration_result: 현재 반복 결과

        Returns:
            경고 메시지 (None이면 과적합 징후 없음)
        """
        warnings: List[str] = []

        # 1. 조건식 복잡도 증가 체크
        if len(self.반복결과목록) >= 2:
            prev_result = self.반복결과목록[-2]
            curr_buystg_len = len(iteration_result.buystg)
            prev_buystg_len = len(prev_result.buystg)

            # 조건식 길이가 급격히 증가한 경우 (50% 이상)
            if prev_buystg_len > 0:
                increase_ratio = (curr_buystg_len - prev_buystg_len) / prev_buystg_len
                if increase_ratio > 0.5:
                    warnings.append(f"조건식 복잡도 급증 ({increase_ratio:.0%})")

        # 2. 거래 수 급감 체크 (초기 대비)
        if len(self.반복결과목록) >= 1:
            initial_trades = self.반복결과목록[0].metrics.get('trade_count', 0)
            current_trades = iteration_result.metrics.get('trade_count', 0)

            if initial_trades > 0:
                reduction_ratio = 1 - (current_trades / initial_trades)
                # 거래 수가 80% 이상 감소한 경우
                if reduction_ratio > 0.8:
                    warnings.append(f"거래 수 급감 ({reduction_ratio:.0%} 감소)")
                # 거래 수가 50% 이상 감소한 경우 경고
                elif reduction_ratio > 0.5:
                    warnings.append(f"거래 수 과도 감소 ({reduction_ratio:.0%})")

        # 3. 필터 수 누적 체크
        total_filters = sum(
            len(r.applied_filters) for r in self.반복결과목록
        )
        if total_filters > 10:
            warnings.append(f"필터 과다 적용 (총 {total_filters}개)")

        # 4. 수익률 vs 거래수 비대칭 체크
        if len(self.반복결과목록) >= 2:
            initial_profit = self.반복결과목록[0].metrics.get('total_profit', 0)
            current_profit = iteration_result.metrics.get('total_profit', 0)
            initial_trades = self.반복결과목록[0].metrics.get('trade_count', 1)
            current_trades = iteration_result.metrics.get('trade_count', 1)

            # 수익 증가 but 거래당 수익 감소
            if current_profit > initial_profit and current_trades > 0 and initial_trades > 0:
                initial_per_trade = initial_profit / initial_trades
                current_per_trade = current_profit / current_trades

                if current_per_trade < initial_per_trade * 0.7:
                    warnings.append("거래당 수익 감소 (효율성 저하)")

        # 5. 연속 악화 체크
        if len(self.반복결과목록) >= 3:
            recent_profits = [
                r.metrics.get('total_profit', 0)
                for r in self.반복결과목록[-3:]
            ]
            # 연속 2회 악화
            if recent_profits[2] < recent_profits[1] < recent_profits[0]:
                warnings.append("연속 2회 성과 악화")

        if warnings:
            return "과적합 가능성: " + ", ".join(warnings)

        return None


# ============================================================================
# Phase 4-5: Walk-Forward 검증, 일시정지/재개, 과적합 감지 통합
# ============================================================================


@dataclass
class CheckpointData:
    """체크포인트 데이터.

    일시정지 시 저장되는 상태 데이터입니다.

    Attributes:
        iteration: 현재 반복 번호
        buystg: 현재 매수 조건식
        sellstg: 매도 조건식
        iteration_results: 이전 반복 결과들
        start_time: 시작 시간
        config: 설정
        params: 백테스트 파라미터
        timestamp: 체크포인트 생성 시각
    """
    iteration: int
    buystg: str
    sellstg: str
    iteration_results: List[IterationResult]
    start_time: datetime
    config: IterativeConfig
    params: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'iteration': self.iteration,
            'buystg': self.buystg[:500] + '...' if len(self.buystg) > 500 else self.buystg,
            'sellstg': self.sellstg[:500] + '...' if len(self.sellstg) > 500 else self.sellstg,
            'iteration_count': len(self.iteration_results),
            'start_time': self.start_time.isoformat(),
            'timestamp': self.timestamp.isoformat(),
        }

    def save(self, path: Path) -> None:
        """체크포인트 저장."""
        data = {
            'iteration': self.iteration,
            'buystg': self.buystg,
            'sellstg': self.sellstg,
            'iteration_results': [r.to_dict() for r in self.iteration_results],
            'start_time': self.start_time.isoformat(),
            'config': self.config.to_dict(),
            'params': {k: str(v) if isinstance(v, (list, dict)) else v
                       for k, v in self.params.items()},
            'timestamp': self.timestamp.isoformat(),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


@dataclass
class WalkForwardResult:
    """Walk-Forward 검증 결과.

    Attributes:
        is_valid: 검증 통과 여부
        in_sample_score: In-Sample 점수
        out_of_sample_score: Out-of-Sample 점수
        robustness_ratio: 견고성 비율 (OOS/IS)
        fold_results: 각 폴드 결과
        overfitting_detected: 과적합 감지 여부
        recommendation: 권장 조치
    """
    is_valid: bool = False
    in_sample_score: float = 0.0
    out_of_sample_score: float = 0.0
    robustness_ratio: float = 0.0
    fold_results: List[Dict[str, Any]] = field(default_factory=list)
    overfitting_detected: bool = False
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'is_valid': self.is_valid,
            'in_sample_score': self.in_sample_score,
            'out_of_sample_score': self.out_of_sample_score,
            'robustness_ratio': self.robustness_ratio,
            'fold_results': self.fold_results,
            'overfitting_detected': self.overfitting_detected,
            'recommendation': self.recommendation,
        }


class IterativeOptimizerEnhanced(IterativeOptimizer):
    """향상된 반복적 조건식 개선 오케스트레이터.

    Phase 4-5 기능:
    - Walk-Forward 검증 자동화
    - 일시정지/재개 기능
    - 과적합 감지 통합
    - UI 진행상황 차트 데이터

    Attributes:
        overfitting_guard: 과적합 감지기
        is_paused: 일시정지 상태
        is_stopped: 중지 요청 상태
        checkpoint: 체크포인트 데이터
    """

    def __init__(
        self,
        config: IterativeConfig,
        qlist: Optional[list] = None,
        backtest_params: Optional[Dict[str, Any]] = None,
        enable_walk_forward: bool = True,
        enable_overfitting_guard: bool = True,
    ):
        """초기화.

        Args:
            config: ICOS 설정
            qlist: 프로세스 간 통신 큐 리스트
            backtest_params: 백테스트 파라미터
            enable_walk_forward: Walk-Forward 검증 활성화
            enable_overfitting_guard: 과적합 감지 활성화
        """
        super().__init__(config, qlist, backtest_params)

        self.enable_walk_forward = enable_walk_forward
        self.enable_overfitting_guard = enable_overfitting_guard

        # 과적합 감지기 (Phase 4)
        if enable_overfitting_guard:
            from .overfitting_guard import OverfittingGuard
            self._overfitting_guard = OverfittingGuard()
        else:
            self._overfitting_guard = None

        # 일시정지/재개 상태
        self._is_paused = False
        self._is_stopped = False
        self._pause_event = None  # threading.Event 사용 가능

        # 체크포인트
        self._checkpoint: Optional[CheckpointData] = None
        self._checkpoint_path: Optional[Path] = None

        # UI 진행상황 데이터 (Phase 5)
        self._progress_data: List[Dict[str, Any]] = []
        self._filter_effect_data: List[Dict[str, Any]] = []

    # ==========================================================================
    # 일시정지/재개 기능
    # ==========================================================================

    def request_pause(self) -> None:
        """일시정지 요청.

        다음 반복이 시작되기 전에 일시정지됩니다.
        """
        self._is_paused = True
        self._log("일시정지 요청됨 - 현재 반복 완료 후 정지합니다.", UI_COLOR_WARNING)

    def request_stop(self) -> None:
        """중지 요청.

        현재 반복을 완료한 후 ICOS를 종료합니다.
        """
        self._is_stopped = True
        self._log("중지 요청됨 - 현재 반복 완료 후 종료합니다.", UI_COLOR_WARNING)

    def resume(self) -> None:
        """일시정지에서 재개."""
        self._is_paused = False
        self._log("재개됨", UI_COLOR_INFO)

    def is_paused(self) -> bool:
        """일시정지 상태 확인."""
        return self._is_paused

    def is_stopped(self) -> bool:
        """중지 상태 확인."""
        return self._is_stopped

    def _save_checkpoint(self, iteration: int, buystg: str, sellstg: str,
                         params: Dict[str, Any]) -> None:
        """체크포인트 저장.

        Args:
            iteration: 현재 반복 번호
            buystg: 현재 매수 조건식
            sellstg: 매도 조건식
            params: 백테스트 파라미터
        """
        self._checkpoint = CheckpointData(
            iteration=iteration,
            buystg=buystg,
            sellstg=sellstg,
            iteration_results=self.반복결과목록.copy(),
            start_time=self._start_time,
            config=self.config,
            params=params,
        )

        if self._checkpoint_path:
            self._checkpoint.save(self._checkpoint_path)
            self._log(f"체크포인트 저장: {self._checkpoint_path}", UI_COLOR_GRAY)

    def get_checkpoint(self) -> Optional[CheckpointData]:
        """현재 체크포인트 반환."""
        return self._checkpoint

    def run_from_checkpoint(
        self,
        checkpoint: CheckpointData,
    ) -> IterativeResult:
        """체크포인트에서 실행 재개.

        Args:
            checkpoint: 체크포인트 데이터

        Returns:
            IterativeResult: 최적화 결과
        """
        self._log(f"체크포인트에서 재개: 반복 {checkpoint.iteration + 1}부터", UI_COLOR_INFO)

        # 상태 복원
        self.현재반복 = checkpoint.iteration
        self.반복결과목록 = checkpoint.iteration_results
        self._start_time = checkpoint.start_time
        self._is_paused = False
        self._is_stopped = False

        # 실행 재개
        return self.run(
            buystg=checkpoint.buystg,
            sellstg=checkpoint.sellstg,
            backtest_params=checkpoint.params,
        )

    # ==========================================================================
    # Walk-Forward 검증
    # ==========================================================================

    def run_with_walk_forward_validation(
        self,
        buystg: str,
        sellstg: str,
        backtest_params: Optional[Dict[str, Any]] = None,
        n_folds: int = 5,
        validation_ratio: float = 0.2,
    ) -> Tuple[IterativeResult, WalkForwardResult]:
        """Walk-Forward 검증과 함께 실행.

        ICOS 완료 후 Walk-Forward 검증을 자동 수행합니다.

        Args:
            buystg: 초기 매수 조건식
            sellstg: 매도 조건식
            backtest_params: 백테스트 파라미터
            n_folds: 폴드 수
            validation_ratio: 검증 데이터 비율

        Returns:
            (ICOS 결과, Walk-Forward 검증 결과)
        """
        # 1. ICOS 실행
        icos_result = self.run(buystg, sellstg, backtest_params)

        if not icos_result.success:
            return icos_result, WalkForwardResult(
                is_valid=False,
                recommendation="ICOS 실행 실패로 Walk-Forward 검증 스킵"
            )

        # 2. Walk-Forward 검증
        self._log("═══ Walk-Forward 검증 시작 ═══", UI_COLOR_HIGHLIGHT)

        wf_result = self._run_walk_forward_validation(
            buystg=icos_result.final_buystg,
            sellstg=icos_result.final_sellstg,
            params=backtest_params or self.backtest_params,
            n_folds=n_folds,
            validation_ratio=validation_ratio,
        )

        # 3. 결과 로그
        if wf_result.is_valid:
            self._log(
                f"Walk-Forward 검증 통과 (견고성: {wf_result.robustness_ratio:.1%})",
                UI_COLOR_SUCCESS
            )
        else:
            self._log(
                f"Walk-Forward 검증 실패 - {wf_result.recommendation}",
                UI_COLOR_WARNING
            )

        return icos_result, wf_result

    def _run_walk_forward_validation(
        self,
        buystg: str,
        sellstg: str,
        params: Dict[str, Any],
        n_folds: int = 5,
        validation_ratio: float = 0.2,
    ) -> WalkForwardResult:
        """Walk-Forward 검증 실행.

        Args:
            buystg: 매수 조건식
            sellstg: 매도 조건식
            params: 백테스트 파라미터
            n_folds: 폴드 수
            validation_ratio: 검증 비율

        Returns:
            WalkForwardResult
        """
        # 날짜 범위 추출
        start_day = params.get('startday', '20230101')
        end_day = params.get('endday', '20241231')

        try:
            start_dt = datetime.strptime(start_day, '%Y%m%d')
            end_dt = datetime.strptime(end_day, '%Y%m%d')
        except ValueError:
            return WalkForwardResult(
                is_valid=False,
                recommendation="날짜 형식 오류"
            )

        total_days = (end_dt - start_dt).days
        if total_days < n_folds * 30:  # 최소 30일/폴드
            return WalkForwardResult(
                is_valid=False,
                recommendation=f"데이터 기간 부족 (최소 {n_folds * 30}일 필요)"
            )

        # 폴드 생성
        fold_size = total_days // n_folds
        fold_results = []
        is_scores = []
        oos_scores = []

        for fold in range(n_folds):
            fold_start = start_dt + pd.Timedelta(days=fold * fold_size)
            fold_end = fold_start + pd.Timedelta(days=fold_size)

            # In-Sample / Out-of-Sample 분할
            val_days = int(fold_size * validation_ratio)
            is_end = fold_end - pd.Timedelta(days=val_days)

            # In-Sample 백테스트
            is_params = params.copy()
            is_params['startday'] = fold_start.strftime('%Y%m%d')
            is_params['endday'] = is_end.strftime('%Y%m%d')

            is_result = self._execute_backtest(buystg, sellstg, is_params)
            is_profit = is_result['metrics'].get('total_profit', 0)
            is_scores.append(is_profit)

            # Out-of-Sample 백테스트
            oos_params = params.copy()
            oos_params['startday'] = is_end.strftime('%Y%m%d')
            oos_params['endday'] = fold_end.strftime('%Y%m%d')

            oos_result = self._execute_backtest(buystg, sellstg, oos_params)
            oos_profit = oos_result['metrics'].get('total_profit', 0)
            oos_scores.append(oos_profit)

            fold_results.append({
                'fold': fold + 1,
                'is_start': fold_start.strftime('%Y%m%d'),
                'is_end': is_end.strftime('%Y%m%d'),
                'oos_start': is_end.strftime('%Y%m%d'),
                'oos_end': fold_end.strftime('%Y%m%d'),
                'is_profit': is_profit,
                'oos_profit': oos_profit,
            })

            self._log(
                f"  폴드 {fold + 1}/{n_folds}: IS={is_profit:,.0f}, OOS={oos_profit:,.0f}",
                UI_COLOR_GRAY
            )

        # 결과 분석
        avg_is = np.mean(is_scores) if is_scores else 0
        avg_oos = np.mean(oos_scores) if oos_scores else 0
        robustness = avg_oos / avg_is if avg_is > 0 else 0

        # 과적합 판정
        overfitting_detected = robustness < 0.5 or avg_oos < 0

        # 권장 조치 결정
        if overfitting_detected:
            recommendation = "과적합 감지 - 필터 수를 줄이거나 더 긴 기간으로 최적화하세요."
        elif robustness < 0.7:
            recommendation = "견고성 낮음 - 추가 검증 권장"
        else:
            recommendation = "검증 통과"

        return WalkForwardResult(
            is_valid=not overfitting_detected and robustness >= 0.5,
            in_sample_score=avg_is,
            out_of_sample_score=avg_oos,
            robustness_ratio=robustness,
            fold_results=fold_results,
            overfitting_detected=overfitting_detected,
            recommendation=recommendation,
        )

    # ==========================================================================
    # 과적합 감지 통합
    # ==========================================================================

    def _check_overfitting(self, iteration_result: IterationResult) -> Optional[Dict[str, Any]]:
        """과적합 여부 체크.

        Args:
            iteration_result: 현재 반복 결과

        Returns:
            과적합 감지 결과 (None이면 과적합 아님)
        """
        if not self._overfitting_guard:
            return None

        # 이전 반복 메트릭 수집
        iteration_history = [r.metrics for r in self.반복결과목록]

        # 복잡도 계산
        condition_complexity = len(iteration_result.buystg)
        applied_filters = len(iteration_result.applied_filters)

        # 과적합 체크
        result = self._overfitting_guard.check(
            train_metrics=iteration_result.metrics,
            validation_metrics=None,  # 별도 검증 데이터 없음
            condition_complexity=condition_complexity,
            applied_filters=applied_filters,
            iteration_history=iteration_history,
        )

        if result.is_overfitting:
            self._log(
                f"⚠️ 과적합 감지: {result.severity.value} ({result.confidence:.1%} 신뢰도)",
                UI_COLOR_WARNING
            )
            for warning in result.warnings[:2]:  # 상위 2개 경고만
                self._log(f"   • {warning}", UI_COLOR_WARNING)

            if result.should_stop:
                self._log("   → 즉시 중단 권장", UI_COLOR_ERROR)

            return result.to_dict()

        return None

    # ==========================================================================
    # UI 진행상황 데이터 (Phase 5)
    # ==========================================================================

    def _update_ui_progress(self, iteration_result: IterationResult) -> None:
        """UI 진행상황 데이터 업데이트.

        Args:
            iteration_result: 반복 결과
        """
        # 진행상황 데이터 추가
        progress_entry = {
            'iteration': iteration_result.iteration + 1,
            'profit': iteration_result.metrics.get('total_profit', 0),
            'win_rate': iteration_result.metrics.get('win_rate', 0),
            'trade_count': iteration_result.metrics.get('trade_count', 0),
            'filter_count': len(iteration_result.applied_filters),
            'execution_time': iteration_result.execution_time,
            'timestamp': datetime.now().isoformat(),
        }
        self._progress_data.append(progress_entry)

        # 필터 효과 데이터 추가
        for f in iteration_result.applied_filters:
            filter_entry = {
                'iteration': iteration_result.iteration + 1,
                'filter_description': f.description,
                'expected_impact': f.expected_impact,
                'source': f.source,
            }
            self._filter_effect_data.append(filter_entry)

        # UI 업데이트 메시지 전송 (chartQ 사용)
        if self.qlist and len(self.qlist) > 4:
            chartQ = self.qlist[4]
            chartQ.put(('icos_progress', self._progress_data.copy()))

    def get_progress_data(self) -> List[Dict[str, Any]]:
        """진행상황 데이터 반환."""
        return self._progress_data.copy()

    def get_filter_effect_data(self) -> List[Dict[str, Any]]:
        """필터 효과 데이터 반환."""
        return self._filter_effect_data.copy()

    def _estimate_remaining_time(self) -> str:
        """남은 예상 시간 계산.

        Returns:
            예상 시간 문자열
        """
        if not self._progress_data:
            return "계산 중..."

        # 평균 실행 시간
        avg_time = np.mean([p['execution_time'] for p in self._progress_data])
        remaining_iterations = self.config.max_iterations - self.현재반복 - 1

        remaining_seconds = avg_time * remaining_iterations

        if remaining_seconds < 60:
            return f"{remaining_seconds:.0f}초"
        elif remaining_seconds < 3600:
            return f"{remaining_seconds / 60:.1f}분"
        else:
            return f"{remaining_seconds / 3600:.1f}시간"

    # ==========================================================================
    # 텔레그램 알림 (Phase 6)
    # ==========================================================================

    def _send_telegram_summary(self, result: IterativeResult) -> None:
        """텔레그램으로 ICOS 완료 요약 전송.

        Args:
            result: ICOS 결과
        """
        if not self.qlist or len(self.qlist) <= 3:
            return

        teleQ = self.qlist[3]

        # 요약 메시지 생성
        if result.success:
            status = "✅ 성공"
        else:
            status = "❌ 실패"

        initial_profit = result.iterations[0].metrics.get('total_profit', 0) if result.iterations else 0
        final_profit = result.iterations[-1].metrics.get('total_profit', 0) if result.iterations else 0

        message = f"""
═══ ICOS 완료 알림 ═══
상태: {status}
반복: {result.num_iterations}회
시간: {result.total_execution_time:.1f}초

📊 성과 변화
초기 수익금: {initial_profit:,.0f}원
최종 수익금: {final_profit:,.0f}원
개선율: {result.total_improvement:.1%}

종료 사유: {result.convergence_reason}
"""
        teleQ.put(('telegram', message.strip()))
