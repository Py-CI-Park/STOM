# Tick 조건식 문서 모음

> 초(秒) 단위 틱 데이터 기반 고빈도 트레이딩 전략 조건식 문서

**📍 위치**: `docs/Condition/Tick/`
**📅 최종 업데이트**: 2025-01-16

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

## 조건식 문서 목록

### 📊 전체 통계

- **전체 조건식**: 73개
- **카테고리**: 8개 (시간대별 + 전략별)
- **핵심 시간대**: 09:00-09:30 (장 초반 급등주 포착)
- **주요 전략**: 모멘텀, 거래량, 호가창, 갭/돌파

---

## 카테고리별 조건식 목록

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
