# Code Review 문서

이 폴더는 STOM 프로젝트의 **코드 리뷰 보고서**를 보관합니다.

## 개요

코드 리뷰는 브랜치 머지 전 코드 품질, 버그 탐지, 아키텍처 일관성을 검증하기 위해 수행됩니다.

## 문서 목록

| 날짜 | 파일명 | 대상 | 상태 |
|------|--------|------|------|
| 2025-12-31 | [2025-12-31_Segment_Final_Reset_Branch_Review.md](./2025-12-31_Segment_Final_Reset_Branch_Review.md) | `research/segment-final-reset` 브랜치 | 버그 발견 |

## 리뷰 프로세스

### 1. 브랜치 분석
- 커밋 히스토리 검토
- 변경 파일 범위 파악
- 이전 브랜치와 비교

### 2. 코드 품질 평가
- 함수 분리 및 모듈화
- 타입 힌팅 및 문서화
- 에러 핸들링
- 테스트 커버리지

### 3. 데이터 정합성 검증
- 컬럼 매핑 확인
- 값 범위 검증
- 스키마 일치 여부

### 4. 결론 및 권장사항
- 버그 우선순위 분류 (P0/P1/P2)
- 수정 방향 제안
- 머지 권장 여부

## 품질 점수 기준

| 점수 | 등급 | 설명 |
|------|------|------|
| 9-10 | 우수 | 즉시 머지 가능 |
| 7-8 | 양호 | 사소한 수정 후 머지 |
| 5-6 | 보통 | 주요 수정 필요 |
| 3-4 | 미흡 | 대폭 수정 필요 |
| 1-2 | 불량 | 재작성 권장 |

## 관련 문서

- [백테스팅 가이드라인 (Tick)](../Guideline/Back_Testing_Guideline_Tick.md)
- [백테스팅 가이드라인 (Min)](../Guideline/Back_Testing_Guideline_Min.md)
- [주식 DB 스키마 정보](../Guideline/Stock_Database_Information.md)
- [세그먼트 필터 통합 가이드](../Guides/Segment_Filter_Condition_Integration_Guide.md)
