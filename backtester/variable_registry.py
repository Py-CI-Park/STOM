# -*- coding: utf-8 -*-
"""
백테스팅 변수 통합 레지스트리

모든 변수(원본, 파생, 필터용)를 하나의 파일에서 관리합니다.
새 변수 추가 시 이 파일만 수정하면 됩니다.

참조 문서: docs/Guideline/Variable_Management_Guide.md

버전: 1.0.0
작성일: 2026-01-07
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Literal


class VariableScope(Enum):
    """변수 시점 분류"""
    BUY = 'buy'           # 매수 시점
    SELL = 'sell'         # 매도 시점
    COMBINED = 'combined' # 매수+매도 조합
    ANALYSIS = 'analysis' # 분석 전용


class VariableTimeframe(Enum):
    """타임프레임 분류"""
    TICK = 'tick'   # Tick 전용
    MIN = 'min'     # Min 전용
    ALL = 'all'     # 공통


@dataclass
class VariableDefinition:
    """
    변수 정의 데이터클래스
    
    Attributes:
        name: 변수명
        display_name: 표시용 이름 (한글)
        scope: 시점 분류 (BUY/SELL/COMBINED/ANALYSIS)
        timeframe: 타임프레임 (TICK/MIN/ALL)
        unit: 단위 (%, 원, 점수 등)
        category: 카테고리 (등락율, 체결강도, 호가 등)
        formula: 산출 공식 (리스트)
        for_filter: 필터 후보 사용 가능 여부
        for_segment_filter: 세그먼트 필터 사용 가능 여부
        runtime_compatible: 런타임 계산 가능 여부
        lookahead_free: 룩어헤드 없음 여부
        source_columns: 의존 컬럼 목록
        description: 설명
    """
    name: str
    display_name: str
    scope: VariableScope
    timeframe: VariableTimeframe
    unit: str
    category: str
    formula: List[str] = field(default_factory=list)
    for_filter: bool = True
    for_segment_filter: bool = True
    runtime_compatible: bool = True
    lookahead_free: bool = True
    source_columns: List[str] = field(default_factory=list)
    description: str = ''


# =============================================================================
# 변수 레지스트리 정의
# =============================================================================

VARIABLE_REGISTRY: Dict[str, VariableDefinition] = {}


def _register(var: VariableDefinition) -> None:
    """변수를 레지스트리에 등록합니다."""
    VARIABLE_REGISTRY[var.name] = var


# -----------------------------------------------------------------------------
# 1. 매수 시점 원본 변수 (30개)
# -----------------------------------------------------------------------------

# 가격/금액
_register(VariableDefinition(
    name='매수가',
    display_name='매수가',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='원',
    category='가격',
    formula=['원본 데이터'],
    description='매수 체결가',
))

_register(VariableDefinition(
    name='매수금액',
    display_name='매수금액',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='원',
    category='가격',
    formula=['원본 데이터'],
    for_filter=False,  # 분석용
    for_segment_filter=False,
    description='매수 총금액 (분석용)',
))

# 시장 지표
_register(VariableDefinition(
    name='매수등락율',
    display_name='매수등락율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='등락율',
    formula=['원본 데이터'],
    description='매수 시점 등락율',
))

_register(VariableDefinition(
    name='매수시가등락율',
    display_name='매수시가등락율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='등락율',
    formula=['원본 데이터'],
    description='시가 대비 등락율',
))

_register(VariableDefinition(
    name='매수체결강도',
    display_name='매수체결강도',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='-',
    category='체결강도',
    formula=['원본 데이터'],
    description='매수 시점 체결강도',
))

_register(VariableDefinition(
    name='매수당일거래대금',
    display_name='매수당일거래대금',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='백만원',
    category='거래대금',
    formula=['원본 데이터'],
    description='당일 거래대금 (단위: 백만원)',
))

_register(VariableDefinition(
    name='매수전일비',
    display_name='매수전일비',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='전일비',
    formula=['원본 데이터'],
    description='전일 종가 대비',
))

_register(VariableDefinition(
    name='매수회전율',
    display_name='매수회전율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='회전율',
    formula=['원본 데이터'],
    description='시장 회전율',
))

_register(VariableDefinition(
    name='매수전일동시간비',
    display_name='매수전일동시간비',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='전일비',
    formula=['원본 데이터'],
    description='전일 동시간 대비',
))

# 가격 범위
_register(VariableDefinition(
    name='매수고가',
    display_name='매수고가',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='원',
    category='가격',
    formula=['원본 데이터'],
    description='당일 고가',
))

_register(VariableDefinition(
    name='매수저가',
    display_name='매수저가',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='원',
    category='가격',
    formula=['원본 데이터'],
    description='당일 저가',
))

_register(VariableDefinition(
    name='매수고저평균대비등락율',
    display_name='매수고저평균대비등락율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='등락율',
    formula=['원본 데이터'],
    description='고저 평균 대비',
))

# 호가 데이터
_register(VariableDefinition(
    name='매수매도총잔량',
    display_name='매수매도총잔량',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='주',
    category='호가',
    formula=['원본 데이터'],
    description='매도 호가 총잔량',
))

_register(VariableDefinition(
    name='매수매수총잔량',
    display_name='매수매수총잔량',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='주',
    category='호가',
    formula=['원본 데이터'],
    description='매수 호가 총잔량',
))

_register(VariableDefinition(
    name='매수호가잔량비',
    display_name='매수호가잔량비',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='호가',
    formula=['원본 데이터'],
    description='매수/매도 잔량 비율',
))

_register(VariableDefinition(
    name='매수매도호가1',
    display_name='매수매도호가1',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='원',
    category='호가',
    formula=['원본 데이터'],
    description='매도1호가',
))

_register(VariableDefinition(
    name='매수매수호가1',
    display_name='매수매수호가1',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='원',
    category='호가',
    formula=['원본 데이터'],
    description='매수1호가',
))

_register(VariableDefinition(
    name='매수스프레드',
    display_name='매수스프레드',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='스프레드',
    formula=['원본 데이터'],
    description='호가 스프레드',
))

# 수급 - Tick 전용
_register(VariableDefinition(
    name='매수초당매수수량',
    display_name='매수초당매수수량',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='주',
    category='수급',
    formula=['원본 데이터'],
    description='초당 매수 체결량',
))

_register(VariableDefinition(
    name='매수초당매도수량',
    display_name='매수초당매도수량',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='주',
    category='수급',
    formula=['원본 데이터'],
    description='초당 매도 체결량',
))

_register(VariableDefinition(
    name='매수초당거래대금',
    display_name='매수초당거래대금',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='백만원',
    category='수급',
    formula=['원본 데이터'],
    description='초당 거래대금',
))

# 수급 - Min 전용
_register(VariableDefinition(
    name='매수분당매수수량',
    display_name='매수분당매수수량',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='주',
    category='수급',
    formula=['원본 데이터'],
    description='분당 매수 체결량',
))

_register(VariableDefinition(
    name='매수분당매도수량',
    display_name='매수분당매도수량',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='주',
    category='수급',
    formula=['원본 데이터'],
    description='분당 매도 체결량',
))

_register(VariableDefinition(
    name='매수분당거래대금',
    display_name='매수분당거래대금',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='백만원',
    category='수급',
    formula=['원본 데이터'],
    description='분당 거래대금',
))

# 기타
_register(VariableDefinition(
    name='시가총액',
    display_name='시가총액',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='억원',
    category='시가총액',
    formula=['원본 데이터'],
    description='종목 시가총액',
))

_register(VariableDefinition(
    name='매수시',
    display_name='매수시',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='-',
    category='시간',
    formula=['원본 데이터'],
    for_filter=False,  # 시간대 필터는 별도 처리
    for_segment_filter=True,
    description='매수 시각 (시)',
))

_register(VariableDefinition(
    name='매수분',
    display_name='매수분',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='-',
    category='시간',
    formula=['원본 데이터'],
    for_filter=False,
    for_segment_filter=True,
    description='매수 시각 (분)',
))

_register(VariableDefinition(
    name='매수초',
    display_name='매수초',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='-',
    category='시간',
    formula=['원본 데이터'],
    for_filter=False,
    for_segment_filter=True,
    description='매수 시각 (초)',
))


# -----------------------------------------------------------------------------
# 2. 매도 시점 원본 변수 (룩어헤드 포함)
# -----------------------------------------------------------------------------

_register(VariableDefinition(
    name='매도등락율',
    display_name='매도등락율',
    scope=VariableScope.SELL,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='등락율',
    formula=['원본 데이터'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='매도 시점 등락율 (룩어헤드)',
))

_register(VariableDefinition(
    name='매도체결강도',
    display_name='매도체결강도',
    scope=VariableScope.SELL,
    timeframe=VariableTimeframe.ALL,
    unit='-',
    category='체결강도',
    formula=['원본 데이터'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='매도 시점 체결강도 (룩어헤드)',
))

_register(VariableDefinition(
    name='매도당일거래대금',
    display_name='매도당일거래대금',
    scope=VariableScope.SELL,
    timeframe=VariableTimeframe.ALL,
    unit='백만원',
    category='거래대금',
    formula=['원본 데이터'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='매도 시점 당일거래대금 (룩어헤드)',
))

_register(VariableDefinition(
    name='보유시간',
    display_name='보유시간',
    scope=VariableScope.SELL,
    timeframe=VariableTimeframe.ALL,
    unit='초/분',
    category='시간',
    formula=['원본 데이터'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='보유 기간 (룩어헤드)',
))

_register(VariableDefinition(
    name='수익금',
    display_name='수익금',
    scope=VariableScope.SELL,
    timeframe=VariableTimeframe.ALL,
    unit='원',
    category='결과',
    formula=['원본 데이터'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='실현 손익 (룩어헤드)',
))

_register(VariableDefinition(
    name='수익률',
    display_name='수익률',
    scope=VariableScope.SELL,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='결과',
    formula=['원본 데이터'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='실현 수익률 (룩어헤드)',
))


# -----------------------------------------------------------------------------
# 3. 파생 변수 - 점수 지표 (매수 시점, 필터 사용 가능)
# -----------------------------------------------------------------------------

_register(VariableDefinition(
    name='모멘텀점수',
    display_name='모멘텀점수',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='점수(-30~+30)',
    category='모멘텀',
    formula=[
        '등락율_norm = 매수등락율 / 10',
        '체결강도_norm = (매수체결강도 - 100) / 50',
        '모멘텀점수 = (등락율_norm*0.4 + 체결강도_norm*0.6) * 10',
    ],
    source_columns=['매수등락율', '매수체결강도'],
    description='등락율과 체결강도 기반 모멘텀 강도',
))

_register(VariableDefinition(
    name='거래품질점수',
    display_name='거래품질점수',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='점수(0~100)',
    category='품질',
    formula=[
        '기본 50점에서 체결강도/호가잔량/시가총액 가산',
        '매수등락율/매수스프레드 조건 감산',
    ],
    source_columns=['매수체결강도', '매수호가잔량비', '시가총액', '매수등락율', '매수스프레드'],
    description='체결강도, 호가잔량비, 시가총액 등 종합 평가',
))

_register(VariableDefinition(
    name='위험도점수',
    display_name='위험도점수',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='점수(0~100)',
    category='위험신호',
    formula=[
        '매수등락율 기반 가산 (>=20: +20, >=25: +10, >=30: +10)',
        '매수체결강도 기반 가산/감산',
        '매수당일거래대금 기반 가산',
        '시가총액 기반 가산',
        '매수호가잔량비 기반 가산',
        '매수스프레드 기반 가산',
        '매수회전율 기반 가산',
        '매수변동폭비율 기반 가산',
        'clip(0, 100)',
    ],
    source_columns=['매수등락율', '매수체결강도', '매수당일거래대금', '시가총액',
                   '매수호가잔량비', '매수스프레드', '매수회전율', '매수변동폭비율'],
    description='매수 시점 종합 위험도 점수 (룩어헤드 없음)',
))


# -----------------------------------------------------------------------------
# 4. 파생 변수 - 변동폭 (매수 시점, 필터 사용 가능)
# -----------------------------------------------------------------------------

_register(VariableDefinition(
    name='매수변동폭',
    display_name='매수변동폭',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='원',
    category='변동성',
    formula=['매수변동폭 = 매수고가 - 매수저가'],
    source_columns=['매수고가', '매수저가'],
    description='당일 고저 가격 차이',
))

_register(VariableDefinition(
    name='매수변동폭비율',
    display_name='매수변동폭비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='변동성',
    formula=['매수변동폭비율 = (매수고가-매수저가)/매수저가*100'],
    source_columns=['매수고가', '매수저가'],
    description='저가 대비 변동폭 비율',
))


# -----------------------------------------------------------------------------
# 5. 파생 변수 - 수급 비율 (Tick 전용, 필터 사용 가능)
# -----------------------------------------------------------------------------

_register(VariableDefinition(
    name='초당매수수량_매도총잔량_비율',
    display_name='초당매수수량_매도총잔량_비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='%',
    category='수급',
    formula=['초당매수수량_매도총잔량_비율 = 매수초당매수수량 / 매수매도총잔량 * 100'],
    source_columns=['매수초당매수수량', '매수매도총잔량'],
    description='초당 매수 수량의 매도 잔량 대비 비율',
))

_register(VariableDefinition(
    name='매도잔량_매수잔량_비율',
    display_name='매도잔량_매수잔량_비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='배율',
    category='호가',
    formula=['매도잔량_매수잔량_비율 = 매수매도총잔량 / 매수매수총잔량'],
    source_columns=['매수매도총잔량', '매수매수총잔량'],
    description='호가 불균형 - 매도 우위',
))

_register(VariableDefinition(
    name='매수잔량_매도잔량_비율',
    display_name='매수잔량_매도잔량_비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='배율',
    category='호가',
    formula=['매수잔량_매도잔량_비율 = 매수매수총잔량 / 매수매도총잔량'],
    source_columns=['매수매수총잔량', '매수매도총잔량'],
    description='호가 불균형 - 매수 우위',
))

_register(VariableDefinition(
    name='초당매도_매수_비율',
    display_name='초당매도_매수_비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='배율',
    category='수급',
    formula=['초당매도_매수_비율 = 매수초당매도수량 / 매수초당매수수량'],
    source_columns=['매수초당매도수량', '매수초당매수수량'],
    description='매도 압력',
))

_register(VariableDefinition(
    name='초당매수_매도_비율',
    display_name='초당매수_매도_비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='배율',
    category='수급',
    formula=['초당매수_매도_비율 = 매수초당매수수량 / 매수초당매도수량'],
    source_columns=['매수초당매수수량', '매수초당매도수량'],
    description='매수 압력',
))

_register(VariableDefinition(
    name='현재가_고저범위_위치',
    display_name='현재가_고저범위_위치',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='%',
    category='가격',
    formula=['현재가_고저범위_위치 = (매수가-매수저가)/(매수고가-매수저가)*100'],
    source_columns=['매수가', '매수고가', '매수저가'],
    description='당일 고저 범위 내 현재가 위치',
))

_register(VariableDefinition(
    name='초당거래대금_당일비중',
    display_name='초당거래대금_당일비중',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='만분율',
    category='수급',
    formula=['초당거래대금_당일비중 = 매수초당거래대금/매수당일거래대금*10000'],
    source_columns=['매수초당거래대금', '매수당일거래대금'],
    description='초당 거래대금의 당일 거래대금 대비 비중',
))

_register(VariableDefinition(
    name='초당순매수수량',
    display_name='초당순매수수량',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='수량',
    category='수급',
    formula=['초당순매수수량 = 매수초당매수수량 - 매수초당매도수량'],
    source_columns=['매수초당매수수량', '매수초당매도수량'],
    description='초당 순매수 수량',
))

_register(VariableDefinition(
    name='초당순매수금액',
    display_name='초당순매수금액',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='백만원',
    category='수급',
    formula=['초당순매수금액 = 초당순매수수량 * 매수가 / 1_000_000'],
    source_columns=['초당순매수수량', '매수가'],
    description='초당 순매수 금액',
))

_register(VariableDefinition(
    name='초당순매수비율',
    display_name='초당순매수비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.TICK,
    unit='%',
    category='수급',
    formula=['초당순매수비율 = 매수초당매수수량 / (매수초당매수수량+매수초당매도수량) * 100'],
    source_columns=['매수초당매수수량', '매수초당매도수량'],
    description='초당 순매수 비율',
))


# -----------------------------------------------------------------------------
# 6. 파생 변수 - 수급 비율 (Min 전용, 필터 사용 가능)
# -----------------------------------------------------------------------------

_register(VariableDefinition(
    name='분당매수수량_매도총잔량_비율',
    display_name='분당매수수량_매도총잔량_비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='%',
    category='수급',
    formula=['분당매수수량_매도총잔량_비율 = 매수분당매수수량 / 매수매도총잔량 * 100'],
    source_columns=['매수분당매수수량', '매수매도총잔량'],
    description='분당 매수 수량의 매도 잔량 대비 비율',
))

_register(VariableDefinition(
    name='분당매도_매수_비율',
    display_name='분당매도_매수_비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='배율',
    category='수급',
    formula=['분당매도_매수_비율 = 매수분당매도수량 / 매수분당매수수량'],
    source_columns=['매수분당매도수량', '매수분당매수수량'],
    description='분당 매도 압력',
))

_register(VariableDefinition(
    name='분당매수_매도_비율',
    display_name='분당매수_매도_비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='배율',
    category='수급',
    formula=['분당매수_매도_비율 = 매수분당매수수량 / 매수분당매도수량'],
    source_columns=['매수분당매수수량', '매수분당매도수량'],
    description='분당 매수 압력',
))

_register(VariableDefinition(
    name='현재가_분봉고저범위_위치',
    display_name='현재가_분봉고저범위_위치',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='%',
    category='가격',
    formula=['현재가_분봉고저범위_위치 = (매수가-분봉저가)/(분봉고가-분봉저가)*100'],
    source_columns=['매수가', '매수분봉고가', '매수분봉저가'],
    description='분봉 고저 범위 내 현재가 위치',
))

_register(VariableDefinition(
    name='분당거래대금_당일비중',
    display_name='분당거래대금_당일비중',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='만분율',
    category='수급',
    formula=['분당거래대금_당일비중 = 매수분당거래대금/매수당일거래대금*10000'],
    source_columns=['매수분당거래대금', '매수당일거래대금'],
    description='분당 거래대금의 당일 거래대금 대비 비중',
))

_register(VariableDefinition(
    name='분당순매수수량',
    display_name='분당순매수수량',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='수량',
    category='수급',
    formula=['분당순매수수량 = 매수분당매수수량 - 매수분당매도수량'],
    source_columns=['매수분당매수수량', '매수분당매도수량'],
    description='분당 순매수 수량',
))

_register(VariableDefinition(
    name='분당순매수금액',
    display_name='분당순매수금액',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='백만원',
    category='수급',
    formula=['분당순매수금액 = 분당순매수수량 * 매수가 / 1_000_000'],
    source_columns=['분당순매수수량', '매수가'],
    description='분당 순매수 금액',
))

_register(VariableDefinition(
    name='분당순매수비율',
    display_name='분당순매수비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.MIN,
    unit='%',
    category='수급',
    formula=['분당순매수비율 = 매수분당매수수량 / (매수분당매수수량+매수분당매도수량) * 100'],
    source_columns=['매수분당매수수량', '매수분당매도수량'],
    description='분당 순매수 비율',
))


# -----------------------------------------------------------------------------
# 7. 파생 변수 - 당일거래대금 비율 (필터 사용 가능)
# -----------------------------------------------------------------------------

_register(VariableDefinition(
    name='당일거래대금_전틱분봉_비율',
    display_name='당일거래대금_전틱분봉_비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='배율',
    category='거래대금',
    formula=['당일거래대금_전틱분봉_비율 = 현재 당일거래대금 / 직전 당일거래대금'],
    source_columns=['매수당일거래대금'],
    description='직전 틱/분봉 대비 당일거래대금 비율',
))

_register(VariableDefinition(
    name='당일거래대금_5틱분봉평균_비율',
    display_name='당일거래대금_5틱분봉평균_비율',
    scope=VariableScope.BUY,
    timeframe=VariableTimeframe.ALL,
    unit='배율',
    category='거래대금',
    formula=['당일거래대금_5틱분봉평균_비율 = 현재 당일거래대금 / 최근 5틱/분봉 평균'],
    source_columns=['매수당일거래대금'],
    description='최근 5틱/분봉 평균 대비 당일거래대금 비율',
))


# -----------------------------------------------------------------------------
# 8. 파생 변수 - 변화량/변화율 (룩어헤드 포함, 필터 사용 불가)
# -----------------------------------------------------------------------------

_register(VariableDefinition(
    name='등락율변화',
    display_name='등락율변화',
    scope=VariableScope.COMBINED,
    timeframe=VariableTimeframe.ALL,
    unit='%p',
    category='변화량',
    formula=['등락율변화 = 매도등락율 - 매수등락율'],
    source_columns=['매도등락율', '매수등락율'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='매도-매수 등락율 변화량 (사후 진단용)',
))

_register(VariableDefinition(
    name='체결강도변화',
    display_name='체결강도변화',
    scope=VariableScope.COMBINED,
    timeframe=VariableTimeframe.ALL,
    unit='-',
    category='변화량',
    formula=['체결강도변화 = 매도체결강도 - 매수체결강도'],
    source_columns=['매도체결강도', '매수체결강도'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='매도-매수 체결강도 변화량 (사후 진단용)',
))

_register(VariableDefinition(
    name='거래대금변화율',
    display_name='거래대금변화율',
    scope=VariableScope.COMBINED,
    timeframe=VariableTimeframe.ALL,
    unit='배율',
    category='변화율',
    formula=['거래대금변화율 = 매도당일거래대금 / 매수당일거래대금'],
    source_columns=['매도당일거래대금', '매수당일거래대금'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='매도/매수 거래대금 비율 (사후 진단용)',
))

_register(VariableDefinition(
    name='당일거래대금_매수매도_비율',
    display_name='당일거래대금_매수매도_비율',
    scope=VariableScope.COMBINED,
    timeframe=VariableTimeframe.ALL,
    unit='배율',
    category='변화율',
    formula=['당일거래대금_매수매도_비율 = 매도당일거래대금 / 매수당일거래대금'],
    source_columns=['매도당일거래대금', '매수당일거래대금'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='매도/매수 당일거래대금 비율 (사후 진단용)',
))


# -----------------------------------------------------------------------------
# 9. 파생 변수 - 진단용 지표 (룩어헤드 포함, 필터 사용 불가)
# -----------------------------------------------------------------------------

_register(VariableDefinition(
    name='매수매도위험도점수',
    display_name='매수매도위험도점수',
    scope=VariableScope.COMBINED,
    timeframe=VariableTimeframe.ALL,
    unit='점수(0~100)',
    category='위험신호',
    formula=['매수→매도 변화량 기반 위험도 점수'],
    source_columns=['등락율변화', '체결강도변화', '호가잔량비변화', '거래대금변화율'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='매수-매도 변화 기반 위험도 (사후 진단용)',
))

_register(VariableDefinition(
    name='시간대평균수익률',
    display_name='시간대평균수익률',
    scope=VariableScope.ANALYSIS,
    timeframe=VariableTimeframe.ALL,
    unit='%',
    category='분석',
    formula=['시간대별 평균 수익률'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='시간대별 평균 수익률 (사후 진단용)',
))

_register(VariableDefinition(
    name='타이밍점수',
    display_name='타이밍점수',
    scope=VariableScope.ANALYSIS,
    timeframe=VariableTimeframe.ALL,
    unit='-',
    category='분석',
    formula=['시간대 타이밍 점수'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='시간대 타이밍 점수 (사후 진단용)',
))

_register(VariableDefinition(
    name='리스크조정수익률',
    display_name='리스크조정수익률',
    scope=VariableScope.ANALYSIS,
    timeframe=VariableTimeframe.ALL,
    unit='-',
    category='분석',
    formula=['수익률 / 위험 요소'],
    for_filter=False,
    for_segment_filter=False,
    lookahead_free=False,
    description='리스크 조정 수익률 (사후 진단용)',
))


# =============================================================================
# 레지스트리 유틸리티 클래스
# =============================================================================

class VariableRegistry:
    """변수 레지스트리 관리 클래스"""
    
    def __init__(self, definitions: Dict[str, VariableDefinition] = None):
        self.definitions = definitions or VARIABLE_REGISTRY
    
    def get(self, name: str) -> Optional[VariableDefinition]:
        """변수 정의를 반환합니다."""
        return self.definitions.get(name)
    
    def get_all(self) -> Dict[str, VariableDefinition]:
        """모든 변수 정의를 반환합니다."""
        return self.definitions.copy()
    
    def get_filter_candidates(self, timeframe: str = 'tick') -> List[str]:
        """
        필터 후보 변수 목록을 반환합니다.
        
        Args:
            timeframe: 'tick' 또는 'min'
            
        Returns:
            필터 사용 가능한 변수명 리스트
        """
        tf = VariableTimeframe.TICK if timeframe == 'tick' else VariableTimeframe.MIN
        return [
            name for name, defn in self.definitions.items()
            if defn.for_filter 
               and defn.lookahead_free
               and defn.timeframe in (tf, VariableTimeframe.ALL)
        ]
    
    def get_segment_filter_candidates(self, timeframe: str = 'tick') -> List[str]:
        """
        세그먼트 필터 후보 변수 목록을 반환합니다.
        
        Args:
            timeframe: 'tick' 또는 'min'
            
        Returns:
            세그먼트 필터 사용 가능한 변수명 리스트
        """
        tf = VariableTimeframe.TICK if timeframe == 'tick' else VariableTimeframe.MIN
        return [
            name for name, defn in self.definitions.items()
            if defn.for_segment_filter 
               and defn.lookahead_free
               and defn.runtime_compatible
               and defn.timeframe in (tf, VariableTimeframe.ALL)
        ]
    
    def get_by_category(self, category: str) -> List[str]:
        """
        카테고리별 변수 목록을 반환합니다.
        
        Args:
            category: 카테고리명 (등락율, 체결강도, 호가 등)
            
        Returns:
            해당 카테고리의 변수명 리스트
        """
        return [
            name for name, defn in self.definitions.items()
            if defn.category == category
        ]
    
    def get_by_scope(self, scope: VariableScope) -> List[str]:
        """
        시점별 변수 목록을 반환합니다.
        
        Args:
            scope: VariableScope (BUY, SELL, COMBINED, ANALYSIS)
            
        Returns:
            해당 시점의 변수명 리스트
        """
        return [
            name for name, defn in self.definitions.items()
            if defn.scope == scope
        ]
    
    def get_by_timeframe(self, timeframe: VariableTimeframe) -> List[str]:
        """
        타임프레임별 변수 목록을 반환합니다.
        
        Args:
            timeframe: VariableTimeframe (TICK, MIN, ALL)
            
        Returns:
            해당 타임프레임의 변수명 리스트
        """
        return [
            name for name, defn in self.definitions.items()
            if defn.timeframe == timeframe
        ]
    
    def is_lookahead_free(self, name: str) -> bool:
        """
        변수가 룩어헤드 없는지 확인합니다.
        
        Args:
            name: 변수명
            
        Returns:
            룩어헤드 없으면 True
        """
        defn = self.definitions.get(name)
        return defn.lookahead_free if defn else False
    
    def get_formula(self, name: str) -> List[str]:
        """
        변수 산출 공식을 반환합니다.
        
        Args:
            name: 변수명
            
        Returns:
            산출 공식 리스트
        """
        defn = self.definitions.get(name)
        return defn.formula if defn else []
    
    def get_source_columns(self, name: str) -> List[str]:
        """
        변수 의존 컬럼을 반환합니다.
        
        Args:
            name: 변수명
            
        Returns:
            의존 컬럼 리스트
        """
        defn = self.definitions.get(name)
        return defn.source_columns if defn else []
    
    def get_categories(self) -> List[str]:
        """
        모든 카테고리 목록을 반환합니다.
        
        Returns:
            카테고리명 리스트 (중복 제거)
        """
        return sorted(list(set(defn.category for defn in self.definitions.values())))
    
    def summary(self) -> Dict:
        """
        레지스트리 요약 정보를 반환합니다.
        
        Returns:
            요약 정보 딕셔너리
        """
        total = len(self.definitions)
        buy_vars = len([d for d in self.definitions.values() if d.scope == VariableScope.BUY])
        sell_vars = len([d for d in self.definitions.values() if d.scope == VariableScope.SELL])
        combined_vars = len([d for d in self.definitions.values() if d.scope == VariableScope.COMBINED])
        analysis_vars = len([d for d in self.definitions.values() if d.scope == VariableScope.ANALYSIS])
        
        filter_candidates = len([d for d in self.definitions.values() if d.for_filter and d.lookahead_free])
        segment_filter_candidates = len([d for d in self.definitions.values() if d.for_segment_filter and d.lookahead_free])
        lookahead_vars = len([d for d in self.definitions.values() if not d.lookahead_free])
        
        tick_vars = len([d for d in self.definitions.values() if d.timeframe == VariableTimeframe.TICK])
        min_vars = len([d for d in self.definitions.values() if d.timeframe == VariableTimeframe.MIN])
        common_vars = len([d for d in self.definitions.values() if d.timeframe == VariableTimeframe.ALL])
        
        return {
            'total': total,
            'by_scope': {
                'buy': buy_vars,
                'sell': sell_vars,
                'combined': combined_vars,
                'analysis': analysis_vars,
            },
            'by_timeframe': {
                'tick': tick_vars,
                'min': min_vars,
                'common': common_vars,
            },
            'filter_candidates': filter_candidates,
            'segment_filter_candidates': segment_filter_candidates,
            'lookahead_vars': lookahead_vars,
            'categories': self.get_categories(),
        }


# =============================================================================
# 호환성 유지: 기존 코드에서 사용하던 BUY_TIME_FILTER_COLUMNS 동적 생성
# =============================================================================

def get_buy_time_filter_columns(timeframe: str = 'tick') -> List[str]:
    """
    기존 metric_registry.py의 BUY_TIME_FILTER_COLUMNS와 호환되는 목록을 반환합니다.
    
    Args:
        timeframe: 'tick' 또는 'min'
        
    Returns:
        필터 후보 변수명 리스트
    """
    registry = VariableRegistry()
    return registry.get_filter_candidates(timeframe)


# 싱글톤 인스턴스
_registry_instance: Optional[VariableRegistry] = None


def get_registry() -> VariableRegistry:
    """
    레지스트리 싱글톤 인스턴스를 반환합니다.
    
    Returns:
        VariableRegistry 인스턴스
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = VariableRegistry()
    return _registry_instance


# =============================================================================
# 테스트/디버깅용
# =============================================================================

if __name__ == '__main__':
    registry = get_registry()
    summary = registry.summary()
    
    print("=" * 60)
    print("백테스팅 변수 레지스트리 요약")
    print("=" * 60)
    print(f"총 변수 수: {summary['total']}")
    print()
    print("시점별:")
    print(f"  - 매수 시점: {summary['by_scope']['buy']}")
    print(f"  - 매도 시점: {summary['by_scope']['sell']}")
    print(f"  - 조합 (매수+매도): {summary['by_scope']['combined']}")
    print(f"  - 분석 전용: {summary['by_scope']['analysis']}")
    print()
    print("타임프레임별:")
    print(f"  - Tick 전용: {summary['by_timeframe']['tick']}")
    print(f"  - Min 전용: {summary['by_timeframe']['min']}")
    print(f"  - 공통: {summary['by_timeframe']['common']}")
    print()
    print(f"필터 후보: {summary['filter_candidates']}")
    print(f"세그먼트 필터 후보: {summary['segment_filter_candidates']}")
    print(f"룩어헤드 포함 변수: {summary['lookahead_vars']}")
    print()
    print(f"카테고리: {', '.join(summary['categories'])}")
    print("=" * 60)
    
    # Tick 필터 후보 출력
    print("\nTick 필터 후보 변수:")
    tick_candidates = registry.get_filter_candidates('tick')
    for i, name in enumerate(tick_candidates, 1):
        defn = registry.get(name)
        print(f"  {i:2d}. {name} ({defn.category})")
    
    print(f"\n총 {len(tick_candidates)}개")
