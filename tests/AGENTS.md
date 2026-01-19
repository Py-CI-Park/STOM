<!-- Parent: ../AGENTS.md -->
# tests/

## Purpose
Unit tests and benchmarks for critical STOM components, with primary focus on backtesting output pipeline validation and performance measurement.

## Key Files

### Backtesting Output Tests
- **`test_backtesting_output.py`** (24 lines)
  - Unit tests for backtesting output subsystems
  - Tests IPC (Inter-Process Communication) data transfer:
    - `test_ipc_roundtrip_pickle()` - Pickle format serialization/deserialization
    - `load_dataframe_ipc()` / `save_dataframe_ipc()` validation
  - Tests caching mechanism:
    - `test_cache_roundtrip()` - Cache save/load with signature validation
    - `build_df_signature()`, `save_cached_df()`, `load_cached_df()` validation
  - Dependencies: `backtester/analysis/cache`, `backtester/analysis/ipc_utils`

- **`benchmark_backtesting_output.py`**
  - Performance benchmarks for backtesting output pipeline
  - Measures execution time and throughput
  - Validates optimization effectiveness

### Strategy Component Tests
- **`test_enhanced_buy_condition.py`**
  - Tests for enhanced buy condition logic
  - Validates strategy signal generation
  - Part of strategy validation framework

- **`test_segment_apply.py`**
  - Tests for segment-based data processing
  - Validates data partitioning and parallel processing
  - Critical for backtesting performance

## For AI Agents

### Running Tests

1. **Execute All Tests**:
   ```bash
   # From project root
   pytest tests/

   # Verbose output
   pytest -v tests/

   # Specific test file
   pytest tests/test_backtesting_output.py
   ```

2. **Run Benchmarks**:
   ```bash
   pytest tests/benchmark_backtesting_output.py --benchmark-only
   ```

### Writing New Tests

1. **Test Structure**:
   ```python
   import pandas as pd
   from backtester.analysis.some_module import function_to_test

   def test_feature_name(tmp_path):
       # Arrange: Setup test data
       df = pd.DataFrame({'col': [1, 2, 3]})

       # Act: Execute function
       result = function_to_test(df, param=value)

       # Assert: Validate results
       assert result is not None
       assert expected_condition
   ```

2. **Naming Conventions**:
   - Test files: `test_<component>.py`
   - Benchmark files: `benchmark_<component>.py`
   - Test functions: `test_<specific_behavior>()`

3. **Test Categories**:
   - **Unit Tests**: Test individual functions/methods in isolation
   - **Integration Tests**: Test component interactions
   - **Benchmarks**: Performance measurement and validation
   - **Roundtrip Tests**: Validate serialization/deserialization

### Test Coverage Focus

1. **Critical Path Components**:
   - Backtesting output pipeline (IPC, caching, exports)
   - Strategy signal generation and condition logic
   - Data processing and transformation
   - Performance-critical functions

2. **Current Coverage**:
   - IPC data transfer (pickle format) ✓
   - Caching mechanism with signature validation ✓
   - Buy condition logic ✓
   - Segment-based processing ✓

3. **Areas Needing Tests**:
   - Strategy execution logic
   - Order management and position tracking
   - Real-time data processing
   - Database query operations
   - UI event handlers

### Testing Patterns

1. **Temporary File Usage**:
   ```python
   def test_file_operation(tmp_path):
       # pytest provides tmp_path fixture
       file_path = tmp_path / "test_file.csv"
       # Use file_path for testing
   ```

2. **DataFrame Testing**:
   ```python
   # Test DataFrame equality
   assert df_result.equals(df_expected)

   # Test DataFrame properties
   assert len(df) == expected_length
   assert list(df.columns) == expected_columns
   ```

3. **Exception Testing**:
   ```python
   import pytest

   def test_error_handling():
       with pytest.raises(ValueError):
           function_that_should_raise(invalid_input)
   ```

### Benchmark Patterns

1. **Performance Measurement**:
   ```python
   def test_benchmark_function(benchmark):
       # benchmark fixture times the function
       result = benchmark(function_to_measure, arg1, arg2)
       assert result is not None
   ```

2. **Comparison Benchmarks**:
   ```python
   def test_compare_methods(benchmark):
       # Compare different implementations
       benchmark.group = "data_processing"
       result = benchmark(optimized_method, data)
   ```

## Dependencies

### Internal Dependencies
- `backtester/analysis/cache` - Caching subsystem
- `backtester/analysis/ipc_utils` - Inter-process data transfer
- `backtester/analysis/metrics_base` - Metrics calculation
- `backtester/analysis/exports` - CSV export functionality

### External Dependencies
- `pytest` - Test framework (install: `pip install pytest`)
- `pytest-benchmark` - Benchmarking plugin (optional)
- `pandas` - DataFrames for test data
- `tmp_path` - pytest fixture for temporary files

### Configuration
- `config/backtesting_output.py` - Indirectly affects tested components
- No pytest configuration file yet (consider adding `pytest.ini`)

## Testing Workflow

### Pre-Commit Testing
1. Run affected tests before committing code changes
2. Ensure all tests pass locally
3. Verify benchmarks show acceptable performance

### Continuous Integration
- Tests should be integrated into CI/CD pipeline
- Run full test suite on pull requests
- Track test coverage metrics
- Monitor benchmark performance trends

### Test-Driven Development
1. Write test for new feature
2. Implement feature until test passes
3. Refactor while keeping tests green
4. Add edge case tests

## Test Organization

### By Component
- **Backtesting**: `test_backtesting_output.py`, `benchmark_backtesting_output.py`
- **Strategy**: `test_enhanced_buy_condition.py`
- **Data Processing**: `test_segment_apply.py`

### By Type
- **Unit Tests** (3 files): Component isolation testing
- **Benchmarks** (1 file): Performance measurement

### Future Organization
Consider organizing by module as test suite grows:
```
tests/
├── backtester/
│   ├── test_analysis.py
│   ├── test_exports.py
│   └── benchmark_engine.py
├── stock/
│   └── test_kiwoom_strategy.py
├── coin/
│   └── test_upbit_strategy.py
└── ui/
    └── test_button_handlers.py
```

## Notes

- Test coverage is currently limited compared to codebase size (70,000+ lines)
- Focus on testing critical path components first
- Consider adding integration tests for multi-process workflows
- Benchmark tests help validate performance optimizations
- Use `tmp_path` fixture to avoid polluting filesystem
- Tests complement educational test code in `/lecture/testcode/`
