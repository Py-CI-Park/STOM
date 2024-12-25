import subprocess
from multiprocessing import Process
from coin.trader_binance_future import BFTrader
from coin.receiver_binance_future import BFReceiver
from coin.strategy_binance_future import StrategyBinanceFuture
from coin.receiver_binance_future_client import BFReceiverClient
from coin.trader_upbit import UBTrader
from coin.receiver_upbit import UBReceiver
from coin.strategy_upbit import StrategyUpbit
from coin.receiver_upbit_client import UBReceiverClient
from ui.set_logfile import SetLogFile
from utility.setting import columns_tdf, columns_jgf, ui_num
from utility.static import int_hms, int_hms_utc, now, strf_time


def process_starter(ui):
    """
    windowQ, soundQ, ui.queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ,  cstgQ, liveQ, kimpQ, wdzservQ, totalQ
       0        1       2      3       4      5      6      7       8         9         10     11    12      13       14
    """
    inthms    = int_hms()
    inthmsutc = int_hms_utc()

    if ui.int_time < 80000 <= inthms:
        SetLogFile(ui)
        ClearTextEdit(ui)

    A = not ui.dict_set['코인장초프로세스종료'] and not ui.dict_set['코인장중프로세스종료']
    B = ui.dict_set['코인장초프로세스종료'] and inthmsutc < ui.dict_set['코인장초전략종료시간']
    C = ui.dict_set['코인장중프로세스종료'] and inthmsutc < ui.dict_set['코인장중전략종료시간']
    D = inthmsutc > 235000

    if A or B or C or D:
        if ui.dict_set['코인리시버']:
            CoinReceiverStart(ui, ui.qlist)
        if ui.dict_set['코인트레이더']:
            CoinTraderStart(ui, ui.qlist, ui.windowQ)

    if ui.dict_set['코인트레이더'] and A and D and not ui.time_sync:
        subprocess.Popen('python64 ./utility/timesync.py')
        ui.time_sync = True

    if ui.int_time < 90000 <= inthms:
        ui.time_sync = False

    if not ui.backtest_engine and ui.dict_set['스톰라이브'] and ui.StomLiveProcessAlive():
        if ui.int_time < 93100 <= inthms:
            if ui.dict_set['주식트레이더']:   ui.StomliveScreenshot('S스톰라이브')
            elif ui.dict_set['코인트레이더']: ui.StomliveScreenshot('C스톰라이브')

    if ui.dict_set['백테스케쥴실행'] and not ui.backtest_engine and now().weekday() == ui.dict_set['백테스케쥴요일']:
        if ui.int_time < ui.dict_set['백테스케쥴시간'] <= inthms:
            ui.AutoBackSchedule(1)

    if ui.auto_run == 1:
        ui.mnButtonClicked_03(stocklogin=True)
        ui.auto_run = 0

    UpdateWindowTitle(ui)
    ui.int_time = inthms


def CoinReceiverStart(ui, qlist):
    if not ui.CoinReceiverProcessAlive():
        if ui.dict_set['리시버공유'] < 2:
            ui.proc_receiver_coin = Process(
                target=UBReceiver if ui.dict_set['거래소'] == '업비트' else BFReceiver, args=(qlist,))
        else:
            ui.proc_receiver_coin = Process(
                target=UBReceiverClient if ui.dict_set['거래소'] == '업비트' else BFReceiverClient,
                args=(qlist,))
        ui.proc_receiver_coin.start()


def CoinTraderStart(ui, qlist, windowQ):
    if ui.dict_set['거래소'] == '업비트' and (ui.dict_set['Access_key1'] is None or ui.dict_set['Secret_key1'] is None):
        windowQ.put((ui_num['C단순텍스트'], '시스템 명령 오류 알림 - 업비트 계정이 설정되지 않아 트레이더를 시작할 수 없습니다. 계정 설정 후 다시 시작하십시오.'))
        return
    elif ui.dict_set['거래소'] == '바이낸스선물' and (ui.dict_set['Access_key2'] is None or ui.dict_set['Secret_key2'] is None):
        windowQ.put((ui_num['C단순텍스트'], '시스템 명령 오류 알림 - 바이낸스선물 계정이 설정되지 않아 트레이더를 시작할 수 없습니다. 계정 설정 후 다시 시작하십시오.'))
        return

    if not ui.CoinStrategyProcessAlive():
        ui.proc_strategy_coin = Process(target=StrategyUpbit if ui.dict_set['거래소'] == '업비트' else StrategyBinanceFuture,
                                        args=(qlist,), daemon=True)
        ui.proc_strategy_coin.start()
    if not ui.CoinTraderProcessAlive():
        ui.proc_trader_coin = Process(target=UBTrader if ui.dict_set['거래소'] == '업비트' else BFTrader,
                                      args=(qlist,))
        ui.proc_trader_coin.start()
        if ui.dict_set['거래소'] == '바이낸스선물':
            ui.ctd_tableWidgettt.setColumnCount(len(columns_tdf))
            ui.ctd_tableWidgettt.setHorizontalHeaderLabels(columns_tdf)
            ui.ctd_tableWidgettt.setColumnWidth(0, 96)
            ui.ctd_tableWidgettt.setColumnWidth(1, 90)
            ui.ctd_tableWidgettt.setColumnWidth(2, 90)
            ui.ctd_tableWidgettt.setColumnWidth(3, 90)
            ui.ctd_tableWidgettt.setColumnWidth(4, 140)
            ui.ctd_tableWidgettt.setColumnWidth(5, 70)
            ui.ctd_tableWidgettt.setColumnWidth(6, 90)
            ui.ctd_tableWidgettt.setColumnWidth(7, 90)
            ui.cjg_tableWidgettt.setColumnCount(len(columns_jgf))
            ui.cjg_tableWidgettt.setHorizontalHeaderLabels(columns_jgf)
            ui.cjg_tableWidgettt.setColumnWidth(0, 96)
            ui.cjg_tableWidgettt.setColumnWidth(1, 70)
            ui.cjg_tableWidgettt.setColumnWidth(2, 115)
            ui.cjg_tableWidgettt.setColumnWidth(3, 115)
            ui.cjg_tableWidgettt.setColumnWidth(4, 90)
            ui.cjg_tableWidgettt.setColumnWidth(5, 90)
            ui.cjg_tableWidgettt.setColumnWidth(6, 90)
            ui.cjg_tableWidgettt.setColumnWidth(7, 90)
            ui.cjg_tableWidgettt.setColumnWidth(8, 90)
            ui.cjg_tableWidgettt.setColumnWidth(9, 90)
            ui.cjg_tableWidgettt.setColumnWidth(10, 90)
            ui.cjg_tableWidgettt.setColumnWidth(11, 90)


def UpdateWindowTitle(ui):
    inthms = int_hms()
    inthmsutc = int_hms_utc()
    text = 'STOM'
    if ui.dict_set['리시버공유'] == 1:
        text = f'{text} Server'
    elif ui.dict_set['리시버공유'] == 2:
        text = f'{text} Client'
    if ui.dict_set['거래소'] == '바이낸스선물' and ui.dict_set['코인트레이더']:
        text = f'{text} | 바이낸스선물'
    elif ui.dict_set['거래소'] == '업비트' and ui.dict_set['코인트레이더']:
        text = f'{text} | 업비트'
    elif ui.dict_set['증권사'] == '키움증권해외선물' and ui.dict_set['주식트레이더']:
        text = f'{text} | 키움증권해외선물'
    elif ui.dict_set['주식트레이더']:
        text = f'{text} | 키움증권'
    if ui.showQsize:
        beqsize = sum((stq.qsize() for stq in ui.back_eques)) if ui.back_eques else 0
        bstqsize = sum((ctq.qsize() for ctq in ui.back_sques)) if ui.back_sques else 0
        text = f'{text} | sreceivQ[{ui.srqsize}] | straderQ[{ui.stqsize}] | sstrateyQ[{ui.ssqsize}] | ' \
               f'creceivQ[{ui.creceivQ.qsize()}] | ctraderQ[{ui.ctraderQ.qsize()}] | cstrateyQ[{ui.cstgQ.qsize()}] | ' \
               f'windowQ[{ui.windowQ.qsize()}] | ui.queryQ[{ui.queryQ.qsize()}] | chartQ[{ui.chartQ.qsize()}] | ' \
               f'hogaQ[{ui.hogaQ.qsize()}] | soundQ[{ui.soundQ.qsize()} | backegQ[{beqsize}] | backstQ[{bstqsize}] | ' \
               f'backttQ[{ui.totalQ.qsize()}]'
    else:
        if ui.dict_set['코인트레이더']:
            text = f'{text} | 모의' if ui.dict_set['코인모의투자'] else f'{text} | 실전'
            if inthmsutc < ui.dict_set["코인장초전략종료시간"]:
                text = f'{text} | {ui.dict_set["코인장초매수전략"] if ui.dict_set["코인장초매수전략"] != "" else "전략사용안함"}'
            else:
                text = f'{text} | {ui.dict_set["코인장중매수전략"] if ui.dict_set["코인장중매수전략"] != "" else "전략사용안함"}'
        elif ui.dict_set['주식트레이더']:
            text = f'{text} | 모의' if ui.dict_set['주식모의투자'] else f'{text} | 실전'
            if inthms < ui.dict_set["주식장초전략종료시간"]:
                text = f'{text} | {ui.dict_set["주식장초매수전략"] if ui.dict_set["주식장초매수전략"] != "" else "전략사용안함"}'
            else:
                text = f'{text} | {ui.dict_set["주식장중매수전략"] if ui.dict_set["주식장중매수전략"] != "" else "전략사용안함"}'
        text = f"{text} | {strf_time('%Y-%m-%d %H:%M:%S')}"
    ui.setWindowTitle(text)


def ClearTextEdit(ui):
    ui.sst_textEditttt_01.clear()
    ui.cst_textEditttt_01.clear()
    ui.src_textEditttt_01.clear()
    ui.crc_textEditttt_01.clear()
