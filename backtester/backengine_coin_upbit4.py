import math
# noinspection PyUnresolvedReferences
import talib
import sqlite3
# noinspection PyUnresolvedReferences
import numpy as np
import pandas as pd
from traceback import print_exc
from backtester.backengine_coin_upbit2 import CoinUpbitBackEngine2
from backtester.back_static import GetBackloadCodeQuery, GetBackloadDayQuery, AddAvgData
from utility.setting import DB_COIN_BACK, BACK_TEMP, DB_COIN_DAY, DB_COIN_MIN, dict_min, dict_order_ratio
# noinspection PyUnresolvedReferences
from utility.static import strp_time, timedelta_sec, strf_time, timedelta_day, GetUpbitHogaunit, pickle_read, pickle_write, GetUpbitPgSgSp


class CoinUpbitBackEngine4(CoinUpbitBackEngine2):
    def __init__(self, gubun, wq, pq, tq, bq, stq_list, profile=False):
        super().__init__(gubun, wq, pq, tq, bq, stq_list, profile)

    def DataLoad(self, data):
        bk = 0
        divid_mode = data[-2]
        con = sqlite3.connect(DB_COIN_BACK)
        con2 = sqlite3.connect(DB_COIN_DAY)
        con3 = sqlite3.connect(DB_COIN_MIN)

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
                        if self.dict_set['코인분봉데이터']:
                            df_min = []
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 < {startday * 1000000} ORDER BY 체결시간 DESC LIMIT {self.dict_set['코인분봉개수']}"
                            df_ = pd.read_sql(query, con3)
                            df_min.append(df_[::-1])
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 >= {startday * 1000000} and 체결시간 <= {endday * 1000000 + 240000}"
                            df_ = pd.read_sql(query, con3)
                            df_min.append(df_)
                            df_min = pd.concat(df_min)
                        if self.dict_set['코인일봉데이터']:
                            startday_ = int(strf_time('%Y%m%d', timedelta_day(-250, strp_time('%Y%m%d', str(startday)))))
                            query = f"SELECT * FROM '{code}' WHERE 일자 >= {startday_} and 일자 <= {endday}"
                            df_day = pd.read_sql(query, con2)
                    except:
                        pass
                    if len_df_tick > 0:
                        df_tick = AddAvgData(df_tick, 8, avg_list)
                        arry_tick = np.array(df_tick)
                        arry_min  = np.array(df_min)
                        arry_day  = np.array(df_day)
                        if self.dict_set['코인분봉데이터']:
                            self.dict_mindex[code] = {}
                            for i, index in enumerate(arry_min[:, 0]):
                                self.dict_mindex[code][index] = i
                        if self.dict_set['코인일봉데이터']:
                            self.dict_dindex[code] = {}
                            for i, index in enumerate(arry_day[:, 0]):
                                self.dict_dindex[code][index] = i
                        if self.dict_set['백테일괄로딩']:
                            self.dict_tik_ar[code] = arry_tick
                            if self.dict_set['코인분봉데이터']:
                                self.dict_min_ar[code] = arry_min
                            if self.dict_set['코인일봉데이터']:
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
                        if self.dict_set['코인분봉데이터']:
                            df_min = []
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 < {startday_ * 1000000} ORDER BY 체결시간 DESC LIMIT {self.dict_set['코인분봉개수']}"
                            df_ = pd.read_sql(query, con3)
                            df_min.append(df_[::-1])
                            query = f"SELECT * FROM '{code}' WHERE 체결시간 >= {startday_ * 1000000} and 체결시간 <= {endday_ * 1000000 + 240000}"
                            df_ = pd.read_sql(query, con3)
                            df_min.append(df_)
                            df_min = pd.concat(df_min)
                        if self.dict_set['코인일봉데이터']:
                            startday_ = int(strf_time('%Y%m%d', timedelta_day(-250, strp_time('%Y%m%d', str(startday_)))))
                            query = f"SELECT * FROM '{code}' WHERE 일자 >= {startday_} and 일자 <= {endday_}"
                            df_day = pd.read_sql(query, con2)
                    except:
                        pass
                    if len_df_tick > 0:
                        df_tick = AddAvgData(df_tick, 8, avg_list)
                        arry_tick = np.array(df_tick)
                        arry_min  = np.array(df_min)
                        arry_day  = np.array(df_day)
                        if self.dict_set['코인분봉데이터']:
                            self.dict_mindex[code] = {}
                            for i, index in enumerate(arry_min[:, 0]):
                                self.dict_mindex[code][index] = i
                        if self.dict_set['코인일봉데이터']:
                            self.dict_dindex[code] = {}
                            for i, index in enumerate(arry_day[:, 0]):
                                self.dict_dindex[code][index] = i
                        if self.dict_set['백테일괄로딩']:
                            self.dict_tik_ar[code] = arry_tick
                            if self.dict_set['코인분봉데이터']:
                                self.dict_min_ar[code] = arry_min
                            if self.dict_set['코인일봉데이터']:
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
                    if self.dict_set['코인분봉데이터']:
                        df_min = []
                        query = f"SELECT * FROM '{code}' WHERE 체결시간 < {startday_ * 1000000} ORDER BY 체결시간 DESC LIMIT {self.dict_set['코인분봉개수']}"
                        df_ = pd.read_sql(query, con3)
                        df_min.append(df_[::-1])
                        query = f"SELECT * FROM '{code}' WHERE 체결시간 >= {startday_ * 1000000} and 체결시간 <= {endday_ * 1000000 + 240000}"
                        df_ = pd.read_sql(query, con3)
                        df_min.append(df_)
                        df_min = pd.concat(df_min)
                    if self.dict_set['코인일봉데이터']:
                        startday_ = int(strf_time('%Y%m%d', timedelta_day(-250, strp_time('%Y%m%d', str(startday_)))))
                        query = f"SELECT * FROM '{code}' WHERE 일자 >= {startday_} and 일자 <= {endday_}"
                        df_day = pd.read_sql(query, con2)
                except:
                    pass
                if len_df_tick > 0:
                    df_tick = AddAvgData(df_tick, 8, avg_list)
                    arry_tick = np.array(df_tick)
                    arry_min  = np.array(df_min)
                    arry_day  = np.array(df_day)
                    if self.dict_set['코인분봉데이터']:
                        self.dict_mindex[code] = {}
                        for i, index in enumerate(arry_min[:, 0]):
                            self.dict_mindex[code][index] = i
                    if self.dict_set['코인일봉데이터']:
                        self.dict_dindex[code] = {}
                        for i, index in enumerate(arry_day[:, 0]):
                            self.dict_dindex[code][index] = i
                    if self.dict_set['백테일괄로딩']:
                        self.dict_tik_ar[code] = arry_tick
                        if self.dict_set['코인분봉데이터']:
                            self.dict_min_ar[code] = arry_min
                        if self.dict_set['코인일봉데이터']:
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
            self.code = self.name = code
            self.total_count = 0

            if self.dict_set['백테주문관리적용'] and self.dict_set['코인매수금지블랙리스트'] and self.code in self.dict_set['코인블랙리스트'] and self.back_type != '백파인더':
                self.tq.put(('백테완료', 0))
                continue

            if not self.dict_set['백테일괄로딩']:
                self.dict_tik_ar = {code: pickle_read(f'{self.gubun}_{BACK_TEMP}/{code}_tick')}
                self.dict_min_ar = {code: pickle_read(f'{self.gubun}_{BACK_TEMP}/{code}_min')}
                self.dict_day_ar = {code: pickle_read(f'{self.gubun}_{BACK_TEMP}/{code}_day')}

            if same_days and same_time:
                self.array_tick = self.dict_tik_ar[code]
            elif same_time:
                self.array_tick = self.dict_tik_ar[code][(self.dict_tik_ar[code][:, 0] >= self.startday * 1000000) &
                                                         (self.dict_tik_ar[code][:,
                                                          0] <= self.endday * 1000000 + 240000)]
            elif same_days:
                self.array_tick = self.dict_tik_ar[code][(self.dict_tik_ar[code][:, 0] % 1000000 >= self.starttime) &
                                                         (self.dict_tik_ar[code][:, 0] % 1000000 <= self.endtime)]
            else:
                self.array_tick = self.dict_tik_ar[code][(self.dict_tik_ar[code][:, 0] >= self.startday * 1000000) &
                                                         (self.dict_tik_ar[code][:,
                                                          0] <= self.endday * 1000000 + 240000) &
                                                         (self.dict_tik_ar[code][:, 0] % 1000000 >= self.starttime) &
                                                         (self.dict_tik_ar[code][:, 0] % 1000000 <= self.endtime)]

            if len(self.array_tick) > 0:
                last = len(self.array_tick) - 1
                for i, index in enumerate(self.array_tick[:, 0]):
                    if self.back_type is None: break
                    next_day_change = i != last and str(index)[:8] != str(self.array_tick[i + 1, 0])[:8]
                    self.tick_count += 1
                    self.index = int(index)
                    self.indexn = i

                    try:
                        if self.dict_set['코인분봉데이터']:
                            self.mindex = self.dict_mindex[code][
                                int(str(self.index)[:10] + dict_min[self.dict_set['코인분봉기간']][
                                    str(self.index)[10:12]] + '00')]
                            self.UpdateCurrentMin(i)
                        if self.dict_set['코인일봉데이터']:
                            self.dindex = self.dict_dindex[code][int(str(self.index)[:8])]
                    except:
                        continue

                    if i != last and not next_day_change:
                        self.Strategy()
                    else:
                        self.LastSell()
                        self.InitTradeInfo()

            self.tq.put(('백테완료', 1 if self.total_count > 0 else 0))

        if self.pattern:
            self.tq.put(('학습결과', self.pattern_buy, self.pattern_sell))

        if self.profile:
            self.pr.print_stats(sort='cumulative')

        while not self.pq.empty():
            self.pq.get()

    def UpdateCurrentMin(self, i):
        현재가 = self.array_tick[i, 1]
        초당거래대금 = self.array_tick[i, 10]
        if self.current_min is None or self.mindex != self.current_min[0]:
            self.current_min = [self.mindex, 현재가, 현재가, 현재가, 초당거래대금]
        else:
            분봉고가, 분봉저가, 분봉거래대금 = self.current_min[2:]
            분봉고가 = 현재가 if 현재가 > 분봉고가 else 분봉고가
            분봉저가 = 현재가 if 현재가 < 분봉저가 else 분봉저가
            분봉거래대금 += 초당거래대금
            self.current_min[2:] = 분봉고가, 분봉저가, 분봉거래대금

    def Strategy(self):
        def now_utc():
            return strp_time('%Y%m%d%H%M%S', str(self.index))

        def Parameter_Previous(aindex, pre):
            pindex = (self.indexn - pre) if pre != -1 else 매수틱번호
            return self.array_tick[pindex, aindex]

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

        def 관심종목N(pre):
            return Parameter_Previous(35, pre)

        def 이동평균(tick, pre=0):
            if tick == 60:
                return Parameter_Previous(36, pre)
            elif tick == 300:
                return Parameter_Previous(37, pre)
            elif tick == 600:
                return Parameter_Previous(38, pre)
            elif tick == 1200:
                return Parameter_Previous(39, pre)
            else:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else 매수틱번호 + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else 매수틱번호 + 1
                return round(self.array_tick[sindex:eindex, 1].mean(), 8)

        def GetArrayIndex(aindex):
            return aindex + 12 * self.avg_list.index(self.avgtime if self.back_type in ('백테스트', '조건최적화', '백파인더') else self.vars[0])

        def Parameter_Area(aindex, vindex, tick, pre, gubun_):
            if tick in self.avg_list:
                return Parameter_Previous(GetArrayIndex(aindex), pre)
            else:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else 매수틱번호 + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else 매수틱번호 + 1
                if gubun_ == 'max':
                    return self.array_tick[sindex:eindex, vindex].max()
                elif gubun_ == 'min':
                    return self.array_tick[sindex:eindex, vindex].min()
                elif gubun_ == 'sum':
                    return self.array_tick[sindex:eindex, vindex].sum()
                else:
                    return self.array_tick[sindex:eindex, vindex].mean()

        def 최고현재가(tick, pre=0):
            return Parameter_Area(40, 1, tick, pre, 'max')

        def 최저현재가(tick, pre=0):
            return Parameter_Area(41, 1, tick, pre, 'min')

        def 체결강도평균(tick, pre=0):
            return Parameter_Area(42, 7, tick, pre, 'mean')

        def 최고체결강도(tick, pre=0):
            return Parameter_Area(43, 7, tick, pre, 'max')

        def 최저체결강도(tick, pre=0):
            return Parameter_Area(44, 7, tick, pre, 'min')

        def 최고초당매수수량(tick, pre=0):
            return Parameter_Area(45, 14, tick, pre, 'max')

        def 누적초당매수수량(tick, pre=0):
            return Parameter_Area(46, 14, tick, pre, 'sum')

        def 최고초당매도수량(tick, pre=0):
            return Parameter_Area(47, 15, tick, pre, 'max')

        def 누적초당매도수량(tick, pre=0):
            return Parameter_Area(48, 15, tick, pre, 'sum')

        def 초당거래대금평균(tick, pre=0):
            return Parameter_Area(49, 19, tick, pre, 'mean')

        def Parameter_Dgree(aindex, vindex, tick, pre, cf):
            if tick in self.avg_list:
                return Parameter_Previous(GetArrayIndex(aindex), pre)
            else:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else 매수틱번호 + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else 매수틱번호 + 1
                dmp_gap = self.array_tick[eindex, vindex] - self.array_tick[sindex, vindex]
                return round(math.atan2(dmp_gap * cf, tick) / (2 * math.pi) * 360, 2)

        def 등락율각도(tick, pre=0):
            return Parameter_Dgree(50, 5, tick, pre, 10)

        def 당일거래대금각도(tick, pre=0):
            return Parameter_Dgree(51, 6, tick, pre, 0.00000001)

        if self.dict_set['코인분봉데이터']:
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

        if self.dict_set['코인일봉데이터']:
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

        현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 초당매수수량, 초당매도수량, 초당거래대금, 고저평균대비등락율, 매도총잔량, \
            매수총잔량, 매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합, \
            관심종목 = self.array_tick[self.indexn, 1:36]
        종목코드, 데이터길이, 시분초, 호가단위 = self.code, self.tick_count, int(str(self.index)[8:]), GetUpbitHogaunit(현재가)

        if self.dict_set['코인분봉데이터']:
            분봉시가, 분봉고가, 분봉저가, 분봉거래대금 = self.current_min[1:]
            분봉최고종가5, 분봉최고고가5, 분봉최고종가10, 분봉최고고가10, 분봉최고종가20, 분봉최고고가20, 분봉최고종가60, 분봉최고고가60, \
                분봉최고종가120, 분봉최고고가120, 분봉최고종가240, 분봉최고고가240, 분봉최저종가5, 분봉최저저가5, 분봉최저종가10, \
                분봉최저저가10, 분봉최저종가20, 분봉최저저가20, 분봉최저종가60, 분봉최저저가60, 분봉최저종가120, 분봉최저저가120, \
                분봉최저종가240, 분봉최저저가240, 분봉종가합계4, 분봉종가합계9, 분봉종가합계19, 분봉종가합계59, 분봉종가합계119, \
                분봉종가합계239, 분봉최고거래대금 = self.dict_min_ar[종목코드][self.mindex, 12:]
            분봉이평5 = round((분봉종가합계4 + 현재가) / 5, 8)
            분봉이평10 = round((분봉종가합계9 + 현재가) / 10, 8)
            분봉이평20 = round((분봉종가합계19 + 현재가) / 20, 8)
            분봉이평60 = round((분봉종가합계59 + 현재가) / 60, 8)
            분봉이평120 = round((분봉종가합계119 + 현재가) / 120, 8)
            분봉이평240 = round((분봉종가합계239 + 현재가) / 240, 8)
            if 분봉최고거래대금 != 0:
                분봉최고거래대금대비 = round(분봉거래대금 / 분봉최고거래대금 * 100, 2)
            else:
                분봉최고거래대금대비 = 0.

        if self.dict_set['코인일봉데이터']:
            일봉최고종가5, 일봉최고고가5, 일봉최고종가10, 일봉최고고가10, 일봉최고종가20, 일봉최고고가20, 일봉최고종가60, 일봉최고고가60, \
                일봉최고종가120, 일봉최고고가120, 일봉최고종가240, 일봉최고고가240, 일봉최저종가5, 일봉최저저가5, 일봉최저종가10, \
                일봉최저저가10, 일봉최저종가20, 일봉최저저가20, 일봉최저종가60, 일봉최저저가60, 일봉최저종가120, 일봉최저저가120, \
                일봉최저종가240, 일봉최저저가240, 일봉종가합계4, 일봉종가합계9, 일봉종가합계19, 일봉종가합계59, 일봉종가합계119, \
                일봉종가합계239, 일봉최고거래대금 = self.dict_day_ar[종목코드][self.dindex, 12:]
            일봉이평5 = round((일봉종가합계4 + 현재가) / 5, 8)
            일봉이평10 = round((일봉종가합계9 + 현재가) / 10, 8)
            일봉이평20 = round((일봉종가합계19 + 현재가) / 20, 8)
            일봉이평60 = round((일봉종가합계59 + 현재가) / 60, 8)
            일봉이평120 = round((일봉종가합계119 + 현재가) / 120, 8)
            일봉이평240 = round((일봉종가합계239 + 현재가) / 240, 8)
            if 일봉최고거래대금 != 0:
                일봉최고거래대금대비 = round(당일거래대금 / 일봉최고거래대금 * 100, 2)
            else:
                일봉최고거래대금대비 = 0.

        if self.back_type == '백파인더':
            if self.tick_count < self.avgtime:
                return

            매수 = True
            try:
                exec(self.buystg, None, locals())
            except:
                print_exc()
                self.BackStop(1)
        else:
            bhogainfo = ((매도호가1, 매도잔량1), (매도호가2, 매도잔량2), (매도호가3, 매도잔량3), (매도호가4, 매도잔량4), (매도호가5, 매도잔량5))
            shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
            self.bhogainfo = bhogainfo[:self.dict_set['코인매수시장가잔량범위']]
            self.shogainfo = shogainfo[:self.dict_set['코인매도시장가잔량범위']]

            for j in range(self.vars_count):
                self.vars_key = j
                if self.back_type in ('백테스트', '조건최적화'):
                    if self.tick_count < self.avgtime:
                        break
                    if self.pattern_test and self.tick_count < self.dict_pattern['인식구간']:
                        break
                elif self.back_type == 'GA최적화':
                    self.vars = self.vars_lists[j]
                    if self.tick_count < self.vars[0]:
                        continue
                elif self.vars_turn >= 0:
                    curr_var = self.vars_list[self.vars_turn][0][j]
                    if curr_var == self.vars_list[self.vars_turn][1]:
                        continue
                    self.vars[self.vars_turn] = curr_var
                    if self.tick_count < self.vars[0]:
                        continue
                elif self.tick_count < self.vars[0]:
                    break

                수익금, 수익률, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간, 보유시간 = 0, 0., 0, 0., 0., 0, strp_time('%Y%m%d', '20000101'), 0
                if self.trade_info[j]['보유중']:
                    _, 매수가, _, _, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간, _, _, _, _, _, _, _, _, _, _, _, _, _, _ = self.trade_info[j].values()
                    매수금액 = 보유수량 * 매수가
                    평가금액 = 보유수량 * 현재가
                    _, 수익금, 수익률 = GetUpbitPgSgSp(매수금액, 평가금액)
                    if 수익률 > 최고수익률:
                        최고수익률 = 수익률
                        self.trade_info[j]['최고수익률'] = 수익률
                    elif 수익률 < 최저수익률:
                        최저수익률 = 수익률
                        self.trade_info[j]['최저수익률'] = 수익률
                    보유시간 = (now_utc() - 매수시간).total_seconds()

                gubun = None
                if self.dict_set['코인매수주문구분'] == '시장가':
                    if not self.trade_info[j]['보유중']:
                        gubun = '매수'
                    elif self.trade_info[j]['매수분할횟수'] < self.dict_set['코인매수분할횟수']:
                        gubun = '매수'
                    else:
                        gubun = '매도'
                elif self.dict_set['코인매수주문구분'] == '지정가':
                    if not self.trade_info[j]['보유중']:
                        if self.trade_info[j]['매수호가'] == 0:
                            gubun = '매수'
                        else:
                            관심이탈 = not 관심종목 and 관심종목N(1)
                            self.CheckBuy(현재가, 관심이탈)
                            continue
                    elif self.trade_info[j]['매수분할횟수'] < self.dict_set['코인매수분할횟수']:
                        if self.trade_info[j]['매수호가'] == 0:
                            gubun = '매수'
                        else:
                            관심이탈 = not 관심종목 and 관심종목N(1)
                            self.CheckBuy(현재가, 관심이탈)
                            continue
                        if self.trade_info[j]['매수호가'] == 0:
                            if self.trade_info[j]['매도호가'] == 0:
                                gubun = '매도'
                            else:
                                관심진입 = 관심종목 and not 관심종목N(1)
                                self.CheckSell(현재가, 관심진입)
                                continue
                    else:
                        if self.trade_info[j]['매도호가'] == 0:
                            gubun = '매도'
                        else:
                            관심진입 = 관심종목 and not 관심종목N(1)
                            self.CheckSell(현재가, 관심진입)
                            continue

                try:
                    if gubun == '매수':
                        if not 관심종목: continue
                        cancel = False
                        if self.dict_set['코인매수금지거래횟수'] and self.dict_set['코인매수금지거래횟수값'] <= self.trade_info[j]['거래횟수']:
                            cancel = True
                        if self.dict_set['코인매수금지손절횟수'] and self.dict_set['코인매수금지손절횟수값'] <= self.trade_info[j]['손절횟수']:
                            cancel = True
                        if self.dict_set['코인매수금지시간'] and self.dict_set['코인매수금지시작시간'] < int(str(self.index)[8:]) < \
                                self.dict_set['코인매수금지종료시간']:
                            cancel = True
                        if self.dict_set['코인매수금지간격'] and now_utc() <= self.day_info[j]['직전거래시간']:
                            cancel = True
                        if self.dict_set['코인매수금지손절간격'] and now_utc() <= self.day_info[j]['손절매도시간']:
                            cancel = True
                        if self.dict_set['코인매수금지200원이하'] and 현재가 <= 200:
                            cancel = True
                        if cancel: continue

                        if self.dict_set['코인매수분할횟수'] == 1:
                            self.trade_info[j]['주문수량'] = round(self.betting / 현재가, 8)
                        else:
                            oc_ratio = dict_order_ratio[self.dict_set['코인매수분할방법']][self.dict_set['코인매수분할횟수']][self.trade_info[j]['매수분할횟수']]
                            self.trade_info[j]['주문수량'] = round(self.betting / (현재가 if not self.trade_info[j]['보유중'] else self.trade_info[j]['매수가']) * oc_ratio / 100, 8)

                        if self.dict_set['코인매수주문구분'] == '지정가':
                            기준가격 = 현재가
                            if self.dict_set['코인매수지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                            if self.dict_set['코인매수지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                            self.trade_info[j]['매수호가_'] = 기준가격 + 호가단위 * self.dict_set['코인매수지정가호가번호']

                        if not self.trade_info[j]['보유중']:
                            매수 = True
                            if self.back_type != '조건최적화':
                                exec(self.buystg, None, locals())
                            else:
                                exec(self.dict_buystg[j], None, locals())
                        else:
                            분할매수기준수익률 = round((현재가 / self.buy_info[9] - 1) * 100, 2) if self.dict_set['코인매수분할고정수익률'] else 수익률
                            if self.dict_set['코인매수분할하방'] and 분할매수기준수익률 < -self.dict_set['코인매수분할하방수익률']:
                                self.Buy()
                            elif self.dict_set['코인매수분할상방'] and 분할매수기준수익률 > self.dict_set['코인매수분할상방수익률']:
                                self.Buy()
                            elif self.dict_set['코인매수분할시그널']:
                                매수 = True
                                if self.back_type != '조건최적화':
                                    exec(self.buystg, None, locals())
                                else:
                                    exec(self.dict_buystg[j], None, locals())
                    else:
                        if (self.dict_set['코인매도손절수익률청산'] and 수익률 < -self.dict_set['코인매도손절수익률']) or \
                                (self.dict_set['코인매도손절수익금청산'] and 수익금 < -self.dict_set['코인매도손절수익금'] * 10000):
                            self.Sonjeol()
                            continue

                        cancel = False
                        if self.dict_set['코인매도금지시간'] and self.dict_set['코인매도금지시작시간'] < int(str(self.index)[8:]) < self.dict_set['코인매도금지종료시간']:
                            cancel = True
                        elif self.dict_set['코인매도금지간격'] and now_utc() <= self.day_info[j]['직전거래시간']:
                            cancel = True
                        elif self.dict_set['코인매수분할횟수'] > 1 and self.dict_set['코인매도금지매수횟수'] and self.trade_info[j]['매수분할횟수'] <= self.dict_set['코인매도금지매수횟수값']:
                            cancel = True
                        if cancel: continue

                        if self.dict_set['코인매도분할횟수'] == 1:
                            self.trade_info[j]['주문수량'] = self.trade_info[j]['보유수량']
                        else:
                            oc_ratio = dict_order_ratio[self.dict_set['코인매도분할방법']][self.dict_set['코인매도분할횟수']][self.trade_info[j]['매도분할횟수']]
                            self.trade_info[j]['주문수량'] = round(self.betting / self.trade_info[j]['매수가'] * oc_ratio / 100, 8)
                            if self.trade_info[j]['주문수량'] > self.trade_info[j]['보유수량'] or self.trade_info[j]['매도분할횟수'] + 1 == self.dict_set['코인매도분할횟수']:
                                self.trade_info[j]['주문수량'] = self.trade_info[j]['보유수량']

                        if self.dict_set['코인매도주문구분'] == '지정가':
                            기준가격 = 현재가
                            if self.dict_set['코인매도지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                            if self.dict_set['코인매도지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                            self.trade_info[j]['매도호가_'] = 기준가격 + 호가단위 * self.dict_set['코인매도지정가호가번호']

                        if self.dict_set['코인매도분할횟수'] == 1:
                            매도 = False
                            if self.back_type != '조건최적화':
                                exec(self.sellstg, None, locals())
                            else:
                                exec(self.dict_sellstg[j], None, locals())
                        else:
                            if self.dict_set['코인매도분할하방'] and 수익률 < -self.dict_set['코인매도분할하방수익률'] * (self.trade_info[j]['매도분할횟수'] + 1):
                                self.Sell(100)
                            elif self.dict_set['코인매도분할상방'] and 수익률 > self.dict_set['코인매도분할상방수익률'] * (self.trade_info[j]['매도분할횟수'] + 1):
                                self.Sell(100)
                            elif self.dict_set['코인매도분할시그널']:
                                매도 = False
                                if self.back_type != '조건최적화':
                                    exec(self.sellstg, None, locals())
                                else:
                                    exec(self.dict_sellstg[j], None, locals())
                except:
                    print_exc()
                    self.BackStop(1)
                    break
