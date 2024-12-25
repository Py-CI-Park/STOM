import gc
import math
import sqlite3
import datetime
import numpy as np
import pandas as pd
from traceback import print_exc
from backtester.back_static import GetBuyStg, GetSellStg, GetBuyConds, GetSellConds, GetBackloadCodeQuery, \
    GetBackloadDayQuery, AddAvgData, GetTradeInfo, AddTalib
from utility.setting import DB_STOCK_BACK, BACK_TEMP, ui_num, DICT_SET
# noinspection PyUnresolvedReferences
from utility.static import strp_time, timedelta_sec, pickle_read, pickle_write, GetKiwoomPgSgSp, GetUvilower5, GetHogaunit


# noinspection PyUnusedLocal
class StockBackEngine:
    def __init__(self, gubun, wq, tq, bq, beq_list, bstq_list, profile=False):
        gc.disable()
        self.gubun        = gubun
        self.wq           = wq
        self.tq           = tq
        self.bq           = bq
        self.beq_list     = beq_list
        self.beq          = beq_list[gubun]
        self.bstq_list    = bstq_list
        self.profile      = profile
        self.dict_set     = DICT_SET

        self.total_ticks  = 0
        self.total_secds  = 0
        self.sell_count   = 0

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
        self.dict_kd      = None
        self.array_tick   = None

        self.is_long      = None
        self.dict_hg      = None

        self.code_list    = []
        self.vars         = []
        self.vars_list    = []
        self.vars_lists   = []
        self.dict_tik_ar  = {}
        self.bhogainfo    = {}
        self.shogainfo    = {}
        self.dict_buystg  = {}
        self.dict_sellstg = {}
        self.dict_sconds  = {}
        self.sell_cond    = 0
        self.opti_turn    = 0

        self.code         = ''
        self.name         = ''
        self.day_info     = {}
        self.trade_info   = {}
        self.index        = 0
        self.indexn       = 0
        self.indexb       = 0
        self.tick_count   = 0
        self.last         = 0

        self.tick_calcul  = False
        self.pattern      = False
        self.pattern_test = False
        self.pattern_buy  = []
        self.pattern_sell = []
        self.dict_pattern = {}
        self.dict_pattern_buy  = {}
        self.dict_pattern_sell = {}
        self.MainLoop()

    def MainLoop(self):
        while True:
            data = self.beq.get()
            if '정보' in data[0]:
                if self.back_type == '최적화':
                    if data[0] == '백테정보':
                        self.betting    = data[1]
                        avg_list        = data[2]
                        self.startday   = data[3]
                        self.endday     = data[4]
                        self.starttime  = data[5]
                        self.endtime    = data[6]
                        self.buystg     = GetBuyStg(data[7], self.gubun)
                        self.sellstg, self.dict_sconds = GetSellStg(data[8], self.gubun)
                        self.CheckAvglist(avg_list)
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop(1)
                    elif data[0] == '변수정보':
                        self.vars_list  = data[1]
                        self.opti_turn  = data[2]
                        self.vars       = [var[1] for var in self.vars_list]
                        self.InitDivid(0)
                        self.InitTradeInfo()
                        self.BackTest()
                elif self.back_type == '전진분석':
                    if data[0] == '백테정보':
                        self.betting    = data[1]
                        avg_list        = data[2]
                        self.starttime  = data[3]
                        self.endtime    = data[4]
                        self.buystg     = GetBuyStg(data[5], self.gubun)
                        self.sellstg, self.dict_sconds = GetSellStg(data[6], self.gubun)
                        self.CheckAvglist(avg_list)
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop(1)
                    elif data[0] == '변수정보':
                        self.vars_list  = data[1]
                        self.opti_turn  = data[2]
                        self.vars       = [var[1] for var in self.vars_list]
                        self.startday   = data[3]
                        self.endday     = data[4]
                        if self.opti_turn == 0:
                            self.tick_calcul = False
                        self.InitDivid(0)
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
                        self.buystg     = GetBuyStg(data[7], self.gubun)
                        self.sellstg, self.dict_sconds = GetSellStg(data[8], self.gubun)
                        self.CheckAvglist(avg_list)
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop(1)
                    elif data[0] == '변수정보':
                        self.vars_lists = data[1]
                        self.InitDivid(0)
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
                        self.dict_sconds  = {}
                        error = False
                        for i in range(20):
                            buystg = GetBuyConds(data[1][i], self.gubun)
                            sellstg, dict_cond = GetSellConds(data[2][i], self.gubun)
                            self.dict_buystg[i]  = buystg
                            self.dict_sellstg[i] = sellstg
                            self.dict_sconds[i]  = dict_cond
                            if buystg is None or sellstg is None: error = True
                        self.InitDivid(0)
                        self.InitTradeInfo()
                        if error:
                            self.BackStop(1)
                        else:
                            self.BackTest()
                elif self.back_type == '백테스트':
                    if data[0] == '백테정보':
                        self.betting    = data[1]
                        self.avgtime    = data[2]
                        self.startday   = data[3]
                        self.endday     = data[4]
                        self.starttime  = data[5]
                        self.endtime    = data[6]
                        self.buystg     = GetBuyStg(data[7], self.gubun)
                        self.sellstg, self.dict_sconds = GetSellStg(data[8], self.gubun)
                        self.pattern_test = data[9]
                        self.InitDivid(2)
                        self.InitTradeInfo()
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop(1)
                        elif self.pattern_test and self.pattern_buy is None:
                            self.BackStop(0)
                        else:
                            start = datetime.datetime.now()
                            self.BackTest()
                            self.total_secds = (datetime.datetime.now() - start).total_seconds()
                    elif data[0] == '학습정보':
                        self.betting    = data[1]
                        self.avgtime    = data[2]
                        self.startday   = data[3]
                        self.endday     = data[4]
                        self.starttime  = data[5]
                        self.endtime    = data[6]
                        self.buystg     = GetBuyStg(data[7], self.gubun)
                        self.sellstg, self.dict_sconds = GetSellStg(data[8], self.gubun)
                        self.dict_pattern      = data[9]
                        self.dict_pattern_buy  = data[10]
                        self.dict_pattern_sell = data[11]
                        self.pattern_buy  = []
                        self.pattern_sell = []
                        self.InitDivid(1)
                        self.InitTradeInfo()
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop(1)
                        else:
                            self.BackTest()
                    elif data[0] == '모델정보':
                        self.pattern_buy  = data[1]
                        self.pattern_sell = data[2]
                    elif data[0] == '패턴정보':
                        self.dict_pattern      = data[1]
                        self.dict_pattern_buy  = data[2]
                        self.dict_pattern_sell = data[3]
                elif self.back_type == '백파인더':
                    if data[0] == '백테정보':
                        self.avgtime    = data[1]
                        self.startday   = data[2]
                        self.endday     = data[3]
                        self.starttime  = data[4]
                        self.endtime    = data[5]
                        self.InitDivid(0)
                        self.InitTradeInfo()
                        try:
                            self.buystg = compile(data[6], '<string>', 'exec')
                        except:
                            print_exc()
                            self.BackStop(1)
                        else:
                            self.BackTest()
            elif data[0] == '백테유형':
                self.back_type = data[1]
                self.tick_calcul = False
            elif data[0] == '설정변경':
                self.dict_set = data[1]
            elif data[0] == '종목명':
                self.dict_cn = data[1]
                self.dict_kd = data[2]
            elif data[0] in ('데이터크기', '데이터로딩'):
                self.DataLoad(data)
            elif data[0] == '데이터이동':
                self.SendData(data)
            elif data[0] == '데이터전송':
                self.RecvdData(data)
            elif data == '벤치점수요청':
                self.bq.put((self.total_ticks, self.total_secds, round(self.total_ticks / self.total_secds, 2)))

    def SendData(self, data):
        _, cnt, procn = data
        for i, code in enumerate(self.code_list):
            if i >= cnt:
                data = ('데이터전송', code, self.dict_tik_ar[code])
                self.beq_list[procn].put(data)
                del self.dict_tik_ar[code]
                print(f'백테엔진 데이터 재분배: 종목코드[{code}] 엔진번호[{self.gubun}->{procn}]')
        self.code_list = self.code_list[:cnt]

    def RecvdData(self, data):
        _, code, arry = data
        if code in self.dict_tik_ar.keys():
            arry = np.r_[self.dict_tik_ar[code], arry]
        self.dict_tik_ar[code] = arry
        if code not in self.code_list:
            self.code_list.append(code)

    def InitDivid(self, pattern):
        self.sell_count = 0
        if pattern == 0:
            self.pattern, self.pattern_test = False, False
        elif pattern == 1:
            self.pattern, self.pattern_test = True, False
        else:
            self.pattern = False
        if self.back_type == '백테스트':
            self.opti_turn = 0
        elif self.back_type in ('GA최적화', '조건최적화'):
            self.opti_turn = 3

    def InitTradeInfo(self):
        self.tick_count = 0
        v = GetTradeInfo(1)
        if self.opti_turn == 1:
            self.trade_info = {vars_turn: {vars_key: v for vars_key in range(len(self.vars_list[vars_turn][0]))} for vars_turn in range(len(self.vars_list))}
        elif self.opti_turn == 3:
            self.trade_info = {vars_turn: {vars_key: v for vars_key in range(20)} for vars_turn in range(50 if self.back_type == 'GA최적화' else 1)}
        else:
            self.trade_info = {0: {0: v}}

    def DataLoad(self, data):
        bk = 0
        divid_mode = data[-2]
        con = sqlite3.connect(DB_STOCK_BACK)

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
                    self.bq.put((code, len_df_tick))
                elif len_df_tick > 0:
                    self.total_ticks += len_df_tick
                    df_tick = AddAvgData(df_tick, 3, avg_list)
                    arry_tick = np.array(df_tick)
                    if self.dict_set['보조지표사용']:
                        arry_tick = AddTalib(arry_tick, self.dict_set['보조지표설정'])
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
                    self.bq.put((day, len_df_tick))
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
                        self.total_ticks += len_df_tick
                        df_tick = AddAvgData(df_tick, 3, avg_list)
                        arry_tick = np.array(df_tick)
                        if self.dict_set['보조지표사용']:
                            arry_tick = AddTalib(arry_tick, self.dict_set['보조지표설정'])
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
                    self.bq.put((day, len_df_tick))
            elif gubun == '데이터로딩':
                df_tick, len_df_tick = None, 0
                try:
                    df_tick = pd.read_sql(GetBackloadCodeQuery(code, day_list, starttime, endtime), con)
                    len_df_tick = len(df_tick)
                except:
                    pass
                if len_df_tick > 0:
                    self.total_ticks += len_df_tick
                    df_tick = AddAvgData(df_tick, 3, avg_list)
                    arry_tick = np.array(df_tick)
                    if self.dict_set['보조지표사용']:
                        arry_tick = AddTalib(arry_tick, self.dict_set['보조지표설정'])
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
            self.wq.put((ui_num['S백테스트'], '백테엔진 구동 시 포함되지 않은 평균값 틱수를 사용하여 중지되었습니다.'))
            self.wq.put((ui_num['S백테스트'], '누락된 평균값 틱수를 추가하여 백테엔진을 재시작하십시오.'))
            self.BackStop(1)

    def BackStop(self, gubun):
        self.back_type = None
        if self.gubun == 0:
            if gubun:
                self.wq.put((ui_num['S백테스트'], '전략 코드 오류로 백테스트를 중지합니다.'))
            else:
                self.wq.put((ui_num['S백테스트'], '학습된 패턴 데이터가 없어 백테스트를 중지합니다.'))

    def SetArrayTick(self, code, same_days, same_time):
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

    def BackTest(self):
        if self.profile:
            import cProfile
            self.pr = cProfile.Profile()
            self.pr.enable()

        same_days = self.startday_ == self.startday and self.endday_ == self.endday
        same_time = self.starttime_ == self.starttime and self.endtime_ == self.endtime

        if not self.tick_calcul and self.opti_turn in (1, 3):
            total_ticks = 0
            for code in self.code_list:
                self.SetArrayTick(code, same_days, same_time)
                total_ticks += len(self.array_tick)
            self.tq.put(('전체틱수', int(total_ticks / 100)))
            self.tick_calcul = True

        j = 0
        len_codes = len(self.code_list)
        for k, code in enumerate(self.code_list):
            self.code = code
            self.name = self.dict_cn[self.code] if self.code in self.dict_cn.keys() else self.code
            self.SetArrayTick(code, same_days, same_time)
            self.last = len(self.array_tick) - 1
            if self.last > 0:
                for i, index in enumerate(self.array_tick[:, 0]):
                    self.index  = int(index)
                    self.indexn = i
                    self.tick_count += 1
                    next_day_change = i == self.last or str(index)[:8] != str(self.array_tick[i + 1, 0])[:8]
                    if not next_day_change:
                        try:
                            self.Strategy()
                        except:
                            print_exc()
                            self.BackStop(1)
                            return
                    else:
                        self.LastSell()
                        self.InitTradeInfo()

                    j += 1
                    if self.opti_turn in (1, 3) and j % 100 == 0: self.tq.put('탐색완료')

            self.tq.put(('백테완료', self.gubun, k+1, len_codes))

        if self.pattern: self.tq.put(('학습결과', self.pattern_buy, self.pattern_sell))
        if self.profile: self.pr.print_stats(sort='cumulative')

    def Strategy(self):
        def now():
            return strp_time('%Y%m%d%H%M%S', str(self.index))

        def Parameter_Previous(aindex, pre):
            pindex = (self.indexn - pre) if pre != -1 else self.indexb
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

        def 관심종목N(pre):
            return Parameter_Previous(44, pre)

        def 이동평균(tick, pre=0):
            if tick == 60:
                return Parameter_Previous(45, pre)
            elif tick == 300:
                return Parameter_Previous(46, pre)
            elif tick == 600:
                return Parameter_Previous(47, pre)
            elif tick == 1200:
                return Parameter_Previous(48, pre)
            else:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else self.indexb + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else self.indexb + 1
                return round(self.array_tick[sindex:eindex, 1].mean(), 3)

        def GetArrayIndex(aindex):
            return aindex + 13 * self.avg_list.index(self.avgtime if self.back_type in ('백테스트', '조건최적화', '백파인더') else self.vars[0])

        def Parameter_Area(aindex, vindex, tick, pre, gubun_):
            if tick in self.avg_list:
                return Parameter_Previous(GetArrayIndex(aindex), pre)
            else:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else self.indexb + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else self.indexb + 1
                if gubun_ == 'max':
                    return self.array_tick[sindex:eindex, vindex].max()
                elif gubun_ == 'min':
                    return self.array_tick[sindex:eindex, vindex].min()
                elif gubun_ == 'sum':
                    return self.array_tick[sindex:eindex, vindex].sum()
                else:
                    return self.array_tick[sindex:eindex, vindex].mean()

        def 최고현재가(tick, pre=0):
            return Parameter_Area(49, 1, tick, pre, 'max')

        def 최저현재가(tick, pre=0):
            return Parameter_Area(50, 1, tick, pre, 'min')

        def 체결강도평균(tick, pre=0):
            return round(Parameter_Area(51, 7, tick, pre, 'mean'), 3)

        def 최고체결강도(tick, pre=0):
            return Parameter_Area(52, 7, tick, pre, 'max')

        def 최저체결강도(tick, pre=0):
            return Parameter_Area(53, 7, tick, pre, 'min')

        def 최고초당매수수량(tick, pre=0):
            return Parameter_Area(54, 14, tick, pre, 'max')

        def 최고초당매도수량(tick, pre=0):
            return Parameter_Area(55, 15, tick, pre, 'max')

        def 누적초당매수수량(tick, pre=0):
            return Parameter_Area(56, 14, tick, pre, 'sum')

        def 누적초당매도수량(tick, pre=0):
            return Parameter_Area(57, 15, tick, pre, 'sum')

        def 초당거래대금평균(tick, pre=0):
            return int(Parameter_Area(58, 19, tick, pre, 'mean'))

        def Parameter_Dgree(aindex, vindex, tick, pre, cf):
            if tick in self.avg_list:
                return Parameter_Previous(GetArrayIndex(aindex), pre)
            else:
                sindex = (self.indexn - pre - tick - 1) if pre != -1  else self.indexb - tick - 1
                eindex = (self.indexn - pre) if pre != -1  else self.indexb
                dmp_gap = self.array_tick[eindex, vindex] - self.array_tick[sindex, vindex]
                return round(math.atan2(dmp_gap * cf, tick) / (2 * math.pi) * 360, 2)

        def 등락율각도(tick, pre=0):
            return Parameter_Dgree(59, 5, tick, pre, 5)

        def 당일거래대금각도(tick, pre=0):
            return Parameter_Dgree(60, 6, tick, pre, 0.01)

        def 전일비각도(tick, pre=0):
            return Parameter_Dgree(61, 9, tick, pre, 1)

        if self.dict_set['보조지표사용']:
            def BBU_N(pre):
                return Parameter_Previous(-14, pre)

            def BBM_N(pre):
                return Parameter_Previous(-13, pre)

            def BBL_N(pre):
                return Parameter_Previous(-12, pre)

            def MACD_N(pre):
                return Parameter_Previous(-11, pre)

            def MACDS_N(pre):
                return Parameter_Previous(-10, pre)

            def MACDH_N(pre):
                return Parameter_Previous(-9, pre)

            def APO_N(pre):
                return Parameter_Previous(-8, pre)

            def KAMA_N(pre):
                return Parameter_Previous(-7, pre)

            def RSI_N(pre):
                return Parameter_Previous(-6, pre)

            def HT_SINE_N(pre):
                return Parameter_Previous(-5, pre)

            def HT_LSINE_N(pre):
                return Parameter_Previous(-4, pre)

            def HT_PHASE_N(pre):
                return Parameter_Previous(-3, pre)

            def HT_QUDRA_N(pre):
                return Parameter_Previous(-2, pre)

            def OBV_N(pre):
                return Parameter_Previous(-1, pre)

            BBU, BBM, BBL, MACD, MACDS, MACDH, APO, KAMA, RSI, HT_SINE, HT_LSINE, HT_PHASE, HT_QUDRA, OBV = \
                self.array_tick[self.indexn, -14:]

        종목명, 종목코드, 데이터길이, 시분초 = self.name, self.code, self.tick_count, int(str(self.index)[8:])
        현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 거래대금증감, 전일비, 회전율, 전일동시간비, 시가총액, 라운드피겨위5호가이내, \
            초당매수수량, 초당매도수량, VI해제시간, VI가격, VI호가단위, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량, \
            매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, \
            매도수5호가잔량합, 관심종목 = self.array_tick[self.indexn, 1:45]
        호가단위 = GetHogaunit(self.dict_kd[종목코드] if 종목코드 in self.dict_kd.keys() else True, 현재가, self.index)
        VI해제시간, VI아래5호가 = strp_time('%Y%m%d%H%M%S', str(int(VI해제시간))), GetUvilower5(VI가격, VI호가단위, self.index)
        bhogainfo = ((매도호가1, 매도잔량1), (매도호가2, 매도잔량2), (매도호가3, 매도잔량3), (매도호가4, 매도잔량4), (매도호가5, 매도잔량5))
        shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
        self.bhogainfo = bhogainfo[:self.dict_set['주식매수시장가잔량범위']]
        self.shogainfo = shogainfo[:self.dict_set['주식매도시장가잔량범위']]

        if self.opti_turn == 1:
            vars_turns = range(len(self.vars_list))
            for vars_turn in vars_turns:
                len_vars_list = len(self.vars_list[vars_turn][0])
                if len_vars_list < 2:
                    continue
                self.vars = [var[1] for var in self.vars_list]
                if vars_turn != 0 and self.tick_count < self.vars[0]:
                    break

                vars_keys = range(len_vars_list)
                for vars_key in vars_keys:
                    self.vars[vars_turn] = self.vars_list[vars_turn][0][vars_key]
                    if self.tick_count < self.vars[0]:
                        continue

                    매수, 매도 = True, False
                    if not self.trade_info[vars_turn][vars_key]['보유중']:
                        if not 관심종목: continue
                        self.SetBuyCount(vars_turn, vars_key, 현재가, 고가, 저가, 등락율각도(30), 당일거래대금각도(30), 전일비, 회전율, 전일동시간비)
                        exec(self.buystg)
                    else:
                        수익률, 최고수익률, 최저수익률, 보유시간, 매수틱번호 = self.SetSellCount(vars_turn, vars_key, 현재가, now())
                        exec(self.sellstg)

        elif self.opti_turn == 3:
            vars_turns = range(50 if self.back_type == 'GA최적화' else 1)
            vars_keys  = range(20)
            for vars_turn in vars_turns:
                for vars_key in vars_keys:
                    index = vars_turn * 20 + vars_key
                    if self.back_type != '조건최적화':
                        self.vars = self.vars_lists[index]
                        if self.tick_count < self.vars[0]:
                            break
                    elif self.tick_count < self.avgtime:
                        break

                    매수, 매도 = True, False
                    if not self.trade_info[vars_turn][vars_key]['보유중']:
                        if not 관심종목: continue
                        self.SetBuyCount(vars_turn, vars_key, 현재가, 고가, 저가, 등락율각도(30), 당일거래대금각도(30), 전일비, 회전율, 전일동시간비)
                        if self.back_type != '조건최적화':
                            exec(self.buystg)
                        else:
                            exec(self.dict_buystg[index])
                    else:
                        수익률, 최고수익률, 최저수익률, 보유시간, 매수틱번호 = self.SetSellCount(vars_turn, vars_key, 현재가, now())
                        if self.back_type != '조건최적화':
                            exec(self.sellstg)
                        else:
                            exec(self.dict_sellstg[index])

        else:
            vars_turn, vars_key = 0, 0
            if self.back_type in ('최적화', '전진분석'):
                if self.tick_count < self.vars[0]:
                    return
            else:
                if self.tick_count < self.avgtime:
                    return
                if (self.pattern or self.pattern_test) and self.tick_count < self.dict_pattern['인식구간']:
                    return

            매수, 매도 = True, False
            if not self.trade_info[vars_turn][vars_key]['보유중']:
                if not 관심종목: return
                self.SetBuyCount(vars_turn, vars_key, 현재가, 고가, 저가, 등락율각도(30), 당일거래대금각도(30), 전일비, 회전율, 전일동시간비)
                exec(self.buystg)
            else:
                수익률, 최고수익률, 최저수익률, 보유시간, 매수틱번호 = self.SetSellCount(vars_turn, vars_key, 현재가, now())
                exec(self.sellstg)

    def SetBuyCount(self, vars_turn, vars_key, 현재가, 고가, 저가, 등락율각도, 당일거래대금각도, 전일비, 회전율, 전일동시간비):
        if self.dict_set['주식비중조절'][0] == 0:
            betting = self.betting
        else:
            if self.dict_set['주식비중조절'][0] == 1:
                비중조절기준 = round((고가 / 저가 - 1) * 100, 2)
            elif self.dict_set['주식비중조절'][0] == 2:
                비중조절기준 = 등락율각도
            elif self.dict_set['주식비중조절'][0] == 3:
                비중조절기준 = 당일거래대금각도
            elif self.dict_set['주식비중조절'][0] == 4:
                비중조절기준 = 전일비
            elif self.dict_set['주식비중조절'][0] == 5:
                비중조절기준 = 회전율
            else:
                비중조절기준 = 전일동시간비

            if 비중조절기준 < self.dict_set['주식비중조절'][1]:
                betting = self.betting * self.dict_set['주식비중조절'][5]
            elif 비중조절기준 < self.dict_set['주식비중조절'][2]:
                betting = self.betting * self.dict_set['주식비중조절'][6]
            elif 비중조절기준 < self.dict_set['주식비중조절'][3]:
                betting = self.betting * self.dict_set['주식비중조절'][7]
            elif 비중조절기준 < self.dict_set['주식비중조절'][4]:
                betting = self.betting * self.dict_set['주식비중조절'][8]
            else:
                betting = self.betting * self.dict_set['주식비중조절'][9]

        self.trade_info[vars_turn][vars_key]['주문수량'] = int(betting / 현재가)

    def SetSellCount(self, vars_turn, vars_key, 현재가, now_time):
        _, 매수가, _, _, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간 = \
            self.trade_info[vars_turn][vars_key].values()
        _, _, 수익률 = GetKiwoomPgSgSp(보유수량 * 매수가, 보유수량 * 현재가)
        if 수익률 > 최고수익률:
            self.trade_info[vars_turn][vars_key]['최고수익률'] = 최고수익률 = 수익률
        elif 수익률 < 최저수익률:
            self.trade_info[vars_turn][vars_key]['최저수익률'] = 최저수익률 = 수익률
        보유시간 = (now_time - 매수시간).total_seconds()
        self.indexb = 매수틱번호
        self.trade_info[vars_turn][vars_key]['주문수량'] = 보유수량
        return 수익률, 최고수익률, 최저수익률, 보유시간, 매수틱번호

    def Buy(self, vars_turn, vars_key):
        if self.back_type == '백테스트':
            if self.pattern:
                self.PatternModeling('매수')
            elif self.pattern_test:
                pattern = self.GetPattern('매수')
                if pattern not in self.pattern_buy:
                    return

        매수금액 = 0
        주문수량 = 미체결수량 = self.trade_info[vars_turn][vars_key]['주문수량']
        if 주문수량 > 0:
            for 매도호가, 매도잔량 in self.bhogainfo:
                if 미체결수량 - 매도잔량 <= 0:
                    매수금액 += 매도호가 * 미체결수량
                    미체결수량 -= 매도잔량
                    break
                else:
                    매수금액 += 매도호가 * 매도잔량
                    미체결수량 -= 매도잔량
            if 미체결수량 <= 0:
                self.trade_info[vars_turn][vars_key] = {
                    '보유중': 1,
                    '매수가': int(round(매수금액 / 주문수량)),
                    '매도가': 0,
                    '주문수량': 0,
                    '보유수량': 주문수량,
                    '최고수익률': 0.,
                    '최저수익률': 0.,
                    '매수틱번호': self.indexn,
                    '매수시간': strp_time('%Y%m%d%H%M%S', str(self.index))
                }

    def Sell(self, vars_turn, vars_key, sell_cond):
        if self.back_type == '백테스트':
            if self.pattern:
                self.PatternModeling('매도')
            elif self.pattern_test:
                pattern = self.GetPattern('매도')
                if pattern not in self.pattern_sell:
                    return

        매도금액 = 0
        주문수량 = 미체결수량 = self.trade_info[vars_turn][vars_key]['주문수량']
        for 매수호가, 매수잔량 in self.shogainfo:
            if 미체결수량 - 매수잔량 <= 0:
                매도금액 += 매수호가 * 미체결수량
                미체결수량 -= 매수잔량
                break
            else:
                매도금액 += 매수호가 * 매수잔량
                미체결수량 -= 매수잔량
        if 미체결수량 <= 0:
            self.trade_info[vars_turn][vars_key]['매도가'] = int(round(매도금액 / 주문수량))
            self.sell_cond = sell_cond
            self.CalculationEyun(vars_turn, vars_key)

    def LastSell(self):
        매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5 = \
            self.array_tick[self.indexn, 23:43]
        shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
        shogainfo = shogainfo[:self.dict_set['주식매도시장가잔량범위']]

        for vars_turn in list(self.trade_info.keys()):
            for vars_key in list(self.trade_info[vars_turn].keys()):
                if self.trade_info[vars_turn][vars_key]['보유중']:
                    매도금액 = 0
                    보유수량 = 미체결수량 = self.trade_info[vars_turn][vars_key]['보유수량']
                    for 매수호가, 매수잔량 in shogainfo:
                        if 미체결수량 - 매수잔량 <= 0:
                            매도금액 += 매수호가 * 미체결수량
                            미체결수량 -= 매수잔량
                            break
                        else:
                            매도금액 += 매수호가 * 매수잔량
                            미체결수량 -= 매수잔량
                    if 미체결수량 <= 0:
                        self.trade_info[vars_turn][vars_key]['매도가'] = int(round(매도금액 / 보유수량))
                    elif 매도금액 == 0:
                        self.trade_info[vars_turn][vars_key]['매도가'] = self.array_tick[self.indexn, 1]
                    else:
                        self.trade_info[vars_turn][vars_key]['매도가'] = int(round(매도금액 / (보유수량 - 미체결수량)))
                    self.trade_info[vars_turn][vars_key]['주문수량'] = 보유수량
                    self.sell_cond = 0
                    self.CalculationEyun(vars_turn, vars_key)

    def CalculationEyun(self, vars_turn, vars_key):
        """
        보유중, 매수가, 매도가, 주문수량, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간 = self.trade_info[vars_turn][vars_key].values()
        """
        if not self.pattern:
            _, bp, sp, oc, _, _, _, bi, bdt = self.trade_info[vars_turn][vars_key].values()
            sgtg = int(self.array_tick[self.indexn, 12])
            ht = int((strp_time('%Y%m%d%H%M%S', str(self.index)) - bdt).total_seconds())
            bt, st, bg = int(self.array_tick[bi, 0]), self.index, oc * bp
            sg, pg, pp = GetKiwoomPgSgSp(bg, oc * sp)
            sc = self.dict_sconds[self.sell_cond] if self.back_type != '조건최적화' else self.dict_sconds[vars_key][self.sell_cond]
            abt, bcx = '', True
            data = ['백테결과', self.name, sgtg, bt, st, ht, bp, sp, bg, sg, pp, pg, sc, abt, bcx, vars_turn, vars_key]
            self.bstq_list[vars_key if self.opti_turn in (1, 3) else (self.sell_count % 5)].put(data)
            self.sell_count += 1
        self.trade_info[vars_turn][vars_key] = GetTradeInfo(1)

    def PatternModeling(self, gubun):
        if self.tick_count > self.dict_pattern['인식구간']:
            last_area_index = self.indexn + self.dict_pattern['조건구간']
            if last_area_index <= self.last and str(self.index)[:8] == str(self.array_tick[last_area_index, 0])[:8]:
                self.PatternFind(gubun)

    def PatternFind(self, gubun):
        curr_price = self.array_tick[self.indexn, 1]
        high_price = self.array_tick[self.indexn + 1:self.indexn + 1 + self.dict_pattern['조건구간'], 1].max()
        low_price  = self.array_tick[self.indexn + 1:self.indexn + 1 + self.dict_pattern['조건구간'], 1].min()
        high_price_per = round((high_price / curr_price - 1) * 100, 2)
        low_price_per  = round((low_price / curr_price - 1) * 100, 2)
        if gubun == '매수':
            if self.dict_pattern['매수조건1'] and high_price_per >= self.dict_pattern['매수조건2']:
                pattern = self.GetPattern('매수')
                if pattern not in self.pattern_buy:
                    self.pattern_buy.append(pattern)
                    self.wq.put((ui_num['S백테스트'], f'매수 패턴 추가 : {pattern}'))
            elif self.dict_pattern['매수조건3'] and curr_price <= low_price:
                pattern = self.GetPattern('매수')
                if pattern not in self.pattern_buy:
                    self.pattern_buy.append(pattern)
                    self.wq.put((ui_num['S백테스트'], f'매수 패턴 추가 : {pattern}'))
        else:
            if self.dict_pattern['매도조건1'] and low_price_per <= -self.dict_pattern['매도조건2']:
                pattern = self.GetPattern('매도')
                if pattern not in self.pattern_sell:
                    self.pattern_sell.append(pattern)
                    self.wq.put((ui_num['S백테스트'], f'매도 패턴 추가 : {pattern}'))
            elif self.dict_pattern['매도조건3'] and curr_price >= high_price:
                pattern = self.GetPattern('매도')
                if pattern not in self.pattern_sell:
                    self.pattern_sell.append(pattern)
                    self.wq.put((ui_num['S백테스트'], f'매도 패턴 추가 : {pattern}'))

    def GetPattern(self, gubun):
        """
        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 거래대금증감, 전일비, 회전율, 전일동시간비, 시가총액, 라운드피겨위5호가이내,
           0      1     2    3    4     5         6         7         8        9      10       11        12           13
        초당매수수량, 초당매도수량, VI해제시간, VI가격, VI호가단위, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량,
            14         15          16      17       18         19            20            21        22
        매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5,
           23       24       25        26       27        28       29        30       31        32
        매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합,
           33       34       35        36       37        38       39        40       41       42          43
        """
        arry_tick = self.array_tick[self.indexn + 1 - self.dict_pattern['인식구간']:self.indexn + 1, :]
        pattern = None
        for factor, unit in self.dict_pattern_buy.items() if gubun == '매수' else self.dict_pattern_sell.items():
            pattern_ = None
            if factor == '등락율':
                pattern_ = arry_tick[:, 5]
            elif factor == '당일거래대금':
                pattern_ = arry_tick[:, 6]
            elif factor == '체결강도':
                pattern_ = arry_tick[:, 7]
            elif factor == '초당매수금액':
                bids     = arry_tick[:, 14]
                price    = arry_tick[:, 1]
                pattern_ = bids * price
            elif factor == '초당매도금액':
                asks     = arry_tick[:, 15]
                price    = arry_tick[:, 1]
                pattern_ = asks * price
            elif factor == '순매수금액':
                bids     = arry_tick[:, 14]
                asks     = arry_tick[:, 15]
                price    = arry_tick[:, 1]
                pattern_ = (bids - asks) * price
            elif factor == '초당거래대금':
                pattern_ = arry_tick[:, 19]
            elif factor == '고저평균대비등락율':
                pattern_ = arry_tick[:, 20]
            elif factor == '매도1잔량금액':
                asks1    = arry_tick[:, 37]
                price    = arry_tick[:, 27]
                pattern_ = asks1 * price
            elif factor == '매수1잔량금액':
                bids1    = arry_tick[:, 38]
                price    = arry_tick[:, 28]
                pattern_ = bids1 * price
            elif factor == '매도총잔량금액':
                tasks    = arry_tick[:, 21]
                price    = arry_tick[:, 1]
                pattern_ = tasks * price
            elif factor == '매수총잔량금액':
                tbids    = arry_tick[:, 22]
                price    = arry_tick[:, 1]
                pattern_ = tbids * price
            elif factor == '매도수5호가총금액':
                t5ab     = arry_tick[:, 43]
                price    = arry_tick[:, 1]
                pattern_ = t5ab * price
            pattern_ = pattern_ * unit
            pattern_ = pattern_.astype(int)
            if pattern is None:
                pattern = pattern_
            else:
                pattern = np.r_[pattern, pattern_]
        return pattern.tolist()
