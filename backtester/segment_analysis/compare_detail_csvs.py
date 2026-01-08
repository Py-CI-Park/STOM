#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
세그먼트 필터 예측-실제 괴리 상세 분석

[목적]
- 원본 detail.csv (5,087건): 기존 조건만 적용한 결과
- 예상 detail_segment.csv (1,497건): 세그먼트 필터 적용 예상 결과
- 실제 Filtered detail.csv (2,867건): 실제 백테스트 결과

[분석]
1. 예상에서는 제외되었는데 실제에서는 포함된 거래 찾기 (+1,370건)
2. 이 거래들의 세그먼트별 분포 분석
3. 어떤 필터 조건이 적용 안 되었는지 확인
"""

import pandas as pd
from pathlib import Path
import sys


class DetailCSVComparator:
    """detail.csv 파일 비교 분석기"""
    
    def __init__(self, original_dir: Path, filtered_dir: Path):
        """
        Args:
            original_dir: 원본 백테스트 결과 디렉토리 (stock_bt_Min_B_Study_251227_20260107210544)
            filtered_dir: Filtered 백테스트 결과 디렉토리 (stock_bt_Min_B_Study_251227_Filtered_20260107215836)
        """
        self.original_dir = Path(original_dir)
        self.filtered_dir = Path(filtered_dir)
        
        # 파일 경로 설정
        self.original_detail_path = None
        self.segment_detail_path = None
        self.filtered_detail_path = None
        
        self._find_files()
    
    def _find_files(self):
        """필요한 파일들 찾기"""
        # 원본 detail.csv
        for f in self.original_dir.glob("*_detail.csv"):
            if 'segment' not in f.name.lower() and 'filtered' not in f.name.lower():
                self.original_detail_path = f
                break
        
        # 세그먼트 예상 결과 (detail_segment.csv)
        for f in self.original_dir.glob("*_detail_segment.csv"):
            self.segment_detail_path = f
            break
        
        # Filtered 백테스트 결과 (1-2_*_detail.csv 형식)
        for f in self.filtered_dir.glob("1-2_*_detail.csv"):
            self.filtered_detail_path = f
            break
        
        print("=== 파일 경로 ===")
        print(f"원본 detail.csv: {self.original_detail_path}")
        print(f"세그먼트 예상 결과: {self.segment_detail_path}")
        print(f"Filtered 실제 결과: {self.filtered_detail_path}")
        print()
    
    def load_data(self) -> dict:
        """데이터 로드"""
        data = {}
        
        if self.original_detail_path and self.original_detail_path.exists():
            data['original'] = pd.read_csv(self.original_detail_path, encoding='utf-8-sig')
            print(f"원본: {len(data['original'])}건")
        
        if self.segment_detail_path and self.segment_detail_path.exists():
            data['segment'] = pd.read_csv(self.segment_detail_path, encoding='utf-8-sig')
            print(f"세그먼트 예상: {len(data['segment'])}건")
        
        if self.filtered_detail_path and self.filtered_detail_path.exists():
            data['filtered'] = pd.read_csv(self.filtered_detail_path, encoding='utf-8-sig')
            print(f"Filtered 실제: {len(data['filtered'])}건")
        
        return data
    
    def create_trade_key(self, df: pd.DataFrame) -> pd.Series:
        """거래 식별 키 생성 (종목명 + 매수일자 + 매수시간)"""
        # 컬럼명 확인
        name_col = None
        date_col = None
        time_col = None
        
        for col in df.columns:
            if col == '종목명':
                name_col = col
            if col == '매수일자':
                date_col = col
            if col == '매수시간':
                time_col = col
        
        if name_col and date_col and time_col:
            return df[name_col].astype(str) + '_' + df[date_col].astype(str) + '_' + df[time_col].astype(str)
        else:
            print(f"Warning: 키 컬럼을 찾을 수 없음. 사용 가능한 컬럼: {df.columns.tolist()[:10]}")
            # 대체 키 생성 (종목명, 시가총액, 매수시간)
            if '종목명' in df.columns and '매수시간' in df.columns:
                return df['종목명'].astype(str) + '_' + df['매수시간'].astype(str)
            return pd.Series(range(len(df)), dtype=str)
    
    def compare(self, data: dict) -> dict:
        """거래 비교 분석"""
        results = {}
        
        if 'segment' not in data or 'filtered' not in data:
            print("Error: 비교할 데이터가 부족합니다.")
            return results
        
        segment_df = data['segment']
        filtered_df = data['filtered']
        
        # 키 생성
        segment_keys = set(self.create_trade_key(segment_df))
        filtered_keys = set(self.create_trade_key(filtered_df))
        
        # 비교
        common = segment_keys & filtered_keys  # 둘 다 있는 거래
        only_in_segment = segment_keys - filtered_keys  # 예상에만 있는 거래 (제외되어야 하는데 안 됨)
        only_in_filtered = filtered_keys - segment_keys  # 실제에만 있는 거래 (추가됨)
        
        results['common'] = len(common)
        results['only_in_segment'] = len(only_in_segment)
        results['only_in_filtered'] = len(only_in_filtered)
        
        print()
        print("=== 거래 비교 결과 ===")
        print(f"공통 거래: {len(common)}건")
        print(f"예상에만 있는 거래 (실제에서 누락됨): {len(only_in_segment)}건")
        print(f"실제에만 있는 거래 (세그먼트 필터 미적용): {len(only_in_filtered)}건")
        
        # 실제에만 있는 거래 분석 (이것이 문제!)
        if only_in_filtered and 'original' in data:
            print()
            print("=== 세그먼트 필터가 적용 안 된 거래 분석 ===")
            
            original_df = data['original']
            original_keys = self.create_trade_key(original_df)
            original_df['_key'] = original_keys
            
            # 실제에만 있는 거래를 원본에서 찾기
            extra_trades = original_df[original_df['_key'].isin(only_in_filtered)]
            
            if not extra_trades.empty:
                # 시간대별 분포
                time_col = None
                for col in extra_trades.columns:
                    if '매수시간' in col:
                        time_col = col
                        break
                
                if time_col:
                    # 시간대 추출 (HHMMSS -> HH)
                    extra_trades['시간대'] = (extra_trades[time_col] // 10000).astype(int)
                    print("\n시간대별 분포:")
                    print(extra_trades['시간대'].value_counts().sort_index())
                
                # 시가총액 분포
                cap_col = None
                for col in extra_trades.columns:
                    if '시가총액' in col:
                        cap_col = col
                        break
                
                if cap_col:
                    # 시가총액 구간별 분포
                    def get_cap_range(cap):
                        if cap < 1000:
                            return '1000억 미만'
                        elif cap < 5000:
                            return '1000-5000억'
                        elif cap < 10000:
                            return '5000억-1조'
                        else:
                            return '1조 이상'
                    
                    extra_trades['시가총액구간'] = extra_trades[cap_col].apply(get_cap_range)
                    print("\n시가총액 구간별 분포:")
                    print(extra_trades['시가총액구간'].value_counts())
                
                # 수익률 분포
                profit_col = None
                for col in extra_trades.columns:
                    if '수익률' in col:
                        profit_col = col
                        break
                
                if profit_col:
                    print(f"\n추가된 거래의 수익률 통계:")
                    print(f"  평균: {extra_trades[profit_col].mean():.2f}%")
                    print(f"  합계: {extra_trades[profit_col].sum():.2f}%")
                    print(f"  양수: {(extra_trades[profit_col] > 0).sum()}건")
                    print(f"  음수: {(extra_trades[profit_col] < 0).sum()}건")
                
                # 세그먼트별 분포 분석
                print("\n=== 세그먼트별 분포 (시가총액 x 시간대) ===")
                if cap_col and time_col:
                    # 시간대 추출 (HHMMSS -> 시간대 이름)
                    def get_time_segment(time_val):
                        hhmm = time_val // 100  # HHMM
                        if hhmm < 959:
                            return 'T1_092900_095900'
                        elif hhmm < 1029:
                            return 'T2_095900_102900'
                        elif hhmm < 1059:
                            return 'T3_102900_105900'
                        elif hhmm < 1129:
                            return 'T4_105900_112900'
                        else:
                            return 'T5_112900_115900'
                    
                    # 시가총액 세그먼트
                    def get_cap_segment(cap):
                        if cap < 1350.5:
                            return '초소형주'
                        elif cap < 2622.0:
                            return '소형주'
                        elif cap < 6432.0:
                            return '중형주'
                        else:
                            return '대형주'
                    
                    extra_copy = extra_trades.copy()
                    extra_copy['시간세그먼트'] = extra_copy[time_col].apply(get_time_segment)
                    extra_copy['시가총액세그먼트'] = extra_copy[cap_col].apply(get_cap_segment)
                    
                    pivot = pd.crosstab(extra_copy['시가총액세그먼트'], extra_copy['시간세그먼트'])
                    print(pivot)
                    
                    # 수익률 분포
                    if profit_col:
                        print("\n세그먼트별 수익률 합계:")
                        profit_pivot = extra_copy.groupby(['시가총액세그먼트', '시간세그먼트'])[profit_col].sum().unstack(fill_value=0)
                        print(profit_pivot.round(2))
                
                # 샘플 출력
                print(f"\n추가된 거래 샘플 (처음 10건):")
                cols_to_show = ['종목명', '시가총액', '매수시간', '매수일자', '수익률']
                available_cols = [c for c in cols_to_show if c in extra_trades.columns]
                if available_cols:
                    print(extra_trades[available_cols].head(10).to_string())
                
                results['extra_trades'] = extra_trades
        
        return results
    
    def analyze_segment_conditions(self, data: dict, segment_ranges_path: Path = None):
        """세그먼트별 필터 조건 적용 검증"""
        if segment_ranges_path and segment_ranges_path.exists():
            ranges_df = pd.read_csv(segment_ranges_path, encoding='utf-8-sig')
            print("\n=== 세그먼트 범위 정의 ===")
            print(ranges_df.to_string())
        
        # combos.csv 분석
        combos_path = None
        for f in self.original_dir.glob("*_segment_combos.csv"):
            combos_path = f
            break
        
        if combos_path and combos_path.exists():
            combos_df = pd.read_csv(combos_path, encoding='utf-8-sig')
            print("\n=== 세그먼트별 필터 조합 ===")
            print(f"총 {len(combos_df)}개 세그먼트")
            
            # 필터가 적용된 세그먼트
            if 'remaining_trades' in combos_df.columns and 'total_trades' in combos_df.columns:
                filtered_segs = combos_df[combos_df['remaining_trades'] < combos_df['total_trades']]
                print(f"필터 적용된 세그먼트: {len(filtered_segs)}개")
    
    def run(self):
        """전체 분석 실행"""
        print("=" * 80)
        print("세그먼트 필터 예측-실제 괴리 상세 분석")
        print("=" * 80)
        print()
        
        # 데이터 로드
        data = self.load_data()
        
        # 비교 분석
        results = self.compare(data)
        
        # 세그먼트 조건 분석
        ranges_path = None
        for f in self.original_dir.glob("*_segment_ranges.csv"):
            ranges_path = f
            break
        self.analyze_segment_conditions(data, ranges_path)
        
        return results


def main():
    """메인 실행"""
    # 경로 설정
    output_base = Path('backtester/backtesting_output')
    
    original_dir = output_base / 'stock_bt_Min_B_Study_251227_20260107210544'
    filtered_dir = output_base / 'stock_bt_Min_B_Study_251227_Filtered_20260107215836'
    
    if not original_dir.exists():
        print(f"Error: 원본 디렉토리 없음: {original_dir}")
        sys.exit(1)
    
    if not filtered_dir.exists():
        print(f"Error: Filtered 디렉토리 없음: {filtered_dir}")
        sys.exit(1)
    
    comparator = DetailCSVComparator(original_dir, filtered_dir)
    results = comparator.run()
    
    # 결과 요약
    print()
    print("=" * 80)
    print("결론")
    print("=" * 80)
    print()
    
    if 'only_in_filtered' in results:
        extra = results['only_in_filtered']
        print(f"세그먼트 필터가 적용되지 않은 거래: {extra}건")
        print()
        print("이 거래들은 세그먼트 분석에서 '제외'로 판정되었지만,")
        print("실제 Filtered 백테스트에서는 포함되었습니다.")
        print()
        print("가능한 원인:")
        print("1. 세그먼트 필터 코드가 정확히 생성되지 않음")
        print("2. 런타임 변수 계산 값이 분석 시점과 다름")
        print("3. 세그먼트 경계값 불일치")


if __name__ == '__main__':
    main()
