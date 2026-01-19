<!-- Parent: ../AGENTS.md -->
# Image Files - UI Documentation & Visual Reference

## Purpose
Visual documentation and learning materials for the STOM trading system user interface. Contains screenshots of all major UI components, system architecture diagrams, and reference images for understanding system workflows.

## Key Files

### System Architecture
- **00_diagram.png** - System architecture overview diagram (exported from stom.drawio)
- **stom.drawio** - Editable Draw.io diagram source file for system architecture

### Main Interface Components
- **01_기본창.png** - Main window interface (primary trading dashboard)
- **02_집계창.png** - Aggregation window (portfolio statistics and summary)
- **16_로그창.png** - Log window (system events and trading logs)
- **17_설정창.png** - Settings window (configuration and preferences)

### Trading Strategy Interfaces
- **03_전략편집기.png** - Strategy editor (condition code editing interface)
- **10_조건편집기.png** - Condition editor (trading rule configuration)
- **08_변수편집기.png** - Variable editor (strategy parameter adjustment)
- **09_범위편집기.png** - Range editor (optimization parameter bounds)

### Backtesting & Optimization
- **04_백파인더.png** - BackFinder interface (strategy discovery tool)
- **05_최적화편집기.png** - Optimization editor (grid search configuration)
- **06_테스트편집기.png** - Test editor (backtesting setup)
- **11_GA편집기.png** - Genetic Algorithm editor (GA optimization setup)
- **07_전진분석.png** - Walk-forward analysis (progressive validation)
- **15_백테스케쥴러.png** - Backtest scheduler (automated testing workflows)

### Backtesting Results
- **12_백테로그.png** - Backtest log (real-time test execution logs)
- **13_백테기록.png** - Backtest records (historical test results table)
- **14_백테기록_그래프비교.png** - Graph comparison (performance visualization)
- **31_백테결과그래프.png** - Backtest result graphs (equity curves, drawdowns)
- **32_백테결과부가정보.png** - Additional test information (statistics and metrics)

### Real-Time Trading
- **18_주문관리.png** - Order management (active orders and execution)
- **19_스톰라이브.png** - STOM Live (real-time trading monitoring)
- **22_차트창.png** - Chart window (candlestick and indicator charts)
- **25_지수차트.png** - Index charts (market index visualization)
- **26_호가창.png** - Order book window (bid/ask depth)

### Market Analysis Tools
- **21_김프창.png** - Kimp window (Kimchi Premium arbitrage monitoring)
- **30_업종별테마별트리맵.png** - Sector/theme TreeMap (market heat map)
- **28_기업정보.png** - Company information (fundamental data)

### Additional Features
- **20_디비관리.png** - Database management (data maintenance tools)
- **29_웹엔진뷰어.png** - Web engine viewer (embedded browser for research)
- **33_텔레그램 사용자버튼.png** - Telegram user buttons (notification controls)
- **35_비중조절.png** - Position sizing adjustment (risk management)

### Reference Materials
- **참고 교차검증.png** - Cross-validation reference (validation methodology)
- **참고 전진분석.jpg** - Walk-forward analysis reference (testing approach)

## For AI Agents

### Documentation Guidelines
1. **UI Reference**: When explaining UI features, reference corresponding screenshot files for visual context
2. **Architecture Discussion**: Use 00_diagram.png as the primary reference for system component interactions
3. **Feature Location**: Help users locate features by referencing specific window images
4. **Workflow Visualization**: Use sequential image numbers to explain multi-step workflows

### Image Usage Patterns
- **UI Development**: Reference screenshots when modifying UI layouts in `/ui/` modules
- **User Documentation**: Link images in markdown docs to provide visual guides
- **Bug Reports**: Reference specific windows when troubleshooting UI issues
- **Feature Requests**: Use existing UI patterns from screenshots as design references

### Korean UI Elements
All screenshots contain Korean language UI elements. Key translations:
- 기본창 (Basic Window) - Main trading interface
- 집계창 (Aggregation Window) - Portfolio summary
- 전략편집기 (Strategy Editor) - Condition code editor
- 백테 (Backtest) - Backtesting features
- 최적화 (Optimization) - Parameter optimization
- 김프 (Kimp) - Kimchi Premium (KRW crypto arbitrage)

### Diagram Maintenance
- **stom.drawio** is the source file for architecture diagrams
- Export to PNG after modifications for documentation consistency
- Keep diagram synchronized with actual system architecture changes

## Dependencies
- **Draw.io** (diagrams.net) - For editing stom.drawio architecture diagram
- **Image viewer** - Standard PNG/JPG viewer for reference materials
- **Screen capture tools** - For updating screenshots after UI changes

## Update Guidelines
When UI components change:
1. Capture new screenshots at consistent resolution
2. Update corresponding numbered image files
3. Maintain Korean language consistency in UI elements
4. Update stom.drawio if architecture changes
5. Export new 00_diagram.png after diagram updates
6. Reference new images in user documentation
