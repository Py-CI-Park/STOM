import os
import re
import sqlite3
import binance
import numpy as np
import pandas as pd
from multiprocessing import Process, Queue, Lock, shared_memory
from backtester.back_code_test import BackCodeTest
from backtester.back_static import GetMoneytopQuery
from backtester.backengine_coin_future import CoinFutureBackEngine
from backtester.backengine_coin_future2 import CoinFutureBackEngine2
from backtester.backengine_coin_upbit import CoinUpbitBackEngine
from backtester.backengine_coin_upbit2 import CoinUpbitBackEngine2
from backtester.backengine_stock import StockBackEngine
from backtester.backengine_stock2 import StockBackEngine2
from backtester.back_subtotal import BackSubTotal
from ui.set_style import style_bc_dk
from utility.static import thread_decorator, qtest_qwait
from utility.setting import DB_STOCK_BACK, DB_COIN_BACK, ui_num, BACK_TEMP


def backengine_show(ui, gubun):
    table_list = []
    BACK_FILE = DB_STOCK_BACK if gubun == '주식' else DB_COIN_BACK
    con = sqlite3.connect(BACK_FILE)
    try:
        df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        table_list = df['name'].to_list()
        table_list.remove('codename')
        table_list.remove('moneytop')
    except:
        pass
    con.close()
    if table_list:
        name_list = [ui.dict_name[code] if code in ui.dict_name.keys() else code for code in table_list]
        name_list.sort()
        ui.be_comboBoxxxxx_02.clear()
        for name in name_list:
            ui.be_comboBoxxxxx_02.addItem(name)
    ui.be_lineEdittttt_01.setText('90000' if gubun == '주식' else '0')
    ui.be_lineEdittttt_02.setText('93000' if gubun == '주식' else '235959')
    if not ui.backengin_window_open:
        ui.be_comboBoxxxxx_01.setCurrentText(ui.dict_set['백테엔진분류방법'])
    ui.dialog_backengine.show()
    ui.backengin_window_open = True


@thread_decorator
def start_backengine(ui, gubun):
    ui.back_engining = True
    ui.startday   = int(ui.be_dateEdittttt_01.date().toString('yyyyMMdd'))
    ui.endday     = int(ui.be_dateEdittttt_02.date().toString('yyyyMMdd'))
    ui.starttime  = int(ui.be_lineEdittttt_01.text())
    ui.endtime    = int(ui.be_lineEdittttt_02.text())
    ui.avg_list   = [int(x) for x in ui.be_lineEdittttt_03.text().split(',')]
    multi         = int(ui.be_lineEdittttt_04.text())
    divid_mode    = ui.be_comboBoxxxxx_01.currentText()
    one_name      = ui.be_comboBoxxxxx_02.currentText()
    one_code      = ui.dict_code[one_name] if one_name in ui.dict_code.keys() else one_name
    ui.multi      = multi
    ui.divid_mode = divid_mode

    for i in range(20):
        bctq = Queue()
        ui.back_sques.append(bctq)
    for i in range(20):
        proc = Process(target=BackSubTotal, args=(i, ui.totalQ, ui.back_sques, ui.dict_set['백테매수시간기준']), daemon=True)
        proc.start()
        ui.back_sprocs.append(proc)
        ui.windowQ.put((ui_num['백테엔진'], f'중간집계용 프로세스{i + 1} 생성 완료'))

    lock = Lock()
    for i in range(multi):
        beq = Queue()
        if gubun == '주식':
            if not ui.dict_set['백테주문관리적용']:
                if i == 0 and ui.dict_set['백테엔진프로파일링']:
                    proc = Process(
                        target=StockBackEngine,
                        args=(i, ui.windowQ, ui.totalQ, ui.backQ, beq, ui.back_sques, lock, True),
                        daemon=True
                    )
                else:
                    proc = Process(
                        target=StockBackEngine,
                        args=(i, ui.windowQ, ui.totalQ, ui.backQ, beq, ui.back_sques, lock),
                        daemon=True
                    )
            else:
                if i == 0 and ui.dict_set['백테엔진프로파일링']:
                    proc = Process(
                        target=StockBackEngine2,
                        args=(i, ui.windowQ, ui.totalQ, ui.backQ, beq, ui.back_sques, lock, True),
                        daemon=True
                    )
                else:
                    proc = Process(
                        target=StockBackEngine2,
                        args=(i, ui.windowQ, ui.totalQ, ui.backQ, beq, ui.back_sques, lock),
                        daemon=True
                    )
        else:
            if not ui.dict_set['백테주문관리적용']:
                if i == 0 and ui.dict_set['백테엔진프로파일링']:
                    proc = Process(
                        target=CoinUpbitBackEngine if ui.dict_set['거래소'] == '업비트' else CoinFutureBackEngine,
                        args=(i, ui.windowQ, ui.totalQ, ui.backQ, beq, ui.back_sques, lock, True),
                        daemon=True
                    )
                else:
                    proc = Process(
                        target=CoinUpbitBackEngine if ui.dict_set['거래소'] == '업비트' else CoinFutureBackEngine,
                        args=(i, ui.windowQ, ui.totalQ, ui.backQ, beq, ui.back_sques, lock),
                        daemon=True
                    )
            else:
                if i == 0 and ui.dict_set['백테엔진프로파일링']:
                    proc = Process(
                        target=CoinUpbitBackEngine2 if ui.dict_set['거래소'] == '업비트' else CoinFutureBackEngine2,
                        args=(i, ui.windowQ, ui.totalQ, ui.backQ, beq, ui.back_sques, lock, True),
                        daemon=True
                    )
                else:
                    proc = Process(
                        target=CoinUpbitBackEngine2 if ui.dict_set['거래소'] == '업비트' else CoinFutureBackEngine2,
                        args=(i, ui.windowQ, ui.totalQ, ui.backQ, beq, ui.back_sques, lock),
                        daemon=True
                    )
        proc.start()
        ui.back_eques.append(beq)
        ui.back_eprocs.append(proc)
        ui.windowQ.put((ui_num['백테엔진'], f'연산용 프로세스{i + 1} 생성 완료'))

    if gubun == '주식':
        ui.webcQ.put(('지수차트', ui.startday))
        ui.df_kp, ui.df_kd = ui.backQ.get()

    if not ui.dict_set['백테일괄로딩']:
        file_list = os.listdir(BACK_TEMP)
        for file in file_list:
            os.remove(f'{BACK_TEMP}/{file}')
        ui.windowQ.put((ui_num['백테엔진'], '이전 임시파일 삭제 완료'))

    dict_kd = None
    try:
        con = sqlite3.connect(DB_STOCK_BACK) if gubun == '주식' else sqlite3.connect(DB_COIN_BACK)
        if gubun == '주식':
            df_cn = pd.read_sql('SELECT * FROM codename', con).set_index('index')
            ui.dict_cn = df_cn['종목명'].to_dict()
            dict_kd = df_cn['코스닥'].to_dict()
        elif ui.dict_set['거래소'] == '바이낸스선물':
            binan = binance.Client()
            datas = binan.futures_exchange_info()
            datas = [x for x in datas['symbols'] if re.search('USDT$', x['symbol']) is not None]
            dict_kd = {x['symbol']: float(x['filters'][0]['tickSize']) for x in datas}
        gubun_ = 'S' if gubun == '주식' else 'CF' if gubun == '코인' and ui.dict_set['거래소'] == '바이낸스선물' else 'C'
        query = GetMoneytopQuery(gubun_, ui.startday, ui.endday, ui.starttime, ui.endtime)
        df_mt = pd.read_sql(query, con)
        con.close()
        df_mt['일자'] = df_mt['index'].apply(lambda x: int(str(x)[:8]))
        df_mt.set_index('index', inplace=True)
    except:
        if gubun == '주식':
            if ui.dict_cn is None:
                ui.windowQ.put((ui_num['백테엔진'], '백테디비에 데이터가 존재하지 않습니다. 디비관리창(Alt + D)에서 백테디비를 생성하십시오.'))
            elif len(ui.dict_cn) < 100:
                ui.windowQ.put((ui_num['백테엔진'], '종목명 테이블이 갱신되지 않았습니다. 수동로그인(Alt + S)을 1회 실행하시오.'))
            elif dict_kd is None:
                ui.windowQ.put((ui_num['백테엔진'], '종목명 테이블에 코스닥 구분 칼럼이 존재하지 않습니다. 수동로그인(Alt + S)을 1회 실행하시오.'))
            else:
                ui.windowQ.put((ui_num['백테엔진'], '백테디비에 데이터가 존재하지 않습니다. 디비관리창(Alt + D)에서 백테디비를 생성하십시오.'))
        else:
            ui.windowQ.put((ui_num['백테엔진'], '백테디비에 데이터가 존재하지 않습니다. 디비관리창(Alt + D)에서 백테디비를 생성하십시오.'))
        ui.BacktestEngineKill()
        return

    if df_mt is None or df_mt.empty:
        ui.windowQ.put((ui_num['백테엔진'], '시작 또는 종료일자가 잘못 선택되었거나 해당 일자에 데이터가 존재하지 않습니다.'))
        ui.BacktestEngineKill()
        return

    ui.dict_mt = df_mt['거래대금순위'].to_dict()
    day_list = list(set(df_mt['일자'].to_list()))
    table_list = list(set(';'.join(list(ui.dict_mt.values())).split(';')))

    day_codes = {}
    for day in day_list:
        df_mt_ = df_mt[df_mt['일자'] == day]
        day_codes[day] = list(set(';'.join(df_mt_['거래대금순위'].to_list()).split(';')))

    code_days = {}
    for code in table_list:
        code_days[code] = [day for day, codes in day_codes.items() if code in codes]

    if divid_mode == '종목코드별 분류' and len(code_days) < multi:
        ui.windowQ.put((ui_num['백테엔진'], '선택한 일자의 종목의 개수가 멀티수보다 작습니다. 일자를 늘리십시오.'))
        ui.BacktestEngineKill()
        return

    if divid_mode == '일자별 분류' and len(day_codes) < multi:
        ui.windowQ.put((ui_num['백테엔진'], '선택한 일자의 수가 멀티수보다 작습니다. 일자를 늘리십시오.'))
        ui.BacktestEngineKill()
        return

    if divid_mode == '한종목 로딩' and one_code not in code_days.keys():
        ui.windowQ.put((ui_num['백테엔진'], f'{one_name} 종목은 선택한 일자에 데이터가 존재하지 않습니다.'))
        ui.BacktestEngineKill()
        return

    if divid_mode == '한종목 로딩' and len(code_days[one_code]) < multi:
        ui.windowQ.put((ui_num['백테엔진'], f'{one_name} 선택한 종목의 일자의 수가 멀티수보다 작습니다. 일자를 늘리십시오.'))
        ui.BacktestEngineKill()
        return

    ui.wdzservQ.put(('manager', '백테엔진구동'))

    for i in range(multi):
        if gubun == '주식':
            ui.back_eques[i].put(('종목명', ui.dict_cn, dict_kd))
        elif ui.dict_set['거래소'] == '바이낸스선물':
            ui.back_eques[i].put(('호가단위', dict_kd))
    ui.windowQ.put((ui_num['백테엔진'], '거래대금순위 및 종목코드 추출 완료'))

    if divid_mode == '종목코드별 분류':
        ui.windowQ.put((ui_num['백테엔진'], '데이터 로딩 시작'))
        code_lists = []
        for i in range(multi):
            code_lists.append([code for j, code in enumerate(table_list) if j % multi == i])
        for i, codes in enumerate(code_lists):
            ui.back_eques[i].put(('데이터로딩', ui.startday, ui.endday, ui.starttime, ui.endtime, codes, ui.avg_list,
                                  code_days, day_codes, divid_mode, one_code))

    elif divid_mode == '일자별 분류':
        ui.windowQ.put((ui_num['백테엔진'], '데이터 로딩 시작'))
        day_lists = []
        for i in range(multi):
            day_lists.append([day for j, day in enumerate(day_list) if j % multi == i])
        for i, days in enumerate(day_lists):
            ui.back_eques[i].put(('데이터로딩', ui.startday, ui.endday, ui.starttime, ui.endtime, days, ui.avg_list,
                                  code_days, day_codes, divid_mode, one_code))
    else:
        ui.windowQ.put((ui_num['백테엔진'], f'데이터 로딩시작'))
        day_list = code_days[one_code]
        day_lists = []
        for i in range(multi):
            day_lists.append([day for j, day in enumerate(day_list) if j % multi == i])
        for i, days in enumerate(day_lists):
            ui.back_eques[i].put(('데이터로딩', ui.startday, ui.endday, ui.starttime, ui.endtime, days, ui.avg_list,
                                  code_days, day_codes, divid_mode, one_code))

    i = 0
    if ui.dict_set['백테일괄로딩']:
        df = pd.DataFrame(columns=['len_df', 'code', 'name', 'shape'])
    else:
        df = pd.DataFrame(columns=['len_df', 'code', 'name'])
    while True:
        try:
            data = ui.backQ.get()
        except:
            pass
        else:
            if data == '로딩완료':
                i += 1
                ui.windowQ.put((ui_num['백테엔진'], f'데이터 로딩 중 ... [{i}/{multi}]'))
                if i == multi:
                    break
            else:
                ui.back_count += 1
                df.loc[data[3]] = data[1:]
                if data[0] is not None:
                    ui.back_shm_list.append(data[0])

    df.sort_values(by=['len_df'], ascending=False, inplace=True)
    df.drop(columns=['len_df'], inplace=True)
    shm_list = list(df.values)

    arry = np.array([0, len(shm_list)])
    shm = shared_memory.SharedMemory(name='back_sequence', create=True, size=arry.nbytes)
    shm_arry = np.ndarray(arry.shape, dtype=arry.dtype, buffer=shm.buf)
    shm_arry[:] = arry[:]
    ui.back_shm_list.append(shm)

    for q in ui.back_eques:
        q.put(('백테데이터', shm_list))

    ui.back_engining = False
    ui.backtest_engine = True
    ui.windowQ.put((ui_num['백테엔진'], '백테엔진 준비 완료'))


def back_code_test1(stg_code, testQ):
    print('전략 코드 오류 테스트 시작')
    while not testQ.empty():
        testQ.get()
    Process(target=BackCodeTest, args=(testQ, stg_code), daemon=True).start()
    return back_code_test_wait('전략', testQ)


def back_code_test2(vars_code, testQ, ga):
    print('범위 코드 오류 테스트 시작')
    while not testQ.empty():
        testQ.get()
    Process(target=BackCodeTest, args=(testQ, '', vars_code, ga), daemon=True).start()
    return back_code_test_wait('범위', testQ)


def back_code_test3(gubun, conds_code, testQ):
    print('조건 코드 오류 테스트 시작')
    while not testQ.empty():
        testQ.get()
    conds_code = conds_code.split('\n')
    conds_code = [x for x in conds_code if x != '' and '#' not in x]
    if gubun == '매수':
        conds_code = 'if ' + ':\n    매수 = False\nelif '.join(conds_code) + ':\n    매수 = False'
    else:
        conds_code = 'if ' + ':\n    매도 = True\nelif '.join(conds_code) + ':\n    매도 = True'
    Process(target=BackCodeTest, args=(testQ, conds_code), daemon=True).start()
    return back_code_test_wait('조건', testQ)


def back_code_test_wait(gubun, testQ):
    data = testQ.get()
    if data == '전략테스트오류':
        print(f'{gubun}에 오류가 있어 저장하지 못하였습니다.')
        return False
    else:
        print(f'{gubun} 코드 오류 테스트 완료')
        return True


def clear_backtestQ(ui):
    if not ui.backQ.empty():
        while not ui.backQ.empty():
            ui.backQ.get()
    if not ui.totalQ.empty():
        while not ui.totalQ.empty():
            ui.totalQ.get()


def backtest_process_kill(ui, gubun):
    ui.back_cancelling = True
    ui.totalQ.put('백테중지')
    qtest_qwait(3)
    if ui.proc_backtester_bs is not None and ui.proc_backtester_bs.is_alive():   ui.proc_backtester_bs.kill()
    if ui.proc_backtester_bf is not None and ui.proc_backtester_bf.is_alive():   ui.proc_backtester_bf.kill()
    if ui.proc_backtester_bc is not None and ui.proc_backtester_bc.is_alive():   ui.proc_backtester_bc.kill()
    if ui.proc_backtester_bp is not None and ui.proc_backtester_bp.is_alive():   ui.proc_backtester_bp.kill()
    if ui.proc_backtester_o is not None and ui.proc_backtester_o.is_alive():    ui.proc_backtester_o.kill()
    if ui.proc_backtester_ov is not None and ui.proc_backtester_ov.is_alive():   ui.proc_backtester_ov.kill()
    if ui.proc_backtester_ovc is not None and ui.proc_backtester_ovc.is_alive():  ui.proc_backtester_ovc.kill()
    if ui.proc_backtester_ot is not None and ui.proc_backtester_ot.is_alive():   ui.proc_backtester_ot.kill()
    if ui.proc_backtester_ovt is not None and ui.proc_backtester_ovt.is_alive():  ui.proc_backtester_ovt.kill()
    if ui.proc_backtester_ovct is not None and ui.proc_backtester_ovct.is_alive(): ui.proc_backtester_ovct.kill()
    if ui.proc_backtester_oc is not None and ui.proc_backtester_oc.is_alive():   ui.proc_backtester_oc.kill()
    if ui.proc_backtester_ocv is not None and ui.proc_backtester_ocv.is_alive():  ui.proc_backtester_ocv.kill()
    if ui.proc_backtester_ocvc is not None and ui.proc_backtester_ocvc.is_alive(): ui.proc_backtester_ocvc.kill()
    if ui.proc_backtester_og is not None and ui.proc_backtester_og.is_alive():   ui.proc_backtester_og.kill()
    if ui.proc_backtester_ogv is not None and ui.proc_backtester_ogv.is_alive():  ui.proc_backtester_ogv.kill()
    if ui.proc_backtester_ogvc is not None and ui.proc_backtester_ogvc.is_alive(): ui.proc_backtester_ogvc.kill()
    if ui.proc_backtester_or is not None and ui.proc_backtester_or.is_alive():   ui.proc_backtester_or.kill()
    if ui.proc_backtester_orv is not None and ui.proc_backtester_orv.is_alive():  ui.proc_backtester_orv.kill()
    if ui.proc_backtester_orvc is not None and ui.proc_backtester_orvc.is_alive(): ui.proc_backtester_orvc.kill()
    if ui.proc_backtester_b is not None and ui.proc_backtester_b.is_alive():    ui.proc_backtester_b.kill()
    if ui.proc_backtester_bv is not None and ui.proc_backtester_bv.is_alive():   ui.proc_backtester_bv.kill()
    if ui.proc_backtester_bvc is not None and ui.proc_backtester_bvc.is_alive():  ui.proc_backtester_bvc.kill()
    if ui.proc_backtester_bt is not None and ui.proc_backtester_bt.is_alive():   ui.proc_backtester_bt.kill()
    if ui.proc_backtester_bvt is not None and ui.proc_backtester_bvt.is_alive():  ui.proc_backtester_bvt.kill()
    if ui.proc_backtester_bvct is not None and ui.proc_backtester_bvct.is_alive(): ui.proc_backtester_bvct.kill()
    if ui.proc_backtester_br is not None and ui.proc_backtester_br.is_alive():   ui.proc_backtester_br.kill()
    if ui.proc_backtester_brv is not None and ui.proc_backtester_brv.is_alive():  ui.proc_backtester_brv.kill()
    if ui.proc_backtester_brvc is not None and ui.proc_backtester_brvc.is_alive(): ui.proc_backtester_brvc.kill()
    if ui.main_btn == 2:
        ui.ss_pushButtonn_08.setStyleSheet(style_bc_dk)
    elif ui.main_btn == 3:
        ui.cs_pushButtonn_08.setStyleSheet(style_bc_dk)
    if gubun: ui.BacktestEngineKill()
    ui.back_cancelling = False
