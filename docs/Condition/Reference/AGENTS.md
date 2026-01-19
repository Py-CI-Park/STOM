<!-- Parent: ../AGENTS.md -->
# External Strategy References

## Purpose
외부 트레이딩 전략 참고 자료 저장소. PyTrader 조건식 샘플과 YouTube 호가창 분석 영상 내용을 문서화하여 전략 개발 시 참고자료로 활용합니다.

## Overview
- **Total files**: 13 files
- **Sources**: PyTrader (7 files), YouTube (6 files)
- **Content types**: Real trading conditions, order book analysis, practical trading tips
- **Purpose**: External validation, strategy inspiration, market insight

## Subdirectories

### PyTrader/ (7 files)
PyTrader 자동매매 프로그램의 실전 조건식 샘플 및 분석.

**Files:**
- `PyTrader_Condition_Summary.xlsx` - 조건식 요약 스프레드시트
- `PyTrader_Real_Condition.md` - 실전 조건식 문서화 (마크다운)
- `PyTrader_Real_Condition.txt` - 실전 조건식 원본 (텍스트)
- `PyTrader_Real_Condition.xml` - 실전 조건식 XML 포맷
- `PyTrader_Sell_Condition.md` - 매도 조건식 문서화
- `PyTrader_Sell_Condition.py` - 매도 조건식 Python 구현
- `sell.md buy.mg 조건식 만들기 .txt` - 매수/매도 조건식 작성 가이드

**Key insights:**
- Real-world trading conditions from proven system
- Order book (호가창) analysis patterns
- Entry/exit signal generation
- Risk management through condition filters
- Multi-timeframe confirmation strategies

### YouTube/ (6 files)
YouTube 트레이딩 강의 영상에서 추출한 호가창 분석 기법 문서화.

**Files:**
- `단타매매 호가창으로 살아남기 - 하락전에 호가창과 차트의 형태.md`
  - Topic: Pre-decline order book and chart patterns
  - Focus: Warning signs before price drops

- `밥먹고 호가창만 연구했습니다.md`
  - Topic: Dedicated order book research
  - Focus: Full-time order book analysis insights

- `세력의 움직임을 확인하는 호가창 분석법 , 모르면 손해봅니다.md`
  - Topic: Detecting institutional movements
  - Focus: Order book patterns revealing big player activity

- `실전에서 호가창 분석은 주식트레이더를 죽이고 살립니다 - 단타매매영상.md`
  - Topic: Critical order book analysis for day trading
  - Focus: Life-or-death importance of order book reading

- `주식호가창보는법 호가창매매 분석 비법 다알려드림.md`
  - Topic: Order book reading methods and trading secrets
  - Focus: Comprehensive order book analysis techniques

- `확실한 호가창 분석법! 공짜로 2% 매일 먹는자리 공개 #주식강의#주식단테#호가창분석.md`
  - Topic: Reliable 2% daily profit strategy
  - Focus: Specific order book patterns for consistent gains

**Key insights:**
- Order book imbalance detection (호가 불균형)
- Bid/ask wall identification (매수벽/매도벽)
- Institutional activity patterns (세력 움직임)
- Pre-movement warning signals (사전 신호)
- Real-time order flow analysis (실시간 호가 흐름)
- Day trading survival tactics (단타 생존 전략)

## For AI Agents

### Using External References
1. **Inspiration, not copy-paste** - Use as conceptual reference, not direct implementation
2. **Validate independently** - External strategies may not work in STOM framework
3. **Adapt to STOM variables** - Map external indicators to available database columns
4. **Backtest rigorously** - External success ≠ guaranteed success in our system
5. **Document sources** - Always cite which reference inspired which strategy

### When Incorporating Reference Ideas
1. **Read and understand** - Fully comprehend the external strategy logic
2. **Identify core concepts** - Extract the underlying principles
3. **Map to STOM data** - Determine which database variables can implement the concept
4. **Create prototype** - Implement minimal version in STOM condition format
5. **Backtest validation** - Test with historical data
6. **Document lineage** - Note in condition document which reference inspired it
7. **Follow template** - Convert to standard condition document format

### PyTrader Integration
**Useful for:**
- Real trading condition validation
- Order book analysis patterns
- Entry/exit signal logic
- Risk management approaches
- Multi-indicator confirmation systems

**Limitations:**
- Different platform architecture
- May use different data sources
- Trading engine differences
- Need adaptation to Kiwoom API

**How to use:**
```
1. Study PyTrader condition logic
2. Identify key indicators and thresholds
3. Map to STOM database columns:
   - PyTrader order book → STOM 호가정보
   - PyTrader volume → STOM 초당거래대금/분당거래대금
   - PyTrader strength → STOM 체결강도
4. Implement in STOM condition format
5. Backtest with STOM data
6. Refine based on results
```

### YouTube Video Content Integration
**Useful for:**
- Order book pattern recognition (호가창 패턴)
- Institutional behavior detection (세력 움직임)
- Pre-movement signal identification (사전 신호 감지)
- Real-world trading psychology
- Market timing techniques

**How to use:**
```
1. Extract core order book patterns from video
2. Define quantitative criteria:
   - Bid wall: 매수총잔량 > threshold
   - Ask wall: 매도총잔량 > threshold
   - Imbalance: (매수총잔량 - 매도총잔량) / 매도총잔량
3. Implement in condition logic
4. Test pattern effectiveness
5. Combine with price/volume confirmations
```

### Critical Variables for Order Book Analysis
From STOM database (stock_tick_back.db):
- `매수총잔량` - Total bid quantity
- `매도총잔량` - Total ask quantity
- `매수잔량1~5` - Bid quantity at each level
- `매도잔량1~5` - Ask quantity at each level
- `매수호가1~5` - Bid prices
- `매도호가1~5` - Ask prices
- `호가스프레드` - Bid-ask spread
- `초당매수수량` - Per-second buy quantity
- `초당매도수량` - Per-second sell quantity
- `체결강도` - Execution strength

### Quality Assessment for External References
**Evaluation criteria:**
1. **Theoretical soundness** - Does the logic make sense?
2. **Data availability** - Can we access required data in STOM?
3. **Quantifiable criteria** - Can we convert qualitative observations to code?
4. **Backtestability** - Can we test it objectively?
5. **Real-world practicality** - Is it executable in live trading?
6. **Risk-reward ratio** - Does it offer acceptable risk/reward?

## Integration Workflow

### From Reference to Production
```
1. External Reference Discovery (PyTrader/YouTube)
   ↓
2. Concept Extraction
   ↓
3. STOM Variable Mapping
   ↓
4. Prototype Implementation
   ↓
5. Backtesting Validation
   ↓
6. Refinement & Optimization
   ↓
7. Documentation (with reference citation)
   ↓
8. Move to Tick/Min folders
```

## Order Book Analysis Patterns (from YouTube)

### Common Patterns Documented
1. **Bid Wall Formation** (매수벽 형성)
   - Large bid quantities at specific price levels
   - Institutional accumulation signal
   - Support level identification

2. **Ask Wall Exhaustion** (매도벽 소진)
   - Gradual reduction of ask quantities
   - Pre-breakout indicator
   - Resistance weakening signal

3. **Order Imbalance** (호가 불균형)
   - Significant difference between bid/ask quantities
   - Directional momentum indicator
   - Short-term price movement predictor

4. **Spread Compression** (스프레드 압축)
   - Narrowing bid-ask spread
   - Pre-movement signal
   - Liquidity concentration indicator

5. **Institutional Footprints** (세력 흔적)
   - Repeated large orders at specific levels
   - Coordinated bid/ask movements
   - Non-retail trading patterns

## Dependencies
- **STOM Variables**: `docs/Guideline/Stock_Database_Information.md`
- **Condition Template**: `docs/Guideline/Condition_Document_Template_Guideline.md`
- **Backtesting**: `backtester/backengine_*.py`
- **Implementation**: `stock/kiwoom_strategy_*.py`

## Related Documentation
- Parent: `../README.md` - Condition folder overview
- Implementation: `../Tick/`, `../Min/` - Where to implement validated ideas
- AI Ideas: `../Idea/` - Alternative strategy source
- Guidelines: `../../Guideline/` - Documentation standards

## Notes
- **External validation** - References show what works in real markets
- **Adaptation required** - Cannot use directly, must adapt to STOM
- **Backtesting mandatory** - All external ideas must be validated
- **Order book focus** - Strong emphasis on 호가창 analysis
- **Practical insights** - Real-world trading experience embedded
- **Korean market specific** - References tailored to Korean stock market
- **Citation required** - Always document which reference inspired strategy
- **Continuous updates** - Add new references as discovered

## Statistics
- Total reference files: 13
- PyTrader conditions: 7 (54%)
- YouTube videos: 6 (46%)
- Order book focused: 12 (92%)
- Implemented in STOM: 0 (requires validation)
- Under evaluation: 13 (100%)

## Future Directions
- Add more external reference sources
- Create systematic evaluation framework
- Track which references led to successful strategies
- Build reference pattern library
- Develop automated reference-to-condition conversion tools
- Expand YouTube video transcription coverage
- Add international trading references
- Create reference effectiveness metrics
