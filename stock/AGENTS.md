<!-- Parent: ../AGENTS.md -->
# Stock Trading Module (Kiwoom API)

## Purpose

This directory contains the Korean stock market trading system using Kiwoom OpenAPI integration. It implements a multi-process architecture for real-time data reception, strategy execution, and order management for the Korean stock market through Kiwoom Securities.

**Key Capabilities**:
- Real-time tick and minute-level data streaming via ZeroMQ
- Multi-process strategy engines with Template Method pattern
- Order execution and position management
- Kiwoom OpenAPI integration with authentication handling
- High-frequency trading with sub-second response times

**Architecture**: Manager process coordinates independent Receiver, Strategy, and Trader processes communicating through ZMQ and multiprocessing Queues.

## Key Files

### Core Infrastructure

**`kiwoom.py`** (7KB, 183 lines)
- Base class for Kiwoom OpenAPI integration
- QAxWidget wrapper for COM API calls
- TR (Transaction) request/response handling
- Real-time data registration and event callbacks
- Condition search integration
- Parses OpenAPI .enc/.dat files for TR specifications
- Used by all Receiver and Trader processes

**`kiwoom_manager.py`** (15KB, ~470 lines)
- Central process coordinator for stock trading
- Spawns and manages Receiver, Strategy, and Trader processes
- ZeroMQ server integration (`ZmqRecv` thread) on configurable port
- Login window management and authentication flow
- Process lifecycle management (start/stop/restart)
- Routes messages between main GUI and worker processes
- Handles emergency shutdown and error recovery

### Data Reception

**`kiwoom_receiver_tick.py`** (36KB, ~1,145 lines)
- Real-time tick-level data streaming
- Handles 20/10/40 FID real-time data registration
- Condition-based stock discovery (조건검색)
- Tick data aggregation and database storage
- Volume spike detection and filtering
- Publishes data to Strategy processes via ZMQ
- Manages stock registration (up to 100 stocks per screen)

**`kiwoom_receiver_min.py`** (6.5KB, ~208 lines)
- Minute-level candle data aggregation
- Collects OHLCV data for registered stocks
- Less frequent updates (1-minute intervals)
- Simpler data structure than tick receiver
- Used for minute-level strategy engines

**`kiwoom_receiver_client.py`** (6KB, ~188 lines)
- Client-side data receiver for Manager process
- Receives real-time data from ZMQ server
- Forwards data to main GUI for display
- Updates UI tables (호가, 체결, 잔고)
- Handles TR request responses

### Strategy Engines

**`kiwoom_strategy_tick.py`** (43KB, ~1,355 lines)
- Tick-level trading strategy execution
- Inherits from `KiwoomReceiverTick` (Template Method pattern)
- Processes real-time tick data for signal generation
- Implements 133 trading conditions (see `/docs/Condition/Tick/`)
- Strategy variables tracking via `self.vars[N]` pattern
- Dynamic condition loading from database
- Publishes buy/sell signals to Trader process

**`kiwoom_strategy_min.py`** (32KB, ~1,020 lines)
- Minute-level trading strategy execution
- Inherits from `KiwoomReceiverMin`
- OHLCV-based technical analysis
- Lower frequency trading compared to tick strategies
- Separate condition set from tick strategies

### Order Execution

**`kiwoom_trader.py`** (46KB, ~1,437 lines)
- Order execution and position management
- Receives signals from Strategy processes via ZMQ
- Order submission through Kiwoom OpenAPI
- Real-time position tracking (체결, 잔고)
- Risk management and order validation
- Profit/loss calculation and reporting
- Handles order rejections and error recovery
- Database persistence for trade history

### REST API

**`kiwoom_rest.py`** (14KB, ~463 lines)
- REST API interface for external integration
- HTTP endpoints for account queries
- Order submission via REST
- Position and balance inquiries
- Authentication and security handling
- Alternative to direct Kiwoom API calls

## Subdirectories

### `login_kiwoom/`
Kiwoom OpenAPI authentication and login automation.

**Files**:
- `autologin1.py` (2.9KB) - Automated login method 1
- `autologin2.py` (2.9KB) - Automated login method 2 (fallback)
- `manuallogin.py` (4.6KB) - Manual login with window detection
- `versionupdater.py` (3.6KB) - OpenAPI version update automation

**Purpose**: Handles the complex Kiwoom login flow, including certificate authentication, version updates, and window automation using win32gui.

## For AI Agents

### Critical Rules

1. **Windows Only**: This module REQUIRES Windows OS and Kiwoom OpenAPI installed at `C:/OpenAPI`
2. **Korean Variables**: DO NOT translate Korean variable names (현재가, 시가, 고가, 저가, 등락율, 거래량)
3. **ZMQ Communication**: All process communication uses ZeroMQ pub/sub + multiprocessing Queues
4. **Template Method Pattern**: Strategy classes inherit from Receiver classes - respect this hierarchy
5. **Real-time Events**: OnReceiveRealData, OnReceiveChejanData are callback-driven - avoid blocking
6. **Screen Numbers**: Kiwoom API uses screen numbers (1000-2000 range) for data registration management

### Architecture Patterns

**Multi-Process Flow**:
```
Manager Process (kiwoom_manager.py)
├─→ Receiver Process (tick/min)
│   └─→ Strategy Process (tick/min) [inherits Receiver]
│       └─→ Publishes signals via ZMQ
└─→ Trader Process (kiwoom_trader.py)
    └─→ Receives signals, executes orders
```

**Data Flow**:
```
Kiwoom API → Receiver (ZMQ Pub) → Strategy (ZMQ Sub) → Trader (ZMQ Sub) → Order API
```

**Event-Driven Callbacks**:
- `OnReceiveRealData(code, fid, data)` - Real-time tick data
- `OnReceiveChejanData(gubun, fid_cnt, fid_list)` - Order execution events
- `OnReceiveTrData(screen, rqname, trcode, record, nnext)` - TR response
- `OnReceiveMsg(screen, rqname, trcode, msg)` - API messages

### Common Operations

**Adding New Strategy**:
1. Create condition document in `/docs/Condition/Tick/` or `/docs/Condition/Min/`
2. Insert strategy into `strategy.db` via UI or SQL
3. Strategy engine loads conditions dynamically from database
4. No code changes needed for new conditions (data-driven)

**Modifying Receiver Logic**:
1. Edit `kiwoom_receiver_tick.py` or `kiwoom_receiver_min.py`
2. Strategy classes inherit changes automatically (Template Method)
3. Test in isolation before deploying to Strategy

**Order Flow Debugging**:
1. Check `kiwoom_trader.py` logs in `/_log/`
2. Verify ZMQ communication (port binding, message format)
3. Check OpenAPI return codes (0 = success)
4. Review `OnReceiveMsg` and `OnReceiveChejanData` callbacks

### Code Patterns

**Kiwoom API Initialization**:
```python
from kiwoom import Kiwoom

class MyReceiver:
    def __init__(self):
        self.kiwoom = Kiwoom(self, gubun='Receiver')
        self.kiwoom.CommConnect()  # Blocks until login
```

**Real-Time Data Registration**:
```python
# Register stocks for real-time updates
self.kiwoom.SetRealReg((screen, codes, fids, '0'))
# screen: 4-digit string (e.g., '1000')
# codes: semicolon-separated stock codes
# fids: semicolon-separated FID numbers
```

**TR Request**:
```python
df = self.kiwoom.Block_Request(
    'opt10001',  # TR code
    종목코드='005930',  # Input parameters
    output='주식기본정보',  # Output block name
    next='0'  # Next page (0=first, 2=next)
)
```

**ZMQ Publishing**:
```python
self.zctx = zmq.Context()
self.sock = self.zctx.socket(zmq.PUB)
self.sock.bind(f'tcp://*:{port}')

# Publish message
self.sock.send_string('strategy')
self.sock.send_pyobj(data)
```

### Performance Notes

- Kiwoom API has rate limits (초당 5회 TR 제한)
- Real-time data limited to 100 stocks per screen (화면당 100종목)
- Use `pythoncom.PumpWaitingMessages()` to avoid blocking UI
- ZMQ provides sub-millisecond latency for inter-process communication
- Database writes are queued to avoid blocking real-time processing

## Dependencies

**Internal Dependencies**:
- `utility/setting.py` - Global configuration, database paths, credentials
- `utility/static.py` - Helper functions (threading, datetime, encryption)
- `utility/query.py` - Database operations via queryQ
- `ui/ui_mainwindow.py` - Main GUI for process coordination

**External Dependencies**:
- `PyQt5` - GUI framework and QAxWidget for COM integration
- `pythoncom` - Windows COM API message pump
- `zmq` (pyzmq) - ZeroMQ messaging for inter-process communication
- `win32gui` - Windows API for login automation
- `pandas` - Data manipulation for TR responses
- Kiwoom OpenAPI (C:/OpenAPI) - Must be installed separately

**Process Communication**:
- Receives from: Main GUI via windowQ, Manager via ZMQ
- Sends to: Strategy via ZMQ, Trader via ZMQ, Main GUI via qlist
- Database: Reads strategy.db, writes stock_tick.db, tradelist.db

**Related Modules**:
- `/coin/` - Cryptocurrency trading (parallel architecture)
- `/backtester/` - Backtesting engine using historical data from this module
- `/ui/` - GUI components for displaying real-time data

## Technical Notes

### OpenAPI Integration

**Installation Path**: `C:/OpenAPI` (hardcoded in `utility/setting.py`)

**Key Files**:
- `/data/*.enc` - TR specification files (zipped .dat files)
- `KHOpenAPI.ocx` - ActiveX control registered with Windows

**Authentication Flow**:
1. Launch OpenAPI login window
2. Enter certificate password (automated or manual)
3. Check for version updates (versionupdater.py)
4. Verify connection via `OnEventConnect` callback

### ZeroMQ Architecture

**Port Configuration**: Set in `utility/setting.py` (default: 5560-5563)

**Message Protocol**:
```python
# Publisher sends
sock.send_string('channel')  # Channel name
sock.send_pyobj(data)        # Python object (pickled)

# Subscriber receives
channel = sock.recv_string()
data = sock.recv_pyobj()
```

**Channels**:
- `receiver` - Raw market data
- `strategy` - Trading signals
- `trader` - Order execution results
- `manager` - Control messages

### Strategy Variable System

**Self-Referential Indexing**:
```python
self.vars = [0] * 200  # Pre-allocated variable array
self.vars[0] = 현재가
self.vars[1] = 이전가격
self.vars[2] = 상승추세
```

**Parameter Access**:
```python
# Access N-bars-ago value
과거가격 = Parameter_Previous('현재가', N)
```

This pattern enables dynamic strategy loading without code changes.

### Error Handling

**Common Errors**:
- `-100`: Login failure
- `-200`: TR request timeout
- `-300`: API rate limit exceeded
- `-308`: Order rejection (insufficient funds, locked stock, etc.)

**Recovery Strategies**:
- Auto-reconnect on connection loss
- Retry logic with exponential backoff
- Emergency position liquidation on critical errors
- Process restart via Manager

## Security Considerations

1. **Credentials**: API credentials encrypted using Fernet in `setting.db`
2. **Authentication**: Certificate-based login (공동인증서)
3. **Order Validation**: Risk checks before order submission
4. **Blacklist**: Stock blacklist management in `utility/setting.py`
5. **Logging**: All orders logged to `/_log/` and `tradelist.db`

## Testing

**Test Files**: See `/lecture/testcode/` for ZMQ communication tests
- `zmq_pub.py` - ZMQ publisher test
- `zmq_sub1/2/3.py` - ZMQ subscriber tests

**Validation**:
1. Run `python utility/database_check.py` before starting
2. Verify Kiwoom OpenAPI connection
3. Test with paper trading account first
4. Monitor logs in `/_log/stock_*.log`

## Version Requirements

- **Windows**: Required (Kiwoom OpenAPI is Windows-only)
- **Python**: 3.8+ (64-bit for memory management)
- **Kiwoom OpenAPI**: Latest version (auto-updates)
- **PyQt5**: 5.15+ (for QAxWidget support)
- **pyzmq**: 25.0+ (for ZeroMQ 4.x)
