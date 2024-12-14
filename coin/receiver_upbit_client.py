import zmq
import time
from threading import Thread, Timer
from utility.static import int_hms_utc
from utility.setting import ui_num, DICT_SET


class ZmqRecv(Thread):
    def __init__(self, cstgQ, creceivQ):
        super().__init__()
        self.cstgQ    = cstgQ
        self.creceivQ = creceivQ
        zctx = zmq.Context()
        self.sock = zctx.socket(zmq.SUB)
        self.sock.connect(f'tcp://localhost:5680')
        self.sock.setsockopt_string(zmq.SUBSCRIBE, '')

    def run(self):
        while True:
            msg  = self.sock.recv_string()
            data = self.sock.recv_pyobj()
            if msg == 'tickdata':
                self.creceivQ.put(data)
            elif msg == 'updatecodes':
                self.creceivQ.put('코인명갱신')
            elif msg == 'focuscodes':
                self.cstgQ.put(['관심목록'] + data)
            elif msg == 'mindata':
                self.cstgQ.put(['분봉데이터', data])
            elif msg == 'daydata':
                self.cstgQ.put(['일봉데이터', data])


class ReceiverUpbitClient:
    def __init__(self, qlist):
        """
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ,  cstgQ, liveQ, kimpQ, wdservQ
           0        1       2      3       4      5      6      7       8         9         10     11    12      13
        """
        self.windowQ   = qlist[0]
        self.soundQ    = qlist[1]
        self.teleQ     = qlist[3]
        self.creceivQ  = qlist[8]
        self.ctraderQ  = qlist[9]
        self.cstgQ     = qlist[10]
        self.dict_set  = DICT_SET

        self.dict_bool = {'프로세스종료': False}
        self.list_jang = []
        self.list_oder = []

        if self.dict_set['리시버공유'] == 1:
            self.zmqserver = ZmqRecv(self.cstgQ, self.creceivQ)
            self.zmqserver.start()

        self.Start()

    def Start(self):
        text = '코인 리시버를 시작하였습니다.'
        if self.dict_set['코인알림소리']: self.soundQ.put(text)
        self.teleQ.put(text)
        self.windowQ.put([ui_num['C단순텍스트'], '시스템 명령 실행 알림 - 리시버 시작'])
        while True:
            data = self.creceivQ.get()
            inthmsutc = int_hms_utc()
            if type(data) == list:
                if len(data) != 2:
                    self.UpdateTickData(data)
                else:
                    self.UpdateList(data)
            elif type(data) == dict:
                self.dict_set = data
            elif type(data) == str:
                if data == '코인명갱신':
                    self.ctraderQ.put('코인명갱신')
                elif data == '프로세스종료':
                    break

            if self.dict_set['코인장초전략종료시간'] < inthmsutc < self.dict_set['코인장초전략종료시간'] + 10:
                if self.dict_set['코인장초프로세스종료'] and not self.dict_bool['프로세스종료']:
                    self.ReceiverProcKill()

            if self.dict_set['코인장중전략종료시간'] < inthmsutc < self.dict_set['코인장중전략종료시간'] + 10:
                if self.dict_set['코인장중프로세스종료'] and not self.dict_bool['프로세스종료']:
                    self.ReceiverProcKill()

        self.windowQ.put([ui_num['C단순텍스트'], '시스템 명령 실행 알림 - 리시버 종료'])
        time.sleep(1)

    def UpdateTickData(self, data):
        self.cstgQ.put(data)
        code, c = data[-2], data[1]
        if code in self.list_oder or code in self.list_jang:
            self.ctraderQ.put([code, c])

    def UpdateList(self, data):
        gubun, data = data
        if gubun == '잔고목록':
            self.list_jang = data
        elif gubun == '주문목록':
            self.list_oder = data

    def ReceiverProcKill(self):
        self.dict_bool['프로세스종료'] = True
        Timer(180, self.creceivQ.put, args=['프로세스종료']).start()
