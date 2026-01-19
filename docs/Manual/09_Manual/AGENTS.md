<!-- Parent: ../AGENTS.md -->
# User Manual Documentation

## Purpose

End-user documentation and operational guides for STOM V1, providing comprehensive instructions for installation, configuration, system startup, daily operations, troubleshooting, and best practices. This section serves as the primary reference for users operating the trading system.

## Key Files

- **user_manual.md** - Complete user manual covering:
  - Installation procedures (pip_install_64.bat and dependencies)
  - System startup and execution (stom.bat, stom_stock.bat, stom_coin.bat)
  - Configuration management (setting.db and UI configuration)
  - Daily operational workflows
  - Troubleshooting common issues
  - Best practices and safety guidelines
  - Account setup and credential management

## For AI Agents

### Maintaining This Section

**When to Update:**
- Installation procedures change
- New dependencies added
- System requirements modified
- Startup procedures updated
- Configuration options added
- Common issues identified
- Best practices evolve
- User interface changes

**Critical Validation Points:**

1. **Installation Commands** - Verify all commands execute correctly:
   ```bash
   # Test installation script exists
   ls C:\System_Trading\STOM\STOM_V1\pip_install_64.bat

   # Verify Python 64-bit requirement documented
   python --version  # Must be 64-bit

   # Test database integrity check
   python C:\System_Trading\STOM\STOM_V1\utility\database_check.py
   ```

2. **Startup Scripts** - Confirm execution procedures:
   ```bash
   # Main startup options
   ls C:\System_Trading\STOM\STOM_V1\stom.bat
   ls C:\System_Trading\STOM\STOM_V1\stom_stock.bat
   ls C:\System_Trading\STOM\STOM_V1\stom_coin.bat

   # Verify administrator privileges requirement documented
   ```

3. **Configuration Files** - Validate configuration references:
   ```python
   # Setting database (encrypted credentials)
   _database/setting.db

   # Configuration management
   utility/setting.py - Global configuration access
   ```

4. **System Requirements** - Confirm requirements current:
   - Windows OS (for Kiwoom API)
   - Python 64-bit (for memory management)
   - Administrator privileges (for system operations)
   - Multi-monitor setup (recommended)

**Update Guidelines:**
1. **Read Before Editing** - Always read `user_manual.md` completely
2. **Test All Procedures** - Execute every documented procedure
3. **Verify Screenshots** - Update screenshots if UI changed
4. **Check File Paths** - Ensure all paths are correct
5. **Validate Commands** - Test all command examples

### Code-Documentation Alignment

**Key Source References:**

**Installation:**
```batch
pip_install_64.bat - Dependency installation script
- PyQt5 ecosystem
- Trading APIs (pyupbit, python-binance)
- Data processing (numpy, pandas)
- TA-Lib (custom wheel in utility/)
- Optimization (optuna, cmaes)
- Communication (websockets, pyzmq)
```

**Startup:**
```batch
stom.bat - Main application launcher with mode selection
stom_stock.bat - Stock trading mode
stom_coin.bat - Cryptocurrency trading mode

# Python direct execution alternative
python stom.py [stock|coin]
```

**Configuration:**
```python
utility/setting.py (42KB) - Configuration management
- Database paths (15 databases)
- Trading parameters
- API credentials (Fernet encrypted)
- Market-specific settings
- Blacklist management
```

**Database Management:**
```python
utility/database_check.py - Integrity verification
- Automatic startup checks
- Schema validation
- Data consistency verification
- Corruption detection
```

**Validation Checklist:**
- [ ] Installation commands tested and working
- [ ] Startup procedures verified
- [ ] Configuration examples accurate
- [ ] Troubleshooting steps effective
- [ ] System requirements current
- [ ] File paths correct
- [ ] Command examples executable

### Content Structure

**Standard Sections in user_manual.md:**
1. **System Requirements** - Hardware and software prerequisites
   - Windows OS (Kiwoom requirement)
   - Python 64-bit
   - Memory requirements (8GB+ recommended)
   - Multi-monitor setup (recommended)
   - Administrator privileges
2. **Installation** - Step-by-step setup
   - Python installation verification
   - Running pip_install_64.bat
   - TA-Lib installation
   - Kiwoom OpenAPI installation (C:/OpenAPI)
   - Database initialization
3. **Initial Configuration** - First-time setup
   - Setting database configuration
   - API credential entry (encrypted storage)
   - Account setup (Kiwoom, Upbit, Binance)
   - Risk management parameters
   - Trading strategy selection
4. **System Startup** - Launching the application
   - Using stom.bat (mode selection)
   - Using stom_stock.bat (stock only)
   - Using stom_coin.bat (crypto only)
   - Startup checks and verification
   - Process initialization monitoring
5. **Daily Operations** - Regular usage workflows
   - Pre-market preparation
   - Market hours monitoring
   - Strategy execution oversight
   - Performance tracking
   - End-of-day procedures
6. **Trading Workflows** - Operational procedures
   - Strategy activation
   - Position monitoring
   - Manual intervention
   - Risk management monitoring
   - Performance review
7. **Configuration Management** - Settings and parameters
   - Accessing settings via UI
   - Modifying trading parameters
   - API credential updates
   - Blacklist management
   - Strategy parameter tuning
8. **Troubleshooting** - Common issues and solutions
   - Installation problems
   - Connection failures
   - Database issues
   - Trading execution errors
   - Performance problems
9. **Best Practices** - Operational guidelines
   - Risk management rules
   - Position sizing guidelines
   - Strategy selection criteria
   - Monitoring procedures
   - Backup procedures
10. **Safety Guidelines** - Critical operational rules
    - Never trade without testing
    - Start with small positions
    - Monitor closely initially
    - Understand risk controls
    - Maintain adequate capital buffer

**What Belongs Here:**
- Installation instructions
- Configuration procedures
- Daily operational workflows
- Troubleshooting guides
- User-facing best practices
- Safety and risk guidelines

**What Belongs Elsewhere:**
- Technical architecture → `02_Architecture/`
- API integration details → `04_API/`
- Database schema → `06_Data/`
- Trading logic → `07_Trading/`
- Backtesting procedures → `08_Backtesting/`

### Common Updates

**Updating Installation Procedures:**
1. Test new installation steps thoroughly
2. Document any new dependencies
3. Update pip_install_64.bat if changed
4. Verify system requirements still accurate
5. Test on clean Windows installation if possible

**Modifying Startup Procedures:**
1. Test new startup flow
2. Update batch file documentation
3. Document any new command-line arguments
4. Verify administrator privilege requirements
5. Update process initialization descriptions

**Adding Configuration Options:**
1. Document new setting location (UI or setting.db)
2. Explain purpose and impact
3. Provide recommended values
4. Note any dependencies or side effects
5. Update configuration examples

**Expanding Troubleshooting:**
1. Document problem symptoms
2. Explain root cause
3. Provide step-by-step solution
4. Include prevention advice
5. Reference related documentation sections

## Dependencies

**Related Manual Sections:**
- `01_Overview/` - System introduction for new users
- `02_Architecture/` - Technical context for advanced users
- `06_Data/` - Database management for troubleshooting
- `07_Trading/` - Trading operations reference
- `08_Backtesting/` - Strategy testing before live use

**Source Code References:**
- `pip_install_64.bat` - Installation script
- `stom.py` - Main entry point
- `stom.bat`, `stom_stock.bat`, `stom_coin.bat` - Startup scripts
- `utility/setting.py` - Configuration management
- `utility/database_check.py` - Database integrity verification
- `utility/static.py` - Helper functions

**External Documentation:**
- Kiwoom OpenAPI installation guide
- Upbit API documentation
- Binance API documentation
- PyQt5 documentation (for UI understanding)

**Learning Resources:**
- `../../learning/` - Korean learning guides (13 files)
  - Mirror user manual structure
  - Provide additional Korean language support
  - Include practical examples

**Documentation Network:**
- Parent: `../AGENTS.md` - Manual documentation standards
- Learning: `../../learning/` - Korean operational guides
- Conditions: `../../Condition/` - Strategy documentation
- Guidelines: `../../Guideline/` - Technical specifications

## Special Considerations

### Windows-Only Requirement
**CRITICAL:** System requires Windows for Kiwoom API:
- Kiwoom OpenAPI only available for Windows
- Must install in C:/OpenAPI directory
- ActiveX controls require Windows
- Cannot run on Linux or Mac

Prominently document this limitation.

### Administrator Privileges
**CRITICAL:** Many operations require administrator access:
- Batch files request elevation
- System resource access
- Kiwoom API integration
- Database operations

Document privilege requirements clearly.

### 64-bit Python Requirement
**CRITICAL:** Must use Python 64-bit:
- Required for memory management
- Large dataset handling
- Multiprocess architecture
- TA-Lib integration

Document verification: `python --version` should indicate 64-bit.

### Credential Security
**CRITICAL:** API credentials encrypted with Fernet:
- Never share setting.db file
- Backup encryption key separately
- Use strong passwords
- Rotate credentials periodically
- Never commit credentials to version control

Emphasize security best practices.

### Initial Capital Requirements
Document capital requirements:
- Minimum account balance for trading
- Reserve for risk management
- Commission and fee considerations
- Market-specific requirements

Provide realistic capital guidelines.

### Testing Before Live Trading
**CRITICAL:** Always test before live deployment:
1. Backtest strategy thoroughly
2. Paper trade with virtual funds
3. Start with minimal position sizes
4. Monitor closely for first sessions
5. Verify risk controls working
6. Gradually increase position sizes

Document testing workflow explicitly.

### Korean Language Support
- UI displays Korean text extensively
- Many Korean trading terms used
- Configuration may have Korean labels
- Error messages may be in Korean

Provide glossary of common Korean terms.

### Multi-Monitor Recommendations
Document multi-monitor setup:
- Main trading window placement
- Chart monitor organization
- Order book displays
- Performance monitoring windows
- Information density optimization

### Backup Procedures
Document backup strategies:
1. Database backups (setting.db especially)
2. Configuration backups
3. Strategy condition files
4. Trading logs
5. Backup frequency recommendations

### Database Integrity Checks
Document automatic checks:
- Runs at startup (database_check.py)
- Schema validation
- Data consistency verification
- Automatic repair attempts
- Manual recovery procedures

### Troubleshooting Section Organization
Organize by symptom:
1. Installation issues
2. Connection problems
3. Trading execution errors
4. Performance issues
5. Database problems
6. UI issues

Each issue includes:
- **Symptoms** - What user sees
- **Cause** - Why it happens
- **Solution** - Step-by-step fix
- **Prevention** - How to avoid

### Error Messages
Document common error messages:
- Korean and English versions
- Meaning and interpretation
- Resolution steps
- When to seek help

### Log File Locations
Document logging:
- `_log/` directory structure
- Log file naming patterns
- What each log contains
- Log retention period
- Using logs for troubleshooting

### Performance Monitoring
Document monitoring during operation:
- Real-time PnL tracking
- Order fill monitoring
- Strategy performance
- System resource usage
- Network connectivity
- API connection status

### Daily Operational Checklist
Provide daily checklist:
**Before Market Open:**
- [ ] System startup successful
- [ ] Database integrity verified
- [ ] API connections established
- [ ] Strategies loaded correctly
- [ ] Risk parameters set
- [ ] Capital adequacy verified

**During Market Hours:**
- [ ] Monitor positions actively
- [ ] Check strategy performance
- [ ] Verify order executions
- [ ] Watch risk metrics
- [ ] Respond to alerts

**After Market Close:**
- [ ] Review day's performance
- [ ] Export trade logs
- [ ] Backup databases
- [ ] Update blacklists if needed
- [ ] Plan next day's strategies

### Contact and Support
Document support resources:
- Where to report issues
- How to request features
- Documentation feedback
- Community resources
- Emergency procedures

### Version Information
Document version tracking:
- Current system version (V1)
- Version history
- Upgrade procedures
- Backward compatibility
- Migration guides

### Regulatory Compliance
Document compliance considerations:
- Tax reporting requirements
- Trade record retention
- Regulatory reporting
- Licensing requirements
- Regional restrictions

### Learning Path for New Users
Suggest learning progression:
1. Read Overview documentation
2. Complete installation
3. Configure system with paper trading
4. Read Trading Engine docs
5. Study example strategies
6. Run backtests
7. Paper trade for practice
8. Start with minimal live positions
9. Gradually increase based on experience

Reference learning guides in `../../learning/` directory.
