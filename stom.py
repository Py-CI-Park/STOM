import zmq
import shutil
import random
import ctypes
import binance
import squarify
import operator
import win32gui
import win32api
import subprocess
import webbrowser

from PIL import Image
from PyQt5.QtGui import QPalette, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, pyqtSlot, QEvent, QUrl,  Qt, QDate, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QMainWindow, QCompleter, QMessageBox, QTableWidgetItem, QApplication, QVBoxLayout, QLineEdit, QPushButton

from ui.set_text import *
from ui.set_style import *
from ui.set_icon import SetIcon
from ui.set_table import SetTable
from ui.set_logtap import SetLogTap
from ui.set_cbtap import SetCoinBack
from ui.set_logfile import SetLogFile
from ui.set_sbtap import SetStockBack
from ui.set_widget import WidgetCreater
from ui.set_setuptap import SetSetupTap
from ui.set_ordertap import SetOrderTap
from ui.set_mainmenu import SetMainMenu
from ui.set_dialog_etc import SetDialogEtc
from ui.set_dialog_back import SetDialogBack
from ui.set_dialog_chart import SetDialogChart

from utility.static import *
from utility.setting import *
from utility.chart_items import *
from utility.hoga import Hoga
from utility.chart import Chart
from utility.sound import Sound
from utility.query import Query
from utility.stomlive import StomLiveClient
from utility.webcrawling import WebCrawling
from utility.telegram_msg import TelegramMsg

from threading import Timer
from matplotlib import font_manager
from matplotlib import pyplot as plt
from multiprocessing import Process, Queue

from coin.kimp import Kimp
from coin.trader_upbit import TraderUpbit
from coin.strategy_upbit import StrategyUpbit
from coin.receiver_upbit import ReceiverUpbit
from coin.receiver_upbit_client import ReceiverUpbitClient
from coin.trader_binance_future import TraderBinanceFuture
from coin.strategy_binance_future import StrategyBinanceFuture
from coin.receiver_binance_future import ReceiverBinanceFuture
from coin.receiver_binance_future_client import ReceiverBinanceFutureClient
from coin.simulator_upbit import ReceiverUpbit2, TraderUpbit2
from coin.simulator_binance import ReceiverBinanceFuture2, TraderBinanceFuture2
from stock.login_kiwoom.manuallogin import leftClick, enter_keys, press_keys

from backtester.back_static import SubTotal, GetMoneytopQuery, RunOptunaServer
from backtester.back_code_test import BackCodeTest
from backtester.backengine_stock import StockBackEngine
from backtester.backengine_stock2 import StockBackEngine2
from backtester.backengine_stock3 import StockBackEngine3
from backtester.backengine_stock4 import StockBackEngine4
from backtester.backengine_coin_upbit import CoinUpbitBackEngine
from backtester.backengine_coin_upbit2 import CoinUpbitBackEngine2
from backtester.backengine_coin_upbit3 import CoinUpbitBackEngine3
from backtester.backengine_coin_upbit4 import CoinUpbitBackEngine4
from backtester.backengine_coin_future import CoinFutureBackEngine
from backtester.backengine_coin_future2 import CoinFutureBackEngine2
from backtester.backengine_coin_future3 import CoinFutureBackEngine3
from backtester.backengine_coin_future4 import CoinFutureBackEngine4
from backtester.backtest import BackTest
from backtester.backfinder import BackFinder
from backtester.optimiz import Optimize
from backtester.optimiz_conditions import OptimizeConditions
from backtester.optimiz_genetic_algorithm import OptimizeGeneticAlgorithm
from backtester.rolling_walk_forward_test import RollingWalkForwardTest


class QuietPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, p_str, p_int, p_str_1):
        pass


class NumericItem(QTableWidgetItem):
    # noinspection PyUnresolvedReferences
    def __lt__(self, other):
        return self.data(Qt.UserRole) < other.data(Qt.UserRole)


class ZmqServ(QThread):
    def __init__(self, wdzservQ_, port_num):
        super().__init__()
        self.wdzservQ_ = wdzservQ_
        self.zctx = zmq.Context()
        self.sock = self.zctx.socket(zmq.PUB)
        self.sock.bind(f'tcp://*:{port_num}')

    def run(self):
        while True:
            msg, data = self.wdzservQ_.get()
            self.sock.send_string(msg, zmq.SNDMORE)
            self.sock.send_pyobj(data)
            if data == '통신종료':
                QThread.sleep(1)
                break
        self.sock.close()
        self.zctx.term()


class ZmqRecv(QThread):
    def __init__(self, qlist_, port_num):
        super().__init__()
        """
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ,  cstgQ, liveQ, kimpQ, wdzservQ
           0        1       2      3       4      5      6      7       8         9         10     11    12      13
        """
        self.windowQ = qlist_[0]
        self.soundQ  = qlist_[1]
        self.queryQ  = qlist_[2]
        self.teleQ   = qlist_[3]
        self.chartQ  = qlist_[4]
        self.hogaQ   = qlist_[5]
        self.liveQ   = qlist_[11]

        self.zctx = zmq.Context()
        self.sock = self.zctx.socket(zmq.SUB)
        self.sock.connect(f'tcp://localhost:{port_num}')
        self.sock.setsockopt_string(zmq.SUBSCRIBE, '')

    def run(self):
        while True:
            msg  = self.sock.recv_string()
            data = self.sock.recv_pyobj()
            if msg == 'window':
                self.windowQ.put(data)
                if data == '통신종료':
                    QThread.sleep(1)
                    break
            elif msg == 'sound':
                self.soundQ.put(data)
            elif msg == 'query':
                self.queryQ.put(data)
            elif msg == 'tele':
                self.teleQ.put(data)
            elif msg == 'chart':
                self.chartQ.put(data)
            elif msg == 'hoga':
                self.hogaQ.put(data)
            elif msg == 'live':
                self.liveQ.put(data)
            elif msg == 'qsize':
                self.windowQ.put(data)
        self.sock.close()
        self.zctx.term()


class Writer(QThread):
    signal1 = pyqtSignal(tuple)
    signal2 = pyqtSignal(tuple)
    signal3 = pyqtSignal(tuple)
    signal4 = pyqtSignal(tuple)
    signal5 = pyqtSignal(tuple)
    signal6 = pyqtSignal(tuple)
    signal7 = pyqtSignal(tuple)
    signal8 = pyqtSignal(tuple)
    signal9 = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        df           = pd.DataFrame
        self.df_list = [df, df, df, df, df, df, df, df]
        self.test    = None

    def run(self):
        gsjm_count = 0
        while True:
            try:
                data = windowQ.get()
                if data[0] == 'qsize':
                    # noinspection PyUnresolvedReferences
                    self.signal9.emit(data[1])
                elif data[0] <= ui_num['DB관리'] or data[0] == ui_num['기업개요']:
                    # noinspection PyUnresolvedReferences
                    self.signal1.emit(data)
                elif ui_num['S실현손익'] <= data[0] <= ui_num['C상세기록']:
                    if data[0] == ui_num['S관심종목']:
                        if not self.test:
                            index = data[1]
                            self.df_list[index] = data[2]
                            gsjm_count += 1
                            if gsjm_count == 8:
                                gsjm_count = 0
                                # noinspection PyTypeChecker
                                df = pd.concat(self.df_list)
                                df.sort_values(by=['d_money'], ascending=False, inplace=True)
                                # noinspection PyUnresolvedReferences
                                self.signal2.emit((ui_num['S관심종목'], df))
                        else:
                            # noinspection PyUnresolvedReferences
                            self.signal2.emit((ui_num['S관심종목'], data[2]))
                    else:
                        # noinspection PyUnresolvedReferences
                        self.signal2.emit(data)
                elif data[0] == ui_num['차트']:
                    # noinspection PyUnresolvedReferences
                    self.signal3.emit(data)
                elif data[0] == ui_num['실시간차트']:
                    # noinspection PyUnresolvedReferences
                    self.signal4.emit(data)
                elif data[0] == ui_num['풍경사진']:
                    # noinspection PyUnresolvedReferences
                    self.signal8.emit(data)
                elif data[0] in (ui_num['일봉차트'], ui_num['분봉차트']):
                    # noinspection PyUnresolvedReferences
                    self.signal7.emit(data)
                elif data[0] in (ui_num['코스피'], ui_num['코스닥']):
                    # noinspection PyUnresolvedReferences
                    self.signal5.emit(data)
                elif data[0] >= ui_num['트리맵']:
                    # noinspection PyUnresolvedReferences
                    self.signal6.emit(data)
                elif data == '복기모드시작':
                    self.test = True
                elif data == '복기모드종료':
                    self.test = False
            except:
                pass


class Window(QMainWindow):
    def __init__(self, auto_run_):
        super().__init__()
        self.auto_run = auto_run_
        self.dict_set = DICT_SET
        self.hogaQ    = hogaQ
        self.main_btn = 0
        self.counter  = 0
        self.cpu_per  = 0
        self.int_time = int_hms()

        self.wc = WidgetCreater(self)
        SetLogFile(self)
        SetIcon(self)
        SetMainMenu(self, self.wc)
        SetTable(self, self.wc)
        SetStockBack(self, self.wc)
        SetCoinBack(self, self.wc)
        SetLogTap(self, self.wc)
        SetSetupTap(self, self.wc)
        SetOrderTap(self, self.wc)
        SetDialogChart(self, self.wc)
        SetDialogEtc(self, self.wc)
        SetDialogBack(self, self.wc)

        self.videoWidget = QVideoWidget(self)
        self.videoWidget.setGeometry(0, 0, 1403, 763)
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile('./ui/intro.mp4')))
        # noinspection PyUnresolvedReferences
        self.mediaPlayer.stateChanged.connect(self.windowclose)
        if self.dict_set['인트로숨김']:
            self.videoWidget.setVisible(False)
        else:
            self.mediaPlayer.play()

        con1 = sqlite3.connect(DB_SETTING)
        con2 = sqlite3.connect(DB_STOCK_BACK)
        try:
            df = pd.read_sql('SELECT * FROM codename', con1).set_index('index')
        except:
            df = pd.read_sql('SELECT * FROM codename', con2).set_index('index')
        con1.close()
        con2.close()

        self.dict_name = {code: df['종목명'][code] for code in df.index}
        self.dict_code = {name: code for code, name in self.dict_name.items()}

        if len(df) < 10:
            print('setting.db 내에 codename 테이블이 갱신되지 않았습니다.')
            print('주식 수동로그인을 한번 실행하면 codename 테이블이 갱신됩니다.')

        con = sqlite3.connect(DB_COIN_TICK)
        df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        con.close()

        self.ct_lineEdittttt_04.setCompleter(QCompleter(list(self.dict_code.values())))
        self.ct_lineEdittttt_05.setCompleter(QCompleter(list(self.dict_name.values()) + df['name'].to_list()))

        self.back_schedul     = False
        self.showQsize        = False
        self.test_pause       = False
        self.image_search     = False
        self.auto_mode        = False
        self.database_control = False
        self.ssicon_alert     = False
        self.csicon_alert     = False
        self.lgicon_alert     = False
        self.database_chart   = False
        self.daydata_download = False
        self.tickdata_save    = False
        self.backtest_engine  = False
        self.time_sync        = False
        self.extend_window    = False
        self.back_condition   = True

        self.animation        = None
        self.webEngineView    = None
        self.df_test          = None
        self.dict_sgbn        = None
        self.dict_cn          = None
        self.dict_mt          = None

        self.dict_info        = {}
        self.vars             = {}
        self.buy_index        = []
        self.sell_index       = []
        self.back_procs       = []
        self.back_pques       = []
        self.bact_procs       = []
        self.bact_pques       = []
        self.avg_list         = []
        self.back_count       = 0
        self.startday         = 0
        self.endday           = 0
        self.starttime        = 0
        self.endtime          = 0
        self.ct_test          = 0
        self.back_scount      = 0

        self.stock_simulator_alive = False
        self.backengin_window_open = False
        self.optuna_window_open    = False

        self.proc_backtester_bb    = None
        self.proc_backtester_bf    = None
        self.proc_backtester_o     = None
        self.proc_backtester_ov    = None
        self.proc_backtester_ovc   = None
        self.proc_backtester_ot    = None
        self.proc_backtester_ovt   = None
        self.proc_backtester_ovct  = None
        self.proc_backtester_or    = None
        self.proc_backtester_orv   = None
        self.proc_backtester_orvc  = None
        self.proc_backtester_b     = None
        self.proc_backtester_bv    = None
        self.proc_backtester_bvc   = None
        self.proc_backtester_bt    = None
        self.proc_backtester_bvt   = None
        self.proc_backtester_bvct  = None
        self.proc_backtester_br    = None
        self.proc_backtester_brv   = None
        self.proc_backtester_brvc  = None
        self.proc_backtester_og    = None
        self.proc_backtester_ogv   = None
        self.proc_backtester_ogvc  = None
        self.proc_backtester_oc    = None
        self.proc_backtester_ocv   = None
        self.proc_backtester_ocvc  = None

        self.proc_stomlive_stock   = None
        self.proc_receiver_coin    = None
        self.proc_strategy_coin    = None
        self.proc_trader_coin      = None
        self.proc_coin_kimp        = None
        self.proc_simulator_rv     = None
        self.proc_simulator_td     = None

        self.backdetail_list       = None
        self.backcheckbox_list     = None
        self.order_combo_name_list = []

        self.ctpg_tik_name         = None
        self.ctpg_tik_cline        = None
        self.ctpg_tik_hline        = None
        self.ctpg_tik_xticks       = None
        self.ctpg_tik_arry         = None
        self.ctpg_tik_legend       = {}
        self.ctpg_tik_item         = {}
        self.ctpg_tik_data         = {}
        self.ctpg_tik_factors      = []
        self.ctpg_tik_labels       = []

        self.ctpg_day_name         = None
        self.ctpg_day_index        = None
        self.ctpg_day_lastmoveavg  = None
        self.ctpg_day_lastcandle   = None
        self.ctpg_day_infiniteline = None
        self.ctpg_day_lastmoneybar = None
        self.ctpg_day_legend1      = None
        self.ctpg_day_legend2      = None
        self.ctpg_day_ymin         = 0
        self.ctpg_day_ymax         = 0

        self.ctpg_min_name         = None
        self.ctpg_min_index        = None
        self.ctpg_min_lastmoveavg  = None
        self.ctpg_min_lastcandle   = None
        self.ctpg_min_infiniteline = None
        self.ctpg_min_lastmoneybar = None
        self.ctpg_min_legend1      = None
        self.ctpg_min_legend2      = None
        self.ctpg_min_ymin         = 0
        self.ctpg_min_ymax         = 0

        self.srqsize = 0
        self.stqsize = 0
        self.ssqsize = 0

        self.df_kp  = None
        self.df_kd  = None
        self.tm_ax1 = None
        self.tm_ax2 = None
        self.df_tm1 = None
        self.df_tm2 = None
        self.tm_cl1 = None
        self.tm_cl2 = None
        self.tm_dt  = False
        self.tm_mc1 = 0
        self.tm_mc2 = 0

        subprocess.Popen('python kiwoom_manager.py')

        port_num = GetPortNumber()
        self.zmqserv = ZmqServ(wdzservQ, port_num)
        self.zmqserv.start()

        self.zmqrecv = ZmqRecv(qlist, port_num + 1)
        self.zmqrecv.start()

        self.qtimer1 = QTimer()
        self.qtimer1.setInterval(1 * 1000)
        # noinspection PyUnresolvedReferences
        self.qtimer1.timeout.connect(self.ProcessStarter)
        self.qtimer1.start()

        self.qtimer2 = QTimer()
        self.qtimer2.setInterval(500)
        # noinspection PyUnresolvedReferences
        self.qtimer2.timeout.connect(self.UpdateProgressBar)
        self.qtimer2.start()

        self.qtimer3 = QTimer()
        self.qtimer3.setInterval(1 * 1000)
        # noinspection PyUnresolvedReferences
        self.qtimer3.timeout.connect(self.UpdateCpuper)
        self.qtimer3.start()

        self.writer = Writer()
        # noinspection PyUnresolvedReferences
        self.writer.signal1.connect(self.UpdateTexedit)
        # noinspection PyUnresolvedReferences
        self.writer.signal2.connect(self.UpdateTablewidget)
        # noinspection PyUnresolvedReferences
        self.writer.signal3.connect(self.DrawChart)
        # noinspection PyUnresolvedReferences
        self.writer.signal4.connect(self.DrawRealChart)
        # noinspection PyUnresolvedReferences
        self.writer.signal5.connect(self.DrawRealJisuChart)
        # noinspection PyUnresolvedReferences
        self.writer.signal6.connect(self.DrawTremap)
        # noinspection PyUnresolvedReferences
        self.writer.signal7.connect(self.DrawChartDayMin)
        # noinspection PyUnresolvedReferences
        self.writer.signal8.connect(self.ImageUpdate)
        # noinspection PyUnresolvedReferences
        self.writer.signal9.connect(self.UpdateSQsize)
        self.writer.start()

        font_name = 'C:/Windows/Fonts/malgun.ttf'
        font_family = font_manager.FontProperties(fname=font_name).get_name()
        plt.rcParams['font.family'] = font_family
        plt.rcParams['axes.unicode_minus'] = False

    def windowclose(self, state):
        if state == QMediaPlayer.StoppedState:
            self.videoWidget.setVisible(False)

    def ShowVideo(self):
        self.videoWidget.setVisible(True)
        self.mediaPlayer.play()

    def ExtendWin(self):
        if self.main_btn not in (2, 3):
            QMessageBox.critical(self, '오류 알림', '전략탭 확장기능은 전략탭에서만 사용할 수 있습니다.')
            return

        if not self.extend_window:
            self.extend_window = True
            self.setFixedSize(1403, 1368)
            self.image_label2.setVisible(True)
            self.progressBarrr.setGeometry(5, 568, 35, 793)
        else:
            self.extend_window = False
            self.setFixedSize(1403, 763)
            self.image_label2.setVisible(False)
            self.progressBarrr.setGeometry(5, 568, 35, 188)

        if self.main_btn == 2:
            self.ss_tab.setGeometry(45, 0, 1353, 1362 if self.extend_window else 757)
            if self.ss_pushButtonn_08.isVisible():
                self.ss_textEditttt_09.setGeometry(7, 10, 1000, 1308 if self.extend_window else 703)
                self.ss_progressBar_01.setGeometry(7, 1323 if self.extend_window else 718, 830, 30)
                self.ss_pushButtonn_08.setGeometry(842, 1323 if self.extend_window else 718, 165, 30)
            elif self.ss_pushButtonn_01.isVisible():
                self.ss_tableWidget_01.setGeometry(7, 40, 1000, 1318 if self.extend_window else 713)
                self.ss_tableWidget_01.setRowCount(60 if self.extend_window else 32)
            elif self.svj_pushButton_01.isVisible():
                self.ss_textEditttt_01.setGeometry(7, 10, 1000, 740 if self.extend_window else 463)
                self.ss_textEditttt_02.setGeometry(7, 756 if self.extend_window else 480, 1000, 602 if self.extend_window else 272)
                self.szoo_pushButon_02.setGeometry(952, 761 if self.extend_window else 483, 50, 20)
            elif self.svc_pushButton_24.isVisible():
                self.ss_textEditttt_01.setGeometry(7, 10, 497, 740 if self.extend_window else 463)
                self.ss_textEditttt_02.setGeometry(7, 756 if self.extend_window else 480, 497, 602 if self.extend_window else 272)
                self.ss_textEditttt_03.setGeometry(509, 10, 497, 740 if self.extend_window else 463)
                self.ss_textEditttt_04.setGeometry(509, 756 if self.extend_window else 480, 497, 602 if self.extend_window else 272)
            elif self.svc_pushButton_21.isVisible():
                self.ss_textEditttt_05.setGeometry(7, 10, 497, 1347 if self.extend_window else 740)
                self.ss_textEditttt_06.setGeometry(509, 10, 497, 1347 if self.extend_window else 740)
            elif self.svo_pushButton_05.isVisible():
                self.ss_textEditttt_07.setGeometry(7, 10, 497, 1347 if self.extend_window else 740)
                self.ss_textEditttt_08.setGeometry(509, 10, 497, 1347 if self.extend_window else 740)
            elif self.sva_pushButton_01.isVisible():
                self.ss_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
                self.ss_textEditttt_04.setGeometry(7, 756 if self.extend_window else 480, 647, 602 if self.extend_window else 272)
                self.ss_textEditttt_06.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)
                self.szoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)
            else:
                self.ss_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
                self.ss_textEditttt_04.setGeometry(7, 756 if self.extend_window else 480, 647, 602 if self.extend_window else 272)
                self.ss_textEditttt_05.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)
                self.szoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)
        else:
            self.cs_tab.setGeometry(45, 0, 1353, 1362 if self.extend_window else 757)
            if self.cs_pushButtonn_08.isVisible():
                self.cs_textEditttt_09.setGeometry(7, 10, 1000, 1308 if self.extend_window else 703)
                self.cs_progressBar_01.setGeometry(7, 1323 if self.extend_window else 718, 830, 30)
                self.cs_pushButtonn_08.setGeometry(842, 1323 if self.extend_window else 718, 165, 30)
            elif self.cs_pushButtonn_01.isVisible():
                self.cs_tableWidget_01.setGeometry(7, 40, 1000, 1318 if self.extend_window else 713)
                self.cs_tableWidget_01.setRowCount(60 if self.extend_window else 32)
            elif self.cvj_pushButton_01.isVisible():
                self.cs_textEditttt_01.setGeometry(7, 10, 1000, 740 if self.extend_window else 463)
                self.cs_textEditttt_02.setGeometry(7, 756 if self.extend_window else 480, 1000, 602 if self.extend_window else 272)
                self.czoo_pushButon_02.setGeometry(952, 761 if self.extend_window else 483, 50, 20)
            elif self.cvc_pushButton_24.isVisible():
                self.cs_textEditttt_01.setGeometry(7, 10, 497, 740 if self.extend_window else 463)
                self.cs_textEditttt_02.setGeometry(7, 756 if self.extend_window else 480, 497, 602 if self.extend_window else 272)
                self.cs_textEditttt_03.setGeometry(509, 10, 497, 740 if self.extend_window else 463)
                self.cs_textEditttt_04.setGeometry(509, 756 if self.extend_window else 480, 497, 602 if self.extend_window else 272)
            elif self.cvc_pushButton_21.isVisible():
                self.cs_textEditttt_05.setGeometry(7, 10, 497, 1347 if self.extend_window else 740)
                self.cs_textEditttt_06.setGeometry(509, 10, 497, 1347 if self.extend_window else 740)
            elif self.cvo_pushButton_05.isVisible():
                self.cs_textEditttt_07.setGeometry(7, 10, 497, 1347 if self.extend_window else 740)
                self.cs_textEditttt_08.setGeometry(509, 10, 497, 1347 if self.extend_window else 740)
            elif self.cva_pushButton_01.isVisible():
                self.cs_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
                self.cs_textEditttt_04.setGeometry(7, 756 if self.extend_window else 480, 647, 602 if self.extend_window else 272)
                self.cs_textEditttt_06.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)
                self.czoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)
            else:
                self.cs_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
                self.cs_textEditttt_04.setGeometry(7, 756 if self.extend_window else 480, 647, 602 if self.extend_window else 272)
                self.cs_textEditttt_05.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)
                self.czoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)

    def ProcessStarter(self):
        inthms    = int_hms()
        inthmsutc = int_hms_utc()

        if self.int_time < 80000 <= inthms:
            SetLogFile(self)
            self.ClearTextEdit()

        A = not self.dict_set['코인장초프로세스종료'] and not self.dict_set['코인장중프로세스종료']
        B = self.dict_set['코인장초프로세스종료'] and inthmsutc < self.dict_set['코인장초전략종료시간']
        C = self.dict_set['코인장중프로세스종료'] and inthmsutc < self.dict_set['코인장중전략종료시간']
        D = inthmsutc > 235000

        if A or B or C or D:
            if self.dict_set['코인리시버']:
                self.CoinReceiverStart()
            if self.dict_set['코인트레이더']:
                self.CoinTraderStart()

        if self.dict_set['코인트레이더'] and A and D and not self.time_sync:
            subprocess.Popen('python64 ./utility/timesync.py')
            self.time_sync = True

        if self.int_time < 90000 <= inthms:
            self.time_sync = False

        if self.dict_set['스톰라이브'] and not self.StockLiveProcessAlive():
            self.proc_stomlive_stock = Process(target=StomLiveClient, args=(qlist,), daemon=True)
            self.proc_stomlive_stock.start()

        if self.dict_set['백테스케쥴실행'] and not self.backtest_engine and now().weekday() == self.dict_set['백테스케쥴요일']:
            if self.int_time < self.dict_set['백테스케쥴시간'] <= inthms:
                self.AutoBackSchedule(1)

        if self.auto_run == 1:
            self.mnButtonClicked_02(stocklogin=True)
            self.auto_run = 0

        self.UpdateWindowTitle()
        self.int_time = inthms

    def CoinReceiverStart(self):
        if not self.CoinReceiverProcessAlive():
            if self.dict_set['리시버공유'] < 2:
                self.proc_receiver_coin = Process(target=ReceiverUpbit if self.dict_set['거래소'] == '업비트' else ReceiverBinanceFuture, args=(qlist,))
            else:
                self.proc_receiver_coin = Process(target=ReceiverUpbitClient if self.dict_set['거래소'] == '업비트' else ReceiverBinanceFutureClient, args=(qlist,))
            self.proc_receiver_coin.start()

    def CoinTraderStart(self):
        if self.dict_set['거래소'] == '업비트' and (self.dict_set['Access_key1'] is None or self.dict_set['Access_key1'] is None):
            QMessageBox.critical(self, '오류 알림', '업비트 계정이 설정되지 않아\n트레이더를 시작할 수 없습니다.\n계정 설정 후 다시 시작하십시오.\n')
            return
        elif self.dict_set['거래소'] == '바이낸스선물' and (self.dict_set['Access_key2'] is None or self.dict_set['Access_key2'] is None):
            QMessageBox.critical(self, '오류 알림', '바이낸스선물 계정이 설정되지 않아\n트레이더를 시작할 수 없습니다.\n계정 설정 후 다시 시작하십시오.\n')
            return

        if not self.CoinStrategyProcessAlive():
            self.proc_strategy_coin = Process(target=StrategyUpbit if self.dict_set['거래소'] == '업비트' else StrategyBinanceFuture, args=(qlist,), daemon=True)
            self.proc_strategy_coin.start()
        if not self.CoinTraderProcessAlive():
            self.proc_trader_coin = Process(target=TraderUpbit if self.dict_set['거래소'] == '업비트' else TraderBinanceFuture, args=(qlist,))
            self.proc_trader_coin.start()
            if self.dict_set['거래소'] == '바이낸스선물':
                self.ctd_tableWidgettt.setColumnCount(len(columns_tdf))
                self.ctd_tableWidgettt.setHorizontalHeaderLabels(columns_tdf)
                self.ctd_tableWidgettt.setColumnWidth(0, 96)
                self.ctd_tableWidgettt.setColumnWidth(1, 90)
                self.ctd_tableWidgettt.setColumnWidth(2, 90)
                self.ctd_tableWidgettt.setColumnWidth(3, 90)
                self.ctd_tableWidgettt.setColumnWidth(4, 140)
                self.ctd_tableWidgettt.setColumnWidth(5, 70)
                self.ctd_tableWidgettt.setColumnWidth(6, 90)
                self.ctd_tableWidgettt.setColumnWidth(7, 90)
                self.cjg_tableWidgettt.setColumnCount(len(columns_jgf))
                self.cjg_tableWidgettt.setHorizontalHeaderLabels(columns_jgf)
                self.cjg_tableWidgettt.setColumnWidth(0, 96)
                self.cjg_tableWidgettt.setColumnWidth(1, 70)
                self.cjg_tableWidgettt.setColumnWidth(2, 115)
                self.cjg_tableWidgettt.setColumnWidth(3, 115)
                self.cjg_tableWidgettt.setColumnWidth(4, 90)
                self.cjg_tableWidgettt.setColumnWidth(5, 90)
                self.cjg_tableWidgettt.setColumnWidth(6, 90)
                self.cjg_tableWidgettt.setColumnWidth(7, 90)
                self.cjg_tableWidgettt.setColumnWidth(8, 90)
                self.cjg_tableWidgettt.setColumnWidth(9, 90)
                self.cjg_tableWidgettt.setColumnWidth(10, 90)
                self.cjg_tableWidgettt.setColumnWidth(11, 90)

    def ClearTextEdit(self):
        self.sst_textEditttt_01.clear()
        self.cst_textEditttt_01.clear()
        self.src_textEditttt_01.clear()
        self.crc_textEditttt_01.clear()

    def UpdateWindowTitle(self):
        inthms = int_hms()
        inthmsutc = int_hms_utc()
        text = 'STOM'
        if self.dict_set['리시버공유'] == 1:
            text = f'{text} Server'
        elif self.dict_set['리시버공유'] == 2:
            text = f'{text} Client'
        if self.dict_set['거래소'] == '바이낸스선물' and self.dict_set['코인트레이더']:
            text = f'{text} | 바이낸스선물'
        elif self.dict_set['거래소'] == '업비트' and self.dict_set['코인트레이더']:
            text = f'{text} | 업비트'
        elif self.dict_set['증권사'] == '키움증권해외선물' and self.dict_set['주식트레이더']:
            text = f'{text} | 키움증권해외선물'
        elif self.dict_set['주식트레이더']:
            text = f'{text} | 키움증권'
        if self.showQsize:
            stqsize = sum((stq.qsize() for stq in self.bact_pques)) if self.bact_pques else 0
            text = f'{text} | sreceivQ[{self.srqsize}] | straderQ[{self.stqsize}] | sstrateyQ[{self.ssqsize}] | ' \
                   f'creceivQ[{creceivQ.qsize()}] | ctraderQ[{ctraderQ.qsize()}] | cstrateyQ[{cstgQ.qsize()}] | ' \
                   f'windowQ[{windowQ.qsize()}] | queryQ[{queryQ.qsize()}] | chartQ[{chartQ.qsize()}] | ' \
                   f'hogaQ[{hogaQ.qsize()}] | soundQ[{soundQ.qsize()} | backstQ[{stqsize}]'
        else:
            if self.dict_set['코인트레이더']:
                text = f'{text} | 모의' if self.dict_set['코인모의투자'] else f'{text} | 실전'
                if inthmsutc < self.dict_set["코인장초전략종료시간"]:
                    text = f'{text} | {self.dict_set["코인장초매수전략"] if self.dict_set["코인장초매수전략"] != "" else "전략사용안함"}'
                else:
                    text = f'{text} | {self.dict_set["코인장중매수전략"] if self.dict_set["코인장중매수전략"] != "" else "전략사용안함"}'
            elif self.dict_set['주식트레이더']:
                text = f'{text} | 모의' if self.dict_set['주식모의투자'] else f'{text} | 실전'
                if inthms < self.dict_set["주식장초전략종료시간"]:
                    text = f'{text} | {self.dict_set["주식장초매수전략"] if self.dict_set["주식장초매수전략"] != "" else "전략사용안함"}'
                else:
                    text = f'{text} | {self.dict_set["주식장중매수전략"] if self.dict_set["주식장중매수전략"] != "" else "전략사용안함"}'
            text = f"{text} | {strf_time('%Y-%m-%d %H:%M:%S')}"
        self.setWindowTitle(text)

    def UpdateProgressBar(self):
        self.progressBarrr.setValue(self.cpu_per)
        self.counter = 0 if self.counter > 999 else self.counter + 1

        self.kp_pushButton.setStyleSheet(style_bc_bb if not self.dialog_kimp.isVisible() else style_bc_bt)
        self.mb_pushButton.setStyleSheet(style_bc_bb if not self.dialog_chart_min.isVisible() else style_bc_bt)
        self.ib_pushButton.setStyleSheet(style_bc_bb if not self.dialog_chart_day.isVisible() else style_bc_bt)
        self.dd_pushButton.setStyleSheet(style_bc_bb if not self.dialog_db.isVisible() else style_bc_bt)
        self.js_pushButton.setStyleSheet(style_bc_bb if not self.dialog_jisu.isVisible() else style_bc_bt)
        self.uj_pushButton.setStyleSheet(style_bc_bb if not self.dialog_tree.isVisible() else style_bc_bt)
        self.gu_pushButton.setStyleSheet(style_bc_bb if not self.dialog_info.isVisible() else style_bc_bt)
        self.hg_pushButton.setStyleSheet(style_bc_bb if not self.dialog_hoga.isVisible() else style_bc_bt)
        self.ct_pushButton.setStyleSheet(style_bc_bb if not self.dialog_chart.isVisible() else style_bc_bt)
        self.ct_pushButtonnn_02.setStyleSheet(style_bc_bt if not self.dialog_factor.isVisible() else style_bc_bb)
        self.ct_pushButtonnn_05.setStyleSheet(style_bc_bt if not self.dialog_test.isVisible() else style_bc_bb)
        self.bs_pushButton.setStyleSheet(style_bc_bb if not self.dialog_scheduler.isVisible() else style_bc_bt)
        self.tt_pushButton.setStyleSheet(style_bc_bb if not self.s_calendarWidgett.isVisible() and not self.c_calendarWidgett.isVisible() else style_bc_bt)

        style_ = style_bc_bt if self.proc_backtester_bb is not None and self.proc_backtester_bb.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svj_pushButton_01.setStyleSheet(style_)
        self.cvj_pushButton_01.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_bf is not None and self.proc_backtester_bf.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svj_pushButton_02.setStyleSheet(style_)
        self.cvj_pushButton_02.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_ovc is not None and self.proc_backtester_ovc.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svc_pushButton_06.setStyleSheet(style_)
        self.cvc_pushButton_06.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_ov is not None and self.proc_backtester_ov.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svc_pushButton_07.setStyleSheet(style_)
        self.cvc_pushButton_07.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_o is not None and self.proc_backtester_o.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svc_pushButton_08.setStyleSheet(style_)
        self.cvc_pushButton_08.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_ovct is not None and self.proc_backtester_ovct.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svc_pushButton_15.setStyleSheet(style_)
        self.cvc_pushButton_15.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_ovt is not None and self.proc_backtester_ovt.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svc_pushButton_16.setStyleSheet(style_)
        self.cvc_pushButton_16.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_ot is not None and self.proc_backtester_ot.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svc_pushButton_17.setStyleSheet(style_)
        self.cvc_pushButton_17.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_orvc is not None and self.proc_backtester_orvc.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svc_pushButton_18.setStyleSheet(style_)
        self.cvc_pushButton_18.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_orv is not None and self.proc_backtester_orv.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svc_pushButton_19.setStyleSheet(style_)
        self.cvc_pushButton_19.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_or is not None and self.proc_backtester_or.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svc_pushButton_20.setStyleSheet(style_)
        self.cvc_pushButton_20.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_ogvc is not None and self.proc_backtester_ogvc.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.sva_pushButton_01.setStyleSheet(style_)
        self.cva_pushButton_01.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_ogv is not None and self.proc_backtester_ogv.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.sva_pushButton_02.setStyleSheet(style_)
        self.cva_pushButton_02.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_og is not None and self.proc_backtester_og.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.sva_pushButton_03.setStyleSheet(style_)
        self.cva_pushButton_03.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_ocvc is not None and self.proc_backtester_ocvc.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svo_pushButton_05.setStyleSheet(style_)
        self.cvo_pushButton_05.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_ocv is not None and self.proc_backtester_ocv.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svo_pushButton_06.setStyleSheet(style_)
        self.cvo_pushButton_06.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_oc is not None and self.proc_backtester_oc.is_alive() and self.counter % 2 != 0 else style_bc_by
        self.svo_pushButton_07.setStyleSheet(style_)
        self.cvo_pushButton_07.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_bvc is not None and self.proc_backtester_bvc.is_alive() and self.counter % 2 != 0 else style_bc_sl
        self.svc_pushButton_27.setStyleSheet(style_)
        self.cvc_pushButton_27.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_bv is not None and self.proc_backtester_bv.is_alive() and self.counter % 2 != 0 else style_bc_sl
        self.svc_pushButton_28.setStyleSheet(style_)
        self.cvc_pushButton_28.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_b is not None and self.proc_backtester_b.is_alive() and self.counter % 2 != 0 else style_bc_sl
        self.svc_pushButton_29.setStyleSheet(style_)
        self.cvc_pushButton_29.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_bvct is not None and self.proc_backtester_bvct.is_alive() and self.counter % 2 != 0 else style_bc_sl
        self.svc_pushButton_30.setStyleSheet(style_)
        self.cvc_pushButton_30.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_bvt is not None and self.proc_backtester_bvt.is_alive() and self.counter % 2 != 0 else style_bc_sl
        self.svc_pushButton_31.setStyleSheet(style_)
        self.cvc_pushButton_31.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_bt is not None and self.proc_backtester_bt.is_alive() and self.counter % 2 != 0 else style_bc_sl
        self.svc_pushButton_32.setStyleSheet(style_)
        self.cvc_pushButton_32.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_brvc is not None and self.proc_backtester_brvc.is_alive() and self.counter % 2 != 0 else style_bc_sl
        self.svc_pushButton_33.setStyleSheet(style_)
        self.cvc_pushButton_33.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_brv is not None and self.proc_backtester_brv.is_alive() and self.counter % 2 != 0 else style_bc_sl
        self.svc_pushButton_34.setStyleSheet(style_)
        self.cvc_pushButton_34.setStyleSheet(style_)

        style_ = style_bc_bt if self.proc_backtester_br is not None and self.proc_backtester_br.is_alive() and self.counter % 2 != 0 else style_bc_sl
        self.svc_pushButton_35.setStyleSheet(style_)
        self.cvc_pushButton_35.setStyleSheet(style_)

        style_ = style_bc_bb if self.ct_test > 0 and self.counter % 2 != 0 else style_bc_bt
        self.tt_pushButtonnn_03.setStyleSheet(style_)

        if self.ssicon_alert:
            icon = self.icon_stocks if self.counter % 2 == 0 else self.icon_stocks2
            self.main_btn_list[2].setIcon(icon)

        if self.csicon_alert:
            icon = self.icon_coins if self.counter % 2 == 0 else self.icon_coins2
            self.main_btn_list[3].setIcon(icon)

        if self.lgicon_alert:
            icon = self.icon_log if self.counter % 2 == 0 else self.icon_log2
            self.main_btn_list[5].setIcon(icon)
            if self.counter % 5 == 0 and (self.dict_set['주식알림소리'] or self.dict_set['코인알림소리']):
                soundQ.put('오류가 발생하였습니다. 로그탭을 확인하십시오.')

        if not self.image_search or (self.counter % 60 == 0 and (self.image_label1.isVisible() or self.image_label2.isVisible())):
            if not self.image_search: self.image_search = True
            webcQ.put(('풍경사진요청', ''))

    def ImageUpdate(self, data):
        if self.image_label1.isVisible():
            self.image_label1.clear()
            qpix = QPixmap()
            qpix.loadFromData(data[1])
            qpix = qpix.scaled(QSize(335, 105), Qt.IgnoreAspectRatio)
            self.image_label1.setPixmap(qpix)
        if self.image_label2.isVisible():
            self.image_label2.clear()
            qpix = QPixmap()
            qpix.loadFromData(data[2])
            qpix = qpix.scaled(QSize(335, 605), Qt.IgnoreAspectRatio)
            self.image_label2.setPixmap(qpix)

    def UpdateSQsize(self, data):
        self.srqsize, self.stqsize, self.ssqsize = data

    @thread_decorator
    def UpdateCpuper(self):
        self.cpu_per = int(psutil.cpu_percent(interval=1))

    @error_decorator
    def UpdateTexedit(self, data):
        if len(data) == 2:
            if '시스템 명령 오류 알림' in data[1]:
                self.lgicon_alert = True

            time_ = str(now())[:-7] if data[0] in (ui_num['S백테스트'], ui_num['C백테스트'], ui_num['CF백테스트']) else str(now())
            log_  = f'<font color=#FF32FF>{data[1]}</font>' if '오류' in data[1] else data[1]
            text  = f'[{time_}] {log_}' if '</font>' not in log_ else f'<font color=white>[{time_}]</font> {log_}'

            if data[0] == ui_num['백테엔진']:
                self.be_textEditxxxx_01.append(text)
                if data[1] == '백테엔진 준비 완료' and self.auto_mode:
                    if self.dialog_backengine.isVisible():
                        self.dialog_backengine.close()
                    qtest_qwait(2)
                    self.AutoBackSchedule(2)
            elif data[0] == ui_num['S로그텍스트']:
                self.sst_textEditttt_01.append(text)
                self.log1.info(text)
            elif data[0] == ui_num['S단순텍스트']:
                self.src_textEditttt_01.append(text)
                self.log2.info(text)
                if '전략연산 프로세스 틱데이터 저장 중 ... [8]' in text:
                    self.tickdata_save = True
            elif data[0] == ui_num['S오더텍스트']:
                self.log3.info(text)
            elif data[0] == ui_num['C로그텍스트']:
                self.cst_textEditttt_01.append(text)
                self.log4.info(text)
            elif data[0] == ui_num['C단순텍스트']:
                self.crc_textEditttt_01.append(text)
                self.log5.info(text)
            elif data[0] == ui_num['S백테스트']:
                if '배팅금액' in data[1] or 'OUT' in data[1] or '결과' in data[1] or '최적값' in data[1] or '벤치점수' in data[1]:
                    color = color_fg_rt
                elif ('AP' in data[1] and '-' in data[1].split('AP')[1]) or ('수익률' in data[1] and '-' in data[1].split('수익률')[1]):
                    color = color_fg_dk
                else:
                    color = color_fg_bt
                self.ss_textEditttt_09.setTextColor(color)
                self.ss_textEditttt_09.append(text)
                self.log6.info(re.sub('(<([^>]+)>)', '', text))
                if data[1] == '전략 코드 오류로 백테스트를 중지합니다.' and self.back_condition: self.BacktestProcessKill()
                if data[1] in ('백테스트 완료', '백파인더 완료', '벤치테스트 완료', '최적화O 완료', '최적화OV 완료', '최적화OVC 완료',
                               '최적화B 완료', '최적화BV 완료', '최적화BVC 완료', '최적화OT 완료', '최적화OVT 완료', '최적화OVCT 완료',
                               '최적화BT 완료', '최적화BVT 완료', '최적화BVCT 완료', '전진분석OR 완료', '전진분석ORV 완료', '전진분석ORVC 완료',
                               '전진분석BR 완료', '전진분석BRV 완료', '전진분석BRVC 완료', '최적화OG 완료', '최적화OGV 완료', '최적화OGVC 완료',
                               '최적화OC 완료', '최적화OCV 완료', '최적화OCVC 완료'):
                    if data[1] in ('최적화O 완료', '최적화OV 완료', '최적화OVC 완료', '최적화B 완료', '최적화BV 완료', '최적화BVC 완료'):
                        self.sActivated_04()
                    if data[1] in ('최적화OG 완료', '최적화OGV 완료', '최적화OGVC 완료'):
                        self.sActivated_06()
                    if not self.dict_set['그래프띄우지않기'] and data[1] not in ('백파인더 완료', '벤치테스트 완료', '최적화OG 완료', '최적화OGV 완료', '최적화OGVC 완료', '최적화OC 완료', '최적화OCV 완료', '최적화OCVC 완료'):
                        self.svjButtonClicked_08()
                    self.BacktestProcessKill()
                    self.ssicon_alert = False
                    self.main_btn_list[2].setIcon(self.icon_stocks)
                    if self.back_schedul:
                        qtest_qwait(3)
                        self.sdButtonClicked_02()
            elif data[0] in (ui_num['C백테스트'], ui_num['CF백테스트']):
                if '배팅금액' in data[1] or 'OUT' in data[1] or '결과' in data[1] or '최적값' in data[1]:
                    color = color_fg_rt
                elif ('AP' in data[1] and '-' in data[1].split('AP')[1]) or \
                        ('수익률' in data[1] and '-' in data[1].split('수익률')[1].split('KRW')[0]):
                    color = color_fg_dk
                else:
                    color = color_fg_bt
                self.cs_textEditttt_09.setTextColor(color)
                self.cs_textEditttt_09.append(text)
                self.log6.info(re.sub('(<([^>]+)>)', '', text))
                if data[1] == '전략 코드 오류로 백테스트를 중지합니다.' and self.back_condition: self.BacktestProcessKill()
                if data[1] in ('백테스트 완료', '백파인더 완료', '벤치테스트 완료', '최적화O 완료', '최적화OV 완료', '최적화OVC 완료',
                               '최적화B 완료', '최적화BV 완료', '최적화BVC 완료', '최적화OT 완료', '최적화OVT 완료', '최적화OVCT 완료',
                               '최적화BT 완료', '최적화BVT 완료', '최적화BVCT 완료', '전진분석OR 완료', '전진분석ORV 완료', '전진분석ORVC 완료',
                               '전진분석BR 완료', '전진분석BRV 완료', '전진분석BRVC 완료', '최적화OG 완료', '최적화OGV 완료', '최적화OGVC 완료',
                               '최적화OC 완료', '최적화OCV 완료', '최적화OCVC 완료'):
                    if data[1] in ('최적화O 완료', '최적화OV 완료', '최적화OVC 완료', '최적화B 완료', '최적화BV 완료', '최적화BVC 완료'):
                        self.cActivated_04()
                    if data[1] in ('최적화OG 완료', '최적화OGV 완료', '최적화OGVC 완료'):
                        self.cActivated_06()
                    if not self.dict_set['그래프띄우지않기'] and data[1] not in ('백파인더 완료', '벤치테스트 완료', '최적화OG 완료', '최적화OGV 완료', '최적화OGVC 완료', '최적화OC 완료', '최적화OCV 완료', '최적화OCVC 완료'):
                        self.cvjButtonClicked_08()
                    self.BacktestProcessKill()
                    self.csicon_alert = False
                    self.main_btn_list[3].setIcon(self.icon_coins)
                    if self.back_schedul:
                        qtest_qwait(3)
                        self.sdButtonClicked_02()
            elif data[0] == ui_num['기업개요']:
                self.gg_textEdittttt_01.clear()
                self.gg_textEdittttt_01.append(data[1])

            if data[0] == ui_num['S단순텍스트'] and '리시버 종료' in data[1]:
                wdzservQ.put(('manager', '리시버 종료'))
            elif data[0] == ui_num['S로그텍스트'] and '전략연산 종료' in data[1]:
                wdzservQ.put(('manager', '전략연산 종료'))
                if self.tickdata_save and self.dict_set['디비자동관리']:
                    self.AutoDataBase(1)
                else:
                    self.StockShutDownCheck()
            elif data[0] == ui_num['S로그텍스트'] and '트레이더 종료' in data[1]:
                wdzservQ.put(('manager', '트레이더 종료'))
            elif data[0] == ui_num['C단순텍스트'] and '리시버 종료' in data[1]:
                if self.CoinReceiverProcessAlive():
                    self.proc_receiver_coin.kill()
            elif data[0] == ui_num['C로그텍스트'] and '전략연산 종료' in data[1]:
                if self.CoinStrategyProcessAlive():
                    self.proc_strategy_coin.kill()
                self.CoinShutDownCheck()
            elif data[0] == ui_num['C로그텍스트'] and '트레이더 종료' in data[1]:
                if self.CoinTraderProcessAlive():
                    self.proc_trader_coin.kill()
            elif data[0] == ui_num['DB관리']:
                if data[1] == 'DB업데이트완료':
                    self.database_control = False
                else:
                    self.db_textEdittttt_01.append(text)
                if data[1] == '날짜별 DB 생성 완료':
                    self.AutoDataBase(2)
                elif data[1] == '당일 데이터 백테디비로 추가 완료':
                    self.AutoDataBase(3)
            elif data[0] == ui_num['바낸선물단위정보']:
                self.dict_info = data[1]
        elif len(data) == 5:
            self.dict_name = data[1]
            self.dict_code = data[2]
            self.dict_sgbn = data[3]
        elif len(data) == 4:
            if data[1] <= data[2]:
                curr_time = now()
                try:
                    rmained_backtime = timedelta_sec((curr_time - data[3]).total_seconds() / data[1] * (data[2] - data[1])) - curr_time
                except:
                    pass
                else:
                    if self.back_schedul:
                        self.list_progressBarrr[self.back_scount].setFormat('%p%')
                        self.list_progressBarrr[self.back_scount].setValue(data[1])
                        self.list_progressBarrr[self.back_scount].setRange(0, data[2])
                    if data[0] == ui_num['S백테바']:
                        self.ss_progressBar_01.setFormat(f'%p% | 남은 시간 {rmained_backtime}')
                        self.ss_progressBar_01.setValue(data[1])
                        self.ss_progressBar_01.setRange(0, data[2])
                    elif data[0] in (ui_num['C백테바'], ui_num['CF백테바']):
                        self.cs_progressBar_01.setFormat(f'%p% | 남은 시간 {rmained_backtime}')
                        self.cs_progressBar_01.setValue(data[1])
                        self.cs_progressBar_01.setRange(0, data[2])

    def AutoDataBase(self, gubun):
        if gubun == 1:
            self.auto_mode = True
            if self.dict_set['주식알림소리'] or self.dict_set['코인알림소리']:
                soundQ.put('데이터베이스 자동관리를 시작합니다.')
            if not self.dialog_db.isVisible():
                self.dialog_db.show()
            qtest_qwait(2)
            self.dbButtonClicked_08()
        elif gubun == 2:
            if not self.dialog_db.isVisible():
                self.dialog_db.show()
            qtest_qwait(2)
            self.dbButtonClicked_07()
        elif gubun == 3:
            if self.dialog_db.isVisible():
                self.dialog_db.close()
            teleQ.put('데이터베이스 자동관리 완료')
            qtest_qwait(2)
            self.auto_mode = False
            self.StockShutDownCheck()

    def AutoBackSchedule(self, gubun):
        if gubun == 1:
            self.auto_mode = True
            if self.dict_set['주식알림소리'] or self.dict_set['코인알림소리']:
                soundQ.put('예약된 백테스트 스케쥴러를 시작합니다.')
            if not self.dialog_backengine.isVisible():
                self.BackengineShow(self.dict_set['백테스케쥴구분'])
            qtest_qwait(2)
            self.backtest_engine = False
            self.BacktestEngineVarsReset()
            qtest_qwait(2)
            self.StartBacktestEngine(self.dict_set['백테스케쥴구분'])
        elif gubun == 2:
            if not self.dialog_scheduler.isVisible():
                self.dialog_scheduler.show()
            qtest_qwait(2)
            self.sdButtonClicked_04()
            qtest_qwait(2)
            self.sd_pushButtonnn_01.setText(self.dict_set['백테스케쥴구분'])
            self.sd_dcomboBoxxxx_01.setCurrentText(self.dict_set['백테스케쥴명'])
            qtest_qwait(2)
            self.sdButtonClicked_02()
        elif gubun == 3:
            if self.dialog_scheduler.isVisible():
                self.dialog_scheduler.close()
            teleQ.put('백테스트 스케쥴러 완료')
            self.auto_mode = False

    def StockShutDownCheck(self):
        if not self.dict_set['백테스케쥴실행'] or now().weekday() != self.dict_set['백테스케쥴요일']:
            if self.dict_set['프로그램종료']:
                QTimer.singleShot(180 * 1000, self.ProcessKill)
            if self.dict_set['리시버공유'] < 2:
                if self.dict_set['주식장초컴퓨터종료'] or self.dict_set['주식장중컴퓨터종료'] or (90000 < int_hms() < 90500 and self.dict_set['휴무컴퓨터종료']):
                    os.system('shutdown /s /t 300')
        elif self.dict_set['주식알림소리']:
            soundQ.put('오늘은 백테 스케쥴러의 실행이 예약되어 있어 프로그램을 종료하지 않습니다.')

    def CoinShutDownCheck(self):
        if not self.dict_set['백테스케쥴실행'] or now().weekday() != self.dict_set['백테스케쥴요일']:
            if self.dict_set['프로그램종료']:
                QTimer.singleShot(180 * 1000, self.ProcessKill)
            if self.dict_set['리시버공유'] < 2:
                if self.dict_set['코인장초컴퓨터종료'] or self.dict_set['코인장중컴퓨터종료']:
                    os.system('shutdown /s /t 300')
        elif self.dict_set['코인알림소리']:
            soundQ.put('오늘은 백테 스케쥴러의 실행이 예약되어 있어 프로그램을 종료하지 않습니다.')

    @error_decorator
    def UpdateTablewidget(self, data):
        if len(data) == 2:
            gubun, df = data
        elif len(data) == 3:
            gubun, usdtokrw, df = data
            self.dialog_kimp.setWindowTitle(f'STOM KIMP - 환율 {usdtokrw:,}원/달러')
        else:
            gubun, df, ymshms, dummy = data
            if self.ctpg_tik_xticks is not None:
                self.UpdateHogainfoForChart(gubun, ymshms)

        tableWidget = None
        if gubun == ui_num['S실현손익']:
            tableWidget = self.stt_tableWidgettt
        elif gubun == ui_num['S거래목록']:
            tableWidget = self.std_tableWidgettt
        elif gubun == ui_num['S잔고평가']:
            tableWidget = self.stj_tableWidgettt
        elif gubun == ui_num['S잔고목록']:
            tableWidget = self.sjg_tableWidgettt
        elif gubun == ui_num['S체결목록']:
            tableWidget = self.scj_tableWidgettt
        elif gubun == ui_num['S당일합계']:
            tableWidget = self.sdt_tableWidgettt
        elif gubun == ui_num['S당일상세']:
            tableWidget = self.sds_tableWidgettt
        elif gubun == ui_num['S누적합계']:
            tableWidget = self.snt_tableWidgettt
        elif gubun == ui_num['S누적상세']:
            tableWidget = self.sns_tableWidgettt
        elif gubun == ui_num['S관심종목']:
            tableWidget = self.sgj_tableWidgettt
        elif gubun == ui_num['C실현손익']:
            tableWidget = self.ctt_tableWidgettt
        elif gubun == ui_num['C거래목록']:
            tableWidget = self.ctd_tableWidgettt
        elif gubun == ui_num['C잔고평가']:
            tableWidget = self.ctj_tableWidgettt
        elif gubun == ui_num['C잔고목록']:
            tableWidget = self.cjg_tableWidgettt
        elif gubun == ui_num['C체결목록']:
            tableWidget = self.ccj_tableWidgettt
        elif gubun == ui_num['C당일합계']:
            tableWidget = self.cdt_tableWidgettt
        elif gubun == ui_num['C당일상세']:
            tableWidget = self.cds_tableWidgettt
            if tableWidget.columnCount() != len(df.columns):
                tableWidget.setColumnCount(len(df.columns))
                tableWidget.setHorizontalHeaderLabels(df.columns)
                if len(df.columns) == 7:
                    tableWidget.setColumnWidth(0, 90)
                    tableWidget.setColumnWidth(1, 101)
                    tableWidget.setColumnWidth(2, 95)
                    tableWidget.setColumnWidth(3, 95)
                    tableWidget.setColumnWidth(4, 95)
                    tableWidget.setColumnWidth(5, 95)
                    tableWidget.setColumnWidth(6, 95)
                else:
                    tableWidget.setColumnWidth(0, 90)
                    tableWidget.setColumnWidth(1, 96)
                    tableWidget.setColumnWidth(2, 80)
                    tableWidget.setColumnWidth(3, 80)
                    tableWidget.setColumnWidth(4, 80)
                    tableWidget.setColumnWidth(5, 80)
                    tableWidget.setColumnWidth(6, 80)
                    tableWidget.setColumnWidth(7, 80)
        elif gubun == ui_num['C누적합계']:
            tableWidget = self.cnt_tableWidgettt
        elif gubun == ui_num['C누적상세']:
            tableWidget = self.cns_tableWidgettt
        elif gubun == ui_num['C관심종목']:
            tableWidget = self.cgj_tableWidgettt
        elif gubun == ui_num['S상세기록']:
            tableWidget = self.ss_tableWidget_01
            tableWidget.setHorizontalHeaderLabels(df.columns)
        elif gubun == ui_num['C상세기록']:
            tableWidget = self.cs_tableWidget_01
            tableWidget.setHorizontalHeaderLabels(df.columns)
        elif gubun in (ui_num['C호가종목'], ui_num['S호가종목']):
            tableWidget = self.hj_tableWidgett_01
        elif gubun in (ui_num['C호가체결'], ui_num['S호가체결']):
            if not self.dialog_hoga.isVisible():
                wdzservQ.put(('receiver', ('호가종목코드', '000000')))
                if self.CoinReceiverProcessAlive():  creceivQ.put('000000')
                return
            tableWidget = self.hc_tableWidgett_01
        elif gubun in (ui_num['C호가체결2'], ui_num['S호가체결2']):
            tableWidget = self.hc_tableWidgett_02
        elif gubun in (ui_num['C호가잔량'], ui_num['S호가잔량']):
            tableWidget = self.hg_tableWidgett_01
        elif gubun == ui_num['기업공시']:
            tableWidget = self.gs_tableWidgett_01
        elif gubun == ui_num['기업뉴스']:
            tableWidget = self.ns_tableWidgett_01
        elif gubun == ui_num['재무년도']:
            tableWidget = self.jm_tableWidgett_01
            tableWidget.setHorizontalHeaderLabels(df.columns)
        elif gubun == ui_num['재무분기']:
            tableWidget = self.jm_tableWidgett_02
            tableWidget.setHorizontalHeaderLabels(df.columns)
        elif gubun == ui_num['스톰라이브1']:
            tableWidget = self.slsd_tableWidgett
        elif gubun == ui_num['스톰라이브2']:
            tableWidget = self.slsn_tableWidgett
        elif gubun == ui_num['스톰라이브3']:
            tableWidget = self.slst_tableWidgett
        elif gubun == ui_num['스톰라이브4']:
            tableWidget = self.slcd_tableWidgett
        elif gubun == ui_num['스톰라이브5']:
            tableWidget = self.slcn_tableWidgett
        elif gubun == ui_num['스톰라이브6']:
            tableWidget = self.slct_tableWidgett
        elif gubun == ui_num['스톰라이브7']:
            tableWidget = self.slbt_tableWidgett
        elif gubun == ui_num['스톰라이브8']:
            tableWidget = self.slbd_tableWidgett
        elif gubun == ui_num['김프']:
            if not self.dialog_kimp.isVisible():
                return
            tableWidget = self.kp_tableWidget_01
        if tableWidget is None:
            return

        len_df = len(df)
        if len_df == 0:
            tableWidget.clearContents()
            return

        if gubun in (ui_num['S상세기록'], ui_num['C상세기록'], ui_num['S관심종목'], ui_num['C관심종목'], ui_num['S당일상세'],
                     ui_num['김프'], ui_num['S누적상세'], ui_num['C당일상세'], ui_num['C누적상세'], ui_num['스톰라이브1'],
                     ui_num['스톰라이브3'], ui_num['스톰라이브4'], ui_num['스톰라이브6'], ui_num['스톰라이브7']):
            tableWidget.setSortingEnabled(False)

        tableWidget.setRowCount(len_df)
        arry = df.values
        for i, index in enumerate(df.index):
            for j, column in enumerate(df.columns):
                if column in ('체결시간', '매수시간', '매도시간'):
                    cgtime = str(arry[i, j])
                    if column == '체결시간': cgtime = f'{cgtime[8:10]}:{cgtime[10:12]}:{cgtime[12:14]}'
                    item = QTableWidgetItem(cgtime)
                elif column in ('거래일자', '일자', '일자 및 시간'):
                    day = arry[i, j]
                    if '.' not in day:
                        day = day[:4] + '.' + day[4:6] + '.' + day[6:]
                    item = QTableWidgetItem(day)
                elif gubun in (ui_num['C체결목록'], ui_num['C잔고목록'], ui_num['C잔고평가'], ui_num['C거래목록'], ui_num['C실현손익']) and \
                        column in ('매입금액', '평가금액', '평가손익', '매수금액', '매도금액', '수익금', '총매수금액', '총매도금액',
                                   '총수익금액', '총손실금액', '수익금합계', '총평가손익', '총매입금액', '총평가금액'):
                    item = QTableWidgetItem(change_format(arry[i, j], dotdown4=True))
                elif column in ('종목명', '포지션', '주문번호', '주문구분', '공시', '정보제공', '언론사', '제목', '링크', '구분', 'period', 'time', '추가매수시간') or \
                        gubun in (ui_num['재무년도'], ui_num['재무분기']) or (self.database_chart and column == '체결수량'):
                    try:
                        item = QTableWidgetItem(str(arry[i, j]))
                    except:
                        continue
                elif '량' in column and gubun in (ui_num['C잔고목록'], ui_num['C체결목록'], ui_num['C거래목록'], ui_num['C호가체결'], ui_num['C호가잔량']):
                    item = QTableWidgetItem(change_format(arry[i, j], dotdown8=True))
                elif (gubun == ui_num['C잔고목록'] and column in ('매입가', '현재가')) or \
                        (gubun == ui_num['C체결목록'] and column in ('체결가', '주문가격')) or \
                        (gubun == ui_num['C호가종목'] and column in ('현재가', '시가', '고가', '저가')) or \
                        (gubun == ui_num['C호가잔량'] and column == '호가'):
                    item = QTableWidgetItem(change_format(arry[i, j], dotdown8=True))
                elif gubun in (ui_num['S관심종목'], ui_num['C관심종목'], ui_num['S상세기록'], ui_num['C상세기록'],
                               ui_num['S당일상세'], ui_num['S누적상세'], ui_num['C당일상세'], ui_num['C누적상세'],
                               ui_num['스톰라이브1'], ui_num['스톰라이브3'], ui_num['스톰라이브4'], ui_num['스톰라이브6'],
                               ui_num['스톰라이브7'], ui_num['김프']):
                    value = str(arry[i, j])
                    if column in ('수익률', '누적수익률', 'per', 'hlml_per', 'ch', 'ch_avg', 'ch_high', '대비(원)',
                                  '대비율(%)', 'aht', 'wr', 'asp', 'tsp', 'mdd', 'cagr'):
                        item = NumericItem(change_format(value))
                    elif (gubun == ui_num['C상세기록'] and column in ('매수가', '매도가')) or column == '바이낸스(달러)':
                        item = NumericItem(change_format(value, dotdown8=True))
                    elif column == '업비트(원)':
                        item = NumericItem(change_format(value, dotdown4=True))
                    elif column == '매도조건':
                        item = QTableWidgetItem(value)
                    else:
                        item = NumericItem(change_format(value, dotdowndel=True))
                    if column != '매도조건':
                        value = float(value)
                        item.setData(Qt.UserRole, value)
                elif column not in ('수익률', '누적수익률', '등락율', '체결강도'):
                    item = QTableWidgetItem(change_format(arry[i, j], dotdowndel=True))
                else:
                    item = QTableWidgetItem(change_format(arry[i, j]))

                if column in ('종목명', '공시', '제목', '링크', '매도조건'):
                    item.setTextAlignment(int(Qt.AlignVCenter | Qt.AlignLeft))
                elif column in ('포지션', '거래횟수', '추정예탁자산', '추정예수금', '보유종목수', '정보제공', '언론사', '주문구분',
                                '매수시간', '매도시간', '체결시간', '거래일자', '기간', '일자', '일자 및 시간', '구분', 'period', 'time'):
                    item.setTextAlignment(int(Qt.AlignVCenter | Qt.AlignCenter))
                else:
                    item.setTextAlignment(int(Qt.AlignVCenter | Qt.AlignRight))

                if gubun in (ui_num['C호가체결'], ui_num['S호가체결']) and not self.database_chart:
                    if column == '체결수량':
                        if i == 0:    item.setIcon(self.icon_totalb)
                        elif i == 11: item.setIcon(self.icon_totals)
                    elif column == '체결강도':
                        if i == 0:    item.setIcon(self.icon_up)
                        elif i == 11: item.setIcon(self.icon_down)
                elif gubun in (ui_num['C호가잔량'], ui_num['S호가잔량']):
                    if column == '잔량':
                        if i == 0:    item.setIcon(self.icon_totalb)
                        elif i == 11: item.setIcon(self.icon_totals)
                    elif column == '호가':
                        if i == 0:    item.setIcon(self.icon_up)
                        elif i == 11: item.setIcon(self.icon_down)
                        else:
                            if self.hj_tableWidgett_01.item(0, 0) is not None:
                                func = comma2int if gubun == ui_num['S호가잔량'] else comma2float
                                o    = func(self.hj_tableWidgett_01.item(0, columns_hj.index('시가')).text())
                                h    = func(self.hj_tableWidgett_01.item(0, columns_hj.index('고가')).text())
                                low  = func(self.hj_tableWidgett_01.item(0, columns_hj.index('저가')).text())
                                uvi  = func(self.hj_tableWidgett_01.item(0, columns_hj.index('UVI')).text())
                                if o != 0:
                                    hg = arry[i, j]
                                    if hg == o:     item.setIcon(self.icon_open)
                                    elif hg == h:   item.setIcon(self.icon_high)
                                    elif hg == low: item.setIcon(self.icon_low)
                                    elif hg == uvi: item.setIcon(self.icon_vi)

                if '수익금' in df.columns and gubun not in (ui_num['S상세기록'], ui_num['C상세기록']):
                    color = color_fg_bt if arry[i, list(df.columns).index('수익금')] >= 0 else color_fg_dk
                    item.setForeground(color)
                elif '누적수익금' in df.columns and gubun not in (ui_num['S상세기록'], ui_num['C상세기록']):
                    color = color_fg_bt if arry[i, list(df.columns).index('누적수익금')] >= 0 else color_fg_dk
                    item.setForeground(color)
                elif '수익금합계' in df.columns and gubun not in (ui_num['S상세기록'], ui_num['C상세기록']):
                    color = color_fg_bt if arry[i, list(df.columns).index('수익금합계')] >= 0 else color_fg_dk
                    item.setForeground(color)
                elif '평가손익' in df.columns and gubun not in (ui_num['S상세기록'], ui_num['C상세기록']):
                    color = color_fg_bt if arry[i, list(df.columns).index('평가손익')] >= 0 else color_fg_dk
                    item.setForeground(color)
                elif '총평가손익' in df.columns and gubun not in (ui_num['S상세기록'], ui_num['C상세기록']):
                    color = color_fg_bt if arry[i, list(df.columns).index('총평가손익')] >= 0 else color_fg_dk
                    item.setForeground(color)
                elif gubun in (ui_num['S체결목록'], ui_num['C체결목록']):
                    order_gubun = arry[i, 1]
                    if order_gubun == '매수':   item.setForeground(color_fg_bt)
                    elif order_gubun == '매도': item.setForeground(color_fg_dk)
                    elif '취소' in order_gubun: item.setForeground(color_fg_bc)
                elif gubun in (ui_num['C호가체결'], ui_num['S호가체결']) and not self.database_chart:
                    if column == '체결수량':
                        if i in (0, 11):
                            color = color_fg_bt if arry[i, j] > arry[11 if i == 0 else 0, 0] else color_fg_dk
                            item.setForeground(color)
                        else:
                            func = comma2int if gubun == ui_num['S호가체결'] else comma2float
                            c    = func(self.hg_tableWidgett_01.item(5, columns_hg.index('호가')).text())
                            if arry[i, j] > 0:
                                item.setForeground(color_fg_bt)
                                if arry[i, j] * c > 90000000:  item.setBackground(color_bf_bt)
                            else:
                                item.setForeground(color_fg_dk)
                                if arry[i, j] * c < -90000000: item.setBackground(color_bf_dk)
                    elif column == '체결강도':
                        color = color_fg_bt if arry[i, j] >= 100 else color_fg_dk
                        item.setForeground(color)
                elif gubun in (ui_num['C호가잔량'], ui_num['S호가잔량']):
                    if column == '잔량':
                        if i in (0, 11):
                            color = color_fg_bt if arry[i, j] > arry[11 if i == 0 else 0, 0] else color_fg_dk
                            item.setForeground(color)
                        elif i < 11:
                            item.setForeground(color_fg_bt)
                        else:
                            item.setForeground(color_fg_dk)
                    elif column == '호가':
                        if column == '호가' and arry[i, j] != 0:
                            if self.hj_tableWidgett_01.item(0, 0) is not None:
                                func = comma2int if gubun == ui_num['S호가잔량'] else comma2float
                                c    = func(self.hj_tableWidgett_01.item(0, columns_hj.index('현재가')).text())
                                if i not in (0, 11) and arry[i, j] == c:
                                    item.setBackground(color_bf_bt)
                elif gubun in (ui_num['기업공시'], ui_num['기업뉴스']):
                    text = arry[i, 2]
                    if '단기과열' in text or '투자주의' in text or '투자경고' in text or '투자위험' in text or \
                            '거래정지' in text or '환기종목' in text or '불성실공시' in text or '관리종목' in text or \
                            '정리매매' in text or '유상증자' in text or '무상증자' in text:
                        item.setForeground(color_fg_bt)
                    else:
                        item.setForeground(color_fg_dk)
                elif gubun in (ui_num['재무년도'],  ui_num['재무분기']):
                    color = color_fg_bt if '-' not in arry[i, j] else color_fg_dk
                    item.setForeground(color)
                tableWidget.setItem(i, j, item)

        if len_df < 13 and gubun in (ui_num['S거래목록'], ui_num['S잔고목록'], ui_num['C거래목록'], ui_num['C잔고목록']):
            tableWidget.setRowCount(13)
        elif len_df < 15 and gubun in (ui_num['S체결목록'], ui_num['C체결목록'], ui_num['S관심종목'], ui_num['C관심종목']):
            tableWidget.setRowCount(15)
        elif len_df < 19 and gubun in (ui_num['S당일상세'], ui_num['C당일상세']):
            tableWidget.setRowCount(19)
        elif len_df < 28 and gubun in (ui_num['S누적상세'], ui_num['C누적상세']):
            tableWidget.setRowCount(28)
        elif len_df < 20 and gubun == ui_num['기업공시']:
            tableWidget.setRowCount(20)
        elif len_df < 10 and gubun == ui_num['기업뉴스']:
            tableWidget.setRowCount(10)
        elif len_df < 32 and gubun in (ui_num['S상세기록'], ui_num['C상세기록']):
            tableWidget.setRowCount(32)
        elif len_df < 30 and gubun in (ui_num['스톰라이브1'], ui_num['스톰라이브4']):
            tableWidget.setRowCount(30)
        elif len_df < 28 and gubun in (ui_num['스톰라이브3'], ui_num['스톰라이브6']):
            tableWidget.setRowCount(28)
        elif len_df < 26 and gubun == ui_num['스톰라이브7']:
            tableWidget.setRowCount(26)
        elif len_df < 50 and gubun == ui_num['김프']:
            tableWidget.setRowCount(50)
        elif len_df < 12 and gubun in (ui_num['C호가체결2'], ui_num['S호가체결2']):
            tableWidget.setRowCount(12)

        if gubun in (ui_num['S상세기록'], ui_num['C상세기록'], ui_num['S관심종목'], ui_num['C관심종목'], ui_num['S당일상세'],
                     ui_num['김프'], ui_num['S누적상세'], ui_num['C당일상세'], ui_num['C누적상세'], ui_num['스톰라이브1'],
                     ui_num['스톰라이브3'], ui_num['스톰라이브4'], ui_num['스톰라이브6'], ui_num['스톰라이브7']):
            tableWidget.setSortingEnabled(True)

    def UpdateHogainfoForChart(self, gubun, ymdhms):
        def setInfiniteLine():
            vhline = pg.InfiniteLine()
            vhline.setPen(pg.mkPen(color_ct_hg, width=1))
            return vhline

        if self.ctpg_tik_hline is None:
            vLine1  = setInfiniteLine()
            vLine2  = setInfiniteLine()
            vLine3  = setInfiniteLine()
            vLine4  = setInfiniteLine()
            vLine5  = setInfiniteLine()
            vLine6  = setInfiniteLine()
            vLine7  = setInfiniteLine()
            vLine8  = setInfiniteLine()
            vLine9  = setInfiniteLine()
            vLine10 = setInfiniteLine()
            vLine11 = setInfiniteLine()
            vLine12 = setInfiniteLine()
            vLine13 = setInfiniteLine()
            vLine14 = setInfiniteLine()
            vLine15 = setInfiniteLine()
            vLine16 = setInfiniteLine()

            if self.ct_pushButtonnn_04.text() == 'CHART 8':
                self.ctpg_tik_hline = [vLine1, vLine2, vLine3, vLine4, vLine5, vLine6, vLine7, vLine8]
            elif self.ct_pushButtonnn_04.text() == 'CHART 12':
                self.ctpg_tik_hline = [vLine1, vLine2, vLine3, vLine4, vLine5, vLine6, vLine7, vLine8, vLine9, vLine10, vLine11, vLine12]
            else:
                self.ctpg_tik_hline = [vLine1, vLine2, vLine3, vLine4, vLine5, vLine6, vLine7, vLine8, vLine9, vLine10, vLine11, vLine12, vLine13, vLine14, vLine15, vLine16]

            self.ctpg[0].addItem(vLine1)
            self.ctpg[1].addItem(vLine2)
            self.ctpg[2].addItem(vLine3)
            self.ctpg[3].addItem(vLine4)
            self.ctpg[4].addItem(vLine5)
            self.ctpg[5].addItem(vLine6)
            self.ctpg[6].addItem(vLine7)
            self.ctpg[7].addItem(vLine8)
            if self.ct_pushButtonnn_04.text() == 'CHART 12':
                self.ctpg[8].addItem(vLine9)
                self.ctpg[9].addItem(vLine10)
                self.ctpg[10].addItem(vLine11)
                self.ctpg[11].addItem(vLine12)
            elif self.ct_pushButtonnn_04.text() == 'CHART 16':
                self.ctpg[8].addItem(vLine9)
                self.ctpg[9].addItem(vLine10)
                self.ctpg[10].addItem(vLine11)
                self.ctpg[11].addItem(vLine12)
                self.ctpg[12].addItem(vLine13)
                self.ctpg[13].addItem(vLine14)
                self.ctpg[14].addItem(vLine15)
                self.ctpg[15].addItem(vLine16)

        x = strp_time('%Y%m%d%H%M%S', ymdhms).timestamp()
        for vline in self.ctpg_tik_hline:
            vline.setPos(x)

        ymd = ymdhms[:8]
        hms = ymdhms[8:]
        self.hg_labellllllll_01.setText(f'{ymd[:4]}-{ymd[4:6]}-{ymd[6:]} {hms[:2]}:{hms[2:4]}:{hms[4:]}')

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
        거래대금순위, 매수가, 매도가
            61       62     63
        """

        xpoint = self.ctpg_tik_xticks.index(x)
        info = ['이평60', '이평300', '이평600', '이평1200', '체결강도', '체결강도평균', '최고체결강도', '최저체결강도', '초당거래대금', '초당거래대금평균', '초당매수수량', '초당매도수량']
        if gubun == ui_num['S호가종목']:
            data = [
                self.ctpg_tik_arry[xpoint, 44], self.ctpg_tik_arry[xpoint, 45], self.ctpg_tik_arry[xpoint, 46],
                self.ctpg_tik_arry[xpoint, 47], self.ctpg_tik_arry[xpoint, 7], self.ctpg_tik_arry[xpoint, 50],
                self.ctpg_tik_arry[xpoint, 51], self.ctpg_tik_arry[xpoint, 52], self.ctpg_tik_arry[xpoint, 19],
                self.ctpg_tik_arry[xpoint, 57], self.ctpg_tik_arry[xpoint, 14], self.ctpg_tik_arry[xpoint, 15]
            ]
            df1  = pd.DataFrame({'체결수량': info, '체결강도': data})
            info = ['고저평균대비등락율', '매도수5호가잔량합', '당일거래대금', '누적초당매수수량', '누적초당매도수량', '등락율각도', '당일거래대금각도', '전일비각도', '거래대금증감', '전일비', '회전율', '전일동시간비']
            data = [
                self.ctpg_tik_arry[xpoint, 20], self.ctpg_tik_arry[xpoint, 43], self.ctpg_tik_arry[xpoint, 6],
                self.ctpg_tik_arry[xpoint, 55], self.ctpg_tik_arry[xpoint, 56], self.ctpg_tik_arry[xpoint, 58],
                self.ctpg_tik_arry[xpoint, 59], self.ctpg_tik_arry[xpoint, 60], self.ctpg_tik_arry[xpoint, 8],
                self.ctpg_tik_arry[xpoint, 9], self.ctpg_tik_arry[xpoint, 10], self.ctpg_tik_arry[xpoint, 11]
            ]
            df2  = pd.DataFrame({'체결수량': info, '체결강도': data})
            coin = False
            windowQ.put((ui_num['S호가체결'], df1))
            windowQ.put((ui_num['S호가체결2'], df2))
        else:
            data = [
                self.ctpg_tik_arry[xpoint, 35], self.ctpg_tik_arry[xpoint, 36], self.ctpg_tik_arry[xpoint, 37],
                self.ctpg_tik_arry[xpoint, 38], self.ctpg_tik_arry[xpoint, 7], self.ctpg_tik_arry[xpoint, 41],
                self.ctpg_tik_arry[xpoint, 42], self.ctpg_tik_arry[xpoint, 43], self.ctpg_tik_arry[xpoint, 10],
                self.ctpg_tik_arry[xpoint, 48], self.ctpg_tik_arry[xpoint, 8], self.ctpg_tik_arry[xpoint, 9]
            ]
            df1  = pd.DataFrame({'체결수량': info, '체결강도': data})
            info = ['고저평균대비등락율', '매도수5호가잔량합', '당일거래대금', '누적초당매수수량', '누적초당매도수량', '등락율각도', '당일거래대금각도']
            data = [
                self.ctpg_tik_arry[xpoint, 11], self.ctpg_tik_arry[xpoint, 34], self.ctpg_tik_arry[xpoint, 6],
                self.ctpg_tik_arry[xpoint, 46], self.ctpg_tik_arry[xpoint, 47], self.ctpg_tik_arry[xpoint, 49],
                self.ctpg_tik_arry[xpoint, 50]
            ]
            df2  = pd.DataFrame({'체결수량': info, '체결강도': data})
            coin = True
            windowQ.put((ui_num['C호가체결'], df1))
            windowQ.put((ui_num['C호가체결2'], df2))

        for i in range(len(self.ctpg_tik_legend)):
            self.ctpg_tik_legend[i].setText(self.GetLabelText(coin, self.ctpg_tik_arry, xpoint, self.ctpg_tik_factors[i], f'{hms[:2]}:{hms[2:4]}:{hms[4:]}'))
            self.ctpg_tik_labels[i].setText('')

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
        거래대금순위, 매수가, 매도가, 매수가2, 매도가2
            51       52     53     54      55
        """

    @error_decorator
    def DrawChart(self, data):
        def cindex(number):
            return dict_stock[number] if not coin else dict_coin[number]

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
        거래대금순위, 매수가, 매도가
            61       62     63
        """
        dict_stock = {
            1: 44, 2: 45, 3: 46, 4: 47, 5: 1, 6: 50, 7: 51, 8: 52, 9: 7, 10: 19, 11: 57, 12: 14, 13: 15, 14: 5, 15: 20,
            16: 22, 17: 21, 18: 38, 19: 37, 20: 43, 21: 6, 22: 55, 23: 56, 24: 58, 25: 59, 26: 60, 27: 8, 28: 9, 29: 10,
            30: 11, 40: 61, 41: 62, 42: 63
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
        거래대금순위, 매수가, 매도가, 매수가2, 매도가2
            51       52     53     54      55
        """
        dict_coin = {
            1: 35, 2: 36, 3: 37, 4: 38, 5: 1, 6: 41, 7: 42, 8: 43, 9: 7, 10: 10, 11: 48, 12: 8, 13: 9, 14: 5, 15: 11,
            16: 13, 17: 12, 18: 29, 19: 28, 20: 34, 21: 6, 22: 46, 23: 47, 24: 49, 25: 50, 40: 51, 41: 52, 42: 53,
            43: 54, 44: 55
        }

        self.ChartClear()
        if not self.dialog_chart.isVisible():
            return

        coin, self.ctpg_tik_xticks, self.ctpg_tik_arry, self.buy_index, self.sell_index = data[1:]
        if coin == '차트오류':
            QMessageBox.critical(self.dialog_chart, '오류 알림', '해당 날짜의 데이터가 존재하지 않습니다.\n')
            return

        xmin, xmax = self.ctpg_tik_xticks[0], self.ctpg_tik_xticks[-1]
        if self.ct_pushButtonnn_04.text() == 'CHART 8':
            chart_count = 8
        elif self.ct_pushButtonnn_04.text() == 'CHART 12':
            chart_count = 12
        else:
            chart_count = 16

        code = self.ct_lineEdittttt_04.text()
        date = strf_time('%Y%m%d', from_timestamp(xmin))
        if not coin: self.KiwoomHTSChart(code, date)

        self.ctpg_tik_factors = []
        if self.ct_checkBoxxxxx_01.isChecked():     self.ctpg_tik_factors.append('현재가')
        if self.ct_checkBoxxxxx_02.isChecked():     self.ctpg_tik_factors.append('체결강도')
        if self.ct_checkBoxxxxx_03.isChecked():     self.ctpg_tik_factors.append('초당거래대금')
        if self.ct_checkBoxxxxx_04.isChecked():     self.ctpg_tik_factors.append('초당체결수량')
        if self.ct_checkBoxxxxx_05.isChecked():     self.ctpg_tik_factors.append('등락율')
        if self.ct_checkBoxxxxx_06.isChecked():     self.ctpg_tik_factors.append('고저평균대비등락율')
        if self.ct_checkBoxxxxx_07.isChecked():     self.ctpg_tik_factors.append('호가총잔량')
        if self.ct_checkBoxxxxx_08.isChecked():     self.ctpg_tik_factors.append('1호가잔량')
        if self.ct_checkBoxxxxx_09.isChecked():     self.ctpg_tik_factors.append('5호가잔량합')
        if self.ct_checkBoxxxxx_10.isChecked():     self.ctpg_tik_factors.append('당일거래대금')
        if self.ct_checkBoxxxxx_11.isChecked():     self.ctpg_tik_factors.append('누적초당매도수수량')
        if self.ct_checkBoxxxxx_12.isChecked():     self.ctpg_tik_factors.append('등락율각도')
        if self.ct_checkBoxxxxx_13.isChecked():     self.ctpg_tik_factors.append('당일거래대금각도')
        if not coin:
            if self.ct_checkBoxxxxx_14.isChecked(): self.ctpg_tik_factors.append('거래대금증감')
            if self.ct_checkBoxxxxx_15.isChecked(): self.ctpg_tik_factors.append('전일비')
            if self.ct_checkBoxxxxx_16.isChecked(): self.ctpg_tik_factors.append('회전율')
            if self.ct_checkBoxxxxx_17.isChecked(): self.ctpg_tik_factors.append('전일동시간비')
            if self.ct_checkBoxxxxx_18.isChecked(): self.ctpg_tik_factors.append('전일비각도')

        for j in range(len(self.ctpg_tik_arry[0, :])):
            if j in (cindex(1), cindex(2), cindex(3), cindex(4), cindex(6), cindex(7), cindex(8), cindex(25)):
                self.ctpg_tik_data[j] = [x for x in self.ctpg_tik_arry[:, j] if x != 0]
            else:
                self.ctpg_tik_data[j] = self.ctpg_tik_arry[:, j]

        hms  = from_timestamp(xmax).strftime('%H:%M:%S')
        tlen = len(self.ctpg_tik_xticks)
        len1 = len(self.ctpg_tik_data[cindex(1)])
        len2 = len(self.ctpg_tik_data[cindex(2)])
        len3 = len(self.ctpg_tik_data[cindex(3)])
        len4 = len(self.ctpg_tik_data[cindex(4)])
        len5 = len(self.ctpg_tik_data[cindex(6)])
        len6 = len(self.ctpg_tik_data[cindex(7)])
        len7 = len(self.ctpg_tik_data[cindex(8)])
        len8 = len(self.ctpg_tik_data[cindex(25)])
        chuse_exist = True if len(self.ctpg_tik_arry[self.ctpg_tik_arry[:, cindex(40)] > 0]) > 0 else False

        for i, factor in enumerate(self.ctpg_tik_factors):
            self.ctpg[i].clear()
            ymin, ymax = 0, 0
            if factor == '현재가':
                list_ = self.ctpg_tik_data[cindex(1)] + self.ctpg_tik_data[cindex(2)] + self.ctpg_tik_data[cindex(3)] + self.ctpg_tik_data[cindex(4)] + list(self.ctpg_tik_data[cindex(5)])
                ymax, ymin = max(list_), min(list_)
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len1:], y=self.ctpg_tik_data[cindex(1)], pen=(140, 140, 145))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len2:], y=self.ctpg_tik_data[cindex(2)], pen=(120, 120, 125))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len3:], y=self.ctpg_tik_data[cindex(3)], pen=(100, 100, 105))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len4:], y=self.ctpg_tik_data[cindex(4)], pen=(80, 80, 85))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(5)], pen=(200, 50, 50))
                for j, price in enumerate(self.ctpg_tik_arry[:, cindex(41)]):
                    if price > 0:
                        arrow = pg.ArrowItem(angle=-180, tipAngle=60, headLen=10, pen='w', brush='r')
                        arrow.setPos(self.ctpg_tik_xticks[j], price)
                        self.ctpg[i].addItem(arrow)
                for j, price in enumerate(self.ctpg_tik_arry[:, cindex(42)]):
                    if price > 0:
                        arrow = pg.ArrowItem(angle=0, tipAngle=60, headLen=10, pen='w', brush='b')
                        arrow.setPos(self.ctpg_tik_xticks[j], price)
                        self.ctpg[i].addItem(arrow)
                if 'USDT' in code:
                    for j, price in enumerate(self.ctpg_tik_arry[:, cindex(43)]):
                        if price > 0:
                            arrow = pg.ArrowItem(angle=-180, tipAngle=60, headLen=10, pen='w', brush='m')
                            arrow.setPos(self.ctpg_tik_xticks[j], price)
                            self.ctpg[i].addItem(arrow)
                    for j, price in enumerate(self.ctpg_tik_arry[:, cindex(44)]):
                        if price > 0:
                            arrow = pg.ArrowItem(angle=0, tipAngle=60, headLen=10, pen='w', brush='b')
                            arrow.setPos(self.ctpg_tik_xticks[j], price)
                            self.ctpg[i].addItem(arrow)
            elif factor == '체결강도':
                ymax, ymin = max(self.ctpg_tik_data[cindex(7)]), min(self.ctpg_tik_data[cindex(8)])
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len5:], y=self.ctpg_tik_data[cindex(6)], pen=(50, 50, 200))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len6:], y=self.ctpg_tik_data[cindex(7)], pen=(200, 50, 50))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len7:], y=self.ctpg_tik_data[cindex(8)], pen=(50, 200, 200))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(9)], pen=(50, 200, 50))
            elif factor == '초당거래대금':
                ymax, ymin = self.ctpg_tik_data[cindex(10)].max(), self.ctpg_tik_data[cindex(10)].min()
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(10)], pen=(200, 50, 50))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(11)], pen=(50, 200, 50))
            elif factor == '초당체결수량':
                ymax, ymin = max(self.ctpg_tik_data[cindex(12)].max(), self.ctpg_tik_data[cindex(13)].max()), min(self.ctpg_tik_data[cindex(12)].min(), self.ctpg_tik_data[cindex(13)].min())
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(12)], pen=(200, 50, 50))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(13)], pen=(50, 50, 200))
            elif factor == '등락율':
                ymax, ymin = self.ctpg_tik_data[cindex(14)].max(), self.ctpg_tik_data[cindex(14)].min()
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(14)], pen=(200, 50, 200))
            elif factor == '고저평균대비등락율':
                ymax, ymin = self.ctpg_tik_data[cindex(15)].max(), self.ctpg_tik_data[cindex(15)].min()
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(15)], pen=(50, 200, 200))
            elif factor == '호가총잔량':
                ymax, ymin = max(self.ctpg_tik_data[cindex(16)].max(), self.ctpg_tik_data[cindex(17)].max()), min(self.ctpg_tik_data[cindex(16)].min(), self.ctpg_tik_data[cindex(17)].min())
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(16)], pen=(200, 50, 50))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(17)], pen=(50, 50, 200))
            elif factor == '1호가잔량':
                ymax, ymin = max(self.ctpg_tik_data[cindex(18)].max(), self.ctpg_tik_data[cindex(19)].max()), min(self.ctpg_tik_data[cindex(18)].min(), self.ctpg_tik_data[cindex(19)].min())
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(18)], pen=(200, 50, 50))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(19)], pen=(50, 50, 200))
            elif factor == '5호가잔량합':
                ymax, ymin = self.ctpg_tik_data[cindex(20)].max(), self.ctpg_tik_data[cindex(20)].min()
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(20)], pen=(200, 50, 50))
            elif factor == '당일거래대금':
                ymax, ymin = self.ctpg_tik_data[cindex(21)].max(), self.ctpg_tik_data[cindex(21)].min()
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(21)], pen=(200, 50, 50))
            elif factor == '누적초당매도수수량':
                ymax, ymin = max(self.ctpg_tik_data[cindex(22)].max(), self.ctpg_tik_data[cindex(23)].max()), min(self.ctpg_tik_data[cindex(22)].min(), self.ctpg_tik_data[cindex(23)].min())
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(22)], pen=(200, 50, 50))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(23)], pen=(50, 50, 200))
            elif factor == '등락율각도':
                ymax, ymin = max(self.ctpg_tik_data[cindex(24)]), min(self.ctpg_tik_data[cindex(24)])
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(24)], pen=(200, 50, 50))
            elif factor == '당일거래대금각도':
                ymax, ymin = max(self.ctpg_tik_data[cindex(25)]), min(self.ctpg_tik_data[cindex(25)])
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len8:], y=self.ctpg_tik_data[cindex(25)], pen=(200, 50, 50))
            elif factor == '전일비각도':
                ymax, ymin = self.ctpg_tik_data[cindex(26)].max(), self.ctpg_tik_data[cindex(26)].min()
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(26)], pen=(200, 50, 50))
            elif factor == '거래대금증감':
                ymax, ymin = self.ctpg_tik_data[cindex(27)].max(), self.ctpg_tik_data[cindex(27)].min()
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(27)], pen=(200, 50, 50))
            elif factor == '전일비':
                ymax, ymin = self.ctpg_tik_data[cindex(28)].max(), self.ctpg_tik_data[cindex(28)].min()
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(28)], pen=(200, 50, 50))
            elif factor == '회전율':
                ymax, ymin = self.ctpg_tik_data[cindex(29)].max(), self.ctpg_tik_data[cindex(29)].min()
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(29)], pen=(200, 50, 50))
            elif factor == '전일동시간비':
                ymax, ymin = self.ctpg_tik_data[cindex(30)].max(), self.ctpg_tik_data[cindex(30)].min()
                if chuse_exist: self.ctpg[i].addItem(ChuseItem(self.ctpg_tik_arry[:, cindex(40)], ymin, ymax, self.ctpg_tik_xticks))
                self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(30)], pen=(200, 50, 50))

            if self.ct_checkBoxxxxx_22.isChecked():
                legend = pg.TextItem(anchor=(1, 0), color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                legend.setText(self.GetLabelText(coin, self.ctpg_tik_arry, -1, self.ctpg_tik_factors[i], hms))
                legend.setFont(qfont12)
                legend.setPos(xmax, ymax)
                self.ctpg[i].addItem(legend)
                self.ctpg_tik_legend[i] = legend

            if i != 0: self.ctpg[i].setXLink(self.ctpg[0])
            self.SetRangeCtpg(i, xmin, xmax, ymin, ymax)
            if self.ct_checkBoxxxxx_22.isChecked(): self.ctpg_tik_legend[i].setPos(self.ctpg_cvb[i].state['viewRange'][0][1], self.ctpg_cvb[i].state['viewRange'][1][1])
            if i == chart_count - 1: break

        if self.ct_checkBoxxxxx_21.isChecked():
            if chart_count == 8:    self.CrossHair(False, coin, self.ctpg[0], self.ctpg[1], self.ctpg[2], self.ctpg[3], self.ctpg[4], self.ctpg[5], self.ctpg[6], self.ctpg[7])
            elif chart_count == 12: self.CrossHair(False, coin, self.ctpg[0], self.ctpg[1], self.ctpg[2], self.ctpg[3], self.ctpg[4], self.ctpg[5], self.ctpg[6], self.ctpg[7], self.ctpg[8], self.ctpg[9], self.ctpg[10], self.ctpg[11])
            elif chart_count == 16: self.CrossHair(False, coin, self.ctpg[0], self.ctpg[1], self.ctpg[2], self.ctpg[3], self.ctpg[4], self.ctpg[5], self.ctpg[6], self.ctpg[7], self.ctpg[8], self.ctpg[9], self.ctpg[10], self.ctpg[11], self.ctpg[12], self.ctpg[13], self.ctpg[14], self.ctpg[15])

        self.ctpg_tik_name = self.ct_lineEdittttt_05.text()
        if not self.database_chart: self.database_chart = True

        if self.dialog_hoga.isVisible() and self.hg_labellllllll_01.text() != '':
            self.hgButtonClicked_02('매수')

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

        win32gui.SetForegroundWindow(int(self.winId()))

    def CrossHair(self, real, coin_, main_pg, sub_pg1, sub_pg2, sub_pg3, sub_pg4, sub_pg5, sub_pg6, sub_pg7, sub_pg8=None,
                  sub_pg9=None, sub_pg10=None, sub_pg11=None, sub_pg12=None, sub_pg13=None, sub_pg14=None, sub_pg15=None):
        def setInfiniteLine(angle=None):
            if angle is None:
                vhline = pg.InfiniteLine()
            else:
                vhline = pg.InfiniteLine(angle=angle)
            vhline.setPen(pg.mkPen(color_cs_hr, width=0.5, style=Qt.DashLine))
            return vhline

        hLine1  = setInfiniteLine(angle=0)
        hLine2  = setInfiniteLine(angle=0)
        hLine3  = setInfiniteLine(angle=0)
        hLine4  = setInfiniteLine(angle=0)
        hLine5  = setInfiniteLine(angle=0)
        hLine6  = setInfiniteLine(angle=0)
        hLine7  = setInfiniteLine(angle=0)
        hLine8  = setInfiniteLine(angle=0)
        hLine9  = setInfiniteLine(angle=0)
        hLine10 = setInfiniteLine(angle=0)
        hLine11 = setInfiniteLine(angle=0)
        hLine12 = setInfiniteLine(angle=0)
        hLine13 = setInfiniteLine(angle=0)
        hLine14 = setInfiniteLine(angle=0)
        hLine15 = setInfiniteLine(angle=0)
        hLine16 = setInfiniteLine(angle=0)

        vLine1  = setInfiniteLine()
        vLine2  = setInfiniteLine()
        vLine3  = setInfiniteLine()
        vLine4  = setInfiniteLine()
        vLine5  = setInfiniteLine()
        vLine6  = setInfiniteLine()
        vLine7  = setInfiniteLine()
        vLine8  = setInfiniteLine()
        vLine9  = setInfiniteLine()
        vLine10 = setInfiniteLine()
        vLine11 = setInfiniteLine()
        vLine12 = setInfiniteLine()
        vLine13 = setInfiniteLine()
        vLine14 = setInfiniteLine()
        vLine15 = setInfiniteLine()
        vLine16 = setInfiniteLine()

        if sub_pg8 is not None and sub_pg12 is not None:
            hLines = [hLine1, hLine2, hLine3, hLine4, hLine5, hLine6, hLine7, hLine8, hLine9, hLine10, hLine11, hLine12, hLine13, hLine14, hLine15, hLine16]
        elif sub_pg8 is not None and sub_pg12 is None:
            hLines = [hLine1, hLine2, hLine3, hLine4, hLine5, hLine6, hLine7, hLine8, hLine9, hLine10, hLine11, hLine12]
        else:
            hLines = [hLine1, hLine2, hLine3, hLine4, hLine5, hLine6, hLine7, hLine8]

        if sub_pg8 is not None and sub_pg12 is not None:
            vLines = [vLine1, vLine2, vLine3, vLine4, vLine5, vLine6, vLine7, vLine8, vLine9, vLine10, vLine11, vLine12, vLine13, vLine14, vLine15, vLine16]
        elif sub_pg8 is not None and sub_pg12 is None:
            vLines = [vLine1, vLine2, vLine3, vLine4, vLine5, vLine6, vLine7, vLine8, vLine9, vLine10, vLine11, vLine12]
        else:
            vLines = [vLine1, vLine2, vLine3, vLine4, vLine5, vLine6, vLine7, vLine8]

        self.ctpg_tik_labels = []
        count_ = 8
        if sub_pg8 is not None:
            count_ = 12
        if sub_pg12 is not None:
            count_ = 16

        for k in range(count_):
            kxmin = self.ctpg_cvb[k].state['viewRange'][0][0]
            kymin = self.ctpg_cvb[k].state['viewRange'][1][0]
            label = pg.TextItem(anchor=(0, 1), color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
            label.setFont(qfont12)
            label.setPos(kxmin, kymin)
            self.ctpg_tik_labels.append(label)
            if k == len(self.ctpg_tik_factors) - 1:
                break

        try:
            main_pg.addItem(vLine1, ignoreBounds=True)
            sub_pg1.addItem(vLine2, ignoreBounds=True)
            sub_pg2.addItem(vLine3, ignoreBounds=True)
            sub_pg3.addItem(vLine4, ignoreBounds=True)
            sub_pg4.addItem(vLine5, ignoreBounds=True)
            sub_pg5.addItem(vLine6, ignoreBounds=True)
            sub_pg6.addItem(vLine7, ignoreBounds=True)
            sub_pg7.addItem(vLine8, ignoreBounds=True)
            main_pg.addItem(hLine1, ignoreBounds=True)
            sub_pg1.addItem(hLine2, ignoreBounds=True)
            sub_pg2.addItem(hLine3, ignoreBounds=True)
            sub_pg3.addItem(hLine4, ignoreBounds=True)
            sub_pg4.addItem(hLine5, ignoreBounds=True)
            sub_pg5.addItem(hLine6, ignoreBounds=True)
            sub_pg6.addItem(hLine7, ignoreBounds=True)
            sub_pg7.addItem(hLine8, ignoreBounds=True)
            main_pg.addItem(self.ctpg_tik_labels[0])
            sub_pg1.addItem(self.ctpg_tik_labels[1])
            sub_pg2.addItem(self.ctpg_tik_labels[2])
            sub_pg3.addItem(self.ctpg_tik_labels[3])
            sub_pg4.addItem(self.ctpg_tik_labels[4])
            sub_pg5.addItem(self.ctpg_tik_labels[5])
            sub_pg6.addItem(self.ctpg_tik_labels[6])
            sub_pg7.addItem(self.ctpg_tik_labels[7])
            if sub_pg8 is not None:
                sub_pg8.addItem(vLine9, ignoreBounds=True)
                sub_pg9.addItem(vLine10, ignoreBounds=True)
                sub_pg10.addItem(vLine11, ignoreBounds=True)
                sub_pg11.addItem(vLine12, ignoreBounds=True)
                sub_pg8.addItem(hLine9, ignoreBounds=True)
                sub_pg9.addItem(hLine10, ignoreBounds=True)
                sub_pg10.addItem(hLine11, ignoreBounds=True)
                sub_pg11.addItem(hLine12, ignoreBounds=True)
                sub_pg8.addItem(self.ctpg_tik_labels[8])
                sub_pg9.addItem(self.ctpg_tik_labels[9])
                sub_pg10.addItem(self.ctpg_tik_labels[10])
                sub_pg11.addItem(self.ctpg_tik_labels[11])
            if sub_pg12 is not None:
                sub_pg12.addItem(vLine13, ignoreBounds=True)
                sub_pg13.addItem(vLine14, ignoreBounds=True)
                sub_pg14.addItem(vLine15, ignoreBounds=True)
                sub_pg15.addItem(vLine16, ignoreBounds=True)
                sub_pg12.addItem(hLine13, ignoreBounds=True)
                sub_pg13.addItem(hLine14, ignoreBounds=True)
                sub_pg14.addItem(hLine15, ignoreBounds=True)
                sub_pg15.addItem(hLine16, ignoreBounds=True)
                sub_pg12.addItem(self.ctpg_tik_labels[12])
                sub_pg13.addItem(self.ctpg_tik_labels[13])
                sub_pg14.addItem(self.ctpg_tik_labels[14])
                sub_pg15.addItem(self.ctpg_tik_labels[15])
        except:
            pass

        if sub_pg8 is not None and sub_pg12 is not None:
            pg_list = [main_pg, sub_pg1, sub_pg2, sub_pg3, sub_pg4, sub_pg5, sub_pg6, sub_pg7, sub_pg8, sub_pg9,
                       sub_pg10, sub_pg11, sub_pg12, sub_pg13, sub_pg14, sub_pg15]
        elif sub_pg8 is not None and sub_pg12 is None:
            pg_list = [main_pg, sub_pg1, sub_pg2, sub_pg3, sub_pg4, sub_pg5, sub_pg6, sub_pg7, sub_pg8, sub_pg9,
                       sub_pg10, sub_pg11]
        else:
            pg_list = [main_pg, sub_pg1, sub_pg2, sub_pg3, sub_pg4, sub_pg5, sub_pg6, sub_pg7]

        def mouseMoved(evt):
            pos = evt[0]
            index = -1
            if main_pg.sceneBoundingRect().contains(pos):        index =  0
            elif sub_pg1.sceneBoundingRect().contains(pos):      index =  1
            elif sub_pg2.sceneBoundingRect().contains(pos):      index =  2
            elif sub_pg3.sceneBoundingRect().contains(pos):      index =  3
            elif sub_pg4.sceneBoundingRect().contains(pos):      index =  4
            elif sub_pg5.sceneBoundingRect().contains(pos):      index =  5
            elif sub_pg6.sceneBoundingRect().contains(pos):      index =  6
            elif sub_pg7.sceneBoundingRect().contains(pos):      index =  7
            if sub_pg8 is not None:
                if sub_pg8.sceneBoundingRect().contains(pos):    index =  8
                elif sub_pg9.sceneBoundingRect().contains(pos):  index =  9
                elif sub_pg10.sceneBoundingRect().contains(pos): index = 10
                elif sub_pg11.sceneBoundingRect().contains(pos): index = 11
            if sub_pg12 is not None:
                if sub_pg12.sceneBoundingRect().contains(pos):   index = 12
                elif sub_pg13.sceneBoundingRect().contains(pos): index = 13
                elif sub_pg14.sceneBoundingRect().contains(pos): index = 14
                elif sub_pg15.sceneBoundingRect().contains(pos): index = 15

            if index != -1:
                try:
                    mousePoint = pg_list[index].getViewBox().mapSceneToView(pos)
                    xpoint = self.ctpg_tik_xticks.index(int(mousePoint.x()))
                    hms_   = from_timestamp(int(mousePoint.x())).strftime('%H:%M:%S')
                    for n, labell in enumerate(self.ctpg_tik_labels):
                        foctor = self.ctpg_tik_factors[n]
                        if index == n:
                            text = f'Y축 {round(mousePoint.y(), 2):,}\n{self.GetLabelText(coin_, self.ctpg_tik_arry, xpoint, foctor, hms_)}'
                        else:
                            text = self.GetLabelText(coin_, self.ctpg_tik_arry, xpoint, foctor, hms_)
                        labell.setText(text)
                        lxmin, lxmax = self.ctpg_cvb[n].state['viewRange'][0]
                        lymin, lymax = self.ctpg_cvb[n].state['viewRange'][1]
                        if not real:
                            if mousePoint.x() < lxmin + (lxmax - lxmin) * 0.33:
                                if self.ct_checkBoxxxxx_21.isChecked():
                                    labell.setAnchor((1, 1))
                                    labell.setPos(lxmax, lymin)
                                if self.ct_checkBoxxxxx_22.isChecked():
                                    self.ctpg_tik_legend[n].setAnchor((1, 0))
                                    self.ctpg_tik_legend[n].setPos(lxmax, lymax)
                            else:
                                if self.ct_checkBoxxxxx_21.isChecked():
                                    labell.setAnchor((0, 1))
                                    labell.setPos(lxmin, lymin)
                                if self.ct_checkBoxxxxx_22.isChecked():
                                    self.ctpg_tik_legend[n].setAnchor((0, 0))
                                    self.ctpg_tik_legend[n].setPos(lxmin, lymax)
                        if n == len(self.ctpg_tik_factors) - 1:
                            break
                    hLines[index].setPos(mousePoint.y())
                    for vLine in vLines:
                        vLine.setPos(mousePoint.x())
                except:
                    pass

        main_pg.proxy = pg.SignalProxy(main_pg.scene().sigMouseMoved, rateLimit=20, slot=mouseMoved)

    @staticmethod
    def GetLabelText(coin, arry, xpoint, factor, hms):
        def cindex(number):
            return dict_stock[number] if not coin else dict_coin[number]

        dict_stock = {
            1: 44, 2: 45, 3: 46, 4: 47, 5: 1, 6: 50, 7: 51, 8: 52, 9: 7, 10: 19, 11: 57, 12: 14, 13: 15, 14: 5, 15: 20,
            16: 22, 17: 21, 18: 38, 19: 37, 20: 43, 21: 6, 22: 55, 23: 56, 24: 58, 25: 59, 26: 60, 27: 8, 28: 9, 29: 10,
            30: 11
        }
        dict_coin = {
            1: 35, 2: 36, 3: 37, 4: 38, 5: 1, 6: 41, 7: 42, 8: 43, 9: 7, 10: 10, 11: 48, 12: 8, 13: 9, 14: 5, 15: 11,
            16: 13, 17: 12, 18: 29, 19: 28, 20: 34, 21: 6, 22: 46, 23: 47, 24: 49, 25: 50
        }

        jpd = 0
        dmj = 0
        jip = 0
        hjp = 0
        jdp = 0
        ema0060 = arry[xpoint, cindex(1)]
        ema0300 = arry[xpoint, cindex(2)]
        ema0600 = arry[xpoint, cindex(3)]
        ema1200 = arry[xpoint, cindex(4)]
        cc      = arry[xpoint, cindex(5)]
        ch      = arry[xpoint, cindex(9)]
        ach     = arry[xpoint, cindex(6)]
        hch     = arry[xpoint, cindex(7)]
        lch     = arry[xpoint, cindex(8)]
        sm      = arry[xpoint, cindex(10)]
        asm     = arry[xpoint, cindex(11)]
        bbc     = arry[xpoint, cindex(12)]
        sbc     = arry[xpoint, cindex(13)]
        per     = arry[xpoint, cindex(14)]
        hlp     = arry[xpoint, cindex(15)]
        tbj     = arry[xpoint, cindex(16)]
        tsj     = arry[xpoint, cindex(17)]
        b1j     = arry[xpoint, cindex(18)]
        s1j     = arry[xpoint, cindex(19)]
        jr5     = arry[xpoint, cindex(20)]
        dm      = arry[xpoint, cindex(21)]
        nsb     = arry[xpoint, cindex(22)]
        nss     = arry[xpoint, cindex(23)]
        prd     = arry[xpoint, cindex(24)]
        dmd     = arry[xpoint, cindex(25)]
        if not coin:
            jpd = arry[xpoint, cindex(26)]
            dmj = arry[xpoint, cindex(27)]
            jip = arry[xpoint, cindex(28)]
            hjp = arry[xpoint, cindex(29)]
            jdp = arry[xpoint, cindex(30)]

        text = ''
        if factor == '현재가':
            if coin:
                text = f"시간 {hms}\n" \
                       f"이평0060 {ema0060:,.8f}\n" \
                       f"이평0300 {ema0300:,.8f}\n" \
                       f"이평0600 {ema0600:,.8f}\n" \
                       f"이평1200 {ema1200:,.8f}\n" \
                       f"현재가       {cc:,.4f}"
            else:
                text = f"시간 {hms}\n" \
                       f"이평0060 {ema0060:,.3f}\n" \
                       f"이평0300 {ema0300:,.3f}\n" \
                       f"이평0600 {ema0600:,.3f}\n" \
                       f"이평1200 {ema1200:,.3f}\n" \
                       f"현재가       {cc:,.0f}"
        elif factor == '체결강도':
            text = f"체결강도        {ch:,.2f}\n" \
                   f"체결강도평균 {ach:,.2f}\n" \
                   f"최고체결강도 {hch:,.2f}\n" \
                   f"최저체결강도 {lch:,.2f}"
        elif factor == '초당거래대금':
            text = f"초당거래대금        {sm:,.0f}\n" \
                   f"초당거래대금평균 {asm:,.0f}"
        elif factor == '초당체결수량':
            if coin:
                text = f"초당매수수량 {bbc:,.8f}\n" \
                       f"초당매도수량 {sbc:,.8f}"
            else:
                text = f"초당매수수량 {bbc:,.0f}\n" \
                       f"초당매도수량 {sbc:,.0f}"
        elif factor == '등락율':
            text = f"등락율 {per:,.2f}%"
        elif factor == '고저평균대비등락율':
            text = f"고저평균등락율 {hlp:,.2f}%"
        elif factor == '호가총잔량':
            if coin:
                text = f"매도총잔량 {tsj:,.8f}\n" \
                       f"매수총잔량 {tbj:,.8f}"
            else:
                text = f"매도총잔량 {tsj:,.0f}\n" \
                       f"매수총잔량 {tbj:,.0f}"
        elif factor == '1호가잔량':
            if coin:
                text = f"매도1잔량 {s1j:,.8f}\n" \
                       f"매수1잔량 {b1j:,.8f}"
            else:
                text = f"매도1잔량 {s1j:,.0f}\n" \
                       f"매수1잔량 {b1j:,.0f}"
        elif factor == '5호가잔량합':
            if coin:
                text = f"5호가잔량합 {jr5:,.8f}"
            else:
                text = f"5호가잔량합 {jr5:,.0f}"
        elif factor == '당일거래대금':
            text = f"당일거래대금 {dm:,.0f}"
        elif factor == '누적초당매도수수량':
            if coin:
                text = f"누적초당매수수량 {nsb:,.8f}\n" \
                       f"누적초당매도수량 {nss:,.8f}"
            else:
                text = f"누적초당매수수량 {nsb:,.0f}\n" \
                       f"누적초당매도수량 {nss:,.0f}"
        elif factor == '등락율각도':
            text = f"등락율각도 {prd:,.2f}º"
        elif factor == '당일거래대금각도':
            text = f"당일거래대금각도 {dmd:,.2f}º"
        elif factor == '전일비각도':
            text = f"전일비각도 {jpd:,.2f}º"
        elif factor == '거래대금증감':
            text = f"거래대금증감 {dmj:,.2f}"
        elif factor == '전일비':
            text = f"전일비 {jip:,.2f}%"
        elif factor == '회전율':
            text = f"회전율 {hjp:,.2f}%"
        elif factor == '전일동시간비':
            text = f"전일동시간비 {jdp:,.2f}%"
        return text

    @error_decorator
    def DrawRealChart(self, data):
        def cindex(number):
            return dict_stock[number] if not coin else dict_coin[number]

        if not self.dialog_chart.isVisible():
            self.ChartClear()
            return

        name, self.ctpg_tik_arry = data[1:]
        coin = True if 'KRW' in name or 'USDT' in name else False

        if self.ct_pushButtonnn_04.text() == 'CHART 8':
            chart_count = 8
        elif self.ct_pushButtonnn_04.text() == 'CHART 12':
            chart_count = 12
        else:
            chart_count = 16

        if self.ctpg_tik_name != name:
            self.ctpg_tik_item    = {}
            self.ctpg_tik_data    = {}
            self.ctpg_tik_legend  = {}
            self.ctpg_tik_factors = []
            if self.ct_checkBoxxxxx_01.isChecked():     self.ctpg_tik_factors.append('현재가')
            if self.ct_checkBoxxxxx_02.isChecked():     self.ctpg_tik_factors.append('체결강도')
            if self.ct_checkBoxxxxx_03.isChecked():     self.ctpg_tik_factors.append('초당거래대금')
            if self.ct_checkBoxxxxx_04.isChecked():     self.ctpg_tik_factors.append('초당체결수량')
            if self.ct_checkBoxxxxx_05.isChecked():     self.ctpg_tik_factors.append('등락율')
            if self.ct_checkBoxxxxx_06.isChecked():     self.ctpg_tik_factors.append('고저평균대비등락율')
            if self.ct_checkBoxxxxx_07.isChecked():     self.ctpg_tik_factors.append('호가총잔량')
            if self.ct_checkBoxxxxx_08.isChecked():     self.ctpg_tik_factors.append('1호가잔량')
            if self.ct_checkBoxxxxx_09.isChecked():     self.ctpg_tik_factors.append('5호가잔량합')
            if self.ct_checkBoxxxxx_10.isChecked():     self.ctpg_tik_factors.append('당일거래대금')
            if self.ct_checkBoxxxxx_11.isChecked():     self.ctpg_tik_factors.append('누적초당매도수수량')
            if self.ct_checkBoxxxxx_12.isChecked():     self.ctpg_tik_factors.append('등락율각도')
            if self.ct_checkBoxxxxx_13.isChecked():     self.ctpg_tik_factors.append('당일거래대금각도')
            if not coin:
                if self.ct_checkBoxxxxx_14.isChecked(): self.ctpg_tik_factors.append('거래대금증감')
                if self.ct_checkBoxxxxx_15.isChecked(): self.ctpg_tik_factors.append('전일비')
                if self.ct_checkBoxxxxx_16.isChecked(): self.ctpg_tik_factors.append('회전율')
                if self.ct_checkBoxxxxx_17.isChecked(): self.ctpg_tik_factors.append('전일동시간비')
                if self.ct_checkBoxxxxx_18.isChecked(): self.ctpg_tik_factors.append('전일비각도')

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

        for j in range(len(self.ctpg_tik_arry[0, :])):
            if j in (cindex(1), cindex(2), cindex(3), cindex(4), cindex(6), cindex(7), cindex(8), cindex(25)):
                self.ctpg_tik_data[j] = [x for x in self.ctpg_tik_arry[:, j] if x != 0]
            else:
                self.ctpg_tik_data[j] = self.ctpg_tik_arry[:, j]

        self.ctpg_tik_xticks = [strp_time('%Y%m%d%H%M%S', str(int(x))).timestamp() for x in self.ctpg_tik_data[0]]
        xmin, xmax = self.ctpg_tik_xticks[0], self.ctpg_tik_xticks[-1]
        hms  = from_timestamp(xmax).strftime('%H:%M:%S')
        tlen = len(self.ctpg_tik_xticks)
        len1 = len(self.ctpg_tik_data[cindex(1)])
        len2 = len(self.ctpg_tik_data[cindex(2)])
        len3 = len(self.ctpg_tik_data[cindex(3)])
        len4 = len(self.ctpg_tik_data[cindex(4)])
        len5 = len(self.ctpg_tik_data[cindex(6)])
        len6 = len(self.ctpg_tik_data[cindex(7)])
        len7 = len(self.ctpg_tik_data[cindex(8)])
        len8 = len(self.ctpg_tik_data[cindex(25)])

        if self.ctpg_tik_name != name:
            for i, factor in enumerate(self.ctpg_tik_factors):
                self.ctpg[i].clear()
                ymin, ymax = 0, 0
                if factor == '현재가':
                    self.ctpg_tik_item[1] = self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len1:], y=self.ctpg_tik_data[cindex(1)], pen=(140, 140, 145))
                    self.ctpg_tik_item[2] = self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len2:], y=self.ctpg_tik_data[cindex(2)], pen=(120, 120, 125))
                    self.ctpg_tik_item[3] = self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len3:], y=self.ctpg_tik_data[cindex(3)], pen=(100, 100, 105))
                    self.ctpg_tik_item[4] = self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len4:], y=self.ctpg_tik_data[cindex(4)], pen=(80, 80, 85))
                    self.ctpg_tik_item[5] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(5)], pen=(200, 50, 50))
                    self.ctpg_tik_cline = pg.InfiniteLine(angle=0)
                    self.ctpg_tik_cline.setPen(pg.mkPen(color_fg_bt))
                    self.ctpg_tik_cline.setPos(self.ctpg_tik_data[cindex(5)][-1])
                    self.ctpg[i].addItem(self.ctpg_tik_cline)
                    list_ = self.ctpg_tik_data[cindex(1)] + self.ctpg_tik_data[cindex(2)] + self.ctpg_tik_data[cindex(3)] + self.ctpg_tik_data[cindex(4)] + list(self.ctpg_tik_data[cindex(5)])
                    ymax, ymin = max(list_), min(list_)
                elif factor == '체결강도':
                    self.ctpg_tik_item[6] = self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len5:], y=self.ctpg_tik_data[cindex(6)], pen=(50, 50, 200))
                    self.ctpg_tik_item[7] = self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len6:], y=self.ctpg_tik_data[cindex(7)], pen=(200, 50, 50))
                    self.ctpg_tik_item[8] = self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len7:], y=self.ctpg_tik_data[cindex(8)], pen=(50, 200, 200))
                    self.ctpg_tik_item[9] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(9)], pen=(50, 200, 50))
                    ymax, ymin = max(self.ctpg_tik_data[cindex(7)]), min(self.ctpg_tik_data[cindex(8)])
                elif factor == '초당거래대금':
                    self.ctpg_tik_item[10] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(10)], pen=(200, 50, 50))
                    self.ctpg_tik_item[11] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(11)], pen=(50, 200, 50))
                    ymax, ymin = self.ctpg_tik_data[cindex(10)].max(), self.ctpg_tik_data[cindex(10)].min()
                elif factor == '초당체결수량':
                    self.ctpg_tik_item[12] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(12)], pen=(200, 50, 50))
                    self.ctpg_tik_item[13] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(13)], pen=(50, 50, 200))
                    ymax, ymin = max(self.ctpg_tik_data[cindex(12)].max(), self.ctpg_tik_data[cindex(13)].max()), min(self.ctpg_tik_data[cindex(12)].min(), self.ctpg_tik_data[cindex(13)].min())
                elif factor == '등락율':
                    self.ctpg_tik_item[14] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(14)], pen=(200, 50, 200))
                    ymax, ymin = self.ctpg_tik_data[cindex(14)].max(), self.ctpg_tik_data[cindex(14)].min()
                elif factor == '고저평균대비등락율':
                    self.ctpg_tik_item[15] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(15)], pen=(50, 200, 200))
                    ymax, ymin = self.ctpg_tik_data[cindex(15)].max(), self.ctpg_tik_data[cindex(15)].min()
                elif factor == '호가총잔량':
                    self.ctpg_tik_item[16] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(16)], pen=(200, 50, 50))
                    self.ctpg_tik_item[17] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(17)], pen=(50, 50, 200))
                    ymax, ymin = max(self.ctpg_tik_data[cindex(16)].max(), self.ctpg_tik_data[cindex(17)].max()), min(self.ctpg_tik_data[cindex(16)].min(), self.ctpg_tik_data[cindex(17)].min())
                elif factor == '1호가잔량':
                    self.ctpg_tik_item[18] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(18)], pen=(200, 50, 50))
                    self.ctpg_tik_item[19] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(19)], pen=(50, 50, 200))
                    ymax, ymin = max(self.ctpg_tik_data[cindex(18)].max(), self.ctpg_tik_data[cindex(19)].max()), min(self.ctpg_tik_data[cindex(18)].min(), self.ctpg_tik_data[cindex(19)].min())
                elif factor == '5호가잔량합':
                    self.ctpg_tik_item[20] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(20)], pen=(200, 50, 50))
                    ymax, ymin = self.ctpg_tik_data[cindex(20)].max(), self.ctpg_tik_data[cindex(20)].min()
                elif factor == '당일거래대금':
                    self.ctpg_tik_item[21] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(21)], pen=(200, 50, 50))
                    ymax, ymin = self.ctpg_tik_data[cindex(21)].max(), self.ctpg_tik_data[cindex(21)].min()
                elif factor == '누적초당매도수수량':
                    self.ctpg_tik_item[22] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(22)], pen=(200, 50, 50))
                    self.ctpg_tik_item[23] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(23)], pen=(50, 50, 200))
                    ymax, ymin = max(self.ctpg_tik_data[cindex(22)].max(), self.ctpg_tik_data[cindex(23)].max()), min(self.ctpg_tik_data[cindex(22)].min(), self.ctpg_tik_data[cindex(23)].min())
                elif factor == '등락율각도':
                    self.ctpg_tik_item[24] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(24)], pen=(200, 50, 50))
                    ymax, ymin = max(self.ctpg_tik_data[cindex(24)]), min(self.ctpg_tik_data[cindex(24)])
                elif factor == '당일거래대금각도':
                    self.ctpg_tik_item[25] = self.ctpg[i].plot(x=self.ctpg_tik_xticks[tlen - len8:], y=self.ctpg_tik_data[cindex(25)], pen=(200, 50, 50))
                    ymax, ymin = max(self.ctpg_tik_data[cindex(25)]), min(self.ctpg_tik_data[cindex(25)])
                elif factor == '전일비각도':
                    self.ctpg_tik_item[26] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(26)], pen=(200, 50, 50))
                    ymax, ymin = self.ctpg_tik_data[cindex(26)].max(), self.ctpg_tik_data[cindex(26)].min()
                elif factor == '거래대금증감':
                    self.ctpg_tik_item[27] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(27)], pen=(200, 50, 50))
                    ymax, ymin = self.ctpg_tik_data[cindex(27)].max(), self.ctpg_tik_data[cindex(27)].min()
                elif factor == '전일비':
                    self.ctpg_tik_item[28] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(28)], pen=(200, 50, 50))
                    ymax, ymin = self.ctpg_tik_data[cindex(28)].max(), self.ctpg_tik_data[cindex(28)].min()
                elif factor == '회전율':
                    self.ctpg_tik_item[29] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(29)], pen=(200, 50, 50))
                    ymax, ymin = self.ctpg_tik_data[cindex(29)].max(), self.ctpg_tik_data[cindex(29)].min()
                elif factor == '전일동시간비':
                    self.ctpg_tik_item[30] = self.ctpg[i].plot(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(30)], pen=(200, 50, 50))
                    ymax, ymin = self.ctpg_tik_data[cindex(30)].max(), self.ctpg_tik_data[cindex(30)].min()

                if self.ct_checkBoxxxxx_22.isChecked():
                    legend = pg.TextItem(anchor=(0, 0), color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                    legend.setFont(qfont12)
                    legend.setText(self.GetLabelText(coin, self.ctpg_tik_arry, -1, self.ctpg_tik_factors[i], hms))
                    self.ctpg[i].addItem(legend)
                    self.ctpg_tik_legend[i] = legend

                if i != 0: self.ctpg[i].setXLink(self.ctpg[0])
                self.SetRangeCtpg(i, xmin, xmax, ymin, ymax)
                if self.ct_checkBoxxxxx_22.isChecked():
                    self.ctpg_tik_legend[i].setPos(self.ctpg_cvb[i].state['viewRange'][0][0], self.ctpg_cvb[i].state['viewRange'][1][1])
                if i == chart_count - 1: break

            self.ctpg_tik_name = name
            if self.ct_checkBoxxxxx_21.isChecked():
                if chart_count == 8:    self.CrossHair(True, coin, self.ctpg[0], self.ctpg[1], self.ctpg[2], self.ctpg[3], self.ctpg[4], self.ctpg[5], self.ctpg[6], self.ctpg[7])
                elif chart_count == 12: self.CrossHair(True, coin, self.ctpg[0], self.ctpg[1], self.ctpg[2], self.ctpg[3], self.ctpg[4], self.ctpg[5], self.ctpg[6], self.ctpg[7], self.ctpg[8], self.ctpg[9], self.ctpg[10], self.ctpg[11])
                elif chart_count == 16: self.CrossHair(True, coin, self.ctpg[0], self.ctpg[1], self.ctpg[2], self.ctpg[3], self.ctpg[4], self.ctpg[5], self.ctpg[6], self.ctpg[7], self.ctpg[8], self.ctpg[9], self.ctpg[10], self.ctpg[11], self.ctpg[12], self.ctpg[13], self.ctpg[14], self.ctpg[15])
        else:
            for i, factor in enumerate(self.ctpg_tik_factors):
                ymin, ymax = 0, 0
                if factor == '현재가':
                    list_ = self.ctpg_tik_data[cindex(1)] + self.ctpg_tik_data[cindex(2)] + self.ctpg_tik_data[cindex(3)] + self.ctpg_tik_data[cindex(4)] + list(self.ctpg_tik_data[cindex(5)])
                    ymax, ymin = max(list_), min(list_)
                    self.ctpg_tik_item[1].setData(x=self.ctpg_tik_xticks[tlen - len1:], y=self.ctpg_tik_data[cindex(1)])
                    self.ctpg_tik_item[2].setData(x=self.ctpg_tik_xticks[tlen - len2:], y=self.ctpg_tik_data[cindex(2)])
                    self.ctpg_tik_item[3].setData(x=self.ctpg_tik_xticks[tlen - len3:], y=self.ctpg_tik_data[cindex(3)])
                    self.ctpg_tik_item[4].setData(x=self.ctpg_tik_xticks[tlen - len4:], y=self.ctpg_tik_data[cindex(4)])
                    self.ctpg_tik_item[5].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(5)])
                    self.ctpg_tik_cline.setPos(self.ctpg_tik_data[cindex(5)][-1])
                elif factor == '체결강도':
                    ymax, ymin = max(self.ctpg_tik_data[cindex(7)]), min(self.ctpg_tik_data[cindex(8)])
                    self.ctpg_tik_item[6].setData(x=self.ctpg_tik_xticks[tlen - len5:], y=self.ctpg_tik_data[cindex(6)])
                    self.ctpg_tik_item[7].setData(x=self.ctpg_tik_xticks[tlen - len6:], y=self.ctpg_tik_data[cindex(7)])
                    self.ctpg_tik_item[8].setData(x=self.ctpg_tik_xticks[tlen - len7:], y=self.ctpg_tik_data[cindex(8)])
                    self.ctpg_tik_item[9].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(9)])
                elif factor == '초당거래대금':
                    ymax, ymin = self.ctpg_tik_data[cindex(10)].max(), self.ctpg_tik_data[cindex(10)].min()
                    self.ctpg_tik_item[10].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(10)])
                    self.ctpg_tik_item[11].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(11)])
                elif factor == '초당체결수량':
                    ymax, ymin = max(self.ctpg_tik_data[cindex(12)].max(), self.ctpg_tik_data[cindex(13)].max()), min(self.ctpg_tik_data[cindex(12)].min(), self.ctpg_tik_data[cindex(13)].min())
                    self.ctpg_tik_item[12].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(12)])
                    self.ctpg_tik_item[13].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(13)])
                elif factor == '등락율':
                    ymax, ymin = self.ctpg_tik_data[cindex(14)].max(), self.ctpg_tik_data[cindex(14)].min()
                    self.ctpg_tik_item[14].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(14)])
                elif factor == '고저평균대비등락율':
                    ymax, ymin = self.ctpg_tik_data[cindex(15)].max(), self.ctpg_tik_data[cindex(15)].min()
                    self.ctpg_tik_item[15].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(15)])
                elif factor == '호가총잔량':
                    ymax, ymin = max(self.ctpg_tik_data[cindex(16)].max(), self.ctpg_tik_data[cindex(17)].max()), min(self.ctpg_tik_data[cindex(16)].min(), self.ctpg_tik_data[cindex(17)].min())
                    self.ctpg_tik_item[16].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(16)])
                    self.ctpg_tik_item[17].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(17)])
                elif factor == '1호가잔량':
                    ymax, ymin = max(self.ctpg_tik_data[cindex(18)].max(), self.ctpg_tik_data[cindex(19)].max()), min(self.ctpg_tik_data[cindex(18)].min(), self.ctpg_tik_data[cindex(19)].min())
                    self.ctpg_tik_item[18].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(18)])
                    self.ctpg_tik_item[19].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(19)])
                elif factor == '5호가잔량합':
                    ymax, ymin = self.ctpg_tik_data[cindex(20)].max(), self.ctpg_tik_data[cindex(20)].min()
                    self.ctpg_tik_item[20].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(20)])
                elif factor == '당일거래대금':
                    ymax, ymin = self.ctpg_tik_data[cindex(21)].max(), self.ctpg_tik_data[cindex(21)].min()
                    self.ctpg_tik_item[21].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(21)])
                elif factor == '누적초당매도수수량':
                    ymax, ymin = max(self.ctpg_tik_data[cindex(22)].max(), self.ctpg_tik_data[cindex(23)].max()), min(self.ctpg_tik_data[cindex(22)].min(), self.ctpg_tik_data[cindex(23)].min())
                    self.ctpg_tik_item[22].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(22)])
                    self.ctpg_tik_item[23].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(23)])
                elif factor == '등락율각도':
                    ymax, ymin = max(self.ctpg_tik_data[cindex(24)]), min(self.ctpg_tik_data[cindex(24)])
                    self.ctpg_tik_item[24].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(24)])
                elif factor == '당일거래대금각도':
                    ymax, ymin = max(self.ctpg_tik_data[cindex(25)]), min(self.ctpg_tik_data[cindex(25)])
                    self.ctpg_tik_item[25].setData(x=self.ctpg_tik_xticks[tlen - len8:], y=self.ctpg_tik_data[cindex(25)])
                elif factor == '전일비각도':
                    ymax, ymin = self.ctpg_tik_data[cindex(26)].max(), self.ctpg_tik_data[cindex(26)].min()
                    self.ctpg_tik_item[26].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(26)])
                elif factor == '거래대금증감':
                    ymax, ymin = self.ctpg_tik_data[cindex(27)].max(), self.ctpg_tik_data[cindex(27)].min()
                    self.ctpg_tik_item[27].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(27)])
                elif factor == '전일비':
                    ymax, ymin = self.ctpg_tik_data[cindex(28)].max(), self.ctpg_tik_data[cindex(28)].min()
                    self.ctpg_tik_item[28].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(28)])
                elif factor == '회전율':
                    ymax, ymin = self.ctpg_tik_data[cindex(29)].max(), self.ctpg_tik_data[cindex(29)].min()
                    self.ctpg_tik_item[29].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(29)])
                elif factor == '전일동시간비':
                    ymax, ymin = self.ctpg_tik_data[cindex(30)].max(), self.ctpg_tik_data[cindex(30)].min()
                    self.ctpg_tik_item[30].setData(x=self.ctpg_tik_xticks, y=self.ctpg_tik_data[cindex(30)])

                self.SetRangeCtpg(i, xmin, xmax, ymin, ymax)
                self.SetPosLegendLabel(i, coin, hms)
                if i == chart_count - 1: break

        if self.database_chart: self.database_chart = False

    def SetRangeCtpg(self, i, xmin, xmax, ymin, ymax):
        self.ctpg_cvb[i].set_range(xmin, xmax, ymin, ymax)
        self.ctpg[i].setRange(xRange=(xmin, xmax), yRange=(ymin, ymax))

    def SetPosLegendLabel(self, i, coin, hms):
        if self.ct_checkBoxxxxx_21.isChecked():
            self.ctpg_tik_labels[i].setPos(self.ctpg_cvb[i].state['viewRange'][0][0], self.ctpg_cvb[i].state['viewRange'][1][0])
        if self.ct_checkBoxxxxx_22.isChecked():
            self.ctpg_tik_legend[i].setPos(self.ctpg_cvb[i].state['viewRange'][0][0], self.ctpg_cvb[i].state['viewRange'][1][1])
            self.ctpg_tik_legend[i].setText(self.GetLabelText(coin, self.ctpg_tik_arry, -1, self.ctpg_tik_factors[i], hms))

    @error_decorator
    def DrawRealJisuChart(self, data):
        if not self.dialog_jisu.isVisible():
            return

        gubun, xticks, ydatas = data
        if gubun == ui_num['코스피']:
            if 40 not in self.ctpg_tik_item.keys():
                self.ctpg_tik_item[40] = self.jspg[1].plot(x=xticks, y=ydatas, pen=(255, 0, 0))
                self.jspg[1].enableAutoRange()
            else:
                self.ctpg_tik_item[40].setData(x=xticks, y=ydatas)
        elif gubun == ui_num['코스닥']:
            if 41 not in self.ctpg_tik_item.keys():
                self.ctpg_tik_item[41] = self.jspg[2].plot(x=xticks, y=ydatas, pen=(0, 0, 255))
                self.jspg[2].enableAutoRange()
            else:
                self.ctpg_tik_item[41].setData(x=xticks, y=ydatas)

    @error_decorator
    def DrawTremap(self, data):
        if not self.dialog_tree.isVisible():
            webcQ.put(('트리맵중단', ''))
            return

        gubun, df1, df2, cl1, cl2 = data
        if gubun == ui_num['트리맵'] and self.tm_dt:
            return

        def mouse_press(event):
            if event.inaxes == self.tm_ax1 and self.df_tm1 is not None:
                if event.button == 1 and event.button != self.tm_mc1:
                    self.tm_mc1 = 1
                    df_ = self.df_tm1[(self.df_tm1['x'] < event.xdata) & (event.xdata < self.df_tm1['x2']) &
                                      (self.df_tm1['y'] < event.ydata) & (event.ydata < self.df_tm1['y2'])]
                    if len(df_) == 1:
                        self.tm_dt = True
                        url = df_['url'].iloc[0]
                        webcQ.put(('트리맵1', url))
                elif event.button == 3 and event.button != self.tm_mc1:
                    self.tm_mc1 = 3
                    self.tm_dt = False
                    self.tm_ax1.clear()
                    self.tm_ax1.axis('off')
                    squarify.plot(sizes=self.df_tm1['등락율'], label=self.df_tm1['업종명'], alpha=.9,
                                  value=self.df_tm1['등락율%'], color=self.tm_cl1, ax=self.tm_ax1,
                                  bar_kwargs=dict(linewidth=1, edgecolor='#000000'))
                    self.canvas.figure.tight_layout()
                    self.canvas.mpl_connect('button_press_event', mouse_press)
                    self.canvas.draw()
            elif event.inaxes == self.tm_ax2 and self.df_tm2 is not None:
                if event.button == 1 and event.button != self.tm_mc2:
                    self.tm_mc2 = 1
                    df_ = self.df_tm2[(self.df_tm2['x'] < event.xdata) & (event.xdata < self.df_tm2['x2']) &
                                      (self.df_tm2['y'] < event.ydata) & (event.ydata < self.df_tm2['y2'])]
                    if len(df_) == 1:
                        self.tm_dt = True
                        url = df_['url'].iloc[0]
                        webcQ.put(('트리맵2', url))
                elif event.button == 3 and event.button != self.tm_mc2:
                    self.tm_mc2 = 3
                    self.tm_dt = False
                    self.tm_ax2.clear()
                    self.tm_ax2.axis('off')
                    squarify.plot(sizes=self.df_tm2['등락율'], label=self.df_tm2['테마명'], alpha=.9,
                                  value=self.df_tm2['등락율%'], color=self.tm_cl2, ax=self.tm_ax2,
                                  bar_kwargs=dict(linewidth=1, edgecolor='#000000'))
                    self.canvas.figure.tight_layout()
                    self.canvas.mpl_connect('button_press_event', mouse_press)
                    self.canvas.draw()

        if gubun == ui_num['트리맵']:
            self.df_tm1 = df1
            self.df_tm2 = df2
            self.tm_cl1 = cl1
            self.tm_cl2 = cl2

            normed = squarify.normalize_sizes(self.df_tm1['등락율'], 100, 100)
            rects = squarify.squarify(normed, 0, 0, 100, 100)
            self.df_tm1['x']  = [rect["x"] for rect in rects]
            self.df_tm1['y']  = [rect["y"] for rect in rects]
            self.df_tm1['dx'] = [rect["dx"] for rect in rects]
            self.df_tm1['dy'] = [rect["dy"] for rect in rects]
            self.df_tm1['x2'] = self.df_tm1['x'] + self.df_tm1['dx']
            self.df_tm1['y2'] = self.df_tm1['y'] + self.df_tm1['dy']

            normed = squarify.normalize_sizes(self.df_tm2['등락율'], 100, 100)
            rects = squarify.squarify(normed, 0, 0, 100, 100)
            self.df_tm2['x']  = [rect["x"] for rect in rects]
            self.df_tm2['y']  = [rect["y"] for rect in rects]
            self.df_tm2['dx'] = [rect["dx"] for rect in rects]
            self.df_tm2['dy'] = [rect["dy"] for rect in rects]
            self.df_tm2['x2'] = self.df_tm2['x'] + self.df_tm2['dx']
            self.df_tm2['y2'] = self.df_tm2['y'] + self.df_tm2['dy']

            if self.tm_ax1 is None:
                self.tm_ax1 = self.canvas.figure.add_subplot(211)
                self.tm_ax2 = self.canvas.figure.add_subplot(212)
            else:
                self.tm_ax1.clear()
                self.tm_ax2.clear()
            self.tm_ax1.axis('off')
            self.tm_ax2.axis('off')
            squarify.plot(sizes=self.df_tm1['등락율'], label=self.df_tm1['업종명'], alpha=.9, value=self.df_tm1['등락율%'],
                          color=self.tm_cl1, ax=self.tm_ax1, bar_kwargs=dict(linewidth=1, edgecolor='#000000'))
            squarify.plot(sizes=self.df_tm2['등락율'], label=self.df_tm2['테마명'], alpha=.9, value=self.df_tm2['등락율%'],
                          color=self.tm_cl2, ax=self.tm_ax2, bar_kwargs=dict(linewidth=1, edgecolor='#000000'))
        elif gubun == ui_num['트리맵1']:
            self.tm_ax1.clear()
            self.tm_ax1.axis('off')
            squarify.plot(sizes=df1['등락율'], label=df1['종목명'], alpha=.9, value=df1['등락율%'],
                          color=cl1, ax=self.tm_ax1, bar_kwargs=dict(linewidth=1, edgecolor='#000000'))
        elif gubun == ui_num['트리맵2']:
            self.tm_ax2.clear()
            self.tm_ax2.axis('off')
            squarify.plot(sizes=df2['등락율'], label=df2['종목명'], alpha=.9, value=df2['등락율%'],
                          color=cl2, ax=self.tm_ax2, bar_kwargs=dict(linewidth=1, edgecolor='#000000'))

        self.canvas.figure.tight_layout()
        self.canvas.mpl_connect('button_press_event', mouse_press)
        self.canvas.draw()

    @error_decorator
    def DrawChartDayMin(self, data):
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
                label.setPos(-0.25, self.ctpg_day_ymin if gubun_ == '일봉' else self.ctpg_min_ymin)
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
                        if (self.ctpg_day_ymin if gubun_ == '일봉' else self.ctpg_min_ymin) > 100:
                            ytext = f'{mousePoint.y():,.0f}'
                        elif (self.ctpg_day_ymin if gubun_ == '일봉' else self.ctpg_min_ymin) > 10:
                            ytext = f'{mousePoint.y():,.2f}'
                        elif (self.ctpg_day_ymin if gubun_ == '일봉' else self.ctpg_min_ymin) > 1:
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
                            label.setPos(last - 1 + 0.25, self.ctpg_day_ymin if gubun_ == '일봉' else self.ctpg_min_ymin)
                        else:
                            label.setAnchor((0, 1))
                            label.setPos(-0.25, self.ctpg_day_ymin if gubun_ == '일봉' else self.ctpg_min_ymin)
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
            self.ctpg_day_ymin = min(arry[:, 1:5].min(), arry[:, 6:].min())
            self.ctpg_day_ymax = max(arry[:, 1:5].max(), arry[:, 6:].max())
        else:
            self.ctpg_min_ymin = min(arry[:, 1:5].min(), arry[:, 6:].min())
            self.ctpg_min_ymax = max(arry[:, 1:5].max(), arry[:, 6:].max())

        if gubun == ui_num['일봉차트']:
            if not self.dialog_chart_day.isVisible():
                return
            if self.ctpg_day_name != name or self.ctpg_day_index != arry[-1, 0]:
                self.ctpg_day[1].clear()
                self.ctpg_day[2].clear()
                self.ctpg_day[1].addItem(MoveavgItem(arry))
                self.ctpg_day[1].addItem(CandlestickItem(arry))
                self.ctpg_day_lastmoveavg = MoveavgItem(arry, last=True)
                self.ctpg_day_lastcandle  = CandlestickItem(arry, last=True)
                self.ctpg_day[1].addItem(self.ctpg_day_lastmoveavg)
                self.ctpg_day[1].addItem(self.ctpg_day_lastcandle)
                self.ctpg_day_infiniteline = pg.InfiniteLine(angle=0)
                self.ctpg_day_infiniteline.setPen(pg.mkPen(color_cs_hr))
                self.ctpg_day_infiniteline.setPos(c)
                self.ctpg_day[1].addItem(self.ctpg_day_infiniteline)
                xticks = list(arry[:, 0])
                xticks = [f'{str(x)[4:6]}-{str(x)[6:8]}' for x in xticks]
                xticks = [list(zip(range(len(xticks))[::12], xticks[::12]))]
                self.ctpg_day[1].getAxis('bottom').setTicks(xticks)
                self.ctpg_day[2].addItem(VolumeBarsItem(arry))
                self.ctpg_day_lastmoneybar = VolumeBarsItem(arry, last=True)
                self.ctpg_day[2].addItem(self.ctpg_day_lastmoneybar)
                self.ctpg_day[2].getAxis('bottom').setLabel(text=name)
                self.ctpg_day[2].getAxis('bottom').setTicks(xticks)
                crosshair(coin, '일봉', main_pg=self.ctpg_day[1], sub_pg=self.ctpg_day[2])
                self.ctpg_day_legend1 = pg.TextItem(color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                self.ctpg_day_legend1.setFont(qfont12)
                self.ctpg_day_legend1.setPos(-0.25, self.ctpg_day_ymax)
                self.ctpg_day_legend1.setText(getMainLegendText(coin))
                self.ctpg_day[1].addItem(self.ctpg_day_legend1)
                self.ctpg_day_legend2 = pg.TextItem(color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                self.ctpg_day_legend2.setFont(qfont12)
                self.ctpg_day_legend2.setPos(-0.25, vmax)
                self.ctpg_day_legend2.setText(getSubLegendText())
                self.ctpg_day[2].addItem(self.ctpg_day_legend2)
                # noinspection PyUnboundLocalVariable
                self.ctpg_cvb[16].set_range(0, x, self.ctpg_day_ymin, self.ctpg_day_ymax)
                # noinspection PyUnboundLocalVariable
                self.ctpg_day[1].setRange(xRange=(0, x), yRange=(self.ctpg_day_ymin, self.ctpg_day_ymax))
                self.ctpg_day[2].enableAutoRange(enable=True)
                self.ctpg_day_name  = name
                self.ctpg_day_index = arry[-1, 0]
            else:
                self.ctpg_day[1].removeItem(self.ctpg_day_lastmoveavg)
                self.ctpg_day[1].removeItem(self.ctpg_day_lastcandle)
                self.ctpg_day_lastmoveavg = MoveavgItem(arry, last=True)
                self.ctpg_day_lastcandle  = CandlestickItem(arry, last=True)
                self.ctpg_day[1].addItem(self.ctpg_day_lastmoveavg)
                self.ctpg_day[1].addItem(self.ctpg_day_lastcandle)
                self.ctpg_day_infiniteline.setPos(c)
                self.ctpg_day_legend1.setText(getMainLegendText(coin))
                self.ctpg_day[2].removeItem(self.ctpg_day_lastmoneybar)
                self.ctpg_day_lastmoneybar = VolumeBarsItem(arry, last=True)
                self.ctpg_day[2].addItem(self.ctpg_day_lastmoneybar)
                self.ctpg_day_legend2.setText(getSubLegendText())
        else:
            if not self.dialog_chart_min.isVisible():
                return
            if self.ctpg_min_name != name or self.ctpg_min_index != arry[-1, 0]:
                self.ctpg_min[1].clear()
                self.ctpg_min[2].clear()
                self.ctpg_min[1].addItem(MoveavgItem(arry))
                self.ctpg_min[1].addItem(CandlestickItem(arry))
                self.ctpg_min_lastmoveavg = MoveavgItem(arry, last=True)
                self.ctpg_min_lastcandle  = CandlestickItem(arry, last=True)
                self.ctpg_min[1].addItem(self.ctpg_min_lastmoveavg)
                self.ctpg_min[1].addItem(self.ctpg_min_lastcandle)
                self.ctpg_min_infiniteline = pg.InfiniteLine(angle=0)
                self.ctpg_min_infiniteline.setPen(pg.mkPen(color_cs_hr))
                self.ctpg_min_infiniteline.setPos(c)
                self.ctpg_min[1].addItem(self.ctpg_min_infiniteline)
                xticks = list(arry[:, 0])
                xticks = [f'{str(x)[8:10]}:{str(x)[10:12]}' for x in xticks]
                xticks = [list(zip(range(len(xticks))[::12], xticks[::12]))]
                self.ctpg_min[1].getAxis('bottom').setTicks(xticks)
                self.ctpg_min[2].addItem(VolumeBarsItem(arry))
                self.ctpg_min_lastmoneybar = VolumeBarsItem(arry, last=True)
                self.ctpg_min[2].addItem(self.ctpg_min_lastmoneybar)
                self.ctpg_min[2].getAxis('bottom').setLabel(text=name)
                self.ctpg_min[2].getAxis('bottom').setTicks(xticks)
                crosshair(coin, '분봉', main_pg=self.ctpg_min[1], sub_pg=self.ctpg_min[2])
                self.ctpg_min_legend1 = pg.TextItem(color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                self.ctpg_min_legend1.setFont(qfont12)
                self.ctpg_min_legend1.setPos(-0.25, self.ctpg_min_ymax)
                self.ctpg_min_legend1.setText(getMainLegendText(coin))
                self.ctpg_min[1].addItem(self.ctpg_min_legend1)
                self.ctpg_min_legend2 = pg.TextItem(color=color_fg_bt, border=color_bg_bt, fill=color_bg_ld)
                self.ctpg_min_legend2.setFont(qfont12)
                self.ctpg_min_legend2.setPos(-0.25, vmax)
                self.ctpg_min_legend2.setText(getSubLegendText())
                self.ctpg_min[2].addItem(self.ctpg_min_legend2)
                # noinspection PyUnboundLocalVariable
                self.ctpg_cvb[17].set_range(0, x, self.ctpg_min_ymin, self.ctpg_min_ymax)
                # noinspection PyUnboundLocalVariable
                self.ctpg_min[1].setRange(xRange=(0, x), yRange=(self.ctpg_min_ymin, self.ctpg_min_ymax))
                self.ctpg_min[2].enableAutoRange(enable=True)
                self.ctpg_min_name  = name
                self.ctpg_min_index = arry[-1, 0]
            else:
                self.ctpg_min[1].removeItem(self.ctpg_min_lastmoveavg)
                self.ctpg_min[1].removeItem(self.ctpg_min_lastcandle)
                self.ctpg_min_lastmoveavg = MoveavgItem(arry, last=True)
                self.ctpg_min_lastcandle  = CandlestickItem(arry, last=True)
                self.ctpg_min[1].addItem(self.ctpg_min_lastmoveavg)
                self.ctpg_min[1].addItem(self.ctpg_min_lastcandle)
                self.ctpg_min_infiniteline.setPos(c)
                self.ctpg_min_legend1.setText(getMainLegendText(coin))
                self.ctpg_min[2].removeItem(self.ctpg_min_lastmoneybar)
                self.ctpg_min_lastmoneybar = VolumeBarsItem(arry, last=True)
                self.ctpg_min[2].addItem(self.ctpg_min_lastmoneybar)
                self.ctpg_min_legend2.setText(getSubLegendText())

    # =================================================================================================================

    def CheckboxChanged_01(self, state):
        if type(self.focusWidget()) != QPushButton:
            if state == Qt.Checked:
                con = sqlite3.connect(DB_SETTING)
                df = pd.read_sql('SELECT * FROM sacc', con).set_index('index')
                con.close()
                if len(df) == 0 or df['아이디2'][0] == '':
                    self.sj_main_cheBox_01.nextCheckState()
                    QMessageBox.critical(self, '오류 알림', '두번째 계정이 설정되지 않아\n리시버를 선택할 수 없습니다.\n계정 설정 후 다시 선택하십시오.\n')
                elif not self.sj_main_cheBox_02.isChecked():
                    self.sj_main_cheBox_02.nextCheckState()
            else:
                if self.sj_main_cheBox_02.isChecked():
                    self.sj_main_cheBox_02.nextCheckState()

    def CheckboxChanged_02(self, state):
        if type(self.focusWidget()) != QPushButton:
            if state == Qt.Checked:
                con = sqlite3.connect(DB_SETTING)
                df = pd.read_sql('SELECT * FROM sacc', con).set_index('index')
                con.close()
                if len(df) == 0 or df['아이디1'][0] == '':
                    self.sj_main_cheBox_02.nextCheckState()
                    QMessageBox.critical(self, '오류 알림', '첫번째 계정이 설정되지 않아\n트레이더를 선택할 수 없습니다.\n계정 설정 후 다시 선택하십시오.\n')
                elif not self.sj_main_cheBox_01.isChecked():
                    self.sj_main_cheBox_01.nextCheckState()
            else:
                if self.sj_main_cheBox_01.isChecked():
                    self.sj_main_cheBox_01.nextCheckState()

    def CheckboxChanged_03(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            if self.sj_main_cheBox_11.isChecked():
                self.sj_main_cheBox_03.nextCheckState()
                QMessageBox.critical(self, '오류 알림', '클라이언트용 스톰은\n틱데이터를 저장할 수 없습니다.\n서버용 스톰으로 저장하십시오.\n')
            else:
                if not self.sj_main_cheBox_01.isChecked():
                    self.sj_main_cheBox_01.nextCheckState()
                if not self.sj_main_cheBox_02.isChecked():
                    self.sj_main_cheBox_02.nextCheckState()

    def CheckboxChanged_04(self, state):
        if type(self.focusWidget()) != QPushButton:
            if state == Qt.Checked:
                if not self.sj_main_cheBox_05.isChecked():
                    self.sj_main_cheBox_05.nextCheckState()
            else:
                if self.sj_main_cheBox_05.isChecked():
                    self.sj_main_cheBox_05.nextCheckState()

    def CheckboxChanged_05(self, state):
        if type(self.focusWidget()) != QPushButton:
            if state == Qt.Checked:
                if not self.sj_main_cheBox_04.isChecked():
                    self.sj_main_cheBox_04.nextCheckState()
            else:
                if self.sj_main_cheBox_04.isChecked():
                    self.sj_main_cheBox_04.nextCheckState()

    def CheckboxChanged_06(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            if self.sj_main_cheBox_11.isChecked():
                self.sj_main_cheBox_03.nextCheckState()
                QMessageBox.critical(self, '오류 알림', '클라이언트용 스톰은\n틱데이터를 저장할 수 없습니다.\n서버용 스톰으로 저장하십시오.\n')
            else:
                if not self.sj_main_cheBox_04.isChecked():
                    self.sj_main_cheBox_04.nextCheckState()
                if not self.sj_main_cheBox_05.isChecked():
                    self.sj_main_cheBox_05.nextCheckState()

    def CheckboxChanged_07(self, state):
        if type(self.focusWidget()) != QPushButton and state != Qt.Checked:
            buttonReply = QMessageBox.question(
                self, '경고', '트레이더 실행 중에 모의모드를 해제하면\n바로 실매매로 전환됩니다. 해제하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply != QMessageBox.Yes:
                self.sj_stock_ckBox_01.nextCheckState()

    def CheckboxChanged_08(self, state):
        if type(self.focusWidget()) != QPushButton and state != Qt.Checked and self.CoinTraderProcessAlive():
            self.sj_coin_cheBox_01.nextCheckState()
            QMessageBox.critical(self, '오류 알림', '트레이더 실행 중에는 모의모드를 해제할 수 없습니다.\n')

    def CheckboxChanged_09(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.sproc_exit_listtt:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    def CheckboxChanged_10(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.cproc_exit_listtt:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    def CheckboxChanged_11(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            if self.sj_back_cheBox_08.isChecked():
                QMessageBox.critical(self, '오류 알림', '일봉데이터 자동다운로드 시는 선택할 수 없습니다.\n')
                self.focusWidget().nextCheckState()
                return
            for widget in self.com_exit_list:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    def CheckboxChanged_12(self, state):
        if type(self.focusWidget()) != QPushButton and state != Qt.Checked:
            if self.dialog_factor.focusWidget() == self.ct_checkBoxxxxx_01:
                self.ct_checkBoxxxxx_01.nextCheckState()
                QMessageBox.critical(self.dialog_factor, '오류 알림', '현재가는 해제할 수 없습니다.\n')

    def CheckboxChanged_13(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.sj_ilbunback_listtt:
                if widget != self.focusWidget() and widget.isChecked():
                    widget.nextCheckState()

    def CheckboxChanged_14(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            if not self.sj_back_cheBox_14.isChecked():
                self.sj_back_cheBox_14.nextCheckState()

    def CheckboxChanged_141(self, state):
        if type(self.focusWidget()) != QPushButton and state != Qt.Checked:
            if self.sj_back_cheBox_13.isChecked():
                self.sj_back_cheBox_13.nextCheckState()

    def CheckboxChanged_15(self, state):
        if type(self.focusWidget()) != QPushButton and state != Qt.Checked:
            if self.sj_back_cheBox_06.isChecked():
                self.sj_back_cheBox_06.nextCheckState()

    def CheckboxChanged_16(self, state):
        gubun = self.list_checkBoxxxxxx.index(self.dialog_scheduler.focusWidget())
        if state == Qt.Checked:
            for item in ('백테스트',
                         '그리드 최적화', '그리드 검증 최적화', '그리드 교차검증 최적화',
                         '그리드 최적화 테스트', '그리드 검증 최적화 테스트', '그리드 교차검증 최적화 테스트',
                         '그리드 최적화 전진분석', '그리드 검증 최적화 전진분석', '그리드 교차검증 최적화 전진분석',
                         '베이지안 최적화', '베이지안 검증 최적화', '베이지안 교차검증 최적화',
                         '베이지안 최적화 테스트', '베이지안 검증 최적화 테스트', '베이지안 교차검증 최적화 테스트',
                         '베이지안 최적화 전진분석', '베이지안 검증 최적화 전진분석', '베이지안 교차검증 최적화 전진분석',
                         'GA 최적화', '검증 GA 최적화', '교차검증 GA 최적화',
                         '조건 최적화', '검증 조건 최적화', '교차검증 조건 최적화'):
                self.list_gcomboBoxxxxx[gubun].addItem(item)
        else:
            self.list_gcomboBoxxxxx[gubun].clear()
            self.list_bcomboBoxxxxx[gubun].clear()
            self.list_scomboBoxxxxx[gubun].clear()
            self.list_vcomboBoxxxxx[gubun].clear()
            self.list_p1comboBoxxxx[gubun].clear()
            self.list_p2comboBoxxxx[gubun].clear()
            self.list_p3comboBoxxxx[gubun].clear()
            self.list_p4comboBoxxxx[gubun].clear()
            self.list_tcomboBoxxxxx[gubun].clear()

    def CheckboxChanged_17(self, state):
        if type(self.focusWidget()) != QPushButton:
            if state == Qt.Checked:
                if self.sj_back_cheBox_18.isChecked():
                    self.sj_back_cheBox_18.nextCheckState()
            else:
                if not self.sj_back_cheBox_18.isChecked():
                    self.sj_back_cheBox_18.nextCheckState()

    def CheckboxChanged_18(self, state):
        if type(self.focusWidget()) != QPushButton:
            if state == Qt.Checked:
                if self.sj_back_cheBox_17.isChecked():
                    self.sj_back_cheBox_17.nextCheckState()
            else:
                if not self.sj_back_cheBox_17.isChecked():
                    self.sj_back_cheBox_17.nextCheckState()

    def CheckboxChanged_19(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.sj_checkbox_list:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    def CheckboxChanged_20(self, state):
        if type(self.focusWidget()) != QPushButton:
            if state == Qt.Checked:
                if self.focusWidget() == self.sj_main_cheBox_10:
                    if self.sj_main_cheBox_11.isChecked():
                        self.sj_main_cheBox_11.nextCheckState()
                else:
                    if self.sj_main_cheBox_10.isChecked():
                        self.sj_main_cheBox_10.nextCheckState()
            elif not self.sj_main_cheBox_11.isChecked() and not self.sj_main_cheBox_10.isChecked() and not self.sj_main_cheBox_09.isChecked():
                self.sj_main_cheBox_09.nextCheckState()

    def CheckboxChanged_21(self, state):
        if type(self.focusWidget()) != QPushButton and state != Qt.Checked:
            if self.focusWidget() == self.sj_main_cheBox_09:
                if not self.sj_main_cheBox_11.isChecked() and not self.sj_main_cheBox_10.isChecked():
                    self.sj_main_cheBox_09.nextCheckState()

    # noinspection PyUnusedLocal
    def CheckboxChanged_22(self, state):
        self.ctpg_tik_name = None

    # =================================================================================================================

    def sbCheckboxChanged_01(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.sodb_checkbox_list1:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    def sbCheckboxChanged_02(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.sodb_checkbox_list2:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    def ssCheckboxChanged_01(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.sods_checkbox_list1:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    def ssCheckboxChanged_02(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.sods_checkbox_list2:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    # =================================================================================================================

    def cbCheckboxChanged_01(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.codb_checkbox_list1:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()
        if self.dict_set['거래소'] == '업비트':
            if self.sj_codb_checkBox_19.isChecked() or self.sj_codb_checkBox_20.isChecked():
                if self.sj_codb_checkBox_19.isChecked():
                    self.sj_codb_checkBox_19.nextCheckState()
                else:
                    self.sj_codb_checkBox_20.nextCheckState()
                QMessageBox.critical(self, '오류 알림', '업비트는 해당주문유형을 사용할 수 없습니다.\n')
                self.sj_codb_checkBox_01.setFocus()
                self.sj_codb_checkBox_01.setChecked(True)

    def cbCheckboxChanged_02(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.codb_checkbox_list2:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    def csCheckboxChanged_01(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.cods_checkbox_list1:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()
        if self.dict_set['거래소'] == '업비트':
            if self.sj_cods_checkBox_19.isChecked() or self.sj_cods_checkBox_20.isChecked():
                if self.sj_cods_checkBox_19.isChecked():
                    self.sj_codb_checkBox_19.nextCheckState()
                else:
                    self.sj_cods_checkBox_20.nextCheckState()
                QMessageBox.critical(self, '오류 알림', '업비트는 해당주문유형을 사용할 수 없습니다.\n')
                self.sj_cods_checkBox_01.setFocus()
                self.sj_cods_checkBox_01.setChecked(True)

    def csCheckboxChanged_02(self, state):
        if type(self.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.cods_checkbox_list2:
                if widget != self.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    @staticmethod
    def opButtonClicked_01():
        RunOptunaServer()
        qtest_qwait(3)
        webbrowser.open_new('http://localhost:8080/')

    # =================================================================================================================

    @pyqtSlot(int, int)
    def CellClicked_01(self, row, col):
        stock = True
        tableWidget = None
        if self.focusWidget() == self.std_tableWidgettt:
            tableWidget = self.std_tableWidgettt
        elif self.focusWidget() == self.sgj_tableWidgettt:
            tableWidget = self.sgj_tableWidgettt
        elif self.focusWidget() == self.scj_tableWidgettt:
            tableWidget = self.scj_tableWidgettt
        elif self.focusWidget() == self.ctd_tableWidgettt:
            stock = False
            tableWidget = self.ctd_tableWidgettt
        elif self.focusWidget() == self.cgj_tableWidgettt:
            stock = False
            tableWidget = self.cgj_tableWidgettt
        elif self.focusWidget() == self.ccj_tableWidgettt:
            stock = False
            tableWidget = self.ccj_tableWidgettt
        if tableWidget is None:
            return
        item = tableWidget.item(row, 0)
        if item is None:
            return
        name = item.text()
        linetext = self.ct_lineEdittttt_03.text()
        tickcount = int(linetext) if linetext != '' else 30
        searchdate = strf_time('%Y%m%d') if stock else strf_time('%Y%m%d', timedelta_sec(-32400))
        code = self.dict_code[name] if name in self.dict_code.keys() else name
        self.ct_lineEdittttt_04.setText(code)
        self.ct_lineEdittttt_05.setText(name)
        self.ShowDialog(name, tickcount, searchdate, col)

    @pyqtSlot(int)
    def CellClicked_02(self, row):
        item = self.sjg_tableWidgettt.item(row, 0)
        if item is None:
            return
        name = item.text()
        oc = comma2int(self.sjg_tableWidgettt.item(row, columns_jg.index('보유수량')).text())
        c = comma2int(self.sjg_tableWidgettt.item(row, columns_jg.index('현재가')).text())
        buttonReply = QMessageBox.question(
            self, '주식 시장가 매도', f'{name} {oc}주를 시장가매도합니다.\n계속하시겠습니까?\n',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if buttonReply == QMessageBox.Yes:
            wdzservQ.put(('trader', ('매도', self.dict_code[name], name, c, oc, now(), True)))

    @pyqtSlot(int)
    def CellClicked_03(self, row):
        item = self.cjg_tableWidgettt.item(row, 0)
        if item is None:
            return
        code    = item.text()
        columns = columns_jg if 'KRW' in code else columns_jgf
        oc      = comma2float(self.cjg_tableWidgettt.item(row, columns.index('보유수량')).text())
        c       = comma2float(self.cjg_tableWidgettt.item(row, columns.index('현재가')).text())
        buttonReply = QMessageBox.question(
            self, '코인 시장가 매도', f'{code} {oc}개를 시장가매도합니다.\n계속하시겠습니까?\n',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if buttonReply == QMessageBox.Yes:
            if self.CoinTraderProcessAlive():
                if 'KRW' in code:
                    ctraderQ.put(('매도', code, c, oc, now(), True))
                else:
                    p = self.cjg_tableWidgettt.item(row, columns_jgf.index('포지션')).text()
                    p = 'SELL_LONG' if p == 'LONG' else 'BUY_SHORT'
                    ctraderQ.put((p, code, c, oc, now(), True))

    @pyqtSlot(int)
    def CellClicked_04(self, row):
        tableWidget = None
        searchdate  = ''
        if self.focusWidget() == self.sds_tableWidgettt:
            tableWidget = self.sds_tableWidgettt
            searchdate  = self.s_calendarWidgett.selectedDate().toString('yyyyMMdd')
        elif self.focusWidget() == self.cds_tableWidgettt:
            tableWidget = self.cds_tableWidgettt
            searchdate  = self.c_calendarWidgett.selectedDate().toString('yyyyMMdd')
        if tableWidget is None:
            return
        item = tableWidget.item(row, 1)
        if item is None:
            return
        name      = item.text()
        linetext  = self.ct_lineEdittttt_03.text()
        tickcount = int(linetext) if linetext != '' else 30
        code      = self.dict_code[name] if name in self.dict_code.keys() else name
        self.ct_lineEdittttt_04.setText(code)
        self.ct_lineEdittttt_05.setText(name)
        self.ct_dateEdittttt_01.setDate(QDate.fromString(searchdate, 'yyyyMMdd'))
        self.ShowDialog(name, tickcount, searchdate, 4)

    @pyqtSlot(int)
    def CellClicked_05(self, row):
        tableWidget = None
        gubun = '주식'
        if self.focusWidget() == self.sns_tableWidgettt:
            tableWidget = self.sns_tableWidgettt
        elif self.focusWidget() == self.cns_tableWidgettt:
            tableWidget = self.cns_tableWidgettt
            gubun = '코인'
        if tableWidget is None:
            return
        item = tableWidget.item(row, 0)
        if item is None:
            return
        date = item.text()
        date = date.replace('.', '')
        table_name = 's_tradelist' if gubun == '주식' else 'c_tradelist' if self.dict_set['거래소'] == '업비트' else 'c_tradelist_future'

        con = sqlite3.connect(DB_TRADELIST)
        df = pd.read_sql(f"SELECT * FROM {table_name} WHERE 체결시간 LIKE '{date}%'", con)
        con.close()

        if len(date) == 6 and gubun == '코인':
            df['구분용체결시간'] = df['체결시간'].apply(lambda x: x[:6])
            df = df[df['구분용체결시간'] == date]
        elif len(date) == 4 and gubun == '코인':
            df['구분용체결시간'] = df['체결시간'].apply(lambda x: x[:4])
            df = df[df['구분용체결시간'] == date]

        df['index'] = df['index'].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:12]}:{x[12:14]}')
        df.set_index('index', inplace=True)
        self.ShowDialogGraph(df)

    @pyqtSlot(int)
    def CellClicked_06(self, row):
        tableWidget = None
        if self.focusWidget() == self.ss_tableWidget_01:
            tableWidget = self.ss_tableWidget_01
        elif self.focusWidget() == self.cs_tableWidget_01:
            tableWidget = self.cs_tableWidget_01
        if tableWidget is None:
            return
        item = tableWidget.item(row, 0)
        if item is None:
            return

        name       = item.text()
        searchdate = tableWidget.item(row, 2).text()[:8]
        buytime    = comma2int(tableWidget.item(row, 2).text())
        selltime   = comma2int(tableWidget.item(row, 3).text())
        buyprice   = comma2float(tableWidget.item(row, 5).text())
        sellprice  = comma2float(tableWidget.item(row, 6).text())
        detail     = [buytime, buyprice, selltime, sellprice]
        buytimes   = tableWidget.item(row, 13).text()

        coin = True if 'KRW' in name or 'USDT' in name else False
        code = self.dict_code[name] if name in self.dict_code.keys() else name
        self.ct_lineEdittttt_04.setText(code)
        self.ct_lineEdittttt_05.setText(name)
        self.ct_dateEdittttt_01.setDate(QDate.fromString(searchdate, 'yyyyMMdd'))
        tickcount = int(self.cvjb_lineEditt_05.text()) if coin else int(self.svjb_lineEditt_05.text())
        self.ShowDialogChart(False, coin, code, tickcount, searchdate, self.ct_lineEdittttt_01.text(), self.ct_lineEdittttt_02.text(), detail, buytimes)

    @pyqtSlot(int)
    def CellClicked_07(self, row):
        item = self.ct_tableWidgett_01.item(row, 0)
        if item is None:
            return
        name = item.text()
        coin = True if 'KRW' in name or 'USDT' in name else False
        code = self.dict_code[name] if name in self.dict_code.keys() else name
        searchdate = self.ct_dateEdittttt_02.date().toString('yyyyMMdd')
        linetext = self.ct_lineEdittttt_03.text()
        tickcount = int(linetext) if linetext != '' else 30
        self.ct_lineEdittttt_04.setText(code)
        self.ct_lineEdittttt_05.setText(name)
        self.ct_dateEdittttt_01.setDate(QDate.fromString(searchdate, 'yyyyMMdd'))
        chartQ.put((coin, code, tickcount, searchdate, self.ct_lineEdittttt_01.text(), self.ct_lineEdittttt_02.text()))

    @pyqtSlot(int)
    def CellClicked_08(self, row):
        tableWidget = None
        if self.dialog_info.focusWidget() == self.gs_tableWidgett_01:
            tableWidget = self.gs_tableWidgett_01
        elif self.dialog_info.focusWidget() == self.ns_tableWidgett_01:
            tableWidget = self.ns_tableWidgett_01
        if tableWidget is None:
            return
        item = tableWidget.item(row, 3)
        if item is None:
            return
        if self.dialog_web.isVisible():
            self.webEngineView.load(QUrl(item.text()))

    @pyqtSlot(int, int)
    def CellClicked_09(self, row, col):
        if self.dialog_db.focusWidget() == self.db_tableWidgett_01:
            item = self.db_tableWidgett_01.item(row, col)
            if item is None:
                return
            stg_name = item.text()
            buttonReply = QMessageBox.question(
                self.dialog_db, '전략 삭제', f'주식전략 "{stg_name}"을(를) 삭제합니다.\n계속하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                con = sqlite3.connect(DB_STRATEGY)
                cur = con.cursor()
                if col == 0:
                    query = f'DELETE FROM stockbuy WHERE "index" = "{stg_name}"'
                elif col == 1:
                    query = f'DELETE FROM stocksell WHERE "index" = "{stg_name}"'
                elif col == 2:
                    query = f'DELETE FROM stockoptibuy WHERE "index" = "{stg_name}"'
                else:
                    query = f'DELETE FROM stockoptisell WHERE "index" = "{stg_name}"'
                cur.execute(query)
                con.commit()
                con.close()
                windowQ.put((ui_num['DB관리'], f'DB 명령 실행 알림 - 주식전략 "{stg_name}" 삭제 완료'))
        elif self.dialog_db.focusWidget() == self.db_tableWidgett_02:
            item = self.db_tableWidgett_02.item(row, col)
            if item is None:
                return
            stg_name = item.text()
            buttonReply = QMessageBox.question(
                self.dialog_db, '범위 또는 조건 삭제', f'주식 범위 또는 조건 "{stg_name}"을(를) 삭제합니다.\n계속하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                con = sqlite3.connect(DB_STRATEGY)
                cur = con.cursor()
                if col == 0:
                    query = f'DELETE FROM stockoptivars WHERE "index" = "{stg_name}"'
                elif col == 1:
                    query = f'DELETE FROM stockvars WHERE "index" = "{stg_name}"'
                elif col == 2:
                    query = f'DELETE FROM stockbuyconds WHERE "index" = "{stg_name}"'
                else:
                    query = f'DELETE FROM stocksellconds WHERE "index" = "{stg_name}"'
                cur.execute(query)
                con.commit()
                con.close()
                windowQ.put((ui_num['DB관리'], f'DB 명령 실행 알림 - 주식 범위 또는 조건 "{stg_name}" 삭제 완료'))
        elif self.dialog_db.focusWidget() == self.db_tableWidgett_03:
            item = self.db_tableWidgett_03.item(row, col)
            if item is None:
                return
            stg_name = item.text()
            buttonReply = QMessageBox.question(
                self.dialog_db, '전략 삭제', f'코인전략 "{stg_name}"을(를) 삭제합니다.\n계속하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                con = sqlite3.connect(DB_STRATEGY)
                cur = con.cursor()
                if col == 0:
                    query = f'DELETE FROM coinbuy WHERE "index" = "{stg_name}"'
                elif col == 1:
                    query = f'DELETE FROM coinsell WHERE "index" = "{stg_name}"'
                elif col == 2:
                    query = f'DELETE FROM coinoptibuy WHERE "index" = "{stg_name}"'
                else:
                    query = f'DELETE FROM coinoptisell WHERE "index" = "{stg_name}"'
                cur.execute(query)
                con.commit()
                con.close()
                windowQ.put((ui_num['DB관리'], f'DB 명령 실행 알림 - 코인전략 "{stg_name}" 삭제 완료'))
        elif self.dialog_db.focusWidget() == self.db_tableWidgett_04:
            item = self.db_tableWidgett_04.item(row, col)
            if item is None:
                return
            stg_name = item.text()
            buttonReply = QMessageBox.question(
                self.dialog_db, '범위 또는 조건 삭제', f'코인 범위 또는 조건 "{stg_name}"을(를) 삭제합니다.\n계속하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                con = sqlite3.connect(DB_STRATEGY)
                cur = con.cursor()
                if col == 0:
                    query = f'DELETE FROM coinoptivars WHERE "index" = "{stg_name}"'
                elif col == 1:
                    query = f'DELETE FROM coinvars WHERE "index" = "{stg_name}"'
                elif col == 2:
                    query = f'DELETE FROM coinbuyconds WHERE "index" = "{stg_name}"'
                else:
                    query = f'DELETE FROM coinsellconds WHERE "index" = "{stg_name}"'
                cur.execute(query)
                con.commit()
                con.close()
                windowQ.put((ui_num['DB관리'], f'DB 명령 실행 알림 - 코인 범위 또는 조건 "{stg_name}" 삭제 완료'))
        elif self.dialog_db.focusWidget() == self.db_tableWidgett_05:
            item = self.db_tableWidgett_05.item(row, col)
            if item is None:
                return
            stg_name = item.text()
            buttonReply = QMessageBox.question(
                self.dialog_db, '스케쥴 삭제', f'스케쥴 "{stg_name}"을(를) 삭제합니다.\n계속하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                con = sqlite3.connect(DB_STRATEGY)
                cur = con.cursor()
                query = f'DELETE FROM schedule WHERE "index" = "{stg_name}"'
                cur.execute(query)
                con.commit()
                con.close()
                windowQ.put((ui_num['DB관리'], f'DB 명령 실행 알림 - 스케쥴 "{stg_name}" 삭제 완료'))

        self.ShowDB()

    @pyqtSlot(int, int)
    def CellClicked_10(self, row, col):
        item = self.hg_tableWidgett_01.item(row, col)
        if item is not None:
            text = item.text()
            if '.' in text:
                order_price = comma2float(text)
            else:
                order_price = comma2int(text)
            self.od_lineEdittttt_01.setText(str(order_price))
            self.TextChanged_05()

    def CellClicked_11(self):
        table_name = 's_tradelist' if self.focusWidget() == self.snt_tableWidgettt else 'c_tradelist' if self.dict_set['거래소'] == '업비트' else 'c_tradelist_future'
        con = sqlite3.connect(DB_TRADELIST)
        df = pd.read_sql(f"SELECT * FROM {table_name}", con)
        con.close()
        df['index'] = df['index'].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:12]}:{x[12:14]}')
        df.set_index('index', inplace=True)
        self.ShowDialogGraph(df)

    # =================================================================================================================

    def ReturnPress_01(self):
        if self.dialog_chart.focusWidget() in (self.ct_lineEdittttt_04, self.ct_lineEdittttt_05, self.ct_pushButtonnn_01):
            searchdate = self.ct_dateEdittttt_01.date().toString('yyyyMMdd')
            linetext = self.ct_lineEdittttt_03.text()
            tickcount = int(linetext) if linetext != '' else 30
            if self.dialog_chart.focusWidget() == self.ct_lineEdittttt_04:
                name = self.ct_lineEdittttt_04.text()
            else:
                name = self.ct_lineEdittttt_05.text()
            if name in self.dict_code.keys():
                code = self.dict_code[name]
            else:
                code = name
                name = self.dict_name[code] if code in self.dict_name.keys() else code
            self.ct_lineEdittttt_04.setText(code)
            self.ct_lineEdittttt_05.setText(name)
            self.ShowDialog(name, tickcount, searchdate, 4)
        elif self.dialog_chart.focusWidget() == self.ct_tableWidgett_01:
            row = self.ct_tableWidgett_01.currentIndex().row()
            item = self.ct_tableWidgett_01.item(row, 0)
            if item is None:
                return
            name = item.text()
            coin = True if 'KRW' in name or 'USDT' in name else False
            code = self.dict_code[name] if name in self.dict_code.keys() else name
            searchdate = self.ct_dateEdittttt_02.date().toString('yyyyMMdd')
            linetext = self.ct_lineEdittttt_03.text()
            tickcount = int(linetext) if linetext != '' else 30
            self.ct_lineEdittttt_04.setText(code)
            self.ct_lineEdittttt_05.setText(name)
            self.ct_dateEdittttt_01.setDate(QDate.fromString(searchdate, 'yyyyMMdd'))
            chartQ.put((coin, code, tickcount, searchdate, self.ct_lineEdittttt_01.text(), self.ct_lineEdittttt_02.text()))

    def ReturnPress_02(self):
        if self.pa_lineEditttt_01.text() == self.dict_set['계좌비밀번호1'] or \
                (self.pa_lineEditttt_01.text() == '' and self.dict_set['계좌비밀번호1'] is None):
            self.sj_sacc_liEdit_01.setEchoMode(QLineEdit.Normal)
            self.sj_sacc_liEdit_02.setEchoMode(QLineEdit.Normal)
            self.sj_sacc_liEdit_03.setEchoMode(QLineEdit.Normal)
            self.sj_sacc_liEdit_04.setEchoMode(QLineEdit.Normal)
            self.sj_sacc_liEdit_05.setEchoMode(QLineEdit.Normal)
            self.sj_sacc_liEdit_06.setEchoMode(QLineEdit.Normal)
            self.sj_sacc_liEdit_07.setEchoMode(QLineEdit.Normal)
            self.sj_sacc_liEdit_08.setEchoMode(QLineEdit.Normal)
            self.sj_cacc_liEdit_01.setEchoMode(QLineEdit.Normal)
            self.sj_cacc_liEdit_02.setEchoMode(QLineEdit.Normal)
            self.sj_tele_liEdit_01.setEchoMode(QLineEdit.Normal)
            self.sj_tele_liEdit_02.setEchoMode(QLineEdit.Normal)
            self.sj_etc_pButton_01.setText('계정 텍스트 가리기')
            self.sj_etc_pButton_01.setStyleSheet(style_bc_dk)
            self.dialog_pass.close()
        else:
            teleQ.put('경고!! 계정 텍스트 보기 비밀번호 입력 오류가 발생하였습니다.')

    # =================================================================================================================

    def TextChanged_01(self):
        if self.dialog_scheduler.focusWidget() not in self.list_slineEdittttt:
            return
        if self.sd_scheckBoxxxx_01.isChecked():
            gubun = self.list_slineEdittttt.index(self.dialog_scheduler.focusWidget())
            text  = self.list_slineEdittttt[gubun].text()
            for i, widget in enumerate(self.list_slineEdittttt):
                if i != gubun:
                    widget.setText(text)

    def TextChanged_02(self):
        if self.dialog_scheduler.focusWidget() not in self.list_elineEdittttt:
            return
        if self.sd_scheckBoxxxx_01.isChecked():
            gubun = self.list_elineEdittttt.index(self.dialog_scheduler.focusWidget())
            text  = self.list_elineEdittttt[gubun].text()
            for i, widget in enumerate(self.list_elineEdittttt):
                if i != gubun:
                    widget.setText(text)

    def TextChanged_03(self):
        if self.dialog_scheduler.focusWidget() not in self.list_blineEdittttt:
            return
        if self.sd_scheckBoxxxx_01.isChecked():
            gubun = self.list_blineEdittttt.index(self.dialog_scheduler.focusWidget())
            text  = self.list_blineEdittttt[gubun].text()
            for i, widget in enumerate(self.list_blineEdittttt):
                if i != gubun:
                    widget.setText(text)

    def TextChanged_04(self):
        if self.dialog_scheduler.focusWidget() not in self.list_alineEdittttt:
            return
        if self.sd_scheckBoxxxx_01.isChecked():
            gubun = self.list_alineEdittttt.index(self.dialog_scheduler.focusWidget())
            text  = self.list_alineEdittttt[gubun].text()
            for i, widget in enumerate(self.list_alineEdittttt):
                combo_text = self.list_gcomboBoxxxxx[i].currentText()
                if i != gubun and '최적화' not in combo_text and '전진분석' not in combo_text:
                    widget.setText(text)

    def TextChanged_05(self):
        name = self.od_comboBoxxxxx_01.currentText()
        if name != '':
            if 'KRW' in name:
                order_price = float(self.od_lineEdittttt_01.text())
                order_count = round(self.dict_set['코인장초투자금'] * 1_000_000 / order_price, 8)
            elif 'USDT' in name:
                order_price = float(self.od_lineEdittttt_01.text())
                order_count = round(self.dict_set['코인장초투자금'] / order_price, 8)
            else:
                order_price = int(self.od_lineEdittttt_01.text())
                order_count = int(self.dict_set['주식장초투자금'] * 1_000_000 / order_price)
            self.od_lineEdittttt_02.setText(str(order_count))

    # =================================================================================================================

    def ShowDialogGraph(self, df):
        if not self.dialog_graph.isVisible():
            self.dialog_graph.show()

        df['이익금액'] = df['수익금'].apply(lambda x: x if x >= 0 else 0)
        df['손실금액'] = df['수익금'].apply(lambda x: x if x < 0 else 0)
        df['수익금합계'] = df['수익금'].cumsum()
        df['수익금합계020'] = df['수익금합계'].rolling(window=20).mean().round(2)
        df['수익금합계060'] = df['수익금합계'].rolling(window=60).mean().round(2)
        df['수익금합계120'] = df['수익금합계'].rolling(window=120).mean().round(2)
        df['수익금합계240'] = df['수익금합계'].rolling(window=240).mean().round(2)
        df['수익금합계480'] = df['수익금합계'].rolling(window=480).mean().round(2)

        self.canvas2.figure.clear()
        ax = self.canvas2.figure.add_subplot(111)
        ax.bar(df.index, df['이익금액'], label='이익금액', color='r')
        ax.bar(df.index, df['손실금액'], label='손실금액', color='b')
        ax.plot(df.index, df['수익금합계480'], linewidth=0.5, label='수익금합계480', color='k')
        ax.plot(df.index, df['수익금합계240'], linewidth=0.5, label='수익금합계240', color='gray')
        ax.plot(df.index, df['수익금합계120'], linewidth=0.5, label='수익금합계120', color='b')
        ax.plot(df.index, df['수익금합계060'], linewidth=0.5, label='수익금합계60', color='g')
        ax.plot(df.index, df['수익금합계020'], linewidth=0.5, label='수익금합계20', color='r')
        ax.plot(df.index, df['수익금합계'], linewidth=2, label='수익금합계', color='orange')
        count = int(len(df) / 20) if int(len(df) / 20) >= 1 else 1
        ax.set_xticks(list(df.index[::count]))
        ax.tick_params(axis='x', labelrotation=45)
        ax.legend(loc='best')
        ax.grid()
        self.canvas2.figure.tight_layout()
        self.canvas2.draw()

    def ShowDialog(self, code_or_name, tickcount, searchdate, col):
        coin = False
        if code_or_name in self.dict_code.keys():
            code = self.dict_code[code_or_name]
        elif code_or_name in self.dict_code.values():
            code = code_or_name
        else:
            code = code_or_name
            coin = True

        if col == 0:
            if not coin:
                self.ShowDialogWeb(True, code)
            else:
                self.ShowDialogHoga(True, coin, code)
        elif col == 1:
            if not coin:
                self.ShowDialogWeb(False, code)
            self.ShowDialogHoga(True, coin, code)
        elif col < 4:
            if not coin:
                self.ShowDialogWeb(False, code)
            self.ShowDialogHoga(False, coin, code)
            self.ShowDialogChart(True, coin, code)
        else:
            if not coin:
                self.ShowDialogWeb(False, code)
            self.ShowDialogHoga(False, coin, code)
            self.ShowDialogChart(False, coin, code, tickcount, searchdate, self.ct_lineEdittttt_01.text(), self.ct_lineEdittttt_02.text())

    def ShowDialogWeb(self, show, code):
        if self.webEngineView is None:
            self.webEngineView = QWebEngineView()
            p = QuietPage(self.webEngineView)
            self.webEngineView.setPage(p)
            web_layout = QVBoxLayout(self.dialog_web)
            web_layout.setContentsMargins(0, 0, 0, 0)
            web_layout.addWidget(self.webEngineView)
        if show and not self.dialog_web.isVisible():
            self.dialog_web.show()
        if show and not self.dialog_info.isVisible():
            self.dialog_info.show()
        if self.dialog_web.isVisible() and self.dialog_info.isVisible():
            self.webEngineView.load(QUrl(f'https://finance.naver.com/item/main.naver?code={code}'))
            webcQ.put(('기업정보', code))

    def ShowDialogHoga(self, show, coin, code):
        if show and not self.dialog_hoga.isVisible():
            self.dialog_hoga.show()
        if self.dialog_hoga.isVisible():
            self.PutHogaCode(coin, code)
        if self.dialog_order.isVisible():
            change = False
            if 'KRW' not in code and 'USDT' not in code:
                name = self.dict_name[code]
                if name not in self.order_combo_name_list:
                    self.od_comboBoxxxxx_01.addItem(name)
                self.od_comboBoxxxxx_01.setCurrentText(name)
                for i in range(100):
                    item = self.sjg_tableWidgettt.item(i, 0)
                    if item is not None:
                        if name == item.text():
                            count = self.sjg_tableWidgettt.item(i, 7).text()
                            self.od_lineEdittttt_02.setText(count)
                            change = True
                            break
                    else:
                        break
            else:
                if code not in self.order_combo_name_list:
                    self.od_comboBoxxxxx_01.addItem(code)
                self.od_comboBoxxxxx_01.setCurrentText(code)
                for i in range(100):
                    item = self.cjg_tableWidgettt.item(i, 0)
                    if item is not None:
                        if code == item.text():
                            count = self.cjg_tableWidgettt.item(i, 7 if 'KRW' in code else 8).text()
                            self.od_lineEdittttt_02.setText(count)
                            change = True
                            break
                    else:
                        break
            if not change:
                self.od_lineEdittttt_01.setText('')
                self.od_lineEdittttt_02.setText('')

    def ShowDialogChart(self, real, coin, code, tickcount=None, searchdate=None, starttime=None, endtime=None, detail=None, buytimes=None):
        if not self.dialog_chart.isVisible():
            if self.main_btn in (1, 3):
                self.ct_lineEdittttt_01.setText('0')
                self.ct_lineEdittttt_02.setText('235959')
            else:
                self.ct_lineEdittttt_01.setText('90000')
                self.ct_lineEdittttt_02.setText('93000')
            self.dialog_chart.show()
        if self.dialog_chart.isVisible() and proc_chart.is_alive():
            if real:
                self.ChartClear()
                if coin:
                    if self.CoinStrategyProcessAlive(): cstgQ.put(code)
                else:
                    wdzservQ.put(('strategy', ('차트종목코드', code, self.dict_sgbn[code])))
            else:
                self.ChartClear()
                if detail is None:
                    chartQ.put((coin, code, tickcount, searchdate, starttime, endtime))
                else:
                    chartQ.put((coin, code, tickcount, searchdate, starttime, endtime, detail, buytimes))

                name = self.dict_name[code] if code in self.dict_name.keys() else code
                if self.dialog_chart_day.isVisible():
                    chartQ.put(('일봉차트', coin, code, name, searchdate))
                if self.dialog_chart_min.isVisible():
                    chartQ.put(('분봉차트', coin, code, name, searchdate))

    def ChartCountChange(self):
        self.ChartClear()
        if self.ct_pushButtonnn_04.text() == 'CHART 8':
            self.ctpg_vboxLayout.removeWidget(self.ctpg_layout)
            self.dialog_chart.setFixedWidth(2088)
            self.ct_groupBoxxxxx_02.setFixedWidth(2078)
            self.ct_dateEdittttt_02.setGeometry(2088, 15, 120, 30)
            self.ct_tableWidgett_01.setGeometry(2088, 55, 120, 1310 if not self.dict_set['저해상도'] else 950)
            self.ct_pushButtonnn_04.setText('CHART 12')
            self.ct_pushButtonnn_06.setText('확장')
            self.ct_pushButtonnn_06.setStyleSheet(style_bc_bt)
            self.ctpg.clear()
            pg.setConfigOption('background', color_bg_bk)
            # noinspection PyAttributeOutsideInit
            self.ctpg_layout = pg.GraphicsLayoutWidget()
            self.ctpg[0],  self.ctpg_cvb[0]  = self.wc.setaddPlot(self.ctpg_layout, 0, 0)
            self.ctpg[1],  self.ctpg_cvb[1]  = self.wc.setaddPlot(self.ctpg_layout, 1, 0)
            self.ctpg[2],  self.ctpg_cvb[2]  = self.wc.setaddPlot(self.ctpg_layout, 2, 0)
            self.ctpg[3],  self.ctpg_cvb[3]  = self.wc.setaddPlot(self.ctpg_layout, 3, 0)
            self.ctpg[4],  self.ctpg_cvb[4]  = self.wc.setaddPlot(self.ctpg_layout, 0, 1)
            self.ctpg[5],  self.ctpg_cvb[5]  = self.wc.setaddPlot(self.ctpg_layout, 1, 1)
            self.ctpg[6],  self.ctpg_cvb[6]  = self.wc.setaddPlot(self.ctpg_layout, 2, 1)
            self.ctpg[7],  self.ctpg_cvb[7]  = self.wc.setaddPlot(self.ctpg_layout, 3, 1)
            self.ctpg[8],  self.ctpg_cvb[8]  = self.wc.setaddPlot(self.ctpg_layout, 0, 2)
            self.ctpg[9],  self.ctpg_cvb[9]  = self.wc.setaddPlot(self.ctpg_layout, 1, 2)
            self.ctpg[10], self.ctpg_cvb[10] = self.wc.setaddPlot(self.ctpg_layout, 2, 2)
            self.ctpg[11], self.ctpg_cvb[11] = self.wc.setaddPlot(self.ctpg_layout, 3, 2)
            self.ctpg_vboxLayout.addWidget(self.ctpg_layout)
        elif self.ct_pushButtonnn_04.text() == 'CHART 12':
            self.ctpg_vboxLayout.removeWidget(self.ctpg_layout)
            self.dialog_chart.setFixedWidth(2773)
            self.ct_groupBoxxxxx_02.setFixedWidth(2763)
            self.ct_dateEdittttt_02.setGeometry(2773, 15, 120, 30)
            self.ct_tableWidgett_01.setGeometry(2773, 55, 120, 1310 if not self.dict_set['저해상도'] else 950)
            self.ct_pushButtonnn_04.setText('CHART 16')
            self.ct_pushButtonnn_06.setText('확장')
            self.ct_pushButtonnn_06.setStyleSheet(style_bc_bt)
            self.ctpg.clear()
            pg.setConfigOption('background', color_bg_bk)
            # noinspection PyAttributeOutsideInit
            self.ctpg_layout = pg.GraphicsLayoutWidget()
            self.ctpg[0],  self.ctpg_cvb[0]  = self.wc.setaddPlot(self.ctpg_layout, 0, 0)
            self.ctpg[1],  self.ctpg_cvb[1]  = self.wc.setaddPlot(self.ctpg_layout, 1, 0)
            self.ctpg[2],  self.ctpg_cvb[2]  = self.wc.setaddPlot(self.ctpg_layout, 2, 0)
            self.ctpg[3],  self.ctpg_cvb[3]  = self.wc.setaddPlot(self.ctpg_layout, 3, 0)
            self.ctpg[4],  self.ctpg_cvb[4]  = self.wc.setaddPlot(self.ctpg_layout, 0, 1)
            self.ctpg[5],  self.ctpg_cvb[5]  = self.wc.setaddPlot(self.ctpg_layout, 1, 1)
            self.ctpg[6],  self.ctpg_cvb[6]  = self.wc.setaddPlot(self.ctpg_layout, 2, 1)
            self.ctpg[7],  self.ctpg_cvb[7]  = self.wc.setaddPlot(self.ctpg_layout, 3, 1)
            self.ctpg[8],  self.ctpg_cvb[8]  = self.wc.setaddPlot(self.ctpg_layout, 0, 2)
            self.ctpg[9],  self.ctpg_cvb[9]  = self.wc.setaddPlot(self.ctpg_layout, 1, 2)
            self.ctpg[10], self.ctpg_cvb[10] = self.wc.setaddPlot(self.ctpg_layout, 2, 2)
            self.ctpg[11], self.ctpg_cvb[11] = self.wc.setaddPlot(self.ctpg_layout, 3, 2)
            self.ctpg[12], self.ctpg_cvb[12] = self.wc.setaddPlot(self.ctpg_layout, 0, 3)
            self.ctpg[13], self.ctpg_cvb[13] = self.wc.setaddPlot(self.ctpg_layout, 1, 3)
            self.ctpg[14], self.ctpg_cvb[14] = self.wc.setaddPlot(self.ctpg_layout, 2, 3)
            self.ctpg[15], self.ctpg_cvb[15] = self.wc.setaddPlot(self.ctpg_layout, 3, 3)
            self.ctpg_vboxLayout.addWidget(self.ctpg_layout)
        elif self.ct_pushButtonnn_04.text() == 'CHART 16':
            self.ctpg_vboxLayout.removeWidget(self.ctpg_layout)
            self.dialog_chart.setFixedWidth(1403)
            self.ct_groupBoxxxxx_02.setFixedWidth(1393)
            self.ct_dateEdittttt_02.setGeometry(1403, 15, 120, 30)
            self.ct_tableWidgett_01.setGeometry(1403, 55, 120, 1310 if not self.dict_set['저해상도'] else 950)
            self.ct_pushButtonnn_04.setText('CHART 8')
            self.ct_pushButtonnn_06.setText('확장')
            self.ct_pushButtonnn_06.setStyleSheet(style_bc_bt)
            self.ctpg.clear()
            pg.setConfigOption('background', color_bg_bk)
            # noinspection PyAttributeOutsideInit
            self.ctpg_layout = pg.GraphicsLayoutWidget()
            self.ctpg[0], self.ctpg_cvb[0] = self.wc.setaddPlot(self.ctpg_layout, 0, 0)
            self.ctpg[1], self.ctpg_cvb[1] = self.wc.setaddPlot(self.ctpg_layout, 1, 0)
            self.ctpg[2], self.ctpg_cvb[2] = self.wc.setaddPlot(self.ctpg_layout, 2, 0)
            self.ctpg[3], self.ctpg_cvb[3] = self.wc.setaddPlot(self.ctpg_layout, 3, 0)
            self.ctpg[4], self.ctpg_cvb[4] = self.wc.setaddPlot(self.ctpg_layout, 0, 1)
            self.ctpg[5], self.ctpg_cvb[5] = self.wc.setaddPlot(self.ctpg_layout, 1, 1)
            self.ctpg[6], self.ctpg_cvb[6] = self.wc.setaddPlot(self.ctpg_layout, 2, 1)
            self.ctpg[7], self.ctpg_cvb[7] = self.wc.setaddPlot(self.ctpg_layout, 3, 1)
            self.ctpg_vboxLayout.addWidget(self.ctpg_layout)

    def ShowDialogChart2(self):
        if self.ct_pushButtonnn_06.text() == '확장':
            if self.ct_pushButtonnn_04.text() == 'CHART 8':
                width = 1528
            elif self.ct_pushButtonnn_04.text() == 'CHART 12':
                width = 2213
            else:
                width = 2898
            self.dialog_chart.setFixedSize(width, 1370 if not self.dict_set['저해상도'] else 1010)
            self.ct_pushButtonnn_06.setText('주식')
            self.ct_pushButtonnn_06.setStyleSheet(style_bc_bb)
            self.ChartMoneyTopList()
        elif self.ct_pushButtonnn_06.text() == '주식':
            self.ct_pushButtonnn_06.setText('코인')
            self.ChartMoneyTopList()
        elif self.ct_pushButtonnn_06.text() == '코인':
            if self.ct_pushButtonnn_04.text() == 'CHART 8':
                width = 1403
            elif self.ct_pushButtonnn_04.text() == 'CHART 12':
                width = 2088
            else:
                width = 2773
            self.dialog_chart.setFixedSize(width, 1370 if not self.dict_set['저해상도'] else 1010)
            self.ct_pushButtonnn_06.setText('확장')
            self.ct_pushButtonnn_06.setStyleSheet(style_bc_bt)

    def ShowQsize(self):
        if not self.showQsize:
            self.qs_pushButton.setStyleSheet(style_bc_bt)
            self.showQsize = True
        else:
            self.qs_pushButton.setStyleSheet(style_bc_bb)
            self.showQsize = False

    def ShowDialogFactor(self):
        self.dialog_factor.show() if not self.dialog_factor.isVisible() else self.dialog_factor.close()

    def ShowDialogTest(self):
        if not self.dialog_test.isVisible():
            self.ct_pushButtonnn_05.setStyleSheet(style_bc_bt)
            self.dialog_test.show()
        else:
            self.ct_pushButtonnn_05.setStyleSheet(style_bc_bb)
            self.dialog_test.close()

    def ShowChart(self):
        if not self.dialog_chart.isVisible():
            if self.main_btn in (1, 3):
                self.ct_lineEdittttt_01.setText('0')
                self.ct_lineEdittttt_02.setText('235959')
            else:
                self.ct_lineEdittttt_01.setText('90000')
                self.ct_lineEdittttt_02.setText('93000')
            self.dialog_chart.show()
        else:
            self.dialog_chart.close()

    def ShowHoga(self):
        if not self.dialog_hoga.isVisible():
            self.dialog_hoga.setFixedSize(572, 355)
            self.hj_tableWidgett_01.setGeometry(5, 5, 562, 42)
            self.hj_tableWidgett_01.setColumnWidth(0, 140)
            self.hj_tableWidgett_01.setColumnWidth(1, 140)
            self.hj_tableWidgett_01.setColumnWidth(2, 140)
            self.hj_tableWidgett_01.setColumnWidth(3, 140)
            self.hj_tableWidgett_01.setColumnWidth(4, 140)
            self.hj_tableWidgett_01.setColumnWidth(5, 140)
            self.hj_tableWidgett_01.setColumnWidth(6, 140)
            self.hj_tableWidgett_01.setColumnWidth(7, 140)
            self.hc_tableWidgett_01.setHorizontalHeaderLabels(columns_hc)
            self.hc_tableWidgett_02.setVisible(False)
            self.hg_tableWidgett_01.setGeometry(285, 52, 282, 297)
            self.dialog_hoga.show()
        else:
            self.dialog_hoga.close()

    def ShowGiup(self):
        if self.webEngineView is None:
            self.webEngineView = QWebEngineView()
            p = QuietPage(self.webEngineView)
            self.webEngineView.setPage(p)
            web_layout = QVBoxLayout(self.dialog_web)
            web_layout.setContentsMargins(0, 0, 0, 0)
            web_layout.addWidget(self.webEngineView)
        if not self.dialog_web.isVisible():
            self.dialog_web.show()
            self.webEngineView.load(QUrl('https://markets.hankyung.com/'))
        else:
            self.dialog_web.close()
        self.dialog_info.show() if not self.dialog_info.isVisible() else self.dialog_info.close()

    def ShowTreemap(self):
        if not self.dialog_tree.isVisible():
            self.dialog_tree.show()
            webcQ.put(('트리맵', ''))
        else:
            self.dialog_tree.close()

    def ShowJisu(self):
        self.dialog_jisu.show() if not self.dialog_jisu.isVisible() else self.dialog_jisu.close()

    def ShowDB(self):
        if not self.dialog_db.isVisible():
            self.dialog_db.show()

        self.db_tableWidgett_01.clearContents()
        self.db_tableWidgett_02.clearContents()
        self.db_tableWidgett_03.clearContents()
        self.db_tableWidgett_04.clearContents()
        self.db_tableWidgett_05.clearContents()

        con = sqlite3.connect(DB_STRATEGY)

        stock_stg_list = ['stockbuy', 'stocksell', 'stockoptibuy', 'stockoptisell']
        maxlow = 0
        for i, stock_stg in enumerate(stock_stg_list):
            df = pd.read_sql(f'SELECT * FROM {stock_stg}', con)
            stg_names = df['index'].to_list()
            stg_names.sort()
            if len(df) > maxlow:
                maxlow = len(df)
                self.db_tableWidgett_01.setRowCount(maxlow)
            for j, stg_name in enumerate(stg_names):
                item = QTableWidgetItem(stg_name)
                item.setTextAlignment(int(Qt.AlignVCenter | Qt.AlignCenter))
                self.db_tableWidgett_01.setItem(j, i, item)
        if maxlow < 8:
            self.db_tableWidgett_01.setRowCount(8)

        stock_stg_list = ['stockoptivars', 'stockvars', 'stockbuyconds', 'stocksellconds']
        maxlow = 0
        for i, stock_stg in enumerate(stock_stg_list):
            df = pd.read_sql(f'SELECT * FROM {stock_stg}', con)
            stg_names = df['index'].to_list()
            stg_names.sort()
            if len(df) > maxlow:
                maxlow = len(df)
                self.db_tableWidgett_02.setRowCount(maxlow)
            for j, stg_name in enumerate(stg_names):
                item = QTableWidgetItem(stg_name)
                item.setTextAlignment(int(Qt.AlignVCenter | Qt.AlignCenter))
                self.db_tableWidgett_02.setItem(j, i, item)
        if maxlow < 8:
            self.db_tableWidgett_02.setRowCount(8)

        maxlow = 0
        coin_stg_list = ['coinbuy', 'coinsell', 'coinoptibuy', 'coinoptisell']
        for i, coin_stg in enumerate(coin_stg_list):
            df = pd.read_sql(f'SELECT * FROM {coin_stg}', con)
            stg_names = df['index'].to_list()
            stg_names.sort()
            if len(df) > maxlow:
                maxlow = len(df)
                self.db_tableWidgett_03.setRowCount(maxlow)
            for j, stg_name in enumerate(stg_names):
                item = QTableWidgetItem(stg_name)
                item.setTextAlignment(int(Qt.AlignVCenter | Qt.AlignCenter))
                self.db_tableWidgett_03.setItem(j, i, item)
        if maxlow < 8:
            self.db_tableWidgett_03.setRowCount(8)

        stock_stg_list = ['coinoptivars', 'coinvars', 'coinbuyconds', 'coinsellconds']
        maxlow = 0
        for i, stock_stg in enumerate(stock_stg_list):
            df = pd.read_sql(f'SELECT * FROM {stock_stg}', con)
            stg_names = df['index'].to_list()
            stg_names.sort()
            if len(df) > maxlow:
                maxlow = len(df)
                self.db_tableWidgett_04.setRowCount(maxlow)
            for j, stg_name in enumerate(stg_names):
                item = QTableWidgetItem(stg_name)
                item.setTextAlignment(int(Qt.AlignVCenter | Qt.AlignCenter))
                self.db_tableWidgett_04.setItem(j, i, item)
        if maxlow < 8:
            self.db_tableWidgett_04.setRowCount(8)

        df = pd.read_sql(f'SELECT * FROM schedule', con)
        stg_names = df['index'].to_list()
        stg_names.sort()
        if len(df) > maxlow:
            maxlow = len(df)
            self.db_tableWidgett_05.setRowCount(maxlow)
        for j, stg_name in enumerate(stg_names):
            item = QTableWidgetItem(stg_name)
            item.setTextAlignment(int(Qt.AlignVCenter | Qt.AlignCenter))
            self.db_tableWidgett_05.setItem(j, 0, item)
        if maxlow < 8:
            self.db_tableWidgett_05.setRowCount(8)

        con.close()

    def PutHogaCode(self, coin, code):
        if coin:
            wdzservQ.put(('receiver', ('호가종목코드', '000000')))
            if self.CoinReceiverProcessAlive():  creceivQ.put(code)
        else:
            if self.CoinReceiverProcessAlive():  creceivQ.put('000000')
            wdzservQ.put(('receiver', ('호가종목코드', code)))

    def ChartMoneyTopList(self):
        searchdate = self.ct_dateEdittttt_02.date().toString('yyyyMMdd')
        starttime  = self.ct_lineEdittttt_01.text()
        endtime    = self.ct_lineEdittttt_02.text()
        coin       = True if self.ct_pushButtonnn_06.text() == '코인' else False

        if coin:
            db_name1 = f'{DB_PATH}/coin_tick_{searchdate}.db'
            db_name2 = DB_COIN_BACK
            db_name3 = DB_COIN_TICK
        else:
            db_name1 = f'{DB_PATH}/stock_tick_{searchdate}.db'
            db_name2 = DB_STOCK_BACK
            db_name3 = DB_STOCK_TICK

        df = None
        try:
            if os.path.isfile(db_name1):
                con = sqlite3.connect(db_name1)
                df = pd.read_sql(f"SELECT * FROM moneytop WHERE `index` LIKE '{searchdate}%' and `index` % 1000000 >= {starttime} and `index` % 1000000 <= {endtime}", con)
                con.close()
            elif os.path.isfile(db_name2):
                con = sqlite3.connect(db_name2)
                df = pd.read_sql(f"SELECT * FROM moneytop WHERE `index` LIKE '{searchdate}%' and `index` % 1000000 >= {starttime} and `index` % 1000000 <= {endtime}", con)
                con.close()
            elif os.path.isfile(db_name3):
                con = sqlite3.connect(db_name3)
                df = pd.read_sql(f"SELECT * FROM moneytop WHERE `index` LIKE '{searchdate}%' and `index` % 1000000 >= {starttime} and `index` % 1000000 <= {endtime}", con)
                con.close()
        except:
            pass

        if df is None or len(df) == 0:
            self.ct_tableWidgett_01.clearContents()
            return

        table_list = list(set(';'.join(df['거래대금순위'].to_list()[30:]).split(';')))
        name_list  = [self.dict_name[code] if code in self.dict_name.keys() else code for code in table_list] if not coin else table_list
        name_list.sort()

        self.ct_tableWidgett_01.setRowCount(len(name_list))
        for i, name in enumerate(name_list):
            item = QTableWidgetItem(name)
            item.setTextAlignment(int(Qt.AlignVCenter | Qt.AlignLeft))
            self.ct_tableWidgett_01.setItem(i, 0, item)
        if len(name_list) < 100:
            self.ct_tableWidgett_01.setRowCount(100)

    def ShowBackScheduler(self):
        self.dialog_scheduler.show() if not self.dialog_scheduler.isVisible() else self.dialog_scheduler.close()

    def ShowChartDay(self):
        self.dialog_chart_day.show() if not self.dialog_chart_day.isVisible() else self.dialog_chart_day.close()

    def ShowChartMin(self):
        self.dialog_chart_min.show() if not self.dialog_chart_min.isVisible() else self.dialog_chart_min.close()

    def ShowKimp(self):
        if not self.dialog_kimp.isVisible():
            self.dialog_kimp.show()
            if not self.CoinKimpProcessAlive():
                self.proc_coin_kimp = Process(target=Kimp, args=(qlist,))
                self.proc_coin_kimp.start()
        else:
            self.dialog_kimp.close()
            if self.CoinKimpProcessAlive():
                self.proc_coin_kimp.kill()
                qtest_qwait(3)

    def ShowOrder(self):
        if not self.dialog_order.isVisible():
            self.dialog_order.show()

            tableWidget = None
            if self.main_btn == 0:
                tableWidget = self.sgj_tableWidgettt
            elif self.main_btn == 1:
                tableWidget = self.cgj_tableWidgettt

            if tableWidget is not None:
                self.od_comboBoxxxxx_01.clear()
                for row in range(100):
                    item = tableWidget.item(row, 0)
                    if item is not None:
                        name = item.text()
                        self.order_combo_name_list.append(name)
                        self.od_comboBoxxxxx_01.addItem(name)
                    else:
                        break
        else:
            self.dialog_order.close()

    # =================================================================================================================

    def BackBench(self):
        buttonReply = QMessageBox.question(
            self, "벤치 테스트", "백테 벤치 테스트를 진행합니다.\n틱데이터가 9시 30분까지 로딩되어 있어야합니다.\n계속하시겠습니까?\n",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if buttonReply == QMessageBox.Yes:
            if self.BacktestProcessAlive():
                QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
            else:
                if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                    self.BackengineShow('주식')
                    return
                if not self.back_condition:
                    QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                    return

                startday  = self.svjb_dateEditt_01.date().toString('yyyyMMdd')
                endday    = self.svjb_dateEditt_02.date().toString('yyyyMMdd')
                starttime = self.svjb_lineEditt_02.text()
                endtime   = self.svjb_lineEditt_03.text()
                betting   = self.svjb_lineEditt_04.text()
                avgtime   = self.svjb_lineEditt_05.text()
                bl        = True if self.dict_set['블랙리스트추가'] else False

                if int(avgtime) not in self.avg_list:
                    QMessageBox.critical(self, '오류 알림', '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                    return
                if '' in (startday, endday, starttime, endtime, betting, avgtime):
                    QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                    return

                self.ClearBacktestQ()
                for bpq in self.back_pques:
                    bpq.put(('백테유형', '백테스트'))

                backQ.put((betting, avgtime, startday, endday, starttime, endtime, '벤치전략', '벤치전략', self.dict_cn, self.back_count, bl, False, self.df_kp, self.df_kd, False))
                self.proc_backtester_bb = Process(target=BackTest, args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '백테스트', 'S'))
                self.proc_backtester_bb.start()
                self.svjButtonClicked_07()
                self.ss_progressBar_01.setValue(0)
                self.ssicon_alert = True

    def ChangeBacksDate(self):
        if self.sd_scheckBoxxxx_01.isChecked():
            gubun = self.list_sdateEdittttt.index(self.dialog_scheduler.focusWidget())
            date  = self.list_sdateEdittttt[gubun].date().toString('yyyyMMdd')
            for i, widget in enumerate(self.list_sdateEdittttt):
                if i != gubun:
                    widget.setDate(QDate.fromString(date, 'yyyyMMdd'))

    def ChangeBackeDate(self):
        if self.sd_scheckBoxxxx_01.isChecked():
            gubun = self.list_edateEdittttt.index(self.dialog_scheduler.focusWidget())
            date  = self.list_edateEdittttt[gubun].date().toString('yyyyMMdd')
            for i, widget in enumerate(self.list_edateEdittttt):
                if i != gubun:
                    widget.setDate(QDate.fromString(date, 'yyyyMMdd'))

    # =================================================================================================================

    def dbButtonClicked_01(self):
        if not self.database_control:
            date = self.db_lineEdittttt_01.text()
            if date == '':
                windowQ.put((ui_num['DB관리'], '일자를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '주식 일자DB의 지정일자 데이터를 삭제합니다.'))
                queryQ.put(('주식일자DB지정일자삭제', date))

    def dbButtonClicked_02(self):
        if not self.database_control:
            time = self.db_lineEdittttt_02.text()
            if time == '':
                windowQ.put((ui_num['DB관리'], '시간를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '주식 일자DB의 지정시간이후 데이터를 삭제합니다.'))
                queryQ.put(('주식일자DB지정시간이후삭제', time))

    def dbButtonClicked_03(self):
        if not self.database_control:
            time = self.db_lineEdittttt_03.text()
            if time == '':
                windowQ.put((ui_num['DB관리'], '시간를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '주식 당일 데이터의 지정시간이후 데이터를 삭제합니다.'))
                queryQ.put(('주식당일데이터지정시간이후삭제', time))

    def dbButtonClicked_04(self):
        if not self.database_control:
            date = self.db_lineEdittttt_04.text()
            if date == '':
                windowQ.put((ui_num['DB관리'], '일자를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '주식 당일DB의 체결시간을 조정합니다.'))
                queryQ.put(('주식체결시간조정', date))

    def dbButtonClicked_05(self):
        if not self.database_control:
            date1 = self.db_lineEdittttt_05.text()
            date2 = self.db_lineEdittttt_06.text()
            if '' in (date1, date2):
                windowQ.put((ui_num['DB관리'], '일자를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '주식 일자DB로 백테DB를 생성합니다.'))
                queryQ.put(('주식백테DB생성', date1, date2))

    def dbButtonClicked_06(self):
        if not self.database_control:
            date1 = self.db_lineEdittttt_07.text()
            date2 = self.db_lineEdittttt_08.text()
            if '' in (date1, date2):
                windowQ.put((ui_num['DB관리'], '일자를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '주식 일자DB를 백테DB로 추가합니다.'))
                queryQ.put(('주식백테디비추가1', date1, date2))

    def dbButtonClicked_07(self):
        if not self.database_control:
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '주식 당일DB를 백테DB로 추가합니다.'))
                queryQ.put(('주식백테디비추가2', ''))

    def dbButtonClicked_08(self):
        if not self.database_control:
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '주식 당일DB를 일자DB로 분리합니다.'))
                queryQ.put(('주식일자DB분리', ''))

    def dbButtonClicked_09(self):
        buttonReply = QMessageBox.warning(
            self.dialog_db, '주식 거래기록 삭제', '체결목록, 잔고목록, 거래목록, 일별목록이 모두 삭제됩니다.\n계속하시겠습니까?\n',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if buttonReply == QMessageBox.Yes:
            if proc_query.is_alive():
                queryQ.put(('거래디비', 'DELETE FROM s_jangolist'))
                queryQ.put(('거래디비', 'DELETE FROM s_tradelist'))
                queryQ.put(('거래디비', 'DELETE FROM s_chegeollist'))
                queryQ.put(('거래디비', 'DELETE FROM s_totaltradelist'))
                queryQ.put(('거래디비', 'VACUUM'))
                windowQ.put((ui_num['DB관리'], '주식 거래기록 삭제 완료'))

    def dbButtonClicked_10(self):
        if not self.database_control:
            date = self.db_lineEdittttt_09.text()
            if date == '':
                windowQ.put((ui_num['DB관리'], '일자를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '코인 일자DB의 지정일자 데이터를 삭제합니다.'))
                queryQ.put(('코인일자DB지정일자삭제', date))

    def dbButtonClicked_11(self):
        if not self.database_control:
            time = self.db_lineEdittttt_10.text()
            if time == '':
                windowQ.put((ui_num['DB관리'], '시간를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '코인 일자DB의 지정시간이후 데이터를 삭제합니다.'))
                queryQ.put(('코인일자DB지정시간이후삭제', time))

    def dbButtonClicked_12(self):
        if not self.database_control:
            time = self.db_lineEdittttt_11.text()
            if time == '':
                windowQ.put((ui_num['DB관리'], '시간를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '코인 당일DB의 지정시간이후 데이터를 삭제합니다.'))
                queryQ.put(('코인당일데이터지정시간이후삭제', time))

    def dbButtonClicked_13(self):
        if not self.database_control:
            date1 = self.db_lineEdittttt_12.text()
            date2 = self.db_lineEdittttt_13.text()
            if '' in (date1, date2):
                windowQ.put((ui_num['DB관리'], '일자를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '코인 일자DB로 백테DB를 생성합니다.'))
                queryQ.put(('코인백테DB생성', date1, date2))

    def dbButtonClicked_14(self):
        if not self.database_control:
            date1 = self.db_lineEdittttt_14.text()
            date2 = self.db_lineEdittttt_15.text()
            if '' in (date1, date2):
                windowQ.put((ui_num['DB관리'], '일자를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '코인 일자DB를 백테DB로 추가합니다.'))
                queryQ.put(('코인백테디비추가1', date1, date2))

    def dbButtonClicked_15(self):
        if not self.database_control:
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '코인 당일DB를 백테DB로 추가합니다.'))
                queryQ.put(('코인백테디비추가2', ''))

    def dbButtonClicked_16(self):
        if not self.database_control:
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '코인 당일DB를 일자DB로 분리합니다.'))
                queryQ.put(('코인일자DB분리', ''))

    def dbButtonClicked_17(self):
        buttonReply = QMessageBox.warning(
            self.dialog_db, '코인 거래기록 삭제', '체결목록, 잔고목록, 거래목록, 일별목록이 모두 삭제됩니다.\n계속하시겠습니까?\n',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if buttonReply == QMessageBox.Yes:
            if proc_query.is_alive():
                queryQ.put(('거래디비', 'DELETE FROM c_jangolist'))
                queryQ.put(('거래디비', 'DELETE FROM c_jangolist_future'))
                queryQ.put(('거래디비', 'DELETE FROM c_tradelist'))
                queryQ.put(('거래디비', 'DELETE FROM c_tradelist_future'))
                queryQ.put(('거래디비', 'DELETE FROM c_chegeollist'))
                queryQ.put(('거래디비', 'DELETE FROM c_totaltradelist'))
                queryQ.put(('거래디비', 'VACUUM'))
                windowQ.put((ui_num['DB관리'], '코인 거래기록 삭제 완료'))

    def dbButtonClicked_18(self):
        if not self.database_control:
            date = self.db_lineEdittttt_16.text()
            if date == '':
                windowQ.put((ui_num['DB관리'], '일자를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '주식 백테DB의 지정일자 데이터를 삭제합니다.'))
                queryQ.put(('주식백테DB지정일자삭제', date))

    def dbButtonClicked_19(self):
        if not self.database_control:
            date = self.db_lineEdittttt_17.text()
            if date == '':
                windowQ.put((ui_num['DB관리'], '일자를 입력하십시오.'))
                return
            if proc_query.is_alive():
                self.database_control = True
                windowQ.put((ui_num['DB관리'], '코인 백테DB의 지정일자 데이터를 삭제합니다.'))
                queryQ.put(('코인백테DB지정일자삭제', date))

    # =================================================================================================================

    def odButtonClicked_01(self):
        name      = self.od_comboBoxxxxx_01.currentText()
        ordertype = self.od_comboBoxxxxx_02.currentText()
        op        = self.od_lineEdittttt_01.text()
        oc        = self.od_lineEdittttt_02.text()
        if '' in (op, oc, name):
            QMessageBox.critical(self.dialog_order, '오류 알림', '종목명, 주문가격, 주문수량을 올바르게 입력하십시오.\n')
            return
        if 'KRW' in name:
            if self.CoinTraderProcessAlive():
                ctraderQ.put(('매수', name, comma2float(op), comma2float(oc), now(), False, ordertype))
        elif 'USDT' not in name:
            code = self.dict_code[name]
            wdzservQ.put(('trader', ('매수', code, name, comma2int(op), comma2int(oc), now(), False, ordertype)))

    def odButtonClicked_02(self):
        name      = self.od_comboBoxxxxx_01.currentText()
        ordertype = self.od_comboBoxxxxx_02.currentText()
        op        = self.od_lineEdittttt_01.text()
        oc        = self.od_lineEdittttt_02.text()
        if '' in (op, oc, name):
            QMessageBox.critical(self.dialog_order, '오류 알림', '종목명, 주문가격, 주문수량을 올바르게 입력하십시오.\n')
            return
        if 'KRW' in name:
            if self.CoinTraderProcessAlive():
                ctraderQ.put(('매도', name, comma2float(op), comma2float(oc), now(), False, ordertype))
        elif 'USDT' not in name:
            code = self.dict_code[name]
            wdzservQ.put(('trader', ('매도', code, name, comma2int(op), comma2int(oc), now(), False, ordertype)))

    def odButtonClicked_03(self):
        name      = self.od_comboBoxxxxx_01.currentText()
        ordertype = self.od_comboBoxxxxx_02.currentText()
        op        = self.od_lineEdittttt_01.text()
        oc        = self.od_lineEdittttt_02.text()
        if '' in (op, oc, name):
            QMessageBox.critical(self.dialog_order, '오류 알림', '종목명, 주문가격, 주문수량을 올바르게 입력하십시오.\n')
            return
        if 'USDT' in name and self.CoinTraderProcessAlive():
            ctraderQ.put(('BUY_LONG', name, comma2float(op), comma2float(oc), now(), False, ordertype))

    def odButtonClicked_04(self):
        name      = self.od_comboBoxxxxx_01.currentText()
        ordertype = self.od_comboBoxxxxx_02.currentText()
        op        = self.od_lineEdittttt_01.text()
        oc        = self.od_lineEdittttt_02.text()
        if '' in (op, oc, name):
            QMessageBox.critical(self.dialog_order, '오류 알림', '종목명, 주문가격, 주문수량을 올바르게 입력하십시오.\n')
            return
        if 'USDT' in name and self.CoinTraderProcessAlive():
            ctraderQ.put(('SELL_LONG', name, comma2float(op), comma2float(oc), now(), False, ordertype))

    def odButtonClicked_05(self):
        name      = self.od_comboBoxxxxx_01.currentText()
        ordertype = self.od_comboBoxxxxx_02.currentText()
        op        = self.od_lineEdittttt_01.text()
        oc        = self.od_lineEdittttt_02.text()
        if '' in (op, oc, name):
            QMessageBox.critical(self.dialog_order, '오류 알림', '종목명, 주문가격, 주문수량을 올바르게 입력하십시오.\n')
            return
        if 'USDT' in name and self.CoinTraderProcessAlive():
            ctraderQ.put(('SELL_SHORT', name, comma2float(op), comma2float(oc), now(), False, ordertype))

    def odButtonClicked_06(self):
        name      = self.od_comboBoxxxxx_01.currentText()
        ordertype = self.od_comboBoxxxxx_02.currentText()
        op        = self.od_lineEdittttt_01.text()
        oc        = self.od_lineEdittttt_02.text()
        if '' in (op, oc, name):
            QMessageBox.critical(self.dialog_order, '오류 알림', '종목명, 주문가격, 주문수량을 올바르게 입력하십시오.\n')
            return
        if 'USDT' in name and self.CoinTraderProcessAlive():
            ctraderQ.put(('BUY_SHORT', name, comma2float(op), comma2float(oc), now(), False, ordertype))

    def odButtonClicked_07(self):
        name = self.od_comboBoxxxxx_01.currentText()
        if name == '':
            QMessageBox.critical(self.dialog_order, '오류 알림', '종목명을 선택하십시오.\n종목명은 관심종목 테이블의 리스트입니다.\n')
            return
        if 'KRW' in name:
            if self.CoinTraderProcessAlive():
                ctraderQ.put(('매수취소', name, 0, 0, now(), False))
        elif 'USDT' in name:
            if self.CoinTraderProcessAlive():
                ctraderQ.put(('BUY_LONG_CANCEL', name, 0, 0, now(), False))
                ctraderQ.put(('SELL_SHORT_CANCEL', name, 0, 0, now(), False))
        else:
            code = self.dict_code[name]
            wdzservQ.put(('trader', ('매수취소', code, name, 0, 0, now(), False)))

    def odButtonClicked_08(self):
        name = self.od_comboBoxxxxx_01.currentText()
        if name == '':
            QMessageBox.critical(self.dialog_order, '오류 알림', '종목명을 선택하십시오.\n종목명은 관심종목 테이블의 리스트입니다.\n')
            return
        if 'KRW' in name:
            if self.CoinTraderProcessAlive():
                ctraderQ.put(('매도취소', name, 0, 0, now(), False))
        elif 'USDT' in name:
            if self.CoinTraderProcessAlive():
                ctraderQ.put(('SELL_LONG_CANCEL', name, 0, 0, now(), False))
                ctraderQ.put(('BUY_SHORT_CANCEL', name, 0, 0, now(), False))
        else:
            code = self.dict_code[name]
            wdzservQ.put(('trader', ('매도취소', code, name, 0, 0, now(), False)))

    # =================================================================================================================

    def cpButtonClicked_01(self):
        backdetail_list = []
        for i, checkbox in enumerate(self.backcheckbox_list):
            if checkbox.isChecked():
                backdetail_list.append(self.backdetail_list[i])

        if len(backdetail_list) >= 2:
            chartQ.put(('그래프비교', backdetail_list))
        else:
            QMessageBox.critical(self.dialog_comp, '오류 알림', '두개 이상의 상세기록을 선택하십시오.\n')

    # =================================================================================================================

    def beButtonClicked_01(self):
        if self.main_btn == 2 or (self.dialog_scheduler.isVisible() and self.sd_pushButtonnn_01.text() == '주식'):
            if not self.backtest_engine:
                self.StartBacktestEngine('주식')
            else:
                buttonReply = QMessageBox.question(
                    self.dialog_backengine, '백테엔진', '이미 백테스트 엔진이 구동중입니다.\n엔진을 재시작하시겠습니까?\n',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if buttonReply == QMessageBox.Yes:
                    self.backtest_engine = False
                    for proc in self.back_procs:
                        proc.kill()
                    for proc in self.bact_procs:
                        proc.kill()
                    self.BacktestEngineVarsReset()
                    qtest_qwait(3)
                    self.StartBacktestEngine('주식')
        elif self.main_btn == 3 or (self.dialog_scheduler.isVisible() and self.sd_pushButtonnn_01.text() == '코인'):
            if not self.backtest_engine:
                self.StartBacktestEngine('코인')
            else:
                buttonReply = QMessageBox.question(
                    self.dialog_backengine, '백테엔진', '이미 백테스트 엔진이 구동중입니다.\n엔진을 재시작하시겠습니까?\n',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if buttonReply == QMessageBox.Yes:
                    self.backtest_engine = False
                    for proc in self.back_procs:
                        proc.kill()
                    for proc in self.bact_procs:
                        proc.kill()
                    self.BacktestEngineVarsReset()
                    qtest_qwait(3)
                    self.StartBacktestEngine('코인')

    def BacktestEngineVarsReset(self):
        self.ClearBacktestQ()
        self.back_procs = []
        self.bact_procs = []
        self.back_pques = []
        self.bact_pques = []
        self.dict_cn    = None
        self.dict_mt    = None
        self.back_count = 0
        self.startday   = 0
        self.endday     = 0
        self.starttime  = 0
        self.endtime    = 0

    def sdButtonClicked_01(self):
        if type(self.dialog_scheduler.focusWidget()) != QLineEdit:
            if self.sd_pushButtonnn_01.text() == '주식':
                self.sd_pushButtonnn_01.setText('코인')
            else:
                self.sd_pushButtonnn_01.setText('주식')

    def sdButtonClicked_02(self):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self.dialog_scheduler, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            bt_gubun = self.sd_pushButtonnn_01.text()
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow(bt_gubun)
                return

            if bt_gubun == '주식' and self.main_btn != 2:
                self.mnButtonClicked_00(2)
            elif bt_gubun == '코인' and self.main_btn != 3:
                self.mnButtonClicked_00(3)

            self.ClearBacktestQ()
            if self.back_schedul:
                self.back_scount += 1
            else:
                for progressBar in self.list_progressBarrr:
                    progressBar.setValue(0)

            while self.back_scount < 16 and not self.list_checkBoxxxxxx[self.back_scount].isChecked():
                self.back_scount += 1

            if self.back_scount < 16:
                back_name = self.list_gcomboBoxxxxx[self.back_scount].currentText()
                if back_name == '백테스트':
                    startday  = self.list_sdateEdittttt[self.back_scount].date().toString('yyyyMMdd')
                    endday    = self.list_edateEdittttt[self.back_scount].date().toString('yyyyMMdd')
                    starttime = self.list_slineEdittttt[self.back_scount].text()
                    endtime   = self.list_elineEdittttt[self.back_scount].text()
                    betting   = self.list_blineEdittttt[self.back_scount].text()
                    avgtime   = self.list_alineEdittttt[self.back_scount].text()
                    buystg    = self.list_bcomboBoxxxxx[self.back_scount].currentText()
                    sellstg   = self.list_scomboBoxxxxx[self.back_scount].currentText()
                    bl        = True if self.dict_set['블랙리스트추가'] else False

                    if int(avgtime) not in self.avg_list:
                        self.StopScheduler()
                        QMessageBox.critical(self.dialog_scheduler, '오류 알림', '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                        return

                    for bpq in self.back_pques:
                        bpq.put(('백테유형', '백테스트'))

                    if bt_gubun == '주식':
                        backQ.put((betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg, self.dict_cn, self.back_count, bl, True, self.df_kp, self.df_kd, False))
                        gubun = 'S'
                    else:
                        backQ.put((betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg, None, self.back_count, bl, True, None, None, False))
                        gubun = 'C' if self.dict_set['거래소'] == '업비트' else 'CF'

                    self.proc_backtester_bb = Process(target=BackTest, args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, gubun))
                    self.proc_backtester_bb.start()

                    if bt_gubun == '주식':
                        self.svjButtonClicked_07()
                        self.ss_progressBar_01.setValue(0)
                        self.ssicon_alert = True
                    else:
                        self.cvjButtonClicked_07()
                        self.cs_progressBar_01.setValue(0)
                        self.csicon_alert = True

                elif '조건' in back_name:
                    starttime   = self.list_slineEdittttt[self.back_scount].text()
                    endtime     = self.list_elineEdittttt[self.back_scount].text()
                    betting     = self.list_blineEdittttt[self.back_scount].text()
                    avgtime     = self.list_alineEdittttt[self.back_scount].text()
                    buystg      = self.list_bcomboBoxxxxx[self.back_scount].currentText()
                    sellstg     = self.list_scomboBoxxxxx[self.back_scount].currentText()
                    bcount      = self.sd_oclineEdittt_01.text()
                    scount      = self.sd_oclineEdittt_02.text()
                    rcount      = self.sd_oclineEdittt_03.text()
                    optistd     = self.list_tcomboBoxxxxx[self.back_scount].currentText()
                    weeks_train = self.list_p1comboBoxxxx[self.back_scount].currentText()
                    weeks_valid = self.list_p2comboBoxxxx[self.back_scount].currentText()
                    weeks_test  = self.list_p3comboBoxxxx[self.back_scount].currentText()
                    benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
                    bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')

                    for bpq in self.back_pques:
                        bpq.put(('백테유형', '조건최적화'))

                    backQ.put((
                        betting, avgtime, starttime, endtime, buystg, sellstg, self.dict_set['최적화기준값제한'], optistd,
                        bcount, scount, rcount, self.back_count, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday
                    ))
                    if bt_gubun == '주식':
                        gubun = 'S'
                    elif self.dict_set['거래소'] == '업비트':
                        gubun = 'C'
                    else:
                        gubun = 'CF'

                    if back_name == '조건 최적화':
                        self.proc_backtester_oc = Process(
                            target=OptimizeConditions,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OC', gubun)
                        )
                        self.proc_backtester_oc.start()
                    elif back_name == '검증 조건 최적화':
                        self.proc_backtester_ocv = Process(
                            target=OptimizeConditions,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OCV', gubun)
                        )
                        self.proc_backtester_ocv.start()
                    elif back_name == '교차검증 조건 최적화':
                        self.proc_backtester_ocvc = Process(
                            target=OptimizeConditions,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OCVC', gubun)
                        )
                        self.proc_backtester_ocvc.start()

                    if bt_gubun == '주식':
                        self.svjButtonClicked_07()
                        self.ss_progressBar_01.setValue(0)
                        self.ssicon_alert = True
                    else:
                        self.cvjButtonClicked_07()
                        self.cs_progressBar_01.setValue(0)
                        self.csicon_alert = True

                elif 'GA' in back_name:
                    starttime   = self.list_slineEdittttt[self.back_scount].text()
                    endtime     = self.list_elineEdittttt[self.back_scount].text()
                    betting     = self.list_blineEdittttt[self.back_scount].text()
                    buystg      = self.list_bcomboBoxxxxx[self.back_scount].currentText()
                    sellstg     = self.list_scomboBoxxxxx[self.back_scount].currentText()
                    optivars    = self.list_vcomboBoxxxxx[self.back_scount].currentText()
                    optistd     = self.list_tcomboBoxxxxx[self.back_scount].currentText()
                    weeks_train = self.list_p1comboBoxxxx[self.back_scount].currentText()
                    weeks_valid = self.list_p2comboBoxxxx[self.back_scount].currentText()
                    weeks_test  = self.list_p3comboBoxxxx[self.back_scount].currentText()
                    benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
                    bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')

                    for bpq in self.back_pques:
                        bpq.put(('백테유형', 'GA최적화'))

                    if bt_gubun == '주식':
                        backQ.put((
                            betting, starttime, endtime, buystg, sellstg, optivars, self.dict_cn, self.dict_set['최적화기준값제한'],
                            optistd, self.back_count, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday
                        ))
                        gubun = 'S'
                    else:
                        backQ.put((
                            betting, starttime, endtime, buystg, sellstg, optivars, None, self.dict_set['최적화기준값제한'],
                            optistd, self.back_count, weeks_train, weeks_valid, weeks_test, benginesday, benginesday
                        ))
                        gubun = 'C' if self.dict_set['거래소'] == '업비트' else 'CF'

                    if back_name == '그리드 GA 최적화':
                        self.proc_backtester_og = Process(
                            target=OptimizeGeneticAlgorithm,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OG', gubun)
                        )
                        self.proc_backtester_og.start()
                    elif back_name == '그리드 검증 GA 최적화':
                        self.proc_backtester_ogv = Process(
                            target=OptimizeGeneticAlgorithm,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OGV', gubun)
                        )
                        self.proc_backtester_ogv.start()
                    elif back_name == '그리드 교차검증 GA 최적화':
                        self.proc_backtester_ogvc = Process(
                            target=OptimizeGeneticAlgorithm,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OGVC', gubun)
                        )
                        self.proc_backtester_ogvc.start()

                    if bt_gubun == '주식':
                        self.svjButtonClicked_07()
                        self.ss_progressBar_01.setValue(0)
                        self.ssicon_alert = True
                    else:
                        self.cvjButtonClicked_07()
                        self.cs_progressBar_01.setValue(0)
                        self.csicon_alert = True

                elif '전진분석' in back_name:
                    startday    = self.list_sdateEdittttt[self.back_scount].date().toString('yyyyMMdd')
                    endday      = self.list_edateEdittttt[self.back_scount].date().toString('yyyyMMdd')
                    starttime   = self.list_slineEdittttt[self.back_scount].text()
                    endtime     = self.list_elineEdittttt[self.back_scount].text()
                    betting     = self.list_blineEdittttt[self.back_scount].text()
                    buystg      = self.list_bcomboBoxxxxx[self.back_scount].currentText()
                    sellstg     = self.list_scomboBoxxxxx[self.back_scount].currentText()
                    optivars    = self.list_vcomboBoxxxxx[self.back_scount].currentText()
                    weeks_train = self.list_p1comboBoxxxx[self.back_scount].currentText()
                    weeks_valid = self.list_p2comboBoxxxx[self.back_scount].currentText()
                    weeks_test  = self.list_p3comboBoxxxx[self.back_scount].currentText()
                    ccount      = self.list_p4comboBoxxxx[self.back_scount].currentText()
                    optistd     = self.list_tcomboBoxxxxx[self.back_scount].currentText()
                    benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
                    bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')
                    optunasampl = self.op_comboBoxxxx_01.currentText()
                    optunafixv  = self.op_lineEditttt_01.text()
                    optunacount = self.op_lineEditttt_02.text()
                    optunaautos = 1 if self.op_checkBoxxxx_01.isChecked() else 0

                    for bpq in self.back_pques:
                        bpq.put(('백테유형', '전진분석'))

                    if bt_gubun == '주식':
                        backQ.put((
                            betting, startday, endday, starttime, endtime, buystg, sellstg, optivars, self.dict_cn,
                            ccount, self.dict_set['최적화기준값제한'], optistd, self.back_count, True, self.df_kp,
                            self.df_kd, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday, optunasampl,
                            optunafixv, optunacount, optunaautos, False
                        ))
                        gubun = 'S'
                    else:
                        backQ.put((
                            betting, startday, endday, starttime, endtime, buystg, sellstg, optivars, None, ccount,
                            self.dict_set['최적화기준값제한'], optistd, self.back_count, True, None, None, weeks_train,
                            weeks_valid, weeks_test, benginesday, bengineeday, optunasampl, optunafixv, optunacount,
                            optunaautos, False
                        ))
                        gubun = 'C' if self.dict_set['거래소'] == '업비트' else 'CF'

                    if back_name == '그리드 최적화 전진분석':
                        self.proc_backtester_or = Process(
                            target=RollingWalkForwardTest,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '전진분석OR', gubun)
                        )
                        self.proc_backtester_or.start()
                    elif back_name == '그리드 검증 최적화 전진분석':
                        self.proc_backtester_orv = Process(
                            target=RollingWalkForwardTest,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '전진분석ORV', gubun)
                        )
                        self.proc_backtester_orv.start()
                    elif back_name == '그리드 교차검증 최적화 전진분석':
                        self.proc_backtester_orvc = Process(
                            target=RollingWalkForwardTest,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '전진분석ORVC', gubun)
                        )
                        self.proc_backtester_orvc.start()
                    elif back_name == '베이지안 최적화 전진분석':
                        self.proc_backtester_br = Process(
                            target=RollingWalkForwardTest,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '전진분석BR', gubun)
                        )
                        self.proc_backtester_br.start()
                    elif back_name == '베이지안 검증 최적화 전진분석':
                        self.proc_backtester_brv = Process(
                            target=RollingWalkForwardTest,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '전진분석BRV', gubun)
                        )
                        self.proc_backtester_brv.start()
                    elif back_name == '베이지안 교차검증 최적화 전진분석':
                        self.proc_backtester_brvc = Process(
                            target=RollingWalkForwardTest,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '전진분석BRVC', gubun)
                        )
                        self.proc_backtester_brvc.start()

                    if bt_gubun == '주식':
                        self.svjButtonClicked_07()
                        self.ss_progressBar_01.setValue(0)
                        self.ssicon_alert = True
                    else:
                        self.cvjButtonClicked_07()
                        self.cs_progressBar_01.setValue(0)
                        self.csicon_alert = True

                elif '최적화' in back_name:
                    starttime   = self.list_slineEdittttt[self.back_scount].text()
                    endtime     = self.list_elineEdittttt[self.back_scount].text()
                    betting     = self.list_blineEdittttt[self.back_scount].text()
                    buystg      = self.list_bcomboBoxxxxx[self.back_scount].currentText()
                    sellstg     = self.list_scomboBoxxxxx[self.back_scount].currentText()
                    optivars    = self.list_vcomboBoxxxxx[self.back_scount].currentText()
                    ccount      = self.list_p4comboBoxxxx[self.back_scount].currentText()
                    optistd     = self.list_tcomboBoxxxxx[self.back_scount].currentText()
                    weeks_train = self.list_p1comboBoxxxx[self.back_scount].currentText()
                    weeks_valid = self.list_p2comboBoxxxx[self.back_scount].currentText()
                    weeks_test  = self.list_p3comboBoxxxx[self.back_scount].currentText()
                    benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
                    bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')
                    optunasampl = self.op_comboBoxxxx_01.currentText()
                    optunafixv  = self.op_lineEditttt_01.text()
                    optunacount = self.op_lineEditttt_02.text()
                    optunaautos = 1 if self.op_checkBoxxxx_01.isChecked() else 0

                    for bpq in self.back_pques:
                        bpq.put(('백테유형', '최적화'))

                    if bt_gubun == '주식':
                        backQ.put((
                            betting, starttime, endtime, buystg, sellstg, optivars, self.dict_cn, ccount,
                            self.dict_set['최적화기준값제한'], optistd, self.back_count, True, self.df_kp, self.df_kd,
                            weeks_train, weeks_valid, weeks_test, benginesday, bengineeday, optunasampl, optunafixv,
                            optunacount, optunaautos, False
                        ))
                        gubun = 'S'
                    else:
                        backQ.put((
                            betting, starttime, endtime, buystg, sellstg, optivars, None, ccount,
                            self.dict_set['최적화기준값제한'], optistd, self.back_count, True, None, None, weeks_train,
                            weeks_valid, weeks_test, benginesday, bengineeday, optunasampl, optunafixv, optunacount,
                            optunaautos, False
                        ))
                        gubun = 'C' if self.dict_set['거래소'] == '업비트' else 'CF'

                    if back_name == '그리드 최적화':
                        self.proc_backtester_o = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화O', gubun)
                        )
                        self.proc_backtester_o.start()
                    elif back_name == '그리드 검증 최적화':
                        self.proc_backtester_ov = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OV', gubun)
                        )
                        self.proc_backtester_ov.start()
                    elif back_name == '그리드 교차검증 최적화':
                        self.proc_backtester_ovc = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OVC', gubun)
                        )
                        self.proc_backtester_ovc.start()
                    elif back_name == '베이지안 최적화':
                        self.proc_backtester_b = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화B', gubun)
                        )
                        self.proc_backtester_b.start()
                    elif back_name == '베이지안 검증 최적화':
                        self.proc_backtester_bv = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화BV', gubun)
                        )
                        self.proc_backtester_bv.start()
                    elif back_name == '베이지안 교차검증 최적화':
                        self.proc_backtester_bvc = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화BVC', gubun)
                        )
                        self.proc_backtester_bvc.start()
                    elif back_name == '그리드 최적화 테스트':
                        self.proc_backtester_ot = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OT', gubun)
                        )
                        self.proc_backtester_ot.start()
                    elif back_name == '그리드 검증 최적화 테스트':
                        self.proc_backtester_ovt = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OVT', gubun)
                        )
                        self.proc_backtester_ovt.start()
                    elif back_name == '그리드 교차검증 최적화 테스트':
                        self.proc_backtester_ovct = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화OVCT', gubun)
                        )
                        self.proc_backtester_ovct.start()
                    elif back_name == '베이지안 최적화 테스트':
                        self.proc_backtester_bt = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화BT', gubun)
                        )
                        self.proc_backtester_bt.start()
                    elif back_name == '베이지안 검증 최적화 테스트':
                        self.proc_backtester_bvt = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화BVT', gubun)
                        )
                        self.proc_backtester_bvt.start()
                    elif back_name == '베이지안 교차검증 최적화 테스트':
                        self.proc_backtester_bvct = Process(
                            target=Optimize,
                            args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '최적화BVCT', gubun)
                        )
                        self.proc_backtester_bvct.start()

                    if bt_gubun == '주식':
                        self.svjButtonClicked_07()
                        self.ss_progressBar_01.setValue(0)
                        self.ssicon_alert = True
                    else:
                        self.cvjButtonClicked_07()
                        self.cs_progressBar_01.setValue(0)
                        self.csicon_alert = True

                self.list_progressBarrr[self.back_scount].setValue(0)
                self.back_schedul = True
            else:
                self.StopScheduler(True)

    def StopScheduler(self, gubun=False):
        self.back_scount = 0
        self.back_schedul = False
        if self.auto_mode:
            self.AutoBackSchedule(3)
        if gubun and self.sd_scheckBoxxxx_02.isChecked():
            QTimer.singleShot(180 * 1000, self.ProcessKill)
            os.system('shutdown /s /t 300')

    def sdButtonClicked_03(self):
        if self.sd_pushButtonnn_01.text() == '주식':
            self.ssButtonClicked_06()
        else:
            self.csButtonClicked_06()
        for progressBar in self.list_progressBarrr:
            progressBar.setValue(0)

    def sdButtonClicked_04(self):
        con = sqlite3.connect(DB_STRATEGY)
        df = pd.read_sql('SELECT * FROM schedule', con).set_index('index')
        con.close()
        if len(df) > 0:
            if self.sd_scheckBoxxxx_01.isChecked():
                self.sd_scheckBoxxxx_01.nextCheckState()
            self.sd_dcomboBoxxxx_01.clear()
            indexs = list(df.index)
            indexs.sort()
            for i, index in enumerate(indexs):
                self.sd_dcomboBoxxxx_01.addItem(index)
                if i == 0:
                    self.sd_dlineEditttt_01.setText(index)

    def sdButtonClicked_05(self):
        schedule_name = self.sd_dlineEditttt_01.text()
        if schedule_name == '':
            QMessageBox.critical(self.dialog_scheduler, '오류 알림', '스케쥴 이름이 공백 상태입니다.\n')
        else:
            schedule = ''
            for i in range(16):
                if self.list_checkBoxxxxxx[i].isChecked():
                    schedule += self.list_gcomboBoxxxxx[i].currentText() + ';'
                    schedule += self.list_slineEdittttt[i].text() + ';'
                    schedule += self.list_elineEdittttt[i].text() + ';'
                    schedule += self.list_blineEdittttt[i].text() + ';'
                    schedule += self.list_alineEdittttt[i].text() + ';'
                    schedule += self.list_p1comboBoxxxx[i].currentText() + ';'
                    schedule += self.list_p2comboBoxxxx[i].currentText() + ';'
                    schedule += self.list_p3comboBoxxxx[i].currentText() + ';'
                    schedule += self.list_p4comboBoxxxx[i].currentText() + ';'
                    schedule += self.list_tcomboBoxxxxx[i].currentText() + ';'
                    schedule += self.list_bcomboBoxxxxx[i].currentText() + ';'
                    schedule += self.list_scomboBoxxxxx[i].currentText() + ';'
                    schedule += self.list_vcomboBoxxxxx[i].currentText() + '^'
            schedule += '1;' if self.sd_scheckBoxxxx_02.isChecked() else '0;'
            schedule += self.sd_oclineEdittt_01.text() + ';'
            schedule += self.sd_oclineEdittt_02.text() + ';'
            schedule += self.sd_oclineEdittt_03.text()
            if proc_query.is_alive():
                queryQ.put(('전략디비', f"DELETE FROM schedule WHERE `index` = '{schedule_name}'"))
                df = pd.DataFrame({'스케쥴': [schedule]}, index=[schedule_name])
                queryQ.put(('전략디비', df, 'schedule', 'append'))
            QMessageBox.information(self.dialog_scheduler, '저장 완료', random.choice(famous_saying))

    # =================================================================================================================

    def mnButtonClicked_00(self, index):
        if self.extend_window:
            QMessageBox.critical(self, '오류 알림', '전략탭 확장 상태에서는 탭을 변경할 수 없습니다.')
            return
        prev_main_btn = self.main_btn
        if prev_main_btn == index: return
        self.image_label1.setVisible(False)
        if index == 3:
            if self.dict_set['거래소'] == '업비트':
                self.cvjb_labelllll_03.setText('백테스트 기본설정   배팅(백만)                        평균틱수   self.vars[0]')
                if self.cvjb_lineEditt_04.text() == '10000':
                    self.cvjb_lineEditt_04.setText('20')
            else:
                self.cvjb_labelllll_03.setText('백테스트 기본설정배팅(USDT)                        평균틱수   self.vars[0]')
                if self.cvjb_lineEditt_04.text() == '20':
                    self.cvjb_lineEditt_04.setText('10000')
        elif index == 5 and self.lgicon_alert:
            self.lgicon_alert = False
            self.main_btn_list[index].setIcon(self.icon_log)
        elif index == 6:
            if self.dict_set['거래소'] == '업비트':
                self.sj_coin_labell_03.setText('장초전략                        백만원,  장중전략                        백만원              전략중지 및 잔고청산  |')
            else:
                self.sj_coin_labell_03.setText('장초전략                        USDT,   장중전략                        USDT              전략중지 및 잔고청산  |')

        self.main_btn = index
        self.main_btn_list[prev_main_btn].setStyleSheet(style_bc_bb)
        self.main_btn_list[self.main_btn].setStyleSheet(style_bc_bt)
        self.main_box_list[prev_main_btn].setVisible(False)
        self.main_box_list[self.main_btn].setVisible(True)
        QTimer.singleShot(400, lambda: self.image_label1.setVisible(True if self.svc_labellllll_05.isVisible() or self.cvc_labellllll_05.isVisible() else False))
        self.animation = QPropertyAnimation(self.main_box_list[self.main_btn], b'size')
        self.animation.setEasingCurve(QEasingCurve.InCirc)
        self.animation.setDuration(300)
        self.animation.setStartValue(QSize(0, 757))
        self.animation.setEndValue(QSize(1353, 757))
        self.animation.start()

    def mnButtonClicked_01(self):
        if self.main_btn == 0:
            if not self.s_calendarWidgett.isVisible():
                boolean1 = False
                boolean2 = True
            else:
                boolean1 = True
                boolean2 = False
            for widget in self.stock_basic_listt:
                widget.setVisible(boolean1)
            for widget in self.stock_total_listt:
                widget.setVisible(boolean2)
        elif self.main_btn == 1:
            if not self.c_calendarWidgett.isVisible():
                boolean1 = False
                boolean2 = True
            else:
                boolean1 = True
                boolean2 = False
            for widget in self.coin_basic_listtt:
                widget.setVisible(boolean1)
            for widget in self.coin_total_listtt:
                widget.setVisible(boolean2)
        else:
            QMessageBox.warning(self, '오류 알림', '해당 버튼은 트레이더탭에서만 작동합니다.\n')

    def mnButtonClicked_02(self, stocklogin=False):
        if stocklogin:
            buttonReply = QMessageBox.Yes
        else:
            if self.dialog_web.isVisible():
                QMessageBox.critical(self, '오류 알림', '웹뷰어창이 열린 상태에서는 수동시작할 수 없습니다.\n웹뷰어창을 닫고 재시도하십시오.\n')
                return
            if self.dict_set['리시버실행시간'] <= int_hms() <= self.dict_set['트레이더실행시간']:
                QMessageBox.critical(self, '오류 알림', '리시버 및 트레이더 실행시간 동안은 수동시작할 수 없습니다.\n')
                return
            buttonReply = QMessageBox.question(
                self, '주식 수동 시작', '주식 리시버 또는 트레이더를 시작합니다.\n이미 실행 중이라면 기존 프로세스는 종료됩니다.\n계속하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )

        if buttonReply == QMessageBox.Yes:
            wdzservQ.put(('manager', '리시버 종료'))
            wdzservQ.put(('manager', '전략연산 종료'))
            wdzservQ.put(('manager', '트레이더 종료'))
            qtest_qwait(3)
            if self.dict_set['리시버공유'] < 2 and self.dict_set['아이디2'] is None:
                QMessageBox.critical(self, '오류 알림', '두번째 계정이 설정되지 않아\n리시버를 시작할 수 없습니다.\n계정 설정 후 다시 시작하십시오.\n')
            if self.dict_set['아이디1'] is None:
                QMessageBox.critical(self, '오류 알림', '첫번째 계정이 설정되지 않아\n트레이더를 시작할 수 없습니다.\n계정 설정 후 다시 시작하십시오.\n')
            if self.dict_set['주식리시버'] and self.dict_set['주식트레이더']:
                if self.dict_set['주식알림소리']:
                    soundQ.put('키움증권 OPEN API에 로그인을 시작합니다.')
                wdzservQ.put(('manager', '주식수동시작'))
        self.ms_pushButton.setStyleSheet(style_bc_bt)

    def mnButtonClicked_03(self):
        if self.geometry().width() > 1000:
            self.setFixedSize(722, 383)
            self.zo_pushButton.setStyleSheet(style_bc_bt)
        else:
            self.setFixedSize(1403, 763)
            self.zo_pushButton.setStyleSheet(style_bc_bb)

    def mnButtonClicked_04(self):
        buttonReply = QMessageBox.warning(
            self, '백테기록삭제', '백테 그래프 및 기록 DB가 삭제됩니다.\n계속하시겠습니까?\n',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if buttonReply == QMessageBox.Yes:
            file_list = os.listdir(GRAPH_PATH)
            for file_name in file_list:
                os.remove(f'{GRAPH_PATH}/{file_name}')
            if proc_query.is_alive():
                con = sqlite3.connect(DB_BACKTEST)
                df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
                con.close()
                table_list = df['name'].to_list()
                for table_name in table_list:
                    queryQ.put(('백테디비', f'DROP TABLE {table_name}'))
                queryQ.put(('백테디비', 'VACUUM'))
            QMessageBox.information(self, '알림', '백테그래프 및 기록DB가 삭제되었습니다.')

    def mnButtonClicked_05(self):
        buttonReply = QMessageBox.warning(
            self, '계정 설정 초기화', '계정 설정 항목이 모두 초기화됩니다.\n계속하시겠습니까?\n',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if buttonReply == QMessageBox.Yes:
            if proc_query.is_alive():
                queryQ.put(('설정디비', 'DELETE FROM sacc'))
                queryQ.put(('설정디비', 'DELETE FROM cacc'))
                queryQ.put(('설정디비', 'DELETE FROM telegram'))
                columns = [
                    "index", "아이디1", "비밀번호1", "인증서비밀번호1", "계좌비밀번호1", "아이디2", "비밀번호2", "인증서비밀번호2", "계좌비밀번호2",
                    "아이디3", "비밀번호3", "인증서비밀번호3", "계좌비밀번호3", "아이디4", "비밀번호4", "인증서비밀번호4", "계좌비밀번호4"
                ]
                data = [0, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
                df = pd.DataFrame([data], columns=columns).set_index('index')
                queryQ.put((df, 'sacc', 'append'))
                columns = ["index", "Access_key1", "Secret_key1", "Access_key2", "Secret_key2"]
                data = [0, '', '', '', '']
                df = pd.DataFrame([data], columns=columns).set_index('index')
                queryQ.put((df, 'cacc', 'append'))
                columns = ["index", "str_bot", "int_id"]
                data = [0, '', '']
                df = pd.DataFrame([data], columns=columns).set_index('index')
                queryQ.put((df, 'telegram', 'append'))
                queryQ.put(('설정디비', 'VACUUM'))
            QMessageBox.information(self, '알림', '계정 설정 항목이 모두 초기화되었습니다.')

    # =================================================================================================================

    def ttButtonClicked_01(self, cmd):
        if '집계' in cmd:
            gubun = 'S' if 'S' in cmd else 'C'
            table = 's_totaltradelist' if 'S' in cmd else 'c_totaltradelist'
            con = sqlite3.connect(DB_TRADELIST)
            df = pd.read_sql(f'SELECT * FROM {table}', con)
            con.close()
            df = df[::-1]
            if len(df) > 0:
                pr = len(df)
                nsp = 100
                for sp in df['수익률'].to_list()[::-1]:
                    nsp = nsp + nsp * sp / 100
                nsp = round(nsp - 100, 2)
                nbg, nsg = df['총매수금액'].sum(), df['총매도금액'].sum()
                npg, nmg = df['총수익금액'].sum(), df['총손실금액'].sum()
                nsig = df['수익금합계'].sum()
                df2 = pd.DataFrame(columns=columns_nt)
                df2.loc[0] = pr, nbg, nsg, npg, nmg, nsp, nsig
                self.UpdateTablewidget((ui_num[f'{gubun}누적합계'], df2))
            else:
                QMessageBox.critical(self, '오류 알림', '거래목록이 존재하지 않습니다.\n')
                return
            if cmd == f'{gubun}일별집계':
                df.rename(columns={'index': '일자'}, inplace=True)
                self.UpdateTablewidget((ui_num[f'{gubun}누적상세'], df))
            elif cmd == f'{gubun}월별집계':
                df['연월'] = df['index'].apply(lambda x: str(x)[:6])
                df2 = pd.DataFrame(columns=columns_nd)
                lastmonth = df['연월'][df.index[-1]]
                month = strf_time('%Y%m')
                while int(month) >= int(lastmonth):
                    df3 = df[df['연월'] == month]
                    if len(df3) > 0:
                        tbg, tsg = df3['총매수금액'].sum(), df3['총매도금액'].sum()
                        sp = round((tsg / tbg - 1) * 100, 2)
                        tpg, tmg = df3['총수익금액'].sum(), df3['총손실금액'].sum()
                        ttsg = df3['수익금합계'].sum()
                        df2.loc[month] = month, tbg, tsg, tpg, tmg, sp, ttsg
                    month = str(int(month) - 89) if int(month[4:]) == 1 else str(int(month) - 1)
                self.UpdateTablewidget((ui_num[f'{gubun}누적상세'], df2))
            elif cmd == f'{gubun}연도별집계':
                df['연도'] = df['index'].apply(lambda x: str(x)[:4])
                df2 = pd.DataFrame(columns=columns_nd)
                lastyear = df['연도'][df.index[-1]]
                year = strf_time('%Y')
                while int(year) >= int(lastyear):
                    df3 = df[df['연도'] == year]
                    if len(df3) > 0:
                        tbg, tsg = df3['총매수금액'].sum(), df3['총매도금액'].sum()
                        sp = round((tsg / tbg - 1) * 100, 2)
                        tpg, tmg = df3['총수익금액'].sum(), df3['총손실금액'].sum()
                        ttsg = df3['수익금합계'].sum()
                        df2.loc[year] = year, tbg, tsg, tpg, tmg, sp, ttsg
                    year = str(int(year) - 1)
                self.UpdateTablewidget((ui_num[f'{gubun}누적상세'], df2))

    # =================================================================================================================

    def ssButtonClicked_01(self):
        con = sqlite3.connect(DB_BACKTEST)
        df  = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        self.ss_comboBoxxxx_01.clear()
        for table in df['name'].to_list()[::-1]:
            if 'stock' in table and '_bt_' in table:
                self.ss_comboBoxxxx_01.addItem(table)
        try:
            df = pd.read_sql(f"SELECT * FROM '{self.ss_comboBoxxxx_01.currentText()}'", con).set_index('index')
        except:
            pass
        else:
            self.UpdateTablewidget((ui_num['S상세기록'], df))
        con.close()

    def ssButtonClicked_02(self):
        con = sqlite3.connect(DB_BACKTEST)
        df  = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        self.ss_comboBoxxxx_02.clear()
        for table in df['name'].to_list()[::-1]:
            if 'stock' in table and ('o_' in table or 'ov_' in table or 'ovc_' in table or 'b_' in table or 'bv_' in table or 'bvc_' in table):
                self.ss_comboBoxxxx_02.addItem(table)
        try:
            df = pd.read_sql(f"SELECT * FROM '{self.ss_comboBoxxxx_02.currentText()}'", con).set_index('index')
        except:
            pass
        else:
            self.UpdateTablewidget((ui_num['S상세기록'], df))
        con.close()

    def ssButtonClicked_03(self):
        con = sqlite3.connect(DB_BACKTEST)
        df  = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        self.ss_comboBoxxxx_03.clear()
        for table in df['name'].to_list()[::-1]:
            if 'stock' in table and '_bt_' not in table and ('t_' in table or 'or_' in table or 'orv_' in table or 'orvc_' in table or 'br_' in table or 'brv_' in table or 'brvc_' in table):
                self.ss_comboBoxxxx_03.addItem(table)
        try:
            df = pd.read_sql(f"SELECT * FROM '{self.ss_comboBoxxxx_03.currentText()}'", con).set_index('index')
        except:
            pass
        else:
            self.UpdateTablewidget((ui_num['S상세기록'], df))
        con.close()

    def ssButtonClicked_04(self):
        comboBox = None
        if self.focusWidget() == self.ss_pushButtonn_02:
            comboBox = self.ss_comboBoxxxx_01
        elif self.focusWidget() == self.ss_pushButtonn_04:
            comboBox = self.ss_comboBoxxxx_02
        elif self.focusWidget() == self.ss_pushButtonn_06:
            comboBox = self.ss_comboBoxxxx_03

        if comboBox is None:
            return

        file_name = comboBox.currentText()

        try:
            image1 = Image.open(f"{GRAPH_PATH}/{file_name}.png")
            image2 = Image.open(f"{GRAPH_PATH}/{file_name}_.png")
            image1.show()
            image2.show()
        except:
            QMessageBox.critical(self, '오류 알림', '저장된 그래프 파일이 존재하지 않습니다.\n')

    def ssButtonClicked_05(self):
        if not self.dialog_comp.isVisible():
            self.dialog_comp.show()

            con = sqlite3.connect(DB_BACKTEST)
            df  = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
            con.close()

            if len(df) > 0:
                self.backdetail_list = [x for x in df['name'].to_list()[::-1] if 'stock' in x and ('t_' in x or 'v_' in x or 'c_' in x or 'vc_' in x)]
                if len(self.backdetail_list) > 0:
                    self.backcheckbox_list = []
                    count = len(self.backdetail_list)
                    self.cp_tableWidget_01.setRowCount(count)
                    for i, backdetailname in enumerate(self.backdetail_list):
                        checkBox = self.wc.setCheckBox(backdetailname, self)
                        self.backcheckbox_list.append(checkBox)
                        self.cp_tableWidget_01.setCellWidget(i, 0, checkBox)
                    if count < 40:
                        self.cp_tableWidget_01.setRowCount(40)
        else:
            self.dialog_comp.close()

    def ssButtonClicked_06(self):
        buttonReply = QMessageBox.question(
            self, '백테스트 중지', '백테스트를 중지합니다.\n계속하시겠습니까?\n',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if buttonReply == QMessageBox.Yes:
            self.BacktestProcessKill()
            self.ss_progressBar_01.setValue(0)
            self.ss_progressBar_01.setFormat('%p%')
            self.back_scount  = 0
            self.back_schedul = False
            self.ssicon_alert = False
            self.main_btn_list[2].setIcon(self.icon_stocks)

    # =================================================================================================================

    def csButtonClicked_01(self):
        con = sqlite3.connect(DB_BACKTEST)
        df  = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        self.cs_comboBoxxxx_01.clear()
        for table in df['name'].to_list()[::-1]:
            if 'coin' in table and '_bt_' in table:
                self.cs_comboBoxxxx_01.addItem(table)
        try:
            df = pd.read_sql(f"SELECT * FROM '{self.cs_comboBoxxxx_01.currentText()}'", con).set_index('index')
        except:
            pass
        else:
            self.UpdateTablewidget((ui_num['C상세기록'], df))
        con.close()

    def csButtonClicked_02(self):
        con = sqlite3.connect(DB_BACKTEST)
        df  = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        self.cs_comboBoxxxx_02.clear()
        for table in df['name'].to_list()[::-1]:
            if 'coin' in table and ('o_' in table or 'ov_' in table or 'ovc_' in table or 'b_' in table or 'bv_' in table or 'bvc_' in table):
                self.cs_comboBoxxxx_02.addItem(table)
        try:
            df = pd.read_sql(f"SELECT * FROM '{self.cs_comboBoxxxx_02.currentText()}'", con).set_index('index')
        except:
            pass
        else:
            self.UpdateTablewidget((ui_num['C상세기록'], df))
        con.close()

    def csButtonClicked_03(self):
        con = sqlite3.connect(DB_BACKTEST)
        df  = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
        self.cs_comboBoxxxx_03.clear()
        for table in df['name'].to_list()[::-1]:
            if 'coin' in table and '_bt_' not in table and ('t_' in table or 'or_' in table or 'orv_' in table or 'orvc_' in table or 'br_' in table or 'brv_' in table or 'brvc_' in table):
                self.cs_comboBoxxxx_03.addItem(table)
        try:
            df = pd.read_sql(f"SELECT * FROM '{self.cs_comboBoxxxx_03.currentText()}'", con).set_index('index')
        except:
            pass
        else:
            self.UpdateTablewidget((ui_num['C상세기록'], df))
        con.close()

    def csButtonClicked_04(self):
        comboBox = None
        if self.focusWidget() == self.cs_pushButtonn_02:
            comboBox = self.cs_comboBoxxxx_01
        elif self.focusWidget() == self.cs_pushButtonn_04:
            comboBox = self.cs_comboBoxxxx_02
        elif self.focusWidget() == self.cs_pushButtonn_06:
            comboBox = self.cs_comboBoxxxx_03

        if comboBox is None:
            return

        file_name = comboBox.currentText()

        try:
            image1 = Image.open(f"{GRAPH_PATH}/{file_name}.png")
            image2 = Image.open(f"{GRAPH_PATH}/{file_name}_.png")
            image1.show()
            image2.show()
        except:
            QMessageBox.critical(self, '오류 알림', '저장된 그래프 파일이 존재하지 않습니다.\n')

    def csButtonClicked_05(self):
        if not self.dialog_comp.isVisible():
            self.dialog_comp.show()

            con = sqlite3.connect(DB_BACKTEST)
            df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
            con.close()

            if len(df) > 0:
                self.backdetail_list = [x for x in df['name'].to_list()[::-1] if 'coin' in x and ('t_' in x or 'v_' in x or 'c_' in x or 'h_' in x)]

            if len(self.backdetail_list) > 0:
                self.backcheckbox_list = []
                count = len(self.backdetail_list)
                self.cp_tableWidget_01.setRowCount(count)
                for i, backdetailname in enumerate(self.backdetail_list):
                    checkBox = self.wc.setCheckBox(backdetailname, self)
                    self.backcheckbox_list.append(checkBox)
                    self.cp_tableWidget_01.setCellWidget(i, 0, checkBox)
                if count < 40:
                    self.cp_tableWidget_01.setRowCount(40)
        else:
            self.dialog_comp.close()

    def csButtonClicked_06(self):
        buttonReply = QMessageBox.question(
            self, '백테스트 중지', '백테스트를 중지합니다.\n계속하시겠습니까?\n',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if buttonReply == QMessageBox.Yes:
            self.BacktestProcessKill()
            self.cs_pushButtonn_08.setStyleSheet(style_bc_dk)
            self.cs_progressBar_01.setValue(0)
            self.cs_progressBar_01.setFormat('%p%')
            self.back_scount  = 0
            self.back_schedul = False
            self.csicon_alert = False
            self.main_btn_list[3].setIcon(self.icon_coins)

    # =================================================================================================================

    def szooButtonClicked_01(self):
        if self.svj_pushButton_01.isVisible():
            if self.szoo_pushButon_01.text() == '확대(esc)':
                self.szoo_pushButon_01.setText('축소(esc)')
                self.szoo_pushButon_01.setGeometry(952, 15, 50, 20)
                self.ss_textEditttt_01.setGeometry(7, 10, 1000, 1347 if self.extend_window else 740)
                self.ss_textEditttt_02.setVisible(False)
                self.szoo_pushButon_02.setVisible(False)
            else:
                self.szoo_pushButon_01.setText('확대(esc)')
                self.szoo_pushButon_01.setGeometry(952, 15, 50, 20)
                self.ss_textEditttt_01.setGeometry(7, 10, 1000, 740 if self.extend_window else 463)
                self.ss_textEditttt_02.setVisible(True)
                self.szoo_pushButon_02.setVisible(True)
        else:
            if self.szoo_pushButon_01.text() == '확대(esc)':
                self.szoo_pushButon_01.setText('축소(esc)')
                self.szoo_pushButon_01.setGeometry(952, 15, 50, 20)
                self.ss_textEditttt_03.setGeometry(7, 10, 1000, 1347 if self.extend_window else 740)
                self.ss_textEditttt_04.setVisible(False)
                if self.sva_pushButton_01.isVisible():
                    self.ss_textEditttt_06.setVisible(False)
                else:
                    self.ss_textEditttt_05.setVisible(False)
                self.szoo_pushButon_02.setVisible(False)
            else:
                self.szoo_pushButon_01.setText('확대(esc)')
                self.szoo_pushButon_01.setGeometry(599, 15, 50, 20)
                self.ss_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
                self.ss_textEditttt_04.setVisible(True)
                if self.sva_pushButton_01.isVisible():
                    self.ss_textEditttt_06.setVisible(True)
                else:
                    self.ss_textEditttt_05.setVisible(True)
                self.szoo_pushButon_02.setVisible(True)

    def szooButtonClicked_02(self):
        if self.svj_pushButton_01.isVisible():
            if self.szoo_pushButon_02.text() == '확대(esc)':
                self.szoo_pushButon_02.setText('축소(esc)')
                self.szoo_pushButon_02.setGeometry(952, 15, 50, 20)
                self.ss_textEditttt_02.setGeometry(7, 10, 1000, 1347 if self.extend_window else 740)
                self.ss_textEditttt_01.setVisible(False)
                self.szoo_pushButon_01.setVisible(False)
            else:
                self.szoo_pushButon_02.setText('확대(esc)')
                self.szoo_pushButon_02.setGeometry(952, 761 if self.extend_window else 483, 50, 20)
                self.ss_textEditttt_02.setGeometry(7, 756 if self.extend_window else 480, 1000, 602 if self.extend_window else 272)
                self.ss_textEditttt_01.setVisible(True)
                self.szoo_pushButon_01.setVisible(True)
        else:
            if self.szoo_pushButon_02.text() == '확대(esc)':
                self.szoo_pushButon_02.setText('축소(esc)')
                self.szoo_pushButon_02.setGeometry(952, 15, 50, 20)
                self.ss_textEditttt_04.setGeometry(7, 10, 1000, 1347 if self.extend_window else 740)
                self.ss_textEditttt_03.setVisible(False)
                if self.sva_pushButton_01.isVisible():
                    self.ss_textEditttt_06.setVisible(False)
                else:
                    self.ss_textEditttt_05.setVisible(False)
                self.szoo_pushButon_01.setVisible(False)
            else:
                self.szoo_pushButon_02.setText('확대(esc)')
                self.szoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)
                self.ss_textEditttt_04.setGeometry(7, 756 if self.extend_window else 480, 647, 602 if self.extend_window else 272)
                self.ss_textEditttt_03.setVisible(True)
                if self.sva_pushButton_01.isVisible():
                    self.ss_textEditttt_06.setVisible(True)
                else:
                    self.ss_textEditttt_05.setVisible(True)
                self.szoo_pushButon_01.setVisible(True)

    # =================================================================================================================

    def czooButtonClicked_01(self):
        if self.cvj_pushButton_01.isVisible():
            if self.czoo_pushButon_01.text() == '확대(esc)':
                self.czoo_pushButon_01.setText('축소(esc)')
                self.czoo_pushButon_01.setGeometry(952, 15, 50, 20)
                self.cs_textEditttt_01.setGeometry(7, 10, 1000, 1347 if self.extend_window else 740)
                self.cs_textEditttt_02.setVisible(False)
                self.czoo_pushButon_02.setVisible(False)
            else:
                self.czoo_pushButon_01.setText('확대(esc)')
                self.czoo_pushButon_01.setGeometry(952, 15, 50, 20)
                self.cs_textEditttt_01.setGeometry(7, 10, 1000, 740 if self.extend_window else 463)
                self.cs_textEditttt_02.setVisible(True)
                self.czoo_pushButon_02.setVisible(True)
        else:
            if self.czoo_pushButon_01.text() == '확대(esc)':
                self.czoo_pushButon_01.setText('축소(esc)')
                self.czoo_pushButon_01.setGeometry(952, 15, 50, 20)
                self.cs_textEditttt_03.setGeometry(7, 10, 1000, 1347 if self.extend_window else 740)
                self.cs_textEditttt_04.setVisible(False)
                if self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_06.setVisible(False)
                else:
                    self.cs_textEditttt_05.setVisible(False)
                self.czoo_pushButon_02.setVisible(False)
            else:
                self.czoo_pushButon_01.setText('확대(esc)')
                self.czoo_pushButon_01.setGeometry(599, 15, 50, 20)
                self.cs_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
                self.cs_textEditttt_04.setVisible(True)
                if self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_06.setVisible(True)
                else:
                    self.cs_textEditttt_05.setVisible(True)
                self.czoo_pushButon_02.setVisible(True)

    def czooButtonClicked_02(self):
        if self.cvj_pushButton_01.isVisible():
            if self.czoo_pushButon_02.text() == '확대(esc)':
                self.czoo_pushButon_02.setText('축소(esc)')
                self.czoo_pushButon_02.setGeometry(952, 15, 50, 20)
                self.cs_textEditttt_02.setGeometry(7, 10, 1000, 1347 if self.extend_window else 740)
                self.cs_textEditttt_01.setVisible(False)
                self.czoo_pushButon_01.setVisible(False)
            else:
                self.czoo_pushButon_02.setText('확대(esc)')
                self.czoo_pushButon_02.setGeometry(952, 761 if self.extend_window else 483, 50, 20)
                self.cs_textEditttt_02.setGeometry(7, 756 if self.extend_window else 480, 1000, 602 if self.extend_window else 272)
                self.cs_textEditttt_01.setVisible(True)
                self.czoo_pushButon_01.setVisible(True)
        else:
            if self.czoo_pushButon_02.text() == '확대(esc)':
                self.czoo_pushButon_02.setText('축소(esc)')
                self.czoo_pushButon_02.setGeometry(952, 15, 50, 20)
                self.cs_textEditttt_04.setGeometry(7, 10, 1000, 1347 if self.extend_window else 740)
                self.cs_textEditttt_03.setVisible(False)
                if self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_06.setVisible(False)
                else:
                    self.cs_textEditttt_05.setVisible(False)
                self.czoo_pushButon_01.setVisible(False)
            else:
                self.czoo_pushButon_02.setText('확대(esc)')
                self.czoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)
                self.cs_textEditttt_04.setGeometry(7, 756 if self.extend_window else 478, 647, 602 if self.extend_window else 272)
                self.cs_textEditttt_03.setVisible(True)
                if self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_06.setVisible(True)
                else:
                    self.cs_textEditttt_05.setVisible(True)
                self.czoo_pushButon_01.setVisible(True)

    # =================================================================================================================

    def Activated_01(self):
        table_name, ui_name_ = None, None
        if self.focusWidget() == self.ss_comboBoxxxx_01:
            table_name = self.ss_comboBoxxxx_01.currentText()
            ui_name_   = 'S상세기록'
        elif self.focusWidget() == self.ss_comboBoxxxx_02:
            table_name = self.ss_comboBoxxxx_02.currentText()
            ui_name_   = 'S상세기록'
        elif self.focusWidget() == self.ss_comboBoxxxx_03:
            table_name = self.ss_comboBoxxxx_03.currentText()
            ui_name_   = 'S상세기록'
        elif self.focusWidget() == self.cs_comboBoxxxx_01:
            table_name = self.cs_comboBoxxxx_01.currentText()
            ui_name_   = 'C상세기록'
        elif self.focusWidget() == self.cs_comboBoxxxx_02:
            table_name = self.cs_comboBoxxxx_02.currentText()
            ui_name_   = 'C상세기록'
        elif self.focusWidget() == self.cs_comboBoxxxx_03:
            table_name = self.cs_comboBoxxxx_03.currentText()
            ui_name_   = 'C상세기록'
        if table_name is None:
            return

        con = sqlite3.connect(DB_BACKTEST)
        df  = pd.read_sql(f"SELECT * FROM '{table_name}'", con).set_index('index')
        con.close()
        self.UpdateTablewidget((ui_num[ui_name_], df))

    def Activated_02(self):
        name = self.sj_set_comBoxx_01.currentText()
        self.sj_set_liEditt_01.setText(name)

    # =================================================================================================================

    def sActivated_01(self):
        strategy_name = self.svjb_comboBoxx_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM stockbuy WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.ss_textEditttt_01.clear()
                self.ss_textEditttt_01.append(df['전략코드'][strategy_name])
                self.svjb_lineEditt_01.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '전략이 DB에 존재하지 않습니다.\n전략을 다시 로딩하십시오.\n')

    def sActivated_02(self):
        strategy_name = self.svjs_comboBoxx_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM stocksell WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.ss_textEditttt_02.clear()
                self.ss_textEditttt_02.append(df['전략코드'][strategy_name])
                self.svjs_lineEditt_01.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '전략이 DB에 존재하지 않습니다.\n전략을 다시 로딩하십시오.\n')

    def sActivated_03(self):
        strategy_name = self.svc_comboBoxxx_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM stockoptibuy WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.ss_textEditttt_03.clear()
                self.ss_textEditttt_03.append(df['전략코드'][strategy_name])
                self.svc_lineEdittt_01.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '전략이 DB에 존재하지 않습니다.\n전략을 다시 로딩하십시오.\n')

    def sActivated_04(self):
        strategy_name = self.svc_comboBoxxx_02.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM stockoptivars WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.ss_textEditttt_05.clear()
                self.ss_textEditttt_05.append(df['전략코드'][strategy_name])
                self.svc_lineEdittt_02.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '범위가 DB에 존재하지 않습니다.\n범위을 다시 로딩하십시오.\n')

    def sActivated_05(self):
        strategy_name = self.svc_comboBoxxx_08.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM stockoptisell WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.ss_textEditttt_04.clear()
                self.ss_textEditttt_04.append(df['전략코드'][strategy_name])
                self.svc_lineEdittt_03.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '전략이 DB에 존재하지 않습니다.\n전략을 다시 로딩하십시오.\n')

    def sActivated_06(self):
        strategy_name = self.sva_comboBoxxx_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM stockvars WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.ss_textEditttt_06.clear()
                self.ss_textEditttt_06.append(df['전략코드'][strategy_name])
                self.sva_lineEdittt_01.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '범위가 DB에 존재하지 않습니다.\n범위을 다시 로딩하십시오.\n')

    def sActivated_07(self):
        strategy_name = self.svo_comboBoxxx_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM stockbuyconds WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.ss_textEditttt_07.clear()
                self.ss_textEditttt_07.append(df['전략코드'][strategy_name])
                self.svo_lineEdittt_01.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '조건이 DB에 존재하지 않습니다.\n조건을 다시 로딩하십시오.\n')

    def sActivated_08(self):
        strategy_name = self.svo_comboBoxxx_02.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM stocksellconds WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.ss_textEditttt_08.clear()
                self.ss_textEditttt_08.append(df['전략코드'][strategy_name])
                self.svo_lineEdittt_02.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '조건이 DB에 존재하지 않습니다.\n조건을 다시 로딩하십시오.\n')

    def sActivated_09(self):
        strategy_name = self.sj_stock_cbBox_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM stockoptibuy WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                optivars = [var for var in list(df.loc[strategy_name])[1:] if var != 9999. and var is not None]
                QMessageBox.warning(
                    self, '경고',
                    '최적화용 전략 선택시 최적값으로 전략이 실행됩니다.\n'
                    '다음 변수값을 확인하십시오\n'
                    f'{optivars}\n'
                    f'매도전략 또한 반드시 최적화용 전략으로 변경하십시오.\n'
                    f'최적화 백테스트를 실행할 경우 자동으로 변경됩니다.\n'
                )

    def sActivated_10(self):
        strategy_name = self.sj_stock_cbBox_03.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM stockoptibuy WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                optivars = [var for var in list(df.loc[strategy_name])[1:] if var != 9999. and var is not None]
                QMessageBox.warning(
                    self, '경고',
                    '최적화용 전략 선택시 최적값으로 전략이 실행됩니다.\n'
                    '다음 변수값을 확인하십시오\n'
                    f'{optivars}\n'
                    f'매도전략 또한 반드시 최적화용 전략으로 변경하십시오.\n'
                    f'최적화 백테스트를 실행할 경우 자동으로 변경됩니다.\n'
                )

    def oActivated_01(self):
        name = self.od_comboBoxxxxx_01.currentText()
        self.od_comboBoxxxxx_02.clear()
        if 'KRW' in name:
            items = ['지정가', '시장가']
        elif 'USDT' in name:
            items = ['시장가', '지정가', '지정가IOC', '지정가FOK']
        else:
            items = ['지정가', '시장가', '최유리지정가', '최우선지정가', '지정가IOC', '시장가IOC', '최유리IOC', '지정가FOK', '시장가FOK', '최유리FOK']
        for item in items:
            self.od_comboBoxxxxx_02.addItem(item)

    # =================================================================================================================

    def cActivated_01(self):
        strategy_name = self.cvjb_comboBoxx_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM coinbuy WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cs_textEditttt_01.clear()
                self.cs_textEditttt_01.append(df['전략코드'][strategy_name])
                self.cvjb_lineEditt_01.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '전략이 DB에 존재하지 않습니다.\n전략을 다시 로딩하십시오.\n')

    def cActivated_02(self):
        strategy_name = self.cvjs_comboBoxx_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM coinsell WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cs_textEditttt_02.clear()
                self.cs_textEditttt_02.append(df['전략코드'][strategy_name])
                self.cvjs_lineEditt_01.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '전략이 DB에 존재하지 않습니다.\n전략을 다시 로딩하십시오.\n')

    def cActivated_03(self):
        strategy_name = self.cvc_comboBoxxx_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM coinoptibuy WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cs_textEditttt_03.clear()
                self.cs_textEditttt_03.append(df['전략코드'][strategy_name])
                self.cvc_lineEdittt_01.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '전략이 DB에 존재하지 않습니다.\n전략을 다시 로딩하십시오.\n')

    def cActivated_04(self):
        strategy_name = self.cvc_comboBoxxx_02.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM coinoptivars WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cs_textEditttt_05.clear()
                self.cs_textEditttt_05.append(df['전략코드'][strategy_name])
                self.cvc_lineEdittt_02.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '범위가 DB에 존재하지 않습니다.\n범위을 다시 로딩하십시오.\n')

    def cActivated_05(self):
        strategy_name = self.cvc_comboBoxxx_08.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM coinoptisell WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cs_textEditttt_04.clear()
                self.cs_textEditttt_04.append(df['전략코드'][strategy_name])
                self.cvc_lineEdittt_03.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '전략이 DB에 존재하지 않습니다.\n전략을 다시 로딩하십시오.\n')

    def cActivated_06(self):
        strategy_name = self.cva_comboBoxxx_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM coinvars WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cs_textEditttt_06.clear()
                self.cs_textEditttt_06.append(df['전략코드'][strategy_name])
                self.cva_lineEdittt_01.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '범위가 DB에 존재하지 않습니다.\n범위을 다시 로딩하십시오.\n')

    def cActivated_07(self):
        strategy_name = self.cvo_comboBoxxx_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM coinbuyconds WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cs_textEditttt_07.clear()
                self.cs_textEditttt_07.append(df['전략코드'][strategy_name])
                self.cvo_lineEdittt_01.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '조건이 DB에 존재하지 않습니다.\n조건을 다시 로딩하십시오.\n')

    def cActivated_08(self):
        strategy_name = self.cvo_comboBoxxx_02.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM coinsellconds WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cs_textEditttt_08.clear()
                self.cs_textEditttt_08.append(df['전략코드'][strategy_name])
                self.cvo_lineEdittt_02.setText(strategy_name)
            else:
                QMessageBox.critical(self, '오류 알림', '조건이 DB에 존재하지 않습니다.\n조건을 다시 로딩하십시오.\n')

    def cActivated_09(self):
        strategy_name = self.sj_coin_comBox_01.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM coinoptibuy WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                optivars = [var for var in list(df.loc[strategy_name])[1:] if var != 9999. and var is not None]
                QMessageBox.warning(
                    self, '경고',
                    '최적화용 전략 선택시 최적값으로 전략이 실행됩니다.\n'
                    '다음 변수값을 확인하십시오\n'
                    f'{optivars}\n'
                    f'매도전략 또한 반드시 최적화용 전략으로 변경하십시오.\n'
                    f'최적화 백테스트를 실행할 경우 자동으로 변경됩니다.\n'
                )

    def cActivated_10(self):
        strategy_name = self.sj_coin_comBox_03.currentText()
        if strategy_name != '':
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql(f"SELECT * FROM coinoptibuy WHERE `index` = '{strategy_name}'", con).set_index('index')
            con.close()
            if len(df) > 0:
                optivars = [var for var in list(df.loc[strategy_name])[1:] if var != 9999. and var is not None]
                QMessageBox.warning(
                    self, '경고',
                    '최적화용 전략 선택시 최적값으로 전략이 실행됩니다.\n'
                    '다음 변수값을 확인하십시오\n'
                    f'{optivars}\n'
                    f'매도전략 또한 반드시 최적화용 전략으로 변경하십시오.\n'
                    f'최적화 백테스트를 실행할 경우 자동으로 변경됩니다.\n'
                )

    def cActivated_11(self):
        coin_trade_name = self.sj_main_comBox_02.currentText()
        if coin_trade_name != '업비트':
            self.sj_main_liEdit_03.setText('5')
            self.sj_main_liEdit_04.setText('10')

    def cActivated_12(self):
        if self.dict_set['거래소'] == '바이낸스선물' and self.sj_main_comBox_03.currentText() == '교차':
            self.sj_main_comBox_03.setCurrentText('격리')
            QMessageBox.warning(self, '경고', '현재 바이낸스 선물 마진타입은 격리타입만 지원합니다.\n')

    def cActivated_13(self):
        if self.dict_set['거래소'] == '바이낸스선물' and self.sj_main_comBox_04.currentText() == '양방향':
            self.sj_main_comBox_04.setCurrentText('단방향')
            QMessageBox.warning(self, '경고', '현재 바이낸스 선물 포지션모드는 단방향만 지원합니다.\n')

    # =================================================================================================================

    def bActivated_01(self):
        try:
            gubun = self.list_checkBoxxxxxx.index(self.dialog_scheduler.focusWidget())
        except:
            gubun = self.list_gcomboBoxxxxx.index(self.dialog_scheduler.focusWidget())
        gubun2 = 'stock' if self.sd_pushButtonnn_01.text() == '주식' else 'coin'

        self.list_bcomboBoxxxxx[gubun].clear()
        self.list_scomboBoxxxxx[gubun].clear()
        self.list_vcomboBoxxxxx[gubun].clear()
        self.list_p1comboBoxxxx[gubun].clear()
        self.list_p2comboBoxxxx[gubun].clear()
        self.list_p3comboBoxxxx[gubun].clear()
        self.list_p4comboBoxxxx[gubun].clear()
        self.list_tcomboBoxxxxx[gubun].clear()
        back_name = self.list_gcomboBoxxxxx[gubun].currentText()
        if back_name == '백테스트':
            con = sqlite3.connect(DB_STRATEGY)
            df = pd.read_sql(f'SELECT * FROM {gubun2}buy', con).set_index('index')
            if len(df) > 0:
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.list_bcomboBoxxxxx[gubun].addItem(index)

            df = pd.read_sql(f'SELECT * FROM {gubun2}sell', con).set_index('index')
            con.close()
            if len(df) > 0:
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.list_scomboBoxxxxx[gubun].addItem(index)
            self.list_alineEdittttt[gubun].setText('30')
        else:
            con = sqlite3.connect(DB_STRATEGY)
            if '조건' in back_name:
                df = pd.read_sql(f'SELECT * FROM {gubun2}buyconds', con).set_index('index')
                if len(df) > 0:
                    indexs = list(df.index)
                    indexs.sort()
                    for i, index in enumerate(indexs):
                        self.list_bcomboBoxxxxx[gubun].addItem(index)

                df = pd.read_sql(f'SELECT * FROM {gubun2}sellconds', con).set_index('index')
                if len(df) > 0:
                    indexs = list(df.index)
                    indexs.sort()
                    for i, index in enumerate(indexs):
                        self.list_scomboBoxxxxx[gubun].addItem(index)
                self.list_alineEdittttt[gubun].setText('30')
            else:
                df = pd.read_sql(f'SELECT * FROM {gubun2}optibuy', con).set_index('index')
                if len(df) > 0:
                    indexs = list(df.index)
                    indexs.sort()
                    for i, index in enumerate(indexs):
                        self.list_bcomboBoxxxxx[gubun].addItem(index)

                df = pd.read_sql(f'SELECT * FROM {gubun2}optisell', con).set_index('index')
                if len(df) > 0:
                    indexs = list(df.index)
                    indexs.sort()
                    for i, index in enumerate(indexs):
                        self.list_scomboBoxxxxx[gubun].addItem(index)

                if 'GA' in back_name:
                    df = pd.read_sql(f'SELECT * FROM {gubun2}vars', con).set_index('index')
                else:
                    df = pd.read_sql(f'SELECT * FROM {gubun2}optivars', con).set_index('index')
                if len(df) > 0:
                    indexs = list(df.index)
                    indexs.sort()
                    for i, index in enumerate(indexs):
                        self.list_vcomboBoxxxxx[gubun].addItem(index)
                self.list_alineEdittttt[gubun].setText('')
            con.close()

            for item in opti_standard:
                self.list_tcomboBoxxxxx[gubun].addItem(item)
            for item in train_period:
                self.list_p1comboBoxxxx[gubun].addItem(item)
            for item in valid_period:
                self.list_p2comboBoxxxx[gubun].addItem(item)
            for item in test_period:
                self.list_p3comboBoxxxx[gubun].addItem(item)
            if 'GA' not in back_name and '조건' not in back_name:
                for item in optimized_count:
                    self.list_p4comboBoxxxx[gubun].addItem(item)

    def bActivated_02(self):
        if self.sd_scheckBoxxxx_01.isChecked():
            list_comboBox = None
            if self.dialog_scheduler.focusWidget() in self.list_p1comboBoxxxx:
                list_comboBox = self.list_p1comboBoxxxx
            elif self.dialog_scheduler.focusWidget() in self.list_p2comboBoxxxx:
                list_comboBox = self.list_p2comboBoxxxx
            elif self.dialog_scheduler.focusWidget() in self.list_p3comboBoxxxx:
                list_comboBox = self.list_p3comboBoxxxx
            elif self.dialog_scheduler.focusWidget() in self.list_p4comboBoxxxx:
                list_comboBox = self.list_p4comboBoxxxx
            elif self.dialog_scheduler.focusWidget() in self.list_tcomboBoxxxxx:
                list_comboBox = self.list_tcomboBoxxxxx
            elif self.dialog_scheduler.focusWidget() in self.list_bcomboBoxxxxx:
                list_comboBox = self.list_bcomboBoxxxxx
            elif self.dialog_scheduler.focusWidget() in self.list_scomboBoxxxxx:
                list_comboBox = self.list_scomboBoxxxxx
            elif self.dialog_scheduler.focusWidget() in self.list_vcomboBoxxxxx:
                list_comboBox = self.list_vcomboBoxxxxx

            if list_comboBox is not None:
                index = list_comboBox.index(self.dialog_scheduler.focusWidget())
                text  = list_comboBox[index].currentText()
                back_type = self.list_gcomboBoxxxxx[index].currentText()
                for i, combobox in enumerate(self.list_gcomboBoxxxxx):
                    if i != index and combobox.currentText() == back_type:
                        list_comboBox[i].setCurrentText(text)

        if self.dialog_scheduler.focusWidget() in self.list_p1comboBoxxxx:
            index = self.list_p1comboBoxxxx.index(self.dialog_scheduler.focusWidget())
            if '전진분석' in self.list_gcomboBoxxxxx[index].currentText() and self.list_p1comboBoxxxx[index].currentText() == 'ALL':
                self.list_p1comboBoxxxx[index].setCurrentText('3')
                QMessageBox.critical(self.dialog_scheduler, '오류 알림', '전진분석은 학습기간을 전체로 설정할 수 없습니다.\n')

    def bActivated_03(self):
        try:
            for checkbox in self.list_checkBoxxxxxx:
                checkbox.setFocus()
                checkbox.setChecked(False)
            if self.sd_scheckBoxxxx_01.isChecked():
                self.sd_scheckBoxxxx_01.nextCheckState()
            schedule_name = self.sd_dcomboBoxxxx_01.currentText()
            self.sd_dlineEditttt_01.setText(schedule_name)
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql('SELECT * FROM schedule', con).set_index('index')
            con.close()
            schedule = df['스케쥴'][schedule_name]
            schedule = schedule.split('^')
            last = len(schedule) - 1
            for i, values_text in enumerate(schedule):
                if i != last:
                    values = values_text.split(';')
                    self.list_checkBoxxxxxx[i].setFocus()
                    self.list_checkBoxxxxxx[i].setChecked(True)
                    self.list_gcomboBoxxxxx[i].setFocus()
                    self.list_gcomboBoxxxxx[i].setCurrentText(values[0])
                    self.list_slineEdittttt[i].setFocus()
                    self.list_slineEdittttt[i].setText(values[1])
                    self.list_elineEdittttt[i].setFocus()
                    self.list_elineEdittttt[i].setText(values[2])
                    self.list_blineEdittttt[i].setFocus()
                    self.list_blineEdittttt[i].setText(values[3])
                    self.list_alineEdittttt[i].setFocus()
                    self.list_alineEdittttt[i].setText(values[4])
                    self.list_p1comboBoxxxx[i].setFocus()
                    self.list_p1comboBoxxxx[i].setCurrentText(values[5])
                    self.list_p2comboBoxxxx[i].setFocus()
                    self.list_p2comboBoxxxx[i].setCurrentText(values[6])
                    self.list_p3comboBoxxxx[i].setFocus()
                    self.list_p3comboBoxxxx[i].setCurrentText(values[7])
                    self.list_p4comboBoxxxx[i].setFocus()
                    self.list_p4comboBoxxxx[i].setCurrentText(values[8])
                    self.list_tcomboBoxxxxx[i].setFocus()
                    self.list_tcomboBoxxxxx[i].setCurrentText(values[9])
                    self.list_bcomboBoxxxxx[i].setFocus()
                    self.list_bcomboBoxxxxx[i].setCurrentText(values[10])
                    self.list_scomboBoxxxxx[i].setFocus()
                    self.list_scomboBoxxxxx[i].setCurrentText(values[11])
                    self.list_vcomboBoxxxxx[i].setFocus()
                    self.list_vcomboBoxxxxx[i].setCurrentText(values[12])
                else:
                    values = values_text.split(';')
                    self.sd_scheckBoxxxx_02.setChecked(True) if values[0] == '1' else self.sd_scheckBoxxxx_02.setChecked(False)
                    self.sd_oclineEdittt_01.setText(values[1])
                    self.sd_oclineEdittt_02.setText(values[2])
                    self.sd_oclineEdittt_03.setText(values[3])
        except:
            pass

    # =================================================================================================================

    def GetFixStrategy(self, strategy, gubun):
        if gubun == '매수':
            if self.focusWidget() in (self.svjb_pushButon_02, self.svc_pushButton_02, self.ss_textEditttt_01, self.ss_textEditttt_03, self.ss_textEditttt_07):
                if '\nif 매수:' in strategy:
                    strategy = strategy.split('\nif 매수:')[0] + stock_buy_signal
                elif 'self.tickdata' not in strategy and stock_buy_signal not in strategy:
                    strategy += '\n' + stock_buy_signal
            else:
                if self.dict_set['거래소'] == '업비트':
                    if '\nif 매수:' in strategy:
                        strategy = strategy.split('\nif 매수:')[0] + coin_buy_signal
                    elif coin_buy_signal not in strategy:
                        strategy += '\n' + coin_buy_signal
                else:
                    if '\nif BUY_LONG or SELL_SHORT:' in strategy:
                        strategy = strategy.split('\nif BUY_LONG or SELL_SHORT:')[0] + coin_future_buy_signal
                    elif coin_future_buy_signal not in strategy:
                        strategy += '\n' + coin_future_buy_signal
        else:
            if self.focusWidget() in (self.svjs_pushButon_02, self.svc_pushButton_10, self.ss_textEditttt_02, self.ss_textEditttt_04, self.ss_textEditttt_08):
                if '\nif 매도:' in strategy:
                    strategy = strategy.split('\nif 매도:')[0] + stock_sell_signal
                elif 'self.tickdata' not in strategy and stock_sell_signal not in strategy:
                    strategy += '\n' + stock_sell_signal
            else:
                if self.dict_set['거래소'] == '업비트':
                    if '\nif 매도:' in strategy:
                        strategy = strategy.split('\nif 매도:')[0] + coin_sell_signal
                    elif coin_sell_signal not in strategy:
                        strategy += '\n' + coin_sell_signal
                else:
                    if "\nif (포지션 == 'LONG' and SELL_LONG) or (포지션 == 'SHORT' and BUY_SHORT):" in strategy:
                        strategy = strategy.split("\nif (포지션 == 'LONG' and SELL_LONG) or (포지션 == 'SHORT' and BUY_SHORT):")[0] + coin_future_sell_signal
                    elif coin_future_sell_signal not in strategy:
                        strategy += '\n' + coin_future_sell_signal
        return strategy

    def GetOptivarsToGavars(self, opti_vars_text):
        ga_vars_text = ''
        try:
            self.vars = {}
            exec(compile(opti_vars_text, '<string>', 'exec'), None, locals())
            for i in range(len(self.vars)):
                ga_vars_text = f'{ga_vars_text}self.vars[{i}] = [['
                vars_start, vars_last, vars_gap = self.vars[i][0]
                vars_high = self.vars[i][1]
                vars_curr = vars_start
                if vars_start == vars_last:
                    ga_vars_text = f'{ga_vars_text}{vars_curr}], {vars_curr}]\n'
                elif vars_start < vars_last:
                    while vars_curr <= vars_last:
                        ga_vars_text = f'{ga_vars_text}{vars_curr}, '
                        vars_curr += vars_gap
                        if vars_gap < 0:
                            vars_curr = round(vars_curr, 1)
                    ga_vars_text = f'{ga_vars_text[:-2]}], {vars_high}]\n'
                else:
                    while vars_curr >= vars_last:
                        ga_vars_text = f'{ga_vars_text}{vars_curr}, '
                        vars_curr += vars_gap
                        if vars_gap < 0:
                            vars_curr = round(vars_curr, 1)
                    ga_vars_text = f'{ga_vars_text[:-2]}], {vars_high}]\n'
        except Exception as e:
            QMessageBox.critical(self, '오류 알림', f'{e}')

        return ga_vars_text[:-1]

    def GetGavarsToOptivars(self, ga_vars_text):
        opti_vars_text = ''
        try:
            self.vars = {}
            exec(compile(ga_vars_text, '<string>', 'exec'), None, locals())
            for i in range(len(self.vars)):
                if len(self.vars[i][0]) == 1:
                    vars_high  = self.vars[i][1]
                    vars_gap_  = 0
                    vars_start = vars_high
                    vars_end   = vars_high
                else:
                    vars_high, vars_gap = self.vars[i][1], self.vars[i][0][1] - self.vars[i][0][0]
                    if type(vars_gap) == float:
                        vars_gap = round(vars_gap, 1)
                    if vars_gap > 10:
                        vars_gap_  = int(vars_gap / 5)
                        vars_start = vars_high - vars_gap + vars_gap_
                        vars_end   = vars_high + vars_gap - vars_gap_
                    else:
                        vars_gap_  = round(self.vars[i][0][1] - self.vars[i][0][0], 1)
                        vars_start = self.vars[i][0][0]
                        vars_end   = self.vars[i][0][-1]
                opti_vars_text = f'{opti_vars_text}self.vars[{i}] = [[{vars_start}, {vars_end}, {vars_gap_}], {vars_high}]\n'
        except Exception as e:
            QMessageBox.critical(self, '오류 알림', f'{e}')

        return opti_vars_text[:-1]

    def GetStgtxtToVarstxt(self, buystg, sellstg):
        cnt = 1
        sellstg_str, buystg_str = '', ''
        if self.focusWidget() == self.svc_pushButton_24:
            if buystg != '' and '변수' in buystg:
                buystg = buystg.split('\n')
                for line in buystg:
                    if '변수' in line:
                        for text in line:
                            buystg_str += text
                            if buystg_str[-2:] == '변수':
                                buystg_str = buystg_str.replace('변수', f'self.vars[{cnt}]')
                                cnt += 1
                        buystg_str += '\n'
                    else:
                        buystg_str += line + '\n'
            if sellstg != '' and '변수' in sellstg:
                sellstg = sellstg.split('\n')
                for line in sellstg:
                    if '변수' in line:
                        for text in line:
                            sellstg_str += text
                            if sellstg_str[-2:] == '변수':
                                sellstg_str = sellstg_str.replace('변수', f'self.vars[{cnt}]')
                                cnt += 1
                        sellstg_str += '\n'
                    else:
                        sellstg_str += line + '\n'
        else:
            if sellstg != '' and '변수' in sellstg:
                sellstg = sellstg.split('\n')
                for line in sellstg:
                    if '변수' in line:
                        for text in line:
                            sellstg_str += text
                            if sellstg_str[-2:] == '변수':
                                sellstg_str = sellstg_str.replace('변수', f'self.vars[{cnt}]')
                                cnt += 1
                        sellstg_str += '\n'
                    else:
                        sellstg_str += line + '\n'
            if buystg != '' and '변수' in buystg:
                buystg = buystg.split('\n')
                for line in buystg:
                    if '변수' in line:
                        for text in line:
                            buystg_str += text
                            if buystg_str[-2:] == '변수':
                                buystg_str = buystg_str.replace('변수', f'self.vars[{cnt}]')
                                cnt += 1
                        buystg_str += '\n'
                    else:
                        buystg_str += line + '\n'

        return buystg_str[:-1], sellstg_str[:-1]

    @staticmethod
    def GetStgtxtSort(buystg, sellstg):
        buystg_str, sellstg_str = '', ''
        if buystg != '' and sellstg != '' and 'self.vars' in buystg and 'self.vars' in sellstg:
            buy_num  = int(buystg.split('self.vars[')[1].split(']')[0])
            sell_num = int(sellstg.split('self.vars[')[1].split(']')[0])
            cnt      = 1
            buystg   = buystg.split('\n')
            sellstg  = sellstg.split('\n')
            if buy_num < sell_num:
                for line in buystg:
                    if 'self.vars' in line and '#' not in line:
                        str_pass = False
                        for text in line:
                            if str_pass:
                                if text == ']':
                                    str_pass = False
                                else:
                                    continue
                            else:
                                buystg_str += text

                            if buystg_str[-5:] == 'vars[':
                                buystg_str += f'{cnt}]'
                                str_pass = True
                                cnt += 1
                        buystg_str += '\n'
                    else:
                        buystg_str += line + '\n'
                for line in sellstg:
                    if 'self.vars' in line and '#' not in line:
                        str_pass = False
                        for text in line:
                            if str_pass:
                                if text == ']':
                                    str_pass = False
                                else:
                                    continue
                            else:
                                sellstg_str += text

                            if sellstg_str[-5:] == 'vars[':
                                sellstg_str += f'{cnt}]'
                                str_pass = True
                                cnt += 1
                        sellstg_str += '\n'
                    else:
                        sellstg_str += line + '\n'
            else:
                for line in sellstg:
                    if 'self.vars' in line and '#' not in line:
                        str_pass = False
                        for text in line:
                            if str_pass:
                                if text == ']':
                                    str_pass = False
                                else:
                                    continue
                            else:
                                sellstg_str += text

                            if sellstg_str[-5:] == 'vars[':
                                sellstg_str += f'{cnt}]'
                                str_pass = True
                                cnt += 1
                        sellstg_str += '\n'
                    else:
                        sellstg_str += line + '\n'
                for line in buystg:
                    if 'self.vars' in line and '#' not in line:
                        str_pass = False
                        for text in line:
                            if str_pass:
                                if text == ']':
                                    str_pass = False
                                else:
                                    continue
                            else:
                                buystg_str += text

                            if buystg_str[-5:] == 'vars[':
                                buystg_str += f'{cnt}]'
                                str_pass = True
                                cnt += 1
                        buystg_str += '\n'
                    else:
                        buystg_str += line + '\n'

        return buystg_str[:-1], sellstg_str[:-1]

    @staticmethod
    def GetStgtxtSort2(optivars, gavars):
        optivars_str, gavars_str = '', ''
        if optivars != '' and 'self.vars' in optivars:
            cnt = 0
            optivars = optivars.split('\n')
            for line in optivars:
                if 'self.vars' in line and '#' not in line:
                    str_pass = False
                    for text in line:
                        if str_pass:
                            if text == ']':
                                str_pass = False
                            else:
                                continue
                        else:
                            optivars_str += text

                        if optivars_str[-5:] == 'vars[':
                            optivars_str += f'{cnt}]'
                            str_pass = True
                            cnt += 1
                    optivars_str += '\n'
                else:
                    optivars_str += line + '\n'
        if gavars != '' and 'self.vars' in gavars:
            cnt = 0
            gavars = gavars.split('\n')
            for line in gavars:
                if 'self.vars' in line and '#' not in line:
                    str_pass = False
                    for text in line:
                        if str_pass:
                            if text == ']':
                                str_pass = False
                            else:
                                continue
                        else:
                            gavars_str += text

                        if gavars_str[-5:] == 'vars[':
                            gavars_str += f'{cnt}]'
                            str_pass = True
                            cnt += 1
                    gavars_str += '\n'
                else:
                    gavars_str += line + '\n'

        return optivars_str[:-1], gavars_str[:-1]

    def stButtonClicked_01(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM back', con).set_index('index')
        con.close()
        std_text = df['최적화기준값제한'][0].split(';')
        self.st_lineEditttt_01.setText(std_text[0])
        self.st_lineEditttt_02.setText(std_text[1])
        self.st_lineEditttt_03.setText(std_text[2])
        self.st_lineEditttt_04.setText(std_text[3])
        self.st_lineEditttt_05.setText(std_text[4])
        self.st_lineEditttt_06.setText(std_text[5])
        self.st_lineEditttt_07.setText(std_text[6])
        self.st_lineEditttt_08.setText(std_text[7])
        self.st_lineEditttt_09.setText(std_text[8])
        self.st_lineEditttt_10.setText(std_text[9])
        self.st_lineEditttt_11.setText(std_text[10])
        self.st_lineEditttt_12.setText(std_text[11])
        self.st_lineEditttt_13.setText(std_text[12])
        self.st_lineEditttt_14.setText(std_text[13])

    def stButtonClicked_02(self):
        std_text1  = self.st_lineEditttt_01.text()
        std_text2  = self.st_lineEditttt_02.text()
        std_text3  = self.st_lineEditttt_03.text()
        std_text4  = self.st_lineEditttt_04.text()
        std_text5  = self.st_lineEditttt_05.text()
        std_text6  = self.st_lineEditttt_06.text()
        std_text7  = self.st_lineEditttt_07.text()
        std_text8  = self.st_lineEditttt_08.text()
        std_text9  = self.st_lineEditttt_09.text()
        std_text10 = self.st_lineEditttt_10.text()
        std_text11 = self.st_lineEditttt_11.text()
        std_text12 = self.st_lineEditttt_12.text()
        std_text13 = self.st_lineEditttt_13.text()
        std_text14 = self.st_lineEditttt_14.text()
        std_list   = [std_text1, std_text2, std_text3, std_text4, std_text5, std_text6, std_text7, std_text8, std_text9,
                      std_text10, std_text11, std_text12, std_text13, std_text14]
        if '' in std_list:
            QMessageBox.critical(self.dialog_std, '오류 알림', '일부 제한값이 공백상태입니다.\n')
        else:
            if proc_query.is_alive():
                std_list = ';'.join(std_list)
                query = f"UPDATE back SET 최적화기준값제한 = '{std_list}'"
                queryQ.put(('설정디비', query))
            self.dict_set['최적화기준값제한'] = std_list
            QMessageBox.information(self.dialog_std, '저장 완료', random.choice(famous_saying))

    # =================================================================================================================

    def svjbButtonClicked_01(self):
        if self.ss_textEditttt_01.isVisible():
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql('SELECT * FROM stockbuy', con).set_index('index')
            con.close()
            if len(df) > 0:
                self.svjb_comboBoxx_01.clear()
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.svjb_comboBoxx_01.addItem(index)
                    if i == 0:
                        self.svjb_lineEditt_01.setText(index)
                self.svjb_pushButon_04.setStyleSheet(style_bc_st)

    def svjbButtonClicked_02(self):
        strategy_name = self.svjb_lineEditt_01.text()
        strategy = self.ss_textEditttt_01.toPlainText()
        if 'self.tickcols' not in strategy:
            strategy = self.GetFixStrategy(strategy, '매수')

        if strategy_name == '':
            QMessageBox.critical(self, '오류 알림', '매수전략의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
        elif not text_not_in_special_characters(strategy_name):
            QMessageBox.critical(self, '오류 알림', '매수전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
        elif strategy == '':
            QMessageBox.critical(self, '오류 알림', '매수전략의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
        else:
            if 'self.tickcols' in strategy or (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest1(strategy):
                if proc_query.is_alive():
                    queryQ.put(('전략디비', f"DELETE FROM stockbuy WHERE `index` = '{strategy_name}'"))
                    df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                    queryQ.put(('전략디비', df, 'stockbuy', 'append'))
                self.svjb_pushButon_04.setStyleSheet(style_bc_st)
                QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def svjbButtonClicked_03(self):
        self.ss_textEditttt_01.clear()
        if not self.dict_set['주식일봉데이터'] and not self.dict_set['주식분봉데이터']:
            self.ss_textEditttt_01.append(stock_buy_var)
        else:
            self.ss_textEditttt_01.append(stock_buy_var_)
        self.svjb_pushButon_04.setStyleSheet(style_bc_st)

    def svjbButtonClicked_04(self):
        strategy = self.ss_textEditttt_01.toPlainText()
        if strategy == '':
            QMessageBox.critical(self, '오류 알림', '매수전략의 코드가 공백 상태입니다.\n')
        else:
            buttonReply = QMessageBox.question(
                self, '전략시작', '매수전략의 연산을 시작합니다. 계속하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                wdzservQ.put(('strategy', ('매수전략', strategy)))
                self.svjb_pushButon_04.setStyleSheet(style_bc_dk)
                self.svjb_pushButon_12.setStyleSheet(style_bc_st)

    def svjbButtonClicked_05(self):
        self.ss_textEditttt_01.append(stock_buy1)

    def svjbButtonClicked_06(self):
        self.ss_textEditttt_01.append(stock_buy2)

    def svjbButtonClicked_07(self):
        self.ss_textEditttt_01.append(stock_buy3)

    def svjbButtonClicked_08(self):
        self.ss_textEditttt_01.append(stock_buy4)

    def svjbButtonClicked_09(self):
        self.ss_textEditttt_01.append(stock_buy5)

    def svjbButtonClicked_10(self):
        self.ss_textEditttt_01.append(stock_buy6)

    def svjbButtonClicked_11(self):
        self.ss_textEditttt_01.append(stock_buy_signal)

    def svjbButtonClicked_12(self):
        wdzservQ.put(('strategy', '매수전략중지'))
        self.svjb_pushButon_12.setStyleSheet(style_bc_dk)
        self.svjb_pushButon_04.setStyleSheet(style_bc_st)

    def sChangeSvjButtonColor(self):
        for button in self.stock_editer_list:
            button.setStyleSheet(style_bc_dk if self.focusWidget() == button else style_bc_bs)

    def svjButtonClicked_01(self):
        self.ss_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
        self.ss_textEditttt_04.setGeometry(7, 756 if self.extend_window else 478, 647, 602 if self.extend_window else 272)
        self.ss_textEditttt_05.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)

        self.svc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.svc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.svc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.svc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.szoo_pushButon_01.setGeometry(599, 15, 50, 20)
        self.szoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)

        self.szoo_pushButon_01.setText('확대(esc)')
        self.szoo_pushButon_02.setText('확대(esc)')

        self.ss_textEditttt_01.setVisible(False)
        self.ss_textEditttt_02.setVisible(False)
        self.ss_textEditttt_03.setVisible(True)
        self.ss_textEditttt_04.setVisible(True)
        self.ss_textEditttt_05.setVisible(True)
        self.ss_textEditttt_06.setVisible(False)

        for item in self.stock_detail_list:
            item.setVisible(False)
        for item in self.stock_baklog_list:
            item.setVisible(False)
        for item in self.stock_datedt_list:
            item.setVisible(False)
        for item in self.stock_backte_list:
            item.setVisible(False)
        for item in self.stock_opcond_list:
            item.setVisible(False)
        for item in self.stock_gaopti_list:
            item.setVisible(False)
        for item in self.stock_rwftvd_list:
            item.setVisible(False)
        for item in self.stock_esczom_list:
            item.setVisible(True)
        for item in self.stock_optimz_list:
            item.setVisible(True)
        for item in self.stock_period_list:
            item.setVisible(True)
        for item in self.stock_optest_list:
            item.setVisible(True)

        self.svc_pushButton_03.setText('최적화 변수범위 로딩(F9)')
        self.svc_pushButton_04.setText('최적화 변수범위 저장(F12)')

        self.image_label1.setVisible(False)
        self.svc_labellllll_04.setText(testtext)
        self.svc_labellllll_05.setVisible(False)
        self.svc_pushButton_21.setVisible(False)
        self.svc_pushButton_22.setVisible(False)
        self.svc_pushButton_23.setVisible(False)
        self.svc_pushButton_24.setVisible(False)
        self.svc_pushButton_25.setVisible(False)
        self.svc_pushButton_26.setVisible(False)
        self.sChangeSvjButtonColor()

    def svjButtonClicked_02(self):
        self.ss_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
        self.ss_textEditttt_04.setGeometry(7, 756 if self.extend_window else 478, 647, 602 if self.extend_window else 272)
        self.ss_textEditttt_05.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)

        self.svc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.svc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.svc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.svc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.szoo_pushButon_01.setGeometry(599, 15, 50, 20)
        self.szoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)

        self.szoo_pushButon_01.setText('확대(esc)')
        self.szoo_pushButon_02.setText('확대(esc)')

        self.ss_textEditttt_01.setVisible(False)
        self.ss_textEditttt_02.setVisible(False)
        self.ss_textEditttt_03.setVisible(True)
        self.ss_textEditttt_04.setVisible(True)
        self.ss_textEditttt_05.setVisible(True)
        self.ss_textEditttt_06.setVisible(False)

        for item in self.stock_detail_list:
            item.setVisible(False)
        for item in self.stock_baklog_list:
            item.setVisible(False)
        for item in self.stock_datedt_list:
            item.setVisible(False)
        for item in self.stock_backte_list:
            item.setVisible(False)
        for item in self.stock_opcond_list:
            item.setVisible(False)
        for item in self.stock_gaopti_list:
            item.setVisible(False)
        for item in self.stock_optest_list:
            item.setVisible(False)
        for item in self.stock_esczom_list:
            item.setVisible(True)
        for item in self.stock_optimz_list:
            item.setVisible(True)
        for item in self.stock_period_list:
            item.setVisible(True)
        for item in self.stock_rwftvd_list:
            item.setVisible(True)

        self.svc_pushButton_03.setText('최적화 변수범위 로딩(F9)')
        self.svc_pushButton_04.setText('최적화 변수범위 저장(F12)')

        self.image_label1.setVisible(False)
        self.svc_labellllll_01.setVisible(False)
        self.svc_labellllll_04.setText(rwfttext)
        self.svc_labellllll_05.setVisible(False)
        self.svc_pushButton_21.setVisible(False)
        self.svc_pushButton_22.setVisible(False)
        self.svc_pushButton_23.setVisible(False)
        self.svc_pushButton_24.setVisible(False)
        self.svc_pushButton_25.setVisible(False)
        self.svc_pushButton_26.setVisible(False)
        self.sChangeSvjButtonColor()

    def svjButtonClicked_03(self):
        self.ss_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
        self.ss_textEditttt_04.setGeometry(7, 756 if self.extend_window else 478, 647, 602 if self.extend_window else 272)
        self.ss_textEditttt_06.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)

        self.svc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.svc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.svc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.svc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.sva_comboBoxxx_01.setGeometry(1012, 115, 165, 30)
        self.sva_lineEdittt_01.setGeometry(1182, 115, 165, 30)
        self.sva_pushButton_04.setGeometry(1012, 150, 165, 30)
        self.sva_pushButton_05.setGeometry(1182, 150, 165, 30)

        self.szoo_pushButon_01.setGeometry(599, 15, 50, 20)
        self.szoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)

        self.szoo_pushButon_01.setText('확대(esc)')
        self.szoo_pushButon_02.setText('확대(esc)')

        self.ss_textEditttt_01.setVisible(False)
        self.ss_textEditttt_02.setVisible(False)
        self.ss_textEditttt_03.setVisible(True)
        self.ss_textEditttt_04.setVisible(True)
        self.ss_textEditttt_05.setVisible(False)
        self.ss_textEditttt_06.setVisible(True)

        for item in self.stock_detail_list:
            item.setVisible(False)
        for item in self.stock_baklog_list:
            item.setVisible(False)
        for item in self.stock_datedt_list:
            item.setVisible(False)
        for item in self.stock_backte_list:
            item.setVisible(False)
        for item in self.stock_opcond_list:
            item.setVisible(False)
        for item in self.stock_optest_list:
            item.setVisible(False)
        for item in self.stock_rwftvd_list:
            item.setVisible(False)
        for item in self.stock_esczom_list:
            item.setVisible(True)
        for item in self.stock_optimz_list:
            item.setVisible(True)
        for item in self.stock_period_list:
            item.setVisible(True)
        for item in self.stock_gaopti_list:
            item.setVisible(True)

        self.sva_pushButton_04.setText('GA 변수범위 로딩(F9)')
        self.sva_pushButton_05.setText('GA 변수범위 저장(F12)')

        self.image_label1.setVisible(False)
        self.svc_labellllll_04.setText(gaoptext)
        self.svc_labellllll_05.setVisible(False)
        self.svc_pushButton_21.setVisible(False)
        self.svc_pushButton_22.setVisible(False)
        self.svc_pushButton_23.setVisible(False)
        self.svc_pushButton_24.setVisible(False)
        self.svc_pushButton_25.setVisible(False)
        self.svc_pushButton_26.setVisible(False)
        self.sChangeSvjButtonColor()

    def svjButtonClicked_04(self):
        self.ss_textEditttt_05.setGeometry(7, 10, 497, 1347 if self.extend_window else 740)
        self.ss_textEditttt_06.setGeometry(509, 10, 497, 1347 if self.extend_window else 740)

        self.svc_comboBoxxx_02.setGeometry(1012, 10, 165, 30)
        self.svc_lineEdittt_02.setGeometry(1182, 10, 165, 30)
        self.svc_pushButton_03.setGeometry(1012, 45, 165, 30)
        self.svc_pushButton_04.setGeometry(1182, 45, 165, 30)

        self.sva_comboBoxxx_01.setGeometry(1012, 80, 165, 30)
        self.sva_lineEdittt_01.setGeometry(1182, 80, 165, 30)
        self.sva_pushButton_04.setGeometry(1012, 115, 165, 30)
        self.sva_pushButton_05.setGeometry(1182, 115, 165, 30)

        self.ss_textEditttt_01.setVisible(False)
        self.ss_textEditttt_02.setVisible(False)
        self.ss_textEditttt_03.setVisible(False)
        self.ss_textEditttt_04.setVisible(False)
        self.ss_textEditttt_05.setVisible(True)
        self.ss_textEditttt_06.setVisible(True)

        for item in self.stock_datedt_list:
            item.setVisible(False)
        for item in self.stock_backte_list:
            item.setVisible(False)
        for item in self.stock_opcond_list:
            item.setVisible(False)
        for item in self.stock_detail_list:
            item.setVisible(False)
        for item in self.stock_baklog_list:
            item.setVisible(False)
        for item in self.stock_optest_list:
            item.setVisible(False)
        for item in self.stock_rwftvd_list:
            item.setVisible(False)
        for item in self.stock_esczom_list:
            item.setVisible(False)
        for item in self.stock_optimz_list:
            item.setVisible(False)
        for item in self.stock_period_list:
            item.setVisible(True)
        for item in self.stock_gaopti_list:
            item.setVisible(True)

        self.sva_pushButton_04.setText('GA 변수범위 로딩')
        self.sva_pushButton_05.setText('GA 변수범위 저장')
        self.svc_pushButton_03.setText('최적화 변수범위 로딩')
        self.svc_pushButton_04.setText('최적화 변수범위 저장')

        self.svc_pushButton_06.setVisible(False)
        self.svc_pushButton_07.setVisible(False)
        self.svc_pushButton_08.setVisible(False)
        self.svc_pushButton_27.setVisible(False)
        self.svc_pushButton_28.setVisible(False)
        self.svc_pushButton_29.setVisible(False)

        self.sva_pushButton_01.setVisible(False)
        self.sva_pushButton_02.setVisible(False)
        self.sva_pushButton_03.setVisible(False)

        self.svc_comboBoxxx_02.setVisible(True)
        self.svc_lineEdittt_02.setVisible(True)
        self.svc_pushButton_03.setVisible(True)
        self.svc_pushButton_04.setVisible(True)

        self.svc_pushButton_11.setVisible(True)

        self.image_label1.setVisible(True)
        self.svc_labellllll_05.setVisible(True)
        self.svc_labellllll_04.setText(gaoptext)
        self.svc_labellllll_05.setText(vedittxt)
        self.svc_pushButton_21.setVisible(True)
        self.svc_pushButton_22.setVisible(True)
        self.svc_pushButton_23.setVisible(True)
        self.svc_pushButton_24.setVisible(False)
        self.svc_pushButton_25.setVisible(False)
        self.svc_pushButton_26.setVisible(False)
        self.sChangeSvjButtonColor()

    def svjButtonClicked_05(self):
        self.ss_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
        self.ss_textEditttt_04.setGeometry(7, 756 if self.extend_window else 478, 647, 602 if self.extend_window else 272)
        self.ss_textEditttt_05.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)

        self.svc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.svc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.svc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.svc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.szoo_pushButon_01.setGeometry(599, 15, 50, 20)
        self.szoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)

        self.szoo_pushButon_01.setText('확대(esc)')
        self.szoo_pushButon_02.setText('확대(esc)')

        self.ss_textEditttt_01.setVisible(False)
        self.ss_textEditttt_02.setVisible(False)
        self.ss_textEditttt_03.setVisible(True)
        self.ss_textEditttt_04.setVisible(True)
        self.ss_textEditttt_05.setVisible(True)
        self.ss_textEditttt_06.setVisible(False)

        for item in self.stock_datedt_list:
            item.setVisible(False)
        for item in self.stock_backte_list:
            item.setVisible(False)
        for item in self.stock_opcond_list:
            item.setVisible(False)
        for item in self.stock_detail_list:
            item.setVisible(False)
        for item in self.stock_baklog_list:
            item.setVisible(False)
        for item in self.stock_optest_list:
            item.setVisible(False)
        for item in self.stock_gaopti_list:
            item.setVisible(False)
        for item in self.stock_rwftvd_list:
            item.setVisible(False)
        for item in self.stock_esczom_list:
            item.setVisible(True)
        for item in self.stock_optimz_list:
            item.setVisible(True)
        for item in self.stock_period_list:
            item.setVisible(True)

        self.svc_pushButton_03.setText('최적화 변수범위 로딩(F9)')
        self.svc_pushButton_04.setText('최적화 변수범위 저장(F12)')

        self.image_label1.setVisible(False)
        self.svc_labellllll_04.setText(optitext)
        self.svc_labellllll_05.setVisible(False)
        self.svc_pushButton_21.setVisible(False)
        self.svc_pushButton_22.setVisible(False)
        self.svc_pushButton_23.setVisible(False)
        self.svc_pushButton_24.setVisible(False)
        self.svc_pushButton_25.setVisible(False)
        self.svc_pushButton_26.setVisible(False)
        self.sChangeSvjButtonColor()

    def svjButtonClicked_06(self):
        self.ss_textEditttt_01.setGeometry(7, 10, 497, 740 if self.extend_window else 463)
        self.ss_textEditttt_02.setGeometry(7, 756 if self.extend_window else 478, 497, 602 if self.extend_window else 272)
        self.ss_textEditttt_03.setGeometry(509, 10, 497, 740 if self.extend_window else 463)
        self.ss_textEditttt_04.setGeometry(509, 756 if self.extend_window else 478, 497, 602 if self.extend_window else 272)

        self.svjb_comboBoxx_01.setGeometry(1012, 10, 165, 30)
        self.svjb_pushButon_01.setGeometry(1182, 10, 165, 30)
        self.svjs_comboBoxx_01.setGeometry(1012, 478, 165, 30)
        self.svjs_pushButon_01.setGeometry(1182, 478, 165, 30)

        self.svc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.svc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.svc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.svc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.ss_textEditttt_01.setVisible(True)
        self.ss_textEditttt_02.setVisible(True)
        self.ss_textEditttt_03.setVisible(True)
        self.ss_textEditttt_04.setVisible(True)
        self.ss_textEditttt_05.setVisible(False)
        self.ss_textEditttt_06.setVisible(False)

        for item in self.stock_datedt_list:
            item.setVisible(False)
        for item in self.stock_backte_list:
            item.setVisible(False)
        for item in self.stock_opcond_list:
            item.setVisible(False)
        for item in self.stock_detail_list:
            item.setVisible(False)
        for item in self.stock_baklog_list:
            item.setVisible(False)
        for item in self.stock_gaopti_list:
            item.setVisible(False)
        for item in self.stock_optest_list:
            item.setVisible(False)
        for item in self.stock_rwftvd_list:
            item.setVisible(False)
        for item in self.stock_esczom_list:
            item.setVisible(False)
        for item in self.stock_optimz_list:
            item.setVisible(True)
        for item in self.stock_period_list:
            item.setVisible(True)

        self.svjb_pushButon_01.setText('매수전략 로딩')
        self.svjs_pushButon_01.setText('매도전략 로딩')

        self.svjb_comboBoxx_01.setVisible(True)
        self.svjb_pushButon_01.setVisible(True)
        self.svjs_comboBoxx_01.setVisible(True)
        self.svjs_pushButon_01.setVisible(True)

        self.svc_lineEdittt_04.setVisible(False)
        self.svc_pushButton_13.setVisible(False)
        self.svc_lineEdittt_05.setVisible(False)
        self.svc_pushButton_14.setVisible(False)

        self.image_label1.setVisible(False)
        self.svc_labellllll_04.setText(optitext)
        self.svc_labellllll_05.setVisible(False)
        self.svc_pushButton_21.setVisible(False)
        self.svc_pushButton_22.setVisible(False)
        self.svc_pushButton_23.setVisible(False)
        self.svc_pushButton_24.setVisible(True)
        self.svc_pushButton_25.setVisible(True)
        self.svc_pushButton_26.setVisible(True)
        self.sChangeSvjButtonColor()

    def svjButtonClicked_07(self):
        self.ss_textEditttt_01.setVisible(False)
        self.ss_textEditttt_02.setVisible(False)
        self.ss_textEditttt_03.setVisible(False)
        self.ss_textEditttt_04.setVisible(False)
        self.ss_textEditttt_05.setVisible(False)
        self.ss_textEditttt_06.setVisible(False)
        self.ss_textEditttt_07.setVisible(False)
        self.ss_textEditttt_08.setVisible(False)

        self.ss_textEditttt_09.setGeometry(7, 10, 1000, 1308 if self.extend_window else 703)
        self.ss_progressBar_01.setGeometry(7, 1323 if self.extend_window else 718, 830, 30)
        self.ss_pushButtonn_08.setGeometry(842, 1323 if self.extend_window else 718, 165, 30)

        for item in self.stock_esczom_list:
            item.setVisible(False)
        for item in self.stock_detail_list:
            item.setVisible(False)
        for item in self.stock_baklog_list:
            item.setVisible(True)
        self.ss_pushButtonn_08.setStyleSheet(style_bc_by)
        self.sChangeSvjButtonColor()

    def svjButtonClicked_08(self):
        self.ss_textEditttt_01.setVisible(False)
        self.ss_textEditttt_02.setVisible(False)
        self.ss_textEditttt_03.setVisible(False)
        self.ss_textEditttt_04.setVisible(False)
        self.ss_textEditttt_05.setVisible(False)
        self.ss_textEditttt_06.setVisible(False)
        self.ss_textEditttt_07.setVisible(False)
        self.ss_textEditttt_08.setVisible(False)

        self.ss_tableWidget_01.setGeometry(7, 40, 1000, 1318 if self.extend_window else 713)
        self.ss_tableWidget_01.setRowCount(60 if self.extend_window else 32)

        for item in self.stock_esczom_list:
            item.setVisible(False)
        for item in self.stock_baklog_list:
            item.setVisible(False)
        for item in self.stock_detail_list:
            item.setVisible(True)
        self.sChangeSvjButtonColor()

    def svjButtonClicked_09(self):
        self.ss_textEditttt_01.setGeometry(7, 10, 1000, 740 if self.extend_window else 463)
        self.ss_textEditttt_02.setGeometry(7, 756 if self.extend_window else 478, 1000, 602 if self.extend_window else 272)

        self.svjb_comboBoxx_01.setGeometry(1012, 10, 165, 25)
        self.svjb_pushButon_01.setGeometry(1012, 40, 165, 30)
        self.svjs_comboBoxx_01.setGeometry(1012, 478, 165, 25)
        self.svjs_pushButon_01.setGeometry(1012, 508, 165, 30)

        self.szoo_pushButon_01.setGeometry(952, 15, 50, 20)
        self.szoo_pushButon_02.setGeometry(952, 761 if self.extend_window else 483, 50, 20)

        self.szoo_pushButon_01.setText('확대(esc)')
        self.szoo_pushButon_02.setText('확대(esc)')

        self.ss_textEditttt_01.setVisible(True)
        self.ss_textEditttt_02.setVisible(True)
        self.ss_textEditttt_03.setVisible(False)
        self.ss_textEditttt_04.setVisible(False)
        self.ss_textEditttt_05.setVisible(False)
        self.ss_textEditttt_06.setVisible(False)

        for item in self.stock_optimz_list:
            item.setVisible(False)
        for item in self.stock_period_list:
            item.setVisible(False)
        for item in self.stock_opcond_list:
            item.setVisible(False)
        for item in self.stock_detail_list:
            item.setVisible(False)
        for item in self.stock_baklog_list:
            item.setVisible(False)
        for item in self.stock_gaopti_list:
            item.setVisible(False)
        for item in self.stock_optest_list:
            item.setVisible(False)
        for item in self.stock_rwftvd_list:
            item.setVisible(False)
        for item in self.stock_datedt_list:
            item.setVisible(True)
        for item in self.stock_esczom_list:
            item.setVisible(True)
        for item in self.stock_backte_list:
            item.setVisible(True)

        self.svjb_pushButon_01.setText('매수전략 로딩(F1)')
        self.svjs_pushButon_01.setText('매도전략 로딩(F5)')

        self.image_label1.setVisible(False)
        self.svc_labellllll_05.setVisible(False)
        self.svc_pushButton_21.setVisible(False)
        self.svc_pushButton_22.setVisible(False)
        self.svc_pushButton_23.setVisible(False)
        self.svc_pushButton_24.setVisible(False)
        self.svc_pushButton_25.setVisible(False)
        self.svc_pushButton_26.setVisible(False)
        self.sChangeSvjButtonColor()

    def svjButtonClicked_10(self):
        self.ss_textEditttt_07.setGeometry(7, 10, 497, 1347 if self.extend_window else 740)
        self.ss_textEditttt_08.setGeometry(509, 10, 497, 1347 if self.extend_window else 740)

        self.ss_textEditttt_01.setVisible(False)
        self.ss_textEditttt_02.setVisible(False)
        self.ss_textEditttt_03.setVisible(False)
        self.ss_textEditttt_04.setVisible(False)
        self.ss_textEditttt_05.setVisible(False)
        self.ss_textEditttt_06.setVisible(False)

        for item in self.stock_esczom_list:
            item.setVisible(False)
        for item in self.stock_backte_list:
            item.setVisible(False)
        for item in self.stock_detail_list:
            item.setVisible(False)
        for item in self.stock_baklog_list:
            item.setVisible(False)
        for item in self.stock_gaopti_list:
            item.setVisible(False)
        for item in self.stock_optest_list:
            item.setVisible(False)
        for item in self.stock_rwftvd_list:
            item.setVisible(False)
        for item in self.stock_datedt_list:
            item.setVisible(False)
        for item in self.stock_optimz_list:
            item.setVisible(True)
        for item in self.stock_period_list:
            item.setVisible(True)
        for item in self.stock_opcond_list:
            item.setVisible(True)

        self.svc_lineEdittt_04.setVisible(False)
        self.svc_lineEdittt_05.setVisible(False)
        self.svc_pushButton_13.setVisible(False)
        self.svc_pushButton_14.setVisible(False)

        self.svc_comboBoxxx_08.setVisible(False)
        self.svc_lineEdittt_03.setVisible(False)
        self.svc_pushButton_09.setVisible(False)
        self.svc_pushButton_10.setVisible(False)

        self.svc_comboBoxxx_02.setVisible(False)
        self.svc_lineEdittt_02.setVisible(False)
        self.svc_pushButton_03.setVisible(False)
        self.svc_pushButton_04.setVisible(False)

        self.image_label1.setVisible(True)
        self.svc_labellllll_01.setVisible(False)
        self.svc_labellllll_04.setVisible(True)
        self.svc_labellllll_05.setVisible(True)
        self.svc_labellllll_04.setText(condtext)
        self.svc_labellllll_05.setText(cedittxt)
        self.svc_pushButton_21.setVisible(False)
        self.svc_pushButton_22.setVisible(False)
        self.svc_pushButton_23.setVisible(False)
        self.svc_pushButton_24.setVisible(False)
        self.svc_pushButton_25.setVisible(False)
        self.svc_pushButton_26.setVisible(False)
        self.sChangeSvjButtonColor()

    def svjButtonClicked_11(self):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            back_club = True if (QApplication.keyboardModifiers() & Qt.ControlModifier) and (QApplication.keyboardModifiers() & Qt.AltModifier) else False
            if back_club and not self.backtest_engine:
                QMessageBox.critical(self, '오류 알림', '백테엔진을 먼저 실행하십시오.\n')
                return
            if not back_club and (not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier)):
                self.BackengineShow('주식')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            startday  = self.svjb_dateEditt_01.date().toString('yyyyMMdd')
            endday    = self.svjb_dateEditt_02.date().toString('yyyyMMdd')
            starttime = self.svjb_lineEditt_02.text()
            endtime   = self.svjb_lineEditt_03.text()
            betting   = self.svjb_lineEditt_04.text()
            avgtime   = self.svjb_lineEditt_05.text()
            buystg    = self.svjb_comboBoxx_01.currentText()
            sellstg   = self.svjs_comboBoxx_01.currentText()
            bl        = True if self.dict_set['블랙리스트추가'] else False

            if int(avgtime) not in self.avg_list:
                QMessageBox.critical(self, '오류 알림', '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                return
            if '' in (startday, endday, starttime, endtime, betting, avgtime):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if '' in (buystg, sellstg):
                QMessageBox.critical(self, '오류 알림', '전략을 저장하고 콤보박스에서 선택하십시오.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', '백테스트'))

            backQ.put((
                betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg, self.dict_cn, self.back_count,
                bl, False, self.df_kp, self.df_kd, back_club
            ))
            self.proc_backtester_bb = Process(
                target=BackTest,
                args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '백테스트', 'S')
            )
            self.proc_backtester_bb.start()
            self.svjButtonClicked_07()
            self.ss_progressBar_01.setValue(0)
            self.ssicon_alert = True

    def svjButtonClicked_12(self):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow('주식')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            startday  = self.svjb_dateEditt_01.date().toString('yyyyMMdd')
            endday    = self.svjb_dateEditt_02.date().toString('yyyyMMdd')
            starttime = self.svjb_lineEditt_02.text()
            endtime   = self.svjb_lineEditt_03.text()
            avgtime   = self.svjb_lineEditt_05.text()
            buystg    = self.svjb_comboBoxx_01.currentText()

            if int(avgtime) not in self.avg_list:
                QMessageBox.critical(self, '오류 알림', '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                return
            if '' in (startday, endday, starttime, endtime, avgtime):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if buystg == '':
                QMessageBox.critical(self, '오류 알림', '매수전략을 저장하고 콤보박스에서 선택하십시오.\n')
                return
            if 'self.tickcols' not in self.ss_textEditttt_01.toPlainText():
                QMessageBox.critical(self, '오류 알림', '현재 매수전략이 백파인더용이 아닙니다.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', '백파인더'))

            backQ.put((avgtime, startday, endday, starttime, endtime, buystg, self.back_count))
            self.proc_backtester_bf = Process(
                target=BackFinder,
                args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, '백파인더', 'S')
            )
            self.proc_backtester_bf.start()
            self.svjButtonClicked_07()
            self.ss_progressBar_01.setValue(0)
            self.ssicon_alert = True

    def svjButtonClicked_13(self):
        if self.ss_textEditttt_01.isVisible():
            self.ss_textEditttt_01.clear()
            self.ss_textEditttt_02.clear()
            self.ss_textEditttt_01.append(example_finder)

    def svjButtonClicked_14(self, back_name):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow('주식')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            randomopti  = True if (QApplication.keyboardModifiers() & Qt.AltModifier) and 'B' not in back_name else False
            starttime   = self.svjb_lineEditt_02.text()
            endtime     = self.svjb_lineEditt_03.text()
            betting     = self.svjb_lineEditt_04.text()
            buystg      = self.svc_comboBoxxx_01.currentText()
            sellstg     = self.svc_comboBoxxx_08.currentText()
            optivars    = self.svc_comboBoxxx_02.currentText()
            ccount      = self.svc_comboBoxxx_06.currentText()
            optistd     = self.svc_comboBoxxx_07.currentText()
            weeks_train = self.svc_comboBoxxx_03.currentText()
            weeks_valid = self.svc_comboBoxxx_04.currentText()
            weeks_test  = self.svc_comboBoxxx_05.currentText()
            benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
            bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')
            optunasampl = self.op_comboBoxxxx_01.currentText()
            optunafixv  = self.op_lineEditttt_01.text()
            optunacount = self.op_lineEditttt_02.text()
            optunaautos = 1 if self.op_checkBoxxxx_01.isChecked() else 0

            if 'VC' in back_name and weeks_train != 'ALL' and int(weeks_train) % int(weeks_valid) != 0:
                QMessageBox.critical(self, '오류 알림', '교차검증의 학습기간은 검증기간의 배수로 선택하십시오.\n')
                return
            if '' in (starttime, endtime, betting):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if '' in (buystg, sellstg):
                QMessageBox.critical(self, '오류 알림', '전략을 저장하고 콤보박스에서 선택하십시오.\n')
                return
            if optivars == '':
                QMessageBox.critical(self, '오류 알림', '변수를 설장하고 콤보박스에서 선택하십시오.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', '최적화'))

            backQ.put((
                betting, starttime, endtime, buystg, sellstg, optivars, self.dict_cn, ccount, self.dict_set['최적화기준값제한'],
                optistd, self.back_count, False, self.df_kp, self.df_kd, weeks_train, weeks_valid, weeks_test, benginesday,
                bengineeday, optunasampl, optunafixv, optunacount, optunaautos, randomopti
            ))
            if back_name == '최적화O':
                self.proc_backtester_o = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_o.start()
            elif back_name == '최적화OV':
                self.proc_backtester_ov = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_ov.start()
            elif back_name == '최적화OVC':
                self.proc_backtester_ovc = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_ovc.start()
            elif back_name == '최적화B':
                self.proc_backtester_b = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_b.start()
            elif back_name == '최적화BV':
                self.proc_backtester_bv = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_bv.start()
            elif back_name == '최적화BVC':
                self.proc_backtester_bvc = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_bvc.start()
            elif back_name == '최적화OT':
                self.proc_backtester_ot = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_ot.start()
            elif back_name == '최적화OVT':
                self.proc_backtester_ovt = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_ovt.start()
            elif back_name == '최적화OVCT':
                self.proc_backtester_ovct = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_ovct.start()
            elif back_name == '최적화BT':
                self.proc_backtester_bt = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_bt.start()
            elif back_name == '최적화BVT':
                self.proc_backtester_bvt = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_bvt.start()
            else:
                self.proc_backtester_bvct = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_bvct.start()
            self.svjButtonClicked_07()
            self.ss_progressBar_01.setValue(0)
            self.ssicon_alert = True

    def svjButtonClicked_15(self, back_name):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow('주식')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            randomopti  = True if (QApplication.keyboardModifiers() & Qt.AltModifier) and 'B' not in back_name else False
            startday    = self.svjb_dateEditt_01.date().toString('yyyyMMdd')
            endday      = self.svjb_dateEditt_02.date().toString('yyyyMMdd')
            starttime   = self.svjb_lineEditt_02.text()
            endtime     = self.svjb_lineEditt_03.text()
            betting     = self.svjb_lineEditt_04.text()
            buystg      = self.svc_comboBoxxx_01.currentText()
            sellstg     = self.svc_comboBoxxx_08.currentText()
            optivars    = self.svc_comboBoxxx_02.currentText()
            ccount      = self.svc_comboBoxxx_06.currentText()
            optistd     = self.svc_comboBoxxx_07.currentText()
            weeks_train = self.svc_comboBoxxx_03.currentText()
            weeks_valid = self.svc_comboBoxxx_04.currentText()
            weeks_test  = self.svc_comboBoxxx_05.currentText()
            benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
            bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')
            optunasampl = self.op_comboBoxxxx_01.currentText()
            optunafixv  = self.op_lineEditttt_01.text()
            optunacount = self.op_lineEditttt_02.text()
            optunaautos = 1 if self.op_checkBoxxxx_01.isChecked() else 0

            if 'VC' in back_name and weeks_train != 'ALL' and int(weeks_train) % int(weeks_valid) != 0:
                QMessageBox.critical(self, '오류 알림', '교차검증의 학습기간은 검증기간의 배수로 선택하십시오.\n')
                return
            if weeks_train == 'ALL':
                QMessageBox.critical(self, '오류 알림', '전진분석 학습기간은 전체를 선택할 수 없습니다.\n')
                return
            if '' in (starttime, endtime, betting):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if '' in (buystg, sellstg):
                QMessageBox.critical(self, '오류 알림', '전략을 저장하고 콤보박스에서 선택하십시오.\n')
                return
            if optivars == '':
                QMessageBox.critical(self, '오류 알림', '변수를 설장하고 콤보박스에서 선택하십시오.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', '전진분석'))

            backQ.put((
                betting, startday, endday, starttime, endtime, buystg, sellstg, optivars, self.dict_cn, ccount,
                self.dict_set['최적화기준값제한'], optistd, self.back_count, False, self.df_kp, self.df_kd, weeks_train,
                weeks_valid, weeks_test, benginesday, bengineeday, optunasampl, optunafixv, optunacount, optunaautos,
                randomopti
            ))
            if back_name == '전진분석OR':
                self.proc_backtester_or = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_or.start()
            elif back_name == '전진분석ORV':
                self.proc_backtester_orv = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_orv.start()
            elif back_name == '전진분석ORVC':
                self.proc_backtester_orvc = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_orvc.start()
            elif back_name == '전진분석BR':
                self.proc_backtester_br = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_br.start()
            elif back_name == '전진분석BRV':
                self.proc_backtester_brv = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_brv.start()
            else:
                self.proc_backtester_brvc = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_brvc.start()
            self.svjButtonClicked_07()
            self.ss_progressBar_01.setValue(0)
            self.ssicon_alert = True

    def svjButtonClicked_16(self, back_name):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow('주식')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            starttime   = self.svjb_lineEditt_02.text()
            endtime     = self.svjb_lineEditt_03.text()
            betting     = self.svjb_lineEditt_04.text()
            buystg      = self.svc_comboBoxxx_01.currentText()
            sellstg     = self.svc_comboBoxxx_08.currentText()
            optivars    = self.sva_comboBoxxx_01.currentText()
            optistd     = self.svc_comboBoxxx_07.currentText()
            weeks_train = self.svc_comboBoxxx_03.currentText()
            weeks_valid = self.svc_comboBoxxx_04.currentText()
            weeks_test  = self.svc_comboBoxxx_05.currentText()
            benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
            bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')

            if 'VC' in back_name and weeks_train != 'ALL' and int(weeks_train) % int(weeks_valid) != 0:
                QMessageBox.critical(self, '오류 알림', '교차검증의 학습기간은 검증기간의 배수로 선택하십시오.\n')
                return
            if '' in (starttime, endtime, betting):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if '' in (buystg, sellstg):
                QMessageBox.critical(self, '오류 알림', '전략을 저장하고 콤보박스에서 선택하십시오.\n')
                return
            if optivars == '':
                QMessageBox.critical(self, '오류 알림', '변수를 설장하고 콤보박스에서 선택하십시오.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', 'GA최적화'))

            backQ.put((
                betting, starttime, endtime, buystg, sellstg, optivars, self.dict_cn, self.dict_set['최적화기준값제한'],
                optistd, self.back_count, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday
            ))
            if back_name == '최적화OG':
                self.proc_backtester_og = Process(
                    target=OptimizeGeneticAlgorithm,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_og.start()
            elif back_name == '최적화OGV':
                self.proc_backtester_ogv = Process(
                    target=OptimizeGeneticAlgorithm,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_ogv.start()
            else:
                self.proc_backtester_ogvc = Process(
                    target=OptimizeGeneticAlgorithm,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_ogvc.start()
            self.svjButtonClicked_07()
            self.ss_progressBar_01.setValue(0)
            self.ssicon_alert = True

    def svjButtonClicked_17(self, back_name):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow('주식')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            starttime   = self.svjb_lineEditt_02.text()
            endtime     = self.svjb_lineEditt_03.text()
            betting     = self.svjb_lineEditt_04.text()
            avgtime     = self.svjb_lineEditt_05.text()
            buystg      = self.svo_comboBoxxx_01.currentText()
            sellstg     = self.svo_comboBoxxx_02.currentText()
            bcount      = self.svo_lineEdittt_03.text()
            scount      = self.svo_lineEdittt_04.text()
            rcount      = self.svo_lineEdittt_05.text()
            optistd     = self.svc_comboBoxxx_07.currentText()
            weeks_train = self.svc_comboBoxxx_03.currentText()
            weeks_valid = self.svc_comboBoxxx_04.currentText()
            weeks_test  = self.svc_comboBoxxx_05.currentText()
            benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
            bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')

            if 'VC' in back_name and weeks_train != 'ALL' and int(weeks_train) % int(weeks_valid) != 0:
                QMessageBox.critical(self, '오류 알림', '교차검증의 학습기간은 검증기간의 배수로 선택하십시오.\n')
                return
            if int(avgtime) not in self.avg_list:
                QMessageBox.critical(self, '오류 알림', '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                return
            if '' in (starttime, endtime, betting, avgtime, bcount, scount, rcount):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if '' in (buystg, sellstg):
                QMessageBox.critical(self, '오류 알림', '조건을 저장하고 콤보박스에서 선택하십시오.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', '조건최적화'))

            backQ.put((
                betting, avgtime, starttime, endtime, buystg, sellstg, self.dict_set['최적화기준값제한'], optistd, bcount,
                scount, rcount, self.back_count, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday
            ))
            if back_name == '최적화OC':
                self.proc_backtester_oc = Process(
                    target=OptimizeConditions,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_oc.start()
            elif back_name == '최적화OCV':
                self.proc_backtester_ocv = Process(
                    target=OptimizeConditions,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_ocv.start()
            else:
                self.proc_backtester_ocvc = Process(
                    target=OptimizeConditions,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'S')
                )
                self.proc_backtester_ocvc.start()
            self.svjButtonClicked_07()
            self.ss_progressBar_01.setValue(0)
            self.ssicon_alert = True

    def svjButtonClicked_26(self):
        opti_vars_text = self.ss_textEditttt_05.toPlainText()
        if opti_vars_text != '':
            ga_vars_text   = self.GetOptivarsToGavars(opti_vars_text)
            self.ss_textEditttt_06.clear()
            self.ss_textEditttt_06.append(ga_vars_text)
        else:
            QMessageBox.critical(self, '오류 알림', '현재 최적화 범위 코드가 공백 상태입니다.\n최적화 범위 코드를 작성하거나 로딩하십시오.\n')

    def svjButtonClicked_27(self):
        ga_vars_text   = self.ss_textEditttt_06.toPlainText()
        if ga_vars_text != '':
            opti_vars_text = self.GetGavarsToOptivars(ga_vars_text)
            self.ss_textEditttt_05.clear()
            self.ss_textEditttt_05.append(opti_vars_text)
        else:
            QMessageBox.critical(self, '오류 알림', '현재 GA 범위 코드가 공백 상태입니다.\nGA 범위 코드를 작성하거나 로딩하십시오.\n')

    def svjButtonClicked_28(self):
        buystg  = self.ss_textEditttt_01.toPlainText()
        sellstg = self.ss_textEditttt_02.toPlainText()
        buystg_str, sellstg_str = self.GetStgtxtToVarstxt(buystg, sellstg)
        self.ss_textEditttt_03.clear()
        self.ss_textEditttt_04.clear()
        self.ss_textEditttt_03.append(buystg_str)
        self.ss_textEditttt_04.append(sellstg_str)

    def svjButtonClicked_32(self):
        optivars = self.ss_textEditttt_05.toPlainText()
        gavars   = self.ss_textEditttt_06.toPlainText()
        optivars_str, gavars_str = self.GetStgtxtSort2(optivars, gavars)
        self.ss_textEditttt_05.clear()
        self.ss_textEditttt_06.clear()
        self.ss_textEditttt_05.append(optivars_str)
        self.ss_textEditttt_06.append(gavars_str)

    def svjButtonClicked_33(self):
        buystg  = self.ss_textEditttt_03.toPlainText()
        sellstg = self.ss_textEditttt_04.toPlainText()
        buystg_str, sellstg_str = self.GetStgtxtSort(buystg, sellstg)
        self.ss_textEditttt_03.clear()
        self.ss_textEditttt_04.clear()
        self.ss_textEditttt_03.append(buystg_str)
        self.ss_textEditttt_04.append(sellstg_str)

    def svjsButtonClicked_01(self):
        if self.ss_textEditttt_02.isVisible():
            con = sqlite3.connect(DB_STRATEGY)
            df = pd.read_sql('SELECT * FROM stocksell', con).set_index('index')
            con.close()
            if len(df) > 0:
                self.svjs_comboBoxx_01.clear()
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.svjs_comboBoxx_01.addItem(index)
                    if i == 0:
                        self.svjs_lineEditt_01.setText(index)
                self.svjs_pushButon_04.setStyleSheet(style_bc_st)

    def svjsButtonClicked_02(self):
        strategy_name = self.svjs_lineEditt_01.text()
        strategy = self.ss_textEditttt_02.toPlainText()
        strategy = self.GetFixStrategy(strategy, '매도')

        if strategy_name == '':
            QMessageBox.critical(self, '오류 알림', '매도전략의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
        elif not text_not_in_special_characters(strategy_name):
            QMessageBox.critical(self, '오류 알림', '매도전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
        elif strategy == '':
            QMessageBox.critical(self, '오류 알림', '매도전략의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
        else:
            if 'self.tickcols' in strategy or (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest1(strategy):
                if proc_query.is_alive():
                    queryQ.put(('전략디비', f"DELETE FROM stocksell WHERE `index` = '{strategy_name}'"))
                    df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                    queryQ.put(('전략디비', df, 'stocksell', 'append'))
                self.svjs_pushButon_04.setStyleSheet(style_bc_st)
                QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def svjsButtonClicked_03(self):
        self.ss_textEditttt_02.clear()
        self.ss_textEditttt_02.append(stock_sell_var)
        self.svjs_pushButon_04.setStyleSheet(style_bc_st)

    def svjsButtonClicked_04(self):
        strategy = self.ss_textEditttt_02.toPlainText()
        if strategy == '':
            QMessageBox.critical(self, '오류 알림', '매도전략의 코드가 공백 상태입니다.\n')
        else:
            buttonReply = QMessageBox.question(
                self, '전략시작', '매도전략의 연산을 시작합니다. 계속하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                wdzservQ.put(('strategy', ('매도전략', strategy)))
                self.svjs_pushButon_04.setStyleSheet(style_bc_dk)
                self.svjs_pushButon_14.setStyleSheet(style_bc_st)

    def svjsButtonClicked_05(self):
        self.ss_textEditttt_02.append(stock_sell1)

    def svjsButtonClicked_06(self):
        self.ss_textEditttt_02.append(stock_sell2)

    def svjsButtonClicked_07(self):
        self.ss_textEditttt_02.append(stock_sell3)

    def svjsButtonClicked_08(self):
        self.ss_textEditttt_02.append(stock_sell4)

    def svjsButtonClicked_09(self):
        self.ss_textEditttt_02.append(stock_sell5)

    def svjsButtonClicked_10(self):
        self.ss_textEditttt_02.append(stock_sell6)

    def svjsButtonClicked_11(self):
        self.ss_textEditttt_02.append(stock_sell7)

    def svjsButtonClicked_12(self):
        self.ss_textEditttt_02.append(stock_sell8)

    def svjsButtonClicked_13(self):
        self.ss_textEditttt_02.append(stock_sell_signal)

    def svjsButtonClicked_14(self):
        wdzservQ.put(('strategy', '매도전략중지'))
        self.svjs_pushButon_14.setStyleSheet(style_bc_dk)
        self.svjs_pushButon_04.setStyleSheet(style_bc_st)

    def svcButtonClicked_01(self):
        if self.ss_textEditttt_03.isVisible():
            con = sqlite3.connect(DB_STRATEGY)
            df = pd.read_sql('SELECT * FROM stockoptibuy', con).set_index('index')
            con.close()
            if len(df) > 0:
                self.svc_comboBoxxx_01.clear()
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.svc_comboBoxxx_01.addItem(index)
                    if i == 0:
                        self.svc_lineEdittt_01.setText(index)

    def svcButtonClicked_02(self):
        if self.ss_textEditttt_03.isVisible():
            strategy_name = self.svc_lineEdittt_01.text()
            strategy = self.ss_textEditttt_03.toPlainText()
            strategy = self.GetFixStrategy(strategy, '매수')

            if strategy_name == '':
                QMessageBox.critical(self, '오류 알림', '최적화 매수전략의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
            elif not text_not_in_special_characters(strategy_name):
                QMessageBox.critical(self, '오류 알림', '최적화 매수전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
            elif strategy == '':
                QMessageBox.critical(self, '오류 알림', '최적화 매수전략의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
            else:
                if 'self.tickcols' in strategy or (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest1(strategy):
                    con = sqlite3.connect(DB_STRATEGY)
                    df = pd.read_sql(f"SELECT * FROM stockoptibuy WHERE `index` = '{strategy_name}'", con)
                    con.close()
                    if proc_query.is_alive():
                        if len(df) > 0:
                            query = f"UPDATE stockoptibuy SET 전략코드 = '{strategy}' WHERE `index` = '{strategy_name}'"
                            queryQ.put(('전략디비', query))
                        else:
                            data = [
                                strategy,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.
                            ]
                            columns = [
                                '전략코드',
                                '변수0', '변수1', '변수2', '변수3', '변수4', '변수5', '변수6', '변수7', '변수8', '변수9',
                                '변수10', '변수11', '변수12', '변수13', '변수14', '변수15', '변수16', '변수17', '변수18', '변수19',
                                '변수20', '변수21', '변수22', '변수23', '변수24', '변수25', '변수26', '변수27', '변수28', '변수29',
                                '변수30', '변수31', '변수32', '변수33', '변수34', '변수35', '변수36', '변수37', '변수38', '변수39',
                                '변수40', '변수41', '변수42', '변수43', '변수44', '변수45', '변수46', '변수47', '변수48', '변수49',
                                '변수50', '변수51', '변수52', '변수53', '변수54', '변수55', '변수56', '변수57', '변수58', '변수59',
                                '변수60', '변수61', '변수62', '변수63', '변수64', '변수65', '변수66', '변수67', '변수68', '변수69',
                                '변수70', '변수71', '변수72', '변수73', '변수74', '변수75', '변수76', '변수77', '변수78', '변수79',
                                '변수80', '변수81', '변수82', '변수83', '변수84', '변수85', '변수86', '변수87', '변수88', '변수89',
                                '변수90', '변수91', '변수92', '변수93', '변수94', '변수95', '변수96', '변수97', '변수98', '변수99',
                                '변수100', '변수101', '변수102', '변수103', '변수104', '변수105', '변수106', '변수107', '변수108', '변수109',
                                '변수110', '변수111', '변수112', '변수113', '변수114', '변수115', '변수116', '변수117', '변수118', '변수119',
                                '변수120', '변수121', '변수122', '변수123', '변수124', '변수125', '변수126', '변수127', '변수128', '변수129',
                                '변수130', '변수131', '변수132', '변수133', '변수134', '변수135', '변수136', '변수137', '변수138', '변수139',
                                '변수140', '변수141', '변수142', '변수143', '변수144', '변수145', '변수146', '변수147', '변수148', '변수149',
                                '변수150', '변수151', '변수152', '변수153', '변수154', '변수155', '변수156', '변수157', '변수158', '변수159',
                                '변수160', '변수161', '변수162', '변수163', '변수164', '변수165', '변수166', '변수167', '변수168', '변수169',
                                '변수170', '변수171', '변수172', '변수173', '변수174', '변수175', '변수176', '변수177', '변수178', '변수179',
                                '변수180', '변수181', '변수182', '변수183', '변수184', '변수185', '변수186', '변수187', '변수188', '변수189',
                                '변수190', '변수191', '변수192', '변수193', '변수194', '변수195', '변수196', '변수197', '변수198', '변수199'
                            ]
                            df = pd.DataFrame([data], columns=columns, index=[strategy_name])
                            queryQ.put(('전략디비', df, 'stockoptibuy', 'append'))
                        QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def svcButtonClicked_03(self):
        if self.ss_textEditttt_05.isVisible():
            con = sqlite3.connect(DB_STRATEGY)
            df = pd.read_sql('SELECT * FROM stockoptivars', con).set_index('index')
            con.close()
            if len(df) > 0:
                self.svc_comboBoxxx_02.clear()
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.svc_comboBoxxx_02.addItem(index)
                    if i == 0:
                        self.svc_lineEdittt_02.setText(index)

    def svcButtonClicked_04(self):
        if self.ss_textEditttt_05.isVisible():
            strategy_name = self.svc_lineEdittt_02.text()
            strategy      = self.ss_textEditttt_05.toPlainText()
            if strategy_name == '':
                QMessageBox.critical(self, '오류 알림', '변수범위의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
            elif not text_not_in_special_characters(strategy_name):
                QMessageBox.critical(self, '오류 알림', '변수범위의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
            elif strategy == '':
                QMessageBox.critical(self, '오류 알림', '변수범위의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
            else:
                if (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest2(strategy):
                    if proc_query.is_alive():
                        queryQ.put(('전략디비', f"DELETE FROM stockoptivars WHERE `index` = '{strategy_name}'"))
                        df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                        queryQ.put(('전략디비', df, 'stockoptivars', 'append'))
                        QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def svcButtonClicked_05(self):
        if self.ss_textEditttt_04.isVisible():
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql('SELECT * FROM stockoptisell', con).set_index('index')
            con.close()
            if len(df) > 0:
                self.svc_comboBoxxx_08.clear()
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.svc_comboBoxxx_08.addItem(index)
                    if i == 0:
                        self.svc_lineEdittt_03.setText(index)

    def svcButtonClicked_06(self):
        if self.ss_textEditttt_04.isVisible():
            strategy_name = self.svc_lineEdittt_03.text()
            strategy      = self.ss_textEditttt_04.toPlainText()
            strategy      = self.GetFixStrategy(strategy, '매도')

            if strategy_name == '':
                QMessageBox.critical(self, '오류 알림', '최적화 매도전략의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
            elif not text_not_in_special_characters(strategy_name):
                QMessageBox.critical(self, '오류 알림', '최적화 매도전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
            elif strategy == '':
                QMessageBox.critical(self, '오류 알림', '최적화 매도전략의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
            else:
                if 'self.tickcols' in strategy or (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest1(strategy):
                    if proc_query.is_alive():
                        queryQ.put(('전략디비', f"DELETE FROM stockoptisell WHERE `index` = '{strategy_name}'"))
                        df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                        queryQ.put(('전략디비', df, 'stockoptisell', 'append'))
                        QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def svcButtonClicked_07(self):
        if self.ss_textEditttt_01.isVisible():
            self.ss_textEditttt_01.clear()
            self.ss_textEditttt_01.append(example_stock_buy)
        if self.ss_textEditttt_02.isVisible():
            self.ss_textEditttt_02.clear()
            self.ss_textEditttt_02.append(example_stock_sell)
        if self.ss_textEditttt_03.isVisible():
            self.ss_textEditttt_03.clear()
            if self.svc_pushButton_24.isVisible():
                self.ss_textEditttt_03.append(example_stockopti_buy1)
            else:
                self.ss_textEditttt_03.append(example_stockopti_buy2)
        if self.ss_textEditttt_04.isVisible():
            self.ss_textEditttt_04.clear()
            if self.svc_pushButton_24.isVisible():
                self.ss_textEditttt_04.append(example_stockopti_sell1)
            else:
                self.ss_textEditttt_04.append(example_stockopti_sell2)
        if self.ss_textEditttt_05.isVisible():
            self.ss_textEditttt_05.clear()
            self.ss_textEditttt_05.append(example_opti_vars)
        if self.ss_textEditttt_06.isVisible():
            self.ss_textEditttt_06.clear()
            self.ss_textEditttt_06.append(example_vars)
        if self.ss_textEditttt_07.isVisible():
            self.ss_textEditttt_07.clear()
            self.ss_textEditttt_07.append(example_buyconds)
        if self.ss_textEditttt_08.isVisible():
            self.ss_textEditttt_08.clear()
            self.ss_textEditttt_08.append(example_sellconds)

    def svcButtonClicked_09(self):
        tabl = 'stockoptivars' if not self.sva_pushButton_01.isVisible() else 'stockvars'
        stgy = self.svc_comboBoxxx_01.currentText()
        opti = self.svc_comboBoxxx_02.currentText() if not self.sva_pushButton_01.isVisible() else self.sva_comboBoxxx_01.currentText()
        name = self.svc_lineEdittt_04.text()
        if stgy == '' or opti == '' or name == '':
            QMessageBox.critical(self, '오류 알림', '전략 및 범위 코드를 선택하거나\n매수전략의 이름을 입력하십시오.\n')
            return
        elif not text_not_in_special_characters(name):
            QMessageBox.critical(self, '오류 알림', '매수전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
            return

        con = sqlite3.connect(DB_STRATEGY)
        df  = pd.read_sql('SELECT * FROM stockoptibuy', con).set_index('index')
        stg = df['전략코드'][stgy]
        df  = pd.read_sql(f'SELECT * FROM "{tabl}"', con).set_index('index')
        opt = df['전략코드'][opti]
        con.close()

        try:
            exec(compile(opt, '<string>', 'exec'), None, locals())
            for i in range(len(self.vars)):
                stg = stg.replace(f'self.vars[{i}]', f'{self.vars[i][1]}')
        except Exception as e:
            QMessageBox.critical(self, '오류 알림', f'{e}')
            return

        queryQ.put(('전략디비', f"DELETE FROM stockbuy WHERE `index` = '{name}'"))
        df = pd.DataFrame({'전략코드': [stg]}, index=[name])
        queryQ.put(('전략디비', df, 'stockbuy', 'append'))
        QMessageBox.information(self, '저장 알림', '최적값으로 매수전략을 저장하였습니다.\n')

    def svcButtonClicked_10(self):
        tabl = 'stockoptivars' if not self.sva_pushButton_01.isVisible() else 'stockvars'
        stgy = self.svc_comboBoxxx_08.currentText()
        opti = self.svc_comboBoxxx_02.currentText() if not self.sva_pushButton_01.isVisible() else self.sva_comboBoxxx_01.currentText()
        name = self.svc_lineEdittt_05.text()
        if stgy == '' or opti == '' or name == '':
            QMessageBox.critical(self, '오류 알림', '전략 및 범위 코드를 선택하거나\n매도전략의 이름을 입력하십시오.\n')
            return
        elif not text_not_in_special_characters(name):
            QMessageBox.critical(self, '오류 알림', '매도전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
            return

        con = sqlite3.connect(DB_STRATEGY)
        df  = pd.read_sql('SELECT * FROM stockoptisell', con).set_index('index')
        stg = df['전략코드'][stgy]
        df  = pd.read_sql(f'SELECT * FROM "{tabl}"', con).set_index('index')
        opt = df['전략코드'][opti]
        con.close()

        try:
            exec(compile(opt, '<string>', 'exec'), None, locals())
            for i in range(len(self.vars)):
                stg = stg.replace(f'self.vars[{i}]', f'{self.vars[i][1]}')
        except Exception as e:
            QMessageBox.critical(self, '오류 알림', f'{e}')
            return

        queryQ.put(('전략디비', f"DELETE FROM stocksell WHERE `index` = '{name}'"))
        df = pd.DataFrame({'전략코드': [stg]}, index=[name])
        queryQ.put(('전략디비', df, 'stocksell', 'append'))
        QMessageBox.information(self, '저장 알림', '최적값으로 매도전략을 저장하였습니다.\n')

    def svcButtonClicked_11(self):
        self.dialog_std.show() if not self.dialog_std.isVisible() else self.dialog_std.close()

    def svcButtonClicked_12(self):
        if not self.dialog_optuna.isVisible():
            if not self.optuna_window_open:
                self.op_lineEditttt_01.setText(self.dict_set['옵튜나고정변수'])
                self.op_lineEditttt_02.setText(str(self.dict_set['옵튜나실행횟수']))
                self.op_checkBoxxxx_01.setChecked(True) if self.dict_set['옵튜나자동스탭'] else self.op_checkBoxxxx_01.setChecked(False)
                self.op_comboBoxxxx_01.setCurrentText(self.dict_set['옵튜나샘플러'])
            self.dialog_optuna.show()
            self.optuna_window_open = True
        else:
            self.dialog_optuna.close()

    def svaButtonClicked_01(self):
        con = sqlite3.connect(DB_STRATEGY)
        df = pd.read_sql('SELECT * FROM stockvars', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.sva_comboBoxxx_01.clear()
            indexs = list(df.index)
            indexs.sort()
            for i, index in enumerate(indexs):
                self.sva_comboBoxxx_01.addItem(index)
                if i == 0:
                    self.sva_lineEdittt_01.setText(index)

    def svaButtonClicked_02(self):
        strategy_name = self.sva_lineEdittt_01.text()
        strategy      = self.ss_textEditttt_06.toPlainText()
        if strategy_name == '':
            QMessageBox.critical(self, '오류 알림', 'GA범위의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
        elif not text_not_in_special_characters(strategy_name):
            QMessageBox.critical(self, '오류 알림', 'GA범위의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
        elif strategy == '':
            QMessageBox.critical(self, '오류 알림', 'GA범위의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
        else:
            if (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest2(strategy, ga=True):
                if proc_query.is_alive():
                    queryQ.put(('전략디비', f"DELETE FROM stockvars WHERE `index` = '{strategy_name}'"))
                    df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                    queryQ.put(('전략디비', df, 'stockvars', 'append'))
                    QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def svoButtonClicked_01(self):
        con = sqlite3.connect(DB_STRATEGY)
        df = pd.read_sql('SELECT * FROM stockbuyconds', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.svo_comboBoxxx_01.clear()
            indexs = list(df.index)
            indexs.sort()
            for i, index in enumerate(indexs):
                self.svo_comboBoxxx_01.addItem(index)
                if i == 0:
                    self.svo_lineEdittt_01.setText(index)

    def svoButtonClicked_02(self):
        strategy_name = self.svo_lineEdittt_01.text()
        strategy      = self.ss_textEditttt_07.toPlainText()
        if strategy_name == '':
            QMessageBox.critical(self, '오류 알림', '매수조건의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
        elif not text_not_in_special_characters(strategy_name):
            QMessageBox.critical(self, '오류 알림', '매수조건의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
        elif strategy == '':
            QMessageBox.critical(self, '오류 알림', '매수조건의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
        else:
            if self.BackCodeTest3('매수', strategy):
                if proc_query.is_alive():
                    queryQ.put(('전략디비', f"DELETE FROM stockbuyconds WHERE `index` = '{strategy_name}'"))
                    df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                    queryQ.put(('전략디비', df, 'stockbuyconds', 'append'))
                    QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def svoButtonClicked_03(self):
        con = sqlite3.connect(DB_STRATEGY)
        df  = pd.read_sql('SELECT * FROM stocksellconds', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.svo_comboBoxxx_02.clear()
            indexs = list(df.index)
            indexs.sort()
            for i, index in enumerate(indexs):
                self.svo_comboBoxxx_02.addItem(index)
                if i == 0:
                    self.svo_lineEdittt_02.setText(index)

    def svoButtonClicked_04(self):
        strategy_name = self.svo_lineEdittt_02.text()
        strategy      = self.ss_textEditttt_08.toPlainText()
        if strategy_name == '':
            QMessageBox.critical(self, '오류 알림', '매도조건의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
        elif not text_not_in_special_characters(strategy_name):
            QMessageBox.critical(self, '오류 알림', '매도조건의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
        elif strategy == '':
            QMessageBox.critical(self, '오류 알림', '매도조건의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
        else:
            if self.BackCodeTest3('매도', strategy):
                if proc_query.is_alive():
                    queryQ.put(('전략디비', f"DELETE FROM stocksellconds WHERE `index` = '{strategy_name}'"))
                    df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                    queryQ.put(('전략디비', df, 'stocksellconds', 'append'))
                    QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def svoButtonClicked_06(self):
        QMessageBox.critical(self, '오류 알림', '범위 편집기 상태에서만 작동합니다.\n')

    # =================================================================================================================

    def cvjbButtonClicked_01(self):
        if self.cs_textEditttt_01.isVisible():
            con = sqlite3.connect(DB_STRATEGY)
            df = pd.read_sql('SELECT * FROM coinbuy', con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cvjb_comboBoxx_01.clear()
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.cvjb_comboBoxx_01.addItem(index)
                    if i == 0:
                        self.cvjb_lineEditt_01.setText(index)
                self.cvjb_pushButon_04.setStyleSheet(style_bc_st)

    def cvjbButtonClicked_02(self):
        strategy_name = self.cvjb_lineEditt_01.text()
        strategy      = self.cs_textEditttt_01.toPlainText()
        if 'self.tickcols' not in strategy:
            strategy = self.GetFixStrategy(strategy, '매수')

        if strategy_name == '':
            QMessageBox.critical(self, '오류 알림', '매수전략의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
        elif not text_not_in_special_characters(strategy_name):
            QMessageBox.critical(self, '오류 알림', '매수전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
        elif strategy == '':
            QMessageBox.critical(self, '오류 알림', '매수전략의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
        else:
            if 'self.tickcols' in strategy or (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest1(strategy):
                if proc_query.is_alive():
                    queryQ.put(('전략디비', f"DELETE FROM coinbuy WHERE `index` = '{strategy_name}'"))
                    df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                    queryQ.put(('전략디비', df, 'coinbuy', 'append'))
                self.cvjb_pushButon_04.setStyleSheet(style_bc_st)
                QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def cvjbButtonClicked_03(self):
        self.cs_textEditttt_01.clear()
        if not self.dict_set['코인일봉데이터'] and not self.dict_set['코인분봉데이터']:
            self.cs_textEditttt_01.append(coin_buy_var if self.dict_set['거래소'] == '업비트' else coin_future_buy_var)
        else:
            self.cs_textEditttt_01.append(coin_buy_var_ if self.dict_set['거래소'] == '업비트' else coin_future_buy_var_)
        self.cvjb_pushButon_04.setStyleSheet(style_bc_st)

    def cvjbButtonClicked_04(self):
        strategy = self.cs_textEditttt_01.toPlainText()
        if strategy == '':
            QMessageBox.critical(self, '오류 알림', '매수전략의 코드가 공백 상태입니다.\n')
        else:
            buttonReply = QMessageBox.question(
                self, '전략시작', '매수전략의 연산을 시작합니다. 계속하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                if self.CoinStrategyProcessAlive():
                    cstgQ.put(('매수전략', strategy))
                self.cvjb_pushButon_04.setStyleSheet(style_bc_dk)
                self.cvjb_pushButon_12.setStyleSheet(style_bc_st)

    def cvjbButtonClicked_05(self):
        self.cs_textEditttt_01.append(coin_buy1)

    def cvjbButtonClicked_06(self):
        self.cs_textEditttt_01.append(coin_buy2)

    def cvjbButtonClicked_07(self):
        self.cs_textEditttt_01.append(coin_buy3)

    def cvjbButtonClicked_08(self):
        self.cs_textEditttt_01.append(coin_buy4)

    def cvjbButtonClicked_09(self):
        self.cs_textEditttt_01.append(coin_buy5)

    def cvjbButtonClicked_10(self):
        self.cs_textEditttt_01.append(coin_buy6)

    def cvjbButtonClicked_11(self):
        self.cs_textEditttt_01.append(coin_buy_signal if self.dict_set['거래소'] == '업비트' else coin_future_buy_signal)

    def cvjbButtonClicked_12(self):
        if self.CoinStrategyProcessAlive():
            cstgQ.put('매수전략중지')
        self.cvjb_pushButon_12.setStyleSheet(style_bc_dk)
        self.cvjb_pushButon_04.setStyleSheet(style_bc_st)

    def cChangeSvjButtonColor(self):
        for button in self.coin_editer_list:
            button.setStyleSheet(style_bc_dk if self.focusWidget() == button else style_bc_bs)

    def cvjButtonClicked_01(self):
        self.cs_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
        self.cs_textEditttt_04.setGeometry(7, 756 if self.extend_window else 478, 647, 602 if self.extend_window else 272)
        self.cs_textEditttt_05.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)

        self.cvc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.cvc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.cvc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.cvc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.czoo_pushButon_01.setGeometry(599, 15, 50, 20)
        self.czoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)

        self.czoo_pushButon_01.setText('확대(esc)')
        self.czoo_pushButon_02.setText('확대(esc)')

        self.cs_textEditttt_01.setVisible(False)
        self.cs_textEditttt_02.setVisible(False)
        self.cs_textEditttt_03.setVisible(True)
        self.cs_textEditttt_04.setVisible(True)
        self.cs_textEditttt_05.setVisible(True)
        self.cs_textEditttt_06.setVisible(False)

        for item in self.coin_detail_list:
            item.setVisible(False)
        for item in self.coin_baklog_list:
            item.setVisible(False)
        for item in self.coin_datedt_list:
            item.setVisible(False)
        for item in self.coin_backte_list:
            item.setVisible(False)
        for item in self.coin_opcond_list:
            item.setVisible(False)
        for item in self.coin_gaopti_list:
            item.setVisible(False)
        for item in self.coin_rwftvd_list:
            item.setVisible(False)
        for item in self.coin_esczom_list:
            item.setVisible(True)
        for item in self.coin_optimz_list:
            item.setVisible(True)
        for item in self.coin_period_list:
            item.setVisible(True)
        for item in self.coin_optest_list:
            item.setVisible(True)

        self.cvc_pushButton_03.setText('최적화 변수범위 로딩(F9)')
        self.cvc_pushButton_04.setText('최적화 변수범위 저장(F12)')

        self.image_label1.setVisible(False)
        self.cvc_labellllll_04.setText(testtext)
        self.cvc_labellllll_05.setVisible(False)
        self.cvc_pushButton_21.setVisible(False)
        self.cvc_pushButton_22.setVisible(False)
        self.cvc_pushButton_23.setVisible(False)
        self.cvc_pushButton_24.setVisible(False)
        self.cvc_pushButton_25.setVisible(False)
        self.cvc_pushButton_26.setVisible(False)
        self.cChangeSvjButtonColor()

    def cvjButtonClicked_02(self):
        self.cs_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
        self.cs_textEditttt_04.setGeometry(7, 756 if self.extend_window else 478, 647, 602 if self.extend_window else 272)
        self.cs_textEditttt_05.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)

        self.cvc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.cvc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.cvc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.cvc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.czoo_pushButon_01.setGeometry(599, 15, 50, 20)
        self.czoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)

        self.czoo_pushButon_01.setText('확대(esc)')
        self.czoo_pushButon_02.setText('확대(esc)')

        self.cs_textEditttt_01.setVisible(False)
        self.cs_textEditttt_02.setVisible(False)
        self.cs_textEditttt_03.setVisible(True)
        self.cs_textEditttt_04.setVisible(True)
        self.cs_textEditttt_05.setVisible(True)
        self.cs_textEditttt_06.setVisible(False)

        for item in self.coin_detail_list:
            item.setVisible(False)
        for item in self.coin_baklog_list:
            item.setVisible(False)
        for item in self.coin_datedt_list:
            item.setVisible(False)
        for item in self.coin_backte_list:
            item.setVisible(False)
        for item in self.coin_opcond_list:
            item.setVisible(False)
        for item in self.coin_gaopti_list:
            item.setVisible(False)
        for item in self.coin_optest_list:
            item.setVisible(False)
        for item in self.coin_esczom_list:
            item.setVisible(True)
        for item in self.coin_optimz_list:
            item.setVisible(True)
        for item in self.coin_period_list:
            item.setVisible(True)
        for item in self.coin_rwftvd_list:
            item.setVisible(True)

        self.cvc_pushButton_03.setText('최적화 변수범위 로딩(F9)')
        self.cvc_pushButton_04.setText('최적화 변수범위 저장(F12)')

        self.image_label1.setVisible(False)
        self.cvc_labellllll_01.setVisible(False)
        self.cvc_labellllll_04.setText(rwfttext)
        self.cvc_labellllll_05.setVisible(False)
        self.cvc_pushButton_21.setVisible(False)
        self.cvc_pushButton_22.setVisible(False)
        self.cvc_pushButton_23.setVisible(False)
        self.cvc_pushButton_24.setVisible(False)
        self.cvc_pushButton_25.setVisible(False)
        self.cvc_pushButton_26.setVisible(False)
        self.cChangeSvjButtonColor()

    def cvjButtonClicked_03(self):
        self.cs_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
        self.cs_textEditttt_04.setGeometry(7, 756 if self.extend_window else 478, 647, 602 if self.extend_window else 272)
        self.cs_textEditttt_06.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)

        self.cvc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.cvc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.cvc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.cvc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.cva_comboBoxxx_01.setGeometry(1012, 115, 165, 30)
        self.cva_lineEdittt_01.setGeometry(1182, 115, 165, 30)
        self.cva_pushButton_04.setGeometry(1012, 150, 165, 30)
        self.cva_pushButton_05.setGeometry(1182, 150, 165, 30)

        self.czoo_pushButon_01.setGeometry(599, 15, 50, 20)
        self.czoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)

        self.czoo_pushButon_01.setText('확대(esc)')
        self.czoo_pushButon_02.setText('확대(esc)')

        self.cs_textEditttt_01.setVisible(False)
        self.cs_textEditttt_02.setVisible(False)
        self.cs_textEditttt_03.setVisible(True)
        self.cs_textEditttt_04.setVisible(True)
        self.cs_textEditttt_05.setVisible(False)
        self.cs_textEditttt_06.setVisible(True)

        for item in self.coin_detail_list:
            item.setVisible(False)
        for item in self.coin_baklog_list:
            item.setVisible(False)
        for item in self.coin_datedt_list:
            item.setVisible(False)
        for item in self.coin_backte_list:
            item.setVisible(False)
        for item in self.coin_opcond_list:
            item.setVisible(False)
        for item in self.coin_optest_list:
            item.setVisible(False)
        for item in self.coin_rwftvd_list:
            item.setVisible(False)
        for item in self.coin_esczom_list:
            item.setVisible(True)
        for item in self.coin_optimz_list:
            item.setVisible(True)
        for item in self.coin_period_list:
            item.setVisible(True)
        for item in self.coin_gaopti_list:
            item.setVisible(True)

        self.cva_pushButton_04.setText('GA 변수범위 로딩(F9)')
        self.cva_pushButton_05.setText('GA 변수범위 저장(F12)')

        self.image_label1.setVisible(False)
        self.cvc_labellllll_04.setText(gaoptext)
        self.cvc_labellllll_05.setVisible(False)
        self.cvc_pushButton_21.setVisible(False)
        self.cvc_pushButton_22.setVisible(False)
        self.cvc_pushButton_23.setVisible(False)
        self.cvc_pushButton_24.setVisible(False)
        self.cvc_pushButton_25.setVisible(False)
        self.cvc_pushButton_26.setVisible(False)
        self.cChangeSvjButtonColor()

    def cvjButtonClicked_04(self):
        self.cs_textEditttt_05.setGeometry(7, 10, 497, 1347 if self.extend_window else 740)
        self.cs_textEditttt_06.setGeometry(509, 10, 497, 1347 if self.extend_window else 740)

        self.cvc_comboBoxxx_02.setGeometry(1012, 10, 165, 30)
        self.cvc_lineEdittt_02.setGeometry(1182, 10, 165, 30)
        self.cvc_pushButton_03.setGeometry(1012, 45, 165, 30)
        self.cvc_pushButton_04.setGeometry(1182, 45, 165, 30)

        self.cva_comboBoxxx_01.setGeometry(1012, 80, 165, 30)
        self.cva_lineEdittt_01.setGeometry(1182, 80, 165, 30)
        self.cva_pushButton_04.setGeometry(1012, 115, 165, 30)
        self.cva_pushButton_05.setGeometry(1182, 115, 165, 30)

        self.cs_textEditttt_01.setVisible(False)
        self.cs_textEditttt_02.setVisible(False)
        self.cs_textEditttt_03.setVisible(False)
        self.cs_textEditttt_04.setVisible(False)
        self.cs_textEditttt_05.setVisible(True)
        self.cs_textEditttt_06.setVisible(True)

        for item in self.coin_datedt_list:
            item.setVisible(False)
        for item in self.coin_backte_list:
            item.setVisible(False)
        for item in self.coin_opcond_list:
            item.setVisible(False)
        for item in self.coin_detail_list:
            item.setVisible(False)
        for item in self.coin_baklog_list:
            item.setVisible(False)
        for item in self.coin_optest_list:
            item.setVisible(False)
        for item in self.coin_rwftvd_list:
            item.setVisible(False)
        for item in self.coin_esczom_list:
            item.setVisible(False)
        for item in self.coin_optimz_list:
            item.setVisible(False)
        for item in self.coin_period_list:
            item.setVisible(True)
        for item in self.coin_gaopti_list:
            item.setVisible(True)

        self.cva_pushButton_04.setText('GA 변수범위 로딩')
        self.cva_pushButton_05.setText('GA 변수범위 저장')
        self.cvc_pushButton_03.setText('최적화 변수범위 로딩')
        self.cvc_pushButton_04.setText('최적화 변수범위 저장')

        self.cvc_pushButton_06.setVisible(False)
        self.cvc_pushButton_07.setVisible(False)
        self.cvc_pushButton_08.setVisible(False)
        self.cvc_pushButton_27.setVisible(False)
        self.cvc_pushButton_28.setVisible(False)
        self.cvc_pushButton_29.setVisible(False)

        self.cva_pushButton_01.setVisible(False)
        self.cva_pushButton_02.setVisible(False)
        self.cva_pushButton_03.setVisible(False)

        self.cvc_comboBoxxx_02.setVisible(True)
        self.cvc_lineEdittt_02.setVisible(True)
        self.cvc_pushButton_03.setVisible(True)
        self.cvc_pushButton_04.setVisible(True)

        self.cvc_pushButton_11.setVisible(True)

        self.image_label1.setVisible(True)
        self.cvc_labellllll_05.setVisible(True)
        self.cvc_labellllll_04.setText(gaoptext)
        self.cvc_labellllll_05.setText(vedittxt)
        self.cvc_pushButton_21.setVisible(True)
        self.cvc_pushButton_22.setVisible(True)
        self.cvc_pushButton_23.setVisible(True)
        self.cvc_pushButton_24.setVisible(False)
        self.cvc_pushButton_25.setVisible(False)
        self.cvc_pushButton_26.setVisible(False)
        self.cChangeSvjButtonColor()

    def cvjButtonClicked_05(self):
        self.cs_textEditttt_03.setGeometry(7, 10, 647, 740 if self.extend_window else 463)
        self.cs_textEditttt_04.setGeometry(7, 756 if self.extend_window else 478, 647, 602 if self.extend_window else 272)
        self.cs_textEditttt_05.setGeometry(659, 10, 347, 1347 if self.extend_window else 740)

        self.cvc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.cvc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.cvc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.cvc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.czoo_pushButon_01.setGeometry(599, 15, 50, 20)
        self.czoo_pushButon_02.setGeometry(599, 761 if self.extend_window else 483, 50, 20)

        self.czoo_pushButon_01.setText('확대(esc)')
        self.czoo_pushButon_02.setText('확대(esc)')

        self.cs_textEditttt_01.setVisible(False)
        self.cs_textEditttt_02.setVisible(False)
        self.cs_textEditttt_03.setVisible(True)
        self.cs_textEditttt_04.setVisible(True)
        self.cs_textEditttt_05.setVisible(True)
        self.cs_textEditttt_06.setVisible(False)

        for item in self.coin_datedt_list:
            item.setVisible(False)
        for item in self.coin_backte_list:
            item.setVisible(False)
        for item in self.coin_opcond_list:
            item.setVisible(False)
        for item in self.coin_detail_list:
            item.setVisible(False)
        for item in self.coin_baklog_list:
            item.setVisible(False)
        for item in self.coin_optest_list:
            item.setVisible(False)
        for item in self.coin_gaopti_list:
            item.setVisible(False)
        for item in self.coin_rwftvd_list:
            item.setVisible(False)
        for item in self.coin_esczom_list:
            item.setVisible(True)
        for item in self.coin_optimz_list:
            item.setVisible(True)
        for item in self.coin_period_list:
            item.setVisible(True)

        self.cvc_pushButton_03.setText('최적화 변수범위 로딩(F9)')
        self.cvc_pushButton_04.setText('최적화 변수범위 저장(F12)')

        self.image_label1.setVisible(False)
        self.cvc_labellllll_04.setText(optitext)
        self.cvc_labellllll_05.setVisible(False)
        self.cvc_pushButton_21.setVisible(False)
        self.cvc_pushButton_22.setVisible(False)
        self.cvc_pushButton_23.setVisible(False)
        self.cvc_pushButton_24.setVisible(False)
        self.cvc_pushButton_25.setVisible(False)
        self.cvc_pushButton_26.setVisible(False)
        self.cChangeSvjButtonColor()

    def cvjButtonClicked_06(self):
        self.cs_textEditttt_01.setGeometry(7, 10, 497, 740 if self.extend_window else 463)
        self.cs_textEditttt_02.setGeometry(7, 756 if self.extend_window else 478, 497, 602 if self.extend_window else 272)
        self.cs_textEditttt_03.setGeometry(509, 10, 497, 740 if self.extend_window else 463)
        self.cs_textEditttt_04.setGeometry(509, 756 if self.extend_window else 478, 497, 602 if self.extend_window else 272)

        self.cvjb_comboBoxx_01.setGeometry(1012, 10, 165, 30)
        self.cvjb_pushButon_01.setGeometry(1182, 10, 165, 30)
        self.cvjs_comboBoxx_01.setGeometry(1012, 478, 165, 30)
        self.cvjs_pushButon_01.setGeometry(1182, 478, 165, 30)

        self.cvc_comboBoxxx_02.setGeometry(1012, 115, 165, 30)
        self.cvc_lineEdittt_02.setGeometry(1182, 115, 165, 30)
        self.cvc_pushButton_03.setGeometry(1012, 150, 165, 30)
        self.cvc_pushButton_04.setGeometry(1182, 150, 165, 30)

        self.cs_textEditttt_01.setVisible(True)
        self.cs_textEditttt_02.setVisible(True)
        self.cs_textEditttt_03.setVisible(True)
        self.cs_textEditttt_04.setVisible(True)
        self.cs_textEditttt_05.setVisible(False)
        self.cs_textEditttt_06.setVisible(False)

        for item in self.coin_datedt_list:
            item.setVisible(False)
        for item in self.coin_backte_list:
            item.setVisible(False)
        for item in self.coin_opcond_list:
            item.setVisible(False)
        for item in self.coin_detail_list:
            item.setVisible(False)
        for item in self.coin_baklog_list:
            item.setVisible(False)
        for item in self.coin_gaopti_list:
            item.setVisible(False)
        for item in self.coin_optest_list:
            item.setVisible(False)
        for item in self.coin_rwftvd_list:
            item.setVisible(False)
        for item in self.coin_esczom_list:
            item.setVisible(False)
        for item in self.coin_optimz_list:
            item.setVisible(True)
        for item in self.coin_period_list:
            item.setVisible(True)

        self.cvjb_pushButon_01.setText('매수전략 로딩')
        self.cvjs_pushButon_01.setText('매도전략 로딩')

        self.cvjb_comboBoxx_01.setVisible(True)
        self.cvjb_pushButon_01.setVisible(True)
        self.cvjs_comboBoxx_01.setVisible(True)
        self.cvjs_pushButon_01.setVisible(True)

        self.cvc_lineEdittt_04.setVisible(False)
        self.cvc_pushButton_13.setVisible(False)
        self.cvc_lineEdittt_05.setVisible(False)
        self.cvc_pushButton_14.setVisible(False)

        self.image_label1.setVisible(False)
        self.cvc_labellllll_04.setText(optitext)
        self.cvc_labellllll_05.setVisible(False)
        self.cvc_pushButton_21.setVisible(False)
        self.cvc_pushButton_22.setVisible(False)
        self.cvc_pushButton_23.setVisible(False)
        self.cvc_pushButton_24.setVisible(True)
        self.cvc_pushButton_25.setVisible(True)
        self.cvc_pushButton_26.setVisible(True)
        self.cChangeSvjButtonColor()

    def cvjButtonClicked_07(self):
        self.cs_textEditttt_01.setVisible(False)
        self.cs_textEditttt_02.setVisible(False)
        self.cs_textEditttt_03.setVisible(False)
        self.cs_textEditttt_04.setVisible(False)
        self.cs_textEditttt_05.setVisible(False)
        self.cs_textEditttt_06.setVisible(False)
        self.cs_textEditttt_07.setVisible(False)
        self.cs_textEditttt_08.setVisible(False)

        self.cs_textEditttt_09.setGeometry(7, 10, 1000, 1308 if self.extend_window else 703)
        self.cs_progressBar_01.setGeometry(7, 1323 if self.extend_window else 718, 830, 30)
        self.cs_pushButtonn_08.setGeometry(842, 1323 if self.extend_window else 718, 165, 30)

        for item in self.coin_esczom_list:
            item.setVisible(False)
        for item in self.coin_detail_list:
            item.setVisible(False)
        for item in self.coin_baklog_list:
            item.setVisible(True)
        self.cs_pushButtonn_08.setStyleSheet(style_bc_by)
        self.cChangeSvjButtonColor()

    def cvjButtonClicked_08(self):
        self.cs_textEditttt_01.setVisible(False)
        self.cs_textEditttt_02.setVisible(False)
        self.cs_textEditttt_03.setVisible(False)
        self.cs_textEditttt_04.setVisible(False)
        self.cs_textEditttt_05.setVisible(False)
        self.cs_textEditttt_06.setVisible(False)
        self.cs_textEditttt_07.setVisible(False)
        self.cs_textEditttt_08.setVisible(False)

        self.cs_tableWidget_01.setGeometry(7, 40, 1000, 1318 if self.extend_window else 713)
        self.cs_tableWidget_01.setRowCount(60 if self.extend_window else 32)

        for item in self.coin_esczom_list:
            item.setVisible(False)
        for item in self.coin_baklog_list:
            item.setVisible(False)
        for item in self.coin_detail_list:
            item.setVisible(True)
        self.cChangeSvjButtonColor()

    def cvjButtonClicked_09(self):
        self.cs_textEditttt_01.setGeometry(7, 10, 1000, 740 if self.extend_window else 463)
        self.cs_textEditttt_02.setGeometry(7, 756 if self.extend_window else 478, 1000, 602 if self.extend_window else 272)

        self.cvjb_comboBoxx_01.setGeometry(1012, 10, 165, 25)
        self.cvjb_pushButon_01.setGeometry(1012, 40, 165, 30)
        self.cvjs_comboBoxx_01.setGeometry(1012, 478, 165, 25)
        self.cvjs_pushButon_01.setGeometry(1012, 508, 165, 30)

        self.czoo_pushButon_01.setGeometry(952, 15, 50, 20)
        self.czoo_pushButon_02.setGeometry(952, 761 if self.extend_window else 483, 50, 20)

        self.czoo_pushButon_01.setText('확대(esc)')
        self.czoo_pushButon_02.setText('확대(esc)')

        self.cs_textEditttt_01.setVisible(True)
        self.cs_textEditttt_02.setVisible(True)
        self.cs_textEditttt_03.setVisible(False)
        self.cs_textEditttt_04.setVisible(False)
        self.cs_textEditttt_05.setVisible(False)
        self.cs_textEditttt_06.setVisible(False)

        for item in self.coin_optimz_list:
            item.setVisible(False)
        for item in self.coin_period_list:
            item.setVisible(False)
        for item in self.coin_opcond_list:
            item.setVisible(False)
        for item in self.coin_detail_list:
            item.setVisible(False)
        for item in self.coin_baklog_list:
            item.setVisible(False)
        for item in self.coin_gaopti_list:
            item.setVisible(False)
        for item in self.coin_optest_list:
            item.setVisible(False)
        for item in self.coin_rwftvd_list:
            item.setVisible(False)
        for item in self.coin_datedt_list:
            item.setVisible(True)
        for item in self.coin_esczom_list:
            item.setVisible(True)
        for item in self.coin_backte_list:
            item.setVisible(True)

        self.cvjb_pushButon_01.setText('매수전략 로딩(F1)')
        self.cvjs_pushButon_01.setText('매도전략 로딩(F5)')

        self.image_label1.setVisible(False)
        self.cvc_labellllll_05.setVisible(False)
        self.cvc_pushButton_21.setVisible(False)
        self.cvc_pushButton_22.setVisible(False)
        self.cvc_pushButton_23.setVisible(False)
        self.cvc_pushButton_24.setVisible(False)
        self.cvc_pushButton_25.setVisible(False)
        self.cvc_pushButton_26.setVisible(False)
        self.cChangeSvjButtonColor()

    def cvjButtonClicked_10(self):
        self.cs_textEditttt_07.setGeometry(7, 10, 497, 1347 if self.extend_window else 740)
        self.cs_textEditttt_08.setGeometry(509, 10, 497, 1347 if self.extend_window else 740)

        self.cs_textEditttt_01.setVisible(False)
        self.cs_textEditttt_02.setVisible(False)
        self.cs_textEditttt_03.setVisible(False)
        self.cs_textEditttt_04.setVisible(False)
        self.cs_textEditttt_05.setVisible(False)
        self.cs_textEditttt_06.setVisible(False)

        for item in self.coin_esczom_list:
            item.setVisible(False)
        for item in self.coin_backte_list:
            item.setVisible(False)
        for item in self.coin_detail_list:
            item.setVisible(False)
        for item in self.coin_baklog_list:
            item.setVisible(False)
        for item in self.coin_gaopti_list:
            item.setVisible(False)
        for item in self.coin_optest_list:
            item.setVisible(False)
        for item in self.coin_rwftvd_list:
            item.setVisible(False)
        for item in self.coin_datedt_list:
            item.setVisible(False)
        for item in self.coin_optimz_list:
            item.setVisible(True)
        for item in self.coin_period_list:
            item.setVisible(True)
        for item in self.coin_opcond_list:
            item.setVisible(True)

        self.cvc_lineEdittt_04.setVisible(False)
        self.cvc_lineEdittt_05.setVisible(False)
        self.cvc_pushButton_13.setVisible(False)
        self.cvc_pushButton_14.setVisible(False)

        self.cvc_comboBoxxx_08.setVisible(False)
        self.cvc_lineEdittt_03.setVisible(False)
        self.cvc_pushButton_09.setVisible(False)
        self.cvc_pushButton_10.setVisible(False)

        self.cvc_comboBoxxx_02.setVisible(False)
        self.cvc_lineEdittt_02.setVisible(False)
        self.cvc_pushButton_03.setVisible(False)
        self.cvc_pushButton_04.setVisible(False)

        self.image_label1.setVisible(True)
        self.cvc_labellllll_01.setVisible(False)
        self.cvc_labellllll_04.setVisible(True)
        self.cvc_labellllll_05.setVisible(True)
        self.cvc_labellllll_04.setText(condtext)
        self.cvc_labellllll_05.setText(cedittxt)
        self.cvc_pushButton_21.setVisible(False)
        self.cvc_pushButton_22.setVisible(False)
        self.cvc_pushButton_23.setVisible(False)
        self.cvc_pushButton_24.setVisible(False)
        self.cvc_pushButton_25.setVisible(False)
        self.cvc_pushButton_26.setVisible(False)
        self.cChangeSvjButtonColor()

    def cvjButtonClicked_11(self):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            back_club = True if (QApplication.keyboardModifiers() & Qt.ControlModifier) and (QApplication.keyboardModifiers() & Qt.AltModifier) else False
            if back_club and not self.backtest_engine:
                QMessageBox.critical(self, '오류 알림', '백테엔진을 먼저 실행하십시오.\n')
                return
            if not back_club and (not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier)):
                self.BackengineShow('코인')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            startday  = self.cvjb_dateEditt_01.date().toString('yyyyMMdd')
            endday    = self.cvjb_dateEditt_02.date().toString('yyyyMMdd')
            starttime = self.cvjb_lineEditt_02.text()
            endtime   = self.cvjb_lineEditt_03.text()
            betting   = self.cvjb_lineEditt_04.text()
            avgtime   = self.cvjb_lineEditt_05.text()
            buystg    = self.cvjb_comboBoxx_01.currentText()
            sellstg   = self.cvjs_comboBoxx_01.currentText()
            bl        = True if self.dict_set['블랙리스트추가'] else False

            if int(avgtime) not in self.avg_list:
                QMessageBox.critical(self, '오류 알림', '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                return
            if '' in (startday, endday, starttime, endtime, betting, avgtime):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if '' in (buystg, sellstg):
                QMessageBox.critical(self, '오류 알림', '전략을 저장하고 콤보박스에서 선택하십시오.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', '백테스트'))

            backQ.put((
                betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg, None, self.back_count,
                bl, False, None, None, back_club
            ))
            self.proc_backtester_bb = Process(
                target=BackTest,
                args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, '백테스트', 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
            )
            self.proc_backtester_bb.start()
            self.cvjButtonClicked_07()
            self.cs_progressBar_01.setValue(0)
            self.csicon_alert = True

    def cvjButtonClicked_12(self):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow('코인')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            startday  = self.cvjb_dateEditt_01.date().toString('yyyyMMdd')
            endday    = self.cvjb_dateEditt_02.date().toString('yyyyMMdd')
            starttime = self.cvjb_lineEditt_02.text()
            endtime   = self.cvjb_lineEditt_03.text()
            avgtime   = self.cvjb_lineEditt_05.text()
            buystg    = self.cvjb_comboBoxx_01.currentText()

            if int(avgtime) not in self.avg_list:
                QMessageBox.critical(self, '오류 알림', '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                return
            if '' in (startday, endday, starttime, endtime, avgtime):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if buystg == '':
                QMessageBox.critical(self, '오류 알림', '매수전략을 저장하고 콤보박스에서 선택하십시오.\n')
                return
            if 'self.tickcols' not in self.cs_textEditttt_01.toPlainText():
                QMessageBox.critical(self, '오류 알림', '현재 매수전략이 백파인더용이 아닙니다.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', '백파인더'))

            backQ.put((avgtime, startday, endday, starttime, endtime, buystg, self.back_count))
            self.proc_backtester_bf = Process(
                target=BackFinder,
                args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, '백파인더', 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
            )
            self.proc_backtester_bf.start()
            self.cvjButtonClicked_07()
            self.cs_progressBar_01.setValue(0)
            self.csicon_alert = True

    def cvjButtonClicked_13(self):
        if self.cs_textEditttt_01.isVisible():
            self.cs_textEditttt_01.clear()
            self.cs_textEditttt_02.clear()
            self.cs_textEditttt_01.append(example_finder if self.dict_set['거래소'] == '업비트' else example_finder_future)

    def cvjButtonClicked_14(self, back_name):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow('코인')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            randomopti  = True if (QApplication.keyboardModifiers() & Qt.AltModifier) and 'B' not in back_name else False
            starttime   = self.cvjb_lineEditt_02.text()
            endtime     = self.cvjb_lineEditt_03.text()
            betting     = self.cvjb_lineEditt_04.text()
            buystg      = self.cvc_comboBoxxx_01.currentText()
            sellstg     = self.cvc_comboBoxxx_08.currentText()
            optivars    = self.cvc_comboBoxxx_02.currentText()
            ccount      = self.cvc_comboBoxxx_06.currentText()
            optistd     = self.cvc_comboBoxxx_07.currentText()
            weeks_train = self.cvc_comboBoxxx_03.currentText()
            weeks_valid = self.cvc_comboBoxxx_04.currentText()
            weeks_test  = self.cvc_comboBoxxx_05.currentText()
            benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
            bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')
            optunasampl = self.op_comboBoxxxx_01.currentText()
            optunafixv  = self.op_lineEditttt_01.text()
            optunacount = self.op_lineEditttt_02.text()
            optunaautos = 1 if self.op_checkBoxxxx_01.isChecked() else 0

            if 'VC' in back_name and weeks_train != 'ALL' and int(weeks_train) % int(weeks_valid) != 0:
                QMessageBox.critical(self, '오류 알림', '교차검증의 학습기간은 검증기간의 배수로 선택하십시오.\n')
                return
            if '' in (starttime, endtime, betting):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if '' in (buystg, sellstg):
                QMessageBox.critical(self, '오류 알림', '전략을 저장하고 콤보박스에서 선택하십시오.\n')
                return
            if optivars == '':
                QMessageBox.critical(self, '오류 알림', '변수를 설장하고 콤보박스에서 선택하십시오.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', '최적화'))

            backQ.put((
                betting, starttime, endtime, buystg, sellstg, optivars, None, ccount, self.dict_set['최적화기준값제한'],
                optistd, self.back_count, False, None, None, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday,
                optunasampl, optunafixv, optunacount, optunaautos, randomopti
            ))
            if back_name == '최적화O':
                self.proc_backtester_o = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_o.start()
            elif back_name == '최적화OV':
                self.proc_backtester_ov = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_ov.start()
            elif back_name == '최적화OVC':
                self.proc_backtester_ovc = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_ovc.start()
            elif back_name == '최적화B':
                self.proc_backtester_b = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_b.start()
            elif back_name == '최적화BV':
                self.proc_backtester_bv = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_bv.start()
            elif back_name == '최적화BVC':
                self.proc_backtester_bvc = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_bvc.start()
            elif back_name == '최적화OT':
                self.proc_backtester_ot = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_ot.start()
            elif back_name == '최적화OVT':
                self.proc_backtester_ovt = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_ovt.start()
            elif back_name == '최적화OVCT':
                self.proc_backtester_ovct = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_ovct.start()
            elif back_name == '최적화BT':
                self.proc_backtester_bt = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_bt.start()
            elif back_name == '최적화BVT':
                self.proc_backtester_bvt = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_bvt.start()
            else:
                self.proc_backtester_bvct = Process(
                    target=Optimize,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_bvct.start()
            self.cvjButtonClicked_07()
            self.cs_progressBar_01.setValue(0)
            self.csicon_alert = True

    def cvjButtonClicked_15(self, back_name):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow('코인')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            randomopti  = True if (QApplication.keyboardModifiers() & Qt.AltModifier) and 'B' not in back_name else False
            startday    = self.cvjb_dateEditt_01.date().toString('yyyyMMdd')
            endday      = self.cvjb_dateEditt_02.date().toString('yyyyMMdd')
            starttime   = self.cvjb_lineEditt_02.text()
            endtime     = self.cvjb_lineEditt_03.text()
            betting     = self.cvjb_lineEditt_04.text()
            buystg      = self.cvc_comboBoxxx_01.currentText()
            sellstg     = self.cvc_comboBoxxx_08.currentText()
            optivars    = self.cvc_comboBoxxx_02.currentText()
            ccount      = self.cvc_comboBoxxx_06.currentText()
            optistd     = self.cvc_comboBoxxx_07.currentText()
            weeks_train = self.cvc_comboBoxxx_03.currentText()
            weeks_valid = self.cvc_comboBoxxx_04.currentText()
            weeks_test  = self.cvc_comboBoxxx_05.currentText()
            benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
            bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')

            if 'VC' in back_name and weeks_train != 'ALL' and int(weeks_train) % int(weeks_valid) != 0:
                QMessageBox.critical(self, '오류 알림', '교차검증의 학습기간은 검증기간의 배수로 선택하십시오.\n')
                return
            if weeks_train == 'ALL':
                QMessageBox.critical(self, '오류 알림', '전진분석 학습기간은 전체를 선택할 수 없습니다.\n')
                return
            if '' in (starttime, endtime, betting):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if '' in (buystg, sellstg):
                QMessageBox.critical(self, '오류 알림', '전략을 저장하고 콤보박스에서 선택하십시오.\n')
                return
            if optivars == '':
                QMessageBox.critical(self, '오류 알림', '변수를 설장하고 콤보박스에서 선택하십시오.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', '전진분석'))

            backQ.put((
                betting, startday, endday, starttime, endtime, buystg, sellstg, optivars, None, ccount, self.dict_set['최적화기준값제한'],
                optistd, self.back_count, False, None, None, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday, randomopti
            ))
            if back_name == '전진분석OR':
                self.proc_backtester_or = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_or.start()
            elif back_name == '전진분석ORV':
                self.proc_backtester_orv = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_orv.start()
            elif back_name == '전진분석ORVC':
                self.proc_backtester_orvc = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_orvc.start()
            elif back_name == '전진분석BR':
                self.proc_backtester_br = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_br.start()
            elif back_name == '전진분석BRV':
                self.proc_backtester_brv = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_brv.start()
            else:
                self.proc_backtester_brvc = Process(
                    target=RollingWalkForwardTest,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_brvc.start()
            self.cvjButtonClicked_07()
            self.cs_progressBar_01.setValue(0)
            self.csicon_alert = True

    def cvjButtonClicked_16(self, back_name):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow('코인')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            starttime   = self.cvjb_lineEditt_02.text()
            endtime     = self.cvjb_lineEditt_03.text()
            betting     = self.cvjb_lineEditt_04.text()
            buystg      = self.cvc_comboBoxxx_01.currentText()
            sellstg     = self.cvc_comboBoxxx_08.currentText()
            optivars    = self.cva_comboBoxxx_01.currentText()
            optistd     = self.cvc_comboBoxxx_07.currentText()
            weeks_train = self.cvc_comboBoxxx_03.currentText()
            weeks_valid = self.cvc_comboBoxxx_04.currentText()
            weeks_test  = self.cvc_comboBoxxx_05.currentText()
            benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
            bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')

            if 'VC' in back_name and weeks_train != 'ALL' and int(weeks_train) % int(weeks_valid) != 0:
                QMessageBox.critical(self, '오류 알림', '교차검증의 학습기간은 검증기간의 배수로 선택하십시오.\n')
                return
            if '' in (starttime, endtime, betting):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if '' in (buystg, sellstg):
                QMessageBox.critical(self, '오류 알림', '전략을 저장하고 콤보박스에서 선택하십시오.\n')
                return
            if optivars == '':
                QMessageBox.critical(self, '오류 알림', '변수를 설장하고 콤보박스에서 선택하십시오.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', 'GA최적화'))

            backQ.put((
                betting, starttime, endtime, buystg, sellstg, optivars, None, self.dict_set['최적화기준값제한'], optistd,
                self.back_count, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday
            ))
            if back_name == '최적화OG':
                self.proc_backtester_og = Process(
                    target=OptimizeGeneticAlgorithm,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_og.start()
            elif back_name == '최적화OGV':
                self.proc_backtester_ogv = Process(
                    target=OptimizeGeneticAlgorithm,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_ogv.start()
            else:
                self.proc_backtester_ogvc = Process(
                    target=OptimizeGeneticAlgorithm,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_ogvc.start()
            self.cvjButtonClicked_07()
            self.cs_progressBar_01.setValue(0)
            self.csicon_alert = True

    def cvjButtonClicked_17(self, back_name):
        if self.BacktestProcessAlive():
            QMessageBox.critical(self, '오류 알림', '현재 백테스터가 실행중입니다.\n중복 실행할 수 없습니다.\n')
        else:
            if not self.backtest_engine or (QApplication.keyboardModifiers() & Qt.ControlModifier):
                self.BackengineShow('코인')
                return
            if not self.back_condition:
                QMessageBox.critical(self, '오류 알림', '이전 백테스트를 중지하고 있습니다.\n잠시 후 다시 시도하십시오.\n')
                return

            starttime   = self.cvjb_lineEditt_02.text()
            endtime     = self.cvjb_lineEditt_03.text()
            betting     = self.cvjb_lineEditt_04.text()
            avgtime     = self.cvjb_lineEditt_05.text()
            buystg      = self.cvo_comboBoxxx_01.currentText()
            sellstg     = self.cvo_comboBoxxx_02.currentText()
            bcount      = self.cvo_lineEdittt_03.text()
            scount      = self.cvo_lineEdittt_04.text()
            rcount      = self.cvo_lineEdittt_05.text()
            optistd     = self.cvc_comboBoxxx_07.currentText()
            weeks_train = self.cvc_comboBoxxx_03.currentText()
            weeks_valid = self.cvc_comboBoxxx_04.currentText()
            weeks_test  = self.cvc_comboBoxxx_05.currentText()
            benginesday = self.be_dateEdittttt_01.date().toString('yyyyMMdd')
            bengineeday = self.be_dateEdittttt_02.date().toString('yyyyMMdd')

            if weeks_train != 'ALL' and int(weeks_train) % int(weeks_valid) != 0:
                QMessageBox.critical(self, '오류 알림', '교차검증의 학습기간은 검증기간의 배수로 선택하십시오.\n')
                return
            if int(avgtime) not in self.avg_list:
                QMessageBox.critical(self, '오류 알림', '백테엔진 시작 시 포함되지 않은 평균값틱수를 사용하였습니다.\n현재의 틱수로 백테스팅하려면 백테엔진을 다시 시작하십시오.\n')
                return
            if '' in (starttime, endtime, betting, avgtime, bcount, scount, rcount):
                QMessageBox.critical(self, '오류 알림', '일부 설정값이 공백 상태입니다.\n')
                return
            if '' in (buystg, sellstg):
                QMessageBox.critical(self, '오류 알림', '조건을 저장하고 콤보박스에서 선택하십시오.\n')
                return

            self.ClearBacktestQ()
            for bpq in self.back_pques:
                bpq.put(('백테유형', '조건최적화'))

            backQ.put((
                betting, avgtime, starttime, endtime, buystg, sellstg, self.dict_set['최적화기준값제한'], optistd, bcount,
                scount, rcount, self.back_count, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday
            ))
            if back_name == '최적화OC':
                self.proc_backtester_oc = Process(
                    target=OptimizeConditions,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_oc.start()
            elif back_name == '최적화OCV':
                self.proc_backtester_ocv = Process(
                    target=OptimizeConditions,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_ocv.start()
            else:
                self.proc_backtester_ocvc = Process(
                    target=OptimizeConditions,
                    args=(windowQ, backQ, soundQ, totalQ, liveQ, self.back_pques, self.bact_pques, back_name, 'C' if self.dict_set['거래소'] == '업비트' else 'CF')
                )
                self.proc_backtester_ocvc.start()
            self.cvjButtonClicked_07()
            self.cs_progressBar_01.setValue(0)
            self.csicon_alert = True

    def cvjButtonClicked_26(self):
        opti_vars_text = self.cs_textEditttt_05.toPlainText()
        if opti_vars_text != '':
            ga_vars_text   = self.GetOptivarsToGavars(opti_vars_text)
            self.cs_textEditttt_06.clear()
            self.cs_textEditttt_06.append(ga_vars_text)
        else:
            QMessageBox.critical(self, '오류 알림', '현재 최적화 범위 코드가 공백 상태입니다.\n최적화 범위 코드를 작성하거나 로딩하십시오.\n')

    def cvjButtonClicked_27(self):
        ga_vars_text = self.cs_textEditttt_06.toPlainText()
        if ga_vars_text != '':
            opti_vars_text = self.GetGavarsToOptivars(ga_vars_text)
            self.cs_textEditttt_05.clear()
            self.cs_textEditttt_05.append(opti_vars_text)
        else:
            QMessageBox.critical(self, '오류 알림', '현재 GA 범위 코드가 공백 상태입니다.\nGA 범위 코드를 작성하거나 로딩하십시오.\n')

    def cvjButtonClicked_28(self):
        buystg  = self.cs_textEditttt_01.toPlainText()
        sellstg = self.cs_textEditttt_02.toPlainText()
        buystg_str, sellstg_str = self.GetStgtxtToVarstxt(buystg, sellstg)
        self.cs_textEditttt_03.clear()
        self.cs_textEditttt_04.clear()
        self.cs_textEditttt_03.append(buystg_str)
        self.cs_textEditttt_04.append(sellstg_str)

    def cvjButtonClicked_32(self):
        optivars = self.cs_textEditttt_05.toPlainText()
        gavars   = self.cs_textEditttt_06.toPlainText()
        optivars_str, gavars_str = self.GetStgtxtSort2(optivars, gavars)
        self.cs_textEditttt_05.clear()
        self.cs_textEditttt_06.clear()
        self.cs_textEditttt_05.append(optivars_str)
        self.cs_textEditttt_06.append(gavars_str)

    def cvjButtonClicked_33(self):
        buystg  = self.cs_textEditttt_03.toPlainText()
        sellstg = self.cs_textEditttt_04.toPlainText()
        buystg_str, sellstg_str = self.GetStgtxtSort(buystg, sellstg)
        self.cs_textEditttt_03.clear()
        self.cs_textEditttt_04.clear()
        self.cs_textEditttt_03.append(buystg_str)
        self.cs_textEditttt_04.append(sellstg_str)

    def cvjsButtonClicked_01(self):
        if self.cs_textEditttt_02.isVisible():
            con = sqlite3.connect(DB_STRATEGY)
            df = pd.read_sql('SELECT * FROM coinsell', con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cvjs_comboBoxx_01.clear()
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.cvjs_comboBoxx_01.addItem(index)
                    if i == 0:
                        self.cvjs_lineEditt_01.setText(index)
                self.cvjs_pushButon_04.setStyleSheet(style_bc_st)

    def cvjsButtonClicked_02(self):
        strategy_name = self.cvjs_lineEditt_01.text()
        strategy      = self.cs_textEditttt_02.toPlainText()
        strategy      = self.GetFixStrategy(strategy, '매도')

        if strategy_name == '':
            QMessageBox.critical(self, '오류 알림', '매도전략의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
        elif not text_not_in_special_characters(strategy_name):
            QMessageBox.critical(self, '오류 알림', '매도전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
        elif strategy == '':
            QMessageBox.critical(self, '오류 알림', '매도전략의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
        else:
            if 'self.tickcols' in strategy or (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest1(strategy):
                if proc_query.is_alive():
                    queryQ.put(('전략디비', f"DELETE FROM coinsell WHERE `index` = '{strategy_name}'"))
                    df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                    queryQ.put(('전략디비', df, 'coinsell', 'append'))
                self.cvjs_pushButon_04.setStyleSheet(style_bc_st)
                QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def cvjsButtonClicked_03(self):
        self.cs_textEditttt_02.clear()
        self.cs_textEditttt_02.append(coin_sell_var if self.dict_set['거래소'] == '업비트' else coin_future_sell_var)
        self.cvjs_pushButon_04.setStyleSheet(style_bc_st)

    def cvjsButtonClicked_04(self):
        strategy = self.cs_textEditttt_02.toPlainText()
        if strategy == '':
            QMessageBox.critical(self, '오류 알림', '매도전략의 코드가 공백 상태입니다.\n')
        else:
            buttonReply = QMessageBox.question(
                self, '전략시작', '매도전략의 연산을 시작합니다. 계속하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                if self.CoinStrategyProcessAlive():
                    cstgQ.put(('매도전략', strategy))
                self.cvjs_pushButon_04.setStyleSheet(style_bc_dk)
                self.cvjs_pushButon_14.setStyleSheet(style_bc_st)

    def cvjsButtonClicked_05(self):
        self.cs_textEditttt_02.append(coin_sell1)

    def cvjsButtonClicked_06(self):
        self.cs_textEditttt_02.append(coin_sell2)

    def cvjsButtonClicked_07(self):
        self.cs_textEditttt_02.append(coin_sell3)

    def cvjsButtonClicked_08(self):
        self.cs_textEditttt_02.append(coin_sell4)

    def cvjsButtonClicked_09(self):
        self.cs_textEditttt_02.append(coin_sell5)

    def cvjsButtonClicked_10(self):
        self.cs_textEditttt_02.append(coin_sell6)

    def cvjsButtonClicked_11(self):
        self.cs_textEditttt_02.append(coin_sell7)

    def cvjsButtonClicked_12(self):
        self.cs_textEditttt_02.append(coin_sell8)

    def cvjsButtonClicked_13(self):
        self.cs_textEditttt_02.append(coin_sell_signal if self.dict_set['거래소'] == '업비트' else coin_future_sell_signal)

    def cvjsButtonClicked_14(self):
        if self.CoinStrategyProcessAlive():
            cstgQ.put('매도전략중지')
        self.cvjs_pushButon_14.setStyleSheet(style_bc_dk)
        self.cvjs_pushButon_04.setStyleSheet(style_bc_st)

    def cvcButtonClicked_01(self):
        if self.cs_textEditttt_03.isVisible():
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql('SELECT * FROM coinoptibuy', con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cvc_comboBoxxx_01.clear()
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.cvc_comboBoxxx_01.addItem(index)
                    if i == 0:
                        self.cvc_lineEdittt_01.setText(index)

    def cvcButtonClicked_02(self):
        if self.cs_textEditttt_03.isVisible():
            strategy_name = self.cvc_lineEdittt_01.text()
            strategy      = self.cs_textEditttt_03.toPlainText()
            strategy      = self.GetFixStrategy(strategy, '매수')

            if strategy_name == '':
                QMessageBox.critical(self, '오류 알림', '최적화 매수전략의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
            elif not text_not_in_special_characters(strategy_name):
                QMessageBox.critical(self, '오류 알림', '최적화 매수전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
            elif strategy == '':
                QMessageBox.critical(self, '오류 알림', '최적화 매수전략의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
            else:
                if 'self.tickcols' in strategy or (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest1(strategy):
                    con = sqlite3.connect(DB_STRATEGY)
                    df = pd.read_sql(f"SELECT * FROM coinoptibuy WHERE `index` = '{strategy_name}'", con)
                    con.close()
                    if proc_query.is_alive():
                        if len(df) > 0:
                            query = f"UPDATE coinoptibuy SET 전략코드 = '{strategy}' WHERE `index` = '{strategy_name}'"
                            queryQ.put(('전략디비', query))
                        else:
                            data = [
                                strategy,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.,
                                9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999., 9999.
                            ]
                            columns = [
                                '전략코드',
                                '변수0', '변수1', '변수2', '변수3', '변수4', '변수5', '변수6', '변수7', '변수8', '변수9',
                                '변수10', '변수11', '변수12', '변수13', '변수14', '변수15', '변수16', '변수17', '변수18', '변수19',
                                '변수20', '변수21', '변수22', '변수23', '변수24', '변수25', '변수26', '변수27', '변수28', '변수29',
                                '변수30', '변수31', '변수32', '변수33', '변수34', '변수35', '변수36', '변수37', '변수38', '변수39',
                                '변수40', '변수41', '변수42', '변수43', '변수44', '변수45', '변수46', '변수47', '변수48', '변수49',
                                '변수50', '변수51', '변수52', '변수53', '변수54', '변수55', '변수56', '변수57', '변수58', '변수59',
                                '변수60', '변수61', '변수62', '변수63', '변수64', '변수65', '변수66', '변수67', '변수68', '변수69',
                                '변수70', '변수71', '변수72', '변수73', '변수74', '변수75', '변수76', '변수77', '변수78', '변수79',
                                '변수80', '변수81', '변수82', '변수83', '변수84', '변수85', '변수86', '변수87', '변수88', '변수89',
                                '변수90', '변수91', '변수92', '변수93', '변수94', '변수95', '변수96', '변수97', '변수98', '변수99',
                                '변수100', '변수101', '변수102', '변수103', '변수104', '변수105', '변수106', '변수107', '변수108', '변수109',
                                '변수110', '변수111', '변수112', '변수113', '변수114', '변수115', '변수116', '변수117', '변수118', '변수119',
                                '변수120', '변수121', '변수122', '변수123', '변수124', '변수125', '변수126', '변수127', '변수128', '변수129',
                                '변수130', '변수131', '변수132', '변수133', '변수134', '변수135', '변수136', '변수137', '변수138', '변수139',
                                '변수140', '변수141', '변수142', '변수143', '변수144', '변수145', '변수146', '변수147', '변수148', '변수149',
                                '변수150', '변수151', '변수152', '변수153', '변수154', '변수155', '변수156', '변수157', '변수158', '변수159',
                                '변수160', '변수161', '변수162', '변수163', '변수164', '변수165', '변수166', '변수167', '변수168', '변수169',
                                '변수170', '변수171', '변수172', '변수173', '변수174', '변수175', '변수176', '변수177', '변수178', '변수179',
                                '변수180', '변수181', '변수182', '변수183', '변수184', '변수185', '변수186', '변수187', '변수188', '변수189',
                                '변수190', '변수191', '변수192', '변수193', '변수194', '변수195', '변수196', '변수197', '변수198', '변수199'
                            ]
                            df = pd.DataFrame([data], columns=columns, index=[strategy_name])
                            queryQ.put(('전략디비', df, 'coinoptibuy', 'append'))
                        QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def cvcButtonClicked_03(self):
        if self.cs_textEditttt_05.isVisible():
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql('SELECT * FROM coinoptivars', con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cvc_comboBoxxx_02.clear()
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.cvc_comboBoxxx_02.addItem(index)
                    if i == 0:
                        self.cvc_lineEdittt_02.setText(index)

    def cvcButtonClicked_04(self):
        if self.cs_textEditttt_05.isVisible():
            strategy_name = self.cvc_lineEdittt_02.text()
            strategy      = self.cs_textEditttt_05.toPlainText()
            if strategy_name == '':
                QMessageBox.critical(self, '오류 알림', '변수범위의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
            elif not text_not_in_special_characters(strategy_name):
                QMessageBox.critical(self, '오류 알림', '변수범위의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
            elif strategy == '':
                QMessageBox.critical(self, '오류 알림', '변수범위의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
            else:
                if (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest2(strategy):
                    if proc_query.is_alive():
                        queryQ.put(('전략디비', f"DELETE FROM coinoptivars WHERE `index` = '{strategy_name}'"))
                        df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                        queryQ.put(('전략디비', df, 'coinoptivars', 'append'))
                        QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def cvcButtonClicked_05(self):
        if self.cs_textEditttt_04.isVisible():
            con = sqlite3.connect(DB_STRATEGY)
            df  = pd.read_sql('SELECT * FROM coinoptisell', con).set_index('index')
            con.close()
            if len(df) > 0:
                self.cvc_comboBoxxx_08.clear()
                indexs = list(df.index)
                indexs.sort()
                for i, index in enumerate(indexs):
                    self.cvc_comboBoxxx_08.addItem(index)
                    if i == 0:
                        self.cvc_lineEdittt_03.setText(index)

    def cvcButtonClicked_06(self):
        if self.cs_textEditttt_04.isVisible():
            strategy_name = self.cvc_lineEdittt_03.text()
            strategy      = self.cs_textEditttt_04.toPlainText()
            strategy      = self.GetFixStrategy(strategy, '매도')

            if strategy_name == '':
                QMessageBox.critical(self, '오류 알림', '최적화 매도전략의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
            elif not text_not_in_special_characters(strategy_name):
                QMessageBox.critical(self, '오류 알림', '최적화 매도전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
            elif strategy == '':
                QMessageBox.critical(self, '오류 알림', '최적화 매도전략의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
            else:
                if 'self.tickcols' in strategy or (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest1(strategy):
                    if proc_query.is_alive():
                        queryQ.put(('전략디비', f"DELETE FROM coinoptisell WHERE `index` = '{strategy_name}'"))
                        df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                        queryQ.put(('전략디비', df, 'coinoptisell', 'append'))
                        QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def cvcButtonClicked_07(self):
        if self.cs_textEditttt_01.isVisible():
            self.cs_textEditttt_01.clear()
            self.cs_textEditttt_01.append(example_coin_buy if self.dict_set['거래소'] == '업비트' else example_coin_future_buy)
        if self.cs_textEditttt_02.isVisible():
            self.cs_textEditttt_02.clear()
            self.cs_textEditttt_02.append(example_coin_sell if self.dict_set['거래소'] == '업비트' else example_coin_future_sell)
        if self.cs_textEditttt_03.isVisible():
            self.cs_textEditttt_03.clear()
            if self.cvc_pushButton_24.isVisible():
                self.cs_textEditttt_03.append(example_coinopti_buy1 if self.dict_set['거래소'] == '업비트' else example_coinopti_future_buy1)
            else:
                self.cs_textEditttt_03.append(example_coinopti_buy2 if self.dict_set['거래소'] == '업비트' else example_coinopti_future_buy2)
        if self.cs_textEditttt_04.isVisible():
            self.cs_textEditttt_04.clear()
            if self.cvc_pushButton_24.isVisible():
                self.cs_textEditttt_04.append(example_coinopti_sell1 if self.dict_set['거래소'] == '업비트' else example_coinopti_future_sell1)
            else:
                self.cs_textEditttt_04.append(example_coinopti_sell2 if self.dict_set['거래소'] == '업비트' else example_coinopti_future_sell2)
        if self.cs_textEditttt_05.isVisible():
            self.cs_textEditttt_05.clear()
            self.cs_textEditttt_05.append(example_opti_vars if self.dict_set['거래소'] == '업비트' else example_opti_future_vars)
        if self.cs_textEditttt_06.isVisible():
            self.cs_textEditttt_06.clear()
            self.cs_textEditttt_06.append(example_vars if self.dict_set['거래소'] == '업비트' else example_future_vars)
        if self.cs_textEditttt_07.isVisible():
            self.cs_textEditttt_07.clear()
            self.cs_textEditttt_07.append(example_buyconds if self.dict_set['거래소'] == '업비트' else example_future_buyconds)
        if self.cs_textEditttt_08.isVisible():
            self.cs_textEditttt_08.clear()
            self.cs_textEditttt_08.append(example_sellconds if self.dict_set['거래소'] == '업비트' else example_future_sellconds)

    def cvcButtonClicked_09(self):
        tabl = 'coinoptivars' if not self.cva_pushButton_01.isVisible() else 'coinvars'
        stgy = self.cvc_comboBoxxx_01.currentText()
        opti = self.cvc_comboBoxxx_02.currentText() if not self.cva_pushButton_01.isVisible() else self.cva_comboBoxxx_01.currentText()
        name = self.cvc_lineEdittt_04.text()
        if stgy == '' or opti == '' or name == '':
            QMessageBox.critical(self, '오류 알림', '전략 및 범위 코드를 선택하거나\n매수전략의 이름을 입력하십시오.\n')
            return
        elif not text_not_in_special_characters(name):
            QMessageBox.critical(self, '오류 알림', '매수전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
            return

        con = sqlite3.connect(DB_STRATEGY)
        df  = pd.read_sql('SELECT * FROM coinoptibuy', con).set_index('index')
        stg = df['전략코드'][stgy]
        df  = pd.read_sql(f'SELECT * FROM "{tabl}"', con).set_index('index')
        opt = df['전략코드'][opti]
        con.close()

        try:
            exec(compile(opt, '<string>', 'exec'), None, locals())
            for i in range(len(self.vars)):
                stg = stg.replace(f'self.vars[{i}]', f'{self.vars[i][1]}')
        except Exception as e:
            QMessageBox.critical(self, '오류 알림', f'{e}')
            return

        queryQ.put(('전략디비', f"DELETE FROM coinbuy WHERE `index` = '{name}'"))
        df = pd.DataFrame({'전략코드': [stg]}, index=[name])
        queryQ.put(('전략디비', df, 'coinbuy', 'append'))
        QMessageBox.information(self, '저장 알림', '최적값으로 매수전략을 저장하였습니다.\n')

    def cvcButtonClicked_10(self):
        tabl = 'coinoptivars' if not self.cva_pushButton_01.isVisible() else 'coinvars'
        stgy = self.cvc_comboBoxxx_08.currentText()
        opti = self.cvc_comboBoxxx_02.currentText() if not self.cva_pushButton_01.isVisible() else self.cva_comboBoxxx_01.currentText()
        name = self.cvc_lineEdittt_05.text()
        if stgy == '' or opti == '' or name == '':
            QMessageBox.critical(self, '오류 알림', '전략 및 범위 코드를 선택하거나\n매도전략의 이름을 입력하십시오.\n')
            return
        elif not text_not_in_special_characters(name):
            QMessageBox.critical(self, '오류 알림', '매도전략의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
            return

        con = sqlite3.connect(DB_STRATEGY)
        df  = pd.read_sql('SELECT * FROM coinoptisell', con).set_index('index')
        stg = df['전략코드'][stgy]
        df  = pd.read_sql(f'SELECT * FROM "{tabl}"', con).set_index('index')
        opt = df['전략코드'][opti]
        con.close()

        try:
            exec(compile(opt, '<string>', 'exec'), None, locals())
            for i in range(len(self.vars)):
                stg = stg.replace(f'self.vars[{i}]', f'{self.vars[i][1]}')
        except Exception as e:
            QMessageBox.critical(self, '오류 알림', f'{e}')
            return

        queryQ.put(('전략디비', f"DELETE FROM coinsell WHERE `index` = '{name}'"))
        df = pd.DataFrame({'전략코드': [stg]}, index=[name])
        queryQ.put(('전략디비', df, 'coinsell', 'append'))
        QMessageBox.information(self, '저장 알림', '최적값으로 매도전략을 저장하였습니다.\n')

    def cvcButtonClicked_11(self):
        self.dialog_std.show() if not self.dialog_std.isVisible() else self.dialog_std.close()

    def cvcButtonClicked_12(self):
        if not self.dialog_optuna.isVisible():
            if not self.optuna_window_open:
                self.op_lineEditttt_01.setText(self.dict_set['옵튜나고정변수'])
                self.op_lineEditttt_02.setText(str(self.dict_set['옵튜나실행횟수']))
                self.op_checkBoxxxx_01.setChecked(True) if self.dict_set['옵튜나자동스탭'] else self.op_checkBoxxxx_01.setChecked(False)
                self.op_comboBoxxxx_01.setCurrentText(self.dict_set['옵튜나샘플러'])
            self.dialog_optuna.show()
            self.optuna_window_open = True
        else:
            self.dialog_optuna.close()

    def cvaButtonClicked_01(self):
        con = sqlite3.connect(DB_STRATEGY)
        df  = pd.read_sql('SELECT * FROM coinvars', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.cva_comboBoxxx_01.clear()
            indexs = list(df.index)
            indexs.sort()
            for i, index in enumerate(indexs):
                self.cva_comboBoxxx_01.addItem(index)
                if i == 0:
                    self.cva_lineEdittt_01.setText(index)

    def cvaButtonClicked_02(self):
        strategy_name = self.cva_lineEdittt_01.text()
        strategy      = self.cs_textEditttt_06.toPlainText()
        if strategy_name == '':
            QMessageBox.critical(self, '오류 알림', 'GA범위의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
        elif not text_not_in_special_characters(strategy_name):
            QMessageBox.critical(self, '오류 알림', 'GA범위의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
        elif strategy == '':
            QMessageBox.critical(self, '오류 알림', 'GA범위의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
        else:
            if (QApplication.keyboardModifiers() & Qt.ControlModifier) or self.BackCodeTest2(strategy, ga=True):
                if proc_query.is_alive():
                    queryQ.put(('전략디비', f"DELETE FROM coinvars WHERE `index` = '{strategy_name}'"))
                    df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                    queryQ.put(('전략디비', df, 'coinvars', 'append'))
                    QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def cvoButtonClicked_01(self):
        con = sqlite3.connect(DB_STRATEGY)
        df  = pd.read_sql('SELECT * FROM coinbuyconds', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.cvo_comboBoxxx_01.clear()
            indexs = list(df.index)
            indexs.sort()
            for i, index in enumerate(indexs):
                self.cvo_comboBoxxx_01.addItem(index)
                if i == 0:
                    self.cvo_lineEdittt_01.setText(index)

    def cvoButtonClicked_02(self):
        strategy_name = self.cvo_lineEdittt_01.text()
        strategy      = self.cs_textEditttt_07.toPlainText()
        if strategy_name == '':
            QMessageBox.critical(self, '오류 알림', '매수조건의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
        elif not text_not_in_special_characters(strategy_name):
            QMessageBox.critical(self, '오류 알림', '매수조건의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
        elif strategy == '':
            QMessageBox.critical(self, '오류 알림', '매수조건의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
        else:
            if self.BackCodeTest3('매수', strategy):
                if proc_query.is_alive():
                    queryQ.put(('전략디비', f"DELETE FROM coinbuyconds WHERE `index` = '{strategy_name}'"))
                    df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                    queryQ.put(('전략디비', df, 'coinbuyconds', 'append'))
                    QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def cvoButtonClicked_03(self):
        con = sqlite3.connect(DB_STRATEGY)
        df  = pd.read_sql('SELECT * FROM coinsellconds', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.cvo_comboBoxxx_02.clear()
            indexs = list(df.index)
            indexs.sort()
            for i, index in enumerate(indexs):
                self.cvo_comboBoxxx_02.addItem(index)
                if i == 0:
                    self.cvo_lineEdittt_02.setText(index)

    def cvoButtonClicked_04(self):
        strategy_name = self.cvo_lineEdittt_02.text()
        strategy      = self.cs_textEditttt_08.toPlainText()
        if strategy_name == '':
            QMessageBox.critical(self, '오류 알림', '매도조건의 이름이 공백 상태입니다.\n이름을 입력하십시오.\n')
        elif not text_not_in_special_characters(strategy_name):
            QMessageBox.critical(self, '오류 알림', '매도조건의 이름에 특문이 포함되어 있습니다.\n언더바(_)를 제외한 특문을 제거하십시오.\n')
        elif strategy == '':
            QMessageBox.critical(self, '오류 알림', '매도조건의 코드가 공백 상태입니다.\n코드를 작성하십시오.\n')
        else:
            if self.BackCodeTest3('매도', strategy):
                if proc_query.is_alive():
                    queryQ.put(('전략디비', f"DELETE FROM coinsellconds WHERE `index` = '{strategy_name}'"))
                    df = pd.DataFrame({'전략코드': [strategy]}, index=[strategy_name])
                    queryQ.put(('전략디비', df, 'coinsellconds', 'append'))
                    QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def cvoButtonClicked_06(self):
        QMessageBox.critical(self, '오류 알림', '범위 편집기 상태에서만 작동합니다.\n')

    # =================================================================================================================

    def BackengineShow(self, gubun):
        table_list = []
        BACK_FILE = DB_STOCK_BACK if gubun == '주식' else DB_COIN_BACK
        con = sqlite3.connect(BACK_FILE)
        try:
            df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
            table_list = df['name'].to_list()
            table_list.remove('codename')
            table_list.remove('moneytop')
        except:
            pass
        con.close()
        if table_list:
            name_list = [self.dict_name[code] if code in self.dict_name.keys() else code for code in table_list]
            name_list.sort()
            self.be_comboBoxxxxx_02.clear()
            for name in name_list:
                self.be_comboBoxxxxx_02.addItem(name)
        self.be_lineEdittttt_01.setText('90000' if gubun == '주식' else '0')
        self.be_lineEdittttt_02.setText('93000' if gubun == '주식' else '235959')
        if not self.backengin_window_open:
            self.be_comboBoxxxxx_01.setCurrentText(self.dict_set['백테엔진분류방법'])
        self.dialog_backengine.show()
        self.backengin_window_open = True

    @thread_decorator
    def StartBacktestEngine(self, gubun):
        self.startday  = int(self.be_dateEdittttt_01.date().toString('yyyyMMdd'))
        self.endday    = int(self.be_dateEdittttt_02.date().toString('yyyyMMdd'))
        self.starttime = int(self.be_lineEdittttt_01.text())
        self.endtime   = int(self.be_lineEdittttt_02.text())
        self.avg_list  = [int(x) for x in self.be_lineEdittttt_03.text().split(',')]
        multi          = int(self.be_lineEdittttt_04.text())
        divid_mode     = self.be_comboBoxxxxx_01.currentText()
        one_name       = self.be_comboBoxxxxx_02.currentText()
        one_code       = self.dict_code[one_name] if one_name in self.dict_code.keys() else one_name

        wdzservQ.put(('manager', '백테엔진구동'))
        for i in range(20):
            stq = Queue()
            if i < 10:
                proc = Process(target=SubTotal, args=(totalQ, stq, self.dict_set['백테매수시간기준'], 1), daemon=True)
            else:
                proc = Process(target=SubTotal, args=(totalQ, stq, self.dict_set['백테매수시간기준'], 0), daemon=True)
            proc.start()
            self.bact_procs.append(proc)
            self.bact_pques.append(stq)
            windowQ.put((ui_num['백테엔진'], f'중간집계용 프로세스{i + 1} 생성 완료'))

        for i in range(multi):
            bpq = Queue()
            if gubun == '주식':
                if not self.dict_set['주식분봉데이터'] and not self.dict_set['주식일봉데이터']:
                    if not self.dict_set['백테주문관리적용']:
                        if i == 0 and self.dict_set['백테엔진프로파일링']:
                            proc = Process(target=StockBackEngine, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques, True), daemon=True)
                        else:
                            proc = Process(target=StockBackEngine, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques), daemon=True)
                    else:
                        if i == 0 and self.dict_set['백테엔진프로파일링']:
                            proc = Process(target=StockBackEngine2, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques, True), daemon=True)
                        else:
                            proc = Process(target=StockBackEngine2, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques), daemon=True)
                else:
                    if not self.dict_set['백테주문관리적용']:
                        if i == 0 and self.dict_set['백테엔진프로파일링']:
                            proc = Process(target=StockBackEngine3, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques, True), daemon=True)
                        else:
                            proc = Process(target=StockBackEngine3, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques), daemon=True)
                    else:
                        if i == 0 and self.dict_set['백테엔진프로파일링']:
                            proc = Process(target=StockBackEngine4, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques, True), daemon=True)
                        else:
                            proc = Process(target=StockBackEngine4, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques), daemon=True)
            else:
                if not self.dict_set['코인분봉데이터'] and not self.dict_set['코인일봉데이터']:
                    if not self.dict_set['백테주문관리적용']:
                        if i == 0 and self.dict_set['백테엔진프로파일링']:
                            proc = Process(target=CoinUpbitBackEngine if self.dict_set['거래소'] == '업비트' else CoinFutureBackEngine, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques, True), daemon=True)
                        else:
                            proc = Process(target=CoinUpbitBackEngine if self.dict_set['거래소'] == '업비트' else CoinFutureBackEngine, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques), daemon=True)
                    else:
                        if i == 0 and self.dict_set['백테엔진프로파일링']:
                            proc = Process(target=CoinUpbitBackEngine2 if self.dict_set['거래소'] == '업비트' else CoinFutureBackEngine2, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques, True), daemon=True)
                        else:
                            proc = Process(target=CoinUpbitBackEngine2 if self.dict_set['거래소'] == '업비트' else CoinFutureBackEngine2, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques), daemon=True)
                else:
                    if not self.dict_set['백테주문관리적용']:
                        if i == 0 and self.dict_set['백테엔진프로파일링']:
                            proc = Process(target=CoinUpbitBackEngine3 if self.dict_set['거래소'] == '업비트' else CoinFutureBackEngine3, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques, True), daemon=True)
                        else:
                            proc = Process(target=CoinUpbitBackEngine3 if self.dict_set['거래소'] == '업비트' else CoinFutureBackEngine3, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques), daemon=True)
                    else:
                        if i == 0 and self.dict_set['백테엔진프로파일링']:
                            proc = Process(target=CoinUpbitBackEngine4 if self.dict_set['거래소'] == '업비트' else CoinFutureBackEngine4, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques, True), daemon=True)
                        else:
                            proc = Process(target=CoinUpbitBackEngine4 if self.dict_set['거래소'] == '업비트' else CoinFutureBackEngine4, args=(i, windowQ, bpq, totalQ, backQ, self.bact_pques), daemon=True)

            proc.start()
            self.back_procs.append(proc)
            self.back_pques.append(bpq)
            windowQ.put((ui_num['백테엔진'], f'연산용 프로세스{i + 1} 생성 완료'))

        if gubun == '주식':
            webcQ.put(('지수차트', self.startday))
            self.df_kp, self.df_kd = backQ.get()

        if not self.dict_set['백테일괄로딩']:
            file_list = os.listdir(BACK_TEMP)
            for file in file_list:
                os.remove(f'{BACK_TEMP}/{file}')
            windowQ.put((ui_num['백테엔진'], '이전 임시파일 삭제 완료'))

        dict_kd = None
        try:
            con = sqlite3.connect(DB_STOCK_BACK) if gubun == '주식' else sqlite3.connect(DB_COIN_BACK)
            if gubun == '주식':
                df_cn = pd.read_sql('SELECT * FROM codename', con).set_index('index')
                self.dict_cn = df_cn['종목명'].to_dict()
                dict_kd = df_cn['코스닥'].to_dict()
            elif self.dict_set['거래소'] == '바이낸스선물':
                binan = binance.Client()
                datas = binan.futures_exchange_info()
                datas = [x for x in datas['symbols'] if re.search('USDT$', x['symbol']) is not None]
                dict_kd = {x['symbol']: float(x['filters'][0]['tickSize']) for x in datas}
            gubun_ = 'S' if gubun == '주식' else 'CF' if gubun == '코인' and self.dict_set['거래소'] == '바이낸스선물' else 'C'
            query = GetMoneytopQuery(gubun_, self.startday, self.endday, self.starttime, self.endtime)
            df_mt = pd.read_sql(query, con)
            con.close()
            df_mt['일자'] = df_mt['index'].apply(lambda x: int(str(x)[:8]))
            df_mt.set_index('index', inplace=True)
        except:
            if gubun == '주식':
                if self.dict_cn is None:
                    windowQ.put((ui_num['백테엔진'], '백테디비에 데이터가 존재하지 않습니다. 디비관리창(Alt + D)에서 백테디비를 생성하십시오.'))
                elif len(self.dict_cn) < 100:
                    windowQ.put((ui_num['백테엔진'], '종목명 테이블이 갱신되지 않았습니다. 수동로그인(Alt + S)을 1회 실행하시오.'))
                elif dict_kd is None:
                    windowQ.put((ui_num['백테엔진'], '종목명 테이블에 코스닥 구분 칼럼이 존재하지 않습니다. 수동로그인(Alt + S)을 1회 실행하시오.'))
                else:
                    windowQ.put((ui_num['백테엔진'], '백테디비에 데이터가 존재하지 않습니다. 디비관리창(Alt + D)에서 백테디비를 생성하십시오.'))
            else:
                windowQ.put((ui_num['백테엔진'], '백테디비에 데이터가 존재하지 않습니다. 디비관리창(Alt + D)에서 백테디비를 생성하십시오.'))
            return

        if df_mt is None or df_mt.empty:
            windowQ.put((ui_num['백테엔진'], '시작 또는 종료일자가 잘못 선택되었거나 해당 일자에 데이터가 존재하지 않습니다.'))
            return

        self.dict_mt = df_mt['거래대금순위'].to_dict()
        day_list = list(set(df_mt['일자'].to_list()))
        table_list = list(set(';'.join(list(self.dict_mt.values())).split(';')))

        day_codes = {}
        for day in day_list:
            df_mt_ = df_mt[df_mt['일자'] == day]
            day_codes[day] = list(set(';'.join(df_mt_['거래대금순위'].to_list()).split(';')))

        code_days = {}
        for code in table_list:
            code_days[code] = [day for day, codes in day_codes.items() if code in codes]

        if divid_mode == '종목코드별 분류' and len(code_days) < multi:
            windowQ.put((ui_num['백테엔진'], '선택한 일자의 종목의 개수가 멀티수보다 작습니다. 일자를 늘리십시오.'))
            return

        if divid_mode == '일자별 분류' and len(day_codes) < multi:
            windowQ.put((ui_num['백테엔진'], '선택한 일자의 수가 멀티수보다 작습니다. 일자를 늘리십시오.'))
            return

        if divid_mode == '한종목 로딩' and one_code not in code_days.keys():
            windowQ.put((ui_num['백테엔진'], f'{one_name} 종목은 선택한 일자에 데이터가 존재하지 않습니다.'))
            return

        if divid_mode == '한종목 로딩' and len(code_days[one_code]) < multi:
            windowQ.put((ui_num['백테엔진'], f'{one_name} 선택한 종목의 일자의 수가 멀티수보다 작습니다. 일자를 늘리십시오.'))
            return

        for i in range(multi):
            if gubun == '주식':
                self.back_pques[i].put(('종목명거래대금순위', self.dict_cn, self.dict_mt, dict_kd))
            else:
                self.back_pques[i].put(('종목명거래대금순위', self.dict_mt, dict_kd))
        windowQ.put((ui_num['백테엔진'], '거래대금순위 및 종목코드 추출 완료'))

        if divid_mode == '종목코드별 분류':
            windowQ.put((ui_num['백테엔진'], '종목별 데이터 크기 추출 시작'))
            code_lists = []
            for i in range(multi):
                code_lists.append([code for j, code in enumerate(table_list) if j % multi == i])
            for i, codes in enumerate(code_lists):
                self.back_pques[i].put(('데이터크기', self.startday, self.endday, self.starttime, self.endtime, codes, self.avg_list, code_days, day_codes, divid_mode, one_code))

            dict_lendf = {}
            last = len(table_list)
            for i in range(last):
                data = backQ.get()
                if data[1] != 0:
                    dict_lendf[data[0]] = data[1]
                if (i + 1) % 100 == 0:
                    windowQ.put((ui_num['백테엔진'], f'종목별 데이터 크기 추출 중 ... [{i + 1}/{last}]'))
            windowQ.put((ui_num['백테엔진'], '종목별 데이터 크기 추출 완료'))

            code_lists  = [[] for _ in range(multi)]
            total_list  = [0 for _ in range(multi)]
            add_count   = 0
            multi_num   = 0
            reverse     = False
            divid_lendf = int(sum(dict_lendf.values()) / multi)
            sort_lendf  = sorted(dict_lendf.items(), key=operator.itemgetter(1), reverse=True)
            for code, lendf in sort_lendf:
                code_lists[multi_num].append(code)
                total_list[multi_num] += lendf
                while True:
                    add_count += 1
                    if add_count % multi == 0:
                        if reverse:
                            reverse   = False
                            multi_num = 0
                        else:
                            reverse   = True
                            multi_num = multi - 1
                    else:
                        if reverse:
                            multi_num -= 1
                        else:
                            multi_num += 1
                    if total_list[multi_num] < divid_lendf:
                        break

            windowQ.put((ui_num['백테엔진'], '종목코드별 분류 완료'))
            for i, codes in enumerate(code_lists):
                self.back_pques[i].put(('데이터로딩', self.startday, self.endday, self.starttime, self.endtime, codes, self.avg_list, code_days, day_codes, divid_mode, one_code))

        elif divid_mode == '일자별 분류':
            windowQ.put((ui_num['백테엔진'], '일자별 데이터 크기 추출 시작'))
            day_lists = []
            for i in range(multi):
                day_lists.append([day for j, day in enumerate(day_list) if j % multi == i])
            for i, days in enumerate(day_lists):
                self.back_pques[i].put(('데이터크기', self.startday, self.endday, self.starttime, self.endtime, days, self.avg_list, code_days, day_codes, divid_mode, one_code))

            dict_lendf = {}
            last = len(day_list)
            for i in range(last):
                data = backQ.get()
                if data[1] != 0:
                    dict_lendf[data[0]] = data[1]
                if (i + 1) % 10 == 0:
                    windowQ.put((ui_num['백테엔진'], f'일자별 데이터 크기 추출 중 ... [{i + 1}/{last}]'))
            windowQ.put((ui_num['백테엔진'], '일자별 데이터 크기 추출 완료'))

            day_lists  = []
            total_list = []
            for _ in range(multi):
                day_lists.append([])
                total_list.append(0)

            add_count   = 0
            multi_num   = 0
            reverse     = False
            divid_lendf = int(sum(dict_lendf.values()) / multi)
            sort_lendf  = sorted(dict_lendf.items(), key=operator.itemgetter(1), reverse=True)
            for day, lendf in sort_lendf:
                day_lists[multi_num].append(day)
                total_list[multi_num] += lendf
                while True:
                    add_count += 1
                    if add_count % multi == 0:
                        if reverse:
                            reverse   = False
                            multi_num = 0
                        else:
                            reverse   = True
                            multi_num = multi - 1
                    else:
                        if reverse:
                            multi_num -= 1
                        else:
                            multi_num += 1
                    if total_list[multi_num] < divid_lendf:
                        break

            windowQ.put((ui_num['백테엔진'], '일자별 분류 완료'))
            for i, days in enumerate(day_lists):
                self.back_pques[i].put(('데이터로딩', self.startday, self.endday, self.starttime, self.endtime, days, self.avg_list, code_days, day_codes, divid_mode, one_code))
        else:
            windowQ.put((ui_num['백테엔진'], f'{one_code} 일자별 데이터 크기 추출 시작'))
            day_list = code_days[one_code]
            day_lists = []
            for i in range(multi):
                day_lists.append([day for j, day in enumerate(day_list) if j % multi == i])
            for i, days in enumerate(day_lists):
                self.back_pques[i].put(('데이터크기', self.startday, self.endday, self.starttime, self.endtime, days, self.avg_list, code_days, day_codes, divid_mode, one_code))

            dict_lendf = {}
            last = len(day_list)
            for i in range(last):
                data = backQ.get()
                if data[1] != 0:
                    dict_lendf[data[0]] = data[1]
                if (i + 1) % 10 == 0:
                    windowQ.put((ui_num['백테엔진'], f'{one_code} 일자별 데이터 크기 추출 중 ... [{i + 1}/{last}]'))
            windowQ.put((ui_num['백테엔진'], f'{one_code} 일자별 데이터 크기 추출 완료'))

            day_lists  = []
            total_list = []
            for _ in range(multi):
                day_lists.append([])
                total_list.append(0)

            add_count   = 0
            multi_num   = 0
            reverse     = False
            divid_lendf = int(sum(dict_lendf.values()) / multi)
            sort_lendf  = sorted(dict_lendf.items(), key=operator.itemgetter(1), reverse=True)
            for day, lendf in sort_lendf:
                day_lists[multi_num].append(day)
                total_list[multi_num] += lendf
                while True:
                    add_count += 1
                    if add_count % multi == 0:
                        if reverse:
                            reverse   = False
                            multi_num = 0
                        else:
                            reverse   = True
                            multi_num = multi - 1
                    else:
                        if reverse:
                            multi_num -= 1
                        else:
                            multi_num += 1
                    if total_list[multi_num] < divid_lendf:
                        break

            windowQ.put((ui_num['백테엔진'], f'{one_code} 일자별 분류 완료'))
            for i, days in enumerate(day_lists):
                self.back_pques[i].put(('데이터로딩', self.startday, self.endday, self.starttime, self.endtime, days, self.avg_list, code_days, day_codes, divid_mode, one_code))

        for _ in range(multi):
            data = backQ.get()
            self.back_count += data
            windowQ.put((ui_num['백테엔진'], f'백테엔진 데이터 로딩 중 ... [{data}]'))
        windowQ.put((ui_num['백테엔진'], '백테엔진 준비 완료'))
        self.backtest_engine = True

    def BackCodeTest1(self, stg_code):
        print('전략 코드 오류 테스트 시작')
        Process(target=BackCodeTest, args=(testQ, stg_code), daemon=True).start()
        return self.BackCodeTestWait('전략')

    def BackCodeTest2(self, vars_code, ga=False):
        print('범위 코드 오류 테스트 시작')
        Process(target=BackCodeTest, args=(testQ, '', vars_code, ga), daemon=True).start()
        return self.BackCodeTestWait('범위')

    def BackCodeTest3(self, gubun, conds_code):
        print('조건 코드 오류 테스트 시작')
        conds_code = conds_code.split('\n')
        conds_code = [x for x in conds_code if x != '' and '#' not in x]
        if gubun == '매수':
            conds_code = 'if ' + ':\n    매수 = False\nelif '.join(conds_code) + ':\n    매수 = False'
        else:
            conds_code = 'if ' + ':\n    매도 = True\nelif '.join(conds_code) + ':\n    매도 = True'
        Process(target=BackCodeTest, args=(testQ, conds_code), daemon=True).start()
        return self.BackCodeTestWait('조건')

    @staticmethod
    def BackCodeTestWait(gubun):
        test_ok   = False
        test_time = timedelta_sec(3)

        while now() < test_time:
            if not testQ.empty():
                testQ.get()
                print(f'{gubun} 코드 오류 테스트 완료')
                test_ok = True
                break
            qtest_qwait(0.1)

        if not test_ok:
            print(f'{gubun}에 오류가 있어 저장하지 못하였습니다.')

        return test_ok

    @staticmethod
    def ClearBacktestQ():
        if not backQ.empty():
            while not backQ.empty():
                backQ.get()
        if not totalQ.empty():
            while not totalQ.empty():
                totalQ.get()

    def BacktestProcessKill(self):
        self.back_condition = False
        totalQ.put('백테중지')
        qtest_qwait(3)
        if self.proc_backtester_bb is not None and   self.proc_backtester_bb.is_alive():   self.proc_backtester_bb.kill()
        if self.proc_backtester_bf is not None and   self.proc_backtester_bf.is_alive():   self.proc_backtester_bf.kill()
        if self.proc_backtester_o is not None and    self.proc_backtester_o.is_alive():    self.proc_backtester_o.kill()
        if self.proc_backtester_ov is not None and   self.proc_backtester_ov.is_alive():   self.proc_backtester_ov.kill()
        if self.proc_backtester_ovc is not None and  self.proc_backtester_ovc.is_alive():  self.proc_backtester_ovc.kill()
        if self.proc_backtester_ot is not None and   self.proc_backtester_ot.is_alive():   self.proc_backtester_ot.kill()
        if self.proc_backtester_ovt is not None and  self.proc_backtester_ovt.is_alive():  self.proc_backtester_ovt.kill()
        if self.proc_backtester_ovct is not None and self.proc_backtester_ovct.is_alive(): self.proc_backtester_ovct.kill()
        if self.proc_backtester_or is not None and   self.proc_backtester_or.is_alive():   self.proc_backtester_or.kill()
        if self.proc_backtester_orv is not None and  self.proc_backtester_orv.is_alive():  self.proc_backtester_orv.kill()
        if self.proc_backtester_orvc is not None and self.proc_backtester_orvc.is_alive(): self.proc_backtester_orvc.kill()
        if self.proc_backtester_b is not None and    self.proc_backtester_b.is_alive():    self.proc_backtester_b.kill()
        if self.proc_backtester_bv is not None and   self.proc_backtester_bv.is_alive():   self.proc_backtester_bv.kill()
        if self.proc_backtester_bvc is not None and  self.proc_backtester_bvc.is_alive():  self.proc_backtester_bvc.kill()
        if self.proc_backtester_bt is not None and   self.proc_backtester_bt.is_alive():   self.proc_backtester_bt.kill()
        if self.proc_backtester_bvt is not None and  self.proc_backtester_bvt.is_alive():  self.proc_backtester_bvt.kill()
        if self.proc_backtester_bvct is not None and self.proc_backtester_bvct.is_alive(): self.proc_backtester_bvct.kill()
        if self.proc_backtester_br is not None and   self.proc_backtester_br.is_alive():   self.proc_backtester_br.kill()
        if self.proc_backtester_brv is not None and  self.proc_backtester_brv.is_alive():  self.proc_backtester_brv.kill()
        if self.proc_backtester_brvc is not None and self.proc_backtester_brvc.is_alive(): self.proc_backtester_brvc.kill()
        if self.proc_backtester_oc is not None and   self.proc_backtester_oc.is_alive():   self.proc_backtester_oc.kill()
        if self.proc_backtester_ocv is not None and  self.proc_backtester_ocv.is_alive():  self.proc_backtester_ocv.kill()
        if self.proc_backtester_ocvc is not None and self.proc_backtester_ocvc.is_alive(): self.proc_backtester_ocvc.kill()
        if self.proc_backtester_og is not None and   self.proc_backtester_og.is_alive():   self.proc_backtester_og.kill()
        if self.proc_backtester_ogv is not None and  self.proc_backtester_ogv.is_alive():  self.proc_backtester_ogv.kill()
        if self.proc_backtester_ogvc is not None and self.proc_backtester_ogvc.is_alive(): self.proc_backtester_ogvc.kill()
        if self.main_btn == 2:   self.ss_pushButtonn_08.setStyleSheet(style_bc_dk)
        elif self.main_btn == 3: self.cs_pushButtonn_08.setStyleSheet(style_bc_dk)
        self.back_condition = True

    # =================================================================================================================

    def lvButtonClicked_01(self):
        self.dialog_leverage.show() if not self.dialog_leverage.isVisible() else self.dialog_leverage.close()

    def lvButtonClicked_02(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM main', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.lv_checkBoxxxx_01.setChecked(True) if df['바이낸스선물고정레버리지'][0] else self.lv_checkBoxxxx_01.setChecked(False)
            self.lv_checkBoxxxx_02.setChecked(True) if not df['바이낸스선물고정레버리지'][0] else self.lv_checkBoxxxx_02.setChecked(False)
            self.lv_lineEditttt_01.setText(str(df['바이낸스선물고정레버리지값'][0]))
            binance_lvrg = []
            for text in df['바이낸스선물변동레버리지값'][0].split('^'):
                lvrg_list = text.split(';')
                binance_lvrg.append(lvrg_list)
            self.lv_lineEditttt_02.setText(binance_lvrg[0][0])
            self.lv_lineEditttt_03.setText(binance_lvrg[0][1])
            self.lv_lineEditttt_04.setText(binance_lvrg[0][2])
            self.lv_lineEditttt_05.setText(binance_lvrg[1][0])
            self.lv_lineEditttt_06.setText(binance_lvrg[1][1])
            self.lv_lineEditttt_07.setText(binance_lvrg[1][2])
            self.lv_lineEditttt_08.setText(binance_lvrg[2][0])
            self.lv_lineEditttt_09.setText(binance_lvrg[2][1])
            self.lv_lineEditttt_10.setText(binance_lvrg[2][2])
            self.lv_lineEditttt_11.setText(binance_lvrg[3][0])
            self.lv_lineEditttt_12.setText(binance_lvrg[3][1])
            self.lv_lineEditttt_13.setText(binance_lvrg[3][2])
            self.lv_lineEditttt_14.setText(binance_lvrg[4][0])
            self.lv_lineEditttt_15.setText(binance_lvrg[4][1])
            self.lv_lineEditttt_16.setText(binance_lvrg[4][2])
        else:
            QMessageBox.critical(self.dialog_leverage, '오류 알림', '기본 설정값이\n존재하지 않습니다.\n')

    def lvButtonClicked_03(self):
        lv0  = 1 if self.lv_checkBoxxxx_01.isChecked() else 0
        lv1  = self.lv_lineEditttt_01.text()
        lv2  = self.lv_lineEditttt_02.text()
        lv3  = self.lv_lineEditttt_03.text()
        lv4  = self.lv_lineEditttt_04.text()
        lv5  = self.lv_lineEditttt_05.text()
        lv6  = self.lv_lineEditttt_06.text()
        lv7  = self.lv_lineEditttt_07.text()
        lv8  = self.lv_lineEditttt_08.text()
        lv9  = self.lv_lineEditttt_09.text()
        lv10 = self.lv_lineEditttt_10.text()
        lv11 = self.lv_lineEditttt_11.text()
        lv12 = self.lv_lineEditttt_12.text()
        lv13 = self.lv_lineEditttt_13.text()
        lv14 = self.lv_lineEditttt_14.text()
        lv15 = self.lv_lineEditttt_15.text()
        lv16 = self.lv_lineEditttt_16.text()
        if '' in (lv1, lv2, lv3, lv4, lv5, lv6, lv7, lv8, lv9, lv10, lv11, lv12, lv13, lv14, lv15, lv16):
            QMessageBox.critical(self.dialog_leverage, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        else:
            lv2, lv3, lv5, lv6, lv8, lv9, lv11, lv12, lv14, lv15 = float(lv2), float(lv3), float(lv5), float(lv6), float(lv8), float(lv9), float(lv11), float(lv12), float(lv14), float(lv15)
            lv1, lv4, lv7, lv10, lv13, lv16 = int(lv1), int(lv4), int(lv7), int(lv10), int(lv13), int(lv16)
            if not (1 <= lv1 <= 125 and 1 <= lv4 <= 125 and 1 <= lv7 <= 125 and 1 <= lv10 <= 125 and 1 <= lv13 <= 125 and 1 <= lv16 <= 125):
                QMessageBox.critical(self, '오류 알림', '레버리지 설정을 1부터 125사이로 입력하십시오.\n')
                return
            else:
                if proc_query.is_alive():
                    lvrg_text = f'{lv2};{lv3};{lv4}^{lv5};{lv6};{lv7}^{lv8};{lv9};{lv10}^{lv11};{lv12};{lv13}^{lv14};{lv15};{lv16}'
                    query = f"UPDATE main SET 바이낸스선물고정레버리지 = {lv0}, 바이낸스선물고정레버리지값 = {lv1}, 바이낸스선물변동레버리지값 = '{lvrg_text}'"
                    queryQ.put(('설정디비', query))
                self.dict_set['바이낸스선물고정레버리지']  = lv0
                self.dict_set['바이낸스선물고정레버리지값'] = lv1
                self.dict_set['바이낸스선물변동레버리지값'] = [[lv2, lv3, lv4], [lv5, lv6, lv7], [lv8, lv9, lv10], [lv11, lv12, lv13], [lv14, lv15, lv16]]
                self.UpdateDictSet()
                QMessageBox.information(self.dialog_leverage, '저장 완료', random.choice(famous_saying))

    def lvCheckChanged_01(self, state):
        if type(self.dialog_leverage.focusWidget()) != QPushButton and state == Qt.Checked:
            for widget in self.lv_checkbox_listt:
                if widget != self.dialog_leverage.focusWidget():
                    if widget.isChecked():
                        widget.nextCheckState()

    def sjButtonClicked_01(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM main', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_main_comBox_01.setCurrentText(df['증권사'][0])
            self.sj_main_cheBox_01.setChecked(True) if df['주식리시버'][0] else self.sj_main_cheBox_01.setChecked(False)
            self.sj_main_cheBox_02.setChecked(True) if df['주식트레이더'][0] else self.sj_main_cheBox_02.setChecked(False)
            self.sj_main_cheBox_03.setChecked(True) if df['주식틱데이터저장'][0] else self.sj_main_cheBox_03.setChecked(False)
            self.sj_main_comBox_02.setCurrentText(df['거래소'][0])
            self.sj_main_cheBox_04.setChecked(True) if df['코인리시버'][0] else self.sj_main_cheBox_04.setChecked(False)
            self.sj_main_cheBox_05.setChecked(True) if df['코인트레이더'][0] else self.sj_main_cheBox_05.setChecked(False)
            self.sj_main_cheBox_06.setChecked(True) if df['코인틱데이터저장'][0] else self.sj_main_cheBox_06.setChecked(False)
            self.sj_main_cheBox_07.setChecked(True) if df['장중전략조건검색식사용'][0] else self.sj_main_cheBox_07.setChecked(False)
            self.sj_main_cheBox_08.setChecked(True) if not df['장중전략조건검색식사용'][0] else self.sj_main_cheBox_08.setChecked(False)
            self.sj_main_liEdit_01.setText(str(df['주식순위시간'][0]))
            self.sj_main_liEdit_02.setText(str(df['주식순위선정'][0]))
            self.sj_main_liEdit_03.setText(str(df['코인순위시간'][0]))
            self.sj_main_liEdit_04.setText(str(df['코인순위선정'][0]))
            self.sj_main_liEdit_05.setText(str(df['리시버실행시간'][0]))
            self.sj_main_liEdit_06.setText(str(df['트레이더실행시간'][0]))
            self.sj_main_comBox_03.setCurrentText('격리' if df['바이낸스선물마진타입'][0] == 'ISOLATED' else '교차')
            self.sj_main_comBox_04.setCurrentText('단방향' if df['바이낸스선물포지션'][0] == 'false' else '양방향')
            self.sj_main_cheBox_08.setChecked(True) if not df['장중전략조건검색식사용'][0] else self.sj_main_cheBox_08.setChecked(False)
            self.sj_main_cheBox_09.setChecked(True) if df['버전업'][0] else self.sj_main_cheBox_09.setChecked(False)
            if df['리시버공유'][0] == 0:
                self.sj_main_cheBox_10.setChecked(False)
                self.sj_main_cheBox_11.setChecked(False)
            elif df['리시버공유'][0] == 1:
                self.sj_main_cheBox_10.setChecked(True)
                self.sj_main_cheBox_11.setChecked(False)
            elif df['리시버공유'][0] == 2:
                self.sj_main_cheBox_10.setChecked(False)
                self.sj_main_cheBox_11.setChecked(True)
        else:
            QMessageBox.critical(self, '오류 알림', '기본 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_02(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM sacc', con).set_index('index')
        con.close()
        comob_name = self.sj_main_comBox_01.currentText()
        if len(df) > 0:
            if comob_name == '키움증권1' and df['아이디1'][0] != '' and df['아이디2'][0] != '':
                self.sj_sacc_liEdit_01.setText(de_text(self.dict_set['키'], df['아이디1'][0]))
                self.sj_sacc_liEdit_02.setText(de_text(self.dict_set['키'], df['비밀번호1'][0]))
                self.sj_sacc_liEdit_03.setText(de_text(self.dict_set['키'], df['인증서비밀번호1'][0]))
                self.sj_sacc_liEdit_04.setText(de_text(self.dict_set['키'], df['계좌비밀번호1'][0]))
                self.sj_sacc_liEdit_05.setText(de_text(self.dict_set['키'], df['아이디2'][0]))
                self.sj_sacc_liEdit_06.setText(de_text(self.dict_set['키'], df['비밀번호2'][0]))
                self.sj_sacc_liEdit_07.setText(de_text(self.dict_set['키'], df['인증서비밀번호2'][0]))
                self.sj_sacc_liEdit_08.setText(de_text(self.dict_set['키'], df['계좌비밀번호2'][0]))
            elif comob_name == '키움증권2' and df['아이디3'][0] != '' and df['아이디4'][0] != '':
                self.sj_sacc_liEdit_01.setText(de_text(self.dict_set['키'], df['아이디3'][0]))
                self.sj_sacc_liEdit_02.setText(de_text(self.dict_set['키'], df['비밀번호3'][0]))
                self.sj_sacc_liEdit_03.setText(de_text(self.dict_set['키'], df['인증서비밀번호3'][0]))
                self.sj_sacc_liEdit_04.setText(de_text(self.dict_set['키'], df['계좌비밀번호3'][0]))
                self.sj_sacc_liEdit_05.setText(de_text(self.dict_set['키'], df['아이디4'][0]))
                self.sj_sacc_liEdit_06.setText(de_text(self.dict_set['키'], df['비밀번호4'][0]))
                self.sj_sacc_liEdit_07.setText(de_text(self.dict_set['키'], df['인증서비밀번호4'][0]))
                self.sj_sacc_liEdit_08.setText(de_text(self.dict_set['키'], df['계좌비밀번호4'][0]))
        else:
            QMessageBox.critical(self, '오류 알림', '주식 계정 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_03(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM cacc', con).set_index('index')
        con.close()
        combo_name = self.sj_main_comBox_02.currentText()
        if len(df) > 0:
            if combo_name == '업비트' and df['Access_key1'][0] != '' and df['Secret_key1'][0] != '':
                self.sj_cacc_liEdit_01.setText(de_text(self.dict_set['키'], df['Access_key1'][0]))
                self.sj_cacc_liEdit_02.setText(de_text(self.dict_set['키'], df['Secret_key1'][0]))
            elif combo_name == '바이낸스선물' and df['Access_key2'][0] != '' and df['Secret_key2'][0] != '':
                self.sj_cacc_liEdit_01.setText(de_text(self.dict_set['키'], df['Access_key2'][0]))
                self.sj_cacc_liEdit_02.setText(de_text(self.dict_set['키'], df['Secret_key2'][0]))
        else:
            QMessageBox.critical(self, '오류 알림', '계정 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_04(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM telegram', con).set_index('index')
        con.close()
        if len(df) > 0 and df['str_bot'][0] != '':
            self.sj_tele_liEdit_01.setText(de_text(self.dict_set['키'], df['str_bot'][0]))
            self.sj_tele_liEdit_02.setText(de_text(self.dict_set['키'], df['int_id'][0]))
        else:
            QMessageBox.critical(self, '오류 알림', '텔레그램 봇토큰 및 사용자 아이디\n설정값이 존재하지 않습니다.\n')

    def sjButtonClicked_05(self):
        con  = sqlite3.connect(DB_SETTING)
        df   = pd.read_sql('SELECT * FROM stock', con).set_index('index')
        con.close()
        con  = sqlite3.connect(DB_STRATEGY)
        dfb  = pd.read_sql('SELECT * FROM stockbuy', con).set_index('index')
        dfs  = pd.read_sql('SELECT * FROM stocksell', con).set_index('index')
        dfob = pd.read_sql('SELECT * FROM stockoptibuy', con).set_index('index')
        dfos = pd.read_sql('SELECT * FROM stockoptisell', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_stock_ckBox_01.setChecked(True) if df['주식모의투자'][0] else self.sj_stock_ckBox_01.setChecked(False)
            self.sj_stock_ckBox_02.setChecked(True) if df['주식알림소리'][0] else self.sj_stock_ckBox_02.setChecked(False)
            self.sj_stock_ckBox_03.setChecked(True) if df['주식장초잔고청산'][0] else self.sj_stock_ckBox_03.setChecked(False)
            self.sj_stock_ckBox_04.setChecked(True) if df['주식장초프로세스종료'][0] else self.sj_stock_ckBox_04.setChecked(False)
            self.sj_stock_ckBox_05.setChecked(True) if df['주식장초컴퓨터종료'][0] else self.sj_stock_ckBox_05.setChecked(False)
            self.sj_stock_ckBox_06.setChecked(True) if df['주식장중잔고청산'][0] else self.sj_stock_ckBox_06.setChecked(False)
            self.sj_stock_ckBox_07.setChecked(True) if df['주식장중프로세스종료'][0] else self.sj_stock_ckBox_07.setChecked(False)
            self.sj_stock_ckBox_08.setChecked(True) if df['주식장중컴퓨터종료'][0] else self.sj_stock_ckBox_08.setChecked(False)
            self.sj_stock_ckBox_09.setChecked(True) if df['주식투자금고정'][0] else self.sj_stock_ckBox_09.setChecked(False)
            self.sj_stock_ckBox_10.setChecked(True) if df['주식손실중지'][0] else self.sj_stock_ckBox_10.setChecked(False)
            self.sj_stock_ckBox_11.setChecked(True) if df['주식수익중지'][0] else self.sj_stock_ckBox_11.setChecked(False)
            self.sj_stock_lEdit_01.setText(str(df['주식장초평균값계산틱수'][0]))
            self.sj_stock_lEdit_02.setText(str(df['주식장초최대매수종목수'][0]))
            self.sj_stock_lEdit_03.setText(str(df['주식장초전략종료시간'][0]))
            self.sj_stock_lEdit_04.setText(str(df['주식장중평균값계산틱수'][0]))
            self.sj_stock_lEdit_05.setText(str(df['주식장중최대매수종목수'][0]))
            self.sj_stock_lEdit_06.setText(str(df['주식장중전략종료시간'][0]))
            self.sj_stock_cbBox_01.clear()
            self.sj_stock_cbBox_02.clear()
            self.sj_stock_cbBox_03.clear()
            self.sj_stock_cbBox_04.clear()
            self.sj_stock_cbBox_01.addItem('사용안함')
            self.sj_stock_cbBox_02.addItem('사용안함')
            self.sj_stock_cbBox_03.addItem('사용안함')
            self.sj_stock_cbBox_04.addItem('사용안함')
            if len(dfb) > 0:
                stg_list = list(dfb.index)
                stg_list.sort()
                for stg in stg_list:
                    self.sj_stock_cbBox_01.addItem(stg)
                    self.sj_stock_cbBox_03.addItem(stg)
            if len(dfob) > 0:
                stg_list = list(dfob.index)
                stg_list.sort()
                for stg in stg_list:
                    self.sj_stock_cbBox_01.addItem(stg)
                    self.sj_stock_cbBox_03.addItem(stg)
            if df['주식장초매수전략'][0] != '':
                self.sj_stock_cbBox_01.setCurrentText(df['주식장초매수전략'][0])
            if df['주식장중매수전략'][0] != '':
                self.sj_stock_cbBox_03.setCurrentText(df['주식장중매수전략'][0])
            if len(dfs) > 0:
                stg_list = list(dfs.index)
                stg_list.sort()
                for stg in stg_list:
                    self.sj_stock_cbBox_02.addItem(stg)
                    self.sj_stock_cbBox_04.addItem(stg)
            if len(dfos) > 0:
                stg_list = list(dfos.index)
                stg_list.sort()
                for stg in stg_list:
                    self.sj_stock_cbBox_02.addItem(stg)
                    self.sj_stock_cbBox_04.addItem(stg)
            if df['주식장초매도전략'][0] != '':
                self.sj_stock_cbBox_02.setCurrentText(df['주식장초매도전략'][0])
            if df['주식장중매도전략'][0] != '':
                self.sj_stock_cbBox_04.setCurrentText(df['주식장중매도전략'][0])
            self.sj_stock_lEdit_07.setText(str(df['주식장초투자금'][0]))
            self.sj_stock_lEdit_08.setText(str(df['주식장중투자금'][0]))
            self.sj_stock_lEdit_09.setText(str(df['주식손실중지수익률'][0]))
            self.sj_stock_lEdit_10.setText(str(df['주식수익중지수익률'][0]))
            if 152000 <= df['주식장중전략종료시간'][0] <= 152759:
                QMessageBox.critical(self, '오류 알림', '주식 장중전략의 종료시간을\n152000 ~ 152759 구간으로 설정할 수 없습니다.\n')
                return
        else:
            QMessageBox.critical(self, '오류 알림', '주식 전략 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_06(self):
        con  = sqlite3.connect(DB_SETTING)
        df   = pd.read_sql('SELECT * FROM coin', con).set_index('index')
        con.close()
        con  = sqlite3.connect(DB_STRATEGY)
        dfb  = pd.read_sql('SELECT * FROM coinbuy', con).set_index('index')
        dfs  = pd.read_sql('SELECT * FROM coinsell', con).set_index('index')
        dfob = pd.read_sql('SELECT * FROM coinoptibuy', con).set_index('index')
        dfos = pd.read_sql('SELECT * FROM coinoptisell', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_coin_cheBox_01.setChecked(True) if df['코인모의투자'][0] else self.sj_coin_cheBox_01.setChecked(False)
            self.sj_coin_cheBox_02.setChecked(True) if df['코인알림소리'][0] else self.sj_coin_cheBox_02.setChecked(False)
            self.sj_coin_cheBox_03.setChecked(True) if df['코인장초잔고청산'][0] else self.sj_coin_cheBox_03.setChecked(False)
            self.sj_coin_cheBox_04.setChecked(True) if df['코인장초프로세스종료'][0] else self.sj_coin_cheBox_04.setChecked(False)
            self.sj_coin_cheBox_05.setChecked(True) if df['코인장초컴퓨터종료'][0] else self.sj_coin_cheBox_05.setChecked(False)
            self.sj_coin_cheBox_06.setChecked(True) if df['코인장중잔고청산'][0] else self.sj_coin_cheBox_06.setChecked(False)
            self.sj_coin_cheBox_07.setChecked(True) if df['코인장중프로세스종료'][0] else self.sj_coin_cheBox_07.setChecked(False)
            self.sj_coin_cheBox_08.setChecked(True) if df['코인장중컴퓨터종료'][0] else self.sj_coin_cheBox_08.setChecked(False)
            self.sj_coin_cheBox_09.setChecked(True) if df['코인투자금고정'][0] else self.sj_coin_cheBox_09.setChecked(False)
            self.sj_coin_cheBox_10.setChecked(True) if df['코인손실중지'][0] else self.sj_coin_cheBox_10.setChecked(False)
            self.sj_coin_cheBox_11.setChecked(True) if df['코인수익중지'][0] else self.sj_coin_cheBox_11.setChecked(False)
            self.sj_coin_liEdit_01.setText(str(df['코인장초평균값계산틱수'][0]))
            self.sj_coin_liEdit_02.setText(str(df['코인장초최대매수종목수'][0]))
            self.sj_coin_liEdit_03.setText(str(df['코인장초전략종료시간'][0]))
            self.sj_coin_liEdit_04.setText(str(df['코인장중평균값계산틱수'][0]))
            self.sj_coin_liEdit_05.setText(str(df['코인장중최대매수종목수'][0]))
            self.sj_coin_liEdit_06.setText(str(df['코인장중전략종료시간'][0]))
            self.sj_coin_comBox_01.clear()
            self.sj_coin_comBox_02.clear()
            self.sj_coin_comBox_03.clear()
            self.sj_coin_comBox_04.clear()
            self.sj_coin_comBox_01.addItem('사용안함')
            self.sj_coin_comBox_02.addItem('사용안함')
            self.sj_coin_comBox_03.addItem('사용안함')
            self.sj_coin_comBox_04.addItem('사용안함')
            if len(dfb) > 0:
                stg_list = list(dfb.index)
                stg_list.sort()
                for stg in stg_list:
                    self.sj_coin_comBox_01.addItem(stg)
                    self.sj_coin_comBox_03.addItem(stg)
            if len(dfob) > 0:
                stg_list = list(dfob.index)
                stg_list.sort()
                for stg in stg_list:
                    self.sj_coin_comBox_01.addItem(stg)
                    self.sj_coin_comBox_03.addItem(stg)
            if df['코인장초매수전략'][0] != '':
                self.sj_coin_comBox_01.setCurrentText(df['코인장초매수전략'][0])
            if df['코인장중매수전략'][0] != '':
                self.sj_coin_comBox_03.setCurrentText(df['코인장중매수전략'][0])
            if len(dfs) > 0:
                stg_list = list(dfs.index)
                stg_list.sort()
                for stg in stg_list:
                    self.sj_coin_comBox_02.addItem(stg)
                    self.sj_coin_comBox_04.addItem(stg)
            if len(dfos) > 0:
                stg_list = list(dfos.index)
                stg_list.sort()
                for stg in stg_list:
                    self.sj_coin_comBox_02.addItem(stg)
                    self.sj_coin_comBox_04.addItem(stg)
            if df['코인장초매도전략'][0] != '':
                self.sj_coin_comBox_02.setCurrentText(df['코인장초매도전략'][0])
            if df['코인장중매도전략'][0] != '':
                self.sj_coin_comBox_04.setCurrentText(df['코인장중매도전략'][0])
            self.sj_coin_liEdit_07.setText(str(df['코인장초투자금'][0]))
            self.sj_coin_liEdit_08.setText(str(df['코인장중투자금'][0]))
            self.sj_coin_liEdit_09.setText(str(df['코인손실중지수익률'][0]))
            self.sj_coin_liEdit_10.setText(str(df['코인수익중지수익률'][0]))
            if df['코인장중전략종료시간'][0] > 234500:
                QMessageBox.critical(self, '오류 알림', '코인 장중전략의 종료시간은\n234500미만으로 설정하십시오.\n')
        else:
            QMessageBox.critical(self, '오류 알림', '코인 전략 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_07(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM back', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_back_cheBox_01.setChecked(True) if df['블랙리스트추가'][0] else self.sj_back_cheBox_01.setChecked(False)
            self.sj_back_cheBox_02.setChecked(True) if df['백테주문관리적용'][0] else self.sj_back_cheBox_02.setChecked(False)
            self.sj_back_cheBox_03.setChecked(True) if df['백테매수시간기준'][0] else self.sj_back_cheBox_03.setChecked(False)
            self.sj_back_cheBox_04.setChecked(True) if df['백테일괄로딩'][0] else self.sj_back_cheBox_04.setChecked(False)
            self.sj_back_cheBox_05.setChecked(True) if not df['백테일괄로딩'][0] else self.sj_back_cheBox_05.setChecked(False)
            self.sj_back_cheBox_06.setChecked(True) if df['주식일봉데이터'][0] else self.sj_back_cheBox_06.setChecked(False)
            self.sj_back_cheBox_07.setChecked(True) if df['주식분봉데이터'][0] else self.sj_back_cheBox_07.setChecked(False)
            self.sj_back_comBox_01.setCurrentText(str(df['주식분봉기간'][0]))
            self.sj_back_cheBox_08.setChecked(True) if df['주식일봉데이터다운'][0] else self.sj_back_cheBox_08.setChecked(False)
            self.sj_back_cheBox_09.setChecked(True) if df['주식일봉다운컴종료'][0] else self.sj_back_cheBox_09.setChecked(False)
            self.sj_back_liEdit_01.setText(str(df['일봉다운실행시간'][0]))
            self.sj_back_cheBox_10.setChecked(True) if df['코인일봉데이터'][0] else self.sj_back_cheBox_10.setChecked(False)
            self.sj_back_cheBox_11.setChecked(True) if df['코인분봉데이터'][0] else self.sj_back_cheBox_11.setChecked(False)
            self.sj_back_comBox_02.setCurrentText(str(df['코인분봉기간'][0]))
            self.sj_back_cheBox_12.setChecked(True) if df['코인일봉데이터다운'][0] else self.sj_back_cheBox_12.setChecked(False)
            self.sj_back_cheBox_13.setChecked(True) if df['그래프저장하지않기'][0] else self.sj_back_cheBox_13.setChecked(False)
            self.sj_back_cheBox_14.setChecked(True) if df['그래프띄우지않기'][0] else self.sj_back_cheBox_14.setChecked(False)
            self.sj_back_cheBox_15.setChecked(True) if df['디비자동관리'][0] else self.sj_back_cheBox_15.setChecked(False)
            self.sj_back_cheBox_16.setChecked(True) if df['교차검증가중치'][0] else self.sj_back_cheBox_16.setChecked(False)
            self.sj_back_comBox_04.clear()
            self.sj_back_cheBox_19.setChecked(True) if df['백테스케쥴실행'][0] else self.sj_back_cheBox_19.setChecked(False)
            con = sqlite3.connect(DB_STRATEGY)
            dfs = pd.read_sql('SELECT * FROM schedule', con).set_index('index')
            con.close()
            indexs = list(dfs.index)
            indexs.sort()
            for index in indexs:
                self.sj_back_comBox_04.addItem(index)
            if df['백테스케쥴요일'][0] == 4:
                self.sj_back_comBox_05.setCurrentText('금')
            elif df['백테스케쥴요일'][0] == 5:
                self.sj_back_comBox_05.setCurrentText('토')
            elif df['백테스케쥴요일'][0] == 6:
                self.sj_back_comBox_05.setCurrentText('일')
            self.sj_back_liEdit_03.setText(str(df['백테스케쥴시간'][0]))
            self.sj_back_comBox_03.setCurrentText(df['백테스케쥴구분'][0])
            self.sj_back_comBox_04.setCurrentText(df['백테스케쥴명'][0])
            self.sj_back_cheBox_17.setChecked(True) if not df['백테날짜고정'][0] else self.sj_back_cheBox_17.setChecked(False)
            self.sj_back_cheBox_18.setChecked(True) if df['백테날짜고정'][0] else self.sj_back_cheBox_18.setChecked(False)
            if df['백테날짜고정'][0]:
                self.sj_back_daEdit_01.setDate(QDate.fromString(self.dict_set['백테날짜'], 'yyyyMMdd'))
            else:
                self.sj_back_liEdit_02.setText(df['백테날짜'][0])
        else:
            QMessageBox.critical(self, '오류 알림', '백테 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_08(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM etc', con).set_index('index')
        con.close()
        if len(df) > 0:
            self.sj_etc_checBox_01.setChecked(True) if df['인트로숨김'][0] else self.sj_etc_checBox_01.setChecked(False)
            self.sj_etc_checBox_02.setChecked(True) if df['저해상도'][0] else self.sj_etc_checBox_02.setChecked(False)
            self.sj_etc_checBox_04.setChecked(True) if df['휴무프로세스종료'][0] else self.sj_etc_checBox_04.setChecked(False)
            self.sj_etc_checBox_05.setChecked(True) if df['휴무컴퓨터종료'][0] else self.sj_etc_checBox_05.setChecked(False)
            self.sj_etc_checBox_03.setChecked(True) if df['창위치기억'][0] else self.sj_etc_checBox_03.setChecked(False)
            self.sj_etc_checBox_06.setChecked(True) if df['스톰라이브'][0] else self.sj_etc_checBox_06.setChecked(False)
            self.sj_etc_checBox_07.setChecked(True) if df['프로그램종료'][0] else self.sj_etc_checBox_07.setChecked(False)
            self.sj_etc_comBoxx_01.setCurrentText(df['테마'][0])
        else:
            QMessageBox.critical(self, '오류 알림', '기타 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_09(self):
        sg  = self.sj_main_comBox_01.currentText()
        sr  = 1 if self.sj_main_cheBox_01.isChecked() else 0
        st  = 1 if self.sj_main_cheBox_02.isChecked() else 0
        ss  = 1 if self.sj_main_cheBox_03.isChecked() else 0
        cg  = self.sj_main_comBox_02.currentText()
        cr  = 1 if self.sj_main_cheBox_04.isChecked() else 0
        ct  = 1 if self.sj_main_cheBox_05.isChecked() else 0
        cs  = 1 if self.sj_main_cheBox_06.isChecked() else 0
        jj  = 1 if self.sj_main_cheBox_07.isChecked() else 0
        smt = self.sj_main_liEdit_01.text()
        smd = self.sj_main_liEdit_02.text()
        cmt = self.sj_main_liEdit_03.text()
        cmd = self.sj_main_liEdit_04.text()
        rdt = self.sj_main_liEdit_05.text()
        tdt = self.sj_main_liEdit_06.text()
        mt  = 'ISOLATED' if self.sj_main_comBox_03.currentText() == '격리' else 'CROSSED'
        pt  = 'false' if self.sj_main_comBox_04.currentText() == '단방향' else 'true'
        vu  = 1 if self.sj_main_cheBox_09.isChecked() else 0
        if self.sj_main_cheBox_10.isChecked():
            rg = 1
        elif self.sj_main_cheBox_11.isChecked():
            rg = 2
        else:
            rg = 0
        if int(cmd) < 10:
            QMessageBox.critical(self, '오류 알림', '코인순위선정은 10이상의 수만 입력하십시오.\n')
        elif '' in (smt, smd, cmt, cmd, rdt, tdt):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        else:
            smt, smd, cmt, cmd, rdt, tdt = int(smt), int(smd), int(cmt), int(cmd), int(rdt), int(tdt)
            if proc_query.is_alive():
                query = f"UPDATE main SET 증권사 = '{sg}', 주식리시버 = {sr}, 주식트레이더 = {st}, 주식틱데이터저장 = {ss}, " \
                        f"거래소 = '{cg}', 코인리시버 = {cr}, 코인트레이더 = {ct}, 코인틱데이터저장 = {cs}, 장중전략조건검색식사용 = {jj}, " \
                        f"주식순위시간 = {smt}, 주식순위선정 = {smd}, 코인순위시간 = {cmt}, 코인순위선정 = {cmd}, 리시버실행시간 = {rdt}, " \
                        f"트레이더실행시간 = {tdt}, 바이낸스선물마진타입 = '{mt}', 바이낸스선물포지션 = '{pt}', '버전업' = {vu}, '리시버공유' = {rg}"
                queryQ.put(('설정디비', query))
            QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

            self.dict_set['증권사']            = sg
            self.dict_set['주식리시버']        = sr
            self.dict_set['주식트레이더']       = st
            self.dict_set['주식틱데이터저장']    = ss
            self.dict_set['거래소']            = cg
            self.dict_set['코인리시버']         = cr
            self.dict_set['코인트레이더']       = ct
            self.dict_set['코인틱데이터저장']    = cs
            self.dict_set['장중전략조건검색식사용'] = jj
            self.dict_set['주식순위시간']       = smt
            self.dict_set['주식순위선정']       = smd
            self.dict_set['코인순위시간']       = cmt
            self.dict_set['코인순위선정']       = cmd
            self.dict_set['리시버실행시간']      = rdt
            self.dict_set['트레이더실행시간']    = tdt
            self.dict_set['바이낸스선물마진타입'] = mt
            self.dict_set['바이낸스선물포지션']   = pt
            self.dict_set['버전업']            = vu
            self.dict_set['리시버공유']         = rg

            if self.dict_set['거래소'] == '업비트':
                self.sj_coin_labell_03.setText('장초전략                        백만원,  장중전략                        백만원              전략중지 및 잔고청산  |')
            else:
                self.sj_coin_labell_03.setText('장초전략                        USDT,   장중전략                        USDT              전략중지 및 잔고청산  |')
            self.UpdateDictSet()
            SetLogFile(self)

    def sjButtonClicked_10(self):
        id1 = self.sj_sacc_liEdit_01.text()
        ps1 = self.sj_sacc_liEdit_02.text()
        cp1 = self.sj_sacc_liEdit_03.text()
        ap1 = self.sj_sacc_liEdit_04.text()
        id2 = self.sj_sacc_liEdit_05.text()
        ps2 = self.sj_sacc_liEdit_06.text()
        cp2 = self.sj_sacc_liEdit_07.text()
        ap2 = self.sj_sacc_liEdit_08.text()
        comob_name = self.sj_main_comBox_01.currentText()
        if '' in (id1, ps1, cp1, ap1, id2, ps2, cp2, ap2):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        else:
            en_id1 = en_text(self.dict_set['키'], id1)
            en_ps1 = en_text(self.dict_set['키'], ps1)
            en_cp1 = en_text(self.dict_set['키'], cp1)
            en_ap1 = en_text(self.dict_set['키'], ap1)
            en_id2 = en_text(self.dict_set['키'], id2)
            en_ps2 = en_text(self.dict_set['키'], ps2)
            en_cp2 = en_text(self.dict_set['키'], cp2)
            en_ap2 = en_text(self.dict_set['키'], ap2)
            if comob_name == '키움증권1':
                if proc_query.is_alive():
                    query = f"UPDATE sacc SET " \
                            f"아이디1 = '{en_id1}', 비밀번호1 = '{en_ps1}', 인증서비밀번호1 = '{en_cp1}', 계좌비밀번호1 = '{en_ap1}', " \
                            f"아이디2 = '{en_id2}', 비밀번호2 = '{en_ps2}', 인증서비밀번호2 = '{en_cp2}', 계좌비밀번호2 = '{en_ap2}'"
                    queryQ.put(('설정디비', query))
                self.dict_set['아이디1']       = id1
                self.dict_set['비밀번호1']      = ps1
                self.dict_set['인증서비밀번호1'] = cp1
                self.dict_set['계좌비밀번호1']  = ap1
                self.dict_set['아이디2']       = id2
                self.dict_set['비밀번호2']      = ps2
                self.dict_set['인증서비밀번호2'] = cp2
                self.dict_set['계좌비밀번호2']   = ap2
            else:
                if proc_query.is_alive():
                    query = f"UPDATE sacc SET " \
                            f"아이디3 = '{en_id1}', 비밀번호3 = '{en_ps1}', 인증서비밀번호3 = '{en_cp1}', 계좌비밀번호3 = '{en_ap1}', " \
                            f"아이디4 = '{en_id2}', 비밀번호4 = '{en_ps2}', 인증서비밀번호4 = '{en_cp2}', 계좌비밀번호4 = '{en_ap2}'"
                    queryQ.put(('설정디비', query))
                self.dict_set['아이디3']        = id1
                self.dict_set['비밀번호3']      = ps1
                self.dict_set['인증서비밀번호3'] = cp1
                self.dict_set['계좌비밀번호3']   = ap1
                self.dict_set['아이디4']        = id2
                self.dict_set['비밀번호4']      = ps2
                self.dict_set['인증서비밀번호4'] = cp2
                self.dict_set['계좌비밀번호4']   = ap2
            QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def sjButtonClicked_11(self):
        access_key = self.sj_cacc_liEdit_01.text()
        secret_key = self.sj_cacc_liEdit_02.text()
        if '' in (access_key, secret_key):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        else:
            combo_name = self.sj_main_comBox_02.currentText()
            if proc_query.is_alive():
                en_access_key = en_text(self.dict_set['키'], access_key)
                en_secret_key = en_text(self.dict_set['키'], secret_key)
                if combo_name == '업비트':
                    query = f"UPDATE cacc SET Access_key1 = '{en_access_key}', Secret_key1 = '{en_secret_key}'"
                else:
                    query = f"UPDATE cacc SET Access_key2 = '{en_access_key}', Secret_key2 = '{en_secret_key}'"
                queryQ.put(('설정디비', query))

            if combo_name == '업비트':
                self.dict_set['Access_key1'] = access_key
                self.dict_set['Secret_key1'] = secret_key
            else:
                self.dict_set['Access_key2'] = access_key
                self.dict_set['Secret_key2'] = secret_key
            QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def sjButtonClicked_12(self):
        str_bot = self.sj_tele_liEdit_01.text()
        int_id = self.sj_tele_liEdit_02.text()
        if '' in (str_bot, int_id):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        else:
            if proc_query.is_alive():
                en_str_bot = en_text(self.dict_set['키'], str_bot)
                en_int_id  = en_text(self.dict_set['키'], int_id)
                df = pd.DataFrame([[en_str_bot, en_int_id]], columns=['str_bot', 'int_id'], index=[0])
                queryQ.put(('설정디비', df, 'telegram', 'replace'))

            self.dict_set['텔레그램봇토큰'] = str_bot
            self.dict_set['텔레그램사용자아이디'] = int(int_id)
            teleQ.put(('설정변경', self.dict_set))
            QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    def sjButtonClicked_13(self):
        me  = 1 if self.sj_stock_ckBox_01.isChecked() else 0
        sd  = 1 if self.sj_stock_ckBox_02.isChecked() else 0
        cs1 = 1 if self.sj_stock_ckBox_03.isChecked() else 0
        pc1 = 1 if self.sj_stock_ckBox_04.isChecked() else 0
        ce1 = 1 if self.sj_stock_ckBox_05.isChecked() else 0
        cs2 = 1 if self.sj_stock_ckBox_06.isChecked() else 0
        pc2 = 1 if self.sj_stock_ckBox_07.isChecked() else 0
        ce2 = 1 if self.sj_stock_ckBox_08.isChecked() else 0
        ts  = 1 if self.sj_stock_ckBox_09.isChecked() else 0
        cm  = 1 if self.sj_stock_ckBox_10.isChecked() else 0
        cp  = 1 if self.sj_stock_ckBox_11.isChecked() else 0
        by1 = self.sj_stock_cbBox_01.currentText()
        sl1 = self.sj_stock_cbBox_02.currentText()
        by2 = self.sj_stock_cbBox_03.currentText()
        sl2 = self.sj_stock_cbBox_04.currentText()
        at1 = self.sj_stock_lEdit_01.text()
        bc1 = self.sj_stock_lEdit_02.text()
        se1 = self.sj_stock_lEdit_03.text()
        at2 = self.sj_stock_lEdit_04.text()
        bc2 = self.sj_stock_lEdit_05.text()
        se2 = self.sj_stock_lEdit_06.text()
        sc  = self.sj_stock_lEdit_07.text()
        sj  = self.sj_stock_lEdit_08.text()
        cmp = self.sj_stock_lEdit_09.text()
        cpp = self.sj_stock_lEdit_10.text()
        if '' in (at1, bc1, se1, at2, bc2, se2, sc, sj, cmp, cpp):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        else:
            at1, bc1, se1, at2, bc2, se2, sc, sj, cmp, cpp = \
                int(at1), int(bc1), int(se1), int(at2), int(bc2), int(se2), float(sc), float(sj), float(cmp), float(cpp)
            if 152000 <= se2 <= 152759 or se2 > 152900:
                QMessageBox.critical(self, '오류 알림', '주식 장중전략의 종료시간을\n152000~152759, 152901~ 구간으로 설정할 수 없습니다.\n')
                return
            if by1 == '사용안함':
                by1 = ''
            if by2 == '사용안함':
                by2 = ''
            if sl1 == '사용안함':
                sl1 = ''
            if sl2 == '사용안함':
                sl2 = ''

            if proc_query.is_alive():
                query = f"UPDATE stock SET 주식모의투자 = {me}, 주식알림소리 = {sd}, 주식장초매수전략 = '{by1}', 주식장초매도전략 = '{sl1}', " \
                        f"주식장초평균값계산틱수 = {at1}, 주식장초최대매수종목수 = {bc1}, 주식장초전략종료시간 = {se1}, 주식장초잔고청산 = {cs1}, " \
                        f"주식장초프로세스종료 = {pc1}, 주식장초컴퓨터종료 = {ce1}, 주식장중매수전략 = '{by2}', 주식장중매도전략 = '{sl2}', " \
                        f"주식장중평균값계산틱수 = {at2}, 주식장중최대매수종목수 = {bc2}, 주식장중전략종료시간 = {se2}, 주식장중잔고청산 = {cs2}, " \
                        f"주식장중프로세스종료 = {pc2}, 주식장중컴퓨터종료 = {ce2}, 주식투자금고정 = {ts}, 주식장초투자금 = {sc}, " \
                        f"주식장중투자금 = {sj}, 주식손실중지 = {cm}, 주식손실중지수익률 = {cmp}, 주식수익중지 = {cp}, 주식수익중지수익률 = {cpp}"
                queryQ.put(('설정디비', query))
            QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

            self.dict_set['주식모의투자']         = me
            self.dict_set['주식알림소리']         = sd
            self.dict_set['주식장초매수전략']      = by1
            self.dict_set['주식장초매도전략']      = sl1
            self.dict_set['주식장초평균값계산틱수'] = at1
            self.dict_set['주식장초최대매수종목수'] = bc1
            self.dict_set['주식장초전략종료시간']   = se1
            self.dict_set['주식장초잔고청산']      = cs1
            self.dict_set['주식장초프로세스종료']   = pc1
            self.dict_set['주식장초컴퓨터종료']     = ce1
            self.dict_set['주식장중매수전략']      = by2
            self.dict_set['주식장중매도전략']      = sl2
            self.dict_set['주식장중평균값계산틱수'] = at2
            self.dict_set['주식장중최대매수종목수'] = bc2
            self.dict_set['주식장중전략종료시간']   = se2
            self.dict_set['주식장중잔고청산']      = cs2
            self.dict_set['주식장중프로세스종료']   = pc2
            self.dict_set['주식장중컴퓨터종료']    = ce2
            self.dict_set['주식투자금고정']        = ts
            self.dict_set['주식장초투자금']        = sc
            self.dict_set['주식장중투자금']        = sj
            self.dict_set['주식손실중지']         = cm
            self.dict_set['주식손실중지수익률']    = cmp
            self.dict_set['주식수익중지']         = cp
            self.dict_set['주식수익중지수익률']    = cpp
            self.UpdateDictSet()

    def sjButtonClicked_14(self):
        me  = 1 if self.sj_coin_cheBox_01.isChecked() else 0
        sd  = 1 if self.sj_coin_cheBox_02.isChecked() else 0
        cs1 = 1 if self.sj_coin_cheBox_03.isChecked() else 0
        pc1 = 1 if self.sj_coin_cheBox_04.isChecked() else 0
        ce1 = 1 if self.sj_coin_cheBox_05.isChecked() else 0
        cs2 = 1 if self.sj_coin_cheBox_06.isChecked() else 0
        pc2 = 1 if self.sj_coin_cheBox_07.isChecked() else 0
        ce2 = 1 if self.sj_coin_cheBox_08.isChecked() else 0
        tc  = 1 if self.sj_coin_cheBox_09.isChecked() else 0
        cm  = 1 if self.sj_coin_cheBox_10.isChecked() else 0
        cp  = 1 if self.sj_coin_cheBox_11.isChecked() else 0
        by1 = self.sj_coin_comBox_01.currentText()
        sl1 = self.sj_coin_comBox_02.currentText()
        by2 = self.sj_coin_comBox_03.currentText()
        sl2 = self.sj_coin_comBox_04.currentText()
        at1 = self.sj_coin_liEdit_01.text()
        bc1 = self.sj_coin_liEdit_02.text()
        se1 = self.sj_coin_liEdit_03.text()
        at2 = self.sj_coin_liEdit_04.text()
        bc2 = self.sj_coin_liEdit_05.text()
        se2 = self.sj_coin_liEdit_06.text()
        sc  = self.sj_coin_liEdit_07.text()
        sj  = self.sj_coin_liEdit_08.text()
        cmp = self.sj_coin_liEdit_09.text()
        cpp = self.sj_coin_liEdit_10.text()
        if '' in (at1, bc1, se1, at2, bc2, se2, sc, sj, cmp, cpp):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        else:
            buttonReply = QMessageBox.question(
                self, "경고", "코인의 전략 종료시간은 UTC 기준입니다.\n한국시간 -9시간으로 설정하였습니까?\n",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                at1, bc1, se1, at2, bc2, se2, sc, sj, cmp, cpp = \
                    int(at1), int(bc1), int(se1), int(at2), int(bc2), int(se2), float(sc), float(sj), float(cmp), float(cpp)
                if se2 > 234500:
                    QMessageBox.critical(self, '오류 알림', '코인 장중전략의 종료시간은\n234500미만으로 설정하십시오.\n')
                    return

                if by1 == '사용안함':
                    by1 = ''
                if by2 == '사용안함':
                    by2 = ''
                if sl1 == '사용안함':
                    sl1 = ''
                if sl2 == '사용안함':
                    sl2 = ''

                if proc_query.is_alive():
                    query = f"UPDATE coin SET 코인모의투자 = {me}, 코인알림소리 = {sd}, 코인장초매수전략 = '{by1}', 코인장초매도전략 = '{sl1}', " \
                            f"코인장초평균값계산틱수 = {at1}, 코인장초최대매수종목수 = {bc1}, 코인장초전략종료시간 = {se1}, 코인장초잔고청산 = {cs1}, " \
                            f"코인장초프로세스종료 = {pc1}, 코인장초컴퓨터종료 = {ce1}, 코인장중매수전략 = '{by2}', 코인장중매도전략 = '{sl2}', " \
                            f"코인장중평균값계산틱수 = {at2}, 코인장중최대매수종목수 = {bc2}, 코인장중전략종료시간 = {se2}, 코인장중잔고청산 = {cs2}, " \
                            f"코인장중프로세스종료 = {pc2}, 코인장중컴퓨터종료 = {ce2}, 코인투자금고정 = {tc}, 코인장초투자금 = {sc}, " \
                            f"코인장중투자금 = {sj}, 코인손실중지 = {cm}, 코인손실중지수익률 = {cmp}, 코인수익중지 = {cp}, 코인수익중지수익률 = {cpp}"
                    queryQ.put(('설정디비', query))
                QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

                self.dict_set['코인모의투자']         = me
                self.dict_set['코인알림소리']         = sd
                self.dict_set['코인장초매수전략']      = by1
                self.dict_set['코인장초매도전략']      = sl1
                self.dict_set['코인장초평균값계산틱수'] = at1
                self.dict_set['코인장초최대매수종목수'] = bc1
                self.dict_set['코인장초전략종료시간']   = se1
                self.dict_set['코인장초잔고청산']      = cs1
                self.dict_set['코인장초프로세스종료']   = pc1
                self.dict_set['코인장초컴퓨터종료']    = ce1
                self.dict_set['코인장중매수전략']      = by2
                self.dict_set['코인장중매도전략']      = sl2
                self.dict_set['코인장중평균값계산틱수'] = at2
                self.dict_set['코인장중최대매수종목수'] = bc2
                self.dict_set['코인장중전략종료시간']   = se2
                self.dict_set['코인장중잔고청산']      = cs2
                self.dict_set['코인장중프로세스종료']   = pc2
                self.dict_set['코인장중컴퓨터종료']     = ce2
                self.dict_set['코인투자금고정']        = tc
                self.dict_set['코인장초투자금']        = sc
                self.dict_set['코인장중투자금']        = sj
                self.dict_set['코인손실중지']         = cm
                self.dict_set['코인손실중지수익률']    = cmp
                self.dict_set['코인수익중지']         = cp
                self.dict_set['코인수익중지수익률']    = cpp
                self.UpdateDictSet()

    def sjButtonClicked_15(self):
        bl  = 1 if self.sj_back_cheBox_01.isChecked() else 0
        bbg = 1 if self.sj_back_cheBox_02.isChecked() else 0
        bsg = 1 if self.sj_back_cheBox_03.isChecked() else 0
        bld = 1 if self.sj_back_cheBox_04.isChecked() else 0
        sdb = 1 if self.sj_back_cheBox_06.isChecked() else 0
        smb = 1 if self.sj_back_cheBox_07.isChecked() else 0
        sab = 1 if self.sj_back_cheBox_08.isChecked() else 0
        de  = 1 if self.sj_back_cheBox_09.isChecked() else 0
        cdb = 1 if self.sj_back_cheBox_10.isChecked() else 0
        cmb = 1 if self.sj_back_cheBox_11.isChecked() else 0
        cab = 1 if self.sj_back_cheBox_12.isChecked() else 0
        gsv = 1 if self.sj_back_cheBox_13.isChecked() else 0
        gpl = 1 if self.sj_back_cheBox_14.isChecked() else 0
        atd = 1 if self.sj_back_cheBox_15.isChecked() else 0
        ext = 1 if self.sj_back_cheBox_16.isChecked() else 0
        bdf = 1 if self.sj_back_cheBox_18.isChecked() else 0
        dt  = self.sj_back_liEdit_01.text()
        smp = int(self.sj_back_comBox_01.currentText())
        cmp = int(self.sj_back_comBox_02.currentText())
        bwd = 0
        bss = 1 if self.sj_back_cheBox_19.isChecked() else 0
        if self.sj_back_comBox_05.currentText() == '금':   bwd = 4
        elif self.sj_back_comBox_05.currentText() == '토': bwd = 5
        elif self.sj_back_comBox_05.currentText() == '일': bwd = 6
        bst = self.sj_back_liEdit_03.text()
        abd = self.sj_back_comBox_03.currentText()
        abn = self.sj_back_comBox_04.currentText()
        if bdf:
            bd = self.sj_back_daEdit_01.date().toString('yyyyMMdd')
        else:
            bd = self.sj_back_liEdit_02.text()

        if '' in (dt, bd, bst):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        elif int(dt) < 154000:
            QMessageBox.critical(self, '오류 알림', '주식 일봉데이터 자동 다운로드는\n15시 40분 이전에 실행할 수 없습니다.\n')
        else:
            dt, bst = int(dt), int(bst)
            if proc_query.is_alive():
                query = f"UPDATE back SET 블랙리스트추가 = {bl}, 백테주문관리적용 = {bbg}, 백테매수시간기준 = {bsg}, 백테일괄로딩 = {bld}, 주식일봉데이터 = {sdb}, " \
                        f"주식분봉데이터 = {smb}, 주식분봉기간 = {smp}, 주식일봉데이터다운 = {sab}, 주식일봉다운컴종료 = {de}, 일봉다운실행시간 = {dt}, " \
                        f"코인일봉데이터 = {cdb}, 코인분봉데이터 = {cmb}, 코인분봉기간 = {cmp}, 코인일봉데이터다운 = {cab}, 그래프저장하지않기 = {gsv}, " \
                        f"그래프띄우지않기 = {gpl}, 디비자동관리 = {atd}, 교차검증가중치 = {ext}, 백테스케쥴실행 = {bss}, 백테스케쥴요일 = {bwd}, 백테스케쥴시간 = {bst}, " \
                        f"백테스케쥴구분 = '{abd}', 백테스케쥴명 = '{abn}', 백테날짜고정 = {bdf}, 백테날짜 = '{bd}'"
                queryQ.put(('설정디비', query))
            QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

            self.dict_set['블랙리스트추가']    = bl
            self.dict_set['백테주문관리적용']   = bbg
            self.dict_set['백테매수시간기준']   = bsg
            self.dict_set['백테일괄로딩']      = bld
            self.dict_set['주식일봉데이터']    = sdb
            self.dict_set['주식분봉데이터']    = smb
            self.dict_set['주식분봉기간']      = smp
            self.dict_set['주식일봉데이터다운'] = sab
            self.dict_set['주식일봉다운컴종료'] = de
            self.dict_set['일봉다운실행시간']  = dt
            self.dict_set['코인일봉데이터']    = cdb
            self.dict_set['코인분봉데이터']    = cmb
            self.dict_set['코인분봉기간']      = cmp
            self.dict_set['코인일봉데이터다운'] = cab
            self.dict_set['그래프저장하지않기'] = gsv
            self.dict_set['그래프띄우지않기']   = gpl
            self.dict_set['디비자동관리']      = atd
            self.dict_set['교차검증가중치']    = ext
            self.dict_set['백테스케쥴실행']    = bss
            self.dict_set['백테스케쥴요일']    = bwd
            self.dict_set['백테스케쥴시간']    = bst
            self.dict_set['백테스케쥴구분']    = abd
            self.dict_set['백테스케쥴명']      = abn
            self.dict_set['백테날짜고정']      = bdf
            self.dict_set['백테날짜']         = bd
            self.UpdateDictSet()

            if sab:
                QMessageBox.warning(self, '경고', '전략종료 후 컴퓨터종료가 체크되어 있으면\n일봉 다운로드가 실행되지 않으니 유의하시길 바랍니다.\n')

    def sjButtonClicked_16(self):
        the = self.sj_etc_comBoxx_01.currentText()
        inr = 1 if self.sj_etc_checBox_01.isChecked() else 0
        ldp = 1 if self.sj_etc_checBox_02.isChecked() else 0
        cgo = 1 if self.sj_etc_checBox_03.isChecked() else 0
        pe  = 1 if self.sj_etc_checBox_04.isChecked() else 0
        ce  = 1 if self.sj_etc_checBox_05.isChecked() else 0
        slv = 1 if self.sj_etc_checBox_06.isChecked() else 0
        pex = 1 if self.sj_etc_checBox_07.isChecked() else 0

        if proc_query.is_alive():
            query = f"UPDATE etc SET 테마 = '{the}', 인트로숨김 = {inr}, 저해상도 = {ldp}, 창위치기억 = {cgo}, " \
                    f"휴무프로세스종료 = {pe}, 휴무컴퓨터종료 = {ce}, 스톰라이브 = {slv}, 프로그램종료 = {pex}"
            queryQ.put(('설정디비', query))
        QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

        self.dict_set['테마']           = the
        self.dict_set['저해상도']        = ldp
        self.dict_set['인트로숨김']      = ldp
        self.dict_set['창위치기억']      = cgo
        self.dict_set['휴무프로세스종료'] = pe
        self.dict_set['휴무컴퓨터종료']   = ce
        self.dict_set['스톰라이브']      = slv
        self.dict_set['프로그램종료']    = pex
        self.UpdateDictSet()

    def sjButtonClicked_17(self):
        if self.sj_etc_pButton_01.text() == '계정 텍스트 보기':
            self.pa_lineEditttt_01.clear()
            if not self.dialog_pass.isVisible():
                self.dialog_pass.show()
        else:
            self.sj_sacc_liEdit_01.setEchoMode(QLineEdit.Password)
            self.sj_sacc_liEdit_02.setEchoMode(QLineEdit.Password)
            self.sj_sacc_liEdit_03.setEchoMode(QLineEdit.Password)
            self.sj_sacc_liEdit_04.setEchoMode(QLineEdit.Password)
            self.sj_sacc_liEdit_05.setEchoMode(QLineEdit.Password)
            self.sj_sacc_liEdit_06.setEchoMode(QLineEdit.Password)
            self.sj_sacc_liEdit_07.setEchoMode(QLineEdit.Password)
            self.sj_sacc_liEdit_08.setEchoMode(QLineEdit.Password)
            self.sj_cacc_liEdit_01.setEchoMode(QLineEdit.Password)
            self.sj_cacc_liEdit_02.setEchoMode(QLineEdit.Password)
            self.sj_tele_liEdit_01.setEchoMode(QLineEdit.Password)
            self.sj_tele_liEdit_02.setEchoMode(QLineEdit.Password)
            self.sj_etc_pButton_01.setText('계정 텍스트 보기')
            self.sj_etc_pButton_01.setStyleSheet(style_bc_bt)

    def sjButtonClicked_18(self):
        self.daydata_download = True
        subprocess.Popen('python download_kiwoom.py')

    def sjButtonClicked_20(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM stockbuyorder', con).set_index('index')
        con.close()

        if len(df) > 0:
            self.sj_sodb_checkBox_01.setChecked(True) if df['주식매수주문구분'][0] == '시장가' else self.sj_sodb_checkBox_01.setChecked(False)
            self.sj_sodb_checkBox_02.setChecked(True) if df['주식매수주문구분'][0] == '지정가' else self.sj_sodb_checkBox_02.setChecked(False)
            self.sj_sodb_checkBox_03.setChecked(True) if df['주식매수주문구분'][0] == '최유리지정가' else self.sj_sodb_checkBox_03.setChecked(False)
            self.sj_sodb_checkBox_04.setChecked(True) if df['주식매수주문구분'][0] == '최우선지정가' else self.sj_sodb_checkBox_04.setChecked(False)
            self.sj_sodb_checkBox_05.setChecked(True) if df['주식매수주문구분'][0] == '지정가IOC' else self.sj_sodb_checkBox_05.setChecked(False)
            self.sj_sodb_checkBox_06.setChecked(True) if df['주식매수주문구분'][0] == '시장가IOC' else self.sj_sodb_checkBox_06.setChecked(False)
            self.sj_sodb_checkBox_07.setChecked(True) if df['주식매수주문구분'][0] == '최유리IOC' else self.sj_sodb_checkBox_07.setChecked(False)
            self.sj_sodb_checkBox_08.setChecked(True) if df['주식매수주문구분'][0] == '지정가FOK' else self.sj_sodb_checkBox_08.setChecked(False)
            self.sj_sodb_checkBox_09.setChecked(True) if df['주식매수주문구분'][0] == '시장가FOK' else self.sj_sodb_checkBox_09.setChecked(False)
            self.sj_sodb_checkBox_10.setChecked(True) if df['주식매수주문구분'][0] == '최유리FOK' else self.sj_sodb_checkBox_10.setChecked(False)
            self.sj_sodb_lineEdit_01.setText(str(df['주식매수분할횟수'][0]))
            self.sj_sodb_checkBox_11.setChecked(True) if df['주식매수분할방법'][0] == 1 else self.sj_sodb_checkBox_11.setChecked(False)
            self.sj_sodb_checkBox_12.setChecked(True) if df['주식매수분할방법'][0] == 2 else self.sj_sodb_checkBox_12.setChecked(False)
            self.sj_sodb_checkBox_13.setChecked(True) if df['주식매수분할방법'][0] == 3 else self.sj_sodb_checkBox_13.setChecked(False)
            self.sj_sodb_checkBox_14.setChecked(True) if df['주식매수분할시그널'][0] else self.sj_sodb_checkBox_14.setChecked(False)
            self.sj_sodb_checkBox_15.setChecked(True) if df['주식매수분할하방'][0] else self.sj_sodb_checkBox_15.setChecked(False)
            self.sj_sodb_checkBox_16.setChecked(True) if df['주식매수분할상방'][0] else self.sj_sodb_checkBox_16.setChecked(False)
            self.sj_sodb_lineEdit_02.setText(str(df['주식매수분할하방수익률'][0]))
            self.sj_sodb_lineEdit_03.setText(str(df['주식매수분할상방수익률'][0]))
            self.sj_sodb_checkBox_27.setChecked(True) if df['주식매수분할고정수익률'][0] else self.sj_sodb_checkBox_27.setChecked(False)
            self.sj_sodb_comboBox_01.setCurrentText(str(df['주식매수지정가기준가격'][0]))
            self.sj_sodb_comboBox_02.setCurrentText(str(df['주식매수지정가호가번호'][0]))
            self.sj_sodb_comboBox_03.setCurrentText(str(df['주식매수시장가잔량범위'][0]))
            self.sj_sodb_checkBox_17.setChecked(True) if df['주식매수취소관심이탈'][0] else self.sj_sodb_checkBox_17.setChecked(False)
            self.sj_sodb_checkBox_18.setChecked(True) if df['주식매수취소매도시그널'][0] else self.sj_sodb_checkBox_18.setChecked(False)
            self.sj_sodb_checkBox_19.setChecked(True) if df['주식매수취소시간'][0] else self.sj_sodb_checkBox_19.setChecked(False)
            self.sj_sodb_lineEdit_04.setText(str(df['주식매수취소시간초'][0]))
            self.sj_sodb_checkBox_20.setChecked(True) if df['주식매수금지블랙리스트'][0] else self.sj_sodb_checkBox_20.setChecked(False)
            self.sj_sodb_checkBox_21.setChecked(True) if df['주식매수금지라운드피겨'][0] else self.sj_sodb_checkBox_21.setChecked(False)
            self.sj_sodb_lineEdit_05.setText(str(df['주식매수금지라운드호가'][0]))
            self.sj_sodb_checkBox_22.setChecked(True) if df['주식매수금지손절횟수'][0] else self.sj_sodb_checkBox_22.setChecked(False)
            self.sj_sodb_lineEdit_06.setText(str(df['주식매수금지손절횟수값'][0]))
            self.sj_sodb_checkBox_23.setChecked(True) if df['주식매수금지거래횟수'][0] else self.sj_sodb_checkBox_23.setChecked(False)
            self.sj_sodb_lineEdit_07.setText(str(df['주식매수금지거래횟수값'][0]))
            self.sj_sodb_checkBox_24.setChecked(True) if df['주식매수금지시간'][0] else self.sj_sodb_checkBox_24.setChecked(False)
            self.sj_sodb_lineEdit_08.setText(str(df['주식매수금지시작시간'][0]))
            self.sj_sodb_lineEdit_09.setText(str(df['주식매수금지종료시간'][0]))
            self.sj_sodb_checkBox_25.setChecked(True) if df['주식매수금지간격'][0] else self.sj_sodb_checkBox_25.setChecked(False)
            self.sj_sodb_lineEdit_10.setText(str(df['주식매수금지간격초'][0]))
            self.sj_sodb_checkBox_26.setChecked(True) if df['주식매수금지손절간격'][0] else self.sj_sodb_checkBox_26.setChecked(False)
            self.sj_sodb_lineEdit_11.setText(str(df['주식매수금지손절간격초'][0]))
            self.sj_sodb_lineEdit_12.setText(str(df['주식매수정정횟수'][0]))
            self.sj_sodb_comboBox_04.setCurrentText(str(df['주식매수정정호가차이'][0]))
            self.sj_sodb_comboBox_05.setCurrentText(str(df['주식매수정정호가'][0]))
        else:
            QMessageBox.critical(self, '오류 알림', '주문관리 주식매수 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_21(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM stocksellorder', con).set_index('index')
        con.close()

        if len(df) > 0:
            self.sj_sods_checkBox_01.setChecked(True) if df['주식매도주문구분'][0] == '시장가' else self.sj_sods_checkBox_01.setChecked(False)
            self.sj_sods_checkBox_02.setChecked(True) if df['주식매도주문구분'][0] == '지정가' else self.sj_sods_checkBox_02.setChecked(False)
            self.sj_sods_checkBox_03.setChecked(True) if df['주식매도주문구분'][0] == '최유리지정가' else self.sj_sods_checkBox_03.setChecked(False)
            self.sj_sods_checkBox_04.setChecked(True) if df['주식매도주문구분'][0] == '최우선지정가' else self.sj_sods_checkBox_04.setChecked(False)
            self.sj_sods_checkBox_05.setChecked(True) if df['주식매도주문구분'][0] == '지정가IOC' else self.sj_sods_checkBox_05.setChecked(False)
            self.sj_sods_checkBox_06.setChecked(True) if df['주식매도주문구분'][0] == '시장가IOC' else self.sj_sods_checkBox_06.setChecked(False)
            self.sj_sods_checkBox_07.setChecked(True) if df['주식매도주문구분'][0] == '최유리IOC' else self.sj_sods_checkBox_07.setChecked(False)
            self.sj_sods_checkBox_08.setChecked(True) if df['주식매도주문구분'][0] == '지정가FOK' else self.sj_sods_checkBox_08.setChecked(False)
            self.sj_sods_checkBox_09.setChecked(True) if df['주식매도주문구분'][0] == '시장가FOK' else self.sj_sods_checkBox_09.setChecked(False)
            self.sj_sods_checkBox_10.setChecked(True) if df['주식매도주문구분'][0] == '최유리FOK' else self.sj_sods_checkBox_10.setChecked(False)
            self.sj_sods_lineEdit_01.setText(str(df['주식매도분할횟수'][0]))
            self.sj_sods_checkBox_11.setChecked(True) if df['주식매도분할방법'][0] == 1 else self.sj_sods_checkBox_11.setChecked(False)
            self.sj_sods_checkBox_12.setChecked(True) if df['주식매도분할방법'][0] == 2 else self.sj_sods_checkBox_12.setChecked(False)
            self.sj_sods_checkBox_13.setChecked(True) if df['주식매도분할방법'][0] == 3 else self.sj_sods_checkBox_13.setChecked(False)
            self.sj_sods_checkBox_14.setChecked(True) if df['주식매도분할시그널'][0] else self.sj_sods_checkBox_14.setChecked(False)
            self.sj_sods_checkBox_15.setChecked(True) if df['주식매도분할하방'][0] else self.sj_sods_checkBox_15.setChecked(False)
            self.sj_sods_checkBox_16.setChecked(True) if df['주식매도분할상방'][0] else self.sj_sods_checkBox_16.setChecked(False)
            self.sj_sods_lineEdit_02.setText(str(df['주식매도분할하방수익률'][0]))
            self.sj_sods_lineEdit_03.setText(str(df['주식매도분할상방수익률'][0]))
            self.sj_sods_comboBox_01.setCurrentText(str(df['주식매도지정가기준가격'][0]))
            self.sj_sods_comboBox_02.setCurrentText(str(df['주식매도지정가호가번호'][0]))
            self.sj_sods_comboBox_03.setCurrentText(str(df['주식매도시장가잔량범위'][0]))
            self.sj_sods_checkBox_17.setChecked(True) if df['주식매도취소관심진입'][0] else self.sj_sods_checkBox_17.setChecked(False)
            self.sj_sods_checkBox_18.setChecked(True) if df['주식매도취소매수시그널'][0] else self.sj_sods_checkBox_18.setChecked(False)
            self.sj_sods_checkBox_19.setChecked(True) if df['주식매도취소시간'][0] else self.sj_sods_checkBox_19.setChecked(False)
            self.sj_sods_lineEdit_04.setText(str(df['주식매도취소시간초'][0]))
            self.sj_sods_checkBox_20.setChecked(True) if df['주식매도손절수익률청산'][0] else self.sj_sods_checkBox_20.setChecked(False)
            self.sj_sods_lineEdit_05.setText(str(df['주식매도손절수익률'][0]))
            self.sj_sods_checkBox_21.setChecked(True) if df['주식매도손절수익금청산'][0] else self.sj_sods_checkBox_21.setChecked(False)
            self.sj_sods_lineEdit_06.setText(str(df['주식매도손절수익금'][0]))
            self.sj_sods_checkBox_22.setChecked(True) if df['주식매도금지매수횟수'][0] else self.sj_sods_checkBox_22.setChecked(False)
            self.sj_sods_lineEdit_07.setText(str(df['주식매도금지매수횟수값'][0]))
            self.sj_sods_checkBox_23.setChecked(True) if df['주식매도금지라운드피겨'][0] else self.sj_sods_checkBox_23.setChecked(False)
            self.sj_sods_lineEdit_08.setText(str(df['주식매도금지라운드호가'][0]))
            self.sj_sods_checkBox_24.setChecked(True) if df['주식매도금지시간'][0] else self.sj_sods_checkBox_24.setChecked(False)
            self.sj_sods_lineEdit_09.setText(str(df['주식매도금지시작시간'][0]))
            self.sj_sods_lineEdit_10.setText(str(df['주식매도금지종료시간'][0]))
            self.sj_sods_checkBox_25.setChecked(True) if df['주식매도금지간격'][0] else self.sj_sods_checkBox_25.setChecked(False)
            self.sj_sods_lineEdit_11.setText(str(df['주식매도금지간격초'][0]))
            self.sj_sods_lineEdit_12.setText(str(df['주식매도정정횟수'][0]))
            self.sj_sods_comboBox_04.setCurrentText(str(df['주식매도정정호가차이'][0]))
            self.sj_sods_comboBox_05.setCurrentText(str(df['주식매도정정호가'][0]))
        else:
            QMessageBox.critical(self, '오류 알림', '주문관리 주식매도 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_22(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM coinbuyorder', con).set_index('index')
        con.close()

        if len(df) > 0:
            self.sj_codb_checkBox_01.setChecked(True) if df['코인매수주문구분'][0] == '시장가' else self.sj_codb_checkBox_01.setChecked(False)
            self.sj_codb_checkBox_02.setChecked(True) if df['코인매수주문구분'][0] == '지정가' else self.sj_codb_checkBox_02.setChecked(False)
            self.sj_codb_checkBox_19.setChecked(True) if df['코인매수주문구분'][0] == '지정가IOC' else self.sj_codb_checkBox_19.setChecked(False)
            self.sj_codb_checkBox_20.setChecked(True) if df['코인매수주문구분'][0] == '지정가FOK' else self.sj_codb_checkBox_20.setChecked(False)
            self.sj_codb_lineEdit_01.setText(str(df['코인매수분할횟수'][0]))
            self.sj_codb_checkBox_03.setChecked(True) if df['코인매수분할방법'][0] == 1 else self.sj_codb_checkBox_03.setChecked(False)
            self.sj_codb_checkBox_04.setChecked(True) if df['코인매수분할방법'][0] == 2 else self.sj_codb_checkBox_04.setChecked(False)
            self.sj_codb_checkBox_05.setChecked(True) if df['코인매수분할방법'][0] == 3 else self.sj_codb_checkBox_05.setChecked(False)
            self.sj_codb_checkBox_06.setChecked(True) if df['코인매수분할시그널'][0] else self.sj_codb_checkBox_06.setChecked(False)
            self.sj_codb_checkBox_07.setChecked(True) if df['코인매수분할하방'][0] else self.sj_codb_checkBox_07.setChecked(False)
            self.sj_codb_checkBox_08.setChecked(True) if df['코인매수분할상방'][0] else self.sj_codb_checkBox_08.setChecked(False)
            self.sj_codb_lineEdit_02.setText(str(df['코인매수분할하방수익률'][0]))
            self.sj_codb_lineEdit_03.setText(str(df['코인매수분할상방수익률'][0]))
            self.sj_codb_checkBox_27.setChecked(True) if df['코인매수분할고정수익률'][0] else self.sj_codb_checkBox_27.setChecked(False)
            self.sj_codb_comboBox_01.setCurrentText(str(df['코인매수지정가기준가격'][0]))
            self.sj_codb_comboBox_02.setCurrentText(str(df['코인매수지정가호가번호'][0]))
            self.sj_codb_comboBox_03.setCurrentText(str(df['코인매수시장가잔량범위'][0]))
            self.sj_codb_checkBox_09.setChecked(True) if df['코인매수취소관심이탈'][0] else self.sj_codb_checkBox_09.setChecked(False)
            self.sj_codb_checkBox_10.setChecked(True) if df['코인매수취소매도시그널'][0] else self.sj_codb_checkBox_10.setChecked(False)
            self.sj_codb_checkBox_11.setChecked(True) if df['코인매수취소시간'][0] else self.sj_codb_checkBox_11.setChecked(False)
            self.sj_codb_lineEdit_04.setText(str(df['코인매수취소시간초'][0]))
            self.sj_codb_checkBox_12.setChecked(True) if df['코인매수금지블랙리스트'][0] else self.sj_codb_checkBox_12.setChecked(False)
            self.sj_codb_checkBox_13.setChecked(True) if df['코인매수금지200원이하'][0] else self.sj_codb_checkBox_13.setChecked(False)
            self.sj_codb_checkBox_14.setChecked(True) if df['코인매수금지손절횟수'][0] else self.sj_codb_checkBox_14.setChecked(False)
            self.sj_codb_lineEdit_05.setText(str(df['코인매수금지손절횟수값'][0]))
            self.sj_codb_checkBox_15.setChecked(True) if df['코인매수금지거래횟수'][0] else self.sj_codb_checkBox_15.setChecked(False)
            self.sj_codb_lineEdit_06.setText(str(df['코인매수금지거래횟수값'][0]))
            self.sj_codb_checkBox_16.setChecked(True) if df['코인매수금지시간'][0] else self.sj_codb_checkBox_16.setChecked(False)
            self.sj_codb_lineEdit_07.setText(str(df['코인매수금지시작시간'][0]))
            self.sj_codb_lineEdit_08.setText(str(df['코인매수금지종료시간'][0]))
            self.sj_codb_checkBox_17.setChecked(True) if df['코인매수금지간격'][0] else self.sj_codb_checkBox_17.setChecked(False)
            self.sj_codb_lineEdit_09.setText(str(df['코인매수금지간격초'][0]))
            self.sj_codb_checkBox_18.setChecked(True) if df['코인매수금지손절간격'][0] else self.sj_codb_checkBox_18.setChecked(False)
            self.sj_codb_lineEdit_10.setText(str(df['코인매수금지손절간격초'][0]))
            self.sj_codb_lineEdit_11.setText(str(df['코인매수정정횟수'][0]))
            self.sj_codb_comboBox_04.setCurrentText(str(df['코인매수정정호가차이'][0]))
            self.sj_codb_comboBox_05.setCurrentText(str(df['코인매수정정호가'][0]))
        else:
            QMessageBox.critical(self, '오류 알림', '주문관리 코인매수 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_23(self):
        con = sqlite3.connect(DB_SETTING)
        df  = pd.read_sql('SELECT * FROM coinsellorder', con).set_index('index')
        con.close()

        if len(df) > 0:
            self.sj_cods_checkBox_01.setChecked(True) if df['코인매도주문구분'][0] == '시장가' else self.sj_cods_checkBox_01.setChecked(False)
            self.sj_cods_checkBox_02.setChecked(True) if df['코인매도주문구분'][0] == '지정가' else self.sj_cods_checkBox_02.setChecked(False)
            self.sj_cods_checkBox_19.setChecked(True) if df['코인매도주문구분'][0] == '지정가IOC' else self.sj_cods_checkBox_19.setChecked(False)
            self.sj_cods_checkBox_20.setChecked(True) if df['코인매도주문구분'][0] == '지정가FOK' else self.sj_cods_checkBox_20.setChecked(False)
            self.sj_cods_lineEdit_01.setText(str(df['코인매도분할횟수'][0]))
            self.sj_cods_checkBox_03.setChecked(True) if df['코인매도분할방법'][0] == 1 else self.sj_cods_checkBox_03.setChecked(False)
            self.sj_cods_checkBox_04.setChecked(True) if df['코인매도분할방법'][0] == 2 else self.sj_cods_checkBox_04.setChecked(False)
            self.sj_cods_checkBox_05.setChecked(True) if df['코인매도분할방법'][0] == 3 else self.sj_cods_checkBox_05.setChecked(False)
            self.sj_cods_checkBox_06.setChecked(True) if df['코인매도분할시그널'][0] else self.sj_cods_checkBox_06.setChecked(False)
            self.sj_cods_checkBox_07.setChecked(True) if df['코인매도분할하방'][0] else self.sj_cods_checkBox_07.setChecked(False)
            self.sj_cods_checkBox_08.setChecked(True) if df['코인매도분할상방'][0] else self.sj_cods_checkBox_08.setChecked(False)
            self.sj_cods_lineEdit_02.setText(str(df['코인매도분할하방수익률'][0]))
            self.sj_cods_lineEdit_03.setText(str(df['코인매도분할상방수익률'][0]))
            self.sj_cods_comboBox_01.setCurrentText(str(df['코인매도지정가기준가격'][0]))
            self.sj_cods_comboBox_02.setCurrentText(str(df['코인매도지정가호가번호'][0]))
            self.sj_cods_comboBox_03.setCurrentText(str(df['코인매도시장가잔량범위'][0]))
            self.sj_cods_checkBox_09.setChecked(True) if df['코인매도취소관심진입'][0] else self.sj_cods_checkBox_09.setChecked(False)
            self.sj_cods_checkBox_10.setChecked(True) if df['코인매도취소매수시그널'][0] else self.sj_cods_checkBox_10.setChecked(False)
            self.sj_cods_checkBox_11.setChecked(True) if df['코인매도취소시간'][0] else self.sj_cods_checkBox_11.setChecked(False)
            self.sj_cods_lineEdit_04.setText(str(df['코인매도취소시간초'][0]))
            self.sj_cods_checkBox_12.setChecked(True) if df['코인매도손절수익률청산'][0] else self.sj_cods_checkBox_12.setChecked(False)
            self.sj_cods_lineEdit_05.setText(str(df['코인매도손절수익률'][0]))
            self.sj_cods_checkBox_13.setChecked(True) if df['코인매도손절수익금청산'][0] else self.sj_cods_checkBox_13.setChecked(False)
            self.sj_cods_lineEdit_06.setText(str(df['코인매도손절수익금'][0]))
            self.sj_cods_checkBox_14.setChecked(True) if df['코인매도금지매수횟수'][0] else self.sj_cods_checkBox_14.setChecked(False)
            self.sj_cods_lineEdit_07.setText(str(df['코인매도금지매수횟수값'][0]))
            self.sj_cods_checkBox_15.setChecked(True) if df['코인매도금지시간'][0] else self.sj_cods_checkBox_15.setChecked(False)
            self.sj_cods_lineEdit_08.setText(str(df['코인매도금지시작시간'][0]))
            self.sj_cods_lineEdit_09.setText(str(df['코인매도금지종료시간'][0]))
            self.sj_cods_checkBox_16.setChecked(True) if df['코인매도금지간격'][0] else self.sj_cods_checkBox_16.setChecked(False)
            self.sj_cods_lineEdit_10.setText(str(df['코인매도금지간격초'][0]))
            self.sj_cods_lineEdit_11.setText(str(df['코인매도정정횟수'][0]))
            self.sj_cods_comboBox_04.setCurrentText(str(df['코인매도정정호가차이'][0]))
            self.sj_cods_comboBox_05.setCurrentText(str(df['코인매도정정호가'][0]))
        else:
            QMessageBox.critical(self, '오류 알림', '주문관리 코인매도 설정값이\n존재하지 않습니다.\n')

    def sjButtonClicked_24(self):
        od = ''
        if self.sj_sodb_checkBox_01.isChecked(): od = '시장가'
        if self.sj_sodb_checkBox_02.isChecked(): od = '지정가'
        if self.sj_sodb_checkBox_03.isChecked(): od = '최유리지정가'
        if self.sj_sodb_checkBox_04.isChecked(): od = '최우선지정가'
        if self.sj_sodb_checkBox_05.isChecked(): od = '지정가IOC'
        if self.sj_sodb_checkBox_06.isChecked(): od = '시장가IOC'
        if self.sj_sodb_checkBox_07.isChecked(): od = '최유리IOC'
        if self.sj_sodb_checkBox_08.isChecked(): od = '지정가FOK'
        if self.sj_sodb_checkBox_09.isChecked(): od = '시장가FOK'
        if self.sj_sodb_checkBox_10.isChecked(): od = '최유리FOK'
        dc = self.sj_sodb_lineEdit_01.text()
        ds = 0
        if self.sj_sodb_checkBox_11.isChecked(): ds = 1
        if self.sj_sodb_checkBox_12.isChecked(): ds = 2
        if self.sj_sodb_checkBox_13.isChecked(): ds = 3
        ds1  = 1 if self.sj_sodb_checkBox_14.isChecked() else 0
        ds2  = 1 if self.sj_sodb_checkBox_15.isChecked() else 0
        ds3  = 1 if self.sj_sodb_checkBox_16.isChecked() else 0
        ds2c = self.sj_sodb_lineEdit_02.text()
        ds3c = self.sj_sodb_lineEdit_03.text()
        bp   = self.sj_sodb_comboBox_01.currentText()
        ju   = self.sj_sodb_comboBox_02.currentText()
        su   = self.sj_sodb_comboBox_03.currentText()
        bf   = 1 if self.sj_sodb_checkBox_27.isChecked() else 0
        bc1  = 1 if self.sj_sodb_checkBox_17.isChecked() else 0
        bc2  = 1 if self.sj_sodb_checkBox_18.isChecked() else 0
        bc3  = 1 if self.sj_sodb_checkBox_19.isChecked() else 0
        bc3c = self.sj_sodb_lineEdit_04.text()
        bb1  = 1 if self.sj_sodb_checkBox_20.isChecked() else 0
        bb2  = 1 if self.sj_sodb_checkBox_21.isChecked() else 0
        bb2c = self.sj_sodb_lineEdit_05.text()
        bb3  = 1 if self.sj_sodb_checkBox_22.isChecked() else 0
        bb3c = self.sj_sodb_lineEdit_06.text()
        bb4  = 1 if self.sj_sodb_checkBox_23.isChecked() else 0
        bb4c = self.sj_sodb_lineEdit_07.text()
        bb5  = 1 if self.sj_sodb_checkBox_24.isChecked() else 0
        bb5s = self.sj_sodb_lineEdit_08.text()
        bb5e = self.sj_sodb_lineEdit_09.text()
        bb6  = 1 if self.sj_sodb_checkBox_25.isChecked() else 0
        bb6s = self.sj_sodb_lineEdit_10.text()
        bb7  = 1 if self.sj_sodb_checkBox_26.isChecked() else 0
        bb7s = self.sj_sodb_lineEdit_11.text()
        bb8  = self.sj_sodb_lineEdit_12.text()
        bb8c = self.sj_sodb_comboBox_04.currentText()
        bb8h = self.sj_sodb_comboBox_05.currentText()

        if '' in (od, dc, ds2c, ds3c, ju, su, bc3c, bb2c, bb3c, bb4c, bb5s, bb5e, bb6s, bb8):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        elif ds == 0:
            QMessageBox.critical(self, '오류 알림', '분할매수방법이 선택되지 않았습니다.\n')
        elif 1 not in (ds1, ds2, ds3):
            QMessageBox.critical(self, '오류 알림', '추가매수방법이 선택되지 않았습니다.\n')
        else:
            dc, ds2c, ds3c, ju, su, bc3c, bb2c, bb3c, bb4c, bb5s, bb5e, bb6s, bb7s, bb8, bb8c, bb8h = \
                int(dc), float(ds2c), float(ds3c), int(ju), int(su), int(bc3c), int(bb2c), int(bb3c), int(bb4c), \
                int(bb5s), int(bb5e), int(bb6s), int(bb7s), int(bb8), int(bb8c), int(bb8h)
            if dc < 0 or ds2c < 0 or ds3c < 0 or su < 0 or bc3c < 0 or bb2c < 0 or bb3c < 0 or bb4c < 0 or \
                    bb5s < 0 or bb5e < 0 or bb6s < 0 or bb7s < 0 or bb8 < 0 or bb8c < 0 or bb8h < 0:
                QMessageBox.critical(self, '오류 알림', '지정가 호가 외 모든 입력값은 양수여야합니다.\n')
                return
            if dc > 5:
                QMessageBox.critical(self, '오류 알림', '매수분할횟수는 5을 초과할 수 없습니다.\n')
                return
            if proc_query.is_alive():
                query = f"UPDATE stockbuyorder SET 주식매수주문구분 = '{od}', 주식매수분할횟수 = {dc}, 주식매수분할방법 = {ds}, 주식매수분할시그널 = {ds1}, " \
                        f"주식매수분할하방 = {ds2}, 주식매수분할상방 = {ds3}, 주식매수분할하방수익률 = {ds2c}, 주식매수분할상방수익률 = {ds3c}, " \
                        f"주식매수분할고정수익률 = {bf}, 주식매수지정가기준가격 = '{bp}', 주식매수지정가호가번호 = {ju}, 주식매수시장가잔량범위 = {su}, " \
                        f"주식매수취소관심이탈 = {bc1}, 주식매수취소매도시그널 = {bc2}, 주식매수취소시간 = {bc3}, 주식매수취소시간초 = {bc3c}, " \
                        f"주식매수금지블랙리스트 = {bb1}, 주식매수금지라운드피겨 = {bb2}, 주식매수금지라운드호가 = {bb2c}, 주식매수금지손절횟수 = {bb3}, " \
                        f"주식매수금지손절횟수값 = {bb3c}, 주식매수금지거래횟수 = {bb4}, 주식매수금지거래횟수값 = {bb4c}, 주식매수금지시간 = {bb5}, " \
                        f"주식매수금지시작시간 = {bb5s}, 주식매수금지종료시간 = {bb5e}, 주식매수금지간격 = {bb6}, 주식매수금지간격초 = {bb6s}, " \
                        f"주식매수금지손절간격 = {bb7}, 주식매수금지손절간격초 = {bb7s}, 주식매수정정횟수 = {bb8}, 주식매수정정호가차이 = {bb8c}, " \
                        f"주식매수정정호가 = {bb8h}"
                queryQ.put(('설정디비', query))
            QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

            self.dict_set['주식매수주문구분']      = od
            self.dict_set['주식매수분할횟수']      = dc
            self.dict_set['주식매수분할방법']      = ds
            self.dict_set['주식매수분할시그널']    = ds1
            self.dict_set['주식매수분할하방']      = ds2
            self.dict_set['주식매수분할상방']      = ds3
            self.dict_set['주식매수분할하방수익률'] = ds2c
            self.dict_set['주식매수분할상방수익률'] = ds3c
            self.dict_set['주식매수분할고정수익률'] = bf
            self.dict_set['주식매수지정가기준가격'] = bp
            self.dict_set['주식매수지정가호가번호'] = ju
            self.dict_set['주식매수시장가잔량범위'] = su
            self.dict_set['주식매수취소관심이탈']   = bc1
            self.dict_set['주식매수취소매도시그널'] = bc2
            self.dict_set['주식매수취소시간']      = bc3
            self.dict_set['주식매수취소시간초']    = bc3c
            self.dict_set['주식매수금지블랙리스트'] = bb1
            self.dict_set['주식매수금지라운드피겨'] = bb2
            self.dict_set['주식매수금지라운드호가'] = bb2c
            self.dict_set['주식매수금지손절횟수']   = bb3
            self.dict_set['주식매수금지손절횟수값'] = bb3c
            self.dict_set['주식매수금지거래횟수']   = bb4
            self.dict_set['주식매수금지거래횟수값'] = bb4c
            self.dict_set['주식매수금지시간']      = bb5
            self.dict_set['주식매수금지시작시간']   = bb5s
            self.dict_set['주식매수금지종료시간']   = bb5e
            self.dict_set['주식매수금지간격']      = bb6
            self.dict_set['주식매수금지간격초']    = bb6s
            self.dict_set['주식매수금지손절간격']   = bb7
            self.dict_set['주식매수금지손절간격초'] = bb7s
            self.dict_set['주식매수정정횟수']      = bb8
            self.dict_set['주식매수정정호가차이']   = bb8c
            self.dict_set['주식매수정정호가']      = bb8h
            self.UpdateDictSet()

    def sjButtonClicked_25(self):
        od = ''
        if self.sj_sods_checkBox_01.isChecked(): od = '시장가'
        if self.sj_sods_checkBox_02.isChecked(): od = '지정가'
        if self.sj_sods_checkBox_03.isChecked(): od = '최유리지정가'
        if self.sj_sods_checkBox_04.isChecked(): od = '최우선지정가'
        if self.sj_sods_checkBox_05.isChecked(): od = '지정가IOC'
        if self.sj_sods_checkBox_06.isChecked(): od = '시장가IOC'
        if self.sj_sods_checkBox_07.isChecked(): od = '최유리IOC'
        if self.sj_sods_checkBox_08.isChecked(): od = '지정가FOK'
        if self.sj_sods_checkBox_09.isChecked(): od = '시장가FOK'
        if self.sj_sods_checkBox_10.isChecked(): od = '최유리FOK'
        dc = self.sj_sods_lineEdit_01.text()
        ds = 0
        if self.sj_sods_checkBox_11.isChecked(): ds = 1
        if self.sj_sods_checkBox_12.isChecked(): ds = 2
        if self.sj_sods_checkBox_13.isChecked(): ds = 3
        ds1  = 1 if self.sj_sods_checkBox_14.isChecked() else 0
        ds2  = 1 if self.sj_sods_checkBox_15.isChecked() else 0
        ds3  = 1 if self.sj_sods_checkBox_16.isChecked() else 0
        ds2c = self.sj_sods_lineEdit_02.text()
        ds3c = self.sj_sods_lineEdit_03.text()
        bp   = self.sj_sods_comboBox_01.currentText()
        ju   = self.sj_sods_comboBox_02.currentText()
        su   = self.sj_sods_comboBox_03.currentText()
        bc1  = 1 if self.sj_sods_checkBox_17.isChecked() else 0
        bc2  = 1 if self.sj_sods_checkBox_18.isChecked() else 0
        bc3  = 1 if self.sj_sods_checkBox_19.isChecked() else 0
        bc3c = self.sj_sods_lineEdit_04.text()
        bb0  = 1 if self.sj_sods_checkBox_20.isChecked() else 0
        bb0c = self.sj_sods_lineEdit_05.text()
        bb6  = 1 if self.sj_sods_checkBox_21.isChecked() else 0
        bb6c = self.sj_sods_lineEdit_06.text()
        bb1  = 1 if self.sj_sods_checkBox_22.isChecked() else 0
        bb1c = self.sj_sods_lineEdit_07.text()
        bb2  = 1 if self.sj_sods_checkBox_23.isChecked() else 0
        bb2c = self.sj_sods_lineEdit_08.text()
        bb3  = 1 if self.sj_sods_checkBox_24.isChecked() else 0
        bb3s = self.sj_sods_lineEdit_09.text()
        bb3e = self.sj_sods_lineEdit_10.text()
        bb4  = 1 if self.sj_sods_checkBox_25.isChecked() else 0
        bb4s = self.sj_sods_lineEdit_11.text()
        bb5  = self.sj_sods_lineEdit_12.text()
        bb5c = self.sj_sods_comboBox_04.currentText()
        bb5h = self.sj_sods_comboBox_05.currentText()

        if '' in (od, dc, ds2c, ds3c, ju, su, bc3c, bb0c, bb1c, bb2c, bb3s, bb3e, bb4s, bb5, bb6c):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        elif ds == 0:
            QMessageBox.critical(self, '오류 알림', '분할매도방법이 선택되지 않았습니다.\n')
        elif 1 not in (ds1, ds2, ds3):
            QMessageBox.critical(self, '오류 알림', '추가매도방법이 선택되지 않았습니다.\n')
        else:
            dc, ds2c, ds3c, ju, su, bc3c, bb0c, bb1c, bb2c, bb3s, bb3e, bb4s, bb5, bb5c, bb5h, bb6c = \
                int(dc), float(ds2c), float(ds3c), int(ju), int(su), int(bc3c), float(bb0c), int(bb1c), int(bb2c), \
                int(bb3s), int(bb3e), int(bb4s), int(bb5), int(bb5c), int(bb5h), int(bb6c)
            if dc < 0 or ds2c < 0 or ds3c < 0 or bc3c < 0 or bb0c < 0 or bb1c < 0 or bb2c < 0 or bb3s < 0 or \
                    bb3e < 0 or bb4s < 0 or bb5 < 0 or bb5c < 0 or bb5h < 0 or bb6c < 0:
                QMessageBox.critical(self, '오류 알림', '모든 값은 양수로 입력하십시오.\n')
                return
            if dc > 5:
                QMessageBox.critical(self, '오류 알림', '매도분할횟수는 5을 초과할 수 없습니다.\n')
                return
            if bb1c > 4:
                QMessageBox.critical(self, '오류 알림', '매도금지 매수횟수는 5미만으로 입력하십시오.\n')
                return
            if proc_query.is_alive():
                query = f"UPDATE stocksellorder SET 주식매도주문구분 = '{od}', 주식매도분할횟수 = {dc}, 주식매도분할방법 = {ds}, " \
                        f"주식매도분할시그널 = {ds1}, 주식매도분할하방 = {ds2}, 주식매도분할상방 = {ds3}, 주식매도분할하방수익률 = {ds2c}, " \
                        f"주식매도분할상방수익률 = {ds3c}, 주식매도지정가기준가격 = '{bp}', 주식매도지정가호가번호 = {ju}, 주식매도시장가잔량범위 = {su}, " \
                        f"주식매도취소관심진입 = {bc1}, 주식매도취소매수시그널 = {bc2}, 주식매도취소시간 = {bc3}, 주식매도취소시간초 = {bc3c}, " \
                        f"주식매도손절수익률청산 = {bb0}, 주식매도손절수익률 = {bb0c}, 주식매도손절수익금청산 = {bb6}, 주식매도손절수익금 = {bb6c}, " \
                        f"주식매도금지매수횟수 = {bb1}, 주식매도금지매수횟수값 = {bb1c}, 주식매도금지라운드피겨 = {bb2}, 주식매도금지라운드호가 = {bb2c}, " \
                        f"주식매도금지시간 = {bb3}, 주식매도금지시작시간 = {bb3s}, 주식매도금지종료시간 = {bb3e}, 주식매도금지간격 = {bb4}, " \
                        f"주식매도금지간격초 = {bb4s}, 주식매도정정횟수 = {bb5}, 주식매도정정호가차이 = {bb5c}, 주식매도정정호가 = {bb5h}"
                queryQ.put(('설정디비', query))
            QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

            self.dict_set['주식매도주문구분']      = od
            self.dict_set['주식매도분할횟수']      = dc
            self.dict_set['주식매도분할방법']      = ds
            self.dict_set['주식매도분할시그널']    = ds1
            self.dict_set['주식매도분할하방']      = ds2
            self.dict_set['주식매도분할상방']      = ds3
            self.dict_set['주식매도분할하방수익률'] = ds2c
            self.dict_set['주식매도분할상방수익률'] = ds3c
            self.dict_set['주식매도지정가기준가격'] = bp
            self.dict_set['주식매도지정가호가번호'] = ju
            self.dict_set['주식매도시장가잔량범위'] = su
            self.dict_set['주식매도취소관심진입']   = bc1
            self.dict_set['주식매도취소매수시그널'] = bc2
            self.dict_set['주식매도취소시간']      = bc3
            self.dict_set['주식매도취소시간초']    = bc3c
            self.dict_set['주식매도손절수익률청산'] = bb0
            self.dict_set['주식매도손절수익률']    = bb0c
            self.dict_set['주식매도손절수익금청산'] = bb6
            self.dict_set['주식매도손절수익금']    = bb6c
            self.dict_set['주식매도금지매수횟수']   = bb1
            self.dict_set['주식매도금지매수횟수값'] = bb1c
            self.dict_set['주식매도금지라운드피겨'] = bb2
            self.dict_set['주식매도금지라운드호가'] = bb2c
            self.dict_set['주식매도금지시간']      = bb3
            self.dict_set['주식매도금지시작시간']   = bb3s
            self.dict_set['주식매도금지종료시간']   = bb3e
            self.dict_set['주식매도금지간격']      = bb4
            self.dict_set['주식매도금지간격초']    = bb4s
            self.dict_set['주식매도정정횟수']      = bb5
            self.dict_set['주식매도정정호가차이']   = bb5c
            self.dict_set['주식매도정정호가']      = bb5h
            self.UpdateDictSet()

    def sjButtonClicked_26(self):
        od = ''
        if self.sj_codb_checkBox_01.isChecked(): od = '시장가'
        if self.sj_codb_checkBox_02.isChecked(): od = '지정가'
        if self.sj_codb_checkBox_19.isChecked(): od = '지정가IOC'
        if self.sj_codb_checkBox_20.isChecked(): od = '지정가FOK'
        dc = self.sj_codb_lineEdit_01.text()
        ds = 0
        if self.sj_codb_checkBox_03.isChecked(): ds = 1
        if self.sj_codb_checkBox_04.isChecked(): ds = 2
        if self.sj_codb_checkBox_05.isChecked(): ds = 3
        ds1  = 1 if self.sj_codb_checkBox_06.isChecked() else 0
        ds2  = 1 if self.sj_codb_checkBox_07.isChecked() else 0
        ds3  = 1 if self.sj_codb_checkBox_08.isChecked() else 0
        ds2c = self.sj_codb_lineEdit_02.text()
        ds3c = self.sj_codb_lineEdit_03.text()
        bp   = self.sj_codb_comboBox_01.currentText()
        ju   = self.sj_codb_comboBox_02.currentText()
        su   = self.sj_codb_comboBox_03.currentText()
        bf   = 1 if self.sj_codb_checkBox_27.isChecked() else 0
        bc1  = 1 if self.sj_codb_checkBox_09.isChecked() else 0
        bc2  = 1 if self.sj_codb_checkBox_10.isChecked() else 0
        bc3  = 1 if self.sj_codb_checkBox_11.isChecked() else 0
        bc3c = self.sj_codb_lineEdit_04.text()
        bb1  = 1 if self.sj_codb_checkBox_12.isChecked() else 0
        bb2  = 1 if self.sj_codb_checkBox_13.isChecked() else 0
        bb3  = 1 if self.sj_codb_checkBox_14.isChecked() else 0
        bb3c = self.sj_codb_lineEdit_05.text()
        bb4  = 1 if self.sj_codb_checkBox_15.isChecked() else 0
        bb4c = self.sj_codb_lineEdit_06.text()
        bb5  = 1 if self.sj_codb_checkBox_16.isChecked() else 0
        bb5s = self.sj_codb_lineEdit_07.text()
        bb5e = self.sj_codb_lineEdit_08.text()
        bb6  = 1 if self.sj_codb_checkBox_17.isChecked() else 0
        bb6s = self.sj_codb_lineEdit_09.text()
        bb7  = 1 if self.sj_codb_checkBox_18.isChecked() else 0
        bb7s = self.sj_codb_lineEdit_10.text()
        bb8  = self.sj_codb_lineEdit_11.text()
        bb8c = self.sj_codb_comboBox_04.currentText()
        bb8h = self.sj_codb_comboBox_05.currentText()

        if '' in (od, dc, ds2c, ds3c, ju, su, bc3c, bb3c, bb4c, bb5s, bb5e, bb6s, bb7s, bb8):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        elif ds == 0:
            QMessageBox.critical(self, '오류 알림', '분할매수방법이 선택되지 않았습니다.\n')
        elif 1 not in (ds1, ds2, ds3):
            QMessageBox.critical(self, '오류 알림', '추가매수방법이 선택되지 않았습니다.\n')
        else:
            dc, ds2c, ds3c, ju, su, bc3c, bb3c, bb4c, bb5s, bb5e, bb6s, bb7s, bb8, bb8c, bb8h = \
                int(dc), float(ds2c), float(ds3c), int(ju), int(su), int(bc3c), int(bb3c), int(bb4c), int(bb5s), \
                int(bb5e), int(bb6s), int(bb7s), int(bb8), int(bb8c), int(bb8h)
            if dc < 0 or ds2c < 0 or ds3c < 0 or su < 0 or bc3c < 0 or bb3c < 0 or bb4c < 0 or \
                    bb5s < 0 or bb5e < 0 or bb6s < 0 or bb7s < 0:
                QMessageBox.critical(self, '오류 알림', '지정가 호가 외 모든 입력값은 양수여야합니다.\n')
                return
            if dc > 5:
                QMessageBox.critical(self, '오류 알림', '매수분할횟수는 5를 초과할 수 없습니다.\n')
                return
            if proc_query.is_alive():
                query = f"UPDATE coinbuyorder SET 코인매수주문구분 = '{od}', 코인매수분할횟수 = {dc}, 코인매수분할방법 = {ds}, 코인매수분할시그널 = {ds1}, " \
                        f"코인매수분할하방 = {ds2}, 코인매수분할상방 = {ds3}, 코인매수분할하방수익률 = {ds2c}, 코인매수분할상방수익률 = {ds3c}, " \
                        f"코인매수분할고정수익률 = {bf}, 코인매수지정가기준가격 = '{bp}', 코인매수지정가호가번호 = {ju}, 코인매수시장가잔량범위 = {su}, " \
                        f"코인매수취소관심이탈 = {bc1}, 코인매수취소매도시그널 = {bc2}, 코인매수취소시간 = {bc3}, 코인매수취소시간초 = {bc3c}, " \
                        f"코인매수금지블랙리스트 = {bb1}, 코인매수금지200원이하 = {bb2}, 코인매수금지손절횟수 = {bb3}, 코인매수금지손절횟수값 = {bb3c}, " \
                        f"코인매수금지거래횟수 = {bb4}, 코인매수금지거래횟수값 = {bb4c}, 코인매수금지시간 = {bb5}, 코인매수금지시작시간 = {bb5s}, " \
                        f"코인매수금지종료시간 = {bb5e}, 코인매수금지간격 = {bb6}, 코인매수금지간격초 = {bb6s}, 코인매수금지손절간격 = {bb7}, " \
                        f"코인매수금지손절간격초 = {bb7s}, 코인매수정정횟수 = {bb8}, 코인매수정정호가차이 = {bb8c}, 코인매수정정호가 = {bb8h}"
                queryQ.put(('설정디비', query))
            QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

            self.dict_set['코인매수주문구분']      = od
            self.dict_set['코인매수분할횟수']      = dc
            self.dict_set['코인매수분할방법']      = ds
            self.dict_set['코인매수분할시그널']    = ds1
            self.dict_set['코인매수분할하방']      = ds2
            self.dict_set['코인매수분할상방']      = ds3
            self.dict_set['코인매수분할하방수익률'] = ds2c
            self.dict_set['코인매수분할상방수익률'] = ds3c
            self.dict_set['코인매수분할고정수익률'] = bf
            self.dict_set['코인매수지정가기준가격'] = bp
            self.dict_set['코인매수지정가호가번호'] = ju
            self.dict_set['코인매수시장가잔량범위'] = su
            self.dict_set['코인매수취소관심이탈']   = bc1
            self.dict_set['코인매수취소매도시그널'] = bc2
            self.dict_set['코인매수취소시간']      = bc3
            self.dict_set['코인매수취소시간초']    = bc3c
            self.dict_set['코인매수금지블랙리스트'] = bb1
            self.dict_set['코인매수금지200원이하'] = bb2
            self.dict_set['코인매수금지손절횟수']   = bb3
            self.dict_set['코인매수금지손절횟수값'] = bb3c
            self.dict_set['코인매수금지거래횟수']   = bb4
            self.dict_set['코인매수금지거래횟수값'] = bb4c
            self.dict_set['코인매수금지시간']      = bb5
            self.dict_set['코인매수금지시작시간']   = bb5s
            self.dict_set['코인매수금지종료시간']   = bb5e
            self.dict_set['코인매수금지간격']      = bb6
            self.dict_set['코인매수금지간격초']     = bb6s
            self.dict_set['코인매수금지손절간격']   = bb7
            self.dict_set['코인매수금지손절간격초'] = bb7s
            self.dict_set['코인매수정정횟수']      = bb8
            self.dict_set['코인매수정정호가차이']   = bb8c
            self.dict_set['코인매수정정호가']      = bb8h
            self.UpdateDictSet()

    def sjButtonClicked_27(self):
        od = ''
        if self.sj_cods_checkBox_01.isChecked(): od = '시장가'
        if self.sj_cods_checkBox_02.isChecked(): od = '지정가'
        if self.sj_cods_checkBox_19.isChecked(): od = '시장가IOC'
        if self.sj_cods_checkBox_20.isChecked(): od = '지정가FOK'
        dc = self.sj_cods_lineEdit_01.text()
        ds = 0
        if self.sj_cods_checkBox_03.isChecked(): ds = 1
        if self.sj_cods_checkBox_04.isChecked(): ds = 2
        if self.sj_cods_checkBox_05.isChecked(): ds = 3
        ds1  = 1 if self.sj_cods_checkBox_06.isChecked() else 0
        ds2  = 1 if self.sj_cods_checkBox_07.isChecked() else 0
        ds3  = 1 if self.sj_cods_checkBox_08.isChecked() else 0
        ds2c = self.sj_cods_lineEdit_02.text()
        ds3c = self.sj_cods_lineEdit_03.text()
        bp   = self.sj_cods_comboBox_01.currentText()
        ju   = self.sj_cods_comboBox_02.currentText()
        su   = self.sj_cods_comboBox_03.currentText()
        bc1  = 1 if self.sj_cods_checkBox_09.isChecked() else 0
        bc2  = 1 if self.sj_cods_checkBox_10.isChecked() else 0
        bc3  = 1 if self.sj_cods_checkBox_11.isChecked() else 0
        bc3c = self.sj_cods_lineEdit_04.text()
        bb0  = 1 if self.sj_cods_checkBox_12.isChecked() else 0
        bb0c = self.sj_cods_lineEdit_05.text()
        bb6  = 1 if self.sj_cods_checkBox_13.isChecked() else 0
        bb6c = self.sj_cods_lineEdit_06.text()
        bb1  = 1 if self.sj_cods_checkBox_14.isChecked() else 0
        bb1c = self.sj_cods_lineEdit_07.text()
        bb3  = 1 if self.sj_cods_checkBox_15.isChecked() else 0
        bb3s = self.sj_cods_lineEdit_08.text()
        bb3e = self.sj_cods_lineEdit_09.text()
        bb4  = 1 if self.sj_cods_checkBox_16.isChecked() else 0
        bb4s = self.sj_cods_lineEdit_10.text()
        bb5  = self.sj_cods_lineEdit_11.text()
        bb5c = self.sj_cods_comboBox_04.currentText()
        bb5h = self.sj_cods_comboBox_05.currentText()

        if '' in (od, dc, ds2c, ds3c, ju, su, bc3c, bb3s, bb3e, bb4s, bb5):
            QMessageBox.critical(self, '오류 알림', '일부 설정값이 입력되지 않았습니다.\n')
        elif ds == 0:
            QMessageBox.critical(self, '오류 알림', '분할매도방법이 선택되지 않았습니다.\n')
        elif 1 not in (ds1, ds2, ds3):
            QMessageBox.critical(self, '오류 알림', '추가매도방법이 선택되지 않았습니다.\n')
        else:
            dc, ds2c, ds3c, ju, su, bc3c, bb0c, bb1c, bb3s, bb3e, bb4s, bb5, bb5c, bb5h, bb6c = \
                int(dc), float(ds2c), float(ds3c), int(ju), int(su), int(bc3c), float(bb0c), int(bb1c), int(bb3s), \
                int(bb3e), int(bb4s), int(bb5), float(bb5c), int(bb5h), int(bb6c)
            if dc < 0 or ds2c < 0 or ds3c < 0 or bc3c < 0 or bb0c < 0 or bb1c < 0 or bb3s < 0 or bb3e < 0 or \
                    bb4s < 0 or bb5 < 0 or bb5c < 0 or bb5h < 0 or bb6c < 0:
                QMessageBox.critical(self, '오류 알림', '모든 값은 양수로 입력하십시오.\n')
                return
            if dc > 5:
                QMessageBox.critical(self, '오류 알림', '매도분할횟수는 5을 초과할 수 없습니다.\n')
                return
            if bb1c > 4:
                QMessageBox.critical(self, '오류 알림', '매도금지 매수횟수는 5미만으로 입력하십시오.\n')
                return
            if proc_query.is_alive():
                query = f"UPDATE coinsellorder SET 코인매도주문구분 = '{od}', 코인매도분할횟수 = {dc}, 코인매도분할방법 = {ds}, " \
                        f"코인매도분할시그널 = {ds1}, 코인매도분할하방 = {ds2}, 코인매도분할상방 = {ds3}, 코인매도분할하방수익률 = {ds2c}, " \
                        f"코인매도분할상방수익률 = {ds3c}, 코인매도지정가기준가격 = '{bp}', 코인매도지정가호가번호 = {ju}, 코인매도시장가잔량범위 = {su}, " \
                        f"코인매도취소관심진입 = {bc1}, 코인매도취소매수시그널 = {bc2}, 코인매도취소시간 = {bc3}, 코인매도취소시간초 = {bc3c}, " \
                        f"코인매도손절수익률청산 = {bb0}, 코인매도손절수익률 = {bb0c}, 코인매도손절수익금청산 = {bb6}, 코인매도손절수익금 = {bb6c}, " \
                        f"코인매도금지매수횟수 = {bb1}, 코인매도금지매수횟수값 = {bb1c}, 코인매도금지시간 = {bb3}, 코인매도금지시작시간 = {bb3s}, " \
                        f"코인매도금지종료시간 = {bb3e}, 코인매도금지간격 = {bb4}, 코인매도금지간격초 = {bb4s}, 코인매도정정횟수 = {bb5}, " \
                        f"코인매도정정호가차이 = {bb5c}, 코인매도정정호가 = {bb5h}"
                queryQ.put(('설정디비', query))
            QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

            self.dict_set['코인매도주문구분']      = od
            self.dict_set['코인매도분할횟수']      = dc
            self.dict_set['코인매도분할방법']      = ds
            self.dict_set['코인매도분할시그널']    = ds1
            self.dict_set['코인매도분할하방']      = ds2
            self.dict_set['코인매도분할상방']      = ds3
            self.dict_set['코인매도분할하방수익률'] = ds2c
            self.dict_set['코인매도분할상방수익률'] = ds3c
            self.dict_set['코인매도지정가기준가격'] = bp
            self.dict_set['코인매도지정가호가번호'] = ju
            self.dict_set['코인매도시장가잔량범위'] = su
            self.dict_set['코인매도취소관심진입']   = bc1
            self.dict_set['코인매도취소매수시그널'] = bc2
            self.dict_set['코인매도취소시간']      = bc3
            self.dict_set['코인매도취소시간초']    = bc3c
            self.dict_set['코인매도손절수익률청산'] = bb0
            self.dict_set['코인매도손절수익률']    = bb0c
            self.dict_set['코인매도손절수익금청산'] = bb6
            self.dict_set['코인매도손절수익금']    = bb6c
            self.dict_set['코인매도금지매수횟수']   = bb1
            self.dict_set['코인매도금지매수횟수값'] = bb1c
            self.dict_set['코인매도금지시간']      = bb3
            self.dict_set['코인매도금지시작시간']   = bb3s
            self.dict_set['코인매도금지종료시간']   = bb3e
            self.dict_set['코인매도금지간격']      = bb4
            self.dict_set['코인매도금지간격초']    = bb4s
            self.dict_set['코인매도정정횟수']      = bb5
            self.dict_set['코인매도정정호가차이']   = bb5c
            self.dict_set['코인매도정정호가']      = bb5h
            self.UpdateDictSet()

    def LoadSettings(self):
        self.sj_set_comBoxx_01.clear()
        file_list = os.listdir(DB_PATH)
        file_list = [x for x in file_list if 'setting_' in x]
        for file_name in file_list:
            name = file_name.replace('setting_', '').replace('.db', '')
            self.sj_set_comBoxx_01.addItem(name)

    def sjButtonClicked_28(self):
        self.LoadSettings()

    def sjButtonClicked_29(self):
        name = self.sj_set_comBoxx_01.currentText()
        if name == '':
            QMessageBox.critical(self, '오류 알림', '설정이름이 선택되지 않았습니다.\n')
            return
        origin_file = f'{DB_PATH}/setting_{name}.db'
        copy_file   = f'{DB_PATH}/setting.db'
        file_list   = os.listdir(DB_PATH)
        if f'setting_{name}.db' not in file_list:
            QMessageBox.critical(self, '오류 알림', '설정파일이 존재하지 않았습니다.\n')
            return
        queryQ.put(('설정변경', origin_file, copy_file))
        qtest_qwait(2)
        self.sjButtonClicked_01()
        self.sjButtonClicked_02()
        self.sjButtonClicked_03()
        self.sjButtonClicked_04()
        self.sjButtonClicked_05()
        self.sjButtonClicked_06()
        self.sjButtonClicked_07()
        self.sjButtonClicked_08()
        self.sjButtonClicked_20()
        self.sjButtonClicked_21()
        self.sjButtonClicked_22()
        self.sjButtonClicked_23()
        self.sjButtonClicked_09()
        self.sjButtonClicked_10()
        self.sjButtonClicked_11()
        self.sjButtonClicked_12()
        self.sjButtonClicked_13()
        self.sjButtonClicked_14()
        self.sjButtonClicked_15()
        self.sjButtonClicked_16()
        self.sjButtonClicked_24()
        self.sjButtonClicked_25()
        self.sjButtonClicked_26()
        self.sjButtonClicked_27()
        QMessageBox.information(self, '모든 설정 적용 완료', random.choice(famous_saying))

    def sjButtonClicked_30(self):
        name = self.sj_set_comBoxx_01.currentText()
        if name == '':
            QMessageBox.critical(self, '오류 알림', '설정이름이 선택되지 않았습니다.\n')
            return
        remove_file = f'{DB_PATH}/setting_{name}.db'
        os.remove(remove_file)
        self.LoadSettings()
        QMessageBox.information(self, '삭제 완료', random.choice(famous_saying))

    def sjButtonClicked_31(self):
        name = self.sj_set_liEditt_01.text()
        if name == '':
            QMessageBox.critical(self, '오류 알림', '설정이름이 입력되지 않았습니다.\n')
            return
        origin_file = f'{DB_PATH}/setting.db'
        copy_file   = f'{DB_PATH}/setting_{name}.db'
        shutil.copy(origin_file, copy_file)
        self.LoadSettings()
        QMessageBox.information(self, '저장 완료', random.choice(famous_saying))

    # =================================================================================================================

    def UpdateDictSet(self):
        wdzservQ.put(('manager', ('설정변경', self.dict_set)))
        if self.CoinReceiverProcessAlive(): creceivQ.put(('설정변경', self.dict_set))
        if self.CoinTraderProcessAlive():   ctraderQ.put(('설정변경', self.dict_set))
        if self.CoinStrategyProcessAlive(): cstgQ.put(('설정변경', self.dict_set))
        if proc_chart.is_alive():           chartQ.put(('설정변경', self.dict_set))
        if self.backtest_engine:
            for bpq in self.back_pques:
                bpq.put(('설정변경', self.dict_set))

    def ctButtonClicked_01(self):
        if not self.SimulatorProcessAlive():
            code = self.ct_lineEdittttt_04.text()
            gubun = '업비트' if 'KRW' in code else '바이낸스선물' if 'USDT' in code else '주식'
            if gubun == '업비트':
                if self.CoinStrategyProcessAlive():
                    QMessageBox.critical(self.dialog_test, '오류 알림', '코인 전략연산 프로세스가 실행중입니다.\n 트레이더을 작동 중지 설정하여 프로그램을 재구동하십시오.')
                    return
            elif gubun == '바이낸스선물':
                if self.CoinStrategyProcessAlive():
                    QMessageBox.critical(self.dialog_test, '오류 알림', '코인 전략연산 프로세스가 실행중입니다.\n 트레이더을 작동 중지 설정하여 프로그램을 재구동하십시오.')
                    return

            elif gubun == '업비트':
                self.proc_simulator_rv  = Process(target=ReceiverUpbit2, args=(qlist,), daemon=True)
                self.proc_simulator_td  = Process(target=TraderUpbit2, args=(qlist,), daemon=True)
                self.proc_strategy_coin = Process(target=StrategyUpbit, args=(qlist,), daemon=True)
            else:
                self.proc_simulator_rv  = Process(target=ReceiverBinanceFuture2, args=(qlist,), daemon=True)
                self.proc_simulator_td  = Process(target=TraderBinanceFuture2, args=(qlist,), daemon=True)
                self.proc_strategy_coin = Process(target=StrategyBinanceFuture, args=(qlist,), daemon=True)

            if gubun == '주식':
                wdzservQ.put(('manager', '시뮬레이터구동'))
                self.stock_simulator_alive = False
            else:
                self.proc_strategy_coin.start()
                self.proc_simulator_td.start()
                self.proc_simulator_rv.start()
            qtest_qwait(2)
            QMessageBox.information(self.dialog_test, '알림', '시뮬레이터 엔진 구동 완료')
        else:
            buttonReply = QMessageBox.question(
                self.dialog_test, '시뮬엔진', '이미 시뮬레이터 엔진이 구동중입니다.\n엔진을 재시작하시겠습니까?\n',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if buttonReply == QMessageBox.Yes:
                self.ctButtonClicked_02()
                self.ctButtonClicked_01()

    def ctButtonClicked_02(self):
        if self.SimulatorProcessAlive():
            if self.proc_simulator_rv is not None and self.proc_simulator_rv.is_alive():
                self.proc_simulator_rv.kill()
            if self.proc_simulator_td is not None and self.proc_simulator_td.is_alive():
                self.proc_simulator_td.kill()
            if self.CoinStrategyProcessAlive():
                self.proc_strategy_coin.kill()
            wdzservQ.put(('manager', '시뮬레이터종료'))
            self.stock_simulator_alive = False
        qtest_qwait(3)
        QMessageBox.information(self.dialog_test, '알림', '시뮬레이터 엔진 종료 완료')

    def ctButtonClicked_03(self):
        code = self.ct_lineEdittttt_04.text()
        if code == '':
            QMessageBox.critical(self.dialog_test, '오류 알림', '종목코드가 입력되지 않았습니다.\n')
            return
        if self.tt_lineEdittttt_01.text() == '':
            QMessageBox.critical(self.dialog_test, '오류 알림', '시작시간이 입력되지 않았습니다.\n')
            return
        if self.tt_lineEdittttt_02.text() == '':
            QMessageBox.critical(self.dialog_test, '오류 알림', '종료시간 입력되지 않았습니다.\n')
            return
        if not self.SimulatorProcessAlive():
            QMessageBox.critical(self.dialog_test, '오류 알림', '시뮬레이터용 엔진이 미실행중입니다.\n')
            return

        gubun      = '업비트' if 'KRW' in code else '바이낸스선물' if 'USDT' in code else '주식'
        date       = self.ct_dateEdittttt_01.date().toString('yyyyMMdd')
        start_time = int(self.tt_lineEdittttt_01.text())
        end_time   = int(self.tt_lineEdittttt_02.text())

        if gubun == '주식' and self.dict_set['주식분봉데이터']:
            wdzservQ.put(('simul_strategy', ('분봉재로딩', code, int(date + '090000'))))
        elif gubun != '주식' and self.dict_set['코인분봉데이터']:
            cstgQ.put(('분봉재로딩', code, int(date + '000000')))
        qtest_qwait(1)

        if gubun == '주식' and self.dict_set['주식일봉데이터']:
            wdzservQ.put(('simul_strategy', ('일봉재로딩', code, int(date))))
        elif gubun != '주식' and self.dict_set['코인일봉데이터']:
            wdzservQ.put(('simul_strategy', ('일봉재로딩', code, int(date + '000000'))))
        qtest_qwait(1)

        self.ChartClear()
        if gubun == '주식':
            wdzservQ.put(('simul_strategy', ('차트종목코드', code)))
            wdzservQ.put(('simul_strategy', ('관심목록', (code,))))
        else:
            cstgQ.put(code)
            cstgQ.put(('관심목록', (code,), (code,)))
        windowQ.put('복기모드시작')

        try:
            file_first_name = 'stock_tick_' if gubun == '주식' else 'coin_tick_'
            con = sqlite3.connect(f'{DB_PATH}/{file_first_name}{date}.db')
            df = pd.read_sql(f'SELECT * FROM "{code}" WHERE "index" LIKE "{date}%"', con)
            con.close()
        except:
            print('일자별 디비에 해당 종목의 데이터가 존재하지 않습니다.')
        else:
            df['구분시간'] = df['index'].apply(lambda x: int(str(x)[8:]))
            df = df[(df['구분시간'] >= start_time) & (df['구분시간'] <= end_time)]
            df.set_index('index', inplace=True)
            self.df_test = df.drop(columns=['구분시간'])
            self.ct_test = 0
            self.TickInput(code, gubun)

    def TickInput(self, code, gubun):
        try:
            dt = self.df_test.index[self.ct_test]
            data = tuple(self.df_test.iloc[self.ct_test])
            if gubun == '주식':
                wdzservQ.put(('trader', ('복기모드시간', str(dt))))
                wdzservQ.put(('receiver', (dt,) + data + (code,)))
            else:
                ctraderQ.put(('복기모드시간', str(dt)))
                creceivQ.put((dt,) + data + (code,))
            self.ct_test += 1
            speed = int(self.tt_comboBoxxxxx_01.currentText())
            if not self.test_pause:
                Timer(round(1 / speed, 2), self.TickInput, args=[code, gubun]).start()
        except:
            if gubun == '주식':
                wdzservQ.put(('simul_strategy', ('관심목록', ())))
                wdzservQ.put(('simul_strategy', '복기모드종료'))
            else:
                cstgQ.put(('관심목록', ()))
                cstgQ.put('복기모드종료')
            windowQ.put('복기모드종료')
            self.ct_test = 0
            self.test_pause = False
            qtest_qwait(2)
            self.ChartClear()

    def ChartClear(self):
        self.ctpg_tik_name         = None
        self.ctpg_tik_cline        = None
        self.ctpg_tik_hline        = None
        self.ctpg_tik_xticks       = None
        self.ctpg_tik_arry         = None
        self.ctpg_tik_legend       = {}
        self.ctpg_tik_item         = {}
        self.ctpg_tik_data         = {}
        self.ctpg_tik_factors      = []
        self.ctpg_tik_labels       = []

        self.ctpg_day_name         = None
        self.ctpg_day_index        = None
        self.ctpg_day_lastmoveavg  = None
        self.ctpg_day_lastcandle   = None
        self.ctpg_day_infiniteline = None
        self.ctpg_day_lastmoneybar = None
        self.ctpg_day_legend1      = None
        self.ctpg_day_legend2      = None
        self.ctpg_day_ymin         = 0
        self.ctpg_day_ymax         = 0

        self.ctpg_min_name         = None
        self.ctpg_min_index        = None
        self.ctpg_min_lastmoveavg  = None
        self.ctpg_min_lastcandle   = None
        self.ctpg_min_infiniteline = None
        self.ctpg_min_lastmoneybar = None
        self.ctpg_min_legend1      = None
        self.ctpg_min_legend2      = None
        self.ctpg_min_ymin         = 0
        self.ctpg_min_ymax         = 0

    # =================================================================================================================

    def ctButtonClicked_04(self):
        if not self.test_pause:
            self.test_pause = True
            self.tt_pushButtonnn_04.setText('재시작')
        else:
            self.test_pause = False
            self.tt_pushButtonnn_04.setText('일시정지')
            code = self.ct_lineEdittttt_04.text()
            gubun = '업비트' if 'KRW' in code else '바이낸스선물' if 'USDT' in code else '주식'
            self.TickInput(code, gubun)

    def ctButtonClicked_05(self):
        self.df_test = None

    def ctButtonClicked_06(self):
        self.dialog_test.close()

    # =================================================================================================================

    def hgButtonClicked_01(self, gubun):
        if not self.dialog_hoga.isVisible(): return
        index = self.hg_labellllllll_01.text()
        if index == '': return
        code  = self.ct_lineEdittttt_04.text()
        name  = self.ct_lineEdittttt_05.text()
        index = index.replace('-', '').replace(' ', '').replace(':', '')
        self.hogaQ.put(('이전호가정보요청' if gubun == '이전' else '다음호가정보요청', code, name, index))

    def hgButtonClicked_02(self, gubun):
        if not self.dialog_hoga.isVisible(): return
        cindex = self.hg_labellllllll_01.text()
        if cindex == '': return
        code   = self.ct_lineEdittttt_04.text()
        name   = self.ct_lineEdittttt_05.text()
        cindex = int(cindex.replace('-', '').replace(' ', '').replace(':', ''))
        index_list = self.buy_index if gubun == '매수' else self.sell_index
        if len(index_list) >= 1:
            if cindex < index_list[-1]:
                index_list = [x for x in index_list if cindex < x]
            index = index_list[0]
            if cindex != index:
                self.hogaQ.put(('매도수호가정보요청', code, name, str(index)))

    # =================================================================================================================

    def CalendarClicked(self, gubun):
        if gubun == 'S':
            table     = 's_tradelist'
            searchday = self.s_calendarWidgett.selectedDate().toString('yyyyMMdd')
        else:
            table     = 'c_tradelist' if self.dict_set['거래소'] == '업비트' else 'c_tradelist_future'
            searchday = self.c_calendarWidgett.selectedDate().toString('yyyyMMdd')
        con = sqlite3.connect(DB_TRADELIST)
        df1 = pd.read_sql(f"SELECT * FROM {table} WHERE 체결시간 LIKE '{searchday}%'", con).set_index('index')
        con.close()
        if len(df1) > 0:
            df1.sort_values(by=['체결시간'], ascending=True, inplace=True)
            if table == 'c_tradelist_future':
                df1 = df1[['체결시간', '종목명', '포지션', '매수금액', '매도금액', '주문수량', '수익률', '수익금']]
            else:
                df1 = df1[['체결시간', '종목명', '매수금액', '매도금액', '주문수량', '수익률', '수익금']]
            nbg, nsg = df1['매수금액'].sum(), df1['매도금액'].sum()
            sp = round((nsg / nbg - 1) * 100, 2)
            npg, nmg, nsig = df1[df1['수익금'] > 0]['수익금'].sum(), df1[df1['수익금'] < 0]['수익금'].sum(), df1['수익금'].sum()
            df2 = pd.DataFrame(columns=columns_dt)
            df2.loc[0] = searchday, nbg, nsg, npg, nmg, sp, nsig
        else:
            df1 = pd.DataFrame(columns=columns_dd)
            df2 = pd.DataFrame(columns=columns_dt)
        self.UpdateTablewidget((ui_num[f'{gubun}당일합계'], df2))
        self.UpdateTablewidget((ui_num[f'{gubun}당일상세'], df1))

    # =================================================================================================================

    def StockLiveProcessAlive(self):
        return self.proc_stomlive_stock is not None and self.proc_stomlive_stock.is_alive()

    def SimulatorProcessAlive(self):
        result = False
        if self.proc_simulator_rv is not None and self.proc_simulator_rv.is_alive() and self.proc_simulator_td is not None and self.proc_simulator_td.is_alive():
            result = True
        if self.stock_simulator_alive:
            result = True
        return result

    def CoinReceiverProcessAlive(self):
        return self.proc_receiver_coin is not None and self.proc_receiver_coin.is_alive()

    def CoinTraderProcessAlive(self):
        return self.proc_trader_coin is not None and self.proc_trader_coin.is_alive()

    def CoinStrategyProcessAlive(self):
        return self.proc_strategy_coin is not None and self.proc_strategy_coin.is_alive()

    def CoinKimpProcessAlive(self):
        return self.proc_coin_kimp is not None and self.proc_coin_kimp.is_alive()

    def BacktestProcessAlive(self):
        return (self.proc_backtester_bb is not None and self.proc_backtester_bb.is_alive()) or \
               (self.proc_backtester_bf is not None and self.proc_backtester_bf.is_alive()) or \
               (self.proc_backtester_o is not None and self.proc_backtester_o.is_alive()) or \
               (self.proc_backtester_ovc is not None and self.proc_backtester_ovc.is_alive()) or \
               (self.proc_backtester_ov is not None and self.proc_backtester_ov.is_alive()) or \
               (self.proc_backtester_ogvc is not None and self.proc_backtester_ogvc.is_alive()) or \
               (self.proc_backtester_ogv is not None and self.proc_backtester_ogv.is_alive()) or \
               (self.proc_backtester_og is not None and self.proc_backtester_og.is_alive()) or \
               (self.proc_backtester_ot is not None and self.proc_backtester_ot.is_alive()) or \
               (self.proc_backtester_ovct is not None and self.proc_backtester_ovct.is_alive()) or \
               (self.proc_backtester_ovt is not None and self.proc_backtester_ovt.is_alive()) or \
               (self.proc_backtester_ocvc is not None and self.proc_backtester_ocvc.is_alive()) or \
               (self.proc_backtester_ocv is not None and self.proc_backtester_ocv.is_alive()) or \
               (self.proc_backtester_oc is not None and self.proc_backtester_oc.is_alive()) or \
               (self.proc_backtester_or is not None and self.proc_backtester_or.is_alive()) or \
               (self.proc_backtester_orv is not None and self.proc_backtester_orv.is_alive()) or \
               (self.proc_backtester_orvc is not None and self.proc_backtester_orvc.is_alive())

    # =================================================================================================================

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.dialog_scheduler.focusWidget() == self.sd_dpushButtonn_01:
                return
            elif QApplication.keyboardModifiers() & Qt.AltModifier:
                if self.BacktestProcessAlive():
                    if self.main_btn == 2:
                        self.ssButtonClicked_06()
                    elif self.main_btn == 3:
                        self.csButtonClicked_06()
                else:
                    if self.main_btn == 2:
                        if self.svj_pushButton_01.isVisible():
                            self.svjButtonClicked_11()
                    elif self.main_btn == 3:
                        if self.cvj_pushButton_01.isVisible():
                            self.cvjButtonClicked_11()
            elif self.focusWidget() in (self.std_tableWidgettt, self.sgj_tableWidgettt, self.scj_tableWidgettt,
                                        self.ctd_tableWidgettt, self.cgj_tableWidgettt, self.ccj_tableWidgettt):
                stock = True
                if self.focusWidget() == self.std_tableWidgettt:
                    tableWidget = self.std_tableWidgettt
                elif self.focusWidget() == self.sgj_tableWidgettt:
                    tableWidget = self.sgj_tableWidgettt
                elif self.focusWidget() == self.scj_tableWidgettt:
                    tableWidget = self.scj_tableWidgettt
                elif self.focusWidget() == self.ctd_tableWidgettt:
                    stock = False
                    tableWidget = self.ctd_tableWidgettt
                elif self.focusWidget() == self.cgj_tableWidgettt:
                    stock = False
                    tableWidget = self.cgj_tableWidgettt
                else:
                    stock = False
                    tableWidget = self.ccj_tableWidgettt
                row  = tableWidget.currentIndex().row()
                col  = tableWidget.currentIndex().column()
                item = tableWidget.item(row, 0)
                if item is not None:
                    name       = item.text()
                    linetext   = self.ct_lineEdittttt_03.text()
                    tickcount  = int(linetext) if linetext != '' else 30
                    searchdate = strf_time('%Y%m%d') if stock else strf_time('%Y%m%d', timedelta_sec(-32400))
                    code       = self.dict_code[name] if name in self.dict_code.keys() else name
                    self.ct_lineEdittttt_04.setText(code)
                    self.ct_lineEdittttt_05.setText(name)
                    self.ShowDialog(name, tickcount, searchdate, col)
            elif self.focusWidget() in (self.sds_tableWidgettt, self.cds_tableWidgettt):
                if self.focusWidget() == self.sds_tableWidgettt:
                    tableWidget = self.sds_tableWidgettt
                    searchdate  = self.s_calendarWidgett.selectedDate().toString('yyyyMMdd')
                else:
                    tableWidget = self.cds_tableWidgettt
                    searchdate  = self.c_calendarWidgett.selectedDate().toString('yyyyMMdd')
                row  = tableWidget.currentIndex().row()
                item = tableWidget.item(row, 1)
                if item is not None:
                    name      = item.text()
                    linetext  = self.ct_lineEdittttt_03.text()
                    tickcount = int(linetext) if linetext != '' else 30
                    code      = self.dict_code[name] if name in self.dict_code.keys() else name
                    self.ct_lineEdittttt_04.setText(code)
                    self.ct_lineEdittttt_05.setText(name)
                    self.ct_dateEdittttt_01.setDate(QDate.fromString(searchdate, 'yyyyMMdd'))
                    self.ShowDialog(name, tickcount, searchdate, 4)
            elif self.focusWidget() in (self.sns_tableWidgettt, self.cns_tableWidgettt):
                if self.focusWidget() == self.sns_tableWidgettt:
                    tableWidget = self.sns_tableWidgettt
                    gubun = '주식'
                else:
                    tableWidget = self.cns_tableWidgettt
                    gubun = '코인'
                row  = tableWidget.currentIndex().row()
                item = tableWidget.item(row, 0)
                if item is not None:
                    date = item.text()
                    date = date.replace('.', '')
                    if gubun == '주식':
                        table_name = 's_tradelist'
                    elif self.dict_set['거래소'] == '업비트':
                        table_name = 'c_tradelist'
                    else:
                        table_name = 'c_tradelist_future'
                    con = sqlite3.connect(DB_TRADELIST)
                    df  = pd.read_sql(f"SELECT * FROM {table_name} WHERE 체결시간 LIKE '{date}%'", con)
                    con.close()
                    if len(date) == 6 and gubun == '코인':
                        df['구분용체결시간'] = df['체결시간'].apply(lambda x: x[:6])
                        df = df[df['구분용체결시간'] == date]
                    elif len(date) == 4 and gubun == '코인':
                        df['구분용체결시간'] = df['체결시간'].apply(lambda x: x[:4])
                        df = df[df['구분용체결시간'] == date]
                    df['index'] = df['index'].apply(lambda x: f'{x[:4]}-{x[4:6]}-{x[6:8]} {x[8:10]}:{x[10:12]}:{x[12:14]}')
                    df.set_index('index', inplace=True)
                    self.ShowDialogGraph(df)
            elif self.focusWidget() in (self.ss_tableWidget_01, self.cs_tableWidget_01):
                tableWidget = self.ss_tableWidget_01 if self.focusWidget() == self.ss_tableWidget_01 else self.cs_tableWidget_01
                row  = tableWidget.currentIndex().row()
                item = tableWidget.item(row, 0)
                if item is not None:
                    name       = item.text()
                    searchdate = tableWidget.item(row, 2).text()[:8]
                    buytime    = comma2int(tableWidget.item(row, 2).text())
                    selltime   = comma2int(tableWidget.item(row, 3).text())
                    buyprice   = comma2float(tableWidget.item(row, 5).text())
                    sellprice  = comma2float(tableWidget.item(row, 6).text())
                    detail     = [buytime, buyprice, selltime, sellprice]
                    buytimes   = tableWidget.item(row, 13).text()
                    coin = True if 'KRW' in name or 'USDT' in name else False
                    code = self.dict_code[name] if name in self.dict_code.keys() else name
                    self.ct_lineEdittttt_04.setText(code)
                    self.ct_lineEdittttt_05.setText(name)
                    self.ct_dateEdittttt_01.setDate(QDate.fromString(searchdate, 'yyyyMMdd'))
                    self.ShowDialogChart(False, coin, code, 30, searchdate, self.ct_lineEdittttt_01.text(), self.ct_lineEdittttt_02.text(), detail, buytimes)
        elif event.key() in (Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5, Qt.Key_6, Qt.Key_7, Qt.Key_8, Qt.Key_9, Qt.Key_0):
            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                if self.main_btn == 2:
                    if event.key() == Qt.Key_1:
                        self.svjButtonClicked_09()
                    elif event.key() == Qt.Key_2:
                        self.svjButtonClicked_05()
                    elif event.key() == Qt.Key_3:
                        self.svjButtonClicked_03()
                    elif event.key() == Qt.Key_4:
                        self.svjButtonClicked_01()
                    elif event.key() == Qt.Key_5:
                        self.svjButtonClicked_02()
                    elif event.key() == Qt.Key_6:
                        self.svjButtonClicked_04()
                    elif event.key() == Qt.Key_7:
                        self.svjButtonClicked_06()
                    elif event.key() == Qt.Key_8:
                        self.svjButtonClicked_10()
                    elif event.key() == Qt.Key_9:
                        self.svjButtonClicked_07()
                    elif event.key() == Qt.Key_0:
                        self.svjButtonClicked_08()
                elif self.main_btn == 3:
                    if event.key() == Qt.Key_1:
                        self.cvjButtonClicked_09()
                    elif event.key() == Qt.Key_2:
                        self.cvjButtonClicked_05()
                    elif event.key() == Qt.Key_3:
                        self.cvjButtonClicked_03()
                    elif event.key() == Qt.Key_4:
                        self.cvjButtonClicked_01()
                    elif event.key() == Qt.Key_5:
                        self.cvjButtonClicked_02()
                    elif event.key() == Qt.Key_6:
                        self.cvjButtonClicked_04()
                    elif event.key() == Qt.Key_7:
                        self.cvjButtonClicked_06()
                    elif event.key() == Qt.Key_8:
                        self.cvjButtonClicked_10()
                    elif event.key() == Qt.Key_9:
                        self.cvjButtonClicked_07()
                    elif event.key() == Qt.Key_0:
                        self.cvjButtonClicked_08()
        elif event.key() == Qt.Key_F4:
            if self.main_btn == 2:
                if self.svj_pushButton_01.isVisible():
                    self.ss_textEditttt_01.setFocus()
                    self.svjbButtonClicked_02()
                elif self.svc_pushButton_06.isVisible() or self.svc_pushButton_15.isVisible() or self.svc_pushButton_18.isVisible() or self.sva_pushButton_01.isVisible():
                    self.ss_textEditttt_03.setFocus()
                    self.svcButtonClicked_02()
                elif self.svo_pushButton_05.isVisible():
                    self.ss_textEditttt_07.setFocus()
                    self.svoButtonClicked_02()
            elif self.main_btn == 3:
                if self.cvj_pushButton_01.isVisible():
                    self.cs_textEditttt_01.setFocus()
                    self.cvjbButtonClicked_02()
                elif self.cvc_pushButton_06.isVisible() or self.cvc_pushButton_15.isVisible() or self.cvc_pushButton_18.isVisible() or self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_03.setFocus()
                    self.cvcButtonClicked_02()
                elif self.cvo_pushButton_05.isVisible():
                    self.cs_textEditttt_07.setFocus()
                    self.cvoButtonClicked_02()
        elif event.key() == Qt.Key_F8:
            if self.main_btn == 2:
                if self.svj_pushButton_01.isVisible():
                    self.ss_textEditttt_02.setFocus()
                    self.svjsButtonClicked_02()
                elif self.svc_pushButton_06.isVisible() or self.svc_pushButton_15.isVisible() or self.svc_pushButton_18.isVisible() or self.sva_pushButton_01.isVisible():
                    self.ss_textEditttt_04.setFocus()
                    self.svcButtonClicked_06()
                elif self.svo_pushButton_05.isVisible():
                    self.ss_textEditttt_08.setFocus()
                    self.svoButtonClicked_04()
            elif self.main_btn == 3:
                if self.cvj_pushButton_01.isVisible():
                    self.cs_textEditttt_02.setFocus()
                    self.cvjsButtonClicked_02()
                elif self.cvc_pushButton_06.isVisible() or self.cvc_pushButton_15.isVisible() or self.cvc_pushButton_18.isVisible() or self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_04.setFocus()
                    self.cvcButtonClicked_06()
                elif self.cvo_pushButton_05.isVisible():
                    self.cs_textEditttt_08.setFocus()
                    self.cvoButtonClicked_04()
        elif event.key() == Qt.Key_F12:
            if self.main_btn == 2:
                if self.svc_pushButton_06.isVisible():
                    self.ss_textEditttt_05.setFocus()
                    self.svcButtonClicked_04()
                elif self.sva_pushButton_03.isVisible():
                    self.ss_textEditttt_06.setFocus()
                    self.svaButtonClicked_02()
            elif self.main_btn == 3:
                if self.cvc_pushButton_06.isVisible():
                    self.cs_textEditttt_05.setFocus()
                    self.cvcButtonClicked_04()
                elif self.cva_pushButton_03.isVisible():
                    self.cs_textEditttt_06.setFocus()
                    self.cvaButtonClicked_02()

    def eventFilter(self, widget, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            if widget == self.ss_textEditttt_01:
                self.ss_textEditttt_01.insertPlainText('    ')
            elif widget == self.ss_textEditttt_02:
                self.ss_textEditttt_02.insertPlainText('    ')
            elif widget == self.ss_textEditttt_03:
                self.ss_textEditttt_03.insertPlainText('    ')
            elif widget == self.ss_textEditttt_04:
                self.ss_textEditttt_04.insertPlainText('    ')
            elif widget == self.cs_textEditttt_01:
                self.cs_textEditttt_01.insertPlainText('    ')
            elif widget == self.cs_textEditttt_02:
                self.cs_textEditttt_02.insertPlainText('    ')
            elif widget == self.cs_textEditttt_03:
                self.cs_textEditttt_03.insertPlainText('    ')
            elif widget == self.cs_textEditttt_04:
                self.cs_textEditttt_04.insertPlainText('    ')
            return True
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            if not self.svc_pushButton_24.isVisible():
                if widget in (self.ss_textEditttt_01, self.ss_textEditttt_03):
                    self.szooButtonClicked_01()
                elif widget in (self.ss_textEditttt_02, self.ss_textEditttt_04):
                    self.szooButtonClicked_02()
            if not self.cvc_pushButton_24.isVisible():
                if widget in (self.cs_textEditttt_01, self.cs_textEditttt_03):
                    self.czooButtonClicked_01()
                elif widget in (self.cs_textEditttt_02, self.cs_textEditttt_04):
                    self.czooButtonClicked_02()
            return True
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_F1:
            if self.main_btn == 2:
                if self.svj_pushButton_01.isVisible():
                    self.ss_textEditttt_01.setFocus()
                    self.svjbButtonClicked_01()
                elif self.svc_pushButton_06.isVisible() or self.sva_pushButton_03.isVisible():
                    self.ss_textEditttt_03.setFocus()
                    self.svcButtonClicked_01()
                elif self.svo_pushButton_05.isVisible():
                    self.ss_textEditttt_07.setFocus()
                    self.svoButtonClicked_01()
            elif self.main_btn == 3:
                if self.cvj_pushButton_01.isVisible():
                    self.cs_textEditttt_01.setFocus()
                    self.cvjbButtonClicked_01()
                elif self.cvc_pushButton_06.isVisible() or self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_04.setFocus()
                    self.cvcButtonClicked_01()
                elif self.cvo_pushButton_05.isVisible():
                    self.cs_textEditttt_08.setFocus()
                    self.cvoButtonClicked_01()
            return True
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_F2:
            if self.main_btn == 2:
                if self.svj_pushButton_01.isVisible():
                    self.ss_textEditttt_01.setFocus()
                    self.svjb_comboBoxx_01.showPopup()
                elif self.svc_pushButton_06.isVisible() or self.sva_pushButton_03.isVisible():
                    self.ss_textEditttt_03.setFocus()
                    self.svc_comboBoxxx_01.showPopup()
                elif self.svo_pushButton_05.isVisible():
                    self.ss_textEditttt_07.setFocus()
                    self.svo_comboBoxxx_01.showPopup()
            elif self.main_btn == 3:
                if self.cvj_pushButton_01.isVisible():
                    self.cs_textEditttt_01.setFocus()
                    self.cvjb_comboBoxx_01.showPopup()
                elif self.cvc_pushButton_06.isVisible() or self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_04.setFocus()
                    self.cvc_comboBoxxx_01.showPopup()
                elif self.cvo_pushButton_05.isVisible():
                    self.cs_textEditttt_08.setFocus()
                    self.cvo_comboBoxxx_01.showPopup()
            return True
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_F3:
            if self.main_btn == 2:
                if self.svj_pushButton_01.isVisible():
                    self.svjb_lineEditt_01.setFocus()
                elif self.svc_pushButton_06.isVisible() or self.sva_pushButton_03.isVisible():
                    self.svc_lineEdittt_01.setFocus()
                elif self.svo_pushButton_05.isVisible():
                    self.svo_lineEdittt_01.setFocus()
            elif self.main_btn == 3:
                if self.cvj_pushButton_01.isVisible():
                    self.cvjb_lineEditt_01.setFocus()
                elif self.cvc_pushButton_06.isVisible() or self.cva_pushButton_01.isVisible():
                    self.cvc_lineEdittt_01.setFocus()
                elif self.cvo_pushButton_05.isVisible():
                    self.cvo_lineEdittt_01.setFocus()
            return True
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_F5:
            if self.main_btn == 2:
                if self.svj_pushButton_01.isVisible():
                    self.ss_textEditttt_02.setFocus()
                    self.svjsButtonClicked_01()
                elif self.svc_pushButton_06.isVisible() or self.sva_pushButton_03.isVisible():
                    self.ss_textEditttt_04.setFocus()
                    self.svcButtonClicked_05()
                elif self.svo_pushButton_05.isVisible():
                    self.ss_textEditttt_05.setFocus()
                    self.svoButtonClicked_03()
            elif self.main_btn == 3:
                if self.cvj_pushButton_01.isVisible():
                    self.cs_textEditttt_02.setFocus()
                    self.cvjsButtonClicked_01()
                elif self.cvc_pushButton_06.isVisible() or self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_05.setFocus()
                    self.cvcButtonClicked_07()
                elif self.cvo_pushButton_05.isVisible():
                    self.cs_textEditttt_06.setFocus()
                    self.cvoButtonClicked_03()
            return True
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_F6:
            if self.main_btn == 2:
                if self.svj_pushButton_01.isVisible():
                    self.ss_textEditttt_02.setFocus()
                    self.svjs_comboBoxx_01.showPopup()
                elif self.svc_pushButton_06.isVisible() or self.sva_pushButton_03.isVisible():
                    self.ss_textEditttt_03.setFocus()
                    self.svc_comboBoxxx_08.showPopup()
                elif self.svo_pushButton_05.isVisible():
                    self.ss_textEditttt_04.setFocus()
                    self.svo_comboBoxxx_02.showPopup()
            elif self.main_btn == 3:
                if self.cvj_pushButton_01.isVisible():
                    self.cs_textEditttt_02.setFocus()
                    self.cvjs_comboBoxx_01.showPopup()
                elif self.cvc_pushButton_06.isVisible() or self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_04.setFocus()
                    self.cvc_comboBoxxx_08.showPopup()
                elif self.cvo_pushButton_05.isVisible():
                    self.cs_textEditttt_05.setFocus()
                    self.cvo_comboBoxxx_02.showPopup()
            return True
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_F7:
            if self.main_btn == 2:
                if self.svj_pushButton_01.isVisible():
                    self.svjs_lineEditt_01.setFocus()
                elif self.svc_pushButton_06.isVisible() or self.sva_pushButton_03.isVisible():
                    self.svc_lineEdittt_03.setFocus()
                elif self.svo_pushButton_05.isVisible():
                    self.svo_lineEdittt_02.setFocus()
            elif self.main_btn == 3:
                if self.cvj_pushButton_01.isVisible():
                    self.cvjs_lineEditt_01.setFocus()
                elif self.cvc_pushButton_06.isVisible() or self.cva_pushButton_01.isVisible():
                    self.cvc_lineEdittt_03.setFocus()
                elif self.cvo_pushButton_05.isVisible():
                    self.cvo_lineEdittt_02.setFocus()
            return True
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_F9:
            if self.main_btn == 2:
                if self.svc_pushButton_06.isVisible():
                    self.ss_textEditttt_05.setFocus()
                    self.svcButtonClicked_03()
                elif self.sva_pushButton_03.isVisible():
                    self.ss_textEditttt_06.setFocus()
                    self.svaButtonClicked_01()
            elif self.main_btn == 3:
                if self.cvc_pushButton_06.isVisible():
                    self.cs_textEditttt_06.setFocus()
                    self.cvcButtonClicked_03()
                elif self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_07.setFocus()
                    self.cvaButtonClicked_02()
            return True
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_F10:
            if self.main_btn == 2:
                if self.svc_pushButton_06.isVisible():
                    self.ss_textEditttt_05.setFocus()
                    self.svc_comboBoxxx_02.showPopup()
                elif self.sva_pushButton_03.isVisible():
                    self.ss_textEditttt_06.setFocus()
                    self.sva_comboBoxxx_01.showPopup()
            elif self.main_btn == 3:
                if self.cvc_pushButton_06.isVisible():
                    self.cs_textEditttt_06.setFocus()
                    self.cvc_comboBoxxx_02.showPopup()
                elif self.cva_pushButton_01.isVisible():
                    self.cs_textEditttt_07.setFocus()
                    self.cva_comboBoxxx_01.showPopup()
            return True
        elif event.type() == QEvent.KeyPress and event.key() == Qt.Key_F11:
            if self.main_btn == 2:
                if self.svc_pushButton_06.isVisible():
                    self.svc_lineEdittt_02.setFocus()
                elif self.sva_pushButton_03.isVisible():
                    self.sva_lineEdittt_01.setFocus()
            elif self.main_btn == 3:
                if self.cvc_pushButton_06.isVisible():
                    self.cvc_lineEdittt_02.setFocus()
                elif self.cva_pushButton_01.isVisible():
                    self.cva_lineEdittt_01.setFocus()
            return True
        else:
            return QMainWindow.eventFilter(self, widget, event)

    def closeEvent(self, a):
        buttonReply = QMessageBox.question(
            self, "프로그램 종료", "프로그램을 종료합니다.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if buttonReply == QMessageBox.Yes:
            self.ProcessKill()
            a.accept()
        else:
            a.ignore()

    # =================================================================================================================

    def ProcessKill(self):
        if self.dict_set['리시버프로파일링']:
            wdzservQ.put(('receiver', '프로파일링결과'))
            qtest_qwait(3)
        if self.dict_set['트레이더프로파일링']:
            wdzservQ.put(('trader', '프로파일링결과'))
            qtest_qwait(3)
        if self.dict_set['전략연산프로파일링']:
            wdzservQ.put(('strategy', '프로파일링결과'))
            qtest_qwait(3)

        wdzservQ.put(('manager', '통신종료'))
        factor_choice = ''
        for checkbox in self.factor_checkbox_list:
            factor_choice = f"{factor_choice}{'1' if checkbox.isChecked() else '0'};"
        query = f"UPDATE etc SET 팩터선택 = '{factor_choice[:-1]}'"
        queryQ.put(('설정디비', query))
        divid_mode      = self.be_comboBoxxxxx_01.currentText()
        optuna_sampler  = self.op_comboBoxxxx_01.currentText()
        optuna_fixvars  = self.op_lineEditttt_01.text()
        optuna_count    = int(self.op_lineEditttt_02.text())
        optuna_autostep = 1 if self.op_checkBoxxxx_01.isChecked() else 0
        query = f"UPDATE back SET 백테엔진분류방법 = '{divid_mode}', '옵튜나샘플러' = '{optuna_sampler}', '옵튜나고정변수' = '{optuna_fixvars}', '옵튜나실행횟수' = {optuna_count}, '옵튜나자동스탭' = {optuna_autostep}"
        queryQ.put(('설정디비', query))

        if self.dict_set['창위치기억']:
            geo_len   = len(self.dict_set['창위치']) if self.dict_set['창위치'] is not None else 0
            geometry  = f"{self.x()};{self.y()};"
            geometry += f"{self.dialog_chart.x()};{self.dialog_chart.y() - 31 if geo_len > 3 and self.dict_set['창위치'][3] + 31 == self.dialog_chart.y() else self.dialog_chart.y()};"
            geometry += f"{self.dialog_scheduler.x()};{self.dialog_scheduler.y() - 31 if geo_len > 5 and self.dict_set['창위치'][5] + 31 == self.dialog_scheduler.y() else self.dialog_scheduler.y()};"
            geometry += f"{self.dialog_jisu.x()};{self.dialog_jisu.y() - 31 if geo_len > 7 and self.dict_set['창위치'][7] + 31 == self.dialog_jisu.y() else self.dialog_jisu.y()};"
            geometry += f"{self.dialog_info.x()};{self.dialog_info.y() - 31 if geo_len > 9 and self.dict_set['창위치'][9] + 31 == self.dialog_info.y() else self.dialog_info.y()};"
            geometry += f"{self.dialog_web.x()};{self.dialog_web.y() - 31 if geo_len > 11 and self.dict_set['창위치'][11] + 31 == self.dialog_web.y() else self.dialog_web.y()};"
            geometry += f"{self.dialog_tree.x()};{self.dialog_tree.y() - 31 if geo_len > 13 and self.dict_set['창위치'][13] + 31 == self.dialog_tree.y() else self.dialog_tree.y()};"
            geometry += f"{self.dialog_chart_day.x()};{self.dialog_chart_day.y() - 31 if geo_len > 15 and self.dict_set['창위치'][15] + 31 == self.dialog_chart_day.y() else self.dialog_chart_day.y()};"
            geometry += f"{self.dialog_chart_min.x()};{self.dialog_chart_min.y() - 31 if geo_len > 17 and self.dict_set['창위치'][17] + 31 == self.dialog_chart_min.y() else self.dialog_chart_min.y()};"
            geometry += f"{self.dialog_kimp.x()};{self.dialog_kimp.y() - 31 if geo_len > 19 and self.dict_set['창위치'][19] + 31 == self.dialog_kimp.y() else self.dialog_kimp.y()};"
            geometry += f"{self.dialog_hoga.x()};{self.dialog_hoga.y() - 31 if geo_len > 21 and self.dict_set['창위치'][21] + 31 == self.dialog_hoga.y() else self.dialog_hoga.y()};"
            geometry += f"{self.dialog_backengine.x()};{self.dialog_backengine.y() - 31 if geo_len > 23 and self.dict_set['창위치'][23] + 31 == self.dialog_backengine.y() else self.dialog_backengine.y()};"
            geometry += f"{self.dialog_order.x()};{self.dialog_order.y() - 31 if geo_len > 25 and self.dict_set['창위치'][25] + 31 == self.dialog_order.y() else self.dialog_order.y()}"
            query = f"UPDATE etc SET 창위치 = '{geometry}'"
            queryQ.put(('설정디비', query))

        if self.writer.isRunning(): self.writer.terminate()
        if self.qtimer1.isActive(): self.qtimer1.stop()
        if self.qtimer2.isActive(): self.qtimer2.stop()
        if self.qtimer3.isActive(): self.qtimer3.stop()

        if self.dialog_chart.isVisible():     self.dialog_chart.close()
        if self.dialog_scheduler.isVisible(): self.dialog_scheduler.close()
        if self.dialog_jisu.isVisible():      self.dialog_jisu.close()
        if self.dialog_info.isVisible():      self.dialog_info.close()
        if self.dialog_web.isVisible():       self.dialog_web.close()
        if self.dialog_tree.isVisible():      self.dialog_tree.close()
        if self.dialog_chart_day.isVisible(): self.dialog_chart_day.close()
        if self.dialog_chart_min.isVisible(): self.dialog_chart_min.close()
        if self.dialog_graph.isVisible():     self.dialog_graph.close()
        if self.dialog_kimp.isVisible():      self.dialog_kimp.close()
        if self.StockLiveProcessAlive():      self.proc_stomlive_stock.kill()

        if self.CoinKimpProcessAlive():
            kimpQ.put('프로세스종료')
            qtest_qwait(3)
        if self.CoinReceiverProcessAlive():
            creceivQ.put('프로세스종료')
            qtest_qwait(3)
            self.proc_receiver_coin.kill()
        if self.CoinTraderProcessAlive():
            if self.dict_set['거래소'] == '바이낸스선물':
                ctraderQ.put('프로세스종료')
            self.proc_trader_coin.kill()
        if self.CoinStrategyProcessAlive():
            self.proc_strategy_coin.kill()

        if self.SimulatorProcessAlive():
            self.proc_simulator_rv.kill()
            self.proc_simulator_td.kill()
        if self.BacktestProcessAlive():
            self.BacktestProcessKill()

        if self.bact_procs:
            for proc in self.bact_procs:
                proc.kill()
        if self.back_procs:
            for proc in self.back_procs:
                proc.kill()
        if self.back_procs or self.bact_procs:
            qtest_qwait(3)

        sys.exit()


if __name__ == '__main__':
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)
    auto_run = 1 if len(sys.argv) > 1 and sys.argv[1] == 'stocklogin' else 0
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--blink-settings=forceDarkModeEnabled=true"
    subprocess.Popen('python64 ./utility/timesync.py')

    windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ, cstgQ, liveQ, totalQ, testQ, kimpQ, wdzservQ = \
        Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue(), Queue()
    qlist = [windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ, cstgQ, liveQ, kimpQ, wdzservQ]

    proc_tele  = Process(target=TelegramMsg, args=(qlist,), daemon=True)
    proc_webc  = Process(target=WebCrawling, args=(qlist,), daemon=True)
    proc_sound = Process(target=Sound, args=(qlist,), daemon=True)
    proc_query = Process(target=Query, args=(qlist,), daemon=True)
    proc_chart = Process(target=Chart, args=(qlist,), daemon=True)
    proc_hoga  = Process(target=Hoga, args=(qlist,), daemon=True)

    proc_tele.start()
    proc_webc.start()
    proc_sound.start()
    proc_query.start()
    proc_chart.start()
    proc_hoga.start()

    app = QApplication(sys.argv)
    app.setStyle('fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, color_bg_bc)
    palette.setColor(QPalette.Background, color_bg_bc)
    palette.setColor(QPalette.WindowText, color_fg_bc)
    palette.setColor(QPalette.Base, color_bg_bc)
    palette.setColor(QPalette.AlternateBase, color_bg_dk)
    palette.setColor(QPalette.Text, color_fg_bc)
    palette.setColor(QPalette.Button, color_bg_bc)
    palette.setColor(QPalette.ButtonText, color_fg_bc)
    palette.setColor(QPalette.Link, color_fg_bk)
    palette.setColor(QPalette.Highlight, color_fg_hl)
    palette.setColor(QPalette.HighlightedText, color_bg_bk)
    app.setPalette(palette)
    window = Window(auto_run)
    window.show()
    app.exec_()
