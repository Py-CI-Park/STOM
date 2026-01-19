<!-- Parent: ../AGENTS.md -->
# Utility Module

## Purpose

Shared functionality and database management layer for STOM V1. This module provides cross-cutting concerns including database operations, settings management, cryptography, helper utilities, and system monitoring. Acts as the foundational infrastructure supporting stock, coin, backtester, and UI modules.

**Module Statistics** (per CLAUDE.md):
- 24 Python files (~3,419 lines total)
- 15 SQLite database management paths
- Queue-based database operations (queryQ)
- Cryptography and API key management (Fernet encryption)
- Performance benchmarking utilities

## Key Files

### Core Infrastructure

**`setting.py`** (42KB, ~1,100 lines)
- Global configuration management for entire system
- 15 database path definitions (DB_SETTING, DB_TRADELIST, DB_STRATEGY, etc.)
- Encrypted credentials storage and retrieval using Fernet
- Market-specific settings (stock/coin parameters)
- Blacklist management (blacklist_stock.txt, blacklist_coin.txt)
- Virtual environment detection (venv_64bit/venv_32bit)
- Configuration dictionaries (DICT_SET) loaded at startup
- Python path selection (PYTHON_32BIT/PYTHON_64BIT)
- Critical paths (OPENAPI_PATH, ICON_PATH, LOGIN_PATH, GRAPH_PATH)

**`static.py`** (16KB, ~400 lines)
- Helper functions used across all modules
- Threading utilities: `thread_decorator`, `threading_timer`, `error_decorator`
- Cryptography: `read_key()`, `en_text()`, `de_text()` (Fernet encryption/decryption)
- Datetime utilities: `now()`, `now_utc()`, `int_hms()`, `strf_time()`
- Process management: `win_proc_alive()`, `opstarter_kill()`
- Serialization: `pickle_write()`, `pickle_read()`, `array_to_bytes()`, `bytes_to_array()`
- UI utilities: `qtest_qwait()`
- Pattern decorators for error handling and async execution

**`query.py`** (24KB, ~600 lines)
- Queue-based database operations (queryQ from qlist[2])
- Three persistent database connections:
  - `con1/cur1`: DB_SETTING (configuration)
  - `con2/cur2`: DB_TRADELIST (trading history)
  - `con3/cur3`: DB_STRATEGY (trading strategies)
- Query types supported:
  - `'설정변경'`: Update settings dictionary
  - `'설정파일변경'`: Replace setting.db file
  - `'설정디비'`: Execute SQL on setting.db
  - `'거래디비'`: Execute SQL on tradelist.db
  - `'전략디비'`: Execute SQL on strategy.db
  - `'백테디비'`: Execute SQL on backtest.db
  - `'백테DB지정일자삭제'`: Delete backtest data by date
- Supports both raw SQL execution and DataFrame operations
- Error handling with windowQ notifications (ui_num['S로그텍스트'])
- Runs in dedicated process for database isolation

### Database Management

**`database_check.py`** (~20KB, ~500 lines)
- Automatic database integrity verification at startup
- Validates all 15 database file existence and schema
- Table structure verification
- Index validation and optimization recommendations
- Data consistency checks
- Automatic repair suggestions for corrupted databases
- Reports issues to main window via windowQ

**`db_update_day.py`** (~1.8KB)
- Daily market data updates for stock/coin databases
- Updates tick and minute databases with latest trading data
- Scheduled execution integration
- Supports both stock_tick/coin_tick and stock_min/coin_min databases

**`db_update_back.py`** (~1.2KB)
- Historical data updates for backtesting databases
- Populates stock_tick_back, stock_min_back, coin_tick_back, coin_min_back
- Batch data processing for large historical datasets
- Used for initial database seeding and gap filling

**`db_distinct.py`** (~1.7KB)
- Removes duplicate records from databases
- Deduplication utilities for tick and minute data
- Optimizes database storage and query performance

### User Interface Utilities

**`chart.py`** (26KB)
- Real-time chart rendering using pyqtgraph
- Candlestick chart generation
- Technical indicator overlays
- Volume bar rendering
- Chart update coordination via chartQ (qlist[4])
- Multiple timeframe support (tick/minute)
- Zoom and pan functionality

**`chart_items.py`** (~6.7KB)
- Custom pyqtgraph items for financial charts
- Candlestick bar items
- Volume histogram items
- Technical indicator line items
- Chart annotation utilities

**`hoga.py`** (~7.5KB)
- Order book (호가) data processing
- Bid/ask price level management
- Order depth calculation
- Market depth visualization data preparation
- Real-time updates via hogaQ (qlist[5])

**`sound.py`** (~744 bytes)
- Audio notification system
- Trading alert sounds
- Event notification audio playback
- Operates via soundQ (qlist[1])

### Communication & Monitoring

**`telegram_msg.py`** (13.8KB)
- Telegram bot integration for remote notifications
- Trading alerts and system status messages
- Position updates and P&L notifications
- Error alerts and critical system events
- Operates via teleQ (qlist[3])

**`webcrawling.py`** (~12KB)
- Web scraping utilities for market data
- News and sentiment data collection
- External data source integration
- Price data validation from multiple sources

**`timesync.py`** (~1.2KB)
- System time synchronization
- Market time coordination (KST/UTC)
- Trading session timing utilities

### Development Tools

**`total_code_line.py`** (~1.5KB)
- Code statistics and line counting
- Project size metrics
- Development progress tracking
- Used for documentation maintenance (see CLAUDE.md stats)

**`syntax.py`** (~4.3KB)
- Syntax validation utilities
- Code pattern verification
- Strategy condition syntax checking
- Used in backtesting condition validation

**`mpl_setup.py`** (~946 bytes)
- Matplotlib configuration for Korean font support
- Chart styling presets
- Font path configuration for Windows environment

### External Dependencies

**TA-Lib Wheels** (custom compiled)
- `TA_Lib-0.4.25-cp311-cp311-win_amd64.whl` (498KB) - 64-bit technical analysis library
- `TA_Lib-0.4.27-cp311-cp311-win32.whl` (357KB) - 32-bit technical analysis library
- Custom-compiled for Python 3.11 on Windows
- Provides 150+ technical indicators for strategy development

### Configuration Files

**`blacklist_stock.txt`**
- List of stock codes excluded from trading
- Risk management blacklist
- Updated manually based on trading experience

**`blacklist_coin.txt`**
- List of cryptocurrency symbols excluded from trading
- Scam token prevention
- Low liquidity coin filtering

## Subdirectories

None. All utility files are flat in `/utility/` directory.

## For AI Agents

### Critical Rules

1. **Database Safety**
   - NEVER modify database files directly - always use query.py via queryQ
   - ALL database operations must go through Query class to prevent corruption
   - NEVER open database connections outside Query process (causes locking)
   - Test database operations in backtester before production use

2. **Settings Management**
   - NEVER modify setting.py's DICT_SET directly at runtime
   - Use `queryQ.put(('설정변경', new_dict))` to update settings
   - ALWAYS validate settings before applying changes
   - Encrypt sensitive credentials using static.py's `en_text()` function

3. **Cryptography**
   - API keys MUST be encrypted using Fernet before storing
   - NEVER commit unencrypted credentials to git
   - Use `read_key()` from static.py to retrieve encryption key
   - Key file location: managed by setting.py (EN_KEY)

4. **Threading & Multiprocessing**
   - Use `@thread_decorator` for non-blocking UI operations
   - Use `@error_decorator` for robust error handling
   - Respect queue-based communication (15 queues in qlist)
   - NEVER share database connections across processes

5. **Korean Variable Names**
   - Preserve Korean variable names in setting.py (현재가, 시가, 고가, 저가)
   - Do NOT translate to English - breaks system-wide references
   - Follow existing naming conventions in DICT_SET

### Common Patterns

**Database Query Pattern**:
```python
# Execute SQL via queryQ (from any process)
queryQ.put(('설정디비', "UPDATE main SET value=1 WHERE index='key'"))

# Write DataFrame to database
queryQ.put(('거래디비', dataframe, 'table_name', 'replace'))

# Read from database (direct connection OK for read-only)
con = sqlite3.connect(DB_SETTING)
df = pd.read_sql('SELECT * FROM main', con)
con.close()
```

**Settings Access Pattern**:
```python
# Import from setting.py
from utility.setting import DICT_SET, DB_SETTING, ui_num

# Access configuration
leverage = DICT_SET['코인레버리지']
exchange = DICT_SET['거래소']

# Update settings at runtime
new_dict = DICT_SET.copy()
new_dict['코인레버리지'] = 5
queryQ.put(('설정변경', new_dict))
```

**Encryption Pattern**:
```python
from utility.static import en_text, de_text, read_key

# Encrypt sensitive data
key = read_key()
encrypted = en_text(key, "my_api_key")

# Decrypt when needed
decrypted = de_text(key, encrypted)
```

**Threading Pattern**:
```python
from utility.static import thread_decorator, error_decorator

@thread_decorator
@error_decorator
def background_task():
    # This runs in separate thread with error handling
    pass

background_task()  # Non-blocking
```

### Database Schema Knowledge

**15 Database Files** (defined in setting.py):
1. `setting.db` - System configuration (12 tables: main, stock, coin, sacc, cacc, telegram, etc.)
2. `tradelist.db` - Trading history and performance metrics
3. `strategy.db` - Trading strategies and parameters
4. `backtest.db` - Backtesting results
5. `stock_tick.db` - Real-time stock tick data
6. `stock_min.db` - Stock minute bar data
7. `stock_tick_back.db` - Historical stock tick data (backtesting)
8. `stock_min_back.db` - Historical stock minute data (backtesting)
9. `coin_tick.db` - Real-time cryptocurrency tick data
10. `coin_min.db` - Cryptocurrency minute bar data
11. `coin_tick_back.db` - Historical crypto tick data (backtesting)
12. `coin_min_back.db` - Historical crypto minute data (backtesting)
13. `optuna.db` - Optimization results (Optuna framework)
14. `setting.db` - User preferences and system state
15. Additional market-specific databases as needed

### Queue Communication Reference

**15 Queues** (qlist indices):
```python
windowQ   = qlist[0]   # Main window events
soundQ    = qlist[1]   # Audio notifications
queryQ    = qlist[2]   # Database operations (Query class)
teleQ     = qlist[3]   # Telegram messages
chartQ    = qlist[4]   # Chart updates
hogaQ     = qlist[5]   # Order book data
webcQ     = qlist[6]   # Web communication
backQ     = qlist[7]   # Backtesting
creceivQ  = qlist[8]   # Coin receiver
ctraderQ  = qlist[9]   # Coin trader
cstgQ     = qlist[10]  # Coin strategy
liveQ     = qlist[11]  # Live trading data
kimpQ     = qlist[12]  # Kimchi premium (arbitrage)
wdzservQ  = qlist[13]  # WebSocket ZMQ server
totalQ    = qlist[14]  # Total statistics
```

### Performance Considerations

1. **Database Optimization**
   - Use indexed queries for large tables
   - Batch INSERT/UPDATE operations with DataFrame.to_sql()
   - Close connections immediately after read-only queries
   - Let Query process handle all writes (prevents locking)

2. **Memory Management**
   - Use numpy arrays for large datasets (`array_to_bytes`/`bytes_to_array`)
   - Prefer pickle serialization for complex objects
   - Monitor memory with psutil integration (via static.py)
   - Clear large DataFrames after processing

3. **Threading Best Practices**
   - UI updates MUST be on main thread (use windowQ.put)
   - Database queries MUST go through queryQ (separate process)
   - Use threading for I/O operations (file, network)
   - Use multiprocessing for CPU-intensive tasks

### Testing & Validation

**Before Deployment**:
1. Run `python utility/database_check.py` to verify database integrity
2. Test settings changes in isolation before system-wide deployment
3. Verify encryption/decryption roundtrip for new credentials
4. Check queue communication with small test messages
5. Validate Korean character handling in database and UI

**Common Issues**:
- Database locked → Another process has connection open, use queryQ instead
- Encryption fails → Check EN_KEY exists and is valid Fernet key
- Queue full → Consumer process crashed, restart system
- Korean encoding errors → Use UTF-8 encoding for all file operations

## Dependencies

### Core Python Libraries
- `sqlite3` - Database operations (built-in)
- `pandas` - DataFrame operations and database I/O
- `numpy` - Array operations and serialization
- `multiprocessing` - Process isolation for database and trading

### Cryptography & Security
- `cryptography.fernet` - Symmetric encryption for credentials
- `fernet` - API key encryption/decryption

### GUI & Visualization
- `PyQt5` - UI utilities (QTest for timing)
- `pyqtgraph` - Real-time chart rendering

### System Integration
- `psutil` - Process monitoring and system resource tracking
- `winreg` - Windows registry access (for paths)
- `os`, `sys`, `shutil` - File system operations

### External Libraries
- `TA-Lib` - Technical analysis (custom wheels provided)
- `pickle` - Object serialization for performance

### Development Tools
- `traceback` - Error logging and debugging
- `datetime` - Time handling and synchronization

## Module Integration

### Upstream Dependencies (Used By)
- `stock/` - Settings, database queries, static helpers
- `coin/` - Settings, database queries, static helpers
- `backtester/` - Database operations, chart rendering
- `ui/` - Chart utilities, hoga rendering, sound notifications
- `stom.py` - Initial settings load and database validation

### Downstream Dependencies (Uses)
- None (utility is foundational layer)

### Cross-Module Communication
- All modules access settings via `from utility.setting import DICT_SET`
- All database writes go through `query.py` via queryQ
- All modules use `static.py` for threading, encryption, datetime
- UI modules use `chart.py`, `chart_items.py`, `hoga.py` for visualization

## Development Guidelines

1. **Adding New Settings**
   - Add to appropriate table in setting.db (main/stock/coin/etc)
   - Update `database_load()` in setting.py to include new setting
   - Document setting purpose and valid value ranges
   - Update CLAUDE.md if adding new configuration category

2. **Adding New Database Queries**
   - Add query type to Query.Start() in query.py
   - Document query format and parameters
   - Add error handling with windowQ notification
   - Test with both SQL and DataFrame operations

3. **Adding New Utilities**
   - Place in static.py if used by 3+ modules
   - Create separate file if >200 lines or domain-specific
   - Use Korean comments for business logic
   - Add docstrings for public functions
   - Export in __init__.py if needed by other modules

4. **Modifying Cryptography**
   - NEVER change encryption algorithm without migration plan
   - Test encryption/decryption roundtrip thoroughly
   - Provide backward compatibility for existing encrypted data
   - Document key rotation procedures

## Security Notes

⚠️ **WARNING**: This module handles sensitive data:
- API keys and secrets (encrypted with Fernet)
- Trading credentials (stored in setting.db)
- Personal telegram bot tokens
- Database with financial transaction history

**Security Checklist**:
- ✅ Credentials encrypted before storage
- ✅ Database files excluded from git (.gitignore)
- ✅ API keys never logged or printed
- ✅ Encryption key stored separately from databases
- ⚠️ Ensure key file is backed up securely (key loss = data loss)
