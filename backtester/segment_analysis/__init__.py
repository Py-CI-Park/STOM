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
from .combination_optimizer import CombinationOptimizerConfig
from .threshold_optimizer import ThresholdOptimizerConfig
from .validation import StabilityValidationConfig
from .code_generator import build_segment_filter_code, save_segment_code
from .risk_metrics import summarize_risk
from .multi_objective import MultiObjectiveConfig, evaluate_candidates, build_pareto_front

__all__ = [
    'SegmentConfig',
    'SegmentBuilder',
    'FilterEvaluatorConfig',
    'FilterEvaluator',
    'CombinationOptimizerConfig',
    'ThresholdOptimizerConfig',
    'StabilityValidationConfig',
    'build_segment_filter_code',
    'save_segment_code',
    'summarize_risk',
    'MultiObjectiveConfig',
    'evaluate_candidates',
    'build_pareto_front',
]
