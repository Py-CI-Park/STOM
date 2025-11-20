# 백테스터 모듈 (backtester/)

## 📋 개요

백테스터 모듈은 **과거 데이터를 이용한 전략 검증**과 **파라미터 최적화**를 수행하는 핵심 시스템입니다. 주식과 암호화폐 각각에 대해 틱/분봉 단위의 백테스팅을 지원하며, Optuna 기반 최적화 및 전진분석을 제공합니다.

---

## 🏗 모듈 구조

```
backtester/
├── backtest.py                      # 백테스트 메인 실행
├── optimiz.py                       # 파라미터 최적화
├── rolling_walk_forward_test.py    # 전진분석
├── backengine_kiwoom_tick.py        # 주식 틱 백테스트
├── backengine_kiwoom_min.py         # 주식 분봉 백테스트
├── backengine_upbit_tick.py         # 업비트 틱 백테스트
├── backengine_upbit_min.py          # 업비트 분봉 백테스트
├── backengine_binance_tick.py       # 바이낸스 틱 백테스트
├── backengine_binance_min.py        # 바이낸스 분봉 백테스트
└── performance_analyzer.py          # 성과 분석
```

---

## 🔬 백테스트 엔진

### 주식 틱 백테스트 (backengine_kiwoom_tick.py)

#### 엔진 구조
```python
class BackEngineKiwoomTick:
    """주식 틱 백테스트 엔진"""
    def __init__(self, strategy_code, start_date, end_date, initial_capital):
        # 전략 코드
        self.strategy_code = strategy_code
        self.strategy = None

        # 백테스트 기간
        self.start_date = start_date
        self.end_date = end_date

        # 초기 자본
        self.initial_capital = initial_capital
        self.cash = initial_capital

        # 거래 관리
        self.positions = {}          # 보유 포지션
        self.trades = []             # 거래 내역
        self.equity_curve = []       # 자산 곡선

        # 데이터베이스
        self.db_tick = DB_STOCK_TICK

    def run(self):
        """백테스트 실행"""
        # 1. 전략 로드
        self.load_strategy()

        # 2. 데이터 로드
        tick_data = self.load_tick_data()

        # 3. 시뮬레이션
        for tick in tick_data:
            self.process_tick(tick)

        # 4. 성과 분석
        results = self.analyze_performance()

        return results

    def load_tick_data(self):
        """틱 데이터 로드"""
        query = """
        SELECT code, timestamp, price, volume
        FROM tick_data
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp
        """
        con = sqlite3.connect(self.db_tick)
        df = pd.read_sql_query(
            query,
            con,
            params=(self.start_date, self.end_date)
        )
        con.close()
        return df

    def process_tick(self, tick):
        """틱 데이터 처리"""
        code = tick['code']
        price = tick['price']
        volume = tick['volume']
        timestamp = tick['timestamp']

        # 전략 실행
        signal = self.strategy.generate_signal(code, price, volume, timestamp)

        # 주문 처리
        if signal == 'BUY':
            self.execute_buy(code, price, timestamp)
        elif signal == 'SELL':
            self.execute_sell(code, price, timestamp)

        # 자산 평가
        self.update_equity(timestamp)

    def execute_buy(self, code, price, timestamp):
        """매수 실행"""
        # 매수 가능 수량 계산
        max_qty = int(self.cash / price)
        if max_qty <= 0:
            return

        # 포지션 크기 제한
        position_size = min(max_qty, self.get_max_position_size(price))

        # 매수 실행
        cost = price * position_size
        self.cash -= cost

        # 포지션 저장
        if code in self.positions:
            self.positions[code]['quantity'] += position_size
            self.positions[code]['avg_price'] = (
                (self.positions[code]['avg_price'] * self.positions[code]['quantity'] + cost) /
                (self.positions[code]['quantity'] + position_size)
            )
        else:
            self.positions[code] = {
                'quantity': position_size,
                'avg_price': price
            }

        # 거래 기록
        self.trades.append({
            'timestamp': timestamp,
            'code': code,
            'side': 'BUY',
            'price': price,
            'quantity': position_size,
            'amount': cost
        })

    def execute_sell(self, code, price, timestamp):
        """매도 실행"""
        if code not in self.positions:
            return

        # 전량 매도
        quantity = self.positions[code]['quantity']
        revenue = price * quantity
        self.cash += revenue

        # 수익 계산
        avg_price = self.positions[code]['avg_price']
        profit = (price - avg_price) * quantity
        profit_rate = (price / avg_price - 1) * 100

        # 포지션 삭제
        del self.positions[code]

        # 거래 기록
        self.trades.append({
            'timestamp': timestamp,
            'code': code,
            'side': 'SELL',
            'price': price,
            'quantity': quantity,
            'amount': revenue,
            'profit': profit,
            'profit_rate': profit_rate
        })

    def update_equity(self, timestamp):
        """자산 평가"""
        # 현금 + 보유 주식 평가액
        equity = self.cash

        for code, position in self.positions.items():
            current_price = self.get_current_price(code)
            equity += current_price * position['quantity']

        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': equity
        })
```

### 주식 분봉 백테스트 (backengine_kiwoom_min.py)

#### 캔들 데이터 처리
```python
class BackEngineKiwoomMin:
    """주식 분봉 백테스트 엔진"""
    def __init__(self, strategy_code, start_date, end_date, initial_capital):
        # 초기화 (틱 엔진과 동일)
        pass

    def load_candle_data(self):
        """분봉 데이터 로드"""
        query = """
        SELECT code, timestamp, open, high, low, close, volume
        FROM candle_data
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp
        """
        con = sqlite3.connect(DB_STOCK_MIN)
        df = pd.read_sql_query(
            query,
            con,
            params=(self.start_date, self.end_date)
        )
        con.close()
        return df

    def process_candle(self, candle):
        """캔들 데이터 처리"""
        code = candle['code']
        timestamp = candle['timestamp']
        ohlcv = {
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close'],
            'volume': candle['volume']
        }

        # 전략 실행 (종가 기준)
        signal = self.strategy.generate_signal(code, ohlcv, timestamp)

        # 주문 처리 (다음 캔들 시가에 체결)
        if signal == 'BUY':
            self.pending_orders.append({
                'code': code,
                'side': 'BUY',
                'timestamp': timestamp
            })
        elif signal == 'SELL':
            self.pending_orders.append({
                'code': code,
                'side': 'SELL',
                'timestamp': timestamp
            })

    def execute_pending_orders(self, next_candle):
        """대기 중인 주문 실행 (다음 캔들 시가)"""
        for order in self.pending_orders:
            code = order['code']
            side = order['side']
            price = next_candle['open']  # 다음 캔들 시가

            if side == 'BUY':
                self.execute_buy(code, price, next_candle['timestamp'])
            elif side == 'SELL':
                self.execute_sell(code, price, next_candle['timestamp'])

        self.pending_orders.clear()
```

---

## 🪙 암호화폐 백테스트 엔진

### 업비트 틱 백테스트 (backengine_upbit_tick.py)

#### 수수료 및 슬리피지 반영
```python
class BackEngineUpbitTick:
    """업비트 틱 백테스트 엔진"""
    def __init__(self, strategy_code, start_date, end_date, initial_capital):
        # 기본 초기화
        self.initial_capital = initial_capital
        self.cash = initial_capital

        # 업비트 수수료 (0.05%)
        self.fee_rate = 0.0005

        # 슬리피지
        self.slippage = 0.001  # 0.1%

    def execute_buy_with_fee(self, market, price, timestamp):
        """수수료 및 슬리피지를 고려한 매수"""
        # 슬리피지 적용
        actual_price = price * (1 + self.slippage)

        # 매수 가능 금액 (최소 주문 5,000원)
        if self.cash < 5000:
            return

        # 수수료를 고려한 매수 수량
        max_amount = self.cash
        quantity = max_amount / (actual_price * (1 + self.fee_rate))

        # 주문 금액
        order_amount = actual_price * quantity
        fee = order_amount * self.fee_rate
        total_cost = order_amount + fee

        # 잔고 부족 체크
        if total_cost > self.cash:
            return

        # 매수 실행
        self.cash -= total_cost

        # 포지션 저장
        if market in self.positions:
            old_qty = self.positions[market]['quantity']
            old_price = self.positions[market]['avg_price']
            new_qty = old_qty + quantity
            new_avg_price = ((old_price * old_qty) + (actual_price * quantity)) / new_qty

            self.positions[market]['quantity'] = new_qty
            self.positions[market]['avg_price'] = new_avg_price
        else:
            self.positions[market] = {
                'quantity': quantity,
                'avg_price': actual_price
            }

        # 거래 기록
        self.trades.append({
            'timestamp': timestamp,
            'market': market,
            'side': 'BUY',
            'price': actual_price,
            'quantity': quantity,
            'fee': fee,
            'amount': order_amount
        })

    def execute_sell_with_fee(self, market, price, timestamp):
        """수수료 및 슬리피지를 고려한 매도"""
        if market not in self.positions:
            return

        # 슬리피지 적용
        actual_price = price * (1 - self.slippage)

        # 전량 매도
        quantity = self.positions[market]['quantity']
        revenue = actual_price * quantity
        fee = revenue * self.fee_rate
        net_revenue = revenue - fee

        # 매도 실행
        self.cash += net_revenue

        # 수익 계산
        avg_price = self.positions[market]['avg_price']
        profit = (actual_price - avg_price) * quantity - fee
        profit_rate = (actual_price / avg_price - 1) * 100

        # 포지션 삭제
        del self.positions[market]

        # 거래 기록
        self.trades.append({
            'timestamp': timestamp,
            'market': market,
            'side': 'SELL',
            'price': actual_price,
            'quantity': quantity,
            'fee': fee,
            'amount': revenue,
            'profit': profit,
            'profit_rate': profit_rate
        })
```

---

## 🎯 파라미터 최적화 (optimiz.py)

### Optuna 기반 최적화

```python
import optuna
from optuna.samplers import TPESampler

class StrategyOptimizer:
    """전략 파라미터 최적화"""
    def __init__(self, engine_class, data_range):
        self.engine_class = engine_class
        self.data_range = data_range

    def objective(self, trial):
        """목적 함수 (Sharpe Ratio 최대화)"""
        # 파라미터 제안
        params = {
            'ma_short': trial.suggest_int('ma_short', 3, 10),
            'ma_long': trial.suggest_int('ma_long', 15, 30),
            'rsi_period': trial.suggest_int('rsi_period', 10, 20),
            'rsi_oversold': trial.suggest_int('rsi_oversold', 20, 35),
            'rsi_overbought': trial.suggest_int('rsi_overbought', 65, 80),
        }

        # 백테스트 실행
        engine = self.engine_class(
            strategy_code=self.create_strategy_code(params),
            start_date=self.data_range['start'],
            end_date=self.data_range['end'],
            initial_capital=10000000
        )
        results = engine.run()

        # Sharpe Ratio 반환
        return results['sharpe_ratio']

    def optimize(self, n_trials=100):
        """최적화 실행"""
        study = optuna.create_study(
            direction='maximize',
            sampler=TPESampler(),
            storage=f'sqlite:///{DB_OPTUNA}',
            study_name='strategy_optimization'
        )

        study.optimize(self.objective, n_trials=n_trials)

        # 최적 파라미터
        best_params = study.best_params
        best_value = study.best_value

        print(f"최적 파라미터: {best_params}")
        print(f"Sharpe Ratio: {best_value:.4f}")

        return best_params

    def create_strategy_code(self, params):
        """파라미터로 전략 코드 생성"""
        strategy_template = f"""
def Strategy(code, price, volume, timestamp):
    ma_short = SMA(price_data, {params['ma_short']})
    ma_long = SMA(price_data, {params['ma_long']})
    rsi = RSI(price_data, {params['rsi_period']})

    if ma_short > ma_long and rsi < {params['rsi_oversold']}:
        return 'BUY'
    elif ma_short < ma_long and rsi > {params['rsi_overbought']}:
        return 'SELL'
    else:
        return 'HOLD'
"""
        return strategy_template
```

---

## 📊 전진분석 (rolling_walk_forward_test.py)

### Walk Forward 검증

```python
class WalkForwardTest:
    """전진분석 테스트"""
    def __init__(self, engine_class, total_period, train_period, test_period):
        self.engine_class = engine_class
        self.total_period = total_period
        self.train_period = train_period  # 학습 기간 (예: 6개월)
        self.test_period = test_period    # 검증 기간 (예: 1개월)

    def run_walk_forward(self):
        """전진분석 실행"""
        results = []

        # 시작일부터 종료일까지 슬라이딩 윈도우
        current_date = self.total_period['start']
        while current_date < self.total_period['end']:
            # 학습 기간
            train_start = current_date
            train_end = self.add_months(current_date, self.train_period)

            # 검증 기간
            test_start = train_end
            test_end = self.add_months(test_start, self.test_period)

            # 학습 기간에서 최적화
            optimizer = StrategyOptimizer(
                self.engine_class,
                {'start': train_start, 'end': train_end}
            )
            best_params = optimizer.optimize(n_trials=50)

            # 검증 기간에서 백테스트
            engine = self.engine_class(
                strategy_code=self.create_strategy(best_params),
                start_date=test_start,
                end_date=test_end,
                initial_capital=10000000
            )
            test_results = engine.run()

            results.append({
                'train_period': (train_start, train_end),
                'test_period': (test_start, test_end),
                'best_params': best_params,
                'test_results': test_results
            })

            # 다음 윈도우로 이동
            current_date = self.add_months(current_date, self.test_period)

        return results

    def analyze_walk_forward_results(self, results):
        """전진분석 결과 분석"""
        # 각 검증 기간의 성과 집계
        total_return = 1.0
        sharpe_ratios = []
        max_drawdowns = []

        for result in results:
            test_results = result['test_results']
            total_return *= (1 + test_results['total_return'])
            sharpe_ratios.append(test_results['sharpe_ratio'])
            max_drawdowns.append(test_results['max_drawdown'])

        # 종합 성과
        final_results = {
            'total_return': (total_return - 1) * 100,
            'avg_sharpe_ratio': np.mean(sharpe_ratios),
            'avg_max_drawdown': np.mean(max_drawdowns),
            'stability': np.std(sharpe_ratios),  # 낮을수록 안정적
        }

        return final_results
```

---

## 📈 성과 분석 (performance_analyzer.py)

### 성과 지표 계산

```python
import numpy as np
import pandas as pd

class PerformanceAnalyzer:
    """성과 분석"""
    def __init__(self, trades, equity_curve):
        self.trades = pd.DataFrame(trades)
        self.equity_curve = pd.DataFrame(equity_curve)

    def calculate_all_metrics(self):
        """모든 성과 지표 계산"""
        metrics = {
            # 수익률
            'total_return': self.calculate_total_return(),
            'annual_return': self.calculate_annual_return(),

            # 리스크
            'volatility': self.calculate_volatility(),
            'max_drawdown': self.calculate_max_drawdown(),

            # 위험 조정 수익률
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),

            # 거래 통계
            'win_rate': self.calculate_win_rate(),
            'profit_factor': self.calculate_profit_factor(),
            'avg_win': self.calculate_avg_win(),
            'avg_loss': self.calculate_avg_loss(),

            # 기타
            'total_trades': len(self.trades),
            'avg_trade_duration': self.calculate_avg_trade_duration(),
        }

        return metrics

    def calculate_total_return(self):
        """총 수익률"""
        initial_equity = self.equity_curve.iloc[0]['equity']
        final_equity = self.equity_curve.iloc[-1]['equity']
        return ((final_equity / initial_equity) - 1) * 100

    def calculate_max_drawdown(self):
        """최대 낙폭 (MDD)"""
        equity = self.equity_curve['equity']
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax * 100
        return drawdown.min()

    def calculate_sharpe_ratio(self, risk_free_rate=0.02):
        """샤프 비율"""
        # 일간 수익률
        equity = self.equity_curve['equity']
        daily_returns = equity.pct_change().dropna()

        # 초과 수익률
        excess_returns = daily_returns - (risk_free_rate / 252)

        # Sharpe Ratio
        if excess_returns.std() == 0:
            return 0
        sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        return sharpe

    def calculate_sortino_ratio(self, risk_free_rate=0.02):
        """소르티노 비율"""
        equity = self.equity_curve['equity']
        daily_returns = equity.pct_change().dropna()

        # 초과 수익률
        excess_returns = daily_returns - (risk_free_rate / 252)

        # 하방 편차
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = downside_returns.std()

        if downside_std == 0:
            return 0
        sortino = excess_returns.mean() / downside_std * np.sqrt(252)
        return sortino

    def calculate_win_rate(self):
        """승률"""
        sell_trades = self.trades[self.trades['side'] == 'SELL']
        if len(sell_trades) == 0:
            return 0
        wins = len(sell_trades[sell_trades['profit'] > 0])
        return (wins / len(sell_trades)) * 100

    def calculate_profit_factor(self):
        """수익 팩터"""
        sell_trades = self.trades[self.trades['side'] == 'SELL']
        total_profit = sell_trades[sell_trades['profit'] > 0]['profit'].sum()
        total_loss = abs(sell_trades[sell_trades['profit'] < 0]['profit'].sum())

        if total_loss == 0:
            return 0
        return total_profit / total_loss

    def plot_equity_curve(self):
        """자산 곡선 그래프"""
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 6))
        plt.plot(self.equity_curve['timestamp'], self.equity_curve['equity'])
        plt.title('Equity Curve')
        plt.xlabel('Date')
        plt.ylabel('Equity')
        plt.grid(True)
        plt.show()

    def plot_drawdown(self):
        """낙폭 그래프"""
        import matplotlib.pyplot as plt

        equity = self.equity_curve['equity']
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax * 100

        plt.figure(figsize=(12, 4))
        plt.fill_between(
            self.equity_curve['timestamp'],
            0,
            drawdown,
            color='red',
            alpha=0.3
        )
        plt.title('Drawdown')
        plt.xlabel('Date')
        plt.ylabel('Drawdown (%)')
        plt.grid(True)
        plt.show()
```

---

## 🚀 백테스트 실행

### 메인 실행 파일 (backtest.py)

```python
def main():
    """백테스트 메인 함수"""
    # 백테스트 설정
    config = {
        'engine': BackEngineKiwoomTick,
        'strategy': 'RSI_MA_Strategy',
        'start_date': '20240101',
        'end_date': '20241231',
        'initial_capital': 10000000,
    }

    # 백테스트 실행
    print("백테스트 시작...")
    engine = config['engine'](
        strategy_code=config['strategy'],
        start_date=config['start_date'],
        end_date=config['end_date'],
        initial_capital=config['initial_capital']
    )
    results = engine.run()

    # 성과 분석
    analyzer = PerformanceAnalyzer(engine.trades, engine.equity_curve)
    metrics = analyzer.calculate_all_metrics()

    # 결과 출력
    print("\n" + "=" * 50)
    print("백테스트 결과")
    print("=" * 50)
    print(f"총 수익률: {metrics['total_return']:.2f}%")
    print(f"연간 수익률: {metrics['annual_return']:.2f}%")
    print(f"최대 낙폭: {metrics['max_drawdown']:.2f}%")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
    print(f"승률: {metrics['win_rate']:.2f}%")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"총 거래 수: {metrics['total_trades']}")
    print("=" * 50)

    # 그래프 출력
    analyzer.plot_equity_curve()
    analyzer.plot_drawdown()

if __name__ == '__main__':
    main()
```

---

*다음: [API 통합](../04_API/api_integration.md)*
*이전: [유틸리티 모듈](utility_module.md)*
