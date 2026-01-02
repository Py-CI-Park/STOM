import re
import pyupbit
import sqlite3
import operator
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from traceback import print_exc
from utility.static import strp_time, strf_time
from utility.setting import ui_num, DB_SETTING
from backtester.output_paths import ensure_backtesting_output_dir, build_backtesting_output_path
from backtester.detail_schema import reorder_detail_columns
from backtester.analysis.exports import ExportBacktestCSV, ExportBacktestCSVParallel
from backtester.analysis.output_config import get_backtesting_output_config
from backtester.analysis.cache import load_cached_df, save_cached_df, build_df_signature
from backtester.analysis.indicators import AddAvgData, GetIndicator
from backtester.analysis.metrics_base import CalculateDerivedMetrics, AnalyzeFilterEffects
from backtester.analysis.optuna_server import RunOptunaServer
from backtester.analysis.plotting import (
    PltAnalysisCharts,
    PltBuySellComparison,
    PltBuySellComparison_Legacy,
    PltFilterAppliedPreviewCharts,
    PltShow,
)
from backtester.analysis.results import AddMdd, GetBackResult, GetResultDataframe
from backtester.analysis.text_utils import _extract_strategy_block_lines

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

SEGMENT_ANALYSIS_MODE = 'phase2+3'
SEGMENT_ANALYSIS_OUTPUT_DIR = None
SEGMENT_ANALYSIS_OPTUNA = False
SEGMENT_ANALYSIS_TEMPLATE_COMPARE = True


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


def _load_segment_config_from_ranges(global_best: dict):
    """
    global_best에 저장된 ranges_path를 로드하여 고정 모드 SegmentConfig를 생성합니다.

    [2026-01-01 신규 추가]
    - 목적: 세그먼트 분석 시 사용한 정확한 경계값으로 필터 적용
    - 입력: global_best dict (ranges_path 포함)
    - 출력: SegmentConfig (dynamic_mode='fixed', 저장된 범위 사용)
    - 폴백: ranges_path가 없으면 기본 SegmentConfig 반환
    """
    try:
        from backtester.segment_analysis.segment_apply import load_segment_config_from_ranges
        return load_segment_config_from_ranges(global_best)
    except Exception as e:
        from backtester.segment_analysis.segmentation import SegmentConfig
        print(f"[Warning] ranges.csv 로드 실패: {e}, 기본 설정 사용")
        return SegmentConfig()


def _build_segment_mask_from_global_best(df: pd.DataFrame, global_best: dict):
    """
    세그먼트 전역 조합(global_best)을 이용해 df에서 통과 마스크를 생성합니다.

    [2026-01-01 버그 수정]
    - 기존: 새로운 SegmentBuilder() 생성 → dynamic 모드로 세그먼트 경계 재계산
    - 문제: 분위수 기반 동적 분할은 데이터마다 경계가 달라짐
           → combos.csv 예측값(+1,085M)과 실제 적용값(+972M)이 불일치
    - 원인: 세그먼트 분석 시 계산된 경계와 이미지 생성 시 재계산된 경계가 다름
    - 해결: global_best에 저장된 ranges_path를 로드하여 고정 모드로 세그먼트 분할
    - 결과: 분석 시 사용한 정확한 경계로 필터 적용 → 예측값과 실제값 일치
    """
    try:
        from backtester.segment_analysis.segment_apply import build_segment_mask_from_global_best
        return build_segment_mask_from_global_best(df, global_best)
    except Exception as e:
        return {
            'mask': None,
            'error': f"세그먼트 필터 적용 실패: {e}",
            'segment_trades': {},
            'missing_columns': [],
            'out_of_range_trades': 0,
        }


def WriteGraphOutputReport(save_file_name, df_tsg, backname=None, seed=None, mdd=None,
                           startday=None, endday=None, starttime=None, endtime=None,
                           buy_vars=None, sell_vars=None, buystg=None, sellstg=None,
                           full_result=None, enhanced_result=None, enhanced_error=None):
    """
    backtester/backtesting_output/<save_file_name> 폴더에 이번 실행의 산출물 목록/요약을 txt로 저장합니다.

    - 생성된 파일 목록(png/csv 등)
    - 생성 시각(파일 수정 시각 기준)
    - 조건식(매수/매도) 및 기본 성과 요약
    - detail.csv 컬럼 설명/공식(이번 실행 기준)
    """
    try:
        def _strip_numeric_prefix(name: str) -> str:
            m = re.match(r'^\d[\d-]*_(.+)$', name)
            return m.group(1) if m else name

        def _describe_output_file(filename: str) -> str:
            filename = _strip_numeric_prefix(filename)
            if filename.endswith('_segment_filtered_.png'):
                return '세그먼트 필터 적용 분포/단계 요약(미리보기)'
            if filename.endswith('_segment_filtered.png'):
                return '세그먼트 필터 적용 수익곡선(미리보기)'
            if filename.endswith('_filtered_.png'):
                return '자동 생성 필터 적용 분포/단계 요약(미리보기)'
            if filename.endswith('_filtered.png'):
                return '자동 생성 필터 적용 수익곡선(미리보기)'
            if filename.endswith('_condition_study.md'):
                return '조건식/필터 스터디 노트(md, 자동 생성)'
            if filename.endswith('_manifest.json'):
                return '산출물 목록/별칭 매니페스트'
            if filename.endswith('_analysis.png'):
                return '백테스팅 결과 분석 차트(분 단위 시간축/구간별 수익 분포)'
            if filename.endswith('_comparison.png'):
                return '매수/매도 시점 비교 분석 차트(변화량/추세/위험도/3D 히트맵 등)'
            if filename.endswith('_enhanced.png'):
                return '필터 기능 분석 차트(통계/시너지/안정성/임계값/코드생성)'
            if filename.endswith('_detail.csv'):
                return '거래 상세 기록(강화 분석 사용 시 강화 파생지표 포함)'
            if filename.endswith('_detail_filtered.csv'):
                return '일반 필터 적용 거래 상세(검증용)'
            if filename.endswith('_detail_segment.csv'):
                return '세그먼트 필터 적용 거래 상세(검증용)'
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
            if filename.endswith('_filter_verification.csv'):
                return '필터 적용 검증 요약'
            if filename.endswith('_segment_summary_full.txt'):
                return '세그먼트 종합 요약 리포트'
            if filename.endswith('_segment_verification.csv'):
                return '세그먼트 필터 적용 검증 요약'
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
                    'desc': '매수등락율/매수체결강도 고정 스케일 기반 모멘텀 점수',
                    'unit': '점수',
                    'formula': [
                        "등락율_norm = 매수등락율 / 10",
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
                # [NEW 2025-12-28] 당일거래대금 시계열 비율 지표
                '당일거래대금_전틱분봉_비율': {
                    'desc': '직전 거래 대비 당일거래대금 변화율',
                    'unit': '배율',
                    'formula': ["현재_당일거래대금 / 직전거래_당일거래대금 if >0 else 1.0"],
                    'note': '첫 거래는 1.0, 거래대금 증감 트렌드 파악용'
                },
                '당일거래대금_매수매도_비율': {
                    'desc': '매수→매도 간 당일거래대금 변화율',
                    'unit': '배율',
                    'formula': ["매도당일거래대금 / 매수당일거래대금 if >0 else 1.0"],
                    'note': '보유 기간 동안 시장 유동성 변화'
                },
                '당일거래대금_5틱분봉평균_비율': {
                    'desc': '최근 5틱/분봉 평균 대비 당일거래대금 비율',
                    'unit': '배율',
                    'formula': ["현재_당일거래대금 / rolling_mean(5) if >0 else 1.0"],
                    'note': '단기 평균 대비 유동성 수준, 노이즈 감소용'
                },
                # [NEW 2025-12-28] ML 예측 지표: 당일거래대금_매수매도_비율 예측값
                '당일거래대금_매수매도_비율_ML': {
                    'desc': '매수시점 변수만으로 예측한 당일거래대금_매수매도_비율',
                    'unit': '배율',
                    'formula': [
                        "ML 회귀 모델 (RandomForest or MLP)",
                        "features: 당일거래대금_전틱분봉_비율, 당일거래대금_5틱분봉평균_비율 등 매수시점 변수",
                        "target: 당일거래대금_매수매도_비율 (매도당일거래대금/매수당일거래대금)"
                    ],
                    'note': 'LOOKAHEAD 있는 실제값 대신 매수시점에서 사용 가능한 예측값. 필터로 안전하게 사용 가능.'
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

        def _collect_segment_outputs(segment_outputs: dict) -> list[tuple[str, str]]:
            if not isinstance(segment_outputs, dict):
                return []

            label_map = {
                'summary_path': '세그먼트 요약',
                'filters_path': '세그먼트 필터 후보',
                'local_combo_path': '세그먼트 로컬 조합',
                'global_combo_path': '전역 조합 요약',
                'thresholds_path': 'Optuna 임계값',
                'segment_code_path': '세그먼트 조건식 코드',
                'segment_code_final_path': '세그먼트 최종 조건식 코드(매수조건 통합)',
                'validation_path': '안정성 검증',
                'heatmap_path': '세그먼트 히트맵',
                'efficiency_path': '필터 효율 차트',
                'comparison_path': '세그먼트 템플릿 비교',
                'summary_report_path': '세그먼트 종합 요약',
            }

            items: list[tuple[str, str]] = []
            for phase_key in ('phase2', 'phase3'):
                phase = segment_outputs.get(phase_key) or {}
                if not isinstance(phase, dict):
                    continue
                for key, label in label_map.items():
                    path = phase.get(key)
                    if path:
                        items.append((label, str(path)))

            template_comp = segment_outputs.get('template_comparison') or {}
            if isinstance(template_comp, dict):
                path = template_comp.get('comparison_path')
                if path:
                    items.append((label_map['comparison_path'], str(path)))

            summary_report_path = segment_outputs.get('summary_report_path')
            if summary_report_path:
                items.append((label_map['summary_report_path'], str(summary_report_path)))

            seen = set()
            deduped = []
            for label, path in items:
                if path in seen:
                    continue
                seen.add(path)
                deduped.append((label, path))

            return deduped

        output_dir = ensure_backtesting_output_dir(save_file_name)
        manifest_path = None
        cfg = {}
        enable_manifest = False
        enable_alias = True
        alias_mode = 'hardlink'
        alias_dir = None
        cleanup_legacy = False
        try:
            cfg = get_backtesting_output_config() or {}
            enable_manifest = bool(cfg.get('output_manifest_enabled', True))
            enable_alias = bool(cfg.get('output_alias_enabled', True))
            alias_mode = str(cfg.get('output_alias_mode', 'hardlink'))
            alias_dir = cfg.get('output_alias_subdir') or None
            cleanup_legacy = bool(cfg.get('output_alias_cleanup_legacy', False))
            if enable_manifest:
                from backtester.output_manifest import build_output_manifest
                manifest_path = build_output_manifest(
                    output_dir,
                    save_file_name,
                    enable_alias=enable_alias,
                    alias_mode=alias_mode,
                    alias_dir=alias_dir,
                    cleanup_legacy=False,
                )
        except Exception:
            manifest_path = None

        report_path = build_backtesting_output_path(save_file_name, "_report.txt", output_dir=output_dir)

        now = datetime.now()
        lines = []
        lines.append("=== STOM Backtester Output Report ===")
        lines.append(f"- 생성 시각: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"- 저장 키(save_file_name): {save_file_name}")
        lines.append(f"- 출력 경로: {output_dir}")
        if manifest_path:
            lines.append(f"- 매니페스트: {manifest_path}")
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
                        lines.append("[적용 순서(추가개선→누적개선, 누적수익금, 누적제외%)]")
                        for st in steps[:10]:
                            try:
                                cum_profit_val = st.get('누적수익금')
                                cum_profit_text = f"{int(cum_profit_val):,}원" if cum_profit_val is not None else "N/A"
                                lines.append(
                                    f"- {st.get('순서', '')}. {str(st.get('필터명', ''))[:24]}: "
                                    f"+{int(st.get('추가개선(중복반영)', 0) or 0):,} → "
                                    f"누적 +{int(st.get('누적개선(동시적용)', 0) or 0):,} "
                                    f"(누적 수익금 {cum_profit_text}) "
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

        # 세그먼트 분석 산출물
        if enhanced_result and enhanced_result.get('segment_outputs'):
            lines.append("")
            lines.append("=== 세그먼트 분석 산출물 ===")
            seg_items = _collect_segment_outputs(enhanced_result.get('segment_outputs') or {})
            if not seg_items:
                lines.append("- 없음")
            else:
                for label, path in seg_items:
                    lines.append(f"- {label}: {path}")

        # 파일 목록
        lines.append("")
        lines.append("=== 생성 파일 목록 ===")
        prefix = str(save_file_name)
        matched = []
        matched_map = {}
        for p in output_dir.iterdir():
            if not p.is_file():
                continue
            name = p.name
            norm_name = _strip_numeric_prefix(name)
            if not norm_name.startswith(prefix):
                continue
            rest = norm_name[len(prefix):]
            if not (rest == '' or rest.startswith('_') or rest.startswith('.')):
                continue
            key = norm_name
            if key not in matched_map:
                matched_map[key] = p
            else:
                # 숫자 프리픽스(새 이름)를 우선 선택
                if name != norm_name and matched_map[key].name == norm_name:
                    matched_map[key] = p
        matched = sorted(matched_map.values(), key=lambda x: x.name)
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
            study_path = build_backtesting_output_path(save_file_name, "_condition_study.md", output_dir=output_dir)
            study_lines: list[str] = []

            study_lines.append("# 조건식/필터 스터디 노트 (자동 생성)")
            study_lines.append("")
            study_lines.append(f"- 생성 시각: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            study_lines.append(f"- save_file_name: {save_file_name}")
            study_lines.append(f"- output_dir: {output_dir}")

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
            study_lines.append(f"- `{build_backtesting_output_path(save_file_name, '_enhanced.png', output_dir=output_dir).name}`: 강화 분석 차트(Chart 18 포함)")
            study_lines.append(f"- `{build_backtesting_output_path(save_file_name, '_filter.csv', output_dir=output_dir).name}`: 필터 후보/조건식 목록")
            study_lines.append(f"- `{build_backtesting_output_path(save_file_name, '_detail.csv', output_dir=output_dir).name}`: 거래 상세 기록(컬럼=거래 항목)")
            study_lines.append(f"- `{build_backtesting_output_path(save_file_name, '_report.txt', output_dir=output_dir).name}`: 실행 리포트")

            seg_items = _collect_segment_outputs((enhanced_result or {}).get('segment_outputs') or {})
            if seg_items:
                study_lines.append("")
                study_lines.append("### 세그먼트 분석 산출물")
                for label, path in seg_items:
                    try:
                        study_lines.append(f"- `{Path(path).name}`: {label}")
                    except Exception:
                        study_lines.append(f"- {path}: {label}")

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
                    study_lines.append("### 적용 순서(추가개선→누적개선, 누적수익금, 누적제외%)")
                    for st in steps[:10]:
                        try:
                            cum_profit_val = st.get('누적수익금')
                            cum_profit_text = f"{int(cum_profit_val):,}원" if cum_profit_val is not None else "N/A"
                            study_lines.append(
                                f"- {st.get('순서', '')}. {str(st.get('필터명', ''))[:30]}: "
                                f"+{int(st.get('추가개선(중복반영)', 0) or 0):,} → "
                                f"누적 +{int(st.get('누적개선(동시적용)', 0) or 0):,} "
                                f"(누적 수익금 {cum_profit_text}) "
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
        try:
            if enable_manifest and cleanup_legacy:
                from backtester.output_manifest import build_output_manifest
                manifest_path = build_output_manifest(
                    output_dir,
                    save_file_name,
                    enable_alias=enable_alias,
                    alias_mode=alias_mode,
                    alias_dir=alias_dir,
                    cleanup_legacy=True,
                )
                if enable_alias:
                    alias_root = output_dir / alias_dir if alias_dir else output_dir
                    report_alias_path = build_backtesting_output_path(save_file_name, "_report.txt", output_dir=alias_root)
                    if report_alias_path.exists():
                        return str(report_alias_path)
        except Exception:
            pass
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


def RunFullAnalysis(df_tsg, save_file_name, teleQ=None,
                    export_detail=True, export_summary=True, export_filter=True,
                    include_filter_recommendations=True,
                    run_comparison_charts: bool = True,
                    buystg_name: str = None, sellstg_name: str = None,
                    startday=None, endday=None, starttime=None, endtime=None):
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
        # 1. 파생 지표 계산 (캐시 재사용)
        cfg = get_backtesting_output_config()
        use_cache = bool(cfg.get('enable_cache', False))
        df_signature = build_df_signature(df_tsg)
        df_analysis = None
        if use_cache:
            df_analysis = load_cached_df(save_file_name, 'derived_metrics', signature=df_signature)
        if df_analysis is None:
            df_analysis = CalculateDerivedMetrics(df_tsg)
            if use_cache:
                save_cached_df(save_file_name, 'derived_metrics', df_analysis, signature=df_signature)

        # 2. CSV 파일 출력
        if cfg.get('enable_csv_parallel', False):
            csv_paths = ExportBacktestCSVParallel(
                df_analysis,
                save_file_name,
                teleQ,
                write_detail=export_detail,
                write_summary=export_summary,
                write_filter=export_filter,
                df_analysis=df_analysis
            )
        else:
            csv_paths = ExportBacktestCSV(
                df_analysis,
                save_file_name,
                teleQ,
                write_detail=export_detail,
                write_summary=export_summary,
                write_filter=export_filter,
                df_analysis=df_analysis
            )
        result['csv_files'] = csv_paths

        # 3. 매수/매도 비교 차트 생성
        if run_comparison_charts:
            PltBuySellComparison(
                df_analysis,
                save_file_name,
                teleQ,
                buystg_name=buystg_name,
                sellstg_name=sellstg_name,
                startday=startday,
                endday=endday,
                starttime=starttime,
                endtime=endtime,
            )
        output_dir = ensure_backtesting_output_dir(save_file_name)
        result['charts'].append(str(build_backtesting_output_path(save_file_name, "_comparison.png", output_dir=output_dir)))

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
