"""
반복적 조건식 개선 시스템 (ICOS) - 결과 분석기.

Iterative Condition Optimization System - Result Analyzer.

이 모듈은 백테스트 결과(df_tsg)를 분석하여 손실 거래 패턴을 추출하고,
필터 생성에 필요한 정보를 제공합니다.

기존 강화 분석 모듈(analysis_enhanced)을 활용하여 통계적으로 유의한
필터 후보를 식별합니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import pandas as pd
import numpy as np

from .config import IterativeConfig, FilterMetric


class LossPatternType(Enum):
    """손실 패턴 유형."""
    TIME_BASED = "time_based"           # 시간대별 손실
    THRESHOLD_BELOW = "threshold_below"  # 임계값 미만 손실
    THRESHOLD_ABOVE = "threshold_above"  # 임계값 이상 손실
    RANGE_INSIDE = "range_inside"        # 범위 내 손실
    RANGE_OUTSIDE = "range_outside"      # 범위 외 손실
    SEGMENT = "segment"                  # 세그먼트별 손실
    ML_PREDICTED = "ml_predicted"        # ML 예측 손실


@dataclass
class LossPattern:
    """손실 거래 패턴.

    손실 거래의 공통 특징을 나타내는 데이터 클래스입니다.

    Attributes:
        pattern_type: 패턴 유형
        column: 관련 컬럼명
        condition: 패턴 조건 (Python 표현식)
        description: 패턴 설명
        loss_count: 해당 패턴의 손실 거래 수
        total_loss: 해당 패턴의 총 손실금액
        loss_ratio: 손실 비율 (해당 조건 거래 중 손실 비율)
        coverage: 커버리지 (전체 손실 거래 중 해당 패턴 비율)
        confidence: 신뢰도 점수 (0.0 ~ 1.0)
        statistical_significance: 통계적 유의성 (p-value)
        metadata: 추가 메타데이터
    """
    pattern_type: LossPatternType
    column: str
    condition: str
    description: str
    loss_count: int
    total_loss: float
    loss_ratio: float
    coverage: float
    confidence: float = 0.0
    statistical_significance: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'pattern_type': self.pattern_type.value,
            'column': self.column,
            'condition': self.condition,
            'description': self.description,
            'loss_count': self.loss_count,
            'total_loss': self.total_loss,
            'loss_ratio': self.loss_ratio,
            'coverage': self.coverage,
            'confidence': self.confidence,
            'statistical_significance': self.statistical_significance,
        }


@dataclass
class FeatureImportance:
    """특징 중요도.

    손실 거래 예측에서 각 특징의 중요도를 나타냅니다.

    Attributes:
        column: 컬럼명
        importance: 중요도 점수 (0.0 ~ 1.0)
        direction: 손실과의 관계 방향 ('positive', 'negative', 'nonlinear')
        mean_loss: 손실 거래에서의 평균값
        mean_profit: 이익 거래에서의 평균값
        separation: 분리도 (손실/이익 평균 차이의 표준화 값)
    """
    column: str
    importance: float
    direction: str
    mean_loss: float
    mean_profit: float
    separation: float

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'column': self.column,
            'importance': self.importance,
            'direction': self.direction,
            'mean_loss': self.mean_loss,
            'mean_profit': self.mean_profit,
            'separation': self.separation,
        }


@dataclass
class AnalysisResult:
    """분석 결과.

    ResultAnalyzer의 분석 결과를 담는 데이터 클래스입니다.

    Attributes:
        total_trades: 총 거래 수
        loss_trades: 손실 거래 수
        profit_trades: 이익 거래 수
        total_profit: 총 수익금
        total_loss: 총 손실금 (음수)
        win_rate: 승률 (%)
        loss_patterns: 발견된 손실 패턴 목록
        feature_importances: 특징 중요도 목록
        segment_analysis: 세그먼트 분석 결과 (옵션)
        filter_candidates: 기존 분석 도구의 필터 후보 (옵션)
        metadata: 추가 메타데이터
    """
    total_trades: int
    loss_trades: int
    profit_trades: int
    total_profit: float
    total_loss: float
    win_rate: float
    loss_patterns: List[LossPattern]
    feature_importances: List[FeatureImportance]
    segment_analysis: Optional[Dict[str, Any]] = None
    filter_candidates: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def net_profit(self) -> float:
        """순이익."""
        return self.total_profit + self.total_loss

    @property
    def profit_factor(self) -> float:
        """손익비."""
        if self.total_loss == 0:
            return float('inf') if self.total_profit > 0 else 0.0
        return abs(self.total_profit / self.total_loss)

    def get_top_patterns(self, n: int = 5) -> List[LossPattern]:
        """상위 N개 손실 패턴 반환 (총 손실금액 기준)."""
        return sorted(
            self.loss_patterns,
            key=lambda p: abs(p.total_loss),
            reverse=True
        )[:n]

    def get_top_features(self, n: int = 5) -> List[FeatureImportance]:
        """상위 N개 중요 특징 반환."""
        return sorted(
            self.feature_importances,
            key=lambda f: f.importance,
            reverse=True
        )[:n]

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'total_trades': self.total_trades,
            'loss_trades': self.loss_trades,
            'profit_trades': self.profit_trades,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'net_profit': self.net_profit,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'loss_patterns': [p.to_dict() for p in self.loss_patterns],
            'feature_importances': [f.to_dict() for f in self.feature_importances],
        }


class ResultAnalyzer:
    """백테스트 결과 분석기.

    백테스트 결과(df_tsg)를 분석하여 손실 거래 패턴을 추출하고,
    필터 생성에 필요한 정보를 제공합니다.

    Attributes:
        config: ICOS 설정

    Example:
        >>> analyzer = ResultAnalyzer(config)
        >>> result = analyzer.analyze(df_tsg)
        >>> top_patterns = result.get_top_patterns(5)
    """

    # 분석 대상 컬럼 (룩어헤드 없는 매수 시점 정보)
    # 주의: columns_bt (utility/setting.py)에 정의된 컬럼명과 일치해야 함
    ANALYSIS_COLUMNS = [
        # 가격/등락 (columns_bt에 존재)
        '매수등락율', '매수시가등락율', '매수고저평균대비등락율',
        # 거래량/대금 (columns_bt에 존재)
        '매수당일거래대금', '매수전일비', '매수회전율', '매수전일동시간비',
        '당일거래대금_전틱분봉_비율', '당일거래대금_5틱분봉평균_비율',
        # 체결 강도 (columns_bt에 존재)
        '매수체결강도',
        # 호가 (columns_bt에 존재)
        '매수호가잔량비', '매수스프레드',
        '매수매도총잔량', '매수매수총잔량',
        # 시가총액 (columns_bt에 존재)
        '시가총액',
        # 고가/저가 (columns_bt에 존재)
        '매수고가', '매수저가',
        # 틱 데이터 (columns_bt에 존재)
        '매수초당매수수량', '매수초당매도수량', '매수초당거래대금',
        # 시간 관련
        '매수일자',
    ]

    # 시간대 컬럼
    TIME_COLUMNS = ['매수시', '매수분']

    # 분석 제외 컬럼 (룩어헤드 또는 결과 변수)
    EXCLUDE_COLUMNS = [
        '수익금', '수익률', '매도가', '매도시간', '보유시간',
        '매도등락율', '매도체결강도', '매도당일거래대금',
    ]

    def __init__(self, config: IterativeConfig):
        """ResultAnalyzer 초기화.

        Args:
            config: ICOS 설정
        """
        self.config = config
        self._enhanced_analysis_available = self._check_enhanced_analysis()

    def _check_enhanced_analysis(self) -> bool:
        """강화 분석 모듈 사용 가능 여부 확인."""
        try:
            from backtester.analysis_enhanced.filters import AnalyzeFilterEffectsEnhanced
            return True
        except ImportError:
            return False

    def analyze(
        self,
        df_tsg: pd.DataFrame,
        use_enhanced: bool = True,
        use_ml: bool = False,
    ) -> AnalysisResult:
        """백테스트 결과 분석.

        Args:
            df_tsg: 거래 상세 DataFrame
            use_enhanced: 기존 강화 분석 모듈 사용 여부
            use_ml: ML 기반 분석 사용 여부

        Returns:
            AnalysisResult: 분석 결과
        """
        if df_tsg is None or df_tsg.empty:
            return self._empty_result()

        # 기본 통계 계산
        total_trades = len(df_tsg)
        loss_mask = df_tsg['수익금'] <= 0
        loss_trades = loss_mask.sum()
        profit_trades = total_trades - loss_trades

        total_profit = df_tsg.loc[~loss_mask, '수익금'].sum() if profit_trades > 0 else 0.0
        total_loss = df_tsg.loc[loss_mask, '수익금'].sum() if loss_trades > 0 else 0.0
        win_rate = (profit_trades / total_trades * 100) if total_trades > 0 else 0.0

        # 손실 패턴 분석
        loss_patterns = self._analyze_loss_patterns(df_tsg, loss_mask)

        # 특징 중요도 분석
        feature_importances = self._analyze_feature_importance(df_tsg, loss_mask)

        # 기존 강화 분석 도구 활용 (옵션)
        filter_candidates = None
        if use_enhanced and self._enhanced_analysis_available:
            filter_candidates = self._run_enhanced_analysis(df_tsg, use_ml)

        return AnalysisResult(
            total_trades=total_trades,
            loss_trades=loss_trades,
            profit_trades=profit_trades,
            total_profit=total_profit,
            total_loss=total_loss,
            win_rate=win_rate,
            loss_patterns=loss_patterns,
            feature_importances=feature_importances,
            filter_candidates=filter_candidates,
            metadata={
                'use_enhanced': use_enhanced,
                'use_ml': use_ml,
                'enhanced_available': self._enhanced_analysis_available,
            },
        )

    def _empty_result(self) -> AnalysisResult:
        """빈 분석 결과 반환."""
        return AnalysisResult(
            total_trades=0,
            loss_trades=0,
            profit_trades=0,
            total_profit=0.0,
            total_loss=0.0,
            win_rate=0.0,
            loss_patterns=[],
            feature_importances=[],
        )

    def _analyze_loss_patterns(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
    ) -> List[LossPattern]:
        """손실 거래 패턴 분석.

        Args:
            df_tsg: 거래 상세 DataFrame
            loss_mask: 손실 거래 마스크

        Returns:
            손실 패턴 목록
        """
        patterns: List[LossPattern] = []
        total_loss_count = loss_mask.sum()
        total_loss_amount = abs(df_tsg.loc[loss_mask, '수익금'].sum())

        if total_loss_count == 0:
            return patterns

        # 디버그: 분석 가능한 컬럼 확인
        available_cols = [c for c in self.ANALYSIS_COLUMNS if c in df_tsg.columns]
        available_time_cols = [c for c in self.TIME_COLUMNS if c in df_tsg.columns]

        # verbose 모드에서 디버그 정보 출력
        if self.config.verbose:
            print(f"[ICOS Analyzer] 총 거래: {len(df_tsg)}, 손실 거래: {total_loss_count}")
            print(f"[ICOS Analyzer] 분석 가능 컬럼: {len(available_cols)}/{len(self.ANALYSIS_COLUMNS)}")
            print(f"[ICOS Analyzer] 시간 컬럼: {available_time_cols}")

        # 1. 시간대별 손실 패턴 (기본)
        time_patterns = self._analyze_time_patterns(df_tsg, loss_mask, total_loss_count)
        patterns.extend(time_patterns)
        if self.config.verbose:
            print(f"[ICOS Analyzer] 시간대 패턴: {len(time_patterns)}개 발견")

        # 2. 임계값 기반 손실 패턴
        threshold_patterns = self._analyze_threshold_patterns(df_tsg, loss_mask, total_loss_count)
        patterns.extend(threshold_patterns)
        if self.config.verbose:
            print(f"[ICOS Analyzer] 임계값 패턴: {len(threshold_patterns)}개 발견")

        # 3. 범위 기반 손실 패턴 (시가총액 등)
        range_patterns = self._analyze_range_patterns(df_tsg, loss_mask, total_loss_count)
        patterns.extend(range_patterns)
        if self.config.verbose:
            print(f"[ICOS Analyzer] 범위 패턴: {len(range_patterns)}개 발견")

        # 4. Phase 3: 고급 시간대 패턴 (5분 단위, 요일별, 세션별)
        advanced_time_patterns = self._analyze_time_patterns_advanced(df_tsg, loss_mask, total_loss_count)
        patterns.extend(advanced_time_patterns)
        if self.config.verbose:
            print(f"[ICOS Analyzer] 고급 시간 패턴: {len(advanced_time_patterns)}개 발견")

        # 5. Phase 3: 복합 조건 패턴 (시간+가격, 거래량+체결강도 등)
        compound_patterns = self._analyze_compound_patterns(df_tsg, loss_mask, total_loss_count)
        patterns.extend(compound_patterns)
        if self.config.verbose:
            print(f"[ICOS Analyzer] 복합 패턴: {len(compound_patterns)}개 발견")

        # 신뢰도 기준 필터링 및 정렬
        # 최소 신뢰도를 0.2로 낮춤 (기존 0.3) - 더 많은 패턴 발견 허용
        min_confidence = 0.2
        before_filter = len(patterns)
        patterns = [p for p in patterns if p.confidence >= min_confidence]
        if self.config.verbose:
            print(f"[ICOS Analyzer] 신뢰도 필터링: {before_filter} → {len(patterns)}개")

        patterns.sort(key=lambda p: abs(p.total_loss), reverse=True)

        return patterns

    def _analyze_time_patterns(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
    ) -> List[LossPattern]:
        """시간대별 손실 패턴 분석."""
        patterns: List[LossPattern] = []

        if '매수시' not in df_tsg.columns:
            return patterns

        for hour in sorted(df_tsg['매수시'].unique()):
            hour_mask = df_tsg['매수시'] == hour
            hour_trades = hour_mask.sum()

            if hour_trades < self.config.filter_generation.min_sample_size:
                continue

            hour_loss_mask = hour_mask & loss_mask
            hour_loss_count = hour_loss_mask.sum()
            hour_loss_amount = df_tsg.loc[hour_loss_mask, '수익금'].sum()
            hour_loss_ratio = hour_loss_count / hour_trades if hour_trades > 0 else 0

            # 전체 손실률과 비교하여 이 시간대가 특히 나쁜지 확인
            overall_loss_ratio = loss_mask.mean()
            if hour_loss_ratio <= overall_loss_ratio:
                continue  # 전체보다 나쁘지 않으면 스킵

            # 커버리지 계산 (전체 손실 중 이 시간대 손실 비율)
            coverage = hour_loss_count / total_loss_count if total_loss_count > 0 else 0

            # 신뢰도 계산 (손실률 차이 * 샘플 수 반영)
            loss_ratio_diff = hour_loss_ratio - overall_loss_ratio
            sample_factor = min(1.0, hour_trades / 100)  # 100건 이상이면 1.0
            confidence = min(1.0, loss_ratio_diff * 2 * sample_factor)

            patterns.append(LossPattern(
                pattern_type=LossPatternType.TIME_BASED,
                column='매수시',
                condition=f"df_tsg['매수시'] == {hour}",
                description=f"시간대 {hour}시 (손실률 {hour_loss_ratio:.1%}, 전체 {overall_loss_ratio:.1%})",
                loss_count=hour_loss_count,
                total_loss=hour_loss_amount,
                loss_ratio=hour_loss_ratio,
                coverage=coverage,
                confidence=confidence,
                metadata={'hour': hour, 'hour_trades': hour_trades},
            ))

        return patterns

    def _analyze_threshold_patterns(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
    ) -> List[LossPattern]:
        """임계값 기반 손실 패턴 분석."""
        patterns: List[LossPattern] = []

        available_cols = [c for c in self.ANALYSIS_COLUMNS if c in df_tsg.columns]

        for col in available_cols:
            if df_tsg[col].isna().all():
                continue

            # 수치형 컬럼만 처리 (문자열 컬럼 제외)
            if not pd.api.types.is_numeric_dtype(df_tsg[col]):
                continue

            # 손실 거래와 이익 거래의 분포 비교
            loss_values = df_tsg.loc[loss_mask, col].dropna()
            profit_values = df_tsg.loc[~loss_mask, col].dropna()

            if len(loss_values) < 10 or len(profit_values) < 10:
                continue

            try:
                loss_mean = loss_values.mean()
                profit_mean = profit_values.mean()

                # 평균 차이가 유의미한 경우
                combined_std = df_tsg[col].std()
                if combined_std == 0 or pd.isna(combined_std):
                    continue
            except (TypeError, ValueError):
                # 수치 연산 실패 시 건너뛰기
                continue

            separation = (loss_mean - profit_mean) / combined_std

            # 임계값 후보 탐색
            if abs(separation) > 0.3:  # 효과 크기가 충분한 경우
                patterns.extend(self._find_threshold_patterns(
                    df_tsg, loss_mask, col, separation, total_loss_count
                ))

        return patterns

    def _find_threshold_patterns(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        col: str,
        separation: float,
        total_loss_count: int,
    ) -> List[LossPattern]:
        """특정 컬럼의 임계값 패턴 탐색."""
        patterns: List[LossPattern] = []

        # 분위수 기반 임계값 후보
        percentiles = [10, 20, 30, 70, 80, 90]
        thresholds = df_tsg[col].quantile([p/100 for p in percentiles]).tolist()

        overall_loss_ratio = loss_mask.mean()

        for i, threshold in enumerate(thresholds):
            # 미만 조건 (하위 제외)
            if percentiles[i] <= 50:
                cond_mask = df_tsg[col] < threshold
                cond_type = LossPatternType.THRESHOLD_BELOW
                direction = "미만"
            else:
                cond_mask = df_tsg[col] >= threshold
                cond_type = LossPatternType.THRESHOLD_ABOVE
                direction = "이상"

            cond_trades = cond_mask.sum()
            if cond_trades < self.config.filter_generation.min_sample_size:
                continue

            cond_loss_mask = cond_mask & loss_mask
            cond_loss_count = cond_loss_mask.sum()
            cond_loss_amount = df_tsg.loc[cond_loss_mask, '수익금'].sum()
            cond_loss_ratio = cond_loss_count / cond_trades if cond_trades > 0 else 0

            # 이 조건의 손실률이 전체보다 높은 경우만
            if cond_loss_ratio <= overall_loss_ratio * 1.1:  # 10% 이상 높아야
                continue

            coverage = cond_loss_count / total_loss_count if total_loss_count > 0 else 0

            # 신뢰도 계산
            loss_ratio_diff = cond_loss_ratio - overall_loss_ratio
            sample_factor = min(1.0, cond_trades / 100)
            confidence = min(1.0, loss_ratio_diff * 2 * sample_factor)

            if confidence < 0.3:
                continue

            patterns.append(LossPattern(
                pattern_type=cond_type,
                column=col,
                condition=f"df_tsg['{col}'] {'<' if direction == '미만' else '>='} {threshold:.4f}",
                description=f"{col} {threshold:.2f} {direction} (손실률 {cond_loss_ratio:.1%})",
                loss_count=cond_loss_count,
                total_loss=cond_loss_amount,
                loss_ratio=cond_loss_ratio,
                coverage=coverage,
                confidence=confidence,
                metadata={
                    'threshold': threshold,
                    'percentile': percentiles[i],
                    'separation': separation,
                },
            ))

        return patterns

    def _analyze_range_patterns(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
    ) -> List[LossPattern]:
        """범위 기반 손실 패턴 분석 (시가총액 등)."""
        patterns: List[LossPattern] = []

        # 시가총액 범위 분석
        if '시가총액' in df_tsg.columns:
            patterns.extend(self._analyze_marketcap_patterns(
                df_tsg, loss_mask, total_loss_count
            ))

        return patterns

    def _analyze_marketcap_patterns(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
    ) -> List[LossPattern]:
        """시가총액 범위 패턴 분석."""
        patterns: List[LossPattern] = []

        # 시가총액 구간 (억 원 단위)
        bins = [0, 5000, 10000, 30000, 50000, 100000, float('inf')]
        labels = ['소형(~5천억)', '소중형(5천~1조)', '중형(1~3조)',
                  '중대형(3~5조)', '대형(5~10조)', '초대형(10조~)']

        df_tsg = df_tsg.copy()
        df_tsg['시총구간'] = pd.cut(df_tsg['시가총액'], bins=bins, labels=labels)

        overall_loss_ratio = loss_mask.mean()

        for label in labels:
            cap_mask = df_tsg['시총구간'] == label
            cap_trades = cap_mask.sum()

            if cap_trades < self.config.filter_generation.min_sample_size:
                continue

            cap_loss_mask = cap_mask & loss_mask
            cap_loss_count = cap_loss_mask.sum()
            cap_loss_amount = df_tsg.loc[cap_loss_mask, '수익금'].sum()
            cap_loss_ratio = cap_loss_count / cap_trades if cap_trades > 0 else 0

            if cap_loss_ratio <= overall_loss_ratio * 1.1:
                continue

            coverage = cap_loss_count / total_loss_count if total_loss_count > 0 else 0

            loss_ratio_diff = cap_loss_ratio - overall_loss_ratio
            sample_factor = min(1.0, cap_trades / 100)
            confidence = min(1.0, loss_ratio_diff * 2 * sample_factor)

            if confidence < 0.3:
                continue

            # 해당 구간의 시가총액 범위 찾기
            idx = labels.index(label)
            lower = bins[idx]
            upper = bins[idx + 1]

            patterns.append(LossPattern(
                pattern_type=LossPatternType.RANGE_INSIDE,
                column='시가총액',
                condition=f"(df_tsg['시가총액'] >= {lower}) & (df_tsg['시가총액'] < {upper})",
                description=f"시가총액 {label} (손실률 {cap_loss_ratio:.1%})",
                loss_count=cap_loss_count,
                total_loss=cap_loss_amount,
                loss_ratio=cap_loss_ratio,
                coverage=coverage,
                confidence=confidence,
                metadata={'range': (lower, upper), 'label': label},
            ))

        return patterns

    def _analyze_feature_importance(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
    ) -> List[FeatureImportance]:
        """특징 중요도 분석."""
        importances: List[FeatureImportance] = []

        available_cols = [c for c in self.ANALYSIS_COLUMNS if c in df_tsg.columns]

        for col in available_cols:
            if df_tsg[col].isna().all():
                continue

            # 수치형 컬럼만 처리 (문자열 컬럼 제외)
            if not pd.api.types.is_numeric_dtype(df_tsg[col]):
                continue

            loss_values = df_tsg.loc[loss_mask, col].dropna()
            profit_values = df_tsg.loc[~loss_mask, col].dropna()

            if len(loss_values) < 10 or len(profit_values) < 10:
                continue

            try:
                loss_mean = loss_values.mean()
                profit_mean = profit_values.mean()

                # 분리도 계산 (Cohen's d와 유사)
                pooled_std = np.sqrt(
                    (loss_values.var() * (len(loss_values) - 1) +
                     profit_values.var() * (len(profit_values) - 1)) /
                    (len(loss_values) + len(profit_values) - 2)
                )

                if pooled_std == 0 or pd.isna(pooled_std):
                    continue
            except (TypeError, ValueError):
                # 수치 연산 실패 시 건너뛰기
                continue

            separation = (loss_mean - profit_mean) / pooled_std

            # 방향 결정
            if separation > 0.2:
                direction = 'positive'  # 높을수록 손실
            elif separation < -0.2:
                direction = 'negative'  # 낮을수록 손실
            else:
                direction = 'nonlinear'

            # 중요도 점수 (분리도의 절대값)
            importance = min(1.0, abs(separation) / 2)

            importances.append(FeatureImportance(
                column=col,
                importance=importance,
                direction=direction,
                mean_loss=loss_mean,
                mean_profit=profit_mean,
                separation=separation,
            ))

        # 중요도 순 정렬
        importances.sort(key=lambda x: x.importance, reverse=True)

        return importances

    def _run_enhanced_analysis(
        self,
        df_tsg: pd.DataFrame,
        use_ml: bool,
    ) -> Optional[List[Dict[str, Any]]]:
        """기존 강화 분석 도구 실행."""
        try:
            from backtester.analysis_enhanced.filters import AnalyzeFilterEffectsEnhanced

            results = AnalyzeFilterEffectsEnhanced(
                df_tsg,
                allow_ml_filters=use_ml,
                correction_method='fdr_bh',
            )

            # 딕셔너리 형태로 변환
            if results:
                return [
                    {
                        'filter_name': r.get('필터명', ''),
                        'condition': r.get('조건식', ''),
                        'code': r.get('적용코드', ''),
                        'category': r.get('분류', ''),
                        'improvement': r.get('수익개선금액', 0),
                        'exclusion_ratio': r.get('제외비율', 0),
                        'remaining_trades': r.get('잔여거래수', 0),
                        'p_value': r.get('p값', 1.0),
                        'significant': r.get('유의함', False),
                    }
                    for r in results
                ]
        except Exception:
            pass

        return None

    # ==================== Phase 3: Advanced Analysis Methods ====================

    def _analyze_time_patterns_advanced(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
    ) -> List[LossPattern]:
        """고급 시간대 패턴 분석.

        Phase 3 Enhancement: 5분 단위 세분화, 요일별 패턴, 장 시작/종료 세션 분석

        Args:
            df_tsg: 거래 상세 DataFrame
            loss_mask: 손실 거래 마스크
            total_loss_count: 전체 손실 거래 수

        Returns:
            고급 시간 패턴 목록
        """
        patterns: List[LossPattern] = []
        overall_loss_ratio = loss_mask.mean()

        # 1. 5분 단위 세분화 분석
        if '매수시' in df_tsg.columns and '매수분' in df_tsg.columns:
            patterns.extend(self._analyze_5min_intervals(
                df_tsg, loss_mask, total_loss_count, overall_loss_ratio
            ))

        # 2. 요일별 패턴 분석
        if '매수일자' in df_tsg.columns:
            patterns.extend(self._analyze_weekday_patterns(
                df_tsg, loss_mask, total_loss_count, overall_loss_ratio
            ))

        # 3. 장 시작/종료 세션 분석
        if '매수시' in df_tsg.columns and '매수분' in df_tsg.columns:
            patterns.extend(self._analyze_market_sessions(
                df_tsg, loss_mask, total_loss_count, overall_loss_ratio
            ))

        return patterns

    def _analyze_5min_intervals(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
        overall_loss_ratio: float,
    ) -> List[LossPattern]:
        """5분 단위 시간대 분석."""
        patterns: List[LossPattern] = []

        # 5분 단위로 구간 생성 (ex: 9시 5분 → 905, 9시 10분 → 910)
        df_tsg = df_tsg.copy()
        df_tsg['_time_5min'] = df_tsg['매수시'] * 100 + (df_tsg['매수분'] // 5) * 5

        for interval in sorted(df_tsg['_time_5min'].unique()):
            interval_mask = df_tsg['_time_5min'] == interval
            interval_trades = interval_mask.sum()

            if interval_trades < self.config.filter_generation.min_sample_size:
                continue

            interval_loss_mask = interval_mask & loss_mask
            interval_loss_count = interval_loss_mask.sum()
            interval_loss_amount = df_tsg.loc[interval_loss_mask, '수익금'].sum()
            interval_loss_ratio = interval_loss_count / interval_trades if interval_trades > 0 else 0

            if interval_loss_ratio <= overall_loss_ratio * 1.1:
                continue

            coverage = interval_loss_count / total_loss_count if total_loss_count > 0 else 0
            confidence = self._calculate_pattern_confidence_advanced(
                interval_loss_ratio, overall_loss_ratio, interval_trades, total_loss_count
            )

            if confidence < 0.25:
                continue

            hour = interval // 100
            minute = interval % 100

            patterns.append(LossPattern(
                pattern_type=LossPatternType.TIME_BASED,
                column='매수시분',
                condition=f"(df_tsg['매수시'] == {hour}) & (df_tsg['매수분'] >= {minute}) & (df_tsg['매수분'] < {minute + 5})",
                description=f"시간대 {hour}:{minute:02d}~{minute+5:02d} (손실률 {interval_loss_ratio:.1%})",
                loss_count=interval_loss_count,
                total_loss=interval_loss_amount,
                loss_ratio=interval_loss_ratio,
                coverage=coverage,
                confidence=confidence,
                metadata={
                    'hour': hour,
                    'minute_start': minute,
                    'minute_end': minute + 5,
                    'interval_trades': interval_trades,
                    'analysis_type': '5min_interval'
                },
            ))

        return patterns

    def _analyze_weekday_patterns(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
        overall_loss_ratio: float,
    ) -> List[LossPattern]:
        """요일별 패턴 분석."""
        patterns: List[LossPattern] = []

        df_tsg = df_tsg.copy()
        try:
            # 매수일자를 datetime으로 변환하여 요일 추출
            df_tsg['_weekday'] = pd.to_datetime(df_tsg['매수일자'].astype(str)).dt.dayofweek
            weekday_names = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
        except Exception:
            return patterns

        for weekday in sorted(df_tsg['_weekday'].unique()):
            weekday_mask = df_tsg['_weekday'] == weekday
            weekday_trades = weekday_mask.sum()

            if weekday_trades < self.config.filter_generation.min_sample_size:
                continue

            weekday_loss_mask = weekday_mask & loss_mask
            weekday_loss_count = weekday_loss_mask.sum()
            weekday_loss_amount = df_tsg.loc[weekday_loss_mask, '수익금'].sum()
            weekday_loss_ratio = weekday_loss_count / weekday_trades if weekday_trades > 0 else 0

            if weekday_loss_ratio <= overall_loss_ratio * 1.1:
                continue

            coverage = weekday_loss_count / total_loss_count if total_loss_count > 0 else 0
            confidence = self._calculate_pattern_confidence_advanced(
                weekday_loss_ratio, overall_loss_ratio, weekday_trades, total_loss_count
            )

            if confidence < 0.25:
                continue

            weekday_name = weekday_names[weekday] if weekday < len(weekday_names) else f"요일{weekday}"

            patterns.append(LossPattern(
                pattern_type=LossPatternType.TIME_BASED,
                column='요일',
                condition=f"pd.to_datetime(df_tsg['매수일자'].astype(str)).dt.dayofweek == {weekday}",
                description=f"{weekday_name} (손실률 {weekday_loss_ratio:.1%})",
                loss_count=weekday_loss_count,
                total_loss=weekday_loss_amount,
                loss_ratio=weekday_loss_ratio,
                coverage=coverage,
                confidence=confidence,
                metadata={
                    'weekday': weekday,
                    'weekday_name': weekday_name,
                    'weekday_trades': weekday_trades,
                    'analysis_type': 'weekday'
                },
            ))

        return patterns

    def _analyze_market_sessions(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
        overall_loss_ratio: float,
    ) -> List[LossPattern]:
        """장 시작/종료 세션 분석 (09:00-09:30, 15:00-15:30)."""
        patterns: List[LossPattern] = []

        sessions = [
            {'name': '장시작(09:00-09:30)', 'hour_start': 9, 'min_start': 0, 'hour_end': 9, 'min_end': 30},
            {'name': '오전초반(09:30-10:00)', 'hour_start': 9, 'min_start': 30, 'hour_end': 10, 'min_end': 0},
            {'name': '점심(11:30-13:00)', 'hour_start': 11, 'min_start': 30, 'hour_end': 13, 'min_end': 0},
            {'name': '오후초반(13:00-14:00)', 'hour_start': 13, 'min_start': 0, 'hour_end': 14, 'min_end': 0},
            {'name': '장마감전(15:00-15:30)', 'hour_start': 15, 'min_start': 0, 'hour_end': 15, 'min_end': 30},
        ]

        df_tsg = df_tsg.copy()
        df_tsg['_time_mins'] = df_tsg['매수시'] * 60 + df_tsg['매수분']

        for session in sessions:
            start_mins = session['hour_start'] * 60 + session['min_start']
            end_mins = session['hour_end'] * 60 + session['min_end']

            session_mask = (df_tsg['_time_mins'] >= start_mins) & (df_tsg['_time_mins'] < end_mins)
            session_trades = session_mask.sum()

            if session_trades < self.config.filter_generation.min_sample_size:
                continue

            session_loss_mask = session_mask & loss_mask
            session_loss_count = session_loss_mask.sum()
            session_loss_amount = df_tsg.loc[session_loss_mask, '수익금'].sum()
            session_loss_ratio = session_loss_count / session_trades if session_trades > 0 else 0

            if session_loss_ratio <= overall_loss_ratio * 1.1:
                continue

            coverage = session_loss_count / total_loss_count if total_loss_count > 0 else 0
            confidence = self._calculate_pattern_confidence_advanced(
                session_loss_ratio, overall_loss_ratio, session_trades, total_loss_count
            )

            if confidence < 0.25:
                continue

            patterns.append(LossPattern(
                pattern_type=LossPatternType.TIME_BASED,
                column='세션',
                condition=f"((df_tsg['매수시'] * 60 + df_tsg['매수분']) >= {start_mins}) & ((df_tsg['매수시'] * 60 + df_tsg['매수분']) < {end_mins})",
                description=f"세션 {session['name']} (손실률 {session_loss_ratio:.1%})",
                loss_count=session_loss_count,
                total_loss=session_loss_amount,
                loss_ratio=session_loss_ratio,
                coverage=coverage,
                confidence=confidence,
                metadata={
                    'session_name': session['name'],
                    'start_time': f"{session['hour_start']:02d}:{session['min_start']:02d}",
                    'end_time': f"{session['hour_end']:02d}:{session['min_end']:02d}",
                    'session_trades': session_trades,
                    'analysis_type': 'market_session'
                },
            ))

        return patterns

    def _analyze_compound_patterns(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
    ) -> List[LossPattern]:
        """복합 조건 패턴 탐지.

        Phase 3 Enhancement: 시간+가격, 거래량+체결강도 등 복합 패턴 분석

        Args:
            df_tsg: 거래 상세 DataFrame
            loss_mask: 손실 거래 마스크
            total_loss_count: 전체 손실 거래 수

        Returns:
            복합 패턴 목록
        """
        patterns: List[LossPattern] = []
        overall_loss_ratio = loss_mask.mean()

        # 1. 시간 + 등락율 복합 패턴
        patterns.extend(self._analyze_time_price_compound(
            df_tsg, loss_mask, total_loss_count, overall_loss_ratio
        ))

        # 2. 거래량 + 체결강도 복합 패턴
        patterns.extend(self._analyze_volume_strength_compound(
            df_tsg, loss_mask, total_loss_count, overall_loss_ratio
        ))

        # 3. 시가총액 + 거래량 복합 패턴
        patterns.extend(self._analyze_cap_volume_compound(
            df_tsg, loss_mask, total_loss_count, overall_loss_ratio
        ))

        return patterns

    def _analyze_time_price_compound(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
        overall_loss_ratio: float,
    ) -> List[LossPattern]:
        """시간 + 등락율 복합 패턴."""
        patterns: List[LossPattern] = []

        if '매수시' not in df_tsg.columns or '매수등락율' not in df_tsg.columns:
            return patterns

        # 등락율 구간 정의
        price_thresholds = [
            ('급등(20%↑)', 20, float('inf')),
            ('상승(10~20%)', 10, 20),
            ('하락(~-5%)', float('-inf'), -5),
        ]

        for hour in [9, 10, 14, 15]:  # 주요 시간대만
            hour_mask = df_tsg['매수시'] == hour

            for price_name, price_min, price_max in price_thresholds:
                if price_max == float('inf'):
                    price_mask = df_tsg['매수등락율'] >= price_min
                    price_cond = f"df_tsg['매수등락율'] >= {price_min}"
                elif price_min == float('-inf'):
                    price_mask = df_tsg['매수등락율'] < price_max
                    price_cond = f"df_tsg['매수등락율'] < {price_max}"
                else:
                    price_mask = (df_tsg['매수등락율'] >= price_min) & (df_tsg['매수등락율'] < price_max)
                    price_cond = f"(df_tsg['매수등락율'] >= {price_min}) & (df_tsg['매수등락율'] < {price_max})"

                compound_mask = hour_mask & price_mask
                compound_trades = compound_mask.sum()

                if compound_trades < self.config.filter_generation.min_sample_size:
                    continue

                compound_loss_mask = compound_mask & loss_mask
                compound_loss_count = compound_loss_mask.sum()
                compound_loss_amount = df_tsg.loc[compound_loss_mask, '수익금'].sum()
                compound_loss_ratio = compound_loss_count / compound_trades if compound_trades > 0 else 0

                # 복합 패턴은 더 높은 손실률 기준 적용
                if compound_loss_ratio <= overall_loss_ratio * 1.2:
                    continue

                coverage = compound_loss_count / total_loss_count if total_loss_count > 0 else 0
                confidence = self._calculate_pattern_confidence_advanced(
                    compound_loss_ratio, overall_loss_ratio, compound_trades, total_loss_count
                )

                if confidence < 0.3:
                    continue

                patterns.append(LossPattern(
                    pattern_type=LossPatternType.SEGMENT,
                    column='시간_등락율',
                    condition=f"(df_tsg['매수시'] == {hour}) & ({price_cond})",
                    description=f"{hour}시 + {price_name} (손실률 {compound_loss_ratio:.1%})",
                    loss_count=compound_loss_count,
                    total_loss=compound_loss_amount,
                    loss_ratio=compound_loss_ratio,
                    coverage=coverage,
                    confidence=confidence,
                    metadata={
                        'hour': hour,
                        'price_range': price_name,
                        'compound_trades': compound_trades,
                        'analysis_type': 'time_price_compound'
                    },
                ))

        return patterns

    def _analyze_volume_strength_compound(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
        overall_loss_ratio: float,
    ) -> List[LossPattern]:
        """거래량 + 체결강도 복합 패턴."""
        patterns: List[LossPattern] = []

        vol_col = '매수전일비' if '매수전일비' in df_tsg.columns else None
        strength_col = '매수체결강도' if '매수체결강도' in df_tsg.columns else None

        if vol_col is None or strength_col is None:
            return patterns

        # 거래량과 체결강도의 분위수 계산
        try:
            vol_q33 = df_tsg[vol_col].quantile(0.33)
            vol_q67 = df_tsg[vol_col].quantile(0.67)
            str_q33 = df_tsg[strength_col].quantile(0.33)
            str_q67 = df_tsg[strength_col].quantile(0.67)
        except Exception:
            return patterns

        # 조합 분석 (저거래량+저체결강도, 고거래량+저체결강도 등)
        combinations = [
            ('저거래량_저체결', vol_col, '<', vol_q33, strength_col, '<', str_q33),
            ('고거래량_저체결', vol_col, '>', vol_q67, strength_col, '<', str_q33),
            ('저거래량_고체결', vol_col, '<', vol_q33, strength_col, '>', str_q67),
        ]

        for combo_name, col1, op1, val1, col2, op2, val2 in combinations:
            if op1 == '<':
                mask1 = df_tsg[col1] < val1
                cond1 = f"df_tsg['{col1}'] < {val1:.4f}"
            else:
                mask1 = df_tsg[col1] > val1
                cond1 = f"df_tsg['{col1}'] > {val1:.4f}"

            if op2 == '<':
                mask2 = df_tsg[col2] < val2
                cond2 = f"df_tsg['{col2}'] < {val2:.4f}"
            else:
                mask2 = df_tsg[col2] > val2
                cond2 = f"df_tsg['{col2}'] > {val2:.4f}"

            compound_mask = mask1 & mask2
            compound_trades = compound_mask.sum()

            if compound_trades < self.config.filter_generation.min_sample_size:
                continue

            compound_loss_mask = compound_mask & loss_mask
            compound_loss_count = compound_loss_mask.sum()
            compound_loss_amount = df_tsg.loc[compound_loss_mask, '수익금'].sum()
            compound_loss_ratio = compound_loss_count / compound_trades if compound_trades > 0 else 0

            if compound_loss_ratio <= overall_loss_ratio * 1.2:
                continue

            coverage = compound_loss_count / total_loss_count if total_loss_count > 0 else 0
            confidence = self._calculate_pattern_confidence_advanced(
                compound_loss_ratio, overall_loss_ratio, compound_trades, total_loss_count
            )

            if confidence < 0.3:
                continue

            patterns.append(LossPattern(
                pattern_type=LossPatternType.SEGMENT,
                column='거래량_체결강도',
                condition=f"({cond1}) & ({cond2})",
                description=f"{combo_name} (손실률 {compound_loss_ratio:.1%})",
                loss_count=compound_loss_count,
                total_loss=compound_loss_amount,
                loss_ratio=compound_loss_ratio,
                coverage=coverage,
                confidence=confidence,
                metadata={
                    'combination': combo_name,
                    'compound_trades': compound_trades,
                    'analysis_type': 'volume_strength_compound'
                },
            ))

        return patterns

    def _analyze_cap_volume_compound(
        self,
        df_tsg: pd.DataFrame,
        loss_mask: pd.Series,
        total_loss_count: int,
        overall_loss_ratio: float,
    ) -> List[LossPattern]:
        """시가총액 + 거래량 복합 패턴."""
        patterns: List[LossPattern] = []

        if '시가총액' not in df_tsg.columns:
            return patterns

        vol_col = '매수당일거래대금' if '매수당일거래대금' in df_tsg.columns else None
        if vol_col is None:
            return patterns

        # 시가총액 구간
        cap_ranges = [
            ('소형', 0, 5000),
            ('중형', 5000, 30000),
            ('대형', 30000, float('inf')),
        ]

        # 거래대금 분위수
        try:
            vol_q50 = df_tsg[vol_col].quantile(0.50)
        except Exception:
            return patterns

        for cap_name, cap_min, cap_max in cap_ranges:
            if cap_max == float('inf'):
                cap_mask = df_tsg['시가총액'] >= cap_min
            else:
                cap_mask = (df_tsg['시가총액'] >= cap_min) & (df_tsg['시가총액'] < cap_max)

            # 저거래대금 조건
            vol_mask = df_tsg[vol_col] < vol_q50

            compound_mask = cap_mask & vol_mask
            compound_trades = compound_mask.sum()

            if compound_trades < self.config.filter_generation.min_sample_size:
                continue

            compound_loss_mask = compound_mask & loss_mask
            compound_loss_count = compound_loss_mask.sum()
            compound_loss_amount = df_tsg.loc[compound_loss_mask, '수익금'].sum()
            compound_loss_ratio = compound_loss_count / compound_trades if compound_trades > 0 else 0

            if compound_loss_ratio <= overall_loss_ratio * 1.2:
                continue

            coverage = compound_loss_count / total_loss_count if total_loss_count > 0 else 0
            confidence = self._calculate_pattern_confidence_advanced(
                compound_loss_ratio, overall_loss_ratio, compound_trades, total_loss_count
            )

            if confidence < 0.3:
                continue

            if cap_max == float('inf'):
                cap_cond = f"df_tsg['시가총액'] >= {cap_min}"
            else:
                cap_cond = f"(df_tsg['시가총액'] >= {cap_min}) & (df_tsg['시가총액'] < {cap_max})"

            patterns.append(LossPattern(
                pattern_type=LossPatternType.SEGMENT,
                column='시총_거래대금',
                condition=f"({cap_cond}) & (df_tsg['{vol_col}'] < {vol_q50:.4f})",
                description=f"{cap_name}주 + 저거래대금 (손실률 {compound_loss_ratio:.1%})",
                loss_count=compound_loss_count,
                total_loss=compound_loss_amount,
                loss_ratio=compound_loss_ratio,
                coverage=coverage,
                confidence=confidence,
                metadata={
                    'cap_range': cap_name,
                    'compound_trades': compound_trades,
                    'analysis_type': 'cap_volume_compound'
                },
            ))

        return patterns

    def _calculate_pattern_confidence_advanced(
        self,
        pattern_loss_ratio: float,
        overall_loss_ratio: float,
        pattern_sample_size: int,
        total_loss_count: int,
    ) -> float:
        """고급 신뢰도 계산.

        Phase 3 Enhancement: 카이제곱 검정 기반 통계적 유의성, Cohen's h 효과 크기

        Args:
            pattern_loss_ratio: 패턴의 손실률
            overall_loss_ratio: 전체 손실률
            pattern_sample_size: 패턴 샘플 수
            total_loss_count: 전체 손실 거래 수

        Returns:
            신뢰도 점수 (0.0 ~ 1.0)
        """
        if pattern_sample_size == 0 or overall_loss_ratio == 0:
            return 0.0

        # 1. 손실률 차이 기반 기본 점수
        loss_ratio_diff = pattern_loss_ratio - overall_loss_ratio
        if loss_ratio_diff <= 0:
            return 0.0

        # 2. Cohen's h 효과 크기 계산 (비율 차이의 효과 크기)
        # Cohen's h = 2 * (arcsin(sqrt(p1)) - arcsin(sqrt(p2)))
        import math
        try:
            h1 = math.asin(math.sqrt(min(1.0, max(0.0, pattern_loss_ratio))))
            h2 = math.asin(math.sqrt(min(1.0, max(0.0, overall_loss_ratio))))
            cohens_h = abs(2 * (h1 - h2))
        except (ValueError, ZeroDivisionError):
            cohens_h = 0.0

        # 3. 표본 적정성 점수 (100건 기준)
        sample_adequacy = min(1.0, pattern_sample_size / 100)

        # 4. 커버리지 보정 (너무 작은 커버리지는 패널티)
        pattern_loss_count = int(pattern_loss_ratio * pattern_sample_size)
        coverage = pattern_loss_count / total_loss_count if total_loss_count > 0 else 0
        coverage_factor = min(1.0, coverage * 10)  # 10% 커버리지면 1.0

        # 5. 카이제곱 검정 기반 유의성 (간단한 근사)
        # 기대값: pattern_sample_size * overall_loss_ratio
        # 관측값: pattern_sample_size * pattern_loss_ratio
        expected = pattern_sample_size * overall_loss_ratio
        observed = pattern_sample_size * pattern_loss_ratio

        if expected > 0:
            chi_sq_approx = ((observed - expected) ** 2) / expected
            # p-value 근사 (chi_sq > 3.84 이면 p < 0.05)
            significance_factor = min(1.0, chi_sq_approx / 10)  # 10 이상이면 매우 유의
        else:
            significance_factor = 0.0

        # 6. 최종 신뢰도 계산 (가중 평균)
        confidence = (
            cohens_h * 0.30 +           # 효과 크기 30%
            sample_adequacy * 0.25 +     # 표본 적정성 25%
            coverage_factor * 0.15 +     # 커버리지 15%
            significance_factor * 0.30   # 통계적 유의성 30%
        )

        return min(1.0, max(0.0, confidence))

    # ==================== End Phase 3: Advanced Analysis Methods ====================

    def get_loss_summary(self, df_tsg: pd.DataFrame) -> Dict[str, Any]:
        """손실 거래 요약 정보 반환.

        Args:
            df_tsg: 거래 상세 DataFrame

        Returns:
            손실 요약 딕셔너리
        """
        if df_tsg is None or df_tsg.empty:
            return {}

        loss_mask = df_tsg['수익금'] <= 0
        loss_df = df_tsg[loss_mask]

        if loss_df.empty:
            return {'loss_count': 0}

        return {
            'loss_count': len(loss_df),
            'total_loss': loss_df['수익금'].sum(),
            'avg_loss': loss_df['수익금'].mean(),
            'max_loss': loss_df['수익금'].min(),
            'loss_by_hour': loss_df.groupby('매수시')['수익금'].sum().to_dict()
            if '매수시' in loss_df.columns else {},
        }
