<!-- Parent: ../AGENTS.md -->
# Claude Opus Strategy Plans

## Purpose
Claude Opus 모델이 생성한 ML/DL 기반 전략 개발 계획 및 시스템 아키텍처 제안. 포괄적이고 체계적인 접근 방식으로 장기적 전략 프레임워크를 제시합니다.

## Overview
- **Total files**: 12 files (7 in subdirectory)
- **Focus**: Systematic ML/DL strategy optimization framework
- **Approach**: Comprehensive 4-phase development roadmap
- **Scope**: Data pipeline, model development, backtesting integration, deployment

## Key Files

### Root Level (5 files)
- **Back_Testing_Guideline_Min.md** (25KB) - 분봉 백테스팅 가이드라인 제안 (752개 문서화된 변수)
- **Back_Testing_Guideline_Tick.md** (33KB) - 틱 백테스팅 가이드라인 제안 (826개 문서화된 변수)
- **Condition_Survey_Idea.md** (4KB) - 조건식 서베이 및 아이디어 제안
- **ML_DL_Backtesting_Optimization_Ideas.md** (51KB) - ML/DL 백테스팅 최적화 종합 아이디어
- **Stock_Database_Information.md** (2.5KB) - 데이터베이스 정보 참조

### program_develop_document/ (7 files)
체계적인 ML/DL 트레이딩 시스템 개발 계획:

- **00_Summary.md** - 전체 프로젝트 요약 및 실행 가이드
  - 4주 개발 로드맵
  - 기술 스택: Python 3.9+, PyTorch, LightGBM, SQLite
  - 예상 성과: 조건식 탐색 속도 1000x, 백테스팅 600x 개선

- **01_project_overview.md** - 프로젝트 개요 및 아키텍처
  - 전체 시스템 아키텍처 설계
  - 4단계 개발 로드맵 (MVP → Core → Advanced → Production)
  - 성능 목표 및 KPI 설정

- **02_data_pipeline.md** - 데이터 파이프라인 구현
  - SQLite 데이터베이스 연동 (54개 컬럼)
  - 특성 엔지니어링 (가격, 거래량, 호가창, 기술적 지표)
  - 데이터 전처리, 정규화, 캐싱, 병렬 처리

- **03_model_development.md** - 단계별 모델 개발
  - Phase 1: LightGBM 프로토타입 (Optuna 최적화)
  - Phase 2: LSTM 딥러닝 모델 (Attention 메커니즘)
  - Phase 3: 앙상블 모델
  - GPU 최적화 및 Mixed Precision Training

- **04_backtesting_integration.md** - 백테스팅 통합
  - 실전 거래 시뮬레이션 엔진
  - 리스크 관리 (손절, 익절, 트레일링 스탑)
  - STOM 조건식 변환기
  - 성과 평가 및 리포팅

- **05_deployment_guide.md** - 배포 및 운영
  - 환경 설정 (Windows/Linux)
  - FastAPI 기반 예측 서버
  - Streamlit 모니터링 대시보드
  - 시스템 모니터링 및 유지보수

- **Stock_Database_Information.md** - 데이터베이스 스키마 참조

## Characteristics

### Claude Opus Strengths
- **Long-form detailed analysis** - 종합적이고 상세한 설명
- **Comprehensive strategy frameworks** - 포괄적 전략 프레임워크
- **Structured approach** - 체계적 문제 해결 접근법
- **Systematic methodology** - 시스템적 방법론
- **Risk-aware planning** - 리스크 인식 계획
- **Long-term strategic vision** - 장기 전략적 비전

### Technical Approach
- **4-Phase Development**:
  1. MVP: LightGBM baseline with basic backtesting
  2. Core: LSTM model with GPU optimization
  3. Advanced: Ensemble models and advanced risk management
  4. Production: API deployment and monitoring dashboard

- **Technology Stack**:
  - ML: LightGBM, XGBoost, Optuna
  - DL: PyTorch, LSTM, Attention mechanisms
  - Data: SQLite, pandas, numpy
  - Deployment: FastAPI, Streamlit

- **Performance Targets**:
  - Strategy search: 1000x faster (1 per hour → 1000 per hour)
  - Backtesting: 600x faster (10 min/condition → 1 sec/condition)
  - Profitability: +20~50% improvement
  - Risk (MDD): 25% improvement (-20% → -15%)

## For AI Agents

### Working with Claude Opus Plans

**When to Use:**
- System architecture design needed
- Long-term strategic planning required
- Comprehensive risk analysis necessary
- Multi-phase development roadmap needed
- Complex multi-component integration
- Detailed technical specifications required

**Validation Approach:**
1. **Assess scope** - Plans are comprehensive, break into manageable phases
2. **Check feasibility** - Verify required data/tools availability
3. **Prototype incrementally** - Implement MVP first, then expand
4. **Validate assumptions** - Test each phase before proceeding
5. **Document thoroughly** - Maintain alignment with original plan
6. **Measure progress** - Track KPIs and performance targets

**Implementation Guidelines:**
1. **Start with Phase 1 (MVP)**:
   - LightGBM baseline model
   - Basic data pipeline from SQLite
   - Simple backtesting integration
   - Performance benchmarking

2. **Validate before Phase 2**:
   - Confirm MVP achieves baseline metrics
   - Verify data quality and availability
   - Assess computational resources
   - Review and refine approach

3. **Expand to Deep Learning (Phase 2)**:
   - Only after ML baseline is solid
   - Requires GPU resources
   - Needs extensive hyperparameter tuning
   - More complex debugging

4. **Production Deployment (Phase 4)**:
   - Only after thorough backtesting
   - Requires monitoring infrastructure
   - Needs operational procedures
   - Risk management critical

### Critical Evaluation

**Strengths:**
- Comprehensive system design
- Well-structured development phases
- Realistic performance targets
- Risk-aware approach
- Production-ready architecture

**Considerations:**
- Ambitious scope - requires significant resources
- Complex technology stack - steep learning curve
- GPU requirements for deep learning phases
- Long development timeline (4+ weeks minimum)
- Requires expertise in ML, DL, and trading systems

**Risk Factors:**
1. **Over-engineering risk** - Complex systems harder to debug and maintain
2. **Data quality dependency** - Models only as good as underlying data
3. **Overfitting potential** - Sophisticated models may overfit to historical data
4. **Computational requirements** - GPU training, large memory footprint
5. **Integration complexity** - Existing STOM system integration challenges

## Dependencies

### Technical Requirements
- **Python 3.9+** - Core programming language
- **PyTorch** - Deep learning framework
- **LightGBM/XGBoost** - ML baseline models
- **Optuna** - Hyperparameter optimization
- **SQLite** - Database (existing STOM structure)
- **GPU (CUDA)** - For deep learning phases
- **FastAPI** - API deployment (Phase 4)
- **Streamlit** - Monitoring dashboard (Phase 4)

### STOM System Dependencies
- **Data access**: `_database/*.db` (SQLite databases)
- **Backtesting**: `backtester/backengine_*` integration
- **Strategy implementation**: `stock/kiwoom_strategy_*` pattern
- **Documentation**: Follow `docs/Guideline/` templates
- **Validation**: Existing condition documentation standards

### External Resources
- **Compute**: GPU for training (Phase 2+)
- **Storage**: Historical data storage (~10GB+ recommended)
- **Memory**: 16GB+ RAM for large-scale backtesting
- **Time**: 4+ weeks for full implementation

## Integration with STOM

### Data Integration
```python
# Claude plan uses existing STOM databases
from utility.setting import DB_STOCK_TICK, DB_STOCK_MIN
import sqlite3

# Data pipeline connects to STOM SQLite databases
conn = sqlite3.connect(DB_STOCK_TICK)
# Load tick/min data for feature engineering
```

### Backtesting Integration
```python
# Plan proposes wrapper around existing backtester
from backtester.backengine_stock_tick import BackEngineStockTick

# ML/DL models generate signals
# Backtester simulates trading with realistic costs
```

### Strategy Implementation
```python
# Validated models convert to STOM condition format
# Follow existing pattern:
# - BO/BOR for buy conditions
# - SO/SOR for sell conditions
# - Document in docs/Condition/Tick or Min
```

## Success Metrics

### Performance Targets (from Claude plan)
| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| Strategy search speed | 1/hour | 1000/hour | 1000x |
| Backtesting time | 10 min | 1 sec | 600x |
| Profitability | Baseline | +20-50% | 1.2-1.5x |
| Max Drawdown | -20% | -15% | 25% |

### Validation Criteria
- **Sharpe Ratio** ≥ 1.5
- **Win Rate** > 50%
- **Profit Factor** > 1.5
- **Consistency** across multiple periods
- **Robustness** to parameter variations

### Phase Completion Criteria
- **Phase 1 (MVP)**: LightGBM baseline outperforms random strategy
- **Phase 2 (Core)**: LSTM model improves on LightGBM baseline
- **Phase 3 (Advanced)**: Ensemble achieves target Sharpe ratio
- **Phase 4 (Production)**: System runs reliably in live environment

## Related Documentation
- **Parent**: `../AGENTS.md` - AI Strategy Ideas overview
- **Comparison**: `../Plan_from_GPT5/` - Alternative GPT-5 approach
- **Implementation**: `../../Tick/`, `../../Min/` - Production strategies
- **Guidelines**: `../../../Guideline/` - Documentation standards
- **Reference**: `ML_DL_Backtesting_Optimization_Ideas.md` - Comprehensive optimization ideas

## Notes
- **Comprehensive but ambitious** - Full implementation requires significant resources
- **Phased approach recommended** - Start with MVP, validate before expanding
- **GPU requirements** - Deep learning phases need GPU acceleration
- **Integration planning critical** - Ensure compatibility with existing STOM architecture
- **Documentation essential** - Maintain traceability from plan to implementation
- **Realistic expectations** - Performance targets are aspirational, validate incrementally
- **Risk management priority** - Don't sacrifice robustness for sophistication
- **Human oversight required** - AI plans need expert review and practical adjustment
