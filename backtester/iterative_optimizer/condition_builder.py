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
        # 호가 데이터
        '매도호가1', '매도호가2', '매도호가3', '매도호가4', '매도호가5',
        '매수호가1', '매수호가2', '매수호가3', '매수호가4', '매수호가5',
        '매도잔량1', '매도잔량2', '매도잔량3', '매도잔량4', '매도잔량5',
        '매수잔량1', '매수잔량2', '매수잔량3', '매수잔량4', '매수잔량5',
        # 틱 모드 변수
        '초당매수수량', '초당매도수량', '초당매도_매수_비율',
        # 분봉 모드 변수
        '분당매수수량', '분당매도수량', '분당매도_매수_비율',
        # 매수 시점 스냅샷
        '매수등락율', '매수체결강도', '매수당일거래대금',
        '매수초당매수수량', '매수초당매도수량',
        '매수분당매수수량', '매수분당매도수량',
        # 파생 점수
        '거래품질점수', '위험도점수',
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
