import pyqtgraph as pg
from ui.ui_crosshair import CrossHair 
from ui.ui_get_label_text import get_label_text
from ui.set_style import qfont12, color_fg_bt, color_bg_bt, color_bg_ld
from utility.static import error_decorator, from_timestamp, strp_time


class DrawRealChart:
    def __init__(self, ui):
        self.ui = ui
        self.crosshair = CrossHair(self.ui)

    @error_decorator
    def draw_realchart(self, data):
        def cindex(number):
            return dict_stock[number] if not coin else dict_coin[number]

        if not self.ui.dialog_chart.isVisible():
            self.ui.ChartClear()
            return

        name, self.ui.ctpg_tik_arry = data[1:]
        coin = True if 'KRW' in name or 'USDT' in name else False

        if self.ui.ct_pushButtonnn_04.text() == 'CHART 8':
            chart_count = 8
        elif self.ui.ct_pushButtonnn_04.text() == 'CHART 12':
            chart_count = 12
        else:
            chart_count = 16

        if self.ui.ctpg_tik_name != name:
            self.ui.ctpg_tik_item    = {}
            self.ui.ctpg_tik_data    = {}
            self.ui.ctpg_tik_legend  = {}
            self.ui.ctpg_tik_factors = []
            if self.ui.ct_checkBoxxxxx_01.isChecked():     self.ui.ctpg_tik_factors.append('현재가')
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

        """ 주식
        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 거래대금증감, 전일비, 회전율, 전일동시간비, 시가총액, 라운드피겨위5호가이내,
           0      1     2    3    4     5         6         7         8        9      10       11        12           13
        초당매수수량, 초당매도수량, VI해제시간, VI가격, VI호가단위, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량,
            14         15          16      17       18         19            20            21        22
        매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5,
           23       24       25        26       27        28       29        30       31        32
        매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합,
           33       34       35        36       37        38       39        40       41       42          43
        이동평균60_, 이동평균300_, 이동평균600_, 이동평균1200_, 최고현재가_, 최저현재가_, 체결강도평균_, 최고체결강도_, 최저체결강도,
            44         45          46           47           48         49         50           51           52
        최고초당매수수량_, 최고초당매도수량_, 누적초당매수수량_, 누적초당매도수량_, 초당거래대금평균_, 등락율각도_, 당일거래대금각도_, 전일비각도_
              53            54               55              56              57           58           59           60
        """
        dict_stock = {
            1: 44, 2: 45, 3: 46, 4: 47, 5: 1, 6: 50, 7: 51, 8: 52, 9: 7, 10: 19, 11: 57, 12: 14, 13: 15, 14: 5, 15: 20,
            16: 22, 17: 21, 18: 38, 19: 37, 20: 43, 21: 6, 22: 55, 23: 56, 24: 58, 25: 59, 26: 60, 27: 8, 28: 9, 29: 10,
            30: 11
        }
        """ 코인
        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 초당매수수량, 초당매도수량, 초당거래대금, 고저평균대비등락율,
           0      1     2    3     4     5        6         7         8           9          10            11
        매도총잔량, 매수총잔량, 매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5,
           12        13        14       15       16        17       18        19       20       21        22       23
        매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합,
           24        25       26       27        28       29        30       31       32        33         34
        이동평균60_, 이동평균300_, 이동평균600_, 이동평균1200_, 최고현재가_, 최저현재가_, 체결강도평균_, 최고체결강도_, 최저체결강도_,
            35         36           37           38          39         40         41           42          43
        최고초당매수수량_, 최고초당매도수량_, 누적초당매수수량_, 누적초당매도수량_, 초당거래대금평균_, 등락율각도_, 당일거래대금각도_
               44            45              46              47              48           49            50
        """
        dict_coin = {
            1: 35, 2: 36, 3: 37, 4: 38, 5: 1, 6: 41, 7: 42, 8: 43, 9: 7, 10: 10, 11: 48, 12: 8, 13: 9, 14: 5, 15: 11,
            16: 13, 17: 12, 18: 29, 19: 28, 20: 34, 21: 6, 22: 46, 23: 47, 24: 49, 25: 50
        }

        for j in range(len(self.ui.ctpg_tik_arry[0, :])):
            if j in (cindex(1), cindex(2), cindex(3), cindex(4), cindex(6), cindex(7), cindex(8), cindex(25)):
                self.ui.ctpg_tik_data[j] = [x for x in self.ui.ctpg_tik_arry[:, j] if x != 0]
            else:
                self.ui.ctpg_tik_data[j] = self.ui.ctpg_tik_arry[:, j]

        self.ui.ctpg_tik_xticks = [strp_time('%Y%m%d%H%M%S', str(int(x))).timestamp() for x in self.ui.ctpg_tik_data[0]]
        xmin, xmax = self.ui.ctpg_tik_xticks[0], self.ui.ctpg_tik_xticks[-1]
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

        if self.ui.ctpg_tik_name != name:
            for i, factor in enumerate(self.ui.ctpg_tik_factors):
                self.ui.ctpg[i].clear()
                ymin, ymax = 0, 0
                if factor == '현재가':
                    self.ui.ctpg_tik_item[1] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len1:], y=self.ui.ctpg_tik_data[cindex(1)], pen=(140, 140, 145))
                    self.ui.ctpg_tik_item[2] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len2:], y=self.ui.ctpg_tik_data[cindex(2)], pen=(120, 120, 125))
                    self.ui.ctpg_tik_item[3] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len3:], y=self.ui.ctpg_tik_data[cindex(3)], pen=(100, 100, 105))
                    self.ui.ctpg_tik_item[4] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len4:], y=self.ui.ctpg_tik_data[cindex(4)], pen=(80, 80, 85))
                    self.ui.ctpg_tik_item[5] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(5)], pen=(200, 50, 50))
                    self.ui.ctpg_tik_cline = pg.InfiniteLine(angle=0)
                    self.ui.ctpg_tik_cline.setPen(pg.mkPen(color_fg_bt))
                    self.ui.ctpg_tik_cline.setPos(self.ui.ctpg_tik_data[cindex(5)][-1])
                    self.ui.ctpg[i].addItem(self.ui.ctpg_tik_cline)
                    list_ = self.ui.ctpg_tik_data[cindex(1)] + self.ui.ctpg_tik_data[cindex(2)] + self.ui.ctpg_tik_data[cindex(3)] + self.ui.ctpg_tik_data[cindex(4)] + list(self.ui.ctpg_tik_data[cindex(5)])
                    ymax, ymin = max(list_), min(list_)
                elif factor == '체결강도':
                    self.ui.ctpg_tik_item[6] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len5:], y=self.ui.ctpg_tik_data[cindex(6)], pen=(50, 50, 200))
                    self.ui.ctpg_tik_item[7] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len6:], y=self.ui.ctpg_tik_data[cindex(7)], pen=(200, 50, 50))
                    self.ui.ctpg_tik_item[8] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len7:], y=self.ui.ctpg_tik_data[cindex(8)], pen=(50, 200, 200))
                    self.ui.ctpg_tik_item[9] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(9)], pen=(50, 200, 50))
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(7)]), min(self.ui.ctpg_tik_data[cindex(8)])
                elif factor == '초당거래대금':
                    self.ui.ctpg_tik_item[10] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(10)], pen=(200, 50, 50))
                    self.ui.ctpg_tik_item[11] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(11)], pen=(50, 200, 50))
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(10)].max(), self.ui.ctpg_tik_data[cindex(10)].min()
                elif factor == '초당체결수량':
                    self.ui.ctpg_tik_item[12] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(12)], pen=(200, 50, 50))
                    self.ui.ctpg_tik_item[13] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(13)], pen=(50, 50, 200))
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(12)].max(), self.ui.ctpg_tik_data[cindex(13)].max()), min(self.ui.ctpg_tik_data[cindex(12)].min(), self.ui.ctpg_tik_data[cindex(13)].min())
                elif factor == '등락율':
                    self.ui.ctpg_tik_item[14] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(14)], pen=(200, 50, 200))
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(14)].max(), self.ui.ctpg_tik_data[cindex(14)].min()
                elif factor == '고저평균대비등락율':
                    self.ui.ctpg_tik_item[15] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(15)], pen=(50, 200, 200))
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(15)].max(), self.ui.ctpg_tik_data[cindex(15)].min()
                elif factor == '호가총잔량':
                    self.ui.ctpg_tik_item[16] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(16)], pen=(200, 50, 50))
                    self.ui.ctpg_tik_item[17] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(17)], pen=(50, 50, 200))
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(16)].max(), self.ui.ctpg_tik_data[cindex(17)].max()), min(self.ui.ctpg_tik_data[cindex(16)].min(), self.ui.ctpg_tik_data[cindex(17)].min())
                elif factor == '1호가잔량':
                    self.ui.ctpg_tik_item[18] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(18)], pen=(200, 50, 50))
                    self.ui.ctpg_tik_item[19] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(19)], pen=(50, 50, 200))
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(18)].max(), self.ui.ctpg_tik_data[cindex(19)].max()), min(self.ui.ctpg_tik_data[cindex(18)].min(), self.ui.ctpg_tik_data[cindex(19)].min())
                elif factor == '5호가잔량합':
                    self.ui.ctpg_tik_item[20] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(20)], pen=(200, 50, 50))
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(20)].max(), self.ui.ctpg_tik_data[cindex(20)].min()
                elif factor == '당일거래대금':
                    self.ui.ctpg_tik_item[21] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(21)], pen=(200, 50, 50))
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(21)].max(), self.ui.ctpg_tik_data[cindex(21)].min()
                elif factor == '누적초당매도수수량':
                    self.ui.ctpg_tik_item[22] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(22)], pen=(200, 50, 50))
                    self.ui.ctpg_tik_item[23] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(23)], pen=(50, 50, 200))
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(22)].max(), self.ui.ctpg_tik_data[cindex(23)].max()), min(self.ui.ctpg_tik_data[cindex(22)].min(), self.ui.ctpg_tik_data[cindex(23)].min())
                elif factor == '등락율각도':
                    self.ui.ctpg_tik_item[24] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(24)], pen=(200, 50, 50))
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(24)]), min(self.ui.ctpg_tik_data[cindex(24)])
                elif factor == '당일거래대금각도':
                    self.ui.ctpg_tik_item[25] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks[tlen - len8:], y=self.ui.ctpg_tik_data[cindex(25)], pen=(200, 50, 50))
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(25)]), min(self.ui.ctpg_tik_data[cindex(25)])
                elif factor == '전일비각도':
                    self.ui.ctpg_tik_item[26] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(26)], pen=(200, 50, 50))
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(26)].max(), self.ui.ctpg_tik_data[cindex(26)].min()
                elif factor == '거래대금증감':
                    self.ui.ctpg_tik_item[27] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(27)], pen=(200, 50, 50))
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(27)].max(), self.ui.ctpg_tik_data[cindex(27)].min()
                elif factor == '전일비':
                    self.ui.ctpg_tik_item[28] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(28)], pen=(200, 50, 50))
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(28)].max(), self.ui.ctpg_tik_data[cindex(28)].min()
                elif factor == '회전율':
                    self.ui.ctpg_tik_item[29] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(29)], pen=(200, 50, 50))
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(29)].max(), self.ui.ctpg_tik_data[cindex(29)].min()
                elif factor == '전일동시간비':
                    self.ui.ctpg_tik_item[30] = self.ui.ctpg[i].plot(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(30)], pen=(200, 50, 50))
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(30)].max(), self.ui.ctpg_tik_data[cindex(30)].min()

                if self.ui.ct_checkBoxxxxx_22.isChecked():
                    legend = pg.TextItem(anchor=(0, 0), color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                    legend.setFont(qfont12)
                    legend.setText(get_label_text(coin, self.ui.ctpg_tik_arry, -1, self.ui.ctpg_tik_factors[i], hms))
                    self.ui.ctpg[i].addItem(legend)
                    self.ui.ctpg_tik_legend[i] = legend

                if i != 0: self.ui.ctpg[i].setXLink(self.ui.ctpg[0])
                self.SetRangeCtpg(i, xmin, xmax, ymin, ymax)
                if self.ui.ct_checkBoxxxxx_22.isChecked():
                    self.ui.ctpg_tik_legend[i].setPos(self.ui.ctpg_cvb[i].state['viewRange'][0][0], self.ui.ctpg_cvb[i].state['viewRange'][1][1])
                if i == chart_count - 1: break

            self.ui.ctpg_tik_name = name
            if self.ui.ct_checkBoxxxxx_21.isChecked():
                if chart_count == 8:    self.crosshair.crosshair(True, coin, self.ui.ctpg[0], self.ui.ctpg[1], self.ui.ctpg[2], self.ui.ctpg[3], self.ui.ctpg[4], self.ui.ctpg[5], self.ui.ctpg[6], self.ui.ctpg[7])
                elif chart_count == 12: self.crosshair.crosshair(True, coin, self.ui.ctpg[0], self.ui.ctpg[1], self.ui.ctpg[2], self.ui.ctpg[3], self.ui.ctpg[4], self.ui.ctpg[5], self.ui.ctpg[6], self.ui.ctpg[7], self.ui.ctpg[8], self.ui.ctpg[9], self.ui.ctpg[10], self.ui.ctpg[11])
                elif chart_count == 16: self.crosshair.crosshair(True, coin, self.ui.ctpg[0], self.ui.ctpg[1], self.ui.ctpg[2], self.ui.ctpg[3], self.ui.ctpg[4], self.ui.ctpg[5], self.ui.ctpg[6], self.ui.ctpg[7], self.ui.ctpg[8], self.ui.ctpg[9], self.ui.ctpg[10], self.ui.ctpg[11], self.ui.ctpg[12], self.ui.ctpg[13], self.ui.ctpg[14], self.ui.ctpg[15])
        else:
            for i, factor in enumerate(self.ui.ctpg_tik_factors):
                ymin, ymax = 0, 0
                if factor == '현재가':
                    list_ = self.ui.ctpg_tik_data[cindex(1)] + self.ui.ctpg_tik_data[cindex(2)] + self.ui.ctpg_tik_data[cindex(3)] + self.ui.ctpg_tik_data[cindex(4)] + list(self.ui.ctpg_tik_data[cindex(5)])
                    ymax, ymin = max(list_), min(list_)
                    self.ui.ctpg_tik_item[1].setData(x=self.ui.ctpg_tik_xticks[tlen - len1:], y=self.ui.ctpg_tik_data[cindex(1)])
                    self.ui.ctpg_tik_item[2].setData(x=self.ui.ctpg_tik_xticks[tlen - len2:], y=self.ui.ctpg_tik_data[cindex(2)])
                    self.ui.ctpg_tik_item[3].setData(x=self.ui.ctpg_tik_xticks[tlen - len3:], y=self.ui.ctpg_tik_data[cindex(3)])
                    self.ui.ctpg_tik_item[4].setData(x=self.ui.ctpg_tik_xticks[tlen - len4:], y=self.ui.ctpg_tik_data[cindex(4)])
                    self.ui.ctpg_tik_item[5].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(5)])
                    self.ui.ctpg_tik_cline.setPos(self.ui.ctpg_tik_data[cindex(5)][-1])
                elif factor == '체결강도':
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(7)]), min(self.ui.ctpg_tik_data[cindex(8)])
                    self.ui.ctpg_tik_item[6].setData(x=self.ui.ctpg_tik_xticks[tlen - len5:], y=self.ui.ctpg_tik_data[cindex(6)])
                    self.ui.ctpg_tik_item[7].setData(x=self.ui.ctpg_tik_xticks[tlen - len6:], y=self.ui.ctpg_tik_data[cindex(7)])
                    self.ui.ctpg_tik_item[8].setData(x=self.ui.ctpg_tik_xticks[tlen - len7:], y=self.ui.ctpg_tik_data[cindex(8)])
                    self.ui.ctpg_tik_item[9].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(9)])
                elif factor == '초당거래대금':
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(10)].max(), self.ui.ctpg_tik_data[cindex(10)].min()
                    self.ui.ctpg_tik_item[10].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(10)])
                    self.ui.ctpg_tik_item[11].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(11)])
                elif factor == '초당체결수량':
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(12)].max(), self.ui.ctpg_tik_data[cindex(13)].max()), min(self.ui.ctpg_tik_data[cindex(12)].min(), self.ui.ctpg_tik_data[cindex(13)].min())
                    self.ui.ctpg_tik_item[12].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(12)])
                    self.ui.ctpg_tik_item[13].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(13)])
                elif factor == '등락율':
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(14)].max(), self.ui.ctpg_tik_data[cindex(14)].min()
                    self.ui.ctpg_tik_item[14].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(14)])
                elif factor == '고저평균대비등락율':
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(15)].max(), self.ui.ctpg_tik_data[cindex(15)].min()
                    self.ui.ctpg_tik_item[15].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(15)])
                elif factor == '호가총잔량':
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(16)].max(), self.ui.ctpg_tik_data[cindex(17)].max()), min(self.ui.ctpg_tik_data[cindex(16)].min(), self.ui.ctpg_tik_data[cindex(17)].min())
                    self.ui.ctpg_tik_item[16].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(16)])
                    self.ui.ctpg_tik_item[17].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(17)])
                elif factor == '1호가잔량':
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(18)].max(), self.ui.ctpg_tik_data[cindex(19)].max()), min(self.ui.ctpg_tik_data[cindex(18)].min(), self.ui.ctpg_tik_data[cindex(19)].min())
                    self.ui.ctpg_tik_item[18].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(18)])
                    self.ui.ctpg_tik_item[19].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(19)])
                elif factor == '5호가잔량합':
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(20)].max(), self.ui.ctpg_tik_data[cindex(20)].min()
                    self.ui.ctpg_tik_item[20].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(20)])
                elif factor == '당일거래대금':
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(21)].max(), self.ui.ctpg_tik_data[cindex(21)].min()
                    self.ui.ctpg_tik_item[21].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(21)])
                elif factor == '누적초당매도수수량':
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(22)].max(), self.ui.ctpg_tik_data[cindex(23)].max()), min(self.ui.ctpg_tik_data[cindex(22)].min(), self.ui.ctpg_tik_data[cindex(23)].min())
                    self.ui.ctpg_tik_item[22].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(22)])
                    self.ui.ctpg_tik_item[23].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(23)])
                elif factor == '등락율각도':
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(24)]), min(self.ui.ctpg_tik_data[cindex(24)])
                    self.ui.ctpg_tik_item[24].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(24)])
                elif factor == '당일거래대금각도':
                    ymax, ymin = max(self.ui.ctpg_tik_data[cindex(25)]), min(self.ui.ctpg_tik_data[cindex(25)])
                    self.ui.ctpg_tik_item[25].setData(x=self.ui.ctpg_tik_xticks[tlen - len8:], y=self.ui.ctpg_tik_data[cindex(25)])
                elif factor == '전일비각도':
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(26)].max(), self.ui.ctpg_tik_data[cindex(26)].min()
                    self.ui.ctpg_tik_item[26].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(26)])
                elif factor == '거래대금증감':
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(27)].max(), self.ui.ctpg_tik_data[cindex(27)].min()
                    self.ui.ctpg_tik_item[27].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(27)])
                elif factor == '전일비':
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(28)].max(), self.ui.ctpg_tik_data[cindex(28)].min()
                    self.ui.ctpg_tik_item[28].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(28)])
                elif factor == '회전율':
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(29)].max(), self.ui.ctpg_tik_data[cindex(29)].min()
                    self.ui.ctpg_tik_item[29].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(29)])
                elif factor == '전일동시간비':
                    ymax, ymin = self.ui.ctpg_tik_data[cindex(30)].max(), self.ui.ctpg_tik_data[cindex(30)].min()
                    self.ui.ctpg_tik_item[30].setData(x=self.ui.ctpg_tik_xticks, y=self.ui.ctpg_tik_data[cindex(30)])

                self.SetRangeCtpg(i, xmin, xmax, ymin, ymax)
                self.SetPosLegendLabel(i, coin, hms)
                if i == chart_count - 1: break

        if self.ui.database_chart: self.ui.database_chart = False

    def SetRangeCtpg(self, i, xmin, xmax, ymin, ymax):
        self.ui.ctpg_cvb[i].set_range(xmin, xmax, ymin, ymax)
        self.ui.ctpg[i].setRange(xRange=(xmin, xmax), yRange=(ymin, ymax))

    def SetPosLegendLabel(self, i, coin, hms):
        if self.ui.ct_checkBoxxxxx_21.isChecked():
            self.ui.ctpg_tik_labels[i].setPos(self.ui.ctpg_cvb[i].state['viewRange'][0][0], self.ui.ctpg_cvb[i].state['viewRange'][1][0])
        if self.ui.ct_checkBoxxxxx_22.isChecked():
            self.ui.ctpg_tik_legend[i].setPos(self.ui.ctpg_cvb[i].state['viewRange'][0][0], self.ui.ctpg_cvb[i].state['viewRange'][1][1])
            self.ui.ctpg_tik_legend[i].setText(get_label_text(coin, self.ui.ctpg_tik_arry, -1, self.ui.ctpg_tik_factors[i], hms))
