import math
# noinspection PyUnresolvedReferences
import talib
import sqlite3
# noinspection PyUnresolvedReferences
import numpy as np
import pandas as pd
from traceback import print_exc
from backtester.backengine_stock import StockBackEngine
from backtester.back_static import GetBackloadCodeQuery, GetBackloadDayQuery, AddAvgData
from utility.setting import DB_STOCK_BACK, BACK_TEMP, DB_STOCK_DAY, DB_STOCK_MIN, dict_min
# noinspection PyUnresolvedReferences
from utility.static import strp_time, timedelta_sec, pickle_read, pickle_write, strf_time, timedelta_day, GetKiwoomPgSgSp, GetUvilower5, GetHogaunit


class StockBackEngine3(StockBackEngine):
    def __init__(self, gubun, wq, pq, tq, bq, stq_list, profile=False):
        super().__init__(gubun, wq, pq, tq, bq, stq_list, profile)

    def DataLoad(self, data):
        bk = 0
        divid_mode = data[-2]
        con  = sqlite3.connect(DB_STOCK_BACK)
        con2 = sqlite3.connect(DB_STOCK_DAY)
        con3 = sqlite3.connect(DB_STOCK_MIN)

        if divid_mode == '종목코드별 분류':
            gubun, startday, endday, starttime, endtime, code_list, avg_list, code_days, _, _, _ = data
            if gubun == '데이터크기':
                for code in code_list:
                    len_df_tick = 0
                    try:
                        df_tick = pd.read_sql(GetBackloadCodeQuery(code, code_days[code], starttime, endtime), con)
                        len_df_tick = len(df_tick)
                    except:
                        pass
                    self.total_ticks += len_df_tick
                    self.bq.put((code, len_df_tick))
            elif gubun == '데이터로딩':
                for code in code_list:
                    df_tick, len_df_tick, df_min, df_day = None, 0, None, None
                    try:
                        df_tick = pd.read_sql(GetBackloadCodeQuery(code, code_days[code], starttime, endtime), con)
                        len_df_tick = len(df_tick)
                        if self.dict_set['주식분봉데이터']:
                            df_min = []
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 < {startday * 1000000} ORDER BY 체결시간 DESC LIMIT {self.dict_set['주식분봉개수']}"
                            df_ = pd.read_sql(query, con3)
                            df_min.append(df_[::-1])
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 >= {startday * 1000000} and 체결시간 <= {endday * 1000000 + 240000}"
                            df_ = pd.read_sql(query, con3)
                            df_min.append(df_)
                            df_min = pd.concat(df_min)
                        if self.dict_set['주식일봉데이터']:
                            startday_ = int(strf_time('%Y%m%d', timedelta_day(-250, strp_time('%Y%m%d', str(startday)))))
                            query = f"SELECT * FROM '{code}' WHERE 일자 >= {startday_} and 일자 <= {endday}"
                            df_day = pd.read_sql(query, con2)
                    except:
                        pass
                    if len_df_tick > 0:
                        AddAvgData(df_tick, 3, avg_list)
                        arry_tick = np.array(df_tick)
                        arry_min  = np.array(df_min)
                        arry_day  = np.array(df_day)
                        if self.dict_set['주식분봉데이터']:
                            self.dict_mindex[code] = {}
                            for i, index in enumerate(arry_min[:, 0]):
                                self.dict_mindex[code][index] = i
                        if self.dict_set['주식일봉데이터']:
                            self.dict_dindex[code] = {}
                            for i, index in enumerate(arry_day[:, 0]):
                                self.dict_dindex[code][index] = i
                        if self.dict_set['백테일괄로딩']:
                            self.dict_tik_ar[code] = arry_tick
                            if self.dict_set['주식분봉데이터']:
                                self.dict_min_ar[code] = arry_min
                            if self.dict_set['주식일봉데이터']:
                                self.dict_day_ar[code] = arry_day
                        else:
                            pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_tick', arry_tick)
                            pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_min', arry_min)
                            pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_day', arry_day)
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
                    self.bq.put((day, len_df_tick))
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
                    df_tick, len_df_tick, df_min, df_day = None, 0, None, None
                    try:
                        df_tick = pd.read_sql(GetBackloadCodeQuery(code, days, starttime, endtime), con)
                        len_df_tick = len(df_tick)
                        if self.dict_set['주식분봉데이터']:
                            df_min = []
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 < {startday_ * 1000000} ORDER BY 체결시간 DESC LIMIT {self.dict_set['주식분봉개수']}"
                            df_ = pd.read_sql(query, con3)
                            df_min.append(df_[::-1])
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 >= {startday_ * 1000000} and 체결시간 <= {endday_ * 1000000 + 240000}"
                            df_ = pd.read_sql(query, con3)
                            df_min.append(df_)
                            df_min = pd.concat(df_min)
                        if self.dict_set['주식일봉데이터']:
                            startday_ = int(strf_time('%Y%m%d', timedelta_day(-250, strp_time('%Y%m%d', str(startday_)))))
                            query = f"SELECT * FROM '{code}' WHERE 일자 >= {startday_} and 일자 <= {endday_}"
                            df_day = pd.read_sql(query, con2)
                    except:
                        pass
                    if len_df_tick > 0:
                        AddAvgData(df_tick, 3, avg_list)
                        arry_tick = np.array(df_tick)
                        arry_min  = np.array(df_min)
                        arry_day  = np.array(df_day)
                        if self.dict_set['주식분봉데이터']:
                            self.dict_mindex[code] = {}
                            for i, index in enumerate(arry_min[:, 0]):
                                self.dict_mindex[code][index] = i
                        if self.dict_set['주식일봉데이터']:
                            self.dict_dindex[code] = {}
                            for i, index in enumerate(arry_day[:, 0]):
                                self.dict_dindex[code][index] = i
                        if self.dict_set['백테일괄로딩']:
                            self.dict_tik_ar[code] = arry_tick
                            if self.dict_set['주식분봉데이터']:
                                self.dict_min_ar[code] = arry_min
                            if self.dict_set['주식일봉데이터']:
                                self.dict_day_ar[code] = arry_day
                        else:
                            pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_tick', arry_tick)
                            pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_min', arry_min)
                            pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_day', arry_day)
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
                    self.bq.put((day, len_df_tick))
            elif gubun == '데이터로딩':
                startday_ = day_list[0]
                endday_   = day_list[-1]
                df_tick, len_df_tick, df_min, df_day = None, 0, None, None
                try:
                    df_tick = pd.read_sql(GetBackloadCodeQuery(code, day_list, starttime, endtime), con)
                    len_df_tick = len(df_tick)
                    if self.dict_set['주식분봉데이터']:
                        df_min = []
                        query = f"SELECT * FROM '{code}' WHERE 체결시간 < {startday_ * 1000000} ORDER BY 체결시간 DESC LIMIT {self.dict_set['주식분봉개수']}"
                        df_ = pd.read_sql(query, con3)
                        df_min.append(df_[::-1])
                        query = f"SELECT * FROM '{code}' WHERE 체결시간 >= {startday_ * 1000000} and 체결시간 <= {endday_ * 1000000 + 240000}"
                        df_ = pd.read_sql(query, con3)
                        df_min.append(df_)
                        df_min = pd.concat(df_min)
                    if self.dict_set['주식일봉데이터']:
                        startday_ = int(strf_time('%Y%m%d', timedelta_day(-250, strp_time('%Y%m%d', str(startday_)))))
                        query = f"SELECT * FROM '{code}' WHERE 일자 >= {startday_} and 일자 <= {endday_}"
                        df_day = pd.read_sql(query, con2)
                except:
                    pass
                if len_df_tick > 0:
                    AddAvgData(df_tick, 3, avg_list)
                    arry_tick = np.array(df_tick)
                    arry_min  = np.array(df_min)
                    arry_day  = np.array(df_day)
                    if self.dict_set['주식분봉데이터']:
                        self.dict_mindex[code] = {}
                        for i, index in enumerate(arry_min[:, 0]):
                            self.dict_mindex[code][index] = i
                    if self.dict_set['주식일봉데이터']:
                        self.dict_dindex[code] = {}
                        for i, index in enumerate(arry_day[:, 0]):
                            self.dict_dindex[code][index] = i
                    if self.dict_set['백테일괄로딩']:
                        self.dict_tik_ar[code] = arry_tick
                        if self.dict_set['주식분봉데이터']:
                            self.dict_min_ar[code] = arry_min
                        if self.dict_set['주식일봉데이터']:
                            self.dict_day_ar[code] = arry_day
                    else:
                        pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_tick', arry_tick)
                        pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_min', arry_min)
                        pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_day', arry_day)
                    self.code_list.append(code)
                    bk += 1

        con3.close()
        con2.close()
        con.close()
        if gubun == '데이터로딩':
            self.bq.put(bk)
            self.avg_list = avg_list
            self.startday_, self.endday_, self.starttime_, self.endtime_ = startday, endday, starttime, endtime

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

            if not self.dict_set['백테일괄로딩']:
                self.dict_tik_ar = {code: pickle_read(f'{self.gubun}_{BACK_TEMP}/{code}_tick')}
                self.dict_min_ar = {code: pickle_read(f'{self.gubun}_{BACK_TEMP}/{code}_min')}
                self.dict_day_ar = {code: pickle_read(f'{self.gubun}_{BACK_TEMP}/{code}_day')}

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
                    if self.back_type is None: break
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
                        self.InitTradeInfo()

            self.tq.put(('백테완료', 1 if self.total_count > 0 else 0))

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

        def Parameter_Previous(vindex, pre):
            if pre != -1:
                return self.array_tick[self.indexn - pre, vindex]
            else:
                return self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], vindex]

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
                return Parameter_Previous(44, pre)
            elif tick == 300:
                return Parameter_Previous(45, pre)
            elif tick == 600:
                return Parameter_Previous(46, pre)
            elif tick == 1200:
                return Parameter_Previous(47, pre)
            else:
                if pre != -1:
                    return round(self.array_tick[self.indexn + 1 - tick - pre:self.indexn + 1 - pre, 1].mean(), 3)
                else:
                    bindex = self.trade_info[self.vars_key]['매수틱번호']
                    return round(self.array_tick[bindex + 1 - tick:bindex + 1, 1].mean(), 3)

        def GetArrayIndex(bc):
            return bc + 13 * self.avg_list.index(self.avgtime if self.back_type in ('백테스트', '조건최적화', '백파인더') else self.vars[0])

        def Parameter_Area(aindex, vindex, tick, pre, gubun_):
            if tick in self.avg_list:
                return Parameter_Previous(GetArrayIndex(aindex), pre)
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

        def Parameter_Dgree(aindex, vindex, tick, pre, cf):
            if tick in self.avg_list:
                return Parameter_Previous(GetArrayIndex(aindex), pre)
            else:
                if pre != -1:
                    dmp_gap = self.array_tick[self.indexn - pre, vindex] - self.array_tick[self.indexn + 1 - tick - pre, vindex]
                else:
                    dmp_gap = self.array_tick[self.trade_info[self.vars_key]['매수틱번호'], vindex] - self.array_tick[self.trade_info[self.vars_key]['매수틱번호'] + 1 - tick, vindex]
                return round(math.atan2(dmp_gap * cf, tick) / (2 * math.pi) * 360, 2)

        def 등락율각도(tick, pre=0):
            return Parameter_Dgree(58, 5, tick, pre, 5)

        def 당일거래대금각도(tick, pre=0):
            return Parameter_Dgree(59, 6, tick, pre, 0.01)

        def 전일비각도(tick, pre=0):
            return Parameter_Dgree(60, 9, tick, pre, 1)

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
            bhogainfo = ((매도호가1, 매도잔량1), (매도호가2, 매도잔량2), (매도호가3, 매도잔량3), (매도호가4, 매도잔량4), (매도호가5, 매도잔량5))
            shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
            self.bhogainfo = bhogainfo[:self.dict_set['주식매수시장가잔량범위']]
            self.shogainfo = shogainfo[:self.dict_set['주식매도시장가잔량범위']]

            for j in range(self.vars_count):
                self.vars_key = j
                if self.back_type in ('백테스트', '조건최적화'):
                    if self.tick_count < self.avgtime:
                        break
                elif self.back_type == 'GA최적화':
                    self.vars = self.vars_lists[j]
                    if self.tick_count < self.vars[0]:
                        continue
                elif self.vars_turn >= 0:
                    self.vars[self.vars_turn] = self.vars_list[self.vars_turn][j]
                    if self.tick_count < self.vars[0]:
                        if self.vars_turn != 0:
                            break
                        else:
                            continue
                elif self.tick_count < self.vars[0]:
                    break

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
                        _, 수익금, 수익률 = GetKiwoomPgSgSp(매수금액, 평가금액)
                        if 수익률 > 최고수익률:
                            self.trade_info[j]['최고수익률'] = 최고수익률 = 수익률
                        elif 수익률 < 최저수익률:
                            self.trade_info[j]['최저수익률'] = 최저수익률 = 수익률
                        보유시간 = (now() - 매수시간).total_seconds()

                        self.trade_info[j]['주문수량'] = 보유수량
                        매도 = False
                        if self.back_type != '조건최적화':
                            exec(self.sellstg, None, locals())
                        else:
                            exec(self.dict_sellstg[j], None, locals())
                except:
                    if self.gubun == 0: print_exc()
                    self.BackStop()
                    break
