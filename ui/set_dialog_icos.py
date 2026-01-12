"""
ICOS (반복적 조건식 개선 시스템) 설정 다이얼로그.

Iterative Condition Optimization System Configuration Dialog.

ICOS 기능 활성화 및 파라미터 설정을 위한 UI 다이얼로그입니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from PyQt5.QtWidgets import QGroupBox, QLabel
from ui.set_style import style_ck_bx, style_bc_dk


class SetDialogICOS:
    """ICOS 설정 다이얼로그 클래스.

    ICOS 관련 설정을 입력받는 다이얼로그를 생성합니다.

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

        # 그룹박스 1: 기본 설정
        self.ui.icos_groupBoxxxx_01 = QGroupBox('기본 설정', self.ui.dialog_icos)

        self.ui.icos_labellllll_01 = QLabel(
            '▣ ICOS는 반복적 백테스팅을 통해 조건식을 점진적으로 개선합니다.',
            self.ui.icos_groupBoxxxx_01
        )

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

        # 그룹박스 2: 필터 생성 설정
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

        # 그룹박스 3: 최적화 알고리즘 설정
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

        # 그룹박스 4: 저장 설정
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

        # 버튼들
        self.ui.icos_pushButton_01 = self.wc.setPushbutton(
            'ICOS 시작',
            box=self.ui.dialog_icos,
            color=2,
            click=self.ui.icosButtonClicked_01
        )
        self.ui.icos_pushButton_02 = self.wc.setPushbutton(
            'ICOS 중지',
            box=self.ui.dialog_icos,
            color=2,
            click=self.ui.icosButtonClicked_02
        )
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

        # 결과 표시 영역
        self.ui.icos_groupBoxxxx_05 = QGroupBox('실행 결과', self.ui.dialog_icos)
        self.ui.icos_textEditxxx_01 = self.wc.setTextEdit(
            self.ui.icos_groupBoxxxx_05,
            vscroll=True
        )

        # 진행률 바
        self.ui.icos_progressBar_01 = self.wc.setProgressBar(self.ui.dialog_icos)

        # 레이아웃 설정
        self._set_layout()

    def _set_layout(self):
        """위젯 레이아웃 설정."""
        # 그룹박스 1: 기본 설정
        self.ui.icos_groupBoxxxx_01.setGeometry(10, 10, 580, 130)
        self.ui.icos_labellllll_01.setGeometry(10, 20, 560, 20)
        self.ui.icos_labellllll_02.setGeometry(10, 50, 120, 20)
        self.ui.icos_lineEdittt_01.setGeometry(130, 47, 60, 25)
        self.ui.icos_labellllll_03.setGeometry(210, 50, 120, 20)
        self.ui.icos_lineEdittt_02.setGeometry(330, 47, 60, 25)
        self.ui.icos_labellllll_04.setGeometry(10, 85, 120, 20)
        self.ui.icos_comboBoxxx_01.setGeometry(130, 82, 130, 25)

        # 그룹박스 2: 필터 생성 설정
        self.ui.icos_groupBoxxxx_02.setGeometry(10, 145, 580, 100)
        self.ui.icos_labellllll_05.setGeometry(10, 25, 130, 20)
        self.ui.icos_lineEdittt_03.setGeometry(140, 22, 60, 25)
        self.ui.icos_labellllll_06.setGeometry(220, 25, 100, 20)
        self.ui.icos_lineEdittt_04.setGeometry(320, 22, 60, 25)
        self.ui.icos_checkBoxxx_01.setGeometry(10, 60, 150, 25)

        # 그룹박스 3: 최적화 알고리즘 설정
        self.ui.icos_groupBoxxxx_03.setGeometry(10, 250, 580, 130)
        self.ui.icos_labellllll_07.setGeometry(10, 25, 100, 20)
        self.ui.icos_comboBoxxx_02.setGeometry(110, 22, 150, 25)
        self.ui.icos_labellllll_08.setGeometry(280, 25, 120, 20)
        self.ui.icos_lineEdittt_05.setGeometry(400, 22, 60, 25)
        self.ui.icos_checkBoxxx_02.setGeometry(10, 60, 200, 25)
        self.ui.icos_labellllll_09.setGeometry(220, 60, 100, 20)
        self.ui.icos_lineEdittt_06.setGeometry(320, 57, 60, 25)

        # 그룹박스 4: 저장 설정
        self.ui.icos_groupBoxxxx_04.setGeometry(10, 385, 580, 80)
        self.ui.icos_checkBoxxx_03.setGeometry(10, 25, 150, 25)
        self.ui.icos_checkBoxxx_04.setGeometry(180, 25, 180, 25)
        self.ui.icos_checkBoxxx_05.setGeometry(380, 25, 150, 25)

        # 버튼들
        self.ui.icos_pushButton_01.setGeometry(10, 475, 100, 32)
        self.ui.icos_pushButton_02.setGeometry(120, 475, 100, 32)
        self.ui.icos_pushButton_03.setGeometry(240, 475, 100, 32)
        self.ui.icos_pushButton_04.setGeometry(350, 475, 100, 32)
        self.ui.icos_pushButton_05.setGeometry(460, 475, 100, 32)

        # 결과 표시 영역
        self.ui.icos_groupBoxxxx_05.setGeometry(10, 515, 580, 180)
        self.ui.icos_textEditxxx_01.setGeometry(10, 20, 560, 150)

        # 진행률 바
        self.ui.icos_progressBar_01.setGeometry(10, 700, 580, 25)

        # 다이얼로그 크기 설정
        self.ui.dialog_icos.setFixedSize(600, 735)
