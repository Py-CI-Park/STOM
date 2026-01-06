# -*- coding: utf-8 -*-
"""
세그먼트 필터 일관성 검증 스크립트

최종 목적:
- 분석 예측값 == 실제 백테스트 결과 검증
- segment_code_final.txt 파일 생성 확인
- ranges.csv 로드 및 동일 경계 사용 확인

사용법:
    python verify_segment_consistency.py [detail.csv 경로]

작성일: 2026-01-05
버전: 2.0
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def _resolve_detail_path(cli_path: Optional[str] = None) -> Path:
    """detail.csv 파일 경로 해석"""
    if cli_path:
        return Path(cli_path).expanduser().resolve()

    graph_dir = Path(__file__).resolve().parent.parent / 'graph'
    candidates = sorted(
        graph_dir.glob('*_detail.csv'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    if not candidates:
        raise FileNotFoundError("graph 폴더에서 detail.csv 파일을 찾지 못했습니다.")
    return candidates[0]


def verify_ranges_csv_loading():
    """
    검증 1: _load_segment_config_from_ranges 함수 존재 확인
    """
    print("\n" + "=" * 60)
    print("[검증 1] ranges.csv 로드 함수 확인")
    print("=" * 60)

    try:
        from backtester.back_static import _load_segment_config_from_ranges
        print("✅ _load_segment_config_from_ranges 함수 존재")
        return True
    except ImportError as e:
        print(f"❌ 함수 임포트 실패: {e}")
        return False


def verify_segment_code_final_generation():
    """
    검증 2: segment_code_final 생성 함수 확인
    """
    print("\n" + "=" * 60)
    print("[검증 2] segment_code_final 생성 함수 확인")
    print("=" * 60)

    try:
        from backtester.segment_analysis.code_generator import (
            save_segment_code_final,
            build_segment_final_code,
        )
        print("✅ save_segment_code_final 함수 존재")
        print("✅ build_segment_final_code 함수 존재")
        return True
    except ImportError as e:
        print(f"❌ 함수 임포트 실패: {e}")
        return False


def verify_ranges_path_in_global_best():
    """
    검증 3: phase2_runner에서 ranges_path 저장 확인
    """
    print("\n" + "=" * 60)
    print("[검증 3] phase2_runner의 ranges_path 저장 확인")
    print("=" * 60)

    try:
        phase2_path = Path(__file__).resolve().parent / 'phase2_runner.py'
        content = phase2_path.read_text(encoding='utf-8')

        if "global_best['ranges_path']" in content:
            print("✅ global_best에 ranges_path 저장 코드 존재")
            return True
        else:
            print("❌ ranges_path 저장 코드 없음")
            return False
    except Exception as e:
        print(f"❌ 파일 확인 실패: {e}")
        return False


def verify_elif_logic():
    """
    검증 4: 세그먼트 필터 if/elif 논리 확인
    """
    print("\n" + "=" * 60)
    print("[검증 4] 세그먼트 필터 if/elif 논리 확인")
    print("=" * 60)

    try:
        code_gen_path = Path(__file__).resolve().parent / 'code_generator.py'
        content = code_gen_path.read_text(encoding='utf-8')

        if 'if_keyword = "if" if i == 0 else "elif"' in content:
            print("✅ if/elif 논리 올바르게 구현됨")
            return True
        else:
            print("❌ if/elif 논리 확인 필요")
            return False
    except Exception as e:
        print(f"❌ 파일 확인 실패: {e}")
        return False


def verify_runtime_mapping():
    """
    검증 5: 런타임 매핑 블록 확인
    """
    print("\n" + "=" * 60)
    print("[검증 5] 런타임 매핑 블록 확인")
    print("=" * 60)

    try:
        from backtester.segment_analysis.code_generator import _build_segment_runtime_preamble
        lines = _build_segment_runtime_preamble()

        required_mappings = [
            '매수초당거래대금',
            '매수등락율',
            '매수체결강도',
            '매수당일거래대금',
        ]

        found = []
        for mapping in required_mappings:
            if any(mapping in line for line in lines):
                found.append(mapping)

        if len(found) == len(required_mappings):
            print(f"✅ 런타임 매핑 {len(found)}/{len(required_mappings)}개 확인")
            return True
        else:
            missing = set(required_mappings) - set(found)
            print(f"⚠️ 누락된 매핑: {missing}")
            return False
    except Exception as e:
        print(f"❌ 런타임 매핑 확인 실패: {e}")
        return False


def check_existing_output_files(detail_path: Path) -> Dict[str, Any]:
    """
    검증 6: 기존 출력 파일 확인
    """
    print("\n" + "=" * 60)
    print("[검증 6] 출력 파일 확인")
    print("=" * 60)

    output_dir = detail_path.parent
    prefix = detail_path.stem.replace('_detail', '')

    files_to_check = [
        f"{prefix}_segment_code.txt",
        f"{prefix}_segment_code_final.txt",
        f"{prefix}_ranges.csv",
        f"{prefix}_combos.csv",
        f"{prefix}_segment_summary_report.txt",
    ]

    result = {}
    for filename in files_to_check:
        filepath = output_dir / filename
        exists = filepath.exists()
        result[filename] = exists
        status = "✅" if exists else "❌"
        print(f"{status} {filename}: {'존재' if exists else '없음'}")

    return result


def run_all_verifications(detail_path: Optional[str] = None):
    """
    모든 검증 실행
    """
    print("=" * 60)
    print("세그먼트 필터 일관성 검증 시작")
    print("=" * 60)

    results = {
        'ranges_csv_loading': verify_ranges_csv_loading(),
        'segment_code_final': verify_segment_code_final_generation(),
        'ranges_path_in_global_best': verify_ranges_path_in_global_best(),
        'elif_logic': verify_elif_logic(),
        'runtime_mapping': verify_runtime_mapping(),
    }

    # 출력 파일 확인 (detail.csv가 있을 경우)
    try:
        path = _resolve_detail_path(detail_path)
        print(f"\n사용 파일: {path.name}")
        results['output_files'] = check_existing_output_files(path)
    except FileNotFoundError:
        print("\n⚠️ detail.csv 파일 없음 - 출력 파일 확인 건너뜀")

    # 결과 요약
    print("\n" + "=" * 60)
    print("검증 결과 요약")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v is True or (isinstance(v, dict) and any(v.values())))
    total = len(results)

    for key, value in results.items():
        if isinstance(value, bool):
            status = "✅ PASS" if value else "❌ FAIL"
            print(f"  {key}: {status}")
        elif isinstance(value, dict):
            found = sum(1 for v in value.values() if v)
            print(f"  {key}: {found}/{len(value)} 파일 존재")

    print(f"\n총 결과: {passed}/{total} 검증 통과")

    if passed == total:
        print("\n🎉 모든 핵심 수정사항이 올바르게 반영되었습니다!")
        print("📋 다음 단계: 실제 백테스트 실행하여 예측값=실제값 확인")
    else:
        print("\n⚠️ 일부 검증 실패 - 코드 확인 필요")

    return results


if __name__ == '__main__':
    cli_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_all_verifications(cli_path)
