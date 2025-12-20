import math
import random
import re
import pyupbit
import sqlite3
import operator
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from numba import jit
from talib import stream
from traceback import print_exc
from matplotlib import pyplot as plt
from optuna_dashboard import run_server
from matplotlib import font_manager, gridspec
from utility.static import strp_time, strf_time, thread_decorator
from utility.setting import ui_num, GRAPH_PATH, DB_SETTING, DB_OPTUNA, columns_bt, columns_btf
from backtester.detail_schema import reorder_detail_columns

# [2025-12-10] 강화된 분석 모듈 임포트
try:
    from backtester.back_analysis_enhanced import (
        CalculateEnhancedDerivedMetrics,
        AnalyzeFilterEffectsEnhanced,
        FindAllOptimalThresholds,
        AnalyzeFilterCombinations,
        AnalyzeFeatureImportance,
        AnalyzeFilterStability,
        GenerateFilterCode,
        PltEnhancedAnalysisCharts,
        RunEnhancedAnalysis,
        ComputeStrategyKey
    )
    ENHANCED_ANALYSIS_AVAILABLE = True
except ImportError:
    ENHANCED_ANALYSIS_AVAILABLE = False


def _convert_bool_ops_to_pandas(expr: str) -> str:
    """
    자동 생성 조건식(문자열)의 and/or를 pandas eval용(&/|)으로 변환합니다.
    - generated_code['buy_conditions']는 'and (...)' 형태이므로 앞의 and도 제거합니다.
    """
    s = str(expr).strip() if expr is not None else ''
    if not s:
        return ''
    if s.lower().startswith('and '):
        s = s[4:].strip()
    # 단순 치환(단어 경계) - 컬럼명이 유니코드/언더스코어 기반이라 충돌 가능성 낮음
    s = re.sub(r'\band\b', '&', s)
    s = re.sub(r'\bor\b', '|', s)
    return s.strip()


def _build_filter_mask_from_generated_code(df: pd.DataFrame, generated_code: dict):
    """
    generated_code['buy_conditions']를 이용해 df에서 '매수 유지(keep)' 마스크를 생성합니다.
    Returns:
        dict:
          - mask: pd.Series[bool] | None
          - exprs: list[str]
          - error: str | None
          - failed_expr: str | None
    """
    result = {'mask': None, 'exprs': [], 'error': None, 'failed_expr': None}
    if not isinstance(df, pd.DataFrame) or df.empty:
        result['error'] = 'df가 비어있음'
        return result
    if not isinstance(generated_code, dict):
        result['error'] = 'generated_code가 dict가 아님'
        return result

    lines = generated_code.get('buy_conditions') or []
    if not lines:
        result['error'] = 'buy_conditions 없음'
        return result

    mask = pd.Series(True, index=df.index)
    safe_globals = {"__builtins__": {}}
    # 컬럼명을 그대로 변수로 제공(유니코드 식별자 포함 가능)
    safe_locals = {str(c): df[c] for c in df.columns}
    safe_locals.update({"np": np, "pd": pd})
    for raw in lines:
        expr = _convert_bool_ops_to_pandas(raw)
        if not expr:
            continue
        try:
            cond = eval(expr, safe_globals, safe_locals)
        except Exception as e:
            result['error'] = str(e)
            result['failed_expr'] = expr
            return result
        try:
            cond = cond.astype(bool)
        except Exception:
            pass
        mask = mask & cond
        result['exprs'].append(expr)

    result['mask'] = mask
    return result


def _extract_strategy_block_lines(code: str, start_marker: str, end_marker: str = None,
                                 max_lines: int = 8, max_line_len: int = 140):
    """
    차트/텔레그램 표시용 전략 블록 라인 추출(간단 버전).
    """
    try:
        s = str(code) if code is not None else ''
        s = s.replace('\r\n', '\n').replace('\r', '\n').strip()
        if not s:
            return []
        lines = s.splitlines()

        start_idx = None
        for i, ln in enumerate(lines):
            if start_marker in ln:
                start_idx = i
                break

        if start_idx is None:
            selected = lines[:max_lines]
        else:
            selected = lines[start_idx:]
            if end_marker:
                end_idx = None
                for j in range(1, len(selected)):
                    if end_marker in selected[j]:
                        end_idx = j
                        break
                if end_idx is not None:
                    selected = selected[:end_idx]
            selected = selected[:max_lines]

        out = []
        for ln in selected:
            if '#' in ln:
                ln = ln.split('#', 1)[0]
            ln = ln.rstrip()
            if not ln.strip():
                continue
            if len(ln) > max_line_len:
                ln = ln[: max_line_len - 3] + '...'
            out.append(ln)
        return out
    except Exception:
        return []


def PltFilterAppliedPreviewCharts(df_all: pd.DataFrame, df_filtered: pd.DataFrame,
                                  save_file_name: str, backname: str, seed: int,
                                  generated_code: dict = None,
                                  buystg: str = None, sellstg: str = None):
    """
    자동 생성 필터(generated_code)를 적용한 결과를 2개의 png로 저장합니다.
    - {전략명}_filtered.png
    - {전략명}_filtered_.png

    2025-12-20 개선: 필터 적용 후 거래가 0건이어도 경고 차트를 생성합니다.
    """
    if df_all is None:
        return None, None
    if len(df_all) < 2:
        return None, None
    if '수익금' not in df_all.columns:
        return None, None

    # 2025-12-20: 필터 적용 후 거래 0건인 경우 경고 차트 생성
    if df_filtered is None or len(df_filtered) < 1:
        # 폰트(한글) 설정
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_family = font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_family
            plt.rcParams['font.sans-serif'] = [font_family]
        except Exception:
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        total_profit = int(pd.to_numeric(df_all['수익금'], errors='coerce').fillna(0).sum())
        total_trades = len(df_all)

        fig, ax = plt.subplots(figsize=(12, 8))
        warning_text = (
            f"⚠️ 필터 적용 결과: 모든 거래 제외됨\n\n"
            f"• 원본 거래: {total_trades:,}건\n"
            f"• 원본 수익금: {total_profit:,}원\n"
            f"• 필터 후: 0건 (제외율 100%)\n\n"
            f"💡 필터 조건이 너무 엄격합니다.\n"
            f"   FILTER_MAX_EXCLUSION_RATIO (기본값 85%)를 확인하세요.\n"
            f"   또는 다른 필터 조합을 시도해 보세요.\n\n"
            f"🔧 back_analysis_enhanced.py에서 다음 상수를 조정할 수 있습니다:\n"
            f"   - FILTER_MAX_EXCLUSION_RATIO: 최대 제외율 (기본 0.85)\n"
            f"   - FILTER_MIN_REMAINING_TRADES: 최소 잔여 거래 수 (기본 30)"
        )

        ax.text(0.5, 0.5, warning_text, ha='center', va='center', fontsize=13,
                transform=ax.transAxes,
                bbox=dict(facecolor='lightyellow', edgecolor='orange', alpha=0.9, linewidth=2))
        ax.set_title(f'{backname} - 필터 적용 결과 경고 (거래 0건)', fontsize=14, color='red')
        ax.axis('off')

        path_main = f"{GRAPH_PATH}/{save_file_name}_filtered.png"
        plt.savefig(path_main, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        return path_main, None

    # 필터 적용 후 거래가 1건인 경우도 처리
    if len(df_filtered) < 2:
        return None, None
    if '수익금' not in df_filtered.columns:
        return None, None

    # 폰트(한글) 설정
    font_path = 'C:/Windows/Fonts/malgun.ttf'
    try:
        font_family = font_manager.FontProperties(fname=font_path).get_name()
        plt.rcParams['font.family'] = font_family
        plt.rcParams['font.sans-serif'] = [font_family]
    except Exception:
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    total_profit = float(pd.to_numeric(df_all['수익금'], errors='coerce').fillna(0).sum())
    filtered_profit = float(pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0).sum())
    improvement = filtered_profit - total_profit
    excluded_ratio = (1.0 - (len(df_filtered) / max(1, len(df_all)))) * 100.0

    # ===== 1) filtered.png (수익곡선 요약) =====
    path_main = f"{GRAPH_PATH}/{save_file_name}_filtered.png"
    fig = plt.figure(figsize=(12, 10))
    gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[1, 3])

    ax0 = fig.add_subplot(gs[0])
    use_dates = False
    dates = None
    base_cum = None
    filt_cum = None
    try:
        if '매수일자' in df_all.columns and '매수일자' in df_filtered.columns:
            base_profit_daily = pd.to_numeric(df_all['수익금'], errors='coerce').fillna(0).groupby(df_all['매수일자']).sum()
            filt_profit_daily = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0).groupby(df_filtered['매수일자']).sum()
            dates = sorted(set(base_profit_daily.index.tolist()) | set(filt_profit_daily.index.tolist()))
            base_profit_daily = base_profit_daily.reindex(dates, fill_value=0)
            filt_profit_daily = filt_profit_daily.reindex(dates, fill_value=0)
            base_cum = base_profit_daily.cumsum()
            filt_cum = filt_profit_daily.cumsum()
            use_dates = True
    except Exception:
        use_dates = False

    if not use_dates:
        base_cum = pd.to_numeric(df_all['수익금'], errors='coerce').fillna(0).cumsum()
        filt_cum = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0).cumsum()
        ax0.plot(range(len(base_cum)), base_cum, linewidth=1.2, label='기준(전체)', color='gray', alpha=0.8)
        ax0.plot(range(len(filt_cum)), filt_cum, linewidth=2.2, label='필터 적용', color='orange')
        ax0.set_title('누적 수익금(원)')
    else:
        x = np.arange(len(dates))
        ax0.plot(x, base_cum.values, linewidth=1.2, label='기준(전체)', color='gray', alpha=0.8)
        ax0.plot(x, filt_cum.values, linewidth=2.2, label='필터 적용', color='orange')
        ax0.set_title('누적 수익금(원) - 일자 기준')
        tick_step = max(1, int(len(dates) / 10))
        ax0.set_xticks(list(x[::tick_step]))
        ax0.set_xticklabels([str(d) for d in dates][::tick_step], rotation=45, ha='right', fontsize=8)
    ax0.legend(loc='best')
    ax0.grid()

    ax1 = fig.add_subplot(gs[1])
    if not use_dates:
        profits = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0)
        x = range(len(profits))
        ax1.bar(x, profits.clip(lower=0), label='이익금액', color='r', alpha=0.7)
        ax1.bar(x, profits.clip(upper=0), label='손실금액', color='b', alpha=0.7)
        ax1.plot(range(len(filt_cum)), filt_cum, linewidth=2.0, label='누적(필터)', color='orange')
        ax1.set_xlabel('거래 순번(필터 적용 후)')
    else:
        profits = filt_cum.diff().fillna(filt_cum.iloc[0])
        x = np.arange(len(dates))
        ax1.bar(x, profits.clip(lower=0).values, label='이익금액', color='r', alpha=0.7)
        ax1.bar(x, profits.clip(upper=0).values, label='손실금액', color='b', alpha=0.7)
        ax1.plot(x, filt_cum.values, linewidth=2.0, label='누적(필터)', color='orange')
        ax1.set_xlabel('매수일자')
        tick_step = max(1, int(len(dates) / 10))
        ax1.set_xticks(list(x[::tick_step]))
        ax1.set_xticklabels([str(d) for d in dates][::tick_step], rotation=45, ha='right', fontsize=8)
    ax1.set_ylabel('수익금(원)')
    ax1.legend(loc='upper left')
    ax1.grid()

    # 조건식/필터 요약 텍스트
    summary_lines = [
        "=== 필터 적용 요약 ===",
        f"- 거래수: {len(df_all):,} → {len(df_filtered):,} (제외 {excluded_ratio:.1f}%)",
        f"- 수익금: {int(total_profit):,}원 → {int(filtered_profit):,}원 (개선 {int(improvement):+,}원)",
    ]
    if isinstance(generated_code, dict) and generated_code.get('summary'):
        s = generated_code.get('summary') or {}
        try:
            summary_lines.append(f"- 자동 생성 필터: {int(s.get('total_filters', 0) or 0):,}개")
            summary_lines.append(f"- 예상 총 개선(동시 적용): {int(s.get('total_improvement_combined', s.get('total_improvement_naive', 0)) or 0):,}원")
        except Exception:
            pass
    if isinstance(generated_code, dict) and generated_code.get('buy_conditions'):
        summary_lines.append("- 적용 조건(일부):")
        for ln in (generated_code.get('buy_conditions') or [])[:5]:
            summary_lines.append(f"  {str(ln).strip()}")

    buy_block = _extract_strategy_block_lines(buystg, start_marker='if 매수:', end_marker='if 매도:', max_lines=6)
    sell_block = _extract_strategy_block_lines(sellstg, start_marker='if 매도:', end_marker=None, max_lines=6)
    if buy_block or sell_block:
        summary_lines.append("- 조건식(일부):")
        if buy_block:
            summary_lines.append("  [매수]")
            summary_lines.extend([f"    {ln}" for ln in buy_block])
        if sell_block:
            summary_lines.append("  [매도]")
            summary_lines.extend([f"    {ln}" for ln in sell_block])

    fig.suptitle(f'{backname} 필터 적용 결과 - {save_file_name}', fontsize=14, fontweight='bold')
    fig.text(0.01, 0.01, "\n".join(summary_lines), fontsize=9, family='monospace',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout(rect=(0, 0.05, 1, 0.96))
    plt.savefig(path_main, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    # ===== 2) filtered_.png (분포/단계 요약) =====
    path_sub = f"{GRAPH_PATH}/{save_file_name}_filtered_.png"
    fig = plt.figure(figsize=(12, 10))
    gs = gridspec.GridSpec(nrows=2, ncols=2, figure=fig, hspace=0.35, wspace=0.25)

    # (1) 누적 수익률(%) - 일자 기준(가능하면 매수일자 사용)
    ax = fig.add_subplot(gs[0, 0])
    if '매수일자' in df_all.columns and '매수일자' in df_filtered.columns:
        base_profit_daily = pd.to_numeric(df_all['수익금'], errors='coerce').fillna(0).groupby(df_all['매수일자']).sum()
        filt_profit_daily = pd.to_numeric(df_filtered['수익금'], errors='coerce').fillna(0).groupby(df_filtered['매수일자']).sum()
        dates = sorted(set(base_profit_daily.index.tolist()) | set(filt_profit_daily.index.tolist()))
        base_profit_daily = base_profit_daily.reindex(dates, fill_value=0)
        filt_profit_daily = filt_profit_daily.reindex(dates, fill_value=0)

        base_daily = base_profit_daily.cumsum()
        filt_daily = filt_profit_daily.cumsum()
        x = np.arange(len(dates))
        if seed:
            base_daily_pct = (base_daily + float(seed)) / float(seed) * 100 - 100
            filt_daily_pct = (filt_daily + float(seed)) / float(seed) * 100 - 100
            ax.plot(x, base_daily_pct.values, label='기준(%)', color='gray', linewidth=1.2)
            ax.plot(x, filt_daily_pct.values, label='필터(%)', color='orange', linewidth=2.0)
            ax.set_ylabel('누적 수익률(%)')
        else:
            ax.plot(x, base_daily.values, label='기준(원)', color='gray', linewidth=1.2)
            ax.plot(x, filt_daily.values, label='필터(원)', color='orange', linewidth=2.0)
            ax.set_ylabel('누적 수익금(원)')
        ax.set_title('일자별 누적 성과(필터 적용 비교)')
        ax.set_xlabel('매수일자')
        tick_step = max(1, int(len(dates) / 10))
        ax.set_xticks(list(x[::tick_step]))
        ax.set_xticklabels([str(d) for d in dates][::tick_step], rotation=45, ha='right', fontsize=8)
    else:
        ax.text(0.5, 0.5, '매수일자 컬럼 없음', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')
    ax.legend(loc='best')
    ax.grid()

    # (2) 단계별 누적개선/제외비율
    ax = fig.add_subplot(gs[0, 1])
    ax2 = ax.twinx()
    steps = (generated_code or {}).get('combine_steps') or []
    if steps:
        x = list(range(1, len(steps) + 1))
        cum_imp = [float(st.get('누적개선(동시적용)', 0) or 0) for st in steps]
        ex_pct = [float(st.get('누적제외비율', 0) or 0) for st in steps]
        ax.plot(x, cum_imp, 'o-', color='green', linewidth=2.0, markersize=4, label='누적개선(원)')
        ax2.plot(x, ex_pct, 's--', color='red', linewidth=1.5, markersize=4, label='누적제외(%)')
        ax.set_title('필터 조합 적용 단계별 누적개선/제외비율')
        ax.set_xlabel('단계')
        ax.set_ylabel('누적개선(원)', color='green')
        ax2.set_ylabel('누적제외(%)', color='red')
        ax.grid()
    else:
        ax.text(0.5, 0.5, 'combine_steps 없음', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')

    # (3) 시간대별 수익금
    ax = fig.add_subplot(gs[1, 0])
    if '매수시' in df_all.columns and '매수시' in df_filtered.columns:
        base_by_hour = df_all.groupby('매수시')['수익금'].sum()
        filt_by_hour = df_filtered.groupby('매수시')['수익금'].sum()
        hours = sorted(set(base_by_hour.index.tolist()) | set(filt_by_hour.index.tolist()))
        base_vals = [float(base_by_hour.get(h, 0) or 0) for h in hours]
        filt_vals = [float(filt_by_hour.get(h, 0) or 0) for h in hours]
        x = np.arange(len(hours))
        ax.bar(x - 0.2, base_vals, width=0.4, label='기준', color='gray', alpha=0.6)
        ax.bar(x + 0.2, filt_vals, width=0.4, label='필터', color='orange', alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels([str(h) for h in hours], rotation=0, fontsize=8)
        ax.set_title('시간대별 수익금(매수시 기준)')
        ax.axhline(y=0, color='black', linewidth=0.8)
        ax.legend(loc='best')
        ax.grid(axis='y')
    else:
        ax.text(0.5, 0.5, '매수시 컬럼 없음', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')

    # (4) 요일별 수익금
    ax = fig.add_subplot(gs[1, 1])
    if '매수일자' in df_all.columns and '매수일자' in df_filtered.columns:
        base_dates = pd.to_datetime(df_all['매수일자'].astype(str), format='%Y%m%d', errors='coerce')
        filt_dates = pd.to_datetime(df_filtered['매수일자'].astype(str), format='%Y%m%d', errors='coerce')

        base_tmp = df_all.copy()
        base_tmp['_wd'] = base_dates.dt.weekday
        filt_tmp = df_filtered.copy()
        filt_tmp['_wd'] = filt_dates.dt.weekday

        base_wd = pd.to_numeric(base_tmp['수익금'], errors='coerce').fillna(0).groupby(base_tmp['_wd']).sum()
        filt_wd = pd.to_numeric(filt_tmp['수익금'], errors='coerce').fillna(0).groupby(filt_tmp['_wd']).sum()
        wds = sorted(set(base_wd.index.tolist()) | set(filt_wd.index.tolist()))
        labels_map = ['월', '화', '수', '목', '금', '토', '일']
        labels = [labels_map[int(w)] if (w is not None and 0 <= int(w) <= 6) else str(w) for w in wds]
        x = np.arange(len(wds))
        base_vals = [float(base_wd.get(w, 0) or 0) for w in wds]
        filt_vals = [float(filt_wd.get(w, 0) or 0) for w in wds]
        ax.bar(x - 0.2, base_vals, width=0.4, label='기준', color='gray', alpha=0.6)
        ax.bar(x + 0.2, filt_vals, width=0.4, label='필터', color='orange', alpha=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_title('요일별 수익금(매수일자 기준)')
        ax.axhline(y=0, color='black', linewidth=0.8)
        ax.legend(loc='best')
        ax.grid(axis='y')
    else:
        ax.text(0.5, 0.5, '매수일자 컬럼 없음', ha='center', va='center', transform=ax.transAxes)
        ax.axis('off')

    fig.suptitle(f'{backname} 필터 적용 분포/단계 요약 - {save_file_name}', fontsize=14, fontweight='bold')
    plt.savefig(path_sub, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    return path_main, path_sub


@thread_decorator
def RunOptunaServer():
    try:
        run_server(DB_OPTUNA)
    except:
        pass


def WriteGraphOutputReport(save_file_name, df_tsg, backname=None, seed=None, mdd=None,
                           startday=None, endday=None, starttime=None, endtime=None,
                           buy_vars=None, sell_vars=None, buystg=None, sellstg=None,
                           full_result=None, enhanced_result=None, enhanced_error=None):
    """
    backtester/graph 폴더에 이번 실행의 산출물 목록/요약을 txt로 저장합니다.

    - 생성된 파일 목록(png/csv 등)
    - 생성 시각(파일 수정 시각 기준)
    - 조건식(매수/매도) 및 기본 성과 요약
    - detail.csv 컬럼 설명/공식(이번 실행 기준)
    """
    try:
        def _describe_output_file(filename: str) -> str:
            if filename.endswith('_filtered_.png'):
                return '자동 생성 필터 적용 분포/단계 요약(미리보기)'
            if filename.endswith('_filtered.png'):
                return '자동 생성 필터 적용 수익곡선(미리보기)'
            if filename.endswith('_condition_study.md'):
                return '조건식/필터 스터디 노트(md, 자동 생성)'
            if filename.endswith('_analysis.png'):
                return '백테스팅 결과 분석 차트(분 단위 시간축/구간별 수익 분포)'
            if filename.endswith('_comparison.png'):
                return '매수/매도 시점 비교 분석 차트(변화량/추세/위험도/3D 히트맵 등)'
            if filename.endswith('_enhanced.png'):
                return '필터 기능 분석 차트(통계/시너지/안정성/임계값/코드생성)'
            if filename.endswith('_detail.csv'):
                return '거래 상세 기록(강화 분석 사용 시 강화 파생지표 포함)'
            if filename.endswith('_summary.csv'):
                return '구간/조건별 요약 통계'
            if filename.endswith('_filter.csv'):
                return '필터 분석 결과(강화 분석 사용 시 t-test/효과크기 포함)'
            if filename.endswith('_optimal_thresholds.csv'):
                return '임계값(Threshold) 최적화 결과'
            if filename.endswith('_filter_combinations.csv'):
                return '필터 조합 시너지 분석 결과'
            if filename.endswith('_filter_stability.csv'):
                return '기간별 필터 안정성(일관성) 분석 결과'
            if filename.endswith('_report.txt'):
                return '이번 실행 산출물 리포트(파일/시간/조건/요약)'
            if filename.endswith('_.png'):
                return '부가정보 차트(지수비교/요일별/시간별 수익금)'
            if filename.endswith('.png'):
                return '수익곡선/누적 수익금 차트'
            return ''

        def _fmt_eok_to_korean(value_eok):
            """
            억 단위 숫자를 사람이 읽기 쉬운 라벨로 변환합니다.
            - 1조(=10,000억) 미만: 억 단위
            - 1조 이상: 조 단위(정수)
            """
            try:
                v = float(value_eok)
            except Exception:
                return str(value_eok)
            if v >= 10000:
                return f"{int(round(v / 10000))}조"
            return f"{int(round(v))}억"

        def _build_detail_csv_docs(df_report: pd.DataFrame) -> list[str]:
            """
            detail.csv(= df_report.to_csv(index=True))에 포함되는 컬럼 설명/공식을 생성합니다.
            - 이번 실행에서 실제 존재하는 컬럼(df_report.columns)만 출력합니다.
            """
            lines_local: list[str] = []
            if df_report is None:
                return lines_local

            # detail.csv 저장과 동일한 컬럼 순서를 사용(가독성)
            try:
                df_report = reorder_detail_columns(df_report)
            except Exception:
                pass

            # 파생 지표(분석 모듈 계산) 중심으로 공식 정의.
            # 그 외 컬럼은 "엔진 수집값"으로 표시하되, 가능한 경우 기본 정의를 제공합니다.
            derived_docs = {
                # 기본 손익/누적
                '수익금합계': {
                    'desc': '수익금 누적합',
                    'unit': '원',
                    'formula': ["수익금합계 = cumsum(수익금)"],
                    'note': 'GetResultDataframe()에서 계산'
                },
                # 매도-매수 변화량
                '등락율변화': {
                    'desc': '등락율 변화(매도-매수)',
                    'unit': '%p',
                    'formula': ["등락율변화 = 매도등락율 - 매수등락율"],
                    'note': '매도 시점 데이터 존재 시 계산'
                },
                '체결강도변화': {
                    'desc': '체결강도 변화(매도-매수)',
                    'unit': '지수',
                    'formula': ["체결강도변화 = 매도체결강도 - 매수체결강도"],
                    'note': '매도 시점 데이터 존재 시 계산'
                },
                '전일비변화': {
                    'desc': '전일비 변화(매도-매수)',
                    'unit': '원/지수',
                    'formula': ["전일비변화 = 매도전일비 - 매수전일비"],
                },
                '회전율변화': {
                    'desc': '회전율 변화(매도-매수)',
                    'unit': '%',
                    'formula': ["회전율변화 = 매도회전율 - 매수회전율"],
                },
                '호가잔량비변화': {
                    'desc': '호가잔량비 변화(매도-매수)',
                    'unit': '%p',
                    'formula': ["호가잔량비변화 = 매도호가잔량비 - 매수호가잔량비"],
                },
                '거래대금변화율': {
                    'desc': '거래대금 변화율(매도/매수)',
                    'unit': '배율',
                    'formula': [
                        "거래대금변화율 = (매도당일거래대금 / 매수당일거래대금) if 매수당일거래대금>0 else 1.0"
                    ],
                },
                '체결강도변화율': {
                    'desc': '체결강도 변화율(매도/매수)',
                    'unit': '배율',
                    'formula': ["체결강도변화율 = (매도체결강도 / 매수체결강도) if 매수체결강도>0 else 1.0"],
                },
                '등락추세': {
                    'desc': '등락율변화의 방향(상승/하락/유지)',
                    'unit': '범주',
                    'formula': ["등락추세 = '상승' if 등락율변화>0 else '하락' if 등락율변화<0 else '유지'"],
                },
                '체결강도추세': {
                    'desc': '체결강도변화의 방향(강화/약화/유지)',
                    'unit': '범주',
                    'formula': ["체결강도추세 = '강화' if 체결강도변화>10 else '약화' if 체결강도변화<-10 else '유지'"],
                },
                '거래량추세': {
                    'desc': '거래대금변화율 기반 거래량 추세(증가/감소/유지)',
                    'unit': '범주',
                    'formula': ["거래량추세 = '증가' if 거래대금변화율>1.2 else '감소' if 거래대금변화율<0.8 else '유지'"],
                },
                '급락신호': {
                    'desc': '급락 신호(매도-매수 변화량 기반)',
                    'unit': 'bool',
                    'formula': ["급락신호 = (등락율변화 < -3) and (체결강도변화 < -20)"],
                    'note': '사후(매도 시점 확정) 지표'
                },
                '매도세증가': {
                    'desc': '매도세 증가(호가잔량비변화 기반)',
                    'unit': 'bool',
                    'formula': ["매도세증가 = (호가잔량비변화 < -0.2)"],
                },
                '거래량급감': {
                    'desc': '거래량 급감(거래대금변화율 기반)',
                    'unit': 'bool',
                    'formula': ["거래량급감 = (거래대금변화율 < 0.5)"],
                },
                # 위험도
                '위험도점수': {
                    'desc': '매수 시점 기반 위험도 점수(룩어헤드 제거)',
                    'unit': '점(0~100)',
                    'formula': [
                        "점수 = 0",
                        "+20 if 매수등락율>=20, +10 if >=25, +10 if >=30",
                        "+15 if 매수체결강도<80, +10 if <60",
                        "+15 if 매수당일거래대금(억환산)<50, +10 if <100",
                        "+15 if 시가총액<1000억, +10 if <5000억",
                        "+10 if 매수호가잔량비<90, +15 if <70",
                        "+10 if 매수스프레드>=0.5, +10 if >=1.0",
                        "+10 if 매수변동폭비율>=5, +10 if >=10",
                        "점수 = clip(점수, 0, 100)"
                    ],
                    'note': '매수 진입 필터/추천에 사용 가능(매수 시점 정보만 사용)'
                },
                '매수매도위험도점수': {
                    'desc': '매수/매도 변화(사후 확정) 기반 위험도 점수',
                    'unit': '점(0~100)',
                    'formula': [
                        "점수 = 0",
                        "+20 if 등락율변화<-2",
                        "+20 if 체결강도변화<-15",
                        "+20 if 호가잔량비변화<-0.3",
                        "+20 if 거래대금변화율<0.6",
                        "+20 if 매수등락율>20",
                        "점수 = clip(점수, 0, 100)"
                    ],
                    'note': '룩어헤드가 포함되므로 필터 추천에는 사용하지 않고, 비교/진단 용도로만 활용'
                },
                # 강화 분석 주요 지표
                '모멘텀점수': {
                    'desc': '매수등락율/매수체결강도 정규화 기반 모멘텀 점수',
                    'unit': '점수',
                    'formula': [
                        "등락율_norm = (매수등락율-mean)/ (std+0.001)",
                        "체결강도_norm = (매수체결강도-100)/50",
                        "모멘텀점수 = (등락율_norm*0.4 + 체결강도_norm*0.6) * 10"
                    ],
                },
                '매수변동폭': {
                    'desc': '매수 시점 고가-저가',
                    'unit': '원',
                    'formula': ["매수변동폭 = 매수고가 - 매수저가"],
                },
                '매수변동폭비율': {
                    'desc': '매수변동폭을 저가 대비 %로 환산',
                    'unit': '%',
                    'formula': ["매수변동폭비율 = ((매수고가-매수저가)/매수저가)*100 if 매수저가>0 else 0"],
                },
                '변동성변화': {
                    'desc': '변동성 변화(매도변동폭비율-매수변동폭비율)',
                    'unit': '%p',
                    'formula': ["변동성변화 = 매도변동폭비율 - 매수변동폭비율"],
                },
                '타이밍점수': {
                    'desc': '시간대별 평균 수익률의 Z-score(사후 결과 기반)',
                    'unit': '점수',
                    'formula': [
                        "시간대평균수익률 = groupby(매수시).mean(수익률)",
                        "타이밍점수 = zscore(시간대평균수익률) * 10"
                    ],
                    'note': '사후(수익률) 기반이므로 필터 추천용으로 직접 사용하면 데이터 누수가 될 수 있음'
                },
                '연속이익': {
                    'desc': '직전 거래까지 연속 이익 횟수',
                    'unit': '회',
                    'formula': ["연속이익 = (이익여부==1) 연속 카운트"],
                },
                '연속손실': {
                    'desc': '직전 거래까지 연속 손실 횟수',
                    'unit': '회',
                    'formula': ["연속손실 = (이익여부==0) 연속 카운트"],
                },
                '리스크조정수익률': {
                    'desc': '수익률을 위험 요인으로 나눈 조정값',
                    'unit': '지표',
                    'formula': ["리스크조정수익률 = 수익률 / (abs(매수등락율)/10 + 보유시간/300 + 1)"],
                    'note': '보유시간 포함(사후 결과) → 진입 필터로 직접 사용 금지'
                },
                '스프레드영향': {
                    'desc': '매수스프레드 수준(낮음/중간/높음)',
                    'unit': '범주',
                    'formula': ["스프레드영향 = '높음'(>0.5) / '중간'(>0.2) / '낮음'"],
                },
                '거래품질점수': {
                    'desc': '매수 시점 거래 품질 종합 점수(0~100)',
                    'unit': '점',
                    'formula': [
                        "기본 50점",
                        "+10 if 매수체결강도>=120, +10 if >=150",
                        "+10 if 매수호가잔량비>=100",
                        "+10 if 1000억<=시가총액<=10000억",
                        "-15 if 매수등락율>=25, -10 if >=30",
                        "-10 if 매수스프레드>=0.5",
                        "clip(0,100)"
                    ],
                },
                # 초당(틱) 지표 조합
                '초당매수수량_매도총잔량_비율': {
                    'desc': '초당매수수량 대비 매도총잔량 비율(매수세 강도)',
                    'unit': '%',
                    'formula': ["(매수초당매수수량 / 매수매도총잔량) * 100 if 매수매도총잔량>0 else 0"],
                },
                '매도잔량_매수잔량_비율': {
                    'desc': '매도총잔량/매수총잔량 비율(호가 불균형 - 매도 우위)',
                    'unit': '배율',
                    'formula': ["매수매도총잔량 / 매수매수총잔량 if 매수매수총잔량>0 else 0"],
                },
                '매수잔량_매도잔량_비율': {
                    'desc': '매수총잔량/매도총잔량 비율(호가 불균형 - 매수 우위)',
                    'unit': '배율',
                    'formula': ["매수매수총잔량 / 매수매도총잔량 if 매수매도총잔량>0 else 0"],
                },
                '초당매도_매수_비율': {
                    'desc': '초당매도수량/초당매수수량 비율(매도 압력)',
                    'unit': '배율',
                    'formula': ["매수초당매도수량 / 매수초당매수수량 if 매수초당매수수량>0 else 0"],
                },
                '초당매수_매도_비율': {
                    'desc': '초당매수수량/초당매도수량 비율(매수 압력)',
                    'unit': '배율',
                    'formula': ["매수초당매수수량 / 매수초당매도수량 if 매수초당매도수량>0 else 0"],
                },
                '현재가_고저범위_위치': {
                    'desc': '매수시점 현재가(매수가)가 고저 범위 내에서 위치하는 비율',
                    'unit': '%',
                    'formula': ["((매수가-매수저가)/(매수고가-매수저가))*100 if (매수고가-매수저가)>0 else 50"],
                },
                '초당거래대금_당일비중': {
                    'desc': '초당거래대금이 당일거래대금에서 차지하는 비중(만분율)',
                    'unit': '만분율',
                    'formula': ["(매수초당거래대금/매수당일거래대금)*10000 if 매수당일거래대금>0 else 0"],
                },
                '초당순매수수량': {
                    'desc': '초당 순매수수량(매수-매도)',
                    'unit': '수량',
                    'formula': ["매수초당매수수량 - 매수초당매도수량"],
                },
                '초당순매수금액': {
                    'desc': '초당 순매수금액(백만원 단위)',
                    'unit': '백만원',
                    'formula': ["(초당순매수수량 * 매수가) / 1_000_000"],
                },
                '초당순매수비율': {
                    'desc': '초당 매수 비중(0~100)',
                    'unit': '%',
                    'formula': ["매수초당매수수량/(매수초당매수수량+매수초당매도수량)*100 if 합>0 else 50"],
                },
                '매도시_초당매수_매도_비율': {
                    'desc': '매도 시점 초당매수/초당매도 비율',
                    'unit': '배율',
                    'formula': ["매도초당매수수량/매도초당매도수량 if 매도초당매도수량>0 else 0"],
                },
                '초당매수수량변화': {
                    'desc': '초당매수수량 변화(매도-매수)',
                    'unit': '수량',
                    'formula': ["매도초당매수수량 - 매수초당매수수량"],
                },
                '초당매도수량변화': {
                    'desc': '초당매도수량 변화(매도-매수)',
                    'unit': '수량',
                    'formula': ["매도초당매도수량 - 매수초당매도수량"],
                },
                '초당거래대금변화': {
                    'desc': '초당거래대금 변화(매도-매수)',
                    'unit': '원/단위',
                    'formula': ["매도초당거래대금 - 매수초당거래대금"],
                },
                '초당거래대금변화율': {
                    'desc': '초당거래대금 변화율(매도/매수)',
                    'unit': '배율',
                    'formula': ["매도초당거래대금/매수초당거래대금 if 매수초당거래대금>0 else 1.0"],
                },
            }

            def _default_doc(col: str):
                return {
                    'desc': '엔진 수집값(원본) 또는 미정의 컬럼',
                    'unit': '',
                    'formula': ['원본 데이터(백테 엔진 수집/계산)'],
                    'note': ''
                }

            def _pattern_doc(col: str):
                # 호가잔량비/스프레드처럼 기본 공식이 명확한 컬럼은 패턴으로 보강
                if col == '보유시간':
                    return {
                        'desc': '보유 시간(매수~매도)',
                        'unit': '초',
                        'formula': ['보유시간 = 매도시간 - 매수시간 (엔진 계산)'],
                        'note': '시간 단위는 엔진 구현에 따름'
                    }
                if col == '수익금':
                    return {
                        'desc': '거래별 손익 금액',
                        'unit': '원',
                        'formula': ['수익금 = 매도금액 - 매수금액 (수수료/슬리피지 반영 여부는 전략/엔진 설정에 따름)'],
                        'note': ''
                    }
                if col == '수익률':
                    return {
                        'desc': '거래별 손익률',
                        'unit': '%',
                        'formula': ['수익률(%) = (수익금 / 매수금액) * 100'],
                        'note': '엔진 계산값과 동일 스케일로 표기'
                    }
                if col.endswith('호가잔량비'):
                    if col.startswith('매수') and '매수매도총잔량' in df_report.columns and '매수매수총잔량' in df_report.columns:
                        return {
                            'desc': '매수 시점 매수총잔량/매도총잔량 비율',
                            'unit': '%',
                            'formula': ['(매수매수총잔량 / 매수매도총잔량) * 100 if 매수매도총잔량>0 else 0'],
                            'note': ''
                        }
                    if col.startswith('매도') and '매도매도총잔량' in df_report.columns and '매도매수총잔량' in df_report.columns:
                        return {
                            'desc': '매도 시점 매수총잔량/매도총잔량 비율',
                            'unit': '%',
                            'formula': ['(매도매수총잔량 / 매도매도총잔량) * 100 if 매도매도총잔량>0 else 0'],
                            'note': ''
                        }
                if col.endswith('스프레드'):
                    if col.startswith('매수'):
                        return {
                            'desc': '매수 시점 1호가 스프레드(매도1-매수1)',
                            'unit': '%',
                            'formula': ['((매수매도호가1-매수매수호가1)/매수매수호가1)*100 if 매수매수호가1>0 else 0'],
                            'note': ''
                        }
                    if col.startswith('매도'):
                        return {
                            'desc': '매도 시점 1호가 스프레드(매도1-매수1)',
                            'unit': '%',
                            'formula': ['((매도매도호가1-매도매수호가1)/매도매수호가1)*100 if 매도매수호가1>0 else 0'],
                            'note': ''
                        }
                if col == '시가총액':
                    return {
                        'desc': '시가총액(매수 시점 스냅샷)',
                        'unit': '억',
                        'formula': ['원본 데이터(엔진 수집): 단위 억'],
                        'note': f"예: 10,000억 = {_fmt_eok_to_korean(10000)}"
                    }
                if col == '매수당일거래대금':
                    return {
                        'desc': '매수 시점 당일거래대금(원본 단위는 전략/데이터에 따라 상이)',
                        'unit': '백만(주로) 또는 억(레거시)',
                        'formula': ['원본 데이터(엔진 수집)'],
                        'note': '강화 필터/차트에서는 값 분포를 보고 단위를 추정하여 억 단위로 라벨링'
                    }
                if col in ('매수초당매수수량', '매수초당매도수량', '매도초당매수수량', '매도초당매도수량'):
                    return {
                        'desc': '초당 체결 수량(초 단위 누적/순간값은 엔진 정의에 따름)',
                        'unit': '수량',
                        'formula': ['원본 데이터(엔진 수집): arry_data[14]/[15]'],
                        'note': 'tick 데이터에서만 의미가 큼'
                    }
                if col in ('매수초당거래대금', '매도초당거래대금'):
                    return {
                        'desc': '초당 거래대금(원본 단위는 엔진/데이터 정의에 따름)',
                        'unit': '원/단위',
                        'formula': ['원본 데이터(엔진 수집): arry_data[16]'],
                        'note': '파생지표에서 당일거래대금 대비 만분율로도 사용'
                    }
                return None

            # 출력(이번 실행 컬럼 순서 기준)
            columns_in_order = ['index'] + list(df_report.columns)
            lines_local.append(f"- 컬럼 수(index 제외): {len(df_report.columns)}")
            lines_local.append("- 아래는 이번 실행 detail.csv(=detail DataFrame) 기준으로, 존재하는 컬럼만 출력합니다.")
            lines_local.append("- 공식은 코드 기준 정의이며, 결측/0분모는 0 또는 기본값으로 처리될 수 있습니다.")
            lines_local.append("")

            for col in columns_in_order:
                if col == 'index':
                    info = {
                        'desc': '거래 인덱스(문자열). 기본은 매수시간/매도시간 중 하나를 문자열로 사용',
                        'unit': 'string',
                        'formula': ['index = str(매수시간) if buystd else str(매도시간)'],
                        'note': 'GetResultDataframe()에서 index로 설정 후 CSV 첫 컬럼으로 저장'
                    }
                else:
                    info = derived_docs.get(col)
                    if info is None:
                        info = _pattern_doc(col) or _default_doc(col)

                lines_local.append(f"[{col}]")
                lines_local.append(f"- 설명: {info.get('desc', '')}")
                if info.get('unit') is not None:
                    lines_local.append(f"- 단위: {info.get('unit', '')}")
                formula = info.get('formula') or []
                if isinstance(formula, str):
                    formula = [formula]
                if formula:
                    lines_local.append("- 공식:")
                    for fline in formula:
                        lines_local.append(f"  - {fline}")
                note = info.get('note')
                if note:
                    lines_local.append(f"- 비고: {note}")
                lines_local.append("")

            return lines_local

        graph_dir = Path(GRAPH_PATH)
        graph_dir.mkdir(parents=True, exist_ok=True)
        report_path = graph_dir / f"{save_file_name}_report.txt"

        now = datetime.now()
        lines = []
        lines.append("=== STOM Backtester Output Report ===")
        lines.append(f"- 생성 시각: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- 저장 키(save_file_name): {save_file_name}")
        if backname is not None:
            lines.append(f"- 백테스트 구분: {backname}")
        if startday is not None and endday is not None:
            lines.append(f"- 기간: {startday} ~ {endday}")
        if starttime is not None and endtime is not None:
            lines.append(f"- 시간: {starttime} ~ {endtime}")
        if seed is not None:
            lines.append(f"- Seed: {seed}")
        if mdd is not None:
            lines.append(f"- MDD(%): {mdd}")

        if enhanced_result is not None and enhanced_error is None:
            lines.append("- 강화 분석: 성공")
        elif enhanced_error is not None:
            lines.append("- 강화 분석: 실패(기본 CSV 대체)")
        else:
            lines.append("- 강화 분석: 미사용")

        # 조건식 정보
        if buy_vars:
            lines.append("")
            lines.append("=== 매수 조건식 ===")
            lines.append(str(buy_vars))
        if sell_vars:
            lines.append("")
            lines.append("=== 매도 조건식 ===")
            lines.append(str(sell_vars))

        # 기본 성과 요약
        lines.append("")
        lines.append("=== 성과 요약 ===")
        total_trades = len(df_tsg) if df_tsg is not None else 0
        lines.append(f"- 거래 수: {total_trades:,}")
        if df_tsg is not None and '수익금' in df_tsg.columns:
            total_profit = int(df_tsg['수익금'].sum())
            win_rate = (df_tsg['수익금'] > 0).mean() * 100 if total_trades > 0 else 0
            avg_return = float(df_tsg['수익률'].mean()) if '수익률' in df_tsg.columns and total_trades > 0 else 0
            lines.append(f"- 총 수익금: {total_profit:,}원")
            lines.append(f"- 승률: {win_rate:.2f}%")
            lines.append(f"- 평균 수익률: {avg_return:.4f}%")

        if df_tsg is not None and '매도조건' in df_tsg.columns:
            try:
                vc = df_tsg['매도조건'].astype(str).value_counts()
                lines.append("")
                lines.append("=== 매도조건 상위(빈도) ===")
                for k, v in vc.head(10).items():
                    lines.append(f"- {k[:60]}: {v}")
            except:
                pass

        # 추천/요약
        if full_result and full_result.get('recommendations'):
            lines.append("")
            lines.append("=== 기본 분석 추천(Top) ===")
            for rec in full_result['recommendations'][:10]:
                lines.append(f"- {rec}")

        if enhanced_result and enhanced_result.get('recommendations'):
            lines.append("")
            lines.append("=== 강화 분석 추천(Top) ===")
            for rec in enhanced_result['recommendations'][:10]:
                lines.append(f"- {rec}")

        # 자동 생성 필터 코드(강화 분석)
        if enhanced_result and enhanced_result.get('generated_code'):
            try:
                gen = enhanced_result.get('generated_code') or {}
                lines.append("")
                lines.append("=== 자동 생성 필터 코드(요약) ===")
                if isinstance(gen, dict) and gen.get('summary'):
                    summary = gen.get('summary') or {}
                    total_filters = int(summary.get('total_filters', 0) or 0)
                    total_impr = int(summary.get('total_improvement_combined', summary.get('total_improvement_naive', 0)) or 0)
                    naive_impr = int(summary.get('total_improvement_naive', 0) or 0)
                    overlap_loss = int(summary.get('overlap_loss', 0) or 0)
                    lines.append(f"- 필터 수: {total_filters:,}개 (조합: AND)")
                    lines.append(f"- 예상 총 개선(동시 적용/중복 반영): {total_impr:,}원")
                    if total_filters > 0:
                        lines.append(f"- 개별개선합/중복: {naive_impr:,}원 / {overlap_loss:+,}원")

                    allow_ml = summary.get('allow_ml_filters')
                    excluded_ml = int(summary.get('excluded_ml_filters', 0) or 0)
                    if allow_ml is not None:
                        lines.append(
                            f"- ML 필터 사용: {'허용' if bool(allow_ml) else '금지'}"
                            + (f" (제외 {excluded_ml}개)" if excluded_ml > 0 else "")
                        )

                    steps = gen.get('combine_steps') or []
                    if steps:
                        lines.append("")
                        lines.append("[적용 순서(추가개선→누적개선, 누적제외%)]")
                        for st in steps[:10]:
                            try:
                                lines.append(
                                    f"- {st.get('순서', '')}. {str(st.get('필터명', ''))[:24]}: "
                                    f"+{int(st.get('추가개선(중복반영)', 0) or 0):,} → "
                                    f"누적 +{int(st.get('누적개선(동시적용)', 0) or 0):,} "
                                    f"(제외 {st.get('누적제외비율', 0)}%)"
                                )
                            except Exception:
                                continue

                    buy_lines = gen.get('buy_conditions') or []
                    if buy_lines:
                        lines.append("")
                        lines.append("[조합 코드(기존 매수조건에 AND 추가)]")
                        for ln in buy_lines[:15]:
                            lines.append(str(ln).rstrip())
                        lines.append("- 상세 후보/조건식은 *_filter.csv 참고")
                else:
                    lines.append("- 생성 불가 또는 후보 없음")
            except Exception:
                pass

        # ML 모델 저장/기록 (강화 분석)
        if enhanced_result and enhanced_result.get('ml_prediction_stats'):
            try:
                ml = enhanced_result.get('ml_prediction_stats') or {}
                lines.append("")
                lines.append("=== ML 모델 정보(손실확률_ML/위험도_ML) ===")
                lines.append(f"- 학습모드: {ml.get('train_mode', ml.get('requested_train_mode', 'N/A'))}")
                lines.append(f"- 모델: {ml.get('model_type', 'N/A')}")
                lines.append(
                    f"- 테스트(AUC/F1/BA): {ml.get('test_auc', 'N/A')}% / {ml.get('test_f1', 'N/A')}% / {ml.get('test_balanced_accuracy', 'N/A')}%"
                )
                lines.append(f"- 손실 비율(y=손실): {ml.get('loss_rate', 'N/A')}%")

                # ML 소요 시간(학습/예측/저장) - 텔레그램/리포트 공통 확인용
                try:
                    timing = ml.get('timing') if isinstance(ml, dict) else None
                    if isinstance(timing, dict):
                        def _fmt_sec(v):
                            try:
                                return f"{float(v):.2f}s"
                            except Exception:
                                return str(v)

                        total_s = timing.get('total_s')
                        parts = []
                        if timing.get('load_latest_s') is not None:
                            parts.append(f"load {_fmt_sec(timing.get('load_latest_s'))}")
                        if timing.get('train_classifiers_s') is not None:
                            parts.append(f"train {_fmt_sec(timing.get('train_classifiers_s'))}")
                        if timing.get('predict_all_s') is not None:
                            parts.append(f"predict {_fmt_sec(timing.get('predict_all_s'))}")
                        if timing.get('save_bundle_s') is not None:
                            parts.append(f"save {_fmt_sec(timing.get('save_bundle_s'))}")

                        if total_s is not None:
                            lines.append(
                                f"- 소요 시간: {_fmt_sec(total_s)}"
                                + (f" ({', '.join(parts)})" if parts else "")
                            )
                except Exception:
                    pass

                # ML 신뢰도(게이트) - 기준 미달이면 *_ML 필터 자동 생성/추천에서 제외
                try:
                    rel = None
                    if isinstance(enhanced_result, dict):
                        rel = enhanced_result.get('ml_reliability')
                    if not isinstance(rel, dict) and isinstance(ml, dict):
                        rel = ml.get('reliability')

                    if isinstance(rel, dict):
                        allow_ml = bool(rel.get('allow_ml_filters', False))
                        crit = rel.get('criteria') or {}
                        crit_txt = (
                            f"AUC≥{crit.get('min_test_auc')}%, "
                            f"F1≥{crit.get('min_test_f1')}%, "
                            f"BA≥{crit.get('min_test_balanced_accuracy')}%"
                        )
                        lines.append(f"- ML 필터 사용: {'허용' if allow_ml else '금지'} ({crit_txt})")
                        if not allow_ml:
                            for r in (rel.get('reasons') or [])[:5]:
                                lines.append(f"  - {r}")
                except Exception:
                    pass

                if ml.get('total_features') is not None:
                    lines.append(f"- 피처 수: {ml.get('total_features')}개")
                if ml.get('strategy_key'):
                    lines.append(f"- 전략키(sha256): {ml.get('strategy_key')}")
                if ml.get('feature_schema_hash'):
                    lines.append(f"- 피처 스키마 해시: {ml.get('feature_schema_hash')}")

                # 저장 경로/결과
                artifacts = ml.get('artifacts') if isinstance(ml, dict) else None
                if isinstance(artifacts, dict):
                    lines.append("")
                    lines.append("=== ML 모델 저장 결과 ===")
                    lines.append(f"- 저장 성공: {artifacts.get('saved', False)}")
                    if artifacts.get('strategy_dir'):
                        lines.append(f"- 전략 폴더: {artifacts.get('strategy_dir')}")
                        try:
                            code_path = Path(artifacts.get('strategy_dir')) / 'strategy_code.txt'
                            if code_path.exists():
                                lines.append(f"- 전략 코드 파일: {str(code_path)}")
                            idx_path = Path(artifacts.get('strategy_dir')) / 'runs_index.jsonl'
                            if idx_path.exists():
                                lines.append(f"- 실행 인덱스: {str(idx_path)}")
                        except Exception:
                            pass
                    if artifacts.get('run_bundle_path'):
                        lines.append(f"- 실행 모델(run): {artifacts.get('run_bundle_path')}")
                    if artifacts.get('latest_bundle_path'):
                        lines.append(f"- 최신 모델(latest): {artifacts.get('latest_bundle_path')}")
                    if artifacts.get('run_meta_path'):
                        lines.append(f"- 실행 메타(run): {artifacts.get('run_meta_path')}")
                    if artifacts.get('latest_meta_path'):
                        lines.append(f"- 최신 메타(latest): {artifacts.get('latest_meta_path')}")
                    if artifacts.get('error'):
                        lines.append(f"- 저장 오류: {artifacts.get('error')}")

                # 설명용 규칙(얕은 트리)
                rules = ml.get('explain_rules')
                if isinstance(rules, list) and len(rules) > 0:
                    lines.append("")
                    lines.append("=== 설명용 규칙(얕은 트리, 참고용) ===")
                    for r in rules[:10]:
                        lines.append(
                            f"- D{r.get('depth')} {r.get('feature')} @ {r.get('threshold')}: "
                            f"left 손실 {r.get('left_loss_rate')}%(n={r.get('left_samples')}), "
                            f"right 손실 {r.get('right_loss_rate')}%(n={r.get('right_samples')})"
                        )

                # 매수매도위험도 회귀 예측 요약
                rr = ml.get('risk_regression')
                if isinstance(rr, dict) and rr.get('best_model'):
                    lines.append("")
                    lines.append("=== 매수매도위험도 예측(회귀) 요약 ===")
                    lines.append(f"- 모델: {rr.get('best_model')}")
                    lines.append(
                        f"- MAE/RMSE/R2/상관: {rr.get('test_mae', 'N/A')} / {rr.get('test_rmse', 'N/A')} / "
                        f"{rr.get('test_r2', 'N/A')} / {rr.get('test_corr', 'N/A')}%"
                    )

                # 로드/재현 방법 안내
                lines.append("")
                lines.append("=== ML 모델 로드/재현 방법(요약) ===")
                lines.append("- 목적: 동일 전략키의 latest 모델을 로드하면, 같은 입력 데이터에 대해 동일 _ML 값을 재현할 수 있습니다.")
                lines.append("- 방법1(코드 옵션): PltShow(..., ml_train_mode='load_latest') 또는 RunEnhancedAnalysis(..., ml_train_mode='load_latest') 또는 PredictRiskWithML(..., train_mode='load_latest')")
                lines.append("- 방법2(joblib 직접): joblib.load(latest_ml_bundle.joblib) -> bundle의 scaler/model로 손실확률/위험도 예측")

                # 추후 개선 아이디어
                lines.append("")
                lines.append("=== ML 개선 아이디어(추후) ===")
                lines.append("- 시계열 분할(TimeSeriesSplit/Walk-Forward)로 미래 구간 검증 후 모델 선택")
                lines.append("- 확률 보정(Platt/Isotonic) 및 임계값(0.5) 최적화로 필터 기준 개선")
                lines.append("- 피처 추가/삭제 등 스키마 변경은 feature_schema_hash로 감지하여 자동 재학습/백업(추후 구현)")
            except Exception:
                pass

        if enhanced_error is not None:
            lines.append("")
            lines.append("=== 강화 분석 오류 ===")
            lines.append(str(enhanced_error))

        # 파일 목록
        lines.append("")
        lines.append("=== 생성 파일 목록 ===")
        prefix = str(save_file_name)
        matched = []
        for p in graph_dir.iterdir():
            if not p.is_file():
                continue
            name = p.name
            if not name.startswith(prefix):
                continue
            rest = name[len(prefix):]
            if rest == '' or rest.startswith('_') or rest.startswith('.'):
                matched.append(p)
        matched = sorted(matched, key=lambda x: x.name)
        if not matched:
            lines.append("(없음)")
        else:
            for p in matched:
                desc = _describe_output_file(p.name)
                try:
                    st = p.stat()
                    mtime = datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    if desc:
                        lines.append(f"- {p.name} | {st.st_size:,} bytes | mtime {mtime} | {desc}")
                    else:
                        lines.append(f"- {p.name} | {st.st_size:,} bytes | mtime {mtime}")
                except:
                    if desc:
                        lines.append(f"- {p.name} | {desc}")
                    else:
                        lines.append(f"- {p.name}")

        # detail.csv 컬럼 설명/공식
        if df_tsg is not None:
            try:
                lines.append("")
                lines.append("=== detail.csv 컬럼 설명/공식(이번 실행 기준) ===")
                lines.extend(_build_detail_csv_docs(df_tsg))
            except:
                lines.append("")
                lines.append("=== detail.csv 컬럼 설명/공식 ===")
                lines.append("(컬럼 설명 생성 중 오류가 발생했습니다. 실행은 계속됩니다.)")

        # [2025-12-19] 조건식/필터 스터디 파일(md) 자동 생성
        # - 최근 백테스팅에 사용한 매수/매도 조건식 + 자동 생성 필터 코드 + 컬럼(거래 항목) 목록을 한 파일로 묶어 학습용으로 제공
        try:
            study_path = graph_dir / f"{save_file_name}_condition_study.md"
            study_lines: list[str] = []

            study_lines.append("# 조건식/필터 스터디 노트 (자동 생성)")
            study_lines.append("")
            study_lines.append(f"- 생성 시각: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            study_lines.append(f"- save_file_name: {save_file_name}")

            strategy_key = None
            ml_stats = (enhanced_result or {}).get('ml_prediction_stats') if isinstance(enhanced_result, dict) else None
            if isinstance(ml_stats, dict):
                strategy_key = ml_stats.get('strategy_key')
            if strategy_key:
                study_lines.append(f"- 전략키(strategy_key): {strategy_key}")

            # 전략 원문 파일 경로(가능 시)
            try:
                artifacts = (ml_stats or {}).get('artifacts') if isinstance(ml_stats, dict) else None
                if isinstance(artifacts, dict) and artifacts.get('strategy_dir'):
                    code_path = Path(str(artifacts.get('strategy_dir'))) / 'strategy_code.txt'
                    if code_path.exists():
                        study_lines.append(f"- 전략 원문: {str(code_path)}")
            except Exception:
                pass

            # ML 신뢰도(게이트) 요약
            try:
                rel = (enhanced_result or {}).get('ml_reliability') if isinstance(enhanced_result, dict) else None
                if isinstance(rel, dict):
                    allow_ml = bool(rel.get('allow_ml_filters', False))
                    crit = rel.get('criteria') or {}
                    crit_txt = (
                        f"AUC≥{crit.get('min_test_auc')}%, "
                        f"F1≥{crit.get('min_test_f1')}%, "
                        f"BA≥{crit.get('min_test_balanced_accuracy')}%"
                    )
                    study_lines.append(f"- ML 필터 사용: {'허용' if allow_ml else '금지'} ({crit_txt})")
                    if not allow_ml:
                        for r in (rel.get('reasons') or [])[:5]:
                            study_lines.append(f"  - {r}")
            except Exception:
                pass

            study_lines.append("")
            study_lines.append("## 참고 파일")
            study_lines.append(f"- `{save_file_name}_enhanced.png`: 강화 분석 차트(Chart 18 포함)")
            study_lines.append(f"- `{save_file_name}_filter.csv`: 필터 후보/조건식 목록")
            study_lines.append(f"- `{save_file_name}_detail.csv`: 거래 상세 기록(컬럼=거래 항목)")
            study_lines.append(f"- `{save_file_name}_report.txt`: 실행 리포트")

            # 매수/매도 조건식(요약)
            study_lines.append("")
            study_lines.append("## 1) 매수/매도 조건식(요약)")
            buy_block = _extract_strategy_block_lines(buystg, start_marker='if 매수:', end_marker='if 매도:', max_lines=30)
            if buy_block:
                study_lines.append("")
                study_lines.append("### 매수(요약)")
                study_lines.append("```text")
                study_lines.extend([str(x) for x in buy_block])
                study_lines.append("```")
            sell_block = _extract_strategy_block_lines(sellstg, start_marker='if 매도:', end_marker=None, max_lines=30)
            if sell_block:
                study_lines.append("")
                study_lines.append("### 매도(요약)")
                study_lines.append("```text")
                study_lines.extend([str(x) for x in sell_block])
                study_lines.append("```")

            # 자동 생성 필터 코드(요약)
            gen = (enhanced_result or {}).get('generated_code') if isinstance(enhanced_result, dict) else None
            if isinstance(gen, dict):
                study_lines.append("")
                study_lines.append("## 2) 자동 생성 필터 코드(요약)")
                s = gen.get('summary') or {}
                if s:
                    study_lines.append(f"- 필터 수: {int(s.get('total_filters', 0) or 0):,}개 (조합: AND)")
                    study_lines.append(
                        f"- 예상 총 개선(동시 적용/중복 반영): "
                        f"{int(s.get('total_improvement_combined', s.get('total_improvement_naive', 0)) or 0):,}원"
                    )
                    allow_ml = s.get('allow_ml_filters')
                    excluded_ml = int(s.get('excluded_ml_filters', 0) or 0)
                    if allow_ml is not None:
                        study_lines.append(
                            f"- ML 필터 사용: {'허용' if bool(allow_ml) else '금지'}"
                            + (f" (제외 {excluded_ml}개)" if excluded_ml > 0 else "")
                        )

                steps = gen.get('combine_steps') or []
                if steps:
                    study_lines.append("")
                    study_lines.append("### 적용 순서(추가개선→누적개선, 누적제외%)")
                    for st in steps[:10]:
                        try:
                            study_lines.append(
                                f"- {st.get('순서', '')}. {str(st.get('필터명', ''))[:30]}: "
                                f"+{int(st.get('추가개선(중복반영)', 0) or 0):,} → "
                                f"누적 +{int(st.get('누적개선(동시적용)', 0) or 0):,} "
                                f"(제외 {st.get('누적제외비율', 0)}%)"
                            )
                        except Exception:
                            continue

                buy_lines = gen.get('buy_conditions') or []
                if buy_lines:
                    study_lines.append("")
                    study_lines.append("### 조합 코드(기존 매수조건에 AND 추가)")
                    study_lines.append("```python")
                    for ln in buy_lines[:20]:
                        study_lines.append(str(ln).rstrip())
                    study_lines.append("```")

            # 컬럼(거래 항목) 스터디
            try:
                df_ref = (enhanced_result or {}).get('enhanced_df') if isinstance(enhanced_result, dict) else None
                if not isinstance(df_ref, pd.DataFrame):
                    df_ref = df_tsg
                if isinstance(df_ref, pd.DataFrame) and not df_ref.empty:
                    df_ref = reorder_detail_columns(df_ref)
                    cols = [str(c) for c in df_ref.columns]

                    base_cols = [
                        '종목명', '시가총액', '포지션', '매수시간', '매도시간', '보유시간', '매도조건', '추가매수시간',
                        '매수가', '매도가', '매수금액', '매도금액', '수익률', '수익금', '수익금합계',
                        '매수일자', '매수시', '매수분', '매수초',
                    ]
                    core_cols = [
                        '모멘텀점수', '거래품질점수', '위험도점수',
                        '손실확률_ML', '위험도_ML', '예측매수매도위험도점수_ML',
                        '매수매도위험도점수', '리스크조정수익률', '급락신호',
                    ]

                    colset = set(cols)
                    base_present = [c for c in base_cols if c in colset]
                    core_present = [c for c in core_cols if c in colset]
                    buy_cols = [c for c in cols if c.startswith('매수') and c not in base_present]
                    sell_cols = [c for c in cols if c.startswith('매도')]
                    ml_cols = [c for c in cols if c.endswith('_ML')]
                    rest = [c for c in cols if c not in set(base_present + core_present + buy_cols + sell_cols)]

                    study_lines.append("")
                    study_lines.append("## 3) 거래 항목(컬럼) 목록(이번 실행 기준)")
                    study_lines.append("- 아래 컬럼들은 `detail.csv`/`filter.csv`에서 필터 후보로 활용할 수 있는 항목입니다.")
                    study_lines.append("- 룩어헤드 방지 원칙: 매도 시점/사후 확정 컬럼은 실거래 필터에 사용 금지")

                    def _dump_cols(title: str, items: list[str]):
                        if not items:
                            return
                        study_lines.append("")
                        study_lines.append(f"### {title} ({len(items)}개)")
                        study_lines.append("```text")
                        study_lines.extend(items)
                        study_lines.append("```")

                    _dump_cols("기본/시간/성과", base_present)
                    _dump_cols("매수 스냅샷(매수*)", buy_cols)
                    _dump_cols("매도 스냅샷(매도*)", sell_cols)
                    _dump_cols("핵심 파생/리스크/ML", core_present)
                    if ml_cols:
                        _dump_cols("ML 컬럼(*_ML)", ml_cols)
                    _dump_cols("기타", rest)

                    study_lines.append("")
                    study_lines.append("## 4) 필터 스터디 템플릿(복사/붙여넣기용)")
                    study_lines.append("- `*_filter.csv`의 `적용코드`를 그대로 매수 조건에 AND로 추가하는 방식이 가장 빠릅니다.")
                    study_lines.append("- 예시(형식):")
                    study_lines.append("```python")
                    study_lines.append("# and (매수등락율 < 8.0)")
                    study_lines.append("# and ((모멘텀점수 < 5.4) or (모멘텀점수 >= 6.7))")
                    study_lines.append("# and (초당순매수수량 < 35000)")
                    study_lines.append("```")
            except Exception:
                pass

            study_path.write_text("\n".join(study_lines), encoding='utf-8-sig')
        except Exception:
            pass

        report_path.write_text("\n".join(lines), encoding='utf-8-sig')
        return str(report_path)
    except:
        print_exc()
        return None


def GetTradeInfo(gubun):
    if gubun == 1:
        v = {
            '보유중': 0,
            '매수가': 0,
            '매도가': 0,
            '주문수량': 0,
            '보유수량': 0,
            '최고수익률': 0.,
            '최저수익률': 0.,
            '매수틱번호': 0,
            '매수시간': strp_time('%Y%m%d', '20000101')
        }
    elif gubun == 2:
        v = {
            '보유중': 0,
            '매수가': 0,
            '매도가': 0,
            '주문수량': 0,
            '보유수량': 0,
            '최고수익률': 0.,
            '최저수익률': 0.,
            '매수틱번호': 0,
            '매수시간': strp_time('%Y%m%d', '20000101'),
            '추가매수시간': [],
            '매수호가': 0,
            '매도호가': 0,
            '매수호가_': 0,
            '매도호가_': 0,
            '추가매수가': 0,
            '매수호가단위': 0,
            '매도호가단위': 0,
            '매수정정횟수': 0,
            '매도정정횟수': 0,
            '매수분할횟수': 0,
            '매도분할횟수': 0,
            '매수주문취소시간': strp_time('%Y%m%d', '20000101'),
            '매도주문취소시간': strp_time('%Y%m%d', '20000101')
        }
    else:
        v = {
            '손절횟수': 0,
            '거래횟수': 0,
            '직전거래시간': strp_time('%Y%m%d', '20000101'),
            '손절매도시간': strp_time('%Y%m%d', '20000101')
        }
    return v


def GetBackloadCodeQuery(code, days, starttime, endtime):
    last = len(days) - 1
    like_text = '( '
    for i, day in enumerate(days):
        if i != last:
            like_text += f"`index` LIKE '{day}%' or "
        else:
            like_text += f"`index` LIKE '{day}%' )"
    if len(str(endtime)) < 5:
        query = f"SELECT * FROM '{code}' WHERE {like_text} and " \
                f"`index` % 10000 >= {starttime} and " \
                f"`index` % 10000 <= {endtime}"
    else:
        query = f"SELECT * FROM '{code}' WHERE {like_text} and " \
                f"`index` % 1000000 >= {starttime} and " \
                f"`index` % 1000000 <= {endtime}"
    return query


def GetBackloadDayQuery(day, code, starttime, endtime):
    if len(str(endtime)) < 5:
        query = f"SELECT * FROM '{code}' WHERE " \
                f"`index` LIKE '{day}%' and " \
                f"`index` % 10000 >= {starttime} and " \
                f"`index` % 10000 <= {endtime}"
    else:
        query = f"SELECT * FROM '{code}' WHERE " \
                f"`index` LIKE '{day}%' and " \
                f"`index` % 1000000 >= {starttime} and " \
                f"`index` % 1000000 <= {endtime}"
    return query


def GetMoneytopQuery(gubun, startday, endday, starttime, endtime):
    if len(str(endtime)) < 5:
        query = f"SELECT * FROM moneytop WHERE " \
                f"`index` >= {startday * 10000} and " \
                f"`index` <= {endday * 10000 + 2400} and " \
                f"`index` % 10000 >= {starttime} and " \
                f"`index` % 10000 <= {endtime}"
    else:
        if gubun == 'S' and starttime < 90030:
            query = f"SELECT * FROM moneytop WHERE " \
                    f"`index` >= {startday * 1000000} and " \
                    f"`index` <= {endday * 1000000 + 240000} and " \
                    f"`index` % 1000000 >= 90030 and " \
                    f"`index` % 1000000 <= {endtime}"
        else:
            query = f"SELECT * FROM moneytop WHERE " \
                    f"`index` >= {startday * 1000000} and " \
                    f"`index` <= {endday * 1000000 + 240000} and " \
                    f"`index` % 1000000 >= {starttime} and " \
                    f"`index` % 1000000 <= {endtime}"
    return query


def AddAvgData(df, round_unit, is_tick, avg_list):
    if is_tick:
        df['이평0060'] = df['현재가'].rolling(window=60).mean().round(round_unit)
        df['이평0300'] = df['현재가'].rolling(window=300).mean().round(round_unit)
        df['이평0600'] = df['현재가'].rolling(window=600).mean().round(round_unit)
        df['이평1200'] = df['현재가'].rolling(window=1200).mean().round(round_unit)
    else:
        df['이평005'] = df['현재가'].rolling(window=5).mean().round(round_unit)
        df['이평010'] = df['현재가'].rolling(window=10).mean().round(round_unit)
        df['이평020'] = df['현재가'].rolling(window=20).mean().round(round_unit)
        df['이평060'] = df['현재가'].rolling(window=60).mean().round(round_unit)
        df['이평120'] = df['현재가'].rolling(window=120).mean().round(round_unit)
    for avg in avg_list:
        df[f'최고현재가{avg}'] = df['현재가'].rolling(window=avg).max()
        df[f'최저현재가{avg}'] = df['현재가'].rolling(window=avg).min()
        if not is_tick:
            df[f'최고분봉고가{avg}'] = df['분봉고가'].rolling(window=avg).max()
            df[f'최저분봉저가{avg}'] = df['분봉저가'].rolling(window=avg).min()
        df[f'체결강도평균{avg}'] = df['체결강도'].rolling(window=avg).mean().round(3)
        df[f'최고체결강도{avg}'] = df['체결강도'].rolling(window=avg).max()
        df[f'최저체결강도{avg}'] = df['체결강도'].rolling(window=avg).min()
        if is_tick:
            df[f'최고초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).max()
            df[f'최고초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).max()
            df[f'누적초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).sum()
            df[f'누적초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).sum()
            df[f'초당거래대금평균{avg}'] = df['초당거래대금'].rolling(window=avg).mean().round(0)
        else:
            df[f'최고분당매수수량{avg}'] = df['분당매수수량'].rolling(window=avg).max()
            df[f'최고분당매도수량{avg}'] = df['분당매도수량'].rolling(window=avg).max()
            df[f'누적분당매수수량{avg}'] = df['분당매수수량'].rolling(window=avg).sum()
            df[f'누적분당매도수량{avg}'] = df['분당매도수량'].rolling(window=avg).sum()
            df[f'분당거래대금평균{avg}'] = df['분당거래대금'].rolling(window=avg).mean().round(0)
        if round_unit == 3:
            df2 = df[['등락율', '당일거래대금', '전일비']].copy()
            df2[f'등락율N{avg}'] = df2['등락율'].shift(avg - 1)
            df2['등락율차이'] = df2['등락율'] - df2[f'등락율N{avg}']
            df2[f'당일거래대금N{avg}'] = df2['당일거래대금'].shift(avg - 1)
            df2['당일거래대금차이'] = df2['당일거래대금'] - df2[f'당일거래대금N{avg}']
            df2[f'전일비N{avg}'] = df2['전일비'].shift(avg - 1)
            df2['전일비차이'] = df2['전일비'] - df2[f'전일비N{avg}']
            df['등락율각도'] = df2['등락율차이'].apply(lambda x: round(math.atan2(x * 5, avg) / (2 * math.pi) * 360, 2))
            df['당일거래대금각도'] = df2['당일거래대금차이'].apply(lambda x: round(math.atan2(x / 100, avg) / (2 * math.pi) * 360, 2))
            df['전일비각도'] = df2['전일비차이'].apply(lambda x: round(math.atan2(x, avg) / (2 * math.pi) * 360, 2))
        else:
            df2 = df[['등락율', '당일거래대금']].copy()
            df2[f'등락율N{avg}'] = df2['등락율'].shift(avg - 1)
            df2['등락율차이'] = df2['등락율'] - df2[f'등락율N{avg}']
            df2[f'당일거래대금N{avg}'] = df2['당일거래대금'].shift(avg - 1)
            df2['당일거래대금차이'] = df2['당일거래대금'] - df2[f'당일거래대금N{avg}']
            df['등락율각도'] = df2['등락율차이'].apply(lambda x: round(math.atan2(x * 10, avg) / (2 * math.pi) * 360, 2))
            df['당일거래대금각도'] = df2['당일거래대금차이'].apply(lambda x: round(math.atan2(x / 100_000_000, avg) / (2 * math.pi) * 360, 2))
    return df


def LoadOrderSetting(gubun):
    con = sqlite3.connect(DB_SETTING)
    if 'S' in gubun:
        df1 = pd.read_sql('SELECT * FROM stockbuyorder', con).set_index('index')
        df2 = pd.read_sql('SELECT * FROM stocksellorder', con).set_index('index')
    else:
        df1 = pd.read_sql('SELECT * FROM coinbuyorder', con).set_index('index')
        df2 = pd.read_sql('SELECT * FROM coinsellorder', con).set_index('index')
    con.close()
    buy_setting = str(list(df1.iloc[0]))
    sell_setting = str(list(df2.iloc[0]))
    return buy_setting, sell_setting


def GetBuyStg(buytxt, gubun):
    buytxt  = buytxt.split('if 매수:')[0] + 'if 매수:\n    self.Buy(vturn, vkey)'
    buystg  = ''
    indistg = ''
    for line in buytxt.split('\n'):
        if 'self.indicator' in line:
            indistg += f'{line}\n'
        else:
            buystg += f'{line}\n'
    if buystg != '':
        try:
            buystg = compile(buystg, '<string>', 'exec')
        except:
            buystg = None
            if gubun == 0: print_exc()
    else:
        buystg = None
    if indistg != '':
        try:
            indistg = compile(indistg, '<string>', 'exec')
        except:
            indistg = None
    else:
        indistg = None
    return buystg, indistg


def GetSellStg(sellstg, gubun):
    sellstg = 'sell_cond = 0\n' + sellstg.split('if 매도:')[0] + 'if 매도:\n    self.Sell(vturn, vkey, sell_cond)'
    sellstg, dict_cond = SetSellCond(sellstg.split('\n'))
    try:
        sellstg = compile(sellstg, '<string>', 'exec')
    except:
        sellstg = None
        if gubun == 0: print_exc()
    return sellstg, dict_cond


def GetBuyConds(buy_conds, gubun):
    buy_conds = 'if ' + ':\n    매수 = False\nelif '.join(
        buy_conds) + ':\n    매수 = False\nif 매수:\n    self.Buy(vturn, vkey)'
    try:
        buy_conds = compile(buy_conds, '<string>', 'exec')
    except:
        buy_conds = None
        if gubun == 0: print_exc()
    return buy_conds


def GetSellConds(sell_conds, gubun):
    sell_conds = 'sell_cond = 0\nif ' + ':\n    매도 = True\nelif '.join(
        sell_conds) + ':\n    매도 = True\nif 매도:\n    self.Sell(vturn, vkey, sell_cond)'
    sell_conds, dict_cond = SetSellCond(sell_conds.split('\n'))
    try:
        sell_conds = compile(sell_conds, '<string>', 'exec')
    except:
        sell_conds = None
        if gubun == 0: print_exc()
    return sell_conds, dict_cond


def SetSellCond(selllist):
    count = 1
    sellstg = ''
    dict_cond = {0: '전략종료청산', 100: '분할매도', 200: '손절청산'}
    for i, text in enumerate(selllist):
        if '#' not in text and ('매도 = True' in text or '매도= True' in text or '매도 =True' in text or '매도=True' in text):
            dict_cond[count] = selllist[i - 1]
            sellstg = f"{sellstg}{text.split('매도')[0]}sell_cond = {count}\n"
            count += 1
        if text != '':
            sellstg = f"{sellstg}{text}\n"
    return sellstg, dict_cond


def GetBuyStgFuture(buystg, gubun):
    buytxt  = buystg.split('if BUY_LONG or SELL_SHORT:')[
                 0] + 'if BUY_LONG:\n    self.Buy(vturn, vkey, "LONG")\nelif SELL_SHORT:\n    self.Buy(vturn, vkey, "SHORT")'
    buystg  = ''
    indistg = ''
    for line in buytxt.split('\n'):
        if 'self.indicator' in line:
            indistg += f'{line}\n'
        else:
            buystg += f'{line}\n'
    if buystg != '':
        try:
            buystg = compile(buystg, '<string>', 'exec')
        except:
            buystg = None
            if gubun == 0: print_exc()
    else:
        buystg = None
    if indistg != '':
        try:
            indistg = compile(indistg, '<string>', 'exec')
        except:
            indistg = None
    else:
        indistg = None
    return buystg, indistg


def GetSellStgFuture(sellstg, gubun):
    sellstg = 'sell_cond = 0\n' + sellstg.split("if (포지션 == 'LONG' and SELL_LONG) or (포지션 == 'SHORT' and BUY_SHORT):")[
        0] + "if 포지션 == 'LONG' and SELL_LONG:\n    self.Sell(vturn, vkey, 'LONG', sell_cond)\nelif 포지션 == 'SHORT' and BUY_SHORT:\n    self.Sell(vturn, vkey, 'SHORT', sell_cond)"
    sellstg, dict_cond = SetSellCondFuture(sellstg.split('\n'))
    try:
        sellstg = compile(sellstg, '<string>', 'exec')
    except:
        sellstg = None
        if gubun == 0: print_exc()
    return sellstg, dict_cond


def GetBuyCondsFuture(is_long, buy_conds, gubun):
    if is_long:
        buy_conds = 'if ' + ':\n    BUY_LONG = False\nelif '.join(
            buy_conds) + ':\n    BUY_LONG = False\nif BUY_LONG:\n    self.Buy(vturn, vkey, "LONG")'
    else:
        buy_conds = 'if ' + ':\n    SELL_SHORT = False\nelif '.join(
            buy_conds) + ':\n    SELL_SHORT = False\nif SELL_SHORT:\n    self.Buy(vturn, vkey, "SHORT")'
    try:
        buy_conds = compile(buy_conds, '<string>', 'exec')
    except:
        buy_conds = None
        if gubun == 0: print_exc()
    return buy_conds


def GetSellCondsFuture(is_long, sell_conds, gubun):
    if is_long:
        sell_conds = 'sell_cond = 0\nif ' + ':\n    SELL_LONG = True\nelif '.join(
            sell_conds) + ':\n    SELL_LONG = True\nif SELL_LONG:\n    self.Sell(vturn, vkey, "SELL_LONG", sell_cond)'
    else:
        sell_conds = 'sell_cond = 0\nif ' + ':\n    BUY_SHORT = True\nelif '.join(
            sell_conds) + ':\n    BUY_SHORT = True\nif BUY_SHORT:\n    self.Sell(vturn, vkey, "BUY_SHORT", sell_cond)'
    sell_conds, dict_cond = SetSellCondFuture(sell_conds.split('\n'))
    try:
        sell_conds = compile(sell_conds, '<string>', 'exec')
    except:
        sell_conds = None
        if gubun == 0: print_exc()
    return sell_conds, dict_cond


def SetSellCondFuture(selllist):
    count = 1
    sellstg = ''
    dict_cond = {0: '전략종료청산', 100: '분할매도', 200: '손절청산'}
    for i, text in enumerate(selllist):
        if '#' not in text:
            if 'SELL_LONG = True' in text or 'SELL_LONG= True' in text or 'SELL_LONG =True' in text or 'SELL_LONG=True' in text:
                dict_cond[count] = selllist[i - 1]
                sellstg = f"{sellstg}{text.split('SELL_LONG')[0]}sell_cond = {count}\n"
                count += 1
            elif 'BUY_SHORT = True' in text or 'BUY_SHORT= True' in text or 'BUY_SHORT =True' in text or 'BUY_SHORT=True' in text:
                dict_cond[count] = selllist[i - 1]
                sellstg = f"{sellstg}{text.split('BUY_SHORT')[0]}sell_cond = {count}\n"
                count += 1
        if text != '':
            sellstg = f"{sellstg}{text}\n"
    return sellstg, dict_cond


def SendTextAndStd(result, dict_train, dict_valid=None, exponential=False):
    gubun, ui_gubun, wq, mq, stdp, optistd, opti_turn, vturn, vkey, vars_list, startday, endday, std_list, betting = result
    if gubun in ('최적화', '최적화테스트'):
        text1 = GetText1(opti_turn, vturn, vars_list)
    elif gubun == 'GA최적화':
        text1 = f'<font color=white> V{vars_list} </font>'
    elif gubun == '전진분석':
        text1 = f'<font color=#f78645>[IN] P[{startday}~{endday}]</font>{GetText1(opti_turn, vturn, vars_list)}'
    else:
        text1 = ''

    stdp_ = 0
    if dict_valid is not None:
        tuple_train = sorted(dict_train.items(), key=operator.itemgetter(0))
        tuple_valid = sorted(dict_valid.items(), key=operator.itemgetter(0))
        train_text = []
        valid_text = []
        train_data = []
        valid_data = []

        for k, v in tuple_train:
            text2, std = GetText2(f'TRAIN{k + 1}', optistd, std_list, betting, v)
            train_text.append(text2)
            train_data.append(std)
        for k, v in tuple_valid:
            text2, std = GetText2(f'VALID{k + 1}', optistd, std_list, betting, v)
            valid_text.append(text2)
            valid_data.append(std)

        std = GetOptiValidStd(train_data, valid_data, optistd, betting, exponential)
        text3, stdp_ = GetText3(std, stdp)
        if opti_turn == 2: text3 = ''

        wq.put((ui_num[f'{ui_gubun}백테스트'], f'{text1}{text3}'))
        for text in train_text:
            wq.put((ui_num[f'{ui_gubun}백테스트'], text))
        for text in valid_text:
            wq.put((ui_num[f'{ui_gubun}백테스트'], text))
    elif dict_train is not None:
        if gubun == '최적화테스트':
            text2, std = GetText2('TEST', optistd, std_list, betting, dict_train)
            text3 = ''
        else:
            text2, std = GetText2('TOTAL', optistd, std_list, betting, dict_train)
            text3, stdp_ = GetText3(std, stdp)
        wq.put((ui_num[f'{ui_gubun}백테스트'], f'{text1}{text2}{text3}'))
    else:
        stdp_ = stdp
        std = -2_000_000_000
        text2 = '매수전략을 만족하는 경우가 없어 결과를 표시할 수 없습니다.'
        wq.put((ui_num[f'{ui_gubun}백테스트'], f'{text1}{text2}'))

    if opti_turn != 2:
        mq.put((vturn, vkey, std))
    return stdp_


def GetText1(opti_turn, vturn, vars_list):
    prev_vars, curr_vars, next_vars = '', '', ''
    if opti_turn != 1:
        next_vars = f'<font color=#6eff6e> V{vars_list} </font>'
    else:
        prev_vars = f' V{vars_list[:vturn]}'.split(']')[0]
        prev_vars = f'<font color=white>{prev_vars}</font>' if vturn == 0 else f'<font color=white>{prev_vars}, </font>'
        curr_vars = f'<font color=#6eff6e>{vars_list[vturn]}</font>'
        next_vars = f'{vars_list[vturn + 1:]}'.split('[')[1]
        if next_vars != ']': next_vars = f', {next_vars}'
        next_vars = f'<font color=white>{next_vars} </font>'
    return f'{prev_vars}{curr_vars}{next_vars}'


def GetText2(gubun, optistd, std_list, betting, result):
    tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi, mdd, mdd_ = result
    if tpp < 0 < tsg: tsg = -2_147_483_648
    mddt = f'{mdd_:,.0f}' if 'G' in optistd else f'{mdd:,.2f}%'
    text = f'{gubun} TC[{tc:,.0f}] ATC[{atc:,.1f}] MH[{mhct}] WR[{wr:,.2f}%] MDD[{mddt}] CAGR[{cagr:,.2f}] TPI[{tpi:,.2f}] AP[{app:,.2f}%] TP[{tpp:,.2f}%] TG[{tsg:,.0f}]'
    std, text = GetOptiStdText(optistd, std_list, betting, result, text)
    text = f'<font color=white>{text}</font>' if tsg >= 0 else f'<font color=#96969b>{text}</font>'
    return text, std


def GetText3(std, stdp):
    text = f'<font color=#f78645>MERGE[{std:,.2f}]</font>'
    if std >= stdp:
        text = f'{text}<font color=#6eff6e>[기준값갱신]</font>' if std > stdp else f'{text}<font color=white>[기준값동일]</font>'
        stdp = std
    return text, stdp


def GetOptiValidStd(train_data, valid_data, optistd, betting, exponential):
    """
    교차검증 최적화 표준값 계산

    변경사항 (2025-11-29):
    - std_false_point (-2,222,222,222) 데이터는 계산에서 제외
    - 유효한 데이터 쌍만으로 평균 계산
    - 모든 데이터가 조건 불만족이면 std_false_point 반환

    가중치(exponential) 예제:
    10개 : 2.00, 1.80, 1.60, 1.40, 1.20, 1.00, 0.80, 0.60, 0.40, 0.20
    8개  : 2.00, 1.75, 1.50, 1.25, 1.00, 0.75, 0.50, 0.25
    7개  : 2.00, 1.71, 1.42, 1.14, 0.86, 0.57, 0.29
    6개  : 2.00, 1.66, 1.33, 1.00, 0.66, 0.33
    5개  : 2.00, 1.60, 1.20, 0.80, 0.40
    4개  : 2.00, 1.50, 1.00, 0.50
    3개  : 2.00, 1.33, 0.66
    2개  : 2.00, 1.0
    """
    std = 0
    valid_count = 0  # 유효한 데이터 쌍 개수
    total_count = len(train_data)
    std_false_point = -2_222_222_222

    for i in range(total_count):
        # 제한 조건 불만족 데이터는 건너뛰기
        if train_data[i] == std_false_point or valid_data[i] == std_false_point:
            continue

        valid_count += 1

        # 가중치 계산 (지수 가중치 옵션)
        if exponential and total_count > 1:
            ex = (total_count - i) * 2 / total_count
        else:
            ex = 1

        # TRAIN × VALID 곱셈
        std_ = train_data[i] * valid_data[i] * ex

        # 누적 (둘 다 음수면 절댓값으로 처리)
        if train_data[i] < 0 and valid_data[i] < 0:
            std = std - std_
        else:
            std = std + std_

    # 유효한 데이터가 없으면 조건 불만족 반환
    if valid_count == 0:
        return std_false_point

    # 평균 계산 (유효 개수로 나눔)
    if optistd == 'TG':
        std = round(std / valid_count / betting, 2)
    else:
        std = round(std / valid_count, 2)

    return std


def GetOptiStdText(optistd, std_list, betting, result, pre_text):
    mdd_low, mdd_high, mhct_low, mhct_high, wr_low, wr_high, ap_low, ap_high, atc_low, atc_high, cagr_low, cagr_high, tpi_low, tpi_high = std_list
    tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi, mdd, mdd_ = result
    std_true = (mdd_low <= mdd <= mdd_high and mhct_low <= mhct <= mhct_high and wr_low <= wr <= wr_high and
                ap_low <= app <= ap_high and atc_low <= atc <= atc_high and cagr_low <= cagr <= cagr_high and tpi_low <= tpi <= tpi_high)
    std, pm, p2m, pam, pwm, ptm, gm, g2m, gam, gwm, gtm, text = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ''
    std_false_point = -2_222_222_222
    if tc > 0:
        if 'TRAIN' in pre_text or 'TOTAL' in pre_text:
            if 'P' in optistd:
                if optistd == 'TP':
                    std = tpp if std_true else std_false_point
                elif optistd == 'TPI':
                    std = tpi if std_true else std_false_point
                elif optistd == 'PM':
                    std = pm = round(tpp / mdd, 2) if std_true else std_false_point
                elif optistd == 'P2M':
                    std = p2m = round(tpp * tpp / mdd / 100, 2) if std_true else std_false_point
                elif optistd == 'PAM':
                    std = pam = round(tpp * app / mdd, 2) if std_true else std_false_point
                elif optistd == 'PWM':
                    std = pwm = round(tpp * wr / mdd / 100, 2) if std_true else std_false_point
                elif optistd == 'PTM':
                    std = ptm = round(tpp * app * wr * tpi * cagr / mdd / 10000, 2) if std_true else std_false_point
            elif 'G' in optistd:
                if optistd == 'TG':
                    std = tsg if std_true else std_false_point
                elif optistd == 'GM':
                    std = gm = round(tsg / mdd_, 2) if std_true else std_false_point
                elif optistd == 'G2M':
                    std = g2m = round(tsg * tsg / mdd_ / betting, 2) if std_true else std_false_point
                elif optistd == 'GAM':
                    std = gam = round(tsg * app / mdd_, 2) if std_true else std_false_point
                elif optistd == 'GWM':
                    std = gwm = round(tsg * wr / mdd_ / 100, 2) if std_true else std_false_point
                elif optistd == 'GTM':
                    std = gtm = round(tsg * app * wr * tpi * cagr / mdd_ / 10000, 2) if std_true else std_false_point
                elif optistd == 'CAGR':
                    std = cagr if std_true else std_false_point
        else:
            if 'P' in optistd:
                if optistd == 'TP':
                    std = tpp if std_true else std_false_point
                elif optistd == 'TPI':
                    std = tpi if std_true else std_false_point
                elif optistd == 'PM':
                    std = pm = round(tpp / mdd, 2) if std_true else std_false_point
                elif optistd == 'P2M':
                    std = p2m = round(tpp * tpp / mdd / 100, 2) if std_true else std_false_point
                elif optistd == 'PAM':
                    std = pam = round(tpp * app / mdd, 2) if std_true else std_false_point
                elif optistd == 'PWM':
                    std = pwm = round(tpp * wr / mdd / 100, 2) if std_true else std_false_point
                elif optistd == 'PTM':
                    std = ptm = round(tpp * app * wr * tpi * cagr / mdd / 10000, 2) if std_true else std_false_point
            elif 'G' in optistd:
                if optistd == 'TG':
                    std = tsg if std_true else std_false_point
                elif optistd == 'GM':
                    std = gm = round(tsg / mdd_, 2) if std_true else std_false_point
                elif optistd == 'G2M':
                    std = g2m = round(tsg * tsg / mdd_ / betting, 2) if std_true else std_false_point
                elif optistd == 'GAM':
                    std = gam = round(tsg * app / mdd_, 2) if std_true else std_false_point
                elif optistd == 'GWM':
                    std = gwm = round(tsg * wr / mdd_ / 100, 2) if std_true else std_false_point
                elif optistd == 'GTM':
                    std = gtm = round(tsg * app * wr * tpi * cagr / mdd_ / 10000, 2) if std_true else std_false_point
                elif optistd == 'CAGR':
                    std = cagr if std_true else std_false_point

    if optistd == 'TP':
        text = pre_text
    elif optistd == 'TG':
        text = pre_text
    elif optistd == 'TPI':
        text = pre_text
    elif optistd == 'CAGR':
        text = pre_text
    elif optistd == 'PM':
        text = f'{pre_text} PM[{pm:.2f}]'
    elif optistd == 'P2M':
        text = f'{pre_text} P2M[{p2m:.2f}]'
    elif optistd == 'PAM':
        text = f'{pre_text} PAM[{pam:.2f}]'
    elif optistd == 'PWM':
        text = f'{pre_text} PWM[{pwm:.2f}]'
    elif optistd == 'PTM':
        text = f'{pre_text} PTM[{ptm:.2f}]'
    elif optistd == 'GM':
        text = f'{pre_text} GM[{gm:.2f}]'
    elif optistd == 'G2M':
        text = f'{pre_text} G2M[{g2m:.2f}]'
    elif optistd == 'GAM':
        text = f'{pre_text} GAM[{gam:.2f}]'
    elif optistd == 'GWM':
        text = f'{pre_text} GWM[{gwm:.2f}]'
    elif optistd == 'GTM':
        text = f'{pre_text} GTM[{gtm:.2f}]'
    return std, text


def PltShow(gubun, teleQ, df_tsg, df_bct, dict_cn, seed, mdd, startday, endday, starttime, endtime, df_kp_, df_kd_, list_days,
            backname, back_text, label_text, save_file_name, schedul, plotgraph, buy_vars=None, sell_vars=None,
            buystg=None, sellstg=None, buystg_name=None, sellstg_name=None, ml_train_mode='train', progress_logs=None):
    df_tsg['수익금합계020'] = df_tsg['수익금합계'].rolling(window=20).mean().round(2)
    df_tsg['수익금합계060'] = df_tsg['수익금합계'].rolling(window=60).mean().round(2)
    df_tsg['수익금합계120'] = df_tsg['수익금합계'].rolling(window=120).mean().round(2)
    df_tsg['수익금합계240'] = df_tsg['수익금합계'].rolling(window=240).mean().round(2)
    df_tsg['수익금합계480'] = df_tsg['수익금합계'].rolling(window=480).mean().round(2)

    profit_values = df_tsg['수익금'].to_numpy(dtype=np.float64)
    df_tsg['이익금액'] = np.where(profit_values >= 0, profit_values, 0)
    df_tsg['손실금액'] = np.where(profit_values < 0, profit_values, 0)

    # 거래가 매우 많으면(예: 60,000건) 차트 렌더링/강화분석 시간이 길어 텔레그램 알림이 늦어질 수 있어,
    # 우선 "진행 중" 메시지를 먼저 전송합니다.
    if teleQ is not None:
        try:
            lines = []
            has_condition = bool(buystg_name or sellstg_name or buystg or sellstg)
            if has_condition:
                sk_short = 'N/A'
                try:
                    if ENHANCED_ANALYSIS_AVAILABLE and (buystg or sellstg):
                        sk = ComputeStrategyKey(buystg=buystg, sellstg=sellstg)
                        if sk:
                            sk_short = (str(sk)[:12] + '...') if len(str(sk)) > 12 else str(sk)
                except Exception:
                    sk_short = 'N/A'

                is_opt = bool(backname and ('최적화' in str(backname)))
                buy_label = "매수 최적화 조건식" if is_opt else "매수 조건식"
                sell_label = "매도 최적화 조건식" if is_opt else "매도 조건식"
                buy_name = buystg_name if buystg_name else 'N/A'
                sell_name = sellstg_name if sellstg_name else 'N/A'

                lines.append("매수/매도 조건식(이름):")
                lines.append(f"- 전략키: {sk_short}")
                lines.append(f"- {buy_label}: {buy_name}")
                lines.append(f"- {sell_label}: {sell_name}")
                lines.append("- 상세 설명/코드/산출물: report.txt 및 models/strategy_code.txt 참고")

            if progress_logs:
                if lines:
                    lines.append("")
                lines.append("백테스트 진행 로그:")
                lines.extend([str(x) for x in progress_logs])

            if lines:
                teleQ.put("\n".join(lines))
            teleQ.put(f'{backname} {save_file_name.split("_")[1]} 분석/차트 생성 중... (거래 {len(df_tsg):,}회)')
        except:
            pass
    sig_list = df_tsg['수익금'].to_list()
    mdd_list = []
    for i in range(30):
        random.shuffle(sig_list)
        df_tsg[f'수익금{i}'] = sig_list
        df_tsg[f'수익금합계{i}'] = df_tsg[f'수익금{i}'].cumsum()
        df_tsg.drop(columns=[f'수익금{i}'], inplace=True)
        try:
            array = np.array(df_tsg[f'수익금합계{i}'], dtype=np.float64)
            lower = np.argmax(np.maximum.accumulate(array) - array)
            upper = np.argmax(array[:lower])
            mdd_ = round(abs(array[upper] - array[lower]) / (array[upper] + seed) * 100, 2)
        except:
            mdd_ = 0.
        mdd_list.append(mdd_)

    is_min = len(str(endtime)) < 5
    df_sg = df_tsg[['수익금']].copy()
    df_sg['일자'] = df_sg.index
    df_sg['일자'] = df_sg['일자'].apply(lambda x: strp_time('%Y%m%d%H%M%S' if not is_min else '%Y%m%d%H%M', x))
    df_sg = df_sg.set_index('일자')

    df_ts = df_sg.resample('D').sum()
    df_ts['수익금합계'] = df_ts['수익금'].cumsum()
    df_ts['수익금합계'] = ((df_ts['수익금합계'] + seed) / seed - 1) * 100

    df_kp, df_kd, df_bc = None, None, None
    if dict_cn is not None:
        df_kp = df_kp_[(df_kp_['index'] >= str(startday)) & (df_kp_['index'] <= str(endday))].copy()
        df_kd = df_kd_[(df_kd_['index'] >= str(startday)) & (df_kd_['index'] <= str(endday))].copy()
        df_kp['종가'] = (df_kp['종가'] / df_kp['종가'].iloc[0] - 1) * 100
        df_kd['종가'] = (df_kd['종가'] / df_kd['종가'].iloc[0] - 1) * 100
        df_kp['일자'] = df_kp['index'].apply(lambda x: strp_time('%Y%m%d', x))
        df_kd['일자'] = df_kd['index'].apply(lambda x: strp_time('%Y%m%d', x))
        df_kp.drop(columns=['index'], inplace=True)
        df_kd.drop(columns=['index'], inplace=True)
        df_kp.set_index('일자', inplace=True)
        df_kd.set_index('일자', inplace=True)
    else:
        df_bc = pyupbit.get_ohlcv()
        df_bc['일자'] = df_bc.index
        startday = strp_time('%Y%m%d', str(startday))
        endday = strp_time('%Y%m%d%H%M%S', str(endday) + '235959')
        df_bc = df_bc[(df_bc['일자'] >= startday) & (df_bc['일자'] <= endday)]
        df_bc['close'] = (df_bc['close'] / df_bc['close'].iloc[0] - 1) * 100

    df_st = df_tsg[['수익금']].copy()
    df_st['시간'] = df_st.index
    df_st['시간'] = df_st['시간'].apply(lambda x: strp_time('%H%M%S' if not is_min else '%H%M', x[8:]))
    df_st.set_index('시간', inplace=True)
    if not is_min:
        start_time = strp_time('%H%M%S', str(starttime).zfill(6))
        end_time = strp_time('%H%M%S', str(endtime).zfill(6))
    else:
        start_time = strp_time('%H%M', str(starttime).zfill(4))
        end_time = strp_time('%H%M', str(endtime).zfill(4))
    total_sec = (end_time - start_time).total_seconds()
    df_st = df_st.resample(f'{total_sec / 600 if total_sec >= 1800 else 3}min').sum()
    df_st['시간'] = df_st.index
    df_st['시간'] = df_st['시간'].apply(lambda x: strf_time('%H%M%S' if not is_min else '%H%M', x))
    if not is_min:
        df_st['시간'] = df_st['시간'].apply(lambda x: f'{x[:2]}:{x[2:4]}:{x[4:]}')
    else:
        df_st['시간'] = df_st['시간'].apply(lambda x: f'{x[:2]}:{x[2:]}')
    df_st.set_index('시간', inplace=True)
    df_st['이익금액'] = df_st['수익금'].apply(lambda x: x if x >= 0 else 0)
    df_st['손실금액'] = df_st['수익금'].apply(lambda x: x if x < 0 else 0)

    df_wt = df_tsg[['수익금']].copy()
    df_wt['요일'] = df_wt.index
    df_wt['요일'] = df_wt['요일'].apply(lambda x: strp_time('%Y%m%d%H%M%S' if not is_min else '%Y%m%d%H%M', x).weekday())
    sum_0 = df_wt[df_wt['요일'] == 0]['수익금'].sum()
    sum_1 = df_wt[df_wt['요일'] == 1]['수익금'].sum()
    sum_2 = df_wt[df_wt['요일'] == 2]['수익금'].sum()
    sum_3 = df_wt[df_wt['요일'] == 3]['수익금'].sum()
    sum_4 = df_wt[df_wt['요일'] == 4]['수익금'].sum()
    wt_index = ['월', '화', '수', '목', '금']
    wt_data = [sum_0, sum_1, sum_2, sum_3, sum_4]
    if dict_cn is None:
        sum_5 = df_wt[df_wt['요일'] == 5]['수익금'].sum()
        sum_6 = df_wt[df_wt['요일'] == 6]['수익금'].sum()
        wt_index += ['토', '일']
        wt_data += [sum_5, sum_6]
    wt_datap, wt_datam = [], []
    for data in wt_data:
        if data >= 0:
            wt_datap.append(data)
            wt_datam.append(0)
        else:
            wt_datap.append(0)
            wt_datam.append(data)

    df_tsg['index'] = df_tsg.index
    if not is_min:
        df_tsg['index'] = df_tsg['index'].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:12]}:{x[12:14]}')
    else:
        df_tsg['index'] = df_tsg['index'].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:]}')
    df_tsg.set_index('index', inplace=True)

    endx_list = None
    if gubun == '최적화':
        if not is_min:
            endx_list = [df_tsg[df_tsg['매도시간'] < list_days[2][0] * 1000000 + 240000].index[-1]]
        else:
            endx_list = [df_tsg[df_tsg['매도시간'] < list_days[2][0] * 10000 + 2400].index[-1]]
        if list_days[1] is not None:
            for vsday, _, _ in list_days[1]:
                if not is_min:
                    df_tsg_ = df_tsg[df_tsg['매도시간'] < vsday * 1000000]
                else:
                    df_tsg_ = df_tsg[df_tsg['매도시간'] < vsday * 10000]
                if len(df_tsg_) > 0:
                    endx_list.append(df_tsg_.index[-1])

    font_name = 'C:/Windows/Fonts/malgun.ttf'
    font_family = font_manager.FontProperties(fname=font_name).get_name()
    plt.rcParams['font.family'] = font_family
    plt.rcParams['axes.unicode_minus'] = False

    plt.figure(f'{backname} 부가정보', figsize=(12, 10))
    gs = gridspec.GridSpec(nrows=2, ncols=2, height_ratios=[1, 1])
    # noinspection PyTypeChecker
    plt.subplot(gs[0])
    for i in range(30):
        plt.plot(df_tsg.index, df_tsg[f'수익금합계{i}'], linewidth=0.5, label=f'MDD {mdd_list[i]}%')
    plt.plot(df_tsg.index, df_tsg['수익금합계'], linewidth=2, label=f'MDD {mdd}%', color='orange')
    max_mdd = max(mdd_list)
    min_mdd = min(mdd_list)
    avg_mdd = round(sum(mdd_list) / len(mdd_list), 2)
    plt.title(f'Max MDD [{max_mdd}%] | Min MDD [{min_mdd}%] | Avg MDD [{avg_mdd}%]')
    count = int(len(df_tsg) / 15) if int(len(df_tsg) / 15) >= 1 else 1
    plt.xticks(list(df_tsg.index[::count]), rotation=45)
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[1])
    plt.plot(df_ts.index, df_ts['수익금합계'], linewidth=2, label='수익률', color='orange')
    if dict_cn is not None:
        plt.plot(df_kp.index, df_kp['종가'], linewidth=0.5, label='코스피', color='r')
        plt.plot(df_kd.index, df_kd['종가'], linewidth=0.5, label='코스닥', color='b')
    else:
        plt.plot(df_bc.index, df_bc['close'], linewidth=0.5, label='KRW-BTC', color='r')
    plt.title('지수비교' if dict_cn is not None else 'BTC비교')
    count = int(len(df_ts) / 20) if int(len(df_ts) / 20) >= 1 else 1
    plt.xticks(list(df_ts.index[::count]), rotation=45)
    plt.legend(loc='best')
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[2])
    plt.bar(df_st.index, df_st['이익금액'], label='이익금액', color='r')
    plt.bar(df_st.index, df_st['손실금액'], label='손실금액', color='b')
    plt.title('시간별 수익금')
    plt.xticks(list(df_st.index), rotation=45)
    plt.legend(loc='best')
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[3])
    plt.bar(wt_index, wt_datap, label='이익금액', color='r')
    plt.bar(wt_index, wt_datam, label='손실금액', color='b')
    plt.title('요일별 수익금')
    plt.xticks(wt_index)
    plt.legend(loc='best')
    plt.grid()
    plt.tight_layout()
    plt.savefig(f"{GRAPH_PATH}/{save_file_name}_.png")

    if buy_vars is None:
        plt.figure(f'{backname} 결과', figsize=(12, 10))
    else:
        plt.figure(f'{backname} 결과', figsize=(12, 12))
    gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[1, 4])
    # noinspection PyTypeChecker
    plt.subplot(gs[0])
    plt.plot(df_bct.index, df_bct['보유금액'], label='보유금액', color='g')
    plt.xticks([])
    if buy_vars is None:
        plt.xlabel('\n' + back_text + '\n' + label_text)
    else:
        plt.xlabel('\n' + back_text + '\n' + label_text + '\n\n' + buy_vars + '\n\n' + sell_vars)
    plt.legend(loc='best')
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[1])
    n_trades = len(df_tsg)
    max_plot_points = 5000
    if n_trades > max_plot_points:
        # 대용량 데이터에서는 bar/scatter 렌더링이 매우 느려지므로, 표시용으로만 구간 집계/샘플링합니다.
        step = int(math.ceil(n_trades / max_plot_points))
        start_idx = np.arange(0, n_trades, step, dtype=np.int64)
        end_idx = np.minimum(start_idx + step - 1, n_trades - 1)
        x = np.arange(len(end_idx))

        profit_bar = np.add.reduceat(df_tsg['이익금액'].to_numpy(dtype=np.float64), start_idx)
        loss_bar = np.add.reduceat(df_tsg['손실금액'].to_numpy(dtype=np.float64), start_idx)

        plt.bar(x, profit_bar, label=f'이익금액(집계:{step}건)', color='r')
        plt.bar(x, loss_bar, label=f'손실금액(집계:{step}건)', color='b')

        def _sample(col: str):
            return df_tsg[col].to_numpy(dtype=np.float64)[end_idx]

        plt.plot(x, _sample('수익금합계480'), linewidth=0.5, label='수익금합계480', color='k')
        plt.plot(x, _sample('수익금합계240'), linewidth=0.5, label='수익금합계240', color='gray')
        plt.plot(x, _sample('수익금합계120'), linewidth=0.5, label='수익금합계120', color='b')
        plt.plot(x, _sample('수익금합계060'), linewidth=0.5, label='수익금합계60', color='g')
        plt.plot(x, _sample('수익금합계020'), linewidth=0.5, label='수익금합계20', color='r')
        plt.plot(x, _sample('수익금합계'), linewidth=2, label='수익금합계', color='orange')

        if gubun == '최적화':
            for i, endx in enumerate(endx_list):
                try:
                    pos_full = df_tsg.index.get_loc(endx)
                    pos = int(pos_full / step)
                    plt.axvline(x=pos, color='red' if i == 0 else 'green', linestyle='--')
                except:
                    continue
            try:
                pos0_full = df_tsg.index.get_loc(endx_list[0])
                pos0 = int(pos0_full / step)
                plt.axvspan(pos0, x[-1], facecolor='gray', alpha=0.1)
            except:
                pass

        tick_step = max(1, int(len(x) / 20))
        tick_positions = list(x[::tick_step])
        tick_labels = [str(v) for v in df_tsg.index[end_idx][::tick_step]]
        plt.xticks(tick_positions, tick_labels, rotation=45)
    else:
        plt.bar(df_tsg.index, df_tsg['이익금액'], label='이익금액', color='r')
        plt.bar(df_tsg.index, df_tsg['손실금액'], label='손실금액', color='b')
        plt.plot(df_tsg.index, df_tsg['수익금합계480'], linewidth=0.5, label='수익금합계480', color='k')
        plt.plot(df_tsg.index, df_tsg['수익금합계240'], linewidth=0.5, label='수익금합계240', color='gray')
        plt.plot(df_tsg.index, df_tsg['수익금합계120'], linewidth=0.5, label='수익금합계120', color='b')
        plt.plot(df_tsg.index, df_tsg['수익금합계060'], linewidth=0.5, label='수익금합계60', color='g')
        plt.plot(df_tsg.index, df_tsg['수익금합계020'], linewidth=0.5, label='수익금합계20', color='r')
        plt.plot(df_tsg.index, df_tsg['수익금합계'], linewidth=2, label='수익금합계', color='orange')
        if gubun == '최적화':
            for i, endx in enumerate(endx_list):
                plt.axvline(x=endx, color='red' if i == 0 else 'green', linestyle='--')
            plt.axvspan(endx_list[0], df_tsg.index[-1], facecolor='gray', alpha=0.1)
        count = int(len(df_tsg) / 20) if int(len(df_tsg) / 20) >= 1 else 1
        plt.xticks(list(df_tsg.index[::count]), rotation=45)
    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.savefig(f"{GRAPH_PATH}/{save_file_name}.png")

    teleQ.put(f'{backname} {save_file_name.split("_")[1]} 완료.')
    teleQ.put(f"{GRAPH_PATH}/{save_file_name}_.png")
    teleQ.put(f"{GRAPH_PATH}/{save_file_name}.png")

    # [2025-12-08] 분석 차트 생성 및 텔레그램 전송 (8개 기본 분석 차트)
    PltAnalysisCharts(df_tsg, save_file_name, teleQ)

    # [2025-12-09] 매수/매도 비교 분석 및 CSV 출력
    # - 강화 분석을 사용할 경우: detail/filter CSV는 강화 분석 결과로 통합(중복 생성 방지)
    full_result = RunFullAnalysis(
        df_tsg,
        save_file_name,
        teleQ,
        export_detail=not ENHANCED_ANALYSIS_AVAILABLE,
        export_summary=True,
        export_filter=not ENHANCED_ANALYSIS_AVAILABLE,
        include_filter_recommendations=not ENHANCED_ANALYSIS_AVAILABLE
    )

    # [2025-12-10] 강화된 분석 실행 (14개 ML/통계 분석 차트)
    enhanced_result = None
    enhanced_error = None
    if ENHANCED_ANALYSIS_AVAILABLE:
        try:
            enhanced_result = RunEnhancedAnalysis(
                df_tsg,
                save_file_name,
                teleQ,
                buystg=buystg,
                sellstg=sellstg,
                buystg_name=buystg_name,
                sellstg_name=sellstg_name,
                backname=backname,
                ml_train_mode=ml_train_mode,
                send_condition_summary=False,
            )

            # [2025-12-19] 자동 생성 필터 조합 적용 미리보기 차트(2개) 생성/전송
            try:
                if teleQ is not None and enhanced_result:
                    gen = enhanced_result.get('generated_code')
                    df_enh = enhanced_result.get('enhanced_df')
                    if isinstance(gen, dict) and isinstance(df_enh, pd.DataFrame) and not df_enh.empty:
                        mask_info = _build_filter_mask_from_generated_code(df_enh, gen)
                        if mask_info and mask_info.get('mask') is not None:
                            df_filt = df_enh[mask_info['mask']].copy()

                            try:
                                total_profit = int(pd.to_numeric(df_enh['수익금'], errors='coerce').fillna(0).sum())
                                filt_profit = int(pd.to_numeric(df_filt['수익금'], errors='coerce').fillna(0).sum())
                                ex_pct = (1.0 - (len(df_filt) / max(1, len(df_enh)))) * 100.0
                                teleQ.put(
                                    "필터 적용 미리보기:\n"
                                    f"- 거래수: {len(df_enh):,} → {len(df_filt):,} (제외 {ex_pct:.1f}%)\n"
                                    f"- 수익금: {total_profit:,}원 → {filt_profit:,}원 ({(filt_profit-total_profit):+,}원)\n"
                                    "- 이미지: 필터 적용 미리보기 2종 전송"
                                )
                            except Exception:
                                pass

                            p_main, p_sub = PltFilterAppliedPreviewCharts(
                                df_enh,
                                df_filt,
                                save_file_name=save_file_name,
                                backname=backname,
                                seed=seed,
                                generated_code=gen,
                                buystg=buystg,
                                sellstg=sellstg
                            )
                            if p_sub:
                                teleQ.put(p_sub)
                            if p_main:
                                teleQ.put(p_main)
                        else:
                            err = mask_info.get('error') if isinstance(mask_info, dict) else 'N/A'
                            failed_expr = mask_info.get('failed_expr') if isinstance(mask_info, dict) else None
                            msg = "필터 적용 미리보기: 마스크 생성 실패"
                            if err:
                                msg += f"\n- 오류: {err}"
                            if failed_expr:
                                msg += f"\n- 실패 조건식: {failed_expr}"
                            teleQ.put(msg)
            except Exception:
                print_exc()
        except Exception as e:
            enhanced_error = e
            print_exc()
            # 강화 분석 실패 시: 기본 detail/filter CSV를 생성해 결과 보존
            try:
                ExportBacktestCSV(
                    df_tsg,
                    save_file_name,
                    teleQ,
                    write_detail=True,
                    write_summary=False,
                    write_filter=True
                )
                if teleQ is not None:
                    df_fallback = CalculateDerivedMetrics(df_tsg)
                    filter_results = AnalyzeFilterEffects(df_fallback)
                    top_filters = [f for f in filter_results if f.get('적용권장', '').count('★') >= 2]
                    recs = [
                        f"[{f['분류']}] {f['필터명']}: 수익개선 {f['수익개선금액']:,}원 예상"
                        for f in top_filters[:5]
                    ]
                    if recs:
                        teleQ.put("📊 필터 추천:\n" + "\n".join(recs))
            except:
                print_exc()

    # [2025-12-14] 산출물 메타 리포트(txt) 저장
    WriteGraphOutputReport(
        save_file_name=save_file_name,
        df_tsg=df_tsg,
        backname=backname,
        seed=seed,
        mdd=mdd,
        startday=startday,
        endday=endday,
        starttime=starttime,
        endtime=endtime,
        buy_vars=buy_vars,
        sell_vars=sell_vars,
        buystg=buystg,
        sellstg=sellstg,
        full_result=full_result,
        enhanced_result=enhanced_result,
        enhanced_error=enhanced_error
    )

    if not schedul and not plotgraph:
        plt.show()


def GetResultDataframe(ui_gubun, list_tsg, arry_bct):
    # [2025-12-10] 확장된 50개 컬럼 사용 (매수/매도 시점 시장 데이터 포함)
    # list_tsg에는 'index'가 포함되지만 '수익금합계'는 없음 (나중에 cumsum으로 계산)
    if ui_gubun in ['CT', 'CF']:
        # 코인: 포지션 컬럼 사용
        columns_without_sum = [col for col in columns_btf if col != '수익금합계']
        columns1 = ['index'] + columns_without_sum
        columns2 = columns_btf
    else:
        # 주식: 시가총액 컬럼 사용
        columns_without_sum = [col for col in columns_bt if col != '수익금합계']
        columns1 = ['index'] + columns_without_sum
        columns2 = columns_bt

    df_tsg = pd.DataFrame(list_tsg, columns=columns1)
    df_tsg.set_index('index', inplace=True)
    df_tsg.sort_index(inplace=True)
    df_tsg['수익금합계'] = df_tsg['수익금'].cumsum()
    df_tsg = df_tsg[columns2]
    arry_bct = arry_bct[arry_bct[:, 1] > 0]
    df_bct = pd.DataFrame(arry_bct[:, 1:], columns=['보유종목수', '보유금액'], index=arry_bct[:, 0])
    df_bct.index = df_bct.index.astype(str)
    return df_tsg, df_bct


def AddMdd(arry_tsg, result):
    """
    arry_tsg
    보유시간, 매도시간, 수익률, 수익금, 수익금합계
      0       1       2       3      4
    """
    try:
        array = arry_tsg[:, 4]
        lower = np.argmax(np.maximum.accumulate(array) - array)
        upper = np.argmax(array[:lower])
        mdd   = round(abs(array[upper] - array[lower]) / (array[upper] + result[10]) * 100, 2)
        mdd_  = int(abs(array[upper] - array[lower]))
    except:
        mdd   = abs(result[7])
        mdd_  = abs(result[8])
    result = result + (mdd, mdd_)
    return result


@jit(nopython=True, cache=True)
def GetBackResult(arry_tsg, arry_bct, betting, ui_gubun, day_count):
    """ dtype = 'float64'
    arry_tsg
    보유시간, 매도시간, 수익률, 수익금, 수익금합계
      0       1       2       3      4
    arry_bct
    체결시간, 보유중목수, 보유금액
      0         1        2
    """
    tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    tc = len(arry_tsg)
    if tc > 0:
        arry_p = arry_tsg[arry_tsg[:, 3] >= 0]
        arry_m = arry_tsg[arry_tsg[:, 3] < 0]
        atc    = round(tc / day_count, 1)
        pc     = len(arry_p)
        mc     = len(arry_m)
        wr     = round(pc / tc * 100, 2)
        ah     = round(arry_tsg[:, 0].sum() / tc, 2)
        app    = round(arry_tsg[:, 2].sum() / tc, 2)
        tsg    = int(arry_tsg[:, 3].sum())
        appp   = arry_p[:, 2].mean() if len(arry_p) > 0 else 0
        ampp   = abs(arry_m[:, 2].mean()) if len(arry_m) > 0 else 0
        try:    mhct = int(arry_bct[int(len(arry_bct) * 0.01):, 1].max())
        except: mhct = 0
        try:    seed = int(arry_bct[int(len(arry_bct) * 0.01):, 2].max())
        except: seed = betting
        tpp    = round(tsg / (seed if seed != 0 else betting) * 100, 2)
        cagr   = round(tpp / day_count * (250 if ui_gubun == 'S' else 365), 2)
        tpi    = round(wr / 100 * (1 + appp / ampp), 2) if ampp != 0 else 1.0

    return tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi


def GetIndicator(mc, mh, ml, mv, k):
    AD, ADOSC, ADXR, APO, AROOND, AROONU, ATR, BBU, BBM, BBL, CCI, DIM, DIP, MACD, MACDS, MACDH, MFI, MOM, OBV, PPO, \
        ROC, RSI, SAR, STOCHSK, STOCHSD, STOCHFK, STOCHFD, WILLR = \
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    try:    AD                     = stream.AD(      mh, ml, mc, mv)
    except: AD                     = 0
    if k[0] != 0:
        try:    ADOSC              = stream.ADOSC(   mh, ml, mc, mv, fastperiod=k[0], slowperiod=k[1])
        except: ADOSC              = 0
    if k[2] != 0:
        try:    ADXR               = stream.ADXR(    mh, ml, mc,     timeperiod=k[2])
        except: ADXR               = 0
    if k[3] != 0:
        try:    APO                = stream.APO(     mc,             fastperiod=k[3], slowperiod=k[4], matype=k[5])
        except: APO                = 0
    if k[6] != 0:
        try:    AROOND, AROONU     = stream.AROON(   mh, ml,         timeperiod=k[6])
        except: AROOND, AROONU     = 0, 0
    if k[7] != 0:
        try:    ATR                = stream.ATR(     mh, ml, mc,     timeperiod=k[7])
        except: ATR                = 0
    if k[8] != 0:
        try:    BBU, BBM, BBL      = stream.BBANDS(  mc,             timeperiod=k[8], nbdevup=k[9], nbdevdn=k[10], matype=k[11])
        except: BBU, BBM, BBL      = 0, 0, 0
    if k[12] != 0:
        try:    CCI                = stream.CCI(     mh, ml, mc,     timeperiod=k[12])
        except: CCI                = 0
    if k[13] != 0:
        try:    DIM, DIP           = stream.MINUS_DI(mh, ml, mc,     timeperiod=k[13]), stream.PLUS_DI( mh, ml, mc, timeperiod=k[13])
        except: DIM, DIP           = 0, 0
    if k[14] != 0:
        try:    MACD, MACDS, MACDH = stream.MACD(    mc,             fastperiod=k[14], slowperiod=k[15], signalperiod=k[16])
        except: MACD, MACDS, MACDH = 0, 0, 0
    if k[17] != 0:
        try:    MFI                = stream.MFI(     mh, ml, mc, mv, timeperiod=k[17])
        except: MFI                = 0
    if k[18] != 0:
        try:    MOM                = stream.MOM(     mc,             timeperiod=k[18])
        except: MOM                = 0
    try:    OBV                    = stream.OBV(     mc, mv)
    except: OBV                    = 0
    if k[19] != 0:
        try:    PPO                = stream.PPO(     mc,             fastperiod=k[19], slowperiod=k[20], matype=k[21])
        except: PPO                = 0
    if k[22] != 0:
        try:    ROC                = stream.ROC(     mc,             timeperiod=k[22])
        except: ROC                = 0
    if k[23] != 0:
        try:    RSI                = stream.RSI(     mc,             timeperiod=k[23])
        except: RSI                = 0
    if k[24] != 0:
        try:    SAR                = stream.SAR(     mh, ml,         acceleration=k[24], maximum=k[25])
        except: SAR                = 0
    if k[26] != 0:
        try:    STOCHSK, STOCHSD   = stream.STOCH(   mh, ml, mc,     fastk_period=k[26], slowk_period=k[27], slowk_matype=k[28], slowd_period=k[29], slowd_matype=k[30])
        except: STOCHSK, STOCHSD   = 0, 0
    if k[31] != 0:
        try:    STOCHFK, STOCHFD   = stream.STOCHF(  mh, ml, mc,     fastk_period=k[31], fastd_period=k[32], fastd_matype=k[33])
        except: STOCHFK, STOCHFD   = 0, 0
    if k[34] != 0:
        try:    WILLR              = stream.WILLR(   mh, ml, mc,     timeperiod=k[34])
        except: WILLR              = 0
    return AD, ADOSC, ADXR, APO, AROOND, AROONU, ATR, BBU, BBM, BBL, CCI, DIM, DIP, MACD, MACDS, MACDH, MFI, MOM, OBV, PPO, ROC, RSI, SAR, STOCHSK, STOCHSD, STOCHFK, STOCHFD, WILLR


# ============================================================================
# [2025-12-08] 백테스팅 분석 차트 (8개 차트)
# ============================================================================

def PltAnalysisCharts(df_tsg, save_file_name, teleQ):
    """
    확장된 상세기록 데이터를 기반으로 분석 차트를 생성하고 텔레그램으로 전송

    Args:
        df_tsg: 확장된 상세기록 DataFrame (50개 컬럼)
        save_file_name: 저장 파일명
        teleQ: 텔레그램 전송 큐

    차트 목록:
        1. 시간대별 수익금 분포
        2. 등락율 구간별 수익금 분포
        3. 체결강도 구간별 수익금 분포 + 승률
        4. 거래대금 구간별 수익금 분포
        5. 시가총액 구간별 수익금 분포
        6. 보유시간 구간별 수익금 분포
        7. 변수 간 상관관계 히트맵
        8. 등락율 vs 수익률 산점도 + 추세선
    """
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

    # 확장 컬럼 존재 여부 확인
    extended_columns = ['매수시', '매수등락율', '매수체결강도', '매수당일거래대금', '시가총액']
    has_extended = all(col in df_tsg.columns for col in extended_columns)

    if not has_extended or len(df_tsg) < 5:
        return  # 데이터가 부족하거나 확장 컬럼이 없으면 건너뜀

    try:
        # 차트용 복사본 (원본 df_tsg에 임시 컬럼 추가되는 부작용 방지)
        df_tsg = df_tsg.copy()
        from matplotlib.ticker import MaxNLocator, AutoMinorLocator

        # 한글 폰트 설정 (개선된 버전)
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_family = font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_family
            plt.rcParams['font.sans-serif'] = [font_family]
        except:
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # x축 라벨/히트맵 글자 겹침 방지를 위해 세로 여백을 늘립니다.
        fig = plt.figure(figsize=(16, 22))
        fig.suptitle(f'백테스팅 분석 차트 - {save_file_name}', fontsize=14, fontweight='bold')

        gs = gridspec.GridSpec(4, 2, figure=fig, hspace=0.45, wspace=0.25)

        # 색상 정의
        color_profit = '#2ECC71'  # 녹색 (이익)
        color_loss = '#E74C3C'    # 빨간색 (손실)
        color_bar = '#3498DB'     # 파란색

        # ============ Chart 1: 매수 시각별(분 단위) 수익 분포 ============
        ax1 = fig.add_subplot(gs[0, 0])
        if '매수시' in df_tsg.columns and '매수분' in df_tsg.columns:
            hour = df_tsg['매수시'].fillna(0).astype(int).astype(str).str.zfill(2)
            minute = df_tsg['매수분'].fillna(0).astype(int).astype(str).str.zfill(2)
            df_tsg['매수시각'] = hour + ':' + minute
            df_time = df_tsg.groupby('매수시각', observed=True).agg({
                '수익금': 'sum',
                '수익률': 'mean',
                '종목명': 'count'
            }).reset_index()
            df_time.columns = ['매수시각', '수익금', '평균수익률', '거래횟수']
            df_time = df_time.sort_values('매수시각')

            x_pos = range(len(df_time))
            colors = [color_profit if x >= 0 else color_loss for x in df_time['수익금']]
            bars = ax1.bar(x_pos, df_time['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
            ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax1.set_xlabel('매수 시각 (HH:MM)')
            ax1.set_ylabel('총 수익금')
            ax1.set_title('매수 시각별 수익금 분포(분 단위) + 거래횟수')

            ax1_twin = ax1.twinx()
            ax1_twin.plot(x_pos, df_time['거래횟수'], 'o-', color='orange', linewidth=1.5, markersize=4)
            ax1_twin.set_ylabel('거래횟수', color='orange')
            ax1_twin.tick_params(axis='y', labelcolor='orange')

            tick_step = max(1, int(len(df_time) / 12))
            ax1.set_xticks(list(range(0, len(df_time), tick_step)))
            ax1.set_xticklabels(df_time['매수시각'].iloc[::tick_step], rotation=45, ha='right', fontsize=8)

            if len(df_time) <= 25:
                for bar, val in zip(bars, df_time['수익금']):
                    if abs(val) > 0:
                        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                                 f'{val/10000:.0f}만', ha='center',
                                 va='bottom' if val >= 0 else 'top', fontsize=7)
        else:
            df_hour = df_tsg.groupby('매수시').agg({'수익금': 'sum', '수익률': 'mean'}).reset_index()
            colors = [color_profit if x >= 0 else color_loss for x in df_hour['수익금']]
            bars = ax1.bar(df_hour['매수시'], df_hour['수익금'], color=colors, alpha=0.8, edgecolor='black',
                           linewidth=0.5)
            ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax1.set_xlabel('매수 시간대 (시)')
            ax1.set_ylabel('총 수익금')
            ax1.set_title('시간대별 수익금 분포')
            ax1.set_xticks(range(9, 16))
            for bar, val in zip(bars, df_hour['수익금']):
                if abs(val) > 0:
                    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                             f'{val/10000:.0f}만', ha='center',
                             va='bottom' if val >= 0 else 'top', fontsize=8)

        # ============ Chart 2: 등락율별 수익 분포 ============
        ax2 = fig.add_subplot(gs[0, 1])
        bins = [0, 5, 10, 15, 20, 30, 100]
        labels = ['0-5%', '5-10%', '10-15%', '15-20%', '20-30%', '30%+']
        df_tsg['등락율구간'] = pd.cut(df_tsg['매수등락율'], bins=bins, labels=labels, right=False)
        df_rate = df_tsg.groupby('등락율구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_rate.columns = ['등락율구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_rate))
        colors = [color_profit if x >= 0 else color_loss for x in df_rate['수익금']]
        ax2.bar(x, df_rate['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.set_xlabel('매수 등락율 구간')
        ax2.set_ylabel('총 수익금')
        ax2.set_title('등락율 구간별 수익금 분포')
        ax2.set_xticks(x)
        ax2.set_xticklabels(df_rate['등락율구간'], rotation=45, ha='right')

        # 거래횟수 표시
        ax2_twin = ax2.twinx()
        ax2_twin.plot(x, df_rate['거래횟수'], 'o-', color='orange', linewidth=2, markersize=6, label='거래횟수')
        ax2_twin.set_ylabel('거래횟수', color='orange')
        ax2_twin.tick_params(axis='y', labelcolor='orange')

        # ============ Chart 3: 체결강도별 수익 분포 ============
        ax3 = fig.add_subplot(gs[1, 0])
        bins_ch = [0, 80, 100, 120, 150, 200, 500]
        labels_ch = ['~80', '80-100', '100-120', '120-150', '150-200', '200+']
        df_tsg['체결강도구간'] = pd.cut(df_tsg['매수체결강도'], bins=bins_ch, labels=labels_ch, right=False)
        df_ch = df_tsg.groupby('체결강도구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_ch.columns = ['체결강도구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_ch))
        colors = [color_profit if x >= 0 else color_loss for x in df_ch['수익금']]
        ax3.bar(x, df_ch['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax3.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax3.set_xlabel('매수 체결강도 구간')
        ax3.set_ylabel('총 수익금')
        ax3.set_title('체결강도 구간별 수익금 분포')
        ax3.set_xticks(x)
        ax3.set_xticklabels(df_ch['체결강도구간'], rotation=45, ha='right')

        # 승률 계산 및 표시
        ax3_twin = ax3.twinx()
        win_rates = []
        for grp in df_ch['체결강도구간']:
            grp_data = df_tsg[df_tsg['체결강도구간'] == grp]
            if len(grp_data) > 0:
                wr = (grp_data['수익금'] > 0).sum() / len(grp_data) * 100
                win_rates.append(wr)
            else:
                win_rates.append(0)
        ax3_twin.plot(x, win_rates, 's--', color='purple', linewidth=2, markersize=6, label='승률')
        ax3_twin.set_ylabel('승률 (%)', color='purple')
        ax3_twin.tick_params(axis='y', labelcolor='purple')
        ax3_twin.set_ylim(0, 100)

        # ============ Chart 4: 거래대금별 수익 분포 ============
        ax4 = fig.add_subplot(gs[1, 1])
        money_series = df_tsg['매수당일거래대금'].dropna()
        # STOM 백테스팅 상세 테이블의 당일거래대금 단위는 "백만"입니다.
        # (예: 10,000 = 100억, 1,000,000 = 1조)
        money_unit = '백만'

        if money_unit == '백만':
            # 기본 분할(억/조 단위로 읽기 쉽게 라벨링, 실제 데이터 단위는 백만)
            max_val = float(money_series.max()) if len(money_series) > 0 else 0.0
            # (백만) 단위: 500=5억, 5,000=50억, 1,000,000=1조
            base_edges = [0, 500, 1000, 2000, 3000, 5000, 7000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]

            edges = [e for e in base_edges if e < max_val]
            # 상단 구간 보정(최대값을 포함하도록 마지막 경계 추가)
            next_edge = next((e for e in base_edges if e >= max_val), None)
            if next_edge is not None:
                edges.append(next_edge)
            else:
                # 1조 이상인 경우: 1조(=1,000,000백만) 단위로 확장
                max_jo = int(math.ceil(max_val / 1000000)) if max_val > 0 else 1
                step_jo = 1  # 1조 단위 고정(요구사항: 1조 이상은 1조 단위)
                step = step_jo * 1000000
                edges = [e for e in edges if e < 1000000]
                for e in range(1000000, (max_jo + step_jo) * 1000000, step):
                    edges.append(e)

            edges = sorted(set(edges))
            if not edges or edges[0] != 0:
                edges = [0] + edges
            edges.append(float('inf'))

            def _fmt_money_million(x):
                if x >= 1000000:
                    return f"{int(round(x / 1000000))}조"
                return f"{int(round(x / 100))}억"

            labels = []
            for i in range(len(edges) - 1):
                lo, hi = edges[i], edges[i + 1]
                if hi == float('inf'):
                    labels.append(f"{_fmt_money_million(lo)}+")
                elif lo == 0:
                    labels.append(f"~{_fmt_money_million(hi)}")
                else:
                    labels.append(f"{_fmt_money_million(lo)}-{_fmt_money_million(hi)}")

            df_tsg['거래대금구간'] = pd.cut(df_tsg['매수당일거래대금'], bins=edges, labels=labels, right=False)
        df_money = df_tsg.groupby('거래대금구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_money.columns = ['거래대금구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_money))
        colors = [color_profit if x >= 0 else color_loss for x in df_money['수익금']]
        ax4.bar(x, df_money['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax4.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax4.set_xlabel('매수 당일거래대금 구간(라벨: 억/조)')
        ax4.set_ylabel('총 수익금')
        if money_unit == '백만':
            ax4.set_title('거래대금 구간별 수익금 분포 (원본 단위: 백만, 라벨: 억/조)')
        else:
            ax4.set_title('거래대금 구간별 수익금 분포 (단위: 억/조)')
        tick_step = max(1, int(math.ceil(len(df_money) / 8)))
        ax4.set_xticks(list(range(0, len(df_money), tick_step)))
        ax4.set_xticklabels([str(v) for v in df_money['거래대금구간'].iloc[::tick_step]],
                            rotation=30, ha='right', fontsize=8)

        # ============ Chart 5: 시가총액별 수익 분포 ============
        ax5 = fig.add_subplot(gs[2, 0])
        cap_series = df_tsg['시가총액'].dropna()
        cap_max = float(cap_series.max()) if len(cap_series) > 0 else 0.0

        # 1조(=10,000억) 미만: 100억 단위로 구간 생성 (요구사항)
        # 1조 이상: 1조 단위로 구간 확장 (요구사항)
        cap_edges = []
        if cap_max <= 0:
            cap_edges = [0, float('inf')]
        elif cap_max < 10000:
            cap_max_rounded = int(math.ceil(cap_max / 100.0) * 100)
            cap_edges = list(range(0, cap_max_rounded + 100, 100))
            cap_edges.append(float('inf'))
        else:
            base_cap_edges = list(range(0, 10000 + 100, 100))  # 0~1조 미만 100억 단위
            cap_edges = [e for e in base_cap_edges if e < 10000]
            max_jo = int(math.ceil(cap_max / 10000)) if cap_max > 0 else 1
            for e in range(10000, (max_jo + 1) * 10000, 10000):
                cap_edges.append(e)
            cap_edges.append(float('inf'))

        cap_edges = sorted(set(cap_edges))

        def _fmt_cap_eok(x):
            # x: 억 단위
            # - 1조 미만: 억 단위로 명확히 표기(라벨 길이/가독성 고려)
            # - 1조 이상: 조 단위로 표기
            if x >= 10000:
                return f"{int(round(x / 10000))}조"
            return f"{int(round(x))}억"

        cap_labels = []
        for i in range(len(cap_edges) - 1):
            lo, hi = cap_edges[i], cap_edges[i + 1]
            if hi == float('inf'):
                cap_labels.append(f"{_fmt_cap_eok(lo)}+")
            elif lo == 0:
                cap_labels.append(f"~{_fmt_cap_eok(hi)}")
            else:
                cap_labels.append(f"{_fmt_cap_eok(lo)}-{_fmt_cap_eok(hi)}")

        df_tsg['시총구간'] = pd.cut(df_tsg['시가총액'], bins=cap_edges, labels=cap_labels, right=False)
        df_cap = df_tsg.groupby('시총구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_cap.columns = ['시총구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_cap))
        colors = [color_profit if x >= 0 else color_loss for x in df_cap['수익금']]
        ax5.bar(x, df_cap['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax5.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax5.set_xlabel('시가총액 구간 (단위: 억, 1조+는 조)')
        ax5.set_ylabel('총 수익금')
        ax5.set_title('시가총액 구간별 수익금 분포')
        tick_step = max(1, int(math.ceil(len(df_cap) / 8)))
        ax5.set_xticks(list(range(0, len(df_cap), tick_step)))
        ax5.set_xticklabels([str(v) for v in df_cap['시총구간'].iloc[::tick_step]],
                            rotation=30, ha='right', fontsize=8)

        # ============ Chart 6: 보유시간별 수익 분포 ============
        ax6 = fig.add_subplot(gs[2, 1])
        df_tsg['보유시간구간'] = pd.cut(df_tsg['보유시간'],
                                      bins=[0, 60, 180, 300, 600, 1800, float('inf')],
                                      labels=['~1분', '1-3분', '3-5분', '5-10분', '10-30분', '30분+'])
        df_hold = df_tsg.groupby('보유시간구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_hold.columns = ['보유시간구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_hold))
        colors = [color_profit if x >= 0 else color_loss for x in df_hold['수익금']]
        ax6.bar(x, df_hold['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax6.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax6.set_xlabel('보유시간 구간')
        ax6.set_ylabel('총 수익금')
        ax6.set_title('보유시간 구간별 수익금 분포')
        ax6.set_xticks(x)
        ax6.set_xticklabels(df_hold['보유시간구간'], rotation=45, ha='right')

        # ============ Chart 7: 상관관계 히트맵 ============
        ax7 = fig.add_subplot(gs[3, 0])
        corr_columns = ['수익률', '매수등락율', '매수체결강도', '매수회전율', '매수전일비', '보유시간']
        available_cols = [col for col in corr_columns if col in df_tsg.columns]

        if len(available_cols) >= 3:
            col_display = {
                '수익률': '수익률',
                '매수등락율': '매수등락',
                '매수체결강도': '매수체결',
                '매수회전율': '매수회전',
                '매수전일비': '매수전일',
                '보유시간': '보유시간',
            }
            display_labels = [col_display.get(c, c) for c in available_cols]
            df_corr = df_tsg[available_cols].corr()
            im = ax7.imshow(df_corr.values, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
            ax7.set_xticks(range(len(available_cols)))
            ax7.set_yticks(range(len(available_cols)))
            ax7.set_xticklabels(display_labels, rotation=30, ha='right', fontsize=8)
            ax7.set_yticklabels(display_labels, fontsize=8)
            ax7.set_title('변수 간 상관관계')
            ax7.xaxis.set_minor_locator(AutoMinorLocator(2))
            ax7.yaxis.set_minor_locator(AutoMinorLocator(2))

            for i in range(len(available_cols)):
                for j in range(len(available_cols)):
                    text = ax7.text(j, i, f'{df_corr.values[i, j]:.2f}',
                                   ha='center', va='center', color='black', fontsize=8)

            plt.colorbar(im, ax=ax7, shrink=0.8)

        # ============ Chart 8: 산점도 (등락율 vs 수익률) ============
        ax8 = fig.add_subplot(gs[3, 1])
        df_scatter = df_tsg
        if len(df_tsg) > 20000:
            # 산점도는 대용량에서 렌더링 시간이 급증하므로 샘플링(표시용) 처리
            df_scatter = df_tsg.sample(n=20000, random_state=42)
        colors = np.where(df_scatter['수익률'].to_numpy(dtype=np.float64) >= 0, color_profit, color_loss)
        ax8.scatter(df_scatter['매수등락율'], df_scatter['수익률'], c=colors, alpha=0.5, s=20, edgecolors='none')
        ax8.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax8.axvline(x=df_tsg['매수등락율'].mean(), color='blue', linestyle=':', linewidth=0.8, alpha=0.5)
        ax8.set_xlabel('매수 등락율 (%)')
        ax8.set_ylabel('수익률 (%)')
        ax8.set_title('등락율 vs 수익률 산점도')

        # 추세선 추가
        if len(df_scatter) > 10:
            z = np.polyfit(df_scatter['매수등락율'], df_scatter['수익률'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(df_scatter['매수등락율'].min(), df_scatter['매수등락율'].max(), 100)
            ax8.plot(x_line, p(x_line), 'b--', linewidth=1, alpha=0.7, label=f'추세선')
            ax8.legend(fontsize=8)

        # 저장 및 전송
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.tight_layout(rect=[0, 0.03, 1, 0.97])

        analysis_path = f"{GRAPH_PATH}/{save_file_name}_analysis.png"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.savefig(analysis_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        # 텔레그램 전송
        if teleQ is not None:
            teleQ.put(analysis_path)

    except Exception as e:
        print_exc()
        try:
            plt.close('all')
        except:
            pass


# ============================================================================
# [2025-12-09] 백테스팅 데이터 분석 및 필터링을 위한 함수들
# ============================================================================

def CalculateDerivedMetrics(df_tsg):
    """
    매수/매도 시점 간 파생 지표를 계산합니다.

    Returns:
        DataFrame with added derived metrics
    """
    df = df_tsg.copy()

    # === 1) 매수 시점 위험도 점수 (0-100, LOOKAHEAD-FREE) ===
    # - 필터 분석은 "매수를 안 하는 조건(진입 회피)"을 찾는 것이므로,
    #   매도 시점 정보(매도등락율/변화량/보유시간 등)를 사용하면 룩어헤드가 됩니다.
    # - 위험도점수는 매수 시점에서 알 수 있는 정보만으로 계산합니다.
    df['위험도점수'] = 0

    if '매수등락율' in df.columns:
        buy_ret = pd.to_numeric(df['매수등락율'], errors='coerce')
        df.loc[buy_ret >= 20, '위험도점수'] += 20
        df.loc[buy_ret >= 25, '위험도점수'] += 10
        df.loc[buy_ret >= 30, '위험도점수'] += 10

    if '매수체결강도' in df.columns:
        buy_power = pd.to_numeric(df['매수체결강도'], errors='coerce')
        df.loc[buy_power < 80, '위험도점수'] += 15
        df.loc[buy_power < 60, '위험도점수'] += 10
        # 과열(초고 체결강도)도 사후 분석에서 손실로 이어지는 경우가 있어 별도 가중(룩어헤드 없음)
        df.loc[buy_power >= 150, '위험도점수'] += 10
        df.loc[buy_power >= 200, '위험도점수'] += 10
        df.loc[buy_power >= 250, '위험도점수'] += 10

    if '매수당일거래대금' in df.columns:
        trade_money_raw = pd.to_numeric(df['매수당일거래대금'], errors='coerce')
        # STOM: 당일거래대금 단위 = 백만 → 억 환산(÷100)
        trade_money_eok = trade_money_raw / 100.0
        df.loc[trade_money_eok < 50, '위험도점수'] += 15
        df.loc[trade_money_eok < 100, '위험도점수'] += 10

    if '시가총액' in df.columns:
        mcap = pd.to_numeric(df['시가총액'], errors='coerce')
        df.loc[mcap < 1000, '위험도점수'] += 15
        df.loc[mcap < 5000, '위험도점수'] += 10

    if '매수호가잔량비' in df.columns:
        hoga = pd.to_numeric(df['매수호가잔량비'], errors='coerce')
        df.loc[hoga < 90, '위험도점수'] += 10
        df.loc[hoga < 70, '위험도점수'] += 15

    if '매수스프레드' in df.columns:
        spread = pd.to_numeric(df['매수스프레드'], errors='coerce')
        df.loc[spread >= 0.5, '위험도점수'] += 10
        df.loc[spread >= 1.0, '위험도점수'] += 10

    # 유동성(회전율) 기반 위험도(룩어헤드 없음)
    if '매수회전율' in df.columns:
        turn = pd.to_numeric(df['매수회전율'], errors='coerce')
        df.loc[turn < 10, '위험도점수'] += 5
        df.loc[turn < 5, '위험도점수'] += 10

    # 매수 변동폭(고가-저가) 기반 변동성(%)이 있으면 반영
    if '매수변동폭비율' in df.columns:
        vol_pct = pd.to_numeric(df['매수변동폭비율'], errors='coerce')
        # 과도한 변동성은 손실 확률이 높아지는 경향이 있어 가중(룩어헤드 없음)
        df.loc[vol_pct >= 7.5, '위험도점수'] += 10
        df.loc[vol_pct >= 10, '위험도점수'] += 10
        df.loc[vol_pct >= 15, '위험도점수'] += 10

    df['위험도점수'] = df['위험도점수'].clip(0, 100)

    # === 2) 매도 시점 데이터 기반 파생지표(진단용) ===
    sell_columns = ['매도등락율', '매도체결강도', '매도당일거래대금', '매도전일비', '매도회전율', '매도호가잔량비']
    has_sell_data = all(col in df.columns for col in sell_columns)

    if has_sell_data:
        # === 변화량 지표 (매도 - 매수) ===
        df['등락율변화'] = df['매도등락율'] - df['매수등락율']
        df['체결강도변화'] = df['매도체결강도'] - df['매수체결강도']
        df['전일비변화'] = df['매도전일비'] - df['매수전일비']
        df['회전율변화'] = df['매도회전율'] - df['매수회전율']
        df['호가잔량비변화'] = df['매도호가잔량비'] - df['매수호가잔량비']

        # === 변화율 지표 (매도 / 매수) ===
        df['거래대금변화율'] = np.where(
            df['매수당일거래대금'] > 0,
            df['매도당일거래대금'] / df['매수당일거래대금'],
            1.0
        )
        df['체결강도변화율'] = np.where(
            df['매수체결강도'] > 0,
            df['매도체결강도'] / df['매수체결강도'],
            1.0
        )

        # === 추세 판단 지표 ===
        df['등락추세'] = df['등락율변화'].apply(lambda x: '상승' if x > 0 else ('하락' if x < 0 else '유지'))
        df['체결강도추세'] = df['체결강도변화'].apply(lambda x: '강화' if x > 10 else ('약화' if x < -10 else '유지'))
        df['거래량추세'] = df['거래대금변화율'].apply(lambda x: '증가' if x > 1.2 else ('감소' if x < 0.8 else '유지'))

        # === 위험 신호 지표 (매도-매수 기반, 진단용) ===
        df['급락신호'] = (df['등락율변화'] < -3) & (df['체결강도변화'] < -20)
        df['매도세증가'] = df['호가잔량비변화'] < -0.2
        df['거래량급감'] = df['거래대금변화율'] < 0.5

        # === 매수/매도 위험도 점수 (0-100, 사후 진단용) ===
        # - 매도 시점 정보(매도-매수 변화량 등)를 포함하는 위험도 점수입니다.
        # - "매수 진입 필터"로 쓰면 룩어헤드가 되므로, 비교/진단 차트용으로만 사용합니다.
        df['매수매도위험도점수'] = 0
        df.loc[df['등락율변화'] < -2, '매수매도위험도점수'] += 20
        df.loc[df['체결강도변화'] < -15, '매수매도위험도점수'] += 20
        df.loc[df['호가잔량비변화'] < -0.3, '매수매도위험도점수'] += 20
        df.loc[df['거래대금변화율'] < 0.6, '매수매도위험도점수'] += 20
        if '매수등락율' in df.columns:
            buy_ret = pd.to_numeric(df['매수등락율'], errors='coerce')
            df.loc[buy_ret > 20, '매수매도위험도점수'] += 20
        df['매수매도위험도점수'] = df['매수매도위험도점수'].clip(0, 100)

    return df


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

        # === 1. 상세 거래 기록 CSV ===
        if write_detail:
            detail_path = f"{GRAPH_PATH}/{save_file_name}_detail.csv"
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
            summary_path = f"{GRAPH_PATH}/{save_file_name}_summary.csv"
            df_summary = pd.DataFrame(summary_data)
            if len(df_summary) > 0:
                df_summary = df_summary.sort_values(['분류', '총수익금'], ascending=[True, False])
                df_summary.to_csv(summary_path, encoding='utf-8-sig', index=False)

        # === 3. 필터 효과 분석 CSV ===
        if write_filter:
            filter_data = AnalyzeFilterEffects(df_analysis)
            filter_path = f"{GRAPH_PATH}/{save_file_name}_filter.csv"
            if len(filter_data) > 0:
                df_filter = pd.DataFrame(filter_data)
                df_filter = df_filter.sort_values('수익개선금액', ascending=False)
                df_filter.to_csv(filter_path, encoding='utf-8-sig', index=False)

        return detail_path, summary_path, filter_path

    except Exception as e:
        print_exc()
        return None, None, None


def AnalyzeFilterEffects(df_tsg):
    """
    조건별 필터 적용 시 예상 효과를 분석합니다.

    Args:
        df_tsg: 파생 지표가 포함된 DataFrame

    Returns:
        list: 필터 효과 분석 결과
    """
    filter_results = []
    total_profit = df_tsg['수익금'].sum()
    total_trades = len(df_tsg)

    if total_trades == 0:
        return filter_results

    # === 필터 조건 정의 ===
    filter_conditions = []

    # 1. 시간대 필터
    if '매수시' in df_tsg.columns:
        for hour in df_tsg['매수시'].unique():
            filter_conditions.append({
                '필터명': f'시간대 {hour}시 제외',
                '조건': df_tsg['매수시'] == hour,
                '분류': '시간대'
            })

    # 2. 등락율 구간 필터
    if '매수등락율' in df_tsg.columns:
        filter_conditions.extend([
            {'필터명': '매수등락율 25% 이상 제외', '조건': df_tsg['매수등락율'] >= 25, '분류': '등락율'},
            {'필터명': '매수등락율 20% 이상 제외', '조건': df_tsg['매수등락율'] >= 20, '분류': '등락율'},
            {'필터명': '매수등락율 5% 미만 제외', '조건': df_tsg['매수등락율'] < 5, '분류': '등락율'},
        ])

    # 3. 체결강도 필터
    if '매수체결강도' in df_tsg.columns:
        filter_conditions.extend([
            {'필터명': '매수체결강도 80 미만 제외', '조건': df_tsg['매수체결강도'] < 80, '분류': '체결강도'},
            {'필터명': '매수체결강도 200 이상 제외', '조건': df_tsg['매수체결강도'] >= 200, '분류': '체결강도'},
        ])

    # 4. (룩어헤드 제거) 매도-매수 변화량/급락신호 기반 필터는 제외
    # - 등락율변화/체결강도변화/거래대금변화율/급락신호 등은 매도 시점 정보가 포함된
    #   "사후 확정 지표"이므로, 매수 진입 필터 추천에는 사용하지 않습니다.

    if '위험도점수' in df_tsg.columns:
        filter_conditions.extend([
            {'필터명': '매수 위험도점수 60점 이상 제외', '조건': df_tsg['위험도점수'] >= 60, '분류': '위험신호'},
            {'필터명': '매수 위험도점수 40점 이상 제외', '조건': df_tsg['위험도점수'] >= 40, '분류': '위험신호'},
        ])

    # 5. 보유시간 필터
    # - 보유시간은 매도 조건(SL/TP 등)의 결과로 결정되는 값이어서,
    #   "매수 시점 필터"로 쓰기 어렵기 때문에 필터 분석에서는 제외합니다.

    # 6. 시가총액 필터
    if '시가총액' in df_tsg.columns:
        filter_conditions.extend([
            {'필터명': '매수시가총액 1000억 미만 제외', '조건': df_tsg['시가총액'] < 1000, '분류': '시가총액'},
            {'필터명': '매수시가총액 3000억 미만 제외', '조건': df_tsg['시가총액'] < 3000, '분류': '시가총액'},
            {'필터명': '매수시가총액 1조 이상 제외', '조건': df_tsg['시가총액'] >= 10000, '분류': '시가총액'},
        ])

    # === 각 필터 효과 계산 ===
    for fc in filter_conditions:
        try:
            filtered_out = df_tsg[fc['조건']]
            remaining = df_tsg[~fc['조건']]

            if len(filtered_out) == 0:
                continue

            filtered_profit = filtered_out['수익금'].sum()
            remaining_profit = remaining['수익금'].sum()
            filtered_count = len(filtered_out)
            remaining_count = len(remaining)

            # 필터 적용 시 수익 개선 효과 (제외된 거래가 손실이면 양수)
            improvement = -filtered_profit

            filter_results.append({
                '분류': fc['분류'],
                '필터명': fc['필터명'],
                '제외거래수': filtered_count,
                '제외비율': round(filtered_count / total_trades * 100, 1),
                '제외거래수익금': int(filtered_profit),
                '잔여거래수': remaining_count,
                '잔여거래수익금': int(remaining_profit),
                '수익개선금액': int(improvement),
                '제외거래승률': round((filtered_out['수익금'] > 0).mean() * 100, 1) if len(filtered_out) > 0 else 0,
                '잔여거래승률': round((remaining['수익금'] > 0).mean() * 100, 1) if len(remaining) > 0 else 0,
                '적용권장': '★★★' if improvement > total_profit * 0.1 else ('★★' if improvement > 0 else ''),
            })
        except:
            continue

    return filter_results


# ============================================================================
# [2025-12-09] 매수/매도 시점 비교 분석 차트 (11개 차트)
# ============================================================================

def PltBuySellComparison_Legacy(df_tsg, save_file_name, teleQ=None):
    """
    매수/매도 시점 비교 분석 차트를 생성합니다.

    Args:
        df_tsg: 백테스팅 결과 DataFrame (파생 지표 포함)
        save_file_name: 저장 파일명
        teleQ: 텔레그램 전송 큐

    차트 목록:
        1. 등락율 변화 vs 수익률 (사분면 분석)
        2. 체결강도 변화 vs 수익률
        3. 매수 vs 매도 등락율 비교 (대각선)
        4. 위험도 점수별 수익금 분포
        5. 등락추세별 수익금
        6. 체결강도추세별 수익금
        7. 필터 효과 파레토 차트
        8. 손실/이익 거래 특성 비교
        9. 추세 조합별 히트맵
        10. 시간대별 추세 변화
        11. 거래대금 변화율별 수익금
    """
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

    # 매도 시점 데이터 확인
    required_cols = ['매도등락율', '매도체결강도', '등락율변화', '체결강도변화']
    if not all(col in df_tsg.columns for col in required_cols):
        return

    if len(df_tsg) < 5:
        return

    try:
        # 한글 폰트 설정 (개선된 버전)
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_family = font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_family
            plt.rcParams['font.sans-serif'] = [font_family]
        except:
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        fig = plt.figure(figsize=(20, 16))
        fig.suptitle(f'매수/매도 시점 비교 분석 - {save_file_name}', fontsize=14, fontweight='bold')

        gs = gridspec.GridSpec(4, 3, figure=fig, hspace=0.35, wspace=0.3)

        color_profit = '#2ECC71'
        color_loss = '#E74C3C'
        color_neutral = '#3498DB'

        # === Chart 1: 등락율 변화 vs 수익률 ===
        ax1 = fig.add_subplot(gs[0, 0])
        colors = [color_profit if x >= 0 else color_loss for x in df_tsg['수익률']]
        ax1.scatter(df_tsg['등락율변화'], df_tsg['수익률'], c=colors, alpha=0.5, s=25)
        ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax1.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
        ax1.set_xlabel('등락율 변화 (매도-매수) %')
        ax1.set_ylabel('수익률 (%)')
        ax1.set_title('등락율 변화 vs 수익률')

        # 사분면 라벨
        ax1.text(0.95, 0.95, '상승+이익', transform=ax1.transAxes, ha='right', va='top', fontsize=8, color='green')
        ax1.text(0.05, 0.95, '하락+이익', transform=ax1.transAxes, ha='left', va='top', fontsize=8, color='blue')
        ax1.text(0.95, 0.05, '상승+손실', transform=ax1.transAxes, ha='right', va='bottom', fontsize=8, color='orange')
        ax1.text(0.05, 0.05, '하락+손실', transform=ax1.transAxes, ha='left', va='bottom', fontsize=8, color='red')

        # === Chart 2: 체결강도 변화 vs 수익률 ===
        ax2 = fig.add_subplot(gs[0, 1])
        colors = [color_profit if x >= 0 else color_loss for x in df_tsg['수익률']]
        ax2.scatter(df_tsg['체결강도변화'], df_tsg['수익률'], c=colors, alpha=0.5, s=25)
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.set_xlabel('체결강도 변화 (매도-매수)')
        ax2.set_ylabel('수익률 (%)')
        ax2.set_title('체결강도 변화 vs 수익률')

        # === Chart 3: 매수 vs 매도 등락율 비교 ===
        ax3 = fig.add_subplot(gs[0, 2])
        colors = [color_profit if x >= 0 else color_loss for x in df_tsg['수익률']]
        ax3.scatter(df_tsg['매수등락율'], df_tsg['매도등락율'], c=colors, alpha=0.5, s=25)
        max_val = max(df_tsg['매수등락율'].max(), df_tsg['매도등락율'].max())
        min_val = min(df_tsg['매수등락율'].min(), df_tsg['매도등락율'].min())
        ax3.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=1, alpha=0.5, label='변화없음')
        ax3.set_xlabel('매수 등락율 (%)')
        ax3.set_ylabel('매도 등락율 (%)')
        ax3.set_title('매수 vs 매도 등락율')
        ax3.legend(fontsize=8)

        # === Chart 4: 위험도 점수 분포 ===
        ax4 = fig.add_subplot(gs[1, 0])
        if '위험도점수' in df_tsg.columns:
            risk_bins = [0, 20, 40, 60, 80, 100]
            risk_labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
            df_tsg['위험도구간'] = pd.cut(df_tsg['위험도점수'], bins=risk_bins, labels=risk_labels, right=False)

            risk_profit = df_tsg.groupby('위험도구간', observed=True)['수익금'].sum()
            colors = [color_profit if x >= 0 else color_loss for x in risk_profit]
            risk_profit.plot(kind='bar', ax=ax4, color=colors, edgecolor='black', linewidth=0.5)
            ax4.set_xlabel('위험도 점수 구간')
            ax4.set_ylabel('총 수익금')
            ax4.set_title('위험도 점수별 수익금 분포')
            ax4.tick_params(axis='x', rotation=45)
            ax4.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

        # === Chart 5: 등락추세별 수익 분포 ===
        ax5 = fig.add_subplot(gs[1, 1])
        if '등락추세' in df_tsg.columns:
            trend_profit = df_tsg.groupby('등락추세')['수익금'].sum()
            trend_count = df_tsg.groupby('등락추세').size()
            colors = [color_profit if trend_profit.get(x, 0) >= 0 else color_loss for x in trend_profit.index]
            bars = ax5.bar(trend_profit.index, trend_profit.values, color=colors, edgecolor='black', linewidth=0.5)
            ax5.set_xlabel('등락 추세')
            ax5.set_ylabel('총 수익금')
            ax5.set_title('등락추세별 수익금')
            ax5.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

            for bar, cnt in zip(bars, trend_count):
                ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=9)

        # === Chart 6: 체결강도추세별 수익 분포 ===
        ax6 = fig.add_subplot(gs[1, 2])
        if '체결강도추세' in df_tsg.columns:
            ch_trend_profit = df_tsg.groupby('체결강도추세')['수익금'].sum()
            ch_trend_count = df_tsg.groupby('체결강도추세').size()
            colors = [color_profit if ch_trend_profit.get(x, 0) >= 0 else color_loss for x in ch_trend_profit.index]
            bars = ax6.bar(ch_trend_profit.index, ch_trend_profit.values, color=colors, edgecolor='black', linewidth=0.5)
            ax6.set_xlabel('체결강도 추세')
            ax6.set_ylabel('총 수익금')
            ax6.set_title('체결강도추세별 수익금')
            ax6.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

            for bar, cnt in zip(bars, ch_trend_count):
                ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=9)

        # === Chart 7: 필터 효과 파레토 차트 ===
        ax7 = fig.add_subplot(gs[2, :2])
        filter_results = AnalyzeFilterEffects(df_tsg)
        if filter_results:
            df_filter = pd.DataFrame(filter_results)
            df_filter = df_filter[df_filter['수익개선금액'] > 0].nlargest(15, '수익개선금액')

            if len(df_filter) > 0:
                x_pos = range(len(df_filter))
                bars = ax7.bar(x_pos, df_filter['수익개선금액'], color=color_profit, edgecolor='black', linewidth=0.5)
                ax7.set_xticks(x_pos)
                ax7.set_xticklabels(df_filter['필터명'], rotation=45, ha='right', fontsize=8)
                ax7.set_ylabel('수익 개선 금액')
                ax7.set_title('필터 적용 시 예상 수익 개선 효과 (Top 15)')

                cumsum = df_filter['수익개선금액'].cumsum()
                cumsum_pct = cumsum / cumsum.iloc[-1] * 100
                ax7_twin = ax7.twinx()
                ax7_twin.plot(x_pos, cumsum_pct, 'ro-', markersize=4, linewidth=1.5)
                ax7_twin.set_ylabel('누적 비율 (%)', color='red')
                ax7_twin.tick_params(axis='y', labelcolor='red')
                ax7_twin.set_ylim(0, 110)

        # === Chart 8: 손실 거래 특성 분석 ===
        ax8 = fig.add_subplot(gs[2, 2])
        loss_trades = df_tsg[df_tsg['수익금'] < 0]
        profit_trades = df_tsg[df_tsg['수익금'] >= 0]

        if len(loss_trades) > 0 and len(profit_trades) > 0:
            compare_cols = ['매수등락율', '매수체결강도', '보유시간']
            available_cols = [c for c in compare_cols if c in df_tsg.columns]

            if available_cols:
                loss_means = [loss_trades[c].mean() for c in available_cols]
                profit_means = [profit_trades[c].mean() for c in available_cols]

                x = np.arange(len(available_cols))
                width = 0.35
                ax8.bar(x - width/2, loss_means, width, label='손실거래', color=color_loss, alpha=0.8)
                ax8.bar(x + width/2, profit_means, width, label='이익거래', color=color_profit, alpha=0.8)
                ax8.set_xticks(x)
                ax8.set_xticklabels(available_cols, rotation=45, ha='right')
                ax8.set_ylabel('평균값')
                ax8.set_title('손실/이익 거래 특성 비교')
                ax8.legend(fontsize=9)

        # === Chart 9: 조건 조합 히트맵 ===
        ax9 = fig.add_subplot(gs[3, 0])
        if '등락추세' in df_tsg.columns and '체결강도추세' in df_tsg.columns:
            pivot = df_tsg.pivot_table(values='수익금', index='등락추세', columns='체결강도추세', aggfunc='sum', fill_value=0)
            im = ax9.imshow(pivot.values, cmap='RdYlGn', aspect='auto')
            ax9.set_xticks(range(len(pivot.columns)))
            ax9.set_yticks(range(len(pivot.index)))
            ax9.set_xticklabels(pivot.columns, fontsize=9)
            ax9.set_yticklabels(pivot.index, fontsize=9)
            ax9.set_xlabel('체결강도 추세')
            ax9.set_ylabel('등락 추세')
            ax9.set_title('추세 조합별 수익금')

            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    val = pivot.values[i, j]
                    text_color = 'white' if abs(val) > pivot.values.max() * 0.5 else 'black'
                    ax9.text(j, i, f'{val/10000:.0f}만', ha='center', va='center', fontsize=8, color=text_color)

            plt.colorbar(im, ax=ax9, shrink=0.8)

        # === Chart 10: 시간대별 매수/매도 추세 변화 ===
        ax10 = fig.add_subplot(gs[3, 1])
        if '매수시' in df_tsg.columns and '등락율변화' in df_tsg.columns:
            hourly_change = df_tsg.groupby('매수시').agg({
                '등락율변화': 'mean',
                '체결강도변화': 'mean',
                '수익금': 'sum'
            })
            x = hourly_change.index
            ax10.bar(x, hourly_change['수익금'], alpha=0.3, color=color_neutral, label='수익금')
            ax10_twin = ax10.twinx()
            ax10_twin.plot(x, hourly_change['등락율변화'], 'g-o', markersize=4, label='등락율변화', linewidth=1.5)
            ax10_twin.plot(x, hourly_change['체결강도변화'] / 10, 'r-s', markersize=4, label='체결강도변화/10', linewidth=1.5)
            ax10.set_xlabel('매수 시간대')
            ax10.set_ylabel('총 수익금')
            ax10_twin.set_ylabel('변화량')
            ax10.set_title('시간대별 추세 변화')
            ax10_twin.legend(loc='upper right', fontsize=8)
            ax10.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)

        # === Chart 11: 거래대금 변화율 분포 ===
        ax11 = fig.add_subplot(gs[3, 2])
        if '거래대금변화율' in df_tsg.columns:
            bins_vol = [0, 0.5, 0.8, 1.0, 1.2, 1.5, 100]
            labels_vol = ['~50%', '50-80%', '80-100%', '100-120%', '120-150%', '150%+']
            df_tsg['거래대금변화구간'] = pd.cut(df_tsg['거래대금변화율'], bins=bins_vol, labels=labels_vol, right=False)

            vol_stats = df_tsg.groupby('거래대금변화구간', observed=True).agg({
                '수익금': 'sum',
                '수익률': 'mean'
            })

            x = range(len(vol_stats))
            colors = [color_profit if x >= 0 else color_loss for x in vol_stats['수익금']]
            bars = ax11.bar(x, vol_stats['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax11.set_xticks(x)
            ax11.set_xticklabels(vol_stats.index, rotation=45, ha='right')
            ax11.set_xlabel('거래대금 변화율')
            ax11.set_ylabel('총 수익금')
            ax11.set_title('거래대금 변화율별 수익금')
            ax11.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

        # 저장 및 전송
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.tight_layout(rect=[0, 0.02, 1, 0.97])

        comparison_path = f"{GRAPH_PATH}/{save_file_name}_comparison.png"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.savefig(comparison_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if teleQ is not None:
            teleQ.put(comparison_path)

    except Exception as e:
        print_exc()
        try:
            plt.close('all')
        except:
            pass


def PltBuySellComparison(df_tsg, save_file_name, teleQ=None):
    """
    매수/매도 시점 비교 분석 차트를 생성합니다.

    목적:
        - 매수/매도 시점 변화(매도-매수)와 수익률 관계를 파악
        - 손실/이익 거래의 특징 차이를 비교해 매도/필터 개선 근거 제공

    차트 구성 (중복 최소화):
        1) 등락율 변화 vs 수익률
        2) 체결강도 변화 vs 수익률
        3) 매수 vs 매도 등락율
        4) 매수시점 위험도 점수별 수익금 분포
        5) 등락추세별 수익금(거래수)
        6) 체결강도추세별 수익금(거래수)
        7) 등락추세×체결강도추세 조합별 수익금 히트맵
        8) 손실/이익 거래 특성 비교(매수단/보유시간)
        9) 손실/이익 거래 변화량 비교(매도-매수)
        10) 3D 히트맵: 매수시간×시가총액 → 평균 수익률
        11) 보유시간 vs 수익률 산점도(분 단위)
    """
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

    # 매도 시점 데이터 확인
    required_cols = ['매도등락율', '매도체결강도', '등락율변화', '체결강도변화']
    if not all(col in df_tsg.columns for col in required_cols):
        return

    if len(df_tsg) < 5:
        return

    try:
        df_tsg = df_tsg.copy()
        from matplotlib.ticker import MaxNLocator, AutoMinorLocator

        # 한글 폰트 설정 (개선된 버전)
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_family = font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_family
            plt.rcParams['font.sans-serif'] = [font_family]
        except:
            plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        fig = plt.figure(figsize=(22, 26))
        fig.suptitle(f'매수/매도 시점 비교 분석 - {save_file_name}', fontsize=14, fontweight='bold')
        gs = gridspec.GridSpec(5, 3, figure=fig, hspace=0.55, wspace=0.32)

        color_profit = '#2ECC71'
        color_loss = '#E74C3C'
        color_neutral = '#3498DB'
        df_scatter = df_tsg
        if len(df_tsg) > 20000:
            # 산점도는 대용량에서 렌더링 시간이 급증하므로 샘플링(표시용) 처리
            df_scatter = df_tsg.sample(n=20000, random_state=42)

        # === Chart 1: 등락율 변화 vs 수익률 ===
        ax1 = fig.add_subplot(gs[0, 0])
        colors = np.where(df_scatter['수익률'].to_numpy(dtype=np.float64) >= 0, color_profit, color_loss)
        ax1.scatter(df_scatter['등락율변화'], df_scatter['수익률'], c=colors, alpha=0.5, s=25, edgecolors='none')
        ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax1.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
        ax1.set_xlabel('등락율 변화 (매도-매수) %')
        ax1.set_ylabel('수익률 (%)')
        ax1.set_title('등락율 변화 vs 수익률')
        ax1.xaxis.set_major_locator(MaxNLocator(nbins=9))
        ax1.yaxis.set_major_locator(MaxNLocator(nbins=9))
        ax1.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax1.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax1.grid(True, which='both', alpha=0.25)

        # 사분면 라벨
        ax1.text(0.95, 0.95, '상승+이익', transform=ax1.transAxes, ha='right', va='top', fontsize=8, color='green')
        ax1.text(0.05, 0.95, '하락+이익', transform=ax1.transAxes, ha='left', va='top', fontsize=8, color='blue')
        ax1.text(0.95, 0.05, '상승+손실', transform=ax1.transAxes, ha='right', va='bottom', fontsize=8, color='orange')
        ax1.text(0.05, 0.05, '하락+손실', transform=ax1.transAxes, ha='left', va='bottom', fontsize=8, color='red')

        # === Chart 2: 체결강도 변화 vs 수익률 ===
        ax2 = fig.add_subplot(gs[0, 1])
        colors = np.where(df_scatter['수익률'].to_numpy(dtype=np.float64) >= 0, color_profit, color_loss)
        ax2.scatter(df_scatter['체결강도변화'], df_scatter['수익률'], c=colors, alpha=0.5, s=25, edgecolors='none')
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.set_xlabel('체결강도 변화 (매도-매수)')
        ax2.set_ylabel('수익률 (%)')
        ax2.set_title('체결강도 변화 vs 수익률')
        ax2.xaxis.set_major_locator(MaxNLocator(nbins=9))
        ax2.yaxis.set_major_locator(MaxNLocator(nbins=9))
        ax2.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax2.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax2.grid(True, which='both', alpha=0.25)

        # === Chart 3: 매수 vs 매도 등락율 비교 ===
        ax3 = fig.add_subplot(gs[0, 2])
        colors = np.where(df_scatter['수익률'].to_numpy(dtype=np.float64) >= 0, color_profit, color_loss)
        ax3.scatter(df_scatter['매수등락율'], df_scatter['매도등락율'], c=colors, alpha=0.5, s=25, edgecolors='none')
        max_val = max(df_tsg['매수등락율'].max(), df_tsg['매도등락율'].max())
        min_val = min(df_tsg['매수등락율'].min(), df_tsg['매도등락율'].min())
        ax3.plot([min_val, max_val], [min_val, max_val], 'k--', linewidth=1, alpha=0.5, label='변화없음')
        ax3.set_xlabel('매수 등락율 (%)')
        ax3.set_ylabel('매도 등락율 (%)')
        ax3.set_title('매수 vs 매도 등락율')
        ax3.legend(fontsize=8)
        ax3.xaxis.set_major_locator(MaxNLocator(nbins=9))
        ax3.yaxis.set_major_locator(MaxNLocator(nbins=9))
        ax3.xaxis.set_minor_locator(AutoMinorLocator(2))
        ax3.yaxis.set_minor_locator(AutoMinorLocator(2))
        ax3.grid(True, which='both', alpha=0.25)

        # === Chart 4: 위험도 점수별 수익금 분포(매수시점) ===
        ax4 = fig.add_subplot(gs[1, 0])
        if '위험도점수' in df_tsg.columns:
            risk_bins = [0, 20, 40, 60, 80, 100]
            risk_labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
            df_tsg['위험도구간'] = pd.cut(df_tsg['위험도점수'], bins=risk_bins, labels=risk_labels, right=False)
            df_risk = df_tsg.groupby('위험도구간', observed=True).agg({'수익금': 'sum', '종목명': 'count'}).reset_index()
            df_risk.columns = ['위험도구간', '수익금', '거래횟수']

            x_pos = range(len(df_risk))
            colors = [color_profit if x >= 0 else color_loss for x in df_risk['수익금']]
            bars = ax4.bar(x_pos, df_risk['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax4.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax4.set_xticks(x_pos)
            ax4.set_xticklabels(df_risk['위험도구간'], rotation=45, ha='right', fontsize=9)
            ax4.set_xlabel('매수 위험도 점수 구간')
            ax4.set_ylabel('총 수익금')
            ax4.set_title('매수 위험도 점수별 수익금 분포')
            for bar, cnt in zip(bars, df_risk['거래횟수']):
                ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f'n={int(cnt)}', ha='center',
                         va='bottom' if bar.get_height() >= 0 else 'top', fontsize=8)
        else:
            ax4.text(0.5, 0.5, '위험도점수 컬럼 없음', ha='center', va='center', fontsize=12, transform=ax4.transAxes)
            ax4.axis('off')

        # === Chart 5: 등락추세별 수익금 ===
        ax5 = fig.add_subplot(gs[1, 1])
        if '등락추세' in df_tsg.columns:
            trend_profit = df_tsg.groupby('등락추세')['수익금'].sum()
            trend_count = df_tsg.groupby('등락추세').size()
            colors = [color_profit if trend_profit.get(x, 0) >= 0 else color_loss for x in trend_profit.index]
            bars = ax5.bar(trend_profit.index, trend_profit.values, color=colors, edgecolor='black', linewidth=0.5)
            ax5.set_xlabel('등락 추세')
            ax5.set_ylabel('총 수익금')
            ax5.set_title('등락추세별 수익금')
            ax5.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

            for bar, cnt in zip(bars, trend_count):
                ax5.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=9)

        # === Chart 6: 체결강도추세별 수익금 ===
        ax6 = fig.add_subplot(gs[1, 2])
        if '체결강도추세' in df_tsg.columns:
            ch_trend_profit = df_tsg.groupby('체결강도추세')['수익금'].sum()
            ch_trend_count = df_tsg.groupby('체결강도추세').size()
            colors = [color_profit if ch_trend_profit.get(x, 0) >= 0 else color_loss for x in ch_trend_profit.index]
            bars = ax6.bar(ch_trend_profit.index, ch_trend_profit.values, color=colors, edgecolor='black', linewidth=0.5)
            ax6.set_xlabel('체결강도 추세')
            ax6.set_ylabel('총 수익금')
            ax6.set_title('체결강도추세별 수익금')
            ax6.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

            for bar, cnt in zip(bars, ch_trend_count):
                ax6.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                         f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=9)

        # === Chart 7: 추세 조합 히트맵 ===
        ax7 = fig.add_subplot(gs[2, 0])
        if '등락추세' in df_tsg.columns and '체결강도추세' in df_tsg.columns:
            pivot = df_tsg.pivot_table(values='수익금', index='등락추세', columns='체결강도추세',
                                       aggfunc='sum', fill_value=0)
            im = ax7.imshow(pivot.values, cmap='RdYlGn', aspect='auto')
            ax7.set_xticks(range(len(pivot.columns)))
            ax7.set_yticks(range(len(pivot.index)))
            ax7.set_xticklabels(pivot.columns, fontsize=9)
            ax7.set_yticklabels(pivot.index, fontsize=9)
            ax7.set_xlabel('체결강도 추세')
            ax7.set_ylabel('등락 추세')
            ax7.set_title('추세 조합별 수익금')

            vmax = float(np.max(np.abs(pivot.values))) if pivot.size else 0
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    val = pivot.values[i, j]
                    text_color = 'white' if vmax and abs(val) > vmax * 0.5 else 'black'
                    ax7.text(j, i, f'{val/10000:.0f}만', ha='center', va='center', fontsize=8, color=text_color)

            plt.colorbar(im, ax=ax7, shrink=0.8)

        loss_trades = df_tsg[df_tsg['수익금'] < 0]
        profit_trades = df_tsg[df_tsg['수익금'] >= 0]

        # === Chart 8: 손실/이익 거래 특성 비교 (매수/보유) ===
        ax8 = fig.add_subplot(gs[2, 1])
        if len(loss_trades) > 0 and len(profit_trades) > 0:
            compare_specs = []
            if '매수등락율' in df_tsg.columns:
                compare_specs.append(('매수등락율', '매수등락율(%)', 1.0))
            if '매수체결강도' in df_tsg.columns:
                compare_specs.append(('매수체결강도', '매수체결강도', 1.0))
            if '위험도점수' in df_tsg.columns:
                compare_specs.append(('위험도점수', '매수 위험도점수', 1.0))
            if '보유시간' in df_tsg.columns:
                compare_specs.append(('보유시간', '보유시간(분)', 1.0 / 60.0))

            if compare_specs:
                loss_means = [loss_trades[c].mean() * scale for c, _, scale in compare_specs]
                profit_means = [profit_trades[c].mean() * scale for c, _, scale in compare_specs]

                x = np.arange(len(compare_specs))
                width = 0.35
                ax8.bar(x - width/2, loss_means, width, label='손실거래', color=color_loss, alpha=0.8)
                ax8.bar(x + width/2, profit_means, width, label='이익거래', color=color_profit, alpha=0.8)
                ax8.set_xticks(x)
                ax8.set_xticklabels([label for _, label, _ in compare_specs], rotation=45, ha='right', fontsize=9)
                ax8.set_ylabel('평균값')
                ax8.set_title('손실/이익 거래 특성 비교 (매수/보유)')
                ax8.legend(fontsize=9)

        # === Chart 9: 손실/이익 거래 변화량 비교 (매도-매수) ===
        ax9 = fig.add_subplot(gs[2, 2])
        if len(loss_trades) > 0 and len(profit_trades) > 0:
            compare_cols = ['등락율변화', '체결강도변화', '거래대금변화율', '호가잔량비변화', '매수매도위험도점수']
            available_cols = [c for c in compare_cols if c in df_tsg.columns]
            if available_cols:
                loss_means = [loss_trades[c].mean() for c in available_cols]
                profit_means = [profit_trades[c].mean() for c in available_cols]

                x = np.arange(len(available_cols))
                width = 0.35
                ax9.bar(x - width/2, loss_means, width, label='손실거래', color=color_loss, alpha=0.8)
                ax9.bar(x + width/2, profit_means, width, label='이익거래', color=color_profit, alpha=0.8)
                ax9.set_xticks(x)
                ax9.set_xticklabels(available_cols, rotation=45, ha='right', fontsize=9)
                ax9.set_ylabel('평균값')
                ax9.set_title('손실/이익 거래 변화량 비교 (매도-매수)')
                ax9.legend(fontsize=9)

        # === Chart 10: 3D 히트맵(매수시간×시가총액 → 평균 수익률) ===
        ax10 = fig.add_subplot(gs[3, :])
        try:
            required_heat_cols = {'시가총액', '수익률'}
            has_time_cols = {'매수시', '매수분'}.issubset(df_tsg.columns)
            if required_heat_cols.issubset(df_tsg.columns) and has_time_cols:
                from matplotlib.colors import TwoSlopeNorm

                df_heat = df_tsg[['매수시', '매수분', '시가총액', '수익률']].copy()
                if '매수초' in df_tsg.columns:
                    df_heat['매수초'] = df_tsg['매수초']
                else:
                    df_heat['매수초'] = 0

                hour = pd.to_numeric(df_heat['매수시'], errors='coerce').fillna(0).astype(int)
                minute = pd.to_numeric(df_heat['매수분'], errors='coerce').fillna(0).astype(int)
                second = pd.to_numeric(df_heat['매수초'], errors='coerce').fillna(0).astype(int)
                minute_of_day = (hour * 60 + minute + (second / 60.0)).astype(float)

                min_val = float(np.nanmin(minute_of_day.to_numpy(dtype=np.float64)))
                max_val = float(np.nanmax(minute_of_day.to_numpy(dtype=np.float64)))
                span = max_val - min_val

                desired_bins = 18
                raw_step = max(1, int(np.ceil(span / max(desired_bins, 1)))) if span > 0 else 5
                step_candidates = [1, 2, 5, 10, 15, 30, 60]
                step = next((c for c in step_candidates if c >= raw_step), step_candidates[-1])
                start = float(np.floor(min_val / step) * step)
                end = float(np.ceil(max_val / step) * step)
                if end <= start:
                    end = start + step
                bins = np.arange(start, end + step, step, dtype=float)
                if len(bins) < 3:
                    bins = np.array([start, start + step, start + 2 * step], dtype=float)

                time_labels = [f"{int(t // 60):02d}:{int(t % 60):02d}" for t in bins[:-1]]
                df_heat['매수시간구간'] = pd.cut(minute_of_day, bins=bins, labels=time_labels, right=False, include_lowest=True)

                mcap = pd.to_numeric(df_heat['시가총액'], errors='coerce')
                mcap_bins = [0, 500, 1000, 2000, 3000, 5000, 10000, 20000, 50000, np.inf]
                mcap_labels = ['~500억', '500-1000억', '1000-2000억', '2000-3000억', '3000-5000억',
                               '0.5-1조', '1-2조', '2-5조', '5조+']
                df_heat['시총구간_3D'] = pd.cut(mcap, bins=mcap_bins, labels=mcap_labels, right=False, include_lowest=True)

                df_heat = df_heat.dropna(subset=['매수시간구간', '시총구간_3D'])
                if len(df_heat) >= 10:
                    pivot = df_heat.pivot_table(values='수익률', index='시총구간_3D', columns='매수시간구간',
                                                aggfunc='mean', observed=True)
                    pivot_count = df_heat.pivot_table(values='수익률', index='시총구간_3D', columns='매수시간구간',
                                                      aggfunc='size', fill_value=0, observed=True)

                    pivot = pivot.reindex(index=mcap_labels, columns=time_labels).dropna(axis=0, how='all').dropna(axis=1, how='all')
                    pivot_count = pivot_count.reindex(index=pivot.index, columns=pivot.columns)

                    if pivot.size > 0:
                        data = pivot.to_numpy(dtype=np.float64)
                        data_masked = np.ma.masked_invalid(data)

                        abs_max = float(np.nanpercentile(np.abs(data), 95)) if np.isfinite(data).any() else 1.0
                        abs_max = max(abs_max, 0.5)
                        norm = TwoSlopeNorm(vcenter=0.0, vmin=-abs_max, vmax=abs_max)

                        cmap = plt.get_cmap('RdYlGn').copy()
                        cmap.set_bad(color='#F2F2F2')

                        im = ax10.imshow(data_masked, cmap=cmap, norm=norm, aspect='auto', interpolation='nearest')
                        ax10.set_title('3D 히트맵: 매수시간×시가총액 → 평균 수익률(%)')
                        ax10.set_xlabel('매수시간(시:분, 구간)')
                        ax10.set_ylabel('시가총액 구간')

                        xcnt = len(pivot.columns)
                        ycnt = len(pivot.index)
                        x_step = max(1, int(np.ceil(xcnt / 20)))
                        ax10.set_xticks(np.arange(0, xcnt, x_step))
                        ax10.set_xticklabels([pivot.columns[i] for i in range(0, xcnt, x_step)],
                                             rotation=45, ha='right', fontsize=8)
                        ax10.set_yticks(np.arange(ycnt))
                        ax10.set_yticklabels(pivot.index, fontsize=9)
                        ax10.grid(False)

                        cbar = plt.colorbar(im, ax=ax10, shrink=0.9, pad=0.02)
                        cbar.set_label('평균 수익률(%)', fontsize=9)

                        if ycnt <= 9 and xcnt <= 18:
                            for yi in range(ycnt):
                                for xi in range(xcnt):
                                    v = data[yi, xi]
                                    n_raw = pivot_count.iat[yi, xi] if pivot_count is not None else 0
                                    try:
                                        n = int(n_raw) if np.isfinite(n_raw) else 0
                                    except Exception:
                                        n = 0
                                    if not np.isfinite(v) or n <= 0:
                                        continue
                                    txt_color = 'white' if abs(v) > abs_max * 0.5 else 'black'
                                    ax10.text(xi, yi, f"{v:.1f}\n(n={n})", ha='center', va='center', fontsize=7, color=txt_color)
                    else:
                        ax10.text(0.5, 0.5, '3D 히트맵 데이터 부족', ha='center', va='center', fontsize=12, transform=ax10.transAxes)
                        ax10.axis('off')
                else:
                    ax10.text(0.5, 0.5, '3D 히트맵 데이터 부족', ha='center', va='center', fontsize=12, transform=ax10.transAxes)
                    ax10.axis('off')
            else:
                ax10.text(0.5, 0.5, '3D 히트맵 생성 불가(시가총액/매수시간 컬럼 부족)', ha='center', va='center', fontsize=11, transform=ax10.transAxes)
                ax10.axis('off')
        except Exception:
            ax10.text(0.5, 0.5, '3D 히트맵 생성 중 오류', ha='center', va='center', fontsize=11, transform=ax10.transAxes)
            ax10.axis('off')

        # === Chart 11: 보유시간 vs 수익률 (분 단위) ===
        ax11 = fig.add_subplot(gs[4, :])
        if '보유시간' in df_tsg.columns:
            plot_df = df_scatter if '보유시간' in df_scatter.columns else df_tsg
            colors = np.where(plot_df['수익률'].to_numpy(dtype=np.float64) >= 0, color_profit, color_loss)
            hold_minutes = plot_df['보유시간'] / 60.0
            ax11.scatter(hold_minutes, plot_df['수익률'], c=colors, alpha=0.5, s=25, edgecolors='none')
            ax11.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax11.set_xlabel('보유시간(분)')
            ax11.set_ylabel('수익률(%)')
            ax11.set_title('보유시간 vs 수익률')
            ax11.xaxis.set_major_locator(MaxNLocator(nbins=12))
            ax11.xaxis.set_minor_locator(AutoMinorLocator(2))
            ax11.yaxis.set_major_locator(MaxNLocator(nbins=10))
            ax11.yaxis.set_minor_locator(AutoMinorLocator(2))
            ax11.grid(True, which='both', alpha=0.25)

        # 저장 및 전송
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.tight_layout(rect=[0, 0.02, 1, 0.97])

        comparison_path = f"{GRAPH_PATH}/{save_file_name}_comparison.png"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            plt.savefig(comparison_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if teleQ is not None:
            teleQ.put(comparison_path)

    except Exception as e:
        print_exc()
        try:
            plt.close('all')
        except:
            pass


def RunFullAnalysis(df_tsg, save_file_name, teleQ=None,
                    export_detail=True, export_summary=True, export_filter=True,
                    include_filter_recommendations=True):
    """
    전체 분석을 실행합니다 (CSV 출력 + 시각화).

    Args:
        df_tsg: 백테스팅 결과 DataFrame
        save_file_name: 저장 파일명
        teleQ: 텔레그램 전송 큐
        export_detail: detail.csv 생성 여부
        export_summary: summary.csv 생성 여부
        export_filter: filter.csv 생성 여부
        include_filter_recommendations: 기본 필터 추천 메시지 전송 여부

    Returns:
        dict: 분석 결과 요약
    """
    result = {
        'csv_files': None,
        'charts': [],
        'recommendations': []
    }

    try:
        # 1. 파생 지표 계산
        df_analysis = CalculateDerivedMetrics(df_tsg)

        # 2. CSV 파일 출력
        csv_paths = ExportBacktestCSV(
            df_analysis,
            save_file_name,
            teleQ,
            write_detail=export_detail,
            write_summary=export_summary,
            write_filter=export_filter
        )
        result['csv_files'] = csv_paths

        # 3. 매수/매도 비교 차트 생성
        PltBuySellComparison(df_analysis, save_file_name, teleQ)
        result['charts'].append(f"{GRAPH_PATH}/{save_file_name}_comparison.png")

        # 4. 필터 추천 생성/전송 (기본 분석)
        if include_filter_recommendations:
            filter_results = AnalyzeFilterEffects(df_analysis)
            top_filters = [f for f in filter_results if f.get('적용권장', '').count('★') >= 2]

            for f in top_filters[:5]:
                result['recommendations'].append(
                    f"[{f['분류']}] {f['필터명']}: 수익개선 {f['수익개선금액']:,}원 예상"
                )

            if teleQ is not None and result['recommendations']:
                msg = "📊 필터 추천:\n" + "\n".join(result['recommendations'])
                teleQ.put(msg)

    except Exception as e:
        print_exc()

    return result
