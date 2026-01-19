<!-- Parent: ../AGENTS.md -->
# User Interface Analysis Documentation

## Purpose

Comprehensive PyQt5 interface design documentation covering main window structure, event handling systems, data display components, chart rendering engines, and styling frameworks. This section provides complete technical documentation of STOM's GUI architecture, enabling understanding and modification of all user-facing interface components.

## Key Files

- **ui_ux_analysis.md** - Complete UI/UX analysis covering:
  - Main window structure (ui_mainwindow.py - 1,083 lines)
  - Event handler system (ui_button_clicked_*.py pattern)
  - Data display updates (ui_update_*.py pattern)
  - Chart rendering engines (ui_draw_*.py - candlesticks, real-time, TreeMap)
  - Layout configuration (set_*.py files)
  - Style management (set_style.py)
  - Signal/slot communication patterns
  - Threading for non-blocking operations
  - Queue-based data updates (windowQ, chartQ, hogaQ)

## For AI Agents

### Maintaining This Section

**When to Update:**
- New UI components added (tabs, widgets, dialogs)
- Event handlers modified or added
- Chart rendering engines updated
- Layout configurations changed
- Styling or themes modified
- Threading patterns changed
- Queue communication for UI updates modified

**Critical Validation Points:**

1. **UI File Structure** - Verify against actual ui/ directory:
   ```bash
   # Main window (should be 1,083 lines)
   wc -l ui/ui_mainwindow.py

   # Count UI component files (should be 70+ files)
   find ui/ -name "*.py" | wc -l

   # Event handlers (pattern: ui_button_clicked_*.py)
   ls ui/ui_button_clicked_*.py

   # Data updates (pattern: ui_update_*.py)
   ls ui/ui_update_*.py

   # Chart rendering (pattern: ui_draw_*.py)
   ls ui/ui_draw_*.py

   # Layout setup (pattern: set_*.py)
   ls ui/set_*.py
   ```

2. **Queue Integration** - Confirm UI-related queues:
   ```python
   # From utility/setting.py qlist
   windowQ  # Index 0 - Main window events
   chartQ   # Index 4 - Chart updates
   hogaQ    # Index 5 - Order book data
   ```

3. **PyQt5 Components** - Verify widget usage:
   - QMainWindow, QWidget, QTabWidget
   - QTableWidget, QTextEdit, QLabel
   - QPushButton, QComboBox, QLineEdit
   - pyqtgraph for real-time charting
   - QThread for background operations

**Update Guidelines:**
1. **Read Before Editing** - Always read `ui_ux_analysis.md` completely
2. **Test UI Changes** - Run application to verify component behavior
3. **Screenshot Updates** - Update screenshots if UI appearance changes
4. **Verify Thread Safety** - Ensure UI updates use proper threading
5. **Check Signal/Slot Connections** - Validate event wiring

### Code-Documentation Alignment

**Key Source References:**

**Main Window:**
```python
ui/ui_mainwindow.py (1,083 lines) - Core UI structure
- QMainWindow subclass
- Tab widget organization
- Process management
- Queue monitoring
- Thread coordination
```

**Event Handlers:**
```python
ui/ui_button_clicked_01.py - General system buttons
ui/ui_button_clicked_02.py - Trading control buttons
ui/ui_button_clicked_03.py - Strategy buttons
ui/ui_button_clicked_cvj.py - Coin order/balance handlers
ui/ui_button_clicked_svj.py - Stock order/balance handlers
```

**Data Display Updates:**
```python
ui/ui_update_01.py - Table updates
ui/ui_update_02.py - Text display updates
ui/ui_update_03.py - Progress indicators
ui/ui_update_cvj.py - Coin data displays
ui/ui_update_svj.py - Stock data displays
```

**Chart Rendering:**
```python
ui/ui_draw_01.py - Candlestick charts
ui/ui_draw_02.py - Real-time line charts
ui/ui_draw_03.py - TreeMap visualizations
ui/ui_draw_04.py - Performance charts
```

**Layout Configuration:**
```python
ui/set_ui.py - Main UI setup
ui/set_style.py - Styling and themes
ui/set_chart.py - Chart widget configuration
ui/set_table.py - Table widget setup
ui/set_text.py - Text widget configuration
```

**Validation Checklist:**
- [ ] File count matches ui/ directory (70+ files)
- [ ] Main window line count accurate (1,083 lines)
- [ ] Event handler patterns documented correctly
- [ ] Queue integration described accurately
- [ ] PyQt5 component usage verified
- [ ] Threading patterns match implementation
- [ ] Chart rendering techniques current

### Content Structure

**Standard Sections in ui_ux_analysis.md:**
1. **UI Architecture Overview** - PyQt5 structure and organization
2. **Main Window** - ui_mainwindow.py analysis
   - QMainWindow structure
   - Tab widget organization
   - Process spawning and monitoring
3. **Event Handling System** - Button click handlers
   - Pattern: ui_button_clicked_*.py
   - Signal/slot connections
   - Event routing to processes via queues
4. **Data Display Components** - Update mechanisms
   - Pattern: ui_update_*.py
   - Table updates (QTableWidget)
   - Text updates (QTextEdit)
   - Progress indicators
5. **Chart Rendering** - Visualization engines
   - Pattern: ui_draw_*.py
   - Candlestick charts (OHLCV)
   - Real-time line charts (pyqtgraph)
   - TreeMap visualizations
6. **Layout Management** - set_*.py configuration
   - Widget creation and placement
   - Tab organization
   - Style application
7. **Threading and Concurrency** - Non-blocking operations
   - QThread usage
   - Queue-based UI updates
   - Thread-safe data access
8. **Styling and Themes** - Visual design
   - set_style.py stylesheet application
   - Color schemes
   - Font management

**What Belongs Here:**
- UI component structure
- Event handling architecture
- Data display mechanisms
- Chart rendering techniques
- Layout and styling
- Threading for UI responsiveness
- PyQt5 patterns and best practices

**What Belongs Elsewhere:**
- Business logic → `07_Trading/`
- Data storage → `06_Data/`
- Process architecture → `02_Architecture/`
- Module implementation → `03_Modules/ui_module.md`

### Common Updates

**Adding New UI Component:**
1. Document widget type and purpose
2. Describe layout placement (which tab, position)
3. Document event handlers if interactive
4. Note data update mechanism if displays data
5. Add to appropriate set_*.py description
6. Update component count statistics

**Modifying Event Handler:**
1. Identify handler file (ui_button_clicked_*.py)
2. Document button purpose and location
3. Describe event processing flow
4. Note queue messages sent to processes
5. Update signal/slot connection documentation

**Updating Chart Rendering:**
1. Identify chart type and rendering file
2. Document data source and format
3. Describe rendering technique (pyqtgraph, native Qt)
4. Note performance considerations
5. Update visualization examples

**Changing Layout:**
1. Document affected set_*.py file
2. Describe new layout structure
3. Update widget placement descriptions
4. Verify responsive behavior
5. Update screenshots if available

## Dependencies

**Related Manual Sections:**
- `02_Architecture/` - Main process and queue architecture
- `03_Modules/ui_module.md` - Detailed UI module implementation
- `07_Trading/` - Business logic behind UI actions
- `06_Data/` - Data displayed in UI components

**Source Code References:**
- `ui/ui_mainwindow.py` - Main window (1,083 lines)
- `ui/ui_button_clicked_*.py` - Event handlers (5+ files)
- `ui/ui_update_*.py` - Data display updates (5+ files)
- `ui/ui_draw_*.py` - Chart rendering (4+ files)
- `ui/set_*.py` - Layout configuration (10+ files)
- `ui/set_style.py` - Styling management

**PyQt5 Documentation:**
- Official Qt5 documentation
- PyQt5 reference guide
- pyqtgraph documentation (for charts)

**Documentation Network:**
- Parent: `../AGENTS.md` - Manual documentation standards
- Architecture: `../02_Architecture/system_architecture.md` - UI in process model
- Modules: `../03_Modules/ui_module.md` - Implementation details

## Special Considerations

### Thread Safety for UI Updates
**CRITICAL:** All UI updates must occur in main thread:
```python
# Correct: Queue-based updates
windowQ.put(['update_table', data])

# Incorrect: Direct update from worker thread
self.table.setItem(0, 0, QTableWidgetItem(value))  # UNSAFE
```

Document proper threading patterns:
- Use signals/slots for cross-thread communication
- Queue-based updates from worker processes
- QThread for background operations
- Never update UI directly from worker threads

### Event Handler Naming Convention
**Pattern:** `ui_button_clicked_<category>.py`

Categories:
- `01` - General system buttons
- `02` - Trading control buttons
- `03` - Strategy management buttons
- `cvj` - Coin order/balance (Coin Volume Jango)
- `svj` - Stock order/balance (Stock Volume Jango)

Preserve this naming pattern in documentation.

### Queue-Based UI Updates
Document queue communication for UI:
- **windowQ** (index 0) - General window events
- **chartQ** (index 4) - Chart update commands
- **hogaQ** (index 5) - Order book data

Format: `queue.put([command, *args])`

### Chart Performance
Document performance considerations:
- Real-time chart update frequency
- Data point limits for responsive rendering
- pyqtgraph optimization techniques
- Canvas vs. OpenGL rendering modes

### Korean Text Display
UI displays Korean text extensively:
- Ensure UTF-8 encoding documented
- Document font requirements
- Note Korean column headers in tables
- Preserve Korean terminology in screenshots

### Multi-Monitor Support
STOM designed for multi-monitor trading:
- Document window sizing strategies
- Note tab organization for trading workflows
- Describe information density considerations

### Responsive Layout
Document layout behavior:
- Minimum window sizes
- Widget resizing behavior
- Tab organization rationale
- Information priority in limited space

### UI State Persistence
Document configuration persistence:
- Window geometry saving/restoring
- Tab selections
- Chart configurations
- Table column widths
- User preferences

### Accessibility Considerations
While not primary focus, document:
- Keyboard shortcuts
- Color contrast for critical information
- Font sizing options
- Screen reader compatibility (if any)

### Testing UI Changes
Provide testing checklist:
1. Visual verification (run application)
2. Event handler testing (click all buttons)
3. Data display testing (verify updates appear)
4. Chart rendering testing (performance check)
5. Layout testing (resize window, check tabs)
6. Threading testing (no UI freezes)

### UI Update Patterns
Document common update patterns:

**Table Update:**
```python
windowQ.put(['update_table', table_name, row, column, value])
```

**Text Update:**
```python
windowQ.put(['update_text', text_widget_name, content])
```

**Chart Update:**
```python
chartQ.put(['update_chart', chart_name, data])
```

### Screenshot Management
If screenshots included:
- Document screenshot capture process
- Note which UI states captured
- Describe annotations or highlights
- Update screenshots after major UI changes
- Maintain consistent screenshot style

### Cross-Platform Considerations
While primarily Windows (Kiwoom requirement):
- Document Windows-specific UI elements
- Note any platform-dependent behaviors
- Describe limitations on other platforms

Maintain focus on actual deployment platform (Windows) in documentation.
