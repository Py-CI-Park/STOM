# 07. 트레이딩 엔진

## ⚡ 트레이딩 엔진 개요

STOM의 트레이딩 엔진은 **고성능 실시간 주문 처리**와 **다중 전략 실행**을 위한 핵심 시스템입니다. 주식과 암호화폐 시장에서 동시에 운영되며, 마이크로초 단위의 빠른 주문 실행을 지원합니다.

### 엔진 아키텍처
```
🎯 전략 엔진 (Strategy Engine)
    ↓
⚡ 주문 관리자 (Order Manager)
    ↓
🔄 리스크 관리자 (Risk Manager)
    ↓
📡 브로커 인터페이스 (Broker Interface)
    ↓
💹 시장 (Market)
```

---

## 🏗️ 전략 엔진 아키텍처

### 전략 기본 구조

#### 1. 기본 전략 클래스 (`strategy_base.py`)

**소스**: 예제 코드

```python
class StrategyBase:
    """전략 기본 클래스"""
    
    def __init__(self, name, symbol, timeframe):
        self.name = name
        self.symbol = symbol
        self.timeframe = timeframe
        self.position = 0
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        
    def on_tick(self, tick_data):
        """틱 데이터 수신 시 호출"""
        raise NotImplementedError
        
    def on_bar(self, bar_data):
        """봉 데이터 수신 시 호출"""
        raise NotImplementedError
        
    def calculate_signals(self, data):
        """매매 신호 계산"""
        raise NotImplementedError
        
    def execute_order(self, order_type, quantity, price=None):
        """주문 실행"""
        order = {
            'strategy': self.name,
            'symbol': self.symbol,
            'type': order_type,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.now()
        }
        return self.order_manager.place_order(order)
```

#### 2. 이동평균 전략 구현

**소스**: 예제 코드

```python
class MovingAverageStrategy(StrategyBase):
    """이동평균 전략"""
    
    def __init__(self, symbol, short_period=5, long_period=20):
        super().__init__("MA_Strategy", symbol, "1m")
        self.short_period = short_period
        self.long_period = long_period
        self.price_buffer = deque(maxlen=long_period)
        
    def on_tick(self, tick_data):
        """틱 데이터 처리"""
        price = tick_data['current_price']
        self.price_buffer.append(price)
        
        if len(self.price_buffer) >= self.long_period:
            signal = self.calculate_signals()
            if signal:
                self.execute_signal(signal, price)
                
    def calculate_signals(self):
        """매매 신호 계산"""
        if len(self.price_buffer) < self.long_period:
            return None
            
        prices = list(self.price_buffer)
        short_ma = sum(prices[-self.short_period:]) / self.short_period
        long_ma = sum(prices) / self.long_period
        
        # 골든 크로스 / 데드 크로스
        if short_ma > long_ma and self.position <= 0:
            return 'BUY'
        elif short_ma < long_ma and self.position >= 0:
            return 'SELL'
            
        return None
        
    def execute_signal(self, signal, price):
        """신호 실행"""
        if signal == 'BUY':
            quantity = self.calculate_position_size(price)
            self.execute_order('BUY', quantity, price)
            self.set_stop_loss(price * 0.98)  # 2% 손절
            self.set_take_profit(price * 1.04)  # 4% 익절
            
        elif signal == 'SELL':
            if self.position > 0:
                self.execute_order('SELL', self.position, price)
```

### 주식 전략 시스템

#### 1. Kiwoom 전략 엔진 (`stock/kiwoom_strategy_tick.py`)

**소스**: 예제 코드

```python
class KiwoomStrategyTick(QAxWidget):
    """키움 틱 전략 엔진"""
    
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        
        # 전략 관리
        self.strategies = {}
        self.active_symbols = set()
        
        # 주문 관리
        self.order_manager = OrderManager()
        self.risk_manager = RiskManager()
        
        # 이벤트 연결
        self.OnReceiveRealData.connect(self.on_receive_real_data)
        self.OnReceiveChejanData.connect(self.on_receive_chejan_data)
        
    def add_strategy(self, strategy):
        """전략 추가"""
        self.strategies[strategy.symbol] = strategy
        self.active_symbols.add(strategy.symbol)
        
        # 실시간 등록
        self.register_real_data(strategy.symbol)
        
    def on_receive_real_data(self, code, real_type, real_data):
        """실시간 데이터 수신"""
        if code in self.strategies:
            strategy = self.strategies[code]
            
            # 틱 데이터 파싱
            tick_data = self.parse_tick_data(code, real_data)
            
            # 리스크 체크
            if self.risk_manager.check_risk(strategy, tick_data):
                strategy.on_tick(tick_data)
                
    def parse_tick_data(self, code, real_data):
        """틱 데이터 파싱"""
        return {
            'symbol': code,
            'current_price': abs(int(self.GetCommRealData(code, 10))),
            'volume': int(self.GetCommRealData(code, 15)),
            'change_rate': float(self.GetCommRealData(code, 12)),
            'timestamp': datetime.now()
        }
```

### 암호화폐 전략 시스템

#### 1. Upbit 전략 엔진 (`coin/upbit_strategy_tick.py`)

**소스**: 예제 코드

```python
class UpbitStrategyTick:
    """업비트 틱 전략 엔진"""
    
    def __init__(self):
        self.client = pyupbit.Upbit(access, secret)
        self.strategies = {}
        self.websocket_manager = WebSocketManager()
        
    async def start_strategy_engine(self):
        """전략 엔진 시작"""
        # WebSocket 연결
        await self.websocket_manager.connect()
        
        # 전략별 데이터 스트림 구독
        for symbol in self.strategies.keys():
            await self.websocket_manager.subscribe_ticker(symbol)
            
        # 메시지 처리 루프
        async for message in self.websocket_manager.listen():
            await self.process_market_data(message)
            
    async def process_market_data(self, message):
        """시장 데이터 처리"""
        symbol = message['code']
        
        if symbol in self.strategies:
            strategy = self.strategies[symbol]
            
            tick_data = {
                'symbol': symbol,
                'price': message['trade_price'],
                'volume': message['trade_volume'],
                'timestamp': datetime.fromtimestamp(message['timestamp'] / 1000)
            }
            
            # 전략 실행
            await strategy.on_tick_async(tick_data)
```

---

## 📋 주문 관리 시스템

### 주문 관리자

#### 1. 주문 관리 클래스

**소스**: 예제 코드 (실제: `*_trader.py`)

```python
class OrderManager:
    """주문 관리자"""
    
    def __init__(self):
        self.pending_orders = {}
        self.executed_orders = []
        self.order_id_counter = 0
        
    def place_order(self, order):
        """주문 접수"""
        order_id = self.generate_order_id()
        order['order_id'] = order_id
        order['status'] = 'PENDING'
        
        # 주문 검증
        if not self.validate_order(order):
            return None
            
        # 주문 큐에 추가
        self.pending_orders[order_id] = order
        
        # 브로커로 주문 전송
        return self.send_to_broker(order)
        
    def validate_order(self, order):
        """주문 검증"""
        # 필수 필드 확인
        required_fields = ['symbol', 'type', 'quantity']
        for field in required_fields:
            if field not in order:
                return False
                
        # 수량 검증
        if order['quantity'] <= 0:
            return False
            
        # 가격 검증 (지정가 주문의 경우)
        if order['type'] in ['LIMIT_BUY', 'LIMIT_SELL']:
            if 'price' not in order or order['price'] <= 0:
                return False
                
        return True
        
    def update_order_status(self, order_id, status, executed_quantity=0):
        """주문 상태 업데이트"""
        if order_id in self.pending_orders:
            order = self.pending_orders[order_id]
            order['status'] = status
            order['executed_quantity'] = executed_quantity
            
            if status in ['FILLED', 'CANCELLED']:
                # 완료된 주문은 실행 목록으로 이동
                self.executed_orders.append(order)
                del self.pending_orders[order_id]
```

### 포지션 관리

#### 1. 포지션 관리자

**소스**: 예제 코드

```python
class PositionManager:
    """포지션 관리자"""
    
    def __init__(self):
        self.positions = {}  # symbol -> position_info
        
    def update_position(self, symbol, quantity, price, order_type):
        """포지션 업데이트"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': 0,
                'avg_price': 0,
                'unrealized_pnl': 0,
                'realized_pnl': 0
            }
            
        position = self.positions[symbol]
        
        if order_type == 'BUY':
            # 매수 시 포지션 증가
            total_cost = position['quantity'] * position['avg_price'] + quantity * price
            total_quantity = position['quantity'] + quantity
            
            if total_quantity > 0:
                position['avg_price'] = total_cost / total_quantity
                
            position['quantity'] = total_quantity
            
        elif order_type == 'SELL':
            # 매도 시 포지션 감소
            if position['quantity'] >= quantity:
                # 실현손익 계산
                realized_pnl = (price - position['avg_price']) * quantity
                position['realized_pnl'] += realized_pnl
                position['quantity'] -= quantity
                
                if position['quantity'] == 0:
                    position['avg_price'] = 0
                    
    def calculate_unrealized_pnl(self, symbol, current_price):
        """미실현손익 계산"""
        if symbol in self.positions:
            position = self.positions[symbol]
            if position['quantity'] > 0:
                unrealized_pnl = (current_price - position['avg_price']) * position['quantity']
                position['unrealized_pnl'] = unrealized_pnl
                return unrealized_pnl
        return 0
```

---

## 🛡️ 리스크 관리 시스템

### 리스크 관리자

#### 1. 리스크 체크 시스템

**소스**: 예제 코드

```python
class RiskManager:
    """리스크 관리자"""
    
    def __init__(self):
        self.max_position_size = 1000000  # 최대 포지션 크기
        self.max_daily_loss = 100000      # 일일 최대 손실
        self.max_drawdown = 0.1           # 최대 드로우다운 (10%)
        
        self.daily_pnl = 0
        self.peak_equity = 0
        self.current_equity = 0
        
    def check_risk(self, strategy, order):
        """리스크 체크"""
        # 포지션 크기 체크
        if not self.check_position_size(order):
            return False
            
        # 일일 손실 체크
        if not self.check_daily_loss():
            return False
            
        # 드로우다운 체크
        if not self.check_drawdown():
            return False
            
        # 전략별 리스크 체크
        if not self.check_strategy_risk(strategy, order):
            return False
            
        return True
        
    def check_position_size(self, order):
        """포지션 크기 체크"""
        position_value = order['quantity'] * order.get('price', 0)
        return position_value <= self.max_position_size
        
    def check_daily_loss(self):
        """일일 손실 체크"""
        return self.daily_pnl > -self.max_daily_loss
        
    def check_drawdown(self):
        """드로우다운 체크"""
        if self.peak_equity == 0:
            return True
            
        drawdown = (self.peak_equity - self.current_equity) / self.peak_equity
        return drawdown <= self.max_drawdown
        
    def update_equity(self, new_equity):
        """자산 업데이트"""
        self.current_equity = new_equity
        
        if new_equity > self.peak_equity:
            self.peak_equity = new_equity
```

### 손절/익절 시스템

#### 1. 자동 손절/익절

**소스**: 예제 코드

```python
class StopLossManager:
    """손절/익절 관리자"""
    
    def __init__(self):
        self.stop_orders = {}  # position_id -> stop_order_info
        
    def set_stop_loss(self, position_id, stop_price, position_info):
        """손절 설정"""
        self.stop_orders[position_id] = {
            'type': 'STOP_LOSS',
            'trigger_price': stop_price,
            'position': position_info,
            'active': True
        }
        
    def set_take_profit(self, position_id, target_price, position_info):
        """익절 설정"""
        self.stop_orders[position_id] = {
            'type': 'TAKE_PROFIT',
            'trigger_price': target_price,
            'position': position_info,
            'active': True
        }
        
    def check_stop_triggers(self, symbol, current_price):
        """손절/익절 트리거 체크"""
        triggered_orders = []
        
        for position_id, stop_order in self.stop_orders.items():
            if not stop_order['active']:
                continue
                
            position = stop_order['position']
            if position['symbol'] != symbol:
                continue
                
            should_trigger = False
            
            if stop_order['type'] == 'STOP_LOSS':
                # 롱 포지션: 현재가 < 손절가
                # 숏 포지션: 현재가 > 손절가
                if position['quantity'] > 0:
                    should_trigger = current_price <= stop_order['trigger_price']
                else:
                    should_trigger = current_price >= stop_order['trigger_price']
                    
            elif stop_order['type'] == 'TAKE_PROFIT':
                # 롱 포지션: 현재가 > 익절가
                # 숏 포지션: 현재가 < 익절가
                if position['quantity'] > 0:
                    should_trigger = current_price >= stop_order['trigger_price']
                else:
                    should_trigger = current_price <= stop_order['trigger_price']
                    
            if should_trigger:
                triggered_orders.append((position_id, stop_order))
                stop_order['active'] = False
                
        return triggered_orders
```

---

## 🔄 실시간 처리 시스템

### 멀티스레딩 처리

#### 1. 스레드 풀 관리

**소스**: 예제 코드

```python
class TradingThreadPool:
    """트레이딩 스레드 풀"""
    
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.data_queue = Queue()
        self.order_queue = Queue()
        
    def start_processing(self):
        """처리 시작"""
        # 데이터 처리 스레드
        self.executor.submit(self.data_processor)
        
        # 주문 처리 스레드
        self.executor.submit(self.order_processor)
        
        # 리스크 모니터링 스레드
        self.executor.submit(self.risk_monitor)
        
    def data_processor(self):
        """데이터 처리 스레드"""
        while True:
            try:
                data = self.data_queue.get(timeout=1)
                self.process_market_data(data)
            except Empty:
                continue
                
    def order_processor(self):
        """주문 처리 스레드"""
        while True:
            try:
                order = self.order_queue.get(timeout=1)
                self.process_order(order)
            except Empty:
                continue
```

### 지연시간 최적화

#### 1. 저지연 처리

**소스**: 예제 코드

```python
class LowLatencyProcessor:
    """저지연 처리기"""
    
    def __init__(self):
        self.process_times = deque(maxlen=1000)
        
    def process_tick_data(self, tick_data):
        """틱 데이터 저지연 처리"""
        start_time = time.perf_counter()
        
        try:
            # 핵심 처리 로직
            self.fast_signal_calculation(tick_data)
            
        finally:
            end_time = time.perf_counter()
            process_time = (end_time - start_time) * 1000  # ms
            self.process_times.append(process_time)
            
    def fast_signal_calculation(self, tick_data):
        """빠른 신호 계산"""
        # 최소한의 계산으로 신호 생성
        price = tick_data['price']
        
        # 간단한 이동평균 (최근 5개 가격)
        if len(self.price_buffer) >= 5:
            ma5 = sum(list(self.price_buffer)[-5:]) / 5
            
            if price > ma5 * 1.001:  # 0.1% 이상 상승
                return 'BUY_SIGNAL'
            elif price < ma5 * 0.999:  # 0.1% 이상 하락
                return 'SELL_SIGNAL'
                
        return None
        
    def get_latency_stats(self):
        """지연시간 통계"""
        if not self.process_times:
            return None
            
        return {
            'avg_latency': np.mean(self.process_times),
            'max_latency': max(self.process_times),
            'min_latency': min(self.process_times),
            'p95_latency': np.percentile(self.process_times, 95)
        }
```

---

*다음: [08. 백테스팅 시스템](../08_Backtesting/backtesting_system.md)* 