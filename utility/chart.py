import os
import math
import talib
import sqlite3
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib import pyplot as plt
from utility.static import strp_time, timedelta_sec, strf_time
from utility.setting import ui_num, DICT_SET, DB_TRADELIST, DB_SETTING, DB_PATH, DB_STOCK_BACK, DB_COIN_BACK, DB_BACKTEST, DB_STOCK_MIN, DB_STOCK_DAY, DB_COIN_MIN, DB_COIN_DAY


class Chart:
    def __init__(self, qlist):
        """
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ,  cstgQ, liveQ, kimpQ, wdzservQ
           0        1       2      3       4      5      6      7       8         9         10     11    12      13
        """
        self.windowQ  = qlist[0]
        self.chartQ   = qlist[4]
        self.dict_set = DICT_SET

        con1 = sqlite3.connect(DB_SETTING)
        con2 = sqlite3.connect(DB_STOCK_BACK)
        try:
            df = pd.read_sql('SELECT * FROM codename', con1).set_index('index')
        except:
            df = pd.read_sql('SELECT * FROM codename', con2).set_index('index')
        con1.close()
        con2.close()

        font_name = 'C:/Windows/Fonts/malgun.ttf'
        font_family = font_manager.FontProperties(fname=font_name).get_name()
        plt.rcParams['font.family'] = font_family
        plt.rcParams['axes.unicode_minus'] = False

        self.dict_name  = df['종목명'].to_dict()
        self.arry_kosp  = None
        self.arry_kosd  = None
        self.Start()

    def Start(self):
        while True:
            data = self.chartQ.get()
            if data[0] == '설정변경':
                self.dict_set = data[1]
            if data[0] == '그래프비교':
                self.GraphComparison(data[1])
            elif len(data) == 3:
                self.UpdateRealJisu(data)
            elif len(data) == 5:
                self.UpdateChartDayMin(data)
            elif len(data) >= 6:
                self.UpdateChart(data)

    @staticmethod
    def GraphComparison(backdetail_list):
        plt.figure('그래프 비교', figsize=(12, 10))
        con = sqlite3.connect(DB_BACKTEST)
        for table in backdetail_list:
            df = pd.read_sql(f'SELECT `index`, `수익금` FROM {table}', con)
            df['index'] = df['index'].apply(lambda x: strp_time('%Y%m%d%H%M%S', x))
            df.set_index('index', inplace=True)
            df = df.resample('D').sum()
            df['수익금합계'] = df['수익금'].cumsum()
            plt.plot(df.index, df['수익금합계'], linewidth=1, label=table)
        con.close()
        plt.legend(loc='best')
        plt.tight_layout()
        plt.grid()
        plt.show()

    def UpdateRealJisu(self, data):
        gubun = data[0]
        jisu_data = data[1:]
        try:
            if gubun == '코스피':
                if self.arry_kosp is None:
                    self.arry_kosp = np.array([jisu_data])
                else:
                    self.arry_kosp = np.r_[self.arry_kosp, np.array([jisu_data])]
                xticks = [strp_time('%Y%m%d%H%M%S', str(int(x))).timestamp() for x in self.arry_kosp[:, 0]]
                self.windowQ.put((ui_num['코스피'], xticks, self.arry_kosp[:, 1]))
            elif gubun == '코스닥':
                if self.arry_kosd is None:
                    self.arry_kosd = np.array([jisu_data])
                else:
                    self.arry_kosd = np.r_[self.arry_kosd, np.array([jisu_data])]
                xticks = [strp_time('%Y%m%d%H%M%S', str(int(x))).timestamp() for x in self.arry_kosd[:, 0]]
                self.windowQ.put((ui_num['코스닥'], xticks, self.arry_kosd[:, 1]))
        except:
            pass

    def UpdateChart(self, data):
        if len(data) == 6:
            coin, code, tickcount, searchdate, starttime, endtime = data
            detail, buytimes = None, None
        else:
            coin, code, tickcount, searchdate, starttime, endtime, detail, buytimes = data

        if coin:
            db_name1 = f'{DB_PATH}/coin_tick_{searchdate}.db'
            db_name2 = DB_COIN_BACK
        else:
            db_name1 = f'{DB_PATH}/stock_tick_{searchdate}.db'
            db_name2 = DB_STOCK_BACK

        query1 = f"SELECT * FROM '{code}' WHERE `index` LIKE '{searchdate}%' and " \
                 f"`index` % 1000000 >= {starttime} and " \
                 f"`index` % 1000000 <= {endtime}"

        query2 = f"SELECT * FROM '{code}' WHERE `index` LIKE '{searchdate}%'"

        df = None
        try:
            if os.path.isfile(db_name1):
                con = sqlite3.connect(db_name1)
                df = pd.read_sql(query1 if starttime != '' and endtime != '' else query2, con).set_index('index')
                con.close()
            elif os.path.isfile(db_name2):
                con = sqlite3.connect(db_name2)
                df = pd.read_sql(query1 if starttime != '' and endtime != '' else query2, con).set_index('index')
                con.close()
        except:
            pass

        if df is None or len(df) == 0:
            self.windowQ.put((ui_num['차트'], '차트오류', '', '', '', ''))
        else:
            if coin:
                gubun = '코인'
                gbtime = self.dict_set['코인장초전략종료시간']
                round_unit = 8
            else:
                gubun = '주식'
                gbtime = self.dict_set['주식장초전략종료시간']
                round_unit = 3

            df['체결시간']     = df.index
            df['이동평균60']   = df['현재가'].rolling(window=60).mean().round(round_unit)
            df['이동평균300']  = df['현재가'].rolling(window=300).mean().round(round_unit)
            df['이동평균600']  = df['현재가'].rolling(window=600).mean().round(round_unit)
            df['이동평균1200'] = df['현재가'].rolling(window=1200).mean().round(round_unit)

            df['최고현재가'] = 0
            df['최저현재가'] = 0
            df['최고초당매수수량'] = 0
            df['최고초당매도수량'] = 0

            """ 체결강도를 최근 5분간의 매도수수량으로 계산하여 표시한다.
            df2 = df[['체결강도', '초당매수수량', '초당매도수량']].copy()
            df2['5분누적매수량'] = df2['초당매수수량'].rolling(window=300).sum()
            df2['5분누적매도량'] = df2['초당매도수량'].rolling(window=300).sum()
            df2.fillna(method='bfill', inplace=True)
            df2['체결강도'] = df2['5분누적매수량'] / df2['5분누적매도량'] * 100
            df2['체결강도'] = df2['체결강도'].round(2)
            df2['체결강도'] = df2['체결강도'].apply(lambda x: 500. if x > 500 else x)
            df['체결강도'] = df['체결강도'][:299].to_list() + df2['체결강도'][299:].to_list()
            """

            if tickcount != 30:
                df['초당거래대금평균'] = df['초당거래대금'].rolling(window=tickcount).mean().round(0)
                df['체결강도평균']    = df['체결강도'].rolling(window=tickcount).mean().round(3)
                df['최고체결강도']    = df['체결강도'].rolling(window=tickcount).max()
                df['최저체결강도']    = df['체결강도'].rolling(window=tickcount).min()
            else:
                df['장초초당거래대금평균'] = df['초당거래대금'].rolling(window=self.dict_set[f'{gubun}장초평균값계산틱수']).mean().round(0)
                df['장초체결강도평균']    = df['체결강도'].rolling(window=self.dict_set[f'{gubun}장초평균값계산틱수']).mean().round(3)
                df['장초최고체결강도']    = df['체결강도'].rolling(window=self.dict_set[f'{gubun}장초평균값계산틱수']).max()
                df['장초최저체결강도']    = df['체결강도'].rolling(window=self.dict_set[f'{gubun}장초평균값계산틱수']).min()

                df['장중초당거래대금평균'] = df['초당거래대금'].rolling(window=self.dict_set[f'{gubun}장중평균값계산틱수']).mean().round(0)
                df['장중체결강도평균']    = df['체결강도'].rolling(window=self.dict_set[f'{gubun}장중평균값계산틱수']).mean().round(3)
                df['장중최고체결강도']    = df['체결강도'].rolling(window=self.dict_set[f'{gubun}장중평균값계산틱수']).max()
                df['장중최저체결강도']    = df['체결강도'].rolling(window=self.dict_set[f'{gubun}장중평균값계산틱수']).min()

                df['구분용체결시간'] = df['체결시간'].apply(lambda x: int(str(x)[8:]))
                df2 = df[df['구분용체결시간'] <= gbtime][['장초초당거래대금평균', '장초체결강도평균', '장초최고체결강도', '장초최저체결강도']]
                df3 = df[df['구분용체결시간'] > gbtime][['장중초당거래대금평균', '장중체결강도평균', '장중최고체결강도', '장중최저체결강도']]

                df['초당거래대금평균'] = df2['장초초당거래대금평균'].to_list() + df3['장중초당거래대금평균'].to_list()
                df['체결강도평균']    = df2['장초체결강도평균'].to_list() + df3['장중체결강도평균'].to_list()
                df['최고체결강도']    = df2['장초최고체결강도'].to_list() + df3['장중최고체결강도'].to_list()
                df['최저체결강도']    = df2['장초최저체결강도'].to_list() + df3['장중최저체결강도'].to_list()

            if tickcount == '': tickcount = self.dict_set[f'{gubun}장초평균값계산틱수']
            df['누적초당매수수량'] = df['초당매수수량'].rolling(window=tickcount).sum()
            df['누적초당매도수량'] = df['초당매도수량'].rolling(window=tickcount).sum()
            df[f'등락율N{tickcount}'] = df['등락율'].shift(tickcount - 1)
            df['등락율차이'] = df['등락율'] - df[f'등락율N{tickcount}']
            df[f'당일거래대금N{tickcount}'] = df['당일거래대금'].shift(tickcount - 1)
            df['당일거래대금차이'] = df['당일거래대금'] - df[f'당일거래대금N{tickcount}']
            if not coin:
                df['등락율각도'] = df['등락율차이'].apply(lambda x: round(math.atan2(x * 5, tickcount) / (2 * math.pi) * 360, 2))
                df['당일거래대금각도'] = df['당일거래대금차이'].apply(lambda x: round(math.atan2(x / 100, tickcount) / (2 * math.pi) * 360, 2))
            else:
                df['등락율각도'] = df['등락율차이'].apply(lambda x: round(math.atan2(x * 10, tickcount) / (2 * math.pi) * 360, 2))
                df['당일거래대금각도'] = df['당일거래대금차이'].apply(lambda x: round(math.atan2(x / 100_000_000, tickcount) / (2 * math.pi) * 360, 2))
            if not coin:
                df[f'전일비N{tickcount}'] = df['전일비'].shift(tickcount - 1)
                df['전일비차이'] = df['전일비'] - df[f'전일비N{tickcount}']
                df['전일비각도'] = df['전일비차이'].apply(lambda x: round(math.atan2(x, tickcount) / (2 * math.pi) * 360, 2))

            buy_index  = []
            sell_index = []
            df['매수가'] = 0
            df['매도가'] = 0
            if 'USDT' in code:
                df['매수가2'] = 0
                df['매도가2'] = 0

            if detail is None:
                con = sqlite3.connect(DB_TRADELIST)
                if coin:
                    df2 = pd.read_sql(f"SELECT * FROM c_chegeollist WHERE 체결시간 LIKE '{searchdate}%' and 종목명 = '{code}'", con).set_index('index')
                else:
                    name = self.dict_name[code] if code in self.dict_name.keys() else code
                    df2 = pd.read_sql(f"SELECT * FROM s_chegeollist WHERE 체결시간 LIKE '{searchdate}%' and 종목명 = '{name}'", con).set_index('index')
                con.close()

                if len(df2) > 0:
                    for index in df2.index:
                        cgtime = int(float(df2['체결시간'][index]))
                        if 'USDT' not in code:
                            if df2['주문구분'][index] == '매수':
                                while cgtime not in df.index:
                                    onesecago = timedelta_sec(-1, strp_time('%Y%m%d%H%M%S', str(cgtime)))
                                    cgtime = int(strf_time('%Y%m%d%H%M%S', onesecago))
                                buy_index.append(cgtime)
                                df.loc[cgtime, '매수가'] = df2['체결가'][index]
                            elif df2['주문구분'][index] == '매도':
                                while cgtime not in df.index:
                                    onesecago = timedelta_sec(-1, strp_time('%Y%m%d%H%M%S', str(cgtime)))
                                    cgtime = int(strf_time('%Y%m%d%H%M%S', onesecago))
                                sell_index.append(cgtime)
                                df.loc[cgtime, '매도가'] = df2['체결가'][index]
                        else:
                            if df2['주문구분'][index] == 'BUY_LONG':
                                while cgtime not in df.index:
                                    onesecago = timedelta_sec(-1, strp_time('%Y%m%d%H%M%S', str(cgtime)))
                                    cgtime = int(strf_time('%Y%m%d%H%M%S', onesecago))
                                buy_index.append(cgtime)
                                df.loc[cgtime, '매수가'] = df2['체결가'][index]
                            elif df2['주문구분'][index] == 'SELL_LONG':
                                while cgtime not in df.index:
                                    onesecago = timedelta_sec(-1, strp_time('%Y%m%d%H%M%S', str(cgtime)))
                                    cgtime = int(strf_time('%Y%m%d%H%M%S', onesecago))
                                sell_index.append(cgtime)
                                df.loc[cgtime, '매도가'] = df2['체결가'][index]
                            elif df2['주문구분'][index] == 'SELL_SHORT':
                                while cgtime not in df.index:
                                    onesecago = timedelta_sec(-1, strp_time('%Y%m%d%H%M%S', str(cgtime)))
                                    cgtime = int(strf_time('%Y%m%d%H%M%S', onesecago))
                                buy_index.append(cgtime)
                                df.loc[cgtime, '매수가2'] = df2['체결가'][index]
                            elif df2['주문구분'][index] == 'BUY_SHORT':
                                while cgtime not in df.index:
                                    onesecago = timedelta_sec(-1, strp_time('%Y%m%d%H%M%S', str(cgtime)))
                                    cgtime = int(strf_time('%Y%m%d%H%M%S', onesecago))
                                sell_index.append(cgtime)
                                df.loc[cgtime, '매도가2'] = df2['체결가'][index]
            else:
                매수시간, 매수가, 매도시간, 매도가 = detail
                buy_index.append(매수시간)
                sell_index.append(매도시간)
                df.loc[매수시간, '매수가'] = 매수가
                df.loc[매도시간, '매도가'] = 매도가
                if buytimes != '':
                    buytimes = buytimes.split('^')
                    buytimes = [x.split(';') for x in buytimes]
                    for x in buytimes:
                        추가매수시간, 추가매수가 = int(x[0]), int(x[1]) if not coin else float(x[1])
                        buy_index.append(추가매수시간)
                        df.loc[추가매수시간, '매수가'] = 추가매수가

            if not coin:
                columns = [
                    '체결시간', '현재가', '시가', '고가', '저가', '등락율', '당일거래대금', '체결강도', '거래대금증감', '전일비', '회전율',
                    '전일동시간비', '시가총액', '라운드피겨위5호가이내', '초당매수수량', '초당매도수량', 'VI해제시간', 'VI가격', 'VI호가단위',
                    '초당거래대금', '고저평균대비등락율', '매도총잔량', '매수총잔량', '매도호가5', '매도호가4', '매도호가3', '매도호가2',
                    '매도호가1', '매수호가1', '매수호가2', '매수호가3', '매수호가4', '매수호가5', '매도잔량5', '매도잔량4', '매도잔량3',
                    '매도잔량2', '매도잔량1', '매수잔량1', '매수잔량2', '매수잔량3', '매수잔량4', '매수잔량5', '매도수5호가잔량합', '관심종목',
                    '이동평균60', '이동평균300', '이동평균600', '이동평균1200', '최고현재가', '최저현재가', '체결강도평균', '최고체결강도',
                    '최저체결강도', '최고초당매수수량', '최고초당매도수량', '누적초당매수수량', '누적초당매도수량', '초당거래대금평균',
                    '등락율각도', '당일거래대금각도', '전일비각도'
                ]
            else:
                columns = [
                    '체결시간', '현재가', '시가', '고가', '저가', '등락율', '당일거래대금', '체결강도', '초당매수수량', '초당매도수량',
                    '초당거래대금', '고저평균대비등락율', '매도총잔량', '매수총잔량', '매도호가5', '매도호가4', '매도호가3', '매도호가2',
                    '매도호가1', '매수호가1', '매수호가2', '매수호가3', '매수호가4', '매수호가5', '매도잔량5', '매도잔량4', '매도잔량3',
                    '매도잔량2', '매도잔량1', '매수잔량1', '매수잔량2', '매수잔량3', '매수잔량4', '매수잔량5', '매도수5호가잔량합', '관심종목',
                    '이동평균60', '이동평균300', '이동평균600', '이동평균1200', '최고현재가', '최저현재가', '체결강도평균', '최고체결강도',
                    '최저체결강도', '최고초당매수수량', '최고초당매도수량', '누적초당매수수량', '누적초당매도수량', '초당거래대금평균',
                    '등락율각도', '당일거래대금각도'
                ]

            columns += ['매수가', '매도가']
            if 'USDT' in code:
                columns += ['매수가2', '매도가2']
            df = df[columns]
            df.fillna(0, inplace=True)
            arry = np.array(df)
            # T_BBU, _, T_BBL = talib.BBANDS(arry[:, 1], timeperiod=30, nbdevup=2, nbdevdn=2, matype=0)
            # T_MACD, T_MACDS, T_MACDH = talib.MACD(arry[:, 1], fastperiod=30, slowperiod=60, signalperiod=15)
            # T_RSI = talib.RSI(arry[:, 1], timeperiod=120)
            # arry = np.r_[
            #     '1',
            #     arry,
            #     np.reshape(T_BBU, (-1, 1)),
            #     np.reshape(T_BBL, (-1, 1)),
            #     np.reshape(T_MACD, (-1, 1)),
            #     np.reshape(T_MACDS, (-1, 1)),
            #     np.reshape(T_MACDH, (-1, 1)),
            #     np.reshape(T_RSI, (-1, 1))
            # ]
            # arry = np.nan_to_num(arry)
            xticks = [strp_time('%Y%m%d%H%M%S', str(int(x))).timestamp() for x in df.index]
            self.windowQ.put((ui_num['차트'], coin, xticks, arry, buy_index, sell_index))

    def UpdateChartDayMin(self, data):
        gubun, coin, code, name, searchdate = data
        searchdate = int(searchdate)
        if gubun == '일봉차트':
            if coin:
                db_name = DB_COIN_DAY
            else:
                db_name = DB_STOCK_DAY

            query = f"SELECT * FROM '{code}' WHERE 일자 <= {searchdate} ORDER BY 일자 DESC LIMIT 120"
            con = sqlite3.connect(db_name)
            df = pd.read_sql(query, con)
            con.close()
            if len(df) > 0:
                df = df[['일자', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240']].copy()
                df = df[::-1]
                self.windowQ.put((ui_num['일봉차트'], name, np.array(df)))
        else:
            if coin:
                db_name = DB_COIN_MIN
                query = f"SELECT * FROM '{code}' WHERE 체결시간 / 1000000 <= {searchdate} ORDER BY 체결시간 DESC LIMIT {int(self.dict_set['코인분봉개수'] / 5)}"
            else:
                db_name = DB_STOCK_MIN
                query = f"SELECT * FROM '{code}' WHERE 체결시간 / 1000000 <= {searchdate} ORDER BY 체결시간 DESC LIMIT {int(self.dict_set['주식분봉개수'] / 5)}"

            con = sqlite3.connect(db_name)
            df = pd.read_sql(query, con)
            con.close()
            if len(df) > 0:
                df = df[['체결시간', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240']].copy()
                df = df[::-1]
                self.windowQ.put((ui_num['분봉차트'], name, np.array(df)))
