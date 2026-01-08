#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
세그먼트 필터 우선 적용 (filter_first=True) 스탠드얼론 테스트

[2026-01-08] 방안 B 구현 검증
- 임포트 종속성 없이 독립 실행 가능
"""

import re
from typing import List, Tuple


def _normalize_code_lines(code_text):
    """코드 텍스트를 라인 리스트로 변환"""
    if not code_text:
        return []
    if isinstance(code_text, str):
        return code_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    return [str(code_text)]


def _inject_segment_filter_first(
    working_lines: List[str],
    segment_code_lines: List[str],
) -> Tuple[List[str], bool]:
    """
    세그먼트 필터를 기존 조건 앞에 배치합니다 (방안 B 구현).
    - code_generator.py의 실제 함수 복사
    """
    # "매수 = True" 라인 찾기
    buy_true_idx = None
    for idx, line in enumerate(working_lines):
        stripped = line.strip()
        if stripped == '매수 = True':
            buy_true_idx = idx
            break

    if buy_true_idx is None:
        print("[Segment Code Generator] '매수 = True' 라인을 찾지 못함 - 파일 끝에 추가")
        fallback = list(working_lines)
        fallback.append("")
        fallback.append("# === 세그먼트 필터 (자동 생성) ===")
        fallback.extend(segment_code_lines)
        fallback.append("")
        return fallback, False

    insert_idx = buy_true_idx + 1
    while insert_idx < len(working_lines) and not working_lines[insert_idx].strip():
        insert_idx += 1

    remaining_lines = working_lines[insert_idx:]

    simple_block = []
    simple_block.append("")
    simple_block.append("# === 세그먼트 필터 (자동 생성) ===")
    simple_block.append("# [2026-01-08] 세그먼트 필터 우선 적용")
    simple_block.append("# 세그먼트 필터를 먼저 평가하여, 해당 세그먼트에서 제외할 거래를 먼저 필터링")
    simple_block.extend(segment_code_lines)
    simple_block.append("")
    simple_block.append("# === 세그먼트 필터 통과 후 기존 조건 평가 ===")
    simple_block.append("# 세그먼트 필터에서 매수=False인 경우, 아래 기존 조건은 추가 제외만 할 뿐 영향 없음")
    simple_block.append("")

    new_lines = []
    new_lines.extend(working_lines[:buy_true_idx + 1])
    new_lines.extend(simple_block)
    new_lines.extend(remaining_lines)

    return new_lines, True


def test_filter_first():
    """filter_first=True 동작 테스트"""

    # 테스트용 원본 매수 조건식
    original_buy_code = """
# 분봉 기반 변수 정의
전일종가 = 현재가 / (1 + (등락율 / 100))

매수 = True

# 공통 선결 조건
if not (관심종목 == 1):
    매수 = False
elif not (0 < 현재가 <= 50000):
    매수 = False
elif not (1.0 < 등락율 <= 20.0):
    매수 = False
elif 시분초 < 120000:
    if 시가총액 < 100000:
        if not (전일비 > 0):
            매수 = False
    else:
        매수 = False
else:
    매수 = False
"""

    # 테스트용 세그먼트 필터 코드
    segment_filter_code = """
# [T1_092900_095900] 시간대
if 시분초 >= 92900 and 시분초 < 95900:
    if 시가총액 >= 6432:
        if not (등락율 < 10):
            매수 = False
        elif not (체결강도 > 100):
            매수 = False
    else:
        매수 = False
else:
    # 정의되지 않은 시간대
    pass
"""

    buy_lines = _normalize_code_lines(original_buy_code)
    segment_lines = _normalize_code_lines(segment_filter_code)

    print("=" * 80)
    print("[테스트] filter_first=True 동작 검증")
    print("=" * 80)

    # filter_first=True (새로운 동작)
    result_first, success_first = _inject_segment_filter_first(buy_lines, segment_lines)

    print("\n[filter_first=True] 세그먼트 필터 우선 적용 결과:")
    print("-" * 80)

    # 매수 = True 위치 확인
    buy_true_idx = None
    segment_start_idx = None
    existing_cond_start_idx = None

    for i, line in enumerate(result_first):
        stripped = line.strip()
        if stripped == '매수 = True':
            buy_true_idx = i
        if '# === 세그먼트 필터' in line and segment_start_idx is None:
            segment_start_idx = i
        if '# 공통 선결 조건' in line:
            existing_cond_start_idx = i

    print(f"매수 = True 위치: 라인 {buy_true_idx}")
    print(f"세그먼트 필터 시작 위치: 라인 {segment_start_idx}")
    print(f"기존 조건 시작 위치: 라인 {existing_cond_start_idx}")

    # 순서 검증
    if buy_true_idx is not None and segment_start_idx is not None and existing_cond_start_idx is not None:
        if buy_true_idx < segment_start_idx < existing_cond_start_idx:
            print("\n[PASS] Correct order: buy=True -> segment filter -> existing conditions")
            order_correct = True
        else:
            print("\n[FAIL] Wrong order!")
            print(f"   Expected: {buy_true_idx} < {segment_start_idx} < {existing_cond_start_idx}")
            order_correct = False
    else:
        print("\n[WARN] Some markers not found")
        order_correct = False

    # 결과 출력
    print("\n[결과 코드]:")
    print("-" * 80)
    for i, line in enumerate(result_first):
        marker = ""
        if i == buy_true_idx:
            marker = " <-- BUY = True"
        elif i == segment_start_idx:
            marker = " <-- SEGMENT FILTER START"
        elif i == existing_cond_start_idx:
            marker = " <-- EXISTING CONDITIONS START"
        print(f"{i+1:3d}| {line}{marker}")

    return order_correct


if __name__ == '__main__':
    success = test_filter_first()
    print("\n" + "=" * 80)
    if success:
        print("[PASS] Test passed: filter_first=True works correctly.")
    else:
        print("[FAIL] Test failed: filter_first=True has issues.")
    print("=" * 80)
