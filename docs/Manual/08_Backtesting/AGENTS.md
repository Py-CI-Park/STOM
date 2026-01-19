<!-- Parent: ../AGENTS.md -->
# Backtesting System Documentation

## Purpose

Comprehensive documentation of STOM's backtesting framework, covering historical data testing engines, parameter optimization systems (grid search and genetic algorithms), performance metrics calculation, and strategy validation. This section provides complete technical reference for testing and optimizing trading strategies before live deployment.

## Key Files

- **backtesting_system.md** - Complete backtesting framework documentation covering:
  - 12 market-specific engines (backengine_*_*.py - market × timeframe combinations)
  - Grid search optimization (backtester/optimiz.py)
  - Genetic algorithm optimization (backtester/optimiz_genetic_algorithm.py)
  - Performance metrics and validation
  - Strategy parameter tuning methodologies
  - Walk-forward testing and validation
  - Backtesting orchestration (backtester/backtest.py)

## For AI Agents

### Maintaining This Section

**When to Update:**
- New backtesting engines added (new markets or timeframes)
- Optimization algorithms modified or added
- Performance metrics calculations changed
- Validation methodologies updated
- Parallel processing approach modified
- Result storage schema changed

**Critical Validation Points:**

1. **Backtesting Engine Files** - Verify 12 market-specific engines:
   ```bash
   # Stock engines (tick and minute)
   ls backtester/backengine_stock_tick.py
   ls backtester/backengine_stock_min.py

   # Crypto engines (Upbit and Binance, tick and minute)
   ls backtester/backengine_upbit_tick.py
   ls backtester/backengine_upbit_min.py
   ls backtester/backengine_binance_tick.py
   ls backtester/backengine_binance_min.py

   # Additional specialized engines
   ls backtester/backengine_*.py | wc -l  # Should be 12 engines
   ```

2. **Optimization Scripts** - Confirm optimization implementations:
   ```bash
   ls backtester/optimiz.py                      # Grid search
   ls backtester/optimiz_genetic_algorithm.py    # GA optimization
   ls backtester/backtest.py                     # Orchestrator
   ```

3. **Guideline Compliance** - Verify guideline references:
   ```bash
   # Backtesting guidelines define variable structures
   ls docs/Guideline/Back_Testing_Guideline_Tick.md  # 826 variables
   ls docs/Guideline/Back_Testing_Guideline_Min.md   # 752 variables
   ```

4. **Result Storage** - Confirm database schema:
   ```python
   # backtest.db - Backtesting results
   # optuna.db - Optimization trial results
   # Reference: docs/Manual/06_Data/data_management.md
   ```

**Update Guidelines:**
1. **Read Before Editing** - Always read `backtesting_system.md` completely
2. **Verify Engine Count** - Maintain accurate count of 12 engines
3. **Test Optimization** - Validate optimization examples execute correctly
4. **Check Metrics** - Ensure performance metric formulas accurate
5. **Update Guidelines** - Coordinate with Back_Testing_Guideline_*.md

### Code-Documentation Alignment

**Key Source References:**

**Backtesting Orchestration:**
```python
backtester/backtest.py - Main orchestrator
- Strategy loading and validation
- Historical data loading
- Engine selection and execution
- Result aggregation
- Performance reporting
```

**Market-Specific Engines:**
```python
# Stock market engines
backtester/backengine_stock_tick.py - Stock tick backtesting
backtester/backengine_stock_min.py - Stock minute backtesting

# Upbit cryptocurrency
backtester/backengine_upbit_tick.py - Upbit tick backtesting
backtester/backengine_upbit_min.py - Upbit minute backtesting

# Binance cryptocurrency
backtester/backengine_binance_tick.py - Binance tick backtesting
backtester/backengine_binance_min.py - Binance minute backtesting

# Pattern: backengine_{market}_{timeframe}.py
```

**Optimization Engines:**
```python
backtester/optimiz.py - Grid search optimization
- Parameter range definitions (BOR, SOR sections)
- Exhaustive search across parameter space
- Parallel execution support
- Best parameter selection

backtester/optimiz_genetic_algorithm.py - GA optimization
- Genetic algorithm implementation
- Fitness function definitions
- Population management
- Convergence criteria
- GAR range usage
```

**Validation and Testing:**
```python
backtester/back_code_test.py - Condition code validation
backtester/backfinder.py - Strategy discovery and testing
```

**Validation Checklist:**
- [ ] Engine count is 12 (markets × timeframes)
- [ ] Optimization methods documented accurately
- [ ] Performance metrics match calculations
- [ ] Guideline references valid (826 tick, 752 minute variables)
- [ ] Database schema references current
- [ ] Parameter sections (BO, BOR, SO, SOR, OR, GAR) documented
- [ ] Multicore usage described accurately

### Content Structure

**Standard Sections in backtesting_system.md:**
1. **Backtesting Architecture** - System overview
   - Orchestration process (backtest.py)
   - Engine selection logic
   - Data flow (historical DB → engine → results)
   - Multicore parallelization
2. **Backtesting Engines** - Market-specific implementations
   - 12 engine descriptions (market × timeframe matrix)
   - Engine capabilities and limitations
   - Data preprocessing
   - Order simulation
3. **Parameter Optimization** - Tuning methodologies
   - Grid search (optimiz.py) - Exhaustive parameter space search
   - Genetic algorithms (optimiz_genetic_algorithm.py) - Evolutionary optimization
   - Parameter sections: BO, BOR, SO, SOR, OR, GAR
   - Walk-forward validation
   - Overfitting prevention
4. **Performance Metrics** - Evaluation criteria
   - Return metrics (total return, CAGR, Sharpe ratio)
   - Risk metrics (max drawdown, volatility, VaR)
   - Trade metrics (win rate, profit factor, avg win/loss)
   - Benchmark comparison
5. **Strategy Validation** - Testing methodologies
   - In-sample vs. out-of-sample testing
   - Walk-forward analysis
   - Monte Carlo simulation
   - Robustness testing
6. **Result Storage and Analysis** - Database integration
   - backtest.db schema
   - optuna.db for optimization trials
   - Result aggregation
   - Performance reporting
7. **Best Practices** - Optimization guidelines
   - Parameter range selection
   - Sample period selection
   - Overfitting detection
   - Strategy refinement workflow

**What Belongs Here:**
- Backtesting engine implementations
- Optimization algorithms
- Performance metrics
- Validation methodologies
- Historical data testing
- Parameter tuning approaches

**What Belongs Elsewhere:**
- Live trading execution → `07_Trading/`
- Historical data storage → `06_Data/`
- Strategy documentation → `../Condition/`
- Guideline specifications → `../Guideline/`
- Module implementation → `03_Modules/backtester_module.md`

### Common Updates

**Adding New Backtesting Engine:**
1. Document market and timeframe combination
2. Describe engine-specific features
3. Note data requirements
4. Update engine count (increment from 12)
5. Add to backengine_*_*.py pattern documentation
6. Document order simulation specifics

**Modifying Optimization Algorithm:**
1. Document algorithm changes
2. Update parameter section references (BOR, SOR, GAR)
3. Describe performance implications
4. Update examples
5. Note convergence criteria changes

**Adding Performance Metric:**
1. Document metric purpose and interpretation
2. Provide calculation formula
3. Note data requirements
4. Update result storage schema if needed
5. Add to performance reporting documentation

**Updating Validation Methodology:**
1. Document new validation approach
2. Describe when to use it
3. Provide examples
4. Note computational requirements
5. Compare to existing methodologies

## Dependencies

**Related Manual Sections:**
- `02_Architecture/` - Backtesting process architecture
- `03_Modules/backtester_module.md` - Detailed backtester implementation
- `06_Data/` - Historical data databases and result storage
- `07_Trading/` - Live trading strategies tested here

**Source Code References:**
- `backtester/backtest.py` - Orchestration
- `backtester/backengine_*_*.py` - 12 market-specific engines
- `backtester/optimiz.py` - Grid search optimization
- `backtester/optimiz_genetic_algorithm.py` - GA optimization
- `backtester/back_code_test.py` - Code validation
- `backtester/backfinder.py` - Strategy discovery

**Guideline Documentation:**
- `../Guideline/Back_Testing_Guideline_Tick.md` (33KB, 826 variables)
- `../Guideline/Back_Testing_Guideline_Min.md` (25KB, 752 variables)
- Define variable structures for tick and minute strategies

**Condition Documentation:**
- `../Condition/Tick/` - 72 tick strategy conditions
- `../Condition/Min/` - 61 minute strategy conditions
- Each condition file includes optimization sections (BOR, SOR, GAR)

**Documentation Network:**
- Parent: `../AGENTS.md` - Manual documentation standards
- Guidelines: `../../Guideline/Back_Testing_Guideline_*.md` - Variable structures
- Conditions: `../../Condition/` - Individual strategy specifications with optimization ranges

## Special Considerations

### Parameter Optimization Sections
**CRITICAL:** Strategy condition files use standardized sections:

**BO (Buy Optimization)** - Actual optimized buy conditions with values
**BOR (Buy Optimization Range)** - Grid search ranges `[min, max, step]`
**SO (Sell Optimization)** - Actual optimized sell conditions with values
**SOR (Sell Optimization Range)** - Grid search ranges `[min, max, step]`
**OR (Overall Range)** - Top 10 critical variables only
**GAR (Genetic Algorithm Range)** - GA ranges `[min, max]` format

Document these sections and their usage in optimization.

### Backtesting Engine Matrix
**12 Engines:** Market (Stock, Upbit, Binance) × Timeframe (Tick, Minute) = 6 base combinations, plus specialized engines

Document matrix clearly:
```
Stock:   backengine_stock_tick.py, backengine_stock_min.py
Upbit:   backengine_upbit_tick.py, backengine_upbit_min.py
Binance: backengine_binance_tick.py, backengine_binance_min.py
...
```

Maintain accurate engine count.

### Grid Search vs. Genetic Algorithm
Document optimization method selection:

**Grid Search (optimiz.py):**
- Exhaustive parameter space search
- Uses BOR and SOR sections
- Computationally expensive but thorough
- Best for small parameter spaces
- Parallel execution support

**Genetic Algorithm (optimiz_genetic_algorithm.py):**
- Evolutionary optimization
- Uses GAR sections
- More efficient for large parameter spaces
- May miss global optimum
- Iterative refinement

Provide selection guidance.

### Overfitting Prevention
**CRITICAL:** Document overfitting detection and prevention:

1. **In-Sample vs. Out-of-Sample** - Split data for validation
2. **Walk-Forward Testing** - Rolling window validation
3. **Parameter Stability** - Test parameter sensitivity
4. **Simplicity Bias** - Prefer simpler strategies
5. **Multiple Markets** - Test across different markets
6. **Statistical Significance** - Ensure sufficient sample size

### Performance Metric Formulas
Document all metric calculations:

**Total Return:**
```
Total Return = (Final Equity - Initial Equity) / Initial Equity × 100%
```

**CAGR (Compound Annual Growth Rate):**
```
CAGR = ((Final Equity / Initial Equity)^(1 / Years)) - 1
```

**Sharpe Ratio:**
```
Sharpe = (Average Return - Risk-Free Rate) / Standard Deviation of Returns
```

**Maximum Drawdown:**
```
Max DD = (Trough Value - Peak Value) / Peak Value × 100%
```

**Win Rate:**
```
Win Rate = (Winning Trades / Total Trades) × 100%
```

**Profit Factor:**
```
Profit Factor = Gross Profit / Gross Loss
```

### Historical Data Requirements
Document data requirements for backtesting:
- Minimum data points for statistical significance
- Data quality requirements
- Missing data handling
- Data preprocessing steps
- Timestamp alignment across markets

### Order Simulation
Document order simulation approach:
- Fill assumptions (immediate, delayed, slippage)
- Commission modeling
- Slippage modeling
- Market impact modeling
- Order rejection scenarios

### Multicore Parallelization
Document parallel processing:
- Parameter combinations distributed across cores
- Result aggregation
- Resource management
- Progress monitoring
- Error handling in parallel execution

Reference `/lecture/testcode/` for performance comparisons.

### Result Storage Schema
Document result database schema:

**backtest.db tables:**
- Strategy parameters tested
- Performance metrics calculated
- Trade-by-trade results
- Equity curves
- Drawdown periods

**optuna.db tables:**
- Optimization trials
- Parameter combinations tested
- Objective function values
- Convergence history

### Walk-Forward Validation
Document walk-forward testing:
1. Split data into in-sample and out-of-sample periods
2. Optimize on in-sample data
3. Validate on out-of-sample data
4. Roll window forward
5. Repeat process
6. Aggregate results

Provide example timeline and parameters.

### Strategy Refinement Workflow
Document iterative improvement process:
1. Initial strategy hypothesis
2. Backtest on historical data
3. Analyze performance metrics
4. Optimize parameters
5. Validate on out-of-sample data
6. Refine strategy logic
7. Repeat until satisfactory
8. Deploy to paper trading
9. Monitor live performance
10. Adjust based on live results

### Benchmark Comparison
Document benchmark selection:
- Buy-and-hold for stock strategies
- Market index for comparison
- Risk-adjusted return comparison
- Statistical significance testing

### Monte Carlo Simulation
Document Monte Carlo validation:
- Trade sequence randomization
- Bootstrap resampling
- Confidence interval estimation
- Worst-case scenario analysis

### Condition Documentation Sync
**CRITICAL:** Backtesting documentation must align with condition files:
- Parameter ranges match BOR/SOR/GAR sections
- Variable counts match guidelines (826 tick, 752 minute)
- Optimization results documented in condition files
- 98.3% compliance rate maintained

Cross-reference `../Condition/` documentation.

### Testing Before Live Deployment
Document pre-deployment checklist:
1. Backtest on multiple time periods
2. Walk-forward validation passed
3. Out-of-sample performance acceptable
4. Parameter stability verified
5. Risk metrics within limits
6. Code validation passed (back_code_test.py)
7. Condition documentation complete
8. Paper trading results satisfactory

### Performance Reporting
Document reporting capabilities:
- Equity curve visualization
- Drawdown charts
- Trade distribution analysis
- Monthly/yearly returns table
- Risk-adjusted metrics
- Benchmark comparison
- Parameter sensitivity analysis

### Common Pitfalls
Document common backtesting mistakes:
- Look-ahead bias
- Survivorship bias
- Curve-fitting/overfitting
- Insufficient data
- Unrealistic fill assumptions
- Ignoring transaction costs
- Testing on same data used for optimization

Provide detection and avoidance strategies.
