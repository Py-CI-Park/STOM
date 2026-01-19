<!-- Parent: ../AGENTS.md -->
# Trading Condition Studies

## Purpose

This directory contains deep analysis of specific trading strategies and condition performance evaluation. It serves as the central repository for:

- **Strategy Performance Analysis**: Statistical validation of trading condition effectiveness
- **Overfitting Risk Assessment**: Identification of conditions with insufficient sample sizes
- **Condition Conflict Detection**: Finding incompatible or contradictory strategy parameters
- **Market Behavior Research**: Analysis of opening sessions, intraday patterns, volatility characteristics
- **Sample Size Validation**: Ensuring statistical significance of backtesting results

**Key Focus Areas**:
- Market opening 5-minute strategies (conditions 902-905)
- Tick-level vs minute-level condition comparison
- Train/validation/test split consistency
- Overfitting detection (17 high-risk conditions identified)
- Statistical significance testing

## Key Files

### Deep Strategy Analysis

**Condition_902_905_Update_2_Deep_Analysis.md** (44KB)
- Comprehensive analysis of market opening 5-minute strategy
- 17 conditions flagged for overfitting risk
- Sample size insufficiency identified (some conditions <100 trades)
- Conflict detection between tick and minute conditions
- Statistical validation with t-tests and effect size calculations
- Walk-forward test results and stability metrics

**Key Findings**:
- **Overfitting Criteria**: 6 judgment indicators (sample size, profit stability, condition conflicts)
- **High-Risk Conditions**: 17 conditions with <300 trades in validation set
- **Conflict Analysis**: Incompatible parameter ranges between tick/minute strategies
- **Recommendations**: Increase data collection period, apply stricter validation thresholds

### Research Notes

**Condition_Tick_902_905_update_2_Study.md** (10KB)
- Initial research notes for tick condition 902-905 updates
- Preliminary observations on strategy behavior
- Data collection requirements
- Testing methodology design

## For AI Agents

### When Adding Condition Study Documents

1. **File Naming Convention**: Use `Condition_[ID]_[Name]_[Analysis_Type].md` format
   - Examples: `Condition_902_905_Update_2_Deep_Analysis.md`, `Condition_Tick_850_Breakout_Study.md`
2. **Document Structure**: Include the following sections:
   - **Overview**: Condition purpose, timeframe, target market
   - **Data Analysis**: Sample sizes, date ranges, market conditions
   - **Statistical Validation**: Significance tests, effect sizes, confidence intervals
   - **Overfitting Assessment**: Sample size adequacy, profit stability, cross-validation results
   - **Conflict Detection**: Parameter inconsistencies with related conditions
   - **Performance Metrics**: Win rate, profit factor, Sharpe ratio, max drawdown
   - **Conclusions**: Risk level, recommendations, implementation guidance
3. **Cross-Reference**: Link to condition document in `docs/Condition/Tick/` or `docs/Condition/Min/`
4. **Update Parent README.md**: Add entry to comprehensive study summary table
5. **Evidence-Based**: Include tables, charts, statistical test results

### When Analyzing Trading Conditions

1. **Pre-Analysis Checklist**:
   - Read condition document (BO, BOR, SO, SOR, OR, GAR sections)
   - Verify guideline compliance (98.3% target)
   - Load backtesting results from `backtest.db`
   - Check related conditions for conflicts
   - Review variable definitions (826 tick variables, 752 minute variables)

2. **Statistical Validation Process**:
   ```python
   # Sample Size Requirements (from Guides/New_Metrics_Development_Process_Guide.md)
   minimum_trades = 300  # Per segment (train/val/test)
   minimum_days = 60     # Data collection period

   # Overfitting Risk Assessment (6 indicators)
   1. Sample size < 300 trades → HIGH RISK
   2. Train-val profit difference > 30% → HIGH RISK
   3. Validation period < 3 months → MEDIUM RISK
   4. Condition count > 10 parameters → MEDIUM RISK
   5. Parameter ranges too narrow → HIGH RISK
   6. Cross-validation instability > 20% → HIGH RISK
   ```

3. **Conflict Detection Algorithm**:
   - **Parameter Range Conflicts**: BO values outside BOR ranges
   - **Logic Conflicts**: Buy and sell conditions that never trigger together
   - **Timeframe Conflicts**: Tick conditions incompatible with minute aggregation
   - **Market Condition Conflicts**: Strategies that contradict market regime filters

4. **Performance Evaluation Metrics**:
   - **Profitability**: Total profit, profit per trade, profit factor
   - **Consistency**: Win rate, consecutive wins/losses, profit stability
   - **Risk**: Max drawdown, Sharpe ratio, Sortino ratio, Calmar ratio
   - **Efficiency**: Trade frequency, holding period, capital utilization
   - **Robustness**: Walk-forward results, out-of-sample performance, sensitivity analysis

5. **Overfitting Prevention**:
   - Apply Bonferroni/FDR correction for multiple hypothesis testing
   - Use purged K-fold cross-validation for time series
   - Implement walk-forward analysis with rolling windows
   - Calculate train/validation/test consistency metrics
   - Monitor parameter sensitivity to input variations

### Analysis Templates

#### Deep Analysis Template
```markdown
# Condition [ID] Deep Analysis

## 1. Overview
- **Condition Name**: [Name]
- **Timeframe**: Tick / Minute
- **Market**: Stock / Coin
- **Analysis Date**: YYYY-MM-DD

## 2. Data Summary
| Metric | Train | Validation | Test |
|--------|-------|------------|------|
| Date Range | | | |
| Trade Count | | | |
| Win Rate | | | |
| Profit Factor | | | |

## 3. Overfitting Assessment
- [ ] Sample size ≥ 300 trades
- [ ] Train-val profit difference < 30%
- [ ] Validation period ≥ 3 months
- [ ] Parameter count ≤ 10
- [ ] Parameter ranges reasonable
- [ ] Cross-validation stability < 20%

**Risk Level**: LOW / MEDIUM / HIGH

## 4. Conflict Detection
- Parameter range conflicts: [List]
- Logic conflicts: [List]
- Timeframe conflicts: [List]
- Market condition conflicts: [List]

## 5. Statistical Validation
- T-test results: [p-value, effect size]
- Confidence intervals: [95% CI]
- Significance level: α = 0.05

## 6. Recommendations
- **Implementation**: Safe / Conditional / Not Recommended
- **Data Requirements**: [Minimum period]
- **Parameter Adjustments**: [Specific changes]
- **Risk Mitigation**: [Strategies]
```

#### Quick Study Template
```markdown
# Condition [ID] Study Notes

## Research Questions
1. [Question 1]
2. [Question 2]

## Preliminary Observations
- [Finding 1]
- [Finding 2]

## Data Collection Requirements
- Timeframe: [Period]
- Markets: [List]
- Minimum trades: [Count]

## Next Steps
- [ ] Collect additional data
- [ ] Run statistical tests
- [ ] Conduct conflict analysis
- [ ] Write deep analysis report
```

### Integration with Other Studies

**With ResearchReports/**:
- Apply overfitting assessment methodology from `Overfitting_Risk_Assessment_Filter_Segment_Analysis.md`
- Use AI/ML automation insights from `AI_ML_Trading_Strategy_Automation_Research.md`
- Reference optimization methods from `Segmented_Filter_Optimization_Research.md`

**With Guides/**:
- Follow `Condition_Optimization_and_Analysis_Guide.md` (826 tick variables)
- Apply `New_Metrics_Development_Process_Guide.md` (10-step process)
- Use `Segment_Filter_Verification_Checklist.md` for validation

**With CodeReview/**:
- Verify condition implementation matches analysis findings
- Cross-check bug fixes against condition performance changes
- Validate data mapping corrections

**With SystemAnalysis/**:
- Compare with OPTISTD calculation methods (14 methods)
- Verify metric integration consistency
- Check cross-timeframe compatibility

### Research Quality Standards

- **Sample Size**: Minimum 300 trades per segment (train/val/test)
- **Data Period**: Minimum 60 days, preferably 90+ days
- **Statistical Significance**: p-value < 0.05 with effect size reporting
- **Cross-Validation**: Walk-forward analysis with rolling windows
- **Documentation**: Link to condition files, include code snippets
- **Reproducibility**: Document parameter settings, random seeds, data versions

### Common Pitfalls to Avoid

1. **Insufficient Sample Size**: Never analyze conditions with <100 trades
2. **Data Snooping**: Avoid repeated testing on same dataset without adjustment
3. **Survivorship Bias**: Include delisted stocks/coins in analysis
4. **Look-Ahead Bias**: Verify LOOKAHEAD-FREE in all calculations
5. **Overfitting**: Monitor train-val profit difference >30%
6. **Ignoring Conflicts**: Always check related conditions for parameter inconsistencies
7. **Cherry-Picking**: Report all results, not just favorable ones

## Dependencies

### Statistical Analysis Tools
- **Core Libraries**: NumPy, pandas, SciPy
- **Statistical Tests**: t-test, F-test, chi-square, Kolmogorov-Smirnov
- **Effect Size**: Cohen's d, Hedge's g, Cliff's delta
- **Visualization**: matplotlib, seaborn for result presentation
- **Cross-Validation**: scikit-learn for K-fold, purged CV

### Backtesting Framework
- **Engines**: `backtester/backengine_*_*.py` (12 engines for tick/minute × markets)
- **Optimization**: `backtester/optimiz.py` (grid search), `optimiz_genetic_algorithm.py`
- **Database**: `backtest.db` for historical results, `tradelist.db` for trade records
- **Strategy Files**: `stock/kiwoom_strategy_tick.py`, `coin/*_strategy_min.py`

### Variable Definitions
- **Tick Variables**: 826 variables documented in `Back_Testing_Guideline_Tick.md`
- **Minute Variables**: 752 variables documented in `Back_Testing_Guideline_Min.md`
- **Segment Filters**: Market cap, time-based, volatility filters
- **Technical Indicators**: TA-Lib functions, custom implementations

### Domain Knowledge
- **Trading Strategy Design**: Entry/exit logic, risk management, position sizing
- **Korean Market**: Kiwoom API specifics, market hours, trading rules
- **Cryptocurrency**: Upbit/Binance API, 24/7 trading, exchange differences
- **Technical Analysis**: Indicator interpretation, pattern recognition
- **Risk Management**: Stop-loss, take-profit, portfolio heat, correlation

### Related Documentation
- **Condition Files**: 133 files in `docs/Condition/Tick/` (72) and `Min/` (61)
- **Guidelines**: `Condition_Document_Template_Guideline.md` for format
- **Manual**: `08_Backtesting/` for backtesting methodology
- **Optimization**: `backtester/` module for parameter tuning

---

**Last Updated**: 2026-01-19
**Total Documents**: 2 files (44KB + 10KB)
**Key Findings**: 17 high-risk conditions, sample size requirements, conflict detection
**Research Focus**: Overfitting prevention, statistical validation, strategy optimization
