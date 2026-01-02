from __future__ import annotations

from copy import deepcopy


_DEFAULT_CONFIG = {
    'enable_parallel_charts': True,
    'parallel_chart_workers': 4,
    'parallel_chart_timeout_s': 600,
    'parallel_start_method': 'spawn',
    'enable_ipc_transfer': True,
    'ipc_format': 'parquet',
    'ipc_cleanup': True,
    'enable_telegram_async': True,
    'telegram_batch_size': 10,
    'telegram_batch_interval_s': 1.0,
    'telegram_queue_timeout_s': 0.2,
    'enable_csv_parallel': True,
    'csv_chunk_size': 200000,
    'enable_numba': True,
    'enable_cache': False,
    'cache_dir': './_cache/backtesting_output',
    'output_manifest_enabled': True,
    'output_alias_enabled': True,
    'output_alias_mode': 'hardlink',  # hardlink | copy | none
}


def get_backtesting_output_config() -> dict:
    config = deepcopy(_DEFAULT_CONFIG)
    try:
        from config.backtesting_output import BACKTESTING_OUTPUT_CONFIG
    except Exception:
        return config

    if isinstance(BACKTESTING_OUTPUT_CONFIG, dict):
        config.update(BACKTESTING_OUTPUT_CONFIG)
    return config
