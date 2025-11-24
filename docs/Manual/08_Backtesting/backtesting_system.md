# 08. 백테스팅 시스템

## 🔬 백테스팅 시스템 개요

STOM의 백테스팅 시스템은 **초고정밀도 틱 데이터 기반 시뮬레이션**을 통해 트레이딩 전략의 성과를 검증합니다. 실제 매매 환경과 동일한 조건(수수료, 슬리피지, 호가 단위 등)을 재현하여 과최적화를 방지하고 실전 성능을 예측합니다.

### 백테스팅 아키텍처
```
📊 전략 정의 (Strategy Definition) - 매수/매도 조건식
    ↓
📥 데이터 로딩 (Data Loading) - 틱/분봉 데이터 로드
    ↓
🔄 멀티프로세스 시뮬레이션 (Multi-Process Simulation)
    ├─ 백테엔진 1~N: 병렬 백테스팅 실행
    ├─ 집계 프로세스: 결과 수집 및 통합
    └─ Total 프로세스: 전체 조율 및 리포트
    ↓
📈 성과 분석 (Performance Analysis) - 수익률, MDD, 샤프 비율 등
    ↓
💾 결과 저장 (Result Storage) - SQLite DB 저장
    ↓
📋 리포트 생성 (Report Generation) - UI 표시 및 그래프
```

### STOM 백테스팅의 핵심 특징

1. **틱 단위 정밀 시뮬레이션**: 실제 체결가 기반 백테스팅
2. **멀티프로세스 병렬처리**: CPU 코어를 최대한 활용한 고속 백테스팅
3. **실전 환경 재현**: 호가 단위, 수수료, 세금, 슬리피지 모두 반영
4. **다양한 최적화 기법**: Grid Search, Optuna, GA, 조건식 최적화
5. **교차 검증**: Train/Valid/Test 데이터 분리로 과최적화 방지

---

## 🏗️ 백테스팅 엔진 구조

### 기본 백테스팅 엔진

#### 1. 백테스팅 메인 프로세스 (`backtester/backtest.py:14-113`)

**실제 코드 위치**: `backtester/backtest.py`

**소스**: 예제 코드

```python
class Total:
    """백테스팅 총괄 프로세스 - 모든 백테스팅 결과를 수집하고 통합"""

    def __init__(self, wq, sq, tq, teleQ, mq, lq, bstq_list, backname, ui_gubun, gubun):
        # wq: UI 업데이트 큐
        # sq: 사운드 큐
        # tq: Total 프로세스 수신 큐
        # bstq_list: 백테스팅 집계 프로세스 큐 리스트
        # backname: 백테스팅 유형 (백테스트, 최적화 등)
        # ui_gubun: UI 구분 (S=주식, C=코인, CF=선물)
        # gubun: 시장 구분 (stock, coin)

        self.back_count = None    # 총 백테스팅 횟수
        self.buystg_name = None   # 매수 전략명
        self.buystg = None        # 매수 전략 코드
        self.sellstg = None       # 매도 전략 코드
        self.dict_cn = None       # 종목명 딕셔너리

        self.betting = None       # 종목당 배팅 금액
        self.startday = None      # 시작 일자
        self.endday = None        # 종료 일자
        self.starttime = None     # 시작 시간
        self.endtime = None       # 종료 시간

        self.MainLoop()

    def MainLoop(self):
        """메인 루프 - 백테스팅 결과 수집 및 처리"""
        bc = 0  # 백테스팅 완료 카운트
        sc = 0  # 집계 완료 카운트
        start = now()

        while True:
            data = self.tq.get()

            # 개별 백테스팅 완료 신호
            if data[0] == '백테완료':
                bc += 1
                self.wq.put((ui_num[f'{self.ui_gubun}백테바'], bc, self.back_count, start))

                if bc == self.back_count:
                    bc = 0
                    # 모든 백테스팅 완료 → 집계 시작
                    for q in self.bstq_list[:5]:
                        q.put(('백테완료', '분리집계'))

            # 집계 완료 신호
            elif data == '집계완료':
                sc += 1
                if sc == 5:
                    sc = 0
                    for q in self.bstq_list[:5]:
                        q.put('결과분리')

            # 결과 분리 완료
            elif data == '분리완료':
                sc += 1
                if sc == 5:
                    sc = 0
                    self.bstq_list[0].put('결과전송')

            # 최종 백테스팅 결과 수신
            elif data[0] == '백테결과':
                _, list_tsg, arry_bct = data
                self.Report(list_tsg, arry_bct)
```

**동작 원리**:
- **멀티프로세스 조율**: 여러 백테엔진이 병렬로 실행하며 결과를 Total 프로세스가 수집
- **진행률 표시**: UI 프로그레스 바 업데이트 (`wq` 큐 사용)
- **단계별 처리**: 백테완료 → 집계 → 결과분리 → 결과전송 순차 진행

### 주식 백테스팅 엔진

#### 1. Kiwoom 틱 백테스팅 엔진 (`backtester/backengine_kiwoom_tick.py:14-240`)

**실제 코드 위치**: `backtester/backengine_kiwoom_tick.py`

**소스**: 예제 코드

```python
class BackEngineKiwoomTick:
    """키움 증권 틱 데이터 백테스팅 엔진 - 실제 키움 OpenAPI 환경 재현"""

    def __init__(self, gubun, wq, tq, bq, beq_list, bstq_list, profile=False):
        # gubun: 엔진 번호 (멀티프로세싱용)
        # wq: UI 업데이트 큐
        # tq: Total 프로세스 통신 큐
        # bq: 백테엔진 수신 큐
        # beq_list: 모든 백테엔진 큐 리스트
        # bstq_list: 집계 프로세스 큐 리스트

        gc.disable()  # 가비지 컬렉션 비활성화 (성능 향상)

        self.gubun = gubun
        self.back_type = None  # '백테스트', '최적화', 'GA최적화', '조건최적화'

        # 백테스팅 설정
        self.betting = None       # 종목당 배팅 금액
        self.avgtime = None       # 이동평균 계산용 틱 수
        self.startday = None      # 시작일
        self.endday = None        # 종료일
        self.starttime = None     # 시작시간
        self.endtime = None       # 종료시간

        # 전략 코드
        self.buystg = None        # 매수 전략 (compile된 코드 객체)
        self.sellstg = None       # 매도 전략 (compile된 코드 객체)
        self.indistg = None       # 지표 계산 전략
        self.dict_sconds = None   # 매도 조건 딕셔너리

        # 데이터 저장소
        self.code_list = []       # 백테스팅할 종목 코드 리스트
        self.dict_arry = {}       # 종목별 틱 데이터 배열
        self.bhogainfo = {}       # 매수 호가 정보
        self.shogainfo = {}       # 매도 호가 정보
        self.trade_info = {}      # 거래 정보 (보유중, 매수가, 매도가 등)
        self.day_info = {}        # 일자별 정보

        self.MainLoop()

    def MainLoop(self):
        """메인 루프 - 백테엔진의 작업 처리"""
        while True:
            data = self.beq.get()

            # 백테스팅 정보 수신
            if '정보' in data[0]:
                if self.back_type == '백테스트':
                    if data[0] == '백테정보':
                        self.betting   = data[1]
                        self.avgtime   = data[2]
                        self.startday  = data[3]
                        self.endday    = data[4]
                        self.starttime = data[5]
                        self.endtime   = data[6]
                        # 전략 코드 컴파일
                        self.buystg, self.indistg = GetBuyStg(data[7], self.gubun)
                        self.sellstg, self.dict_sconds = GetSellStg(data[8], self.gubun)
                        self.InitDivid()
                        self.InitTradeInfo()
                        if self.buystg is None or self.sellstg is None:
                            self.BackStop()
                        else:
                            self.BackTest()

            # 백테스팅 유형 설정
            elif data[0] == '백테유형':
                self.back_type = data[1]

            # 데이터 로딩
            elif data[0] in ('데이터크기', '데이터로딩'):
                self.DataLoad(data)

    def DataLoad(self, data):
        """틱 데이터 로딩 - SQLite에서 종목별 틱 데이터 읽기"""
        bk = 0
        divid_mode = data[-1]
        is_tick = self.dict_set['주식타임프레임']  # True=틱, False=분봉

        # DB 연결 (틱 또는 분봉)
        con = sqlite3.connect(DB_STOCK_BACK_TICK if is_tick else DB_STOCK_BACK_MIN)

        if divid_mode == '종목코드별 분류':
            gubun, startday, endday, starttime, endtime, code_list, avg_list, code_days, _, _, _ = data

            for code in code_list:
                df_tick, len_df_tick = None, 0
                try:
                    # 종목별 틱 데이터 쿼리 (backtester/back_static.py:75-91)
                    df_tick = pd.read_sql(GetBackloadCodeQuery(code, code_days[code], starttime, endtime), con)
                    len_df_tick = len(df_tick)
                except:
                    pass

                if gubun == '데이터크기':
                    self.bq.put((code, len_df_tick))
                elif len_df_tick > 0:
                    # 이동평균 등 추가 데이터 계산 (backtester/back_static.py:131-183)
                    df_tick = AddAvgData(df_tick, 3, is_tick, avg_list)
                    arry_tick = np.array(df_tick)

                    if self.dict_set['백테일괄로딩']:
                        # 메모리에 일괄 로딩 (빠른 접근)
                        self.dict_arry[code] = arry_tick
                    else:
                        # 파일로 저장 (메모리 절약)
                        pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_tick', arry_tick)

                    self.code_list.append(code)
                    bk += 1
```

**주요 특징**:
- **실전 환경 재현**: 키움 API의 실제 호가 단위, 수수료(0.015%), 증권거래세(0.25%) 반영
- **멀티프로세스**: 각 엔진이 독립적으로 종목 그룹을 처리
- **메모리 최적화**: 일괄 로딩 또는 파일 캐시 선택 가능
- **틱/분봉 지원**: 설정에 따라 틱 데이터 또는 분봉 데이터 사용

### 암호화폐 백테스팅 엔진

#### 1. Upbit 백테스팅 (`backtester/backengine_upbit_tick.py`)

**소스**: 예제 코드

```python
class BackEngineUpbitTick:
    """업비트 틱 데이터 백테스팅 엔진"""
    
    def __init__(self):
        self.initial_krw = 1000000
        self.current_krw = self.initial_krw
        self.coin_holdings = {}
        
        # 업비트 수수료 (0.05%)
        self.commission_rate = 0.0005
        
    def load_upbit_tick_data(self, market, start_date, end_date):
        """업비트 틱 데이터 로드"""
        query = """
        SELECT timestamp, trade_price, trade_volume, acc_trade_price
        FROM coin_tick 
        WHERE market = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
        """
        
        return db_manager.execute_query(query, [market, start_date, end_date])
        
    def run_coin_strategy(self, strategy_name, market, start_date, end_date):
        """코인 전략 백테스팅"""
        # 데이터 로드
        tick_data = self.load_upbit_tick_data(market, start_date, end_date)
        
        # 전략별 처리
        if strategy_name == 'scalping':
            return self.run_scalping_strategy(market, tick_data)
        elif strategy_name == 'momentum':
            return self.run_momentum_strategy(market, tick_data)
            
    def run_scalping_strategy(self, market, tick_data):
        """스캘핑 전략"""
        price_buffer = deque(maxlen=10)
        position = 0
        entry_price = 0
        
        for tick in tick_data:
            timestamp, price, volume, acc_trade_price = tick
            price_buffer.append(price)
            
            if len(price_buffer) >= 10:
                # 단기 모멘텀 계산
                recent_prices = list(price_buffer)
                momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                
                # 매수 신호 (0.1% 이상 상승)
                if momentum > 0.001 and position == 0:
                    quantity = self.current_krw * 0.1 / price  # 10% 투자
                    if self.execute_buy(market, quantity, price, timestamp):
                        position = quantity
                        entry_price = price
                        
                # 매도 신호 (0.2% 수익 또는 -0.1% 손실)
                elif position > 0:
                    profit_rate = (price - entry_price) / entry_price
                    
                    if profit_rate >= 0.002 or profit_rate <= -0.001:
                        if self.execute_sell(market, position, price, timestamp):
                            position = 0
                            entry_price = 0
                            
        return self.calculate_performance()
```

---

## 📊 성과 분석 시스템

### 성과 지표 계산

#### 1. 성과 분석기

**소스**: 예제 코드

```python
class PerformanceAnalyzer:
    """성과 분석기"""
    
    def __init__(self, trades, equity_curve, initial_capital):
        self.trades = trades
        self.equity_curve = equity_curve
        self.initial_capital = initial_capital
        
    def calculate_metrics(self):
        """성과 지표 계산"""
        metrics = {}
        
        # 기본 수익률 지표
        metrics.update(self.calculate_return_metrics())
        
        # 리스크 지표
        metrics.update(self.calculate_risk_metrics())
        
        # 거래 지표
        metrics.update(self.calculate_trade_metrics())
        
        # 드로우다운 지표
        metrics.update(self.calculate_drawdown_metrics())
        
        return metrics
        
    def calculate_return_metrics(self):
        """수익률 지표"""
        final_value = self.equity_curve[-1] if self.equity_curve else self.initial_capital
        
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # 연율화 수익률
        days = len(self.equity_curve)
        annual_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'final_value': final_value
        }
        
    def calculate_risk_metrics(self):
        """리스크 지표"""
        if len(self.equity_curve) < 2:
            return {'volatility': 0, 'sharpe_ratio': 0}
            
        # 일일 수익률 계산
        daily_returns = []
        for i in range(1, len(self.equity_curve)):
            daily_return = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            daily_returns.append(daily_return)
            
        # 변동성 (연율화)
        volatility = np.std(daily_returns) * np.sqrt(252)
        
        # 샤프 비율 (무위험 수익률 3% 가정)
        avg_return = np.mean(daily_returns) * 252
        sharpe_ratio = (avg_return - 0.03) / volatility if volatility > 0 else 0
        
        return {
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio
        }
        
    def calculate_trade_metrics(self):
        """거래 지표"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }
            
        # 매수/매도 쌍 찾기
        trade_pairs = self.find_trade_pairs()
        
        winning_trades = [t for t in trade_pairs if t['pnl'] > 0]
        losing_trades = [t for t in trade_pairs if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / len(trade_pairs) if trade_pairs else 0
        
        avg_profit = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        total_profit = sum([t['pnl'] for t in winning_trades])
        total_loss = abs(sum([t['pnl'] for t in losing_trades]))
        
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return {
            'total_trades': len(trade_pairs),
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor
        }
        
    def calculate_drawdown_metrics(self):
        """드로우다운 지표"""
        if not self.equity_curve:
            return {'max_drawdown': 0, 'max_drawdown_duration': 0}
            
        peak = self.equity_curve[0]
        max_drawdown = 0
        max_duration = 0
        current_duration = 0
        
        for value in self.equity_curve:
            if value > peak:
                peak = value
                current_duration = 0
            else:
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
                current_duration += 1
                max_duration = max(max_duration, current_duration)
                
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_duration': max_duration
        }
```

### 벤치마크 비교

#### 1. 벤치마크 분석

**소스**: 예제 코드

```python
class BenchmarkAnalyzer:
    """벤치마크 비교 분석"""
    
    def __init__(self):
        self.benchmarks = {
            'KOSPI': self.load_kospi_data,
            'KOSDAQ': self.load_kosdaq_data,
            'BTC': self.load_bitcoin_data
        }
        
    def compare_with_benchmark(self, strategy_returns, benchmark_name, start_date, end_date):
        """벤치마크와 비교"""
        # 벤치마크 데이터 로드
        benchmark_data = self.benchmarks[benchmark_name](start_date, end_date)
        benchmark_returns = self.calculate_benchmark_returns(benchmark_data)
        
        # 상관관계 계산
        correlation = np.corrcoef(strategy_returns, benchmark_returns)[0, 1]
        
        # 베타 계산
        beta = np.cov(strategy_returns, benchmark_returns)[0, 1] / np.var(benchmark_returns)
        
        # 알파 계산 (CAPM)
        strategy_avg_return = np.mean(strategy_returns)
        benchmark_avg_return = np.mean(benchmark_returns)
        risk_free_rate = 0.03 / 252  # 일일 무위험 수익률
        
        alpha = strategy_avg_return - (risk_free_rate + beta * (benchmark_avg_return - risk_free_rate))
        
        return {
            'correlation': correlation,
            'beta': beta,
            'alpha': alpha * 252,  # 연율화
            'information_ratio': self.calculate_information_ratio(strategy_returns, benchmark_returns)
        }
        
    def calculate_information_ratio(self, strategy_returns, benchmark_returns):
        """정보 비율 계산"""
        excess_returns = np.array(strategy_returns) - np.array(benchmark_returns)
        tracking_error = np.std(excess_returns)
        
        if tracking_error == 0:
            return 0
            
        return np.mean(excess_returns) / tracking_error
```

---

## 📈 최적화 시스템

STOM의 최적화 시스템은 전략 파라미터를 자동으로 튜닝하여 최고의 성능을 찾아냅니다. 과최적화를 방지하기 위해 **Train/Valid/Test** 데이터 분리와 다양한 최적화 알고리즘을 제공합니다.

### 최적화 유형

1. **일반 최적화 (Optuna)**: Bayesian Optimization 기반, 효율적인 파라미터 탐색
2. **GA 최적화**: 유전 알고리즘 기반, 전역 최적해 탐색
3. **조건식 최적화**: 매수/매도 조건문의 모든 조합 탐색
4. **전진분석 (Rolling Walk Forward)**: 시계열 데이터의 미래 예측 성능 검증

### 파라미터 최적화 프로세스 (`backtester/optimiz.py:16-200`)

**실제 코드 위치**: `backtester/optimiz.py`

**소스**: 예제 코드

```python
class Total:
    """최적화 총괄 프로세스 - Optuna 기반 파라미터 최적화"""

    def __init__(self, wq, sq, tq, teleQ, mq, lq, beq_list, bstq_list, backname, ui_gubun, gubun, multi, divid_mode):
        # wq: UI 업데이트 큐
        # beq_list: 백테엔진 큐 리스트
        # bstq_list: 집계 프로세스 큐 리스트
        # backname: 최적화 유형 ('최적화', 'VC최적화', 'V최적화')
        # multi: 멀티프로세스 개수
        # divid_mode: 데이터 분할 모드

        self.back_count = None       # 백테스팅 횟수
        self.opti_turn = None        # 최적화 단계 (0=ALL, 1=TRAIN, 2=VALID, 4=TEST)

        # 최적화 변수
        self.vars = None             # 현재 변수 조합
        self.vars_list = None        # 모든 변수 조합 리스트
        self.stdp = -2_000_000_000  # 현재 최고 성능 점수
        self.total_count = 0         # 총 최적화 횟수
        self.total_count2 = 0        # 총 틱 수

        # 교차 검증
        self.dict_t = {}             # Train 데이터 결과
        self.dict_v = {}             # Valid 데이터 결과
        self.weeks_train = None      # 학습 기간 (주 단위)
        self.weeks_valid = None      # 검증 기간 (주 단위)
        self.weeks_test = None       # 테스트 기간 (주 단위)

        self.MainLoop()

    def MainLoop(self):
        """메인 루프 - 최적화 결과 수집 및 평가"""
        tt  = 0   # 탐색 완료 카운트
        sc  = 0   # 집계 완료 카운트
        bc  = 0   # 백테스팅 완료 카운트
        tbc = 0   # 전체 백테스팅 완료 카운트
        st  = {}  # 변수 조합별 상태
        start = now()

        while True:
            data = self.tq.get()

            # 백테스팅 완료 신호
            if data[0] == '백테완료':
                bc  += 1
                tbc += 1

                # opti_turn에 따라 다른 처리
                if self.opti_turn == 1:
                    # TRAIN 단계: 데이터 일괄 로딩 최적화
                    pass
                elif self.opti_turn in (0, 2):
                    # ALL 또는 VALID 단계: 진행률 표시
                    self.wq.put((ui_num[f'{self.ui_gubun}백테바'], bc, self.total_count, start))

                if bc == self.back_count:
                    bc = 0
                    if self.opti_turn == 1:
                        # TRAIN 단계 완료 → 미분리 집계
                        for q in self.bstq_list:
                            q.put(('백테완료', '미분리집계'))
                    else:
                        # 분리 집계
                        for q in self.bstq_list[:5]:
                            q.put(('백테완료', '분리집계'))

            # Train/Valid 결과 수신
            elif data[0] in ('TRAIN', 'VALID'):
                gubun, num, data, vturn, vkey = data

                # vturn: 변수 조합 턴 번호
                # vkey: 변수 조합 키

                if vturn not in self.dict_t.keys():
                    self.dict_t[vturn] = {}
                if vkey not in self.dict_t[vturn].keys():
                    self.dict_t[vturn][vkey] = {}
                if vturn not in self.dict_v.keys():
                    self.dict_v[vturn] = {}
                if vkey not in self.dict_v[vturn].keys():
                    self.dict_v[vturn][vkey] = {}

                if gubun == 'TRAIN':
                    self.dict_t[vturn][vkey][num] = data
                else:
                    self.dict_v[vturn][vkey][num] = data

                st[vturn][vkey] += 1
                if st[vturn][vkey] == self.sub_total:
                    # 모든 Train/Valid 결과 수집 완료 → 평가
                    self.stdp = SendTextAndStd(
                        self.GetSendData(vturn, vkey),
                        self.dict_t[vturn][vkey],
                        self.dict_v[vturn][vkey],
                        self.dict_set['교차검증가중치']
                    )
                    st[vturn][vkey] = 0

            # ALL (단일 백테스팅) 결과 수신
            elif data[0] == 'ALL':
                _, _, data, vturn, vkey = data
                self.stdp = SendTextAndStd(self.GetSendData(vturn, vkey), data)
```

**최적화 프로세스 흐름**:

1. **변수 범위 설정**: UI에서 최적화할 변수와 범위 지정 (예: RSI 기간 10~30)
2. **데이터 분할**:
   - **V최적화**: Train (학습) + Valid (검증)
   - **VC최적화**: Train + Valid (교차검증, k-fold 방식)
   - **일반 최적화**: 전체 데이터 사용
3. **Optuna 탐색**: Bayesian Optimization으로 효율적인 파라미터 탐색
4. **성능 평가**: Train과 Valid 데이터의 가중 평균으로 과최적화 방지
5. **최적 파라미터 선택**: 가장 높은 점수를 받은 파라미터 조합 선택

### 몬테카를로 시뮬레이션

#### 1. 몬테카를로 분석

**소스**: 예제 코드

```python
class MonteCarloAnalyzer:
    """몬테카를로 시뮬레이션"""
    
    def __init__(self, trades):
        self.trades = trades
        
    def run_simulation(self, num_simulations=1000):
        """몬테카를로 시뮬레이션 실행"""
        simulation_results = []
        
        for _ in range(num_simulations):
            # 거래 순서 랜덤 셔플
            shuffled_trades = self.trades.copy()
            random.shuffle(shuffled_trades)
            
            # 자산 곡선 계산
            equity_curve = self.calculate_equity_curve(shuffled_trades)
            
            # 성과 지표 계산
            final_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
            max_drawdown = self.calculate_max_drawdown(equity_curve)
            
            simulation_results.append({
                'final_return': final_return,
                'max_drawdown': max_drawdown,
                'equity_curve': equity_curve
            })
            
        return self.analyze_simulation_results(simulation_results)
        
    def analyze_simulation_results(self, results):
        """시뮬레이션 결과 분석"""
        final_returns = [r['final_return'] for r in results]
        max_drawdowns = [r['max_drawdown'] for r in results]
        
        return {
            'return_percentiles': {
                '5%': np.percentile(final_returns, 5),
                '25%': np.percentile(final_returns, 25),
                '50%': np.percentile(final_returns, 50),
                '75%': np.percentile(final_returns, 75),
                '95%': np.percentile(final_returns, 95)
            },
            'drawdown_percentiles': {
                '5%': np.percentile(max_drawdowns, 5),
                '25%': np.percentile(max_drawdowns, 25),
                '50%': np.percentile(max_drawdowns, 50),
                '75%': np.percentile(max_drawdowns, 75),
                '95%': np.percentile(max_drawdowns, 95)
            },
            'probability_of_loss': len([r for r in final_returns if r < 0]) / len(final_returns)
        }
```

---

## 📋 리포트 생성

### 백테스팅 리포트

#### 1. 리포트 생성기

**소스**: 예제 코드

```python
class BacktestReportGenerator:
    """백테스팅 리포트 생성기"""
    
    def __init__(self, performance_analyzer, benchmark_analyzer):
        self.performance_analyzer = performance_analyzer
        self.benchmark_analyzer = benchmark_analyzer
        
    def generate_html_report(self, output_path):
        """HTML 리포트 생성"""
        # 성과 지표 계산
        metrics = self.performance_analyzer.calculate_metrics()
        
        # 차트 생성
        charts = self.generate_charts()
        
        # HTML 템플릿
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>백테스팅 리포트</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .metric { margin: 10px 0; }
                .chart { margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>백테스팅 리포트</h1>
            
            <h2>성과 요약</h2>
            <div class="metric">총 수익률: {total_return:.2%}</div>
            <div class="metric">연율화 수익률: {annual_return:.2%}</div>
            <div class="metric">샤프 비율: {sharpe_ratio:.2f}</div>
            <div class="metric">최대 드로우다운: {max_drawdown:.2%}</div>
            <div class="metric">승률: {win_rate:.2%}</div>
            
            <h2>자산 곡선</h2>
            <div class="chart">{equity_chart}</div>
            
            <h2>드로우다운 차트</h2>
            <div class="chart">{drawdown_chart}</div>
            
            <h2>월별 수익률</h2>
            <div class="chart">{monthly_returns_chart}</div>
            
        </body>
        </html>
        """.format(**metrics, **charts)
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)
            
    def generate_charts(self):
        """차트 생성"""
        import matplotlib.pyplot as plt
        import base64
        from io import BytesIO
        
        charts = {}
        
        # 자산 곡선 차트
        plt.figure(figsize=(12, 6))
        plt.plot(self.performance_analyzer.equity_curve)
        plt.title('자산 곡선')
        plt.xlabel('일자')
        plt.ylabel('자산 가치')
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        chart_data = base64.b64encode(buffer.getvalue()).decode()
        charts['equity_chart'] = f'<img src="data:image/png;base64,{chart_data}">'
        plt.close()
        
        return charts
```

---

*다음: [09. 사용자 매뉴얼](../09_Manual/user_manual.md)* 
## 🧬 유전 알고리즘 (GA) 최적화

### GA 최적화 개요 (`backtester/optimiz_genetic_algorithm.py:160-300`)

**실제 코드 위치**: `backtester/optimiz_genetic_algorithm.py`

유전 알고리즘(Genetic Algorithm)은 자연 선택의 원리를 모방한 최적화 기법입니다. STOM의 GA 최적화는 **전역 최적해(Global Optimum)** 탐색에 탁월하며, 수백 개의 변수 조합을 동시에 진화시킵니다.

### GA 작동 원리

```
1세대: 무작위 변수 조합 1000개 생성
   ↓
백테스팅 실행 → 성능 평가 (적합도 함수)
   ↓
2세대: 상위 20% 선택 (엘리트 전략)
   ├─ 교차(Crossover): 우수한 변수끼리 결합
   ├─ 돌연변이(Mutation): 일부 변수 무작위 변경
   └─ 새로운 1000개 조합 생성
   ↓
... 50세대 반복 ...
   ↓
최적 변수 조합 도출
```

**GA 최적화의 장점**:
- **전역 최적해 탐색**: 국소 최적해(Local Optimum)에 갇히지 않음
- **대규모 탐색 공간**: 수백 개 변수 조합을 동시에 평가
- **다양성 유지**: 돌연변이로 새로운 가능성 탐색

**단점**:
- **계산 비용**: 많은 백테스팅 필요 (1000개 × 50세대 = 50,000회)
- **수렴 속도**: Optuna보다 느릴 수 있음

---

## 🔍 조건식 최적화

### 조건식 최적화 개요 (`backtester/optimiz_conditions.py:147-200`)

**실제 코드 위치**: `backtester/optimiz_conditions.py`

조건식 최적화는 **매수 조건과 매도 조건의 모든 조합**을 탐색하여 최고의 조건문을 찾습니다. 파라미터 최적화가 "숫자 값"을 튜닝한다면, 조건식 최적화는 "논리식 자체"를 탐색합니다.

### 조건식 최적화 원리

```
매수 조건 5개 정의:
├─ 조건1: RSI < 30 and 체결강도 > 100
├─ 조건2: 이평선60 상향돌파
├─ 조건3: 전일비 > 5% and 거래량 급증
├─ 조건4: MACD 골든크로스
└─ 조건5: 볼린저밴드 하단 터치

매도 조건 5개 정의:
├─ 조건1: 수익률 > 2% (익절)
├─ 조건2: 수익률 < -1% (손절)
├─ 조건3: RSI > 70 (과매수)
├─ 조건4: 보유시간 > 600초 (시간손절)
└─ 조건5: 이평선60 하향이탈

전체 조합: 5 × 5 = 25가지
↓
백테스팅 실행 → 최고 성능 조합 선택
```

**조건식 최적화 활용**:
- **초기 전략 탐색**: 어떤 조건이 효과적인지 빠르게 파악
- **조건 조합 발견**: 단독으로는 약하지만 조합하면 강력한 조건 발견
- **전략 검증**: 직관적으로 만든 조건식의 실제 성능 확인

---

## 📚 학습용 예제 - 전략 개발 워크플로우

### 예제 1: RSI 역추세 전략 완전 개발 과정

실전에서 사용 가능한 RSI 전략을 처음부터 끝까지 개발하는 과정입니다.

**단계 1: 기본 아이디어 정의**

**소스**: 예제 코드

```python
"""
전략 아이디어: RSI 과매도 구간 매수
- 매수: RSI < 30 (과매도)
- 매도: RSI > 70 (과매수) 또는 수익률 2% 또는 손실률 -1%
"""
```

**단계 2: 백테스팅으로 기본 성능 확인**

**소스**: 예제 코드

```python
# 고정 파라미터로 백테스팅 (backtester/backtest.py 사용)
# RSI 기간=14, 과매도=30, 과매수=70, 익절=2%, 손절=1%

매수 전략:
if RSI < 30 and 체결강도 > 100:
    매수 = 1

매도 전략:
if 보유중:
    수익률 = (현재가 - 매수가) / 매수가 * 100
    if RSI > 70 or 수익률 >= 2.0 or 수익률 <= -1.0:
        매도 = 1
```

**결과**: 연간 수익률 8%, Sharpe 0.9, MDD -15% → 개선 필요

**단계 3: 조건식 최적화로 더 나은 조건 찾기**

**소스**: 예제 코드

```python
# 다양한 매수/매도 조건 시도 (backtester/optimiz_conditions.py)

매수 조건 후보:
1. RSI < 30 and 체결강도 > 100
2. RSI < 25 and 등락율 < -3%
3. 볼린저밴드 하단 터치 and RSI < 35
4. MACD < 0 and RSI < 30
5. 이평선60 > 현재가 and RSI < 32

매도 조건 후보:
1. RSI > 70 or 수익률 >= 2%
2. 수익률 >= 3% or 수익률 <= -1.5%
3. 보유시간 > 900초
4. RSI > 65 and 체결강도 < 90
5. 이평선60 상향돌파
```

**최적 조합 발견**: 매수 조건 3번 + 매도 조건 2번  
**결과**: 연간 수익률 15%, Sharpe 1.3, MDD -12%

**단계 4: 파라미터 최적화 (Optuna)**

**소스**: 예제 코드

```python
# 발견한 조건식의 파라미터 튜닝 (backtester/optimiz.py)

최적화 변수:
- RSI 기간: 10~20
- 과매도 기준: 25~40
- 익절: 2.0~4.0%
- 손절: 0.5~2.0%
- 시간 손절: 600~1800초
```

**최적 파라미터**: RSI=12, 과매도=32, 익절=2.7%, 손절=0.9%, 시간=1200초  
**결과**: 연간 수익률 22%, Sharpe 1.8, MDD -10%

**단계 5: 교차 검증 (Train/Valid/Test)**

**소스**: 예제 코드

```python
# V최적화로 과최적화 방지 (backtester/optimiz.py)
# 데이터 분할: Train 70% + Valid 30%

Train 성능: 연간 25%, Sharpe 2.0, MDD -9%
Valid 성능: 연간 18%, Sharpe 1.5, MDD -12%
```

**평가**: Train-Valid 성능 차이 28% → 약간의 과최적화 의심

**단계 6: 전진 분석 (Walk Forward)**

**소스**: 예제 코드

```python
# 롤링 윈도우로 실전 성능 예측 (backtester/rolling_walk_forward_test.py)

윈도우 1 (2023.01~06): Test Sharpe 1.6
윈도우 2 (2023.04~09): Test Sharpe 1.4
윈도우 3 (2023.07~12): Test Sharpe 1.7
윈도우 4 (2023.10~2024.03): Test Sharpe 1.2
윈도우 5 (2024.01~06): Test Sharpe 1.5

평균 Sharpe: 1.48
양수 윈도우: 100%
```

**결론**: ✅ 실전 적용 가능 - 일관된 성능

**단계 7: 실전 모니터링**

- 실제 거래 3개월 후 재평가
- 성능 하락 시 파라미터 재최적화
- 시장 환경 변화 감지 시 조건식 재검토

---

### 예제 2: 과최적화를 피하는 10가지 원칙 (학습용 가이드)

**소스**: 예제 코드

```python
"""
과최적화 방지 체크리스트

1. ✅ Train/Valid/Test 데이터 분리
   - Train: 60%, Valid: 20%, Test: 20%
   - 시계열 순서 유지 (랜덤 샘플링 금지)

2. ✅ 충분한 거래 횟수 확보
   - 최소 200회 이상 거래
   - 거래가 특정 기간에 몰리지 않도록

3. ✅ Train-Valid 성능 차이 30% 이내
   - 차이가 크면 파라미터 범위 축소
   - 또는 더 단순한 전략으로 변경

4. ✅ 파라미터 개수 제한
   - 최대 5개 이하 권장
   - 파라미터 간 상관관계 확인

5. ✅ 변수 범위 합리적으로 설정
   - RSI 기간: 5~30 (O), 1~100 (X - 너무 넓음)
   - 경험적 범위 활용

6. ✅ 전진 분석 필수
   - 최소 6개월 이상 기간
   - 다양한 시장 환경 포함

7. ✅ 여러 시장/종목에서 검증
   - 단일 종목 과최적화 방지
   - 최소 10개 이상 종목 테스트

8. ✅ 성능 지표 다각도 평가
   - Sharpe Ratio만 보지 말고
   - MDD, 승률, Profit Factor도 확인

9. ✅ 단순한 전략 선호
   - 복잡한 조건 < 단순하고 강건한 조건
   - "If 조건 10개 AND..." → 과최적화 의심

10. ✅ 주기적 재평가
    - 3개월마다 성능 리뷰
    - 시장 regime 변화 감지
"""

# 과최적화 탐지 코드
def detect_overfitting(train_perf, valid_perf, test_perf):
    warnings = []

    # 1. Train-Valid 격차
    train_sharpe = train_perf['sharpe']
    valid_sharpe = valid_perf['sharpe']
    if train_sharpe > 0:
        gap = (train_sharpe - valid_sharpe) / train_sharpe * 100
        if gap > 30:
            warnings.append(f'⚠️ Train-Valid 격차 {gap:.1f}%')

    # 2. 거래 횟수
    if valid_perf['trades'] < 100:
        warnings.append(f'⚠️ Valid 거래 {valid_perf["trades"]}회 (최소 100회)')

    # 3. Valid-Test 불일치
    test_sharpe = test_perf['sharpe']
    if abs(valid_sharpe - test_sharpe) / valid_sharpe > 0.4:
        warnings.append(f'⚠️ Valid-Test 불일치')

    return len(warnings) == 0, warnings

# 사용 예시
is_safe, warnings = detect_overfitting(train, valid, test)
if not is_safe:
    print('과최적화 의심:', warnings)
```

---

## 🎯 실전 적용 가이드

### 백테스팅 → 실전 전환 프로세스

```
1. 백테스팅 완료 (MDD < 20%, Sharpe > 1.0)
   ↓
2. 전진 분석 통과 (양수 윈도우 > 70%)
   ↓
3. 소액 실전 테스트 (종목당 10만원, 1개월)
   ↓
4. 실제 성능 vs 백테스팅 비교
   - 슬리피지 측정: 백테 가격 vs 실제 체결가
   - 수수료 오차: 예상 vs 실제
   ↓
5. 성능 검증 통과 시 → 본격 운용
   - 점진적 자금 증액 (월 20%씩)
   - 최대 리스크 한도: 총 자산의 30%
```

### 실전 vs 백테스팅 차이점

| 항목 | 백테스팅 | 실전 | 대응 방안 |
|------|---------|------|----------|
| **체결 가격** | 틱 데이터 현재가 | 호가 단위, 슬리피지 | 백테에 슬리피지 0.1% 반영 |
| **체결 여부** | 100% 체결 가정 | 유동성 부족 시 미체결 | 거래량 조건 추가 (일 50억 이상) |
| **수수료** | 고정 0.015% | 증권사별 상이 | 실제 수수료로 백테 재실행 |
| **심리적 요인** | 없음 | 연속 손실 시 전략 이탈 | 손실 허용 한도 사전 설정 |
| **시스템 리스크** | 없음 | 서버 다운, 네트워크 끊김 | 이중화, 알림 시스템 |

---

*다음: [09. 사용자 매뉴얼](../09_Manual/user_manual.md)*
