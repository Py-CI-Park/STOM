import os
import sys
import time
import sqlite3
import pandas as pd
from PyQt5.QtWidgets import QApplication
from multiprocessing import Process, Queue, Lock
from stock.kiwoom import Kiwoom
from utility.static import now
from stock.login_kiwoom.manuallogin import find_window, manual_login


class DataDownload:
    app = QApplication(sys.argv)

    def __init__(self, gubun, q_, lock_):
        self.gubun = gubun
        self.q     = q_
        self.lock  = lock_
        self.kw    = Kiwoom(self, 'Downloader')
        self.Download()

    def Download(self):
        def convert(df_):
            columns = ['체결시간', '현재가', '거래량']
            df_ = df_[columns].copy()
            df_[columns] = df_[columns].astype('int64')
            df_['현재가'] = df_['현재가'] / 100
            return df_

        self.kw.CommConnect()
        code = '001' if self.gubun == 1 else '101'

        df = []
        self.lock.acquire()
        df2 = self.kw.Block_Request('opt20004', 업종코드=code, 틱범위='1', output='업종틱차트조회', next=0)
        self.lock.release()
        df2 = convert(df2)
        df.append(df2)
        while self.kw.dict_bool['TR다음']:
            time.sleep(3.35)
            self.lock.acquire()
            df2 = self.kw.Block_Request('opt20004', 업종코드=code, 틱범위='1', output='업종틱차트조회', next=2)
            self.lock.release()
            df2 = convert(df2)
            df.append(df2)
            print(f"[{now()}]지수데이터 다운로드 중 .. [{self.gubun}][{df2['체결시간'][0]}]")

        df = pd.concat(df)
        df = df[::-1]
        df['일자'] = df['체결시간'].apply(lambda x: int(str(x)[:8]))
        df['시가'] = 0.
        df['고가'] = 0.
        df['저가'] = 0.
        df['전일대비'] = 0.
        df['등락율'] = 0.

        전일종가, 시가, 고가, 저가 = 0., 0., 0., 0.
        for i in range(len(df)):
            현재가 = df['현재가'].iloc[i]
            if i == 0 or df['일자'].iloc[i] != df['일자'].iloc[i-1]:
                전일종가 = df['현재가'].iloc[i if i == 0 else i-1]
                시가, 고가, 저가 = 현재가, 현재가, 현재가
            elif 현재가 > 고가: 고가 = 현재가
            elif 현재가 < 저가: 저가 = 현재가
            전일대비 = round(현재가 - 전일종가, 2)
            등락율 = round((현재가 / 전일종가 - 1) * 100, 2)
            df.iloc[i, 4:] = 시가, 고가, 저가, 전일대비, 등락율

        df = df[df['일자'] > df['일자'].iloc[0]]
        df = df[['체결시간', '현재가', '시가', '고가', '저가', '전일대비', '거래량', '등락율']]
        df.set_index('체결시간', inplace=True)

        self.q.put((code, df))
        time.sleep(3)
        sys.exit()


class Query:
    def __init__(self, q_):
        self.q = q_
        self.Start()

    def Start(self):
        k = 0
        while True:
            code, df = self.q.get()
            if len(df) > 0:
                con = sqlite3.connect('./_database/stock_jisu.db')
                df.to_sql(code, con, if_exists='append', chunksize=1000)
                con.close()
            k += 1
            if k == 2: break

        print(f'[{now()}]데이터 다운로드가 완료되었습니다.')
        sys.exit()


def login(gubun):
    while find_window('Open API login') == 0:
        time.sleep(1)
    time.sleep(2)
    manual_login(gubun)
    time.sleep(20)
    os.system('C:/Windows/System32/taskkill /f /im opstarter.exe')


if __name__ == '__main__':
    login_info = 'C:/OpenAPI/system/Autologin.dat'
    if os.path.isfile(login_info):
        os.remove('C:/OpenAPI/system/Autologin.dat')

    q = Queue()
    lock = Lock()

    con_ = sqlite3.connect('./_database/stock_jisu.db')
    df_jisu = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con_)
    con_.close()

    Process(target=Query, args=(q,)).start()
    Process(target=DataDownload, args=(1, q, lock)).start()
    login(2)
    Process(target=DataDownload, args=(2, q, lock)).start()
    login(4)
