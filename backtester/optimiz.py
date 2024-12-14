import sys
import time
import optuna
import sqlite3
import numpy as np
import pandas as pd
from multiprocessing import Process, Queue
from backtester.back_static import SendTextAndStd, GetBackResult, PltShow, GetMoneytopQuery
from utility.static import strf_time, strp_time, now, timedelta_day
from utility.setting import DB_STOCK_BACK, DB_COIN_BACK, ui_num, DB_STRATEGY, DB_BACKTEST, columns_vc, DICT_SET, DB_SETTING, DB_OPTUNA


class Total:
    def __init__(self, wq, sq, tq, mq, lq, tdq_list, vdq_list, stq_list, backname, ui_gubun, gubun):
        self.wq           = wq
        self.sq           = sq
        self.tq           = tq
        self.mq           = mq
        self.lq           = lq
        self.tdq_list     = tdq_list
        self.vdq_list     = vdq_list
        self.stq_list     = stq_list
        self.backname     = backname
        self.ui_gubun     = ui_gubun
        self.gubun        = gubun
        self.dict_set     = DICT_SET
        gubun_text        = f'{self.gubun}_future' if self.ui_gubun == 'CF' else self.gubun
        self.savename     = f'{gubun_text}_{self.backname.replace("최적화", "").lower()}'

        self.start        = now()
        self.back_count   = None
        self.file_name    = strf_time('%Y%m%d%H%M%S')

        self.dict_cn      = None
        self.buystg_name  = None
        self.buystg       = None
        self.sellstg      = None
        self.optivars     = None
        self.std_list     = None
        self.optistandard = None
        self.day_count    = None
        self.weeks_train  = None
        self.weeks_valid  = None
        self.weeks_test   = None

        self.betting      = None
        self.startday     = None
        self.endday       = None
        self.list_days    = None
        self.starttime    = None
        self.endtime      = None
        self.schedul      = None

        self.df_kp        = None
        self.df_kd        = None
        self.df_tsg       = None
        self.df_bct       = None

        self.dict_t       = {}
        self.dict_v       = {}

        self.vars         = None
        self.vars_list    = None
        self.vars_turn    = None
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
                if sc < 10:
                    continue

                sc = 0
                columns = ['index', '종목명', '시가총액' if self.ui_gubun != 'CF' else '포지션', '매수시간', '매도시간',
                           '보유시간', '매수가', '매도가', '매수금액', '매도금액', '수익률', '수익금', '매도조건', '추가매수시간']
                if self.vars_turn >= -1:
                    k = 0
                    for vars_key, list_tsg in total_dict_tsg.items():
                        data = ['결과집계', columns, list_tsg, total_dict_bct[vars_key]]
                        train_days, valid_days, test_days = self.list_days
                        if valid_days is not None:
                            for j, vdays in enumerate(valid_days):
                                data_ = data + [vdays[0], vdays[1], test_days[0], train_days[2] - vdays[2], vdays[2], j, vars_key]
                                self.tdq_list[k % 5].put(data_)
                                self.vdq_list[k % 5].put(data_)
                                k += 1
                        else:
                            data_ = data + [train_days[2], vars_key]
                            self.stq_list[k % 10].put(data_)
                            k += 1
                    total_dict_tsg = {}
                    total_dict_bct = {}
                else:
                    self.df_tsg = pd.DataFrame(dict(zip(columns, total_dict_tsg[0])))
                    self.df_tsg.set_index('index', inplace=True)
                    self.df_tsg.sort_index(inplace=True)
                    arry_bct = total_dict_bct[0]
                    arry_bct = arry_bct[arry_bct[:, 1] > 0]
                    self.df_bct = pd.DataFrame(arry_bct[:, 1], columns=['보유종목수'], index=arry_bct[:, 0])
                    self.Report()

            elif data[0] == '백테완료':
                bc  += 1
                tbc += 1
                if data[1]:
                    tc += 1
                self.wq.put([ui_num[f'{self.ui_gubun}백테바'], tbc, self.total_count, self.start])

                if bc == self.back_count:
                    bc = 0
                    if tc > 0:
                        tc = 0
                        for ctq in self.stq_list:
                            ctq.put('백테완료')
                    else:
                        self.stdp = SendTextAndStd(self.GetSendData(0), self.std_list, self.betting, None)

            elif data[0] in ['TRAIN', 'VALID']:
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
                self.vars      = [var[-1] for var in self.vars_list]
            elif data[0] == '재최적화':
                self.start = now()
                tbc = 0
            elif data[0] == '경우의수':
                self.total_count = data[1]
                self.back_count  = data[2]
            elif data[0] == '횟수변경':
                self.total_count = data[1]
            elif data == '백테중지':
                self.mq.put('백테중지')
                break

        time.sleep(1)
        sys.exit()

    def BackInfo(self, data):
        self.betting      = data[1]
        self.startday     = data[2]
        self.endday       = data[3]
        self.starttime    = data[4]
        self.endtime      = data[5]
        self.buystg_name  = data[6]
        self.buystg       = data[7]
        self.sellstg      = data[8]
        self.optivars     = data[9]
        self.dict_cn      = data[10]
        self.std_list     = data[11]
        self.optistandard = data[12]
        self.schedul      = data[13]
        self.df_kp        = data[14]
        self.df_kd        = data[15]
        self.list_days    = data[16]
        self.day_count    = data[17]
        self.weeks_train  = data[18]
        self.weeks_valid  = data[19]
        self.weeks_test   = data[20]
        if self.list_days[1] is not None:
            self.sub_total = len(self.list_days[1]) * 2
        else:
            self.sub_total = 2

    def GetSendData(self, vars_key=0):
        if self.vars_turn >= 0:
            self.vars[self.vars_turn] = self.vars_list[self.vars_turn][vars_key]
        return ['최적화', self.ui_gubun, self.wq, self.mq, self.stdp, self.optistandard, self.vars_turn, vars_key, self.vars, self.startday, self.endday]

    def Report(self):
        if 'T' in self.backname:
            _, _, test_days = self.list_days
            df_tsg = self.df_tsg[(self.df_tsg['매도시간'] >= test_days[0] * 1000000) & (self.df_tsg['매도시간'] <= test_days[1] * 1000000 + 240000)]
            df_bct = self.df_bct[(self.df_bct.index >= test_days[0] * 1000000) & (self.df_bct.index <= test_days[1] * 1000000 + 240000)]
            _, _, result = GetBackResult(df_tsg, df_bct, self.betting, self.optistandard, test_days[2])
            senddata = self.GetSendData()
            senddata[0] = '최적화테스트'
            SendTextAndStd(senddata, self.std_list, self.betting, result)

        self.df_tsg, self.df_bct, result = GetBackResult(self.df_tsg, self.df_bct, self.betting, self.optistandard, self.day_count)
        SendTextAndStd(self.GetSendData(), self.std_list, self.betting, result)
        tc, atc, pc, mc, wr, ah, ap, tsp, tsg, mhct, onegm, cagr, tpi, mdd, mdd_ = result

        startday, endday, starttime, endtime = str(self.startday), str(self.endday), str(self.starttime).zfill(6), str(self.endtime).zfill(6)
        startday  = startday[:4] + '-' + startday[4:6] + '-' + startday[6:]
        endday    = endday[:4] + '-' + endday[4:6] + '-' + endday[6:]
        starttime = starttime[:2] + ':' + starttime[2:4] + ':' + starttime[4:]
        endtime   = endtime[:2] + ':' + endtime[2:4] + ':' + endtime[4:]
        bet_unit  = '원' if self.ui_gubun != 'CF' else 'USDT'

        if self.weeks_valid == 0 and self.weeks_test == 0:
            back_text = f'백테기간 : {startday}~{endday}, 백테시간 : {starttime}~{endtime}, 학습+검증기간 : {self.weeks_train}, 거래일수 : {self.day_count}, 평균값계산틱수 : {self.vars[0]}'
        elif self.weeks_valid == 0 and self.weeks_test != 0:
            back_text = f'백테기간 : {startday}~{endday}, 백테시간 : {starttime}~{endtime}, 학습+검증/확인기간 : {self.weeks_train}/{self.weeks_test}, 거래일수 : {self.day_count}, 평균값계산틱수 : {self.vars[0]}'
        elif self.weeks_test == 0:
            back_text = f'백테기간 : {startday}~{endday}, 백테시간 : {starttime}~{endtime}, 학습/검증기간 : {self.weeks_train}/{self.weeks_valid}, 거래일수 : {self.day_count}, 평균값계산틱수 : {self.vars[0]}'
        else:
            back_text = f'백테기간 : {startday}~{endday}, 백테시간 : {starttime}~{endtime}, 학습/검증/확인기간 : {self.weeks_train}/{self.weeks_valid}/{self.weeks_test}, 거래일수 : {self.day_count}, 평균값계산틱수 : {self.vars[0]}'

        mdd_text   = f'최대낙폭금액 {mdd_:,.0f}{bet_unit}' if 'G' in self.optistandard else f'최대낙폭률 {mdd:,.2f}%'
        label_text = f'변수 {self.vars}\n종목당 배팅금액 {int(self.betting):,}{bet_unit}, 필요자금 {onegm:,}{bet_unit}, ' \
                     f'거래횟수 {tc}회, 일평균거래횟수 {atc}회, 적정최대보유종목수 {mhct}개, 평균보유기간 {ah:.2f}초\n' \
                     f'익절 {pc}회, 손절 {mc}회, 승률 {wr:.2f}%, 평균수익률 {ap:.2f}%, 수익률합계 {tsp:.2f}%, ' \
                     f'{mdd_text}, 수익금합계 {tsg:,}{bet_unit}, 매매성능지수 {tpi:.2f}, 연간예상수익률 {cagr:.2f}%'

        if self.dict_set['스톰라이브']:
            backlive_text = f'back;{startday}~{endday};{starttime}~{endtime};{self.day_count};{self.vars[0]};{int(self.betting)};'\
                            f'{onegm};{tc};{atc};{mhct};{ah:.2f};{pc};{mc};{wr:.2f};{ap:.2f};{tsp:.2f};{mdd:.2f};{tsg};{cagr:.2f}'
            self.lq.put(backlive_text)

        if 'T' not in self.backname:
            con = sqlite3.connect(DB_SETTING)
            cur = con.cursor()
            df = pd.read_sql(f'SELECT * FROM {self.gubun}', con).set_index('index')
            gubun = '주식' if self.gubun == 'stock' else '코인'
            if self.buystg_name == df[f'{gubun}장초매수전략'][0]:
                cur.execute(f'UPDATE {self.gubun} SET {gubun}장초평균값계산틱수={self.vars[0]}')
            if self.buystg_name == df[f'{gubun}장중매수전략'][0]:
                cur.execute(f'UPDATE {self.gubun} SET {gubun}장중평균값계산틱수={self.vars[0]}')
            con.commit()
            con.close()

            con = sqlite3.connect(DB_STRATEGY)
            cur = con.cursor()
            for i, value in enumerate(self.vars):
                cur.execute(f"UPDATE {self.gubun}optibuy SET 변수{i}={value} WHERE `index`='{self.buystg_name}'")
            con.commit()
            con.close()
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'최적화전략 {self.buystg_name}의 최적값 및 평균틱수 갱신 완료'])

        save_file_name = f'{self.savename}_{self.buystg_name}_{self.optistandard}_{self.file_name}'
        data = [f'{self.vars}', int(self.betting), onegm, tc, atc, mhct, ah, pc, mc, wr, ap, tsp, mdd, tsg, tpi, cagr, self.buystg, self.sellstg, self.optivars]
        df = pd.DataFrame([data], columns=columns_vc, index=[self.file_name])
        con = sqlite3.connect(DB_BACKTEST)
        df.to_sql(self.savename, con, if_exists='append', chunksize=1000)
        self.df_tsg.to_sql(save_file_name, con, if_exists='append', chunksize=1000)
        con.close()
        self.wq.put([ui_num[f'{self.ui_gubun.replace("F", "")}상세기록'], self.df_tsg])

        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 백테스트 소요시간 {now() - self.start}'])
        self.sq.put(f'{self.backname} 백테스트를 완료하였습니다.')

        PltShow('최적화', self.df_tsg, self.df_bct, self.dict_cn, onegm, mdd, self.startday, self.endday, self.starttime, self.endtime,
                self.df_kp, self.df_kd, self.list_days, self.backname, back_text, label_text, save_file_name, self.schedul, False)

        self.mq.put('백테스트 완료')


class StopWhenNotUpdateBestCallBack:
    def __init__(self, wq, tq, back_count, ui_gubun, len_vars):
        self.wq         = wq
        self.tq         = tq
        self.back_count = back_count
        self.ui_gubun   = ui_gubun
        self.len_vars   = len_vars
        self.start = now()

    def __call__(self, study: optuna.study.Study, trial: optuna.trial.FrozenTrial) -> None:
        best_opt = study.best_value
        best_num = study.best_trial.number
        curr_num = trial.number
        last_num = best_num + self.len_vars
        rema_num = last_num - curr_num
        total_count = self.back_count * (last_num + 1)
        self.tq.put(['횟수변경', total_count])
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'<font color=#45cdf7>OPTUNA INFO 최고기준값[{best_opt:,}] 기준값갱신[{best_num}] 현재횟수[{curr_num}] 남은횟수[{rema_num}]</font>'])
        if curr_num == last_num:
            study.stop()


class Optimize:
    def __init__(self, wq, bq, sq, tq, lq, pq_list, stq_list, backname, ui_gubun):
        self.wq        = wq
        self.bq        = bq
        self.sq        = sq
        self.tq        = tq
        self.lq        = lq
        self.pq_list   = pq_list
        self.stq_list  = stq_list
        self.backname  = backname
        self.ui_gubun  = ui_gubun   # 'S', 'C', 'CF'
        self.dict_set  = DICT_SET
        self.gubun     = 'stock' if self.ui_gubun == 'S' else 'coin'
        self.vars      = {}
        self.study     = None
        self.dict_optuna_vars = {}
        self.Start()

    def Start(self):
        data = self.bq.get()
        if self.ui_gubun != 'CF':
            betting = float(data[0]) * 1000000  # 주식용 백만원 단위로 입력된 값
        else:
            betting = float(data[0])            # 바이낸스 선물용 단위 USDT
        starttime   = int(data[1])
        endtime     = int(data[2])
        buystg_name     = data[3]
        sellstg_name    = data[4]
        optivars_name   = data[5]
        dict_cn         = data[6]
        ccount      = int(data[7])
        std_text        = data[8].split(';')
        std_text        = [float(x) for x in std_text]
        optistandard    = data[9]
        back_count      = data[10]
        schedul         = data[11]
        df_kp           = data[12]
        df_kq           = data[13]
        weeks_train     = data[14]
        weeks_valid = int(data[15])
        weeks_test  = int(data[16])
        backengin_sday  = data[17]
        backengin_eday  = data[18]
        optuna_sampler  = data[19]
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
        if data[20] != '':
            try:
                optuna_fixvars  = [int(x.strip()) for x in data[20].split(',')]
            except:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '고정할 범위의 번호를 잘못입력하였습니다.'])
                self.SysExit(True)
        optuna_autostep = data[21]

        if weeks_train != 'ALL':
            weeks_train = int(weeks_train)
        else:
            allweeks = int(((strp_time('%Y%m%d', backengin_eday) - strp_time('%Y%m%d', backengin_sday)).days + 1) / 7)
            if 'T' in self.backname:
                weeks_train = allweeks - weeks_valid - weeks_test
            elif 'V' in self.backname:
                weeks_train = allweeks - weeks_valid
            else:
                weeks_train = allweeks

        if 'V' not in self.backname: weeks_valid = 0
        if 'T' not in self.backname: weeks_test = 0
        dt_endday   = strp_time('%Y%m%d', backengin_eday)
        startday    = timedelta_day(-(weeks_train + weeks_valid + weeks_test) * 7 + 1, dt_endday)
        sweek       = startday.weekday()
        if sweek   != 0: startday = timedelta_day(7 - sweek, startday)
        startday    = int(strf_time('%Y%m%d', startday))
        endday      = int(backengin_eday)
        train_days_ = [startday, int(strf_time('%Y%m%d', timedelta_day(-weeks_test * 7, dt_endday)))]
        valid_days_ = []
        if 'VC' in self.backname:
            for i in range(int(weeks_train / weeks_valid) + 1):
                valid_days_.append([
                    int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid * (i + 1) + weeks_test) * 7 + 1, dt_endday))),
                    int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid * i + weeks_test) * 7, dt_endday)))
                ])
        elif 'V' in self.backname:
            valid_days_.append([
                int(strf_time('%Y%m%d', timedelta_day(-(weeks_valid + weeks_test) * 7 + 1, dt_endday))),
                int(strf_time('%Y%m%d', timedelta_day(-weeks_test * 7, dt_endday)))
            ])
        else:
            valid_days_ = None
        if 'T' in self.backname:
            test_days = [int(strf_time('%Y%m%d', timedelta_day(-weeks_test * 7 + 1, dt_endday))), endday]
        else:
            next_day  = int(strf_time('%Y%m%d', timedelta_day(1, dt_endday)))
            test_days = [next_day, next_day]

        if int(backengin_sday) > startday:
            perio_text = '학습시간'
            if 'V' in self.backname:
                perio_text = f'{perio_text} + 검증기간'
            if 'T' in self.backname:
                perio_text = f'{perio_text} + 확인기간'
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'백테엔진에 로딩된 데이터가 부족합니다. 최소 {perio_text} 만큼의 데이터가 필요합니다'])
            self.SysExit(True)

        con   = sqlite3.connect(DB_STOCK_BACK if self.ui_gubun == 'S' else DB_COIN_BACK)
        query = GetMoneytopQuery(self.ui_gubun, startday, endday, starttime, endtime)
        df_mt = pd.read_sql(query, con)
        con.close()

        if len(df_mt) == 0 or back_count == 0:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '날짜 지정이 잘못되었거나 데이터가 존재하지 않습니다.'])
            self.SysExit(True)

        df_mt['일자'] = df_mt['index'].apply(lambda x: int(str(x)[:8]))
        day_list = list(set(df_mt['일자'].to_list()))
        day_list.sort()

        startday, endday = day_list[0], day_list[-1]
        train_days_list = [x for x in day_list if train_days_[0] <= x <= train_days_[1]]
        train_days = [train_days_list[0], train_days_list[-1], len(train_days_list)]
        if 'V' in self.backname:
            valid_days = []
            for vdays in valid_days_:
                valid_days_list = [x for x in day_list if vdays[0] <= x <= vdays[1]]
                valid_days.append([valid_days_list[0], valid_days_list[-1], len(valid_days_list)])
        else:
            valid_days = None
        if 'T' in self.backname:
            test_days_list = [x for x in day_list if test_days[0] <= x <= test_days[1]]
            test_days = [test_days_list[0], test_days_list[-1], len(test_days_list)]
        list_days = [train_days, valid_days, test_days]

        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 학습 기간 {train_days[0]} ~ {train_days[1]}'])
        if 'V' in self.backname:
            for vsday, veday, _ in valid_days:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 검증 기간 {vsday} ~ {veday}'])
        if 'T' in self.backname:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 확인 기간 {test_days[0]} ~ {test_days[1]}'])

        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 기간 추출 완료'])

        arry_bct = np.zeros((len(df_mt), 2), dtype='int64')
        arry_bct[:, 0] = df_mt['index'].values
        data = ['백테정보', arry_bct, betting, optistandard]
        for q in self.stq_list:
            q.put(data)
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
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'시스템 명령 오류 알림 - {self.backname} 변수설정 {e}'])
            self.SysExit(True)

        total_count = 0
        vars_type = []
        vars_ = []
        for var in list(self.vars.values()):
            low, high, gap = var[0]
            opti = var[1]
            vars_list = []
            if gap == 0:
                vars_list.append(low)
                vars_list.append(opti)
            else:
                k = 0
                while True:
                    v = low + gap * k
                    if (low < high and v <= high) or (low > high and v >= high):
                        vars_list.append(v)
                    else:
                        vars_list.append(opti)
                        break
                    k += 1
            vars_type.append(1 if low < high else 0)
            vars_.append(vars_list)
            if gap != 0: total_count += 1

        avg_list    = vars_[0][:-1]
        total_count *= ccount if ccount != 0 else 1
        total_count += 2
        total_count *= back_count
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 매도수전략 및 변수 설정 완료'])

        mq = Queue()
        tdq_list = self.stq_list[:5]
        vdq_list = self.stq_list[5:]
        Process(target=Total, args=(self.wq, self.sq, self.tq, mq, self.lq, tdq_list, vdq_list, self.stq_list, self.backname, self.ui_gubun, self.gubun)).start()
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 집계용 프로세스 생성 완료'])

        self.tq.put(['백테정보', betting, startday, endday, starttime, endtime, buystg_name, buystg, sellstg, optivars, dict_cn, std_text,
                     optistandard, schedul, df_kp, df_kq, list_days, len(day_list), weeks_train, weeks_valid, weeks_test])
        data = ['백테정보', betting, avg_list, startday, endday, starttime, endtime, buystg, sellstg]
        for q in self.pq_list:
            q.put(data)

        if 'B' in self.backname:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'<font color=#45cdf7>OPTUNA Sampler : {optuna_sampler}</font>'])
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 백테스터 시작'])

        if 'B' in self.backname:
            total_count_ = back_count * (len(self.vars) + 1)
            self.tq.put(['경우의수', total_count_, back_count])

            def objective(trial):
                optuna_vars = []
                for n, var_ in enumerate(list(self.vars.values())):
                    if n < 10:
                        trial_name = f'00{n}'
                    elif n < 100:
                        trial_name = f'0{n}'
                    else:
                        trial_name = f'{n}'

                    if not (var_[0][2] == 0 or n in optuna_fixvars):
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

                    optuna_vars.append([trial_])

                if str(optuna_vars) not in self.dict_optuna_vars.keys():
                    self.tq.put(['변수정보', optuna_vars, -1])
                    for ctq in self.stq_list:
                        ctq.put('백테시작')
                    for pq in self.pq_list:
                        pq.put(['변수정보', optuna_vars, -1])
                    data_ = mq.get()
                    if type(data_) == str:
                        ostd = 0
                        self.SysExit(True)
                    else:
                        ostd = data_[0]
                        self.dict_optuna_vars[str(optuna_vars)] = ostd
                else:
                    ostd = self.dict_optuna_vars[str(optuna_vars)]
                return ostd

            total_change = 1
            study_name = f'{self.backname}_{buystg_name}_{strf_time("%Y%m%d%H%M%S")}'
            optuna.logging.disable_default_handler()
            if sampler is None:
                self.study = optuna.create_study(storage=DB_OPTUNA, study_name=study_name, direction='maximize')
            else:
                self.study = optuna.create_study(storage=DB_OPTUNA, study_name=study_name, direction='maximize', sampler=sampler)
            self.study.optimize(objective, n_trials=10000, callbacks=[StopWhenNotUpdateBestCallBack(self.wq, self.tq, back_count, self.ui_gubun, len(self.vars))])
            for i, var in enumerate(list(self.study.best_params.values())):
                vars_[i][-1] = var
        else:
            self.tq.put(['경우의수', total_count, back_count])
            self.tq.put(['변수정보', vars_, -1])
            for q in self.stq_list:
                q.put('백테시작')
            for q in self.pq_list:
                q.put(['변수정보', vars_, -1])

            hstd = 0
            data = mq.get()
            if type(data) == str:
                self.SysExit(True)
            else:
                hstd = data[0]

            k = 1
            total_change = 0
            change_var_count = None
            for _ in range(ccount if ccount != 0 else 100):
                if ccount == 0:
                    if change_var_count == 0:
                        break
                    if k > 1:
                        self.tq.put(['재최적화'])
                        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'무한모드 {k}단계 시작, 최적값 변경 개수 [{change_var_count}]'])

                change_var_count = 0
                for i, vars_list in enumerate(vars_):
                    len_vars_list = len(vars_list) - 2
                    if len_vars_list > 0:
                        self.tq.put(['변수정보', vars_, i])
                        for q in self.stq_list:
                            q.put('백테시작')
                        for q in self.pq_list:
                            q.put(['변수정보', vars_, i])

                        for _ in range(len_vars_list):
                            data = mq.get()
                            if type(data) == str:
                                self.SaveOptiVars(total_change, optivars, optivars_, vars_, optivars_name)
                                self.SysExit(True)
                            else:
                                std, vars_key = data
                                curr_typ = vars_type[i]
                                curr_var = vars_list[vars_key]
                                high_var = vars_list[-1]
                                if std > hstd or (std == hstd and ((curr_typ and curr_var > high_var) or (not curr_typ and curr_var < high_var))):
                                    hstd = std
                                    vars_list[-1] = curr_var
                                    total_change += 1
                                    change_var_count += 1
                k += 1

        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '최적값 백테스트 시작'])
        self.tq.put(['변수정보', vars_, -2])
        for q in self.stq_list:
            q.put('백테시작')
        for q in self.pq_list:
            q.put(['변수정보', vars_, -2])
        _ = mq.get()
        self.SaveOptiVars(total_change, optivars, optivars_, vars_, optivars_name)

        mq.close()
        if self.dict_set['스톰라이브']: self.lq.put(self.backname.replace('O', '').replace('B', ''))
        self.SysExit(False)

    def SaveOptiVars(self, change, optivars, optivars_, vars_, optivars_name):
        if change > 0:
            optivars = optivars.split('self.vars[0]')[0]
            exec(optivars_, None, locals())
            for i in range(len(self.vars)):
                prev_var = self.vars[i][1]
                best_var = vars_[i][-1]
                if prev_var != best_var:
                    self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 결과 self.vars[{i}]의 최적값 {prev_var} -> {best_var}'])
                    self.vars[i][1] = best_var
                optivars += f'self.vars[{i}] = {self.vars[i]}\n'

            if 'T' not in self.backname:
                optivars = optivars[:-1]
                con = sqlite3.connect(DB_STRATEGY)
                cur = con.cursor()
                cur.execute(f"UPDATE {self.gubun}optivars SET 전략코드 = '{optivars}' WHERE `index` = '{optivars_name}'")
                con.commit()
                con.close()
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} {optivars_name}의 최적값 갱신 완료'])

    def SysExit(self, cancel):
        if cancel:
            self.wq.put([ui_num[f'{self.ui_gubun}백테바'], 0, 100, 0])
        else:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 완료'])
        time.sleep(1)
        sys.exit()
