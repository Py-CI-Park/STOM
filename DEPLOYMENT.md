# STOM Web Interface Deployment Guide

## Overview

This guide covers deploying the STOM Trading System with its new web interface. The system consists of:

- **FastAPI Backend**: REST API and WebSocket server
- **Web Frontend**: HTML/CSS/JavaScript interface
- **CLI Interface**: Command-line automation tools
- **Background Services**: Data processing and trading engines
- **SQLite Databases**: Existing database structure preserved

## Prerequisites

### System Requirements

- **Operating System**: Windows 10/11 (for Kiwoom API) or Linux/macOS (crypto only)
- **Python**: 3.8 or higher (64-bit recommended)
- **Memory**: Minimum 8GB RAM, 16GB recommended
- **Storage**: 10GB free space for databases and logs
- **Network**: Stable internet connection for market data

### Dependencies

Install Python dependencies:

```bash
cd web_app
pip install -r requirements.txt
```

### Additional Requirements for Full Trading

- **Kiwoom Securities API**: For Korean stock trading (Windows only)
- **Exchange API Keys**: Upbit, Binance accounts for cryptocurrency trading
- **Telegram Bot** (optional): For notifications

## Installation

### 1. Environment Setup

Create environment configuration file:

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

Example `.env` file:

```bash
# Server Configuration
STOM_HOST=127.0.0.1
STOM_PORT=8000
STOM_DEBUG=false
STOM_ENVIRONMENT=production

# Security
STOM_SECRET_KEY=your-super-secret-key-here
STOM_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
STOM_DATABASE_PATH=./_database

# Trading
STOM_ENABLE_LIVE_TRADING=false
STOM_ENABLE_PAPER_TRADING=true
STOM_MAX_POSITION_SIZE=1000000
STOM_MAX_DAILY_LOSS=100000

# External APIs
STOM_KIWOOM_ENABLED=false
STOM_UPBIT_ENABLED=false
STOM_BINANCE_ENABLED=false

# Logging
STOM_LOG_LEVEL=INFO
STOM_LOG_FILE=logs/stom.log
```

### 2. Database Setup

Initialize the database structure:

```bash
# Ensure database directory exists
mkdir -p _database

# Initialize databases (if not already present)
python -c "
from web_app.database.db_manager import DatabaseManager
import asyncio

async def init_db():
    db = DatabaseManager()
    await db.initialize()
    print('Database initialized')
    await db.close()

asyncio.run(init_db())
"
```

### 3. User Setup

Create initial admin user:

```bash
python -c "
from web_app.core.security import auth_manager

# Create admin user
user = auth_manager.create_user(
    username='admin',
    password='your-secure-password',
    role='admin',
    permissions=['all']
)
print(f'Admin user created: {user}')
"
```

## Running the System

### Development Mode

For development and testing:

```bash
# Start web server with auto-reload
python web_app/main.py

# Or using uvicorn directly
uvicorn web_app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Production Mode

For production deployment:

```bash
# Start web server
STOM_ENVIRONMENT=production python web_app/main.py

# Or using uvicorn with production settings
uvicorn web_app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### CLI Mode

For automation and batch processing:

```bash
# Interactive CLI
python web_app/main.py --cli

# Direct commands
python web_app/main.py --cli status
python web_app/main.py --cli positions
python web_app/main.py --cli place_order BTCUSDT buy market 0.1
```

## Service Management

### Windows Service (Recommended for Production)

Create Windows service using `nssm`:

1. Download NSSM from https://nssm.cc/
2. Install service:

```cmd
nssm install STOM
nssm set STOM Application "C:\Python\python.exe"
nssm set STOM AppParameters "C:\STOM\web_app\main.py"
nssm set STOM AppDirectory "C:\STOM"
nssm set STOM DisplayName "STOM Trading System"
nssm set STOM Description "Professional Trading System"
nssm start STOM
```

### Linux SystemD Service

Create systemd service file `/etc/systemd/system/stom.service`:

```ini
[Unit]
Description=STOM Trading System
After=network.target

[Service]
Type=simple
User=stom
WorkingDirectory=/opt/stom
Environment=PATH=/opt/stom/venv/bin
ExecStart=/opt/stom/venv/bin/python web_app/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable stom
sudo systemctl start stom
sudo systemctl status stom
```

## Configuration

### Trading Configuration

Configure trading settings through web interface or database:

```python
# Example: Enable paper trading
from web_app.database.db_manager import DatabaseManager
import asyncio

async def configure_trading():
    db = DatabaseManager()
    await db.initialize()
    
    # Enable paper trading
    await db.update_setting('main', '0', '실전거래', False)
    await db.update_setting('main', '0', '거래활성화', True)
    
    print('Trading configuration updated')
    await db.close()

asyncio.run(configure_trading())
```

### Market Data Sources

Configure market data connections:

1. **Stock Data (Kiwoom)**:
   - Install Kiwoom OpenAPI
   - Configure login credentials
   - Enable stock receiver

2. **Cryptocurrency Data**:
   - Configure exchange API keys
   - Enable coin receivers
   - Set trading pairs

### Security Configuration

1. **Change Default Passwords**:
   ```python
   from web_app.core.security import auth_manager
   
   # Update admin password
   auth_manager.update_user('admin', {'password': 'new-secure-password'})
   ```

2. **Configure API Keys**:
   ```python
   from web_app.core.security import api_key_auth
   
   # Create API key for automation
   api_key = api_key_auth.create_api_key('automation', ['all'])
   print(f'API Key: {api_key}')
   ```

3. **SSL/HTTPS Setup** (Production):
   ```bash
   # Using nginx as reverse proxy
   sudo apt install nginx
   
   # Configure nginx with SSL certificate
   # Example nginx configuration provided below
   ```

## Monitoring and Maintenance

### Health Checks

Monitor system health:

```bash
# Check system status
curl http://localhost:8000/health

# Check trading status
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/trading/system/status
```

### Log Management

Logs are written to:
- **Application logs**: `logs/stom.log`
- **Access logs**: `logs/access.log`
- **Error logs**: `logs/error.log`

Configure log rotation:

```bash
# Linux logrotate configuration
sudo cat > /etc/logrotate.d/stom << EOF
/opt/stom/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 stom stom
    postrotate
        systemctl reload stom
    endscript
}
EOF
```

### Database Maintenance

Regular maintenance tasks:

```bash
# Backup databases
python -c "
from web_app.database.db_manager import DatabaseManager
import asyncio

async def backup():
    db = DatabaseManager()
    await db.initialize()
    
    for db_name in db.databases:
        backup_path = f'backup/{db_name}_{datetime.now().strftime(\"%Y%m%d\")}.db'
        await db.backup_database(db_name, backup_path)
        print(f'Backed up {db_name}')
    
    await db.close()

asyncio.run(backup())
"

# Optimize databases
python -c "
from web_app.database.db_manager import DatabaseManager
import asyncio

async def optimize():
    db = DatabaseManager()
    await db.initialize()
    
    for db_name in db.databases:
        await db.optimize_database(db_name)
        print(f'Optimized {db_name}')
    
    await db.close()

asyncio.run(optimize())
"
```

## Reverse Proxy Setup (Production)

### Nginx Configuration

Example `/etc/nginx/sites-available/stom`:

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static {
        alias /opt/stom/web_app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   # Find process using port
   netstat -tulpn | grep :8000
   
   # Kill process if needed
   sudo kill -9 PID
   ```

2. **Database Lock Errors**:
   ```bash
   # Check for orphaned connections
   lsof | grep .db
   
   # Restart application
   sudo systemctl restart stom
   ```

3. **WebSocket Connection Issues**:
   - Check firewall settings
   - Verify proxy configuration
   - Check browser console for errors

4. **Authentication Failures**:
   ```bash
   # Reset admin password
   python -c "
   from web_app.core.security import auth_manager
   auth_manager.update_user('admin', {'password': 'newpassword'})
   print('Password reset')
   "
   ```

### Performance Tuning

1. **Database Optimization**:
   - Regular VACUUM operations
   - Index optimization
   - Archive old data

2. **Memory Management**:
   - Monitor memory usage
   - Adjust process limits
   - Configure swap if needed

3. **Network Optimization**:
   - Use WebSocket compression
   - Configure rate limiting
   - Implement caching

## Backup and Recovery

### Backup Strategy

1. **Daily Automated Backups**:
   ```bash
   #!/bin/bash
   # backup_stom.sh
   
   DATE=$(date +%Y%m%d)
   BACKUP_DIR="/backup/stom/$DATE"
   
   mkdir -p "$BACKUP_DIR"
   
   # Backup databases
   cp -r _database/ "$BACKUP_DIR/"
   
   # Backup configuration
   cp .env "$BACKUP_DIR/"
   
   # Backup logs (last 7 days)
   find logs/ -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;
   
   # Compress backup
   tar -czf "/backup/stom_$DATE.tar.gz" "$BACKUP_DIR"
   rm -rf "$BACKUP_DIR"
   
   # Remove old backups (keep 30 days)
   find /backup/ -name "stom_*.tar.gz" -mtime +30 -delete
   ```

2. **Schedule with Cron**:
   ```bash
   # Add to crontab
   0 2 * * * /opt/stom/backup_stom.sh
   ```

### Recovery Procedure

1. **Stop Services**:
   ```bash
   sudo systemctl stop stom
   ```

2. **Restore Databases**:
   ```bash
   # Extract backup
   tar -xzf stom_backup.tar.gz
   
   # Restore databases
   cp -r backup/_database/ ./
   ```

3. **Restart Services**:
   ```bash
   sudo systemctl start stom
   ```

## Security Considerations

### Network Security

1. **Firewall Configuration**:
   ```bash
   # UFW example
   sudo ufw allow 22/tcp      # SSH
   sudo ufw allow 443/tcp     # HTTPS
   sudo ufw allow 80/tcp      # HTTP (redirect to HTTPS)
   sudo ufw deny 8000/tcp     # Block direct access to app
   sudo ufw enable
   ```

2. **VPN Access**: Consider VPN for admin access
3. **Fail2ban**: Configure for brute force protection

### Application Security

1. **Regular Updates**: Keep dependencies updated
2. **Secret Management**: Use environment variables
3. **API Rate Limiting**: Prevent abuse
4. **Input Validation**: Sanitize all inputs
5. **Audit Logging**: Log all trading activities

## Support and Maintenance

### Regular Maintenance Schedule

- **Daily**: Check logs, monitor performance
- **Weekly**: Database optimization, backup verification
- **Monthly**: Security updates, configuration review
- **Quarterly**: Full system audit, disaster recovery test

### Getting Help

1. **Check Logs**: Review application and system logs
2. **Health Endpoint**: Use `/health` for system status
3. **CLI Tools**: Use CLI commands for diagnostics
4. **Documentation**: Refer to API documentation at `/docs`

For additional support, refer to the project documentation or submit issues through the project repository.