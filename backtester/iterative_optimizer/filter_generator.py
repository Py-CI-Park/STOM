"""
반복적 조건식 개선 시스템 (ICOS) - 필터 생성기.

Iterative Condition Optimization System - Filter Generator.

이 모듈은 분석 결과를 기반으로 필터 후보를 생성합니다.
손실 패턴에서 필터 조건을 추출하고, 우선순위를 결정합니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import re

from .config import IterativeConfig, FilterMetric
from .analyzer import AnalysisResult, LossPattern, LossPatternType, FeatureImportance
from .data_types import FilterCandidate


class FilterPriority(Enum):
    """필터 우선순위."""
    CRITICAL = 1    # 즉시 적용 권장
    HIGH = 2        # 높은 우선순위
    MEDIUM = 3      # 중간 우선순위
    LOW = 4         # 낮은 우선순위
    EXPERIMENTAL = 5  # 실험적 (검증 필요)


@dataclass
class FilterScore:
    """필터 점수.

    필터의 효과와 신뢰도를 종합한 점수입니다.

    Attributes:
        improvement_score: 개선 점수 (손실 제거량 기반)
        confidence_score: 신뢰도 점수
        stability_score: 안정성 점수
        coverage_score: 커버리지 점수
        total_score: 종합 점수
    """
    improvement_score: float
    confidence_score: float
    stability_score: float
    coverage_score: float

    @property
    def total_score(self) -> float:
        """종합 점수 계산 (가중 평균)."""
        weights = {
            'improvement': 0.4,
            'confidence': 0.3,
            'stability': 0.2,
            'coverage': 0.1,
        }
        return (
            self.improvement_score * weights['improvement'] +
            self.confidence_score * weights['confidence'] +
            self.stability_score * weights['stability'] +
            self.coverage_score * weights['coverage']
        )


class FilterGenerator:
    """필터 생성기.

    분석 결과를 기반으로 조건식에 적용할 필터 후보를 생성합니다.

    Attributes:
        config: ICOS 설정

    Example:
        >>> generator = FilterGenerator(config)
        >>> filters = generator.generate(analysis_result)
        >>> top_filter = filters[0]
    """

    def __init__(self, config: IterativeConfig):
        """FilterGenerator 초기화.

        Args:
            config: ICOS 설정
        """
        self.config = config

    def generate(
        self,
        analysis: AnalysisResult,
        max_filters: Optional[int] = None,
    ) -> List[FilterCandidate]:
        """필터 후보 생성.

        분석 결과를 기반으로 필터 후보를 생성하고 우선순위를 결정합니다.

        Args:
            analysis: 분석 결과
            max_filters: 최대 생성 필터 수 (None이면 설정값 사용)

        Returns:
            필터 후보 목록 (우선순위 순)
        """
        if not analysis.loss_patterns:
            return []

        max_count = max_filters or self.config.filter_generation.max_filters_per_iteration

        # 1. 손실 패턴에서 필터 후보 생성
        candidates = self._generate_from_patterns(analysis.loss_patterns)

        # 2. 기존 분석 도구 결과에서 필터 후보 추가 (있는 경우)
        if analysis.filter_candidates:
            candidates.extend(self._generate_from_enhanced(analysis.filter_candidates))

        # 3. 중복 제거
        candidates = self._deduplicate(candidates)

        # 4. 점수 계산 및 정렬
        scored_candidates = [
            (self._calculate_score(c, analysis), c)
            for c in candidates
        ]
        scored_candidates.sort(key=lambda x: x[0].total_score, reverse=True)

        # 5. 상위 N개 선택
        top_candidates = [c for _, c in scored_candidates[:max_count]]

        return top_candidates

    def _generate_from_patterns(
        self,
        patterns: List[LossPattern],
    ) -> List[FilterCandidate]:
        """손실 패턴에서 필터 후보 생성."""
        candidates: List[FilterCandidate] = []

        for pattern in patterns:
            candidate = self._pattern_to_filter(pattern)
            if candidate:
                candidates.append(candidate)

        return candidates

    def _pattern_to_filter(self, pattern: LossPattern) -> Optional[FilterCandidate]:
        """손실 패턴을 필터 후보로 변환."""
        # 패턴 유형에 따른 필터 코드 생성
        if pattern.pattern_type == LossPatternType.TIME_BASED:
            return self._create_time_filter(pattern)
        elif pattern.pattern_type == LossPatternType.THRESHOLD_BELOW:
            return self._create_threshold_below_filter(pattern)
        elif pattern.pattern_type == LossPatternType.THRESHOLD_ABOVE:
            return self._create_threshold_above_filter(pattern)
        elif pattern.pattern_type == LossPatternType.RANGE_INSIDE:
            return self._create_range_filter(pattern)
        elif pattern.pattern_type == LossPatternType.RANGE_OUTSIDE:
            return self._create_range_filter(pattern)
        elif pattern.pattern_type == LossPatternType.SEGMENT:
            return self._create_segment_filter(pattern)

        return None

    def _create_segment_filter(self, pattern: LossPattern) -> Optional[FilterCandidate]:
        """세그먼트(복합) 패턴 필터 생성."""
        analysis_type = pattern.metadata.get('analysis_type', '')

        if analysis_type == 'time_price_compound':
            # 시간 + 등락율 복합 패턴
            hour = pattern.metadata.get('hour', 0)
            price_range = pattern.metadata.get('price_range', '')

            # 등락율 조건 파싱
            if '급등' in price_range:
                price_cond = "(등락율 < 20)"
            elif '상승' in price_range:
                price_cond = "not ((등락율 >= 10) and (등락율 < 20))"
            elif '하락' in price_range:
                price_cond = "(등락율 >= -5)"
            else:
                price_cond = "True"

            condition = f"not ((시분초 // 10000 == {hour}) and not {price_cond})"
            description = f"{hour}시 + {price_range} 제외 (손실률 {pattern.loss_ratio:.1%})"

        elif analysis_type == 'volume_strength_compound':
            # 거래량 + 체결강도 복합 패턴은 조건이 이미 pattern.condition에 있음
            # 이를 런타임 변수로 변환 필요
            combination = pattern.metadata.get('combination', '')
            # 복잡한 복합 조건은 건너뜀 (런타임 변수 매핑 어려움)
            return None

        elif analysis_type == 'cap_volume_compound':
            # 시가총액 + 거래량 복합 패턴
            # 복잡한 복합 조건은 건너뜀
            return None

        else:
            return None

        return FilterCandidate(
            condition=condition,
            description=description,
            source="loss_pattern",
            expected_impact=pattern.confidence,
            metadata={
                'pattern_type': pattern.pattern_type.value,
                'analysis_type': analysis_type,
                'loss_count': pattern.loss_count,
                'total_loss': pattern.total_loss,
            },
        )

    def _create_time_filter(self, pattern: LossPattern) -> FilterCandidate:
        """시간대 필터 생성.

        다양한 시간 패턴 유형 처리:
        - 시간대 (hour): 매수시 != hour
        - 5분 단위 (5min_interval): (매수시 != hour) or (매수분 < minute_start) or (매수분 >= minute_end)
        - 세션 (market_session): 시간 범위 제외
        - 요일 (weekday): 요일 제외 (런타임 지원 필요)
        """
        analysis_type = pattern.metadata.get('analysis_type', 'hour')

        if analysis_type == '5min_interval':
            # 5분 단위 시간대 제외
            hour = pattern.metadata.get('hour', 0)
            minute_start = pattern.metadata.get('minute_start', 0)
            minute_end = pattern.metadata.get('minute_end', 5)

            # 해당 5분 구간 제외 조건 (구간 밖이면 True)
            # not ((매수시 == hour) and (매수분 >= minute_start) and (매수분 < minute_end))
            condition = f"not ((시분초 // 10000 == {hour}) and ((시분초 // 100) % 100 >= {minute_start}) and ((시분초 // 100) % 100 < {minute_end}))"
            description = f"시간대 {hour}:{minute_start:02d}~{minute_end:02d} 제외 (손실률 {pattern.loss_ratio:.1%})"

        elif analysis_type == 'market_session':
            # 세션 시간대 제외
            start_time = pattern.metadata.get('start_time', '09:00')
            end_time = pattern.metadata.get('end_time', '09:30')
            session_name = pattern.metadata.get('session_name', '세션')

            # 시간을 분 단위로 변환
            start_parts = start_time.split(':')
            end_parts = end_time.split(':')
            start_mins = int(start_parts[0]) * 60 + int(start_parts[1])
            end_mins = int(end_parts[0]) * 60 + int(end_parts[1])

            # 시분초에서 분 단위로 변환하여 비교
            # 시분초 = HHMMSS 형식 (ex: 93015 = 09:30:15)
            condition = f"not (((시분초 // 10000) * 60 + ((시분초 // 100) % 100) >= {start_mins}) and ((시분초 // 10000) * 60 + ((시분초 // 100) % 100) < {end_mins}))"
            description = f"세션 {session_name} 제외 (손실률 {pattern.loss_ratio:.1%})"

        elif analysis_type == 'weekday':
            # 요일 제외 - 런타임에서 매수일자로 요일 계산 필요
            # 현재는 건너뜀 (런타임 지원 필요)
            weekday = pattern.metadata.get('weekday', 0)
            weekday_name = pattern.metadata.get('weekday_name', '')
            # 직접 적용 불가 - 런타임에서 요일 계산 필요하므로 기본 필터로 처리하지 않음
            return None

        else:
            # 기본 시간대 (hour 단위)
            hour = pattern.metadata.get('hour', 0)
            condition = f"(시분초 // 10000 != {hour})"
            description = f"시간대 {hour}시 제외 (손실률 {pattern.loss_ratio:.1%})"

        return FilterCandidate(
            condition=condition,
            description=description,
            source="loss_pattern",
            expected_impact=pattern.confidence,
            metadata={
                'pattern_type': pattern.pattern_type.value,
                'column': pattern.column,
                'analysis_type': analysis_type,
                'loss_count': pattern.loss_count,
                'total_loss': pattern.total_loss,
            },
        )

    def _create_threshold_below_filter(self, pattern: LossPattern) -> FilterCandidate:
        """미만 임계값 필터 생성 (해당 값 미만 제외)."""
        threshold = pattern.metadata.get('threshold', 0)
        col = pattern.column

        # 변수명 변환 (df_tsg 컬럼명 -> buystg 변수명)
        var_name = self._column_to_variable(col)

        # 필터 조건: 미만 제외 -> 이상만 허용
        condition = f"({var_name} >= {threshold:.4f})"

        return FilterCandidate(
            condition=condition,
            description=f"{col} {threshold:.2f} 미만 제외",
            source="loss_pattern",
            expected_impact=pattern.confidence,
            metadata={
                'pattern_type': pattern.pattern_type.value,
                'column': col,
                'threshold': threshold,
                'direction': 'below',
                'loss_count': pattern.loss_count,
                'total_loss': pattern.total_loss,
            },
        )

    def _create_threshold_above_filter(self, pattern: LossPattern) -> FilterCandidate:
        """이상 임계값 필터 생성 (해당 값 이상 제외)."""
        threshold = pattern.metadata.get('threshold', 0)
        col = pattern.column

        var_name = self._column_to_variable(col)

        # 필터 조건: 이상 제외 -> 미만만 허용
        condition = f"({var_name} < {threshold:.4f})"

        return FilterCandidate(
            condition=condition,
            description=f"{col} {threshold:.2f} 이상 제외",
            source="loss_pattern",
            expected_impact=pattern.confidence,
            metadata={
                'pattern_type': pattern.pattern_type.value,
                'column': col,
                'threshold': threshold,
                'direction': 'above',
                'loss_count': pattern.loss_count,
                'total_loss': pattern.total_loss,
            },
        )

    def _create_range_filter(self, pattern: LossPattern) -> FilterCandidate:
        """범위 필터 생성."""
        range_tuple = pattern.metadata.get('range', (0, 0))
        lower, upper = range_tuple
        col = pattern.column

        var_name = self._column_to_variable(col)

        if pattern.pattern_type == LossPatternType.RANGE_INSIDE:
            # 범위 내 제외 -> 범위 밖만 허용
            if upper == float('inf'):
                condition = f"({var_name} < {lower:.0f})"
            else:
                condition = f"(({var_name} < {lower:.0f}) or ({var_name} >= {upper:.0f}))"
            desc = f"{col} {lower:.0f}~{upper:.0f} 범위 제외"
        else:
            # 범위 밖 제외 -> 범위 내만 허용
            condition = f"(({var_name} >= {lower:.0f}) and ({var_name} < {upper:.0f}))"
            desc = f"{col} {lower:.0f}~{upper:.0f} 범위만 허용"

        return FilterCandidate(
            condition=condition,
            description=desc,
            source="loss_pattern",
            expected_impact=pattern.confidence,
            metadata={
                'pattern_type': pattern.pattern_type.value,
                'column': col,
                'range': range_tuple,
                'loss_count': pattern.loss_count,
                'total_loss': pattern.total_loss,
            },
        )

    def _generate_from_enhanced(
        self,
        filter_candidates: List[Dict[str, Any]],
    ) -> List[FilterCandidate]:
        """기존 강화 분석 결과에서 필터 후보 생성."""
        candidates: List[FilterCandidate] = []

        for fc in filter_candidates:
            # 통계적으로 유의한 필터만
            if not fc.get('significant', False):
                continue

            code = fc.get('code', '')
            if not code:
                continue

            # 필터 코드 정규화
            condition = self._normalize_filter_code(code)

            candidates.append(FilterCandidate(
                condition=condition,
                description=fc.get('filter_name', ''),
                source="enhanced_analysis",
                expected_impact=min(1.0, abs(fc.get('improvement', 0)) / 100000),
                metadata={
                    'category': fc.get('category', ''),
                    'improvement': fc.get('improvement', 0),
                    'exclusion_ratio': fc.get('exclusion_ratio', 0),
                    'p_value': fc.get('p_value', 1.0),
                },
            ))

        return candidates

    def _column_to_variable(self, column: str) -> str:
        """DataFrame 컬럼명을 buystg 변수명으로 변환.

        대부분의 경우 동일하지만, 일부 매핑이 필요할 수 있음.
        """
        # 매수 시점 스냅샷 컬럼은 '매수' 접두사 제거
        if column.startswith('매수') and column != '매수시':
            # 매수등락율 -> 등락율, 매수체결강도 -> 체결강도
            var_name = column[2:]  # '매수' 제거
            return var_name

        # 그 외는 그대로
        return column

    def _normalize_filter_code(self, code: str) -> str:
        """필터 코드 정규화.

        기존 분석 도구의 코드 형식을 ICOS 형식으로 변환합니다.
        """
        # 이미 괄호로 감싸져 있으면 그대로
        code = code.strip()
        if not code.startswith('('):
            code = f"({code})"

        return code

    def _deduplicate(
        self,
        candidates: List[FilterCandidate],
    ) -> List[FilterCandidate]:
        """중복 필터 제거."""
        seen_conditions = set()
        unique_candidates: List[FilterCandidate] = []

        for candidate in candidates:
            # 조건 정규화 (공백 제거, 소문자)
            normalized = re.sub(r'\s+', '', candidate.condition.lower())

            if normalized not in seen_conditions:
                seen_conditions.add(normalized)
                unique_candidates.append(candidate)

        return unique_candidates

    def _calculate_score(
        self,
        candidate: FilterCandidate,
        analysis: AnalysisResult,
    ) -> FilterScore:
        """필터 점수 계산."""
        # 개선 점수 (예상 영향도 기반)
        improvement_score = min(1.0, candidate.expected_impact)

        # 신뢰도 점수
        confidence_score = candidate.expected_impact

        # 안정성 점수 (메타데이터 기반)
        p_value = candidate.metadata.get('p_value', 1.0)
        stability_score = 1.0 - min(1.0, p_value)

        # 커버리지 점수
        loss_count = candidate.metadata.get('loss_count', 0)
        if analysis.loss_trades > 0:
            coverage_score = min(1.0, loss_count / analysis.loss_trades)
        else:
            coverage_score = 0.0

        return FilterScore(
            improvement_score=improvement_score,
            confidence_score=confidence_score,
            stability_score=stability_score,
            coverage_score=coverage_score,
        )

    def prioritize(
        self,
        candidates: List[FilterCandidate],
    ) -> List[Tuple[FilterCandidate, FilterPriority]]:
        """필터 우선순위 결정.

        Args:
            candidates: 필터 후보 목록

        Returns:
            (필터, 우선순위) 튜플 목록
        """
        prioritized: List[Tuple[FilterCandidate, FilterPriority]] = []

        for candidate in candidates:
            priority = self._determine_priority(candidate)
            prioritized.append((candidate, priority))

        # 우선순위 순 정렬
        prioritized.sort(key=lambda x: x[1].value)

        return prioritized

    def _determine_priority(self, candidate: FilterCandidate) -> FilterPriority:
        """필터 우선순위 결정."""
        impact = candidate.expected_impact
        source = candidate.source

        # 높은 영향도 + 통계적 유의성 -> CRITICAL
        if impact >= 0.8 and candidate.metadata.get('p_value', 1.0) < 0.01:
            return FilterPriority.CRITICAL

        # 높은 영향도 -> HIGH
        if impact >= 0.6:
            return FilterPriority.HIGH

        # 중간 영향도 -> MEDIUM
        if impact >= 0.4:
            return FilterPriority.MEDIUM

        # 낮은 영향도 but 통계적 유의성 -> LOW
        if candidate.metadata.get('significant', False):
            return FilterPriority.LOW

        # 그 외 -> EXPERIMENTAL
        return FilterPriority.EXPERIMENTAL

    def generate_combined_filter(
        self,
        candidates: List[FilterCandidate],
        max_combine: int = 3,
    ) -> Optional[FilterCandidate]:
        """여러 필터를 조합한 복합 필터 생성.

        Args:
            candidates: 조합할 필터 후보 목록
            max_combine: 최대 조합 수

        Returns:
            복합 필터 (None이면 조합 불가)
        """
        if not candidates:
            return None

        # 상위 N개 선택
        top_candidates = candidates[:max_combine]

        if len(top_candidates) == 1:
            return top_candidates[0]

        # 조건 조합 (AND)
        conditions = [c.condition for c in top_candidates]
        combined_condition = " and ".join(conditions)

        # 설명 조합
        descriptions = [c.description for c in top_candidates]
        combined_description = " + ".join(descriptions)

        # 예상 영향도 (최대값 사용, 시너지 고려)
        impacts = [c.expected_impact for c in top_candidates]
        combined_impact = min(1.0, max(impacts) * 1.1)  # 10% 시너지 보너스

        return FilterCandidate(
            condition=combined_condition,
            description=f"복합 필터: {combined_description}",
            source="combined",
            expected_impact=combined_impact,
            metadata={
                'combined_count': len(top_candidates),
                'individual_conditions': [c.condition for c in top_candidates],
            },
        )

    def validate_filter(self, candidate: FilterCandidate) -> Tuple[bool, str]:
        """필터 유효성 검증.

        Args:
            candidate: 검증할 필터

        Returns:
            (유효 여부, 오류 메시지)
        """
        condition = candidate.condition

        # 빈 조건
        if not condition or not condition.strip():
            return False, "빈 조건식"

        # 위험한 키워드 체크
        dangerous_keywords = ['import', 'exec', 'eval', '__', 'os.', 'sys.']
        for keyword in dangerous_keywords:
            if keyword in condition:
                return False, f"위험한 키워드 포함: {keyword}"

        # 괄호 균형 체크
        if condition.count('(') != condition.count(')'):
            return False, "괄호 불균형"

        # 기본 문법 체크 (간단한 검증)
        try:
            # 변수를 더미 값으로 대체하여 파싱 테스트
            test_condition = condition
            for var in ['등락율', '체결강도', '시가총액', '매수시', '당일거래대금']:
                test_condition = test_condition.replace(var, '1')
            compile(test_condition, '<string>', 'eval')
        except SyntaxError as e:
            return False, f"문법 오류: {e}"

        return True, ""

    # ==================== Phase 3: Advanced Filter Generation ====================

    def _remove_correlated_filters(
        self,
        candidates: List[FilterCandidate],
        correlation_threshold: float = 0.7,
    ) -> List[FilterCandidate]:
        """상관관계 기반 중복 필터 제거.

        Phase 3 Enhancement: 동일 컬럼 기반 필터 간 상관성 분석으로 중복 제거

        Args:
            candidates: 필터 후보 목록
            correlation_threshold: 상관계수 임계값 (이상이면 중복으로 간주)

        Returns:
            중복 제거된 필터 목록
        """
        if len(candidates) <= 1:
            return candidates

        # 컬럼별 필터 그룹화
        column_groups: Dict[str, List[FilterCandidate]] = {}
        for candidate in candidates:
            col = candidate.metadata.get('column', 'unknown')
            if col not in column_groups:
                column_groups[col] = []
            column_groups[col].append(candidate)

        filtered_candidates: List[FilterCandidate] = []

        for col, group in column_groups.items():
            if len(group) == 1:
                filtered_candidates.extend(group)
                continue

            # 같은 컬럼의 필터 중 최고 점수 필터 선택
            # 또는 서로 다른 방향의 필터는 유지 (예: 미만 제외 vs 이상 제외)
            direction_groups: Dict[str, List[FilterCandidate]] = {}
            for c in group:
                direction = c.metadata.get('direction', 'unknown')
                pattern_type = c.metadata.get('pattern_type', 'unknown')
                key = f"{direction}_{pattern_type}"
                if key not in direction_groups:
                    direction_groups[key] = []
                direction_groups[key].append(c)

            # 각 방향에서 최고 임팩트 필터 선택
            for direction_key, dir_group in direction_groups.items():
                best = max(dir_group, key=lambda x: x.expected_impact)
                filtered_candidates.append(best)

        # 유사 임계값 필터 추가 제거
        final_candidates = self._remove_similar_thresholds(filtered_candidates, correlation_threshold)

        return final_candidates

    def _remove_similar_thresholds(
        self,
        candidates: List[FilterCandidate],
        similarity_threshold: float = 0.7,
    ) -> List[FilterCandidate]:
        """유사한 임계값을 가진 필터 제거."""
        if len(candidates) <= 1:
            return candidates

        kept_candidates: List[FilterCandidate] = []

        for candidate in sorted(candidates, key=lambda x: x.expected_impact, reverse=True):
            threshold = candidate.metadata.get('threshold')
            col = candidate.metadata.get('column', '')
            direction = candidate.metadata.get('direction', '')

            if threshold is None:
                kept_candidates.append(candidate)
                continue

            # 이미 유지된 필터와 임계값 유사성 비교
            is_similar = False
            for kept in kept_candidates:
                kept_threshold = kept.metadata.get('threshold')
                kept_col = kept.metadata.get('column', '')
                kept_direction = kept.metadata.get('direction', '')

                if kept_threshold is None:
                    continue

                # 같은 컬럼, 같은 방향일 때만 비교
                if col == kept_col and direction == kept_direction:
                    # 임계값 유사성 계산 (상대적 차이)
                    if kept_threshold != 0:
                        similarity = 1 - abs(threshold - kept_threshold) / abs(kept_threshold)
                        if similarity >= similarity_threshold:
                            is_similar = True
                            break

            if not is_similar:
                kept_candidates.append(candidate)

        return kept_candidates

    def _analyze_filter_synergy(
        self,
        candidates: List[FilterCandidate],
        analysis: AnalysisResult,
    ) -> Dict[Tuple[int, int], float]:
        """필터 조합의 시너지 효과 분석.

        Phase 3 Enhancement: 필터 조합 시 예상되는 시너지 효과 계산

        Args:
            candidates: 필터 후보 목록
            analysis: 분석 결과

        Returns:
            {(필터1 인덱스, 필터2 인덱스): 시너지 점수} 딕셔너리
        """
        synergy_scores: Dict[Tuple[int, int], float] = {}

        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                synergy = self._calculate_synergy(candidates[i], candidates[j], analysis)
                synergy_scores[(i, j)] = synergy

        return synergy_scores

    def _calculate_synergy(
        self,
        filter1: FilterCandidate,
        filter2: FilterCandidate,
        analysis: AnalysisResult,
    ) -> float:
        """두 필터 간 시너지 점수 계산.

        시너지가 높을수록 함께 적용 시 효과가 좋음
        시너지가 낮거나 음수면 상충되는 필터

        Args:
            filter1: 첫 번째 필터
            filter2: 두 번째 필터
            analysis: 분석 결과

        Returns:
            시너지 점수 (-1.0 ~ 1.0)
        """
        col1 = filter1.metadata.get('column', '')
        col2 = filter2.metadata.get('column', '')

        # 같은 컬럼 기반 필터는 시너지가 낮음 (중복 가능성)
        if col1 == col2:
            return -0.5

        # 보완적 컬럼 조합은 시너지가 높음
        complementary_pairs = [
            ('매수시', '등락율'),      # 시간 + 가격
            ('매수시', '체결강도'),    # 시간 + 체결강도
            ('시가총액', '당일거래대금'),  # 시가총액 + 거래량
            ('등락율', '체결강도'),    # 가격 + 체결강도
            ('전일비', '체결강도'),    # 거래량 + 체결강도
        ]

        for pair in complementary_pairs:
            if (col1 in pair[0] or pair[0] in col1) and (col2 in pair[1] or pair[1] in col2):
                return 0.8
            if (col2 in pair[0] or pair[0] in col2) and (col1 in pair[1] or pair[1] in col1):
                return 0.8

        # 서로 다른 분석 유형의 필터는 중간 시너지
        type1 = filter1.metadata.get('analysis_type', '')
        type2 = filter2.metadata.get('analysis_type', '')

        if type1 != type2 and type1 and type2:
            return 0.5

        # 기본 시너지
        return 0.2

    def _select_by_priority(
        self,
        candidates: List[FilterCandidate],
        max_count: int,
    ) -> List[FilterCandidate]:
        """우선순위 기반 필터 선택.

        Phase 3 Enhancement: CRITICAL > HIGH > MEDIUM > LOW 순으로 선택

        Args:
            candidates: 필터 후보 목록
            max_count: 최대 선택 개수

        Returns:
            선택된 필터 목록
        """
        # 우선순위별 분류
        priority_buckets: Dict[FilterPriority, List[FilterCandidate]] = {
            FilterPriority.CRITICAL: [],
            FilterPriority.HIGH: [],
            FilterPriority.MEDIUM: [],
            FilterPriority.LOW: [],
            FilterPriority.EXPERIMENTAL: [],
        }

        for candidate in candidates:
            priority = self._determine_priority(candidate)
            priority_buckets[priority].append(candidate)

        # 각 버킷 내에서 점수순 정렬
        for priority in priority_buckets:
            priority_buckets[priority].sort(key=lambda x: x.expected_impact, reverse=True)

        # 우선순위 순으로 선택
        selected: List[FilterCandidate] = []
        for priority in FilterPriority:
            if len(selected) >= max_count:
                break
            for candidate in priority_buckets[priority]:
                if len(selected) >= max_count:
                    break
                selected.append(candidate)

        return selected

    def generate_advanced(
        self,
        analysis: AnalysisResult,
        max_filters: Optional[int] = None,
        use_synergy: bool = True,
        remove_correlated: bool = True,
    ) -> List[FilterCandidate]:
        """고급 필터 생성 (Phase 3).

        상관관계 제거, 시너지 분석, 우선순위 기반 선택을 적용한 필터 생성

        Args:
            analysis: 분석 결과
            max_filters: 최대 생성 필터 수
            use_synergy: 시너지 분석 사용 여부
            remove_correlated: 상관 필터 제거 여부

        Returns:
            필터 후보 목록
        """
        if not analysis.loss_patterns:
            return []

        max_count = max_filters or self.config.filter_generation.max_filters_per_iteration

        # 1. 기본 필터 생성
        candidates = self._generate_from_patterns(analysis.loss_patterns)

        # 2. 강화 분석 결과 추가
        if analysis.filter_candidates:
            candidates.extend(self._generate_from_enhanced(analysis.filter_candidates))

        # 3. 기본 중복 제거
        candidates = self._deduplicate(candidates)

        # 4. Phase 3: 상관관계 기반 중복 제거
        if remove_correlated:
            before_count = len(candidates)
            candidates = self._remove_correlated_filters(candidates)
            if self.config.verbose:
                print(f"[ICOS FilterGen] 상관 필터 제거: {before_count} → {len(candidates)}개")

        # 5. 점수 계산
        for candidate in candidates:
            score = self._calculate_score(candidate, analysis)
            candidate.metadata['total_score'] = score.total_score

        # 6. Phase 3: 시너지 분석
        if use_synergy and len(candidates) >= 2:
            synergy_scores = self._analyze_filter_synergy(candidates, analysis)
            # 시너지 정보를 메타데이터에 추가
            for (i, j), synergy in synergy_scores.items():
                if synergy >= 0.5:  # 높은 시너지만 기록
                    if i < len(candidates):
                        existing = candidates[i].metadata.get('synergies', [])
                        existing.append({'partner_idx': j, 'score': synergy})
                        candidates[i].metadata['synergies'] = existing

        # 7. Phase 3: 우선순위 기반 선택
        selected = self._select_by_priority(candidates, max_count)

        if self.config.verbose:
            print(f"[ICOS FilterGen] 최종 선택: {len(selected)}개 필터")
            for i, c in enumerate(selected):
                priority = self._determine_priority(c)
                print(f"  [{i+1}] {priority.name}: {c.description[:50]}...")

        return selected

    def generate_synergistic_combination(
        self,
        candidates: List[FilterCandidate],
        analysis: AnalysisResult,
        max_combine: int = 3,
    ) -> Optional[FilterCandidate]:
        """시너지 기반 복합 필터 생성.

        Phase 3 Enhancement: 시너지 점수가 높은 필터들을 조합

        Args:
            candidates: 조합할 필터 후보 목록
            analysis: 분석 결과
            max_combine: 최대 조합 수

        Returns:
            최적 복합 필터
        """
        if len(candidates) < 2:
            return self.generate_combined_filter(candidates, max_combine)

        # 시너지 분석
        synergy_scores = self._analyze_filter_synergy(candidates, analysis)

        # 최고 시너지 조합 찾기
        best_combination: List[int] = []
        best_total_synergy = -float('inf')

        # 2개 조합
        for (i, j), synergy in synergy_scores.items():
            if synergy > best_total_synergy:
                best_total_synergy = synergy
                best_combination = [i, j]

        # 3개 조합 (선택적)
        if max_combine >= 3 and len(candidates) >= 3:
            for i in range(len(candidates)):
                for j in range(i + 1, len(candidates)):
                    for k in range(j + 1, len(candidates)):
                        total_synergy = (
                            synergy_scores.get((i, j), 0) +
                            synergy_scores.get((i, k), 0) +
                            synergy_scores.get((j, k), 0)
                        ) / 3
                        if total_synergy > best_total_synergy:
                            best_total_synergy = total_synergy
                            best_combination = [i, j, k]

        if not best_combination:
            return self.generate_combined_filter(candidates[:max_combine], max_combine)

        # 최적 조합으로 복합 필터 생성
        selected_candidates = [candidates[i] for i in best_combination if i < len(candidates)]
        combined = self.generate_combined_filter(selected_candidates, len(selected_candidates))

        if combined:
            combined.metadata['synergy_score'] = best_total_synergy
            combined.metadata['combination_indices'] = best_combination

        return combined

    # ==================== End Phase 3: Advanced Filter Generation ====================
