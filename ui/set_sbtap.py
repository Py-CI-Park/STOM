from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QLabel
from ui.set_style import qfont12, qfont13, qfont14, style_pgbar, style_bc_dk
from ui.set_text import optistandard, optitext, train_period, valid_period, test_period, optimized_count, opti_standard
from utility.setting import columns_bt


class SetStockBack:
    def __init__(self, ui_class, wc):
        self.ui = ui_class
        self.wc = wc
        self.set()

    def set(self):
        self.ui.ss_textEditttt_01 = self.wc.setTextEdit(self.ui.ss_tab, filter_=True, font=qfont14)
        self.ui.ss_textEditttt_02 = self.wc.setTextEdit(self.ui.ss_tab, filter_=True, font=qfont14)
        self.ui.ss_textEditttt_03 = self.wc.setTextEdit(self.ui.ss_tab, visible=False, filter_=True, font=qfont14)
        self.ui.ss_textEditttt_04 = self.wc.setTextEdit(self.ui.ss_tab, visible=False, filter_=True, font=qfont14)
        self.ui.ss_textEditttt_05 = self.wc.setTextEdit(self.ui.ss_tab, visible=False, filter_=True, font=qfont14)
        self.ui.ss_textEditttt_06 = self.wc.setTextEdit(self.ui.ss_tab, visible=False, filter_=True, font=qfont14)
        self.ui.ss_textEditttt_07 = self.wc.setTextEdit(self.ui.ss_tab, visible=False, filter_=True, font=qfont14)
        self.ui.ss_textEditttt_08 = self.wc.setTextEdit(self.ui.ss_tab, visible=False, filter_=True, font=qfont14)

    # =================================================================================================================

        self.ui.szoo_pushButon_01 = self.wc.setPushbutton('확대(esc)', box=self.ui.ss_tab, click=self.ui.szooButtonClicked_01)
        self.ui.szoo_pushButon_02 = self.wc.setPushbutton('확대(esc)', box=self.ui.ss_tab, click=self.ui.szooButtonClicked_02)

        self.ui.stock_esczom_list = [self.ui.szoo_pushButon_01, self.ui.szoo_pushButon_02]

    # =================================================================================================================

        self.ui.ss_tableWidget_01 = self.wc.setTablewidget(self.ui.ss_tab, columns_bt, 32, vscroll=True, clicked=self.ui.CellClicked_06)
        self.ui.ss_comboBoxxxx_01 = self.wc.setCombobox(self.ui.ss_tab, font=qfont12, activated=self.ui.Activated_01)
        self.ui.ss_pushButtonn_01 = self.wc.setPushbutton('백테스트상세기록', box=self.ui.ss_tab, click=self.ui.ssButtonClicked_01, tip='백테스트 상세기록을 불러온다.')
        self.ui.ss_pushButtonn_02 = self.wc.setPushbutton('그래프', box=self.ui.ss_tab, click=self.ui.ssButtonClicked_04, tip='선택된 상세기록의 그래프를 표시한다.')
        self.ui.ss_comboBoxxxx_02 = self.wc.setCombobox(self.ui.ss_tab, font=qfont12, activated=self.ui.Activated_01)
        self.ui.ss_pushButtonn_03 = self.wc.setPushbutton('최적화상세기록', box=self.ui.ss_tab, click=self.ui.ssButtonClicked_02, tip='최적화 상세기록을 불러온다.')
        self.ui.ss_pushButtonn_04 = self.wc.setPushbutton('그래프', box=self.ui.ss_tab, click=self.ui.ssButtonClicked_04, tip='선택된 상세기록의 그래프를 표시한다.')
        self.ui.ss_comboBoxxxx_03 = self.wc.setCombobox(self.ui.ss_tab, font=qfont12, activated=self.ui.Activated_01)
        self.ui.ss_pushButtonn_05 = self.wc.setPushbutton('그외상세기록', box=self.ui.ss_tab, click=self.ui.ssButtonClicked_03, tip='최적화 테스트 및 전진분석 상세기록을 불러온다.')
        self.ui.ss_pushButtonn_06 = self.wc.setPushbutton('그래프', box=self.ui.ss_tab, click=self.ui.ssButtonClicked_04, tip='선택된 상세기록의 그래프를 표시한다.')
        self.ui.ss_pushButtonn_07 = self.wc.setPushbutton('비교', box=self.ui.ss_tab, click=self.ui.ssButtonClicked_05, tip='두개 이상의 그래프를 선택 비교한다.')

        self.ui.stock_detail_list = [
            self.ui.ss_tableWidget_01, self.ui.ss_comboBoxxxx_01, self.ui.ss_pushButtonn_01, self.ui.ss_pushButtonn_02,
            self.ui.ss_comboBoxxxx_02, self.ui.ss_pushButtonn_03, self.ui.ss_pushButtonn_04, self.ui.ss_comboBoxxxx_03,
            self.ui.ss_pushButtonn_05, self.ui.ss_pushButtonn_06, self.ui.ss_pushButtonn_07
        ]

        for widget in self.ui.stock_detail_list:
            widget.setVisible(False)

    # =================================================================================================================

        self.ui.ss_textEditttt_09 = self.wc.setTextEdit(self.ui.ss_tab, visible=False, vscroll=True)
        self.ui.ss_progressBar_01 = self.wc.setProgressBar(self.ui.ss_tab, style=style_pgbar, visible=False)
        self.ui.ss_pushButtonn_08 = self.wc.setPushbutton('백테스트 중지', box=self.ui.ss_tab, click=self.ui.ssButtonClicked_06, color=2, visible=False, tip='(Alt+Enter) 실행중인 백테스트를 중지한다.')

        self.ui.stock_baklog_list = [self.ui.ss_textEditttt_09, self.ui.ss_progressBar_01, self.ui.ss_pushButtonn_08]

    # =================================================================================================================

        self.ui.svjb_comboBoxx_01 = self.wc.setCombobox(self.ui.ss_tab, font=qfont14, activated=self.ui.sActivated_01)
        self.ui.svjb_lineEditt_01 = self.wc.setLineedit(self.ui.ss_tab, font=qfont14, aleft=True, ltext='F2, F3', style=style_bc_dk)
        self.ui.svjb_pushButon_01 = self.wc.setPushbutton('매수전략 로딩(F1)', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_01, color=1)
        self.ui.svjb_pushButon_02 = self.wc.setPushbutton('매수전략 저장(F4)', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_02, color=1, tip='작성된 매수전략을 저장한다.\nCtrl 키와 함께 누르면 코드 테스트 과정을 생략한다.')
        self.ui.svjb_pushButon_03 = self.wc.setPushbutton('매수변수 로딩', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_03, color=1, tip='매수전략에 사용할 수 있는 변수목록을 불러온다.')
        self.ui.svjb_pushButon_04 = self.wc.setPushbutton('매수전략 시작', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_04, color=1, tip='작성한 전략을 저장 후 콤보박스에서 선택해야 적용된다.')
        self.ui.svjb_pushButon_05 = self.wc.setPushbutton('VI해제시간비교', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_05)
        self.ui.svjb_pushButon_06 = self.wc.setPushbutton('VI아래5호가비교', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_06)
        self.ui.svjb_pushButon_07 = self.wc.setPushbutton('등락율제한', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_07)
        self.ui.svjb_pushButon_08 = self.wc.setPushbutton('고저평균대비등락율', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_08)
        self.ui.svjb_pushButon_09 = self.wc.setPushbutton('체결강도하한', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_09)
        self.ui.svjb_pushButon_10 = self.wc.setPushbutton('체결강도차이', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_10)
        self.ui.svjb_pushButon_11 = self.wc.setPushbutton('매수시그널', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_11, color=3)
        self.ui.svjb_pushButon_12 = self.wc.setPushbutton('매수전략 중지', box=self.ui.ss_tab, click=self.ui.svjbButtonClicked_12, color=1, tip='실행중인 매수전략을 중지한다.')

        self.ui.svj_pushButton_01 = self.wc.setPushbutton('백테스트', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_11, color=2, tip='(Alt+Enter) 기본전략을 백테스팅한다.\nCtrl키와 함께 누르면 백테스트 엔진을 재시작할 수 있습니다.\nCtrl + Alt 키와 함계 누르면 백테 완료 후 변수목록이 포함된 그래프가 저장됩니다.')
        self.ui.svj_pushButton_02 = self.wc.setPushbutton('백파인더', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_12, color=2, tip='구간등락율을 기준으로 변수를 탐색한다.')
        self.ui.svj_pushButton_05 = self.wc.setPushbutton('백파인더 예제', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_13, color=3)

        self.ui.svjs_comboBoxx_01 = self.wc.setCombobox(self.ui.ss_tab, font=qfont14, activated=self.ui.sActivated_02)
        self.ui.svjs_lineEditt_01 = self.wc.setLineedit(self.ui.ss_tab, font=qfont14, aleft=True, ltext='F6, F7', style=style_bc_dk)
        self.ui.svjs_pushButon_01 = self.wc.setPushbutton('매도전략 로딩(F5)', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_01, color=1)
        self.ui.svjs_pushButon_02 = self.wc.setPushbutton('매도전략 저장(F8)', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_02, color=1, tip='작성된 매도전략을 저장한다.\nCtrl 키와 함께 누르면 코드 테스트 과정을 생략한다.')
        self.ui.svjs_pushButon_03 = self.wc.setPushbutton('매도변수 로딩', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_03, color=1, tip='매도전략에 사용할 수 있는 변수목록을 불러온다.')
        self.ui.svjs_pushButon_04 = self.wc.setPushbutton('매도전략 시작', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_04, color=1, tip='작성한 전략을 저장 후 콤보박스에서 선택해야 적용된다.')
        self.ui.svjs_pushButon_05 = self.wc.setPushbutton('손절라인청산', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_05)
        self.ui.svjs_pushButon_06 = self.wc.setPushbutton('익절라인청산', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_06)
        self.ui.svjs_pushButon_07 = self.wc.setPushbutton('수익율보존청산', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_07)
        self.ui.svjs_pushButon_08 = self.wc.setPushbutton('보유시간기준청산', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_08)
        self.ui.svjs_pushButon_09 = self.wc.setPushbutton('VI직전매도', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_09)
        self.ui.svjs_pushButon_10 = self.wc.setPushbutton('고저평균등락율', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_10)
        self.ui.svjs_pushButon_11 = self.wc.setPushbutton('최고체결강도비교', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_11)
        self.ui.svjs_pushButon_12 = self.wc.setPushbutton('호가총잔량비교', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_12)
        self.ui.svjs_pushButon_13 = self.wc.setPushbutton('매도시그널', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_13, color=3)
        self.ui.svjs_pushButon_14 = self.wc.setPushbutton('매도전략 중지', box=self.ui.ss_tab, click=self.ui.svjsButtonClicked_14, color=1, tip='실행중인 매도전략을 당장 중지한다.')

        self.ui.stock_backte_list = [
            self.ui.svjb_comboBoxx_01, self.ui.svjb_lineEditt_01, self.ui.svjb_pushButon_01, self.ui.svjb_pushButon_02,
            self.ui.svjb_pushButon_03, self.ui.svjb_pushButon_04, self.ui.svjb_pushButon_05, self.ui.svjb_pushButon_06,
            self.ui.svjb_pushButon_07, self.ui.svjb_pushButon_08, self.ui.svjb_pushButon_09, self.ui.svjb_pushButon_10,
            self.ui.svjb_pushButon_11, self.ui.svjb_pushButon_12, self.ui.svj_pushButton_01, self.ui.svj_pushButton_02,
            self.ui.svj_pushButton_05, self.ui.svjs_comboBoxx_01,
            self.ui.svjs_lineEditt_01, self.ui.svjs_pushButon_01, self.ui.svjs_pushButon_02, self.ui.svjs_pushButon_03,
            self.ui.svjs_pushButon_04, self.ui.svjs_pushButon_05, self.ui.svjs_pushButon_06, self.ui.svjs_pushButon_07,
            self.ui.svjs_pushButon_08, self.ui.svjs_pushButon_09, self.ui.svjs_pushButon_10, self.ui.svjs_pushButon_11,
            self.ui.svjs_pushButon_12, self.ui.svjs_pushButon_13, self.ui.svjs_pushButon_14
        ]

    # =================================================================================================================

        self.ui.svjb_labelllll_01 = QLabel('백테스트 기간설정                                         ~', self.ui.ss_tab)
        self.ui.svjb_labelllll_02 = QLabel('백테스트 시간설정     시작시간                         종료시간', self.ui.ss_tab)
        self.ui.svjb_labelllll_03 = QLabel('백테스트 기본설정   배팅(백만)                        평균틱수   self.vars[0]', self.ui.ss_tab)
        if self.ui.dict_set['백테날짜고정']:
            self.ui.svjb_dateEditt_01 = self.wc.setDateEdit(self.ui.ss_tab, qday=QDate.fromString(self.ui.dict_set['백테날짜'], 'yyyyMMdd'))
        else:
            self.ui.svjb_dateEditt_01 = self.wc.setDateEdit(self.ui.ss_tab, addday=-int(self.ui.dict_set['백테날짜']))
        self.ui.svjb_dateEditt_02 = self.wc.setDateEdit(self.ui.ss_tab)
        self.ui.svjb_lineEditt_02 = self.wc.setLineedit(self.ui.ss_tab, ltext='90000' if self.ui.dict_set['주식타임프레임'] else '900', style=style_bc_dk)
        self.ui.svjb_lineEditt_03 = self.wc.setLineedit(self.ui.ss_tab, ltext='93000' if self.ui.dict_set['주식타임프레임'] else '1519', style=style_bc_dk)
        self.ui.svjb_lineEditt_04 = self.wc.setLineedit(self.ui.ss_tab, ltext='20',    style=style_bc_dk)
        self.ui.svjb_lineEditt_05 = self.wc.setLineedit(self.ui.ss_tab, ltext='30',    style=style_bc_dk)

        self.ui.stock_datedt_list = [self.ui.svjb_labelllll_01, self.ui.svjb_dateEditt_01, self.ui.svjb_dateEditt_02, self.ui.svjb_lineEditt_05]

    # =================================================================================================================

        self.ui.svj_pushButton_15 = self.wc.setPushbutton('전략 편집기', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_09, color=5, tip='단축키(Alt+1)')
        self.ui.svj_pushButton_11 = self.wc.setPushbutton('최적화 편집기', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_05, color=4, tip='단축키(Alt+2)')
        self.ui.svj_pushButton_09 = self.wc.setPushbutton('테스트 편집기', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_01, color=4, tip='단축키(Alt+3)')
        self.ui.svj_pushButton_07 = self.wc.setPushbutton('전진분석', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_02, color=4, tip='단축키(Alt+4)')
        self.ui.svj_pushButton_08 = self.wc.setPushbutton('GA 편집기', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_03, color=4, tip='단축키(Alt+5)')
        self.ui.svj_pushButton_10 = self.wc.setPushbutton('조건 편집기', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_10, color=4, tip='단축키(Alt+6)')
        self.ui.svj_pushButton_12 = self.wc.setPushbutton('범위 편집기', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_04, color=4, tip='단축키(Alt+7)')
        self.ui.svj_pushButton_16 = self.wc.setPushbutton('변수 편집기', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_06, color=4, tip='단축키(Alt+8)')
        self.ui.svj_pushButton_13 = self.wc.setPushbutton('백테스트 로그', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_07, color=4, tip='단축키(Alt+9)')
        self.ui.svj_pushButton_14 = self.wc.setPushbutton('상세기록', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_08, color=4, tip='단축키(Alt+0)')

        self.ui.stock_editer_list = [
            self.ui.svj_pushButton_07, self.ui.svj_pushButton_08, self.ui.svj_pushButton_09, self.ui.svj_pushButton_10,
            self.ui.svj_pushButton_11, self.ui.svj_pushButton_12, self.ui.svj_pushButton_13, self.ui.svj_pushButton_14,
            self.ui.svj_pushButton_15, self.ui.svj_pushButton_16
        ]

    # =================================================================================================================

        self.ui.svc_comboBoxxx_01 = self.wc.setCombobox(self.ui.ss_tab, font=qfont14, activated=self.ui.sActivated_03)
        self.ui.svc_lineEdittt_01 = self.wc.setLineedit(self.ui.ss_tab, font=qfont14, aleft=True, ltext='F2, F3', style=style_bc_dk)
        self.ui.svc_pushButton_01 = self.wc.setPushbutton('최적화 매수전략 로딩(F1)', box=self.ui.ss_tab, click=self.ui.svcButtonClicked_01, color=1)
        self.ui.svc_pushButton_02 = self.wc.setPushbutton('최적화 매수전략 저장(F4)', box=self.ui.ss_tab, click=self.ui.svcButtonClicked_02, color=1, tip='작성된 최적화 매수전략을 저장한다.\nCtrl 키와 함께 누르면 코드 테스트 과정을 생략한다.')

        self.ui.svc_comboBoxxx_02 = self.wc.setCombobox(self.ui.ss_tab, font=qfont14, activated=self.ui.sActivated_04)
        self.ui.svc_lineEdittt_02 = self.wc.setLineedit(self.ui.ss_tab, font=qfont14, aleft=True, ltext='F10, F11', style=style_bc_dk)
        self.ui.svc_pushButton_03 = self.wc.setPushbutton('최적화 변수범위 로딩(F9)', box=self.ui.ss_tab, click=self.ui.svcButtonClicked_03, color=1)
        self.ui.svc_pushButton_04 = self.wc.setPushbutton('최적화 변수범위 저장(F12)', box=self.ui.ss_tab, click=self.ui.svcButtonClicked_04, color=1, tip='작성된 최적화 변수설정을 저장한다.\nCtrl 키와 함께 누르면 코드 테스트 과정을 생략한다.')

        self.ui.svc_labellllll_01 = QLabel('▣ 일반은 학습기간, 검증은 검증기간, 테스트는 확인기간까지 선택', self.ui.ss_tab)
        self.ui.svc_labellllll_02 = QLabel('최적화 학습기간                   검증기간                   확인기간', self.ui.ss_tab)
        self.ui.svc_comboBoxxx_03 = self.wc.setCombobox(self.ui.ss_tab, items=train_period, tip='최적화 학습기간(주단위)을 선택하십시오.')
        self.ui.svc_comboBoxxx_04 = self.wc.setCombobox(self.ui.ss_tab, items=valid_period, tip='최적화 검증기간(주단위)을 선택하십시오.')
        self.ui.svc_comboBoxxx_05 = self.wc.setCombobox(self.ui.ss_tab, items=test_period, tip='최적화 확인기간(주단위)을 선택하십시오.')
        self.ui.svc_labellllll_03 = QLabel('최적화 실행횟수                   기준값', self.ui.ss_tab)
        self.ui.svc_comboBoxxx_06 = self.wc.setCombobox(self.ui.ss_tab, items=optimized_count, tip='최적화 횟수를 선택하십시오. 0선택 시 최적값이 변하지 않을 때까지 반복됩니다.')
        self.ui.svc_comboBoxxx_07 = self.wc.setCombobox(self.ui.ss_tab, items=opti_standard, tip=optistandard)
        self.ui.svc_pushButton_05 = self.wc.setPushbutton('기준값', color=2, box=self.ui.ss_tab, click=self.ui.svcButtonClicked_10, tip='백테 결과값 중 특정 수치를 만족하지 못하면\n기준값을 0으로 도출하도록 설정한다.')
        self.ui.svc_pushButton_36 = self.wc.setPushbutton('optuna', color=3, box=self.ui.ss_tab, click=self.ui.svcButtonClicked_11, tip='옵튜나의 샘플러를 선택하거나 대시보드를 열람한다')

        self.ui.stock_period_list = [
            self.ui.svc_labellllll_01, self.ui.svc_labellllll_02, self.ui.svc_comboBoxxx_03, self.ui.svc_comboBoxxx_04,
            self.ui.svc_comboBoxxx_05, self.ui.svc_comboBoxxx_06, self.ui.svc_labellllll_03, self.ui.svc_comboBoxxx_07,
            self.ui.svc_pushButton_05, self.ui.svc_pushButton_36
        ]

        for widget in self.ui.stock_period_list:
            widget.setVisible(False)

    # =================================================================================================================

        self.ui.svc_pushButton_06 = self.wc.setPushbutton('교차검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화OVC', color=2, tip='학습기간과 검증기간을 선택하여 진행되며\n검증 최적화는 1회만 검증을 하지만, 교차검증은\n검증기간을 학습기간 / 검증기간 + 1만큼 교차분류하여 그리드 최적화한다.\nAlt키와 함께 누르면 모든 변수의 최적값을 랜덤 변경하여 시작한다.\nCtrl+Shift와 함께 누르면 매수변수만 최적화한다.\nCtrl+Alt와 함께 누르면 매도변수만 최적화한다.')
        self.ui.svc_pushButton_07 = self.wc.setPushbutton('검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화OV', color=2, tip='학습기간과 검증기간을 선택하여 진행되며\n데이터의 시계열 순서대로 학습, 검증기간을 분류하여 그리드 최적화한다.\nAlt키와 함께 누르면 모든 변수의 최적값을 랜덤 변경하여 시작힌다.\nCtrl+Shift와 함께 누르면 매수변수만 최적화한다.\nCtrl+Alt와 함께 누르면 매도변수만 최적화한다.')
        self.ui.svc_pushButton_08 = self.wc.setPushbutton('그리드', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화O', color=2, tip='학습기간만 선택하여 진행되며\n데이터 전체를 기반으로 그리드 최적화한다.\nAlt키와 함께 누르면 모든 변수의 최적값을 랜덤 변경하여 시작힌다.\nCtrl+Shift와 함께 누르면 매수변수만 최적화한다.\nCtrl+Alt와 함께 누르면 매도변수만 최적화한다.')
        self.ui.svc_pushButton_27 = self.wc.setPushbutton('교차검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화BVC', color=3, tip='학습기간과 검증기간을 선택하여 진행되며\n검증 최적화는 1회만 검증을 하지만, 교차검증은\n검증기간을 학습기간 / 검증기간 + 1만큼 교차분류하여 베이지안 최적화한다.\nCtrl+Shift와 함께 누르면 매수변수만 최적화한다.\nCtrl+Alt와 함께 누르면 매도변수만 최적화한다.')
        self.ui.svc_pushButton_28 = self.wc.setPushbutton('검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화BV', color=3, tip='학습기간과 검증기간을 선택하여 진행되며\n데이터의 시계열 순서대로 학습, 검증기간을 분류하여 베이지안 최적화한다.\nCtrl+Shift와 함께 누르면 매수변수만 최적화한다.\nCtrl+Alt와 함께 누르면 매도변수만 최적화한다.')
        self.ui.svc_pushButton_29 = self.wc.setPushbutton('베이지안', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화B', color=3, tip='학습기간만 선택하여 진행되며\n데이터 전체를 기반으로 베이지안 최적화한다.\nCtrl+Shift와 함께 누르면 매수변수만 최적화한다.\nCtrl+Alt와 함께 누르면 매도변수만 최적화한다.')

    # =================================================================================================================

        self.ui.svc_comboBoxxx_08 = self.wc.setCombobox(self.ui.ss_tab, font=qfont14, activated=self.ui.sActivated_05)
        self.ui.svc_lineEdittt_03 = self.wc.setLineedit(self.ui.ss_tab, font=qfont14, aleft=True, ltext='F6, F7', style=style_bc_dk)
        self.ui.svc_pushButton_09 = self.wc.setPushbutton('최적화 매도전략 로딩(F5)', box=self.ui.ss_tab, click=self.ui.svcButtonClicked_05, color=1)
        self.ui.svc_pushButton_10 = self.wc.setPushbutton('최적화 매도전략 저장(F8)', box=self.ui.ss_tab, click=self.ui.svcButtonClicked_06, color=1, tip='작성된 최적화 매도전략을 저장한다.\nCtrl 키와 함께 누르면 코드 테스트 과정을 생략한다.')
        self.ui.svc_labellllll_04 = QLabel(optitext, self.ui.ss_tab)
        self.ui.svc_labellllll_04.setFont(qfont13)
        self.ui.svc_pushButton_11 = self.wc.setPushbutton('예제', box=self.ui.ss_tab, click=self.ui.svcButtonClicked_07, color=3)

        self.ui.svc_lineEdittt_04 = self.wc.setLineedit(self.ui.ss_tab, font=qfont14, aleft=True, visible=False, style=style_bc_dk)
        self.ui.svc_pushButton_13 = self.wc.setPushbutton('매수전략으로 저장', box=self.ui.ss_tab, click=self.ui.svcButtonClicked_08, color=1, visible=False, tip='최적값으로 백테용 매수전략으로 저장한다.')
        self.ui.svc_lineEdittt_05 = self.wc.setLineedit(self.ui.ss_tab, font=qfont14, aleft=True, visible=False, style=style_bc_dk)
        self.ui.svc_pushButton_14 = self.wc.setPushbutton('매도전략으로 저장', box=self.ui.ss_tab, click=self.ui.svcButtonClicked_09, color=1, visible=False, tip='최적값으로 백테용 매도전략으로 저장한다.')

        self.ui.stock_optimz_list = [
            self.ui.svc_comboBoxxx_01, self.ui.svc_comboBoxxx_02, self.ui.svc_comboBoxxx_03, self.ui.svc_comboBoxxx_08,
            self.ui.svc_lineEdittt_01, self.ui.svc_lineEdittt_02, self.ui.svc_lineEdittt_03, self.ui.svc_labellllll_04,
            self.ui.svc_pushButton_01, self.ui.svc_pushButton_02, self.ui.svc_pushButton_03, self.ui.svc_pushButton_04,
            self.ui.svc_pushButton_06, self.ui.svc_pushButton_07, self.ui.svc_pushButton_08, self.ui.svc_pushButton_09,
            self.ui.svc_pushButton_10, self.ui.svc_pushButton_11, self.ui.svc_lineEdittt_04, self.ui.svc_lineEdittt_05,
            self.ui.svc_pushButton_13, self.ui.svc_pushButton_14, self.ui.svc_pushButton_27, self.ui.svc_pushButton_28,
            self.ui.svc_pushButton_29
        ]

        for widget in self.ui.stock_optimz_list:
            widget.setVisible(False)

    # =================================================================================================================

        self.ui.svc_pushButton_15 = self.wc.setPushbutton('교차검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화OVCT', color=2, tip='학습기간, 검증기간, 확인기간을 선택하여 진행되며\n그리드 교차검증 최적화로 구한 최적값을 확인기간에 대하여 테스트한다.\nAlt키와 함께 누르면 모든 변수의 최적값을 랜덤 변경하여 시작힌다.')
        self.ui.svc_pushButton_16 = self.wc.setPushbutton('검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화OVT', color=2, tip='학습기간, 검증기간, 확인기간을 선택하여 진행되며\n그리드 검증 최적화로 구한 최적값을 확인기간에 대하여 테스트한다.\nAlt키와 함께 누르면 모든 변수의 최적값을 랜덤 변경하여 시작힌다.')
        self.ui.svc_pushButton_17 = self.wc.setPushbutton('그리드', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화OT', color=2, tip='학습기간, 확인기간을 선택하여 진행되며\n그리드 최적화로 구한 최적값을 확인기간에 대하여 테스트한다.\nAlt키와 함께 누르면 모든 변수의 최적값을 랜덤 변경하여 시작힌다.')
        self.ui.svc_pushButton_30 = self.wc.setPushbutton('교차검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화BVCT', color=3, tip='학습기간, 검증기간, 확인기간을 선택하여 진행되며\n베이지안 교차검증 최적화로 구한 최적값을 확인기간에 대하여 테스트한다.')
        self.ui.svc_pushButton_31 = self.wc.setPushbutton('검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화BVT', color=3, tip='학습기간, 검증기간, 확인기간을 선택하여 진행되며\n베이지안 검증 최적화로 구한 최적값을 확인기간에 대하여 테스트한다.')
        self.ui.svc_pushButton_32 = self.wc.setPushbutton('베이지안', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화BT', color=3, tip='학습기간, 확인기간을 선택하여 진행되며\n베이지안 최적화로 구한 최적값을 확인기간에 대하여 테스트한다.')

        self.ui.stock_optest_list = [
            self.ui.svc_pushButton_15, self.ui.svc_pushButton_16, self.ui.svc_pushButton_17, self.ui.svc_comboBoxxx_02,
            self.ui.svc_lineEdittt_02, self.ui.svc_pushButton_03, self.ui.svc_pushButton_04, self.ui.svc_pushButton_30,
            self.ui.svc_pushButton_31, self.ui.svc_pushButton_32
        ]

        for widget in self.ui.stock_optest_list:
            widget.setVisible(False)

    # =================================================================================================================

        self.ui.svc_pushButton_18 = self.wc.setPushbutton('교차검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_15, cmd='전진분석ORVC', color=2, tip='학습기간, 확인기간, 전체기간을 선택하여 진행되며\n그리드 교차검증 최적화 테스트를 전진분석한다.\nAlt키와 함께 누르면 모든 변수의 최적값을 랜덤 변경하여 시작힌다.')
        self.ui.svc_pushButton_19 = self.wc.setPushbutton('검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_15, cmd='전진분석ORV', color=2, tip='학습기간, 검증기간, 확인기간, 전체기간을 선택하여 진행되며\n그리드 검증 최적화 테스트를 전진분석한다.\nAlt키와 함께 누르면 모든 변수의 최적값을 랜덤 변경하여 시작힌다.')
        self.ui.svc_pushButton_20 = self.wc.setPushbutton('그리드', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_15, cmd='전진분석OR', color=2, tip='학습기간, 검증기간, 확인기간, 전체기간을 선택하여 진행되며\n그리드 최적화 테스트를 전진분석한다.\nAlt키와 함께 누르면 모든 변수의 최적값을 랜덤 변경하여 시작힌다.')
        self.ui.svc_pushButton_33 = self.wc.setPushbutton('교차검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_15, cmd='전진분석BRVC', color=3, tip='학습기간, 확인기간, 전체기간을 선택하여 진행되며\n베이지안 교차검증 최적화 테스트를 전진분석한다.')
        self.ui.svc_pushButton_34 = self.wc.setPushbutton('검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_15, cmd='전진분석BRV', color=3, tip='학습기간, 검증기간, 확인기간, 전체기간을 선택하여 진행되며\n베이지안 검증 최적화 테스트를 전진분석한다.')
        self.ui.svc_pushButton_35 = self.wc.setPushbutton('베이지안', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_15, cmd='전진분석BR', color=3, tip='학습기간, 검증기간, 확인기간, 전체기간을 선택하여 진행되며\n베이지안 최적화 테스트를 전진분석한다.')

        self.ui.stock_rwftvd_list = [
            self.ui.svc_pushButton_18, self.ui.svc_pushButton_19, self.ui.svc_pushButton_20, self.ui.svc_comboBoxxx_02,
            self.ui.svc_lineEdittt_02, self.ui.svc_pushButton_03, self.ui.svc_pushButton_04, self.ui.svjb_labelllll_01,
            self.ui.svjb_dateEditt_01, self.ui.svjb_dateEditt_02, self.ui.svc_pushButton_33, self.ui.svc_pushButton_34,
            self.ui.svc_pushButton_35
        ]

        for widget in self.ui.stock_rwftvd_list:
            if widget not in (self.ui.svjb_labelllll_01, self.ui.svjb_dateEditt_01, self.ui.svjb_dateEditt_02):
                widget.setVisible(False)

    # =================================================================================================================

        self.ui.sva_pushButton_01 = self.wc.setPushbutton('교차검증 GA 최적화', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_16, cmd='최적화OGVC', color=2, tip='학습기간과 검증기간을 선택하여 진행되며\n교차 검증 GA최적화한다.')
        self.ui.sva_pushButton_02 = self.wc.setPushbutton('검증 GA 최적화', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_16, cmd='최적화OGV', color=2, tip='학습기간과 검증기간을 선택하여 진행되며\n검증 GA최적화한다.')
        self.ui.sva_pushButton_03 = self.wc.setPushbutton('GA 최적화', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_16, cmd='최적화OG', color=2, tip='학습기간을 선택하여 진행되며\n데이터 전체를 사용하여 GA최적화한다.')

        self.ui.sva_comboBoxxx_01 = self.wc.setCombobox(self.ui.ss_tab, font=qfont14, activated=self.ui.sActivated_06)
        self.ui.sva_lineEdittt_01 = self.wc.setLineedit(self.ui.ss_tab, font=qfont14, aleft=True, ltext='F10, F11', style=style_bc_dk)
        self.ui.sva_pushButton_04 = self.wc.setPushbutton('GA 변수범위 로딩(F9)', box=self.ui.ss_tab, click=self.ui.svaButtonClicked_01, color=1)
        self.ui.sva_pushButton_05 = self.wc.setPushbutton('GA 변수범위 저장(F12)', box=self.ui.ss_tab, click=self.ui.svaButtonClicked_02, color=1, tip='작성된 변수범위를 저장한다.\nCtrl 키와 함께 누르면 코드 테스트 과정을 생략한다.')

        self.ui.stock_gaopti_list = [
            self.ui.sva_pushButton_01, self.ui.sva_pushButton_02, self.ui.sva_pushButton_03, self.ui.sva_comboBoxxx_01,
            self.ui.sva_lineEdittt_01, self.ui.sva_pushButton_04, self.ui.sva_pushButton_05, self.ui.svc_labellllll_04
        ]

        for widget in self.ui.stock_gaopti_list:
            widget.setVisible(False)

    # =================================================================================================================

        self.ui.svc_pushButton_21 = self.wc.setPushbutton('최적화 > GA 범위 변환', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_18, color=2, visible=False, tip='최적화용 범위코드를 GA용으로 변환한다.')
        self.ui.svc_pushButton_22 = self.wc.setPushbutton('GA > 최적화 범위 변환', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_19, color=2, visible=False, tip='GA용 범위코드를 최적화용으로 변환한다.')
        self.ui.svc_pushButton_23 = self.wc.setPushbutton('변수 키값 재정렬', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_21, color=2, visible=False, tip='범위 변수 self.vars의 키값을 재정렬한다.')

    # =================================================================================================================

        self.ui.svc_pushButton_24 = self.wc.setPushbutton('최적화 변수 변환(매수우선)', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_20, color=2, visible=False, tip='일반 전략의 각종 변수를 매수우선 최적화용 변수로 변환한다.')
        self.ui.svc_pushButton_25 = self.wc.setPushbutton('최적화 변수 변환(매도우선)', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_20, color=2, visible=False, tip='일반 전략의 각종 변수를 매도우선 최적화용 변수로 변환한다.')
        self.ui.svc_pushButton_26 = self.wc.setPushbutton('변수 키값 재정렬', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_22, color=2, visible=False, tip='변수 self.vars의 키값을 재정렬한다.\n매수, 매도 self.vars의 첫번째 키값을 비교해서\n매수가 빠르면 매수우선, 매도가 빠르면 매도우선으로 재정렬된다.')
        self.ui.svc_labellllll_05 = QLabel('', self.ui.ss_tab)
        self.ui.svc_labellllll_05.setVisible(False)

    # =================================================================================================================

        self.ui.svo_comboBoxxx_01 = self.wc.setCombobox(self.ui.ss_tab, font=qfont14, activated=self.ui.sActivated_07)
        self.ui.svo_lineEdittt_01 = self.wc.setLineedit(self.ui.ss_tab, font=qfont14, aleft=True, ltext='F2, F3', style=style_bc_dk)
        self.ui.svo_pushButton_01 = self.wc.setPushbutton('매수조건 로딩(F1)', box=self.ui.ss_tab, click=self.ui.svoButtonClicked_01, color=1)
        self.ui.svo_pushButton_02 = self.wc.setPushbutton('매수조건 저장(F4)', box=self.ui.ss_tab, click=self.ui.svoButtonClicked_02, color=1, tip='작성된 매수조건을 저장한다.\nCtrl 키와 함께 누르면 코드 테스트 과정을 생략한다.')
        self.ui.svo_comboBoxxx_02 = self.wc.setCombobox(self.ui.ss_tab, font=qfont14, activated=self.ui.sActivated_08)
        self.ui.svo_lineEdittt_02 = self.wc.setLineedit(self.ui.ss_tab, font=qfont14, aleft=True, ltext='F6, F7', style=style_bc_dk)
        self.ui.svo_pushButton_03 = self.wc.setPushbutton('매도조건 로딩(F5)', box=self.ui.ss_tab, click=self.ui.svoButtonClicked_03, color=1)
        self.ui.svo_pushButton_04 = self.wc.setPushbutton('매도조건 저장(F8)', box=self.ui.ss_tab, click=self.ui.svoButtonClicked_04, color=1, tip='작성된 매도조건을 저장한다.\nCtrl 키와 함께 누르면 코드 테스트 과정을 생략한다.')

        self.ui.svo_labellllll_04 = QLabel('매수조건수                     매도조건수                    최적화횟수', self.ui.ss_tab)
        self.ui.svo_lineEdittt_03 = self.wc.setLineedit(self.ui.ss_tab, ltext='10', style=style_bc_dk)
        self.ui.svo_lineEdittt_04 = self.wc.setLineedit(self.ui.ss_tab, ltext='5', style=style_bc_dk)
        self.ui.svo_lineEdittt_05 = self.wc.setLineedit(self.ui.ss_tab, ltext='1000', style=style_bc_dk)

        self.ui.svo_pushButton_05 = self.wc.setPushbutton('교차검증 조건 최적화', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_17, cmd='최적화OCVC', color=2, tip='학습기간과 검증기간을 선택하여 진행되며\n교차 검증 조건최적화한다.')
        self.ui.svo_pushButton_06 = self.wc.setPushbutton('검증 조건 최적화', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_17, cmd='최적화OCV', color=2, tip='학습기간과 검증기간을 선택하여 진행되며\n검증 조건최적화한다.')
        self.ui.svo_pushButton_07 = self.wc.setPushbutton('조건 최적화', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_17, cmd='최적화OC', color=2, tip='학습기간을 선택하여 진행되며\n데이터 전체를 사용하여 조건최적화한다.')

        self.ui.svo_pushButton_08 = self.wc.setPushbutton('예제', box=self.ui.ss_tab, click=self.ui.svcButtonClicked_07, color=3)

        self.ui.stock_opcond_list = [
            self.ui.ss_textEditttt_07, self.ui.ss_textEditttt_08, self.ui.svo_comboBoxxx_01, self.ui.svo_lineEdittt_01,
            self.ui.svo_pushButton_01, self.ui.svo_pushButton_02, self.ui.svo_comboBoxxx_02, self.ui.svo_lineEdittt_02,
            self.ui.svo_pushButton_03, self.ui.svo_pushButton_04, self.ui.svo_pushButton_05, self.ui.svo_pushButton_06,
            self.ui.svo_pushButton_07, self.ui.svo_labellllll_04, self.ui.svo_lineEdittt_03, self.ui.svo_lineEdittt_04,
            self.ui.svo_lineEdittt_05, self.ui.svo_pushButton_08, self.ui.svc_labellllll_04
        ]

        for widget in self.ui.stock_opcond_list:
            widget.setVisible(False)

    # =================================================================================================================

        self.ui.ss_textEditttt_01.setGeometry(7, 10, 1000, 463)
        self.ui.ss_textEditttt_02.setGeometry(7, 480, 1000, 272)
        self.ui.ss_textEditttt_03.setGeometry(509, 10, 497, 463)
        self.ui.ss_textEditttt_04.setGeometry(509, 480, 497, 272)
        self.ui.ss_textEditttt_05.setGeometry(659, 10, 347, 740)
        self.ui.ss_textEditttt_06.setGeometry(659, 10, 347, 740)
        self.ui.ss_textEditttt_07.setGeometry(7, 10, 497, 740)
        self.ui.ss_textEditttt_08.setGeometry(509, 10, 497, 740)

        self.ui.szoo_pushButon_01.setGeometry(952, 15, 50, 20)
        self.ui.szoo_pushButon_02.setGeometry(952, 483, 50, 20)

        self.ui.ss_tableWidget_01.setGeometry(7, 40, 1000, 713)
        self.ui.ss_comboBoxxxx_01.setGeometry(7, 10, 150, 25)
        self.ui.ss_pushButtonn_01.setGeometry(162, 10, 100, 25)
        self.ui.ss_pushButtonn_02.setGeometry(267, 10, 55, 25)
        self.ui.ss_comboBoxxxx_02.setGeometry(327, 10, 150, 25)
        self.ui.ss_pushButtonn_03.setGeometry(482, 10, 100, 25)
        self.ui.ss_pushButtonn_04.setGeometry(587, 10, 55, 25)
        self.ui.ss_comboBoxxxx_03.setGeometry(647, 10, 150, 25)
        self.ui.ss_pushButtonn_05.setGeometry(802, 10, 100, 25)
        self.ui.ss_pushButtonn_06.setGeometry(907, 10, 55, 25)
        self.ui.ss_pushButtonn_07.setGeometry(967, 10, 40, 25)

        self.ui.ss_textEditttt_09.setGeometry(7, 10, 1000, 703)
        self.ui.ss_progressBar_01.setGeometry(7, 718, 830, 30)
        self.ui.ss_pushButtonn_08.setGeometry(842, 718, 165, 30)

        self.ui.svjb_comboBoxx_01.setGeometry(1012, 10, 165, 25)
        self.ui.svjb_lineEditt_01.setGeometry(1182, 10, 165, 25)
        self.ui.svjb_pushButon_01.setGeometry(1012, 40, 165, 30)
        self.ui.svjb_pushButon_02.setGeometry(1182, 40, 165, 30)
        self.ui.svjb_pushButon_03.setGeometry(1012, 75, 165, 30)
        self.ui.svjb_pushButon_04.setGeometry(1182, 75, 165, 30)
        self.ui.svjb_pushButon_05.setGeometry(1012, 110, 165, 30)
        self.ui.svjb_pushButon_06.setGeometry(1182, 110, 165, 30)
        self.ui.svjb_pushButon_07.setGeometry(1012, 145, 165, 30)
        self.ui.svjb_pushButon_08.setGeometry(1182, 145, 165, 30)
        self.ui.svjb_pushButon_09.setGeometry(1012, 180, 165, 30)
        self.ui.svjb_pushButon_10.setGeometry(1182, 180, 165, 30)
        self.ui.svjb_pushButon_11.setGeometry(1012, 215, 165, 30)
        self.ui.svjb_pushButon_12.setGeometry(1182, 215, 165, 30)

        self.ui.svj_pushButton_01.setGeometry(1012, 335, 165, 30)
        self.ui.svj_pushButton_02.setGeometry(1012, 370, 165, 30)
        self.ui.svj_pushButton_05.setGeometry(1012, 405, 165, 30)

        self.ui.svjs_comboBoxx_01.setGeometry(1012, 478, 165, 25)
        self.ui.svjs_lineEditt_01.setGeometry(1182, 478, 165, 25)
        self.ui.svjs_pushButon_01.setGeometry(1012, 508, 165, 30)
        self.ui.svjs_pushButon_02.setGeometry(1182, 508, 165, 30)
        self.ui.svjs_pushButon_03.setGeometry(1012, 543, 165, 30)
        self.ui.svjs_pushButon_04.setGeometry(1182, 543, 165, 30)
        self.ui.svjs_pushButon_05.setGeometry(1012, 578, 165, 30)
        self.ui.svjs_pushButon_06.setGeometry(1182, 578, 165, 30)
        self.ui.svjs_pushButon_07.setGeometry(1012, 613, 165, 30)
        self.ui.svjs_pushButon_08.setGeometry(1182, 613, 165, 30)
        self.ui.svjs_pushButon_09.setGeometry(1012, 648, 165, 30)
        self.ui.svjs_pushButon_10.setGeometry(1182, 648, 165, 30)
        self.ui.svjs_pushButon_11.setGeometry(1012, 683, 165, 30)
        self.ui.svjs_pushButon_12.setGeometry(1182, 683, 165, 30)
        self.ui.svjs_pushButon_13.setGeometry(1012, 718, 165, 30)
        self.ui.svjs_pushButon_14.setGeometry(1182, 718, 165, 30)

        self.ui.svjb_labelllll_01.setGeometry(1012, 255, 340, 20)
        self.ui.svjb_labelllll_02.setGeometry(1012, 280, 340, 20)
        self.ui.svjb_labelllll_03.setGeometry(1012, 305, 335, 20)

        self.ui.svjb_dateEditt_01.setGeometry(1112, 255, 110, 20)
        self.ui.svjb_dateEditt_02.setGeometry(1237, 255, 110, 20)
        self.ui.svjb_lineEditt_02.setGeometry(1167, 280, 60, 20)
        self.ui.svjb_lineEditt_03.setGeometry(1287, 280, 60, 20)
        self.ui.svjb_lineEditt_04.setGeometry(1167, 305, 60, 20)
        self.ui.svjb_lineEditt_05.setGeometry(1287, 305, 60, 20)

        self.ui.svj_pushButton_07.setGeometry(1182, 335, 80, 30)
        self.ui.svj_pushButton_08.setGeometry(1267, 335, 80, 30)
        self.ui.svj_pushButton_09.setGeometry(1182, 370, 80, 30)
        self.ui.svj_pushButton_10.setGeometry(1267, 370, 80, 30)
        self.ui.svj_pushButton_11.setGeometry(1182, 405, 80, 30)
        self.ui.svj_pushButton_12.setGeometry(1267, 405, 80, 30)
        self.ui.svj_pushButton_13.setGeometry(1012, 440, 80, 30)
        self.ui.svj_pushButton_14.setGeometry(1097, 440, 80, 30)
        self.ui.svj_pushButton_15.setGeometry(1182, 440, 80, 30)
        self.ui.svj_pushButton_16.setGeometry(1267, 440, 80, 30)

        self.ui.svc_comboBoxxx_01.setGeometry(1012, 45, 165, 30)
        self.ui.svc_lineEdittt_01.setGeometry(1182, 45, 165, 30)
        self.ui.svc_pushButton_01.setGeometry(1012, 80, 165, 30)
        self.ui.svc_pushButton_02.setGeometry(1182, 80, 165, 30)

        self.ui.svc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.ui.svc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.ui.svc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.ui.svc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.ui.svc_labellllll_01.setGeometry(1012, 250, 335, 25)
        self.ui.svc_labellllll_02.setGeometry(1012, 190, 335, 25)
        self.ui.svc_comboBoxxx_03.setGeometry(1097, 190, 45, 25)
        self.ui.svc_comboBoxxx_04.setGeometry(1197, 190, 45, 25)
        self.ui.svc_comboBoxxx_05.setGeometry(1302, 190, 45, 25)

        self.ui.svc_labellllll_03.setGeometry(1012, 220, 335, 25)
        self.ui.svc_comboBoxxx_06.setGeometry(1097, 220, 45, 25)
        self.ui.svc_comboBoxxx_07.setGeometry(1187, 220, 55, 25)
        self.ui.svc_pushButton_05.setGeometry(1247, 220, 47, 25)
        self.ui.svc_pushButton_36.setGeometry(1299, 220, 48, 25)

        self.ui.svc_pushButton_06.setGeometry(1012, 335, 80, 30)
        self.ui.svc_pushButton_07.setGeometry(1012, 370, 80, 30)
        self.ui.svc_pushButton_08.setGeometry(1012, 405, 80, 30)
        self.ui.svc_pushButton_27.setGeometry(1097, 335, 80, 30)
        self.ui.svc_pushButton_28.setGeometry(1097, 370, 80, 30)
        self.ui.svc_pushButton_29.setGeometry(1097, 405, 80, 30)

        self.ui.svc_comboBoxxx_08.setGeometry(1012, 513, 165, 30)
        self.ui.svc_lineEdittt_03.setGeometry(1182, 513, 165, 30)
        self.ui.svc_pushButton_09.setGeometry(1012, 548, 165, 30)
        self.ui.svc_pushButton_10.setGeometry(1182, 548, 165, 30)
        self.ui.svc_labellllll_04.setGeometry(1012, 583, 335, 130)
        self.ui.svc_pushButton_11.setGeometry(1012, 718, 335, 30)

        self.ui.svc_lineEdittt_04.setGeometry(1012, 10, 165, 30)
        self.ui.svc_pushButton_13.setGeometry(1182, 10, 165, 30)
        self.ui.svc_lineEdittt_05.setGeometry(1012, 478, 165, 30)
        self.ui.svc_pushButton_14.setGeometry(1182, 478, 165, 30)

        self.ui.svc_pushButton_15.setGeometry(1012, 335, 80, 30)
        self.ui.svc_pushButton_16.setGeometry(1012, 370, 80, 30)
        self.ui.svc_pushButton_17.setGeometry(1012, 405, 80, 30)
        self.ui.svc_pushButton_30.setGeometry(1097, 335, 80, 30)
        self.ui.svc_pushButton_31.setGeometry(1097, 370, 80, 30)
        self.ui.svc_pushButton_32.setGeometry(1097, 405, 80, 30)

        self.ui.svc_pushButton_18.setGeometry(1012, 335, 80, 30)
        self.ui.svc_pushButton_19.setGeometry(1012, 370, 80, 30)
        self.ui.svc_pushButton_20.setGeometry(1012, 405, 80, 30)
        self.ui.svc_pushButton_33.setGeometry(1097, 335, 80, 30)
        self.ui.svc_pushButton_34.setGeometry(1097, 370, 80, 30)
        self.ui.svc_pushButton_35.setGeometry(1097, 405, 80, 30)

        self.ui.sva_pushButton_01.setGeometry(1012, 335, 165, 30)
        self.ui.sva_pushButton_02.setGeometry(1012, 370, 165, 30)
        self.ui.sva_pushButton_03.setGeometry(1012, 405, 165, 30)

        self.ui.sva_comboBoxxx_01.setGeometry(1012, 115, 165, 30)
        self.ui.sva_lineEdittt_01.setGeometry(1182, 115, 165, 30)
        self.ui.sva_pushButton_04.setGeometry(1012, 150, 165, 30)
        self.ui.sva_pushButton_05.setGeometry(1182, 150, 165, 30)

        self.ui.svc_pushButton_21.setGeometry(1012, 335, 165, 30)
        self.ui.svc_pushButton_22.setGeometry(1012, 370, 165, 30)
        self.ui.svc_pushButton_23.setGeometry(1012, 405, 165, 30)
        self.ui.svc_pushButton_24.setGeometry(1012, 335, 165, 30)
        self.ui.svc_pushButton_25.setGeometry(1012, 370, 165, 30)
        self.ui.svc_pushButton_26.setGeometry(1012, 405, 165, 30)
        self.ui.svc_labellllll_05.setGeometry(1012, 150, 335, 40)

        self.ui.svo_comboBoxxx_01.setGeometry(1012, 10, 165, 30)
        self.ui.svo_lineEdittt_01.setGeometry(1182, 10, 165, 30)
        self.ui.svo_pushButton_01.setGeometry(1012, 45, 165, 30)
        self.ui.svo_pushButton_02.setGeometry(1182, 45, 165, 30)
        self.ui.svo_comboBoxxx_02.setGeometry(1012, 80, 165, 30)
        self.ui.svo_lineEdittt_02.setGeometry(1182, 80, 165, 30)
        self.ui.svo_pushButton_03.setGeometry(1012, 115, 165, 30)
        self.ui.svo_pushButton_04.setGeometry(1182, 115, 165, 30)

        self.ui.svo_labellllll_04.setGeometry(1012, 255, 335, 20)
        self.ui.svo_lineEdittt_03.setGeometry(1072, 255, 45, 20)
        self.ui.svo_lineEdittt_04.setGeometry(1197, 255, 45, 20)
        self.ui.svo_lineEdittt_05.setGeometry(1302, 255, 45, 20)

        self.ui.svo_pushButton_05.setGeometry(1012, 335, 165, 30)
        self.ui.svo_pushButton_06.setGeometry(1012, 370, 165, 30)
        self.ui.svo_pushButton_07.setGeometry(1012, 405, 165, 30)

        self.ui.svo_pushButton_08.setGeometry(1012, 718, 335, 30)
