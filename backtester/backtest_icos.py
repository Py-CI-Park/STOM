"""
ICOS 전용 백테스트 클래스 - 기존 BackTest 엔진 완전 통합.

Iterative Condition Optimization System (ICOS) BackTest Class.

이 모듈은 기존 BackTest 클래스의 백테스트 엔진(back_eques 멀티프로세스)을
완전히 재활용하면서 반복적 조건식 최적화를 수행합니다.

주요 특징:
1. 기존 BackTest 클래스와 동일한 backQ 통신 방식 사용
2. back_eques를 통한 멀티코어 분산 처리
3. 반복마다 조건식 분석 및 개선
4. 수렴 시 최종 백테스트 자동 실행 (optimiz.py 패턴)

작성일: 2026-01-19
브랜치: feature/icos-complete-implementation
"""

import sys
import time
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
from multiprocessing import Process, Queue
from typing import Optional, Dict, Any, Tuple, List

from backtester.back_static import (
    GetMoneytopQuery, GetBackResult, GetResultDataframe, AddMdd, PltShow
)
from utility.static import now, strf_time
from utility.setting import (
    DB_STRATEGY, DB_BACKTEST, ui_num, columns_vj, DICT_SET,
    DB_STOCK_BACK_TICK, DB_COIN_BACK_TICK, DB_STOCK_BACK_MIN, DB_COIN_BACK_MIN
)

# ICOS 분석 모듈
from backtester.iterative_optimizer.config import IterativeConfig
from backtester.iterative_optimizer.analyzer import ResultAnalyzer, AnalysisResult
from backtester.iterative_optimizer.filter_generator import FilterGenerator
from backtester.iterative_optimizer.condition_builder import ConditionBuilder
from backtester.iterative_optimizer.convergence import ConvergenceChecker
from backtester.iterative_optimizer.storage import IterationStorage


class ICOSTotal:
    """ICOS 전용 집계 프로세스.

    기존 Total 클래스를 확장하여 ICOS 반복에 결과를 전달합니다.
    반복 모드에서는 Report() 후 프로세스 종료 없이 결과만 전달합니다.

    Attributes:
        wq: windowQ (UI 로그)
        sq: soundQ (알림)
        tq: totalQ (집계 수신)
        mq: 결과 큐 (부모 프로세스로 결과 전달)
        icos_mode: ICOS 반복 모드 여부
    """

    def __init__(
        self,
        wq,
        sq,
        tq,
        teleQ,
        mq,
        lq,
        bstq_list,
        backname: str,
        ui_gubun: str,
        gubun: str,
        icos_mode: bool = True,
        iteration_info: Optional[Dict] = None,
    ):
        """ICOSTotal 초기화.

        Args:
            wq: windowQ
            sq: soundQ
            tq: totalQ
            teleQ: 텔레그램 큐
            mq: 결과 큐 (ICOS 반복용)
            lq: liveQ
            bstq_list: back_sques
            backname: 백테스트 이름
            ui_gubun: 'S', 'C', 'CF'
            gubun: 'stock' 또는 'coin'
            icos_mode: ICOS 반복 모드 여부
            iteration_info: 반복 정보 {'current': n, 'max': m}
        """
        self.wq = wq
        self.sq = sq
        self.tq = tq
        self.mq = mq
        self.lq = lq
        self.teleQ = teleQ
        self.bstq_list = bstq_list
        self.backname = backname
        self.ui_gubun = ui_gubun
        self.gubun = gubun
        self.dict_set = DICT_SET
        gubun_text = f'{self.gubun}_future' if self.ui_gubun == 'CF' else self.gubun
        self.savename = f'{gubun_text}_icos'

        self.icos_mode = icos_mode
        self.iteration_info = iteration_info or {'current': 0, 'max': 5}

        self.back_count = None
        self.buystg_name = None
        self.sellstg_name = None
        self.buystg = None
        self.sellstg = None
        self.dict_cn = None
        self.blacklist = None
        self.day_count = None

        self.betting = None
        self.startday = None
        self.endday = None
        self.starttime = None
        self.endtime = None
        self.avgtime = None
        self.schedul = None

        self.df_tsg = None
        self.df_bct = None
        self.df_kp = None
        self.df_kd = None
        self.back_club = None

        self.MainLoop()

    def MainLoop(self):
        """메인 집계 루프.

        기존 Total.MainLoop()와 동일하되,
        ICOS 모드에서는 결과를 mq로 전달하고 계속 대기합니다.
        """
        bc = 0
        sc = 0
        start = now()

        while True:
            data = self.tq.get()

            if data[0] == '백테완료':
                bc += 1
                self.wq.put((
                    ui_num[f'{self.ui_gubun}백테바'],
                    bc, self.back_count, start
                ))

                if bc == self.back_count:
                    bc = 0
                    for q in self.bstq_list[:5]:
                        q.put(('백테완료', '분리집계'))

            elif data == '집계완료':
                sc += 1
                if sc == 5:
                    sc = 0
                    for q in self.bstq_list[:5]:
                        q.put('결과분리')

            elif data == '분리완료':
                sc += 1
                if sc == 5:
                    sc = 0
                    self.bstq_list[0].put('결과전송')

            elif data[0] == '백테결과':
                _, list_tsg, arry_bct = data
                self._process_result(list_tsg, arry_bct)

            elif data[0] == '백테정보':
                self.betting = data[1]
                self.avgtime = data[2]
                self.startday = data[3]
                self.endday = data[4]
                self.starttime = data[5]
                self.endtime = data[6]
                self.buystg_name = data[7]
                self.sellstg_name = data[8]
                self.buystg = data[9]
                self.sellstg = data[10]
                self.dict_cn = data[11]
                self.back_count = data[12]
                self.day_count = data[13]
                self.blacklist = data[14]
                self.schedul = data[15]
                self.df_kp = data[16]
                self.df_kd = data[17]
                self.back_club = data[18] if len(data) > 18 else False

            elif data == '백테중지':
                self.mq.put({'status': 'stopped'})
                break

            elif data == 'ICOS종료':
                # ICOS 완료 후 정상 종료
                break

        time.sleep(1)
        sys.exit()

    def _process_result(self, list_tsg, arry_bct):
        """백테스트 결과 처리.

        ICOS 모드: 결과를 분석용 데이터로 변환하여 mq에 전달
        최종 모드: 기존 Report()와 동일하게 처리
        """
        if not list_tsg:
            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                '매수전략을 만족하는 경우가 없어 결과를 표시할 수 없습니다.'
            ))
            self.mq.put({
                'status': 'no_trades',
                'df_tsg': None,
                'metrics': None,
            })
            return

        # 결과 DataFrame 생성
        self.df_tsg, self.df_bct = GetResultDataframe(
            self.ui_gubun, list_tsg, arry_bct
        )

        # 기본 메트릭 계산
        _df_tsg = self.df_tsg[
            ['보유시간', '매도시간', '수익률', '수익금', '수익금합계']
        ].copy()
        arry_tsg = np.array(_df_tsg, dtype='float64')
        arry_bct_sorted = np.sort(arry_bct, axis=0)[::-1]
        result = GetBackResult(
            arry_tsg, arry_bct_sorted, self.betting, self.ui_gubun, self.day_count
        )
        result = AddMdd(arry_tsg, result)
        tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi, mdd, mdd_ = result

        metrics = {
            'trade_count': tc,
            'avg_trade_count': atc,
            'profit_count': pc,
            'loss_count': mc,
            'win_rate': wr,
            'avg_hold_time': ah,
            'avg_profit_rate': app,
            'total_profit_rate': tpp,
            'total_profit': tsg,
            'max_hold_count': mhct,
            'seed': seed,
            'cagr': cagr,
            'tpi': tpi,
            'mdd': mdd,
            'mdd_': mdd_,
        }

        # 반복 정보 로그
        iter_text = (
            f"반복 {self.iteration_info['current'] + 1}/{self.iteration_info['max']}"
        )
        self.wq.put((
            ui_num[f'{self.ui_gubun}백테스트'],
            f'<font color=#45cdf7>[ICOS] {iter_text} 완료 - '
            f'거래 {tc}회, 승률 {wr:.1f}%, 수익금 {tsg:,}원</font>'
        ))

        # 결과 전달
        self.mq.put({
            'status': 'completed',
            'df_tsg': self.df_tsg,
            'df_bct': self.df_bct,
            'metrics': metrics,
            'arry_bct': arry_bct,
            'arry_tsg': arry_tsg,
        })


class ICOSBackTest:
    """ICOS 전용 백테스트 클래스.

    기존 BackTest 클래스를 모델로 하여 반복적 조건식 최적화를 수행합니다.
    back_eques를 통한 멀티프로세스 백테스트 엔진을 재사용합니다.

    핵심 차이점:
    - Start() 대신 ICOSLoop() 사용
    - 반복마다 조건식 분석 및 개선
    - 수렴 시 최종 백테스트 자동 실행

    Attributes:
        wq: windowQ
        bq: backQ
        beq_list: back_eques (백엔진 큐)
        bstq_list: back_sques (집계 큐)
        icos_config: ICOS 설정 딕셔너리
    """

    def __init__(
        self,
        wq,
        bq,
        sq,
        tq,
        lq,
        teleQ,
        beq_list,
        bstq_list,
        backname: str,
        ui_gubun: str,
        icos_config: Dict[str, Any],
    ):
        """ICOSBackTest 초기화.

        Args:
            wq: windowQ
            bq: backQ
            sq: soundQ
            tq: totalQ
            lq: liveQ
            teleQ: 텔레그램 큐
            beq_list: back_eques
            bstq_list: back_sques
            backname: 백테스트 이름 ('ICOS')
            ui_gubun: 'S', 'C', 'CF'
            icos_config: ICOS 설정
        """
        self.wq = wq
        self.bq = bq
        self.sq = sq
        self.tq = tq
        self.lq = lq
        self.teleQ = teleQ
        self.beq_list = beq_list
        self.bstq_list = bstq_list
        self.backname = backname
        self.ui_gubun = ui_gubun
        self.dict_set = DICT_SET
        self.gubun = 'stock' if self.ui_gubun == 'S' else 'coin'

        # ICOS 설정
        self.icos_config = icos_config
        self.max_iterations = icos_config.get('max_iterations', 5)
        self.convergence_threshold = icos_config.get('convergence_threshold', 5) / 100

        # ICOS 컴포넌트 초기화
        self.config = IterativeConfig.from_dict(icos_config)
        self.analyzer = ResultAnalyzer(self.config)
        self.filter_gen = FilterGenerator(self.config)
        self.condition_builder = ConditionBuilder(self.config)
        self.convergence_checker = ConvergenceChecker(self.config)
        self.storage = IterationStorage(self.config)

        # 상태 변수
        self.current_iteration = 0
        self.iteration_results = []
        self.converged = False
        self.initial_buystg = None
        self.initial_sellstg = None
        self.current_buystg = None
        self.current_sellstg = None

        # 백테스트 파라미터 (backQ에서 수신)
        self.betting = None
        self.avgtime = None
        self.startday = None
        self.endday = None
        self.starttime = None
        self.endtime = None
        self.dict_cn = None
        self.back_count = None
        self.bl = None
        self.df_kp = None
        self.df_kd = None

        # 결과 큐 (ICOSTotal과 통신)
        self.result_queue = Queue()

        # 메인 루프 시작
        self.ICOSLoop()

    def ICOSLoop(self):
        """ICOS 메인 반복 루프.

        1. backQ에서 초기 파라미터 수신
        2. 반복: 백테스트 → 분석 → 필터 생성 → 조건식 개선
        3. 수렴 또는 최대 반복 도달 시 최종 백테스트 실행
        """
        self.wq.put((ui_num[f'{self.ui_gubun}백테바'], 0, 100, 0))
        start_time = now()

        # === 1. backQ에서 파라미터 수신 ===
        data = self.bq.get()
        if not self._parse_backq_data(data):
            self._sys_exit(True)
            return

        self.wq.put((
            ui_num[f'{self.ui_gubun}백테스트'],
            f'<font color=#45cdf7>[ICOS] 반복적 조건식 개선 시작 '
            f'(최대 {self.max_iterations}회)</font>'
        ))

        # 초기 조건식 저장
        self.initial_buystg = self.current_buystg
        self.initial_sellstg = self.current_sellstg

        # === 2. 반복 루프 ===
        while self.current_iteration < self.max_iterations and not self.converged:
            iter_start = now()
            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                f'<font color=#7cfc00>[ICOS] 반복 {self.current_iteration + 1}/'
                f'{self.max_iterations} 시작</font>'
            ))

            # === 2.1 백테스트 실행 ===
            result = self._run_backtest_iteration()
            if result is None or result.get('status') != 'completed':
                self.wq.put((
                    ui_num[f'{self.ui_gubun}백테스트'],
                    '<font color=#ff0000>[ICOS] 백테스트 실패 - 루프 종료</font>'
                ))
                break

            df_tsg = result['df_tsg']
            metrics = result['metrics']

            # 반복 결과 저장
            self.iteration_results.append({
                'iteration': self.current_iteration,
                'metrics': metrics,
                'buystg': self.current_buystg,
                'timestamp': now(),
            })

            # === 2.2 결과 분석 ===
            analysis = self.analyzer.analyze(df_tsg)
            if not analysis.loss_patterns:
                self.wq.put((
                    ui_num[f'{self.ui_gubun}백테스트'],
                    '<font color=#ffa500>[ICOS] 분석할 손실 패턴 없음 - 수렴</font>'
                ))
                self.converged = True
                break

            # === 2.3 필터 생성 ===
            filter_candidates = self.filter_gen.generate(analysis)
            if not filter_candidates:
                self.wq.put((
                    ui_num[f'{self.ui_gubun}백테스트'],
                    '<font color=#ffa500>[ICOS] 생성할 필터 없음 - 수렴</font>'
                ))
                self.converged = True
                break

            # === 2.4 조건식 개선 ===
            build_result = self.condition_builder.build(
                self.current_buystg, filter_candidates
            )
            new_buystg = build_result.new_condition
            applied_filters = build_result.applied_filters

            if not applied_filters:
                self.wq.put((
                    ui_num[f'{self.ui_gubun}백테스트'],
                    '<font color=#ffa500>[ICOS] 적용할 필터 없음 - 수렴</font>'
                ))
                self.converged = True
                break

            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                f'<font color=#cccccc>[ICOS] {len(applied_filters)}개 필터 적용됨</font>'
            ))

            # === 2.5 수렴 체크 ===
            if len(self.iteration_results) >= 2:
                prev_metrics = self.iteration_results[-2]['metrics']
                improvement = self._calculate_improvement(prev_metrics, metrics)
                self.wq.put((
                    ui_num[f'{self.ui_gubun}백테스트'],
                    f'<font color=#cccccc>[ICOS] 개선율: {improvement:.1f}%</font>'
                ))

                if self.convergence_checker.check(
                    metrics, prev_metrics, self.current_iteration
                ):
                    self.wq.put((
                        ui_num[f'{self.ui_gubun}백테스트'],
                        f'<font color=#7cfc00>[ICOS] 수렴 조건 달성!</font>'
                    ))
                    self.converged = True
                    break

            # 다음 반복 준비
            self.current_buystg = new_buystg
            self.current_iteration += 1

            iter_duration = now() - iter_start
            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                f'<font color=#888888>[ICOS] 반복 {self.current_iteration} 완료 '
                f'(소요: {iter_duration})</font>'
            ))

        # === 3. 최종 백테스트 실행 ===
        self._run_final_backtest()

        # === 4. 결과 저장 및 종료 ===
        total_duration = now() - start_time
        self.wq.put((
            ui_num[f'{self.ui_gubun}백테스트'],
            f'<font color=#45cdf7>[ICOS] 완료 - 총 {self.current_iteration}회 반복, '
            f'소요시간 {total_duration}</font>'
        ))

        # 개선된 조건식 DB 저장 옵션
        if self.icos_config.get('save_improved_condition', False):
            self._save_improved_condition()

        self._sys_exit(False)

    def _parse_backq_data(self, data) -> bool:
        """backQ에서 수신한 데이터 파싱.

        기존 BackTest.Start()와 동일한 형식을 처리합니다.

        Args:
            data: backQ에서 수신한 튜플

        Returns:
            파싱 성공 여부
        """
        try:
            if self.ui_gubun != 'CF':
                self.betting = float(data[0]) * 1000000
            else:
                self.betting = float(data[0])
            self.avgtime = int(data[1])
            self.startday = int(data[2])
            self.endday = int(data[3])
            self.starttime = int(data[4])
            self.endtime = int(data[5])
            buystg_name = data[6]
            sellstg_name = data[7]
            self.dict_cn = data[8]
            self.back_count = data[9]
            self.bl = data[10]
            self.df_kp = data[12]
            self.df_kd = data[13]

            # DB에서 전략 코드 조회
            con = sqlite3.connect(DB_STRATEGY)
            dfb = pd.read_sql(
                f'SELECT * FROM {self.gubun}buy', con
            ).set_index('index')
            dfs = pd.read_sql(
                f'SELECT * FROM {self.gubun}sell', con
            ).set_index('index')
            con.close()

            self.current_buystg = dfb['전략코드'][buystg_name]
            self.current_sellstg = dfs['전략코드'][sellstg_name]
            self.buystg_name = buystg_name
            self.sellstg_name = sellstg_name

            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                f'<font color=#cccccc>[ICOS] 전략 로드: {buystg_name} / {sellstg_name}</font>'
            ))

            return True

        except Exception as e:
            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                f'<font color=#ff0000>[ICOS] 파라미터 파싱 오류: {e}</font>'
            ))
            return False

    def _run_backtest_iteration(self) -> Optional[Dict]:
        """단일 반복 백테스트 실행.

        기존 BackTest.Start() 로직을 재사용하되,
        결과를 ICOSTotal에서 수신하여 반환합니다.

        Returns:
            백테스트 결과 딕셔너리 또는 None
        """
        # 기간 데이터 조회
        if self.ui_gubun == 'S':
            db = DB_STOCK_BACK_TICK if self.dict_set['주식타임프레임'] else DB_STOCK_BACK_MIN
        else:
            db = DB_COIN_BACK_TICK if self.dict_set['코인타임프레임'] else DB_COIN_BACK_MIN

        con = sqlite3.connect(db)
        query = GetMoneytopQuery(
            self.ui_gubun, self.startday, self.endday,
            self.starttime, self.endtime
        )
        df_mt = pd.read_sql(query, con)
        con.close()

        if len(df_mt) == 0 or self.back_count == 0:
            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                '[ICOS] 날짜 지정이 잘못되었거나 데이터가 존재하지 않습니다.'
            ))
            return None

        df_mt['일자'] = df_mt['index'].apply(lambda x: int(str(x)[:8]))
        day_count = len(list(set(df_mt['일자'].to_list())))

        # 보유종목수 어레이 생성
        arry_bct = np.zeros((len(df_mt), 3), dtype='float64')
        arry_bct[:, 0] = df_mt['index'].values

        # ICOSTotal 프로세스 시작
        mq = Queue()
        total_proc = Process(
            target=ICOSTotal,
            args=(
                self.wq, self.sq, self.tq, self.teleQ, mq, self.lq,
                self.bstq_list, self.backname, self.ui_gubun, self.gubun,
                True,  # icos_mode
                {'current': self.current_iteration, 'max': self.max_iterations}
            )
        )
        total_proc.start()

        # 백테정보 전송 (백엔진 + 집계)
        data = (
            '백테정보', self.ui_gubun, None, None, arry_bct,
            self.betting, day_count
        )
        for q in self.bstq_list:
            q.put(data)

        # totalQ로 백테정보 전송 (ICOSTotal용)
        self.tq.put((
            '백테정보', self.betting, self.avgtime, self.startday, self.endday,
            self.starttime, self.endtime, self.buystg_name, self.sellstg_name,
            self.current_buystg, self.current_sellstg, self.dict_cn,
            self.back_count, day_count, self.bl, False,  # schedul=False
            self.df_kp, self.df_kd, False  # back_club=False
        ))

        # 백테스트 시작
        time.sleep(0.5)
        for q in self.bstq_list:
            q.put(('백테시작', 2))

        data = (
            '백테정보', self.betting, self.avgtime, self.startday, self.endday,
            self.starttime, self.endtime, self.current_buystg, self.current_sellstg
        )
        for q in self.beq_list:
            q.put(data)

        # 결과 대기
        try:
            result = mq.get(timeout=600)  # 10분 타임아웃
        except:
            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                '<font color=#ff0000>[ICOS] 백테스트 타임아웃</font>'
            ))
            total_proc.terminate()
            return None

        # ICOSTotal에 종료 신호
        self.tq.put('ICOS종료')
        total_proc.join(timeout=5)
        if total_proc.is_alive():
            total_proc.terminate()

        return result

    def _run_final_backtest(self):
        """최종 조건식으로 백테스트 실행.

        optimiz.py:569-571 패턴 적용:
        최적화 완료 후 최종 조건으로 기존 백테스트 자동 실행
        """
        self.wq.put((
            ui_num[f'{self.ui_gubun}백테스트'],
            '<font color=#7cfc00>[ICOS] 최적화된 조건식으로 최종 백테스트 실행</font>'
        ))

        # 최종 백테스트는 일반 모드로 실행 (icos_mode=False)
        # 이렇게 하면 Report()에서 DB 저장, 그래프 생성 등 모든 기능 실행

        if self.ui_gubun == 'S':
            db = DB_STOCK_BACK_TICK if self.dict_set['주식타임프레임'] else DB_STOCK_BACK_MIN
        else:
            db = DB_COIN_BACK_TICK if self.dict_set['코인타임프레임'] else DB_COIN_BACK_MIN

        con = sqlite3.connect(db)
        query = GetMoneytopQuery(
            self.ui_gubun, self.startday, self.endday,
            self.starttime, self.endtime
        )
        df_mt = pd.read_sql(query, con)
        con.close()

        df_mt['일자'] = df_mt['index'].apply(lambda x: int(str(x)[:8]))
        day_count = len(list(set(df_mt['일자'].to_list())))

        arry_bct = np.zeros((len(df_mt), 3), dtype='float64')
        arry_bct[:, 0] = df_mt['index'].values

        # 최종 결과용 Total 프로세스 (일반 모드)
        mq = Queue()
        from backtester.backtest import Total  # 기존 Total 사용
        total_proc = Process(
            target=Total,
            args=(
                self.wq, self.sq, self.tq, self.teleQ, mq, self.lq,
                self.bstq_list, f'{self.backname}_최종', self.ui_gubun, self.gubun
            )
        )
        total_proc.start()

        # 백테정보 전송
        data = (
            '백테정보', self.ui_gubun, None, None, arry_bct,
            self.betting, day_count
        )
        for q in self.bstq_list:
            q.put(data)

        self.tq.put((
            '백테정보', self.betting, self.avgtime, self.startday, self.endday,
            self.starttime, self.endtime,
            f'{self.buystg_name}_ICOS', self.sellstg_name,
            self.current_buystg, self.current_sellstg, self.dict_cn,
            self.back_count, day_count, self.bl, False,
            self.df_kp, self.df_kd, True  # back_club=True로 상세 리포트
        ))

        time.sleep(0.5)
        for q in self.bstq_list:
            q.put(('백테시작', 2))

        data = (
            '백테정보', self.betting, self.avgtime, self.startday, self.endday,
            self.starttime, self.endtime, self.current_buystg, self.current_sellstg
        )
        for q in self.beq_list:
            q.put(data)

        # 결과 대기
        try:
            result = mq.get(timeout=600)
            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                f'<font color=#7cfc00>[ICOS] 최종 백테스트 완료</font>'
            ))
        except:
            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                '<font color=#ff0000>[ICOS] 최종 백테스트 타임아웃</font>'
            ))

        total_proc.join(timeout=10)
        if total_proc.is_alive():
            total_proc.terminate()

    def _calculate_improvement(
        self,
        prev_metrics: Dict,
        curr_metrics: Dict
    ) -> float:
        """개선율 계산.

        Args:
            prev_metrics: 이전 반복 메트릭
            curr_metrics: 현재 반복 메트릭

        Returns:
            개선율 (%)
        """
        # 주요 지표: 수익금, 승률, 매매성능지수
        prev_profit = prev_metrics.get('total_profit', 0)
        curr_profit = curr_metrics.get('total_profit', 0)

        if prev_profit == 0:
            return 100.0 if curr_profit > 0 else 0.0

        return ((curr_profit - prev_profit) / abs(prev_profit)) * 100

    def _save_improved_condition(self):
        """개선된 조건식 DB 저장."""
        if not self.current_buystg or self.current_buystg == self.initial_buystg:
            return

        try:
            timestamp = strf_time('%Y%m%d_%H%M%S')
            new_name = f'{self.buystg_name}_ICOS_{timestamp}'

            con = sqlite3.connect(DB_STRATEGY)
            df = pd.read_sql(f'SELECT * FROM {self.gubun}buy', con)

            # 새 행 추가
            new_row = {
                'index': new_name,
                '전략코드': self.current_buystg,
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_sql(f'{self.gubun}buy', con, if_exists='replace', index=False)
            con.close()

            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                f'<font color=#7cfc00>[ICOS] 개선된 조건식 저장: {new_name}</font>'
            ))

        except Exception as e:
            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                f'<font color=#ff0000>[ICOS] 조건식 저장 실패: {e}</font>'
            ))

    def _sys_exit(self, cancel: bool):
        """프로세스 종료.

        Args:
            cancel: 취소 여부
        """
        if cancel:
            self.wq.put((ui_num[f'{self.ui_gubun}백테바'], 0, 100, 0))
        else:
            self.wq.put((
                ui_num[f'{self.ui_gubun}백테스트'],
                f'[ICOS] {self.backname} 완료'
            ))
            if self.dict_set.get('스톰라이브', False):
                self.lq.put('ICOS')

        time.sleep(1)
        sys.exit()
