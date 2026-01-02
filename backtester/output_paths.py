from __future__ import annotations

from pathlib import Path

from backtester.output_manifest import build_numbered_path

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


def build_backtesting_output_path(
    save_file_name: str | None,
    suffix: str,
    *,
    output_dir: Path | str | None = None,
    prefix: str | None = None,
) -> Path:
    base_dir = Path(output_dir) if output_dir is not None else ensure_backtesting_output_dir(save_file_name)
    name_prefix = prefix or (str(save_file_name) if save_file_name is not None else '')
    return build_numbered_path(base_dir, name_prefix, suffix)


def get_legacy_graph_dir() -> Path:
    return Path(GRAPH_PATH)
