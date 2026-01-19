<!-- Parent: ../AGENTS.md -->
# Trading Engine Documentation

## Purpose

Comprehensive documentation of STOM's real-time trading execution engine, covering strategy signal generation, order execution, position management, risk controls, and order lifecycle management. This section provides complete technical reference for the core trading functionality that drives automated trading across Korean stocks and cryptocurrencies.

## Key Files

- **trading_engine.md** - Complete trading engine documentation covering:
  - Strategy engines (*_strategy_*.py - signal generation and technical analysis)
  - Trader processes (*_trader.py - order execution and position management)
  - Receiver processes (*_receiver_*.py - real-time data collection and preprocessing)
  - Risk controls and position sizing
  - Order lifecycle management (creation, submission, fill, cancel)
  - Performance monitoring and trade logging
  - Template Method pattern in strategy implementation

## For AI Agents

### Maintaining This Section

**When to Update:**
- New trading strategies implemented
- Order execution logic modified
- Risk management rules changed
- Position sizing algorithms updated
- Signal generation methods changed
- Performance tracking enhanced
- Multi-market coordination modified

**Critical Validation Points:**

1. **Strategy Engine Files** - Verify strategy implementation files:
   ```bash
   # Stock strategies
   ls stock/kiwoom_strategy_tick.py  # 42KB tick strategy
   ls stock/kiwoom_strategy_min.py   # Minute strategy

   # Crypto strategies
   ls coin/upbit_strategy_tick.py
   ls coin/upbit_strategy_min.py
   ls coin/binance_strategy_tick.py
   ls coin/binance_strategy_min.py
   ```

2. **Trader Implementation** - Confirm order execution files:
   ```bash
   # Stock trader
   ls stock/kiwoom_trader.py  # 46KB order execution

   # Crypto traders
   ls coin/upbit_trader.py
   ls coin/binance_trader.py
   ```

3. **Receiver Data Flow** - Verify data collection processes:
   ```bash
   # Real-time data receivers
   ls stock/kiwoom_receiver_tick.py
   ls coin/upbit_receiver_tick.py
   ls coin/binance_receiver_tick.py
   ```

4. **Template Method Pattern** - Verify strategy class hierarchy:
   ```python
   # Base pattern: Receiver → Strategy (Template Method)
   # Strategy classes define template, subclasses implement hooks
   # Tick strategies are base, Minute strategies derive
   ```

**Update Guidelines:**
1. **Read Before Editing** - Always read `trading_engine.md` completely
2. **Verify Strategy Logic** - Test strategy signal generation
3. **Check Risk Controls** - Validate risk management rules documented
4. **Test Order Flow** - Verify order lifecycle descriptions accurate
5. **Update Performance Metrics** - Keep performance documentation current

### Code-Documentation Alignment

**Key Source References:**

**Strategy Engines:**
```python
stock/kiwoom_strategy_tick.py (42KB) - Stock tick strategy
- Technical indicator calculations
- Signal generation logic
- Buy/sell condition evaluation
- Risk management integration
- Template Method pattern implementation

coin/upbit_strategy_min.py - Upbit minute strategy
coin/binance_strategy_min.py - Binance minute strategy
```

**Trader Processes:**
```python
stock/kiwoom_trader.py (46KB) - Stock order execution
- Order creation and submission
- Position tracking
- Fill monitoring
- Cancel/modify operations
- Trade logging

coin/upbit_trader.py - Upbit order execution
coin/binance_trader.py - Binance order execution
```

**Receiver Processes:**
```python
stock/kiwoom_receiver_tick.py - Real-time stock data
- WebSocket/ZMQ data streaming
- Data normalization
- Queue distribution

coin/upbit_receiver_tick.py - Upbit WebSocket
coin/binance_receiver_tick.py - Binance WebSocket
```

**Risk Management:**
```python
utility/setting.py - Risk parameters
- Position size limits
- Maximum loss thresholds
- Daily trade limits
- Blacklist management
```

**Validation Checklist:**
- [ ] Strategy file references accurate (tick vs. minute)
- [ ] Order execution flow matches trader implementation
- [ ] Risk controls match setting.py configuration
- [ ] Signal generation logic accurately described
- [ ] Template Method pattern correctly documented
- [ ] Korean trading terms preserved (매수, 매도, 체결, 잔고)
- [ ] Performance metrics match actual calculations

### Content Structure

**Standard Sections in trading_engine.md:**
1. **Trading Architecture Overview** - Process coordination
   - Receiver → Strategy → Trader flow
   - Queue-based communication
   - Process lifecycle
2. **Strategy Engines** - Signal generation
   - Technical indicator calculations (TA-Lib integration)
   - Buy/sell condition evaluation
   - Template Method pattern (base strategy, hook methods)
   - Self-referencing indexing (self.vars[N])
   - Parameter management (Parameter_Previous)
3. **Order Execution** - Trader processes
   - Order creation and validation
   - Exchange API integration
   - Order status monitoring
   - Fill tracking
   - Cancel/modify operations
4. **Risk Management** - Risk controls
   - Position sizing algorithms
   - Maximum loss limits
   - Daily trade count limits
   - Blacklist enforcement
   - Drawdown protection
5. **Position Management** - Portfolio tracking
   - Position entry/exit
   - Average price calculation
   - Realized/unrealized PnL
   - Portfolio statistics
6. **Performance Monitoring** - Trade tracking
   - Trade logging to tradelist.db
   - Win rate calculation
   - Profit factor metrics
   - Maximum drawdown tracking
7. **Multi-Market Coordination** - Cross-market strategies
   - Kimchi premium arbitrage (kimpQ)
   - Portfolio rebalancing
   - Risk distribution

**What Belongs Here:**
- Trading strategy logic
- Order execution mechanisms
- Risk management rules
- Position tracking
- Performance calculations
- Trade lifecycle management

**What Belongs Elsewhere:**
- API integration details → `04_API/`
- Database storage → `06_Data/`
- UI display → `05_UI_UX/`
- Backtesting strategies → `08_Backtesting/`
- Process architecture → `02_Architecture/`

### Common Updates

**Adding New Strategy:**
1. Document strategy purpose and market conditions
2. Describe technical indicators used
3. Document buy/sell signal conditions
4. Specify risk management rules
5. Note position sizing approach
6. Create condition documentation file
7. Reference guideline compliance (BO, BOR, SO, SOR)

**Modifying Order Execution:**
1. Document execution logic changes
2. Update order lifecycle descriptions
3. Note API changes if affected
4. Update error handling documentation
5. Verify risk controls still apply

**Updating Risk Management:**
1. Document rule changes with rationale
2. Update position sizing formulas
3. Note impact on existing strategies
4. Update setting.py references
5. Test risk controls with examples

**Enhancing Performance Tracking:**
1. Document new metrics added
2. Update calculation formulas
3. Note database schema changes
4. Update tradelist.db references
5. Provide interpretation guidelines

## Dependencies

**Related Manual Sections:**
- `02_Architecture/` - Trading process architecture
- `03_Modules/stock_module.md` - Stock trading implementation
- `03_Modules/coin_module.md` - Crypto trading implementation
- `04_API/` - Exchange API integration for orders
- `06_Data/` - Trade data storage (tradelist.db, strategy.db)
- `08_Backtesting/` - Strategy testing before live deployment

**Source Code References:**
- `stock/kiwoom_strategy_tick.py` (42KB) - Stock tick strategy
- `stock/kiwoom_trader.py` (46KB) - Stock order execution
- `coin/*_strategy_*.py` - Cryptocurrency strategies
- `coin/*_trader.py` - Crypto order execution
- `stock/kiwoom_receiver_tick.py` - Real-time data reception
- `utility/setting.py` - Risk management configuration

**Condition Documentation:**
- `../Condition/Tick/` - Tick strategy conditions (72 files)
- `../Condition/Min/` - Minute strategy conditions (61 files)
- Condition files document BO, BOR, SO, SOR sections

**Documentation Network:**
- Parent: `../AGENTS.md` - Manual documentation standards
- Guidelines: `../../Guideline/Back_Testing_Guideline_*.md` - Strategy documentation standards
- Conditions: `../../Condition/` - Individual strategy specifications

## Special Considerations

### Template Method Pattern
**CRITICAL:** Strategy classes use Template Method pattern:

```python
# Base class defines algorithm structure
class BaseStrategy:
    def execute_trading_cycle(self):
        self.collect_data()
        self.calculate_indicators()  # Hook method
        self.generate_signals()      # Hook method
        self.execute_orders()

# Subclasses implement hook methods
class TickStrategy(BaseStrategy):
    def calculate_indicators(self):
        # Specific implementation

    def generate_signals(self):
        # Specific implementation
```

Document this pattern clearly with examples from actual code.

### Self-Referencing Indexing
Strategy code uses `self.vars[N]` for parameter access:
```python
# N-th variable access
현재가 = self.vars[0]
시가 = self.vars[1]
고가 = self.vars[2]
저가 = self.vars[3]
```

Document this indexing pattern and typical variable assignments.

### Korean Trading Terminology
**Preserve these terms:**
- 매수 (buy)
- 매도 (sell)
- 체결 (fill/execution)
- 잔고 (balance/position)
- 손익 (profit/loss)
- 현재가 (current price)

These are standard Korean trading terms, not typos.

### Risk Control Hierarchy
Document risk control precedence:
1. Account-level limits (total capital at risk)
2. Position-level limits (max position size)
3. Daily limits (max trades per day)
4. Strategy-level limits (per-strategy exposure)
5. Blacklist enforcement (prohibited symbols)

### Position Sizing Algorithms
Document position sizing approaches:
- Fixed lot size
- Percentage of capital
- Volatility-based (ATR)
- Kelly criterion
- Custom algorithms per strategy

Provide formulas and examples.

### Order Lifecycle States
Document order states and transitions:
1. **Created** - Order object instantiated
2. **Submitted** - Sent to exchange
3. **Accepted** - Exchange acknowledged
4. **Partially Filled** - Some quantity filled
5. **Filled** - Complete fill
6. **Cancelled** - Cancellation confirmed
7. **Rejected** - Exchange rejected
8. **Error** - Execution error occurred

Provide state transition diagram.

### Performance Metrics Calculations
Document metric formulas:

**Win Rate:**
```
Win Rate = (Number of Winning Trades) / (Total Trades) × 100%
```

**Profit Factor:**
```
Profit Factor = (Gross Profit) / (Gross Loss)
```

**Maximum Drawdown:**
```
Max DD = (Trough Value - Peak Value) / (Peak Value) × 100%
```

**Sharpe Ratio:**
```
Sharpe = (Average Return - Risk-Free Rate) / (Standard Deviation of Returns)
```

### Signal Generation Timing
Document signal generation timing:
- Tick strategies: Every tick update
- Minute strategies: On minute close
- Signal validity period
- Signal expiration handling

### Order Execution Strategies
Document execution approaches:
- Market orders (immediate execution)
- Limit orders (price improvement)
- Stop orders (risk management)
- Iceberg orders (large positions)
- TWAP/VWAP (algorithmic execution)

### Multi-Market Coordination
Document cross-market strategies:
- Kimchi premium arbitrage (Korea crypto vs. global)
- Portfolio rebalancing across markets
- Risk distribution strategies
- Capital allocation algorithms

### Error Handling
Document error recovery:
- Exchange API errors
- Network disconnections
- Insufficient funds
- Invalid orders
- Order rejection handling
- Automatic retry logic

### Trade Logging
Document logging to tradelist.db:
- Entry timestamp
- Exit timestamp
- Entry price
- Exit price
- Quantity
- Commission/fees
- Realized PnL
- Strategy identifier
- Market conditions

### Real-Time vs. Backtesting
Document differences:
- Live trading uses real-time data via receivers
- Backtesting uses historical data from databases
- Strategy code should be identical
- Risk controls may differ
- Performance metrics calculated same way

### Condition Documentation Compliance
**CRITICAL:** All strategies must have condition documentation:
- Located in `docs/Condition/Tick/` or `docs/Condition/Min/`
- Must follow template (BO, BOR, SO, SOR, OR, GAR sections)
- Currently 98.3% compliance rate (119/121 files)
- Update condition docs when strategy changes

### Testing Before Deployment
Document testing requirements:
1. Backtest strategy thoroughly
2. Validate risk controls
3. Test order execution in paper trading
4. Verify performance metrics accurate
5. Run with small position sizes first
6. Monitor closely during first live sessions

### Performance Monitoring
Document monitoring during live trading:
- Real-time PnL tracking
- Order fill rates
- Slippage monitoring
- Commission impact
- Strategy performance vs. expectations
- Risk metric tracking

### Parameter Optimization
Document parameter tuning process:
- Use backtesting module for optimization
- Grid search or genetic algorithm
- Walk-forward validation
- Out-of-sample testing
- Parameter stability analysis
- Overfitting prevention

Reference `08_Backtesting/` for optimization details.
