<!-- Parent: ../AGENTS.md -->
# 1단계: 검토 대기 (To Be Reviewed)

## Purpose
초기 작성 완료되어 검토 대기 중인 1분봉 트레이딩 전략 조건식 저장소. 기본 문서 구조와 조건식 코드가 작성되었으나, 백테스팅 검증 및 최적화 파라미터 확정이 필요한 단계입니다.

## Overview
- **전체 조건식**: 45개 (90%)
- **상태**: 초기 작성 완료, 백테스팅 검증 대기
- **문서 품질**: 가이드라인 준수 (BO/BOR/SO/SOR/OR/GAR 섹션 포함)
- **다음 단계**: 백테스팅 실행 → 결과 분석 → 파라미터 조정 → 2_Under_review/ 이동

## Key Files

### MACD-Based Strategies (5 files)
- `Condition_MACD_GoldenCross.md` - MACD 골든크로스 기본 패턴
- `Condition_MACD_Golden_Cross.md` - MACD 골든크로스 변형
- `Condition_Min_MACD_Cross.md` - MACD 크로스오버 + RSI 필터 복합 전략
- `Condition_Min_MACD_Divergence.md` - MACD 다이버전스 포착
- `Condition_Min_MACD_Histogram.md` - MACD 히스토그램 패턴 분석

### RSI-Based Strategies (4 files)
- `Condition_RSI_Oversold_Rebound.md` - RSI 과매도 구간 리바운드
- `Condition_Min_RSI_Divergence.md` - 가격-RSI 다이버전스 매매
- `Condition_Min_RSI_Oversold.md` - RSI 과매도 반등 전략
- `Condition_Min_RSI_Reversal.md` - RSI 반전 패턴 포착

### Bollinger Bands (6 files)
- `Condition_Bollinger_Reversal.md` - 볼린저 밴드 반전 전략
- `Condition_Min_BB_Squeeze.md` - 변동성 수축(Squeeze) 후 돌파
- `Condition_Min_Bollinger_Breakout_Strategy.md` - BBand 상단 돌파 전략
- `Condition_Min_Bollinger_Bounce.md` - BBand 하단 반등 전략
- `Condition_Min_Bollinger_Width.md` - BBand 폭 분석 전략
- `Condition_Min_BB_RSI_Combo.md` - BBand + RSI 복합 전략

### Moving Average Strategies (5 files)
- `Condition_MA_Alignment_Momentum.md` - 이동평균 정배열 + 모멘텀
- `Condition_Min_MA_Convergence.md` - 이동평균 수렴 후 발산
- `Condition_Min_Multi_MA_Cross.md` - 다중 MA 크로스오버
- `Condition_Min_MA_GoldenCross.md` - MA 골든크로스 전략
- `Condition_Min_MA_Support.md` - MA 지지선 활용 전략

### Volume-Based Strategies (4 files)
- `Condition_Min_Volume_Breakout.md` - 거래량 급증 + 가격 돌파
- `Condition_Min_Volume_Momentum.md` - 거래량 모멘텀 추종
- `Condition_Min_Volume_Weighted.md` - 거래량 가중 분석
- `Condition_Min_Volume_Price_Action.md` - 거래량-가격 동행 분석

### Stochastic Strategies (3 files)
- `Condition_Min_Stochastic_Cross.md` - Stochastic %K/%D 크로스
- `Condition_Min_Stochastic_Oversold.md` - Stochastic 과매도 반등
- `Condition_Min_Stochastic_Divergence.md` - Stochastic 다이버전스

### Multi-Indicator Strategies (3 files)
- `Condition_Min_900_1000_BB_RSI.md` - 09:00~10:00 BBand + RSI 전략
- `Condition_Min_MultiIndicator_Composite.md` - 다중 지표 종합 전략
- `Condition_Min_Multi_Indicator_Fusion.md` - 지표 융합 시스템

### Special Indicators (7 files)
- `Condition_Min_ADX_TrendStrength.md` - ADX 추세 강도 측정
- `Condition_Min_ATR_Breakout.md` - ATR 변동성 돌파 전략
- `Condition_Min_CCI_Extreme.md` - CCI 극단값 매매
- `Condition_Min_MFI_MoneyFlow.md` - MFI 자금 흐름 분석
- `Condition_Min_ROC_Momentum.md` - ROC 변화율 모멘텀
- `Condition_Min_WilliamsR_Oversold.md` - Williams %R 과매도
- `Condition_Min_Ichimoku_Cloud.md` - 일목균형표 전략

### Pattern & Trend Strategies (6 files)
- `Condition_Gap_Up_Breakout.md` - 갭상승 돌파 전략
- `Condition_Min_Candle_Pattern.md` - 캔들 패턴 인식 전략
- `Condition_Min_SAR_Reversal.md` - Parabolic SAR 반전
- `Condition_Min_Trend_Following.md` - 추세 추종 전략
- `Condition_Min_Support_Resistance.md` - 지지/저항 브레이크아웃
- `Condition_Min_Price_Action.md` - 프라이스 액션 전략

### Research & Exploration (2 files)
- `Condition_Find_1_Min.md` - 분봉 종합 탐색 전략
- `Condition_Min_0930_1000_Trend.md` - 09:30~10:00 추세 전략

## For AI Agents

### Primary Responsibilities
1. **Document Quality Assurance**
   - Verify all 6 sections present: Overview, Buy Conditions, Sell Conditions, BO/BOR, SO/SOR, OR/GAR
   - Check Korean variable names preserved: 분봉시가, 분봉고가, 분봉저가, 분봉종가
   - Ensure TA-Lib indicators properly documented: MACD, RSI, BBand, Stochastic, etc.
   - Validate optimization section format: BO (actual values), BOR (ranges), OR (top 10 only)

2. **Backtesting Preparation**
   - Confirm condition code is executable Python
   - Verify variable names match `stock_min_back.db` schema (108 columns)
   - Check time-based branching logic (시분초 < 93000, < 110000, etc.)
   - Validate indicator calculation references (MACDN(1), RSIN(1), etc.)

3. **Review Workflow Management**
   - When backtesting starts: Move to `2_Under_review/`
   - Track files with incomplete optimization sections
   - Flag strategies with over-optimization risk (too many indicators)
   - Monitor documentation compliance rate (maintain 98.3%+)

### When Adding New Files Here
1. Use template: `docs/Guideline/Condition_Document_Template_Guideline.md`
2. Reference guideline: `docs/Guideline/Back_Testing_Guideline_Min.md`
3. Follow naming: `Condition_Min_[Indicator]_[Strategy].md`
4. Include all 6 required sections
5. Place in this folder only if initial documentation complete
6. Mark TODO sections if optimization ranges need refinement

### Quality Checks Before Moving to 2_Under_review/
- [ ] All 6 sections present and complete
- [ ] Buy/Sell conditions use correct variable names (Korean preserved)
- [ ] TA-Lib indicators properly referenced
- [ ] Optimization sections follow BO/BOR/SO/SOR/OR/GAR format
- [ ] Code is executable Python (no syntax errors)
- [ ] Variables exist in `stock_min_back.db` schema
- [ ] Document follows naming convention
- [ ] Time-based logic is sensible (if applicable)

### Common Issues to Fix
1. **Missing Optimization Sections**: Add BO/BOR/SO/SOR/OR/GAR with placeholder ranges
2. **Incorrect Variable Names**: Use Korean names from guideline (분봉시가, not min_open)
3. **Over-Optimization**: Flag strategies with >5 optimization variables
4. **Incomplete Code**: Ensure buy/sell logic is complete executable Python
5. **Template Non-Compliance**: Add missing sections (Overview, Backtesting Results)

### Moving to Next Stage
Files move to `2_Under_review/` when:
- Backtesting execution begins
- Initial parameter optimization started
- Active analysis or refinement in progress

## Dependencies
- **Template**: `docs/Guideline/Condition_Document_Template_Guideline.md`
- **Guideline**: `docs/Guideline/Back_Testing_Guideline_Min.md` (752 variables, 108 columns)
- **Database**: `_database/stock_min_back.db`
- **Backtesting**: `backtester/backengine_stock_min*.py`
- **Strategy**: `stock/kiwoom_strategy_min.py`
- **Parent**: `../AGENTS.md` - Min strategies overview

## Review Criteria
- **Document Structure**: All 6 sections present ✓
- **Code Quality**: Executable Python, correct variable names ✓
- **Optimization Format**: BO/BOR/SO/SOR/OR/GAR sections ✓
- **Indicator Usage**: Proper TA-Lib indicator references ✓
- **Naming Convention**: `Condition_Min_[Indicator]_[Strategy].md` ✓
- **Korean Variables**: 분봉 variables preserved ✓

## Next Steps
1. Prioritize strategies for backtesting (start with simpler single-indicator strategies)
2. Execute backtesting using `backtester/backtest.py`
3. Analyze results and refine optimization ranges
4. Move tested files to `2_Under_review/`
5. Document findings and improvement opportunities

## Statistics
- Total files: 45 (90% of Min strategies)
- MACD-based: 5
- RSI-based: 4
- Bollinger Bands: 6
- Moving Averages: 5
- Volume-based: 4
- Stochastic: 3
- Multi-indicator: 3
- Special indicators: 7
- Pattern & Trend: 6
- Research: 2

## Notes
- This is the largest review stage (90% of strategies)
- Focus on high-quality documentation before backtesting
- Avoid moving files to next stage without proper validation
- Maintain 98.3%+ guideline compliance rate
- Document any discovered issues or improvement needs
- Coordinate with backtester team before mass testing
