import os
import time
import psutil
import datetime
import numpy as np
from sys import getsizeof
from multiprocessing import Process, Queue


class MainProcess:
    def __init__(self, q_):
        self.q = q_
        self.Start()

    def Start(self):
        get_time = datetime.datetime.now() + datetime.timedelta(seconds=20)
        while True:
            if datetime.datetime.now() > get_time:
                data = self.q.get()

            p = psutil.Process(os.getpid())
            memory = round(p.memory_info()[0] / 2 ** 20, 2)
            print(f'MainProcess\tMemonry {memory:>7.2f}MB')
            time.sleep(1)


class SubProcess:
    def __init__(self, q_):
        self.q = q_
        self.tm = 0
        self.Start()

    def Start(self):
        while True:
            ar = np.random.rand(10000000)
            ar_msize = round(getsizeof(ar) / 1000000, 2)
            self.tm = round(self.tm + ar_msize, 2)

            p = psutil.Process(os.getpid())
            memory = round(p.memory_info()[0] / 2 ** 20, 2)

            if memory + ar_msize < 1400:
                self.q.put(ar)

            print(f'SubProcess\tMemonry {memory:>7.2f}MB\tPut Size {ar_msize}MB\tTotal Put Size {self.tm:>7.2f}MB')
            time.sleep(1)


if __name__ == '__main__':
    q = Queue()
    Process(target=SubProcess, args=(q,), daemon=True).start()
    MainProcess(q)
