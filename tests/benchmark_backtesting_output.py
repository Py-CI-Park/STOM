import argparse
import time

import pandas as pd

from backtester.analysis.metrics_base import CalculateDerivedMetrics
from backtester.analysis.exports import ExportBacktestCSV


def run_benchmark(detail_csv: str, save_file_name: str) -> None:
    df_detail = pd.read_csv(detail_csv, encoding='utf-8-sig')

    start = time.perf_counter()
    df_analysis = CalculateDerivedMetrics(df_detail)
    metrics_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    ExportBacktestCSV(df_detail, save_file_name, write_detail=True, write_summary=True, write_filter=True, df_analysis=df_analysis)
    csv_elapsed = time.perf_counter() - start

    print(f"Derived metrics: {metrics_elapsed:.3f}s")
    print(f"CSV export:      {csv_elapsed:.3f}s")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backtesting output benchmark')
    parser.add_argument('--detail', required=True, help='Path to detail CSV')
    parser.add_argument('--save', required=True, help='Save file name (output folder name)')
    args = parser.parse_args()
    run_benchmark(args.detail, args.save)
