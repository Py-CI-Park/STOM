<!-- Parent: ../AGENTS.md -->
# API Integration Documentation

## Purpose

Complete API integration patterns and specifications for all supported trading platforms in STOM V1. Documents authentication, connection management, data streaming protocols, order execution interfaces, and error handling for Kiwoom OpenAPI (Korean stocks), Upbit (Korean cryptocurrency), and Binance (global cryptocurrency) exchanges.

## Key Files

- **api_integration.md** - Comprehensive API integration documentation covering:
  - Kiwoom OpenAPI integration (Windows-only, ZMQ-based manager pattern)
  - Upbit REST API + WebSocket streaming
  - Binance REST API + WebSocket streaming
  - Authentication and credential management (Fernet encryption)
  - Connection lifecycle and error recovery
  - Rate limiting and API quota management
  - Data format standardization across exchanges

## For AI Agents

### Maintaining This Section

**When to Update:**
- New exchange integrations added
- API version upgrades (Kiwoom, Upbit, Binance)
- Authentication methods change
- WebSocket protocol updates
- Rate limiting rules modified
- Error handling strategies improved
- API endpoint changes or deprecations

**Critical Validation Points:**

1. **API Credentials Management** - Verify encryption and storage:
   ```python
   # utility/setting.py - Encrypted credential storage
   from cryptography.fernet import Fernet

   # Credential types documented:
   - Kiwoom: Account number, password, cert password
   - Upbit: Access key, secret key
   - Binance: API key, secret key
   ```

2. **Connection Patterns** - Confirm against actual implementation:
   ```python
   # Kiwoom (ZMQ-based)
   stock/kiwoom_manager.py - ZeroMQ pub/sub pattern

   # Upbit (WebSocket)
   coin/upbit_receiver_*.py - WebSocket streaming

   # Binance (WebSocket)
   coin/binance_receiver_*.py - WebSocket streaming
   ```

3. **API Endpoints** - Verify URLs and versions:
   - Kiwoom: Local OpenAPI installation (C:/OpenAPI)
   - Upbit: https://api.upbit.com/v1/
   - Binance: https://api.binance.com/api/v3/

**Update Guidelines:**
1. **Read Before Editing** - Always read `api_integration.md` completely
2. **Test Connections** - Verify API examples work with current versions
3. **Document Rate Limits** - Keep rate limiting rules current
4. **Verify Endpoints** - Test all documented API endpoints
5. **Check Error Codes** - Update error handling based on latest API docs

### Code-Documentation Alignment

**Key Source References:**

**Kiwoom OpenAPI Integration:**
```python
stock/kiwoom_manager.py - ZMQ-based manager process
stock/kiwoom_receiver_tick.py - Real-time data via OpenAPI
stock/kiwoom_trader.py - Order execution methods

# Authentication (Windows registry or config file)
# Connection via ZeroMQ for multiprocess architecture
# Event-driven callbacks from OpenAPI
```

**Upbit Integration:**
```python
coin/upbit_receiver_tick.py - WebSocket streaming
coin/upbit_receiver_min.py - Minute data aggregation
coin/upbit_trader.py - REST API order execution

# WebSocket: wss://api.upbit.com/websocket/v1
# REST API: https://api.upbit.com/v1/
# Authentication: JWT token with API keys
```

**Binance Integration:**
```python
coin/binance_receiver_tick.py - WebSocket streaming
coin/binance_receiver_min.py - Minute data aggregation
coin/binance_trader.py - REST API order execution

# WebSocket: wss://stream.binance.com:9443/ws
# REST API: https://api.binance.com/api/v3/
# Authentication: HMAC SHA256 signatures
```

**Credential Management:**
```python
utility/setting.py - Encrypted storage with Fernet
utility/static.py - Encryption/decryption helpers

# Database: setting.db - 암호화된 credential 저장
```

**Validation Checklist:**
- [ ] API versions match documented versions
- [ ] Endpoint URLs are current
- [ ] Authentication methods verified
- [ ] WebSocket URLs correct
- [ ] Rate limits documented accurately
- [ ] Error codes match current API specs
- [ ] Code examples are executable

### Content Structure

**Standard Sections in api_integration.md:**
1. **Overview** - Supported exchanges and integration approach
2. **Kiwoom OpenAPI** - Korean stock market integration
   - Windows installation requirements
   - ZMQ manager pattern
   - Event-driven architecture
   - Account authentication
3. **Upbit API** - Korean cryptocurrency exchange
   - REST API authentication (JWT)
   - WebSocket real-time streaming
   - Order management endpoints
   - Rate limiting (requests per second)
4. **Binance API** - Global cryptocurrency exchange
   - REST API authentication (HMAC)
   - WebSocket market data streams
   - Order execution and management
   - Weight-based rate limiting
5. **Common Patterns** - Shared integration approaches
   - Credential encryption (Fernet)
   - Connection pooling and retry logic
   - Error handling strategies
   - Data format standardization
6. **Testing and Validation** - API integration testing

**What Belongs Here:**
- API endpoint documentation
- Authentication mechanisms
- Connection lifecycle management
- Request/response formats
- Error handling patterns
- Rate limiting strategies
- WebSocket protocol details

**What Belongs Elsewhere:**
- Trading strategy logic → `07_Trading/`
- Data storage → `06_Data/`
- UI for API interactions → `05_UI_UX/`
- Module implementation → `03_Modules/`

### Common Updates

**Adding New Exchange:**
1. Document API version and base URLs
2. Describe authentication mechanism
3. Document rate limiting rules
4. Add WebSocket connection details
5. Document order execution endpoints
6. Provide code examples
7. Add error handling patterns

**Updating API Version:**
1. Note version change and deprecations
2. Update endpoint URLs if changed
3. Document new features or changes
4. Update authentication if modified
5. Revise rate limits if changed
6. Test all documented examples
7. Update error code mappings

**Modifying Authentication:**
1. Document new credential requirements
2. Update encryption/storage patterns
3. Revise code examples
4. Test authentication flow
5. Update troubleshooting section

## Dependencies

**Related Manual Sections:**
- `03_Modules/stock_module.md` - Kiwoom integration implementation
- `03_Modules/coin_module.md` - Upbit/Binance implementation details
- `06_Data/` - API credential storage in setting.db
- `07_Trading/` - Order execution using APIs

**Source Code References:**
- `stock/kiwoom_manager.py` - Kiwoom OpenAPI integration
- `coin/upbit_receiver_*.py` - Upbit WebSocket/REST
- `coin/binance_receiver_*.py` - Binance WebSocket/REST
- `coin/*_trader.py` - Order execution via APIs
- `utility/setting.py` - Credential encryption and storage
- `utility/static.py` - Crypto helper functions

**External Documentation:**
- Kiwoom OpenAPI: Official Windows documentation (Korean)
- Upbit API: https://docs.upbit.com/
- Binance API: https://binance-docs.github.io/apidocs/

**Documentation Network:**
- Parent: `../AGENTS.md` - Manual documentation standards
- Architecture: `../02_Architecture/system_architecture.md` - API integration in architecture
- Modules: `../03_Modules/` - Implementation details

## Special Considerations

### Windows Requirement for Kiwoom
**CRITICAL:** Kiwoom OpenAPI only works on Windows:
- Requires installation in `C:/OpenAPI`
- ActiveX control integration
- Windows registry for configuration
- Cannot run on Linux/Mac

Document this prominently in Kiwoom section.

### API Key Security
**CRITICAL:** Never commit API keys to version control:
- All credentials encrypted with Fernet in setting.db
- Database excluded from git (in `_database/`)
- Document encryption process clearly
- Provide key rotation procedures

### Rate Limiting Strategies
Each exchange has different rate limiting:

**Upbit:**
- Requests per second limits
- WebSocket connection limits
- Order placement quotas

**Binance:**
- Weight-based system
- Order rate limits
- IP-based restrictions

Document rate limit handling strategies:
- Request queuing
- Exponential backoff
- Connection pooling
- Error recovery

### WebSocket Reliability
Document WebSocket best practices:
- Automatic reconnection on disconnect
- Heartbeat/ping-pong mechanisms
- Message queue buffering
- Connection state monitoring
- Error recovery procedures

### Authentication Testing
Provide testing procedures:
```python
# Test Kiwoom connection
python -c "from stock.kiwoom_manager import *; test_connection()"

# Test Upbit authentication
python -c "from coin.upbit_trader import *; test_auth()"

# Test Binance authentication
python -c "from coin.binance_trader import *; test_auth()"
```

### API Version Tracking
Maintain version history:
- Document current API versions in use
- Track API version upgrade history
- Note breaking changes between versions
- Provide migration guides for upgrades

### Error Code Documentation
Maintain comprehensive error code tables:
- HTTP status codes
- Exchange-specific error codes
- WebSocket error codes
- Recovery strategies for each error type

### Data Format Standardization
Document how STOM standardizes data across exchanges:
- Common price/volume representation
- Timestamp normalization (UTC vs. local)
- Order status mapping
- Currency pair notation

### Credential Rotation
Document credential rotation procedures:
1. Generate new API keys on exchange
2. Update encrypted storage in setting.db
3. Test new credentials
4. Revoke old credentials
5. Update documentation

### Troubleshooting Section
Maintain common issues and solutions:
- Connection timeouts
- Authentication failures
- Rate limiting errors
- WebSocket disconnections
- Order execution failures

### Cross-Exchange Compatibility
Document how STOM abstracts differences:
- Unified order interface
- Common data structures
- Consistent error handling
- Standardized market data formats

This enables strategy code to work across exchanges with minimal changes.
