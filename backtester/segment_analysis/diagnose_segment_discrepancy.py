"""
세그먼트 필터 예측-실제 괴리 진단 스크립트

목적:
1. 거래 수 단계별 분석 (원본 → 기존조건 → 세그먼트필터 → Filtered)
2. 변수 값 비교 (분석 시 vs 런타임)
3. 세그먼트별 거래 매칭

사용법:
    python diagnose_segment_discrepancy.py <original_output_dir> <filtered_output_dir>

예시:
    python diagnose_segment_discrepancy.py \
        stock_bt_Min_B_Study_251227_20260107210544 \
        stock_bt_Min_B_Study_251227_Filtered_20260107215836
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SegmentRange:
    """세그먼트 경계값"""
    label: str
    min_val: float
    max_val: Optional[float]


@dataclass
class DiagnosisResult:
    """진단 결과"""
    original_count: int
    after_existing_cond: int
    after_segment_filter: int
    filtered_count: int
    segment_breakdown: Dict[str, Dict]
    variable_comparison: Dict[str, Dict]
    recommendations: List[str]


class SegmentDiscrepancyDiagnoser:
    """세그먼트 필터 괴리 진단기"""
    
    # 시가총액 경계값 (ranges.csv 기준)
    CAP_RANGES = [
        SegmentRange('초소형주', 0, 1350.5),
        SegmentRange('소형주', 1350.5, 2622),
        SegmentRange('중형주', 2622, 6432),
        SegmentRange('대형주', 6432, None),
    ]
    
    # 시간대 경계값
    TIME_RANGES = [
        SegmentRange('T1_092900_095900', 92900, 95900),
        SegmentRange('T2_095900_102900', 95900, 102900),
        SegmentRange('T3_102900_105900', 102900, 105900),
        SegmentRange('T4_105900_112900', 105900, 112900),
        SegmentRange('T5_112900_115900', 112900, 115900),
    ]
    
    # 전체 제외 세그먼트
    EXCLUDED_SEGMENTS = {
        '초소형주_T1_092900_095900',
        '초소형주_T2_095900_102900',
        '초소형주_T4_105900_112900',
        '초소형주_T5_112900_115900',
        '소형주_T1_092900_095900',
        '중형주_T1_092900_095900',
    }
    
    def __init__(self, original_dir: Path, filtered_dir: Path, output_base: Path):
        self.original_dir = original_dir
        self.filtered_dir = filtered_dir
        self.output_base = output_base
        
        self.df_original: Optional[pd.DataFrame] = None
        self.df_filtered: Optional[pd.DataFrame] = None
        self.segment_filters: Optional[pd.DataFrame] = None
        self.segment_combos: Optional[pd.DataFrame] = None
        
    def load_data(self) -> bool:
        """데이터 로드"""
        print("\n=== 데이터 로드 ===")
        
        # 원본 detail.csv 찾기
        original_details = list(self.original_dir.glob('*_detail.csv'))
        if not original_details:
            print(f"ERROR: 원본 detail.csv를 찾을 수 없음: {self.original_dir}")
            return False
        
        # 가장 큰 파일 선택 (segment가 아닌 것)
        original_detail = None
        for f in sorted(original_details, key=lambda x: x.stat().st_size, reverse=True):
            if 'segment' not in f.name and 'filtered' not in f.name.lower():
                original_detail = f
                break
        
        if original_detail is None:
            original_detail = original_details[0]
        
        print(f"원본 파일: {original_detail.name}")
        self.df_original = pd.read_csv(original_detail)
        print(f"  - 거래 수: {len(self.df_original):,}건")
        
        # Filtered detail.csv 찾기
        filtered_details = list(self.filtered_dir.glob('*_detail.csv'))
        if not filtered_details:
            print(f"WARNING: Filtered detail.csv를 찾을 수 없음: {self.filtered_dir}")
        else:
            filtered_detail = None
            for f in sorted(filtered_details, key=lambda x: x.stat().st_size, reverse=True):
                if 'segment' not in f.name and 'filtered' not in f.name.lower():
                    filtered_detail = f
                    break
            if filtered_detail is None:
                filtered_detail = filtered_details[0]
            
            print(f"Filtered 파일: {filtered_detail.name}")
            self.df_filtered = pd.read_csv(filtered_detail)
            print(f"  - 거래 수: {len(self.df_filtered):,}건")
        
        # 세그먼트 필터 정보 로드
        segment_filters = list(self.original_dir.glob('*dynamic_semi_segment_filters.csv'))
        if segment_filters:
            self.segment_filters = pd.read_csv(segment_filters[0])
            print(f"세그먼트 필터: {segment_filters[0].name}")
        
        segment_combos = list(self.original_dir.glob('*dynamic_semi_segment_combos.csv'))
        if segment_combos:
            self.segment_combos = pd.read_csv(segment_combos[0])
            print(f"세그먼트 조합: {segment_combos[0].name}")
        
        return True
    
    def _get_segment_label(self, cap: float, time: int) -> str:
        """시가총액과 시간으로 세그먼트 라벨 반환"""
        cap_label = '범위외'
        for cr in self.CAP_RANGES:
            if cr.max_val is None:
                if cap >= cr.min_val:
                    cap_label = cr.label
                    break
            elif cr.min_val <= cap < cr.max_val:
                cap_label = cr.label
                break
        
        time_label = '범위외'
        for tr in self.TIME_RANGES:
            if tr.min_val <= time < tr.max_val:
                time_label = tr.label
                break
        
        return f"{cap_label}_{time_label}"
    
    def _simulate_existing_conditions(self, df: pd.DataFrame) -> pd.Series:
        """
        기존 매수 조건 시뮬레이션 (Min_B_Study_251227 기반)
        
        주요 조건:
        - 관심종목 == 1
        - 0 < 현재가 <= 50000
        - 1.0 < 등락율 <= 20.0
        - 시분초 < 120000
        - 시가총액 < 100000 (10조)
        """
        mask = pd.Series([True] * len(df), index=df.index)
        
        # 컬럼 존재 여부 확인 및 조건 적용
        col_mapping = {
            '관심종목': lambda x: x == 1,
            '매수가': lambda x: (x > 0) & (x <= 50000),  # 현재가 대용
            '매수등락율': lambda x: (x > 1.0) & (x <= 20.0),  # 등락율 대용
        }
        
        # 시분초 추출 (매수시간에서)
        if '매수시간' in df.columns:
            # 매수시간 형식: YYYYMMDDHHMMSS 또는 HHMMSS
            try:
                time_str = df['매수시간'].astype(str)
                if time_str.str.len().iloc[0] > 6:
                    # YYYYMMDDHHMMSS 형식
                    시분초 = time_str.str[-6:].astype(int)
                else:
                    시분초 = time_str.astype(int)
                mask &= (시분초 < 120000)
            except:
                pass
        
        # 시가총액 조건
        if '시가총액' in df.columns:
            mask &= (df['시가총액'] < 100000)  # 10조 미만
        
        # 등락율 조건
        if '매수등락율' in df.columns:
            mask &= (df['매수등락율'] > 1.0) & (df['매수등락율'] <= 20.0)
        
        return mask
    
    def _simulate_segment_filter(self, df: pd.DataFrame) -> pd.Series:
        """
        세그먼트 필터 시뮬레이션
        
        세그먼트별로 정의된 필터 조건 적용
        """
        mask = pd.Series([False] * len(df), index=df.index)
        
        # 시분초 추출
        if '매수시간' in df.columns:
            try:
                time_str = df['매수시간'].astype(str)
                if time_str.str.len().iloc[0] > 6:
                    시분초 = time_str.str[-6:].astype(int)
                else:
                    시분초 = time_str.astype(int)
            except:
                return mask
        else:
            return mask
        
        시가총액 = df['시가총액'] if '시가총액' in df.columns else pd.Series([0] * len(df))
        
        # 각 세그먼트별로 필터 적용
        for tr in self.TIME_RANGES:
            time_mask = (시분초 >= tr.min_val) & (시분초 < tr.max_val)
            
            for cr in self.CAP_RANGES:
                if cr.max_val is None:
                    cap_mask = 시가총액 >= cr.min_val
                else:
                    cap_mask = (시가총액 >= cr.min_val) & (시가총액 < cr.max_val)
                
                segment_mask = time_mask & cap_mask
                segment_label = f"{cr.label}_{tr.label}"
                
                if segment_label in self.EXCLUDED_SEGMENTS:
                    # 전체 제외 세그먼트: 모두 False
                    continue
                else:
                    # 필터 적용 세그먼트: 해당 세그먼트 거래는 일단 포함
                    # (실제 필터 조건은 여기서 단순화)
                    mask |= segment_mask
        
        return mask
    
    def analyze_trade_counts(self) -> Dict:
        """Phase 1-1: 거래 수 단계별 분석"""
        print("\n=== Phase 1-1: 거래 수 단계별 분석 ===")
        
        df = self.df_original.copy()
        results = {}
        
        # 1. 원본 거래 수
        results['original'] = len(df)
        print(f"1. 원본 거래 수: {results['original']:,}건")
        
        # 2. 기존 조건 적용 후
        existing_mask = self._simulate_existing_conditions(df)
        results['after_existing'] = existing_mask.sum()
        print(f"2. 기존 조건 적용 후: {results['after_existing']:,}건 (제외 {results['original'] - results['after_existing']:,}건)")
        
        # 3. 세그먼트 필터만 적용 (기존 조건 무시)
        segment_mask = self._simulate_segment_filter(df)
        results['segment_only'] = segment_mask.sum()
        print(f"3. 세그먼트 필터만 적용: {results['segment_only']:,}건 (제외 {results['original'] - results['segment_only']:,}건)")
        
        # 4. 기존 조건 + 세그먼트 필터 (현재 구조)
        combined_mask = existing_mask & segment_mask
        results['combined_current'] = combined_mask.sum()
        print(f"4. 기존+세그먼트 (현재): {results['combined_current']:,}건")
        
        # 5. 실제 Filtered 결과
        results['filtered_actual'] = len(self.df_filtered) if self.df_filtered is not None else 0
        print(f"5. 실제 Filtered 결과: {results['filtered_actual']:,}건")
        
        # 6. 세그먼트 분석 예상 (combos.csv)
        if self.segment_combos is not None and 'remaining_trades' in self.segment_combos.columns:
            results['segment_expected'] = int(self.segment_combos['remaining_trades'].iloc[0])
        else:
            results['segment_expected'] = 1497  # 기본값
        print(f"6. 세그먼트 분석 예상: {results['segment_expected']:,}건")
        
        # 괴리 분석
        print("\n--- 괴리 분석 ---")
        diff_expected_actual = results['filtered_actual'] - results['segment_expected']
        print(f"예상 vs 실제 차이: {diff_expected_actual:+,}건 ({diff_expected_actual/results['segment_expected']*100:+.1f}%)")
        
        # 핵심 발견
        print("\n--- 핵심 발견 ---")
        if results['after_existing'] < results['original'] * 0.8:
            print(f"[!] 기존 조건이 많은 거래를 제외: {results['original'] - results['after_existing']:,}건 ({(results['original'] - results['after_existing'])/results['original']*100:.1f}%)")
        
        if results['segment_only'] != results['segment_expected']:
            print(f"[!] 세그먼트 필터 단독 결과가 예상과 다름: {results['segment_only']}건 vs {results['segment_expected']}건")
        
        return results
    
    def analyze_segment_breakdown(self) -> Dict:
        """Phase 1-3: 세그먼트별 거래 매칭"""
        print("\n=== Phase 1-3: 세그먼트별 거래 분석 ===")
        
        df = self.df_original.copy()
        results = {}
        
        # 시분초 추출
        if '매수시간' in df.columns:
            time_str = df['매수시간'].astype(str)
            if time_str.str.len().iloc[0] > 6:
                df['시분초'] = time_str.str[-6:].astype(int)
            else:
                df['시분초'] = time_str.astype(int)
        
        # 세그먼트 라벨 추가
        df['segment'] = df.apply(
            lambda row: self._get_segment_label(
                row.get('시가총액', 0), 
                row.get('시분초', 0)
            ), 
            axis=1
        )
        
        # 세그먼트별 통계
        print("\n세그먼트별 거래 수 및 수익:")
        print("-" * 80)
        print(f"{'세그먼트':<35} {'거래수':>8} {'수익금':>15} {'승률':>8} {'상태':<15}")
        print("-" * 80)
        
        for segment_name in sorted(df['segment'].unique()):
            seg_df = df[df['segment'] == segment_name]
            count = len(seg_df)
            profit = seg_df['수익금'].sum() if '수익금' in seg_df.columns else 0
            winrate = (seg_df['수익금'] > 0).mean() * 100 if '수익금' in seg_df.columns else 0
            
            status = '전체제외' if segment_name in self.EXCLUDED_SEGMENTS else '필터적용'
            
            results[segment_name] = {
                'count': count,
                'profit': profit,
                'winrate': winrate,
                'status': status
            }
            
            print(f"{segment_name:<35} {count:>8,} {profit:>15,.0f} {winrate:>7.1f}% {status:<15}")
        
        print("-" * 80)
        
        # 전체 제외 세그먼트 요약
        excluded_count = sum(r['count'] for name, r in results.items() if name in self.EXCLUDED_SEGMENTS)
        excluded_profit = sum(r['profit'] for name, r in results.items() if name in self.EXCLUDED_SEGMENTS)
        
        print(f"\n전체제외 세그먼트 합계: {excluded_count:,}건, {excluded_profit:,.0f}원")
        print(f"필터적용 세그먼트 합계: {len(df) - excluded_count:,}건")
        
        return results
    
    def compare_variables(self) -> Dict:
        """Phase 1-2: 변수 값 비교"""
        print("\n=== Phase 1-2: 변수 값 비교 ===")
        
        # 주요 비교 대상 변수
        key_variables = [
            '시가총액',
            '매수등락율',
            '매수체결강도',
            '매수당일거래대금',
            '매수회전율',
            '매수전일비',
            '매수전일동시간비',
            '매수호가잔량비',
            '매수스프레드',
            '매수변동폭',
            '매수고저평균대비등락율',
            '당일거래대금_5틱분봉평균_비율',
            '현재가_고저범위_위치',
            '거래품질점수',
        ]
        
        results = {}
        
        df_orig = self.df_original
        df_filt = self.df_filtered if self.df_filtered is not None else pd.DataFrame()
        
        print(f"\n{'변수명':<35} {'원본 평균':>12} {'원본 중앙':>12} {'Filtered 평균':>12} {'Filtered 중앙':>12}")
        print("-" * 95)
        
        for var in key_variables:
            orig_mean = df_orig[var].mean() if var in df_orig.columns else np.nan
            orig_median = df_orig[var].median() if var in df_orig.columns else np.nan
            filt_mean = df_filt[var].mean() if var in df_filt.columns else np.nan
            filt_median = df_filt[var].median() if var in df_filt.columns else np.nan
            
            results[var] = {
                'orig_mean': orig_mean,
                'orig_median': orig_median,
                'filt_mean': filt_mean,
                'filt_median': filt_median,
            }
            
            print(f"{var:<35} {orig_mean:>12.2f} {orig_median:>12.2f} {filt_mean:>12.2f} {filt_median:>12.2f}")
        
        return results
    
    def generate_report(self, trade_counts: Dict, segment_breakdown: Dict, var_comparison: Dict) -> str:
        """진단 보고서 생성"""
        report = []
        report.append("=" * 80)
        report.append("세그먼트 필터 예측-실제 괴리 진단 보고서")
        report.append("=" * 80)
        report.append("")
        
        # 1. 거래 수 분석
        report.append("## 1. 거래 수 단계별 분석")
        report.append("")
        report.append(f"| 단계 | 거래 수 | 제외율 |")
        report.append(f"|------|---------|--------|")
        report.append(f"| 원본 | {trade_counts['original']:,} | - |")
        report.append(f"| 기존 조건 후 | {trade_counts['after_existing']:,} | {(1-trade_counts['after_existing']/trade_counts['original'])*100:.1f}% |")
        report.append(f"| 세그먼트만 | {trade_counts['segment_only']:,} | {(1-trade_counts['segment_only']/trade_counts['original'])*100:.1f}% |")
        report.append(f"| 현재 구조 | {trade_counts['combined_current']:,} | {(1-trade_counts['combined_current']/trade_counts['original'])*100:.1f}% |")
        report.append(f"| 실제 Filtered | {trade_counts['filtered_actual']:,} | {(1-trade_counts['filtered_actual']/trade_counts['original'])*100:.1f}% |")
        report.append(f"| 세그먼트 예상 | {trade_counts['segment_expected']:,} | {(1-trade_counts['segment_expected']/trade_counts['original'])*100:.1f}% |")
        report.append("")
        
        # 2. 핵심 발견
        report.append("## 2. 핵심 발견")
        report.append("")
        
        diff = trade_counts['filtered_actual'] - trade_counts['segment_expected']
        report.append(f"- 예상 대비 실제 거래 수 차이: **{diff:+,}건** ({diff/trade_counts['segment_expected']*100:+.1f}%)")
        
        if trade_counts['segment_only'] < trade_counts['after_existing']:
            report.append(f"- 세그먼트 필터가 더 많이 제외: 기존 {trade_counts['original']-trade_counts['after_existing']:,}건 vs 세그먼트 {trade_counts['original']-trade_counts['segment_only']:,}건")
        else:
            report.append(f"- 기존 조건이 더 많이 제외: 기존 {trade_counts['original']-trade_counts['after_existing']:,}건 vs 세그먼트 {trade_counts['original']-trade_counts['segment_only']:,}건")
        
        report.append("")
        
        # 3. 원인 분석
        report.append("## 3. 원인 분석")
        report.append("")
        
        if trade_counts['filtered_actual'] > trade_counts['segment_expected']:
            report.append("**문제**: 실제 거래 수가 예상보다 많음 → 세그먼트 필터가 예상보다 덜 제외")
            report.append("")
            report.append("가능한 원인:")
            report.append("1. 세그먼트 필터가 기존 조건 뒤에 배치되어, 이미 False인 거래에는 영향 없음")
            report.append("2. 런타임 변수 계산 값이 분석 시와 다름")
            report.append("3. 세그먼트 경계값 불일치")
        else:
            report.append("**문제**: 실제 거래 수가 예상보다 적음 → 기존 조건이 추가로 제외")
        
        report.append("")
        
        # 4. 권장 조치
        report.append("## 4. 권장 조치")
        report.append("")
        report.append("1. **방안 B 적용**: 세그먼트 필터를 기존 조건 앞에 배치")
        report.append("2. **방안 A 검토**: 기존 조건을 세그먼트 필터로 완전 대체")
        report.append("3. **변수 계산 통일**: 런타임 변수가 분석 시와 동일한지 확인")
        
        return '\n'.join(report)
    
    def run_diagnosis(self) -> DiagnosisResult:
        """전체 진단 실행"""
        print("=" * 80)
        print("세그먼트 필터 예측-실제 괴리 진단")
        print("=" * 80)
        
        if not self.load_data():
            raise RuntimeError("데이터 로드 실패")
        
        # Phase 1-1: 거래 수 분석
        trade_counts = self.analyze_trade_counts()
        
        # Phase 1-3: 세그먼트별 분석
        segment_breakdown = self.analyze_segment_breakdown()
        
        # Phase 1-2: 변수 비교
        var_comparison = self.compare_variables()
        
        # 보고서 생성
        report = self.generate_report(trade_counts, segment_breakdown, var_comparison)
        print("\n" + report)
        
        # 보고서 저장
        report_path = self.output_base / 'segment_discrepancy_diagnosis.md'
        report_path.write_text(report, encoding='utf-8')
        print(f"\n보고서 저장: {report_path}")
        
        return DiagnosisResult(
            original_count=trade_counts['original'],
            after_existing_cond=trade_counts['after_existing'],
            after_segment_filter=trade_counts['segment_only'],
            filtered_count=trade_counts['filtered_actual'],
            segment_breakdown=segment_breakdown,
            variable_comparison=var_comparison,
            recommendations=[
                "방안 B: 세그먼트 필터 우선 적용",
                "방안 A: 세그먼트 전용 조건식",
                "변수 계산 로직 통일",
            ]
        )


def main():
    """메인 함수"""
    output_base = Path('backtester/backtesting_output')
    
    # 최신 출력 디렉토리 자동 탐색
    original_dir = None
    filtered_dir = None
    
    for d in sorted(output_base.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        name = d.name
        if 'Min_B_Study_251227_20260107210544' in name and 'Filtered' not in name:
            original_dir = d
        elif 'Min_B_Study_251227_Filtered' in name:
            filtered_dir = d
        
        if original_dir and filtered_dir:
            break
    
    if original_dir is None:
        # 수동 지정
        original_dir = output_base / 'stock_bt_Min_B_Study_251227_20260107210544'
    if filtered_dir is None:
        filtered_dir = output_base / 'stock_bt_Min_B_Study_251227_Filtered_20260107215836'
    
    print(f"원본 디렉토리: {original_dir}")
    print(f"Filtered 디렉토리: {filtered_dir}")
    
    diagnoser = SegmentDiscrepancyDiagnoser(original_dir, filtered_dir, output_base)
    result = diagnoser.run_diagnosis()
    
    return result


if __name__ == '__main__':
    main()
