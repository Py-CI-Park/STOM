from __future__ import annotations

from pathlib import Path

from utility.setting import BACKTEST_OUTPUT_PATH, GRAPH_PATH


def get_backtesting_output_dir(save_file_name: str | None) -> Path:
    base_dir = Path(BACKTEST_OUTPUT_PATH)
    if save_file_name:
        return base_dir / str(save_file_name)
    return base_dir


def ensure_backtesting_output_dir(save_file_name: str | None) -> Path:
    output_dir = get_backtesting_output_dir(save_file_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_legacy_graph_dir() -> Path:
    return Path(GRAPH_PATH)
