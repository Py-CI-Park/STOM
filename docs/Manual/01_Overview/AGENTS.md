<!-- Parent: ../AGENTS.md -->
# Project Overview Documentation

## Purpose

Entry point documentation for STOM (System Trading Optimization Manager) V1, providing high-level project introduction including scope, goals, major features, technical stack overview, and licensing information. This section serves as the gateway for understanding STOM's purpose, capabilities, and overall system characteristics.

## Key Files

- **project_overview.md** - Complete project introduction covering system purpose, key features, technical architecture summary, target markets (Korean stocks via Kiwoom, cryptocurrencies via Upbit/Binance), and project statistics

## For AI Agents

### Maintaining This Section

**When to Update:**
- Major feature additions or removals
- Changes to technical stack (core dependencies like PyQt5, TA-Lib, multiprocessing architecture)
- Project statistics updates (file counts, line counts, database counts)
- Market support changes (new exchanges, API integrations)
- Licensing or project scope modifications

**Update Guidelines:**
1. **Read Before Editing** - Always read `project_overview.md` before making changes
2. **Verify Statistics** - All project metrics must reflect actual codebase state
   - Python source file count (currently 157 files)
   - Total line count (~70,000+ lines)
   - Database count (15 SQLite databases)
   - Documentation file count (175+ markdown files)
3. **Preserve High-Level Nature** - Keep content introductory, avoid deep technical details
4. **Maintain Bilingual Context** - Preserve Korean terminology where appropriate
5. **Cross-Reference Accuracy** - Ensure links to other manual sections remain valid

**Verification Process:**
```bash
# Verify Python file count
find C:\System_Trading\STOM\STOM_V1 -name "*.py" -type f | wc -l

# Verify markdown documentation count
find C:\System_Trading\STOM\STOM_V1\docs -name "*.md" -type f | wc -l

# Check database files
ls C:\System_Trading\STOM\STOM_V1\_database\*.db
```

**Common Updates:**
- **Technical Stack Changes** - Update framework versions, new library integrations
- **Feature Announcements** - Add new trading modes, market support, optimization methods
- **Project Milestones** - Update completion percentages, documentation compliance rates
- **System Capabilities** - Reflect new backtesting features, strategy types, UI improvements

### Code-Documentation Alignment

**Key Source References:**
- `stom.py` - Main entry point and mode selection
- `utility/setting.py` - Database paths (15 databases listed)
- `pip_install_64.bat` - Dependency list and technical requirements
- `CLAUDE.md` (project root) - Master project statistics
- `utility/total_code_line.py` - Line count verification script

**Validation Checklist:**
- [ ] File counts match actual repository state
- [ ] Database list matches `_database/` directory
- [ ] Technical stack matches `pip_install_64.bat` requirements
- [ ] Market integrations match available API modules
- [ ] Command examples are executable and tested
- [ ] Cross-references to other sections are valid

### Content Structure

**Standard Sections in project_overview.md:**
1. **System Purpose** - What STOM does and why it exists
2. **Key Features** - Core capabilities (multiprocess, real-time trading, backtesting)
3. **Technical Architecture** - High-level overview (PyQt5, multiprocess, queues)
4. **Supported Markets** - Kiwoom (Korean stocks), Upbit, Binance (crypto)
5. **Project Statistics** - File counts, line counts, database counts
6. **Technology Stack** - Core frameworks and libraries
7. **Documentation Scope** - Overview of available documentation

**What Belongs Here:**
- High-level system description
- Major feature categories
- Technology choices and rationale
- Project scale and scope
- Entry-level understanding material

**What Belongs Elsewhere:**
- Detailed architecture → `02_Architecture/`
- Module-level details → `03_Modules/`
- API specifications → `04_API/`
- Database schemas → `06_Data/`
- Installation procedures → `09_Manual/`

## Dependencies

**Related Manual Sections:**
- `02_Architecture/` - Detailed system design referenced in overview
- `03_Modules/` - Module descriptions summarized in overview
- `04_API/` - Market integrations mentioned in overview
- `09_Manual/` - User-facing features introduced in overview

**Source Code References:**
- `stom.py` - Main entry point and system initialization
- `stom_stock.bat` / `stom_coin.bat` - Execution modes
- `utility/setting.py` - System configuration and database paths
- `pip_install_64.bat` - Complete dependency list

**Documentation Network:**
- Parent: `../AGENTS.md` - Manual documentation standards
- Project Root: `../../CLAUDE.md` - Master project context
- Learning: `../../learning/01-프로젝트-소개.md` - User-facing introduction (Korean)

**Cross-References:**
- All other manual sections link back to Overview for context
- README.md navigation starts with Overview section
- Overview provides roadmap to detailed documentation

## Special Considerations

### Korean Trading Context
- Preserve Korean market terminology (키움증권, 업비트, 바이낸스)
- Maintain bilingual context where appropriate
- Korean stock market specifics (Windows requirement for Kiwoom API)

### Statistics Maintenance
- Update project statistics during major code changes
- Coordinate with `utility/total_code_line.py` for line counts
- Verify database count against `_database/` directory
- Check documentation count with automated scripts

### Documentation Compliance
- Currently maintaining 98.3% condition documentation compliance
- Reference this metric in overview as quality indicator
- Update compliance percentage when validation cycles complete

### Version Information
- Keep verification dates current (format: YYYY-MM-DD)
- Note major system version changes (currently STOM V1)
- Track documentation revision history in README.md
