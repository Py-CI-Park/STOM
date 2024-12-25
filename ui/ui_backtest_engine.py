import os
import re
import sqlite3
import binance
import operator
import pandas as pd
from multiprocessing import Process, Queue
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
from utility.setting import DB_STOCK_BACK, DB_COIN_BACK, ui_num, BACK_TEMP
from utility.static import thread_decorator, timedelta_sec, now, qtest_qwait


def backtest_engine_show(ui, gubun):
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
def start_backtest_engine(ui, gubun, windowQ, wdzservQ, backQ, totalQ, webcQ):
    ui.backtest_engine = True
    ui.startday  = int(ui.be_dateEdittttt_01.date().toString('yyyyMMdd'))
    ui.endday    = int(ui.be_dateEdittttt_02.date().toString('yyyyMMdd'))
    ui.starttime = int(ui.be_lineEdittttt_01.text())
    ui.endtime   = int(ui.be_lineEdittttt_02.text())
    ui.avg_list  = [int(x) for x in ui.be_lineEdittttt_03.text().split(',')]
    multi          = int(ui.be_lineEdittttt_04.text())
    divid_mode     = ui.be_comboBoxxxxx_01.currentText()
    one_name       = ui.be_comboBoxxxxx_02.currentText()
    one_code       = ui.dict_code[one_name] if one_name in ui.dict_code.keys() else one_name

    wdzservQ.put(('manager', '백테엔진구동'))
    for i in range(20):
        bctq = Queue()
        ui.back_cques.append(bctq)
    for i in range(20):
        proc = Process(target=BackSubTotal, args=(i, totalQ, ui.back_cques, ui.dict_set['백테매수시간기준']), daemon=True)
        proc.start()
        ui.back_cprocs.append(proc)
        windowQ.put((ui_num['백테엔진'], f'중간집계용 프로세스{i + 1} 생성 완료'))

    for i in range(multi):
        bpq = Queue()
        if gubun == '주식':
            if not ui.dict_set['백테주문관리적용']:
                if i == 0 and ui.dict_set['백테엔진프로파일링']:
                    proc = Process(target=StockBackEngine, args=(i, windowQ, bpq, totalQ, backQ, ui.back_cques, True), daemon=True)
                else:
                    proc = Process(target=StockBackEngine, args=(i, windowQ, bpq, totalQ, backQ, ui.back_cques), daemon=True)
            else:
                if i == 0 and ui.dict_set['백테엔진프로파일링']:
                    proc = Process(target=StockBackEngine2, args=(i, windowQ, bpq, totalQ, backQ, ui.back_cques, True), daemon=True)
                else:
                    proc = Process(target=StockBackEngine2, args=(i, windowQ, bpq, totalQ, backQ, ui.back_cques), daemon=True)
        else:
            if not ui.dict_set['백테주문관리적용']:
                if i == 0 and ui.dict_set['백테엔진프로파일링']:
                    proc = Process(target=CoinUpbitBackEngine if ui.dict_set['거래소'] == '업비트' else CoinFutureBackEngine, args=(i, windowQ, bpq, totalQ, backQ, ui.back_cques, True), daemon=True)
                else:
                    proc = Process(target=CoinUpbitBackEngine if ui.dict_set['거래소'] == '업비트' else CoinFutureBackEngine, args=(i, windowQ, bpq, totalQ, backQ, ui.back_cques), daemon=True)
            else:
                if i == 0 and ui.dict_set['백테엔진프로파일링']:
                    proc = Process(target=CoinUpbitBackEngine2 if ui.dict_set['거래소'] == '업비트' else CoinFutureBackEngine2, args=(i, windowQ, bpq, totalQ, backQ, ui.back_cques, True), daemon=True)
                else:
                    proc = Process(target=CoinUpbitBackEngine2 if ui.dict_set['거래소'] == '업비트' else CoinFutureBackEngine2, args=(i, windowQ, bpq, totalQ, backQ, ui.back_cques), daemon=True)
        proc.start()
        ui.back_eprocs.append(proc)
        ui.back_eques.append(bpq)
        windowQ.put((ui_num['백테엔진'], f'연산용 프로세스{i + 1} 생성 완료'))

    if gubun == '주식':
        webcQ.put(('지수차트', ui.startday))
        ui.df_kp, ui.df_kd = backQ.get()

    if not ui.dict_set['백테일괄로딩']:
        file_list = os.listdir(BACK_TEMP)
        for file in file_list:
            os.remove(f'{BACK_TEMP}/{file}')
        windowQ.put((ui_num['백테엔진'], '이전 임시파일 삭제 완료'))

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
                windowQ.put((ui_num['백테엔진'], '백테디비에 데이터가 존재하지 않습니다. 디비관리창(Alt + D)에서 백테디비를 생성하십시오.'))
            elif len(ui.dict_cn) < 100:
                windowQ.put((ui_num['백테엔진'], '종목명 테이블이 갱신되지 않았습니다. 수동로그인(Alt + S)을 1회 실행하시오.'))
            elif dict_kd is None:
                windowQ.put((ui_num['백테엔진'], '종목명 테이블에 코스닥 구분 칼럼이 존재하지 않습니다. 수동로그인(Alt + S)을 1회 실행하시오.'))
            else:
                windowQ.put((ui_num['백테엔진'], '백테디비에 데이터가 존재하지 않습니다. 디비관리창(Alt + D)에서 백테디비를 생성하십시오.'))
        else:
            windowQ.put((ui_num['백테엔진'], '백테디비에 데이터가 존재하지 않습니다. 디비관리창(Alt + D)에서 백테디비를 생성하십시오.'))
        ui.BacktestEngineKill()
        return

    if df_mt is None or df_mt.empty:
        windowQ.put((ui_num['백테엔진'], '시작 또는 종료일자가 잘못 선택되었거나 해당 일자에 데이터가 존재하지 않습니다.'))
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
        windowQ.put((ui_num['백테엔진'], '선택한 일자의 종목의 개수가 멀티수보다 작습니다. 일자를 늘리십시오.'))
        ui.BacktestEngineKill()
        return

    if divid_mode == '일자별 분류' and len(day_codes) < multi:
        windowQ.put((ui_num['백테엔진'], '선택한 일자의 수가 멀티수보다 작습니다. 일자를 늘리십시오.'))
        ui.BacktestEngineKill()
        return

    if divid_mode == '한종목 로딩' and one_code not in code_days.keys():
        windowQ.put((ui_num['백테엔진'], f'{one_name} 종목은 선택한 일자에 데이터가 존재하지 않습니다.'))
        ui.BacktestEngineKill()
        return

    if divid_mode == '한종목 로딩' and len(code_days[one_code]) < multi:
        windowQ.put((ui_num['백테엔진'], f'{one_name} 선택한 종목의 일자의 수가 멀티수보다 작습니다. 일자를 늘리십시오.'))
        ui.BacktestEngineKill()
        return

    for i in range(multi):
        if gubun == '주식':
            ui.back_eques[i].put(('종목명', ui.dict_cn, dict_kd))
        elif ui.dict_set['거래소'] == '바이낸스선물':
            ui.back_eques[i].put(('호가단위', dict_kd))
    windowQ.put((ui_num['백테엔진'], '거래대금순위 및 종목코드 추출 완료'))

    if divid_mode == '종목코드별 분류':
        windowQ.put((ui_num['백테엔진'], '종목별 데이터 크기 추출 시작'))
        code_lists = []
        for i in range(multi):
            code_lists.append([code for j, code in enumerate(table_list) if j % multi == i])
        for i, codes in enumerate(code_lists):
            ui.back_eques[i].put(('데이터크기', ui.startday, ui.endday, ui.starttime, ui.endtime, codes, ui.avg_list, code_days, day_codes, divid_mode, one_code))

        dict_lendf = {}
        last = len(table_list)
        for i in range(last):
            data = backQ.get()
            if data[1] != 0:
                dict_lendf[data[0]] = data[1]
            if (i + 1) % 100 == 0:
                windowQ.put((ui_num['백테엔진'], f'종목별 데이터 크기 추출 중 ... [{i + 1}/{last}]'))
        windowQ.put((ui_num['백테엔진'], '종목별 데이터 크기 추출 완료'))

        code_lists  = [[] for _ in range(multi)]
        total_list  = [0 for _ in range(multi)]
        add_count   = 0
        multi_num   = 0
        reverse     = False
        divid_lendf = int(sum(dict_lendf.values()) / multi)
        sort_lendf  = sorted(dict_lendf.items(), key=operator.itemgetter(1), reverse=True)
        for code, lendf in sort_lendf:
            code_lists[multi_num].append(code)
            total_list[multi_num] += lendf
            while True:
                add_count += 1
                if add_count % multi == 0:
                    if reverse:
                        reverse   = False
                        multi_num = 0
                    else:
                        reverse   = True
                        multi_num = multi - 1
                else:
                    if reverse:
                        multi_num -= 1
                    else:
                        multi_num += 1
                if total_list[multi_num] < divid_lendf:
                    break

        windowQ.put((ui_num['백테엔진'], '종목코드별 분류 완료'))
        for i, codes in enumerate(code_lists):
            ui.back_eques[i].put(('데이터로딩', ui.startday, ui.endday, ui.starttime, ui.endtime, codes, ui.avg_list, code_days, day_codes, divid_mode, one_code))

    elif divid_mode == '일자별 분류':
        windowQ.put((ui_num['백테엔진'], '일자별 데이터 크기 추출 시작'))
        day_lists = []
        for i in range(multi):
            day_lists.append([day for j, day in enumerate(day_list) if j % multi == i])
        for i, days in enumerate(day_lists):
            ui.back_eques[i].put(('데이터크기', ui.startday, ui.endday, ui.starttime, ui.endtime, days, ui.avg_list, code_days, day_codes, divid_mode, one_code))

        dict_lendf = {}
        last = len(day_list)
        for i in range(last):
            data = backQ.get()
            if data[1] != 0:
                dict_lendf[data[0]] = data[1]
            if (i + 1) % 10 == 0:
                windowQ.put((ui_num['백테엔진'], f'일자별 데이터 크기 추출 중 ... [{i + 1}/{last}]'))
        windowQ.put((ui_num['백테엔진'], '일자별 데이터 크기 추출 완료'))

        day_lists  = []
        total_list = []
        for _ in range(multi):
            day_lists.append([])
            total_list.append(0)

        add_count   = 0
        multi_num   = 0
        reverse     = False
        divid_lendf = int(sum(dict_lendf.values()) / multi)
        sort_lendf  = sorted(dict_lendf.items(), key=operator.itemgetter(1), reverse=True)
        for day, lendf in sort_lendf:
            day_lists[multi_num].append(day)
            total_list[multi_num] += lendf
            while True:
                add_count += 1
                if add_count % multi == 0:
                    if reverse:
                        reverse   = False
                        multi_num = 0
                    else:
                        reverse   = True
                        multi_num = multi - 1
                else:
                    if reverse:
                        multi_num -= 1
                    else:
                        multi_num += 1
                if total_list[multi_num] < divid_lendf:
                    break

        windowQ.put((ui_num['백테엔진'], '일자별 분류 완료'))
        for i, days in enumerate(day_lists):
            ui.back_eques[i].put(('데이터로딩', ui.startday, ui.endday, ui.starttime, ui.endtime, days, ui.avg_list, code_days, day_codes, divid_mode, one_code))
    else:
        windowQ.put((ui_num['백테엔진'], f'{one_code} 일자별 데이터 크기 추출 시작'))
        day_list = code_days[one_code]
        day_lists = []
        for i in range(multi):
            day_lists.append([day for j, day in enumerate(day_list) if j % multi == i])
        for i, days in enumerate(day_lists):
            ui.back_eques[i].put(('데이터크기', ui.startday, ui.endday, ui.starttime, ui.endtime, days, ui.avg_list, code_days, day_codes, divid_mode, one_code))

        dict_lendf = {}
        last = len(day_list)
        for i in range(last):
            data = backQ.get()
            if data[1] != 0:
                dict_lendf[data[0]] = data[1]
            if (i + 1) % 10 == 0:
                windowQ.put((ui_num['백테엔진'], f'{one_code} 일자별 데이터 크기 추출 중 ... [{i + 1}/{last}]'))
        windowQ.put((ui_num['백테엔진'], f'{one_code} 일자별 데이터 크기 추출 완료'))

        day_lists  = []
        total_list = []
        for _ in range(multi):
            day_lists.append([])
            total_list.append(0)

        add_count   = 0
        multi_num   = 0
        reverse     = False
        divid_lendf = int(sum(dict_lendf.values()) / multi)
        sort_lendf  = sorted(dict_lendf.items(), key=operator.itemgetter(1), reverse=True)
        for day, lendf in sort_lendf:
            day_lists[multi_num].append(day)
            total_list[multi_num] += lendf
            while True:
                add_count += 1
                if add_count % multi == 0:
                    if reverse:
                        reverse   = False
                        multi_num = 0
                    else:
                        reverse   = True
                        multi_num = multi - 1
                else:
                    if reverse:
                        multi_num -= 1
                    else:
                        multi_num += 1
                if total_list[multi_num] < divid_lendf:
                    break

        windowQ.put((ui_num['백테엔진'], f'{one_code} 일자별 분류 완료'))
        for i, days in enumerate(day_lists):
            ui.back_eques[i].put(('데이터로딩', ui.startday, ui.endday, ui.starttime, ui.endtime, days, ui.avg_list, code_days, day_codes, divid_mode, one_code))

    for _ in range(multi):
        data = backQ.get()
        ui.back_count += data
        windowQ.put((ui_num['백테엔진'], f'백테엔진 데이터 로딩 중 ... [{data}]'))
    windowQ.put((ui_num['백테엔진'], '백테엔진 준비 완료'))

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
    test_ok   = False
    test_time = timedelta_sec(3)

    while now() < test_time:
        if not testQ.empty():
            testQ.get()
            print(f'{gubun} 코드 오류 테스트 완료')
            test_ok = True
            break
        qtest_qwait(0.1)

    if not test_ok:
        print(f'{gubun}에 오류가 있어 저장하지 못하였습니다.')

    return test_ok

def clear_backtestQ(backQ, totalQ):
    if not backQ.empty():
        while not backQ.empty():
            backQ.get()
    if not totalQ.empty():
        while not totalQ.empty():
            totalQ.get()

def backtest_process_kill(ui, gubun, totalQ):
    ui.back_condition = False
    totalQ.put('백테중지')
    qtest_qwait(3)
    if ui.proc_backtester_bb is not None and   ui.proc_backtester_bb.is_alive():   ui.proc_backtester_bb.kill()
    if ui.proc_backtester_bf is not None and   ui.proc_backtester_bf.is_alive():   ui.proc_backtester_bf.kill()
    if ui.proc_backtester_bc is not None and   ui.proc_backtester_bc.is_alive():   ui.proc_backtester_bc.kill()
    if ui.proc_backtester_bp is not None and   ui.proc_backtester_bp.is_alive():   ui.proc_backtester_bp.kill()
    if ui.proc_backtester_o is not None and    ui.proc_backtester_o.is_alive():    ui.proc_backtester_o.kill()
    if ui.proc_backtester_ov is not None and   ui.proc_backtester_ov.is_alive():   ui.proc_backtester_ov.kill()
    if ui.proc_backtester_ovc is not None and  ui.proc_backtester_ovc.is_alive():  ui.proc_backtester_ovc.kill()
    if ui.proc_backtester_ot is not None and   ui.proc_backtester_ot.is_alive():   ui.proc_backtester_ot.kill()
    if ui.proc_backtester_ovt is not None and  ui.proc_backtester_ovt.is_alive():  ui.proc_backtester_ovt.kill()
    if ui.proc_backtester_ovct is not None and ui.proc_backtester_ovct.is_alive(): ui.proc_backtester_ovct.kill()
    if ui.proc_backtester_or is not None and   ui.proc_backtester_or.is_alive():   ui.proc_backtester_or.kill()
    if ui.proc_backtester_orv is not None and  ui.proc_backtester_orv.is_alive():  ui.proc_backtester_orv.kill()
    if ui.proc_backtester_orvc is not None and ui.proc_backtester_orvc.is_alive(): ui.proc_backtester_orvc.kill()
    if ui.proc_backtester_b is not None and    ui.proc_backtester_b.is_alive():    ui.proc_backtester_b.kill()
    if ui.proc_backtester_bv is not None and   ui.proc_backtester_bv.is_alive():   ui.proc_backtester_bv.kill()
    if ui.proc_backtester_bvc is not None and  ui.proc_backtester_bvc.is_alive():  ui.proc_backtester_bvc.kill()
    if ui.proc_backtester_bt is not None and   ui.proc_backtester_bt.is_alive():   ui.proc_backtester_bt.kill()
    if ui.proc_backtester_bvt is not None and  ui.proc_backtester_bvt.is_alive():  ui.proc_backtester_bvt.kill()
    if ui.proc_backtester_bvct is not None and ui.proc_backtester_bvct.is_alive(): ui.proc_backtester_bvct.kill()
    if ui.proc_backtester_br is not None and   ui.proc_backtester_br.is_alive():   ui.proc_backtester_br.kill()
    if ui.proc_backtester_brv is not None and  ui.proc_backtester_brv.is_alive():  ui.proc_backtester_brv.kill()
    if ui.proc_backtester_brvc is not None and ui.proc_backtester_brvc.is_alive(): ui.proc_backtester_brvc.kill()
    if ui.proc_backtester_oc is not None and   ui.proc_backtester_oc.is_alive():   ui.proc_backtester_oc.kill()
    if ui.proc_backtester_ocv is not None and  ui.proc_backtester_ocv.is_alive():  ui.proc_backtester_ocv.kill()
    if ui.proc_backtester_ocvc is not None and ui.proc_backtester_ocvc.is_alive(): ui.proc_backtester_ocvc.kill()
    if ui.proc_backtester_og is not None and   ui.proc_backtester_og.is_alive():   ui.proc_backtester_og.kill()
    if ui.proc_backtester_ogv is not None and  ui.proc_backtester_ogv.is_alive():  ui.proc_backtester_ogv.kill()
    if ui.proc_backtester_ogvc is not None and ui.proc_backtester_ogvc.is_alive(): ui.proc_backtester_ogvc.kill()
    if ui.main_btn == 2:   ui.ss_pushButtonn_08.setStyleSheet(style_bc_dk)
    elif ui.main_btn == 3: ui.cs_pushButtonn_08.setStyleSheet(style_bc_dk)
    if gubun: ui.BacktestEngineKill()
    ui.back_condition = True
