# -*- coding: utf-8 -*-
"""
Segmentation Module - 세그먼트 분할 모듈

시가총액/시간 구간 기반 데이터 세그먼트 분할:
- 시가총액: 소형주(<3000억), 중형주(3000-10000억), 대형주(≥10000억)
- 시간: T1(09:00-05), T2(09:05-10), T3(09:10-15), T4(09:15-20)
- 총 12개 세그먼트 생성 (3 × 4)

Research: docs/Study/ResearchReports/2025-12-20_Segmented_Filter_Optimization_Research.md
Author: Claude Code
Date: 2025-12-20
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, time
import re
from typing import Any, Dict, List, Tuple, Optional
import pandas as pd
import numpy as np


@dataclass
class SegmentConfig:
    """
    세그먼트 분할 설정

    시가총액/시간 구간 설정은 연구용 사례이며,
    조건식과 시장환경에 따라 변경될 수 있음.
    """

    # 시가총액 구간 (억원 단위)
    market_cap_ranges: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        '소형주': (0, 3000),          # < 3000억
        '중형주': (3000, 10000),      # 3000~10000억
        '대형주': (10000, float('inf'))  # >= 10000억
    })

    # 시간 구간 (시분초 형식: HHMMSS)
    time_ranges: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        'T1_090000_090500': (90000, 90500),  # 09:00:00 ~ 09:05:00
        'T2_090500_091000': (90500, 91000),  # 09:05:00 ~ 09:10:00
        'T3_091000_091500': (91000, 91500),  # 09:10:00 ~ 09:15:00
        'T4_091500_092000': (91500, 92000),  # 09:15:00 ~ 09:20:00
    })

    # 최소 거래수 제약
    min_trades: Dict[str, Any] = field(default_factory=lambda: {
        'absolute_min': 30,         # 대표본 구간 최소치
        'small_segment_min': 10,    # 소표본 구간 완화 최소치
        'relative_min': 0.15,       # 세그먼트 내 거래의 15% 이상 유지
    })

    # 최대 제외율 제약
    max_exclusion: Dict[str, float] = field(default_factory=lambda: {
        'per_segment': 0.85,        # 세그먼트별 최대 85% 제외
        'global': 0.90,             # 전체 최대 90% 제외
        'adaptive': True            # 세그먼트 크기에 따라 조정
    })

    # 세그먼트 검증 설정
    validation: Dict[str, bool] = field(default_factory=lambda: {
        'check_min_trades': True,    # 최소 거래수 검증
        'warn_imbalance': True,      # 불균형 경고
        'auto_merge_small': False,   # 소규모 세그먼트 자동 병합 (기본 False)
        'track_out_of_range': True,  # 구간 외 데이터 비중 추적
    })

    # 반-동적 분할 옵션
    dynamic_mode: str = 'fixed'  # fixed | semi | dynamic | time_only
    dynamic_market_cap_quantiles: Tuple[float, float] = (0.33, 0.66)
    dynamic_time_quantiles: Tuple[float, float, float] = (0.25, 0.5, 0.75)
    dynamic_min_samples: int = 200

    def get_dynamic_min_trades(self, segment_size: int) -> int:
        """
        세그먼트 크기에 따른 동적 최소 거래수 계산

        Args:
            segment_size: 세그먼트 내 총 거래수

        Returns:
            동적으로 계산된 최소 거래수
        """
        relative_min = int(segment_size * self.min_trades['relative_min'])
        return max(
            self.min_trades['small_segment_min'],
            min(self.min_trades['absolute_min'], relative_min)
        )


class SegmentBuilder:
    """
    세그먼트 분할 실행 클래스

    detail.csv 데이터를 시가총액/시간 기준으로 12개 세그먼트로 분할
    """

    def __init__(self, config: Optional[SegmentConfig] = None):
        """
        Args:
            config: 세그먼트 설정 (기본값 사용 가능)
        """
        self.config = config or SegmentConfig()
        self.segments: Dict[str, pd.DataFrame] = {}
        self.segment_stats: Dict[str, dict] = {}
        self.out_of_range: pd.DataFrame = pd.DataFrame()
        self.runtime_market_cap_ranges: Dict[str, Tuple[float, float]] = {}
        self.runtime_time_ranges: Dict[str, Tuple[int, int]] = {}
        self.range_summary: pd.DataFrame = pd.DataFrame()
        self.dynamic_flags = {'market_cap': False, 'time': False}

    def build_segments(self, df_detail: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        detail 데이터를 12개 세그먼트로 분할

        Args:
            df_detail: 백테스팅 detail.csv 데이터프레임
                필수 컬럼: 시가총액, 매수시간 (또는 매수시/매수분/매수초)

        Returns:
            세그먼트 ID → DataFrame 딕셔너리

        Raises:
            ValueError: 필수 컬럼 누락 또는 데이터 부족
        """
        # 1. 필수 컬럼 검증
        self._validate_columns(df_detail)

        # 2. 시분초 컬럼 생성 (없으면)
        df_work = self._prepare_time_column(df_detail.copy())

        # 2-1. 반-동적 분할 범위 적용
        self._refresh_ranges(df_work)

        # 3. 세그먼트 ID 할당
        df_work['세그먼트ID'] = self._assign_segment_ids(df_work)

        out_of_range_data = df_work[df_work['세그먼트ID'] == 'Out_of_Range'].copy()
        self.out_of_range = out_of_range_data

        # 4. 세그먼트별 분할
        segments = {}
        for seg_id in self._get_all_segment_ids():
            seg_data = df_work[df_work['세그먼트ID'] == seg_id].copy()
            segments[seg_id] = seg_data

        # 5. 세그먼트 검증 및 통계
        self._validate_segments(segments, len(df_work), out_of_range_data=out_of_range_data)

        self.segments = segments
        return segments

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """필수 컬럼 검증"""
        required = ['시가총액']
        time_cols_option1 = ['매수시간']
        time_cols_option2 = ['매수시', '매수분', '매수초']

        # 시가총액 필수
        if '시가총액' not in df.columns:
            raise ValueError("필수 컬럼 누락: '시가총액'")

        # 시간 컬럼 중 하나 필수
        has_time = ('매수시간' in df.columns or
                    all(c in df.columns for c in time_cols_option2))

        if not has_time:
            raise ValueError(
                "필수 시간 컬럼 누락: '매수시간' 또는 ('매수시', '매수분', '매수초')"
            )

    def _prepare_time_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        시분초 컬럼 준비 (HHMMSS 형식)

        매수시간 컬럼이 있으면 파싱, 없으면 매수시/매수분/매수초로 조합
        """
        if '시분초' in df.columns:
            return df

        def _sanitize_hhmmss(series: pd.Series) -> pd.Series:
            hh = series // 10000
            mm = (series // 100) % 100
            ss = series % 100
            valid = (hh.between(0, 23) & mm.between(0, 59) & ss.between(0, 59))
            return series.where(valid)

        def _parse_time_value(value) -> Optional[int]:
            if pd.isna(value):
                return None

            if isinstance(value, (pd.Timestamp, datetime)):
                return value.hour * 10000 + value.minute * 100 + value.second

            if isinstance(value, time):
                return value.hour * 10000 + value.minute * 100 + value.second

            digits = None
            if isinstance(value, (int, np.integer)):
                digits = str(int(value))
            elif isinstance(value, (float, np.floating)):
                digits = str(int(value))
            else:
                text = str(value).strip()
                if not text:
                    return None

                if any(sep in text for sep in (':', '-', '/', 'T', ' ')):
                    ts = pd.to_datetime(text, errors='coerce')
                    if not pd.isna(ts):
                        return ts.hour * 10000 + ts.minute * 100 + ts.second

                digits = re.sub(r'\D', '', text)
            if not digits:
                return None

            if len(digits) >= 14:
                digits = digits[-6:]
            elif len(digits) == 12:
                digits = digits[-4:] + '00'
            elif len(digits) == 10:
                digits = digits[-4:] + '00'
            elif len(digits) == 8:
                return None
            elif len(digits) == 6:
                pass
            elif len(digits) == 5:
                digits = digits.zfill(6)
            elif len(digits) == 4:
                digits = digits + '00'
            else:
                digits = digits.zfill(6)

            try:
                hhmmss = int(digits)
            except ValueError:
                return None

            hh = hhmmss // 10000
            mm = (hhmmss // 100) % 100
            ss = hhmmss % 100
            if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59):
                return None

            return hhmmss

        if '매수시간' in df.columns:
            df['시분초'] = df['매수시간'].apply(_parse_time_value)

            if df['시분초'].isna().any() and all(c in df.columns for c in ['매수시', '매수분', '매수초']):
                fallback = (
                    pd.to_numeric(df['매수시'], errors='coerce').fillna(0).astype(int) * 10000 +
                    pd.to_numeric(df['매수분'], errors='coerce').fillna(0).astype(int) * 100 +
                    pd.to_numeric(df['매수초'], errors='coerce').fillna(0).astype(int)
                )
                fallback = _sanitize_hhmmss(fallback)
                df['시분초'] = df['시분초'].fillna(fallback)

        elif all(c in df.columns for c in ['매수시', '매수분', '매수초']):
            df['시분초'] = (
                pd.to_numeric(df['매수시'], errors='coerce').fillna(0).astype(int) * 10000 +
                pd.to_numeric(df['매수분'], errors='coerce').fillna(0).astype(int) * 100 +
                pd.to_numeric(df['매수초'], errors='coerce').fillna(0).astype(int)
            )
            df['시분초'] = _sanitize_hhmmss(df['시분초'])

        # 유효하지 않은 시간 제거
        df = df[df['시분초'].notna()].copy()
        df['시분초'] = df['시분초'].astype(int)

        return df

    def _assign_segment_ids(self, df: pd.DataFrame) -> pd.Series:
        """
        각 거래에 세그먼트 ID 할당

        Returns:
            세그먼트 ID 시리즈 (예: "소형주_T1_090000_090500")
        """
        segment_ids = pd.Series(['Unknown'] * len(df), index=df.index)

        # 시가총액 구간 결정
        cap_segments = pd.Series(['Unknown'] * len(df), index=df.index)
        for cap_name, (cap_min, cap_max) in self.runtime_market_cap_ranges.items():
            mask = (df['시가총액'] >= cap_min) & (df['시가총액'] < cap_max)
            cap_segments[mask] = cap_name

        # 시간 구간 결정
        time_segments = pd.Series(['Unknown'] * len(df), index=df.index)
        for time_name, (time_min, time_max) in self.runtime_time_ranges.items():
            mask = (df['시분초'] >= time_min) & (df['시분초'] < time_max)
            time_segments[mask] = time_name

        # 조합하여 세그먼트 ID 생성
        segment_ids = cap_segments + '_' + time_segments

        # Unknown 필터링 (구간 외 데이터)
        segment_ids[segment_ids.str.contains('Unknown')] = 'Out_of_Range'

        return segment_ids

    def _get_all_segment_ids(self) -> List[str]:
        """모든 가능한 세그먼트 ID 목록 생성"""
        segment_ids = []
        for cap_name in self.runtime_market_cap_ranges.keys():
            for time_name in self.runtime_time_ranges.keys():
                segment_ids.append(f"{cap_name}_{time_name}")
        return segment_ids

    def _validate_segments(self, segments: Dict[str, pd.DataFrame],
                          total_trades: int,
                          out_of_range_data: Optional[pd.DataFrame] = None) -> None:
        """
        세그먼트 검증 및 통계 생성

        - 최소 거래수 검증
        - 불균형 경고
        - 통계 정보 수집
        """
        stats = {}
        warnings = []

        for seg_id, seg_data in segments.items():
            n_trades = len(seg_data)

            # 동적 최소 거래수
            min_required = self.config.get_dynamic_min_trades(n_trades)

            # 기본 통계
            stat = {
                'segment_id': seg_id,
                'trades': n_trades,
                'ratio': n_trades / total_trades if total_trades > 0 else 0,
                'min_required': min_required,
                'valid': n_trades >= min_required,
            }

            # 수익금 통계 (있으면)
            if '수익금' in seg_data.columns and n_trades > 0:
                stat.update({
                    'total_profit': seg_data['수익금'].sum(),
                    'avg_profit': seg_data['수익금'].mean(),
                    'std_profit': seg_data['수익금'].std(),
                })

            # 승률 (있으면)
            if '수익금' in seg_data.columns and n_trades > 0:
                stat['winrate'] = (seg_data['수익금'] > 0).sum() / n_trades * 100

            stats[seg_id] = stat

            # 경고 수집
            if self.config.validation['check_min_trades'] and not stat['valid']:
                warnings.append(
                    f"[WARNING] {seg_id}: {n_trades}건 (최소 {min_required}건 필요)"
                )

            # 불균형 경고 (1% 미만)
            if (self.config.validation['warn_imbalance'] and
                stat['ratio'] < 0.01 and n_trades > 0):
                warnings.append(
                    f"[WARNING] {seg_id}: 전체의 {stat['ratio']*100:.2f}% (불균형)"
                )

        self.segment_stats = stats

        if (self.config.validation.get('track_out_of_range', True) and
                out_of_range_data is not None and len(out_of_range_data) > 0):
            n_trades = len(out_of_range_data)
            stat = {
                'segment_id': 'Out_of_Range',
                'trades': n_trades,
                'ratio': n_trades / total_trades if total_trades > 0 else 0,
                'min_required': 0,
                'valid': False,
                'note': '범위 외 데이터',
            }
            if '수익금' in out_of_range_data.columns:
                stat.update({
                    'total_profit': out_of_range_data['수익금'].sum(),
                    'avg_profit': out_of_range_data['수익금'].mean(),
                    'std_profit': out_of_range_data['수익금'].std(),
                })
                stat['winrate'] = (out_of_range_data['수익금'] > 0).sum() / n_trades * 100
            self.segment_stats['Out_of_Range'] = stat

        # 경고 출력
        if warnings:
            print("\n[세그먼트 검증 경고]")
            for w in warnings[:10]:  # 최대 10개
                print(w)
            if len(warnings) > 10:
                print(f"... 외 {len(warnings)-10}개 경고")

    def get_segment_summary(self) -> pd.DataFrame:
        """
        세그먼트별 요약 통계 반환

        Returns:
            세그먼트 통계 DataFrame
        """
        if not self.segment_stats:
            raise ValueError("build_segments()를 먼저 실행하세요.")

        return pd.DataFrame.from_dict(
            self.segment_stats,
            orient='index'
        ).reset_index(drop=True)

    def get_range_summary_df(self) -> pd.DataFrame:
        """
        세그먼트 분할에 사용된 구간 요약을 반환
        """
        if self.range_summary is None or self.range_summary.empty:
            self.range_summary = self._build_range_summary()
        return self.range_summary.copy()

    def get_valid_segments(self) -> Dict[str, pd.DataFrame]:
        """
        최소 거래수 조건을 만족하는 유효 세그먼트만 반환

        Returns:
            유효 세그먼트 딕셔너리
        """
        if not self.segments:
            raise ValueError("build_segments()를 먼저 실행하세요.")

        valid = {}
        for seg_id, seg_data in self.segments.items():
            stat = self.segment_stats.get(seg_id, {})
            if stat.get('valid', False):
                valid[seg_id] = seg_data

        return valid

    def save_segments(self, output_dir: str, prefix: str = 'segment') -> List[str]:
        """
        세그먼트별 CSV 파일 저장

        Args:
            output_dir: 출력 디렉토리
            prefix: 파일명 접두사

        Returns:
            저장된 파일 경로 목록
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        saved_files = []
        for seg_id, seg_data in self.segments.items():
            if len(seg_data) > 0:
                # 파일명 정리 (특수문자 제거)
                safe_id = seg_id.replace('_', '-')
                filepath = os.path.join(output_dir, f"{prefix}_{safe_id}.csv")
                seg_data.to_csv(filepath, index=False, encoding='utf-8-sig')
                saved_files.append(filepath)

        # 요약 통계 저장
        summary_path = os.path.join(output_dir, f"{prefix}_summary.csv")
        self.get_segment_summary().to_csv(
            summary_path, index=False, encoding='utf-8-sig'
        )
        saved_files.append(summary_path)

        return saved_files

    def _refresh_ranges(self, df: pd.DataFrame) -> None:
        """
        설정에 따라 고정/반-동적 분할 범위를 갱신
        """
        self.runtime_market_cap_ranges = dict(self.config.market_cap_ranges)
        self.runtime_time_ranges = dict(self.config.time_ranges)
        self.dynamic_flags = {'market_cap': False, 'time': False}

        mode = str(self.config.dynamic_mode or 'fixed').lower()
        dynamic_cap = mode in ('semi', 'semi_dynamic', 'semi-dynamic', 'dynamic', 'all', 'market')
        dynamic_time = mode in ('dynamic', 'all', 'time', 'time_only', 'time_dynamic')

        if dynamic_cap:
            ranges = self._build_dynamic_market_cap_ranges(df)
            if ranges:
                self.runtime_market_cap_ranges = ranges
                self.dynamic_flags['market_cap'] = True

        if dynamic_time:
            ranges = self._build_dynamic_time_ranges(df)
            if ranges:
                self.runtime_time_ranges = ranges
                self.dynamic_flags['time'] = True

        self.range_summary = self._build_range_summary()

    def _build_dynamic_market_cap_ranges(self, df: pd.DataFrame) -> Optional[Dict[str, Tuple[float, float]]]:
        series = pd.to_numeric(df.get('시가총액'), errors='coerce').dropna()
        if series.size < self.config.dynamic_min_samples:
            return None

        q1, q2 = self.config.dynamic_market_cap_quantiles
        try:
            v1 = float(series.quantile(q1))
            v2 = float(series.quantile(q2))
        except Exception:
            return None

        base_min = min(r[0] for r in self.config.market_cap_ranges.values())
        if not (v1 > base_min and v2 > v1):
            return None

        return {
            '소형주': (base_min, v1),
            '중형주': (v1, v2),
            '대형주': (v2, float('inf')),
        }

    def _build_dynamic_time_ranges(self, df: pd.DataFrame) -> Optional[Dict[str, Tuple[int, int]]]:
        series = pd.to_numeric(df.get('시분초'), errors='coerce').dropna()
        if series.size < self.config.dynamic_min_samples:
            return None

        base_min = min(r[0] for r in self.config.time_ranges.values())
        base_max = max(r[1] for r in self.config.time_ranges.values())
        series = series[(series >= base_min) & (series < base_max)]
        if series.size < self.config.dynamic_min_samples:
            return None

        qs = list(self.config.dynamic_time_quantiles)
        if len(qs) != 3:
            return None

        try:
            q_values = [int(series.quantile(q)) for q in qs]
        except Exception:
            return None

        boundaries = [int(base_min)] + q_values + [int(base_max)]
        if len(set(boundaries)) < 5:
            return None
        if not all(boundaries[i] < boundaries[i + 1] for i in range(len(boundaries) - 1)):
            return None

        labels = []
        for label in self.config.time_ranges.keys():
            prefix = str(label).split('_')[0]
            labels.append(prefix)

        if len(labels) != 4:
            labels = ['T1', 'T2', 'T3', 'T4']

        ranges: Dict[str, Tuple[int, int]] = {}
        for idx, prefix in enumerate(labels):
            start = boundaries[idx]
            end = boundaries[idx + 1]
            name = f"{prefix}_{start:06d}_{end:06d}"
            ranges[name] = (start, end)
        return ranges

    def _build_range_summary(self) -> pd.DataFrame:
        rows = []
        cap_source = 'dynamic' if self.dynamic_flags.get('market_cap') else 'fixed'
        time_source = 'dynamic' if self.dynamic_flags.get('time') else 'fixed'

        for label, (min_v, max_v) in self.runtime_market_cap_ranges.items():
            rows.append({
                'range_type': 'market_cap',
                'label': label,
                'min': float(min_v),
                'max': float(max_v) if max_v != float('inf') else None,
                'source': cap_source,
            })

        for label, (min_v, max_v) in self.runtime_time_ranges.items():
            rows.append({
                'range_type': 'time',
                'label': label,
                'min': int(min_v),
                'max': int(max_v),
                'source': time_source,
            })

        return pd.DataFrame(rows)


# ============================================================================
# 유틸리티 함수
# ============================================================================

def create_segment_matrix_view(segment_stats: pd.DataFrame) -> pd.DataFrame:
    """
    세그먼트 통계를 매트릭스 뷰로 변환

    Args:
        segment_stats: get_segment_summary() 결과

    Returns:
        시가총액(행) × 시간(열) 매트릭스
    """
    if segment_stats.empty:
        return pd.DataFrame()

    segment_stats = segment_stats[segment_stats['segment_id'] != 'Out_of_Range']

    # segment_id 파싱
    segment_stats = segment_stats.copy()
    segment_stats['시가총액'] = segment_stats['segment_id'].str.split('_').str[0]
    segment_stats['시간대'] = segment_stats['segment_id'].str.split('_').str[1]

    # 피벗 테이블
    matrix = segment_stats.pivot_table(
        index='시가총액',
        columns='시간대',
        values='trades',
        fill_value=0
    )

    # 행/열 정렬
    row_order = ['소형주', '중형주', '대형주']
    col_order = ['T1', 'T2', 'T3', 'T4']

    matrix = matrix.reindex(
        index=[r for r in row_order if r in matrix.index],
        columns=[c for c in col_order if c in matrix.columns]
    )

    return matrix


if __name__ == '__main__':
    """
    테스트 실행 예시
    """
    # 샘플 데이터 생성
    np.random.seed(42)
    n_samples = 1000

    sample_data = pd.DataFrame({
        '시가총액': np.random.choice([1000, 5000, 15000], n_samples),
        '매수시': np.random.choice([9], n_samples),
        '매수분': np.random.choice([0, 5, 10, 15], n_samples),
        '매수초': np.random.randint(0, 60, n_samples),
        '수익금': np.random.randn(n_samples) * 100000,
    })

    # 세그먼트 분할
    builder = SegmentBuilder()
    segments = builder.build_segments(sample_data)

    # 요약 통계
    summary = builder.get_segment_summary()
    print("\n[세그먼트 요약]")
    print(summary[['segment_id', 'trades', 'ratio', 'valid']])

    # 매트릭스 뷰
    matrix = create_segment_matrix_view(summary)
    print("\n[세그먼트 매트릭스 - 거래수]")
    print(matrix)
