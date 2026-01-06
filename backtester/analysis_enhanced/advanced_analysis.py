# -*- coding: utf-8 -*-
"""
Advanced Analysis Module

고급 분석 기능을 제공합니다:
- SHAP 기반 특성 중요도 해석
- 적응형 세그먼트 클러스터링
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


# =============================================================================
# SHAP 기반 특성 중요도 분석
# =============================================================================

@dataclass
class SHAPAnalysisResult:
    """SHAP 분석 결과"""
    feature_importance: List[Tuple[str, float]]  # (feature_name, importance)
    feature_directions: Dict[str, float]  # feature -> mean shap (positive = increases loss)
    top_positive_features: List[str]  # 손실 증가 특성
    top_negative_features: List[str]  # 손실 감소 특성
    shap_values: Optional[np.ndarray] = None
    error: Optional[str] = None


def analyze_with_shap(
    df: pd.DataFrame,
    model,
    feature_columns: List[str],
    target_column: str = '수익금',
    n_samples: int = 1000,
) -> SHAPAnalysisResult:
    """
    SHAP을 사용하여 모델의 특성 중요도를 분석합니다.

    SHAP(SHapley Additive exPlanations)은 각 특성이 예측에 미치는 기여도를
    게임 이론 기반으로 계산합니다.

    Args:
        df: 데이터프레임
        model: 학습된 sklearn 모델 (tree-based 권장)
        feature_columns: 분석할 특성 컬럼 리스트
        target_column: 타겟 컬럼
        n_samples: SHAP 계산에 사용할 샘플 수 (속도/정확도 트레이드오프)

    Returns:
        SHAPAnalysisResult: SHAP 분석 결과
    """
    try:
        import shap
    except ImportError:
        return SHAPAnalysisResult(
            feature_importance=[],
            feature_directions={},
            top_positive_features=[],
            top_negative_features=[],
            error="shap 라이브러리가 설치되지 않았습니다. pip install shap"
        )

    try:
        # 데이터 준비
        available_cols = [c for c in feature_columns if c in df.columns]
        if not available_cols:
            return SHAPAnalysisResult(
                feature_importance=[],
                feature_directions={},
                top_positive_features=[],
                top_negative_features=[],
                error="사용 가능한 특성 컬럼이 없습니다"
            )

        X = df[available_cols].fillna(0).values
        
        # 샘플링 (대규모 데이터 처리)
        if len(X) > n_samples:
            indices = np.random.choice(len(X), size=n_samples, replace=False)
            X_sample = X[indices]
        else:
            X_sample = X

        # SHAP 계산 (Tree 모델용 최적화)
        if hasattr(model, 'feature_importances_'):
            # Tree-based model
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_sample)
            
            # Binary classification의 경우 positive class 선택
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            # 기타 모델용 Kernel SHAP (느림)
            explainer = shap.KernelExplainer(model.predict_proba, shap.sample(X_sample, 100))
            shap_values = explainer.shap_values(X_sample[:100])
            if isinstance(shap_values, list):
                shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]

        # 특성별 중요도 계산
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        mean_shap = shap_values.mean(axis=0)  # 방향성 포함

        # 결과 정리
        importance_list = sorted(
            zip(available_cols, mean_abs_shap),
            key=lambda x: x[1],
            reverse=True
        )

        directions = dict(zip(available_cols, mean_shap))

        # 손실 증가/감소 특성 분류
        positive_features = [f for f, d in directions.items() if d > 0]
        negative_features = [f for f, d in directions.items() if d < 0]

        # 상위 특성 선택 (중요도 기준)
        top_positive = [f for f, _ in importance_list if f in positive_features][:5]
        top_negative = [f for f, _ in importance_list if f in negative_features][:5]

        return SHAPAnalysisResult(
            feature_importance=[(f, float(v)) for f, v in importance_list],
            feature_directions={k: float(v) for k, v in directions.items()},
            top_positive_features=top_positive,
            top_negative_features=top_negative,
            shap_values=shap_values,
        )

    except Exception as e:
        return SHAPAnalysisResult(
            feature_importance=[],
            feature_directions={},
            top_positive_features=[],
            top_negative_features=[],
            error=str(e)
        )


def get_shap_filter_recommendations(
    shap_result: SHAPAnalysisResult,
    df: pd.DataFrame,
    top_n: int = 5,
) -> List[Dict]:
    """
    SHAP 결과를 기반으로 필터 추천을 생성합니다.

    손실을 증가시키는 특성(positive SHAP)에 대해
    해당 특성의 극단값을 제외하는 필터를 추천합니다.

    Args:
        shap_result: SHAP 분석 결과
        df: 데이터프레임
        top_n: 추천 필터 수

    Returns:
        필터 추천 리스트
    """
    recommendations = []

    for feature in shap_result.top_positive_features[:top_n]:
        if feature not in df.columns:
            continue

        direction = shap_result.feature_directions.get(feature, 0)
        values = df[feature].dropna()

        if len(values) < 10:
            continue

        # 손실 증가 방향 확인
        # Positive SHAP = 높은 값이 손실 증가 → 높은 값 제외
        # (실제로는 도메인 지식 필요)
        threshold = values.quantile(0.8) if direction > 0 else values.quantile(0.2)

        recommendations.append({
            '특성': feature,
            'SHAP_방향': round(direction, 4),
            '추천_임계값': round(threshold, 4),
            '추천_필터': f"{feature} < {threshold:.2f}" if direction > 0 else f"{feature} >= {threshold:.2f}",
            '근거': f"SHAP {direction:.3f} (손실 {'증가' if direction > 0 else '감소'})"
        })

    return recommendations


# =============================================================================
# 적응형 세그먼트 클러스터링
# =============================================================================

@dataclass
class AdaptiveSegmentResult:
    """적응형 세그먼트 결과"""
    n_segments: int
    segment_labels: np.ndarray
    segment_boundaries: Dict[str, List[Tuple[float, float]]]  # column -> [(min, max), ...]
    segment_stats: List[Dict]  # 각 세그먼트 통계
    clustering_method: str
    silhouette_score: Optional[float] = None
    error: Optional[str] = None


def discover_adaptive_segments(
    df: pd.DataFrame,
    segment_columns: List[str] = None,
    n_segments: int = 4,
    method: str = 'kmeans',
) -> AdaptiveSegmentResult:
    """
    K-Means 클러스터링으로 자연스러운 세그먼트 경계를 발견합니다.

    고정된 시가총액 구간(초소형주/소형주/중형주/대형주) 대신,
    실제 데이터 분포에 맞는 세그먼트를 자동으로 발견합니다.

    Args:
        df: 데이터프레임
        segment_columns: 세그먼트 기준 컬럼 (기본: ['시가총액'])
        n_segments: 세그먼트 수
        method: 클러스터링 방법 ('kmeans' | 'quantile')

    Returns:
        AdaptiveSegmentResult: 세그먼트 결과
    """
    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import silhouette_score
    except ImportError:
        return AdaptiveSegmentResult(
            n_segments=0,
            segment_labels=np.array([]),
            segment_boundaries={},
            segment_stats=[],
            clustering_method=method,
            error="sklearn 라이브러리가 필요합니다"
        )

    # 기본 세그먼트 컬럼
    if segment_columns is None:
        segment_columns = ['시가총액']

    # 사용 가능한 컬럼 필터링
    available_cols = [c for c in segment_columns if c in df.columns]
    if not available_cols:
        return AdaptiveSegmentResult(
            n_segments=0,
            segment_labels=np.array([]),
            segment_boundaries={},
            segment_stats=[],
            clustering_method=method,
            error="세그먼트 기준 컬럼이 없습니다"
        )

    try:
        # 데이터 준비
        X = df[available_cols].fillna(df[available_cols].median()).values

        # 로그 변환 (시가총액 등 스케일이 큰 변수)
        X_log = np.log1p(np.abs(X))

        # 스케일링
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_log)

        # 클러스터링
        if method == 'kmeans':
            kmeans = KMeans(n_clusters=n_segments, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)
        elif method == 'quantile':
            # 분위수 기반 세그먼트
            labels = np.zeros(len(df), dtype=int)
            for i, col in enumerate(available_cols):
                quantiles = pd.qcut(df[col], q=n_segments, labels=False, duplicates='drop')
                labels = labels * n_segments + quantiles.fillna(0).astype(int)
            labels = labels % n_segments
        else:
            labels = np.zeros(len(df), dtype=int)

        # 실루엣 점수 계산
        sil_score = None
        if len(np.unique(labels)) > 1:
            try:
                sil_score = silhouette_score(X_scaled, labels)
            except Exception:
                pass

        # 세그먼트 경계 계산
        boundaries = {}
        for col in available_cols:
            col_boundaries = []
            for seg_id in range(n_segments):
                seg_mask = labels == seg_id
                seg_values = df.loc[seg_mask, col]
                if len(seg_values) > 0:
                    col_boundaries.append((float(seg_values.min()), float(seg_values.max())))
                else:
                    col_boundaries.append((0.0, 0.0))
            boundaries[col] = col_boundaries

        # 세그먼트 통계
        segment_stats = []
        for seg_id in range(n_segments):
            seg_mask = labels == seg_id
            seg_df = df[seg_mask]

            stats = {
                'segment_id': seg_id,
                'n_trades': int(seg_mask.sum()),
                'ratio': round(seg_mask.sum() / len(df) * 100, 1),
            }

            if '수익금' in seg_df.columns and len(seg_df) > 0:
                stats['total_profit'] = int(seg_df['수익금'].sum())
                stats['mean_profit'] = int(seg_df['수익금'].mean())
                stats['win_rate'] = round((seg_df['수익금'] > 0).mean() * 100, 1)

            for col in available_cols:
                if col in seg_df.columns and len(seg_df) > 0:
                    stats[f'{col}_min'] = float(seg_df[col].min())
                    stats[f'{col}_max'] = float(seg_df[col].max())
                    stats[f'{col}_mean'] = float(seg_df[col].mean())

            segment_stats.append(stats)

        return AdaptiveSegmentResult(
            n_segments=n_segments,
            segment_labels=labels,
            segment_boundaries=boundaries,
            segment_stats=segment_stats,
            clustering_method=method,
            silhouette_score=sil_score,
        )

    except Exception as e:
        return AdaptiveSegmentResult(
            n_segments=0,
            segment_labels=np.array([]),
            segment_boundaries={},
            segment_stats=[],
            clustering_method=method,
            error=str(e)
        )


def compare_segment_methods(
    df: pd.DataFrame,
    methods: List[str] = None,
    n_segments_list: List[int] = None,
) -> List[Dict]:
    """
    여러 세그먼트 방법을 비교합니다.

    Args:
        df: 데이터프레임
        methods: 비교할 방법 리스트
        n_segments_list: 비교할 세그먼트 수 리스트

    Returns:
        비교 결과 리스트
    """
    if methods is None:
        methods = ['kmeans', 'quantile']
    if n_segments_list is None:
        n_segments_list = [3, 4, 5]

    results = []

    for method in methods:
        for n_seg in n_segments_list:
            result = discover_adaptive_segments(df, n_segments=n_seg, method=method)

            if result.error:
                continue

            # 세그먼트별 수익성 분산 계산 (높을수록 세그먼트가 수익성을 잘 분리)
            profits_by_seg = []
            for stat in result.segment_stats:
                if 'mean_profit' in stat:
                    profits_by_seg.append(stat['mean_profit'])

            profit_variance = np.var(profits_by_seg) if profits_by_seg else 0

            results.append({
                'method': method,
                'n_segments': n_seg,
                'silhouette_score': result.silhouette_score,
                'profit_variance': round(profit_variance, 0),
                'segment_stats': result.segment_stats,
            })

    # 수익 분산 기준 정렬 (높을수록 좋음)
    results.sort(key=lambda x: x.get('profit_variance', 0), reverse=True)

    return results


# =============================================================================
# 유틸리티
# =============================================================================

def get_adaptive_segment_config(
    segment_result: AdaptiveSegmentResult,
) -> Dict:
    """
    적응형 세그먼트 결과를 기존 SegmentConfig 형식으로 변환합니다.
    """
    if not segment_result.segment_boundaries:
        return {}

    # 시가총액 경계 추출
    cap_boundaries = segment_result.segment_boundaries.get('시가총액', [])

    # 세그먼트 이름 생성
    segment_names = [f'seg_{i}' for i in range(segment_result.n_segments)]

    # SegmentConfig 형식으로 변환
    market_cap_ranges = {}
    for i, (bounds, name) in enumerate(zip(cap_boundaries, segment_names)):
        market_cap_ranges[name] = bounds

    return {
        'market_cap_ranges': market_cap_ranges,
        'n_segments': segment_result.n_segments,
        'method': segment_result.clustering_method,
        'silhouette_score': segment_result.silhouette_score,
    }
