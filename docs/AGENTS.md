<!-- Parent: ../AGENTS.md -->
# Documentation System

## Purpose

Comprehensive documentation system for STOM (System Trading Optimization Manager) V1 with 175+ markdown files covering all aspects of system architecture, trading strategies, development guidelines, and user manuals. This directory serves as the central knowledge repository for:

- **Trading strategy documentation** (133 condition files, 98.3% compliance)
- **System manuals and architecture** (10 major sections)
- **Development guidelines and standards** (5 core guidelines + 8 user manuals)
- **Research reports and analysis** (10+ studies)
- **Learning resources and references**

## Key Files

- **README.md** - Main documentation hub with complete navigation guide (540 lines)
- **Condition_Update_Plan.md** - Condition documentation update planning and tracking

## Subdirectories

### **Manual/** - System Documentation
Comprehensive 10-section system documentation covering entire STOM architecture:

- **01_Overview/** - Project scope, goals, and technical stack overview
- **02_Architecture/** - System architecture, multiprocess design, and data flow patterns
- **03_Modules/** - Detailed analysis of stock, coin, ui, utility, and backtester modules
- **04_API/** - Integration patterns for Kiwoom, Upbit, and Binance APIs
- **05_UI_UX/** - Interface components, event handling, and chart rendering
- **06_Data/** - Database structure (15 SQLite DBs), schema, and management
- **07_Trading/** - Strategy execution engine, order management, risk controls
- **08_Backtesting/** - Backtesting engines, optimization systems (grid search, genetic algorithms)
- **09_Manual/** - User guides for installation, usage, and troubleshooting
- **10_Conclusion/** - API references, diagrams, glossary, and appendices
- **11_etc/** - Additional resources and miscellaneous documentation
- **DOCUMENTATION_GUIDE.md** - Automated validation procedures and quality standards

### **Condition/** - Trading Strategy Documentation (133 files, 98.3% compliant)
All trading condition files with standardized documentation format:

- **Tick/** (72 files) - High-frequency tick strategies (second-level)
  - 8 categories: Time-based (27), Momentum (8), Volume (6), Order Book (7), Gap/Breakout (7), Reversal (6), Special (5), Research (17)
  - Gold standards: Condition_Tick_902_905_update_2.md, Condition_Tick_900_920_Enhanced.md
  - Subdirectory: `20250808_study/` - Strategy research and testing
- **Min/** (61 files) - Minute-based strategies with technical indicators
  - 10 categories: MACD (5), RSI (4), Bollinger Bands (6), Moving Average (5), Volume (4), Stochastic (3), Complex (3), Other indicators (7), Patterns (6), Research (15)
  - Subdirectory: `Idea/` - Strategy concepts and AI-generated ideas
- **Idea/** (26 files) - AI-generated strategy concepts
  - `Plan_from_GPT5/` (14 files) - GPT-5 based strategy plans
  - `Plan_from_claude_opus/` (12 files) - Claude Opus based strategy plans
- **Reference/** (8 files) - External references and learning materials
  - `PyTrader/` (2 files) - PyTrader reference materials
  - `YouTube/` (6 files) - Order book analysis tutorials

### **Guideline/** - Development Standards
Development guidelines and documentation templates:

- **Back_Testing_Guideline_Tick.md** (33KB, 826 variables) - Complete tick backtesting guide
- **Back_Testing_Guideline_Min.md** (25KB, 752 variables) - Complete minute backtesting guide
- **Condition_Document_Template_Guideline.md** (32KB, 850+ lines) - Condition documentation template with 42 checkpoints
- **Stock_Database_Information.md** (20KB) - Database schema documentation (108 minute columns, 93 tick columns)
- **Manual_Generation_Guideline.md** (31KB) - Project analysis and documentation strategy guide
- **Variable_Management_Guide.md** - Variable naming and management conventions
- **사용설명서/** (8 files) - Korean user manuals in 4 parts (summary + detailed)

### **Study/** - Research and Analysis
Research reports, system analysis, and documentation reviews:

- **ResearchReports/** (4 files) - AI/ML trading automation research (XGBoost, SHAP, Genetic Programming, LLM)
- **SystemAnalysis/** (3 files) - System optimization, Git branch structure analysis
- **ConditionStudies/** (2 files) - In-depth trading condition analysis
- **DocumentationReviews/** (1 file) - Documentation quality verification (106 docs, 4.5/5 quality)
- **Guides/** (1 file) - Condition optimization and analysis guides
- **CodeReview/** - Technical code review documents
- **Development/** - Development process documentation
- Root-level studies: Backtesting analysis, segment filter studies, exec-to-function migration design

### **learning/** - Learning Resources (13 files)
Progressive learning path for STOM system:

- **01-시작하기.md** - Getting started guide
- **02-아키텍처-개요.md** - Architecture overview
- **03-주식거래-시스템.md** - Stock trading system
- **04-암호화폐-시스템.md** - Cryptocurrency system
- **05-백테스팅-시스템.md** - Backtesting system
- **06-데이터베이스-구조.md** - Database structure
- **07-UI-시스템.md** - UI system
- **08-프로세스-통신.md** - Process communication (queues, ZMQ, WebSocket)
- **09-커스터마이징-가이드.md** - Customization guide
- **10-전략-개발-가이드.md** - Strategy development guide
- **11-최적화-가이드.md** - Optimization guide
- **12-문제해결-가이드.md** - Troubleshooting guide

### **CodeReview/** - Code Review Documents
Technical analysis and code review documents:

- **Backtesting_Data_Loading_Multicore_Analysis.md** - Multicore performance analysis

### **dev_plan/** - Development Plans
Development planning and tracking documents:

- **20260105_Segment_Filter_Consistency_Fix_V2_Master_Plan.md** - Master plan for segment filter fixes

### **Error_Log/** - Error Documentation
Error tracking and resolution documentation

### **Plan/** - Project Planning
Project-level planning documents and roadmaps

### **update_log/** - Update Logs
Change logs and update tracking for documentation and code

### **가상환경구축연구/** - Virtual Environment Research
Korean directory for virtual environment setup and management research

## For AI Agents

### Documentation Maintenance

**Quality Standards:**
- **98.3% compliance target** for condition documentation (119/121 files currently compliant)
- All condition files must follow `Condition_Document_Template_Guideline.md`
- Each file requires: BO (Buy Optimization), BOR (ranges), SO (Sell Optimization), SOR (ranges), OR (Overall Range), GAR (Genetic Algorithm Range)
- Automated validation via `DOCUMENTATION_GUIDE.md`

**When Modifying Documentation:**
1. **Read before editing** - Always read entire file before making changes
2. **Preserve Korean** - Keep Korean variable names (현재가, 시가, 고가, 저가, 등락율)
3. **Follow templates** - Strictly adhere to established documentation templates
4. **Update cross-references** - Update all related documents when making changes
5. **Maintain compliance** - Ensure 98.3%+ guideline compliance rate
6. **Verify code alignment** - Keep documentation synchronized with source code

**Adding New Documentation:**
1. Identify appropriate subdirectory (Manual/, Condition/, Guideline/, Study/)
2. Copy relevant template or reference existing high-quality documents
3. Follow naming conventions: `Condition_[Type]_[Strategy].md` or `[Category]_[Topic].md`
4. Update parent README.md to include new document
5. Add cross-references to related documents
6. Validate against documentation guidelines before committing

**Condition Files:**
- **Tick strategies** → `Condition/Tick/` directory
- **Minute strategies** → `Condition/Min/` directory
- Must include all optimization sections (BO, BOR, SO, SOR, OR, GAR)
- Reference source files: `stock/kiwoom_strategy_tick.py` or `*_min.py`
- Document optimization ranges for grid search and genetic algorithms

**Manual Updates:**
- System architecture changes → `Manual/02_Architecture/`
- Module functionality → `Manual/03_Modules/`
- API integration → `Manual/04_API/`
- UI/UX changes → `Manual/05_UI_UX/`
- Database schema → `Manual/06_Data/` + `Guideline/Stock_Database_Information.md`

**Research Documentation:**
- Analysis reports → `Study/ResearchReports/`
- System studies → `Study/SystemAnalysis/`
- Condition analysis → `Study/ConditionStudies/`
- Code reviews → `Study/CodeReview/` or `CodeReview/`

**Validation Process:**
1. Run automated validation checks from `DOCUMENTATION_GUIDE.md`
2. Self-check procedure for condition files
3. Verify code snippet references link to actual source files
4. Manual review for complex sections
5. Update compliance statistics in README.md

**Documentation Architecture:**
- **175+ markdown files** spanning entire system
- **Hierarchical structure** with README files at each level
- **Cross-linked navigation** between related documents
- **Evidence-based** - all documentation backed by actual code/tests/results

### Common Tasks

**Finding Variable Definitions:**
- Tick variables: `Guideline/Back_Testing_Guideline_Tick.md` (826 variables)
- Minute variables: `Guideline/Back_Testing_Guideline_Min.md` (752 variables)
- Database columns: `Guideline/Stock_Database_Information.md`

**Creating New Strategy Documentation:**
1. Read appropriate guideline (Tick or Min)
2. Copy template from `Guideline/Condition_Document_Template_Guideline.md`
3. Analyze gold standard examples:
   - Tick: `Condition/Tick/Condition_Tick_902_905_update_2.md`
   - Min: `Condition/Min/Condition_Find_1_Min.md`
4. Document strategy with all required sections
5. Validate against 42-point checklist
6. Save to appropriate directory (Tick/ or Min/)

**Understanding System Architecture:**
1. Start with `Manual/README.md` for overview
2. Read `Manual/02_Architecture/system_architecture.md`
3. Study module-specific docs in `Manual/03_Modules/`
4. Review process communication in `learning/08-프로세스-통신.md`

**Troubleshooting Documentation Issues:**
- Check `Manual/09_Manual/user_manual.md` for user-facing issues
- Review `learning/12-문제해결-가이드.md` for common problems
- Consult `Error_Log/` for known error patterns
- Reference `Study/DocumentationReviews/` for quality issues

## Dependencies

- **Markdown** - All documentation in Markdown format (.md)
- **Documentation tools** - Validation scripts, template generators
- **Cross-references** - Extensive internal linking between documents
- **Source code** - Documentation synchronized with actual codebase in `../stock/`, `../coin/`, `../ui/`, `../backtester/`, `../utility/`
- **Database** - Schema documentation tied to SQLite databases in `../_database/`

## Project Context

**Project:** STOM V1 (System Trading Optimization Manager)
**Language:** Python 3.x with PyQt5
**Trading Markets:** Korean stocks (Kiwoom), Cryptocurrency (Upbit, Binance)
**Scale:** 157 Python files (~70,000+ lines), 175+ markdown docs
**Architecture:** Multiprocess (15 queues), real-time WebSocket/ZMQ
**Documentation Date:** 2025-12-20

For system-wide context, see `../CLAUDE.md` and parent directory `../AGENTS.md`.
