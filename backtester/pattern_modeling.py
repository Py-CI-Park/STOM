import sys
import time
import numpy as np
from multiprocessing import Process, Queue
from utility.static import now
from utility.setting import ui_num, DICT_SET, DB_PATH


class Total:
    def __init__(self, mq, wq, tq, stq_list, ui_gubun, back_count):
        self.mq         = mq
        self.wq         = wq
        self.tq         = tq
        self.stq_list   = stq_list
        self.ui_gubun   = ui_gubun
        self.back_count = back_count
        self.start      = now()
        self.arry_pattern_buy  = None
        self.arry_pattern_sell = None
        self.Start()

    def Start(self):
        bc = 0
        st = 0
        while True:
            data = self.tq.get()
            if data == '학습완료':
                bc += 1
                self.wq.put((ui_num[f'{self.ui_gubun}백테바'], bc, self.back_count, self.start))
                self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 중 ... [{bc}/{self.back_count}]'))

                if bc == self.back_count:
                    for stq in self.stq_list:
                        stq.put('학습완료')

            elif data[0] == '학습결과':
                _, buy_arry, sell_arry = data
                if buy_arry is not None:
                    if self.arry_pattern_buy is None:
                        self.arry_pattern_buy = buy_arry
                    else:
                        self.arry_pattern_buy = np.r_[self.arry_pattern_buy, buy_arry]
                if sell_arry is not None:
                    if self.arry_pattern_sell is None:
                        self.arry_pattern_sell = sell_arry
                    else:
                        self.arry_pattern_sell = np.r_[self.arry_pattern_sell, sell_arry]

                st += 1
                if st == 20:
                    # self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 데이터 중 매도패턴에 있는 매수패턴 삭제 중 ...'))
                    # delete_index = []
                    # for i, pattern_buy in enumerate(self.arry_pattern_buy):
                    #     if pattern_buy in self.arry_pattern_sell:
                    #         delete_index.append(i)
                    # if delete_index:
                    #     self.arry_pattern_buy = np.delete(self.arry_pattern_buy, delete_index, 0)
                    # self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'매도패턴에 있는 매수패턴 [{len(delete_index)}]개 삭제 완료'))

                    self.mq.put((self.arry_pattern_buy, self.arry_pattern_sell))
                    break

            elif data == '백테중지':
                self.mq.put('백테중지')
                break

        time.sleep(3)
        sys.exit()


class PatternModeling:
    def __init__(self, wq, bq, tq, stq_list, pq_list, ui_gubun):
        self.wq       = wq
        self.bq       = bq
        self.tq       = tq
        self.stq_list = stq_list
        self.pq_list  = pq_list
        self.ui_gubun = ui_gubun
        self.dict_set = DICT_SET
        self.gubun    = 'stock' if self.ui_gubun == 'S' else 'coin'
        self.Start()

    def Start(self):
        data = self.bq.get()
        startday  = int(data[0])
        endday    = int(data[1])
        starttime = int(data[2])
        endtime   = int(data[3])
        back_count    = data[4]

        mq = Queue()
        Process(target=Total, args=(mq, self.wq, self.tq, self.stq_list, self.ui_gubun, back_count)).start()

        self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 시작'))
        for q in self.stq_list:
            q.put('학습시작')
        for q in self.pq_list:
            q.put(('학습정보', startday, endday, starttime, endtime, 30, 600, 100))

        data = mq.get()
        if type(data) == tuple:
            arry_pattern_buy, arry_pattern_sell = data
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'매수 패턴의 개수 : {len(arry_pattern_buy)}'))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'매도 패턴의 개수 : {len(arry_pattern_sell)}'))
            np.save(f'{DB_PATH}/pattern_buy', arry_pattern_buy)
            np.save(f'{DB_PATH}/pattern_sell', arry_pattern_sell)
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 데이터 저장 완료'))
            for q in self.pq_list:
                q.put(('모델정보', arry_pattern_buy, arry_pattern_sell))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'백테엔진으로 패턴 데이터 전송 완료'))
            self.wq.put((ui_num[f'{self.ui_gubun}백테스트'], f'패턴 학습 완료'))
        time.sleep(3)
        sys.exit()
