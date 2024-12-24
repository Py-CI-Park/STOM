import math
# noinspection PyUnresolvedReferences
import talib
import sqlite3
import numpy as np
import pandas as pd
from traceback import print_exc
from stock.strategy_kiwoom import StrategyKiwoom
# noinspection PyUnresolvedReferences
from utility.static import now, strf_time, strp_time, timedelta_sec, GetUvilower5, GetKiwoomPgSgSp, GetHogaunit
from utility.setting import ui_num, DB_STOCK_DAY, DB_STOCK_MIN, dict_min, dict_order_ratio


class StrategyKiwoom2(StrategyKiwoom):
    def __init__(self, gubun, qlist):
        super().__init__(gubun, qlist)

    def LoadDayMinData(self):
        if self.dict_set['주식분봉데이터']:
            con = sqlite3.connect(DB_STOCK_MIN)
            df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
            if len(df) > 0:
                code_list = df['name'].to_list()
                last = len(code_list)
                for i, code in enumerate(code_list):
                    if code in self.dict_stgn.keys() and self.gubun == self.dict_stgn[code]:
                        df = pd.read_sql(f"SELECT * FROM '{code}' ORDER BY 체결시간 DESC LIMIT {self.dict_set['주식분봉개수']}", con)
                        columns = ['체결시간', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240']
                        """ 보조지표 사용예
                        columns = [
                            '체결시간', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120',
                            '이평240', 'BBU', 'BBM', 'BBL', 'RSI', 'CCI', 'MACD', 'MACDS', 'MACDH', 'STOCK', 'STOCD', 'ATR'
                        ]
                        """
                        df = df[columns][::-1]
                        self.dict_min_ar[code] = np.array(df)
                        print(f'[{now()}] 주식 분봉데이터 로딩 중 ... [{i + 1}/{last}]')
                for code in self.dict_min_ar.keys():
                    self.dict_min_data[code] = self.GetNewLineData(self.dict_min_ar[code], self.dict_set['주식분봉개수'])
                self.kwzservQ.put(('window', (ui_num['S로그텍스트'], '시스템 명령 실행 알림 - 분봉데이터 로딩 완료')))
            else:
                self.dict_set['주식분봉데이터'] = False
                self.kwzservQ.put(('window', (ui_num['S로그텍스트'], '시스템 명령 오류 알림 - 분봉데이터가 존재하지 않습니다.')))
            con.close()

        if self.dict_set['주식일봉데이터']:
            con = sqlite3.connect(DB_STOCK_DAY)
            df = pd.read_sql("SELECT name FROM sqlite_master WHERE TYPE = 'table'", con)
            if len(df) > 0:
                code_list = df['name'].to_list()
                last = len(code_list)
                for i, code in enumerate(code_list):
                    if code in self.dict_stgn.keys() and self.gubun == self.dict_stgn[code]:
                        df = pd.read_sql(f"SELECT * FROM '{code}' ORDER BY 일자 DESC LIMIT 250", con)
                        columns = ['일자', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240']
                        """ 보조지표 사용예
                        columns = [
                            '일자', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120',
                            '이평240', 'BBU', 'BBM', 'BBL', 'RSI', 'CCI', 'MACD', 'MACDS', 'MACDH', 'STOCK', 'STOCD', 'ATR'
                        ]
                        """
                        df = df[columns][::-1]
                        self.dict_day_ar[code] = np.array(df)
                        print(f'[{now()}] 주식 일봉데이터 로딩 중 ... [{i + 1}/{last}]')
                for code in self.dict_day_ar.keys():
                    self.dict_day_data[code] = self.GetNewLineData(self.dict_day_ar[code], 250)
                self.kwzservQ.put(('window', (ui_num['S로그텍스트'], '시스템 명령 실행 알림 - 일봉데이터 로딩 완료')))
            else:
                self.dict_set['주식일봉데이터'] = False
                self.kwzservQ.put(('window', (ui_num['S로그텍스트'], '시스템 명령 오류 알림 - 일봉데이터가 존재하지 않습니다.')))
            con.close()

    @staticmethod
    def GetNewLineData(ar, hmcount):
        최고종가5   = ar[-5:,   4].max()
        최고고가5   = ar[-5:,   2].max()
        최고종가10  = ar[-10:,  4].max()
        최고고가10  = ar[-10:,  2].max()
        최고종가20  = ar[-20:,  4].max()
        최고고가20  = ar[-20:,  2].max()
        최고종가60  = ar[-60:,  4].max()
        최고고가60  = ar[-60:,  2].max()
        최고종가120 = ar[-120:, 4].max()
        최고고가120 = ar[-120:, 2].max()
        최고종가240 = ar[-240:, 4].max()
        최고고가240 = ar[-240:, 2].max()
        최저종가5   = ar[-5:,   4].min()
        최저저가5   = ar[-5:,   3].min()
        최저종가10  = ar[-10:,  4].min()
        최저저가10  = ar[-10:,  3].min()
        최저종가20  = ar[-20:,  4].min()
        최저저가20  = ar[-20:,  3].min()
        최저종가60  = ar[-60:,  4].min()
        최저저가60  = ar[-60:,  3].min()
        최저종가120 = ar[-120:, 4].min()
        최저저가120 = ar[-120:, 3].min()
        최저종가240 = ar[-240:, 4].min()
        최저저가240 = ar[-240:, 3].min()
        종가합계4   = ar[-4:,   4].sum()
        종가합계9   = ar[-9:,   4].sum()
        종가합계19  = ar[-19:,  4].sum()
        종가합계59  = ar[-59:,  4].sum()
        종가합계119 = ar[-119:, 4].sum()
        종가합계239 = ar[-239:, 4].sum()
        최고거래대금 = ar[-hmcount:, 5].max()
        new_data = [
            최고종가5, 최고고가5, 최고종가10, 최고고가10, 최고종가20, 최고고가20, 최고종가60, 최고고가60, 최고종가120, 최고고가120, 최고종가240, 최고고가240,
            최저종가5, 최저저가5, 최저종가10, 최저저가10, 최저종가20, 최저저가20, 최저종가60, 최저저가60, 최저종가120, 최저저가120, 최저종가240, 최저저가240,
            종가합계4, 종가합계9, 종가합계19, 종가합계59, 종가합계119, 종가합계239, 최고거래대금
        ]
        return new_data

    def UpdateTriple(self, data):
        gubun, code, dt = data
        if gubun == '분봉재로딩':
            con = sqlite3.connect(DB_STOCK_MIN)
            df = pd.read_sql(f"SELECT * FROM '{code}' WHERE 체결시간 < {dt} ORDER BY 체결시간 DESC LIMIT {self.dict_set['주식분봉개수']}", con)
            columns = ['체결시간', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240']
            df = df[columns][::-1]
            self.dict_min_ar[code] = np.array(df)
            self.dict_min_data[code] = self.GetNewLineData(self.dict_min_ar[code], self.dict_set['주식분봉개수'])
            con.close()
        elif gubun == '일봉재로딩':
            con = sqlite3.connect(DB_STOCK_DAY)
            df = pd.read_sql(f"SELECT * FROM '{code}' WHERE 일자 < {dt} ORDER BY 일자 DESC LIMIT 250", con)
            columns = ['일자', '시가', '고가', '저가', '종가', '거래대금', '이평5', '이평10', '이평20', '이평60', '이평120', '이평240']
            df = df[columns][::-1]
            self.dict_day_ar[code] = np.array(df)
            self.dict_day_data[code] = self.GetNewLineData(self.dict_day_ar[code], 250)
            con.close()

    def Strategy(self, data):
        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 거래대금증감, 전일비, 회전율, 전일동시간비, 시가총액, \
            라운드피겨위5호가이내, 초당매수수량, 초당매도수량, VI해제시간, VI가격, VI호가단위, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량, \
            매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, \
            매도수5호가잔량합, 종목코드, 종목명, 틱수신시간 = data

        def Parameter_Previous(aindex, pre):
            pindex = (self.indexn - pre) if pre != -1 else 매수틱번호
            return self.dict_tik_ar[종목코드][pindex, aindex]

        def 현재가N(pre):
            return Parameter_Previous(1, pre)

        def 시가N(pre):
            return Parameter_Previous(2, pre)

        def 고가N(pre):
            return Parameter_Previous(3, pre)

        def 저가N(pre):
            return Parameter_Previous(4, pre)

        def 등락율N(pre):
            return Parameter_Previous(5, pre)

        def 당일거래대금N(pre):
            return Parameter_Previous(6, pre)

        def 체결강도N(pre):
            return Parameter_Previous(7, pre)

        def 거래대금증감N(pre):
            return Parameter_Previous(8, pre)

        def 전일비N(pre):
            return Parameter_Previous(9, pre)

        def 회전율N(pre):
            return Parameter_Previous(10, pre)

        def 전일동시간비N(pre):
            return Parameter_Previous(11, pre)

        def 시가총액N(pre):
            return Parameter_Previous(12, pre)

        def 라운드피겨위5호가이내N(pre):
            return Parameter_Previous(13, pre)

        def 초당매수수량N(pre):
            return Parameter_Previous(14, pre)

        def 초당매도수량N(pre):
            return Parameter_Previous(15, pre)

        def 초당거래대금N(pre):
            return Parameter_Previous(19, pre)

        def 고저평균대비등락율N(pre):
            return Parameter_Previous(20, pre)

        def 매도총잔량N(pre):
            return Parameter_Previous(21, pre)

        def 매수총잔량N(pre):
            return Parameter_Previous(22, pre)

        def 매도호가5N(pre):
            return Parameter_Previous(23, pre)

        def 매도호가4N(pre):
            return Parameter_Previous(24, pre)

        def 매도호가3N(pre):
            return Parameter_Previous(25, pre)

        def 매도호가2N(pre):
            return Parameter_Previous(26, pre)

        def 매도호가1N(pre):
            return Parameter_Previous(27, pre)

        def 매수호가1N(pre):
            return Parameter_Previous(28, pre)

        def 매수호가2N(pre):
            return Parameter_Previous(29, pre)

        def 매수호가3N(pre):
            return Parameter_Previous(30, pre)

        def 매수호가4N(pre):
            return Parameter_Previous(31, pre)

        def 매수호가5N(pre):
            return Parameter_Previous(32, pre)

        def 매도잔량5N(pre):
            return Parameter_Previous(33, pre)

        def 매도잔량4N(pre):
            return Parameter_Previous(34, pre)

        def 매도잔량3N(pre):
            return Parameter_Previous(35, pre)

        def 매도잔량2N(pre):
            return Parameter_Previous(36, pre)

        def 매도잔량1N(pre):
            return Parameter_Previous(37, pre)

        def 매수잔량1N(pre):
            return Parameter_Previous(38, pre)

        def 매수잔량2N(pre):
            return Parameter_Previous(39, pre)

        def 매수잔량3N(pre):
            return Parameter_Previous(40, pre)

        def 매수잔량4N(pre):
            return Parameter_Previous(41, pre)

        def 매수잔량5N(pre):
            return Parameter_Previous(42, pre)

        def 매도수5호가잔량합N(pre):
            return Parameter_Previous(43, pre)

        def 이동평균(tick, pre=0):
            if tick == 60:
                return Parameter_Previous(44, pre)
            elif tick == 300:
                return Parameter_Previous(45, pre)
            elif tick == 600:
                return Parameter_Previous(46, pre)
            elif tick == 1200:
                return Parameter_Previous(47, pre)
            else:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else 매수틱번호 + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else 매수틱번호 + 1
                return round(self.dict_tik_ar[종목코드][sindex:eindex, 1].mean(), 3)

        def Parameter_Area(aindex, vindex, tick, pre, gubun_):
            if tick == 평균값계산틱수:
                return Parameter_Previous(aindex, pre)
            else:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else 매수틱번호 + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else 매수틱번호 + 1
                if gubun_ == 'max':
                    return self.dict_tik_ar[종목코드][sindex:eindex, vindex].max()
                elif gubun_ == 'min':
                    return self.dict_tik_ar[종목코드][sindex:eindex, vindex].min()
                elif gubun_ == 'sum':
                    return self.dict_tik_ar[종목코드][sindex:eindex, vindex].sum()
                else:
                    return self.dict_tik_ar[종목코드][sindex:eindex, vindex].mean()

        def 최고현재가(tick, pre=0):
            return Parameter_Area(48, 1, tick, pre, 'max')

        def 최저현재가(tick, pre=0):
            return Parameter_Area(49, 1, tick, pre, 'min')

        def 체결강도평균(tick, pre=0):
            return Parameter_Area(50, 7, tick, pre, 'mean')

        def 최고체결강도(tick, pre=0):
            return Parameter_Area(51, 7, tick, pre, 'max')

        def 최저체결강도(tick, pre=0):
            return Parameter_Area(52, 7, tick, pre, 'min')

        def 최고초당매수수량(tick, pre=0):
            return Parameter_Area(53, 14, tick, pre, 'max')

        def 최고초당매도수량(tick, pre=0):
            return Parameter_Area(54, 15, tick, pre, 'max')

        def 누적초당매수수량(tick, pre=0):
            return Parameter_Area(55, 14, tick, pre, 'sum')

        def 누적초당매도수량(tick, pre=0):
            return Parameter_Area(56, 15, tick, pre, 'sum')

        def 초당거래대금평균(tick, pre=0):
            return Parameter_Area(57, 19, tick, pre, 'mean')

        def Parameter_Dgree(aindex, vindex, tick, pre, cf):
            if tick == 평균값계산틱수:
                return Parameter_Previous(aindex, pre)
            else:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1  else 매수틱번호 + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1  else 매수틱번호 + 1
                dmp_gap = self.dict_tik_ar[종목코드][eindex, vindex] - self.dict_tik_ar[종목코드][sindex, vindex]
                return round(math.atan2(dmp_gap * cf, tick) / (2 * math.pi) * 360, 2)

        def 등락율각도(tick, pre=0):
            return Parameter_Dgree(58, 5, tick, pre, 5)

        def 당일거래대금각도(tick, pre=0):
            return Parameter_Dgree(59, 6, tick, pre, 0.01)

        def 전일비각도(tick, pre=0):
            return Parameter_Dgree(60, 9, tick, pre, 1)

        분봉체결시간 = int(str(체결시간)[:10] + dict_min[self.dict_set['주식분봉기간']][str(체결시간)[10:12]] + '00')
        if self.dict_set['주식분봉데이터']:
            def 분봉시가N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 1]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 1]

            def 분봉고가N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 2]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 2]

            def 분봉저가N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 3]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 3]

            def 분봉현재가N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 4]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 4]

            def 분봉거래대금N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 5]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 5]

            def 분봉이평5N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 6]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 6]

            def 분봉이평10N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 7]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 7]

            def 분봉이평20N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 8]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 8]

            def 분봉이평60N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 9]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 9]

            def 분봉이평120N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 10]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 10]

            def 분봉이평240N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 11]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 11]

            """ 보조지표 사용예
            def M_BBU_N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 12]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 12]
    
            def M_BBM_N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 13]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 13]
    
            def M_BBL_N(pre):
                if 분봉체결시간 != self.dict_min_ar[종목코드][-1, 0]:
                    return self.dict_min_ar[종목코드][-pre, 14]
                else:
                    return self.dict_min_ar[종목코드][-(pre + 1), 14]
            .
            .
            .
            """

        일봉일자 = int(str(체결시간)[:8])
        if self.dict_set['주식일봉데이터']:
            def 일봉시가N(pre):
                return self.dict_day_ar[종목코드][-pre, 1]

            def 일봉고가N(pre):
                return self.dict_day_ar[종목코드][-pre, 2]

            def 일봉저가N(pre):
                return self.dict_day_ar[종목코드][-pre, 3]

            def 일봉현재가N(pre):
                return self.dict_day_ar[종목코드][-pre, 4]

            def 일봉거래대금N(pre):
                return self.dict_day_ar[종목코드][-pre, 5]

            def 일봉이평5N(pre):
                return self.dict_day_ar[종목코드][-pre, 6]

            def 일봉이평10N(pre):
                return self.dict_day_ar[종목코드][-pre, 7]

            def 일봉이평20N(pre):
                return self.dict_day_ar[종목코드][-pre, 8]

            def 일봉이평60N(pre):
                return self.dict_day_ar[종목코드][-pre, 9]

            def 일봉이평120N(pre):
                return self.dict_day_ar[종목코드][-pre, 10]

            def 일봉이평240N(pre):
                return self.dict_day_ar[종목코드][-pre, 11]

        bhogainfo = ((매도호가1, 매도잔량1), (매도호가2, 매도잔량2), (매도호가3, 매도잔량3), (매도호가4, 매도잔량4), (매도호가5, 매도잔량5))
        shogainfo = ((매수호가1, 매수잔량1), (매수호가2, 매수잔량2), (매수호가3, 매수잔량3), (매수호가4, 매수잔량4), (매수호가5, 매수잔량5))
        self.bhogainfo = bhogainfo[:self.dict_set['주식매수시장가잔량범위']]
        self.shogainfo = shogainfo[:self.dict_set['주식매도시장가잔량범위']]

        시분초 = int(str(체결시간)[8:])
        호가단위 = GetHogaunit(종목코드 in self.tuple_kosd, 현재가, 체결시간)
        VI아래5호가 = GetUvilower5(VI가격, VI호가단위, 체결시간)
        VI해제시간_ = int(strf_time('%Y%m%d%H%M%S', VI해제시간))
        평균값계산틱수 = self.dict_set['주식장초평균값계산틱수'] if 시분초 < self.dict_set['주식장초전략종료시간'] else self.dict_set['주식장중평균값계산틱수']
        이동평균60_, 이동평균300_, 이동평균600_, 이동평균1200_, 최고현재가_, 최저현재가_ = 0., 0., 0., 0., 0, 0
        체결강도평균_, 최고체결강도_, 최저체결강도_, 최고초당매수수량_, 최고초당매도수량_ = 0., 0., 0., 0, 0
        누적초당매수수량_, 누적초당매도수량_, 초당거래대금평균_, 등락율각도_, 당일거래대금각도_, 전일비각도_ = 0, 0, 0., 0., 0., 0.

        if 종목코드 in self.dict_tik_ar.keys():
            len_array = len(self.dict_tik_ar[종목코드])
            if len_array >=   59: 이동평균60_   = round((self.dict_tik_ar[종목코드][  -59:, 1].sum() + 현재가) /   60, 3)
            if len_array >=  299: 이동평균300_  = round((self.dict_tik_ar[종목코드][ -299:, 1].sum() + 현재가) /  300, 3)
            if len_array >=  599: 이동평균600_  = round((self.dict_tik_ar[종목코드][ -599:, 1].sum() + 현재가) /  600, 3)
            if len_array >= 1199: 이동평균1200_ = round((self.dict_tik_ar[종목코드][-1199:, 1].sum() + 현재가) / 1200, 3)
            if len_array >= 평균값계산틱수 - 1:
                최고현재가_      = max(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 1].max(), 현재가)
                최저현재가_      = min(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 1].min(), 현재가)
                체결강도평균_    =    (self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 7].sum() + 체결강도) / 평균값계산틱수
                최고체결강도_    = max(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 7].max(), 체결강도)
                최저체결강도_    = min(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 7].min(), 체결강도)
                최고초당매수수량_ = max(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 14].max(), 초당매수수량)
                최고초당매도수량_ = min(self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 15].min(), 초당매도수량)
                누적초당매수수량_ =     self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 14].sum() + 초당매수수량
                누적초당매도수량_ =     self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 15].sum() + 초당매도수량
                초당거래대금평균_ =    (self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1):, 19].sum() + 초당거래대금) / 평균값계산틱수
                등락율각도_      = round(math.atan2((등락율 - self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1), 5]) * 5, 평균값계산틱수) / (2 * math.pi) * 360, 2)
                당일거래대금각도_ = round(math.atan2((당일거래대금 - self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1), 6]) / 100, 평균값계산틱수) / (2 * math.pi) * 360, 2)
                전일비각도_      = round(math.atan2(전일비 - self.dict_tik_ar[종목코드][-(평균값계산틱수 - 1), 9], 평균값계산틱수) / (2 * math.pi) * 360, 2)

        new_data_tick = [
            체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 거래대금증감, 전일비, 회전율, 전일동시간비, 시가총액, 라운드피겨위5호가이내,
            초당매수수량, 초당매도수량, VI해제시간_, VI가격, VI호가단위, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량,
            매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5,
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, 매도수5호가잔량합,
            이동평균60_, 이동평균300_, 이동평균600_, 이동평균1200_, 최고현재가_, 최저현재가_, 체결강도평균_, 최고체결강도_, 최저체결강도_,
            최고초당매수수량_, 최고초당매도수량_, 누적초당매수수량_, 누적초당매도수량_, 초당거래대금평균_, 등락율각도_, 당일거래대금각도_, 전일비각도_
        ]

        """
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
              53            54               55              56              57             58         59            60
        """

        if 종목코드 not in self.dict_tik_ar.keys():
            self.dict_tik_ar[종목코드] = np.array([new_data_tick])
        else:
            self.dict_tik_ar[종목코드] = np.r_[self.dict_tik_ar[종목코드], np.array([new_data_tick])]

        데이터길이 = len(self.dict_tik_ar[종목코드])
        self.indexn = 데이터길이 - 1

        if 데이터길이 > 1800 and (self.dict_set['리시버공유'] == 2 or not self.dict_set['주식틱데이터저장']):
            self.dict_tik_ar[종목코드] = np.delete(self.dict_tik_ar[종목코드], 0, 0)

        분봉시가, 분봉고가, 분봉저가, 분봉거래대금, 분봉이평5, 분봉이평10, 분봉이평20, 분봉이평60, 분봉이평120, 분봉이평240 = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        일봉이평5, 일봉이평10, 일봉이평20, 일봉이평60, 일봉이평120, 일봉이평240 = 0, 0, 0, 0, 0, 0

        if self.dict_set['주식분봉데이터']:
            if 종목코드 not in self.dict_min_data.keys():
                return
            try:
                if 분봉체결시간 == self.dict_min_ar[종목코드][-1, 0]:
                    분봉시가, 분봉고가, 분봉저가 = self.dict_min_ar[종목코드][-1, 1:4]
                    분봉거래대금 = self.dict_min_ar[종목코드][-1, 5]
                    분봉고가 = 현재가 if 현재가 > 분봉고가 else 분봉고가
                    분봉저가 = 현재가 if 현재가 < 분봉저가 else 분봉저가
                    분봉거래대금 += 초당거래대금
                    """ 보조지표 사용예
                    M_BBU, M_BBM, M_BBL = talib.BBANDS(np.r_[self.dict_min_ar[종목코드][:-1, 4], np.array([현재가])], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
                    M_BBU, M_BBM, M_BBL = M_BBU[-1], M_BBM[-1], M_BBL[-1]
                    M_RSI = talib.RSI(np.r_[self.dict_min_ar[종목코드][:-1, 4], np.array([현재가])], timeperiod=14)[-1]
                    M_CCI = talib.CCI(np.r_[self.dict_min_ar[종목코드][:-1, 2], np.array([분봉고가])], np.r_[self.dict_min_ar[종목코드][:-1, 3], np.array([분봉저가])], np.r_[self.dict_min_ar[종목코드][:-1, 4], np.array([현재가])], timeperiod=14)[-1]
                    M_MACD, M_MACDS, M_MACDH = talib.MACD(np.r_[self.dict_min_ar[종목코드][:-1, 4], np.array([현재가])], fastperiod=12, slowperiod=26, signalperiod=9)
                    M_MACD, M_MACDS, M_MACDH = M_MACD[-1], M_MACDS[-1], M_MACDH[-1]
                    M_STOCK, M_STOCD = talib.STOCH(np.r_[self.dict_min_ar[종목코드][:-1, 2], np.array([분봉고가])], np.r_[self.dict_min_ar[종목코드][:-1, 3], np.array([분봉저가])], np.r_[self.dict_min_ar[종목코드][:-1, 4], np.array([현재가])], fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
                    M_STOCK, M_STOCD = M_STOCK[-1], M_STOCD[-1]
                    M_ATR = talib.ATR(np.r_[self.dict_min_ar[종목코드][:-1, 2], np.array([분봉고가])], np.r_[self.dict_min_ar[종목코드][:-1, 3], np.array([분봉저가])], np.r_[self.dict_min_ar[종목코드][:-1, 4], np.array([현재가])], timeperiod=14)[-1]
                    """
                else:
                    self.dict_min_data[종목코드] = self.GetNewLineData(self.dict_min_ar[종목코드], self.dict_set['주식분봉개수'])
                    분봉시가, 분봉고가, 분봉저가, 분봉거래대금 = 현재가, 현재가, 현재가, 초당거래대금
                    """ 보조지표 사용예
                    M_BBU, M_BBM, M_BBL = talib.BBANDS(np.r_[self.dict_min_ar[종목코드][:, 4], np.array([현재가])], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
                    M_BBU, M_BBM, M_BBL = M_BBU[-1], M_BBM[-1], M_BBL[-1]
                    M_RSI = talib.RSI(np.r_[self.dict_min_ar[종목코드][:, 4], np.array([현재가])], timeperiod=14)[-1]
                    M_CCI = talib.CCI(np.r_[self.dict_min_ar[종목코드][:, 2], np.array([분봉고가])], np.r_[self.dict_min_ar[종목코드][:, 3], np.array([분봉저가])], np.r_[self.dict_min_ar[종목코드][:, 4], np.array([현재가])], timeperiod=14)[-1]
                    M_MACD, M_MACDS, M_MACDH = talib.MACD(np.r_[self.dict_min_ar[종목코드][:, 4], np.array([현재가])], fastperiod=12, slowperiod=26, signalperiod=9)
                    M_MACD, M_MACDS, M_MACDH = M_MACD[-1], M_MACDS[-1], M_MACDH[-1]
                    M_STOCK, M_STOCD = talib.STOCH(np.r_[self.dict_min_ar[종목코드][:, 2], np.array([분봉고가])], np.r_[self.dict_min_ar[종목코드][:, 3], np.array([분봉저가])], np.r_[self.dict_min_ar[종목코드][:, 4], np.array([현재가])], fastk_period=5, slowk_period=3, slowk_matype=0, slowM_period=3, slowM_matype=0)
                    M_STOCK, M_STOCD = M_STOCK[-1], M_STOCD[-1]
                    M_ATR = talib.ATR(np.r_[self.dict_min_ar[종목코드][:, 2], np.array([분봉고가])], np.r_[self.dict_min_ar[종목코드][:, 3], np.array([분봉저가])], np.r_[self.dict_min_ar[종목코드][:, 4], np.array([현재가])], timeperiod=14)[-1]
                    """
                분봉최고종가5, 분봉최고고가5, 분봉최고종가10, 분봉최고고가10, 분봉최고종가20, 분봉최고고가20, 분봉최고종가60, \
                    분봉최고고가60, 분봉최고종가120, 분봉최고고가120, 분봉최고종가240, 분봉최고고가240, 분봉최저종가5, 분봉최저저가5, \
                    분봉최저종가10, 분봉최저저가10, 분봉최저종가20, 분봉최저저가20, 분봉최저종가60, 분봉최저저가60, 분봉최저종가120, \
                    분봉최저저가120, 분봉최저종가240, 분봉최저저가240, 분봉종가합계4, 분봉종가합계9, 분봉종가합계19, 분봉종가합계59, \
                    분봉종가합계119, 분봉종가합계239, 분봉최고거래대금 = self.dict_min_data[종목코드]
                분봉이평5   = round((분봉종가합계4   + 현재가) /   5, 3)
                분봉이평10  = round((분봉종가합계9   + 현재가) /  10, 3)
                분봉이평20  = round((분봉종가합계19  + 현재가) /  20, 3)
                분봉이평60  = round((분봉종가합계59  + 현재가) /  60, 3)
                분봉이평120 = round((분봉종가합계119 + 현재가) / 120, 3)
                분봉이평240 = round((분봉종가합계239 + 현재가) / 240, 3)
                분봉최고거래대금대비 = round(분봉거래대금 / 분봉최고거래대금 * 100, 2) if 분봉최고거래대금 != 0 else 0.
            except Exception as e:
                self.kwzservQ.put(('window', (ui_num['S단순텍스트'], f'시스템 명령 오류 알림 - 분봉데이터 {e}')))
                return

        if self.dict_set['주식일봉데이터']:
            if 종목코드 not in self.dict_day_data.keys():
                return
            try:
                일봉최고종가5, 일봉최고고가5, 일봉최고종가10, 일봉최고고가10, 일봉최고종가20, 일봉최고고가20, 일봉최고종가60, \
                    일봉최고고가60, 일봉최고종가120, 일봉최고고가120, 일봉최고종가240, 일봉최고고가240, 일봉최저종가5, 일봉최저저가5, \
                    일봉최저종가10, 일봉최저저가10, 일봉최저종가20, 일봉최저저가20, 일봉최저종가60, 일봉최저저가60, 일봉최저종가120, \
                    일봉최저저가120, 일봉최저종가240, 일봉최저저가240, 일봉종가합계4, 일봉종가합계9, 일봉종가합계19, 일봉종가합계59, \
                    일봉종가합계119, 일봉종가합계239, 일봉최고거래대금 = self.dict_day_data[종목코드]
                일봉이평5   = round((일봉종가합계4   + 현재가) /   5, 3)
                일봉이평10  = round((일봉종가합계9   + 현재가) /  10, 3)
                일봉이평20  = round((일봉종가합계19  + 현재가) /  20, 3)
                일봉이평60  = round((일봉종가합계59  + 현재가) /  60, 3)
                일봉이평120 = round((일봉종가합계119 + 현재가) / 120, 3)
                일봉이평240 = round((일봉종가합계239 + 현재가) / 240, 3)
                hmp_ratio = round((now() - self.day_start).total_seconds() / 23400, 2)
                일봉최고거래대금대비 = round(당일거래대금 / (일봉최고거래대금 * hmp_ratio) * 100, 2) if 일봉최고거래대금 != 0 and hmp_ratio != 0. else 0.
                """ 보조지표 사용예
                D_BBU, D_BBM, D_BBL = talib.BBANDS(np.r_[self.dict_day_ar[종목코드][:, 4], np.array([현재가])], timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)
                D_BBU, D_BBM, D_BBL = D_BBU[-1], D_BBM[-1], D_BBL[-1]
                D_RSI = talib.RSI(np.r_[self.dict_day_ar[종목코드][:, 4], np.array([현재가])], timeperiod=14)[-1]
                D_CCI = talib.CCI(np.r_[self.dict_day_ar[종목코드][:, 2], np.array([고가])], np.r_[self.dict_day_ar[종목코드][:, 3], np.array([저가])], np.r_[self.dict_day_ar[종목코드][:, 4], np.array([현재가])], timeperiod=14)[-1]
                D_MACD, D_MACDS, D_MACDH = talib.MACD(np.r_[self.dict_day_ar[종목코드][:, 4], np.array([현재가])], fastperiod=12, slowperiod=26, signalperiod=9)
                D_MACD, D_MACDS, D_MACDH = D_MACD[-1], D_MACDS[-1], D_MACDH[-1]
                D_STOCK, D_STOCD = talib.STOCH(np.r_[self.dict_day_ar[종목코드][:, 2], np.array([고가])], np.r_[self.dict_day_ar[종목코드][:, 3], np.array([저가])], np.r_[self.dict_day_ar[종목코드][:, 4], np.array([현재가])], fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
                D_STOCK, D_STOCD = D_STOCK[-1], D_STOCD[-1]
                D_ATR = talib.ATR(np.r_[self.dict_day_ar[종목코드][:, 2], np.array([고가])], np.r_[self.dict_day_ar[종목코드][:, 3], np.array([저가])], np.r_[self.dict_day_ar[종목코드][:, 4], np.array([현재가])], timeperiod=14)[-1]
                """
            except Exception as e:
                self.kwzservQ.put(('window', (ui_num['S단순텍스트'], f'시스템 명령 오류 알림 - 일봉데이터 {e}')))
                return

        if 체결강도평균_ != 0 and not (매수잔량5 == 0 and 매도잔량5 == 0):
            if 종목코드 in self.df_jg.index:
                매수틱번호 = self.dict_buy_tik[종목코드] if 종목코드 in self.dict_buy_tik.keys() else len(self.dict_tik_ar[종목코드]) - 1
                매입가 = self.df_jg['매입가'][종목코드]
                보유수량 = self.df_jg['보유수량'][종목코드]
                매입금액 = self.df_jg['매입금액'][종목코드]
                분할매수횟수 = int(self.df_jg['분할매수횟수'][종목코드])
                분할매도횟수 = int(self.df_jg['분할매도횟수'][종목코드])
                _, 수익금, 수익률 = GetKiwoomPgSgSp(매입금액, 보유수량 * 현재가)
                매수시간 = strp_time('%Y%m%d%H%M%S', self.df_jg['매수시간'][종목코드])
                보유시간 = (now() - 매수시간).total_seconds()
                if 종목코드 not in self.dict_hilo.keys():
                    self.dict_hilo[종목코드] = [수익률, 수익률]
                else:
                    if 수익률 > self.dict_hilo[종목코드][0]:
                        self.dict_hilo[종목코드][0] = 수익률
                    elif 수익률 < self.dict_hilo[종목코드][1]:
                        self.dict_hilo[종목코드][1] = 수익률
                최고수익률, 최저수익률 = self.dict_hilo[종목코드]
            else:
                매수틱번호, 수익금, 수익률, 매입가, 보유수량, 분할매수횟수, 분할매도횟수, 매수시간, 보유시간, 최고수익률, 최저수익률 = 0, 0, 0, 0, 0, 0, 0, now(), 0, 0, 0

            BBT = not self.dict_set['주식매수금지시간'] or not (self.dict_set['주식매수금지시작시간'] < 시분초 < self.dict_set['주식매수금지종료시간'])
            BLK = not self.dict_set['주식매수금지블랙리스트'] or 종목코드 not in self.dict_set['주식블랙리스트']
            ING = 종목코드 in self.tuple_gsjm
            NIB = 종목코드 not in self.list_buy
            NIS = 종목코드 not in self.list_sell

            A = ING and NIB and 매입가 == 0
            B = self.dict_set['주식매수분할시그널']
            C = NIB and 매입가 != 0 and 분할매수횟수 < self.dict_set['주식매수분할횟수']
            D = NIB and self.dict_set['주식매도취소매수시그널'] and not NIS

            if BBT and BLK and (A or (B and C) or C or D):
                매수수량 = 0

                if A or (B and C) or C:
                    oc_ratio = dict_order_ratio[self.dict_set['주식매수분할방법']][self.dict_set['주식매수분할횟수']][분할매수횟수]
                    매수수량 = int(self.int_tujagm / (현재가 if 매입가 == 0 else 매입가) * oc_ratio / 100)

                if A or (B and C) or D:
                    매수 = True
                    if 시분초 < self.dict_set['주식장초전략종료시간']:
                        if self.buystrategy1 is not None:
                            try:
                                exec(self.buystrategy1, None, locals())
                            except:
                                print_exc()
                                self.kwzservQ.put(('window', (ui_num['S단순텍스트'], '시스템 명령 오류 알림 - BuyStrategy1')))
                    elif self.dict_set['주식장초전략종료시간'] <= 시분초 < self.dict_set['주식장중전략종료시간']:
                        if self.buystrategy2 is not None:
                            if not self.stg_change:
                                self.vars = self.vars2
                                self.stg_change = True
                            try:
                                exec(self.buystrategy2, None, locals())
                            except:
                                print_exc()
                                self.kwzservQ.put(('window', (ui_num['S단순텍스트'], '시스템 명령 오류 알림 - BuyStrategy2')))
                elif C:
                    매수 = False
                    분할매수기준수익률 = round((현재가 / 현재가N(-1) - 1) * 100, 2) if self.dict_set['주식매수분할고정수익률'] else 수익률
                    if self.dict_set['주식매수분할하방'] and 분할매수기준수익률 < -self.dict_set['주식매수분할하방수익률']:
                        매수 = True
                    elif self.dict_set['주식매수분할상방'] and 분할매수기준수익률 > self.dict_set['주식매수분할상방수익률']:
                        매수 = True

                    if 매수:
                        self.Buy(종목코드, 종목명, 매수수량, 현재가, 매도호가1, 매수호가1, 데이터길이)

            SBT = not self.dict_set['주식매도금지시간'] or not (self.dict_set['주식매도금지시작시간'] < 시분초 < self.dict_set['주식매도금지종료시간'])
            SCC = self.dict_set['주식매수분할횟수'] == 1 or not self.dict_set['주식매도금지매수횟수'] or 분할매수횟수 > self.dict_set['주식매도금지매수횟수값']
            NIB = 종목코드 not in self.list_buy

            A = NIB and NIS and SCC and 매입가 != 0 and self.dict_set['주식매도분할횟수'] == 1
            B = self.dict_set['주식매도분할시그널']
            C = NIB and NIS and SCC and 매입가 != 0 and 분할매도횟수 < self.dict_set['주식매도분할횟수']
            D = NIS and self.dict_set['주식매수취소매도시그널'] and not NIB
            E = NIB and NIS and 매입가 != 0 and self.dict_set['주식매도손절수익률청산'] and 수익률 < -self.dict_set['주식매도손절수익률']
            F = NIB and NIS and 매입가 != 0 and self.dict_set['주식매도손절수익금청산'] and 수익금 < -self.dict_set['주식매도손절수익금']

            if SBT and (A or (B and C) or C or D or E or F):
                매도 = False
                매도수량 = 0
                강제청산 = E or F

                if A or E or F:
                    매도수량 = 보유수량
                elif (B and C) or C:
                    oc_ratio = dict_order_ratio[self.dict_set['주식매도분할방법']][self.dict_set['주식매도분할횟수']][분할매도횟수]
                    매도수량 = int(self.int_tujagm / 매입가 * oc_ratio / 100)
                    if 매도수량 > 보유수량 or 분할매도횟수 + 1 == self.dict_set['주식매도분할횟수']: 매도수량 = 보유수량

                if A or (B and C) or D:
                    if 시분초 < self.dict_set['주식장초전략종료시간']:
                        if self.sellstrategy1 is not None:
                            try:
                                exec(self.sellstrategy1, None, locals())
                            except:
                                print_exc()
                                self.kwzservQ.put(('window', (ui_num['S단순텍스트'], '시스템 명령 오류 알림 - SellStrategy1')))
                    elif self.dict_set['주식장초전략종료시간'] <= 시분초 < self.dict_set['주식장중전략종료시간']:
                        if self.sellstrategy2 is not None:
                            try:
                                exec(self.sellstrategy2, None, locals())
                            except:
                                print_exc()
                                self.kwzservQ.put(('window', (ui_num['S단순텍스트'], '시스템 명령 오류 알림 - SellStrategy2')))
                elif C or E or F:
                    if 강제청산:
                        매도 = True
                    elif C:
                        if self.dict_set['주식매도분할하방'] and 수익률 < -self.dict_set['주식매도분할하방수익률'] * (분할매도횟수 + 1):
                            매도 = True
                        elif self.dict_set['주식매도분할상방'] and 수익률 > self.dict_set['주식매도분할상방수익률'] * (분할매도횟수 + 1):
                            매도 = True

                    if 매도:
                        self.Sell(종목코드, 종목명, 매도수량, 현재가, 매도호가1, 매수호가1, 강제청산)

        if self.dict_set['주식분봉데이터']:
            if self.dict_min_ar[종목코드][-1, 0] == 분봉체결시간:
                self.dict_min_ar[종목코드][-1, :] = 분봉체결시간, 분봉시가, 분봉고가, 분봉저가, 현재가, 분봉거래대금, 분봉이평5, 분봉이평10, 분봉이평20, 분봉이평60, 분봉이평120, 분봉이평240
                # self.dict_min_ar[종목코드][-1, :] = 분봉체결시간, 분봉시가, 분봉고가, 분봉저가, 현재가, 분봉거래대금, 분봉이평5, 분봉이평10, 분봉이평20, 분봉이평60, 분봉이평120, 분봉이평240, M_BBU, M_BBM, M_BBL, M_RSI, M_CCI, M_MACD, M_MACDS, M_MACDH, M_STOCK, M_STOCD, M_ATR
            else:
                new_data = [분봉체결시간, 분봉시가, 분봉고가, 분봉저가, 현재가, 분봉거래대금, 분봉이평5, 분봉이평10, 분봉이평20, 분봉이평60, 분봉이평120, 분봉이평240]
                # new_data = [분봉체결시간, 분봉시가, 분봉고가, 분봉저가, 현재가, 분봉거래대금, 분봉이평5, 분봉이평10, 분봉이평20, 분봉이평60, 분봉이평120, 분봉이평240, M_BBU, M_BBM, M_BBL, M_RSI, M_CCI, M_MACD, M_MACDS, M_MACDH, M_STOCK, M_STOCD, M_ATR]
                self.dict_min_ar[종목코드] = np.r_[self.dict_min_ar[종목코드], np.array([new_data])]
                if len(self.dict_min_ar[종목코드]) > self.dict_set['주식분봉개수']:
                    self.dict_min_ar[종목코드] = np.delete(self.dict_min_ar[종목코드], 0, 0)

            if self.chart_code == 종목코드:
                self.kwzservQ.put(('window', (ui_num['분봉차트'], 종목명, self.dict_min_ar[종목코드][-120:])))

        if self.dict_set['주식일봉데이터']:
            if self.dict_day_ar[종목코드][-1, 0] == 일봉일자:
                self.dict_day_ar[종목코드][-1, :] = 일봉일자, 시가, 고가, 저가, 현재가, 당일거래대금, 일봉이평5, 일봉이평10, 일봉이평20, 일봉이평60, 일봉이평120, 일봉이평240
            else:
                new_data = [일봉일자, 시가, 고가, 저가, 현재가, 당일거래대금, 일봉이평5, 일봉이평10, 일봉이평20, 일봉이평60, 일봉이평120, 일봉이평240]
                self.dict_day_ar[종목코드] = np.r_[self.dict_day_ar[종목코드], np.array([new_data])]

            if self.chart_code == 종목코드:
                self.kwzservQ.put(('window', (ui_num['일봉차트'], 종목명, self.dict_day_ar[종목코드][-120:])))

        if 종목코드 in self.tuple_gsjm:
            self.df_gj.loc[종목코드] = 종목명, 등락율, 고저평균대비등락율, 초당거래대금, 초당거래대금평균_, 당일거래대금, 체결강도, 체결강도평균_, 최고체결강도_

        if len(self.dict_tik_ar[종목코드]) >= 평균값계산틱수 and self.chart_code == 종목코드:
            self.kwzservQ.put(('window', (ui_num['실시간차트'], 종목명, self.dict_tik_ar[종목코드][-1800:, :])))

        if 틱수신시간 != 0:
            gap = (now() - 틱수신시간).total_seconds()
            self.kwzservQ.put(('window', (ui_num['S단순텍스트'], f'전략스 연산 시간 알림 - 수신시간과 연산시간의 차이는 [{gap:.6f}]초입니다.')))
