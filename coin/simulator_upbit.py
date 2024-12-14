import pyupbit
import pandas as pd
from utility.static import now, strf_time, timedelta_sec, int_hms_utc, GetUpbitPgSgSp
from utility.setting import columns_cj, columns_tj, columns_jg, columns_td, columns_tt, ui_num, DICT_SET


class ReceiverUpbit2:
    def __init__(self, qlist):
        """
           0        1       2      3       4      5      6       7         8        9       10       11        12
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, sreceivQ, straderQ, sstg1Q, sstg2Q, creceivQ, ctraderQ,
        cstgQ, tick1Q, tick2Q, tick3Q, tick4Q, tick5Q, tick6Q, tick7Q, tick8Q, tick9Q, liveQ, backQ, kimpQ
         13      14      15      16      17      18      19      20      21      22     23     24     25
        """
        self.hogaQ     = qlist[5]
        self.creceivQ  = qlist[11]
        self.ctraderQ  = qlist[12]
        self.cstgQ     = qlist[13]
        self.dict_set  = DICT_SET
        self.list_jang = []
        self.Start()

    def Start(self):
        while True:
            data = self.creceivQ.get()
            if type(data) == list:
                if len(data) != 2:
                    self.UpdateTestMode(data)
                else:
                    self.UpdateList(data)

    def UpdateTestMode(self, data):
        code = data[-1]
        c, o, h, low, per, _, ch, bids, asks = data[1:10]
        hogadata = data[12:34]
        self.cstgQ.put(data + [now()])
        if code in self.list_jang:
            self.ctraderQ.put([code, c])
        self.hogaQ.put([code, c, per, 0, 0, o, h, low])
        self.hogaQ.put([bids, ch])
        self.hogaQ.put([-asks, ch])
        self.hogaQ.put([code] + hogadata + [0, 0])

    def UpdateList(self, data):
        gubun, list_ = data
        self.list_jang = list_


class TraderUpbit2:
    def __init__(self, qlist):
        """
           0        1       2      3       4      5      6       7         8        9       10       11        12
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, sreceivQ, straderQ, sstg1Q, sstg2Q, creceivQ, ctraderQ,
        cstgQ, tick1Q, tick2Q, tick3Q, tick4Q, tick5Q, tick6Q, tick7Q, tick8Q, tick9Q, liveQ, backQ, kimpQ
         13      14      15      16      17      18      19      20      21      22     23     24     25
        """
        self.windowQ  = qlist[0]
        self.soundQ   = qlist[1]
        self.creceivQ = qlist[11]
        self.ctraderQ = qlist[12]
        self.cstgQ    = qlist[13]
        self.dict_set = DICT_SET

        self.df_cj = pd.DataFrame(columns=columns_cj)
        self.df_jg = pd.DataFrame(columns=columns_jg)
        self.df_tj = pd.DataFrame(columns=columns_tj)
        self.df_td = pd.DataFrame(columns=columns_td)
        self.df_tt = pd.DataFrame(columns=columns_tt)

        self.dict_name = {}
        self.dict_curc = {}
        self.dict_buy  = {}
        self.dict_sell = {}

        self.str_today = strf_time('%Y%m%d', timedelta_sec(-32400))
        self.dict_intg = {
            '예수금': 0,
            '추정예수금': 0,
            '추정예탁자산': 0,
            '종목당투자금': 0
        }
        curr_time = now()
        self.dict_time = {
            '계좌평가계산': curr_time,
            '잔고목록전송': curr_time
        }
        self.UpdateDictName()
        self.GetBalances()
        self.Start()

    def Start(self):
        while True:
            data = self.ctraderQ.get()
            if type(data) == list:
                self.UpdateList(data)
            elif type(data) == dict:
                self.dict_set = data

            curr_time = now()
            if curr_time > self.dict_time['계좌평가계산']:
                inthmsutc = int_hms_utc()
                self.UpdateTotaljango(inthmsutc)
                self.dict_time['계좌평가계산'] = timedelta_sec(1)
            if curr_time > self.dict_time['잔고목록전송']:
                self.cstgQ.put(self.df_jg.copy())
                self.dict_time['잔고목록전송'] = timedelta_sec(0.5)

    def UpdateDictName(self):
        for dict_ticker in pyupbit.get_tickers(fiat="KRW", verbose=True):
            code = dict_ticker['market']
            name = dict_ticker['korean_name']
            if code not in self.dict_name.keys():
                dummy_time = timedelta_sec(-3600)
                self.dict_name[code] = [name, dummy_time, dummy_time, dummy_time]

    def GetBalances(self):
        self.dict_intg['예수금'] = self.dict_intg['추정예수금'] = self.dict_intg['추정예탁자산'] = 100_000_000

    def UpdateList(self, data):
        if len(data) == 6:
            self.CheckOrder(data[0], data[1], data[2], data[3])
        elif len(data) == 2:
            code, c = data
            self.dict_curc[code] = c
            try:
                if code in self.df_jg.index and c != self.df_jg['현재가'][code]:
                    jg = self.df_jg['매입금액'][code]
                    jc = self.df_jg['보유수량'][code]
                    pg, sg, sp = GetUpbitPgSgSp(jg, jc * c)
                    columns = ['현재가', '수익률', '평가손익', '평가금액']
                    self.df_jg.loc[code, columns] = c, sp, sg, pg
            except:
                pass

    def CheckOrder(self, og, code, op, oc):
        NIJ = code not in self.df_jg.index
        INB = code in self.dict_buy.keys()
        INS = code in self.dict_sell.keys()

        cancel = False
        curr_time = now()
        if og == '매수':
            inthmsutc = int_hms_utc()
            df1 = self.df_td[self.df_td['종목명'] == code]
            df2 = self.df_td[(self.df_td['종목명'] == code) & (self.df_td['수익률'] < 0)]
            if self.dict_set['코인매수금지거래횟수'] and self.dict_set['코인매수금지거래횟수값'] <= len(df1):
                cancel = True
            elif self.dict_set['코인매수금지손절횟수'] and self.dict_set['코인매수금지손절횟수값'] <= len(df2):
                cancel = True
            elif NIJ and inthmsutc < self.dict_set['코인장초전략종료시간'] and len(self.df_jg) >= self.dict_set['코인장초최대매수종목수']:
                cancel = True
            elif NIJ and inthmsutc > self.dict_set['코인장초전략종료시간'] and len(self.df_jg) >= self.dict_set['코인장중최대매수종목수']:
                cancel = True
            elif self.dict_set['코인매수금지간격'] and curr_time < self.dict_name[code][2]:
                cancel = True
            elif self.dict_set['코인매수금지손절간격'] and curr_time < self.dict_name[code][3]:
                cancel = True
            elif not NIJ and self.df_jg['분할매수횟수'][code] >= self.dict_set['코인매수분할횟수']:
                cancel = True
            elif self.dict_intg['추정예수금'] < oc * op:
                if curr_time > self.dict_name[code][1]:
                    self.CreateOrder('시드부족', code, op, oc)
                    self.dict_name[code][1] = timedelta_sec(180)
                cancel = True
            elif INB:
                cancel = True
        elif og == '매도':
            if NIJ or INS:
                cancel = True
            elif self.dict_set['코인매도금지간격'] and curr_time < self.dict_time[code][2]:
                cancel = True

        if cancel:
            if '취소' not in og:
                self.cstgQ.put([f'{og}취소', code])
        else:
            if oc > 0:
                self.CreateOrder(og, code, op, oc)
            else:
                self.cstgQ.put([f'{og}취소', code])

    def CreateOrder(self, og, code, op, oc):
        if oc > 0:
            if self.dict_set['코인모의투자'] or og == '시드부족':
                if og == '시드부족':
                    self.UpdateChejanData(og, code, oc, 0, oc, op, 0, '')
                else:
                    self.UpdateChejanData(og, code, oc, oc, 0, op, op, '')

    def UpdateChejanData(self, gubun, code, oc, cc, mc, cp, op, on):
        dt = self.GetIndex()

        if gubun in ['매수', '매도']:
            if gubun == '매수':
                if code in self.df_jg.index:
                    jc = round(self.df_jg['보유수량'][code] + cc, 8)
                    jg = int(self.df_jg['매입금액'][code] + cc * cp)
                    jp = round(jg / jc, 4)
                    pg, sg, sp = GetUpbitPgSgSp(jg, jc * cp)
                    columns = ['매입가', '현재가', '수익률', '평가손익', '매입금액', '평가금액', '보유수량', '매수시간']
                    self.df_jg.loc[code, columns] = jp, cp, sp, sg, jg, pg, jc, dt[:14]
                else:
                    jc = cc
                    jg = int(cc * cp)
                    jp = cp
                    pg, sg, sp = GetUpbitPgSgSp(jg, jc * cp)
                    self.df_jg.loc[code] = code, jp, cp, sp, sg, jg, pg, jc, 0, 0, dt[:14]

                if mc == 0:
                    self.df_jg.loc[code, '분할매수횟수'] = self.df_jg['분할매수횟수'][code] + 1
                    if code in self.dict_buy.keys():
                        del self.dict_buy[code]

            else:
                jc = round(self.df_jg['보유수량'][code] - cc, 8)
                jp = self.df_jg['매입가'][code]
                if jc != 0:
                    jg = int(jp * jc)
                    pg, sg, sp = GetUpbitPgSgSp(jg, jc * cp)
                    columns = ['현재가', '수익률', '평가손익', '매입금액', '평가금액', '보유수량']
                    self.df_jg.loc[code, columns] = cp, sp, sg, jg, pg, jc
                else:
                    self.df_jg.drop(index=code, inplace=True)

                if mc == 0:
                    if jc > 0:
                        self.df_jg.loc[code, '분할매도횟수'] = self.df_jg['분할매도횟수'][code] + 1
                    if code in self.dict_sell.keys():
                        del self.dict_sell[code]

                jg = jp * cc
                pg, sg, sp = GetUpbitPgSgSp(jg, cc * cp)
                self.UpdateTradelist(dt, code, jg, pg, cc, sp, sg, dt[:14])

                if sp < 0:
                    self.dict_name[code][3] = timedelta_sec(self.dict_set['코인매수금지손절간격초'])

            columns = ['평가손익', '매입금액', '평가금액', '분할매수횟수', '분할매도횟수']
            self.df_jg[columns] = self.df_jg[columns].astype(int)
            self.df_jg.sort_values(by=['매입금액'], ascending=False, inplace=True)
            self.cstgQ.put(self.df_jg.copy())

            if mc == 0:
                self.cstgQ.put([gubun + '완료', code])

            self.UpdateChegeollist(dt, code, gubun, oc, cc, mc, cp, dt[:14], op, on)

            if gubun == '매수':
                self.dict_intg['예수금'] -= int(cc * cp)
            else:
                self.dict_intg['예수금'] += jg + sg
                self.dict_intg['추정예수금'] += jg + sg

            if self.dict_set['코인알림소리']:
                self.soundQ.put(f'{self.dict_name[code][0]}을 {gubun}하였습니다.')
            self.windowQ.put([ui_num['C로그텍스트'], f'주문 관리 시스템 알림 - [체결] {code} | {cp} | {cc} | {gubun}'])

        elif gubun == '시드부족':
            self.UpdateChegeollist(dt, code, gubun, oc, cc, mc, cp, dt[:14], op, on)

        self.creceivQ.put(['잔고목록', list(self.df_jg.index)])

    def UpdateTradelist(self, index, code, jg, pg, cc, sp, sg, ct):
        self.df_td.loc[index] = code, jg, pg, cc, sp, sg, ct
        self.windowQ.put([ui_num['C거래목록'], self.df_td[::-1]])
        self.UpdateTotaltradelist()

    def UpdateTotaltradelist(self):
        tdt = len(self.df_td)
        tbg = self.df_td['매수금액'].sum()
        tsg = self.df_td['매도금액'].sum()
        sig = self.df_td[self.df_td['수익금'] > 0]['수익금'].sum()
        ssg = self.df_td[self.df_td['수익금'] < 0]['수익금'].sum()
        sg  = self.df_td['수익금'].sum()
        sp  = round(sg / self.dict_intg['추정예탁자산'] * 100, 2)
        self.df_tt = pd.DataFrame([[tdt, tbg, tsg, sig, ssg, sp, sg]], columns=columns_tt, index=[self.str_today])
        self.windowQ.put([ui_num['C실현손익'], self.df_tt])

    def UpdateChegeollist(self, index, code, gubun, oc, cc, mc, cp, dt, op, on):
        self.dict_name[code][2] = timedelta_sec(self.dict_set['코인매수금지간격초'])
        self.df_cj.loc[index] = code, gubun, oc, cc, mc, cp, dt, op, on
        self.windowQ.put([ui_num['C체결목록'], self.df_cj[::-1]])

    def UpdateTotaljango(self, inthmsutc):
        if len(self.df_jg) > 0:
            tsg = self.df_jg['평가손익'].sum()
            tbg = self.df_jg['매입금액'].sum()
            tpg = self.df_jg['평가금액'].sum()
            bct = len(self.df_jg)
            tsp = round(tsg / tbg * 100, 2)
            self.dict_intg['추정예탁자산'] = self.dict_intg['예수금'] + tpg
            self.df_tj = pd.DataFrame([[self.dict_intg['추정예탁자산'], self.dict_intg['예수금'], bct, tsp, tsg, tbg, tpg]], columns=columns_tj, index=[self.str_today])
        else:
            self.df_tj = pd.DataFrame([[self.dict_intg['추정예탁자산'], self.dict_intg['예수금'], 0, 0.0, 0, 0, 0]], columns=columns_tj, index=[self.str_today])

        if self.dict_set['코인투자금고정']:
            if inthmsutc < self.dict_set['코인장초전략종료시간']:
                tujagm = int(self.dict_set['코인장초투자금'] * 1_000_000)
            else:
                tujagm = int(self.dict_set['코인장중투자금'] * 1_000_000)
        else:
            if inthmsutc < self.dict_set['코인장초전략종료시간']:
                tujagm = int(self.dict_intg['추정예탁자산'] * 0.98 / self.dict_set['코인장초최대매수종목수'])
            else:
                tujagm = int(self.dict_intg['추정예탁자산'] * 0.98 / self.dict_set['코인장중최대매수종목수'])

        if self.dict_intg['종목당투자금'] != tujagm:
            self.dict_intg['종목당투자금'] = tujagm
            self.cstgQ.put(self.dict_intg['종목당투자금'])

        self.windowQ.put([ui_num['C잔고목록'], self.df_jg.copy()])
        self.windowQ.put([ui_num['C잔고평가'], self.df_tj.copy()])

    def GetIndex(self):
        dt = strf_time('%Y%m%d%H%M%S%f', timedelta_sec(-32400))
        if dt in self.df_cj.index:
            while dt in self.df_cj.index:
                dt = str(int(dt) + 1)
        return dt
