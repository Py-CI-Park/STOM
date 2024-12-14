import sys
import random
import pyupbit
import sqlite3
import operator
import telegram
import numpy as np
import pandas as pd
from traceback import print_exc
from matplotlib import pyplot as plt
from matplotlib import font_manager, gridspec
from utility.static import strp_time, strf_time, timedelta_sec
from utility.setting import ui_num, GRAPH_PATH, columns_btf, columns_bt, DICT_SET, DB_SETTING

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
            '매수주문시간': strp_time('%Y%m%d', '20000101'),
            '매도주문시간': strp_time('%Y%m%d', '20000101')
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
    last      = len(days) - 1
    like_text = '( '
    for i, day in enumerate(days):
        if i != last:
            like_text += f"`index` LIKE '{day}%' or "
        else:
            like_text += f"`index` LIKE '{day}%' )"
    query = f"SELECT * FROM '{code}' WHERE {like_text} and " \
            f"`index` % 1000000 >= {starttime} and " \
            f"`index` % 1000000 <= {endtime}"
    return query


def GetBackloadDayQuery(day, code, starttime, endtime):
    query = f"SELECT * FROM '{code}' WHERE " \
            f"`index` LIKE '{day}%' and " \
            f"`index` % 1000000 >= {starttime} and " \
            f"`index` % 1000000 <= {endtime}"
    return query


def GetMoneytopQuery(gubun, startday, endday, starttime, endtime):
    if gubun == 'S' and starttime < 90030:
        query = f"SELECT * FROM moneytop WHERE " \
                f"`index` >= {startday * 1000000} and " \
                f"`index` <= {endday * 1000000 + 240000} and " \
                f"`index` % 1000000 >= {90030} and " \
                f"`index` % 1000000 <= {endtime}"
    else:
        query = f"SELECT * FROM moneytop WHERE " \
                f"`index` >= {startday * 1000000} and " \
                f"`index` <= {endday * 1000000 + 240000} and " \
                f"`index` % 1000000 >= {starttime} and " \
                f"`index` % 1000000 <= {endtime}"
    return query


def AddAvgData(df, r, avg_list):
    df['이평60'] = df['현재가'].rolling(window=60).mean().round(r)
    df['이평300'] = df['현재가'].rolling(window=300).mean().round(r)
    df['이평600'] = df['현재가'].rolling(window=600).mean().round(r)
    df['이평1200'] = df['현재가'].rolling(window=1200).mean().round(r)
    for avg in avg_list:
        df[f'최고현재가{avg}'] = df['현재가'].rolling(window=avg).max()
        df[f'최저현재가{avg}'] = df['현재가'].rolling(window=avg).min()
        df[f'체결강도평균{avg}'] = df['체결강도'].rolling(window=avg).mean()
        df[f'최고체결강도{avg}'] = df['체결강도'].rolling(window=avg).max()
        df[f'최저체결강도{avg}'] = df['체결강도'].rolling(window=avg).min()
        df[f'최고초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).max()
        df[f'최고초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).max()
        df[f'누적초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).sum()
        df[f'누적초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).sum()
        df[f'초당거래대금평균{avg}'] = df['초당거래대금'].rolling(window=avg).mean()
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
    buy_setting  = str(list(df1.iloc[0]))
    sell_setting = str(list(df2.iloc[0]))
    return buy_setting, sell_setting


def GetBuyStg(buystg):
    buystg = buystg.split('if 매수:')[0] + 'if 매수:\n    self.Buy()'
    try:
        buystg = compile(buystg, '<string>', 'exec')
    except:
        buystg = None
        print_exc()
    return buystg


def GetSellStg(sellstg):
    sellstg = 'sell_cond = 0\n' + sellstg.split('if 매도:')[0] + 'if 매도:\n    self.Sell(sell_cond)'
    sellstg, dict_cond = SetSellCond(sellstg.split('\n'))
    try:
        sellstg = compile(sellstg, '<string>', 'exec')
    except:
        sellstg = None
        print_exc()
    return sellstg, dict_cond


def GetBuyConds(buy_conds):
    buy_conds = 'if ' + ':\n    매수 = False\nelif '.join(buy_conds) + ':\n    매수 = False\nif 매수:\n    self.Buy()'
    try:
        buy_conds = compile(buy_conds, '<string>', 'exec')
    except:
        buy_conds = None
        print_exc()
    return buy_conds


def GetSellConds(sell_conds):
    sell_conds = 'sell_cond = 0\nif ' + ':\n    매도 = True\nelif '.join(sell_conds) + ':\n    매도 = True\nif 매도:\n    self.Sell(sell_cond)'
    sell_conds, dict_cond = SetSellCond(sell_conds.split('\n'))
    try:
        sell_conds = compile(sell_conds, '<string>', 'exec')
    except:
        sell_conds = None
        print_exc()
    return sell_conds, dict_cond


def SetSellCond(selllist):
    count     = 1
    sellstg   = ''
    dict_cond = {0: '전략종료청산', 100: '분할매도', 200: '손절청산'}
    for i, text in enumerate(selllist):
        if '#' not in text and ('매도 = True' in text or '매도= True' in text or '매도 =True' in text or '매도=True' in text):
            dict_cond[count] = selllist[i - 1]
            sellstg = f"{sellstg}{text.split('매도')[0]}sell_cond = {count}\n"
            count  += 1
        if text != '':
            sellstg = f"{sellstg}{text}\n"
    return sellstg, dict_cond


def GetBuyStgFuture(buystg):
    buystg = buystg.split('if BUY_LONG or SELL_SHORT:')[0] + 'if BUY_LONG:\n    self.Buy("BUY_LONG")\nelif SELL_SHORT:\n    self.Buy("SELL_SHORT")'
    try:
        buystg = compile(buystg, '<string>', 'exec')
    except:
        buystg = None
        print_exc()
    return buystg


def GetSellStgFuture(sellstg):
    sellstg = 'sell_cond = 0\n' + sellstg.split("if (포지션 == 'LONG' and SELL_LONG) or (포지션 == 'SHORT' and BUY_SHORT):")[0] + "if 포지션 == 'LONG' and SELL_LONG:\n    self.Sell('SELL_LONG', sell_cond)\nelif 포지션 == 'SHORT' and BUY_SHORT:\n    self.Sell('BUY_SHORT', sell_cond)"
    sellstg, dict_cond = SetSellCond(sellstg.split('\n'))
    try:
        sellstg = compile(sellstg, '<string>', 'exec')
    except:
        sellstg = None
        print_exc()
    return sellstg, dict_cond


def GetBuyCondsFuture(is_long, buy_conds):
    if is_long:
        buy_conds = 'if ' + ':\n    BUY_LONG = False\nelif '.join(buy_conds) + ':\n    BUY_LONG = False\nif BUY_LONG:\n    self.Buy("BUY_LONG")'
    else:
        buy_conds = 'if ' + ':\n    SELL_SHORT = False\nelif '.join(buy_conds) + ':\n    SELL_SHORT = False\nif SELL_SHORT:\n    self.Buy("SELL_SHORT")'
    try:
        buy_conds = compile(buy_conds, '<string>', 'exec')
    except:
        buy_conds = None
        print_exc()
    return buy_conds


def GetSellCondsFuture(is_long, sell_conds):
    if is_long:
        sell_conds = 'sell_cond = 0\nif ' + ':\n    SELL_LONG = True\nelif '.join(sell_conds) + ':\n    SELL_LONG = True\nif SELL_LONG:\n    self.Sell("SELL_LONG", sell_cond)'
    else:
        sell_conds = 'sell_cond = 0\nif ' + ':\n    BUY_SHORT = True\nelif '.join(sell_conds) + ':\n    BUY_SHORT = True\nif BUY_SHORT:\n    self.Sell("BUY_SHORT", sell_cond)'
    sell_conds, dict_cond = SetSellCondFuture(sell_conds.split('\n'))
    try:
        sell_conds = compile(sell_conds, '<string>', 'exec')
    except:
        sell_conds = None
        print_exc()
    return sell_conds, dict_cond


def SetSellCondFuture(selllist):
    count     = 1
    sellstg   = ''
    dict_cond = {0: '전략종료청산', 100: '분할매도', 200: '손절청산'}
    for i, text in enumerate(selllist):
        if '#' not in text:
            if 'SELL_LONG = True' in text or 'SELL_LONG= True' in text or 'SELL_LONG =True' in text or 'SELL_LONG=True' in text:
                dict_cond[count] = selllist[i - 1]
                sellstg = f"{sellstg}{text.split('SELL_LONG')[0]}sell_cond = {count}\n"
                count  += 1
            elif 'BUY_SHORT = True' in text or 'BUY_SHORT= True' in text or 'BUY_SHORT =True' in text or 'BUY_SHORT=True' in text:
                dict_cond[count] = selllist[i - 1]
                sellstg = f"{sellstg}{text.split('BUY_SHORT')[0]}sell_cond = {count}\n"
                count  += 1
        if text != '':
            sellstg = f"{sellstg}{text}\n"
    return sellstg, dict_cond


def SendTextAndStd(back_list, std_list, betting, dict_train, dict_valid=None, exponential=False):
    gubun, ui_gubun, wq, mq, stdp, optistd, vars_turn, vars_key, vars_list, startday, endday = back_list
    if gubun in ['최적화', '최적화테스트']:
        text1 = GetText1(vars_turn, vars_list)
    elif gubun == 'GA최적화':
        text1 = f'<font color=white> V{vars_list} </font>'
    elif gubun == '전진분석':
        text1 = f'<font color=#f78645>[IN] P[{startday}~{endday}]</font>{GetText1(vars_turn, vars_list)}'
    else:
        text1 = ''

    stdp_ = 0
    if dict_valid is not None:
        duple_train = sorted(dict_train.items(), key=operator.itemgetter(0))
        duple_valid = sorted(dict_valid.items(), key=operator.itemgetter(0))
        train_text = []
        valid_text = []
        train_data = []
        valid_data = []

        for k, v in duple_train:
            text2, std = GetText2(f'TRAIN{k + 1}', optistd, std_list, betting, v)
            train_text.append(text2)
            train_data.append(std)
        for k, v in duple_valid:
            text2, std = GetText2(f'VALID{k + 1}', optistd, std_list, betting, v)
            valid_text.append(text2)
            valid_data.append(std)

        std = GetOptiValidStd(train_data, valid_data, optistd, betting, exponential)
        text3, stdp_ = GetText3(True, std, stdp)

        wq.put([ui_num[f'{ui_gubun}백테스트'], f'{text1}{text3}'])
        for text in train_text:
            wq.put([ui_num[f'{ui_gubun}백테스트'], text])
        for text in valid_text:
            wq.put([ui_num[f'{ui_gubun}백테스트'], text])
    elif dict_train is not None:
        if gubun in ['GA최적화', '조건최적화']:
            text2, std   = GetText2('', optistd, std_list, betting, dict_train)
            text3, stdp_ = GetText3(False, std, stdp)
            text2 = f'{text2}{text3}'
        elif gubun == '최적화테스트':
            text2, std = GetText2('TEST', optistd, std_list, betting, dict_train)
        else:
            text2, std = GetText2('TOTAL', optistd, std_list, betting, dict_train)
        wq.put([ui_num[f'{ui_gubun}백테스트'], f'{text1}{text2}'])
    else:
        std = 0
        text2 = '매수전략을 만족하는 경우가 없어 결과를 표시할 수 없습니다.'
        wq.put([ui_num[f'{ui_gubun}백테스트'], f'{text1}{text2}'])

    if vars_turn >= -1:
        mq.put([std, vars_key])
    return stdp_


def GetText1(vars_turn, vars_list):
    prev_vars, curr_vars, next_vars = '', '', ''
    if vars_turn < 0:
        next_vars = f'<font color=#6eff6e> V{vars_list} </font>'
    else:
        prev_vars = f' V{vars_list[:vars_turn]}'.split(']')[0]
        prev_vars = f'<font color=white>{prev_vars}</font>' if vars_turn == 0 else f'<font color=white>{prev_vars}, </font>'
        curr_vars = f'<font color=#6eff6e>{vars_list[vars_turn]}</font>'
        next_vars = f'{vars_list[vars_turn + 1:]}'.split('[')[1]
        if next_vars != ']': next_vars = f', {next_vars}'
        next_vars = f'<font color=white>{next_vars} </font>'
    return f'{prev_vars}{curr_vars}{next_vars}'


def GetText2(gubun, optistd, std_list, betting, result):
    tc, atc, pc, mc, wr, ah, ap, tsp, tsg, mhct, onegm, cagr, tpi, mdd = result
    if tsp < 0 < tsg: tsg = -2147483648
    mdd_ = f'{mdd:,.0f}' if 'G' in optistd else f'{mdd:,.2f}%'
    text = f'{gubun} TC[{tc:,.0f}] ATC[{atc:,.1f}] MH[{mhct}] WR[{wr:,.2f}%] MDD[{mdd_}] CAGR[{cagr:,.2f}] TPI[{tpi:,.2f}] AP[{ap:,.2f}%] TP[{tsp:,.2f}%] TG[{tsg:,.0f}]'
    std, text = GetOptiStdText(optistd, std_list, betting, result, text)
    text = f'<font color=white>{text}</font>' if tsg >= 0 else f'<font color=#96969b>{text}</font>'
    return text, std


def GetText3(gubun, std, stdp):
    text = f'<font color=#f78645>MERGE[{std:,.2f}]</font>' if gubun else ''
    if std >= stdp:
        text = f'{text}<font color=#6eff6e>[기준값갱신]</font>' if std > stdp else f'{text}<font color=white>[기준값동일]</font>'
        stdp = std
    return text, stdp


def GetOptiValidStd(train_data, valid_data, optistd, betting, exponential):
    std = 0
    count = len(train_data)
    """
    가중치(exponential) 예제
    10개 : 2.00, 1.80, 1.60, 1.40, 1.20, 1.00, 0.80, 0.60, 0.40, 0.20
    8개  : 2.00, 1.75, 1.50, 1.25, 1.00, 0.75, 0.50, 0.25
    7개  : 2.00, 1.71, 1.42, 1.14, 0.86, 0.57, 0.29
    6개  : 2.00, 1.66, 1.33, 1.00, 0.66, 0.33
    5개  : 2.00, 1.60, 1.20, 0.80, 0.40
    4개  : 2.00, 1.50, 1.00, 0.50
    3개  : 2.00, 1.33, 0.66
    2개  : 2.00, 1.0
    """
    for i in range(count):
        ex   = (count - i) * 2 / count
        std_ = train_data[i] * valid_data[i] * ex if exponential and count > 1 else train_data[i] * valid_data[i]
        std  = std - std_ if train_data[i] < 0 and valid_data[i] < 0 else std + std_
    if optistd == 'TP':    std = round(std / count, 2)
    elif optistd == 'TG':  std = round(std / count / betting, 2)
    elif optistd == 'PM':  std = round(std / count, 2)
    elif optistd == 'P2M': std = round(std / count, 2)
    elif optistd == 'PAM': std = round(std / count, 2)
    elif optistd == 'PWM': std = round(std / count, 2)
    elif optistd == 'GM':  std = round(std / count, 2)
    elif optistd == 'G2M': std = round(std / count, 2)
    elif optistd == 'GAM': std = round(std / count, 2)
    elif optistd == 'GWM': std = round(std / count, 2)
    return std


def GetOptiStdText(optistd, std_list, betting, result, pre_text):
    mdd_low, mdd_high, mhct_low, mhct_high, wr_low, wr_high, ap_low, ap_high, atc_low, atc_high, cagr_low, cagr_high, tpi_low, tpi_high = std_list
    tc, atc, pc, mc, wr, ah, ap, tsp, tsg, mhct, onegm, cagr, tpi, mdd = result
    mdd_ = round(mdd / tsg * 100, 2) if 'G' in optistd and tsg != 0 else mdd
    std_true = mdd_low <= mdd_ <= mdd_high and mhct_low <= mhct <= mhct_high and wr_low <= wr <= wr_high and \
        ap_low <= ap <= ap_high and atc_low <= atc <= atc_high and cagr_low <= cagr <= cagr_high and tpi_low <= tpi <= tpi_high
    std, pm, p2m, pam, pwm, gm, g2m, gam, gwm, text = 0, 0, 0, 0, 0, 0, 0, 0, 0, ''
    if tc > 0:
        if 'TRAIN' in pre_text:
            if 'P' in optistd:
                if optistd == 'TP':
                    std = tsp if std_true else 0
                elif optistd == 'PM':
                    std = pm = round(tsp / mdd, 2) if std_true else 0
                elif optistd == 'P2M':
                    std = p2m = round(tsp * tsp / mdd / 100, 2) if std_true else 0
                elif optistd == 'PAM':
                    std = pam = round(tsp * ap / mdd, 2) if std_true else 0
                elif optistd == 'PWM':
                    std = pwm = round(tsp * wr / mdd / 100, 2) if std_true else 0
            elif 'G' in optistd:
                if optistd == 'TG':
                    std = tsg if std_true else 0
                elif optistd == 'GM':
                    std = gm = round(tsg / mdd, 2) if std_true else 0
                elif optistd == 'G2M':
                    std = g2m = round(tsg * tsg / mdd / betting, 2) if std_true else 0
                elif optistd == 'GAM':
                    std = gam = round(tsg * ap / mdd, 2) if std_true else 0
                elif optistd == 'GWM':
                    std = gwm = round(tsg * wr / mdd / 100, 2) if std_true else 0
        else:
            if 'P' in optistd:
                if optistd == 'TP':
                    std = tsp
                elif optistd == 'PM':
                    std = pm = round(tsp / mdd, 2)
                elif optistd == 'P2M':
                    std = p2m = round(tsp * tsp / mdd / 100, 2)
                elif optistd == 'PAM':
                    std = pam = round(tsp * ap / mdd, 2)
                elif optistd == 'PWM':
                    std = pwm = round(tsp * wr / mdd / 100, 2)
            elif 'G' in optistd:
                if optistd == 'TG':
                    std = tsg
                elif optistd == 'GM':
                    std = gm = round(tsg / mdd, 2)
                elif optistd == 'G2M':
                    std = g2m = round(tsg * tsg / mdd / betting, 2)
                elif optistd == 'GAM':
                    std = gam = round(tsg * ap / mdd, 2)
                elif optistd == 'GWM':
                    std = gwm = round(tsg * wr / mdd / 100, 2)

    if optistd == 'TP':    text = pre_text
    elif optistd == 'TG':  text = pre_text
    elif optistd == 'PM':  text = f'{pre_text} PM[{pm:.2f}]'
    elif optistd == 'P2M': text = f'{pre_text} P2M[{p2m:.2f}]'
    elif optistd == 'PAM': text = f'{pre_text} PAM[{pam:.2f}]'
    elif optistd == 'PWM': text = f'{pre_text} PWM[{pwm:.2f}]'
    elif optistd == 'GM':  text = f'{pre_text} GM[{gm:.2f}]'
    elif optistd == 'G2M': text = f'{pre_text} G2M[{g2m:.2f}]'
    elif optistd == 'GAM': text = f'{pre_text} GAM[{gam:.2f}]'
    elif optistd == 'GWM': text = f'{pre_text} GWM[{gwm:.2f}]'
    return std, text


def GetBackResult(df_tsg, df_bct, betting, optistd, day_count):
    tc = len(df_tsg)
    if tc > 0:
        atc = round(tc / day_count, 1)
        pc  = len(df_tsg[df_tsg['수익률'] >= 0])
        mc  = len(df_tsg[df_tsg['수익률'] < 0])
        wr  = round(pc / tc * 100, 2)
        ah  = round(df_tsg['보유시간'].sum() / tc, 2)
        ap  = round(df_tsg['수익률'].sum() / tc, 2)
        tsg = int(df_tsg['수익금'].sum())
        tpg = df_tsg[df_tsg['수익률'] >= 0]['수익률'].mean()
        tmg = abs(df_tsg[df_tsg['수익률'] < 0]['수익률'].mean())

        df_bct = df_bct.sort_values(by=['보유종목수'], ascending=False)
        mhct   = df_bct['보유종목수'].iloc[int(len(df_bct) * 0.01):].max()
        onegm  = int(betting * mhct) if int(betting * mhct) > betting else betting
        tsp    = round(tsg / onegm * 100, 2)
        cname  = df_tsg['종목명'].iloc[0]
        cagr   = round(tsp / day_count * (365 if 'KRW' in cname or 'USDT' in cname else 250), 2)
        tpi    = round(wr / 100 * (1 + tpg / tmg), 2)

        df_bct.index = df_bct.index.astype(str)
        df_bct.sort_index(inplace=True)
        df_tsg['수익금합계'] = df_tsg['수익금'].cumsum()
        df_tsg[['수익금합계']] = df_tsg[['수익금합계']].astype(float)

        columns = columns_btf if '포지션' in df_tsg.columns else columns_bt
        df_tsg = df_tsg[columns]

        try:
            array = np.array(df_tsg['수익금합계'], dtype=np.float64)
            lower = np.argmax(np.maximum.accumulate(array) - array)
            upper = np.argmax(array[:lower])
            if 'G' in optistd:
                mdd = int(abs(array[upper] - array[lower]))
            else:
                mdd = round(abs(array[upper] - array[lower]) / (array[upper] + onegm) * 100, 2)
        except:
            mdd = 0.
    else:
        tc, atc, pc, mc, wr, ah, ap, tsp, tsg, mhct, onegm, cagr, tpi, mdd = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

    if mdd == 0: mdd = round((tsg if 'G' in optistd else tsp) / 100, 2)
    return df_tsg, df_bct, [tc, atc, pc, mc, wr, ah, ap, tsp, tsg, mhct, onegm, cagr, tpi, mdd]


def PltShow(gubun, df_tsg, df_bct, dict_cn, onegm, mdd, startday, endday, starttime, endtime, df_kp_, df_kd_, list_days,
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
            mdd_ = round(abs(array[upper] - array[lower]) / (array[upper] + onegm) * 100, 2)
        except:
            mdd_ = 0.
        mdd_list.append(mdd_)

    df_sg = df_tsg[['수익금']].copy()
    df_sg['일자'] = df_sg.index
    df_sg['일자'] = df_sg['일자'].apply(lambda x: strp_time('%Y%m%d%H%M%S', x))
    df_sg = df_sg.set_index('일자')

    df_ts = df_sg.resample('D').sum()
    df_ts['수익금합계'] = df_ts['수익금'].cumsum()
    df_ts['수익금합계'] = ((df_ts['수익금합계'] + onegm) / onegm - 1) * 100

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
    df_st['시간'] = df_st['시간'].apply(lambda x: strp_time('%H%M%S', x[8:]))
    df_st = df_st.set_index('시간')
    start_time = strp_time('%H%M%S', str(starttime).zfill(6))
    end_time = strp_time('%H%M%S', str(endtime).zfill(6))
    total_sec = (end_time - start_time).total_seconds()
    df_st = df_st.resample(f'{total_sec / 600 if total_sec >= 1800 else 3}min').sum()
    df_st['시간'] = df_st.index
    df_st['시간'] = df_st['시간'].apply(lambda x: strf_time('%H%M%S', x))
    df_st['시간'] = df_st['시간'].apply(lambda x: x[:2] + ':' + x[2:4] + ':' + x[4:])
    df_st = df_st.set_index('시간')
    df_st['이익금액'] = df_st['수익금'].apply(lambda x: x if x >= 0 else 0)
    df_st['손실금액'] = df_st['수익금'].apply(lambda x: x if x < 0 else 0)

    df_wt = df_tsg[['수익금']].copy()
    df_wt['요일'] = df_wt.index
    df_wt['요일'] = df_wt['요일'].apply(lambda x: strp_time('%Y%m%d%H%M%S', x).weekday())
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
    df_tsg['index'] = df_tsg['index'].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:12]}:{x[12:14]}')
    df_tsg.set_index('index', inplace=True)

    endx_list = None
    if gubun == '최적화':
        endx_list = [df_tsg[df_tsg['매도시간'] < list_days[2][0] * 1000000 + 240000].index[-1]]
        if list_days[1] is not None:
            for vsday, _, _ in list_days[1]:
                df_tsg_ = df_tsg[df_tsg['매도시간'] < vsday * 1000000]
                if len(df_tsg_) > 0:
                    endx_list.append(df_tsg_.index[-1])

    telebot = None
    try:
        telebot = telegram.Bot(DICT_SET['텔레그램봇토큰'])
    except:
        pass

    if telebot is not None and backname != '백테스트':
        telebot.sendMessage(chat_id=DICT_SET['텔레그램사용자아이디'], text=f'{backname} 완료.')

    font_name = 'C:/Windows/Fonts/malgun.ttf'
    font_family = font_manager.FontProperties(fname=font_name).get_name()
    plt.rcParams['font.family'] = font_family
    plt.rcParams['axes.unicode_minus'] = False

    plt.figure(f'{backname} 부가정보', figsize=(12, 10))
    gs = gridspec.GridSpec(nrows=2, ncols=2, height_ratios=[1, 1])
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
    plt.subplot(gs[2])
    plt.bar(df_st.index, df_st['이익금액'], label='이익금액', color='r')
    plt.bar(df_st.index, df_st['손실금액'], label='손실금액', color='b')
    plt.title('시간별 수익금')
    plt.xticks(list(df_st.index), rotation=45)
    plt.legend(loc='best')
    plt.grid()
    plt.subplot(gs[3])
    plt.bar(wt_index, wt_datap, label='이익금액', color='r')
    plt.bar(wt_index, wt_datam, label='손실금액', color='b')
    plt.title('요일별 수익금')
    plt.xticks(wt_index)
    plt.legend(loc='best')
    plt.grid()
    plt.tight_layout()
    plt.savefig(f"{GRAPH_PATH}/{save_file_name}_.png")

    if telebot is not None and backname != '백테스트':
        with open(f"{GRAPH_PATH}/{save_file_name}_.png", 'rb') as image:
            telebot.send_photo(chat_id=DICT_SET['텔레그램사용자아이디'], photo=image, caption=f'{save_file_name}_')

    if buy_vars is None:
        plt.figure(f'{backname} 결과', figsize=(12, 10))
    else:
        plt.figure(f'{backname} 결과', figsize=(12, 12))
    gs = gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[1, 4])
    plt.subplot(gs[0])
    plt.plot(df_bct.index, df_bct['보유종목수'], label='보유종목수', color='g')
    plt.xticks([])
    if buy_vars is None:
        plt.xlabel('\n' + back_text + '\n' + label_text)
    else:
        plt.xlabel('\n' + back_text + '\n' + label_text + '\n\n' + buy_vars + '\n\n' + sell_vars)
    plt.legend(loc='best')
    plt.grid()
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

    if telebot is not None and backname != '백테스트':
        with open(f"{GRAPH_PATH}/{save_file_name}.png", 'rb') as image:
            telebot.send_photo(chat_id=DICT_SET['텔레그램사용자아이디'], photo=image, caption=f'{save_file_name}')

    if not schedul and not plotgraph:
        plt.show()


class CollectTotal:
    def __init__(self, tq, ctq, buystd, gubun):
        self.tq        = tq
        self.ctq       = ctq
        self.buystd    = buystd
        self.gubun     = gubun
        self.arry_bct  = None
        self.list_data = [[], [], [], [], [], [], [], [], [], [], [], [], [], []]
        self.Start()

    def Start(self):
        while True:
            data = self.ctq.get()
            if data[0] == '백테결과':
                self.Collect(data)
            elif data == '백테완료':
                if self.list_data[0]:
                    data = ['백테결과', self.gubun, self.list_data, self.arry_bct]
                else:
                    data = ['백테결과', None, None, None]
                self.tq.put(data)
            elif data == '백테시작':
                self.InitData()
            elif data[0] == '보유종목수어레이':
                self.arry_bct = data[1]
            else:
                break
        sys.exit()

    def Collect(self, data):
        index = str(data[3]) if self.buystd else str(data[4])
        while index in self.list_data[0]:
            index = strf_time('%Y%m%d%H%M%S', timedelta_sec(1, strp_time('%Y%m%d%H%M%S', index)))

        self.list_data[0].append(index)
        self.list_data[1].append(data[1])
        self.list_data[2].append(data[2])
        self.list_data[3].append(data[3])
        self.list_data[4].append(data[4])
        self.list_data[5].append(data[5])
        self.list_data[6].append(data[6])
        self.list_data[7].append(data[7])
        self.list_data[8].append(data[8])
        self.list_data[9].append(data[9])
        self.list_data[10].append(data[10])
        self.list_data[11].append(data[11])
        self.list_data[12].append(data[12])
        self.list_data[13].append(data[13])

        if data[14]:
            arry_bct = self.arry_bct[(self.arry_bct[:, 0] >= data[3]) & (self.arry_bct[:, 0] <= data[4])]
            arry_bct[:, 1] += 1
            self.arry_bct[(self.arry_bct[:, 0] >= data[3]) & (self.arry_bct[:, 0] <= data[4])] = arry_bct

    def InitData(self):
        self.arry_bct[:, 1] = 0
        self.list_data = [[], [], [], [], [], [], [], [], [], [], [], [], [], []]


class SubTotal:
    def __init__(self, tq, stq, betting, optistd, gubun):
        self.tq      = tq
        self.stq     = stq
        self.betting = betting
        self.optistd = optistd
        self.gubun   = gubun
        self.Start()

    def Start(self):
        while True:
            data = self.stq.get()
            if type(data) == list:
                self.SendSubTotal(data)
            else:
                break
        sys.exit()

    def SendSubTotal(self, data):
        columns, list_data, arry_bct = data[:3]
        df_tsg = pd.DataFrame(dict(zip(columns, list_data)))
        df_tsg.set_index('index', inplace=True)
        df_tsg.sort_index(inplace=True)
        arry_bct = arry_bct[arry_bct[:, 1] > 0]
        df_bct = pd.DataFrame(arry_bct[:, 1], columns=['보유종목수'], index=arry_bct[:, 0])

        if len(data) == 10:
            vsday, veday, tsday, tdaycnt, vdaycnt, index, vars_key = data[3:]
            if self.gubun:
                df_tsg = df_tsg[(df_tsg['매도시간'] < vsday * 1000000) | ((df_tsg['매도시간'] > veday * 1000000 + 240000) & (df_tsg['매도시간'] < tsday * 1000000))]
                df_bct = df_bct[(df_bct.index < vsday * 1000000) | ((df_bct.index > veday * 1000000 + 240000) & (df_bct.index < tsday * 1000000))]
            else:
                df_tsg = df_tsg[(df_tsg['매도시간'] >= vsday * 1000000) & (df_tsg['매도시간'] <= veday * 1000000 + 240000)]
                df_bct = df_bct[(df_bct.index >= vsday * 1000000) & (df_bct.index <= veday * 1000000 + 240000)]
            _, _, result = GetBackResult(df_tsg, df_bct, self.betting, self.optistd, tdaycnt if self.gubun else vdaycnt)
            self.tq.put(['TRAIN' if self.gubun else 'VALID', index, result, vars_key])
        elif len(data) == 9:
            vsday, veday, tdaycnt, vdaycnt, index, vars_key = data[3:]
            if self.gubun:
                df_tsg = df_tsg[(df_tsg['매도시간'] < vsday * 1000000) | (df_tsg['매도시간'] > veday * 1000000 + 240000)]
                df_bct = df_bct[(df_bct.index < vsday * 1000000) | (df_bct.index > veday * 1000000 + 240000)]
            else:
                df_tsg = df_tsg[(df_tsg['매도시간'] >= vsday * 1000000) & (df_tsg['매도시간'] <= veday * 1000000 + 240000)]
                df_bct = df_bct[(df_bct.index >= vsday * 1000000) & (df_bct.index <= veday * 1000000 + 240000)]
            _, _, result = GetBackResult(df_tsg, df_bct, self.betting, self.optistd, tdaycnt if self.gubun else vdaycnt)
            self.tq.put(['TRAIN' if self.gubun else 'VALID', index, result, vars_key])
        elif len(data) == 6:
            teday, daycnt, vars_key = data[3:]
            df_tsg['구분'] = df_tsg['매도시간'].apply(lambda x: 0 if int(x / 1000000) % 2 == 0 else 1)
            df_bct['구분'] = df_bct.index
            df_bct['구분'] = df_bct['구분'].apply(lambda x: 0 if int(x / 1000000) % 2 == 0 else 1)
            gb = 0 if teday % 2 == 0 else 1
            if self.gubun:
                df_tsg = df_tsg[(df_tsg['매도시간'] < teday * 1000000) & (df_tsg['구분'] == gb)]
                df_bct = df_bct[(df_bct.index < teday * 1000000) & (df_bct['구분'] == gb)]
            else:
                df_tsg = df_tsg[(df_tsg['매도시간'] < teday * 1000000) & (df_tsg['구분'] != gb)]
                df_bct = df_bct[(df_bct.index < teday * 1000000) & (df_bct['구분'] != gb)]
            _, _, result = GetBackResult(df_tsg, df_bct, self.betting, self.optistd, daycnt)
            self.tq.put(['TRAIN' if self.gubun else 'VALID', 0, result, vars_key])
        else:
            daycnt, vars_key = data[3:]
            _, _, result = GetBackResult(df_tsg, df_bct, self.betting, self.optistd, daycnt)
            self.tq.put(['ALL', 0, result, vars_key])
