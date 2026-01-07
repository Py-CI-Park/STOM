from traceback import print_exc
from pathlib import Path
import pandas as pd
from multiprocessing import get_context

from backtester.analysis.metrics_base import CalculateDerivedMetrics, AnalyzeFilterEffects
from backtester.analysis.ipc_utils import save_dataframe_ipc, load_dataframe_ipc, cleanup_ipc_path
from backtester.analysis.output_config import get_backtesting_output_config
from backtester.analysis.cache import load_cached_df, save_cached_df, build_df_signature
from backtester.detail_schema import reorder_detail_columns
from backtester.output_paths import ensure_backtesting_output_dir, build_backtesting_output_path
from backtester.analysis_enhanced.utils import round_dataframe_floats, DEFAULT_DECIMAL_PLACES


def _export_detail_csv(df_analysis: pd.DataFrame,
                       output_dir,
                       save_file_name: str,
                       chunk_size: int | None = None) -> str | None:
    if df_analysis is None or df_analysis.empty:
        return None
    detail_path = str(build_backtesting_output_path(save_file_name, "_detail.csv", output_dir=output_dir))
    # [2026-01-07] 소수점 4자리 제한 적용 후 CSV 저장
    df_rounded = round_dataframe_floats(df_analysis, decimals=DEFAULT_DECIMAL_PLACES)
    if chunk_size:
        df_rounded.to_csv(detail_path, encoding='utf-8-sig', index=True, chunksize=chunk_size)
    else:
        df_rounded.to_csv(detail_path, encoding='utf-8-sig', index=True)
    return detail_path


def _build_summary_df(df_analysis: pd.DataFrame) -> pd.DataFrame:
    summary_data = []

    # 시간대별 요약
    if '매수시' in df_analysis.columns:
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
    if '매수등락율' in df_analysis.columns:
        bins = [0, 5, 10, 15, 20, 25, 30, 100]
        labels = ['0-5%', '5-10%', '10-15%', '15-20%', '20-25%', '25-30%', '30%+']
        df_analysis = df_analysis.copy()
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
    if '매수체결강도' in df_analysis.columns:
        bins_ch = [0, 80, 100, 120, 150, 200, 500]
        labels_ch = ['~80', '80-100', '100-120', '120-150', '150-200', '200+']
        df_analysis = df_analysis.copy()
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
    if '매도조건' in df_analysis.columns:
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

    if not summary_data:
        return pd.DataFrame()
    df_summary = pd.DataFrame(summary_data)
    return df_summary.sort_values(['분류', '총수익금'], ascending=[True, False])


def _export_summary_csv(df_analysis: pd.DataFrame, output_dir, save_file_name: str) -> str | None:
    df_summary = _build_summary_df(df_analysis)
    if df_summary.empty:
        return None
    summary_path = str(build_backtesting_output_path(save_file_name, "_summary.csv", output_dir=output_dir))
    df_summary.to_csv(summary_path, encoding='utf-8-sig', index=False)
    return summary_path


def _export_filter_csv(df_analysis: pd.DataFrame, output_dir, save_file_name: str) -> str | None:
    filter_data = AnalyzeFilterEffects(df_analysis)
    if len(filter_data) == 0:
        return None
    filter_path = str(build_backtesting_output_path(save_file_name, "_filter.csv", output_dir=output_dir))
    df_filter = pd.DataFrame(filter_data)
    df_filter = df_filter.sort_values('수익개선금액', ascending=False)
    df_filter.to_csv(filter_path, encoding='utf-8-sig', index=False)
    return filter_path


def _export_detail_worker(ipc_path: str, output_dir: str, save_file_name: str, chunk_size: int | None):
    df = load_dataframe_ipc(ipc_path)
    if df is None or df.empty:
        return None
    return _export_detail_csv(df, Path(output_dir), save_file_name, chunk_size=chunk_size)


def _export_summary_worker(ipc_path: str, output_dir: str, save_file_name: str):
    df = load_dataframe_ipc(ipc_path)
    if df is None or df.empty:
        return None
    return _export_summary_csv(df, Path(output_dir), save_file_name)


def _export_filter_worker(ipc_path: str, output_dir: str, save_file_name: str):
    df = load_dataframe_ipc(ipc_path)
    if df is None or df.empty:
        return None
    return _export_filter_csv(df, Path(output_dir), save_file_name)

def ExportBacktestCSV(df_tsg, save_file_name, teleQ=None, write_detail=True, write_summary=True, write_filter=True,
                      df_analysis=None, chunk_size: int | None = 200000):
    """
    백테스팅 결과를 CSV 파일로 내보냅니다.

    Args:
        df_tsg: 백테스팅 결과 DataFrame
        save_file_name: 저장 파일명
        teleQ: 텔레그램 전송 큐
        write_detail: detail.csv 생성 여부
        write_summary: summary.csv 생성 여부
        write_filter: filter.csv 생성 여부
        df_analysis: 파생 지표 계산 결과 (재사용 시 중복 계산 방지)
        chunk_size: detail.csv 저장 시 chunksize (None이면 기본 단일 저장)

    Returns:
        tuple: (detail_path, summary_path, filter_path)
    """
    try:
        # 파생 지표 계산 (필요 시 재사용)
        cfg = get_backtesting_output_config()
        use_cache = bool(cfg.get('enable_cache', False))
        df_signature = build_df_signature(df_tsg)
        if df_analysis is None:
            if use_cache:
                df_analysis = load_cached_df(save_file_name, 'derived_metrics', signature=df_signature)
            if df_analysis is None:
                df_analysis = CalculateDerivedMetrics(df_tsg)
                if use_cache:
                    save_cached_df(save_file_name, 'derived_metrics', df_analysis, signature=df_signature)
        df_analysis = reorder_detail_columns(df_analysis)

        detail_path, summary_path, filter_path = None, None, None
        output_dir = ensure_backtesting_output_dir(save_file_name)

        if write_detail:
            detail_path = _export_detail_csv(df_analysis, output_dir, save_file_name, chunk_size=chunk_size)
        if write_summary:
            summary_path = _export_summary_csv(df_analysis, output_dir, save_file_name)
        if write_filter:
            filter_path = _export_filter_csv(df_analysis, output_dir, save_file_name)

        return detail_path, summary_path, filter_path

    except Exception as e:
        print_exc()
        return None, None, None


def ExportBacktestCSVParallel(df_tsg,
                              save_file_name,
                              teleQ=None,
                              write_detail=True,
                              write_summary=True,
                              write_filter=True,
                              df_analysis=None,
                              chunk_size: int | None = None,
                              ipc_format: str | None = None,
                              start_method: str | None = None):
    try:
        cfg = get_backtesting_output_config()
        if chunk_size is None:
            chunk_size = cfg.get('csv_chunk_size', 200000)
        if ipc_format is None:
            ipc_format = cfg.get('ipc_format', 'parquet')
        if start_method is None:
            start_method = cfg.get('parallel_start_method', 'spawn')

        use_cache = bool(cfg.get('enable_cache', False))
        df_signature = build_df_signature(df_tsg)
        if df_analysis is None:
            if use_cache:
                df_analysis = load_cached_df(save_file_name, 'derived_metrics', signature=df_signature)
            if df_analysis is None:
                df_analysis = CalculateDerivedMetrics(df_tsg)
                if use_cache:
                    save_cached_df(save_file_name, 'derived_metrics', df_analysis, signature=df_signature)
        df_analysis = reorder_detail_columns(df_analysis)

        output_dir = ensure_backtesting_output_dir(save_file_name)
        ipc_path = save_dataframe_ipc(df_analysis, output_dir, f"{save_file_name}_analysis", prefer_format=ipc_format)
        if ipc_path is None:
            return ExportBacktestCSV(
                df_tsg,
                save_file_name,
                teleQ,
                write_detail=write_detail,
                write_summary=write_summary,
                write_filter=write_filter,
                df_analysis=df_analysis,
                chunk_size=chunk_size,
            )

        ctx = get_context(start_method)
        processes = []

        if write_detail:
            p = ctx.Process(
                target=_export_detail_worker,
                args=(str(ipc_path), str(output_dir), save_file_name, chunk_size),
            )
            p.start()
            processes.append(p)

        if write_summary:
            p = ctx.Process(
                target=_export_summary_worker,
                args=(str(ipc_path), str(output_dir), save_file_name),
            )
            p.start()
            processes.append(p)

        if write_filter:
            p = ctx.Process(
                target=_export_filter_worker,
                args=(str(ipc_path), str(output_dir), save_file_name),
            )
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

        if cfg.get('ipc_cleanup', True):
            cleanup_ipc_path(ipc_path)

        detail_path = str(build_backtesting_output_path(save_file_name, "_detail.csv", output_dir=output_dir)) if write_detail else None
        summary_path = str(build_backtesting_output_path(save_file_name, "_summary.csv", output_dir=output_dir)) if write_summary else None
        filter_path = str(build_backtesting_output_path(save_file_name, "_filter.csv", output_dir=output_dir)) if write_filter else None

        return detail_path, summary_path, filter_path

    except Exception:
        print_exc()
        return None, None, None
