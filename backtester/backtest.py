import re
import sys
import time
import sqlite3
import numpy as np
import pandas as pd
from multiprocessing import Process, Queue
from backtester.back_static import GetBackResult, PltShow, GetMoneytopQuery
from ui.set_text import example_stock_buy, example_stock_sell
from utility.static import now, strf_time
from utility.setting import DB_STRATEGY, DB_BACKTEST, ui_num, stockreadlines, columns_vj, DICT_SET, DB_STOCK_BACK, DB_COIN_BACK, coinreadlines


class Total:
    def __init__(self, wq, sq, tq, mq, lq, bq, ctq_list, backname, ui_gubun, gubun):
        self.wq           = wq
        self.sq           = sq
        self.tq           = tq
        self.mq           = mq
        self.lq           = lq
        self.bq           = bq
        self.ctq_list     = ctq_list
        self.backname     = backname
        self.ui_gubun     = ui_gubun
        self.gubun        = gubun
        self.dict_set     = DICT_SET
        gubun_text        = f'{self.gubun}_future' if self.ui_gubun == 'CF' else self.gubun
        self.savename     = f'{gubun_text}_bt'

        self.start        = now()
        self.back_count   = None
        self.dict_bkvc    = {}
        self.dict_bkvc_   = {}
        self.vb_file_name = strf_time('%Y%m%d%H%M%S', now())

        self.buystg_name  = None
        self.buystg       = None
        self.sellstg      = None
        self.dict_cn      = None
        self.blacklist    = None
        self.day_count    = None

        self.betting      = None
        self.startday     = None
        self.endday       = None
        self.starttime    = None
        self.endtime      = None
        self.avgtime      = None
        self.schedul      = None

        self.df_tsg       = None
        self.df_bct       = None

        self.df_kp        = None
        self.df_kd        = None
        self.back_club    = None

        self.dict_t       = {}
        self.dict_v       = {}
        self.insertlist   = []

        self.Start()

    def Start(self):
        tc  = 0
        bc  = 0
        while True:
            data = self.tq.get()
            if data[0] == '백테결과':
                _, vars_key, list_data, arry_bct = data
                if vars_key is not None:
                    columns = ['index', '종목명', '시가총액' if self.ui_gubun != 'CF' else '포지션', '매수시간', '매도시간',
                               '보유시간', '매수가', '매도가', '매수금액', '매도금액', '수익률', '수익금', '매도조건', '추가매수시간']
                    self.df_tsg = pd.DataFrame(dict(zip(columns, list_data)))
                    self.df_tsg.set_index('index', inplace=True)
                    self.df_tsg.sort_index(inplace=True)
                    arry_bct = arry_bct[arry_bct[:, 1] > 0]
                    self.df_bct = pd.DataFrame(arry_bct[:, 1], columns=['보유종목수'], index=arry_bct[:, 0])
                    if self.blacklist: self.InsertBlacklist()
                    self.Report()

            elif data[0] == '백테완료':
                bc  += 1
                if data[1]: tc += 1
                self.wq.put([ui_num[f'{self.ui_gubun}백테바'], bc, self.back_count, self.start])

                if bc == self.back_count:
                    bc = 0
                    if tc > 0:
                        tc = 0
                        for ctq in self.ctq_list:
                            ctq.put('백테완료')
                    else:
                        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '매수전략을 만족하는 경우가 없어 결과를 표시할 수 없습니다.'])
                        self.mq.put('백테스트 완료')

            elif data[0] == '백테정보':
                self.betting     = data[1]
                self.avgtime     = data[2]
                self.startday    = data[3]
                self.endday      = data[4]
                self.starttime   = data[5]
                self.endtime     = data[6]
                self.buystg_name = data[7]
                self.buystg      = data[8]
                self.sellstg     = data[9]
                self.dict_cn     = data[10]
                self.back_count  = data[11]
                self.day_count   = data[12]
                self.blacklist   = data[13]
                self.schedul     = data[14]
                self.df_kp       = data[15]
                self.df_kd       = data[16]
                self.back_club   = data[17]

            elif data == '백테중지':
                self.mq.put('백테중지')
                break

        time.sleep(1)
        sys.exit()

    def InsertBlacklist(self):
        name_list = list(set(self.df_tsg['종목명'].to_list()))
        dict_code = {name: code for code, name in self.dict_cn.items()}
        for name in name_list:
            if name not in dict_code.keys():
                continue
            code = dict_code[name]
            df_tsg = self.df_tsg[self.df_tsg['종목명'] == name]
            trade_count = len(df_tsg)
            total_eyun = df_tsg['수익금'].sum()
            if self.ui_gubun == 'S':
                if trade_count >= 10 and total_eyun < 0 and code + '\n' not in stockreadlines:
                    stockreadlines.append(code + '\n')
                    self.insertlist.append(code)
            else:
                if trade_count >= 10 and total_eyun < 0 and code + '\n' not in coinreadlines:
                    coinreadlines.append(code + '\n')
                    self.insertlist.append(code)
        if len(self.insertlist) > 0:
            if self.ui_gubun == 'S':
                with open('./utility/blacklist_stock.txt', 'w') as f:
                    f.write(''.join(stockreadlines))
            else:
                with open('./utility/blacklist_coin.txt', 'w') as f:
                    f.write(''.join(coinreadlines))

    def Report(self):
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 소요시간 {now() - self.start}'])
        if self.buystg_name == '벤치전략':
            self.mq.put('벤치테스트 완료')
        else:
            self.df_tsg, self.df_bct, result = GetBackResult(self.df_tsg, self.df_bct, self.betting, '', self.day_count)
            tc, atc, pc, mc, wr, ah, ap, tsp, tsg, mhct, onegm, cagr, tpi, mdd, mdd_ = result

            save_time = strf_time('%Y%m%d%H%M%S')
            startday, endday, starttime, endtime = str(self.startday), str(self.endday), str(self.starttime).zfill(6), str(self.endtime).zfill(6)
            startday  = startday[:4] + '-' + startday[4:6] + '-' + startday[6:]
            endday    = endday[:4] + '-' + endday[4:6] + '-' + endday[6:]
            starttime = starttime[:2] + ':' + starttime[2:4] + ':' + starttime[4:]
            endtime   = endtime[:2] + ':' + endtime[2:4] + ':' + endtime[4:]
            bet_unit  = '원' if self.ui_gubun != 'CF' else 'USDT'
            back_text = f'백테기간 : {startday}~{endday}, 백테시간 : {starttime}~{endtime}, 거래일수 : {self.day_count}, 평균값계산틱수 : {self.avgtime}'
            label_text = f'종목당 배팅금액 {int(self.betting):,}{bet_unit}, 필요자금 {onegm:,}{bet_unit}, '\
                         f'거래횟수 {tc}회, 일평균거래횟수 {atc}회, 적정최대보유종목수 {mhct}개, 평균보유기간 {ah:.2f}초\n' \
                         f'익절 {pc}회, 손절 {mc}회, 승률 {wr:.2f}%, 평균수익률 {ap:.2f}%, 수익률합계 {tsp:.2f}%, '\
                         f'최대낙폭률 {mdd:.2f}%, 수익금합계 {tsg:,}{bet_unit}, 매매성능지수 {tpi:.2f}, 연간예상수익률 {cagr:.2f}%'
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '백테스팅 결과\n' + label_text])

            if self.dict_set['스톰라이브']:
                backlive_text = f'back;{startday}~{endday};{starttime}~{endtime};{self.day_count};{self.avgtime};{int(self.betting)};'\
                                f'{onegm};{tc};{atc};{mhct};{ah:.2f};{pc};{mc};{wr:.2f};{ap:.2f};{tsp:.2f};{mdd:.2f};{tsg};{cagr:.2f}'
                self.lq.put(backlive_text)

            data = [int(self.betting), onegm, tc, atc, mhct, ah, pc, mc, wr, ap, tsp, mdd, tsg, tpi, cagr, self.buystg, self.sellstg]
            df = pd.DataFrame([data], columns=columns_vj, index=[save_time])

            save_file_name = f'{self.savename}_{self.buystg_name}_{save_time}'
            con = sqlite3.connect(DB_BACKTEST)
            df.to_sql(self.savename, con, if_exists='append', chunksize=1000)
            self.df_tsg.to_sql(save_file_name, con, if_exists='append', chunksize=1000)
            con.close()
            self.wq.put([ui_num[f'{self.ui_gubun.replace("F", "")}상세기록' if self.ui_gubun == 'CF' else f'{self.ui_gubun}상세기록'], self.df_tsg])

            if self.blacklist:
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'블랙리스트 추가 {self.insertlist}'])
            self.sq.put(f'{self.backname}를 완료하였습니다.')

            if self.back_club:
                buystg_text  = ('\n'.join([x for x in self.buystg.split('if 매수:')[0].split('\n') if '#' not in x])).split(' ')
                buystg_text  = [x for x in buystg_text if x != '매수' and re.compile('[가-힣]+').findall(x) != []]
                buystg_text  = [x.replace('(', '').replace(')', '').replace(':', '').replace('\n', '') for x in set(buystg_text)]
                buy_vars = '------------------------------------------------------------------------------------ 매수변수목록 ------------------------------------------------------------------------------------\n'
                for i, text in enumerate(buystg_text):
                    if (i + 1) % 11 == 0:
                        buy_vars = f'{buy_vars}, {text},\n'
                    elif i == 0 or i % 11 == 0:
                        buy_vars = f'{buy_vars}{text}'
                    else:
                        buy_vars = f'{buy_vars}, {text}'
                sellstg_text = ('\n'.join([x for x in self.sellstg.split('if 매도:')[0].split('\n') if '#' not in x])).split(' ')
                sellstg_text = [x for x in sellstg_text if x != '매도' and re.compile('[가-힣]+').findall(x) != []]
                sellstg_text = [x.replace('(', '').replace(')', '').replace(':', '').replace('\n', '') for x in set(sellstg_text)]
                sell_vars = '------------------------------------------------------------------------------------ 매도변수목록 ------------------------------------------------------------------------------------\n'
                for i, text in enumerate(sellstg_text):
                    if (i + 1) % 11 == 0:
                        sell_vars = f'{sell_vars}, {text},\n'
                    elif i == 0 or i % 11 == 0:
                        sell_vars = f'{sell_vars}{text}'
                    else:
                        sell_vars = f'{sell_vars}, {text}'

                PltShow('백테스트', self.df_tsg, self.df_bct, self.dict_cn, onegm, mdd, self.startday, self.endday, self.starttime, self.endtime,
                        self.df_kp, self.df_kd, None, self.backname, back_text, label_text, save_file_name, self.schedul, False, buy_vars=buy_vars, sell_vars=sell_vars)
            else:
                if not self.dict_set['그래프저장하지않기']:
                    PltShow('백테스트', self.df_tsg, self.df_bct, self.dict_cn, onegm, mdd, self.startday, self.endday, self.starttime, self.endtime,
                            self.df_kp, self.df_kd, None, self.backname, back_text, label_text, save_file_name, self.schedul, self.dict_set['그래프띄우지않기'])

            self.mq.put(f'{self.backname} 완료')


class BackTest:
    def __init__(self, wq, bq, sq, tq, lq, pq_list, ctq_list, backname, ui_gubun):
        self.wq       = wq
        self.bq       = bq
        self.sq       = sq
        self.tq       = tq
        self.lq       = lq
        self.pq_list  = pq_list
        self.ctq_list = ctq_list
        self.backname = backname
        self.ui_gubun = ui_gubun
        self.dict_set = DICT_SET
        self.gubun    = 'stock' if self.ui_gubun == 'S' else 'coin'
        self.Start()

    def Start(self):
        data = self.bq.get()
        if self.ui_gubun != 'CF':
            betting = float(data[0]) * 1000000
        else:
            betting = float(data[0])
        avgtime   = int(data[1])
        startday  = int(data[2])
        endday    = int(data[3])
        starttime = int(data[4])
        endtime   = int(data[5])
        buystg_name   = data[6]
        sellstg_name  = data[7]
        dict_cn       = data[8]
        back_count    = data[9]
        bl            = data[10]
        schedul       = data[11]
        df_kp         = data[12]
        df_kq         = data[13]
        back_club     = data[14]

        if buystg_name == '벤치전략':
            betting   = 20000000
            avgtime   = 30
            starttime = 90030
            endtime   = 93000

        con   = sqlite3.connect(DB_STOCK_BACK if self.ui_gubun == 'S' else DB_COIN_BACK)
        query = GetMoneytopQuery(self.ui_gubun, startday, endday, starttime, endtime)
        df_mt = pd.read_sql(query, con)
        con.close()

        if len(df_mt) == 0 or back_count == 0:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '날짜 지정이 잘못되었거나 데이터가 존재하지 않습니다.\n'])
            self.SysExit(True)

        df_mt['일자'] = df_mt['index'].apply(lambda x: int(str(x)[:8]))
        day_count = len(list(set(df_mt['일자'].to_list())))
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 기간 추출 완료'])

        arry_bct = np.zeros((len(df_mt), 2), dtype='int64')
        arry_bct[:, 0] = df_mt['index'].values
        data = ['보유종목수어레이', arry_bct]
        for q in self.ctq_list:
            q.put(data)
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 보유종목수 어레이 생성 완료'])

        if buystg_name != '벤치전략':
            con = sqlite3.connect(DB_STRATEGY)
            dfb = pd.read_sql(f'SELECT * FROM {self.gubun}buy', con).set_index('index')
            dfs = pd.read_sql(f'SELECT * FROM {self.gubun}sell', con).set_index('index')
            con.close()
            buystg  = dfb['전략코드'][buystg_name]
            sellstg = dfs['전략코드'][sellstg_name]
        else:
            buystg  = example_stock_buy
            sellstg = example_stock_sell

        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 매도수전략 설정 완료'])

        mq = Queue()
        Process(target=Total, args=(self.wq, self.sq, self.tq, mq, self.lq, self.bq, self.ctq_list, self.backname, self.ui_gubun, self.gubun)).start()
        self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 집계용 프로세스 생성 완료'])

        self.tq.put(['백테정보', betting, avgtime, startday, endday, starttime, endtime, buystg_name, buystg, sellstg,
                     dict_cn, back_count, day_count, bl, schedul, df_kp, df_kq, back_club])
        data = ['백테정보', betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg, None]

        for q in self.ctq_list:
            q.put('백테시작')
        for q in self.pq_list:
            q.put(data)

        data = mq.get()
        if buystg_name == '벤치전략':
            bench_point = 0
            total_ticks = 0
            for pq in self.pq_list:
                pq.put(['벤치점수요청'])
            for i, _ in enumerate(self.pq_list):
                tc, ts, bp = self.bq.get()
                total_ticks += tc
                bench_point += bp
                self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'프로세스[{i + 1}] 틱수 [{tc:,.0f}] 초당연산틱수 [{bp:,.0f}]'])
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'벤치점수 집계 전체틱수 [{total_ticks:,.0f}] 초당연산틱수합계 [{bench_point:,.0f}]'])

        if self.dict_set['스톰라이브']: self.lq.put(self.backname)
        if data == f'{self.backname} 완료':
            if buystg_name == '벤치전략':
                self.SysExit(False, True)
            else:
                self.SysExit(False)
        else:
            self.SysExit(True)

    def SysExit(self, cancel, bench=False):
        if cancel:
            self.wq.put([ui_num[f'{self.ui_gubun}백테바'], 0, 100, 0])
        elif bench:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], '벤치테스트 완료'])
        else:
            self.wq.put([ui_num[f'{self.ui_gubun}백테스트'], f'{self.backname} 완료'])
        time.sleep(1)
        sys.exit()
