"""
ICOS & 분석 설정 다이얼로그.

ICOS (Iterative Condition Optimization System) 및 백테스팅 결과 분석 설정을 위한 UI.

개선된 구조:
1. 백테스팅 결과 분석: Phase A(필터 분석), ML 분석, Phase C(세그먼트 분석) 개별 설정
2. ICOS 반복 최적화: 분석과 독립적으로 실행 가능

워크플로우:
- 분석 비활성화: 기본 백테스트 → 이미지 2개 텔레그램 전송
- 분석 활성화: 상세 분석 → 단계별 결과 텔레그램 전송
- ICOS 활성화: 반복적 조건식 개선 → 분석 설정과 독립적으로 실행

작성일: 2026-01-12
수정일: 2026-01-14
브랜치: feature/iterative-condition-optimizer
"""

from PyQt5.QtWidgets import QGroupBox, QLabel
from PyQt5.QtGui import QFont
from ui.set_style import style_ck_bx, style_bc_dk


# ============================================================================
# 툴팁 정의 (한글 설명)
# ============================================================================

TOOLTIPS = {
    # 분석 섹션
    'analysis_enabled': (
        '백테스팅 결과 분석 기능 ON/OFF\n'
        '• 활성화: 상세 분석 후 텔레그램 알림\n'
        '• 비활성화: 기본 이미지 2개만 전송'
    ),
    'filter_effects': (
        '필터 효과 분석 (통계적 유의성 검정)\n'
        '• 각 필터가 수익률에 미치는 영향 분석\n'
        '• T-검정, 카이제곱 검정 사용'
    ),
    'optimal_thresholds': (
        '최적 임계값 탐색\n'
        '• 각 필터의 최적 임계값 자동 탐색\n'
        '• 그리드 서치 방식 사용'
    ),
    'filter_combinations': (
        '필터 조합 분석\n'
        '• 필터들의 상호작용 효과 분석\n'
        '• 최적 필터 조합 도출'
    ),
    'filter_stability': (
        '필터 안정성 검증\n'
        '• 시간대별 필터 효과 일관성 확인\n'
        '• 과적합 여부 진단'
    ),
    'generate_code': (
        '필터 조건식 자동 생성\n'
        '• 분석 결과를 Python 조건식으로 변환\n'
        '• 복사하여 바로 사용 가능'
    ),
    'ml_risk': (
        'ML 위험도 예측\n'
        '• 머신러닝으로 거래 위험도 예측\n'
        '• XGBoost 모델 사용'
    ),
    'ml_importance': (
        'ML 특성 중요도\n'
        '• 변수별 중요도 순위 표시\n'
        '• 핵심 변수 파악에 유용'
    ),
    'ml_mode': (
        'ML 모드 선택\n'
        '• 학습: 새 모델 학습\n'
        '• 테스트: 기존 모델로 예측'
    ),
    'segment_enabled': (
        '세그먼트 분석 활성화\n'
        '• 시간대/요일/가격대별 성과 분석\n'
        '• 최적 거래 구간 파악'
    ),
    'segment_optuna': (
        'Optuna 최적화 사용\n'
        '• 베이지안 최적화로 파라미터 탐색\n'
        '• 더 정확하지만 시간 소요'
    ),
    'segment_template': (
        '템플릿 비교\n'
        '• 기존 조건식 템플릿과 비교 분석\n'
        '• 개선점 도출'
    ),
    'segment_autosave': (
        '분석 결과 자동 저장\n'
        '• 결과를 파일로 자동 저장\n'
        '• 나중에 다시 확인 가능'
    ),
    'notification_level': (
        '텔레그램 알림 레벨\n'
        '• 상세: 모든 분석 결과 전송\n'
        '• 요약: 핵심 결과만 전송\n'
        '• 없음: 알림 비활성화'
    ),
    # ICOS 섹션
    'icos_enabled': (
        'ICOS 활성화 (분석과 독립)\n'
        '• 활성화 시 백테스트 후 자동 조건식 개선\n'
        '• 분석 비활성화 상태에서도 실행 가능'
    ),
    'icos_max_iterations': (
        '최대 반복 횟수 (1~20)\n'
        '• 권장: 3~5회\n'
        '• 많을수록 시간 소요'
    ),
    'icos_convergence': (
        '수렴 기준 (%)\n'
        '• 개선율이 이 값 이하면 종료\n'
        '• 낮을수록 더 많이 최적화'
    ),
    'icos_metric': (
        '최적화 기준 선택\n'
        '• 수익금: 총 수익 최대화\n'
        '• 승률: 거래 성공률 최대화\n'
        '• 복합점수: 균형잡힌 최적화'
    ),
    'icos_method': (
        '최적화 방법 선택\n'
        '• 그리드서치: 전수 탐색 (안정적)\n'
        '• 유전알고리즘: 진화 탐색 (빠름)\n'
        '• 베이지안: 지능형 탐색 (효율적)'
    ),
}


class SetDialogICOS:
    """ICOS & 분석 설정 다이얼로그 클래스.

    백테스팅 결과 분석 옵션과 ICOS 반복 최적화 옵션을 분리하여 제공합니다.

    Attributes:
        ui: 메인 UI 클래스 참조
        wc: 위젯 생성기 참조
    """

    def __init__(self, ui_class, wc):
        """SetDialogICOS 초기화.

        Args:
            ui_class: 메인 UI 클래스
            wc: 위젯 생성기
        """
        self.ui = ui_class
        self.wc = wc
        self.set()

    def set(self):
        """다이얼로그 UI 구성."""
        # 메인 다이얼로그 생성 (제목 변경)
        self.ui.dialog_icos = self.wc.setDialog('STOM - 백테스팅 분석 & ICOS 설정')
        self.ui.dialog_icos.geometry().center()

        # 상태 변수 초기화
        self.ui.analysis_enabled = True  # 분석 기본 활성화
        self.ui.icos_enabled = False  # ICOS 기본 비활성화

        # =====================================================================
        # 섹션 1: 백테스팅 결과 분석 (Analysis)
        # =====================================================================
        self.ui.analysis_groupBoxxxx_00 = QGroupBox(
            '백테스팅 결과 분석', self.ui.dialog_icos
        )

        # 분석 활성화 체크박스 (메인 토글)
        self.ui.analysis_checkBoxxx_00 = self.wc.setCheckBox(
            '분석 활성화 (비활성 시 기본 이미지만 전송)',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_00.setToolTip(TOOLTIPS['analysis_enabled'])
        self.ui.analysis_checkBoxxx_00.stateChanged.connect(
            self._on_analysis_enabled_changed
        )

        # 상태 표시 라벨
        self.ui.analysis_statusLabel = QLabel(
            '상태: 활성화됨', self.ui.analysis_groupBoxxxx_00
        )
        self.ui.analysis_statusLabel.setStyleSheet(
            'color: #00ff00; font-weight: bold;'
        )

        # -----------------------------------------------------------------
        # Phase A: 필터 분석 옵션
        # -----------------------------------------------------------------
        self.ui.analysis_labelllll_01 = QLabel(
            'Phase A: 필터 분석', self.ui.analysis_groupBoxxxx_00
        )
        self.ui.analysis_labelllll_01.setStyleSheet(
            'color: #87ceeb; font-weight: bold;'
        )

        # 필터 효과 분석 (통계 유의성 검정)
        self.ui.analysis_checkBoxxx_01 = self.wc.setCheckBox(
            '필터 효과 분석',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_01.setToolTip(TOOLTIPS['filter_effects'])

        # 최적 임계값 탐색
        self.ui.analysis_checkBoxxx_02 = self.wc.setCheckBox(
            '최적 임계값 탐색',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_02.setToolTip(TOOLTIPS['optimal_thresholds'])

        # 필터 조합 분석
        self.ui.analysis_checkBoxxx_03 = self.wc.setCheckBox(
            '필터 조합 분석',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_03.setToolTip(TOOLTIPS['filter_combinations'])

        # 필터 안정성 검증
        self.ui.analysis_checkBoxxx_04 = self.wc.setCheckBox(
            '필터 안정성 검증',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_04.setToolTip(TOOLTIPS['filter_stability'])

        # 필터 조건식 자동 생성
        self.ui.analysis_checkBoxxx_05 = self.wc.setCheckBox(
            '필터 조건식 자동 생성',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_05.setToolTip(TOOLTIPS['generate_code'])

        # -----------------------------------------------------------------
        # ML 분석 옵션
        # -----------------------------------------------------------------
        self.ui.analysis_labelllll_02 = QLabel(
            'ML 분석', self.ui.analysis_groupBoxxxx_00
        )
        self.ui.analysis_labelllll_02.setStyleSheet(
            'color: #87ceeb; font-weight: bold;'
        )

        # ML 위험도 예측
        self.ui.analysis_checkBoxxx_06 = self.wc.setCheckBox(
            'ML 위험도 예측',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_06.setToolTip(TOOLTIPS['ml_risk'])

        # ML 특성 중요도 분석
        self.ui.analysis_checkBoxxx_07 = self.wc.setCheckBox(
            'ML 특성 중요도',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_07.setToolTip(TOOLTIPS['ml_importance'])

        # ML 모드 선택 (train/test)
        self.ui.analysis_labelllll_03 = QLabel(
            'ML 모드:', self.ui.analysis_groupBoxxxx_00
        )
        self.ui.analysis_comboBoxxx_01 = self.wc.setCombobox(
            self.ui.analysis_groupBoxxxx_00,
            items=['학습(train)', '테스트(test)']
        )
        self.ui.analysis_comboBoxxx_01.setToolTip(TOOLTIPS['ml_mode'])

        # -----------------------------------------------------------------
        # Phase C: 세그먼트 분석 옵션
        # -----------------------------------------------------------------
        self.ui.analysis_labelllll_04 = QLabel(
            'Phase C: 세그먼트 분석', self.ui.analysis_groupBoxxxx_00
        )
        self.ui.analysis_labelllll_04.setStyleSheet(
            'color: #87ceeb; font-weight: bold;'
        )

        # 세그먼트 분석 활성화
        self.ui.analysis_checkBoxxx_08 = self.wc.setCheckBox(
            '세그먼트 분석 활성화',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_08.setToolTip(TOOLTIPS['segment_enabled'])

        # Optuna 최적화 사용
        self.ui.analysis_checkBoxxx_09 = self.wc.setCheckBox(
            'Optuna 최적화',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_09.setToolTip(TOOLTIPS['segment_optuna'])

        # 템플릿 비교
        self.ui.analysis_checkBoxxx_10 = self.wc.setCheckBox(
            '템플릿 비교',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_10.setToolTip(TOOLTIPS['segment_template'])

        # 분석 결과 자동 저장
        self.ui.analysis_checkBoxxx_11 = self.wc.setCheckBox(
            '분석 결과 자동 저장',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )
        self.ui.analysis_checkBoxxx_11.setToolTip(TOOLTIPS['segment_autosave'])

        # -----------------------------------------------------------------
        # 알림 설정
        # -----------------------------------------------------------------
        self.ui.analysis_labelllll_05 = QLabel(
            '알림 설정', self.ui.analysis_groupBoxxxx_00
        )
        self.ui.analysis_labelllll_05.setStyleSheet(
            'color: #87ceeb; font-weight: bold;'
        )

        self.ui.analysis_labelllll_06 = QLabel(
            '텔레그램 알림:', self.ui.analysis_groupBoxxxx_00
        )
        self.ui.analysis_comboBoxxx_02 = self.wc.setCombobox(
            self.ui.analysis_groupBoxxxx_00,
            items=['상세', '요약', '없음']
        )
        self.ui.analysis_comboBoxxx_02.setToolTip(TOOLTIPS['notification_level'])

        # =====================================================================
        # 섹션 2: ICOS 반복 최적화
        # =====================================================================
        self.ui.icos_groupBoxxxx_00 = QGroupBox(
            'ICOS 반복 최적화 (Iterative Condition Optimization)', self.ui.dialog_icos
        )

        # ICOS 활성화 체크박스
        self.ui.icos_checkBoxxx_00 = self.wc.setCheckBox(
            'ICOS 활성화',
            self.ui.icos_groupBoxxxx_00,
            checked=False,
            style=style_ck_bx
        )
        self.ui.icos_checkBoxxx_00.setToolTip(TOOLTIPS['icos_enabled'])
        self.ui.icos_checkBoxxx_00.stateChanged.connect(
            self._on_icos_enabled_changed
        )

        # ICOS 안내 라벨
        self.ui.icos_labellllll_00 = QLabel(
            '* "백테스트" 유형에서만 작동 (그리드/베이지안/GA/조건최적화 제외)\n'
            '* 활성화 시 백테스트 실행 후 조건식 자동 개선',
            self.ui.icos_groupBoxxxx_00
        )
        self.ui.icos_labellllll_00.setStyleSheet('color: #ffa500;')  # 주의 색상

        # 상태 표시 라벨
        self.ui.icos_statusLabel = QLabel('상태: 비활성', self.ui.icos_groupBoxxxx_00)
        self.ui.icos_statusLabel.setStyleSheet('color: #888888;')

        # -----------------------------------------------------------------
        # ICOS 기본 설정 (축소된 형태)
        # -----------------------------------------------------------------
        # 최대 반복 횟수
        self.ui.icos_labellllll_02 = QLabel(
            '최대 반복:', self.ui.icos_groupBoxxxx_00
        )
        self.ui.icos_lineEdittt_01 = self.wc.setLineedit(
            self.ui.icos_groupBoxxxx_00,
            ltext='5',
            style=style_bc_dk
        )
        self.ui.icos_lineEdittt_01.setToolTip(TOOLTIPS['icos_max_iterations'])

        # 수렴 기준값
        self.ui.icos_labellllll_03 = QLabel(
            '수렴 기준(%):', self.ui.icos_groupBoxxxx_00
        )
        self.ui.icos_lineEdittt_02 = self.wc.setLineedit(
            self.ui.icos_groupBoxxxx_00,
            ltext='5',
            style=style_bc_dk
        )
        self.ui.icos_lineEdittt_02.setToolTip(TOOLTIPS['icos_convergence'])

        # 최적화 기준
        self.ui.icos_labellllll_04 = QLabel(
            '최적화 기준:', self.ui.icos_groupBoxxxx_00
        )
        self.ui.icos_comboBoxxx_01 = self.wc.setCombobox(
            self.ui.icos_groupBoxxxx_00,
            items=['수익금', '승률', '수익팩터', '샤프비율', 'MDD', '복합점수']
        )
        self.ui.icos_comboBoxxx_01.setToolTip(TOOLTIPS['icos_metric'])

        # 최적화 방법
        self.ui.icos_labellllll_07 = QLabel(
            '최적화 방법:', self.ui.icos_groupBoxxxx_00
        )
        self.ui.icos_comboBoxxx_02 = self.wc.setCombobox(
            self.ui.icos_groupBoxxxx_00,
            items=['그리드서치', '유전알고리즘', '베이지안(Optuna)']
        )
        self.ui.icos_comboBoxxx_02.setToolTip(TOOLTIPS['icos_method'])

        # =====================================================================
        # 버튼들 (설정 관리용)
        # =====================================================================
        self.ui.icos_pushButton_03 = self.wc.setPushbutton(
            '설정 저장',
            box=self.ui.dialog_icos,
            click=self.ui.icosButtonClicked_03
        )
        self.ui.icos_pushButton_04 = self.wc.setPushbutton(
            '설정 로딩',
            box=self.ui.dialog_icos,
            click=self.ui.icosButtonClicked_04
        )
        self.ui.icos_pushButton_05 = self.wc.setPushbutton(
            '기본값 복원',
            box=self.ui.dialog_icos,
            click=self.ui.icosButtonClicked_05
        )
        self.ui.icos_pushButton_06 = self.wc.setPushbutton(
            '닫기',
            box=self.ui.dialog_icos,
            click=lambda: self.ui.dialog_icos.close()
        )

        # =====================================================================
        # 결과 표시 영역
        # =====================================================================
        self.ui.icos_groupBoxxxx_05 = QGroupBox('실행 로그', self.ui.dialog_icos)
        self.ui.icos_textEditxxx_01 = self.wc.setTextEdit(
            self.ui.icos_groupBoxxxx_05,
            vscroll=True
        )

        # 진행률 바
        self.ui.icos_progressBar_01 = self.wc.setProgressBar(self.ui.dialog_icos)

        # 레이아웃 설정
        self._set_layout()

        # 저장된 설정 자동 로드
        self._auto_load_config()

        # 초기 로그 메시지
        if self.ui.icos_enabled:
            self.ui.icos_textEditxxx_01.append(
                '<font color="#7cfc00">ICOS 모드가 활성화되어 있습니다. '
                '백테스트 실행 시 자동 조건식 개선이 수행됩니다.</font>'
            )
        else:
            self.ui.icos_textEditxxx_01.append(
                '<font color="#87ceeb">백테스팅 결과 분석 설정이 로드되었습니다.</font>'
            )
            self.ui.icos_textEditxxx_01.append(
                '<font color="#888888">분석 옵션을 설정한 후 백테스트를 실행하세요.</font>'
            )

    def _on_analysis_enabled_changed(self, state):
        """분석 활성화 체크박스 상태 변경 핸들러."""
        self.ui.analysis_enabled = (state == 2)  # Qt.Checked = 2
        if self.ui.analysis_enabled:
            self.ui.analysis_statusLabel.setText('상태: 활성화됨')
            self.ui.analysis_statusLabel.setStyleSheet(
                'color: #00ff00; font-weight: bold;'
            )
            self.ui.icos_textEditxxx_01.append(
                '<font color="#7cfc00">백테스팅 결과 분석이 활성화되었습니다.</font>'
            )
            # 하위 옵션들 활성화
            self._set_analysis_options_enabled(True)
        else:
            self.ui.analysis_statusLabel.setText('상태: 비활성 (기본 이미지만 전송)')
            self.ui.analysis_statusLabel.setStyleSheet(
                'color: #ffa500; font-weight: bold;'
            )
            self.ui.icos_textEditxxx_01.append(
                '<font color="#ffa500">백테스팅 결과 분석 비활성화. '
                '기본 이미지 2개만 텔레그램 전송됩니다.</font>'
            )
            # 하위 옵션들 비활성화
            self._set_analysis_options_enabled(False)

    def _set_analysis_options_enabled(self, enabled: bool):
        """분석 하위 옵션들의 활성화 상태 설정."""
        widgets = [
            self.ui.analysis_checkBoxxx_01,
            self.ui.analysis_checkBoxxx_02,
            self.ui.analysis_checkBoxxx_03,
            self.ui.analysis_checkBoxxx_04,
            self.ui.analysis_checkBoxxx_05,
            self.ui.analysis_checkBoxxx_06,
            self.ui.analysis_checkBoxxx_07,
            self.ui.analysis_comboBoxxx_01,
            self.ui.analysis_checkBoxxx_08,
            self.ui.analysis_checkBoxxx_09,
            self.ui.analysis_checkBoxxx_10,
            self.ui.analysis_checkBoxxx_11,
            self.ui.analysis_comboBoxxx_02,
        ]
        for widget in widgets:
            widget.setEnabled(enabled)

    def _on_icos_enabled_changed(self, state):
        """ICOS 활성화 체크박스 상태 변경 핸들러."""
        self.ui.icos_enabled = (state == 2)  # Qt.Checked = 2
        if self.ui.icos_enabled:
            self.ui.icos_statusLabel.setText('상태: 활성화됨')
            self.ui.icos_statusLabel.setStyleSheet('color: #00ff00; font-weight: bold;')
            self.ui.icos_textEditxxx_01.append(
                '<font color="#7cfc00">ICOS 모드 활성화됨. '
                '백테스트 실행 시 조건식 자동 개선이 수행됩니다.</font>'
            )
            # ICOS 하위 옵션들 활성화
            self._set_icos_options_enabled(True)
        else:
            self.ui.icos_statusLabel.setText('상태: 비활성')
            self.ui.icos_statusLabel.setStyleSheet('color: #888888;')
            self.ui.icos_textEditxxx_01.append(
                '<font color="#888888">ICOS 모드 비활성화됨.</font>'
            )
            # ICOS 하위 옵션들 비활성화
            self._set_icos_options_enabled(False)

    def _set_icos_options_enabled(self, enabled: bool):
        """ICOS 하위 옵션들의 활성화 상태 설정."""
        widgets = [
            self.ui.icos_lineEdittt_01,
            self.ui.icos_lineEdittt_02,
            self.ui.icos_comboBoxxx_01,
            self.ui.icos_comboBoxxx_02,
        ]
        for widget in widgets:
            widget.setEnabled(enabled)

    def _auto_load_config(self):
        """다이얼로그 초기화 시 저장된 설정 자동 로드.

        저장된 설정 파일이 있으면 자동으로 로드하여 이전 상태를 복원합니다.
        설정 파일이 없으면 기본값을 유지합니다.
        """
        import json
        from pathlib import Path
        from ui.ui_button_clicked_icos import (
            _apply_analysis_config,
            _apply_icos_config,
            ANALYSIS_DEFAULTS,
        )

        # 통합 설정 파일 경로
        main_path = Path('./_database/icos_analysis_config.json')
        legacy_path = Path('./_database/icos_config.json')

        loaded_path = None
        if main_path.exists():
            loaded_path = main_path
        elif legacy_path.exists():
            loaded_path = legacy_path

        if loaded_path is None:
            # 설정 파일 없음 - 기본값 유지
            return

        try:
            with open(loaded_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)

            # 새 형식인지 확인
            if 'analysis' in config_dict:
                _apply_analysis_config(self.ui, config_dict.get('analysis', {}))
                _apply_icos_config(self.ui, config_dict.get('icos', {}))
            else:
                # 기존 형식 (ICOS만)
                _apply_icos_config(self.ui, config_dict)
                _apply_analysis_config(self.ui, ANALYSIS_DEFAULTS)

            # 상태 업데이트 (체크박스 상태 동기화)
            self.ui.icos_enabled = self.ui.icos_checkBoxxx_00.isChecked()
            self.ui.analysis_enabled = self.ui.analysis_checkBoxxx_00.isChecked()

            # ICOS 옵션 활성화 상태 업데이트
            self._set_icos_options_enabled(self.ui.icos_enabled)

            # 상태 라벨 업데이트
            if self.ui.icos_enabled:
                self.ui.icos_statusLabel.setText('상태: 활성화됨')
                self.ui.icos_statusLabel.setStyleSheet(
                    'color: #00ff00; font-weight: bold;'
                )
            else:
                self.ui.icos_statusLabel.setText('상태: 비활성')
                self.ui.icos_statusLabel.setStyleSheet('color: #888888;')

            # 디버그: 로드된 설정 로그
            if hasattr(self.ui, 'icos_textEditxxx_01'):
                self.ui.icos_textEditxxx_01.append(
                    f'<font color="#888888">[DEBUG] _auto_load_config 완료: '
                    f'icos_enabled={self.ui.icos_enabled}, '
                    f'analysis_enabled={self.ui.analysis_enabled}</font>'
                )

        except Exception as e:
            # 설정 로드 실패 시 기본값 유지
            if hasattr(self.ui, 'icos_textEditxxx_01'):
                self.ui.icos_textEditxxx_01.append(
                    f'<font color="#ff8800">[DEBUG] _auto_load_config 오류: {e}</font>'
                )

    def _set_layout(self):
        """위젯 레이아웃 설정."""
        dialog_width = 620
        margin = 10
        group_width = dialog_width - 2 * margin

        # =====================================================================
        # 섹션 1: 백테스팅 결과 분석 (Analysis)
        # =====================================================================
        analysis_y = 10
        self.ui.analysis_groupBoxxxx_00.setGeometry(
            margin, analysis_y, group_width, 310
        )

        # 활성화 체크박스 및 상태
        self.ui.analysis_checkBoxxx_00.setGeometry(10, 22, 350, 25)
        self.ui.analysis_statusLabel.setGeometry(450, 22, 140, 25)

        # Phase A: 필터 분석
        self.ui.analysis_labelllll_01.setGeometry(10, 52, 150, 20)
        self.ui.analysis_checkBoxxx_01.setGeometry(10, 75, 140, 22)
        self.ui.analysis_checkBoxxx_02.setGeometry(155, 75, 140, 22)
        self.ui.analysis_checkBoxxx_03.setGeometry(300, 75, 140, 22)
        self.ui.analysis_checkBoxxx_04.setGeometry(445, 75, 140, 22)
        self.ui.analysis_checkBoxxx_05.setGeometry(10, 100, 180, 22)

        # ML 분석
        self.ui.analysis_labelllll_02.setGeometry(10, 130, 100, 20)
        self.ui.analysis_checkBoxxx_06.setGeometry(10, 153, 140, 22)
        self.ui.analysis_checkBoxxx_07.setGeometry(155, 153, 140, 22)
        self.ui.analysis_labelllll_03.setGeometry(310, 153, 60, 22)
        self.ui.analysis_comboBoxxx_01.setGeometry(375, 150, 120, 25)

        # Phase C: 세그먼트 분석
        self.ui.analysis_labelllll_04.setGeometry(10, 185, 200, 20)
        self.ui.analysis_checkBoxxx_08.setGeometry(10, 208, 160, 22)
        self.ui.analysis_checkBoxxx_09.setGeometry(175, 208, 130, 22)
        self.ui.analysis_checkBoxxx_10.setGeometry(310, 208, 110, 22)
        self.ui.analysis_checkBoxxx_11.setGeometry(425, 208, 160, 22)

        # 알림 설정
        self.ui.analysis_labelllll_05.setGeometry(10, 240, 100, 20)
        self.ui.analysis_labelllll_06.setGeometry(10, 265, 100, 22)
        self.ui.analysis_comboBoxxx_02.setGeometry(115, 262, 100, 25)

        # =====================================================================
        # 섹션 2: ICOS 반복 최적화 (미구현)
        # =====================================================================
        icos_y = analysis_y + 320
        self.ui.icos_groupBoxxxx_00.setGeometry(
            margin, icos_y, group_width, 140
        )

        # ICOS 활성화 및 상태
        self.ui.icos_checkBoxxx_00.setGeometry(10, 22, 150, 25)
        self.ui.icos_statusLabel.setGeometry(170, 22, 180, 25)
        self.ui.icos_labellllll_00.setGeometry(360, 18, 230, 35)

        # ICOS 설정 (한 줄로 축소)
        self.ui.icos_labellllll_02.setGeometry(10, 60, 70, 22)
        self.ui.icos_lineEdittt_01.setGeometry(80, 57, 45, 25)
        self.ui.icos_labellllll_03.setGeometry(135, 60, 85, 22)
        self.ui.icos_lineEdittt_02.setGeometry(220, 57, 45, 25)
        self.ui.icos_labellllll_04.setGeometry(275, 60, 80, 22)
        self.ui.icos_comboBoxxx_01.setGeometry(355, 57, 90, 25)
        self.ui.icos_labellllll_07.setGeometry(10, 95, 80, 22)
        self.ui.icos_comboBoxxx_02.setGeometry(90, 92, 140, 25)

        # =====================================================================
        # 버튼들
        # =====================================================================
        button_y = icos_y + 150
        self.ui.icos_pushButton_03.setGeometry(margin, button_y, 100, 32)
        self.ui.icos_pushButton_04.setGeometry(margin + 110, button_y, 100, 32)
        self.ui.icos_pushButton_05.setGeometry(margin + 220, button_y, 100, 32)
        self.ui.icos_pushButton_06.setGeometry(group_width - 90, button_y, 100, 32)

        # =====================================================================
        # 결과 표시 영역 (로그 영역 확대: 130px → 200px)
        # =====================================================================
        log_y = button_y + 42
        self.ui.icos_groupBoxxxx_05.setGeometry(margin, log_y, group_width, 200)
        self.ui.icos_textEditxxx_01.setGeometry(10, 20, group_width - 20, 170)

        # 진행률 바 (로그 영역 확대에 따라 위치 조정)
        progress_y = log_y + 210
        self.ui.icos_progressBar_01.setGeometry(margin, progress_y, group_width, 25)

        # 다이얼로그 크기 설정
        dialog_height = progress_y + 40
        self.ui.dialog_icos.setFixedSize(dialog_width, dialog_height)
