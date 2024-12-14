import sys
import zmq
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from utility.setting import DICT_SET, ui_num
from utility.static import now, strf_time, strp_time, timedelta_sec, int_hms


class ZmqRecv(QThread):
    signal1 = pyqtSignal(tuple)
    signal2 = pyqtSignal(tuple)
    signal3 = pyqtSignal(int)

    def __init__(self, sstgQs):
        super().__init__()
        self.sstgQs = sstgQs
        zctx = zmq.Context()
        self.sock = zctx.socket(zmq.SUB)
        self.sock.connect('tcp://localhost:5777')
        self.sock.setsockopt_string(zmq.SUBSCRIBE, '')

    def run(self):
        while True:
            msg  = self.sock.recv_string()
            data = self.sock.recv_pyobj()
            if msg == 'tickdata':
                # noinspection PyUnresolvedReferences
                self.signal1.emit(data)
            elif msg == 'focuscodes':
                for q in self.sstgQs:
                    q.put(data)
            elif msg == 'logininfo':
                # noinspection PyUnresolvedReferences
                self.signal2.emit(data)
            elif msg == 'operation':
                # noinspection PyUnresolvedReferences
                self.signal3.emit(data)


class Updater(QThread):
    signal = pyqtSignal(tuple)

    def __init__(self, sreceivQ):
        super().__init__()
        self.sreceivQ = sreceivQ

    def run(self):
        while True:
            data = self.sreceivQ.get()
            # noinspection PyUnresolvedReferences
            self.signal.emit(data)


class ReceiverKiwoomClient:
    def __init__(self, qlist):
        app = QApplication(sys.argv)

        self.kwzservQ = qlist[0]
        self.sreceivQ = qlist[1]
        self.straderQ = qlist[2]
        self.sstgQs   = qlist[3]
        self.dict_set = DICT_SET

        self.dict_name   = {}
        self.dict_code   = {}
        self.dict_sgbn   = {}
        self.tuple_jang  = ()
        self.tuple_order = ()
        self.tuple_kosd  = ()
        self.operation   = 1
        self.hoga_code   = None
        self.dict_bool   = {
            '장중단타전략시작': False,
            '프로세스종료': False
        }

        curr_time = now()
        remaintime = (strp_time('%Y%m%d%H%M%S', strf_time('%Y%m%d') + '090100') - curr_time).total_seconds()
        self.dict_time = {'휴무종료': timedelta_sec(remaintime) if remaintime > 0 else None}

        self.updater = Updater(self.sreceivQ)
        # noinspection PyUnresolvedReferences
        self.updater.signal.connect(self.UpdateTuple)
        self.updater.start()

        self.zmqrecv = ZmqRecv(self.sstgQs)
        # noinspection PyUnresolvedReferences
        self.zmqrecv.signal1.connect(self.UpdateTickData)
        # noinspection PyUnresolvedReferences
        self.zmqrecv.signal2.connect(self.UpdateLoginInfo)
        # noinspection PyUnresolvedReferences
        self.zmqrecv.signal3.connect(self.UpdateOperation)
        self.zmqrecv.start()

        self.qtimer1 = QTimer()
        self.qtimer1.setInterval(1 * 1000)
        # noinspection PyUnresolvedReferences
        self.qtimer1.timeout.connect(self.Scheduler)
        self.qtimer1.start()

        text = '주식 리시버를 시작하였습니다.'
        if self.dict_set['주식알림소리']: self.kwzservQ.put(('sound', text))
        self.kwzservQ.put(('tele', text))
        self.kwzservQ.put(('window', (ui_num['S단순텍스트'], '시스템 명령 실행 알림 - 리시버 시작')))

        app.exec_()

    def UpdateTuple(self, data):
        gubun, data = data
        if gubun == '잔고목록':
            self.tuple_jang = data
        elif gubun == '주문목록':
            self.tuple_order = data
        elif gubun == '호가종목코드':
            self.hoga_code = data
        elif gubun == '설정변경':
            self.dict_set = data

    def UpdateTickData(self, data):
        code, c = data[-3], data[1]
        self.sstgQs[self.dict_sgbn[code]].put(data)
        if code in self.tuple_jang or code in self.tuple_order:
            self.straderQ.put((code, c))
        if self.hoga_code == code:
            name = data[-2]
            c, o, h, low, per, _, ch, _, _, _, _, sgta, _, bids, asks, _, uvi = data[1:18]
            hogadata = data[21:43]
            self.kwzservQ.put(('hoga', (name, c, per, sgta, uvi, o, h, low)))
            self.kwzservQ.put(('hoga', (-asks, ch)))
            self.kwzservQ.put(('hoga', (bids, ch)))
            self.kwzservQ.put(('hoga', (name,) + hogadata + (0, 0)))

    def UpdateLoginInfo(self, data):
        self.tuple_kosd, self.dict_sgbn, self.dict_name, self.dict_code = data
        self.kwzservQ.put(('window', (ui_num['종목명데이터'], self.dict_name, self.dict_code, self.dict_sgbn, '더미')))
        self.straderQ.put(('종목구분번호', self.dict_sgbn))
        for q in self.sstgQs:
            q.put(('종목구분번호', self.dict_sgbn))
            q.put(('코스닥목록', self.tuple_kosd))

    def UpdateOperation(self, data):
        self.operation = data

    def Scheduler(self):
        curr_time = now()
        inthms = int_hms()
        if self.operation == 1 and self.dict_time['휴무종료'] is not None and self.dict_time['휴무종료'] <= curr_time:
            if self.dict_set['휴무프로세스종료'] and not self.dict_bool['프로세스종료']:
                self.ReceiverProcKill()
        if self.operation in (2, 3):
            if not self.dict_bool['장중단타전략시작'] and not self.dict_bool['프로세스종료'] and self.dict_set['주식장초전략종료시간'] <= inthms:
                if self.dict_set['주식장초프로세스종료']:
                    self.ReceiverProcKill()
                else:
                    self.StartJangjungStrategy()
            if self.dict_bool['장중단타전략시작'] and not self.dict_bool['프로세스종료'] and self.dict_set['주식장중전략종료시간'] <= inthms and self.dict_set['주식장중프로세스종료']:
                self.ReceiverProcKill()
        if self.operation == 8 and not self.dict_bool['프로세스종료'] and 153500 <= inthms:
            self.ReceiverProcKill()

    def ReceiverProcKill(self):
        self.dict_bool['프로세스종료'] = True
        self.straderQ.put('프로세스종료')
        QTimer.singleShot(180 * 1000, self.SysExit)

    def StartJangjungStrategy(self):
        self.dict_bool['장중단타전략시작'] = True
        self.kwzservQ.put(('window', (ui_num['S로그텍스트'], '시스템 명령 실행 알림 - 장중 단타 전략 시작')))

    def SysExit(self):
        self.dict_bool['프로세스종료'] = True
        if self.qtimer1.isActive():  self.qtimer1.stop()
        if self.updater.isRunning(): self.updater.quit()
        for q in self.sstgQs:
            q.put('프로세스종료')
        self.kwzservQ.put(('window', (ui_num['S단순텍스트'], '시스템 명령 실행 알림 - 리시버 종료')))
