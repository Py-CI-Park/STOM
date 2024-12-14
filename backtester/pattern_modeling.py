import sys
import time
import numpy as np
from multiprocessing import Process, Queue
from utility.static import now, pickle_write
from utility.setting import ui_num, DICT_SET, DB_PATH


class Total:
    def __init__(self, mq, wq, tq, ui_gubun, multi):
        self.mq         = mq
        self.wq         = wq
        self.tq         = tq
        self.ui_gubun   = ui_gubun
        self.multi      = multi
        self.start      = now()
        self.pattern_buy  = None
        self.pattern_sell = None
        self.Start()

    def Start(self):
        bc = 0
        while True:
            data = self.tq.get()
            if data[0] == '학습결과':
                bc += 1
                _, pattern_buy, pattern_sell = data
                if self.pattern_buy is None:
                    self.pattern_buy = pattern_buy
                else:
                    for pattern in pattern_buy:
                        if pattern not in self.pattern_buy:
                            self.pattern_buy = np.r_[self.pattern_buy, np.array([pattern])]
                if self.pattern_sell is None:
                    self.pattern_sell = pattern_sell
                else:
                    for pattern in pattern_sell:
                        if pattern not in self.pattern_sell:
                            self.pattern_sell = np.r_[self.pattern_sell, np.array([pattern])]

                self.wq.put((ui_num[f'{self.ui_gubun}백테바'], bc, self.multi, self.start))
                if bc == self.multi:
                    self.mq.put((self.pattern_buy, self.pattern_sell))
                    break

            elif data == '백테중지':
                self.mq.put('백테중지')
                break

        time.sleep(3)
        sys.exit()


class PatternModeling:
    def __init__(self, wq, bq, tq, stq_list, pq_list, ui_gubun, multi):
        self.wq       = wq
        self.bq       = bq
        self.tq       = tq
        self.stq_list = stq_list
        self.pq_list  = pq_list
        self.ui_gubun = ui_gubun
        self.multi    = multi
        self.dict_set = DICT_SET
        self.gubun    = 'stock' if self.ui_gubun == 'S' else 'coin'
        self.Start()

    def Start(self):
        data = self.bq.get()
        startday  = int(data[0])
        endday    = int(data[1])
        starttime = int(data[2])
        endtime   = int(data[3])

        mq = Queue()
        Process(target=Total, args=(mq, self.wq, self.tq, self.ui_gubun, self.multi)).start()

        dict_index = {}
        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 시작'))
        for q in self.pq_list:
            q.put(('학습정보', startday, endday, starttime, endtime, 60, 600, dict_index))

        data = mq.get()
        if type(data) == tuple:
            pattern_buy, pattern_sell = data
            print(pattern_buy)
            print(pattern_sell)
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'매수 패턴의 개수 : {len(pattern_buy)}'))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'매수 패턴의 개수 : {len(pattern_sell)}'))
            pickle_write(f'{DB_PATH}/pattern_buy', pattern_buy)
            pickle_write(f'{DB_PATH}/pattern_sell', pattern_sell)
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 데이터 저장 완료'))
            pattern_data = ('모델정보', pattern_buy, pattern_sell)
            for q in self.pq_list:
                q.put(pattern_data)
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'백테엔진으로 패턴 데이터 전송 완료'))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 완료'))

        time.sleep(3)
        sys.exit()
