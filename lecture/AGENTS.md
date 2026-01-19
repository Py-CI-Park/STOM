<!-- Parent: ../AGENTS.md -->
# Educational Materials & Testing

## Purpose
Educational materials and performance benchmarking for STOM system optimization. Contains test code for comparing different implementation approaches, ZMQ communication patterns, and performance analysis tools.

## Key Files

### Performance Benchmarking Tests
- **numpyint_vs_pureint.py** - Compares NumPy integer array performance vs pure Python int() conversion in high-frequency data processing loops
- **pandas.at_vs_list.apd_to_df.py** - Benchmarks different data access methods (pandas.at vs list operations) for real-time data structures
- **dict_insert_vs_update.py** - Compares dictionary insertion vs update operations for optimal data structure choices
- **dictadd_vs_listappend.py** - Tests dictionary append vs list append performance in data accumulation scenarios
- **createdict_pure_vs_zip.py** - Compares pure dictionary creation vs zip-based approaches
- **list_dict_comprehension.py** - Performance analysis of list and dictionary comprehensions
- **in_list_or_array.py** - Tests membership checking in lists vs arrays
- **slice_numpy_vs_dict.py** - Compares slicing operations between NumPy arrays and dictionaries

### Data Processing Tests
- **pickle_speed.py** - Serialization performance benchmarking for data persistence and inter-process communication
- **numpydtypememory.py** - Memory usage analysis for different NumPy data types in large arrays
- **shared_memory.py** - Shared memory access patterns for multiprocess architectures

### Communication Tests
- **zmq_pub.py** - ZeroMQ publisher test for multi-subscriber real-time data streaming
- **zmq_sub1.py / zmq_sub2.py / zmq_sub3.py** - ZeroMQ subscriber tests demonstrating parallel data reception patterns

### Trading-Specific Tests
- **test_candle_pattern.py** - Pattern recognition algorithm testing for candlestick analysis
- **test_withdrawfee.py** - Fee calculation verification for different exchanges and transaction types
- **realtime_fid.py** - Real-time field ID processing tests for Kiwoom API data streams

### Visualization Tests
- **back_plot_3d.py** - 3D plotting tests for backtest result visualization

## Subdirectories
- **imagefiles/** - Learning material images and visual documentation
- **pycharm/** - PyCharm IDE configuration files for project setup
- **testcode/** - Performance benchmarking and testing scripts (19 files)

## For AI Agents

### Performance Testing Guidelines
1. **Before Optimization**: Always run relevant benchmark tests from testcode/ to establish baseline performance
2. **Data Structure Selection**: Consult benchmark results when choosing between NumPy arrays, lists, or dictionaries for high-frequency operations
3. **Communication Patterns**: Reference ZMQ tests (zmq_pub.py, zmq_sub*.py) for proper multi-process communication implementation
4. **Memory Optimization**: Use numpydtypememory.py results to select appropriate data types for large arrays

### Benchmarking Best Practices
- Run tests multiple times for statistical validity
- Test under realistic data volumes (10,000+ iterations)
- Consider both execution speed and memory usage
- Document performance results in code comments

### Testing Workflow
1. Identify optimization target (data structure, communication, serialization)
2. Locate relevant test file in testcode/
3. Run baseline benchmark
4. Implement optimization
5. Run comparative benchmark
6. Document performance improvement with evidence

### Key Performance Insights
- **NumPy vs Pure Python**: NumPy array operations are generally faster for bulk data processing but have initialization overhead
- **Dictionary Operations**: Update is faster than repeated insertions for existing keys
- **ZMQ Communication**: PUB-SUB pattern supports efficient one-to-many real-time data distribution
- **Serialization**: pickle provides fast serialization for Python objects in IPC scenarios

## Dependencies
- **numpy** - Array operations and numerical computing
- **pandas** - Data structure benchmarking
- **zmq (pyzmq)** - ZeroMQ messaging library for communication tests
- **pickle** - Python serialization (standard library)
- **time** - Performance timing (standard library)
- **matplotlib** - Visualization for 3D plotting tests

## Testing Context
All tests are designed for high-frequency trading system requirements where microsecond-level optimizations matter. Performance characteristics discovered here inform architectural decisions throughout the STOM codebase.
