BACKTESTING_OUTPUT_CONFIG = {
    # 병렬 차트 생성
    'enable_parallel_charts': True,
    'parallel_chart_workers': 4,
    'parallel_chart_timeout_s': 600,
    'parallel_start_method': 'spawn',

    # IPC(프로세스 간 데이터 전달)
    'enable_ipc_transfer': True,
    'ipc_format': 'parquet',  # parquet | feather | pickle
    'ipc_cleanup': True,

    # 텔레그램 전송
    'enable_telegram_async': True,
    'telegram_batch_size': 10,
    'telegram_batch_interval_s': 1.0,
    'telegram_queue_timeout_s': 0.2,

    # CSV 저장
    'enable_csv_parallel': True,
    'csv_chunk_size': 200000,

    # 최적화
    'enable_numba': True,
    'enable_cache': False,
    'cache_dir': './_cache/backtesting_output',
    'output_manifest_enabled': True,
    'output_alias_enabled': False,
    'output_alias_mode': 'hardlink',
    'output_alias_subdir': None,
    'output_alias_cleanup_legacy': False,
}
