# -*- coding: utf-8 -*-
"""
[2025-12-10] Backtesting enhanced analysis module
[2025-12-13] Additional improvements applied

Features:
1. Statistical significance checks (t-test, effect size)
2. Filter combination analysis (synergy)
3. ML-based feature importance
4. Dynamic optimal threshold search
5. Auto condition code generation
6. Period-based filter stability
7. Tick/Min timeframe auto-detection
8. Synergy heatmap visualization
9. Threshold efficiency curve charts
10. Dynamic X-axis binning (data distribution)
11. Risk score formula chart

Author: Claude
Date: 2025-12-10, Updated: 2025-12-13

Refactor: feature modules separated, this file re-exports the public API.
"""

from backtester.analysis_enhanced.config import (
    MODEL_BASE_DIR,
    ML_RELIABILITY_CRITERIA,
    FILTER_MAX_EXCLUSION_RATIO,
    FILTER_MIN_REMAINING_TRADES,
)
from backtester.analysis_enhanced.utils import (
    _normalize_text_for_hash,
    ComputeStrategyKey,
    _extract_strategy_block_lines,
    _safe_filename,
    _write_json,
    _append_jsonl,
)
from backtester.analysis_enhanced.stats import (
    CalculateStatisticalSignificance,
    CalculateEffectSizeInterpretation,
)
from backtester.analysis_enhanced.metrics_enhanced import (
    DetectTimeframe,
    CalculateEnhancedDerivedMetrics,
)
from backtester.analysis_enhanced.thresholds import (
    FindOptimalThresholds,
    FindOptimalRangeThresholds,
    FindAllOptimalThresholds,
)
from backtester.analysis_enhanced.filters import (
    AnalyzeFilterCombinations,
    AnalyzeFilterEffectsEnhanced,
    AnalyzeFilterEffectsLookahead,
    AnalyzeFilterStability,
    GenerateFilterCode,
)
from backtester.analysis_enhanced.ml import (
    AssessMlReliability,
    _save_ml_bundle,
    _load_ml_bundle,
    _feature_schema_hash,
    _prepare_feature_matrix,
    _apply_ml_bundle,
    _extract_tree_rules,
    AnalyzeFeatureImportance,
    PredictRiskWithML,
)
from backtester.analysis_enhanced.plotting import (
    CreateSynergyHeatmapData,
    PrepareThresholdCurveData,
    _FindNearestIndex,
    PltEnhancedAnalysisCharts,
)
from backtester.analysis_enhanced.runner import RunEnhancedAnalysis

__all__ = [
    'MODEL_BASE_DIR',
    'ML_RELIABILITY_CRITERIA',
    'FILTER_MAX_EXCLUSION_RATIO',
    'FILTER_MIN_REMAINING_TRADES',
    '_normalize_text_for_hash',
    'ComputeStrategyKey',
    '_extract_strategy_block_lines',
    '_safe_filename',
    '_write_json',
    '_append_jsonl',
    'CalculateStatisticalSignificance',
    'CalculateEffectSizeInterpretation',
    'DetectTimeframe',
    'CalculateEnhancedDerivedMetrics',
    'FindOptimalThresholds',
    'FindOptimalRangeThresholds',
    'FindAllOptimalThresholds',
    'AnalyzeFilterCombinations',
    'AnalyzeFilterEffectsEnhanced',
    'AnalyzeFilterEffectsLookahead',
    'AnalyzeFilterStability',
    'GenerateFilterCode',
    'AssessMlReliability',
    '_save_ml_bundle',
    '_load_ml_bundle',
    '_feature_schema_hash',
    '_prepare_feature_matrix',
    '_apply_ml_bundle',
    '_extract_tree_rules',
    'AnalyzeFeatureImportance',
    'PredictRiskWithML',
    'CreateSynergyHeatmapData',
    'PrepareThresholdCurveData',
    '_FindNearestIndex',
    'PltEnhancedAnalysisCharts',
    'RunEnhancedAnalysis',
]
