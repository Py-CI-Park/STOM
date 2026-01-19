<!-- Parent: ../AGENTS.md -->
# Research & Study Documentation

## Purpose

This directory contains comprehensive research reports, system analysis, code reviews, and study materials for the STOM V1 project. It serves as the central repository for:

- **Research Findings**: AI/ML trading strategy automation, optimization methods, overfitting prevention
- **System Analysis**: Performance evaluation, architecture review, optimization system improvements
- **Code Reviews**: Branch review reports, quality assessments, bug identification
- **Condition Studies**: Deep analysis of specific trading strategies and conditions
- **Development Studies**: Feature implementation plans, enhancement proposals
- **Documentation Reviews**: Quality verification, consistency checks
- **Practical Guides**: Optimization workflows, metric development, integration processes

**Total Documents**: 19+ files (~730KB)
**Documentation Quality**: 4.5/5 with 300+ code snippets
**Current Status**: 17 completed, 1 under review

## Key Files

### Root-Level Study Files

**Backtesting Analysis**:
- `Backtesting_Output_Speed_Analysis.md` (46KB) - Performance benchmarking and optimization analysis
- `20260106_Enhanced_Backtesting_Analysis_System_Study.md` (25KB) - Backtesting system enhancements
- `20260107_Enhanced_Backtesting_System_Complete_Analysis.md` (23KB) - Complete backtesting system analysis

**Condition & Strategy Studies**:
- `20260106_Enhanced_Buy_Condition_Generator_Study.md` (15KB) - Buy condition generation research
- `20260106_Segment_Filter_Variable_Definition_Study.md` (18KB) - Segment filter variables analysis
- `segment_filter_verification_issue.md` (31KB) - Filter verification problem investigation
- `Study_Automated_Condition_Optimization_System.md` (7KB) - Automated optimization system overview

**Design & Implementation**:
- `20260107_Exec_to_Function_Migration_Design.md` (9KB) - Code refactoring design document
- `20260107_Enhanced_Backtesting_Analysis_System_Deep_Dive.md` (20KB) - Deep technical analysis

**Telegram Integration**:
- `Telegram_Charts_Analysis.md` (306 bytes) - Telegram chart analysis reference

**Comprehensive Overview**:
- `README.md` (22KB) - Complete index with study summary table, categorization by topic, document status tracking

## Subdirectories

### 1. CodeReview/
Code quality verification, branch reviews, bug detection, and architectural consistency checks.

**Files**: 2 documents
- `2025-12-31_Segment_Final_Reset_Branch_Review.md` (9KB) - Branch review with P0 bug detection
- `README.md` - Code review documentation index

**Purpose**: Ensure code quality before merges, identify data mapping bugs, architectural violations

**Reference**: `./CodeReview/README.md`

### 2. ConditionStudies/
Deep analysis of specific trading conditions and strategy performance evaluation.

**Files**: 2 documents
- `Condition_902_905_Update_2_Deep_Analysis.md` (44KB) - Market opening 5-minute strategy analysis
- `Condition_Tick_902_905_update_2_Study.md` (10KB) - Tick condition research notes

**Key Findings**: Overfitting risks in 17 conditions, sample size issues, condition conflict identification

**Reference**: `./ConditionStudies/`

### 3. Development/
Feature implementation plans, system enhancement proposals, and development roadmaps.

**Files**: 2+ documents
- `20260113_ICOS_Dialog_Enhancement_Plan.md` - ICOS dialog improvements
- `20260114_ICOS_Complete_Implementation_Plan.md` - Complete ICOS implementation strategy

**Purpose**: Document development initiatives, technical design decisions, implementation roadmaps

**Reference**: `./Development/`

### 4. DocumentationReviews/
Quality verification and consistency checks for project documentation.

**Files**: 1 document
- `2025-11-17_Documentation_Review_Report.md` (27KB) - 106 documents quality verification

**Key Metrics**: 4.5/5 quality score, 300+ code snippets, 5 broken links identified

**Reference**: `./DocumentationReviews/`

### 5. Guides/
Practical guides for optimization workflows, metric development, and system integration.

**Files**: 3 documents
- `Condition_Optimization_and_Analysis_Guide.md` (13KB) - 826 tick variables catalog and optimization methods
- `New_Metrics_Development_Process_Guide.md` (52KB) - 10-step metric development process with LOOKAHEAD-FREE verification
- `Segment_Filter_Condition_Integration_Guide.md` (8KB) - Segment filter integration workflow

**Purpose**: Provide actionable guidance for development, testing, and integration tasks

**Reference**: `./Guides/`

### 6. ResearchReports/
Comprehensive research on AI/ML automation, optimization methods, and overfitting prevention.

**Files**: 5 documents
- `AI_ML_Trading_Strategy_Automation_Research.md` (74KB) - AI/ML strategy automation (826 variables)
- `Research_Report_Automated_Condition_Finding.md` (7KB) - Automated condition discovery
- `AI_Driven_Condition_Automation_Circular_Research_System.md` (80KB) - Circular research system design
- `2025-12-20_Segmented_Filter_Optimization_Research.md` (45KB) - Market cap/time segmentation research
- `2025-12-29_Overfitting_Risk_Assessment_Filter_Segment_Analysis.md` (120KB) - Overfitting risk evaluation

**Key Technologies**: XGBoost, SHAP, Genetic Programming, LLM, NSGA-II, Optuna, Walk-Forward validation

**Reference**: `./ResearchReports/`

### 7. SystemAnalysis/
In-depth analysis of STOM system performance, optimization algorithms, and architectural improvements.

**Files**: 11+ documents including ML/ and Telegram/ subdirectories
- `Optistd_System_Analysis.md` (20KB) - OPTISTD 14 calculation methods analysis
- `STOM_Optimization_System_Improvements.md` (19KB) - 15 improvement proposals
- `2025-12-13_Git_Branch_Structure_Analysis.md` (38KB) - Git structure cleanup report
- `2025-12-28_Backtesting_Output_System_Analysis.md` (95KB) - 93-column output system analysis
- `2025-12-28_New_Metrics_Integration_Verification_Report.md` (48KB) - Metric integration verification
- `2025-12-28_Risk_Score_Calculation_and_Cross_Timeframe_Compatibility_Analysis.md` (5KB)
- `20260108_Segment_Filter_Prediction_vs_Actual_Discrepancy_Analysis.md`
- `20260115_ICOS_Implementation_Action_Plan.md`
- `20260115_ICOS_Pipeline_Analysis_and_Integration_Plan.md`

**Subdirectories**:
- `ML/` - Machine learning system analysis
- `Telegram/` - Telegram integration analysis

**Key Issues Identified**: Extreme value amplification, train×valid multiplication problems, cross-timeframe compatibility

**Reference**: `./SystemAnalysis/`

## For AI Agents

### When Adding Research Documents

1. **File Naming Convention**: Use `YYYY-MM-DD_Descriptive_Title.md` format
2. **Categorization**: Place documents in appropriate subdirectories based on content type
3. **Update README.md**: Add entry to the comprehensive study summary table with:
   - Document name, category, creation date, size
   - Key topics and major findings
   - Related technologies and status
4. **Document Structure**: Include overview, analysis results, conclusions, and references sections
5. **Cross-References**: Link to related documents in Manual/, Guideline/, and Condition/ directories

### When Analyzing Trading Strategies

1. **Read Existing Studies**: Review ConditionStudies/ for patterns and methodologies
2. **Check Variable Definitions**: Reference Guides/Condition_Optimization_and_Analysis_Guide.md (826 tick variables)
3. **Verify Overfitting Risks**: Apply criteria from ResearchReports/Overfitting_Risk_Assessment (6 judgment indicators)
4. **Document Findings**: Include statistical validation, sample size analysis, walk-forward test results
5. **Integration Guidance**: Reference Guides/Segment_Filter_Condition_Integration_Guide.md for implementation

### When Reviewing Code

1. **Follow Review Template**: Use CodeReview/Segment_Final_Reset_Branch_Review.md as reference
2. **Bug Prioritization**: Classify as P0 (critical), P1 (high), P2 (medium) with fix recommendations
3. **Data Mapping Verification**: Check column mappings, value ranges, type consistency
4. **Architecture Consistency**: Verify adherence to multiprocess architecture, queue patterns, naming conventions
5. **Quality Scoring**: Provide objective quality score (0-10) with specific criteria

### When Conducting System Analysis

1. **Performance Benchmarking**: Reference Backtesting_Output_Speed_Analysis.md for methodology
2. **Optimization Review**: Apply 15 improvement criteria from STOM_Optimization_System_Improvements.md
3. **Statistical Validation**: Use harmonic mean for MERGE calculations, avoid train×valid multiplication
4. **Integration Testing**: Verify compatibility across tick/minute timeframes, databases, UI components
5. **Documentation**: Include quantitative metrics, code snippets, before/after comparisons

### When Writing Guides

1. **Process Documentation**: Break into clear numbered steps (10-step metric development process)
2. **Checklist Format**: Provide validation checklists (LOOKAHEAD-FREE verification, integration checklist)
3. **Code Templates**: Include practical code examples and templates
4. **Best Practices**: Document proven patterns from successful implementations
5. **Troubleshooting**: Add common issues and resolution strategies

### Research Quality Standards

- **Evidence-Based**: Support conclusions with quantitative data and statistical validation
- **Reproducible**: Include code snippets, parameter settings, and experimental setup
- **Cross-Validated**: Apply walk-forward analysis, train/test separation
- **Documented**: Link to source files, reference related research
- **Actionable**: Provide specific implementation recommendations with priority rankings

### Documentation Maintenance

- **Monthly Review**: Verify document relevance and accuracy
- **Quarterly Cleanup**: Archive outdated documents, update status indicators
- **Annual Audit**: Reassess directory structure and categorization
- **Version Control**: Use meaningful commit messages for research documentation
- **Compliance Tracking**: Maintain 98.3%+ documentation guideline compliance

### Integration Points

**With Manual/**:
- System architecture analysis connects to `02_Architecture/`
- Performance findings inform `08_Backtesting/`
- UI/UX studies reference `05_UI_UX/`

**With Guideline/**:
- Variable definitions align with `Back_Testing_Guideline_Tick.md` (826 variables)
- Optimization methods reference `Condition_Document_Template_Guideline.md`

**With Condition/**:
- Strategy studies analyze specific condition files in `Tick/` and `Min/`
- Optimization research validates condition document compliance (98.3%)

## Dependencies

### Research Methodologies
- **Statistical Analysis**: SciPy, NumPy, pandas for quantitative evaluation
- **Machine Learning**: XGBoost, SHAP for feature importance analysis
- **Optimization**: Optuna, NSGA-II, CMA-ES for parameter tuning
- **Validation**: Walk-Forward Analysis, Purged K-Fold cross-validation
- **Overfitting Prevention**: Bonferroni/FDR correction, train/val/test separation

### Analysis Tools
- **Performance Profiling**: timeit, cProfile, memory_profiler
- **Data Visualization**: matplotlib, seaborn for result presentation
- **Code Quality**: pylint, mypy for static analysis
- **Git Analysis**: gitpython for branch structure analysis
- **Documentation**: Markdown for report generation

### Domain Knowledge Requirements
- **Trading Strategy Design**: Technical analysis, risk management
- **Backtesting Principles**: LOOKAHEAD-FREE verification, sample size requirements
- **Multiprocess Architecture**: Queue-based communication, process coordination
- **Database Management**: SQLite schema, query optimization
- **Statistical Testing**: Hypothesis testing, confidence intervals, effect sizes

### External References
- **STOM Framework**: `utility/setting.py`, `utility/static.py`, `utility/query.py`
- **Backtesting System**: `backtester/backengine_*_*.py` (12 engines)
- **Strategy Files**: `stock/kiwoom_strategy_tick.py`, `coin/*_strategy_min.py`
- **Optimization**: `backtester/optimiz.py`, `backtester/optimiz_genetic_algorithm.py`

---

**Last Updated**: 2025-01-19
**Total Documents**: 19+ files in 7 subdirectories
**Documentation Quality**: 4.5/5 (98.3% guideline compliance)
**Status**: 17 completed, 1 under review
