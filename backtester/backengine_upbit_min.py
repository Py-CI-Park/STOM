import math
from talib import stream
from backtester.back_static import GetIndicator
from backtester.backengine_upbit_tick import BackEngineUpbitTick
from utility.setting import BACK_TEMP
# noinspection PyUnresolvedReferences
from utility.static import strp_time, timedelta_sec, pickle_read, GetUvilower5


# noinspection PyUnusedLocal
class BackEngineUpbitMin(BackEngineUpbitTick):
    def SetArrayTick(self, code, same_days, same_time):
        if not self.dict_set['백테일괄로딩']:
            self.dict_arry = {code: pickle_read(f'{BACK_TEMP}/{self.gubun}_{code}_tick')}

        if same_days and same_time:
            self.arry_data = self.dict_arry[code]
        elif same_time:
            self.arry_data = self.dict_arry[code][(self.dict_arry[code][:, 0] >= self.startday * 10000) &
                                                  (self.dict_arry[code][:, 0] <= self.endday * 10000 + 2400)]
        elif same_days:
            self.arry_data = self.dict_arry[code][(self.dict_arry[code][:, 0] % 10000 >= self.starttime) &
                                                  (self.dict_arry[code][:, 0] % 10000 <= self.endtime)]
        else:
            self.arry_data = self.dict_arry[code][(self.dict_arry[code][:, 0] >= self.startday * 10000) &
                                                  (self.dict_arry[code][:, 0] <= self.endday * 10000 + 2400) &
                                                  (self.dict_arry[code][:, 0] % 10000 >= self.starttime) &
                                                  (self.dict_arry[code][:, 0] % 10000 <= self.endtime)]

    def Strategy(self):
        def now_utc():
            return strp_time('%Y%m%d%H%M', str(self.index))

        def Parameter_Previous(aindex, pre):
            if pre < 데이터길이:
                pindex = (self.indexn - pre) if pre != -1 else self.indexb
                return self.arry_data[pindex, aindex]
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

        def 분당매수수량N(pre):
            return Parameter_Previous(8, pre)

        def 분당매도수량N(pre):
            return Parameter_Previous(9, pre)

        def 분봉시가N(pre):
            return Parameter_Previous(10, pre)

        def 분봉고가N(pre):
            return Parameter_Previous(11, pre)

        def 분봉저가N(pre):
            return Parameter_Previous(12, pre)

        def 분당거래대금N(pre):
            return Parameter_Previous(13, pre)

        def 고저평균대비등락율N(pre):
            return Parameter_Previous(14, pre)

        def 매도총잔량N(pre):
            return Parameter_Previous(15, pre)

        def 매수총잔량N(pre):
            return Parameter_Previous(16, pre)

        def 매도호가5N(pre):
            return Parameter_Previous(17, pre)

        def 매도호가4N(pre):
            return Parameter_Previous(18, pre)

        def 매도호가3N(pre):
            return Parameter_Previous(19, pre)

        def 매도호가2N(pre):
            return Parameter_Previous(20, pre)

        def 매도호가1N(pre):
            return Parameter_Previous(21, pre)

        def 매수호가1N(pre):
            return Parameter_Previous(22, pre)

        def 매수호가2N(pre):
            return Parameter_Previous(23, pre)

        def 매수호가3N(pre):
            return Parameter_Previous(24, pre)

        def 매수호가4N(pre):
            return Parameter_Previous(25, pre)

        def 매수호가5N(pre):
            return Parameter_Previous(26, pre)

        def 매도잔량5N(pre):
            return Parameter_Previous(27, pre)

        def 매도잔량4N(pre):
            return Parameter_Previous(28, pre)

        def 매도잔량3N(pre):
            return Parameter_Previous(29, pre)

        def 매도잔량2N(pre):
            return Parameter_Previous(30, pre)

        def 매도잔량1N(pre):
            return Parameter_Previous(31, pre)

        def 매수잔량1N(pre):
            return Parameter_Previous(32, pre)

        def 매수잔량2N(pre):
            return Parameter_Previous(33, pre)

        def 매수잔량3N(pre):
            return Parameter_Previous(34, pre)

        def 매수잔량4N(pre):
            return Parameter_Previous(35, pre)

        def 매수잔량5N(pre):
            return Parameter_Previous(36, pre)

        def 매도수5호가잔량합N(pre):
            return Parameter_Previous(37, pre)

        def 관심종목N(pre):
            return Parameter_Previous(38, pre)

        def 이동평균(tick, pre=0):
            if tick == 5:
                return Parameter_Previous(39, pre)
            elif tick == 10:
                return Parameter_Previous(40, pre)
            elif tick == 20:
                return Parameter_Previous(41, pre)
            elif tick == 60:
                return Parameter_Previous(42, pre)
            elif tick == 120:
                return Parameter_Previous(43, pre)
            else:
                if tick + pre <= 데이터길이:
                    sindex = (self.indexn + 1 - pre - tick) if pre != -1  else self.indexb + 1 - tick
                    eindex = (self.indexn + 1 - pre) if pre != -1  else self.indexb + 1
                    return round(self.arry_data[sindex:eindex, 1].mean(), 3)
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
                        return self.arry_data[sindex:eindex, vindex].max()
                    elif gubun_ == 'min':
                        return self.arry_data[sindex:eindex, vindex].min()
                    elif gubun_ == 'sum':
                        return self.arry_data[sindex:eindex, vindex].sum()
                    else:
                        return self.arry_data[sindex:eindex, vindex].mean()
                return 0

        def 최고현재가(tick, pre=0):
            return Parameter_Area(44, 1, tick, pre, 'max')

        def 최저현재가(tick, pre=0):
            return Parameter_Area(45, 1, tick, pre, 'min')

        def 최고분봉고가(tick, pre=0):
            return Parameter_Area(46, 11, tick, pre, 'max')

        def 최저분봉저가(tick, pre=0):
            return Parameter_Area(47, 12, tick, pre, 'min')

        def 체결강도평균(tick, pre=0):
            return round(Parameter_Area(48, 7, tick, pre, 'mean'), 3)

        def 최고체결강도(tick, pre=0):
            return Parameter_Area(49, 7, tick, pre, 'max')

        def 최저체결강도(tick, pre=0):
            return Parameter_Area(50, 7, tick, pre, 'min')

        def 최고분당매수수량(tick, pre=0):
            return Parameter_Area(51, 8, tick, pre, 'max')

        def 최고분당매도수량(tick, pre=0):
            return Parameter_Area(52, 9, tick, pre, 'max')

        def 누적분당매수수량(tick, pre=0):
            return Parameter_Area(53, 8, tick, pre, 'sum')

        def 누적분당매도수량(tick, pre=0):
            return Parameter_Area(54, 9, tick, pre, 'sum')

        def 분당거래대금평균(tick, pre=0):
            return int(Parameter_Area(55, 13, tick, pre, 'mean'))

        def Parameter_Dgree(aindex, vindex, tick, pre, cf):
            if tick in self.avg_list:
                return Parameter_Previous(GetArrayIndex(aindex), pre)
            else:
                if tick + pre <= 데이터길이:
                    sindex = (self.indexn - pre - tick + 1) if pre != -1  else self.indexb - tick + 1
                    eindex = (self.indexn - pre) if pre != -1  else self.indexb
                    dmp_gap = self.arry_data[eindex, vindex] - self.arry_data[sindex, vindex]
                    return round(math.atan2(dmp_gap * cf, tick) / (2 * math.pi) * 360, 2)
                return 0

        def 등락율각도(tick, pre=0):
            return Parameter_Dgree(56, 5, tick, pre, 10)

        def 당일거래대금각도(tick, pre=0):
            return Parameter_Dgree(57, 6, tick, pre, 0.00000001)

        def 경과틱수(조건명):
            if 종목코드 in self.dict_cond_indexn.keys() and \
                    조건명 in self.dict_cond_indexn[종목코드].keys() and self.dict_cond_indexn[종목코드][조건명] != 0:
                return self.indexn - self.dict_cond_indexn[종목코드][조건명]
            return 0

        def AD_N(pre):
            try:    AD_ = stream.AD(mh[:-pre], ml[:-pre], mc[:-pre], mv[:-pre])
            except: AD_ = 0
            return AD_

        def ADOSC_N(pre):
            try:    ADOSC_ = stream.ADOSC(mh[:-pre], ml[:-pre], mc[:-pre], mv[:-pre], fastperiod=k[0], slowperiod=k[1])
            except: ADOSC_ = 0
            return ADOSC_

        def ADXR_N(pre):
            try:    ADXR_ = stream.ADXR(mh[:-pre], ml[:-pre], mc[:-pre], timeperiod=k[2])
            except: ADXR_ = 0
            return ADXR_

        def APO_N(pre):
            try:    APO_ = stream.APO(mc[:-pre], fastperiod=k[3], slowperiod=k[4], matype=k[5])
            except: APO_ = 0
            return APO_

        def AROOND_N(pre):
            try:    AROOND_, AROONU_ = stream.AROON(mh[:-pre], ml[:-pre], timeperiod=k[6])
            except: AROOND_, AROONU_ = 0, 0
            return AROOND_

        def AROONU_N(pre):
            try:    AROOND_, AROONU_ = stream.AROON(mh[:-pre], ml[:-pre], timeperiod=k[3])
            except: AROOND_, AROONU_ = 0, 0
            return AROONU_

        def ATR_N(pre):
            try:    ATR_ = stream.ATR(mh[:-pre], ml[:-pre], mc[:-pre], timeperiod=k[7])
            except: ATR_ = 0
            return ATR_

        def BBU_N(pre):
            try:    BBU_, BBM_, BBL_ = stream.BBANDS(mc[:-pre], timeperiod=k[8], nbdevup=k[9], nbdevdn=k[10], matype=k[11])
            except: BBU_, BBM_, BBL_ = 0, 0, 0
            return BBU_

        def BBM_N(pre):
            try:    BBU_, BBM_, BBL_ = stream.BBANDS(mc[:-pre], timeperiod=k[8], nbdevup=k[9], nbdevdn=k[10], matype=k[11])
            except: BBU_, BBM_, BBL_ = 0, 0, 0
            return BBM_

        def BBL_N(pre):
            try:    BBU_, BBM_, BBL_ = stream.BBANDS(mc[:-pre], timeperiod=k[8], nbdevup=k[9], nbdevdn=k[10], matype=k[11])
            except: BBU_, BBM_, BBL_ = 0, 0, 0
            return BBL_

        def CCI_N(pre):
            try:    CCI_ = stream.CCI(mh[:-pre], ml[:-pre], mc[:-pre], timeperiod=k[12])
            except: CCI_ = 0
            return CCI_

        def DIM_N(pre):
            try:    DIM_ = stream.MINUS_DI(mh[:-pre], ml[:-pre], mc[:-pre], timeperiod=k[13])
            except: DIM_ = 0, 0
            return DIM_

        def DIP_N(pre):
            try:    DIP_ = stream.PLUS_DI(mh[:-pre], ml[:-pre], mc[:-pre], timeperiod=k[13])
            except: DIP_ = 0
            return DIP_

        def MACD_N(pre):
            try:    MACD_, MACDS_, MACDH_ = stream.MACD(mc[:-pre], fastperiod=k[14], slowperiod=k[15], signalperiod=k[16])
            except: MACD_, MACDS_, MACDH_ = 0, 0, 0
            return MACD_

        def MACDS_N(pre):
            try:    MACD_, MACDS_, MACDH_ = stream.MACD(mc[:-pre], fastperiod=k[14], slowperiod=k[15], signalperiod=k[16])
            except: MACD_, MACDS_, MACDH_ = 0, 0, 0
            return MACDS_

        def MACDH_N(pre):
            try:    MACD_, MACDS_, MACDH_ = stream.MACD(mc[:-pre], fastperiod=k[14], slowperiod=k[15], signalperiod=k[16])
            except: MACD_, MACDS_, MACDH_ = 0, 0, 0
            return MACDH_

        def MFI_N(pre):
            try:    MFI_ = stream.MFI(mh[:-pre], ml[:-pre], mc[:-pre], mv[:-pre], timeperiod=k[17])
            except: MFI_ = 0
            return MFI_

        def MOM_N(pre):
            try:    MOM_ = stream.MOM(mc[:-pre], timeperiod=k[18])
            except: MOM_ = 0
            return MOM_

        def OBV_N(pre):
            try:    OBV_ = stream.OBV(mc[:-pre], mv)
            except: OBV_ = 0
            return OBV_

        def PPO_N(pre):
            try:    PPO_ = stream.PPO(mc[:-pre], fastperiod=k[19], slowperiod=k[20], matype=k[21])
            except: PPO_ = 0
            return PPO_

        def ROC_N(pre):
            try:    ROC_ = stream.ROC(mc[:-pre], timeperiod=k[22])
            except: ROC_ = 0
            return ROC_

        def RSI_N(pre):
            try:    RSI_ = stream.RSI(mc[:-pre], timeperiod=k[23])
            except: RSI_ = 0
            return RSI_

        def SAR_N(pre):
            try:    SAR_ = stream.SAR(mh[:-pre], ml[:-pre], acceleration=k[24], maximum=k[25])
            except: SAR_ = 0
            return SAR_

        def STOCHSK_N(pre):
            try:    STOCHSK_, STOCHSD_ = stream.STOCH(mh[:-pre], ml[:-pre], mc[:-pre], fastk_period=k[26], slowk_period=k[27], slowk_matype=k[28], slowd_period=k[29], slowd_matype=k[30])
            except: STOCHSK_, STOCHSD_ = 0, 0
            return STOCHSK_

        def STOCHSD_N(pre):
            try:    STOCHSK_, STOCHSD_ = stream.STOCH(mh[:-pre], ml[:-pre], mc[:-pre], fastk_period=k[26], slowk_period=k[27], slowk_matype=k[28], slowd_period=k[29], slowd_matype=k[30])
            except: STOCHSK_, STOCHSD_ = 0, 0
            return STOCHSD_

        def STOCHFK_N(pre):
            try:    STOCHFK_, STOCHFD_ = stream.STOCHF(mh[:-pre], ml[:-pre], mc[:-pre], fastk_period=k[31], fastd_period=k[32], fastd_matype=k[33])
            except: STOCHFK_, STOCHFD_ = 0, 0
            return STOCHFK_

        def STOCHFD_N(pre):
            try:    STOCHFK_, STOCHFD_ = stream.STOCHF(mh[:-pre], ml[:-pre], mc[:-pre], fastk_period=k[31], fastd_period=k[32], fastd_matype=k[33])
            except: STOCHFK_, STOCHFD_ = 0, 0
            return STOCHFD_

        def WILLR_N(pre):
            try:    WILLR_ = stream.WILLR(mh[:-pre], ml[:-pre], mc[:-pre], timeperiod=k[34])
            except: WILLR_ = 0
            return WILLR_

        종목명, 종목코드, 데이터길이, 시분초 = self.name, self.code, self.tick_count, int(str(self.index)[8:] + '00')
        현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, \
            분당매수수량, 분당매도수량, 분봉시가, 분봉고가, 분봉저가, 분당거래대금, \
            고저평균대비등락율, 매도총잔량, 매수총잔량, 매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, \
            매수호가3, 매수호가4, 매수호가5, 매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, \
            매수잔량4, 매수잔량5, 매도수5호가잔량합, 관심종목 = self.arry_data[self.indexn, 1:39]
        호가단위 = 매도호가2 - 매도호가1
        bhogainfo = ((매도호가1, 매도잔량1), (매도호가2, 매도잔량2), (매도호가3, 매도잔량3), (매도호가4, 매도잔량4), (매도호가5, 매도잔량5))
        shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
        self.bhogainfo = bhogainfo[:self.dict_set['코인매수시장가잔량범위']]
        self.shogainfo = shogainfo[:self.dict_set['코인매도시장가잔량범위']]

        if self.dict_condition:
            if 종목코드 not in self.dict_cond_indexn.keys():
                self.dict_cond_indexn[종목코드] = {}
            for k, v in self.dict_condition.items():
                exec(v)

        start, end = self.indexn+1-self.tick_count, self.indexn+1
        mc = self.arry_data[start:end, 1]
        mh = self.arry_data[start:end, 11]
        ml = self.arry_data[start:end, 12]
        mv = self.arry_data[start:end, 13]

        if self.opti_turn == 1:
            for vturn in self.trade_info.keys():
                self.vars = [var[1] for var in self.vars_list]
                if vturn != 0 and self.tick_count < self.vars[0]:
                    break

                for vkey in self.trade_info[vturn].keys():
                    self.vars[vturn] = self.vars_list[vturn][0][vkey]
                    if self.tick_count < self.vars[0]:
                        continue

                    if self.indistg is not None:
                        exec(self.indistg)
                    k = list(self.indicator.values())
                    AD, ADOSC, ADXR, APO, AROOND, AROONU, ATR, BBU, BBM, BBL, CCI, DIM, DIP, MACD, MACDS, MACDH, MFI, MOM, \
                        OBV, PPO, ROC, RSI, SAR, STOCHSK, STOCHSD, STOCHFK, STOCHFD, WILLR = GetIndicator(mc, mh, ml, mv, k)

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

                    if self.indistg is not None:
                        exec(self.indistg)
                    k = list(self.indicator.values())
                    AD, ADOSC, ADXR, APO, AROOND, AROONU, ATR, BBU, BBM, BBL, CCI, DIM, DIP, MACD, MACDS, MACDH, MFI, MOM, \
                        OBV, PPO, ROC, RSI, SAR, STOCHSK, STOCHSD, STOCHFK, STOCHFD, WILLR = GetIndicator(mc, mh, ml, mv, k)

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

            if self.indistg is not None:
                exec(self.indistg)
            k = list(self.indicator.values())
            AD, ADOSC, ADXR, APO, AROOND, AROONU, ATR, BBU, BBM, BBL, CCI, DIM, DIP, MACD, MACDS, MACDH, MFI, MOM, \
                OBV, PPO, ROC, RSI, SAR, STOCHSK, STOCHSD, STOCHFK, STOCHFD, WILLR = GetIndicator(mc, mh, ml, mv, k)

            매수, 매도 = True, False
            if not self.trade_info[vturn][vkey]['보유중']:
                if not 관심종목: return
                self.SetBuyCount(vturn, vkey, 현재가, 고가, 저가, 등락율각도(30), 당일거래대금각도(30))
                exec(self.buystg)
            else:
                수익률, 최고수익률, 최저수익률, 보유시간, 매수틱번호 = self.SetSellCount(vturn, vkey, 현재가, now_utc())
                exec(self.sellstg)
