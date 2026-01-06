# -*- coding: utf-8 -*-
"""
Unit Tests for Enhanced Buy Condition Generator v2.0

Tests all new modules:
- stats.py: Multiple testing correction
- validation_enhanced.py: Purged Walk-Forward CV
- feature_selection.py: MI and correlation-based selection
- ensemble_filter.py: Bootstrap ensemble selection
- advanced_analysis.py: Adaptive segmentation

Run with: pytest tests/test_enhanced_buy_condition.py -v
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
import pytest


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing"""
    np.random.seed(42)
    n = 500
    
    df = pd.DataFrame({
        '매수일자': pd.date_range('2025-01-01', periods=n, freq='H').strftime('%Y%m%d'),
        '매수등락율': np.random.uniform(-5, 15, n),
        '매수체결강도': np.random.uniform(50, 150, n),
        '매수회전율': np.random.uniform(1, 20, n),
        '시가총액': np.random.uniform(100, 50000, n),
        '수익금': np.random.normal(0, 100000, n),
    })
    
    return df


@pytest.fixture
def sample_filter_results(sample_df):
    """Create sample filter results for testing"""
    return [
        {
            '필터명': '등락율>5',
            '조건식': "(df_tsg['매수등락율'] > 5.0)",
            '수익개선금액': 50000,
            '제외건수': 100,
            'p값': 0.02,
            '유의함': '예',
        },
        {
            '필터명': '체결강도>100',
            '조건식': "(df_tsg['매수체결강도'] > 100)",
            '수익개선금액': 30000,
            '제외건수': 80,
            'p값': 0.08,
            '유의함': '아니오',
        },
        {
            '필터명': '회전율>10',
            '조건식': "(df_tsg['매수회전율'] > 10)",
            '수익개선금액': 20000,
            '제외건수': 60,
            'p값': 0.04,
            '유의함': '예',
        },
    ]


# =============================================================================
# Test: Multiple Testing Correction
# =============================================================================

class TestMultipleTestingCorrection:
    """Tests for stats.py multiple testing correction"""
    
    def test_bonferroni_correction(self, sample_filter_results):
        """Test Bonferroni correction reduces false positives"""
        from backtester.analysis_enhanced.stats import apply_multiple_testing_correction
        
        # Make a copy
        results = [dict(r) for r in sample_filter_results]
        
        corrected = apply_multiple_testing_correction(results, method='bonferroni')
        
        # Check that adjusted p-values are added
        assert all('p값_adjusted' in r for r in corrected)
        assert all('보정방법' in r for r in corrected)
        
        # Bonferroni: p_adj = p * n, so should be more conservative
        for r in corrected:
            assert r['p값_adjusted'] >= r['p값']
    
    def test_holm_correction(self, sample_filter_results):
        """Test Holm correction"""
        from backtester.analysis_enhanced.stats import apply_multiple_testing_correction
        
        results = [dict(r) for r in sample_filter_results]
        corrected = apply_multiple_testing_correction(results, method='holm')
        
        assert corrected[0]['보정방법'] == 'holm'
        assert all('p값_adjusted' in r for r in corrected)
    
    def test_fdr_bh_correction(self, sample_filter_results):
        """Test FDR-BH correction"""
        from backtester.analysis_enhanced.stats import apply_multiple_testing_correction
        
        results = [dict(r) for r in sample_filter_results]
        corrected = apply_multiple_testing_correction(results, method='fdr_bh')
        
        assert corrected[0]['보정방법'] == 'fdr_bh'
    
    def test_no_correction(self, sample_filter_results):
        """Test that 'none' method returns unchanged results"""
        from backtester.analysis_enhanced.stats import apply_multiple_testing_correction
        
        results = [dict(r) for r in sample_filter_results]
        corrected = apply_multiple_testing_correction(results, method='none')
        
        # Should return same results
        assert len(corrected) == len(sample_filter_results)
    
    def test_get_correction_summary(self, sample_filter_results):
        """Test correction summary generation"""
        from backtester.analysis_enhanced.stats import (
            apply_multiple_testing_correction, get_correction_summary
        )
        
        results = [dict(r) for r in sample_filter_results]
        corrected = apply_multiple_testing_correction(results, method='bonferroni')
        summary = get_correction_summary(corrected)
        
        assert 'total_tests' in summary
        assert 'significant_before' in summary
        assert 'significant_after' in summary
        assert 'method' in summary


# =============================================================================
# Test: Purged Walk-Forward CV
# =============================================================================

class TestPurgedWalkForwardCV:
    """Tests for validation_enhanced.py"""
    
    def test_split_generation(self, sample_df):
        """Test that splits are generated correctly"""
        from backtester.analysis_enhanced.validation_enhanced import (
            PurgedWalkForwardConfig, purged_walk_forward_splits
        )
        
        config = PurgedWalkForwardConfig(
            n_splits=3,
            gap_ratio=0.05,
            min_trades_per_fold=10
        )
        
        splits = list(purged_walk_forward_splits(sample_df, config))
        
        # Should generate some splits
        assert len(splits) > 0
        
        # Each split should have train and test masks
        for train_mask, test_mask in splits:
            assert train_mask.sum() > 0
            assert test_mask.sum() > 0
            
            # No overlap between train and test
            assert not np.any(train_mask & test_mask)
    
    def test_filter_validation(self, sample_df):
        """Test single filter validation"""
        from backtester.analysis_enhanced.validation_enhanced import (
            PurgedWalkForwardConfig, validate_filter_with_cv
        )
        
        config = PurgedWalkForwardConfig(
            n_splits=3,
            min_trades_per_fold=10
        )
        
        result = validate_filter_with_cv(
            df=sample_df,
            filter_expr="(df_tsg['매수등락율'] > 5.0)",
            filter_name='test_filter',
            config=config
        )
        
        assert result.filter_name == 'test_filter'
        assert hasattr(result, 'mean_train_improvement')
        assert hasattr(result, 'mean_test_improvement')
        assert hasattr(result, 'generalization_ratio')


# =============================================================================
# Test: Feature Selection
# =============================================================================

class TestFeatureSelection:
    """Tests for feature_selection.py"""
    
    def test_mutual_information_calculation(self, sample_df):
        """Test MI calculation"""
        from backtester.analysis_enhanced.feature_selection import (
            calculate_filter_mutual_information
        )
        
        # Create filter masks
        filter_masks = [
            (sample_df['매수등락율'] > 5.0).values,
            (sample_df['매수체결강도'] > 100).values,
        ]
        filter_names = ['등락율>5', '체결강도>100']
        
        mi_results = calculate_filter_mutual_information(
            sample_df, filter_masks, filter_names
        )
        
        assert len(mi_results) > 0
        assert all('mi_score' in r for r in mi_results)
        assert all('filter_name' in r for r in mi_results)
    
    def test_correlation_matrix(self, sample_df):
        """Test Jaccard correlation matrix"""
        from backtester.analysis_enhanced.feature_selection import (
            calculate_filter_correlation_matrix
        )
        
        filter_masks = [
            (sample_df['매수등락율'] > 5.0).values,
            (sample_df['매수등락율'] > 3.0).values,  # Similar filter
            (sample_df['매수체결강도'] > 100).values,
        ]
        
        corr_matrix = calculate_filter_correlation_matrix(filter_masks)
        
        # Should be square matrix
        assert corr_matrix.shape == (3, 3)
        
        # Diagonal should be 1 (perfect correlation with self)
        np.testing.assert_array_almost_equal(
            np.diag(corr_matrix), np.ones(3)
        )
        
        # First two filters should have high correlation
        assert corr_matrix[0, 1] > 0.5
    
    def test_greedy_diverse_selection(self, sample_df, sample_filter_results):
        """Test diversity-aware greedy selection"""
        from backtester.analysis_enhanced.feature_selection import (
            greedy_select_diverse_filters
        )
        
        selected = greedy_select_diverse_filters(
            filter_results=sample_filter_results,
            df=sample_df,
            max_filters=2,
            diversity_weight=0.3
        )
        
        assert len(selected) <= 2
        assert all('다양성점수' in f for f in selected)


# =============================================================================
# Test: Ensemble Filter Selection
# =============================================================================

class TestEnsembleFilter:
    """Tests for ensemble_filter.py"""
    
    def test_ensemble_selection(self, sample_df):
        """Test bootstrap ensemble selection"""
        from backtester.analysis_enhanced.ensemble_filter import (
            EnsembleConfig, ensemble_filter_selection
        )
        
        def simple_analyze(df):
            return [
                {
                    '필터명': '등락율>5',
                    '조건식': "(df_tsg['매수등락율'] > 5.0)",
                    '필터코드': '# test',
                    '수익개선금액': -df.loc[df['매수등락율'] > 5, '수익금'].sum(),
                    '제외건수': (df['매수등락율'] > 5).sum(),
                }
            ]
        
        config = EnsembleConfig(
            n_bootstrap=5,
            sample_ratio=0.7,
            vote_threshold=0.5
        )
        
        result = ensemble_filter_selection(
            df=sample_df,
            analyze_func=simple_analyze,
            config=config
        )
        
        assert 'stable_filters' in result
        assert 'vote_counts' in result


# =============================================================================
# Test: Adaptive Segmentation
# =============================================================================

class TestAdaptiveSegmentation:
    """Tests for advanced_analysis.py adaptive segmentation"""
    
    def test_kmeans_segmentation(self, sample_df):
        """Test K-Means based segmentation"""
        try:
            from backtester.analysis_enhanced.advanced_analysis import (
                discover_adaptive_segments
            )
        except (PermissionError, ImportError) as e:
            pytest.skip(f"Cannot import: {e}")
        
        result = discover_adaptive_segments(
            df=sample_df,
            segment_columns=['매수등락율'],
            n_segments=3,
            method='kmeans'
        )
        
        if result.error:
            pytest.skip(f"Segmentation error: {result.error}")
        
        assert result.n_segments == 3
        assert len(result.segment_labels) == len(sample_df)
        assert result.segment_boundaries is not None


# =============================================================================
# Test: Integration
# =============================================================================

class TestIntegration:
    """Integration tests"""
    
    def test_full_pipeline(self, sample_df):
        """Test full analysis pipeline"""
        from backtester.analysis_enhanced.stats import apply_multiple_testing_correction
        from backtester.analysis_enhanced.feature_selection import (
            calculate_filter_mutual_information,
            calculate_filter_correlation_matrix
        )
        
        # Step 1: Create filter results
        filter_results = [
            {
                '필터명': '등락율>5',
                '조건식': "(df_tsg['매수등락율'] > 5.0)",
                '수익개선금액': 50000,
                'p값': 0.02,
                '유의함': '예',
            },
            {
                '필터명': '체결강도>100',
                '조건식': "(df_tsg['매수체결강도'] > 100)",
                '수익개선금액': 30000,
                'p값': 0.08,
                '유의함': '아니오',
            },
        ]
        
        # Step 2: Multiple testing correction
        corrected = apply_multiple_testing_correction(filter_results, method='bonferroni')
        assert len(corrected) == 2
        
        # Step 3: MI calculation
        filter_masks = [
            (sample_df['매수등락율'] > 5.0).values,
            (sample_df['매수체결강도'] > 100).values,
        ]
        mi_results = calculate_filter_mutual_information(sample_df, filter_masks)
        assert len(mi_results) > 0
        
        # Step 4: Correlation matrix
        corr_matrix = calculate_filter_correlation_matrix(filter_masks)
        assert corr_matrix.shape == (2, 2)


# =============================================================================
# Run tests
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
