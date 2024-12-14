import os
import sqlite3
import numpy as np
import pandas as pd
from utility.static import now, timedelta_sec
from utility.setting import ui_num, columns_hj, DB_PATH, DB_COIN_TICK, DB_STOCK_TICK, DB_COIN_BACK, DB_STOCK_BACK


class Hoga:
    def __init__(self, qlist):
        """
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ,  cstgQ, liveQ, kimpQ, wdservQ
           0        1       2      3       4      5      6      7       8         9         10     11    12      13
        """
        self.windowQ   = qlist[0]
        self.hogaQ     = qlist[5]
        self.hoga_name = None
        self.df_hj     = None
        self.df_hc     = None
        self.df_hg     = None
        self.bool_hjup = False
        self.bool_hcup = False
        self.bool_hgup = False
        self.time_uphg = now()
        self.InitHoga('S')
        self.Start()

    def Start(self):
        while True:
            data = self.hogaQ.get()
            if len(data) == 8:
                self.UpdateHogaJongmok(data)
            elif len(data) == 2:
                self.UpdateChegeolcount(data)
            elif len(data) == 4:
                self.UpdateHogaForChart(data)
            else:
                self.UpdateHogajalryang(data)

            if now() > self.time_uphg:
                if self.bool_hjup and self.df_hc is not None:
                    if 'KRW' in self.hoga_name or 'USDT' in self.hoga_name:
                        self.windowQ.put([ui_num['C호가종목'], self.df_hj])
                    else:
                        self.windowQ.put([ui_num['S호가종목'], self.df_hj])
                    self.bool_hjup = False
                if self.bool_hcup and self.df_hc is not None:
                    if 'KRW' in self.hoga_name or 'USDT' in self.hoga_name:
                        self.windowQ.put([ui_num['C호가체결'], self.df_hc])
                    else:
                        self.windowQ.put([ui_num['S호가체결'], self.df_hc])
                    self.bool_hcup = False
                if self.bool_hgup and self.df_hg is not None:
                    if 'KRW' in self.hoga_name or 'USDT' in self.hoga_name:
                        self.windowQ.put([ui_num['C호가잔량'], self.df_hg])
                    else:
                        self.windowQ.put([ui_num['S호가잔량'], self.df_hg])
                    self.bool_hgup = False
                self.time_uphg = timedelta_sec(0.25)

    def InitHoga(self, gubun):
        zero_list = np.zeros(12).tolist()
        self.df_hj = pd.DataFrame({'종목명': [''], '현재가': [0.], '등락율': [0.], '시가총액': [0], 'UVI': [0], '시가': [0], '고가': [0], '저가': [0]})
        self.df_hc = pd.DataFrame({'체결수량': zero_list, '체결강도': zero_list})
        self.df_hg = pd.DataFrame({'잔량': zero_list, '호가': zero_list})
        self.windowQ.put([ui_num[f'{gubun}호가종목'], self.df_hj])
        self.windowQ.put([ui_num[f'{gubun}호가체결'], self.df_hc])
        self.windowQ.put([ui_num[f'{gubun}호가잔량'], self.df_hg])
        self.hoga_name = ''

    def UpdateHogaJongmok(self, data):
        gubun = 'C' if 'KRW' in data[0] or 'USDT' in data[0] else 'S'
        if self.hoga_name != data[0]:
            self.InitHoga(gubun)
            self.hoga_name = data[0]
        self.df_hj = pd.DataFrame([data], columns=columns_hj)
        self.bool_hjup = True

    def UpdateChegeolcount(self, data):
        v, ch = data
        if v > 0:
            if 'KRW' in self.hoga_name or 'USDT' in self.hoga_name:
                tbc = round(self.df_hc['체결수량'][0] + v, 8)
                tsc = round(self.df_hc['체결수량'][11], 8)
            else:
                tbc = self.df_hc['체결수량'][0] + v
                tsc = self.df_hc['체결수량'][11]
        else:
            if 'KRW' in self.hoga_name or 'USDT' in self.hoga_name:
                tbc = round(self.df_hc['체결수량'][0], 8)
                tsc = round(self.df_hc['체결수량'][11] + abs(v), 8)
            else:
                tbc = self.df_hc['체결수량'][0]
                tsc = self.df_hc['체결수량'][11] + abs(v)

        hch = self.df_hc['체결강도'][0]
        lch = self.df_hc['체결강도'][11]

        if hch < ch:
            hch = ch
        if lch == 0 or lch > ch:
            lch = ch

        self.df_hc = self.df_hc.shift(1)
        self.df_hc.loc[0] = tbc, hch
        self.df_hc.loc[1] = v, ch
        self.df_hc.loc[11] = tsc, lch
        self.bool_hcup = True

    def UpdateHogajalryang(self, data):
        gubun = 'C' if 'KRW' in data[0] or 'USDT' in data[0] else 'S'
        if self.hoga_name != data[0]:
            self.InitHoga(gubun)
            self.hoga_name = data[0]

        jr = [data[1]] + data[13:23] + [data[2]]
        if 'KRW' in self.hoga_name or 'USDT' in self.hoga_name:
            hg = [self.df_hj['고가'][0]] + data[3:13] + [self.df_hj['저가'][0]]
        else:
            hg = [data[23]] + data[3:13] + [data[24]]

        self.df_hg = pd.DataFrame({'잔량': jr, '호가': hg})
        self.bool_hgup = True

    def UpdateHogaForChart(self, data):
        cmd, code, name, index = data
        searchdate = index[:8]
        gubun = 'C' if 'KRW' in code or 'USDT' in code else 'S'
        index = int(index)
        self.InitHoga(gubun)

        if gubun == 'C':
            db_name1 = f'{DB_PATH}/coin_tick_{searchdate}.db'
            db_name2 = DB_COIN_BACK
            db_name3 = DB_COIN_TICK
        else:
            db_name1 = f'{DB_PATH}/stock_tick_{searchdate}.db'
            db_name2 = DB_STOCK_BACK
            db_name3 = DB_STOCK_TICK

        if cmd == '이전호가정보요청':
            query = f"SELECT * FROM '{code}' WHERE `index` < {index} ORDER BY `index` DESC LIMIT 1"
        elif cmd == '다음호가정보요청':
            query = f"SELECT * FROM '{code}' WHERE `index` > {index} ORDER BY `index` LIMIT 1"
        else:
            query = f"SELECT * FROM '{code}' WHERE `index` = {index}"

        df = None
        try:
            if os.path.isfile(db_name1):
                con = sqlite3.connect(db_name1)
                df = pd.read_sql(query, con).set_index('index')
                con.close()
            elif os.path.isfile(db_name2):
                con = sqlite3.connect(db_name2)
                df = pd.read_sql(query, con).set_index('index')
                con.close()
            elif os.path.isfile(db_name3):
                con = sqlite3.connect(db_name3)
                df = pd.read_sql(query, con).set_index('index')
                con.close()
        except:
            pass

        if df is not None and len(df) > 0:
            if gubun == 'C':
                data = [name, df['현재가'].iloc[0], df['등락율'].iloc[0], 0, 0, df['시가'].iloc[0], df['고가'].iloc[0], df['저가'].iloc[0]]
            else:
                data = [name, df['현재가'].iloc[0], df['등락율'].iloc[0], df['시가총액'].iloc[0], df['VI가격'].iloc[0], df['시가'].iloc[0], df['고가'].iloc[0], df['저가'].iloc[0]]
            self.df_hj = pd.DataFrame([data], columns=columns_hj)

            data = list(df.iloc[0])
            if gubun == 'C':
                jr = [data[11]] + data[23:33] + [data[12]]
                hg = [df['고가'].iloc[0]] + data[13:23] + [df['저가'].iloc[0]]
            else:
                jr = [data[20]] + data[32:42] + [data[21]]
                hg = [df['VI가격'].iloc[0]] + data[22:32] + [0]
            self.df_hg = pd.DataFrame({'잔량': jr, '호가': hg})

            self.windowQ.put([ui_num[f'{gubun}호가종목'], self.df_hj, str(df.index[0]), 'dummy'])
            self.windowQ.put([ui_num[f'{gubun}호가잔량'], self.df_hg])
