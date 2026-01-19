<!-- Parent: ../AGENTS.md -->
# Min 조건식 문서

## Purpose
1분봉 캔들 데이터를 활용한 스윙/단타 트레이딩 전략 조건식 저장소. 1분 단위 캔들 데이터 기반으로 기술적 지표(MACD, RSI, BBand 등)를 활용한 추세 추종, 반전 포착, 복합 전략을 포함합니다.

## Overview
- **시간 단위**: 1분 단위 캔들 데이터
- **타겟 시간**: 장 시작부터 장 마감까지 (09:00~15:30)
- **데이터베이스**: `stock_min_back.db`
- **변수**: 분봉시가/고가/저가, 분당거래대금, TA-Lib 지표 등 108개 컬럼
- **전략 유형**: 기술적 지표 기반 매매, 추세 추종, 반전 포착, 시간대별 특화 전략
- **전체 조건식**: 49개 (Main) + 15개 (Idea) = 65개
- **준수율**: 98.3% 가이드라인 준수

## Review Process (3-Stage)
- **1_To_be_reviewed/**: 45개 (90%) - 초기 작성 완료, 검토 대기
- **2_Under_review/**: 6개 (10%) - 검토 및 개선 진행 중
- **3_Review_finished/**: 0개 - 검토 완료 (아직 없음)
- **Idea/**: 15개 - 전략 아이디어 및 개념 검증 단계

## Tick vs Min Strategies
| 구분 | Tick 전략 | Min 전략 |
|------|-----------|----------|
| 시간 단위 | 초(1초) | 분(1분) |
| 데이터 갱신 | 실시간 틱 | 1분마다 |
| 봉 정보 | 일봉만 | 일봉 + 분봉 |
| 보조지표 | 제한적 | 풍부한 TA-Lib 지표 |
| 주요 용도 | 초단타, 급등주 즉시 포착 | 단타, 스윙, 기술적 분석 |

## Key Files by Indicator Type

### MACD-Based (5 files)
- `Condition_MACD_GoldenCross.md` - MACD 골든크로스 패턴
- `Condition_Min_MACD_Cross.md` - MACD 크로스오버 + RSI 필터
- `Condition_Min_MACD_GoldenCross.md` - MACD + BBand 복합

### RSI-Based (4 files)
- `Condition_Min_RSI_Divergence.md` - 가격-RSI 다이버전스
- `Condition_Min_RSI_Oversold.md` - RSI 과매도 반등
- `Condition_RSI_Oversold_Rebound.md` - RSI 과매도 리바운드

### Bollinger Bands (6 files)
- `Condition_Bollinger_Reversal.md` - 볼린저 밴드 반전
- `Condition_Min_BB_Squeeze.md` - 변동성 수축(Squeeze)
- `Condition_Min_Bollinger_Breakout_Strategy.md` - BBand 상단 돌파

### Moving Average (5 files)
- `Condition_MA_Alignment_Momentum.md` - 이동평균 정배열 + 모멘텀
- `Condition_Min_MA_Convergence.md` - 이동평균 수렴
- `Condition_Min_Multi_MA_Cross.md` - 다중 MA 크로스

### Volume-Based (4 files)
- `Condition_Min_Volume_Breakout.md` - 거래량 급증 + 가격 돌파
- `Condition_Min_Volume_Momentum.md` - 거래량 모멘텀
- `Condition_Min_Volume_Weighted.md` - 거래량 가중 분석

### Stochastic (3 files)
- `Condition_Min_Stochastic_Cross.md` - %K/%D 크로스
- `Condition_Min_Stochastic_Oversold.md` - 과매도 반등

### Multi-Indicator (3 files)
- `Condition_Min_900_1000_BB_RSI.md` - BBand + RSI 복합
- `Condition_Min_MultiIndicator_Composite.md` - 다중 지표 종합
- `Condition_Min_Multi_Indicator_Fusion.md` - 지표 융합 시스템

### Special Indicators (7 files)
- `Condition_Min_ADX_TrendStrength.md` - ADX 추세 강도
- `Condition_Min_ATR_Breakout.md` - ATR 변동성 돌파
- `Condition_Min_CCI_Extreme.md` - CCI 극단값
- `Condition_Min_MFI_MoneyFlow.md` - MFI 자금 흐름
- `Condition_Min_ROC_Momentum.md` - ROC 변화율
- `Condition_Min_WilliamsR_Oversold.md` - Williams %R 과매도

### Pattern & Trend (6 files)
- `Condition_Gap_Up_Breakout.md` - 갭상승 돌파
- `Condition_Min_Candle_Pattern.md` - 캔들 패턴 인식
- `Condition_Min_SAR_Reversal.md` - Parabolic SAR 반전
- `Condition_Min_Trend_Following.md` - 추세 추종

### Research (6 files)
- `Condition_Find_1_Min.md` - 분봉 종합 탐색
- `Condition_Stomer_Min.md` - Stomer 분봉 전략
- `Condition_Study_1_Min.md` - 1차 연구
- `Condition_Study_3_902_min.md` - 09:02 분봉 연구

## Subdirectories

### 1_To_be_reviewed/
검토 대기 중인 조건식 45개 (90%). 기본 문서 구조와 조건식 코드 작성 완료, 백테스팅 검증 필요.

### 2_Under_review/
검토 진행 중 6개 (10%). 백테스팅 실행 중이거나 결과 분석 단계.
- Condition_Stomer_Min.md
- Condition_Study_1_Min.md
- Condition_Study_2_Min.md
- Condition_Study_3_902_min.md
- Condition_Study_3_9010_min.md
- Condition_Min_Study_251227_Full_Segment.md

### Idea/
전략 아이디어 및 개념 검증 단계 15개. 기술적 지표 기반 4개, 시장 상황별 5개, 고급 전략 4개, 일반 아이디어 2개.

**Technical Indicators:**
- `Condition_MACD_Precision_System.md` - MACD 정밀 시스템
- `Condition_RSI_Multilayer_Filter.md` - RSI 다층 필터
- `Condition_Bollinger_Strategic.md` - 볼린저 전략적 활용
- `Condition_Triple_Confirmation.md` - 3중 확인 시스템

**Market Situations:**
- `Condition_Basic_Surge_Detection.md` - 기본 급등 감지
- `Opening_Surge_Strategy_20250713_temp.md` - 장 시작 급등
- `gap_up_momentum_20250713_temp.md` - 갭 상승 모멘텀
- `Condition_Reversal_Point.md` - 반전 지점 포착
- `Condition_Time_Specific.md` - 시간대별 특화

**Advanced Strategies:**
- `Condition_Comprehensive_Strategy_20250713_temp.md` - 종합 통합
- `Condition_Advanced_Algorithm.md` - 고급 알고리즘
- `Condition_Risk_Management.md` - 리스크 관리
- `Condition_Portfolio_Management.md` - 포트폴리오 관리

**General Ideas:**
- `아이디어.md` - 분봉 전략 아이디어 모음 v1
- `아이디어_v2.md` - 분봉 전략 아이디어 모음 v2

## For AI Agents

### Maintaining Min Strategies
1. **Always read files before modifications** - Never suggest changes without reading
2. **Preserve Korean variable names** - 분봉시가, 분봉고가, 분당거래대금 등 번역 금지
3. **Respect naming conventions** - `Condition_Min_[Indicator]_[Strategy].md` 패턴
4. **Follow documentation template** - `Condition_Document_Template_Guideline.md` 준수
5. **Maintain 98.3%+ compliance** - 가이드라인 준수율 유지
6. **Test with backtester** - 실제 배포 전 검증 필수
7. **Leverage TA-Lib indicators** - MACD, RSI, BBand, Stochastic, ADX, ATR 등 활용

### When Adding New Min Strategies
1. Use template: `docs/Guideline/Condition_Document_Template_Guideline.md`
2. Reference guideline: `docs/Guideline/Back_Testing_Guideline_Min.md`
3. Study examples: MACD/RSI/BBand strategies
4. Follow naming: `Condition_Min_[Indicator]_[Strategy].md`
5. Include all sections: Overview, Buy/Sell Conditions (with TA-Lib indicators), Optimization, Backtesting Results
6. Use candle data: 분봉시가, 분봉고가, 분봉저가, 분봉종가
7. Apply time-based branching: Different strategies for different time windows

### Quality Standards
- **Document structure**: Header + Overview + Conditions (with TA-Lib) + Optimization + Results
- **Code patterns**: Candle patterns, indicator crossovers, time branching
- **Optimization sections**: BO/BOR/SO/SOR/OR/GAR format
- **Variable documentation**: 108 columns from `stock_min_back.db`
- **Review process**: Move through 3-stage review
- **Indicator combinations**: Avoid over-optimization, test thoroughly

### Critical Variables (Min)
- **Candle data**: `분봉시가`, `분봉고가`, `분봉저가`, `분봉종가`
- **Volume**: `분당거래대금`, `분당매수수량`, `분당매도수량`, `분당순매수금액`
- **MACD**: `MACD`, `MACD시그널`, `MACD히스토그램`
- **RSI**: `RSI` (Relative Strength Index)
- **Bollinger Bands**: `BBandUpper`, `BBandMiddle`, `BBandLower`
- **Moving Averages**: `이동평균5`, `이동평균20`, `이동평균60`, `이동평균120`
- **Stochastic**: `STOCHSK`, `STOCHSD`
- **Others**: `ADX`, `ATR`, `CCI`, `MFI`, `ROC`, `Williams%R`, `Parabolic SAR`

### Min Strategy Patterns

#### 1. Candle Data Usage
```python
# Candle pattern detection
if 분봉시가 < 분봉저가:  # Falling candle
    if 현재가 > 분봉고가:  # High breakout
        매수 = True

# Volume increase
if 분당거래대금 > 분당거래대금N(1) * 1.5:
    매수 = True
```

#### 2. TA-Lib Indicators
```python
# MACD Golden Cross
if MACD < MACD시그널N(1) and MACD >= MACD시그널:
    매수 = True

# RSI Oversold
if RSIN(1) < 30 and RSI >= 30:
    매수 = True

# Bollinger Band Bounce
if 현재가N(1) <= BBandLower and 현재가 > BBandLower:
    매수 = True
```

#### 3. Time-Based Strategy
```python
if 시분초 < 93000:  # Before 09:30 (early market)
    # Surge detection
    if 등락율 > 3.0 and 체결강도 > 100:
        매수 = True
elif 시분초 < 110000:  # Before 11:00 (morning)
    # Technical indicator strategy
    if MACD > MACD시그널 and RSI < 70:
        매수 = True
else:  # After 11:00 (afternoon)
    # Trend following
    if 이동평균5 > 이동평균20 and 현재가 > 이동평균5:
        매수 = True
```

## Dependencies
- **Template**: `docs/Guideline/Condition_Document_Template_Guideline.md`
- **Guideline**: `docs/Guideline/Back_Testing_Guideline_Min.md` (25KB, 752 documented variables)
- **Database**: `_database/stock_min_back.db` (108 columns)
- **Backtesting engines**: `backtester/backengine_stock_min*.py`
- **Strategy implementation**: `stock/kiwoom_strategy_min.py`
- **Data structure**: `docs/Guideline/Stock_Database_Information.md`
- **TA-Lib**: Technical analysis library for indicators

## Related Documentation
- Parent: `../README.md` - Condition folder overview
- Sibling: `../Tick/` - Tick strategies (틱 전략)
- Reference: `../Reference/` - External references
- Idea: `./Idea/` - Strategy ideas and concepts

## Statistics
- Total documents: 68 markdown files (50 Main + 15 Idea + 3 other)
- Condition strategies: 49 documented (Main)
- Idea strategies: 15 documented
- Template-compliant: 48/49 (98.3%)
- Under active development: 6 files
- Research phase: 6 files
- Idea phase: 15 files

## Notes
- Min strategies focus on short-term to swing trading (minutes to hours)
- Utilizes rich TA-Lib indicators unavailable in Tick data
- Candle pattern analysis provides better trend identification
- Less noise compared to Tick data, more stable signals
- Suitable for systematic trading with multiple confirmation indicators
- Avoid over-optimization when combining multiple indicators
- Test across different market conditions and time periods
- Document quality maintained at 98.3% compliance rate
