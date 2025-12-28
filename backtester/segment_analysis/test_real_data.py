# -*- coding: utf-8 -*-
"""
실제 백테스팅 데이터로 세그먼트 분할 테스트
"""

import sys
from typing import Optional
import pandas as pd
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backtester.segment_analysis import SegmentConfig, SegmentBuilder
from backtester.segment_analysis.segmentation import create_segment_matrix_view


def _resolve_detail_path(cli_path: Optional[str]) -> Path:
    if cli_path:
        return Path(cli_path).expanduser().resolve()

    graph_dir = Path(__file__).resolve().parent.parent / 'graph'
    candidates = sorted(graph_dir.glob('*_detail.csv'),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True)
    if not candidates:
        raise FileNotFoundError("graph 폴더에서 detail.csv 파일을 찾지 못했습니다.")
    return candidates[0]


def main():
    # 최신 detail.csv 파일 로드 (또는 CLI 지정)
    detail_path = _resolve_detail_path(sys.argv[1] if len(sys.argv) > 1 else None)

    print(f"Loading: {detail_path.name}")
    df_detail = pd.read_csv(detail_path, encoding='utf-8-sig')
    print(f"Total trades: {len(df_detail):,}")

    # 필수 컬럼 확인
    print(f"\nColumns preview: {df_detail.columns[:10].tolist()}")

    # 데이터 샘플 확인
    if '시가총액' in df_detail.columns:
        print(f"\n시가총액 범위: {df_detail['시가총액'].min():.0f} ~ {df_detail['시가총액'].max():.0f}")
        print(f"시가총액 분포:")
        print(f"  초소형주(<2500): {(df_detail['시가총액'] < 2500).sum():,}건")
        print(f"  소형주(2500-5000): {((df_detail['시가총액'] >= 2500) & (df_detail['시가총액'] < 5000)).sum():,}건")
        print(f"  중형주(5000-10000): {((df_detail['시가총액'] >= 5000) & (df_detail['시가총액'] < 10000)).sum():,}건")
        print(f"  대형주(>=10000): {(df_detail['시가총액'] >= 10000).sum():,}건")

    # 세그먼트 분할
    print("\n" + "="*60)
    print("세그먼트 분할 실행...")
    print("="*60)

    builder = SegmentBuilder()
    segments = builder.build_segments(df_detail)

    # 요약 통계
    summary = builder.get_segment_summary()
    print("\n[세그먼트 요약]")
    display_cols = ['segment_id', 'trades', 'ratio', 'valid']
    if 'winrate' in summary.columns:
        display_cols.append('winrate')
    print(summary[display_cols].to_string())

    # 매트릭스 뷰
    matrix = create_segment_matrix_view(summary)
    print("\n[세그먼트 매트릭스 - 거래수]")
    print(matrix.to_string())

    # 유효 세그먼트 수
    valid_segments = builder.get_valid_segments()
    print(f"\n유효 세그먼트: {len(valid_segments)}/12")

    # 전체 대비 유효 데이터 비율
    total_valid_trades = sum(len(seg) for seg in valid_segments.values())
    print(f"유효 거래수: {total_valid_trades:,}/{len(df_detail):,} " +
          f"({total_valid_trades/len(df_detail)*100:.1f}%)")


if __name__ == '__main__':
    main()
