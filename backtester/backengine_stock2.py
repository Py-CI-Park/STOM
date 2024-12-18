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


class StockBackEngine2(StockBackEngine):
    def __init__(self, gubun, wq, pq, tq, bq, stq_list, profile=False):
        super().__init__(gubun, wq, pq, tq, bq, stq_list, profile)

    def InitTradeInfo(self):
        self.tick_count = 0
        v = GetTradeInfo(3)
        if self.vars_count == 1:
            self.day_info = {0: v}
        else:
            self.day_info = {k: v for k in range(self.vars_count)}
        v = GetTradeInfo(2)
        if self.vars_count == 1:
            self.trade_info = {0: v}
        else:
            self.trade_info = {k: v for k in range(self.vars_count)}

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
                self.tq.put(('백테완료', 0))
                continue

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
                    if self.back_type is None: break
                    next_day_change = i != last and index + 500000 < self.array_tick[i + 1, 0]
                    self.tick_count += 1
                    self.index  = int(index)
                    self.indexn = i

                    if i != last and not next_day_change:
                        self.Strategy()
                    else:
                        self.LastSell()
                        self.InitTradeInfo()

            self.tq.put(('백테완료', 1 if self.total_count > 0 else 0))

        if self.profile:
            self.pr.print_stats(sort='cumulative')

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
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else 매수틱번호 + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else 매수틱번호 + 1
                dmp_gap = self.array_tick[eindex, vindex] - self.array_tick[sindex, vindex]
                return round(math.atan2(dmp_gap * cf, tick) / (2 * math.pi) * 360, 2)

        def 등락율각도(tick, pre=0):
            return Parameter_Dgree(58, 5, tick, pre, 5)

        def 당일거래대금각도(tick, pre=0):
            return Parameter_Dgree(59, 6, tick, pre, 0.01)

        def 전일비각도(tick, pre=0):
            return Parameter_Dgree(60, 9, tick, pre, 1)

        종목명, 종목코드, 데이터길이, 시분초 = self.name, self.code, self.tick_count, int(str(self.index)[8:])
        현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 거래대금증감, 전일비, 회전율, 전일동시간비, 시가총액, 라운드피겨위5호가이내, \
            초당매수수량, 초당매도수량, VI해제시간, VI가격, VI호가단위, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량, \
            매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, \
            매도수5호가잔량합 = self.array_tick[self.indexn, 1:44]
        호가단위 = GetHogaunit(self.dict_kd[종목코드] if 종목코드 in self.dict_kd.keys() else True, 현재가, self.index)
        VI해제시간, VI아래5호가 = strp_time('%Y%m%d%H%M%S', str(int(VI해제시간))), GetUvilower5(VI가격, VI호가단위, self.index)

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
                    _, 수익금, 수익률 = GetKiwoomPgSgSp(매수금액, 평가금액)
                    if 수익률 > 최고수익률:
                        self.trade_info[j]['최고수익률'] = 최고수익률 = 수익률
                    elif 수익률 < 최저수익률:
                        self.trade_info[j]['최저수익률'] = 최저수익률 = 수익률
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
                                continue
                        except:
                            continue

                        cancel = False
                        if self.dict_set['주식매수금지거래횟수'] and self.dict_set['주식매수금지거래횟수값'] <= self.day_info[j]['거래횟수']:
                            cancel = True
                        elif self.dict_set['주식매수금지손절횟수'] and self.dict_set['주식매수금지손절횟수값'] <= self.day_info[j]['손절횟수']:
                            cancel = True
                        elif self.dict_set['주식매수금지시간'] and self.dict_set['주식매수금지시작시간'] < int(str(self.index)[8:]) < self.dict_set['주식매수금지종료시간']:
                            cancel = True
                        elif self.dict_set['주식매수금지간격'] and now() <= self.day_info[j]['직전거래시간']:
                            cancel = True
                        elif self.dict_set['주식매수금지손절간격'] and now() <= self.day_info[j]['손절매도시간']:
                            cancel = True
                        elif self.dict_set['주식매수금지라운드피겨'] and roundfigure_upper(현재가, self.dict_set['주식매수금지라운드호가'], self.index):
                            cancel = True
                        if cancel: continue

                        if self.dict_set['주식매수분할횟수'] == 1:
                            self.trade_info[j]['주문수량'] = int(self.betting / 현재가)
                        else:
                            oc_ratio = dict_order_ratio[self.dict_set['주식매수분할방법']][self.dict_set['주식매수분할횟수']][self.trade_info[j]['매수분할횟수']]
                            self.trade_info[j]['주문수량'] = int(self.betting / (현재가 if not self.trade_info[j]['보유중'] else self.trade_info[j]['매수가']) * oc_ratio / 100)

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
                            continue

                        cancel = False
                        if self.dict_set['주식매도금지시간'] and self.dict_set['주식매도금지시작시간'] < int(str(self.index)[8:]) < self.dict_set['주식매도금지종료시간']:
                            cancel = True
                        elif self.dict_set['주식매도금지간격'] and now() <= self.day_info[j]['직전거래시간']:
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
                    break

    def Buy(self):
        주문수량 = 미체결수량 = self.trade_info[self.vars_key]['주문수량']
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
                    if self.trade_info[self.vars_key]['보유수량'] == 0:
                        self.trade_info[self.vars_key]['매수가'] = int(round(매수금액 / 주문수량))
                        self.trade_info[self.vars_key]['보유수량'] = 주문수량
                        self.UpdateBuyInfo(True)
                    else:
                        매수가 = self.trade_info[self.vars_key]['매수가']
                        보유수량 = self.trade_info[self.vars_key]['보유수량']
                        총수량 = 보유수량 + 주문수량
                        self.trade_info[self.vars_key]['추가매수가'] = int(round(매수금액 / 주문수량))
                        self.trade_info[self.vars_key]['매수가'] = int(round((매수가 * 보유수량 + 매수금액) / 총수량))
                        self.trade_info[self.vars_key]['보유수량'] = 총수량
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
        self.day_info[self.vars_key]['직전거래시간'] = timedelta_sec(self.dict_set['주식매수금지간격초'], datetimefromindex)
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
            매도금액 = 0
            주문수량 = 미체결수량 = self.trade_info[self.vars_key]['주문수량']
            for 매수호가, 매수잔량 in self.shogainfo:
                if 미체결수량 - 매수잔량 <= 0:
                    매도금액 += 매수호가 * 미체결수량
                    미체결수량 -= 매수잔량
                    break
                else:
                    매도금액 += 매수호가 * 매수잔량
                    미체결수량 -= 매수잔량
            if 미체결수량 <= 0:
                self.trade_info[self.vars_key]['매도가'] = int(round(매도금액 / 주문수량))
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

    def CalculationEyun(self):
        self.total_count += 1
        _, bp, sp, oc, bc, hp, lp, bi, _, abt, _, _, _, _, _, _, _, _, _, _, _, _, _ = self.trade_info[self.vars_key].values()
        sgtg = int(self.array_tick[self.indexn, 12])
        ht = int((strp_time('%Y%m%d%H%M%S', str(self.index)) - strp_time('%Y%m%d%H%M%S', str(int(self.array_tick[bi, 0])))).total_seconds())
        bt, st, bg = int(self.array_tick[bi, 0]), self.index, oc * bp
        sg, pg, pp = GetKiwoomPgSgSp(bg, oc * sp)
        sc = self.dict_sconds[self.sell_cond] if self.back_type != '조건최적화' else self.dict_sconds[self.vars_key][self.sell_cond]
        abt, bcx = '^'.join(abt), bc - oc == 0
        data = ('백테결과', self.name, sgtg, bt, st, ht, bp, sp, bg, sg, pp, pg, sc, abt, bcx, self.vars_key)
        self.stq_list[self.vars_key if self.divid == 0 else (self.sell_count % self.divid)].put(data)
        if pp < 0:
            self.day_info[self.vars_key]['손절횟수'] += 1
            self.day_info[self.vars_key]['손절매도시간'] = timedelta_sec(self.dict_set['주식매수금지손절간격초'], strp_time('%Y%m%d%H%M%S', str(self.index)))
        if self.trade_info[self.vars_key]['보유수량'] - self.trade_info[self.vars_key]['주문수량'] > 0:
            self.trade_info[self.vars_key]['매도호가'] = 0
            self.trade_info[self.vars_key]['보유수량'] -= self.trade_info[self.vars_key]['주문수량']
            self.trade_info[self.vars_key]['매도정정횟수'] = 0
            self.trade_info[self.vars_key]['매도분할횟수'] += 1
        else:
            self.trade_info[self.vars_key] = GetTradeInfo(2)
        self.sell_count += 1
