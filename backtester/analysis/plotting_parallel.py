from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
import multiprocessing as mp
from pathlib import Path
from typing import Any

from backtester.analysis.ipc_utils import load_dataframe_ipc
from backtester.output_paths import ensure_backtesting_output_dir


def _run_chart_job(job: dict) -> dict:
    try:
        import matplotlib
        matplotlib.use('Agg')
    except Exception:
        pass

    job_type = job.get('type')
    save_file_name = job.get('save_file_name')
    df_path = job.get('df_path')

    df_tsg = load_dataframe_ipc(df_path) if df_path else job.get('df_tsg')
    if df_tsg is None or df_tsg.empty:
        return {'success': False, 'type': job_type, 'error': 'df_tsg_empty'}

    output_dir = ensure_backtesting_output_dir(save_file_name)
    paths: list[str] = []

    try:
        if job_type == 'analysis':
            from backtester.analysis.plotting import PltAnalysisCharts
            PltAnalysisCharts(
                df_tsg,
                save_file_name,
                None,
                buystg_name=job.get('buystg_name'),
                sellstg_name=job.get('sellstg_name'),
                startday=job.get('startday'),
                endday=job.get('endday'),
                starttime=job.get('starttime'),
                endtime=job.get('endtime'),
            )
            path = str(output_dir / f"{save_file_name}_analysis.png")
            if Path(path).exists():
                paths.append(path)
        elif job_type == 'comparison':
            from backtester.analysis.plotting import PltBuySellComparison
            PltBuySellComparison(
                df_tsg,
                save_file_name,
                None,
                buystg_name=job.get('buystg_name'),
                sellstg_name=job.get('sellstg_name'),
                startday=job.get('startday'),
                endday=job.get('endday'),
                starttime=job.get('starttime'),
                endtime=job.get('endtime'),
            )
            path = str(output_dir / f"{save_file_name}_comparison.png")
            if Path(path).exists():
                paths.append(path)
        elif job_type == 'enhanced':
            from backtester.analysis_enhanced.plotting import PltEnhancedAnalysisCharts
            PltEnhancedAnalysisCharts(
                df_tsg,
                save_file_name,
                None,
                filter_results=job.get('filter_results'),
                filter_results_lookahead=job.get('filter_results_lookahead'),
                feature_importance=job.get('feature_importance'),
                optimal_thresholds=job.get('optimal_thresholds'),
                filter_combinations=job.get('filter_combinations'),
                filter_stability=job.get('filter_stability'),
                generated_code=job.get('generated_code'),
                buystg=job.get('buystg'),
                sellstg=job.get('sellstg'),
                buystg_name=job.get('buystg_name'),
                sellstg_name=job.get('sellstg_name'),
                startday=job.get('startday'),
                endday=job.get('endday'),
                starttime=job.get('starttime'),
                endtime=job.get('endtime'),
            )
            path = str(output_dir / f"{save_file_name}_enhanced.png")
            if Path(path).exists():
                paths.append(path)
        else:
            return {'success': False, 'type': job_type, 'error': 'unknown_job'}

        return {'success': True, 'type': job_type, 'paths': paths}
    except Exception as exc:
        return {'success': False, 'type': job_type, 'error': str(exc)}


def run_parallel_chart_jobs(jobs: list[dict],
                            max_workers: int,
                            timeout_s: int = 600,
                            start_method: str = 'spawn') -> list[dict]:
    if not jobs:
        return []

    ctx = mp.get_context(start_method)
    results: list[dict[str, Any]] = []

    with ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx) as executor:
        future_map = {executor.submit(_run_chart_job, job): job for job in jobs}
        try:
            for future in as_completed(future_map, timeout=timeout_s):
                try:
                    results.append(future.result())
                except Exception as exc:
                    results.append({'success': False, 'type': 'unknown', 'error': str(exc)})
        except TimeoutError:
            for future in future_map:
                if not future.done():
                    future.cancel()
            results.append({'success': False, 'type': 'timeout', 'error': 'timeout'})

    return results
