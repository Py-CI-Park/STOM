import math
# noinspection PyUnresolvedReferences
import talib
# noinspection PyUnresolvedReferences
import numpy as np
from traceback import print_exc
from backtester.backengine_stock import StockBackEngine
from backtester.back_static import GetTradeInfo
from utility.setting import BACK_TEMP, dict_order_ratio
from utility.static import strp_time, timedelta_sec, roundfigure_upper, roundfigure_lower, pickle_read, GetKiwoomPgSgSp, GetUvilower5, GetHogaunit


# noinspection PyUnusedLocal
class StockBackEngine2(StockBackEngine):
    def InitTradeInfo(self):
        self.tick_count = 0
        v = GetTradeInfo(3)
        if self.opti_turn == 1:
            self.day_info = {vars_turn: {vars_key: v for vars_key in range(len(self.vars_list[vars_turn][0]))} for vars_turn in range(len(self.vars_list))}
        elif self.opti_turn == 3:
            self.day_info = {vars_turn: {vars_key: v for vars_key in range(20)} for vars_turn in range(50 if self.back_type == 'GA최적화' else 1)}
        else:
            self.day_info = {0: {0: v}}
        v = GetTradeInfo(2)
        if self.opti_turn == 1:
            self.trade_info = {vars_turn: {vars_key: v for vars_key in range(len(self.vars_list[vars_turn][0]))} for vars_turn in range(len(self.vars_list))}
        elif self.opti_turn == 3:
            self.trade_info = {vars_turn: {vars_key: v for vars_key in range(20)} for vars_turn in range(50 if self.back_type == 'GA최적화' else 1)}
        else:
            self.trade_info = {0: {0: v}}

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
            self.tq.put(('전체틱수', total_ticks))
            self.tick_calcul = True

        for code in self.code_list:
            self.code = code
            self.name = self.dict_cn[self.code] if self.code in self.dict_cn.keys() else self.code
            self.total_count = 0

            if self.dict_set['백테주문관리적용'] and self.dict_set['주식매수금지블랙리스트'] and self.code in self.dict_set['주식블랙리스트'] and self.back_type != '백파인더':
                self.tq.put(('백테완료', 0))
                continue

            if not self.dict_set['백테일괄로딩']:
                self.dict_tik_ar = {code: pickle_read(f'{BACK_TEMP}/{self.gubun}_{code}_tick')}

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
                    else:
                        self.LastSell()
                        self.InitTradeInfo()
                    if self.back_type is None: break
                    if self.opti_turn in (1, 3): self.tq.put('탐색완료')

            self.tq.put(('백테완료', self.total_count))

        if self.pattern: self.tq.put(('학습결과', self.pattern_buy, self.pattern_sell))
        if self.profile: self.pr.print_stats(sort='cumulative')

    def Strategy(self):
        def now():
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
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else 매수틱번호 + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else 매수틱번호 + 1
                return round(self.array_tick[sindex:eindex, 1].mean(), 3)

        def GetArrayIndex(aindex):
            return aindex + 13 * self.avg_list.index(self.avgtime if self.back_type in ('백테스트', '조건최적화', '백파인더') else self.vars[0])

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
            return Parameter_Area(49, 1, tick, pre, 'max')

        def 최저현재가(tick, pre=0):
            return Parameter_Area(50, 1, tick, pre, 'min')

        def 체결강도평균(tick, pre=0):
            return Parameter_Area(51, 7, tick, pre, 'mean')

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
            return Parameter_Area(58, 19, tick, pre, 'mean')

        def Parameter_Dgree(aindex, vindex, tick, pre, cf):
            if tick in self.avg_list:
                return Parameter_Previous(GetArrayIndex(aindex), pre)
            else:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else 매수틱번호 + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else 매수틱번호 + 1
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

                    수익금, 수익률 = 0, 0
                    보유중, 매수가, 매도가, 주문수량, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간, 추가매수시간, 매수호가, \
                        매도호가, 매수호가_, 매도호가_, 추가매수가, 매수호가단위, 매도호가단위, 매수정정횟수, 매도정정횟수, 매수분할횟수, \
                        매도분할횟수, 매수주문취소시간, 매도주문취소시간 = self.trade_info[vars_turn][vars_key].values()
                    if self.trade_info[vars_turn][vars_key]['보유중']:
                        _, 수익금, 수익률 = GetKiwoomPgSgSp(보유수량 * 매수가, 보유수량 * 현재가)
                        if 수익률 > 최고수익률:
                            self.trade_info[vars_turn][vars_key]['최고수익률'] = 최고수익률 = 수익률
                        elif 수익률 < 최저수익률:
                            self.trade_info[vars_turn][vars_key]['최저수익률'] = 최저수익률 = 수익률
                        보유시간 = (now() - 매수시간).total_seconds()

                    gubun = None
                    if self.dict_set['주식매수주문구분'] == '시장가':
                        if not 보유중:
                            gubun = '매수'
                        elif 매수분할횟수 < self.dict_set['주식매수분할횟수']:
                            gubun = '매수매도'
                        else:
                            gubun = '매도'
                    elif self.dict_set['주식매수주문구분'] == '지정가':
                        if not 보유중:
                            if 매수호가 == 0:
                                gubun = '매수'
                            else:
                                관심이탈 = not 관심종목 and 관심종목N(1)
                                self.CheckBuy(vars_turn, vars_key, 현재가, 관심이탈)
                                continue
                        elif 매수분할횟수 < self.dict_set['주식매수분할횟수']:
                            if 매수호가 == 0 and 매도호가 == 0:
                                if self.dict_set['주식매도금지매수횟수'] and 매수분할횟수 < self.dict_set['주식매도금지매수횟수값']:
                                    gubun = '매수'
                                else:
                                    gubun = '매수매도'
                            elif 매수호가 != 0:
                                관심이탈 = not 관심종목 and 관심종목N(1)
                                self.CheckBuy(vars_turn, vars_key, 현재가, 관심이탈)
                                continue
                            else:
                                관심진입 = 관심종목 and not 관심종목N(1)
                                self.CheckSell(vars_turn, vars_key, 현재가, 관심진입)
                                continue
                        else:
                            if 매도호가 == 0:
                                gubun = '매도'
                            else:
                                관심진입 = 관심종목 and not 관심종목N(1)
                                self.CheckSell(vars_turn, vars_key, 현재가, 관심진입)
                                continue

                    매수, 매도 = True, False
                    if '매수' in gubun:
                        if not 관심종목: continue
                        cancel = False
                        거래횟수, 손절횟수, 직전거래시간, 손절매도시간 = self.day_info[vars_turn][vars_key].values()
                        if self.dict_set['주식매수금지거래횟수'] and self.dict_set['주식매수금지거래횟수값'] <= 거래횟수:
                            cancel = True
                        elif self.dict_set['주식매수금지손절횟수'] and self.dict_set['주식매수금지손절횟수값'] <= 손절횟수:
                            cancel = True
                        elif self.dict_set['주식매수금지시간'] and self.dict_set['주식매수금지시작시간'] < \
                                int(str(self.index)[8:]) < self.dict_set['주식매수금지종료시간']:
                            cancel = True
                        elif self.dict_set['주식매수금지간격'] and now() <= 직전거래시간:
                            cancel = True
                        elif self.dict_set['주식매수금지손절간격'] and now() <= 손절매도시간:
                            cancel = True
                        elif self.dict_set['주식매수금지라운드피겨'] and \
                                roundfigure_upper(현재가, self.dict_set['주식매수금지라운드호가'], self.index):
                            cancel = True
                        if cancel: continue

                        if self.dict_set['주식매수분할횟수'] == 1:
                            self.trade_info[vars_turn][vars_key]['주문수량'] = int(self.betting / 현재가)
                        else:
                            oc_ratio = dict_order_ratio[self.dict_set['주식매수분할방법']][
                                self.dict_set['주식매수분할횟수']][매수분할횟수]
                            self.trade_info[vars_turn][vars_key]['주문수량'] = int(self.betting / (
                                현재가 if not 보유중 else 매수가) * oc_ratio / 100)

                        if self.dict_set['주식매수주문구분'] == '지정가':
                            기준가격 = 현재가
                            if self.dict_set['주식매수지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                            if self.dict_set['주식매수지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                            self.trade_info[vars_turn][vars_key]['매수호가_'] = \
                                기준가격 + 호가단위 * self.dict_set['주식매수지정가호가번호']

                        if not 보유중:
                            exec(self.buystg)
                        else:
                            분할매수기준수익률 = \
                                round((현재가 / 추가매수가 - 1) * 100, 2) if self.dict_set['주식매수분할고정수익률'] else 수익률
                            if self.dict_set['주식매수분할하방'] and 분할매수기준수익률 < -self.dict_set['주식매수분할하방수익률']:
                                self.Buy(vars_turn, vars_key)
                            elif self.dict_set['주식매수분할상방'] and 분할매수기준수익률 > self.dict_set['주식매수분할상방수익률']:
                                self.Buy(vars_turn, vars_key)
                            elif self.dict_set['주식매수분할시그널']:
                                exec(self.buystg)

                    if '매도' in gubun:
                        if (self.dict_set['주식매도손절수익률청산'] and 수익률 < -self.dict_set['주식매도손절수익률']) or \
                                (self.dict_set['주식매도손절수익금청산'] and 수익금 < -self.dict_set['주식매도손절수익금'] * 10000):
                            self.Sonjeol(vars_turn, vars_key)
                            continue

                        cancel = False
                        if self.dict_set['주식매도주문구분'] == '시장가':
                            if 매수분할횟수 != self.trade_info[vars_turn][vars_key]['매수분할횟수']:
                                cancel = True
                        elif self.trade_info[vars_turn][vars_key]['매수호가'] != 0:
                            cancel = True
                        if cancel: continue

                        cancel = False
                        if self.dict_set['주식매도금지시간'] and self.dict_set['주식매도금지시작시간'] < \
                                int(str(self.index)[8:]) < self.dict_set['주식매도금지종료시간']:
                            cancel = True
                        elif self.dict_set['주식매도금지간격'] and now() <= self.day_info[vars_turn][vars_key]['직전거래시간']:
                            cancel = True
                        elif self.dict_set['주식매도금지라운드피겨'] and \
                                roundfigure_lower(현재가, self.dict_set['주식매도금지라운드호가'], self.index):
                            cancel = True
                        elif self.dict_set['주식매수분할횟수'] > 1 and self.dict_set['주식매도금지매수횟수'] and \
                                매수분할횟수 <= self.dict_set['주식매도금지매수횟수값']:
                            cancel = True
                        if cancel: continue

                        if self.dict_set['주식매도분할횟수'] == 1:
                            self.trade_info[vars_turn][vars_key]['주문수량'] = 보유수량
                        else:
                            oc_ratio = dict_order_ratio[self.dict_set['주식매도분할방법']][
                                self.dict_set['주식매도분할횟수']][매도분할횟수]
                            self.trade_info[vars_turn][vars_key]['주문수량'] = \
                                int(self.betting / self.trade_info[vars_turn][vars_key]['매수가'] * oc_ratio / 100)
                            if self.trade_info[vars_turn][vars_key]['주문수량'] > 보유수량 or \
                                    매도분할횟수 + 1 == self.dict_set['주식매도분할횟수']:
                                self.trade_info[vars_turn][vars_key]['주문수량'] = 보유수량

                        if self.dict_set['주식매도주문구분'] == '지정가':
                            기준가격 = 현재가
                            if self.dict_set['주식매도지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                            if self.dict_set['주식매도지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                            self.trade_info[vars_turn][vars_key]['매도호가_'] = \
                                기준가격 + 호가단위 * self.dict_set['주식매도지정가호가번호']

                        if self.dict_set['주식매도분할횟수'] == 1:
                            exec(self.sellstg)
                        else:
                            if self.dict_set['주식매도분할하방'] and \
                                    수익률 < -self.dict_set['주식매도분할하방수익률'] * (매도분할횟수 + 1):
                                self.Sell(vars_turn, vars_key, 100)
                            elif self.dict_set['주식매도분할상방'] and \
                                    수익률 > self.dict_set['주식매도분할상방수익률'] * (매도분할횟수 + 1):
                                self.Sell(vars_turn, vars_key, 100)
                            elif self.dict_set['주식매도분할시그널']:
                                exec(self.sellstg)

        elif self.opti_turn == 3:
            vars_turns = range(50 if self.back_type == 'GA최적화' else 1)
            for vars_turn in vars_turns:
                vars_keys = range(20)
                for vars_key in vars_keys:
                    index = vars_turn * 20 + vars_key
                    if self.back_type != '조건최적화':
                        self.vars = self.vars_lists[index]
                        if self.tick_count < self.vars[0]:
                            break
                    elif self.tick_count < self.avgtime:
                        break

                    수익금, 수익률 = 0, 0
                    보유중, 매수가, 매도가, 주문수량, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간, 추가매수시간, 매수호가, \
                        매도호가, 매수호가_, 매도호가_, 추가매수가, 매수호가단위, 매도호가단위, 매수정정횟수, 매도정정횟수, 매수분할횟수, \
                        매도분할횟수, 매수주문취소시간, 매도주문취소시간 = self.trade_info[vars_turn][vars_key].values()
                    if self.trade_info[vars_turn][vars_key]['보유중']:
                        _, 수익금, 수익률 = GetKiwoomPgSgSp(보유수량 * 매수가, 보유수량 * 현재가)
                        if 수익률 > 최고수익률:
                            self.trade_info[vars_turn][vars_key]['최고수익률'] = 최고수익률 = 수익률
                        elif 수익률 < 최저수익률:
                            self.trade_info[vars_turn][vars_key]['최저수익률'] = 최저수익률 = 수익률
                        보유시간 = (now() - 매수시간).total_seconds()

                    gubun = None
                    if self.dict_set['주식매수주문구분'] == '시장가':
                        if not 보유중:
                            gubun = '매수'
                        elif 매수분할횟수 < self.dict_set['주식매수분할횟수']:
                            gubun = '매수매도'
                        else:
                            gubun = '매도'
                    elif self.dict_set['주식매수주문구분'] == '지정가':
                        if not 보유중:
                            if 매수호가 == 0:
                                gubun = '매수'
                            else:
                                관심이탈 = not 관심종목 and 관심종목N(1)
                                self.CheckBuy(vars_turn, vars_key, 현재가, 관심이탈)
                                continue
                        elif 매수분할횟수 < self.dict_set['주식매수분할횟수']:
                            if 매수호가 == 0 and 매도호가 == 0:
                                if self.dict_set['주식매도금지매수횟수'] and \
                                        매수분할횟수 < self.dict_set['주식매도금지매수횟수값']:
                                    gubun = '매수'
                                else:
                                    gubun = '매수매도'
                            elif 매수호가 != 0:
                                관심이탈 = not 관심종목 and 관심종목N(1)
                                self.CheckBuy(vars_turn, vars_key, 현재가, 관심이탈)
                                continue
                            else:
                                관심진입 = 관심종목 and not 관심종목N(1)
                                self.CheckSell(vars_turn, vars_key, 현재가, 관심진입)
                                continue
                        else:
                            if 매도호가 == 0:
                                gubun = '매도'
                            else:
                                관심진입 = 관심종목 and not 관심종목N(1)
                                self.CheckSell(vars_turn, vars_key, 현재가, 관심진입)
                                continue

                    매수, 매도 = True, False
                    if '매수' in gubun:
                        if not 관심종목: continue
                        cancel = False
                        거래횟수, 손절횟수, 직전거래시간, 손절매도시간 = self.day_info[vars_turn][vars_key].values()
                        if self.dict_set['주식매수금지거래횟수'] and self.dict_set['주식매수금지거래횟수값'] <= 거래횟수:
                            cancel = True
                        elif self.dict_set['주식매수금지손절횟수'] and self.dict_set['주식매수금지손절횟수값'] <= 손절횟수:
                            cancel = True
                        elif self.dict_set['주식매수금지시간'] and self.dict_set['주식매수금지시작시간'] < \
                                int(str(self.index)[8:]) < self.dict_set['주식매수금지종료시간']:
                            cancel = True
                        elif self.dict_set['주식매수금지간격'] and now() <= 직전거래시간:
                            cancel = True
                        elif self.dict_set['주식매수금지손절간격'] and now() <= 손절매도시간:
                            cancel = True
                        elif self.dict_set['주식매수금지라운드피겨'] and \
                                roundfigure_upper(현재가, self.dict_set['주식매수금지라운드호가'], self.index):
                            cancel = True
                        if cancel: continue

                        if self.dict_set['주식매수분할횟수'] == 1:
                            self.trade_info[vars_turn][vars_key]['주문수량'] = int(self.betting / 현재가)
                        else:
                            oc_ratio = dict_order_ratio[self.dict_set['주식매수분할방법']][
                                self.dict_set['주식매수분할횟수']][매수분할횟수]
                            self.trade_info[vars_turn][vars_key]['주문수량'] = int(self.betting / (
                                현재가 if not 보유중 else 매수가) * oc_ratio / 100)

                        if self.dict_set['주식매수주문구분'] == '지정가':
                            기준가격 = 현재가
                            if self.dict_set['주식매수지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                            if self.dict_set['주식매수지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                            self.trade_info[vars_turn][vars_key]['매수호가_'] = \
                                기준가격 + 호가단위 * self.dict_set['주식매수지정가호가번호']

                        if not 보유중:
                            if self.back_type != '조건최적화':
                                exec(self.buystg)
                            else:
                                exec(self.dict_buystg[index])
                        else:
                            분할매수기준수익률 = \
                                round((현재가 / 추가매수가 - 1) * 100, 2) if self.dict_set['주식매수분할고정수익률'] else 수익률
                            if self.dict_set['주식매수분할하방'] and \
                                    분할매수기준수익률 < -self.dict_set['주식매수분할하방수익률']:
                                self.Buy(vars_turn, vars_key)
                            elif self.dict_set['주식매수분할상방'] and \
                                    분할매수기준수익률 > self.dict_set['주식매수분할상방수익률']:
                                self.Buy(vars_turn, vars_key)
                            elif self.dict_set['주식매수분할시그널']:
                                if self.back_type != '조건최적화':
                                    exec(self.buystg)
                                else:
                                    exec(self.dict_buystg[index])

                    if '매도' in gubun:
                        if (self.dict_set['주식매도손절수익률청산'] and 수익률 < -self.dict_set['주식매도손절수익률']) or \
                                (self.dict_set['주식매도손절수익금청산'] and 수익금 < -self.dict_set['주식매도손절수익금'] * 10000):
                            self.Sonjeol(vars_turn, vars_key)
                            continue

                        cancel = False
                        if self.dict_set['주식매도주문구분'] == '시장가':
                            if 매수분할횟수 != self.trade_info[vars_turn][vars_key]['매수분할횟수']:
                                cancel = True
                        elif self.trade_info[vars_turn][vars_key]['매수호가'] != 0:
                            cancel = True
                        if cancel: continue

                        cancel = False
                        if self.dict_set['주식매도금지시간'] and self.dict_set['주식매도금지시작시간'] < \
                                int(str(self.index)[8:]) < self.dict_set['주식매도금지종료시간']:
                            cancel = True
                        elif self.dict_set['주식매도금지간격'] and now() <= self.day_info[vars_turn][vars_key]['직전거래시간']:
                            cancel = True
                        elif self.dict_set['주식매도금지라운드피겨'] and \
                                roundfigure_lower(현재가, self.dict_set['주식매도금지라운드호가'], self.index):
                            cancel = True
                        elif self.dict_set['주식매수분할횟수'] > 1 and self.dict_set['주식매도금지매수횟수'] and \
                                매수분할횟수 <= self.dict_set['주식매도금지매수횟수값']:
                            cancel = True
                        if cancel: continue

                        if self.dict_set['주식매도분할횟수'] == 1:
                            self.trade_info[vars_turn][vars_key]['주문수량'] = 보유수량
                        else:
                            oc_ratio = dict_order_ratio[self.dict_set['주식매도분할방법']][
                                self.dict_set['주식매도분할횟수']][매도분할횟수]
                            self.trade_info[vars_turn][vars_key]['주문수량'] = \
                                int(self.betting / self.trade_info[vars_turn][vars_key]['매수가'] * oc_ratio / 100)
                            if self.trade_info[vars_turn][vars_key]['주문수량'] > 보유수량 or \
                                    매도분할횟수 + 1 == self.dict_set['주식매도분할횟수']:
                                self.trade_info[vars_turn][vars_key]['주문수량'] = 보유수량

                        if self.dict_set['주식매도주문구분'] == '지정가':
                            기준가격 = 현재가
                            if self.dict_set['주식매도지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                            if self.dict_set['주식매도지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                            self.trade_info[vars_turn][vars_key]['매도호가_'] = \
                                기준가격 + 호가단위 * self.dict_set['주식매도지정가호가번호']

                        if self.dict_set['주식매도분할횟수'] == 1:
                            if self.back_type != '조건최적화':
                                exec(self.sellstg)
                            else:
                                exec(self.dict_sellstg[index])
                        else:
                            if self.dict_set['주식매도분할하방'] and \
                                    수익률 < -self.dict_set['주식매도분할하방수익률'] * (매도분할횟수 + 1):
                                self.Sell(vars_turn, vars_key, 100)
                            elif self.dict_set['주식매도분할상방'] and \
                                    수익률 > self.dict_set['주식매도분할상방수익률'] * (매도분할횟수 + 1):
                                self.Sell(vars_turn, vars_key, 100)
                            elif self.dict_set['주식매도분할시그널']:
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

            수익금, 수익률 = 0, 0
            보유중, 매수가, 매도가, 주문수량, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간, 추가매수시간, 매수호가, \
                매도호가, 매수호가_, 매도호가_, 추가매수가, 매수호가단위, 매도호가단위, 매수정정횟수, 매도정정횟수, 매수분할횟수, \
                매도분할횟수, 매수주문취소시간, 매도주문취소시간 = self.trade_info[vars_turn][vars_key].values()
            if self.trade_info[vars_turn][vars_key]['보유중']:
                _, 수익금, 수익률 = GetKiwoomPgSgSp(보유수량 * 매수가, 보유수량 * 현재가)
                if 수익률 > 최고수익률:
                    self.trade_info[vars_turn][vars_key]['최고수익률'] = 최고수익률 = 수익률
                elif 수익률 < 최저수익률:
                    self.trade_info[vars_turn][vars_key]['최저수익률'] = 최저수익률 = 수익률
                보유시간 = (now() - 매수시간).total_seconds()

            gubun = None
            if self.dict_set['주식매수주문구분'] == '시장가':
                if not 보유중:
                    gubun = '매수'
                elif 매수분할횟수 < self.dict_set['주식매수분할횟수']:
                    gubun = '매수매도'
                else:
                    gubun = '매도'
            elif self.dict_set['주식매수주문구분'] == '지정가':
                if not 보유중:
                    if 매수호가 == 0:
                        gubun = '매수'
                    else:
                        관심이탈 = not 관심종목 and 관심종목N(1)
                        self.CheckBuy(vars_turn, vars_key, 현재가, 관심이탈)
                        return
                elif 매수분할횟수 < self.dict_set['주식매수분할횟수']:
                    if 매수호가 == 0 and 매도호가 == 0:
                        if self.dict_set['주식매도금지매수횟수'] and 매수분할횟수 < self.dict_set['주식매도금지매수횟수값']:
                            gubun = '매수'
                        else:
                            gubun = '매수매도'
                    elif 매수호가 != 0:
                        관심이탈 = not 관심종목 and 관심종목N(1)
                        self.CheckBuy(vars_turn, vars_key, 현재가, 관심이탈)
                        return
                    else:
                        관심진입 = 관심종목 and not 관심종목N(1)
                        self.CheckSell(vars_turn, vars_key, 현재가, 관심진입)
                        return
                else:
                    if 매도호가 == 0:
                        gubun = '매도'
                    else:
                        관심진입 = 관심종목 and not 관심종목N(1)
                        self.CheckSell(vars_turn, vars_key, 현재가, 관심진입)
                        return

            매수, 매도 = True, False
            if '매수' in gubun:
                if not 관심종목: return
                cancel = False
                거래횟수, 손절횟수, 직전거래시간, 손절매도시간 = self.day_info[vars_turn][vars_key].values()
                if self.dict_set['주식매수금지거래횟수'] and self.dict_set['주식매수금지거래횟수값'] <= 거래횟수:
                    cancel = True
                elif self.dict_set['주식매수금지손절횟수'] and self.dict_set['주식매수금지손절횟수값'] <= 손절횟수:
                    cancel = True
                elif self.dict_set['주식매수금지시간'] and self.dict_set['주식매수금지시작시간'] < \
                        int(str(self.index)[8:]) < self.dict_set['주식매수금지종료시간']:
                    cancel = True
                elif self.dict_set['주식매수금지간격'] and now() <= 직전거래시간:
                    cancel = True
                elif self.dict_set['주식매수금지손절간격'] and now() <= 손절매도시간:
                    cancel = True
                elif self.dict_set['주식매수금지라운드피겨'] and \
                        roundfigure_upper(현재가, self.dict_set['주식매수금지라운드호가'], self.index):
                    cancel = True
                if cancel: return

                if self.dict_set['주식매수분할횟수'] == 1:
                    self.trade_info[vars_turn][vars_key]['주문수량'] = int(self.betting / 현재가)
                else:
                    oc_ratio = dict_order_ratio[self.dict_set['주식매수분할방법']][
                        self.dict_set['주식매수분할횟수']][매수분할횟수]
                    self.trade_info[vars_turn][vars_key]['주문수량'] = int(self.betting / (
                        현재가 if not 보유중 else 매수가) * oc_ratio / 100)

                if self.dict_set['주식매수주문구분'] == '지정가':
                    기준가격 = 현재가
                    if self.dict_set['주식매수지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                    if self.dict_set['주식매수지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                    self.trade_info[vars_turn][vars_key]['매수호가_'] = \
                        기준가격 + 호가단위 * self.dict_set['주식매수지정가호가번호']

                if not 보유중:
                    exec(self.buystg)
                else:
                    분할매수기준수익률 = \
                        round((현재가 / 추가매수가 - 1) * 100, 2) if self.dict_set['주식매수분할고정수익률'] else 수익률
                    if self.dict_set['주식매수분할하방'] and 분할매수기준수익률 < -self.dict_set['주식매수분할하방수익률']:
                        self.Buy(vars_turn, vars_key)
                    elif self.dict_set['주식매수분할상방'] and 분할매수기준수익률 > self.dict_set['주식매수분할상방수익률']:
                        self.Buy(vars_turn, vars_key)
                    elif self.dict_set['주식매수분할시그널']:
                        exec(self.buystg)

            if '매도' in gubun:
                if (self.dict_set['주식매도손절수익률청산'] and 수익률 < -self.dict_set['주식매도손절수익률']) or \
                        (self.dict_set['주식매도손절수익금청산'] and 수익금 < -self.dict_set['주식매도손절수익금'] * 10000):
                    self.Sonjeol(vars_turn, vars_key)
                    return

                cancel = False
                if self.dict_set['주식매도주문구분'] == '시장가':
                    if 매수분할횟수 != self.trade_info[vars_turn][vars_key]['매수분할횟수']:
                        cancel = True
                elif self.trade_info[vars_turn][vars_key]['매수호가'] != 0:
                    cancel = True
                if cancel: return

                cancel = False
                if self.dict_set['주식매도금지시간'] and self.dict_set['주식매도금지시작시간'] < \
                        int(str(self.index)[8:]) < self.dict_set['주식매도금지종료시간']:
                    cancel = True
                elif self.dict_set['주식매도금지간격'] and now() <= self.day_info[vars_turn][vars_key]['직전거래시간']:
                    cancel = True
                elif self.dict_set['주식매도금지라운드피겨'] and \
                        roundfigure_lower(현재가, self.dict_set['주식매도금지라운드호가'], self.index):
                    cancel = True
                elif self.dict_set['주식매수분할횟수'] > 1 and self.dict_set['주식매도금지매수횟수'] and \
                        매수분할횟수 <= self.dict_set['주식매도금지매수횟수값']:
                    cancel = True
                if cancel: return

                if self.dict_set['주식매도분할횟수'] == 1:
                    self.trade_info[vars_turn][vars_key]['주문수량'] = 보유수량
                else:
                    oc_ratio = dict_order_ratio[self.dict_set['주식매도분할방법']][
                        self.dict_set['주식매도분할횟수']][매도분할횟수]
                    self.trade_info[vars_turn][vars_key]['주문수량'] = \
                        int(self.betting / self.trade_info[vars_turn][vars_key]['매수가'] * oc_ratio / 100)
                    if self.trade_info[vars_turn][vars_key]['주문수량'] > 보유수량 or \
                            매도분할횟수 + 1 == self.dict_set['주식매도분할횟수']:
                        self.trade_info[vars_turn][vars_key]['주문수량'] = 보유수량

                if self.dict_set['주식매도주문구분'] == '지정가':
                    기준가격 = 현재가
                    if self.dict_set['주식매도지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                    if self.dict_set['주식매도지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                    self.trade_info[vars_turn][vars_key]['매도호가_'] = \
                        기준가격 + 호가단위 * self.dict_set['주식매도지정가호가번호']

                if self.dict_set['주식매도분할횟수'] == 1:
                    exec(self.sellstg)
                else:
                    if self.dict_set['주식매도분할하방'] and \
                            수익률 < -self.dict_set['주식매도분할하방수익률'] * (매도분할횟수 + 1):
                        self.Sell(vars_turn, vars_key, 100)
                    elif self.dict_set['주식매도분할상방'] and \
                            수익률 > self.dict_set['주식매도분할상방수익률'] * (매도분할횟수 + 1):
                        self.Sell(vars_turn, vars_key, 100)
                    elif self.dict_set['주식매도분할시그널']:
                        exec(self.sellstg)

    def Buy(self, vars_turn, vars_key):
        if self.back_type == '백테스트':
            if self.pattern:
                self.PatternModeling('매수')
            elif self.pattern_test:
                pattern = self.GetPattern('매수')
                if pattern not in self.pattern_buy:
                    return

        주문수량 = 미체결수량 = self.trade_info[vars_turn][vars_key]['주문수량']
        if 주문수량 > 0:
            if self.dict_set['주식매수주문구분'] == '시장가':
                매수금액 = 0
                for 매도호가, 매도잔량 in self.bhogainfo:
                    if 미체결수량 - 매도잔량 <= 0:
                        매수금액 += 매도호가 * 미체결수량
                        미체결수량 -= 매도잔량
                        break
                    else:
                        매수금액 += 매도호가 * 매도잔량
                        미체결수량 -= 매도잔량
                if 미체결수량 <= 0:
                    매수가 = self.trade_info[vars_turn][vars_key]['매수가']
                    보유수량 = self.trade_info[vars_turn][vars_key]['보유수량']
                    직전매수금액 = 매수가 * 보유수량
                    추가매수가 = int(round(매수금액 / 주문수량))
                    총수량 = 보유수량 + 주문수량
                    평단가 = int(round((직전매수금액 + 매수금액) / 총수량))
                    self.trade_info[vars_turn][vars_key]['매수가'] = 평단가
                    self.trade_info[vars_turn][vars_key]['보유수량'] = 총수량
                    self.trade_info[vars_turn][vars_key]['추가매수가'] = 추가매수가
                    self.UpdateBuyInfo(vars_turn, vars_key, True if 매수가 == 0 else False)
            elif self.dict_set['주식매수주문구분'] == '지정가':
                self.trade_info[vars_turn][vars_key]['매수호가'] = self.trade_info[vars_turn][vars_key]['매수호가_']
                self.trade_info[vars_turn][vars_key]['매수호가단위'] = (
                    GetHogaunit(self.dict_kd[self.code] if self.code in self.dict_kd.keys() else True,
                                self.array_tick[self.indexn, 1], self.index))
                self.trade_info[vars_turn][vars_key]['매수주문취소시간'] = \
                    timedelta_sec(self.dict_set['주식매수취소시간초'], strp_time('%Y%m%d%H%M%S', str(self.index)))

    def CheckBuy(self, vars_turn, vars_key, 현재가, 관심이탈):
        """
        보유중, 매수가, 매도가, 주문수량, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간, 추가매수시간, 매수호가, 매도호가, \
            매수호가_, 매도호가_, 추가매수가, 매수호가단위, 매도호가단위, 매수정정횟수, 매도정정횟수, 매수분할횟수, 매도분할횟수, \
            매수주문취소시간, 매도주문취소시간 = self.trade_info[vars_turn][vars_key].values()
        """
        _, 매수가, _, 주문수량, 보유수량, _, _, _, _, _, 매수호가, _, _, _, _, \
            매수호가단위, _, _, _, _, _, 매수주문취소시간 = self.trade_info[vars_turn][vars_key].values()

        if self.dict_set['주식매수취소관심이탈'] and 관심이탈:
            self.trade_info[vars_turn][vars_key]['매수호가'] = 0
        elif self.dict_set['주식매수취소시간'] and strp_time('%Y%m%d%H%M%S', str(self.index)) > 매수주문취소시간:
            self.trade_info[vars_turn][vars_key]['매수호가'] = 0
        elif self.trade_info[vars_turn][vars_key]['매수정정횟수'] < self.dict_set['주식매수정정횟수'] and \
                현재가 >= 매수호가 + 매수호가단위 * self.dict_set['주식매수정정호가차이']:
            self.trade_info[vars_turn][vars_key]['매수호가'] = 현재가 - 매수호가단위 * self.dict_set['주식매수정정호가']
            self.trade_info[vars_turn][vars_key]['매수정정횟수'] += 1
            매수호가단위 = \
                GetHogaunit(self.dict_kd[self.code] if self.code in self.dict_kd.keys() else True, 현재가, self.index)
            self.trade_info[vars_turn][vars_key]['매수호가단위'] = 매수호가단위
        elif 현재가 < 매수호가:
            직전매수금액 = 매수가 * 보유수량
            매수금액 = 매수호가 * 주문수량
            총수량 = 보유수량 + 주문수량
            평단가 = int(round((직전매수금액 + 매수금액) / 총수량))
            self.trade_info[vars_turn][vars_key]['매수가'] = 평단가
            self.trade_info[vars_turn][vars_key]['보유수량'] = 총수량
            self.trade_info[vars_turn][vars_key]['추가매수가'] = int(매수호가)
            self.UpdateBuyInfo(vars_turn, vars_key, True if 매수가 == 0 else False)

    def UpdateBuyInfo(self, vars_turn, vars_key, firstbuy):
        datetimefromindex = strp_time('%Y%m%d%H%M%S', str(self.index))
        self.trade_info[vars_turn][vars_key]['보유중'] = 1
        self.trade_info[vars_turn][vars_key]['매수호가'] = 0
        self.trade_info[vars_turn][vars_key]['매수정정횟수'] = 0
        self.day_info[vars_turn][vars_key]['직전거래시간'] = \
            timedelta_sec(self.dict_set['주식매수금지간격초'], datetimefromindex)
        if firstbuy:
            self.trade_info[vars_turn][vars_key]['매수틱번호'] = self.indexn
            self.trade_info[vars_turn][vars_key]['매수시간'] = datetimefromindex
            self.trade_info[vars_turn][vars_key]['추가매수시간'] = []
            self.trade_info[vars_turn][vars_key]['매수분할횟수'] = 0
        text = f"{self.index};{self.trade_info[vars_turn][vars_key]['추가매수가']}"
        self.trade_info[vars_turn][vars_key]['추가매수시간'].append(text)
        self.trade_info[vars_turn][vars_key]['매수분할횟수'] += 1

    def Sell(self, vars_turn, vars_key, sell_cond):
        if self.back_type == '백테스트':
            if self.pattern:
                self.PatternModeling('매도')
            elif self.pattern_test:
                pattern = self.GetPattern('매도')
                if pattern not in self.pattern_sell:
                    return

        if self.dict_set['주식매도주문구분'] == '시장가':
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
        elif self.dict_set['주식매도주문구분'] == '지정가':
            현재가 = self.array_tick[self.indexn, 1]
            self.sell_cond = sell_cond
            self.trade_info[vars_turn][vars_key]['매도호가'] = self.trade_info[vars_turn][vars_key]['매도호가_']
            self.trade_info[vars_turn][vars_key]['매도호가단위'] = (
                GetHogaunit(self.dict_kd[self.code] if self.code in self.dict_kd.keys() else True, 현재가, self.index))
            self.trade_info[vars_turn][vars_key]['매도주문취소시간'] = \
                timedelta_sec(self.dict_set['주식매도취소시간초'], strp_time('%Y%m%d%H%M%S', str(self.index)))

    def CheckSell(self, vars_turn, vars_key, 현재가, 관심진입):
        """
        보유중, 매수가, 매도가, 주문수량, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간, 추가매수시간, 매수호가, 매도호가, \
            매수호가_, 매도호가_, 추가매수가, 매수호가단위, 매도호가단위, 매수정정횟수, 매도정정횟수, 매수분할횟수, 매도분할횟수, \
            매수주문취소시간, 매도주문취소시간 = self.trade_info[vars_turn][vars_key].values()
        """
        _, _, _, _, _, _, _, _, _, _, _, 매도호가, _, _, _, _, \
            매도호가단위, _, 매도정정횟수, _, _, _, 매도주문취소시간 = self.trade_info[vars_turn][vars_key].values()

        if self.dict_set['주식매도취소관심진입'] and 관심진입:
            self.trade_info[vars_turn][vars_key]['매도호가'] = 0
        elif self.dict_set['주식매도취소시간'] and strp_time('%Y%m%d%H%M%S', str(self.index)) > 매도주문취소시간:
            self.trade_info[vars_turn][vars_key]['매도호가'] = 0
        elif 매도정정횟수 < self.dict_set['주식매도정정횟수'] and 현재가 <= 매도호가 - 매도호가단위 * self.dict_set['주식매도정정호가차이']:
            self.trade_info[vars_turn][vars_key]['매도호가'] = 현재가 + 매도호가단위 * self.dict_set['주식매도정정호가']
            self.trade_info[vars_turn][vars_key]['매도정정횟수'] += 1
            매도호가단위 = GetHogaunit(self.dict_kd[self.code] if self.code in self.dict_kd.keys() else True, 현재가, self.index)
            self.trade_info[vars_turn][vars_key]['매도호가단위'] = 매도호가단위
        elif 현재가 > 매도호가:
            self.trade_info[vars_turn][vars_key]['매도가'] = 매도호가
            self.CalculationEyun(vars_turn, vars_key)

    def Sonjeol(self, vars_turn, vars_key):
        origin_sell_gubun = self.dict_set['주식매도주문구분']
        self.dict_set['주식매도주문구분'] = '시장가'
        self.trade_info[vars_turn][vars_key]['주문수량'] = self.trade_info[vars_turn][vars_key]['보유수량']
        self.Sell(vars_turn, vars_key, 200)
        self.dict_set['주식매도주문구분'] = origin_sell_gubun

    def CalculationEyun(self, vars_turn, vars_key):
        """
        보유중, 매수가, 매도가, 주문수량, 보유수량, 최고수익률, 최저수익률, 매수틱번호, 매수시간, 추가매수시간, 매수호가, 매도호가, \
            매수호가_, 매도호가_, 추가매수가, 매수호가단위, 매도호가단위, 매수정정횟수, 매도정정횟수, 매수분할횟수, 매도분할횟수, \
            매수주문취소시간, 매도주문취소시간 = self.trade_info[vars_turn][vars_key].values()
        """
        _, bp, sp, oc, bc, _, _, bi, bdt, abt, _, _, _, _, _, _, _, _, _, _, _, _, _ = self.trade_info[vars_turn][vars_key].values()
        bt, st, bg = int(self.array_tick[bi, 0]), self.index, oc * bp
        sg, pg, pp = GetKiwoomPgSgSp(bg, oc * sp)

        if not self.pattern:
            self.total_count += 1
            sgtg = int(self.array_tick[self.indexn, 12])
            ht = int((strp_time('%Y%m%d%H%M%S', str(self.index)) - bdt).total_seconds())
            sc = self.dict_sconds[self.sell_cond] if self.back_type != '조건최적화' else self.dict_sconds[vars_key][self.sell_cond]
            abt, bcx = '^'.join(abt), bc - oc == 0
            data = ['백테결과', self.name, sgtg, bt, st, ht, bp, sp, bg, sg, pp, pg, sc, abt, bcx, vars_turn, vars_key]
            self.bstq_list[vars_key if self.opti_turn in (1, 3) else (self.sell_count % 5)].put(data)
            self.sell_count += 1

        if pp < 0:
            self.day_info[vars_turn][vars_key]['손절횟수'] += 1
            self.day_info[vars_turn][vars_key]['손절매도시간'] = \
                timedelta_sec(self.dict_set['주식매수금지손절간격초'], strp_time('%Y%m%d%H%M%S', str(self.index)))
        if bc - oc > 0:
            self.trade_info[vars_turn][vars_key]['매도호가'] = 0
            self.trade_info[vars_turn][vars_key]['보유수량'] -= self.trade_info[vars_turn][vars_key]['주문수량']
            self.trade_info[vars_turn][vars_key]['매도정정횟수'] = 0
            self.trade_info[vars_turn][vars_key]['매도분할횟수'] += 1
        else:
            self.trade_info[vars_turn][vars_key] = GetTradeInfo(2)
