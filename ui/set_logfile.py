import logging
from utility.static import strf_time


class SetLogFile:
    def __init__(self, ui_class):
        self.ui = ui_class
        self.set()

    def set(self):
        self.ui.log1 = self.setLog('TraderStock', f"./_log/TS_{strf_time('%Y%m%d')}.txt")
        self.ui.log2 = self.setLog('ReceiverStock', f"./_log/RS_{strf_time('%Y%m%d')}.txt")
        self.ui.log3 = self.setLog('TraderCoin', f"./_log/TC_{strf_time('%Y%m%d')}.txt")
        self.ui.log4 = self.setLog('ReceiverCoin', f"./_log/RC_{strf_time('%Y%m%d')}.txt")
        self.ui.log5 = self.setLog('BacktesterStock', f"./_log/BS_{strf_time('%Y%m%d')}.txt")
        self.ui.log6 = self.setLog('BacktesterCoin', f"./_log/BC_{strf_time('%Y%m%d')}.txt")
        self.ui.log7 = self.setLog('StockOrder', f"./_log/OD_{strf_time('%Y%m%d')}.txt")

    @staticmethod
    def setLog(name, filename):
        log = logging.getLogger(name)
        log.setLevel(logging.INFO)
        log.addHandler(logging.FileHandler(filename=filename, encoding='utf-8'))
        return log
