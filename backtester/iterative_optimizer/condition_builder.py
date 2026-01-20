"""
반복적 조건식 개선 시스템 (ICOS) - 조건식 빌더.

Iterative Condition Optimization System - Condition Builder.

이 모듈은 필터 후보를 기존 매수 조건식에 통합하여
새로운 조건식을 생성합니다.

기존 code_generator.py의 패턴을 참조하되, ICOS에 맞게 단순화합니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Set
import re

from .config import IterativeConfig
from .data_types import FilterCandidate


@dataclass
class BuildResult:
    """조건식 빌드 결과.

    Attributes:
        success: 성공 여부
        new_buystg: 새 매수 조건식 (성공 시)
        applied_filters: 실제 적용된 필터 목록
        error_message: 에러 메시지 (실패 시)
        used_variables: 사용된 변수 목록
        preamble_lines: 런타임 preamble 코드 라인들
    """
    success: bool
    new_buystg: str
    applied_filters: List[FilterCandidate]
    error_message: Optional[str] = None
    used_variables: Set[str] = field(default_factory=set)
    preamble_lines: List[str] = field(default_factory=list)


class ConditionBuilder:
    """조건식 빌더.

    필터 후보를 기존 매수 조건식에 통합하여 새 조건식을 생성합니다.

    Attributes:
        config: ICOS 설정

    Example:
        >>> builder = ConditionBuilder(config)
        >>> result = builder.build(buystg, filters)
        >>> if result.success:
        ...     print(f"새 조건식: {result.new_buystg[:100]}...")
    """

    # 필터 조건에서 사용 가능한 변수들 (STOM 패턴)
    ALLOWED_VARIABLES = {
        # 시장 데이터
        '현재가', '시가', '고가', '저가', '등락율', '전일비',
        '당일거래대금', '체결강도', '거래대금증감', '회전율',
        '전일동시간비', '시가총액', '시분초',
        # 파생 등락율 (매수 시점 스냅샷)
        '시가등락율', '고저평균대비등락율',
        # 호가 데이터
        '매도호가1', '매도호가2', '매도호가3', '매도호가4', '매도호가5',
        '매수호가1', '매수호가2', '매수호가3', '매수호가4', '매수호가5',
        '매도잔량1', '매도잔량2', '매도잔량3', '매도잔량4', '매도잔량5',
        '매수잔량1', '매수잔량2', '매수잔량3', '매수잔량4', '매수잔량5',
        # 호가 총잔량
        '매도총잔량', '매수총잔량', '매도매수총잔량',
        '호가잔량비', '매수스프레드',
        # 틱 모드 변수
        '초당매수수량', '초당매도수량', '초당매도_매수_비율', '초당거래대금',
        # 분봉 모드 변수
        '분당매수수량', '분당매도수량', '분당매도_매수_비율', '분당거래대금',
        # 매수 시점 스냅샷 (런타임 변수는 '매수' 접두사 없음)
        '매수등락율', '매수체결강도', '매수당일거래대금',
        '매수초당매수수량', '매수초당매도수량',
        '매수분당매수수량', '매수분당매도수량',
        # 참고: '매수고가', '매수저가', '매수시가'는 df_tsg 컬럼명이며,
        # 런타임에서는 '고가', '저가', '시가'로 변환됨
        # 시간 관련 파생 변수 (시간 필터용)
        '매수시', '매수분',  # 시간대 필터용 (filter_generator에서 시분초 기반으로 변환)
        # 분당 거래 데이터 비율
        '당일거래대금_전틱분봉_비율', '당일거래대금_5틱분봉평균_비율',
        # 파생 점수
        '거래품질점수', '위험도점수',
        # 분위수/중앙값 참조 (런타임 계산 변수)
        '전일비_q33', '전일비_q67', '체결강도_q33', '체결강도_q67',
        '당일거래대금_median',
        # Python 논리 연산자 및 함수 (조건식 파싱용)
        'not', 'and', 'or', 'True', 'False',
    }

    # 필터 마커 (중복 삽입 방지)
    FILTER_MARKER_START = "# === ICOS 필터 시작 ==="
    FILTER_MARKER_END = "# === ICOS 필터 끝 ==="

    def __init__(self, config: IterativeConfig):
        """ConditionBuilder 초기화.

        Args:
            config: ICOS 설정
        """
        self.config = config

    def build(
        self,
        buystg: str,
        filters: List[FilterCandidate],
        max_filters: Optional[int] = None,
    ) -> BuildResult:
        """필터를 적용한 새 조건식 빌드.

        Args:
            buystg: 기존 매수 조건식
            filters: 적용할 필터 후보 목록
            max_filters: 최대 적용 필터 수 (None이면 설정값 사용)

        Returns:
            BuildResult: 빌드 결과
        """
        if not filters:
            return BuildResult(
                success=True,
                new_buystg=buystg,
                applied_filters=[],
            )

        # 최대 필터 수 결정
        limit = max_filters or self.config.filter_generation.max_filters_per_iteration
        filters_to_apply = filters[:limit]

        try:
            # 1. 기존 ICOS 필터 블록 제거 (재적용 시)
            clean_buystg = self._remove_existing_filter_block(buystg)

            # 2. 필터 조건식 생성
            filter_conditions = []
            applied_filters = []
            used_vars: Set[str] = set()

            for f in filters_to_apply:
                # 조건식 검증
                is_valid, error = self.validate_condition(f.condition)
                if not is_valid:
                    continue

                filter_conditions.append(f.condition)
                applied_filters.append(f)
                used_vars.update(self._extract_variables(f.condition))

            if not filter_conditions:
                return BuildResult(
                    success=True,
                    new_buystg=buystg,
                    applied_filters=[],
                    error_message="유효한 필터가 없음",
                )

            # 3. 런타임 preamble 생성 (파생 변수 정의)
            preamble_lines = self._generate_preamble(used_vars)

            # 4. 필터 블록 생성
            filter_block = self._build_filter_block(applied_filters, filter_conditions)

            # 5. 조건식에 삽입
            new_buystg = self._inject_filter_block(clean_buystg, preamble_lines, filter_block)

            # 6. 최종 문법 검증
            syntax_valid, syntax_error = self._validate_syntax(new_buystg)
            if not syntax_valid:
                return BuildResult(
                    success=False,
                    new_buystg=buystg,
                    applied_filters=[],
                    error_message=f"문법 검증 실패: {syntax_error}",
                )

            return BuildResult(
                success=True,
                new_buystg=new_buystg,
                applied_filters=applied_filters,
                used_variables=used_vars,
                preamble_lines=preamble_lines,
            )

        except Exception as e:
            return BuildResult(
                success=False,
                new_buystg=buystg,
                applied_filters=[],
                error_message=str(e),
            )

    def validate_condition(self, condition: str) -> Tuple[bool, Optional[str]]:
        """필터 조건식 유효성 검증.

        Args:
            condition: 검증할 조건식

        Returns:
            (유효 여부, 에러 메시지)
        """
        if not condition or not condition.strip():
            return False, "빈 조건식"

        # 기본 문법 검증 (괄호 균형)
        if condition.count('(') != condition.count(')'):
            return False, "괄호 불균형"

        # 위험한 키워드 검사
        dangerous_patterns = [
            r'\bimport\b', r'\bexec\b', r'\beval\b', r'\bopen\b',
            r'\b__\w+__\b', r'\bos\.',  r'\bsys\.', r'\bsubprocess\.',
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, condition):
                return False, f"허용되지 않은 패턴: {pattern}"

        # 사용된 변수 확인 (허용된 변수만)
        used_vars = self._extract_variables(condition)
        # 주의: self.vars[N] 형식은 항상 허용
        for var in used_vars:
            if var not in self.ALLOWED_VARIABLES and not var.startswith('self.vars'):
                # 숫자만 있는 경우 (상수)는 허용
                if not var.replace('.', '').replace('-', '').isdigit():
                    return False, f"허용되지 않은 변수: {var}"

        # Python 문법 검증 (컴파일 테스트)
        try:
            # 조건식을 if문으로 감싸서 컴파일
            test_code = f"if {condition}:\n    pass"
            compile(test_code, '<string>', 'exec')
        except SyntaxError as e:
            return False, f"문법 오류: {e}"

        return True, None

    def _extract_variables(self, condition: str) -> Set[str]:
        """조건식에서 사용된 변수 추출.

        Args:
            condition: 조건식

        Returns:
            사용된 변수 집합
        """
        variables = set()

        # 한글 변수명 패턴
        korean_var_pattern = r'[가-힣_][가-힣0-9_]*'
        matches = re.findall(korean_var_pattern, condition)
        variables.update(matches)

        # self.vars[N] 패턴
        vars_pattern = r'self\.vars\[\d+\]'
        vars_matches = re.findall(vars_pattern, condition)
        variables.update(vars_matches)

        # 예약어/연산자 제거
        keywords = {'and', 'or', 'not', 'True', 'False', 'None', 'if', 'else'}
        variables -= keywords

        return variables

    def _remove_existing_filter_block(self, buystg: str) -> str:
        """기존 ICOS 필터 블록 제거.

        Args:
            buystg: 조건식

        Returns:
            필터 블록이 제거된 조건식
        """
        if self.FILTER_MARKER_START not in buystg:
            return buystg

        # 마커 사이의 내용 제거
        pattern = rf'{re.escape(self.FILTER_MARKER_START)}.*?{re.escape(self.FILTER_MARKER_END)}\n?'
        cleaned = re.sub(pattern, '', buystg, flags=re.DOTALL)

        return cleaned

    def _generate_preamble(self, used_vars: Set[str]) -> List[str]:
        """런타임 preamble 코드 생성.

        파생 변수(거래품질점수, 위험도점수 등)가 필요한 경우
        해당 변수를 정의하는 코드를 생성합니다.

        Args:
            used_vars: 사용된 변수 집합

        Returns:
            preamble 코드 라인 리스트
        """
        lines = []

        # 거래품질점수 정의
        if '거래품질점수' in used_vars:
            lines.extend([
                "# 거래품질점수 계산",
                "try:",
                "    거래품질점수 = 50",
                "    if 매수체결강도 >= 120: 거래품질점수 += 10",
                "    if 매수체결강도 >= 150: 거래품질점수 += 10",
                "    if 매수당일거래대금 >= 100000000: 거래품질점수 += 10",
                "    if 매수등락율 <= 5: 거래품질점수 += 10",
                "    if 매수등락율 <= 3: 거래품질점수 += 10",
                "except NameError:",
                "    거래품질점수 = 50",
                "",
            ])

        # 위험도점수 정의
        if '위험도점수' in used_vars:
            lines.extend([
                "# 위험도점수 계산",
                "try:",
                "    위험도점수 = 0",
                "    if 매수등락율 >= 20: 위험도점수 += 20",
                "    if 매수등락율 >= 25: 위험도점수 += 15",
                "    if 매수체결강도 <= 80: 위험도점수 += 15",
                "    if 매수체결강도 <= 60: 위험도점수 += 15",
                "    if 매수당일거래대금 <= 10000000: 위험도점수 += 20",
                "except NameError:",
                "    위험도점수 = 50",
                "",
            ])

        # 초당 매수/매도 비율 정의
        if '초당매도_매수_비율' in used_vars:
            lines.extend([
                "# 초당매도_매수_비율 계산",
                "try:",
                "    초당매도_매수_비율 = 초당매도수량 / (초당매수수량 + 1e-6)",
                "except NameError:",
                "    초당매도_매수_비율 = 1.0",
                "",
            ])

        # 분당 매수/매도 비율 정의
        if '분당매도_매수_비율' in used_vars:
            lines.extend([
                "# 분당매도_매수_비율 계산",
                "try:",
                "    분당매도_매수_비율 = 분당매도수량 / (분당매수수량 + 1e-6)",
                "except NameError:",
                "    분당매도_매수_비율 = 1.0",
                "",
            ])

        return lines

    def _build_filter_block(
        self,
        filters: List[FilterCandidate],
        conditions: List[str],
    ) -> List[str]:
        """필터 블록 코드 생성.

        Args:
            filters: 적용할 필터 목록
            conditions: 필터 조건식 목록

        Returns:
            필터 블록 코드 라인 리스트
        """
        lines = [
            self.FILTER_MARKER_START,
            f"# 적용 필터 수: {len(filters)}",
            "",
        ]

        for i, (f, cond) in enumerate(zip(filters, conditions)):
            # 필터 설명 주석
            lines.append(f"# [{i+1}] {f.description} (영향도: {f.expected_impact:.2f})")

            # NOT 조건으로 변환 (조건 불만족 시 매수 차단)
            # 조건이 이미 부정형이면 그대로, 아니면 not으로 감싸기
            if cond.strip().startswith('not ') or cond.strip().startswith('(not '):
                # 이미 부정형: (not (X > Y)) 형태 → 매수 차단 조건으로 사용
                block_condition = cond
            else:
                # 긍정형: (X > Y) 형태 → 불만족 시 차단 = not (X > Y)
                block_condition = f"not ({cond})"

            lines.extend([
                f"if {block_condition}:",
                "    매수 = False",
                "",
            ])

        lines.append(self.FILTER_MARKER_END)

        return lines

    def _inject_filter_block(
        self,
        buystg: str,
        preamble: List[str],
        filter_block: List[str],
    ) -> str:
        """필터 블록을 조건식에 삽입.

        "if 매수:" 라인 앞에 필터 블록을 삽입합니다.

        Args:
            buystg: 기존 조건식
            preamble: preamble 코드 라인
            filter_block: 필터 블록 코드 라인

        Returns:
            필터가 삽입된 새 조건식
        """
        lines = buystg.split('\n')
        result_lines = []

        # "if 매수:" 패턴 찾기
        buy_pattern = re.compile(r'^(\s*)if\s+매수\s*:')
        inserted = False

        for line in lines:
            match = buy_pattern.match(line)
            if match and not inserted:
                indent = match.group(1) or ''

                # preamble 삽입
                if preamble:
                    result_lines.append("")
                    for pl in preamble:
                        result_lines.append(indent + pl if pl.strip() else pl)

                # 필터 블록 삽입
                result_lines.append("")
                for fl in filter_block:
                    result_lines.append(indent + fl if fl.strip() else fl)
                result_lines.append("")

                inserted = True

            result_lines.append(line)

        # "if 매수:" 를 못 찾은 경우 맨 끝에 추가
        if not inserted:
            if preamble:
                result_lines.extend(preamble)
            result_lines.extend(filter_block)

        return '\n'.join(result_lines)

    def _validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """전체 조건식 문법 검증.

        Args:
            code: 검증할 코드

        Returns:
            (유효 여부, 에러 메시지)
        """
        try:
            compile(code, '<string>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, f"라인 {e.lineno}: {e.msg}"

    def build_single_condition(
        self,
        column: str,
        operator: str,
        threshold: float,
    ) -> str:
        """단일 필터 조건식 생성.

        Args:
            column: 컬럼명 (예: '매수등락율')
            operator: 연산자 ('>', '<', '>=', '<=', '==', '!=')
            threshold: 임계값

        Returns:
            조건식 문자열 (예: "(매수등락율 >= 5.0)")
        """
        # 숫자 포맷팅
        if isinstance(threshold, float):
            if threshold == int(threshold):
                threshold_str = str(int(threshold))
            else:
                threshold_str = f"{threshold:.4f}".rstrip('0').rstrip('.')
        else:
            threshold_str = str(threshold)

        return f"({column} {operator} {threshold_str})"

    def combine_conditions(
        self,
        conditions: List[str],
        operator: str = 'and',
    ) -> str:
        """여러 조건식 결합.

        Args:
            conditions: 조건식 목록
            operator: 결합 연산자 ('and' 또는 'or')

        Returns:
            결합된 조건식
        """
        if not conditions:
            return "True"

        if len(conditions) == 1:
            return conditions[0]

        joiner = f" {operator} "
        return f"({joiner.join(conditions)})"

    def get_filter_summary(self, filters: List[FilterCandidate]) -> str:
        """필터 목록 요약 문자열 생성.

        Args:
            filters: 필터 목록

        Returns:
            요약 문자열
        """
        if not filters:
            return "적용된 필터 없음"

        lines = [f"적용된 필터 {len(filters)}개:"]
        for i, f in enumerate(filters):
            lines.append(f"  [{i+1}] {f.description}")
            lines.append(f"      조건: {f.condition}")
            lines.append(f"      영향도: {f.expected_impact:.2f}")

        return '\n'.join(lines)

    # ==================== Phase 3: Advanced Condition Building ====================

    def build_optimized_combinations(
        self,
        buystg: str,
        filters: List[FilterCandidate],
        strategy: str = 'greedy',
        max_combinations: int = 5,
    ) -> List[BuildResult]:
        """AND/OR 조합 최적화.

        Phase 3 Enhancement: greedy, exhaustive, genetic 전략 지원

        Args:
            buystg: 기존 매수 조건식
            filters: 적용할 필터 후보 목록
            strategy: 최적화 전략 ('greedy', 'exhaustive', 'genetic')
            max_combinations: 최대 조합 수

        Returns:
            빌드 결과 목록 (최적 조합순)
        """
        if not filters:
            return [self.build(buystg, [])]

        if strategy == 'greedy':
            return self._build_greedy_combinations(buystg, filters, max_combinations)
        elif strategy == 'exhaustive':
            return self._build_exhaustive_combinations(buystg, filters, max_combinations)
        elif strategy == 'genetic':
            return self._build_genetic_combinations(buystg, filters, max_combinations)
        else:
            # 기본: greedy
            return self._build_greedy_combinations(buystg, filters, max_combinations)

    def _build_greedy_combinations(
        self,
        buystg: str,
        filters: List[FilterCandidate],
        max_combinations: int,
    ) -> List[BuildResult]:
        """Greedy 방식 조합 생성.

        영향도 순으로 필터를 하나씩 추가하며 조합 생성

        Args:
            buystg: 기존 매수 조건식
            filters: 필터 목록
            max_combinations: 최대 조합 수

        Returns:
            빌드 결과 목록
        """
        results: List[BuildResult] = []

        # 영향도 순 정렬
        sorted_filters = sorted(filters, key=lambda x: x.expected_impact, reverse=True)

        # 점진적으로 필터 추가
        for i in range(1, min(len(sorted_filters) + 1, max_combinations + 1)):
            selected = sorted_filters[:i]

            # 충돌 검사
            conflicts = self._detect_filter_conflicts(selected)
            if conflicts:
                if self.config.verbose:
                    print(f"[ICOS Builder] 필터 충돌 감지: {conflicts}")
                continue

            result = self.build(buystg, selected)
            if result.success:
                result.metadata = {'strategy': 'greedy', 'filter_count': i}
                results.append(result)

        return results

    def _build_exhaustive_combinations(
        self,
        buystg: str,
        filters: List[FilterCandidate],
        max_combinations: int,
    ) -> List[BuildResult]:
        """Exhaustive 방식 조합 생성.

        모든 가능한 조합을 평가 (필터 수 제한 적용)

        Args:
            buystg: 기존 매수 조건식
            filters: 필터 목록
            max_combinations: 최대 조합 수

        Returns:
            빌드 결과 목록
        """
        from itertools import combinations

        results: List[BuildResult] = []

        # 최대 3개 필터로 조합 제한 (조합 폭발 방지)
        max_filter_count = min(3, len(filters))

        for size in range(1, max_filter_count + 1):
            for combo in combinations(filters, size):
                combo_list = list(combo)

                # 충돌 검사
                conflicts = self._detect_filter_conflicts(combo_list)
                if conflicts:
                    continue

                result = self.build(buystg, combo_list)
                if result.success:
                    # 조합 점수 계산
                    total_impact = sum(f.expected_impact for f in combo_list)
                    result.metadata = {
                        'strategy': 'exhaustive',
                        'filter_count': size,
                        'total_impact': total_impact,
                    }
                    results.append(result)

                if len(results) >= max_combinations * 2:
                    break

            if len(results) >= max_combinations * 2:
                break

        # 점수순 정렬 후 상위 반환
        results.sort(key=lambda x: x.metadata.get('total_impact', 0), reverse=True)
        return results[:max_combinations]

    def _build_genetic_combinations(
        self,
        buystg: str,
        filters: List[FilterCandidate],
        max_combinations: int,
    ) -> List[BuildResult]:
        """Genetic Algorithm 방식 조합 생성.

        유전 알고리즘으로 최적 조합 탐색

        Args:
            buystg: 기존 매수 조건식
            filters: 필터 목록
            max_combinations: 최대 조합 수

        Returns:
            빌드 결과 목록
        """
        import random

        if len(filters) <= 3:
            # 필터가 적으면 exhaustive로 대체
            return self._build_exhaustive_combinations(buystg, filters, max_combinations)

        # GA 파라미터
        population_size = min(20, len(filters) * 2)
        generations = 10
        mutation_rate = 0.2

        # 개체: 필터 인덱스의 바이너리 마스크
        def create_individual():
            # 1~3개 필터 선택
            count = random.randint(1, min(3, len(filters)))
            indices = random.sample(range(len(filters)), count)
            mask = [i in indices for i in range(len(filters))]
            return mask

        def evaluate(mask):
            selected = [f for i, f in enumerate(filters) if mask[i]]
            if not selected:
                return 0
            conflicts = self._detect_filter_conflicts(selected)
            if conflicts:
                return 0
            return sum(f.expected_impact for f in selected)

        def crossover(parent1, parent2):
            # 단순 교차
            point = random.randint(1, len(parent1) - 1)
            child = parent1[:point] + parent2[point:]
            return child

        def mutate(individual):
            individual = individual.copy()
            for i in range(len(individual)):
                if random.random() < mutation_rate:
                    individual[i] = not individual[i]
            return individual

        # 초기 개체군 생성
        population = [create_individual() for _ in range(population_size)]

        # 진화
        for _ in range(generations):
            # 평가
            scored = [(evaluate(ind), ind) for ind in population]
            scored.sort(key=lambda x: x[0], reverse=True)

            # 엘리트 선택
            elites = [ind for _, ind in scored[:population_size // 2]]

            # 다음 세대 생성
            new_population = elites.copy()
            while len(new_population) < population_size:
                parent1, parent2 = random.sample(elites, 2)
                child = crossover(parent1, parent2)
                child = mutate(child)
                new_population.append(child)

            population = new_population

        # 최종 평가
        final_scored = [(evaluate(ind), ind) for ind in population]
        final_scored.sort(key=lambda x: x[0], reverse=True)

        # 상위 조합으로 결과 생성
        results: List[BuildResult] = []
        seen_combinations = set()

        for score, mask in final_scored:
            if score <= 0:
                continue

            selected = [f for i, f in enumerate(filters) if mask[i]]
            combo_key = tuple(sorted(f.condition for f in selected))

            if combo_key in seen_combinations:
                continue
            seen_combinations.add(combo_key)

            result = self.build(buystg, selected)
            if result.success:
                result.metadata = {
                    'strategy': 'genetic',
                    'filter_count': len(selected),
                    'ga_score': score,
                }
                results.append(result)

            if len(results) >= max_combinations:
                break

        return results

    def _detect_filter_conflicts(
        self,
        filters: List[FilterCandidate],
    ) -> List[Tuple[int, int, str]]:
        """필터 충돌 감지.

        Phase 3 Enhancement: 상충되는 필터 조합 탐지

        Args:
            filters: 검사할 필터 목록

        Returns:
            충돌 목록: [(인덱스1, 인덱스2, 충돌유형), ...]
        """
        conflicts: List[Tuple[int, int, str]] = []

        for i in range(len(filters)):
            for j in range(i + 1, len(filters)):
                conflict_type = self._check_conflict(filters[i], filters[j])
                if conflict_type:
                    conflicts.append((i, j, conflict_type))

        return conflicts

    def _check_conflict(
        self,
        filter1: FilterCandidate,
        filter2: FilterCandidate,
    ) -> Optional[str]:
        """두 필터 간 충돌 검사.

        Args:
            filter1: 첫 번째 필터
            filter2: 두 번째 필터

        Returns:
            충돌 유형 (None이면 충돌 없음)
        """
        col1 = filter1.metadata.get('column', '')
        col2 = filter2.metadata.get('column', '')

        # 같은 컬럼에 대한 상반된 조건
        if col1 == col2 and col1:
            dir1 = filter1.metadata.get('direction', '')
            dir2 = filter2.metadata.get('direction', '')

            # 같은 컬럼에 대해 '미만' + '이상' 조건이 있으면 모든 값 제외 가능
            if (dir1 == 'below' and dir2 == 'above') or (dir1 == 'above' and dir2 == 'below'):
                th1 = filter1.metadata.get('threshold', 0)
                th2 = filter2.metadata.get('threshold', 0)

                # 범위 겹침 검사
                if dir1 == 'below' and dir2 == 'above':
                    # filter1: < th1, filter2: >= th2
                    if th1 <= th2:
                        return 'empty_range'  # 빈 범위
                elif dir1 == 'above' and dir2 == 'below':
                    # filter1: >= th1, filter2: < th2
                    if th2 <= th1:
                        return 'empty_range'

        # 시간대 필터 충돌 (너무 많은 시간대 제외)
        if col1 == '매수시' and col2 == '매수시':
            hour1 = filter1.metadata.get('hour')
            hour2 = filter2.metadata.get('hour')
            # 2개 이상의 시간대 제외는 경고 (충돌로 처리하지는 않음)
            pass

        return None

    def _auto_adjust_threshold(
        self,
        df_tsg,
        column: str,
        initial_threshold: float,
        direction: str,
        adjustment_range: float = 0.3,
        steps: int = 7,
    ) -> Tuple[float, float]:
        """임계값 자동 조정.

        Phase 3 Enhancement: ±30% 범위 내 최적 임계값 탐색

        Args:
            df_tsg: 거래 데이터 DataFrame
            column: 대상 컬럼
            initial_threshold: 초기 임계값
            direction: 조건 방향 ('below' 또는 'above')
            adjustment_range: 조정 범위 비율 (0.3 = ±30%)
            steps: 탐색 단계 수

        Returns:
            (최적 임계값, 예상 개선율)
        """
        import numpy as np
        import pandas as pd

        if df_tsg is None or column not in df_tsg.columns:
            return initial_threshold, 0.0

        loss_mask = df_tsg['수익금'] <= 0
        overall_loss_ratio = loss_mask.mean()

        if overall_loss_ratio == 0:
            return initial_threshold, 0.0

        # 탐색 범위 설정
        min_th = initial_threshold * (1 - adjustment_range)
        max_th = initial_threshold * (1 + adjustment_range)
        thresholds = np.linspace(min_th, max_th, steps)

        best_threshold = initial_threshold
        best_improvement = 0.0

        for th in thresholds:
            # 조건 적용
            if direction == 'below':
                # 미만 제외: >= th 만 허용
                mask = df_tsg[column] >= th
            else:
                # 이상 제외: < th 만 허용
                mask = df_tsg[column] < th

            remaining = mask.sum()
            if remaining < 10:  # 최소 샘플 수
                continue

            # 조건 적용 후 손실률
            remaining_losses = (mask & loss_mask).sum()
            new_loss_ratio = remaining_losses / remaining if remaining > 0 else 0

            # 개선율 계산
            improvement = (overall_loss_ratio - new_loss_ratio) / overall_loss_ratio if overall_loss_ratio > 0 else 0

            # 제외율 패널티 (너무 많이 제외하면 패널티)
            exclusion_rate = 1 - (remaining / len(df_tsg))
            penalized_improvement = improvement * (1 - exclusion_rate * 0.5)

            if penalized_improvement > best_improvement:
                best_improvement = penalized_improvement
                best_threshold = th

        return best_threshold, best_improvement

    def build_with_or_conditions(
        self,
        buystg: str,
        filter_groups: List[List[FilterCandidate]],
    ) -> BuildResult:
        """OR 조건을 포함한 빌드.

        Phase 3 Enhancement: 필터 그룹을 OR로 연결

        Args:
            buystg: 기존 매수 조건식
            filter_groups: 필터 그룹 목록 (각 그룹 내는 AND, 그룹 간은 OR)

        Returns:
            빌드 결과
        """
        if not filter_groups:
            return self.build(buystg, [])

        # 각 그룹의 조건을 AND로 결합
        group_conditions = []
        all_filters: List[FilterCandidate] = []

        for group in filter_groups:
            if not group:
                continue

            conditions = [f.condition for f in group]
            combined = self.combine_conditions(conditions, 'and')
            group_conditions.append(combined)
            all_filters.extend(group)

        if not group_conditions:
            return self.build(buystg, [])

        # 그룹들을 OR로 결합
        final_condition = self.combine_conditions(group_conditions, 'or')

        # 결합된 조건으로 단일 FilterCandidate 생성
        combined_filter = FilterCandidate(
            condition=final_condition,
            description=f"OR 조합: {len(filter_groups)}개 그룹",
            source="or_combination",
            expected_impact=max(f.expected_impact for f in all_filters) if all_filters else 0,
            metadata={
                'group_count': len(filter_groups),
                'total_filters': len(all_filters),
            },
        )

        return self.build(buystg, [combined_filter])

    def refine_filter_threshold(
        self,
        filter_candidate: FilterCandidate,
        df_tsg,
    ) -> FilterCandidate:
        """필터 임계값 정제.

        Phase 3 Enhancement: 데이터 기반 임계값 최적화

        Args:
            filter_candidate: 정제할 필터
            df_tsg: 거래 데이터 DataFrame

        Returns:
            정제된 FilterCandidate
        """
        threshold = filter_candidate.metadata.get('threshold')
        column = filter_candidate.metadata.get('column')
        direction = filter_candidate.metadata.get('direction')

        if threshold is None or column is None or direction is None:
            return filter_candidate

        # 최적 임계값 탐색
        optimal_threshold, improvement = self._auto_adjust_threshold(
            df_tsg, column, threshold, direction
        )

        # 개선이 있는 경우에만 업데이트
        if improvement > 0.05:  # 5% 이상 개선
            # 새 조건 생성
            if direction == 'below':
                new_condition = f"({column} >= {optimal_threshold:.4f})"
            else:
                new_condition = f"({column} < {optimal_threshold:.4f})"

            return FilterCandidate(
                condition=new_condition,
                description=f"{filter_candidate.description} (임계값 조정: {threshold:.2f} → {optimal_threshold:.2f})",
                source=filter_candidate.source,
                expected_impact=filter_candidate.expected_impact * (1 + improvement),
                metadata={
                    **filter_candidate.metadata,
                    'original_threshold': threshold,
                    'optimized_threshold': optimal_threshold,
                    'threshold_improvement': improvement,
                },
            )

        return filter_candidate

    # ==================== End Phase 3: Advanced Condition Building ====================
