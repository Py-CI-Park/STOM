# ICOS 다이얼로그 개선 계획서

> **작성일**: 2026-01-13
> **목적**: 백테스팅 결과 분석 옵션을 ICOS와 분리하여 Alt+I 다이얼로그에서 개별 설정
> **브랜치**: feature/iterative-condition-optimizer

---

## 1. 현재 상황 분석

### 1.1 기존 백테스팅 결과 분석 프로세스

```
백테스트 완료
    ↓
WriteGraphOutputReport() [back_static.py]
    ↓
RunEnhancedAnalysis() [analysis_enhanced/runner.py]
    ├─ Phase A: 일반 필터 분석 (Step 1-9)
    │   ├─ Step 1: 강화 파생 지표 계산
    │   ├─ Step 2: ML 위험도 예측
    │   ├─ Step 3: 필터 효과 분석 (통계 유의성)
    │   ├─ Step 4: 최적 임계값 탐색
    │   ├─ Step 5: 필터 조합 분석
    │   ├─ Step 6: ML 특성 중요도
    │   ├─ Step 7: 필터 안정성 검증
    │   ├─ Step 8: 조건식 코드 생성
    │   └─ Step 9: filter_code_final.txt 생성
    │
    ├─ Phase B: 결과 저장 (Step 10-11)
    │   ├─ Step 10: CSV 파일 저장
    │   └─ Step 11: 차트 생성
    │
    └─ Phase C: 세그먼트 분석 (Step 12, 조건부)
        ├─ Phase2: 세그먼트 분할 + 필터 탐색
        ├─ Phase3: 세그먼트별 최적화
        ├─ Template 비교 (Optuna)
        └─ segment_code_final.txt 생성
    ↓
텔레그램 전송 (분석 로그, 차트, 요약)
```

### 1.2 현재 ICOS 다이얼로그 구조

```
┌─────────────────────────────────────────────────┐
│ ICOS 모드 (상단)                                │
│   [x] ICOS 활성화                               │
├─────────────────────────────────────────────────┤
│ 기본 설정                                       │
│   최대 반복 횟수: [5]                           │
│   수렴 기준값: [5] %                            │
│   최적화 기준: [수익금 ▼]                       │
├─────────────────────────────────────────────────┤
│ 필터 생성 설정                                  │
│   반복당 최대 필터 수: [3]                      │
│   최소 샘플 수: [30]                            │
│   [x] 세그먼트 분석 활용                        │
├─────────────────────────────────────────────────┤
│ 최적화 알고리즘                                 │
│   최적화 방법: [그리드서치 ▼]                   │
│   최적화 시도 횟수: [100]                       │
│   [ ] Walk-Forward 검증 활성화                  │
│   W-F 폴드 수: [5]                              │
├─────────────────────────────────────────────────┤
│ 저장 설정                                       │
│   [x] 반복 결과 저장                            │
│   [x] 최종 조건식 자동 저장                     │
│   [ ] 상세 로그 출력                            │
├─────────────────────────────────────────────────┤
│ [설정 저장] [설정 로딩] [기본값 복원] [ICOS 중지]│
├─────────────────────────────────────────────────┤
│ 실행 로그                                       │
│ ┌─────────────────────────────────────────────┐ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│ [██████████████████████████████████████] 100%   │
└─────────────────────────────────────────────────┘
```

---

## 2. 개선 목표

### 2.1 핵심 요구사항

1. **백테스팅 결과 분석**과 **ICOS 반복 최적화**를 **완전 분리**
2. 백테스팅 결과 분석 옵션:
   - 비활성화: 기본 백테스트 → 이미지 2개만 텔레그램 전송
   - 활성화: 상세 분석 (Phase A/B/C) 진행 → 상세 결과 텔레그램 전송
3. 각 분석 단계별 세부 옵션 설정 가능

### 2.2 새로운 다이얼로그 구조

```
┌─────────────────────────────────────────────────────────────────┐
│ STOM ICOS & 분석 설정                                           │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 백테스팅 결과 분석 (Analysis)                    [활성화 ✓] │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Phase A: 필터 분석                                          │ │
│ │   [x] 필터 효과 분석 (통계 유의성 검정)                     │ │
│ │   [x] 최적 임계값 탐색                                      │ │
│ │   [x] 필터 조합 분석                                        │ │
│ │   [x] 필터 안정성 검증                                      │ │
│ │   [x] 필터 조건식 자동 생성                                 │ │
│ │                                                             │ │
│ │ ML 분석                                                     │ │
│ │   [x] ML 위험도 예측                                        │ │
│ │   [x] ML 특성 중요도 분석                                   │ │
│ │   ML 모드: [학습(train) ▼]                                  │ │
│ │                                                             │ │
│ │ Phase C: 세그먼트 분석                                      │ │
│ │   [x] 세그먼트 분석 활성화                                  │ │
│ │   [x] Optuna 최적화 사용                                    │ │
│ │   [x] 템플릿 비교                                           │ │
│ │   [x] 분석 결과 자동 저장 (DB)                              │ │
│ │                                                             │ │
│ │ 알림 설정                                                   │ │
│ │   텔레그램 알림: [상세 ▼] (없음/요약/상세)                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ICOS 반복 최적화 (미구현)                        [비활성 -] │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ * 향후 구현 예정 - 백테스트 실행 연동 필요                  │ │
│ │   최대 반복 횟수: [5]                                       │ │
│ │   수렴 기준값: [5] %                                        │ │
│ │   ... (기존 옵션 유지)                                      │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ [설정 저장] [설정 로딩] [기본값 복원]              [닫기]       │
│                                                                 │
│ 실행 로그                                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 개발 단계 계획

### Phase 1: UI 재구조화 (set_dialog_icos.py)

| Step | 작업 | 예상 시간 |
|------|------|----------|
| 1-1 | 백테스팅 결과 분석 그룹박스 추가 | 15분 |
| 1-2 | Phase A 필터 분석 옵션 위젯 추가 | 10분 |
| 1-3 | ML 분석 옵션 위젯 추가 | 10분 |
| 1-4 | Phase C 세그먼트 분석 옵션 위젯 추가 | 10분 |
| 1-5 | 알림 설정 옵션 위젯 추가 | 5분 |
| 1-6 | ICOS 그룹박스 축소 및 재배치 | 10분 |
| 1-7 | 레이아웃 조정 | 10분 |

### Phase 2: 설정 저장/로딩 업데이트 (ui_button_clicked_icos.py)

| Step | 작업 | 예상 시간 |
|------|------|----------|
| 2-1 | 분석 설정 수집 함수 구현 | 15분 |
| 2-2 | 분석 설정 적용 함수 구현 | 15분 |
| 2-3 | JSON 저장/로딩 업데이트 | 10분 |
| 2-4 | 기본값 상수 업데이트 | 5분 |

### Phase 3: 백테스트 연동 (back_static.py 수정)

| Step | 작업 | 예상 시간 |
|------|------|----------|
| 3-1 | UI 설정값을 backQ에 전달하는 메커니즘 구현 | 20분 |
| 3-2 | WriteGraphOutputReport 파라미터 확장 | 15분 |
| 3-3 | RunEnhancedAnalysis 호출 조건 분기 | 15분 |
| 3-4 | 비활성화 시 기본 이미지만 전송 로직 | 10분 |

### Phase 4: 테스트 및 검증

| Step | 작업 | 예상 시간 |
|------|------|----------|
| 4-1 | 문법 검사 | 5분 |
| 4-2 | 다이얼로그 표시 테스트 | 10분 |
| 4-3 | 설정 저장/로딩 테스트 | 10분 |

---

## 4. 상세 설계

### 4.1 새로운 UI 변수 목록

```python
# 백테스팅 결과 분석 관련
ui.analysis_enabled = False                    # 분석 활성화 여부
ui.analysis_groupBoxxxx_00 = QGroupBox()       # 메인 그룹박스

# Phase A: 필터 분석
ui.analysis_checkBoxxx_01 = QCheckBox()        # 필터 효과 분석
ui.analysis_checkBoxxx_02 = QCheckBox()        # 최적 임계값 탐색
ui.analysis_checkBoxxx_03 = QCheckBox()        # 필터 조합 분석
ui.analysis_checkBoxxx_04 = QCheckBox()        # 필터 안정성 검증
ui.analysis_checkBoxxx_05 = QCheckBox()        # 필터 조건식 자동 생성

# ML 분석
ui.analysis_checkBoxxx_06 = QCheckBox()        # ML 위험도 예측
ui.analysis_checkBoxxx_07 = QCheckBox()        # ML 특성 중요도
ui.analysis_comboBoxxx_01 = QComboBox()        # ML 모드 (train/test)

# Phase C: 세그먼트 분석
ui.analysis_checkBoxxx_08 = QCheckBox()        # 세그먼트 분석 활성화
ui.analysis_checkBoxxx_09 = QCheckBox()        # Optuna 최적화
ui.analysis_checkBoxxx_10 = QCheckBox()        # 템플릿 비교
ui.analysis_checkBoxxx_11 = QCheckBox()        # 분석 결과 자동 저장

# 알림 설정
ui.analysis_comboBoxxx_02 = QComboBox()        # 텔레그램 알림 레벨
```

### 4.2 설정 딕셔너리 구조

```python
ANALYSIS_DEFAULTS = {
    'enabled': True,

    # Phase A: 필터 분석
    'filter_analysis': {
        'filter_effects': True,           # 필터 효과 분석
        'optimal_thresholds': True,       # 최적 임계값 탐색
        'filter_combinations': True,      # 필터 조합 분석
        'filter_stability': True,         # 필터 안정성 검증
        'generate_code': True,            # 필터 조건식 생성
    },

    # ML 분석
    'ml_analysis': {
        'risk_prediction': True,          # ML 위험도 예측
        'feature_importance': True,       # ML 특성 중요도
        'mode': 'train',                  # 'train' or 'test'
    },

    # Phase C: 세그먼트 분석
    'segment_analysis': {
        'enabled': True,                  # 세그먼트 분석 활성화
        'optuna': True,                   # Optuna 최적화
        'template_compare': True,         # 템플릿 비교
        'auto_save': True,                # 분석 결과 자동 저장
    },

    # 알림 설정
    'notification': {
        'level': 'detailed',              # 'none', 'summary', 'detailed'
    },
}
```

### 4.3 백테스트 연동 흐름

```
[백테스트 버튼 클릭]
    ↓
sdbutton_clicked_02(ui)
    ↓
(분석 설정 수집)
analysis_config = _collect_analysis_config(ui)
    ↓
backQ.put((..., analysis_config))  # 백테스트 파라미터에 분석 설정 추가
    ↓
[BackTest 프로세스]
    ↓
WriteGraphOutputReport(..., analysis_config=analysis_config)
    ↓
if analysis_config['enabled']:
    RunEnhancedAnalysis(
        ...,
        run_filter_analysis=analysis_config['filter_analysis']['filter_effects'],
        run_ml_analysis=analysis_config['ml_analysis']['risk_prediction'],
        segment_analysis_mode='phase2+3' if analysis_config['segment_analysis']['enabled'] else 'off',
        ...
    )
else:
    # 기본 이미지 2개만 텔레그램 전송
    send_basic_report_images(teleQ)
```

---

## 5. 파일 변경 목록

| 파일 | 변경 유형 | 변경 내용 |
|------|----------|----------|
| `ui/set_dialog_icos.py` | 대폭 수정 | 다이얼로그 재구조화, 분석 옵션 UI 추가 |
| `ui/ui_button_clicked_icos.py` | 수정 | 분석 설정 수집/적용 함수 추가 |
| `ui/ui_button_clicked_sd.py` | 수정 | 분석 설정 전달 로직 추가 |
| `backtester/back_static.py` | 수정 | WriteGraphOutputReport 파라미터 확장 |
| `backtester/backtest.py` | 수정 | 분석 설정 전달 (필요 시) |

---

## 6. 구현 우선순위

1. **Phase 1**: UI 재구조화 (가장 중요, 사용자 경험)
2. **Phase 2**: 설정 저장/로딩 (설정 영속성)
3. **Phase 3**: 백테스트 연동 (실제 동작)
4. **Phase 4**: 테스트

---

## 7. 롤백 계획

문제 발생 시:
1. `ui/set_dialog_icos.py` 원복
2. `ui/ui_button_clicked_icos.py` 원복
3. `ui/ui_button_clicked_sd.py` 원복
4. `back_static.py` 원복 (필요 시)

---

## 8. 예상 결과

### 비활성화 상태
```
백테스트 완료
    ↓
기본 리포트 생성 (기존)
    ↓
이미지 2개 텔레그램 전송 (차트, 요약)
    ↓
완료
```

### 활성화 상태 (전체 분석)
```
백테스트 완료
    ↓
RunEnhancedAnalysis 실행 (12단계)
    ↓
상세 분석 결과 텔레그램 전송
    - [1/12] 강화 파생 지표 계산 완료
    - [2/12] ML 위험도 예측 완료
    - ...
    - 필터 요약, 세그먼트 결과
    ↓
CSV/차트/조건식 파일 저장
    ↓
완료
```

---

**작성자**: Claude Opus 4.5
**검토 필요**: 사용자 승인 후 구현 진행
