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
| [Condition_Tick_902_905_update_2_soruce.md](./Condition_Tick_902_905_update_2_soruce.md) | update_2의 원본 소스 코드 |
| [Condition_Tick_902_905_update_soruce.md](./Condition_Tick_902_905_update_soruce.md) | update_1의 원본 소스 코드 |
| [Condition_Tick_902_update_soruce.md](./Condition_Tick_902_update_soruce.md) | 902 업데이트의 원본 소스 코드 |

---

### 서브폴더: 20250808_study

**📂 위치**: `docs/Condition/Tick/20250808_study/`

특정 날짜 연구 자료 모음

| 파일명 | 연구 내용 |
|--------|-----------|
| [Condition_Study_Open_Breakout.md](./20250808_study/Condition_Study_Open_Breakout.md) | 시가 돌파 전략 연구 (2025-08-08) |

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

- **전체 문서 수**: 31개
- **프로덕션 조건식**: 10개
- **연구 조건식**: 11개
- **AI 생성 조건식**: 2개
- **템플릿/테스트**: 1개
- **소스 파일**: 3개
- **서브폴더**: 1개 (20250808_study)

---

**📝 Note**:
- 프로덕션 조건식은 충분한 백테스팅 검증을 거친 문서입니다.
- 연구 조건식은 아이디어 단계이며, 추가 검증이 필요합니다.
- AI 생성 조건식은 반드시 백테스팅 후 사용하세요.

**💡 Tip**: 새로운 전략 개발 시 [Condition_Tick_902_905_update_2.md](./Condition_Tick_902_905_update_2.md)를 골드 스탠다드로 참조하세요.
