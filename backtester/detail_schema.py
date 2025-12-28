from __future__ import annotations

import re

import pandas as pd


_RE_CHART_HELPER = re.compile(r'^수익금합계\\d+$')

_CHART_HELPER_COLS = {
    # PltShow()에서 생성되는 이동평균/보조 컬럼
    '수익금합계020',
    '수익금합계060',
    '수익금합계120',
    '수익금합계240',
    '수익금합계480',
    '이익금액',
    '손실금액',
}


def reorder_detail_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    detail.csv(거래 상세기록) 컬럼을 '읽기 쉬운 그룹' 중심으로 재정렬합니다.
    - 컬럼 존재 유무에 따라 유연하게 동작하며, 미정의 컬럼은 뒤에 유지됩니다.
    - 차트 보조용 컬럼(수익금합계020/…/랜덤 MDD 곡선 등)은 맨 뒤로 이동합니다.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df

    cols = list(df.columns)
    out: list[str] = []

    def add(col: str):
        if col in cols and col not in out:
            out.append(col)

    # 1) 일반/식별/시간
    for col in [
        '종목명',
        '시가총액',
        '포지션',
        '매수시간',
        '매도시간',
        '보유시간',
        '매도조건',
        '추가매수시간',
    ]:
        add(col)

    # 2) 가격/금액/성과
    for col in [
        '매수가',
        '매도가',
        '매수금액',
        '매도금액',
        '수익률',
        '수익금',
        '수익금합계',
    ]:
        add(col)

    # 3) 매수 시각 분해(정렬/그룹용)
    for col in ['매수일자', '매수시', '매수분', '매수초']:
        add(col)

    # 4) 매수 시점 스냅샷(원본/파생 혼합: 매수*)
    for col in cols:
        if col.startswith('매수') and col not in out:
            out.append(col)

    # 5) 매도 시점 스냅샷(원본/파생 혼합: 매도*)
    for col in cols:
        if col.startswith('매도') and col not in out:
            out.append(col)

    # 6) 핵심 파생/리스크/ML 예측(우선 배치)
    for col in [
        '모멘텀점수',
        '거래품질점수',
        '위험도점수',
        '손실확률_ML',
        '위험도_ML',
        '예측매수매도위험도점수_ML',
        '매수매도위험도점수',
        '리스크조정수익률',
        '급락신호',
    ]:
        add(col)

    # 7) 나머지 + (차트 보조 컬럼은 맨 뒤)
    chart_helpers: list[str] = []
    for col in cols:
        if col in out:
            continue
        if col in _CHART_HELPER_COLS or _RE_CHART_HELPER.match(col):
            chart_helpers.append(col)
            continue
        out.append(col)

    out.extend([c for c in chart_helpers if c not in out])

    return df[out].copy()

