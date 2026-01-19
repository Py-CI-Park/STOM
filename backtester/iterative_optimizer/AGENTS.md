<!-- Parent: ../AGENTS.md -->
# backtester/iterative_optimizer

## Purpose
Parameter tuning and iterative optimization system (ICOS - Iterative Condition Optimization System). Solves prediction-reality gap by using actual backtests instead of ML predictions for progressive strategy refinement.

## Key Files

### Core System (Phase 1-7)
- `__init__.py` - Package API and version (v0.7.0)
- `config.py` - Configuration classes and presets (conservative, aggressive, quick)
- `data_types.py` - Common data structures (FilterCandidate, IterationResult)
- `runner.py` - Main orchestrator (IterativeOptimizer, IterativeResult)

### Analysis & Generation (Phase 2)
- `analyzer.py` - ResultAnalyzer for loss pattern detection
- `filter_generator.py` - FilterGenerator with priority scoring

### Condition Building (Phase 3)
- `condition_builder.py` - ConditionBuilder for strategy code generation
- `storage.py` - IterationStorage for persistence

### Comparison & Convergence (Phase 4)
- `comparator.py` - ResultComparator for metric comparison
- `convergence.py` - ConvergenceChecker for stopping criteria

### Synchronous Execution (Phase 7)
- `backtest_sync.py` - SyncBacktestRunner for multicore backtest integration

## Subdirectories
- `optimization/` - Optimization algorithms
  - `base.py` - BaseOptimizer abstract class
  - `grid_search.py` - GridSearchOptimizer
  - `genetic.py` - GeneticOptimizer
  - `bayesian.py` - BayesianOptimizer
  - `walk_forward.py` - WalkForwardValidator
  - `__init__.py` - Exports all optimizers

## For AI Agents
When working with iterative optimization:

### System Philosophy
- **Measurement over Prediction**: Real backtests replace ML filter predictions
- **Iterative Refinement**: Convergence through repeated testing
- **Integration**: Works with existing multicore backtest infrastructure
- **Modularity**: Each component independently testable

### Usage Pattern
```python
from backtester.iterative_optimizer import IterativeOptimizer, IterativeConfig

config = IterativeConfig(
    enabled=True,
    max_iterations=5,
    convergence_method="plateau",
)
optimizer = IterativeOptimizer(config)
result = optimizer.run(buystg, sellstg)

if result.success:
    print(f"Improvement: {result.total_improvement:.2%}")
    print(f"Final strategy: {result.final_buystg[:100]}...")
```

### Phase Workflow
1. **Phase 1**: Config & Runner setup
2. **Phase 2**: Analyze baseline → Generate filter candidates
3. **Phase 3**: Build new conditions → Store iterations
4. **Phase 4**: Compare results → Check convergence
5. **Phase 5**: Advanced optimization (Grid/GA/Bayesian)
6. **Phase 6**: Walk-forward validation
7. **Phase 7**: Synchronous backtest execution

### Configuration
Three presets available:
- `PRESET_CONSERVATIVE` - Safe, fewer iterations
- `PRESET_AGGRESSIVE` - Maximum optimization
- `PRESET_QUICK_TEST` - Fast development testing

### Convergence Methods
- `plateau` - Stop when improvement stalls
- `threshold` - Stop at target improvement level
- `combined` - Use both criteria

### Optimization Methods
- `grid_search` - Exhaustive parameter search
- `genetic` - Evolutionary algorithm
- `bayesian` - Probabilistic optimization
- `walk_forward` - Time-series validation

### Filter Metrics
- `win_rate` - 승률 (win rate)
- `profit_factor` - 수익률 (profit rate)
- `sharpe` - Sharpe ratio
- `mdd` - Maximum drawdown

### Storage
- Results saved to `_icos_results/` directory
- JSON metadata with full configuration
- Iteration history for analysis
- Generated code saved to `.txt` files

### Integration Points
- `SyncBacktestRunner` bridges to multicore backtester
- Compatible with existing strategy format
- Uses same database schema (`strategy.db`)
- Outputs to `backtesting_output/` directory

## Dependencies
- numpy/pandas - Data processing
- optuna - Bayesian optimization
- All dependencies from `backtester/analysis/`
- Multicore backtesting system (via `SyncBacktestRunner`)

## Branch Information
- Development branch: `feature/iterative-condition-optimizer`
- Current version: 0.7.0
- Author: STOM Development Team
- Created: 2026-01-12
