<!-- Parent: ../AGENTS.md -->
# icon/

## Purpose
Visual resources and UI icons for the STOM application. Contains image assets used throughout the PyQt5 interface including application icons, status indicators, and UI elements.

## Key Files

### Application Icons
- `stom.ico` - Main application icon (Windows .ico format)
- `python.png` - Python branding icon

### Market Type Icons
- `stock.png`, `stocks.png`, `stocks2.png` - Stock market indicators
- `coin.png`, `coins.png`, `coins2.png` - Cryptocurrency market indicators

### Status & Action Icons
- `checked.png`, `unchecked.png` - Checkbox states
- `start.png` - Process start indicator
- `live.png` - Live trading indicator
- `log.png`, `log2.png` - Logging/history indicators
- `total.png` - Total statistics display
- `set.png` - Settings/configuration

### Delete Operations
- `backdel.png` - Backtest deletion
- `accdel.png` - Account deletion
- `dbdel.png` - Database deletion

### Bitmap Indicators (.bmp)
- `up.bmp`, `down.bmp` - Price movement indicators
- `high.bmp`, `low.bmp` - Price extreme indicators
- `open.bmp` - Opening price indicator
- `vi.bmp` - Volatility Interruption indicator
- `pers.bmp`, `perb.bmp` - Performance indicators (stock/binance)
- `totals.bmp`, `totalb.bmp` - Total statistics (stock/binance)

## For AI Agents

### Icon Usage Patterns
1. **File Format Selection**:
   - Use `.png` for general UI elements (transparency support)
   - Use `.bmp` for specific trading indicators (performance optimization)
   - Use `.ico` for application window icon

2. **Naming Conventions**:
   - Market type: `stock`, `stocks`, `coin`, `coins` (plural variants for different sizes/contexts)
   - Actions: `*del.png` for deletion operations
   - Status: descriptive names (`checked`, `live`, `start`)

3. **Adding New Icons**:
   - Follow existing naming patterns
   - Provide multiple sizes if needed (append `2` for variants)
   - Use consistent file formats within categories
   - Update `ui/set_style.py` to reference new icons

4. **Icon References**:
   - Icons are loaded via `QIcon()` and `QPixmap()` in PyQt5
   - Paths are typically relative: `f"./icon/{filename}"`
   - Used in: `ui/set_*.py`, `ui/ui_*.py`, `stom.py`

### Common Operations
- **Icon not displaying**: Check file path, format compatibility, and PyQt5 resource loading
- **Adding themed icons**: Consider creating variants (light/dark mode) if needed
- **Icon size**: Ensure multiple sizes for different DPI/scaling scenarios
- **Performance**: `.bmp` files load faster for frequently updated indicators

## Dependencies

### Used By
- `ui/` - All UI modules reference icons for visual elements
- `stom.py` - Main application window icon
- `ui/set_style.py` - Style sheets with icon paths
- `ui/ui_mainwindow.py` - Toolbar and menu icons

### External Dependencies
- PyQt5.QtGui (QIcon, QPixmap)
- PyQt5.QtCore (Qt resource system)

## File Organization

### By Category
1. **Core Application** (2): `stom.ico`, `python.png`
2. **Market Types** (6): Stock and coin variants
3. **Status Indicators** (4): Checked, live, start, log
4. **Action Icons** (4): Deletion operations, settings
5. **Trading Indicators** (13): BMP files for real-time data display

### By File Format
- PNG files (16): General UI elements with transparency
- BMP files (13): High-performance trading indicators
- ICO files (1): Application icon

## Notes
- Icons are static resources; no runtime generation
- All icons are in version control (small file sizes)
- No localization needed (visual elements are universal)
- Consider adding SVG versions for scalability in future iterations
