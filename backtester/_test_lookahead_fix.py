# -*- coding: utf-8 -*-
"""
LOOKAHEAD 문제 수정 및 ML 예측 기능 검증 스크립트

변경사항:
1. 당일거래대금_매수매도_비율을 explicit_buy_columns에서 제거
2. 당일거래대금_전틱분봉_비율, 당일거래대금_5틱분봉평균_비율을 PredictRiskWithML features에 추가
3. 당일거래대금_매수매도_비율_ML 예측 기능 추가
"""

def verify_lookahead_fix():
    """LOOKAHEAD 문제 수정 검증"""
    print("=" * 80)
    print("1. LOOKAHEAD 문제 수정 검증")
    print("=" * 80)

    # filter_evaluator.py 검증
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from backtester.segment_analysis.filter_evaluator import FilterEvaluatorConfig
    config = FilterEvaluatorConfig()

    print("\n[filter_evaluator.py]")
    print(f"explicit_buy_columns 개수: {len(config.explicit_buy_columns)}")

    if '당일거래대금_매수매도_비율' in config.explicit_buy_columns:
        print("❌ FAIL: 당일거래대금_매수매도_비율이 아직 explicit_buy_columns에 있습니다!")
        return False
    else:
        print("✅ PASS: 당일거래대금_매수매도_비율이 제거되었습니다.")

    if '당일거래대금_전틱분봉_비율' in config.explicit_buy_columns:
        print("✅ PASS: 당일거래대금_전틱분봉_비율이 포함되어 있습니다.")
    else:
        print("❌ FAIL: 당일거래대금_전틱분봉_비율이 없습니다!")
        return False

    if '당일거래대금_5틱분봉평균_비율' in config.explicit_buy_columns:
        print("✅ PASS: 당일거래대금_5틱분봉평균_비율이 포함되어 있습니다.")
    else:
        print("❌ FAIL: 당일거래대금_5틱분봉평균_비율이 없습니다!")
        return False

    return True


def verify_ml_prediction():
    """ML 예측 기능 검증"""
    print("\n" + "=" * 80)
    print("2. ML 예측 기능 검증")
    print("=" * 80)

    import pandas as pd
    import numpy as np

    # 테스트 데이터 생성
    print("\n[테스트 데이터 생성]")
    n_samples = 200
    np.random.seed(42)

    df_test = pd.DataFrame({
        '수익금': np.random.randn(n_samples) * 10000,
        '매수당일거래대금': np.random.uniform(100, 1000, n_samples),
        '매도당일거래대금': np.random.uniform(100, 1200, n_samples),
        '매수등락율': np.random.randn(n_samples) * 2,
        '매수시가등락율': np.random.randn(n_samples) * 1.5,
        '매수체결강도': np.random.uniform(0, 100, n_samples),
        '시가총액': np.random.uniform(100, 10000, n_samples),
        '모멘텀점수': np.random.uniform(0, 100, n_samples),
        '거래품질점수': np.random.uniform(0, 100, n_samples),
        '위험도점수': np.random.uniform(0, 100, n_samples),
    })

    # 당일거래대금 비율 지표 추가
    from backtester.analysis_enhanced.metrics import CalculateEnhancedDerivedMetrics
    df_enhanced = CalculateEnhancedDerivedMetrics(df_test)

    print(f"테스트 샘플 수: {len(df_enhanced)}")

    # 필수 컬럼 확인
    required_cols = [
        '당일거래대금_전틱분봉_비율',
        '당일거래대금_매수매도_비율',
        '당일거래대금_5틱분봉평균_비율'
    ]

    print("\n[필수 컬럼 확인]")
    for col in required_cols:
        if col in df_enhanced.columns:
            print(f"✅ {col}: 존재")
        else:
            print(f"❌ {col}: 없음!")
            return False

    # ML 예측 실행
    print("\n[ML 예측 실행]")
    from backtester.analysis_enhanced.ml import PredictRiskWithML

    try:
        df_predicted, stats = PredictRiskWithML(
            df_enhanced,
            save_file_name='test_lookahead_fix',
            buystg='테스트 매수 조건',
            sellstg='테스트 매도 조건',
            train_mode='train'
        )

        print("✅ PredictRiskWithML 실행 성공")

        # 결과 확인
        if '당일거래대금_매수매도_비율_ML' in df_predicted.columns:
            print("✅ 당일거래대금_매수매도_비율_ML 컬럼 생성됨")

            # 통계 확인
            ml_values = df_predicted['당일거래대금_매수매도_비율_ML'].dropna()
            if len(ml_values) > 0:
                print(f"\n[예측 결과 통계]")
                print(f"  - 예측값 개수: {len(ml_values)}")
                print(f"  - 평균: {ml_values.mean():.4f}")
                print(f"  - 표준편차: {ml_values.std():.4f}")
                print(f"  - 최소: {ml_values.min():.4f}")
                print(f"  - 최대: {ml_values.max():.4f}")

                # 실제값과 예측값 비교
                if '당일거래대금_매수매도_비율' in df_predicted.columns:
                    actual = df_predicted['당일거래대금_매수매도_비율'].dropna()
                    common_idx = ml_values.index.intersection(actual.index)
                    if len(common_idx) > 10:
                        corr = np.corrcoef(
                            ml_values.loc[common_idx],
                            actual.loc[common_idx]
                        )[0, 1]
                        print(f"  - 실제값과 상관계수: {corr:.3f}")
            else:
                print("❌ FAIL: 예측값이 모두 NaN입니다!")
                return False
        else:
            print("❌ FAIL: 당일거래대금_매수매도_비율_ML 컬럼이 생성되지 않았습니다!")
            return False

        # stats 확인
        if stats and 'trade_money_regression' in stats:
            tm_stats = stats['trade_money_regression']
            if tm_stats:
                print(f"\n[회귀 모델 성능]")
                print(f"  - 모델: {tm_stats.get('best_model', 'N/A')}")
                print(f"  - Test MAE: {tm_stats.get('test_mae', 'N/A')}")
                print(f"  - Test RMSE: {tm_stats.get('test_rmse', 'N/A')}")
                print(f"  - Test R²: {tm_stats.get('test_r2', 'N/A')}")
                print(f"  - Test 상관계수: {tm_stats.get('test_corr', 'N/A')}%")
                print("✅ ML 모델 통계 정상 생성됨")
            else:
                print("⚠️ WARNING: trade_money_regression_stats가 None입니다 (샘플 부족 가능)")
        else:
            print("⚠️ WARNING: stats에 trade_money_regression이 없습니다")

        return True

    except Exception as e:
        print(f"❌ FAIL: ML 예측 실행 중 오류 발생")
        print(f"  오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_documentation():
    """Documentation 검증"""
    print("\n" + "=" * 80)
    print("3. Documentation 검증")
    print("=" * 80)

    from backtester.back_static import GetDerivedMetricsDocumentation

    docs = GetDerivedMetricsDocumentation()

    print("\n[derived_docs 확인]")
    if '당일거래대금_매수매도_비율_ML' in docs:
        doc = docs['당일거래대금_매수매도_비율_ML']
        print("✅ 당일거래대금_매수매도_비율_ML documentation 존재")
        print(f"  - desc: {doc.get('desc', 'N/A')}")
        print(f"  - unit: {doc.get('unit', 'N/A')}")
        print(f"  - formula: {doc.get('formula', 'N/A')}")
        print(f"  - note: {doc.get('note', 'N/A')}")
        return True
    else:
        print("❌ FAIL: 당일거래대금_매수매도_비율_ML documentation이 없습니다!")
        return False


if __name__ == '__main__':
    print("\n")
    print("*" * 80)
    print("LOOKAHEAD 문제 수정 및 ML 예측 기능 검증")
    print("*" * 80)

    results = []

    # 1. LOOKAHEAD 문제 수정 검증
    results.append(verify_lookahead_fix())

    # 2. ML 예측 기능 검증
    results.append(verify_ml_prediction())

    # 3. Documentation 검증
    results.append(verify_documentation())

    # 최종 결과
    print("\n" + "=" * 80)
    print("검증 결과 요약")
    print("=" * 80)

    test_names = [
        "LOOKAHEAD 문제 수정",
        "ML 예측 기능",
        "Documentation"
    ]

    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i}. {name}: {status}")

    all_passed = all(results)
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 모든 검증 통과!")
    else:
        print("❌ 일부 검증 실패. 위 결과를 확인하세요.")
    print("=" * 80)
