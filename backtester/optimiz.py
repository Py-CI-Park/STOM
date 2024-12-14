import sys
import time
import sqlite3
import numpy as np
import pandas as pd
from multiprocessing import Process, Queue
from backtester.back_static import SubTotal, SendTextAndStd, GetBackResult, PltShow, GetMoneytopQuery
from utility.static import strf_time, strp_time, now, timedelta_day
from utility.setting import DB_STOCK_BACK, DB_COIN_BACK, ui_num, DB_STRATEGY, DB_BACKTEST, columns_vc, DICT_SET, DB_SETTING


class Total:
    def __init__(self, wq, sq, tq, mq, lq, tdq_list, vdq_list, ctq_list, backname, ui_gubun, gubun):
        self.wq           = wq
        self.sq           = sq
        self.tq           = tq
        self.mq           = mq
        self.lq           = lq
        self.tdq_list     = tdq_list
        self.vdq_list     = vdq_list
        self.ctq_list     = ctq_list
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
        self.arry_bct     = None

        self.dict_t       = {}
        self.dict_v       = {}

        self.vars         = None
        self.vars_list    = None
        self.vars_turn    = None
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
                _, vars_key, list_data, arry_bct = data
                if vars_key is not None:
                    columns = ['index', '종목명', '시가총액' if self.ui_gubun != 'CF' else '포지션', '매수시간', '매도시간',
                               '보유시간', '매수가', '매도가', '매수금액', '매도금액', '수익률', '수익금', '매도조건', '추가매수시간']
                    if self.vars_turn >= -1:
                        data = [columns, list_data, arry_bct]
                        train_days, valid_days, test_days = self.list_days
                        if valid_days is not None:
                            for i, vdays in enumerate(valid_days):
                                data_ = data + [vdays[0], vdays[1], test_days[0], train_days[2] - vdays[2], vdays[2], i, vars_key]
                                self.tdq_list[i].put(data_)
                                self.vdq_list[i].put(data_)
                        else:
                            data_ = data + [train_days[1], int(train_days[2] / 2), vars_key]
                            self.tdq_list[0].put(data_)
                            self.vdq_list[0].put(data_)
                    else:
                        self.df_tsg = pd.DataFrame(dict(zip(columns, list_data)))
                        self.df_tsg.set_index('index', inplace=True)
                        self.df_tsg.sort_index(inplace=True)
                        arry_bct = arry_bct[arry_bct[:, 1] > 0]
                        self.df_bct = pd.DataFrame(arry_bct[:, 1], columns=['보유종목수'], index=arry_bct[:, 0])
                        self.Report()

            elif data[0] == '백테완료':
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
                        if self.vars_turn >= 0:
                            _, valid_days, _ = self.list_days
                            if valid_days is not None:
                                for i, _ in enumerate(valid_days):
                                    self.stdp = SendTextAndStd(self.GetSendData(i), self.std_list, self.betting, None)
                            else:
                                self.stdp = SendTextAndStd(self.GetSendData(0), self.std_list, self.betting, None)
                        else:
                            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '매수전략을 만족하는 경우가 없어 결과를 표시할 수 없습니다.'])
                            self.mq.put('백테스트 완료')

            elif data[0] in ['TRAIN', 'VALID']:
                vars_key = data[-1]
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
                self.vars_list = data[1]
                self.vars_turn = data[2]
                self.vars      = [var[-1] for var in self.vars_list]
            elif data[0] == '재최적화':
                self.start = now()
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
        self.buystg_name  = data[6]
        self.buystg       = data[7]
        self.sellstg      = data[8]
        self.optivars     = data[9]
        self.dict_cn      = data[10]
        self.std_list     = data[11]
        self.optistandard = data[12]
        self.schedul      = data[13]
        self.arry_bct     = data[14]
        self.df_kp        = data[15]
        self.df_kd        = data[16]
        self.list_days    = data[17]
        self.day_count    = data[18]
        self.weeks_train  = data[19]
        self.weeks_valid  = data[20]
        self.weeks_test   = data[21]
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
        tc, atc, pc, mc, wr, ah, ap, tsp, tsg, mhct, onegm, cagr, tpi, mdd = result

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

        mdd_ = f'최대낙폭금액 {mdd:,.0f}{bet_unit}' if 'G' in self.optistandard else f'최대낙폭률 {mdd:,.2f}%'
        label_text = f'변수 {self.vars}\n종목당 배팅금액 {int(self.betting):,}{bet_unit}, 필요자금 {onegm:,}{bet_unit}, ' \
                     f'거래횟수 {tc}회, 일평균거래횟수 {atc}회, 적정최대보유종목수 {mhct}개, 평균보유기간 {ah:.2f}초\n' \
                     f'익절 {pc}회, 손절 {mc}회, 승률 {wr:.2f}%, 평균수익률 {ap:.2f}%, 수익률합계 {tsp:.2f}%, ' \
                     f'{mdd_}, 수익금합계 {tsg:,}{bet_unit}, 매매성능지수 {tpi:.2f}, 연간예상수익률 {cagr:.2f}%'

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


class Optimize:
    def __init__(self, wq, bq, sq, tq, lq, pq_list, ctq_list, backname, ui_gubun):
        self.wq        = wq
        self.bq        = bq
        self.sq        = sq
        self.tq        = tq
        self.lq        = lq
        self.pq_list   = pq_list
        self.ctq_list  = ctq_list
        self.backname  = backname   # '최적화OH', '최적화OV', '최적화OVC', '최적화OHT', '최적화OVT', '최적화OVCT'
        self.ui_gubun  = ui_gubun   # 'S', 'C', 'CF'
        self.dict_set  = DICT_SET
        self.gubun     = 'stock' if self.ui_gubun == 'S' else 'coin'
        self.vars      = {}
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
        if weeks_train != 'ALL':
            weeks_train = int(weeks_train)
        else:
            allweeks = int(((strp_time('%Y%m%d', backengin_eday) - strp_time('%Y%m%d', backengin_sday)).days + 1) / 7)
            if 'HT' in self.backname:
                weeks_train = allweeks - weeks_test
            elif 'T' in self.backname:
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
        elif 'OH' in self.backname:
            valid_days_ = None
        if 'T' in self.backname:
            test_days = [int(strf_time('%Y%m%d', timedelta_day(-weeks_test * 7 + 1, dt_endday))), endday]
        else:
            next_day  = int(strf_time('%Y%m%d', timedelta_day(1, dt_endday)))
            test_days = [next_day, next_day]

        if int(backengin_sday) > startday:
            if 'OHT' in self.backname:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 + 확인기간 만큼의 데이터가 필요합니다'])
            elif 'OH' in self.backname:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 만큼의 데이터가 필요합니다'])
            elif 'T' in self.backname:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 + 검증기간 + 확인기간 만큼의 데이터가 필요합니다'])
            else:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '백테엔진에 로딩된 데이터가 부족합니다. 최소 학습기간 + 검증기간 만큼의 데이터가 필요합니다'])
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
        data = ['보유종목수어레이', arry_bct]
        for q in self.ctq_list:
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
        tdq_list = []
        vdq_list = []
        if 'V' in self.backname:
            for _ in list_days[1]:
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

        Process(target=Total, args=(self.wq, self.sq, self.tq, mq, self.lq, tdq_list, vdq_list, self.ctq_list, self.backname, self.ui_gubun, self.gubun)).start()
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 집계용 프로세스 생성 완료'])

        self.tq.put(['백테정보', betting, startday, endday, starttime, endtime, buystg_name, buystg, sellstg, optivars,
                     dict_cn, std_text, optistandard, schedul, arry_bct, df_kp, df_kq, list_days, len(day_list), weeks_train, weeks_valid, weeks_test])
        data = ['백테정보', betting, avg_list, startday, endday, starttime, endtime, buystg, sellstg]
        for q in self.pq_list:
            q.put(data)

        self.tq.put(['경우의수', total_count, back_count])
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 백테스터 시작'])

        self.tq.put(['변수정보', vars_, -1])
        for q in self.ctq_list:
            q.put('백테시작')
        for q in self.pq_list:
            q.put(['변수정보', vars_, -1])
        hstd, _ = mq.get()

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
                    for q in self.ctq_list:
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
        for q in self.ctq_list:
            q.put('백테시작')
        for q in self.pq_list:
            q.put(['변수정보', vars_, -2])
        _ = mq.get()
        self.SaveOptiVars(total_change, optivars, optivars_, vars_, optivars_name)

        mq.close()
        if self.dict_set['스톰라이브']: self.lq.put(self.backname)
        self.SysExit(False)

    def SaveOptiVars(self, change, optivars, optivars_, vars_, optivars_name):
        if change > 0:
            cur_vars = [var[-1] for var in vars_]
            optivars = optivars.split('self.vars[0]')[0]
            exec(optivars_, None, locals())
            for i in range(len(self.vars)):
                if self.vars[i][1] != cur_vars[i]:
                    self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 결과 self.vars[{i}]의 최적값 {self.vars[i][1]} -> {cur_vars[i]}'])
                    self.vars[i][1] = cur_vars[i]
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
