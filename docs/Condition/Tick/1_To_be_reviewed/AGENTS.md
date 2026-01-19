<!-- Parent: ../AGENTS.md -->
# 1단계: 검토 대기 (To Be Reviewed)

## Purpose
초기 작성이 완료되어 검토를 기다리는 틱 전략 조건식 저장소. 기본 문서 구조와 조건식 코드는 작성되었으나, 백테스팅 검증과 성능 평가가 필요한 단계입니다.

## Overview
- **전략 수**: 63개 조건 파일
- **상태**: 초기 작성 완료, 백테스팅 검증 대기
- **다음 단계**: `2_Under_review/`로 이동 (백테스팅 시작 시)
- **문서 준수**: 기본 템플릿 구조 갖춤

## Key Files

### By Strategy Category

#### Time-Based Strategies (시간대별, 27개)
**Early Opening (09:00-09:30)**
- `Condition_Tick_900_920.md` - 09:00-09:20 초기 모멘텀
- `Condition_Tick_900_930_Composite_Study.md` - 종합 복합 지표
- `Condition_Tick_0900_0910_Opening_Volume.md` - 거래량 폭발
- `Condition_Tick_905_915_LongTail.md` - 긴 꼬리 반전
- `Condition_Tick_910_930_Rebound.md` - 반등 포착
- `Condition_Tick_925_935_Angle_Strategy.md` - 각도 지표 삼각 검증
- `Condition_Tick_0930_1000_PostBreakout.md` - 돌파 후 추격
- `Condition_Tick_930_1000_Early_Momentum_Continuation.md` - 모멘텀 지속
- `Condition_Tick_930_1000_Momentum.md` - 모멘텀 전략
- `Condition_Tick_935_945_Momentum.md` - 09:35-09:45 모멘텀

**Mid-Morning (10:00-12:00)**
- `Condition_Tick_1000_1100_Breakout.md` - 10시대 돌파
- `Condition_Tick_1100_1200_Consolidation_Breakout.md` - 횡보 돌파
- `Condition_Tick_1130_1200_PreLunch.md` - 점심 직전
- `Condition_Tick_1130_1300_Lunch_Volatility.md` - 점심시간 변동성

**Afternoon (13:00-15:00)**
- `Condition_Tick_1300_1400_AfternoonRebound.md` - 오후 반등
- `Condition_Tick_1300_1400_Strength_Surge.md` - 체결강도 급증
- `Condition_Tick_1400_1430_Closing_Momentum.md` - 마감 모멘텀
- `Condition_Tick_1430_1500_ClosingMomentum.md` - 종가 모멘텀

#### Momentum-Based (모멘텀, 8개)
- `Condition_Early_Momentum_Surge.md` - 초기 모멘텀 급증
- `Condition_Tick_Opening_Momentum.md` - 시초가 모멘텀
- `Condition_Tick_Momentum_Surge.md` - 모멘텀 서지
- `Condition_Tick_Momentum_Acceleration.md` - 모멘텀 가속
- `Condition_Tick_MomentumReversal.md` - 모멘텀 반전
- `Condition_Tick_Early_Breakout.md` - 조기 돌파
- `Condition_Tick_Breakout_Confirmation.md` - 돌파 확인
- `Condition_Tick_ConsolidationBreakout.md` - 횡보 돌파

#### Volume-Based (거래량, 6개)
- `Condition_Tick_VolumeSpike.md` - 거래량 스파이크
- `Condition_Tick_Volume_Surge.md` - 거래량 급증
- `Condition_Tick_Volume_Burst.md` - 거래량 폭발
- `Condition_Tick_Volume_Explosion.md` - 거래량 대폭발
- `Condition_Volume_Explosion.md` - 거래량 폭발 (복사본)
- `Condition_Tick_Volatility_Expansion.md` - 변동성 확대

#### Order Book-Based (호가창, 7개)
- `Condition_Order_Book_Imbalance.md` - 호가 불균형
- `Condition_Tick_Bid_Ask_Pressure.md` - 매수매도 압력
- `Condition_Tick_Ask_Spread_Narrow.md` - 매도호가 좁힘
- `Condition_Tick_BidWall_Surge.md` - 매수벽 형성
- `Condition_Tick_Strong_Bid_Support.md` - 강력한 매수 지지
- `Condition_Tick_SellWall_Exhaustion.md` - 매도벽 소진
- `Condition_Tick_Continuous_Buy.md` - 연속 매수

#### Gap/Breakout Strategies (갭/돌파, 7개)
- `Condition_Tick_GapTrading.md` - 갭 트레이딩
- `Condition_Tick_Gap_Up_Continuation.md` - 상승 갭 지속
- `Condition_Tick_PriceAction.md` - 가격 액션

#### Reversal/Scalping (반전/스캘핑, 6개)
- `Condition_RSI_Reversal.md` - RSI 반전
- `Condition_MA_Breakout_Scalping.md` - 이동평균 돌파 스캘핑
- `Condition_Strength_Reversal.md` - 강도 반전
- `Condition_Tick_Strength_Reversal.md` - 틱 강도 반전
- `Condition_Tick_Quick_Scalping.md` - 빠른 스캘핑
- `Condition_Stomer.md` - 스토머 전략

#### Special Indicators (특수 지표, 5개)
- `Condition_Tick_MarketCap_Differential.md` - 시가총액 차등
- `Condition_Tick_Net_Buy_Surge.md` - 순매수 급증

#### Research/AI/Templates (연구/AI, 17개)
**Study Series**
- `Condition_Study_1.md` - 연구 1
- `Condition_Study_2.md` - 연구 2
- `Condition_Study_2_T.md` - 연구 2 변형
- `Condition_Study_3_902.md` - 연구 3: 09:02 특화
- `Condition_Study_4_905.md` - 연구 4: 09:05 특화
- `Condition_Study_5_9010.md` - 연구 5: 09:10 특화
- `Condition_Study_93000.md` - 연구: 93000 변수
- `Condition_Study_High_Over.md` - 연구: 고가 초과

**AI-Generated**
- `Condition_Study_By_GPT_o1.md` - GPT-o1 생성
- `Condition_Study_By_Grok3.md` - Grok3 생성

**Experimental**
- `Condition_Find_1.md` - 실험 1

**Templates**
- `Condition_Test_Template.md` - 테스트 템플릿

## For AI Agents

### When Reviewing Strategies in This Stage

1. **Initial Assessment**
   - Verify document structure follows template
   - Check all required sections present
   - Validate Korean variable names preserved
   - Confirm optimization sections (BO/BOR/SO/SOR) exist

2. **Pre-Backtesting Validation**
   - Review strategy logic for coherence
   - Check time window appropriateness
   - Validate indicator calculations
   - Ensure no syntax errors in condition code

3. **Moving to Under Review**
   - When backtesting begins: Move file to `../2_Under_review/`
   - Update parent AGENTS.md with file counts
   - Create corresponding backtesting task
   - Track in project management system

4. **Quality Gates Before Moving**
   - ✅ Document structure complete
   - ✅ All sections filled (no placeholders)
   - ✅ Optimization ranges defined
   - ✅ Code blocks formatted correctly
   - ✅ Variable names in Korean preserved
   - ✅ Template compliance verified

### Critical Rules

1. **Never modify without reading** - Always read file before suggesting changes
2. **Preserve Korean variables** - 현재가, 시가, 고가, 저가, 등락율, 체결강도
3. **Maintain naming convention** - `Condition_Tick_[HHMM]_[HHMM]_[Strategy].md`
4. **Follow template structure** - See `docs/Guideline/Condition_Document_Template_Guideline.md`
5. **Respect review stages** - Don't skip stages in the review process
6. **Document all changes** - Update parent AGENTS.md when moving files

### Common Issues to Check

- Missing optimization sections (BO/BOR/SO/SOR/OR/GAR)
- Incomplete variable documentation
- Time window logic errors
- Hardcoded values without optimization ranges
- English translations of Korean variable names (❌ PROHIBITED)
- Missing backtesting results section (acceptable at this stage)

## Dependencies

### Required Reading
- **Parent**: `../AGENTS.md` - Tick strategy overview
- **Template**: `docs/Guideline/Condition_Document_Template_Guideline.md`
- **Guideline**: `docs/Guideline/Back_Testing_Guideline_Tick.md` (826 documented variables)

### Reference Examples
- `../2_Under_review/Condition_Tick_902_905_update_2.md` - Gold standard example
- `Condition_Tick_900_920_Enhanced.md` - Multi-tier structure
- `Condition_Tick_925_935_Angle_Strategy.md` - Angle indicator validation

### Backtesting Requirements
- **Database**: `_database/stock_tick_back.db` (93 columns)
- **Engine**: `backtester/backengine_stock_tick.py`
- **Strategy**: `stock/kiwoom_strategy_tick.py`
- **Results DB**: `_database/backtest.db`

### Review Criteria
1. **Structure Compliance**: Template sections complete
2. **Code Quality**: Logic coherent, no syntax errors
3. **Documentation**: Variables documented, ranges defined
4. **Korean Preservation**: No translation of native terms
5. **Optimization Ready**: BO/BOR/SO/SOR/OR/GAR sections present

## Statistics
- **Total Files**: 63 condition files
- **Compliance Rate**: Template structure present
- **Next Stage**: 12 files in `2_Under_review/`
- **Review Process**: 3-stage (To_be_reviewed → Under_review → Review_finished)
- **Target**: Move to production after successful backtesting

## Notes
- Files at this stage have not undergone backtesting validation
- Some files may have incomplete optimization sections (acceptable here)
- Priority should be given to time-based strategies (09:00-09:30 window)
- Research and AI-generated files need extra scrutiny before backtesting
- Template files should not be moved to review stages
