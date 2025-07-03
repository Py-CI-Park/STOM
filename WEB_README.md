# STOM Trading System - Web Interface

🚀 **Professional-grade high-frequency trading system with modern web interface**

This is the web-based version of the STOM (System Trading Optimization Manager) trading system, providing a modern REST API, real-time WebSocket communication, and browser-based interface while preserving all the powerful features of the original PyQt5 application.

## 🌟 Features

### 🖥️ **Modern Web Interface**
- Real-time trading dashboard with live data
- Interactive charts and market data visualization
- Responsive design for desktop and mobile
- WebSocket-powered real-time updates

### 🔧 **Powerful API**
- RESTful API for all trading operations
- WebSocket API for real-time data streaming
- JWT-based authentication and authorization
- Comprehensive API documentation with OpenAPI/Swagger

### 💻 **CLI Automation**
- Command-line interface for automation
- Batch processing capabilities
- Scriptable trading operations
- Perfect for algorithmic trading

### 📊 **Advanced Trading Features**
- Multi-market support (Korean stocks, cryptocurrencies)
- Real-time order management
- Position tracking and P&L monitoring
- Risk management and controls
- Strategy backtesting and optimization

### 🔐 **Enterprise Security**
- User authentication and role-based access
- API key management for automation
- Encrypted credential storage
- Session management and security headers

### 📈 **Data Management**
- Preserves existing SQLite database structure
- Real-time market data collection
- Historical data analysis
- Data export and import capabilities

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ (64-bit recommended)
- 8GB+ RAM (16GB recommended for live trading)
- Windows 10/11 (for Korean stock trading) or Linux/macOS (crypto only)

### Installation

1. **Install Dependencies**
   ```bash
   cd web_app
   pip install -r requirements.txt
   ```

2. **Start the System**
   ```bash
   # Simple start (development mode)
   python start_stom_web.py
   
   # Production mode
   python start_stom_web.py --production --host 0.0.0.0
   
   # CLI mode
   python start_stom_web.py --cli
   ```

3. **Access the Interface**
   - **Web Interface**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/health

### First Login

Default credentials:
- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Change the default password immediately in production!**

## 📖 Usage Examples

### Web Interface

1. **Login** to the web interface at http://localhost:8000
2. **Monitor** your portfolio on the dashboard
3. **Place orders** through the trading interface
4. **View positions** and order history
5. **Configure settings** for your trading preferences

### API Usage

```python
import requests

# Login and get token
response = requests.post('http://localhost:8000/api/auth/login-json', 
                        json={'username': 'admin', 'password': 'admin123'})
token = response.json()['access_token']

# Get portfolio summary
headers = {'Authorization': f'Bearer {token}'}
portfolio = requests.get('http://localhost:8000/api/trading/portfolio/summary', 
                        headers=headers)
print(portfolio.json())

# Place an order
order = requests.post('http://localhost:8000/api/trading/orders',
                     headers=headers,
                     json={
                         'symbol': 'BTCUSDT',
                         'side': 'buy',
                         'order_type': 'market',
                         'size': 0.1
                     })
print(order.json())
```

### CLI Usage

```bash
# Interactive mode
python start_stom_web.py --cli

# Direct commands
python start_stom_web.py --cli status
python start_stom_web.py --cli positions
python start_stom_web.py --cli place_order BTCUSDT buy market 0.1
python start_stom_web.py --cli export --type trades --output trades.csv

# Automation script
cat << 'EOF' > trading_script.sh
#!/bin/bash
# Daily trading automation

# Check system status
python start_stom_web.py --cli status

# Get current positions
python start_stom_web.py --cli positions

# Export trading data
python start_stom_web.py --cli export --type trades --output "trades_$(date +%Y%m%d).csv"
EOF

chmod +x trading_script.sh
./trading_script.sh
```

### WebSocket Connection

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Subscribe to market data
ws.onopen = () => {
    ws.send(JSON.stringify({
        type: 'subscribe',
        channels: ['market_data', 'positions', 'orders']
    }));
};

// Handle real-time data
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'channel_data') {
        console.log(`Update from ${data.channel}:`, data.data);
    }
};
```

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   CLI Client    │    │  API Client     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼───────────────┐
                    │      FastAPI Server        │
                    │   ┌─────────────────────┐   │
                    │   │   WebSocket Hub    │   │
                    │   └─────────────────────┘   │
                    └─────────────┬───────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
    ┌─────────▼──────────┐ ┌─────▼──────┐ ┌─────────▼─────────┐
    │  Trading Service   │ │  Process   │ │  Database Manager │
    │                    │ │  Manager   │ │                   │
    └─────────┬──────────┘ └─────┬──────┘ └──────────┬────────┘
              │                  │                   │
    ┌─────────▼──────────┐ ┌─────▼──────┐ ┌─────────▼─────────┐
    │  Market Data       │ │ Background │ │  SQLite           │
    │  Risk Management   │ │ Services   │ │  Databases        │
    │  Order Execution   │ │            │ │                   │
    └────────────────────┘ └────────────┘ └───────────────────┘
```

### Key Features

- **Multi-Process Architecture**: Background services for data processing
- **Real-time Communication**: WebSocket for live updates
- **Database Abstraction**: Async SQLite operations
- **Modular Design**: Clean separation of concerns
- **Scalable**: Easy to extend and modify

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
# Server Configuration
STOM_HOST=127.0.0.1
STOM_PORT=8000
STOM_DEBUG=false

# Security
STOM_SECRET_KEY=your-super-secret-key-here
STOM_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Trading
STOM_ENABLE_LIVE_TRADING=false
STOM_ENABLE_PAPER_TRADING=true
STOM_MAX_POSITION_SIZE=1000000
STOM_MAX_DAILY_LOSS=100000

# External APIs
STOM_KIWOOM_ENABLED=false
STOM_UPBIT_ENABLED=false
STOM_BINANCE_ENABLED=false
```

### Database Configuration

The system uses the existing SQLite database structure:

- `setting.db` - System configuration and encrypted credentials
- `tradelist.db` - Trading history and performance
- `strategy.db` - Trading strategies and parameters
- `backtest.db` - Backtesting results
- `stock_*.db` / `coin_*.db` - Market data (tick/minute)

## 🔐 Security

### Authentication

- **JWT Tokens**: Secure API access with expiring tokens
- **Role-based Access**: Admin, trader, and read-only roles
- **API Keys**: For automated systems and scripts
- **Session Management**: Secure session handling

### Best Practices

1. **Change Default Passwords**: Update admin credentials immediately
2. **Use HTTPS**: Configure SSL/TLS for production
3. **Firewall**: Restrict access to necessary ports only
4. **Regular Updates**: Keep dependencies updated
5. **Backup**: Regular database backups
6. **Monitor**: Log all trading activities

## 📊 API Reference

### Authentication Endpoints

- `POST /api/auth/login` - Login with credentials
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/refresh` - Refresh access token

### Trading Endpoints

- `GET /api/trading/positions` - Get current positions
- `GET /api/trading/orders` - Get order history
- `POST /api/trading/orders` - Place new order
- `DELETE /api/trading/orders/{id}` - Cancel order
- `GET /api/trading/portfolio/summary` - Portfolio overview

### Data Endpoints

- `GET /api/database/tables/{db_name}` - Database schema
- `POST /api/database/query/{db_name}` - Execute SQL query
- `GET /api/database/trading-data/{market}/{type}` - Market data

### Settings Endpoints

- `GET /api/settings/system` - System configuration
- `PUT /api/settings/system` - Update system settings
- `GET /api/settings/markets` - Market configuration

For complete API documentation, visit `/docs` when the server is running.

## 🔄 Migration from PyQt5 Version

The web interface preserves all functionality from the original PyQt5 application:

### ✅ **Preserved Features**
- All 16-process architecture (converted to background services)
- Complete database structure and data
- Trading algorithms and strategies
- Risk management systems
- Market data processing
- Backtesting and optimization

### 🚀 **New Features**
- Web-based interface accessible from anywhere
- REST API for integration with other systems
- CLI automation for algorithmic trading
- Real-time WebSocket communication
- Mobile-friendly responsive design
- Multi-user support with authentication

### 📋 **Migration Steps**

1. **Backup Existing Data**
   ```bash
   cp -r _database _database_backup
   ```

2. **Install Web Interface**
   ```bash
   cd web_app
   pip install -r requirements.txt
   ```

3. **Start Web System**
   ```bash
   python start_stom_web.py
   ```

4. **Verify Data Migration**
   - Check that all databases are accessible
   - Verify trading history is preserved
   - Test strategy configurations

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Use different port
   python start_stom_web.py --port 8080
   ```

2. **Database Locked**
   ```bash
   # Check for running processes
   ps aux | grep stom
   # Kill if necessary and restart
   ```

3. **Login Failed**
   ```bash
   # Reset admin password
   python -c "
   from web_app.core.security import auth_manager
   auth_manager.update_user('admin', {'password': 'newpassword'})
   "
   ```

4. **WebSocket Connection Failed**
   - Check browser console for errors
   - Verify firewall settings
   - Test with different browser

### Performance Tips

1. **Memory Optimization**
   - Monitor memory usage with system tools
   - Adjust database query limits
   - Consider data archiving for old records

2. **Network Optimization**
   - Use compression for WebSocket data
   - Implement caching for frequently accessed data
   - Consider CDN for static assets in production

## 🤝 Contributing

This web interface extends the original STOM system with modern capabilities while maintaining backward compatibility. Contributions are welcome!

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest web_app/tests/

# Code formatting
black web_app/
isort web_app/

# Type checking
mypy web_app/
```

## 📄 License

This project maintains the same license as the original STOM system. Please refer to the main project license file.

## 🆘 Support

- **Documentation**: Visit `/docs` for API documentation
- **Health Check**: Use `/health` endpoint for system status
- **Logs**: Check `logs/stom.log` for application logs
- **CLI Help**: Run `python start_stom_web.py --cli help`

---

**Happy Trading! 📈**