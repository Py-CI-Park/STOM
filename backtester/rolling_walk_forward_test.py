import sys
import time
import sqlite3
import numpy as np
import pandas as pd
from multiprocessing import Process, Queue
from backtester.back_static import SubTotal, SendTextAndStd, GetBackResult, GetQuery, PltShow, LoadOrderSetting
from utility.static import strf_time, now, timedelta_day, pickle_write, pickle_read, pickle_delete, strp_time, timedelta_sec
from utility.setting import ui_num, DB_STRATEGY, DB_BACKTEST, DICT_SET, DB_STOCK_BACK, DB_COIN_BACK, BACKVC_PATH


class Total:
    def __init__(self, wq, sq, tq, mq, bq, pq_list, tdq_list, vdq_list, backname, ui_gubun, gubun):
        self.wq           = wq
        self.sq           = sq
        self.tq           = tq
        self.mq           = mq
        self.bq           = bq
        self.pq_list      = pq_list
        self.tdq_list     = tdq_list
        self.vdq_list     = vdq_list
        self.backname     = backname
        self.ui_gubun     = ui_gubun
        self.gubun        = gubun
        self.dict_set     = DICT_SET
        gubun_text        = f'{self.gubun}_future' if self.ui_gubun == 'CF' else self.gubun
        self.savename     = f'{gubun_text}_{self.backname.replace("최적화", "").lower()}'

        self.start        = now()
        self.back_count   = None
        self.in_out_count = None
        self.dict_bkvc    = {}
        self.dict_bkvc_   = {}
        self.file_name    = strf_time('%Y%m%d%H%M%S')

        self.dict_cn      = None
        self.buystg_name  = None
        self.buystg       = None
        self.sellstg      = None
        self.optivars     = None
        self.list_days    = None
        self.std_list     = None
        self.optistandard = None
        self.weeks_train  = None
        self.weeks_valid  = None
        self.weeks_test   = None

        self.betting      = None
        self.startday_    = None
        self.endday_      = None
        self.startday     = None
        self.endday       = None
        self.starttime    = None
        self.endtime      = None

        self.shutdown     = None
        self.schedul      = None

        self.df_kp        = None
        self.df_kd        = None
        self.df_tsg       = None
        self.df_bct       = None
        self.arry_bct     = None

        self.df_ttsg      = []
        self.df_tbct      = []
        self.dict_train   = {}
        self.dict_valid   = {}
        self.dict_tsg1    = {}
        self.dict_tsg2    = {}
        self.dict_tsg3    = {}
        self.dict_tsg4    = {}
        self.dict_tsg5    = {}
        self.dict_tsg6    = {}
        self.dict_tsg7    = {}
        self.dict_tsg8    = {}
        self.dict_tsg9    = {}
        self.dict_tsg10   = {}
        self.dict_tsg11   = {}
        self.dict_tsg12   = {}
        self.dict_tsg13   = {}

        self.list_del_vc  = []

        self.hstd_list    = None
        self.last_vars    = None
        self.vars         = None
        self.varc         = None
        self.stdp         = -100_000_000_000
        self.sub_total    = 0
        self.total_count  = 0

        self.Start()

    def Start(self):
        st  = 0
        oc  = 0
        tc  = 0
        bc  = 0
        tbc = 0
        while True:
            data = self.tq.get()
            if data[0] == '백테결과':
                if self.dict_cn is not None:
                    name = self.dict_cn[data[1]] if data[1] in self.dict_cn.keys() else data[1]
                else:
                    name = data[1]
                index = str(data[3]) if self.dict_set['백테매수시간기준'] else str(data[4])
                while index in self.dict_tsg1.keys():
                    index = strf_time('%Y%m%d%H%M%S', timedelta_sec(1, strp_time('%Y%m%d%H%M%S', index)))
                self.dict_tsg1[index]  = name
                self.dict_tsg2[index]  = data[2]
                self.dict_tsg3[index]  = data[3]
                self.dict_tsg4[index]  = data[4]
                self.dict_tsg5[index]  = data[5]
                self.dict_tsg6[index]  = data[6]
                self.dict_tsg7[index]  = data[7]
                self.dict_tsg8[index]  = data[8]
                self.dict_tsg9[index]  = data[9]
                self.dict_tsg10[index] = data[10]
                self.dict_tsg11[index] = data[11]
                self.dict_tsg12[index] = data[12]
                self.dict_tsg13[index] = data[13]
                if data[14] and self.arry_bct is not None:
                    arry_bct = self.arry_bct[(self.arry_bct[:, 0] >= data[3]) & (self.arry_bct[:, 0] <= data[4])]
                    arry_bct[:, 1] += 1
                    self.arry_bct[(self.arry_bct[:, 0] >= data[3]) & (self.arry_bct[:, 0] <= data[4])] = arry_bct
            elif data[0] == '백테완료':
                bc  += 1
                tbc += 1
                if data[1]: tc += 1
                self.wq.put([ui_num[f'{self.ui_gubun}백테바'], tbc, self.total_count, self.start])

                if bc == self.back_count:
                    columns = ['종목명', '시가총액' if self.ui_gubun != 'CF' else '포지션', '매수시간', '매도시간', '보유시간',
                               '매수가', '매도가', '매수금액', '매도금액', '수익률', '수익금', '매도조건', '추가매수시간']
                    self.df_tsg = pd.DataFrame(
                        dict(zip(columns,
                                 [self.dict_tsg1.values(), self.dict_tsg2.values(), self.dict_tsg3.values(),
                                  self.dict_tsg4.values(), self.dict_tsg5.values(), self.dict_tsg6.values(),
                                  self.dict_tsg7.values(), self.dict_tsg8.values(), self.dict_tsg9.values(),
                                  self.dict_tsg10.values(), self.dict_tsg11.values(), self.dict_tsg12.values(),
                                  self.dict_tsg13.values()])),
                        index=list(self.dict_tsg1.keys())
                    )
                    self.df_tsg.sort_index(inplace=True)
                    arry_bct    = self.arry_bct[self.arry_bct[:, 1] > 0]
                    self.df_bct = pd.DataFrame(arry_bct[:, 1], columns=['보유종목수'], index=arry_bct[:, 0])

                    if self.hstd_list is None:
                        df_tsg, df_bct = None, None
                        if f'{self.vars}' in self.dict_bkvc.keys():
                            df_tsg, df_bct = self.dict_bkvc[f'{self.vars}']
                        if df_tsg is not None:
                            self.df_tsg = pd.concat([df_tsg, self.df_tsg])
                            self.df_bct = pd.concat([df_bct, self.df_bct])

                        data = [self.df_tsg, self.df_bct]
                        train_days, valid_days, test_days = self.list_days[self.in_out_count]
                        if valid_days is not None:
                            for i, vdays in enumerate(valid_days):
                                data_ = data + [vdays[0], vdays[1], test_days[0], train_days[2] - vdays[2], vdays[2], i]
                                self.tdq_list[i].put(data_)
                                self.vdq_list[i].put(data_)
                        else:
                            data_ = data + [train_days[1], int(train_days[2] / 2)]
                            self.tdq_list[0].put(data_)
                            self.vdq_list[0].put(data_)

                        if tc > 0:
                            self.dict_bkvc_[f'{self.vars}'] = data
                            for pq in self.pq_list:
                                pq.put(['이전데이터날짜갱신', f'{self.vars}', self.endday])
                    else:
                        bc  = 0
                        oc += 1
                        self.df_ttsg.append(self.df_tsg)
                        self.df_tbct.append(self.df_bct)
                        self.Report(oc)
                        self.InitData()
            elif data[0] in ['TRAIN', 'VALID']:
                if data[0] == 'TRAIN':
                    self.dict_train[data[1]] = data[2]
                else:
                    self.dict_valid[data[1]] = data[2]
                st += 1
                if st == self.sub_total:
                    self.stdp = SendTextAndStd(self.GetSendData(), self.std_list, self.betting, self.dict_train, self.dict_valid, self.dict_set['교차검증가중치'])
                    self.InitData()
                    st = 0
                    tc = 0
                    bc = 0
            elif data[0] == '백테정보':
                self.BackInfo(data)
            elif data[0] == '변수정보':
                self.vars = data[1]
                self.varc = data[2]
            elif data[0] == '재최적화':
                self.start = now()
                tbc = 0
            elif data[0] == '경우의수':
                self.SaveBackData()
                self.total_count  = data[1]
                self.back_count   = data[2]
                self.startday     = data[3]
                self.endday       = data[4]
                self.in_out_count = data[5]
                self.stdp         = -100_000_000_000
                self.LoadBackVcData([self.betting, self.startday, self.endday, self.starttime, self.endtime, self.buystg, self.sellstg])
            elif data[0] == '최적화정보':
                self.hstd_list = data[1]
                self.last_vars = data[2]
            elif data == '이전데이터정리':
                if self.dict_bkvc_:
                    self.dict_bkvc  = self.dict_bkvc_
                    self.dict_bkvc_ = {}
            elif data == '백테중지':
                if self.tdq_list:
                    for q in self.tdq_list:
                        q.put('서브집계프로세스종료')
                    for q in self.vdq_list:
                        q.put('서브집계프로세스종료')
                self.mq.put('백테중지')
                self.SaveBackData()
                break

        time.sleep(1)
        sys.exit()

    def LoadBackVcData(self, data):
        betting, startday, endday, starttime, endtime, buystg, sellstg = data
        buy_setting, sell_setting = LoadOrderSetting(self.ui_gubun)
        dict_days = {}
        con = sqlite3.connect(DB_BACKTEST)
        try:
            df = pd.read_sql('SELECT * FROM back_vc_list', con)
            if not self.dict_set['백테주문관리적용']:
                df = df[(df['매수전략'] == buystg) & (df['매도전략'] == sellstg) & (df['시작일자'] == startday) &
                        (df['종료일자'] <= endday) & (df['시작시간'] == starttime) & (df['종료시간'] == endtime) &
                        (df['배팅금액'] == betting) & (df['주관적용'] == 0)]
            else:
                df = df[(df['매수전략'] == buystg) & (df['매도전략'] == sellstg) & (df['시작일자'] == startday) &
                        (df['종료일자'] <= endday) & (df['시작시간'] == starttime) & (df['종료시간'] == endtime) &
                        (df['배팅금액'] == betting) & (df['주관적용'] == 1) & (df['매수주관'] == buy_setting) & (df['매도주관'] == sell_setting)]
            if len(df) > 0:
                df.sort_values(by=['index', '종료일자'], ascending=False, inplace=True)
                df.set_index('index', inplace=True)
                for file_name in df.index:
                    dict_data = pickle_read(f'{BACKVC_PATH}/{file_name}')
                    if dict_data is not None:
                        self.list_del_vc.append(file_name)
                        vars_day = df['종료일자'][file_name]
                        for key, value in dict_data.items():
                            if key not in self.dict_bkvc.keys():
                                self.dict_bkvc[key] = value
                                dict_days[key] = vars_day
                    self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'이전 최적화 데이터 로딩 중 ... {file_name}'])
        except:
            pass
        con.close()

        if dict_days != {}:
            for pq in self.pq_list:
                pq.put(['이전데이터갱신', dict_days])

    def SaveBackData(self):
        if self.list_del_vc:
            con = sqlite3.connect(DB_BACKTEST)
            cur = con.cursor()
            for file_name in self.list_del_vc:
                pickle_delete(f'{BACKVC_PATH}/{file_name}')
                cur.execute(f'DELETE FROM back_vc_list WHERE "index" = "{file_name}"')
            con.commit()
            con.close()

        order_back = self.dict_set['백테주문관리적용']
        buy_setting, sell_setting = LoadOrderSetting(self.ui_gubun)
        if len(self.dict_bkvc_) > 0:
            df = pd.DataFrame(
                dict(zip(['배팅금액', '시작일자', '종료일자', '시작시간', '종료시간', '매수전략', '매도전략', '주관적용', '매수주관', '매도주관'],
                         [self.betting, self.startday, self.endday, self.starttime, self.endtime, self.buystg, self.sellstg, order_back, buy_setting, sell_setting])),
                index=[self.file_name]
            )
            con = sqlite3.connect(DB_BACKTEST)
            df.to_sql('back_vc_list', con, if_exists='append', chunksize=1000)
            con.close()
            try:
                pickle_write(f'{BACKVC_PATH}/{self.file_name}', self.dict_bkvc_)
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '최적화 과정 데이터 저장 완료'])
            except:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '최적화 과정 데이터 저장 실패 : 데이터 크기 초과'])
            self.dict_bkvc_ = {}

    def InitData(self):
        self.dict_train = {}
        self.dict_valid = {}
        self.dict_tsg1  = {}
        self.dict_tsg2  = {}
        self.dict_tsg3  = {}
        self.dict_tsg4  = {}
        self.dict_tsg5  = {}
        self.dict_tsg6  = {}
        self.dict_tsg7  = {}
        self.dict_tsg8  = {}
        self.dict_tsg9  = {}
        self.dict_tsg10 = {}
        self.dict_tsg11 = {}
        self.dict_tsg12 = {}
        self.dict_tsg13 = {}
        self.arry_bct[:, 1] = 0

    def BackInfo(self, data):
        self.betting      = data[1]
        self.startday_    = data[2]
        self.endday_      = data[3]
        self.starttime    = data[4]
        self.endtime      = data[5]
        self.buystg_name  = data[6]
        self.buystg       = data[7]
        self.sellstg      = data[8]
        self.optivars     = data[9]
        self.dict_cn      = data[10]
        self.list_days    = data[11]
        self.std_list     = data[12]
        self.optistandard = data[13]
        self.schedul      = data[14]
        self.arry_bct     = data[15]
        self.df_kp        = data[16]
        self.df_kd        = data[17]
        self.weeks_train  = data[18]
        self.weeks_valid  = data[19]
        self.weeks_test   = data[20]
        if self.list_days[0][1] is not None:
            self.sub_total = len(self.list_days[0][1]) * 2
        else:
            self.sub_total = 2

    def GetSendData(self):
        return ['전진분석', self.ui_gubun, self.wq, self.mq, self.stdp, self.optistandard, self.varc, self.vars, self.startday, self.endday]

    def Report(self, oc):
        tc = len(self.df_tsg)
        if tc > 0:
            pc     = len(self.df_tsg[self.df_tsg['수익률'] >= 0])
            wr     = round(pc / tc * 100, 2)
            tsg    = int(self.df_tsg['수익금'].sum())
            df_bct = self.df_bct.sort_values(by=['보유종목수'], ascending=False)
            mhct   = df_bct['보유종목수'].iloc[int(len(self.df_bct) * 0.01):].max()
            onegm  = int(self.betting * mhct) if int(self.betting * mhct) > self.betting else self.betting
            tsp    = round(tsg / onegm * 100, 2)
        else:
            wr     = 0
            tsg    = 0
            mhct   = 0
            tsp    = 0.

        startday = self.hstd_list[oc - 1][0]
        endday   = self.hstd_list[oc - 1][1]
        merge    = self.hstd_list[oc - 1][2]

        text1 = f'[IN] P[{startday}~{endday}] {self.vars} MERGE[{merge:,.2f}]'
        text2 = f'[OUT] P[{self.startday}~{self.endday}] TC[{tc}] MH[{mhct}] WR[{wr:.2f}%] TP[{tsp:.2f}%] TG[{tsg:,.0f}]'
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], text1])
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], text2])

        if oc < self.in_out_count:
            self.mq.put('아웃샘플 백테스트')

        if oc == self.in_out_count:
            self.df_ttsg = pd.concat(self.df_ttsg)
            self.df_tbct = pd.concat(self.df_tbct)

            df_ttsg = self.df_ttsg[['수익금']].copy()
            df_ttsg['index'] = df_ttsg.index
            df_ttsg['index'] = df_ttsg['index'].apply(lambda x: x[:8])
            out_day_count = len(list(set(df_ttsg['index'].to_list())))

            self.df_ttsg, self.df_tbct, result = GetBackResult(self.df_ttsg, self.df_tbct, self.betting, self.optistandard, out_day_count)
            tc, atc, pc, mc, wr, ah, ap, tsp, tsg, mhct, onegm, cagr, tpi, mdd = result

            startday, endday, starttime, endtime = str(self.startday_), str(self.endday_), str(self.starttime).zfill(6), str(self.endtime).zfill(6)
            startday  = startday[:4] + '-' + startday[4:6] + '-' + startday[6:]
            endday    = endday[:4] + '-' + endday[4:6] + '-' + endday[6:]
            starttime = starttime[:2] + ':' + starttime[2:4] + ':' + starttime[4:]
            endtime   = endtime[:2] + ':' + endtime[2:4] + ':' + endtime[4:]
            bet_unit  = '원' if self.ui_gubun != 'CF' else 'USDT'

            if self.weeks_valid == 0:
                back_text = f'백테기간 : {startday}~{endday}, 백테시간 : {starttime}~{endtime}, 학습+검증/확인기간 : {self.weeks_train}/{self.weeks_test}, 거래일수 : {out_day_count}'
            else:
                back_text = f'백테기간 : {startday}~{endday}, 백테시간 : {starttime}~{endtime}, 학습/검증/확인기간 : {self.weeks_train}/{self.weeks_valid}/{self.weeks_test}, 거래일수 : {out_day_count}'

            mdd_       = f'최대낙폭금액 {mdd:,.0f}{bet_unit}' if 'G' in self.optistandard else f'최대낙폭률 {mdd:,.2f}%'
            label_text = f'종목당 배팅금액 {int(self.betting):,}{bet_unit}, 필요자금 {onegm:,}{bet_unit}, ' \
                         f'거래횟수 {tc}회, 일평균거래횟수 {atc}회, 적정최대보유종목수 {mhct}개, 평균보유기간 {ah:.2f}초\n' \
                         f'익절 {pc}회, 손절 {mc}회, 승률 {wr:.2f}%, 평균수익률 {ap:.2f}%, 수익률합계 {tsp:.2f}%, ' \
                         f'{mdd_}, 수익금합계 {tsg:,}{bet_unit}, 매매성능지수 {tpi:.2f}, 연간예상수익률 {cagr:.2f}%'

            save_file_name = f"{self.savename}_{self.buystg_name}_{self.optistandard}_{self.file_name}"
            con = sqlite3.connect(DB_BACKTEST)
            self.df_ttsg.to_sql(save_file_name, con, if_exists='append', chunksize=1000)
            con.close()
            self.wq.put([ui_num[f'{self.ui_gubun.replace("F", "")}상세기록'], self.df_ttsg])

            self.SaveBackData()
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 아웃샘플 백테스터 완료'])
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 백테스트 소요시간 {now() - self.start}'])
            self.sq.put(f'{self.backname} 백테스트를 완료하였습니다.')

            PltShow('전진분석', self.df_ttsg, self.df_tbct, self.dict_cn, onegm, mdd, self.startday, self.endday, self.starttime, self.endtime,
                    self.df_kp, self.df_kd, self.list_days, self.backname, back_text, label_text, save_file_name, self.schedul, False)
            self.mq.put('백테스트 완료')


class RollingWalkForwardTest:
    def __init__(self, wq, bq, sq, tq, lq, pq_list, backname, ui_gubun):
        self.wq        = wq
        self.bq        = bq
        self.sq        = sq
        self.tq        = tq
        self.lq        = lq
        self.pq_list   = pq_list
        self.backname  = backname
        self.ui_gubun  = ui_gubun
        self.dict_set  = DICT_SET
        self.gubun     = 'stock' if self.ui_gubun == 'S' else 'coin'
        self.vars      = {}
        self.high_vars = []
        self.Start()

    def Start(self):
        data = self.bq.get()
        if self.ui_gubun != 'CF':
            betting = float(data[0]) * 1000000
        else:
            betting = float(data[0])
        startday    = int(data[1])
        endday      = int(data[2])
        starttime   = int(data[3])
        endtime     = int(data[4])
        buystg_name     = data[5]
        sellstg_name    = data[6]
        optivars_name   = data[7]
        dict_cn         = data[8]
        ccount      = int(data[9])
        std_text        = data[10].split(';')
        std_text        = [float(x) for x in std_text]
        optistandard    = data[11]
        back_count      = data[12]
        schedul         = data[13]
        df_kp           = data[14]
        df_kd           = data[15]
        weeks_train = int(data[16])
        weeks_valid = int(data[17])
        weeks_test  = int(data[18])
        backengin_sday  = data[19]
        backengin_eday  = data[20]

        if 'V' in self.backname:
            int_day = int(strf_time('%Y%m%d', timedelta_day(-(weeks_train + weeks_valid + weeks_test + 1) * 7 + 1, strp_time('%Y%m%d', str(endday)))))
            if int(backengin_sday) > int_day or startday > int_day or endday > int(backengin_eday):
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 + 검증기간 + 확인기간 * 2 만큼의 데이터가 필요합니다'])
                self.SysExit(True)
        else:
            int_day = int(strf_time('%Y%m%d', timedelta_day(-(weeks_train + weeks_test + 1) * 7 + 1, strp_time('%Y%m%d', str(endday)))))
            if int(backengin_sday) > int_day or startday > int_day or endday > int(backengin_eday):
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 + 확인기간 * 2 만큼의 데이터가 필요합니다'])
                self.SysExit(True)

        con   = sqlite3.connect(DB_STOCK_BACK if self.ui_gubun == 'S' else DB_COIN_BACK)
        query = GetQuery(self.ui_gubun, startday, endday, starttime, endtime)
        df_mt = pd.read_sql(query, con)
        con.close()

        if len(df_mt) == 0 or back_count == 0:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '날짜 지정이 잘못되었거나 데이터가 존재하지 않습니다.\n'])
            self.SysExit(True)

        df_mt['일자'] = df_mt['index'].apply(lambda x: int(str(x)[:8]))
        day_list = list(set(df_mt['일자'].to_list()))
        day_list.sort()

        if 'V' not in self.backname: weeks_valid = 0

        k = 0
        list_days_ = []
        dt_endday  = strp_time('%Y%m%d', str(endday))
        startday_  = int(strf_time('%Y%m%d', timedelta_day(-(weeks_train + weeks_valid + weeks_test) * 7 + 1, dt_endday)))
        while startday_ >= startday:
            train_days = [
                startday_,
                int(strf_time('%Y%m%d', timedelta_day(-weeks_test * (k + 1) * 7, dt_endday)))
            ]
            valid_days = []
            if 'VC' in self.backname:
                for i in range(int(weeks_train / weeks_valid) + 1):
                    valid_days.append([
                        int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid * (i + 1) + weeks_test * (k + 1)) * 7 + 1, dt_endday))),
                        int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid * i + weeks_test * (k + 1)) * 7, dt_endday)))
                    ])
            elif 'V' in self.backname:
                valid_days.append([
                    int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid + weeks_test * (k + 1)) * 7 + 1, dt_endday))),
                    int(strf_time('%Y%m%d', timedelta_day(-(weeks_test * (k + 1)) * 7, dt_endday)))
                ])
            else:
                valid_days = None
            test_days = [
                int(strf_time('%Y%m%d', timedelta_day(-(weeks_test * (k + 1)) * 7 + 1, dt_endday))),
                int(strf_time('%Y%m%d', timedelta_day(-(weeks_test * k) * 7, dt_endday)))
            ]
            list_days_.append([train_days, valid_days, test_days])
            k += 1
            startday_ = int(strf_time('%Y%m%d', timedelta_day(-(weeks_train + weeks_valid + weeks_test * (k + 1)) * 7 + 1)))

        list_days = []
        for train_days, valid_days, test_days in list_days_:
            train_days_list = [x for x in day_list if train_days[0] <= x <= train_days[1]]
            train_days  = [train_days_list[0], train_days_list[-1], len(train_days_list)]
            valid_days_ = []
            if 'V' in self.backname:
                for vsday, veday in valid_days:
                    valid_days_list = [x for x in day_list if vsday <= x <= veday]
                    valid_days_.append([valid_days_list[0], valid_days_list[-1], len(valid_days_list)])
            else:
                valid_days_ = None
            test_days_list = [x for x in day_list if test_days[0] <= x <= test_days[1]]
            test_days = [test_days_list[0], test_days_list[-1]]
            list_days.append([train_days, valid_days_, test_days])

        list_days = list_days[::-1]
        for i, data in enumerate(list_days):
            train_days, valid_days, test_days = data
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 학습기간 {i + 1} : {train_days[0]} ~ {train_days[1]}'])
            if 'V' in self.backname:
                for vsday, veday, _ in valid_days:
                    self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 검증기간 {i + 1} : {vsday} ~ {veday}'])
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 확인기간 {i + 1} : {test_days[0]} ~ {test_days[1]}'])
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 일자 추출 완료'])

        arry_bct = np.zeros((len(df_mt), 2), dtype='int64')
        arry_bct[:, 0] = df_mt['index'].values
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 보유종목수 어레이 생성 완료'])

        con = sqlite3.connect(DB_STRATEGY)
        df = pd.read_sql(f'SELECT * FROM {self.gubun}optibuy', con).set_index('index')
        buystg = df['전략코드'][buystg_name]
        df = pd.read_sql(f'SELECT * FROM {self.gubun}optisell', con).set_index('index')
        sellstg = df['전략코드'][sellstg_name]
        df = pd.read_sql(f'SELECT * FROM {self.gubun}optivars', con).set_index('index')
        optivars = df['전략코드'][optivars_name]
        con.close()

        optivars_ = compile(optivars, '<string>', 'exec')
        try:
            exec(optivars_, None, locals())
        except Exception as e:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'시스템 명령 오류 알림 - 최적화 변수설정 1단계 {e}'])
            self.SysExit(True)

        vars_type   = []
        total_count = 1
        vars_       = list(self.vars.values())
        vars_zero   = [x[0][0] for x in vars_]
        for var in vars_:
            vars_type.append('오름차순' if var[0][0] < var[0][1] else '내림차순')
            if var[0][2] != 0:
                total_count += int((var[0][1] - var[0][0]) / var[0][2])
        total_count *= ccount if ccount != 0 else 1
        total_count *= len(list_days)
        total_count *= back_count
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 매도수전략 설정 완료'])

        if vars_[0][0][2] == 0:
            avg_list = [vars_[0][0][0]]
        else:
            avg_list = [x for x in range(vars_[0][0][0], vars_[0][0][1] + vars_[0][0][2], vars_[0][0][2])]

        mq = Queue()
        tdq_list = []
        vdq_list = []
        if 'V' in self.backname:
            for _ in list_days[0][1]:
                tdq, vdq = Queue(), Queue()
                tdq_list.append(tdq)
                vdq_list.append(vdq)
                Process(target=SubTotal, args=(self.tq, tdq, betting, optistandard, 1)).start()
                Process(target=SubTotal, args=(self.tq, vdq, betting, optistandard, 0)).start()
        else:
            tdq, vdq = Queue(), Queue()
            tdq_list.append(tdq)
            vdq_list.append(vdq)
            Process(target=SubTotal, args=(self.tq, tdq, betting, optistandard, 1)).start()
            Process(target=SubTotal, args=(self.tq, vdq, betting, optistandard, 0)).start()
        Process(target=Total, args=(self.wq, self.sq, self.tq, mq, self.bq, self.pq_list, tdq_list, vdq_list, self.backname, self.ui_gubun, self.gubun)).start()
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 집계용 프로세스 생성 완료'])

        self.tq.put(['백테정보', betting, startday, endday, starttime, endtime, buystg_name, buystg, sellstg, optivars,
                     dict_cn, list_days, std_text, optistandard, schedul, arry_bct, df_kp, df_kd, weeks_train, weeks_valid, weeks_test])
        for pq in self.pq_list:
            pq.put(['백테정보', betting, avg_list, starttime, endtime, buystg, sellstg])

        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 인샘플 최적화 시작'])

        hstd_list = []
        hvar_list = []
        for j, data in enumerate(list_days):
            train_days, valid_days, test_days = data
            startday, endday = train_days[0], train_days[1]
            k     = 1
            hstd  = None
            change_var_count = None
            self.tq.put(['경우의수', total_count, back_count, startday, endday, j])

            for _ in range(ccount if ccount != 0 else 100):
                if ccount == 0:
                    if change_var_count == 0:
                        break
                    if k > 1:
                        self.tq.put(['재최적화'])
                        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'무한모드 {k}단계 시작, 최적값 변경 개수 [{change_var_count}]'])

                self.tq.put('이전데이터정리')

                change_var_count = 0
                for i, x in enumerate(vars_zero):
                    vars_[i][0][0] = x
                cur_vars = [var[1] for var in vars_]
                self.tq.put(['변수정보', cur_vars, -1])
                for pq in self.pq_list:
                    pq.put(['변수정보', cur_vars, startday, endday, False])

                hstd = mq.get()
                if type(hstd) != str:
                    self.high_vars = vars_[0][1]
                else:
                    self.SysExit(True)

                i    = 0
                last = len(vars_) - 1
                while True:
                    if vars_[i][0][2] != 0 and vars_[i][0][0] != vars_[i][1]:
                        cur_vars = [var[0][0] if j == i else var[1] for j, var in enumerate(vars_)]
                        self.tq.put(['변수정보', cur_vars, i])
                        for pq in self.pq_list:
                            pq.put(['변수정보', cur_vars, startday, endday, False])

                        std = mq.get()
                        if type(std) != str:
                            if std > hstd or (std == hstd and ((vars_type[i] == '오름차순' and vars_[i][0][0] > vars_[i][1]) or (vars_type[i] == '내림차순' and vars_[i][0][0] < vars_[i][1]))):
                                hstd = std
                                self.high_vars = vars_[i][0][0]
                        else:
                            self.SysExit(True)

                    if vars_[i][0][0] == vars_[i][0][1]:
                        if vars_[i][1] != self.high_vars:
                            vars_[i][1] = self.high_vars
                            change_var_count += 1
                        if i < last:
                            i += 1
                            self.high_vars = vars_[i][1]
                        else:
                            break
                    else:
                        vars_[i][0][0] = round(vars_[i][0][0] + vars_[i][0][2], 1)
                k += 1

            hvar_list.append([x[1] for x in vars_])
            hstd_list.append([startday, endday, hstd])
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 인샘플 최적화 완료'])

        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 아웃샘플 백테스터 시작'])
        if hvar_list: self.tq.put(['최적화정보', hstd_list, hvar_list[-1]])

        oc = len(list_days)
        for i, data in enumerate(list_days):
            startday, endday = data[2]
            self.tq.put(['경우의수', total_count, back_count, startday, endday, oc])
            self.tq.put(['변수정보', hvar_list[i], -2])
            for pq in self.pq_list:
                pq.put(['변수정보', hvar_list[i], startday, endday, True])
            _ = mq.get()

        mq.close()
        if self.dict_set['스톰라이브']: self.lq.put(self.backname)
        self.SysExit(False)

    def SysExit(self, cancel):
        if cancel:
            self.wq.put([ui_num[f'{self.ui_gubun}백테바'], 0, 100, 0])
        else:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 완료'])
        time.sleep(1)
        sys.exit()
