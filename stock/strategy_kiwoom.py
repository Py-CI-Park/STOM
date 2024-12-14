import math
import time
import sqlite3
import numpy as np
import pandas as pd
from utility.setting import DB_STRATEGY, DICT_SET, ui_num, columns_jg, columns_gj, dict_order_ratio
# noinspection PyUnresolvedReferences
from utility.static import now, strf_time, strp_time, int_hms, timedelta_sec, GetUvilower5, GetKiwoomPgSgSp, GetHogaunit


class StrategyKiwoom:
    def __init__(self, gubun, qlist):
        """
           0        1       2      3       4      5      6       7         8        9       10       11        12
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, sreceivQ, straderQ, sstg1Q, sstg2Q, creceivQ, ctraderQ,
        cstgQ, tick1Q, tick2Q, tick3Q, tick4Q, tick5Q, tick6Q, tick7Q, tick8Q, tick9Q, liveQ, backQ, kimpQ
         13      14      15      16      17      18      19      20      21      22     23     24     25
        """
        self.gubun    = gubun
        self.windowQ  = qlist[0]
        self.chartQ   = qlist[4]
        self.straderQ = qlist[8]
        if self.gubun == 1:
            self.sstgQ = qlist[9]
        else:
            self.sstgQ = qlist[10]
        self.dict_set = DICT_SET

        if self.gubun == 1 and self.dict_set['전략연산프로파일링']:
            import cProfile
            self.pr = cProfile.Profile()
            self.pr.enable()

        self.buystrategy1  = None
        self.buystrategy2  = None
        self.sellstrategy1 = None
        self.sellstrategy2 = None

        self.vars          = {}
        self.vars2         = {}
        self.dict_tik_ar   = {}
        self.dict_day_ar   = {}
        self.dict_min_ar   = {}
        self.dict_day_data = {}
        self.dict_min_data = {}
        self.dict_buyinfo  = {}

        self.UpdateStrategy()

        self.list_kosd  = []
        self.list_gsjm  = []
        self.list_buy   = []
        self.list_sell  = []

        self.int_tujagm = 0
        self.stg_change = False
        self.chart_code = None
        self.dict_stgn  = None
        self.day_start  = strp_time('%Y%m%d%H%M%S', strf_time('%Y%m%d') + '090000')
        self.df_jg      = pd.DataFrame(columns=columns_jg)
        self.df_gj      = pd.DataFrame(columns=columns_gj)

        self.bhogainfo = {}
        self.shogainfo = {}
        self.dict_hilo = {}

        self.Start()

    def UpdateStrategy(self):
        con  = sqlite3.connect(DB_STRATEGY)
        dfb  = pd.read_sql('SELECT * FROM stockbuy', con).set_index('index')
        dfs  = pd.read_sql('SELECT * FROM stocksell', con).set_index('index')
        dfob = pd.read_sql('SELECT * FROM stockoptibuy', con).set_index('index')
        dfos = pd.read_sql('SELECT * FROM stockoptisell', con).set_index('index')
        con.close()

        if self.dict_set['주식장초매수전략'] == '':
            self.buystrategy1 = None
        elif self.dict_set['주식장초매수전략'] in dfb.index:
            self.buystrategy1 = compile(dfb['전략코드'][self.dict_set['주식장초매수전략']], '<string>', 'exec')
        elif self.dict_set['주식장초매수전략'] in dfob.index:
            self.buystrategy1 = compile(dfob['전략코드'][self.dict_set['주식장초매수전략']], '<string>', 'exec')
            self.vars = {i: var for i, var in enumerate(list(dfob.loc[self.dict_set['주식장초매수전략']])[1:]) if var != 9999.}

        if self.dict_set['주식장초매도전략'] == '':
            self.sellstrategy1 = None
        elif self.dict_set['주식장초매도전략'] in dfs.index:
            self.sellstrategy1 = compile(dfs['전략코드'][self.dict_set['주식장초매도전략']], '<string>', 'exec')
        elif self.dict_set['주식장초매도전략'] in dfos.index:
            self.sellstrategy1 = compile(dfos['전략코드'][self.dict_set['주식장초매도전략']], '<string>', 'exec')

        if self.dict_set['주식장중매수전략'] == '':
            self.buystrategy2 = None
        elif self.dict_set['주식장중매수전략'] in dfb.index:
            self.buystrategy2 = compile(dfb['전략코드'][self.dict_set['주식장중매수전략']], '<string>', 'exec')
        elif self.dict_set['주식장중매수전략'] in dfob.index:
            self.buystrategy2 = compile(dfob['전략코드'][self.dict_set['주식장중매수전략']], '<string>', 'exec')
            self.vars2 = {i: var for i, var in enumerate(list(dfob.loc[self.dict_set['주식장중매수전략']])[1:]) if var != 9999.}

        if self.dict_set['주식장중매도전략'] == '':
            self.sellstrategy2 = None
        elif self.dict_set['주식장중매도전략'] in dfs.index:
            self.sellstrategy2 = compile(dfs['전략코드'][self.dict_set['주식장중매도전략']], '<string>', 'exec')
        elif self.dict_set['주식장중매도전략'] in dfos.index:
            self.sellstrategy2 = compile(dfos['전략코드'][self.dict_set['주식장중매도전략']], '<string>', 'exec')

    def Start(self):
        if self.gubun == 2:
            self.windowQ.put([ui_num['S로그텍스트'], '시스템 명령 실행 알림 - 전략연산 시작'])
        jg_receiv_count = 0
        while True:
            data = self.sstgQ.get()
            if type(data) == list:
                if len(data) == 2:
                    self.UpdateList(data)
                else:
                    self.Strategy(data)
            elif type(data) == pd.DataFrame:
                self.df_jg = data
                jg_receiv_count += 1
                if jg_receiv_count % 2 == 0:
                    self.PutGsjmAndDeleteHilo()
            elif type(data) == int:
                self.int_tujagm = data
            elif type(data) == dict:
                if '키' in data.keys():
                    self.dict_set = data
                    self.UpdateStrategy()
                else:
                    self.dict_stgn = data
            elif type(data) == str:
                if data == '전략프로세스종료':
                    break
                elif data == '복기모드종료':
                    self.dict_tik_ar = {}
                else:
                    self.chart_code = data

        if self.gubun == 2:
            self.windowQ.put([ui_num['S로그텍스트'], '시스템 명령 실행 알림 - 전략연산 종료'])
        time.sleep(3)

    def UpdateList(self, data):
        gubun, codeorlist = data
        if gubun == '관심목록':
            self.list_gsjm = codeorlist
            drop_index_list = list(set(list(self.df_gj.index)) - set(codeorlist))
            self.df_gj.drop(index=drop_index_list, inplace=True)
        elif gubun in ['매수완료', '매수취소']:
            if codeorlist in self.list_buy:
                self.list_buy.remove(codeorlist)
        elif gubun in ['매도완료', '매도취소']:
            if codeorlist in self.list_sell:
                self.list_sell.remove(codeorlist)
        elif gubun == '매수주문':
            if codeorlist not in self.list_buy:
                self.list_buy.append(codeorlist)
        elif gubun == '매도주문':
            if codeorlist not in self.list_sell:
                self.list_sell.append(codeorlist)
        elif gubun == '매수전략':
            if int_hms() < self.dict_set['주식장초전략종료시간']:
                self.buystrategy1 = compile(codeorlist, '<string>', 'exec')
            else:
                self.buystrategy2 = compile(codeorlist, '<string>', 'exec')
        elif gubun == '매도전략':
            if int_hms() < self.dict_set['주식장초전략종료시간']:
                self.sellstrategy1 = compile(codeorlist, '<string>', 'exec')
            else:
                self.sellstrategy2 = compile(codeorlist, '<string>', 'exec')
        elif gubun == '매수전략중지':
            self.buystrategy1 = None
            self.buystrategy2 = None
        elif gubun == '매도전략중지':
            self.sellstrategy1 = None
            self.sellstrategy2 = None
        elif gubun == '코스닥목록':
            self.list_kosd = codeorlist
        elif gubun == '프로파일링결과':
            self.pr.print_stats(sort='cumulative')

    def Strategy(self, data):
        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 거래대금증감, 전일비, 회전율, 전일동시간비, 시가총액, \
            라운드피겨위5호가이내, 초당매수수량, 초당매도수량, VI해제시간, VI가격, VI호가단위, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량, \
            매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, \
            매도수5호가잔량합, 종목코드, 틱수신시간, 종목명 = data

        def 구간최고현재가(pre):
            return max(self.dict_tik_ar[종목코드][-(pre - 1):, 5].max(), 현재가)

        def 구간최저현재가(pre):
            return min(self.dict_tik_ar[종목코드][-(pre - 1):, 5].min(), 현재가)

        def 누적초당매수수량(pre):
            try:
                return self.dict_tik_ar[종목코드][-(pre - 1):, 12].sum() + 초당매수수량
            except:
                return 0

        def 누적초당매도수량(pre):
            try:
                return self.dict_tik_ar[종목코드][-(pre - 1):, 13].sum() + 초당매도수량
            except:
                return 0

        def 최고초당매수수량(pre):
            return max(self.dict_tik_ar[종목코드][-(pre - 1):, 12].max(), 초당매수수량)

        def 최고초당매도수량(pre):
            return max(self.dict_tik_ar[종목코드][-(pre - 1):, 13].max(), 초당매도수량)

        def 전일비각도(pre):
            try:
                jvp_gap = 전일비 - self.dict_tik_ar[종목코드][-(pre - 1), 27]
                return round(math.atan2(jvp_gap, pre) / (2 * math.pi) * 360, 2)
            except:
                return 0

        def 당일거래대금각도(pre):
            try:
                dmp_gap = 당일거래대금 - self.dict_tik_ar[종목코드][-(pre - 1), 21]
                return round(math.atan2(dmp_gap, pre) / (2 * math.pi) * 360, 2)
            except:
                return 0

        def 이평60N(pre):
            return self.dict_tik_ar[종목코드][-pre, 1]

        def 이평300N(pre):
            return self.dict_tik_ar[종목코드][-pre, 2]

        def 이평600N(pre):
            return self.dict_tik_ar[종목코드][-pre, 3]

        def 이평1200N(pre):
            return self.dict_tik_ar[종목코드][-pre, 4]

        def 현재가N(pre):
            return self.dict_tik_ar[종목코드][-pre, 5]

        def 체결강도N(pre):
            return self.dict_tik_ar[종목코드][-pre, 6]

        def 체결강도평균N(pre):
            return self.dict_tik_ar[종목코드][-pre, 7]

        def 최고체결강도N(pre):
            return self.dict_tik_ar[종목코드][-pre, 8]

        def 최저체결강도N(pre):
            return self.dict_tik_ar[종목코드][-pre, 9]

        def 초당거래대금N(pre):
            return self.dict_tik_ar[종목코드][-pre, 10]

        def 초당거래대금평균N(pre):
            return self.dict_tik_ar[종목코드][-pre, 11]

        def 초당매수수량N(pre):
            return self.dict_tik_ar[종목코드][-pre, 12]

        def 초당매도수량N(pre):
            return self.dict_tik_ar[종목코드][-pre, 13]

        def 등락율N(pre):
            return self.dict_tik_ar[종목코드][-pre, 14]

        def 고저평균대비등락율N(pre):
            return self.dict_tik_ar[종목코드][-pre, 15]

        def 매수총잔량N(pre):
            return self.dict_tik_ar[종목코드][-pre, 16]

        def 매도총잔량N(pre):
            return self.dict_tik_ar[종목코드][-pre, 17]

        def 매수잔량1N(pre):
            return self.dict_tik_ar[종목코드][-pre, 18]

        def 매도잔량1N(pre):
            return self.dict_tik_ar[종목코드][-pre, 19]

        def 매도수5호가잔량합N(pre):
            return self.dict_tik_ar[종목코드][-pre, 20]

        def 당일거래대금N(pre):
            return self.dict_tik_ar[종목코드][-pre, 21]

        def 누적초당매수수량N(pre):
            return self.dict_tik_ar[종목코드][-pre, 22]

        def 누적초당매도수량N(pre):
            return self.dict_tik_ar[종목코드][-pre, 23]

        def 당일거래대금각도N(pre):
            return self.dict_tik_ar[종목코드][-pre, 24]

        def 전일비각도N(pre):
            return self.dict_tik_ar[종목코드][-pre, 25]

        def 거래대금증감N(pre):
            return self.dict_tik_ar[종목코드][-pre, 26]

        def 전일비N(pre):
            return self.dict_tik_ar[종목코드][-pre, 27]

        def 회전율N(pre):
            return self.dict_tik_ar[종목코드][-pre, 28]

        def 전일동시간비N(pre):
            return self.dict_tik_ar[종목코드][-pre, 29]

        def 고가N(pre):
            return self.dict_tik_ar[종목코드][-pre, 30]

        def 저가N(pre):
            return self.dict_tik_ar[종목코드][-pre, 31]

        bhogainfo = {
            1: {매도호가1: 매도잔량1},
            2: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2},
            3: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2, 매도호가3: 매도잔량3},
            4: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2, 매도호가3: 매도잔량3, 매도호가4: 매도잔량4},
            5: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2, 매도호가3: 매도잔량3, 매도호가4: 매도잔량4, 매도호가5: 매도잔량5}
        }
        shogainfo = {
            1: {매수호가1: 매수잔량1},
            2: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2},
            3: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3},
            4: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3, 매수호가4: 매수잔량4},
            5: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3, 매수호가4: 매수잔량4, 매수호가5: 매수잔량5}
        }
        self.bhogainfo = bhogainfo[self.dict_set['주식매수시장가잔량범위']]
        self.shogainfo = shogainfo[self.dict_set['주식매도시장가잔량범위']]

        시분초 = int(str(체결시간)[8:])
        호가단위 = GetHogaunit(종목코드 in self.list_kosd, 현재가, 체결시간)
        VI아래5호가 = GetUvilower5(VI가격, VI호가단위, 체결시간)
        데이터길이 = len(self.dict_tik_ar[종목코드]) + 1 if 종목코드 in self.dict_tik_ar.keys() else 1
        평균값계산틱수 = self.dict_set['주식장초평균값계산틱수'] if 시분초 < self.dict_set['주식장초전략종료시간'] else self.dict_set['주식장중평균값계산틱수']
        초당거래대금평균, 체결강도평균, 최고체결강도, 최저체결강도, 이평60, 이평300, 이평600, 이평1200 = 0., 0., 0., 0., 0., 0., 0., 0.

        """
        체결시간, 이평60, 이평300, 이평600, 이평1200, 현재가, 체결강도, 체결강도평균, 최고체결강도, 최저체결강도, 초당거래대금,
           0       1      2        3       4       5       6        7           8           9          10  
        초당거래대금평균, 초당매수수량, 초당매도수량, 등락율, 고저평균대비등락율, 매수총잔량, 매도총잔량, 매수잔량1, 매도잔량1,
              11           12         13        14         15           16        17        18       19
        매도수5호가잔량합, 당일거래대금, 누적초당매수수량(평균값계산틱수), 누적초당매도수량(평균값계산틱수), 당일거래대금각도(평균값계산틱수),
               20          21                   22                          23                          24
        전일비각도(평균값계산틱수), 거래대금증감, 전일비, 회전율, 전일동시간비, 고가, 저가
                 25                26       27     28       29       30   31
        """

        if 종목코드 in self.dict_tik_ar.keys():
            if len(self.dict_tik_ar[종목코드]) >= 평균값계산틱수 - 1:
                초당거래대금평균 = (self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 10].sum() + 초당거래대금) / 평균값계산틱수
                체결강도평균    = (self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):,  6].sum() + 체결강도) / 평균값계산틱수
                최고체결강도 = max(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):,  6].max(), 체결강도)
                최저체결강도 = min(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):,  6].min(), 체결강도)
            if len(self.dict_tik_ar[종목코드]) >=   59: 이평60   = round((self.dict_tik_ar[종목코드][  -59:, 5].sum() + 현재가) /   60, 3)
            if len(self.dict_tik_ar[종목코드]) >=  299: 이평300  = round((self.dict_tik_ar[종목코드][ -299:, 5].sum() + 현재가) /  300, 3)
            if len(self.dict_tik_ar[종목코드]) >=  599: 이평600  = round((self.dict_tik_ar[종목코드][ -599:, 5].sum() + 현재가) /  600, 3)
            if len(self.dict_tik_ar[종목코드]) >= 1199: 이평1200 = round((self.dict_tik_ar[종목코드][-1199:, 5].sum() + 현재가) / 1200, 3)

        if 초당거래대금평균 != 0 and not (매수잔량5 == 0 and 매도잔량5 == 0):
            if 종목코드 in self.df_jg.index and ((self.gubun == 1 and self.dict_stgn[종목코드]) or (self.gubun == 2 and not self.dict_stgn[종목코드])):
                매입가 = self.df_jg['매입가'][종목코드]
                보유수량 = self.df_jg['보유수량'][종목코드]
                매입금액 = self.df_jg['매입금액'][종목코드]
                분할매수횟수 = int(self.df_jg['분할매수횟수'][종목코드])
                분할매도횟수 = int(self.df_jg['분할매도횟수'][종목코드])
                _, 수익금, 수익률 = GetKiwoomPgSgSp(매입금액, 보유수량 * 현재가)
                매수시간 = strp_time('%Y%m%d%H%M%S', self.df_jg['매수시간'][종목코드])

                if 종목코드 not in self.dict_hilo.keys():
                    self.dict_hilo[종목코드] = [수익률, 수익률]
                else:
                    if 수익률 > self.dict_hilo[종목코드][0]:
                        self.dict_hilo[종목코드][0] = 수익률
                    elif 수익률 < self.dict_hilo[종목코드][1]:
                        self.dict_hilo[종목코드][1] = 수익률
                최고수익률, 최저수익률 = self.dict_hilo[종목코드]
            else:
                수익금, 수익률, 매입가, 보유수량, 분할매수횟수, 분할매도횟수, 매수시간, 최고수익률, 최저수익률 = 0, 0, 0, 0, 0, 0, now(), 0, 0

            BBT = not self.dict_set['주식매수금지시간'] or not (self.dict_set['주식매수금지시작시간'] < 시분초 < self.dict_set['주식매수금지종료시간'])
            BLK = not self.dict_set['주식매수금지블랙리스트'] or 종목코드 not in self.dict_set['주식블랙리스트']
            ING = 종목코드 in self.list_gsjm
            NIB = 종목코드 not in self.list_buy
            NIS = 종목코드 not in self.list_sell

            A = ING and NIB and 매입가 == 0
            B = self.dict_set['주식매수분할시그널']
            C = NIB and 매입가 != 0 and 분할매수횟수 < self.dict_set['주식매수분할횟수']
            D = NIB and self.dict_set['주식매도취소매수시그널'] and not NIS

            if BBT and BLK and (A or (B and C) or C or D):
                매수수량 = 0
                매수시점정보 = [
                    등락율, 고저평균대비등락율, 초당거래대금, 초당거래대금평균, 당일거래대금, 체결강도, 체결강도평균, 최고체결강도, 최저체결강도,
                    현재가, 초당매수수량, 초당매도수량, 매수잔량1, 매도잔량1, 매수총잔량, 매도총잔량, 이평60, 이평300, 이평600, 이평1200
                ]

                if A or (B and C) or C:
                    oc_ratio = dict_order_ratio[self.dict_set['주식매수분할방법']][self.dict_set['주식매수분할횟수']][분할매수횟수]
                    매수수량 = int(self.int_tujagm / (현재가 if 매입가 == 0 else 매입가) * oc_ratio / 100)

                if A or (B and C) or D:
                    매수 = True
                    if 시분초 < self.dict_set['주식장초전략종료시간']:
                        if self.buystrategy1 is not None:
                            try:
                                exec(self.buystrategy1, None, locals())
                            except Exception as e:
                                self.windowQ.put([ui_num['S단순텍스트'], f'시스템 명령 오류 알림 - BuyStrategy1 {e}'])
                    elif self.dict_set['주식장초전략종료시간'] <= 시분초 < self.dict_set['주식장중전략종료시간']:
                        if self.buystrategy2 is not None:
                            if not self.stg_change:
                                self.vars = self.vars2
                                self.stg_change = True
                            try:
                                exec(self.buystrategy2, None, locals())
                            except Exception as e:
                                self.windowQ.put([ui_num['S단순텍스트'], f'시스템 명령 오류 알림 - BuyStrategy2 {e}'])
                elif C:
                    매수 = False
                    분할매수기준수익률 = round((현재가 / self.dict_buyinfo[종목코드][9] - 1) * 100, 2) if self.dict_set['주식매수분할고정수익률'] else 수익률
                    if self.dict_set['주식매수분할하방'] and 분할매수기준수익률 < -self.dict_set['주식매수분할하방수익률']:  매수 = True
                    elif self.dict_set['주식매수분할상방'] and 분할매수기준수익률 > self.dict_set['주식매수분할상방수익률']: 매수 = True

                    if 매수:
                        if '지정가' in self.dict_set['주식매수주문구분']:
                            기준가격 = 현재가
                            if self.dict_set['주식매수지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                            if self.dict_set['주식매수지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                            self.list_buy.append(종목코드)
                            self.straderQ.put(['매수', 종목코드, 종목명, 기준가격, 매수수량, now(), False])
                            self.dict_buyinfo[종목코드] = 매수시점정보
                        else:
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
                                예상체결가 = int(round(매수금액 / 매수수량)) if 매수수량 != 0 else 0
                                self.list_buy.append(종목코드)
                                self.straderQ.put(['매수', 종목코드, 종목명, 예상체결가, 매수수량, now(), False])
                                self.dict_buyinfo[종목코드] = 매수시점정보

            SBT = not self.dict_set['주식매도금지시간'] or not (self.dict_set['주식매도금지시작시간'] < 시분초 < self.dict_set['주식매도금지종료시간'])
            SCC = self.dict_set['주식매수분할횟수'] == 1 or not self.dict_set['주식매도금지매수횟수'] or 분할매수횟수 > self.dict_set['주식매도금지매수횟수값']
            NIB = 종목코드 not in self.list_buy

            A = NIB and NIS and SCC and 매입가 != 0 and self.dict_set['주식매도분할횟수'] == 1
            B = self.dict_set['주식매도분할시그널']
            C = NIB and NIS and SCC and 매입가 != 0 and 분할매도횟수 < self.dict_set['주식매도분할횟수']
            D = NIS and self.dict_set['주식매수취소매도시그널'] and not NIB
            E = NIB and NIS and 매입가 != 0 and self.dict_set['주식매도손절수익률청산'] and 수익률 < -self.dict_set['주식매도손절수익률']
            F = NIB and NIS and 매입가 != 0 and self.dict_set['주식매도손절수익금청산'] and 수익금 < -self.dict_set['주식매도손절수익금']

            if SBT and (A or (B and C) or C or D or E or F):
                매도수량 = 0
                if 종목코드 not in self.dict_buyinfo.keys():
                    self.dict_buyinfo[종목코드] = [
                        등락율, 고저평균대비등락율, 초당거래대금, 초당거래대금평균, 당일거래대금, 체결강도, 체결강도평균, 최고체결강도, 최저체결강도,
                        현재가, 초당매수수량, 초당매도수량, 매수잔량1, 매도잔량1, 매수총잔량, 매도총잔량, 이평60, 이평300, 이평600, 이평1200
                    ]
                매수시점등락율, 매수시점고저평균대비등락율, 매수시점초당거래대금, 매수시점초당거래대금평균, 매수시점당일거래대금, 매수시점체결강도, \
                    매수시점체결강도평균, 매수시점최고체결강도, 매수시점최저체결강도, 매수시점현재가, 매수시점초당매수수량, 매수시점초당매도수량, \
                    매수시점매수잔량1, 매수시점매도잔량1, 매수시점매수총잔량, 매수시점매도총잔량, 매수시점이평60, 매수시점이평300, \
                    매수시점이평600, 매수시점이평1200 = self.dict_buyinfo[종목코드]

                if A or E or F:
                    매도수량 = 보유수량
                elif (B and C) or C:
                    oc_ratio = dict_order_ratio[self.dict_set['주식매도분할방법']][self.dict_set['주식매도분할횟수']][분할매도횟수]
                    매도수량 = int(self.int_tujagm / 매입가 * oc_ratio / 100)
                    if 매도수량 > 보유수량 or 분할매도횟수 + 1 == self.dict_set['주식매도분할횟수']: 매도수량 = 보유수량

                if A or (B and C) or D:
                    매도 = False
                    if 시분초 < self.dict_set['주식장초전략종료시간']:
                        if self.sellstrategy1 is not None:
                            try:
                                exec(self.sellstrategy1, None, locals())
                            except Exception as e:
                                self.windowQ.put([ui_num['S단순텍스트'], f'시스템 명령 오류 알림 - SellStrategy1 {e}'])
                    elif self.dict_set['주식장초전략종료시간'] <= 시분초 < self.dict_set['주식장중전략종료시간']:
                        if self.sellstrategy2 is not None:
                            try:
                                exec(self.sellstrategy2, None, locals())
                            except Exception as e:
                                self.windowQ.put([ui_num['S단순텍스트'], f'시스템 명령 오류 알림 - SellStrategy2 {e}'])
                elif C or E or F:
                    매도 = False
                    if E or F:
                        매도 = True
                    elif C:
                        if self.dict_set['주식매도분할하방'] and 수익률 < -self.dict_set['주식매도분할하방수익률'] * (분할매도횟수 + 1):  매도 = True
                        elif self.dict_set['주식매도분할상방'] and 수익률 > self.dict_set['주식매도분할상방수익률'] * (분할매도횟수 + 1): 매도 = True

                    if 매도:
                        if '지정가' in self.dict_set['주식매도주문구분'] and not (E or F):
                            기준가격 = 현재가
                            if self.dict_set['주식매도지정가기준가격'] == '매도1호가': 기준가격 = 매도호가1
                            if self.dict_set['주식매도지정가기준가격'] == '매수1호가': 기준가격 = 매수호가1
                            self.list_sell.append(종목코드)
                            self.straderQ.put(['매도', 종목코드, 종목명, 기준가격, 매도수량, now(), False])
                        else:
                            남은수량 = 매도수량
                            직전남은수량 = 매도수량
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
                                예상체결가 = int(round(매도금액 / 매도수량)) if 매도수량 != 0 else 0
                                self.list_sell.append(종목코드)
                                self.straderQ.put(['매도', 종목코드, 종목명, 예상체결가, 매도수량, now(), True if E or F else False])

        new_data_tick = [
            체결시간, 이평60, 이평300, 이평600, 이평1200, 현재가, 체결강도, 체결강도평균, 최고체결강도, 최저체결강도, 초당거래대금,
            초당거래대금평균, 초당매수수량, 초당매도수량, 등락율, 고저평균대비등락율, 매수총잔량, 매도총잔량, 매수잔량1, 매도잔량1,
            매도수5호가잔량합, 당일거래대금, 누적초당매수수량(평균값계산틱수), 누적초당매도수량(평균값계산틱수), 당일거래대금각도(평균값계산틱수),
            전일비각도(평균값계산틱수), 거래대금증감, 전일비, 회전율, 전일동시간비, 고가, 저가
        ]

        if 종목코드 not in self.dict_tik_ar.keys():
            self.dict_tik_ar[종목코드] = np.array([new_data_tick])
        else:
            self.dict_tik_ar[종목코드] = np.r_[self.dict_tik_ar[종목코드], np.array([new_data_tick])]
            if len(self.dict_tik_ar[종목코드]) > 1800:
                self.dict_tik_ar[종목코드] = np.delete(self.dict_tik_ar[종목코드], 0, 0)

        if 종목코드 in self.list_gsjm:
            self.df_gj.loc[종목코드] = 종목명, 등락율, 고저평균대비등락율, 초당거래대금, 초당거래대금평균, 당일거래대금, 체결강도, 체결강도평균, 최고체결강도

        if len(self.dict_tik_ar[종목코드]) >= 평균값계산틱수 and self.chart_code == 종목코드:
            self.windowQ.put([ui_num['실시간차트'], 종목명, self.dict_tik_ar[종목코드]])

        if 틱수신시간 != 0:
            gap = (now() - 틱수신시간).total_seconds()
            self.windowQ.put([ui_num['S단순텍스트'], f'전략스 연산 시간 알림 - 수신시간과 연산시간의 차이는 [{gap:.6f}]초입니다.'])

    def PutGsjmAndDeleteHilo(self):
        if len(self.df_gj) > 0:
            self.windowQ.put([ui_num[f'S관심종목{self.gubun}'], self.df_gj.copy()])
        if len(self.dict_hilo) > 0:
            for code in list(self.dict_hilo.keys()):
                if code not in self.df_jg.index:
                    del self.dict_hilo[code]
