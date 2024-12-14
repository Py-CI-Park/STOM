import sys
import time
import pandas as pd
from multiprocessing import Process, Queue
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow


class Writer(QThread):
    # 사용자 시그널
    signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            data = windowQ.get()
            # noinspection PyUnresolvedReferences
            # emit하면 signal.connect로 연결해 놓은 함수가 실행된다.
            self.signal.emit(data)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('멀티프로세싱과 큐')
        self.setFixedSize(300, 130)
        self.geometry().center()

        self.qtimer = QTimer()
        self.qtimer.setInterval(1 * 1000)
        # noinspection PyUnresolvedReferences
        self.qtimer.timeout.connect(self.Scheduler)
        self.qtimer.start()

        self.writer = Writer()
        # noinspection PyUnresolvedReferences
        self.writer.signal.connect(self.Update)
        self.writer.start()

    @staticmethod
    def Update(data):
        gubun, df_jg = data
        print(' {:>20} : {:<100}'.format('UI Process', gubun + ' 표시'))
        print('\n')
        print(df_jg)
        print('\n')

    def Scheduler(self):
        # 특정시간에 주식 프로세스 시작
        # 특정시간에 코인 프로세스 시작
        pass


class Updater(QThread):
    signal = pyqtSignal(list)

    def __init__(self, receiverQ_):
        super().__init__()
        self.receiverQ = receiverQ_

    def run(self):
        while True:
            data = self.receiverQ.get()
            # noinspection PyUnresolvedReferences
            self.signal.emit(data)


class Receiver:
    def __init__(self, qlist_):
        """
            0         1           2          3         4
        [windowQ, receiverQ, collectorQ, strategyQ, traderQ]
        """
        app_ = QApplication(sys.argv)

        self.receiverQ  = qlist_[1]
        self.collectorQ = qlist_[2]
        self.strategyQ  = qlist_[3]
        self.traderQ    = qlist_[4]

        self.list_jang  = []

        self.updater = Updater(self.receiverQ)
        # noinspection PyUnresolvedReferences
        self.updater.signal.connect(self.UpdateJango)
        self.updater.start()

        self.qtimer = QTimer()
        self.qtimer.setInterval(2 * 1000)
        # noinspection PyUnresolvedReferences
        self.qtimer.timeout.connect(self.Scheduler)
        self.qtimer.start()

        app_.exec_()

    def UpdateJango(self, data):
        gubun, code = data
        if gubun == '잔고편입' and code not in self.list_jang:
            print(' {:>20} : {:<100}'.format('Receiver Process', f'{gubun} 수신 {code}'))
            self.list_jang.append(code)
        elif gubun == '잔고청산' and code in self.list_jang:
            print(' {:>20} : {:<100}'.format('Receiver Process', f'{gubun} 수신 {code}'))
            self.list_jang.remove(code)

    def Scheduler(self):
        # 실제는 리시버가 증권사 서버로 실시간요청을 하고 그것을 수신한 데이터이다.
        # 현재는 예제용이며 증권사부터 받은 실시간 데이터 대신 단순 텍스트로 수신한다고 가정한다.
        self.OnReceiveRealData('실시간데이터')

    def OnReceiveRealData(self, data):
        print(' {:>20} : {:<100}'.format('Receiver Process', data + ' 수신'))
        # 실시간 데이터 가공 과정 생략
        직전현재가 = 49000
        현재가 = 50000
        code = '005930'
        self.collectorQ.put('가공된 실시간데이터')
        self.strategyQ.put('가공된 실시간데이터')
        if code in self.list_jang and 현재가 != 직전현재가:
            self.traderQ.put(['잔고갱신', code, 현재가])


class Collector:
    def __init__(self, qlist_):
        """
            0         1           2          3         4
        [windowQ, receiverQ, collectorQ, strategyQ, traderQ]
        """
        self.collectorQ = qlist_[2]
        self.Start()

    def Start(self):
        while True:
            data = self.collectorQ.get()
            if data == '가공된 실시간데이터':
                print(' {:>20} : {:<100}'.format('Collector Process', data + ' 수신'))
                self.UpdateTickData()
            elif data == '틱데이터저장':
                self.SaveTickData()

    @staticmethod
    def UpdateTickData():
        # 데이터 기록 코드
        print(' {:>20} : {:<100}'.format('Collector Process', '틱데이터 기록'))

    def SaveTickData(self):
        # 기록된 데이터를 DB로 저장
        pass


class Strategy:
    def __init__(self, qlist_):
        """
            0         1           2          3         4
        [windowQ, receiverQ, collectorQ, strategyQ, traderQ]
        """
        self.strategyQ = qlist_[3]
        self.traderQ   = qlist_[4]

        # columns = ['종목명', '매입가', '현재가', '수익률', '평가손익', '매입금액', '평가금액', '보유수량', '매수시간']
        columns = ['종목명']
        self.df_jg = pd.DataFrame(columns=columns)
        self.list_buy_signal  = []
        self.list_sell_signal = []

        self.Start()

    def Start(self):
        while True:
            data = self.strategyQ.get()
            if data == '가공된 실시간데이터':
                print(' {:>20} : {:<100}'.format('Strategy Process', data + ' 수신'))
                self.Strategy(data)
            elif data[0] == '잔고정보':
                self.df_jg = data[1]
            elif data[0] in ['매수완료', '매수취소']:
                if data[1] in self.list_buy_signal:
                    self.list_buy_signal.remove(data[1])
            elif data[0] in ['매도완료', '매도취소']:
                if data[1] in self.list_sell_signal:
                    self.list_sell_signal.remove(data[1])

    def Strategy(self, data):
        code = '005930'
        print(' {:>20} : {:<100}'.format('Strategy Process', data + '전략 연산'))
        if code not in self.df_jg.index:
            if code not in self.list_buy_signal:
                self.list_buy_signal.append(code)
                self.traderQ.put(['매수 시그널', code])
        else:
            if code not in self.list_sell_signal:
                self.list_sell_signal.append(code)
                self.traderQ.put(['매도 시그널', code])


class Updater2(QThread):
    signal1 = pyqtSignal(list)
    signal2 = pyqtSignal(list)

    def __init__(self, traderQ_):
        super().__init__()
        self.traderQ = traderQ_

    def run(self):
        while True:
            data = self.traderQ.get()
            if data[0] in ['매수 시그널', '매도 시그널']:
                # noinspection PyUnresolvedReferences
                self.signal1.emit(data)
            elif data[0] == '잔고갱신':
                # noinspection PyUnresolvedReferences
                self.signal2.emit(data)


class Trader:
    def __init__(self, qlist_):
        """
            0         1           2          3         4
        [windowQ, receiverQ, collectorQ, strategyQ, traderQ]
        """
        app_ = QApplication(sys.argv)

        self.windowQ   = qlist_[0]
        self.receiverQ = qlist_[1]
        self.strategyQ = qlist_[3]
        self.traderQ   = qlist_[4]

        self.list_buy_order  = []
        self.list_sell_order = []

        # columns = ['종목명', '매입가', '현재가', '수익률', '평가손익', '매입금액', '평가금액', '보유수량', '매수시간']
        columns = ['종목명']
        self.df_jg = pd.DataFrame(columns=columns)

        self.updater = Updater2(self.traderQ)
        # noinspection PyUnresolvedReferences
        self.updater.signal1.connect(self.SendOrder)
        # noinspection PyUnresolvedReferences
        self.updater.signal2.connect(self.UpdateJango)
        self.updater.start()

        self.qtimer = QTimer()
        self.qtimer.setInterval(1 * 1000)
        # noinspection PyUnresolvedReferences
        self.qtimer.timeout.connect(self.Scheduler)
        self.qtimer.start()

        app_.exec_()

    def SendOrder(self, data):
        gubun, code = data
        if gubun == '매수 시그널':
            if code not in self.list_buy_order:
                self.list_buy_order.append(code)
                # 실제는 매수 주문 코드를 작성해야한다.
                print(' {:>20} : {:<100}'.format('Trader Process', '매수 주문 전송'))
                # 주문체결을 받았다고 가정한다.
                self.OnReceiveChejanData('매수체결')
            else:
                self.strategyQ.put(['매수취소', code])
        elif gubun == '매도 시그널':
            if code not in self.list_sell_order:
                self.list_sell_order.append(code)
                # 실제는 매도 주문 코드를 작성해야한다.
                print(' {:>20} : {:<100}'.format('Trader Process', '매도 주문 전송'))
                # 서버로 부터 주문체결을 받았다고 가정한다.
                self.OnReceiveChejanData('매도체결')
            else:
                self.strategyQ.put(['매도취소', code])

    @staticmethod
    def UpdateJango(data):
        gubun, code, c = data
        print(' {:>20} : {:<100}'.format('Trader Process', f'잔고갱신용 현재가 수신 {code} {c}'))
        # self.df_jg 잔고갱신(수익률, 평가금액, 평가손익)

    def OnReceiveChejanData(self, data):
        code = '005930'
        if data == '매수체결':
            print(' {:>20} : {:<100}'.format('Trader Process', '매수 주문 체결 수신'))
            if code in self.list_buy_order:
                self.list_buy_order.remove(code)
            # 잔고갱신(수익률, 평가금액, 평가손익)
            self.df_jg.loc[code] = '삼성전자'
            self.strategyQ.put(['매수완료', code])
            self.receiverQ.put(['잔고편입', code])
        elif data == '매도체결':
            print(' {:>20} : {:<100}'.format('Trader Process', '매도 주문 체결 수신'))
            if code in self.list_sell_order:
                self.list_sell_order.remove(code)
            self.df_jg.drop(index=code, inplace=True)
            self.strategyQ.put(['매도완료', code])
            self.receiverQ.put(['잔고청산', code])
        self.strategyQ.put(['잔고정보', self.df_jg])

    def Scheduler(self):
        self.windowQ.put(['잔고정보', self.df_jg])
        self.strategyQ.put(['잔고정보', self.df_jg])


class CoinReceiver:
    def __init__(self):
        self.start()

    def start(self):
        q1, q2 = Queue(), Queue()
        while True:
            if not q1.empty():
                data = q1.get()
                print(' {:>20} : {:<100}'.format('코인티커수신', data))

            if not q2.empty():
                data = q2.get()
                print(' {:>20} : {:<100}'.format('코인호가수신', data))

            self.Scheduler()

            if q1.empty() and q2.empty():
                time.sleep(0.001)

    def Scheduler(self):
        pass


if __name__ == '__main__':
    windowQ, receiverQ, collectorQ, strategyQ, traderQ = Queue(), Queue(), Queue(), Queue(), Queue()
    qlist = [windowQ, receiverQ, collectorQ, strategyQ, traderQ]

    # 인자 하나만 넣을때는 반드시 "," 콤머!!
    # 데몬일 경우 서브 프로세스를 생성할 수 없다.
    Process(target=Receiver, args=(qlist,), daemon=True).start()
    Process(target=Collector, args=(qlist,), daemon=True).start()
    Process(target=Strategy, args=(qlist,), daemon=True).start()
    Process(target=Trader, args=(qlist,), daemon=True).start()

    app = QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec_()  # 파이큐티 이벤트루프
