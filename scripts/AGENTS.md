<!-- Parent: ../AGENTS.md -->
# scripts/

## Purpose
Automation and performance measurement scripts for backtesting system analysis. Contains utilities for profiling, benchmarking, and validating backtesting output performance.

## Key Files

### Performance Measurement
- **`measure_backtesting_performance.py`** (38 lines)
  - CLI tool for measuring backtesting output pipeline performance
  - Profiles three key components:
    1. **Metrics Calculation**: `CalculateDerivedMetrics()` timing
    2. **CSV Export**: `ExportBacktestCSV()` timing
    3. **Full Analysis**: `RunFullAnalysis()` timing (optional)
  - Usage: `python scripts/measure_backtesting_performance.py --detail <csv> --save <name> [--full]`
  - Output: Execution time for each pipeline stage

## For AI Agents

### Working with Scripts

1. **Performance Measurement**:
   ```bash
   # Basic measurement (metrics + CSV)
   python scripts/measure_backtesting_performance.py \
     --detail _icos_results/detail.csv \
     --save output_name

   # Full pipeline measurement
   python scripts/measure_backtesting_performance.py \
     --detail _icos_results/detail.csv \
     --save output_name \
     --full
   ```

2. **Adding New Scripts**:
   - Place automation utilities in this directory
   - Use descriptive names: `<verb>_<target>_<purpose>.py`
   - Include CLI argument parsing with `argparse`
   - Add timing/profiling output for performance validation
   - Document usage in this AGENTS.md

3. **Script Development Patterns**:
   - Import from `backtester/` modules for analysis components
   - Use `time.perf_counter()` for precise timing
   - Accept file paths as CLI arguments (use `argparse`)
   - Provide clear console output with timing breakdowns
   - Support both partial and full pipeline execution

4. **Integration Points**:
   - Scripts analyze output from `backtester/` modules
   - Work with CSV files from `_icos_results/` directory
   - Can optionally integrate with telegram queue (`teleQ`)
   - Reference configuration from `config/backtesting_output.py`

### Common Use Cases

1. **Performance Profiling**:
   - Identify bottlenecks in backtesting output pipeline
   - Compare performance before/after optimizations
   - Validate parallel processing improvements
   - Measure impact of configuration changes

2. **Regression Testing**:
   - Ensure performance doesn't degrade with code changes
   - Validate optimization effectiveness
   - Compare different IPC formats (pickle, parquet, feather)
   - Test parallel vs. sequential execution

3. **Debugging**:
   - Isolate slow components in analysis pipeline
   - Verify data processing correctness
   - Test CSV export functionality
   - Validate full analysis workflow

## Dependencies

### Internal Dependencies
- `backtester/analysis/metrics_base` - `CalculateDerivedMetrics()`
- `backtester/analysis/exports` - `ExportBacktestCSV()`
- `backtester/back_static` - `RunFullAnalysis()`

### External Dependencies
- `pandas` - Data manipulation
- `argparse` - CLI argument parsing
- `time` - Performance timing

### Configuration
- `config/backtesting_output.py` - Pipeline configuration (indirectly used by imported modules)

## Script Categories

### Current Scripts (1)
- Performance measurement

### Potential Additions
- Database cleanup automation
- Batch backtesting orchestration
- Result validation and comparison
- Report generation automation
- Data export utilities

## Notes

- Scripts are standalone utilities, not part of main application
- Execute from project root: `python scripts/<script_name>.py`
- Scripts should be idempotent and safe to re-run
- Consider adding more automation as backtesting workflow evolves
- Future: Add batch processing scripts for multiple backtest scenarios
