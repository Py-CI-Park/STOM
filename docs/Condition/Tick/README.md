# Tick 조건식 문서 모음

> 초(秒) 단위 틱 데이터 기반 고빈도 트레이딩 전략 조건식 문서

**📍 위치**: `docs/Condition/Tick/`
**📅 최종 업데이트**: 2025-11-29
**✅ 가이드라인 준수율**: 98.3% (전체 최적화 섹션 포함)
**🔄 검토 프로세스**: 3단계 검토 시스템 운영 중

---

## 📋 목차

- [개요](#개요)
- [조건식 문서 목록](#조건식-문서-목록)
  - [프로덕션 조건식](#프로덕션-조건식-production)
  - [연구 및 스터디 조건식](#연구-및-스터디-조건식)
  - [AI 생성 조건식](#ai-생성-조건식)
  - [테스트 및 템플릿](#테스트-및-템플릿)
- [문서 작성 가이드](#문서-작성-가이드)
- [관련 문서](#관련-문서)

---

## 개요

이 폴더는 **초(秒) 단위 틱 데이터**를 활용한 고빈도 트레이딩 전략의 조건식 문서를 모아둔 곳입니다.

### 📢 3단계 검토 프로세스 도입 (2025-11-29)

**체계적인 품질 관리를 위한 3단계 검토 프로세스**를 운영합니다:

- **1_To_be_reviewed/** (검토 대기): 63개
  - 초기 작성 완료 후 검토 대기 중인 조건식
  - 기본적인 문서 구조와 조건식 코드는 작성되어 있음
  - 백테스팅 결과 검증 및 최적화 필요

- **2_Under_review/** (검토 중): 9개
  - 현재 검토 및 개선 작업이 진행 중인 조건식
  - 백테스팅 실행 중이거나 결과 분석 단계
  - 조건 개선 연구 및 최적화 진행 중

- **3_Review_finished/** (검토 완료): 0개
  - 검토가 완료되어 프로덕션 배포 가능한 조건식
  - 충분한 백테스팅 검증 완료
  - 문서화 및 최적화 작업 완료

### Tick 전략의 특징

- **시간 단위**: 1초 단위 실시간 데이터
- **타겟 시간**: 주로 장 시작 직후 (09:00~09:30)
- **데이터베이스**: `stock_tick_back.db`
- **변수**: 초당거래대금, 체결강도, 초당매수/매도수량 등 93개 컬럼
- **전략 유형**: 급등주 포착, 시가 갭 돌파, 체결강도 기반 매매

### 명명 규칙

```
C_T_[시작시간]_[종료시간]_[업데이트버전]_[매수/매도]
예: Condition_Tick_902_905_update_2 (09:02~09:05 구간, 2차 업데이트)
```

---

## 📊 전체 Tick 조건식 상세 목록 (68개)

> **표준화 완료 (2025-01-21)**: 모든 Tick 조건식이 [[Condition_Document_Template_Guideline]] 표준 형식을 준수합니다.

아래 표는 **모든 Tick 조건식의 핵심 특징**을 한눈에 볼 수 있도록 정리한 것입니다. 각 조건식의 대상 시간 구간, 대상 종목, 전략 타입, 핵심 변수를 비교하여 적합한 전략을 선택할 수 있습니다.

| 파일명 | 대상 시간 구간 | 대상 종목 | 전략 타입 | 핵심 변수 |
|--------|----------------|-----------|-----------|-----------|
| [Condition_Early_Momentum_Surge](./Condition_Early_Momentum_Surge.md) | 09:00:00 ~ 09:05:00 (장 시작 5분) | 전 종목 대상 | 장초 급등 모멘텀 포착 초단타 전략 | 초당거래대금, 체결강도, 급등 모멘텀 |
| [Condition_Find_1](./Condition_Find_1.md) | 09:00:00 ~ 15:30:00 (장 전체) | 시가총액 3,000억 차등 기준 | 틱 기반 종합 탐색 전략 | 초당거래대금, 체결강도, 등락율, 호가정보 |
| [Condition_MA_Breakout_Scalping](./Condition_MA_Breakout_Scalping.md) | 09:00:00 ~ 09:20:00 (장 시작 20분) | 전 종목 대상 | 이동평균선 돌파 스캘핑 전략 | 이동평균(60틱), 초당거래대금, 체결강도 |
| [Condition_Order_Book_Imbalance](./Condition_Order_Book_Imbalance.md) | 09:00:00 ~ 15:30:00 (장 전체) | 전 종목 대상 | 호가창 매수/매도 잔량 불균형 포착 전략 | 매수총잔량, 매도총잔량, 호가 불균형 비율 |
| [Condition_RSI_Reversal](./Condition_RSI_Reversal.md) | 09:00:00 ~ 15:30:00 (장 전체) | 전 종목 대상 | RSI 과매도 구간 반등 포착 전략 | RSI, 과매도 구간, 반등 신호 |
| [Condition_Stomer](./Condition_Stomer.md) | 09:00:00 ~ 15:30:00 (장 전체) | 시가총액 차등 기준 | 틱 기반 종합 전략 | 초당거래대금, 체결강도, 등락율, 호가정보 |
| [Condition_Strength_Reversal](./Condition_Strength_Reversal.md) | 09:00:00 ~ 15:30:00 (장 전체) | 전 종목 대상 | 체결강도 반전 포착 전략 | 체결강도, 반전 신호, 초당거래대금 |
| [Condition_Study_1](./Condition_Study_1.md) | 09:00:00 ~ 15:30:00 (장 전체) | 전 종목 대상 | 틱 기반 연구용 전략 | 초당거래대금, 체결강도, 등락율 |
| [Condition_Study_2](./Condition_Study_2.md) | 09:10:00 ~ 09:10:59 (특정 1분 구간) | 전 종목 대상 | 틱 기반 연구용 전략 | 초당거래대금, 체결강도, 등락율 |
| [Condition_Study_2_T](./Condition_Study_2_T.md) | 틱 데이터 기반 (시간대별) | 전 종목 대상 | 틱 기반 연구용 전략 | 초당거래대금, 체결강도, 등락율 |
| [Condition_Study_3_902](./Condition_Study_3_902.md) | 09:02:00 ~ 09:05:00 | 전 종목 대상 | 틱 기반 연구용 전략 (902 구간) | 초당거래대금, 체결강도, 등락율 |
| [Condition_Study_4_905](./Condition_Study_4_905.md) | 09:05:00 ~ 09:10:00 | 전 종목 대상 | 틱 기반 연구용 전략 (905 구간) | 초당거래대금, 체결강도, 등락율 |
| [Condition_Study_5_9010](./Condition_Study_5_9010.md) | 09:10:00 ~ 09:15:00 | 전 종목 대상 | 틱 기반 연구용 전략 (9010 구간) | 초당거래대금, 체결강도, 등락율 |
| [Condition_Study_93000](./Condition_Study_93000.md) | 09:30:00 이후 | 전 종목 대상 | 틱 기반 연구용 전략 (93000 이후 구간) | 초당거래대금, 체결강도, 등락율 |
| [Condition_Study_By_GPT_o1](./Condition_Study_By_GPT_o1.md) | 틱 데이터 기반 (장 전체) | 전 종목 대상 | AI 생성 실험적 전략 | AI 생성 조건식 |
| [Condition_Study_By_Grok3](./Condition_Study_By_Grok3.md) | 09:00:00 ~ 09:30:00 (장 초반) | 극초단타 매매 대상 종목 | AI(Grok3) 생성 극초단타 전략 (보유시간 10~60초) | AI 생성 조건식, 매수 세력 급증 포착 |
| [Condition_Study_High_Over](./Condition_Study_High_Over.md) | 09:00:00 ~ 15:30:00 (장 전체) | 전 종목 대상 | 고가 돌파 및 초과 전략 | 고가, 초당거래대금, 등락율 |
| [Condition_Test_Template](./Condition_Test_Template.md) | 테스트용 (가변) | 테스트용 전 종목 | 템플릿 및 테스트용 | 테스트용 변수 |
| [Condition_Tick_0900_0910_Opening_Volume](./Condition_Tick_0900_0910_Opening_Volume.md) | 09:00:00 ~ 09:10:00 (개장 직후 10분) | 시가총액 3,000억 미만, 가격대 1,500원~20,000원 | 개장 갭상승 + 대량거래 모멘텀 포착 | 초당거래대금, 체결강도, 시가등락율, 시가대비등락율, 초당순매수금액, 회전율 |
| [Condition_Tick_0930_1000_PostBreakout](./Condition_Tick_0930_1000_PostBreakout.md) | 09:30:00 ~ 10:00:00 (장 시작 30분 후 안정화 구간) | 시가총액 및 가격대 필터링 적용, 가격대 1,000원~50,000원 | 고가 돌파 후 재조정 완료 후 재진입 (PostBreakout) | 최고현재가(1800), 이동평균(60), 초당거래대금, 체결강도, 등락율각도 |
| [Condition_Tick_1000_1100_Breakout](./Condition_Tick_1000_1100_Breakout.md) | 10:00:00 ~ 11:00:00 (장 시작 1시간 후 안정화 구간) | 시가총액 및 가격대 필터링 적용, 가격대 1,000원~50,000원 | 고가 돌파 모멘텀 포착 (Breakout) | 최고현재가(600), 이동평균(60/120/180), 초당거래대금, 체결강도, 등락율각도 |
| [Condition_Tick_1100_1200_Consolidation_Breakout](./Condition_Tick_1100_1200_Consolidation_Breakout.md) | 11:00:00 ~ 12:00:00 (장 중반 횡보 구간) | 가격대 2,000원~20,000원, 시가총액 차등 (1,500억/3,000억 기준) | 횡보 돌파 + 체결강도 급상승 (Consolidation Breakout) | 초당거래대금, 체결강도, 초당순매수금액, 최고체결강도(60), 최저체결강도(60), 등락율각도 |
| [Condition_Tick_1130_1200_PreLunch](./Condition_Tick_1130_1200_PreLunch.md) | 11:30:00 ~ 12:00:00 (점심시간 전 청산 구간) | 관심종목, 가격대 1,000원~50,000원 | 점심시간 전 포지션 정리 (PreLunch) | 등락율각도(30/60), 초당거래대금평균(60/120), 초당매수수량, 초당매도수량 |
| [Condition_Tick_1130_1300_Lunch_Volatility](./Condition_Tick_1130_1300_Lunch_Volatility.md) | 11:30:00 ~ 13:00:00 (점심시간 전후) | 가격대 2,500원~18,000원, 시가총액 차등 (2,000억/4,000억 기준) | 변동성 확대 포착 (Lunch Volatility) | 등락율각도(30/60), 전일비각도(60), 체결강도, 초당거래대금, 초당순매수금액, 최고체결강도(60), 최저체결강도(60) |
| [Condition_Tick_1300_1400_AfternoonRebound](./Condition_Tick_1300_1400_AfternoonRebound.md) | 13:00:00 ~ 14:00:00 (오후 장 초반) | 관심종목 | 점심시간 이후 반등 포착 (Afternoon Rebound) | 초당거래대금평균(120), 체결강도, 최저체결강도(120), 최저현재가(60), 이동평균(60) |
| [Condition_Tick_1300_1400_Strength_Surge](./Condition_Tick_1300_1400_Strength_Surge.md) | 13:00:00 ~ 14:00:00 (오후 초반) | 가격대 3,000원~25,000원, 시가총액 차등 (2,000억/5,000억 기준) | 체결강도 급등 포착 (Strength Surge) | 체결강도평균(30), 체결강도N(1), 최고체결강도(60), 누적초당매수수량(30), 누적초당매도수량(30), 초당순매수금액 |
| [Condition_Tick_1400_1430_Closing_Momentum](./Condition_Tick_1400_1430_Closing_Momentum.md) | 14:00:00 ~ 14:30:00 (장 마감 전) | 가격대 2,000원~30,000원, 시가총액 2,000억 기준 | 마감 전 급등 포착 (Pre-Closing Surge) | 등락율각도(30), 초당거래대금평균(30), 체결강도, 최고초당매수수량(60), 초당순매수금액 |
| [Condition_Tick_1430_1500_ClosingMomentum](./Condition_Tick_1430_1500_ClosingMomentum.md) | 14:30:00 ~ 15:00:00 (장 마감 30분) | 관심종목 | 마감 모멘텀 포착 (Closing Momentum) | 초당거래대금평균(180), 등락율각도(30), 당일거래대금각도(30), 최고초당매수수량(60), 최고초당매도수량(60) |
| [Condition_Tick_900_920](./Condition_Tick_900_920.md) | N/A | N/A | N/A | N/A |
| [Condition_Tick_900_920_Enhanced](./Condition_Tick_900_920_Enhanced.md) | N/A | N/A | N/A | N/A |
| [Condition_Tick_900_930_Composite_Study](./Condition_Tick_900_930_Composite_Study.md) | 09:00:00 ~ 09:30:00 (장 시작 30분 전체) | 관심종목, 가격대 1,000원~50,000원, 시가총액 3,000억 미만 | 시간대별 복합 패턴 종합 (Composite Multi-Pattern) | 시가등락율, 시가대비등락율, 초당순매수금액, 초당거래대금, 체결강도, 이동평균, 아래꼬리비율, 고점돌파여부 |
| [Condition_Tick_902](./Condition_Tick_902.md) | 09:00:00 ~ 09:02:00 (장 시작 2분) | 시가총액 3,000억 이하 중소형주 | 틱 기반 장 초반 극초단타 전략 | 체결강도, 초당거래대금, 등락율각도, VI호가, 라운드피겨 |
| [Condition_Tick_902_905](./Condition_Tick_902_905.md) | N/A | 시가총액 3,000억 미만, 가격대 1,000원~50,000원 | 갭상승 + 거래대금 가속 모멘텀 추종 | 체결강도, 초당거래대금, 시가등락율, 회전율, 당일거래대금각도 |
| [Condition_Tick_902_905_update](./Condition_Tick_902_905_update.md) | 09:00:00 ~ 09:05:00 (장 시작 5분) | 전 종목 대상 | 틱 기반 902/905 통합 전략 | 체결강도, 초당거래대금, 등락율각도, 시가총액 차등 조건 |
| [Condition_Tick_902_905_update_2](./Condition_Tick_902_905_update_2.md) | 09:00:00 ~ 09:05:00 (장 시작 5분) | 전 종목 대상 | 틱 기반 902/905 통합 전략 (버전 2) | 체결강도, 초당거래대금, 회전율, 당일거래대금각도 |
| [Condition_Tick_902_Update](./Condition_Tick_902_Update.md) | 09:00:00 ~ 09:02:00 (개장 초반 2분) | 시가총액 3,000억 미만, 가격대 1,000원~50,000원 | 갭상승 + 거래대금 폭발 모멘텀 포착 | 시가등락율, 초당거래대금, 체결강도, 회전율, 전일비, 당일거래대금각도 |
| [Condition_Tick_905_915_LongTail](./Condition_Tick_905_915_LongTail.md) | 09:05:00 ~ 09:15:00 (장 시작 5분 후 ~ 15분 후) | 시가총액별 구분, 가격대 1,000원~50,000원 | 긴 아래 꼬리 + V자 반등 패턴 포착 | 고저평균대비등락율, 초당거래대금비율, 체결강도, 등락율각도, 전일비, 회전율 |
| [Condition_Tick_910_930_Rebound](./Condition_Tick_910_930_Rebound.md) | 09:10:00 ~ 09:30:00 (장 시작 10분 후 ~ 30분 후) | 시가총액별 구분, 가격대 1,000원~50,000원 | 조정 후 재상승 돌파 패턴 포착 | 최고현재가(300), 초당거래대금비율, 체결강도, 등락율각도, 이동평균(60/120) |
| [Condition_Tick_925_935_Angle_Strategy](./Condition_Tick_925_935_Angle_Strategy.md) | N/A | 시가총액 차등 (1,500억 / 2,500억 / 그 이상) | 각도 지표 복합 활용 + 체결강도 변동성 + 호가잔량 밸런스 | 등락율각도, 전일비각도, 당일거래대금각도, 체결강도 변동성, 누적지표 |
| [Condition_Tick_930_1000_Early_Momentum_Continuation](./Condition_Tick_930_1000_Early_Momentum_Continuation.md) | 09:30:00 ~ 10:00:00 (장 안정화 구간) | 관심종목, 가격대 1,000원~50,000원, 시가총액 차등 (2,500억/5,000억 기준) | 초기 모멘텀 지속 + 추세 확인 (Early Momentum Continuation) | 시가등락율, 시가대비등락율, 초당순매수금액, 이동평균(30/60/120), 체결강도평균(60), 고가대비하락율, 거래대금안정성 |
| [Condition_Tick_930_1000_Momentum](./Condition_Tick_930_1000_Momentum.md) | 09:30:00 ~ 10:00:00 (장 시작 30분 이후 안정화 구간) | 시가총액 3,000억 미만 중소형주, 가격대 1,000원~30,000원 | 모멘텀 지속 추종 (Momentum Continuation) | 체결강도, 이동평균정배열, 등락율각도(60/120), 당일거래대금각도, RSI, MACD |
| [Condition_Tick_935_945_Momentum](./Condition_Tick_935_945_Momentum.md) | N/A | 시가총액 차등 (2,000억 / 5,000억 / 그 이상) | 체결강도 모멘텀 + 거래대금 가속 + 등락율각도 복합 전략 | 체결강도, 초당거래대금, 등락율각도, 당일거래대금각도, 누적초당매수/매도수량 |
| [Condition_Tick_Ask_Spread_Narrow](./Condition_Tick_Ask_Spread_Narrow.md) | 09:00:00 ~ 09:20:00 (장 초반 20분) | 시가총액 차등 기준 (1,500억, 3,000억) | 호가 스프레드 축소 감지 전략 | 스프레드, 스프레드비율, 매수/매도총잔량 |
| [Condition_Tick_BidWall_Surge](./Condition_Tick_BidWall_Surge.md) | 09:00:00 ~ 09:20:00 (장 초반) | 가격대 1,000원~50,000원, 시가총액 차등 (1,500억 기준) | 호가창 매수벽 급증 포착 (Bid Wall Surge) | 매수총잔량, 매도총잔량, 호가잔량비율, 매수벽강도, 초당매수수량, 초당순매수금액 |
| [Condition_Tick_Bid_Ask_Pressure](./Condition_Tick_Bid_Ask_Pressure.md) | 09:00:00 ~ 09:20:00 (장 초반 20분) | 시가총액 2,000억 차등 기준 | 호가창 불균형 포착 전략 | 매수총잔량, 매도총잔량, 호가 불균형 |
| [Condition_Tick_Breakout_Confirmation](./Condition_Tick_Breakout_Confirmation.md) | 09:00:00 ~ 09:20:00 (장 시작 20분) | 시가총액 차등 (3,200억 기준), 가격대 1,800원~42,000원 | 고가 돌파 + 거래량 동반 확인 (Breakout Confirmation) | 최고현재가(60), 초당거래대금, 체결강도, 데이터길이 |
| [Condition_Tick_ConsolidationBreakout](./Condition_Tick_ConsolidationBreakout.md) | 09:05:00 ~ 14:30:00 (장중 전체) | 관심종목, 가격대 1,000원~50,000원 | 횡보 돌파 (Consolidation Breakout) | 횡보구간범위, 최고현재가(300), 최저현재가(300), 초당거래대금평균(300), 돌파강도, 초당매수수량, 초당매도수량 |
| [Condition_Tick_Continuous_Buy](./Condition_Tick_Continuous_Buy.md) | 09:00:00 ~ 09:20:00 (장 초반) | 가격대 800원~35,000원, 시가총액 차등 (1,500억/3,000억 기준) | 연속 매수틱 포착 (Continuous Buy Tick) | 연속상승틱, 연속매수우위, 체결강도(연속), 등락율각도(15), 이동평균(20), 최고초당매수수량(25) |
| [Condition_Tick_Early_Breakout](./Condition_Tick_Early_Breakout.md) | 09:00:00 ~ 09:20:00 (장 시작 20분, 특히 60틱 이내) | 시가총액 차등 (2,500억 기준), 가격대 필터링 적용 | 장 시작 직후 급등 돌파 포착 (Early Breakout) | 데이터길이, 등락율, 전일비, 전일동시간비, 초당거래대금, 체결강도 |
| [Condition_Tick_GapTrading](./Condition_Tick_GapTrading.md) | 09:00:00 ~ 10:00:00 (장 시작 1시간) | 관심종목, 가격대 1,000원~50,000원, 갭비율 2% 이상 | 갭 확대 포착 (Gap Trading) | 갭비율, 시가대비상승율, 초당거래대금평균(60/120), 초당매수수량, 초당매도수량 |
| [Condition_Tick_Gap_Up_Continuation](./Condition_Tick_Gap_Up_Continuation.md) | 09:00:00 ~ 09:20:00 (장 시작 20분) | 시가총액 차등 (2,500억 기준), 시가등락율 2% 이상 갭상승 | 갭상승 지속 (Gap Up Continuation) | 시가등락율, 시가대비등락율, 저가, 체결강도, 등락율각도, 매수총잔량, 매도총잔량 |
| [Condition_Tick_MarketCap_Differential](./Condition_Tick_MarketCap_Differential.md) | 09:00:00 ~ 09:20:00 (장 시작 20분) | 시가총액 차등 적용 | 시가총액별 차별화 전략 | 시가총액, 초당거래대금, 체결강도 |
| [Condition_Tick_MomentumReversal](./Condition_Tick_MomentumReversal.md) | 09:00:00 ~ 15:30:00 (장 전체) | 시가총액 3,000억 차등 기준 | 틱 기반 모멘텀 반전 포착 전략 | 등락율각도, 저점대비반등률, 초당매수/매도수량 |
| [Condition_Tick_Momentum_Acceleration](./Condition_Tick_Momentum_Acceleration.md) | 09:00:00 ~ 09:20:00 (장 초반) | 가격대 1,100원~41,000원, 시가총액 차등 (1,500억/3,000억 기준) | 등락율 모멘텀 가속 포착 (Momentum Acceleration) | 등락율가속도, 등락율변화, 등락율각도(17), 현재가(연속), 체결강도, 초당거래대금평균(23) |
| [Condition_Tick_Momentum_Surge](./Condition_Tick_Momentum_Surge.md) | 09:00:00 ~ 09:20:00 (장 시작 20분) | 시가총액 차등 (3,000억/10,000억 기준), 가격대 필터링 적용 | 가격 상승 모멘텀 급등 포착 (Momentum Surge) | 등락율각도, 이동평균(30/60/90), 체결강도, 전일비각도, 당일거래대금각도, 회전율 |
| [Condition_Tick_Net_Buy_Surge](./Condition_Tick_Net_Buy_Surge.md) | 09:00:00 ~ 09:20:00 (장 초반) | 가격대 950원~39,000원, 시가총액 차등 (1,500억/3,000억 기준) | 순매수 급증 포착 (Net Buy Surge) | 순매수금액, 순매수비율, 초당매수수량, 누적초당매수수량(20), 체결강도, 등락율각도(19) |
| [Condition_Tick_Opening_Momentum](./Condition_Tick_Opening_Momentum.md) | 09:00:00 ~ 09:20:00 (장 시작 20분) | 시가총액 차등 (3,500억 기준), 가격대 2,000원~45,000원 | 갭 상승 + 강한 모멘텀 포착 (Opening Momentum) | 시가등락율, 시가대비등락율, 고가대비하락율, 등락율각도, 초당거래대금 |
| [Condition_Tick_PriceAction](./Condition_Tick_PriceAction.md) | 09:00:00 ~ 15:30:00 (장 전체) | 시가총액 3,000억 차등 기준 | 틱 기반 가격 패턴 분석 전략 | Higher Low 패턴, 고가/저가 근접도, 가격 압축/확장 |
| [Condition_Tick_Quick_Scalping](./Condition_Tick_Quick_Scalping.md) | 09:00:00 ~ 09:20:00 (장 초반 20분) | 시가총액 2,000억 차등 기준 | 초단타 스캘핑 (3~5분 극초단타) | 초당거래대금, 체결강도, 즉시 반응 지표 |
| [Condition_Tick_SellWall_Exhaustion](./Condition_Tick_SellWall_Exhaustion.md) | 09:00:00 ~ 09:20:00 (장 초반 20분) | 시가총액 차등 기준 (1,500억, 3,000억) | 매도벽 소진 포착 전략 | 매도잔량감소율, 매도벽비율, 초당매수수량 |
| [Condition_Tick_Strength_Reversal](./Condition_Tick_Strength_Reversal.md) | 09:00:00 ~ 09:20:00 (장 초반 20분) | 시가총액 차등 기준 (1,500억, 3,000억) | 체결강도 급반전 포착 전략 | 체결강도, 체결강도차이, 체결강도평균대비 |
| [Condition_Tick_Strong_Bid_Support](./Condition_Tick_Strong_Bid_Support.md) | 09:00:00 ~ 09:20:00 (장 시작 20분) | 시가총액 차등 (3,000억/10,000억 기준), 가격대 필터링 적용 | 매수호가 집중 + 호가잔량 우위 포착 (Strong Bid Support) | 매수총잔량, 매도총잔량, 매수잔량1~3, 초당매수수량, 체결강도 |
| [Condition_Tick_Volatility_Expansion](./Condition_Tick_Volatility_Expansion.md) | 09:00:00 ~ 09:20:00 (장 초반) | 가격대 850원~36,000원, 시가총액 차등 (1,500억/3,000억 기준) | 변동성 확대 포착 (Volatility Expansion) | 변동폭비율, 변동폭증가율, 체결강도, 초당거래대금평균(25), 등락율각도(16) |
| [Condition_Tick_VolumeSpike](./Condition_Tick_VolumeSpike.md) | 09:02:00 ~ 15:00:00 (장중 전체) | 관심종목, 가격대 1,000원~50,000원 | 거래량 급증 감지 (Volume Spike) | 초당거래대금평균(120), 초당매수수량, 초당매도수량, 등락율각도(30/60), 체결강도평균(60) |
| [Condition_Tick_Volume_Burst](./Condition_Tick_Volume_Burst.md) | 09:00:00 ~ 09:20:00 (장 시작 20분) | 시가총액 차등 (2,500억 기준), 등락율 2~15% | 거래량 급증 돌파 (Volume Burst Breakout) | 초당거래대금평균(60), 체결강도, 초당매수수량, 매도총잔량, 전일비, 전일동시간비 |
| [Condition_Tick_Volume_Explosion](./Condition_Tick_Volume_Explosion.md) | 09:00:00 ~ 09:20:00 (장 시작 20분) | 시가총액 차등 (1,500억/3,000억 기준), 가격대 1,000원~40,000원 | 거래대금 급증 및 매수 폭발 모멘텀 포착 (Volume Explosion) | 초당거래대금, 초당매수수량, 거래대금배율, 매수폭발도, 체결강도, 등락율각도 |
| [Condition_Tick_Volume_Surge](./Condition_Tick_Volume_Surge.md) | 장중 전체 (시간대 제한 없음) | 시가총액 및 가격대 필터링 적용 | 거래량 급증 및 매수세 급등 포착 (Volume Surge) | 초당거래대금, 체결강도, 누적초당매수수량, 당일거래대금각도, 등락율각도 |
| [Condition_Volume_Explosion](./Condition_Volume_Explosion.md) | 09:10:00 ~ 09:15:00 (장 시작 10~15분) | 시가총액 차등 (1,500억/2,500억 기준), 가격대 2,000원~45,000원 | 거래대금 폭발적 증가 포착 (Volume Explosion) | 초당거래대금, 당일거래대금각도, 체결강도, 등락율각도, 전일비, 전일동시간비 |

**총 68개의 Tick 조건식**이 표준화되어 있습니다.

💡 **활용 팁**:
- **시간대별 선택**: 장 초반(09:00~09:30)에 집중하려면 Opening, Gap, Early 관련 전략 활용
- **전략 타입별 선택**: 호가창 분석은 BidWall, Ask 관련, 모멘텀은 Momentum, Surge 관련 전략 참조
- **종목 필터링**: 시가총액에 따라 차등 조건이 적용된 전략을 선택하여 최적화

---

## 조건식 문서 목록

### 📊 전체 통계

- **전체 조건식**: 72개
- **검토 프로세스**:
  - 검토 대기 (1_To_be_reviewed): 63개 (87.5%)
  - 검토 중 (2_Under_review): 9개 (12.5%)
  - 검토 완료 (3_Review_finished): 0개 (0%)
- **카테고리**: 8개 (시간대별 + 전략별)
- **핵심 시간대**: 09:00-09:30 (장 초반 급등주 포착)
- **주요 전략**: 모멘텀, 거래량, 호가창, 갭/돌파

---

## 검토 단계별 조건식 현황

### 1️⃣ 검토 대기 중 (1_To_be_reviewed/) - 63개

초기 작성이 완료되어 검토 대기 중인 조건식입니다. 기본적인 문서 구조와 조건식 코드는 작성되어 있으나, 백테스팅 결과 검증 및 최적화 작업이 필요합니다.

**📂 위치**: `docs/Condition/Tick/1_To_be_reviewed/`

**주요 조건식**:
- Condition_Early_Momentum_Surge.md
- Condition_Find_1.md
- Condition_MA_Breakout_Scalping.md
- Condition_Order_Book_Imbalance.md
- Condition_RSI_Reversal.md
- (외 58개)

### 2️⃣ 검토 진행 중 (2_Under_review/) - 9개

현재 검토 및 개선 작업이 진행 중인 조건식입니다. 백테스팅 실행 중이거나 결과 분석 단계에 있습니다.

**📂 위치**: `docs/Condition/Tick/2_Under_review/`

**주요 조건식**:
- Condition_Tick_902.md - 장 시작 2분 집중 전략
- Condition_Tick_902_905.md - 초기 통합 버전
- Condition_Tick_902_905_update.md - 1차 업데이트
- Condition_Tick_902_905_update_2.md - 2차 업데이트 (골드 스탠다드)
- Condition_Tick_902_905_update_3.md - 3차 업데이트 (최신)
- Condition_Tick_902_Update.md - 902 업데이트
- (외 소스 파일 3개)

### 3️⃣ 검토 완료 (3_Review_finished/) - 0개

검토가 완료되어 프로덕션 배포 가능한 조건식입니다. 현재는 검토 완료된 조건식이 없습니다.

**📂 위치**: `docs/Condition/Tick/3_Review_finished/`

**상태**: 검토 완료된 조건식 없음 (검토 진행 중)

---

## 카테고리별 조건식 목록 (참고용)

### 프로덕션 조건식 (Production)

✅ 검증 완료 및 실전 배포 가능한 고품질 조건식

#### 🏆 추천 조건식 (Template Compliant)

| 파일명 | 시간대 | 전략 개요 | 상태 | 문서 품질 |
|--------|--------|-----------|------|-----------|
| [Condition_Tick_902_905_update_2.md](./Condition_Tick_902_905_update_2.md) | 09:02~09:05 | 시가등락율 + 체결강도 기반 급등주 포착 | ✅ 프로덕션 | ⭐⭐⭐⭐⭐ |
| [Condition_Tick_900_920.md](./Condition_Tick_900_920.md) | 09:00~09:20 | 4구간 분할 다중 시간대 전략 | ✅ 프로덕션 | ⭐⭐⭐⭐⭐ |
| [Condition_Tick_900_920_Enhanced.md](./Condition_Tick_900_920_Enhanced.md) | 09:00~09:20 | 900_920 대폭 고도화 - 시가총액 3티어 × 4시간대 = 12전략 조합 | ✅ 프로덕션 | ⭐⭐⭐⭐⭐ |
| [Condition_Tick_925_935_Angle_Strategy.md](./Condition_Tick_925_935_Angle_Strategy.md) | 09:25~09:35 | 각도 지표 삼각 검증 - 등락율/전일비/거래대금 각도 + 체결강도변동성 | ✅ 프로덕션 | ⭐⭐⭐⭐⭐ |
| [Condition_Tick_900_930_Composite_Study.md](./Condition_Tick_900_930_Composite_Study.md) | 09:00~09:30 | 종합 조건식 (복합 지표) | ✅ 프로덕션 | ⭐⭐⭐⭐ |

**특징**:
- `Condition_Document_Template_Guideline.md` 완벽 준수
- 공통 계산 지표, 시간대별 분기, 시가총액 차등 조건 구현
- 최적화 변수 및 GA 범위 상세 명시
- 조건 개선 연구 섹션 포함

#### 📌 기타 프로덕션 조건식

| 파일명 | 시간대 | 전략 개요 | 버전 |
|--------|--------|-----------|------|
| [Condition_Tick_902_905_update.md](./Condition_Tick_902_905_update.md) | 09:02~09:05 | 1차 업데이트 버전 | v1 |
| [Condition_Tick_902_Update.md](./Condition_Tick_902_Update.md) | 09:02 | 시작 2분 집중 전략 | v1 |
| [Condition_Tick_902.md](./Condition_Tick_902.md) | 09:02 | 초기 버전 | v0 |
| [Condition_Tick_902_905.md](./Condition_Tick_902_905.md) | 09:02~09:05 | 초기 통합 버전 | v0 |
| [Condition_Tick_905_915_LongTail.md](./Condition_Tick_905_915_LongTail.md) | 09:05~09:15 | 롱테일 급등주 전략 | v1 |
| [Condition_Tick_910_930_Rebound.md](./Condition_Tick_910_930_Rebound.md) | 09:10~09:30 | 반등 포착 전략 | v1 |

---

### 연구 및 스터디 조건식

🔬 백테스팅 및 분석 단계의 연구용 조건식

| 파일명 | 주요 연구 내용 | 상태 |
|--------|---------------|------|
| [Condition_Study_1.md](./Condition_Study_1.md) | 기본 Tick 전략 연구 | 📊 연구 |
| [Condition_Study_2.md](./Condition_Study_2.md) | 2차 개선 연구 | 📊 연구 |
| [Condition_Study_2_T.md](./Condition_Study_2_T.md) | 2차 연구 변형 (T버전) | 📊 연구 |
| [Condition_Study_3_902.md](./Condition_Study_3_902.md) | 09:02 구간 집중 연구 | 📊 연구 |
| [Condition_Study_4_905.md](./Condition_Study_4_905.md) | 09:05 구간 집중 연구 | 📊 연구 |
| [Condition_Study_5_9010.md](./Condition_Study_5_9010.md) | 09:10 구간 집중 연구 | 📊 연구 |
| [Condition_Study_93000.md](./Condition_Study_93000.md) | 전일 대비 3배 급등 연구 | 📊 연구 |
| [Condition_Study_High_Over.md](./Condition_Study_High_Over.md) | 신고가 돌파 전략 연구 | 📊 연구 |
| [Condition_Find_1.md](./Condition_Find_1.md) | 조건 탐색 1차 연구 | 📊 연구 |
| [Condition_Stomer.md](./Condition_Stomer.md) | Stomer 전략 연구 | 📊 연구 |

---

### AI 생성 조건식

🤖 AI 모델이 생성한 전략 아이디어 (검증 필요)

| 파일명 | 생성 AI | 내용 | 상태 |
|--------|---------|------|------|
| [Condition_Study_By_GPT_o1.md](./Condition_Study_By_GPT_o1.md) | GPT-o1 | GPT-o1 제안 전략 | 🔍 검증 필요 |
| [Condition_Study_By_Grok3.md](./Condition_Study_By_Grok3.md) | Grok3 | Grok3 제안 전략 | 🔍 검증 필요 |

**Note**: AI 생성 조건식은 백테스팅 검증 후 프로덕션 이동 권장

---

### 테스트 및 템플릿

🧪 개발 및 테스트용 문서

| 파일명 | 용도 | 설명 |
|--------|------|------|
| [Condition_Test_Template.md](./Condition_Test_Template.md) | 테스트 템플릿 | 새로운 조건식 개발 시 사용하는 빈 템플릿 |

---

### 소스 파일 (Source)

📄 원본 코드 또는 참고용 소스

| 파일명 | 설명 |
|--------|------|
| [Condition_Tick_902_905_update_2_source.md](./Condition_Tick_902_905_update_2_source.md) | update_2의 원본 소스 코드 |
| [Condition_Tick_902_905_update_source.md](./Condition_Tick_902_905_update_source.md) | update_1의 원본 소스 코드 |
| [Condition_Tick_902_update_source.md](./Condition_Tick_902_update_source.md) | 902 업데이트의 원본 소스 코드 |

---

### 서브폴더: 20250808_study

**📂 위치**: `docs/Condition/Tick/20250808_study/`

특정 날짜 연구 자료 모음

| 파일명 | 연구 내용 |
|--------|-----------|
| [Condition_Study_Open_Breakout.md](./20250808_study/Condition_Study_Open_Breakout.md) | 시가 돌파 전략 연구 (2025-08-08) |

---

## 전략 유형별 분류

### 1️⃣ 시간대별 전략 (27개)

장 시작부터 마감까지 시간대별 특화 전략

#### 🌅 장 초반 (09:00-09:30) - 18개

급등주 포착의 핵심 시간대

| 파일명 | 시간대 | 전략 핵심 | 상태 |
|--------|--------|-----------|------|
| [Condition_Tick_0900_0910_Opening_Volume.md](./Condition_Tick_0900_0910_Opening_Volume.md) | 09:00-09:10 | 시작 10분 거래량 급증 | ✅ |
| [Condition_Tick_900_920.md](./Condition_Tick_900_920.md) | 09:00-09:20 | 4구간 분할 다중 시간대 | ⭐⭐⭐⭐⭐ |
| [Condition_Tick_900_920_Enhanced.md](./Condition_Tick_900_920_Enhanced.md) | 09:00-09:20 | 시가총액 3티어 × 4시간대 조합 | ⭐⭐⭐⭐⭐ |
| [Condition_Tick_900_930_Composite_Study.md](./Condition_Tick_900_930_Composite_Study.md) | 09:00-09:30 | 종합 복합 지표 | ⭐⭐⭐⭐ |
| [Condition_Tick_902.md](./Condition_Tick_902.md) | 09:02 | 시작 2분 집중 | ✅ |
| [Condition_Tick_902_905.md](./Condition_Tick_902_905.md) | 09:02-09:05 | 초기 통합 버전 | ✅ |
| [Condition_Tick_902_905_update.md](./Condition_Tick_902_905_update.md) | 09:02-09:05 | 1차 업데이트 | ✅ |
| [Condition_Tick_902_905_update_2.md](./Condition_Tick_902_905_update_2.md) | 09:02-09:05 | 2차 업데이트 | ⭐⭐⭐⭐⭐ |
| [Condition_Tick_902_Update.md](./Condition_Tick_902_Update.md) | 09:02 | 902 업데이트 | ✅ |
| [Condition_Tick_905_915_LongTail.md](./Condition_Tick_905_915_LongTail.md) | 09:05-09:15 | 롱테일 급등주 | ✅ |
| [Condition_Tick_910_930_Rebound.md](./Condition_Tick_910_930_Rebound.md) | 09:10-09:30 | 반등 포착 | ✅ |
| [Condition_Tick_925_935_Angle_Strategy.md](./Condition_Tick_925_935_Angle_Strategy.md) | 09:25-09:35 | 각도 지표 삼각 검증 | ⭐⭐⭐⭐⭐ |
| [Condition_Tick_930_1000_Early_Momentum_Continuation.md](./Condition_Tick_930_1000_Early_Momentum_Continuation.md) | 09:30-10:00 | 초기 모멘텀 지속 | ✅ |
| [Condition_Tick_930_1000_Momentum.md](./Condition_Tick_930_1000_Momentum.md) | 09:30-10:00 | 모멘텀 전략 | ✅ |
| [Condition_Tick_0930_1000_PostBreakout.md](./Condition_Tick_0930_1000_PostBreakout.md) | 09:30-10:00 | 돌파 후 추격 | ✅ |
| [Condition_Tick_935_945_Momentum.md](./Condition_Tick_935_945_Momentum.md) | 09:35-09:45 | 935-945 모멘텀 | ✅ |
| [Condition_Tick_Opening_Momentum.md](./Condition_Tick_Opening_Momentum.md) | 09:00-09:20 | 장 초반 모멘텀 | ✅ |
| [Condition_Early_Momentum_Surge.md](./Condition_Early_Momentum_Surge.md) | 09:00-09:30 | 초기 급등 모멘텀 | ✅ |

#### ☀️ 오전장 (10:00-12:00) - 5개

| 파일명 | 시간대 | 전략 핵심 | 상태 |
|--------|--------|-----------|------|
| [Condition_Tick_1000_1100_Breakout.md](./Condition_Tick_1000_1100_Breakout.md) | 10:00-11:00 | 오전장 돌파 | ✅ |
| [Condition_Tick_1100_1200_Consolidation_Breakout.md](./Condition_Tick_1100_1200_Consolidation_Breakout.md) | 11:00-12:00 | 횡보 후 돌파 | ✅ |
| [Condition_Tick_1130_1200_PreLunch.md](./Condition_Tick_1130_1200_PreLunch.md) | 11:30-12:00 | 점심 전 마감 | ✅ |
| [Condition_Tick_1130_1300_Lunch_Volatility.md](./Condition_Tick_1130_1300_Lunch_Volatility.md) | 11:30-13:00 | 점심 시간 변동성 | ✅ |
| [Condition_Tick_ConsolidationBreakout.md](./Condition_Tick_ConsolidationBreakout.md) | 전체 | 횡보 구간 돌파 | ✅ |

#### 🌤️ 오후장 (13:00-15:00) - 4개

| 파일명 | 시간대 | 전략 핵심 | 상태 |
|--------|--------|-----------|------|
| [Condition_Tick_1300_1400_AfternoonRebound.md](./Condition_Tick_1300_1400_AfternoonRebound.md) | 13:00-14:00 | 오후 반등 | ✅ |
| [Condition_Tick_1300_1400_Strength_Surge.md](./Condition_Tick_1300_1400_Strength_Surge.md) | 13:00-14:00 | 오후 강세 급등 | ✅ |
| [Condition_Tick_1400_1430_Closing_Momentum.md](./Condition_Tick_1400_1430_Closing_Momentum.md) | 14:00-14:30 | 마감 모멘텀 | ✅ |
| [Condition_Tick_1430_1500_ClosingMomentum.md](./Condition_Tick_1430_1500_ClosingMomentum.md) | 14:30-15:00 | 마감 30분 | ✅ |

---

### 2️⃣ 모멘텀 기반 전략 (8개)

시가대비등락율, 체결강도, 급등 속도 등 모멘텀 지표 활용

| 파일명 | 전략 핵심 | 상태 |
|--------|-----------|------|
| [Condition_Early_Momentum_Surge.md](./Condition_Early_Momentum_Surge.md) | 초기 급등 모멘텀 포착 | ✅ |
| [Condition_Tick_Momentum_Acceleration.md](./Condition_Tick_Momentum_Acceleration.md) | 모멘텀 가속도 분석 | ✅ |
| [Condition_Tick_Momentum_Surge.md](./Condition_Tick_Momentum_Surge.md) | 모멘텀 급증 감지 | ✅ |
| [Condition_Tick_MomentumReversal.md](./Condition_Tick_MomentumReversal.md) | 모멘텀 반전 | ✅ |
| [Condition_Tick_Opening_Momentum.md](./Condition_Tick_Opening_Momentum.md) | 장 초반 모멘텀 | ✅ |
| [Condition_Tick_930_1000_Momentum.md](./Condition_Tick_930_1000_Momentum.md) | 930-1000 모멘텀 | ✅ |
| [Condition_Tick_935_945_Momentum.md](./Condition_Tick_935_945_Momentum.md) | 935-945 모멘텀 | ✅ |
| [Condition_Tick_930_1000_Early_Momentum_Continuation.md](./Condition_Tick_930_1000_Early_Momentum_Continuation.md) | 초기 모멘텀 지속 | ✅ |

**특징**: 등락율 각도, 체결강도 변화율, 시가대비 상승률 활용

---

### 3️⃣ 거래량 기반 전략 (6개)

초당거래대금, 거래량 급증, 거래 폭발 패턴 활용

| 파일명 | 전략 핵심 | 상태 |
|--------|-----------|------|
| [Condition_Tick_VolumeSpike.md](./Condition_Tick_VolumeSpike.md) | 거래량 스파이크 | ✅ |
| [Condition_Tick_Volume_Burst.md](./Condition_Tick_Volume_Burst.md) | 거래량 폭발 | ✅ |
| [Condition_Tick_Volume_Explosion.md](./Condition_Tick_Volume_Explosion.md) | 거래량 폭발적 증가 | ✅ |
| [Condition_Tick_Volume_Surge.md](./Condition_Tick_Volume_Surge.md) | 거래량 급증 | ✅ |
| [Condition_Volume_Explosion.md](./Condition_Volume_Explosion.md) | 거래량 폭발 (변형) | ✅ |
| [Condition_Tick_0900_0910_Opening_Volume.md](./Condition_Tick_0900_0910_Opening_Volume.md) | 시작 10분 거래량 | ✅ |

**특징**: 초당거래대금, 평균 대비 배수, 연속 증가 패턴

---

### 4️⃣ 호가창 기반 전략 (7개)

매수/매도 호가, 잔량, 호가 스프레드, 매도벽/매수벽 분석

| 파일명 | 전략 핵심 | 상태 |
|--------|-----------|------|
| [Condition_Order_Book_Imbalance.md](./Condition_Order_Book_Imbalance.md) | 호가 불균형 | ✅ |
| [Condition_Tick_Ask_Spread_Narrow.md](./Condition_Tick_Ask_Spread_Narrow.md) | 호가 스프레드 축소 | ✅ |
| [Condition_Tick_BidWall_Surge.md](./Condition_Tick_BidWall_Surge.md) | 매수벽 형성 | ✅ |
| [Condition_Tick_Bid_Ask_Pressure.md](./Condition_Tick_Bid_Ask_Pressure.md) | 매수/매도 압력 | ✅ |
| [Condition_Tick_SellWall_Exhaustion.md](./Condition_Tick_SellWall_Exhaustion.md) | 매도벽 소진 | ✅ |
| [Condition_Tick_Strong_Bid_Support.md](./Condition_Tick_Strong_Bid_Support.md) | 강력한 매수 지지 | ✅ |
| [Condition_Tick_Continuous_Buy.md](./Condition_Tick_Continuous_Buy.md) | 연속 매수 유입 | ✅ |

**특징**: 매도호가총잔량, 매수호가총잔량, 호가비율, 순매수금액

---

### 5️⃣ 갭/돌파 전략 (7개)

시가 갭, 신고가 돌파, 저항선 돌파 전략

| 파일명 | 전략 핵심 | 상태 |
|--------|-----------|------|
| [Condition_Tick_GapTrading.md](./Condition_Tick_GapTrading.md) | 갭 거래 전략 | ✅ |
| [Condition_Tick_Gap_Up_Continuation.md](./Condition_Tick_Gap_Up_Continuation.md) | 갭 상승 지속 | ✅ |
| [Condition_Tick_Breakout_Confirmation.md](./Condition_Tick_Breakout_Confirmation.md) | 돌파 확인 | ✅ |
| [Condition_Tick_ConsolidationBreakout.md](./Condition_Tick_ConsolidationBreakout.md) | 횡보 돌파 | ✅ |
| [Condition_Tick_Early_Breakout.md](./Condition_Tick_Early_Breakout.md) | 초기 돌파 | ✅ |
| [Condition_MA_Breakout_Scalping.md](./Condition_MA_Breakout_Scalping.md) | 이동평균 돌파 스캘핑 | ✅ |
| [Condition_Study_High_Over.md](./Condition_Study_High_Over.md) | 신고가 돌파 연구 | 📊 |

**특징**: 시가등락율, 전일대비 갭, 고가 돌파 확인

---

### 6️⃣ 반전/스캘핑 전략 (6개)

빠른 반전 포착 및 초단타 스캘핑 전략

| 파일명 | 전략 핵심 | 상태 |
|--------|-----------|------|
| [Condition_RSI_Reversal.md](./Condition_RSI_Reversal.md) | RSI 반전 | ✅ |
| [Condition_Strength_Reversal.md](./Condition_Strength_Reversal.md) | 강도 반전 | ✅ |
| [Condition_Tick_Strength_Reversal.md](./Condition_Tick_Strength_Reversal.md) | 체결강도 반전 | ✅ |
| [Condition_Tick_MomentumReversal.md](./Condition_Tick_MomentumReversal.md) | 모멘텀 반전 | ✅ |
| [Condition_Tick_Quick_Scalping.md](./Condition_Tick_Quick_Scalping.md) | 빠른 스캘핑 | ✅ |
| [Condition_MA_Breakout_Scalping.md](./Condition_MA_Breakout_Scalping.md) | MA 돌파 스캘핑 | ✅ |

**특징**: 빠른 진입/청산, 단기 반전 포착, 초단타 매매

---

### 7️⃣ 특수 지표 전략 (5개)

시가총액, 순매수, 변동성, 가격 액션 등 특수 지표 활용

| 파일명 | 전략 핵심 | 상태 |
|--------|-----------|------|
| [Condition_Tick_MarketCap_Differential.md](./Condition_Tick_MarketCap_Differential.md) | 시가총액 차등 전략 | ✅ |
| [Condition_Tick_Net_Buy_Surge.md](./Condition_Tick_Net_Buy_Surge.md) | 순매수 급증 | ✅ |
| [Condition_Tick_PriceAction.md](./Condition_Tick_PriceAction.md) | 가격 액션 분석 | ✅ |
| [Condition_Tick_Volatility_Expansion.md](./Condition_Tick_Volatility_Expansion.md) | 변동성 확장 | ✅ |
| [Condition_Tick_925_935_Angle_Strategy.md](./Condition_Tick_925_935_Angle_Strategy.md) | 각도 지표 삼각 검증 | ⭐⭐⭐⭐⭐ |

**특징**: 전문 지표 조합, 시가총액 티어별 전략, 각도 분석

---

### 8️⃣ 연구 및 AI 조건식 (17개)

🔬 연구용 조건식 및 AI 생성 전략

| 파일명 | 유형 | 상태 |
|--------|------|------|
| [Condition_Find_1.md](./Condition_Find_1.md) | 연구 | 📊 |
| [Condition_Stomer.md](./Condition_Stomer.md) | 연구 | 📊 |
| [Condition_Study_1.md](./Condition_Study_1.md) | 연구 | 📊 |
| [Condition_Study_2.md](./Condition_Study_2.md) | 연구 | 📊 |
| [Condition_Study_2_T.md](./Condition_Study_2_T.md) | 연구 | 📊 |
| [Condition_Study_3_902.md](./Condition_Study_3_902.md) | 연구 | 📊 |
| [Condition_Study_4_905.md](./Condition_Study_4_905.md) | 연구 | 📊 |
| [Condition_Study_5_9010.md](./Condition_Study_5_9010.md) | 연구 | 📊 |
| [Condition_Study_93000.md](./Condition_Study_93000.md) | 연구 | 📊 |
| [Condition_Study_High_Over.md](./Condition_Study_High_Over.md) | 연구 | 📊 |
| [Condition_Study_By_GPT_o1.md](./Condition_Study_By_GPT_o1.md) | AI (GPT-o1) | 🔍 |
| [Condition_Study_By_Grok3.md](./Condition_Study_By_Grok3.md) | AI (Grok3) | 🔍 |
| [Condition_Test_Template.md](./Condition_Test_Template.md) | 템플릿 | 🧪 |
| [Condition_Tick_902_905_update_2_source.md](./Condition_Tick_902_905_update_2_source.md) | 소스 | 📄 |
| [Condition_Tick_902_905_update_source.md](./Condition_Tick_902_905_update_source.md) | 소스 | 📄 |
| [Condition_Tick_902_update_source.md](./Condition_Tick_902_update_source.md) | 소스 | 📄 |
| [Condition_Study_Open_Breakout.md](./20250808_study/Condition_Study_Open_Breakout.md) | 연구 (2025-08-08) | 📊 |

---

## 문서 작성 가이드

### 새로운 Tick 조건식 문서 작성 시

1. **템플릿 참조**: [Condition_Document_Template_Guideline.md](../../Guideline/Condition_Document_Template_Guideline.md)
2. **가이드라인 숙지**: [Back_Testing_Guideline_Tick.md](../../Guideline/Back_Testing_Guideline_Tick.md)
3. **예제 참고**: [Condition_Tick_902_905_update_2.md](./Condition_Tick_902_905_update_2.md)

### 필수 섹션

- ✅ 문서 헤더 (관련 가이드라인 링크)
- ✅ 개요 (전략 요약, 타겟 시간대, 시장 특성)
- ✅ 공통 계산 지표 (전일종가, 시가등락율, 시가대비등락율, 초당순매수금액)
- ✅ 매수/매도 조건 (시간대별 분기 코드)
- ✅ 최적화 섹션 (변수 설계, 범위, GA 변환, 시간 계산)
- ✅ 백테스팅 결과
- ✅ 조건 개선 연구 (10개 카테고리)

### 코드 패턴 예시

```python
# ================================
#  공통 계산 지표
# ================================
전일종가          = 현재가 / (1 + (등락율 / 100))
시가등락율        = ((시가 - 전일종가) / 전일종가) * 100
시가대비등락율    = ((현재가 - 시가) / 시가) * 100
초당순매수금액    = (초당매수수량 - 초당매도수량) * 현재가 / 1_000_000

# ================================
#  매수 조건
# ================================
매수 = True

# 1. 공통 필터
if not (관심종목 == 1):
    매수 = False
elif not (1000 < 현재가 <= 50000):
    매수 = False

# 2. 시간대별 전략 분기
elif 시분초 < 90200:  # 09:00:00 ~ 09:02:00
    if 시가총액 < 3000:
        if not (2.0 <= 시가등락율 < 4.0):
            매수 = False
        elif not (체결강도 >= 50 and 체결강도 <= 300):
            매수 = False
```

---

## 관련 문서

### 상위 문서
- [📂 docs/Condition/README.md](../README.md) - 조건식 폴더 전체 개요
- [📂 docs/README.md](../../README.md) - 전체 문서 구조

### 가이드라인
- [📘 Back_Testing_Guideline_Tick.md](../../Guideline/Back_Testing_Guideline_Tick.md) - Tick 백테스팅 완전 가이드
- [📙 Condition_Document_Template_Guideline.md](../../Guideline/Condition_Document_Template_Guideline.md) - 조건식 문서 작성 템플릿
- [📕 Stock_Database_Information.md](../../Guideline/Stock_Database_Information.md) - 틱 데이터베이스 구조

### 관련 폴더
- [📂 docs/Condition/Min/](../Min/) - 분봉 조건식 모음
- [📂 docs/Guideline/](../../Guideline/) - 가이드라인 문서

---

## 🎯 추천 학습 경로

### 초급 (Tick 전략 입문)
1. [Back_Testing_Guideline_Tick.md](../../Guideline/Back_Testing_Guideline_Tick.md) 숙지
2. [Condition_Tick_902_905_update_2.md](./Condition_Tick_902_905_update_2.md) 분석
3. [Condition_Test_Template.md](./Condition_Test_Template.md)로 첫 전략 작성

### 중급 (전략 최적화)
1. 여러 시간대 조건식 비교 분석 (902, 905, 910 등)
2. 최적화 변수 설계 및 GA 범위 설정 연습
3. 백테스팅 결과 분석 및 개선

### 고급 (복합 전략)
1. [Condition_Tick_900_920.md](./Condition_Tick_900_920.md) - 다중 시간대 분할 연구
2. [Condition_Tick_900_930_Composite_Study.md](./Condition_Tick_900_930_Composite_Study.md) - 복합 지표 활용
3. 자신만의 조건 개선 연구 수행

---

## 📊 통계

- **전체 문서 수**: 73개
- **카테고리별 분포**:
  - 시간대별 전략: 27개 (장 초반 18개, 오전장 5개, 오후장 4개)
  - 모멘텀 기반: 8개
  - 거래량 기반: 6개
  - 호가창 기반: 7개
  - 갭/돌파: 7개
  - 반전/스캘핑: 6개
  - 특수 지표: 5개
  - 연구/AI: 17개 (연구 13개, AI 2개, 템플릿/소스 4개)
- **문서 품질 분포**:
  - ⭐⭐⭐⭐⭐ (최고 품질): 4개
  - ✅ (검증 완료): 52개
  - 📊 (연구 단계): 13개
  - 🔍 (AI 생성): 2개
  - 🧪/📄 (템플릿/소스): 4개

---

**📝 Note**:
- 프로덕션 조건식은 충분한 백테스팅 검증을 거친 문서입니다.
- 연구 조건식은 아이디어 단계이며, 추가 검증이 필요합니다.
- AI 생성 조건식은 반드시 백테스팅 후 사용하세요.

**💡 Tip**: 새로운 전략 개발 시 [Condition_Tick_902_905_update_2.md](./Condition_Tick_902_905_update_2.md)를 골드 스탠다드로 참조하세요.
