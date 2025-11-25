# Condition Detail Check and Plan

docs/Guideline/Condition_Document_Template_Guideline.md 기준으로 조건식 문서들을 점검하기 위한 상세 체크 테이블과 진행 계획입니다.
**모든 조건식을 하나씩 점검할 때마다 반드시 Condition_Document_Template_Guideline.md를 동시에 열어 둔 채로 각 조항을 문서와 대조하며 체크합니다.** Tick/Min 여부와 관계없이 동일한 강도로 검토하고, 가이드라인 조항을 재확인한 뒤 수정·보완 후에만 체크 표시를 합니다.
모든 Tick/Min 조건식 문서를 대상으로 하며, 각 체크 항목은 가이드라인의 필수 준수사항 13개를 그대로 반영합니다.

## 체크 기준 (Condition_Document_Template_Guideline.md 0. 필수 준수사항)

1. 상단 참조 표기 여부
2. 개요(시간, 종목 범위, 전략 타입, 핵심 변수·지표, 업데이트 이력) 5대 정보 포함 여부
3. 템플릿 목차 및 섹션 구조 유지 여부
4. 전략 ID·파일명·접미사 등 명명 규칙 준수 여부
5. 공통 계산 지표를 상단에 정리했는지 여부
6. self.vars 매핑/주석(의미, 단위, 범위, 간격, 개수) 포함 여부
7. 조건식 개선 방향 연구 섹션(최소 3개, 우선순위) 포함 여부
8. 최적화 경우의 수·소요 시간 계산 및 GA/OR 제안 여부
9. 모호 표현 없이 수치/조건을 명확히 기입했는지 여부
10. 백테스트 코드 변수명 호환성(self.vars, Buy/Sell, 시분초 등) 확보 여부
11. 매수/매도 초기값 및 로직 패턴 준수 여부
12. self.vars 인덱스 구간 규칙 준수 여부
13. if/elif 체인 구조 준수 여부

## Tick Condition Checklist

| Condition | Path | Type | Plan Status | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | C13 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Condition_Early_Momentum_Surge | docs/Condition/Tick/Condition_Early_Momentum_Surge.md | Tick | Completed | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Condition_Find_1 | docs/Condition/Tick/Condition_Find_1.md | Tick | Completed | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Condition_MA_Breakout_Scalping | docs/Condition/Tick/Condition_MA_Breakout_Scalping.md | Tick | Completed | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Condition_Order_Book_Imbalance | docs/Condition/Tick/Condition_Order_Book_Imbalance.md | Tick | Completed | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Condition_RSI_Reversal | docs/Condition/Tick/Condition_RSI_Reversal.md | Tick | Completed | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Condition_Stomer | docs/Condition/Tick/Condition_Stomer.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Strength_Reversal | docs/Condition/Tick/Condition_Strength_Reversal.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_1 | docs/Condition/Tick/Condition_Study_1.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_2 | docs/Condition/Tick/Condition_Study_2.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_2_T | docs/Condition/Tick/Condition_Study_2_T.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_3_902 | docs/Condition/Tick/Condition_Study_3_902.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_4_905 | docs/Condition/Tick/Condition_Study_4_905.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_5_9010 | docs/Condition/Tick/Condition_Study_5_9010.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_93000 | docs/Condition/Tick/Condition_Study_93000.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_By_GPT_o1 | docs/Condition/Tick/Condition_Study_By_GPT_o1.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_By_Grok3 | docs/Condition/Tick/Condition_Study_By_Grok3.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_High_Over | docs/Condition/Tick/Condition_Study_High_Over.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Test_Template | docs/Condition/Tick/Condition_Test_Template.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_0900_0910_Opening_Volume | docs/Condition/Tick/Condition_Tick_0900_0910_Opening_Volume.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_0930_1000_PostBreakout | docs/Condition/Tick/Condition_Tick_0930_1000_PostBreakout.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_1000_1100_Breakout | docs/Condition/Tick/Condition_Tick_1000_1100_Breakout.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_1100_1200_Consolidation_Breakout | docs/Condition/Tick/Condition_Tick_1100_1200_Consolidation_Breakout.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_1130_1200_PreLunch | docs/Condition/Tick/Condition_Tick_1130_1200_PreLunch.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_1130_1300_Lunch_Volatility | docs/Condition/Tick/Condition_Tick_1130_1300_Lunch_Volatility.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_1300_1400_AfternoonRebound | docs/Condition/Tick/Condition_Tick_1300_1400_AfternoonRebound.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_1300_1400_Strength_Surge | docs/Condition/Tick/Condition_Tick_1300_1400_Strength_Surge.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_1400_1430_Closing_Momentum | docs/Condition/Tick/Condition_Tick_1400_1430_Closing_Momentum.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_1430_1500_ClosingMomentum | docs/Condition/Tick/Condition_Tick_1430_1500_ClosingMomentum.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_900_920 | docs/Condition/Tick/Condition_Tick_900_920.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_900_920_Enhanced | docs/Condition/Tick/Condition_Tick_900_920_Enhanced.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_900_930_Composite_Study | docs/Condition/Tick/Condition_Tick_900_930_Composite_Study.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_902 | docs/Condition/Tick/Condition_Tick_902.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_902_905 | docs/Condition/Tick/Condition_Tick_902_905.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_902_905_update | docs/Condition/Tick/Condition_Tick_902_905_update.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_902_905_update_2 | docs/Condition/Tick/Condition_Tick_902_905_update_2.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_902_905_update_2_source | docs/Condition/Tick/Condition_Tick_902_905_update_2_source.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_902_905_update_source | docs/Condition/Tick/Condition_Tick_902_905_update_source.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_902_Update | docs/Condition/Tick/Condition_Tick_902_Update.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_902_update_source | docs/Condition/Tick/Condition_Tick_902_update_source.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_905_915_LongTail | docs/Condition/Tick/Condition_Tick_905_915_LongTail.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_910_930_Rebound | docs/Condition/Tick/Condition_Tick_910_930_Rebound.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_925_935_Angle_Strategy | docs/Condition/Tick/Condition_Tick_925_935_Angle_Strategy.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_930_1000_Early_Momentum_Continuation | docs/Condition/Tick/Condition_Tick_930_1000_Early_Momentum_Continuation.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_930_1000_Momentum | docs/Condition/Tick/Condition_Tick_930_1000_Momentum.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_935_945_Momentum | docs/Condition/Tick/Condition_Tick_935_945_Momentum.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Ask_Spread_Narrow | docs/Condition/Tick/Condition_Tick_Ask_Spread_Narrow.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_BidWall_Surge | docs/Condition/Tick/Condition_Tick_BidWall_Surge.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Bid_Ask_Pressure | docs/Condition/Tick/Condition_Tick_Bid_Ask_Pressure.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Breakout_Confirmation | docs/Condition/Tick/Condition_Tick_Breakout_Confirmation.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_ConsolidationBreakout | docs/Condition/Tick/Condition_Tick_ConsolidationBreakout.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Continuous_Buy | docs/Condition/Tick/Condition_Tick_Continuous_Buy.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Early_Breakout | docs/Condition/Tick/Condition_Tick_Early_Breakout.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_GapTrading | docs/Condition/Tick/Condition_Tick_GapTrading.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Gap_Up_Continuation | docs/Condition/Tick/Condition_Tick_Gap_Up_Continuation.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_MarketCap_Differential | docs/Condition/Tick/Condition_Tick_MarketCap_Differential.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_MomentumReversal | docs/Condition/Tick/Condition_Tick_MomentumReversal.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Momentum_Acceleration | docs/Condition/Tick/Condition_Tick_Momentum_Acceleration.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Momentum_Surge | docs/Condition/Tick/Condition_Tick_Momentum_Surge.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Net_Buy_Surge | docs/Condition/Tick/Condition_Tick_Net_Buy_Surge.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Opening_Momentum | docs/Condition/Tick/Condition_Tick_Opening_Momentum.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_PriceAction | docs/Condition/Tick/Condition_Tick_PriceAction.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Quick_Scalping | docs/Condition/Tick/Condition_Tick_Quick_Scalping.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_SellWall_Exhaustion | docs/Condition/Tick/Condition_Tick_SellWall_Exhaustion.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Strength_Reversal | docs/Condition/Tick/Condition_Tick_Strength_Reversal.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Strong_Bid_Support | docs/Condition/Tick/Condition_Tick_Strong_Bid_Support.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Volatility_Expansion | docs/Condition/Tick/Condition_Tick_Volatility_Expansion.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_VolumeSpike | docs/Condition/Tick/Condition_Tick_VolumeSpike.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Volume_Burst | docs/Condition/Tick/Condition_Tick_Volume_Burst.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Volume_Explosion | docs/Condition/Tick/Condition_Tick_Volume_Explosion.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Tick_Volume_Surge | docs/Condition/Tick/Condition_Tick_Volume_Surge.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Volume_Explosion | docs/Condition/Tick/Condition_Volume_Explosion.md | Tick | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

## Min Condition Checklist

| Condition | Path | Type | Plan Status | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | C9 | C10 | C11 | C12 | C13 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Condition_Bollinger_Reversal | docs/Condition/Min/Condition_Bollinger_Reversal.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Find_1_Min | docs/Condition/Min/Condition_Find_1_Min.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Gap_Up_Breakout | docs/Condition/Min/Condition_Gap_Up_Breakout.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_MACD_GoldenCross | docs/Condition/Min/Condition_MACD_GoldenCross.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_MACD_Golden_Cross | docs/Condition/Min/Condition_MACD_Golden_Cross.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_MA_Alignment_Momentum | docs/Condition/Min/Condition_MA_Alignment_Momentum.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_0930_1000_Trend | docs/Condition/Min/Condition_Min_0930_1000_Trend.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_900_1000_BB_RSI | docs/Condition/Min/Condition_Min_900_1000_BB_RSI.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_ADX_TrendStrength | docs/Condition/Min/Condition_Min_ADX_TrendStrength.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_ATR_Breakout | docs/Condition/Min/Condition_Min_ATR_Breakout.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_BB_Squeeze | docs/Condition/Min/Condition_Min_BB_Squeeze.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_BBand_Reversal | docs/Condition/Min/Condition_Min_BBand_Reversal.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Bollinger_Bounce | docs/Condition/Min/Condition_Min_Bollinger_Bounce.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Bollinger_Breakout_Strategy | docs/Condition/Min/Condition_Min_Bollinger_Breakout_Strategy.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Bollinger_Squeeze | docs/Condition/Min/Condition_Min_Bollinger_Squeeze.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_CCI_Extreme | docs/Condition/Min/Condition_Min_CCI_Extreme.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Candle_Pattern | docs/Condition/Min/Condition_Min_Candle_Pattern.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_MACD_Cross | docs/Condition/Min/Condition_Min_MACD_Cross.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_MACD_Crossover | docs/Condition/Min/Condition_Min_MACD_Crossover.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_MACD_GoldenCross | docs/Condition/Min/Condition_Min_MACD_GoldenCross.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_MA_Alignment | docs/Condition/Min/Condition_Min_MA_Alignment.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_MA_Convergence | docs/Condition/Min/Condition_Min_MA_Convergence.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_MFI_MoneyFlow | docs/Condition/Min/Condition_Min_MFI_MoneyFlow.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_MFI_Money_Flow | docs/Condition/Min/Condition_Min_MFI_Money_Flow.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Moving_Average_Golden_Cross | docs/Condition/Min/Condition_Min_Moving_Average_Golden_Cross.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_MultiIndicator_Composite | docs/Condition/Min/Condition_Min_MultiIndicator_Composite.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Multi_Indicator_Fusion | docs/Condition/Min/Condition_Min_Multi_Indicator_Fusion.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Multi_MA_Cross | docs/Condition/Min/Condition_Min_Multi_MA_Cross.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_ROC_Momentum | docs/Condition/Min/Condition_Min_ROC_Momentum.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_RSI_Divergence | docs/Condition/Min/Condition_Min_RSI_Divergence.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_RSI_Oversold | docs/Condition/Min/Condition_Min_RSI_Oversold.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_RSI_Reversal | docs/Condition/Min/Condition_Min_RSI_Reversal.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_SAR_Reversal | docs/Condition/Min/Condition_Min_SAR_Reversal.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Stochastic_Cross | docs/Condition/Min/Condition_Min_Stochastic_Cross.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Stochastic_Crossover | docs/Condition/Min/Condition_Min_Stochastic_Crossover.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Stochastic_Oversold | docs/Condition/Min/Condition_Min_Stochastic_Oversold.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Study_source | docs/Condition/Min/Condition_Min_Study_source.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_SupportResistance | docs/Condition/Min/Condition_Min_SupportResistance.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Trend_Following | docs/Condition/Min/Condition_Min_Trend_Following.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Volume_Breakout | docs/Condition/Min/Condition_Min_Volume_Breakout.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Volume_Momentum | docs/Condition/Min/Condition_Min_Volume_Momentum.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Volume_Price_Trend | docs/Condition/Min/Condition_Min_Volume_Price_Trend.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_Volume_Weighted | docs/Condition/Min/Condition_Min_Volume_Weighted.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Min_WilliamsR_Oversold | docs/Condition/Min/Condition_Min_WilliamsR_Oversold.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_RSI_Oversold_Rebound | docs/Condition/Min/Condition_RSI_Oversold_Rebound.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Stomer_Min | docs/Condition/Min/Condition_Stomer_Min.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_1_Min | docs/Condition/Min/Condition_Study_1_Min.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_2_Min | docs/Condition/Min/Condition_Study_2_Min.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_3_9010_min | docs/Condition/Min/Condition_Study_3_9010_min.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Condition_Study_3_902_min | docs/Condition/Min/Condition_Study_3_902_min.md | Min | Not started | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

## 리뷰 플랜

| Step | Description | Status |
| --- | --- | --- |
| 1 | Tick 조건식을 한 문서씩 열고 Condition_Document_Template_Guideline.md 조항과 직접 대조하며 상단 참조/개요/구조/명명 규칙을 점검 후 체크 테이블 업데이트 | Not started |
| 2 | 동일하게 가이드를 옆에 둔 채로 self.vars 매핑, 초기값/if-elif 패턴, 백테스트 호환성 등 코드 패턴 요소를 검토 | Not started |
| 3 | 최적화 경우의 수 계산, 개선 방향 연구 섹션, 모호 표현 여부를 가이드라인 항목별로 재확인하며 점검 | Not started |
| 4 | Min 조건식 문서도 문서별로 가이드라인을 병행 열람하여 동일 기준을 적용하고 누락/위반 사항을 기록 | Not started |
| 5 | 모든 문서에 대해 수정 우선순위와 실행 계획을 수립하고 후속 커밋으로 반영 (필요 시 가이드라인 재검토) | Not started |
