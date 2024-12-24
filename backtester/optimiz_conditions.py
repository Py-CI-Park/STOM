import sys
import time
import random
import sqlite3
import operator
import numpy as np
import pandas as pd
from multiprocessing import Process, Queue
from backtester.back_static import SendTextAndStd, GetMoneytopQuery
from utility.static import factorial, strf_time, now, timedelta_day, strp_time
from utility.setting import ui_num, DB_STRATEGY, DICT_SET, DB_BACKTEST, DB_STOCK_BACK, DB_COIN_BACK


class Total:
    def __init__(self, wq, tq, mq, tdq_list, vdq_list, stq_list, ui_gubun):
        self.wq           = wq
        self.tq           = tq
        self.mq           = mq
        self.tdq_list     = tdq_list
        self.vdq_list     = vdq_list
        self.stq_list     = stq_list
        self.ui_gubun     = ui_gubun
        self.dict_set     = DICT_SET

        self.start        = now()
        self.back_count   = None

        self.std_list     = None
        self.optistandard = None
        self.day_count    = None

        self.betting      = None
        self.startday     = None
        self.endday       = None
        self.valid_days   = None
        self.starttime    = None
        self.endtime      = None
        self.avgtime      = None

        self.dict_t       = {}
        self.dict_v       = {}

        self.stdp         = -2_147_483_648
        self.sub_total    = 0
        self.total_count  = 0

        self.Start()

    def Start(self):
        st  = {}
        tc  = 0
        bc  = 0
        tbc = 0
        sc  = 0
        dict_tsg = {}
        dict_bct = {}
        while True:
            data = self.tq.get()
            if data[0] == '백테완료':
                bc  += 1
                tbc += 1
                if data[1]: tc += 1
                self.wq.put((ui_num[f'{self.ui_gubun}백테바'], tbc, self.total_count, self.start))

                if bc == self.back_count:
                    bc = 0
                    if tc > 0:
                        tc = 0
                        for stq in self.stq_list:
                            stq.put(('백테완료', '미분리집계'))
                    else:
                        for vars_key in range(20):
                            self.stdp = SendTextAndStd(self.GetSendData(vars_key), self.std_list, self.betting, None)

            elif data[0] == '백테결과':
                _, vars_key, list_tsg, arry_bct = data
                if list_tsg is not None:
                    dict_tsg[vars_key] = list_tsg
                    dict_bct[vars_key] = arry_bct

                sc += 1
                if sc == 20:
                    sc = 0
                    columns = ['index', '종목명', '시가총액' if self.ui_gubun != 'CF' else '포지션', '매수시간', '매도시간',
                               '보유시간', '매수가', '매도가', '매수금액', '매도금액', '수익률', '수익금', '매도조건', '추가매수시간']
                    k  = 0
                    for vars_key, list_tsg in dict_tsg.items():
                        data = ('결과집계', columns, list_tsg, dict_bct[vars_key])
                        if self.valid_days is not None:
                            for i, vdays in enumerate(self.valid_days):
                                data_ = data + (vdays[0], vdays[1], vdays[2], vdays[3], i, vars_key)
                                self.tdq_list[k % 10].put(data_)
                                self.vdq_list[k % 10].put(data_)
                                k += 1
                        else:
                            data_ = data + (self.day_count, vars_key)
                            self.stq_list[k % 20].put(data_)
                            k += 1

                    if len(dict_tsg) < 20:
                        zero_key_list = [x for x in range(20) if x not in dict_tsg.keys()]
                        for vars_key in zero_key_list:
                            self.stdp = SendTextAndStd(self.GetSendData(vars_key), self.std_list, self.betting, None)
                    dict_tsg = {}
                    dict_bct = {}

            elif data[0] in ('TRAIN', 'VALID'):
                gubun, num, data, vars_key = data
                if vars_key not in self.dict_t.keys(): self.dict_t[vars_key] = {}
                if vars_key not in self.dict_v.keys(): self.dict_v[vars_key] = {}
                if vars_key not in st.keys(): st[vars_key] = 0
                if gubun == 'TRAIN':
                    self.dict_t[vars_key][num] = data
                else:
                    self.dict_v[vars_key][num] = data
                st[vars_key] += 1
                if st[vars_key] == self.sub_total:
                    self.stdp = SendTextAndStd(self.GetSendData(vars_key), self.std_list, self.betting, self.dict_t[vars_key], self.dict_v[vars_key], self.dict_set['교차검증가중치'])
                    st[vars_key] = 0

            elif data[0] == 'ALL':
                _, _, data, vars_key = data
                self.stdp = SendTextAndStd(self.GetSendData(vars_key), self.std_list, self.betting, data)

            elif data[0] == '백테정보':
                self.BackInfo(data)
            elif data[0] == '경우의수':
                self.total_count = data[1]
                self.back_count  = data[2]
            elif data == '백테중지':
                self.mq.put('백테중지')
                break

        time.sleep(1)
        sys.exit()

    def BackInfo(self, data):
        self.betting      = data[1]
        self.avgtime      = data[2]
        self.startday     = data[3]
        self.endday       = data[4]
        self.starttime    = data[5]
        self.endtime      = data[6]
        self.std_list     = data[7]
        self.optistandard = data[8]
        self.valid_days   = data[9]
        self.day_count    = data[10]
        if self.valid_days is not None:
            self.sub_total = len(self.valid_days) * 2
        else:
            self.sub_total = 2

    def GetSendData(self, vars_key=0):
        return ['조건최적화', self.ui_gubun, self.wq, self.mq, self.stdp, self.optistandard, 0, vars_key, None, self.startday, self.endday]


class OptimizeConditions:
    def __init__(self, wq, bq, sq, tq, lq, pq_list, stq_list, backname, ui_gubun):
        self.wq           = wq
        self.bq           = bq
        self.sq           = sq
        self.tq           = tq
        self.lq           = lq
        self.pq_list      = pq_list
        self.stq_list     = stq_list
        self.backname     = backname
        self.ui_gubun     = ui_gubun
        self.result       = {}
        self.opti_list    = []
        self.bcount       = None
        self.scount       = None
        self.buyconds     = None
        self.sellconds    = None
        self.optistandard = None
        self.dict_set     = DICT_SET
        self.gubun        = 'stock' if self.ui_gubun == 'S' else 'coin'
        self.savename     = f'{self.gubun}_{self.backname.replace("최적화", "").lower()}'
        self.Start()

    def Start(self):
        data = self.bq.get()
        if self.ui_gubun != 'CF':
            betting = float(data[0]) * 1000000
        else:
            betting = float(data[0])
        avgtime       = int(data[1])
        starttime     = int(data[2])
        endtime       = int(data[3])
        buystg_name       = data[4]
        sellstg_name      = data[5]
        std_text          = data[6].split(';')
        std_text          = [float(x) for x in std_text]
        self.optistandard = data[7]
        self.bcount   = int(data[8])
        self.scount   = int(data[9])
        rcount        = int(data[10])
        back_count        = data[11]
        weeks_train       = data[12]
        weeks_valid   = int(data[13])
        _             = int(data[14])
        backengin_sday    = data[15]
        backengin_eday    = data[16]
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
                self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 + 검증기간 만큼의 데이터가 필요합니다'))
            else:
                self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 만큼의 데이터가 필요합니다'))
            self.SysExit(True)

        con   = sqlite3.connect(DB_STOCK_BACK if self.ui_gubun == 'S' else DB_COIN_BACK)
        query = GetMoneytopQuery(self.ui_gubun, startday, endday, starttime, endtime)
        df_mt = pd.read_sql(query, con)
        con.close()

        if len(df_mt) == 0 or back_count == 0:
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], '날짜 지정이 잘못되었거나 데이터가 존재하지 않습니다.\n'))
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

        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 학습 기간 {startday} ~ {endday}'))
        if 'V' in self.backname:
            for vsday, veday, _, _ in valid_days:
                self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 검증 기간 {vsday} ~ {veday}'))
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 기간 추출 완료'))

        arry_bct = np.zeros((len(df_mt), 2), dtype='int64')
        arry_bct[:, 0] = df_mt['index'].values
        data = ('백테정보', arry_bct, betting)
        for q in self.stq_list:
            q.put(data)
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 보유종목수 어레이 생성 완료'))

        con = sqlite3.connect(DB_STRATEGY)
        dfb = pd.read_sql(f'SELECT * FROM {self.gubun}buyconds', con).set_index('index')
        dfs = pd.read_sql(f'SELECT * FROM {self.gubun}sellconds', con).set_index('index')
        con.close()

        self.buyconds  = dfb['전략코드'][buystg_name].split('\n')
        self.sellconds = dfs['전략코드'][sellstg_name].split('\n')

        is_long = None
        if self.ui_gubun == 'CF':
            if '#' in self.buyconds[0] and 'LONG' in self.buyconds[0] and '#' in self.sellconds[0] and 'LONG' in self.sellconds[0]:
                is_long = True
            elif '#' in self.buyconds[0] and 'SHORT' in self.buyconds[0] and '#' in self.sellconds[0] and 'SHORT' in self.sellconds[0]:
                is_long = False
            if is_long is None:
                self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], '롱숏구분(#LONG 또는 #SHORT)이 없거나 매도수 구분이 다릅니다.\n'))
                self.SysExit(True)

        self.buyconds  = [x for x in self.buyconds if x != '' and '#' not in x]
        self.sellconds = [x for x in self.sellconds if x != '' and '#' not in x]
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 매도수조건 설정 완료'))

        bc = factorial(len(self.buyconds)) / (factorial(self.bcount) * factorial(len(self.buyconds) - self.bcount))
        sc = factorial(len(self.sellconds)) / (factorial(self.scount) * factorial(len(self.sellconds) - self.scount))
        total_count = int(bc * sc)
        if total_count < rcount:
            rcount = total_count
        rcount = int(rcount / 20)
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 전체 경우의 수 계산 완료 [{total_count:,.0f}]'))

        mq = Queue()
        tdq_list = self.stq_list[:10]
        vdq_list = self.stq_list[10:]
        Process(target=Total, args=(self.wq, self.tq, mq, tdq_list, vdq_list, self.stq_list, self.ui_gubun)).start()
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 집계용 프로세스 생성 완료'))

        self.tq.put(('백테정보', betting, avgtime, startday, endday, starttime, endtime, std_text, self.optistandard, valid_days, len(day_list)))
        data = ('백테정보', betting, avgtime, startday, endday, starttime, endtime)
        for q in self.pq_list:
            q.put(data)

        start = now()
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 백테스터 시작'))
        self.tq.put(('경우의수', rcount * back_count, back_count))

        for _ in range(rcount):
            buy_conds, sell_conds = self.GetCondlist()
            for q in self.stq_list:
                q.put('백테시작')
            if is_long is None:
                data = ('조건정보', buy_conds, sell_conds)
            else:
                data = ('조건정보', is_long, buy_conds, sell_conds)
            for q in self.pq_list:
                q.put(data)

            for _ in range(20):
                data = mq.get()
                if type(data) == str:
                    if len(self.result) > 0:
                        self.ShowTopCondlist(5)
                        self.ShowTopConds()
                    self.SysExit(True)
                else:
                    std, vars_key = data
                    if std > 0:
                        self.result[std] = [buy_conds[vars_key], sell_conds[vars_key]]

        if len(self.result) > 0:
            self.ShowTopCondlist(5)
            self.ShowTopConds()
        else:
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 기준값 0을 초과하는 조합이 없습니다.'))

        mq.close()
        if self.dict_set['스톰라이브']: self.lq.put(self.backname)
        self.sq.put('조건 최적화가 완료되었습니다.')
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 소요시간 {now() - start}'))
        self.SysExit(False)

    def GetCondlist(self):
        opti_list = []
        buyconds  = []
        sellconds = []
        for _ in range(20):
            while opti_list == [] or opti_list in self.opti_list:
                random.shuffle(self.buyconds)
                random.shuffle(self.sellconds)
                buycond  = self.buyconds[:self.bcount]
                sellcond = self.sellconds[:self.scount]
                buycond.sort()
                sellcond.sort()
                opti_list = [buycond, sellcond]
            buyconds.append(opti_list[0])
            sellconds.append(opti_list[1])
            self.opti_list.append(opti_list)
        return buyconds, sellconds

    def ShowTopCondlist(self, rank):
        rs_list = sorted(self.result.items(), key=operator.itemgetter(0), reverse=True)
        for key, value in rs_list[:rank]:
            buyconds  = 'if ' + ':\n    매수 = False\nelif '.join(value[0]) + ':\n    매수 = False'
            sellconds = 'if ' + ':\n    매도 = True\nelif '.join(value[1]) + ':\n    매도 = True'
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 결과 - {self.optistandard}[{key}]\n'))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 결과 - 매수조건\n{buyconds}\n'))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 결과 - 매도조건\n{sellconds}\n'))
            data = [[self.optistandard, key, buyconds, sellconds]]
            df = pd.DataFrame(data, columns=['기준', '기준값', '매수코드', '매도코드'], index=[strf_time('%Y%m%d%H%M%S')])
            con = sqlite3.connect(DB_BACKTEST)
            df.to_sql(self.savename, con, if_exists='append', chunksize=1000)
            con.close()

    def ShowTopConds(self):
        buy_conds_freq  = {}
        sell_conds_freq = {}

        rs_list    = sorted(self.result.items(), key=operator.itemgetter(0), reverse=True)
        opti_dict  = {x: y for x, y in rs_list}
        for key, value in opti_dict.items():
            for cond in value[0]:
                if cond in buy_conds_freq.keys():
                    buy_conds_freq[cond] += 1
                else:
                    buy_conds_freq[cond] = 1
            for cond in value[1]:
                if cond in sell_conds_freq.keys():
                    sell_conds_freq[cond] += 1
                else:
                    sell_conds_freq[cond] = 1

        buy_conds_freq  = sorted(buy_conds_freq.items(), key=operator.itemgetter(1), reverse=True)
        sell_conds_freq = sorted(sell_conds_freq.items(), key=operator.itemgetter(1), reverse=True)

        text = '조건회적화 결과 - 매수조건 출현빈도\n'
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 결과 - 매수조건 출현빈도'))
        for key, value in buy_conds_freq:
            text += f'[{value}] {key}\n'
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'[{value}] {key}'))

        text += '\n조건회적화 결과 - 매도조건 출현빈도\n'
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 결과 - 매도조건 출현빈도'))
        for key, value in sell_conds_freq:
            text += f'[{value}] {key}\n'
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'[{value}] {key}'))

        df = pd.DataFrame({'조건별출현빈도': [text]}, index=[strf_time('%Y%m%d%H%M%S')])
        con = sqlite3.connect(DB_BACKTEST)
        df.to_sql(f'{self.savename}_conds', con, if_exists='append', chunksize=1000)
        con.close()

    def SysExit(self, cancel):
        if cancel:
            self.wq.put((ui_num[f'{self.ui_gubun}백테바'], 0, 100, 0))
        else:
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 완료'))
        time.sleep(1)
        sys.exit()
