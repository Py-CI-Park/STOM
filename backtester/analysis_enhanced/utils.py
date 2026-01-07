# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


# =============================================================================
# [2026-01-07] 소수점 정밀도 제한 유틸리티
# =============================================================================
# 백테스팅 분석에서 생성되는 파생 변수들의 소수점을 최대 4자리로 제한합니다.
# - 목적: CSV 출력 시 가독성 향상, 파일 크기 감소, 일관된 정밀도 유지
# - 적용 대상: 비율, 퍼센트, 점수 등 연산으로 생성되는 파생 변수

DEFAULT_DECIMAL_PLACES = 4  # 기본 소수점 자릿수


def round_decimal(value, decimals: int = DEFAULT_DECIMAL_PLACES):
    """
    단일 값의 소수점을 지정된 자릿수로 반올림합니다.
    
    Args:
        value: 반올림할 값 (숫자, None, NaN 등)
        decimals: 소수점 자릿수 (기본값: 4)
    
    Returns:
        반올림된 값 (원본이 None/NaN이면 그대로 반환)
    """
    if value is None:
        return None
    try:
        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
            return value
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return value


def round_series(series: pd.Series, decimals: int = DEFAULT_DECIMAL_PLACES) -> pd.Series:
    """
    pandas Series의 소수점을 지정된 자릿수로 반올림합니다.
    
    Args:
        series: 반올림할 Series
        decimals: 소수점 자릿수 (기본값: 4)
    
    Returns:
        반올림된 Series
    """
    if series is None or not isinstance(series, pd.Series):
        return series
    try:
        return series.round(decimals)
    except Exception:
        return series


def round_dataframe_floats(
    df: pd.DataFrame,
    decimals: int = DEFAULT_DECIMAL_PLACES,
    exclude_columns: list = None,
) -> pd.DataFrame:
    """
    DataFrame의 모든 float 컬럼을 지정된 소수점 자릿수로 반올림합니다.
    
    Args:
        df: 반올림할 DataFrame
        decimals: 소수점 자릿수 (기본값: 4)
        exclude_columns: 제외할 컬럼 목록 (예: 인덱스, ID 등)
    
    Returns:
        반올림된 DataFrame
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return df
    
    exclude_columns = exclude_columns or []
    result = df.copy()
    
    for col in result.columns:
        if col in exclude_columns:
            continue
        if pd.api.types.is_float_dtype(result[col]):
            try:
                result[col] = result[col].round(decimals)
            except Exception:
                pass
    
    return result


def format_float_str(value, decimals: int = DEFAULT_DECIMAL_PLACES) -> str:
    """
    숫자를 지정된 소수점 자릿수의 문자열로 변환합니다.
    정수 값이면 소수점 없이 반환합니다.
    
    Args:
        value: 변환할 값
        decimals: 소수점 자릿수 (기본값: 4)
    
    Returns:
        포맷팅된 문자열
    """
    if value is None:
        return ''
    try:
        v = float(value)
        if np.isnan(v) or np.isinf(v):
            return str(value)
        # 정수인 경우 소수점 없이 반환
        if v == int(v):
            return str(int(v))
        # 소수점 자릿수 적용 후 불필요한 0 제거
        formatted = f"{v:.{decimals}f}".rstrip('0').rstrip('.')
        return formatted
    except (TypeError, ValueError):
        return str(value)

def _normalize_text_for_hash(text) -> str:
    if text is None:
        return ''
    s = str(text)
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    return s.strip()

def ComputeStrategyKey(buystg: str = None, sellstg: str = None) -> str:
    """
    매수/매도 전략 코드(전체 텍스트)를 바탕으로 전략 식별키를 생성합니다.
    - 가장 정확한 식별을 위해 sha256(매수코드 + 매도코드) 기반으로 생성
    """
    buy = _normalize_text_for_hash(buystg)
    sell = _normalize_text_for_hash(sellstg)
    payload = f"BUY:\n{buy}\n\nSELL:\n{sell}".encode('utf-8')
    return hashlib.sha256(payload).hexdigest()

def _extract_strategy_block_lines(code: str, start_marker: str, end_marker: str | None = None,
                                 max_lines: int = 12, max_line_len: int = 140) -> list[str]:
    """
    전략 문자열에서 특정 블록(예: 'if 매수:' ~ 'if 매도:') 라인 일부만 추출합니다.
    - 텔레그램/차트 표시 목적이므로, 너무 긴 라인은 잘라냅니다.
    """
    try:
        s = _normalize_text_for_hash(code)
        if not s:
            return []
        lines = s.splitlines()

        start_idx = None
        for i, ln in enumerate(lines):
            if start_marker in ln:
                start_idx = i
                break

        if start_idx is None:
            selected = lines[:max_lines]
        else:
            selected = lines[start_idx:]
            if end_marker:
                end_idx = None
                for j in range(1, len(selected)):
                    if end_marker in selected[j]:
                        end_idx = j
                        break
                if end_idx is not None:
                    selected = selected[:end_idx]
            selected = selected[:max_lines]

        out: list[str] = []
        for ln in selected:
            # 주석 제거(간단 버전)
            if '#' in ln:
                ln = ln.split('#', 1)[0]
            ln = ln.rstrip()
            if not ln.strip():
                continue
            if len(ln) > max_line_len:
                ln = ln[: max_line_len - 3] + "..."
            out.append(ln)
        return out
    except Exception:
        return []

def _safe_filename(name: str, max_len: int = 90) -> str:
    """
    Windows 경로 길이 이슈를 줄이기 위한 안전한 파일명 생성.
    - 너무 길면 앞부분 + 해시로 축약
    """
    s = str(name) if name is not None else 'run'
    s = s.replace('\\', '_').replace('/', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_') \
         .replace('<', '_').replace('>', '_').replace('|', '_')
    s = s.strip()
    if len(s) <= max_len:
        return s
    h = hashlib.sha1(s.encode('utf-8')).hexdigest()[:10]
    return f"{s[:max_len - 11]}_{h}"

def _write_json(path: Path, data: dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8-sig')
    except Exception:
        pass

def _append_jsonl(path: Path, data: dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8-sig') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        pass
