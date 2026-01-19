<!-- Parent: ../AGENTS.md -->
# Backtester Module

## Purpose

Historical data testing and optimization engine for STOM trading strategies. Provides comprehensive backtesting across multiple markets (Kiwoom stock, Upbit, Binance) and timeframes (tick, minute), with grid search and genetic algorithm optimization capabilities. Supports multi-core parallel processing for performance-intensive backtesting operations.

## Key Files

### Core Orchestration
- **backtest.py** - Main backtesting orchestrator
  - Coordinates multi-process backtesting workflow
  - Manages queue communication between engines
  - Aggregates and presents results with MDD calculation
  - Generates performance metrics and visualizations

- **backfinder.py** - Strategy discovery and testing
  - Automated strategy discovery across market conditions
  - Iterative testing of strategy combinations
  - Performance ranking and filtering
  - Results aggregation and database storage

### Optimization Engines
- **optimiz.py** - Grid search optimization
  - Multi-variable parameter grid search
  - Optuna integration for hyperparameter tuning
  - Train/validation/test split support
  - Parallel optimization across multiple cores
  - Results persistence to DB_OPTUNA database

- **optimiz_genetic_algorithm.py** - Genetic algorithm optimization
  - Evolutionary parameter optimization
  - Population-based search with crossover/mutation
  - Fitness evaluation using trading performance metrics
  - Convergence tracking and early stopping
  - Alternative to grid search for large parameter spaces

- **optimiz_conditions.py** - Condition-based optimization
  - Specific optimization for trading condition files
  - Integration with condition documentation (BO, BOR, SO, SOR, OR, GAR)
  - Validates against 98.3% documentation compliance standard

### Market-Specific Engines

**Stock (Kiwoom) Engines:**
- **backengine_kiwoom_tick.py** - Stock tick-level backtesting
- **backengine_kiwoom_tick2.py** - Alternative tick engine implementation
- **backengine_kiwoom_min.py** - Stock minute-level backtesting
- **backengine_kiwoom_min2.py** - Alternative minute engine implementation

**Cryptocurrency Engines:**
- **backengine_upbit_tick.py** - Upbit tick-level backtesting
- **backengine_upbit_tick2.py** - Alternative Upbit tick engine
- **backengine_upbit_min.py** - Upbit minute-level backtesting
- **backengine_upbit_min2.py** - Alternative Upbit minute engine
- **backengine_binance_tick.py** - Binance tick-level backtesting
- **backengine_binance_tick2.py** - Alternative Binance tick engine
- **backengine_binance_min.py** - Binance minute-level backtesting
- **backengine_binance_min2.py** - Alternative Binance minute engine

**Pattern:** `backengine_{market}_{timeframe}.py` and `backengine_{market}_{timeframe}2.py` variants

### Validation and Testing
- **back_code_test.py** - Condition code validation
  - Validates strategy code syntax and logic
  - Checks variable range definitions (BO, BOR, SO, SOR)
  - Ensures grid search parameter counts (≤20 per variable)
  - Verifies genetic algorithm range formats
  - Compiles and tests strategy code before execution

- **test_opti_valid_std.py** - Optimization validation with standard deviation
  - Statistical validation of optimization results
  - Standard deviation analysis for robustness
  - Train/validation/test performance comparison

- **rolling_walk_forward_test.py** - Walk-forward analysis
  - Rolling window backtesting
  - Out-of-sample validation
  - Strategy degradation detection over time

### Analysis and Utilities
- **back_analysis_enhanced.py** - Enhanced backtesting analysis
  - Advanced performance metrics calculation
  - Win rate, profit factor, Sharpe ratio analysis
  - Drawdown analysis and recovery periods
  - Trade distribution and pattern analysis

- **back_subtotal.py** - Subtotal aggregation for backtest results
  - Aggregates results across multiple runs
  - Calculates cumulative statistics
  - Generates summary reports

- **back_static.py** - Static helper functions for backtesting
  - `PltShow()` - Visualization generation
  - `GetMoneytopQuery()` - Query top performing parameters
  - `GetBackResult()` - Result extraction from database
  - `GetResultDataframe()` - Convert results to DataFrame
  - `AddMdd()` - Maximum Drawdown calculation
  - `SendTextAndStd()` - UI notification helpers

### Infrastructure and Configuration
- **backtest_icos.py** - ICOS (Integrated Condition Optimization System) integration
  - Automated backtesting workflow
  - Integration with main window scheduler
  - Condition file discovery and loading
  - Results reporting and persistence

- **detail_schema.py** - Detailed database schema definitions
  - Backtesting result table schemas
  - Optimization result table schemas
  - Performance metrics column definitions

- **output_paths.py** - Output path management
  - Centralized backtesting output directory management
  - Result file path generation
  - Organized storage by market/timeframe/date

- **output_manifest.py** - Output file manifest tracking
  - Tracks generated output files
  - Metadata for result files
  - File organization and cleanup utilities

- **variable_registry.py** - Variable registry system
  - Centralized variable definition tracking
  - Maps strategy variables to documentation
  - Supports 826 tick variables and 752 minute variables
  - Ensures consistency with guideline documentation

### Advanced Optimization Tools
- **segment_filter_optimizer.py** - Segment-based optimization
  - Market condition segmentation
  - Conditional optimization (trending vs ranging markets)
  - Adaptive parameter selection

### Development and Debugging
- **_test_lookahead_fix.py** - Lookahead bias testing
  - Validates no future data leakage
  - Tests temporal data integrity
  - Critical for strategy validation

- **_test_metrics_update.py** - Metrics calculation testing
  - Tests performance metric calculations
  - Validates statistical accuracy
  - Unit tests for key metrics

- **_verify_simple.py** - Simple verification script
  - Quick validation of basic backtesting functionality
  - Smoke tests for engine integrity

## Subdirectories

### analysis/
Historical backtesting analysis results and reports. Contains aggregated performance data, comparison studies, and historical test runs.
**Reference:** See `analysis/AGENTS.md` (if exists) for detailed file structure.

### analysis_enhanced/
Advanced analysis outputs with enhanced metrics and visualizations. Includes Sharpe ratio analysis, drawdown studies, trade pattern recognition, and statistical robustness tests.
**Reference:** See `analysis_enhanced/AGENTS.md` (if exists) for detailed methodology.

### graph/
Backtesting visualization outputs. Contains equity curves, drawdown charts, performance heatmaps, and optimization convergence plots.
**Reference:** Generated by `back_static.py:PltShow()` and pyqtgraph rendering.

### iterative_optimizer/
Iterative parameter tuning tools and progressive optimization workflows. Supports multi-stage refinement and adaptive parameter adjustment.
**Reference:** See `iterative_optimizer/AGENTS.md` (if exists) for optimization strategies.

### segment_analysis/
Market segment analysis outputs. Contains performance breakdowns by market condition (trending, ranging, volatile), time of day, and volatility regimes.
**Reference:** Generated by `segment_filter_optimizer.py`.

### backtesting_output/
Primary output directory for all backtesting results. Organized by market, timeframe, strategy, and execution date. Includes CSV exports, performance summaries, and optimization logs.
**Reference:** Managed by `output_paths.py` and `output_manifest.py`.

## For AI Agents

### Understanding Backtesting Architecture

**Multi-Process Design:**
- Main process spawns dedicated backengine processes per market/timeframe
- Queue-based communication (`backQ`) for result aggregation
- Parallel execution across multiple CPU cores for performance
- Separate processes for optimization (grid search vs genetic algorithm)

**Data Flow Pattern:**
```
Historical Data (SQLite) → BackEngine Process → Strategy Execution → Trade Simulation → Performance Metrics → Results Database
                                    ↓
                          Queue Communication (backQ)
                                    ↓
                          Total/Aggregation Process → UI Update → Database Persistence
```

### Backtesting Workflow

**Standard Backtesting Process:**
1. Load strategy conditions from `DB_STRATEGY` (strategy.db)
2. Retrieve historical data from market-specific databases:
   - Tick: `DB_STOCK_BACK_TICK`, `DB_COIN_BACK_TICK`
   - Minute: `DB_STOCK_BACK_MIN`, `DB_COIN_BACK_MIN`
3. Execute strategy logic in appropriate `backengine_*_*.py`
4. Simulate trades with realistic order execution
5. Calculate performance metrics (win rate, profit factor, MDD, Sharpe)
6. Store results to `DB_BACKTEST` (backtest.db)
7. Generate visualizations and reports

**Optimization Process:**
1. Define parameter ranges (BO, BOR, SO, SOR sections in condition docs)
2. Choose optimization method:
   - Grid Search (`optimiz.py`) - Exhaustive search, ≤20 values per variable
   - Genetic Algorithm (`optimiz_genetic_algorithm.py`) - Large parameter spaces
3. Execute parallel optimization across parameter combinations
4. Validate results with train/validation/test splits
5. Store optimal parameters to `DB_OPTUNA` (optuna.db)
6. Update condition documentation with optimized values

### Key Patterns and Conventions

**Engine Selection:**
- Tick strategies: Use `backengine_{market}_tick.py` for second-level execution
- Minute strategies: Use `backengine_{market}_min.py` for minute-level bars
- Alternative engines (`*2.py` variants): Used for specific optimizations or parallel testing

**Variable Management:**
- All strategy variables accessed via `self.vars[N]` dictionary
- Variable ranges defined in condition documentation (BOR, SOR, GAR sections)
- Registry system (`variable_registry.py`) ensures documentation compliance
- 826 documented tick variables, 752 documented minute variables

**Performance Metrics:**
- **수익률 (Profit Rate)**: Total return percentage
- **승률 (Win Rate)**: Percentage of profitable trades
- **평균손익 (Average Profit/Loss)**: Mean P&L per trade
- **MDD (Maximum Drawdown)**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return metric
- **Profit Factor**: Gross profit / gross loss ratio

### Common Operations

**Running Backtests:**
```python
# From UI or direct execution
python backtester/backtest.py

# Via ICOS automated workflow
python backtester/backtest_icos.py
```

**Optimization:**
```python
# Grid search optimization
python backtester/optimiz.py

# Genetic algorithm optimization
python backtester/optimiz_genetic_algorithm.py

# Condition-specific optimization
python backtester/optimiz_conditions.py
```

**Validation:**
```python
# Validate strategy code before backtesting
python backtester/back_code_test.py

# Walk-forward validation
python backtester/rolling_walk_forward_test.py
```

### Database Integration

**Strategy Loading:**
- Strategies stored in `DB_STRATEGY` (strategy.db)
- Buy/sell conditions retrieved by strategy name
- Variable definitions loaded from condition documentation

**Historical Data:**
- Stock tick data: `DB_STOCK_BACK_TICK` (stock_tick.db)
- Stock minute data: `DB_STOCK_BACK_MIN` (stock_min.db)
- Coin tick data: `DB_COIN_BACK_TICK` (coin_tick.db)
- Coin minute data: `DB_COIN_BACK_MIN` (coin_min.db)

**Results Storage:**
- Backtest results: `DB_BACKTEST` (backtest.db)
- Optimization results: `DB_OPTUNA` (optuna.db)
- Performance metrics persisted for analysis and comparison

### Code Modification Guidelines

**When Adding New Engines:**
1. Follow naming convention: `backengine_{market}_{timeframe}.py`
2. Implement queue communication via `backQ` for result reporting
3. Use market-specific data loading from appropriate database
4. Calculate standard performance metrics (win rate, profit, MDD)
5. Support both BO/SO (optimized) and BOR/SOR (range) execution modes
6. Test with `back_code_test.py` before integration

**When Modifying Optimization:**
1. Ensure parameter count limits (≤20 per variable for grid search)
2. Validate range definitions match condition documentation format
3. Test with small parameter spaces before full optimization runs
4. Verify train/validation/test split logic
5. Check results persistence to `DB_OPTUNA`

**When Adding Metrics:**
1. Update `back_static.py` helper functions
2. Add metric calculations to all `backengine_*_*.py` files
3. Update database schema in `detail_schema.py`
4. Document metric definitions and calculations
5. Add visualization support in `PltShow()`

### Performance Considerations

**Optimization:**
- Parallel processing enabled via multiprocessing
- Multiple cores utilized for grid search (default: CPU count - 1)
- Genetic algorithms for large parameter spaces (>10^6 combinations)
- Caching of technical indicator calculations
- Efficient numpy/pandas operations for data processing

**Memory Management:**
- Large historical datasets loaded incrementally
- Result aggregation via queues to avoid memory duplication
- Periodic garbage collection during long optimization runs
- Database connections properly closed after operations

**Bottlenecks:**
- Disk I/O for historical data loading (use SSD if possible)
- Strategy complexity impacts execution time
- Number of parameter combinations in grid search
- Historical data volume (tick data > minute data)

### Debugging and Troubleshooting

**Common Issues:**
- **Lookahead Bias**: Validate with `_test_lookahead_fix.py`
- **Parameter Range Errors**: Check BOR/SOR definitions with `back_code_test.py`
- **Database Locks**: Ensure proper connection management in multi-process environment
- **Queue Communication Failures**: Verify process lifecycle and queue passing
- **Optimization Not Converging**: Check fitness function and parameter ranges

**Validation Steps:**
1. Run `back_code_test.py` to validate strategy code syntax
2. Execute `_verify_simple.py` for basic functionality checks
3. Test with small date ranges before full historical backtests
4. Compare results across `*2.py` engine variants for consistency
5. Verify documentation compliance (98.3% standard)

**Logging and Monitoring:**
- Progress tracking via queue messages to UI
- Performance metrics logged to `/_log/` directory
- Database query logging for debugging data issues
- Telegram notifications for long-running optimizations (via `teleQ`)

### Integration Points

**UI Integration:**
- Backtest results displayed in main window tables
- Progress bars updated via `windowQ` queue messages
- Charts rendered via `chartQ` for equity curves
- UI event handlers in `ui/ui_button_clicked_*.py`

**Strategy Integration:**
- Strategy code loaded from condition files (`/docs/Condition/`)
- Variable definitions from documentation (BO, BOR, SO, SOR, OR, GAR)
- Technical indicators from `utility.setting.indicator`
- Shared functions from `utility/static.py`

**Database Integration:**
- All backtests coordinated through `utility/query.py` via `queryQ`
- Database paths managed in `utility/setting.py`
- Schema definitions in `detail_schema.py`
- Integrity checks via `utility/database_check.py` on startup

### Quality Standards

**Documentation Compliance:**
- All condition files must have BO, BOR, SO, SOR sections
- Variable ranges must be documented (current: 98.3% compliance)
- Code references must link to source files
- Optimization results should update condition documentation

**Code Quality:**
- All strategy code must pass `back_code_test.py` validation
- No lookahead bias (validate with `_test_lookahead_fix.py`)
- Metrics calculations verified with `_test_metrics_update.py`
- Performance benchmarking for optimization efficiency

**Testing Requirements:**
- Walk-forward validation for production strategies
- Out-of-sample testing with train/validation/test splits
- Statistical significance of optimization results
- Robustness testing across market conditions (segment analysis)

### Advanced Features

**ICOS Integration:**
- Automated backtesting scheduler integration
- Condition file auto-discovery and loading
- Results persistence and reporting
- Triggered via main window scheduler or manual execution

**Segment Analysis:**
- Market regime detection (trending, ranging, volatile)
- Conditional optimization for specific market conditions
- Time-of-day performance analysis
- Volatility-adjusted parameter selection

**Iterative Optimization:**
- Multi-stage parameter refinement
- Progressive narrowing of search space
- Adaptive learning from previous optimization runs
- Convergence tracking and early stopping

## Dependencies

**Core Libraries:**
- **optuna** - Hyperparameter optimization framework for grid search
- **cmaes** - Covariance Matrix Adaptation Evolution Strategy for genetic algorithms
- **numpy** (v1.26.4) - Numerical computing and array operations
- **pandas** (v2.0.3) - DataFrame operations and data manipulation
- **sqlite3** - Database connectivity for historical data and results
- **multiprocessing** - Parallel execution across CPU cores
- **pyqtgraph** - Real-time chart rendering for equity curves

**Technical Analysis:**
- **TA-Lib** (custom wheel) - Technical indicator calculations
- **utility.setting.indicator** - Custom indicator definitions

**Internal Dependencies:**
- `utility/static.py` - Helper functions (datetime, threading, encryption)
- `utility/setting.py` - Database paths, configuration, API credentials
- `utility/query.py` - Queue-based database operations
- `back_static.py` - Backtesting-specific helper functions

**Database Files:**
- `strategy.db` - Strategy definitions and conditions
- `backtest.db` - Backtesting results and performance metrics
- `optuna.db` - Optimization results and parameter tuning history
- `stock_tick.db` / `stock_min.db` - Stock historical data
- `coin_tick.db` / `coin_min.db` - Cryptocurrency historical data

## Related Documentation

- `/docs/Guideline/Back_Testing_Guideline_Tick.md` - 826 documented tick variables
- `/docs/Guideline/Back_Testing_Guideline_Min.md` - 752 documented minute variables
- `/docs/Condition/` - Trading condition files (133 files, 98.3% compliance)
- `/docs/CodeReview/Backtesting_Data_Loading_Multicore_Analysis.md` - Performance analysis
- `/docs/Manual/08_Backtesting/` - User manual for backtesting workflows
- `CLAUDE.md` - Project overview and development guidelines

---

**Note for AI Agents:** This module is the core of STOM's strategy validation and optimization. Always validate strategy code with `back_code_test.py` before execution, ensure documentation compliance (98.3% standard), and test for lookahead bias. Backtesting is CPU-intensive; use parallel processing and consider memory constraints when working with large historical datasets. The queue-based architecture requires proper process lifecycle management to avoid deadlocks.
