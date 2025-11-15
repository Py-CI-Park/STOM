# Min 조건식 문서 모음

> 1분봉 캔들 데이터 기반 스윙/단타 트레이딩 전략 조건식 문서

**📍 위치**: `docs/Condition/Min/`
**📅 최종 업데이트**: 2025-01-15

---

## 📋 목차

- [개요](#개요)
- [조건식 문서 목록](#조건식-문서-목록)
  - [프로덕션 조건식](#프로덕션-조건식-production)
  - [연구 및 스터디 조건식](#연구-및-스터디-조건식)
  - [아이디어 조건식](#아이디어-조건식-idea)
- [문서 작성 가이드](#문서-작성-가이드)
- [관련 문서](#관련-문서)

---

## 개요

이 폴더는 **1분봉 캔들 데이터**를 활용한 스윙/단타 트레이딩 전략의 조건식 문서를 모아둔 곳입니다.

### Min 전략의 특징

- **시간 단위**: 1분 단위 캔들 데이터
- **타겟 시간**: 장 시작부터 장 마감까지 (09:00~15:30)
- **데이터베이스**: `stock_min_back.db`
- **변수**: 분봉시가/고가/저가, 분당거래대금, TA-Lib 지표 등 108개 컬럼
- **전략 유형**:
  - 급등주 포착 (장 초반)
  - 기술적 지표 기반 매매 (MACD, RSI, BBand 등)
  - 시간대별 특화 전략

### Tick 전략과의 차이점

| 구분 | Tick 전략 | Min 전략 |
|------|-----------|----------|
| 시간 단위 | 초(1초) | 분(1분) |
| 데이터 갱신 | 실시간 틱 | 1분마다 |
| 봉 정보 | 일봉만 | 일봉 + 분봉 |
| 보조지표 | 제한적 | 풍부한 TA-Lib 지표 |
| 시간 표기 | hhmmss | hhmmss |
| 주요 용도 | 초단타, 급등주 즉시 포착 | 단타, 스윙, 기술적 분석 |

---

## 조건식 문서 목록

### 프로덕션 조건식 (Production)

✅ 검증 완료 및 실전 배포 가능한 조건식

| 파일명 | 시간대 | 전략 개요 | 상태 |
|--------|--------|-----------|------|
| [Condition_Find_1_Min.md](./Condition_Find_1_Min.md) | 전체 | 분봉 기반 조건 탐색 1차 | ✅ 프로덕션 |
| [Condition_Stomer_Min.md](./Condition_Stomer_Min.md) | 전체 | Stomer 분봉 전략 | ✅ 프로덕션 |

---

### 연구 및 스터디 조건식

🔬 백테스팅 및 분석 단계의 연구용 조건식

| 파일명 | 주요 연구 내용 | 상태 |
|--------|---------------|------|
| [Condition_Study_1_Min.md](./Condition_Study_1_Min.md) | 기본 분봉 전략 연구 | 📊 연구 |
| [Condition_Study_2_Min.md](./Condition_Study_2_Min.md) | 2차 개선 연구 | 📊 연구 |
| [Condition_Study_3_902_min.md](./Condition_Study_3_902_min.md) | 09:02 분봉 집중 연구 | 📊 연구 |
| [Condition_Study_3_9010_min.md](./Condition_Study_3_9010_min.md) | 09:10 분봉 집중 연구 | 📊 연구 |
| [Condition_Min_Study_soruce.md](./Condition_Min_Study_soruce.md) | 분봉 연구 원본 소스 | 📄 소스 |

---

### 아이디어 조건식 (Idea)

💡 전략 아이디어 및 개념 검증 단계 문서

**📂 위치**: `docs/Condition/Min/Idea/`

#### 기술적 지표 기반 전략

| 파일명 | 주요 지표 | 전략 개요 | 상태 |
|--------|-----------|-----------|------|
| [Condition_MACD_Precision_System.md](./Idea/Condition_MACD_Precision_System.md) | MACD | MACD 정밀 시스템 전략 | 💡 아이디어 |
| [Condition_RSI_Multilayer_Filter.md](./Idea/Condition_RSI_Multilayer_Filter.md) | RSI | RSI 다층 필터 시스템 | 💡 아이디어 |
| [Condition_Bollinger_Strategic.md](./Idea/Condition_Bollinger_Strategic.md) | BBand | 볼린저 밴드 전략적 활용 | 💡 아이디어 |
| [Condition_Triple_Confirmation.md](./Idea/Condition_Triple_Confirmation.md) | 복합지표 | 3중 확인 시스템 (MACD+RSI+BBand) | 💡 아이디어 |

#### 시장 상황별 전략

| 파일명 | 시장 상황 | 전략 개요 | 상태 |
|--------|-----------|-----------|------|
| [Condition_Basic_Surge_Detection.md](./Idea/Condition_Basic_Surge_Detection.md) | 급등 | 기본 급등 감지 전략 | 💡 아이디어 |
| [Opening_Surge_Strategy_20250713_temp.md](./Idea/Opening_Surge_Strategy_20250713_temp.md) | 장 초반 | 장 시작 급등 전략 (2025-07-13) | 🚧 임시 |
| [gap_up_momentum_20250713_temp.md](./Idea/gap_up_momentum_20250713_temp.md) | 갭상승 | 갭 상승 모멘텀 전략 (2025-07-13) | 🚧 임시 |
| [Condition_Reversal_Point.md](./Idea/Condition_Reversal_Point.md) | 반등 | 반전 지점 포착 전략 | 💡 아이디어 |
| [Condition_Time_Specific.md](./Idea/Condition_Time_Specific.md) | 시간대별 | 특정 시간대 특화 전략 | 💡 아이디어 |

#### 고급 전략 및 시스템

| 파일명 | 전략 유형 | 전략 개요 | 상태 |
|--------|-----------|-----------|------|
| [Condition_Comprehensive_Strategy_20250713_temp.md](./Idea/Condition_Comprehensive_Strategy_20250713_temp.md) | 종합 전략 | 포괄적 통합 전략 (2025-07-13) | 🚧 임시 |
| [Condition_Advanced_Algorithm.md](./Idea/Condition_Advanced_Algorithm.md) | 고급 알고리즘 | 고급 알고리즘 기반 전략 | 💡 아이디어 |
| [Condition_Risk_Management.md](./Idea/Condition_Risk_Management.md) | 리스크 관리 | 리스크 관리 중심 전략 | 💡 아이디어 |
| [Condition_Portfolio_Management.md](./Idea/Condition_Portfolio_Management.md) | 포트폴리오 | 포트폴리오 관리 전략 | 🚧 작성 중 |

#### 일반 아이디어

| 파일명 | 내용 | 상태 |
|--------|------|------|
| [아이디어.md](./Idea/아이디어.md) | 분봉 전략 아이디어 모음 (v1) | 💡 아이디어 |
| [아이디어_v2.md](./Idea/아이디어_v2.md) | 분봉 전략 아이디어 모음 (v2) | 💡 아이디어 |

---

## 문서 작성 가이드

### 새로운 Min 조건식 문서 작성 시

1. **템플릿 참조**: [Condition_Document_Template_Guideline.md](../../Guideline/Condition_Document_Template_Guideline.md)
2. **가이드라인 숙지**: [Back_Testing_Guideline_Min.md](../../Guideline/Back_Testing_Guideline_Min.md)
3. **예제 참고**: Tick 예제를 Min 변수로 변환하여 적용

### Min 전략 특화 가이드

#### 1. 분봉 데이터 활용

```python
# 분봉 캔들 정보 활용
if 분봉시가 < 분봉저가:  # 하락 분봉
    if 현재가 > 분봉고가:  # 고가 돌파
        매수 = True

# 분당 거래량 증가 확인
if 분당거래대금 > 분당거래대금N(1) * 1.5:
    매수 = True
```

#### 2. TA-Lib 지표 활용

```python
# MACD 골든크로스
if MACD < MACD시그널N(1) and MACD >= MACD시그널:
    매수 = True

# RSI 과매도 구간 반등
if RSIN(1) < 30 and RSI >= 30:
    매수 = True

# 볼린저 밴드 하단 터치 후 반등
if 현재가N(1) <= BBandLower and 현재가 > BBandLower:
    매수 = True
```

#### 3. 시간대별 전략 분기

```python
# 시간대별 다른 조건 적용
if 시분초 < 93000:  # 09:30 이전 (장 초반)
    # 급등주 포착 전략
    if 등락율 > 3.0 and 체결강도 > 100:
        매수 = True
elif 시분초 < 110000:  # 11:00 이전 (오전장)
    # 기술적 지표 기반 전략
    if MACD > MACD시그널 and RSI < 70:
        매수 = True
else:  # 11:00 이후 (오후장)
    # 안정적 추세 추종 전략
    if 이동평균5 > 이동평균20 and 현재가 > 이동평균5:
        매수 = True
```

### 필수 섹션

- ✅ 문서 헤더 (관련 가이드라인 링크)
- ✅ 개요 (전략 요약, 타겟 시간대, 주요 지표)
- ✅ 매수/매도 조건 (분봉 데이터 및 TA-Lib 지표 활용)
- ✅ 최적화 섹션 (변수 설계, 범위, GA 변환)
- ✅ 백테스팅 결과
- ✅ 조건 개선 연구

---

## 관련 문서

### 상위 문서
- [📂 docs/Condition/README.md](../README.md) - 조건식 폴더 전체 개요
- [📂 docs/README.md](../../README.md) - 전체 문서 구조

### 가이드라인
- [📗 Back_Testing_Guideline_Min.md](../../Guideline/Back_Testing_Guideline_Min.md) - 분봉 백테스팅 완전 가이드
- [📙 Condition_Document_Template_Guideline.md](../../Guideline/Condition_Document_Template_Guideline.md) - 조건식 문서 작성 템플릿
- [📕 Stock_Database_Information.md](../../Guideline/Stock_Database_Information.md) - 분봉 데이터베이스 구조

### 관련 폴더
- [📂 docs/Condition/Tick/](../Tick/) - 틱 조건식 모음
- [📂 docs/Guideline/](../../Guideline/) - 가이드라인 문서

---

## 🎯 추천 학습 경로

### 초급 (Min 전략 입문)
1. [Back_Testing_Guideline_Min.md](../../Guideline/Back_Testing_Guideline_Min.md) 숙지
2. [Condition_Study_1_Min.md](./Condition_Study_1_Min.md) 분석
3. 간단한 이동평균 기반 전략 작성

### 중급 (기술적 지표 활용)
1. [Condition_MACD_Precision_System.md](./Idea/Condition_MACD_Precision_System.md) - MACD 전략 연구
2. [Condition_RSI_Multilayer_Filter.md](./Idea/Condition_RSI_Multilayer_Filter.md) - RSI 전략 연구
3. [Condition_Bollinger_Strategic.md](./Idea/Condition_Bollinger_Strategic.md) - BBand 전략 연구
4. 단일 지표 기반 전략 백테스팅

### 고급 (복합 전략)
1. [Condition_Triple_Confirmation.md](./Idea/Condition_Triple_Confirmation.md) - 복합 지표 전략
2. [Condition_Comprehensive_Strategy_20250713_temp.md](./Idea/Condition_Comprehensive_Strategy_20250713_temp.md) - 종합 전략
3. 시간대별 + 지표별 조합 전략 개발

---

## 📊 통계

- **전체 문서 수**: 20개
- **프로덕션 조건식**: 2개
- **연구 조건식**: 5개
- **아이디어 조건식**: 15개
  - 기술적 지표 기반: 4개
  - 시장 상황별: 5개
  - 고급 전략: 4개
  - 일반 아이디어: 2개

---

## 💡 주요 특징

### Min 전략의 강점

1. **풍부한 보조지표**: MACD, RSI, BBand, 이동평균 등 다양한 TA-Lib 지표 활용 가능
2. **캔들 패턴 분석**: 분봉시가/고가/저가/종가를 활용한 캔들 패턴 분석
3. **안정적인 신호**: 1분 단위 데이터로 틱 데이터 대비 노이즈 감소
4. **유연한 시간 프레임**: 전체 거래 시간 활용 가능 (09:00~15:30)

### Tick 대비 장점

- 기술적 지표 활용으로 더 정교한 분석 가능
- 캔들 패턴 인식으로 추세 파악 용이
- 틱 데이터 대비 데이터 용량 작아 백테스팅 속도 빠름
- 스윙 트레이딩에 적합

---

**📝 Note**:
- 프로덕션 조건식은 충분한 백테스팅 검증을 거친 문서입니다.
- 아이디어 조건식은 개념 단계이며, 백테스팅 검증이 필요합니다.
- 임시(temp) 파일은 작업 중인 문서로, 완성 후 정식 파일명으로 변경됩니다.

**💡 Tip**:
- TA-Lib 지표 조합 시 과최적화에 주의하세요.
- 분봉 데이터는 틱 데이터보다 지연이 있으므로, 초단타보다는 단타/스윙에 적합합니다.
- 여러 시간 프레임을 조합하여 신뢰도를 높일 수 있습니다.
