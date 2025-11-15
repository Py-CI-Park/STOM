# 08. 백테스팅 시스템

## 🔬 백테스팅 시스템 개요

STOM의 백테스팅 시스템은 **고정밀도 시뮬레이션**을 통해 트레이딩 전략의 성과를 검증합니다. 틱 데이터부터 일봉 데이터까지 다양한 시간 프레임에서 백테스팅을 지원하며, 실제 거래 환경과 유사한 조건을 재현합니다.

### 백테스팅 아키텍처
```
📊 전략 정의 (Strategy Definition)
    ↓
🔄 시뮬레이션 엔진 (Simulation Engine)
    ↓
📈 성과 분석 (Performance Analysis)
    ↓
📋 리포트 생성 (Report Generation)
```

---

## 🏗️ 백테스팅 엔진 구조

### 기본 백테스팅 엔진

#### 1. 백테스팅 엔진 기본 클래스 (`backtester/backengine.py`)
```python
class BacktestEngine:
    """백테스팅 엔진 기본 클래스"""
    
    def __init__(self, initial_capital=10000000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
        # 수수료 및 슬리피지 설정
        self.commission_rate = 0.0015  # 0.15%
        self.slippage = 0.001          # 0.1%
        
    def run_backtest(self, strategy, data, start_date, end_date):
        """백테스팅 실행"""
        self.reset_state()
        
        # 데이터 필터링
        filtered_data = self.filter_data_by_date(data, start_date, end_date)
        
        # 시뮬레이션 실행
        for timestamp, market_data in filtered_data:
            self.process_timestamp(strategy, timestamp, market_data)
            
        # 최종 결과 계산
        return self.calculate_final_results()
        
    def process_timestamp(self, strategy, timestamp, market_data):
        """타임스탬프별 처리"""
        # 전략 신호 계산
        signals = strategy.calculate_signals(market_data)
        
        # 주문 실행
        for signal in signals:
            self.execute_order(signal, market_data, timestamp)
            
        # 포지션 평가
        self.update_portfolio_value(market_data, timestamp)
        
    def execute_order(self, order, market_data, timestamp):
        """주문 실행"""
        symbol = order['symbol']
        order_type = order['type']
        quantity = order['quantity']
        
        # 실행 가격 계산 (슬리피지 포함)
        if order_type == 'BUY':
            execution_price = market_data[symbol]['price'] * (1 + self.slippage)
        else:
            execution_price = market_data[symbol]['price'] * (1 - self.slippage)
            
        # 수수료 계산
        commission = execution_price * quantity * self.commission_rate
        
        # 거래 기록
        trade = {
            'timestamp': timestamp,
            'symbol': symbol,
            'type': order_type,
            'quantity': quantity,
            'price': execution_price,
            'commission': commission,
            'total_cost': execution_price * quantity + commission
        }
        
        self.trades.append(trade)
        self.update_position(trade)
```

### 주식 백테스팅 엔진

#### 1. Kiwoom 틱 백테스팅 (`backtester/backengine_kiwoom_tick.py`)
```python
class BackEngineKiwoomTick:
    """키움 틱 데이터 백테스팅 엔진"""
    
    def __init__(self):
        self.initial_balance = 10000000
        self.current_balance = self.initial_balance
        self.holdings = {}
        self.trade_history = []
        
        # 거래 설정
        self.commission_rate = 0.00015  # 키움 수수료 0.015%
        self.tax_rate = 0.0025          # 증권거래세 0.25% (매도시)
        
    def load_tick_data(self, symbol, start_date, end_date):
        """틱 데이터 로드"""
        query = """
        SELECT timestamp, current_price, volume, change_rate
        FROM stock_tick 
        WHERE code = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
        """
        
        return db_manager.execute_query(query, [symbol, start_date, end_date])
        
    def run_strategy_backtest(self, strategy_code, symbol, start_date, end_date):
        """전략 백테스팅 실행"""
        # 틱 데이터 로드
        tick_data = self.load_tick_data(symbol, start_date, end_date)
        
        # 전략 초기화
        strategy = self.initialize_strategy(strategy_code, symbol)
        
        # 틱별 시뮬레이션
        for tick in tick_data:
            timestamp, price, volume, change_rate = tick
            
            # 전략 신호 계산
            signal = strategy.process_tick({
                'timestamp': timestamp,
                'price': price,
                'volume': volume,
                'change_rate': change_rate
            })
            
            # 신호 실행
            if signal:
                self.execute_signal(signal, price, timestamp)
                
        return self.generate_backtest_report()
        
    def execute_signal(self, signal, price, timestamp):
        """신호 실행"""
        if signal['action'] == 'BUY':
            self.execute_buy_order(signal, price, timestamp)
        elif signal['action'] == 'SELL':
            self.execute_sell_order(signal, price, timestamp)
            
    def execute_buy_order(self, signal, price, timestamp):
        """매수 주문 실행"""
        symbol = signal['symbol']
        quantity = signal['quantity']
        
        # 매수 가능 여부 확인
        total_cost = price * quantity
        commission = total_cost * self.commission_rate
        
        if self.current_balance >= total_cost + commission:
            # 잔고 차감
            self.current_balance -= (total_cost + commission)
            
            # 보유 주식 업데이트
            if symbol in self.holdings:
                # 평균 단가 계산
                current_qty = self.holdings[symbol]['quantity']
                current_avg = self.holdings[symbol]['avg_price']
                
                new_qty = current_qty + quantity
                new_avg = ((current_avg * current_qty) + (price * quantity)) / new_qty
                
                self.holdings[symbol] = {
                    'quantity': new_qty,
                    'avg_price': new_avg
                }
            else:
                self.holdings[symbol] = {
                    'quantity': quantity,
                    'avg_price': price
                }
                
            # 거래 기록
            self.record_trade('BUY', symbol, quantity, price, commission, timestamp)
            
    def execute_sell_order(self, signal, price, timestamp):
        """매도 주문 실행"""
        symbol = signal['symbol']
        quantity = signal['quantity']
        
        # 보유 주식 확인
        if symbol in self.holdings and self.holdings[symbol]['quantity'] >= quantity:
            # 매도 대금 계산
            sell_amount = price * quantity
            commission = sell_amount * self.commission_rate
            tax = sell_amount * self.tax_rate
            
            net_amount = sell_amount - commission - tax
            
            # 잔고 증가
            self.current_balance += net_amount
            
            # 보유 주식 감소
            self.holdings[symbol]['quantity'] -= quantity
            
            if self.holdings[symbol]['quantity'] == 0:
                del self.holdings[symbol]
                
            # 거래 기록
            self.record_trade('SELL', symbol, quantity, price, commission + tax, timestamp)
```

### 암호화폐 백테스팅 엔진

#### 1. Upbit 백테스팅 (`backtester/backengine_upbit_tick.py`)
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

### 파라미터 최적화

#### 1. 그리드 서치 최적화
```python
class ParameterOptimizer:
    """파라미터 최적화기"""
    
    def __init__(self, backtest_engine):
        self.backtest_engine = backtest_engine
        
    def grid_search(self, strategy_class, data, parameter_grid):
        """그리드 서치 최적화"""
        results = []
        
        # 모든 파라미터 조합 생성
        param_combinations = self.generate_combinations(parameter_grid)
        
        for params in param_combinations:
            # 전략 인스턴스 생성
            strategy = strategy_class(**params)
            
            # 백테스팅 실행
            result = self.backtest_engine.run_backtest(strategy, data)
            
            # 결과 저장
            results.append({
                'parameters': params,
                'performance': result
            })
            
        # 최적 파라미터 선택
        best_result = max(results, key=lambda x: x['performance']['sharpe_ratio'])
        
        return best_result, results
        
    def generate_combinations(self, parameter_grid):
        """파라미터 조합 생성"""
        keys = list(parameter_grid.keys())
        values = list(parameter_grid.values())
        
        combinations = []
        for combination in itertools.product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)
            
        return combinations
        
    def walk_forward_optimization(self, strategy_class, data, parameter_grid, 
                                 train_period=252, test_period=63):
        """워크 포워드 최적화"""
        results = []
        
        for i in range(train_period, len(data) - test_period, test_period):
            # 훈련 데이터
            train_data = data[i-train_period:i]
            
            # 테스트 데이터
            test_data = data[i:i+test_period]
            
            # 훈련 기간에서 최적 파라미터 찾기
            best_params, _ = self.grid_search(strategy_class, train_data, parameter_grid)
            
            # 테스트 기간에서 성과 검증
            strategy = strategy_class(**best_params['parameters'])
            test_result = self.backtest_engine.run_backtest(strategy, test_data)
            
            results.append({
                'train_period': (i-train_period, i),
                'test_period': (i, i+test_period),
                'best_parameters': best_params['parameters'],
                'test_performance': test_result
            })
            
        return results
```

### 몬테카를로 시뮬레이션

#### 1. 몬테카를로 분석
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