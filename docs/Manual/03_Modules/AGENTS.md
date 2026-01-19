<!-- Parent: ../AGENTS.md -->
# Module Analysis Documentation

## Purpose

In-depth technical analysis of all five major STOM modules, providing comprehensive documentation of implementation details, class hierarchies, code patterns, and module interactions. This section serves as the detailed reference for understanding each module's internal structure and functionality.

## Key Files

- **modules_analysis.md** - Central hub document linking to all five module analyses
- **stock_module.md** - Korean stock trading via Kiwoom API (9 files, ~7,800 lines)
  - Receiver, Strategy, Trader processes
  - Kiwoom OpenAPI integration patterns
  - ZMQ-based manager architecture
- **coin_module.md** - Cryptocurrency trading for Upbit and Binance (16 files, ~10,098 lines)
  - WebSocket real-time data streaming
  - Multi-exchange REST API integration
  - Unified strategy engine architecture
- **ui_module.md** - PyQt5 interface components (70+ files, ~20,625 lines)
  - Main window structure (ui_mainwindow.py - 1,083 lines)
  - Event handlers (ui_button_clicked_*.py pattern)
  - Data display updates (ui_update_*.py pattern)
  - Chart rendering (ui_draw_*.py - candlesticks, real-time, TreeMap)
- **utility_module.md** - Shared utilities and database management (24 files, ~3,419 lines)
  - Setting management (setting.py - global configuration)
  - Database query process (query.py - queue-based operations)
  - Static helpers (static.py - threading, encryption, datetime, UI)
- **backtester_module.md** - Backtesting engines and optimization (23 files, ~12,993 lines)
  - 12 market-specific engines (backengine_*_*.py)
  - Grid search optimization (optimiz.py)
  - Genetic algorithm optimization (optimiz_genetic_algorithm.py)

## For AI Agents

### Maintaining This Section

**When to Update:**
- New files added to any module directory
- Class hierarchies or inheritance patterns change
- File naming patterns evolve
- Module responsibilities shift
- Code statistics change significantly (±5% file count or line count)
- New design patterns implemented within modules

**Critical Validation Points:**

1. **File and Line Counts** - Must match actual codebase:
   ```bash
   # Stock module
   find stock/ -name "*.py" | wc -l  # Should be 9 files
   wc -l stock/*.py | tail -1        # Should be ~7,800 lines

   # Coin module
   find coin/ -name "*.py" | wc -l   # Should be 16 files
   wc -l coin/*.py | tail -1         # Should be ~10,098 lines

   # UI module
   find ui/ -name "*.py" | wc -l     # Should be 70+ files
   wc -l ui/*.py | tail -1           # Should be ~20,625 lines

   # Utility module
   find utility/ -name "*.py" | wc -l # Should be 24 files
   wc -l utility/*.py | tail -1       # Should be ~3,419 lines

   # Backtester module
   find backtester/ -name "*.py" | wc -l # Should be 23 files
   wc -l backtester/*.py | tail -1       # Should be ~12,993 lines
   ```

2. **Naming Pattern Compliance** - Verify file naming conventions:
   - `*_receiver_*.py` - Real-time data collection
   - `*_strategy_*.py` - Trading logic and signal generation
   - `*_trader.py` - Order execution and position management
   - `*_manager.py` - Process/resource coordination
   - `backengine_*_*.py` - Market-specific backtesting (market × timeframe)
   - `ui_*.py` - Interface components and event handlers
   - `ui_button_clicked_*.py` - Event handlers
   - `ui_update_*.py` - Data display updates
   - `ui_draw_*.py` - Chart rendering

3. **Class Hierarchy Accuracy** - Confirm inheritance patterns exist in code:
   - Stock module inherits from Kiwoom base classes
   - Coin module inherits from Upbit/Binance base classes
   - Tick strategies are base, Minute strategies derive
   - Strategy classes use Template Method pattern with hook methods

**Update Guidelines:**
1. **Read Before Editing** - Always read target module documentation completely
2. **Cross-Reference Source** - Verify all claims against actual module code
3. **Update Statistics** - Recalculate file/line counts when documenting changes
4. **Preserve Korean Terms** - Keep variable names like 현재가, 시가, 고가, 저가
5. **Check Cross-Module Impact** - Module changes may affect architecture docs

### Code-Documentation Alignment

**Key Source References by Module:**

**Stock Module:**
```python
stock/kiwoom_manager.py - Process orchestration
stock/kiwoom_receiver_tick.py - Tick data collection
stock/kiwoom_receiver_min.py - Minute data aggregation
stock/kiwoom_strategy_tick.py - Tick trading strategy (42KB)
stock/kiwoom_strategy_min.py - Minute trading strategy
stock/kiwoom_trader.py - Order execution (46KB)
```

**Coin Module:**
```python
coin/upbit_receiver_tick.py - Upbit WebSocket streaming
coin/binance_receiver_tick.py - Binance WebSocket streaming
coin/upbit_strategy_tick.py - Upbit tick strategy
coin/upbit_strategy_min.py - Upbit minute strategy
coin/binance_strategy_tick.py - Binance tick strategy
coin/binance_strategy_min.py - Binance minute strategy
coin/upbit_trader.py - Upbit order execution
coin/binance_trader.py - Binance order execution
```

**UI Module:**
```python
ui/ui_mainwindow.py - Main window (1,083 lines)
ui/set_*.py - Layout configuration
ui/ui_button_clicked_*.py - Event handlers
ui/ui_update_*.py - Display updates
ui/ui_draw_*.py - Chart rendering
ui/set_style.py - Styling and themes
```

**Utility Module:**
```python
utility/setting.py - Global configuration (42KB)
utility/static.py - Helper functions (16KB)
utility/query.py - Database operations (24KB)
utility/database_check.py - Integrity verification
```

**Backtester Module:**
```python
backtester/backtest.py - Orchestrator
backtester/backengine_stock_tick.py - Stock tick backtesting
backtester/backengine_stock_min.py - Stock minute backtesting
backtester/backengine_coin_tick.py - Crypto tick backtesting
backtester/backengine_coin_min.py - Crypto minute backtesting
backtester/optimiz.py - Grid search
backtester/optimiz_genetic_algorithm.py - GA optimization
```

**Validation Checklist (Per Module):**
- [ ] File count matches actual directory
- [ ] Line count within ±5% of actual
- [ ] File naming patterns documented accurately
- [ ] Class names and inheritance verified
- [ ] Code examples reference actual implementations
- [ ] Korean variable names preserved
- [ ] Cross-references to other modules valid

### Content Structure

**Standard Sections in Each Module Document:**
1. **Module Overview** - Purpose and responsibilities
2. **File Structure** - Complete file listing with purposes
3. **Class Hierarchy** - Inheritance patterns and relationships
4. **Key Classes and Methods** - Core functionality documentation
5. **Code Patterns** - Module-specific design patterns
6. **Data Flow** - How data moves through module
7. **Inter-Module Communication** - Queue usage, shared data
8. **Configuration** - Module-specific settings
9. **Testing and Validation** - Quality assurance approaches

**Module-Specific Considerations:**

**Stock Module:**
- Windows-only Kiwoom API requirements
- ZMQ-based manager pattern
- Korean market specifics (시가, 고가, 저가, 현재가)

**Coin Module:**
- WebSocket connection management
- Multi-exchange architecture
- REST API + WebSocket hybrid approach

**UI Module:**
- PyQt5 event loop integration
- Threading for non-blocking operations
- Signal/slot communication patterns

**Utility Module:**
- Singleton pattern for settings
- Queue-based database access
- Fernet encryption for credentials

**Backtester Module:**
- Multicore parallelization
- Strategy parameter optimization
- Performance metric calculations

### Common Updates

**Adding New File to Module:**
1. Update file count in module documentation
2. Recalculate total line count
3. Add file description to file structure section
4. Document file's role in module data flow
5. Update class hierarchy if new classes introduced
6. Note naming pattern compliance

**Modifying Class Hierarchy:**
1. Read both old documentation and current code
2. Update inheritance diagrams
3. Document new base classes or interfaces
4. Update affected module documentation
5. Check for Template Method pattern changes
6. Verify Strategy pattern implementations

**Refactoring Module Organization:**
1. Document file moves or renames
2. Update all file path references
3. Recalculate statistics
4. Update inter-module communication descriptions
5. Check cross-references in other manual sections
6. Update architecture documentation if significant

## Dependencies

**Related Manual Sections:**
- `02_Architecture/` - Process architecture context for modules
- `04_API/` - External API integrations used by stock/coin modules
- `05_UI_UX/` - Detailed UI module analysis
- `06_Data/` - Database interactions from utility module
- `07_Trading/` - Trading logic in stock/coin/backtester modules
- `08_Backtesting/` - Backtester module implementation details

**Source Code References:**
- `stock/` - Stock module source files (9 files)
- `coin/` - Cryptocurrency module source files (16 files)
- `ui/` - User interface source files (70+ files)
- `utility/` - Utility module source files (24 files)
- `backtester/` - Backtesting module source files (23 files)

**Documentation Network:**
- Parent: `../AGENTS.md` - Manual documentation standards
- Overview: `../01_Overview/project_overview.md` - Module summary
- Architecture: `../02_Architecture/system_architecture.md` - Module interactions
- Learning: `../../learning/03-모듈-구조.md` - User-facing module guide (Korean)

**Cross-References:**
- Each module doc references relevant condition documentation in `../../Condition/`
- Backtester module docs reference guidelines in `../../Guideline/Back_Testing_Guideline_*.md`
- Utility module docs reference database info in `../../Guideline/Stock_Database_Information.md`

## Special Considerations

### Code Statistics Maintenance
- Update file/line counts during significant changes
- Use `utility/total_code_line.py` for accurate counts
- Document statistics verification date
- Note discrepancies and investigate causes

### Korean Variable Names
**CRITICAL:** Never translate Korean variable names:
- 현재가 (current price)
- 시가 (open price)
- 고가 (high price)
- 저가 (low price)
- 등락율 (rate of change)

These are intentional and widely used throughout codebase.

### Module Independence
Document module coupling:
- Which queues module uses
- Which other modules it depends on
- Shared data structures
- Configuration dependencies

### Template Method Pattern
Strategy classes use Template Method extensively:
- Base class defines algorithm structure
- Subclasses implement hook methods
- Document which methods are abstract vs. concrete
- Show inheritance hierarchy clearly

### Performance Characteristics
Document performance-critical aspects:
- Real-time processing requirements
- Multicore utilization
- Memory management
- Database query optimization

### Testing Approaches
Each module has different testing needs:
- Stock: Integration tests with Kiwoom API
- Coin: WebSocket connection tests
- UI: Manual testing and visual verification
- Utility: Unit tests for helpers
- Backtester: Performance validation tests

Reference test code in `/lecture/testcode/` where applicable.

### Module Evolution
Track module changes over time:
- File additions/removals
- Refactoring initiatives
- Performance optimizations
- Design pattern introductions
- Maintain changelog in module documentation

### Cross-Module Coordination
When updating module documentation:
1. Check if changes affect architecture docs
2. Update inter-module communication descriptions
3. Verify queue usage documentation
4. Update data flow diagrams
5. Check API integration docs
6. Coordinate with learning guides

Module documentation is the most detailed level and must maintain highest accuracy.
