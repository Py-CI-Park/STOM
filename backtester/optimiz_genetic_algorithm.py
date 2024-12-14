import sys
import time
import random
import sqlite3
import operator
import numpy as np
import pandas as pd
from multiprocessing import Process, Queue
from backtester.back_static import GetBackResult, SubTotal, SendTextAndStd, GetQuery, LoadOrderSetting
from utility.static import strf_time, now, pickle_read, pickle_write, timedelta_day, timedelta_sec, strp_time
from utility.setting import DB_STOCK_BACK, ui_num, DB_STRATEGY, DB_BACKTEST, BACKVC_PATH, DICT_SET, DB_COIN_BACK


class Total:
    def __init__(self, wq, tq, mq, pq_list, tdq_list, vdq_list, ui_gubun):
        self.wq           = wq
        self.tq           = tq
        self.mq           = mq
        self.pq_list      = pq_list
        self.tdq_list     = tdq_list
        self.vdq_list     = vdq_list
        self.ui_gubun     = ui_gubun
        self.dict_set     = DICT_SET

        self.start        = now()
        self.back_count   = None
        self.dict_bkvc    = {}
        self.dict_bkvc_   = {}
        self.file_name    = strf_time('%Y%m%d%H%M%S')

        self.dict_cn      = None
        self.buystg       = None
        self.sellstg      = None
        self.std_list     = None
        self.optistandard = None
        self.day_count    = None

        self.betting      = None
        self.startday     = None
        self.endday       = None
        self.valid_days   = None
        self.starttime    = None
        self.endtime      = None

        self.df_kp        = None
        self.df_kd        = None

        self.df_tsg       = None
        self.df_bct       = None
        self.arry_bct     = None

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

        self.vars         = None
        self.stdp         = -100_000_000_000
        self.sub_total    = 0
        self.total_count  = 0

        self.Start()

    def Start(self):
        st  = 0
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

                    if self.valid_days is not None:
                        df_tsg, df_bct = None, None
                        if f'{self.vars}' in self.dict_bkvc_.keys():
                            df_tsg, df_bct = self.dict_bkvc_[f'{self.vars}']
                        elif f'{self.vars}' in self.dict_bkvc.keys():
                            df_tsg, df_bct = self.dict_bkvc[f'{self.vars}']
                        if df_tsg is not None:
                            self.df_tsg = pd.concat([df_tsg, self.df_tsg])
                            self.df_bct = pd.concat([df_bct, self.df_bct])

                        data = [self.df_tsg, self.df_bct]
                        for i, vdays in enumerate(self.valid_days):
                            data_ = data + [vdays[0], vdays[1], vdays[2], vdays[3], i]
                            self.tdq_list[i].put(data_)
                            self.vdq_list[i].put(data_)

                        if tc > 0:
                            self.dict_bkvc_[f'{self.vars}'] = data
                            for pq in self.pq_list:
                                pq.put(['이전데이터날짜갱신', f'{self.vars}', self.endday])
                    else:
                        _, _, result = GetBackResult(self.df_tsg, self.df_bct, self.betting, self.optistandard, self.day_count)
                        self.stdp = SendTextAndStd(self.GetSendData(), self.std_list, self.betting, result)
                        self.InitData()
                        bc = 0
            elif data[0] == 'TRAIN':
                self.dict_train[data[1]] = data[2]
                st += 1
                if st == self.sub_total:
                    self.stdp = SendTextAndStd(self.GetSendData(), self.std_list, self.betting, self.dict_train, self.dict_valid, self.dict_set['교차검증가중치'])
                    self.InitData()
                    st = 0
                    tc = 0
                    bc = 0
            elif data[0] == 'VALID':
                self.dict_valid[data[1]] = data[2]
                st += 1
                if st == self.sub_total:
                    self.stdp = SendTextAndStd(self.GetSendData(), self.std_list, self.betting, self.dict_train, self.dict_valid, self.dict_set['교차검증가중치'])
                    self.InitData()
                    st = 0
                    bc = 0
            elif data[0] == '백테정보':
                self.BackInfo(data)
            elif data[0] == '변수정보':
                self.vars = data[1]
            elif data[0] == '시작시간':
                self.start = data[1]
                tbc = 0
            elif data[0] == '경우의수':
                self.total_count = data[1]
                self.back_count  = data[2]
            elif data[0] == '이전데이터로딩':
                self.LoadBackVcData(data[1:])
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
                        vars_day = df['종료일자'][file_name]
                        for key, value in dict_data.items():
                            if key not in self.dict_bkvc.keys():
                                self.dict_bkvc[key] = value
                                dict_days[key] = vars_day
                    self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'이전 최적화 데이터 로딩 중 ... {file_name}'])
        except:
            pass
        con.close()
        self.mq.put(dict_days)

    def SaveBackData(self):
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
        self.startday     = data[2]
        self.endday       = data[3]
        self.starttime    = data[4]
        self.endtime      = data[5]
        self.buystg       = data[6]
        self.sellstg      = data[7]
        self.dict_cn      = data[8]
        self.std_list     = data[9]
        self.optistandard = data[10]
        self.arry_bct     = data[11]
        self.valid_days   = data[12]
        self.day_count    = data[13]
        if self.valid_days is not None:
            self.sub_total = len(self.valid_days) * 2
        else:
            self.sub_total = 2

    def GetSendData(self):
        return ['GA최적화', self.ui_gubun, self.wq, self.mq, self.stdp, self.optistandard, None, self.vars, self.startday, self.endday]


class OptimizeGeneticAlgorithm:
    def __init__(self, wq, bq, sq, tq, lq, pq_list, backname, ui_gubun):
        self.wq          = wq
        self.bq          = bq
        self.sq          = sq
        self.tq          = tq
        self.lq          = lq
        self.pq_list     = pq_list
        self.backname    = backname
        self.ui_gubun    = ui_gubun
        self.fixed_list  = []
        self.opti_list   = []
        self.vars_list   = []
        self.high_vars   = []
        self.result      = {}
        self.vars        = {}
        self.total_count = 0
        self.dict_set    = DICT_SET
        self.gubun       = 'stock' if self.ui_gubun == 'S' else 'coin'
        self.savename    = f'{self.gubun}_{self.backname.replace("최적화", "").lower()}'
        self.Start()

    def Start(self):
        data = self.bq.get()
        if self.ui_gubun != 'CF':
            betting = float(data[0]) * 1000000
        else:
            betting = float(data[0])
        starttime   = int(data[1])
        endtime     = int(data[2])
        buystg_name     = data[3]
        sellstg_name    = data[4]
        optivars_name   = data[5]
        dict_cn         = data[6]
        std_text        = data[7].split(';')
        std_text        = [float(x) for x in std_text]
        optistandard    = data[8]
        back_count      = data[9]
        weeks_train     = data[10]
        weeks_valid = int(data[11])
        _           = int(data[12])
        backengin_sday  = data[13]
        backengin_eday  = data[14]
        if weeks_train != 'ALL':
            weeks_train = int(weeks_train)
        else:
            allweeks = int(((strp_time('%Y%m%d', backengin_eday) - strp_time('%Y%m%d', backengin_sday)).days + 1) / 7)
            if 'V' in self.backname:
                weeks_train = allweeks - weeks_valid
            else:
                weeks_train = allweeks

        if 'V' not in self.backname: weeks_valid = 0
        dt_endday   = strp_time('%Y%m%d', backengin_eday)
        startday    = timedelta_day(-(weeks_train + weeks_valid) * 7 + 1, dt_endday)
        sweek       = startday.weekday()
        if sweek != 0: startday = timedelta_day(7 - sweek, startday)
        startday    = int(strf_time('%Y%m%d', startday))
        endday      = int(backengin_eday)
        valid_days_ = []
        if 'VC' in self.backname:
            for i in range(int(weeks_train / weeks_valid) + 1):
                valid_days_.append([
                    int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid * 7 * (i + 1)) + 1, dt_endday))),
                    int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid * 7 * i), dt_endday)))
                ])
        elif 'V' in self.backname:
            valid_days_.append([int(strf_time('%Y%m%d', timedelta_day(-weeks_valid * 7 + 1, dt_endday))), endday])
        else:
            valid_days_ = None

        if int(backengin_sday) > startday:
            if 'V' in self.backname:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 + 검증기간 만큼의 데이터가 필요합니다'])
            else:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 만큼의 데이터가 필요합니다'])
            self.SysExit(True)

        con   = sqlite3.connect(DB_STOCK_BACK if self.ui_gubun == 'S' else DB_COIN_BACK)
        query = GetQuery(self.ui_gubun, startday, endday, starttime, endtime)
        df_mt = pd.read_sql(query, con)
        con.close()

        if len(df_mt) == 0 or back_count == 0:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '날짜 지정이 잘못되었거나 데이터가 존재하지 않습니다.\n'])
            self.SysExit(True)

        df_mt['일자'] = df_mt['index'].apply(lambda x: int(str(x)[:8]))
        day_list  = list(set(df_mt['일자'].to_list()))
        day_list.sort()

        valid_days = None
        startday, endday = day_list[0], day_list[-1]
        train_count = len([x for x in day_list if startday <= x <= endday])
        if 'V' in self.backname:
            valid_days = []
            for vsday, veday in valid_days_:
                valid_days_list = [x for x in day_list if vsday <= x <= veday]
                vdaycnt = len(valid_days_list)
                tdaycnt = train_count - vdaycnt
                valid_days.append([valid_days_list[0], valid_days_list[-1], tdaycnt, vdaycnt])

        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 학습 기간 {startday} ~ {endday}'])
        if 'V' in self.backname:
            for vsday, veday, _, _ in valid_days:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 검증 기간 {vsday} ~ {veday}'])
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 기간 추출 완료'])

        arry_bct = np.zeros((len(df_mt), 2), dtype='int64')
        arry_bct[:, 0] = df_mt['index'].values
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 보유종목수 어레이 생성 완료'])

        con = sqlite3.connect(DB_STRATEGY)
        dfb = pd.read_sql(f'SELECT * FROM {self.gubun}optibuy', con).set_index('index')
        dfs = pd.read_sql(f'SELECT * FROM {self.gubun}optisell', con).set_index('index')
        buystg  = dfb['전략코드'][buystg_name]
        sellstg = dfs['전략코드'][sellstg_name]
        df = pd.read_sql(f'SELECT * FROM {self.gubun}vars', con).set_index('index')
        optivars = df['전략코드'][optivars_name]
        con.close()

        optivars_ = compile(df['전략코드'][optivars_name], '<string>', 'exec')
        try:
            exec(optivars_, None, locals())
        except Exception as e:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'시스템 명령 오류 알림 - {self.backname} 변수설정 {e}'])
            self.SysExit(True)

        self.total_count = 1
        for value in list(self.vars.values()):
            self.total_count *= len(value[0])
            self.opti_list.append(value[0])
            self.fixed_list.append(value[1])
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 백테스터용 매도수전략 설정 완료'])

        mq = Queue()
        tdq_list = []
        vdq_list = []
        if 'V' in self.backname:
            for _ in valid_days:
                tdq, vdq = Queue(), Queue()
                tdq_list.append(tdq)
                vdq_list.append(vdq)
                Process(target=SubTotal, args=(self.tq, tdq, betting, optistandard, 1)).start()
                Process(target=SubTotal, args=(self.tq, vdq, betting, optistandard, 0)).start()
        Process(target=Total, args=(self.wq, self.tq, mq, self.pq_list, tdq_list, vdq_list, self.ui_gubun)).start()
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 집계용 프로세스 생성 완료'])

        self.tq.put(['이전데이터로딩', betting, startday, endday, starttime, endtime, buystg, sellstg])
        dict_days = mq.get()
        self.tq.put(['백테정보', betting, startday, endday, starttime, endtime, buystg, sellstg, dict_cn, std_text, optistandard, arry_bct, valid_days, len(day_list)])
        for pq in self.pq_list:
            pq.put(['백테정보', betting, self.vars[0][0], startday, endday, starttime, endtime, buystg, sellstg, dict_days])

        start = now()
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 백테스터 시작'])

        k    = 1
        vc   = len(self.opti_list)
        goal = 2 ** int(round(vc / 2))
        self.vars_list = []
        while self.total_count > goal:
            self.tq.put(['시작시간', now()])
            self.tq.put(['경우의수', vc * 10 * back_count, back_count])

            for _ in range(vc * 10):
                vars_list = self.GetVarslist()
                if vars_list:
                    self.tq.put(['변수정보', vars_list])
                    for pq in self.pq_list:
                        pq.put(['변수정보', vars_list, False])

                    std = mq.get()
                    if type(std) != str:
                        self.result[std] = vars_list
                    else:
                        if len(self.result) > 0:
                            self.SaveVarslist(100, optistandard, buystg, sellstg)
                        self.SysExit(True)
                else:
                    self.total_count = 0
                    break

            if self.total_count == 0:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 모든 경우의 수 탐색 완료'])
                break

            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 결과 {k}단계 완료'])
            self.SetOptilist(k, int(vc / 4) if vc / 4 > 5 else 5, goal, optistandard)
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 결과 현재 경우의수[{self.total_count:,.0f}] 목표 경우의수[{goal:,.0f}]'])
            k += 1

        self.SaveVarslist(100, optistandard, buystg, sellstg)

        exec(optivars_, None, locals())
        optivars = optivars.split('self.vars[0]')[0]
        for i in range(len(self.vars)):
            if self.vars[i][1] != self.high_vars[i]:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 결과 self.vars[{i}]의 최적값 변경 {self.vars[i][1]} -> {self.high_vars[i]}'])
                self.vars[i][1] = self.high_vars[i]
            optivars += f'self.vars[{i}] = {self.vars[i]}\n'

        con = sqlite3.connect(DB_STRATEGY)
        cur = con.cursor()
        cur.execute(f"UPDATE {self.gubun}vars SET 전략코드 = '{optivars}' WHERE `index` = '{optivars_name}'")
        con.commit()
        con.close()

        mq.close()
        if self.dict_set['스톰라이브']: self.lq.put(f'{self.backname}')
        self.sq.put('지에이 최적화가 완료되었습니다.')
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 소요시간 {now() - start}'])
        self.SysExit(False)

    def GetVarslist(self):
        vars_list  = []
        limit_time = timedelta_sec(10)
        while vars_list == [] or (vars_list in self.vars_list and now() < limit_time):
            vars_list = []
            for vars_ in self.opti_list:
                vars_list.append(random.choice(vars_))
        if now() >= limit_time:
            vars_list = []
        else:
            self.vars_list.append(vars_list)
        return vars_list

    def SetOptilist(self, count, rank, goal, optistandard):
        self.opti_list = [[] for _ in self.opti_list]
        rs_list = sorted(self.result.items(), key=operator.itemgetter(0), reverse=True)

        text = f'{self.backname} 결과\n'
        for std, vars_list in rs_list[:rank]:
            if optistandard == 'TG':
                text += f' 기준값 [{std:,.0f}] 변수 {vars_list}\n'
            else:
                text += f' 기준값 [{std:.2f}] 변수 {vars_list}\n'
            for i, vars_ in enumerate(vars_list):
                if vars_ not in self.opti_list[i]:
                    self.opti_list[i].append(vars_)
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], text[:-1]])

        self.total_count = 1
        for i, vars_ in enumerate(self.opti_list):
            if count < 2 and self.fixed_list[i] not in vars_:
                self.opti_list[i].append(self.fixed_list[i])
            self.opti_list[i].sort()
            self.total_count *= len(vars_)

        if self.total_count <= goal:
            text = ''
            for std, vars_list in rs_list[rank:100 - rank]:
                if optistandard == 'TG':
                    text += f' 기준값 [{std:,.0f}] 변수 {vars_list}\n'
                else:
                    text += f' 기준값 [{std:.2f}] 변수 {vars_list}\n'
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], text[:-1]])

    def SaveVarslist(self, rank, optistandard, buystg, sellstg):
        rs_list = sorted(self.result.items(), key=operator.itemgetter(0), reverse=True)
        con = sqlite3.connect(DB_BACKTEST)
        for std, vars_list in rs_list[:rank]:
            data = [[optistandard, std, f'{vars_list}', buystg, sellstg]]
            df = pd.DataFrame(data, columns=['기준', '기준값', '범위설정', '매수코드', '매도코드'], index=[strf_time('%Y%m%d%H%M%S')])
            df.to_sql(self.savename, con, if_exists='append', chunksize=1000)
        con.close()
        self.high_vars = rs_list[0][1]
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 상위100위 결과 저장 완료'])

    def SysExit(self, cancel):
        if cancel:
            self.wq.put([ui_num[f'{self.ui_gubun}백테바'], 0, 100, 0])
        else:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 완료'])
        time.sleep(1)
        sys.exit()
