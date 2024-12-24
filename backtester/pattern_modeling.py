import sys
import time
import sqlite3
import pandas as pd
from multiprocessing import Process, Queue
from utility.static import now, pickle_write
from utility.setting import ui_num, DICT_SET, PATTERN_PATH, DB_STRATEGY


class Total:
    def __init__(self, mq, wq, tq, ui_gubun, back_cnt, multi):
        self.mq           = mq
        self.wq           = wq
        self.tq           = tq
        self.ui_gubun     = ui_gubun
        self.back_count   = back_cnt
        self.multi        = multi
        self.pattern_buy  = None
        self.pattern_sell = None
        self.Start()

    def Start(self):
        start = now()
        bc, tc, dbpc, dspc = 0, 0, 0, 0
        list_pattern_buy  = []
        list_pattern_sell = []
        while True:
            data = self.tq.get()
            if data[0] == '백테완료':
                bc += 1
                self.wq.put((ui_num[f'{self.ui_gubun}백테바'], bc, self.back_count, start))
            elif data[0] == '학습결과':
                tc += 1
                _, pattern_buy, pattern_sell = data
                list_pattern_buy.append(pattern_buy)
                list_pattern_sell.append(pattern_sell)
                if tc == self.multi:
                    self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], '패턴 학습 매수 데이터 정리 시작'))
                    for i, pattern_buy in enumerate(list_pattern_buy):
                        if self.pattern_buy is None:
                            self.pattern_buy = pattern_buy
                        else:
                            for pattern in pattern_buy:
                                if pattern not in self.pattern_buy:
                                    self.pattern_buy.append(pattern)
                    for i, pattern_sell in enumerate(list_pattern_sell):
                        if self.pattern_sell is None:
                            self.pattern_sell = pattern_sell
                        else:
                            for pattern in pattern_sell:
                                if pattern not in self.pattern_sell:
                                    self.pattern_sell.append(pattern)
                    self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], '패턴 학습 매수 데이터 정리 완료'))
                    self.mq.put((self.pattern_buy, self.pattern_sell))
                    break

            elif data == '백테중지':
                self.mq.put('백테중지')
                break

        time.sleep(3)
        sys.exit()


class PatternModeling:
    def __init__(self, wq, bq, tq, bctq_list, beq_list, ui_gubun, back_cnt, multi):
        self.wq        = wq
        self.bq        = bq
        self.tq        = tq
        self.bctq_list = bctq_list
        self.beq_list  = beq_list
        self.ui_gubun  = ui_gubun
        self.back_cnt  = back_cnt
        self.multi     = multi
        self.dict_set  = DICT_SET
        self.gubun     = 'stock' if self.ui_gubun == 'S' else 'coin'
        self.Start()

    def Start(self):
        self.wq.put((ui_num[f'{self.ui_gubun}백테바'], 0, 100, 0))
        start_time = now()
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
        dict_pattern      = data[8]
        dict_pattern_buy  = data[9]
        dict_pattern_sell = data[10]

        con = sqlite3.connect(DB_STRATEGY)
        dfb = pd.read_sql(f'SELECT * FROM {self.gubun}buy', con).set_index('index')
        dfs = pd.read_sql(f'SELECT * FROM {self.gubun}sell', con).set_index('index')
        con.close()
        buystg  = dfb['전략코드'][buystg_name]
        sellstg = dfs['전략코드'][sellstg_name]

        mq = Queue()
        Process(target=Total, args=(mq, self.wq, self.tq, self.ui_gubun, self.back_cnt, self.multi)).start()

        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 시작'))
        data = ('학습정보', betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg, dict_pattern, dict_pattern_buy, dict_pattern_sell)
        for q in self.beq_list:
            q.put(data)

        data = mq.get()
        if type(data) == tuple:
            pattern_buy, pattern_sell = data
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 데이터 매수 : {len(pattern_buy)}개'))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 데이터 매도 : {len(pattern_sell)}개'))
            pickle_write(f"{PATTERN_PATH}/pattern_{self.gubun}_{dict_pattern['패턴이름']}_buy", pattern_buy)
            pickle_write(f"{PATTERN_PATH}/pattern_{self.gubun}_{dict_pattern['패턴이름']}_sell", pattern_sell)
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 데이터 저장 완료'))
            pattern_data = ('모델정보', pattern_buy, pattern_sell)
            for q in self.beq_list:
                q.put(pattern_data)
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 데이터 백테엔진으로 전송 완료'))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 백테스트 소요시간 {now() - start_time}'))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 완료'))

        time.sleep(3)
        sys.exit()
