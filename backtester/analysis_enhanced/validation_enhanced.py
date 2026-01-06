# -*- coding: utf-8 -*-
"""
Enhanced Validation Module

과적합 방지를 위한 교차 검증 기능을 제공합니다.
- Purged Walk-Forward Cross-Validation
- Out-of-Sample 성능 추정
- 필터 안정성 검증
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Generator
import numpy as np
import pandas as pd


# =============================================================================
# 설정
# =============================================================================

@dataclass
class PurgedWalkForwardConfig:
    """Purged Walk-Forward CV 설정"""
    n_splits: int = 5
    train_ratio: float = 0.6
    gap_ratio: float = 0.05  # 훈련/테스트 간 갭 (정보 누수 방지)
    min_trades_per_fold: int = 50
    date_column: str = '매수일자'


@dataclass
class FilterValidationResult:
    """필터 교차 검증 결과"""
    filter_name: str
    filter_expr: str
    
    # 훈련/테스트 성능
    train_improvements: List[float] = field(default_factory=list)
    test_improvements: List[float] = field(default_factory=list)
    train_exclusion_rates: List[float] = field(default_factory=list)
    test_exclusion_rates: List[float] = field(default_factory=list)
    
    # 집계 통계
    mean_train_improvement: float = 0.0
    mean_test_improvement: float = 0.0
    std_test_improvement: float = 0.0
    generalization_ratio: float = 0.0  # test / train 비율
    
    # 일관성
    positive_fold_ratio: float = 0.0  # 테스트에서 양수인 fold 비율
    is_robust: bool = False


# =============================================================================
# Purged Walk-Forward Cross-Validation
# =============================================================================

def purged_walk_forward_splits(
    df: pd.DataFrame,
    config: Optional[PurgedWalkForwardConfig] = None,
) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
    """
    Purged Walk-Forward 교차 검증 분할을 생성합니다.

    시계열 데이터에서 미래 정보 누수를 방지하기 위해:
    1. 훈련 데이터는 항상 테스트 데이터보다 과거
    2. 훈련과 테스트 사이에 'gap' 기간을 둠 (자기상관 방지)

    구조:
    |---Train---|--Gap--|---Test---|
    
    Args:
        df: 데이터프레임 (date_column 컬럼 필요)
        config: 설정

    Yields:
        (train_mask, test_mask) 튜플

    Example:
        >>> for train_mask, test_mask in purged_walk_forward_splits(df):
        ...     train_df = df[train_mask]
        ...     test_df = df[test_mask]
        ...     # 훈련 데이터로 필터 발견, 테스트 데이터로 검증
    """
    config = config or PurgedWalkForwardConfig()
    
    # 날짜 파싱
    if config.date_column not in df.columns:
        # 날짜 컬럼이 없으면 인덱스 기반 분할
        yield from _index_based_splits(df, config)
        return
    
    try:
        dates = pd.to_datetime(df[config.date_column].astype(str), format='%Y%m%d')
    except Exception:
        # 날짜 파싱 실패 시 인덱스 기반
        yield from _index_based_splits(df, config)
        return
    
    unique_dates = np.sort(dates.unique())
    n_dates = len(unique_dates)
    
    if n_dates < 20:
        # 날짜가 너무 적으면 인덱스 기반
        yield from _index_based_splits(df, config)
        return
    
    fold_size = n_dates // config.n_splits
    gap_size = max(1, int(fold_size * config.gap_ratio))
    
    for i in range(config.n_splits - 1):  # 마지막 fold는 테스트 불가
        # 훈련: 처음부터 현재 fold까지
        train_end_idx = (i + 1) * fold_size
        
        # 갭
        test_start_idx = train_end_idx + gap_size
        
        # 테스트: 갭 이후부터 다음 fold까지
        test_end_idx = min(n_dates, test_start_idx + fold_size)
        
        if test_start_idx >= n_dates or test_end_idx <= test_start_idx:
            continue
        
        train_dates = set(unique_dates[:train_end_idx])
        test_dates = set(unique_dates[test_start_idx:test_end_idx])
        
        train_mask = dates.isin(train_dates).values
        test_mask = dates.isin(test_dates).values
        
        # 최소 거래 수 확인
        if train_mask.sum() >= config.min_trades_per_fold and \
           test_mask.sum() >= config.min_trades_per_fold:
            yield train_mask, test_mask


def _index_based_splits(
    df: pd.DataFrame,
    config: PurgedWalkForwardConfig,
) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
    """
    인덱스 기반 분할 (날짜 정보가 없을 때)
    """
    n = len(df)
    fold_size = n // config.n_splits
    gap_size = max(1, int(fold_size * config.gap_ratio))
    
    for i in range(config.n_splits - 1):
        train_end = (i + 1) * fold_size
        test_start = train_end + gap_size
        test_end = min(n, test_start + fold_size)
        
        if test_start >= n:
            continue
        
        train_mask = np.zeros(n, dtype=bool)
        test_mask = np.zeros(n, dtype=bool)
        
        train_mask[:train_end] = True
        test_mask[test_start:test_end] = True
        
        if train_mask.sum() >= config.min_trades_per_fold and \
           test_mask.sum() >= config.min_trades_per_fold:
            yield train_mask, test_mask


# =============================================================================
# 필터 교차 검증
# =============================================================================

def validate_filter_with_cv(
    df: pd.DataFrame,
    filter_expr: str,
    filter_name: str = '',
    config: Optional[PurgedWalkForwardConfig] = None,
) -> FilterValidationResult:
    """
    단일 필터의 Out-of-Sample 성능을 교차 검증으로 평가합니다.

    각 fold에서:
    1. 훈련 데이터: 필터 효과 계산 (in-sample)
    2. 테스트 데이터: 동일 필터 적용하여 효과 계산 (out-of-sample)
    3. 일반화 비율 = OOS 개선 / IS 개선

    Args:
        df: 전체 데이터프레임
        filter_expr: 필터 조건식 (eval 가능)
        filter_name: 필터 이름
        config: CV 설정

    Returns:
        FilterValidationResult: 교차 검증 결과
    """
    config = config or PurgedWalkForwardConfig()
    result = FilterValidationResult(
        filter_name=filter_name,
        filter_expr=filter_expr,
    )
    
    if '수익금' not in df.columns:
        return result
    
    safe_globals = {"__builtins__": {}}
    safe_locals = {"df_tsg": df, "np": np, "pd": pd}
    
    for train_mask, test_mask in purged_walk_forward_splits(df, config):
        train_df = df[train_mask].copy()
        test_df = df[test_mask].copy()
        
        # 필터 마스크 계산 (각 subset에 대해)
        try:
            # 훈련 데이터에서 필터 적용
            train_locals = {"df_tsg": train_df, "np": np, "pd": pd}
            train_filter = eval(filter_expr, safe_globals, train_locals)
            if hasattr(train_filter, 'values'):
                train_filter = train_filter.values
            train_filter = np.asarray(train_filter, dtype=bool)
            
            # 테스트 데이터에서 필터 적용
            test_locals = {"df_tsg": test_df, "np": np, "pd": pd}
            test_filter = eval(filter_expr, safe_globals, test_locals)
            if hasattr(test_filter, 'values'):
                test_filter = test_filter.values
            test_filter = np.asarray(test_filter, dtype=bool)
        except Exception:
            continue
        
        # 훈련 개선 계산
        train_profit = train_df['수익금'].values.astype(float)
        train_filtered_profit = train_profit[train_filter].sum()
        train_improvement = -train_filtered_profit  # 제외된 손실 = 개선
        train_exclusion_rate = train_filter.sum() / max(1, len(train_df))
        
        # 테스트 개선 계산
        test_profit = test_df['수익금'].values.astype(float)
        test_filtered_profit = test_profit[test_filter].sum()
        test_improvement = -test_filtered_profit
        test_exclusion_rate = test_filter.sum() / max(1, len(test_df))
        
        result.train_improvements.append(train_improvement)
        result.test_improvements.append(test_improvement)
        result.train_exclusion_rates.append(train_exclusion_rate)
        result.test_exclusion_rates.append(test_exclusion_rate)
    
    # 집계 통계 계산
    if result.train_improvements:
        result.mean_train_improvement = float(np.mean(result.train_improvements))
        result.mean_test_improvement = float(np.mean(result.test_improvements))
        result.std_test_improvement = float(np.std(result.test_improvements))
        
        if result.mean_train_improvement > 0:
            result.generalization_ratio = result.mean_test_improvement / result.mean_train_improvement
        
        # 테스트에서 양수인 fold 비율
        positive_folds = sum(1 for x in result.test_improvements if x > 0)
        result.positive_fold_ratio = positive_folds / len(result.test_improvements)
        
        # 견고성 판정: OOS에서도 60%+ fold에서 양수 && 일반화 비율 50%+
        result.is_robust = (
            result.positive_fold_ratio >= 0.6 and
            result.generalization_ratio >= 0.5
        )
    
    return result


def validate_filters_batch(
    df: pd.DataFrame,
    filter_results: List[Dict],
    config: Optional[PurgedWalkForwardConfig] = None,
    top_n: int = 20,
) -> List[Dict]:
    """
    여러 필터의 Out-of-Sample 성능을 일괄 검증합니다.

    Args:
        df: 전체 데이터프레임
        filter_results: 필터 분석 결과 리스트 (AnalyzeFilterEffectsEnhanced 출력)
        config: CV 설정
        top_n: 상위 N개 필터만 검증

    Returns:
        OOS 검증 결과가 추가된 필터 리스트
    """
    config = config or PurgedWalkForwardConfig()
    
    # 상위 N개만 검증 (계산량 제한)
    candidates = [f for f in filter_results if f.get('수익개선금액', 0) > 0]
    candidates = candidates[:top_n]
    
    for f in candidates:
        expr = f.get('조건식')
        name = f.get('필터명', '')
        
        if not expr:
            continue
        
        cv_result = validate_filter_with_cv(df, expr, name, config)
        
        # 결과 추가
        f['OOS_평균개선'] = int(cv_result.mean_test_improvement)
        f['OOS_표준편차'] = int(cv_result.std_test_improvement)
        f['일반화비율'] = round(cv_result.generalization_ratio * 100, 1)
        f['양수fold비율'] = round(cv_result.positive_fold_ratio * 100, 1)
        f['OOS_견고'] = '예' if cv_result.is_robust else '아니오'
    
    return filter_results


# =============================================================================
# 앙상블 검증 (Bootstrap)
# =============================================================================

def bootstrap_filter_validation(
    df: pd.DataFrame,
    filter_expr: str,
    n_bootstrap: int = 100,
    sample_ratio: float = 0.8,
) -> Dict:
    """
    부트스트랩으로 필터 효과의 신뢰구간을 추정합니다.

    Args:
        df: 데이터프레임
        filter_expr: 필터 조건식
        n_bootstrap: 부트스트랩 반복 수
        sample_ratio: 각 샘플의 크기 비율

    Returns:
        dict: 부트스트랩 결과
            - improvements: 각 샘플의 개선값 리스트
            - mean: 평균 개선
            - std: 표준편차
            - ci_lower: 95% 신뢰구간 하한
            - ci_upper: 95% 신뢰구간 상한
            - stability: 양수 비율
    """
    if '수익금' not in df.columns:
        return {}
    
    n = len(df)
    sample_size = int(n * sample_ratio)
    
    safe_globals = {"__builtins__": {}}
    improvements = []
    
    for _ in range(n_bootstrap):
        # 부트스트랩 샘플 (with replacement)
        idx = np.random.choice(n, size=sample_size, replace=True)
        sample_df = df.iloc[idx].copy()
        
        try:
            sample_locals = {"df_tsg": sample_df, "np": np, "pd": pd}
            filter_mask = eval(filter_expr, safe_globals, sample_locals)
            if hasattr(filter_mask, 'values'):
                filter_mask = filter_mask.values
            filter_mask = np.asarray(filter_mask, dtype=bool)
            
            profit = sample_df['수익금'].values.astype(float)
            improvement = -profit[filter_mask].sum()
            improvements.append(improvement)
        except Exception:
            continue
    
    if not improvements:
        return {}
    
    improvements = np.array(improvements)
    
    return {
        'improvements': improvements.tolist(),
        'mean': float(np.mean(improvements)),
        'std': float(np.std(improvements)),
        'ci_lower': float(np.percentile(improvements, 2.5)),
        'ci_upper': float(np.percentile(improvements, 97.5)),
        'stability': float((improvements > 0).mean()),
    }


# =============================================================================
# 유틸리티
# =============================================================================

def get_cv_summary(filter_results: List[Dict]) -> Dict:
    """
    교차 검증 결과 요약을 반환합니다.

    Args:
        filter_results: OOS 검증이 적용된 필터 결과 리스트

    Returns:
        dict: 요약 정보
    """
    validated = [f for f in filter_results if 'OOS_평균개선' in f]
    robust = [f for f in validated if f.get('OOS_견고') == '예']
    
    if not validated:
        return {'validated_count': 0}
    
    return {
        'validated_count': len(validated),
        'robust_count': len(robust),
        'robust_ratio': round(len(robust) / len(validated) * 100, 1),
        'avg_generalization_ratio': round(
            np.mean([f.get('일반화비율', 0) for f in validated]), 1
        ),
        'top_robust_filters': [
            f.get('필터명') for f in sorted(
                robust, 
                key=lambda x: x.get('OOS_평균개선', 0), 
                reverse=True
            )[:5]
        ],
    }
