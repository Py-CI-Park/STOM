# -*- coding: utf-8 -*-
from pathlib import Path

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
