# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

STOM (System Trading Optimization Manager) V1 is a professional-grade high-frequency trading system for Korean stock markets (via Kiwoom Securities) and cryptocurrency markets (Upbit, Binance). It's a multi-process, real-time trading platform with comprehensive backtesting capabilities built with PyQt5.

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
- **Main Process**: PyQt5 GUI (`ui/ui_mainwindow.py`)
- **Data Receivers**: Real-time market data collection (`*_receiver_*.py`)
- **Strategy Engines**: Trading signal generation (`*_strategy_*.py`)
- **Traders**: Order execution and management (`*_trader.py`)
- **Backtesting**: Historical analysis and optimization (`backtester/`)

**Key Modules:**
- `/stock/` - Korean stock market trading via Kiwoom API
- `/coin/` - Cryptocurrency trading (Upbit, Binance)
- `/backtester/` - Historical testing and optimization
- `/ui/` - PyQt5 user interface components
- `/utility/` - Shared functionality and database management

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
- `*_receiver_*.py` - Real-time data collection
- `*_strategy_*.py` - Trading logic and signals
- `*_trader.py` - Order execution
- `backengine_*.py` - Market-specific backtesting
- `ui_*.py` - Interface components and event handlers
- `set_*.py` - UI component setup

### Key Classes & Patterns
- **Strategy Pattern**: Each market has dedicated strategy engines
- **Observer Pattern**: Real-time data updates via queues/WebSocket
- **Factory Pattern**: Market-specific engines (Kiwoom, Upbit, Binance)
- **Singleton Pattern**: Configuration and database managers

### Inter-Process Communication
- Python multiprocessing queues for data flow
- ZeroMQ for high-performance messaging
- WebSocket connections for real-time market data
- SQLite for persistent storage and cross-process data sharing

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

## Common Development Tasks

### Adding New Trading Strategies
1. Create strategy file in appropriate market directory (`stock/` or `coin/`)
2. Follow naming pattern: `{market}_strategy_{timeframe}.py`
3. Implement strategy logic using existing technical indicators
4. Add strategy to database via UI or direct SQL insertion
5. Test with backtesting engine before live deployment

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