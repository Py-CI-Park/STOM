# -*- coding: utf-8 -*-
"""
Genetic Algorithm Filter Optimizer

유전 알고리즘을 사용하여 세그먼트별 최적 필터 조합을 탐색합니다.
Beam Search 대비 10배 이상 넓은 탐색 공간을 커버합니다.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from .combination_optimizer import apply_filter_mask


# =============================================================================
# 설정
# =============================================================================

@dataclass
class GAConfig:
    """유전 알고리즘 설정"""
    population_size: int = 100  # 모집단 크기
    generations: int = 50  # 세대 수
    mutation_rate: float = 0.1  # 돌연변이 확률
    crossover_rate: float = 0.7  # 교차 확률
    elite_size: int = 10  # 엘리트 보존 크기
    tournament_size: int = 5  # 토너먼트 선택 크기
    max_filters_per_segment: int = 3  # 세그먼트당 최대 필터 수
    max_exclusion_ratio: float = 0.9  # 최대 제외 비율
    exclusion_penalty_threshold: float = 0.5  # 페널티 적용 시작 제외 비율


@dataclass
class GAResult:
    """유전 알고리즘 결과"""
    best_chromosome: Dict[str, List[int]]
    best_fitness: float
    best_improvement: float
    best_exclusion_ratio: float
    generations_run: int
    fitness_history: List[float] = field(default_factory=list)
    
    # 세그먼트별 상세
    segment_details: Dict[str, Dict] = field(default_factory=dict)


# =============================================================================
# 유전 알고리즘 최적화기
# =============================================================================

class GeneticFilterOptimizer:
    """
    유전 알고리즘을 사용한 필터 조합 최적화.

    Chromosome: 각 세그먼트에서 선택된 필터 인덱스 리스트
    Fitness: 총 개선금액 - 제외 페널티

    Example:
        >>> optimizer = GeneticFilterOptimizer(segments, candidates_by_segment)
        >>> result = optimizer.optimize()
        >>> print(f"Best improvement: {result.best_improvement:,}원")
    """

    def __init__(
        self,
        segments: Dict[str, pd.DataFrame],
        candidates_by_segment: Dict[str, List[dict]],
        config: Optional[GAConfig] = None,
    ):
        """
        Args:
            segments: 세그먼트별 데이터프레임 {seg_id: df}
            candidates_by_segment: 세그먼트별 필터 후보 {seg_id: [filter_dict, ...]}
            config: GA 설정
        """
        self.segments = segments
        self.candidates = candidates_by_segment
        self.config = config or GAConfig()
        
        # 전체 거래 수 계산
        self.total_trades = sum(len(df) for df in segments.values())
        
        # 캐싱을 위한 마스크 사전 계산
        self._masks_cache: Dict[str, List[np.ndarray]] = {}
        self._profit_cache: Dict[str, np.ndarray] = {}
        self._precompute_masks()

    def _precompute_masks(self):
        """필터 마스크를 사전 계산하여 캐싱"""
        for seg_id, seg_df in self.segments.items():
            if seg_df.empty or '수익금' not in seg_df.columns:
                self._masks_cache[seg_id] = []
                self._profit_cache[seg_id] = np.array([])
                continue
            
            self._profit_cache[seg_id] = seg_df['수익금'].values.astype(float)
            
            cands = self.candidates.get(seg_id, [])
            masks = []
            for cand in cands:
                mask = apply_filter_mask(seg_df, cand)
                masks.append(mask)
            self._masks_cache[seg_id] = masks

    def _create_random_chromosome(self) -> Dict[str, List[int]]:
        """무작위 염색체 생성"""
        chromosome = {}
        for seg_id in self.segments.keys():
            cands = self.candidates.get(seg_id, [])
            if not cands:
                chromosome[seg_id] = []
                continue
            
            n_select = random.randint(0, min(len(cands), self.config.max_filters_per_segment))
            if n_select > 0:
                chromosome[seg_id] = random.sample(range(len(cands)), n_select)
            else:
                chromosome[seg_id] = []
        
        return chromosome

    def _fitness(self, chromosome: Dict[str, List[int]]) -> Tuple[float, float, float]:
        """
        적합도 계산.

        Returns:
            (fitness, improvement, exclusion_ratio)
        """
        total_improvement = 0.0
        total_excluded = 0
        
        for seg_id, selected_indices in chromosome.items():
            masks = self._masks_cache.get(seg_id, [])
            profit = self._profit_cache.get(seg_id)
            
            if profit is None or len(profit) == 0:
                continue
            
            seg_trades = len(profit)
            
            if not selected_indices:
                # 필터 없음: 개선 0
                continue
            
            # 선택된 필터 마스크 결합 (AND: 모든 필터 통과해야 유지)
            combined_mask = np.ones(seg_trades, dtype=bool)
            for idx in selected_indices:
                if idx < len(masks):
                    combined_mask &= masks[idx]
            
            # 개선 계산
            remaining_profit = profit[combined_mask].sum()
            original_profit = profit.sum()
            improvement = remaining_profit - original_profit
            
            total_improvement += improvement
            total_excluded += (~combined_mask).sum()
        
        # 제외 비율
        exclusion_ratio = total_excluded / max(1, self.total_trades)
        
        # 유효성 검사
        if exclusion_ratio > self.config.max_exclusion_ratio:
            return -float('inf'), total_improvement, exclusion_ratio
        
        # 페널티 계산
        penalty = 0.0
        if exclusion_ratio > self.config.exclusion_penalty_threshold:
            excess = exclusion_ratio - self.config.exclusion_penalty_threshold
            penalty = abs(total_improvement) * excess * 0.5
        
        fitness = total_improvement - penalty
        
        return fitness, total_improvement, exclusion_ratio

    def _tournament_select(self, population: List[Dict], fitnesses: List[float]) -> Dict:
        """토너먼트 선택"""
        indices = random.sample(range(len(population)), min(self.config.tournament_size, len(population)))
        best_idx = max(indices, key=lambda i: fitnesses[i])
        return population[best_idx]

    def _crossover(self, parent1: Dict, parent2: Dict) -> Tuple[Dict, Dict]:
        """교차 (세그먼트 단위)"""
        child1, child2 = {}, {}
        
        for seg_id in parent1.keys():
            if random.random() < self.config.crossover_rate:
                child1[seg_id] = parent2.get(seg_id, []).copy()
                child2[seg_id] = parent1.get(seg_id, []).copy()
            else:
                child1[seg_id] = parent1.get(seg_id, []).copy()
                child2[seg_id] = parent2.get(seg_id, []).copy()
        
        return child1, child2

    def _mutate(self, chromosome: Dict) -> Dict:
        """돌연변이"""
        for seg_id in chromosome.keys():
            if random.random() >= self.config.mutation_rate:
                continue
            
            cands = self.candidates.get(seg_id, [])
            if not cands:
                continue
            
            current = chromosome[seg_id]
            
            # 돌연변이 유형 선택
            mutation_type = random.choice(['add', 'remove', 'replace'])
            
            if mutation_type == 'add' and len(current) < self.config.max_filters_per_segment:
                # 새 필터 추가
                available = set(range(len(cands))) - set(current)
                if available:
                    chromosome[seg_id] = current + [random.choice(list(available))]
            
            elif mutation_type == 'remove' and current:
                # 필터 제거
                chromosome[seg_id] = [f for i, f in enumerate(current) if i != random.randint(0, len(current) - 1)]
            
            elif mutation_type == 'replace' and current:
                # 필터 교체
                available = set(range(len(cands))) - set(current)
                if available:
                    replace_idx = random.randint(0, len(current) - 1)
                    chromosome[seg_id][replace_idx] = random.choice(list(available))
        
        return chromosome

    def optimize(self, verbose: bool = False) -> GAResult:
        """
        유전 알고리즘 최적화 실행.

        Args:
            verbose: 진행 상황 출력 여부

        Returns:
            GAResult: 최적화 결과
        """
        # 초기 모집단 생성
        population = [self._create_random_chromosome() for _ in range(self.config.population_size)]
        
        best_chromosome = None
        best_fitness = -float('inf')
        best_improvement = 0.0
        best_exclusion = 0.0
        fitness_history = []
        
        for gen in range(self.config.generations):
            # 적합도 평가
            fitness_scores = []
            improvements = []
            exclusions = []
            
            for chromo in population:
                fit, imp, exc = self._fitness(chromo)
                fitness_scores.append(fit)
                improvements.append(imp)
                exclusions.append(exc)
            
            # 최고 개체 추적
            gen_best_idx = max(range(len(population)), key=lambda i: fitness_scores[i])
            if fitness_scores[gen_best_idx] > best_fitness:
                best_fitness = fitness_scores[gen_best_idx]
                best_chromosome = {k: v.copy() for k, v in population[gen_best_idx].items()}
                best_improvement = improvements[gen_best_idx]
                best_exclusion = exclusions[gen_best_idx]
            
            fitness_history.append(best_fitness)
            
            if verbose and (gen + 1) % 10 == 0:
                print(f"[GA] Gen {gen + 1}/{self.config.generations}: "
                      f"Best fitness={best_fitness:.0f}, Improvement={best_improvement:,.0f}원")
            
            # 엘리트 선택
            elite_indices = sorted(range(len(population)), key=lambda i: fitness_scores[i], reverse=True)
            elite = [population[i] for i in elite_indices[:self.config.elite_size]]
            
            # 다음 세대 생성
            next_gen = [{k: v.copy() for k, v in e.items()} for e in elite]
            
            while len(next_gen) < self.config.population_size:
                # 부모 선택
                p1 = self._tournament_select(population, fitness_scores)
                p2 = self._tournament_select(population, fitness_scores)
                
                # 교차
                c1, c2 = self._crossover(p1, p2)
                
                # 돌연변이
                c1 = self._mutate(c1)
                c2 = self._mutate(c2)
                
                next_gen.extend([c1, c2])
            
            population = next_gen[:self.config.population_size]
        
        # 세그먼트별 상세 정보 생성
        segment_details = {}
        if best_chromosome:
            for seg_id, selected in best_chromosome.items():
                cands = self.candidates.get(seg_id, [])
                segment_details[seg_id] = {
                    'selected_indices': selected,
                    'selected_filters': [cands[i].get('filter_name', f'filter_{i}') for i in selected if i < len(cands)],
                    'n_filters': len(selected),
                }
        
        return GAResult(
            best_chromosome=best_chromosome or {},
            best_fitness=best_fitness,
            best_improvement=best_improvement,
            best_exclusion_ratio=best_exclusion,
            generations_run=self.config.generations,
            fitness_history=fitness_history,
            segment_details=segment_details,
        )


# =============================================================================
# 유틸리티 함수
# =============================================================================

def run_ga_optimization(
    df: pd.DataFrame,
    filter_results: List[dict],
    segment_column: str = '시가총액구간',
    config: Optional[GAConfig] = None,
) -> GAResult:
    """
    데이터프레임과 필터 결과로부터 GA 최적화를 실행합니다.

    Args:
        df: 전체 데이터프레임
        filter_results: 필터 분석 결과 리스트
        segment_column: 세그먼트 분할 컬럼
        config: GA 설정

    Returns:
        GAResult: 최적화 결과
    """
    config = config or GAConfig()
    
    # 세그먼트 분할
    if segment_column in df.columns:
        segments = {str(k): g for k, g in df.groupby(segment_column)}
    else:
        # 세그먼트 없으면 전체를 하나의 세그먼트로
        segments = {'all': df}
    
    # 필터 후보 변환
    candidates_by_segment = {}
    for seg_id in segments.keys():
        cands = []
        for f in filter_results:
            if f.get('수익개선금액', 0) <= 0:
                continue
            
            expr = f.get('조건식', '')
            if not expr:
                continue
            
            # 조건식에서 컬럼과 임계값 추출 시도
            cand = {
                'filter_name': f.get('필터명', ''),
                'condition_expr': expr,
                'improvement': f.get('수익개선금액', 0),
            }
            
            # 단순 임계값 필터 파싱 시도
            if "df_tsg['" in expr:
                try:
                    import re
                    match = re.search(r"df_tsg\['([^']+)'\]\s*([<>=]+)\s*([\d.]+)", expr)
                    if match:
                        cand['column'] = match.group(1)
                        op = match.group(2)
                        cand['threshold'] = float(match.group(3))
                        cand['direction'] = 'less' if '<' in op else 'greater'
                except Exception:
                    pass
            
            cands.append(cand)
        
        candidates_by_segment[seg_id] = cands
    
    # GA 실행
    optimizer = GeneticFilterOptimizer(segments, candidates_by_segment, config)
    return optimizer.optimize()


def convert_ga_result_to_combination(
    ga_result: GAResult,
    candidates_by_segment: Dict[str, List[dict]],
) -> dict:
    """
    GA 결과를 기존 combination_optimizer 형식으로 변환합니다.
    """
    combination = {}
    
    for seg_id, selected_indices in ga_result.best_chromosome.items():
        cands = candidates_by_segment.get(seg_id, [])
        filters = []
        
        for idx in selected_indices:
            if idx < len(cands):
                filters.append({
                    'column': cands[idx].get('column'),
                    'threshold': cands[idx].get('threshold'),
                    'direction': cands[idx].get('direction'),
                    'filter_name': cands[idx].get('filter_name'),
                })
        
        combination[seg_id] = {
            'filters': filters,
            'improvement': ga_result.best_improvement / max(1, len(ga_result.best_chromosome)),
        }
    
    return {
        'combination': combination,
        'score': ga_result.best_fitness,
        'excluded_trades': int(ga_result.best_exclusion_ratio * ga_result.best_improvement),  # 근사값
    }
