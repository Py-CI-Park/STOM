# -*- coding: utf-8 -*-
"""
Ensemble Filter Module

Bootstrap 앙상블을 통한 견고한 필터 선택 기능을 제공합니다.
- Bootstrap 기반 필터 안정성 검증
- 투표 기반 필터 선택
- 과적합 방지를 위한 다중 샘플 검증
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


# =============================================================================
# 설정
# =============================================================================

@dataclass
class EnsembleConfig:
    """앙상블 필터 설정"""
    n_bootstrap: int = 10  # 부트스트랩 반복 수
    sample_ratio: float = 0.8  # 각 샘플 크기 비율
    vote_threshold: float = 0.6  # 선택 임계값 (60%+ 샘플에서 선택된 필터만)
    min_improvement: float = 0  # 최소 개선 금액
    top_n_per_sample: int = 10  # 각 샘플에서 상위 N개 필터만 선택


@dataclass
class EnsembleFilterResult:
    """앙상블 필터 결과"""
    filter_name: str
    filter_expr: str
    filter_code: str
    
    # 투표 결과
    vote_count: int = 0
    vote_ratio: float = 0.0
    
    # 부트스트랩 통계
    mean_improvement: float = 0.0
    std_improvement: float = 0.0
    min_improvement: float = 0.0
    max_improvement: float = 0.0
    
    # 일관성
    positive_sample_ratio: float = 0.0  # 양수 개선인 샘플 비율
    
    # 판정
    is_stable: bool = False


# =============================================================================
# Bootstrap 앙상블 필터 선택
# =============================================================================

def ensemble_filter_selection(
    df: pd.DataFrame,
    analyze_func,
    config: Optional[EnsembleConfig] = None,
) -> Dict:
    """
    Bootstrap 앙상블을 통해 견고한 필터를 선택합니다.

    과정:
    1. N개의 부트스트랩 샘플 생성
    2. 각 샘플에서 필터 분석 실행
    3. 각 샘플에서 상위 필터 선택
    4. 투표: vote_threshold 이상의 샘플에서 선택된 필터만 최종 선택

    이 방식은 특정 데이터 부분집합에서만 좋은 성능을 보이는
    "우연히 좋은" 필터를 걸러내고, 데이터 전반에서 일관되게
    효과가 있는 필터만 선택합니다.

    Args:
        df: 전체 데이터프레임
        analyze_func: 필터 분석 함수 (df -> list of filter results)
        config: 앙상블 설정

    Returns:
        dict: 앙상블 결과
            - stable_filters: 안정적인 필터 리스트
            - vote_counts: 각 필터의 투표 수
            - bootstrap_stats: 각 필터의 부트스트랩 통계
    """
    config = config or EnsembleConfig()
    
    if '수익금' not in df.columns:
        return {'stable_filters': [], 'error': 'no_profit_column'}
    
    n = len(df)
    sample_size = int(n * config.sample_ratio)
    
    # 각 샘플에서 선택된 필터 수집
    all_selections = []  # List of (filter_key, improvement)
    filter_improvements = {}  # filter_key -> list of improvements
    filter_info = {}  # filter_key -> filter dict (마지막 것 저장)
    
    for i in range(config.n_bootstrap):
        # 부트스트랩 샘플 생성 (with replacement)
        idx = np.random.choice(n, size=sample_size, replace=True)
        sample_df = df.iloc[idx].copy().reset_index(drop=True)
        
        try:
            # 필터 분석 실행
            sample_results = analyze_func(sample_df)
            
            if not sample_results:
                continue
            
            # 상위 N개 필터 선택 (개선 효과 양수인 것만)
            positive_filters = [
                f for f in sample_results 
                if f.get('수익개선금액', 0) > config.min_improvement
            ]
            top_filters = positive_filters[:config.top_n_per_sample]
            
            # 선택된 필터 기록
            for f in top_filters:
                filter_key = (f.get('필터명', ''), f.get('적용코드', ''))
                improvement = f.get('수익개선금액', 0)
                
                all_selections.append(filter_key)
                
                if filter_key not in filter_improvements:
                    filter_improvements[filter_key] = []
                filter_improvements[filter_key].append(improvement)
                
                filter_info[filter_key] = f
                
        except Exception:
            continue
    
    if not all_selections:
        return {'stable_filters': [], 'error': 'no_filters_found'}
    
    # 투표 집계
    vote_counts = Counter(all_selections)
    
    # 결과 생성
    results = []
    for filter_key, count in vote_counts.items():
        vote_ratio = count / config.n_bootstrap
        improvements = filter_improvements.get(filter_key, [])
        info = filter_info.get(filter_key, {})
        
        if not improvements:
            continue
        
        imp_arr = np.array(improvements)
        positive_ratio = (imp_arr > 0).mean()
        
        result = EnsembleFilterResult(
            filter_name=filter_key[0],
            filter_expr=info.get('조건식', ''),
            filter_code=filter_key[1],
            vote_count=count,
            vote_ratio=round(vote_ratio, 3),
            mean_improvement=float(np.mean(imp_arr)),
            std_improvement=float(np.std(imp_arr)),
            min_improvement=float(np.min(imp_arr)),
            max_improvement=float(np.max(imp_arr)),
            positive_sample_ratio=round(positive_ratio, 3),
            is_stable=vote_ratio >= config.vote_threshold and positive_ratio >= 0.8,
        )
        results.append(result)
    
    # 투표 수 내림차순 정렬
    results.sort(key=lambda x: (x.vote_count, x.mean_improvement), reverse=True)
    
    # 안정적인 필터만 추출
    stable_filters = [r for r in results if r.is_stable]
    
    return {
        'stable_filters': stable_filters,
        'all_results': results,
        'vote_counts': dict(vote_counts),
        'config': {
            'n_bootstrap': config.n_bootstrap,
            'sample_ratio': config.sample_ratio,
            'vote_threshold': config.vote_threshold,
        },
        'stats': {
            'total_unique_filters': len(results),
            'stable_filter_count': len(stable_filters),
            'stability_ratio': round(len(stable_filters) / max(1, len(results)) * 100, 1),
        },
    }


def run_ensemble_filter_analysis(
    df: pd.DataFrame,
    config: Optional[EnsembleConfig] = None,
) -> Dict:
    """
    기본 필터 분석 함수를 사용하여 앙상블 분석을 실행합니다.

    Args:
        df: 데이터프레임
        config: 앙상블 설정

    Returns:
        앙상블 결과
    """
    from .filters import AnalyzeFilterEffectsEnhanced
    
    def analyze_sample(sample_df):
        return AnalyzeFilterEffectsEnhanced(
            sample_df,
            allow_ml_filters=True,
            correction_method='none',  # 샘플별로는 보정하지 않음
        )
    
    return ensemble_filter_selection(df, analyze_sample, config)


# =============================================================================
# 유틸리티
# =============================================================================

def convert_ensemble_results_to_filter_results(
    ensemble_result: Dict,
) -> List[Dict]:
    """
    앙상블 결과를 표준 필터 결과 형식으로 변환합니다.

    Args:
        ensemble_result: ensemble_filter_selection 출력

    Returns:
        표준 필터 결과 리스트 (AnalyzeFilterEffectsEnhanced 출력과 호환)
    """
    stable_filters = ensemble_result.get('stable_filters', [])
    
    results = []
    for ef in stable_filters:
        results.append({
            '필터명': ef.filter_name,
            '조건식': ef.filter_expr,
            '적용코드': ef.filter_code,
            '수익개선금액': int(ef.mean_improvement),
            '개선표준편차': int(ef.std_improvement),
            '투표수': ef.vote_count,
            '투표비율': round(ef.vote_ratio * 100, 1),
            '양수비율': round(ef.positive_sample_ratio * 100, 1),
            '안정성': '예' if ef.is_stable else '아니오',
            '선택방법': 'bootstrap_ensemble',
        })
    
    return results


def get_ensemble_summary(ensemble_result: Dict) -> Dict:
    """
    앙상블 결과 요약을 반환합니다.
    """
    stats = ensemble_result.get('stats', {})
    config = ensemble_result.get('config', {})
    stable_filters = ensemble_result.get('stable_filters', [])
    
    summary = {
        'n_bootstrap': config.get('n_bootstrap', 0),
        'vote_threshold': config.get('vote_threshold', 0),
        'total_filters_found': stats.get('total_unique_filters', 0),
        'stable_filters_count': stats.get('stable_filter_count', 0),
        'stability_ratio': stats.get('stability_ratio', 0),
    }
    
    if stable_filters:
        summary['top_stable_filters'] = [
            {
                'name': f.filter_name,
                'votes': f.vote_count,
                'mean_improvement': int(f.mean_improvement),
            }
            for f in stable_filters[:5]
        ]
    
    return summary


# =============================================================================
# 고급 앙상블: 시간 기반 분할
# =============================================================================

def time_based_ensemble_validation(
    df: pd.DataFrame,
    analyze_func,
    date_column: str = '매수일자',
    n_time_splits: int = 5,
    top_n: int = 10,
) -> Dict:
    """
    시간 기반 분할로 필터 안정성을 검증합니다.

    부트스트랩과 달리, 시간 순서대로 데이터를 분할하여
    각 기간에서 일관되게 효과가 있는 필터를 찾습니다.

    Args:
        df: 데이터프레임
        analyze_func: 필터 분석 함수
        date_column: 날짜 컬럼
        n_time_splits: 시간 분할 수
        top_n: 각 기간에서 상위 N개 필터

    Returns:
        시간 기반 검증 결과
    """
    if date_column not in df.columns:
        # 날짜 컬럼이 없으면 인덱스 기반 분할
        split_indices = np.array_split(np.arange(len(df)), n_time_splits)
        time_dfs = [df.iloc[idx].copy() for idx in split_indices]
    else:
        try:
            dates = pd.to_datetime(df[date_column].astype(str), format='%Y%m%d')
            unique_dates = np.sort(dates.unique())
            date_splits = np.array_split(unique_dates, n_time_splits)
            time_dfs = []
            for date_group in date_splits:
                mask = dates.isin(date_group)
                time_dfs.append(df[mask].copy())
        except Exception:
            split_indices = np.array_split(np.arange(len(df)), n_time_splits)
            time_dfs = [df.iloc[idx].copy() for idx in split_indices]
    
    # 각 기간에서 필터 분석
    period_selections = []
    filter_by_period = {}
    
    for i, period_df in enumerate(time_dfs):
        if len(period_df) < 20:
            continue
        
        try:
            results = analyze_func(period_df)
            positive = [f for f in results if f.get('수익개선금액', 0) > 0]
            top = positive[:top_n]
            
            for f in top:
                key = (f.get('필터명', ''), f.get('적용코드', ''))
                period_selections.append(key)
                
                if key not in filter_by_period:
                    filter_by_period[key] = {
                        'periods': [],
                        'improvements': [],
                        'info': f,
                    }
                filter_by_period[key]['periods'].append(i)
                filter_by_period[key]['improvements'].append(f.get('수익개선금액', 0))
                
        except Exception:
            continue
    
    # 결과 집계
    results = []
    for key, data in filter_by_period.items():
        n_periods = len(data['periods'])
        coverage = n_periods / n_time_splits
        improvements = data['improvements']
        
        results.append({
            '필터명': key[0],
            '적용코드': key[1],
            '기간수': n_periods,
            '기간커버리지': round(coverage * 100, 1),
            '평균개선': int(np.mean(improvements)),
            '개선표준편차': int(np.std(improvements)),
            '최소개선': int(np.min(improvements)),
            '시간안정': '예' if coverage >= 0.6 and min(improvements) > 0 else '아니오',
        })
    
    results.sort(key=lambda x: (x['기간수'], x['평균개선']), reverse=True)
    
    return {
        'time_stable_filters': [r for r in results if r['시간안정'] == '예'],
        'all_results': results,
        'n_time_splits': n_time_splits,
        'periods_analyzed': len(time_dfs),
    }
