import time
import sqlite3
import numpy as np
import pandas as pd
from utility.static import now
from utility.setting import ui_num, DB_STOCK_TICK


class CollectorKiwoom:
    def __init__(self, gubun, qlist):
        """
           0        1       2      3       4      5      6       7         8        9       10       11        12
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, sreceivQ, straderQ, sstg1Q, sstg2Q, creceivQ, ctraderQ,
        cstgQ, tick1Q, tick2Q, tick3Q, tick4Q, tick5Q, tick6Q, tick7Q, tick8Q, tick9Q, liveQ, backQ, kimpQ
         13      14      15      16      17      18      19      20      21      22     23     24     25
        """
        self.gubun      = gubun
        self.windowQ    = qlist[0]
        self.tickQ      = qlist[13 + self.gubun]
        self.list_tickQ = [qlist[14], qlist[15], qlist[16], qlist[17], qlist[18], qlist[19], qlist[20], qlist[21]]
        self.dict_arry  = {}
        self.Start()

    def Start(self):
        if self.gubun == 8:
            self.windowQ.put([ui_num['S단순텍스트'], '시스템 명령 실행 알림 - 콜렉터 시작'])
        while True:
            data = self.tickQ.get()
            if type(data) == list:
                if data[0] != '콜렉터종료':
                    self.UpdateTickData(data)
                else:
                    self.SaveTickData(data)
                    if data[2]:
                        break

        if self.gubun == 8:
            self.windowQ.put([ui_num['S단순텍스트'], '시스템 명령 실행 알림 - 콜렉터 종료'])
        time.sleep(3)

    def UpdateTickData(self, data):
        code, receivetime = data[-2:]
        del data[-2:]

        if code not in self.dict_arry.keys():
            self.dict_arry[code] = np.array([data])
        else:
            self.dict_arry[code] = np.r_[self.dict_arry[code], np.array([data])]

        if self.gubun == 8 and receivetime != 0:
            gap = (now() - receivetime).total_seconds()
            self.windowQ.put([ui_num['S단순텍스트'], f'콜렉터 수신 기록 알림 - 수신시간과 기록시간의 차이는 [{gap:.6f}]초입니다.'])

    def SaveTickData(self, data):
        codes, sysexit = data[1:]
        for code in list(self.dict_arry.keys()):
            if code not in codes:
                del self.dict_arry[code]

        columns_ts = [
            'index', '현재가', '시가', '고가', '저가', '등락율', '당일거래대금', '체결강도', '거래대금증감', '전일비', '회전율',
            '전일동시간비', '시가총액', '라운드피겨위5호가이내', '초당매수수량', '초당매도수량', 'VI해제시간', 'VI가격', 'VI호가단위',
            '초당거래대금', '고저평균대비등락율', '매도총잔량', '매수총잔량', '매도호가5', '매도호가4', '매도호가3', '매도호가2',
            '매도호가1', '매수호가1', '매수호가2', '매수호가3', '매수호가4', '매수호가5', '매도잔량5', '매도잔량4', '매도잔량3',
            '매도잔량2', '매도잔량1', '매수잔량1', '매수잔량2', '매수잔량3', '매수잔량4', '매수잔량5', '매도수5호가잔량합'
        ]

        last = len(self.dict_arry)
        con = sqlite3.connect(DB_STOCK_TICK)
        if last > 0:
            start = now()
            for i, code in enumerate(list(self.dict_arry.keys())):
                df = pd.DataFrame(self.dict_arry[code], columns=columns_ts)
                df[['index']] = df[['index']].astype('int64')
                df.set_index('index', inplace=True)
                df.to_sql(code, con, if_exists='append', chunksize=1000)
                text = f'시스템 명령 실행 알림 - 콜렉터 프로세스 틱데이터 저장 중 ... [{self.gubun}]{i + 1}/{last}'
                self.windowQ.put([ui_num['S단순텍스트'], text])
            save_time = (now() - start).total_seconds()
            text = f'시스템 명령 실행 알림 - 틱데이터 저장 쓰기소요시간은 [{save_time:.6f}]초입니다.'
            self.windowQ.put([ui_num['S단순텍스트'], text])
        con.close()

        self.dict_arry = {}
        if self.gubun != 8:
            self.list_tickQ[self.gubun].put(['콜렉터종료', codes, sysexit])
