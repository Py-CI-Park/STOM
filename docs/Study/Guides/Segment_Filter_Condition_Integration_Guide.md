# 세그먼트 필터 조건식 통합 프로세스 가이드

## 1. 목적

세그먼트 필터 최적화 결과를 **기존 매수/매도 조건식에 안정적으로 통합**하고,
바로 사용할 수 있는 최종 조건식(`*_segment_code_final.txt`)을 생성하는 절차를 정리합니다.

---

## 2. 입력/출력 구조

### 2.1 백테스팅 출력 폴더 구조

- 출력 폴더 패턴: `backtester/backtesting_output/<save_file_name>/`
- 예시: `backtester/backtesting_output/stock_bt_Min_B_Study_251227_20251229173431/`

### 2.2 핵심 산출물 파일

#### 기본 필터(세그먼트 제외)
- `*_filter.csv`: 개별 필터 후보
- `*_filter_combinations.csv`: 필터 조합 결과
- `*_filtered.png`: 필터 적용 수익 곡선
- `*_filter_verification.csv`: 필터 적용 결과 요약(예상/실제 비교)

#### 필터 적용 detail (신규)
- `*_detail_filtered.csv`: 일반 필터 조건 적용 후 거래 상세(검증용)
- `*_detail_segment.csv`: 세그먼트 필터 적용 후 거래 상세(검증용)

#### 세그먼트 필터(핵심)
- `*_segment_filtered.png`: 세그먼트 필터 적용 결과(이미지/메모 박스 포함)
- `*_segment_combos.csv`: 전역 조합(Global Best) 요약
- `*_segment_code.txt`: 전역 조합 기반 세그먼트 필터 코드(자동 생성)
- `*_segment_ranges.csv`: 실제 사용된 시가총액/시간 구간
- `*_segment_filters.csv`: 세그먼트별 필터 후보
- `*_segment_local_combos.csv`: 세그먼트별 로컬 조합
- `*_segment_summary.csv`: 세그먼트 요약 통계
- `*_segment_verification.csv`: 세그먼트 적용 결과 요약(예상/실제 비교)

#### 템플릿 비교 산출물(옵션)
- `*_segment_template_comparison.csv`
- `*_tmpl_*_segment_ranges.csv`
- `*_tmpl_*_segment_code.txt`

#### 최종 통합 산출물(신규)
- `*_segment_code_final.txt`: **매수 조건식 + 세그먼트 필터 + 매도 조건식 통합본**

> 참고: 출력 파일은 `0_`, `1-1_` 등 번호 접두어로 별칭이 생성될 수 있으며, 기존 파일명도 유지됩니다.

---

## 3. 이미지(세그먼트 필터 결과) 기준과 코드 기준

`*_segment_filtered.png`의 메모 박스에 표시되는 조합은 보통
`*_segment_combos.csv`의 **전역 조합(Global Best)**을 기반으로 합니다.

- **이미지 기준 확인 경로**: `*_segment_combos.csv`
- **코드 기준 확인 경로**: `*_segment_code.txt`
- **구간 기준 확인 경로**: `*_segment_ranges.csv`

> 템플릿 비교(`*_segment_template_comparison.csv`)를 수행한 경우,
> `*_segment_summary_full.txt`에는 템플릿 기반 구간(동적/스케일)이 기록될 수 있습니다.
> 이때 **실제 적용된 구간은 `*_segment_ranges.csv`를 우선** 확인해야 합니다.

---

## 4. 최종 조건식 생성 흐름

1. **원본 매수/매도 조건식 확보**
   - 실험한 조건식 코드(예: Min_B_Study_251227, Min_S_Study_251227)

2. **세그먼트 필터 전역 조합 확인**
   - `*_segment_combos.csv`의 상위 조합 확인
   - `*_segment_code.txt`로 코드 블록 확인

3. **최종 통합 파일 생성**
   - `analysis_enhanced/runner.py` 실행 시
     `*_segment_code_final.txt` 자동 생성
   - 내부 로직: 원본 매수 조건식 + `필터통과` 블록 + `매수 = 매수 and 필터통과` + `if 매수:`

4. **텔레그램 알림 확인**
   - 최종 파일 생성 후: `최종 작성 업데이트 된 조건식 파일: <path>` 메시지 전송

---

## 5. 변수 매핑 및 주의사항

세그먼트 필터는 **매수 시점 스냅샷 변수(매수 접두사)**를 사용합니다.
`*_segment_code_final.txt`에는 기본 매핑/파생 변수 블록이 자동으로 포함되지만,
실전 반영 전에 아래 항목을 반드시 확인하세요.

- `매수매도호가1/매수매수호가1` → `매도호가1/매수호가1`
- `매수매도총잔량/매수매수총잔량` → `매도총잔량/매수총잔량`
- `매수스프레드`, `매수호가잔량비`, `매수변동폭`, `초당*` 계열은 **파생 계산 필요**
- `매수시간/매수일자`는 **`YYYYMMDDHHMM` 형태**로 자동 생성되며, 실전 환경에 맞게 확인 필요
- `모멘텀점수`는 **간소화된 정규화(고정 스케일)**로 계산되므로, 분포 기반 정규화가 필요하면 별도 재정의 필요
- `당일거래대금_매수매도_비율` 등 **매도 시점 값이 필요한 항목**은 실전에서 기본값 처리될 수 있음
- `당일거래대금_전틱분봉_비율`, `당일거래대금_5틱분봉평균_비율`은 **매수 시점 변수**로 필터/세그먼트 필터에 사용 가능

> 상세 변수 정의는 `backtester/back_static.py`의 공식 설명을 참고합니다.

---

## 6. 적용 절차 체크리스트

- [ ] 원본 매수/매도 조건식 확보
- [ ] `*_segment_combos.csv`로 전역 조합 확인
- [ ] `*_segment_ranges.csv`로 실제 구간 확인
- [ ] `*_segment_code_final.txt` 생성 여부 확인
- [ ] 조건식 문서(예: `Condition_Min_Study_251227_Full_Segment.md`) 업데이트
- [ ] 최종 백테스트 재검증 및 보고서(`*_report.txt`) 확인

---

## 7. 예시 경로 (Min_B_Study_251227)

- 출력 폴더: `backtester/backtesting_output/stock_bt_Min_B_Study_251227_20251229173431/`
- 이미지: `..._segment_filtered.png`
- 전역 조합: `..._segment_combos.csv`
- 세그먼트 코드: `..._segment_code.txt`
- 구간 정의: `..._segment_ranges.csv`
- 최종 통합 코드: `..._segment_code_final.txt`

---

## 8. 참고 문서

- `docs/Study/ResearchReports/2025-12-20_Segmented_Filter_Optimization_Research.md`
- `docs/Study/ResearchReports/2025-12-29_Overfitting_Risk_Assessment_Filter_Segment_Analysis.md`
- `docs/Condition/Min/2_Under_review/Condition_Min_Study_251227_Full_Segment.md`
