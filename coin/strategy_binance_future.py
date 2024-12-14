import math
import time
# noinspection PyUnresolvedReferences
import talib
import sqlite3
import numpy as np
import pandas as pd
from traceback import print_exc
# noinspection PyUnresolvedReferences
from utility.static import now, now_utc, strp_time, int_hms_utc, timedelta_sec, GetBinanceShortPgSgSp, GetBinanceLongPgSgSp
from utility.setting import DB_STRATEGY, DICT_SET, ui_num, columns_jgf, columns_gj, dict_min, dict_order_ratio, DB_COIN_MIN, DB_COIN_DAY


class StrategyBinanceFuture:
    def __init__(self, qlist):
        """
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ,  cstgQ, liveQ, kimpQ, wdzservQ
           0        1       2      3       4      5      6      7       8         9         10     11    12      13
        """
        self.windowQ  = qlist[0]
        self.queryQ   = qlist[2]
        self.chartQ   = qlist[4]
        self.ctraderQ = qlist[9]
        self.cstgQ    = qlist[10]
        self.dict_set = DICT_SET

        self.buystrategy1  = None
        self.sellstrategy1 = None
        self.buystrategy2  = None
        self.sellstrategy2 = None

        self.vars          = {}
        self.vars2         = {}
        self.dict_tik_ar   = {}
        self.dict_tik_ar2  = {}
        self.dict_day_ar   = {}
        self.dict_min_ar   = {}
        self.dict_day_data = {}
        self.dict_min_data = {}
        self.dict_buyinfo  = {}
        self.dict_sgn_tik  = {}
        self.dict_buy_tik  = {}

        self.tuple_gsjm1    = []
        self.tuple_gsjm2    = []

        self.dict_info     = {}
        self.dict_hilo     = {}
        self.dict_signal   = {'BUY_LONG': [], 'SELL_SHORT': [], 'SELL_LONG': [], 'BUY_SHORT': []}
        self.bhogainfo     = {}
        self.shogainfo     = {}
        self.dict_sgn_tik  = {}
        self.dict_buy_tik  = {}

        self.jgrv_count = 0
        self.int_tujagm = 0
        self.stg_change = False
        self.chart_code = None
        self.df_gj = pd.DataFrame(columns=columns_gj)
        self.df_jg = pd.DataFrame(columns=columns_jgf)

        self.UpdateStringategy()
        self.MainLoop()

    def UpdateStringategy(self):
        con  = sqlite3.connect(DB_STRATEGY)
        dfb  = pd.read_sql('SELECT * FROM coinbuy', con).set_index('index')
        dfs  = pd.read_sql('SELECT * FROM coinsell', con).set_index('index')
        dfob = pd.read_sql('SELECT * FROM coinoptibuy', con).set_index('index')
        dfos = pd.read_sql('SELECT * FROM coinoptisell', con).set_index('index')
        con.close()

        if self.dict_set['코인장초매수전략'] == '':
            self.buystrategy1 = None
        elif self.dict_set['코인장초매수전략'] in dfb.index:
            self.buystrategy1 = compile(dfb['전략코드'][self.dict_set['코인장초매수전략']], '<string>', 'exec')
        elif self.dict_set['코인장초매수전략'] in dfob.index:
            self.buystrategy1 = compile(dfob['전략코드'][self.dict_set['코인장초매수전략']], '<string>', 'exec')
            self.vars = {i: var for i, var in enumerate(list(dfob.loc[self.dict_set['코인장초매수전략']])[1:]) if var != 9999.}

        if self.dict_set['코인장초매도전략'] == '':
            self.sellstrategy1 = None
        elif self.dict_set['코인장초매도전략'] in dfs.index:
            self.sellstrategy1 = compile(dfs['전략코드'][self.dict_set['코인장초매도전략']], '<string>', 'exec')
        elif self.dict_set['코인장초매도전략'] in dfos.index:
            self.sellstrategy1 = compile(dfos['전략코드'][self.dict_set['코인장초매도전략']], '<string>', 'exec')

        if self.dict_set['코인장중매수전략'] == '':
            self.buystrategy2 = None
        elif self.dict_set['코인장중매수전략'] in dfb.index:
            self.buystrategy2 = compile(dfb['전략코드'][self.dict_set['코인장중매수전략']], '<string>', 'exec')
        elif self.dict_set['코인장중매수전략'] in dfob.index:
            self.buystrategy2 = compile(dfob['전략코드'][self.dict_set['코인장중매수전략']], '<string>', 'exec')
            self.vars2 = {i: var for i, var in enumerate(list(dfob.loc[self.dict_set['코인장중매수전략']])[1:]) if var != 9999.}

        if self.dict_set['코인장중매도전략'] == '':
            self.sellstrategy2 = None
        elif self.dict_set['코인장중매도전략'] in dfs.index:
            self.sellstrategy2 = compile(dfs['전략코드'][self.dict_set['코인장중매도전략']], '<string>', 'exec')
        elif self.dict_set['코인장중매도전략'] in dfos.index:
            self.sellstrategy2 = compile(dfos['전략코드'][self.dict_set['코인장중매도전략']], '<string>', 'exec')

    def MainLoop(self):
        self.windowQ.put((ui_num['C로그텍스트'], '시스템 명령 실행 알림 - 전략 연산 시작'))
        while True:
            data = self.cstgQ.get()
            if type(data) == tuple:
                if len(data) > 3:
                    self.Strategy(data)
                elif len(data) == 2:
                    self.UpdateTuple(data)
                elif len(data) == 3:
                    self.UpdateTriple(data)
            elif type(data) == str:
                self.UpdateString(data)
                if data == '프로세스종료':
                    break

        self.windowQ.put((ui_num['C로그텍스트'], '시스템 명령 실행 알림 - 전략연산 종료'))
        time.sleep(1)

    def UpdateTuple(self, data):
        gubun, data = data
        if '_COMPLETE' in gubun:
            gubun = gubun.replace('_COMPLETE', '')
            if data in self.dict_signal[gubun]:
                self.dict_signal[gubun].remove(data)
            if gubun in ('BUY_LONG', 'SELL_SHORT'):
                if data in self.dict_sgn_tik.keys():
                    self.dict_buy_tik[data] = self.dict_sgn_tik[data]
                else:
                    self.dict_buy_tik[data] = len(self.dict_tik_ar[data]) - 1
        elif '_CANCEL' in gubun:
            gubun = gubun.replace('_CANCEL', '')
            if data in self.dict_signal[gubun]:
                self.dict_signal[gubun].remove(data)
        elif '_MANUAL' in gubun:
            gubun = gubun.replace('_MANUAL', '')
            if data not in self.dict_signal[gubun]:
                self.dict_signal[gubun].append(data)
        elif gubun == '잔고목록':
            self.df_jg = data
            self.jgrv_count += 1
            if self.jgrv_count == 2:
                self.jgrv_count = 0
                self.PutGsjmAndDeleteHilo()
        elif gubun == '매수전략':
            if int_hms_utc() < self.dict_set['코인장초전략종료시간']:
                self.buystrategy1 = compile(data, '<string>', 'exec')
            else:
                self.buystrategy2 = compile(data, '<string>', 'exec')
        elif gubun == '매도전략':
            if int_hms_utc() < self.dict_set['코인장초전략종료시간']:
                self.sellstrategy1 = compile(data, '<string>', 'exec')
            else:
                self.sellstrategy2 = compile(data, '<string>', 'exec')
        elif gubun == '종목당투자금':
            self.int_tujagm = data
        elif gubun == '차트종목코드':
            self.chart_code = data
        elif gubun == '설정변경':
            self.dict_set = data
            self.UpdateStringategy()
        elif gubun == '일봉데이터':
            self.dict_day_ar = data
            for data in self.dict_day_ar.keys():
                self.dict_day_data[data] = self.GetNewLineData(self.dict_day_ar[data], 250)
            self.windowQ.put((ui_num['C로그텍스트'], '시스템 명령 실행 알림 - 일봉데이터 로딩 완료'))
        elif gubun == '분봉데이터':
            self.dict_min_ar = data
            for data in self.dict_min_ar.keys():
                self.dict_min_data[data] = self.GetNewLineData(self.dict_min_ar[data], self.dict_set['코인분봉개수'])
            self.windowQ.put((ui_num['C로그텍스트'], '시스템 명령 실행 알림 - 분봉데이터 로딩 완료'))
        elif gubun == '바낸선물단위정보':
            self.dict_info = data

    def UpdateTriple(self, data):
        gubun, data1, data2 = data
        if gubun == '관심목록':
            self.tuple_gsjm1, self.tuple_gsjm2 = data1, data2
            drop_index_list = list(set(list(self.df_gj.index)) - set(self.tuple_gsjm2))
            self.df_gj.drop(index=drop_index_list, inplace=True)
        elif gubun == '분봉재로딩':
            con = sqlite3.connect(DB_COIN_MIN)
            df = pd.read_sql(f"SELECT * FROM '{data1}' WHERE 체결시간 < {data2} ORDER BY 체결시간 DESC LIMIT {self.dict_set['코인분봉개수']}", con)
            columns = ['체결시간', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240']
            df = df[columns][::-1]
            self.dict_min_ar[data1] = np.array(df)
            self.dict_min_data[data1] = self.GetNewLineData(self.dict_min_ar[data1], self.dict_set['코인분봉개수'])
            con.close()
        elif gubun == '일봉재로딩':
            con = sqlite3.connect(DB_COIN_DAY)
            df = pd.read_sql(f"SELECT * FROM '{data1}' WHERE 일자 < {data2} ORDER BY 일자 DESC LIMIT 250", con)
            columns = ['일자', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240']
            df = df[columns][::-1]
            self.dict_day_ar[data1] = np.array(df)
            self.dict_day_data[data1] = self.GetNewLineData(self.dict_day_ar[data1], 250)
            con.close()

    def UpdateString(self, data):
        if data == '매수전략중지':
            self.buystrategy1 = None
            self.buystrategy2 = None
        elif data == '매도전략중지':
            self.sellstrategy1 = None
            self.sellstrategy2 = None
        elif data == '복기모드종료':
            self.dict_tik_ar = {}

    @staticmethod
    def GetNewLineData(ar, hmcount):
        최고종가5   = ar[-5:,   4].max()
        최고고가5   = ar[-5:,   2].max()
        최고종가10  = ar[-10:,  4].max()
        최고고가10  = ar[-10:,  2].max()
        최고종가20  = ar[-20:,  4].max()
        최고고가20  = ar[-20:,  2].max()
        최고종가60  = ar[-60:,  4].max()
        최고고가60  = ar[-60:,  2].max()
        최고종가120 = ar[-120:, 4].max()
        최고고가120 = ar[-120:, 2].max()
        최고종가240 = ar[-240:, 4].max()
        최고고가240 = ar[-240:, 2].max()
        최저종가5   = ar[-5:,   4].min()
        최저저가5   = ar[-5:,   3].min()
        최저종가10  = ar[-10:,  4].min()
        최저저가10  = ar[-10:,  3].min()
        최저종가20  = ar[-20:,  4].min()
        최저저가20  = ar[-20:,  3].min()
        최저종가60  = ar[-60:,  4].min()
        최저저가60  = ar[-60:,  3].min()
        최저종가120 = ar[-120:, 4].min()
        최저저가120 = ar[-120:, 3].min()
        최저종가240 = ar[-240:, 4].min()
        최저저가240 = ar[-240:, 3].min()
        종가합계4   = ar[-4:,   4].sum()
        종가합계9   = ar[-9:,   4].sum()
        종가합계19  = ar[-19:,  4].sum()
        종가합계59  = ar[-59:,  4].sum()
        종가합계119 = ar[-119:, 4].sum()
        종가합계239 = ar[-239:, 4].sum()
        최고거래대금 = ar[-hmcount:, 5].max()
        new_data = [
            최고종가5, 최고고가5, 최고종가10, 최고고가10, 최고종가20, 최고고가20, 최고종가60, 최고고가60, 최고종가120, 최고고가120, 최고종가240, 최고고가240,
            최저종가5, 최저저가5, 최저종가10, 최저저가10, 최저종가20, 최저저가20, 최저종가60, 최저저가60, 최저종가120, 최저저가120, 최저종가240, 최저저가240,
            종가합계4, 종가합계9, 종가합계19, 종가합계59, 종가합계119, 종가합계239, 최고거래대금
        ]
        return new_data

    def Strategy(self, data):
        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 초당매수수량, 초당매도수량, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량, \
            매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, \
            매도수5호가잔량합, 종목코드, 틱수신시간 = data

        def Parameter_Previous(number, pre):
            if pre != -1:
                return self.dict_tik_ar[종목코드][index-pre, number]
            else:
                return self.dict_tik_ar[종목코드][매수틱번호, number]

        def 현재가N(pre):
            return Parameter_Previous(1, pre)

        def 시가N(pre):
            return Parameter_Previous(2, pre)

        def 고가N(pre):
            return Parameter_Previous(3, pre)

        def 저가N(pre):
            return Parameter_Previous(4, pre)

        def 등락율N(pre):
            return Parameter_Previous(5, pre)

        def 당일거래대금N(pre):
            return Parameter_Previous(6, pre)

        def 체결강도N(pre):
            return Parameter_Previous(7, pre)

        def 초당매수수량N(pre):
            return Parameter_Previous(8, pre)

        def 초당매도수량N(pre):
            return Parameter_Previous(9, pre)

        def 초당거래대금N(pre):
            return Parameter_Previous(10, pre)

        def 고저평균대비등락율N(pre):
            return Parameter_Previous(11, pre)

        def 매도총잔량N(pre):
            return Parameter_Previous(12, pre)

        def 매수총잔량N(pre):
            return Parameter_Previous(13, pre)

        def 매도호가5N(pre):
            return Parameter_Previous(14, pre)

        def 매도호가4N(pre):
            return Parameter_Previous(15, pre)

        def 매도호가3N(pre):
            return Parameter_Previous(16, pre)

        def 매도호가2N(pre):
            return Parameter_Previous(17, pre)

        def 매도호가1N(pre):
            return Parameter_Previous(18, pre)

        def 매수호가1N(pre):
            return Parameter_Previous(19, pre)

        def 매수호가2N(pre):
            return Parameter_Previous(20, pre)

        def 매수호가3N(pre):
            return Parameter_Previous(21, pre)

        def 매수호가4N(pre):
            return Parameter_Previous(22, pre)

        def 매수호가5N(pre):
            return Parameter_Previous(23, pre)

        def 매도잔량5N(pre):
            return Parameter_Previous(24, pre)

        def 매도잔량4N(pre):
            return Parameter_Previous(25, pre)

        def 매도잔량3N(pre):
            return Parameter_Previous(26, pre)

        def 매도잔량2N(pre):
            return Parameter_Previous(27, pre)

        def 매도잔량1N(pre):
            return Parameter_Previous(28, pre)

        def 매수잔량1N(pre):
            return Parameter_Previous(29, pre)

        def 매수잔량2N(pre):
            return Parameter_Previous(30, pre)

        def 매수잔량3N(pre):
            return Parameter_Previous(31, pre)

        def 매수잔량4N(pre):
            return Parameter_Previous(32, pre)

        def 매수잔량5N(pre):
            return Parameter_Previous(33, pre)

        def 매도수5호가잔량합N(pre):
            return Parameter_Previous(34, pre)

        def 이동평균(tick, pre=0):
            if tick == 60:
                return Parameter_Previous(35, pre)
            elif tick == 300:
                return Parameter_Previous(36, pre)
            elif tick == 600:
                return Parameter_Previous(37, pre)
            elif tick == 1200:
                return Parameter_Previous(38, pre)
            else:
                if pre != -1:
                    return round(self.dict_tik_ar[종목코드][index+1-tick-pre:index+1-pre, 1].mean(), 3)
                else:
                    return round(self.dict_tik_ar[종목코드][매수틱번호+1-tick:매수틱번호+1, 1].mean(), 3)

        def Parameter_Area(aindex, vindex, tick, pre, gubun_):
            if tick == 평균값계산틱수:
                return Parameter_Previous(aindex, pre)
            else:
                if pre != -1:
                    if gubun_ == 'max':
                        return self.dict_tik_ar[종목코드][index+1-pre-tick:index+1-pre, vindex].max()
                    elif gubun_ == 'min':
                        return self.dict_tik_ar[종목코드][index+1-pre-tick:index+1-pre, vindex].min()
                    elif gubun_ == 'sum':
                        return self.dict_tik_ar[종목코드][index+1-pre-tick:index+1-pre, vindex].sum()
                    else:
                        return self.dict_tik_ar[종목코드][index+1-pre-tick:index+1-pre, vindex].mean()
                else:
                    if gubun_ == 'max':
                        return self.dict_tik_ar[종목코드][매수틱번호+1-tick:매수틱번호+1, vindex].max()
                    elif gubun_ == 'min':
                        return self.dict_tik_ar[종목코드][매수틱번호+1-tick:매수틱번호+1, vindex].min()
                    else:
                        return self.dict_tik_ar[종목코드][매수틱번호+1-tick:매수틱번호+1, vindex].mean()

        def 최고현재가(tick, pre=0):
            return Parameter_Area(39, 1, tick, pre, 'max')

        def 최저현재가(tick, pre=0):
            return Parameter_Area(40, 1, tick, pre, 'min')

        def 체결강도평균(tick, pre=0):
            return Parameter_Area(41, 7, tick, pre, 'mean')

        def 최고체결강도(tick, pre=0):
            return Parameter_Area(42, 7, tick, pre, 'max')

        def 최저체결강도(tick, pre=0):
            return Parameter_Area(43, 7, tick, pre, 'min')

        def 최고초당매수수량(tick, pre=0):
            return Parameter_Area(44, 14, tick, pre, 'max')

        def 최고초당매도수량(tick, pre=0):
            return Parameter_Area(45, 15, tick, pre, 'max')

        def 누적초당매수수량(tick, pre=0):
            return Parameter_Area(46, 14, tick, pre, 'sum')

        def 누적초당매도수량(tick, pre=0):
            return Parameter_Area(47, 15, tick, pre, 'sum')

        def 초당거래대금평균(tick, pre=0):
            return Parameter_Area(48, 19, tick, pre, 'mean')

        def Parameter_Dgree(aindex, vindex, tick, pre, cf):
            if tick == 평균값계산틱수:
                return Parameter_Previous(aindex, pre)
            else:
                if pre != -1:
                    dmp_gap = self.dict_tik_ar[종목코드][index-pre, vindex] - self.dict_tik_ar[종목코드][index+1-tick-pre, vindex]
                else:
                    dmp_gap = self.dict_tik_ar[종목코드][매수틱번호, vindex] - self.dict_tik_ar[종목코드][매수틱번호+1-tick, vindex]
                return round(math.atan2(dmp_gap * cf, tick) / (2 * math.pi) * 360, 2)

        def 등락율각도(tick, pre=0):
            return Parameter_Dgree(49, 5, tick, pre, 10)

        def 당일거래대금각도(tick, pre=0):
            return Parameter_Dgree(50, 6, tick, pre, 0.00000001)

        분봉체결시간 = int(str(체결시간)[:10] + dict_min[self.dict_set['코인분봉기간']][str(체결시간)[10:12]] + '00')
        if self.dict_set['코인분봉데이터']:
            def 분봉시가N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 1]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 1]

            def 분봉고가N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 2]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 2]

            def 분봉저가N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 3]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 3]

            def 분봉현재가N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 4]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 4]

            def 분봉거래대금N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 5]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 5]

            def 분봉이평5N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 6]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 6]

            def 분봉이평10N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 7]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 7]

            def 분봉이평20N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 8]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 8]

            def 분봉이평60N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 9]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 9]

            def 분봉이평120N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 10]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 10]

            def 분봉이평240N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 11]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 11]

        일봉일자 = int(str(체결시간)[:8])
        if self.dict_set['코인일봉데이터']:
            def 일봉시가N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 1]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 1]

            def 일봉고가N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 2]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 2]

            def 일봉저가N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 3]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 3]

            def 일봉현재가N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 4]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 4]

            def 일봉거래대금N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 5]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 5]

            def 일봉이평5N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 6]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 6]

            def 일봉이평10N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 7]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 7]

            def 일봉이평20N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 8]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 8]

            def 일봉이평60N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 9]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 9]

            def 일봉이평120N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 10]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 10]

            def 일봉이평240N(pre):
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    return self.dict_day_ar[종목코드][-pre, 11]
                else:
                    return self.dict_day_ar[종목코드][-(pre + 1), 11]

        bhogainfo = ((매도호가1, 매도잔량1), (매도호가2, 매도잔량2), (매도호가3, 매도잔량3), (매도호가4, 매도잔량4), (매도호가5, 매도잔량5))
        shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
        self.bhogainfo = bhogainfo[:self.dict_set['코인매수시장가잔량범위']]
        self.shogainfo = shogainfo[:self.dict_set['코인매도시장가잔량범위']]

        시분초, 호가단위 = int(str(체결시간)[8:]), self.dict_info[종목코드]['호가단위']
        데이터길이 = len(self.dict_tik_ar[종목코드]) + 1 if 종목코드 in self.dict_tik_ar.keys() else 1
        평균값계산틱수 = self.dict_set['코인장초평균값계산틱수'] if 시분초 < self.dict_set['코인장초전략종료시간'] else self.dict_set['코인장중평균값계산틱수']
        이동평균60_, 이동평균300_, 이동평균600_, 이동평균1200_, 최고현재가_, 최저현재가_ = 0., 0., 0., 0., 0, 0
        체결강도평균_, 최고체결강도_, 최저체결강도_, 최고초당매수수량_, 최고초당매도수량_ = 0., 0., 0., 0, 0
        누적초당매수수량_, 누적초당매도수량_, 초당거래대금평균_, 등락율각도_, 당일거래대금각도_, 전일비각도_ = 0, 0, 0., 0., 0., 0.
        분봉시가, 분봉고가, 분봉저가, 분봉이평5, 분봉이평10, 분봉이평20, 분봉이평60, 분봉이평120, 분봉이평240, 분봉거래대금 = 0, 0, 0, 0., 0., 0., 0., 0., 0., 0
        일봉이평5, 일봉이평10, 일봉이평20, 일봉이평60, 일봉이평120, 일봉이평240 = 0., 0., 0., 0., 0., 0.

        if 종목코드 in self.dict_tik_ar.keys():
            if len(self.dict_tik_ar[종목코드]) >=   59: 이동평균60_   = round((self.dict_tik_ar[종목코드][  -59:, 1].sum() + 현재가) /   60, 8)
            if len(self.dict_tik_ar[종목코드]) >=  299: 이동평균300_  = round((self.dict_tik_ar[종목코드][ -299:, 1].sum() + 현재가) /  300, 8)
            if len(self.dict_tik_ar[종목코드]) >=  599: 이동평균600_  = round((self.dict_tik_ar[종목코드][ -599:, 1].sum() + 현재가) /  600, 8)
            if len(self.dict_tik_ar[종목코드]) >= 1199: 이동평균1200_ = round((self.dict_tik_ar[종목코드][-1199:, 1].sum() + 현재가) / 1200, 8)
            if len(self.dict_tik_ar[종목코드]) >= 평균값계산틱수 - 1:
                최고현재가_      = max(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 1].max(), 현재가)
                최저현재가_      = min(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 1].min(), 현재가)
                체결강도평균_    =    (self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 7].sum() + 체결강도) / 평균값계산틱수
                최고체결강도_    = max(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 7].max(), 체결강도)
                최저체결강도_    = min(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 7].min(), 체결강도)
                최고초당매수수량_ = max(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 8].max(), 초당매수수량)
                최고초당매도수량_ = min(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 9].min(), 초당매도수량)
                누적초당매수수량_ =     self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 8].sum() + 초당매수수량
                누적초당매도수량_ =     self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 9].sum() + 초당매도수량
                초당거래대금평균_ =    (self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 10].sum() + 초당거래대금) / 평균값계산틱수
                등락율각도_      = round(math.atan2((등락율 - self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1), 5]) * 10, 평균값계산틱수) / (2 * math.pi) * 360, 2)
                당일거래대금각도_ = round(math.atan2((당일거래대금 - self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1), 6]) / 100_000_000, 평균값계산틱수) / (2 * math.pi) * 360, 2)

        new_data_tick = [
            체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 초당매수수량, 초당매도수량, 초당거래대금, 고저평균대비등락율,
            매도총잔량, 매수총잔량, 매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5,
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합,
            이동평균60_, 이동평균300_, 이동평균600_, 이동평균1200_, 최고현재가_, 최저현재가_, 체결강도평균_, 최고체결강도_, 최저체결강도_,
            최고초당매수수량_, 최고초당매도수량_, 누적초당매수수량_, 누적초당매도수량_, 초당거래대금평균_, 등락율각도_, 당일거래대금각도_
        ]

        """
        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 초당매수수량, 초당매도수량, 초당거래대금, 고저평균대비등락율,
           0      1     2    3     4     5        6         7         8           9          10            11
        매도총잔량, 매수총잔량, 매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5,
           12        13        14       15       16        17       18        19       20       21        22       23
        매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합,
           24        25       26       27        28       29        30       31       32        33         34
        이동평균60_, 이동평균300_, 이동평균600_, 이동평균1200_, 최고현재가_, 최저현재가_, 체결강도평균_, 최고체결강도_, 최저체결강도_,
            35         36           37           38          39         40         41           42          43
        최고초당매수수량_, 최고초당매도수량_, 누적초당매수수량_, 누적초당매도수량_, 초당거래대금평균_, 등락율각도_, 당일거래대금각도_
               44            45              46              47              48           49           50
        """

        if 종목코드 not in self.dict_tik_ar.keys():
            self.dict_tik_ar[종목코드] = np.array([new_data_tick])
        else:
            self.dict_tik_ar[종목코드] = np.r_[self.dict_tik_ar[종목코드], np.array([new_data_tick])]
            if len(self.dict_tik_ar[종목코드]) > 1800:
                self.dict_tik_ar[종목코드] = np.delete(self.dict_tik_ar[종목코드], 0, 0)

        데이터길이 = len(self.dict_tik_ar[종목코드])
        index = 데이터길이 - 1

        new_dbdata_min = None
        new_dbdata_day = None

        if self.dict_set['코인분봉데이터']:
            if 종목코드 not in self.dict_min_data.keys():
                return

            try:
                if 분봉체결시간 == self.dict_min_ar[종목코드][-1, 0]:
                    분봉시가, 분봉고가, 분봉저가 = self.dict_min_ar[종목코드][-1, 1:4]
                    분봉거래대금 = self.dict_min_ar[종목코드][-1, 5]
                    분봉고가 = 현재가 if 현재가 > 분봉고가 else 분봉고가
                    분봉저가 = 현재가 if 현재가 < 분봉저가 else 분봉저가
                    분봉거래대금 += 초당거래대금
                else:
                    new_dbdata_min = list(self.dict_min_ar[종목코드][-1, :]) + self.dict_min_data[종목코드]
                    self.dict_min_data[종목코드] = self.GetNewLineData(self.dict_min_ar[종목코드], self.dict_set['코인분봉개수'])
                    분봉시가, 분봉고가, 분봉저가, 분봉거래대금 = 현재가, 현재가, 현재가, 초당거래대금

                분봉최고종가5, 분봉최고고가5, 분봉최고종가10, 분봉최고고가10, 분봉최고종가20, 분봉최고고가20,  분봉최고종가60, \
                    분봉최고고가60, 분봉최고종가120, 분봉최고고가120, 분봉최고종가240, 분봉최고고가240, 분봉최저종가5, 분봉최저저가5, \
                    분봉최저종가10, 분봉최저저가10, 분봉최저종가20, 분봉최저저가20, 분봉최저종가60, 분봉최저저가60, 분봉최저종가120, \
                    분봉최저저가120, 분봉최저종가240, 분봉최저저가240, 분봉종가합계4, 분봉종가합계9, 분봉종가합계19, 분봉종가합계59, \
                    분봉종가합계119, 분봉종가합계239, 분봉최고거래대금 = self.dict_min_data[종목코드]
                분봉이평5   = round((분봉종가합계4   + 현재가) /   5, 8)
                분봉이평10  = round((분봉종가합계9   + 현재가) /  10, 8)
                분봉이평20  = round((분봉종가합계19  + 현재가) /  20, 8)
                분봉이평60  = round((분봉종가합계59  + 현재가) /  60, 8)
                분봉이평120 = round((분봉종가합계119 + 현재가) / 120, 8)
                분봉이평240 = round((분봉종가합계239 + 현재가) / 240, 8)
                분봉최고거래대금대비 = round(분봉거래대금 / 분봉최고거래대금 * 100, 2) if 분봉최고거래대금 != 0 else 0.
            except Exception as e:
                self.windowQ.put((ui_num['C단순텍스트'], f'시스템 명령 오류 알림 - 분봉데이터 {e}'))
                return

        if self.dict_set['코인일봉데이터']:
            if 종목코드 not in self.dict_day_data.keys():
                return

            try:
                if 일봉일자 != self.dict_day_ar[종목코드][-1, 0]:
                    new_dbdata_day = list(self.dict_day_ar[종목코드][-1, :]) + self.dict_day_data[종목코드]
                    self.dict_day_data[종목코드] = self.GetNewLineData(self.dict_day_ar[종목코드], 250)

                일봉최고종가5, 일봉최고고가5, 일봉최고종가10, 일봉최고고가10, 일봉최고종가20, 일봉최고고가20, 일봉최고종가60, \
                    일봉최고고가60, 일봉최고종가120, 일봉최고고가120, 일봉최고종가240, 일봉최고고가240, 일봉최저종가5, 일봉최저저가5, \
                    일봉최저종가10, 일봉최저저가10, 일봉최저종가20, 일봉최저저가20, 일봉최저종가60, 일봉최저저가60, 일봉최저종가120, \
                    일봉최저저가120, 일봉최저종가240, 일봉최저저가240, 일봉종가합계4, 일봉종가합계9, 일봉종가합계19, 일봉종가합계59, \
                    일봉종가합계119, 일봉종가합계239, 일봉최고거래대금 = self.dict_day_data[종목코드]
                일봉이평5   = round((일봉종가합계4   + 현재가) /   5, 8)
                일봉이평10  = round((일봉종가합계9   + 현재가) /  10, 8)
                일봉이평20  = round((일봉종가합계19  + 현재가) /  20, 8)
                일봉이평60  = round((일봉종가합계59  + 현재가) /  60, 8)
                일봉이평120 = round((일봉종가합계119 + 현재가) / 120, 8)
                일봉이평240 = round((일봉종가합계239 + 현재가) / 240, 8)
                일봉최고거래대금대비 = round(당일거래대금 / 일봉최고거래대금 * 100, 2) if 일봉최고거래대금 != 0 else 0.
            except Exception as e:
                self.windowQ.put((ui_num['C단순텍스트'], f'시스템 명령 오류 알림 - 일봉데이터 {e}'))
                return

        if 체결강도평균_ != 0:
            if 종목코드 in self.df_jg.index:
                매수틱번호 = self.dict_buy_tik[종목코드] if 종목코드 in self.dict_buy_tik.keys() else 0
                포지션 = self.df_jg['포지션'][종목코드]
                매입가 = self.df_jg['매입가'][종목코드]
                보유수량 = self.df_jg['보유수량'][종목코드]
                매입금액 = self.df_jg['매입금액'][종목코드]
                레버리지 = self.df_jg['레버리지'][종목코드]
                분할매수횟수 = int(self.df_jg['분할매수횟수'][종목코드])
                분할매도횟수 = int(self.df_jg['분할매도횟수'][종목코드])
                if 포지션 == 'LONG':
                    _, 수익금, 수익률 = GetBinanceLongPgSgSp(매입금액, 보유수량 * 현재가, '시장가' in self.dict_set['코인매수주문구분'], '시장가' in self.dict_set['코인매도주문구분'])
                else:
                    _, 수익금, 수익률 = GetBinanceShortPgSgSp(매입금액, 보유수량 * 현재가, '시장가' in self.dict_set['코인매수주문구분'], '시장가' in self.dict_set['코인매도주문구분'])
                매수시간 = strp_time('%Y%m%d%H%M%S', self.df_jg['매수시간'][종목코드])
                보유시간 = (now_utc() - 매수시간).total_seconds()
                if 종목코드 not in self.dict_hilo.keys():
                    self.dict_hilo[종목코드] = [수익률, 수익률]
                else:
                    if 수익률 > self.dict_hilo[종목코드][0]:
                        self.dict_hilo[종목코드][0] = 수익률
                    elif 수익률 < self.dict_hilo[종목코드][1]:
                        self.dict_hilo[종목코드][1] = 수익률
                최고수익률, 최저수익률 = self.dict_hilo[종목코드]
            else:
                포지션, 수익금, 수익률, 레버리지, 매입가, 보유수량, 분할매수횟수, 분할매도횟수, 매수시간, 보유시간, 최고수익률, 최저수익률 = None, 0, 0, 1, 0, 0, 0, 0, now(), 0, 0, 0

            BBT  = not self.dict_set['코인매수금지시간'] or not (self.dict_set['코인매수금지시작시간'] < 시분초 < self.dict_set['코인매수금지종료시간'])
            BLK  = not self.dict_set['코인매수금지블랙리스트'] or 종목코드 not in self.dict_set['코인블랙리스트']
            C20  = not self.dict_set['코인매수금지200원이하'] or 현재가 > 200
            ING  = 종목코드 in self.tuple_gsjm1
            NIBL = 종목코드 not in self.dict_signal['BUY_LONG']
            NISS = 종목코드 not in self.dict_signal['SELL_SHORT']
            NISL = 종목코드 not in self.dict_signal['SELL_LONG']
            NIBS = 종목코드 not in self.dict_signal['BUY_SHORT']
            A    = ING and NIBL and 포지션 is None
            B    = ING and NISS and 포지션 is None
            C    = self.dict_set['코인매수분할시그널']
            D    = NIBL and 포지션 == 'LONG' and 분할매수횟수 < self.dict_set['코인매수분할횟수']
            E    = NISS and 포지션 == 'SHORT' and 분할매수횟수 < self.dict_set['코인매수분할횟수']
            F    = NIBL and self.dict_set['코인매도취소매수시그널'] and not NISL
            G    = NISS and self.dict_set['코인매도취소매수시그널'] and not NIBS

            if BBT and BLK and C20 and (A or B or (C and D) or (C and E) or D or E or F or G):
                BUY_LONG, SELL_SHORT = True, True
                매수수량 = 0

                if not (F or G):
                    oc_ratio = dict_order_ratio[self.dict_set['코인매수분할방법']][self.dict_set['코인매수분할횟수']][분할매수횟수]
                    매수수량 = round(self.int_tujagm / (현재가 if 매입가 == 0 else 매입가) * oc_ratio / 100, self.dict_info[종목코드]['소숫점자리수'])

                if A or B or (C and (D or E)) or F or G:
                    if 시분초 < self.dict_set['코인장초전략종료시간']:
                        if self.buystrategy1 is not None:
                            try:
                                exec(self.buystrategy1, None, locals())
                            except:
                                print_exc()
                                self.windowQ.put((ui_num['C단순텍스트'], '시스템 명령 오류 알림 - BuyStrategy1'))
                    elif self.dict_set['코인장초전략종료시간'] <= 시분초 < self.dict_set['코인장중전략종료시간']:
                        if self.buystrategy2 is not None:
                            if not self.stg_change:
                                self.vars = self.vars2
                                self.stg_change = True
                            try:
                                exec(self.buystrategy2, None, locals())
                            except:
                                print_exc()
                                self.windowQ.put((ui_num['C단순텍스트'], '시스템 명령 오류 알림 - BuyStrategy2'))
                elif D or E:
                    분할매수기준수익률 = round((현재가 / self.dict_buyinfo[종목코드][9] - 1) * 100, 2) if self.dict_set['코인매수분할고정수익률'] else 수익률
                    if D:
                        if self.dict_set['코인매수분할하방'] and 분할매수기준수익률 < -self.dict_set['코인매수분할하방수익률']:
                            BUY_LONG   = True
                        elif self.dict_set['코인매수분할상방'] and 분할매수기준수익률 > self.dict_set['코인매수분할상방수익률']:
                            BUY_LONG   = True
                    elif E:
                        if self.dict_set['코인매수분할하방'] and 분할매수기준수익률 < -self.dict_set['코인매수분할하방수익률']:
                            SELL_SHORT = True
                        elif self.dict_set['코인매수분할상방'] and 분할매수기준수익률 > self.dict_set['코인매수분할상방수익률']:
                            SELL_SHORT = True

                    if BUY_LONG or SELL_SHORT:
                        self.Buy(종목코드, BUY_LONG, 현재가, 매도호가1, 매수호가1, 매수수량, 데이터길이)

            SBT  = not self.dict_set['코인매도금지시간'] or not (self.dict_set['코인매도금지시작시간'] < 시분초 < self.dict_set['코인매도금지종료시간'])
            SCC  = self.dict_set['코인매수분할횟수'] == 1 or not self.dict_set['코인매도금지매수횟수'] or 분할매수횟수 > self.dict_set['코인매도금지매수횟수값']
            NIBL = 종목코드 not in self.dict_signal['BUY_LONG']
            NISS = 종목코드 not in self.dict_signal['SELL_SHORT']

            A    = NIBL and NISL and SCC and 포지션 == 'LONG' and self.dict_set['코인매도분할횟수'] == 1
            B    = NISS and NIBS and SCC and 포지션 == 'SHORT' and self.dict_set['코인매도분할횟수'] == 1
            C    = self.dict_set['코인매도분할시그널']
            D    = NIBL and NISL and SCC and 포지션 == 'LONG' and 분할매도횟수 < self.dict_set['코인매도분할횟수']
            E    = NISS and NIBS and SCC and 포지션 == 'SHORT' and 분할매도횟수 < self.dict_set['코인매도분할횟수']
            F    = NISL and self.dict_set['코인매수취소매도시그널'] and not NIBL
            G    = NIBS and self.dict_set['코인매수취소매도시그널'] and not NISS
            H    = NIBL and NISL and 포지션 == 'LONG' and self.dict_set['코인매도손절수익률청산'] and 수익률 < -self.dict_set['코인매도손절수익률']
            J    = NISS and NIBS and 포지션 == 'SHORT' and self.dict_set['코인매도손절수익률청산'] and 수익률 < -self.dict_set['코인매도손절수익률']
            K    = NIBL and NISL and 포지션 == 'LONG' and self.dict_set['코인매도손절수익금청산'] and 수익금 < -self.dict_set['코인매도손절수익금']
            L    = NISS and NIBS and 포지션 == 'SHORT' and self.dict_set['코인매도손절수익금청산'] and 수익금 < -self.dict_set['코인매도손절수익금']
            M    = NIBL and NISL and 포지션 == 'LONG' and 수익률 * 레버리지 < -90
            N    = NISS and NIBS and 포지션 == 'SHORT' and 수익률 * 레버리지 < -90

            if SBT and (A or B or (C and D) or (C and E) or D or E or F or G or H or J or K or L or M or N):
                SELL_LONG, BUY_SHORT = False, False
                매도수량 = 0
                강제청산 = H or J or K or L or M or N

                if A or B or H or J or K or L or M or N:
                    매도수량 = 보유수량
                elif not (F or G):
                    oc_ratio = dict_order_ratio[self.dict_set['코인매도분할방법']][self.dict_set['코인매도분할횟수']][분할매도횟수]
                    매도수량 = round(self.int_tujagm / 매입가 * oc_ratio / 100, self.dict_info[종목코드]['소숫점자리수'])
                    if 매도수량 > 보유수량 or 분할매도횟수 + 1 == self.dict_set['코인매도분할횟수']: 매도수량 = 보유수량

                if A or B or (C and (D or E)) or F or G:
                    if 시분초 < self.dict_set['코인장초전략종료시간']:
                        if self.sellstrategy1 is not None:
                            try:
                                exec(self.sellstrategy1, None, locals())
                            except:
                                print_exc()
                                self.windowQ.put((ui_num['C단순텍스트'], '시스템 명령 오류 알림 - SellStrategy1'))
                    elif self.dict_set['코인장초전략종료시간'] <= 시분초 < self.dict_set['코인장중전략종료시간']:
                        if self.sellstrategy2 is not None:
                            try:
                                exec(self.sellstrategy2, None, locals())
                            except:
                                print_exc()
                                self.windowQ.put((ui_num['C단순텍스트'], '시스템 명령 오류 알림 - SellStrategy2'))
                elif D or E or H or J or K or L or M or N:
                    if H or K or M:
                        SELL_LONG = True
                    elif J or L or N:
                        BUY_SHORT = True
                    elif D:
                        if self.dict_set['코인매도분할하방'] and 수익률 < -self.dict_set['코인매도분할하방수익률'] * (분할매도횟수 + 1):
                            SELL_LONG = True
                        elif self.dict_set['코인매도분할상방'] and 수익률 > self.dict_set['코인매도분할상방수익률'] * (분할매도횟수 + 1):
                            SELL_LONG = True
                    elif E:
                        if self.dict_set['코인매도분할하방'] and 수익률 < -self.dict_set['코인매도분할하방수익률'] * (분할매도횟수 + 1):
                            BUY_SHORT = True
                        elif self.dict_set['코인매도분할상방'] and 수익률 > self.dict_set['코인매도분할상방수익률'] * (분할매도횟수 + 1):
                            BUY_SHORT = True

                    if (포지션 == 'LONG' and SELL_LONG) or (포지션 == 'SHORT' and BUY_SHORT):
                        self.Sell(종목코드, 포지션, SELL_LONG, 현재가, 매도호가1, 매수호가1, 매도수량, 강제청산)

        if 종목코드 in self.tuple_gsjm2:
            self.df_gj.loc[종목코드] = 종목코드, 등락율, 고저평균대비등락율, 초당거래대금, 초당거래대금평균_, 당일거래대금, 체결강도, 체결강도평균_, 최고체결강도_

        if len(self.dict_tik_ar[종목코드]) >= 평균값계산틱수 and self.chart_code == 종목코드:
            self.windowQ.put((ui_num['실시간차트'], 종목코드, self.dict_tik_ar[종목코드]))

        if self.dict_set['코인틱데이터저장'] and 종목코드 in self.tuple_gsjm2:
            if 종목코드 not in self.dict_tik_ar2.keys():
                self.dict_tik_ar2[종목코드] = np.array([new_data_tick[:35]])
            else:
                self.dict_tik_ar2[종목코드] = np.r_[self.dict_tik_ar2[종목코드], np.array([new_data_tick[:35]])]

        if self.dict_set['코인분봉데이터']:
            if new_dbdata_min is None:
                self.dict_min_ar[종목코드][-1, :] = 분봉체결시간, 분봉시가, 분봉고가, 분봉저가, 현재가, 분봉거래대금, 분봉이평5, 분봉이평10, 분봉이평20, 분봉이평60, 분봉이평120, 분봉이평240
            else:
                new_data = [분봉체결시간, 분봉시가, 분봉고가, 분봉저가, 현재가, 분봉거래대금, 분봉이평5, 분봉이평10, 분봉이평20, 분봉이평60, 분봉이평120, 분봉이평240]
                self.dict_min_ar[종목코드] = np.r_[self.dict_min_ar[종목코드], np.array([new_data])]
                if len(self.dict_min_ar[종목코드]) > self.dict_set['코인분봉개수']:
                    self.dict_min_ar[종목코드] = np.delete(self.dict_min_ar[종목코드], 0, 0)
                self.queryQ.put(('코인분봉', new_dbdata_min, 종목코드, 'append'))

            if self.chart_code == 종목코드:
                self.windowQ.put((ui_num['분봉차트'], 종목코드, self.dict_min_ar[종목코드][-120:]))

        if self.dict_set['코인일봉데이터']:
            if new_dbdata_day is None:
                self.dict_day_ar[종목코드][-1, :] = 일봉일자, 시가, 고가, 저가, 현재가, 당일거래대금, 일봉이평5, 일봉이평10, 일봉이평20, 일봉이평60, 일봉이평120, 일봉이평240
            else:
                new_data = [일봉일자, 시가, 고가, 저가, 현재가, 당일거래대금, 일봉이평5, 일봉이평10, 일봉이평20, 일봉이평60, 일봉이평120, 일봉이평240]
                self.dict_day_ar[종목코드] = np.r_[self.dict_day_ar[종목코드], np.array([new_data])]
                if len(self.dict_day_ar[종목코드]) > 250:
                    self.dict_day_ar[종목코드] = np.delete(self.dict_day_ar[종목코드], 0, 0)
                self.queryQ.put(('코인일봉', new_dbdata_day, 종목코드, 'append'))

            if self.chart_code == 종목코드:
                self.windowQ.put((ui_num['일봉차트'], 종목코드, self.dict_day_ar[종목코드][-120:]))

        if 틱수신시간 != 0:
            if self.dict_tik_ar2:
                data = ('코인디비', self.dict_tik_ar2)
                self.queryQ.put(data)
                self.dict_tik_ar2 = {}

            gap = (now() - 틱수신시간).total_seconds()
            self.windowQ.put((ui_num['C단순텍스트'], f'전략스 연산 시간 알림 - 수신시간과 연산시간의 차이는 [{gap:.6f}]초입니다.'))

    def Buy(self, 종목코드, BUY_LONG, 현재가, 매도호가1, 매수호가1, 매수수량, 데이터길이):
        구분 = 'BUY_LONG' if BUY_LONG else 'SELL_SHORT'
        if '지정가' in self.dict_set['코인매수주문구분']:
            기준가격 = 현재가
            if self.dict_set['코인매수지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1 if BUY_LONG else 매수호가1
            if self.dict_set['코인매수지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1 if BUY_LONG else 매도호가1
            self.dict_signal[구분].append(종목코드)
            self.dict_sgn_tik[종목코드] = 데이터길이 - 1
            self.ctraderQ.put((구분, 종목코드, 기준가격, 매수수량, now(), False))
        else:
            남은수량 = 매수수량
            직전남은수량 = 매수수량
            매수금액 = 0
            hogainfo = self.bhogainfo if BUY_LONG else self.shogainfo
            hogainfo = hogainfo[self.dict_set['코인매수시장가잔량범위']]
            for 호가, 잔량 in hogainfo.items():
                남은수량 -= 잔량
                if 남은수량 <= 0:
                    매수금액 += 호가 * 직전남은수량
                    break
                else:
                    매수금액 += 호가 * 잔량
                    직전남은수량 = 남은수량
            if 남은수량 <= 0:
                예상체결가 = round(매수금액 / 매수수량, 8) if 매수수량 != 0 else 0
                self.dict_signal[구분].append(종목코드)
                self.dict_sgn_tik[종목코드] = 데이터길이 - 1
                self.ctraderQ.put((구분, 종목코드, 예상체결가, 매수수량, now(), False))

    def Sell(self, 종목코드, 포지션, SELL_LONG, 현재가, 매도호가1, 매수호가1, 매도수량, 강제청산):
        구분 = 'SELL_LONG' if 포지션 == 'LONG' and SELL_LONG else 'BUY_SHORT'
        if '지정가' in self.dict_set['코인매도주문구분'] and not 강제청산:
            기준가격 = 현재가
            if self.dict_set['코인매도지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1 if 구분 == 'SELL_LONG' else 매수호가1
            if self.dict_set['코인매도지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1 if 구분 == 'SELL_LONG' else 매도호가1
            self.dict_signal[구분].append(종목코드)
            self.ctraderQ.put((구분, 종목코드, 기준가격, 매도수량, now(), False))
        else:
            남은수량 = 매도수량
            직전남은수량 = 매도수량
            매도금액 = 0
            hogainfo = self.shogainfo if 구분 == 'SELL_LONG' else self.bhogainfo
            hogainfo = hogainfo[self.dict_set['코인매도시장가잔량범위']]
            for 호가, 잔량 in hogainfo.items():
                남은수량 -= 잔량
                if 남은수량 <= 0:
                    매도금액 += 호가 * 직전남은수량
                    break
                else:
                    매도금액 += 호가 * 잔량
                    직전남은수량 = 남은수량
            if 남은수량 <= 0:
                예상체결가 = round(매도금액 / 매도수량, 8) if 매도수량 != 0 else 0
                self.dict_signal[구분].append(종목코드)
                self.ctraderQ.put((구분, 종목코드, 예상체결가, 매도수량, now(), True if 강제청산 else False))

    def PutGsjmAndDeleteHilo(self):
        self.df_gj.sort_values(by=['d_money'], ascending=False, inplace=True)
        self.windowQ.put((ui_num['C관심종목'], self.df_gj))
        for code in list(self.dict_hilo.keys()):
            if code not in self.df_jg.index:
                del self.dict_hilo[code]
