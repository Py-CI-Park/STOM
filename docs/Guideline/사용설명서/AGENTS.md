<!-- Parent: ../AGENTS.md -->
# Korean User Manual (사용설명서)

## Purpose

This directory contains comprehensive Korean-language user manuals for the STOM trading system, designed for end-users operating the system in production. The manuals provide step-by-step guidance for system setup, configuration, trading operations, and troubleshooting.

**Target Audience**: Korean-speaking traders and system operators with minimal technical background

**Documentation Philosophy**:
- **Dual Format**: Each part has a detailed script version (스크립트) and a concise summary version (요약)
- **Progressive Learning**: Structured in 4 parts from basic setup to advanced troubleshooting
- **Screenshot-Driven**: Visual guides with keyboard shortcuts and UI navigation
- **Practical Focus**: Real-world usage scenarios and operational procedures

## Key Files

### Part 1: Getting Started (시작하기)

**21_스톰사용설명서 1부_스크립트.md** (37KB, ~900 lines)
- Initial installation and 32-bit vs 64-bit environment setup
- Encryption key management and credential storage
- Main window layout and tab structure
- Keyboard shortcuts (Alt-T, Alt-S, Alt-D, Alt-P, Alt-U, Alt-K, Alt-B, Alt-Q)
- Database management basics (Ctrl-B, Ctrl-P, Ctrl-A)

**21_스톰사용설명서 1부_요약.md** (12KB, ~95 lines)
- Condensed version covering installation, UI overview, and essential shortcuts
- Quick reference for experienced users

### Part 2: Basic Features (기본 기능)

**22_스톰사용설명서 2부_스크립트.md** (41KB, ~1,000 lines)
- Strategy configuration and trading condition setup
- Backtesting execution and result analysis
- Position management and trade history
- Real-time chart monitoring and factor display
- Simulator mode for testing without real orders

**22_스톰사용설명서 2부_요약.md** (13KB, ~110 lines)
- Quick guide to strategy setup, backtesting, and trade monitoring
- Essential operations for daily trading

### Part 3: Advanced Features (고급 기능)

**23_스톰사용설명서 3부_스크립트.md** (75KB, ~1,800 lines)
- Live trading activation and monitoring
- Multi-strategy coordination
- Performance optimization and queue management
- Risk management settings (position sizing, stop-loss)
- Telegram notifications and alert configuration
- Advanced charting and technical analysis tools

**23_스톰사용설명서 3부_요약.md** (11KB, ~100 lines)
- Concise guide to live trading, risk management, and monitoring tools
- Quick reference for experienced traders

### Part 4: Troubleshooting (문제 해결)

**24_스톰사용설명서 4부_스크립트.md** (9KB, ~200 lines)
- Common issues and solutions
- Database integrity checks and repair procedures
- API connection troubleshooting (Kiwoom, Upbit, Binance)
- Performance diagnostics and optimization
- Error log analysis

**24_스톰사용설명서 4부_요약.md** (6KB, ~70 lines)
- Quick troubleshooting checklist
- Emergency procedures and support contacts

## For AI Agents

### Primary Directives

**CRITICAL RULES FOR KOREAN DOCUMENTATION**:
1. **Language Preservation**: NEVER translate Korean content to English without explicit user request
2. **Cultural Context**: Maintain Korean financial terminology (주식, 코인, 체결, 잔고, 수익률, 매수, 매도)
3. **Format Consistency**: Preserve dual-format structure (script + summary) for all parts
4. **Screenshot References**: When updating UI, verify screenshot references remain valid
5. **Keyboard Shortcuts**: Maintain accurate shortcut documentation (Alt-*, Ctrl-*)
6. **Read Before Edit**: ALWAYS read manual files before suggesting modifications

### Maintenance Patterns

**When Updating User Manuals**:

1. **UI Changes**:
   - Update both script and summary versions
   - Verify keyboard shortcuts match `ui/set_shortcut.py`
   - Update screenshot references if UI layout changed
   - Check related sections across all 4 parts

2. **Feature Additions**:
   - Add to appropriate part (1: setup, 2: basic, 3: advanced, 4: troubleshooting)
   - Include in script version with detailed explanation
   - Add concise entry to summary version
   - Update keyboard shortcut list if applicable

3. **Troubleshooting Updates**:
   - Add new issues to Part 4 script version
   - Classify by severity (common, rare, critical)
   - Include step-by-step resolution procedures
   - Reference related log files or error codes

4. **Content Synchronization**:
   - Script version is authoritative source
   - Summary version should reflect major points only
   - Maintain consistent terminology across all parts
   - Cross-reference between parts when necessary

### Korean Terminology Standards

**Financial Terms** (DO NOT TRANSLATE):
- 주식 (stock), 코인 (coin), 암호화폐 (cryptocurrency)
- 매수 (buy), 매도 (sell), 체결 (execution)
- 잔고 (balance), 잔권 (remaining position)
- 수익률 (return rate), 손익 (profit/loss)
- 거래목록 (trade list), 체결목록 (execution list)

**Technical Terms** (DO NOT TRANSLATE):
- 백테스트 (backtest), 최적화 (optimization)
- 전략 (strategy), 조건 (condition)
- 호가창 (order book window), 차트 (chart)
- 데이터베이스 (database), 로그인 (login)
- 시뮬레이터 (simulator), 스케줄러 (scheduler)

**UI Elements** (Keep Korean):
- 설정창 (settings window), 전략창 (strategy window)
- 단축키 (shortcut key), 확장버튼 (expand button)
- 종목명 (stock name), 업종 (industry sector)
- 트리맵 (treemap), 그래프 (graph)

### Content Structure Guidelines

**Script Version (스크립트)**:
- Detailed step-by-step instructions with rationale
- Complete keyboard shortcut documentation
- Screenshots and visual guides (referenced, not embedded)
- Real-world usage examples and scenarios
- Troubleshooting tips within each section
- Target length: 900-1,800 lines depending on part complexity

**Summary Version (요약)**:
- Concise bullet points covering essential operations
- Quick reference for keyboard shortcuts
- Core concepts without detailed explanation
- Assumes familiarity with basic terminology
- Target length: 70-110 lines

### Documentation Patterns

**Keyboard Shortcut Documentation**:
```markdown
- **Alt-T**: 수익 집계 창 전환
- **Alt-S**: 주식 수동 시작
- **Alt-D**: DB 관리
- **Alt-P**: GIMP 창 실행
- **Alt-U**: 업종 및 테마 트리맵 표시
```

**Feature Explanation Pattern**:
```markdown
### [Feature Number]. [Icon] [Feature Name]
- [Purpose and overview]
- [Step-by-step instructions]
- [Important notes and warnings]
- [Related features and shortcuts]
```

**Troubleshooting Entry Pattern**:
```markdown
### [Issue Category]
- **증상**: [Symptom description]
- **원인**: [Root cause]
- **해결방법**: [Step-by-step solution]
- **예방**: [Prevention tips]
```

### Cross-Reference Management

**Internal References** (within 사용설명서/):
- Part 1 → Part 2: Setup completion leads to strategy configuration
- Part 2 → Part 3: Basic features lead to live trading
- Part 3 → Part 4: Advanced usage references troubleshooting
- Part 4 → Part 1-3: Troubleshooting references specific feature sections

**External References** (to other documentation):
- → `docs/Manual/`: Technical implementation details (for advanced users)
- → `docs/Guideline/`: Strategy development and backtesting guidelines
- → `utility/setting.py`: Configuration reference
- → `ui/ui_mainwindow.py`: UI component reference

### Common Tasks

**Add New Feature to Manual**:
1. Determine appropriate part (1: setup, 2: basic, 3: advanced)
2. Write detailed explanation in script version with:
   - Feature purpose and use cases
   - Step-by-step operation instructions
   - Keyboard shortcuts (if applicable)
   - Screenshots or visual references
   - Troubleshooting tips
3. Add concise summary to corresponding summary version
4. Update keyboard shortcut index if applicable
5. Add troubleshooting entry to Part 4 if needed

**Update UI Changes**:
1. Identify affected manual sections across all 4 parts
2. Update script versions with new UI element descriptions
3. Update summary versions with new navigation paths
4. Verify keyboard shortcuts in `ui/set_shortcut.py`
5. Note screenshot update requirements
6. Check cross-references remain valid

**Synchronize Script and Summary**:
1. Review script version for major concept changes
2. Extract key points for summary version
3. Ensure summary bullet points match script sections
4. Maintain consistent terminology
5. Verify keyboard shortcuts identical in both versions

### Quality Standards

**Completeness Checklist**:
- [ ] All 4 parts have both script and summary versions
- [ ] Keyboard shortcuts match actual implementation
- [ ] Korean terminology consistent across all parts
- [ ] Cross-references between parts are valid
- [ ] Screenshot references are current
- [ ] Troubleshooting covers common issues
- [ ] Content progression (basic → advanced) is logical

**Language Quality**:
- [ ] Korean grammar and spelling correct
- [ ] Financial terminology appropriate for Korean market
- [ ] Technical terms use standard Korean IT vocabulary
- [ ] Explanations clear for non-technical users
- [ ] Formal but accessible tone (존댓말)

**Technical Accuracy**:
- [ ] UI navigation paths correct
- [ ] Keyboard shortcuts verified in code
- [ ] Feature descriptions match actual behavior
- [ ] Database operations align with `utility/query.py`
- [ ] API references correct (Kiwoom, Upbit, Binance)

## Dependencies

### Internal Dependencies

**Source Code References**:
- `ui/ui_mainwindow.py` - Main window layout and tab structure
- `ui/set_shortcut.py` - Keyboard shortcut definitions
- `utility/setting.py` - Configuration settings and defaults
- `utility/database_check.py` - Database integrity procedures
- `stock/kiwoom_manager.py` - Stock trading process flow
- `coin/*_receiver_*.py` - Cryptocurrency data flow

**Related Documentation**:
- `docs/Manual/` - Technical system documentation (English)
- `docs/Guideline/Back_Testing_Guideline_Tick.md` - Tick strategy reference
- `docs/Guideline/Back_Testing_Guideline_Min.md` - Minute strategy reference
- `docs/Guideline/Condition_Document_Template_Guideline.md` - Strategy documentation format
- `docs/DOCUMENTATION_GUIDE.md` - Documentation validation procedures

### External Dependencies

**Runtime Requirements**:
- Python 32-bit or 64-bit (encryption key compatibility critical)
- Kiwoom OpenAPI (for stock trading, Windows only)
- Upbit/Binance API credentials (for cryptocurrency trading)
- SQLite databases in `_database/` directory
- Registry storage for encryption keys (Windows)

**UI Components**:
- PyQt5 main window and dialog components
- pyqtgraph for real-time charting
- QWebEngine for embedded browser (company info, news)
- System tray integration for notifications

**Data Sources**:
- Kiwoom OpenAPI real-time tick data
- Upbit WebSocket streams
- Binance WebSocket streams
- SQLite historical databases (tick, minute, day)

### Cross-Reference Matrix

| Manual Part | Key Topics | Related Code | Related Docs |
|-------------|-----------|--------------|--------------|
| Part 1 (시작하기) | Installation, UI layout, shortcuts | `stom.py`, `ui/ui_mainwindow.py` | `docs/Manual/01_Overview/` |
| Part 2 (기본 기능) | Strategy setup, backtesting | `backtester/*.py`, `ui/ui_button_clicked_*.py` | `Back_Testing_Guideline_*.md` |
| Part 3 (고급 기능) | Live trading, monitoring | `*_trader.py`, `*_strategy_*.py` | `docs/Manual/07_Trading/` |
| Part 4 (문제 해결) | Troubleshooting, diagnostics | `utility/database_check.py` | `docs/Manual/09_Manual/` |

### Version Synchronization

**Manual-Code Alignment**:
- Manual content should reflect current UI state in `ui/` modules
- Keyboard shortcuts must match `ui/set_shortcut.py` definitions
- Feature descriptions must match actual behavior in process modules
- Database procedures must align with `utility/query.py` operations
- API workflows must match manager process implementations

**Documentation Hierarchy**:
```
CLAUDE.md (overview)
    ↓
docs/Manual/ (technical details, English)
    ↓
docs/Guideline/ (development standards)
    ↓
docs/Guideline/사용설명서/ (user manuals, Korean) ← YOU ARE HERE
```

---

**Last Updated**: 2026-01-19
**Total Files**: 8 (4 script + 4 summary versions)
**Language**: Korean (한국어)
**Target Audience**: End-users, traders, system operators
**Content Structure**: Progressive (basic setup → advanced features → troubleshooting)
