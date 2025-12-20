# -*- coding: utf-8 -*-
"""
Segment Filter Optimizer (Phase 1)

세그먼트 분할 + 필터 평가 + 기본 산출물 생성까지 실행합니다.
"""

from __future__ import annotations

from backtester.segment_analysis.phase1_runner import run_phase1


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m backtester.segment_filter_optimizer <detail.csv>")

    summary_path, filters_path = run_phase1(sys.argv[1])
    print(f"[Phase1] Summary: {summary_path}")
    if filters_path:
        print(f"[Phase1] Filters: {filters_path}")
    else:
        print("[Phase1] Filters: (empty)")
