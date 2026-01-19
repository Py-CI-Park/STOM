<!-- Parent: ../AGENTS.md -->
# config/

## Purpose
Application-wide configuration files for runtime behavior control. Contains centralized settings for subsystem optimization, feature toggles, and performance tuning.

## Key Files

### Backtesting Output Configuration
- **`backtesting_output.py`** (32 lines)
  - Central configuration for backtesting output pipeline
  - Controls parallel processing, data transfer, and optimization features
  - Imported by: `backtester/analysis/` modules

## Configuration Schema

### Parallel Processing
```python
'enable_parallel_charts': True        # Enable parallel chart generation
'parallel_chart_workers': 4           # Number of worker processes (CPU cores)
'parallel_chart_timeout_s': 600       # Timeout for chart generation (10 min)
'parallel_start_method': 'spawn'      # Process start method (spawn/fork/forkserver)
```

### IPC (Inter-Process Communication)
```python
'enable_ipc_transfer': True           # Enable IPC for data transfer between processes
'ipc_format': 'parquet'               # Serialization format: parquet | feather | pickle
'ipc_cleanup': True                   # Auto-cleanup temporary IPC files
```

### Telegram Integration
```python
'enable_telegram_async': True         # Enable async telegram message sending
'telegram_batch_size': 10             # Messages per batch
'telegram_batch_interval_s': 1.0      # Seconds between batches
'telegram_queue_timeout_s': 0.2       # Queue get() timeout
```

### CSV Export
```python
'enable_csv_parallel': True           # Enable parallel CSV writing
'csv_chunk_size': 200000              # Rows per chunk for parallel processing
```

### Optimization Features
```python
'enable_numba': True                  # Enable Numba JIT compilation
'enable_cache': False                 # Enable result caching (currently disabled)
'cache_dir': './_cache/backtesting_output'  # Cache directory path
'output_manifest_enabled': True       # Enable output manifest generation
'output_alias_enabled': False         # Enable output aliasing (currently disabled)
'output_alias_mode': 'hardlink'       # Alias mode: hardlink | symlink | copy
'output_alias_subdir': None           # Subdirectory for aliases
'output_alias_cleanup_legacy': False  # Cleanup old aliases
```

## For AI Agents

### Working with Configuration

1. **Reading Configuration**:
   ```python
   from config.backtesting_output import BACKTESTING_OUTPUT_CONFIG

   # Access settings
   workers = BACKTESTING_OUTPUT_CONFIG['parallel_chart_workers']
   ipc_format = BACKTESTING_OUTPUT_CONFIG['ipc_format']
   ```

2. **Configuration-Driven Features**:
   ```python
   # Check feature flag before using feature
   if BACKTESTING_OUTPUT_CONFIG['enable_parallel_charts']:
       # Execute parallel chart generation
       create_charts_parallel(workers=BACKTESTING_OUTPUT_CONFIG['parallel_chart_workers'])
   else:
       # Fall back to sequential processing
       create_charts_sequential()
   ```

3. **Modifying Configuration**:
   - Edit `config/backtesting_output.py` directly
   - Restart application for changes to take effect
   - Test configuration changes with `scripts/measure_backtesting_performance.py`
   - Validate with `tests/test_backtesting_output.py`

### Configuration Guidelines

1. **Performance Tuning**:
   - **`parallel_chart_workers`**: Set to CPU core count (4-8 typical)
   - **`csv_chunk_size`**: Larger = less overhead, more memory (100K-500K)
   - **`telegram_batch_size`**: Balance latency vs. throughput (5-20)
   - **`ipc_format`**:
     - `parquet` - Best compression, slower
     - `feather` - Good balance
     - `pickle` - Fastest, largest files

2. **Feature Flags**:
   - Disable features causing issues without code changes
   - Enable/disable for A/B performance testing
   - Gradual rollout of experimental features

3. **Resource Management**:
   - **`parallel_chart_timeout_s`**: Increase for large backtests
   - **`telegram_queue_timeout_s`**: Balance responsiveness vs. CPU usage
   - **`ipc_cleanup`**: Enable to avoid disk space issues

### Adding New Configuration

1. **New Setting Structure**:
   ```python
   BACKTESTING_OUTPUT_CONFIG = {
       # Existing settings...

       # New feature configuration
       'enable_new_feature': True,
       'new_feature_param': 100,
       'new_feature_mode': 'option1',  # option1 | option2
   }
   ```

2. **Documentation**:
   - Add inline comments explaining purpose
   - Document valid value ranges
   - Note performance implications
   - Update this AGENTS.md file

3. **Validation**:
   - Add validation in consuming modules
   - Provide sensible defaults
   - Log configuration usage for debugging

### Configuration Best Practices

1. **Naming Conventions**:
   - Feature flags: `enable_<feature>`
   - Parameters: `<feature>_<parameter>`
   - Units: Include unit in name (`_s`, `_ms`, `_mb`)

2. **Type Consistency**:
   - Booleans for feature flags
   - Integers for counts/sizes
   - Floats for timeouts/intervals
   - Strings for mode/format selection

3. **Safe Defaults**:
   - Conservative values for new features
   - Disable experimental features by default
   - Ensure backward compatibility

## Configuration Impact

### Performance Impact by Setting

| Setting | Impact | Trade-off |
|---------|--------|-----------|
| `enable_parallel_charts` | +50-70% speed | +Memory usage |
| `parallel_chart_workers` | +Linear scaling | +Memory per worker |
| `ipc_format=parquet` | -Disk space | +CPU, -Speed |
| `ipc_format=pickle` | +Speed | +Disk space |
| `enable_csv_parallel` | +30-50% CSV speed | +Memory |
| `enable_numba` | +20-50% calculation | +First-run time |
| `telegram_batch_size=10` | -Network calls | +Latency |

### Dependencies

#### Used By
- `backtester/analysis/charts.py` - Parallel chart generation
- `backtester/analysis/ipc_utils.py` - IPC data transfer
- `backtester/analysis/exports.py` - CSV export
- `backtester/analysis/metrics_base.py` - Calculation optimizations
- `backtester/back_static.py` - Telegram integration

#### Related Files
- `tests/test_backtesting_output.py` - Configuration validation
- `scripts/measure_backtesting_performance.py` - Performance measurement
- `utility/setting.py` - Global system settings (separate)

## Future Configuration

### Potential Additions
1. **Memory Management**:
   ```python
   'max_memory_gb': 16              # Memory limit for parallel operations
   'memory_monitoring': True        # Enable memory usage tracking
   ```

2. **Logging Configuration**:
   ```python
   'log_level': 'INFO'              # DEBUG | INFO | WARNING | ERROR
   'log_performance': True          # Log timing information
   ```

3. **Caching Strategy**:
   ```python
   'cache_ttl_hours': 24            # Cache time-to-live
   'cache_max_size_gb': 10          # Maximum cache size
   ```

## Notes

- Configuration is Python-based (not YAML/JSON) for simplicity and type safety
- Changes require application restart (no hot-reloading)
- Consider environment-specific configs for production vs. development
- Monitor impact of configuration changes with benchmarks
- Document all configuration changes in version control
- Configuration is separate from `utility/setting.py` (database/API credentials)
