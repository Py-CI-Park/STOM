import argparse
import time

import pandas as pd

from backtester.analysis.metrics_base import CalculateDerivedMetrics
from backtester.analysis.exports import ExportBacktestCSV
from backtester.back_static import RunFullAnalysis


def measure(detail_csv: str, save_file_name: str, run_full: bool = False) -> None:
    df_detail = pd.read_csv(detail_csv, encoding='utf-8-sig')

    start = time.perf_counter()
    df_analysis = CalculateDerivedMetrics(df_detail)
    metrics_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    ExportBacktestCSV(df_detail, save_file_name, write_detail=True, write_summary=True, write_filter=True, df_analysis=df_analysis)
    csv_elapsed = time.perf_counter() - start

    print(f"[metrics] {metrics_elapsed:.3f}s")
    print(f"[csv]     {csv_elapsed:.3f}s")

    if run_full:
        start = time.perf_counter()
        RunFullAnalysis(df_detail, save_file_name, teleQ=None)
        full_elapsed = time.perf_counter() - start
        print(f"[full]    {full_elapsed:.3f}s")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Measure backtesting output performance')
    parser.add_argument('--detail', required=True, help='Path to detail CSV')
    parser.add_argument('--save', required=True, help='Save file name (output folder name)')
    parser.add_argument('--full', action='store_true', help='Run full analysis pipeline')
    args = parser.parse_args()
    measure(args.detail, args.save, run_full=args.full)
