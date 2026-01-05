# 세그먼트 필터 일관성 수정 V2 - 마스터 플랜

**작성일**: 2026-01-05
**브랜치**: `fix/segment-filter-consistency-v2`
**기반 커밋**: `f44c348e9074f5c4295f2e7cf8ad513b6229d475`

---

## 1. 프로젝트 개요

### 1.1 최종 목적

**세그먼트 필터 분석에서 생성된 조건식을 사용한 백테스팅 결과가 분석 예측값과 동일해야 함**

```
목표:
분석 예측: +1,085M원 (1,475건, 29.10% 잔여)
실제 적용: +1,085M원 (1,475건, 29.10% 잔여) ✅ (동일해야 함)
```

### 1.2 핵심 산출물

1. **즉시 사용 가능한 매수 조건식 파일** (`*_segment_code_final.txt`)
   - 원본 매수 조건식 + 세그먼트 필터 통합
   - 런타임 매핑 포함
   - 바로 백테스팅에 적용 가능

2. **종합 Summary Report**
   - 사용된 매수/매도 조건식 원문 포함
   - 분석 결과 예측값
   - 생성된 필터 조건식

3. **검증 시스템**
   - 분석 예측값 == 실제 백테스트 결과 검증
   - 자동화된 일관성 체크

---

## 2. 핵심 문제 분석

### 2.1 근본 원인 (커밋 5540b6b6에서 발견)

```
문제 상황:
- combos.csv 예측: +1,085M원 (1,475건, 29.10% 잔여)
- 실제 적용 결과: +972M원 (1,095건, 21.5% 잔여)
- 차이: -113M원 (-380건, -7.6%p) ❌

원인 분석:
1. 세그먼트 분석 단계 (phase2_runner.py)
   - 원본 데이터로 분위수 계산 → 경계 A (예: 대형주 ≥ 6,432억)
   - ranges.csv에 저장

2. 필터 적용 단계 (back_static.py)
   - 새로운 SegmentBuilder() 생성 → 분위수 재계산
   - 강화 데이터(enhanced_df)로 인해 경계 B (다름!)
   - 결과: 다른 거래에 필터 적용 → 예측값 불일치

핵심: "조건을 결정한 경계"와 "조건을 적용하는 경계"가 달랐음
```

### 2.2 해결 방법

```python
# 기존 (문제)
builder = SegmentBuilder()  # 새로 생성 → 경계 재계산 → 불일치!

# 수정 (해결)
seg_config = _load_segment_config_from_ranges(global_best)  # ranges.csv 로드
builder = SegmentBuilder(seg_config)  # 저장된 경계 사용 → 일치!
```

---

## 3. 커밋 분석 및 반영 계획

### 3.1 research/segment-final-reset 브랜치 전체 커밋

| 순서 | 커밋 | 설명 | 반영 여부 | 이유 |
|------|------|------|----------|------|
| 1 | `7b5e15ee` | 세그먼트 최종 조건식 생성/안내 및 문서 정리 | ✅ 반영 | 사용자 요청 (6ae3ea82~506863da 범위의 첫 커밋) |
| 2 | `6ae3ea82` | 필터 후보에서 매수금액/당일거래대금_매수매도_비율 제외 | ✅ 반영 | 사용자 요청 |
| 3 | `6c0a0d68` | 세그먼트 최종조건식 주입 방식 개선 | ✅ 반영 | 사용자 요청 |
| 4 | `19a022d3` | 세그먼트 필터 런타임 매핑 보강 | ✅ 반영 | 사용자 요청 |
| 5 | `5fd56aff` | 매수 초당/분당 거래대금 매핑 보정 | ✅ 반영 | 사용자 요청 |
| 6 | `506863da` | 틱/분봉 데이터 타입 판단 로직 개선 | ✅ 반영 | 사용자 요청 (범위 끝) |
| 7 | `0f9f8293` | 최상위 템플릿 segment_code 사용 | ✅ 반영 (검토 후) | 검토 요청 범위 |
| 8 | `f46ca940` | 런타임 매핑 함수 체크 버그 수정 | ✅ 반영 (검토 후) | 검토 요청 범위 |
| 9 | `8c1ea6f2` | 변수 인식 오류 수정 (locals() 제거) | ✅ 반영 (검토 후) | 검토 요청 범위 |
| 10 | `f1e0df9e` | if/elif 논리 버그 수정 | ✅ 반영 (검토 후) | 검토 요청 범위 끝 |
| 11 | `5540b6b6` | **핵심!** 예측값/실제값 일치 구현 (ranges.csv 로드) | ✅ **필수 반영** | 핵심 문제 해결 |
| 12 | `6bd012bc` | Merge branch | ⚠️ 선택적 | Merge 커밋 |
| 13 | `58570315` | 파이프라인 리팩토링 및 검증 체계 보강 | ✅ 반영 (검토 필요) | 검증 강화 |
| 14 | `3b9e786f` | 출력 번호체계/alias 정비 | ✅ 반영 | 사용자 요청 (번호 개선) |
| 15 | `ae059806` | 출력 파일명 번호 체계 | ✅ 반영 | 사용자 요청 |
| 16 | `009dc5fe` | 출력 파일 번호 체계 재정비 | ✅ 반영 | 사용자 요청 (범위 끝) |
| 17~ | `2114dda3`~`e783e17c` | B_/S_ 컬럼 표준화 시도들 | ❌ **무시** | 실패한 시도들 (사용자 지시) |

### 3.2 반영 순서

```
Phase A: 기초 기능 (7b5e15ee ~ 506863da)
Phase B: 검토 후 반영 (0f9f8293 ~ f1e0df9e)
Phase C: 핵심 버그 수정 (5540b6b6) ← 가장 중요!
Phase D: 검증 강화 (58570315)
Phase E: 번호 체계 정비 (3b9e786f ~ 009dc5fe)
```

---

## 4. 변수 정의 명세 시스템

### 4.1 설계 원칙 (detail_canonical_schema.py 참고)

```
명명 규칙:
1. 거래 기본 정보: 접두사 없음 (매수가, 매도가, 수익률, 보유시간)
2. 매수 시점 스냅샷: "매수시_" 또는 "매수" 접두사
3. 매도 시점 스냅샷: "매도시_" 또는 "매도" 접두사
4. 종목 고유 속성: 접두사 없음 (시가총액, 종목명, 종목코드)

주의: B_/S_ 패턴은 사용하지 않음 (실패한 시도)
```

### 4.2 런타임 매핑 블록

백테스팅 엔진에서 사용하는 변수명 → 분석에서 사용하는 변수명 매핑:

```python
# 세그먼트 필터에서 사용하는 변수들의 런타임 매핑
# code_generator.py의 _build_segment_runtime_preamble() 함수에서 생성

매수초당거래대금 = (분당거래대금 / 60) if '분당거래대금' in locals() else 초당거래대금
매수등락율 = 등락율
매수체결강도 = 체결강도
매수당일거래대금 = 당일거래대금
# ... (Back_Testing_Guideline_Tick/Min.md 문서 참조)
```

---

## 5. 파이프라인 전체 흐름

### 5.1 현재 파이프라인

```
1. 백테스트 실행
   └→ detail.csv 생성 (거래 상세 기록)

2. 강화 분석 (RunEnhancedAnalysis)
   ├→ 파생 지표 계산
   ├→ 필터 효과 분석
   └→ 필터 코드 생성

3. 세그먼트 분석 (Phase 1~3)
   ├→ Phase 1: 세그먼트 분할
   ├→ Phase 2: 조합 최적화 → combos.csv, ranges.csv
   └→ Phase 3: 검증

4. 조건식 생성
   ├→ segment_code.txt (세그먼트 필터만)
   └→ segment_code_final.txt (매수 조건식 + 세그먼트 필터 통합) ← 목표!
```

### 5.2 수정 후 파이프라인

```
1. 백테스트 실행
   └→ detail.csv 생성

2. 강화 분석
   └→ 필터 분석

3. 세그먼트 분석
   ├→ ranges.csv 저장 (경계값)
   ├→ combos.csv 저장 (최적 조합)
   └→ global_best에 ranges_path 포함 ✅

4. 조건식 생성
   ├→ segment_code.txt
   └→ segment_code_final.txt (매수 + 필터 통합, 런타임 매핑 포함)

5. Summary Report 생성
   ├→ 원본 매수/매도 조건식 포함 ✅
   ├→ 분석 예측값 포함
   └→ 생성된 조건식 경로 포함

6. 필터 적용 검증 (선택적)
   ├→ ranges.csv 로드 (동일 경계 사용) ✅
   └→ 예측값 == 실제값 검증
```

---

## 6. 구현 계획

### Phase 1: 커밋 반영 (순서대로)

#### Step 1.1: 기초 기능 (7b5e15ee ~ 506863da)
```bash
git cherry-pick 7b5e15ee  # 최종 조건식 생성/안내
git cherry-pick 6ae3ea82  # 필터 후보 제외
git cherry-pick 6c0a0d68  # 주입 방식 개선
git cherry-pick 19a022d3  # 런타임 매핑 보강
git cherry-pick 5fd56aff  # 거래대금 매핑 보정
git cherry-pick 506863da  # 틱/분봉 판단 로직
```

#### Step 1.2: 검토 후 반영 (0f9f8293 ~ f1e0df9e)
```bash
git cherry-pick 0f9f8293  # 최상위 템플릿 segment_code
git cherry-pick f46ca940  # 런타임 매핑 함수 체크
git cherry-pick 8c1ea6f2  # locals() 제거
git cherry-pick f1e0df9e  # if/elif 수정
```

#### Step 1.3: 핵심 버그 수정 (5540b6b6) ← 가장 중요!
```bash
git cherry-pick 5540b6b6  # ranges.csv 로드하여 동일 경계 사용
```

#### Step 1.4: 검증 강화 (58570315)
```bash
git cherry-pick 58570315  # 파이프라인 리팩토링
```

#### Step 1.5: 번호 체계 정비 (3b9e786f ~ 009dc5fe)
```bash
git cherry-pick 3b9e786f  # 출력 번호체계/alias
git cherry-pick ae059806  # 파일명 번호 체계
git cherry-pick 009dc5fe  # 번호 체계 재정비
```

### Phase 2: 최종 조건식 파일 생성 검증

1. `segment_code_final.txt` 파일이 생성되는지 확인
2. 파일에 다음 내용이 포함되는지 검증:
   - 원본 매수 조건식
   - 세그먼트 필터 조건식
   - 런타임 매핑 블록
   - `if 매수 and 필터통과:` 형태의 통합 조건

### Phase 3: Summary Report 개선

1. 사용된 매수/매도 조건식 원문 포함
2. 분석 예측값 (수익 개선, 거래 감소율)
3. 생성된 조건식 파일 경로

### Phase 4: 검증 테스트

1. 분석 예측값 추출
2. 생성된 조건식으로 백테스트 재실행
3. 결과 비교: 예측값 == 실제값?

---

## 7. 파일 수정 목록

### 7.1 핵심 수정 파일

| 파일 | 수정 내용 |
|------|----------|
| `backtester/back_static.py` | `_load_segment_config_from_ranges()` 함수 추가, ranges.csv 로드 |
| `backtester/segment_analysis/phase2_runner.py` | `global_best`에 `ranges_path` 저장 |
| `backtester/segment_analysis/code_generator.py` | 런타임 매핑 보강, 최종 조건식 생성 |
| `backtester/analysis_enhanced/runner.py` | 최종 조건식 생성 호출 |
| `backtester/segment_analysis/segment_summary_report.py` | 매수/매도 조건식 원문 포함 |

### 7.2 참조 문서

| 문서 | 용도 |
|------|------|
| `docs/Guideline/Back_Testing_Guideline_Tick.md` | 틱 데이터 변수 정의 (826개) |
| `docs/Guideline/Back_Testing_Guideline_Min.md` | 분봉 데이터 변수 정의 (752개) |
| `docs/Study/segment_filter_verification_issue.md` | 문제 분석 문서 |

---

## 8. 검증 기준

### 8.1 필수 검증 항목

| 항목 | 기준 |
|------|------|
| segment_code_final.txt 생성 | 파일 존재 및 내용 검증 |
| 런타임 매핑 포함 | `매수초당거래대금 = ...` 등 매핑 코드 존재 |
| 매수 조건식 통합 | `if 매수 and 필터통과:` 패턴 존재 |
| Summary Report | 매수/매도 조건식 원문 포함 |
| 예측값 일치 | combos.csv 예측 == 실제 백테스트 결과 |

### 8.2 성공 기준

```
✅ segment_code_final.txt 파일이 바로 사용 가능한 형태로 생성됨
✅ Summary Report에 모든 필요 정보 포함
✅ 분석 예측값과 실제 백테스트 결과가 ±1% 이내로 일치
```

---

## 9. 위험 요소 및 대응

| 위험 | 대응 |
|------|------|
| 충돌 발생 시 | 충돌 해결 후 검증, 필요시 수동 병합 |
| 경계값 불일치 | ranges.csv 로드 검증 로그 추가 |
| 변수명 매핑 오류 | 가이드라인 문서 기반 검증 |

---

## 10. 일정

| Phase | 예상 소요 | 설명 |
|-------|----------|------|
| Phase 1 | 2-3시간 | 커밋 반영 및 충돌 해결 |
| Phase 2 | 1시간 | 최종 조건식 생성 검증 |
| Phase 3 | 1시간 | Summary Report 개선 |
| Phase 4 | 1-2시간 | 검증 테스트 |
| **합계** | **5-7시간** | |

---

## 11. 부록: 자동화 테스트 시스템 (선택적)

### 11.1 목표

- 수동 테스트 프로세스 자동화
- AI가 직접 테스트 실행 및 결과 분석 가능

### 11.2 현재 수동 프로세스

```
1. stom_venv.bat 실행
2. '주식 전략' 아이콘 클릭
3. 백테스트 아이콘 클릭
4. 날짜 선택 (2025-04-01 ~ 2025-11-30)
5. 파라미터 입력 (900, 1519, 30, 32)
6. 백테스트 엔진 시작
7. 조건식 선택 (Min_B_Study_251227, Min_S_Study_251227)
8. 백테스트 실행
9. 결과 분석
```

### 11.3 자동화 방안 (구현 시 고려)

```python
# CLI 기반 백테스트 실행기 (예시)
# 기존 GUI 코드에 영향 없이 별도 모듈로 구현

def run_backtest_headless(
    start_date: str,
    end_date: str,
    buy_strategy: str,
    sell_strategy: str,
    params: tuple,
) -> dict:
    """헤드리스 백테스트 실행"""
    # ... 구현
    return results
```

### 11.4 우선순위

**핵심 기능 완성이 최우선**, 자동화는 핵심 완성 후 검토

---

**문서 버전**: 2.0
**작성자**: AI Assistant
**최종 수정**: 2026-01-05
