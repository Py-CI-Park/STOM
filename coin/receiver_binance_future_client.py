import zmq
import time
from threading import Thread
from utility.static import int_hms_utc, threading_timer
from utility.setting import ui_num, DICT_SET


class ZmqRecv(Thread):
    def __init__(self, creceivQ, cstgQ, ctraderQ):
        super().__init__()
        self.creceivQ = creceivQ
        self.cstgQ    = cstgQ
        self.ctraderQ = ctraderQ
        zctx = zmq.Context()
        self.sock = zctx.socket(zmq.SUB)
        self.sock.connect(f'tcp://localhost:5779')
        self.sock.setsockopt_string(zmq.SUBSCRIBE, '')

    def run(self):
        while True:
            msg  = self.sock.recv_string()
            data = self.sock.recv_pyobj()
            if msg == 'tickdata':
                self.creceivQ.put(data)
            elif msg == 'updatecodes':
                self.ctraderQ.put(data)
            elif msg == 'focuscodes':
                self.cstgQ.put(data)
            elif msg == 'mindata':
                self.cstgQ.put(data)
            elif msg == 'daydata':
                self.cstgQ.put(data)


class ReceiverBinanceFutureClient:
    def __init__(self, qlist):
        """
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ,  cstgQ, liveQ, kimpQ, wdzservQ
           0        1       2      3       4      5      6      7       8         9         10     11    12      13
        """
        self.windowQ   = qlist[0]
        self.soundQ    = qlist[1]
        self.teleQ     = qlist[3]
        self.hogaQ     = qlist[5]
        self.creceivQ  = qlist[8]
        self.ctraderQ  = qlist[9]
        self.cstgQ     = qlist[10]
        self.dict_set  = DICT_SET

        self.dict_bool   = {'프로세스종료': False}
        self.tuple_jang  = ()
        self.tuple_order = ()
        self.hoga_code   = None

        if self.dict_set['리시버공유'] == 1:
            self.zmqserver = ZmqRecv(self.creceivQ, self.cstgQ, self.ctraderQ)
            self.zmqserver.start()

        self.MainLoop()

    def MainLoop(self):
        text = '코인 리시버를 시작하였습니다.'
        if self.dict_set['코인알림소리']: self.soundQ.put(text)
        self.teleQ.put(text)
        self.windowQ.put((ui_num['C단순텍스트'], '시스템 명령 실행 알림 - 리시버 시작'))
        while True:
            data = self.creceivQ.get()
            if len(data) != 2:
                self.UpdateTickData(data)
            else:
                self.UpdateTuple(data)
            if data == '프로세스종료':
                self.ctraderQ.put('프로세스종료')
                self.cstgQ.put('프로세스종료')
                break

            inthmsutc = int_hms_utc()
            if self.dict_set['코인장초전략종료시간'] < inthmsutc < self.dict_set['코인장초전략종료시간'] + 10:
                if self.dict_set['코인장초프로세스종료'] and not self.dict_bool['프로세스종료']:
                    self.ReceiverProcKill()

            if self.dict_set['코인장중전략종료시간'] < inthmsutc < self.dict_set['코인장중전략종료시간'] + 10:
                if self.dict_set['코인장중프로세스종료'] and not self.dict_bool['프로세스종료']:
                    self.ReceiverProcKill()

        self.windowQ.put((ui_num['C단순텍스트'], '시스템 명령 실행 알림 - 리시버 종료'))
        time.sleep(1)

    def UpdateTickData(self, data):
        self.cstgQ.put(data)
        code, c = data[-2], data[1]
        if code in self.tuple_order or code in self.tuple_jang:
            self.ctraderQ.put((code, c))
        if self.hoga_code == code:
            c, o, h, low, per, _, ch, bids, asks = data[1:10]
            hogadata = data[12:34]
            self.hogaQ.put((code, c, per, 0, 0, o, h, low))
            self.hogaQ.put((-asks, ch))
            self.hogaQ.put((bids, ch))
            self.hogaQ.put((code,) + hogadata + (0, 0))

    def UpdateTuple(self, data):
        gubun, data = data
        if gubun == '잔고목록':
            self.tuple_jang = data
        elif gubun == '주문목록':
            self.tuple_order = data

    def ReceiverProcKill(self):
        self.dict_bool['프로세스종료'] = True
        threading_timer(180, self.creceivQ.put, '프로세스종료')
