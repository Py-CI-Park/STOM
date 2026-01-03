# -*- coding: utf-8 -*-
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


BUY_TIME_FILTER_COLUMNS_LEGACY: List[str] = [
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

BUY_TIME_FILTER_COLUMNS: List[str] = [
    'B_등락율', 'B_시가등락율', 'B_당일거래대금', 'B_체결강도',
    'B_전일비', 'B_회전율', 'B_전일동시간비', 'B_고가', 'B_저가',
    'B_고저평균대비등락율', 'B_매도총잔량', 'B_매수총잔량',
    'B_호가잔량비', 'B_매도호가1', 'B_매수호가1', 'B_스프레드',
    'B_초당매수수량', 'B_초당매도수량', 'B_초당거래대금',
    '시가총액', 'B_가', 'B_시', 'B_분', 'B_초',
    'B_모멘텀점수', 'B_변동폭', 'B_변동폭비율', 'B_거래품질점수', 'B_위험도점수',
    'B_초당매수수량_매도총잔량_비율', 'B_매도잔량_매수잔량_비율', 'B_매수잔량_매도잔량_비율',
    'B_초당매도_매수_비율', 'B_초당매수_매도_비율', 'B_현재가_고저범위_위치',
    'B_초당거래대금_당일비중', 'B_초당순매수수량', 'B_초당순매수금액', 'B_초당순매수비율',
    'B_당일거래대금_전틱분봉_비율', 'B_당일거래대금_5틱분봉평균_비율',
]


ANALYSIS_ONLY_COLUMNS: List[str] = [
]

METRIC_DEFINITIONS: Dict[str, MetricDefinition] = {
    'B_모멘텀점수': MetricDefinition(
        name='B_모멘텀점수',
        scope='buy',
        unit='점수',
        formula=[
            '등락율_norm = B_등락율 / 10',
            '체결강도_norm = (B_체결강도 - 100) / 50',
            'B_모멘텀점수 = (등락율_norm*0.4 + 체결강도_norm*0.6) * 10',
        ],
    ),

    'B_거래품질점수': MetricDefinition(
        name='B_거래품질점수',
        scope='buy',
        unit='점수(0~100)',
        formula=[
            '기본 50점에서 체결강도/호가잔량/시가총액 가산',
            'B_등락율/B_스프레드 조건 감산',
        ],
    ),

    'B_위험도점수': MetricDefinition(
        name='B_위험도점수',
        scope='buy',
        unit='점수(0~100)',
        formula=[
            'B_등락율/체결강도/거래대금/시가총액/호가잔량/스프레드 기반 가산',
            '회전율/변동폭비율 기반 가산',
        ],
    ),

    'B_변동폭': MetricDefinition(
        name='B_변동폭',
        scope='buy',
        unit='원',
        formula=['B_변동폭 = B_고가 - B_저가'],
    ),

    'B_변동폭비율': MetricDefinition(
        name='B_변동폭비율',
        scope='buy',
        unit='%',
        formula=['B_변동폭비율 = (B_고가-B_저가)/B_저가*100'],
    ),

    'B_초당매수수량_매도총잔량_비율': MetricDefinition(
        name='B_초당매수수량_매도총잔량_비율',
        scope='buy',
        unit='%',
        formula=['B_초당매수수량_매도총잔량_비율 = B_초당매수수량 / B_매도총잔량 * 100'],
    ),

    'B_매도잔량_매수잔량_비율': MetricDefinition(
        name='B_매도잔량_매수잔량_비율',
        scope='buy',
        unit='배율',
        formula=['B_매도잔량_매수잔량_비율 = B_매도총잔량 / B_매수총잔량'],
    ),

    'B_매수잔량_매도잔량_비율': MetricDefinition(
        name='B_매수잔량_매도잔량_비율',
        scope='buy',
        unit='배율',
        formula=['B_매수잔량_매도잔량_비율 = B_매수총잔량 / B_매도총잔량'],
    ),

    'B_초당매도_매수_비율': MetricDefinition(
        name='B_초당매도_매수_비율',
        scope='buy',
        unit='배율',
        formula=['B_초당매도_매수_비율 = B_초당매도수량 / B_초당매수수량'],
    ),

    'B_초당매수_매도_비율': MetricDefinition(
        name='B_초당매수_매도_비율',
        scope='buy',
        unit='배율',
        formula=['B_초당매수_매도_비율 = B_초당매수수량 / B_초당매도수량'],
    ),

    'B_현재가_고저범위_위치': MetricDefinition(
        name='B_현재가_고저범위_위치',
        scope='buy',
        unit='%',
        formula=['B_현재가_고저범위_위치 = (B_가-B_저가)/(B_고가-B_저가)*100'],
    ),

    'B_초당거래대금_당일비중': MetricDefinition(
        name='B_초당거래대금_당일비중',
        scope='buy',
        unit='만분율',
        formula=['B_초당거래대금_당일비중 = B_초당거래대금/B_당일거래대금*10000'],
    ),

    'B_초당순매수수량': MetricDefinition(
        name='B_초당순매수수량',
        scope='buy',
        unit='수량',
        formula=['B_초당순매수수량 = B_초당매수수량 - B_초당매도수량'],
    ),

    'B_초당순매수금액': MetricDefinition(
        name='B_초당순매수금액',
        scope='buy',
        unit='백만원',
        formula=['B_초당순매수금액 = B_초당순매수수량 * B_가 / 1_000_000'],
    ),

    'B_초당순매수비율': MetricDefinition(
        name='B_초당순매수비율',
        scope='buy',
        unit='%',
        formula=['B_초당순매수비율 = B_초당매수수량 / (B_초당매수수량+B_초당매도수량) * 100'],
    ),

}
