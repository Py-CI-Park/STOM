<!-- Parent: ../AGENTS.md -->
# Kiwoom API Authentication

## Purpose
Handles Kiwoom OpenAPI login and authentication management for Korean stock trading. This module automates the login process through Windows COM automation, supporting both automatic login configuration and version updates.

## Key Files

### `autologin1.py` (88 lines)
First account automatic login configuration script
- Initializes Kiwoom OpenAPI COM object (`KHOPENAPI.KHOpenAPICtrl.1`)
- Removes existing `Autologin.dat` file to ensure clean setup
- Spawns PyQt5 process for API connection
- Automates login form input using win32gui/win32api
- Configures automatic login for accounts 1, 3, 5, or 7
- Handles certificate expiration notifications via Telegram
- Uses `auto_on(1)` for account password configuration

### `autologin2.py` (88 lines)
Second account automatic login configuration script
- Identical structure to `autologin1.py` with different account mappings
- Configures automatic login for accounts 2, 4, 6, or 8
- Uses `auto_on(2)` for account password configuration
- Supports multi-account trading setups (up to 4 broker accounts)

### `manuallogin.py` (131 lines)
Windows automation utilities and manual login helper functions
- **Window management**: `find_window()`, `enum_windows()`
- **Input automation**: `leftClick()`, `doubleClick()`, `enter_keys()`, `press_keys()`
- **Login orchestration**: `manual_login(gubun)` - automates credential entry
- **Account setup**: `auto_on(gubun)` - configures account passwords and auto-login
- Uses win32api/win32gui for Windows message posting and control manipulation
- Supports toggle between real server and simulation server (commented code at lines 91-96)

### `versionupdater.py` (113 lines)
Kiwoom OpenAPI version update automation
- Monitors `opstarter` window for version update prompts
- Automates version upgrade process with button clicking
- Implements 90-second timeout for update completion
- Cleans up processes and windows after successful update
- Integrates with `manual_login()` for post-update re-authentication
- Handles certificate expiration notifications

## For AI Agents

### Critical Constraints
**Windows-Only Environment**
- Requires Windows OS with Kiwoom OpenAPI installed at `C:/OpenAPI`
- Dependencies: PyQt5, QAxWidget, win32api, win32gui, pythoncom
- COM object requirement: `KHOPENAPI.KHOpenAPICtrl.1` must be registered

**Security Considerations**
- Credentials stored in encrypted format via `utility/setting.py` (DICT_SET)
- Supports up to 8 account configurations (4 broker accounts × 2 accounts each)
- Certificate passwords and account passwords managed separately
- Telegram integration for security notifications (certificate expiration)

### Code Patterns
**Process-Based Architecture**
- Uses `multiprocessing.Process` for isolated PyQt5 execution
- Daemon processes for non-blocking operation
- COM pump messaging: `pythoncom.PumpWaitingMessages()` for event handling

**Window Automation Pattern**
```python
# Standard automation sequence
hwnd = find_window('Open API login')           # Locate window
control = win32gui.GetDlgItem(hwnd, 0x3E8)    # Get control handle
enter_keys(control, credentials)               # Input data
click_button(win32gui.GetDlgItem(hwnd, 0x1))  # Submit
```

**Settings Access Pattern**
```python
# Account selection based on broker configuration
if DICT_SET['증권사'] == '키움증권1':    # Broker 1
    manual_login(1)  # Account 1 (autologin1)
    manual_login(2)  # Account 2 (autologin2)
```

### Modification Guidelines

**Adding Account Support**
1. Update `DICT_SET` in `utility/setting.py` with new credentials
2. Add conditional branch in autologin scripts (lines 66-73)
3. Update `auto_on()` function in `manuallogin.py` (lines 111-130)

**Changing Server Mode (Real/Simulation)**
1. Locate commented section in `manuallogin.py` (lines 91-96)
2. Toggle enabled/disabled state of server mode button (0x3ED)
3. Test thoroughly - simulation server uses different data/orders

**Debugging Login Issues**
- Check `OPENAPI_PATH` in `utility/setting.py`
- Verify `Autologin.dat` deletion success
- Monitor window titles with `enum_windows()` for changes
- Use `time.sleep()` adjustments for timing-sensitive operations
- Check control IDs (0x3E8, 0x3E9, 0x3EA) if UI updated

**DO NOT**
- Remove `opstarter_kill()` calls - prevents zombie processes
- Modify credential access patterns - breaks encryption
- Skip `pythoncom.PumpWaitingMessages()` - causes COM hangs
- Remove certificate expiration handling - critical security alert

### Integration Points
- **Imports from utility/**: `setting.py` (credentials, paths), `static.py` (helpers)
- **Telegram notifications**: Uses token/ID from DICT_SET for alerts
- **Main application**: Called by stock trading initialization sequence
- **Database**: No direct access - authentication only

### Testing Considerations
- Requires active Kiwoom OpenAPI installation
- Cannot be unit tested without Windows environment
- Manual testing required for UI automation changes
- Certificate expiration testing requires expired cert environment
- Version update testing needs actual API version mismatch

## Dependencies

**External**
- **Kiwoom OpenAPI**: Must be installed at path specified in `OPENAPI_PATH`
- **Windows COM objects**: `KHOPENAPI.KHOpenAPICtrl.1`
- **Python libraries**: PyQt5, QAxContainer, pywin32 (win32api/win32gui), pythoncom

**Internal**
- `utility/setting.py`: OPENAPI_PATH, DICT_SET (credentials, broker config)
- `utility/static.py`: opstarter_kill(), now(), timedelta_sec()

**Configuration Requirements**
- `DICT_SET['증권사']`: Broker selection ('키움증권1' ~ '키움증권4')
- `DICT_SET['아이디{N}']`: Login IDs (N=1-8)
- `DICT_SET['비밀번호{N}']`: Passwords (N=1-8)
- `DICT_SET['인증서비밀번호{N}']`: Certificate passwords (N=1-8)
- `DICT_SET['계좌비밀번호{N}']`: Account passwords (N=1-8)
- `DICT_SET['텔레그램봇토큰{N}']`: Telegram bot tokens (N=1-4)
- `DICT_SET['텔레그램사용자아이디{N}']`: Telegram user IDs (N=1-4)
