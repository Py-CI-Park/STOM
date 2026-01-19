<!-- Parent: ../AGENTS.md -->
# GPT-5 Strategy Plans (Version G)

## Purpose
GPT-5 모델이 생성한 ML 기반 조건식 최적화 계획 (Version G). 실용적이고 코드 중심의 접근 방식으로 빠른 프로토타이핑과 반복 실험을 강조합니다.

## Overview
- **Total files**: 14 files (9 in subdirectory)
- **Focus**: Minimal viable research codebase with rapid iteration
- **Approach**: Quantify variable contribution to profit with minimal modules
- **Scope**: Data loader, labeling, feature engineering, backtester wrapper, optimization

## Key Files

### Root Level (5 files)
- **Back_Testing_Guideline_Min.md** (25KB) - 분봉 백테스팅 가이드라인 제안 (752개 문서화된 변수)
- **Back_Testing_Guideline_Tick.md** (33KB) - 틱 백테스팅 가이드라인 제안 (826개 문서화된 변수)
- **Condition_Survey_Idea.md** (4KB) - 조건식 서베이 및 아이디어 제안
- **Condition_Survey_ML_DL_Plan.md** (11KB) - ML/DL 조건식 최적화 계획
- **Stock_Database_Information.md** (2.5KB) - 데이터베이스 정보 참조

### program_develop_document_versionG/ (9 files)
최소 모듈 기반 빠른 반복 실험 프레임워크:

- **00_Overview.md** - 목적, 범위, 성공 기준
  - 최종 목표: 조건식 변수의 수익 기여 정량화
  - 핵심 결과물: `research/` 최소 코드베이스
  - 성공 기준: Sharpe ≥ 1.0, OOS ≥ 0.8, 1시간 내 200+ trials

- **01_Code_Map.md** - 프로젝트 구조 및 모듈 설계
  - `research/` 폴더 구조
  - 핵심 모듈: loader, label, feature, backtest wrapper, optimize, model, evaluate
  - 최소 의존성 원칙

- **02_Data_and_Labeling.md** - 데이터 로딩 및 레이블링
  - SQLite 로더 (multiprocessing 지원)
  - 레이블 생성: 수익 > 비용 분류
  - 특징 추출: 기본 윈도우 통계

- **03_Backtester_Wrapper.md** - 백테스터 래퍼 설계
  - 기존 STOM 백테스터 연동
  - 조건식 파라미터 → 백테스트 결과 매핑
  - 병렬 평가 지원

- **04_Optimization_and_Search.md** - 최적화 및 탐색
  - Optuna 기반 하이퍼파라미터 탐색
  - 200-500 trials 목표
  - 병렬화 4+ workers
  - MLflow 로깅

- **05_Model_Baselines.md** - 베이스라인 모델
  - XGBoost GPU 베이스라인
  - 단순 특징 중요도 분석
  - 빠른 프로토타이핑 우선

- **06_Experiment_and_Evaluation.md** - 실험 및 평가
  - 워크포워드 3분할 + OOS 1분할
  - 비용/슬리피지 반영
  - 재현성 검증 (±10% 변동)

- **07_Project_Plan_and_Milestones.md** - 프로젝트 계획 및 마일스톤
  - Phase 1: Setup (1-2일)
  - Phase 2: 베이스라인 (2-3일)
  - Phase 3: 최적화 (3-4일)
  - Phase 4: 평가 및 리포트 (1-2일)

- **08_Quickstart.md** - 빠른 시작 가이드
  - 설치 및 설정
  - 샘플 실행 코드
  - 일반적인 문제 해결

## Characteristics

### GPT-5 Strengths
- **Concise, actionable recommendations** - 간결하고 실행 가능한 제안
- **Practical implementation focus** - 실용적 구현 중심
- **Code-oriented solutions** - 코드 중심 솔루션
- **Rapid prototyping approach** - 빠른 프로토타이핑 접근
- **Minimal viable approach** - 최소 기능 제품 원칙
- **Quick iteration cycles** - 빠른 반복 주기

### Technical Approach
- **Minimal Module Design**:
  - Loader: SQLite → DataFrame
  - Labeling: Simple profit > cost classification
  - Features: Basic window statistics
  - Backtester wrapper: STOM integration
  - Optimization: Optuna with parallel execution
  - Model: XGBoost GPU baseline
  - Evaluation: Walk-forward + OOS validation

- **Technology Stack**:
  - ML: XGBoost (GPU), scikit-learn
  - Optimization: Optuna (200-500 trials)
  - Data: SQLite, pandas, multiprocessing
  - Tracking: MLflow
  - Validation: Walk-forward analysis

- **Performance Targets**:
  - Walk-forward average Sharpe ≥ 1.0
  - OOS Sharpe ≥ 0.8
  - Reproducibility: ±10% performance variation
  - Speed: 200+ trials in 1 hour (GPU, 4+ workers)

## For AI Agents

### Working with GPT-5 Plans

**When to Use:**
- Quick prototype needed
- Code implementation details required
- Specific problem-solving approach
- Iterative refinement cycle
- Minimal viable product approach
- Fast turnaround required

**Validation Approach:**
1. **Start minimal** - Implement only essential components
2. **Validate quickly** - Test each module independently
3. **Iterate rapidly** - Refine based on immediate results
4. **Scale gradually** - Add complexity only when needed
5. **Document concisely** - Keep documentation actionable
6. **Measure continuously** - Track metrics at each iteration

**Implementation Guidelines:**
1. **Setup (1-2 days)**:
   - Create `research/` folder structure
   - Install dependencies (XGBoost, Optuna, MLflow)
   - Test SQLite connection
   - Verify data access

2. **Baseline (2-3 days)**:
   - Implement data loader with multiprocessing
   - Create simple labeling (profit > cost)
   - Extract basic features (windows, returns)
   - Train XGBoost baseline
   - Verify feature importance

3. **Optimization (3-4 days)**:
   - Wrap STOM backtester
   - Setup Optuna with 4+ workers
   - Run 200-500 trials
   - Log results to MLflow
   - Analyze top performers

4. **Evaluation (1-2 days)**:
   - Walk-forward validation (3 folds)
   - OOS testing (1 fold)
   - Check reproducibility
   - Generate report
   - Document findings

### Critical Evaluation

**Strengths:**
- Minimal scope - easier to implement and debug
- Fast iteration - see results quickly
- Practical focus - code-ready solutions
- Realistic timeline - 1-2 weeks total
- Lower resource requirements - no deep learning complexity
- Clear success criteria - quantifiable targets

**Considerations:**
- Simpler models - may miss complex patterns
- Basic features - limited signal extraction
- Optimization-focused - risk of overfitting
- Less comprehensive - narrower scope than Claude plan
- Requires existing backtester - depends on STOM integration

**Risk Factors:**
1. **Overfitting risk** - 200-500 trials may overfit to training data
2. **Feature simplicity** - Basic features may not capture all signals
3. **Reproducibility challenges** - ±10% variation still significant
4. **Generalization concerns** - OOS validation critical but limited
5. **Integration dependency** - Relies heavily on existing STOM backtester

## Dependencies

### Technical Requirements
- **Python 3.8+** - Core programming language
- **XGBoost** - GPU-accelerated ML baseline
- **Optuna** - Hyperparameter optimization (200-500 trials)
- **MLflow** - Experiment tracking and logging
- **SQLite** - Database (existing STOM structure)
- **pandas/numpy** - Data manipulation
- **multiprocessing** - Parallel data loading
- **scikit-learn** - ML utilities

### STOM System Dependencies
- **Data access**: `_database/*.db` (SQLite databases)
- **Backtesting**: `backtester/backengine_*` integration (critical)
- **Strategy pattern**: Understanding of existing condition format
- **Documentation**: Follow `docs/Guideline/` templates
- **Validation**: Existing condition documentation standards

### External Resources
- **Compute**: GPU recommended for XGBoost (optional, CPU works)
- **Storage**: Historical data access (~5GB+ recommended)
- **Memory**: 8GB+ RAM for backtesting
- **Time**: 1-2 weeks for full implementation

## Integration with STOM

### Data Integration
```python
# GPT plan uses existing STOM databases
from utility.setting import DB_STOCK_TICK, DB_STOCK_MIN
import sqlite3
import pandas as pd

# Minimal loader with multiprocessing
def load_data(db_path, stock_codes, start_date, end_date):
    conn = sqlite3.connect(db_path)
    # Load and return DataFrame
    return df
```

### Backtesting Integration
```python
# Critical: Wrapper around existing backtester
from backtester.backengine_stock_tick import BackEngineStockTick

# Map condition parameters to backtest results
def evaluate_condition(params):
    # Convert params to condition format
    # Run backtester
    # Return metrics (Sharpe, MDD, etc.)
    return metrics
```

### Optimization Flow
```python
import optuna

# Optuna objective function
def objective(trial):
    params = {
        'window': trial.suggest_int('window', 5, 50),
        'threshold': trial.suggest_float('threshold', 0.01, 0.1)
    }
    metrics = evaluate_condition(params)
    return metrics['sharpe']

# Run optimization with parallel workers
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=200, n_jobs=4)
```

## Success Metrics

### Performance Targets (from GPT plan)
| Metric | Target | Constraint |
|--------|--------|------------|
| Walk-forward Sharpe | ≥ 1.0 | Average across 3 folds |
| OOS Sharpe | ≥ 0.8 | Out-of-sample validation |
| Reproducibility | ±10% | Performance variation |
| Optimization speed | 200+ trials | Within 1 hour (GPU, 4 workers) |

### Validation Criteria
- **Walk-forward validation**: 3 folds with progressive time periods
- **OOS testing**: 1 fold completely unseen data
- **Cost/slippage**: Realistic transaction costs included
- **Reproducibility**: Same setup yields consistent results (±10%)
- **Speed**: Optimization completes in reasonable time

### Phase Completion Criteria
- **Phase 1 (Setup)**: All modules import, data loads successfully
- **Phase 2 (Baseline)**: XGBoost trains, features show importance
- **Phase 3 (Optimization)**: 200+ trials complete, top candidates identified
- **Phase 4 (Evaluation)**: Walk-forward + OOS pass criteria, report generated

## Related Documentation
- **Parent**: `../AGENTS.md` - AI Strategy Ideas overview
- **Comparison**: `../Plan_from_claude_opus/` - Alternative Claude Opus approach
- **Implementation**: `../../Tick/`, `../../Min/` - Production strategies
- **Guidelines**: `../../../Guideline/` - Documentation standards
- **Reference**: `Condition_Survey_ML_DL_Plan.md` - ML/DL optimization plan

## Comparison: GPT-5 vs Claude Opus

### GPT-5 (Version G) Approach
- **Philosophy**: Minimal viable research codebase
- **Timeline**: 1-2 weeks
- **Complexity**: Lower (XGBoost baseline only)
- **Scope**: Focused (quantify variable contribution)
- **Resources**: Moderate (GPU recommended, CPU okay)
- **Risk**: Overfitting via optimization

### Claude Opus Approach
- **Philosophy**: Comprehensive 4-phase system
- **Timeline**: 4+ weeks
- **Complexity**: Higher (ML + DL + Ensemble)
- **Scope**: Comprehensive (full deployment pipeline)
- **Resources**: High (GPU required for DL)
- **Risk**: Over-engineering

### Which to Choose?
**Use GPT-5 plan when:**
- Limited time/resources available
- Need quick validation of concept
- Want iterative refinement approach
- Focus on variable importance analysis
- Prefer simpler, maintainable code

**Use Claude Opus plan when:**
- Long-term strategic project
- Resources available for full implementation
- Need comprehensive system architecture
- Want production-ready deployment
- Willing to invest in deep learning

## Notes
- **Practical and focused** - Narrower scope easier to complete
- **Backtester integration critical** - Success depends on STOM wrapper quality
- **Overfitting risk** - 200-500 trials may overfit, validate carefully
- **Quick wins possible** - Can see results in days, not weeks
- **Iteration-friendly** - Easy to refine and expand incrementally
- **Documentation concise** - Keep docs actionable, not exhaustive
- **Realistic expectations** - Sharpe 1.0/0.8 targets are achievable but not guaranteed
- **Human oversight required** - Automated optimization needs expert review
- **Version G specificity** - This is a specific version, may have been refined from earlier versions
- **Complementary approach** - Can combine with Claude Opus insights for hybrid strategy
