
class BackCollector:
    def __init__(self, vk, tq, bctqs, buystd):
        self.vars_key   = vk
        self.tq         = tq
        self.bctqs      = bctqs
        self.bctq       = self.bctqs[self.vars_key]
        self.buystd     = buystd
        self.list_tsg   = None
        self.arry_bct   = None
        self.arry_bct_  = None
        self.complete1  = False
        self.complete2  = False
        self.separation = None
        self.ddict_tsg  = {}
        self.ddict_bct  = {}
        self.MainLoop()

    def MainLoop(self):
        while True:
            data = self.bctq.get()
            if data[0] == '백테결과':
                self.CollectData(data)
            elif data[0] == '백테완료':
                self.complete1 = True
                self.separation = data[1]
            elif data == '결과분리':
                self.DivideData()
            elif data[0] == '분리결과':
                self.ConcatData(data)
            elif data == '결과전송':
                self.complete2 = True
            elif data[0] == '백테정보':
                self.arry_bct_ = data[1]
            elif data == '백테시작':
                self.complete1 = False
                self.complete2 = False
                self.list_tsg  = None
                self.arry_bct  = None
                self.ddict_tsg = {}
                self.ddict_bct = {}

            if self.complete1 and self.bctq.empty():
                if self.separation == '분리집계':
                    self.tq.put('집계완료')
                else:
                    self.tq.put(('백테결과', self.vars_key, self.ddict_tsg, self.ddict_bct))
                self.complete1 = False

            if self.complete2 and self.bctq.empty():
                self.tq.put(('백테결과', self.vars_key, self.list_tsg, self.arry_bct))
                self.complete2 = False

    def CollectData(self, data):
        _, 종목명, 시가총액또는포지션, 매수시간, 매도시간, 보유시간, 매수가, 매도가, 매수금액, 매도금액, 수익률, 수익금, 매도조건, 추가매수시간, 잔량없음, vars_turn, vars_key = data
        if vars_turn not in self.ddict_tsg.keys():
            self.ddict_tsg[vars_turn] = {}
            self.ddict_bct[vars_turn] = {}
        if vars_key not in self.ddict_tsg[vars_turn].keys():
            self.ddict_tsg[vars_turn][vars_key] = [[] for _ in range(14)]
            self.ddict_bct[vars_turn][vars_key] = self.arry_bct_.copy()

        index = str(매수시간) if self.buystd else str(매도시간)
        self.ddict_tsg[vars_turn][vars_key][0].append(index)
        self.ddict_tsg[vars_turn][vars_key][1].append(종목명)
        self.ddict_tsg[vars_turn][vars_key][2].append(시가총액또는포지션)
        self.ddict_tsg[vars_turn][vars_key][3].append(매수시간)
        self.ddict_tsg[vars_turn][vars_key][4].append(매도시간)
        self.ddict_tsg[vars_turn][vars_key][5].append(보유시간)
        self.ddict_tsg[vars_turn][vars_key][6].append(매수가)
        self.ddict_tsg[vars_turn][vars_key][7].append(매도가)
        self.ddict_tsg[vars_turn][vars_key][8].append(매수금액)
        self.ddict_tsg[vars_turn][vars_key][9].append(매도금액)
        self.ddict_tsg[vars_turn][vars_key][10].append(수익률)
        self.ddict_tsg[vars_turn][vars_key][11].append(수익금)
        self.ddict_tsg[vars_turn][vars_key][12].append(매도조건)
        self.ddict_tsg[vars_turn][vars_key][13].append(추가매수시간)

        if 잔량없음:
            arry_bct  = self.ddict_bct[vars_turn][vars_key]
            arry_bct_ = arry_bct[(매수시간 <= arry_bct[:, 0]) & (arry_bct[:, 0] <= 매도시간)]
            arry_bct_[:, 1] += 1
            arry_bct[(매수시간 <= arry_bct[:, 0]) & (arry_bct[:, 0] <= 매도시간)] = arry_bct_
            self.ddict_bct[vars_turn][vars_key] = arry_bct

    def DivideData(self):
        if self.ddict_tsg:
            self.bctqs[0].put(('분리결과', self.ddict_tsg[0][0], self.ddict_bct[0][0]))
        self.tq.put('분리완료')

    def ConcatData(self, data):
        _, list_tsg, arry_bct = data
        if self.list_tsg is None:
            self.list_tsg = [[] for _ in range(14)]
            self.arry_bct = arry_bct
        else:
            self.arry_bct[:, 1] += arry_bct[:, 1]
        for i, list_ in enumerate(list_tsg):
            self.list_tsg[i] += list_
