<!-- Parent: ../AGENTS.md -->
# Machine Learning System Analysis

## Purpose

This subdirectory contains analysis of machine learning components within the STOM system. It serves as the repository for:

- **ML Model Performance Analysis**: Evaluation of model accuracy, precision, recall, and other metrics
- **Feature Engineering Studies**: Analysis of feature importance, correlation, and effectiveness
- **Model Improvement Proposals**: Recommendations for enhancing ML model performance
- **Integration Analysis**: ML component integration with backtesting and trading systems
- **Computational Efficiency**: Performance profiling and optimization of ML pipelines

**Key Objectives**:
- Evaluate effectiveness of ML models for trading strategy generation
- Identify feature engineering opportunities (from 826 tick variables, 752 minute variables)
- Propose model architecture improvements
- Optimize ML pipeline performance
- Ensure LOOKAHEAD-FREE compliance in feature engineering

## Key Files

### Model Improvement Studies

**ML_Model_Improvement_Study.md**
- Analysis of current ML model implementations
- Performance evaluation metrics
- Feature importance analysis (SHAP values)
- Overfitting assessment
- Recommendations for model enhancements
- Computational efficiency considerations

## For AI Agents

### When Adding ML Analysis Documents

1. **File Naming Convention**: Use `ML_[Component]_[Analysis_Type]_Study.md` format
   - Examples: `ML_Feature_Selection_Analysis.md`, `ML_Model_Architecture_Comparison.md`
2. **Document Structure**: Include the following sections:
   - **Overview**: ML component analyzed, scope, objectives
   - **Current State**: Existing implementation, baseline performance
   - **Data Analysis**: Feature statistics, distributions, correlations
   - **Model Evaluation**: Performance metrics, validation results, overfitting checks
   - **Feature Importance**: SHAP values, permutation importance, correlation analysis
   - **Improvement Proposals**: Specific recommendations with expected impact
   - **Implementation Plan**: Steps, effort estimates, validation approach
   - **Success Metrics**: KPIs to measure improvements
   - **Appendices**: Detailed results, code snippets, visualizations
3. **Evidence-Based**: Support findings with quantitative data, charts, statistical tests
4. **LOOKAHEAD-FREE Verification**: Ensure no future information leakage in features
5. **Update Parent AGENTS.md**: Add entry describing study scope and findings

### When Analyzing ML Components

1. **ML Analysis Framework**:
   ```markdown
   # ML Component Analysis Template

   ## 1. Overview
   **Component**: [ML model/pipeline being analyzed]
   **Analysis Date**: YYYY-MM-DD
   **Analyst**: [Name/team]

   **Research Questions**:
   1. [Question 1]
   2. [Question 2]
   3. [Question 3]

   ## 2. Current State

   ### 2.1 Model Architecture
   ```python
   # Current model implementation
   model = XGBClassifier(
       n_estimators=100,
       max_depth=5,
       learning_rate=0.1,
       # ... other parameters
   )
   ```

   ### 2.2 Features
   **Total Features**: [Count]
   **Feature Categories**:
   - Price-based: [Count] (현재가, 시가, 고가, 저가)
   - Volume-based: [Count] (거래량, 거래대금)
   - Technical indicators: [Count] (moving averages, RSI, etc.)
   - Engineered features: [Count] (custom calculations)

   ### 2.3 Baseline Performance
   | Metric | Train | Validation | Test |
   |--------|-------|------------|------|
   | Accuracy | X% | Y% | Z% |
   | Precision | X% | Y% | Z% |
   | Recall | X% | Y% | Z% |
   | F1-Score | X% | Y% | Z% |
   | ROC-AUC | X% | Y% | Z% |

   ## 3. Data Analysis

   ### 3.1 Feature Statistics
   | Feature | Mean | Std | Min | Max | Missing % |
   |---------|------|-----|-----|-----|-----------|
   | [Feature 1] | X | Y | Z | W | N% |

   ### 3.2 Feature Distributions
   [Histograms, box plots for key features]

   ### 3.3 Correlation Analysis
   [Correlation matrix, heatmap]
   - High correlations (>0.8): [List of feature pairs]
   - Potential multicollinearity issues: [Description]

   ### 3.4 Target Variable Balance
   | Class | Count | Percentage |
   |-------|-------|------------|
   | Positive (Buy) | X | Y% |
   | Negative (No Buy) | Z | W% |

   **Imbalance Ratio**: X:Y
   **Resampling Strategy**: [SMOTE, undersampling, class weights, etc.]

   ## 4. Model Evaluation

   ### 4.1 Performance Metrics
   **Classification Report**:
   ```
   [Output of classification_report]
   ```

   **Confusion Matrix**:
   | | Predicted Neg | Predicted Pos |
   |---|---------------|---------------|
   | Actual Neg | TN | FP |
   | Actual Pos | FN | TP |

   ### 4.2 Overfitting Assessment
   **Train-Val Gap Analysis**:
   - Accuracy gap: X%
   - Precision gap: Y%
   - Recall gap: Z%

   **Diagnosis**: [Overfitting / Well-fitted / Underfitting]

   **Evidence**:
   - [ ] Train accuracy >> Val accuracy (>10% gap) → Overfitting
   - [ ] Both train and val accuracy low → Underfitting
   - [ ] Train ≈ Val accuracy, both high → Well-fitted

   ### 4.3 Cross-Validation Results
   **Method**: Purged K-Fold (K=5) for time series

   | Fold | Accuracy | Precision | Recall | F1-Score |
   |------|----------|-----------|--------|----------|
   | 1 | X% | Y% | Z% | W% |
   | 2 | X% | Y% | Z% | W% |
   | ... | ... | ... | ... | ... |
   | Mean | X% | Y% | Z% | W% |
   | Std | ±X% | ±Y% | ±Z% | ±W% |

   **Stability Assessment**: Std < 5% → Stable, 5-10% → Moderate, >10% → Unstable

   ### 4.4 Learning Curves
   [Plot of train/val performance vs training set size]

   **Interpretation**:
   - More data needed? [Yes/No, evidence]
   - Model complexity appropriate? [Yes/No, evidence]

   ## 5. Feature Importance Analysis

   ### 5.1 SHAP Value Analysis
   ```python
   import shap

   explainer = shap.TreeExplainer(model)
   shap_values = explainer.shap_values(X_test)

   # Summary plot
   shap.summary_plot(shap_values, X_test)
   ```

   **Top 20 Features by Mean |SHAP|**:
   | Rank | Feature | Mean |SHAP| | Interpretation |
   |------|---------|-------------|----------------|
   | 1 | [Feature] | X.XX | [Impact on predictions] |
   | 2 | [Feature] | X.XX | [Impact on predictions] |
   | ... | ... | ... | ... |

   ### 5.2 Permutation Importance
   [Bar chart of permutation importance scores]

   **Top 10 Features**:
   1. [Feature 1]: [Score]
   2. [Feature 2]: [Score]
   ...

   ### 5.3 Feature Redundancy
   **Highly Correlated Feature Pairs** (>0.9):
   - [Feature A] ↔ [Feature B]: Correlation = X.XX
   - Recommendation: [Keep which one and why]

   **Low Importance Features** (Mean |SHAP| < 0.01):
   - [List of features]
   - Recommendation: Consider removal to reduce model complexity

   ## 6. LOOKAHEAD-FREE Verification

   ### 6.1 Feature Calculation Audit
   For each feature, verify that calculation uses only past information:

   **Feature: [Name]**
   ```python
   # Current calculation
   df['feature'] = df['value'].shift(1).rolling(20).mean()
   ```

   **LOOKAHEAD Check**:
   - [ ] Uses .shift() to avoid current bar
   - [ ] Rolling window looks backward only
   - [ ] No future information used
   - **Status**: ✅ LOOKAHEAD-FREE / ❌ LOOKAHEAD BIAS

   ### 6.2 Target Variable Leakage Check
   - [ ] Target calculated after feature cutoff time
   - [ ] No overlap between feature period and target period
   - [ ] Proper train/val/test split (no data leakage)

   ### 6.3 Validation
   ```python
   # Test for lookahead bias
   def test_lookahead_bias(df, feature_col, target_col):
       # Correlation of feature[t] with target[t-1] should be ~0
       corr_past = df[feature_col].corr(df[target_col].shift(-1))
       assert abs(corr_past) < 0.1, f"LOOKAHEAD BIAS detected: corr={corr_past}"
   ```

   ## 7. Improvement Proposals

   ### Proposal 1: [Title]
   **Priority**: P0/P1/P2
   **Effort**: XS/S/M/L/XL
   **Expected Impact**: [Quantitative estimate]

   **Description**: [What to change]

   **Implementation**:
   ```python
   # Proposed change
   ```

   **Validation Plan**:
   - [ ] Implement change
   - [ ] Re-train model
   - [ ] Evaluate on validation set
   - [ ] Compare metrics to baseline
   - [ ] Verify no LOOKAHEAD bias

   **Expected Results**:
   | Metric | Baseline | Expected | Improvement |
   |--------|----------|----------|-------------|
   | Accuracy | X% | Y% | +Z% |
   | Precision | X% | Y% | +Z% |

   ### Proposal 2: [Title]
   [Similar structure]

   ## 8. Implementation Plan

   ### Phase 1: Quick Wins (Week 1-2)
   - [ ] Remove redundant features (XS effort)
   - [ ] Adjust class weights for imbalance (XS effort)
   - [ ] Tune learning rate and max_depth (S effort)

   ### Phase 2: Feature Engineering (Week 3-4)
   - [ ] Add new technical indicators (M effort)
   - [ ] Engineer interaction features (M effort)
   - [ ] Validate LOOKAHEAD-FREE (S effort)

   ### Phase 3: Model Architecture (Week 5-6)
   - [ ] Try ensemble methods (L effort)
   - [ ] Experiment with neural networks (XL effort)
   - [ ] Hyperparameter optimization with Optuna (M effort)

   ### Resources
   - Developer time: [X days]
   - Compute resources: [GPU if applicable]
   - Data requirements: [Additional data needed?]

   ## 9. Success Metrics

   **Immediate (2 weeks)**:
   - Val accuracy improves from X% to Y%
   - Train-val gap reduces from X% to <5%

   **Short-term (1 month)**:
   - Test accuracy >Z%
   - Feature count reduced by X%
   - Training time <Y minutes

   **Long-term (3 months)**:
   - Live trading performance validates model
   - Sharpe ratio >X
   - Max drawdown <Y%

   ## 10. References

   **Related Code**:
   - [file.py]: [Lines XX-YY]

   **Related Documentation**:
   - `Back_Testing_Guideline_Tick.md` (826 variables)
   - `AI_ML_Trading_Strategy_Automation_Research.md`

   **External Resources**:
   - [Paper/blog]: [URL]

   ## Appendices

   ### Appendix A: Complete Feature List
   [All features with descriptions]

   ### Appendix B: SHAP Plots
   [Detailed SHAP visualizations]

   ### Appendix C: Model Training Code
   ```python
   # Complete training script
   ```

   ### Appendix D: Hyperparameter Tuning Results
   [Optuna study results, parameter importance]
   ```

2. **ML Performance Profiling**:
   ```python
   import time
   import numpy as np
   from sklearn.metrics import classification_report, confusion_matrix
   import shap

   class MLPerformanceAnalyzer:
       def __init__(self, model, X_train, y_train, X_val, y_val, X_test, y_test):
           self.model = model
           self.X_train = X_train
           self.y_train = y_train
           self.X_val = X_val
           self.y_val = y_val
           self.X_test = X_test
           self.y_test = y_test
           self.results = {}

       def evaluate_performance(self):
           """Comprehensive performance evaluation"""
           for name, X, y in [('train', self.X_train, self.y_train),
                              ('val', self.X_val, self.y_val),
                              ('test', self.X_test, self.y_test)]:
               y_pred = self.model.predict(X)
               y_proba = self.model.predict_proba(X)[:, 1]

               self.results[f'{name}_report'] = classification_report(y, y_pred)
               self.results[f'{name}_confusion'] = confusion_matrix(y, y_pred)
               self.results[f'{name}_proba'] = y_proba

       def analyze_overfitting(self):
           """Check for overfitting"""
           train_score = self.model.score(self.X_train, self.y_train)
           val_score = self.model.score(self.X_val, self.y_val)
           gap = train_score - val_score

           self.results['overfitting_check'] = {
               'train_score': train_score,
               'val_score': val_score,
               'gap': gap,
               'status': 'Overfitting' if gap > 0.10 else 'OK'
           }

       def feature_importance_shap(self, sample_size=100):
           """Compute SHAP values for feature importance"""
           # Sample for efficiency
           X_sample = self.X_test.sample(min(sample_size, len(self.X_test)))

           explainer = shap.TreeExplainer(self.model)
           shap_values = explainer.shap_values(X_sample)

           # Mean absolute SHAP values
           mean_shap = np.abs(shap_values).mean(axis=0)
           feature_importance = pd.DataFrame({
               'feature': X_sample.columns,
               'importance': mean_shap
           }).sort_values('importance', ascending=False)

           self.results['feature_importance'] = feature_importance
           return shap_values

       def profile_inference_time(self, n_runs=100):
           """Profile prediction time"""
           times = []
           for _ in range(n_runs):
               start = time.perf_counter()
               self.model.predict(self.X_test[:1])
               end = time.perf_counter()
               times.append(end - start)

           self.results['inference_time'] = {
               'mean_ms': np.mean(times) * 1000,
               'median_ms': np.median(times) * 1000,
               'p95_ms': np.percentile(times, 95) * 1000,
               'p99_ms': np.percentile(times, 99) * 1000
           }

       def check_lookahead_bias(self, df, feature_cols, target_col):
           """Verify LOOKAHEAD-FREE compliance"""
           lookahead_issues = []
           for feature in feature_cols:
               # Check if feature[t] correlates with target[t-1]
               # (should be ~0 if LOOKAHEAD-FREE)
               corr = df[feature].corr(df[target_col].shift(-1))
               if abs(corr) > 0.1:
                   lookahead_issues.append({
                       'feature': feature,
                       'correlation': corr,
                       'status': 'POTENTIAL LOOKAHEAD BIAS'
                   })

           self.results['lookahead_check'] = lookahead_issues
           return len(lookahead_issues) == 0

       def generate_report(self):
           """Generate comprehensive analysis report"""
           return self.results
   ```

3. **Feature Engineering Best Practices**:
   - Use only historical data (t-1 and earlier for feature calculation)
   - Apply .shift(1) before any aggregation (rolling, expanding)
   - Validate features with LOOKAHEAD-FREE tests
   - Document feature calculation logic clearly
   - Consider computational cost (826 tick variables can be expensive)
   - Remove highly correlated features (>0.9 correlation)
   - Normalize/standardize features appropriately
   - Handle missing values explicitly (forward fill, interpolation, or drop)

4. **Model Selection Guidelines**:
   - **XGBoost/LightGBM**: Good for tabular data, fast, interpretable (SHAP)
   - **Random Forest**: Robust, less prone to overfitting, slower
   - **Neural Networks**: For complex patterns, requires more data, less interpretable
   - **Ensemble Methods**: Combine multiple models for robustness
   - **Linear Models**: Fast, interpretable, good baseline

### Integration with Other Studies

**With ResearchReports/**:
- Implement ML automation research findings
- Apply overfitting prevention methods (6 indicators)
- Use validated feature engineering techniques

**With ConditionStudies/**:
- Analyze ML-generated strategy performance
- Compare ML strategies to rule-based conditions
- Validate ML predictions against actual trades

**With SystemAnalysis/**:
- Evaluate ML component performance in production
- Profile computational efficiency
- Identify optimization opportunities

**With Guides/**:
- Create ML workflow guides (training, evaluation, deployment)
- Document feature engineering processes
- Standardize model evaluation procedures

### ML-Specific Quality Standards

- **LOOKAHEAD-FREE**: All features must use only past information
- **Cross-Validation**: Use time series-aware CV (purged K-fold, walk-forward)
- **Overfitting Prevention**: Train-val gap <10%, CV stability <10%
- **Feature Count**: Limit to <100 features to avoid overfitting (from 826 available)
- **Sample Size**: Minimum 10× features for training set
- **Interpretability**: Prefer interpretable models (XGBoost + SHAP) for trading
- **Inference Speed**: <10ms per prediction for real-time trading

## Dependencies

### ML Libraries
- **Core**: scikit-learn, XGBoost, LightGBM, CatBoost
- **Interpretability**: SHAP, LIME, ELI5
- **Optimization**: Optuna, Hyperopt
- **Validation**: mlxtend (purged CV), scipy
- **Visualization**: matplotlib, seaborn, yellowbrick

### STOM Framework
- **Variables**: 826 tick variables, 752 minute variables (from Guidelines)
- **Backtesting**: Integration with `backtester/` module
- **Database**: Feature storage in SQLite databases
- **Real-time**: Integration with `*_strategy_*.py` for live trading

### Domain Knowledge
- **Trading Strategy**: Technical analysis, market microstructure
- **Time Series**: Stationarity, autocorrelation, seasonality
- **Feature Engineering**: Domain-specific features for trading
- **Risk Management**: Position sizing, stop-loss integration with ML

### Related Documentation
- `ResearchReports/AI_ML_Trading_Strategy_Automation_Research.md` (74KB)
- `Guideline/Back_Testing_Guideline_Tick.md` (826 variables)
- `Guides/New_Metrics_Development_Process_Guide.md` (LOOKAHEAD-FREE)

---

**Last Updated**: 2026-01-19
**Total Documents**: 1 file
**Focus**: ML model performance, feature engineering, LOOKAHEAD-FREE validation
**Quality Standards**: Statistical rigor, overfitting prevention, interpretability
