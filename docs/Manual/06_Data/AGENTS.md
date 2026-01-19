<!-- Parent: ../AGENTS.md -->
# Data Management Documentation

## Purpose

Complete database architecture documentation covering STOM's 15 SQLite databases, schema specifications, setting management, query processes, and data integrity verification. This section provides comprehensive reference for all data storage, retrieval, and management operations across the trading system.

## Key Files

- **data_management.md** - Database architecture and management covering:
  - 15 SQLite databases in `/_database/` directory
  - Schema specifications (108 minute columns, Storbritannien tick columns documented)
  - Setting database (setting.db with encrypted credentials)
  - Market data storage (tick, minute, trade history)
  - Query process architecture (queue-based database operations)
  - Database integrity verification (database_check.py)
  - Data flow and persistence patterns

## For AI Agents

### Maintaining This Section

**When to Update:**
- New database added to `_database/` directory
- Schema changes (new tables, columns, indices)
- Query patterns modified
- Data retention policies changed
- Encryption methods updated
- Database integrity checks modified
- Performance optimization changes

**Critical Validation Points:**

1. **Database Count and List** - Must match actual _database/ directory:
   ```bash
   # Should list exactly 15 databases
   ls C:\System_Trading\STOM\STOM_V1\_database\*.db

   # Expected databases:
   setting.db           # System settings and encrypted credentials
   stock_tick.db        # Stock tick data
   stock_min.db         # Stock minute data
   coin_tick.db         # Cryptocurrency tick data
   coin_min.db          # Cryptocurrency minute data
   tradelist.db         # Trading history and performance
   strategy.db          # Trading strategies and parameters
   backtest.db          # Backtesting results
   optuna.db            # Optimization results
   # Plus others as documented
   ```

2. **Schema Documentation** - Verify against actual table structures:
   ```python
   # utility/setting.py - Database paths and connections
   # utility/query.py - Query definitions and schema access

   # Cross-reference with:
   # docs/Guideline/Stock_Database_Information.md
   # - 108 minute columns documented
   # - 93 tick columns documented
   ```

3. **Query Process Architecture** - Confirm queue-based pattern:
   ```python
   # utility/query.py - Query process implementation
   # Queue: queryQ (index 2 in qlist)
   # Pattern: queryQ.put(['command', *args])
   ```

**Update Guidelines:**
1. **Read Before Editing** - Always read `data_management.md` completely
2. **Verify Schema Changes** - Test against actual database files
3. **Update Cross-References** - Coordinate with Stock_Database_Information.md
4. **Test Queries** - Validate all documented SQL queries execute correctly
5. **Check Encryption** - Verify credential encryption still works

### Code-Documentation Alignment

**Key Source References:**

**Database Management:**
```python
utility/setting.py - Database path definitions
- 15 database paths defined
- Connection pooling configuration
- Schema initialization

utility/query.py (24KB) - Query process implementation
- Queue-based database operations
- Query definitions for all databases
- Transaction management
- Error handling

utility/database_check.py - Integrity verification
- Schema validation
- Data consistency checks
- Automatic startup verification
```

**Schema Definitions:**
```python
# Primary data storage schemas
stock_tick.db - Tick-level stock data
stock_min.db - Minute-level stock data
coin_tick.db - Tick-level cryptocurrency data
coin_min.db - Minute-level cryptocurrency data

# System databases
setting.db - Configuration and encrypted credentials
tradelist.db - Order history and trade records
strategy.db - Trading strategy parameters

# Analysis databases
backtest.db - Backtesting results and metrics
optuna.db - Optimization trial results
```

**Credential Encryption:**
```python
utility/setting.py - Fernet encryption
utility/static.py - Crypto helper functions

# Encrypted fields in setting.db:
- Kiwoom account credentials
- Upbit API keys
- Binance API keys
- Telegram bot tokens
```

**Validation Checklist:**
- [ ] Database count is exactly 15
- [ ] All database purposes documented
- [ ] Schema column counts match actual (108 min, 93 tick)
- [ ] Query patterns match utility/query.py
- [ ] Encryption methods current
- [ ] Integrity check process documented
- [ ] Cross-references to Stock_Database_Information.md valid

### Content Structure

**Standard Sections in data_management.md:**
1. **Database Overview** - 15 databases and purposes
2. **Setting Database** - Configuration and credentials
   - Encrypted credential storage
   - System configuration tables
   - User preferences
3. **Market Data Databases** - Real-time and historical data
   - Tick databases (stock_tick.db, coin_tick.db)
   - Minute databases (stock_min.db, coin_min.db)
   - Schema specifications
   - Index strategies
4. **Trading Databases** - Order and trade history
   - tradelist.db structure
   - Performance metrics
   - Trade analysis tables
5. **Strategy Databases** - Strategy parameters and results
   - strategy.db schema
   - Parameter storage
   - Strategy versioning
6. **Backtesting Databases** - Test results and optimization
   - backtest.db structure
   - optuna.db for optimization
   - Performance metrics
7. **Query Process Architecture** - Database access pattern
   - Queue-based operations (queryQ)
   - Transaction management
   - Connection pooling
8. **Data Integrity** - Verification and consistency
   - database_check.py automation
   - Integrity constraints
   - Recovery procedures

**What Belongs Here:**
- Database schemas and structures
- Query patterns and SQL
- Data retention policies
- Encryption methods
- Integrity verification
- Performance optimization
- Backup and recovery

**What Belongs Elsewhere:**
- Data display in UI → `05_UI_UX/`
- Data processing logic → `03_Modules/`
- API data sources → `04_API/`
- Architecture context → `02_Architecture/`

### Common Updates

**Adding New Database:**
1. Add to database list (must maintain count)
2. Document purpose and use cases
3. Describe schema structure
4. Document access pattern (which processes use it)
5. Update query.py documentation
6. Update database_check.py if verification needed
7. Update utility/setting.py database paths

**Modifying Schema:**
1. Document schema change with migration steps
2. Update column count documentation
3. Update Stock_Database_Information.md
4. Document backward compatibility
5. Update query.py affected queries
6. Test database_check.py validation
7. Note schema version change

**Changing Query Patterns:**
1. Document new query approach
2. Update query.py code examples
3. Describe performance implications
4. Update transaction management if affected
5. Test error handling scenarios

## Dependencies

**Related Manual Sections:**
- `02_Architecture/` - Query process in multiprocess architecture
- `03_Modules/utility_module.md` - Database utility implementation
- `07_Trading/` - Trading data storage
- `08_Backtesting/` - Backtesting data storage

**Source Code References:**
- `utility/setting.py` (42KB) - Database paths and configuration
- `utility/query.py` (24KB) - Query process and SQL
- `utility/database_check.py` - Integrity verification
- `utility/static.py` - Encryption helpers
- `_database/*.db` - Actual database files (excluded from git)

**External Documentation:**
- `../Guideline/Stock_Database_Information.md` - Detailed schema reference
  - 108 minute columns documented
  - 93 tick columns documented
  - Column types and purposes

**Documentation Network:**
- Parent: `../AGENTS.md` - Manual documentation standards
- Overview: `../01_Overview/project_overview.md` - Database count summary
- Architecture: `../02_Architecture/system_architecture.md` - Query process architecture
- Guideline: `../../Guideline/Stock_Database_Information.md` - Schema details

## Special Considerations

### Database File Exclusion
**CRITICAL:** Database files excluded from git:
- `_database/` directory in `.gitignore`
- Contains sensitive trading data
- Contains encrypted credentials
- Fresh installation requires database initialization

Document database initialization process clearly.

### Credential Encryption
**CRITICAL:** All credentials encrypted with Fernet:
```python
from cryptography.fernet import Fernet

# Encryption key management
# Key stored separately from databases
# Never commit encryption keys to git
```

Document encryption process:
1. Key generation
2. Credential encryption
3. Storage in setting.db
4. Decryption for use
5. Key rotation procedures

### Schema Column Counts
**Must match Stock_Database_Information.md:**
- Stock minute data: 108 columns
- Stock tick data: 93 columns

These counts verified in documentation compliance checks. Update both files together.

### Query Process Queue
**Queue:** queryQ (index 2 in qlist)

All database operations go through query process:
- Ensures serialized access
- Prevents database locks
- Centralized error handling
- Transaction management

Document queue message format:
```python
queryQ.put(['command', 'database', 'operation', *args])
```

### Database Integrity Checks
**Automatic:** database_check.py runs at startup

Verification includes:
- Schema validation
- Index verification
- Data consistency checks
- Corruption detection
- Automatic repairs if possible

Document check procedures and manual recovery steps.

### Performance Optimization
Document optimization strategies:
- Index design for common queries
- Connection pooling parameters
- Transaction batching
- Query optimization techniques
- Vacuum and analyze schedules

### Data Retention Policies
Document retention rules:
- Real-time tick data retention period
- Historical minute data retention
- Trade history archival
- Backtesting result cleanup
- Log data retention

### Backup Procedures
Document backup strategies:
- Database backup frequency
- Backup location and format
- Restoration procedures
- Testing backup integrity
- Disaster recovery steps

### Migration Procedures
When schemas change:
1. Document schema version
2. Provide migration SQL scripts
3. Test migration on copy first
4. Backup before migration
5. Verify data integrity after
6. Update documentation

### Korean Column Names
Many tables use Korean column names:
- 현재가 (current price)
- 시가 (open price)
- 고가 (high price)
- 저가 (low price)
- 거래량 (volume)
- 등락율 (rate of change)

**Never translate these.** Document romanization if needed for international developers.

### Database Statistics
Maintain database size statistics:
- Typical database sizes
- Growth rates
- Storage requirements
- Performance characteristics

Update after significant data accumulation.

### Multi-Database Queries
Some operations span multiple databases:
- Document join strategies
- Note transaction boundaries
- Describe consistency guarantees
- Explain performance implications

### SQLite-Specific Features
Document SQLite-specific considerations:
- WAL mode for concurrency
- Memory-mapped I/O
- Page size optimization
- Journal modes
- Pragma settings

### Testing Database Operations
Provide testing procedures:
```python
# Test database connectivity
python utility/database_check.py

# Test query process
python -c "from utility.query import *; test_queries()"

# Verify schema
python -c "from utility.setting import *; print_schemas()"
```

### Cross-Database Consistency
Some data relationships span databases:
- Document referential integrity approaches
- Describe consistency enforcement
- Note eventual consistency patterns
- Explain reconciliation procedures

### Data Privacy
Document data privacy considerations:
- Personal trading data
- API credentials
- Account information
- Logging sensitive data
- Data anonymization for debugging

### Performance Monitoring
Document database performance monitoring:
- Query execution time tracking
- Index usage statistics
- Lock contention monitoring
- Storage utilization
- Query plan analysis

Provide tools or queries for monitoring.
