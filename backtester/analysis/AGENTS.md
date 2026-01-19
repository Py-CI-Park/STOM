<!-- Parent: ../AGENTS.md -->
# backtester/analysis

## Purpose
Historical analysis tools and utilities for backtesting results processing. Provides core metrics calculation, result handling, caching, and performance optimization for backtest analysis.

## Key Files
- `metrics_base.py` - Base metrics calculations (MDD, profitability, etc.)
- `results.py` - Result processing with Numba optimization (GetBackResult)
- `indicators.py` - Technical indicator calculations
- `cache.py` - Performance caching layer
- `optuna_server.py` - Optimization experiment tracking
- `text_utils.py` - Text formatting utilities
- `memo_utils.py` - Memoization helpers
- `ipc_utils.py` - Inter-process communication utilities
- `filter_apply.py` - Filter application logic
- `output_config.py` - Output configuration management
- `plotting.py` - Chart plotting utilities
- `plotting_parallel.py` - Parallel plotting for performance
- `exports.py` - Export functionality
- `metric_registry.py` - Metric registration system

## Subdirectories
None

## For AI Agents
When working with backtest analysis:
1. Use `metrics_base.py` for calculating standard metrics (MDD, profit rate, etc.)
2. `results.py` contains Numba-optimized `GetBackResult()` function - critical for performance
3. Cache results using `cache.py` to avoid redundant calculations
4. For visualization, use `plotting.py` or `plotting_parallel.py` for multi-core rendering
5. All metrics follow Korean naming conventions (승률, 수익률, MDD)
6. Optimize with Numba when processing large result sets
7. Use `metric_registry.py` for adding custom metrics

## Dependencies
- numpy==1.26.4 - Array operations
- pandas==2.0.3 - Data manipulation
- numba - JIT compilation for performance
- optuna - Hyperparameter optimization
- matplotlib/pyqtgraph - Plotting
