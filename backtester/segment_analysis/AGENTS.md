<!-- Parent: ../AGENTS.md -->
# backtester/segment_analysis

## Purpose
Segment-based performance studies dividing data by market cap, time periods, volatility, or other dimensions. Optimizes filters separately for each segment to improve overall strategy performance.

## Key Files

### Core Components
- `__init__.py` - Package exports and API
- `segmentation.py` - SegmentConfig, SegmentBuilder (data partitioning)
- `filter_evaluator.py` - FilterEvaluator (evaluate filter performance per segment)
- `combination_optimizer.py` - Combine multiple filters optimally
- `threshold_optimizer.py` - Optimize threshold values per segment
- `validation.py` - Stability validation across segments
- `risk_metrics.py` - Risk calculation per segment
- `multi_objective.py` - Pareto optimization (profit vs. stability)

### Code Generation
- `code_generator.py` - Generate executable filter code from segment rules
- `segment_apply.py` - Apply segment filters to new data

### Visualization & Reporting
- `segment_visualizer.py` - Heatmaps and segment comparison charts
- `segment_outputs.py` - Output file management
- `segment_summary_report.py` - Comprehensive reports
- `segment_mode_comparator.py` - Compare different segmentation modes
- `segment_template_comparator.py` - Compare segmentation templates

### Runner Scripts
- `phase1_runner.py` - Initial segment optimization
- `phase2_runner.py` - Filter combination optimization
- `phase3_runner.py` - Final validation and code generation
- `advanced_search_runner.py` - Advanced optimization search
- `decision_report_runner.py` - Decision support reports
- `multi_objective_runner.py` - Multi-objective optimization

### Testing & Debugging
- `test_real_data.py` - Real data testing
- `test_filter_first_standalone.py` - Filter testing
- `runtime_debug.py` - Runtime debugging
- `verify_segment_consistency.py` - Consistency checks
- `compare_detail_csvs.py` - Compare CSV outputs

### Optimization
- `genetic_optimizer.py` - Genetic algorithm for segment optimization

## Subdirectories
None

## For AI Agents
When working with segment analysis:

### Segmentation Strategy
1. Define segments using `SegmentConfig` (market cap ranges, time periods)
2. Use `SegmentBuilder` to partition backtest data
3. Common dimensions: market_cap (시가총액), time_of_day (시간대), volatility (변동성)

### Optimization Workflow
1. **Phase 1**: Initial segment identification and filter evaluation
   - Run `phase1_runner.py` for baseline segment performance
   - Use `filter_evaluator.py` to test individual filters per segment
2. **Phase 2**: Filter combination optimization
   - Run `phase2_runner.py` to find optimal filter combinations
   - `combination_optimizer.py` tests multiple filter combinations
3. **Phase 3**: Validation and code generation
   - Run `phase3_runner.py` for final validation
   - `code_generator.py` produces executable Python code

### Multi-Objective Optimization
- Use `multi_objective.py` for Pareto-optimal solutions
- Balance profit vs. stability/drawdown
- `build_pareto_front()` returns non-dominated solutions

### Code Generation
- `build_segment_filter_code()` generates if-elif-else chains
- Output format matches strategy execution requirements
- Korean variable names (시가총액, 시간대, etc.)

### Validation
- `validation.py` checks stability across data splits
- `verify_segment_consistency.py` ensures logical consistency
- Walk-forward validation prevents overfitting

### Output Files
- Segment summaries (CSV)
- Filter codes (TXT)
- Heatmaps (PNG)
- Comparison reports (CSV)

## Dependencies
- numpy/pandas - Data manipulation
- scipy - Statistical analysis
- matplotlib - Visualization
- optuna - Optimization (if using genetic algorithms)
- All dependencies from `backtester/analysis/`
