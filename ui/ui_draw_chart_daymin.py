import pyqtgraph as pg
from PyQt5.QtCore import Qt
from ui.set_style import qfont12, color_fg_bt, color_bg_bt, color_bg_ld, color_cs_hr
from utility.chart_items import MoveavgItem, CandlestickItem, VolumeBarsItem
from utility.setting import ui_num
from utility.static import error_decorator


class DrawChartDayMin:
    def __init__(self, ui):
        self.ui = ui

    @error_decorator
    def draw_chart_daymin(self, data):
        def crosshair(coinn, gubun_, main_pg=None, sub_pg=None):
            if main_pg is not None:
                vLine1 = pg.InfiniteLine()
                vLine1.setPen(pg.mkPen(color_cs_hr, width=0.5, style=Qt.DashLine))
                hLine = pg.InfiniteLine(angle=0)
                hLine.setPen(pg.mkPen(color_cs_hr, width=0.5, style=Qt.DashLine))
                main_pg.addItem(vLine1, ignoreBounds=True)
                main_pg.addItem(hLine, ignoreBounds=True)
                main_vb = main_pg.getViewBox()
                label = pg.TextItem(anchor=(0, 1), color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                label.setFont(qfont12)
                label.setPos(-0.25, self.ui.ctpg_day_ymin if gubun_ == '일봉' else self.ui.ctpg_min_ymin)
                main_pg.addItem(label)
            if sub_pg is not None:
                vLine2 = pg.InfiniteLine()
                vLine2.setPen(pg.mkPen(color_cs_hr, width=0.5, style=Qt.DashLine))
                sub_pg.addItem(vLine2, ignoreBounds=True)
                sub_vb = sub_pg.getViewBox()

            def mouseMoved(evt):
                try:
                    pos = evt[0]
                    if main_pg is not None and main_pg.sceneBoundingRect().contains(pos):
                        mousePoint = main_vb.mapSceneToView(pos)
                        xpont = int(mousePoint.x() + 0.5)
                        xtext = str(int(arry[xpont, 0]))
                        xtext = f'{xtext[:4]}-{xtext[4:6]}-{xtext[6:8]}' if len(xtext) == 8 else f'{xtext[:4]}-{xtext[4:6]}-{xtext[6:8]} {xtext[8:10]}:{xtext[10:12]}'
                        if (self.ui.ctpg_day_ymin if gubun_ == '일봉' else self.ui.ctpg_min_ymin) > 100:
                            ytext = f'{mousePoint.y():,.0f}'
                        elif (self.ui.ctpg_day_ymin if gubun_ == '일봉' else self.ui.ctpg_min_ymin) > 10:
                            ytext = f'{mousePoint.y():,.2f}'
                        elif (self.ui.ctpg_day_ymin if gubun_ == '일봉' else self.ui.ctpg_min_ymin) > 1:
                            ytext = f'{mousePoint.y():,.3f}'
                        else:
                            ytext = f'{mousePoint.y():,.4f}'
                        per   = round((arry[xpont, 4] / arry[xpont - 1, 4] - 1) * 100, 2)
                        dmper = round(arry[xpont, 5] / arry[xpont - 1, 5] * 100, 2) if arry[xpont - 1, 5] != 0 else 0.
                        if coinn:
                            textt = f'Y축 {ytext}\n' \
                                    f'시간 {xtext}\n' \
                                    f'시가 {arry[xpont, 1]:,.4f}\n' \
                                    f'고가 {arry[xpont, 2]:,.4f}\n' \
                                    f'저가 {arry[xpont, 3]:,.4f}\n' \
                                    f'종가 {arry[xpont, 4]:,.4f}\n' \
                                    f'등락율 {per:.2f}%\n' \
                                    f'거래대금 {arry[xpont, 5]:,.0f}\n' \
                                    f'증감비율 {dmper:,.2f}%'
                        else:
                            textt = f'Y축 {ytext}\n' \
                                    f'시간 {xtext}\n' \
                                    f'시가 {arry[xpont, 1]:,.0f}\n' \
                                    f'고가 {arry[xpont, 2]:,.0f}\n' \
                                    f'저가 {arry[xpont, 3]:,.0f}\n' \
                                    f'종가 {arry[xpont, 4]:,.0f}\n' \
                                    f'등락율 {per:.2f}%\n' \
                                    f'거래대금 {arry[xpont, 5]:,.0f}\n' \
                                    f'증감비율 {dmper:,.2f}%'
                        label.setText(textt)
                        last = len(arry)
                        if xpont < last / 3:
                            label.setAnchor((1, 1))
                            label.setPos(last - 1 + 0.25, self.ui.ctpg_day_ymin if gubun_ == '일봉' else self.ui.ctpg_min_ymin)
                        else:
                            label.setAnchor((0, 1))
                            label.setPos(-0.25, self.ui.ctpg_day_ymin if gubun_ == '일봉' else self.ui.ctpg_min_ymin)
                        vLine1.setPos(mousePoint.x())
                        hLine.setPos(mousePoint.y())
                        if sub_pg is not None:
                            vLine2.setPos(mousePoint.x())
                    if sub_pg is not None and sub_pg.sceneBoundingRect().contains(pos):
                        mousePoint = sub_vb.mapSceneToView(pos)
                        vLine1.setPos(mousePoint.x())
                        vLine2.setPos(mousePoint.x())
                except:
                    pass

            main_pg.proxy = pg.SignalProxy(main_pg.scene().sigMouseMoved, rateLimit=20, slot=mouseMoved)

        def getMainLegendText(coinn):
            cc     = arry[-1, 4]
            ema05  = arry[-1, 6]
            ema10  = arry[-1, 7]
            ema20  = arry[-1, 8]
            ema60  = arry[-1, 9]
            ema120 = arry[-1, 10]
            ema240 = arry[-1, 11]
            per    = round((arry[-1, 4] / arry[-2, 4] - 1) * 100, 2)
            if coinn:
                text  = f"이평005 {ema05:,.8f}\n" \
                        f"이평010 {ema10:,.8f}\n" \
                        f"이평020 {ema20:,.8f}\n" \
                        f"이평060 {ema60:,.8f}\n" \
                        f"이평120 {ema120:,.8f}\n" \
                        f"이평240 {ema240:,.8f}\n" \
                        f"현재가    {cc:,.4f}\n" \
                        f"등락율    {per:.2f}%"
            else:
                text  = f"이평005 {ema05:,.3f}\n" \
                        f"이평010 {ema10:,.3f}\n" \
                        f"이평020 {ema20:,.3f}\n" \
                        f"이평060 {ema60:,.3f}\n" \
                        f"이평120 {ema120:,.3f}\n" \
                        f"이평240 {ema240:,.3f}\n" \
                        f"현재가    {cc:,.0f}\n" \
                        f"등락율    {per:.2f}%"
            return text

        def getSubLegendText():
            money = arry[-1, 5]
            per   = round(arry[-1, 5] / arry[-2, 5] * 100, 2) if arry[-2, 5] != 0 else 0.
            textt = f"거래대금 {money:,.0f}\n증감비율 {per:,.2f}%"
            return textt

        """
        '일자', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240'
          0      1      2      3      4        5         6        7        8        9        10        11
        """

        gubun, name, arry = data
        x    = len(arry) - 1
        c    = arry[-1, 4]
        vmax = arry[:, 5].max()
        coin = True if 'KRW' in name or 'USDT' in name else False
        if gubun == ui_num['일봉차트']:
            self.ui.ctpg_day_ymin = min(arry[:, 1:5].min(), arry[:, 6:].min())
            self.ui.ctpg_day_ymax = max(arry[:, 1:5].max(), arry[:, 6:].max())
        else:
            self.ui.ctpg_min_ymin = min(arry[:, 1:5].min(), arry[:, 6:].min())
            self.ui.ctpg_min_ymax = max(arry[:, 1:5].max(), arry[:, 6:].max())

        if gubun == ui_num['일봉차트']:
            if not self.ui.dialog_chart_day.isVisible():
                return
            if self.ui.ctpg_day_name != name or self.ui.ctpg_day_index != arry[-1, 0]:
                self.ui.ctpg_day[1].clear()
                self.ui.ctpg_day[2].clear()
                self.ui.ctpg_day[1].addItem(MoveavgItem(arry))
                self.ui.ctpg_day[1].addItem(CandlestickItem(arry))
                self.ui.ctpg_day_lastmoveavg = MoveavgItem(arry, last=True)
                self.ui.ctpg_day_lastcandle  = CandlestickItem(arry, last=True)
                self.ui.ctpg_day[1].addItem(self.ui.ctpg_day_lastmoveavg)
                self.ui.ctpg_day[1].addItem(self.ui.ctpg_day_lastcandle)
                self.ui.ctpg_day_infiniteline = pg.InfiniteLine(angle=0)
                self.ui.ctpg_day_infiniteline.setPen(pg.mkPen(color_cs_hr))
                self.ui.ctpg_day_infiniteline.setPos(c)
                self.ui.ctpg_day[1].addItem(self.ui.ctpg_day_infiniteline)
                xticks = list(arry[:, 0])
                xticks = [f'{str(x)[4:6]}-{str(x)[6:8]}' for x in xticks]
                xticks = [list(zip(range(len(xticks))[::12], xticks[::12]))]
                self.ui.ctpg_day[1].getAxis('bottom').setTicks(xticks)
                self.ui.ctpg_day[2].addItem(VolumeBarsItem(arry))
                self.ui.ctpg_day_lastmoneybar = VolumeBarsItem(arry, last=True)
                self.ui.ctpg_day[2].addItem(self.ui.ctpg_day_lastmoneybar)
                self.ui.ctpg_day[2].getAxis('bottom').setLabel(text=name)
                self.ui.ctpg_day[2].getAxis('bottom').setTicks(xticks)
                crosshair(coin, '일봉', main_pg=self.ui.ctpg_day[1], sub_pg=self.ui.ctpg_day[2])
                self.ui.ctpg_day_legend1 = pg.TextItem(color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                self.ui.ctpg_day_legend1.setFont(qfont12)
                self.ui.ctpg_day_legend1.setPos(-0.25, self.ui.ctpg_day_ymax)
                self.ui.ctpg_day_legend1.setText(getMainLegendText(coin))
                self.ui.ctpg_day[1].addItem(self.ui.ctpg_day_legend1)
                self.ui.ctpg_day_legend2 = pg.TextItem(color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                self.ui.ctpg_day_legend2.setFont(qfont12)
                self.ui.ctpg_day_legend2.setPos(-0.25, vmax)
                self.ui.ctpg_day_legend2.setText(getSubLegendText())
                self.ui.ctpg_day[2].addItem(self.ui.ctpg_day_legend2)
                # noinspection PyUnboundLocalVariable
                self.ui.ctpg_cvb[16].set_range(0, x, self.ui.ctpg_day_ymin, self.ui.ctpg_day_ymax)
                # noinspection PyUnboundLocalVariable
                self.ui.ctpg_day[1].setRange(xRange=(0, x), yRange=(self.ui.ctpg_day_ymin, self.ui.ctpg_day_ymax))
                self.ui.ctpg_day[2].enableAutoRange(enable=True)
                self.ui.ctpg_day_name  = name
                self.ui.ctpg_day_index = arry[-1, 0]
            else:
                self.ui.ctpg_day[1].removeItem(self.ui.ctpg_day_lastmoveavg)
                self.ui.ctpg_day[1].removeItem(self.ui.ctpg_day_lastcandle)
                self.ui.ctpg_day_lastmoveavg = MoveavgItem(arry, last=True)
                self.ui.ctpg_day_lastcandle  = CandlestickItem(arry, last=True)
                self.ui.ctpg_day[1].addItem(self.ui.ctpg_day_lastmoveavg)
                self.ui.ctpg_day[1].addItem(self.ui.ctpg_day_lastcandle)
                self.ui.ctpg_day_infiniteline.setPos(c)
                self.ui.ctpg_day_legend1.setText(getMainLegendText(coin))
                self.ui.ctpg_day[2].removeItem(self.ui.ctpg_day_lastmoneybar)
                self.ui.ctpg_day_lastmoneybar = VolumeBarsItem(arry, last=True)
                self.ui.ctpg_day[2].addItem(self.ui.ctpg_day_lastmoneybar)
                self.ui.ctpg_day_legend2.setText(getSubLegendText())
        else:
            if not self.ui.dialog_chart_min.isVisible():
                return
            if self.ui.ctpg_min_name != name or self.ui.ctpg_min_index != arry[-1, 0]:
                self.ui.ctpg_min[1].clear()
                self.ui.ctpg_min[2].clear()
                self.ui.ctpg_min[1].addItem(MoveavgItem(arry))
                self.ui.ctpg_min[1].addItem(CandlestickItem(arry))
                self.ui.ctpg_min_lastmoveavg = MoveavgItem(arry, last=True)
                self.ui.ctpg_min_lastcandle  = CandlestickItem(arry, last=True)
                self.ui.ctpg_min[1].addItem(self.ui.ctpg_min_lastmoveavg)
                self.ui.ctpg_min[1].addItem(self.ui.ctpg_min_lastcandle)
                self.ui.ctpg_min_infiniteline = pg.InfiniteLine(angle=0)
                self.ui.ctpg_min_infiniteline.setPen(pg.mkPen(color_cs_hr))
                self.ui.ctpg_min_infiniteline.setPos(c)
                self.ui.ctpg_min[1].addItem(self.ui.ctpg_min_infiniteline)
                xticks = list(arry[:, 0])
                xticks = [f'{str(x)[8:10]}:{str(x)[10:12]}' for x in xticks]
                xticks = [list(zip(range(len(xticks))[::12], xticks[::12]))]
                self.ui.ctpg_min[1].getAxis('bottom').setTicks(xticks)
                self.ui.ctpg_min[2].addItem(VolumeBarsItem(arry))
                self.ui.ctpg_min_lastmoneybar = VolumeBarsItem(arry, last=True)
                self.ui.ctpg_min[2].addItem(self.ui.ctpg_min_lastmoneybar)
                self.ui.ctpg_min[2].getAxis('bottom').setLabel(text=name)
                self.ui.ctpg_min[2].getAxis('bottom').setTicks(xticks)
                crosshair(coin, '분봉', main_pg=self.ui.ctpg_min[1], sub_pg=self.ui.ctpg_min[2])
                self.ui.ctpg_min_legend1 = pg.TextItem(color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                self.ui.ctpg_min_legend1.setFont(qfont12)
                self.ui.ctpg_min_legend1.setPos(-0.25, self.ui.ctpg_min_ymax)
                self.ui.ctpg_min_legend1.setText(getMainLegendText(coin))
                self.ui.ctpg_min[1].addItem(self.ui.ctpg_min_legend1)
                self.ui.ctpg_min_legend2 = pg.TextItem(color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                self.ui.ctpg_min_legend2.setFont(qfont12)
                self.ui.ctpg_min_legend2.setPos(-0.25, vmax)
                self.ui.ctpg_min_legend2.setText(getSubLegendText())
                self.ui.ctpg_min[2].addItem(self.ui.ctpg_min_legend2)
                # noinspection PyUnboundLocalVariable
                self.ui.ctpg_cvb[17].set_range(0, x, self.ui.ctpg_min_ymin, self.ui.ctpg_min_ymax)
                # noinspection PyUnboundLocalVariable
                self.ui.ctpg_min[1].setRange(xRange=(0, x), yRange=(self.ui.ctpg_min_ymin, self.ui.ctpg_min_ymax))
                self.ui.ctpg_min[2].enableAutoRange(enable=True)
                self.ui.ctpg_min_name  = name
                self.ui.ctpg_min_index = arry[-1, 0]
            else:
                self.ui.ctpg_min[1].removeItem(self.ui.ctpg_min_lastmoveavg)
                self.ui.ctpg_min[1].removeItem(self.ui.ctpg_min_lastcandle)
                self.ui.ctpg_min_lastmoveavg = MoveavgItem(arry, last=True)
                self.ui.ctpg_min_lastcandle  = CandlestickItem(arry, last=True)
                self.ui.ctpg_min[1].addItem(self.ui.ctpg_min_lastmoveavg)
                self.ui.ctpg_min[1].addItem(self.ui.ctpg_min_lastcandle)
                self.ui.ctpg_min_infiniteline.setPos(c)
                self.ui.ctpg_min_legend1.setText(getMainLegendText(coin))
                self.ui.ctpg_min[2].removeItem(self.ui.ctpg_min_lastmoneybar)
                self.ui.ctpg_min_lastmoneybar = VolumeBarsItem(arry, last=True)
                self.ui.ctpg_min[2].addItem(self.ui.ctpg_min_lastmoneybar)
                self.ui.ctpg_min_legend2.setText(getSubLegendText())
