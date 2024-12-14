import math
# noinspection PyUnresolvedReferences
import talib
import sqlite3
import datetime
# noinspection PyUnresolvedReferences
import numpy as np
import pandas as pd
from traceback import print_exc
from utility.setting import DB_COIN_BACK, BACK_TEMP, ui_num, DICT_SET
# noinspection PyUnresolvedReferences
from utility.static import strp_time, timedelta_sec, strf_time, timedelta_day, GetUpbitHogaunit, pickle_read, pickle_write, GetUpbitPgSgSp
from backtester.back_static import GetBuyStg, GetSellStg, GetBuyConds, GetSellConds, GetBackloadCodeQuery, GetBackloadDayQuery, AddAvgData, GetTradeInfo


class CoinUpbitBackEngine:
    def __init__(self, gubun, wq, pq, tq, bq, ctq_list, profile=False):
        self.gubun        = gubun
        self.wq           = wq
        self.pq           = pq
        self.tq           = tq
        self.bq           = bq
        self.ctq_list     = ctq_list
        self.profile      = profile
        self.dict_set     = DICT_SET

        self.total_ticks  = 0
        self.total_secds  = 0
        self.total_count  = 0

        self.pr           = None
        self.back_type    = None
        self.betting      = None
        self.avgtime      = None
        self.avg_list     = None
        self.startday     = None
        self.endday       = None
        self.starttime    = None
        self.endtime      = None

        self.startday_    = None
        self.endday_      = None
        self.starttime_   = None
        self.endtime_     = None

        self.buystg       = None
        self.sellstg      = None
        self.dict_cn      = None
        self.dict_mt      = None
        self.dict_kd      = None
        self.array_tick   = None

        self.is_long      = None
        self.dict_hg      = None

        self.code_list    = []
        self.vars         = []
        self.vars_list    = []
        self.vars_lists   = []
        self.buy_info     = []
        self.dict_tik_ar  = {}
        self.dict_day_ar  = {}
        self.dict_min_ar  = {}
        self.dict_dindex  = {}
        self.dict_mindex  = {}
        self.bhogainfo    = {}
        self.shogainfo    = {}
        self.dict_cond    = {}
        self.dict_buystg  = {}
        self.dict_sellstg = {}
        self.didict_cond  = {}
        self.sell_cond    = 0
        self.vars_turn    = 0
        self.vars_count   = 0
        self.vars_key     = 0
        self.high_var     = 0

        self.code         = ''
        self.name         = ''
        self.day_info     = {}
        self.trade_info   = {}
        self.current_min  = []
        self.index        = 0
        self.indexn       = 0
        self.dindex       = 0
        self.mindex       = 0
        self.tick_count   = 0

        self.Start()

    def Start(self):
        while True:
            data = self.pq.get()
            if '정보' in data[0]:
                if self.back_type == '최적화':
                    if data[0] == '백테정보':
                        self.betting    = data[1]
                        avg_list        = data[2]
                        self.startday   = data[3]
                        self.endday     = data[4]
                        self.starttime  = data[5]
                        self.endtime    = data[6]
                        self.buystg     = GetBuyStg(data[7])
                        self.sellstg, self.dict_cond = GetSellStg(data[8])
                        self.CheckAvglist(avg_list)
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop()
                    elif data[0] == '변수정보':
                        self.vars_list  = data[1]
                        self.vars_turn  = data[2]
                        self.vars       = [var[-1] for var in self.vars_list]
                        self.high_var   = self.vars[self.vars_turn]
                        self.vars_count = 1 if self.vars_turn < 0 else len(self.vars_list[self.vars_turn]) - 1
                        self.InitDayInfo()
                        self.InitTradeInfo()
                        self.BackTest()
                elif self.back_type == 'GA최적화':
                    if data[0] == '백테정보':
                        self.betting    = data[1]
                        avg_list        = data[2]
                        self.startday   = data[3]
                        self.endday     = data[4]
                        self.starttime  = data[5]
                        self.endtime    = data[6]
                        self.buystg     = GetBuyStg(data[7])
                        self.sellstg, self.dict_cond = GetSellStg(data[8])
                        self.CheckAvglist(avg_list)
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop()
                    elif data[0] == '변수정보':
                        self.vars_lists = data[1]
                        self.vars_count = 10
                        self.InitDayInfo()
                        self.InitTradeInfo()
                        self.BackTest()
                elif self.back_type == '조건최적화':
                    if data[0] == '백테정보':
                        self.betting    = data[1]
                        self.avgtime    = data[2]
                        self.startday   = data[3]
                        self.endday     = data[4]
                        self.starttime  = data[5]
                        self.endtime    = data[6]
                    elif data[0] == '조건정보':
                        self.dict_buystg  = {}
                        self.dict_sellstg = {}
                        self.didict_cond  = {}
                        error = False
                        for i in range(10):
                            buystg = GetBuyConds(data[1][i])
                            sellstg, dict_cond = GetSellConds(data[2][i])
                            self.dict_buystg[i]  = buystg
                            self.dict_sellstg[i] = sellstg
                            self.didict_cond[i]  = dict_cond
                            if buystg is None or sellstg is None: error = True
                        self.vars_count = 10
                        self.InitDayInfo()
                        self.InitTradeInfo()
                        if error:
                            self.BackStop()
                        else:
                            self.BackTest()
                elif self.back_type == '전진분석':
                    if data[0] == '백테정보':
                        self.betting    = data[1]
                        avg_list        = data[2]
                        self.starttime  = data[3]
                        self.endtime    = data[4]
                        self.buystg     = GetBuyStg(data[5])
                        self.sellstg, self.dict_cond = GetSellStg(data[6])
                        self.CheckAvglist(avg_list)
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop()
                    elif data[0] == '변수정보':
                        self.vars_list  = data[1]
                        self.vars_turn  = data[2]
                        self.vars       = [var[-1] for var in self.vars_list]
                        self.high_var   = self.vars[self.vars_turn]
                        self.vars_count = 1 if self.vars_turn < 0 else len(self.vars_list[self.vars_turn]) - 1
                        self.startday   = data[3]
                        self.endday     = data[4]
                        self.InitDayInfo()
                        self.InitTradeInfo()
                        self.BackTest()
                elif self.back_type == '백테스트':
                    if data[0] == '백테정보':
                        self.betting    = data[1]
                        self.avgtime    = data[2]
                        self.startday   = data[3]
                        self.endday     = data[4]
                        self.starttime  = data[5]
                        self.endtime    = data[6]
                        self.buystg     = GetBuyStg(data[7])
                        self.sellstg, self.dict_cond = GetSellStg(data[8])
                        self.vars_count = 1
                        self.InitDayInfo()
                        self.InitTradeInfo()
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop()
                        else:
                            start = datetime.datetime.now()
                            self.BackTest()
                            self.total_secds = (datetime.datetime.now() - start).total_seconds()
                elif self.back_type == '백파인더':
                    if data[0] == '백테정보':
                        self.avgtime    = data[1]
                        self.startday   = data[2]
                        self.endday     = data[3]
                        self.starttime  = data[4]
                        self.endtime    = data[5]
                        self.vars_count = 1
                        self.InitDayInfo()
                        self.InitTradeInfo()
                        try:
                            self.buystg = compile(data[6], '<string>', 'exec')
                        except:
                            if self.gubun == 0: print_exc()
                            self.BackStop()
                        else:
                            self.BackTest()
            elif data[0] == '백테유형':
                self.back_type = data[1]
            elif data[0] == '설정변경':
                self.dict_set = data[1]
            elif data[0] == '종목명거래대금순위':
                self.dict_mt = data[1]
            elif data[0] in ['데이터크기', '데이터로딩']:
                self.DataLoad(data)
            elif data[0] == '벤치점수요청':
                self.bq.put([self.total_ticks, self.total_secds, round(self.total_ticks / self.total_secds, 2)])

    def InitDayInfo(self):
        self.tick_count = 0

    def InitTradeInfo(self):
        v = GetTradeInfo(1)
        if self.vars_count == 1:
            self.trade_info = {0: v}
        else:
            self.trade_info = {k: v for k in range(self.vars_count)}

    def DataLoad(self, data):
        bk = 0
        divid_mode = data[-2]
        con = sqlite3.connect(DB_COIN_BACK)

        if divid_mode == '종목코드별 분류':
            gubun, startday, endday, starttime, endtime, code_list, avg_list, code_days, _, _, _ = data
            for code in code_list:
                df_tick, len_df_tick = None, 0
                try:
                    df_tick = pd.read_sql(GetBackloadCodeQuery(code, code_days[code], starttime, endtime), con)
                    len_df_tick = len(df_tick)
                except:
                    pass
                if gubun == '데이터크기':
                    self.total_ticks += len_df_tick
                    self.bq.put([code, len_df_tick])
                elif len_df_tick > 0:
                    AddAvgData(df_tick, 8, avg_list)
                    arry_tick = np.array(df_tick)
                    if self.dict_set['백테일괄로딩']:
                        self.dict_tik_ar[code] = arry_tick
                    else:
                        pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_tick', arry_tick)
                    self.code_list.append(code)
                    bk += 1
        elif divid_mode == '일자별 분류':
            gubun, startday, endday, starttime, endtime, day_list, avg_list, code_days, day_codes, _, _ = data
            if gubun == '데이터크기':
                for day in day_list:
                    len_df_tick = 0
                    for code in day_codes[day]:
                        try:
                            df_tick = pd.read_sql(GetBackloadDayQuery(day, code, starttime, endtime), con)
                            len_df_tick += len(df_tick)
                        except:
                            pass
                    self.total_ticks += len_df_tick
                    self.bq.put([day, len_df_tick])
            elif gubun == '데이터로딩':
                code_list = []
                for day in day_list:
                    for code in day_codes[day]:
                        if code not in code_list:
                            code_list.append(code)
                for code in code_list:
                    days = [day for day in day_list if day in code_days[code]]
                    df_tick, len_df_tick = None, 0
                    try:
                        df_tick = pd.read_sql(GetBackloadCodeQuery(code, days, starttime, endtime), con)
                        len_df_tick += len(df_tick)
                    except:
                        pass
                    if len_df_tick > 0:
                        AddAvgData(df_tick, 8, avg_list)
                        arry_tick = np.array(df_tick)
                        if self.dict_set['백테일괄로딩']:
                            self.dict_tik_ar[code] = arry_tick
                        else:
                            pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_tick', arry_tick)
                        self.code_list.append(code)
                        bk += 1
        else:
            gubun, startday, endday, starttime, endtime, day_list, avg_list, _, _, _, code = data
            if gubun == '데이터크기':
                for day in day_list:
                    len_df_tick = 0
                    try:
                        df_tick = pd.read_sql(GetBackloadDayQuery(day, code, starttime, endtime), con)
                        len_df_tick = len(df_tick)
                    except:
                        pass
                    self.total_ticks += len_df_tick
                    self.bq.put([day, len_df_tick])
            elif gubun == '데이터로딩':
                df_tick, len_df_tick = None, 0
                try:
                    df_tick = pd.read_sql(GetBackloadCodeQuery(code, day_list, starttime, endtime), con)
                    len_df_tick = len(df_tick)
                except:
                    pass

                if len_df_tick > 0:
                    AddAvgData(df_tick, 8, avg_list)
                    arry_tick = np.array(df_tick)
                    if self.dict_set['백테일괄로딩']:
                        self.dict_tik_ar[code] = arry_tick
                    else:
                        pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_tick', arry_tick)
                    self.code_list.append(code)
                    bk += 1

        con.close()
        if gubun == '데이터로딩':
            self.bq.put(bk)
            self.avg_list = avg_list
            self.startday_, self.endday_, self.starttime_, self.endtime_ = startday, endday, starttime, endtime

    def CheckAvglist(self, avg_list):
        not_in_list = [x for x in avg_list if x not in self.avg_list]
        if len(not_in_list) > 0 and self.gubun == 0:
            self.wq.put([ui_num['C백테스트'], '백테엔진 구동 시 포함되지 않은 평균값 틱수를 사용하여 중지되었습니다.'])
            self.wq.put([ui_num['C백테스트'], '누락된 평균값 틱수를 추가하여 백테엔진을 재시작하십시오.'])
            self.BackStop()

    def BackStop(self):
        self.back_type = None
        if self.gubun == 0: self.wq.put([ui_num['C백테스트'], '전략 코드 오류로 백테스트를 중지합니다.'])

    def BackTest(self):
        if self.profile:
            import cProfile
            self.pr = cProfile.Profile()
            self.pr.enable()

        same_days = self.startday_ == self.startday and self.endday_ == self.endday
        same_time = self.starttime_ == self.starttime and self.endtime_ == self.endtime
        for code in self.code_list:
            self.code = self.name = code
            self.total_count = 0

            if not self.dict_set['백테일괄로딩']:
                self.dict_tik_ar = {code: pickle_read(f'{BACK_TEMP}/{self.gubun}_{code}_tick')}

            if same_days and same_time:
                self.array_tick = self.dict_tik_ar[code]
            elif same_time:
                self.array_tick = self.dict_tik_ar[code][(self.dict_tik_ar[code][:, 0] >= self.startday * 1000000) &
                                                         (self.dict_tik_ar[code][:, 0] <= self.endday * 1000000 + 240000)]
            elif same_days:
                self.array_tick = self.dict_tik_ar[code][(self.dict_tik_ar[code][:, 0] % 1000000 >= self.starttime) &
                                                         (self.dict_tik_ar[code][:, 0] % 1000000 <= self.endtime)]
            else:
                self.array_tick = self.dict_tik_ar[code][(self.dict_tik_ar[code][:, 0] >= self.startday * 1000000) &
                                                         (self.dict_tik_ar[code][:, 0] <= self.endday * 1000000 + 240000) &
                                                         (self.dict_tik_ar[code][:, 0] % 1000000 >= self.starttime) &
                                                         (self.dict_tik_ar[code][:, 0] % 1000000 <= self.endtime)]

            if len(self.array_tick) > 0:
                last = len(self.array_tick) - 1
                for i, index in enumerate(self.array_tick[:, 0]):
                    if self.back_type is None: return
                    next_day_change = i != last and str(index)[:8] != str(self.array_tick[i + 1, 0])[:8]
                    self.tick_count += 1
                    self.index  = int(index)
                    self.indexn = i

                    if i != last and not next_day_change:
                        self.Strategy()
                    else:
                        self.LastSell()
                        self.InitDayInfo()
                        self.InitTradeInfo()

            self.tq.put(['백테완료', 1 if self.total_count > 0 else 0])

        if self.profile:
            self.pr.print_stats(sort='cumulative')

    def Strategy(self):
        def now_utc():
            return strp_time('%Y%m%d%H%M%S', str(self.index))

        def Parameter_Previous(number, pre):
            if pre != -1:
                return self.array_tick[self.indexn - pre, number]
            else:
                return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], number]

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
                if pre != -1:
                    return self.array_tick[self.indexn - pre, 35]
                else:
                    return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 35]
            elif tick == 300:
                if pre != -1:
                    return self.array_tick[self.indexn - pre, 36]
                else:
                    return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 36]
            elif tick == 600:
                if pre != -1:
                    return self.array_tick[self.indexn - pre, 37]
                else:
                    return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 37]
            elif tick == 1200:
                if pre != -1:
                    return self.array_tick[self.indexn - pre, 38]
                else:
                    return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 38]
            else:
                if pre != -1:
                    return round(self.array_tick[self.indexn + 1 - tick - pre:self.indexn + 1 - pre, 1].mean(), 8)
                else:
                    bindex = self.trade_info[self.vars_key]['매수틱번호']
                    return round(self.array_tick[bindex + 1 - tick:bindex + 1, 1].mean(), 8)

        def GetArrayIndex(bc):
            return bc + 10 * self.avg_list.index(self.avgtime if self.back_type in ['백테스트', '조건최적화', '백파인더'] else self.vars[0])

        def Parameter_Area(aindex, vindex, tick, pre, gubun_):
            if tick in self.avg_list:
                if pre != -1:
                    return self.array_tick[self.indexn - pre, GetArrayIndex(aindex)]
                else:
                    return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], GetArrayIndex(aindex)]
            else:
                if pre != -1:
                    if gubun_ == 'max':
                        return self.array_tick[self.indexn + 1 - tick - pre:self.indexn + 1 - pre, vindex].max()
                    elif gubun_ == 'min':
                        return self.array_tick[self.indexn + 1 - tick - pre:self.indexn + 1 - pre, vindex].min()
                    elif gubun_ == 'sum':
                        return self.array_tick[self.indexn + 1 - tick - pre:self.indexn + 1 - pre, vindex].sum()
                    else:
                        return self.array_tick[self.indexn + 1 - tick - pre:self.indexn + 1 - pre, vindex].mean()
                else:
                    bindex = self.trade_info[self.vars_key]['매수틱번호']
                    if gubun_ == 'max':
                        return self.array_tick[bindex + 1 - tick:bindex + 1, vindex].max()
                    elif gubun_ == 'min':
                        return self.array_tick[bindex + 1 - tick:bindex + 1, vindex].min()
                    else:
                        return self.array_tick[bindex + 1 - tick:bindex + 1, vindex].mean()

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

        def 누적초당매수수량(tick, pre=0):
            return Parameter_Area(45, 14, tick, pre, 'sum')

        def 최고초당매도수량(tick, pre=0):
            return Parameter_Area(46, 15, tick, pre, 'max')

        def 누적초당매도수량(tick, pre=0):
            return Parameter_Area(47, 15, tick, pre, 'sum')

        def 초당거래대금평균(tick, pre=0):
            return Parameter_Area(48, 19, tick, pre, 'mean')

        def 당일거래대금각도(tick, pre=0):
            if pre != -1:
                dmp_gap = self.array_tick[self.indexn - pre, 6] - self.array_tick[self.indexn + 1 - tick - pre, 6]
            else:
                dmp_gap = self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 6] - self.array_tick[self.trade_info[self.vars_key]['매수틱번호'] + 1 - tick, 6]
            return round(math.atan2(dmp_gap, tick) / (2 * math.pi) * 360, 2)

        현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 초당매수수량, 초당매도수량, 초당거래대금, 고저평균대비등락율, 매도총잔량, \
            매수총잔량, 매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합 = self.array_tick[self.indexn, 1:35]
        종목코드, 데이터길이, 시분초, 호가단위 = self.code, self.tick_count, int(str(self.index)[8:]), GetUpbitHogaunit(현재가)

        if self.back_type == '백파인더':
            if self.tick_count < self.avgtime:
                return

            매수 = True
            try:
                exec(self.buystg, None, locals())
            except:
                if self.gubun == 0: print_exc()
                self.BackStop()
        else:
            bhogainfo = ((매도호가1, 매도잔량1), (매도호가2, 매도잔량2), (매도호가3, 매도잔량3), (매도호가4, 매도잔량4), (매도호가5, 매도잔량5))
            shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
            self.bhogainfo = bhogainfo[:self.dict_set['코인매수시장가잔량범위']]
            self.shogainfo = shogainfo[:self.dict_set['코인매도시장가잔량범위']]

            for j in range(self.vars_count):
                if self.back_type is None: return
                self.vars_key = j
                if self.back_type in ['백테스트', '조건최적화']:
                    if self.tick_count < self.avgtime:
                        return
                else:
                    if self.back_type == 'GA최적화':
                        self.vars = self.vars_lists[j]
                    elif self.vars_turn >= 0:
                        curr_var = self.vars_list[self.vars_turn][j]
                        if curr_var == self.high_var:
                            continue
                        self.vars[self.vars_turn] = curr_var

                    if self.tick_count < self.vars[0]:
                        if self.vars_turn == 0:
                            continue
                        else:
                            return

                try:
                    if not self.trade_info[j]['보유중']:
                        try:
                            if self.code not in self.dict_mt[self.index]:
                                continue
                        except:
                            continue

                        self.trade_info[j]['주문수량'] = int(self.betting / 현재가)
                        매수 = True
                        if self.back_type != '조건최적화':
                            exec(self.buystg, None, locals())
                        else:
                            exec(self.dict_buystg[j], None, locals())
                    else:
                        _, 매수가, _, _, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간 = self.trade_info[j].values()
                        매수금액 = 보유수량 * 매수가
                        평가금액 = 보유수량 * 현재가
                        _, 수익금, 수익률 = GetUpbitPgSgSp(매수금액, 평가금액)
                        if 수익률 > 최고수익률:
                            self.trade_info[j]['최고수익률'] = 최고수익률 = 수익률
                        elif 수익률 < 최저수익률:
                            self.trade_info[j]['최저수익률'] = 최저수익률 = 수익률
                        보유시간 = (now_utc() - 매수시간).total_seconds()

                        self.trade_info[j]['주문수량'] = 보유수량
                        매도 = False
                        if self.back_type != '조건최적화':
                            exec(self.sellstg, None, locals())
                        else:
                            exec(self.dict_sellstg[j], None, locals())
                except:
                    if self.gubun == 0: print_exc()
                    self.BackStop()
                    return

    def Buy(self):
        매수수량 = self.trade_info[self.vars_key]['주문수량']
        if 매수수량 > 0:
            남은수량 = 매수수량
            직전남은수량 = 매수수량
            매수금액 = 0
            for 매도호가, 매도잔량 in self.bhogainfo:
                남은수량 -= 매도잔량
                if 남은수량 <= 0:
                    매수금액 += 매도호가 * 직전남은수량
                    break
                else:
                    매수금액 += 매도호가 * 매도잔량
                    직전남은수량 = 남은수량
            if 남은수량 <= 0:
                self.trade_info[self.vars_key] = {
                    '보유중': 1,
                    '매수가': round(매수금액 / 매수수량, 4),
                    '매도가': 0,
                    '주문수량': 매수수량,
                    '보유수량': 매수수량,
                    '최고수익률': 0.,
                    '최저수익률': 0.,
                    '매수틱번호': self.indexn,
                    '매수시간': strp_time('%Y%m%d%H%M%S', str(self.index))
                }

    def Sell(self, sell_cond):
        주문수량 = self.trade_info[self.vars_key]['주문수량']
        남은수량 = 주문수량
        직전남은수량 = 주문수량
        매도금액 = 0
        for 매수호가, 매수잔량 in self.shogainfo:
            남은수량 -= 매수잔량
            if 남은수량 <= 0:
                매도금액 += 매수호가 * 직전남은수량
                break
            else:
                매도금액 += 매수호가 * 매수잔량
                직전남은수량 = 남은수량
        if 남은수량 <= 0:
            self.trade_info[self.vars_key]['매도가'] = round(매도금액 / 주문수량, 4)
            self.sell_cond = sell_cond
            self.CalculationEyun()

    def LastSell(self):
        매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5 = self.array_tick[self.indexn, 14:34]
        shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
        shogainfo = shogainfo[:self.dict_set['코인매도시장가잔량범위']]

        for k in range(self.vars_count):
            self.vars_key = k
            if self.trade_info[self.vars_key]['보유중']:
                남은수량 = self.trade_info[self.vars_key]['보유수량']
                직전남은수량 = 남은수량
                매도금액 = 0
                for 매수호가, 매수잔량 in shogainfo:
                    남은수량 -= 매수잔량
                    if 남은수량 <= 0:
                        매도금액 += 매수호가 * 직전남은수량
                        break
                    else:
                        매도금액 += 매수호가 * 매수잔량
                        직전남은수량 = 남은수량

                보유수량 = self.trade_info[self.vars_key]['보유수량']
                if 남은수량 <= 0:
                    self.trade_info[self.vars_key]['매도가'] = round(매도금액 / 보유수량, 4)
                elif 매도금액 == 0:
                    self.trade_info[self.vars_key]['매도가'] = self.array_tick[self.indexn, 1]
                else:
                    self.trade_info[self.vars_key]['매도가'] = round(매도금액 / (보유수량 - 남은수량), 4)

                self.trade_info[self.vars_key]['주문수량'] = 보유수량
                self.sell_cond = 0
                self.CalculationEyun()

    def CalculationEyun(self):
        self.total_count += 1
        _, 매수가, 매도가, 주문수량, 보유수량, 최고수익률, 최저수익률, 매수틱번호, _ = self.trade_info[self.vars_key].values()
        시가총액 = 0
        매수시간, 매도시간, 보유시간, 매수금액 = int(self.array_tick[매수틱번호, 0]), self.index, self.indexn - 매수틱번호, 주문수량 * 매수가
        매도금액, 수익금, 수익률 = GetUpbitPgSgSp(매수금액, 주문수량 * 매도가)
        매도조건 = self.dict_cond[self.sell_cond] if self.back_type != '조건최적화' else self.didict_cond[self.vars_key][self.sell_cond]
        추가매수시간, 잔량없음 = '', True
        data = ['백테결과', self.name, 시가총액, 매수시간, 매도시간, 보유시간, 매수가, 매도가, 매수금액, 매도금액, 수익률, 수익금, 매도조건, 추가매수시간, 잔량없음, self.vars_key]
        self.ctq_list[self.vars_key].put(data)
        self.trade_info[self.vars_key] = GetTradeInfo(1)
