<!-- Parent: ../AGENTS.md -->
# YouTube Trading Video References

## Purpose
YouTube 트레이딩 강의 영상에서 추출한 호가창(order book) 분석 기법 문서화. 실전 트레이딩 전문가들의 인사이트를 정량화하여 STOM 전략 개발에 활용합니다.

## Overview
- **Total files**: 6 video transcript/analysis files
- **Content type**: Order book analysis techniques (호가창 분석)
- **Format**: Markdown transcripts with key insights
- **Focus**: Day trading survival tactics, institutional movement detection
- **Market**: Korean stock market (Kiwoom exchange)

## Key Files

### 1. 단타매매 호가창으로 살아남기 - 하락전에 호가창과 차트의 형태.md
**Topic**: Pre-decline order book and chart patterns
**Key Focus**: Warning signs before price drops
**Useful For:**
- Detecting early warning signals before price collapse
- Identifying institutional selling patterns
- Risk management through pattern recognition
- Exit timing optimization

**Core Concepts:**
- Pre-decline order book characteristics
- Chart pattern + order book confluence
- Institutional distribution signals
- Defensive trading tactics

### 2. 밥먹고 호가창만 연구했습니다.md
**Topic**: Dedicated order book research
**Key Focus**: Full-time order book analysis insights
**Useful For:**
- Deep order book pattern understanding
- Professional-level order book reading
- Real-time decision-making frameworks
- Market microstructure insights

**Core Concepts:**
- Order book dynamics and flow
- Bid/ask wall interpretation
- Liquidity analysis techniques
- Real-time pattern recognition

### 3. 세력의 움직임을 확인하는 호가창 분석법 , 모르면 손해봅니다.md
**Topic**: Detecting institutional movements
**Key Focus**: Order book patterns revealing big player activity
**Useful For:**
- Identifying institutional accumulation/distribution
- Detecting smart money movements
- Following institutional footprints
- Avoiding liquidity traps

**Core Concepts:**
- 세력 (institutional player) identification
- Non-retail trading pattern detection
- Coordinated order book manipulation
- Volume profile analysis

### 4. 실전에서 호가창 분석은 주식트레이더를 죽이고 살립니다 - 단타매매영상.md
**Topic**: Critical order book analysis for day trading
**Key Focus**: Life-or-death importance of order book reading
**Useful For:**
- Day trading survival tactics
- Real-time execution decisions
- Risk management in fast markets
- Scalping and momentum trading

**Core Concepts:**
- High-stakes trading decisions
- Real-time order book interpretation
- Execution timing optimization
- Day trader survival strategies

### 5. 주식호가창보는법 호가창매매 분석 비법 다알려드림.md
**Topic**: Order book reading methods and trading secrets
**Key Focus**: Comprehensive order book analysis techniques
**Useful For:**
- Learning systematic order book analysis
- Understanding bid/ask dynamics
- Pattern recognition training
- Building order book intuition

**Core Concepts:**
- Systematic order book reading framework
- Multiple timeframe order book analysis
- Order book + price action integration
- Trading secret methodologies

### 6. 확실한 호가창 분석법! 공짜로 2% 매일 먹는자리 공개 #주식강의#주식단테#호가창분석.md
**Topic**: Reliable 2% daily profit strategy
**Key Focus**: Specific order book patterns for consistent gains
**Useful For:**
- Systematic profit generation
- Repeatable trading patterns
- Consistency in day trading
- Low-risk high-probability setups

**Core Concepts:**
- 2% daily target methodology
- High-probability order book setups
- Consistent pattern exploitation
- Risk-reward optimization

## Key Insights from YouTube Videos

### Common Themes Across Videos

#### 1. Order Book Imbalance (호가 불균형)
**Concept**: Significant difference between bid and ask quantities signals directional pressure

**STOM Variables:**
- `매수총잔량` - Total bid quantity across all levels
- `매도총잔량` - Total ask quantity across all levels
- `매수잔량1~5` - Individual bid level quantities
- `매도잔량1~5` - Individual ask level quantities

**Quantification:**
```python
imbalance_ratio = (매수총잔량 - 매도총잔량) / 매도총잔량
# Bullish: imbalance_ratio > 0.5
# Bearish: imbalance_ratio < -0.5
```

#### 2. Bid/Ask Wall Detection (매수벽/매도벽)
**Concept**: Large quantities at specific price levels indicate institutional positioning

**STOM Variables:**
- `매수호가1~5` - Bid prices at each level
- `매수잔량1~5` - Bid quantities at each level
- `매도호가1~5` - Ask prices at each level
- `매도잔량1~5` - Ask quantities at each level

**Quantification:**
```python
# Bid wall: 매수잔량1 > avg(매수잔량2~5) * 3
# Ask wall: 매도잔량1 > avg(매도잔량2~5) * 3
# Support: Persistent large bid quantities
# Resistance: Persistent large ask quantities
```

#### 3. Institutional Activity (세력 움직임)
**Concept**: Coordinated large orders reveal institutional presence

**STOM Variables:**
- `초당매수수량` - Per-second buy quantity
- `초당매도수량` - Per-second sell quantity
- `체결강도` - Execution strength (buy pressure vs. sell pressure)
- `체결강도평균` - Average execution strength

**Quantification:**
```python
# Institutional buying: 체결강도 > 200 and 초당매수수량 increasing
# Institutional selling: 체결강도 < 50 and 초당매도수량 increasing
```

#### 4. Pre-Movement Warning Signals (사전 신호)
**Concept**: Order book changes precede price movements

**STOM Variables:**
- `호가스프레드` - Bid-ask spread
- `매수총잔량` / `매도총잔량` dynamics
- Rate of change in order book quantities

**Quantification:**
```python
# Spread compression: 호가스프레드 decreasing while volume increasing
# Imbalance shift: Rapid change in 매수총잔량/매도총잔량 ratio
```

#### 5. Real-Time Order Flow (실시간 호가 흐름)
**Concept**: Continuous order book monitoring reveals market sentiment

**STOM Variables:**
- `초당체결수량` - Per-second execution quantity
- `초당거래대금` - Per-second trading value
- `분당거래대금` - Per-minute trading value
- Velocity of order book changes

**Quantification:**
```python
# Surge detection: 초당거래대금 > 분당거래대금평균 * 2
# Flow direction: 초당매수수량 vs. 초당매도수량
```

## For AI Agents

### Critical Guidelines

**DO:**
1. **Extract quantifiable patterns** - Convert qualitative observations to code
2. **Validate with data** - Test patterns against historical order book data
3. **Combine with price action** - Order book alone is insufficient
4. **Consider execution costs** - High-frequency signals may not be profitable after costs
5. **Document thoroughly** - Cite which video and timestamp inspired pattern
6. **Backtest rigorously** - YouTube success stories may not translate to systematic trading
7. **Adapt to STOM framework** - Use available database variables

**DO NOT:**
1. **Believe claims uncritically** - "2% daily" claims require validation
2. **Copy-paste ideas** - Videos are qualitative, code requires quantification
3. **Ignore market context** - Patterns work differently in different market regimes
4. **Skip backtesting** - Never implement without historical validation
5. **Forget transaction costs** - Order book patterns may require frequent trading
6. **Rely on single patterns** - Combine multiple confirmations
7. **Ignore risk management** - Videos may omit risk controls

### Integration Workflow

#### Step 1: Video Content Analysis
```
Watch video → Extract core concepts → Identify key patterns
```
- What specific order book behavior is described?
- What are the visual/numerical indicators?
- What timeframe is being discussed?
- What market conditions does this work in?

#### Step 2: Pattern Quantification
```
Qualitative observation → Mathematical expression → STOM variables
```

**Example:**
- Video: "매수잔량이 매도잔량보다 월등히 많을 때 매수"
- Quantification: `매수총잔량 > 매도총잔량 * threshold`
- STOM vars: `vars[10]` (매수총잔량), `vars[11]` (매도총잔량)
- Threshold: Optimize via backtesting

#### Step 3: Multi-Indicator Confirmation
```
Order book pattern + Price action + Volume → Confluence signal
```

**Framework:**
```python
def video_pattern_signal(vars):
    # Order book component (from YouTube)
    order_book_bullish = 매수총잔량 > 매도총잔량 * 1.5

    # Price action confirmation
    price_trending_up = 현재가 > 이동평균5

    # Volume confirmation
    volume_surge = 분당거래대금 > 분당거래대금평균 * 1.2

    # Confluence
    if order_book_bullish and price_trending_up and volume_surge:
        return True
    return False
```

#### Step 4: Backtesting Validation
```
Implement in STOM → Run backtest → Analyze performance → Iterate
```
- Test pattern in isolation
- Test with confirmations
- Test across different time periods
- Test in different market conditions
- Measure win rate, profit factor, drawdown

#### Step 5: Optimization
```
Define parameter ranges → Grid search → Walk-forward validation
```
- Identify key thresholds mentioned in video
- Define reasonable ranges (BOR/SOR sections)
- Optimize systematically
- Validate out-of-sample

#### Step 6: Documentation
```
Create condition document → Cite video source → Explain adaptations
```
- Follow STOM condition template
- Include video title and key timestamp
- Document quantification methodology
- Explain why certain thresholds were chosen

### Example Integration: "2% Daily Strategy"

**Video Claim**: Specific order book patterns can yield 2% daily profit

**AI Agent Process:**
1. **Extract Pattern**:
   - Large bid wall at current price level
   - Decreasing ask quantities
   - Execution strength > 150
   - Price near day low

2. **Quantify**:
```python
# BO Section
매수잔량1 > 평균매수잔량 * 3.0  # Bid wall
매도총잔량 < 매도총잔량[1분전] * 0.8  # Ask exhaustion
체결강도 > 150  # Buying pressure
등락율 < -2.0 and 등락율 > -5.0  # Near day low but not panic
```

3. **Backtest**: Test if this actually yields 2% average gain

4. **Result**: Likely finds:
   - Win rate may be 55-65% (not 100% as video implies)
   - Average gain per trade: 0.5-1.5% (not 2%)
   - Requires tight risk management (stop-loss at -1%)
   - Works better in certain market conditions

5. **Document**:
   - Cite video as inspiration
   - Document actual backtested performance
   - Explain deviations from video claims
   - Include optimization parameters

### Critical Variables for YouTube Pattern Implementation

**From STOM Stock Database** (`stock_tick_back.db`):

**Order Book Core:**
- `매수총잔량` - Total bid quantity (sum of all bid levels)
- `매도총잔량` - Total ask quantity (sum of all ask levels)
- `매수잔량1` to `매수잔량5` - Bid quantities at levels 1-5
- `매도잔량1` to `매도잔량5` - Ask quantities at levels 1-5
- `매수호가1` to `매수호가5` - Bid prices at levels 1-5
- `매도호가1` to `매도호가5` - Ask prices at levels 1-5
- `호가스프레드` - Bid-ask spread

**Execution Strength:**
- `체결강도` - Current execution strength (매수 vs. 매도 pressure)
- `체결강도평균` - Average execution strength over period

**Volume Metrics:**
- `초당체결수량` - Per-second execution quantity
- `초당거래대금` - Per-second trading value
- `초당매수수량` - Per-second buy quantity
- `초당매도수량` - Per-second sell quantity
- `분당거래대금` - Per-minute trading value

**Price Action:**
- `현재가` - Current price
- `시가` - Open price
- `고가` - High price
- `저가` - Low price
- `등락율` - Price change percentage

**Reference Documentation:**
- Full variable list: `docs/Guideline/Stock_Database_Information.md`
- Tick strategy variables: `docs/Guideline/Back_Testing_Guideline_Tick.md` (826 variables)
- Min strategy variables: `docs/Guideline/Back_Testing_Guideline_Min.md` (752 variables)

### Common YouTube Pattern Types

#### Pattern Type 1: Bid Wall Accumulation
**Video Description**: "큰 매수벽이 형성되면 매수"
**Quantification**:
```python
매수잔량1 > threshold_absolute  # e.g., > 10000 shares
매수잔량1 > avg(매수잔량2~5) * ratio  # e.g., ratio = 3.0
매수잔량1 persistent over time  # Wall doesn't disappear
```
**Optimization**: `threshold_absolute`, `ratio`

#### Pattern Type 2: Ask Wall Exhaustion
**Video Description**: "매도 잔량이 계속 줄어들 때 매수 타이밍"
**Quantification**:
```python
매도총잔량[now] < 매도총잔량[1분전] * 0.8
매도총잔량[now] < 매도총잔량[2분전] * 0.7
체결강도 > 120  # Buying pressure increasing
```
**Optimization**: Lookback periods, thresholds

#### Pattern Type 3: Imbalance Surge
**Video Description**: "매수 잔량이 갑자기 매도 잔량을 압도할 때"
**Quantification**:
```python
current_imbalance = (매수총잔량 - 매도총잔량) / 매도총잔량
previous_imbalance = calculate_previous()
if current_imbalance > threshold and current_imbalance > previous_imbalance * 2:
    signal = True
```
**Optimization**: `threshold`, imbalance ratio

#### Pattern Type 4: Institutional Footprint
**Video Description**: "세력의 큰 손이 들어올 때 따라 매수"
**Quantification**:
```python
초당매수수량 > threshold_high  # Large per-second buying
초당매수수량 sustained over multiple seconds
체결강도 > 180  # Strong buying pressure
매수잔량1 > avg * 2  # Bid support
```
**Optimization**: Thresholds for size and duration

#### Pattern Type 5: Spread Compression
**Video Description**: "스프레드가 좁아지면서 거래량이 증가하면 직전 신호"
**Quantification**:
```python
호가스프레드 decreasing
초당거래대금 increasing
호가스프레드 < avg_spread * 0.5
분당거래대금 > 분당거래대금평균 * 1.5
```
**Optimization**: Compression ratio, volume threshold

## Validation Framework

### Pattern Validation Checklist

Before implementing YouTube-inspired pattern:

1. **Conceptual Validation**
   - [ ] Core concept makes logical sense
   - [ ] Mechanism of action understood (why it works)
   - [ ] Market conditions identified (when it works)
   - [ ] Risk factors recognized (when it fails)

2. **Quantification Validation**
   - [ ] Qualitative pattern converted to mathematical expression
   - [ ] All required STOM variables available
   - [ ] Thresholds and parameters defined
   - [ ] Edge cases considered

3. **Implementation Validation**
   - [ ] Code syntax validated with `backtester/back_code_test.py`
   - [ ] Variable access patterns correct (`self.vars[]`)
   - [ ] Korean variable names preserved
   - [ ] Logic flow tested manually

4. **Backtesting Validation**
   - [ ] Tested on minimum 3-month data
   - [ ] Multiple market conditions (trending/ranging)
   - [ ] Win rate documented
   - [ ] Profit factor > 1.5
   - [ ] Maximum drawdown acceptable
   - [ ] Transaction costs included

5. **Optimization Validation**
   - [ ] Parameter ranges defined (BOR/SOR)
   - [ ] Grid search or genetic algorithm applied
   - [ ] Walk-forward validation performed
   - [ ] Overfitting checked (out-of-sample testing)
   - [ ] Optimal parameters reasonable

6. **Documentation Validation**
   - [ ] Condition document created
   - [ ] Video source cited (title, timestamp)
   - [ ] Quantification methodology explained
   - [ ] Backtest results documented
   - [ ] Compliance with 98.3% guideline

7. **Risk Management Validation**
   - [ ] Stop-loss implemented
   - [ ] Position sizing defined
   - [ ] Maximum loss per trade acceptable
   - [ ] Risk-reward ratio > 2:1
   - [ ] Correlation with existing strategies checked

### Performance Expectations

**Reality Check**: YouTube claims vs. systematic trading reality

| Video Claim | Typical Backtest Reality | Reason for Difference |
|------------|-------------------------|----------------------|
| "2% daily profit" | 0.3-0.8% average per trade | Cherry-picked examples, survivorship bias |
| "90% win rate" | 55-65% win rate | Hindsight bias, selective memory |
| "Works every time" | Works in specific conditions | Market regime dependency |
| "Never lose" | Drawdowns 10-30% | Risk management required |
| "Simple pattern" | Requires multiple confirmations | Complexity in execution |

**Key Insight**: Use videos for **inspiration and concepts**, not **performance expectations**.

## Dependencies

### Internal Dependencies
- **Variable Reference**: `docs/Guideline/Stock_Database_Information.md` (108 columns)
- **Tick Guideline**: `docs/Guideline/Back_Testing_Guideline_Tick.md` (826 variables)
- **Min Guideline**: `docs/Guideline/Back_Testing_Guideline_Min.md` (752 variables)
- **Template**: `docs/Guideline/Condition_Document_Template_Guideline.md`
- **Backtesting**: `backtester/backengine_stock_tick.py` (order book data required)
- **Implementation**: `stock/kiwoom_strategy_tick.py` (real-time order book access)

### External Dependencies
- **YouTube Videos**: Original content source (requires internet for video access)
- **Korean Language**: Understanding Korean required for video comprehension
- **Market Context**: Korean stock market specific (Kiwoom exchange)
- **Order Book Data**: Historical order book data in STOM database

### Tool Dependencies
- **Video Player**: For reviewing video content
- **Korean-English Dictionary**: For technical term translation
- **Backtester**: For pattern validation
- **Optimizer**: For parameter tuning

## Related Documentation
- **Parent**: `../AGENTS.md` - Reference folder overview
- **Sibling**: `../PyTrader/AGENTS.md` - PyTrader condition references
- **Implementation**: `../../Tick/`, `../../Min/` - Where to place validated strategies
- **AI Ideas**: `../../Idea/` - Alternative strategy sources
- **Guidelines**: `../../../Guideline/` - Documentation standards

## Notes

### Strengths of YouTube References
- **Real-world insights** - From experienced traders
- **Visual patterns** - Easier to understand than text
- **Practical focus** - Day trading survival tactics
- **Market-specific** - Korean market order book dynamics
- **Free knowledge** - Accessible educational content
- **Diverse perspectives** - Multiple traders' viewpoints

### Limitations and Caveats
- **Qualitative descriptions** - Requires quantification for systematic trading
- **Cherry-picked examples** - Videos show best-case scenarios
- **Hindsight bias** - Patterns clear in hindsight, unclear in real-time
- **No statistical validation** - Claims not backtested systematically
- **Marketing component** - Videos may oversell effectiveness
- **Execution differences** - Manual trading ≠ algorithmic trading
- **Data availability** - Not all patterns have sufficient data for backtesting

### Best Practices
1. **Validate everything** - Never trust claims without backtesting
2. **Quantify systematically** - Convert patterns to code
3. **Combine confirmations** - Use multiple indicators
4. **Test extensively** - Multiple time periods and conditions
5. **Document sources** - Cite video and timestamp
6. **Manage expectations** - Real performance < video claims
7. **Iterate continuously** - Refine based on results

### Common Pitfalls
- Believing "2% daily" claims without validation
- Implementing single patterns without confirmations
- Ignoring transaction costs and slippage
- Overfitting to recent market conditions
- Not documenting quantification methodology
- Skipping out-of-sample testing
- Forgetting risk management

### Integration Success Factors
1. **Critical thinking** - Question all claims
2. **Mathematical rigor** - Quantify precisely
3. **Statistical validation** - Backtest thoroughly
4. **Risk awareness** - Implement stop-losses
5. **Documentation discipline** - Maintain 98.3% compliance
6. **Continuous learning** - Iterate based on results

## Statistics
- Total YouTube reference files: 6
- Order book focus: 100% (all videos about 호가창)
- Day trading focus: 83% (5 of 6 videos)
- Institutional detection: 50% (3 of 6 videos)
- Performance claims: 100% (all make profitability claims)
- Validated in STOM: 0% (requires quantification and backtesting)
- Quantification difficulty: High (qualitative to quantitative conversion required)

## Future Directions
- Expand YouTube video reference library
- Create systematic pattern extraction framework
- Build quantification templates for common patterns
- Track which video patterns perform best after backtesting
- Develop automated video transcript analysis
- Create pattern recognition benchmark database
- Validate cross-video pattern consistency
- Build community-contributed pattern library
- Develop real-time order book pattern detection alerts
- Create educational content bridging YouTube insights and STOM implementation
