<!-- Parent: ../AGENTS.md -->
# Tick 조건식 문서

## Purpose
초(秒) 단위 틱 데이터를 활용한 고빈도 트레이딩 전략 조건식 저장소. 1초 단위 실시간 데이터 기반으로 급등주 포착, 시가 갭 돌파, 체결강도 기반 매매 등 초단타 전략을 포함합니다.

## Overview
- **시간 단위**: 1초 단위 실시간 데이터
- **타겟 시간**: 주로 장 시작 직후 (09:00~09:30)
- **데이터베이스**: `stock_tick_back.db`
- **변수**: 초당거래대금, 체결강도, 초당매수/매도수량 등 93개 컬럼
- **전략 유형**: 급등주 포착, 시가 갭 돌파, 체결강도 기반 매매
- **전체 조건식**: 72개 (76개 마크다운 파일)
- **준수율**: 98.3% 가이드라인 준수

## Review Process (3-Stage)
- **1_To_be_reviewed/**: 63개 - 초기 작성 완료, 검토 대기
- **2_Under_review/**: 9개 - 검토 및 개선 진행 중
- **3_Review_finished/**: 0개 - 검토 완료 (아직 없음)
- **20250808_study/**: 특정 날짜 연구 자료

## Key Files
### Production Ready (⭐⭐⭐⭐⭐)
- `Condition_Tick_902_905_update_2.md` - 골드 스탠다드, 09:02~09:05 전략
- `Condition_Tick_900_920_Enhanced.md` - 시가총액 3티어 × 4시간대 조합
- `Condition_Tick_925_935_Angle_Strategy.md` - 각도 지표 삼각 검증
- `Condition_Tick_900_930_Composite_Study.md` - 종합 복합 지표

### By Strategy Type
- **시간대별 전략** (27개): 장 초반 18개, 오전장 5개, 오후장 4개
- **모멘텀 기반** (8개): 등락율 각도, 체결강도, 시가대비 상승률
- **거래량 기반** (6개): 초당거래대금, 평균 대비 배수
- **호가창 기반** (7개): 매수/매도 잔량, 호가 스프레드
- **갭/돌파 전략** (7개): 시가 갭, 신고가 돌파
- **반전/스캘핑** (6개): 빠른 진입/청산
- **특수 지표** (5개): 시가총액 차등, 순매수 급증
- **연구/AI** (17개): 연구 13개, AI 2개, 템플릿 4개

## Subdirectories

### 1_To_be_reviewed/
검토 대기 중인 조건식 63개. 기본 문서 구조와 조건식 코드 작성 완료, 백테스팅 검증 필요.

### 2_Under_review/
검토 진행 중 9개. 백테스팅 실행 중이거나 결과 분석 단계.
- Condition_Tick_902.md
- Condition_Tick_902_905.md
- Condition_Tick_902_905_update.md
- Condition_Tick_902_905_update_2.md (골드 스탠다드)
- Condition_Tick_902_Update.md
- Source files (3개)

### 20250808_study/
특정 날짜(2025-08-08) 연구 자료 모음.

## For AI Agents

### Maintaining Tick Strategies
1. **Always read files before modifications** - Never suggest changes without reading
2. **Preserve Korean variable names** - 현재가, 시가, 고가, 저가, 등락율 등 번역 금지
3. **Respect naming conventions** - `Condition_Tick_[시간]_[전략].md` 패턴
4. **Follow documentation template** - `Condition_Document_Template_Guideline.md` 준수
5. **Maintain 98.3%+ compliance** - 가이드라인 준수율 유지
6. **Test with backtester** - 실제 배포 전 검증 필수

### When Adding New Tick Strategies
1. Use template: `docs/Guideline/Condition_Document_Template_Guideline.md`
2. Reference guideline: `docs/Guideline/Back_Testing_Guideline_Tick.md`
3. Study example: `Condition_Tick_902_905_update_2.md`
4. Follow naming: `Condition_Tick_[HHMM]_[HHMM]_[Strategy].md`
5. Include all sections: Overview, Common Indicators, Buy/Sell Conditions, Optimization, Backtesting Results, Improvement Research

### Quality Standards
- **Document structure**: Header + Overview + Common Indicators + Conditions + Optimization + Results
- **Code patterns**: Time branching, market cap differentiation, signal filtering
- **Optimization sections**: BO/BOR/SO/SOR/OR/GAR format
- **Variable documentation**: 93 columns from `stock_tick_back.db`
- **Review process**: Move through 3-stage review (To_be_reviewed → Under_review → Review_finished)

### Critical Variables (Tick)
- `초당거래대금` - Per-second trading volume (KRW millions)
- `체결강도` - Execution strength (buy/sell ratio)
- `초당매수수량`, `초당매도수량` - Per-second buy/sell quantities
- `시가등락율` - Opening price change ratio
- `시가대비등락율` - Current vs opening price ratio
- `등락율각도` - Rate of change angle
- `호가정보` - Order book data (bid/ask spreads, quantities)

## Dependencies
- **Template**: `docs/Guideline/Condition_Document_Template_Guideline.md`
- **Guideline**: `docs/Guideline/Back_Testing_Guideline_Tick.md` (33KB, 826 documented variables)
- **Database**: `_database/stock_tick_back.db` (93 columns)
- **Backtesting engines**: `backtester/backengine_stock_tick*.py`
- **Strategy implementation**: `stock/kiwoom_strategy_tick.py`
- **Data structure**: `docs/Guideline/Stock_Database_Information.md`

## Related Documentation
- Parent: `../README.md` - Condition folder overview
- Sibling: `../Min/` - Minute strategies (분봉 전략)
- Reference: `../Reference/` - External references (PyTrader, YouTube)
- Idea: `../Idea/` - AI-generated strategy concepts

## Statistics
- Total documents: 76 markdown files
- Condition strategies: 72 documented
- Template-compliant: 70/72 (98.3%)
- Production-ready: 4 files (⭐⭐⭐⭐⭐ rated)
- Under active development: 9 files
- Research phase: 13 files
- AI-generated: 2 files

## Notes
- Tick strategies focus on ultra-short-term trading (seconds to minutes)
- Primary time window: 09:00-09:30 (market opening surge)
- High-frequency data requires fast signal processing
- Most effective for gap trading and momentum surge capture
- Document quality maintained at 98.3% compliance rate
