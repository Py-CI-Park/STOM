<!-- Parent: ../AGENTS.md -->
# PyTrader Trading Conditions

## Purpose
PyTrader 자동매매 프로그램의 실전 조건식 샘플 저장소. 검증된 실전 트레이딩 시스템의 조건식을 분석하여 STOM 전략 개발 시 참고자료로 활용합니다.

## Overview
- **Total files**: 7 files
- **Content types**: Real trading conditions, order book analysis, entry/exit logic
- **Formats**: Excel, Markdown, XML, Python, Text
- **Focus**: Proven real-world trading strategies
- **Market**: Korean stock market (Kiwoom API)

## Key Files

### Summary and Overview
- **PyTrader_Condition_Summary.xlsx** (Excel)
  - Comprehensive condition expression summary spreadsheet
  - Structured overview of all trading conditions
  - Quick reference for condition parameters

### Buy Condition Documentation
- **sell.md buy.mg 조건식 만들기 .txt** (Text)
  - Guide for creating buy/sell conditions
  - Condition expression construction methodology
  - Best practices for condition design

### Sell Condition Documentation
- **PyTrader_Sell_Condition.md** (Markdown)
  - Sell condition logic documentation
  - Exit signal generation rules
  - Risk management through sell conditions

- **PyTrader_Sell_Condition.py** (Python)
  - Python implementation of sell conditions
  - Executable sell logic code
  - Direct code reference for implementation

### Real Trading Conditions
- **PyTrader_Real_Condition.md** (Markdown)
  - Real production trading conditions in markdown format
  - Human-readable documentation with explanations
  - Key insights and rationale for each condition

- **PyTrader_Real_Condition.txt** (Text)
  - Original text format of real trading conditions
  - Raw condition expressions
  - Direct copy from PyTrader system

- **PyTrader_Real_Condition.xml** (XML)
  - Structured XML format of trading conditions
  - Machine-readable condition definitions
  - Hierarchical condition organization

## Key Insights from PyTrader

### Real-World Validation
- Conditions from proven trading system with real money
- Field-tested strategies with demonstrated effectiveness
- Practical risk management through condition filters

### Order Book Analysis Patterns
- 호가창 (order book) analysis techniques
- Bid/ask quantity imbalance detection
- Institutional activity pattern recognition
- Support/resistance level identification via order book

### Entry Signal Generation
- Multi-indicator confirmation strategies
- Price action + volume + order book confluence
- Momentum and trend strength validation
- Timing optimization for entry execution

### Exit Signal Logic
- Profit-taking strategies
- Stop-loss implementation
- Trailing stop mechanisms
- Time-based exits

### Risk Management
- Position sizing rules
- Maximum loss limits
- Correlation-based filtering
- Market condition filters

## For AI Agents

### Critical Guidelines

**DO:**
1. Use as **conceptual reference** and **inspiration source**
2. Extract **underlying principles** and **core logic**
3. Map PyTrader indicators to **STOM database variables**
4. Adapt conditions to **STOM framework architecture**
5. **Backtest rigorously** with STOM historical data
6. **Document lineage** - cite which PyTrader condition inspired STOM strategy
7. Follow **STOM condition template** format

**DO NOT:**
1. Copy-paste code directly without understanding
2. Assume PyTrader success = STOM success without validation
3. Use PyTrader-specific APIs or data structures directly
4. Skip backtesting because "it worked in PyTrader"
5. Ignore STOM framework patterns and conventions

### Integration Workflow

#### Step 1: Analysis
```
Read PyTrader condition → Understand core logic → Identify key indicators
```
- What market behavior is being detected?
- What are the quantitative criteria?
- What risk controls are implemented?

#### Step 2: Variable Mapping
```
PyTrader Variable → STOM Database Column
```

**Common Mappings:**
- PyTrader order book → STOM `매수총잔량`, `매도총잔량`, `매수잔량1~5`, `매도잔량1~5`
- PyTrader volume → STOM `초당거래대금`, `분당거래대금`, `거래대금`
- PyTrader strength → STOM `체결강도`, `체결강도평균`
- PyTrader price → STOM `현재가`, `시가`, `고가`, `저가`, `등락율`
- PyTrader indicators → STOM `이동평균`, `볼린저밴드`, `RSI`, etc.

**Reference:**
- STOM variables: `docs/Guideline/Stock_Database_Information.md`
- Tick variables: `docs/Guideline/Back_Testing_Guideline_Tick.md` (826 variables)
- Min variables: `docs/Guideline/Back_Testing_Guideline_Min.md` (752 variables)

#### Step 3: Prototype Implementation
```
Create minimal STOM condition → Implement BO/SO sections → Test syntax
```
- Use STOM condition document template
- Implement buy conditions (BO section)
- Implement sell conditions (SO section)
- Follow Korean variable naming convention
- Use self.vars[] for multi-variable access

#### Step 4: Backtesting Validation
```
Run backtest → Analyze results → Compare with expectations
```
- Use `backtester/backtest.py` for initial testing
- Test across multiple date ranges
- Validate with different market conditions
- Check performance metrics (win rate, profit factor, drawdown)

#### Step 5: Optimization
```
Define parameter ranges (BOR/SOR) → Run optimization → Select best parameters
```
- Create BOR (Buy Optimization Range) for grid search
- Create SOR (Sell Optimization Range)
- Use `backtester/optimiz.py` for optimization
- Consider OR (Overall Range) for top 10 variables
- Consider GAR (Genetic Algorithm Range) for complex optimization

#### Step 6: Documentation
```
Create full condition document → Include reference citation → Submit for review
```
- Follow template: `docs/Guideline/Condition_Document_Template_Guideline.md`
- Include sections: BO, BOR, SO, SOR, OR, GAR
- Document source: "Inspired by PyTrader [condition name]"
- Explain adaptations made for STOM framework

### Example Integration

**PyTrader Condition:**
```python
# 매수잔량 > 매도잔량 * 2 and 체결강도 > 150
```

**STOM Adaptation:**
```python
# BO Section
def 조건만족여부(vars):
    매수총잔량 = vars[10]
    매도총잔량 = vars[11]
    체결강도 = vars[15]

    if 매수총잔량 > 매도총잔량 * 2.0 and 체결강도 > 150:
        return True
    return False
```

**BOR Section (for optimization):**
```python
매수매도잔량비율 = [1.5, 3.0, 0.1]  # [min, max, step]
체결강도하한 = [100, 200, 10]
```

### Useful PyTrader Patterns

#### Pattern 1: Order Book Imbalance
```
Concept: Detect significant bid/ask imbalance
STOM Implementation: (매수총잔량 - 매도총잔량) / 매도총잔량 > threshold
Validation: Backtest with various threshold values
```

#### Pattern 2: Execution Strength Confirmation
```
Concept: Strong buying pressure indicated by 체결강도
STOM Implementation: 체결강도 > threshold and 체결강도평균 increasing
Validation: Test with different timeframes
```

#### Pattern 3: Volume Surge Detection
```
Concept: Abnormal volume increase signals institutional activity
STOM Implementation: 분당거래대금 > 분당거래대금평균 * ratio
Validation: Optimize ratio parameter
```

#### Pattern 4: Multi-Level Order Book Support
```
Concept: Strong support at multiple bid levels
STOM Implementation: sum(매수잔량1 to 매수잔량5) > threshold
Validation: Compare with historical support levels
```

## Validation Checklist

Before moving PyTrader-inspired strategy to production:

1. **Logic Validation**
   - [ ] Core concept understood and documented
   - [ ] Variable mappings verified against STOM database
   - [ ] Code syntax validated with `backtester/back_code_test.py`
   - [ ] Edge cases considered

2. **Backtesting Validation**
   - [ ] Tested on minimum 3-month historical data
   - [ ] Tested across different market conditions (bull/bear/sideways)
   - [ ] Win rate > 50% or profit factor > 1.5
   - [ ] Maximum drawdown acceptable (< 30%)
   - [ ] Sufficient number of trades (> 30 for statistical significance)

3. **Optimization Validation**
   - [ ] Parameter ranges defined (BOR/SOR)
   - [ ] Grid search completed
   - [ ] Optimal parameters selected
   - [ ] Walk-forward validation performed
   - [ ] No overfitting detected

4. **Documentation Validation**
   - [ ] Condition document created following template
   - [ ] BO, BOR, SO, SOR, OR, GAR sections complete
   - [ ] PyTrader source cited in documentation
   - [ ] Adaptation rationale explained
   - [ ] Compliance with 98.3% documentation guideline

5. **Risk Management Validation**
   - [ ] Position sizing rules defined
   - [ ] Stop-loss implemented
   - [ ] Maximum loss per trade acceptable
   - [ ] Correlation with existing strategies checked

## Dependencies

### Internal Dependencies
- **Variable Reference**: `docs/Guideline/Stock_Database_Information.md` - 108 stock tick columns
- **Tick Guideline**: `docs/Guideline/Back_Testing_Guideline_Tick.md` - 826 documented variables
- **Min Guideline**: `docs/Guideline/Back_Testing_Guideline_Min.md` - 752 documented variables
- **Template**: `docs/Guideline/Condition_Document_Template_Guideline.md`
- **Backtesting**: `backtester/backengine_stock_tick.py`, `backtester/backengine_stock_min.py`
- **Implementation**: `stock/kiwoom_strategy_tick.py`, `stock/kiwoom_strategy_min.py`

### External Dependencies
- **PyTrader System**: Original condition source (external)
- **Kiwoom API**: Data compatibility verification required
- **Market Data**: Sufficient historical data for backtesting

### Tool Dependencies
- **Python**: Condition logic implementation
- **SQLite**: Historical data access
- **Backtester**: Strategy validation
- **Optimizer**: Parameter tuning (grid search, genetic algorithm)

## Related Documentation
- **Parent**: `../AGENTS.md` - Reference folder overview
- **Sibling**: `../YouTube/AGENTS.md` - YouTube video references
- **Implementation**: `../../Tick/`, `../../Min/` - Where to place validated strategies
- **AI Ideas**: `../../Idea/` - Alternative strategy sources
- **Guidelines**: `../../../Guideline/` - Documentation standards

## Notes

### Strengths of PyTrader References
- **Real-world proven** - Conditions from live trading system
- **Complete logic** - Both buy and sell conditions documented
- **Multiple formats** - Excel, Markdown, XML, Python, Text
- **Practical focus** - Risk management and order book analysis
- **Korean market** - Tailored to Kiwoom API and Korean stock market

### Limitations and Caveats
- **Different architecture** - PyTrader != STOM framework
- **Data source differences** - May use different data providers
- **Timing differences** - Real-time execution vs. backtesting
- **API differences** - PyTrader API != Kiwoom API in STOM
- **Unknown parameters** - Some conditions may lack optimization history
- **Adaptation required** - Cannot use directly without modification

### Best Practices
1. **Study first** - Fully understand before implementing
2. **Map carefully** - Verify all variable mappings
3. **Test thoroughly** - Backtest extensively
4. **Document completely** - Maintain 98.3% compliance
5. **Cite sources** - Always reference PyTrader origin
6. **Iterate continuously** - Refine based on backtesting results
7. **Share learnings** - Document what worked and what didn't

### Common Pitfalls
- Assuming PyTrader conditions work as-is in STOM
- Ignoring market regime changes since condition was created
- Over-optimizing parameters to historical data
- Neglecting transaction costs and slippage
- Skipping walk-forward validation
- Not documenting adaptation rationale

## Statistics
- Total PyTrader files: 7
- Format distribution: Excel (1), Markdown (3), Python (1), XML (1), Text (2)
- Focus areas: Order book (100%), Entry signals (86%), Exit signals (71%)
- Implementation status: Reference only (not directly implemented)
- Validation status: Requires backtesting and adaptation

## Future Directions
- Extract more specific condition logic from Excel summary
- Create systematic PyTrader-to-STOM conversion framework
- Build pattern library from PyTrader conditions
- Track which PyTrader patterns perform best in STOM
- Expand PyTrader reference collection
- Create automated variable mapping tools
- Develop PyTrader condition parser for faster integration
