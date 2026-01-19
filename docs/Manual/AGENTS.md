<!-- Parent: ../AGENTS.md -->
# System Manual Documentation

## Purpose

Comprehensive system documentation for STOM (System Trading Optimization Manager) V1, organized into 10 numbered sections plus additional resources. This directory provides complete technical documentation covering architecture, modules, APIs, data management, trading execution, backtesting systems, and user guides.

**Documentation Scope:**
- Complete system architecture and design patterns
- Detailed module-level analysis (stock, coin, ui, utility, backtester)
- API integration specifications for Kiwoom, Upbit, and Binance
- Database schema and management (15 SQLite databases)
- Trading engine and execution logic
- Backtesting and optimization frameworks
- User manuals and troubleshooting guides
- Code-verified documentation with 98%+ accuracy

## Key Files

- **README.md** - Main manual hub with navigation to all 10 sections plus conclusion (96 lines)
- **DOCUMENTATION_GUIDE.md** - Automated validation procedures for maintaining documentation-code alignment

## Subdirectories

### **01_Overview/** - Project Overview
High-level project introduction including scope, goals, major features, technical stack overview, and licensing information. Entry point for understanding STOM's purpose and capabilities.

**Reference:** `01_Overview/project_overview.md`

### **02_Architecture/** - System Architecture
Complete system design documentation covering multiprocess architecture, 15-queue communication system, data flow patterns, process coordination, and design patterns (Strategy, Observer, Factory, Singleton, Template Method, Command).

**Reference:** `02_Architecture/system_architecture.md`

### **03_Modules/** - Module Analysis
In-depth technical analysis of all five major modules:
- **stock_module.md** - Korean stock trading via Kiwoom API (9 files, ~7,800 lines)
- **coin_module.md** - Cryptocurrency trading for Upbit and Binance (16 files, ~10,098 lines)
- **ui_module.md** - PyQt5 interface components (70+ files, ~20,625 lines)
- **utility_module.md** - Shared utilities and database management (24 files, ~3,419 lines)
- **backtester_module.md** - Backtesting engines and optimization (23 files, ~12,993 lines)

**Reference:** `03_Modules/modules_analysis.md` (central hub)

### **04_API/** - API Integration
API integration patterns and specifications for all supported trading platforms:
- Kiwoom OpenAPI (ZMQ-based manager pattern)
- Upbit REST + WebSocket
- Binance REST + WebSocket
- Authentication, credential encryption, and connection management

**Reference:** `04_API/api_integration.md`

### **05_UI_UX/** - User Interface Analysis
PyQt5 interface design documentation covering:
- Main window structure (`ui_mainwindow.py` - 1,083 lines)
- Event handlers (`ui_button_clicked_*.py` pattern)
- Data display updates (`ui_update_*.py` pattern)
- Chart rendering (`ui_draw_*.py` - candlesticks, real-time, TreeMap)
- Style management and layout configuration

**Reference:** `05_UI_UX/ui_ux_analysis.md`

### **06_Data/** - Data Management
Complete database architecture documentation:
- 15 SQLite databases in `/_database/` directory
- Schema specifications (108 minute columns, 93 tick columns documented)
- Setting management (`setting.db` with encrypted credentials)
- Market data storage (tick, minute, trade history)
- Query process and database integrity verification

**Reference:** `06_Data/data_management.md`
**Cross-reference:** `../Guideline/Stock_Database_Information.md`

### **07_Trading/** - Trading Engine
Real-time trading execution documentation:
- Strategy engines (`*_strategy_*.py` - signal generation)
- Trader processes (`*_trader.py` - order execution and position management)
- Receiver processes (`*_receiver_*.py` - real-time data collection)
- Risk controls and position sizing
- Order lifecycle management

**Reference:** `07_Trading/trading_engine.md`

### **08_Backtesting/** - Backtesting System
Comprehensive backtesting framework documentation:
- 12 market-specific engines (`backengine_*_*.py`)
- Grid search optimization (`backtester/optimiz.py`)
- Genetic algorithm optimization (`backtester/optimiz_genetic_algorithm.py`)
- Performance metrics and validation
- Strategy parameter tuning

**Reference:** `08_Backtesting/backtesting_system.md`
**Cross-reference:** `../Guideline/Back_Testing_Guideline_Tick.md`, `../Guideline/Back_Testing_Guideline_Min.md`

### **09_Manual/** - User Guides
End-user documentation and operational guides:
- Installation procedures (`pip_install_64.bat`)
- System startup and execution (`stom.bat`, `stom_stock.bat`, `stom_coin.bat`)
- Configuration management
- Troubleshooting common issues
- Best practices and operational workflows

**Reference:** `09_Manual/user_manual.md`
**Cross-reference:** `../learning/` directory (13 Korean learning guides)

### **10_Conclusion/** - References and Appendices
Supporting documentation and reference materials:
- API reference tables
- System diagrams and flowcharts
- Glossary of terms (Korean trading terminology)
- Appendices with additional technical details
- Summary of findings and recommendations

**Reference:** `10_Conclusion/conclusion.md`

### **11_etc/** - Additional Resources
Miscellaneous documentation, supplementary materials, and resources that don't fit into the primary 10 sections.

## For AI Agents

### Documentation Maintenance Standards

**Code-Documentation Alignment:**
- All documentation MUST be verified against actual source code
- File paths, class names, method signatures must match reality
- Code snippets must reference actual implementations
- Configuration values must reflect current system state
- Command examples must be executable and tested

**Validation Process:**
1. Read `DOCUMENTATION_GUIDE.md` for automated validation procedures
2. Verify all file paths exist and are correct
3. Check class/method names against actual code
4. Test all command examples
5. Validate configuration values and constants
6. Update "최근 검증일" (Last Verification Date) in README.md

**Recent Verification (2025-11-26):**
- Path corrections: `STOM_V1/` → `STOM/`
- Command updates: `python main.py` → `python stom.py`
- Architecture patterns verified against actual implementation
- Queue system validated (15 queues in qlist)
- Module statistics updated with actual file counts

### Modifying Manual Documentation

**Before Making Changes:**
1. **Read entire target file** - Never edit without reading first
2. **Verify current state** - Check if documentation matches code
3. **Identify affected sections** - Map which manual sections need updates
4. **Check cross-references** - Find related documents that need coordination

**Making Changes:**
1. **Preserve Korean terminology** - Keep technical terms like 현재가, 시가, 고가, 저가, 등락율
2. **Update all affected sections** - Architecture changes may impact multiple manual sections
3. **Maintain structural consistency** - Follow existing markdown formatting and hierarchy
4. **Add verification markers** - Note changes in README.md verification history

**Which Section to Update:**
- System design changes → `02_Architecture/`
- Module functionality changes → `03_Modules/[specific_module].md`
- API integration changes → `04_API/`
- UI/UX changes → `05_UI_UX/`
- Database schema changes → `06_Data/` + `../Guideline/Stock_Database_Information.md`
- Trading logic changes → `07_Trading/`
- Backtesting changes → `08_Backtesting/` + `../Guideline/Back_Testing_Guideline_*.md`
- User-facing changes → `09_Manual/`
- New appendices → `10_Conclusion/`

**Cross-Directory Impact:**
- Architecture changes often require updates to `../learning/02-아키텍처-개요.md`
- Database changes must update `06_Data/` AND `../Guideline/Stock_Database_Information.md`
- Backtesting changes need coordination with `../Condition/` documentation
- All major changes should be reflected in project root `../CLAUDE.md`

### Adding New Sections

**Expansion Guidelines:**
- New major features → Consider adding to appropriate numbered section (01-10)
- Cross-cutting concerns → May need updates across multiple sections
- Experimental features → Document in `11_etc/` until stabilized
- Research findings → Consider `../Study/` directory instead

**Structural Integrity:**
- Maintain 10-section organization for major documentation
- Use `11_etc/` for overflow and miscellaneous content
- Keep README.md navigation accurate
- Preserve hierarchical numbering (01-10)

### Documentation Architecture Patterns

**Hierarchical Structure:**
```
Manual/
├── README.md (central hub)
├── DOCUMENTATION_GUIDE.md (validation procedures)
├── 01_Overview/ → Entry point
├── 02_Architecture/ → System design
├── 03_Modules/ → Detailed implementation
├── 04_API/ → External integrations
├── 05_UI_UX/ → User interface
├── 06_Data/ → Data layer
├── 07_Trading/ → Business logic
├── 08_Backtesting/ → Testing & optimization
├── 09_Manual/ → User documentation
├── 10_Conclusion/ → References & appendices
└── 11_etc/ → Miscellaneous
```

**Cross-Reference Network:**
- Manual sections reference source code files directly
- Code-to-doc traceability through file paths
- Related documentation linked via markdown references
- Learning guides (`../learning/`) mirror manual structure

**Quality Gates:**
- All code references must be verified
- Command examples must be tested
- Statistics must be current (line counts, file counts)
- Korean terminology preserved and consistent
- Validation date must be updated after verification

### Common Tasks

**Verifying Architecture Documentation:**
1. Read `02_Architecture/system_architecture.md`
2. Compare queue system description against `utility/setting.py` (qlist definition)
3. Verify multiprocess structure against actual process files
4. Check design patterns against code implementations
5. Update any discrepancies and note in README.md

**Updating Module Documentation:**
1. Identify affected module(s) in `03_Modules/`
2. Read current module documentation
3. Compare against actual source files in `../stock/`, `../coin/`, `../ui/`, etc.
4. Update file counts, line counts, class names
5. Verify code snippets still accurate
6. Check cross-references to other manual sections

**Synchronizing with Code Changes:**
1. When source code changes, identify affected manual sections
2. Read both old documentation and new code
3. Update technical details (class names, methods, patterns)
4. Preserve user-facing explanations unless behavior changed
5. Update verification date in README.md
6. Consider impact on `../learning/` guides and `../CLAUDE.md`

**Handling Database Schema Changes:**
1. Update `06_Data/data_management.md` with schema changes
2. Update `../Guideline/Stock_Database_Information.md` with column details
3. Update affected module documentation (usually `03_Modules/utility_module.md`)
4. Update `../learning/06-데이터베이스-구조.md` if user-impacting
5. Verify all references to database structure across manual

## Dependencies

- **Source Code** - Documentation references actual code in `../stock/`, `../coin/`, `../ui/`, `../backtester/`, `../utility/`
- **Database** - Schema documentation tied to SQLite databases in `../_database/`
- **Guidelines** - Cross-references to `../Guideline/` for detailed specifications
- **Learning Resources** - Parallel structure with `../learning/` directory
- **Condition Documentation** - Trading strategies documented in `../Condition/`
- **Markdown** - All documentation in Markdown format with consistent hierarchy

## Project Context

**System:** STOM V1 (System Trading Optimization Manager)
**Architecture:** Multiprocess PyQt5 application with 15-queue communication
**Markets:** Korean stocks (Kiwoom OpenAPI), Cryptocurrency (Upbit, Binance)
**Scale:** 157 Python files (~70,000+ lines), 175+ markdown files
**Documentation Strategy:** Code-verified, hierarchical, cross-referenced
**Quality Target:** 98%+ code-documentation alignment

For broader project context, see parent `../AGENTS.md` and project root `../CLAUDE.md`.
