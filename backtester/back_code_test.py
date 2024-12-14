from traceback import print_exc
from utility.setting import DICT_SET
# noinspection PyUnresolvedReferences
from utility.static import now, now_utc, timedelta_sec


# noinspection PyUnusedLocal
class BackCodeTest:
    def __init__(self, testQ, stg, var=None, ga=False):
        self.testQ = testQ
        self.vars  = {0: []}

        error = False
        if var is None:
            for i in range(200):
                self.vars[i] = 1
        else:
            try:
                exec(compile(var, '<string>', 'exec'), None, locals())
                max_len_var = 0
                vars_number = 0
                for i, v in enumerate(list(self.vars.values())):
                    len_var = 0
                    if ga:
                        len_var = len(v[0])
                    elif v[0][2] != 0:
                        len_var = (v[0][1] - v[0][0]) / v[0][2] + 1
                    if len_var > max_len_var:
                        max_len_var = len_var
                        vars_number = i
                if max_len_var > 20:
                    print('경고 :: 변수 범위의 최대개수는 20개입니다.')
                    print(f'경고 :: self.vars[{vars_number}]의 범위를 수정하십시오.')
                    error = True
            except:
                print_exc()
                error = True

        if not error:
            try:
                self.stg = compile(stg, '<string>', 'exec')
            except:
                print_exc()
                error = True

            if not error:
                self.dict_set    = DICT_SET
                self.bhogainfo   = {}
                self.shogainfo   = {}
                self.dict_signal = {}
                self.list_buy    = []
                self.list_sell   = []

                if var is None:
                    self.Test()
                else:
                    self.testQ.put('전략테스트완료')

    def Buy(self, *args):
        pass

    def Sell(self, *args):
        pass

    def Test(self):
        def 현재가N(pre):
            return 1

        def 시가N(pre):
            return 1

        def 고가N(pre):
            return 1

        def 저가N(pre):
            return 1

        def 등락율N(pre):
            return 1

        def 당일거래대금N(pre):
            return 1

        def 체결강도N(pre):
            return 1

        def 거래대금증감N(pre):
            return 1

        def 전일비N(pre):
            return 1

        def 회전율N(pre):
            return 1

        def 전일동시간비N(pre):
            return 1

        def 시가총액N(pre):
            return 1

        def 라운드피겨위5호가이내N(pre):
            return 1

        def 초당매수수량N(pre):
            return 1

        def 초당매도수량N(pre):
            return 1

        def 초당거래대금N(pre):
            return 1

        def 고저평균대비등락율N(pre):
            return 1

        def 매도총잔량N(pre):
            return 1

        def 매수총잔량N(pre):
            return 1

        def 매도호가5N(pre):
            return 1

        def 매도호가4N(pre):
            return 1

        def 매도호가3N(pre):
            return 1

        def 매도호가2N(pre):
            return 1

        def 매도호가1N(pre):
            return 1

        def 매수호가1N(pre):
            return 1

        def 매수호가2N(pre):
            return 1

        def 매수호가3N(pre):
            return 1

        def 매수호가4N(pre):
            return 1

        def 매수호가5N(pre):
            return 1

        def 매도잔량5N(pre):
            return 1

        def 매도잔량4N(pre):
            return 1

        def 매도잔량3N(pre):
            return 1

        def 매도잔량2N(pre):
            return 1

        def 매도잔량1N(pre):
            return 1

        def 매수잔량1N(pre):
            return 1

        def 매수잔량2N(pre):
            return 1

        def 매수잔량3N(pre):
            return 1

        def 매수잔량4N(pre):
            return 1

        def 매수잔량5N(pre):
            return 1

        def 매도수5호가잔량합N(pre):
            return 1

        def 이동평균(tick, pre=0):
            return 1

        def 당일거래대금각도(tick, pre=0):
            return 1

        def 전일비각도(tick, pre=0):
            return 1

        def 최고현재가(tick, pre=0):
            return 1

        def 최저현재가(tick, pre=0):
            return 1

        def 체결강도평균(tick, pre=0):
            return 1

        def 최고체결강도(tick, pre=0):
            return 1

        def 최저체결강도(tick, pre=0):
            return 1

        def 최고초당매수수량(tick, pre=0):
            return 1

        def 최고초당매도수량(tick, pre=0):
            return 1

        def 누적초당매수수량(tick, pre=0):
            return 1

        def 누적초당매도수량(tick, pre=0):
            return 1

        def 초당거래대금평균(tick, pre=0):
            return 1

        def 분봉시가N(pre):
            return 1

        def 분봉고가N(pre):
            return 1

        def 분봉저가N(pre):
            return 1

        def 분봉현재가N(pre):
            return 1

        def 분봉거래대금N(pre):
            return 1

        def 분봉이평5N(pre):
            return 1

        def 분봉이평10N(pre):
            return 1

        def 분봉이평20N(pre):
            return 1

        def 분봉이평60N(pre):
            return 1

        def 분봉이평120N(pre):
            return 1

        def 분봉이평240N(pre):
            return 1

        def 일봉시가N(pre):
            return 1

        def 일봉고가N(pre):
            return 1

        def 일봉저가N(pre):
            return 1

        def 일봉현재가N(pre):
            return 1

        def 일봉거래대금N(pre):
            return 1

        def 일봉이평5N(pre):
            return 1

        def 일봉이평10N(pre):
            return 1

        def 일봉이평20N(pre):
            return 1

        def 일봉이평60N(pre):
            return 1

        def 일봉이평120N(pre):
            return 1

        def 일봉이평240N(pre):
            return 1

        체결시간, 현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, 거래대금증감, 전일비, 회전율, 전일동시간비, 시가총액, \
            라운드피겨위5호가이내, 초당매수수량, 초당매도수량, VI해제시간, VI가격, VI호가단위, 초당거래대금, 고저평균대비등락율, 매도총잔량, 매수총잔량, \
            매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, 매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
            매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, 매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5, \
            매도수5호가잔량합, 종목코드, 틱수신시간, 종목명 = [
                20220721090001, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1,
                now(), 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 1, '005930', now(), '삼성전자']

        일봉최고종가5, 일봉최고고가5, 일봉최고종가10, 일봉최고고가10, 일봉최고종가20, 일봉최고고가20, 일봉최고종가60, \
            일봉최고고가60, 일봉최고종가120, 일봉최고고가120, 일봉최고종가240, 일봉최고고가240, 일봉최저종가5, 일봉최저저가5, \
            일봉최저종가10, 일봉최저저가10, 일봉최저종가20, 일봉최저저가20, 일봉최저종가60, 일봉최저저가60, 일봉최저종가120, \
            일봉최저저가120, 일봉최저종가240, 일봉최저저가240, 일봉종가합계4, 일봉종가합계9, 일봉종가합계19, 일봉종가합계59, \
            일봉종가합계119, 일봉종가합계239, 일봉최고거래대금 = [
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        분봉최고종가5, 분봉최고고가5, 분봉최고종가10, 분봉최고고가10, 분봉최고종가20, 분봉최고고가20, 분봉최고종가60, \
            분봉최고고가60, 분봉최고종가120, 분봉최고고가120, 분봉최고종가240, 분봉최고고가240, 분봉최저종가5, 분봉최저저가5, \
            분봉최저종가10, 분봉최저저가10, 분봉최저종가20, 분봉최저저가20, 분봉최저종가60, 분봉최저저가60, 분봉최저종가120, \
            분봉최저저가120, 분봉최저종가240, 분봉최저저가240, 분봉종가합계4, 분봉종가합계9, 분봉종가합계19, 분봉종가합계59, \
            분봉종가합계119, 분봉종가합계239, 분봉최고거래대금 = [
                1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        dict_bhogainfo = {
            1: {매도호가1: 매도잔량1},
            2: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2},
            3: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2, 매도호가3: 매도잔량3},
            4: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2, 매도호가3: 매도잔량3, 매도호가4: 매도잔량4},
            5: {매도호가1: 매도잔량1, 매도호가2: 매도잔량2, 매도호가3: 매도잔량3, 매도호가4: 매도잔량4, 매도호가5: 매도잔량5}
        }
        dict_shogainfo = {
            1: {매수호가1: 매수잔량1},
            2: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2},
            3: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3},
            4: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3, 매수호가4: 매수잔량4},
            5: {매수호가1: 매수잔량1, 매수호가2: 매수잔량2, 매수호가3: 매수잔량3, 매수호가4: 매수잔량4, 매수호가5: 매수잔량5}
        }

        self.bhogainfo = dict_bhogainfo[self.dict_set['주식매수시장가잔량범위']]
        self.shogainfo = dict_shogainfo[self.dict_set['주식매도시장가잔량범위']]

        시분초, VI아래5호가, 데이터길이, 호가단위, 포지션 = int(str(체결시간)[8:]), 1, 1800, 1, 'LONG'
        평균값계산틱수 = self.dict_set['주식장초평균값계산틱수'] if 시분초 < self.dict_set['주식장초전략종료시간'] else self.dict_set['주식장중평균값계산틱수']
        분봉시가, 분봉고가, 분봉저가, 분봉이평5, 분봉이평10, 분봉이평20, 분봉이평60, 분봉이평120, 분봉이평240, 분봉거래대금 = 1, 1, 1, 1., 1., 1., 1., 1., 1., 1
        일봉이평5, 일봉이평10, 일봉이평20, 일봉이평60, 일봉이평120, 일봉이평240 = 1., 1., 1., 1., 1., 1.
        수익률, 매입가, 보유수량, 매도수량, 분할매수횟수, 분할매도횟수, 매수시간, 보유시간, 최고수익률, 최저수익률 = 1, 1, 1, 1, 1, 0, now(), 0, 1, 0
        매수, 매도, BUY_LONG, SELL_LONG, SELL_SHORT, BUY_SHORT, 강제청산 = False, False, False, False, False, False, False

        exec(self.stg, None, locals())
        self.testQ.put('전략테스트완료')
