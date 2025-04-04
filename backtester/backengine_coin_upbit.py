import gc
import math
import sqlite3
import datetime
import numpy as np
import pandas as pd
from traceback import print_exc
from multiprocessing import shared_memory
from utility.setting import DB_COIN_BACK, BACK_TEMP, ui_num, DICT_SET
# noinspection PyUnresolvedReferences
from utility.static import strp_time, timedelta_sec, pickle_read, pickle_write, GetUpbitPgSgSp, strf_time
from backtester.back_static import GetBuyStg, GetSellStg, GetBuyConds, GetSellConds, GetBackloadCodeQuery, AddAvgData, GetTradeInfo, AddTalib


# noinspection PyUnusedLocal
class CoinUpbitBackEngine:
    def __init__(self, gubun, wq, tq, bq, beq, bstq_list, lock, profile=False):
        gc.disable()
        self.gubun        = gubun
        self.wq           = wq
        self.tq           = tq
        self.bq           = bq
        self.beq          = beq
        self.bstq_list    = bstq_list
        self.lock         = lock
        self.profile      = profile
        self.dict_set     = DICT_SET

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
        self.array_tick   = None

        self.is_long      = None

        self.shm_list     = []
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
        self.sell_count   = 0
        self.sell_cond    = 0
        self.opti_turn    = 0

        self.total_ticks  = 0
        self.total_secds  = 0

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

        self.dict_condition    = {}
        self.dict_cond_indexn  = {}
        self.SetDictCondition()
        self.MainLoop()

    def SetDictCondition(self):
        if self.dict_set['코인경과틱수설정'] != '':
            def compile_condition(x):
                return compile(f'if {x}:\n    self.dict_cond_indexn[종목코드][k] = self.indexn', '<string>', 'exec')
            text_list  = self.dict_set['코인경과틱수설정'].split(';')
            half_cnt   = int(len(text_list) / 2)
            key_list   = text_list[:half_cnt]
            value_list = text_list[half_cnt:]
            value_list = [compile_condition(x) for x in value_list]
            self.dict_condition = dict(zip(key_list, value_list))

    def MainLoop(self):
        while True:
            data = self.beq.get()
            if '정보' in data[0]:
                if self.back_type == '최적화':
                    if data[0] == '백테정보':
                        self.betting   = data[1]
                        avg_list       = data[2]
                        self.startday  = data[3]
                        self.endday    = data[4]
                        self.starttime = data[5]
                        self.endtime   = data[6]
                        self.buystg    = GetBuyStg(data[7], self.gubun)
                        self.sellstg, self.dict_sconds = GetSellStg(data[8], self.gubun)
                        self.CheckAvglist(avg_list)
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop(1)
                    elif data[0] == '변수정보':
                        self.vars_list = data[1]
                        self.opti_turn = data[2]
                        self.vars      = [var[1] for var in self.vars_list]
                        self.InitDivid(0)
                        self.InitTradeInfo()
                        self.BackTest()
                elif self.back_type == '전진분석':
                    if data[0] == '백테정보':
                        self.betting   = data[1]
                        avg_list       = data[2]
                        self.starttime = data[3]
                        self.endtime   = data[4]
                        self.buystg    = GetBuyStg(data[5], self.gubun)
                        self.sellstg, self.dict_sconds = GetSellStg(data[6], self.gubun)
                        self.CheckAvglist(avg_list)
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop(1)
                    elif data[0] == '변수정보':
                        self.vars_list = data[1]
                        self.opti_turn = data[2]
                        self.vars      = [var[1] for var in self.vars_list]
                        self.startday  = data[3]
                        self.endday    = data[4]
                        if self.opti_turn == 1:
                            self.tick_calcul = False
                        self.InitDivid(0)
                        self.InitTradeInfo()
                        self.BackTest()
                elif self.back_type == 'GA최적화':
                    if data[0] == '백테정보':
                        self.betting   = data[1]
                        avg_list       = data[2]
                        self.startday  = data[3]
                        self.endday    = data[4]
                        self.starttime = data[5]
                        self.endtime   = data[6]
                        self.buystg    = GetBuyStg(data[7], self.gubun)
                        self.sellstg, self.dict_sconds = GetSellStg(data[8], self.gubun)
                        self.CheckAvglist(avg_list)
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop(1)
                        else:
                            self.InitDivid(0)
                            self.TotalTickCount()
                    elif data[0] == '변수정보':
                        self.vars_lists = data[1]
                        self.InitDivid(0)
                        self.InitTradeInfo()
                        self.BackTest()
                elif self.back_type == '조건최적화':
                    if data[0] == '백테정보':
                        self.betting   = data[1]
                        self.avgtime   = data[2]
                        self.startday  = data[3]
                        self.endday    = data[4]
                        self.starttime = data[5]
                        self.endtime   = data[6]
                        self.InitDivid(0)
                        self.TotalTickCount()
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
                        self.betting   = data[1]
                        self.avgtime   = data[2]
                        self.startday  = data[3]
                        self.endday    = data[4]
                        self.starttime = data[5]
                        self.endtime   = data[6]
                        self.buystg    = GetBuyStg(data[7], self.gubun)
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
                        self.betting   = data[1]
                        self.avgtime   = data[2]
                        self.startday  = data[3]
                        self.endday    = data[4]
                        self.starttime = data[5]
                        self.endtime   = data[6]
                        self.buystg    = GetBuyStg(data[7], self.gubun)
                        self.sellstg, self.dict_sconds = GetSellStg(data[8], self.gubun)
                        self.dict_pattern      = data[9]
                        self.dict_pattern_buy  = data[10]
                        self.dict_pattern_sell = data[11]
                        self.pattern_buy       = []
                        self.pattern_sell      = []
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
                        self.avgtime   = data[1]
                        self.startday  = data[2]
                        self.endday    = data[3]
                        self.starttime = data[4]
                        self.endtime   = data[5]
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
                self.SetDictCondition()
            elif data[0] == '데이터로딩':
                self.DataLoad(data)
            elif data[0] == '백테데이터':
                self.shm_list = data[1]

    def InitDivid(self, pattern):
        self.sell_count = 0
        if pattern == 0:
            self.pattern, self.pattern_test = False, False
        elif pattern == 1:
            self.pattern, self.pattern_test = True, False
        else:
            self.pattern = False
        if self.back_type == '백테스트':
            self.opti_turn = 2
        elif self.back_type in ('GA최적화', '조건최적화'):
            self.opti_turn = 3

    def InitTradeInfo(self):
        self.dict_cond_indexn = {}
        self.tick_count = 0
        v = GetTradeInfo(1)
        if self.opti_turn == 1:
            self.trade_info = {t: {k: v for k in range(len(x[0]))} for t, x in enumerate(self.vars_list) if len(x[0]) > 1}
        elif self.opti_turn == 3:
            self.trade_info = {t: {k: v for k in range(20)} for t in range(50 if self.back_type == 'GA최적화' else 1)}
        else:
            self.trade_info = {0: {0: v}}

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

                if len_df_tick > 0:
                    df_tick = AddAvgData(df_tick, 8, avg_list)
                    arry_tick = np.array(df_tick)
                    if self.dict_set['보조지표사용']:
                        arry_tick = AddTalib(arry_tick, self.dict_set['보조지표설정'], True)
                    if self.dict_set['백테일괄로딩']:
                        shm  = shared_memory.SharedMemory(create=True, size=arry_tick.nbytes)
                        shm_arry = np.ndarray(arry_tick.shape, dtype=arry_tick.dtype, buffer=shm.buf)
                        shm_arry[:] = arry_tick[:]
                        data = (shm, len_df_tick, code, shm.name, arry_tick.shape)
                    else:
                        name = f"{BACK_TEMP}/{self.gubun}_{code}_{strf_time('%f')}"
                        pickle_write(name, arry_tick)
                        data = (None, len_df_tick, code, name)
                    self.bq.put(data)
        elif divid_mode == '일자별 분류':
            gubun, startday, endday, starttime, endtime, day_list, avg_list, code_days, day_codes, _, _ = data
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
                    df_tick = AddAvgData(df_tick, 8, avg_list)
                    arry_tick = np.array(df_tick)
                    if self.dict_set['보조지표사용']:
                        arry_tick = AddTalib(arry_tick, self.dict_set['보조지표설정'], True)
                    if self.dict_set['백테일괄로딩']:
                        shm  = shared_memory.SharedMemory(create=True, size=arry_tick.nbytes)
                        shm_arry = np.ndarray(arry_tick.shape, dtype=arry_tick.dtype, buffer=shm.buf)
                        shm_arry[:] = arry_tick[:]
                        data = (shm, len_df_tick, code, shm.name, arry_tick.shape)
                    else:
                        name = f"{BACK_TEMP}/{self.gubun}_{code}_{strf_time('%f')}"
                        pickle_write(name, arry_tick)
                        data = (None, len_df_tick, code, name)
                    self.bq.put(data)
        else:
            gubun, startday, endday, starttime, endtime, day_list, avg_list, _, _, _, code = data
            df_tick, len_df_tick = None, 0
            try:
                df_tick = pd.read_sql(GetBackloadCodeQuery(code, day_list, starttime, endtime), con)
                len_df_tick = len(df_tick)
            except:
                pass
            if len_df_tick > 0:
                df_tick = AddAvgData(df_tick, 8, avg_list)
                arry_tick = np.array(df_tick)
                if self.dict_set['보조지표사용']:
                    arry_tick = AddTalib(arry_tick, self.dict_set['보조지표설정'], True)
                if self.dict_set['백테일괄로딩']:
                    shm  = shared_memory.SharedMemory(create=True, size=arry_tick.nbytes)
                    shm_arry = np.ndarray(arry_tick.shape, dtype=arry_tick.dtype, buffer=shm.buf)
                    shm_arry[:] = arry_tick[:]
                    data = (shm, len_df_tick, code, shm.name, arry_tick.shape)
                else:
                    name = f"{BACK_TEMP}/{self.gubun}_{code}_{strf_time('%f')}"
                    pickle_write(name, arry_tick)
                    data = (None, len_df_tick, code, name)
                self.bq.put(data)

        con.close()
        self.avg_list = avg_list
        self.startday_, self.endday_, self.starttime_, self.endtime_ = startday, endday, starttime, endtime
        self.bq.put('로딩완료')

    def CheckAvglist(self, avg_list):
        not_in_list = [x for x in avg_list if x not in self.avg_list]
        if len(not_in_list) > 0 and self.gubun == 0:
            self.wq.put((ui_num['C백테스트'], '백테엔진 구동 시 포함되지 않은 평균값 틱수를 사용하여 중지되었습니다.'))
            self.wq.put((ui_num['C백테스트'], '누락된 평균값 틱수를 추가하여 백테엔진을 재시작하십시오.'))
            self.BackStop(1)

    def BackStop(self, gubun):
        self.back_type = None
        if self.gubun == 0:
            if gubun:
                self.wq.put((ui_num['C백테스트'], '전략 코드 오류로 백테스트를 중지합니다.'))
            else:
                self.wq.put((ui_num['C백테스트'], '학습된 패턴 데이터가 없어 백테스트를 중지합니다.'))

    def SetArrayTick(self, same_days, same_time):
        self.lock.acquire()
        reslut     = False
        ticks      = 0
        exist_shm1 = shared_memory.SharedMemory(name='back_sequence')
        shm_index  = np.ndarray((2,), dtype=np.int32, buffer=exist_shm1.buf)
        exist_shm2 = None

        if shm_index[0] < shm_index[1]:
            if self.dict_set['백테일괄로딩']:
                self.code, name, shape = self.shm_list[shm_index[0]]
                exist_shm2 = shared_memory.SharedMemory(name=name)
                array_tick = np.ndarray(shape, dtype=np.float64, buffer=exist_shm2.buf)
            else:
                self.code, file_name = self.shm_list[shm_index[0]]
                array_tick = pickle_read(file_name)

            shm_index[0] += 1
            self.name = self.code

            if same_days and same_time:
                self.array_tick = array_tick
            elif same_time:
                self.array_tick = array_tick[(array_tick[:, 0] >= self.startday * 1000000) &
                                             (array_tick[:, 0] <= self.endday * 1000000 + 240000)]
            elif same_days:
                self.array_tick = array_tick[(array_tick[:, 0] % 1000000 >= self.starttime) &
                                             (array_tick[:, 0] % 1000000 <= self.endtime)]
            else:
                self.array_tick = array_tick[(array_tick[:, 0] >= self.startday * 1000000) &
                                             (array_tick[:, 0] <= self.endday * 1000000 + 240000) &
                                             (array_tick[:, 0] % 1000000 >= self.starttime) &
                                             (array_tick[:, 0] % 1000000 <= self.endtime)]
            reslut = True
            ticks  = len(self.array_tick)

        exist_shm1.close()
        self.lock.release()
        return reslut, ticks, exist_shm2

    def TotalTickCount(self):
        same_days   = self.startday_ == self.startday and self.endday_ == self.endday
        same_time   = self.starttime_ == self.starttime and self.endtime_ == self.endtime
        total_ticks = 0
        while True:
            result, ticks, exist_shm2 = self.SetArrayTick(same_days, same_time)
            if result:
                total_ticks += ticks
                if exist_shm2 is not None: exist_shm2.close()
            else:
                break
        self.tq.put(('전체틱수', int(total_ticks / 100)))

    def BackTest(self):
        if self.profile:
            import cProfile
            self.pr = cProfile.Profile()
            self.pr.enable()

        same_days = self.startday_ == self.startday and self.endday_ == self.endday
        same_time = self.starttime_ == self.starttime and self.endtime_ == self.endtime

        j = 0
        total_ticks = 0
        while True:
            result, ticks, exist_shm2 = self.SetArrayTick(same_days, same_time)
            if result:
                self.last = ticks - 1
                if ticks > 0:
                    for i, index in enumerate(self.array_tick[:, 0]):
                        self.index = int(index)
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

                        if self.opti_turn in (1, 3):
                            j += 1
                            if j % 100 == 0: self.tq.put('탐색완료')

                if self.opti_turn == 0: total_ticks += ticks
                if exist_shm2 is not None: exist_shm2.close()
                self.tq.put('백테완료')
            else:
                break

        if self.opti_turn == 0: self.tq.put(('전체틱수', int(total_ticks / 100)))
        if self.pattern: self.tq.put(('학습결과', self.pattern_buy, self.pattern_sell))
        if self.profile: self.pr.print_stats(sort='cumulative')

    def Strategy(self):
        def now_utc():
            return strp_time('%Y%m%d%H%M%S', str(self.index))

        def Parameter_Previous(aindex, pre):
            if pre < 데이터길이:
                pindex = (self.indexn - pre) if pre != -1 else self.indexb
                return self.array_tick[pindex, aindex]
            return 0

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
                if tick + pre <= 데이터길이:
                    sindex = (self.indexn + 1 - pre - tick) if pre != -1  else self.indexb + 1 - tick
                    eindex = (self.indexn + 1 - pre) if pre != -1  else self.indexb + 1
                    return round(self.array_tick[sindex:eindex, 1].mean(), 8)
                return 0

        def GetArrayIndex(aindex):
            return aindex + 12 * self.avg_list.index(self.avgtime if self.back_type in ('백테스트', '조건최적화', '백파인더') else self.vars[0])

        def Parameter_Area(aindex, vindex, tick, pre, gubun_):
            if tick in self.avg_list:
                return Parameter_Previous(GetArrayIndex(aindex), pre)
            else:
                if tick + pre <= 데이터길이:
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
                return 0

        def 최고현재가(tick, pre=0):
            return Parameter_Area(40, 1, tick, pre, 'max')

        def 최저현재가(tick, pre=0):
            return Parameter_Area(41, 1, tick, pre, 'min')

        def 체결강도평균(tick, pre=0):
            return round(Parameter_Area(42, 7, tick, pre, 'mean'), 3)

        def 최고체결강도(tick, pre=0):
            return Parameter_Area(43, 7, tick, pre, 'max')

        def 최저체결강도(tick, pre=0):
            return Parameter_Area(44, 7, tick, pre, 'min')

        def 최고초당매수수량(tick, pre=0):
            return Parameter_Area(45, 8, tick, pre, 'max')

        def 최고초당매도수량(tick, pre=0):
            return Parameter_Area(46, 9, tick, pre, 'max')

        def 누적초당매수수량(tick, pre=0):
            return Parameter_Area(47, 8, tick, pre, 'sum')

        def 누적초당매도수량(tick, pre=0):
            return Parameter_Area(48, 9, tick, pre, 'sum')

        def 초당거래대금평균(tick, pre=0):
            return int(Parameter_Area(49, 10, tick, pre, 'mean'))

        def Parameter_Dgree(aindex, vindex, tick, pre, cf):
            if tick in self.avg_list:
                return Parameter_Previous(GetArrayIndex(aindex), pre)
            else:
                if tick + pre <= 데이터길이:
                    sindex = (self.indexn - pre - tick + 1) if pre != -1  else self.indexb - tick + 1
                    eindex = (self.indexn - pre) if pre != -1  else self.indexb
                    dmp_gap = self.array_tick[eindex, vindex] - self.array_tick[sindex, vindex]
                    return round(math.atan2(dmp_gap * cf, tick) / (2 * math.pi) * 360, 2)
                return 0

        def 등락율각도(tick, pre=0):
            return Parameter_Dgree(50, 5, tick, pre, 10)

        def 당일거래대금각도(tick, pre=0):
            return Parameter_Dgree(51, 6, tick, pre, 0.00000001)

        def 경과틱수(조건명):
            if 조건명 in self.dict_cond_indexn[종목코드].keys() and self.dict_cond_indexn[종목코드][조건명] != 0:
                return self.indexn - self.dict_cond_indexn[종목코드][조건명]
            return 0

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

        현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 초당매수수량, 초당매도수량, 초당거래대금, 고저평균대비등락율, 매도총잔량, \
            매수총잔량, 매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합, \
            관심종목 = self.array_tick[self.indexn, 1:36]
        종목코드, 데이터길이, 시분초, 호가단위 = self.code, self.tick_count, int(str(self.index)[8:]), 매도호가2 - 매도호가1
        bhogainfo = ((매도호가1, 매도잔량1), (매도호가2, 매도잔량2), (매도호가3, 매도잔량3), (매도호가4, 매도잔량4), (매도호가5, 매도잔량5))
        shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
        self.bhogainfo = bhogainfo[:self.dict_set['코인매수시장가잔량범위']]
        self.shogainfo = shogainfo[:self.dict_set['코인매도시장가잔량범위']]

        if self.dict_condition:
            if 종목코드 not in self.dict_cond_indexn.keys():
                self.dict_cond_indexn[종목코드] = {}
            for k, v in self.dict_condition.items():
                exec(v)

        if self.opti_turn == 1:
            for vturn in self.trade_info.keys():
                self.vars = [var[1] for var in self.vars_list]
                if vturn != 0 and self.tick_count < self.vars[0]:
                    break

                for vkey in self.trade_info[vturn].keys():
                    self.vars[vturn] = self.vars_list[vturn][0][vkey]
                    if self.tick_count < self.vars[0]:
                        continue

                    매수, 매도 = True, False
                    if not self.trade_info[vturn][vkey]['보유중']:
                        if not 관심종목: continue
                        self.SetBuyCount(vturn, vkey, 현재가, 고가, 저가, 등락율각도(30), 당일거래대금각도(30))
                        exec(self.buystg)
                    else:
                        수익률, 최고수익률, 최저수익률, 보유시간, 매수틱번호 = self.SetSellCount(vturn, vkey, 현재가, now_utc())
                        exec(self.sellstg)

        elif self.opti_turn == 3:
            for vturn in self.trade_info.keys():
                for vkey in self.trade_info[vturn].keys():
                    index_ = vturn * 20 + vkey
                    if self.back_type != '조건최적화':
                        self.vars = self.vars_lists[index_]
                        if self.tick_count < self.vars[0]:
                            break
                    elif self.tick_count < self.avgtime:
                        break

                    매수, 매도 = True, False
                    if not self.trade_info[vturn][vkey]['보유중']:
                        if not 관심종목: continue
                        self.SetBuyCount(vturn, vkey, 현재가, 고가, 저가, 등락율각도(30), 당일거래대금각도(30))
                        if self.back_type != '조건최적화':
                            exec(self.buystg)
                        else:
                            exec(self.dict_buystg[index_])
                    else:
                        수익률, 최고수익률, 최저수익률, 보유시간, 매수틱번호 = self.SetSellCount(vturn, vkey, 현재가, now_utc())
                        if self.back_type != '조건최적화':
                            exec(self.sellstg)
                        else:
                            exec(self.dict_sellstg[index_])

        else:
            vturn, vkey = 0, 0
            if self.back_type in ('최적화', '전진분석'):
                if self.tick_count < self.vars[0]:
                    return
            else:
                if self.tick_count < self.avgtime:
                    return
                if (self.pattern or self.pattern_test) and self.tick_count < self.dict_pattern['인식구간']:
                    return

            매수, 매도 = True, False
            if not self.trade_info[vturn][vkey]['보유중']:
                if not 관심종목: return
                self.SetBuyCount(vturn, vkey, 현재가, 고가, 저가, 등락율각도(30), 당일거래대금각도(30))
                exec(self.buystg)
            else:
                수익률, 최고수익률, 최저수익률, 보유시간, 매수틱번호 = self.SetSellCount(vturn, vkey, 현재가, now_utc())
                exec(self.sellstg)

    def SetBuyCount(self, vturn, vkey, 현재가, 고가, 저가, 등락율각도, 당일거래대금각도):
        if self.dict_set['코인비중조절'][0] == 0:
            betting = self.betting
        else:
            if self.dict_set['코인비중조절'][0] == 1:
                비중조절기준 = round((고가 / 저가 - 1) * 100, 2)
            elif self.dict_set['코인비중조절'][0] == 2:
                비중조절기준 = 등락율각도
            else:
                비중조절기준 = 당일거래대금각도

            if 비중조절기준 < self.dict_set['코인비중조절'][1]:
                betting = self.betting * self.dict_set['코인비중조절'][5]
            elif 비중조절기준 < self.dict_set['코인비중조절'][2]:
                betting = self.betting * self.dict_set['코인비중조절'][6]
            elif 비중조절기준 < self.dict_set['코인비중조절'][3]:
                betting = self.betting * self.dict_set['코인비중조절'][7]
            elif 비중조절기준 < self.dict_set['코인비중조절'][4]:
                betting = self.betting * self.dict_set['코인비중조절'][8]
            else:
                betting = self.betting * self.dict_set['코인비중조절'][9]

        self.trade_info[vturn][vkey]['주문수량'] = round(betting / 현재가, 8)

    def SetSellCount(self, vturn, vkey, 현재가, now_time):
        _, 매수가, _, _, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간 = \
            self.trade_info[vturn][vkey].values()
        _, _, 수익률 = GetUpbitPgSgSp(보유수량 * 매수가, 보유수량 * 현재가)
        if 수익률 > 최고수익률:
            self.trade_info[vturn][vkey]['최고수익률'] = 최고수익률 = 수익률
        elif 수익률 < 최저수익률:
            self.trade_info[vturn][vkey]['최저수익률'] = 최저수익률 = 수익률
        보유시간 = (now_time - 매수시간).total_seconds()
        self.indexb = 매수틱번호
        self.trade_info[vturn][vkey]['주문수량'] = 보유수량
        return 수익률, 최고수익률, 최저수익률, 보유시간, 매수틱번호

    def Buy(self, vturn, vkey):
        if self.back_type == '백테스트':
            if self.pattern:
                self.PatternModeling('매수')
            elif self.pattern_test:
                pattern = self.GetPattern('매수')
                if pattern not in self.pattern_buy:
                    return

        매수금액 = 0
        주문수량 = 미체결수량 = self.trade_info[vturn][vkey]['주문수량']
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
                self.trade_info[vturn][vkey] = {
                    '보유중': 1,
                    '매수가': round(매수금액 / 주문수량, 4),
                    '매도가': 0,
                    '주문수량': 0,
                    '보유수량': 주문수량,
                    '최고수익률': 0.,
                    '최저수익률': 0.,
                    '매수틱번호': self.indexn,
                    '매수시간': strp_time('%Y%m%d%H%M%S', str(self.index))
                }

    def Sell(self, vturn, vkey, sell_cond):
        if self.back_type == '백테스트':
            if self.pattern:
                self.PatternModeling('매도')
            elif self.pattern_test:
                pattern = self.GetPattern('매도')
                if pattern not in self.pattern_sell:
                    return

        매도금액 = 0
        주문수량 = 미체결수량 = self.trade_info[vturn][vkey]['주문수량']
        for 매수호가, 매수잔량 in self.shogainfo:
            if 미체결수량 - 매수잔량 <= 0:
                매도금액 += 매수호가 * 미체결수량
                미체결수량 -= 매수잔량
                break
            else:
                매도금액 += 매수호가 * 매수잔량
                미체결수량 -= 매수잔량
        if 미체결수량 <= 0:
            self.trade_info[vturn][vkey]['매도가'] = round(매도금액 / 주문수량, 4)
            self.sell_cond = sell_cond
            self.CalculationEyun(vturn, vkey)

    def LastSell(self):
        매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5 = \
            self.array_tick[self.indexn, 14:34]
        shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
        shogainfo = shogainfo[:self.dict_set['코인매도시장가잔량범위']]

        for vturn in self.trade_info.keys():
            for vkey in self.trade_info[vturn].keys():
                if self.trade_info[vturn][vkey]['보유중']:
                    매도금액 = 0
                    보유수량 = 미체결수량 = self.trade_info[vturn][vkey]['보유수량']
                    for 매수호가, 매수잔량 in shogainfo:
                        if 미체결수량 - 매수잔량 <= 0:
                            매도금액 += 매수호가 * 미체결수량
                            미체결수량 -= 매수잔량
                            break
                        else:
                            매도금액 += 매수호가 * 매수잔량
                            미체결수량 -= 매수잔량
                    if 미체결수량 <= 0:
                        self.trade_info[vturn][vkey]['매도가'] = round(매도금액 / 보유수량, 4)
                    elif 매도금액 == 0:
                        self.trade_info[vturn][vkey]['매도가'] = self.array_tick[self.indexn, 1]
                    else:
                        self.trade_info[vturn][vkey]['매도가'] = round(매도금액 / (보유수량 - 미체결수량), 4)

                    self.trade_info[vturn][vkey]['주문수량'] = 보유수량
                    self.sell_cond = 0
                    self.CalculationEyun(vturn, vkey)

    def CalculationEyun(self, vturn, vkey):
        """
        보유중, 매수가, 매도가, 주문수량, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간 = self.trade_info[vturn][vkey].values()
        """
        if not self.pattern:
            _, bp, sp, oc, _, _, _, bi, bdt = self.trade_info[vturn][vkey].values()
            sgtg = 0
            ht = int((strp_time('%Y%m%d%H%M%S', str(self.index)) - bdt).total_seconds())
            bt, st, bg = int(self.array_tick[bi, 0]), self.index, oc * bp
            pg, sg, pp = GetUpbitPgSgSp(bg, oc * sp)
            sc = self.dict_sconds[self.sell_cond] if self.back_type != '조건최적화' else self.dict_sconds[vkey][self.sell_cond]
            abt, bcx = '', True
            data = ('백테결과', self.name, sgtg, bt, st, ht, bp, sp, bg, pg, pp, sg, sc, abt, bcx, vturn, vkey)
            self.bstq_list[vkey if self.opti_turn in (1, 3) else (self.sell_count % 5)].put(data)
            self.sell_count += 1
        self.trade_info[vturn][vkey] = GetTradeInfo(1)

    def PatternModeling(self, gubun):
        last_area_index = self.indexn + self.dict_pattern['조건구간']
        if last_area_index <= self.last and str(self.index)[:8] == str(self.array_tick[last_area_index, 0])[:8]:
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
        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 초당매수수량, 초당매도수량, 초당거래대금, 고저평균대비등락율,
           0      1     2    3     4     5        6         7         8           9          10            11
        매도총잔량, 매수총잔량, 매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5,
           12        13        14       15       16        17       18        19       20       21        22       23
        매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합,
           24        25       26       27        28       29        30       31       32        33         34
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
                bids     = arry_tick[:, 8]
                price    = arry_tick[:, 1]
                pattern_ = bids * price
            elif factor == '초당매도금액':
                asks     = arry_tick[:, 9]
                price    = arry_tick[:, 1]
                pattern_ = asks * price
            elif factor == '순매수금액':
                bids     = arry_tick[:, 8]
                asks     = arry_tick[:, 9]
                price    = arry_tick[:, 1]
                pattern_ = (bids - asks) * price
            elif factor == '초당거래대금':
                pattern_ = arry_tick[:, 10]
            elif factor == '고저평균대비등락율':
                pattern_ = arry_tick[:, 11]
            elif factor == '매도1잔량금액':
                asks1    = arry_tick[:, 28]
                price    = arry_tick[:, 18]
                pattern_ = asks1 * price
            elif factor == '매수1잔량금액':
                bids1    = arry_tick[:, 29]
                price    = arry_tick[:, 19]
                pattern_ = bids1 * price
            elif factor == '매도총잔량금액':
                tasks    = arry_tick[:, 12]
                price    = arry_tick[:, 1]
                pattern_ = tasks * price
            elif factor == '매수총잔량금액':
                tbids    = arry_tick[:, 13]
                price    = arry_tick[:, 1]
                pattern_ = tbids * price
            elif factor == '매도수5호가총금액':
                t5ab     = arry_tick[:, 34]
                price    = arry_tick[:, 1]
                pattern_ = t5ab * price
            pattern_ = pattern_ * unit
            pattern_ = pattern_.astype(int)
            if pattern is None:
                pattern = pattern_
            else:
                pattern = np.r_[pattern, pattern_]
        return pattern.tolist()
