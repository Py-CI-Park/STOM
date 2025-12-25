# -*- coding: utf-8 -*-
"""
[2025-12-10] 백테스팅 결과 분석 강화 모듈
[2025-12-13] 추가 개선 적용

기능:
1. 통계적 유의성 검증 (t-test, 효과 크기)
2. 필터 조합 분석 (시너지 효과)
3. ML 기반 특성 중요도 분석
4. 동적 최적 임계값 탐색
5. 조건식 코드 자동 생성
6. 기간별 필터 안정성 검증
7. Tick/Min 타임프레임 자동 감지 (NEW)
8. 필터 조합 시너지 히트맵 시각화 (NEW)
9. 최적 임계값 효율성 곡선 차트 (NEW)
10. 동적 X축 세분화 (데이터 분포 기반) (NEW)
11. 위험도 공식 차트 표시 (NEW)

Author: Claude
Date: 2025-12-10, Updated: 2025-12-13
"""

import numpy as np
import pandas as pd
import hashlib
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from scipy import stats
from itertools import combinations
from traceback import print_exc
from matplotlib import pyplot as plt
from matplotlib import font_manager, gridspec
from backtester.output_paths import ensure_backtesting_output_dir
from backtester.detail_schema import reorder_detail_columns


# ============================================================================
# ML 모델 저장/로드 유틸
# ============================================================================

MODEL_BASE_DIR = (Path(__file__).resolve().parent / 'models')

# ML 신뢰도 기준(게이팅)
# - 기준 미달이면: 자동 필터 분석/코드 생성에서 *_ML 컬럼 사용 금지(공부/검증 목적의 컬럼 생성은 유지)
# - 2025-12-20 개선: 기준 상향 (55→65 AUC, 50→55 F1, 55→60 BA)
#   기존 55%는 랜덤(50%) 대비 너무 낮음. 학술적으로 AUC 0.7이 "fair", 0.8이 "good" 수준
ML_RELIABILITY_CRITERIA = {
    'min_test_auc': 65.0,               # 55→65: 실용적 최소 수준 (랜덤 50% 대비 15%p 이상)
    'min_test_f1': 55.0,                # 50→55: macro F1
    'min_test_balanced_accuracy': 60.0, # 55→60: 불균형 데이터 기준
}

# 필터 조합 선택 시 제외율/잔여거래 제한 (2025-12-20 신규)
# - 제외율이 100%가 되면 거래가 0건이 되어 무의미함
# - 최소한의 거래가 남아야 실제 트레이딩이 가능함
FILTER_MAX_EXCLUSION_RATIO = 0.85   # 최대 제외율 85% (거래의 15% 이상은 남겨야 함)
FILTER_MIN_REMAINING_TRADES = 30    # 최소 잔여 거래 수 (30건 미만이면 통계적 의미 없음)


def AssessMlReliability(ml_prediction_stats: dict | None,
                        criteria: dict | None = None) -> dict:
    """
    ML 모델 신뢰도 기준을 평가해, *_ML 기반 필터 사용 허용 여부를 반환합니다.

    Returns:
        dict:
            - allow_ml_filters: bool
            - criteria: dict
            - metrics: dict
            - reasons: list[str]
    """
    criteria_local = dict(ML_RELIABILITY_CRITERIA)
    if isinstance(criteria, dict):
        criteria_local.update({k: v for k, v in criteria.items() if v is not None})

    def _to_float_or_none(v):
        try:
            if v is None:
                return None
            if isinstance(v, str) and v.strip().lower() in ('n/a', 'na', 'none', ''):
                return None
            return float(v)
        except Exception:
            return None

    stats = ml_prediction_stats if isinstance(ml_prediction_stats, dict) else {}

    auc = _to_float_or_none(stats.get('test_auc'))
    f1 = _to_float_or_none(stats.get('test_f1'))
    ba = _to_float_or_none(stats.get('test_balanced_accuracy'))

    reasons: list[str] = []
    allow = True

    if auc is None or f1 is None or ba is None:
        allow = False
        if auc is None:
            reasons.append("AUC 값이 없어 신뢰도 판정 불가")
        if f1 is None:
            reasons.append("F1 값이 없어 신뢰도 판정 불가")
        if ba is None:
            reasons.append("Balanced Accuracy 값이 없어 신뢰도 판정 불가")
    else:
        if auc < float(criteria_local['min_test_auc']):
            allow = False
            reasons.append(f"AUC {auc:.1f}% < 기준 {float(criteria_local['min_test_auc']):.1f}%")
        if f1 < float(criteria_local['min_test_f1']):
            allow = False
            reasons.append(f"F1 {f1:.1f}% < 기준 {float(criteria_local['min_test_f1']):.1f}%")
        if ba < float(criteria_local['min_test_balanced_accuracy']):
            allow = False
            reasons.append(f"BA {ba:.1f}% < 기준 {float(criteria_local['min_test_balanced_accuracy']):.1f}%")

    return {
        'allow_ml_filters': bool(allow),
        'criteria': criteria_local,
        'metrics': {
            'test_auc': auc,
            'test_f1': f1,
            'test_balanced_accuracy': ba,
        },
        'reasons': reasons,
    }


def _normalize_text_for_hash(text) -> str:
    if text is None:
        return ''
    s = str(text)
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    return s.strip()


def ComputeStrategyKey(buystg: str = None, sellstg: str = None) -> str:
    """
    매수/매도 전략 코드(전체 텍스트)를 바탕으로 전략 식별키를 생성합니다.
    - 가장 정확한 식별을 위해 sha256(매수코드 + 매도코드) 기반으로 생성
    """
    buy = _normalize_text_for_hash(buystg)
    sell = _normalize_text_for_hash(sellstg)
    payload = f"BUY:\n{buy}\n\nSELL:\n{sell}".encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def _extract_strategy_block_lines(code: str, start_marker: str, end_marker: str | None = None,
                                 max_lines: int = 12, max_line_len: int = 140) -> list[str]:
    """
    전략 문자열에서 특정 블록(예: 'if 매수:' ~ 'if 매도:') 라인 일부만 추출합니다.
    - 텔레그램/차트 표시 목적이므로, 너무 긴 라인은 잘라냅니다.
    """
    try:
        s = _normalize_text_for_hash(code)
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

        out: list[str] = []
        for ln in selected:
            # 주석 제거(간단 버전)
            if '#' in ln:
                ln = ln.split('#', 1)[0]
            ln = ln.rstrip()
            if not ln.strip():
                continue
            if len(ln) > max_line_len:
                ln = ln[: max_line_len - 3] + "..."
            out.append(ln)
        return out
    except Exception:
        return []


def _safe_filename(name: str, max_len: int = 90) -> str:
    """
    Windows 경로 길이 이슈를 줄이기 위한 안전한 파일명 생성.
    - 너무 길면 앞부분 + 해시로 축약
    """
    s = str(name) if name is not None else 'run'
    s = s.replace('\\', '_').replace('/', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_') \
         .replace('<', '_').replace('>', '_').replace('|', '_')
    s = s.strip()
    if len(s) <= max_len:
        return s
    h = hashlib.sha1(s.encode('utf-8')).hexdigest()[:10]
    return f"{s[:max_len - 11]}_{h}"


def _write_json(path: Path, data: dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8-sig')
    except Exception:
        pass


def _append_jsonl(path: Path, data: dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8-sig') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _save_ml_bundle(bundle: dict, strategy_key: str, save_file_name: str):
    """
    ML 번들을 실행별로 저장하고(누적), 전략 폴더의 latest도 갱신합니다.
    Returns:
        dict: 저장 결과(경로/오류)
    """
    result = {
        'saved': False,
        'strategy_key': strategy_key,
        'run_bundle_path': None,
        'latest_bundle_path': None,
        'run_meta_path': None,
        'latest_meta_path': None,
        'strategy_dir': None,
        'error': None,
    }
    if not strategy_key or not save_file_name:
        result['error'] = 'strategy_key/save_file_name 누락'
        return result

    try:
        from joblib import dump as joblib_dump
    except Exception as e:
        result['error'] = f'joblib import 실패: {e}'
        return result

    try:
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        safe_save = _safe_filename(save_file_name, max_len=80)
        run_id = hashlib.sha1(str(save_file_name).encode('utf-8')).hexdigest()[:10]

        strategy_dir = MODEL_BASE_DIR / 'strategies' / str(strategy_key)
        runs_dir = strategy_dir / 'runs'
        runs_dir.mkdir(parents=True, exist_ok=True)

        run_bundle_path = runs_dir / f"{safe_save}_{run_id}_{ts}_ml_bundle.joblib"
        run_meta_path = runs_dir / f"{safe_save}_{run_id}_{ts}_ml_bundle_meta.json"

        # 저장 (압축 레벨은 속도/용량 균형)
        joblib_dump(bundle, run_bundle_path, compress=3)

        meta = {
            'bundle_version': bundle.get('bundle_version'),
            'created_at': bundle.get('created_at'),
            'save_file_name': bundle.get('save_file_name'),
            'strategy_key': bundle.get('strategy_key'),
            'feature_schema_hash': bundle.get('feature_schema_hash'),
            'n_features': len(bundle.get('features_loss') or []),
            'model_type': (bundle.get('train_stats') or {}).get('model_type'),
            'train_mode': bundle.get('train_mode'),
            'paths': {
                'run_bundle': str(run_bundle_path),
            },
        }
        _write_json(run_meta_path, meta)

        # latest 갱신
        latest_bundle_path = strategy_dir / 'latest_ml_bundle.joblib'
        latest_meta_path = strategy_dir / 'latest_ml_bundle_meta.json'
        try:
            shutil.copy2(run_bundle_path, latest_bundle_path)
            shutil.copy2(run_meta_path, latest_meta_path)
        except Exception:
            # 복사 실패하더라도 run 저장은 성공으로 처리
            pass

        # 전략 코드(해시 대상) 저장 (있으면 유지)
        try:
            strategy_code_path = strategy_dir / 'strategy_code.txt'
            if not strategy_code_path.exists():
                buystg = bundle.get('strategy', {}).get('buystg', '')
                sellstg = bundle.get('strategy', {}).get('sellstg', '')
                strategy_code_path.write_text(
                    "=== BUY STRATEGY ===\n"
                    + _normalize_text_for_hash(buystg)
                    + "\n\n=== SELL STRATEGY ===\n"
                    + _normalize_text_for_hash(sellstg)
                    + "\n",
                    encoding='utf-8-sig'
                )
        except Exception:
            pass

        # 인덱스(누적 로그)
        _append_jsonl(strategy_dir / 'runs_index.jsonl', meta)

        result.update({
            'saved': True,
            'run_bundle_path': str(run_bundle_path),
            'latest_bundle_path': str(latest_bundle_path) if latest_bundle_path.exists() else None,
            'run_meta_path': str(run_meta_path),
            'latest_meta_path': str(latest_meta_path) if latest_meta_path.exists() else None,
            'strategy_dir': str(strategy_dir),
        })
        return result
    except Exception as e:
        result['error'] = str(e)
        return result


def _load_ml_bundle(path: Path):
    try:
        from joblib import load as joblib_load
        return joblib_load(path)
    except Exception:
        return None


def _feature_schema_hash(features) -> str:
    try:
        cols = [str(c) for c in (features or [])]
        cols_sorted = sorted(set(cols))
        payload = ("\n".join(cols_sorted)).encode('utf-8')
        return hashlib.sha256(payload).hexdigest()
    except Exception:
        return None


def _prepare_feature_matrix(df: pd.DataFrame, feature_list):
    """
    feature_list 순서대로 X를 생성합니다.
    - 컬럼이 없으면 생성(NaN) 후 0으로 채움
    - NaN은 각 컬럼 median으로 채움(모두 NaN이면 0)
    """
    df_local = df.copy()
    features = [str(c) for c in (feature_list or [])]
    for col in features:
        if col not in df_local.columns:
            df_local[col] = np.nan
        df_local[col] = pd.to_numeric(df_local[col], errors='coerce')
        med = float(df_local[col].median()) if df_local[col].notna().any() else 0.0
        df_local[col] = df_local[col].fillna(med)
    X = df_local[features].to_numpy(dtype=np.float64)
    return X


def _apply_ml_bundle(df: pd.DataFrame, bundle: dict):
    """
    저장된 ML 번들을 이용해 df에 _ML 컬럼을 채웁니다.
    Returns:
        (df, info_dict)
    """
    info = {
        'used_saved_model': False,
        'missing_features': [],
        'strategy_key': None,
        'feature_schema_hash': None,
    }
    if not isinstance(bundle, dict):
        return df, info

    try:
        features = bundle.get('features_loss') or []
        scaler = bundle.get('scaler_loss')
        rf_model = bundle.get('rf_model')
        gb_model = bundle.get('gb_model')

        info['strategy_key'] = bundle.get('strategy_key')
        info['feature_schema_hash'] = bundle.get('feature_schema_hash')

        # 결측 피처 체크
        missing = [c for c in features if c not in df.columns]
        info['missing_features'] = missing

        X_all = _prepare_feature_matrix(df, features)
        X_all_scaled = scaler.transform(X_all) if scaler is not None else X_all

        rf_proba_all = rf_model.predict_proba(X_all_scaled)[:, 1] if rf_model is not None else None
        gb_proba_all = gb_model.predict_proba(X_all_scaled)[:, 1] if gb_model is not None else None

        if rf_proba_all is not None and gb_proba_all is not None:
            loss_prob_all = (rf_proba_all + gb_proba_all) / 2
        elif rf_proba_all is not None:
            loss_prob_all = rf_proba_all
        elif gb_proba_all is not None:
            loss_prob_all = gb_proba_all
        else:
            loss_prob_all = np.full(len(df), 0.5, dtype=np.float64)

        df = df.copy()
        df['손실확률_ML'] = loss_prob_all
        df['위험도_ML'] = (loss_prob_all * 100).clip(0, 100)

        # (옵션) 매수매도위험도 회귀 예측
        rr = bundle.get('risk_regression') if isinstance(bundle.get('risk_regression'), dict) else None
        if rr and rr.get('model') is not None and rr.get('scaler') is not None:
            try:
                Xr_all = _prepare_feature_matrix(df, rr.get('features') or features)
                Xr_all_s = rr['scaler'].transform(Xr_all)
                pred_all = rr['model'].predict(Xr_all_s)
                df['예측매수매도위험도점수_ML'] = np.clip(pred_all, 0, 100)
            except Exception:
                df['예측매수매도위험도점수_ML'] = np.nan
        else:
            if '예측매수매도위험도점수_ML' not in df.columns:
                df['예측매수매도위험도점수_ML'] = np.nan

        info['used_saved_model'] = True
        return df, info
    except Exception:
        return df, info


def _extract_tree_rules(tree_model, scaler, feature_names, max_depth: int = 2):
    """
    설명용(규칙화) 간단 트리 규칙 추출.
    - scaler가 있으면 임계값을 원 스케일로 복원합니다.
    """
    rules = []
    try:
        tree = tree_model.tree_
    except Exception:
        return rules

    def _inv_scale(feature_idx: int, thr: float) -> float:
        try:
            if scaler is None:
                return float(thr)
            return float(thr) * float(scaler.scale_[feature_idx]) + float(scaler.mean_[feature_idx])
        except Exception:
            return float(thr)

    def _walk(node_id: int, depth: int):
        if depth > max_depth:
            return
        # 내부 노드인지 확인
        if tree.feature[node_id] == -2:
            return
        feature_idx = int(tree.feature[node_id])
        feature_name = feature_names[feature_idx] if feature_idx < len(feature_names) else f"f{feature_idx}"
        thr_scaled = float(tree.threshold[node_id])
        thr = _inv_scale(feature_idx, thr_scaled)
        left = int(tree.children_left[node_id])
        right = int(tree.children_right[node_id])
        try:
            left_n = int(tree.n_node_samples[left])
            right_n = int(tree.n_node_samples[right])
            left_val = tree.value[left][0]
            right_val = tree.value[right][0]
            left_loss_rate = float(left_val[1] / (left_val[0] + left_val[1]) * 100) if (left_val[0] + left_val[1]) > 0 else 0.0
            right_loss_rate = float(right_val[1] / (right_val[0] + right_val[1]) * 100) if (right_val[0] + right_val[1]) > 0 else 0.0
        except Exception:
            left_n = right_n = 0
            left_loss_rate = right_loss_rate = 0.0

        rules.append({
            'depth': depth,
            'feature': feature_name,
            'threshold': round(thr, 6),
            'rule_left': f"{feature_name} < {thr:.6g}",
            'rule_right': f"{feature_name} >= {thr:.6g}",
            'left_samples': left_n,
            'right_samples': right_n,
            'left_loss_rate': round(left_loss_rate, 2),
            'right_loss_rate': round(right_loss_rate, 2),
        })

        _walk(left, depth + 1)
        _walk(right, depth + 1)

    _walk(0, 0)
    return rules[:15]


# ============================================================================
# 1. 통계적 유의성 검증
# ============================================================================

def CalculateStatisticalSignificance(filtered_out, remaining):
    """
    필터 효과의 통계적 유의성을 계산합니다.

    Args:
        filtered_out: 제외되는 거래 DataFrame 또는 수익금 배열/시리즈
        remaining: 남는 거래 DataFrame 또는 수익금 배열/시리즈

    Returns:
        dict: 통계 검정 결과
            - t_stat: t-통계량
            - p_value: p-값
            - effect_size: Cohen's d 효과 크기
            - confidence_interval: 95% 신뢰구간
            - significant: 유의한지 여부 (p < 0.05)
    """
    result = {
        't_stat': 0,
        'p_value': 1.0,
        'effect_size': 0,
        'confidence_interval': (0, 0),
        'significant': False
    }

    if len(filtered_out) < 2 or len(remaining) < 2:
        return result

    try:
        def _to_profit_array(obj):
            if isinstance(obj, pd.DataFrame):
                if '수익금' in obj.columns:
                    return obj['수익금'].to_numpy(dtype=np.float64)
                return obj.to_numpy(dtype=np.float64).reshape(-1)
            if isinstance(obj, pd.Series):
                return obj.to_numpy(dtype=np.float64)
            return np.asarray(obj, dtype=np.float64)

        # 두 그룹의 수익금
        group1 = _to_profit_array(filtered_out)
        group2 = _to_profit_array(remaining)

        if group1.size < 2 or group2.size < 2:
            return result

        # Welch's t-test (등분산 가정하지 않음)
        t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)

        # Cohen's d 효과 크기
        pooled_std = np.sqrt((np.var(group1) + np.var(group2)) / 2)
        if pooled_std > 0:
            effect_size = (np.mean(group1) - np.mean(group2)) / pooled_std
        else:
            effect_size = 0

        # 95% 신뢰구간 (평균 차이에 대한)
        mean_diff = np.mean(group1) - np.mean(group2)
        se = np.sqrt(np.var(group1)/len(group1) + np.var(group2)/len(group2))
        ci_low = mean_diff - 1.96 * se
        ci_high = mean_diff + 1.96 * se

        result = {
            't_stat': round(t_stat, 3),
            'p_value': round(p_value, 4),
            'effect_size': round(effect_size, 3),
            'confidence_interval': (round(ci_low, 0), round(ci_high, 0)),
            'significant': p_value < 0.05
        }
    except:
        pass

    return result


def CalculateEffectSizeInterpretation(effect_size):
    """
    Cohen's d 효과 크기를 해석합니다.

    Returns:
        str: 효과 크기 해석 (작음/중간/큼/매우큼)
    """
    abs_effect = abs(effect_size)
    if abs_effect < 0.2:
        return '무시'
    elif abs_effect < 0.5:
        return '작음'
    elif abs_effect < 0.8:
        return '중간'
    elif abs_effect < 1.2:
        return '큼'
    else:
        return '매우큼'


def DetectTimeframe(df_tsg, save_file_name=''):
    """
    백테스팅 데이터의 타임프레임(Tick/Min)을 자동 감지합니다.

    Args:
        df_tsg: 백테스팅 결과 DataFrame
        save_file_name: 저장 파일명 (선택적)

    Returns:
        dict: 타임프레임 정보
            - timeframe: 'tick' 또는 'min'
            - scale_factor: 스케일 조정 계수
            - time_unit: 시간 단위 ('초' 또는 '분')
            - holding_bins: 보유시간 bins
            - holding_labels: 보유시간 라벨
            - label: 표시용 라벨
    """
    # 파일명에서 감지
    name_lower = save_file_name.lower()
    if 'tick' in name_lower or '_t_' in name_lower:
        timeframe = 'tick'
    elif 'min' in name_lower or '_m_' in name_lower:
        timeframe = 'min'
    else:
        # 인덱스 형식에서 감지 (YYYYMMDDHHMMSS vs YYYYMMDDHHMM)
        try:
            first_idx = str(df_tsg.index[0])
            if len(first_idx) >= 14:  # 초까지 있으면 Tick
                timeframe = 'tick'
            else:
                timeframe = 'min'
        except:
            timeframe = 'tick'  # 기본값

    # 스케일 조정
    if timeframe == 'tick':
        return {
            'timeframe': 'tick',
            'scale_factor': 1,
            'time_unit': '초',
            'holding_bins': [0, 30, 60, 120, 300, 600, 1200, 3600],
            'holding_labels': ['~30초', '30-60초', '1-2분', '2-5분',
                              '5-10분', '10-20분', '20분+'],
            'label': 'Tick 데이터'
        }
    else:
        return {
            'timeframe': 'min',
            'scale_factor': 60,
            'time_unit': '분',
            'holding_bins': [0, 1, 3, 5, 10, 30, 60, 1440],
            'holding_labels': ['~1분', '1-3분', '3-5분', '5-10분',
                              '10-30분', '30-60분', '1시간+'],
            'label': 'Min 데이터'
        }


def CreateSynergyHeatmapData(filter_combinations, top_n=10):
    """
    필터 조합 분석 결과를 히트맵용 데이터로 변환합니다.

    Args:
        filter_combinations: 필터 조합 분석 결과 리스트
        top_n: 표시할 필터 수

    Returns:
        tuple: (filter_names, heatmap_matrix, annotations)
    """
    if not filter_combinations or len(filter_combinations) == 0:
        return None, None, None

    # 2개 조합만 추출
    two_combos = [c for c in filter_combinations if c['조합유형'] == '2개 조합']

    if len(two_combos) == 0:
        return None, None, None

    # 사용된 필터 목록 추출
    filter_set = set()
    for combo in two_combos[:30]:
        filter_set.add(combo['필터1'])
        filter_set.add(combo['필터2'])

    filter_names = sorted(list(filter_set))[:top_n]
    n = len(filter_names)

    if n < 2:
        return None, None, None

    # 히트맵 매트릭스 초기화
    heatmap_matrix = np.zeros((n, n))
    annotations = [['' for _ in range(n)] for _ in range(n)]

    # 조합 정보 채우기
    for combo in two_combos:
        f1, f2 = combo['필터1'], combo['필터2']
        if f1 in filter_names and f2 in filter_names:
            i, j = filter_names.index(f1), filter_names.index(f2)
            synergy = combo['시너지비율']
            heatmap_matrix[i, j] = synergy
            heatmap_matrix[j, i] = synergy  # 대칭

            # 주석 (시너지 효과 금액)
            synergy_effect = combo['시너지효과']
            if synergy_effect >= 0:
                annotations[i][j] = f'+{synergy_effect/1000000:.1f}M'
            else:
                annotations[i][j] = f'{synergy_effect/1000000:.1f}M'
            annotations[j][i] = annotations[i][j]

    # 필터명 축약
    short_names = [name[:15] for name in filter_names]

    return short_names, heatmap_matrix, annotations


def PrepareThresholdCurveData(optimal_thresholds, top_n=5):
    """
    최적 임계값 탐색 결과에서 효율성 곡선용 데이터를 준비합니다.

    Args:
        optimal_thresholds: 최적 임계값 분석 결과 리스트
        top_n: 표시할 컬럼 수

    Returns:
        list: 각 컬럼별 곡선 데이터 리스트
    """
    if not optimal_thresholds or len(optimal_thresholds) == 0:
        return []

    curve_data = []

    for i, opt in enumerate(optimal_thresholds[:top_n]):
        try:
            column = opt['column']
            direction = opt['direction']
            all_thresholds = opt.get('all_thresholds', [])

            if not all_thresholds or not isinstance(all_thresholds, list):
                continue

            # 데이터 추출
            thresholds = [t['threshold'] for t in all_thresholds]
            improvements = [t['improvement'] for t in all_thresholds]
            efficiencies = [t['efficiency'] for t in all_thresholds]
            excluded_ratios = [t['excluded_ratio'] for t in all_thresholds]

            curve_data.append({
                'column': column,
                'direction': direction,
                'thresholds': thresholds,
                'improvements': improvements,
                'efficiencies': efficiencies,
                'excluded_ratios': excluded_ratios,
                'optimal_threshold': opt['optimal_threshold'],
                'optimal_improvement': opt['improvement'],
                'filter_name': opt.get('필터명', f'{column} 필터')
            })
        except:
            continue

    return curve_data


def _FindNearestIndex(values, target):
    try:
        arr = np.asarray(values, dtype=float)
        tgt = float(target)
        return int(np.nanargmin(np.abs(arr - tgt)))
    except Exception:
        return 0


# ============================================================================
# 2. 강화된 파생 지표 계산
# ============================================================================

def CalculateEnhancedDerivedMetrics(df_tsg):
    """
    강화된 파생 지표를 계산합니다.

    기존 지표 + 추가 지표:
    - 모멘텀 지표
    - 변동성 지표
    - 연속 손익 패턴
    - 리스크 조정 수익률
    - 시장 타이밍 점수

    Args:
        df_tsg: 백테스팅 결과 DataFrame

    Returns:
        DataFrame: 강화된 파생 지표가 추가된 DataFrame
    """
    df = df_tsg.copy()

    # 기존 매도 시점 컬럼 확인
    sell_columns = ['매도등락율', '매도체결강도', '매도당일거래대금', '매도전일비', '매도회전율', '매도호가잔량비']
    has_sell_data = all(col in df.columns for col in sell_columns)

    if has_sell_data:
        # === 1. 변화량 지표 (매도 - 매수) ===
        df['등락율변화'] = df['매도등락율'] - df['매수등락율']
        df['체결강도변화'] = df['매도체결강도'] - df['매수체결강도']
        df['전일비변화'] = df['매도전일비'] - df['매수전일비']
        df['회전율변화'] = df['매도회전율'] - df['매수회전율']
        df['호가잔량비변화'] = df['매도호가잔량비'] - df['매수호가잔량비']

        # === 2. 변화율 지표 (매도 / 매수) ===
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

        # === 3. 추세 판단 지표 ===
        df['등락추세'] = df['등락율변화'].apply(lambda x: '상승' if x > 0 else ('하락' if x < 0 else '유지'))
        df['체결강도추세'] = df['체결강도변화'].apply(lambda x: '강화' if x > 10 else ('약화' if x < -10 else '유지'))
        df['거래량추세'] = df['거래대금변화율'].apply(lambda x: '증가' if x > 1.2 else ('감소' if x < 0.8 else '유지'))

        # === 4. 위험 신호 지표 ===
        df['급락신호'] = (df['등락율변화'] < -3) & (df['체결강도변화'] < -20)
        df['매도세증가'] = df['호가잔량비변화'] < -0.2
        df['거래량급감'] = df['거래대금변화율'] < 0.5

        # === 5. 매수/매도 위험도 점수 (0-100, 사후 진단용) ===
        # - 매도 시점 확정 정보(매도-매수 변화량 등)를 포함하는 위험도 점수입니다.
        # - "매수 진입 필터"로 쓰면 룩어헤드가 되므로, 비교/진단 차트용으로만 사용합니다.
        df['매수매도위험도점수'] = 0
        df.loc[df['등락율변화'] < -2, '매수매도위험도점수'] += 15
        df.loc[df['등락율변화'] < -5, '매수매도위험도점수'] += 10  # 추가 가중치
        df.loc[df['체결강도변화'] < -15, '매수매도위험도점수'] += 15
        df.loc[df['체결강도변화'] < -30, '매수매도위험도점수'] += 10  # 추가 가중치
        df.loc[df['호가잔량비변화'] < -0.3, '매수매도위험도점수'] += 15
        df.loc[df['거래대금변화율'] < 0.6, '매수매도위험도점수'] += 15
        if '매수등락율' in df.columns:
            df.loc[df['매수등락율'] > 20, '매수매도위험도점수'] += 10
            df.loc[df['매수등락율'] > 25, '매수매도위험도점수'] += 10  # 추가 가중치
        df['매수매도위험도점수'] = df['매수매도위험도점수'].clip(0, 100)

    # === 6. 모멘텀 점수 (NEW) ===
    if '매수등락율' in df.columns and '매수체결강도' in df.columns:
        # 등락율과 체결강도를 정규화하여 모멘텀 점수 계산
        등락율_norm = (df['매수등락율'] - df['매수등락율'].mean()) / (df['매수등락율'].std() + 0.001)
        체결강도_norm = (df['매수체결강도'] - 100) / 50  # 100을 기준으로 정규화
        df['모멘텀점수'] = round((등락율_norm * 0.4 + 체결강도_norm * 0.6) * 10, 2)

    # === 7. 변동성 지표 (NEW) ===
    if '매수고가' in df.columns and '매수저가' in df.columns:
        df['매수변동폭'] = df['매수고가'] - df['매수저가']
        df['매수변동폭비율'] = np.where(
            df['매수저가'] > 0,
            (df['매수고가'] - df['매수저가']) / df['매수저가'] * 100,
            0
        )

    if has_sell_data and '매도고가' in df.columns:
        df['매도변동폭비율'] = np.where(
            df['매도저가'] > 0,
            (df['매도고가'] - df['매도저가']) / df['매도저가'] * 100,
            0
        )
        df['변동성변화'] = df['매도변동폭비율'] - df['매수변동폭비율']

    # === 7.5. 매수 시점 위험도 점수 (0-100, LOOKAHEAD-FREE) ===
    # - 필터 분석은 "매수를 안 하는 조건(진입 회피)"을 찾는 것이므로,
    #   매도 시점 정보(매도등락율/변화량/보유시간 등)를 사용하면 룩어헤드가 됩니다.
    # - 위험도점수는 매수 시점에서 알 수 있는 정보만으로 계산합니다.
    df['위험도점수'] = 0

    # 1) 과열(추격 매수) 위험: 매수등락율
    if '매수등락율' in df.columns:
        buy_ret = pd.to_numeric(df['매수등락율'], errors='coerce')
        df.loc[buy_ret >= 20, '위험도점수'] += 20
        df.loc[buy_ret >= 25, '위험도점수'] += 10
        df.loc[buy_ret >= 30, '위험도점수'] += 10

    # 2) 매수체결강도 약세 위험
    if '매수체결강도' in df.columns:
        buy_power = pd.to_numeric(df['매수체결강도'], errors='coerce')
        df.loc[buy_power < 80, '위험도점수'] += 15
        df.loc[buy_power < 60, '위험도점수'] += 10
        # 과열(초고 체결강도)도 손실로 이어지는 경우가 있어 별도 가중(룩어헤드 없음)
        df.loc[buy_power >= 150, '위험도점수'] += 10
        df.loc[buy_power >= 200, '위험도점수'] += 10
        df.loc[buy_power >= 250, '위험도점수'] += 10

    # 3) 유동성 위험: 매수당일거래대금 (원본 단위가 '백만' 또는 '억' 혼재 가능)
    if '매수당일거래대금' in df.columns:
        trade_money_raw = pd.to_numeric(df['매수당일거래대금'], errors='coerce')
        # STOM: 당일거래대금 단위 = 백만 → 억 환산(÷100)
        trade_money_eok = trade_money_raw / 100.0
        df.loc[trade_money_eok < 50, '위험도점수'] += 15
        df.loc[trade_money_eok < 100, '위험도점수'] += 10

    # 4) 소형주 위험: 시가총액(억)
    if '시가총액' in df.columns:
        mcap = pd.to_numeric(df['시가총액'], errors='coerce')
        df.loc[mcap < 1000, '위험도점수'] += 15
        df.loc[mcap < 5000, '위험도점수'] += 10

    # 5) 매도우위(호가) 위험: 매수호가잔량비
    if '매수호가잔량비' in df.columns:
        hoga = pd.to_numeric(df['매수호가잔량비'], errors='coerce')
        df.loc[hoga < 90, '위험도점수'] += 10
        df.loc[hoga < 70, '위험도점수'] += 15

    # 6) 슬리피지/비유동 위험: 매수스프레드(%)
    if '매수스프레드' in df.columns:
        spread = pd.to_numeric(df['매수스프레드'], errors='coerce')
        df.loc[spread >= 0.5, '위험도점수'] += 10
        df.loc[spread >= 1.0, '위험도점수'] += 10

    # 6.5) 유동성(회전율) 기반 위험도(룩어헤드 없음)
    if '매수회전율' in df.columns:
        turn = pd.to_numeric(df['매수회전율'], errors='coerce')
        df.loc[turn < 10, '위험도점수'] += 5
        df.loc[turn < 5, '위험도점수'] += 10

    # 7) 변동성 위험: 매수변동폭비율(%)
    if '매수변동폭비율' in df.columns:
        vol_pct = pd.to_numeric(df['매수변동폭비율'], errors='coerce')
        df.loc[vol_pct >= 7.5, '위험도점수'] += 10
        df.loc[vol_pct >= 10, '위험도점수'] += 10
        df.loc[vol_pct >= 15, '위험도점수'] += 10

    df['위험도점수'] = df['위험도점수'].clip(0, 100)

    # === 8. 시장 타이밍 점수 (NEW) ===
    if '매수시' in df.columns:
        # 시간대별 평균 수익률을 기반으로 타이밍 점수 계산
        hour_profit = df.groupby('매수시')['수익률'].mean()
        df['시간대평균수익률'] = df['매수시'].map(hour_profit)
        df['타이밍점수'] = round((df['시간대평균수익률'] - df['시간대평균수익률'].mean()) /
                               (df['시간대평균수익률'].std() + 0.001) * 10, 2)

    # === 9. 연속 손익 패턴 (NEW) ===
    df['이익여부'] = (df['수익금'] > 0).astype(int)
    df['연속이익'] = 0
    df['연속손실'] = 0

    consecutive_win = 0
    consecutive_loss = 0
    for i in range(len(df)):
        if df.iloc[i]['이익여부'] == 1:
            consecutive_win += 1
            consecutive_loss = 0
        else:
            consecutive_loss += 1
            consecutive_win = 0
        df.iloc[i, df.columns.get_loc('연속이익')] = consecutive_win
        df.iloc[i, df.columns.get_loc('연속손실')] = consecutive_loss

    # === 10. 리스크 조정 점수 (NEW) ===
    if '매수등락율' in df.columns and '보유시간' in df.columns:
        # 수익률 / (위험 요소들의 가중 합)
        risk_factor = (df['매수등락율'].abs() / 10 +
                       df['보유시간'] / 300 +
                       1)  # 최소값 보장
        df['리스크조정수익률'] = round(df['수익률'] / risk_factor, 4)

    # === 11. 스프레드 영향도 (NEW) ===
    if '매수스프레드' in df.columns:
        df['스프레드영향'] = np.where(
            df['매수스프레드'] > 0.5, '높음',
            np.where(df['매수스프레드'] > 0.2, '중간', '낮음')
        )

    # === 12. 거래 품질 점수 (NEW) - 종합 점수 ===
    df['거래품질점수'] = 50  # 기본값

    # 긍정적 요소 가산
    if '매수체결강도' in df.columns:
        df.loc[df['매수체결강도'] >= 120, '거래품질점수'] += 10
        df.loc[df['매수체결강도'] >= 150, '거래품질점수'] += 10

    if '매수호가잔량비' in df.columns:
        df.loc[df['매수호가잔량비'] >= 100, '거래품질점수'] += 10

    if '시가총액' in df.columns:
        df.loc[(df['시가총액'] >= 1000) & (df['시가총액'] <= 10000), '거래품질점수'] += 10

    # 부정적 요소 감산
    if '매수등락율' in df.columns:
        df.loc[df['매수등락율'] >= 25, '거래품질점수'] -= 15
        df.loc[df['매수등락율'] >= 30, '거래품질점수'] -= 10

    if '매수스프레드' in df.columns:
        df.loc[df['매수스프레드'] >= 0.5, '거래품질점수'] -= 10

    df['거래품질점수'] = df['거래품질점수'].clip(0, 100)

    # === 13. 지표 조합 비율 (NEW 2025-12-14) ===
    # 조건식에서 사용하는 주요 지표 조합을 파생 지표로 추가

    # 13.1 초당매수수량 / 매도총잔량 비율 (매수세 강도)
    if '매수초당매수수량' in df.columns and '매수매도총잔량' in df.columns:
        df['초당매수수량_매도총잔량_비율'] = np.where(
            df['매수매도총잔량'] > 0,
            df['매수초당매수수량'] / df['매수매도총잔량'] * 100,
            0
        )

    # 13.2 매도총잔량 / 매수총잔량 비율 (호가 불균형 - 매도 우위)
    if '매수매도총잔량' in df.columns and '매수매수총잔량' in df.columns:
        df['매도잔량_매수잔량_비율'] = np.where(
            df['매수매수총잔량'] > 0,
            df['매수매도총잔량'] / df['매수매수총잔량'],
            0
        )

    # 13.3 매수총잔량 / 매도총잔량 비율 (호가 불균형 - 매수 우위)
    if '매수매수총잔량' in df.columns and '매수매도총잔량' in df.columns:
        df['매수잔량_매도잔량_비율'] = np.where(
            df['매수매도총잔량'] > 0,
            df['매수매수총잔량'] / df['매수매도총잔량'],
            0
        )

    # 13.4 초당매도수량 / 초당매수수량 비율 (매도 압력)
    if '매수초당매도수량' in df.columns and '매수초당매수수량' in df.columns:
        df['초당매도_매수_비율'] = np.where(
            df['매수초당매수수량'] > 0,
            df['매수초당매도수량'] / df['매수초당매수수량'],
            0
        )

    # 13.5 초당매수수량 / 초당매도수량 비율 (매수 압력)
    if '매수초당매수수량' in df.columns and '매수초당매도수량' in df.columns:
        df['초당매수_매도_비율'] = np.where(
            df['매수초당매도수량'] > 0,
            df['매수초당매수수량'] / df['매수초당매도수량'],
            0
        )

    # 13.6 현재가 위치 비율: 매수가 / (고가 - (고가-저가)*factor) 형태
    # 고가 근처에서 거래 중인지 확인 (저가 대비 현재가 위치)
    if '매수가' in df.columns and '매수고가' in df.columns and '매수저가' in df.columns:
        price_range = df['매수고가'] - df['매수저가']
        df['현재가_고저범위_위치'] = np.where(
            price_range > 0,
            (df['매수가'] - df['매수저가']) / price_range * 100,
            50  # 범위가 0이면 중간값
        )

    # 13.7 초당거래대금 관련 지표 (거래 강도)
    if '매수초당거래대금' in df.columns and '매수당일거래대금' in df.columns:
        # 초당거래대금 비중 (당일거래대금 대비)
        df['초당거래대금_당일비중'] = np.where(
            df['매수당일거래대금'] > 0,
            df['매수초당거래대금'] / df['매수당일거래대금'] * 10000,  # 만분율
            0
        )

    # 13.8 초당순매수금액 (초당매수수량 - 초당매도수량) * 현재가
    if '매수초당매수수량' in df.columns and '매수초당매도수량' in df.columns and '매수가' in df.columns:
        df['초당순매수수량'] = df['매수초당매수수량'] - df['매수초당매도수량']
        df['초당순매수금액'] = df['초당순매수수량'] * df['매수가'] / 1_000_000  # 백만원 단위

    # 13.9 초당매수수량 / 초당매도수량 순매수 비율 (0~200 범위로 정규화)
    if '매수초당매수수량' in df.columns and '매수초당매도수량' in df.columns:
        total_volume = df['매수초당매수수량'] + df['매수초당매도수량']
        df['초당순매수비율'] = np.where(
            total_volume > 0,
            df['매수초당매수수량'] / total_volume * 100,
            50  # 거래 없으면 중립
        )

    # === 14. 매도 시점 지표 조합 (NEW 2025-12-14) ===
    # 매도 시점에서의 지표 변화도 분석에 활용

    # 14.1 매도 시점 초당매수/매도 비율
    if '매도초당매수수량' in df.columns and '매도초당매도수량' in df.columns:
        df['매도시_초당매수_매도_비율'] = np.where(
            df['매도초당매도수량'] > 0,
            df['매도초당매수수량'] / df['매도초당매도수량'],
            0
        )

    # 14.2 초당 지표 변화 (매도 - 매수)
    if '매수초당매수수량' in df.columns and '매도초당매수수량' in df.columns:
        df['초당매수수량변화'] = df['매도초당매수수량'] - df['매수초당매수수량']

    if '매수초당매도수량' in df.columns and '매도초당매도수량' in df.columns:
        df['초당매도수량변화'] = df['매도초당매도수량'] - df['매수초당매도수량']

    if '매수초당거래대금' in df.columns and '매도초당거래대금' in df.columns:
        df['초당거래대금변화'] = df['매도초당거래대금'] - df['매수초당거래대금']
        df['초당거래대금변화율'] = np.where(
            df['매수초당거래대금'] > 0,
            df['매도초당거래대금'] / df['매수초당거래대금'],
            1.0
        )

    return df


# ============================================================================
# 3. 동적 최적 임계값 탐색
# ============================================================================

def FindOptimalThresholds(df_tsg, column, direction='less', n_splits=20):
    """
    특정 컬럼에 대해 최적의 필터 임계값을 탐색합니다.

    Args:
        df_tsg: DataFrame
        column: 분석할 컬럼명
        direction: 'less' (미만 제외) 또는 'greater' (이상 제외)
        n_splits: 분할 수

    Returns:
        dict: 최적 임계값 정보
            - optimal_threshold: 최적 임계값
            - improvement: 수익 개선 금액
            - excluded_ratio: 제외 비율
            - all_thresholds: 모든 임계값 결과
    """
    if column not in df_tsg.columns:
        return None

    values = df_tsg[column].dropna()
    if len(values) < 10:
        return None

    # 분위수 기반 임계값 생성
    percentiles = np.linspace(5, 95, n_splits)
    thresholds = np.percentile(values, percentiles)

    results = []
    total_profit = df_tsg['수익금'].sum()
    total_trades = len(df_tsg)
    profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)
    col_arr = df_tsg[column].to_numpy(dtype=np.float64)

    for threshold in thresholds:
        if direction == 'less':
            condition = col_arr < threshold
        else:
            condition = col_arr >= threshold

        excluded_count = int(np.sum(condition))
        remaining_count = total_trades - excluded_count
        if excluded_count == 0 or remaining_count == 0:
            continue

        excluded_profit = float(np.sum(profit_arr[condition]))
        improvement = -excluded_profit
        excluded_ratio = excluded_count / total_trades * 100
        remaining_winrate = (profit_arr[~condition] > 0).mean() * 100

        # 효율성 점수: 수익개선 / 제외거래수 (제외 거래당 개선 효과)
        efficiency = improvement / excluded_count if excluded_count > 0 else 0

        results.append({
            'threshold': round(threshold, 2),
            'improvement': int(improvement),
            'excluded_ratio': round(excluded_ratio, 1),
            'excluded_count': excluded_count,
            'remaining_count': remaining_count,
            'remaining_winrate': round(remaining_winrate, 1),
            'efficiency': round(efficiency, 0)
        })

    if not results:
        return None

    # 최적 임계값 선택 (수익개선 × 효율성 가중)
    df_results = pd.DataFrame(results)

    # 제외 비율이 너무 큰 경우(거의 거래를 안 하는 케이스)는 과적합/왜곡 위험이 커서 제한
    # - 기존 50% 제한은 "좋은 구간만 남기는" 범위 필터를 놓치는 경우가 있어 80%로 완화
    df_valid = df_results[df_results['excluded_ratio'] <= 80]

    if len(df_valid) == 0:
        return None

    # 수익개선이 양수인 것 중 효율성이 가장 높은 것
    df_positive = df_valid[df_valid['improvement'] > 0]

    if len(df_positive) > 0:
        best_idx = df_positive['efficiency'].idxmax()
        best = df_positive.loc[best_idx]
    else:
        best = df_valid.loc[df_valid['improvement'].idxmax()]

    return {
        'column': column,
        'direction': direction,
        'optimal_threshold': best['threshold'],
        'improvement': best['improvement'],
        'excluded_ratio': best['excluded_ratio'],
        'excluded_count': best['excluded_count'],
        'remaining_winrate': best['remaining_winrate'],
        'efficiency': best['efficiency'],
        'all_thresholds': results
    }


def FindOptimalRangeThresholds(df_tsg, column, mode='outside', n_bins=10, max_excluded_ratio=80):
    """
    특정 컬럼에 대해 "범위(구간)" 기반 필터를 탐색합니다.

    mode:
        - 'outside': 범위 밖 제외(= 범위 안에서만 매수)  → excluded = (x < low) or (x >= high)
        - 'inside' : 범위 안 제외(= 특정 구간만 회피)     → excluded = (low <= x < high)
    """
    if column not in df_tsg.columns:
        return None

    try:
        s = df_tsg[column]
        if not pd.api.types.is_numeric_dtype(s):
            return None
        values = s.dropna().to_numpy(dtype=np.float64)
    except Exception:
        return None

    if len(values) < 50:
        return None

    # 분위수 기반 경계값 생성(중복 제거)
    percentiles = np.linspace(0, 100, n_bins + 1)
    try:
        edges = np.nanpercentile(values, percentiles)
        edges = np.unique(edges)
    except Exception:
        return None

    if len(edges) < 4:
        return None

    # 전체 배열(NaN 포함)로 bin index 생성
    col_arr = df_tsg[column].to_numpy(dtype=np.float64)
    profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)
    total_profit = float(np.nansum(profit_arr))
    total_trades = int(len(col_arr))

    # NaN은 bin=-1로 처리
    valid_mask = np.isfinite(col_arr)
    valid_vals = col_arr[valid_mask]
    if len(valid_vals) == 0:
        return None

    # bin: 0..k-2 (edges 길이 k)
    # bins: [edges[i], edges[i+1]) 형태로 맞추기 위해 side='right'를 사용(경계값은 상위 bin으로)
    bin_idx = np.searchsorted(edges[1:-1], valid_vals, side='right')
    bin_count = int(len(edges) - 1)
    counts = np.bincount(bin_idx, minlength=bin_count).astype(np.int64)
    profit_sums = np.bincount(bin_idx, weights=profit_arr[valid_mask], minlength=bin_count).astype(np.float64)
    win_counts = np.bincount(bin_idx, weights=(profit_arr[valid_mask] > 0).astype(np.int64), minlength=bin_count).astype(np.int64)

    # prefix sums for O(k^2) interval evaluation
    pc = np.concatenate(([0], np.cumsum(counts)))
    pp = np.concatenate(([0.0], np.cumsum(profit_sums)))
    pw = np.concatenate(([0], np.cumsum(win_counts)))

    best = None
    k = bin_count

    for i in range(k):
        for j in range(i, k):
            low = float(edges[i])
            high = float(edges[j + 1]) if (j + 1) < len(edges) else float(edges[-1])
            if not np.isfinite(low) or not np.isfinite(high) or high <= low:
                continue

            in_count = int(pc[j + 1] - pc[i])
            if in_count <= 0:
                continue

            in_profit = float(pp[j + 1] - pp[i])
            in_wins = int(pw[j + 1] - pw[i])

            if mode == 'inside':
                excluded_count = in_count
                excluded_profit = in_profit
                remaining_count = total_trades - excluded_count
                remaining_wins = int(np.sum(profit_arr > 0)) - in_wins
            else:
                # outside
                excluded_count = total_trades - in_count
                excluded_profit = total_profit - in_profit
                remaining_count = in_count
                remaining_wins = in_wins

            if excluded_count <= 0 or remaining_count <= 0:
                continue

            excluded_ratio = excluded_count / total_trades * 100
            if excluded_ratio > max_excluded_ratio:
                continue

            improvement = -excluded_profit
            if improvement <= 0:
                continue

            remaining_winrate = (remaining_wins / remaining_count * 100.0) if remaining_count > 0 else 0.0
            efficiency = improvement / excluded_count if excluded_count > 0 else 0.0

            candidate = {
                'column': column,
                'direction': 'range',
                'mode': mode,
                'low': round(low, 6),
                'high': round(high, 6),
                'improvement': int(improvement),
                'excluded_ratio': round(excluded_ratio, 1),
                'excluded_count': int(excluded_count),
                'remaining_winrate': round(remaining_winrate, 1),
                'efficiency': round(efficiency, 0),
            }

            if best is None:
                best = candidate
                continue

            # 우선순위: 효율성 → 개선금액(동률 시)
            if candidate['efficiency'] > best.get('efficiency', 0):
                best = candidate
            elif candidate['efficiency'] == best.get('efficiency', 0) and candidate['improvement'] > best.get('improvement', 0):
                best = candidate

    return best


def FindAllOptimalThresholds(df_tsg):
    """
    모든 주요 컬럼에 대해 최적 임계값을 탐색합니다.

    Returns:
        list: 각 컬럼별 최적 임계값 정보
    """
    results = []

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

    def _detect_trade_money_unit(series):
        # STOM: 당일거래대금 단위는 "백만"으로 고정(요구사항).
        return '백만'

    trade_money_unit = None
    if '매수당일거래대금' in df_tsg.columns:
        trade_money_unit = _detect_trade_money_unit(df_tsg['매수당일거래대금'])

    # 분석할 컬럼과 방향 정의
    columns_config = [
        ('매수등락율', 'greater', '매수등락율 {:.0f}% 이상 제외'),
        ('매수등락율', 'less', '매수등락율 {:.0f}% 미만 제외'),
        ('매수체결강도', 'less', '매수체결강도 {:.0f} 미만 제외'),
        ('매수체결강도', 'greater', '매수체결강도 {:.0f} 이상 제외'),
        ('매수당일거래대금', 'less', '매수당일거래대금 {:.0f}억 미만 제외'),
        ('시가총액', 'less', '매수시가총액 {:.0f}억 미만 제외'),
        ('시가총액', 'greater', '매수시가총액 {:.0f}억 이상 제외'),
        ('매수호가잔량비', 'less', '매수호가잔량비 {:.0f}% 미만 제외'),
        ('매수스프레드', 'greater', '매수스프레드 {:.2f}% 이상 제외'),
    ]

    # 파생 지표도 분석
    if '위험도점수' in df_tsg.columns:
        columns_config.append(('위험도점수', 'greater', '매수위험도 {:.0f}점 이상 제외'))

    if '거래품질점수' in df_tsg.columns:
        columns_config.append(('거래품질점수', 'less', '거래품질(매수) {:.0f}점 미만 제외'))

    if '모멘텀점수' in df_tsg.columns:
        columns_config.append(('모멘텀점수', 'less', '모멘텀(매수) {:.1f} 미만 제외'))

    for column, direction, name_template in columns_config:
        result = FindOptimalThresholds(df_tsg, column, direction)
        if result and result['improvement'] > 0:
            raw_thr = result.get('optimal_threshold')
            result['임계값(원본)'] = raw_thr

            # 표시용 라벨 정리(단위/스케일 혼동 방지)
            if column == '매수당일거래대금':
                unit = trade_money_unit or '백만'
                try:
                    thr_eok = float(raw_thr) / 100.0 if unit == '백만' else float(raw_thr)
                except Exception:
                    thr_eok = raw_thr
                result['임계값(표시)'] = _fmt_eok_to_korean(thr_eok)
                result['원본단위'] = unit
                result['필터명'] = f"매수당일거래대금 {result['임계값(표시)']} 미만 제외"
            elif column == '시가총액':
                try:
                    thr_eok = float(raw_thr)
                except Exception:
                    thr_eok = raw_thr
                result['임계값(표시)'] = _fmt_eok_to_korean(thr_eok)
                suffix = '미만 제외' if direction == 'less' else '이상 제외'
                result['필터명'] = f"매수시가총액 {result['임계값(표시)']} {suffix}"
            else:
                result['필터명'] = name_template.format(raw_thr)
            results.append(result)

    # 수익 개선금액 기준 정렬
    results.sort(key=lambda x: x['improvement'], reverse=True)

    return results


# ============================================================================
# 4. 필터 조합 분석
# ============================================================================

def AnalyzeFilterCombinations(df_tsg, single_filters=None, max_filters=3, top_n=10):
    """
    필터 조합의 시너지 효과를 분석합니다.

    Args:
        df_tsg: DataFrame
        max_filters: 최대 조합 필터 수 (2 또는 3)
        top_n: 분석할 상위 단일 필터 수

    Returns:
        list: 필터 조합 분석 결과
    """
    # 먼저 단일 필터 분석(이미 계산된 결과가 있으면 재사용)
    if single_filters is None:
        single_filters = AnalyzeFilterEffectsEnhanced(df_tsg)

    if not single_filters:
        return []

    # 상위 필터만 조합 분석 (계산량 제한)
    top_filters = [f for f in single_filters if f['수익개선금액'] > 0][:top_n]

    if len(top_filters) < 2:
        return []

    total_trades = len(df_tsg)
    profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)

    # 조건식은 조합 루프에서 반복 eval 되면 비용이 커서, 상위 필터에 대해서만 미리 평가해둡니다.
    safe_globals = {"__builtins__": {}}
    safe_locals = {"df_tsg": df_tsg, "np": np, "pd": pd}
    cond_arrays = []
    for f in top_filters:
        try:
            cond_expr = f.get('조건식')
            if not cond_expr:
                cond_arrays.append(None)
                continue
            cond = eval(cond_expr, safe_globals, safe_locals)
            cond_arr = cond.to_numpy(dtype=bool) if hasattr(cond, 'to_numpy') else np.asarray(cond, dtype=bool)
            cond_arrays.append(cond_arr)
        except:
            cond_arrays.append(None)

    combination_results = []

    # 2개 필터 조합
    for f1, f2 in combinations(range(len(top_filters)), 2):
        filter1 = top_filters[f1]
        filter2 = top_filters[f2]

        try:
            cond1 = cond_arrays[f1]
            cond2 = cond_arrays[f2]
            if cond1 is None or cond2 is None:
                continue

            combined_condition = cond1 | cond2  # OR 조건 (둘 중 하나라도 해당되면 제외)
            excluded_count = int(np.sum(combined_condition))
            remaining_count = total_trades - excluded_count
            if excluded_count == 0 or remaining_count == 0:
                continue

            improvement = -float(np.sum(profit_arr[combined_condition]))
            excluded_ratio = excluded_count / total_trades * 100

            # 시너지 효과 계산 (조합 개선 - 개별 개선 합)
            individual_sum = filter1['수익개선금액'] + filter2['수익개선금액']
            synergy = improvement - individual_sum
            synergy_ratio = synergy / individual_sum * 100 if individual_sum > 0 else 0

            combination_results.append({
                '조합유형': '2개 조합',
                '필터1': filter1['필터명'],
                '필터2': filter2['필터명'],
                '필터3': '',
                '개별개선합': int(individual_sum),
                '조합개선': int(improvement),
                '시너지효과': int(synergy),
                '시너지비율': round(synergy_ratio, 1),
                '제외비율': round(excluded_ratio, 1),
                '잔여승률': round((profit_arr[~combined_condition] > 0).mean() * 100, 1),
                '잔여거래수': remaining_count,
                '권장': '★★★' if synergy_ratio > 20 else ('★★' if synergy_ratio > 0 else ''),
            })
        except:
            continue

    # 3개 필터 조합 (상위 5개만)
    if max_filters >= 3 and len(top_filters) >= 3:
        for f1, f2, f3 in combinations(range(min(5, len(top_filters))), 3):
            filter1 = top_filters[f1]
            filter2 = top_filters[f2]
            filter3 = top_filters[f3]

            try:
                cond1 = cond_arrays[f1]
                cond2 = cond_arrays[f2]
                cond3 = cond_arrays[f3]
                if cond1 is None or cond2 is None or cond3 is None:
                    continue

                combined_condition = cond1 | cond2 | cond3

                excluded_count = int(np.sum(combined_condition))
                remaining_count = total_trades - excluded_count
                if excluded_count == 0 or remaining_count == 0:
                    continue

                improvement = -float(np.sum(profit_arr[combined_condition]))
                excluded_ratio = excluded_count / total_trades * 100

                individual_sum = filter1['수익개선금액'] + filter2['수익개선금액'] + filter3['수익개선금액']
                synergy = improvement - individual_sum
                synergy_ratio = synergy / individual_sum * 100 if individual_sum > 0 else 0

                combination_results.append({
                    '조합유형': '3개 조합',
                    '필터1': filter1['필터명'],
                    '필터2': filter2['필터명'],
                    '필터3': filter3['필터명'],
                    '개별개선합': int(individual_sum),
                    '조합개선': int(improvement),
                    '시너지효과': int(synergy),
                    '시너지비율': round(synergy_ratio, 1),
                    '제외비율': round(excluded_ratio, 1),
                    '잔여승률': round((profit_arr[~combined_condition] > 0).mean() * 100, 1),
                    '잔여거래수': remaining_count,
                    '권장': '★★★' if synergy_ratio > 20 else ('★★' if synergy_ratio > 0 else ''),
                })
            except:
                continue

    # 조합 적용 시 개선금액 기준 정렬(내림차순)
    # - "현재 조건식에 불필요한 조건"을 찾기 위해, 최종 개선 효과가 큰 조합을 상단에 배치
    combination_results.sort(
        key=lambda x: (x.get('조합개선', 0), x.get('시너지효과', 0), x.get('시너지비율', 0)),
        reverse=True
    )

    return combination_results


# ============================================================================
# 5. 강화된 필터 효과 분석
# ============================================================================

def AnalyzeFilterEffectsEnhanced(df_tsg, allow_ml_filters: bool = True):
    """
    강화된 필터 효과 분석 (통계적 유의성 + 동적 임계값 포함)

    Args:
        df_tsg: DataFrame
        allow_ml_filters: True면 *_ML 컬럼(손실확률_ML/위험도_ML 등)도 필터 후보로 포함합니다.

    Returns:
        list: 필터 효과 분석 결과 (통계 검정 결과 포함)
    """
    filter_results = []
    total_profit = df_tsg['수익금'].sum()
    total_trades = len(df_tsg)

    if total_trades == 0:
        return filter_results

    profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)
    return_arr = df_tsg['수익률'].to_numpy(dtype=np.float64) if '수익률' in df_tsg.columns else None

    # === 필터 조건 정의 (조건식 포함) ===
    filter_conditions = []

    def _fmt_eok_to_korean(value_eok):
        """
        억 단위 숫자를 사람이 읽기 쉬운 라벨로 변환합니다.
        - 1조(=10,000억) 미만: 억 단위
        - 1조 이상: 조 단위(정수)
        """
        try:
            v = float(value_eok)
        except:
            return str(value_eok)
        if v >= 10000:
            return f"{int(round(v / 10000))}조"
        return f"{int(round(v))}억"

    def _detect_trade_money_unit(series):
        # STOM: 당일거래대금 단위는 "백만"으로 고정(요구사항).
        return '백만'

    # 1. 시간대 필터
    if '매수시' in df_tsg.columns:
        for hour in sorted(df_tsg['매수시'].unique()):
            filter_conditions.append({
                '필터명': f'시간대 {hour}시 제외',
                '조건': df_tsg['매수시'] == hour,
                '조건식': f"df_tsg['매수시'] == {hour}",
                '분류': '시간대',
                '코드': f'매수시 != {hour}'
            })

    # 2. 전 컬럼 스캔: "매수 시점에 알 수 있는 변수" 중심으로 동적 임계값/범위 필터 탐색
    # - 목적: 매수시점 모든 변수(가능한 범위)를 검토하고, 개선 효과가 큰 필터를 추천
    # - 원칙(룩어헤드 방지): 매도* / 변화량(*변화, *변화율) / 보유시간 / 수익결과 기반 컬럼은 제외

    trade_money_unit = _detect_trade_money_unit(df_tsg['매수당일거래대금']) if '매수당일거래대금' in df_tsg.columns else '백만'

    def _fmt_number(v, decimals=2):
        try:
            x = float(v)
        except Exception:
            return str(v)
        if abs(x - round(x)) < 1e-9:
            return f"{int(round(x))}"
        if abs(x) >= 1000:
            return f"{x:,.0f}"
        s = f"{x:.{decimals}f}"
        return s.rstrip('0').rstrip('.')

    def _fmt_trade_money(raw_value):
        # raw_value: df_tsg['매수당일거래대금'] 원본 단위(권장: 백만)
        try:
            rv = float(raw_value)
        except Exception:
            return str(raw_value)
        eok = rv / 100.0 if trade_money_unit == '백만' else rv
        return _fmt_eok_to_korean(eok)

    def _categorize(col: str) -> str:
        if col == '시가총액':
            return '시가총액'
        if '위험도' in col:
            return '위험신호'
        if '품질' in col:
            return '품질'
        if '모멘텀' in col:
            return '모멘텀'
        if '등락' in col:
            return '등락율'
        if '체결강도' in col:
            return '체결강도'
        if '거래대금' in col:
            return '거래대금'
        if '회전율' in col:
            return '회전율'
        if '전일' in col:
            return '전일비'
        if '스프레드' in col:
            return '스프레드'
        if '호가' in col or '잔량' in col:
            return '호가'
        if '초당' in col:
            return '초당'
        return '기타'

    def _is_buytime_candidate(col: str) -> bool:
        # "매도"로 시작하더라도, 매수 시점 호가/잔량에서 파생된 변수는 예외적으로 허용합니다.
        # (예: 매도잔량_매수잔량_비율 = 매수 시점의 매도/매수 잔량 비율)
        allow_sellside_buytime_cols = {
            '매도잔량_매수잔량_비율',
        }
        if col in ('수익금', '수익률', '보유시간', '매수시간', '매도시간', '매수일자', '추가매수시간', '매도조건'):
            return False
        if col.startswith('매도') and col not in allow_sellside_buytime_cols:
            return False
        if col.startswith('수익금'):
            return False
        if col in ('이익금액', '손실금액', '이익여부', '시간대평균수익률', '타이밍점수', '리스크조정수익률',
                   '연속이익', '연속손실', '매수매도위험도점수'):
            return False
        if '매도시' in col:
            return False
        if '변화' in col:
            return False
        # 시간 컬럼은 별도(시간대 필터)로 처리
        if col in ('매수시', '매수분', '매수초'):
            return False
        return True

    candidate_cols = []
    for col in df_tsg.columns:
        col = str(col)
        if (not allow_ml_filters) and col.endswith('_ML'):
            continue
        if not _is_buytime_candidate(col):
            continue
        try:
            if not pd.api.types.is_numeric_dtype(df_tsg[col]):
                continue
        except Exception:
            continue
        candidate_cols.append(col)

    # 컬럼별로 최적 임계값(less/greater) + 범위 필터를 제한적으로 추가
    for col in sorted(candidate_cols):
        try:
            col_series = df_tsg[col]
            if col_series.notna().sum() < 50:
                continue
            if col_series.nunique(dropna=True) < 5:
                continue

            category = _categorize(col)

            # 1) 단일 임계값(미만 제외 / 이상 제외)
            for direction in ('less', 'greater'):
                res = FindOptimalThresholds(df_tsg, col, direction=direction, n_splits=20)
                if not res or res.get('improvement', 0) <= 0:
                    continue

                thr = float(res.get('optimal_threshold'))
                col_arr = col_series.to_numpy(dtype=np.float64)

                if direction == 'less':
                    cond_arr = col_arr < thr
                    cond_expr = f"df_tsg['{col}'] < {round(thr, 6)}"
                    keep_code = f"({col} >= {round(thr, 6)})"
                    suffix = '미만 제외'
                else:
                    cond_arr = col_arr >= thr
                    cond_expr = f"df_tsg['{col}'] >= {round(thr, 6)}"
                    keep_code = f"({col} < {round(thr, 6)})"
                    suffix = '이상 제외'

                if col == '매수당일거래대금':
                    thr_label = _fmt_trade_money(thr)
                    name = f"매수당일거래대금 {thr_label} {suffix}"
                    keep_code = f"{keep_code}  # 단위:{trade_money_unit}(≈{thr_label})"
                elif col == '시가총액':
                    name = f"매수시가총액 {_fmt_eok_to_korean(thr)} {suffix}"
                elif col == '위험도점수':
                    name = f"매수 위험도점수 {thr:.0f}점 {suffix}"
                elif col == '거래품질점수':
                    name = f"거래품질점수 {thr:.0f}점 {suffix}"
                else:
                    name = f"{col} {_fmt_number(thr)} {suffix}"

                filter_conditions.append({
                    '필터명': name,
                    '조건': cond_arr,
                    '조건식': cond_expr,
                    '분류': category,
                    '코드': keep_code,
                    '탐색기반': f"최적임계({direction})",
                })

            # 2) 범위 필터(하한/상한): outside(범위 밖 제외) / inside(구간 제외)
            for mode in ('outside', 'inside'):
                r = FindOptimalRangeThresholds(df_tsg, col, mode=mode, n_bins=10, max_excluded_ratio=80)
                if not r or r.get('improvement', 0) <= 0:
                    continue

                low = float(r['low'])
                high = float(r['high'])
                col_arr = col_series.to_numpy(dtype=np.float64)
                finite = col_arr[np.isfinite(col_arr)]
                if len(finite) == 0:
                    continue
                col_min = float(np.min(finite))
                col_max = float(np.max(finite))
                # 양쪽 경계가 모두 "내부"에 있어야 진짜 범위 필터(= one-sided 중복 방지)
                eps = 1e-12
                if not (low > col_min + eps and high < col_max - eps):
                    continue

                if mode == 'outside':
                    # 범위 밖 제외 → 범위 안에서만 매수
                    cond_arr = (col_arr < low) | (col_arr >= high)
                    cond_expr = f"(df_tsg['{col}'] < {round(low, 6)}) | (df_tsg['{col}'] >= {round(high, 6)})"
                    keep_code = f"(({col} >= {round(low, 6)}) and ({col} < {round(high, 6)}))"
                    suffix = '범위 밖 제외(범위만 매수)'
                else:
                    # 범위 안 제외 → 특정 구간 회피
                    cond_arr = (col_arr >= low) & (col_arr < high)
                    cond_expr = f"(df_tsg['{col}'] >= {round(low, 6)}) & (df_tsg['{col}'] < {round(high, 6)})"
                    keep_code = f"(({col} < {round(low, 6)}) or ({col} >= {round(high, 6)}))"
                    suffix = '구간 제외'

                if col == '매수당일거래대금':
                    lo_label = _fmt_trade_money(low)
                    hi_label = _fmt_trade_money(high)
                    name = f"매수당일거래대금 {lo_label}~{hi_label} {suffix}"
                    keep_code = f"{keep_code}  # 단위:{trade_money_unit}(≈{lo_label}~{hi_label})"
                elif col == '시가총액':
                    name = f"매수시가총액 {_fmt_eok_to_korean(low)}~{_fmt_eok_to_korean(high)} {suffix}"
                elif col == '위험도점수':
                    name = f"매수 위험도점수 {low:.0f}~{high:.0f} {suffix}"
                else:
                    name = f"{col} {_fmt_number(low)}~{_fmt_number(high)} {suffix}"

                filter_conditions.append({
                    '필터명': name,
                    '조건': cond_arr,
                    '조건식': cond_expr,
                    '분류': category,
                    '코드': keep_code,
                    '탐색기반': f"범위({mode})",
                })
        except Exception:
            continue

    # (룩어헤드 제거) 급락신호/매도-매수 변화량 기반 지표는 매도 시점 확정 정보이므로
    # "매수 진입 필터" 추천 대상에서 제외합니다.

    # === 각 필터 효과 계산 (통계 검정 포함) ===
    for fc in filter_conditions:
        try:
            cond = fc['조건']
            cond_arr = cond.to_numpy(dtype=bool) if hasattr(cond, 'to_numpy') else np.asarray(cond, dtype=bool)
            filtered_count = int(np.sum(cond_arr))
            remaining_count = total_trades - filtered_count

            if filtered_count == 0 or remaining_count == 0:
                continue

            filtered_profit = float(np.sum(profit_arr[cond_arr]))
            remaining_profit = float(total_profit - filtered_profit)

            improvement = -filtered_profit

            # 통계적 유의성 검증
            stat_result = CalculateStatisticalSignificance(profit_arr[cond_arr], profit_arr[~cond_arr])
            effect_interpretation = CalculateEffectSizeInterpretation(stat_result['effect_size'])

            # 제외 거래의 특성 분석
            if return_arr is not None:
                filtered_avg_profit = float(np.nanmean(return_arr[cond_arr])) if filtered_count > 0 else 0.0
                remaining_avg_profit = float(np.nanmean(return_arr[~cond_arr])) if remaining_count > 0 else 0.0
            else:
                filtered_avg_profit = 0.0
                remaining_avg_profit = 0.0

            # 권장 등급 (개선된 로직)
            if improvement > total_profit * 0.15 and stat_result['significant']:
                rating = '★★★'
            elif improvement > total_profit * 0.05 and stat_result['p_value'] < 0.1:
                rating = '★★'
            elif improvement > 0:
                rating = '★'
            else:
                rating = ''

            filter_results.append({
                '분류': fc['분류'],
                '필터명': fc['필터명'],
                '조건식': fc['조건식'],
                '적용코드': fc['코드'],
                '제외거래수': filtered_count,
                '제외비율': round(filtered_count / total_trades * 100, 1),
                '제외거래수익금': int(filtered_profit),
                '제외평균수익률': round(filtered_avg_profit, 2),
                '잔여거래수': remaining_count,
                '잔여거래수익금': int(remaining_profit),
                '잔여평균수익률': round(remaining_avg_profit, 2),
                '수익개선금액': int(improvement),
                '제외거래승률': round((profit_arr[cond_arr] > 0).mean() * 100, 1) if filtered_count > 0 else 0.0,
                '잔여거래승률': round((profit_arr[~cond_arr] > 0).mean() * 100, 1) if remaining_count > 0 else 0.0,
                't통계량': stat_result['t_stat'],
                'p값': stat_result['p_value'],
                '효과크기': stat_result['effect_size'],
                '효과해석': effect_interpretation,
                '신뢰구간': stat_result['confidence_interval'],
                '유의함': '예' if stat_result['significant'] else '아니오',
                '적용권장': rating,
            })
        except:
            continue

    # 수익개선금액 기준 정렬
    filter_results.sort(key=lambda x: x['수익개선금액'], reverse=True)

    return filter_results


def AnalyzeFilterEffectsLookahead(df_tsg):
    """
    (진단용) 매도 시점 확정 정보까지 포함한 필터 효과 분석.

    중요:
    - 이 분석은 매도 시점 데이터/변화량/보유시간 등 룩어헤드가 포함될 수 있으므로,
      실거래용 "매수 진입 필터 추천/자동 조건식 생성"에는 사용하지 않습니다.
    - 목적은 '손실 거래에서 사후적으로 어떤 지표가 같이 나왔는지'를 빠르게 파악하기 위함입니다.
    """
    filter_results = []
    if df_tsg is None or len(df_tsg) == 0:
        return filter_results
    if '수익금' not in df_tsg.columns:
        return filter_results

    total_trades = int(len(df_tsg))
    total_profit = float(df_tsg['수익금'].sum())
    profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)
    return_arr = df_tsg['수익률'].to_numpy(dtype=np.float64) if '수익률' in df_tsg.columns else None

    def _fmt_eok_to_korean(value_eok):
        try:
            v = float(value_eok)
        except Exception:
            return str(value_eok)
        if v >= 10000:
            return f"{int(round(v / 10000))}조"
        return f"{int(round(v))}억"

    def _detect_trade_money_unit(series):
        # STOM: 당일거래대금 단위는 "백만"으로 고정(요구사항).
        return '백만'

    trade_money_unit = None
    if '매도당일거래대금' in df_tsg.columns:
        trade_money_unit = _detect_trade_money_unit(df_tsg['매도당일거래대금'])
    elif '매수당일거래대금' in df_tsg.columns:
        trade_money_unit = _detect_trade_money_unit(df_tsg['매수당일거래대금'])
    else:
        trade_money_unit = '백만'

    def _fmt_trade_money(raw_value):
        try:
            rv = float(raw_value)
        except Exception:
            return str(raw_value)
        eok = rv / 100.0 if trade_money_unit == '백만' else rv
        return _fmt_eok_to_korean(eok)

    # 사후 진단용으로 의미 있는 대표 컬럼만 선정(과도한 계산/과적합 방지)
    candidate_cols = [
        # 매도 확정 정보/변화량
        '매수매도위험도점수', '보유시간',
        '등락율변화', '체결강도변화', '거래대금변화율', '체결강도변화율', '호가잔량비변화',
        '급락신호', '매도세증가', '거래량급감',
        # 매도 시점 스냅샷
        '매도등락율', '매도체결강도', '매도당일거래대금', '매도전일비', '매도회전율', '매도호가잔량비', '매도스프레드',
    ]

    filter_conditions = []
    for col in candidate_cols:
        if col not in df_tsg.columns:
            continue
        s = df_tsg[col]

        # bool/flag 컬럼은 True 제외만 검사
        if pd.api.types.is_bool_dtype(s) or str(s.dtype) == 'bool':
            cond_arr = s.to_numpy(dtype=bool)
            excluded_count = int(np.sum(cond_arr))
            if excluded_count == 0 or excluded_count == total_trades:
                continue
            filter_conditions.append({
                '필터명': f"{col} True 제외(사후진단)",
                '조건': cond_arr,
                '조건식': f"df_tsg['{col}'] == True",
                '분류': '사후진단',
                '코드': f"# (진단용) {col} == True 제외",
            })
            continue

        if not pd.api.types.is_numeric_dtype(s):
            continue

        # one-sided 임계값(미만/이상)만(사후진단이므로 단순/빠르게)
        for direction in ('less', 'greater'):
            res = FindOptimalThresholds(df_tsg, col, direction=direction, n_splits=20)
            if not res or res.get('improvement', 0) <= 0:
                continue

            thr = float(res.get('optimal_threshold'))
            col_arr = s.to_numpy(dtype=np.float64)

            if direction == 'less':
                cond_arr = col_arr < thr
                cond_expr = f"df_tsg['{col}'] < {round(thr, 6)}"
                keep_code = f"({col} >= {round(thr, 6)})"
                suffix = '미만 제외'
            else:
                cond_arr = col_arr >= thr
                cond_expr = f"df_tsg['{col}'] >= {round(thr, 6)}"
                keep_code = f"({col} < {round(thr, 6)})"
                suffix = '이상 제외'

            if col in ('매수당일거래대금', '매도당일거래대금'):
                thr_label = _fmt_trade_money(thr)
                name = f"{col} {thr_label} {suffix}(사후진단)"
                keep_code = f"{keep_code}  # 단위:{trade_money_unit}(≈{thr_label})"
            elif col == '시가총액':
                name = f"{col} {_fmt_eok_to_korean(thr)} {suffix}(사후진단)"
            else:
                name = f"{col} {thr:.2f} {suffix}(사후진단)"

            filter_conditions.append({
                '필터명': name,
                '조건': cond_arr,
                '조건식': cond_expr,
                '분류': '사후진단',
                '코드': keep_code,
            })

    for fc in filter_conditions:
        try:
            cond_arr = fc['조건']
            cond_arr = cond_arr.to_numpy(dtype=bool) if hasattr(cond_arr, 'to_numpy') else np.asarray(cond_arr, dtype=bool)
            filtered_count = int(np.sum(cond_arr))
            remaining_count = total_trades - filtered_count
            if filtered_count == 0 or remaining_count == 0:
                continue

            filtered_profit = float(np.sum(profit_arr[cond_arr]))
            remaining_profit = float(total_profit - filtered_profit)
            improvement = -filtered_profit

            # 통계 검정(가능하면 동일 포맷 유지)
            stat_result = CalculateStatisticalSignificance(profit_arr[cond_arr], profit_arr[~cond_arr])
            effect_interpretation = CalculateEffectSizeInterpretation(stat_result['effect_size'])

            if return_arr is not None:
                filtered_avg_profit = float(np.nanmean(return_arr[cond_arr])) if filtered_count > 0 else 0.0
                remaining_avg_profit = float(np.nanmean(return_arr[~cond_arr])) if remaining_count > 0 else 0.0
            else:
                filtered_avg_profit = 0.0
                remaining_avg_profit = 0.0

            filter_results.append({
                '분류': fc.get('분류', '사후진단'),
                '필터명': fc.get('필터명', ''),
                '조건식': fc.get('조건식', ''),
                '적용코드': fc.get('코드', ''),
                '제외거래수': filtered_count,
                '제외비율': round(filtered_count / total_trades * 100, 1),
                '제외거래수익금': int(filtered_profit),
                '제외평균수익률': round(filtered_avg_profit, 2),
                '잔여거래수': remaining_count,
                '잔여거래수익금': int(remaining_profit),
                '잔여평균수익률': round(remaining_avg_profit, 2),
                '수익개선금액': int(improvement),
                '제외거래승률': round((profit_arr[cond_arr] > 0).mean() * 100, 1) if filtered_count > 0 else 0.0,
                '잔여거래승률': round((profit_arr[~cond_arr] > 0).mean() * 100, 1) if remaining_count > 0 else 0.0,
                't통계량': stat_result['t_stat'],
                'p값': stat_result['p_value'],
                '효과크기': stat_result['effect_size'],
                '효과해석': effect_interpretation,
                '신뢰구간': stat_result['confidence_interval'],
                '유의함': '예' if stat_result['significant'] else '아니오',
                '적용권장': '※진단용(룩어헤드)',
            })
        except Exception:
            continue

    filter_results.sort(key=lambda x: x.get('수익개선금액', 0), reverse=True)
    return filter_results


# ============================================================================
# 6. ML 기반 특성 중요도 분석
# ============================================================================

def AnalyzeFeatureImportance(df_tsg):
    """
    RandomForest를 사용하여 특성 중요도를 분석합니다.
    
    개선사항:
    - 매수 시점에서 사용 가능한 모든 숫자형 변수를 동적으로 탐지
    - 불균형 데이터에서 class_weight='balanced' 사용
    - F1 Score (macro) 기반 평가로 소수 클래스 성능 반영

    Returns:
        dict: 특성 중요도 분석 결과
            - feature_importance: 특성별 중요도
            - top_features: 상위 특성
            - decision_rules: 주요 분기 규칙
            - model_f1: F1 Score (불균형 데이터 평가에 적합)
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.dummy import DummyClassifier
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import f1_score, balanced_accuracy_score
    except ImportError:
        return None

    # ================================================================
    # 매수 시점에서 사용 가능한 모든 숫자형 변수를 동적으로 탐지
    # ================================================================
    # 1) 명시적 매수 시점 컬럼 (접두사 '매수')
    # 2) 매수 시점에서 확정된 컬럼 (시가총액, 위험도점수, 모멘텀점수 등 파생 지표)
    # 3) 제외할 컬럼: 매도 시점 변수, 결과 변수, 변화량 지표(룩어헤드)
    
    # 매도 시점 또는 결과 관련 컬럼 패턴 (제외)
    # - 주의: "매도" 문자열이 포함되더라도, 매수시점 호가/잔량(예: 매수매도총잔량, 매도잔량_매수잔량_비율)은
    #         매수 시점에 알 수 있는 정보이므로 제외하지 않습니다.
    exclude_patterns = [
        '수익금', '수익률', '손실', '이익', '보유시간',
        '변화', '추세', '매수매도위험도점수',  # 사후 계산 위험도(룩어헤드 포함)
        '연속이익', '연속손실', '리스크조정수익률',  # 사후 통계
        '합계', '누적', '수익금합계',
        '손실확률', '_ML',  # 모델 출력 컬럼(재실행 시 자기 자신 포함 방지)
    ]
    
    # 명시적으로 매수 시점에서 사용 가능한 변수 목록
    explicit_buy_columns = [
        '매수등락율', '매수시가등락율', '매수당일거래대금', '매수체결강도',
        '매수전일비', '매수회전율', '매수전일동시간비', '매수고가', '매수저가',
        '매수고저평균대비등락율', '매수매도총잔량', '매수매수총잔량',
        '매수호가잔량비', '매수매도호가1', '매수매수호가1', '매수스프레드',
        '매수초당매수수량', '매수초당매도수량', '매수초당거래대금',
        '시가총액', '매수가', '매수시', '매수분', '매수초',
        # 파생 지표 (매수 시점 데이터만으로 계산된 것들)
        '모멘텀점수', '매수변동폭', '매수변동폭비율', '거래품질점수',
        '초당매수수량_매도총잔량_비율', '매도잔량_매수잔량_비율',
        '매수잔량_매도잔량_비율', '초당매도_매수_비율', '초당매수_매도_비율',
        '현재가_고저범위_위치', '초당거래대금_당일비중',
        '초당순매수수량', '초당순매수금액', '초당순매수비율',
    ]
    
    # 동적으로 사용 가능한 컬럼 선택
    feature_columns = []
    for col in df_tsg.columns:
        # 숫자형 컬럼만
        if not pd.api.types.is_numeric_dtype(df_tsg[col]):
            continue
        
        # 제외 패턴 확인
        col_lower = col.lower()
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern.lower() in col_lower:
                should_exclude = True
                break
        
        if should_exclude:
            continue
        
        # 명시적 매수 컬럼이거나 매수 접두사가 있는 경우
        if col in explicit_buy_columns:
            feature_columns.append(col)
        elif col.startswith('매수') and col not in feature_columns:
            feature_columns.append(col)
    
    # 추가: 시가총액 등 명시적으로 매수 시점 확정 변수
    for col in ['시가총액', '모멘텀점수', '거래품질점수', '위험도점수']:
        if col in df_tsg.columns and col not in feature_columns:
            feature_columns.append(col)
    
    available_features = [col for col in feature_columns if col in df_tsg.columns]

    if len(available_features) < 3:
        return None

    # 타겟 변수: 이익 여부
    required_cols = available_features + ['수익금']
    df_analysis = df_tsg[required_cols].dropna()

    if len(df_analysis) < 50:
        return None

    X = df_analysis[available_features]
    y = (df_analysis['수익금'] > 0).astype(int)

    # Train/Test 분리(과대평가 방지)
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )
    except Exception:
        # 샘플 수가 작거나 stratify 불가 등 예외 시 전체 학습으로 폴백
        X_train, X_test, y_train, y_test = X, X, y, y

    # 표준화
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test) if len(X_test) else X_train_scaled

    # ================================================================
    # 기준선(베이스라인) 지표 계산
    # - model_accuracy는 Balanced Accuracy를 사용하므로, baseline도 동일 metric으로 계산합니다.
    # ================================================================
    try:
        pos_ratio = float(y.mean())
    except Exception:
        pos_ratio = 0.0
    majority_accuracy = round(max(pos_ratio, 1 - pos_ratio) * 100, 1)

    baseline_accuracy = 50.0
    baseline_f1 = 0.0
    random_f1 = 0.0
    random_accuracy = 50.0
    try:
        dummy_major = DummyClassifier(strategy='most_frequent')
        dummy_major.fit(X_train_scaled, y_train)
        y_base = dummy_major.predict(X_test_scaled)
        baseline_accuracy = round(balanced_accuracy_score(y_test, y_base) * 100, 1)
        baseline_f1 = round(f1_score(y_test, y_base, average='macro') * 100, 1)

        dummy_rand = DummyClassifier(strategy='stratified', random_state=42)
        dummy_rand.fit(X_train_scaled, y_train)
        y_rand = dummy_rand.predict(X_test_scaled)
        random_accuracy = round(balanced_accuracy_score(y_test, y_rand) * 100, 1)
        random_f1 = round(f1_score(y_test, y_rand, average='macro') * 100, 1)
    except Exception:
        pass

    # ================================================================
    # RandomForest with class_weight='balanced' for imbalanced data
    # ================================================================
    rf_clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        min_samples_leaf=10,
        class_weight='balanced',  # 불균형 데이터 처리
        random_state=42,
        n_jobs=-1
    )
    rf_clf.fit(X_train_scaled, y_train)

    # 특성 중요도 (RandomForest)
    importance = dict(zip(available_features, rf_clf.feature_importances_))
    importance_sorted = sorted(importance.items(), key=lambda x: x[1], reverse=True)

    # Decision Tree도 학습 (분기 규칙 추출용)
    clf = DecisionTreeClassifier(
        max_depth=4, 
        min_samples_leaf=10, 
        class_weight='balanced',
        random_state=42
    )
    clf.fit(X_train_scaled, y_train)

    # 분기 규칙 추출 (간략화)
    tree = clf.tree_
    rules = []

    def extract_rules(node_id, depth, prefix=""):
        if tree.feature[node_id] != -2:  # 내부 노드
            feature_name = available_features[tree.feature[node_id]]
            threshold = tree.threshold[node_id]

            # 원래 스케일로 변환
            feature_idx = available_features.index(feature_name)
            original_threshold = threshold * scaler.scale_[feature_idx] + scaler.mean_[feature_idx]

            if depth <= 2:  # 상위 2레벨만
                left_samples = tree.n_node_samples[tree.children_left[node_id]]
                right_samples = tree.n_node_samples[tree.children_right[node_id]]

                left_value = tree.value[tree.children_left[node_id]][0]
                right_value = tree.value[tree.children_right[node_id]][0]

                left_win_rate = left_value[1] / (left_value[0] + left_value[1]) * 100 if (left_value[0] + left_value[1]) > 0 else 0
                right_win_rate = right_value[1] / (right_value[0] + right_value[1]) * 100 if (right_value[0] + right_value[1]) > 0 else 0

                rules.append({
                    'depth': depth,
                    'feature': feature_name,
                    'threshold': round(original_threshold, 2),
                    'left_samples': left_samples,
                    'right_samples': right_samples,
                    'left_win_rate': round(left_win_rate, 1),
                    'right_win_rate': round(right_win_rate, 1),
                    'rule': f"{feature_name} < {original_threshold:.1f}: 승률 {left_win_rate:.1f}% (n={left_samples})"
                })

                extract_rules(tree.children_left[node_id], depth + 1, prefix + "L")
                extract_rules(tree.children_right[node_id], depth + 1, prefix + "R")

    extract_rules(0, 0)

    # 성능 평가 (F1 Score, Balanced Accuracy 사용)
    try:
        y_pred_train = rf_clf.predict(X_train_scaled)
        y_pred_test = rf_clf.predict(X_test_scaled)
        
        train_f1 = round(f1_score(y_train, y_pred_train, average='macro') * 100, 1)
        test_f1 = round(f1_score(y_test, y_pred_test, average='macro') * 100, 1)
        
        train_acc = round(balanced_accuracy_score(y_train, y_pred_train) * 100, 1)
        test_acc = round(balanced_accuracy_score(y_test, y_pred_test) * 100, 1)
    except Exception:
        train_f1 = test_f1 = 0.0
        train_acc = test_acc = 0.0

    return {
        'feature_importance': importance_sorted,
        'top_features': importance_sorted[:10],  # 상위 10개로 확장
        'decision_rules': rules[:10],
        'model_accuracy': test_acc,  # Balanced Accuracy
        'model_accuracy_train': train_acc,
        'model_f1': test_f1,
        'model_f1_train': train_f1,
        'baseline_accuracy': baseline_accuracy,  # Balanced Accuracy 기준선
        'baseline_f1': baseline_f1,
        'baseline_majority_accuracy': majority_accuracy,
        'random_baseline_accuracy': random_accuracy,
        'random_baseline_f1': random_f1,
        'total_features_used': len(available_features),
        'features_used': available_features,
    }


# ============================================================================
# 6.5. ML 기반 매수매도 위험도 예측 (NEW)
# ============================================================================

def PredictRiskWithML(df_tsg, save_file_name=None, buystg=None, sellstg=None, strategy_key=None, train_mode: str = 'train'):
    """
    머신러닝을 사용하여 매수 시점의 위험도를 예측합니다.
    
    매수 시점에서 사용 가능한 모든 변수를 바탕으로:
    1. 손실 확률(loss_prob_ml) 예측
    2. ML 기반 위험도 점수(risk_score_ml) 계산
    3. 실제 매수매도위험도점수와 비교

    추가 기능:
    - (저장) 실행별로 학습된 모델 번들(joblib)을 저장하고, 전략(조건식) 폴더의 latest도 갱신합니다.
    - (로드) train_mode를 'load_latest'로 주면, 동일 전략키의 latest 모델로 예측값을 재현할 수 있습니다.
    
    Returns:
        tuple: (updated_df, prediction_stats)
        - updated_df: ML 예측값이 추가된 DataFrame
        - prediction_stats: 예측 성능 통계
    """
    try:
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.neural_network import MLPRegressor
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import f1_score, balanced_accuracy_score, roc_auc_score
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        from sklearn.utils.class_weight import compute_sample_weight
    except ImportError:
        return df_tsg, None
    
    timing = {}
    total_start = time.perf_counter()

    df = df_tsg.copy()

    # 전략키(조건식 식별) 계산
    strategy_key_local = strategy_key
    if not strategy_key_local and (buystg is not None or sellstg is not None):
        try:
            strategy_key_local = ComputeStrategyKey(buystg=buystg, sellstg=sellstg)
        except Exception:
            strategy_key_local = None

    # 모델 로드(옵션)
    if train_mode in ('load_latest', 'load_only') and strategy_key_local:
        t0_load = time.perf_counter()
        latest_path = MODEL_BASE_DIR / 'strategies' / str(strategy_key_local) / 'latest_ml_bundle.joblib'
        if latest_path.exists():
            bundle = _load_ml_bundle(latest_path)
            if isinstance(bundle, dict) and bundle.get('rf_model') is not None:
                df_loaded, info = _apply_ml_bundle(df, bundle)
                train_stats = bundle.get('train_stats') or {}
                timing['load_latest_s'] = round(time.perf_counter() - t0_load, 4)
                timing['total_s'] = round(time.perf_counter() - total_start, 4)
                stats = {
                    'model_type': train_stats.get('model_type', 'SavedBundle'),
                    'train_mode': 'loaded_latest',
                    'strategy_key': strategy_key_local,
                    'feature_schema_hash': bundle.get('feature_schema_hash'),
                    'total_features': len(bundle.get('features_loss') or []),
                    'top_features': train_stats.get('top_features'),
                    'test_auc': train_stats.get('test_auc'),
                    'test_f1': train_stats.get('test_f1'),
                    'test_balanced_accuracy': train_stats.get('test_balanced_accuracy'),
                    'loss_rate': train_stats.get('loss_rate'),
                    'timing': timing,
                    'loaded_from': str(latest_path),
                    'missing_features': info.get('missing_features') or [],
                    'artifacts': {
                        'latest_bundle_path': str(latest_path),
                        'strategy_dir': str(latest_path.parent),
                        'saved': True,
                    }
                }
                return df_loaded, stats
        if train_mode == 'load_only':
            # 로드만 허용인데 실패한 경우: 기본값으로 폴백
            df['손실확률_ML'] = 0.5
            df['위험도_ML'] = 50
            df['예측매수매도위험도점수_ML'] = np.nan
            timing['load_only_failed_s'] = round(time.perf_counter() - t0_load, 4)
            timing['total_s'] = round(time.perf_counter() - total_start, 4)
            return df, {
                'model_type': 'N/A',
                'train_mode': 'load_only_failed',
                'strategy_key': strategy_key_local,
                'error': 'latest 모델을 찾지 못해 예측을 수행하지 못했습니다.',
                'timing': timing,
            }
    
    # ================================================================
    # 매수 시점에서 사용 가능한 변수만 선택 (룩어헤드 방지)
    # ================================================================
    exclude_patterns = [
        '수익금', '수익률', '손실', '이익', '보유시간',
        '변화', '추세', '매수매도위험도점수',  # 사후 계산 위험도(룩어헤드 포함)
        '연속이익', '연속손실', '리스크조정수익률',
        '합계', '누적', '수익금합계', '손실확률', '_ML', 'risk_score_ml',
    ]
    
    explicit_buy_columns = [
        '매수등락율', '매수시가등락율', '매수당일거래대금', '매수체결강도',
        '매수전일비', '매수회전율', '매수전일동시간비', '매수고가', '매수저가',
        '매수고저평균대비등락율', '매수매도총잔량', '매수매수총잔량',
        '매수호가잔량비', '매수매도호가1', '매수매수호가1', '매수스프레드',
        '매수초당매수수량', '매수초당매도수량', '매수초당거래대금',
        '시가총액', '매수가', '매수시', '매수분', '매수초',
        '모멘텀점수', '매수변동폭', '매수변동폭비율', '거래품질점수',
        '초당매수수량_매도총잔량_비율', '매도잔량_매수잔량_비율',
        '매수잔량_매도잔량_비율', '초당매도_매수_비율', '초당매수_매도_비율',
        '현재가_고저범위_위치', '초당거래대금_당일비중',
        '초당순매수수량', '초당순매수금액', '초당순매수비율',
        '위험도점수',  # 규칙 기반 위험도 (매수 시점 정보만 사용)
    ]
    
    feature_columns = []
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        
        col_lower = col.lower()
        should_exclude = False
        for pattern in exclude_patterns:
            if pattern.lower() in col_lower:
                should_exclude = True
                break
        
        if should_exclude:
            continue
        
        if col in explicit_buy_columns:
            feature_columns.append(col)
        elif col.startswith('매수') and col not in feature_columns:
            feature_columns.append(col)
    
    for col in ['시가총액', '모멘텀점수', '거래품질점수', '위험도점수']:
        if col in df.columns and col not in feature_columns:
            feature_columns.append(col)
    
    available_features = [col for col in feature_columns if col in df.columns]
    
    if len(available_features) < 5:
        # 피처가 부족하면 기본값 설정
        df['손실확률_ML'] = 0.5
        df['위험도_ML'] = 50
        df['예측매수매도위험도점수_ML'] = np.nan
        timing['total_s'] = round(time.perf_counter() - total_start, 4)
        return df, {
            'model_type': 'N/A',
            'train_mode': 'insufficient_features',
            'strategy_key': strategy_key_local,
            'total_features': len(available_features),
            'feature_schema_hash': _feature_schema_hash(available_features),
            'timing': timing,
        }
    
    # ================================================================
    # 타겟 변수: 손실 여부 (수익금 <= 0)
    # ================================================================
    required_cols = available_features + ['수익금']
    df_analysis = df[required_cols].copy()
    
    # NaN 처리 (평균값으로 대체)
    for col in available_features:
        if df_analysis[col].isna().sum() > 0:
            df_analysis[col] = df_analysis[col].fillna(df_analysis[col].median())
    
    df_clean = df_analysis.dropna(subset=['수익금'])
    
    if len(df_clean) < 50:
        df['손실확률_ML'] = 0.5
        df['위험도_ML'] = 50
        df['예측매수매도위험도점수_ML'] = np.nan
        timing['total_s'] = round(time.perf_counter() - total_start, 4)
        return df, {
            'model_type': 'N/A',
            'train_mode': 'insufficient_samples',
            'strategy_key': strategy_key_local,
            'total_features': len(available_features),
            'feature_schema_hash': _feature_schema_hash(available_features),
            'n_samples': int(len(df_clean)),
            'timing': timing,
        }
    
    X = df_clean[available_features].values
    y = (df_clean['수익금'] <= 0).astype(int).values  # 손실=1, 이익=0
    
    # Train/Test 분리
    t0 = time.perf_counter()
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )
    except Exception:
        X_train, X_test, y_train, y_test = X, X, y, y
    timing['split_s'] = round(time.perf_counter() - t0, 4)
    
    # 표준화
    t0 = time.perf_counter()
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    timing['scale_s'] = round(time.perf_counter() - t0, 4)
    
    # ================================================================
    # 앙상블 모델: RandomForest + GradientBoosting
    # ================================================================
    t0 = time.perf_counter()
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    gb_model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        min_samples_leaf=10,
        random_state=42
    )
    
    sample_weight = None
    try:
        sample_weight = compute_sample_weight(class_weight='balanced', y=y_train)
    except Exception:
        sample_weight = None

    rf_model.fit(X_train_scaled, y_train)
    if sample_weight is not None:
        gb_model.fit(X_train_scaled, y_train, sample_weight=sample_weight)
    else:
        gb_model.fit(X_train_scaled, y_train)
    timing['train_classifiers_s'] = round(time.perf_counter() - t0, 4)

    # ================================================================
    # 설명용(규칙화) 얕은 트리 학습 (공식/조건식 형태로 참고용)
    # - 실제 필터로 쓰기 전 반드시 검증 필요(과최적화/분포변화 위험)
    # ================================================================
    explain_tree = None
    explain_rules = []
    t0 = time.perf_counter()
    try:
        explain_tree = DecisionTreeClassifier(
            max_depth=4,
            min_samples_leaf=50,
            class_weight='balanced',
            random_state=42
        )
        explain_tree.fit(X_train_scaled, y_train)
        explain_rules = _extract_tree_rules(explain_tree, scaler, available_features, max_depth=2)
    except Exception:
        explain_tree = None
        explain_rules = []
    timing['train_explain_tree_s'] = round(time.perf_counter() - t0, 4)
    
    # 앙상블 예측 (확률 평균)
    t0 = time.perf_counter()
    rf_proba = rf_model.predict_proba(X_test_scaled)[:, 1]
    gb_proba = gb_model.predict_proba(X_test_scaled)[:, 1]
    ensemble_proba = (rf_proba + gb_proba) / 2
    timing['predict_test_s'] = round(time.perf_counter() - t0, 4)
    
    # 성능 평가
    t0 = time.perf_counter()
    try:
        y_pred = (ensemble_proba >= 0.5).astype(int)
        test_f1 = round(f1_score(y_test, y_pred, average='macro') * 100, 1)
        test_acc = round(balanced_accuracy_score(y_test, y_pred) * 100, 1)
        test_auc = round(roc_auc_score(y_test, ensemble_proba) * 100, 1)
    except Exception:
        test_f1 = test_acc = test_auc = 0.0
    timing['eval_s'] = round(time.perf_counter() - t0, 4)
    
    # ================================================================
    # 전체 데이터에 대해 예측
    # ================================================================
    # 전체 데이터 표준화
    t0 = time.perf_counter()
    X_all = df_analysis[available_features].values
    
    # NaN을 median으로 채우기
    for i, col in enumerate(available_features):
        mask = np.isnan(X_all[:, i])
        if mask.any():
            X_all[mask, i] = np.nanmedian(X_all[:, i])
    
    X_all_scaled = scaler.transform(X_all)
    
    # 앙상블 예측
    rf_proba_all = rf_model.predict_proba(X_all_scaled)[:, 1]
    gb_proba_all = gb_model.predict_proba(X_all_scaled)[:, 1]
    loss_prob_all = (rf_proba_all + gb_proba_all) / 2
    timing['predict_all_s'] = round(time.perf_counter() - t0, 4)
    
    # DataFrame에 추가 (원본 인덱스 유지)
    df['손실확률_ML'] = np.nan
    df['위험도_ML'] = np.nan

    # df_analysis와 동일한 인덱스로 할당 (안전한 방식)
    # - 대용량 데이터에서 인덱스 중복/불일치 문제 방지를 위해 Series.update() 사용
    try:
        # 방법 1: Series를 생성하여 update로 안전하게 할당
        loss_prob_series = pd.Series(loss_prob_all, index=df_analysis.index)
        risk_prob_series = pd.Series((loss_prob_all * 100).clip(0, 100), index=df_analysis.index)

        # df의 해당 컬럼을 Series로 변환 후 update
        df['손실확률_ML'] = df['손실확률_ML'].astype(float)
        df['위험도_ML'] = df['위험도_ML'].astype(float)

        # update는 인덱스가 일치하는 위치에만 값을 할당
        df['손실확률_ML'].update(loss_prob_series)
        df['위험도_ML'].update(risk_prob_series)
    except Exception:
        # 방법 2: 폴백 - iloc 기반 위치 매핑 (인덱스 무관)
        try:
            # df_analysis의 원본 위치를 추적하여 할당
            analysis_idx_set = set(df_analysis.index)
            idx_to_pos = {idx: i for i, idx in enumerate(df_analysis.index)}

            for df_idx in df.index:
                if df_idx in idx_to_pos:
                    pos = idx_to_pos[df_idx]
                    df.at[df_idx, '손실확률_ML'] = loss_prob_all[pos]
                    df.at[df_idx, '위험도_ML'] = min(max(loss_prob_all[pos] * 100, 0), 100)
        except Exception:
            pass  # 최종 폴백: NaN 유지 후 중앙값으로 채움
    
    # NaN 채우기 (중앙값)
    median_prob = float(np.nanmedian(loss_prob_all))
    df['손실확률_ML'] = df['손실확률_ML'].fillna(median_prob)
    df['위험도_ML'] = df['위험도_ML'].fillna(median_prob * 100)

    # ================================================================
    # (추가) 매수 시점 변수로 "매수매도위험도점수"를 예측(회귀)하여 비교 컬럼 생성
    # - 목적: 룩어헤드로 계산된 위험도(사후 점수)를 매수시점 정보만으로 얼마나 근사할 수 있는지 확인
    # ================================================================
    risk_regression_stats = None
    risk_reg_model = None
    risk_reg_scaler = None
    risk_reg_model_name = None
    df['예측매수매도위험도점수_ML'] = np.nan
    if '매수매도위험도점수' in df.columns:
        t0 = time.perf_counter()
        try:
            df_risk = df[available_features + ['매수매도위험도점수']].copy()
            df_risk['매수매도위험도점수'] = pd.to_numeric(df_risk['매수매도위험도점수'], errors='coerce')
            df_risk = df_risk.dropna(subset=['매수매도위험도점수'])

            if len(df_risk) >= 50:
                for col in available_features:
                    if df_risk[col].isna().sum() > 0:
                        df_risk[col] = df_risk[col].fillna(df_risk[col].median())

                Xr = df_risk[available_features].values
                yr = df_risk['매수매도위험도점수'].values

                try:
                    Xr_train, Xr_test, yr_train, yr_test = train_test_split(
                        Xr, yr, test_size=0.25, random_state=42
                    )
                except Exception:
                    Xr_train, Xr_test, yr_train, yr_test = Xr, Xr, yr, yr

                scaler_r = StandardScaler()
                Xr_train_s = scaler_r.fit_transform(Xr_train)
                Xr_test_s = scaler_r.transform(Xr_test)

                rf_reg = RandomForestRegressor(
                    n_estimators=150,
                    max_depth=10,
                    min_samples_leaf=5,
                    random_state=42,
                    n_jobs=-1
                )
                rf_reg.fit(Xr_train_s, yr_train)
                pred_rf = rf_reg.predict(Xr_test_s)
                mae_rf = float(mean_absolute_error(yr_test, pred_rf))

                max_mlp_samples = 25000
                if len(yr_train) > max_mlp_samples:
                    rng = np.random.RandomState(42)
                    idx = rng.choice(len(yr_train), max_mlp_samples, replace=False)
                    X_mlp, y_mlp = Xr_train_s[idx], yr_train[idx]
                else:
                    X_mlp, y_mlp = Xr_train_s, yr_train

                mlp_reg = MLPRegressor(
                    hidden_layer_sizes=(64, 32),
                    max_iter=200,
                    early_stopping=True,
                    random_state=42
                )
                mlp_reg.fit(X_mlp, y_mlp)
                pred_mlp = mlp_reg.predict(Xr_test_s)
                mae_mlp = float(mean_absolute_error(yr_test, pred_mlp))

                if mae_mlp <= mae_rf:
                    best_name = 'MLPRegressor'
                    best_model = mlp_reg
                    best_pred_test = pred_mlp
                    best_mae = mae_mlp
                else:
                    best_name = 'RandomForestRegressor'
                    best_model = rf_reg
                    best_pred_test = pred_rf
                    best_mae = mae_rf

                rmse = float(np.sqrt(mean_squared_error(yr_test, best_pred_test)))
                r2 = float(r2_score(yr_test, best_pred_test))
                try:
                    corr = float(np.corrcoef(yr_test, best_pred_test)[0, 1])
                except Exception:
                    corr = float('nan')

                # 전체 데이터 예측
                Xr_all = df[available_features].copy()
                for col in available_features:
                    if Xr_all[col].isna().sum() > 0:
                        Xr_all[col] = Xr_all[col].fillna(Xr_all[col].median())
                Xr_all_s = scaler_r.transform(Xr_all.values)
                pred_all = best_model.predict(Xr_all_s)
                df['예측매수매도위험도점수_ML'] = np.clip(pred_all, 0, 100)

                # NaN 채우기 (중앙값)
                med_pred = float(np.nanmedian(df['예측매수매도위험도점수_ML'].values))
                df['예측매수매도위험도점수_ML'] = df['예측매수매도위험도점수_ML'].fillna(med_pred)

                risk_regression_stats = {
                    'target': '매수매도위험도점수',
                    'best_model': best_name,
                    'test_mae': round(best_mae, 2),
                    'test_rmse': round(rmse, 2),
                    'test_r2': round(r2, 3),
                    'test_corr': round(corr * 100, 1) if np.isfinite(corr) else None,
                    'mae_rf': round(mae_rf, 2),
                    'mae_mlp': round(mae_mlp, 2),
                }
                risk_reg_model = best_model
                risk_reg_scaler = scaler_r
                risk_reg_model_name = best_name
        except Exception:
            pass
        timing['risk_regression_s'] = round(time.perf_counter() - t0, 4)

    # ================================================================
    # 실제 매수매도위험도점수와 비교 (상관관계)
    # ================================================================
    correlation_actual = None
    if '매수매도위험도점수' in df.columns:
        try:
            corr = df[['위험도_ML', '매수매도위험도점수']].corr().iloc[0, 1]
            correlation_actual = round(corr * 100, 1) if pd.notna(corr) else None
        except Exception:
            pass
    
    correlation_rule = None
    if '위험도점수' in df.columns:
        try:
            corr = df[['위험도_ML', '위험도점수']].corr().iloc[0, 1]
            correlation_rule = round(corr * 100, 1) if pd.notna(corr) else None
        except Exception:
            pass
    
    # Feature Importance 추출
    feature_importance = sorted(
        zip(available_features, rf_model.feature_importances_),
        key=lambda x: x[1], reverse=True
    )[:10]

    schema_hash = _feature_schema_hash(available_features)
    
    prediction_stats = {
        'model_type': 'Ensemble (RandomForest + GradientBoosting)',
        'train_mode': 'trained_new',
        'requested_train_mode': train_mode,
        'save_file_name': save_file_name,
        'strategy_key': strategy_key_local,
        'feature_schema_hash': schema_hash,
        'test_f1': test_f1,
        'test_balanced_accuracy': test_acc,
        'test_auc': test_auc,
        'total_features': len(available_features),
        'top_features': feature_importance,
        'correlation_with_actual_risk': correlation_actual,
        'correlation_with_rule_risk': correlation_rule,
        'risk_regression': risk_regression_stats,
        'risk_regression_model': risk_reg_model_name,
        'explain_rules': explain_rules,
        'loss_rate': round(y.mean() * 100, 1),
    }

    # ================================================================
    # 모델 번들 저장(실행별 + 전략 latest)
    # ================================================================
    artifacts = None
    t0 = time.perf_counter()
    try:
        if save_file_name and strategy_key_local:
            bundle = {
                'bundle_version': 1,
                'created_at': datetime.now().isoformat(timespec='seconds'),
                'save_file_name': save_file_name,
                'strategy_key': strategy_key_local,
                'train_mode': prediction_stats.get('train_mode'),
                'feature_schema_hash': schema_hash,
                'features_loss': list(available_features),
                'scaler_loss': scaler,
                'rf_model': rf_model,
                'gb_model': gb_model,
                'loss_threshold': 0.5,
                'risk_regression': {
                    'features': list(available_features),
                    'scaler': risk_reg_scaler,
                    'model': risk_reg_model,
                    'best_model_name': risk_reg_model_name,
                    'stats': risk_regression_stats,
                } if (risk_reg_model is not None and risk_reg_scaler is not None) else None,
                'explain_tree': explain_tree,
                'explain_rules': explain_rules,
                'train_stats': {
                    'model_type': prediction_stats.get('model_type'),
                    'test_auc': prediction_stats.get('test_auc'),
                    'test_f1': prediction_stats.get('test_f1'),
                    'test_balanced_accuracy': prediction_stats.get('test_balanced_accuracy'),
                    'loss_rate': prediction_stats.get('loss_rate'),
                    'top_features': feature_importance,
                },
                'strategy': {
                    'buystg': buystg,
                    'sellstg': sellstg,
                }
            }
            artifacts = _save_ml_bundle(bundle, strategy_key=strategy_key_local, save_file_name=save_file_name)
        else:
            artifacts = {'saved': False, 'error': 'save_file_name/strategy_key 누락'}
    except Exception as e:
        artifacts = {'saved': False, 'error': str(e)}

    timing['save_bundle_s'] = round(time.perf_counter() - t0, 4)
    timing['total_s'] = round(time.perf_counter() - total_start, 4)
    prediction_stats['timing'] = timing
    prediction_stats['artifacts'] = artifacts
    
    return df, prediction_stats


# ============================================================================
# 7. 기간별 필터 안정성 검증
# ============================================================================

def AnalyzeFilterStability(df_tsg, n_periods=5):
    """
    필터 효과의 시간적 안정성을 검증합니다.

    Args:
        df_tsg: DataFrame
        n_periods: 분할 기간 수

    Returns:
        list: 필터별 안정성 분석 결과
    """
    if len(df_tsg) < n_periods * 20:
        return []

    # 인덱스로 기간 분할
    period_size = len(df_tsg) // n_periods
    periods = []
    for i in range(n_periods):
        start_idx = i * period_size
        end_idx = start_idx + period_size if i < n_periods - 1 else len(df_tsg)
        periods.append(df_tsg.iloc[start_idx:end_idx])

    # 주요 필터만 안정성 분석
    key_filters = [
        ('매수등락율 >= 20', lambda df: df['매수등락율'] >= 20, '등락율'),
        ('매수체결강도 < 80', lambda df: df['매수체결강도'] < 80, '체결강도'),
    ]

    if '시가총액' in df_tsg.columns:
        key_filters.append(('매수시가총액 < 1000', lambda df: df['시가총액'] < 1000, '시가총액'))

    if '위험도점수' in df_tsg.columns:
        key_filters.append(('위험도점수 >= 50', lambda df: df['위험도점수'] >= 50, '위험도'))

    stability_results = []

    for filter_name, filter_func, category in key_filters:
        try:
            if filter_name.split()[0] not in df_tsg.columns:
                continue

            period_improvements = []

            for period_df in periods:
                condition = filter_func(period_df)
                filtered_out = period_df[condition]
                improvement = -filtered_out['수익금'].sum() if len(filtered_out) > 0 else 0
                period_improvements.append(improvement)

            # 안정성 지표 계산
            improvements = np.array(period_improvements)
            mean_improvement = np.mean(improvements)
            std_improvement = np.std(improvements)
            positive_periods = sum(1 for x in improvements if x > 0)

            # 일관성 점수 (0-100)
            # 모든 기간에서 양수이고 변동성이 낮을수록 높음
            consistency_score = (positive_periods / n_periods) * 50
            if mean_improvement > 0 and std_improvement > 0:
                cv = std_improvement / mean_improvement  # 변동계수
                consistency_score += max(0, 50 - cv * 50)

            stability_results.append({
                '분류': category,
                '필터명': filter_name,
                '평균개선': int(mean_improvement),
                '표준편차': int(std_improvement),
                '양수기간수': positive_periods,
                '총기간수': n_periods,
                '일관성점수': round(consistency_score, 1),
                '기간별개선': [int(x) for x in period_improvements],
                '안정성등급': '안정' if consistency_score >= 70 else ('보통' if consistency_score >= 40 else '불안정'),
            })
        except:
            continue

    stability_results.sort(key=lambda x: x['일관성점수'], reverse=True)
    return stability_results


# ============================================================================
# 8. 조건식 코드 자동 생성
# ============================================================================

def GenerateFilterCode(filter_results, df_tsg=None, top_n=5, allow_ml_filters: bool = True):
    """
    필터 분석 결과를 바탕으로 실제 적용 가능한 조건식 코드를 생성합니다.

    Args:
        filter_results: 필터 분석 결과 리스트
        df_tsg: (선택) 원본 DataFrame. 전달되면 "동시 적용(중복 반영)" 기준으로
                예상 총 개선/누적 제외비율/추가 개선(증분)을 계산합니다.
        top_n: 상위 N개 필터(최대)
        allow_ml_filters: False면 *_ML 필터는 코드 생성에서 제외합니다.

    Returns:
        dict: 코드 생성 결과
            - buy_conditions: 매수 조건 코드
            - filter_conditions: 필터 조건 코드
            - full_code: 전체 조건식 코드
    """
    if not filter_results:
        return None

    filtered = list(filter_results)
    excluded_ml_count = 0
    if not allow_ml_filters:
        filtered_no_ml = []
        for f in filtered:
            text = f"{f.get('필터명', '')} {f.get('조건식', '')} {f.get('적용코드', '')}"
            if '_ML' in str(text):
                excluded_ml_count += 1
                continue
            filtered_no_ml.append(f)
        filtered = filtered_no_ml

    # 기본 후보: 개선(+) + 적용코드/조건식이 있는 항목
    candidates = [
        f for f in filtered
        if f.get('수익개선금액', 0) > 0 and f.get('적용코드') and f.get('조건식')
    ]

    if not candidates:
        return None

    # df_tsg가 있으면 "동시 적용(OR 제외)" 기준으로 중복/상쇄를 반영한 그리디 조합을 만듭니다.
    selected = []
    combine_steps = []
    combined_improvement = None
    naive_sum = 0

    if df_tsg is not None and '수익금' in df_tsg.columns and len(df_tsg) > 0:
        try:
            total_trades = int(len(df_tsg))
            profit_arr = df_tsg['수익금'].to_numpy(dtype=np.float64)
            base_profit = float(np.sum(profit_arr))
            return_arr = None
            if '수익률' in df_tsg.columns:
                return_arr = pd.to_numeric(df_tsg['수익률'], errors='coerce').fillna(0).to_numpy(dtype=np.float64)

            safe_globals = {"__builtins__": {}}
            safe_locals = {"df_tsg": df_tsg, "np": np, "pd": pd}

            cand_masks = []
            for f in candidates:
                cond_expr = f.get('조건식', '')
                cond = eval(cond_expr, safe_globals, safe_locals)
                cond_arr = cond.to_numpy(dtype=bool) if hasattr(cond, 'to_numpy') else np.asarray(cond, dtype=bool)
                if len(cond_arr) != total_trades:
                    cand_masks.append(None)
                else:
                    cand_masks.append(cond_arr)

            excluded_mask = np.zeros(total_trades, dtype=bool)
            cum_impr = 0.0
            chosen_idx = set()

            # 2025-12-20: 제외율/잔여거래 제한을 적용하여 100% 제외 방지
            max_exclusion_ratio = FILTER_MAX_EXCLUSION_RATIO  # 기본값 0.85
            # 작은 샘플에서도 필터 조합을 시도할 수 있도록, "전체의 15%"와 "기본 30건" 중 더 작은 값을 사용
            dynamic_min_remaining = max(1, min(int(total_trades * 0.15), FILTER_MIN_REMAINING_TRADES))

            max_steps = min(int(top_n), len(candidates))
            for step in range(max_steps):
                best_i = None
                best_inc = 0.0

                for i, (f, mask) in enumerate(zip(candidates, cand_masks)):
                    if i in chosen_idx or mask is None:
                        continue

                    # 2025-12-20: 새 필터 추가 시 제외율/잔여거래 제한 체크
                    new_excluded_mask = excluded_mask | mask
                    new_excluded_count = int(np.sum(new_excluded_mask))
                    new_remaining_count = total_trades - new_excluded_count
                    new_exclusion_ratio = new_excluded_count / total_trades

                    # 제외율이 MAX를 초과하면 이 필터는 선택하지 않음
                    if new_exclusion_ratio > max_exclusion_ratio:
                        continue
                    # 잔여 거래 수가 MIN 미만이면 이 필터는 선택하지 않음
                    if new_remaining_count < dynamic_min_remaining:
                        continue

                    add_mask = mask & (~excluded_mask)
                    inc = -float(np.sum(profit_arr[add_mask]))
                    if inc > best_inc:
                        best_inc = inc
                        best_i = i

                if best_i is None or best_inc <= 0:
                    break

                chosen_idx.add(best_i)
                excluded_mask |= cand_masks[best_i]
                cum_impr += best_inc

                excluded_count = int(np.sum(excluded_mask))
                remaining_count = total_trades - excluded_count
                remaining_winrate = float((profit_arr[~excluded_mask] > 0).mean() * 100) if remaining_count > 0 else 0.0
                remaining_return = None
                if return_arr is not None and remaining_count > 0:
                    remaining_return = float(np.mean(return_arr[~excluded_mask]))

                selected.append(candidates[best_i])
                combine_steps.append({
                    '순서': step + 1,
                    '필터명': candidates[best_i].get('필터명', ''),
                    '조건코드': candidates[best_i].get('적용코드', ''),
                    '개별개선': int(candidates[best_i].get('수익개선금액', 0)),
                    '추가개선(중복반영)': int(best_inc),
                    '누적개선(동시적용)': int(cum_impr),
                    '누적수익금': int(base_profit + cum_impr),
                    '누적제외비율': round(excluded_count / total_trades * 100, 1),
                    '잔여거래수': int(remaining_count),
                    '잔여승률': round(remaining_winrate, 1),
                    '잔여평균수익률': round(remaining_return, 2) if remaining_return is not None else None,
                })

            combined_improvement = int(cum_impr)
            naive_sum = int(sum(f.get('수익개선금액', 0) for f in selected))
        except Exception:
            selected = []
            combine_steps = []
            combined_improvement = None
            naive_sum = 0

    # fallback: df_tsg가 없으면 단순히 상위 N개(개별개선 기준)를 사용
    if not selected:
        selected = candidates[:top_n]
        naive_sum = int(sum(f.get('수익개선금액', 0) for f in selected))
        combined_improvement = naive_sum

    # 카테고리별 조건 분류
    conditions_by_category = {}
    for f in selected:
        category = f['분류']
        if category not in conditions_by_category:
            conditions_by_category[category] = []
        conditions_by_category[category].append(f)

    # 코드 생성
    code_lines = []
    code_lines.append("# ===== 자동 생성된 필터 조건 (백테스팅 분석 기반) =====")
    code_lines.append("")

    # 매수 조건에 추가할 필터
    buy_filter_lines = []

    for category, filters in conditions_by_category.items():
        code_lines.append(f"# [{category}] 필터")

        for f in filters:
            code_lines.append(f"# - {f['필터명']}: 수익개선 {f['수익개선금액']:,}원, 제외율 {f['제외비율']}%")

            # 조건식을 실제 코드로 변환
            if '적용코드' in f and f['적용코드']:
                buy_filter_lines.append(f"    and {f['적용코드']}")

        code_lines.append("")

    # 전체 매수 조건 예시
    code_lines.append("# ===== 적용 예시 =====")
    code_lines.append("# 기존 매수 조건에 다음 필터를 AND 조건으로 추가:")
    code_lines.append("#")
    code_lines.append("# if 기존매수조건")
    for line in buy_filter_lines:
        code_lines.append(f"#{line}")
    code_lines.append("#     매수 = True")
    code_lines.append("#")
    code_lines.append("# [조합 방식 설명]")
    code_lines.append("# - 각 필터는 '해당 조건이면 매수하지 않음(제외)'을 의미합니다.")
    code_lines.append("# - 여러 필터를 함께 쓴다는 것은: (필터1 통과) AND (필터2 통과) AND ... 로 해석됩니다.")
    code_lines.append("#   즉, 제외 조건 기준으로 보면 (제외1) OR (제외2) OR ... 입니다.")
    if combined_improvement is not None:
        overlap_loss = int(naive_sum - combined_improvement)
        code_lines.append("#")
        code_lines.append(f"# 예상 총 개선(동시 적용/중복 반영): {combined_improvement:,}원")
        code_lines.append(f"# 개별 개선 합(단순 합산): {naive_sum:,}원")
        code_lines.append(f"# 중복/상쇄(합산-동시적용): {overlap_loss:,}원")

    # 개별 조건식
    individual_conditions = []
    for f in selected:
        if '적용코드' in f:
            individual_conditions.append({
                '필터명': f['필터명'],
                '조건코드': f['적용코드'],
                '수익개선': f['수익개선금액'],
                '제외율': f['제외비율']
            })

    return {
        'code_text': '\n'.join(code_lines),
        'buy_conditions': buy_filter_lines,
        'individual_conditions': individual_conditions,
        'combine_steps': combine_steps,
        'summary': {
            'total_filters': len(selected),
            'total_improvement_combined': int(combined_improvement) if combined_improvement is not None else int(naive_sum),
            'total_improvement_naive': int(naive_sum),
            'overlap_loss': int(naive_sum - (combined_improvement if combined_improvement is not None else naive_sum)),
            'categories': list(conditions_by_category.keys()),
            'allow_ml_filters': bool(allow_ml_filters),
            'excluded_ml_filters': int(excluded_ml_count),
        }
    }


# ============================================================================
# 9. 강화된 시각화 차트
# ============================================================================

def PltEnhancedAnalysisCharts(df_tsg, save_file_name, teleQ,
                              filter_results=None, filter_results_lookahead=None,
                              feature_importance=None,
                              optimal_thresholds=None, filter_combinations=None,
                              filter_stability=None, generated_code=None,
                              buystg: str = None, sellstg: str = None):
    """
    강화된 분석 차트를 생성합니다.

    신규 차트:
    - 필터 효과 통계 요약 테이블
    - 특성 중요도 막대 차트
    - 최적 임계값 탐색 결과 (NEW)
    - 필터 조합 시너지 히트맵 (NEW)
    - 최적 임계값 효율성 곡선 (NEW)
    - (진단용) 룩어헤드 포함 필터 효과 Top (NEW)
    """
    if len(df_tsg) < 5:
        return

    try:
        # 차트용 복사본 (원본 df_tsg에 구간 컬럼 등이 추가되는 부작용 방지)
        df_tsg = df_tsg.copy()

        # 한글 폰트 설정
        # - 요약 텍스트 등에서 기본 monospace(DejaVu Sans Mono)로 fallback 되면 한글이 깨질 수 있어,
        #   family/monospace 모두에 한글 폰트를 우선 지정합니다.
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_family = font_manager.FontProperties(fname=font_path).get_name()
            plt.rcParams['font.family'] = font_family
            plt.rcParams['font.sans-serif'] = [font_family]
            plt.rcParams['font.monospace'] = [font_family, 'Consolas', 'monospace']
            try:
                font_manager.fontManager.addfont(font_path)
            except:
                pass
        except:
            plt.rcParams['font.family'] = 'Malgun Gothic'
            plt.rcParams['font.sans-serif'] = ['Malgun Gothic', 'DejaVu Sans']
            plt.rcParams['font.monospace'] = ['Malgun Gothic', 'Consolas', 'monospace']
        plt.rcParams['axes.unicode_minus'] = False

        # 타임프레임 감지
        tf_info = DetectTimeframe(df_tsg, save_file_name)

        fig = plt.figure(figsize=(20, 38))
        fig.suptitle(f'백테스팅 필터 분석 차트 - {save_file_name} ({tf_info["label"]})',
                     fontsize=16, fontweight='bold')

        gs = gridspec.GridSpec(8, 3, figure=fig, hspace=0.45, wspace=0.3)

        color_profit = '#2ECC71'
        color_loss = '#E74C3C'
        color_neutral = '#3498DB'

        # ============ Chart 1: 필터 효과 순위 ============
        ax1 = fig.add_subplot(gs[0, :2])
        if filter_results and len(filter_results) > 0:
            top_10 = [f for f in filter_results if f['수익개선금액'] > 0][:10]
            if top_10:
                names = [f['필터명'][:20] for f in top_10]
                improvements = [f['수익개선금액'] for f in top_10]
                colors = [color_profit for _ in improvements]

                y_pos = range(len(names))
                ax1.barh(y_pos, improvements, color=colors, edgecolor='black', linewidth=0.5)
                ax1.set_yticks(y_pos)
                ax1.set_yticklabels(names, fontsize=9)
                ax1.set_xlabel('수익 개선 금액')
                ax1.set_title('Top 10 필터 효과 (수익개선 기준)')

                # 값 표시
                for i, v in enumerate(improvements):
                    ax1.text(v + max(improvements) * 0.01, i, f'{v:,}원', va='center', fontsize=8)

                ax1.invert_yaxis()

        # ============ Chart 2: 통계적 유의성 요약 ============
        ax2 = fig.add_subplot(gs[0, 2])
        if filter_results and len(filter_results) > 0:
            significant_count = sum(1 for f in filter_results if f.get('유의함') == '예')
            total_count = len(filter_results)

            sizes = [significant_count, total_count - significant_count]
            labels = [f'유의함\n({significant_count})', f'비유의\n({total_count - significant_count})']
            colors = [color_profit, '#CCCCCC']

            ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax2.set_title('필터 통계적 유의성 분포')

        # ============ Chart 3: 특성 중요도 ============
        ax3 = fig.add_subplot(gs[1, 0])
        if feature_importance and 'feature_importance' in feature_importance:
            fi = feature_importance['feature_importance'][:8]
            names = [x[0] for x in fi]
            values = [x[1] for x in fi]

            y_pos = range(len(names))
            ax3.barh(y_pos, values, color=color_neutral, edgecolor='black', linewidth=0.5)
            ax3.set_yticks(y_pos)
            ax3.set_yticklabels(names, fontsize=9)
            ax3.set_xlabel('중요도')
            test_acc = feature_importance.get("model_accuracy", 0)
            base_acc = feature_importance.get("baseline_accuracy", 0)
            ax3.set_title(f"ML 특성 중요도 (정확도 test: {test_acc}%, 기준선: {base_acc}%)")
            ax3.invert_yaxis()

        # ============ Chart 4: 효과 크기 분포 ============
        ax4 = fig.add_subplot(gs[1, 1])
        if filter_results and len(filter_results) > 0:
            effect_sizes = [f['효과크기'] for f in filter_results if '효과크기' in f]
            if effect_sizes:
                ax4.hist(effect_sizes, bins=20, color=color_neutral, edgecolor='black', alpha=0.7)
                ax4.axvline(x=0.2, color='orange', linestyle='--', label='작은 효과')
                ax4.axvline(x=0.5, color='red', linestyle='--', label='중간 효과')
                ax4.axvline(x=0.8, color='purple', linestyle='--', label='큰 효과')
                ax4.set_xlabel('Cohen\'s d 효과 크기')
                ax4.set_ylabel('필터 수')
                ax4.set_title('필터 효과 크기 분포')
                ax4.legend(fontsize=8)

        # ============ Chart 5: 필터 적용 시 예상 수익 개선 효과 (Top 15) ============
        ax5 = fig.add_subplot(gs[1, 2])
        if filter_results and len(filter_results) > 0:
            df_filter = pd.DataFrame(filter_results)
            if '수익개선금액' in df_filter.columns and '필터명' in df_filter.columns:
                df_filter = df_filter[df_filter['수익개선금액'] > 0].sort_values('수익개선금액', ascending=False).head(15)

                if len(df_filter) > 0:
                    x_pos = range(len(df_filter))
                    ax5.bar(x_pos, df_filter['수익개선금액'], color=color_profit, edgecolor='black', linewidth=0.5)
                    ax5.set_xticks(list(x_pos))
                    ax5.set_xticklabels([str(x)[:18] for x in df_filter['필터명']],
                                        rotation=45, ha='right', fontsize=7)
                    ax5.set_ylabel('수익 개선 금액')
                    ax5.set_title('필터 적용 시 예상 수익 개선 효과 (Top 15)\n(막대=개별개선, 빨간선=누적(동시적용/중복반영))')
                    ax5.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

                    try:
                        if '조건식' in df_filter.columns and '수익금' in df_tsg.columns:
                            safe_globals = {"__builtins__": {}}
                            safe_locals = {"df_tsg": df_tsg, "np": np, "pd": pd}
                            profit_arr_local = df_tsg['수익금'].to_numpy(dtype=np.float64)
                            excluded_mask = np.zeros(len(df_tsg), dtype=bool)
                            cum_values = []
                            cum = 0.0
                            for expr in df_filter['조건식'].tolist():
                                cond = eval(expr, safe_globals, safe_locals)
                                cond_arr = cond.to_numpy(dtype=bool) if hasattr(cond, 'to_numpy') else np.asarray(cond, dtype=bool)
                                add_mask = cond_arr & (~excluded_mask)
                                cum += -float(np.sum(profit_arr_local[add_mask]))
                                excluded_mask |= cond_arr
                                cum_values.append(cum)

                            denom = float(cum_values[-1]) if cum_values else 0.0
                            if denom <= 0:
                                # 누적 개선이 0 이하로 끝나는 케이스는 비율 표시가 왜곡될 수 있어
                                # 기존(단순 합산) 누적비율로 폴백합니다.
                                cumsum = df_filter['수익개선금액'].cumsum()
                                denom = float(cumsum.iloc[-1]) if len(cumsum) > 0 else 0.0
                                cumsum_pct = (cumsum / denom * 100) if denom else [0 for _ in cumsum]
                            else:
                                cumsum_pct = [(v / denom * 100) for v in cum_values]
                        else:
                            cumsum = df_filter['수익개선금액'].cumsum()
                            denom = float(cumsum.iloc[-1]) if len(cumsum) > 0 else 0.0
                            cumsum_pct = (cumsum / denom * 100) if denom else [0 for _ in cumsum]

                        ax5_twin = ax5.twinx()
                        ax5_twin.plot(list(x_pos), cumsum_pct, 'ro-', markersize=3, linewidth=1.2)
                        ax5_twin.set_ylabel('누적 비율 (%)', color='red')
                        ax5_twin.tick_params(axis='y', labelcolor='red')
                        ax5_twin.set_ylim(0, 110)
                    except:
                        pass
                else:
                    ax5.text(0.5, 0.5, '개선 효과(+) 필터 없음', ha='center', va='center',
                             fontsize=12, transform=ax5.transAxes)
                    ax5.axis('off')
            else:
                ax5.text(0.5, 0.5, '필터 결과 컬럼 누락', ha='center', va='center',
                         fontsize=12, transform=ax5.transAxes)
                ax5.axis('off')
        else:
            ax5.text(0.5, 0.5, '필터 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax5.transAxes)
            ax5.axis('off')

        # ============ Chart 6-8: 필터 개선 핵심 보조 지표 ============
        # Chart 6: 기간별 안정성(일관성) Top
        ax6 = fig.add_subplot(gs[2, 0])
        if filter_stability and len(filter_stability) > 0:
            top_stable = sorted(filter_stability, key=lambda x: x.get('일관성점수', 0), reverse=True)[:10]
            names = [str(x.get('필터명', ''))[:18] for x in top_stable]
            scores = [x.get('일관성점수', 0) for x in top_stable]
            colors = []
            for x in top_stable:
                grade = x.get('안정성등급', '')
                if grade == '안정':
                    colors.append(color_profit)
                elif grade == '보통':
                    colors.append('#F1C40F')
                else:
                    colors.append(color_loss)

            y_pos = range(len(names))
            ax6.barh(y_pos, scores, color=colors, edgecolor='black', linewidth=0.5)
            ax6.set_yticks(y_pos)
            ax6.set_yticklabels(names, fontsize=8)
            ax6.set_xlabel('일관성점수(0-100)')
            ax6.set_title('필터 안정성 Top 10')
            ax6.invert_yaxis()
            for i, item in enumerate(top_stable):
                avg_imp = item.get('평균개선', 0)
                ax6.text(scores[i] + 1, i, f"+{avg_imp/10000:.0f}만", va='center', fontsize=7)
        else:
            ax6.text(0.5, 0.5, '안정성 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax6.transAxes)
            ax6.axis('off')

        # Chart 7: 최적 임계값 요약 (Top)
        ax7 = fig.add_subplot(gs[2, 1])
        ax7.axis('off')
        if optimal_thresholds and len(optimal_thresholds) > 0:
            top_thr = optimal_thresholds[:8]
            table_data = []
            for t in top_thr:
                name = t.get('필터명') or str(t.get('column', ''))[:22]
                improvement = t.get('improvement', 0)
                excluded_ratio = t.get('excluded_ratio', 0)
                efficiency = t.get('efficiency', '')
                table_data.append([str(name)[:22], f"{int(improvement):,}", f"{excluded_ratio}", f"{efficiency}"])

            tbl = ax7.table(
                cellText=table_data,
                colLabels=['필터명', '개선(원)', '제외(%)', '효율'],
                loc='center'
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(7)
            tbl.scale(1, 1.4)
            ax7.set_title('최적 임계값 요약 (Top)', fontsize=10)
        else:
            ax7.text(0.5, 0.5, '임계값 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax7.transAxes)

        # Chart 8: 필터 조합 시너지 상위
        ax8 = fig.add_subplot(gs[2, 2])
        ax8.axis('off')
        if filter_combinations and len(filter_combinations) > 0:
            top_combo = sorted(filter_combinations, key=lambda x: x.get('시너지효과', 0), reverse=True)[:8]
            lines = []
            for c in top_combo:
                combo_type = c.get('조합유형', '')
                f1 = str(c.get('필터1', ''))[:14]
                f2 = str(c.get('필터2', ''))[:14]
                f3 = str(c.get('필터3', ''))[:14]
                if combo_type == '3개 조합' and f3:
                    name = f"{f1}+{f2}+{f3}"
                else:
                    name = f"{f1}+{f2}"
                lines.append(
                    f"- {name}: 시너지 {int(c.get('시너지효과', 0)):,}원 ({c.get('시너지비율', 0)}%)"
                )
            text = "\n".join(lines) if lines else '조합 분석 데이터 없음'
            ax8.text(0.02, 0.98, text, transform=ax8.transAxes, va='top', fontsize=8,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
            ax8.set_title('필터 조합 시너지 Top', fontsize=10)
        else:
            ax8.text(0.5, 0.5, '조합 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax8.transAxes)

        # ============ Chart 9: 거래품질점수별 수익금 ============
        ax9 = fig.add_subplot(gs[3, 0])
        if '거래품질점수' in df_tsg.columns:
            bins = [0, 30, 40, 50, 60, 70, 100]
            labels = ['~30', '30-40', '40-50', '50-60', '60-70', '70+']
            df_tsg['품질구간'] = pd.cut(df_tsg['거래품질점수'], bins=bins, labels=labels, right=False)
            df_qual = df_tsg.groupby('품질구간', observed=True).agg({'수익금': 'sum', '종목명': 'count'}).reset_index()
            df_qual.columns = ['품질구간', '수익금', '거래수']
            colors = [color_profit if x >= 0 else color_loss for x in df_qual['수익금']]
            bars = ax9.bar(range(len(df_qual)), df_qual['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax9.set_xticks(range(len(df_qual)))
            ax9.set_xticklabels(df_qual['품질구간'], rotation=45)
            ax9.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax9.set_xlabel('거래품질 점수')
            ax9.set_ylabel('총 수익금')
            ax9.set_title('거래품질 점수별 수익금 (NEW)')

            # 거래수 표시
            for i, (bar, cnt) in enumerate(zip(bars, df_qual['거래수'])):
                ax9.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'n={cnt}', ha='center', va='bottom' if bar.get_height() >= 0 else 'top', fontsize=8)

        # ============ Chart 10: 매수 위험도점수별 수익금 ============
        ax10 = fig.add_subplot(gs[3, 1])
        if '위험도점수' in df_tsg.columns:
            # 동적 bins 생성: 데이터 분포에 기반
            risk_min = df_tsg['위험도점수'].min()
            risk_max = df_tsg['위험도점수'].max()
            if risk_max - risk_min > 50:
                bins = [0, 20, 40, 60, 80, 100]
            else:
                # 데이터 범위가 좁으면 더 세분화
                bins = list(range(int(risk_min), int(risk_max) + 20, 10))
                if bins[-1] < 100:
                    bins.append(100)
            labels = [f'{bins[i]}-{bins[i+1]}' for i in range(len(bins)-1)]
            df_tsg['위험도구간'] = pd.cut(df_tsg['위험도점수'], bins=bins, labels=labels, right=False)
            df_risk = df_tsg.groupby('위험도구간', observed=True).agg({'수익금': 'sum', '종목명': 'count'}).reset_index()
            df_risk.columns = ['위험도구간', '수익금', '거래수']
            colors = [color_profit if x >= 0 else color_loss for x in df_risk['수익금']]
            bars = ax10.bar(range(len(df_risk)), df_risk['수익금'], color=colors, edgecolor='black', linewidth=0.5)
            ax10.set_xticks(range(len(df_risk)))
            ax10.set_xticklabels(df_risk['위험도구간'], rotation=45)
            ax10.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax10.set_xlabel('매수 위험도 점수')
            ax10.set_ylabel('총 수익금')
            
            # 위험도 공식 표시 (매수 시점 기반 / 룩어헤드 제거)
            risk_formula = (
                "위험도(매수 시점) 공식:\n"
                "- 매수등락율>=20:+20, >=25:+10, >=30:+10\n"
                "- 매수체결강도<80:+15, <60:+10 | 과열>=150:+10, >=200:+10, >=250:+10\n"
                "- 거래대금(억=매수당일거래대금/100)<50:+15, <100:+10\n"
                "- 시총(억)<1000:+15, <5000:+10 | 호가잔량비<90:+10, <70:+15\n"
                "- 스프레드>=0.5:+10, >=1.0:+10 | 회전율<10:+5, <5:+10\n"
                "- 변동폭비율>=7.5:+10, >=10:+10, >=15:+10"
            )
            ax10.set_title(f'매수 위험도 점수별 수익금 (룩어헤드 없음)\n{risk_formula}', fontsize=8, loc='left')

        # ============ Chart 11: 리스크조정수익률 분포 ============
        ax11 = fig.add_subplot(gs[3, 2])
        if '리스크조정수익률' in df_tsg.columns:
            profit_trades = df_tsg[df_tsg['수익금'] > 0]['리스크조정수익률']
            loss_trades = df_tsg[df_tsg['수익금'] <= 0]['리스크조정수익률']

            ax11.hist(profit_trades, bins=30, alpha=0.6, color=color_profit, label='이익 거래', edgecolor='black')
            ax11.hist(loss_trades, bins=30, alpha=0.6, color=color_loss, label='손실 거래', edgecolor='black')
            ax11.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
            ax11.set_xlabel('리스크 조정 수익률')
            ax11.set_ylabel('거래 수')
            ax11.set_title('리스크 조정 수익률 분포 (NEW)')
            ax11.legend(fontsize=9)

        # ============ Chart 12: 필터 결과 요약 테이블 ============
        ax12 = fig.add_subplot(gs[4, :2])
        ax12.axis('off')
        if filter_results and len(filter_results) > 0:
            top_filters = [f for f in filter_results if f.get('수익개선금액', 0) > 0][:12]
            if not top_filters:
                top_filters = filter_results[:12]

            table_data = []
            for f in top_filters:
                name = str(f.get('필터명', ''))[:26]
                improvement = int(f.get('수익개선금액', 0) or 0)
                excluded = f.get('제외비율', '')
                p_value = f.get('p값', '')
                significant = f.get('유의함', '')
                effect_size = f.get('효과크기', '')
                recommend = str(f.get('적용권장', ''))
                table_data.append([
                    name,
                    f"{improvement:,}",
                    f"{excluded}",
                    f"{p_value}",
                    f"{significant}",
                    f"{effect_size}",
                    recommend
                ])

            tbl = ax12.table(
                cellText=table_data,
                colLabels=['필터명', '개선(원)', '제외(%)', 'p값', '유의', '효과(d)', '권장'],
                loc='center'
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(7)
            tbl.scale(1, 1.55)
            ax12.set_title('필터 결과 요약 (Top)', fontsize=11)

            try:
                for row_idx, f in enumerate(top_filters, start=1):
                    stars = str(f.get('적용권장', ''))
                    is_sig = str(f.get('유의함', '')) == '예'
                    if stars.count('★') >= 3:
                        row_color = '#E8F8F5'
                    elif is_sig:
                        row_color = '#FEF9E7'
                    else:
                        row_color = 'white'
                    for col_idx in range(7):
                        tbl[(row_idx, col_idx)].set_facecolor(row_color)
            except:
                pass
        else:
            ax12.text(0.5, 0.5, '필터 분석 결과 없음', ha='center', va='center',
                      fontsize=12, transform=ax12.transAxes)

        # ============ Chart 13: 자동 생성 조건식 요약 ============
        ax13 = fig.add_subplot(gs[4, 2])
        ax13.axis('off')
        if generated_code and generated_code.get('code_text'):
            summary = generated_code.get('summary', {}) or {}
            code_text = str(generated_code.get('code_text', '') or '')
            code_lines = [ln.rstrip() for ln in code_text.splitlines() if ln is not None]
            snippet = "\n".join(code_lines[:18])
            if len(code_lines) > 18:
                snippet += "\n..."

            header_lines = [
                "=== 자동 생성 코드 요약 ===",
                f"- 필터 수: {int(summary.get('total_filters', 0) or 0):,}",
                f"- 예상 총 개선(동시적용): {int(summary.get('total_improvement_combined', summary.get('total_improvement_naive', 0)) or 0):,}원",
                f"- 개별개선합/중복: {int(summary.get('total_improvement_naive', 0) or 0):,}원 / {int(summary.get('overlap_loss', 0) or 0):+,}원",
            ]
            categories = summary.get('categories') or []
            if categories:
                shown = ", ".join([str(x) for x in categories[:6]])
                header_lines.append(f"- 카테고리: {shown}" + (" ..." if len(categories) > 6 else ""))

            ax13.text(
                0.02, 0.98,
                "\n".join(header_lines) + "\n\n" + snippet,
                transform=ax13.transAxes,
                va='top',
                fontsize=8,
                family='monospace',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
            )
            ax13.set_title('조건식 코드 생성', fontsize=10)
        else:
            ax13.text(0.5, 0.5, '코드 생성 결과 없음', ha='center', va='center',
                      fontsize=12, transform=ax13.transAxes)

        # ============ Chart 14: 필터 조합 시너지 히트맵 (NEW) ============
        ax14 = fig.add_subplot(gs[5, 0])
        if filter_combinations and len(filter_combinations) > 0:
            filter_names, heatmap_matrix, annotations = CreateSynergyHeatmapData(
                filter_combinations, top_n=8
            )

            if filter_names is not None and heatmap_matrix is not None:
                vmin = float(np.nanmin(heatmap_matrix)) if np.isfinite(heatmap_matrix).any() else -100.0
                vmax = float(np.nanmax(heatmap_matrix)) if np.isfinite(heatmap_matrix).any() else 100.0
                vmin = min(vmin, -100.0)
                vmax = max(vmax, 100.0)
                im = ax14.imshow(heatmap_matrix, cmap='RdYlGn', aspect='auto',
                                vmin=vmin, vmax=vmax)
                ax14.set_xticks(range(len(filter_names)))
                ax14.set_yticks(range(len(filter_names)))
                ax14.set_xticklabels(filter_names, rotation=45, ha='right', fontsize=7)
                ax14.set_yticklabels(filter_names, fontsize=7)
                ax14.set_title('필터 조합 시너지 히트맵 (NEW)\n(음수=시너지↓, 양수=시너지↑)',
                              fontsize=9)

                # 값 표시
                for i in range(len(filter_names)):
                    for j in range(len(filter_names)):
                        if annotations[i][j]:
                            ax14.text(j, i, annotations[i][j], ha='center', va='center',
                                     fontsize=6,
                                     color='white' if abs(heatmap_matrix[i, j]) > 50 else 'black')

                plt.colorbar(im, ax=ax14, shrink=0.8, label='시너지비율(%)')
            else:
                ax14.text(0.5, 0.5, '조합 분석 데이터 없음', ha='center', va='center',
                         fontsize=12, transform=ax14.transAxes)
                ax14.axis('off')
        else:
            ax14.text(0.5, 0.5, '조합 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax14.transAxes)
            ax14.axis('off')

        # ============ Chart 15: 최적 임계값 효율성 곡선 (NEW) ============
        ax15 = fig.add_subplot(gs[5, 1])
        if optimal_thresholds and len(optimal_thresholds) > 0:
            curve_data = PrepareThresholdCurveData(optimal_thresholds, top_n=3)

            if curve_data:
                colors = ['#E74C3C', '#3498DB', '#2ECC71']
                for i, data in enumerate(curve_data):
                    color = colors[i % len(colors)]
                    # 제외비율 대비 효율성 곡선
                    ax15.plot(data['excluded_ratios'],
                             [e/1000000 for e in data['efficiencies']],
                             marker='o', markersize=3, label=data['column'][:12],
                             color=color, linewidth=1.5)
                    # 최적점 표시
                    opt_idx = _FindNearestIndex(data.get('thresholds', []), data.get('optimal_threshold'))
                    ax15.scatter(data['excluded_ratios'][opt_idx],
                                data['efficiencies'][opt_idx]/1000000,
                                s=100, marker='*', color=color, edgecolors='black',
                                zorder=5)

                ax15.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
                ax15.set_xlabel('제외 비율 (%)')
                ax15.set_ylabel('효율성 (백만원)')
                ax15.set_title('최적 임계값 효율성 곡선 (NEW)\n(★=최적점)', fontsize=9)
                ax15.legend(fontsize=7, loc='best')
                ax15.grid(True, alpha=0.3)
            else:
                ax15.text(0.5, 0.5, '임계값 분석 데이터 없음', ha='center', va='center',
                         fontsize=12, transform=ax15.transAxes)
                ax15.axis('off')
        else:
            ax15.text(0.5, 0.5, '임계값 분석 데이터 없음', ha='center', va='center',
                     fontsize=12, transform=ax15.transAxes)
            ax15.axis('off')

        # ============ Chart 16: 요약 통계 텍스트 ============
        ax16 = fig.add_subplot(gs[5, 2])
        ax16.axis('off')

        total_trades = len(df_tsg)
        total_profit = df_tsg['수익금'].sum()
        win_rate = (df_tsg['수익금'] > 0).mean() * 100
        avg_profit = df_tsg['수익률'].mean()

        summary_text = f"""
        === 분석 요약 ({tf_info['label']}) ===

        총 거래 수: {total_trades:,}
        총 수익금: {total_profit:,}원
        승률: {win_rate:.1f}%
        평균 수익률: {avg_profit:.2f}%

        === 주요 발견 ===
        """

        if filter_results:
            top_filter = filter_results[0] if filter_results else None
            if top_filter and top_filter['수익개선금액'] > 0:
                summary_text += f"""
        최적 필터: {top_filter['필터명'][:25]}
        예상 개선: {top_filter['수익개선금액']:,}원
        통계적 유의성: {top_filter.get('유의함', 'N/A')}
                """

        if feature_importance:
            top_feature = feature_importance['top_features'][0] if feature_importance.get('top_features') else None
            if top_feature:
                summary_text += f"""
        가장 중요한 변수: {top_feature[0]}
        중요도: {top_feature[1]:.3f}
                """

        # 최적 임계값 정보 추가
        if optimal_thresholds and len(optimal_thresholds) > 0:
            top_threshold = optimal_thresholds[0]
            summary_text += f"""
        === 최적 임계값 ===
        {top_threshold.get('필터명', 'N/A')}
        개선: {top_threshold.get('improvement', 0):,.0f}원
                """

        # 매수/매도 조건식(요약) 추가 (공부/검증 목적)
        try:
            if buystg or sellstg:
                sk = ComputeStrategyKey(buystg=buystg, sellstg=sellstg)
                sk_short = (str(sk)[:12] + '...') if sk else 'N/A'
                buy_block = _extract_strategy_block_lines(
                    buystg, start_marker='if 매수:', end_marker='if 매도:', max_lines=5
                )
                sell_block = _extract_strategy_block_lines(
                    sellstg, start_marker='if 매도:', end_marker=None, max_lines=5
                )

                summary_text += f"""
        === 조건식(요약) ===
        전략키: {sk_short}
        매수:
        """ + ("\n".join([f"        {ln}" for ln in buy_block]) if buy_block else "        (없음)") + """
        매도:
        """ + ("\n".join([f"        {ln}" for ln in sell_block]) if sell_block else "        (없음)")
        except Exception:
            pass

        ax16.text(0.1, 0.9, summary_text, transform=ax16.transAxes, fontsize=10,
                 verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        # ============ Chart 18: 자동 생성 필터 조합 적용 시 수익금 변화 (NEW) ============
        ax18 = fig.add_subplot(gs[6, :])
        if generated_code and generated_code.get('combine_steps') and '수익금' in df_tsg.columns:
            try:
                steps = generated_code.get('combine_steps') or []
                base_profit = float(pd.to_numeric(df_tsg['수익금'], errors='coerce').fillna(0).sum())

                labels = ['기준']
                cum_imp = [0.0]
                ex_pct = [0.0]
                for st in steps[:8]:
                    labels.append(str(st.get('필터명', ''))[:16])
                    cum_imp.append(float(st.get('누적개선(동시적용)', 0) or 0))
                    ex_pct.append(float(st.get('누적제외비율', 0) or 0))

                x = list(range(len(labels)))
                profit_after = [base_profit + v for v in cum_imp]

                ax18.plot(x, profit_after, 'o-', color=color_profit, linewidth=2.2, markersize=5, label='예상 수익금(원)')
                ax18.axhline(y=base_profit, color='gray', linestyle='--', linewidth=0.8, alpha=0.8)
                ax18.set_xticks(x)
                ax18.set_xticklabels(labels, rotation=20, ha='right', fontsize=9)
                ax18.set_ylabel('예상 수익금(원)')
                ax18.set_title('자동 생성 필터 조합 적용 시 예상 수익금 변화\n(누적개선=동시 적용/중복 반영, 단계별 제외비율 함께 표시)', fontsize=11)
                ax18.grid(axis='y', alpha=0.4)

                ax18_t = ax18.twinx()
                ax18_t.plot(x, ex_pct, 's--', color='red', linewidth=1.6, markersize=4, label='누적 제외(%)')
                ax18_t.set_ylabel('누적 제외 비율(%)', color='red')
                ax18_t.tick_params(axis='y', labelcolor='red')
                ax18_t.set_ylim(0, min(100, max(ex_pct) * 1.2 + 5))

                # 값 라벨
                for xi, p in zip(x, profit_after):
                    ax18.text(xi, p, f"{int(p):,}", fontsize=8, ha='center', va='bottom')
            except Exception:
                ax18.text(0.5, 0.5, '필터 조합 변화 그래프 생성 실패', ha='center', va='center',
                          fontsize=12, transform=ax18.transAxes)
                ax18.axis('off')
        else:
            ax18.text(0.5, 0.5, '자동 생성 코드(combine_steps) 또는 수익금 컬럼 없음', ha='center', va='center',
                      fontsize=12, transform=ax18.transAxes)
            ax18.axis('off')

        # ============ Chart 17: (진단용) 룩어헤드 포함 필터 효과 Top ============
        ax17 = fig.add_subplot(gs[7, :])
        if filter_results_lookahead and len(filter_results_lookahead) > 0:
            top_15 = [f for f in filter_results_lookahead if f.get('수익개선금액', 0) > 0][:15]
            if top_15:
                names = [str(f.get('필터명', ''))[:26] for f in top_15]
                improvements = [int(f.get('수익개선금액', 0)) for f in top_15]

                y_pos = range(len(names))
                ax17.barh(y_pos, improvements, color='#F39C12', alpha=0.85, edgecolor='black', linewidth=0.5)
                ax17.set_yticks(y_pos)
                ax17.set_yticklabels(names, fontsize=9)
                ax17.set_xlabel('수익 개선 금액(원)')
                ax17.set_title('사후진단(룩어헤드) Top 15 필터 효과\n※ 매도 확정 정보 포함 → 실거래/자동 조건식에는 사용 금지', fontsize=11)
                ax17.invert_yaxis()

                # 값/제외비율 표시
                max_val = max(improvements) if improvements else 0
                for i, f in enumerate(top_15):
                    v = int(f.get('수익개선금액', 0))
                    ex = f.get('제외비율', 0)
                    ax17.text(v + max_val * 0.01, i, f"{v:,}원 (제외 {ex}%)", va='center', fontsize=8)
            else:
                ax17.text(0.5, 0.5, '사후진단 결과(양수 개선) 없음', ha='center', va='center',
                          fontsize=12, transform=ax17.transAxes)
                ax17.axis('off')
        else:
            ax17.text(0.5, 0.5, '사후진단(룩어헤드) 분석 데이터 없음', ha='center', va='center',
                      fontsize=12, transform=ax17.transAxes)
            ax17.axis('off')

        # 저장 및 전송
        # tight_layout은 colorbar/그리드와 함께 경고가 자주 발생하여(subplot 배치가 깨질 수 있음),
        # 고정 margins로 레이아웃을 안정화합니다.
        fig.subplots_adjust(left=0.05, right=0.98, bottom=0.04, top=0.94, hspace=0.55, wspace=0.3)
        output_dir = ensure_backtesting_output_dir(save_file_name)
        analysis_path = str(output_dir / f"{save_file_name}_enhanced.png")
        plt.savefig(analysis_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        if teleQ is not None:
            teleQ.put(analysis_path)

        return analysis_path

    except Exception as e:
        print_exc()
        try:
            plt.close('all')
        except:
            pass
        return None


# ============================================================================
# 10. 전체 강화 분석 실행
# ============================================================================

def RunEnhancedAnalysis(df_tsg, save_file_name, teleQ=None, buystg=None, sellstg=None,
                        buystg_name=None, sellstg_name=None, backname=None,
                        ml_train_mode: str = 'train', send_condition_summary: bool = True,
                        segment_analysis_mode: str = 'off',
                        segment_output_dir: str | None = None,
                        segment_optuna: bool = False,
                        segment_template_compare: bool = False):
    """
    강화된 전체 분석을 실행합니다.

    기능:
    1. 강화된 파생 지표 계산
    2. 통계적 유의성 검증 포함 필터 분석
    3. 최적 임계값 탐색
    4. 필터 조합 분석
    5. ML 기반 특성 중요도
    6. 기간별 필터 안정성
    7. 조건식 코드 자동 생성
    8. 강화된 시각화
    9. 세그먼트 분석(Phase2/3) 통합(옵션)

    Returns:
        dict: 분석 결과 요약
    """
    result = {
        'enhanced_df': None,
        'filter_results': [],
        'filter_results_lookahead': [],
        'optimal_thresholds': [],
        'filter_combinations': [],
        'feature_importance': None,
        'filter_stability': [],
        'generated_code': None,
        'charts': [],
        'recommendations': [],
        'csv_files': [],
        'ml_prediction_stats': None,  # NEW: ML 예측 통계
        'ml_reliability': None,       # NEW: ML 신뢰도/게이트 결과
        'segment_outputs': None,      # NEW: 세그먼트 분석 산출물
    }

    try:
        # 1. 강화된 파생 지표 계산
        df_enhanced = CalculateEnhancedDerivedMetrics(df_tsg)
        
        # 1.5. ML 기반 위험도 예측 (NEW)
        # - 손실확률_ML: ML이 예측한 손실 확률 (0~1)
        # - 위험도_ML: ML 기반 위험도 점수 (0~100)
        # - 예측매수매도위험도점수_ML: 매수 시점 변수로 예측한 매수매도위험도점수(0~100)
        # - detail.csv에 추가하여 실제 매수매도위험도점수와 비교 가능
        df_enhanced, ml_prediction_stats = PredictRiskWithML(
            df_enhanced,
            save_file_name=save_file_name,
            buystg=buystg,
            sellstg=sellstg,
            train_mode=ml_train_mode
        )
        result['ml_prediction_stats'] = ml_prediction_stats

        ml_reliability = AssessMlReliability(ml_prediction_stats)
        result['ml_reliability'] = ml_reliability
        allow_ml_filters = bool((ml_reliability or {}).get('allow_ml_filters', False))
        try:
            if isinstance(ml_prediction_stats, dict):
                ml_prediction_stats['reliability'] = ml_reliability
        except Exception:
            pass
        
        result['enhanced_df'] = df_enhanced

        # 2. 강화된 필터 효과 분석 (통계 검정 포함)
        filter_results = AnalyzeFilterEffectsEnhanced(df_enhanced, allow_ml_filters=allow_ml_filters)
        result['filter_results'] = filter_results

        # 2-1. (진단용) 룩어헤드 포함 필터 효과 분석
        filter_results_lookahead = AnalyzeFilterEffectsLookahead(df_enhanced)
        result['filter_results_lookahead'] = filter_results_lookahead

        # 3. 최적 임계값 탐색
        optimal_thresholds = FindAllOptimalThresholds(df_enhanced)
        result['optimal_thresholds'] = optimal_thresholds

        # 4. 필터 조합 분석 (단일 필터 결과 재사용으로 중복 계산 제거)
        filter_combinations = AnalyzeFilterCombinations(df_enhanced, single_filters=filter_results)
        result['filter_combinations'] = filter_combinations

        # 5. ML 특성 중요도
        feature_importance = AnalyzeFeatureImportance(df_enhanced)
        result['feature_importance'] = feature_importance

        # 6. 필터 안정성 검증
        filter_stability = AnalyzeFilterStability(df_enhanced)
        result['filter_stability'] = filter_stability

        # 7. 조건식 코드 생성
        generated_code = GenerateFilterCode(filter_results, df_tsg=df_enhanced, allow_ml_filters=allow_ml_filters)
        result['generated_code'] = generated_code

        # 8. CSV 파일 저장
        # 상세 거래 기록 (강화 분석 사용 시: detail.csv로 통합하여 중복 생성 방지)
        # - 손실확률_ML, 위험도_ML, 예측매수매도위험도점수_ML 컬럼이 포함되어 비교 가능
        output_dir = ensure_backtesting_output_dir(save_file_name)
        detail_path = str(output_dir / f"{save_file_name}_detail.csv")
        df_enhanced_out = reorder_detail_columns(df_enhanced)
        df_enhanced_out.to_csv(detail_path, encoding='utf-8-sig', index=True)
        result['csv_files'].append(detail_path)

        # 필터 분석 결과
        if filter_results:
            # 강화 분석 사용 시: filter.csv로 통합하여 중복 생성 방지
            filter_path = str(output_dir / f"{save_file_name}_filter.csv")
            pd.DataFrame(filter_results).to_csv(filter_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(filter_path)

        # (진단용) 룩어헤드 포함 필터 분석 결과
        if filter_results_lookahead:
            lookahead_path = str(output_dir / f"{save_file_name}_filter_lookahead.csv")
            pd.DataFrame(filter_results_lookahead).to_csv(lookahead_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(lookahead_path)

        # 최적 임계값
        if optimal_thresholds:
            threshold_path = str(output_dir / f"{save_file_name}_optimal_thresholds.csv")
            pd.DataFrame(optimal_thresholds).to_csv(threshold_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(threshold_path)

        # 필터 조합
        if filter_combinations:
            combo_path = str(output_dir / f"{save_file_name}_filter_combinations.csv")
            df_combo = pd.DataFrame(filter_combinations)
            if '조합개선' in df_combo.columns:
                sort_cols = ['조합개선']
                sort_asc = [False]
                if '시너지효과' in df_combo.columns:
                    sort_cols.append('시너지효과')
                    sort_asc.append(False)
                df_combo = df_combo.sort_values(sort_cols, ascending=sort_asc)

            df_combo = df_combo.rename(columns={
                '조합유형': '조합유형(필터개수)',
                '개별개선합': '개별개선합(원=각필터단독개선합)',
                '조합개선': '조합개선(원=조합적용개선금액)',
                '시너지효과': '시너지효과(원=조합개선-개별개선합)',
                '시너지비율': '시너지비율(%=시너지효과/개별개선합)',
                '제외비율': '제외비율(%=조합적용시제외)',
                '잔여승률': '잔여승률(%=조합적용후)',
                '잔여거래수': '잔여거래수(건)',
                '권장': '권장(시너지기준)'
            })

            df_combo.to_csv(combo_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(combo_path)

        # 필터 안정성
        if filter_stability:
            stability_path = str(output_dir / f"{save_file_name}_filter_stability.csv")
            pd.DataFrame(filter_stability).to_csv(stability_path, encoding='utf-8-sig', index=False)
            result['csv_files'].append(stability_path)

        # 9. 강화된 차트 생성
        chart_path = PltEnhancedAnalysisCharts(
            df_enhanced,
            save_file_name,
            teleQ,
            filter_results=filter_results,
            filter_results_lookahead=filter_results_lookahead,
            feature_importance=feature_importance,
            optimal_thresholds=optimal_thresholds,
            filter_combinations=filter_combinations,
            filter_stability=filter_stability,
            generated_code=generated_code,
            buystg=buystg,
            sellstg=sellstg
        )
        if chart_path:
            result['charts'].append(chart_path)

        # 9-1. 세그먼트 분석(옵션)
        segment_outputs = None
        if segment_analysis_mode and str(segment_analysis_mode).lower() not in ('off', 'false', 'none'):
            try:
                from backtester.segment_analysis.phase2_runner import run_phase2, Phase2RunnerConfig
                from backtester.segment_analysis.phase3_runner import run_phase3, Phase3RunnerConfig
                from backtester.segment_analysis.filter_evaluator import FilterEvaluatorConfig
                from backtester.segment_analysis.segment_template_comparator import (
                    run_segment_template_comparison,
                    SegmentTemplateComparisonConfig,
                )

                mode = str(segment_analysis_mode).lower()
                segment_output_base = segment_output_dir or str(output_dir)
                filter_config = FilterEvaluatorConfig(allow_ml_filters=allow_ml_filters)
                segment_outputs = {}
                segment_timing = {}
                segment_start = time.perf_counter()

                if mode in ('phase2', 'phase2+3', 'phase2_phase3', 'all', 'auto'):
                    t0 = time.perf_counter()
                    segment_outputs['phase2'] = run_phase2(
                        detail_path,
                        filter_config=filter_config,
                        runner_config=Phase2RunnerConfig(
                            output_dir=segment_output_base,
                            prefix=save_file_name,
                            enable_optuna=segment_optuna
                        )
                    )
                    segment_timing['phase2_s'] = round(time.perf_counter() - t0, 4)

                if mode in ('phase3', 'phase2+3', 'phase2_phase3', 'all', 'auto'):
                    t0 = time.perf_counter()
                    segment_outputs['phase3'] = run_phase3(
                        detail_path,
                        filter_config=filter_config,
                        runner_config=Phase3RunnerConfig(
                            output_dir=segment_output_base,
                            prefix=save_file_name
                        )
                    )
                    segment_timing['phase3_s'] = round(time.perf_counter() - t0, 4)

                if segment_template_compare and mode in ('phase2', 'phase2+3', 'phase2_phase3', 'all', 'auto', 'compare', 'template'):
                    t0 = time.perf_counter()
                    segment_outputs['template_comparison'] = run_segment_template_comparison(
                        detail_path,
                        filter_config=filter_config,
                        runner_config=SegmentTemplateComparisonConfig(
                            output_dir=segment_output_base,
                            prefix=save_file_name,
                            max_templates=4,
                            top_n_dynamic=1,
                            enable_dynamic_expansion=True,
                            enable_optuna=segment_optuna,
                        ),
                    )
                    segment_timing['template_s'] = round(time.perf_counter() - t0, 4)

                segment_timing['total_s'] = round(time.perf_counter() - segment_start, 4)
                segment_outputs['timing'] = segment_timing

                try:
                    from backtester.segment_analysis.segment_summary_report import write_segment_summary_report

                    summary_path = write_segment_summary_report(
                        segment_output_base,
                        save_file_name,
                        segment_outputs,
                    )
                    if summary_path:
                        segment_outputs['summary_report_path'] = summary_path
                except Exception:
                    print_exc()
            except Exception:
                print_exc()

        result['segment_outputs'] = segment_outputs

        # 10. 추천 메시지 생성
        recommendations = []

        # 통계적으로 유의한 필터
        filter_results_safe = filter_results or []
        filter_combinations_safe = filter_combinations or []
        filter_stability_safe = filter_stability or []

        significant_filters = [
            f for f in filter_results_safe
            if f.get('유의함') == '예' and float(f.get('수익개선금액', 0) or 0) > 0
        ][:3]
        for f in significant_filters:
            try:
                recommendations.append(
                    f"[통계적 유의] {f.get('필터명', '')}: +{int(f.get('수익개선금액', 0) or 0):,}원 (p={f.get('p값', 'N/A')})"
                )
            except Exception:
                continue

        # 시너지 높은 조합
        high_synergy = [c for c in filter_combinations_safe if float(c.get('시너지비율', 0) or 0) > 10][:2]
        for c in high_synergy:
            try:
                recommendations.append(
                    f"[조합추천] {str(c.get('필터1', ''))[:15]} + {str(c.get('필터2', ''))[:15]}: "
                    f"시너지 +{int(c.get('시너지효과', 0) or 0):,}원"
                )
            except Exception:
                continue

        # 안정적인 필터
        stable_filters = [
            f for f in filter_stability_safe
            if f.get('안정성등급') == '안정' and float(f.get('평균개선', 0) or 0) > 0
        ][:2]
        for f in stable_filters:
            try:
                recommendations.append(
                    f"[안정성] {f.get('필터명', '')}: 일관성 {f.get('일관성점수', 'N/A')}점"
                )
            except Exception:
                continue

        result['recommendations'] = recommendations

        # 11. 텔레그램 전송
        if teleQ is not None:
            def _safe_put(text: str):
                try:
                    teleQ.put(text)
                except Exception:
                    pass

            # 매수/매도 조건식(이름만)
            if send_condition_summary:
                try:
                    if buystg_name or sellstg_name or buystg or sellstg:
                        sk = None
                        try:
                            if isinstance(ml_prediction_stats, dict):
                                sk = ml_prediction_stats.get('strategy_key')
                        except Exception:
                            sk = None
                        if not sk:
                            sk = ComputeStrategyKey(buystg=buystg, sellstg=sellstg)

                        sk_short = (str(sk)[:12] + '...') if sk else 'N/A'
                        is_opt = bool(backname and ('최적화' in str(backname)))
                        buy_label = "매수 최적화 조건식" if is_opt else "매수 조건식"
                        sell_label = "매도 최적화 조건식" if is_opt else "매도 조건식"

                        buy_name = buystg_name if buystg_name else 'N/A'
                        sell_name = sellstg_name if sellstg_name else 'N/A'

                        lines = []
                        lines.append("매수/매도 조건식(이름):")
                        lines.append(f"- 전략키: {sk_short}")
                        lines.append(f"- {buy_label}: {buy_name}")
                        lines.append(f"- {sell_label}: {sell_name}")
                        lines.append("- 전체 원문/산출물 목록은 report.txt 및 models/strategy_code.txt 참고")
                        _safe_put("\n".join(lines))
                except Exception:
                    pass

            # ML 예측 통계 메시지 (NEW)
            if ml_prediction_stats:
                ml_lines = []
                ml_lines.append("머신러닝 변수 예측 결과:")
                ml_lines.append(f"- 모델: {ml_prediction_stats.get('model_type', 'N/A')}")
                ml_lines.append(
                    f"- 테스트(AUC/F1/BA): "
                    f"{ml_prediction_stats.get('test_auc', 'N/A')}% / "
                    f"{ml_prediction_stats.get('test_f1', 'N/A')}% / "
                    f"{ml_prediction_stats.get('test_balanced_accuracy', 'N/A')}%"
                )
                ml_lines.append(f"- 사용 피처: {ml_prediction_stats.get('total_features', 0)}개")
                ml_lines.append("- 예측 변수: 손실확률_ML, 위험도_ML, 예측매수매도위험도점수_ML")

                # 소요 시간(학습/예측/저장) 요약
                try:
                    tinfo = ml_prediction_stats.get('timing') if isinstance(ml_prediction_stats, dict) else None
                    if isinstance(tinfo, dict):
                        def _fmt_sec(v):
                            try:
                                return f"{float(v):.2f}s"
                            except Exception:
                                return str(v)

                        total_s = tinfo.get('total_s')
                        parts = []
                        if tinfo.get('load_latest_s') is not None:
                            parts.append(f"load { _fmt_sec(tinfo.get('load_latest_s')) }")
                        if tinfo.get('train_classifiers_s') is not None:
                            parts.append(f"train { _fmt_sec(tinfo.get('train_classifiers_s')) }")
                        if tinfo.get('predict_all_s') is not None:
                            parts.append(f"predict { _fmt_sec(tinfo.get('predict_all_s')) }")
                        if tinfo.get('save_bundle_s') is not None:
                            parts.append(f"save { _fmt_sec(tinfo.get('save_bundle_s')) }")
                        if total_s is not None:
                            if parts:
                                ml_lines.append(f"- 소요 시간: {_fmt_sec(total_s)} ({', '.join(parts)})")
                            else:
                                ml_lines.append(f"- 소요 시간: {_fmt_sec(total_s)}")
                except Exception:
                    pass

                # ML 신뢰도(게이트) 결과: 기준 미달이면 *_ML 필터 자동 생성/추천에서 제외
                try:
                    rel = None
                    if isinstance(ml_prediction_stats, dict):
                        rel = ml_prediction_stats.get('reliability')
                    if not isinstance(rel, dict):
                        rel = result.get('ml_reliability') if isinstance(result, dict) else None
                    if isinstance(rel, dict):
                        allow_ml = bool(rel.get('allow_ml_filters', False))
                        crit = rel.get('criteria') or {}
                        crit_txt = (
                            f"AUC≥{crit.get('min_test_auc')}%, "
                            f"F1≥{crit.get('min_test_f1')}%, "
                            f"BA≥{crit.get('min_test_balanced_accuracy')}%"
                        )
                        ml_lines.append(f"- 신뢰도 판정: {'PASS' if allow_ml else 'FAIL'} ({crit_txt})")
                        if not allow_ml:
                            reasons = rel.get('reasons') or []
                            for r in reasons[:2]:
                                ml_lines.append(f"  - {r}")
                            ml_lines.append("- *_ML 기반 필터: 자동 생성/추천에서 제외됨")
                except Exception:
                    pass
                 
                # 상관관계 정보
                corr_actual = ml_prediction_stats.get('correlation_with_actual_risk')
                corr_rule = ml_prediction_stats.get('correlation_with_rule_risk')
                if corr_actual is not None:
                    ml_lines.append(f"- 실제 매수매도위험도 상관: {corr_actual}%")
                if corr_rule is not None:
                    ml_lines.append(f"- 규칙기반 위험도점수 상관: {corr_rule}%")

                # 매수매도위험도 회귀 예측(룩어헤드 위험도 점수 근사)
                risk_reg = ml_prediction_stats.get('risk_regression') if isinstance(ml_prediction_stats, dict) else None
                if isinstance(risk_reg, dict) and risk_reg.get('best_model'):
                    corr_txt = f", 상관 {risk_reg.get('test_corr')}%" if risk_reg.get('test_corr') is not None else ""
                    ml_lines.append(
                        f"- 매수매도위험도 예측(회귀): MAE {risk_reg.get('test_mae', 'N/A')}점, "
                        f"R2 {risk_reg.get('test_r2', 'N/A')}{corr_txt} ({risk_reg.get('best_model')})"
                    )

                # 모델 저장 정보
                artifacts = ml_prediction_stats.get('artifacts') if isinstance(ml_prediction_stats, dict) else None
                if isinstance(artifacts, dict):
                    sk = ml_prediction_stats.get('strategy_key') or artifacts.get('strategy_key')
                    sk_short = (str(sk)[:12] + '...') if sk else 'N/A'
                    if artifacts.get('saved'):
                        ml_lines.append(f"- 모델 저장: 성공 (전략키 {sk_short})")
                        p = artifacts.get('latest_bundle_path') or artifacts.get('run_bundle_path')
                        if p:
                            try:
                                ml_lines.append(f"- 모델 파일: {Path(p).name}")
                            except Exception:
                                pass
                    else:
                        err = artifacts.get('error')
                        ml_lines.append(f"- 모델 저장: 실패/미수행 ({err})" if err else "- 모델 저장: 실패/미수행")
                
                # 주요 피처
                top_features = ml_prediction_stats.get('top_features', [])[:5]
                if top_features:
                    ml_lines.append("- 주요 피처(중요도):")
                    for feat, imp in top_features:
                        ml_lines.append(f"  - {feat}: {imp:.3f}")
                
                ml_lines.append("- detail.csv에 '손실확률_ML', '위험도_ML', '예측매수매도위험도점수_ML' 컬럼 추가됨")
                
                _safe_put("\n".join(ml_lines))

            # 요약 메시지
            if recommendations:
                msg = "강화된 필터 분석 결과:\n\n" + "\n".join(recommendations)
                _safe_put(msg)
            else:
                # 추천 메시지가 비어 있어도 "왜 비었는지" 요약을 보내도록 보강
                try:
                    pos_filters = sum(1 for f in filter_results_safe if float(f.get('수익개선금액', 0) or 0) > 0)
                    sig_pos_filters = sum(
                        1 for f in filter_results_safe
                        if f.get('유의함') == '예' and float(f.get('수익개선금액', 0) or 0) > 0
                    )
                except Exception:
                    pos_filters = 0
                    sig_pos_filters = 0

                msg = (
                    "강화된 필터 분석 결과:\n"
                    "- 추천 조건을 만족하는 항목이 없어 요약만 전송합니다.\n"
                    f"- 필터 결과: 총 {len(filter_results_safe):,}개 (개선(+) {pos_filters:,}개, 유의(+) {sig_pos_filters:,}개)\n"
                    f"- 조합 분석: {len(filter_combinations_safe):,}개\n"
                    f"- 안정성 분석: {len(filter_stability_safe):,}개\n"
                    f"- 코드 생성: {'가능' if (generated_code and generated_code.get('summary')) else '불가'}"
                )
                _safe_put(msg)

            # 조건식 코드
            if generated_code and generated_code.get('summary'):
                summary = generated_code.get('summary', {})
                total_filters = int(summary.get('total_filters', 0))
                total_impr = int(summary.get('total_improvement_combined', summary.get('total_improvement_naive', 0)))
                naive_impr = int(summary.get('total_improvement_naive', total_impr))
                overlap_loss = int(summary.get('overlap_loss', naive_impr - total_impr))
                allow_ml_filters_summary = summary.get('allow_ml_filters')
                excluded_ml_filters_summary = int(summary.get('excluded_ml_filters', 0) or 0)
 
                lines = []
                lines.append("자동 생성 필터 코드(요약):")
                lines.append(f"- 총 {total_filters}개 필터 (조합: AND, 즉 '모든 조건을 만족해야 매수')")
                lines.append(f"- 예상 총 개선(동시 적용/중복 반영): {total_impr:,}원")
                if total_filters > 0:
                    lines.append(f"- 개별개선합(단순 합산): {naive_impr:,}원, 중복/상쇄: {overlap_loss:+,}원")
                if allow_ml_filters_summary is not None:
                    lines.append(
                        f"- ML 필터 사용: {'허용' if bool(allow_ml_filters_summary) else '금지'}"
                        + (f" (제외 {excluded_ml_filters_summary}개)" if excluded_ml_filters_summary > 0 else "")
                    )
 
                steps = generated_code.get('combine_steps') or []
                if steps:
                    lines.append("- 적용 순서(추가개선→누적개선, 누적수익금, 누적제외%):")
                    for st in steps[: min(8, len(steps))]:
                        cum_profit_val = st.get('누적수익금')
                        cum_profit_text = f"{int(cum_profit_val):,}원" if cum_profit_val is not None else "N/A"
                        lines.append(
                            f"  {st.get('순서', '')}. {str(st.get('필터명', ''))[:18]}: "
                            f"+{int(st.get('추가개선(중복반영)', 0)):,} → 누적 +{int(st.get('누적개선(동시적용)', 0)):,} "
                            f"(누적 수익금 {cum_profit_text}) "
                            f"(제외 {st.get('누적제외비율', 0)}%)"
                        )

                buy_lines = generated_code.get('buy_conditions') or []
                if buy_lines:
                    lines.append("- 조합 코드(기존 매수조건에 AND 추가):")
                    for l in buy_lines[: min(8, len(buy_lines))]:
                        lines.append(f"  {l.strip()}")
                    lines.append("- 전체 설명/코드/산출물 목록은 report.txt 참고")

                _safe_put("\n".join(lines))
            else:
                # 코드가 생성되지 않더라도 원인을 파악할 수 있도록 요약 메시지 전송
                try:
                    candidate_count = sum(
                        1 for f in filter_results_safe
                        if float(f.get('수익개선금액', 0) or 0) > 0 and f.get('적용코드') and f.get('조건식')
                    )
                    pos_count = sum(1 for f in filter_results_safe if float(f.get('수익개선금액', 0) or 0) > 0)
                except Exception:
                    candidate_count = 0
                    pos_count = 0

                msg = (
                    "자동 생성 필터 코드(요약):\n"
                    "- 생성 불가 또는 후보 없음\n"
                    f"- 개선(+) 필터: {pos_count:,}개\n"
                    f"- 코드 생성 후보(개선(+) + 적용코드 + 조건식): {candidate_count:,}개\n"
                    "- filter.csv를 확인해 적용코드/조건식 유무를 점검하세요."
                )
                _safe_put(msg)

            # 세그먼트 분석 리포트(옵션)
            segment_outputs = result.get('segment_outputs') if isinstance(result, dict) else None
            if segment_outputs:
                try:
                    seg_lines = ["세그먼트 분석 결과:"]
                    phase2 = segment_outputs.get('phase2') or {}
                    phase3 = segment_outputs.get('phase3') or {}
                    template_comp = segment_outputs.get('template_comparison') or {}
                    timing = segment_outputs.get('timing') or {}

                    code_summary = phase2.get('segment_code_summary') or {}
                    if code_summary:
                        seg_lines.append(
                            f"- 조건식 요약: {code_summary.get('segments', 0)}구간, "
                            f"필터 {code_summary.get('filters', 0)}개"
                        )

                    combo_path = phase2.get('global_combo_path')
                    if combo_path and Path(combo_path).exists():
                        try:
                            df_combo = pd.read_csv(combo_path, encoding='utf-8-sig')
                            if not df_combo.empty:
                                row = df_combo.iloc[0]
                                total_impr = int(row.get('total_improvement', 0) or 0)
                                remaining_trades = int(row.get('remaining_trades', 0) or 0)
                                remaining_ratio = float(row.get('remaining_ratio', 0) or 0)
                                seg_lines.append(
                                    f"- 전역 조합 개선: {total_impr:+,}원, "
                                    f"잔여 {remaining_trades:,}건 ({remaining_ratio * 100:.1f}%)"
                                )
                        except Exception:
                            pass

                    summary_path = phase3.get('summary_path') or phase2.get('summary_path')
                    if summary_path and Path(summary_path).exists():
                        try:
                            df_summary = pd.read_csv(summary_path, encoding='utf-8-sig')
                            if not df_summary.empty and 'trades' in df_summary.columns:
                                total_trades = int(df_summary['trades'].sum())
                                out_row = df_summary[df_summary['segment_id'] == 'Out_of_Range']
                                if not out_row.empty and total_trades > 0:
                                    out_trades = int(out_row.iloc[0].get('trades', 0) or 0)
                                    seg_lines.append(
                                        f"- 구간 외 거래: {out_trades:,}건 ({out_trades / total_trades * 100:.1f}%)"
                                    )
                                if 'profit' in df_summary.columns:
                                    df_main = df_summary[df_summary['segment_id'] != 'Out_of_Range']
                                    top_rows = df_main.sort_values('profit', ascending=False).head(2)
                                    if not top_rows.empty:
                                        tops = []
                                        for _, row in top_rows.iterrows():
                                            seg_id = row.get('segment_id')
                                            profit = int(row.get('profit', 0) or 0)
                                            if seg_id:
                                                tops.append(f"{seg_id}({profit:,}원)")
                                        if tops:
                                            seg_lines.append("- 상위 세그먼트: " + ", ".join(tops))
                        except Exception:
                            pass

                    comp_path = template_comp.get('comparison_path')
                    if comp_path and Path(comp_path).exists():
                        try:
                            df_comp = pd.read_csv(comp_path, encoding='utf-8-sig')
                            if not df_comp.empty:
                                df_rank = df_comp.copy()
                                if 'score' in df_rank.columns:
                                    df_rank = df_rank.sort_values(['score'], ascending=[False])
                                best = df_rank.iloc[0]
                                seg_lines.append(
                                    f"- 템플릿 비교: {Path(comp_path).name} (최상: {best.get('template', 'N/A')})"
                                )
                        except Exception:
                            seg_lines.append(f"- 템플릿 비교: {Path(comp_path).name}")

                    summary_path = segment_outputs.get('summary_report_path')
                    if summary_path:
                        try:
                            seg_lines.append(f"- 종합 요약: {Path(summary_path).name}")
                        except Exception:
                            seg_lines.append(f"- 종합 요약: {summary_path}")

                    if timing:
                        def _fmt_sec(v):
                            try:
                                return f"{float(v):.2f}s"
                            except Exception:
                                return str(v)

                        total_s = timing.get('total_s')
                        parts = []
                        if timing.get('phase2_s') is not None:
                            parts.append(f"phase2 {_fmt_sec(timing.get('phase2_s'))}")
                        if timing.get('phase3_s') is not None:
                            parts.append(f"phase3 {_fmt_sec(timing.get('phase3_s'))}")
                        if timing.get('template_s') is not None:
                            parts.append(f"template {_fmt_sec(timing.get('template_s'))}")
                        if total_s is not None:
                            if parts:
                                seg_lines.append(f"- 세그먼트 분석 소요 시간: {_fmt_sec(total_s)} ({', '.join(parts)})")
                            else:
                                seg_lines.append(f"- 세그먼트 분석 소요 시간: {_fmt_sec(total_s)}")
                        elif parts:
                            seg_lines.append(f"- 세그먼트 분석 소요 시간: {', '.join(parts)}")

                    _safe_put("\n".join(seg_lines))

                    for key in ('heatmap_path', 'efficiency_path'):
                        p = phase3.get(key)
                        if p and Path(p).exists():
                            teleQ.put(str(Path(p)))
                except Exception:
                    pass

    except Exception as e:
        print_exc()

    return result
