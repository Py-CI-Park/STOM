# 세그먼트 필터 검증 체크리스트

**버전**: v1.0  
**목적**: 세그먼트 필터의 예상값과 실제 적용 결과가 일치하는지 단계별로 검증

---

## 1) 산출물 존재 확인

- `*_detail.csv` 존재
- `*_segment_combos.csv` 존재
- `*_segment_code_final.txt` 존재
- `*_segment_verification.csv` 생성 여부 확인

---

## 2) 예상 vs 실제 비교

### 2.1 세그먼트 예상값(전역 조합)
- `*_segment_combos.csv`의 `combo_id=1` 값 확인
  - `remaining_trades`
  - `remaining_ratio`
  - `total_improvement`

### 2.2 실제 적용 결과
- `*_segment_verification.csv` 확인
  - `remaining_trades`
  - `remaining_ratio`
  - `improvement`
  - `expected_remaining_trades`
  - `expected_improvement`

---

## 3) 불일치 발생 시 점검 포인트

1. **세그먼트 경계 불일치**
   - `*_segment_ranges.csv`와 `segment_code_final.txt`의 구간이 동일한지 확인
2. **런타임 매핑 누락**
   - `segment_code_final.txt`의 runtime mapping 블록 포함 여부 확인
3. **변수 계산 방식 차이**
   - `모멘텀점수`, `위험도점수` 등 고정 스케일 계산식과 일치 여부 확인
4. **누락 컬럼**
   - `*_segment_verification.csv`의 `missing_columns` 확인
5. **Out_of_Range 거래**
   - `out_of_range_trades` 값 확인

---

## 4) 필터 적용 검증(일반 필터)

- `*_filter_verification.csv` 확인
  - `remaining_trades`
  - `improvement`
  - `expected_improvement`

---

## 5) 최종 확인

- `*_segment_code_final.txt`로 백테스트 재실행 후 결과 비교
- `*_segment_filtered.png` / `*_filtered.png` 이미지 시각 비교

