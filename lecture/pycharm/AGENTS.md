<!-- Parent: ../AGENTS.md -->
# PyCharm IDE Configuration

## Purpose
PyCharm IDE configuration files for the STOM trading system development environment. Provides standardized code style, color scheme, and project settings for consistent development experience across team members.

## Key Files

### Color Scheme
- **Darcula_copy.icls** - Custom Darcula-based color scheme for PyCharm editor
  - Optimized for long coding sessions with reduced eye strain
  - Syntax highlighting configured for Python trading code
  - Custom colors for Korean variable names and comments

### Code Style Configuration
- **Project_Default.xml** - Project-level code style settings
  - Python code formatting rules (PEP 8 compliance with project-specific adjustments)
  - Indentation, spacing, and line length configurations
  - Import statement ordering and grouping rules
  - Naming conventions for variables, functions, and classes

## For AI Agents

### Development Environment Setup
When setting up a new development environment or assisting with IDE configuration:

1. **Color Scheme Installation**
   - Import `Darcula_copy.icls` to PyCharm: File → Settings → Editor → Color Scheme → Import Scheme
   - Optimized for reading Korean variable names (현재가, 시가, 고가, 저가, etc.)
   - Provides clear visual distinction between code elements in multi-process architecture

2. **Code Style Application**
   - Import `Project_Default.xml` to PyCharm: File → Settings → Editor → Code Style → Import Scheme
   - Ensures consistent formatting across all Python modules (157 files)
   - Automatically enforces project conventions during code completion and refactoring

### Code Style Guidelines
The `Project_Default.xml` configuration enforces these patterns:

**Indentation**:
- 4 spaces per indentation level (standard Python)
- Continuation indent: 4 spaces
- Tab size: 4 spaces (spaces, not tabs)

**Line Length**:
- Maximum line length: 120 characters (STOM project standard)
- Allows for complex trading logic expressions without excessive line breaks

**Import Organization**:
```python
# Standard library imports
import os
import sys

# Third-party imports
import numpy as np
import pandas as pd

# Local application imports
from utility.setting import *
from utility.static import *
```

**Naming Conventions**:
- **Korean Variables**: Allowed and encouraged for domain-specific trading terms
- **Class Names**: PascalCase (e.g., `KiwoomStrategy`, `UpbitTrader`)
- **Function Names**: snake_case (e.g., `process_tick_data`, `calculate_indicators`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_POSITION_SIZE`, `TICK_INTERVAL`)
- **Private Members**: Leading underscore (e.g., `_internal_state`)

### IDE Features Optimization
The configuration files optimize PyCharm for:

**Multi-Process Development**:
- Debugger settings for multiple Python processes
- Console output formatting for queue-based communication logs
- Breakpoint configurations for multiprocessing.Process debugging

**Large Codebase Navigation**:
- Indexed search optimized for 157 Python files (~70,000 lines)
- Custom scopes for different modules (stock/, coin/, ui/, backtester/)
- Quick navigation between strategy files and their condition documents

**Database Integration**:
- SQLite database console settings for 15 databases
- Query result formatting for tick/minute data inspection
- Schema visualization preferences

### Consistency Guidelines
When modifying code or generating new files:

1. **Always Apply Code Style**: Use PyCharm's "Reformat Code" (Ctrl+Alt+L) before committing
2. **Preserve Korean Variables**: Do not translate domain-specific Korean variable names
3. **Follow Import Order**: Standard library → Third-party → Local application
4. **Respect Line Length**: Break complex expressions at 120 characters
5. **Use Type Hints**: For public APIs and function signatures (Python 3.7+ compatible)

### Custom IDE Behaviors
The configuration includes these project-specific customizations:

**File Templates**:
- Strategy file template with standard imports and class structure
- Condition document template with BO/BOR/SO/SOR sections
- Test file template for performance benchmarking

**Live Templates** (code snippets):
- `strat` → Strategy class boilerplate
- `recv` → Receiver class boilerplate
- `trad` → Trader class boilerplate
- `qput` → Queue put operation with error handling
- `dbq` → Database query via queryQ

**External Tools**:
- Database integrity checker: `python utility/database_check.py`
- Documentation validator: `python utility/validate_docs.py`
- Code line counter: `python utility/total_code_line.py`

## Dependencies

### PyCharm Version
- **Minimum**: PyCharm Professional 2020.3 or later
- **Recommended**: PyCharm Professional 2023.x or later
- **Community Edition**: Compatible, but lacks database tools integration

### Python Interpreter
- **Required**: Python 3.7+ (64-bit)
- **Recommended**: Python 3.9 or 3.10 for optimal performance
- **Virtual Environment**: Recommended for dependency isolation

### PyCharm Plugins
Recommended plugins for STOM development:
- **Python Security** - Detect security vulnerabilities in trading code
- **CSV Plugin** - View CSV data files in structured format
- **Markdown** - Edit documentation files with preview
- **.ignore** - Manage .gitignore for database files

## Installation Instructions

### First-Time Setup
1. Clone STOM repository
2. Open project in PyCharm
3. Import color scheme: Settings → Editor → Color Scheme → ⚙️ → Import Scheme → `Darcula_copy.icls`
4. Import code style: Settings → Editor → Code Style → ⚙️ → Import Scheme → `Project_Default.xml`
5. Configure Python interpreter: Settings → Project → Python Interpreter → Add → System Interpreter (64-bit)
6. Install dependencies: Run `pip_install_64.bat`
7. Verify setup: Run `python utility/database_check.py`

### Sharing Configuration
To share IDE settings with team members:
1. Export updated schemes from PyCharm settings
2. Update files in `lecture/pycharm/`
3. Commit changes with descriptive message
4. Notify team to re-import configurations

### Troubleshooting
**Korean Characters Display Issues**:
- Ensure console encoding is set to UTF-8: Settings → Editor → File Encodings
- Verify font supports Korean characters (e.g., Consolas, D2Coding)

**Code Style Not Applying**:
- Check that `Project_Default.xml` is set as active scheme
- Verify reformatting is enabled: Settings → Editor → Code Style → Python
- Clear IDE cache and restart: File → Invalidate Caches / Restart

**Import Organization Issues**:
- Ensure optimize imports uses project scheme: Settings → Editor → Code Style → Python → Imports
- Configure third-party library detection: Settings → Project Structure → Mark external libraries

## Maintenance
Update these configuration files when:
- Project coding standards change
- New code patterns emerge (e.g., async/await for WebSocket handling)
- Team preferences evolve
- PyCharm version upgrades introduce new features
- Korean variable naming conventions expand
