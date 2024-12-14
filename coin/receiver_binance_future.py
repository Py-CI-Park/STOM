import re
import zmq
import time
import sqlite3
import binance
import asyncio
import operator
import numpy as np
import pandas as pd
from threading import Thread, Timer
from multiprocessing import Process, Queue
from binance.enums import HistoricalKlinesType
from binance import AsyncClient, BinanceSocketManager
from utility.setting import ui_num, DICT_SET, DB_COIN_DAY, DB_COIN_MIN
from utility.static import now, strf_time, strp_time, timedelta_sec, from_timestamp, int_hms_utc


class ZmqServ(Thread):
    def __init__(self, zq):
        super().__init__()
        self.zq = zq
        zctx = zmq.Context()
        self.sock = zctx.socket(zmq.PUB)
        self.sock.bind(f'tcp://*:5779')

    def run(self):
        while True:
            msg, data = self.zq.get()
            self.sock.send_string(msg, zmq.SNDMORE)
            self.sock.send_pyobj(data)


class ReceiverBinanceFuture:
    def __init__(self, qlist):
        """
        windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ, creceivQ, ctraderQ,  cstgQ, liveQ, kimpQ, wdzservQ
           0        1       2      3       4      5      6      7       8         9         10     11    12      13
        """
        self.windowQ  = qlist[0]
        self.soundQ   = qlist[1]
        self.queryQ   = qlist[2]
        self.teleQ    = qlist[3]
        self.hogaQ    = qlist[5]
        self.creceivQ = qlist[8]
        self.ctraderQ = qlist[9]
        self.cstgQ    = qlist[10]
        self.dict_set = DICT_SET

        self.dict_bool = {
            '프로세스종료': False
        }
        self.dict_tick = {}
        self.dict_hgdt = {}
        self.dict_tddt = {}
        self.dict_tm5m = {}
        self.dict_arry = {}
        self.dict_mtop = {}
        self.dict_hgbs = {}
        self.dict_dlhp = {}

        curr_time = now()
        self.dict_time = {
            '티커리스트재조회': timedelta_sec(600),
            '거래대금순위기록': curr_time,
            '거래대금순위저장': curr_time,
            '저가대비고가등락율갱신': curr_time
        }

        self.list_gsjm1 = []
        self.list_gsjm2 = []
        self.list_jang  = []
        self.list_oder  = []
        self.list_prmt  = []

        self.int_logt  = int(strf_time('%Y%m%d%H%M', timedelta_sec(-32400)))
        self.int_jcct  = int(strf_time('%Y%m%d%H%M%S', timedelta_sec(-32400)))
        self.dt_mtct   = None
        self.hoga_code = None
        self.proc_webs = None
        self.codes     = None

        self.binance   = binance.Client()

        self.zq = Queue()
        if self.dict_set['리시버공유'] == 1:
            self.zmqserver = ZmqServ(self.zq)
            self.zmqserver.start()

        self.Start()

    def Start(self):
        text = '코인 리시버를 시작하였습니다.'
        if self.dict_set['코인알림소리']: self.soundQ.put(text)
        self.teleQ.put(text)
        self.windowQ.put([ui_num['C단순텍스트'], '시스템 명령 실행 알림 - 리시버 시작'])
        self.codes = self.GetTickers(first=True)
        if self.dict_set['코인일봉데이터다운']: self.DaydataDownload()
        wsq = Queue()
        while True:
            curr_time = now()
            inthmsutc = int_hms_utc()

            if self.proc_webs is None or not self.proc_webs.is_alive():
                self.WebSocketsStart(wsq)

            if not self.creceivQ.empty():
                data = self.creceivQ.get()
                if type(data) == list:
                    self.UpdateList(data)
                elif type(data) == dict:
                    self.dict_set = data
                elif type(data) == str:
                    if data == '프로세스종료':
                        self.ctraderQ.put('프로세스종료')
                        self.cstgQ.put('프로세스종료')
                        self.WebProcessKill()
                        break
                    else:
                        self.hoga_code = data

            if not wsq.empty():
                data = wsq.get()
                if data == 'ConnectionClosedError':
                    self.windowQ.put([ui_num['C단순텍스트'], '시스템 명령 오류 알림 - 웹소켓 연결 끊김으로 다시 연결합니다.'])
                    self.WebProcessKill()
                elif data[0] == 'trade':
                    try:
                        data = data[1]['data']
                        code = data['s']
                        c    = float(data['p'])
                        v    = float(data['q'])
                        m    = data['m']
                        dt   = int(strf_time('%Y%m%d%H%M%S', from_timestamp(int(data['T']) / 1000 - 32400)))
                    except Exception as e:
                        self.windowQ.put([ui_num['C단순텍스트'], f'시스템 명령 오류 알림 - 웹소켓 trade {e}'])
                    else:
                        self.UpdateTradeData(code, c, v, m, dt)
                elif data[0] == 'depth':
                    try:
                        data = data[1]['data']
                        code = data['s']
                        dt   = int(strf_time('%Y%m%d%H%M%S', from_timestamp(int(data['T']) / 1000 - 32400)))
                        hoga_seprice = [
                            float(data['a'][9][0]), float(data['a'][8][0]), float(data['a'][7][0]), float(data['a'][6][0]), float(data['a'][5][0]),
                            float(data['a'][4][0]), float(data['a'][3][0]), float(data['a'][2][0]), float(data['a'][1][0]), float(data['a'][0][0])
                        ]
                        hoga_buprice = [
                            float(data['b'][0][0]), float(data['b'][1][0]), float(data['b'][2][0]), float(data['b'][3][0]), float(data['b'][4][0]),
                            float(data['b'][5][0]), float(data['b'][6][0]), float(data['b'][7][0]), float(data['b'][8][0]), float(data['b'][9][0])
                        ]
                        hoga_samount = [
                            float(data['a'][9][1]), float(data['a'][8][1]), float(data['a'][7][1]), float(data['a'][6][1]), float(data['a'][5][1]),
                            float(data['a'][4][1]), float(data['a'][3][1]), float(data['a'][2][1]), float(data['a'][1][1]), float(data['a'][0][1])
                        ]
                        hoga_bamount = [
                            float(data['b'][0][1]), float(data['b'][1][1]), float(data['b'][2][1]), float(data['b'][3][1]), float(data['b'][4][1]),
                            float(data['b'][5][1]), float(data['b'][6][1]), float(data['b'][7][1]), float(data['b'][8][1]), float(data['b'][9][1])
                        ]
                        hoga_tamount = [
                            round(sum(hoga_samount), 8), round(sum(hoga_bamount), 8)
                        ]
                    except Exception as e:
                        self.windowQ.put([ui_num['C단순텍스트'], f'시스템 명령 오류 알림 - 웹소켓 depth {e}'])
                    else:
                        self.UpdateHogaData(dt, hoga_tamount, hoga_seprice, hoga_buprice, hoga_samount, hoga_bamount, code, curr_time)

            if curr_time > self.dict_time['거래대금순위기록']:
                self.UpdateMoneyTop()
                self.dict_time['거래대금순위기록'] = timedelta_sec(1)

            if curr_time > self.dict_time['거래대금순위저장']:
                self.MoneyTopSearch()
                df = pd.DataFrame(self.dict_mtop.values(), columns=['거래대금순위'], index=list(self.dict_mtop.keys()))
                self.queryQ.put(['코인디비', df, 'moneytop', 'append'])
                self.dict_mtop = {}
                self.dict_time['거래대금순위저장'] = timedelta_sec(10)

            if not self.dict_set['바이낸스선물고정레버리지'] and curr_time > self.dict_time['저가대비고가등락율갱신']:
                if len(self.dict_dlhp) > 0:
                    self.ctraderQ.put(['저가대비고가등락율', self.dict_dlhp])
                self.dict_time['저가대비고가등락율갱신'] = timedelta_sec(300)

            if self.dict_set['코인장초전략종료시간'] < inthmsutc < self.dict_set['코인장초전략종료시간'] + 10:
                if self.dict_set['코인장초프로세스종료'] and not self.dict_bool['프로세스종료']:
                    self.ReceiverProcKill()

            if self.dict_set['코인장중전략종료시간'] < inthmsutc < self.dict_set['코인장중전략종료시간'] + 10:
                if self.dict_set['코인장중프로세스종료'] and not self.dict_bool['프로세스종료']:
                    self.ReceiverProcKill()

            if curr_time > self.dict_time['티커리스트재조회']:
                codes = self.GetTickers()
                if len(codes) > len(self.codes):
                    self.codes = codes
                    self.ctraderQ.put('코인명갱신')
                    if self.dict_set['리시버공유'] == 1:
                        self.zq.put(['updatecodes', ''])
                    self.WebProcessKill()
                self.dict_time['티커리스트재조회'] = timedelta_sec(600)

            if self.creceivQ.empty() and wsq.empty():
                time.sleep(0.001)

        self.windowQ.put([ui_num['C단순텍스트'], '시스템 명령 실행 알림 - 리시버 종료'])
        time.sleep(1)

    def ReceiverProcKill(self):
        self.dict_bool['프로세스종료'] = True
        Timer(180, self.creceivQ.put, args=['프로세스종료']).start()

    def WebSocketsStart(self, wsq):
        self.proc_webs = Process(target=WebSocketManager, args=(self.codes, wsq), daemon=True)
        self.proc_webs.start()

    def WebProcessKill(self):
        if self.proc_webs.is_alive(): self.proc_webs.kill()
        time.sleep(3)

    def GetTickers(self, first=False):
        dict_tm5m = {}
        try:
            datas = self.binance.futures_ticker()
        except Exception as e:
            print(e)
        else:
            datas = [data for data in datas if re.search('USDT$', data['symbol']) is not None]
            ymd   = strf_time('%Y%m%d', timedelta_sec(-32400))
            for data in datas:
                code = data['symbol']
                if code not in self.dict_tick.keys():
                    c    = float(data['lastPrice'])
                    o    = float(data['openPrice'])
                    h    = float(data['highPrice'])
                    low  = float(data['lowPrice'])
                    per  = round(float(data['priceChangePercent']), 2)
                    dm   = float(data['quoteVolume'])
                    prec = round(c - float(data['priceChange']), 8)
                    self.dict_tick[code] = [c, o, h, low, per, dm, 0, 0, 0, 0, 0]
                    self.dict_tddt[code] = [ymd, prec]
                    self.dict_hgbs[code] = [0, 0]
                    dict_tm5m[code] = dm

        if first:
            self.list_prmt = [x for x, y in sorted(dict_tm5m.items(), key=operator.itemgetter(1), reverse=True)[:self.dict_set['코인순위선정']]]
            for code in self.list_prmt:
                self.InsertGsjmlist(code)
            self.list_gsjm1 = self.list_prmt[:-3]
            data1, data2 = self.list_gsjm1.copy(), self.list_gsjm2.copy()
            self.cstgQ.put(['관심목록', data1, data2])
            if self.dict_set['리시버공유'] == 1:
                self.zq.put(['focuscodes', [data1, data2]])

        return list(self.dict_tick.keys())

    def UpdateList(self, data):
        gubun, code_list = data
        if gubun == '잔고목록':
            self.list_jang = code_list
        elif gubun == '주문목록':
            self.list_oder = code_list

    def UpdateTradeData(self, code, c, v, m, dt):
        if dt != self.int_jcct and dt > self.int_jcct:
            self.int_jcct = dt

        ymd = str(dt)[:8]
        if ymd != self.dict_tddt[code][0]:
            self.dict_tddt[code] = [ymd, self.dict_tick[code][0]]
            prebids, preasks, pretbids, pretasks = 0, 0, 0, 0
            bids_ = v if not m else 0
            asks_ = 0 if not m else v
            bids  = round(prebids + bids_, 8)
            asks  = round(preasks + asks_, 8)
            tbids = round(pretbids + bids_, 8)
            tasks = round(pretasks + asks_, 8)
            try:
                ch = round(tbids / tasks * 100, 2)
            except:
                ch = 500.
            ch = 500. if ch > 500 else ch
            o, h, low = c, c, c
            dm = round(v * c, 2)
        else:
            prebids, preasks, pretbids, pretasks = self.dict_tick[code][7:]
            bids_ = v if not m else 0
            asks_ = 0 if not m else v
            bids  = round(prebids + bids_, 8)
            asks  = round(preasks + asks_, 8)
            tbids = round(pretbids + bids_, 8)
            tasks = round(pretasks + asks_, 8)
            try:
                ch = round(tbids / tasks * 100, 2)
            except:
                ch = 500.
            ch = 500. if ch > 500 else ch
            o, h, low = self.dict_tick[code][1:4]
            h   = c if c > h else h
            low = c if c < low else low
            dm  = round(self.dict_tick[code][5] + v * c, 2)

        per = round((c / self.dict_tddt[code][1] - 1) * 100, 2)
        self.dict_tick[code] = [c, o, h, low, per, dm, ch, bids, asks, tbids, tasks]
        self.dict_hgbs[code] = [0, c] if not m else [c, 0]

        dt_ = int(str(dt)[:13])
        if code not in self.dict_arry.keys():
            self.dict_arry[code] = np.array([[dt_, dm]])
        elif dt_ != self.dict_arry[code][-1, 0]:
            self.dict_arry[code] = np.r_[self.dict_arry[code], np.array([[dt_, dm]])]
            if len(self.dict_arry[code]) == self.dict_set['코인순위시간'] * 6:
                self.dict_tm5m[code] = round(dm - self.dict_arry[code][0, 1], 2)
                self.dict_arry[code] = np.delete(self.dict_arry[code], 0, 0)

        if code not in self.dict_dlhp.keys() or dt_ != self.dict_dlhp[code][0]:
            self.dict_dlhp[code] = [dt_, round((h / low - 1) * 100, 2)]

        if self.hoga_code == code:
            self.hogaQ.put([code, c, per, 0, 0, o, h, low])
            if not m:
                self.hogaQ.put([bids_, ch])
            else:
                self.hogaQ.put([-asks_, ch])

    def UpdateHogaData(self, dt, hoga_tamount, hoga_seprice, hoga_buprice, hoga_samount, hoga_bamount, code, receivetime):
        sm = 0
        int_logt = int(str(dt)[:12])
        ticksend = False
        if code in self.dict_tick.keys():
            if code in self.dict_hgdt.keys():
                if dt > self.dict_hgdt[code][0]:
                    if self.dict_tick[code][5] >= self.dict_hgdt[code][1]:
                        sm = round(self.dict_tick[code][5] - self.dict_hgdt[code][1], 2)
                    else:
                        sm = self.dict_tick[code][5]
                    ticksend = True
            else:
                ticksend = True

        if ticksend:
            csp, cbp = self.dict_hgbs[code]

            if hoga_seprice[-1] < csp:
                index = 0
                for i, price in enumerate(hoga_seprice[::-1]):
                    if price >= csp:
                        index = i
                        break
                if index <= 5:
                    hoga_seprice = hoga_seprice[5 - index:10 - index]
                    hoga_samount = hoga_samount[5 - index:10 - index]
                else:
                    hoga_seprice = list(np.zeros(index - 5)) + hoga_seprice[:10 - index]
                    hoga_samount = list(np.zeros(index - 5)) + hoga_samount[:10 - index]
            else:
                hoga_seprice = hoga_seprice[-5:]
                hoga_samount = hoga_samount[-5:]

            if hoga_buprice[0] > cbp:
                index = 0
                for i, price in enumerate(hoga_buprice):
                    if price <= cbp:
                        index = i
                        break
                hoga_buprice = hoga_buprice[index:index + 5]
                hoga_bamount = hoga_bamount[index:index + 5]
                if index > 5:
                    hoga_buprice = hoga_buprice + list(np.zeros(index - 5))
                    hoga_bamount = hoga_bamount + list(np.zeros(index - 5))
            else:
                hoga_buprice = hoga_buprice[:5]
                hoga_bamount = hoga_bamount[:5]

            c     = self.dict_tick[code][0]
            hlp   = round((c / ((self.dict_tick[code][2] + self.dict_tick[code][3]) / 2) - 1) * 100, 2)
            hgjrt = sum(hoga_samount + hoga_bamount)
            logt  = now() if self.int_logt < int_logt else 0
            data  = [dt] + self.dict_tick[code][:9] + [sm, hlp] + hoga_tamount + hoga_seprice + hoga_buprice + hoga_samount + hoga_bamount + [hgjrt, code, logt]

            self.cstgQ.put(data)
            if code in self.list_oder or code in self.list_jang:
                self.ctraderQ.put([code, c])
            if self.dict_set['리시버공유'] == 1:
                self.zq.put(['tickdata', data])

            self.dict_hgdt[code] = [dt, self.dict_tick[code][5]]
            self.dict_tick[code][7:9] = [0, 0]

        if self.hoga_code == code:
            self.hogaQ.put([code] + hoga_tamount + hoga_seprice[-5:] + hoga_buprice[:5] + hoga_samount[-5:] + hoga_bamount[:5])

        if self.int_logt < int_logt:
            gap = (now() - receivetime).total_seconds()
            self.windowQ.put([ui_num['C단순텍스트'], f'리시버 연산 시간 알림 - 수신시간과 연산시간의 차이는 [{gap:.6f}]초입니다.'])
            self.int_logt = int_logt

    def UpdateMoneyTop(self):
        data1, data2 = self.list_gsjm1.copy(), self.list_gsjm2.copy()
        self.cstgQ.put(['관심목록', data1, data2])
        if self.dict_set['리시버공유'] == 1:
            self.zq.put(['focuscodes', [data1, data2]])

        text_gsjm = ';'.join(self.list_gsjm1)
        curr_strtime = str(self.int_jcct)
        curr_datetime = strp_time('%Y%m%d%H%M%S', curr_strtime)

        if self.dt_mtct is not None:
            gap_seconds = (curr_datetime - self.dt_mtct).total_seconds()
            while gap_seconds > 1:
                gap_seconds -= 1
                pre_time = strf_time('%Y%m%d%H%M%S', timedelta_sec(-gap_seconds, curr_datetime))
                self.dict_mtop[int(pre_time)] = text_gsjm

        if curr_datetime != self.dt_mtct:
            self.dict_mtop[int(curr_strtime)] = text_gsjm
            self.dt_mtct = curr_datetime

    def MoneyTopSearch(self):
        if len(self.dict_tm5m) > 0:
            list_mtop = [x for x, y in sorted(self.dict_tm5m.items(), key=operator.itemgetter(1), reverse=True)[:self.dict_set['코인순위선정']]]
            self.list_gsjm1 = list_mtop[:-3]

            insert_list = list(set(list_mtop) - set(self.list_prmt))
            if len(insert_list) > 0:
                for code in insert_list:
                    self.InsertGsjmlist(code)

            delete_list = list(set(self.list_prmt) - set(list_mtop))
            if len(delete_list) > 0:
                for code in delete_list:
                    self.DeleteGsjmlist(code)

            self.list_prmt = list_mtop

    def InsertGsjmlist(self, code):
        if code not in self.list_gsjm2:
            self.list_gsjm2.append(code)
            if self.dict_set['코인매도취소관심진입']:
                self.ctraderQ.put(['관심진입', code])

    def DeleteGsjmlist(self, code):
        if code in self.list_gsjm2:
            self.list_gsjm2.remove(code)
            if self.dict_set['코인매수취소관심이탈']:
                self.ctraderQ.put(['관심이탈', code])

    def DaydataDownload(self):
        last = len(self.codes)

        if self.dict_set['코인분봉데이터']:
            dict_lastmin = {}
            con = sqlite3.connect(DB_COIN_MIN)
            dfm = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
            if len(dfm) > 0:
                for code in dfm['name'].to_list():
                    df = pd.read_sql(f"SELECT * FROM '{code}' ORDER BY 체결시간 DESC LIMIT 1", con)
                    dict_lastmin[code] = df['체결시간'].iloc[0]

            dict_min_ar = {}
            for i, code in enumerate(self.codes):
                time.sleep(0.1)
                try:
                    klines = self.binance.get_historical_klines(code, f'{self.dict_set["코인분봉기간"]}m', klines_type=HistoricalKlinesType.FUTURES)
                except Exception as e:
                    print(e)
                else:
                    columns = ['체결시간', '시가', '고가', '저가', '종가', '더미1', '더미2', '거래대금', '더미3', '더미4', '더미5', '더미6']
                    df = pd.DataFrame(klines, columns=columns)
                    df[columns] = df[columns].astype(float)
                    df.drop(columns=['더미1', '더미2', '더미3', '더미4', '더미5', '더미6'], inplace=True)
                    df['체결시간'] = df['체결시간'].apply(lambda x: int(strf_time('%Y%m%d%H%M%S', from_timestamp(x / 1000 - 32400))))

                    df['이평5']   = df['종가'].rolling(window=5).mean().round(8)
                    df['이평10']  = df['종가'].rolling(window=10).mean().round(8)
                    df['이평20']  = df['종가'].rolling(window=20).mean().round(8)
                    df['이평60']  = df['종가'].rolling(window=60).mean().round(8)
                    df['이평120'] = df['종가'].rolling(window=120).mean().round(8)
                    df['이평240'] = df['종가'].rolling(window=240).mean().round(8)

                    df['최고종가5']   = df['종가'].rolling(window=5).max().shift(1)
                    df['최고고가5']   = df['고가'].rolling(window=5).max().shift(1)
                    df['최고종가10']  = df['종가'].rolling(window=10).max().shift(1)
                    df['최고고가10']  = df['고가'].rolling(window=10).max().shift(1)
                    df['최고종가20']  = df['종가'].rolling(window=20).max().shift(1)
                    df['최고고가20']  = df['고가'].rolling(window=20).max().shift(1)
                    df['최고종가60']  = df['종가'].rolling(window=60).max().shift(1)
                    df['최고고가60']  = df['고가'].rolling(window=60).max().shift(1)
                    df['최고종가120'] = df['종가'].rolling(window=120).max().shift(1)
                    df['최고고가120'] = df['고가'].rolling(window=120).max().shift(1)
                    df['최고종가240'] = df['종가'].rolling(window=240).max().shift(1)
                    df['최고고가240'] = df['고가'].rolling(window=240).max().shift(1)

                    df['최저종가5']   = df['종가'].rolling(window=5).min().shift(1)
                    df['최저저가5']   = df['저가'].rolling(window=5).min().shift(1)
                    df['최저종가10']  = df['종가'].rolling(window=10).min().shift(1)
                    df['최저저가10']  = df['저가'].rolling(window=10).min().shift(1)
                    df['최저종가20']  = df['종가'].rolling(window=20).min().shift(1)
                    df['최저저가20']  = df['저가'].rolling(window=20).min().shift(1)
                    df['최저종가60']  = df['종가'].rolling(window=60).min().shift(1)
                    df['최저저가60']  = df['저가'].rolling(window=60).min().shift(1)
                    df['최저종가120'] = df['종가'].rolling(window=120).min().shift(1)
                    df['최저저가120'] = df['저가'].rolling(window=120).min().shift(1)
                    df['최저종가240'] = df['종가'].rolling(window=240).min().shift(1)
                    df['최저저가240'] = df['저가'].rolling(window=240).min().shift(1)

                    df['종가합계4']   = df['종가'].rolling(window=4).sum().shift(1)
                    df['종가합계9']   = df['종가'].rolling(window=9).sum().shift(1)
                    df['종가합계19']  = df['종가'].rolling(window=19).sum().shift(1)
                    df['종가합계59']  = df['종가'].rolling(window=59).sum().shift(1)
                    df['종가합계119'] = df['종가'].rolling(window=119).sum().shift(1)
                    df['종가합계239'] = df['종가'].rolling(window=239).sum().shift(1)
                    df['최고거래대금'] = df['거래대금'].rolling(window=self.dict_set['코인분봉개수']).max().shift(1)
                    df.fillna(0, inplace=True)

                    columns = ['체결시간', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240']
                    df2 = df[columns][-self.dict_set['코인분봉개수']:]
                    dict_min_ar[code] = np.array(df2)

                    if code in dict_lastmin.keys():
                        df = df[df['체결시간'] > dict_lastmin[code]]
                    df = df.set_index('체결시간')
                    if len(df) > 0:
                        self.queryQ.put(['코인분봉', df, code, 'append'])
                print(f'코인 분봉데이터 다운로드 중 ... [{i + 1}/{last}]')

            print('코인 분봉데이터 다운로드 완료')
            self.cstgQ.put(['분봉데이터', dict_min_ar])
            if self.dict_set['리시버공유'] == 1:
                self.zq.put(['mindata', dict_min_ar])
            con.close()

        if self.dict_set['코인일봉데이터']:
            dict_lastday = {}
            con = sqlite3.connect(DB_COIN_DAY)
            dfd = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
            if len(dfd) > 0:
                for code in dfd['name'].to_list():
                    df = pd.read_sql(f"SELECT * FROM '{code}' ORDER BY 일자 DESC LIMIT 1", con)
                    dict_lastday[code] = df['일자'].iloc[0]

            dict_day_ar = {}
            for i, code in enumerate(self.codes):
                time.sleep(0.1)
                try:
                    klines = self.binance.get_historical_klines(code, '1d', klines_type=HistoricalKlinesType.FUTURES)
                except Exception as e:
                    print(e)
                else:
                    columns = ['일자', '시가', '고가', '저가', '종가', '더미1', '더미2', '거래대금', '더미3', '더미4', '더미5', '더미6']
                    df = pd.DataFrame(klines, columns=columns)
                    df[columns] = df[columns].astype(float)
                    df.drop(columns=['더미1', '더미2', '더미3', '더미4', '더미5', '더미6'], inplace=True)
                    df['일자'] = df['일자'].apply(lambda x: int(strf_time('%Y%m%d', from_timestamp(x / 1000 - 32400))))

                    df['이평5']   = df['종가'].rolling(window=5).mean().round(8)
                    df['이평10']  = df['종가'].rolling(window=10).mean().round(8)
                    df['이평20']  = df['종가'].rolling(window=20).mean().round(8)
                    df['이평60']  = df['종가'].rolling(window=60).mean().round(8)
                    df['이평120'] = df['종가'].rolling(window=120).mean().round(8)
                    df['이평240'] = df['종가'].rolling(window=240).mean().round(8)

                    df['최고종가5']   = df['종가'].rolling(window=5).max().shift(1)
                    df['최고고가5']   = df['고가'].rolling(window=5).max().shift(1)
                    df['최고종가10']  = df['종가'].rolling(window=10).max().shift(1)
                    df['최고고가10']  = df['고가'].rolling(window=10).max().shift(1)
                    df['최고종가20']  = df['종가'].rolling(window=20).max().shift(1)
                    df['최고고가20']  = df['고가'].rolling(window=20).max().shift(1)
                    df['최고종가60']  = df['종가'].rolling(window=60).max().shift(1)
                    df['최고고가60']  = df['고가'].rolling(window=60).max().shift(1)
                    df['최고종가120'] = df['종가'].rolling(window=120).max().shift(1)
                    df['최고고가120'] = df['고가'].rolling(window=120).max().shift(1)
                    df['최고종가240'] = df['종가'].rolling(window=240).max().shift(1)
                    df['최고고가240'] = df['고가'].rolling(window=240).max().shift(1)

                    df['최저종가5']   = df['종가'].rolling(window=5).min().shift(1)
                    df['최저저가5']   = df['저가'].rolling(window=5).min().shift(1)
                    df['최저종가10']  = df['종가'].rolling(window=10).min().shift(1)
                    df['최저저가10']  = df['저가'].rolling(window=10).min().shift(1)
                    df['최저종가20']  = df['종가'].rolling(window=20).min().shift(1)
                    df['최저저가20']  = df['저가'].rolling(window=20).min().shift(1)
                    df['최저종가60']  = df['종가'].rolling(window=60).min().shift(1)
                    df['최저저가60']  = df['저가'].rolling(window=60).min().shift(1)
                    df['최저종가120'] = df['종가'].rolling(window=120).min().shift(1)
                    df['최저저가120'] = df['저가'].rolling(window=120).min().shift(1)
                    df['최저종가240'] = df['종가'].rolling(window=240).min().shift(1)
                    df['최저저가240'] = df['저가'].rolling(window=240).min().shift(1)

                    df['종가합계4']   = df['종가'].rolling(window=4).sum().shift(1)
                    df['종가합계9']   = df['종가'].rolling(window=9).sum().shift(1)
                    df['종가합계19']  = df['종가'].rolling(window=19).sum().shift(1)
                    df['종가합계59']  = df['종가'].rolling(window=59).sum().shift(1)
                    df['종가합계119'] = df['종가'].rolling(window=119).sum().shift(1)
                    df['종가합계239'] = df['종가'].rolling(window=239).sum().shift(1)
                    df['최고거래대금'] = df['거래대금'].rolling(window=250).max().shift(1)
                    df.fillna(0, inplace=True)

                    columns = ['일자', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240']
                    df2 = df[columns][-250:]
                    dict_day_ar[code] = np.array(df2)

                    if code in dict_lastday.keys():
                        df = df[df['일자'] > dict_lastday[code]]
                    df = df.set_index('일자')
                    if len(df) > 0:
                        self.queryQ.put(['코인일봉', df, code, 'append'])
                print(f'코인 일봉데이터 다운로드 중 ... [{i + 1}/{last}]')

            print('코인 일봉데이터 다운로드 완료')
            self.cstgQ.put(['일봉데이터', dict_day_ar])
            if self.dict_set['리시버공유'] == 1:
                self.zq.put(['daydata', dict_day_ar])
            con.close()


class WebSocketManager:
    def __init__(self, codes, q):
        self.codes = codes
        self.q     = q
        self.AsyncioLoop()

    async def task_trade_socket(self):
        client = await AsyncClient.create()
        bm = BinanceSocketManager(client)
        stream_list = []
        for code in self.codes:
            stream_list.append(f'{code.lower()}@aggTrade')
        ts = bm.futures_multiplex_socket(stream_list)
        async with ts as trade_socket:
            while True:
                try:
                    recv_data = await trade_socket.recv()
                    self.q.put(['trade', recv_data])
                except:
                    self.q.put('ConnectionClosedError')

    async def task_depth_socket(self):
        client = await AsyncClient.create()
        bm = BinanceSocketManager(client)
        stream_list = []
        for code in self.codes:
            stream_list.append(f'{code.lower()}@depth10')
        ts = bm.futures_multiplex_socket(stream_list)
        async with ts as depth_socket:
            while True:
                try:
                    recv_data = await depth_socket.recv()
                    self.q.put(['depth', recv_data])
                except:
                    self.q.put('ConnectionClosedError')

    def AsyncioLoop(self):
        loop = asyncio.get_event_loop()
        asyncio.ensure_future(self.task_trade_socket())
        asyncio.ensure_future(self.task_depth_socket())
        loop.run_forever()
