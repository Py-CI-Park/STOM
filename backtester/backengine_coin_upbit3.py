import math
import sqlite3
import pandas as pd
from traceback import print_exc
from backtester.back_static import GetBuyStg, GetSellStg, GetBuyConds, GetSellConds
from utility.setting import DB_COIN_BACK, BACK_TEMP, DICT_SET, DB_COIN_DAY, DB_COIN_MIN, ui_num, dict_min, dict_order_ratio
from utility.static import strp_time, timedelta_sec, strf_time, timedelta_day, GetUpbitHogaunit, pickle_read, pickle_write, GetUpbitPgSgSp


class CoinUpbitBackEngine3:
    def __init__(self, gubun, wq, pq, tq, bq):
        self.gubun       = gubun
        self.wq          = wq
        self.pq          = pq
        self.tq          = tq
        self.bq          = bq
        self.dict_set    = DICT_SET

        self.back_type   = None
        self.betting     = None
        self.avgtime     = None
        self.avg_list    = None
        self.startday    = None
        self.endday      = None
        self.starttime   = None
        self.endtime     = None

        self.startday_   = None
        self.endday_     = None
        self.starttime_  = None
        self.endtime_    = None

        self.buystg      = None
        self.sellstg     = None
        self.dict_mt     = None
        self.array_tick  = None
        self.dict_days   = {}

        self.tickcols    = None
        self.tickdata    = None

        self.code_list   = []
        self.buy_info_   = []
        self.buy_info    = []
        self.dict_tik_ar = {}
        self.dict_day_ar = {}
        self.dict_min_ar = {}
        self.dict_dindex = {}
        self.dict_mindex = {}
        self.bhogainfo   = {}
        self.shogainfo   = {}
        self.vars        = {}
        self.dict_cond   = {}
        self.sell_cond   = 0

        self.code        = None
        self.day_info    = None
        self.trade_info  = None
        self.current_min = None
        self.high        = False
        self.index       = 0
        self.indexb      = 0
        self.indexn      = 0
        self.tick_count  = 0
        self.total_count = 0
        self.dindex      = 0
        self.mindex      = 0

        self.InitDayInfo()
        self.InitTradeInfo()
        self.Start()

    def InitDayInfo(self):
        self.tick_count = 0
        self.day_info = {
            '손절횟수': 0,
            '거래횟수': 0,
            '직전거래시간': strp_time('%Y%m%d', '20000101'),
            '손절매도시간': strp_time('%Y%m%d', '20000101')
        }

    def InitTradeInfo(self):
        self.trade_info = {
            '보유중': False,
            '매수가': 0,
            '매도가': 0,
            '주문수량': 0,
            '보유수량': 0,
            '매수호가': 0,
            '매도호가': 0,
            '매수호가_': 0,
            '매도호가_': 0,
            '추가매수가': 0,
            '최고수익률': 0.,
            '최저수익률': 0.,
            '매수호가단위': 0,
            '매도호가단위': 0,
            '매수정정횟수': 0,
            '매도정정횟수': 0,
            '매수분할횟수': 0,
            '매도분할횟수': 0,
            '추가매수시간': [],
            '매수체결시간': strp_time('%Y%m%d', '20000101'),
            '매수주문시간': strp_time('%Y%m%d', '20000101'),
            '매도주문시간': strp_time('%Y%m%d', '20000101')
        }

    def Start(self):
        while True:
            data = self.pq.get()
            if data[0] == '백테유형':
                self.back_type = data[1]
            elif data[0] == '설정변경':
                self.dict_set = data[1]
            elif data[0] == '이전데이터날짜갱신':
                self.dict_days[data[1]] = data[2]
            elif self.back_type == '최적화':
                if data[0] == '백테정보':
                    self.betting   = data[1]
                    avg_list       = data[2]
                    self.startday  = data[3]
                    self.endday    = data[4]
                    self.starttime = data[5]
                    self.endtime   = data[6]
                    self.buystg    = GetBuyStg(data[7])
                    self.sellstg, self.dict_cond = GetSellStg(data[8])
                    self.dict_days = data[9]
                    self.CheckAvglist(avg_list)
                    if self.buystg is None or self.sellstg is None:
                        self.BackStop()
                elif data[0] == '변수정보':
                    self.vars      = data[1]
                    self.high      = data[2]
                    self.BackTest()
                    self.high      = False
            elif self.back_type == '조건최적화':
                if data[0] == '백테정보':
                    self.betting   = data[1]
                    self.avgtime   = data[2]
                    self.startday  = data[3]
                    self.endday    = data[4]
                    self.starttime = data[5]
                    self.endtime   = data[6]
                if data[0] == '조건정보':
                    self.buystg    = GetBuyConds(data[1])
                    self.sellstg, self.dict_cond = GetSellConds(data[2])
                    if self.buystg is None or self.sellstg is None:
                        self.BackStop()
                    else:
                        self.BackTest()
            elif self.back_type == '전진분석':
                if data[0] == '백테정보':
                    self.betting   = data[1]
                    avg_list       = data[2]
                    self.starttime = data[3]
                    self.endtime   = data[4]
                    self.buystg    = GetBuyStg(data[5])
                    self.sellstg, self.dict_cond = GetSellStg(data[6])
                    self.CheckAvglist(avg_list)
                    if self.buystg is None or self.sellstg is None:
                        self.BackStop()
                elif data[0] == '변수정보':
                    self.vars      = data[1]
                    self.startday  = data[2]
                    self.high      = data[4]
                    self.BackTest()
                    self.high      = False
                elif data[0] == '이전데이터갱신':
                    self.dict_days = data[1]
            elif self.back_type == '백테스트':
                if data[0] == '백테정보':
                    self.betting   = data[1]
                    self.avgtime   = data[2]
                    self.startday  = data[3]
                    self.endday    = data[4]
                    self.starttime = data[5]
                    self.endtime   = data[6]
                    self.buystg    = GetBuyStg(data[7])
                    self.sellstg, self.dict_cond = GetSellStg(data[8])
                    if self.buystg is None or self.sellstg is None:
                        self.BackStop()
                    else:
                        self.BackTest()
            elif self.back_type == '백파인더':
                if data[0] == '백테정보':
                    self.avgtime   = data[1]
                    self.startday  = data[2]
                    self.endday    = data[3]
                    self.starttime = data[4]
                    self.endtime   = data[5]
                    try:
                        self.buystg = compile(data[6], '<string>', 'exec')
                    except:
                        print_exc()
                        self.BackStop()
                    else:
                        self.BackTest()
            elif data[0] == '종목명거래대금순위':
                self.dict_mt = data[1]
            elif data[0] == '데이터크기':
                self.DataSize(data)
            elif data[0] == '데이터로딩':
                self.DataLoad(data)

    def DataSize(self, data):
        startday, endday, starttime, endtime, code_list, avg_list, code_days = data[1:]
        con = sqlite3.connect(DB_COIN_BACK)
        for code in code_list:
            ramsize = 0
            try:
                last = len(code_days[code]) - 1
                like_text = '( '
                for i, day in enumerate(code_days[code]):
                    if i != last:
                        like_text += f"`index` LIKE '{day}%' or "
                    else:
                        like_text += f"`index` LIKE '{day}%' )"
                query = f"SELECT * FROM '{code}' WHERE {like_text} and " \
                        f"`index` % 1000000 >= {starttime} and " \
                        f"`index` % 1000000 <= {endtime}"
                df = pd.read_sql(query, con)
            except:
                pass
            else:
                if len(df) > 0:
                    df['이평60']   = df['현재가'].rolling(window=60).mean().round(8)
                    df['이평300']  = df['현재가'].rolling(window=300).mean().round(8)
                    df['이평600']  = df['현재가'].rolling(window=600).mean().round(8)
                    df['이평1200'] = df['현재가'].rolling(window=1200).mean().round(8)
                    for avg in avg_list:
                        df[f'초당거래대금평균{avg}'] = df['초당거래대금'].rolling(window=avg).mean()
                        df[f'체결강도평균{avg}']    = df['체결강도'].rolling(window=avg).mean()
                        df[f'최고체결강도{avg}']    = df['체결강도'].rolling(window=avg).max()
                        df[f'최저체결강도{avg}']    = df['체결강도'].rolling(window=avg).min()
                        df[f'누적초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).sum()
                        df[f'누적초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).sum()
                    arry = df.to_numpy()
                    ramsize = arry.nbytes
            self.bq.put_nowait([code, ramsize])
        con.close()

    def DataLoad(self, data):
        startday, endday, starttime, endtime, code_list, avg_list, code_days = data[1:]
        bk   = 0
        con  = sqlite3.connect(DB_COIN_BACK)
        con2 = sqlite3.connect(DB_COIN_DAY)
        con3 = sqlite3.connect(DB_COIN_MIN)
        for code in code_list:
            df_min = None
            df_day = None
            try:
                last = len(code_days[code]) - 1
                like_text = '( '
                for i, day in enumerate(code_days[code]):
                    if i != last:
                        like_text += f"`index` LIKE '{day}%' or "
                    else:
                        like_text += f"`index` LIKE '{day}%' )"
                query = f"SELECT * FROM '{code}' WHERE {like_text} and " \
                        f"`index` % 1000000 >= {starttime} and " \
                        f"`index` % 1000000 <= {endtime}"
                df = pd.read_sql(query, con)

                if self.dict_set['코인분봉데이터']:
                    df1 = []
                    query = f"SELECT * FROM '{code}' WHERE 체결시간 < {startday * 1000000} ORDER BY 체결시간 DESC LIMIT {self.dict_set['코인분봉개수']}"
                    df2 = pd.read_sql(query, con3)
                    df1.append(df2[::-1])
                    query = f"SELECT * FROM '{code}' WHERE 체결시간 >= {startday * 1000000} and 체결시간 <= {endday * 1000000 + 240000}"
                    df2 = pd.read_sql(query, con3)
                    df1.append(df2)
                    df_min = pd.concat(df1)

                if self.dict_set['코인일봉데이터']:
                    startday_ = int(strf_time('%Y%m%d', timedelta_day(-250, strp_time('%Y%m%d', str(startday)))))
                    query = f"SELECT * FROM '{code}' WHERE 일자 >= {startday_} and 일자 <= {endday}"
                    df_day = pd.read_sql(query, con2)
            except:
                pass
            else:
                if len(df) > 0:
                    df['이평60']   = df['현재가'].rolling(window=60).mean().round(8)
                    df['이평300']  = df['현재가'].rolling(window=300).mean().round(8)
                    df['이평600']  = df['현재가'].rolling(window=600).mean().round(8)
                    df['이평1200'] = df['현재가'].rolling(window=1200).mean().round(8)
                    for avg in avg_list:
                        df[f'초당거래대금평균{avg}'] = df['초당거래대금'].rolling(window=avg).mean()
                        df[f'체결강도평균{avg}']    = df['체결강도'].rolling(window=avg).mean()
                        df[f'최고체결강도{avg}']    = df['체결강도'].rolling(window=avg).max()
                        df[f'최저체결강도{avg}']    = df['체결강도'].rolling(window=avg).min()
                        df[f'누적초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).sum()
                        df[f'누적초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).sum()
                    data = df.to_numpy()
                    if self.dict_set['백테일괄로딩']:
                        self.dict_tik_ar[code] = data
                    else:
                        pickle_write(f'{BACK_TEMP}/{code}', data)

                    if self.dict_set['코인분봉데이터']:
                        self.dict_min_ar[code] = df_min.to_numpy()
                        self.dict_mindex[code] = {}
                        for i, index in enumerate(self.dict_min_ar[code][:, 0]):
                            self.dict_mindex[code][index] = i

                    if self.dict_set['코인일봉데이터']:
                        self.dict_day_ar[code] = df_day.to_numpy()
                        self.dict_dindex[code] = {}
                        for i, index in enumerate(self.dict_day_ar[code][:, 0]):
                            self.dict_dindex[code][index] = i

                    self.code_list.append(code)
                    bk += 1
        con3.close()
        con2.close()
        con.close()
        self.bq.put_nowait(bk)
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
        self.wq.put([ui_num['C백테스트'], '전략 코드 오류로 백테스트를 중지합니다.'])

    def BackTest(self):
        same_days = self.startday_ == self.startday and self.endday_ == self.endday
        same_time = self.starttime_ == self.starttime and self.endtime_ == self.endtime
        for code in self.code_list:
            self.code = code
            self.total_count = 0

            if self.dict_set['백테주문관리적용'] and self.dict_set['코인매수금지블랙리스트'] and self.code in self.dict_set['코인블랙리스트'] and self.back_type != '백파인더':
                self.tq.put(['백테완료', 0])
                continue

            if not self.dict_set['백테일괄로딩']:
                self.dict_tik_ar = {code: pickle_read(f'{BACK_TEMP}/{code}')}

            if self.back_type in ['최적화', '전진분석'] and not self.high and self.dict_days is not None and f'{self.vars}' in self.dict_days.keys():
                self.array_tick = self.dict_tik_ar[code][(self.dict_tik_ar[code][:, 0] > self.dict_days[f'{self.vars}'] * 1000000 + 240000) &
                                                         (self.dict_tik_ar[code][:, 0] <= self.endday * 1000000 + 240000) &
                                                         (self.dict_tik_ar[code][:, 0] % 1000000 >= self.starttime) &
                                                         (self.dict_tik_ar[code][:, 0] % 1000000 <= self.endtime)]
            else:
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
                    next_day_change = i != last and str(index)[:8] != str(self.array_tick[i + 1, 0])[:8]
                    self.tick_count += 1
                    self.index  = int(index)
                    self.indexn = i

                    try:
                        if self.dict_set['코인분봉데이터']:
                            self.mindex = self.dict_mindex[code][int(str(self.index)[:10] + dict_min[self.dict_set['코인분봉기간']][str(self.index)[10:12]] + '00')]
                            self.UpdateCurrentMin(i)
                        if self.dict_set['코인일봉데이터']:
                            self.dindex = self.dict_dindex[code][int(str(self.index)[:8])]
                    except:
                        continue

                    if i != last and not next_day_change:
                        if not self.dict_set['백테주문관리적용']:
                            if not self.trade_info['보유중']:
                                self.Strategy('매수')
                            else:
                                self.Strategy('매도')
                        else:
                            if self.dict_set['코인매수주문구분'] == '시장가':
                                if not self.trade_info['보유중']:
                                    self.Strategy('매수')
                                elif self.trade_info['매수분할횟수'] < self.dict_set['코인매수분할횟수']:
                                    pre_hold_count = self.trade_info['보유수량']
                                    self.Strategy('매수')
                                    if self.trade_info['보유수량'] == pre_hold_count:
                                        self.Strategy('매도')
                                else:
                                    self.Strategy('매도')
                            elif self.dict_set['코인매수주문구분'] == '지정가':
                                if not self.trade_info['보유중']:
                                    if self.trade_info['매수호가'] == 0:
                                        self.Strategy('매수')
                                    else:
                                        self.CheckBuy()
                                elif self.trade_info['매수분할횟수'] < self.dict_set['코인매수분할횟수']:
                                    if self.trade_info['매수호가'] == 0:
                                        self.Strategy('매수')
                                    else:
                                        self.CheckBuy()
                                    if self.trade_info['매수호가'] == 0:
                                        if self.trade_info['매도호가'] == 0:
                                            self.Strategy('매도')
                                        else:
                                            self.CheckSell()
                                else:
                                    if self.trade_info['매도호가'] == 0:
                                        self.Strategy('매도')
                                    else:
                                        self.CheckSell()
                    else:
                        if self.trade_info['보유중']:
                            self.LastSell()
                        self.InitDayInfo()
                        self.InitTradeInfo()

            self.tq.put('백테완료' if self.back_type == '백파인더' else ['백테완료', 1 if self.total_count > 0 else 0])

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

    def Strategy(self, gubun):
        if gubun == '매수':
            try:
                if self.code not in self.dict_mt[self.index]:
                    return
            except:
                return
            if self.tick_count < (self.avgtime if self.back_type in ['백테스트', '조건최적화', '백파인더'] else self.vars[0]):
                return

        def now_utc():
            return strp_time('%Y%m%d%H%M%S', str(self.index))

        def GetArrayIndex(bc):
            return bc + 6 * self.avg_list.index(self.avgtime if self.back_type in ['백테스트', '조건최적화', '백파인더'] else self.vars[0])

        def 구간최고현재가(pre):
            return self.array_tick[self.indexn + 1 - pre:self.indexn + 1, 1].max()

        def 구간최저현재가(pre):
            return self.array_tick[self.indexn + 1 - pre:self.indexn + 1, 1].min()

        def 누적초당매수수량(pre):
            if pre in self.avg_list:
                return self.array_tick[self.indexn, GetArrayIndex(43)]
            else:
                return self.array_tick[self.indexn + 1 - pre:self.indexn + 1, 8].sum()

        def 누적초당매도수량(pre):
            if pre in self.avg_list:
                return self.array_tick[self.indexn, GetArrayIndex(44)]
            else:
                return self.array_tick[self.indexn + 1 - pre:self.indexn + 1, 9].sum()

        def 최고초당매수수량(pre):
            return self.array_tick[self.indexn + 1 - pre:self.indexn + 1:, 8].max()

        def 최고초당매도수량(pre):
            return self.array_tick[self.indexn + 1 - pre:self.indexn + 1:, 9].max()

        def 당일거래대금각도(pre):
            dmp_gap = self.array_tick[self.indexn, 6] - self.array_tick[self.indexn - (pre - 1), 6]
            return round(math.atan2(dmp_gap, pre) / (2 * math.pi) * 360, 2)

        def 현재가N(pre):
            return self.array_tick[self.indexn - pre, 1]

        def 고가N(pre):
            return self.array_tick[self.indexn - pre, 3]

        def 저가N(pre):
            return self.array_tick[self.indexn - pre, 4]

        def 등락율N(pre):
            return self.array_tick[self.indexn - pre, 5]

        def 당일거래대금N(pre):
            return self.array_tick[self.indexn - pre, 6]

        def 체결강도N(pre):
            return self.array_tick[self.indexn - pre, 7]

        def 초당매수수량N(pre):
            return self.array_tick[self.indexn - pre, 8]

        def 초당매도수량N(pre):
            return self.array_tick[self.indexn - pre, 9]

        def 초당거래대금N(pre):
            return self.array_tick[self.indexn - pre, 10]

        def 고저평균대비등락율N(pre):
            return self.array_tick[self.indexn - pre, 11]

        def 매도총잔량N(pre):
            return self.array_tick[self.indexn - pre, 12]

        def 매수총잔량N(pre):
            return self.array_tick[self.indexn - pre, 13]

        def 매도잔량1N(pre):
            return self.array_tick[self.indexn - pre, 28]

        def 매수잔량1N(pre):
            return self.array_tick[self.indexn - pre, 29]

        def 매도수5호가잔량합N(pre):
            return self.array_tick[self.indexn - pre, 34]

        def 이평60N(pre):
            return self.array_tick[self.indexn - pre, 35]

        def 이평300N(pre):
            return self.array_tick[self.indexn - pre, 36]

        def 이평600N(pre):
            return self.array_tick[self.indexn - pre, 37]

        def 이평1200N(pre):
            return self.array_tick[self.indexn - pre, 38]

        def 초당거래대금평균N(pre):
            return self.array_tick[self.indexn - pre, GetArrayIndex(39)]

        def 체결강도평균N(pre):
            return self.array_tick[self.indexn - pre, GetArrayIndex(40)]

        def 최고체결강도N(pre):
            return self.array_tick[self.indexn - pre, GetArrayIndex(41)]

        def 최저체결강도N(pre):
            return self.array_tick[self.indexn - pre, GetArrayIndex(42)]

        def 누적초당매수수량N(pre):
            return self.array_tick[self.indexn - pre, GetArrayIndex(43)]

        def 누적초당매도수량N(pre):
            return self.array_tick[self.indexn - pre, GetArrayIndex(44)]

        def 당일거래대금각도N(pre):
            jvp_gap = self.array_tick[self.indexn - pre, 6] - self.array_tick[self.indexn - pre - 29, 6]
            return round(math.atan2(jvp_gap, 30) / (2 * math.pi) * 360, 2)

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
            이평60, 이평300, 이평600, 이평1200 = self.array_tick[self.indexn, 1:39]
        종목코드, 데이터길이, 시분초, 호가단위 = self.code, self.tick_count, int(str(self.index)[8:]), GetUpbitHogaunit(현재가)
        초당거래대금평균, 체결강도평균, 최고체결강도, 최저체결강도 = self.array_tick[self.indexn, GetArrayIndex(39):GetArrayIndex(43)]
        수익금, 수익률, 보유수량, 매수시간, 최고수익률, 최저수익률 = 0, 0., 0, strp_time('%Y%m%d', '20000101'), 0., 0.
        if self.trade_info['보유중']:
            bg = self.trade_info['보유수량'] * self.trade_info['매수가']
            cg = self.trade_info['보유수량'] * 현재가
            _, 수익금, 수익률 = GetUpbitPgSgSp(bg, cg)
            if 수익률 > self.trade_info['최고수익률']:
                self.trade_info['최고수익률'] = 수익률
            elif 수익률 < self.trade_info['최저수익률']:
                self.trade_info['최저수익률'] = 수익률
            보유수량 = self.trade_info['보유수량']
            매수시간 = self.trade_info['매수체결시간']
            최고수익률 = self.trade_info['최고수익률']
            최저수익률 = self.trade_info['최저수익률']
        self.buy_info_ = [
            등락율, 고저평균대비등락율, 초당거래대금, 초당거래대금평균, 당일거래대금, 체결강도, 체결강도평균, 최고체결강도, 최저체결강도,
            현재가, 초당매수수량, 초당매도수량, 매수잔량1, 매도잔량1, 매수총잔량, 매도총잔량, 이평60, 이평300, 이평600, 이평1200
        ]
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
        self.bhogainfo = self.bhogainfo[self.dict_set['코인매수시장가잔량범위']]
        self.shogainfo = self.shogainfo[self.dict_set['코인매도시장가잔량범위']]

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
            매수 = True
            try:
                exec(self.buystg, None, locals())
            except:
                print_exc()
                self.BackStop()
        elif gubun == '매수':
            if not self.dict_set['백테주문관리적용']:
                self.trade_info['주문수량'] = round(self.betting / 현재가, 8)
                매수 = True
                try:
                    exec(self.buystg, None, locals())
                except:
                    print_exc()
                    self.BackStop()
            else:
                cancel = False
                if self.dict_set['코인매수금지거래횟수'] and self.dict_set['코인매수금지거래횟수값'] <= self.trade_info['거래횟수']:
                    cancel = True
                if self.dict_set['코인매수금지손절횟수'] and self.dict_set['코인매수금지손절횟수값'] <= self.trade_info['손절횟수']:
                    cancel = True
                if self.dict_set['코인매수금지시간'] and self.dict_set['코인매수금지시작시간'] < int(str(self.index)[8:]) < self.dict_set['코인매수금지종료시간']:
                    cancel = True
                if self.dict_set['코인매수금지간격'] and now_utc() <= self.day_info['직전거래시간']:
                    cancel = True
                if self.dict_set['코인매수금지손절간격'] and now_utc() <= self.day_info['손절매도시간']:
                    cancel = True
                if self.dict_set['코인매수금지200원이하'] and 현재가 <= 200:
                    cancel = True
                if cancel: return

                if self.dict_set['코인매수분할횟수'] == 1:
                    self.trade_info['주문수량'] = round(self.betting / 현재가, 8)
                else:
                    oc_ratio = dict_order_ratio[self.dict_set['코인매수분할방법']][self.dict_set['코인매수분할횟수']][self.trade_info['매수분할횟수']]
                    self.trade_info['주문수량'] = round(self.betting / (현재가 if not self.trade_info['보유중'] else self.trade_info['매수가']) * oc_ratio / 100, 8)

                if self.dict_set['코인매수주문구분'] == '지정가':
                    기준가격 = 현재가
                    if self.dict_set['코인매수지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                    if self.dict_set['코인매수지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                    self.trade_info['매수호가_'] = 기준가격 + 호가단위 * self.dict_set['코인매수지정가호가번호']

                if not self.trade_info['보유중']:
                    매수 = True
                    try:
                        exec(self.buystg, None, locals())
                    except:
                        print_exc()
                        self.BackStop()
                else:
                    분할매수기준수익률 = round((현재가 / self.buy_info[9] - 1) * 100, 2) if self.dict_set['코인매수분할고정수익률'] else 수익률
                    if self.dict_set['코인매수분할하방'] and 분할매수기준수익률 < -self.dict_set['코인매수분할하방수익률']:  self.Buy()
                    elif self.dict_set['코인매수분할상방'] and 분할매수기준수익률 > self.dict_set['코인매수분할상방수익률']: self.Buy()
                    elif self.dict_set['코인매수분할시그널']:
                        매수 = True
                        exec(self.buystg, None, locals())
        else:
            매수시점등락율, 매수시점고저평균대비등락율, 매수시점초당거래대금, 매수시점초당거래대금평균, 매수시점당일거래대금, 매수시점체결강도, \
                매수시점체결강도평균, 매수시점최고체결강도, 매수시점최저체결강도, 매수시점현재가, 매수시점초당매수수량, 매수시점초당매도수량, \
                매수시점매수잔량1, 매수시점매도잔량1, 매수시점매수총잔량, 매수시점매도총잔량, 매수시점이평60, 매수시점이평300, \
                매수시점이평600, 매수시점이평1200 = self.buy_info

            if not self.dict_set['백테주문관리적용']:
                self.trade_info['주문수량'] = self.trade_info['보유수량']
                매도 = False
                try:
                    exec(self.sellstg, None, locals())
                except:
                    print_exc()
                    self.BackStop()
            else:
                if (self.dict_set['코인매도손절수익률청산'] and 수익률 < -self.dict_set['코인매도손절수익률']) or \
                        (self.dict_set['코인매도손절수익금청산'] and 수익금 < -self.dict_set['코인매도손절수익금'] * 10000):
                    self.Sonjeol()
                    return

                cancel = False
                if self.dict_set['코인매도금지시간'] and self.dict_set['코인매도금지시작시간'] < int(str(self.index)[8:]) < self.dict_set['코인매도금지종료시간']:
                    cancel = True
                elif self.dict_set['코인매도금지간격'] and now_utc() <= self.day_info['직전거래시간']:
                    cancel = True
                elif self.dict_set['코인매수분할횟수'] > 1 and self.dict_set['코인매도금지매수횟수'] and self.trade_info['매수분할횟수'] <= self.dict_set['코인매도금지매수횟수값']:
                    cancel = True
                if cancel: return

                if self.dict_set['코인매도분할횟수'] == 1:
                    self.trade_info['주문수량'] = self.trade_info['보유수량']
                else:
                    oc_ratio = dict_order_ratio[self.dict_set['코인매도분할방법']][self.dict_set['코인매도분할횟수']][self.trade_info['매도분할횟수']]
                    self.trade_info['주문수량'] = round(self.betting / self.trade_info['매수가'] * oc_ratio / 100, 8)
                    if self.trade_info['주문수량'] > self.trade_info['보유수량'] or self.trade_info['매도분할횟수'] + 1 == self.dict_set['코인매도분할횟수']:
                        self.trade_info['주문수량'] = self.trade_info['보유수량']

                if self.dict_set['코인매도주문구분'] == '지정가':
                    기준가격 = 현재가
                    if self.dict_set['코인매도지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                    if self.dict_set['코인매도지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                    self.trade_info['매도호가_'] = 기준가격 + 호가단위 * self.dict_set['코인매도지정가호가번호']

                if self.dict_set['코인매도분할횟수'] == 1:
                    매도 = False
                    try:
                        exec(self.sellstg, None, locals())
                    except:
                        print_exc()
                        self.BackStop()
                else:
                    if self.dict_set['코인매도분할하방'] and 수익률 < -self.dict_set['코인매도분할하방수익률'] * (self.trade_info['매도분할횟수'] + 1):  self.Sell(100)
                    elif self.dict_set['코인매도분할상방'] and 수익률 > self.dict_set['코인매도분할상방수익률'] * (self.trade_info['매도분할횟수'] + 1): self.Sell(100)
                    elif self.dict_set['코인매도분할시그널']:
                        매도 = False
                        exec(self.sellstg, None, locals())

    def Buy(self):
        if not self.dict_set['백테주문관리적용']:
            매수수량 = self.trade_info['주문수량']
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
                    self.trade_info['매수가'] = round(매수금액 / 매수수량, 4)
                    self.trade_info['보유수량'] = 매수수량
                    self.UpdateBuyInfo(True)
        else:
            현재가 = self.array_tick[self.indexn, 1]
            if self.dict_set['코인매수주문구분'] == '시장가':
                매수수량 = self.trade_info['주문수량']
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
                        if self.trade_info['보유수량'] == 0:
                            self.trade_info['매수가'] = round(매수금액 / 매수수량, 4)
                            self.trade_info['보유수량'] = 매수수량
                            self.UpdateBuyInfo(True)
                        else:
                            self.trade_info['추가매수가'] = int(round(매수금액 / 매수수량))
                            self.trade_info['매수가'] = round((self.trade_info['매수가'] * self.trade_info['보유수량'] + 매수금액) / (self.trade_info['보유수량'] + 매수수량), 4)
                            self.trade_info['보유수량'] += 매수수량
                            self.UpdateBuyInfo(False)
            elif self.dict_set['코인매수주문구분'] == '지정가':
                self.trade_info['매수호가'] = self.trade_info['매수호가_']
                self.trade_info['매수호가단위'] = GetUpbitHogaunit(현재가)
                self.trade_info['매수주문시간'] = timedelta_sec(self.dict_set['코인매수취소시간초'], strp_time('%Y%m%d%H%M%S', str(self.index)))

    def CheckBuy(self):
        현재가 = self.array_tick[self.indexn, 1]
        if self.dict_set['코인매수취소관심이탈'] and self.index in self.dict_mt.keys() and self.code not in self.dict_mt[self.index]:
            self.trade_info['매수호가'] = 0
        elif self.dict_set['코인매수취소시간'] and strp_time('%Y%m%d%H%M%S', str(self.index)) > self.trade_info['매수주문시간']:
            self.trade_info['매수호가'] = 0
        elif self.trade_info['매수정정횟수'] < self.dict_set['코인매수정정횟수'] and \
                현재가 >= self.trade_info['매수호가'] + self.trade_info['매수호가단위'] * self.dict_set['코인매수정정호가차이']:
            self.trade_info['매수호가'] = 현재가 - self.trade_info['매수호가단위'] * self.dict_set['코인매수정정호가']
            self.trade_info['매수정정횟수'] += 1
            self.trade_info['매수호가단위'] = GetUpbitHogaunit(현재가)
        elif 현재가 < self.trade_info['매수호가']:
            if self.trade_info['보유수량'] == 0:
                self.trade_info['매수가'] = self.trade_info['매수호가']
                self.trade_info['보유수량'] = round(self.betting / self.trade_info['매수호가'], 8)
                self.UpdateBuyInfo(True)
            else:
                self.trade_info['추가매수가'] = self.trade_info['매수호가']
                self.trade_info['매수가'] = round(self.trade_info['매수가'] * self.trade_info['보유수량'] + self.trade_info['매수호가'] * self.trade_info['주문수량'] / (self.trade_info['보유수량'] + self.trade_info['주문수량']), 4)
                self.trade_info['보유수량'] = round(self.trade_info['보유수량'] + self.trade_info['주문수량'], 8)
                self.UpdateBuyInfo(False)

    def UpdateBuyInfo(self, firstbuy):
        self.buy_info = self.buy_info_
        self.trade_info['보유중'] = True
        if firstbuy:
            self.indexb = self.indexn
            self.trade_info['추가매수시간'] = []
        else:
            self.trade_info['추가매수시간'].append(f"{self.index};{self.trade_info['추가매수가']}")
        if self.dict_set['백테주문관리적용']:
            self.trade_info['매수호가'] = 0
            self.trade_info['매수정정횟수'] = 0
            self.trade_info['매수분할횟수'] += 1
            self.trade_info['매수체결시간'] = strp_time('%Y%m%d%H%M%S', str(self.index))
            self.day_info['직전거래시간'] = timedelta_sec(self.dict_set['코인매수금지간격초'], self.trade_info['매수체결시간'])

    def Sell(self, sell_cond):
        if not self.dict_set['백테주문관리적용']:
            남은수량 = self.trade_info['주문수량']
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
                self.trade_info['매도가'] = round(매도금액 / self.trade_info['주문수량'], 4)
                self.sell_cond = sell_cond
                self.UpdateSellInfo()
        else:
            if self.dict_set['코인매도주문구분'] == '시장가':
                남은수량 = self.trade_info['주문수량']
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
                    self.trade_info['매도가'] = round(매도금액 / self.trade_info['주문수량'], 4)
                    self.sell_cond = sell_cond
                    self.UpdateSellInfo()
            elif self.dict_set['코인매도주문구분'] == '지정가':
                현재가 = self.array_tick[self.indexn, 1]
                self.sell_cond = sell_cond
                self.trade_info['매도호가'] = self.trade_info['매도호가_']
                self.trade_info['매도호가단위'] = GetUpbitHogaunit(현재가)
                self.trade_info['매도주문시간'] = timedelta_sec(self.dict_set['코인매도취소시간초'], strp_time('%Y%m%d%H%M%S', str(self.index)))

    def CheckSell(self):
        현재가 = self.array_tick[self.indexn, 1]
        이전인덱스 = self.array_tick[self.indexn - 1, 0]
        if self.dict_set['코인매도취소관심진입'] and 이전인덱스 in self.dict_mt.keys() and self.index in self.dict_mt.keys() and \
                self.code not in self.dict_mt[이전인덱스] and self.code in self.dict_mt[self.index]:
            self.trade_info['매도호가'] = 0
        elif self.dict_set['코인매도취소시간'] and strp_time('%Y%m%d%H%M%S', str(self.index)) > self.trade_info['매도주문시간']:
            self.trade_info['매도호가'] = 0
        elif self.trade_info['매도정정횟수'] < self.dict_set['코인매도정정횟수'] and \
                현재가 <= self.trade_info['매도호가'] - self.trade_info['매도호가단위'] * self.dict_set['코인매도정정호가차이']:
            self.trade_info['매도호가'] = 현재가 + self.trade_info['매도호가단위'] * self.dict_set['코인매도정정호가']
            self.trade_info['매도정정횟수'] += 1
            self.trade_info['매도호가단위'] = GetUpbitHogaunit(현재가)
        elif 현재가 > self.trade_info['매도호가']:
            self.trade_info['매도가'] = self.trade_info['매도호가']
            self.UpdateSellInfo()

    def UpdateSellInfo(self):
        self.CalculationEyun()
        if not self.dict_set['백테주문관리적용']:
            self.InitTradeInfo()
        else:
            if self.trade_info['보유수량'] - self.trade_info['주문수량'] > 0:
                self.trade_info['매도호가'] = 0
                self.trade_info['보유수량'] = round(self.trade_info['보유수량'] - self.trade_info['주문수량'], 8)
                self.trade_info['매도정정횟수'] = 0
                self.trade_info['매도분할횟수'] += 1
            else:
                self.InitTradeInfo()

    def Sonjeol(self):
        origin_sell_gubun = self.dict_set['코인매도주문구분']
        self.dict_set['코인매도주문구분'] = '시장가'
        self.trade_info['주문수량'] = self.trade_info['보유수량']
        self.Sell(200)
        self.dict_set['코인매도주문구분'] = origin_sell_gubun

    def LastSell(self):
        매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5 = self.array_tick[self.indexn, 14:34]
        dict_shogainfo = {
            1: {매수호가1: 매수잔량1},
            2: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2},
            3: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3},
            4: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3, 매수호가4: 매수잔량4},
            5: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3, 매수호가4: 매수잔량4, 매수호가5: 매수잔량5}
        }
        self.shogainfo = dict_shogainfo[self.dict_set['코인매도시장가잔량범위']]

        남은수량 = self.trade_info['보유수량']
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
            self.trade_info['매도가'] = round(매도금액 / self.trade_info['보유수량'], 4)
        elif 매도금액 == 0:
            self.trade_info['매도가'] = self.array_tick[self.indexn, 1]
        else:
            self.trade_info['매도가'] = round(매도금액 / (self.trade_info['보유수량'] - 남은수량), 4)

        self.trade_info['주문수량'] = self.trade_info['보유수량']
        self.sell_cond = 0
        self.UpdateSellInfo()

    def CalculationEyun(self):
        self.total_count += 1
        hold_sec = self.indexn - self.indexb
        hold_rec = self.trade_info['보유수량'] - self.trade_info['주문수량'] == 0
        bg = self.trade_info['주문수량'] * self.trade_info['매수가']
        pg, sg, sp = GetUpbitPgSgSp(bg, self.trade_info['주문수량'] * self.trade_info['매도가'])
        self.tq.put(['백테결과', self.code, 0, int(self.array_tick[self.indexb, 0]), self.index, hold_sec,
                     self.trade_info['매수가'], self.trade_info['매도가'], bg, pg, sp, sg, self.dict_cond[self.sell_cond],
                     '^'.join(self.trade_info['추가매수시간']), hold_rec])
        if self.dict_set['백테주문관리적용']:
            self.day_info['거래횟수'] += 1
            sell_time = strp_time('%Y%m%d%H%M%S', str(self.index))
            self.day_info['직전거래시간'] = timedelta_sec(self.dict_set['코인매수금지간격초'], sell_time)
            if sp < 0:
                self.day_info['손절횟수'] += 1
                self.day_info['손절매도시간'] = timedelta_sec(self.dict_set['코인매수금지손절간격초'], sell_time)
