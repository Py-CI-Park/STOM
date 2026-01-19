<!-- Parent: ../AGENTS.md -->
# backtester/iterative_optimizer/optimization

## Purpose
Optimization algorithm implementations for the Iterative Condition Optimization System (ICOS). Provides multiple strategies for parameter tuning and filter combination optimization to progressively refine trading strategies.

## Key Files

### Base Infrastructure
- `__init__.py` - Package exports (v0.1.0) - All optimizers and result types
- `base.py` - Abstract base classes:
  - `BaseOptimizer` - Common optimizer interface
  - `OptimizationResult` - Unified result structure
  - `OptimizationTrial` - Single trial representation
  - `OptimizationStatus` - Lifecycle state management
  - `SearchSpace` - Parameter space definition

### Grid Search Optimizer
- `grid_search.py` - Exhaustive parameter exploration:
  - `GridSearchOptimizer` - Systematic search through all parameter combinations
  - `GridSearchConfig` - Grid resolution, max combinations, early stopping
  - **Use Case**: Comprehensive exploration with manageable parameter spaces
  - **Advantages**: Guarantees finding global optimum in discrete space
  - **Limitations**: Exponential complexity with parameter count

### Genetic Algorithm Optimizer
- `genetic.py` - Evolutionary filter optimization:
  - `GeneticOptimizer` - Selection, crossover, mutation for filter evolution
  - `GeneticConfig` - Population size, generations, crossover/mutation rates
  - `Individual` - Chromosome representation
  - **Use Case**: Large parameter spaces with complex interactions
  - **Advantages**: Explores diverse solution space efficiently
  - **Limitations**: May converge to local optima

### Bayesian Optimizer
- `bayesian.py` - Probabilistic optimization via Optuna:
  - `BayesianOptimizer` - TPE (Tree-structured Parzen Estimator) algorithm
  - `BayesianConfig` - Trial count, timeout, warmup, pruning settings
  - **Use Case**: Expensive evaluation functions (long backtests)
  - **Advantages**: Sample efficiency, uncertainty quantification
  - **Limitations**: Requires optuna dependency
  - **Dependency**: `optuna`, `TPESampler`, `MedianPruner`

### Walk-Forward Validator
- `walk_forward.py` - Overfitting prevention through time-series validation:
  - `WalkForwardValidator` - Rolling window train/test splitting
  - `WalkForwardResult` - Multi-fold validation metrics
  - `FoldResult` - Individual fold performance
  - `OverfitLevel` - Train-test gap classification (none/low/moderate/high/severe)
  - **Use Case**: Final validation before deployment
  - **Advantages**: Realistic out-of-sample performance estimation
  - **Limitations**: Reduces effective training data

## For AI Agents

### Algorithm Selection Guide

**When to use Grid Search:**
- ≤5 parameters with discrete ranges
- Need guaranteed optimal solution
- Computational budget allows exhaustive search
- Baseline comparison before advanced methods

**When to use Genetic Algorithm:**
- 5-20 parameters with complex interactions
- Discrete or mixed parameter spaces
- Good enough solution acceptable (not guaranteed optimal)
- Prior knowledge for initial population available

**When to use Bayesian Optimization:**
- Expensive backtest evaluation (>10 seconds per trial)
- Continuous parameter spaces
- Need uncertainty estimates
- Limited evaluation budget (<100 trials)

**When to use Walk-Forward:**
- Always use for final validation
- Check overfitting after any optimization
- Assess strategy robustness across time periods
- Prepare for production deployment

### Implementation Patterns

**Basic Optimization:**
```python
from backtester.iterative_optimizer.optimization import (
    GridSearchOptimizer,
    GridSearchConfig,
)

config = GridSearchConfig(
    resolution=10,
    max_combinations=1000,
    early_stop_no_improve=50,
)
optimizer = GridSearchOptimizer(config)
result = optimizer.optimize(candidates, eval_func)

print(f"Best score: {result.best_score:.4f}")
print(f"Best filters: {result.best_filters}")
```

**Genetic Algorithm:**
```python
from backtester.iterative_optimizer.optimization import (
    GeneticOptimizer,
    GeneticConfig,
)

config = GeneticConfig(
    population_size=50,
    n_generations=20,
    crossover_rate=0.8,
    mutation_rate=0.1,
    elite_ratio=0.1,
)
optimizer = GeneticOptimizer(config)
result = optimizer.optimize(candidates, eval_func)
```

**Bayesian Optimization:**
```python
from backtester.iterative_optimizer.optimization import (
    BayesianOptimizer,
    BayesianConfig,
)

config = BayesianConfig(
    n_trials=100,
    n_startup_trials=10,
    multivariate=True,
    use_pruner=True,
)
optimizer = BayesianOptimizer(config)
result = optimizer.optimize(candidates, eval_func)
```

**Walk-Forward Validation:**
```python
from backtester.iterative_optimizer.optimization import WalkForwardValidator

validator = WalkForwardValidator(
    n_folds=5,
    train_ratio=0.8,
)
wf_result = validator.validate(best_filters, best_params, data)

print(f"Overfitting level: {wf_result.overfitting_level}")
print(f"Average test score: {wf_result.avg_test_score:.4f}")
print(f"Score degradation: {wf_result.score_degradation:.2%}")
```

### Common Optimization Workflow

1. **Initial Exploration (Grid Search)**:
   - Define coarse parameter ranges
   - Run grid search with low resolution (5-10 points)
   - Identify promising regions

2. **Refinement (Genetic or Bayesian)**:
   - Narrow parameter ranges based on initial results
   - Use GA for discrete spaces, Bayesian for continuous
   - Iterate until convergence

3. **Validation (Walk-Forward)**:
   - Apply walk-forward to best configuration
   - Check overfitting level
   - If overfitting HIGH/SEVERE, add regularization or simplify filters

4. **Final Selection**:
   - Choose configuration with best out-of-sample performance
   - Document parameter sensitivity
   - Set confidence intervals from walk-forward results

### Integration with ICOS Runner

Optimizers are called by `runner.py` in Phase 5:
```python
# In IterativeOptimizer.run()
if self.config.optimization_method == "grid_search":
    result = self.grid_optimizer.optimize(...)
elif self.config.optimization_method == "genetic":
    result = self.genetic_optimizer.optimize(...)
elif self.config.optimization_method == "bayesian":
    result = self.bayesian_optimizer.optimize(...)

# Always validate with walk-forward
wf_result = self.validator.validate(result.best_filters, ...)
```

### Performance Considerations

**Grid Search:**
- Time complexity: O(n^d) where n=resolution, d=dimensions
- Memory: O(n^d) for result storage
- Parallelizable: Yes (independent evaluations)

**Genetic Algorithm:**
- Time complexity: O(p * g * e) where p=population, g=generations, e=eval_time
- Memory: O(p) for population storage
- Parallelizable: Partially (fitness evaluation)

**Bayesian Optimization:**
- Time complexity: O(t * e) where t=trials, e=eval_time
- Memory: O(t) for trial history
- Parallelizable: Limited (sequential sampling)

**Walk-Forward:**
- Time complexity: O(f * o) where f=folds, o=optimization_time
- Memory: O(f * d) where d=data_size
- Parallelizable: Yes (fold-level)

### Error Handling

All optimizers follow consistent error patterns:
- Return `OptimizationStatus.FAILED` on evaluation errors
- Log warnings for parameter constraint violations
- Gracefully handle early stopping conditions
- Preserve best solution if interrupted

### Extension Points

**Adding New Optimizer:**
1. Inherit from `BaseOptimizer`
2. Implement `optimize()` method signature
3. Return `OptimizationResult` with required fields
4. Add to `__init__.py` exports
5. Document in this file

**Custom Evaluation Function:**
```python
def custom_eval(filters: List[FilterCandidate],
                params: Dict[str, Any]) -> float:
    # Must return single scalar score (higher is better)
    # Can access backtester via SyncBacktestRunner
    pass

result = optimizer.optimize(candidates, custom_eval)
```

### Debugging Tips

- Enable optimizer logging: Set `logging.DEBUG` level
- Check trial history: `result.trials` contains all attempts
- Validate search space: Ensure parameter ranges are reasonable
- Monitor convergence: Plot `result.score_history`
- Profile evaluation: Time single `eval_func` call

## Dependencies

### Required
- `numpy` - Numerical operations
- `pandas` - Data manipulation (walk-forward splitting)
- `itertools` - Grid generation
- `random`, `copy` - Genetic algorithm operations

### Optional
- `optuna>=3.0` - Bayesian optimization (BayesianOptimizer only)
- `cmaes` - CMA-ES sampler for optuna
- `matplotlib` - Visualization (if plotting enabled)

### Internal
- `..config` - `IterativeConfig`, `FilterMetric`, `ValidationConfig`
- `..data_types` - `FilterCandidate`, `IterationResult`
- `..backtest_sync` - `SyncBacktestRunner` for evaluation

## Algorithm References

**Grid Search:**
- Exhaustive search strategy
- Standard ML/optimization baseline

**Genetic Algorithm:**
- Holland, J. H. (1992). "Adaptation in Natural and Artificial Systems"
- Tournament selection, single-point crossover, uniform mutation

**Bayesian Optimization:**
- Bergstra, J. et al. (2011). "Algorithms for Hyper-Parameter Optimization"
- TPE (Tree-structured Parzen Estimator)
- Optuna framework: https://optuna.org/

**Walk-Forward Analysis:**
- Pardo, R. (2008). "The Evaluation and Optimization of Trading Strategies"
- Rolling window methodology for time-series validation
- Industry standard for trading strategy validation
