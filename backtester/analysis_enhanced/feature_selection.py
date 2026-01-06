# -*- coding: utf-8 -*-
"""
Feature Selection Module

필터 선택을 위한 고급 기능을 제공합니다.
- 상호정보(Mutual Information) 기반 사전 선택
- 상관관계 기반 다양성 선택
- 중복 필터 제거
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


# =============================================================================
# 상호정보(Mutual Information) 기반 필터 선택
# =============================================================================

def calculate_filter_mutual_information(
    df: pd.DataFrame,
    filter_masks: List[np.ndarray],
    filter_names: Optional[List[str]] = None,
) -> List[Dict]:
    """
    각 필터 마스크와 손실 결과 간의 상호정보(MI)를 계산합니다.

    상호정보가 높을수록 해당 필터가 손실을 예측하는 데 유용한 정보를 담고 있습니다.
    MI가 낮은 필터는 "노이즈"일 가능성이 높아 제외할 수 있습니다.

    Args:
        df: 데이터프레임 (수익금 컬럼 필요)
        filter_masks: 필터 마스크 리스트 (True = 제외 대상)
        filter_names: 필터 이름 리스트 (선택)

    Returns:
        list: 각 필터의 MI 결과
            - filter_idx: 필터 인덱스
            - filter_name: 필터 이름
            - mi_score: 상호정보 점수
            - is_informative: MI > threshold 여부
    """
    if '수익금' not in df.columns or not filter_masks:
        return []
    
    # 손실 여부 (binary target)
    y = (df['수익금'] <= 0).values.astype(int)
    n_samples = len(y)
    
    results = []
    
    for i, mask in enumerate(filter_masks):
        if mask is None:
            continue
        
        mask = np.asarray(mask, dtype=bool)
        if len(mask) != n_samples:
            continue
        
        # 상호정보 계산 (이산 변수)
        mi = _mutual_information_discrete(mask.astype(int), y)
        
        name = filter_names[i] if filter_names and i < len(filter_names) else f'filter_{i}'
        
        results.append({
            'filter_idx': i,
            'filter_name': name,
            'mi_score': round(mi, 6),
            'is_informative': mi >= 0.01,  # 임계값
        })
    
    # MI 점수 내림차순 정렬
    results.sort(key=lambda x: x['mi_score'], reverse=True)
    
    return results


def _mutual_information_discrete(x: np.ndarray, y: np.ndarray) -> float:
    """
    두 이산 변수 간의 상호정보를 계산합니다.

    MI(X, Y) = H(X) + H(Y) - H(X, Y)
    
    여기서 H는 엔트로피입니다.
    """
    n = len(x)
    if n == 0:
        return 0.0
    
    # 확률 분포 계산
    def entropy(arr):
        _, counts = np.unique(arr, return_counts=True)
        probs = counts / n
        return -np.sum(probs * np.log2(probs + 1e-10))
    
    # 결합 엔트로피
    xy = np.stack([x, y], axis=1)
    _, joint_counts = np.unique(xy, axis=0, return_counts=True)
    joint_probs = joint_counts / n
    h_xy = -np.sum(joint_probs * np.log2(joint_probs + 1e-10))
    
    # MI = H(X) + H(Y) - H(X,Y)
    mi = entropy(x) + entropy(y) - h_xy
    
    return max(0.0, mi)  # MI는 항상 >= 0


def filter_by_mutual_information(
    filter_results: List[Dict],
    df: pd.DataFrame,
    mi_threshold: float = 0.01,
) -> List[Dict]:
    """
    상호정보 기준으로 노이즈 필터를 제거합니다.

    Args:
        filter_results: 필터 분석 결과 리스트
        df: 데이터프레임
        mi_threshold: MI 임계값 (이 값 미만인 필터 제거)

    Returns:
        MI 기준 통과한 필터만 포함된 리스트
    """
    if '수익금' not in df.columns or not filter_results:
        return filter_results
    
    # 필터 마스크 생성
    masks = []
    safe_globals = {"__builtins__": {}}
    safe_locals = {"df_tsg": df, "np": np, "pd": pd}
    
    for f in filter_results:
        expr = f.get('조건식')
        if not expr:
            masks.append(None)
            continue
        
        try:
            cond = eval(expr, safe_globals, safe_locals)
            if hasattr(cond, 'values'):
                cond = cond.values
            masks.append(np.asarray(cond, dtype=bool))
        except Exception:
            masks.append(None)
    
    # MI 계산
    mi_results = calculate_filter_mutual_information(
        df, 
        masks,
        [f.get('필터명', '') for f in filter_results]
    )
    
    # MI 점수를 원본 결과에 추가
    mi_map = {r['filter_idx']: r for r in mi_results}
    
    filtered_results = []
    for i, f in enumerate(filter_results):
        mi_info = mi_map.get(i, {})
        f['MI점수'] = mi_info.get('mi_score', 0)
        f['정보성'] = '예' if mi_info.get('is_informative', False) else '아니오'
        
        # MI 임계값 통과한 필터만 포함
        if mi_info.get('mi_score', 0) >= mi_threshold:
            filtered_results.append(f)
    
    return filtered_results


# =============================================================================
# 상관관계 기반 다양성 선택
# =============================================================================

def calculate_filter_correlation_matrix(
    filter_masks: List[np.ndarray],
) -> np.ndarray:
    """
    필터 마스크 간의 상관관계 행렬을 계산합니다.

    Jaccard 유사도를 사용합니다:
    J(A, B) = |A ∩ B| / |A ∪ B|

    상관관계가 높은 필터는 비슷한 거래를 제외하므로,
    둘 중 하나만 선택해도 됩니다.

    Args:
        filter_masks: 필터 마스크 리스트

    Returns:
        np.ndarray: 상관관계 행렬 (n x n)
    """
    n = len(filter_masks)
    if n == 0:
        return np.array([])
    
    corr_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i, n):
            if filter_masks[i] is None or filter_masks[j] is None:
                corr_matrix[i, j] = corr_matrix[j, i] = 0
                continue
            
            mask_i = np.asarray(filter_masks[i], dtype=bool)
            mask_j = np.asarray(filter_masks[j], dtype=bool)
            
            intersection = np.sum(mask_i & mask_j)
            union = np.sum(mask_i | mask_j)
            
            if union > 0:
                jaccard = intersection / union
            else:
                jaccard = 0
            
            corr_matrix[i, j] = corr_matrix[j, i] = jaccard
    
    return corr_matrix


def greedy_select_diverse_filters(
    filter_results: List[Dict],
    df: pd.DataFrame,
    max_filters: int = 10,
    diversity_weight: float = 0.3,
    min_improvement: float = 0,
) -> List[Dict]:
    """
    다양성을 고려한 그리디 필터 선택을 수행합니다.

    기존 그리디 선택은 개별 개선이 큰 필터를 순차적으로 선택하지만,
    이 방식은 상관관계가 높은 필터를 선택할 때 페널티를 부여합니다.

    Score = improvement * (1 - diversity_weight * max_correlation_with_selected)

    Args:
        filter_results: 필터 분석 결과 리스트
        df: 데이터프레임
        max_filters: 최대 선택 필터 수
        diversity_weight: 다양성 가중치 (0~1, 높을수록 다양성 중요)
        min_improvement: 최소 개선 금액

    Returns:
        다양성이 고려된 선택 필터 리스트
    """
    if not filter_results:
        return []
    
    # 개선 효과가 있는 필터만 후보로
    candidates = [f for f in filter_results if f.get('수익개선금액', 0) > min_improvement]
    
    if not candidates:
        return []
    
    # 필터 마스크 생성
    safe_globals = {"__builtins__": {}}
    safe_locals = {"df_tsg": df, "np": np, "pd": pd}
    
    masks = []
    for f in candidates:
        expr = f.get('조건식')
        if not expr:
            masks.append(None)
            continue
        
        try:
            cond = eval(expr, safe_globals, safe_locals)
            if hasattr(cond, 'values'):
                cond = cond.values
            masks.append(np.asarray(cond, dtype=bool))
        except Exception:
            masks.append(None)
    
    # 상관관계 행렬 계산
    corr_matrix = calculate_filter_correlation_matrix(masks)
    
    # 그리디 선택 with 다양성 페널티
    selected_indices = []
    selected = []
    
    for _ in range(min(max_filters, len(candidates))):
        best_score = -float('inf')
        best_idx = None
        
        for i, f in enumerate(candidates):
            if i in selected_indices:
                continue
            
            improvement = f.get('수익개선금액', 0)
            
            # 다양성 페널티 계산
            if selected_indices:
                max_corr = max(corr_matrix[i, j] for j in selected_indices)
            else:
                max_corr = 0
            
            # 점수 = 개선 * (1 - 다양성가중치 * 최대상관관계)
            score = improvement * (1 - diversity_weight * max_corr)
            
            if score > best_score:
                best_score = score
                best_idx = i
        
        if best_idx is not None:
            candidates[best_idx]['다양성점수'] = round(best_score, 0)
            candidates[best_idx]['최대상관관계'] = round(
                max(corr_matrix[best_idx, j] for j in selected_indices) if selected_indices else 0, 
                3
            )
            selected.append(candidates[best_idx])
            selected_indices.append(best_idx)
    
    return selected


def remove_redundant_filters(
    filter_results: List[Dict],
    df: pd.DataFrame,
    correlation_threshold: float = 0.8,
) -> List[Dict]:
    """
    상관관계가 높은 중복 필터를 제거합니다.

    두 필터의 Jaccard 유사도가 threshold 이상이면,
    개선 효과가 작은 필터를 제거합니다.

    Args:
        filter_results: 필터 분석 결과 리스트
        df: 데이터프레임
        correlation_threshold: 중복 판정 임계값 (0~1)

    Returns:
        중복이 제거된 필터 리스트
    """
    if not filter_results:
        return []
    
    # 필터 마스크 생성
    safe_globals = {"__builtins__": {}}
    safe_locals = {"df_tsg": df, "np": np, "pd": pd}
    
    masks = []
    for f in filter_results:
        expr = f.get('조건식')
        if not expr:
            masks.append(None)
            continue
        
        try:
            cond = eval(expr, safe_globals, safe_locals)
            if hasattr(cond, 'values'):
                cond = cond.values
            masks.append(np.asarray(cond, dtype=bool))
        except Exception:
            masks.append(None)
    
    # 상관관계 행렬 계산
    corr_matrix = calculate_filter_correlation_matrix(masks)
    
    # 개선 효과 순으로 정렬 (높은 것이 우선)
    sorted_indices = sorted(
        range(len(filter_results)),
        key=lambda i: filter_results[i].get('수익개선금액', 0),
        reverse=True
    )
    
    # 중복 제거
    kept_indices = set()
    removed_indices = set()
    
    for i in sorted_indices:
        if i in removed_indices:
            continue
        
        kept_indices.add(i)
        
        # i와 높은 상관관계를 가진 필터 제거
        for j in sorted_indices:
            if j == i or j in kept_indices or j in removed_indices:
                continue
            
            if corr_matrix[i, j] >= correlation_threshold:
                removed_indices.add(j)
                # 제거 이유 기록
                filter_results[j]['제거이유'] = f"'{filter_results[i].get('필터명', '')}' 와 중복 (상관계수 {corr_matrix[i, j]:.2f})"
    
    # 유지된 필터만 반환
    result = [filter_results[i] for i in sorted(kept_indices)]
    
    return result


# =============================================================================
# 유틸리티
# =============================================================================

def get_feature_selection_summary(
    original_count: int,
    mi_filtered_count: int,
    diversity_selected_count: int,
    final_count: int,
) -> Dict:
    """
    특성 선택 결과 요약을 반환합니다.
    """
    return {
        'original_filters': original_count,
        'after_mi_filter': mi_filtered_count,
        'after_diversity_select': diversity_selected_count,
        'final_count': final_count,
        'reduction_rate': round((1 - final_count / max(1, original_count)) * 100, 1),
    }
