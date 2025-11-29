"""
교차검증 최적화 GetOptiValidStd 함수 단위 테스트

작성일: 2025-11-29
목적: std_false_point 처리 로직 검증
"""

import sys
sys.path.append('C:/System_Trading/STOM/STOM_V1')

from backtester.back_static import GetOptiValidStd


def test_scenario_1():
    """시나리오 1: 모든 VALID 조건 불만족"""
    print("\n=== 시나리오 1: 모든 VALID 조건 불만족 ===")
    train_data = [100.5, 150.3, 200.7]
    valid_data = [-2_222_222_222, -2_222_222_222, -2_222_222_222]
    optistd = 'TP'
    betting = 10000
    exponential = False

    result = GetOptiValidStd(train_data, valid_data, optistd, betting, exponential)

    print(f"TRAIN: {train_data}")
    print(f"VALID: {valid_data}")
    print(f"결과: {result}")
    print(f"예상: -2222222222 (std_false_point)")

    assert result == -2_222_222_222, f"예상값 불일치: {result}"
    print("[OK] 테스트 통과")


def test_scenario_2():
    """시나리오 2: 일부 VALID만 조건 만족"""
    print("\n=== 시나리오 2: 일부 VALID만 조건 만족 ===")
    train_data = [100.5, 150.3, 200.7]
    valid_data = [-2_222_222_222, 120.5, -2_222_222_222]
    optistd = 'TP'
    betting = 10000
    exponential = False

    result = GetOptiValidStd(train_data, valid_data, optistd, betting, exponential)

    print(f"TRAIN: {train_data}")
    print(f"VALID: {valid_data}")
    print(f"결과: {result}")

    # 예상: 150.3 * 120.5 / 1 = 18,111.15
    expected = round(150.3 * 120.5, 2)
    print(f"예상: {expected}")

    assert result == expected, f"예상값 불일치: {result} != {expected}"
    print("[OK] 테스트 통과")


def test_scenario_3():
    """시나리오 3: 모든 데이터 조건 만족"""
    print("\n=== 시나리오 3: 모든 데이터 조건 만족 ===")
    train_data = [100.5, 150.3, 200.7]
    valid_data = [95.2, 145.8, 195.3]
    optistd = 'TP'
    betting = 10000
    exponential = False

    result = GetOptiValidStd(train_data, valid_data, optistd, betting, exponential)

    print(f"TRAIN: {train_data}")
    print(f"VALID: {valid_data}")
    print(f"결과: {result}")

    # 예상: (100.5*95.2 + 150.3*145.8 + 200.7*195.3) / 3
    expected = round((100.5*95.2 + 150.3*145.8 + 200.7*195.3) / 3, 2)
    print(f"예상: {expected}")

    assert result == expected, f"예상값 불일치: {result} != {expected}"
    print("[OK] 테스트 통과")


def test_scenario_4():
    """시나리오 4: 지수 가중치 적용"""
    print("\n=== 시나리오 4: 지수 가중치 적용 ===")
    train_data = [100.5, 150.3, 200.7]
    valid_data = [95.2, 145.8, -2_222_222_222]
    optistd = 'TP'
    betting = 10000
    exponential = True

    result = GetOptiValidStd(train_data, valid_data, optistd, betting, exponential)

    print(f"TRAIN: {train_data}")
    print(f"VALID: {valid_data}")
    print(f"exponential: {exponential}")
    print(f"결과: {result}")

    # 예상 계산:
    # i=0: ex = (3-0)*2/3 = 2.0, std += 100.5 * 95.2 * 2.0 = 19,135.20
    # i=1: ex = (3-1)*2/3 = 1.33, std += 150.3 * 145.8 * 1.33 = 29,143.69
    # i=2: 건너뜀
    # valid_count = 2, std = 48,278.89 / 2 = 24,139.45
    ex1 = (3 - 0) * 2 / 3
    ex2 = (3 - 1) * 2 / 3
    expected = round((100.5 * 95.2 * ex1 + 150.3 * 145.8 * ex2) / 2, 2)
    print(f"예상: {expected}")

    assert result == expected, f"예상값 불일치: {result} != {expected}"
    print("[OK] 테스트 통과")


def test_scenario_5():
    """시나리오 5: TG 옵션 (betting으로 추가 나눔)"""
    print("\n=== 시나리오 5: TG 옵션 ===")
    train_data = [100000, 150000, 200000]
    valid_data = [95000, 145000, 195000]
    optistd = 'TG'
    betting = 10000
    exponential = False

    result = GetOptiValidStd(train_data, valid_data, optistd, betting, exponential)

    print(f"TRAIN: {train_data}")
    print(f"VALID: {valid_data}")
    print(f"optistd: {optistd} (betting으로 추가 나눔)")
    print(f"결과: {result}")

    # 예상: (100000*95000 + 150000*145000 + 200000*195000) / 3 / 10000
    expected = round((100000*95000 + 150000*145000 + 200000*195000) / 3 / betting, 2)
    print(f"예상: {expected}")

    assert result == expected, f"예상값 불일치: {result} != {expected}"
    print("[OK] 테스트 통과")


def test_scenario_6():
    """시나리오 6: 음수 데이터 처리"""
    print("\n=== 시나리오 6: 음수 데이터 처리 ===")
    train_data = [-50.5, 150.3, 200.7]
    valid_data = [-30.2, 145.8, 195.3]
    optistd = 'TP'
    betting = 10000
    exponential = False

    result = GetOptiValidStd(train_data, valid_data, optistd, betting, exponential)

    print(f"TRAIN: {train_data}")
    print(f"VALID: {valid_data}")
    print(f"결과: {result}")

    # 예상: 둘 다 음수면 빼기
    # std = 0 - (-50.5 * -30.2) + (150.3 * 145.8) + (200.7 * 195.3)
    std_ = 0
    std_ = std_ - (-50.5 * -30.2)  # 둘 다 음수
    std_ = std_ + (150.3 * 145.8)
    std_ = std_ + (200.7 * 195.3)
    expected = round(std_ / 3, 2)
    print(f"예상: {expected}")

    assert result == expected, f"예상값 불일치: {result} != {expected}"
    print("[OK] 테스트 통과")


if __name__ == '__main__':
    print("=" * 60)
    print("교차검증 최적화 GetOptiValidStd 함수 단위 테스트")
    print("=" * 60)

    try:
        test_scenario_1()
        test_scenario_2()
        test_scenario_3()
        test_scenario_4()
        test_scenario_5()
        test_scenario_6()

        print("\n" + "=" * 60)
        print("[OK] 모든 테스트 통과!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[FAIL] 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
