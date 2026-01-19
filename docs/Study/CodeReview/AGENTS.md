<!-- Parent: ../AGENTS.md -->
# Code Review Studies

## Purpose

This directory contains code quality verification reports, branch reviews, bug detection analyses, and architectural consistency checks. It serves as the central repository for ensuring code quality before merges, identifying data mapping bugs, and verifying adherence to STOM framework patterns.

**Key Objectives**:
- Pre-merge code quality verification
- Critical bug detection (P0, P1, P2 classification)
- Data mapping and type consistency validation
- Architectural compliance verification
- Quality scoring and improvement recommendations

## Key Files

### Branch Reviews

**2025-12-31_Segment_Final_Reset_Branch_Review.md** (9KB)
- Comprehensive branch review for segment filter final reset feature
- P0 bug detection: filter validation logic errors
- Data mapping verification across tick/minute databases
- Architecture consistency checks
- Quality score: 7.5/10 with specific improvement recommendations

### Documentation

**README.md**
- Code review documentation index
- Review template reference
- Quality standards documentation

## For AI Agents

### When Adding Code Review Documents

1. **File Naming Convention**: Use `YYYY-MM-DD_Feature_Description_Review.md` format
2. **Document Structure**: Include the following sections:
   - **Executive Summary**: Branch purpose, review scope, key findings
   - **Critical Issues (P0)**: Bugs that must be fixed before merge
   - **High Priority Issues (P1)**: Important improvements for immediate follow-up
   - **Medium Priority Issues (P2)**: Enhancements for future consideration
   - **Quality Assessment**: Objective score (0-10) with criteria breakdown
   - **Recommendations**: Prioritized action items
   - **Code Snippets**: Include actual code with line references
3. **Bug Prioritization**:
   - **P0 (Critical)**: Data corruption, security vulnerabilities, system crashes
   - **P1 (High)**: Performance issues, incorrect calculations, architectural violations
   - **P2 (Medium)**: Code quality, maintainability, minor inconsistencies
4. **Update README.md**: Add entry with review date, branch, key findings
5. **Cross-References**: Link to related code files, documentation, and study reports

### When Conducting Code Reviews

1. **Pre-Review Checklist**:
   - Read relevant source files in `stock/`, `coin/`, `backtester/`, `ui/` modules
   - Review related documentation in `Manual/` and `Guideline/` directories
   - Check existing condition documents for compliance (98.3% target)
   - Verify database schema compatibility in `utility/setting.py`

2. **Data Mapping Verification**:
   - Check column name mappings between databases
   - Verify data type consistency (int, float, str)
   - Validate value range constraints
   - Test NULL/NaN handling
   - Confirm index alignment for time series data

3. **Architecture Consistency**:
   - **Multiprocess Pattern**: Verify queue-based communication (qlist 0-14)
   - **Naming Conventions**: `*_receiver_*.py`, `*_strategy_*.py`, `*_trader.py`
   - **Process Boundaries**: No mixing of receiver/strategy/trader concerns
   - **Korean Variable Names**: Preserve 현재가, 시가, 고가, 저가 naming
   - **Template Method Pattern**: Strategy classes inherit from Receiver base

4. **Quality Assessment Criteria** (0-10 scale):
   - **Functionality** (3 points): Correct implementation, no bugs
   - **Architecture** (2 points): Adherence to STOM patterns
   - **Code Quality** (2 points): Readability, maintainability
   - **Documentation** (2 points): Comments, docstrings, guideline compliance
   - **Testing** (1 point): Backtester validation, test coverage

5. **Code Review Template**:
   ```markdown
   ## Critical Issues (P0)
   ### Issue 1: [Title]
   **Location**: `file.py:line_number`
   **Problem**: [Description]
   **Impact**: [Consequences]
   **Fix**: [Specific solution]
   **Code**:
   ```python
   # Current (incorrect)
   # Proposed (correct)
   ```

   ## Quality Score: X/10
   - Functionality: X/3
   - Architecture: X/2
   - Code Quality: X/2
   - Documentation: X/2
   - Testing: X/1
   ```

### Review Focus Areas

1. **Data Integrity**:
   - Segment filter value ranges (0.0-1.0 normalization)
   - Database column mappings (93 stock columns, 42 coin columns)
   - Cross-timeframe compatibility (tick vs minute data)

2. **Performance**:
   - Query optimization (indexed lookups)
   - NumPy vectorization opportunities
   - Multiprocessing efficiency (15 queues, ZMQ communication)

3. **Trading Logic**:
   - LOOKAHEAD-FREE verification (no future data leakage)
   - Buy/Sell condition consistency
   - Risk management implementation
   - Position sizing correctness

4. **UI/UX**:
   - PyQt5 signal/slot connections
   - Thread safety for UI updates
   - Chart rendering performance (pyqtgraph)
   - Event handler correctness (`ui_button_clicked_*.py`)

### Integration with Other Studies

**With ConditionStudies/**:
- Verify condition implementations match documented strategies
- Check for overfitting risks identified in condition analysis
- Validate sample size requirements

**With SystemAnalysis/**:
- Reference optimization system improvements (15 proposals)
- Verify metric calculations (OPTISTD 14 methods)
- Check backtesting output system compatibility (93 columns)

**With Guides/**:
- Apply metric development process (10-step guide)
- Use segment filter integration checklist
- Follow optimization workflow best practices

### Quality Standards

- **Evidence-Based**: Support findings with code snippets and line references
- **Actionable**: Provide specific fix recommendations, not vague suggestions
- **Prioritized**: Use P0/P1/P2 classification for clear action items
- **Objective**: Use 0-10 quality scoring with transparent criteria
- **Reproducible**: Include test cases to verify bug fixes

### Review Lifecycle

1. **Pre-Merge Review**: Conduct comprehensive review before branch merge
2. **Bug Tracking**: Create GitHub issues for P0/P1 items
3. **Post-Merge Verification**: Validate fixes in main branch
4. **Follow-Up**: Schedule P2 items for future sprints
5. **Continuous Improvement**: Update review templates based on learnings

## Dependencies

### Code Analysis Tools
- **Static Analysis**: pylint, mypy for type checking
- **Performance Profiling**: cProfile, memory_profiler
- **Code Quality**: flake8, black for formatting
- **Git Tools**: gitpython for branch analysis
- **Diff Tools**: difflib for code comparison

### STOM Framework Knowledge
- **Architecture**: Multiprocess, queue-based (15 queues), ZMQ communication
- **Database**: SQLite schema (15 databases), query patterns
- **Trading Logic**: Tick/minute strategies, backtesting engines (12 engines)
- **UI Components**: PyQt5 patterns, signal/slot, threading

### Domain Expertise
- **Trading Systems**: Order execution, position management, risk control
- **Technical Analysis**: Indicator calculations, signal generation
- **Backtesting**: LOOKAHEAD-FREE, walk-forward validation
- **Korean Market**: Kiwoom API integration, market conventions

### Related Documentation
- **STOM Framework**: `utility/setting.py`, `utility/static.py`, `utility/query.py`
- **Guidelines**: `Back_Testing_Guideline_Tick.md` (826 variables)
- **Manual**: `02_Architecture/`, `03_Modules/`, `07_Trading/`
- **Conditions**: 133 condition files (98.3% compliance target)

---

**Last Updated**: 2026-01-19
**Total Documents**: 2 files
**Review Coverage**: Branch reviews, bug detection, architecture verification
**Quality Focus**: P0/P1/P2 classification, 0-10 scoring system
