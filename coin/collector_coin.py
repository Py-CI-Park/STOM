import time
import numpy as np
from utility.static import now
from utility.setting import ui_num


class CollectorCoin:
    def __init__(self, qlist):
        """
           0        1       2      3       4      5      6       7         8        9       10       11        12
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, sreceivQ, straderQ, sstg1Q, sstg2Q, creceivQ, ctraderQ,
        cstgQ, tick1Q, tick2Q, tick3Q, tick4Q, tick5Q, tick6Q, tick7Q, tick8Q, tick9Q, liveQ, backQ, kimpQ
         13      14      15      16      17      18      19      20      21      22     23     24     25
        """
        self.windowQ    = qlist[0]
        self.queryQ     = qlist[2]
        self.tick9Q     = qlist[22]
        self.dict_arry  = {}
        self.tick_count = 0
        self.Start()

    def Start(self):
        self.windowQ.put([ui_num['C단순텍스트'], '시스템 명령 실행 알림 - 콜렉터 시작'])

        while True:
            data = self.tick9Q.get()
            if type(data) == list:
                self.UpdateTickData(data)
            elif data == '프로세스종료':
                self.queryQ.put(['코인디비', self.dict_arry])
                break

        self.windowQ.put([ui_num['C단순텍스트'], '시스템 명령 실행 알림 - 콜렉터 종료'])
        time.sleep(3)

    def UpdateTickData(self, data):
        code, receivetime = data[-2:]
        del data[-2:]

        if code not in self.dict_arry.keys():
            self.dict_arry[code] = np.array([data])
        else:
            self.dict_arry[code] = np.r_[self.dict_arry[code], np.array([data])]

        self.tick_count += 1
        if self.tick_count > 1000:
            self.queryQ.put(['코인디비', self.dict_arry])
            self.dict_arry  = {}
            self.tick_count = 0

        if receivetime != 0:
            gap = (now() - receivetime).total_seconds()
            self.windowQ.put([ui_num['C단순텍스트'], f'콜렉터 수신 기록 알림 - 수신시간과 기록시간의 차이는 [{gap:.6f}]초입니다.'])
