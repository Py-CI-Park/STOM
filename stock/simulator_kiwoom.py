import sqlite3
import pandas as pd
from utility.setting import ui_num, columns_cj, columns_tj, columns_jg, columns_td, columns_tt, DICT_SET, DB_STOCK_BACK
from utility.static import now, strf_time, strp_time, timedelta_sec, roundfigure_lower, roundfigure_upper, int_hms, GetKiwoomPgSgSp


class ReceiverKiwoom2:
    def __init__(self, qlist):
        """
           0        1       2      3       4      5      6       7         8        9       10       11        12
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, sreceivQ, straderQ, sstg1Q, sstg2Q, creceivQ, ctraderQ,
        cstgQ, tick1Q, tick2Q, tick3Q, tick4Q, tick5Q, tick6Q, tick7Q, tick8Q, tick9Q, liveQ, backQ, kimpQ
         13      14      15      16      17      18      19      20      21      22     23     24     25
        """
        self.hogaQ     = qlist[5]
        self.sreceivQ  = qlist[7]
        self.straderQ  = qlist[8]
        self.sstg1Q    = qlist[9]
        self.dict_name = {}
        self.list_jang = []
        self.LoadCodename()
        self.Start()

    def Start(self):
        while True:
            data = self.sreceivQ.get()
            if type(data) == list:
                if len(data) != 2:
                    self.UpdateTestMode(data)
                else:
                    self.UpdateList(data)

    def LoadCodename(self):
        con = sqlite3.connect(DB_STOCK_BACK)
        df_cn = pd.read_sql('SELECT * FROM codename', con).set_index('index')
        con.close()
        self.dict_name = df_cn['종목명'].to_dict()
        dict_sgbn = {code: 1 for code, _ in self.dict_name.items()}
        list_kosd = list(df_cn[df_cn['코스닥'] == 1].index)
        self.sstg1Q.put(dict_sgbn)
        self.sstg1Q.put(['코스닥목록', list_kosd])

    def UpdateTestMode(self, data):
        code = data[-1]
        c, o, h, low, per, _, ch, _, _, _, _, sgta, _, bids, asks, vitime, uvi = data[1:18]
        data[16] = strp_time('%Y%m%d%H%M%S', str(int(vitime)))
        hogadata = data[21:43]
        name = self.dict_name[code]
        self.sstg1Q.put(data + [now(), name])
        if code in self.list_jang:
            self.straderQ.put([code, c])
        self.hogaQ.put([name, c, per, sgta, uvi, o, h, low])
        self.hogaQ.put([bids, ch])
        self.hogaQ.put([-asks, ch])
        self.hogaQ.put([name] + hogadata + [0, 0])

    def UpdateList(self, data):
        gubun, data = data
        self.list_jang = data


class TraderKiwoom2:
    def __init__(self, qlist):
        """
           0        1       2      3       4      5      6       7         8        9       10       11        12
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, sreceivQ, straderQ, sstg1Q, sstg2Q, creceivQ, ctraderQ,
        cstgQ, tick1Q, tick2Q, tick3Q, tick4Q, tick5Q, tick6Q, tick7Q, tick8Q, tick9Q, liveQ, backQ, kimpQ
         13      14      15      16      17      18      19      20      21      22     23     24     25
        """
        self.windowQ  = qlist[0]
        self.soundQ   = qlist[1]
        self.sreceivQ = qlist[7]
        self.straderQ = qlist[8]
        self.sstg1Q   = qlist[9]
        self.dict_set = DICT_SET

        self.df_cj = pd.DataFrame(columns=columns_cj)
        self.df_jg = pd.DataFrame(columns=columns_jg)
        self.df_tj = pd.DataFrame(columns=columns_tj)
        self.df_td = pd.DataFrame(columns=columns_td)
        self.df_tt = pd.DataFrame(columns=columns_tt)

        self.dict_buy  = {}
        self.dict_sell = {}
        self.dict_name = {}
        self.dict_curc = {}
        self.dict_intg = {
            '예수금': 0,
            '추정예수금': 0,
            '추정예탁자산': 0,
            '종목당투자금': 0
        }
        self.dict_strg = {
            '당일날짜': strf_time('%Y%m%d')
        }
        curr_time = now()
        self.dict_time = {
            '계좌평가계산': curr_time,
            '잔고목록전송': curr_time
        }
        self.int_hgtime = int(strf_time('%Y%m%d%H%M%S'))
        self.test_mode  = False
        self.test_time  = None

        self.LoadCodename()
        self.GetAccountjanGo()
        self.Start()

    def Start(self):
        while True:
            data = self.straderQ.get()
            if type(data) == list:
                self.UpdateList(data)
            elif type(data) == dict:
                self.UpdateDictset(data)
            elif type(data) == str:
                self.UpdateStr(data)

            curr_time = now()
            if curr_time > self.dict_time['계좌평가계산']:
                inthms = int_hms()
                self.UpdateTotaljango(inthms)
                self.dict_time['계좌평가계산'] = timedelta_sec(1)
            if curr_time > self.dict_time['잔고목록전송']:
                self.sstg1Q.put(self.df_jg.copy())
                self.dict_time['잔고목록전송'] = timedelta_sec(0.5)

    def LoadCodename(self):
        con = sqlite3.connect(DB_STOCK_BACK)
        df_cn = pd.read_sql('SELECT * FROM codename', con).set_index('index')
        con.close()
        self.dict_name = df_cn['종목명'].to_dict()
        dummy_time = timedelta_sec(-3600)
        self.dict_name = {key: [value, dummy_time, dummy_time, dummy_time] for key, value in self.dict_name.items()}

    def GetAccountjanGo(self):
        self.dict_intg['예수금'] = self.dict_intg['추정예수금'] = self.dict_intg['추정예탁자산'] = 100_000_000
        self.df_tj.loc[self.dict_strg['당일날짜']] = self.dict_intg['추정예탁자산'], self.dict_intg['예수금'], 0, 0, 0, 0, 0

    def UpdateList(self, data):
        if len(data) == 7:
            self.CheckOrder(data[0], data[1], data[2], data[3], data[4])
        elif len(data) == 2:
            code, c = data
            self.dict_curc[code] = c
            try:
                if c != self.df_jg['현재가'][code]:
                    jg = self.df_jg['매입금액'][code]
                    jc = int(self.df_jg['보유수량'][code])
                    pg, sg, sp = GetKiwoomPgSgSp(jg, jc * c)
                    columns = ['현재가', '수익률', '평가손익', '평가금액']
                    self.df_jg.loc[code, columns] = c, sp, sg, pg
            except:
                pass

    def UpdateDictset(self, data):
        self.dict_set = data

    def UpdateStr(self, data):
        self.test_time  = data.split(' ')[1]
        self.int_hgtime = int(self.test_time)

    def CheckOrder(self, gubun, code, name, op, oc):
        NIJ = code not in self.df_jg.index
        INB = code in self.dict_buy.keys()
        INS = code in self.dict_sell.keys()

        on = ''
        cancel = False
        curr_time = now()
        if gubun == '매수':
            df1 = self.df_td[self.df_td['종목명'] == name]
            df2 = self.df_td[(self.df_td['종목명'] == name) & (self.df_td['수익률'] < 0)]
            if self.dict_set['주식매수금지거래횟수'] and self.dict_set['주식매수금지거래횟수값'] <= len(df1):
                cancel = True
            elif self.dict_set['주식매수금지손절횟수'] and self.dict_set['주식매수금지손절횟수값'] <= len(df2):
                cancel = True
            elif self.dict_set['주식매수금지간격'] and curr_time < self.dict_name[code][2]:
                cancel = True
            elif self.dict_set['주식매수금지손절간격'] and curr_time < self.dict_name[code][3]:
                cancel = True
            elif not NIJ and self.df_jg['분할매수횟수'][code] >= self.dict_set['주식매수분할횟수']:
                cancel = True
            elif self.dict_intg['추정예수금'] < oc * op:
                if code not in self.dict_name.keys() or curr_time > self.dict_name[code][1]:
                    self.CreateOrder('시드부족', code, name, op, oc, '')
                    self.dict_name[code][1] = timedelta_sec(180)
                cancel = True
            elif INB:
                cancel = True
        elif gubun == '매도':
            if NIJ or INS:
                cancel = True
            elif self.dict_set['주식매도금지간격'] and curr_time < self.dict_name[code][2]:
                cancel = True

        if cancel:
            self.PutOrderComplete(f'{gubun}취소', code)
        elif oc > 0:
            self.CreateOrder(gubun, code, name, op, oc, on)

    def CreateOrder(self, gubun, code, name, op, oc, on):
        cancel = False
        if gubun == '매수':
            if self.dict_set['주식매수금지라운드피겨'] and roundfigure_upper(op, self.dict_set['주식매수금지라운드호가'], self.int_hgtime):
                cancel = True
        elif gubun == '매도':
            if self.dict_set['주식매도금지라운드피겨'] and roundfigure_lower(op, self.dict_set['주식매도금지라운드호가'], self.int_hgtime):
                cancel = True
        elif gubun == '매수정정':
            if self.dict_set['주식매수금지라운드피겨'] and roundfigure_upper(op, self.dict_set['주식매수금지라운드호가'], self.int_hgtime):
                cancel = True
        elif gubun == '매도정정':
            if self.dict_set['주식매도금지라운드피겨'] and roundfigure_lower(op, self.dict_set['주식매도금지라운드호가'], self.int_hgtime):
                cancel = True

        if cancel:
            self.PutOrderComplete(f'{gubun}취소', code)
        elif oc > 0:
            ct = self.test_time
            if gubun == '시드부족':
                self.UpdateChejanData(code, name, '체결', gubun, oc, 0, oc, op, 0, ct, on)
            else:
                self.UpdateChejanData(code, name, '체결', gubun, oc, oc, 0, op, op, ct, on)

    def UpdateChejanData(self, code, name, ot, og, oc, cc, mc, op, cp, ct, on):
        index = strf_time('%Y%m%d%H%M%S%f')
        if index in self.df_cj.index:
            while index in self.df_cj.index:
                index = str(int(index) + 1)

        if ot == '체결' and og in ['매수', '매도']:
            if og == '매수':
                if code in self.df_jg.index:
                    jc = self.df_jg['보유수량'][code] + cc
                    jg = self.df_jg['매입금액'][code] + cc * cp
                    jp = int(round(jg / jc))
                    pg, sg, sp = GetKiwoomPgSgSp(jg, jc * cp)
                    columns = ['매입가', '현재가', '수익률', '평가손익', '매입금액', '평가금액', '보유수량', '매수시간']
                    self.df_jg.loc[code, columns] = jp, cp, sp, sg, jg, pg, jc, ct
                else:
                    jc = cc
                    jg = cc * cp
                    jp = cp
                    pg, sg, sp = GetKiwoomPgSgSp(jg, jc * cp)
                    self.df_jg.loc[code] = name, jp, cp, sp, sg, jg, pg, jc, 0, 0, ct

                if mc == 0:
                    self.df_jg.loc[code, '분할매수횟수'] = self.df_jg['분할매수횟수'][code] + 1
                    if code in self.dict_buy.keys():
                        del self.dict_buy[code]

            else:
                if code not in self.df_jg.index:
                    return

                jc = self.df_jg['보유수량'][code] - cc
                jp = self.df_jg['매입가'][code]
                if jc != 0:
                    jg = jp * jc
                    pg, sg, sp = GetKiwoomPgSgSp(jg, jc * cp)
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
                pg, sg, sp = GetKiwoomPgSgSp(jg, cc * cp)
                self.UpdateTradelist(index, name, jg, pg, cc, sp, sg, ct)

                if sp < 0:
                    self.dict_name[code][3] = timedelta_sec(self.dict_set['주식매수금지손절간격초'])

            columns = ['매입가', '현재가', '평가손익', '매입금액', '평가금액', '보유수량', '분할매수횟수', '분할매도횟수']
            self.df_jg[columns] = self.df_jg[columns].astype(int)
            self.df_jg.sort_values(by=['매입금액'], ascending=False, inplace=True)

            self.sstg1Q.put(self.df_jg.copy())
            if mc == 0:
                self.PutOrderComplete(og + '완료', code)

            self.UpdateChegeollist(index, code, name, og, oc, cc, mc, cp, ct, op, on)

            if og == '매수':
                self.dict_intg['예수금'] -= cc * cp
            else:
                self.dict_intg['예수금'] += jg + sg
                self.dict_intg['추정예수금'] += jg + sg

            if self.dict_set['주식알림소리']:
                self.soundQ.put(f'{name} {cc}주를 {og}하였습니다')
            self.windowQ.put([ui_num['S로그텍스트'], f'주문 관리 시스템 알림 - [{ot}] {name} | {cp} | {cc} | {og}'])

        elif ot == '체결' and og == '시드부족':
            self.UpdateChegeollist(index, code, name, og, oc, cc, mc, cp, ct, op, on)

        self.sreceivQ.put(['잔고목록', list(self.df_jg.index)])

    def UpdateTradelist(self, index, name, jg, pg, cc, sp, sg, ct):
        self.df_td.loc[index] = name, jg, pg, cc, sp, sg, ct
        self.windowQ.put([ui_num['S거래목록'], self.df_td[::-1]])
        self.UpdateTotaltradelist()

    def UpdateTotaltradelist(self):
        tdt = len(self.df_td)
        tbg = self.df_td['매수금액'].sum()
        tsg = self.df_td['매도금액'].sum()
        sig = self.df_td[self.df_td['수익금'] > 0]['수익금'].sum()
        ssg = self.df_td[self.df_td['수익금'] < 0]['수익금'].sum()
        sg  = self.df_td['수익금'].sum()
        sp  = round(sg / self.dict_intg['추정예탁자산'] * 100, 2)
        self.df_tt = pd.DataFrame([[tdt, tbg, tsg, sig, ssg, sp, sg]], columns=columns_tt, index=[self.dict_strg['당일날짜']])
        self.windowQ.put([ui_num['S실현손익'], self.df_tt])

    def UpdateChegeollist(self, index, code, name, og, oc, cc, mc, cp, ct, op, on):
        self.dict_name[code][2] = timedelta_sec(self.dict_set['주식매수금지간격초'])
        self.df_cj.loc[index] = name, og, oc, cc, mc, cp, ct, op, on
        self.windowQ.put([ui_num['S체결목록'], self.df_cj[::-1]])

    def UpdateTotaljango(self, inthms):
        if len(self.df_jg) > 0:
            tsg = self.df_jg['평가손익'].sum()
            tbg = self.df_jg['매입금액'].sum()
            tpg = self.df_jg['평가금액'].sum()
            bct = len(self.df_jg)
            tsp = round(tsg / tbg * 100, 2)
            ttg = self.dict_intg['예수금'] + tpg
            self.df_tj.loc[self.dict_strg['당일날짜']] = ttg, self.dict_intg['예수금'], bct, tsp, tsg, tbg, tpg
        else:
            self.df_tj.loc[self.dict_strg['당일날짜']] = self.dict_intg['예수금'], self.dict_intg['예수금'], 0, 0.0, 0, 0, 0

        self.windowQ.put([ui_num['S잔고목록'], self.df_jg.copy()])
        self.windowQ.put([ui_num['S잔고평가'], self.df_tj.copy()])

        if self.dict_set['주식투자금고정']:
            if inthms < self.dict_set['주식장초전략종료시간']:
                tujagm = int(self.dict_set['주식장초투자금'] * 1_000_000)
            else:
                tujagm = int(self.dict_set['주식장중투자금'] * 1_000_000)
        else:
            if inthms < self.dict_set['주식장초전략종료시간']:
                if '시장가' in self.dict_set['주식매수주문구분']:
                    tujagm = int((self.dict_intg['추정예탁자산'] - self.dict_intg['추정예탁자산'] / self.dict_set['주식장초최대매수종목수'] * 0.3) / self.dict_set['주식장초최대매수종목수'])
                else:
                    tujagm = int(self.dict_intg['추정예탁자산'] * 0.98 / self.dict_set['주식장초최대매수종목수'])
            else:
                if '시장가' in self.dict_set['주식매수주문구분']:
                    tujagm = int((self.dict_intg['추정예탁자산'] - self.dict_intg['추정예탁자산'] / self.dict_set['주식장중최대매수종목수'] * 0.3) / self.dict_set['주식장중최대매수종목수'])
                else:
                    tujagm = int(self.dict_intg['추정예탁자산'] * 0.98 / self.dict_set['주식장중최대매수종목수'])

        if self.dict_intg['종목당투자금'] != tujagm:
            self.dict_intg['종목당투자금'] = tujagm
            self.sstg1Q.put(self.dict_intg['종목당투자금'])

    def PutOrderComplete(self, cmsg, code):
        self.sstg1Q.put([cmsg, code])
