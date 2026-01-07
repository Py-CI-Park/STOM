# -*- coding: utf-8 -*-
"""
Unit Tests for Segment Apply Module

Tests:
- validate_segment_filter_consistency()
- get_filter_diagnostic_info()
- build_segment_mask_from_global_best()
- load_segment_config_from_ranges()

Run with: pytest tests/test_segment_apply.py -v
"""

import sys
from pathlib import Path
import tempfile
import shutil

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
    """백테스팅 결과 DataFrame 생성"""
    np.random.seed(42)
    n = 500
    
    # 시가총액 분포: 대형주, 중형주, 소형주, 초소형주
    cap_bins = [50000, 10000, 5000, 1000, 100]  # 억 단위
    cap_probs = [0.1, 0.2, 0.3, 0.4]
    
    caps = np.random.choice(cap_bins[:-1], n, p=cap_probs)
    caps = caps + np.random.uniform(-500, 500, n)  # 노이즈 추가
    
    # 시간대 분포 (HHMMSS)
    times = np.random.choice([91000, 100000, 110000, 130000, 143000], n)
    times = times + np.random.randint(0, 5959, n)
    
    df = pd.DataFrame({
        '시가총액': caps,
        '시분초': times,
        '매수등락율': np.random.uniform(-5, 25, n),
        '매수체결강도': np.random.uniform(50, 200, n),
        '수익금': np.random.normal(0, 100000, n),
        '매수일자': np.random.choice([20250401, 20250402, 20250403], n),
    })
    
    return df


@pytest.fixture
def sample_global_best(tmp_path):
    """샘플 global_best 딕셔너리 생성"""
    # ranges.csv 생성
    ranges_path = tmp_path / "ranges.csv"
    ranges_df = pd.DataFrame([
        {'range_type': 'market_cap', 'label': '대형주', 'min': 10000, 'max': float('inf')},
        {'range_type': 'market_cap', 'label': '중형주', 'min': 5000, 'max': 10000},
        {'range_type': 'market_cap', 'label': '소형주', 'min': 1000, 'max': 5000},
        {'range_type': 'market_cap', 'label': '초소형주', 'min': 0, 'max': 1000},
        {'range_type': 'time', 'label': 'T1', 'min': 90000, 'max': 100000},
        {'range_type': 'time', 'label': 'T2', 'min': 100000, 'max': 113000},
        {'range_type': 'time', 'label': 'T3', 'min': 113000, 'max': 140000},
        {'range_type': 'time', 'label': 'T4', 'min': 140000, 'max': 153000},
    ])
    ranges_df.to_csv(ranges_path, index=False, encoding='utf-8-sig')
    
    global_best = {
        'ranges_path': str(ranges_path),
        'combination': {
            '대형주_T1': {
                'exclude_segment': False,
                'filters': [
                    {'column': '매수등락율', 'threshold': 20, 'direction': 'less'},
                ]
            },
            '대형주_T2': {
                'exclude_segment': False,
                'filters': [
                    {'column': '매수체결강도', 'threshold': 80, 'direction': 'greater'},
                ]
            },
            '중형주_T1': {
                'exclude_segment': True,  # 세그먼트 제외
            },
            '소형주_T1': {
                'exclude_segment': False,
                'filters': []  # 필터 없음
            },
        }
    }
    
    return global_best


@pytest.fixture
def temp_dir():
    """임시 디렉토리 생성"""
    dirpath = tempfile.mkdtemp()
    yield dirpath
    shutil.rmtree(dirpath)


# =============================================================================
# Test: load_segment_config_from_ranges
# =============================================================================

class TestLoadSegmentConfigFromRanges:
    """load_segment_config_from_ranges 테스트"""
    
    def test_load_valid_ranges(self, sample_global_best):
        """유효한 ranges.csv 로드 테스트"""
        from backtester.segment_analysis.segment_apply import load_segment_config_from_ranges
        
        config = load_segment_config_from_ranges(sample_global_best)
        
        assert config.dynamic_mode == 'fixed'
        assert '대형주' in config.market_cap_ranges
        assert 'T1' in config.time_ranges
        assert config.market_cap_ranges['대형주'][0] == 10000
    
    def test_load_missing_ranges_path(self):
        """ranges_path가 없을 때 기본 설정 반환"""
        from backtester.segment_analysis.segment_apply import load_segment_config_from_ranges
        
        config = load_segment_config_from_ranges({})
        
        # 기본 SegmentConfig 반환
        assert config is not None
    
    def test_load_invalid_path(self):
        """존재하지 않는 경로"""
        from backtester.segment_analysis.segment_apply import load_segment_config_from_ranges
        
        config = load_segment_config_from_ranges({'ranges_path': '/nonexistent/path.csv'})
        
        assert config is not None


# =============================================================================
# Test: build_segment_mask_from_global_best
# =============================================================================

class TestBuildSegmentMask:
    """build_segment_mask_from_global_best 테스트"""
    
    def test_basic_mask_generation(self, sample_df, sample_global_best):
        """기본 마스크 생성 테스트"""
        from backtester.segment_analysis.segment_apply import build_segment_mask_from_global_best
        
        result = build_segment_mask_from_global_best(sample_df, sample_global_best)
        
        assert result['error'] is None
        assert result['mask'] is not None
        assert len(result['mask']) == len(sample_df)
        assert isinstance(result['mask'], np.ndarray)
    
    def test_empty_dataframe(self, sample_global_best):
        """빈 DataFrame 처리"""
        from backtester.segment_analysis.segment_apply import build_segment_mask_from_global_best
        
        empty_df = pd.DataFrame()
        result = build_segment_mask_from_global_best(empty_df, sample_global_best)
        
        assert result['error'] is not None
        assert 'df가 비어있음' in result['error']
    
    def test_invalid_global_best(self, sample_df):
        """잘못된 global_best 처리"""
        from backtester.segment_analysis.segment_apply import build_segment_mask_from_global_best
        
        result = build_segment_mask_from_global_best(sample_df, None)
        assert result['error'] is not None
        
        result = build_segment_mask_from_global_best(sample_df, {})
        assert result['error'] is not None
    
    def test_missing_columns(self, sample_df, sample_global_best):
        """누락 컬럼 감지"""
        from backtester.segment_analysis.segment_apply import build_segment_mask_from_global_best
        
        # 존재하지 않는 컬럼 필터 추가
        sample_global_best['combination']['대형주_T1']['filters'].append({
            'column': '없는컬럼',
            'threshold': 100,
            'direction': 'less',
        })
        
        result = build_segment_mask_from_global_best(sample_df, sample_global_best)
        
        assert '없는컬럼' in result['missing_columns']


# =============================================================================
# Test: validate_segment_filter_consistency
# =============================================================================

class TestValidateSegmentFilterConsistency:
    """validate_segment_filter_consistency 테스트"""
    
    def test_consistency_check_pass(self, sample_df, sample_global_best):
        """일관성 검증 통과 테스트"""
        from backtester.segment_analysis.segment_apply import (
            validate_segment_filter_consistency,
            build_segment_mask_from_global_best,
        )
        
        # 먼저 실제 통과 수 계산
        mask_result = build_segment_mask_from_global_best(sample_df, sample_global_best)
        actual_remaining = int(mask_result['mask'].sum()) if mask_result['mask'] is not None else 0
        
        # 일관성 검증 (예상 = 실제)
        result = validate_segment_filter_consistency(
            df=sample_df,
            global_best=sample_global_best,
            expected_remaining=actual_remaining,
            tolerance=0.05,
        )
        
        assert result['is_valid'] is True
        assert result['actual_remaining'] == actual_remaining
        assert len(result['warnings']) == 0
    
    def test_consistency_check_fail(self, sample_df, sample_global_best):
        """일관성 검증 실패 테스트"""
        from backtester.segment_analysis.segment_apply import validate_segment_filter_consistency
        
        # 잘못된 예상값으로 검증
        result = validate_segment_filter_consistency(
            df=sample_df,
            global_best=sample_global_best,
            expected_remaining=10,  # 실제보다 훨씬 적은 값
            tolerance=0.05,
        )
        
        assert result['is_valid'] is False
        assert len(result['warnings']) > 0
        assert '예측-실제 불일치' in result['warnings'][0]
    
    def test_no_expected_value(self, sample_df, sample_global_best):
        """예상값 없이 검증"""
        from backtester.segment_analysis.segment_apply import validate_segment_filter_consistency
        
        result = validate_segment_filter_consistency(
            df=sample_df,
            global_best=sample_global_best,
            expected_remaining=None,
        )
        
        # 예상값 없으면 일단 유효
        assert result['is_valid'] is True


# =============================================================================
# Test: get_filter_diagnostic_info
# =============================================================================

class TestGetFilterDiagnosticInfo:
    """get_filter_diagnostic_info 테스트"""
    
    def test_diagnostic_info(self, sample_df, sample_global_best):
        """진단 정보 생성 테스트"""
        from backtester.segment_analysis.segment_apply import get_filter_diagnostic_info
        
        result = get_filter_diagnostic_info(sample_df, sample_global_best)
        
        assert result['total_trades'] == len(sample_df)
        assert result['ranges_path_valid'] is True
        assert result['config_mode'] == 'fixed'
        assert '매수등락율' in result['filter_coverage']
        assert result['filter_coverage']['매수등락율'] is True
    
    def test_diagnostic_missing_columns(self, sample_df, sample_global_best):
        """필터 컬럼 누락 진단"""
        from backtester.segment_analysis.segment_apply import get_filter_diagnostic_info
        
        # 존재하지 않는 컬럼 필터 추가
        sample_global_best['combination']['대형주_T1']['filters'].append({
            'column': '없는컬럼',
            'threshold': 100,
            'direction': 'less',
        })
        
        result = get_filter_diagnostic_info(sample_df, sample_global_best)
        
        assert '없는컬럼' in result['filter_coverage']
        assert result['filter_coverage']['없는컬럼'] is False


# =============================================================================
# Test: Integration
# =============================================================================

class TestIntegration:
    """통합 테스트"""
    
    def test_full_workflow(self, sample_df, sample_global_best):
        """전체 워크플로우 테스트"""
        from backtester.segment_analysis.segment_apply import (
            validate_segment_filter_consistency,
            get_filter_diagnostic_info,
            build_segment_mask_from_global_best,
        )
        
        # 1. 진단 정보 확인
        diag = get_filter_diagnostic_info(sample_df, sample_global_best)
        assert diag['total_trades'] > 0
        
        # 2. 마스크 생성
        mask_result = build_segment_mask_from_global_best(sample_df, sample_global_best)
        assert mask_result['error'] is None
        
        # 3. 일관성 검증
        actual_remaining = int(mask_result['mask'].sum())
        validation = validate_segment_filter_consistency(
            df=sample_df,
            global_best=sample_global_best,
            expected_remaining=actual_remaining,
        )
        assert validation['is_valid'] is True
        
        # 4. 필터 적용
        filtered_df = sample_df[mask_result['mask']].copy()
        assert len(filtered_df) == actual_remaining
        
        print(f"\n통합 테스트 결과:")
        print(f"  - 전체 거래 수: {diag['total_trades']}")
        print(f"  - 필터 통과 수: {actual_remaining}")
        print(f"  - 통과율: {actual_remaining / diag['total_trades'] * 100:.1f}%")
        print(f"  - 세그먼트별 통과: {mask_result['segment_trades']}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
