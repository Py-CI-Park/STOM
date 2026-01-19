<!-- Parent: ../AGENTS.md -->
# 2단계: 검토 진행 중 (Under Review)

## Purpose
백테스팅 실행 중이거나 결과 분석 단계에 있는 1분봉 트레이딩 전략 조건식 저장소. 파라미터 최적화, 성능 평가, 개선 작업이 진행 중인 전략들이 포함됩니다.

## Overview
- **전체 조건식**: 7개 (12%)
- **상태**: 백테스팅 실행 중, 결과 분석, 파라미터 조정
- **작업 유형**: 성능 검증, 최적화, 개선안 적용
- **다음 단계**: 검증 완료 → 3_Review_finished/ 이동 또는 1_To_be_reviewed/ 재검토

## Key Files

### Active Research Strategies (6 files)
1. **Condition_Stomer_Min.md**
   - **Type**: Stomer 분봉 종합 전략
   - **Status**: 초기 백테스팅 완료, 파라미터 최적화 필요
   - **Focus**: 다중 지표 융합 시스템
   - **Next**: 최적화 범위 재조정

2. **Condition_Study_1_Min.md**
   - **Type**: 1차 연구 전략
   - **Status**: 백테스팅 결과 분석 중
   - **Focus**: 기본 지표 조합 테스트
   - **Next**: 개선안 적용 및 재테스트

3. **Condition_Study_2_Min.md**
   - **Type**: 2차 연구 전략
   - **Status**: 1차 전략 개선 버전 테스트
   - **Focus**: 필터 조건 강화
   - **Next**: 성능 비교 분석

4. **Condition_Study_3_902_min.md**
   - **Type**: 09:02 분봉 특화 전략
   - **Status**: 시간대별 전략 검증 중
   - **Focus**: 장 시작 변동성 활용
   - **Next**: 다른 시간대 확장 검토

5. **Condition_Study_3_9010_min.md**
   - **Type**: 09:10 분봉 특화 전략
   - **Status**: 09:02 전략 후속 테스트
   - **Focus**: 초기 변동성 안정화 구간
   - **Next**: 통합 전략 개발

6. **Condition_Min_Study_251227_Full_Segment.md**
   - **Type**: 전체 시간대 세그먼트 전략
   - **Status**: 종합 테스트 진행 중
   - **Focus**: 시간대별 세그먼트 분할 매매
   - **Next**: 세그먼트별 성능 개선

### Recent Additions (1 file)
7. **Condition_Min_Study_Segment_Filter_251225.md**
   - **Type**: 세그먼트 필터링 전략
   - **Status**: 최신 추가, 백테스팅 준비 중
   - **Focus**: 세그먼트별 필터 조건 최적화
   - **Next**: 초기 백테스팅 실행

## For AI Agents

### Primary Responsibilities
1. **Backtesting Coordination**
   - Track backtesting execution status for each file
   - Monitor optimization progress (grid search, genetic algorithm)
   - Coordinate with `backtester/backengine_stock_min*.py` engines
   - Document performance metrics: 승률, 손익률, MDD, Sharpe ratio

2. **Performance Analysis**
   - Analyze backtesting results against benchmarks
   - Compare multiple parameter sets (BO vs optimized)
   - Identify overfitting risks and robustness issues
   - Validate across different market conditions and time periods

3. **Improvement Implementation**
   - Apply refinements based on backtesting results
   - Update BO/BOR/SO/SOR/OR/GAR sections with optimized values
   - Add Backtesting Results section with detailed metrics
   - Document lessons learned and improvement rationale

4. **Workflow Management**
   - Move files to `3_Review_finished/` when validation complete
   - Return files to `1_To_be_reviewed/` if major revisions needed
   - Flag strategies requiring human expert review
   - Maintain review status tracking

### When Files Enter This Stage
Files move here from `1_To_be_reviewed/` when:
- Backtesting execution begins
- Initial optimization parameters need refinement
- Active performance analysis in progress
- Improvement iterations underway

### Active Tasks for Current Files

#### High Priority
1. **Condition_Min_Study_251227_Full_Segment.md**
   - Execute comprehensive backtesting across all segments
   - Analyze segment-specific performance variations
   - Optimize parameters for each time segment
   - Document segment transition logic

2. **Condition_Min_Study_Segment_Filter_251225.md**
   - Run initial backtesting with current parameters
   - Evaluate filter effectiveness
   - Compare with unfiltered baseline
   - Refine filter criteria based on results

#### Medium Priority
3. **Condition_Study_3_902_min.md** & **Condition_Study_3_9010_min.md**
   - Compare 09:02 vs 09:10 strategy performance
   - Identify optimal early-market entry timing
   - Test combined strategy approach
   - Document time-specific patterns

4. **Condition_Study_1_Min.md** & **Condition_Study_2_Min.md**
   - Compare Study 1 vs Study 2 improvements
   - Quantify impact of filter enhancements
   - Validate improvement consistency across periods
   - Document best practices

#### Lower Priority
5. **Condition_Stomer_Min.md**
   - Re-evaluate multi-indicator approach
   - Simplify if overfitting detected
   - Test reduced indicator set
   - Document optimization trade-offs

### Quality Checks Before Moving to 3_Review_finished/
- [ ] Backtesting completed with >1000 trades
- [ ] Optimization results documented in BO/BOR/SO/SOR sections
- [ ] Performance metrics meet minimum thresholds:
  - 승률 (Win Rate): >50%
  - 손익률 (Profit Factor): >1.5
  - MDD (Max Drawdown): <20%
  - Sharpe Ratio: >1.0
- [ ] Robustness validated across different periods
- [ ] No significant overfitting detected
- [ ] Backtesting Results section complete with charts
- [ ] Code validated and executable
- [ ] Documentation updated with findings

### Common Issues to Address
1. **Overfitting**: Too many optimization parameters causing curve-fitting
2. **Low Sample Size**: Insufficient trade count for statistical significance
3. **Parameter Instability**: Performance varies drastically with small parameter changes
4. **Market Regime Dependency**: Strategy works only in specific market conditions
5. **Implementation Gap**: Backtesting results not replicable in live trading
6. **Documentation Lag**: Code changes not reflected in documentation

### Moving to Next Stage
**To 3_Review_finished/**:
- All quality checks passed ✓
- Performance metrics exceed thresholds ✓
- Robustness validated ✓
- Documentation complete and accurate ✓
- Ready for production deployment consideration

**Back to 1_To_be_reviewed/**:
- Major issues discovered requiring redesign
- Performance below acceptable thresholds
- Overfitting cannot be resolved with current approach
- Strategy concept needs fundamental revision

## Dependencies
- **Guideline**: `docs/Guideline/Back_Testing_Guideline_Min.md` (752 variables)
- **Database**: `_database/stock_min_back.db` (108 columns)
- **Backtesting**: `backtester/backengine_stock_min*.py` engines
- **Optimization**: `backtester/optimiz.py` (grid search), `backtester/optimiz_genetic_algorithm.py`
- **Results DB**: `_database/backtest.db`, `_database/optuna.db`
- **Strategy**: `stock/kiwoom_strategy_min.py`
- **Parent**: `../AGENTS.md` - Min strategies overview

## Review Criteria
- **Backtesting Complete**: >1000 trades, multiple periods ✓
- **Performance Metrics**: Meet minimum thresholds ✓
- **Optimization**: BO/BOR sections updated with results ✓
- **Robustness**: Validated across market conditions ✓
- **Documentation**: Complete with results section ✓
- **Code Quality**: Executable and validated ✓

## Backtesting Requirements

### Minimum Standards
- **Data Period**: >6 months (preferably 1+ year)
- **Trade Count**: >1000 trades for statistical significance
- **Win Rate**: >50% for consistency
- **Profit Factor**: >1.5 for profitability
- **Max Drawdown**: <20% for risk management
- **Sharpe Ratio**: >1.0 for risk-adjusted returns

### Validation Tests
1. **Walk-Forward Analysis**: Test on out-of-sample data
2. **Parameter Sensitivity**: Verify stability with parameter variations
3. **Market Regime Testing**: Bull, bear, sideways market validation
4. **Slippage & Commission**: Include realistic transaction costs
5. **Position Sizing**: Test with actual capital constraints

## Performance Tracking

### Current Review Status
- **Stomer_Min**: Initial testing, needs optimization
- **Study_1_Min**: Analysis phase
- **Study_2_Min**: Comparison with Study 1
- **Study_3_902_min**: Time-specific validation
- **Study_3_9010_min**: Time-specific validation
- **Study_251227_Full_Segment**: Comprehensive testing
- **Study_Segment_Filter_251225**: Initial backtesting pending

### Metrics to Track
- Total trades executed
- Win rate (%)
- Profit factor
- Max drawdown (%)
- Average profit/loss per trade
- Sharpe ratio
- Sortino ratio
- Calmar ratio
- Recovery factor
- Consistency score

## Next Steps
1. Execute pending backtests for new files
2. Analyze results for completed tests
3. Update optimization parameters based on findings
4. Document performance metrics and insights
5. Move validated strategies to 3_Review_finished/
6. Iterate on underperforming strategies

## Statistics
- Total files: 7 (12% of Min strategies)
- Active research: 6 strategies
- Recent additions: 1 strategy
- Time-specific: 2 strategies (09:02, 09:10)
- Segment-based: 2 strategies
- General study: 3 strategies

## Notes
- This stage represents active development and refinement
- Focus on data-driven optimization, not speculation
- Document all findings for knowledge transfer
- Maintain balance between optimization and overfitting prevention
- Coordinate with backtester team for resource allocation
- Regular status updates recommended
- Keep 1-2 weeks maximum in this stage per strategy
