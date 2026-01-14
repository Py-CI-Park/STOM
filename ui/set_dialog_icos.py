"""
ICOS & 분석 설정 다이얼로그.

ICOS (Iterative Condition Optimization System) 및 백테스팅 결과 분석 설정을 위한 UI.

개선된 구조:
1. 백테스팅 결과 분석: Phase A(필터 분석), ML 분석, Phase C(세그먼트 분석) 개별 설정
2. ICOS 반복 최적화: 미구현 상태로 표시 (향후 개발)

워크플로우:
- 분석 비활성화: 기본 백테스트 → 이미지 2개 텔레그램 전송
- 분석 활성화: 상세 분석 → 단계별 결과 텔레그램 전송

작성일: 2026-01-12
수정일: 2026-01-13
브랜치: feature/enhanced-buy-condition-generator
"""

from PyQt5.QtWidgets import QGroupBox, QLabel
from PyQt5.QtGui import QFont
from ui.set_style import style_ck_bx, style_bc_dk


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

        # 최적 임계값 탐색
        self.ui.analysis_checkBoxxx_02 = self.wc.setCheckBox(
            '최적 임계값 탐색',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )

        # 필터 조합 분석
        self.ui.analysis_checkBoxxx_03 = self.wc.setCheckBox(
            '필터 조합 분석',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )

        # 필터 안정성 검증
        self.ui.analysis_checkBoxxx_04 = self.wc.setCheckBox(
            '필터 안정성 검증',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )

        # 필터 조건식 자동 생성
        self.ui.analysis_checkBoxxx_05 = self.wc.setCheckBox(
            '필터 조건식 자동 생성',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )

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

        # ML 특성 중요도 분석
        self.ui.analysis_checkBoxxx_07 = self.wc.setCheckBox(
            'ML 특성 중요도',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )

        # ML 모드 선택 (train/test)
        self.ui.analysis_labelllll_03 = QLabel(
            'ML 모드:', self.ui.analysis_groupBoxxxx_00
        )
        self.ui.analysis_comboBoxxx_01 = self.wc.setCombobox(
            self.ui.analysis_groupBoxxxx_00,
            items=['학습(train)', '테스트(test)']
        )

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

        # Optuna 최적화 사용
        self.ui.analysis_checkBoxxx_09 = self.wc.setCheckBox(
            'Optuna 최적화',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )

        # 템플릿 비교
        self.ui.analysis_checkBoxxx_10 = self.wc.setCheckBox(
            '템플릿 비교',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )

        # 분석 결과 자동 저장
        self.ui.analysis_checkBoxxx_11 = self.wc.setCheckBox(
            '분석 결과 자동 저장',
            self.ui.analysis_groupBoxxxx_00,
            checked=True,
            style=style_ck_bx
        )

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
        self.ui.icos_checkBoxxx_00.stateChanged.connect(
            self._on_icos_enabled_changed
        )

        # ICOS 안내 라벨
        self.ui.icos_labellllll_00 = QLabel(
            '* 활성화 시 백테스트 실행 후 조건식 자동 개선\n'
            '* 수렴 기준 도달 시 자동 종료',
            self.ui.icos_groupBoxxxx_00
        )
        self.ui.icos_labellllll_00.setStyleSheet('color: #87ceeb;')

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

        # 수렴 기준값
        self.ui.icos_labellllll_03 = QLabel(
            '수렴 기준(%):', self.ui.icos_groupBoxxxx_00
        )
        self.ui.icos_lineEdittt_02 = self.wc.setLineedit(
            self.ui.icos_groupBoxxxx_00,
            ltext='5',
            style=style_bc_dk
        )

        # 최적화 기준
        self.ui.icos_labellllll_04 = QLabel(
            '최적화 기준:', self.ui.icos_groupBoxxxx_00
        )
        self.ui.icos_comboBoxxx_01 = self.wc.setCombobox(
            self.ui.icos_groupBoxxxx_00,
            items=['수익금', '승률', '수익팩터', '샤프비율', 'MDD', '복합점수']
        )

        # 최적화 방법
        self.ui.icos_labellllll_07 = QLabel(
            '최적화 방법:', self.ui.icos_groupBoxxxx_00
        )
        self.ui.icos_comboBoxxx_02 = self.wc.setCombobox(
            self.ui.icos_groupBoxxxx_00,
            items=['그리드서치', '유전알고리즘', '베이지안(Optuna)']
        )

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

        # 초기 로그 메시지
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
        # 결과 표시 영역
        # =====================================================================
        log_y = button_y + 42
        self.ui.icos_groupBoxxxx_05.setGeometry(margin, log_y, group_width, 130)
        self.ui.icos_textEditxxx_01.setGeometry(10, 20, group_width - 20, 100)

        # 진행률 바
        progress_y = log_y + 140
        self.ui.icos_progressBar_01.setGeometry(margin, progress_y, group_width, 25)

        # 다이얼로그 크기 설정
        dialog_height = progress_y + 40
        self.ui.dialog_icos.setFixedSize(dialog_width, dialog_height)
