<!-- Parent: ../AGENTS.md -->
# Trading Condition Documentation

## Purpose

This directory contains **133 trading strategy condition files** with **98.3% documentation compliance**, serving as the central repository for all STOM trading strategy documentation. The condition files define buy/sell logic, optimization parameters, and backtesting configurations for both tick-level (second-by-second) and minute-level trading strategies.

**Key Statistics (2025-11-29)**:
- Total condition files: 133 (Tick: 72, Min: 61)
- Documentation compliance: 98.3% (119/121 fully compliant)
- Strategy types: High-frequency tick strategies, technical indicator-based minute strategies
- Optimization coverage: BO, BOR, SO, SOR, OR, GAR sections

## Key Files

**Root Directory**:
- `README.md` - Comprehensive overview of all condition documentation with statistics, workflow, and recent updates
- `Condition_Detail_Check_and_Plan.md` - Documentation quality control plan and phase completion records

**Template & Guidelines**:
- Referenced: `../Guideline/Condition_Document_Template_Guideline.md` - Standard template structure
- Referenced: `../Guideline/Back_Testing_Guideline_Tick.md` - Tick strategy backtesting guide (826 documented variables)
- Referenced: `../Guideline/Back_Testing_Guideline_Min.md` - Minute strategy backtesting guide (752 documented variables)

## Subdirectories

### `Tick/` - Tick-Level Trading Strategies (72 files)

**Purpose**: Second-by-second high-frequency trading strategies focused on capturing rapid price movements during market opening hours.

**Key Characteristics**:
- Time interval: 1-second tick data
- Primary trading hours: Market open (09:00-09:30)
- Database: `stock_tick_back.db`
- Key variables: 초당거래대금 (per-second trading value), 체결강도 (execution strength), 초당매수/매도수량 (per-second buy/sell volume)

**Structure**:
- `1_To_be_reviewed/` - 63 strategies awaiting initial review
- `2_Under_review/` - 9 strategies currently under active review
- `20250808_study/` - Specific date-based research materials
- `README.md` - Detailed tick strategy catalog with star ratings

**Gold Standard Examples** (⭐⭐⭐⭐⭐):
- `Condition_Tick_902_905_update_2.md` - Production-ready 09:02-09:05 strategy
- `Condition_Tick_900_920.md` - Multi-timeframe split strategy

**For AI Agents**: Tick strategies require deep understanding of market microstructure, order book dynamics, and ultra-low latency execution patterns. Focus on opening volatility capture and momentum detection using per-second metrics.

### `Min/` - Minute-Level Trading Strategies (61 files)

**Purpose**: Minute candlestick-based swing and day trading strategies using technical indicators for entire trading session.

**Key Characteristics**:
- Time interval: 1-minute candlestick data
- Primary trading hours: Full session (09:00-15:30)
- Database: `stock_min_back.db`
- Key variables: 분봉시가/고가/저가 (OHLC), TA-Lib indicators (MACD, RSI, Bollinger Bands)

**Structure**:
- `1_To_be_reviewed/` - 45 strategies awaiting initial review
- `2_Under_review/` - 5 strategies currently under active review
- `Idea/` - 15 strategy ideas and AI-generated concepts
- `README.md` - Detailed minute strategy catalog with classifications

**Notable Examples**:
- `Condition_Find_1_Min.md` - Fundamental minute-based strategy
- `Condition_Stomer_Min.md` - STOM standard minute strategy
- `Condition_MACD_Precision_System.md` (Idea/) - MACD-based precision system

**For AI Agents**: Minute strategies leverage technical analysis patterns and indicator combinations. Focus on trend following, mean reversion, and multi-indicator confirmation systems. Understand TA-Lib integration patterns.

### `Idea/` - Strategy Ideas and AI-Generated Plans

**Purpose**: Repository for AI-generated strategy plans, experimental concepts, and research documents from GPT-5 and Claude Opus.

**Structure**:
- `Plan_from_GPT5/` - 14 documents including strategy surveys, ML/DL plans, and program development roadmaps (versionG)
- `Plan_from_claude_opus/` - 12 documents including alternative strategy approaches, data pipelines, and deployment guides

**Key Documents**:
- `Condition_Survey_Idea.md` - Comprehensive strategy idea surveys (both AI versions)
- `ML_DL_Backtesting_Optimization_Ideas.md` - Machine learning integration concepts
- `00_Overview.md` / `00_Summary.md` - Project overview documents (AI-specific versions)

**For AI Agents**: These are experimental and conceptual materials requiring validation before production use. Treat as research references rather than proven strategies. Cross-reference with actual backtesting results before implementation.

### `Reference/` - External References and Learning Materials

**Purpose**: External trading knowledge from PyTrader framework and YouTube educational content on order book analysis.

**Structure**:
- `PyTrader/` - 2 documents: Real trading conditions and sell condition patterns from PyTrader framework
- `YouTube/` - 6 documents: Order book analysis tutorials, market maker behavior, and short-term trading techniques

**For AI Agents**: Use these as supplementary educational materials to understand market microstructure concepts, order book dynamics, and practitioner knowledge. Not directly executable strategies but valuable context for understanding trading patterns.

## For AI Agents

### Primary Responsibilities

**Documentation Maintenance**:
1. **Template Compliance**: Ensure all condition files follow `Condition_Document_Template_Guideline.md` structure
2. **Optimization Sections**: Verify presence of all six required sections (BO, BOR, SO, SOR, OR, GAR)
3. **Variable Documentation**: Maintain `self.vars[i]` index mapping with clear comments (meaning, unit, range, interval, count)
4. **Code-Documentation Alignment**: Keep condition code synchronized with documentation (98.3% compliance target)

**Section Structure Requirements**:
- **BO (Buy Optimization)**: Actual optimized buy conditions with concrete values
- **BOR (Buy Optimization Range)**: Variable ranges for grid search `[min, max, step]`
- **SO (Sell Optimization)**: Actual optimized sell conditions with concrete values
- **SOR (Sell Optimization Range)**: Sell parameter ranges for grid search
- **OR (Overall Range)**: Top 10 most important variables only (consolidated)
- **GAR (Genetic Algorithm Range)**: Format `[min, max]` without step (for genetic algorithms)

**Validation Rules**:
- `self.vars[0]`: Reserved for fixed values (not optimized)
- `self.vars[1+]`: Optimization variables (buy first, then sell)
- Continuous indexing required (no gaps)
- Range function parentheses mandatory: `이동평균(30)`, not `이동평균30`
- NumPy compatibility: No chained comparisons (`a < b < c` → `a < b and b < c`)
- Range step validation: `(max - min) % step == 0` (Optuna compatibility)
- Maximum 20 values per variable: `(max - min) / step + 1 ≤ 20`

**Review Process Integration**:
- Track strategy progression through 3-stage review: `1_To_be_reviewed/` → `2_Under_review/` → `3_Review_finished/`
- Update statistics after moving files between review stages
- Maintain README.md accuracy with file counts and status

**Code Analysis Patterns**:
- Korean variable names preserved: 현재가 (current price), 시가 (open), 고가 (high), 저가 (low), 등락율 (rate of change)
- Buy logic starts with `True`, sell logic starts with `False` (2.6 convention)
- First condition uses `if`, subsequent conditions use `elif` (2.8 chain structure)
- Common calculation indicators grouped at section top to avoid duplication

### Working with Strategy Documents

**When Creating New Strategies**:
1. Copy template structure from gold standard examples
2. Define time range, target securities, strategy type, core variables
3. Write common calculation indicators first (avoid duplication)
4. Implement buy/sell logic with proper `self.vars[]` indexing
5. Generate all six optimization sections (BO, BOR, SO, SOR, OR, GAR)
6. Add improvement research section (minimum 3 ideas with priorities)
7. Calculate expected case count and optimization time estimates

**When Reviewing Existing Strategies**:
1. Verify all 14 mandatory checklist items (section 0 of template guideline)
2. Check variable indexing continuity and mapping comments
3. Validate range parameters against NumPy/Optuna compatibility rules
4. Confirm backtesting code compatibility with STOM framework
5. Ensure no ambiguous terms ("적당히", "유동적으로" prohibited)
6. Cross-reference with backtesting guideline variable definitions

**Quality Assurance**:
- Gold standard target: ⭐⭐⭐⭐⭐ (like `Condition_Tick_902_905_update_2.md`)
- Minimum production standard: ✅ (98.3% template compliance)
- Research stage acceptable: 📊 (partial documentation OK during development)
- AI-generated requires: 🔍 (mandatory validation before production use)

### Integration Points

**Database Dependencies**:
- Tick strategies: `stock_tick_back.db` schema (108 columns documented)
- Minute strategies: `stock_min_back.db` schema (93 columns documented)
- Strategy storage: `strategy.db` (condition code and parameters)
- Results tracking: `backtest.db`, `tradelist.db`

**Code Module Links**:
- Backtesting engines: `backtester/backengine_*_*.py` (12 market × timeframe combinations)
- Strategy execution: `stock/kiwoom_strategy_tick.py`, `coin/*_strategy_min.py`
- Optimization: `backtester/optimiz.py` (grid search), `backtester/optimiz_genetic_algorithm.py` (GA)

**Workflow Coordination**:
- Condition documents → Backtesting → Optimization → Production deployment
- Documentation updates must precede code changes
- Maintain bidirectional traceability between code and documentation

## Dependencies

**Core Guidelines** (must read):
- `../Guideline/Condition_Document_Template_Guideline.md` - 14-point compliance checklist, template structure, variable mapping rules
- `../Guideline/Back_Testing_Guideline_Tick.md` - 826 documented tick variables, database schema, calculation formulas
- `../Guideline/Back_Testing_Guideline_Min.md` - 752 documented minute variables, TA-Lib indicators, database schema

**Supporting Documentation**:
- `../Guideline/Stock_Database_Information.md` - Database structures (15 SQLite databases)
- `../Manual/` - System architecture and component interaction patterns
- `/backtester/` - Backtesting engine implementation (23 files, ~12,993 lines)

**Tool Dependencies**:
- Python 64-bit required
- TA-Lib (custom wheel in `/utility/`)
- SQLite database layer
- Optuna optimization framework
- NumPy/Pandas data processing

**Version Control**:
- All condition files tracked in git
- Documentation compliance tracked through manual reviews
- Phase completion records in `Condition_Detail_Check_and_Plan.md`
- Recent milestone: Phase 1-5 completion (2025-11-23) achieving 98.3% compliance

---

**Last Updated**: 2025-11-29
**Document Version**: 1.0
**Compliance Status**: 98.3% (119/121 files fully compliant)
