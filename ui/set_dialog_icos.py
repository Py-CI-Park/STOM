"""
ICOS (반복적 조건식 개선 시스템) 설정 다이얼로그.

Iterative Condition Optimization System Configuration Dialog.

ICOS 기능 활성화 및 파라미터 설정을 위한 UI 다이얼로그입니다.

개선된 워크플로우:
1. Alt+I로 ICOS 다이얼로그 열기
2. "ICOS 활성화" 체크박스 활성화
3. 필요한 설정 조정
4. 백테스트 스케줄러에서 조건식 선택
5. 백테스트 버튼 클릭 → ICOS 모드로 실행

작성일: 2026-01-12
수정일: 2026-01-13
브랜치: feature/iterative-condition-optimizer
"""

from PyQt5.QtWidgets import QGroupBox, QLabel
from PyQt5.QtGui import QFont
from ui.set_style import style_ck_bx, style_bc_dk


class SetDialogICOS:
    """ICOS 설정 다이얼로그 클래스.

    ICOS 관련 설정을 입력받는 다이얼로그를 생성합니다.
    백테스트 실행 시 ICOS 활성화 여부에 따라 자동으로 ICOS 모드로 전환됩니다.

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
        """ICOS 설정 다이얼로그 UI 구성."""
        # 메인 다이얼로그 생성
        self.ui.dialog_icos = self.wc.setDialog('STOM ICOS - 반복적 조건식 개선 시스템')
        self.ui.dialog_icos.geometry().center()

        # ICOS 활성화 상태 변수 초기화
        self.ui.icos_enabled = False

        # =====================================================================
        # 상단: ICOS 활성화 영역 (눈에 띄게)
        # =====================================================================
        self.ui.icos_groupBoxxxx_00 = QGroupBox('ICOS 모드', self.ui.dialog_icos)

        # ICOS 활성화 체크박스 (큰 폰트로 강조)
        self.ui.icos_checkBoxxx_00 = self.wc.setCheckBox(
            'ICOS 활성화 (백테스트 시 자동 적용)',
            self.ui.icos_groupBoxxxx_00,
            checked=False,
            style=style_ck_bx
        )
        # 체크박스 변경 시 상태 업데이트
        self.ui.icos_checkBoxxx_00.stateChanged.connect(self._on_icos_enabled_changed)

        self.ui.icos_labellllll_00 = QLabel(
            '활성화 시 백테스트 버튼 클릭으로 ICOS가 실행됩니다.\n'
            '스케줄러에서 선택한 조건식과 기간 설정이 사용됩니다.',
            self.ui.icos_groupBoxxxx_00
        )

        # 상태 표시 라벨
        self.ui.icos_statusLabel = QLabel('상태: 비활성', self.ui.icos_groupBoxxxx_00)

        # =====================================================================
        # 그룹박스 1: 기본 설정
        # =====================================================================
        self.ui.icos_groupBoxxxx_01 = QGroupBox('기본 설정', self.ui.dialog_icos)

        # 최대 반복 횟수
        self.ui.icos_labellllll_02 = QLabel('최대 반복 횟수', self.ui.icos_groupBoxxxx_01)
        self.ui.icos_lineEdittt_01 = self.wc.setLineedit(
            self.ui.icos_groupBoxxxx_01,
            ltext='5',
            style=style_bc_dk
        )

        # 수렴 기준값
        self.ui.icos_labellllll_03 = QLabel('수렴 기준값 (%)', self.ui.icos_groupBoxxxx_01)
        self.ui.icos_lineEdittt_02 = self.wc.setLineedit(
            self.ui.icos_groupBoxxxx_01,
            ltext='5',
            style=style_bc_dk
        )

        # 최적화 메트릭 선택
        self.ui.icos_labellllll_04 = QLabel('최적화 기준', self.ui.icos_groupBoxxxx_01)
        self.ui.icos_comboBoxxx_01 = self.wc.setCombobox(
            self.ui.icos_groupBoxxxx_01,
            items=['수익금', '승률', '수익팩터', '샤프비율', 'MDD', '복합점수']
        )

        # =====================================================================
        # 그룹박스 2: 필터 생성 설정
        # =====================================================================
        self.ui.icos_groupBoxxxx_02 = QGroupBox('필터 생성 설정', self.ui.dialog_icos)

        # 최대 필터 수
        self.ui.icos_labellllll_05 = QLabel('반복당 최대 필터 수', self.ui.icos_groupBoxxxx_02)
        self.ui.icos_lineEdittt_03 = self.wc.setLineedit(
            self.ui.icos_groupBoxxxx_02,
            ltext='3',
            style=style_bc_dk
        )

        # 최소 샘플 수
        self.ui.icos_labellllll_06 = QLabel('최소 샘플 수', self.ui.icos_groupBoxxxx_02)
        self.ui.icos_lineEdittt_04 = self.wc.setLineedit(
            self.ui.icos_groupBoxxxx_02,
            ltext='30',
            style=style_bc_dk
        )

        # 세그먼트 분석 사용
        self.ui.icos_checkBoxxx_01 = self.wc.setCheckBox(
            '세그먼트 분석 활용',
            self.ui.icos_groupBoxxxx_02,
            checked=True,
            style=style_ck_bx
        )

        # =====================================================================
        # 그룹박스 3: 최적화 알고리즘 설정
        # =====================================================================
        self.ui.icos_groupBoxxxx_03 = QGroupBox('최적화 알고리즘', self.ui.dialog_icos)

        # 최적화 방법 선택
        self.ui.icos_labellllll_07 = QLabel('최적화 방법', self.ui.icos_groupBoxxxx_03)
        self.ui.icos_comboBoxxx_02 = self.wc.setCombobox(
            self.ui.icos_groupBoxxxx_03,
            items=['그리드서치', '유전알고리즘', '베이지안(Optuna)']
        )

        # 최적화 횟수/시도 수
        self.ui.icos_labellllll_08 = QLabel('최적화 시도 횟수', self.ui.icos_groupBoxxxx_03)
        self.ui.icos_lineEdittt_05 = self.wc.setLineedit(
            self.ui.icos_groupBoxxxx_03,
            ltext='100',
            style=style_bc_dk
        )

        # Walk-Forward 검증
        self.ui.icos_checkBoxxx_02 = self.wc.setCheckBox(
            'Walk-Forward 검증 활성화',
            self.ui.icos_groupBoxxxx_03,
            checked=False,
            style=style_ck_bx
        )

        # Walk-Forward 폴드 수
        self.ui.icos_labellllll_09 = QLabel('W-F 폴드 수', self.ui.icos_groupBoxxxx_03)
        self.ui.icos_lineEdittt_06 = self.wc.setLineedit(
            self.ui.icos_groupBoxxxx_03,
            ltext='5',
            style=style_bc_dk
        )

        # =====================================================================
        # 그룹박스 4: 저장 설정
        # =====================================================================
        self.ui.icos_groupBoxxxx_04 = QGroupBox('저장 설정', self.ui.dialog_icos)

        # 반복 결과 저장
        self.ui.icos_checkBoxxx_03 = self.wc.setCheckBox(
            '반복 결과 저장',
            self.ui.icos_groupBoxxxx_04,
            checked=True,
            style=style_ck_bx
        )

        # 최종 조건식 자동 저장
        self.ui.icos_checkBoxxx_04 = self.wc.setCheckBox(
            '최종 조건식 자동 저장',
            self.ui.icos_groupBoxxxx_04,
            checked=True,
            style=style_ck_bx
        )

        # 상세 로그 출력
        self.ui.icos_checkBoxxx_05 = self.wc.setCheckBox(
            '상세 로그 출력',
            self.ui.icos_groupBoxxxx_04,
            checked=False,
            style=style_ck_bx
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

        # ICOS 중지 버튼 (실행 중일 때만 사용)
        self.ui.icos_pushButton_02 = self.wc.setPushbutton(
            'ICOS 중지',
            box=self.ui.dialog_icos,
            color=2,
            click=self.ui.icosButtonClicked_02
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

    def _on_icos_enabled_changed(self, state):
        """ICOS 활성화 체크박스 상태 변경 핸들러."""
        self.ui.icos_enabled = (state == 2)  # Qt.Checked = 2
        if self.ui.icos_enabled:
            self.ui.icos_statusLabel.setText('상태: 활성화됨 (백테스트 시 ICOS 모드)')
            self.ui.icos_statusLabel.setStyleSheet('color: #00ff00; font-weight: bold;')
            self.ui.icos_textEditxxx_01.append(
                '<font color="#7cfc00">ICOS 모드 활성화됨. '
                '백테스트 버튼으로 실행하세요.</font>'
            )
        else:
            self.ui.icos_statusLabel.setText('상태: 비활성')
            self.ui.icos_statusLabel.setStyleSheet('color: #888888;')
            self.ui.icos_textEditxxx_01.append(
                '<font color="#ffa500">ICOS 모드 비활성화됨. '
                '일반 백테스트로 실행됩니다.</font>'
            )

    def _set_layout(self):
        """위젯 레이아웃 설정."""
        # 상단: ICOS 활성화 영역
        self.ui.icos_groupBoxxxx_00.setGeometry(10, 10, 580, 90)
        self.ui.icos_checkBoxxx_00.setGeometry(10, 22, 350, 25)
        self.ui.icos_labellllll_00.setGeometry(10, 48, 400, 35)
        self.ui.icos_statusLabel.setGeometry(420, 22, 150, 25)

        # 그룹박스 1: 기본 설정
        self.ui.icos_groupBoxxxx_01.setGeometry(10, 105, 580, 70)
        self.ui.icos_labellllll_02.setGeometry(10, 25, 120, 20)
        self.ui.icos_lineEdittt_01.setGeometry(130, 22, 60, 25)
        self.ui.icos_labellllll_03.setGeometry(210, 25, 120, 20)
        self.ui.icos_lineEdittt_02.setGeometry(330, 22, 60, 25)
        self.ui.icos_labellllll_04.setGeometry(410, 25, 80, 20)
        self.ui.icos_comboBoxxx_01.setGeometry(490, 22, 80, 25)

        # 그룹박스 2: 필터 생성 설정
        self.ui.icos_groupBoxxxx_02.setGeometry(10, 180, 580, 70)
        self.ui.icos_labellllll_05.setGeometry(10, 25, 130, 20)
        self.ui.icos_lineEdittt_03.setGeometry(140, 22, 60, 25)
        self.ui.icos_labellllll_06.setGeometry(220, 25, 100, 20)
        self.ui.icos_lineEdittt_04.setGeometry(320, 22, 60, 25)
        self.ui.icos_checkBoxxx_01.setGeometry(400, 22, 170, 25)

        # 그룹박스 3: 최적화 알고리즘 설정
        self.ui.icos_groupBoxxxx_03.setGeometry(10, 255, 580, 100)
        self.ui.icos_labellllll_07.setGeometry(10, 25, 100, 20)
        self.ui.icos_comboBoxxx_02.setGeometry(110, 22, 150, 25)
        self.ui.icos_labellllll_08.setGeometry(280, 25, 120, 20)
        self.ui.icos_lineEdittt_05.setGeometry(400, 22, 60, 25)
        self.ui.icos_checkBoxxx_02.setGeometry(10, 60, 200, 25)
        self.ui.icos_labellllll_09.setGeometry(220, 60, 100, 20)
        self.ui.icos_lineEdittt_06.setGeometry(320, 57, 60, 25)

        # 그룹박스 4: 저장 설정
        self.ui.icos_groupBoxxxx_04.setGeometry(10, 360, 580, 55)
        self.ui.icos_checkBoxxx_03.setGeometry(10, 22, 150, 25)
        self.ui.icos_checkBoxxx_04.setGeometry(180, 22, 180, 25)
        self.ui.icos_checkBoxxx_05.setGeometry(380, 22, 150, 25)

        # 버튼들
        self.ui.icos_pushButton_03.setGeometry(10, 420, 100, 32)
        self.ui.icos_pushButton_04.setGeometry(120, 420, 100, 32)
        self.ui.icos_pushButton_05.setGeometry(230, 420, 100, 32)
        self.ui.icos_pushButton_02.setGeometry(480, 420, 100, 32)

        # 결과 표시 영역
        self.ui.icos_groupBoxxxx_05.setGeometry(10, 460, 580, 150)
        self.ui.icos_textEditxxx_01.setGeometry(10, 20, 560, 120)

        # 진행률 바
        self.ui.icos_progressBar_01.setGeometry(10, 615, 580, 25)

        # 다이얼로그 크기 설정 (더 컴팩트하게)
        self.ui.dialog_icos.setFixedSize(600, 650)
