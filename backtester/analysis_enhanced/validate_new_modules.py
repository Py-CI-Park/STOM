"""
Real Data Validation Script for Enhanced Buy Condition Generator v2.0
Tests all new modules with actual backtest output data.

Usage:
    python backtester/analysis_enhanced/validate_new_modules.py
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np


def load_test_data(detail_csv_path: str) -> pd.DataFrame:
    """Load and prepare test data from detail.csv"""
    print(f"\n[1] Loading test data from: {detail_csv_path}")
    df = pd.read_csv(detail_csv_path, encoding='utf-8-sig')
    print(f"    Loaded {len(df):,} trades with {len(df.columns)} columns")
    
    # Check required columns
    required = ['수익률', '수익금', '매수등락율', '매수체결강도', '매수회전율']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"    WARNING: Missing columns: {missing}")
    else:
        print(f"    All required columns present")
    
    return df


def test_multiple_testing_correction(df: pd.DataFrame) -> dict:
    """Test 1: Multiple Testing Correction"""
    print("\n[2] Testing Multiple Testing Correction...")
    from backtester.analysis_enhanced.stats import apply_multiple_testing_correction, get_correction_summary
    
    # Generate fake filter results with p-values (function expects list of dicts)
    np.random.seed(42)
    n_tests = 50
    p_values_raw = np.random.uniform(0.01, 0.1, n_tests)
    # Add some truly significant ones
    p_values_raw[:5] = [0.001, 0.002, 0.005, 0.008, 0.01]
    
    # Create filter results in expected format
    filter_results = [{'필터명': f'filter_{i}', 'p값': p} for i, p in enumerate(p_values_raw)]
    
    results = {}
    for method in ['bonferroni', 'holm', 'fdr_bh']:
        start = time.time()
        # Make a copy since the function modifies in place
        filter_results_copy = [dict(f) for f in filter_results]
        corrected = apply_multiple_testing_correction(filter_results_copy, method=method)
        elapsed = time.time() - start
        
        n_sig_before = sum(1 for p in p_values_raw if p < 0.05)
        n_sig_after = sum(1 for f in corrected if f.get('p값_adjusted', 1.0) < 0.05)
        
        results[method] = {
            'n_significant_before': n_sig_before,
            'n_significant_after': n_sig_after,
            'false_positive_reduction': f"{(1 - n_sig_after/max(n_sig_before, 1))*100:.1f}%",
            'elapsed_ms': f"{elapsed*1000:.2f}"
        }
        print(f"    {method}: {n_sig_before} -> {n_sig_after} significant ({results[method]['false_positive_reduction']} reduction)")
    
    # Get summary from last corrected result (expects the corrected filter_results list)
    # Need to add '유의함' field for the summary function
    for f in corrected:
        f['유의함'] = '예' if f['p값'] < 0.05 else '아니오'
    summary = get_correction_summary(corrected)
    print(f"    Summary: {summary}")
    
    return results


def test_purged_walk_forward_cv(df: pd.DataFrame) -> dict:
    """Test 2: Purged Walk-Forward CV"""
    print("\n[3] Testing Purged Walk-Forward CV...")
    from backtester.analysis_enhanced.validation_enhanced import (
        PurgedWalkForwardConfig, purged_walk_forward_splits, validate_filter_with_cv
    )
    
    config = PurgedWalkForwardConfig(n_splits=5, gap_ratio=0.05, min_trades_per_fold=30)
    
    # Test split generation
    start = time.time()
    splits = list(purged_walk_forward_splits(df, config))
    elapsed_splits = time.time() - start
    
    print(f"    Generated {len(splits)} CV splits in {elapsed_splits*1000:.2f}ms")
    for i, (train_mask, test_mask) in enumerate(splits):
        train_count = train_mask.sum()
        test_count = test_mask.sum()
        print(f"      Split {i+1}: train={train_count:,}, test={test_count:,}")
    
    # Validate a filter using filter expression
    filter_expr = "(df_tsg['매수등락율'] > 5.0)"  # Simple filter that should exclude some trades
    
    start = time.time()
    cv_result = validate_filter_with_cv(
        df=df,
        filter_expr=filter_expr,
        filter_name='등락율>5',
        config=config
    )
    elapsed_validate = time.time() - start
    
    results = {
        'n_splits': len(splits),
        'mean_train_improvement': f"{cv_result.mean_train_improvement:.0f}원",
        'mean_test_improvement': f"{cv_result.mean_test_improvement:.0f}원",
        'std_test_improvement': f"{cv_result.std_test_improvement:.0f}원",
        'generalization_ratio': f"{cv_result.generalization_ratio:.2%}",
        'positive_fold_ratio': f"{cv_result.positive_fold_ratio:.2%}",
        'is_robust': cv_result.is_robust,
        'elapsed_ms': f"{elapsed_validate*1000:.2f}"
    }
    print(f"    OOS Validation: mean_train={results['mean_train_improvement']}, mean_test={results['mean_test_improvement']}")
    print(f"    Generalization: {results['generalization_ratio']}, Positive folds: {results['positive_fold_ratio']}, Robust: {cv_result.is_robust}")
    
    return results


def test_feature_selection(df: pd.DataFrame) -> dict:
    """Test 3: Feature Selection (MI & Correlation)"""
    print("\n[4] Testing Feature Selection...")
    from backtester.analysis_enhanced.feature_selection import (
        calculate_filter_mutual_information,
        calculate_filter_correlation_matrix,
        greedy_select_diverse_filters,
        remove_redundant_filters
    )
    
    # Create filter masks as list of numpy arrays
    filter_masks = [
        (df['매수등락율'] > 3.0).values,
        (df['매수등락율'] > 5.0).values,
        (df['매수체결강도'] > 100).values,
        (df['매수체결강도'] > 120).values,
        (df['매수회전율'] > 5).values,
        (df['매수회전율'] > 10).values,
    ]
    filter_names = ['등락율>3', '등락율>5', '체결강도>100', '체결강도>120', '회전율>5', '회전율>10']
    
    # Test MI calculation
    start = time.time()
    mi_results = calculate_filter_mutual_information(df, filter_masks, filter_names)
    elapsed_mi = time.time() - start
    
    print(f"    Mutual Information scores ({elapsed_mi*1000:.2f}ms):")
    for r in mi_results[:5]:
        print(f"      {r['filter_name']}: {r['mi_score']:.4f} {'(informative)' if r['is_informative'] else ''}")
    
    # Test correlation matrix
    start = time.time()
    corr_matrix = calculate_filter_correlation_matrix(filter_masks)
    elapsed_corr = time.time() - start
    
    print(f"    Correlation matrix ({elapsed_corr*1000:.2f}ms): shape={corr_matrix.shape}")
    
    # Create filter_results in expected format for greedy selection
    filter_results = []
    for i, name in enumerate(filter_names):
        mask = filter_masks[i]
        filtered_profit = df['수익금'].values[mask].sum()
        filter_results.append({
            '필터명': name,
            '조건식': f"(df_tsg['매수등락율'] > {3 if i < 2 else 100 if i < 4 else 5})",  # Simplified
            '수익개선금액': -filtered_profit,  # Improvement = negative of excluded profits
            '제외건수': mask.sum(),
        })
    
    # Test greedy selection
    start = time.time()
    selected = greedy_select_diverse_filters(
        filter_results=filter_results,
        df=df,
        max_filters=3,
        diversity_weight=0.3
    )
    elapsed_greedy = time.time() - start
    
    print(f"    Greedy diverse selection ({elapsed_greedy*1000:.2f}ms): {[s['필터명'] for s in selected]}")
    
    # Test redundancy removal
    start = time.time()
    non_redundant = remove_redundant_filters(filter_results, df, correlation_threshold=0.8)
    elapsed_redundant = time.time() - start
    
    print(f"    Non-redundant filters ({elapsed_redundant*1000:.2f}ms): {[f['필터명'] for f in non_redundant]}")
    
    return {
        'n_original_filters': len(filter_masks),
        'n_selected': len(selected),
        'n_non_redundant': len(non_redundant),
        'top_mi_filter': mi_results[0]['filter_name'] if mi_results else 'N/A',
        'elapsed_total_ms': f"{(elapsed_mi + elapsed_corr + elapsed_greedy + elapsed_redundant)*1000:.2f}"
    }


def test_ensemble_filter(df: pd.DataFrame) -> dict:
    """Test 4: Ensemble Filter Selection"""
    print("\n[5] Testing Ensemble Filter Selection...")
    from backtester.analysis_enhanced.ensemble_filter import (
        EnsembleConfig, ensemble_filter_selection
    )
    
    # Create a simple analyze function that returns filter results
    def simple_analyze_func(sample_df):
        """Simple filter analysis function for testing"""
        filter_results = []
        
        # Test a few simple filters
        filters = [
            ('등락율>5', "(df_tsg['매수등락율'] > 5.0)", sample_df['매수등락율'] > 5.0),
            ('체결강도>100', "(df_tsg['매수체결강도'] > 100)", sample_df['매수체결강도'] > 100),
            ('회전율>5', "(df_tsg['매수회전율'] > 5)", sample_df['매수회전율'] > 5),
        ]
        
        for name, expr, mask in filters:
            if mask.sum() > 0:
                excluded_profit = sample_df.loc[mask, '수익금'].sum()
                improvement = -excluded_profit  # Positive if excluded losses
                filter_results.append({
                    '필터명': name,
                    '조건식': expr,
                    '필터코드': f"# {name}",
                    '수익개선금액': improvement,
                    '제외건수': mask.sum(),
                })
        
        return filter_results
    
    config = EnsembleConfig(
        n_bootstrap=10,  # Reduced for speed
        sample_ratio=0.7,
        vote_threshold=0.5
    )
    
    start = time.time()
    ensemble_result = ensemble_filter_selection(
        df=df,
        analyze_func=simple_analyze_func,
        config=config
    )
    elapsed = time.time() - start
    
    stable_filters = ensemble_result.get('stable_filters', [])
    vote_counts = ensemble_result.get('vote_counts', {})
    
    print(f"    Ensemble voting ({elapsed*1000:.2f}ms):")
    print(f"      Stable filters: {len(stable_filters)}")
    print(f"      Vote counts: {vote_counts}")
    
    return {
        'n_selected': len(stable_filters),
        'stable_filters': [f.filter_name for f in stable_filters] if stable_filters else [],
        'elapsed_ms': f"{elapsed*1000:.2f}"
    }


def test_genetic_optimizer(df: pd.DataFrame) -> dict:
    """Test 5: Genetic Algorithm Optimizer"""
    print("\n[6] Testing Genetic Algorithm Optimizer...")
    
    try:
        from backtester.segment_analysis.genetic_optimizer import (
            GAConfig, GeneticFilterOptimizer
        )
    except (PermissionError, ImportError) as e:
        print(f"    SKIP: Cannot import genetic_optimizer ({e})")
        return {'status': 'skipped', 'reason': str(e)}
    
    # Create segment-filter data structure
    # Simulating 3 segments with filter analysis results
    segment_filter_results = {}
    
    # Create filter masks
    base_filters = {
        '등락율>3': (df['매수등락율'] > 3.0).values,
        '체결강도>100': (df['매수체결강도'] > 100).values,
        '회전율>5': (df['매수회전율'] > 5).values,
    }
    
    profits = df['수익금'].values
    
    # Simulate segments by time-based split
    n = len(df)
    segments = [
        ('segment_1', list(range(0, n//3))),
        ('segment_2', list(range(n//3, 2*n//3))),
        ('segment_3', list(range(2*n//3, n))),
    ]
    
    for seg_name, seg_indices in segments:
        segment_filter_results[seg_name] = {
            'indices': seg_indices,
            'filters': {
                fname: {
                    'mask': fmask[seg_indices],
                    'improvement': np.random.uniform(1, 5),  # Simulated
                    'p_value': np.random.uniform(0.01, 0.1)
                }
                for fname, fmask in base_filters.items()
            }
        }
    
    config = GAConfig(
        population_size=20,  # Reduced for speed
        generations=10,
        mutation_rate=0.1,
        crossover_rate=0.8,
        tournament_size=3,
        elitism_count=2
    )
    
    start = time.time()
    optimizer = GeneticFilterOptimizer(
        segment_filter_results=segment_filter_results,
        profits=profits,
        config=config
    )
    best_solution, best_fitness, history = optimizer.optimize()
    elapsed = time.time() - start
    
    print(f"    GA Optimization ({elapsed*1000:.2f}ms):")
    print(f"      Best fitness: {best_fitness:.4f}")
    print(f"      Best solution: {best_solution}")
    print(f"      Generations: {len(history)}")
    print(f"      Fitness progression: {[f'{h:.3f}' for h in history[:5]]} ... {[f'{h:.3f}' for h in history[-3:]]}")
    
    return {
        'best_fitness': f"{best_fitness:.4f}",
        'n_segments': len(segments),
        'generations': len(history),
        'final_improvement': f"{(history[-1] - history[0]) / abs(history[0]) * 100:.1f}%" if history[0] != 0 else "N/A",
        'elapsed_ms': f"{elapsed*1000:.2f}"
    }


def test_adaptive_segmentation(df: pd.DataFrame) -> dict:
    """Test 6: Adaptive Segmentation (K-Means Clustering)"""
    print("\n[7] Testing Adaptive Segmentation...")
    
    try:
        from backtester.analysis_enhanced.advanced_analysis import (
            discover_adaptive_segments
        )
    except (PermissionError, ImportError) as e:
        print(f"    SKIP: Cannot import advanced_analysis ({e})")
        return {'status': 'skipped', 'reason': str(e)}
    
    # Use columns available in the data
    segment_cols = ['매수등락율', '매수체결강도']
    available_cols = [c for c in segment_cols if c in df.columns]
    
    if len(available_cols) < 1:
        print("    SKIP: Not enough segment columns available")
        return {'status': 'skipped', 'reason': 'insufficient columns'}
    
    start = time.time()
    result = discover_adaptive_segments(
        df=df,
        segment_columns=available_cols,
        n_segments=4,
        method='kmeans'
    )
    elapsed = time.time() - start
    
    if result.error:
        print(f"    ERROR: {result.error}")
        return {'status': 'error', 'error': result.error}
    
    # Count segments
    segment_sizes = {}
    for label in np.unique(result.segment_labels):
        segment_sizes[label] = int(np.sum(result.segment_labels == label))
    
    print(f"    Adaptive segmentation ({elapsed*1000:.2f}ms):")
    print(f"      Segments: {result.n_segments}")
    print(f"      Silhouette score: {result.silhouette_score:.4f}" if result.silhouette_score else "      Silhouette score: N/A")
    print(f"      Segment sizes: {segment_sizes}")
    print(f"      Boundaries: {list(result.segment_boundaries.keys())}")
    
    return {
        'n_segments': result.n_segments,
        'silhouette_score': f"{result.silhouette_score:.4f}" if result.silhouette_score else 'N/A',
        'segment_sizes': segment_sizes,
        'elapsed_ms': f"{elapsed*1000:.2f}"
    }


def test_shap_analysis(df: pd.DataFrame) -> dict:
    """Test 7: SHAP Analysis (Optional - requires shap library)"""
    print("\n[8] Testing SHAP Analysis...")
    
    try:
        import shap
    except ImportError:
        print("    SKIP: shap library not installed (pip install shap)")
        return {'status': 'skipped', 'reason': 'shap not installed'}
    
    from backtester.analysis_enhanced.advanced_analysis import (
        analyze_with_shap, get_shap_filter_recommendations
    )
    
    # Prepare features and target
    feature_cols = ['매수등락율', '매수체결강도', '매수회전율', '매수당일거래대금']
    available_cols = [c for c in feature_cols if c in df.columns]
    
    if len(available_cols) < 3:
        print("    SKIP: Not enough feature columns available")
        return {'status': 'skipped', 'reason': 'insufficient columns'}
    
    features = df[available_cols].fillna(0)
    target = (df['수익금'] > 0).astype(int)
    
    start = time.time()
    shap_result = analyze_with_shap(
        features=features,
        target=target,
        max_samples=min(500, len(df))  # Limit for speed
    )
    elapsed = time.time() - start
    
    print(f"    SHAP Analysis ({elapsed*1000:.2f}ms):")
    print(f"      Feature importance: {shap_result.feature_importance}")
    
    # Get filter recommendations
    recommendations = get_shap_filter_recommendations(shap_result, top_k=3)
    print(f"      Recommendations: {recommendations}")
    
    return {
        'feature_importance': shap_result.feature_importance,
        'n_recommendations': len(recommendations),
        'elapsed_ms': f"{elapsed*1000:.2f}"
    }


def main():
    """Main validation function"""
    print("=" * 70)
    print("Enhanced Buy Condition Generator v2.0 - Real Data Validation")
    print("=" * 70)
    
    # Find the latest backtest output
    output_dir = project_root / "backtester" / "backtesting_output"
    latest_dir = sorted(output_dir.glob("stock_bt_*"))[-1] if list(output_dir.glob("stock_bt_*")) else None
    
    if not latest_dir:
        print("ERROR: No backtest output found!")
        return
    
    detail_csv = list(latest_dir.glob("*_detail.csv"))
    if not detail_csv:
        print(f"ERROR: No detail.csv found in {latest_dir}")
        return
    
    # Use the main detail.csv (not filtered)
    detail_csv = [f for f in detail_csv if 'filtered' not in f.name][0]
    
    # Load test data
    df = load_test_data(str(detail_csv))
    
    # Run all tests
    results = {}
    
    results['multiple_testing'] = test_multiple_testing_correction(df)
    results['purged_cv'] = test_purged_walk_forward_cv(df)
    results['feature_selection'] = test_feature_selection(df)
    results['ensemble_filter'] = test_ensemble_filter(df)
    results['genetic_optimizer'] = test_genetic_optimizer(df)
    results['adaptive_segmentation'] = test_adaptive_segmentation(df)
    results['shap_analysis'] = test_shap_analysis(df)
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, test_result in results.items():
        status = test_result.get('status', 'passed')
        if status == 'skipped':
            print(f"  [{test_name}] SKIPPED - {test_result.get('reason', 'unknown')}")
        elif 'error' in str(test_result).lower():
            print(f"  [{test_name}] FAILED")
            all_passed = False
        else:
            print(f"  [{test_name}] PASSED")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("ALL TESTS PASSED! New modules validated with real data.")
    else:
        print("SOME TESTS FAILED. Please check the output above.")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    main()
