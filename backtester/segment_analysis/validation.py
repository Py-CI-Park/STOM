# -*- coding: utf-8 -*-
"""
Constraint Validation Helpers

세그먼트/전역 제약 조건을 검증합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ConstraintConfig:
    min_trades_per_segment: int = 30
    max_exclusion_per_segment: float = 0.85
    max_exclusion_global: float = 0.80
    min_total_trades: Optional[int] = None


def validate_segment_combo(remaining_trades: int, exclusion_ratio: float, config: ConstraintConfig) -> bool:
    if remaining_trades < config.min_trades_per_segment:
        return False
    if exclusion_ratio > config.max_exclusion_per_segment:
        return False
    return True


def validate_global_state(excluded_trades: int, total_trades: int, config: ConstraintConfig) -> bool:
    excluded_ratio = excluded_trades / max(1, total_trades)
    if excluded_ratio > config.max_exclusion_global:
        return False
    if config.min_total_trades is not None and (total_trades - excluded_trades) < config.min_total_trades:
        return False
    return True
