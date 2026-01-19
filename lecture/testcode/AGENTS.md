<!-- Parent: ../AGENTS.md -->
# Test Code - Performance Benchmarking

## Purpose
Performance benchmarking and testing scripts for optimizing STOM trading system components. Contains comparative tests for data structures, algorithms, communication patterns, and serialization methods to inform architectural decisions for high-frequency trading operations.

## Key Files

### Data Structure Performance Tests

#### Array vs Native Type Comparisons
- **numpyint_vs_pureint.py** - NumPy integer array vs pure Python int() conversion
  - Tests bulk data type conversions in high-frequency tick processing
  - Measures initialization overhead vs vectorized operation benefits
  - Informs choice between numpy.array and native Python types for small datasets

- **in_list_or_array.py** - Membership checking performance (list vs array)
  - Compares `item in list` vs `item in numpy.array`
  - Critical for symbol filtering and blacklist checking in real-time processing
  - Tests various dataset sizes to find performance crossover points

- **slice_numpy_vs_dict.py** - Slicing operations (NumPy vs dictionary)
  - Benchmarks array slicing vs dictionary key-based access for historical data
  - Evaluates memory efficiency for storing candlestick data
  - Guides implementation of lookback window operations in strategies

#### Dictionary Operations
- **dict_insert_vs_update.py** - Dictionary insert vs update performance
  - Compares `dict[key] = value` vs `dict.update({key: value})`
  - Critical for real-time tick data accumulation patterns
  - Measures impact on position tracking and order management dictionaries

- **dictadd_vs_listappend.py** - Dictionary append vs list append
  - Tests data accumulation patterns for trade history and tick storage
  - Evaluates memory footprint differences at scale (10,000+ operations)
  - Informs choice between dict-based and list-based data buffers

- **createdict_pure_vs_zip.py** - Dictionary creation methods
  - Compares manual dict creation vs zip-based initialization
  - Relevant for initializing strategy parameters and configuration objects
  - Measures readability vs performance tradeoffs

#### Comprehension Performance
- **list_dict_comprehension.py** - List and dictionary comprehension benchmarks
  - Tests comprehension vs loop-based construction for various data structures
  - Evaluates performance for filtering and transforming tick/minute data
  - Provides guidelines for readable yet efficient data transformations

### DataFrame and Data Access Tests

- **pandas.at_vs_list.apd_to_df.py** - Pandas data access methods
  - Benchmarks `df.at[]`, `df.loc[]`, `df.iloc[]` vs list operations
  - Critical for strategy calculations accessing recent candlestick data
  - Tests conversion performance: list append → DataFrame creation
  - Informs optimal patterns for maintaining sliding windows of market data

### Memory Optimization Tests

- **numpydtypememory.py** - NumPy data type memory analysis
  - Compares memory usage: int8, int16, int32, int64, float32, float64
  - Tests memory footprint for large tick data arrays (millions of records)
  - Guides dtype selection for price, volume, and indicator storage
  - Critical for managing memory in multi-process architecture (15 processes)

- **shared_memory.py** - Shared memory access patterns
  - Tests multiprocessing.shared_memory for inter-process data sharing
  - Evaluates alternatives to queue-based communication for large datasets
  - Benchmarks read/write performance for shared price history
  - Explores zero-copy data sharing for real-time strategy calculations

### Serialization and Persistence

- **pickle_speed.py** - Pickle serialization performance
  - Benchmarks pickle dump/load for various data structures
  - Tests serialization of strategy state, position data, and configuration
  - Compares protocol versions (2, 3, 4, 5) for speed/size tradeoffs
  - Informs choice for queue-based IPC and database persistence patterns

### Communication Pattern Tests

#### ZeroMQ Multi-Process Communication
- **zmq_pub.py** - ZeroMQ publisher (PUB socket)
  - Publishes test messages to multiple subscribers simultaneously
  - Simulates Kiwoom manager broadcasting tick data to strategy processes
  - Tests message throughput and latency for real-time data distribution

- **zmq_sub1.py** - ZeroMQ subscriber #1 (SUB socket)
  - Subscribes to all topics, measures reception latency
  - Tests basic subscriber pattern for strategy processes

- **zmq_sub2.py** - ZeroMQ subscriber #2 with topic filtering
  - Demonstrates selective topic subscription for specific symbols
  - Measures filtering performance impact on message processing

- **zmq_sub3.py** - ZeroMQ subscriber #3 with custom handling
  - Tests advanced message handling and deserialization patterns
  - Evaluates error recovery and reconnection logic

**ZMQ Test Workflow**:
1. Run `zmq_pub.py` in terminal 1 (starts publisher)
2. Run `zmq_sub1.py`, `zmq_sub2.py`, `zmq_sub3.py` in separate terminals
3. Observe message distribution, latency, and throughput
4. Measure CPU and memory usage under load

### Trading-Specific Tests

- **test_candle_pattern.py** - Candlestick pattern recognition
  - Tests pattern detection algorithms: Doji, Hammer, Engulfing, etc.
  - Benchmarks pattern matching speed for real-time tick aggregation
  - Validates accuracy against known pattern examples
  - Measures performance impact of pattern recognition in strategy loops

- **test_withdrawfee.py** - Exchange fee calculations
  - Verifies withdrawal fee calculations for Upbit and Binance
  - Tests maker/taker fee computation accuracy
  - Validates fee impact on profit/loss calculations
  - Ensures consistency with exchange API documentation

- **realtime_fid.py** - Kiwoom API field ID processing
  - Tests FID (Field ID) parsing from Kiwoom real-time data streams
  - Benchmarks lookup performance for mapping FIDs to data fields
  - Validates correct extraction of price, volume, and order book data
  - Critical for `stock/kiwoom_receiver_tick.py` implementation

### Visualization Tests

- **back_plot_3d.py** - 3D backtest result plotting
  - Tests 3D surface plots for parameter optimization visualization
  - Benchmarks rendering performance for large result sets (1000+ tests)
  - Explores matplotlib 3D capabilities for equity surface plots
  - Evaluates alternative visualization libraries (plotly, mayavi)

## For AI Agents

### Performance Testing Workflow

**Before Making Optimization Decisions**:
1. Identify the operation to optimize (data structure, communication, serialization)
2. Locate the relevant test file in this directory
3. Run the benchmark to establish baseline performance
4. Analyze results: execution time, memory usage, CPU load
5. Document findings in code comments or optimization notes

**After Implementing Changes**:
1. Re-run the corresponding benchmark with new implementation
2. Compare results quantitatively (% improvement, absolute timing)
3. Verify no regressions in other performance metrics
4. Document optimization results with evidence
5. Update architectural decisions in relevant module documentation

### Test Execution Guidelines

**Running Individual Tests**:
```bash
cd C:\System_Trading\STOM\STOM_V1\lecture\testcode
python numpyint_vs_pureint.py
python pandas.at_vs_list.apd_to_df.py
python dict_insert_vs_update.py
```

**Running ZMQ Communication Tests**:
```bash
# Terminal 1 (Publisher)
python zmq_pub.py

# Terminal 2 (Subscriber 1)
python zmq_sub1.py

# Terminal 3 (Subscriber 2)
python zmq_sub2.py

# Terminal 4 (Subscriber 3)
python zmq_sub3.py
```

**Best Practices**:
- Run tests multiple times (5-10 iterations) for statistical validity
- Test under realistic data volumes (10,000+ operations for high-frequency scenarios)
- Measure both cold start and warm cache performance
- Monitor system resources (CPU, RAM) during execution
- Document environment: Python version, NumPy version, system specs

### Key Performance Insights

**Data Structure Selection**:
- **NumPy Arrays**: Faster for bulk operations (>1000 elements), higher initialization overhead
- **Pure Python**: Better for small datasets (<100 elements), lower memory footprint
- **Dictionary Update**: Faster than insert for existing keys, use for position tracking
- **List Append**: Faster than dict append for sequential data, use for tick accumulation

**DataFrame Usage**:
- **pandas.at[]**: Fastest for single cell access, use in tight loops
- **pandas.loc[]**: Better for row/column slicing, use for batch operations
- **List → DataFrame**: Efficient pattern: accumulate in list, convert to DataFrame periodically

**Memory Optimization**:
- **int32 vs int64**: 50% memory savings, sufficient for price data (max ~2 billion)
- **float32 vs float64**: 50% memory savings, acceptable precision for most indicators
- **Shared Memory**: 10x faster than pickle for large arrays, use for historical price data

**Communication Patterns**:
- **ZMQ PUB-SUB**: Efficiently distributes data to multiple processes, <1ms latency
- **Queue**: Simpler API, better for small messages, ~5-10ms latency
- **Pickle**: Fast for Python objects, use protocol 4+ for best performance

**Trading Operations**:
- **Pattern Recognition**: <1ms per candle required for real-time processing
- **Fee Calculation**: Pre-compute fee tables, avoid runtime calculations
- **FID Parsing**: Use dictionary lookup, not string parsing

### Test Modification Guidelines

When creating new benchmark tests:
1. **Structure**: Import timing modules, define test functions, run multiple iterations
2. **Output**: Print results in consistent format (operation, time, iterations/sec)
3. **Parameters**: Test with realistic data volumes from STOM use cases
4. **Comparison**: Include baseline (current method) vs alternative (proposed method)
5. **Documentation**: Add docstring explaining what is being tested and why

**Example Test Structure**:
```python
import time
import numpy as np

def test_method_a(iterations=10000):
    """Test Method A: Pure Python approach"""
    start = time.time()
    for i in range(iterations):
        # Method A implementation
        pass
    elapsed = time.time() - start
    return elapsed

def test_method_b(iterations=10000):
    """Test Method B: NumPy vectorized approach"""
    start = time.time()
    for i in range(iterations):
        # Method B implementation
        pass
    elapsed = time.time() - start
    return elapsed

if __name__ == "__main__":
    iterations = 10000
    print(f"Testing with {iterations} iterations...")

    time_a = test_method_a(iterations)
    time_b = test_method_b(iterations)

    print(f"Method A: {time_a:.4f}s ({iterations/time_a:.0f} ops/sec)")
    print(f"Method B: {time_b:.4f}s ({iterations/time_b:.0f} ops/sec)")
    print(f"Speedup: {time_a/time_b:.2f}x")
```

### Integration with STOM Modules

**Informing Architectural Decisions**:

1. **`stock/kiwoom_receiver_tick.py`** (42KB)
   - Uses insights from `numpyint_vs_pureint.py` for tick data conversion
   - Applies patterns from `realtime_fid.py` for FID parsing
   - Implements ZMQ patterns tested in `zmq_pub.py`, `zmq_sub*.py`

2. **`coin/upbit_strategy_min.py`** (28KB)
   - Data access patterns informed by `pandas.at_vs_list.py`
   - Dictionary operations guided by `dict_insert_vs_update.py`
   - Candlestick patterns from `test_candle_pattern.py`

3. **`backtester/backengine_*_*.py`** (12 files)
   - Array dtype choices from `numpydtypememory.py`
   - Slicing operations from `slice_numpy_vs_dict.py`
   - Plotting tested in `back_plot_3d.py`

4. **`utility/query.py`** (24KB)
   - Serialization approach from `pickle_speed.py`
   - Queue communication patterns for database operations

5. **All Strategy Files** (133 condition files)
   - Indicator calculations use NumPy patterns from performance tests
   - Data structure choices informed by benchmark results
   - Pattern recognition implementations validated by test accuracy

### Continuous Performance Monitoring

**Regression Detection**:
- Run relevant benchmarks after major changes
- Compare results against baseline metrics
- Flag performance regressions >10% for investigation
- Update benchmarks when new optimization techniques are discovered

**Documentation Updates**:
- Record performance characteristics in module docstrings
- Update CLAUDE.md with new performance insights
- Link optimization decisions to specific test results
- Maintain performance changelog for major improvements

## Dependencies

### Core Testing Libraries
- **time** (standard library) - Basic timing measurements
- **timeit** (standard library) - Precise timing for microbenchmarks
- **numpy** - Array operations and numerical computing (1.26.4)
- **pandas** - DataFrame benchmarking (2.0.3)

### Communication Testing
- **zmq (pyzmq)** - ZeroMQ messaging library for multi-process tests
- **pickle** (standard library) - Serialization benchmarking

### Visualization
- **matplotlib** - 3D plotting for backtest result visualization
- **mpl_toolkits.mplot3d** - 3D axes for surface plots

### System Monitoring
- **psutil** (optional) - CPU and memory monitoring during tests
- **memory_profiler** (optional) - Detailed memory usage analysis

### Trading Libraries
- **pyupbit** - For fee structure validation in `test_withdrawfee.py`
- **python-binance** - For Binance fee calculation tests

## Testing Context

All benchmarks are designed for **high-frequency trading system requirements** where:
- Microsecond-level optimizations matter for tick processing (1000+ ticks/second)
- Memory efficiency is critical for multi-process architecture (15 concurrent processes)
- Communication latency impacts real-time strategy execution (<10ms target)
- Serialization performance affects queue throughput and database persistence

Performance characteristics discovered here directly inform architectural decisions throughout the STOM codebase and are documented in module comments with references to specific test files.

## Maintenance Guidelines

**Adding New Tests**:
1. Identify optimization question (e.g., "dict vs list for order tracking")
2. Create descriptive filename (e.g., `dict_vs_list_order_tracking.py`)
3. Implement comparative benchmark with realistic data volumes
4. Run tests on reference hardware, document results
5. Update this AGENTS.md with test description and key insights
6. Reference test in relevant module documentation

**Updating Existing Tests**:
- Modify tests when dependencies upgrade (NumPy, pandas versions)
- Adjust test parameters if typical data volumes change
- Re-run benchmarks on new hardware configurations
- Document performance changes in test comments

**Test Deprecation**:
- Mark tests as deprecated if optimization questions are resolved
- Keep historical tests for reference (don't delete)
- Document why test is no longer relevant in test header comment
