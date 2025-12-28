from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd

from backtester.analysis.output_config import get_backtesting_output_config


def _get_cache_dir(save_file_name: str, cache_dir: Optional[str] = None) -> Path:
    cfg = get_backtesting_output_config()
    base = Path(cache_dir or cfg.get('cache_dir', './_cache/backtesting_output'))
    out_dir = base / str(save_file_name)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def build_df_signature(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {'rows': 0}
    last_index = None
    try:
        last_index = str(df.index[-1])
    except Exception:
        last_index = None
    return {
        'rows': int(len(df)),
        'last_index': last_index,
    }


def load_cached_df(save_file_name: str,
                   key: str,
                   signature: Optional[dict] = None,
                   cache_dir: Optional[str] = None) -> Optional[pd.DataFrame]:
    try:
        cache_base = _get_cache_dir(save_file_name, cache_dir=cache_dir)
        data_path = cache_base / f"{key}.pkl"
        meta_path = cache_base / f"{key}.meta.json"
        if not data_path.exists():
            return None
        if signature is not None and meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding='utf-8'))
                if meta.get('rows') != signature.get('rows') or meta.get('last_index') != signature.get('last_index'):
                    return None
            except Exception:
                return None
        return pd.read_pickle(data_path)
    except Exception:
        return None


def save_cached_df(save_file_name: str,
                   key: str,
                   df: pd.DataFrame,
                   signature: Optional[dict] = None,
                   cache_dir: Optional[str] = None) -> Optional[str]:
    try:
        cache_base = _get_cache_dir(save_file_name, cache_dir=cache_dir)
        data_path = cache_base / f"{key}.pkl"
        df.to_pickle(data_path)
        if signature is not None:
            meta_path = cache_base / f"{key}.meta.json"
            meta_path.write_text(json.dumps(signature, ensure_ascii=False), encoding='utf-8')
        return str(data_path)
    except Exception:
        return None
