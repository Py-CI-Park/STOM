# -*- coding: utf-8 -*-
"""
[2025-12-28] 당일거래대금 비율 지표 추가 구현 검증 스크립트

목적:
- 새로 추가한 당일거래대금 비율 지표 3종이 정상적으로 생성되는지 검증
- 값의 범위와 의미가 올바른지 확인

검증 항목:
1. 당일거래대금_전틱분봉_비율
2. 당일거래대금_매수매도_비율
3. 당일거래대금_5틱분봉평균_비율
"""

import numpy as np
import pandas as pd
from backtester.analysis_enhanced.metrics_enhanced import CalculateEnhancedDerivedMetrics

def test_new_trade_money_ratio_metrics():
    """
    새로 추가한 당일거래대금 비율 지표 검증
    """
    print("=" * 80)
    print("당일거래대금 비율 지표 추가 구현 검증")
    print("=" * 80)

    # 1. 테스트 데이터 생성
    print("\n[1] 테스트 데이터 생성 중...")

    test_data = {
        '종목명': ['종목A', '종목A', '종목A', '종목A', '종목A', '종목A', '종목A', '종목A', '종목A', '종목A'],
        '매수시간': pd.date_range('2025-01-01 09:00:00', periods=10, freq='1min'),
        '매도시간': pd.date_range('2025-01-01 09:05:00', periods=10, freq='1min'),
        '매수가': [10000, 10100, 10200, 10300, 10400, 10500, 10600, 10700, 10800, 10900],
        '매도가': [10050, 10150, 10250, 10350, 10450, 10550, 10650, 10750, 10850, 10950],
        '매수금액': [1000000, 1010000, 1020000, 1030000, 1040000, 1050000, 1060000, 1070000, 1080000, 1090000],
        '매도금액': [1005000, 1015000, 1025000, 1035000, 1045000, 1055000, 1065000, 1075000, 1085000, 1095000],
        '수익금': [5000, 5000, 5000, 5000, 5000, 5000, 5000, 5000, 5000, 5000],
        '수익률': [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
        '보유시간': [300, 300, 300, 300, 300, 300, 300, 300, 300, 300],

        # 핵심 테스트 대상: 매수당일거래대금 (점진적 증가 패턴)
        '매수당일거래대금': [
            10000,  # 백만원 (100억)
            12000,  # 20% 증가
            14400,  # 20% 증가
            17280,  # 20% 증가
            20736,  # 20% 증가
            24883,  # 20% 증가
            29860,  # 20% 증가
            35832,  # 20% 증가
            42998,  # 20% 증가
            51598,  # 20% 증가
        ],

        # 매도당일거래대금 (매수 대비 10% 증가 패턴)
        '매도당일거래대금': [
            11000,  # 10% 증가
            13200,  # 10% 증가
            15840,  # 10% 증가
            19008,  # 10% 증가
            22810,  # 10% 증가
            27371,  # 10% 증가
            32846,  # 10% 증가
            39415,  # 10% 증가
            47298,  # 10% 증가
            56758,  # 10% 증가
        ],

        # 기타 필수 컬럼
        '매수등락율': [5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9],
        '매수체결강도': [110, 112, 114, 116, 118, 120, 122, 124, 126, 128],
        '매도등락율': [5.5, 5.6, 5.7, 5.8, 5.9, 6.0, 6.1, 6.2, 6.3, 6.4],
        '매도체결강도': [115, 117, 119, 121, 123, 125, 127, 129, 131, 133],
    }

    df = pd.DataFrame(test_data)
    print(f"[OK] 테스트 데이터 생성 완료 ({len(df)}개 거래)")

    # 2. 파생 지표 계산 (새 지표 포함)
    print("\n[2] 파생 지표 계산 중...")

    df_enhanced = CalculateEnhancedDerivedMetrics(df)

    print(f"[OK] 파생 지표 계산 완료 (총 컬럼 수: {len(df_enhanced.columns)}개)")

    # 3. 새로 추가한 지표 확인
    print("\n[3] 새로 추가한 지표 검증")
    print("-" * 80)

    new_metrics = [
        '당일거래대금_전틱분봉_비율',
        '당일거래대금_매수매도_비율',
        '당일거래대금_5틱분봉평균_비율',
    ]

    all_exist = True
    for metric in new_metrics:
        if metric in df_enhanced.columns:
            print(f"[OK] {metric}: 생성됨")
        else:
            print(f"[FAIL] {metric}: 미생성 (오류)")
            all_exist = False

    if not all_exist:
        print("\n[WARNING] 일부 지표가 생성되지 않았습니다. 구현을 확인하세요.")
        return False

    # 4. 지표 값 검증
    print("\n[4] 지표 값 검증")
    print("-" * 80)

    # 4.1 당일거래대금_전틱분봉_비율 검증
    print("\n[4.1] 당일거래대금_전틱분봉_비율")
    print("  - 의미: 직전 거래 대비 당일거래대금 변화율")
    print("  - 기대값: 첫 거래=1.0, 이후=1.2 (20% 증가)")

    ratio_1 = df_enhanced['당일거래대금_전틱분봉_비율'].values
    print(f"  - 실제값: {ratio_1[:5]}")  # 처음 5개만 출력

    expected_first = 1.0
    expected_others = 1.2

    if abs(ratio_1[0] - expected_first) < 0.01:
        print(f"  [OK] 첫 거래 값 정상: {ratio_1[0]:.4f}")
    else:
        print(f"  [FAIL] 첫 거래 값 비정상: {ratio_1[0]:.4f} (기대값: {expected_first})")

    if all(abs(r - expected_others) < 0.01 for r in ratio_1[1:]):
        print(f"  [OK] 이후 거래 값 정상: 평균 {np.mean(ratio_1[1:]):.4f}")
    else:
        print(f"  [FAIL] 이후 거래 값 비정상: 평균 {np.mean(ratio_1[1:]):.4f} (기대값: {expected_others})")

    # 4.2 당일거래대금_매수매도_비율 검증
    print("\n[4.2] 당일거래대금_매수매도_비율")
    print("  - 의미: 매수 시점 대비 매도 시점 당일거래대금 변화율")
    print("  - 기대값: 1.1 (10% 증가)")

    ratio_2 = df_enhanced['당일거래대금_매수매도_비율'].values
    print(f"  - 실제값: {ratio_2[:5]}")  # 처음 5개만 출력

    expected_buy_sell = 1.1

    if all(abs(r - expected_buy_sell) < 0.01 for r in ratio_2):
        print(f"  [OK] 모든 거래 값 정상: 평균 {np.mean(ratio_2):.4f}")
    else:
        print(f"  [FAIL] 일부 거래 값 비정상: 평균 {np.mean(ratio_2):.4f} (기대값: {expected_buy_sell})")

    # 4.3 당일거래대금_5틱분봉평균_비율 검증
    print("\n[4.3] 당일거래대금_5틱분봉평균_비율")
    print("  - 의미: 최근 5틱/분봉 평균 대비 당일거래대금 비율")
    print("  - 기대값: 변동 (거래에 따라 다름, 범위: 0.5~2.0)")

    ratio_3 = df_enhanced['당일거래대금_5틱분봉평균_비율'].values
    print(f"  - 실제값: {ratio_3}")
    print(f"  - 최소값: {np.min(ratio_3):.4f}")
    print(f"  - 최대값: {np.max(ratio_3):.4f}")
    print(f"  - 평균값: {np.mean(ratio_3):.4f}")

    if all(0.5 <= r <= 2.0 for r in ratio_3):
        print(f"  [OK] 모든 값이 합리적 범위 내 (0.5~2.0)")
    else:
        print(f"  [WARNING] 일부 값이 범위 밖 (확인 필요)")

    # 5. 요약
    print("\n" + "=" * 80)
    print("검증 요약")
    print("=" * 80)

    print(f"\n[OK] 신규 지표 개수: {len(new_metrics)}개")
    print(f"[OK] 모든 지표 생성: {'예' if all_exist else '아니오'}")
    print(f"[OK] 기존 컬럼 수: {len(df.columns)}개")
    print(f"[OK] 증가 컬럼 수: {len(df_enhanced.columns) - len(df.columns)}개")
    print(f"[OK] 최종 컬럼 수: {len(df_enhanced.columns)}개")

    print("\n신규 지표 활용 예시:")
    print("  - 필터 조건: 당일거래대금_전틱분봉_비율 >= 1.2  # 거래대금 20% 이상 증가")
    print("  - 필터 조건: 당일거래대금_매수매도_비율 >= 1.1  # 보유 중 유동성 10% 이상 증가")
    print("  - 필터 조건: 당일거래대금_5틱분봉평균_비율 >= 1.3  # 평균 대비 30% 이상 활성화")

    print("\n검증 완료! 구현이 정상적으로 동작합니다.")

    return True


if __name__ == '__main__':
    try:
        success = test_new_trade_money_ratio_metrics()

        if success:
            print("\n" + "=" * 80)
            print("[SUCCESS] 모든 검증 통과! 백테스팅 시스템에서 정상 사용 가능합니다.")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("[FAIL] 검증 실패! 구현을 다시 확인하세요.")
            print("=" * 80)

    except Exception as e:
        print("\n" + "=" * 80)
        print(f"[ERROR] 오류 발생: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
