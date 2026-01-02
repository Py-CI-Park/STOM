# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import Dict

import numpy as np
import pandas as pd


def _convert_bool_ops_to_pandas(expr: str) -> str:
    """
    자동 생성 조건식(문자열)의 and/or를 pandas eval용(&/|)으로 변환합니다.
    - generated_code['buy_conditions']는 'and (...)' 형태이므로 앞의 and도 제거합니다.
    """
    s = str(expr).strip() if expr is not None else ''
    if not s:
        return ''
    if s.lower().startswith('and '):
        s = s[4:].strip()
    s = re.sub(r'\band\b', '&', s)
    s = re.sub(r'\bor\b', '|', s)
    return s.strip()


def build_filter_mask_from_generated_code(df: pd.DataFrame, generated_code: dict) -> Dict[str, object]:
    """
    generated_code['buy_conditions']를 이용해 df에서 '매수 유지(keep)' 마스크를 생성합니다.
    Returns:
        dict:
          - mask: pd.Series[bool] | None
          - exprs: list[str]
          - error: str | None
          - failed_expr: str | None
    """
    result = {'mask': None, 'exprs': [], 'error': None, 'failed_expr': None}
    if not isinstance(df, pd.DataFrame) or df.empty:
        result['error'] = 'df가 비어있음'
        return result
    if not isinstance(generated_code, dict):
        result['error'] = 'generated_code가 dict가 아님'
        return result

    lines = generated_code.get('buy_conditions') or []
    if not lines:
        result['error'] = 'buy_conditions 없음'
        return result

    mask = pd.Series(True, index=df.index)
    safe_globals = {"__builtins__": {}}
    safe_locals = {str(c): df[c] for c in df.columns}
    safe_locals.update({"np": np, "pd": pd})

    for raw in lines:
        expr = _convert_bool_ops_to_pandas(raw)
        if not expr:
            continue
        try:
            cond = eval(expr, safe_globals, safe_locals)
        except Exception as e:
            result['error'] = str(e)
            result['failed_expr'] = expr
            return result
        try:
            cond = cond.astype(bool)
        except Exception:
            pass
        mask = mask & cond
        result['exprs'].append(expr)

    result['mask'] = mask
    return result
