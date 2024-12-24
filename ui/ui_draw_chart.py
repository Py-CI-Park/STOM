import win32gui
import pyqtgraph as pg
from PyQt5.QtWidgets import QMessageBox
from ui.ui_crosshair import CrossHair
from ui.ui_get_label_text import get_label_text
from utility.chart_items import ChuseItem
from ui.set_style import qfont12, color_fg_bt, color_bg_bt, color_bg_ld
from stock.login_kiwoom.manuallogin import leftClick, enter_keys, press_keys
from utility.static import error_decorator, strf_time, from_timestamp, thread_decorator


class DrawChart:
    def __init__(self, ui):
        self.ui = ui
        self.crosshair = CrossHair(self.ui)

    @error_decorator
    def draw_chart(self, data):
        def cindex(number):
            return dict_stock[number] if not coin else dict_coin[number]

        """ 주식
        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 거래대금증감, 전일비, 회전율, 전일동시간비, 시가총액, 라운드피겨위5호가이내,
           0      1     2    3    4     5         6         7         8        9      10       11        12           13
        초당매수수량, 초당매도수량, VI해제시간, VI가격, VI호가단위, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량,
            14         15          16      17       18         19            20            21        22
        매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5,
           23       24       25        26       27        28       29        30       31        32
        매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합, 관심종목
           33       34       35        36       37        38       39        40       41       42          43           44
        이동평균60_, 이동평균300_, 이동평균600_, 이동평균1200_, 최고현재가_, 최저현재가_, 체결강도평균_, 최고체결강도_, 최저체결강도,
            45         46          47           48           49         50         51           52           53
        최고초당매수수량_, 최고초당매도수량_, 누적초당매수수량_, 누적초당매도수량_, 초당거래대금평균_, 등락율각도_, 당일거래대금각도_, 전일비각도_
              54            55               56              57              58             59         60            61
        매수가, 매도가
          62    63
        """
        dict_stock = {
            1: 45, 2: 46, 3: 47, 4: 48, 5: 1, 6: 51, 7: 52, 8: 53, 9: 7, 10: 19, 11: 58, 12: 14, 13: 15, 14: 5, 15: 20,
            16: 22, 17: 21, 18: 38, 19: 37, 20: 43, 21: 6, 22: 56, 23: 57, 24: 59, 25: 60, 26: 61, 27: 8, 28: 9, 29: 10,
            30: 11, 40: 44, 41: 62, 42: 63
        }
        """ 코인
        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 초당매수수량, 초당매도수량, 초당거래대금, 고저평균대비등락율,
           0      1     2    3     4     5        6         7         8           9          10            11
        매도총잔량, 매수총잔량, 매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5,
           12        13        14       15       16        17       18        19       20       21        22       23
        매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합, 관심종목,
           24        25       26       27        28       29        30       31       32        33         34           35
        이동평균60_, 이동평균300_, 이동평균600_, 이동평균1200_, 최고현재가_, 최저현재가_, 체결강도평균_, 최고체결강도_, 최저체결강도_,
            36         37           38          39          40         51          42           43          44
        최고초당매수수량_, 최고초당매도수량_, 누적초당매수수량_, 누적초당매도수량_, 초당거래대금평균_, 등락율각도_, 당일거래대금각도_
               45            46              47              48              49           50           51
        매수가, 매도가, 매수가2, 매도가2
          52    53     54      55
        """
        dict_coin = {
            1: 36, 2: 37, 3: 38, 4: 39, 5: 1, 6: 42, 7: 43, 8: 44, 9: 7, 10: 10, 11: 49, 12: 8, 13: 9, 14: 5, 15: 11,
            16: 13, 17: 12, 18: 29, 19: 28, 20: 34, 21: 6, 22: 47, 23: 48, 24: 50, 25: 51, 40: 35, 41: 52, 42: 53,
            43: 54, 44: 55
        }

        self.ui.ChartClear()
        if not self.ui.dialog_chart.isVisible():
            return

        coin, self.ui.ctpg_tik_xticks, self.ui.ctpg_tik_arry, self.ui.buy_index, self.ui.sell_index = data[1:]
        if coin == '차트오류':
            QMessageBox.critical(self.ui.dialog_chart, '오류 알림', '해당 날짜의 데이터가 존재하지 않습니다.\n')
            return

        xmin, xmax = self.ui.ctpg_tik_xticks[0], self.ui.ctpg_tik_xticks[-1]
        if self.ui.ct_pushButtonnn_04.text() == 'CHART 8':
            chart_count = 8
        elif self.ui.ct_pushButtonnn_04.text() == 'CHART 12':
            chart_count = 12
        else:
            chart_count = 16

        code = self.ui.ct_lineEdittttt_04.text()
        date = strf_time('%Y%m%d', from_timestamp(xmin))
        if not coin: self.KiwoomHTSChart(code, date)

        self.ui.ctpg_tik_factors = []
        if self.ui.ct_checkBoxxxxx_01.isChecked():     self.ui.ctpg_tik_factors.append('현재가')
        # self.ui.ctpg_tik_factors.append('MACD')
        # self.ui.ctpg_tik_factors.append('RSI')
        if self.ui.ct_checkBoxxxxx_02.isChecked():     self.ui.ctpg_tik_factors.append('체결강도')
        if self.ui.ct_checkBoxxxxx_03.isChecked():     self.ui.ctpg_tik_factors.append('초당거래대금')
        if self.ui.ct_checkBoxxxxx_04.isChecked():     self.ui.ctpg_tik_factors.append('초당체결수량')
        if self.ui.ct_checkBoxxxxx_05.isChecked():     self.ui.ctpg_tik_factors.append('등락율')
        if self.ui.ct_checkBoxxxxx_06.isChecked():     self.ui.ctpg_tik_factors.append('고저평균대비등락율')
        if self.ui.ct_checkBoxxxxx_07.isChecked():     self.ui.ctpg_tik_factors.append('호가총잔량')
        if self.ui.ct_checkBoxxxxx_08.isChecked():     self.ui.ctpg_tik_factors.append('1호가잔량')
        if self.ui.ct_checkBoxxxxx_09.isChecked():     self.ui.ctpg_tik_factors.append('5호가잔량합')
        if self.ui.ct_checkBoxxxxx_10.isChecked():     self.ui.ctpg_tik_factors.append('당일거래대금')
        if self.ui.ct_checkBoxxxxx_11.isChecked():     self.ui.ctpg_tik_factors.append('누적초당매도수수량')
        if self.ui.ct_checkBoxxxxx_12.isChecked():     self.ui.ctpg_tik_factors.append('등락율각도')
        if self.ui.ct_checkBoxxxxx_13.isChecked():     self.ui.ctpg_tik_factors.append('당일거래대금각도')
        if not coin:
            if self.ui.ct_checkBoxxxxx_14.isChecked(): self.ui.ctpg_tik_factors.append('거래대금증감')
            if self.ui.ct_checkBoxxxxx_15.isChecked(): self.ui.ctpg_tik_factors.append('전일비')
            if self.ui.ct_checkBoxxxxx_16.isChecked(): self.ui.ctpg_tik_factors.append('회전율')
            if self.ui.ct_checkBoxxxxx_17.isChecked(): self.ui.ctpg_tik_factors.append('전일동시간비')
            if self.ui.ct_checkBoxxxxx_18.isChecked(): self.ui.ctpg_tik_factors.append('전일비각도')

        for j in range(len(self.ui.ctpg_tik_arry[0, :])):
            # if j in (cindex(1), cindex(2), cindex(3), cindex(4), cindex(6), cindex(7), cindex(8), cindex(25), 64, 65, 66, 67, 68, 69):
            if j in (cindex(1), cindex(2), cindex(3), cindex(4), cindex(6), cindex(7), cindex(8), cindex(25)):
                self.ui.ctpg_tik_data[j] = [x for x in self.ui.ctpg_tik_arry[:, j] if x != 0]
            else:
                self.ui.ctpg_tik_data[j] = self.ui.ctpg_tik_arry[:, j]

        hms  = from_timestamp(xmax).strftime('%H:%M:%S')
        tlen = len(self.ui.ctpg_tik_xticks)
        len1 = len(self.ui.ctpg_tik_data[cindex(1)])
        len2 = len(self.ui.ctpg_tik_data[cindex(2)])
        len3 = len(self.ui.ctpg_tik_data[cindex(3)])
        len4 = len(self.ui.ctpg_tik_data[cindex(4)])
        len5 = len(self.ui.ctpg_tik_data[cindex(6)])
        len6 = len(self.ui.ctpg_tik_data[cindex(7)])
        len7 = len(self.ui.ctpg_tik_data[cindex(8)])
        len8 = len(self.ui.ctpg_tik_data[cindex(25)])
        # len9 = len(self.ui.ctpg_tik_data[64])
        # len10 = len(self.ui.ctpg_tik_data[65])
        # len11 = len(self.ui.ctpg_tik_data[66])
        # len12 = len(self.ui.ctpg_tik_data[67])
        # len13 = len(self.ui.ctpg_tik_data[68])
        # len14 = len(self.ui.ctpg_tik_data[69])
        chuse_exist = True if len(self.ui.ctpg_tik_arry[self.ui.ctpg_tik_arry[:, cindex(40)] > 0]) > 0 else False

        for i, factor in enumerate(self.ui.ctpg_tik_factors):
            self.ui.ctpg[i].clear()
            ymin, ymax = 0, 0
            if factor == '현재가':
                list_ = self.ui.ctpg_tik_data[cindex(1)] + self.ui.ctpg_tik_data[cindex(2)] + self.ui.ctpg_tik_data[cindex(3)] + self.ui.ctpg_tik_data[cindex(4)] + list(self.ui.ctpg_tik_data[cindex(5)])
                ymax, ymin = max(list_), min(list_)
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                # self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len9:], y=self.ui.ctpg_tik_data[64], pen=(100, 180, 100))
                # self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len10:], y=self.ui.ctpg_tik_data[65], pen=(100, 100, 180))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len1:], y=self.ui.ctpg_tik_data[cindex(1)], pen=(140, 140, 145))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len2:], y=self.ui.ctpg_tik_data[cindex(2)], pen=(120, 120, 125))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len3:], y=self.ui.ctpg_tik_data[cindex(3)], pen=(100, 100, 105))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len4:], y=self.ui.ctpg_tik_data[cindex(4)], pen=(80, 80, 85))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(5)], pen=(200, 50, 50))
                for j, price in enumerate(self.ui.ctpg_tik_arry[:, cindex(41)]):
                    if price > 0:
                        arrow = pg.ArrowItem(angle=-180, tipAngle=60, headLen=10, pen='w', brush='r')
                        arrow.setPos(self.ui.ctpg_tik_xticks[j], price)
                        self.ui.ctpg[i].addItem(arrow)
                for j, price in enumerate(self.ui.ctpg_tik_arry[:, cindex(42)]):
                    if price > 0:
                        arrow = pg.ArrowItem(angle=0, tipAngle=60, headLen=10, pen='w', brush='b')
                        arrow.setPos(self.ui.ctpg_tik_xticks[j], price)
                        self.ui.ctpg[i].addItem(arrow)
                if 'USDT' in code:
                    for j, price in enumerate(self.ui.ctpg_tik_arry[:, cindex(43)]):
                        if price > 0:
                            arrow = pg.ArrowItem(angle=-180, tipAngle=60, headLen=10, pen='w', brush='m')
                            arrow.setPos(self.ui.ctpg_tik_xticks[j], price)
                            self.ui.ctpg[i].addItem(arrow)
                    for j, price in enumerate(self.ui.ctpg_tik_arry[:, cindex(44)]):
                        if price > 0:
                            arrow = pg.ArrowItem(angle=0, tipAngle=60, headLen=10, pen='w', brush='b')
                            arrow.setPos(self.ui.ctpg_tik_xticks[j], price)
                            self.ui.ctpg[i].addItem(arrow)
            # elif factor == 'MACD':
            #     list_ = self.ui.ctpg_tik_data[66] + self.ui.ctpg_tik_data[67] + self.ui.ctpg_tik_data[68]
            #     ymax, ymin = max(list_), min(list_)
            #     if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
            #     self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len11:], y=self.ui.ctpg_tik_data[66], pen=(100, 250, 100))
            #     self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len12:], y=self.ui.ctpg_tik_data[67], pen=(250, 100, 100))
            #     self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len13:], y=self.ui.ctpg_tik_data[68], pen=(100, 100, 250))
            # elif factor == 'RSI':
            #     ymax, ymin = max(self.ui.ctpg_tik_data[69]), min(self.ui.ctpg_tik_data[69])
            #     if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
            #     self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len14:], y=self.ui.ctpg_tik_data[69], pen=(250, 100, 100))
            elif factor == '체결강도':
                ymax, ymin = max(self.ui.ctpg_tik_data[cindex(7)]), min(self.ui.ctpg_tik_data[cindex(8)])
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len5:], y=self.ui.ctpg_tik_data[cindex(6)], pen=(50, 50, 200))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len6:], y=self.ui.ctpg_tik_data[cindex(7)], pen=(200, 50, 50))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len7:], y=self.ui.ctpg_tik_data[cindex(8)], pen=(50, 200, 200))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(9)], pen=(50, 200, 50))
            elif factor == '초당거래대금':
                ymax, ymin = self.ui.ctpg_tik_data[cindex(10)].max(), self.ui.ctpg_tik_data[cindex(10)].min()
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(10)], pen=(200, 50, 50))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(11)], pen=(50, 200, 50))
            elif factor == '초당체결수량':
                ymax, ymin = max(self.ui.ctpg_tik_data[cindex(12)].max(), self.ui.ctpg_tik_data[cindex(13)].max()), min(self.ui.ctpg_tik_data[cindex(12)].min(), self.ui.ctpg_tik_data[cindex(13)].min())
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(12)], pen=(200, 50, 50))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(13)], pen=(50, 50, 200))
            elif factor == '등락율':
                ymax, ymin = self.ui.ctpg_tik_data[cindex(14)].max(), self.ui.ctpg_tik_data[cindex(14)].min()
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(14)], pen=(200, 50, 200))
            elif factor == '고저평균대비등락율':
                ymax, ymin = self.ui.ctpg_tik_data[cindex(15)].max(), self.ui.ctpg_tik_data[cindex(15)].min()
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(15)], pen=(50, 200, 200))
            elif factor == '호가총잔량':
                ymax, ymin = max(self.ui.ctpg_tik_data[cindex(16)].max(), self.ui.ctpg_tik_data[cindex(17)].max()), min(self.ui.ctpg_tik_data[cindex(16)].min(), self.ui.ctpg_tik_data[cindex(17)].min())
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(16)], pen=(200, 50, 50))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(17)], pen=(50, 50, 200))
            elif factor == '1호가잔량':
                ymax, ymin = max(self.ui.ctpg_tik_data[cindex(18)].max(), self.ui.ctpg_tik_data[cindex(19)].max()), min(self.ui.ctpg_tik_data[cindex(18)].min(), self.ui.ctpg_tik_data[cindex(19)].min())
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(18)], pen=(200, 50, 50))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(19)], pen=(50, 50, 200))
            elif factor == '5호가잔량합':
                ymax, ymin = self.ui.ctpg_tik_data[cindex(20)].max(), self.ui.ctpg_tik_data[cindex(20)].min()
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(20)], pen=(200, 50, 50))
            elif factor == '당일거래대금':
                ymax, ymin = self.ui.ctpg_tik_data[cindex(21)].max(), self.ui.ctpg_tik_data[cindex(21)].min()
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(21)], pen=(200, 50, 50))
            elif factor == '누적초당매도수수량':
                ymax, ymin = max(self.ui.ctpg_tik_data[cindex(22)].max(), self.ui.ctpg_tik_data[cindex(23)].max()), min(self.ui.ctpg_tik_data[cindex(22)].min(), self.ui.ctpg_tik_data[cindex(23)].min())
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(22)], pen=(200, 50, 50))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(23)], pen=(50, 50, 200))
            elif factor == '등락율각도':
                ymax, ymin = max(self.ui.ctpg_tik_data[cindex(24)]), min(self.ui.ctpg_tik_data[cindex(24)])
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(24)], pen=(200, 50, 50))
            elif factor == '당일거래대금각도':
                ymax, ymin = max(self.ui.ctpg_tik_data[cindex(25)]), min(self.ui.ctpg_tik_data[cindex(25)])
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len8:], y=self.ui.ctpg_tik_data[cindex(25)], pen=(200, 50, 50))
            elif factor == '전일비각도':
                ymax, ymin = self.ui.ctpg_tik_data[cindex(26)].max(), self.ui.ctpg_tik_data[cindex(26)].min()
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(26)], pen=(200, 50, 50))
            elif factor == '거래대금증감':
                ymax, ymin = self.ui.ctpg_tik_data[cindex(27)].max(), self.ui.ctpg_tik_data[cindex(27)].min()
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(27)], pen=(200, 50, 50))
            elif factor == '전일비':
                ymax, ymin = self.ui.ctpg_tik_data[cindex(28)].max(), self.ui.ctpg_tik_data[cindex(28)].min()
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(28)], pen=(200, 50, 50))
            elif factor == '회전율':
                ymax, ymin = self.ui.ctpg_tik_data[cindex(29)].max(), self.ui.ctpg_tik_data[cindex(29)].min()
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(29)], pen=(200, 50, 50))
            elif factor == '전일동시간비':
                ymax, ymin = self.ui.ctpg_tik_data[cindex(30)].max(), self.ui.ctpg_tik_data[cindex(30)].min()
                if chuse_exist: self.ui.ctpg[i].addItem(ChuseItem(self.ui.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ui.ctpg_tik_xticks))
                self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(30)], pen=(200, 50, 50))

            if self.ui.ct_checkBoxxxxx_22.isChecked():
                legend = pg.TextItem(anchor=(1, 0), color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                legend.setText(get_label_text(coin, self.ui.ctpg_tik_arry, -1, self.ui.ctpg_tik_factors[i], hms))
                legend.setFont(qfont12)
                legend.setPos(xmax, ymax)
                self.ui.ctpg[i].addItem(legend)
                self.ui.ctpg_tik_legend[i] = legend

            if i != 0: self.ui.ctpg[i].setXLink(self.ui.ctpg[0])
            self.SetRangeCtpg(i, xmin, xmax, ymin, ymax)
            if self.ui.ct_checkBoxxxxx_22.isChecked(): self.ui.ctpg_tik_legend[i].setPos(self.ui.ctpg_cvb[i].state['viewRange'][0][1], self.ui.ctpg_cvb[i].state['viewRange'][1][1])
            if i == chart_count - 1: break

        if self.ui.ct_checkBoxxxxx_21.isChecked():
            if chart_count == 8:    self.crosshair.crosshair(False, coin, self.ui.ctpg[0], self.ui.ctpg[1], self.ui.ctpg[2], self.ui.ctpg[3], self.ui.ctpg[4], self.ui.ctpg[5], self.ui.ctpg[6], self.ui.ctpg[7])
            elif chart_count == 12: self.crosshair.crosshair(False, coin, self.ui.ctpg[0], self.ui.ctpg[1], self.ui.ctpg[2], self.ui.ctpg[3], self.ui.ctpg[4], self.ui.ctpg[5], self.ui.ctpg[6], self.ui.ctpg[7], self.ui.ctpg[8], self.ui.ctpg[9], self.ui.ctpg[10], self.ui.ctpg[11])
            elif chart_count == 16: self.crosshair.crosshair(False, coin, self.ui.ctpg[0], self.ui.ctpg[1], self.ui.ctpg[2], self.ui.ctpg[3], self.ui.ctpg[4], self.ui.ctpg[5], self.ui.ctpg[6], self.ui.ctpg[7], self.ui.ctpg[8], self.ui.ctpg[9], self.ui.ctpg[10], self.ui.ctpg[11], self.ui.ctpg[12], self.ui.ctpg[13], self.ui.ctpg[14], self.ui.ctpg[15])

        self.ui.ctpg_tik_name = self.ui.ct_lineEdittttt_05.text()
        if not self.ui.database_chart: self.ui.database_chart = True

        if self.ui.dialog_hoga.isVisible() and self.ui.hg_labellllllll_01.text() != '':
            self.ui.hgButtonClicked_02('매수')

    def SetRangeCtpg(self, i, xmin, xmax, ymin, ymax):
        self.ui.ctpg_cvb[i].set_range(xmin, xmax, ymin, ymax)
        self.ui.ctpg[i].setRange(xRange=(xmin, xmax), yRange=(ymin, ymax))

    @thread_decorator
    def KiwoomHTSChart(self, code, date):
        try:
            hwnd_mult = win32gui.FindWindowEx(None, None, None, "[0607] 멀티차트")
            if hwnd_mult != 0:
                win32gui.SetForegroundWindow(hwnd_mult)
                self.HTSControl(code, date, hwnd_mult)
            else:
                hwnd_main = win32gui.FindWindowEx(None, None, '_NKHeroMainClass', None)
                if hwnd_main != 0:
                    win32gui.SetForegroundWindow(hwnd_main)
                    hwnd_mult = win32gui.FindWindowEx(hwnd_main, None, "MDIClient", None)
                    hwnd_mult = win32gui.FindWindowEx(hwnd_mult, None, None, "[0607] 멀티차트")
                    self.HTSControl(code, date, hwnd_mult)
        except:
            pass

    def HTSControl(self, code, date, hwnd_mult):
        try:
            hwnd_part = win32gui.FindWindowEx(hwnd_mult, None, "AfxFrameOrView110", None)
            hwnd_prev = win32gui.FindWindowEx(hwnd_part, None, "AfxWnd110", None)
            hwnd_prev = win32gui.FindWindowEx(hwnd_part, hwnd_prev, "AfxWnd110", None)
            hwnd_part = win32gui.FindWindowEx(hwnd_part, hwnd_prev, "AfxWnd110", None)

            hwnd_prev = win32gui.FindWindowEx(hwnd_part, None, "AfxWnd110", None)
            hwnd_part = win32gui.FindWindowEx(hwnd_part, hwnd_prev, "AfxWnd110", None)

            hwnd_prev = win32gui.FindWindowEx(hwnd_part, None, "AfxWnd110", None)
            hwnd_mid1 = win32gui.FindWindowEx(hwnd_part, hwnd_prev, "AfxWnd110", None)
            hwnd_mid2 = win32gui.FindWindowEx(hwnd_part, hwnd_mid1, "AfxWnd110", None)
            hwnd_mid3 = win32gui.FindWindowEx(hwnd_part, hwnd_mid2, "AfxWnd110", None)

            hwnd_prev = win32gui.FindWindowEx(hwnd_mid2, None, "AfxWnd110", None)
            hwnd_prev = win32gui.FindWindowEx(hwnd_mid2, hwnd_prev, "AfxWnd110", None)
            hwnd_prev = win32gui.FindWindowEx(hwnd_mid2, hwnd_prev, "AfxWnd110", None)
            hwnd_code = win32gui.FindWindowEx(hwnd_mid2, hwnd_prev, "AfxWnd110", None)

            leftClick(15, 15, win32gui.GetDlgItem(hwnd_code, 0x01))
            enter_keys(win32gui.GetDlgItem(hwnd_code, 0x01), code)

            leftClick(15, 15, win32gui.GetDlgItem(hwnd_mid3, 0x834))
            hwnd_prev = win32gui.FindWindowEx(hwnd_mid1, None, "AfxWnd110", None)
            hwnd_part = win32gui.FindWindowEx(hwnd_mid1, hwnd_prev, "AfxWnd110", None)
            hwnd_date = win32gui.FindWindowEx(hwnd_part, None, "AfxWnd110", None)

            leftClick(15, 15, win32gui.GetDlgItem(hwnd_date, 0x7D1))
            press_keys(int(date[0]))
            press_keys(int(date[1]))
            press_keys(int(date[2]))
            press_keys(int(date[3]))
            press_keys(int(date[4]))
            press_keys(int(date[5]))
            press_keys(int(date[6]))
            press_keys(int(date[7]))
            # noinspection PyUnresolvedReferences
            win32api.Sleep(200)

            leftClick(15, 15, win32gui.GetDlgItem(hwnd_mid3, 0x838))
            hwnd_prev = win32gui.FindWindowEx(hwnd_mid1, None, "AfxWnd110", None)
            hwnd_part = win32gui.FindWindowEx(hwnd_mid1, hwnd_prev, "AfxWnd110", None)
            hwnd_date = win32gui.FindWindowEx(hwnd_part, None, "AfxWnd110", None)

            leftClick(15, 15, win32gui.GetDlgItem(hwnd_date, 0x7D1))
            press_keys(int(date[4]))
            press_keys(int(date[5]))
            press_keys(int(date[6]))
            press_keys(int(date[7]))
        except:
            print('키움HTS에 멀티차트가 없거나 일봉, 분봉 차트 두개로 설정되어 있지 않습니다.')
            print('2x1로 좌측은 일봉, 우측은 분봉, 종목일괄변경으로 설정하신 다음 실행하십시오.')

        win32gui.SetForegroundWindow(int(self.ui.winId()))
