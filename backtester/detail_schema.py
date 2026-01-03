from __future__ import annotations

import re

import pandas as pd

from backtester.analysis.metric_registry import BUY_TIME_FILTER_COLUMNS_LEGACY



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

_EXTRA_BUY_COLUMNS_LEGACY = {
    '추가매수시간',
    '손실확률_ML',
    '위험도_ML',
    '예측매수매도위험도점수_ML',
    '시간대평균수익률',
    '타이밍점수',
    '리스크조정수익률',
    '스프레드영향',
}


def canonicalize_detail_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    detail.csv 컬럼명을 B_/S_ 규칙으로 정규화합니다.
    - 매수* → B_* (앞의 '매수' 제거)
    - 매도* → S_* (앞의 '매도' 제거)
    - 매수 접두 없는 매수 시점 지표는 B_ 접두로 변환
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df

    cols = list(df.columns)
    rename_map: dict[str, str] = {}

    for col in cols:
        if not isinstance(col, str):
            continue
        if col.startswith('매수'):
            rename_map[col] = f"B_{col[2:]}"
        elif col.startswith('매도'):
            rename_map[col] = f"S_{col[2:]}"

    for col in BUY_TIME_FILTER_COLUMNS_LEGACY:
        if col in cols and not col.startswith(('매수', '매도', 'B_', 'S_')):
            rename_map[col] = f"B_{col}"

    for col in _EXTRA_BUY_COLUMNS_LEGACY:
        if col in cols and not col.startswith('B_'):
            rename_map[col] = f"B_{col}"

    if not rename_map:
        return df

    df_out = df.copy()
    drop_cols = [old for old, new in rename_map.items() if new in df_out.columns]
    if drop_cols:
        df_out = df_out.drop(columns=drop_cols)

    rename_map = {old: new for old, new in rename_map.items() if old not in drop_cols}
    if rename_map:
        df_out = df_out.rename(columns=rename_map)

    return df_out


def reorder_detail_columns(df: pd.DataFrame) -> pd.DataFrame:

    """
    detail.csv(거래 상세기록) 컬럼을 '읽기 쉬운 그룹' 중심으로 재정렬합니다.
    - 컬럼 존재 유무에 따라 유연하게 동작하며, 미정의 컬럼은 뒤에 유지됩니다.
    - 차트 보조용 컬럼(수익금합계020/…/랜덤 MDD 곡선 등)은 맨 뒤로 이동합니다.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df

    df = canonicalize_detail_columns(df)
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
        'B_시간',
        'S_시간',
        '보유시간',
        'S_조건',
        'B_추가매수시간',
    ]:
        add(col)

    # 2) 가격/금액/성과
    for col in [
        'B_가',
        'S_가',
        'B_금액',
        'S_금액',
        '수익률',
        '수익금',
        '수익금합계',
    ]:
        add(col)

    # 3) 매수 시각 분해(정렬/그룹용)
    for col in ['B_일자', 'B_시', 'B_분', 'B_초']:
        add(col)

    # 4) 핵심 파생/리스크/ML 예측(우선 배치)
    for col in [
        'B_모멘텀점수',
        'B_거래품질점수',
        'B_위험도점수',
        'B_손실확률_ML',
        'B_위험도_ML',
        'B_예측매수매도위험도점수_ML',
        'B_매수매도위험도점수',
        'B_리스크조정수익률',
        '급락신호',
    ]:
        add(col)

    # 5) 매수 시점 스냅샷(원본/파생 혼합: B_*)
    for col in cols:
        if col.startswith('B_') and col not in out:
            out.append(col)

    # 6) 매도 시점 스냅샷(원본/파생 혼합: S_*)
    for col in cols:
        if col.startswith('S_') and col not in out:
            out.append(col)

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


