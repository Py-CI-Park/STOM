<!-- Parent: ../AGENTS.md -->
# UI Module (PyQt5)

## Purpose
PyQt5-based graphical user interface for STOM V1 trading system. Contains 70+ component files (~20,625 lines) providing real-time market data visualization, trading controls, backtesting interfaces, and system monitoring.

## Key Files

### Main Window & Coordination
- **ui_mainwindow.py** (1,083 lines) - Main application window, process coordination, queue management, signal routing
  - Inherits from multiple UI component mixins
  - Coordinates 15 inter-process communication queues
  - Manages real-time data updates via PyQt signals/slots

### Event Handlers (ui_button_clicked_*.py)
Event handlers organized by functional area:

**Stock Trading (svj = 주식체결잔고)**
- **ui_button_clicked_svj.py** (54,866 lines) - Stock trading panel buttons (buy/sell execution)
- **ui_button_clicked_svc.py** (12,305 lines) - Stock condition configuration
- **ui_button_clicked_svjb.py** (4,076 lines) - Stock backtesting controls
- **ui_button_clicked_svjs.py** (4,237 lines) - Stock strategy selection
- **ui_button_clicked_svoa.py** (5,107 lines) - Stock order automation

**Cryptocurrency Trading (cvj = 코인체결잔고)**
- **ui_button_clicked_cvj.py** (54,921 lines) - Cryptocurrency trading panel buttons
- **ui_button_clicked_cvc.py** (13,514 lines) - Crypto condition configuration
- **ui_button_clicked_cvjb.py** (4,440 lines) - Crypto backtesting controls
- **ui_button_clicked_cvjs.py** (4,609 lines) - Crypto strategy selection
- **ui_button_clicked_cvoa.py** (5,098 lines) - Crypto order automation

**Other Controls**
- **ui_button_clicked_chart.py** (3,217 lines) - Chart view controls
- **ui_button_clicked_db.py** (9,630 lines) - Database management buttons
- **ui_button_clicked_etc.py** (12,636 lines) - Miscellaneous controls
- **ui_button_clicked_etsj.py** (3,778 lines) - Additional trading controls
- **ui_button_clicked_icos.py** (33,152 lines) - ICOS (Integrated Condition Optimization System) controls
- **ui_button_clicked_mn.py** (15,227 lines) - Main menu buttons
- **ui_button_clicked_ob.py** (5,281 lines) - Order book controls
- **ui_button_clicked_sd.py** (47,587 lines) - System dashboard buttons
- **ui_button_clicked_sj.py** (85,498 lines) - Strategy journal controls
- **ui_button_clicked_ss_cs.py** (9,624 lines) - Stock/crypto synchronization
- **ui_button_clicked_zoom.py** (7,624 lines) - Chart zoom controls

### Data Display Updates (ui_update_*.py)
- **ui_update_tablewidget.py** (29,548 lines) - Real-time table updates (positions, orders, trade history)
- **ui_update_textedit.py** (17,416 lines) - Text field updates (logs, strategy output, system messages)
- **ui_update_progressbar.py** (8,342 lines) - Progress indicators (backtesting, optimization, data loading)

### Chart Rendering (ui_draw_*.py)
- **ui_draw_chart.py** (33,279 lines) - Main candlestick chart rendering (pyqtgraph)
- **ui_draw_realchart.py** (41,725 lines) - Real-time tick/minute chart updates
- **ui_draw_jisuchart.py** (977 lines) - Index chart rendering (KOSPI, KOSDAQ, Bitcoin)
- **ui_draw_treemap.py** (6,488 lines) - TreeMap visualization for portfolio composition

### Component Setup (set_*.py)
- **set_widget.py** (25,222 lines) - Widget creation and initialization
- **set_style.py** (10,855 lines) - Styling, themes, colors, fonts
  - Custom dark theme with QColor definitions
  - Button styles (buy/sell/disabled states)
  - Font configurations (나눔고딕 12-14px)
- **set_table.py** (8,925 lines) - Table widget configurations
- **set_text.py** (123,840 lines) - Text content, help messages, templates
- **set_mainmenu.py** (8,453 lines) - Main menu bar setup
- **set_icon.py** (1,561 lines) - Application icons and images

**Tab Configurations**
- **set_ordertap.py** (48,035 lines) - Order management tab layout
- **set_setuptap.py** (30,856 lines) - System setup tab
- **set_logtap.py** (753 lines) - Log viewer tab
- **set_sbtap.py** (48,579 lines) - Stock backtesting tab
- **set_cbtap.py** (48,015 lines) - Crypto backtesting tab

**Dialog Windows**
- **set_dialog_back.py** (74,828 lines) - Backtesting dialog configurations
- **set_dialog_chart.py** (36,942 lines) - Chart settings dialog
- **set_dialog_etc.py** (60,521 lines) - Miscellaneous dialogs
- **set_dialog_icos.py** (29,774 lines) - ICOS configuration dialog

### Additional UI Components
- **ui_backtest_engine.py** (22,529 lines) - Backtesting engine integration
- **ui_betting_cotrol.py** (7,529 lines) - Position sizing and risk controls
- **ui_cell_clicked.py** (14,200 lines) - Table cell click event handlers
- **ui_chart_count_change.py** (8,434 lines) - Chart data range controls
- **ui_checkbox_changed.py** (11,951 lines) - Checkbox state handlers
- **ui_crosshair.py** (10,714 lines) - Chart crosshair functionality
- **ui_event_filter.py** (10,014 lines) - Custom event filtering
- **ui_extend_window.py** (6,498 lines) - Window resize/extend controls
- **ui_key_press_event.py** (11,406 lines) - Keyboard shortcut handlers
- **ui_process_alive.py** (2,866 lines) - Process health monitoring
- **ui_process_kill.py** (5,611 lines) - Process termination handlers
- **ui_process_starter.py** (3,008 lines) - Process launch handlers
- **ui_show_dialog.py** (20,722 lines) - Dialog display logic
- **ui_vars_change.py** (12,328 lines) - Variable change handlers
- **ui_activated_*.py** - Combobox/dropdown activation handlers (stock, coin, backtesting)
- **ui_etc.py** (6,496 lines) - Miscellaneous UI utilities

### Media & Resources
- **set_mediaplayer.py** (829 lines) - Media playback controls
- **intro.mp4** (20MB) - Application intro video

## Subdirectories
None - All UI components in flat structure

## For AI Agents

### Code Modification Rules
1. **Always Read Before Edit** - Never modify UI files without reading them first
2. **Preserve Korean Variables** - Keep Korean text for labels, tooltips, help messages (e.g., "확대(esc)", "체결잔고")
3. **Respect Naming Conventions**:
   - `ui_button_clicked_*.py` - Button event handlers
   - `ui_update_*.py` - Data display updates
   - `ui_draw_*.py` - Chart rendering
   - `set_*.py` - Component setup and configuration
   - `svj` prefix = Stock trading (주식체결잔고)
   - `cvj` prefix = Crypto trading (코인체결잔고)

### UI Architecture Patterns
- **Mixin-Based Design** - `ui_mainwindow.py` inherits from multiple component classes
- **Signal-Slot Communication** - PyQt5 signals for queue-based updates
- **Observer Pattern** - Real-time data updates via queue monitoring
- **Dynamic Layout** - Window geometry changes based on `ui.extend_window` flag
- **Theme Support** - Dark theme with customizable colors in `set_style.py`

### Event Handling
- **Button Clicks** - Organized by functional area (stock/crypto/chart/database)
- **Table Interactions** - Cell clicks, row selections, sorting
- **Keyboard Shortcuts** - ESC for zoom toggle, custom key bindings
- **Process Communication** - All inter-process communication via 15 queues (windowQ, chartQ, etc.)

### Chart Rendering
- **pyqtgraph Library** - High-performance real-time charting
- **Candlestick Charts** - OHLC data visualization with volume bars
- **Real-time Updates** - Tick-by-tick chart updates via queue
- **Technical Indicators** - MA lines, volume, custom overlays
- **Crosshair Tool** - Interactive price/time cursor

### Styling Guidelines
- **Colors** - Defined in `set_style.py` with QColor objects
  - Buy buttons: Red tones (`color_pluss`, `style_bc_by`)
  - Sell buttons: Blue tones (`color_minus`, `style_bc_sl`)
  - Enabled: Green (`style_bc_bs`)
  - Disabled: Dark green (`style_bc_bd`)
- **Fonts** - 나눔고딕 (NanumGothic) 12-14px for Korean text
- **Dark Theme** - Background colors from `color_bg_bk` (20, 20, 30) to `color_bg_bt` (50, 50, 60)
- **Foreground** - Text colors from `color_fg_dk` (150, 150, 160) to `color_fg_bt` (230, 230, 240)

### Common UI Tasks

**Adding New Button Handler**:
1. Create function in appropriate `ui_button_clicked_*.py` file
2. Follow naming pattern: `{prefix}_button_clicked_{number}`
3. Connect signal in `set_widget.py` or setup file
4. Update `ui_mainwindow.py` if cross-module coordination needed

**Updating Table Display**:
1. Modify `ui_update_tablewidget.py` for table logic
2. Use queue-based updates (windowQ) from worker processes
3. Preserve column definitions from `set_table.py`
4. Test with real-time data flow

**Adding Chart Indicator**:
1. Extend `ui_draw_chart.py` or `ui_draw_realchart.py`
2. Use pyqtgraph API for rendering
3. Add color definitions to `set_style.py`
4. Update chart configuration dialogs

**Creating New Dialog**:
1. Add setup in `set_dialog_*.py` with layout
2. Create display logic in `ui_show_dialog.py`
3. Wire button/event handlers to dialog actions
4. Test modal vs. non-modal behavior

### Testing & Validation
- **UI Responsiveness** - Test with high-frequency data updates (tick data)
- **Memory Leaks** - Monitor long-running sessions for memory growth
- **Thread Safety** - All UI updates must occur in main thread (use signals)
- **Multi-Monitor** - Test window positioning and chart layouts
- **Process Communication** - Verify queue-based updates don't block UI

### Performance Considerations
- **pyqtgraph Optimization** - Limit chart data points (e.g., last 500 candles)
- **Table Updates** - Batch updates to minimize redraws
- **Signal Throttling** - Debounce high-frequency signals
- **Widget Visibility** - Hide unused components to reduce render overhead
- **Queue Monitoring** - Prevent queue overflow with proper consumer rates

### Integration Points
- **Process Queues** - 15 queues defined in `ui_mainwindow.py` (windowQ, chartQ, hogaQ, etc.)
- **Database** - Real-time queries via queryQ to query process
- **WebSocket** - Market data via receiver processes
- **Backtester** - Integration via backQ for historical testing
- **Telegram** - Notifications via teleQ

### Common Patterns
- **Geometry Management** - Dynamic layout with `setGeometry()` based on window state
- **Visibility Toggles** - Show/hide widget groups (e.g., `stock_detail_list`)
- **Style Application** - Runtime stylesheet changes via `setStyleSheet()`
- **Text Templates** - Reusable help text from `set_text.py`
- **Icon Management** - Centralized icon loading in `set_icon.py`

### Debugging UI Issues
1. **Check Logs** - `/_log/` directory for UI-related errors
2. **Signal Connections** - Verify signal-slot connections in setup files
3. **Queue Flow** - Monitor queue contents for data flow issues
4. **Widget Hierarchy** - Inspect parent-child relationships
5. **Event Propagation** - Check event filter chain in `ui_event_filter.py`

## Dependencies
- **PyQt5** - Main GUI framework (Qt5 widgets, layouts, signals/slots)
- **PyQt5-WebEngine** - Web content rendering for dialogs
- **pyqtgraph** - High-performance plotting and charting
- **multiprocessing** - Process management and queue communication
- **utility modules** - setting, static, query, chart, hoga, sound, telegram_msg

## Documentation References
See `/docs/Manual/05_UI_UX/` for detailed UI/UX analysis and design documentation.
