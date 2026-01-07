# -*- coding: utf-8 -*-
"""
메트릭 레지스트리

NOTE: 변수 관리의 단일 소스(Single Source of Truth)는 
      `backtester/variable_registry.py`입니다.
      이 파일의 BUY_TIME_FILTER_COLUMNS는 레거시 호환성을 위해 유지됩니다.
      새로운 변수 추가 시 반드시 variable_registry.py에도 등록해주세요.
      
참조: docs/Guideline/Variable_Management_Guide.md
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    scope: str  # buy | sell | combined | analysis_only
    unit: str
    formula: List[str]
    runtime_compatible: bool = True
    for_filter: bool = True


# NOTE: 이 리스트는 레거시 호환성을 위해 유지됩니다.
# 변수 관리의 단일 소스: backtester/variable_registry.py
# 새로운 변수 추가 시 variable_registry.py에도 등록하세요.
BUY_TIME_FILTER_COLUMNS: List[str] = [
    '매수등락율', '매수시가등락율', '매수당일거래대금', '매수체결강도',
    '매수전일비', '매수회전율', '매수전일동시간비', '매수고가', '매수저가',
    '매수고저평균대비등락율', '매수매도총잔량', '매수매수총잔량',
    '매수호가잔량비', '매수매도호가1', '매수매수호가1', '매수스프레드',
    '매수초당매수수량', '매수초당매도수량', '매수초당거래대금',
    '시가총액', '매수가', '매수시', '매수분', '매수초',
    '모멘텀점수', '매수변동폭', '매수변동폭비율', '거래품질점수', '위험도점수',
    '초당매수수량_매도총잔량_비율', '매도잔량_매수잔량_비율', '매수잔량_매도잔량_비율',
    '초당매도_매수_비율', '초당매수_매도_비율', '현재가_고저범위_위치',
    '초당거래대금_당일비중', '초당순매수수량', '초당순매수금액', '초당순매수비율',
    '당일거래대금_전틱분봉_비율', '당일거래대금_5틱분봉평균_비율',
]

ANALYSIS_ONLY_COLUMNS: List[str] = [
]

METRIC_DEFINITIONS: Dict[str, MetricDefinition] = {
    '모멘텀점수': MetricDefinition(
        name='모멘텀점수',
        scope='buy',
        unit='점수',
        formula=[
            '등락율_norm = 매수등락율 / 10',
            '체결강도_norm = (매수체결강도 - 100) / 50',
            '모멘텀점수 = (등락율_norm*0.4 + 체결강도_norm*0.6) * 10',
        ],
    ),
    '거래품질점수': MetricDefinition(
        name='거래품질점수',
        scope='buy',
        unit='점수(0~100)',
        formula=[
            '기본 50점에서 체결강도/호가잔량/시가총액 가산',
            '매수등락율/매수스프레드 조건 감산',
        ],
    ),
    '위험도점수': MetricDefinition(
        name='위험도점수',
        scope='buy',
        unit='점수(0~100)',
        formula=[
            '매수등락율/체결강도/거래대금/시가총액/호가잔량/스프레드 기반 가산',
            '회전율/변동폭비율 기반 가산',
        ],
    ),
    '매수변동폭': MetricDefinition(
        name='매수변동폭',
        scope='buy',
        unit='원',
        formula=['매수변동폭 = 매수고가 - 매수저가'],
    ),
    '매수변동폭비율': MetricDefinition(
        name='매수변동폭비율',
        scope='buy',
        unit='%',
        formula=['매수변동폭비율 = (매수고가-매수저가)/매수저가*100'],
    ),
    '초당매수수량_매도총잔량_비율': MetricDefinition(
        name='초당매수수량_매도총잔량_비율',
        scope='buy',
        unit='%',
        formula=['초당매수수량_매도총잔량_비율 = 초당매수수량 / 매도총잔량 * 100'],
    ),
    '매도잔량_매수잔량_비율': MetricDefinition(
        name='매도잔량_매수잔량_비율',
        scope='buy',
        unit='배율',
        formula=['매도잔량_매수잔량_비율 = 매도총잔량 / 매수총잔량'],
    ),
    '매수잔량_매도잔량_비율': MetricDefinition(
        name='매수잔량_매도잔량_비율',
        scope='buy',
        unit='배율',
        formula=['매수잔량_매도잔량_비율 = 매수총잔량 / 매도총잔량'],
    ),
    '초당매도_매수_비율': MetricDefinition(
        name='초당매도_매수_비율',
        scope='buy',
        unit='배율',
        formula=['초당매도_매수_비율 = 초당매도수량 / 초당매수수량'],
    ),
    '초당매수_매도_비율': MetricDefinition(
        name='초당매수_매도_비율',
        scope='buy',
        unit='배율',
        formula=['초당매수_매도_비율 = 초당매수수량 / 초당매도수량'],
    ),
    '현재가_고저범위_위치': MetricDefinition(
        name='현재가_고저범위_위치',
        scope='buy',
        unit='%',
        formula=['현재가_고저범위_위치 = (매수가-매수저가)/(매수고가-매수저가)*100'],
    ),
    '초당거래대금_당일비중': MetricDefinition(
        name='초당거래대금_당일비중',
        scope='buy',
        unit='만분율',
        formula=['초당거래대금_당일비중 = 매수초당거래대금/매수당일거래대금*10000'],
    ),
    '초당순매수수량': MetricDefinition(
        name='초당순매수수량',
        scope='buy',
        unit='수량',
        formula=['초당순매수수량 = 초당매수수량 - 초당매도수량'],
    ),
    '초당순매수금액': MetricDefinition(
        name='초당순매수금액',
        scope='buy',
        unit='백만원',
        formula=['초당순매수금액 = 초당순매수수량 * 매수가 / 1_000_000'],
    ),
    '초당순매수비율': MetricDefinition(
        name='초당순매수비율',
        scope='buy',
        unit='%',
        formula=['초당순매수비율 = 초당매수수량 / (초당매수수량+초당매도수량) * 100'],
    ),
}
