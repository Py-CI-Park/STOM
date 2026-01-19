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
from utility.setting import DB_STRATEGY, ui_num
from utility.static import qtest_qwait
from ui.ui_button_clicked_icos import (
    _collect_icos_config,
    _collect_analysis_config,
    # Note: _run_icos_process는 더 이상 사용하지 않음 (2026-01-19)
    # 새로운 ICOSBackTest 클래스가 기존 백테스트 엔진을 완전 통합
)


def _check_icos_enabled(ui) -> bool:
    """ICOS 활성화 상태 확인.

    설정 파일을 우선 확인하여 UI 속성과 동기화합니다.
    다이얼로그를 열지 않아도 ICOS 상태를 확인할 수 있습니다.

    Args:
        ui: 메인 UI 클래스

    Returns:
        ICOS 활성화 여부 (True/False)
    """
    import json
    import traceback
    from pathlib import Path

    # 기본 로그 타겟 (예외 발생 시에도 로깅 가능하도록)
    log_target = 6  # 기본값: S백테스트

    try:
        # bt_gubun에 따른 로그 출력 대상 결정
        bt_gubun = ui.sd_pushButtonnn_01.text() if hasattr(ui, 'sd_pushButtonnn_01') else '주식'
        log_target = ui_num.get('S백테스트' if bt_gubun == '주식' else 'C백테스트', 6)

        # 함수 진입 로그 (디버깅용)
        ui.windowQ.put((log_target,
            '<font color=#888888>[DEBUG] _check_icos_enabled() 함수 진입</font>'))

        # 프로젝트 루트 디렉토리 기준 절대 경로 생성
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, '_database')

        ui.windowQ.put((log_target,
            f'<font color=#888888>[DEBUG] 설정 파일 경로: {db_path}</font>'))

        # 1. 설정 파일에서 확인 (가장 신뢰할 수 있는 소스)
        main_path = Path(os.path.join(db_path, 'icos_analysis_config.json'))
        legacy_path = Path(os.path.join(db_path, 'icos_config.json'))

        ui.windowQ.put((log_target,
            f'<font color=#888888>[DEBUG] main_path 존재여부: {main_path.exists()}</font>'))

        if main_path.exists():
            try:
                with open(main_path, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                # 새 형식에서 icos.enabled 확인
                icos_config = config_dict.get('icos', {})
                enabled = icos_config.get('enabled', False)
                # UI 속성과 동기화
                ui.icos_enabled = enabled
                # 디버그 로그
                ui.windowQ.put((log_target,
                    f'<font color=#888888>[DEBUG] ICOS 설정: enabled={enabled} (설정파일)</font>'))
                return enabled
            except Exception as e:
                ui.windowQ.put((log_target,
                    f'<font color=#ff8800>[DEBUG] 설정파일 로드 오류: {e}</font>'))
        elif legacy_path.exists():
            try:
                with open(legacy_path, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                enabled = config_dict.get('enabled', False)
                ui.icos_enabled = enabled
                ui.windowQ.put((log_target,
                    f'<font color=#888888>[DEBUG] ICOS 설정: enabled={enabled} (레거시)</font>'))
                return enabled
            except Exception as e:
                ui.windowQ.put((log_target,
                    f'<font color=#ff8800>[DEBUG] 레거시 파일 로드 오류: {e}</font>'))

        # 2. 설정 파일이 없는 경우 UI 속성 확인
        if hasattr(ui, 'icos_enabled'):
            ui.windowQ.put((log_target,
                f'<font color=#888888>[DEBUG] ICOS 설정: enabled={ui.icos_enabled} (UI속성)</font>'))
            return ui.icos_enabled

        # 기본값: 비활성화
        ui.icos_enabled = False
        ui.windowQ.put((log_target,
            '<font color=#888888>[DEBUG] ICOS 설정: enabled=False (기본값)</font>'))
        return False

    except Exception as e:
        # 모든 예외를 잡아서 로깅
        error_msg = f'[ICOS 오류] _check_icos_enabled 예외: {type(e).__name__}: {e}'
        try:
            ui.windowQ.put((log_target,
                f'<font color=#ff0000>{error_msg}</font>'))
            ui.windowQ.put((log_target,
                f'<font color=#ff0000>[ICOS 오류] 스택: {traceback.format_exc()}</font>'))
        except:
            print(error_msg)
            traceback.print_exc()
        return False


def _run_icos_backtest(ui, bt_gubun, buystg, sellstg, startday, endday, starttime, endtime, betting, avgtime):
    """ICOS 모드 백테스트 실행 (완전 통합 방식).

    기존 BackTest 엔진(back_eques 멀티프로세스)을 완전히 재활용하면서
    반복적 조건식 최적화를 수행합니다.

    변경사항 (2026-01-19):
    - 기존 SyncBacktestRunner 대신 ICOSBackTest 클래스 사용
    - backQ 큐를 통한 기존 백테스트 엔진 재활용
    - back_eques 멀티프로세스 분산 처리 활용
    - optimiz.py 패턴 적용: 최적화 완료 후 최종 백테스트 자동 실행

    Args:
        ui: 메인 UI 클래스
        bt_gubun: '주식' 또는 '코인'
        buystg: 매수 조건식 이름
        sellstg: 매도 조건식 이름
        startday: 시작일 (YYYYMMDD)
        endday: 종료일 (YYYYMMDD)
        starttime: 시작시간 (HHMM)
        endtime: 종료시간 (HHMM)
        betting: 베팅금액
        avgtime: 평균값틱수
    """
    from backtester.backtest_icos import ICOSBackTest

    # 이미 ICOS가 실행 중인지 확인
    if hasattr(ui, 'proc_icos') and ui.proc_icos is not None and ui.proc_icos.is_alive():
        QMessageBox.warning(
            ui.dialog_scheduler,
            '알림',
            'ICOS가 이미 실행 중입니다.\n'
        )
        return

    # ICOS 설정값 수집
    try:
        icos_config = _collect_icos_config(ui)
        analysis_config = _collect_analysis_config(ui)

        # 통합 config_dict 생성
        config_dict = {
            **icos_config,
            'analysis': analysis_config,
        }

        # 디버그 로그
        log_target = ui_num.get('S백테스트' if bt_gubun == '주식' else 'C백테스트', 6)
        ui.windowQ.put((log_target,
            f'<font color=#888888>[ICOS] 설정: max_iter={icos_config.get("max_iterations")}, '
            f'threshold={icos_config.get("convergence_threshold")}%</font>'))

    except ValueError as e:
        QMessageBox.critical(
            ui.dialog_scheduler,
            'ICOS 설정 오류',
            f'ICOS 설정값 오류: {str(e)}\nAlt+I로 설정을 확인하세요.\n'
        )
        return
    except Exception as e:
        err_log_target = ui_num.get('S백테스트' if bt_gubun == '주식' else 'C백테스트', 6)
        ui.windowQ.put((err_log_target,
            f'<font color=#ff0000>[ICOS 오류] 설정 수집 실패: {type(e).__name__}: {e}</font>'))
        return

    # gubun 결정
    gubun = 'S' if bt_gubun == '주식' else ('C' if ui.dict_set['거래소'] == '업비트' else 'CF')

    # 백테엔진 시작 여부 확인
    if not hasattr(ui, 'dict_cn') or not ui.dict_cn:
        QMessageBox.critical(
            ui.dialog_scheduler,
            'ICOS 오류',
            '백테엔진이 시작되지 않았습니다.\n\n'
            'ICOS를 실행하려면 먼저 백테엔진을 시작해야 합니다.\n'
            '(백테스트 버튼 클릭 또는 Ctrl+백테스트)\n'
        )
        return

    # ICOS 로그 초기화
    if hasattr(ui, 'icos_textEditxxx_01'):
        ui.icos_textEditxxx_01.clear()
        ui.icos_textEditxxx_01.append('<font color="#45cdf7">ICOS 완전 통합 모드 시작</font>')
        ui.icos_textEditxxx_01.append(f'<font color="#cccccc">조건식: {buystg} / {sellstg}</font>')
        ui.icos_textEditxxx_01.append(f'<font color="#cccccc">기간: {startday} ~ {endday}</font>')
        ui.icos_textEditxxx_01.append(
            '<font color="#888888">기존 백테스트 엔진(멀티프로세스) 활용</font>')

        if hasattr(ui, 'icos_progressBar_01'):
            ui.icos_progressBar_01.setValue(0)

    # 블랙리스트 설정
    bl = True if ui.dict_set['블랙리스트추가'] else False

    # 백테 유형 설정 - '백테스트' 유형 사용 (백엔진에 'ICOS' 분기가 없음)
    # ICOS의 개별 백테스트는 기본 백테스트와 동일하므로 '백테스트' 유형 재사용
    for q in ui.back_eques:
        q.put(('백테유형', '백테스트'))

    # backQ에 파라미터 전달 (기존 백테스트와 동일한 형식!)
    # BackTest.Start()에서 수신하는 것과 동일한 튜플
    ui.backQ.put((
        betting,      # [0] 배팅금액 (백만원 단위)
        avgtime,      # [1] 평균값틱수
        startday,     # [2] 시작일
        endday,       # [3] 종료일
        starttime,    # [4] 시작시간
        endtime,      # [5] 종료시간
        buystg,       # [6] 매수 조건식 이름 (ICOSBackTest에서 DB 조회)
        sellstg,      # [7] 매도 조건식 이름
        ui.dict_cn,   # [8] 종목코드-종목명
        ui.back_count, # [9] 총 틱 수
        bl,           # [10] 블랙리스트
        True,         # [11] 주식=True (스케줄 플래그)
        ui.df_kp,     # [12] 코스피 지수
        ui.df_kd,     # [13] 코스닥 지수
        False         # [14] 플래그
    ))

    # ICOSBackTest 프로세스 시작
    try:
        ui.proc_icos = Process(
            target=ICOSBackTest,
            args=(
                ui.windowQ,     # wq
                ui.backQ,       # bq
                ui.soundQ,      # sq
                ui.totalQ,      # tq
                ui.liveQ,       # lq
                ui.teleQ,       # teleQ
                ui.back_eques,  # beq_list
                ui.back_sques,  # bstq_list
                'ICOS',         # backname
                gubun,          # ui_gubun
                config_dict,    # icos_config
            )
        )
        ui.proc_icos.start()

        # UI 업데이트
        start_log_target = ui_num.get('S백테스트' if bt_gubun == '주식' else 'C백테스트', 6)
        ui.windowQ.put((start_log_target,
            f'<font color=#45cdf7>[ICOS] 기존 백테스트 엔진 통합 모드 시작 (PID: {ui.proc_icos.pid})</font>'))

        if hasattr(ui, 'icos_textEditxxx_01'):
            ui.icos_textEditxxx_01.append(
                f'<font color="#7cfc00">ICOSBackTest 프로세스 시작 (PID: {ui.proc_icos.pid})</font>')

        # 상태 업데이트 (기존 백테스트와 동일)
        if bt_gubun == '주식':
            ui.svjButtonClicked_07()
            ui.ss_progressBar_01.setValue(0)
            ui.ssicon_alert = True
        else:
            ui.cvjButtonClicked_07()
            ui.cs_progressBar_01.setValue(0)
            ui.csicon_alert = True

        # 스케줄 진행 표시
        ui.list_progressBarrr[ui.back_scount].setValue(0)
        ui.back_schedul = True

    except Exception as e:
        QMessageBox.critical(
            ui.dialog_scheduler,
            'ICOS 실행 오류',
            f'ICOS 시작 실패: {str(e)}\n'
        )
        if hasattr(ui, 'icos_textEditxxx_01'):
            ui.icos_textEditxxx_01.append(f'<font color="#ff0000">오류: {str(e)}</font>')


def bebutton_clicked_01(ui):
    if ui.back_engining:
        QMessageBox.critical(ui.dialog_backengine, '오류 알림', '백테엔진 구동 중...\n')
        return

    if ui.main_btn == 2 or (ui.dialog_scheduler.isVisible() and ui.sd_pushButtonnn_01.text() == '주식'):
        if not ui.backtest_engine:
            ui.StartBacktestEngine('주식')
        else:
            buttonReply = QMessageBox.question(
                ui.dialog_backengine, '백테엔진', '이미 백테스트 엔진이 구동중입니다.\n엔진을 재시작하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                ui.BacktestEngineKill()
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
                ui.BacktestEngineKill()
                qtest_qwait(3)
                ui.StartBacktestEngine('코인')


def backtest_engine_kill(ui):
    ui.ClearBacktestQ()
    for p in ui.back_sprocs:
        p.kill()
    for p in ui.back_eprocs:
        p.kill()
    for q in ui.back_sques:
        q.close()
    for q in ui.back_eques:
        q.close()
    ui.back_eprocs = []
    ui.back_sprocs = []
    ui.back_eques  = []
    ui.back_sques  = []
    ui.dict_cn     = None
    ui.dict_mt     = None
    ui.back_count  = 0
    ui.back_engining   = False
    ui.backtest_engine = False
    ui.windowQ.put((ui_num['백테엔진'], '<font color=#45cdf7>모든 백테엔진 프로세스가 종료되었습니다.</font>'))


def sdbutton_clicked_01(ui):
    if type(ui.dialog_scheduler.focusWidget()) != QLineEdit:
        if ui.sd_pushButtonnn_01.text() == '주식':
            ui.sd_pushButtonnn_01.setText('코인')
        else:
            ui.sd_pushButtonnn_01.setText('주식')


def sdbutton_clicked_02(ui):
    # === 파일 무결성 검증: 이 메시지가 보이면 최신 코드가 실행 중 ===
    import datetime
    import os

    # 파일 로그 강제 쓰기 (UI 큐와 무관하게 작동)
    log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            '_log', 'icos_debug.txt')
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"[{datetime.datetime.now()}] sdbutton_clicked_02() 호출됨!\n")
            f.write(f"파일 위치: {__file__}\n")
            f.write(f"함수 버전: a250e76_VERIFICATION\n")
            f.write(f"{'='*80}\n")
    except Exception as e:
        pass  # 로그 실패해도 계속 진행

    # 함수 진입 즉시 로그 출력 (조건문 이전)
    bt_gubun_initial = ui.sd_pushButtonnn_01.text() if hasattr(ui, 'sd_pushButtonnn_01') else '알수없음'
    log_target_initial = ui_num.get('S백테스트' if bt_gubun_initial == '주식' else 'C백테스트', 6)

    # UI 큐 로그 (3개 방법 동시 시도)
    try:
        ui.windowQ.put((log_target_initial,
            f'<font color=#ff00ff>★★★ [TRACE] sdbutton_clicked_02() 함수 진입! bt_gubun={bt_gubun_initial} ★★★</font>'))
    except:
        pass

    try:
        ui.windowQ.put((log_target_initial,
            f'<font color=#ff0000>!!! FILE VERIFICATION: a250e76_VERIFICATION !!!</font>'))
    except:
        pass

    # 강제 print (콘솔 출력)
    print(f"\n{'='*80}")
    print(f"[ICOS DEBUG] sdbutton_clicked_02() CALLED at {datetime.datetime.now()}")
    print(f"[ICOS DEBUG] File: {__file__}")
    print(f"[ICOS DEBUG] Version: a250e76_VERIFICATION")
    print(f"{'='*80}\n")

    if ui.BacktestProcessAlive():
        ui.windowQ.put((log_target_initial,
            '<font color=#ff8800>[TRACE] 백테스트 이미 실행 중 - 중단</font>'))
        QMessageBox.critical(ui.dialog_scheduler, '오류 알림', '현재 백테스트가 실행중입니다.\n중복 실행할 수 없습니다.\n')
    else:
        ui.windowQ.put((log_target_initial,
            '<font color=#00ff00>[TRACE] 백테스트 실행 가능 - 계속 진행</font>'))
        if ui.back_engining:
            ui.windowQ.put((log_target_initial,
                '<font color=#ff8800>[TRACE] 백테엔진 구동 중 - 중단</font>'))
            QMessageBox.critical(ui.dialog_backengine, '오류 알림', '백테엔진 구동 중...\n')
            return

        ui.windowQ.put((log_target_initial,
            f'<font color=#00ffff>[TRACE] backtest_engine={ui.backtest_engine}</font>'))

        bt_gubun = ui.sd_pushButtonnn_01.text()
        if not ui.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
            ui.windowQ.put((log_target_initial,
                '<font color=#ff8800>[TRACE] 백테엔진 미구동 또는 Ctrl 키 - 백테엔진 창 열고 중단</font>'))
            ui.BackTestengineShow(bt_gubun)
            return

        ui.windowQ.put((log_target_initial,
            '<font color=#00ff00>[TRACE] 백테엔진 구동됨 - 백테스트 실행 진행</font>'))

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

        ui.windowQ.put((log_target_initial,
            f'<font color=#00ffff>[TRACE] back_scount={ui.back_scount}, back_schedul={ui.back_schedul}</font>'))

        while ui.back_scount < 16 and not ui.list_checkBoxxxxxx[ui.back_scount].isChecked():
            ui.back_scount += 1

        ui.windowQ.put((log_target_initial,
            f'<font color=#00ffff>[TRACE] 체크박스 검색 후 back_scount={ui.back_scount}</font>'))

        if ui.back_scount < 16:
            back_name = ui.list_gcomboBoxxxxx[ui.back_scount].currentText()

            # 디버그: sdbutton_clicked_02 진입 로그
            _debug_log_target = ui_num.get('S백테스트' if bt_gubun == '주식' else 'C백테스트', 6)
            ui.windowQ.put((_debug_log_target,
                f'<font color=#00ffff>[DEBUG] sdbutton_clicked_02: back_name={back_name}, bt_gubun={bt_gubun}</font>'))

            # ICOS 상태 로그 출력 (모든 백테스트 유형에서)
            ui.windowQ.put((_debug_log_target,
                '<font color=#00ffff>[DEBUG] _check_icos_enabled() 호출 전</font>'))
            icos_enabled = _check_icos_enabled(ui)
            ui.windowQ.put((_debug_log_target,
                f'<font color=#00ffff>[DEBUG] _check_icos_enabled() 반환값: {icos_enabled}</font>'))

            bt_gubun_check = ui.sd_pushButtonnn_01.text() if hasattr(ui, 'sd_pushButtonnn_01') else '주식'
            icos_log_target = ui_num.get('S백테스트' if bt_gubun_check == '주식' else 'C백테스트', 6)
            if icos_enabled:
                if back_name == '백테스트':
                    ui.windowQ.put((icos_log_target,
                        '<font color=#7cfc00>[ICOS] ICOS 모드 활성화됨 - 반복적 조건식 개선이 실행됩니다.</font>'))
                else:
                    ui.windowQ.put((icos_log_target,
                        f'<font color=#ffa500>[ICOS] ICOS가 활성화되어 있지만, "{back_name}" 유형은 ICOS와 호환되지 않습니다.</font>'))
                    ui.windowQ.put((icos_log_target,
                        '<font color=#888888>[ICOS] ICOS는 "백테스트" 유형에서만 작동합니다. '
                        '현재 유형은 기존 방식으로 실행됩니다.</font>'))

            if back_name == '백테스트':
                startday  = ui.list_sdateEdittttt[ui.back_scount].date().toString('yyyyMMdd')
                endday    = ui.list_edateEdittttt[ui.back_scount].date().toString('yyyyMMdd')
                starttime = ui.list_slineEdittttt[ui.back_scount].text()
                endtime   = ui.list_elineEdittttt[ui.back_scount].text()
                betting   = ui.list_blineEdittttt[ui.back_scount].text()
                avgtime   = ui.list_alineEdittttt[ui.back_scount].text()
                buystg    = ui.list_bcomboBoxxxxx[ui.back_scount].currentText()
                sellstg   = ui.list_scomboBoxxxxx[ui.back_scount].currentText()
                bl = True if ui.dict_set['블랙리스트추가'] else False

                if int(avgtime) not in ui.avg_list:
                    ui.StopScheduler()
                    QMessageBox.critical(ui.dialog_scheduler, '오류 알림',
                                         '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                    return

                # ICOS 모드 - 위에서 이미 확인된 icos_enabled 사용
                if icos_enabled:
                    # ICOS는 단일 조건식에 대한 반복 최적화이므로 스케줄러를 비활성화
                    # 스케줄러가 활성화되어 있으면 ICOS 완료 후 다음 백테스트가 자동 실행됨
                    original_schedul = ui.back_schedul
                    ui.back_schedul = False  # 스케줄러 임시 비활성화

                    ui.windowQ.put((_debug_log_target,
                        f'<font color=#00ff00>[ICOS] 스케줄러 비활성화 (원래: {original_schedul})</font>'))

                    _run_icos_backtest(ui, bt_gubun, buystg, sellstg, startday, endday, starttime, endtime, betting, avgtime)
                    return

                for q in ui.back_eques:
                    q.put(('백테유형', '백테스트'))

                if bt_gubun == '주식':
                    ui.backQ.put((betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg, ui.dict_cn,
                                  ui.back_count, bl, True, ui.df_kp, ui.df_kd, False))
                    gubun = 'S'
                    ui.proc_backtester_bs = Process(
                        target=BackTest,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques,
                              ui.back_sques, back_name, gubun)
                    )
                    ui.proc_backtester_bs.start()
                    ui.svjButtonClicked_07()
                    ui.ss_progressBar_01.setValue(0)
                    ui.ssicon_alert = True
                else:
                    ui.backQ.put((betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg, None,
                                  ui.back_count, bl, True, None, None, False))
                    gubun = 'C' if ui.dict_set['거래소'] == '업비트' else 'CF'
                    ui.proc_backtester_bs = Process(
                        target=BackTest,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques,
                              ui.back_sques, back_name, gubun)
                    )
                    ui.proc_backtester_bs.start()
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

                for q in ui.back_eques:
                    q.put(('백테유형', '조건최적화'))

                ui.backQ.put((
                    betting, avgtime, starttime, endtime, buystg, sellstg, ui.dict_set['최적화기준값제한'], optistd,
                    bcount, scount, rcount, ui.back_count, weeks_train, weeks_valid, weeks_test, benginesday,
                    bengineeday
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
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.back_eques, ui.back_sques, '최적화OC', gubun)
                    )
                    ui.proc_backtester_oc.start()
                elif back_name == '검증 조건 최적화':
                    ui.proc_backtester_ocv = Process(
                        target=OptimizeConditions,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.back_eques, ui.back_sques, '최적화OCV', gubun)
                    )
                    ui.proc_backtester_ocv.start()
                elif back_name == '교차검증 조건 최적화':
                    ui.proc_backtester_ocvc = Process(
                        target=OptimizeConditions,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.back_eques, ui.back_sques, '최적화OCVC', gubun)
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

                for q in ui.back_eques:
                    q.put(('백테유형', 'GA최적화'))

                if bt_gubun == '주식':
                    ui.backQ.put((
                        betting, starttime, endtime, buystg, sellstg, optivars, ui.dict_cn, ui.dict_set['최적화기준값제한'],
                        optistd, ui.back_count, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday
                    ))
                    gubun = 'S'
                else:
                    ui.backQ.put((
                        betting, starttime, endtime, buystg, sellstg, optivars, None, ui.dict_set['최적화기준값제한'],
                        optistd, ui.back_count, weeks_train, weeks_valid, weeks_test, benginesday, benginesday
                    ))
                    gubun = 'C' if ui.dict_set['거래소'] == '업비트' else 'CF'

                if back_name == 'GA 최적화':
                    ui.proc_backtester_og = Process(
                        target=OptimizeGeneticAlgorithm,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.back_eques, ui.back_sques, '최적화OG', gubun)
                    )
                    ui.proc_backtester_og.start()
                elif back_name == '검증 GA 최적화':
                    ui.proc_backtester_ogv = Process(
                        target=OptimizeGeneticAlgorithm,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.back_eques, ui.back_sques, '최적화OGV', gubun)
                    )
                    ui.proc_backtester_ogv.start()
                elif back_name == '교차검증 GA 최적화':
                    ui.proc_backtester_ogvc = Process(
                        target=OptimizeGeneticAlgorithm,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.back_eques, ui.back_sques, '최적화OGVC', gubun)
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

                for q in ui.back_eques:
                    q.put(('백테유형', '전진분석'))

                if bt_gubun == '주식':
                    ui.backQ.put((
                        betting, startday, endday, starttime, endtime, buystg, sellstg, optivars, ui.dict_cn,
                        ccount, ui.dict_set['최적화기준값제한'], optistd, ui.back_count, True, ui.df_kp,
                        ui.df_kd, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday, optunasampl,
                        optunafixv, optunacount, optunaautos, False
                    ))
                    gubun = 'S'
                else:
                    ui.backQ.put((
                        betting, startday, endday, starttime, endtime, buystg, sellstg, optivars, None, ccount,
                        ui.dict_set['최적화기준값제한'], optistd, ui.back_count, True, None, None, weeks_train,
                        weeks_valid, weeks_test, benginesday, bengineeday, optunasampl, optunafixv, optunacount,
                        optunaautos, False
                    ))
                    gubun = 'C' if ui.dict_set['거래소'] == '업비트' else 'CF'

                if back_name == '그리드 최적화 전진분석':
                    ui.proc_backtester_or = Process(
                        target=RollingWalkForwardTest,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '전진분석OR', gubun)
                    )
                    ui.proc_backtester_or.start()
                elif back_name == '그리드 검증 최적화 전진분석':
                    ui.proc_backtester_orv = Process(
                        target=RollingWalkForwardTest,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '전진분석ORV', gubun)
                    )
                    ui.proc_backtester_orv.start()
                elif back_name == '그리드 교차검증 최적화 전진분석':
                    ui.proc_backtester_orvc = Process(
                        target=RollingWalkForwardTest,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '전진분석ORVC', gubun)
                    )
                    ui.proc_backtester_orvc.start()
                elif back_name == '베이지안 최적화 전진분석':
                    ui.proc_backtester_br = Process(
                        target=RollingWalkForwardTest,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '전진분석BR', gubun)
                    )
                    ui.proc_backtester_br.start()
                elif back_name == '베이지안 검증 최적화 전진분석':
                    ui.proc_backtester_brv = Process(
                        target=RollingWalkForwardTest,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '전진분석BRV', gubun)
                    )
                    ui.proc_backtester_brv.start()
                elif back_name == '베이지안 교차검증 최적화 전진분석':
                    ui.proc_backtester_brvc = Process(
                        target=RollingWalkForwardTest,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '전진분석BRVC', gubun)
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

                for q in ui.back_eques:
                    q.put(('백테유형', '최적화'))

                if bt_gubun == '주식':
                    ui.backQ.put((
                        betting, starttime, endtime, buystg, sellstg, optivars, ui.dict_cn, ccount,
                        ui.dict_set['최적화기준값제한'], optistd, ui.back_count, True, ui.df_kp, ui.df_kd,
                        weeks_train, weeks_valid, weeks_test, benginesday, bengineeday, optunasampl, optunafixv,
                        optunacount, optunaautos, False, False, False
                    ))
                    gubun = 'S'
                else:
                    ui.backQ.put((
                        betting, starttime, endtime, buystg, sellstg, optivars, None, ccount,
                        ui.dict_set['최적화기준값제한'], optistd, ui.back_count, True, None, None, weeks_train,
                        weeks_valid, weeks_test, benginesday, bengineeday, optunasampl, optunafixv, optunacount,
                        optunaautos, False, False, False
                    ))
                    gubun = 'C' if ui.dict_set['거래소'] == '업비트' else 'CF'

                if back_name == '그리드 최적화':
                    ui.proc_backtester_o = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화O', gubun)
                    )
                    ui.proc_backtester_o.start()
                elif back_name == '그리드 검증 최적화':
                    ui.proc_backtester_ov = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화OV', gubun)
                    )
                    ui.proc_backtester_ov.start()
                elif back_name == '그리드 교차검증 최적화':
                    ui.proc_backtester_ovc = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화OVC', gubun)
                    )
                    ui.proc_backtester_ovc.start()
                elif back_name == '베이지안 최적화':
                    ui.proc_backtester_b = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화B', gubun)
                    )
                    ui.proc_backtester_b.start()
                elif back_name == '베이지안 검증 최적화':
                    ui.proc_backtester_bv = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화BV', gubun)
                    )
                    ui.proc_backtester_bv.start()
                elif back_name == '베이지안 교차검증 최적화':
                    ui.proc_backtester_bvc = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화BVC', gubun)
                    )
                    ui.proc_backtester_bvc.start()
                elif back_name == '그리드 최적화 테스트':
                    ui.proc_backtester_ot = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화OT', gubun)
                    )
                    ui.proc_backtester_ot.start()
                elif back_name == '그리드 검증 최적화 테스트':
                    ui.proc_backtester_ovt = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화OVT', gubun)
                    )
                    ui.proc_backtester_ovt.start()
                elif back_name == '그리드 교차검증 최적화 테스트':
                    ui.proc_backtester_ovct = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화OVCT', gubun)
                    )
                    ui.proc_backtester_ovct.start()
                elif back_name == '베이지안 최적화 테스트':
                    ui.proc_backtester_bt = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화BT', gubun)
                    )
                    ui.proc_backtester_bt.start()
                elif back_name == '베이지안 검증 최적화 테스트':
                    ui.proc_backtester_bvt = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화BVT', gubun)
                    )
                    ui.proc_backtester_bvt.start()
                elif back_name == '베이지안 교차검증 최적화 테스트':
                    ui.proc_backtester_bvct = Process(
                        target=Optimize,
                        args=(ui.windowQ, ui.backQ, ui.soundQ, ui.totalQ, ui.liveQ, ui.teleQ, ui.back_eques, ui.back_sques,
                              ui.multi, ui.divid_mode, '최적화BVCT', gubun)
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
            ui.windowQ.put((log_target_initial,
                f'<font color=#ff0000>[TRACE] back_scount >= 16 ({ui.back_scount}) - 스케줄러 중지</font>'))
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


def sdbutton_clicked_05(ui):
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
        if ui.proc_query.is_alive():
            ui.queryQ.put(('전략디비', f"DELETE FROM schedule WHERE `index` = '{schedule_name}'"))
            df = pd.DataFrame({'스케쥴': [schedule]}, index=[schedule_name])
            ui.queryQ.put(('전략디비', df, 'schedule', 'append'))
        QMessageBox.information(ui.dialog_scheduler, '저장 완료', random.choice(famous_saying))
