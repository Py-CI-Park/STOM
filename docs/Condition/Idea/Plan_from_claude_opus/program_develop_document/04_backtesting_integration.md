# 백테스팅 통합 가이드

## 1. 백테스팅 엔진 아키텍처

### 1.1 시스템 구성도
```
ML/DL Models → Signal Generator → Order Manager → Position Manager → Performance Tracker
                                         ↓                ↓                    ↓
                                   Risk Manager    Portfolio Manager    Metrics Calculator
                                         ↓                ↓                    ↓
                                   STOM System    Database Logger      Report Generator
```

## 2. 백테스팅 엔진 구현

### 2.1 핵심 백테스팅 엔진

```python
# backtesting/engine.py
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class Order:
    """주문 정보"""
    timestamp: datetime
    stock_code: str
    order_type: str  # 'buy' or 'sell'
    price: float
    quantity: int
    commission: float = 0.00015  # 0.015%
    tax: float = 0.0023  # 0.23% (매도시)

@dataclass
class Position:
    """포지션 정보"""
    stock_code: str
    entry_time: datetime
    entry_price: float
    quantity: int
    current_price: float
    holding_period: int = 0
    peak_price: float = 0
    
    @property
    def current_value(self) -> float:
        return self.current_price * self.quantity
    
    @property
    def profit_loss(self) -> float:
        return (self.current_price - self.entry_price) * self.quantity
    
    @property
    def profit_loss_pct(self) -> float:
        return (self.current_price / self.entry_price - 1) * 100
    
    @property
    def peak_profit_pct(self) -> float:
        return (self.peak_price / self.entry_price - 1) * 100

class BacktestEngine:
    """백테스팅 엔진"""
    
    def __init__(
        self,
        initial_capital: float = 10_000_000,
        max_positions: int = 10,
        position_size: float = 0.1,  # 자본의 10%
        stop_loss: float = -3.0,  # -3% 손절
        take_profit: float = 5.0,  # 5% 익절
        trailing_stop: float = 2.0,  # 2% 트레일링 스탑
        commission: float = 0.00015,
        tax: float = 0.0023
    ):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_positions = max_positions
        self.position_size = position_size
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop = trailing_stop
        self.commission = commission
        self.tax = tax
        
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.orders: List[Order] = []
        self.equity_curve: List[float] = [initial_capital]
        self.trades_log: List[Dict] = []
        
        self.logger = logging.getLogger(__name__)
    
    def calculate_position_size(self, price: float) -> int:
        """포지션 크기 계산"""
        available_capital = self.current_capital * self.position_size
        max_shares = int(available_capital / price)
        
        # 최소 거래 단위 고려
        if max_shares < 1:
            return 0
        
        return max_shares
    
    def can_buy(self) -> bool:
        """매수 가능 여부"""
        return len(self.positions) < self.max_positions
    
    def execute_buy(
        self,
        timestamp: datetime,
        stock_code: str,
        price: float,
        signal_strength: float = 1.0
    ) -> bool:
        """매수 실행"""
        if not self.can_buy():
            return False
        
        if stock_code in self.positions:
            return False  # 이미 보유 중
        
        # 포지션 크기 계산
        quantity = self.calculate_position_size(price)
        if quantity == 0:
            return False
        
        # 거래 비용 계산
        cost = price * quantity
        commission_cost = cost * self.commission
        total_cost = cost + commission_cost
        
        if total_cost > self.current_capital:
            # 자본 부족시 수량 조정
            quantity = int((self.current_capital - commission_cost) / price)
            if quantity < 1:
                return False
            cost = price * quantity
            commission_cost = cost * self.commission
            total_cost = cost + commission_cost
        
        # 주문 실행
        self.current_capital -= total_cost
        
        position = Position(
            stock_code=stock_code,
            entry_time=timestamp,
            entry_price=price,
            quantity=quantity,
            current_price=price,
            peak_price=price
        )
        
        self.positions[stock_code] = position
        
        order = Order(
            timestamp=timestamp,
            stock_code=stock_code,
            order_type='buy',
            price=price,
            quantity=quantity,
            commission=commission_cost
        )
        
        self.orders.append(order)
        
        self.logger.info(
            f"BUY: {stock_code} - {quantity}주 @ {price:,.0f}원 "
            f"(비용: {total_cost:,.0f}원, 신호강도: {signal_strength:.2f})"
        )
        
        return True
    
    def execute_sell(
        self,
        timestamp: datetime,
        stock_code: str,
        price: float,
        reason: str = 'signal'
    ) -> bool:
        """매도 실행"""
        if stock_code not in self.positions:
            return False
        
        position = self.positions[stock_code]
        
        # 거래 비용 계산
        revenue = price * position.quantity
        commission_cost = revenue * self.commission
        tax_cost = revenue * self.tax
        total_cost = commission_cost + tax_cost
        net_revenue = revenue - total_cost
        
        # 자본 업데이트
        self.current_capital += net_revenue
        
        # 거래 기록
        profit_loss = net_revenue - (position.entry_price * position.quantity * (1 + self.commission))
        profit_loss_pct = (profit_loss / (position.entry_price * position.quantity)) * 100
        
        trade_log = {
            'timestamp': timestamp,
            'stock_code': stock_code,
            'entry_time': position.entry_time,
            'exit_time': timestamp,
            'entry_price': position.entry_price,
            'exit_price': price,
            'quantity': position.quantity,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct,
            'holding_period': position.holding_period,
            'reason': reason
        }
        
        self.trades_log.append(trade_log)
        
        # 포지션 제거
        position.current_price = price
        self.closed_positions.append(position)
        del self.positions[stock_code]
        
        order = Order(
            timestamp=timestamp,
            stock_code=stock_code,
            order_type='sell',
            price=price,
            quantity=position.quantity,
            commission=total_cost
        )
        
        self.orders.append(order)
        
        self.logger.info(
            f"SELL: {stock_code} - {position.quantity}주 @ {price:,.0f}원 "
            f"(수익: {profit_loss:,.0f}원, {profit_loss_pct:.2f}%, 사유: {reason})"
        )
        
        return True
    
    def update_positions(self, timestamp: datetime, price_data: Dict[str, float]):
        """포지션 업데이트 및 리스크 관리"""
        for stock_code, position in list(self.positions.items()):
            if stock_code not in price_data:
                continue
            
            current_price = price_data[stock_code]
            position.current_price = current_price
            position.holding_period += 1
            
            # Peak price 업데이트
            if current_price > position.peak_price:
                position.peak_price = current_price
            
            # 손절매
            if position.profit_loss_pct <= self.stop_loss:
                self.execute_sell(timestamp, stock_code, current_price, reason='stop_loss')
                continue
            
            # 익절매
            if position.profit_loss_pct >= self.take_profit:
                self.execute_sell(timestamp, stock_code, current_price, reason='take_profit')
                continue
            
            # 트레일링 스탑
            if position.peak_profit_pct > 3.0:  # 3% 이상 상승한 경우
                trailing_stop_price = position.peak_price * (1 - self.trailing_stop / 100)
                if current_price <= trailing_stop_price:
                    self.execute_sell(timestamp, stock_code, current_price, reason='trailing_stop')
    
    def calculate_portfolio_value(self, price_data: Dict[str, float]) -> float:
        """포트폴리오 가치 계산"""
        positions_value = sum(
            position.quantity * price_data.get(stock_code, position.current_price)
            for stock_code, position in self.positions.items()
        )
        return self.current_capital + positions_value
    
    def get_performance_metrics(self) -> Dict:
        """성과 지표 계산"""
        if not self.trades_log:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        trades_df = pd.DataFrame(self.trades_log)
        
        # 기본 통계
        winning_trades = trades_df[trades_df['profit_loss'] > 0]
        losing_trades = trades_df[trades_df['profit_loss'] <= 0]
        
        total_trades = len(trades_df)
        num_winning = len(winning_trades)
        num_losing = len(losing_trades)
        
        # 승률
        win_rate = num_winning / total_trades if total_trades > 0 else 0
        
        # 평균 수익/손실
        avg_profit = winning_trades['profit_loss'].mean() if num_winning > 0 else 0
        avg_loss = losing_trades['profit_loss'].mean() if num_losing > 0 else 0
        
        # Profit Factor
        total_profit = winning_trades['profit_loss'].sum() if num_winning > 0 else 0
        total_loss = abs(losing_trades['profit_loss'].sum()) if num_losing > 0 else 1
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        # 총 수익률
        final_value = self.calculate_portfolio_value({})
        total_return = (final_value / self.initial_capital - 1) * 100
        
        # 샤프 비율
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        # 최대 낙폭
        equity_series = pd.Series(self.equity_curve)
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax * 100
        max_drawdown = drawdown.min()
        
        return {
            'total_trades': total_trades,
            'winning_trades': num_winning,
            'losing_trades': num_losing,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_holding_period': trades_df['holding_period'].mean() if total_trades > 0 else 0
        }
```

### 2.2 신호 생성기

```python
# backtesting/signal_generator.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

class SignalGenerator:
    """ML/DL 모델 기반 신호 생성"""
    
    def __init__(self, models: Dict, thresholds: Dict = None):
        """
        Args:
            models: 예측 모델 딕셔너리
            thresholds: 신호 임계값 딕셔너리
        """
        self.models = models
        self.thresholds = thresholds or {
            'buy': 0.6,
            'sell': 0.4,
            'strong_buy': 0.8,
            'strong_sell': 0.2
        }
    
    def generate_signals(
        self,
        features: pd.DataFrame,
        method: str = 'ensemble'
    ) -> pd.DataFrame:
        """
        거래 신호 생성
        
        Args:
            features: 특성 데이터
            method: 'ensemble', 'lightgbm', 'lstm'
            
        Returns:
            신호 DataFrame (buy_signal, sell_signal, signal_strength)
        """
        signals = pd.DataFrame(index=features.index)
        
        if method == 'ensemble':
            # 앙상블 예측
            predictions = self._ensemble_predict(features)
        else:
            # 단일 모델 예측
            model = self.models.get(method)
            if model is None:
                raise ValueError(f"Model {method} not found")
            predictions = model.predict_proba(features)[:, 1]
        
        # 신호 생성
        signals['prediction'] = predictions
        signals['buy_signal'] = predictions > self.thresholds['buy']
        signals['sell_signal'] = predictions < self.thresholds['sell']
        signals['strong_buy'] = predictions > self.thresholds['strong_buy']
        signals['strong_sell'] = predictions < self.thresholds['strong_sell']
        signals['signal_strength'] = predictions
        
        # 신호 평활화 (노이즈 제거)
        signals = self._smooth_signals(signals)
        
        return signals
    
    def _ensemble_predict(self, features: pd.DataFrame) -> np.ndarray:
        """앙상블 예측"""
        predictions = []
        weights = {'lightgbm': 0.5, 'lstm': 0.3, 'xgboost': 0.2}
        
        for name, model in self.models.items():
            if name in weights:
                pred = model.predict_proba(features)
                if len(pred.shape) > 1:
                    pred = pred[:, 1]
                predictions.append(pred * weights[name])
        
        return np.sum(predictions, axis=0)
    
    def _smooth_signals(self, signals: pd.DataFrame, window: int = 3) -> pd.DataFrame:
        """신호 평활화"""
        # 이동평균으로 노이즈 제거
        signals['signal_strength_smooth'] = (
            signals['signal_strength'].rolling(window=window, min_periods=1).mean()
        )
        
        # 연속된 신호만 유지
        signals['buy_signal_filtered'] = (
            signals['buy_signal'].rolling(window=2, min_periods=1).sum() >= 2
        )
        signals['sell_signal_filtered'] = (
            signals['sell_signal'].rolling(window=2, min_periods=1).sum() >= 2
        )
        
        return signals
```

## 3. STOM 시스템 통합

### 3.1 STOM 조건식 변환기

```python
# backtesting/stom_converter.py
import re
from typing import Dict, List

class STOMConditionConverter:
    """STOM 조건식을 Python 함수로 변환"""
    
    def __init__(self):
        self.variable_mapping = {
            '현재가': 'current_price',
            '시가': 'open_price',
            '고가': 'high_price',
            '저가': 'low_price',
            '등락율': 'change_rate',
            '체결강도': 'volume_power',
            '초당거래대금': 'volume_per_sec',
            '매도총잔량': 'ask_volume',
            '매수총잔량': 'bid_volume'
        }
    
    def convert_condition(self, stom_condition: str) -> str:
        """
        STOM 조건식을 Python 코드로 변환
        
        Args:
            stom_condition: STOM 조건식 문자열
            
        Returns:
            Python 함수 문자열
        """
        # 변수명 변환
        python_code = stom_condition
        for stom_var, python_var in self.variable_mapping.items():
            python_code = python_code.replace(stom_var, f"df['{python_var}']")
        
        # N(x) 형식 변환 (이전 틱 참조)
        python_code = re.sub(
            r"df\['(\w+)'\]N\((\d+)\)",
            r"df['\1'].shift(\2)",
            python_code
        )
        
        # 구간 함수 변환
        python_code = self._convert_range_functions(python_code)
        
        return python_code
    
    def _convert_range_functions(self, code: str) -> str:
        """구간 함수 변환"""
        # 이동평균(x) -> rolling(x).mean()
        code = re.sub(
            r"이동평균\((\d+)\)",
            r"df['current_price'].rolling(\1).mean()",
            code
        )
        
        # 최고현재가(x) -> rolling(x).max()
        code = re.sub(
            r"최고현재가\((\d+)\)",
            r"df['current_price'].rolling(\1).max()",
            code
        )
        
        # 체결강도평균(x) -> rolling(x).mean()
        code = re.sub(
            r"체결강도평균\((\d+)\)",
            r"df['volume_power'].rolling(\1).mean()",
            code
        )
        
        return code
    
    def create_strategy_function(
        self,
        buy_condition: str,
        sell_condition: str
    ) -> callable:
        """전략 함수 생성"""
        buy_code = self.convert_condition(buy_condition)
        sell_code = self.convert_condition(sell_condition)
        
        func_str = f"""
def strategy(df):
    buy_signal = {buy_code}
    sell_signal = {sell_code}
    return buy_signal, sell_signal
"""
        
        # 함수 실행
        exec_globals = {}
        exec(func_str, exec_globals)
        
        return exec_globals['strategy']
```

### 3.2 실시간 백테스팅 시뮬레이터

```python
# backtesting/simulator.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

class RealtimeSimulator:
    """실시간 백테스팅 시뮬레이터"""
    
    def __init__(
        self,
        engine: 'BacktestEngine',
        signal_generator: 'SignalGenerator',
        data_pipeline: 'DataPipeline'
    ):
        self.engine = engine
        self.signal_generator = signal_generator
        self.data_pipeline = data_pipeline
        self.is_running = False
    
    def simulate(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        tick_interval: int = 1,  # 초
        speed_multiplier: float = 60.0  # 60배속
    ):
        """
        실시간 시뮬레이션
        
        Args:
            stock_codes: 종목 코드 리스트
            start_date: 시작 날짜
            end_date: 종료 날짜
            tick_interval: 틱 간격 (초)
            speed_multiplier: 재생 속도 배수
        """
        print("=" * 60)
        print("실시간 백테스팅 시뮬레이션 시작")
        print("=" * 60)
        
        # 데이터 로드
        all_data = {}
        for code in stock_codes:
            df = self.data_pipeline.db_connector.load_stock_data(
                code, start_date, end_date
            )
            all_data[code] = df
        
        # 시간 인덱스 생성
        all_timestamps = sorted(set(
            timestamp 
            for df in all_data.values() 
            for timestamp in df.index
        ))
        
        self.is_running = True
        portfolio_values = []
        
        for i, timestamp in enumerate(all_timestamps):
            if not self.is_running:
                break
            
            # 현재 시점 데이터
            current_data = {}
            current_features = {}
            
            for code in stock_codes:
                if timestamp in all_data[code].index:
                    # 현재까지의 데이터
                    historical = all_data[code].loc[:timestamp]
                    
                    if len(historical) > 100:  # 최소 데이터 요구
                        # 특성 생성
                        features = self.data_pipeline.feature_engineer.create_all_features(
                            historical.tail(200)
                        )
                        
                        if not features.empty:
                            current_features[code] = features.iloc[-1:]
                            current_data[code] = historical.iloc[-1]['현재가']
            
            # 신호 생성
            for code, features in current_features.items():
                signals = self.signal_generator.generate_signals(features)
                
                if not signals.empty:
                    signal = signals.iloc[-1]
                    
                    # 매수 신호
                    if signal['buy_signal'] and code not in self.engine.positions:
                        self.engine.execute_buy(
                            timestamp,
                            code,
                            current_data[code],
                            signal['signal_strength']
                        )
                    
                    # 매도 신호
                    elif signal['sell_signal'] and code in self.engine.positions:
                        self.engine.execute_sell(
                            timestamp,
                            code,
                            current_data[code],
                            reason='signal'
                        )
            
            # 포지션 업데이트
            self.engine.update_positions(timestamp, current_data)
            
            # 포트폴리오 가치 기록
            portfolio_value = self.engine.calculate_portfolio_value(current_data)
            portfolio_values.append(portfolio_value)
            self.engine.equity_curve.append(portfolio_value)
            
            # 진행 상황 출력 (10% 단위)
            if i % max(1, len(all_timestamps) // 10) == 0:
                progress = (i / len(all_timestamps)) * 100
                print(f"진행률: {progress:.1f}% - "
                      f"포트폴리오: {portfolio_value:,.0f}원 - "
                      f"포지션: {len(self.engine.positions)}개")
            
            # 속도 조절 (실시간 시뮬레이션)
            if speed_multiplier > 0:
                time.sleep(tick_interval / speed_multiplier)
        
        print("\n시뮬레이션 완료!")
        return portfolio_values
```

## 4. 성과 평가 및 리포팅

### 4.1 성과 분석기

```python
# backtesting/performance_analyzer.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class PerformanceAnalyzer:
    """백테스팅 성과 분석"""
    
    def __init__(self, engine: 'BacktestEngine'):
        self.engine = engine
        self.trades_df = pd.DataFrame(engine.trades_log) if engine.trades_log else pd.DataFrame()
    
    def generate_report(self) -> Dict:
        """종합 리포트 생성"""
        metrics = self.engine.get_performance_metrics()
        
        report = {
            '기본 통계': self._get_basic_stats(),
            '수익성 지표': self._get_profitability_metrics(),
            '리스크 지표': self._get_risk_metrics(),
            '거래 분석': self._get_trade_analysis(),
            '월별 성과': self._get_monthly_performance()
        }
        
        return report
    
    def _get_basic_stats(self) -> Dict:
        """기본 통계"""
        if self.trades_df.empty:
            return {}
        
        return {
            '총 거래 횟수': len(self.trades_df),
            '평균 보유 기간': f"{self.trades_df['holding_period'].mean():.1f} 틱",
            '최대 보유 기간': f"{self.trades_df['holding_period'].max()} 틱",
            '최소 보유 기간': f"{self.trades_df['holding_period'].min()} 틱",
            '거래 종목 수': self.trades_df['stock_code'].nunique()
        }
    
    def _get_profitability_metrics(self) -> Dict:
        """수익성 지표"""
        metrics = self.engine.get_performance_metrics()
        
        return {
            '총 수익률': f"{metrics['total_return']:.2f}%",
            '승률': f"{metrics['win_rate']*100:.1f}%",
            '평균 수익': f"{metrics['avg_profit']:,.0f}원",
            '평균 손실': f"{metrics['avg_loss']:,.0f}원",
            'Profit Factor': f"{metrics['profit_factor']:.2f}"
        }
    
    def _get_risk_metrics(self) -> Dict:
        """리스크 지표"""
        metrics = self.engine.get_performance_metrics()
        equity_curve = pd.Series(self.engine.equity_curve)
        
        # 일별 수익률
        daily_returns = equity_curve.pct_change().dropna()
        
        # Sortino Ratio
        downside_returns = daily_returns[daily_returns < 0]
        sortino_ratio = (daily_returns.mean() / downside_returns.std() * np.sqrt(252) 
                        if len(downside_returns) > 0 else 0)
        
        # Calmar Ratio
        calmar_ratio = (metrics['total_return'] / abs(metrics['max_drawdown']) 
                       if metrics['max_drawdown'] != 0 else 0)
        
        return {
            '최대 낙폭': f"{metrics['max_drawdown']:.2f}%",
            '샤프 비율': f"{metrics['sharpe_ratio']:.2f}",
            'Sortino 비율': f"{sortino_ratio:.2f}",
            'Calmar 비율': f"{calmar_ratio:.2f}",
            '일 변동성': f"{daily_returns.std()*100:.2f}%"
        }
    
    def _get_trade_analysis(self) -> Dict:
        """거래 분석"""
        if self.trades_df.empty:
            return {}
        
        # 거래 사유별 분석
        reason_analysis = self.trades_df.groupby('reason').agg({
            'profit_loss': ['count', 'sum', 'mean'],
            'profit_loss_pct': 'mean'
        }).round(2)
        
        # 최고/최저 거래
        best_trade = self.trades_df.loc[self.trades_df['profit_loss'].idxmax()]
        worst_trade = self.trades_df.loc[self.trades_df['profit_loss'].idxmin()]
        
        return {
            '거래 사유별 분석': reason_analysis.to_dict(),
            '최고 수익 거래': {
                '종목': best_trade['stock_code'],
                '수익': f"{best_trade['profit_loss']:,.0f}원",
                '수익률': f"{best_trade['profit_loss_pct']:.2f}%"
            },
            '최대 손실 거래': {
                '종목': worst_trade['stock_code'],
                '손실': f"{worst_trade['profit_loss']:,.0f}원",
                '손실률': f"{worst_trade['profit_loss_pct']:.2f}%"
            }
        }
    
    def _get_monthly_performance(self) -> pd.DataFrame:
        """월별 성과"""
        if self.trades_df.empty:
            return pd.DataFrame()
        
        trades = self.trades_df.copy()
        trades['month'] = pd.to_datetime(trades['exit_time']).dt.to_period('M')
        
        monthly = trades.groupby('month').agg({
            'profit_loss': 'sum',
            'profit_loss_pct': 'mean',
            'stock_code': 'count'
        }).rename(columns={
            'profit_loss': '월 수익',
            'profit_loss_pct': '평균 수익률',
            'stock_code': '거래 횟수'
        })
        
        return monthly
    
    def plot_performance(self):
        """성과 차트 생성"""
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                '자산 곡선', '일별 수익률',
                '거래 분포', '수익률 분포',
                '월별 성과', '낙폭 차트'
            )
        )
        
        # 1. 자산 곡선
        equity_curve = pd.Series(self.engine.equity_curve)
        fig.add_trace(
            go.Scatter(y=equity_curve, mode='lines', name='Portfolio Value'),
            row=1, col=1
        )
        
        # 2. 일별 수익률
        daily_returns = equity_curve.pct_change().dropna() * 100
        fig.add_trace(
            go.Bar(y=daily_returns, name='Daily Returns'),
            row=1, col=2
        )
        
        if not self.trades_df.empty:
            # 3. 거래 분포
            fig.add_trace(
                go.Histogram(x=self.trades_df['profit_loss'], nbinsx=30, name='P&L Distribution'),
                row=2, col=1
            )
            
            # 4. 수익률 분포
            fig.add_trace(
                go.Box(y=self.trades_df['profit_loss_pct'], name='Return Distribution'),
                row=2, col=2
            )
            
            # 5. 월별 성과
            monthly = self._get_monthly_performance()
            if not monthly.empty:
                fig.add_trace(
                    go.Bar(x=monthly.index.astype(str), y=monthly['월 수익'], name='Monthly P&L'),
                    row=3, col=1
                )
        
        # 6. 낙폭 차트
        cummax = equity_curve.cummax()
        drawdown = (equity_curve - cummax) / cummax * 100
        fig.add_trace(
            go.Scatter(y=drawdown, mode='lines', fill='tozeroy', name='Drawdown'),
            row=3, col=2
        )
        
        # 레이아웃 설정
        fig.update_layout(
            height=900,
            showlegend=False,
            title_text="백테스팅 성과 분석"
        )
        
        fig.show()
    
    def save_report(self, filepath: str):
        """리포트 저장"""
        report = self.generate_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("백테스팅 성과 리포트\n")
            f.write("=" * 60 + "\n\n")
            
            for section, data in report.items():
                f.write(f"## {section}\n")
                f.write("-" * 40 + "\n")
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        f.write(f"  - {key}: {value}\n")
                elif isinstance(data, pd.DataFrame):
                    f.write(data.to_string())
                    f.write("\n")
                
                f.write("\n")
        
        print(f"리포트 저장 완료: {filepath}")
```

## 5. 통합 실행 예제

### 5.1 백테스팅 실행 스크립트

```python
# scripts/run_backtest.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from data.pipeline import DataPipeline
from models.lightgbm_model import LightGBMTrader
from backtesting.engine import BacktestEngine
from backtesting.signal_generator import SignalGenerator
from backtesting.simulator import RealtimeSimulator
from backtesting.performance_analyzer import PerformanceAnalyzer

def main():
    print("=" * 60)
    print("ML/DL 백테스팅 시스템")
    print("=" * 60)
    
    # 1. 데이터 및 모델 준비
    print("\n1. 데이터 및 모델 로딩...")
    
    pipeline = DataPipeline(
        db_path='./data/stock_data.db',
        cache_dir='./cache'
    )
    
    # 모델 로드
    lgb_model = LightGBMTrader.load('./models/lightgbm_phase1.pkl')
    
    models = {
        'lightgbm': lgb_model
    }
    
    # 2. 백테스팅 엔진 초기화
    print("\n2. 백테스팅 엔진 초기화...")
    
    engine = BacktestEngine(
        initial_capital=10_000_000,
        max_positions=5,
        position_size=0.2,  # 20% per position
        stop_loss=-3.0,
        take_profit=5.0,
        trailing_stop=2.0
    )
    
    # 3. 신호 생성기 설정
    signal_generator = SignalGenerator(
        models=models,
        thresholds={
            'buy': 0.65,
            'sell': 0.35,
            'strong_buy': 0.8,
            'strong_sell': 0.2
        }
    )
    
    # 4. 시뮬레이션 실행
    print("\n3. 백테스팅 시뮬레이션 시작...")
    
    simulator = RealtimeSimulator(engine, signal_generator, pipeline)
    
    portfolio_values = simulator.simulate(
        stock_codes=['005930', '000660'],  # 삼성전자, SK하이닉스
        start_date='20230101000000',
        end_date='20230630235959',
        speed_multiplier=0  # 최대 속도
    )
    
    # 5. 성과 분석
    print("\n4. 성과 분석...")
    
    analyzer = PerformanceAnalyzer(engine)
    report = analyzer.generate_report()
    
    print("\n" + "=" * 60)
    print("백테스팅 결과")
    print("=" * 60)
    
    for section, data in report.items():
        print(f"\n[{section}]")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
    
    # 6. 차트 생성
    print("\n5. 성과 차트 생성...")
    analyzer.plot_performance()
    
    # 7. 리포트 저장
    analyzer.save_report('./reports/backtest_report.txt')
    
    print("\n✅ 백테스팅 완료!")

if __name__ == "__main__":
    main()
```

## 6. 최적화 및 개선

### 6.1 병렬 백테스팅

```python
# backtesting/parallel_engine.py
from multiprocessing import Pool, cpu_count
import itertools

def run_single_backtest(params):
    """단일 백테스트 실행"""
    stop_loss, take_profit, position_size = params
    
    engine = BacktestEngine(
        initial_capital=10_000_000,
        stop_loss=stop_loss,
        take_profit=take_profit,
        position_size=position_size
    )
    
    # 백테스트 실행...
    # ... 
    
    metrics = engine.get_performance_metrics()
    return params, metrics

def parallel_optimization():
    """병렬 파라미터 최적화"""
    
    # 파라미터 그리드
    stop_loss_range = [-2, -3, -4, -5]
    take_profit_range = [3, 5, 7, 10]
    position_size_range = [0.1, 0.15, 0.2, 0.25]
    
    # 모든 조합 생성
    param_combinations = list(itertools.product(
        stop_loss_range,
        take_profit_range,
        position_size_range
    ))
    
    # 병렬 실행
    with Pool(cpu_count()) as pool:
        results = pool.map(run_single_backtest, param_combinations)
    
    # 최적 파라미터 찾기
    best_params = max(results, key=lambda x: x[1]['sharpe_ratio'])
    
    return best_params
```

## 7. 다음 단계

1. **실시간 거래 연동**
   - STOM 실거래 API 연결
   - 주문 관리 시스템
   - 리스크 관리 자동화

2. **고급 백테스팅 기능**
   - 슬리피지 모델링
   - 시장 충격 비용
   - 다중 자산 포트폴리오

3. **성과 모니터링**
   - 실시간 대시보드
   - 알림 시스템
   - 성과 보고서 자동화
