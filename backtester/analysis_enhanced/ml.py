# -*- coding: utf-8 -*-
import hashlib
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from traceback import print_exc

import numpy as np
import pandas as pd

from .config import (
    MODEL_BASE_DIR,
    ML_RELIABILITY_CRITERIA,
)
from .utils import (
    _normalize_text_for_hash,
    _safe_filename,
    _write_json,
    _append_jsonl,
    ComputeStrategyKey,
)

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
        # [NEW 2025-12-28] 당일거래대금 시계열 비율 지표 (LOOKAHEAD-FREE)
        '당일거래대금_전틱분봉_비율', '당일거래대금_매수매도_비율', '당일거래대금_5틱분봉평균_비율',
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
