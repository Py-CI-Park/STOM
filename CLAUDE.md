# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

STOM (System Trading Optimization Manager) V1 is a professional-grade high-frequency trading system for Korean stock markets (via Kiwoom Securities) and cryptocurrency markets (Upbit, Binance). It's a multi-process, real-time trading platform with comprehensive backtesting capabilities built with PyQt5.

**Project Statistics** (as of 2025-11-26):
- 157 Python source files (~70,000+ lines of code)
- 175+ markdown documentation files
- 133 trading condition files (98.3% documentation compliant)
- 15 SQLite databases for data separation
- Multi-process architecture with 15 inter-process queues

## Common Commands

### Installation & Setup
```bash
# Install dependencies (requires Python 64-bit)
pip_install_64.bat

# Database integrity check (run automatically on startup)
python64 ./utility/database_check.py
```

### Running the System
```bash
# Main application (requires admin privileges)
stom.bat

# Stock trading mode
stom_stock.bat

# Cryptocurrency trading mode
stom_coin.bat

# Direct Python execution
python64 stom.py [stock|coin]
```

### Development & Testing
```bash
# Run backtesting
python64 backtester/backtest.py

# Parameter optimization
python64 backtester/optimiz.py

# Database operations
python64 utility/db_update_day.py
python64 utility/db_update_back.py
```

## Architecture Overview

### Core Components

**Multi-Process Architecture:**
- **Main Process**: PyQt5 GUI (`ui/ui_mainwindow.py` - 1,083 lines)
- **Data Receivers**: Real-time market data collection (`*_receiver_*.py`)
- **Strategy Engines**: Trading signal generation (`*_strategy_*.py`)
- **Traders**: Order execution and management (`*_trader.py`)
- **Backtesting**: Historical analysis and optimization (`backtester/`)
- **Query Process**: Database operations via queue-based architecture
- **Manager Processes**: Kiwoom manager for ZMQ-based communication

**Key Modules:**
- `/stock/` - Korean stock market trading via Kiwoom API (9 files, ~7,800 lines)
- `/coin/` - Cryptocurrency trading Upbit, Binance (16 files, ~10,098 lines)
- `/backtester/` - Historical testing and optimization (23 files, ~12,993 lines)
- `/ui/` - PyQt5 user interface components (70+ files, ~20,625 lines)
- `/utility/` - Shared functionality and database management (24 files, ~3,419 lines)
- `/docs/` - Comprehensive documentation (175+ markdown files)
- `/lecture/` - Educational materials and performance tests

### Database Structure

SQLite databases in `/_database/`:
- `setting.db` - System configuration and encrypted credentials
- `stock_tick.db` / `coin_tick.db` - Real-time tick data
- `stock_min.db` / `coin_min.db` - Minute data
- `tradelist.db` - Trading history and performance
- `strategy.db` - Trading strategies and parameters
- `backtest.db` - Backtesting results
- `optuna.db` - Optimization results

### Configuration Management

All settings managed through `utility/setting.py`:
- Database paths and connections
- Trading parameters and risk controls
- API credentials (encrypted using Fernet)
- Market-specific configurations
- Blacklist management for stocks/coins

## Development Patterns

### File Naming Conventions
- `*_receiver_*.py` - Real-time data collection (WebSocket/ZMQ)
- `*_strategy_*.py` - Trading logic and signal generation
- `*_trader.py` - Order execution and position management
- `*_manager.py` - Process/resource orchestration
- `backengine_*_*.py` - Market-specific backtesting (market × timeframe)
- `ui_*.py` - Interface components and event handlers
- `ui_button_clicked_*.py` - Event handlers (cvj=coin volume journal, svj=stock volume journal)
- `ui_update_*.py` - Data display updates (table, text, progress)
- `ui_draw_*.py` - Chart rendering (candles, real-time, TreeMap)
- `set_*.py` - UI component setup and layout
- `_database/` - SQLite databases (excluded from git)
- `_log/` - Application logs (excluded from git)

### Key Classes & Patterns

**Design Patterns:**
- **Strategy Pattern**: Each market has dedicated strategy engines
- **Observer Pattern**: Real-time data updates via queues/WebSocket
- **Factory Pattern**: Market-specific engines (Kiwoom, Upbit, Binance)
- **Singleton Pattern**: Configuration and database managers
- **Template Method**: Strategy classes inherit from Receiver classes
- **Command Pattern**: Queue-based operations for all cross-process communication

**Class Hierarchies:**
- Stock modules inherit from Kiwoom base classes
- Coin modules inherit from Upbit/Binance base classes
- Tick strategies as base, Minute strategies as derived
- Strategy classes use Template Method pattern with hook methods

**Code Patterns:**
- Korean variable names extensively used (현재가, 시가, 고가, 저가, 등락율)
- Self-referential indexing: `self.vars[N]` for accessing N-th variable
- Dictionary lookups: `Parameter_Previous(index, lookback)` for historical data
- Tuple unpacking for data parameter passing
- Decorators: `@pyqtSlot`, `@thread_decorator`, `@error_decorator`

### Inter-Process Communication

**Queue-Based Architecture** (15 Queues):
```python
# Main queue list (qlist indices)
qlist = [
    windowQ,    # 0  - Main window events
    soundQ,     # 1  - Audio notifications
    queryQ,     # 2  - Database operations
    teleQ,      # 3  - Telegram alerts
    chartQ,     # 4  - Chart updates
    hogaQ,      # 5  - Orderbook (호가) data
    webcQ,      # 6  - Web communication
    backQ,      # 7  - Backtesting
    creceivQ,   # 8  - Coin receiver
    ctraderQ,   # 9  - Coin trader
    cstgQ,      # 10 - Coin strategy
    liveQ,      # 11 - Live trading data
    kimpQ,      # 12 - Kimchi premium (arbitrage)
    wdzservQ,   # 13 - WebSocket ZMQ server
    totalQ      # 14 - Total statistics
]
```

**Communication Methods:**
- Python multiprocessing queues for sequential operations
- ZeroMQ (ZMQ) for high-performance real-time data streaming
- WebSocket connections for exchange APIs (Upbit, Binance)
- SQLite for persistent storage and cross-process data sharing
- Threading for UI updates and non-blocking operations

## Important Technical Details

### Market-Specific Requirements
- **Kiwoom Stock**: Requires Windows, Kiwoom OpenAPI installation at `C:/OpenAPI`
- **Cryptocurrency**: REST API + WebSocket connections
- **Real-time Data**: Tick-level processing for ultra-high-frequency trading

### Performance Considerations
- Uses numpy/pandas for high-performance data processing
- TA-Lib for technical analysis (custom wheel in `/utility/`)
- pyqtgraph for real-time chart rendering
- Optimized database queries with indexed tables

### Security Features
- Encrypted credential storage using cryptography.fernet
- API key management through `utility/static.py`
- Blacklist management for risk control
- Position sizing and risk management built-in

### Dependencies
Critical dependencies (see `pip_install_64.bat`):
- PyQt5 ecosystem (GUI, WebEngine, pyqtgraph)
- Trading APIs (pyupbit, python-binance)
- Data processing (numpy==1.26.4, pandas==2.0.3)
- Technical analysis (TA-Lib custom wheel)
- Optimization (optuna, cmaes)
- Communication (websockets, pyzmq)

## Documentation Structure

### Documentation Architecture (`/docs/`)

**Manual/** - Comprehensive system analysis (16 files):
- `01_Overview/` - Project scope & tech stack
- `02_Architecture/` - System design & component interactions
- `03_Modules/` - Detailed analysis (stock, coin, ui, utility, backtester)
- `04_API/` - Integration patterns
- `05_UI_UX/` - Interface analysis
- `06_Data/` - Database structure & management
- `07_Trading/` - Execution engine
- `08_Backtesting/` - Testing & optimization
- `09_Manual/` - User guide
- `10_Conclusion/` - Summary & references
- `DOCUMENTATION_GUIDE.md` - Validation procedures

**Guideline/** - Development standards:
- `Back_Testing_Guideline_Tick.md` (33KB, 826 documented variables)
- `Back_Testing_Guideline_Min.md` (25KB, 752 documented variables)
- `Condition_Document_Template_Guideline.md` - Template for trading conditions
- `Stock_Database_Information.md` (108/93 columns documented)
- `Manual_Generation_Guideline.md` - Manual creation process
- `사용설명서/` - User manual (Korean, 8 files)

**Condition/** - Trading conditions (133 files, 98.3% compliant):
- `Tick/` - 72 condition files (초단위 strategies)
- `Min/` - 61 condition files (분봉 strategies)
- `Idea/` - Strategy ideas from AI assistants
- `Reference/` - PyTrader, YouTube references

**CodeReview/** - Technical analysis:
- `Backtesting_Data_Loading_Multicore_Analysis.md`

### Trading Condition Document Pattern

Each condition file follows this structure:
- **BO (Buy Optimization)** - Optimized buy conditions with actual values
- **BOR (Buy Optimization Range)** - Variable ranges for grid search `[min, max, step]`
- **SO (Sell Optimization)** - Optimized sell conditions
- **SOR (Sell Optimization Range)** - Sell parameter ranges
- **OR (Overall Range)** - Top 10 key variables only
- **GAR (Genetic Algorithm Range)** - `[min, max]` format for genetic algorithms

### Documentation Validation

**Recent Validation (2025-11-26)**:
- 119/121 condition files (98.3%) comply with documentation guidelines
- Automated optimization section generation implemented
- Code-documentation traceability established
- Path corrections: `STOM_V1/` → `STOM/`
- Command updates: `python main.py` → `python64 stom.py`

**Validation Process**:
1. Automated checks via `DOCUMENTATION_GUIDE.md`
2. Self-check procedures for condition files
3. Code snippet references linked to source files
4. Manual review for complex sections

## Common Development Tasks

### Adding New Trading Strategies
1. Create strategy file in appropriate market directory (`stock/` or `coin/`)
2. Follow naming pattern: `{market}_strategy_{timeframe}.py`
3. Implement strategy logic using existing technical indicators
4. Create condition document in `/docs/Condition/Tick/` or `/docs/Condition/Min/`
5. Follow condition document template (BO, BOR, SO, SOR, OR, GAR sections)
6. Add strategy to database via UI or direct SQL insertion
7. Test with backtesting engine before live deployment
8. Ensure 98.3% documentation guideline compliance

### Database Schema Changes
1. Modify `utility/setting.py` for new database paths
2. Update `utility/query.py` for new queries
3. Run `utility/database_check.py` to verify integrity
4. Consider migration scripts for existing data

### UI Modifications
1. Layout changes in `ui/set_*.py` files
2. Event handlers in `ui/ui_*.py` files
3. Styling updates in `ui/set_style.py`
4. Chart modifications in `ui/ui_draw_*.py`

### Performance Optimization
1. Profile using `utility/total_code_line.py` and timing tests
2. Optimize database queries in `utility/query.py`
3. Consider numpy vectorization for calculations
4. Use multiprocessing for CPU-intensive tasks
5. Reference performance benchmarks in `/lecture/testcode/`:
   - `numpyint_vs_pureint.py` - NumPy vs Python integers
   - `pandas.at_vs_list.apd_to_df.py` - Data access methods
   - `dict_insert_vs_update.py` - Dictionary operations
   - `pickle_speed.py` - Serialization performance

### Testing and Quality Assurance

**Testing Infrastructure**:
- Educational test code in `/lecture/testcode/`
- Performance comparison tests for optimization decisions
- ZMQ communication tests (`zmq_pub.py`, `zmq_sub1/2/3.py`)
- Pattern recognition tests (`test_candle_pattern.py`)
- Fee calculation tests (`test_withdrawfee.py`)

**Quality Checks**:
- `database_check.py` - Runs automatically on startup
- Data integrity validation on application launch
- Documentation compliance tracking (98.3% current rate)
- Code-documentation alignment validation

**Backtester Validation**:
- `back_code_test.py` - Condition code validation
- `backfinder.py` - Strategy discovery and testing

## Troubleshooting

### Common Issues
- **Admin privileges required**: All batch files request elevation
- **Database locks**: Check for concurrent access in multi-process operations
- **API connection failures**: Verify credentials in encrypted storage
- **Memory usage**: Monitor with `psutil` integration for large datasets

### Debugging
- Log files automatically generated by system
- Telegram integration for real-time alerts
- Database integrity checks on startup
- Built-in performance monitoring via UI

### Development Environment
- Requires Windows for Kiwoom API integration
- Python 64-bit required for memory management
- Admin privileges needed for system operations
- Multiple monitors recommended for trading interface

## Process Flow and Execution Model

### Multi-Process Execution Architecture

```
Main Process (PyQt5 GUI)
├─→ Kiwoom Manager Process (stock/kiwoom_manager.py)
│   ├─→ Receiver Tick Process (WebSocket/ZMQ streaming)
│   ├─→ Receiver Min Process (Minute data aggregation)
│   ├─→ Strategy Engine Process (Signal generation)
│   └─→ Trader Process (Order execution & management)
│
├─→ Coin Receiver Process
│   ├─→ Upbit WebSocket (Real-time tick data)
│   ├─→ Binance WebSocket (Real-time tick data)
│   ├─→ Strategy Engine (Combined or separate)
│   └─→ Trader Process (Multi-exchange orders)
│
├─→ Query Process (Database operations via queryQ)
├─→ Backtester Processes (Parallelized optimization)
├─→ Kimp Process (Kimchi premium arbitrage monitoring)
└─→ Chart Update Thread (UI rendering)
```

### Data Flow Patterns

**Real-time Trading Flow**:
1. Exchange → WebSocket/API → Receiver Process
2. Receiver → Queue → Strategy Engine
3. Strategy → Signal → Trader Process
4. Trader → Order → Exchange API
5. Result → Database (via queryQ) → UI Update

**Backtesting Flow**:
1. Historical Data (Database) → BackEngine
2. BackEngine → Strategy Logic → Trading Signals
3. Signals → Simulated Orders → P&L Calculation
4. Results → Database → Optimization Engine
5. Optimization → Parameter Tuning → Repeat

**UI Update Flow**:
1. Process → Queue (windowQ/chartQ/hogaQ) → Main Process
2. Main Process → UI Thread → Display Update
3. User Action → Button Event → Process Queue → Worker Process

## Critical Files Reference

### Entry Points
- `stom.py` - Main application entry point (mode selection)
- `stom.bat` / `stom_stock.bat` / `stom_coin.bat` - Launcher scripts

### Core Configuration
- `utility/setting.py` (42KB) - Global configuration, 15 database paths, encrypted credentials
- `utility/static.py` (16KB) - Helper functions (threading, encryption, datetime, UI)
- `utility/query.py` (24KB) - Queue-based database operations

### Process Managers
- `stock/kiwoom_manager.py` - Stock trading process orchestration
- `ui/ui_mainwindow.py` (1,083 lines) - Main GUI and process coordination

### Trading Engines
- `stock/kiwoom_strategy_tick.py` (42KB) - Stock tick strategy
- `coin/upbit_strategy_min.py` / `coin/binance_strategy_min.py` - Crypto strategies
- `stock/kiwoom_trader.py` (46KB) - Order execution and position management

### Backtesting
- `backtester/backtest.py` - Backtesting orchestrator
- `backtester/backengine_*_*.py` (12 files) - Market-specific engines
- `backtester/optimiz.py` - Grid search optimization
- `backtester/optimiz_genetic_algorithm.py` - Genetic algorithm optimization

## Important Conventions for AI Assistants

### When Modifying Code

1. **Always read files before editing** - Never propose changes to unread code
2. **Preserve Korean variable names** - Don't translate 현재가, 시가, 고가, 저가, etc.
3. **Maintain queue architecture** - All cross-process communication via queues
4. **Follow naming conventions** - Respect `*_receiver_*.py`, `*_strategy_*.py` patterns
5. **Update documentation** - Any code change requires corresponding doc update
6. **Test with backtester** - Validate strategy changes before live deployment
7. **Check database schema** - Coordinate changes across multiple databases
8. **Maintain compliance** - Keep condition documents at 98.3%+ compliance rate

### When Adding Features

1. **Use existing patterns** - Follow Template Method, Strategy, Observer patterns
2. **Respect process boundaries** - Don't mix concerns across process types
3. **Add to appropriate module** - Stock/Coin/UI/Utility/Backtester separation
4. **Document thoroughly** - Create condition docs for new strategies
5. **Consider performance** - Reference `/lecture/testcode/` benchmarks
6. **Update queue list** - Add new queues to qlist if needed
7. **Encrypt sensitive data** - Use Fernet encryption for credentials

### When Debugging

1. **Check logs** - `/_log/` contains process-specific logs
2. **Verify database** - Run `utility/database_check.py`
3. **Test queue communication** - Verify queue flow across processes
4. **Validate condition code** - Use `back_code_test.py`
5. **Check documentation alignment** - Ensure code matches docs (98.3% target)

## Recent Project State (2025-11-26)

**Completed Initiatives**:
- Phase 5: 119/121 condition files (98.3%) now documentation compliant
- Automated optimization section generation for trading conditions
- Manual document code-reference validation (7 files, 138 code blocks)
- Path and command corrections throughout documentation

**Current Focus**:
- Maintaining documentation-code alignment
- Continuous strategy optimization
- Performance benchmarking and improvements

**Technical Debt**:
- Limited formal unit testing (educational tests exist)
- Some legacy code patterns in older modules
- Documentation still being brought to 100% compliance (2 files remaining)