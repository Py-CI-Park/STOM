<!-- Parent: ../AGENTS.md -->
# Cryptocurrency Trading Module

## Purpose
This directory contains the cryptocurrency trading subsystem for STOM V1, supporting both **Upbit** (Korean exchange) and **Binance** (international exchange) with real-time tick-level data processing, strategy engines, and multi-exchange order execution. It implements WebSocket-based high-frequency trading with multiprocess architecture for parallel data collection, signal generation, and trade execution.

## Key Components

### Multi-Exchange Architecture
The module supports dual-exchange operations with independent but parallel processing pipelines:
- **Upbit Pipeline**: 8 files (~5,000 lines) - Korean KRW market
- **Binance Pipeline**: 8 files (~5,000 lines) - USDT futures and spot markets
- **Kimp Module**: Kimchi premium (price arbitrage) monitoring between exchanges

### Process Types
1. **Receivers**: WebSocket data collection (`*_receiver_*.py`)
2. **Strategies**: Signal generation engines (`*_strategy_*.py`)
3. **Traders**: Order execution and position management (`*_trader.py`)
4. **WebSockets**: Exchange-specific connection handlers (`*_websocket.py`)
5. **Clients**: REST API interaction (`*_receiver_client.py`)

## Key Files

### Upbit Exchange (8 files)
- **upbit_strategy_tick.py** - Tick-level (second-level) trading strategy engine
  - Inherits base strategy patterns
  - Real-time signal generation from tick data
  - Technical indicator computation (TA-Lib integration)
  - Korean variable names: 현재가, 시가, 고가, 저가, 등락율

- **upbit_strategy_min.py** - Minute-level (1/3/5-minute) strategy engine
  - Inherits from `UpbitStrategyTick` (Template Method pattern)
  - Aggregated candle analysis with minute-level data
  - Historical data lookback via `Parameter_Previous()` method

- **upbit_trader.py** - Upbit order execution and position management
  - pyupbit REST API integration for orders
  - Real-time position tracking and P&L calculation
  - Buy/sell signal handling from strategy queues
  - Database persistence for trade history

- **upbit_receiver_tick.py** - Real-time tick data collection
  - WebSocket connection to Upbit streaming API
  - ZMQ publisher (port 5778) for data distribution
  - Tick-to-minute aggregation for strategy engines
  - Database storage to `coin_tick.db` and `coin_min.db`

- **upbit_receiver_min.py** - Minute-level data receiver (aggregated data)

- **upbit_receiver_client.py** - REST API client for historical data and account info

- **upbit_websocket.py** - WebSocket connection manager for Upbit
  - Handles connection lifecycle, reconnection logic
  - Message parsing and distribution

### Binance Exchange (8 files)
- **binance_strategy_tick.py** - Tick-level strategy for Binance futures/spot

- **binance_strategy_min.py** - Minute-level strategy engine
  - Inherits from `BinanceStrategyTick`
  - Supports both short and long positions (futures)
  - Leverage management via `GetBinanceShortPgSgSp` / `GetBinanceLongPgSgSp`

- **binance_trader.py** - Binance order execution for futures and spot
  - python-binance library for REST API
  - WebSocket trader subprocess (`binance_websocket.WebSocketTrader`)
  - Long/short position tracking for futures
  - Leverage management and liquidation monitoring

- **binance_receiver_tick.py** - Real-time tick data from Binance WebSocket

- **binance_receiver_min.py** - Minute-level aggregated data receiver

- **binance_receiver_client.py** - REST API client for historical candles

- **binance_websocket.py** - WebSocket manager for Binance streams
  - Multi-stream subscription (trades, orderbook, klines)
  - Futures and spot market support

### Cross-Exchange Monitoring
- **kimp_upbit_binance.py** - Kimchi premium arbitrage monitor
  - Real-time price comparison between Upbit (KRW) and Binance (USDT)
  - USD/KRW conversion rate tracking
  - Arbitrage opportunity detection
  - Dual WebSocket subscriptions to both exchanges
  - Process: monitors price spreads, calculates kimchi premium percentage

## Subdirectories
- **__pycache__/** - Python bytecode cache (git-ignored)

## Data Flow Architecture

### Queue-Based Communication
The module interacts with 15 queues from the main qlist:
```python
windowQ   # 0  - Main window UI updates
soundQ    # 1  - Audio notifications
queryQ    # 2  - Database operations (via query process)
teleQ     # 3  - Telegram alerts
chartQ    # 4  - Real-time chart updates
hogaQ     # 5  - Order book (호가) data
webcQ     # 6  - Web communication
backQ     # 7  - Backtesting operations
creceivQ  # 8  - Coin receiver commands
ctraderQ  # 9  - Coin trader commands
cstgQ     # 10 - Coin strategy commands
liveQ     # 11 - Live trading data
kimpQ     # 12 - Kimchi premium data
wdzservQ  # 13 - WebSocket ZMQ server
totalQ    # 14 - System-wide statistics
```

### Process Flow
1. **Data Collection**: WebSocket → Receiver → Database + ZMQ Publisher
2. **Signal Generation**: Receiver → Strategy Queue → Strategy Engine → Buy/Sell Signals
3. **Order Execution**: Strategy → Trader Queue → Trader → Exchange API
4. **UI Updates**: Trader → windowQ/chartQ → Main Window → Display

### ZMQ Distribution
- Receivers publish tick data via ZMQ (port 5778 for Upbit)
- Enables efficient multiprocess distribution without queue bottlenecks
- Strategy and analysis processes subscribe to relevant data streams

## For AI Agents

### Critical Rules

1. **Preserve Korean Variable Names**
   - **DO NOT translate**: 현재가 (current price), 시가 (open), 고가 (high), 저가 (low), 등락율 (change rate)
   - **DO NOT translate**: 매수 (buy), 매도 (sell), 체결강도 (execution strength), 호가 (order book)
   - These are domain-standard names used throughout the system

2. **Template Method Pattern**
   - Strategy classes inherit from base tick strategies
   - `Strategy(self, data)` method is the template hook
   - Minute strategies extend tick strategies with additional aggregated data

3. **Parameter Access Pattern**
   - Use `Parameter_Previous(index, lookback)` for historical data access
   - Helper functions: `현재가N(pre)`, `시가N(pre)`, `고가N(pre)`, etc.
   - `self.dict_arry[종목코드][index, column]` for raw array access

4. **Queue Communication**
   - All process communication via queues (no direct calls)
   - Follow qlist indexing convention (0-14)
   - Use tuple unpacking for data parameters

5. **WebSocket Handling**
   - Connection lifecycle managed by dedicated classes
   - Always implement reconnection logic
   - Handle both exchange-specific message formats

6. **Database Operations**
   - Never direct SQLite access - use queryQ
   - Databases: `coin_tick.db`, `coin_min.db`, `tradelist.db`, `strategy.db`
   - Settings stored in encrypted format in `setting.db`

### Code Patterns

**Strategy Signal Generation**:
```python
# Buy signal example
if 매수조건1 and 매수조건2:
    self.매수신호 = True
    self.매수가격 = 현재가
    self.매수수량 = self.GetBuyAmount(종목코드)
```

**Trader Order Execution**:
```python
# Queue-based order handling
if signal == 'buy':
    order_result = self.upbit.buy_market_order(code, amount)
    self.dict_buy[code] = order_result
```

**Historical Lookback**:
```python
# Access 5 bars ago
previous_close = 현재가N(5)
# Access at buffer start
buffer_start = 현재가N(-1)
```

### Testing Considerations

1. **WebSocket Mocking**
   - Mock exchange WebSocket responses for testing
   - Test reconnection logic with simulated disconnections
   - Verify data integrity through the receiver → strategy → trader pipeline

2. **Strategy Backtesting**
   - Use `backtester/backengine_coin_tick.py` or `backengine_coin_min.py`
   - Verify strategy logic against historical data from databases
   - Check condition documentation in `/docs/Condition/Tick/` or `/docs/Condition/Min/`

3. **Order Execution Testing**
   - Use testnet/sandbox APIs when available (Binance testnet)
   - Verify order parameters before live trading
   - Monitor queue communication delays

### Exchange-Specific Notes

**Upbit**:
- KRW market only (no leverage)
- Spot trading only
- Market/limit orders via pyupbit
- WebSocket ticker and orderbook streams
- Trade fees: 0.05% (configurable in settings)

**Binance**:
- USDT pairs (spot and futures)
- Leverage trading supported (up to 125x)
- Long/short positions
- Multiple order types (market, limit, stop-loss)
- WebSocket: trades, depth, kline streams
- Separate spot and futures APIs

**Kimchi Premium (Kimp)**:
- Monitors price differences between Upbit (KRW) and Binance (USDT)
- Requires USD/KRW conversion rate
- Arbitrage opportunities when premium exceeds thresholds
- Real-time dual WebSocket subscriptions

### Common Issues

1. **WebSocket Disconnections**
   - Exchanges periodically disconnect idle connections
   - Implement exponential backoff for reconnections
   - Check network stability and firewall settings

2. **API Rate Limits**
   - Upbit: 8 requests/second (public), 8 requests/second (private)
   - Binance: Weight-based (1200/minute), order-based (10/second)
   - Use WebSocket for real-time data, REST only for orders/historical

3. **Data Synchronization**
   - Tick data arrives asynchronously
   - Strategy engines must handle partial data
   - Database writes via queryQ to avoid locking

4. **Position Tracking**
   - Upbit: Simple buy/sell tracking (no positions)
   - Binance: Long/short position management, liquidation monitoring
   - Verify position state after reconnections

### Documentation References

- **Condition Files**: `/docs/Condition/Tick/` and `/docs/Condition/Min/`
  - Each strategy has corresponding condition documentation (98.3% compliance)
  - Contains optimized parameters (BO, SO) and ranges (BOR, SOR, OR, GAR)

- **Database Schema**: `/docs/Guideline/Stock_Database_Information.md`
  - Shared schema between stock and coin modules
  - Columns documented with Korean-English mapping

- **Backtesting Guide**:
  - Tick strategies: `/docs/Guideline/Back_Testing_Guideline_Tick.md` (826 documented variables)
  - Min strategies: `/docs/Guideline/Back_Testing_Guideline_Min.md` (752 documented variables)

## Dependencies

### Core Libraries
- **pyupbit** - Upbit REST API and WebSocket client
- **python-binance** / **binance** - Binance REST API and WebSocket
- **websockets** - Async WebSocket connections
- **pyzmq** - ZeroMQ for high-performance message distribution

### Data Processing
- **numpy** (==1.26.4) - Numerical arrays for tick/minute data storage
- **pandas** (==2.0.3) - DataFrames for trade history and analysis
- **TA-Lib** - Technical analysis indicators (custom wheel in `/utility/`)

### Supporting Libraries
- **PyQt5** - UI components and event loops
- **sqlite3** - Database storage and retrieval
- **cryptography** - API key encryption (Fernet)
- **requests** - REST API fallback and auxiliary calls

### Exchange-Specific
- **pyupbit** - `pyupbit.get_tickers()`, `pyupbit.Upbit()` for orders
- **binance.Client** - REST API client for Binance
- **BinanceSocketManager** - WebSocket stream manager
- **AsyncClient** - Async operations for futures trading

## Performance Considerations

1. **Tick Processing Speed**
   - Sub-millisecond tick ingestion required for HFT
   - NumPy arrays for efficient historical data storage
   - ZMQ publishing avoids queue serialization overhead

2. **Strategy Latency**
   - Target: <10ms from tick → signal
   - TA-Lib streaming mode for real-time indicators
   - Minimize database reads in hot path

3. **Order Execution Speed**
   - Direct REST API calls (no middleware)
   - Pre-computed position sizes and parameters
   - WebSocket order updates for fastest confirmation

4. **Database Optimization**
   - Indexed tables for tick/minute data queries
   - Batch inserts via queryQ to avoid locking
   - Separate databases for tick vs. minute to reduce contention

## Security and API Management

1. **Credential Storage**
   - API keys encrypted with `cryptography.fernet` in `setting.db`
   - Loaded via `utility/setting.py` and `utility/static.py`
   - Never hardcode API keys or secrets

2. **API Key Permissions**
   - Upbit: Trading permission required
   - Binance: Spot and/or Futures trading enabled
   - Recommended: IP whitelist restrictions

3. **Risk Controls**
   - Position size limits in settings
   - Maximum leverage configuration (Binance)
   - Coin blacklist management
   - Daily loss limits and circuit breakers
