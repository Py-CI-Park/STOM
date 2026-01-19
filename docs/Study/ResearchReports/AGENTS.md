<!-- Parent: ../AGENTS.md -->
# Research Reports

## Purpose

This directory contains comprehensive research on AI/ML automation, optimization methods, overfitting prevention, and advanced trading strategy development. It serves as the central repository for:

- **AI/ML Strategy Automation**: Machine learning applications for trading strategy generation and optimization
- **Optimization Research**: Advanced parameter tuning methods (genetic algorithms, Bayesian, NSGA-II)
- **Overfitting Prevention**: Statistical methods for robust strategy validation
- **Segmentation Analysis**: Market cap and time-based strategy segmentation
- **Risk Assessment**: Comprehensive risk evaluation frameworks
- **Circular Research Systems**: Self-improving research and development loops

**Key Technologies**: XGBoost, SHAP, Genetic Programming, LLM, NSGA-II, Optuna, Walk-Forward Validation

## Key Files

### AI/ML Automation Research

**AI_ML_Trading_Strategy_Automation_Research.md** (74KB)
- Comprehensive AI/ML strategy automation framework
- **Variable Catalog**: 826 tick variables with ML feature engineering
- **ML Techniques**: XGBoost for feature importance, SHAP for interpretability
- **Genetic Programming**: Automated strategy generation
- **LLM Integration**: Strategy ideation and parameter optimization
- **Validation**: Walk-forward, purged K-fold, Bonferroni correction
- **Implementation**: End-to-end automation pipeline design

**AI_Driven_Condition_Automation_Circular_Research_System.md** (80KB)
- Self-improving research and development loop
- **Circular Process**: Research → Implementation → Testing → Analysis → Refinement
- **Automation Levels**: Data collection, strategy generation, validation, deployment
- **Feedback Mechanisms**: Performance monitoring, adaptation triggers
- **Quality Gates**: Statistical validation at each loop iteration
- **Scalability**: Multi-strategy parallel evaluation

**Research_Report_Automated_Condition_Finding.md** (7KB)
- Automated strategy discovery methods
- Pattern recognition in historical data
- Hypothesis generation and testing
- Validation framework for discovered patterns

### Optimization & Segmentation

**2025-12-20_Segmented_Filter_Optimization_Research.md** (45KB)
- Market cap and time-based strategy segmentation
- **Segmentation Types**: Large/mid/small cap, opening/closing sessions, volatility regimes
- **Optimization Methods**: Per-segment parameter tuning, cross-segment validation
- **Performance Analysis**: Segment-specific metrics, transition handling
- **Implementation**: Database schema, filter integration, backtester modifications

**2026-01-07_Segment_Filter_Discrepancy_Analysis.md**
- Analysis of prediction vs. actual performance discrepancies
- Filter effectiveness validation
- Root cause investigation for mismatches
- Improvement recommendations

### Risk Assessment & Methodology

**2025-12-29_Overfitting_Risk_Assessment_Filter_Segment_Analysis.md** (120KB)
- **Comprehensive overfitting assessment framework**
- **6 Judgment Indicators**: Sample size, profit stability, validation period, parameter count, range reasonableness, cross-validation stability
- **Risk Scoring**: Quantitative risk assessment (0.0-1.0 scale)
- **Filter-Specific Analysis**: Segment filter overfitting detection
- **Statistical Methods**: Bonferroni/FDR correction, multiple hypothesis testing
- **Validation**: Walk-forward, purged K-fold, Monte Carlo simulation
- **Recommendations**: Risk mitigation strategies by severity level

**2026-01-07_Risk_Score_Improvement_Research.md**
- Enhanced risk scoring methodology
- Multi-dimensional risk assessment
- Dynamic risk thresholds
- Risk-adjusted performance metrics

**2026-01-10_Backtesting_Analysis_Methodology_Research.md**
- Comprehensive backtesting methodology framework
- Statistical validation procedures
- Performance attribution methods
- Best practices for robust analysis

### Advanced Optimization Studies

**2026-01-12_Iterative_Condition_Optimizer_Feasibility_Study.md**
- ICOS (Iterative Condition Optimizer System) feasibility analysis
- Iterative optimization loop design
- Convergence criteria and stopping conditions
- Computational efficiency considerations
- Integration with existing backtesting framework

## For AI Agents

### When Adding Research Reports

1. **File Naming Convention**: Use `YYYY-MM-DD_Research_Topic_[Type].md` format
   - Examples: `2026-01-15_Deep_Learning_Strategy_Generation_Research.md`
2. **Document Structure**: Include the following sections:
   - **Abstract**: 200-word summary of research purpose, methods, findings
   - **Introduction**: Problem statement, motivation, research questions
   - **Literature Review**: Related work, gaps in existing approaches
   - **Methodology**: Research design, data sources, analysis methods
   - **Results**: Quantitative findings with tables, charts, statistical tests
   - **Discussion**: Interpretation, implications, limitations
   - **Conclusions**: Key findings, recommendations, future work
   - **References**: Citations to papers, documentation, code
   - **Appendices**: Detailed data, code snippets, supplementary analysis
3. **Evidence-Based**: All claims supported by data, experiments, or citations
4. **Reproducible**: Include sufficient detail for replication
5. **Update Parent README.md**: Add entry to study summary table

### When Conducting Research

1. **Research Design Template**:
   ```markdown
   # [Research Topic] Research Report

   ## Abstract
   **Purpose**: [Research objective]
   **Methods**: [Approach used]
   **Results**: [Key findings]
   **Conclusions**: [Main takeaways]

   **Keywords**: [5-7 keywords for indexing]

   ## 1. Introduction

   ### 1.1 Problem Statement
   [Clear articulation of the problem being addressed]

   ### 1.2 Research Questions
   1. [Question 1]
   2. [Question 2]
   3. [Question 3]

   ### 1.3 Motivation
   [Why this research is important]

   ### 1.4 Scope
   [What is included and excluded]

   ## 2. Literature Review

   ### 2.1 Related Work
   [Summary of existing research and approaches]

   ### 2.2 Gaps and Limitations
   [What is missing or inadequate in current approaches]

   ### 2.3 Our Contribution
   [How this research fills the gaps]

   ## 3. Methodology

   ### 3.1 Research Design
   [Overall approach: experimental, analytical, empirical, theoretical]

   ### 3.2 Data Sources
   - **Historical Data**: [Period, markets, instruments]
   - **Sample Size**: [Number of observations]
   - **Data Quality**: [Cleaning, validation procedures]

   ### 3.3 Analysis Methods
   - **Statistical Tests**: [Tests used with significance levels]
   - **ML Algorithms**: [Models with hyperparameters]
   - **Validation**: [Cross-validation, walk-forward, etc.]

   ### 3.4 Implementation
   ```python
   # Key algorithm pseudocode or actual implementation
   ```

   ### 3.5 Evaluation Metrics
   - [Metric 1]: [Definition, interpretation]
   - [Metric 2]: [Definition, interpretation]

   ## 4. Results

   ### 4.1 Descriptive Statistics
   [Summary of data characteristics]

   ### 4.2 Main Findings
   #### Finding 1: [Title]
   **Observation**: [What was found]
   **Evidence**: [Data, statistical tests]
   **Significance**: [p-value, effect size]

   **Table/Figure**: [Visual representation]

   #### Finding 2: [Title]
   [Similar structure]

   ### 4.3 Sensitivity Analysis
   [How robust are findings to parameter changes]

   ### 4.4 Performance Comparison
   | Method | Metric 1 | Metric 2 | Metric 3 |
   |--------|----------|----------|----------|
   | Baseline | X | Y | Z |
   | Proposed | X' | Y' | Z' |
   | Improvement | +XX% | +YY% | +ZZ% |

   ## 5. Discussion

   ### 5.1 Interpretation
   [What do the results mean]

   ### 5.2 Implications
   - **Theoretical**: [Contributions to knowledge]
   - **Practical**: [Application to STOM system]

   ### 5.3 Limitations
   1. [Limitation 1]: [Description and impact]
   2. [Limitation 2]: [Description and impact]

   ### 5.4 Comparison with Related Work
   [How findings compare to literature]

   ## 6. Conclusions

   ### 6.1 Summary of Findings
   [Concise summary of main results]

   ### 6.2 Recommendations
   1. **Immediate**: [Short-term actions]
   2. **Medium-term**: [3-6 month actions]
   3. **Long-term**: [Strategic actions]

   ### 6.3 Future Work
   - [Research direction 1]
   - [Research direction 2]

   ## 7. References

   ### Academic Papers
   1. [Citation 1]
   2. [Citation 2]

   ### Documentation
   - [Internal doc 1]
   - [Internal doc 2]

   ### Code References
   - [Source file 1]: [Lines XX-YY]
   - [Source file 2]: [Lines XX-YY]

   ## Appendices

   ### Appendix A: Detailed Data Description
   [Table schemas, variable definitions]

   ### Appendix B: Additional Results
   [Supplementary tables and figures]

   ### Appendix C: Code Listings
   ```python
   # Complete implementation code
   ```

   ### Appendix D: Experimental Setup
   [Hardware, software versions, parameter settings]
   ```

2. **Statistical Rigor Requirements**:
   ```markdown
   ## Statistical Validation Standards

   ### Hypothesis Testing
   - **Null Hypothesis**: Clearly stated
   - **Significance Level**: α = 0.05 (Bonferroni-corrected if multiple tests)
   - **Effect Size**: Cohen's d, Hedge's g (report alongside p-values)
   - **Confidence Intervals**: 95% CI for all key metrics
   - **Power Analysis**: Ensure sufficient sample size (β = 0.20)

   ### Cross-Validation
   - **Method**: Purged K-fold for time series (K=5 minimum)
   - **Walk-Forward**: Rolling windows with embargo periods
   - **Out-of-Sample**: Minimum 20% holdout set
   - **Train/Val/Test Split**: 60/20/20 or 50/25/25

   ### Overfitting Prevention
   - **Sample Size**: Minimum 300 trades per strategy
   - **Multiple Testing**: Bonferroni or FDR correction
   - **Regularization**: L1/L2 penalties for ML models
   - **Feature Selection**: Limit features to avoid curse of dimensionality
   - **Cross-Validation Stability**: <20% performance variance

   ### Performance Metrics
   - **Returns**: Annualized return, CAGR
   - **Risk**: Volatility, max drawdown, VaR, CVaR
   - **Risk-Adjusted**: Sharpe, Sortino, Calmar, Information ratios
   - **Consistency**: Win rate, profit factor, consecutive losses
   - **Transaction Costs**: Include realistic slippage and commissions
   ```

3. **ML Research Best Practices**:
   ```python
   # Template for ML research implementation
   import numpy as np
   import pandas as pd
   from sklearn.model_selection import TimeSeriesSplit
   from sklearn.metrics import accuracy_score, precision_score, recall_score
   import shap

   class MLStrategyResearch:
       def __init__(self, data, features, target):
           self.data = data
           self.features = features
           self.target = target
           self.model = None
           self.results = {}

       def prepare_data(self):
           """
           Prepare features ensuring LOOKAHEAD-FREE.
           All features must use only past information.
           """
           # Feature engineering
           # Verify no future information leakage
           pass

       def train_with_cv(self, model, n_splits=5):
           """
           Train with purged K-fold cross-validation for time series.
           """
           tscv = TimeSeriesSplit(n_splits=n_splits)
           scores = []

           for train_idx, test_idx in tscv.split(self.data):
               # Implement embargo period to prevent leakage
               # Train and evaluate
               pass

           return scores

       def feature_importance_analysis(self):
           """
           Analyze feature importance using SHAP values.
           """
           explainer = shap.TreeExplainer(self.model)
           shap_values = explainer.shap_values(self.X_test)

           # Visualize and interpret
           return shap_values

       def overfitting_assessment(self):
           """
           Check for overfitting using 6 indicators.
           """
           indicators = {
               'sample_size': len(self.data) >= 300,
               'train_val_gap': abs(train_perf - val_perf) < 0.30,
               'cv_stability': cv_std < 0.20,
               'feature_count': len(self.features) <= 20,
               'validation_period': validation_days >= 90,
               'parameter_reasonableness': True  # Manual check
           }
           return indicators

       def generate_report(self):
           """
           Generate comprehensive research report.
           """
           report = {
               'performance': self.results,
               'feature_importance': self.feature_importance,
               'overfitting_check': self.overfitting_indicators,
               'statistical_tests': self.statistical_results
           }
           return report
   ```

4. **Optimization Research Guidelines**:
   - **Parameter Space**: Define reasonable ranges based on domain knowledge
   - **Optimization Method**: Grid search for <5 parameters, Bayesian/GA for more
   - **Validation**: Walk-forward validation with out-of-sample testing
   - **Convergence**: Define stopping criteria (max iterations, performance plateau)
   - **Robustness**: Test sensitivity to parameter changes (±10% variation)
   - **Computational Efficiency**: Profile time/memory usage, parallelization opportunities

5. **Segmentation Research Framework**:
   ```markdown
   ## Segmentation Analysis Template

   ### 1. Segment Definition
   - **Segmentation Variable**: [Market cap / Time / Volatility]
   - **Segment Boundaries**: [Thresholds and rationale]
   - **Overlap Handling**: [How to handle boundary cases]

   ### 2. Within-Segment Analysis
   - **Sample Size**: [Per segment]
   - **Performance Metrics**: [By segment]
   - **Parameter Optimization**: [Segment-specific tuning]

   ### 3. Cross-Segment Analysis
   - **Performance Comparison**: [Statistical tests between segments]
   - **Transition Handling**: [Strategy for segment switches]
   - **Interaction Effects**: [Segment combinations]

   ### 4. Validation
   - **Holdout Testing**: [Out-of-sample by segment]
   - **Walk-Forward**: [Rolling segment validation]
   - **Stability**: [Performance consistency over time]

   ### 5. Implementation Considerations
   - **Database Schema**: [Segment storage]
   - **Runtime Efficiency**: [Segment classification speed]
   - **Edge Cases**: [Handling missing/invalid segments]
   ```

### Integration with Other Studies

**With ConditionStudies/**:
- Apply research findings to specific condition analysis
- Use overfitting assessment framework (6 indicators)
- Implement validated statistical methods

**With Development/**:
- Translate research findings into implementation plans
- Design systems based on research recommendations
- Plan phased rollouts of new techniques

**With Guides/**:
- Create practical guides from research methodologies
- Document proven workflows from successful research
- Standardize research processes

**With SystemAnalysis/**:
- Apply research methods to system optimization
- Validate system improvements with rigorous testing
- Benchmark new approaches against baselines

**With CodeReview/**:
- Ensure research implementations follow best practices
- Validate ML model code for correctness
- Review statistical validity of implementations

### Research Quality Standards

- **Reproducibility**: All experiments must be reproducible with documented seeds, parameters, data versions
- **Statistical Rigor**: Use appropriate tests, corrections for multiple comparisons, effect size reporting
- **Peer Review**: Internal review before publication, external expert consultation for complex topics
- **Code Quality**: Research code follows same standards as production (linting, testing, documentation)
- **Documentation**: Clear explanation of methods, assumptions, limitations

### Common Research Topics

**AI/ML Applications**:
- Feature engineering for trading strategies (826 tick variables)
- ML model selection and hyperparameter tuning
- Interpretability with SHAP, LIME
- Ensemble methods for robust predictions
- Transfer learning across markets/timeframes

**Optimization Methods**:
- Genetic algorithms for parameter tuning
- Bayesian optimization for efficient search
- Multi-objective optimization (NSGA-II)
- Walk-forward optimization windows
- Computational efficiency improvements

**Risk & Validation**:
- Overfitting detection and prevention
- Walk-forward validation protocols
- Purged K-fold cross-validation
- Bonferroni/FDR correction methods
- Monte Carlo simulation for robustness

**Strategy Development**:
- Automated strategy generation
- Genetic programming for logic discovery
- LLM-assisted strategy ideation
- Strategy combination and ensemble
- Adaptive strategies with regime detection

**Performance Analysis**:
- Attribution analysis (factor decomposition)
- Transaction cost impact studies
- Slippage modeling and mitigation
- Market impact estimation
- Portfolio heat and correlation analysis

## Dependencies

### Research Tools & Libraries

**Machine Learning**:
- **Core**: scikit-learn, XGBoost, LightGBM, CatBoost
- **Deep Learning**: TensorFlow, PyTorch (if applicable)
- **Interpretability**: SHAP, LIME, ELI5
- **Optimization**: Optuna, Hyperopt, scipy.optimize
- **Genetic Algorithms**: DEAP, pymoo (NSGA-II)

**Statistical Analysis**:
- **Core**: SciPy, statsmodels, pingouin
- **Time Series**: tsfresh, tslearn, prophet
- **Bayesian**: PyMC3, ArviZ
- **Validation**: scikit-learn cross-validation, mlxtend

**Data Processing**:
- **Core**: NumPy, pandas
- **Feature Engineering**: featuretools, tsfresh
- **Scaling**: RobustScaler, StandardScaler (scikit-learn)

**Visualization**:
- **Core**: matplotlib, seaborn
- **Interactive**: plotly, bokeh
- **ML-Specific**: yellowbrick, shap plots

### STOM Framework Knowledge

**Backtesting System**:
- 12 backtesting engines (`backtester/backengine_*_*.py`)
- Optimization scripts (`optimiz.py`, `optimiz_genetic_algorithm.py`)
- Result databases (`backtest.db`, `optuna.db`)

**Variable Definitions**:
- 826 tick variables (`Back_Testing_Guideline_Tick.md`)
- 752 minute variables (`Back_Testing_Guideline_Min.md`)
- Segment filters (market cap, time, volatility)

**Strategy Implementation**:
- Strategy files (`*_strategy_tick.py`, `*_strategy_min.py`)
- Condition documents (133 files, 98.3% compliance)
- Template Method pattern for strategy extension

### Domain Expertise

**Trading Systems**:
- Strategy development and validation
- Risk management and position sizing
- Transaction cost modeling
- Market microstructure

**Statistical Methods**:
- Hypothesis testing and p-value interpretation
- Effect size calculation and interpretation
- Multiple testing correction (Bonferroni, FDR)
- Cross-validation for time series

**Machine Learning**:
- Model selection and hyperparameter tuning
- Feature engineering and selection
- Overfitting prevention techniques
- Model interpretability methods

**Optimization**:
- Parameter space design
- Search algorithms (grid, random, Bayesian, genetic)
- Convergence criteria and stopping conditions
- Computational efficiency considerations

### Related Documentation

**Guidelines**:
- `Back_Testing_Guideline_Tick.md` (826 variables)
- `New_Metrics_Development_Process_Guide.md` (10-step process)
- `Condition_Optimization_and_Analysis_Guide.md`

**Manual**:
- `08_Backtesting/` for backtesting methodology
- `03_Modules/backtester/` for implementation details

**Condition Documents**:
- 133 condition files for strategy reference
- Template compliance (98.3% target)

---

**Last Updated**: 2026-01-19
**Total Documents**: 9 files (~400KB total)
**Key Technologies**: XGBoost, SHAP, Genetic Programming, LLM, NSGA-II, Optuna
**Research Focus**: AI/ML automation, overfitting prevention (6 indicators), segmentation, risk assessment
**Quality Standards**: Statistical rigor, reproducibility, peer review
