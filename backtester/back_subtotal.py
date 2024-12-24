import pandas as pd
from backtester.back_static import GetBackResult


class BackSubTotal:
    def __init__(self, gubun, tq, bstq, betting):
        self.gubun   = gubun
        self.tq      = tq
        self.bstq    = bstq
        self.betting = betting
        self.MainLoop()

    def MainLoop(self):
        while True:
            data = self.bstq.get()
            self.SendSubTotal(data)

    def SendSubTotal(self, data):
        _, columns, list_data, arry_bct = data[:4]
        df_tsg = pd.DataFrame(dict(zip(columns, list_data)))
        df_tsg.set_index('index', inplace=True)
        df_tsg.sort_index(inplace=True)
        arry_bct = arry_bct[arry_bct[:, 1] > 0]
        df_bct = pd.DataFrame(arry_bct[:, 1], columns=['보유종목수'], index=arry_bct[:, 0])

        if len(data) == 12:
            vsday, veday, tsday, tdaycnt, vdaycnt, index, vars_turn, vars_key = data[4:]
            if self.gubun:
                df_tsg = df_tsg[(df_tsg['매도시간'] < vsday * 1000000) | ((veday * 1000000 + 240000 < df_tsg['매도시간']) & (df_tsg['매도시간'] < tsday * 1000000))]
                df_bct = df_bct[(df_bct.index < vsday * 1000000) | ((veday * 1000000 + 240000 < df_bct.index) & (df_bct.index < tsday * 1000000))]
            else:
                df_tsg = df_tsg[(vsday * 1000000 <= df_tsg['매도시간']) & (df_tsg['매도시간'] <= veday * 1000000 + 240000)]
                df_bct = df_bct[(vsday * 1000000 <= df_bct.index) & (df_bct.index <= veday * 1000000 + 240000)]
            _, _, result = GetBackResult(df_tsg, df_bct, self.betting, tdaycnt if self.gubun else vdaycnt)
            self.tq.put(('TRAIN' if self.gubun else 'VALID', index, result, vars_turn, vars_key))
        elif len(data) == 11:
            vsday, veday, tdaycnt, vdaycnt, index, vars_turn, vars_key = data[4:]
            if self.gubun:
                df_tsg = df_tsg[(df_tsg['매도시간'] < vsday * 1000000) | (veday * 1000000 + 240000 < df_tsg['매도시간'])]
                df_bct = df_bct[(vsday * 1000000 < df_bct.index) | (df_bct.index > veday * 1000000 + 240000)]
            else:
                df_tsg = df_tsg[(vsday * 1000000 <= df_tsg['매도시간']) & (df_tsg['매도시간'] <= veday * 1000000 + 240000)]
                df_bct = df_bct[(vsday * 1000000 <= df_bct.index) & (df_bct.index <= veday * 1000000 + 240000)]
            _, _, result = GetBackResult(df_tsg, df_bct, self.betting, tdaycnt if self.gubun else vdaycnt)
            self.tq.put(('TRAIN' if self.gubun else 'VALID', index, result, vars_turn, vars_key))
        else:
            daycnt, vars_turn, vars_key = data[4:]
            _, _, result = GetBackResult(df_tsg, df_bct, self.betting, daycnt)
            self.tq.put(('ALL', 0, result, vars_turn, vars_key))
