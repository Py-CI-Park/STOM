from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

import pandas as pd


def _ensure_ipc_dir(output_dir: str | Path) -> Path:
    base = Path(output_dir)
    ipc_dir = base / "ipc"
    ipc_dir.mkdir(parents=True, exist_ok=True)
    return ipc_dir


def _try_parquet(df: pd.DataFrame, path: Path) -> bool:
    try:
        df.to_parquet(path, engine='pyarrow', index=True)
        return True
    except Exception:
        try:
            df.to_parquet(path, index=True)
            return True
        except Exception:
            return False


def _try_feather(df: pd.DataFrame, path: Path) -> bool:
    try:
        df.reset_index(drop=False).to_feather(path)
        return True
    except Exception:
        return False


def _try_pickle(df: pd.DataFrame, path: Path) -> bool:
    try:
        df.to_pickle(path)
        return True
    except Exception:
        return False


def save_dataframe_ipc(df: pd.DataFrame,
                       output_dir: str | Path,
                       prefix: str,
                       prefer_format: str = 'parquet') -> Optional[Path]:
    if df is None or df.empty:
        return None

    ipc_dir = _ensure_ipc_dir(output_dir)
    uid = uuid.uuid4().hex
    order = [prefer_format, 'parquet', 'feather', 'pickle']

    for fmt in order:
        if fmt == 'parquet':
            path = ipc_dir / f"{prefix}_{uid}.parquet"
            if _try_parquet(df, path):
                return path
        elif fmt == 'feather':
            path = ipc_dir / f"{prefix}_{uid}.feather"
            if _try_feather(df, path):
                return path
        elif fmt == 'pickle':
            path = ipc_dir / f"{prefix}_{uid}.pkl"
            if _try_pickle(df, path):
                return path

    return None


def load_dataframe_ipc(path: str | Path) -> Optional[pd.DataFrame]:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists():
        return None

    suffix = file_path.suffix.lower()
    try:
        if suffix == '.parquet':
            return pd.read_parquet(file_path)
        if suffix == '.feather':
            df = pd.read_feather(file_path)
            if 'index' in df.columns:
                df = df.set_index('index')
            return df
        if suffix == '.pkl':
            return pd.read_pickle(file_path)
    except Exception:
        return None

    return None


def cleanup_ipc_path(path: str | Path) -> None:
    try:
        file_path = Path(path)
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass
