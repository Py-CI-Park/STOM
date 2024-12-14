import zmq
import time
import numpy as np
from multiprocessing import Process


class ZmqServer:
    def __init__(self):
        zctx = zmq.Context()
        self.sock = zctx.socket(zmq.PUB)
        self.sock.bind(f'tcp://*:5556')
        self.Start()

    def Start(self):
        while True:
            time.sleep(2)
            data = np.random.rand(5)
            self.sock.send_string('server', zmq.SNDMORE)
            self.sock.send_pyobj(data)


class ZmqClient1:
    def __init__(self):
        zctx = zmq.Context()
        self.sock = zctx.socket(zmq.SUB)
        self.sock.connect(f'tcp://localhost:5556')
        self.sock.setsockopt(zmq.SUBSCRIBE, b'server')
        self.Start()

    def Start(self):
        while True:
            channel = self.sock.recv_string()
            data    = self.sock.recv_pyobj()
            print('C1', channel, data)


class ZmqClient2:
    def __init__(self):
        zctx = zmq.Context()
        self.sock = zctx.socket(zmq.SUB)
        self.sock.connect(f'tcp://localhost:5556')
        self.sock.setsockopt(zmq.SUBSCRIBE, b'server')
        self.Start()

    def Start(self):
        while True:
            channel = self.sock.recv_string()
            data    = self.sock.recv_pyobj()
            time.sleep(1)
            print('C2', channel, data)


if __name__ == '__main__':
    Process(target=ZmqServer).start()
    Process(target=ZmqClient1).start()
    Process(target=ZmqClient2).start()
