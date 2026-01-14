"""
ICOS를 위한 동기식 백테스트 실행기.

Synchronous Backtest Runner for ICOS (Iterative Condition Optimization System).

기존 멀티프로세스 백테스팅 시스템의 핵심 로직을 동기적으로 실행하여
ICOS 반복 루프에서 사용할 수 있게 합니다.

작성일: 2026-01-14
브랜치: feature/iterative-condition-optimizer
"""

import math
import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from traceback import print_exc

from utility.setting import (
    DB_STOCK_BACK_TICK, DB_STOCK_BACK_MIN,
    DB_COIN_BACK_TICK, DB_COIN_BACK_MIN,
    DICT_SET, DB_STRATEGY,
)
from backtester.back_static import (
    GetMoneytopQuery, GetBuyStg, GetSellStg, GetTradeInfo, AddAvgData,
)
from backtester.analysis.results import GetResultDataframe, GetBackResult, AddMdd
from utility.static import strp_time, timedelta_sec, GetKiwoomPgSgSp, GetUpbitPgSgSp


class SyncBacktestRunner:
    """동기식 백테스트 실행기.

    ICOS 반복 루프에서 사용하기 위한 동기적 백테스트 실행기입니다.
    기존 백엔진의 핵심 로직을 단일 프로세스에서 실행합니다.

    Attributes:
        ui_gubun: UI 구분 ('S': 주식, 'C': 코인)
        timeframe: 타임프레임 ('tick' 또는 'min')
        dict_cn: 종목코드-종목명 딕셔너리
        verbose: 상세 로그 출력 여부

    Example:
        >>> runner = SyncBacktestRunner(ui_gubun='S', timeframe='tick')
        >>> result = runner.run(buystg, sellstg, params)
        >>> df_tsg = result['df_tsg']
        >>> metrics = result['metrics']
    """

    def __init__(
        self,
        ui_gubun: str = 'S',
        timeframe: str = 'tick',
        dict_cn: Optional[Dict[str, str]] = None,
        verbose: bool = False,
    ):
        """초기화.

        Args:
            ui_gubun: UI 구분 ('S': 주식, 'C': 코인)
            timeframe: 타임프레임 ('tick' 또는 'min')
            dict_cn: 종목코드-종목명 딕셔너리
            verbose: 상세 로그 출력 여부
        """
        self.ui_gubun = ui_gubun
        self.timeframe = timeframe
        self.dict_cn = dict_cn or {}
        self.verbose = verbose
        self.dict_set = DICT_SET.copy()

        # STOM 패턴: 한국어 상태 변수
        self.실행시작시간: Optional[datetime] = None
        self.실행종료시간: Optional[datetime] = None

        # 백엔진 상태 변수
        self.list_tsg: List = []
        self.arry_bct: Optional[np.ndarray] = None
        self.code = ''
        self.name = ''
        self.index = 0
        self.indexn = 0
        self.indexb = 0
        self.tick_count = 0
        self.sell_count = 0
        self.arry_data: Optional[np.ndarray] = None
        self.trade_info: Dict = {}
        self.day_info: Dict = {}
        self.dict_cond_indexn: Dict = {}
        self.sell_cond = 0

        # 매수/매도 호가 정보
        self.bhogainfo = []
        self.shogainfo = []

    def _log(self, message: str) -> None:
        """로그 출력."""
        if self.verbose:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] [SyncBacktest] {message}")

    def _get_db_path(self) -> str:
        """백테스트 데이터베이스 경로 반환."""
        is_tick = self.timeframe == 'tick'
        if self.ui_gubun == 'S':
            return DB_STOCK_BACK_TICK if is_tick else DB_STOCK_BACK_MIN
        else:
            return DB_COIN_BACK_TICK if is_tick else DB_COIN_BACK_MIN

    def _load_period_data(
        self,
        code_list: List[str],
        startday: int,
        endday: int,
        starttime: int,
        endtime: int,
        avg_list: List[int],
    ) -> Dict[str, np.ndarray]:
        """기간 데이터 로드.

        Args:
            code_list: 종목코드 리스트
            startday: 시작일 (YYYYMMDD)
            endday: 종료일 (YYYYMMDD)
            starttime: 시작시간 (HHMMSS)
            endtime: 종료시간 (HHMMSS)
            avg_list: 평균값 계산 틱수 리스트

        Returns:
            종목코드별 데이터 배열 딕셔너리
        """
        db = self._get_db_path()
        self._log(f"데이터 로드: {db}")

        dict_arry = {}
        is_tick = self.timeframe == 'tick'

        con = sqlite3.connect(db)

        for code in code_list:
            try:
                # 기본 쿼리: 날짜 및 시간 범위 필터링
                query = f"""
                    SELECT * FROM '{code}'
                    WHERE `index` >= {startday * 1000000 + starttime}
                    AND `index` <= {endday * 1000000 + endtime}
                    ORDER BY `index`
                """
                df = pd.read_sql(query, con)

                if len(df) > 0:
                    # 평균 데이터 추가
                    df = AddAvgData(df, 3, is_tick, avg_list)
                    dict_arry[code] = np.array(df)
                    self._log(f"  {code}: {len(df)}건 로드")
            except Exception as e:
                self._log(f"  {code}: 로드 실패 - {e}")
                continue

        con.close()

        total_count = sum(len(arr) for arr in dict_arry.values())
        self._log(f"데이터 로드 완료: {len(dict_arry)}종목, {total_count}건")

        return dict_arry

    def _load_strategy_from_db(
        self,
        buystg_name: str,
        sellstg_name: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """데이터베이스에서 전략 로드.

        Args:
            buystg_name: 매수 전략 이름
            sellstg_name: 매도 전략 이름

        Returns:
            (매수 조건식, 매도 조건식) 튜플
        """
        gubun = 'stock' if self.ui_gubun == 'S' else 'coin'

        con = sqlite3.connect(DB_STRATEGY)
        dfb = pd.read_sql(f'SELECT * FROM {gubun}buy', con).set_index('index')
        dfs = pd.read_sql(f'SELECT * FROM {gubun}sell', con).set_index('index')
        con.close()

        buystg = dfb['전략코드'].get(buystg_name)
        sellstg = dfs['전략코드'].get(sellstg_name)

        return buystg, sellstg

    def run(
        self,
        buystg: str,
        sellstg: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """백테스트 실행.

        Args:
            buystg: 매수 조건식 (Python 코드 문자열)
            sellstg: 매도 조건식 (Python 코드 문자열)
            params: 백테스트 파라미터
                - betting: 배팅금액
                - startday: 시작일 (YYYYMMDD)
                - endday: 종료일 (YYYYMMDD)
                - starttime: 시작시간 (HHMMSS)
                - endtime: 종료시간 (HHMMSS)
                - avgtime: 평균값 계산 틱수
                - code_list: 종목코드 리스트 (선택)
                - dict_cn: 종목코드-종목명 딕셔너리 (선택)

        Returns:
            백테스트 결과 딕셔너리:
                - df_tsg: 거래 상세 DataFrame
                - df_bct: 보유종목수 DataFrame
                - metrics: 성과 지표 딕셔너리
                - execution_time: 실행 시간 (초)
        """
        self.실행시작시간 = datetime.now()

        # 파라미터 추출
        betting = params.get('betting', 1000000)
        startday = params.get('startday')
        endday = params.get('endday')
        starttime = params.get('starttime', 90000)
        endtime = params.get('endtime', 153000)
        avgtime = params.get('avgtime', 9)
        code_list = params.get('code_list', [])
        avg_list = params.get('avg_list', [9, 60, 300, 600, 1200])

        # dict_cn 업데이트
        if 'dict_cn' in params:
            self.dict_cn = params['dict_cn']

        self._log(f"백테스트 시작: {startday}~{endday}, 배팅={betting:,}")

        # 전략 컴파일
        buystg_compiled, indistg = GetBuyStg(buystg, 0)
        sellstg_compiled, dict_sconds = GetSellStg(sellstg, 0)

        if buystg_compiled is None or sellstg_compiled is None:
            self._log("전략 컴파일 실패")
            return self._empty_result()

        # 1. 기간 데이터 로드
        if not code_list:
            self._log("종목코드 리스트가 비어있음 - 빈 결과 반환")
            return self._empty_result()

        dict_arry = self._load_period_data(
            code_list, startday, endday, starttime, endtime, avg_list
        )

        if not dict_arry:
            self._log("데이터 없음 - 빈 결과 반환")
            return self._empty_result()

        # 2. 전체 틱 수 계산 및 보유종목수 배열 초기화
        total_ticks = sum(len(arr) for arr in dict_arry.values())
        self.arry_bct = np.zeros((total_ticks, 3), dtype='float64')

        # 3. 백엔진 실행 (동기식)
        self._log("백엔진 실행 중...")
        self.list_tsg = []

        self._run_backengine_sync(
            buystg_compiled=buystg_compiled,
            sellstg_compiled=sellstg_compiled,
            dict_sconds=dict_sconds,
            betting=betting,
            avgtime=avgtime,
            dict_arry=dict_arry,
            code_list=list(dict_arry.keys()),
        )

        if not self.list_tsg:
            self._log("거래 없음 - 빈 결과 반환")
            return self._empty_result()

        self._log(f"백엔진 완료: {len(self.list_tsg)}건 거래")

        # 4. 결과 처리
        df_tsg, df_bct = GetResultDataframe(self.ui_gubun, self.list_tsg, self.arry_bct)

        # 일자 수 계산
        all_indices = []
        for arr in dict_arry.values():
            all_indices.extend(arr[:, 0])
        day_count = len(set(int(str(int(idx))[:8]) for idx in all_indices))

        # 5. 메트릭 계산
        arry_tsg = np.array(
            df_tsg[['보유시간', '매도시간', '수익률', '수익금', '수익금합계']],
            dtype='float64'
        )
        arry_bct_sorted = np.sort(self.arry_bct, axis=0)[::-1]
        result = GetBackResult(arry_tsg, arry_bct_sorted, betting, self.ui_gubun, day_count)
        result = AddMdd(arry_tsg, result)

        tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi, mdd, mdd_ = result

        metrics = {
            'total_profit': float(tsg),
            'win_rate': float(wr),
            'trade_count': int(tc),
            'avg_trade_count': float(atc),
            'profit_count': int(pc),
            'loss_count': int(mc),
            'profit_factor': float(pc / max(mc, 1)),
            'max_drawdown': float(mdd),
            'avg_profit_rate': float(app),
            'total_profit_rate': float(tpp),
            'avg_hold_time': float(ah),
            'max_hold_count': int(mhct),
            'required_seed': float(seed),
            'cagr': float(cagr),
            'tpi': float(tpi),
            'day_count': int(day_count),
        }

        self.실행종료시간 = datetime.now()
        execution_time = (self.실행종료시간 - self.실행시작시간).total_seconds()

        self._log(f"백테스트 완료: 수익금={tsg:,}, 승률={wr:.2f}%, 실행시간={execution_time:.1f}초")

        return {
            'df_tsg': df_tsg,
            'df_bct': df_bct,
            'metrics': metrics,
            'execution_time': execution_time,
        }

    def _run_backengine_sync(
        self,
        buystg_compiled,
        sellstg_compiled,
        dict_sconds: Dict,
        betting: float,
        avgtime: int,
        dict_arry: Dict[str, np.ndarray],
        code_list: List[str],
    ) -> None:
        """백엔진 핵심 로직 동기 실행.

        기존 backengine의 BackTest(), Strategy() 메서드 로직을
        단일 프로세스에서 실행합니다.

        Args:
            buystg_compiled: 컴파일된 매수 조건식
            sellstg_compiled: 컴파일된 매도 조건식
            dict_sconds: 매도 조건 딕셔너리
            betting: 배팅금액
            avgtime: 평균값 계산 틱수
            dict_arry: 종목코드별 데이터 배열
            code_list: 종목코드 리스트
        """
        self.buystg = buystg_compiled
        self.sellstg = sellstg_compiled
        self.dict_sconds = dict_sconds
        self.betting = betting
        self.avgtime = avgtime

        bct_index = 0  # arry_bct 인덱스

        for code in code_list:
            if code not in dict_arry:
                continue

            self.code = code
            self.name = self.dict_cn.get(code, code)
            self.arry_data = dict_arry[code]

            self._init_trade_info()

            last = len(self.arry_data) - 1
            if last <= 0:
                continue

            for i, index in enumerate(self.arry_data[:, 0]):
                self.index = int(index)
                self.indexn = i
                self.tick_count += 1

                # arry_bct에 인덱스 저장
                if bct_index < len(self.arry_bct):
                    self.arry_bct[bct_index, 0] = self.index
                    bct_index += 1

                next_day_change = (
                    i == last or
                    str(index)[:8] != str(self.arry_data[i + 1, 0])[:8]
                )

                if not next_day_change:
                    try:
                        self._strategy()
                    except Exception:
                        print_exc()
                        return
                else:
                    self._last_sell()
                    self._init_trade_info()

    def _init_trade_info(self) -> None:
        """거래 정보 초기화."""
        self.dict_cond_indexn = {}
        self.tick_count = 0
        v = GetTradeInfo(1)
        self.trade_info = {0: {0: v}}
        self.day_info = {0: {0: GetTradeInfo(3) if self.ui_gubun == 'S' else GetTradeInfo(3)}}

    def _strategy(self) -> None:
        """전략 실행.

        기존 BackEngineKiwoomTick.Strategy() 메서드의 단순화된 버전.
        opti_turn=2 (백테스트) 모드로 동작.
        """
        def now():
            return strp_time('%Y%m%d%H%M%S', str(self.index))

        def Parameter_Previous(aindex, pre):
            if pre < 데이터길이:
                pindex = (self.indexn - pre) if pre != -1 else self.indexb
                return self.arry_data[pindex, aindex]
            return 0

        def 현재가N(pre):
            return Parameter_Previous(1, pre)

        def 시가N(pre):
            return Parameter_Previous(2, pre)

        def 고가N(pre):
            return Parameter_Previous(3, pre)

        def 저가N(pre):
            return Parameter_Previous(4, pre)

        def 등락율N(pre):
            return Parameter_Previous(5, pre)

        def 당일거래대금N(pre):
            return Parameter_Previous(6, pre)

        def 체결강도N(pre):
            return Parameter_Previous(7, pre)

        def 이동평균(tick, pre=0):
            if tick + pre <= 데이터길이:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1 else self.indexb + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1 else self.indexb + 1
                return round(self.arry_data[sindex:eindex, 1].mean(), 3)
            return 0

        def 최고현재가(tick, pre=0):
            if tick + pre <= 데이터길이:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1 else self.indexb + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1 else self.indexb + 1
                return self.arry_data[sindex:eindex, 1].max()
            return 0

        def 최저현재가(tick, pre=0):
            if tick + pre <= 데이터길이:
                sindex = (self.indexn + 1 - pre - tick) if pre != -1 else self.indexb + 1 - tick
                eindex = (self.indexn + 1 - pre) if pre != -1 else self.indexb + 1
                return self.arry_data[sindex:eindex, 1].min()
            return 0

        def 등락율각도(tick, pre=0):
            if tick + pre <= 데이터길이:
                sindex = (self.indexn - pre - tick + 1) if pre != -1 else self.indexb - tick + 1
                eindex = (self.indexn - pre) if pre != -1 else self.indexb
                dmp_gap = self.arry_data[eindex, 5] - self.arry_data[sindex, 5]
                return round(math.atan2(dmp_gap * 5, tick) / (2 * math.pi) * 360, 2)
            return 0

        def 당일거래대금각도(tick, pre=0):
            if tick + pre <= 데이터길이:
                sindex = (self.indexn - pre - tick + 1) if pre != -1 else self.indexb - tick + 1
                eindex = (self.indexn - pre) if pre != -1 else self.indexb
                dmp_gap = self.arry_data[eindex, 6] - self.arry_data[sindex, 6]
                return round(math.atan2(dmp_gap * 0.01, tick) / (2 * math.pi) * 360, 2)
            return 0

        # 데이터 추출
        종목명, 종목코드, 데이터길이, 시분초 = self.name, self.code, self.tick_count, int(str(self.index)[8:])

        # 주식/코인별 데이터 컬럼 매핑
        if self.ui_gubun == 'S':
            현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도 = self.arry_data[self.indexn, 1:8]
            관심종목 = self.arry_data[self.indexn, 44] if self.arry_data.shape[1] > 44 else 1
            매도호가1 = self.arry_data[self.indexn, 27] if self.arry_data.shape[1] > 27 else 현재가 * 1.001
            매수호가1 = self.arry_data[self.indexn, 28] if self.arry_data.shape[1] > 28 else 현재가 * 0.999
            매도잔량1 = self.arry_data[self.indexn, 37] if self.arry_data.shape[1] > 37 else 1000
            매수잔량1 = self.arry_data[self.indexn, 38] if self.arry_data.shape[1] > 38 else 1000
        else:
            현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도 = self.arry_data[self.indexn, 1:8]
            관심종목 = self.arry_data[self.indexn, 35] if self.arry_data.shape[1] > 35 else 1
            매도호가1 = self.arry_data[self.indexn, 18] if self.arry_data.shape[1] > 18 else 현재가 * 1.001
            매수호가1 = self.arry_data[self.indexn, 19] if self.arry_data.shape[1] > 19 else 현재가 * 0.999
            매도잔량1 = self.arry_data[self.indexn, 28] if self.arry_data.shape[1] > 28 else 1000
            매수잔량1 = self.arry_data[self.indexn, 29] if self.arry_data.shape[1] > 29 else 1000

        호가단위 = abs(매도호가1 - 매수호가1) if 매도호가1 != 매수호가1 else 1
        self.bhogainfo = [(매도호가1, 매도잔량1)]
        self.shogainfo = [(매수호가1, 매수잔량1)]

        # 데이터길이 체크
        if self.tick_count < self.avgtime:
            return

        vturn, vkey = 0, 0

        보유중 = self.trade_info[vturn][vkey].get('보유중', 0)
        매수가 = self.trade_info[vturn][vkey].get('매수가', 0)
        보유수량 = self.trade_info[vturn][vkey].get('보유수량', 0)
        최고수익률 = self.trade_info[vturn][vkey].get('최고수익률', 0)
        최저수익률 = self.trade_info[vturn][vkey].get('최저수익률', 0)
        매수틱번호 = self.trade_info[vturn][vkey].get('매수틱번호', 0)
        매수시간 = self.trade_info[vturn][vkey].get('매수시간', now())

        # 수익 계산
        수익금, 수익률, 보유시간 = 0, 0, 0
        if 보유중:
            self.indexb = 매수틱번호
            if self.ui_gubun == 'S':
                _, 수익금, 수익률 = GetKiwoomPgSgSp(보유수량 * 매수가, 보유수량 * 현재가)
            else:
                _, 수익금, 수익률 = GetUpbitPgSgSp(보유수량 * 매수가, 보유수량 * 현재가)

            if 수익률 > 최고수익률:
                self.trade_info[vturn][vkey]['최고수익률'] = 최고수익률 = 수익률
            elif 수익률 < 최저수익률:
                self.trade_info[vturn][vkey]['최저수익률'] = 최저수익률 = 수익률

            보유시간 = int((now() - 매수시간).total_seconds())

        # 매수/매도 판단
        매수, 매도 = True, False

        if not 보유중:
            # 매수 조건 실행
            if 관심종목:
                try:
                    exec(self.buystg)
                except:
                    pass
        else:
            # 매도 조건 실행
            try:
                exec(self.sellstg)
            except:
                pass

    def Buy(self, vturn=0, vkey=0):
        """매수 실행."""
        현재가 = self.arry_data[self.indexn, 1]
        주문수량 = int(self.betting / 현재가)

        if 주문수량 > 0:
            매수금액 = 현재가 * 주문수량
            self.trade_info[vturn][vkey]['보유중'] = 1
            self.trade_info[vturn][vkey]['매수가'] = 현재가
            self.trade_info[vturn][vkey]['보유수량'] = 주문수량
            self.trade_info[vturn][vkey]['매수틱번호'] = self.indexn
            self.trade_info[vturn][vkey]['매수시간'] = strp_time('%Y%m%d%H%M%S', str(self.index))
            self.trade_info[vturn][vkey]['추가매수시간'] = [f"{self.index};{현재가}"]
            self.trade_info[vturn][vkey]['매수분할횟수'] = 1

    def Sell(self, vturn=0, vkey=0, sell_cond=100):
        """매도 실행."""
        self.sell_cond = sell_cond
        self._calculation_eyun(vturn, vkey)

    def _calculation_eyun(self, vturn: int, vkey: int) -> None:
        """수익 계산 및 거래 기록.

        Args:
            vturn: 변수 턴
            vkey: 변수 키
        """
        bp = self.trade_info[vturn][vkey].get('매수가', 0)
        sp = self.arry_data[self.indexn, 1]  # 현재가 = 매도가
        oc = self.trade_info[vturn][vkey].get('보유수량', 0)
        bc = oc
        bi = self.trade_info[vturn][vkey].get('매수틱번호', 0)
        bdt = self.trade_info[vturn][vkey].get('매수시간', datetime.now())
        abt = self.trade_info[vturn][vkey].get('추가매수시간', [])

        bt = int(self.arry_data[bi, 0])
        st = self.index
        bg = oc * bp

        if self.ui_gubun == 'S':
            pg, sg, pp = GetKiwoomPgSgSp(bg, oc * sp)
        else:
            pg, sg, pp = GetUpbitPgSgSp(bg, oc * sp)

        sgtg = 0
        ht = int((strp_time('%Y%m%d%H%M%S', str(self.index)) - bdt).total_seconds())
        sc = self.dict_sconds.get(self.sell_cond, f'조건{self.sell_cond}')
        abt_str = '^'.join(abt) if abt else ''
        bcx = True

        # 거래 기록 추가 (기본 17개 필드)
        data = (
            '백테결과', self.name, sgtg, bt, st, ht, bp, sp, bg, pg, pp, sg, sc, abt_str, bcx, vturn, vkey
        )
        self.list_tsg.append(data)
        self.sell_count += 1

        # 거래 정보 초기화
        self.trade_info[vturn][vkey] = GetTradeInfo(1)

    def _last_sell(self) -> None:
        """일 마감 시 보유 종목 청산."""
        vturn, vkey = 0, 0
        if self.trade_info[vturn][vkey].get('보유중', 0):
            self.Sell(vturn, vkey, 200)  # 200: 장마감 청산

    def _empty_result(self) -> Dict[str, Any]:
        """빈 결과 반환."""
        self.실행종료시간 = datetime.now()
        execution_time = 0.0
        if self.실행시작시간:
            execution_time = (self.실행종료시간 - self.실행시작시간).total_seconds()

        return {
            'df_tsg': pd.DataFrame(),
            'df_bct': pd.DataFrame(),
            'metrics': {
                'total_profit': 0.0,
                'win_rate': 0.0,
                'trade_count': 0,
                'avg_trade_count': 0.0,
                'profit_count': 0,
                'loss_count': 0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'avg_profit_rate': 0.0,
                'total_profit_rate': 0.0,
                'avg_hold_time': 0.0,
                'max_hold_count': 0,
                'required_seed': 0.0,
                'cagr': 0.0,
                'tpi': 0.0,
                'day_count': 0,
            },
            'execution_time': execution_time,
        }

    def run_with_strategy_names(
        self,
        buystg_name: str,
        sellstg_name: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """전략 이름으로 백테스트 실행.

        데이터베이스에서 전략을 로드하여 백테스트를 실행합니다.

        Args:
            buystg_name: 매수 전략 이름
            sellstg_name: 매도 전략 이름
            params: 백테스트 파라미터

        Returns:
            백테스트 결과 딕셔너리
        """
        buystg, sellstg = self._load_strategy_from_db(buystg_name, sellstg_name)

        if buystg is None or sellstg is None:
            self._log(f"전략 로드 실패: {buystg_name}, {sellstg_name}")
            return self._empty_result()

        return self.run(buystg, sellstg, params)
