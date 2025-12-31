# STOM Study & Analysis Repository

STOM 프로젝트의 연구, 분석, 검증 문서를 체계적으로 관리하는 저장소입니다.

## 📂 폴더 구조

```
Study/
├── README.md (현재 문서)
├── CodeReview/               # 코드 리뷰 보고서 (1개)
│   ├── README.md
│   └── 2025-12-31_Segment_Final_Reset_Branch_Review.md
├── DocumentationReviews/    # 문서 리뷰 및 검증 (1개)
│   └── 2025-11-17_Documentation_Review_Report.md
├── ResearchReports/          # 연구 보고서 (5개)
│   ├── AI_ML_Trading_Strategy_Automation_Research.md
│   ├── Research_Report_Automated_Condition_Finding.md
│   ├── AI_Driven_Condition_Automation_Circular_Research_System.md
│   ├── 2025-12-20_Segmented_Filter_Optimization_Research.md
│   └── 2025-12-29_Overfitting_Risk_Assessment_Filter_Segment_Analysis.md
├── SystemAnalysis/           # 시스템 분석 및 개선사항 (6개)
│   ├── Optistd_System_Analysis.md
│   ├── STOM_Optimization_System_Improvements.md
│   ├── 2025-12-13_Git_Branch_Structure_Analysis.md
│   ├── 2025-12-28_Backtesting_Output_System_Analysis.md
│   ├── 2025-12-28_New_Metrics_Integration_Verification_Report.md
│   └── Telegram/
│       └── Telegram_Charts_Analysis.md
├── ConditionStudies/         # 트레이딩 조건 심층 분석 (2개)
│   ├── Condition_902_905_Update_2_Deep_Analysis.md
│   └── Condition_Tick_902_905_update_2_Study.md
└── Guides/                   # 가이드 및 참고자료 (3개)
    ├── Condition_Optimization_and_Analysis_Guide.md
    ├── New_Metrics_Development_Process_Guide.md
    └── Segment_Filter_Condition_Integration_Guide.md
```

**총 문서 수**: 19개 | **총 용량**: ~730KB

---

## 🎯 종합 스터디 요약 (Quick Overview)

전체 연구/분석 문서의 핵심 내용을 한눈에 파악할 수 있는 종합 테이블입니다.

| # | 문서명 | 카테고리 | 작성일 | 크기 | 핵심 주제 | 주요 성과/결론 | 관련 기술 | 상태 |
|:-:|:-------|:---------|:-------|:----:|:----------|:--------------|:----------|:----:|
| 1 | **Documentation Review Report** | 문서 리뷰 | 2025-11-17 | 27KB | 106개 문서 품질 검증 | • 문서화 품질 4.5/5<br>• 300개 이상 코드 스니펫<br>• 5개 깨진 링크 발견 | Markdown, Documentation | ✅ |
| 2 | **AI/ML Trading Strategy Automation** | 연구 보고서 | 2025-11-27 | 74KB | AI/ML 기반 전략 자동화 | • 조건 선택 자동화 (826개 변수)<br>• 최적화 시간: 587년 → 수시간<br>• 과적합 방지 메커니즘 | XGBoost, Optuna, RL, LLM | ✅ |
| 3 | **Automated Condition Finding** | 연구 보고서 | 2025-11-27 | 7KB | 조건식 자동 발굴 시스템 | • Feature Importance (SHAP)<br>• Genetic Programming<br>• LLM 기반 코드 생성 | DEAP, GPT-4, FinRL | ✅ |
| 4 | **Optistd System Analysis** | 시스템 분석 | 2025-11-29 | 20KB | OPTISTD 14가지 분석 | • 교차검증 MERGE 계산식<br>• TRAIN/VALID/TEST 차이<br>• 극단값 증폭 문제 식별 | NumPy, Statistics | ✅ |
| 5 | **Optimization System Improvements** | 시스템 분석 | 2025-11-29 | 19KB | 최적화 시스템 개선안 | • 15가지 개선 방안<br>• 조화평균 MERGE 제안<br>• Grid/Optuna/GA 비교 | Optuna, CMA-ES, QMCS | ✅ |
| 6 | **Git Branch Structure Analysis** | 시스템 분석 | 2025-12-13 | 38KB | Git 브랜치 구조 분석 및 정리 | • 7→3 커밋 스쿼싱<br>• 브랜치 6개 정리<br>• STOM_V1 브랜치 생성<br>• 히스토리 무결성 검증 | Git, Version Control | ✅ |
| 7 | **Condition 902/905 Deep Analysis** | 조건 분석 | 2025-11-29 | 44KB | 장 시작 5분 전략 심층 분석 | • 17개 조건 과적합 위험<br>• 체결강도 50-300 범위<br>• 조건 충돌 문제 식별 | Technical Analysis | ✅ |
| 8 | **Condition 902/905 Study** | 조건 분석 | 2025-11-29 | 10KB | 틱 조건 스터디 노트 | • 2단계 최적화 (Coarse→Fine)<br>• 조건 무력화 방법<br>• 조건 조합 아이디어 | Backtesting | ✅ |
| 9 | **Optimization & Analysis Guide** | 가이드 | 2025-11-29 | 13KB | 전체 변수 사전 및 가이드 | • 826개 틱 변수 정리<br>• 7가지 카테고리 분류<br>• 무력화 설정값 제공 | Documentation | ✅ |
| 10 | **AI Condition Automation Circular System** | 연구 보고서 | 2025-12-01 | 80KB | AI 기반 조건식 자동화 순환 연구 | • 133개 조건 분석 (826/752 변수)<br>• 4단계 순환 프로세스 설계<br>• LLM/GP/Feature Importance 통합 | LLM, DEAP, XGBoost, SHAP, SQLite | ✅ |
| 11 | **Telegram Charts Analysis** | 시스템 분석 | 2025-12-14 | 40KB | 텔레그램 차트/CSV 기반 백테스팅 강화 분석 | • 기본/강화 CSV 산출물(최대 8종) 정의<br>• 필터 효과(통계)·시너지·안정성·임계값 분석 정리<br>• 텔레그램 전송 플로우 문서화 | pandas, SciPy, scikit-learn, Telegram | ✅ |
| 12 | **Segmented Filter Optimization Research** | 연구 보고서 | 2025-12-20 | 45KB | 시가총액/시간 구간 분할 기반 필터 조합 최적화 연구 (v2.0) | • 12개 세그먼트(3시총×4시간) 분할 설계<br>• 2단계 계층적 최적화(Greedy+Beam Search) 알고리즘<br>• NSGA-II 다목적 최적화/Optuna 임계값 탐색<br>• Walk-Forward 검증 및 과적합 방지 전략<br>• 코드 자동 생성 아키텍처 설계 | Optimization, Segmentation, NSGA-II, Optuna, Walk-Forward | ✅ |
| 13 | **Risk Score Calculation Analysis** | 시스템 분석 | 2025-12-28 | 5KB | 위험도 점수 산출 및 타임프레임 호환성 분석 | • 분봉/틱 데이터 간 위험도 점수 일관성 검증<br>• 상태값(Snapshot) 및 누적값(Daily) 기반 중립성 분석<br>• 분석 엔진(metrics_base.py/metrics_enhanced.py)과 조건식 문서 간 로직 동기화 | Statistics, Python, Documentation | ✅ |
| 14 | **Backtesting Output System Analysis** | 시스템 분석 | 2025-12-28 | 95KB | 백테스팅 출력 시스템 상세 분석 | • 93개 컬럼 파생 지표 계산 로직 분석<br>• 1분봉/1초봉 변수 차이 및 처리 검증<br>• 비율 조합 지표 구현 현황 확인<br>• 당일거래대금 비율 지표 추가 구현 권장 | Python, NumPy, Pandas, Analysis | ✅ |
| 15 | **New Metrics Integration Verification Report** | 시스템 분석 | 2025-12-28 | 48KB | 당일거래대금 비율 지표 통합 검증 | • 신규 지표 3종 백테스팅 시스템 통합<br>• detail.csv/report.txt 자동 문서화<br>• 필터/세그먼트/ML feature 호환성 검증<br>• 4개 파일 수정으로 완전 통합 완료 | Python, Integration Testing | ✅ |
| 16 | **New Metrics Development Process Guide** | 가이드 | 2025-12-28 | 52KB | 신규 지표 개발 및 통합 체계적 프로세스 | • 10단계 개발 프로세스 정립<br>• LOOKAHEAD-FREE 검증 가이드<br>• 6개 시스템 통합 체크리스트<br>• 코드 템플릿 및 실전 사례 포함 | Documentation, Process | ✅ |
| 17 | **Overfitting Risk Assessment Filter/Segment Analysis** | 연구 보고서 | 2025-12-29 | 120KB | 백테스팅 필터/세그먼트 분석 오버피팅 위험 평가 | • 5가지 오버피팅 발생 메커니즘 분석<br>• 6가지 판단 지표 체계 제안<br>• Walk-Forward/Purged K-Fold 검증 방법<br>• 긴급/단기/중기 개선 로드맵<br>• 종합 오버피팅 점수 시스템 | Statistics, Cross-Validation, Overfitting Prevention | ✅ |
| 18 | **Segment Filter Condition Integration Guide** | 가이드 | 2025-12-30 | 8KB | 세그먼트 필터 통합 프로세스 | • 최종 조건식 파일 생성 절차<br>• 텔레그램 안내 흐름 정리<br>• 전역 조합/코드/구간 기준 정리 | Markdown, Process | ✅ |
| 19 | **Segment Final Reset Branch Review** | 코드 리뷰 | 2025-12-31 | 9KB | segment-final-reset 브랜치 코드 리뷰 | • 5개 커밋 분석 및 평가<br>• 매수초당거래대금 매핑 버그 발견<br>• 품질 점수 7.3/10<br>• 머지 전 P0 버그 수정 필요 | Git, Code Review, Data Mapping | ⚠️ |

### 📊 스터디 주제별 분류

#### 🤖 AI/ML 연구 (4개)
- **자동화**: AI/ML 기반 전략 자동화, 조건식 자동 발굴, 순환 연구 시스템
- **최적화**: 세그먼트 분할 기반 필터 조합 최적화 (신규)
- **핵심 기술**: XGBoost, SHAP, Genetic Programming, LLM, Reinforcement Learning, DEAP, NSGA-II, Optuna
- **목표**: 826개 변수 중 최적 조합 자동 발견, 최적화 시간 단축 (587년→수시간), 완전 자동화된 순환 개선 프로세스, 세그먼트별 필터 최적화

#### ⚙️ 시스템 최적화 및 관리 (7개)
- **분석 대상**: OPTISTD 14가지 계산식, 교차검증 MERGE, Grid/Optuna/GA, Git 브랜치 구조, 텔레그램 분석 시스템, 위험도 점수 산출 로직, 백테스팅 출력 시스템
- **문제 식별**: 극단값 증폭, TRAIN×VALID 곱셈 문제 (수정 완료), 분봉/틱 간 변수 호환성 이슈 해결, 당일거래대금 비율 지표 미구현 (해결 완료)
- **개선안**: 조화평균 사용, 15가지 구체적 개선 방안, 위험도 점수 로직 표준화 및 동기화, 당일거래대금 비율 지표 3종 추가 및 완전 통합

#### 📈 조건 전략 연구 (2개)
- **대상 조건**: Condition_Tick_902_905_update_2 (장 시작 5분)
- **문제점**: 17개 조건 과적합, 표본 부족, 조건 충돌
- **해결책**: 2단계 최적화, 조건 완화, 조합 전략

#### 📚 문서화 & 가이드 (3개)
- **문서 품질**: 106개 문서, 품질 4.5/5, 300개 이상 코드 스니펫
- **변수 사전**: 826개 틱 변수, 752개 분봉 변수, 7가지 카테고리
- **실무 가이드**: 무력화 설정, 최적화 방법론, 베스트 프랙티스
- **개발 가이드**: 신규 지표 개발 프로세스 (10단계, 체크리스트 포함)

---

## 📋 문서 인덱스

### 1. Documentation Reviews (문서 리뷰)

프로젝트 문서의 품질 검증 및 개선사항을 다룹니다.

| 문서명 | 작성일 | 상태 | 설명 |
|--------|--------|------|------|
| [2025-11-17_Documentation_Review_Report.md](./DocumentationReviews/2025-11-17_Documentation_Review_Report.md) | 2025-11-17 | ✅ 완료 | 문서 검증 및 개선사항 리포트 |

**주요 내용:**
- 문서 일관성 검증
- 코드-문서 정합성 확인
- 개선 권장사항

---

### 2. Research Reports (연구 보고서)

새로운 기술, 전략, 방법론에 대한 연구 결과를 담고 있습니다.

| 문서명 | 작성일 | 상태 | 설명 |
|--------|--------|------|------|
| [AI_ML_Trading_Strategy_Automation_Research.md](./ResearchReports/AI_ML_Trading_Strategy_Automation_Research.md) | 2025-11-27 | ✅ 완료 | AI/ML 기반 트레이딩 전략 자동화 연구 (73KB) |
| [Research_Report_Automated_Condition_Finding.md](./ResearchReports/Research_Report_Automated_Condition_Finding.md) | 2025-11-27 | ✅ 완료 | 조건식 자동 탐색 시스템 연구 |
| [AI_Driven_Condition_Automation_Circular_Research_System.md](./ResearchReports/AI_Driven_Condition_Automation_Circular_Research_System.md) | 2025-12-01 | ✅ 완료 | AI 기반 조건식 자동화 순환 연구 시스템 (80KB) |
| [2025-12-20_Segmented_Filter_Optimization_Research.md](./ResearchReports/2025-12-20_Segmented_Filter_Optimization_Research.md) | 2025-12-20 | ✅ 완료 | 시가총액/시간 구간 분할 기반 필터 조합 최적화 연구 (45KB) |
| [2025-12-29_Overfitting_Risk_Assessment_Filter_Segment_Analysis.md](./ResearchReports/2025-12-29_Overfitting_Risk_Assessment_Filter_Segment_Analysis.md) | 2025-12-29 | ✅ 완료 | 백테스팅 필터/세그먼트 분석 오버피팅 위험 평가 연구 (120KB) |

**주요 내용:**
- AI/ML 트레이딩 전략 적용 방안
- 자동화된 조건식 탐색 메커니즘
- 머신러닝 기반 전략 생성 프로세스
- 4단계 순환 개선 시스템 (생성→테스트→기록→개선)
- LLM/GP/Feature Importance 통합 아키텍처
- 세그먼트 분할 기반 필터 조합 최적화
- 오버피팅 위험 평가 및 예방 방법
- 교차 검증 및 통계적 검증 방법론
- 실전 적용 가능성 검토

---

### 3. System Analysis (시스템 분석)

STOM 시스템의 성능, 구조, 최적화, 버전 관리에 대한 심층 분석입니다.

| 문서명 | 작성일 | 상태 | 설명 |
|--------|--------|------|------|
| [Optistd_System_Analysis.md](./SystemAnalysis/Optistd_System_Analysis.md) | 2025-11-29 | ✅ 완료 | Optistd 최적화 시스템 분석 |
| [STOM_Optimization_System_Improvements.md](./SystemAnalysis/STOM_Optimization_System_Improvements.md) | 2025-11-29 | ✅ 완료 | STOM 최적화 시스템 개선방안 |
| [2025-12-13_Git_Branch_Structure_Analysis.md](./SystemAnalysis/2025-12-13_Git_Branch_Structure_Analysis.md) | 2025-12-13 | ✅ 완료 | Git 브랜치 구조 분석 및 정리 보고서 (38KB) |
| [Telegram_Charts_Analysis.md](./SystemAnalysis/Telegram/Telegram_Charts_Analysis.md) | 2025-12-14 | ✅ 완료 | 텔레그램 추가 차트/CSV 기반 강화 분석 시스템 문서 (v2.0) |
| [2025-12-28_Backtesting_Output_System_Analysis.md](./SystemAnalysis/2025-12-28_Backtesting_Output_System_Analysis.md) | 2025-12-28 | ✅ 완료 | 백테스팅 출력 시스템 상세 분석 (95KB) |

**주요 내용:**
- 최적화 시스템 아키텍처 분석
- 성능 병목지점 식별
- 개선 방안 및 로드맵
- 시스템 효율성 향상 전략
- Git 브랜치 구조 분석 및 커밋 히스토리 정리

---

### 4. Condition Studies (조건 심층 분석)

특정 트레이딩 조건에 대한 상세 연구 및 분석입니다.

| 문서명 | 작성일 | 상태 | 설명 |
|--------|--------|------|------|
| [Condition_902_905_Update_2_Deep_Analysis.md](./ConditionStudies/Condition_902_905_Update_2_Deep_Analysis.md) | 2025-11-29 | ✅ 완료 | 조건 902, 905 업데이트2 심층 분석 (43KB) |
| [Condition_Tick_902_905_update_2_Study.md](./ConditionStudies/Condition_Tick_902_905_update_2_Study.md) | 2025-11-29 | ✅ 완료 | 틱 조건 902, 905 업데이트2 연구 |

**주요 내용:**
- 조건 902, 905의 상세 분석
- Update 2 버전의 개선사항
- 성능 비교 및 백테스팅 결과
- 실전 적용 시나리오

---

### 5. Guides (가이드)

조건 최적화 및 분석을 위한 실무 가이드입니다.

| 문서명 | 작성일 | 상태 | 설명 |
|--------|--------|------|------|
| [Condition_Optimization_and_Analysis_Guide.md](./Guides/Condition_Optimization_and_Analysis_Guide.md) | 2025-11-29 | ✅ 완료 | 조건 최적화 및 분석 가이드 |
| [New_Metrics_Development_Process_Guide.md](./Guides/New_Metrics_Development_Process_Guide.md) | 2025-12-28 | ✅ 완료 | 신규 지표 개발 및 통합 프로세스 가이드 |
| [Segment_Filter_Condition_Integration_Guide.md](./Guides/Segment_Filter_Condition_Integration_Guide.md) | 2025-12-30 | ✅ 완료 | 세그먼트 필터 통합 프로세스 가이드 |

**주요 내용:**
- 조건 최적화 프로세스
- 분석 방법론
- 베스트 프랙티스
- 문제 해결 가이드

---

### 6. Code Reviews (코드 리뷰)

브랜치 머지 전 코드 품질, 버그 탐지, 아키텍처 일관성 검증을 위한 코드 리뷰 보고서입니다.

| 문서명 | 작성일 | 상태 | 설명 |
|--------|--------|------|------|
| [2025-12-31_Segment_Final_Reset_Branch_Review.md](./CodeReview/2025-12-31_Segment_Final_Reset_Branch_Review.md) | 2025-12-31 | ⚠️ 버그 발견 | segment-final-reset 브랜치 코드 리뷰 (9KB) |

**주요 내용:**
- 커밋 히스토리 분석 및 변경 범위 파악
- 코드 품질 평가 (함수 분리, 타입 힌팅, 에러 핸들링)
- 데이터 정합성 검증 (컬럼 매핑, 값 범위)
- 버그 우선순위 분류 (P0/P1/P2) 및 수정 방향 제안

---

## 📊 문서 현황

| 카테고리 | 문서 수 | 완료 | 진행 중 | 계획 |
|----------|---------|------|---------|------|
| Documentation Reviews | 1 | 1 | 0 | 0 |
| Research Reports | 5 | 5 | 0 | 0 |
| System Analysis | 6 | 6 | 0 | 0 |
| Condition Studies | 2 | 2 | 0 | 0 |
| Guides | 3 | 3 | 0 | 0 |
| Code Reviews | 1 | 0 | 1 | 0 |
| **전체** | **19** | **17** | **1** | **0** |

## 🎯 문서 상태 범례

- ✅ **완료**: 문서 작성 및 검토 완료
- 🔄 **진행 중**: 현재 작성 또는 업데이트 중
- 📋 **계획**: 작성 예정
- ⚠️ **검토 필요**: 업데이트 또는 재검토 필요
- 🗄️ **보관**: 참고용 보관 문서

## 📝 문서 작성 가이드라인

### 1. 파일명 규칙
- **날짜 포함**: `YYYY-MM-DD_Title.md` (예: 2025-11-17_Documentation_Review_Report.md)
- **설명적 제목**: 내용을 명확히 나타내는 제목 사용
- **카테고리 접두사**: 필요시 카테고리 표시 (예: Condition_, Research_Report_)

### 2. 문서 구조
```markdown
# 문서 제목

## 개요
- 작성일:
- 작성자:
- 목적:
- 관련 이슈/PR:

## 주요 내용
...

## 분석 결과
...

## 결론 및 권장사항
...

## 참고자료
...
```

### 3. 문서 추가 프로세스
1. 적절한 카테고리 폴더에 문서 추가
2. README.md의 해당 섹션 테이블 업데이트
3. 문서 현황 통계 업데이트
4. Git 커밋 시 의미있는 커밋 메시지 작성

### 4. 정기 검토
- **월간 검토**: 모든 문서의 관련성 및 정확성 확인
- **분기별 정리**: 오래된 문서 아카이빙 또는 업데이트
- **연간 감사**: 전체 문서 구조 재평가

## 💡 핵심 인사이트 및 발견사항

### 🔍 주요 발견사항

1. **최적화 시스템 문제**
   - 교차검증 MERGE 계산에서 TRAIN×VALID 곱셈이 극단값을 증폭
   - 조화평균 사용으로 균형잡힌 평가 가능
   - 15가지 구체적 개선 방안 도출

2. **AI/ML 적용 가능성**
   - 826개 변수 중 유효 조합 자동 발견 가능
   - 최적화 시간: 587년 → 수 시간으로 단축
   - XGBoost, SHAP, Genetic Programming, LLM 활용

3. **조건 전략 이슈**
   - Condition 902/905: 17개 조건으로 인한 과적합 위험
   - 표본 부족, 조건 충돌, 각도 필터 과잉 문제
   - 2단계 최적화 (Coarse→Fine) 접근 필요

4. **문서화 수준**
   - 106개 문서, 품질 4.5/5의 우수한 수준
   - 300개 이상의 실행 가능한 코드 스니펫
   - 826개 틱 변수 + 752개 분봉 변수 완전 문서화

5. **오버피팅 위험 평가** (2025-12-29 추가)
   - 현재 시스템의 오버피팅 위험도: **높음** 🔴
   - 주요 원인: Train/Test 미분리, 다중 비교 보정 없음, Walk-Forward 미구현
   - 6가지 판단 지표 체계 제안 (통계적 유의성, 샘플 크기, 제외율, WFA 저하율, 민감도, 일관성)
   - 종합 오버피팅 점수 시스템 설계 (80점 이상 → 신뢰 가능)
   - 긴급/단기/중기 개선 로드맵 제시
   - 백테스트 → 실전 성능 저하율 예상: 40-70%

### 🎯 향후 연구 방향

#### 단기 (1-3개월)
- [ ] 조화평균 기반 MERGE 계산 구현 및 테스트
- [ ] Condition 902/905 조건 완화 실험
- [ ] XGBoost 기반 Feature Importance 분석 시스템 구축
- [ ] **Train/Val/Test 데이터 분할 시스템 구현** (긴급) 🔴
- [ ] **Bonferroni/FDR 다중 비교 보정 적용** (긴급) 🔴
- [ ] **Walk-Forward Analysis 구현** (높음) 🟠

#### 중기 (3-6개월)
- [ ] Genetic Programming 조건식 자동 생성 시스템
- [ ] Optuna 기반 하이퍼파라미터 최적화 고도화
- [ ] LLM 활용 조건식 코드 생성 파이프라인

#### 장기 (6-12개월)
- [ ] Reinforcement Learning 기반 동적 전략 학습
- [ ] 실시간 시장 변화 감지 및 자동 재조정 시스템
- [ ] 완전 자동화된 전략 발굴 및 검증 플랫폼

### 📈 적용 우선순위

| 순위 | 개선사항 | 예상 효과 | 난이도 | 우선도 |
|:----:|:---------|:----------|:------:|:------:|
| 1 | 조화평균 MERGE 구현 | ⭐⭐⭐⭐⭐ | 낮음 | 🔴 긴급 |
| 2 | Feature Importance 분석 | ⭐⭐⭐⭐ | 중간 | 🟠 높음 |
| 3 | 조건 무력화 실험 도구 | ⭐⭐⭐⭐ | 낮음 | 🟠 높음 |
| 4 | Optuna 최적화 고도화 | ⭐⭐⭐⭐ | 중간 | 🟡 중간 |
| 5 | Genetic Programming | ⭐⭐⭐⭐⭐ | 높음 | 🟡 중간 |
| 6 | LLM 코드 생성 | ⭐⭐⭐⭐⭐ | 높음 | 🟢 낮음 |
| 7 | RL 기반 전략 학습 | ⭐⭐⭐⭐⭐ | 매우높음 | 🟢 낮음 |

## 🔗 관련 링크

- [프로젝트 메인 문서](../Manual/)
- [개발 가이드라인](../Guideline/)
- [트레이딩 조건 문서](../Condition/)
- [백테스팅 가이드](../Guideline/Back_Testing_Guideline_Tick.md)
- [API 문서](../Manual/04_API/)

## 📞 문의 및 기여

### 문의사항
문서 관련 문의사항이나 개선 제안이 있으시면 이슈를 등록해주세요.

### 기여 방법
1. 새로운 연구/분석 문서 작성
2. 기존 문서 업데이트 및 개선
3. 코드 구현 및 실험 결과 공유
4. 리뷰 및 피드백 제공

---

**최종 업데이트**: 2025-12-31
**문서 관리자**: STOM Development Team
**문서 버전**: 2.5