import os
import random
import sqlite3
import pandas as pd
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLineEdit, QMessageBox, QApplication
from multiprocessing import Process
from backtester.optimiz import Optimize
from backtester.backtest import BackTest
from backtester.optimiz_conditions import OptimizeConditions
from backtester.optimiz_genetic_algorithm import OptimizeGeneticAlgorithm
from backtester.rolling_walk_forward_test import RollingWalkForwardTest
from ui.set_text import famous_saying
from utility.setting import DB_STRATEGY
from utility.static import qtest_qwait


def bebutton_clicked_01(ui):
    if ui.main_btn == 2 or (ui.dialog_scheduler.isVisible() and ui.sd_pushButtonnn_01.text() == '주식'):
        if not ui.backtest_engine:
            ui.StartBacktestEngine('주식')
        else:
            buttonReply = QMessageBox.question(
                ui.dialog_backengine, '백테엔진', '이미 백테스트 엔진이 구동중입니다.\n엔진을 재시작하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                ui.backtest_engine = False
                for proc in ui.back_procs:
                    proc.kill()
                for proc in ui.bact_procs:
                    proc.kill()
                ui.BacktestEngineVarsReset()
                qtest_qwait(3)
                ui.StartBacktestEngine('주식')
    elif ui.main_btn == 3 or (ui.dialog_scheduler.isVisible() and ui.sd_pushButtonnn_01.text() == '코인'):
        if not ui.backtest_engine:
            ui.StartBacktestEngine('코인')
        else:
            buttonReply = QMessageBox.question(
                ui.dialog_backengine, '백테엔진', '이미 백테스트 엔진이 구동중입니다.\n엔진을 재시작하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                ui.backtest_engine = False
                for proc in ui.back_procs:
                    proc.kill()
                for proc in ui.bact_procs:
                    proc.kill()
                ui.BacktestEngineVarsReset()
                qtest_qwait(3)
                ui.StartBacktestEngine('코인')

def backtest_engine_vars_reset(ui):
    ui.ClearBacktestQ()
    ui.back_procs = []
    ui.bact_procs = []
    ui.back_pques = []
    ui.bact_pques = []
    ui.dict_cn    = None
    ui.dict_mt    = None
    ui.back_count = 0
    ui.startday   = 0
    ui.endday     = 0
    ui.starttime  = 0
    ui.endtime    = 0

def back_bench(ui, windowQ, backQ, soundQ, totalQ, liveQ):
    buttonReply = QMessageBox.question(
        ui, "벤치 테스트", "백테 벤치 테스트를 진행합니다.\n틱데이터가 9시 30분까지 로딩되어 있어야합니다.\n계속하시겠습니까?\n",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    )
    if buttonReply == QMessageBox.Yes:
        if ui.BacktestProcessAlive():
            QMessageBox.critical(ui, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not ui.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                ui.BackTestengineShow('주식')
                return
            if not ui.back_condition:
                QMessageBox.critical(ui, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            startday  = ui.svjb_dateEditt_01.date().toString('yyyyMMdd')
            endday    = ui.svjb_dateEditt_02.date().toString('yyyyMMdd')
            starttime = ui.svjb_lineEditt_02.text()
            endtime   = ui.svjb_lineEditt_03.text()
            betting   = ui.svjb_lineEditt_04.text()
            avgtime   = ui.svjb_lineEditt_05.text()
            bl        = True if ui.dict_set['블랙리스트추가'] else False

            if int(avgtime) not in ui.avg_list:
                QMessageBox.critical(ui, '오류 알림', '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                return
            if '' in (startday, endday, starttime, endtime, betting, avgtime):
                QMessageBox.critical(ui, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return

            ui.ClearBacktestQ()
            for bpq in ui.back_pques:
                bpq.put(('백테유형', '백테스트'))

            backQ.put((betting, avgtime, startday, endday, starttime, endtime, '벤치전략', '벤치전략', ui.dict_cn, ui.back_count, bl, False, ui.df_kp, ui.df_kd, False, False))
            ui.proc_backtester_bb = Process(target=BackTest, args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '백테스트', 'S'))
            ui.proc_backtester_bb.start()
            ui.svjButtonClicked_07()
            ui.ss_progressBar_01.setValue(0)
            ui.ssicon_alert = True

def sdbutton_clicked_01(ui):
    if type(ui.dialog_scheduler.focusWidget()) != QLineEdit:
        if ui.sd_pushButtonnn_01.text() == '주식':
            ui.sd_pushButtonnn_01.setText('코인')
        else:
            ui.sd_pushButtonnn_01.setText('주식')

def sdbutton_clicked_02(ui, windowQ, backQ, soundQ, totalQ, liveQ):
    if ui.BacktestProcessAlive():
        QMessageBox.critical(ui.dialog_scheduler, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
    else:
        bt_gubun = ui.sd_pushButtonnn_01.text()
        if not ui.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
            ui.BackTestengineShow(bt_gubun)
            return

        if bt_gubun == '주식' and ui.main_btn != 2:
            ui.mnButtonClicked_01(2)
        elif bt_gubun == '코인' and ui.main_btn != 3:
            ui.mnButtonClicked_01(3)

        ui.ClearBacktestQ()
        if ui.back_schedul:
            ui.back_scount += 1
        else:
            for progressBar in ui.list_progressBarrr:
                progressBar.setValue(0)

        while ui.back_scount < 16 and not ui.list_checkBoxxxxxx[ui.back_scount].isChecked():
            ui.back_scount += 1

        if ui.back_scount < 16:
            back_name = ui.list_gcomboBoxxxxx[ui.back_scount].currentText()
            if back_name == '백테스트':
                startday  = ui.list_sdateEdittttt[ui.back_scount].date().toString('yyyyMMdd')
                endday    = ui.list_edateEdittttt[ui.back_scount].date().toString('yyyyMMdd')
                starttime = ui.list_slineEdittttt[ui.back_scount].text()
                endtime   = ui.list_elineEdittttt[ui.back_scount].text()
                betting   = ui.list_blineEdittttt[ui.back_scount].text()
                avgtime   = ui.list_alineEdittttt[ui.back_scount].text()
                buystg    = ui.list_bcomboBoxxxxx[ui.back_scount].currentText()
                sellstg   = ui.list_scomboBoxxxxx[ui.back_scount].currentText()
                bl        = True if ui.dict_set['블랙리스트추가'] else False

                if int(avgtime) not in ui.avg_list:
                    ui.StopScheduler()
                    QMessageBox.critical(ui.dialog_scheduler, '오류 알림', '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                    return

                for bpq in ui.back_pques:
                    bpq.put(('백테유형', '백테스트'))

                if bt_gubun == '주식':
                    backQ.put((betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg, ui.dict_cn, ui.back_count, bl, True, ui.df_kp, ui.df_kd, False, False))
                    gubun = 'S'
                else:
                    backQ.put((betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg, None, ui.back_count, bl, True, None, None, False, False))
                    gubun = 'C' if ui.dict_set['거래소'] == '업비트' else 'CF'

                ui.proc_backtester_bb = Process(target=BackTest, args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, back_name, gubun))
                ui.proc_backtester_bb.start()

                if bt_gubun == '주식':
                    ui.svjButtonClicked_07()
                    ui.ss_progressBar_01.setValue(0)
                    ui.ssicon_alert = True
                else:
                    ui.cvjButtonClicked_07()
                    ui.cs_progressBar_01.setValue(0)
                    ui.csicon_alert = True

            elif '조건' in back_name:
                starttime   = ui.list_slineEdittttt[ui.back_scount].text()
                endtime     = ui.list_elineEdittttt[ui.back_scount].text()
                betting     = ui.list_blineEdittttt[ui.back_scount].text()
                avgtime     = ui.list_alineEdittttt[ui.back_scount].text()
                buystg      = ui.list_bcomboBoxxxxx[ui.back_scount].currentText()
                sellstg     = ui.list_scomboBoxxxxx[ui.back_scount].currentText()
                bcount      = ui.sd_oclineEdittt_01.text()
                scount      = ui.sd_oclineEdittt_02.text()
                rcount      = ui.sd_oclineEdittt_03.text()
                optistd     = ui.list_tcomboBoxxxxx[ui.back_scount].currentText()
                weeks_train = ui.list_p1comboBoxxxx[ui.back_scount].currentText()
                weeks_valid = ui.list_p2comboBoxxxx[ui.back_scount].currentText()
                weeks_test  = ui.list_p3comboBoxxxx[ui.back_scount].currentText()
                benginesday = ui.be_dateEdittttt_01.date().toString('yyyyMMdd')
                bengineeday = ui.be_dateEdittttt_02.date().toString('yyyyMMdd')

                for bpq in ui.back_pques:
                    bpq.put(('백테유형', '조건최적화'))

                backQ.put((
                    betting, avgtime, starttime, endtime, buystg, sellstg, ui.dict_set['최적화기준값제한'], optistd,
                    bcount, scount, rcount, ui.back_count, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday
                ))
                if bt_gubun == '주식':
                    gubun = 'S'
                elif ui.dict_set['거래소'] == '업비트':
                    gubun = 'C'
                else:
                    gubun = 'CF'

                if back_name == '조건 최적화':
                    ui.proc_backtester_oc = Process(
                        target=OptimizeConditions,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OC', gubun)
                    )
                    ui.proc_backtester_oc.start()
                elif back_name == '검증 조건 최적화':
                    ui.proc_backtester_ocv = Process(
                        target=OptimizeConditions,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OCV', gubun)
                    )
                    ui.proc_backtester_ocv.start()
                elif back_name == '교차검증 조건 최적화':
                    ui.proc_backtester_ocvc = Process(
                        target=OptimizeConditions,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OCVC', gubun)
                    )
                    ui.proc_backtester_ocvc.start()

                if bt_gubun == '주식':
                    ui.svjButtonClicked_07()
                    ui.ss_progressBar_01.setValue(0)
                    ui.ssicon_alert = True
                else:
                    ui.cvjButtonClicked_07()
                    ui.cs_progressBar_01.setValue(0)
                    ui.csicon_alert = True

            elif 'GA' in back_name:
                starttime   = ui.list_slineEdittttt[ui.back_scount].text()
                endtime     = ui.list_elineEdittttt[ui.back_scount].text()
                betting     = ui.list_blineEdittttt[ui.back_scount].text()
                buystg      = ui.list_bcomboBoxxxxx[ui.back_scount].currentText()
                sellstg     = ui.list_scomboBoxxxxx[ui.back_scount].currentText()
                optivars    = ui.list_vcomboBoxxxxx[ui.back_scount].currentText()
                optistd     = ui.list_tcomboBoxxxxx[ui.back_scount].currentText()
                weeks_train = ui.list_p1comboBoxxxx[ui.back_scount].currentText()
                weeks_valid = ui.list_p2comboBoxxxx[ui.back_scount].currentText()
                weeks_test  = ui.list_p3comboBoxxxx[ui.back_scount].currentText()
                benginesday = ui.be_dateEdittttt_01.date().toString('yyyyMMdd')
                bengineeday = ui.be_dateEdittttt_02.date().toString('yyyyMMdd')

                for bpq in ui.back_pques:
                    bpq.put(('백테유형', 'GA최적화'))

                if bt_gubun == '주식':
                    backQ.put((
                        betting, starttime, endtime, buystg, sellstg, optivars, ui.dict_cn, ui.dict_set['최적화기준값제한'],
                        optistd, ui.back_count, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday
                    ))
                    gubun = 'S'
                else:
                    backQ.put((
                        betting, starttime, endtime, buystg, sellstg, optivars, None, ui.dict_set['최적화기준값제한'],
                        optistd, ui.back_count, weeks_train, weeks_valid, weeks_test, benginesday, benginesday
                    ))
                    gubun = 'C' if ui.dict_set['거래소'] == '업비트' else 'CF'

                if back_name == '그리드 GA 최적화':
                    ui.proc_backtester_og = Process(
                        target=OptimizeGeneticAlgorithm,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OG', gubun)
                    )
                    ui.proc_backtester_og.start()
                elif back_name == '그리드 검증 GA 최적화':
                    ui.proc_backtester_ogv = Process(
                        target=OptimizeGeneticAlgorithm,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OGV', gubun)
                    )
                    ui.proc_backtester_ogv.start()
                elif back_name == '그리드 교차검증 GA 최적화':
                    ui.proc_backtester_ogvc = Process(
                        target=OptimizeGeneticAlgorithm,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OGVC', gubun)
                    )
                    ui.proc_backtester_ogvc.start()

                if bt_gubun == '주식':
                    ui.svjButtonClicked_07()
                    ui.ss_progressBar_01.setValue(0)
                    ui.ssicon_alert = True
                else:
                    ui.cvjButtonClicked_07()
                    ui.cs_progressBar_01.setValue(0)
                    ui.csicon_alert = True

            elif '전진분석' in back_name:
                startday    = ui.list_sdateEdittttt[ui.back_scount].date().toString('yyyyMMdd')
                endday      = ui.list_edateEdittttt[ui.back_scount].date().toString('yyyyMMdd')
                starttime   = ui.list_slineEdittttt[ui.back_scount].text()
                endtime     = ui.list_elineEdittttt[ui.back_scount].text()
                betting     = ui.list_blineEdittttt[ui.back_scount].text()
                buystg      = ui.list_bcomboBoxxxxx[ui.back_scount].currentText()
                sellstg     = ui.list_scomboBoxxxxx[ui.back_scount].currentText()
                optivars    = ui.list_vcomboBoxxxxx[ui.back_scount].currentText()
                weeks_train = ui.list_p1comboBoxxxx[ui.back_scount].currentText()
                weeks_valid = ui.list_p2comboBoxxxx[ui.back_scount].currentText()
                weeks_test  = ui.list_p3comboBoxxxx[ui.back_scount].currentText()
                ccount      = ui.list_p4comboBoxxxx[ui.back_scount].currentText()
                optistd     = ui.list_tcomboBoxxxxx[ui.back_scount].currentText()
                benginesday = ui.be_dateEdittttt_01.date().toString('yyyyMMdd')
                bengineeday = ui.be_dateEdittttt_02.date().toString('yyyyMMdd')
                optunasampl = ui.op_comboBoxxxx_01.currentText()
                optunafixv  = ui.op_lineEditttt_01.text()
                optunacount = ui.op_lineEditttt_02.text()
                optunaautos = 1 if ui.op_checkBoxxxx_01.isChecked() else 0

                for bpq in ui.back_pques:
                    bpq.put(('백테유형', '전진분석'))

                if bt_gubun == '주식':
                    backQ.put((
                        betting, startday, endday, starttime, endtime, buystg, sellstg, optivars, ui.dict_cn,
                        ccount, ui.dict_set['최적화기준값제한'], optistd, ui.back_count, True, ui.df_kp,
                        ui.df_kd, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday, optunasampl,
                        optunafixv, optunacount, optunaautos, False
                    ))
                    gubun = 'S'
                else:
                    backQ.put((
                        betting, startday, endday, starttime, endtime, buystg, sellstg, optivars, None, ccount,
                        ui.dict_set['최적화기준값제한'], optistd, ui.back_count, True, None, None, weeks_train,
                        weeks_valid, weeks_test, benginesday, bengineeday, optunasampl, optunafixv, optunacount,
                        optunaautos, False
                    ))
                    gubun = 'C' if ui.dict_set['거래소'] == '업비트' else 'CF'

                if back_name == '그리드 최적화 전진분석':
                    ui.proc_backtester_or = Process(
                        target=RollingWalkForwardTest,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '전진분석OR', gubun)
                    )
                    ui.proc_backtester_or.start()
                elif back_name == '그리드 검증 최적화 전진분석':
                    ui.proc_backtester_orv = Process(
                        target=RollingWalkForwardTest,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '전진분석ORV', gubun)
                    )
                    ui.proc_backtester_orv.start()
                elif back_name == '그리드 교차검증 최적화 전진분석':
                    ui.proc_backtester_orvc = Process(
                        target=RollingWalkForwardTest,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '전진분석ORVC', gubun)
                    )
                    ui.proc_backtester_orvc.start()
                elif back_name == '베이지안 최적화 전진분석':
                    ui.proc_backtester_br = Process(
                        target=RollingWalkForwardTest,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '전진분석BR', gubun)
                    )
                    ui.proc_backtester_br.start()
                elif back_name == '베이지안 검증 최적화 전진분석':
                    ui.proc_backtester_brv = Process(
                        target=RollingWalkForwardTest,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '전진분석BRV', gubun)
                    )
                    ui.proc_backtester_brv.start()
                elif back_name == '베이지안 교차검증 최적화 전진분석':
                    ui.proc_backtester_brvc = Process(
                        target=RollingWalkForwardTest,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '전진분석BRVC', gubun)
                    )
                    ui.proc_backtester_brvc.start()

                if bt_gubun == '주식':
                    ui.svjButtonClicked_07()
                    ui.ss_progressBar_01.setValue(0)
                    ui.ssicon_alert = True
                else:
                    ui.cvjButtonClicked_07()
                    ui.cs_progressBar_01.setValue(0)
                    ui.csicon_alert = True

            elif '최적화' in back_name:
                starttime   = ui.list_slineEdittttt[ui.back_scount].text()
                endtime     = ui.list_elineEdittttt[ui.back_scount].text()
                betting     = ui.list_blineEdittttt[ui.back_scount].text()
                buystg      = ui.list_bcomboBoxxxxx[ui.back_scount].currentText()
                sellstg     = ui.list_scomboBoxxxxx[ui.back_scount].currentText()
                optivars    = ui.list_vcomboBoxxxxx[ui.back_scount].currentText()
                ccount      = ui.list_p4comboBoxxxx[ui.back_scount].currentText()
                optistd     = ui.list_tcomboBoxxxxx[ui.back_scount].currentText()
                weeks_train = ui.list_p1comboBoxxxx[ui.back_scount].currentText()
                weeks_valid = ui.list_p2comboBoxxxx[ui.back_scount].currentText()
                weeks_test  = ui.list_p3comboBoxxxx[ui.back_scount].currentText()
                benginesday = ui.be_dateEdittttt_01.date().toString('yyyyMMdd')
                bengineeday = ui.be_dateEdittttt_02.date().toString('yyyyMMdd')
                optunasampl = ui.op_comboBoxxxx_01.currentText()
                optunafixv  = ui.op_lineEditttt_01.text()
                optunacount = ui.op_lineEditttt_02.text()
                optunaautos = 1 if ui.op_checkBoxxxx_01.isChecked() else 0

                for bpq in ui.back_pques:
                    bpq.put(('백테유형', '최적화'))

                if bt_gubun == '주식':
                    backQ.put((
                        betting, starttime, endtime, buystg, sellstg, optivars, ui.dict_cn, ccount,
                        ui.dict_set['최적화기준값제한'], optistd, ui.back_count, True, ui.df_kp, ui.df_kd,
                        weeks_train, weeks_valid, weeks_test, benginesday, bengineeday, optunasampl, optunafixv,
                        optunacount, optunaautos, False
                    ))
                    gubun = 'S'
                else:
                    backQ.put((
                        betting, starttime, endtime, buystg, sellstg, optivars, None, ccount,
                        ui.dict_set['최적화기준값제한'], optistd, ui.back_count, True, None, None, weeks_train,
                        weeks_valid, weeks_test, benginesday, bengineeday, optunasampl, optunafixv, optunacount,
                        optunaautos, False
                    ))
                    gubun = 'C' if ui.dict_set['거래소'] == '업비트' else 'CF'

                if back_name == '그리드 최적화':
                    ui.proc_backtester_o = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화O', gubun)
                    )
                    ui.proc_backtester_o.start()
                elif back_name == '그리드 검증 최적화':
                    ui.proc_backtester_ov = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OV', gubun)
                    )
                    ui.proc_backtester_ov.start()
                elif back_name == '그리드 교차검증 최적화':
                    ui.proc_backtester_ovc = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OVC', gubun)
                    )
                    ui.proc_backtester_ovc.start()
                elif back_name == '베이지안 최적화':
                    ui.proc_backtester_b = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화B', gubun)
                    )
                    ui.proc_backtester_b.start()
                elif back_name == '베이지안 검증 최적화':
                    ui.proc_backtester_bv = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화BV', gubun)
                    )
                    ui.proc_backtester_bv.start()
                elif back_name == '베이지안 교차검증 최적화':
                    ui.proc_backtester_bvc = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화BVC', gubun)
                    )
                    ui.proc_backtester_bvc.start()
                elif back_name == '그리드 최적화 테스트':
                    ui.proc_backtester_ot = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OT', gubun)
                    )
                    ui.proc_backtester_ot.start()
                elif back_name == '그리드 검증 최적화 테스트':
                    ui.proc_backtester_ovt = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OVT', gubun)
                    )
                    ui.proc_backtester_ovt.start()
                elif back_name == '그리드 교차검증 최적화 테스트':
                    ui.proc_backtester_ovct = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화OVCT', gubun)
                    )
                    ui.proc_backtester_ovct.start()
                elif back_name == '베이지안 최적화 테스트':
                    ui.proc_backtester_bt = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화BT', gubun)
                    )
                    ui.proc_backtester_bt.start()
                elif back_name == '베이지안 검증 최적화 테스트':
                    ui.proc_backtester_bvt = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화BVT', gubun)
                    )
                    ui.proc_backtester_bvt.start()
                elif back_name == '베이지안 교차검증 최적화 테스트':
                    ui.proc_backtester_bvct = Process(
                        target=Optimize,
                        args=(windowQ, backQ, soundQ, totalQ, liveQ, ui.back_pques, ui.bact_pques, '최적화BVCT', gubun)
                    )
                    ui.proc_backtester_bvct.start()

                if bt_gubun == '주식':
                    ui.svjButtonClicked_07()
                    ui.ss_progressBar_01.setValue(0)
                    ui.ssicon_alert = True
                else:
                    ui.cvjButtonClicked_07()
                    ui.cs_progressBar_01.setValue(0)
                    ui.csicon_alert = True

            ui.list_progressBarrr[ui.back_scount].setValue(0)
            ui.back_schedul = True
        else:
            StopScheduler(ui, True)

def StopScheduler(ui, gubun=False):
    ui.back_scount = 0
    ui.back_schedul = False
    if ui.auto_mode:
        ui.AutoBackSchedule(3)
    if gubun and ui.sd_scheckBoxxxx_02.isChecked():
        QTimer.singleShot(180 * 1000, ui.ProcessKill)
        os.system('shutdown /s /t 300')

def sdbutton_clicked_03(ui):
    if ui.sd_pushButtonnn_01.text() == '주식':
        ui.ssButtonClicked_06()
    else:
        ui.csButtonClicked_06()
    for progressBar in ui.list_progressBarrr:
        progressBar.setValue(0)

def sdbutton_clicked_04(ui):
    con = sqlite3.connect(DB_STRATEGY)
    df = pd.read_sql('SELECT * FROM schedule', con).set_index('index')
    con.close()
    if len(df) > 0:
        if ui.sd_scheckBoxxxx_01.isChecked():
            ui.sd_scheckBoxxxx_01.nextCheckState()
        ui.sd_dcomboBoxxxx_01.clear()
        indexs = list(df.index)
        indexs.sort()
        for i, index in enumerate(indexs):
            ui.sd_dcomboBoxxxx_01.addItem(index)
            if i == 0:
                ui.sd_dlineEditttt_01.setText(index)

def sdbutton_clicked_05(ui, proc_query, queryQ):
    schedule_name = ui.sd_dlineEditttt_01.text()
    if schedule_name == '':
        QMessageBox.critical(ui.dialog_scheduler, '오류 알림', '스케쥴 이름이 공백 상태입니다.\n')
    else:
        schedule = ''
        for i in range(16):
            if ui.list_checkBoxxxxxx[i].isChecked():
                schedule += ui.list_gcomboBoxxxxx[i].currentText() + ';'
                schedule += ui.list_slineEdittttt[i].text() + ';'
                schedule += ui.list_elineEdittttt[i].text() + ';'
                schedule += ui.list_blineEdittttt[i].text() + ';'
                schedule += ui.list_alineEdittttt[i].text() + ';'
                schedule += ui.list_p1comboBoxxxx[i].currentText() + ';'
                schedule += ui.list_p2comboBoxxxx[i].currentText() + ';'
                schedule += ui.list_p3comboBoxxxx[i].currentText() + ';'
                schedule += ui.list_p4comboBoxxxx[i].currentText() + ';'
                schedule += ui.list_tcomboBoxxxxx[i].currentText() + ';'
                schedule += ui.list_bcomboBoxxxxx[i].currentText() + ';'
                schedule += ui.list_scomboBoxxxxx[i].currentText() + ';'
                schedule += ui.list_vcomboBoxxxxx[i].currentText() + '^'
        schedule += '1;' if ui.sd_scheckBoxxxx_02.isChecked() else '0;'
        schedule += ui.sd_oclineEdittt_01.text() + ';'
        schedule += ui.sd_oclineEdittt_02.text() + ';'
        schedule += ui.sd_oclineEdittt_03.text()
        if proc_query.is_alive():
            queryQ.put(('전략디비', f"DELETE FROM schedule WHERE `index` = '{schedule_name}'"))
            df = pd.DataFrame({'스케쥴': [schedule]}, index=[schedule_name])
            queryQ.put(('전략디비', df, 'schedule', 'append'))
        QMessageBox.information(ui.dialog_scheduler, '저장 완료', random.choice(famous_saying))
