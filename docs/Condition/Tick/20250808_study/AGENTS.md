<!-- Parent: ../AGENTS.md -->
# 20250808 연구 자료 (Study Archive)

## Purpose
2025년 8월 8일 특정 시장 상황에 대한 심층 연구 자료를 보관하는 디렉토리. 특정 날짜의 시장 데이터를 기반으로 한 전략 개발 및 검증 과정을 문서화합니다.

## Overview
- **연구 날짜**: 2025년 8월 8일
- **전략 수**: 1개 연구 파일
- **목적**: 특정 시장 상황 분석 및 전략 개발
- **상태**: 연구 자료 보관
- **활용**: 유사 시장 상황 발생 시 참조

## Key Files

### `Condition_Study_Open_Breakout.md`
**시초가 돌파 전략 연구**
- 시가 갭 상황에서의 돌파 패턴 분석
- 09:00 개장 직후 가격 움직임 연구
- 시가총액별 돌파 성공률 차이 검증
- 체결강도와 거래량의 관계 분석

**연구 초점:**
1. 시초가 형성 메커니즘
2. 갭 상승 후 돌파 조건
3. 거짓 돌파 필터링 방법
4. 최적 진입 타이밍 결정

**주요 발견사항:**
- 시가총액이 클수록 돌파 신뢰도 높음
- 체결강도 150% 이상에서 돌파 성공률 증가
- 첫 3분 내 거래량이 일평균 10% 이상 필요
- 호가 스프레드가 좁을수록 추세 지속력 강함

## For AI Agents

### When Working with Study Files

1. **Understanding Study Context**
   - Study files represent specific date analysis
   - Findings may not generalize to all market conditions
   - Use as reference, not production strategy
   - Validate findings against broader datasets

2. **Research Methodology**
   ```
   Study Workflow:
   1. Identify specific market event/pattern
   2. Collect tick-level data for target date
   3. Analyze price action and indicators
   4. Document findings and patterns
   5. Test generalization on similar dates
   6. Incorporate learnings into main strategies
   ```

3. **Integration with Main Strategies**
   - Extract validated patterns
   - Test on broader time periods
   - Incorporate into existing condition files
   - Document origin in improvement research section

4. **Study File Characteristics**
   - Date-specific analysis (YYYYMMDD)
   - Exploratory research focus
   - May have incomplete optimization sections
   - Emphasis on pattern discovery over performance

5. **Creating New Study Files**
   ```markdown
   Naming: Condition_Study_[Description].md
   Location: docs/Condition/Tick/[YYYYMMDD]_study/
   Format: Standard template with additional research sections
   Focus: Pattern discovery and validation
   ```

### Critical Rules for Study Files

1. **Temporal Context**
   - Always include study date in documentation
   - Note market conditions (bullish/bearish/volatile)
   - Document unusual events (news, announcements)
   - Specify trading session characteristics

2. **Data Integrity**
   - Verify data completeness for study date
   - Check for anomalies or data gaps
   - Document data source and collection method
   - Validate against official exchange data

3. **Pattern Generalization**
   - Test pattern on multiple dates (±7 days)
   - Validate across different market conditions
   - Document generalization success rate
   - Note conditions where pattern fails

4. **Research Documentation**
   - Clear hypothesis statement
   - Detailed analysis methodology
   - Statistical validation of findings
   - Limitations and edge cases

5. **Production Integration**
   - Do not deploy study files directly to production
   - Extract validated patterns only
   - Test thoroughly on broader datasets
   - Document origin when incorporating into main strategies

### Study Analysis Framework

**Phase 1: Pattern Identification**
- Visual inspection of charts
- Anomaly detection in indicators
- Correlation analysis between variables
- Identification of potential entry/exit signals

**Phase 2: Hypothesis Formation**
- Articulate observed pattern as testable hypothesis
- Define measurable conditions
- Specify expected outcomes
- Identify required indicators

**Phase 3: Validation**
- Test on study date data
- Extend to adjacent dates (±3-7 days)
- Validate statistical significance
- Document success/failure conditions

**Phase 4: Integration Planning**
- Assess applicability to existing strategies
- Plan parameter ranges for optimization
- Design incremental rollout approach
- Prepare backtesting validation plan

### Research Quality Standards

**Minimum Requirements:**
- Clear research question or hypothesis
- Detailed methodology description
- Data analysis with visualizations (if applicable)
- Statistical validation of findings
- Limitations and caveats documented

**Best Practices:**
- Compare multiple dates with similar characteristics
- Use control dates to verify pattern uniqueness
- Document negative findings (what didn't work)
- Include reproducibility instructions
- Link to related production strategies

### Common Study Patterns

**Market Event Studies:**
- Opening surge analysis (09:00-09:10)
- Pre-close momentum shifts (14:50-15:00)
- Lunch volatility patterns (11:30-13:00)
- Post-news reaction timings

**Indicator Studies:**
- New indicator validation
- Indicator combination optimization
- Threshold determination for existing indicators
- Cross-indicator correlation analysis

**Strategy Evolution Studies:**
- Parameter sensitivity analysis
- Time window optimization
- Entry/exit condition refinement
- Filter effectiveness evaluation

## Dependencies

### Required Reading
- **Parent**: `../AGENTS.md` - Tick strategy overview
- **Template**: `docs/Guideline/Condition_Document_Template_Guideline.md`
- **Guideline**: `docs/Guideline/Back_Testing_Guideline_Tick.md`
- **Main Strategies**: `../1_To_be_reviewed/` and `../2_Under_review/`

### Data Sources
- **Study Database**: `_database/stock_tick_back.db`
- **Date Range**: 2025-08-08 (primary), ±7 days (validation)
- **Market Data**: Korean stock market (KRX)
- **Trading Hours**: 09:00-15:30 (regular session)

### Analysis Tools
- **Backtesting**: `backtester/backengine_stock_tick.py`
- **Visualization**: `ui/ui_draw_*.py` (chart rendering)
- **Statistics**: pandas, numpy for data analysis
- **Indicators**: TA-Lib custom wheel in `/utility/`

### Integration Targets
- Time-based strategies: `Condition_Tick_[HHMM]_*.md`
- Breakout strategies: `Condition_Tick_*_Breakout.md`
- Opening strategies: `Condition_Tick_Opening_*.md`
- Gap strategies: `Condition_Tick_Gap*.md`

## Statistics
- **Total Study Files**: 1
- **Study Date**: 2025-08-08
- **Research Focus**: Opening breakout patterns
- **Status**: Archived research
- **Integration Status**: Pending validation for production strategies

## Notes

### Study Context (2025-08-08)
- **Market Condition**: [Document when file is analyzed]
- **Index Movement**: [Document KOSPI/KOSDAQ performance]
- **Volatility Level**: [Document VIX or similar metric]
- **Notable Events**: [Document any significant news/events]

### Research Outcomes
1. **Validated Patterns**
   - Opening surge characteristics
   - Breakout confirmation signals
   - Volume threshold requirements

2. **Rejected Hypotheses**
   - [Document patterns that didn't validate]
   - [Note why certain indicators failed]

3. **Future Research Directions**
   - Expand date range for validation
   - Test pattern robustness across market conditions
   - Develop adaptive threshold mechanism
   - Integrate with existing opening strategies

### Integration Roadmap
1. **Immediate** (Week 1-2)
   - Validate findings on ±7 day window
   - Document generalization success rate
   - Prepare integration proposal

2. **Short-term** (Week 3-4)
   - Incorporate validated patterns into `Condition_Tick_900_920*.md`
   - Update optimization sections with new parameters
   - Run comprehensive backtesting

3. **Long-term** (Month 2+)
   - Monitor live performance
   - Collect additional study dates
   - Refine pattern conditions based on production feedback

### Directory Organization
```
20250808_study/
├── AGENTS.md (this file)
├── Condition_Study_Open_Breakout.md
└── [Future study files for this date]

Potential future structure:
20250808_study/
├── AGENTS.md
├── market_context.md (optional)
├── Condition_Study_Open_Breakout.md
├── Condition_Study_[Other_Pattern].md
└── analysis_results/ (optional subfolder)
```

### Related Research
- **Similar Studies**: Check `../1_To_be_reviewed/Condition_Study_*.md` series
- **AI Research**: See `../1_To_be_reviewed/Condition_Study_By_*.md` files
- **Production Examples**: Refer to `../2_Under_review/Condition_Tick_902_905_update_2.md`

### Best Practices for Future Studies
1. Create date-specific directories for major research efforts
2. Include market context documentation
3. Link findings to production strategy improvements
4. Archive negative results to avoid repeated research
5. Maintain clear connection to main strategy repository
