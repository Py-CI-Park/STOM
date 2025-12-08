import math
import random
import pyupbit
import sqlite3
import operator
import numpy as np
import pandas as pd
from numba import jit
from talib import stream
from traceback import print_exc
from matplotlib import pyplot as plt
from optuna_dashboard import run_server
from matplotlib import font_manager, gridspec
from utility.static import strp_time, strf_time, thread_decorator
from utility.setting import ui_num, GRAPH_PATH, DB_SETTING, DB_OPTUNA


@thread_decorator
def RunOptunaServer():
    try:
        run_server(DB_OPTUNA)
    except:
        pass


def GetTradeInfo(gubun):
    if gubun == 1:
        v = {
            '보유중': 0,
            '매수가': 0,
            '매도가': 0,
            '주문수량': 0,
            '보유수량': 0,
            '최고수익률': 0.,
            '최저수익률': 0.,
            '매수틱번호': 0,
            '매수시간': strp_time('%Y%m%d', '20000101')
        }
    elif gubun == 2:
        v = {
            '보유중': 0,
            '매수가': 0,
            '매도가': 0,
            '주문수량': 0,
            '보유수량': 0,
            '최고수익률': 0.,
            '최저수익률': 0.,
            '매수틱번호': 0,
            '매수시간': strp_time('%Y%m%d', '20000101'),
            '추가매수시간': [],
            '매수호가': 0,
            '매도호가': 0,
            '매수호가_': 0,
            '매도호가_': 0,
            '추가매수가': 0,
            '매수호가단위': 0,
            '매도호가단위': 0,
            '매수정정횟수': 0,
            '매도정정횟수': 0,
            '매수분할횟수': 0,
            '매도분할횟수': 0,
            '매수주문취소시간': strp_time('%Y%m%d', '20000101'),
            '매도주문취소시간': strp_time('%Y%m%d', '20000101')
        }
    else:
        v = {
            '손절횟수': 0,
            '거래횟수': 0,
            '직전거래시간': strp_time('%Y%m%d', '20000101'),
            '손절매도시간': strp_time('%Y%m%d', '20000101')
        }
    return v


def GetBackloadCodeQuery(code, days, starttime, endtime):
    last = len(days) - 1
    like_text = '( '
    for i, day in enumerate(days):
        if i != last:
            like_text += f"`index` LIKE '{day}%' or "
        else:
            like_text += f"`index` LIKE '{day}%' )"
    if len(str(endtime)) < 5:
        query = f"SELECT * FROM '{code}' WHERE {like_text} and " \
                f"`index` % 10000 >= {starttime} and " \
                f"`index` % 10000 <= {endtime}"
    else:
        query = f"SELECT * FROM '{code}' WHERE {like_text} and " \
                f"`index` % 1000000 >= {starttime} and " \
                f"`index` % 1000000 <= {endtime}"
    return query


def GetBackloadDayQuery(day, code, starttime, endtime):
    if len(str(endtime)) < 5:
        query = f"SELECT * FROM '{code}' WHERE " \
                f"`index` LIKE '{day}%' and " \
                f"`index` % 10000 >= {starttime} and " \
                f"`index` % 10000 <= {endtime}"
    else:
        query = f"SELECT * FROM '{code}' WHERE " \
                f"`index` LIKE '{day}%' and " \
                f"`index` % 1000000 >= {starttime} and " \
                f"`index` % 1000000 <= {endtime}"
    return query


def GetMoneytopQuery(gubun, startday, endday, starttime, endtime):
    if len(str(endtime)) < 5:
        query = f"SELECT * FROM moneytop WHERE " \
                f"`index` >= {startday * 10000} and " \
                f"`index` <= {endday * 10000 + 2400} and " \
                f"`index` % 10000 >= {starttime} and " \
                f"`index` % 10000 <= {endtime}"
    else:
        if gubun == 'S' and starttime < 90030:
            query = f"SELECT * FROM moneytop WHERE " \
                    f"`index` >= {startday * 1000000} and " \
                    f"`index` <= {endday * 1000000 + 240000} and " \
                    f"`index` % 1000000 >= 90030 and " \
                    f"`index` % 1000000 <= {endtime}"
        else:
            query = f"SELECT * FROM moneytop WHERE " \
                    f"`index` >= {startday * 1000000} and " \
                    f"`index` <= {endday * 1000000 + 240000} and " \
                    f"`index` % 1000000 >= {starttime} and " \
                    f"`index` % 1000000 <= {endtime}"
    return query


def AddAvgData(df, round_unit, is_tick, avg_list):
    if is_tick:
        df['이평0060'] = df['현재가'].rolling(window=60).mean().round(round_unit)
        df['이평0300'] = df['현재가'].rolling(window=300).mean().round(round_unit)
        df['이평0600'] = df['현재가'].rolling(window=600).mean().round(round_unit)
        df['이평1200'] = df['현재가'].rolling(window=1200).mean().round(round_unit)
    else:
        df['이평005'] = df['현재가'].rolling(window=5).mean().round(round_unit)
        df['이평010'] = df['현재가'].rolling(window=10).mean().round(round_unit)
        df['이평020'] = df['현재가'].rolling(window=20).mean().round(round_unit)
        df['이평060'] = df['현재가'].rolling(window=60).mean().round(round_unit)
        df['이평120'] = df['현재가'].rolling(window=120).mean().round(round_unit)
    for avg in avg_list:
        df[f'최고현재가{avg}'] = df['현재가'].rolling(window=avg).max()
        df[f'최저현재가{avg}'] = df['현재가'].rolling(window=avg).min()
        if not is_tick:
            df[f'최고분봉고가{avg}'] = df['분봉고가'].rolling(window=avg).max()
            df[f'최저분봉저가{avg}'] = df['분봉저가'].rolling(window=avg).min()
        df[f'체결강도평균{avg}'] = df['체결강도'].rolling(window=avg).mean().round(3)
        df[f'최고체결강도{avg}'] = df['체결강도'].rolling(window=avg).max()
        df[f'최저체결강도{avg}'] = df['체결강도'].rolling(window=avg).min()
        if is_tick:
            df[f'최고초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).max()
            df[f'최고초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).max()
            df[f'누적초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).sum()
            df[f'누적초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).sum()
            df[f'초당거래대금평균{avg}'] = df['초당거래대금'].rolling(window=avg).mean().round(0)
        else:
            df[f'최고분당매수수량{avg}'] = df['분당매수수량'].rolling(window=avg).max()
            df[f'최고분당매도수량{avg}'] = df['분당매도수량'].rolling(window=avg).max()
            df[f'누적분당매수수량{avg}'] = df['분당매수수량'].rolling(window=avg).sum()
            df[f'누적분당매도수량{avg}'] = df['분당매도수량'].rolling(window=avg).sum()
            df[f'분당거래대금평균{avg}'] = df['분당거래대금'].rolling(window=avg).mean().round(0)
        if round_unit == 3:
            df2 = df[['등락율', '당일거래대금', '전일비']].copy()
            df2[f'등락율N{avg}'] = df2['등락율'].shift(avg - 1)
            df2['등락율차이'] = df2['등락율'] - df2[f'등락율N{avg}']
            df2[f'당일거래대금N{avg}'] = df2['당일거래대금'].shift(avg - 1)
            df2['당일거래대금차이'] = df2['당일거래대금'] - df2[f'당일거래대금N{avg}']
            df2[f'전일비N{avg}'] = df2['전일비'].shift(avg - 1)
            df2['전일비차이'] = df2['전일비'] - df2[f'전일비N{avg}']
            df['등락율각도'] = df2['등락율차이'].apply(lambda x: round(math.atan2(x * 5, avg) / (2 * math.pi) * 360, 2))
            df['당일거래대금각도'] = df2['당일거래대금차이'].apply(lambda x: round(math.atan2(x / 100, avg) / (2 * math.pi) * 360, 2))
            df['전일비각도'] = df2['전일비차이'].apply(lambda x: round(math.atan2(x, avg) / (2 * math.pi) * 360, 2))
        else:
            df2 = df[['등락율', '당일거래대금']].copy()
            df2[f'등락율N{avg}'] = df2['등락율'].shift(avg - 1)
            df2['등락율차이'] = df2['등락율'] - df2[f'등락율N{avg}']
            df2[f'당일거래대금N{avg}'] = df2['당일거래대금'].shift(avg - 1)
            df2['당일거래대금차이'] = df2['당일거래대금'] - df2[f'당일거래대금N{avg}']
            df['등락율각도'] = df2['등락율차이'].apply(lambda x: round(math.atan2(x * 10, avg) / (2 * math.pi) * 360, 2))
            df['당일거래대금각도'] = df2['당일거래대금차이'].apply(lambda x: round(math.atan2(x / 100_000_000, avg) / (2 * math.pi) * 360, 2))
    return df


def LoadOrderSetting(gubun):
    con = sqlite3.connect(DB_SETTING)
    if 'S' in gubun:
        df1 = pd.read_sql('SELECT * FROM stockbuyorder', con).set_index('index')
        df2 = pd.read_sql('SELECT * FROM stocksellorder', con).set_index('index')
    else:
        df1 = pd.read_sql('SELECT * FROM coinbuyorder', con).set_index('index')
        df2 = pd.read_sql('SELECT * FROM coinsellorder', con).set_index('index')
    con.close()
    buy_setting = str(list(df1.iloc[0]))
    sell_setting = str(list(df2.iloc[0]))
    return buy_setting, sell_setting


def GetBuyStg(buytxt, gubun):
    buytxt  = buytxt.split('if 매수:')[0] + 'if 매수:\n    self.Buy(vturn, vkey)'
    buystg  = ''
    indistg = ''
    for line in buytxt.split('\n'):
        if 'self.indicator' in line:
            indistg += f'{line}\n'
        else:
            buystg += f'{line}\n'
    if buystg != '':
        try:
            buystg = compile(buystg, '<string>', 'exec')
        except:
            buystg = None
            if gubun == 0: print_exc()
    else:
        buystg = None
    if indistg != '':
        try:
            indistg = compile(indistg, '<string>', 'exec')
        except:
            indistg = None
    else:
        indistg = None
    return buystg, indistg


def GetSellStg(sellstg, gubun):
    sellstg = 'sell_cond = 0\n' + sellstg.split('if 매도:')[0] + 'if 매도:\n    self.Sell(vturn, vkey, sell_cond)'
    sellstg, dict_cond = SetSellCond(sellstg.split('\n'))
    try:
        sellstg = compile(sellstg, '<string>', 'exec')
    except:
        sellstg = None
        if gubun == 0: print_exc()
    return sellstg, dict_cond


def GetBuyConds(buy_conds, gubun):
    buy_conds = 'if ' + ':\n    매수 = False\nelif '.join(
        buy_conds) + ':\n    매수 = False\nif 매수:\n    self.Buy(vturn, vkey)'
    try:
        buy_conds = compile(buy_conds, '<string>', 'exec')
    except:
        buy_conds = None
        if gubun == 0: print_exc()
    return buy_conds


def GetSellConds(sell_conds, gubun):
    sell_conds = 'sell_cond = 0\nif ' + ':\n    매도 = True\nelif '.join(
        sell_conds) + ':\n    매도 = True\nif 매도:\n    self.Sell(vturn, vkey, sell_cond)'
    sell_conds, dict_cond = SetSellCond(sell_conds.split('\n'))
    try:
        sell_conds = compile(sell_conds, '<string>', 'exec')
    except:
        sell_conds = None
        if gubun == 0: print_exc()
    return sell_conds, dict_cond


def SetSellCond(selllist):
    count = 1
    sellstg = ''
    dict_cond = {0: '전략종료청산', 100: '분할매도', 200: '손절청산'}
    for i, text in enumerate(selllist):
        if '#' not in text and ('매도 = True' in text or '매도= True' in text or '매도 =True' in text or '매도=True' in text):
            dict_cond[count] = selllist[i - 1]
            sellstg = f"{sellstg}{text.split('매도')[0]}sell_cond = {count}\n"
            count += 1
        if text != '':
            sellstg = f"{sellstg}{text}\n"
    return sellstg, dict_cond


def GetBuyStgFuture(buystg, gubun):
    buytxt  = buystg.split('if BUY_LONG or SELL_SHORT:')[
                 0] + 'if BUY_LONG:\n    self.Buy(vturn, vkey, "LONG")\nelif SELL_SHORT:\n    self.Buy(vturn, vkey, "SHORT")'
    buystg  = ''
    indistg = ''
    for line in buytxt.split('\n'):
        if 'self.indicator' in line:
            indistg += f'{line}\n'
        else:
            buystg += f'{line}\n'
    if buystg != '':
        try:
            buystg = compile(buystg, '<string>', 'exec')
        except:
            buystg = None
            if gubun == 0: print_exc()
    else:
        buystg = None
    if indistg != '':
        try:
            indistg = compile(indistg, '<string>', 'exec')
        except:
            indistg = None
    else:
        indistg = None
    return buystg, indistg


def GetSellStgFuture(sellstg, gubun):
    sellstg = 'sell_cond = 0\n' + sellstg.split("if (포지션 == 'LONG' and SELL_LONG) or (포지션 == 'SHORT' and BUY_SHORT):")[
        0] + "if 포지션 == 'LONG' and SELL_LONG:\n    self.Sell(vturn, vkey, 'LONG', sell_cond)\nelif 포지션 == 'SHORT' and BUY_SHORT:\n    self.Sell(vturn, vkey, 'SHORT', sell_cond)"
    sellstg, dict_cond = SetSellCondFuture(sellstg.split('\n'))
    try:
        sellstg = compile(sellstg, '<string>', 'exec')
    except:
        sellstg = None
        if gubun == 0: print_exc()
    return sellstg, dict_cond


def GetBuyCondsFuture(is_long, buy_conds, gubun):
    if is_long:
        buy_conds = 'if ' + ':\n    BUY_LONG = False\nelif '.join(
            buy_conds) + ':\n    BUY_LONG = False\nif BUY_LONG:\n    self.Buy(vturn, vkey, "LONG")'
    else:
        buy_conds = 'if ' + ':\n    SELL_SHORT = False\nelif '.join(
            buy_conds) + ':\n    SELL_SHORT = False\nif SELL_SHORT:\n    self.Buy(vturn, vkey, "SHORT")'
    try:
        buy_conds = compile(buy_conds, '<string>', 'exec')
    except:
        buy_conds = None
        if gubun == 0: print_exc()
    return buy_conds


def GetSellCondsFuture(is_long, sell_conds, gubun):
    if is_long:
        sell_conds = 'sell_cond = 0\nif ' + ':\n    SELL_LONG = True\nelif '.join(
            sell_conds) + ':\n    SELL_LONG = True\nif SELL_LONG:\n    self.Sell(vturn, vkey, "SELL_LONG", sell_cond)'
    else:
        sell_conds = 'sell_cond = 0\nif ' + ':\n    BUY_SHORT = True\nelif '.join(
            sell_conds) + ':\n    BUY_SHORT = True\nif BUY_SHORT:\n    self.Sell(vturn, vkey, "BUY_SHORT", sell_cond)'
    sell_conds, dict_cond = SetSellCondFuture(sell_conds.split('\n'))
    try:
        sell_conds = compile(sell_conds, '<string>', 'exec')
    except:
        sell_conds = None
        if gubun == 0: print_exc()
    return sell_conds, dict_cond


def SetSellCondFuture(selllist):
    count = 1
    sellstg = ''
    dict_cond = {0: '전략종료청산', 100: '분할매도', 200: '손절청산'}
    for i, text in enumerate(selllist):
        if '#' not in text:
            if 'SELL_LONG = True' in text or 'SELL_LONG= True' in text or 'SELL_LONG =True' in text or 'SELL_LONG=True' in text:
                dict_cond[count] = selllist[i - 1]
                sellstg = f"{sellstg}{text.split('SELL_LONG')[0]}sell_cond = {count}\n"
                count += 1
            elif 'BUY_SHORT = True' in text or 'BUY_SHORT= True' in text or 'BUY_SHORT =True' in text or 'BUY_SHORT=True' in text:
                dict_cond[count] = selllist[i - 1]
                sellstg = f"{sellstg}{text.split('BUY_SHORT')[0]}sell_cond = {count}\n"
                count += 1
        if text != '':
            sellstg = f"{sellstg}{text}\n"
    return sellstg, dict_cond


def SendTextAndStd(result, dict_train, dict_valid=None, exponential=False):
    gubun, ui_gubun, wq, mq, stdp, optistd, opti_turn, vturn, vkey, vars_list, startday, endday, std_list, betting = result
    if gubun in ('최적화', '최적화테스트'):
        text1 = GetText1(opti_turn, vturn, vars_list)
    elif gubun == 'GA최적화':
        text1 = f'<font color=white> V{vars_list} </font>'
    elif gubun == '전진분석':
        text1 = f'<font color=#f78645>[IN] P[{startday}~{endday}]</font>{GetText1(opti_turn, vturn, vars_list)}'
    else:
        text1 = ''

    stdp_ = 0
    if dict_valid is not None:
        tuple_train = sorted(dict_train.items(), key=operator.itemgetter(0))
        tuple_valid = sorted(dict_valid.items(), key=operator.itemgetter(0))
        train_text = []
        valid_text = []
        train_data = []
        valid_data = []

        for k, v in tuple_train:
            text2, std = GetText2(f'TRAIN{k + 1}', optistd, std_list, betting, v)
            train_text.append(text2)
            train_data.append(std)
        for k, v in tuple_valid:
            text2, std = GetText2(f'VALID{k + 1}', optistd, std_list, betting, v)
            valid_text.append(text2)
            valid_data.append(std)

        std = GetOptiValidStd(train_data, valid_data, optistd, betting, exponential)
        text3, stdp_ = GetText3(std, stdp)
        if opti_turn == 2: text3 = ''

        wq.put((ui_num[f'{ui_gubun}백테스트'], f'{text1}{text3}'))
        for text in train_text:
            wq.put((ui_num[f'{ui_gubun}백테스트'], text))
        for text in valid_text:
            wq.put((ui_num[f'{ui_gubun}백테스트'], text))
    elif dict_train is not None:
        if gubun == '최적화테스트':
            text2, std = GetText2('TEST', optistd, std_list, betting, dict_train)
            text3 = ''
        else:
            text2, std = GetText2('TOTAL', optistd, std_list, betting, dict_train)
            text3, stdp_ = GetText3(std, stdp)
        wq.put((ui_num[f'{ui_gubun}백테스트'], f'{text1}{text2}{text3}'))
    else:
        stdp_ = stdp
        std = -2_000_000_000
        text2 = '매수전략을 만족하는 경우가 없어 결과를 표시할 수 없습니다.'
        wq.put((ui_num[f'{ui_gubun}백테스트'], f'{text1}{text2}'))

    if opti_turn != 2:
        mq.put((vturn, vkey, std))
    return stdp_


def GetText1(opti_turn, vturn, vars_list):
    prev_vars, curr_vars, next_vars = '', '', ''
    if opti_turn != 1:
        next_vars = f'<font color=#6eff6e> V{vars_list} </font>'
    else:
        prev_vars = f' V{vars_list[:vturn]}'.split(']')[0]
        prev_vars = f'<font color=white>{prev_vars}</font>' if vturn == 0 else f'<font color=white>{prev_vars}, </font>'
        curr_vars = f'<font color=#6eff6e>{vars_list[vturn]}</font>'
        next_vars = f'{vars_list[vturn + 1:]}'.split('[')[1]
        if next_vars != ']': next_vars = f', {next_vars}'
        next_vars = f'<font color=white>{next_vars} </font>'
    return f'{prev_vars}{curr_vars}{next_vars}'


def GetText2(gubun, optistd, std_list, betting, result):
    tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi, mdd, mdd_ = result
    if tpp < 0 < tsg: tsg = -2_147_483_648
    mddt = f'{mdd_:,.0f}' if 'G' in optistd else f'{mdd:,.2f}%'
    text = f'{gubun} TC[{tc:,.0f}] ATC[{atc:,.1f}] MH[{mhct}] WR[{wr:,.2f}%] MDD[{mddt}] CAGR[{cagr:,.2f}] TPI[{tpi:,.2f}] AP[{app:,.2f}%] TP[{tpp:,.2f}%] TG[{tsg:,.0f}]'
    std, text = GetOptiStdText(optistd, std_list, betting, result, text)
    text = f'<font color=white>{text}</font>' if tsg >= 0 else f'<font color=#96969b>{text}</font>'
    return text, std


def GetText3(std, stdp):
    text = f'<font color=#f78645>MERGE[{std:,.2f}]</font>'
    if std >= stdp:
        text = f'{text}<font color=#6eff6e>[기준값갱신]</font>' if std > stdp else f'{text}<font color=white>[기준값동일]</font>'
        stdp = std
    return text, stdp


def GetOptiValidStd(train_data, valid_data, optistd, betting, exponential):
    """
    교차검증 최적화 표준값 계산

    변경사항 (2025-11-29):
    - std_false_point (-2,222,222,222) 데이터는 계산에서 제외
    - 유효한 데이터 쌍만으로 평균 계산
    - 모든 데이터가 조건 불만족이면 std_false_point 반환

    가중치(exponential) 예제:
    10개 : 2.00, 1.80, 1.60, 1.40, 1.20, 1.00, 0.80, 0.60, 0.40, 0.20
    8개  : 2.00, 1.75, 1.50, 1.25, 1.00, 0.75, 0.50, 0.25
    7개  : 2.00, 1.71, 1.42, 1.14, 0.86, 0.57, 0.29
    6개  : 2.00, 1.66, 1.33, 1.00, 0.66, 0.33
    5개  : 2.00, 1.60, 1.20, 0.80, 0.40
    4개  : 2.00, 1.50, 1.00, 0.50
    3개  : 2.00, 1.33, 0.66
    2개  : 2.00, 1.0
    """
    std = 0
    valid_count = 0  # 유효한 데이터 쌍 개수
    total_count = len(train_data)
    std_false_point = -2_222_222_222

    for i in range(total_count):
        # 제한 조건 불만족 데이터는 건너뛰기
        if train_data[i] == std_false_point or valid_data[i] == std_false_point:
            continue

        valid_count += 1

        # 가중치 계산 (지수 가중치 옵션)
        if exponential and total_count > 1:
            ex = (total_count - i) * 2 / total_count
        else:
            ex = 1

        # TRAIN × VALID 곱셈
        std_ = train_data[i] * valid_data[i] * ex

        # 누적 (둘 다 음수면 절댓값으로 처리)
        if train_data[i] < 0 and valid_data[i] < 0:
            std = std - std_
        else:
            std = std + std_

    # 유효한 데이터가 없으면 조건 불만족 반환
    if valid_count == 0:
        return std_false_point

    # 평균 계산 (유효 개수로 나눔)
    if optistd == 'TG':
        std = round(std / valid_count / betting, 2)
    else:
        std = round(std / valid_count, 2)

    return std


def GetOptiStdText(optistd, std_list, betting, result, pre_text):
    mdd_low, mdd_high, mhct_low, mhct_high, wr_low, wr_high, ap_low, ap_high, atc_low, atc_high, cagr_low, cagr_high, tpi_low, tpi_high = std_list
    tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi, mdd, mdd_ = result
    std_true = (mdd_low <= mdd <= mdd_high and mhct_low <= mhct <= mhct_high and wr_low <= wr <= wr_high and
                ap_low <= app <= ap_high and atc_low <= atc <= atc_high and cagr_low <= cagr <= cagr_high and tpi_low <= tpi <= tpi_high)
    std, pm, p2m, pam, pwm, ptm, gm, g2m, gam, gwm, gtm, text = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ''
    std_false_point = -2_222_222_222
    if tc > 0:
        if 'TRAIN' in pre_text or 'TOTAL' in pre_text:
            if 'P' in optistd:
                if optistd == 'TP':
                    std = tpp if std_true else std_false_point
                elif optistd == 'TPI':
                    std = tpi if std_true else std_false_point
                elif optistd == 'PM':
                    std = pm = round(tpp / mdd, 2) if std_true else std_false_point
                elif optistd == 'P2M':
                    std = p2m = round(tpp * tpp / mdd / 100, 2) if std_true else std_false_point
                elif optistd == 'PAM':
                    std = pam = round(tpp * app / mdd, 2) if std_true else std_false_point
                elif optistd == 'PWM':
                    std = pwm = round(tpp * wr / mdd / 100, 2) if std_true else std_false_point
                elif optistd == 'PTM':
                    std = ptm = round(tpp * app * wr * tpi * cagr / mdd / 10000, 2) if std_true else std_false_point
            elif 'G' in optistd:
                if optistd == 'TG':
                    std = tsg if std_true else std_false_point
                elif optistd == 'GM':
                    std = gm = round(tsg / mdd_, 2) if std_true else std_false_point
                elif optistd == 'G2M':
                    std = g2m = round(tsg * tsg / mdd_ / betting, 2) if std_true else std_false_point
                elif optistd == 'GAM':
                    std = gam = round(tsg * app / mdd_, 2) if std_true else std_false_point
                elif optistd == 'GWM':
                    std = gwm = round(tsg * wr / mdd_ / 100, 2) if std_true else std_false_point
                elif optistd == 'GTM':
                    std = gtm = round(tsg * app * wr * tpi * cagr / mdd_ / 10000, 2) if std_true else std_false_point
                elif optistd == 'CAGR':
                    std = cagr if std_true else std_false_point
        else:
            if 'P' in optistd:
                if optistd == 'TP':
                    std = tpp if std_true else std_false_point
                elif optistd == 'TPI':
                    std = tpi if std_true else std_false_point
                elif optistd == 'PM':
                    std = pm = round(tpp / mdd, 2) if std_true else std_false_point
                elif optistd == 'P2M':
                    std = p2m = round(tpp * tpp / mdd / 100, 2) if std_true else std_false_point
                elif optistd == 'PAM':
                    std = pam = round(tpp * app / mdd, 2) if std_true else std_false_point
                elif optistd == 'PWM':
                    std = pwm = round(tpp * wr / mdd / 100, 2) if std_true else std_false_point
                elif optistd == 'PTM':
                    std = ptm = round(tpp * app * wr * tpi * cagr / mdd / 10000, 2) if std_true else std_false_point
            elif 'G' in optistd:
                if optistd == 'TG':
                    std = tsg if std_true else std_false_point
                elif optistd == 'GM':
                    std = gm = round(tsg / mdd_, 2) if std_true else std_false_point
                elif optistd == 'G2M':
                    std = g2m = round(tsg * tsg / mdd_ / betting, 2) if std_true else std_false_point
                elif optistd == 'GAM':
                    std = gam = round(tsg * app / mdd_, 2) if std_true else std_false_point
                elif optistd == 'GWM':
                    std = gwm = round(tsg * wr / mdd_ / 100, 2) if std_true else std_false_point
                elif optistd == 'GTM':
                    std = gtm = round(tsg * app * wr * tpi * cagr / mdd_ / 10000, 2) if std_true else std_false_point
                elif optistd == 'CAGR':
                    std = cagr if std_true else std_false_point

    if optistd == 'TP':
        text = pre_text
    elif optistd == 'TG':
        text = pre_text
    elif optistd == 'TPI':
        text = pre_text
    elif optistd == 'CAGR':
        text = pre_text
    elif optistd == 'PM':
        text = f'{pre_text} PM[{pm:.2f}]'
    elif optistd == 'P2M':
        text = f'{pre_text} P2M[{p2m:.2f}]'
    elif optistd == 'PAM':
        text = f'{pre_text} PAM[{pam:.2f}]'
    elif optistd == 'PWM':
        text = f'{pre_text} PWM[{pwm:.2f}]'
    elif optistd == 'PTM':
        text = f'{pre_text} PTM[{ptm:.2f}]'
    elif optistd == 'GM':
        text = f'{pre_text} GM[{gm:.2f}]'
    elif optistd == 'G2M':
        text = f'{pre_text} G2M[{g2m:.2f}]'
    elif optistd == 'GAM':
        text = f'{pre_text} GAM[{gam:.2f}]'
    elif optistd == 'GWM':
        text = f'{pre_text} GWM[{gwm:.2f}]'
    elif optistd == 'GTM':
        text = f'{pre_text} GTM[{gtm:.2f}]'
    return std, text


def PltShow(gubun, teleQ, df_tsg, df_bct, dict_cn, seed, mdd, startday, endday, starttime, endtime, df_kp_, df_kd_, list_days,
            backname, back_text, label_text, save_file_name, schedul, plotgraph, buy_vars=None, sell_vars=None):
    df_tsg['수익금합계020'] = df_tsg['수익금합계'].rolling(window=20).mean().round(2)
    df_tsg['수익금합계060'] = df_tsg['수익금합계'].rolling(window=60).mean().round(2)
    df_tsg['수익금합계120'] = df_tsg['수익금합계'].rolling(window=120).mean().round(2)
    df_tsg['수익금합계240'] = df_tsg['수익금합계'].rolling(window=240).mean().round(2)
    df_tsg['수익금합계480'] = df_tsg['수익금합계'].rolling(window=480).mean().round(2)

    df_tsg['이익금액'] = df_tsg['수익금'].apply(lambda x: x if x >= 0 else 0)
    df_tsg['손실금액'] = df_tsg['수익금'].apply(lambda x: x if x < 0 else 0)
    sig_list = df_tsg['수익금'].to_list()
    mdd_list = []
    for i in range(30):
        random.shuffle(sig_list)
        df_tsg[f'수익금{i}'] = sig_list
        df_tsg[f'수익금합계{i}'] = df_tsg[f'수익금{i}'].cumsum()
        df_tsg.drop(columns=[f'수익금{i}'], inplace=True)
        try:
            array = np.array(df_tsg[f'수익금합계{i}'], dtype=np.float64)
            lower = np.argmax(np.maximum.accumulate(array) - array)
            upper = np.argmax(array[:lower])
            mdd_ = round(abs(array[upper] - array[lower]) / (array[upper] + seed) * 100, 2)
        except:
            mdd_ = 0.
        mdd_list.append(mdd_)

    is_min = len(str(endtime)) < 5
    df_sg = df_tsg[['수익금']].copy()
    df_sg['일자'] = df_sg.index
    df_sg['일자'] = df_sg['일자'].apply(lambda x: strp_time('%Y%m%d%H%M%S' if not is_min else '%Y%m%d%H%M', x))
    df_sg = df_sg.set_index('일자')

    df_ts = df_sg.resample('D').sum()
    df_ts['수익금합계'] = df_ts['수익금'].cumsum()
    df_ts['수익금합계'] = ((df_ts['수익금합계'] + seed) / seed - 1) * 100

    df_kp, df_kd, df_bc = None, None, None
    if dict_cn is not None:
        df_kp = df_kp_[(df_kp_['index'] >= str(startday)) & (df_kp_['index'] <= str(endday))].copy()
        df_kd = df_kd_[(df_kd_['index'] >= str(startday)) & (df_kd_['index'] <= str(endday))].copy()
        df_kp['종가'] = (df_kp['종가'] / df_kp['종가'].iloc[0] - 1) * 100
        df_kd['종가'] = (df_kd['종가'] / df_kd['종가'].iloc[0] - 1) * 100
        df_kp['일자'] = df_kp['index'].apply(lambda x: strp_time('%Y%m%d', x))
        df_kd['일자'] = df_kd['index'].apply(lambda x: strp_time('%Y%m%d', x))
        df_kp.drop(columns=['index'], inplace=True)
        df_kd.drop(columns=['index'], inplace=True)
        df_kp.set_index('일자', inplace=True)
        df_kd.set_index('일자', inplace=True)
    else:
        df_bc = pyupbit.get_ohlcv()
        df_bc['일자'] = df_bc.index
        startday = strp_time('%Y%m%d', str(startday))
        endday = strp_time('%Y%m%d%H%M%S', str(endday) + '235959')
        df_bc = df_bc[(df_bc['일자'] >= startday) & (df_bc['일자'] <= endday)]
        df_bc['close'] = (df_bc['close'] / df_bc['close'].iloc[0] - 1) * 100

    df_st = df_tsg[['수익금']].copy()
    df_st['시간'] = df_st.index
    df_st['시간'] = df_st['시간'].apply(lambda x: strp_time('%H%M%S' if not is_min else '%H%M', x[8:]))
    df_st.set_index('시간', inplace=True)
    if not is_min:
        start_time = strp_time('%H%M%S', str(starttime).zfill(6))
        end_time = strp_time('%H%M%S', str(endtime).zfill(6))
    else:
        start_time = strp_time('%H%M', str(starttime).zfill(4))
        end_time = strp_time('%H%M', str(endtime).zfill(4))
    total_sec = (end_time - start_time).total_seconds()
    df_st = df_st.resample(f'{total_sec / 600 if total_sec >= 1800 else 3}min').sum()
    df_st['시간'] = df_st.index
    df_st['시간'] = df_st['시간'].apply(lambda x: strf_time('%H%M%S' if not is_min else '%H%M', x))
    if not is_min:
        df_st['시간'] = df_st['시간'].apply(lambda x: f'{x[:2]}:{x[2:4]}:{x[4:]}')
    else:
        df_st['시간'] = df_st['시간'].apply(lambda x: f'{x[:2]}:{x[2:]}')
    df_st.set_index('시간', inplace=True)
    df_st['이익금액'] = df_st['수익금'].apply(lambda x: x if x >= 0 else 0)
    df_st['손실금액'] = df_st['수익금'].apply(lambda x: x if x < 0 else 0)

    df_wt = df_tsg[['수익금']].copy()
    df_wt['요일'] = df_wt.index
    df_wt['요일'] = df_wt['요일'].apply(lambda x: strp_time('%Y%m%d%H%M%S' if not is_min else '%Y%m%d%H%M', x).weekday())
    sum_0 = df_wt[df_wt['요일'] == 0]['수익금'].sum()
    sum_1 = df_wt[df_wt['요일'] == 1]['수익금'].sum()
    sum_2 = df_wt[df_wt['요일'] == 2]['수익금'].sum()
    sum_3 = df_wt[df_wt['요일'] == 3]['수익금'].sum()
    sum_4 = df_wt[df_wt['요일'] == 4]['수익금'].sum()
    wt_index = ['월', '화', '수', '목', '금']
    wt_data = [sum_0, sum_1, sum_2, sum_3, sum_4]
    if dict_cn is None:
        sum_5 = df_wt[df_wt['요일'] == 5]['수익금'].sum()
        sum_6 = df_wt[df_wt['요일'] == 6]['수익금'].sum()
        wt_index += ['토', '일']
        wt_data += [sum_5, sum_6]
    wt_datap, wt_datam = [], []
    for data in wt_data:
        if data >= 0:
            wt_datap.append(data)
            wt_datam.append(0)
        else:
            wt_datap.append(0)
            wt_datam.append(data)

    df_tsg['index'] = df_tsg.index
    if not is_min:
        df_tsg['index'] = df_tsg['index'].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:12]}:{x[12:14]}')
    else:
        df_tsg['index'] = df_tsg['index'].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:]}')
    df_tsg.set_index('index', inplace=True)

    endx_list = None
    if gubun == '최적화':
        if not is_min:
            endx_list = [df_tsg[df_tsg['매도시간'] < list_days[2][0] * 1000000 + 240000].index[-1]]
        else:
            endx_list = [df_tsg[df_tsg['매도시간'] < list_days[2][0] * 10000 + 2400].index[-1]]
        if list_days[1] is not None:
            for vsday, _, _ in list_days[1]:
                if not is_min:
                    df_tsg_ = df_tsg[df_tsg['매도시간'] < vsday * 1000000]
                else:
                    df_tsg_ = df_tsg[df_tsg['매도시간'] < vsday * 10000]
                if len(df_tsg_) > 0:
                    endx_list.append(df_tsg_.index[-1])

    font_name = 'C:/Windows/Fonts/malgun.ttf'
    font_family = font_manager.FontProperties(fname=font_name).get_name()
    plt.rcParams['font.family'] = font_family
    plt.rcParams['axes.unicode_minus'] = False

    plt.figure(f'{backname} 부가정보', figsize=(12, 10))
    gs = gridspec.GridSpec(nrows=2, ncols=2, height_ratios=[1, 1])
    # noinspection PyTypeChecker
    plt.subplot(gs[0])
    for i in range(30):
        plt.plot(df_tsg.index, df_tsg[f'수익금합계{i}'], linewidth=0.5, label=f'MDD {mdd_list[i]}%')
    plt.plot(df_tsg.index, df_tsg['수익금합계'], linewidth=2, label=f'MDD {mdd}%', color='orange')
    max_mdd = max(mdd_list)
    min_mdd = min(mdd_list)
    avg_mdd = round(sum(mdd_list) / len(mdd_list), 2)
    plt.title(f'Max MDD [{max_mdd}%] | Min MDD [{min_mdd}%] | Avg MDD [{avg_mdd}%]')
    count = int(len(df_tsg) / 15) if int(len(df_tsg) / 15) >= 1 else 1
    plt.xticks(list(df_tsg.index[::count]), rotation=45)
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[1])
    plt.plot(df_ts.index, df_ts['수익금합계'], linewidth=2, label='수익률', color='orange')
    if dict_cn is not None:
        plt.plot(df_kp.index, df_kp['종가'], linewidth=0.5, label='코스피', color='r')
        plt.plot(df_kd.index, df_kd['종가'], linewidth=0.5, label='코스닥', color='b')
    else:
        plt.plot(df_bc.index, df_bc['close'], linewidth=0.5, label='KRW-BTC', color='r')
    plt.title('지수비교' if dict_cn is not None else 'BTC비교')
    count = int(len(df_ts) / 20) if int(len(df_ts) / 20) >= 1 else 1
    plt.xticks(list(df_ts.index[::count]), rotation=45)
    plt.legend(loc='best')
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[2])
    plt.bar(df_st.index, df_st['이익금액'], label='이익금액', color='r')
    plt.bar(df_st.index, df_st['손실금액'], label='손실금액', color='b')
    plt.title('시간별 수익금')
    plt.xticks(list(df_st.index), rotation=45)
    plt.legend(loc='best')
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[3])
    plt.bar(wt_index, wt_datap, label='이익금액', color='r')
    plt.bar(wt_index, wt_datam, label='손실금액', color='b')
    plt.title('요일별 수익금')
    plt.xticks(wt_index)
    plt.legend(loc='best')
    plt.grid()
    plt.tight_layout()
    plt.savefig(f"{GRAPH_PATH}/{save_file_name}_.png")

    if buy_vars is None:
        plt.figure(f'{backname} 결과', figsize=(12, 10))
    else:
        plt.figure(f'{backname} 결과', figsize=(12, 12))
    gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[1, 4])
    # noinspection PyTypeChecker
    plt.subplot(gs[0])
    plt.plot(df_bct.index, df_bct['보유금액'], label='보유금액', color='g')
    plt.xticks([])
    if buy_vars is None:
        plt.xlabel('\n' + back_text + '\n' + label_text)
    else:
        plt.xlabel('\n' + back_text + '\n' + label_text + '\n\n' + buy_vars + '\n\n' + sell_vars)
    plt.legend(loc='best')
    plt.grid()
    # noinspection PyTypeChecker
    plt.subplot(gs[1])
    plt.bar(df_tsg.index, df_tsg['이익금액'], label='이익금액', color='r')
    plt.bar(df_tsg.index, df_tsg['손실금액'], label='손실금액', color='b')
    plt.plot(df_tsg.index, df_tsg['수익금합계480'], linewidth=0.5, label='수익금합계480', color='k')
    plt.plot(df_tsg.index, df_tsg['수익금합계240'], linewidth=0.5, label='수익금합계240', color='gray')
    plt.plot(df_tsg.index, df_tsg['수익금합계120'], linewidth=0.5, label='수익금합계120', color='b')
    plt.plot(df_tsg.index, df_tsg['수익금합계060'], linewidth=0.5, label='수익금합계60', color='g')
    plt.plot(df_tsg.index, df_tsg['수익금합계020'], linewidth=0.5, label='수익금합계20', color='r')
    plt.plot(df_tsg.index, df_tsg['수익금합계'], linewidth=2, label='수익금합계', color='orange')
    if gubun == '최적화':
        for i, endx in enumerate(endx_list):
            plt.axvline(x=endx, color='red' if i == 0 else 'green', linestyle='--')
        plt.axvspan(endx_list[0], df_tsg.index[-1], facecolor='gray', alpha=0.1)
    count = int(len(df_tsg) / 20) if int(len(df_tsg) / 20) >= 1 else 1
    plt.xticks(list(df_tsg.index[::count]), rotation=45)
    plt.legend(loc='upper left')
    plt.grid()
    plt.tight_layout()
    plt.savefig(f"{GRAPH_PATH}/{save_file_name}.png")

    teleQ.put(f'{backname} {save_file_name.split("_")[1]} 완료.')
    teleQ.put(f"{GRAPH_PATH}/{save_file_name}_.png")
    teleQ.put(f"{GRAPH_PATH}/{save_file_name}.png")

    # [2025-12-08] 분석 차트 생성 및 텔레그램 전송
    PltAnalysisCharts(df_tsg, save_file_name, teleQ)

    if not schedul and not plotgraph:
        plt.show()


def GetResultDataframe(ui_gubun, list_tsg, arry_bct):
    # [2025-12-08] 백테스팅 상세기록 테이블 확장 - 매수 시점 시장 데이터 추가
    # 확장된 데이터 여부 확인 (리스트가 비어있지 않고 첫 항목 길이로 판단)
    is_extended = len(list_tsg) > 0 and len(list_tsg[0]) > 14

    if is_extended:
        columns1 = [
            'index', '종목명', '시가총액' if ui_gubun != 'CF' else '포지션', '매수시간', '매도시간',
            '보유시간', '매수가', '매도가', '매수금액', '매도금액', '수익률', '수익금', '매도조건', '추가매수시간',
            '매수일자', '매수시', '매수분', '매수초',
            '매수등락율', '매수시가등락율', '매수당일거래대금', '매수체결강도',
            '매수전일비', '매수회전율', '매수전일동시간비',
            '매수고가', '매수저가', '매수고저평균대비등락율',
            '매수매도총잔량', '매수매수총잔량', '매수호가잔량비',
            '매수매도호가1', '매수매수호가1', '매수스프레드'
        ]
        columns2 = [
            '종목명', '시가총액' if ui_gubun != 'CF' else '포지션', '매수시간', '매도시간', '보유시간', '매수가', '매도가',
            '매수금액', '매도금액', '수익률', '수익금', '수익금합계', '매도조건', '추가매수시간',
            '매수일자', '매수시', '매수분', '매수초',
            '매수등락율', '매수시가등락율', '매수당일거래대금', '매수체결강도',
            '매수전일비', '매수회전율', '매수전일동시간비',
            '매수고가', '매수저가', '매수고저평균대비등락율',
            '매수매도총잔량', '매수매수총잔량', '매수호가잔량비',
            '매수매도호가1', '매수매수호가1', '매수스프레드'
        ]
    else:
        columns1 = [
            'index', '종목명', '시가총액' if ui_gubun != 'CF' else '포지션', '매수시간', '매도시간',
            '보유시간', '매수가', '매도가', '매수금액', '매도금액', '수익률', '수익금', '매도조건', '추가매수시간'
        ]
        columns2 = [
            '종목명', '시가총액' if ui_gubun != 'CF' else '포지션', '매수시간', '매도시간', '보유시간', '매수가', '매도가',
            '매수금액', '매도금액', '수익률', '수익금', '수익금합계', '매도조건', '추가매수시간'
        ]

    df_tsg = pd.DataFrame(list_tsg, columns=columns1)
    df_tsg.set_index('index', inplace=True)
    df_tsg.sort_index(inplace=True)
    df_tsg['수익금합계'] = df_tsg['수익금'].cumsum()
    df_tsg = df_tsg[columns2]
    arry_bct = arry_bct[arry_bct[:, 1] > 0]
    df_bct = pd.DataFrame(arry_bct[:, 1:], columns=['보유종목수', '보유금액'], index=arry_bct[:, 0])
    df_bct.index = df_bct.index.astype(str)
    return df_tsg, df_bct


def AddMdd(arry_tsg, result):
    """
    arry_tsg
    보유시간, 매도시간, 수익률, 수익금, 수익금합계
      0       1       2       3      4
    """
    try:
        array = arry_tsg[:, 4]
        lower = np.argmax(np.maximum.accumulate(array) - array)
        upper = np.argmax(array[:lower])
        mdd   = round(abs(array[upper] - array[lower]) / (array[upper] + result[10]) * 100, 2)
        mdd_  = int(abs(array[upper] - array[lower]))
    except:
        mdd   = abs(result[7])
        mdd_  = abs(result[8])
    result = result + (mdd, mdd_)
    return result


@jit(nopython=True, cache=True)
def GetBackResult(arry_tsg, arry_bct, betting, ui_gubun, day_count):
    """ dtype = 'float64'
    arry_tsg
    보유시간, 매도시간, 수익률, 수익금, 수익금합계
      0       1       2       3      4
    arry_bct
    체결시간, 보유중목수, 보유금액
      0         1        2
    """
    tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    tc = len(arry_tsg)
    if tc > 0:
        arry_p = arry_tsg[arry_tsg[:, 3] >= 0]
        arry_m = arry_tsg[arry_tsg[:, 3] < 0]
        atc    = round(tc / day_count, 1)
        pc     = len(arry_p)
        mc     = len(arry_m)
        wr     = round(pc / tc * 100, 2)
        ah     = round(arry_tsg[:, 0].sum() / tc, 2)
        app    = round(arry_tsg[:, 2].sum() / tc, 2)
        tsg    = int(arry_tsg[:, 3].sum())
        appp   = arry_p[:, 2].mean() if len(arry_p) > 0 else 0
        ampp   = abs(arry_m[:, 2].mean()) if len(arry_m) > 0 else 0
        try:    mhct = int(arry_bct[int(len(arry_bct) * 0.01):, 1].max())
        except: mhct = 0
        try:    seed = int(arry_bct[int(len(arry_bct) * 0.01):, 2].max())
        except: seed = betting
        tpp    = round(tsg / (seed if seed != 0 else betting) * 100, 2)
        cagr   = round(tpp / day_count * (250 if ui_gubun == 'S' else 365), 2)
        tpi    = round(wr / 100 * (1 + appp / ampp), 2) if ampp != 0 else 1.0

    return tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi


def GetIndicator(mc, mh, ml, mv, k):
    AD, ADOSC, ADXR, APO, AROOND, AROONU, ATR, BBU, BBM, BBL, CCI, DIM, DIP, MACD, MACDS, MACDH, MFI, MOM, OBV, PPO, \
        ROC, RSI, SAR, STOCHSK, STOCHSD, STOCHFK, STOCHFD, WILLR = \
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    try:    AD                     = stream.AD(      mh, ml, mc, mv)
    except: AD                     = 0
    if k[0] != 0:
        try:    ADOSC              = stream.ADOSC(   mh, ml, mc, mv, fastperiod=k[0], slowperiod=k[1])
        except: ADOSC              = 0
    if k[2] != 0:
        try:    ADXR               = stream.ADXR(    mh, ml, mc,     timeperiod=k[2])
        except: ADXR               = 0
    if k[3] != 0:
        try:    APO                = stream.APO(     mc,             fastperiod=k[3], slowperiod=k[4], matype=k[5])
        except: APO                = 0
    if k[6] != 0:
        try:    AROOND, AROONU     = stream.AROON(   mh, ml,         timeperiod=k[6])
        except: AROOND, AROONU     = 0, 0
    if k[7] != 0:
        try:    ATR                = stream.ATR(     mh, ml, mc,     timeperiod=k[7])
        except: ATR                = 0
    if k[8] != 0:
        try:    BBU, BBM, BBL      = stream.BBANDS(  mc,             timeperiod=k[8], nbdevup=k[9], nbdevdn=k[10], matype=k[11])
        except: BBU, BBM, BBL      = 0, 0, 0
    if k[12] != 0:
        try:    CCI                = stream.CCI(     mh, ml, mc,     timeperiod=k[12])
        except: CCI                = 0
    if k[13] != 0:
        try:    DIM, DIP           = stream.MINUS_DI(mh, ml, mc,     timeperiod=k[13]), stream.PLUS_DI( mh, ml, mc, timeperiod=k[13])
        except: DIM, DIP           = 0, 0
    if k[14] != 0:
        try:    MACD, MACDS, MACDH = stream.MACD(    mc,             fastperiod=k[14], slowperiod=k[15], signalperiod=k[16])
        except: MACD, MACDS, MACDH = 0, 0, 0
    if k[17] != 0:
        try:    MFI                = stream.MFI(     mh, ml, mc, mv, timeperiod=k[17])
        except: MFI                = 0
    if k[18] != 0:
        try:    MOM                = stream.MOM(     mc,             timeperiod=k[18])
        except: MOM                = 0
    try:    OBV                    = stream.OBV(     mc, mv)
    except: OBV                    = 0
    if k[19] != 0:
        try:    PPO                = stream.PPO(     mc,             fastperiod=k[19], slowperiod=k[20], matype=k[21])
        except: PPO                = 0
    if k[22] != 0:
        try:    ROC                = stream.ROC(     mc,             timeperiod=k[22])
        except: ROC                = 0
    if k[23] != 0:
        try:    RSI                = stream.RSI(     mc,             timeperiod=k[23])
        except: RSI                = 0
    if k[24] != 0:
        try:    SAR                = stream.SAR(     mh, ml,         acceleration=k[24], maximum=k[25])
        except: SAR                = 0
    if k[26] != 0:
        try:    STOCHSK, STOCHSD   = stream.STOCH(   mh, ml, mc,     fastk_period=k[26], slowk_period=k[27], slowk_matype=k[28], slowd_period=k[29], slowd_matype=k[30])
        except: STOCHSK, STOCHSD   = 0, 0
    if k[31] != 0:
        try:    STOCHFK, STOCHFD   = stream.STOCHF(  mh, ml, mc,     fastk_period=k[31], fastd_period=k[32], fastd_matype=k[33])
        except: STOCHFK, STOCHFD   = 0, 0
    if k[34] != 0:
        try:    WILLR              = stream.WILLR(   mh, ml, mc,     timeperiod=k[34])
        except: WILLR              = 0
    return AD, ADOSC, ADXR, APO, AROOND, AROONU, ATR, BBU, BBM, BBL, CCI, DIM, DIP, MACD, MACDS, MACDH, MFI, MOM, OBV, PPO, ROC, RSI, SAR, STOCHSK, STOCHSD, STOCHFK, STOCHFD, WILLR


# [2025-12-08] 백테스팅 상세기록 테이블 확장 - 분석 차트 생성 함수
def PltAnalysisCharts(df_tsg, save_file_name, teleQ):
    """
    확장된 상세기록 데이터를 기반으로 분석 차트를 생성하고 텔레그램으로 전송

    Args:
        df_tsg: 확장된 상세기록 DataFrame (34개 컬럼)
        save_file_name: 저장 파일명
        teleQ: 텔레그램 전송 큐
    """
    # 확장 컬럼 존재 여부 확인
    extended_columns = ['매수시', '매수등락율', '매수체결강도', '매수당일거래대금', '시가총액']
    has_extended = all(col in df_tsg.columns for col in extended_columns)

    if not has_extended or len(df_tsg) < 5:
        return  # 데이터가 부족하거나 확장 컬럼이 없으면 건너뜀

    try:
        # 한글 폰트 설정
        font_path = 'C:/Windows/Fonts/malgun.ttf'
        try:
            font_manager.fontManager.addfont(font_path)
            plt.rcParams['font.family'] = 'Malgun Gothic'
        except:
            pass
        plt.rcParams['axes.unicode_minus'] = False

        fig = plt.figure(figsize=(16, 20))
        fig.suptitle(f'백테스팅 분석 차트 - {save_file_name}', fontsize=14, fontweight='bold')

        gs = gridspec.GridSpec(4, 2, figure=fig, hspace=0.35, wspace=0.25)

        # 색상 정의
        color_profit = '#2ECC71'  # 녹색 (이익)
        color_loss = '#E74C3C'    # 빨간색 (손실)
        color_bar = '#3498DB'     # 파란색

        # ============ Chart 1: 시간대별 수익 분포 ============
        ax1 = fig.add_subplot(gs[0, 0])
        df_hour = df_tsg.groupby('매수시').agg({'수익금': 'sum', '수익률': 'mean'}).reset_index()
        colors = [color_profit if x >= 0 else color_loss for x in df_hour['수익금']]
        bars = ax1.bar(df_hour['매수시'], df_hour['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax1.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax1.set_xlabel('매수 시간대 (시)')
        ax1.set_ylabel('총 수익금')
        ax1.set_title('시간대별 수익금 분포')
        ax1.set_xticks(range(9, 16))
        for bar, val in zip(bars, df_hour['수익금']):
            if abs(val) > 0:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{val/10000:.0f}만', ha='center', va='bottom' if val >= 0 else 'top', fontsize=8)

        # ============ Chart 2: 등락율별 수익 분포 ============
        ax2 = fig.add_subplot(gs[0, 1])
        bins = [0, 5, 10, 15, 20, 30, 100]
        labels = ['0-5%', '5-10%', '10-15%', '15-20%', '20-30%', '30%+']
        df_tsg['등락율구간'] = pd.cut(df_tsg['매수등락율'], bins=bins, labels=labels, right=False)
        df_rate = df_tsg.groupby('등락율구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_rate.columns = ['등락율구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_rate))
        colors = [color_profit if x >= 0 else color_loss for x in df_rate['수익금']]
        ax2.bar(x, df_rate['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax2.set_xlabel('매수 등락율 구간')
        ax2.set_ylabel('총 수익금')
        ax2.set_title('등락율 구간별 수익금 분포')
        ax2.set_xticks(x)
        ax2.set_xticklabels(df_rate['등락율구간'], rotation=45, ha='right')

        # 거래횟수 표시
        ax2_twin = ax2.twinx()
        ax2_twin.plot(x, df_rate['거래횟수'], 'o-', color='orange', linewidth=2, markersize=6, label='거래횟수')
        ax2_twin.set_ylabel('거래횟수', color='orange')
        ax2_twin.tick_params(axis='y', labelcolor='orange')

        # ============ Chart 3: 체결강도별 수익 분포 ============
        ax3 = fig.add_subplot(gs[1, 0])
        bins_ch = [0, 80, 100, 120, 150, 200, 500]
        labels_ch = ['~80', '80-100', '100-120', '120-150', '150-200', '200+']
        df_tsg['체결강도구간'] = pd.cut(df_tsg['매수체결강도'], bins=bins_ch, labels=labels_ch, right=False)
        df_ch = df_tsg.groupby('체결강도구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_ch.columns = ['체결강도구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_ch))
        colors = [color_profit if x >= 0 else color_loss for x in df_ch['수익금']]
        ax3.bar(x, df_ch['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax3.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax3.set_xlabel('매수 체결강도 구간')
        ax3.set_ylabel('총 수익금')
        ax3.set_title('체결강도 구간별 수익금 분포')
        ax3.set_xticks(x)
        ax3.set_xticklabels(df_ch['체결강도구간'], rotation=45, ha='right')

        # 승률 계산 및 표시
        ax3_twin = ax3.twinx()
        win_rates = []
        for grp in df_ch['체결강도구간']:
            grp_data = df_tsg[df_tsg['체결강도구간'] == grp]
            if len(grp_data) > 0:
                wr = (grp_data['수익금'] > 0).sum() / len(grp_data) * 100
                win_rates.append(wr)
            else:
                win_rates.append(0)
        ax3_twin.plot(x, win_rates, 's--', color='purple', linewidth=2, markersize=6, label='승률')
        ax3_twin.set_ylabel('승률 (%)', color='purple')
        ax3_twin.tick_params(axis='y', labelcolor='purple')
        ax3_twin.set_ylim(0, 100)

        # ============ Chart 4: 거래대금별 수익 분포 ============
        ax4 = fig.add_subplot(gs[1, 1])
        # 거래대금을 로그 스케일 구간으로 나눔
        df_tsg['거래대금구간'] = pd.cut(df_tsg['매수당일거래대금'],
                                      bins=[0, 100, 500, 1000, 5000, 10000, float('inf')],
                                      labels=['~100억', '100-500억', '500-1000억', '1000-5000억', '5000억-1조', '1조+'])
        df_money = df_tsg.groupby('거래대금구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_money.columns = ['거래대금구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_money))
        colors = [color_profit if x >= 0 else color_loss for x in df_money['수익금']]
        ax4.bar(x, df_money['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax4.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax4.set_xlabel('매수 당일거래대금 구간')
        ax4.set_ylabel('총 수익금')
        ax4.set_title('거래대금 구간별 수익금 분포')
        ax4.set_xticks(x)
        ax4.set_xticklabels(df_money['거래대금구간'], rotation=45, ha='right')

        # ============ Chart 5: 시가총액별 수익 분포 ============
        ax5 = fig.add_subplot(gs[2, 0])
        df_tsg['시총구간'] = pd.cut(df_tsg['시가총액'],
                                   bins=[0, 1000, 3000, 10000, 50000, float('inf')],
                                   labels=['~1000억', '1000-3000억', '3000억-1조', '1-5조', '5조+'])
        df_cap = df_tsg.groupby('시총구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_cap.columns = ['시총구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_cap))
        colors = [color_profit if x >= 0 else color_loss for x in df_cap['수익금']]
        ax5.bar(x, df_cap['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax5.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax5.set_xlabel('시가총액 구간')
        ax5.set_ylabel('총 수익금')
        ax5.set_title('시가총액 구간별 수익금 분포')
        ax5.set_xticks(x)
        ax5.set_xticklabels(df_cap['시총구간'], rotation=45, ha='right')

        # ============ Chart 6: 보유시간별 수익 분포 ============
        ax6 = fig.add_subplot(gs[2, 1])
        df_tsg['보유시간구간'] = pd.cut(df_tsg['보유시간'],
                                      bins=[0, 60, 180, 300, 600, 1800, float('inf')],
                                      labels=['~1분', '1-3분', '3-5분', '5-10분', '10-30분', '30분+'])
        df_hold = df_tsg.groupby('보유시간구간', observed=True).agg({
            '수익금': 'sum', '수익률': 'mean', '종목명': 'count'
        }).reset_index()
        df_hold.columns = ['보유시간구간', '수익금', '평균수익률', '거래횟수']

        x = range(len(df_hold))
        colors = [color_profit if x >= 0 else color_loss for x in df_hold['수익금']]
        ax6.bar(x, df_hold['수익금'], color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
        ax6.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax6.set_xlabel('보유시간 구간')
        ax6.set_ylabel('총 수익금')
        ax6.set_title('보유시간 구간별 수익금 분포')
        ax6.set_xticks(x)
        ax6.set_xticklabels(df_hold['보유시간구간'], rotation=45, ha='right')

        # ============ Chart 7: 상관관계 히트맵 ============
        ax7 = fig.add_subplot(gs[3, 0])
        corr_columns = ['수익률', '매수등락율', '매수체결강도', '매수회전율', '매수전일비', '보유시간']
        available_cols = [col for col in corr_columns if col in df_tsg.columns]

        if len(available_cols) >= 3:
            df_corr = df_tsg[available_cols].corr()
            im = ax7.imshow(df_corr.values, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
            ax7.set_xticks(range(len(available_cols)))
            ax7.set_yticks(range(len(available_cols)))
            ax7.set_xticklabels(available_cols, rotation=45, ha='right', fontsize=9)
            ax7.set_yticklabels(available_cols, fontsize=9)
            ax7.set_title('변수 간 상관관계')

            # 상관계수 값 표시
            for i in range(len(available_cols)):
                for j in range(len(available_cols)):
                    text = ax7.text(j, i, f'{df_corr.values[i, j]:.2f}',
                                   ha='center', va='center', color='black', fontsize=8)

            plt.colorbar(im, ax=ax7, shrink=0.8)

        # ============ Chart 8: 산점도 (등락율 vs 수익률) ============
        ax8 = fig.add_subplot(gs[3, 1])
        colors = [color_profit if x >= 0 else color_loss for x in df_tsg['수익률']]
        ax8.scatter(df_tsg['매수등락율'], df_tsg['수익률'], c=colors, alpha=0.5, s=20, edgecolors='none')
        ax8.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
        ax8.axvline(x=df_tsg['매수등락율'].mean(), color='blue', linestyle=':', linewidth=0.8, alpha=0.5)
        ax8.set_xlabel('매수 등락율 (%)')
        ax8.set_ylabel('수익률 (%)')
        ax8.set_title('등락율 vs 수익률 산점도')

        # 추세선 추가
        if len(df_tsg) > 10:
            z = np.polyfit(df_tsg['매수등락율'], df_tsg['수익률'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(df_tsg['매수등락율'].min(), df_tsg['매수등락율'].max(), 100)
            ax8.plot(x_line, p(x_line), 'b--', linewidth=1, alpha=0.7, label=f'추세선')
            ax8.legend(fontsize=8)

        # 저장 및 전송
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        analysis_path = f"{GRAPH_PATH}/{save_file_name}_analysis.png"
        plt.savefig(analysis_path, dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        # 텔레그램 전송
        if teleQ is not None:
            teleQ.put(analysis_path)

    except Exception as e:
        print_exc()
        try:
            plt.close('all')
        except:
            pass
