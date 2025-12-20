# -*- coding: utf-8 -*-
"""
Segment Analysis Package

세그먼트 기반 필터 최적화 시스템:
- 시가총액/시간 구간별 데이터 분할
- 세그먼트별 필터 평가 및 최적화
- 다목적 최적화 및 검증

Author: Claude Code
Date: 2025-12-20
"""

from .segmentation import SegmentConfig, SegmentBuilder
from .filter_evaluator import FilterEvaluatorConfig, FilterEvaluator

__all__ = [
    'SegmentConfig',
    'SegmentBuilder',
    'FilterEvaluatorConfig',
    'FilterEvaluator',
]
