import math
# noinspection PyUnresolvedReferences
import talib
import sqlite3
import datetime
# noinspection PyUnresolvedReferences
import numpy as np
import pandas as pd
from traceback import print_exc
from backtester.back_static import GetBuyStg, GetSellStg, GetBuyConds, GetSellConds, GetBackloadCodeQuery, GetBackloadDayQuery, AddAvgData
from utility.setting import DB_STOCK_BACK, BACK_TEMP, DICT_SET, DB_STOCK_DAY, DB_STOCK_MIN, ui_num, dict_min, dict_order_ratio
from utility.static import strp_time, timedelta_sec, roundfigure_upper, roundfigure_lower, pickle_read, pickle_write, strf_time, timedelta_day, GetKiwoomPgSgSp, GetUvilower5, GetHogaunit


class StockBackEngine4:
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

        self.code         = None
        self.name         = None
        self.day_info     = None
        self.trade_info   = None
        self.current_min  = None
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
                        self.vars_turn  = -1
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
                self.dict_cn = data[1]
                self.dict_mt = data[2]
                self.dict_kd = data[3]
            elif data[0] in ['데이터크기', '데이터로딩']:
                self.DataLoad(data)
            elif data[0] == '벤치점수요청':
                self.bq.put([self.total_ticks, self.total_secds, round(self.total_ticks / self.total_secds, 2)])

    def InitDayInfo(self):
        self.tick_count = 0
        v = {
            '손절횟수': 0,
            '거래횟수': 0,
            '직전거래시간': strp_time('%Y%m%d', '20000101'),
            '손절매도시간': strp_time('%Y%m%d', '20000101')
        }
        if self.vars_count == 1:
            self.day_info = {0: v}
        else:
            self.day_info = {k: v for k in range(self.vars_count)}

    def InitTradeInfo(self):
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
        if self.vars_count == 1:
            self.trade_info = {0: v}
        else:
            self.trade_info = {k: v for k in range(self.vars_count)}

    def DataLoad(self, data):
        bk = 0
        divid_mode = data[-2]
        con  = sqlite3.connect(DB_STOCK_BACK)
        con2 = sqlite3.connect(DB_STOCK_DAY)
        con3 = sqlite3.connect(DB_STOCK_MIN)

        if divid_mode == '종목코드별 분류':
            gubun, startday, endday, starttime, endtime, code_list, avg_list, code_days, _, _, _ = data
            for code in code_list:
                len_df = 0
                df_min = None
                df_day = None
                try:
                    df = pd.read_sql(GetBackloadCodeQuery(code, code_days[code], starttime, endtime), con)
                    if self.dict_set['주식분봉데이터']:
                        df1 = []
                        query = f"SELECT * FROM '{code}' WHERE 체결시간 < {startday * 1000000} ORDER BY 체결시간 DESC LIMIT {self.dict_set['주식분봉개수']}"
                        df2 = pd.read_sql(query, con3)
                        df1.append(df2[::-1])
                        query = f"SELECT * FROM '{code}' WHERE 체결시간 >= {startday * 1000000} and 체결시간 <= {endday * 1000000 + 240000}"
                        df2 = pd.read_sql(query, con3)
                        df1.append(df2)
                        df_min = pd.concat(df1)
                    if self.dict_set['주식일봉데이터']:
                        startday_ = int(strf_time('%Y%m%d', timedelta_day(-250, strp_time('%Y%m%d', str(startday)))))
                        query = f"SELECT * FROM '{code}' WHERE 일자 >= {startday_} and 일자 <= {endday}"
                        df_day = pd.read_sql(query, con2)
                except:
                    pass
                else:
                    len_df = len(df)
                    if len_df > 0 and gubun == '데이터로딩':
                        df = AddAvgData(df, 3, avg_list)
                        data = df.to_numpy()
                        if self.dict_set['백테일괄로딩']:
                            self.dict_tik_ar[code] = data
                        else:
                            pickle_write(f'{BACK_TEMP}/{code}', data)
                        if self.dict_set['주식분봉데이터']:
                            self.dict_min_ar[code] = df_min.to_numpy()
                            self.dict_mindex[code] = {}
                            for i, index in enumerate(self.dict_min_ar[code][:, 0]):
                                self.dict_mindex[code][index] = i
                        if self.dict_set['주식일봉데이터']:
                            self.dict_day_ar[code] = df_day.to_numpy()
                            self.dict_dindex[code] = {}
                            for i, index in enumerate(self.dict_day_ar[code][:, 0]):
                                self.dict_dindex[code][index] = i
                        self.code_list.append(code)
                        bk += 1
                if gubun == '데이터크기':
                    self.total_ticks += len_df
                    self.bq.put_nowait([code, len_df])
        elif divid_mode == '일자별 분류':
            gubun, startday, endday, starttime, endtime, day_list, avg_list, code_days, day_codes, _, _ = data
            if gubun == '데이터크기':
                for day in day_list:
                    len_df = 0
                    for code in day_codes[day]:
                        try:
                            df = pd.read_sql(GetBackloadDayQuery(day, code, starttime, endtime), con)
                        except:
                            pass
                        else:
                            len_df += len(df)
                    self.total_ticks += len_df
                    self.bq.put_nowait([day, len_df])
            elif gubun == '데이터로딩':
                code_list = []
                for day in day_list:
                    for code in day_codes[day]:
                        if code not in code_list:
                            code_list.append(code)
                for code in code_list:
                    days      = [day for day in day_list if day in code_days[code]]
                    startday_ = days[0]
                    endday_   = days[-1]
                    df_min    = None
                    df_day    = None
                    try:
                        df = pd.read_sql(GetBackloadCodeQuery(code, days, starttime, endtime), con)
                        if self.dict_set['주식분봉데이터']:
                            df1 = []
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 < {startday_ * 1000000} ORDER BY 체결시간 DESC LIMIT {self.dict_set['주식분봉개수']}"
                            df2 = pd.read_sql(query, con3)
                            df1.append(df2[::-1])
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 >= {startday_ * 1000000} and 체결시간 <= {endday_ * 1000000 + 240000}"
                            df2 = pd.read_sql(query, con3)
                            df1.append(df2)
                            df_min = pd.concat(df1)
                        if self.dict_set['주식일봉데이터']:
                            startday_ = int(strf_time('%Y%m%d', timedelta_day(-250, strp_time('%Y%m%d', str(startday_)))))
                            query = f"SELECT * FROM '{code}' WHERE 일자 >= {startday_} and 일자 <= {endday_}"
                            df_day = pd.read_sql(query, con2)
                    except:
                        pass
                    else:
                        if len(df) > 0:
                            df = AddAvgData(df, 3, avg_list)
                            arry = df.to_numpy()
                            if self.dict_set['백테일괄로딩']:
                                self.dict_tik_ar[code] = arry
                            else:
                                pickle_write(f'{BACK_TEMP}/{code}', arry)
                            if self.dict_set['주식분봉데이터']:
                                self.dict_min_ar[code] = df_min.to_numpy()
                                self.dict_mindex[code] = {}
                                for i, index in enumerate(self.dict_min_ar[code][:, 0]):
                                    self.dict_mindex[code][index] = i
                            if self.dict_set['주식일봉데이터']:
                                self.dict_day_ar[code] = df_day.to_numpy()
                                self.dict_dindex[code] = {}
                                for i, index in enumerate(self.dict_day_ar[code][:, 0]):
                                    self.dict_dindex[code][index] = i
                            self.code_list.append(code)
                            bk += 1
        else:
            gubun, startday, endday, starttime, endtime, day_list, avg_list, _, _, _, code = data
            if gubun == '데이터크기':
                for day in day_list:
                    len_df = 0
                    try:
                        df = pd.read_sql(GetBackloadDayQuery(day, code, starttime, endtime), con)
                    except:
                        pass
                    else:
                        len_df = len(df)
                    self.total_ticks += len_df
                    self.bq.put_nowait([day, len_df])
            elif gubun == '데이터로딩':
                for code in self.code_list:
                    startday_ = day_list[0]
                    endday_   = day_list[-1]
                    df_min    = None
                    df_day    = None
                    try:
                        df = pd.read_sql(GetBackloadCodeQuery(code, day_list, starttime, endtime), con)
                        if self.dict_set['주식분봉데이터']:
                            df1 = []
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 < {startday_ * 1000000} ORDER BY 체결시간 DESC LIMIT {self.dict_set['주식분봉개수']}"
                            df2 = pd.read_sql(query, con3)
                            df1.append(df2[::-1])
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 >= {startday_ * 1000000} and 체결시간 <= {endday_ * 1000000 + 240000}"
                            df2 = pd.read_sql(query, con3)
                            df1.append(df2)
                            df_min = pd.concat(df1)
                        if self.dict_set['주식일봉데이터']:
                            startday_ = int(strf_time('%Y%m%d', timedelta_day(-250, strp_time('%Y%m%d', str(startday_)))))
                            query = f"SELECT * FROM '{code}' WHERE 일자 >= {startday_} and 일자 <= {endday_}"
                            df_day = pd.read_sql(query, con2)
                    except:
                        pass
                    else:
                        if len(df) > 0:
                            df = AddAvgData(df, 3, avg_list)
                            arry = df.to_numpy()
                            if self.dict_set['백테일괄로딩']:
                                self.dict_tik_ar[code] = arry
                            else:
                                pickle_write(f'{BACK_TEMP}/{code}', arry)
                            if self.dict_set['주식분봉데이터']:
                                self.dict_min_ar[code] = df_min.to_numpy()
                                self.dict_mindex[code] = {}
                                for i, index in enumerate(self.dict_min_ar[code][:, 0]):
                                    self.dict_mindex[code][index] = i
                            if self.dict_set['주식일봉데이터']:
                                self.dict_day_ar[code] = df_day.to_numpy()
                                self.dict_dindex[code] = {}
                                for i, index in enumerate(self.dict_day_ar[code][:, 0]):
                                    self.dict_dindex[code][index] = i
                            self.code_list.append(code)
                            bk += 1

        con3.close()
        con2.close()
        con.close()
        if gubun == '데이터로딩':
            self.bq.put_nowait(bk)
        self.avg_list = avg_list
        self.startday_, self.endday_, self.starttime_, self.endtime_ = startday, endday, starttime, endtime

    def CheckAvglist(self, avg_list):
        not_in_list = [x for x in avg_list if x not in self.avg_list]
        if len(not_in_list) > 0 and self.gubun == 0:
            self.wq.put([ui_num['S백테스트'], '백테엔진 구동 시 포함되지 않은 평균값 틱수를 사용하여 중지되었습니다.'])
            self.wq.put([ui_num['S백테스트'], '누락된 평균값 틱수를 추가하여 백테엔진을 재시작하십시오.'])
            self.BackStop()

    def BackStop(self):
        self.back_type = None
        if self.gubun == 0: self.wq.put([ui_num['S백테스트'], '전략 코드 오류로 백테스트를 중지합니다.'])

    def BackTest(self):
        if self.profile:
            import cProfile
            self.pr = cProfile.Profile()
            self.pr.enable()

        same_days = self.startday_ == self.startday and self.endday_ == self.endday
        same_time = self.starttime_ == self.starttime and self.endtime_ == self.endtime
        for code in self.code_list:
            self.code = code
            self.name = self.dict_cn[self.code] if self.code in self.dict_cn.keys() else self.code
            self.total_count = 0

            if self.dict_set['백테주문관리적용'] and self.dict_set['주식매수금지블랙리스트'] and self.code in self.dict_set['주식블랙리스트'] and self.back_type != '백파인더':
                self.tq.put(['백테완료', 0])
                continue

            if not self.dict_set['백테일괄로딩']:
                self.dict_tik_ar = {code: pickle_read(f'{BACK_TEMP}/{code}')}

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
                    next_day_change = i != last and index + 500000 < self.array_tick[i + 1, 0]
                    self.tick_count += 1
                    self.index  = int(index)
                    self.indexn = i

                    try:
                        if self.dict_set['주식분봉데이터']:
                            self.mindex = self.dict_mindex[code][int(str(self.index)[:10] + dict_min[self.dict_set['주식분봉기간']][str(self.index)[10:12]] + '00')]
                            self.UpdateCurrentMin(i)
                        if self.dict_set['주식일봉데이터']:
                            self.dindex = self.dict_dindex[code][int(str(self.index)[:8])]
                    except:
                        continue

                    if i != last and not next_day_change:
                        self.Strategy()
                    else:
                        self.LastSell()
                        self.InitDayInfo()

            self.tq.put(['백테완료', 1 if self.total_count > 0 else 0])

        if self.profile:
            self.pr.print_stats(sort='cumulative')

    def UpdateCurrentMin(self, i):
        현재가 = self.array_tick[i, 1]
        초당거래대금 = self.array_tick[i, 19]
        if self.current_min is None or self.mindex != self.current_min[0]:
            self.current_min = [self.mindex, 현재가, 현재가, 현재가, 초당거래대금]
        else:
            분봉고가, 분봉저가, 분봉거래대금 = self.current_min[2:]
            분봉고가 = 현재가 if 현재가 > 분봉고가 else 분봉고가
            분봉저가 = 현재가 if 현재가 < 분봉저가 else 분봉저가
            분봉거래대금 += 초당거래대금
            self.current_min[2:] = 분봉고가, 분봉저가, 분봉거래대금

    def Strategy(self):
        def now():
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

        def 거래대금증감N(pre):
            return Parameter_Previous(8, pre)

        def 전일비N(pre):
            return Parameter_Previous(9, pre)

        def 회전율N(pre):
            return Parameter_Previous(10, pre)

        def 전일동시간비N(pre):
            return Parameter_Previous(11, pre)

        def 시가총액N(pre):
            return Parameter_Previous(12, pre)

        def 라운드피겨위5호가이내N(pre):
            return Parameter_Previous(13, pre)

        def 초당매수수량N(pre):
            return Parameter_Previous(14, pre)

        def 초당매도수량N(pre):
            return Parameter_Previous(15, pre)

        def 초당거래대금N(pre):
            return Parameter_Previous(19, pre)

        def 고저평균대비등락율N(pre):
            return Parameter_Previous(20, pre)

        def 매도총잔량N(pre):
            return Parameter_Previous(21, pre)

        def 매수총잔량N(pre):
            return Parameter_Previous(22, pre)

        def 매도호가5N(pre):
            return Parameter_Previous(23, pre)

        def 매도호가4N(pre):
            return Parameter_Previous(24, pre)

        def 매도호가3N(pre):
            return Parameter_Previous(25, pre)

        def 매도호가2N(pre):
            return Parameter_Previous(26, pre)

        def 매도호가1N(pre):
            return Parameter_Previous(27, pre)

        def 매수호가1N(pre):
            return Parameter_Previous(28, pre)

        def 매수호가2N(pre):
            return Parameter_Previous(29, pre)

        def 매수호가3N(pre):
            return Parameter_Previous(30, pre)

        def 매수호가4N(pre):
            return Parameter_Previous(31, pre)

        def 매수호가5N(pre):
            return Parameter_Previous(32, pre)

        def 매도잔량5N(pre):
            return Parameter_Previous(33, pre)

        def 매도잔량4N(pre):
            return Parameter_Previous(34, pre)

        def 매도잔량3N(pre):
            return Parameter_Previous(35, pre)

        def 매도잔량2N(pre):
            return Parameter_Previous(36, pre)

        def 매도잔량1N(pre):
            return Parameter_Previous(37, pre)

        def 매수잔량1N(pre):
            return Parameter_Previous(38, pre)

        def 매수잔량2N(pre):
            return Parameter_Previous(39, pre)

        def 매수잔량3N(pre):
            return Parameter_Previous(40, pre)

        def 매수잔량4N(pre):
            return Parameter_Previous(41, pre)

        def 매수잔량5N(pre):
            return Parameter_Previous(42, pre)

        def 매도수5호가잔량합N(pre):
            return Parameter_Previous(43, pre)

        def 이동평균(tick, pre=0):
            if tick == 60:
                if pre != -1:
                    return self.array_tick[self.indexn - pre, 44]
                else:
                    return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 44]
            elif tick == 300:
                if pre != -1:
                    return self.array_tick[self.indexn - pre, 45]
                else:
                    return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 45]
            elif tick == 600:
                if pre != -1:
                    return self.array_tick[self.indexn - pre, 46]
                else:
                    return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 46]
            elif tick == 1200:
                if pre != -1:
                    return self.array_tick[self.indexn - pre, 47]
                else:
                    return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 47]
            else:
                if pre != -1:
                    return round(self.array_tick[self.indexn + 1 - tick - pre:self.indexn + 1 - pre, 1].mean(), 3)
                else:
                    bindex = self.trade_info[self.vars_key]['매수틱번호']
                    return round(self.array_tick[bindex + 1 - tick:bindex + 1, 1].mean(), 3)

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
            return Parameter_Area(48, 1, tick, pre, 'max')

        def 최저현재가(tick, pre=0):
            return Parameter_Area(49, 1, tick, pre, 'min')

        def 체결강도평균(tick, pre=0):
            return Parameter_Area(50, 7, tick, pre, 'mean')

        def 최고체결강도(tick, pre=0):
            return Parameter_Area(51, 7, tick, pre, 'max')

        def 최저체결강도(tick, pre=0):
            return Parameter_Area(52, 7, tick, pre, 'min')

        def 최고초당매수수량(tick, pre=0):
            return Parameter_Area(53, 14, tick, pre, 'max')

        def 최고초당매도수량(tick, pre=0):
            return Parameter_Area(54, 15, tick, pre, 'max')

        def 누적초당매수수량(tick, pre=0):
            return Parameter_Area(55, 14, tick, pre, 'sum')

        def 누적초당매도수량(tick, pre=0):
            return Parameter_Area(56, 15, tick, pre, 'sum')

        def 초당거래대금평균(tick, pre=0):
            return Parameter_Area(57, 19, tick, pre, 'mean')

        def 당일거래대금각도(tick, pre=0):
            if pre != -1:
                dmp_gap = self.array_tick[self.indexn - pre, 6] - self.array_tick[self.indexn + 1 - tick - pre, 6]
            else:
                dmp_gap = self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 6] - self.array_tick[self.trade_info[self.vars_key]['매수틱번호'] + 1 - tick, 6]
            return round(math.atan2(dmp_gap, tick) / (2 * math.pi) * 360, 2)

        def 전일비각도(tick, pre=0):
            if pre != -1:
                jvp_gap = self.array_tick[self.indexn - pre, 9] - self.array_tick[self.indexn - tick - 1 - pre, 9]
            else:
                jvp_gap = self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], 9] - self.array_tick[self.trade_info[self.vars_key]['매수틱번호'] + 1 - tick, 9]
            return round(math.atan2(jvp_gap, tick) / (2 * math.pi) * 360, 2)

        if self.dict_set['주식분봉데이터']:
            def 분봉시가N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 1]

            def 분봉고가N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 2]

            def 분봉저가N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 3]

            def 분봉현재가N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 4]

            def 분봉거래대금N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 5]

            def 분봉이평5N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 6]

            def 분봉이평10N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 7]

            def 분봉이평20N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 8]

            def 분봉이평60N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 9]

            def 분봉이평120N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 10]

            def 분봉이평240N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 11]

            """ 보조지표 사용예
            def M_BBU_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 43]

            def M_BBM_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 44]

            def M_BBL_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 45]

            def M_RSI_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 46]

            def M_CCI_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 47]

            def M_MACD_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 48]

            def M_MACDS_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 49]

            def M_MACDH_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 50]

            def M_STOCK_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 51]

            def M_STOCD_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 52]

            def M_ATR_N(pre):
                return self.dict_min_ar[self.code][self.mindex - pre, 53]
            """

        if self.dict_set['주식일봉데이터']:
            def 일봉시가N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 1]

            def 일봉고가N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 2]

            def 일봉저가N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 3]

            def 일봉현재가N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 4]

            def 일봉거래대금N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 5]

            def 일봉이평5N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 6]

            def 일봉이평10N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 7]

            def 일봉이평20N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 8]

            def 일봉이평60N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 9]

            def 일봉이평120N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 10]

            def 일봉이평240N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 11]

            """ 보조지표 사용예
            def D_BBU_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 43]

            def D_BBM_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 44]

            def D_BBL_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 45]

            def D_RSI_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 46]

            def D_CCI_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 47]

            def D_MACD_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 48]

            def D_MACDS_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 49]

            def D_MACDH_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 50]

            def D_STOCK_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 51]

            def D_STOCD_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 52]

            def D_ATR_N(pre):
                return self.dict_day_ar[self.code][self.dindex - pre, 53]
            """

        종목명, 종목코드, 데이터길이, 시분초 = self.name, self.code, self.tick_count, int(str(self.index)[8:])
        현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 거래대금증감, 전일비, 회전율, 전일동시간비, 시가총액, 라운드피겨위5호가이내, \
            초당매수수량, 초당매도수량, VI해제시간, VI가격, VI호가단위, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량, \
            매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, \
            매도수5호가잔량합 = self.array_tick[self.indexn, 1:44]
        호가단위 = GetHogaunit(self.dict_kd[종목코드] if 종목코드 in self.dict_kd.keys() else True, 현재가, self.index)
        VI해제시간, VI아래5호가 = strp_time('%Y%m%d%H%M%S', str(int(VI해제시간))), GetUvilower5(VI가격, VI호가단위, self.index)

        if self.dict_set['주식분봉데이터']:
            분봉시가, 분봉고가, 분봉저가, 분봉거래대금 = self.current_min[1:]
            분봉최고종가5, 분봉최고고가5, 분봉최고종가10, 분봉최고고가10, 분봉최고종가20, 분봉최고고가20, 분봉최고종가60, 분봉최고고가60, \
                분봉최고종가120, 분봉최고고가120, 분봉최고종가240, 분봉최고고가240, 분봉최저종가5, 분봉최저저가5, 분봉최저종가10, \
                분봉최저저가10, 분봉최저종가20, 분봉최저저가20, 분봉최저종가60, 분봉최저저가60, 분봉최저종가120, 분봉최저저가120, \
                분봉최저종가240, 분봉최저저가240, 분봉종가합계4, 분봉종가합계9, 분봉종가합계19, 분봉종가합계59, 분봉종가합계119, \
                분봉종가합계239, 분봉최고거래대금 = self.dict_min_ar[종목코드][self.mindex, 12:]
            분봉이평5 = round((분봉종가합계4 + 현재가) / 5, 3)
            분봉이평10 = round((분봉종가합계9 + 현재가) / 10, 3)
            분봉이평20 = round((분봉종가합계19 + 현재가) / 20, 3)
            분봉이평60 = round((분봉종가합계59 + 현재가) / 60, 3)
            분봉이평120 = round((분봉종가합계119 + 현재가) / 120, 3)
            분봉이평240 = round((분봉종가합계239 + 현재가) / 240, 3)
            if 분봉최고거래대금 != 0:
                분봉최고거래대금대비 = round(분봉거래대금 / 분봉최고거래대금 * 100, 2)
            else:
                분봉최고거래대금대비 = 0.

            """ 보조지표 사용예
            M_BBU, M_BBM, M_BBL = talib.BBANDS(np.r_[self.dict_min_ar[종목코드][:self.mindex, 4], np.array([현재가])], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
            M_BBU, M_BBM, M_BBL = M_BBU[-1], M_BBM[-1], M_BBL[-1]
            M_RSI = talib.RSI(np.r_[self.dict_min_ar[종목코드][:self.mindex, 4], np.array([현재가])], timeperiod=14)[-1]
            M_CCI = talib.CCI(np.r_[self.dict_min_ar[종목코드][:self.mindex, 2], np.array([분봉고가])], np.r_[self.dict_min_ar[종목코드][:self.mindex, 3], np.array([분봉저가])], np.r_[self.dict_min_ar[종목코드][:self.mindex, 4], np.array([현재가])], timeperiod=14)[-1]
            M_MACD, M_MACDS, M_MACDH = talib.MACD(np.r_[self.dict_min_ar[종목코드][:self.mindex, 4], np.array([현재가])], fastperiod=12, slowperiod=26, signalperiod=9)
            M_MACD, M_MACDS, M_MACDH = M_MACD[-1], M_MACDS[-1], M_MACDH[-1]
            M_STOCK, M_STOCD = talib.STOCH(np.r_[self.dict_min_ar[종목코드][:self.mindex, 2], np.array([분봉고가])], np.r_[self.dict_min_ar[종목코드][:self.mindex, 3], np.array([분봉저가])], np.r_[self.dict_min_ar[종목코드][:self.mindex, 4], np.array([현재가])], fastk_period=5, slowk_period=3, slowk_matype=0, slowM_period=3, slowM_matype=0)
            M_STOCK, M_STOCD = M_STOCK[-1], M_STOCD[-1]
            M_ATR = talib.ATR(np.r_[self.dict_min_ar[종목코드][:self.mindex, 2], np.array([분봉고가])], np.r_[self.dict_min_ar[종목코드][:self.mindex, 3], np.array([분봉저가])], np.r_[self.dict_min_ar[종목코드][:self.mindex, 4], np.array([현재가])], timeperiod=14)[-1]
            """

        if self.dict_set['주식일봉데이터']:
            일봉최고종가5, 일봉최고고가5, 일봉최고종가10, 일봉최고고가10, 일봉최고종가20, 일봉최고고가20, 일봉최고종가60, 일봉최고고가60, \
                일봉최고종가120, 일봉최고고가120, 일봉최고종가240, 일봉최고고가240, 일봉최저종가5, 일봉최저저가5, 일봉최저종가10, \
                일봉최저저가10, 일봉최저종가20, 일봉최저저가20, 일봉최저종가60, 일봉최저저가60, 일봉최저종가120, 일봉최저저가120, \
                일봉최저종가240, 일봉최저저가240, 일봉종가합계4, 일봉종가합계9, 일봉종가합계19, 일봉종가합계59, 일봉종가합계119, \
                일봉종가합계239, 일봉최고거래대금 = self.dict_day_ar[종목코드][self.dindex, 12:]
            일봉이평5 = round((일봉종가합계4 + 현재가) / 5, 3)
            일봉이평10 = round((일봉종가합계9 + 현재가) / 10, 3)
            일봉이평20 = round((일봉종가합계19 + 현재가) / 20, 3)
            일봉이평60 = round((일봉종가합계59 + 현재가) / 60, 3)
            일봉이평120 = round((일봉종가합계119 + 현재가) / 120, 3)
            일봉이평240 = round((일봉종가합계239 + 현재가) / 240, 3)
            day_start = strp_time('%Y%m%d%H%M%S', str(self.index)[:8] + '090000')
            hmp_ratio = round((now() - day_start).total_seconds() / 23400, 2)
            if 일봉최고거래대금 != 0 and hmp_ratio != 0.:
                일봉최고거래대금대비 = round(당일거래대금 / (일봉최고거래대금 * hmp_ratio) * 100, 2)
            else:
                일봉최고거래대금대비 = 0.

            """ 보조지표 사용예
            D_BBU, D_BBM, D_BBL = talib.BBANDS(np.r_[self.dict_day_ar[종목코드][:self.dindex, 4], np.array([현재가])], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
            D_BBU, D_BBM, D_BBL = D_BBU[-1], D_BBM[-1], D_BBL[-1]
            D_RSI = talib.RSI(np.r_[self.dict_day_ar[종목코드][:self.dindex, 4], np.array([현재가])], timeperiod=14)[-1]
            D_CCI = talib.CCI(np.r_[self.dict_day_ar[종목코드][:self.dindex, 2], np.array([고가])], np.r_[self.dict_day_ar[종목코드][:self.dindex, 3], np.array([저가])], np.r_[self.dict_day_ar[종목코드][:self.dindex, 4], np.array([현재가])], timeperiod=14)[-1]
            D_MACD, D_MACDS, D_MACDH = talib.MACD(np.r_[self.dict_day_ar[종목코드][:self.dindex, 4], np.array([현재가])], fastperiod=12, slowperiod=26, signalperiod=9)
            D_MACD, D_MACDS, D_MACDH = D_MACD[-1], D_MACDS[-1], D_MACDH[-1]
            D_STOCK, D_STOCD = talib.STOCH(np.r_[self.dict_day_ar[종목코드][:self.dindex, 2], np.array([고가])], np.r_[self.dict_day_ar[종목코드][:self.dindex, 3], np.array([저가])], np.r_[self.dict_day_ar[종목코드][:self.dindex, 4], np.array([현재가])], fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
            D_STOCK, D_STOCD = D_STOCK[-1], D_STOCD[-1]
            D_ATR = talib.ATR(np.r_[self.dict_day_ar[종목코드][:self.dindex, 2], np.array([고가])], np.r_[self.dict_day_ar[종목코드][:self.dindex, 3], np.array([저가])], np.r_[self.dict_day_ar[종목코드][:self.dindex, 4], np.array([현재가])], timeperiod=14)[-1]
            """

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
            self.bhogainfo = {
                1: {매도호가1: 매도잔량1},
                2: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2},
                3: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2, 매도호가3: 매도잔량3},
                4: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2, 매도호가3: 매도잔량3, 매도호가4: 매도잔량4},
                5: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2, 매도호가3: 매도잔량3, 매도호가4: 매도잔량4, 매도호가5: 매도잔량5}
            }
            self.shogainfo = {
                1: {매수호가1: 매수잔량1},
                2: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2},
                3: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3},
                4: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3, 매수호가4: 매수잔량4},
                5: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3, 매수호가4: 매수잔량4, 매수호가5: 매수잔량5}
            }
            self.bhogainfo = self.bhogainfo[self.dict_set['주식매수시장가잔량범위']]
            self.shogainfo = self.shogainfo[self.dict_set['주식매도시장가잔량범위']]

            for j in range(self.vars_count):
                self.vars_key = j
                if self.back_type in ['백테스트', '조건최적화']:
                    if self.tick_count < self.avgtime:
                        return
                else:
                    if self.back_type == 'GA최적화':
                        self.vars = self.vars_lists[j]
                    else:
                        self.vars[self.vars_turn] = self.vars_list[self.vars_turn][j]
                    if self.tick_count < self.vars[0]:
                        return

                수익금, 수익률, 보유수량, 최고수익률, 최저수익률, 매수시간, 보유시간 = 0, 0., 0, 0., 0., strp_time('%Y%m%d', '20000101'), 0
                if self.trade_info[j]['보유중']:
                    _, 매수가, _, _, 보유수량, 최고수익률, 최저수익률, _, 매수시간 = list(self.trade_info[j].values())[:9]
                    매수금액 = 보유수량 * 매수가
                    평가금액 = 보유수량 * 현재가
                    _, 수익금, 수익률 = GetKiwoomPgSgSp(매수금액, 평가금액)
                    if 수익률 > 최고수익률:
                        최고수익률 = 수익률
                        self.trade_info[j]['최고수익률'] = 수익률
                    elif 수익률 < 최저수익률:
                        최저수익률 = 수익률
                        self.trade_info[j]['최저수익률'] = 수익률
                    보유시간 = (now() - 매수시간).total_seconds()

                gubun = None
                if self.dict_set['주식매수주문구분'] == '시장가':
                    if not self.trade_info[j]['보유중']:
                        gubun = '매수'
                    elif self.trade_info[j]['매수분할횟수'] < self.dict_set['주식매수분할횟수']:
                        gubun = '매수'
                    else:
                        gubun = '매도'
                elif self.dict_set['주식매수주문구분'] == '지정가':
                    if not self.trade_info[j]['보유중']:
                        if self.trade_info[j]['매수호가'] == 0:
                            gubun = '매수'
                        else:
                            self.CheckBuy()
                            continue
                    elif self.trade_info[j]['매수분할횟수'] < self.dict_set['주식매수분할횟수']:
                        if self.trade_info[j]['매수호가'] == 0:
                            gubun = '매수'
                        else:
                            self.CheckBuy()
                            continue
                        if self.trade_info[j]['매수호가'] == 0:
                            if self.trade_info[j]['매도호가'] == 0:
                                gubun = '매도'
                            else:
                                self.CheckSell()
                                continue
                    else:
                        if self.trade_info[j]['매도호가'] == 0:
                            gubun = '매도'
                        else:
                            self.CheckSell()
                            continue

                try:
                    if gubun == '매수':
                        try:
                            if self.code not in self.dict_mt[self.index]:
                                return
                        except:
                            return

                        cancel = False
                        if self.dict_set['주식매수금지거래횟수'] and self.dict_set['주식매수금지거래횟수값'] <= self.day_info['거래횟수']:
                            cancel = True
                        elif self.dict_set['주식매수금지손절횟수'] and self.dict_set['주식매수금지손절횟수값'] <= self.day_info['손절횟수']:
                            cancel = True
                        elif self.dict_set['주식매수금지시간'] and self.dict_set['주식매수금지시작시간'] < int(str(self.index)[8:]) < self.dict_set['주식매수금지종료시간']:
                            cancel = True
                        elif self.dict_set['주식매수금지간격'] and now() <= self.day_info['직전거래시간']:
                            cancel = True
                        elif self.dict_set['주식매수금지손절간격'] and now() <= self.day_info['손절매도시간']:
                            cancel = True
                        elif self.dict_set['주식매수금지라운드피겨'] and roundfigure_upper(현재가, self.dict_set['주식매수금지라운드호가'], self.index):
                            cancel = True
                        if cancel: continue

                        if self.dict_set['주식매수분할횟수'] == 1:
                            self.trade_info[j]['주문수량'] = int(self.betting / 현재가)
                        else:
                            oc_ratio = dict_order_ratio[self.dict_set['주식매수분할방법']][self.dict_set['주식매수분할횟수']][
                                self.trade_info[j]['매수분할횟수']]
                            self.trade_info[j]['주문수량'] = int(self.betting / (
                                현재가 if not self.trade_info[j]['보유중'] else self.trade_info[j][
                                    '매수가']) * oc_ratio / 100)

                        if self.dict_set['주식매수주문구분'] == '지정가':
                            기준가격 = 현재가
                            if self.dict_set['주식매수지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                            if self.dict_set['주식매수지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                            self.trade_info[j]['매수호가_'] = 기준가격 + 호가단위 * self.dict_set['주식매수지정가호가번호']

                        if not self.trade_info[j]['보유중']:
                            매수 = True
                            if self.back_type != '조건최적화':
                                exec(self.buystg, None, locals())
                            else:
                                exec(self.dict_buystg[j], None, locals())
                        else:
                            분할매수기준수익률 = round((현재가 / self.buy_info[9] - 1) * 100, 2) if self.dict_set['주식매수분할고정수익률'] else 수익률
                            if self.dict_set['주식매수분할하방'] and 분할매수기준수익률 < -self.dict_set['주식매수분할하방수익률']:
                                self.Buy()
                            elif self.dict_set['주식매수분할상방'] and 분할매수기준수익률 > self.dict_set['주식매수분할상방수익률']:
                                self.Buy()
                            elif self.dict_set['주식매수분할시그널']:
                                매수 = True
                                if self.back_type != '조건최적화':
                                    exec(self.buystg, None, locals())
                                else:
                                    exec(self.dict_buystg[j], None, locals())
                    else:
                        if (self.dict_set['주식매도손절수익률청산'] and 수익률 < -self.dict_set['주식매도손절수익률']) or \
                                (self.dict_set['주식매도손절수익금청산'] and 수익금 < -self.dict_set['주식매도손절수익금'] * 10000):
                            self.Sonjeol()
                            return

                        cancel = False
                        if self.dict_set['주식매도금지시간'] and self.dict_set['주식매도금지시작시간'] < int(str(self.index)[8:]) < self.dict_set['주식매도금지종료시간']:
                            cancel = True
                        elif self.dict_set['주식매도금지간격'] and now() <= self.day_info['직전거래시간']:
                            cancel = True
                        elif self.dict_set['주식매도금지라운드피겨'] and roundfigure_lower(현재가, self.dict_set['주식매도금지라운드호가'], self.index):
                            cancel = True
                        elif self.dict_set['주식매수분할횟수'] > 1 and self.dict_set['주식매도금지매수횟수'] and self.trade_info[j]['매수분할횟수'] <= self.dict_set['주식매도금지매수횟수값']:
                            cancel = True
                        if cancel: continue

                        if self.dict_set['주식매도분할횟수'] == 1:
                            self.trade_info[j]['주문수량'] = self.trade_info[j]['보유수량']
                        else:
                            oc_ratio = dict_order_ratio[self.dict_set['주식매도분할방법']][self.dict_set['주식매도분할횟수']][self.trade_info[j]['매도분할횟수']]
                            self.trade_info[j]['주문수량'] = int(self.betting / self.trade_info[j]['매수가'] * oc_ratio / 100)
                            if self.trade_info[j]['주문수량'] > self.trade_info[j]['보유수량'] or self.trade_info[j]['매도분할횟수'] + 1 == self.dict_set['주식매도분할횟수']:
                                self.trade_info[j]['주문수량'] = self.trade_info[j]['보유수량']

                        if self.dict_set['주식매도주문구분'] == '지정가':
                            기준가격 = 현재가
                            if self.dict_set['주식매도지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                            if self.dict_set['주식매도지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                            self.trade_info[j]['매도호가_'] = 기준가격 + 호가단위 * self.dict_set['주식매도지정가호가번호']

                        if self.dict_set['주식매도분할횟수'] == 1:
                            매도 = False
                            if self.back_type != '조건최적화':
                                exec(self.sellstg, None, locals())
                            else:
                                exec(self.dict_sellstg[j], None, locals())
                        else:
                            if self.dict_set['주식매도분할하방'] and 수익률 < -self.dict_set['주식매도분할하방수익률'] * (self.trade_info[j]['매도분할횟수'] + 1):
                                self.Sell(100)
                            elif self.dict_set['주식매도분할상방'] and 수익률 > self.dict_set['주식매도분할상방수익률'] * (self.trade_info[j]['매도분할횟수'] + 1):
                                self.Sell(100)
                            elif self.dict_set['주식매도분할시그널']:
                                매도 = False
                                if self.back_type != '조건최적화':
                                    exec(self.sellstg, None, locals())
                                else:
                                    exec(self.dict_sellstg[j], None, locals())
                except:
                    if self.gubun == 0: print_exc()
                    self.BackStop()

    def Buy(self):
        if self.dict_set['주식매수주문구분'] == '시장가':
            매수수량 = self.trade_info[self.vars_key]['주문수량']
            if 매수수량 > 0:
                남은수량 = 매수수량
                직전남은수량 = 매수수량
                매수금액 = 0
                for 매도호가, 매도잔량 in self.bhogainfo.items():
                    남은수량 -= 매도잔량
                    if 남은수량 <= 0:
                        매수금액 += 매도호가 * 직전남은수량
                        break
                    else:
                        매수금액 += 매도호가 * 매도잔량
                        직전남은수량 = 남은수량
                if 남은수량 <= 0:
                    if self.trade_info[self.vars_key]['보유수량'] == 0:
                        self.trade_info[self.vars_key]['매수가'] = int(round(매수금액 / 매수수량))
                        self.trade_info[self.vars_key]['보유수량'] = 매수수량
                        self.UpdateBuyInfo(True)
                    else:
                        self.trade_info[self.vars_key]['추가매수가'] = int(round(매수금액 / 매수수량))
                        self.trade_info[self.vars_key]['매수가'] = int(round((self.trade_info[self.vars_key]['매수가'] * self.trade_info[self.vars_key]['보유수량'] + 매수금액) / (self.trade_info[self.vars_key]['보유수량'] + 매수수량)))
                        self.trade_info[self.vars_key]['보유수량'] += 매수수량
                        self.UpdateBuyInfo(False)

        elif self.dict_set['주식매수주문구분'] == '지정가':
            self.trade_info[self.vars_key]['매수호가'] = self.trade_info[self.vars_key]['매수호가_']
            self.trade_info[self.vars_key]['매수호가단위'] = GetHogaunit(self.dict_kd[self.code] if self.code in self.dict_kd.keys() else True, self.array_tick[self.indexn, 1], self.index)
            self.trade_info[self.vars_key]['매수주문시간'] = timedelta_sec(self.dict_set['주식매수취소시간초'], strp_time('%Y%m%d%H%M%S', str(self.index)))

    def CheckBuy(self):
        현재가 = self.array_tick[self.indexn, 1]
        if self.dict_set['주식매수취소관심이탈'] and self.index in self.dict_mt.keys() and self.code not in self.dict_mt[self.index]:
            self.trade_info[self.vars_key]['매수호가'] = 0
        elif self.dict_set['주식매수취소시간'] and strp_time('%Y%m%d%H%M%S', str(self.index)) > self.trade_info[self.vars_key]['매수주문시간']:
            self.trade_info[self.vars_key]['매수호가'] = 0
        elif self.trade_info[self.vars_key]['매수정정횟수'] < self.dict_set['주식매수정정횟수'] and \
                현재가 >= self.trade_info[self.vars_key]['매수호가'] + self.trade_info[self.vars_key]['매수호가단위'] * self.dict_set['주식매수정정호가차이']:
            self.trade_info[self.vars_key]['매수호가'] = 현재가 - self.trade_info[self.vars_key]['매수호가단위'] * self.dict_set['주식매수정정호가']
            self.trade_info[self.vars_key]['매수정정횟수'] += 1
            self.trade_info[self.vars_key]['매수호가단위'] = GetHogaunit(self.dict_kd[self.code] if self.code in self.dict_kd.keys() else True, 현재가, self.index)
        elif 현재가 < self.trade_info[self.vars_key]['매수호가']:
            if self.trade_info[self.vars_key]['보유수량'] == 0:
                self.trade_info[self.vars_key]['매수가'] = self.trade_info[self.vars_key]['매수호가']
                self.trade_info[self.vars_key]['보유수량'] = int(self.betting / self.trade_info[self.vars_key]['매수호가'])
                self.UpdateBuyInfo(True)
            else:
                self.trade_info[self.vars_key]['추가매수가'] = self.trade_info[self.vars_key]['매수호가']
                self.trade_info[self.vars_key]['매수가'] = int(round(self.trade_info[self.vars_key]['매수가'] * self.trade_info[self.vars_key]['보유수량'] + self.trade_info[self.vars_key]['매수호가'] * self.trade_info[self.vars_key]['주문수량'] / (self.trade_info[self.vars_key]['보유수량'] + self.trade_info[self.vars_key]['주문수량'])))
                self.trade_info[self.vars_key]['보유수량'] += self.trade_info[self.vars_key]['주문수량']
                self.UpdateBuyInfo(False)

    def UpdateBuyInfo(self, firstbuy):
        datetimefromindex = strp_time('%Y%m%d%H%M%S', str(self.index))
        self.trade_info[self.vars_key]['보유중'] = 1
        self.trade_info[self.vars_key]['매수호가'] = 0
        self.trade_info[self.vars_key]['매수정정횟수'] = 0
        self.day_info['직전거래시간'] = timedelta_sec(self.dict_set['주식매수금지간격초'], datetimefromindex)
        if firstbuy:
            self.trade_info[self.vars_key]['매수틱번호'] = self.indexn
            self.trade_info[self.vars_key]['매수시간'] = datetimefromindex
            self.trade_info[self.vars_key]['추가매수시간'] = []
            self.trade_info[self.vars_key]['매수분할횟수'] = 1
        else:
            self.trade_info[self.vars_key]['추가매수시간'].append(f"{self.index};{self.trade_info[self.vars_key]['추가매수가']}")
            self.trade_info[self.vars_key]['매수분할횟수'] += 1

    def Sell(self, sell_cond):
        if self.dict_set['주식매도주문구분'] == '시장가':
            남은수량 = self.trade_info[self.vars_key]['주문수량']
            직전남은수량 = 남은수량
            매도금액 = 0
            for 매수호가, 매수잔량 in self.shogainfo.items():
                남은수량 -= 매수잔량
                if 남은수량 <= 0:
                    매도금액 += 매수호가 * 직전남은수량
                    break
                else:
                    매도금액 += 매수호가 * 매수잔량
                    직전남은수량 = 남은수량
            if 남은수량 <= 0:
                self.trade_info[self.vars_key]['매도가'] = int(round(매도금액 / self.trade_info[self.vars_key]['주문수량']))
                self.sell_cond = sell_cond
                self.CalculationEyun()
        elif self.dict_set['주식매도주문구분'] == '지정가':
            현재가 = self.array_tick[self.indexn, 1]
            self.sell_cond = sell_cond
            self.trade_info[self.vars_key]['매도호가'] = self.trade_info[self.vars_key]['매도호가_']
            self.trade_info[self.vars_key]['매도호가단위'] = GetHogaunit(self.dict_kd[self.code] if self.code in self.dict_kd.keys() else True, 현재가, self.index)
            self.trade_info[self.vars_key]['매도주문시간'] = timedelta_sec(self.dict_set['주식매도취소시간초'], strp_time('%Y%m%d%H%M%S', str(self.index)))

    def CheckSell(self):
        현재가 = self.array_tick[self.indexn, 1]
        이전인덱스 = self.array_tick[self.indexn - 1, 0]
        if self.dict_set['주식매도취소관심진입'] and 이전인덱스 in self.dict_mt.keys() and self.index in self.dict_mt.keys() and \
                self.code not in self.dict_mt[이전인덱스] and self.code in self.dict_mt[self.index]:
            self.trade_info[self.vars_key]['매도호가'] = 0
        elif self.dict_set['주식매도취소시간'] and strp_time('%Y%m%d%H%M%S', str(self.index)) > self.trade_info[self.vars_key]['매도주문시간']:
            self.trade_info[self.vars_key]['매도호가'] = 0
        elif self.trade_info[self.vars_key]['매도정정횟수'] < self.dict_set['주식매도정정횟수'] and \
                현재가 <= self.trade_info[self.vars_key]['매도호가'] - self.trade_info[self.vars_key]['매도호가단위'] * self.dict_set['주식매도정정호가차이']:
            self.trade_info[self.vars_key]['매도호가'] = 현재가 + self.trade_info[self.vars_key]['매도호가단위'] * self.dict_set['주식매도정정호가']
            self.trade_info[self.vars_key]['매도정정횟수'] += 1
            self.trade_info[self.vars_key]['매도호가단위'] = GetHogaunit(self.dict_kd[self.code] if self.code in self.dict_kd.keys() else True, 현재가, self.index)
        elif 현재가 > self.trade_info[self.vars_key]['매도호가']:
            self.trade_info[self.vars_key]['매도가'] = self.trade_info[self.vars_key]['매도호가']
            self.CalculationEyun()

    def Sonjeol(self):
        origin_sell_gubun = self.dict_set['주식매도주문구분']
        self.dict_set['주식매도주문구분'] = '시장가'
        self.trade_info[self.vars_key]['주문수량'] = self.trade_info[self.vars_key]['보유수량']
        self.Sell(200)
        self.dict_set['주식매도주문구분'] = origin_sell_gubun

    def LastSell(self):
        매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5 = self.array_tick[self.indexn, 23:43]
        self.shogainfo = {
            1: {매수호가1: 매수잔량1},
            2: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2},
            3: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3},
            4: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3, 매수호가4: 매수잔량4},
            5: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3, 매수호가4: 매수잔량4, 매수호가5: 매수잔량5}
        }
        self.shogainfo = self.shogainfo[self.dict_set['주식매도시장가잔량범위']]

        for k in range(self.vars_count):
            self.vars_key = k
            if self.trade_info[self.vars_key]['보유중']:
                남은수량 = self.trade_info[self.vars_key]['보유수량']
                직전남은수량 = 남은수량
                매도금액 = 0
                for 매수호가, 매수잔량 in self.shogainfo.items():
                    남은수량 -= 매수잔량
                    if 남은수량 <= 0:
                        매도금액 += 매수호가 * 직전남은수량
                        break
                    else:
                        매도금액 += 매수호가 * 매수잔량
                        직전남은수량 = 남은수량

                보유수량 = self.trade_info[self.vars_key]['보유수량']
                if 남은수량 <= 0:
                    self.trade_info[self.vars_key]['매도가'] = int(round(매도금액 / 보유수량))
                elif 매도금액 == 0:
                    self.trade_info[self.vars_key]['매도가'] = self.array_tick[self.indexn, 1]
                else:
                    self.trade_info[self.vars_key]['매도가'] = int(round(매도금액 / (보유수량 - 남은수량)))

                self.trade_info[self.vars_key]['주문수량'] = 보유수량
                self.sell_cond = 0
                self.CalculationEyun()

    def CalculationEyun(self):
        self.total_count += 1
        _, 매수가, 매도가, 주문수량, 보유수량, 최고수익률, 최저수익률, 매수틱번호, _, 추가매수시간 = list(self.trade_info[self.vars_key].values())[:10]
        시가총액 = int(self.array_tick[self.indexn, 12])
        매수시간, 매도시간, 보유시간, 매수금액 = int(self.array_tick[매수틱번호, 0]), self.index, self.indexn - 매수틱번호, 주문수량 * 매수가
        매도금액, 수익금, 수익률 = GetKiwoomPgSgSp(매수금액, 주문수량 * 매도가)
        매도조건 = self.dict_cond[self.sell_cond] if self.back_type != '조건최적화' else self.didict_cond[self.vars_key][self.sell_cond]
        추가매수시간, 잔량없음 = '^'.join(추가매수시간), 보유수량 - 주문수량 == 0
        data = ['백테결과', self.name, 시가총액, 매수시간, 매도시간, 보유시간, 매수가, 매도가, 매수금액, 매도금액, 수익률, 수익금, 매도조건, 추가매수시간, 잔량없음, self.vars_key]
        self.ctq_list[self.vars_key].put(data)
        if 수익률 < 0:
            self.day_info[self.vars_key]['손절횟수'] += 1
            self.day_info[self.vars_key]['손절매도시간'] = timedelta_sec(self.dict_set['주식매수금지손절간격초'], strp_time('%Y%m%d%H%M%S', str(self.index)))
        if self.trade_info[self.vars_key]['보유수량'] - self.trade_info[self.vars_key]['주문수량'] > 0:
            self.trade_info[self.vars_key]['매도호가'] = 0
            self.trade_info[self.vars_key]['보유수량'] -= self.trade_info[self.vars_key]['주문수량']
            self.trade_info[self.vars_key]['매도정정횟수'] = 0
            self.trade_info[self.vars_key]['매도분할횟수'] += 1
        else:
            self.trade_info[self.vars_key]['보유중'] = 0
            self.trade_info[self.vars_key]['매수호가'] = 0
            self.trade_info[self.vars_key]['보유수량'] = 0
