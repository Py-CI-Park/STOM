import os
import random
import sqlite3
import pandas as pd
from PyQt5.QtWidgets import QMessageBox
from ui.set_text import famous_saying
from utility.setting import DB_STRATEGY, PATTERN_PATH
from utility.static import pickle_read


def pactivated_01(ui):
    name = ui.pt_comboBoxxxxx_00.currentText()
    con = sqlite3.connect(DB_STRATEGY)
    if ui.main_btn == 2:
        df = pd.read_sql(f'SELECT * FROM stockpattern WHERE `index`= "{name}"', con)
    else:
        df = pd.read_sql(f'SELECT * FROM coinpattern WHERE `index`= "{name}"', con)
    con.close()
    if len(df) > 0:
        pattern = df['패턴설정'][0]
        pattern = pattern.split('^')
        ui.pt_comboBoxxxxx_14.setCurrentText(pattern[0])
        ui.pt_comboBoxxxxx_15.setCurrentText(pattern[1])
        ui.pt_checkBoxxxxx_14.setChecked(True if pattern[2] == '1' else False)
        ui.pt_lineEdittttt_01.setText(pattern[3])
        ui.pt_checkBoxxxxx_15.setChecked(True if pattern[4] == '1' else False)
        ui.pt_checkBoxxxxx_34.setChecked(True if pattern[5] == '1' else False)
        ui.pt_lineEdittttt_02.setText(pattern[6])
        ui.pt_checkBoxxxxx_35.setChecked(True if pattern[7] == '1' else False)
        ui.pt_checkBoxxxxx_01.setChecked(True if pattern[8] == '1' else False)
        ui.pt_checkBoxxxxx_02.setChecked(True if pattern[9] == '1' else False)
        ui.pt_checkBoxxxxx_03.setChecked(True if pattern[10] == '1' else False)
        ui.pt_checkBoxxxxx_04.setChecked(True if pattern[11] == '1' else False)
        ui.pt_checkBoxxxxx_05.setChecked(True if pattern[12] == '1' else False)
        ui.pt_checkBoxxxxx_06.setChecked(True if pattern[13] == '1' else False)
        ui.pt_checkBoxxxxx_07.setChecked(True if pattern[14] == '1' else False)
        ui.pt_checkBoxxxxx_08.setChecked(True if pattern[15] == '1' else False)
        ui.pt_checkBoxxxxx_09.setChecked(True if pattern[16] == '1' else False)
        ui.pt_checkBoxxxxx_10.setChecked(True if pattern[17] == '1' else False)
        ui.pt_checkBoxxxxx_11.setChecked(True if pattern[18] == '1' else False)
        ui.pt_checkBoxxxxx_12.setChecked(True if pattern[19] == '1' else False)
        ui.pt_checkBoxxxxx_13.setChecked(True if pattern[20] == '1' else False)
        ui.pt_comboBoxxxxx_01.setCurrentText(pattern[21])
        ui.pt_comboBoxxxxx_02.setCurrentText(pattern[22])
        ui.pt_comboBoxxxxx_03.setCurrentText(pattern[23])
        ui.pt_comboBoxxxxx_04.setCurrentText(pattern[24])
        ui.pt_comboBoxxxxx_05.setCurrentText(pattern[25])
        ui.pt_comboBoxxxxx_06.setCurrentText(pattern[26])
        ui.pt_comboBoxxxxx_07.setCurrentText(pattern[27])
        ui.pt_comboBoxxxxx_08.setCurrentText(pattern[28])
        ui.pt_comboBoxxxxx_09.setCurrentText(pattern[29])
        ui.pt_comboBoxxxxx_10.setCurrentText(pattern[30])
        ui.pt_comboBoxxxxx_11.setCurrentText(pattern[31])
        ui.pt_comboBoxxxxx_12.setCurrentText(pattern[32])
        ui.pt_comboBoxxxxx_13.setCurrentText(pattern[33])
        ui.pt_checkBoxxxxx_21.setChecked(True if pattern[34] == '1' else False)
        ui.pt_checkBoxxxxx_22.setChecked(True if pattern[35] == '1' else False)
        ui.pt_checkBoxxxxx_23.setChecked(True if pattern[36] == '1' else False)
        ui.pt_checkBoxxxxx_24.setChecked(True if pattern[37] == '1' else False)
        ui.pt_checkBoxxxxx_25.setChecked(True if pattern[38] == '1' else False)
        ui.pt_checkBoxxxxx_26.setChecked(True if pattern[39] == '1' else False)
        ui.pt_checkBoxxxxx_27.setChecked(True if pattern[40] == '1' else False)
        ui.pt_checkBoxxxxx_28.setChecked(True if pattern[41] == '1' else False)
        ui.pt_checkBoxxxxx_29.setChecked(True if pattern[42] == '1' else False)
        ui.pt_checkBoxxxxx_30.setChecked(True if pattern[43] == '1' else False)
        ui.pt_checkBoxxxxx_31.setChecked(True if pattern[44] == '1' else False)
        ui.pt_checkBoxxxxx_32.setChecked(True if pattern[45] == '1' else False)
        ui.pt_checkBoxxxxx_33.setChecked(True if pattern[46] == '1' else False)
        ui.pt_comboBoxxxxx_21.setCurrentText(pattern[47])
        ui.pt_comboBoxxxxx_22.setCurrentText(pattern[48])
        ui.pt_comboBoxxxxx_23.setCurrentText(pattern[49])
        ui.pt_comboBoxxxxx_24.setCurrentText(pattern[50])
        ui.pt_comboBoxxxxx_25.setCurrentText(pattern[51])
        ui.pt_comboBoxxxxx_26.setCurrentText(pattern[52])
        ui.pt_comboBoxxxxx_27.setCurrentText(pattern[53])
        ui.pt_comboBoxxxxx_28.setCurrentText(pattern[54])
        ui.pt_comboBoxxxxx_29.setCurrentText(pattern[55])
        ui.pt_comboBoxxxxx_30.setCurrentText(pattern[56])
        ui.pt_comboBoxxxxx_31.setCurrentText(pattern[57])
        ui.pt_comboBoxxxxx_32.setCurrentText(pattern[58])
        ui.pt_comboBoxxxxx_33.setCurrentText(pattern[59])

def ptbutton_clicked_01(ui):
    con = sqlite3.connect(DB_STRATEGY)
    if ui.main_btn == 2:
        df = pd.read_sql('SELECT * FROM stockpattern', con).set_index('index')
    else:
        df = pd.read_sql('SELECT * FROM coinpattern', con).set_index('index')
    con.close()
    if len(df) > 0:
        ui.pt_comboBoxxxxx_00.clear()
        for pattern_name in df.index:
            ui.pt_comboBoxxxxx_00.addItem(pattern_name)

def ptbutton_clicked_02(ui, proc_query, queryQ):
    if ui.main_btn == 2:
        name = ui.svjb_comboBoxx_01.currentText()
    else:
        name = ui.cvjb_comboBoxx_01.currentText()

    if name == '':
        QMessageBox.critical(ui.dialog_pattern, '오류 알림', '패턴의 이름은 전략의 이름이 포함되어 저장됩니다.\n전략을 로딩하고 선택하십시오.')
        return
    if not ui.pt_checkBoxxxxx_14.isChecked() and not ui.pt_checkBoxxxxx_15.isChecked():
        QMessageBox.critical(ui.dialog_pattern, '오류 알림', '매수 패턴 인식 조건을 선택하십시오.\n')
        return
    if ui.pt_checkBoxxxxx_14.isChecked() and ui.pt_checkBoxxxxx_15.isChecked():
        QMessageBox.critical(ui.dialog_pattern, '오류 알림', '매수 패턴 인식 조건은 하나만 선택할 수 있습니다.\n')
        return
    if not ui.pt_checkBoxxxxx_34.isChecked() and not ui.pt_checkBoxxxxx_35.isChecked():
        QMessageBox.critical(ui.dialog_pattern, '오류 알림', '매도 패턴 인식 조건을 선택하십시오.\n')
        return
    if ui.pt_checkBoxxxxx_34.isChecked() and ui.pt_checkBoxxxxx_35.isChecked():
        QMessageBox.critical(ui.dialog_pattern, '오류 알림', '매도 패턴 인식 조건은 하나만 선택할 수 있습니다.\n')
        return
    if ui.pt_checkBoxxxxx_14.isChecked() and ui.pt_lineEdittttt_01.text() == '':
        QMessageBox.critical(ui.dialog_pattern, '오류 알림', '매수 패턴 인식 조건 등락율 수치를 입력하십시오.\n')
        return
    if ui.pt_checkBoxxxxx_34.isChecked() and ui.pt_lineEdittttt_02.text() == '':
        QMessageBox.critical(ui.dialog_pattern, '오류 알림', '매도 패턴 인식 조건 등락율 수치를 입력하십시오.\n')
        return
    if ui.pt_lineEdittttt_01.text() == '' or ui.pt_lineEdittttt_02.text() == '':
        QMessageBox.critical(ui.dialog_pattern, '오류 알림', '등락율 수치가 입력되지 않았습니다.\n사용하지 않더라도 입력되어야 합니다.')
        return

    pattern = [
        ui.pt_comboBoxxxxx_14.currentText(),
        ui.pt_comboBoxxxxx_15.currentText(),
        '1' if ui.pt_checkBoxxxxx_14.isChecked() else '0',
        ui.pt_lineEdittttt_01.text(),
        '1' if ui.pt_checkBoxxxxx_15.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_34.isChecked() else '0',
        ui.pt_lineEdittttt_02.text(),
        '1' if ui.pt_checkBoxxxxx_35.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_01.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_02.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_03.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_04.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_05.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_06.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_07.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_08.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_09.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_10.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_11.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_12.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_13.isChecked() else '0',
        ui.pt_comboBoxxxxx_01.currentText(),
        ui.pt_comboBoxxxxx_02.currentText(),
        ui.pt_comboBoxxxxx_03.currentText(),
        ui.pt_comboBoxxxxx_04.currentText(),
        ui.pt_comboBoxxxxx_05.currentText(),
        ui.pt_comboBoxxxxx_06.currentText(),
        ui.pt_comboBoxxxxx_07.currentText(),
        ui.pt_comboBoxxxxx_08.currentText(),
        ui.pt_comboBoxxxxx_09.currentText(),
        ui.pt_comboBoxxxxx_10.currentText(),
        ui.pt_comboBoxxxxx_11.currentText(),
        ui.pt_comboBoxxxxx_12.currentText(),
        ui.pt_comboBoxxxxx_13.currentText(),
        '1' if ui.pt_checkBoxxxxx_21.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_22.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_23.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_24.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_25.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_26.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_27.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_28.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_29.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_30.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_31.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_32.isChecked() else '0',
        '1' if ui.pt_checkBoxxxxx_33.isChecked() else '0',
        ui.pt_comboBoxxxxx_21.currentText(),
        ui.pt_comboBoxxxxx_22.currentText(),
        ui.pt_comboBoxxxxx_23.currentText(),
        ui.pt_comboBoxxxxx_24.currentText(),
        ui.pt_comboBoxxxxx_25.currentText(),
        ui.pt_comboBoxxxxx_26.currentText(),
        ui.pt_comboBoxxxxx_27.currentText(),
        ui.pt_comboBoxxxxx_28.currentText(),
        ui.pt_comboBoxxxxx_29.currentText(),
        ui.pt_comboBoxxxxx_30.currentText(),
        ui.pt_comboBoxxxxx_31.currentText(),
        ui.pt_comboBoxxxxx_32.currentText(),
        ui.pt_comboBoxxxxx_33.currentText()
    ]
    pattern = '^'.join(pattern)
    df = pd.DataFrame({'패턴설정': [pattern]}, index=[name])
    if proc_query.is_alive():
        if ui.main_btn == 2:
            queryQ.put(('전략디비', f"DELETE FROM stockpattern WHERE `index` = '{name}'"))
            queryQ.put(('전략디비', df, 'stockpattern', 'append'))
        else:
            queryQ.put(('전략디비', f"DELETE FROM coinpattern WHERE `index` = '{name}'"))
            queryQ.put(('전략디비', df, 'coinpattern', 'append'))
        QMessageBox.information(ui.dialog_pattern, '저장 완료', random.choice(famous_saying))

def ptbutton_clicked_03(ui):
    if ui.main_btn == 2:
        middle_name = 'stock'
    else:
        middle_name = 'coin'
    last_name = ui.pt_comboBoxxxxx_00.currentText()
    if last_name != '':
        pattern_buy_name  = f'{PATTERN_PATH}/pattern_{middle_name}_{last_name}_buy'
        pattern_sell_name = f'{PATTERN_PATH}/pattern_{middle_name}_{last_name}_sell'
        if os.path.isfile(f'{pattern_buy_name}.pkl') and os.path.isfile(f'{pattern_sell_name}.pkl'):
            if ui.backtest_engine:
                for q in ui.back_pques:
                    q.put(('백테유형', '백테스트'))
                dict_pattern, dict_pattern_buy, dict_pattern_sell = GetPatternSetup(ui)
                for q in ui.back_pques:
                    q.put(('패턴정보', dict_pattern, dict_pattern_buy, dict_pattern_sell))
                pattern_buy  = pickle_read(pattern_buy_name)
                pattern_sell = pickle_read(pattern_sell_name)
                for q in ui.back_pques:
                    q.put(('모델정보', pattern_buy, pattern_sell))
                QMessageBox.information(ui.dialog_pattern, '전송 완료', random.choice(famous_saying))
            else:
                QMessageBox.critical(ui.dialog_pattern, '오류 알림', '백테엔진이 미실행중입니다.\n먼저 백테엔진을 구동하십시오.\n')
        else:
            QMessageBox.critical(ui.dialog_pattern, '오류 알림', '학습 데이터 파일이 존재하지 않습니다.\n')
    else:
        QMessageBox.critical(ui.dialog_pattern, '오류 알림', '전송할 패턴 데이터의 이름을 콤보박스에서 선택하십시오.\n')

def GetPatternSetup(ui):
    dict_pattern = {
        '패턴이름': ui.pt_comboBoxxxxx_00.currentText(),
        '인식구간': int(ui.pt_comboBoxxxxx_14.currentText()),
        '조건구간': int(ui.pt_comboBoxxxxx_15.currentText()),
        '매수조건1': 1 if ui.pt_checkBoxxxxx_14.isChecked() else 0,
        '매수조건2': float(ui.pt_lineEdittttt_01.text()),
        '매수조건3': 1 if ui.pt_checkBoxxxxx_15.isChecked() else 0,
        '매도조건1': 1 if ui.pt_checkBoxxxxx_34.isChecked() else 0,
        '매도조건2': float(ui.pt_lineEdittttt_02.text()),
        '매도조건3': 1 if ui.pt_checkBoxxxxx_35.isChecked() else 0
    }
    dict_pattern_buy = {}
    if ui.pt_checkBoxxxxx_01.isChecked():
        dict_pattern_buy['등락율'] = float(ui.pt_comboBoxxxxx_01.currentText())
    if ui.pt_checkBoxxxxx_02.isChecked():
        dict_pattern_buy['당일거래대금'] = float(ui.pt_comboBoxxxxx_02.currentText())
    if ui.pt_checkBoxxxxx_03.isChecked():
        dict_pattern_buy['체결강도'] = float(ui.pt_comboBoxxxxx_03.currentText())
    if ui.pt_checkBoxxxxx_04.isChecked():
        dict_pattern_buy['초당매수금액'] = float(ui.pt_comboBoxxxxx_04.currentText())
    if ui.pt_checkBoxxxxx_05.isChecked():
        dict_pattern_buy['초당매도금액'] = float(ui.pt_comboBoxxxxx_05.currentText())
    if ui.pt_checkBoxxxxx_06.isChecked():
        dict_pattern_buy['순매수금액'] = float(ui.pt_comboBoxxxxx_06.currentText())
    if ui.pt_checkBoxxxxx_07.isChecked():
        dict_pattern_buy['초당거래대금'] = float(ui.pt_comboBoxxxxx_07.currentText())
    if ui.pt_checkBoxxxxx_08.isChecked():
        dict_pattern_buy['고저평균대비등락율'] = float(ui.pt_comboBoxxxxx_08.currentText())
    if ui.pt_checkBoxxxxx_09.isChecked():
        dict_pattern_buy['매도1잔량금액'] = float(ui.pt_comboBoxxxxx_09.currentText())
    if ui.pt_checkBoxxxxx_10.isChecked():
        dict_pattern_buy['매수1잔량금액'] = float(ui.pt_comboBoxxxxx_10.currentText())
    if ui.pt_checkBoxxxxx_11.isChecked():
        dict_pattern_buy['매도총잔량금액'] = float(ui.pt_comboBoxxxxx_11.currentText())
    if ui.pt_checkBoxxxxx_12.isChecked():
        dict_pattern_buy['매수총잔량금액'] = float(ui.pt_comboBoxxxxx_12.currentText())
    if ui.pt_checkBoxxxxx_13.isChecked():
        dict_pattern_buy['매도수5호가총금액'] = float(ui.pt_comboBoxxxxx_13.currentText())
    dict_pattern_sell = {}
    if ui.pt_checkBoxxxxx_21.isChecked():
        dict_pattern_sell['등락율'] = float(ui.pt_comboBoxxxxx_21.currentText())
    if ui.pt_checkBoxxxxx_22.isChecked():
        dict_pattern_sell['당일거래대금'] = float(ui.pt_comboBoxxxxx_22.currentText())
    if ui.pt_checkBoxxxxx_23.isChecked():
        dict_pattern_sell['체결강도'] = float(ui.pt_comboBoxxxxx_23.currentText())
    if ui.pt_checkBoxxxxx_24.isChecked():
        dict_pattern_sell['초당매수금액'] = float(ui.pt_comboBoxxxxx_24.currentText())
    if ui.pt_checkBoxxxxx_25.isChecked():
        dict_pattern_sell['초당매도금액'] = float(ui.pt_comboBoxxxxx_25.currentText())
    if ui.pt_checkBoxxxxx_26.isChecked():
        dict_pattern_sell['순매수금액'] = float(ui.pt_comboBoxxxxx_26.currentText())
    if ui.pt_checkBoxxxxx_27.isChecked():
        dict_pattern_sell['초당거래대금'] = float(ui.pt_comboBoxxxxx_27.currentText())
    if ui.pt_checkBoxxxxx_28.isChecked():
        dict_pattern_sell['고저평균대비등락율'] = float(ui.pt_comboBoxxxxx_28.currentText())
    if ui.pt_checkBoxxxxx_29.isChecked():
        dict_pattern_sell['매도1잔량금액'] = float(ui.pt_comboBoxxxxx_29.currentText())
    if ui.pt_checkBoxxxxx_30.isChecked():
        dict_pattern_sell['매수1잔량금액'] = float(ui.pt_comboBoxxxxx_30.currentText())
    if ui.pt_checkBoxxxxx_31.isChecked():
        dict_pattern_sell['매도총잔량금액'] = float(ui.pt_comboBoxxxxx_31.currentText())
    if ui.pt_checkBoxxxxx_32.isChecked():
        dict_pattern_sell['매수총잔량금액'] = float(ui.pt_comboBoxxxxx_32.currentText())
    if ui.pt_checkBoxxxxx_33.isChecked():
        dict_pattern_sell['매도수5호가총금액'] = float(ui.pt_comboBoxxxxx_33.currentText())
    return dict_pattern, dict_pattern_buy, dict_pattern_sell
