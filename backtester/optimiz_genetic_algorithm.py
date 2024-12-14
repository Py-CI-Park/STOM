import sys
import time
import random
import sqlite3
import operator
import numpy as np
import pandas as pd
from multiprocessing import Process, Queue
from backtester.back_static import SubTotal, SendTextAndStd, GetMoneytopQuery
from utility.static import strf_time, now, timedelta_day, timedelta_sec, strp_time
from utility.setting import DB_STOCK_BACK, ui_num, DB_STRATEGY, DB_BACKTEST, DICT_SET, DB_COIN_BACK


class Total:
    def __init__(self, wq, tq, mq, tdq_list, vdq_list, ctq_list, ui_gubun):
        self.wq           = wq
        self.tq           = tq
        self.mq           = mq
        self.tdq_list     = tdq_list
        self.vdq_list     = vdq_list
        self.ctq_list     = ctq_list
        self.ui_gubun     = ui_gubun
        self.dict_set     = DICT_SET

        self.start        = now()
        self.back_count   = None

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

        self.dict_t       = {}
        self.dict_v       = {}

        self.vars_lists   = None
        self.stdp         = -100_000_000_000
        self.sub_total    = 0
        self.total_count  = 0

        self.Start()

    def Start(self):
        st  = {}
        tc  = 0
        bc  = 0
        tbc = 0
        while True:
            data = self.tq.get()
            if data[0] == '백테결과':
                _, vars_key, list_k, list_c, arry_bct = data
                if vars_key is not None:
                    columns = ['종목명', '시가총액' if self.ui_gubun != 'CF' else '포지션', '매수시간', '매도시간', '보유시간',
                               '매수가', '매도가', '매수금액', '매도금액', '수익률', '수익금', '매도조건', '추가매수시간']
                    if self.valid_days is not None:
                        data = [columns, list_c, list_k, arry_bct]
                        for i, vdays in enumerate(self.valid_days):
                            data_ = data + [vdays[0], vdays[1], vdays[2], vdays[3], i, vars_key]
                            self.tdq_list[i].put(data_)
                            self.vdq_list[i].put(data_)
                    else:
                        data = [columns, list_k, list_k, arry_bct, self.day_count, vars_key]
                        self.tdq_list[vars_key].put(data)

            elif data == '백테완료':
                bc  += 1
                tbc += 1
                if data[1]: tc += 1
                self.wq.put([ui_num[f'{self.ui_gubun}백테바'], tbc, self.total_count, self.start])

                if bc == self.back_count:
                    bc = 0
                    if tc > 0:
                        tc = 0
                        for ctq in self.ctq_list:
                            ctq.put('백테완료')
                    else:
                        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '매수전략을 만족하는 종목이 없어 결과를 표시할 수 없습니다.'])
                        self.BackStop()
                        break

            elif data[0] in ['TRAIN', 'VALID', 'ALL']:
                vars_key = data[-1]
                if data[0] == 'ALL':
                    self.stdp = SendTextAndStd(self.GetSendData(data[-1]), self.std_list, self.betting, data[2])
                else:
                    if vars_key not in self.dict_t.keys(): self.dict_t[vars_key] = {}
                    if vars_key not in self.dict_v.keys(): self.dict_v[vars_key] = {}
                    if vars_key not in st.keys(): st[vars_key] = 0
                    if data[0] == 'TRAIN':
                        self.dict_t[vars_key][data[1]] = data[2]
                    else:
                        self.dict_v[vars_key][data[1]] = data[2]
                    st[vars_key] += 1
                    if st[vars_key] == self.sub_total:
                        self.stdp = SendTextAndStd(self.GetSendData(vars_key), self.std_list, self.betting, self.dict_t[vars_key], self.dict_v[vars_key], self.dict_set['교차검증가중치'])
                        st[vars_key] = 0

            elif data[0] == '백테정보':
                self.BackInfo(data)
            elif data[0] == '변수정보':
                self.vars_lists = data[1]
            elif data[0] == '시작시간':
                self.start = data[1]
                tbc = 0
            elif data[0] == '경우의수':
                self.total_count = data[1]
                self.back_count  = data[2]
            elif data == '백테중지':
                self.BackStop()
                break

        time.sleep(1)
        sys.exit()

    def BackStop(self):
        if self.tdq_list:
            for q in self.tdq_list:
                q.put('서브집계프로세스종료')
            for q in self.vdq_list:
                q.put('서브집계프로세스종료')
        self.mq.put('백테중지')

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
        self.valid_days   = data[11]
        self.day_count    = data[12]
        if self.valid_days is not None:
            self.sub_total = len(self.valid_days) * 2
        else:
            self.sub_total = 2

    def GetSendData(self, vars_key):
        return ['GA최적화', self.ui_gubun, self.wq, self.mq, self.stdp, self.optistandard, 0, vars_key, self.vars_lists[vars_key], self.startday, self.endday]


class OptimizeGeneticAlgorithm:
    def __init__(self, wq, bq, sq, tq, lq, pq_list, ctq_list, backname, ui_gubun):
        self.wq          = wq
        self.bq          = bq
        self.sq          = sq
        self.tq          = tq
        self.lq          = lq
        self.pq_list     = pq_list
        self.ctq_list    = ctq_list
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
        weeks_train = int(data[10])
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
        query = GetMoneytopQuery(self.ui_gubun, startday, endday, starttime, endtime)
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
        data = ['보유종목수어레이', arry_bct]
        for q in self.ctq_list:
            q.put(data)
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
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 매도수전략 설정 완료'])

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
        else:
            for _ in range(10):
                tdq = Queue()
                tdq_list.append(tdq)
                Process(target=SubTotal, args=(self.tq, tdq, betting, optistandard, 1)).start()

        Process(target=Total, args=(self.wq, self.tq, mq, tdq_list, vdq_list, self.ctq_list, self.ui_gubun)).start()
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 집계용 프로세스 생성 완료'])

        self.tq.put(['백테정보', betting, startday, endday, starttime, endtime, buystg, sellstg, dict_cn, std_text, optistandard, valid_days, len(day_list)])
        data = ['백테정보', betting, self.vars[0][0], startday, endday, starttime, endtime, buystg, sellstg]
        for q in self.pq_list:
            q.put(data)

        start = now()
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 백테스터 시작'])

        k    = 1
        vc   = len(self.opti_list)
        goal = 2 ** int(round(vc / 2))
        self.vars_list = []
        while self.total_count > goal:
            self.tq.put(['시작시간', now()])
            self.tq.put(['경우의수', vc * back_count, back_count])

            for _ in range(vc):
                vars_lists = self.GetVarslist()
                if vars_lists:
                    self.tq.put(['변수정보', vars_lists])
                    for q in self.ctq_list:
                        q.put('백테시작')
                    for q in self.pq_list:
                        q.put(['변수정보', vars_lists])

                    for _ in range(10):
                        data = mq.get()
                        if type(data) == str:
                            if len(self.result) > 0:
                                self.SaveVarslist(100, optistandard, buystg, sellstg)
                            self.SysExit(True)
                        else:
                            std, vars_key = data
                            self.result[std] = vars_lists[vars_key]
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
        vars_lists = []
        limit_time = timedelta_sec(30)
        for _ in range(10):
            vars_list  = []
            while vars_list == [] or (vars_list in self.vars_list and now() < limit_time):
                vars_list = []
                for vars_ in self.opti_list:
                    vars_list.append(random.choice(vars_))
            if now() >= limit_time:
                vars_lists = []
            else:
                vars_lists.append(vars_list)
                self.vars_list.append(vars_list)
        return vars_lists

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
