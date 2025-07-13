# 06. 데이터 관리

## 📊 데이터 관리 개요

STOM 시스템은 **고성능 실시간 데이터 처리**를 위한 다층 데이터 아키텍처를 구현합니다. 주식과 암호화폐 시장의 틱 데이터부터 분봉 데이터까지 다양한 시간 프레임의 데이터를 효율적으로 수집, 저장, 처리합니다.

### 데이터 처리 파이프라인
```
📡 실시간 데이터 수신
    ↓
🔄 데이터 전처리 및 검증
    ↓
💾 메모리 버퍼링 (고속 처리)
    ↓
🗄️ 데이터베이스 저장 (영구 보관)
    ↓
📈 차트 및 분석 시스템 공급
```

---

## 🗄️ 데이터베이스 아키텍처

### SQLite 기반 데이터 저장소

#### 1. 데이터베이스 구조 (`utility/setting.py`)
```python
# 데이터베이스 경로 설정
DATABASE_PATHS = {
    'stock': {
        'tick': 'database/stock_tick.db',
        'min': 'database/stock_min.db',
        'day': 'database/stock_day.db'
    },
    'coin': {
        'tick': 'database/coin_tick.db', 
        'min': 'database/coin_min.db',
        'day': 'database/coin_day.db'
    },
    'backtest': 'database/backtest.db',
    'strategy': 'database/strategy.db'
}

def get_database_path(market, timeframe):
    """데이터베이스 경로 반환"""
    return DATABASE_PATHS.get(market, {}).get(timeframe)
```

#### 2. 테이블 스키마 설계

##### 주식 틱 데이터 테이블
```sql
CREATE TABLE IF NOT EXISTS stock_tick (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,                 -- 종목코드
    name TEXT,                          -- 종목명
    current_price INTEGER,              -- 현재가
    open_price INTEGER,                 -- 시가
    high_price INTEGER,                 -- 고가
    low_price INTEGER,                  -- 저가
    volume INTEGER,                     -- 거래량
    volume_price REAL,                  -- 거래대금
    change_rate REAL,                   -- 등락률
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_code_timestamp (code, timestamp),
    INDEX idx_timestamp (timestamp)
);
```

##### 암호화폐 틱 데이터 테이블
```sql
CREATE TABLE IF NOT EXISTS coin_tick (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market TEXT NOT NULL,               -- 마켓 (KRW-BTC)
    trade_price REAL,                   -- 체결가
    trade_volume REAL,                  -- 체결량
    acc_trade_price REAL,               -- 누적거래대금
    acc_trade_volume REAL,              -- 누적거래량
    prev_closing_price REAL,            -- 전일종가
    change_rate REAL,                   -- 등락률
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_market_timestamp (market, timestamp)
);
```

##### 분봉 데이터 테이블
```sql
CREATE TABLE IF NOT EXISTS ohlcv_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,               -- 심볼
    timeframe TEXT NOT NULL,            -- 시간프레임 (1m, 5m, 1h, 1d)
    open_price REAL,                    -- 시가
    high_price REAL,                    -- 고가
    low_price REAL,                     -- 저가
    close_price REAL,                   -- 종가
    volume REAL,                        -- 거래량
    timestamp DATETIME,                 -- 시간
    UNIQUE(symbol, timeframe, timestamp),
    INDEX idx_symbol_timeframe_timestamp (symbol, timeframe, timestamp)
);
```

### 데이터베이스 연결 관리

#### 1. 연결 풀링 시스템
```python
class DatabaseManager:
    """데이터베이스 연결 관리자"""
    
    def __init__(self):
        self.connections = {}
        self.connection_lock = threading.Lock()
        
    def get_connection(self, db_path):
        """데이터베이스 연결 반환"""
        thread_id = threading.get_ident()
        key = f"{db_path}_{thread_id}"
        
        with self.connection_lock:
            if key not in self.connections:
                conn = sqlite3.connect(
                    db_path, 
                    check_same_thread=False,
                    timeout=30.0
                )
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                self.connections[key] = conn
                
        return self.connections[key]
    
    def execute_query(self, db_path, query, params=None):
        """쿼리 실행"""
        conn = self.get_connection(db_path)
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.fetchall()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
```

#### 2. 배치 삽입 최적화
```python
class BatchInserter:
    """배치 삽입 최적화"""
    
    def __init__(self, db_manager, batch_size=1000):
        self.db_manager = db_manager
        self.batch_size = batch_size
        self.buffers = {}
        
    def add_data(self, table_name, data):
        """데이터 추가"""
        if table_name not in self.buffers:
            self.buffers[table_name] = []
            
        self.buffers[table_name].append(data)
        
        # 배치 크기 도달 시 자동 플러시
        if len(self.buffers[table_name]) >= self.batch_size:
            self.flush_buffer(table_name)
            
    def flush_buffer(self, table_name):
        """버퍼 플러시"""
        if table_name not in self.buffers or not self.buffers[table_name]:
            return
            
        data_list = self.buffers[table_name]
        
        # 배치 삽입 쿼리 생성
        if table_name == 'stock_tick':
            query = """
            INSERT INTO stock_tick 
            (code, name, current_price, open_price, high_price, low_price, 
             volume, volume_price, change_rate, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        elif table_name == 'coin_tick':
            query = """
            INSERT INTO coin_tick 
            (market, trade_price, trade_volume, acc_trade_price, 
             acc_trade_volume, prev_closing_price, change_rate, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
        # 배치 실행
        conn = self.db_manager.get_connection(self.get_db_path(table_name))
        cursor = conn.cursor()
        
        try:
            cursor.executemany(query, data_list)
            conn.commit()
            self.buffers[table_name] = []  # 버퍼 클리어
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
```

---

## 📡 실시간 데이터 수신

### 주식 데이터 수신 시스템

#### 1. Kiwoom API 데이터 수신 (`stock/kiwoom_receiver_tick.py`)
```python
class KiwoomReceiverTick(QAxWidget):
    """키움 틱 데이터 수신기"""
    
    def __init__(self):
        super().__init__()
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
        
        # 이벤트 핸들러 연결
        self.OnReceiveTrData.connect(self.receive_tr_data)
        self.OnReceiveRealData.connect(self.receive_real_data)
        
        # 데이터 버퍼
        self.tick_buffer = deque(maxlen=10000)
        self.batch_inserter = BatchInserter(db_manager)
        
    def receive_real_data(self, code, real_type, real_data):
        """실시간 데이터 수신"""
        if real_type == "주식체결":
            tick_data = self.parse_stock_tick(code, real_data)
            self.process_tick_data(tick_data)
            
    def parse_stock_tick(self, code, real_data):
        """주식 틱 데이터 파싱"""
        current_price = abs(int(self.GetCommRealData(code, 10)))
        volume = int(self.GetCommRealData(code, 15))
        change_rate = float(self.GetCommRealData(code, 12))
        
        return {
            'code': code,
            'current_price': current_price,
            'volume': volume,
            'change_rate': change_rate,
            'timestamp': datetime.now()
        }
        
    def process_tick_data(self, tick_data):
        """틱 데이터 처리"""
        # 메모리 버퍼에 추가
        self.tick_buffer.append(tick_data)
        
        # 데이터베이스 배치 삽입
        self.batch_inserter.add_data('stock_tick', (
            tick_data['code'],
            tick_data.get('name', ''),
            tick_data['current_price'],
            tick_data.get('open_price', 0),
            tick_data.get('high_price', 0),
            tick_data.get('low_price', 0),
            tick_data['volume'],
            tick_data.get('volume_price', 0),
            tick_data['change_rate'],
            tick_data['timestamp']
        ))
        
        # 실시간 차트 업데이트
        self.send_to_ui(tick_data)
```

### 암호화폐 데이터 수신 시스템

#### 1. Upbit WebSocket 수신 (`coin/upbit_receiver.py`)
```python
class UpbitReceiver:
    """업비트 실시간 데이터 수신기"""
    
    def __init__(self):
        self.ws = None
        self.tick_buffer = deque(maxlen=10000)
        self.batch_inserter = BatchInserter(db_manager)
        
    async def connect_websocket(self):
        """웹소켓 연결"""
        uri = "wss://api.upbit.com/websocket/v1"
        
        # 구독 메시지
        subscribe_message = [
            {"ticket": "test"},
            {
                "type": "ticker",
                "codes": ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
            }
        ]
        
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(subscribe_message))
            
            while True:
                try:
                    data = await websocket.recv()
                    tick_data = self.parse_upbit_tick(data)
                    self.process_tick_data(tick_data)
                except Exception as e:
                    print(f"WebSocket 오류: {e}")
                    break
                    
    def parse_upbit_tick(self, raw_data):
        """업비트 틱 데이터 파싱"""
        data = json.loads(raw_data)
        
        return {
            'market': data['code'],
            'trade_price': data['trade_price'],
            'trade_volume': data['trade_volume'],
            'acc_trade_price': data['acc_trade_price_24h'],
            'acc_trade_volume': data['acc_trade_volume_24h'],
            'prev_closing_price': data['prev_closing_price'],
            'change_rate': data['signed_change_rate'],
            'timestamp': datetime.fromtimestamp(data['timestamp'] / 1000)
        }
```

#### 2. Binance WebSocket 수신 (`coin/binance_receiver.py`)
```python
class BinanceReceiver:
    """바이낸스 실시간 데이터 수신기"""
    
    def __init__(self):
        self.client = Client()
        self.tick_buffer = deque(maxlen=10000)
        
    def start_ticker_socket(self, symbols):
        """티커 소켓 시작"""
        def handle_socket_message(msg):
            tick_data = self.parse_binance_tick(msg)
            self.process_tick_data(tick_data)
            
        # 멀티 심볼 스트림
        streams = [f"{symbol.lower()}@ticker" for symbol in symbols]
        self.bm = BinanceSocketManager(self.client)
        self.conn_key = self.bm.start_multiplex_socket(streams, handle_socket_message)
        self.bm.start()
        
    def parse_binance_tick(self, msg):
        """바이낸스 틱 데이터 파싱"""
        data = msg['data']
        
        return {
            'symbol': data['s'],
            'price': float(data['c']),
            'volume': float(data['v']),
            'change_percent': float(data['P']),
            'timestamp': datetime.fromtimestamp(int(data['E']) / 1000)
        }
```

---

## 🔄 데이터 전처리 및 검증

### 데이터 품질 관리

#### 1. 데이터 검증 시스템
```python
class DataValidator:
    """데이터 검증 클래스"""
    
    def __init__(self):
        self.validation_rules = {
            'stock_tick': {
                'current_price': {'min': 1, 'max': 1000000},
                'volume': {'min': 0, 'max': 999999999},
                'change_rate': {'min': -30.0, 'max': 30.0}
            },
            'coin_tick': {
                'trade_price': {'min': 0.0001, 'max': 1000000},
                'trade_volume': {'min': 0, 'max': 999999999},
                'change_rate': {'min': -50.0, 'max': 50.0}
            }
        }
        
    def validate_data(self, data_type, data):
        """데이터 검증"""
        rules = self.validation_rules.get(data_type, {})
        errors = []
        
        for field, rule in rules.items():
            if field in data:
                value = data[field]
                
                # 범위 검증
                if 'min' in rule and value < rule['min']:
                    errors.append(f"{field} 값이 최소값({rule['min']})보다 작음: {value}")
                    
                if 'max' in rule and value > rule['max']:
                    errors.append(f"{field} 값이 최대값({rule['max']})보다 큼: {value}")
                    
                # 타입 검증
                if 'type' in rule and not isinstance(value, rule['type']):
                    errors.append(f"{field} 타입 오류: {type(value)} != {rule['type']}")
                    
        return len(errors) == 0, errors
        
    def clean_data(self, data_type, data):
        """데이터 정제"""
        if data_type == 'stock_tick':
            # 가격 데이터 절댓값 처리
            if 'current_price' in data:
                data['current_price'] = abs(data['current_price'])
                
            # 거래량 0 이하 값 처리
            if 'volume' in data and data['volume'] <= 0:
                data['volume'] = 0
                
        elif data_type == 'coin_tick':
            # 소수점 정밀도 조정
            if 'trade_price' in data:
                data['trade_price'] = round(data['trade_price'], 8)
                
        return data
```

#### 2. 이상치 탐지 시스템
```python
class OutlierDetector:
    """이상치 탐지 클래스"""
    
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.price_history = {}
        
    def detect_price_outlier(self, symbol, current_price):
        """가격 이상치 탐지"""
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.window_size)
            
        history = self.price_history[symbol]
        
        if len(history) < 10:  # 최소 데이터 필요
            history.append(current_price)
            return False
            
        # 통계적 이상치 탐지 (Z-score)
        mean_price = np.mean(history)
        std_price = np.std(history)
        
        if std_price == 0:
            return False
            
        z_score = abs((current_price - mean_price) / std_price)
        
        # Z-score > 3이면 이상치로 판단
        is_outlier = z_score > 3
        
        if not is_outlier:
            history.append(current_price)
            
        return is_outlier
        
    def detect_volume_spike(self, symbol, current_volume):
        """거래량 급증 탐지"""
        if symbol not in self.volume_history:
            self.volume_history[symbol] = deque(maxlen=self.window_size)
            
        history = self.volume_history[symbol]
        
        if len(history) < 10:
            history.append(current_volume)
            return False
            
        avg_volume = np.mean(history)
        
        # 평균 거래량의 5배 이상이면 급증으로 판단
        is_spike = current_volume > avg_volume * 5
        
        history.append(current_volume)
        return is_spike
```

---

## 📈 시계열 데이터 처리

### OHLCV 데이터 생성

#### 1. 틱 데이터 집계 시스템
```python
class OHLCVAggregator:
    """OHLCV 데이터 집계기"""
    
    def __init__(self):
        self.tick_buffers = {}
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
        
    def add_tick(self, symbol, tick_data):
        """틱 데이터 추가"""
        if symbol not in self.tick_buffers:
            self.tick_buffers[symbol] = {tf: [] for tf in self.timeframes}
            
        # 모든 시간프레임에 틱 추가
        for timeframe in self.timeframes:
            self.tick_buffers[symbol][timeframe].append(tick_data)
            
        # 시간프레임별 집계 확인
        self.check_aggregation(symbol, tick_data['timestamp'])
        
    def check_aggregation(self, symbol, timestamp):
        """집계 시점 확인"""
        for timeframe in self.timeframes:
            if self.should_aggregate(timeframe, timestamp):
                ohlcv = self.aggregate_ticks(symbol, timeframe)
                if ohlcv:
                    self.save_ohlcv(symbol, timeframe, ohlcv)
                    self.tick_buffers[symbol][timeframe] = []
                    
    def should_aggregate(self, timeframe, timestamp):
        """집계 필요 여부 확인"""
        if timeframe == '1m':
            return timestamp.second == 0
        elif timeframe == '5m':
            return timestamp.minute % 5 == 0 and timestamp.second == 0
        elif timeframe == '15m':
            return timestamp.minute % 15 == 0 and timestamp.second == 0
        elif timeframe == '1h':
            return timestamp.minute == 0 and timestamp.second == 0
        elif timeframe == '4h':
            return timestamp.hour % 4 == 0 and timestamp.minute == 0 and timestamp.second == 0
        elif timeframe == '1d':
            return timestamp.hour == 0 and timestamp.minute == 0 and timestamp.second == 0
            
    def aggregate_ticks(self, symbol, timeframe):
        """틱 데이터 집계"""
        ticks = self.tick_buffers[symbol][timeframe]
        
        if not ticks:
            return None
            
        prices = [tick['price'] for tick in ticks]
        volumes = [tick['volume'] for tick in ticks]
        
        ohlcv = {
            'symbol': symbol,
            'timeframe': timeframe,
            'open': prices[0],
            'high': max(prices),
            'low': min(prices),
            'close': prices[-1],
            'volume': sum(volumes),
            'timestamp': self.get_candle_timestamp(ticks[0]['timestamp'], timeframe)
        }
        
        return ohlcv
        
    def get_candle_timestamp(self, timestamp, timeframe):
        """캔들 타임스탬프 계산"""
        if timeframe == '1m':
            return timestamp.replace(second=0, microsecond=0)
        elif timeframe == '5m':
            minute = (timestamp.minute // 5) * 5
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        # ... 다른 시간프레임 처리
```

### 기술적 지표 계산

#### 1. 이동평균 계산
```python
class TechnicalIndicators:
    """기술적 지표 계산"""
    
    @staticmethod
    def simple_moving_average(prices, period):
        """단순 이동평균"""
        if len(prices) < period:
            return None
            
        return sum(prices[-period:]) / period
        
    @staticmethod
    def exponential_moving_average(prices, period, alpha=None):
        """지수 이동평균"""
        if alpha is None:
            alpha = 2 / (period + 1)
            
        ema = prices[0]
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
            
        return ema
        
    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        """볼린저 밴드"""
        if len(prices) < period:
            return None, None, None
            
        sma = TechnicalIndicators.simple_moving_average(prices, period)
        std = np.std(prices[-period:])
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return upper_band, sma, lower_band
        
    @staticmethod
    def rsi(prices, period=14):
        """RSI 계산"""
        if len(prices) < period + 1:
            return None
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
```

---

## 💾 데이터 압축 및 아카이빙

### 데이터 압축 시스템

#### 1. 시계열 데이터 압축
```python
class DataCompressor:
    """데이터 압축 관리"""
    
    def __init__(self):
        self.compression_rules = {
            'tick_data': {
                'retention_days': 30,
                'compression_after_days': 7
            },
            'minute_data': {
                'retention_days': 365,
                'compression_after_days': 30
            },
            'daily_data': {
                'retention_days': 3650,  # 10년
                'compression_after_days': 365
            }
        }
        
    def compress_old_data(self, data_type):
        """오래된 데이터 압축"""
        rules = self.compression_rules.get(data_type)
        if not rules:
            return
            
        cutoff_date = datetime.now() - timedelta(days=rules['compression_after_days'])
        
        # 압축 대상 데이터 조회
        query = f"""
        SELECT * FROM {data_type} 
        WHERE timestamp < ? AND compressed = 0
        ORDER BY timestamp
        """
        
        data = db_manager.execute_query(query, (cutoff_date,))
        
        if data:
            # 데이터 압축 및 저장
            compressed_data = self.compress_data_chunk(data)
            self.save_compressed_data(data_type, compressed_data)
            
            # 원본 데이터 삭제 또는 압축 플래그 설정
            self.mark_as_compressed(data_type, cutoff_date)
            
    def compress_data_chunk(self, data):
        """데이터 청크 압축"""
        # pandas DataFrame으로 변환
        df = pd.DataFrame(data)
        
        # 파케트 형식으로 압축
        buffer = io.BytesIO()
        df.to_parquet(buffer, compression='gzip')
        
        return buffer.getvalue()
        
    def decompress_data_chunk(self, compressed_data):
        """압축 데이터 해제"""
        buffer = io.BytesIO(compressed_data)
        df = pd.read_parquet(buffer)
        
        return df.to_dict('records')
```

### 데이터 아카이빙

#### 1. 자동 아카이빙 시스템
```python
class DataArchiver:
    """데이터 아카이빙 관리"""
    
    def __init__(self, archive_path="archive/"):
        self.archive_path = archive_path
        self.ensure_archive_directory()
        
    def archive_old_data(self, data_type, retention_days):
        """오래된 데이터 아카이빙"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # 아카이빙 대상 데이터 조회
        query = f"""
        SELECT * FROM {data_type} 
        WHERE timestamp < ?
        ORDER BY timestamp
        """
        
        data = db_manager.execute_query(query, (cutoff_date,))
        
        if data:
            # 월별로 그룹화하여 아카이빙
            grouped_data = self.group_by_month(data)
            
            for month_key, month_data in grouped_data.items():
                archive_file = f"{self.archive_path}/{data_type}_{month_key}.parquet.gz"
                self.save_archive_file(archive_file, month_data)
                
            # 아카이빙된 데이터 삭제
            self.delete_archived_data(data_type, cutoff_date)
            
    def group_by_month(self, data):
        """월별 데이터 그룹화"""
        grouped = {}
        
        for record in data:
            timestamp = record['timestamp']
            month_key = timestamp.strftime('%Y_%m')
            
            if month_key not in grouped:
                grouped[month_key] = []
                
            grouped[month_key].append(record)
            
        return grouped
        
    def restore_archived_data(self, data_type, start_date, end_date):
        """아카이빙된 데이터 복원"""
        restored_data = []
        
        # 해당 기간의 아카이브 파일 찾기
        archive_files = self.find_archive_files(data_type, start_date, end_date)
        
        for archive_file in archive_files:
            file_data = self.load_archive_file(archive_file)
            
            # 날짜 범위 필터링
            filtered_data = [
                record for record in file_data
                if start_date <= record['timestamp'] <= end_date
            ]
            
            restored_data.extend(filtered_data)
            
        return restored_data
```

---

## 🔍 데이터 조회 및 분석

### 고성능 데이터 조회

#### 1. 인덱스 최적화 쿼리
```python
class DataQueryOptimizer:
    """데이터 조회 최적화"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.query_cache = {}
        
    def get_ohlcv_data(self, symbol, timeframe, start_date, end_date, limit=None):
        """OHLCV 데이터 조회"""
        cache_key = f"{symbol}_{timeframe}_{start_date}_{end_date}_{limit}"
        
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
            
        query = """
        SELECT timestamp, open_price, high_price, low_price, close_price, volume
        FROM ohlcv_data 
        WHERE symbol = ? AND timeframe = ? 
        AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
        """
        
        params = [symbol, timeframe, start_date, end_date]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        result = self.db_manager.execute_query(query, params)
        
        # 결과 캐싱 (최대 1000개 쿼리)
        if len(self.query_cache) < 1000:
            self.query_cache[cache_key] = result
            
        return result
        
    def get_latest_tick_data(self, symbols, limit=100):
        """최신 틱 데이터 조회"""
        placeholders = ','.join(['?' for _ in symbols])
        
        query = f"""
        SELECT * FROM (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY code ORDER BY timestamp DESC
            ) as rn
            FROM stock_tick 
            WHERE code IN ({placeholders})
        ) WHERE rn <= ?
        ORDER BY code, timestamp DESC
        """
        
        params = symbols + [limit]
        return self.db_manager.execute_query(query, params)
        
    def get_volume_profile(self, symbol, start_date, end_date, price_bins=50):
        """거래량 프로파일 조회"""
        query = """
        SELECT 
            ROUND(current_price / ? ) * ? as price_level,
            SUM(volume) as total_volume,
            COUNT(*) as tick_count
        FROM stock_tick 
        WHERE code = ? AND timestamp BETWEEN ? AND ?
        GROUP BY price_level
        ORDER BY price_level
        """
        
        # 가격 구간 계산
        price_data = self.db_manager.execute_query(
            "SELECT MIN(current_price), MAX(current_price) FROM stock_tick WHERE code = ?",
            [symbol]
        )
        
        min_price, max_price = price_data[0]
        bin_size = (max_price - min_price) / price_bins
        
        params = [bin_size, bin_size, symbol, start_date, end_date]
        return self.db_manager.execute_query(query, params)
```

### 데이터 분석 도구

#### 1. 통계 분석 함수
```python
class DataAnalyzer:
    """데이터 분석 도구"""
    
    def __init__(self, query_optimizer):
        self.query_optimizer = query_optimizer
        
    def calculate_volatility(self, symbol, timeframe, period_days=30):
        """변동성 계산"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        data = self.query_optimizer.get_ohlcv_data(
            symbol, timeframe, start_date, end_date
        )
        
        if len(data) < 2:
            return None
            
        # 일일 수익률 계산
        returns = []
        for i in range(1, len(data)):
            prev_close = data[i-1][4]  # close_price
            curr_close = data[i][4]
            daily_return = (curr_close - prev_close) / prev_close
            returns.append(daily_return)
            
        # 연율화 변동성
        volatility = np.std(returns) * np.sqrt(252)  # 252 trading days
        return volatility
        
    def calculate_correlation(self, symbol1, symbol2, timeframe, period_days=30):
        """상관관계 계산"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        data1 = self.query_optimizer.get_ohlcv_data(symbol1, timeframe, start_date, end_date)
        data2 = self.query_optimizer.get_ohlcv_data(symbol2, timeframe, start_date, end_date)
        
        # 공통 시간대 데이터 추출
        common_data = self.align_time_series(data1, data2)
        
        if len(common_data) < 10:
            return None
            
        prices1 = [row[4] for row in common_data['data1']]  # close_price
        prices2 = [row[4] for row in common_data['data2']]
        
        correlation = np.corrcoef(prices1, prices2)[0, 1]
        return correlation
        
    def detect_support_resistance(self, symbol, timeframe, period_days=90):
        """지지/저항선 탐지"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        data = self.query_optimizer.get_ohlcv_data(symbol, timeframe, start_date, end_date)
        
        highs = [row[2] for row in data]  # high_price
        lows = [row[3] for row in data]   # low_price
        
        # 지지선 (저점들의 클러스터)
        support_levels = self.find_price_clusters(lows, tolerance=0.02)
        
        # 저항선 (고점들의 클러스터)
        resistance_levels = self.find_price_clusters(highs, tolerance=0.02)
        
        return {
            'support_levels': support_levels,
            'resistance_levels': resistance_levels
        }
        
    def find_price_clusters(self, prices, tolerance=0.02):
        """가격 클러스터 찾기"""
        clusters = []
        sorted_prices = sorted(prices)
        
        current_cluster = [sorted_prices[0]]
        
        for price in sorted_prices[1:]:
            if abs(price - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                current_cluster.append(price)
            else:
                if len(current_cluster) >= 3:  # 최소 3개 이상의 터치
                    clusters.append({
                        'level': np.mean(current_cluster),
                        'strength': len(current_cluster),
                        'prices': current_cluster
                    })
                current_cluster = [price]
                
        return sorted(clusters, key=lambda x: x['strength'], reverse=True)
```

---

*다음: [07. 트레이딩 엔진](../07_Trading/trading_engine.md)* 