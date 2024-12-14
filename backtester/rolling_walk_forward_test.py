import sys
import time
import optuna
import random
import sqlite3
import numpy as np
import pandas as pd
from multiprocessing import Process, Queue
from backtester.back_static import SendTextAndStd, GetBackResult, GetMoneytopQuery, PltShow
from utility.static import strf_time, now, timedelta_day, strp_time
from utility.setting import ui_num, DB_STRATEGY, DB_BACKTEST, DICT_SET, DB_STOCK_BACK, DB_COIN_BACK, DB_OPTUNA


class Total:
    def __init__(self, wq, sq, tq, mq, tdq_list, vdq_list, stq_list, backname, ui_gubun, gubun):
        self.wq           = wq
        self.sq           = sq
        self.tq           = tq
        self.mq           = mq
        self.tdq_list     = tdq_list
        self.vdq_list     = vdq_list
        self.stq_list     = stq_list
        self.backname     = backname
        self.ui_gubun     = ui_gubun
        self.gubun        = gubun
        self.dict_set     = DICT_SET
        gubun_text        = f'{self.gubun}_future' if self.ui_gubun == 'CF' else self.gubun
        self.savename     = f'{gubun_text}_{self.backname.replace("전진분석", "").lower()}'

        self.start        = now()
        self.back_count   = None
        self.in_out_count = None
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
        self.schedul      = None

        self.df_kp        = None
        self.df_kd        = None
        self.df_tsg       = None
        self.df_bct       = None

        self.df_ttsg      = []
        self.df_tbct      = []

        self.dict_t       = {}
        self.dict_v       = {}

        self.vars         = None
        self.vars_list    = None
        self.vars_turn    = None
        self.hstd_list    = None
        self.stdp         = -2_147_483_648
        self.sub_total    = 0
        self.total_count  = 0

        self.Start()

    def Start(self):
        st  = {}
        tc  = 0
        oc  = 0
        bc  = 0
        tbc = 0
        sc  = 0
        total_dict_tsg = {}
        total_dict_bct = {}
        while True:
            data = self.tq.get()
            if data[0] == '백테결과':
                _, dict_tsg, dict_bct = data
                if dict_tsg:
                    for vars_key, list_tsg in dict_tsg.items():
                        arry_bct = dict_bct[vars_key]
                        if vars_key not in total_dict_tsg.keys():
                            total_dict_tsg[vars_key] = [[] for _ in range(14)]
                            total_dict_bct[vars_key] = arry_bct
                        else:
                            total_dict_bct[vars_key][:, 1] += arry_bct[:, 1]

                        for j, tsg_data in enumerate(list_tsg):
                            total_dict_tsg[vars_key][j] += tsg_data
                            # if j == 0:
                            #     for index in tsg_data:
                            #         index_ = index
                            #         while index_ in total_dict_tsg[vars_key][j]:
                            #             index_ = strf_time('%Y%m%d%H%M%S', timedelta_sec(1, strp_time('%Y%m%d%H%M%S', index_)))
                            #         total_dict_tsg[vars_key][j].append(index_)
                            # else:
                            #     total_dict_tsg[vars_key][j] += tsg_data
                sc += 1
                if sc < 20:
                    continue

                sc = 0
                columns = ['index', '종목명', '시가총액' if self.ui_gubun != 'CF' else '포지션', '매수시간', '매도시간', '보유시간',
                           '매수가', '매도가', '매수금액', '매도금액', '수익률', '수익금', '매도조건', '추가매수시간']
                if self.vars_turn >= -1:
                    k = 0
                    for vars_key, list_tsg in total_dict_tsg.items():
                        data = ('결과집계', columns, list_tsg, total_dict_bct[vars_key])
                        train_days, valid_days, test_days = self.list_days[self.in_out_count]
                        if valid_days is not None:
                            for j, vdays in enumerate(valid_days):
                                data_ = data + (vdays[0], vdays[1], test_days[0], train_days[2] - vdays[2], vdays[2], j, vars_key)
                                self.tdq_list[k % 10].put(data_)
                                self.vdq_list[k % 10].put(data_)
                                k += 1
                        else:
                            data_ = data + (train_days[2], vars_key)
                            self.stq_list[k % 20].put(data_)
                            k += 1

                    if self.vars_turn != -1:
                        curr_vars_list = self.vars_list[self.vars_turn][0]
                        if len(total_dict_tsg) < len(curr_vars_list) - 1:
                            curr_high_index = curr_vars_list.index(self.vars_list[self.vars_turn][1])
                            curr_vars_count = len(curr_vars_list)
                            zero_key_list = [x for x in range(curr_vars_count) if x not in total_dict_tsg.keys() and x != curr_high_index]
                            for vars_key in zero_key_list:
                                self.stdp = SendTextAndStd(self.GetSendData(vars_key), self.std_list, self.betting, None)
                    total_dict_tsg = {}
                    total_dict_bct = {}
                else:
                    self.df_tsg = pd.DataFrame(dict(zip(columns, total_dict_tsg[0])))
                    self.df_tsg.set_index('index', inplace=True)
                    self.df_tsg.sort_index(inplace=True)
                    arry_bct = total_dict_bct[0]
                    arry_bct = arry_bct[arry_bct[:, 1] > 0]
                    self.df_bct = pd.DataFrame(arry_bct[:, 1], columns=['보유종목수'], index=arry_bct[:, 0])
                    self.df_ttsg.append(self.df_tsg)
                    self.df_tbct.append(self.df_bct)
                    oc += 1
                    if oc < self.in_out_count:
                        self.SemiReport(oc)
                    else:
                        self.Report()

            elif data[0] == '백테완료':
                bc  += 1
                tbc += 1
                if data[1]:
                    tc += 1
                self.wq.put((ui_num[f'{self.ui_gubun}백테바'], tbc, self.total_count, self.start))

                if bc == self.back_count:
                    bc = 0
                    if tc > 0:
                        tc = 0
                        for ctq in self.stq_list:
                            ctq.put('백테완료')
                    else:
                        for vars_key in range(len(self.vars_list[self.vars_turn][0])):
                            self.stdp = SendTextAndStd(self.GetSendData(vars_key), self.std_list, self.betting, None)

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
            elif data[0] == '변수정보':
                self.vars_list = data[1]
                self.vars_turn = data[2]
                self.vars      = [var[1] for var in self.vars_list]
            elif data[0] == '재최적화':
                self.start = now()
                tbc = 0
            elif data[0] == '경우의수':
                self.total_count  = data[1]
                self.back_count   = data[2]
                self.startday     = data[3]
                self.endday       = data[4]
                self.in_out_count = data[5]
                self.stdp         = -2_147_483_648
            elif data[0] == '횟수변경':
                self.total_count = data[1]
            elif data[0] == '최적화정보':
                self.hstd_list = data[1]
            elif data == '백테중지':
                self.mq.put('백테중지')
                break

        time.sleep(1)
        sys.exit()

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
        self.df_kp        = data[15]
        self.df_kd        = data[16]
        self.weeks_train  = data[17]
        self.weeks_valid  = data[18]
        self.weeks_test   = data[19]
        if self.list_days[0][1] is not None:
            self.sub_total = len(self.list_days[0][1]) * 2
        else:
            self.sub_total = 2

    def GetSendData(self, vars_key=0):
        if self.vars_turn >= 0:
            self.vars[self.vars_turn] = self.vars_list[self.vars_turn][0][vars_key]
        return ['전진분석', self.ui_gubun, self.wq, self.mq, self.stdp, self.optistandard, self.vars_turn, vars_key, self.vars, self.startday, self.endday]

    def SemiReport(self, oc):
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
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], text1))
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], text2))
        self.mq.put('아웃샘플 백테스트')

    def Report(self):
        self.df_ttsg = pd.concat(self.df_ttsg)
        self.df_tbct = pd.concat(self.df_tbct)

        df_ttsg = self.df_ttsg[['수익금']].copy()
        df_ttsg['index'] = df_ttsg.index
        df_ttsg['index'] = df_ttsg['index'].apply(lambda x: x[:8])
        out_day_count = len(list(set(df_ttsg['index'].to_list())))

        self.df_ttsg, self.df_tbct, result = GetBackResult(self.df_ttsg, self.df_tbct, self.betting, self.optistandard, out_day_count)
        tc, atc, pc, mc, wr, ah, ap, tsp, tsg, mhct, onegm, cagr, tpi, mdd, mdd_ = result

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

        mdd_test   = f'최대낙폭금액 {mdd_:,.0f}{bet_unit}' if 'G' in self.optistandard else f'최대낙폭률 {mdd:,.2f}%'
        label_text = f'종목당 배팅금액 {int(self.betting):,}{bet_unit}, 필요자금 {onegm:,}{bet_unit}, ' \
                     f'거래횟수 {tc}회, 일평균거래횟수 {atc}회, 적정최대보유종목수 {mhct}개, 평균보유기간 {ah:.2f}초\n' \
                     f'익절 {pc}회, 손절 {mc}회, 승률 {wr:.2f}%, 평균수익률 {ap:.2f}%, 수익률합계 {tsp:.2f}%, ' \
                     f'{mdd_test}, 수익금합계 {tsg:,}{bet_unit}, 매매성능지수 {tpi:.2f}, 연간예상수익률 {cagr:.2f}%'

        save_file_name = f"{self.savename}_{self.buystg_name}_{self.optistandard}_{self.file_name}"
        con = sqlite3.connect(DB_BACKTEST)
        self.df_ttsg.to_sql(save_file_name, con, if_exists='append', chunksize=1000)
        con.close()
        self.wq.put((ui_num[f'{self.ui_gubun.replace("F", "")}상세기록'], self.df_ttsg))

        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 아웃샘플 백테스터 완료'))
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 백테스트 소요시간 {now() - self.start}'))
        self.sq.put(f'{self.backname} 백테스트를 완료하였습니다.')

        PltShow('전진분석', self.df_ttsg, self.df_tbct, self.dict_cn, onegm, mdd, self.startday, self.endday, self.starttime, self.endtime,
                self.df_kp, self.df_kd, self.list_days, self.backname, back_text, label_text, save_file_name, self.schedul, False)
        self.mq.put('백테스트 완료')


class StopWhenNotUpdateBestCallBack:
    def __init__(self, wq, tq, back_count, optuna_count, ui_gubun, len_vars):
        self.wq           = wq
        self.tq           = tq
        self.back_count   = back_count
        self.optuna_count = optuna_count
        self.ui_gubun     = ui_gubun
        self.len_vars     = len_vars

    def __call__(self, study: optuna.study.Study, trial: optuna.trial.FrozenTrial) -> None:
        best_opt    = study.best_value
        best_num    = study.best_trial.number
        curr_num    = trial.number
        last_num    = (best_num + self.len_vars) if self.optuna_count == 0 else (best_num + self.optuna_count)
        rema_num    = last_num - curr_num
        total_count = self.back_count * (last_num + 1)
        self.tq.put(('횟수변경', total_count))
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'<font color=#45cdf7>OPTUNA INFO 최고기준값[{best_opt:,}] 기준값갱신[{best_num}] 현재횟수[{curr_num}] 남은횟수[{rema_num}]</font>'))
        if curr_num == last_num:
            study.stop()


class RollingWalkForwardTest:
    def __init__(self, wq, bq, sq, tq, lq, pq_list, stq_list, backname, ui_gubun):
        self.wq        = wq
        self.bq        = bq
        self.sq        = sq
        self.tq        = tq
        self.lq        = lq
        self.pq_list   = pq_list
        self.stq_list  = stq_list
        self.backname  = backname
        self.ui_gubun  = ui_gubun
        self.dict_set  = DICT_SET
        self.gubun     = 'stock' if self.ui_gubun == 'S' else 'coin'
        self.vars      = {}
        self.high_vars = []
        self.htsd      = -2_147_483_648
        self.study     = None
        self.dict_simple_vars = {}
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
        optuna_sampler  = data[21]
        if optuna_sampler == 'BruteForceSampler':
            sampler = optuna.samplers.BruteForceSampler()
        elif optuna_sampler == 'CmaEsSampler':
            sampler = optuna.samplers.CmaEsSampler()
        elif optuna_sampler == 'QMCSampler':
            sampler = optuna.samplers.QMCSampler()
        elif optuna_sampler == 'RandomSampler':
            sampler = optuna.samplers.RandomSampler()
        elif optuna_sampler == 'TPESampler':
            sampler = optuna.samplers.TPESampler()
        else:
            sampler = None
        optuna_fixvars = []
        if data[22] != '':
            try:
                optuna_fixvars  = [int(x.strip()) for x in data[22].split(',')]
            except:
                self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], '고정할 범위의 번호를 잘못입력하였습니다.'))
                self.SysExit(True)
        optuna_count = int(data[23])
        optuna_autostep  = data[24]
        random_optivars  = data[25]

        if 'V' in self.backname:
            int_day = int(strf_time('%Y%m%d', timedelta_day(-(weeks_train + weeks_valid + weeks_test + 1) * 7 + 1, strp_time('%Y%m%d', str(endday)))))
            if int(backengin_sday) > int_day or startday > int_day or endday > int(backengin_eday):
                self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 + 검증기간 + 확인기간 * 2 만큼의 데이터가 필요합니다'))
                self.SysExit(True)
        else:
            int_day = int(strf_time('%Y%m%d', timedelta_day(-(weeks_train + weeks_test + 1) * 7 + 1, strp_time('%Y%m%d', str(endday)))))
            if int(backengin_sday) > int_day or startday > int_day or endday > int(backengin_eday):
                self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 + 확인기간 * 2 만큼의 데이터가 필요합니다'))
                self.SysExit(True)

        con   = sqlite3.connect(DB_STOCK_BACK if self.ui_gubun == 'S' else DB_COIN_BACK)
        query = GetMoneytopQuery(self.ui_gubun, startday, endday, starttime, endtime)
        df_mt = pd.read_sql(query, con)
        con.close()

        if len(df_mt) == 0 or back_count == 0:
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], '날짜 지정이 잘못되었거나 데이터가 존재하지 않습니다.\n'))
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
                startday_, int(strf_time('%Y%m%d', timedelta_day(-weeks_test * (k + 1) * 7, dt_endday)))
            ]
            valid_days_ = []
            if 'VC' in self.backname:
                for i in range(int(weeks_train / weeks_valid) + 1):
                    valid_days_.append([
                        int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid * (i + 1) + weeks_test * (k + 1)) * 7 + 1, dt_endday))),
                        int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid * i + weeks_test * (k + 1)) * 7, dt_endday)))
                    ])
            elif 'V' in self.backname:
                valid_days_.append([
                    int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid + weeks_test * (k + 1)) * 7 + 1, dt_endday))),
                    int(strf_time('%Y%m%d', timedelta_day(-(weeks_test * (k + 1)) * 7, dt_endday)))
                ])
            else:
                valid_days_ = None
            test_days = [
                int(strf_time('%Y%m%d', timedelta_day(-(weeks_test * (k + 1)) * 7 + 1, dt_endday))),
                int(strf_time('%Y%m%d', timedelta_day(-(weeks_test * k) * 7, dt_endday)))
            ]
            list_days_.append([train_days, valid_days_, test_days])
            k += 1
            startday_ = int(strf_time('%Y%m%d', timedelta_day(-(weeks_train + weeks_valid + weeks_test * (k + 1)) * 7 + 1)))

        list_days = []
        for train_days_, valid_days_, test_days_ in list_days_:
            train_days_list = [x for x in day_list if train_days_[0] <= x <= train_days_[1]]
            train_days = [train_days_list[0], train_days_list[-1], len(train_days_list)]
            valid_days = []
            if 'V' in self.backname:
                for vsday, veday in valid_days_:
                    valid_days_list = [x for x in day_list if vsday <= x <= veday]
                    valid_days.append([valid_days_list[0], valid_days_list[-1], len(valid_days_list)])
            else:
                valid_days = None
            test_days_list = [x for x in day_list if test_days_[0] <= x <= test_days_[1]]
            test_days = [test_days_list[0], test_days_list[-1]]
            list_days.append([train_days, valid_days, test_days])

        list_days = list_days[::-1]
        for i, data in enumerate(list_days):
            train_days, valid_days, test_days = data
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 학습기간 {i + 1} : {train_days[0]} ~ {train_days[1]}'))
            if 'V' in self.backname:
                for vsday, veday, _ in valid_days:
                    self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 검증기간 {i + 1} : {vsday} ~ {veday}'))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 확인기간 {i + 1} : {test_days[0]} ~ {test_days[1]}'))
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 일자 추출 완료'))

        arry_bct = np.zeros((len(df_mt), 2), dtype='int64')
        arry_bct[:, 0] = df_mt['index'].values
        data = ('백테정보', arry_bct, betting, optistandard)
        for q in self.stq_list:
            q.put(data)
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 보유종목수 어레이 생성 완료'))

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
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'시스템 명령 오류 알림 - 최적화 변수설정 1단계 {e}'))
            self.SysExit(True)

        total_count = 0
        vars_type = []
        vars_ = []
        for var in list(self.vars.values()):
            low, high, gap = var[0]
            opti = var[1]
            vars_type.append(1 if low < high else 0)

            varint = 1 if type(gap) == int else 0
            vars_list = [[], opti]
            if gap == 0:
                vars_list[0].append(low)
            else:
                total_count += 1
                k = 0
                while True:
                    if varint:
                        v = low + gap * k
                    else:
                        v = round(low + gap * k, 1)
                    if (low < high and v <= high) or (low > high and v >= high):
                        vars_list[0].append(v)
                    else:
                        break
                    k += 1
            if opti not in vars_list[0] or random_optivars:
                vars_list[1] = random.choice(vars_list[0])
            vars_.append(vars_list)

        out_count   = len(list_days)
        len_vars    = len(vars_)
        avg_list    = vars_[0][0]
        total_count *= ccount if ccount != 0 else 1
        total_count += 1
        total_count *= out_count
        total_count += out_count
        total_count *= back_count
        text = f'{self.backname} 매도수전략 및 변수 설정 완료' if not random_optivars else f'{self.backname} 매도수전략 및 변수 최적값 랜덤 설정 완료'
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], text))

        mq = Queue()
        tdq_list = self.stq_list[:10]
        vdq_list = self.stq_list[10:]
        Process(target=Total, args=(self.wq, self.sq, self.tq, mq, tdq_list, vdq_list, self.stq_list, self.backname, self.ui_gubun, self.gubun)).start()
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 집계용 프로세스 생성 완료'))

        self.tq.put(('백테정보', betting, startday, endday, starttime, endtime, buystg_name, buystg, sellstg, optivars, dict_cn,
                     list_days, std_text, optistandard, schedul, df_kp, df_kd, weeks_train, weeks_valid, weeks_test))
        data = ('백테정보', betting, avg_list, starttime, endtime, buystg, sellstg)
        for q in self.pq_list:
            q.put(data)

        if 'B' in self.backname:
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'<font color=#45cdf7>OPTUNA Sampler : {optuna_sampler}</font>'))
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 인샘플 최적화 시작'))

        hstd_list = []
        hvar_list = []
        for t, day_data in enumerate(list_days):
            train_days, _, _ = day_data
            startday, endday = train_days[0], train_days[1]
            self.dict_simple_vars = {}

            if 'B' in self.backname:
                self.htsd = 0
                if optuna_count == 0:
                    total_count = back_count * (len(self.vars) + 1)
                else:
                    total_count = back_count * optuna_count
                self.tq.put(('경우의수', total_count, back_count, startday, endday, t))

                def objective(trial):
                    simple_vars = []
                    optuna_vars = []
                    for j, var_ in enumerate(list(self.vars.values())):
                        if j < 10:
                            trial_name = f'00{j}'
                        elif j < 100:
                            trial_name = f'0{j}'
                        else:
                            trial_name = f'{j}'

                        if not (var_[0][2] == 0 or j in optuna_fixvars):
                            if optuna_autostep:
                                if type(var_[0][2]) == int:
                                    if var_[0][0] < var_[0][1]:
                                        trial_ = trial.suggest_int(trial_name, var_[0][0], var_[0][1])
                                    else:
                                        trial_ = trial.suggest_int(trial_name, var_[0][1], var_[0][0])
                                else:
                                    if var_[0][0] < var_[0][1]:
                                        trial_ = trial.suggest_float(trial_name, var_[0][0], var_[0][1])
                                    else:
                                        trial_ = trial.suggest_float(trial_name, var_[0][1], var_[0][0])
                            else:
                                if type(var_[0][2]) == int:
                                    if var_[0][0] < var_[0][1]:
                                        trial_ = trial.suggest_int(trial_name, var_[0][0], var_[0][1], step=var_[0][2])
                                    else:
                                        trial_ = trial.suggest_int(trial_name, var_[0][1], var_[0][0], step=-var_[0][2])
                                else:
                                    if var_[0][0] < var_[0][1]:
                                        trial_ = trial.suggest_float(trial_name, var_[0][0], var_[0][1], step=var_[0][2])
                                    else:
                                        trial_ = trial.suggest_float(trial_name, var_[0][1], var_[0][0], step=-var_[0][2])
                        else:
                            if type(var_[1]) == int:
                                trial_ = trial.suggest_int(trial_name, var_[1], var_[1])
                            else:
                                trial_ = trial.suggest_float(trial_name, var_[1], var_[1])

                        simple_vars.append(trial_)
                        optuna_vars.append(['', trial_])

                    str_simple_vars = str(simple_vars)
                    if str_simple_vars not in self.dict_simple_vars.keys():
                        self.tq.put(('변수정보', optuna_vars, -1))
                        for stq in self.stq_list:
                            stq.put('백테시작')
                        for pq in self.pq_list:
                            pq.put(('변수정보', optuna_vars, -1, startday, endday))
                        data_ = mq.get()
                        if type(data_) == str:
                            ostd = 0
                            self.SysExit(True)
                        else:
                            ostd = data_[0]
                            self.dict_simple_vars[str_simple_vars] = ostd
                            if data_[0] > self.htsd: self.htsd = ostd
                    else:
                        ostd = self.dict_simple_vars[str_simple_vars]
                    return ostd

                total_change = 1
                study_name = f'{self.backname}_{buystg_name}_{strf_time("%Y%m%d%H%M%S")}'
                optuna.logging.disable_default_handler()
                if sampler is None:
                    self.study = optuna.create_study(storage=DB_OPTUNA, study_name=study_name, direction='maximize')
                else:
                    self.study = optuna.create_study(storage=DB_OPTUNA, study_name=study_name, direction='maximize', sampler=sampler)
                self.study.optimize(objective, n_trials=10000, callbacks=[StopWhenNotUpdateBestCallBack(self.wq, self.tq, back_count, optuna_count, self.ui_gubun, len(self.vars))])
                for i, var in enumerate(list(self.study.best_params.values())):
                    vars_[i][1] = var
            else:
                self.tq.put(('경우의수', total_count, back_count, startday, endday, t))
                self.tq.put(('변수정보', vars_, -1))
                for q in self.stq_list:
                    q.put('백테시작')
                for q in self.pq_list:
                    q.put(('변수정보', vars_, -1, startday, endday))
                self.htsd, _ = mq.get()

                k = 1
                change_var_count = None
                for _ in range(ccount if ccount != 0 else 100):
                    if ccount == 0:
                        if change_var_count == 0:
                            break
                        if k > 1:
                            self.tq.put('재최적화')
                            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'무한모드 {k}단계 시작, 최적값 변경 개수 [{change_var_count}]'))

                    change_var_count = 0
                    for i in range(len_vars):
                        len_vars_ = len(vars_[i][0]) - 1
                        if len_vars_ > 0:
                            start = now()
                            print('==================================================================')
                            print('vars_list :', vars_[i][0])
                            print('vars_turn :', i, 'len_vars :', len_vars_)
                            self.tq.put(('변수정보', vars_, i))
                            for q in self.stq_list:
                                q.put('백테시작')
                            for q in self.pq_list:
                                q.put(('변수정보', vars_, i, startday, endday))

                            for _ in range(len_vars_):
                                data = mq.get()
                                if type(data) == str:
                                    self.SysExit(True)
                                else:
                                    std, vars_key = data
                                    print(' - vars_key_ :', vars_key, 'stdpoint :', std)
                                    curr_typ = vars_type[i]
                                    curh_var = vars_[i][0][vars_key]
                                    preh_var = vars_[i][1]
                                    if std > self.htsd or (std == self.htsd and ((curr_typ and curh_var > preh_var) or (not curr_typ and curh_var < preh_var))):
                                        print(' * updatestd :', f'{preh_var} -> {curh_var}')
                                        self.htsd = std
                                        vars_[i][1] = curh_var
                                        change_var_count += 1
                            print(' - time_left :', (now() - start).total_seconds(), 'seconds')
                k += 1

            hvar_list.append(vars_)
            hstd_list.append([startday, endday, self.htsd])
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 인샘플 최적화 완료'))

        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 아웃샘플 백테스터 시작'))
        self.tq.put(('최적화정보', hstd_list))
        for i, data in enumerate(list_days):
            startday, endday = data[2]
            self.tq.put(('경우의수', total_count, back_count, startday, endday, out_count))
            self.tq.put(('변수정보', hvar_list[i], -2))
            for q in self.stq_list:
                q.put('백테시작')
            for q in self.pq_list:
                q.put(('변수정보', hvar_list[i], -2, startday, endday))
            _ = mq.get()

        mq.close()
        if self.dict_set['스톰라이브']: self.lq.put(self.backname.replace('O', '').replace('B', ''))
        self.SysExit(False)

    def SysExit(self, cancel):
        if cancel:
            self.wq.put((ui_num[f'{self.ui_gubun}백테바'], 0, 100, 0))
        else:
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 완료'))
        time.sleep(1)
        sys.exit()
