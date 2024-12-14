import os
import sys
import time
# noinspection PyUnresolvedReferences
import talib
import sqlite3
import pandas as pd
from PyQt5.QtWidgets import QApplication
from multiprocessing import Process, Queue, Lock
from stock.kiwoom import Kiwoom
from utility.static import strf_time, now
from utility.setting import DB_STOCK_DAY, DICT_SET, DB_STOCK_MIN
from stock.login_kiwoom.manuallogin import find_window, manual_login


class DataDownload:
    app = QApplication(sys.argv)

    def __init__(self, gubun, q_, lock_, minfirst_, dayfirst_, multi_):
        self.gubun    = gubun
        self.q        = q_
        self.lock     = lock_
        self.minfirst = minfirst_
        self.dayfirst = dayfirst_
        self.multi    = multi_
        self.kw       = Kiwoom(self, 'Downloader')
        self.Download()

    def Download(self):
        def code_delete(code):
            ret = self.kw.ocx.dynamicCall('KOA_Functions(QString, QString)', 'GetStockMarketKind', code)
            if int(ret) in [3, 4, 6, 8, 9, 14, 16, 19, 30, 60]:
                return True
            if code[-1] != '0':
                return True
            if '스팩' in self.kw.GetMasterCodeName(code):
                return True
            return False

        self.kw.CommConnect()
        list_code = self.kw.GetCodeListByMarket('0') + self.kw.GetCodeListByMarket('10')
        list_code = [code for code in list_code if not code_delete(code)]
        if self.multi:
            list_code = [code for i, code in enumerate(list_code) if i % 8 == self.gubun - 1]
        else:
            list_code = [code for i, code in enumerate(list_code) if i % 4 == self.gubun - 1]
        last = len(list_code)

        if DICT_SET['주식분봉데이터']:
            for i, code in enumerate(list_code):
                time.sleep(3.35)
                if self.minfirst:
                    df = []
                    self.lock.acquire()
                    df2 = self.kw.Block_Request('opt10080', 종목코드=code, 틱범위=str(DICT_SET['주식분봉기간']), 수정주가='1', output='주식분봉차트조회', next=0)
                    self.lock.release()
                    df.append(df2)
                    last_day = df2['체결시간'][0][:8]
                    while last_day > '20220314':
                        if self.kw.dict_bool['TR다음']:
                            time.sleep(3.35)
                            self.lock.acquire()
                            df2 = self.kw.Block_Request('opt10080', 종목코드=code, 틱범위=str(DICT_SET['주식분봉기간']), 수정주가='1', output='주식분봉차트조회', next=2)
                            self.lock.release()
                            df.append(df2)
                            last_day = df2['체결시간'][0][:8]
                        else:
                            break
                    df = pd.concat(df)
                else:
                    self.lock.acquire()
                    df = self.kw.Block_Request('opt10080', 종목코드=code, 틱범위=str(DICT_SET['주식분봉기간']), 수정주가='1', output='주식분봉차트조회', next=0)
                    self.lock.release()

                try:
                    df = df[::-1]
                    columns = ['체결시간', '시가', '고가', '저가', '현재가', '거래량']
                    df = df[columns]
                    df[columns] = df[columns].astype('int64')
                    df = df.abs()
                    df['거래대금'] = (df['시가'] + df['고가'] + df['저가'] + df['현재가']) / 4 * df['거래량'] / 1000000
                    df[['거래대금']] = df[['거래대금']].astype(int)
                    df.rename(columns={'현재가': '종가'}, inplace=True)
                    df['체결시간구분용'] = df['체결시간'].apply(lambda x: int(str(x)[8:]))
                    df = df[df['체결시간구분용'] <= 153000]
                    df.drop(columns=['거래량', '체결시간구분용'], inplace=True)
                except:
                    continue

                df['이평5']   = df['종가'].rolling(window=5).mean().round(3)
                df['이평10']  = df['종가'].rolling(window=10).mean().round(3)
                df['이평20']  = df['종가'].rolling(window=20).mean().round(3)
                df['이평60']  = df['종가'].rolling(window=60).mean().round(3)
                df['이평120'] = df['종가'].rolling(window=120).mean().round(3)
                df['이평240'] = df['종가'].rolling(window=240).mean().round(3)

                df['최고종가5']   = df['종가'].rolling(window=5).max().shift(1)
                df['최고고가5']   = df['고가'].rolling(window=5).max().shift(1)
                df['최고종가10']  = df['종가'].rolling(window=10).max().shift(1)
                df['최고고가10']  = df['고가'].rolling(window=10).max().shift(1)
                df['최고종가20']  = df['종가'].rolling(window=20).max().shift(1)
                df['최고고가20']  = df['고가'].rolling(window=20).max().shift(1)
                df['최고종가60']  = df['종가'].rolling(window=60).max().shift(1)
                df['최고고가60']  = df['고가'].rolling(window=60).max().shift(1)
                df['최고종가120'] = df['종가'].rolling(window=120).max().shift(1)
                df['최고고가120'] = df['고가'].rolling(window=120).max().shift(1)
                df['최고종가240'] = df['종가'].rolling(window=240).max().shift(1)
                df['최고고가240'] = df['고가'].rolling(window=240).max().shift(1)

                df['최저종가5']   = df['종가'].rolling(window=5).min().shift(1)
                df['최저저가5']   = df['저가'].rolling(window=5).min().shift(1)
                df['최저종가10']  = df['종가'].rolling(window=10).min().shift(1)
                df['최저저가10']  = df['저가'].rolling(window=10).min().shift(1)
                df['최저종가20']  = df['종가'].rolling(window=20).min().shift(1)
                df['최저저가20']  = df['저가'].rolling(window=20).min().shift(1)
                df['최저종가60']  = df['종가'].rolling(window=60).min().shift(1)
                df['최저저가60']  = df['저가'].rolling(window=60).min().shift(1)
                df['최저종가120'] = df['종가'].rolling(window=120).min().shift(1)
                df['최저저가120'] = df['저가'].rolling(window=120).min().shift(1)
                df['최저종가240'] = df['종가'].rolling(window=240).min().shift(1)
                df['최저저가240'] = df['저가'].rolling(window=240).min().shift(1)

                df['종가합계4']   = df['종가'].rolling(window=4).sum().shift(1)
                df['종가합계9']   = df['종가'].rolling(window=9).sum().shift(1)
                df['종가합계19']  = df['종가'].rolling(window=19).sum().shift(1)
                df['종가합계59']  = df['종가'].rolling(window=59).sum().shift(1)
                df['종가합계119'] = df['종가'].rolling(window=119).sum().shift(1)
                df['종가합계239'] = df['종가'].rolling(window=239).sum().shift(1)
                df['최고거래대금'] = df['거래대금'].rolling(window=DICT_SET['주식분봉개수']).max().shift(1)

                """ 보조지표 사용예
                df['BBU'], df['BBM'], df['BBL'] = talib.BBANDS(df['종가'].values, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
                df['RSI'] = talib.RSI(df['종가'].values, timeperiod=14)
                df['CCI'] = talib.CCI(df['고가'].values, df['저가'].values, df['종가'].values, timeperiod=14)
                df['MACD'], df['MACDS'], df['MACDH'] = talib.MACD(df['종가'].values, fastperiod=12, slowperiod=26, signalperiod=9)
                df['STOCK'], df['STOCD'] = talib.STOCH(df['고가'].values, df['저가'].values, df['종가'].values, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
                df['ATR'] = talib.ATR(df['고가'].values, df['저가'].values, df['종가'].values, timeperiod=14)
                """

                df.fillna(0, inplace=True)
                self.q.put(['분봉데이터', code, df])
                print(f'[{now()}] 주식 분봉데이터 다운로드 중 ... [{self.gubun}][{i+1}/{last}]')

        if DICT_SET['주식일봉데이터']:
            for i, code in enumerate(list_code):
                time.sleep(3.35)
                if self.dayfirst:
                    df = []
                    self.lock.acquire()
                    df2 = self.kw.Block_Request('opt10081', 종목코드=code, 기준일자=strf_time('%Y%m%d'), 수정주가='1', output='주식일봉차트조회', next=0)
                    self.lock.release()
                    df.append(df2)
                    last_day = df2['일자'][0][:8]
                    while last_day > '20210314':
                        if self.kw.dict_bool['TR다음']:
                            time.sleep(3.35)
                            self.lock.acquire()
                            df2 = self.kw.Block_Request('opt10081', 종목코드=code, 기준일자=strf_time('%Y%m%d'), 수정주가='1', output='주식일봉차트조회', next=2)
                            self.lock.release()
                            df.append(df2)
                            last_day = df2['일자'][0][:8]
                        else:
                            break
                    df = pd.concat(df)
                else:
                    self.lock.acquire()
                    df = self.kw.Block_Request('opt10081', 종목코드=code, 기준일자=strf_time('%Y%m%d'), 수정주가='1', output='주식일봉차트조회', next=0)
                    self.lock.release()

                try:
                    df = df[::-1]
                    columns = ['일자', '시가', '고가', '저가', '현재가', '거래대금']
                    df = df[columns]
                    df[columns] = df[columns].astype('int64')
                    df = df.abs()
                    df.rename(columns={'현재가': '종가'}, inplace=True)
                except:
                    continue

                df['이평5']   = df['종가'].rolling(window=5).mean().round(3)
                df['이평10']  = df['종가'].rolling(window=10).mean().round(3)
                df['이평20']  = df['종가'].rolling(window=20).mean().round(3)
                df['이평60']  = df['종가'].rolling(window=60).mean().round(3)
                df['이평120'] = df['종가'].rolling(window=120).mean().round(3)
                df['이평240'] = df['종가'].rolling(window=240).mean().round(3)

                df['최고종가5']   = df['종가'].rolling(window=5).max().shift(1)
                df['최고고가5']   = df['고가'].rolling(window=5).max().shift(1)
                df['최고종가10']  = df['종가'].rolling(window=10).max().shift(1)
                df['최고고가10']  = df['고가'].rolling(window=10).max().shift(1)
                df['최고종가20']  = df['종가'].rolling(window=20).max().shift(1)
                df['최고고가20']  = df['고가'].rolling(window=20).max().shift(1)
                df['최고종가60']  = df['종가'].rolling(window=60).max().shift(1)
                df['최고고가60']  = df['고가'].rolling(window=60).max().shift(1)
                df['최고종가120'] = df['종가'].rolling(window=120).max().shift(1)
                df['최고고가120'] = df['고가'].rolling(window=120).max().shift(1)
                df['최고종가240'] = df['종가'].rolling(window=240).max().shift(1)
                df['최고고가240'] = df['고가'].rolling(window=240).max().shift(1)

                df['최저종가5']   = df['종가'].rolling(window=5).min().shift(1)
                df['최저저가5']   = df['저가'].rolling(window=5).min().shift(1)
                df['최저종가10']  = df['종가'].rolling(window=10).min().shift(1)
                df['최저저가10']  = df['저가'].rolling(window=10).min().shift(1)
                df['최저종가20']  = df['종가'].rolling(window=20).min().shift(1)
                df['최저저가20']  = df['저가'].rolling(window=20).min().shift(1)
                df['최저종가60']  = df['종가'].rolling(window=60).min().shift(1)
                df['최저저가60']  = df['저가'].rolling(window=60).min().shift(1)
                df['최저종가120'] = df['종가'].rolling(window=120).min().shift(1)
                df['최저저가120'] = df['저가'].rolling(window=120).min().shift(1)
                df['최저종가240'] = df['종가'].rolling(window=240).min().shift(1)
                df['최저저가240'] = df['저가'].rolling(window=240).min().shift(1)

                df['종가합계4']   = df['종가'].rolling(window=4).sum().shift(1)
                df['종가합계9']   = df['종가'].rolling(window=9).sum().shift(1)
                df['종가합계19']  = df['종가'].rolling(window=19).sum().shift(1)
                df['종가합계59']  = df['종가'].rolling(window=59).sum().shift(1)
                df['종가합계119'] = df['종가'].rolling(window=119).sum().shift(1)
                df['종가합계239'] = df['종가'].rolling(window=239).sum().shift(1)
                df['최고거래대금'] = df['거래대금'].rolling(window=250).max().shift(1)

                """ 보조지표 사용예
                df['BBU'], df['BBM'], df['BBL'] = talib.BBANDS(df['종가'].values, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
                df['RSI'] = talib.RSI(df['종가'].values, timeperiod=14)
                df['CCI'] = talib.CCI(df['고가'].values, df['저가'].values, df['종가'].values, timeperiod=14)
                df['MACD'], df['MACDS'], df['MACDH'] = talib.MACD(df['종가'].values, fastperiod=12, slowperiod=26, signalperiod=9)
                df['STOCK'], df['STOCD'] = talib.STOCH(df['고가'].values, df['저가'].values, df['종가'].values, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
                df['ATR'] = talib.ATR(df['고가'].values, df['저가'].values, df['종가'].values, timeperiod=14)
                """

                df.fillna(0, inplace=True)
                self.q.put(['일봉데이터', code, df])
                print(f'[{now()}] 주식 일봉데이터 다운로드 중 ... [{self.gubun}][{i+1}/{last}]')

        self.q.put('다운로드완료')
        sys.exit()


class Query:
    def __init__(self, q_, multi_):
        self.q = q_
        self.multi = multi_
        self.Start()

    def Start(self):
        dict_lastday = {}
        dict_lastmin = {}

        con1 = sqlite3.connect(DB_STOCK_DAY)
        con2 = sqlite3.connect(DB_STOCK_MIN)

        dfd = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con1)
        if len(dfd) > 0:
            for code in dfd['name'].to_list():
                df = pd.read_sql(f"SELECT * FROM '{code}' ORDER BY 일자 DESC LIMIT 1", con1)
                dict_lastday[code] = df['일자'].iloc[0]

        dfm = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con2)
        if len(dfm) > 0:
            for code in dfm['name'].to_list():
                df = pd.read_sql(f"SELECT * FROM '{code}' ORDER BY 체결시간 DESC LIMIT 1", con2)
                dict_lastmin[code] = df['체결시간'].iloc[0]

        k = 0
        while True:
            data = self.q.get()
            if data == '다운로드완료':
                k += 1
                if self.multi:
                    if k == 8:
                        break
                else:
                    if k == 4:
                        break
            else:
                gubun, code, df = data
                if gubun == '일봉데이터':
                    if len(df) > 0:
                        if code in dict_lastday.keys():
                            df = df[df['일자'] > dict_lastday[code]]
                        df.set_index('일자', inplace=True)
                        df.to_sql(code, con1, if_exists='append', chunksize=1000)
                elif gubun == '분봉데이터':
                    if len(df) > 0:
                        if code in dict_lastmin.keys():
                            df = df[df['체결시간'] > dict_lastmin[code]]
                        df.set_index('체결시간', inplace=True)
                        df.to_sql(code, con2, if_exists='append', chunksize=1000)

        con1.close()
        con2.close()

        print(f'[{now()}] 데이터 다운로드가 완료되었습니다.')
        if DICT_SET['주식일봉다운컴종료']:
            os.system('shutdown /s /t 300')
        sys.exit()


def login(gubun):
    while find_window('Open API login') == 0:
        time.sleep(1)
    time.sleep(2)
    manual_login(gubun)
    if gubun == 1:
        time.sleep(40)
    else:
        time.sleep(20)
    os.system('C:/Windows/System32/taskkill /f /im opstarter.exe')


if __name__ == '__main__':
    login_info = 'C:/OpenAPI/system/Autologin.dat'
    if os.path.isfile(login_info):
        os.remove('C:/OpenAPI/system/Autologin.dat')

    q = Queue()
    lock = Lock()

    con = sqlite3.connect(DB_STOCK_MIN)
    df_min = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
    con.close()
    minfirst = False if len(df_min) > 0 else True

    con = sqlite3.connect(DB_STOCK_DAY)
    df_day = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
    con.close()
    dayfirst = False if len(df_day) > 0 else True

    multi = False
    if DICT_SET['아이디3'] is not None and DICT_SET['아이디4'] is not None:
        multi = True

    Process(target=Query, args=(q, multi)).start()
    Process(target=DataDownload, args=(1, q, lock, minfirst, dayfirst, multi)).start()
    login(1)
    Process(target=DataDownload, args=(2, q, lock, minfirst, dayfirst, multi)).start()
    login(2)
    Process(target=DataDownload, args=(3, q, lock, minfirst, dayfirst, multi)).start()
    login(3)
    Process(target=DataDownload, args=(4, q, lock, minfirst, dayfirst, multi)).start()
    login(4)

    if multi:
        Process(target=DataDownload, args=(5, q, lock, minfirst, dayfirst, multi)).start()
        login(5)
        Process(target=DataDownload, args=(6, q, lock, minfirst, dayfirst, multi)).start()
        login(6)
        Process(target=DataDownload, args=(7, q, lock, minfirst, dayfirst, multi)).start()
        login(7)
        Process(target=DataDownload, args=(8, q, lock, minfirst, dayfirst, multi)).start()
        login(8)
