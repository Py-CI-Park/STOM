from traceback import print_exc
import pandas as pd
from backtester.analysis.metrics import CalculateDerivedMetrics, AnalyzeFilterEffects
from backtester.detail_schema import reorder_detail_columns
from backtester.output_paths import ensure_backtesting_output_dir

def ExportBacktestCSV(df_tsg, save_file_name, teleQ=None, write_detail=True, write_summary=True, write_filter=True):
    """
    백테스팅 결과를 CSV 파일로 내보냅니다.

    Args:
        df_tsg: 백테스팅 결과 DataFrame
        save_file_name: 저장 파일명
        teleQ: 텔레그램 전송 큐
        write_detail: detail.csv 생성 여부
        write_summary: summary.csv 생성 여부
        write_filter: filter.csv 생성 여부

    Returns:
        tuple: (detail_path, summary_path, filter_path)
    """
    try:
        # 파생 지표 계산
        df_analysis = CalculateDerivedMetrics(df_tsg)
        df_analysis = reorder_detail_columns(df_analysis)

        detail_path, summary_path, filter_path = None, None, None
        output_dir = ensure_backtesting_output_dir(save_file_name)

        # === 1. 상세 거래 기록 CSV ===
        if write_detail:
            detail_path = str(output_dir / f"{save_file_name}_detail.csv")
            df_analysis.to_csv(detail_path, encoding='utf-8-sig', index=True)

        # === 2. 조건별 요약 통계 CSV ===
        summary_data = []

        # 시간대별 요약
        if write_summary and '매수시' in df_analysis.columns:
            for hour in df_analysis['매수시'].unique():
                hour_data = df_analysis[df_analysis['매수시'] == hour]
                summary_data.append({
                    '분류': '시간대별',
                    '조건': f'{hour}시',
                    '거래횟수': len(hour_data),
                    '승률': round((hour_data['수익금'] > 0).mean() * 100, 2),
                    '총수익금': int(hour_data['수익금'].sum()),
                    '평균수익률': round(hour_data['수익률'].mean(), 2),
                    '평균보유시간': round(hour_data['보유시간'].mean(), 1),
                    '손실거래비중': round((hour_data['수익금'] < 0).mean() * 100, 2)
                })

        # 등락율 구간별 요약
        if write_summary and '매수등락율' in df_analysis.columns:
            bins = [0, 5, 10, 15, 20, 25, 30, 100]
            labels = ['0-5%', '5-10%', '10-15%', '15-20%', '20-25%', '25-30%', '30%+']
            df_analysis['등락율구간_'] = pd.cut(df_analysis['매수등락율'], bins=bins, labels=labels, right=False)
            for grp in labels:
                grp_data = df_analysis[df_analysis['등락율구간_'] == grp]
                if len(grp_data) > 0:
                    summary_data.append({
                        '분류': '등락율구간별',
                        '조건': grp,
                        '거래횟수': len(grp_data),
                        '승률': round((grp_data['수익금'] > 0).mean() * 100, 2),
                        '총수익금': int(grp_data['수익금'].sum()),
                        '평균수익률': round(grp_data['수익률'].mean(), 2),
                        '평균보유시간': round(grp_data['보유시간'].mean(), 1),
                        '손실거래비중': round((grp_data['수익금'] < 0).mean() * 100, 2)
                    })

        # 체결강도 구간별 요약
        if write_summary and '매수체결강도' in df_analysis.columns:
            bins_ch = [0, 80, 100, 120, 150, 200, 500]
            labels_ch = ['~80', '80-100', '100-120', '120-150', '150-200', '200+']
            df_analysis['체결강도구간_'] = pd.cut(df_analysis['매수체결강도'], bins=bins_ch, labels=labels_ch, right=False)
            for grp in labels_ch:
                grp_data = df_analysis[df_analysis['체결강도구간_'] == grp]
                if len(grp_data) > 0:
                    summary_data.append({
                        '분류': '체결강도구간별',
                        '조건': grp,
                        '거래횟수': len(grp_data),
                        '승률': round((grp_data['수익금'] > 0).mean() * 100, 2),
                        '총수익금': int(grp_data['수익금'].sum()),
                        '평균수익률': round(grp_data['수익률'].mean(), 2),
                        '평균보유시간': round(grp_data['보유시간'].mean(), 1),
                        '손실거래비중': round((grp_data['수익금'] < 0).mean() * 100, 2)
                    })

        # 매도조건별 요약
        if write_summary and '매도조건' in df_analysis.columns:
            for cond in df_analysis['매도조건'].unique():
                cond_data = df_analysis[df_analysis['매도조건'] == cond]
                summary_data.append({
                    '분류': '매도조건별',
                    '조건': str(cond)[:30],
                    '거래횟수': len(cond_data),
                    '승률': round((cond_data['수익금'] > 0).mean() * 100, 2),
                    '총수익금': int(cond_data['수익금'].sum()),
                    '평균수익률': round(cond_data['수익률'].mean(), 2),
                    '평균보유시간': round(cond_data['보유시간'].mean(), 1),
                    '손실거래비중': round((cond_data['수익금'] < 0).mean() * 100, 2)
                })

        if write_summary:
            summary_path = str(output_dir / f"{save_file_name}_summary.csv")
            df_summary = pd.DataFrame(summary_data)
            if len(df_summary) > 0:
                df_summary = df_summary.sort_values(['분류', '총수익금'], ascending=[True, False])
                df_summary.to_csv(summary_path, encoding='utf-8-sig', index=False)

        # === 3. 필터 효과 분석 CSV ===
        if write_filter:
            filter_data = AnalyzeFilterEffects(df_analysis)
            filter_path = str(output_dir / f"{save_file_name}_filter.csv")
            if len(filter_data) > 0:
                df_filter = pd.DataFrame(filter_data)
                df_filter = df_filter.sort_values('수익개선금액', ascending=False)
                df_filter.to_csv(filter_path, encoding='utf-8-sig', index=False)

        return detail_path, summary_path, filter_path

    except Exception as e:
        print_exc()
        return None, None, None


