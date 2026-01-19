<!-- Parent: ../AGENTS.md -->
# System Architecture Documentation

## Purpose

Comprehensive system design documentation covering STOM's multiprocess architecture, 15-queue communication system, data flow patterns, process coordination, and design patterns. This section provides the technical blueprint for understanding how all system components interact, communicate, and coordinate in a high-frequency trading environment.

## Key Files

- **system_architecture.md** - Complete architectural documentation including:
  - Multiprocess execution model (7+ concurrent processes)
  - 15-queue communication system (qlist architecture)
  - Data flow patterns (real-time, backtesting, UI updates)
  - Design patterns (Strategy, Observer, Factory, Singleton, Template Method, Command)
  - Process coordination and lifecycle management
  - ZeroMQ (ZMQ) integration for high-performance IPC

## For AI Agents

### Maintaining This Section

**When to Update:**
- New process types added or removed
- Queue system modifications (adding/removing queues from qlist)
- Communication protocol changes (ZMQ, WebSocket, multiprocessing.Queue)
- Design pattern implementations modified
- Data flow architecture changes
- Process coordination logic updates

**Critical Validation Points:**
1. **Queue System Accuracy** - The 15-queue qlist MUST match `utility/setting.py`
   ```python
   qlist = [
       windowQ,    # 0  - Main window events
       soundQ,     # 1  - Audio notifications
       queryQ,     # 2  - Database operations
       teleQ,      # 3  - Telegram notifications
       chartQ,     # 4  - Chart updates
       hogaQ,      # 5  - Order book data
       webcQ,      # 6  - Web communication
       backQ,      # 7  - Backtesting
       creceivQ,   # 8  - Coin receiver
       ctraderQ,   # 9  - Coin trader
       cstgQ,      # 10 - Coin strategy
       liveQ,      # 11 - Live trading data
       kimpQ,      # 12 - Kimchi premium (arbitrage)
       wdzservQ,   # 13 - WebSocket ZMQ server
       totalQ      # 14 - Overall statistics
   ]
   ```

2. **Process Architecture** - Verify against actual process files:
   - `stock/kiwoom_manager.py` - Stock trading process orchestration
   - `coin/*_receiver_*.py` - Cryptocurrency data collection
   - `*_strategy_*.py` - Trading signal generation
   - `*_trader.py` - Order execution
   - `backtester/*.py` - Backtesting engines
   - `ui/ui_mainwindow.py` - GUI main process

3. **Design Patterns** - Confirm implementations exist in code:
   - **Strategy Pattern** - Market-specific strategy engines
   - **Observer Pattern** - Queue/WebSocket event-driven updates
   - **Factory Pattern** - Market-specific engine instantiation
   - **Singleton Pattern** - Setting and database managers
   - **Template Method** - Strategy class hierarchy (Receiver → Strategy)
   - **Command Pattern** - Queue-based inter-process communication

**Update Guidelines:**
1. **Read Before Editing** - Always read `system_architecture.md` completely
2. **Verify Process Counts** - Count actual process spawns in manager files
3. **Test Queue Communication** - Ensure queue index references are accurate
4. **Validate Flow Diagrams** - Confirm data flow descriptions match actual behavior
5. **Check Design Pattern Claims** - Verify each pattern with actual code examples

### Code-Documentation Alignment

**Key Source References:**
```python
# Queue system definition
utility/setting.py - Line ~50-70 (qlist definition)

# Main process coordination
ui/ui_mainwindow.py - Process spawning and queue setup

# Stock market processes
stock/kiwoom_manager.py - Manager process orchestration
stock/kiwoom_receiver_tick.py - Data collection
stock/kiwoom_strategy_tick.py - Signal generation
stock/kiwoom_trader.py - Order execution

# Cryptocurrency processes
coin/upbit_receiver_tick.py - Upbit data streaming
coin/binance_receiver_tick.py - Binance data streaming
coin/*_strategy_*.py - Crypto trading strategies

# Backtesting processes
backtester/backtest.py - Backtesting orchestrator
backtester/backengine_*_*.py - Market-specific engines

# Database query process
utility/query.py - Queue-based database operations
```

**Validation Checklist:**
- [ ] Queue count matches qlist (currently 15 queues)
- [ ] Process types match actual manager files
- [ ] Data flow diagrams reflect actual communication paths
- [ ] Design patterns have code examples
- [ ] ZMQ usage matches implementation in manager files
- [ ] WebSocket connections match receiver implementations
- [ ] Multiprocessing.Queue usage matches actual queues

### Content Structure

**Standard Sections in system_architecture.md:**
1. **Multiprocess Architecture** - Process types and coordination
2. **Queue Communication System** - 15-queue qlist architecture
3. **Data Flow Patterns** - Real-time, backtesting, UI update flows
4. **Process Lifecycle** - Startup, runtime, shutdown sequences
5. **Design Patterns** - Six core patterns with code examples
6. **Communication Protocols** - ZMQ, WebSocket, Queue, SQLite
7. **Performance Considerations** - Concurrency, IPC overhead, optimization

**Architecture Diagrams Should Include:**
- Process hierarchy and relationships
- Queue routing and data flow
- Inter-process communication patterns
- Lifecycle state transitions
- Error handling and recovery flows

### Common Updates

**Adding New Process Type:**
1. Update multiprocess architecture section
2. Add to process hierarchy diagram
3. Document queue usage (which queues it reads/writes)
4. Describe lifecycle integration
5. Note startup order dependencies

**Modifying Queue System:**
1. Update qlist definition with exact indices
2. Document queue purpose and data format
3. List all producer and consumer processes
4. Update data flow diagrams
5. Note any index changes affecting multiple files

**Changing Communication Protocol:**
1. Document protocol selection rationale
2. Describe message formats and serialization
3. Update performance characteristics
4. Note error handling and retry logic
5. Update affected data flow patterns

## Dependencies

**Related Manual Sections:**
- `03_Modules/` - Detailed module implementations of architectural components
- `04_API/` - External API integrations within process architecture
- `05_UI_UX/` - GUI main process and event handling
- `06_Data/` - Database access via query process and queue
- `07_Trading/` - Trading process architecture and coordination

**Source Code References:**
- `utility/setting.py` - Queue definitions (qlist)
- `ui/ui_mainwindow.py` - Main process and process spawning
- `stock/kiwoom_manager.py` - Stock trading process manager
- `coin/*_receiver_*.py` - Cryptocurrency receiver processes
- `*_strategy_*.py` - Strategy engine processes
- `*_trader.py` - Trading execution processes
- `backtester/backtest.py` - Backtesting orchestration
- `utility/query.py` - Database query process

**Documentation Network:**
- Parent: `../AGENTS.md` - Manual documentation standards
- Overview: `../01_Overview/project_overview.md` - High-level architecture summary
- Learning: `../../learning/02-아키텍처-개요.md` - User-facing architecture guide (Korean)

**Cross-References:**
- Module documentation references architecture for context
- Trading engine docs reference process coordination
- Data management docs reference query process architecture
- UI docs reference main process and event queue system

## Special Considerations

### Queue System Synchronization
**Critical:** The qlist definition in `utility/setting.py` is the single source of truth. All documentation must match exactly:
- Queue count (15 queues)
- Queue indices (0-14)
- Queue names and purposes
- Queue data types and formats

### Process Communication Performance
- ZMQ used for high-frequency data streaming (receiver → strategy)
- multiprocessing.Queue for control messages and state updates
- WebSocket for exchange API real-time data
- SQLite for persistent storage and process-shared data
- Document performance characteristics and trade-offs

### Design Pattern Validation
Each documented design pattern must have:
- Clear code example from actual implementation
- Class hierarchy diagram showing inheritance
- Explanation of pattern benefits in trading context
- References to specific files implementing pattern

### Architecture Evolution
Track major architectural changes:
- Process additions/removals
- Queue system modifications
- Communication protocol upgrades
- Performance optimizations
- Maintain changelog of architectural decisions

### Verification Procedures
Run these checks when updating architecture documentation:
```bash
# Verify process count
grep -r "Process(" stock/ coin/ backtester/ utility/ | wc -l

# Verify queue definitions
grep "windowQ\|soundQ\|queryQ" utility/setting.py

# Check ZMQ usage
grep -r "zmq\." stock/ coin/

# Validate WebSocket connections
grep -r "websocket" coin/
```

### Cross-Module Impact
Architecture changes often require updates to:
- `../03_Modules/` - Module implementation details
- `../../learning/02-아키텍처-개요.md` - Korean learning guide
- `../../CLAUDE.md` - Project-level architecture summary
- Multiple module-specific documentation files

Always coordinate architecture documentation updates across all affected sections.
