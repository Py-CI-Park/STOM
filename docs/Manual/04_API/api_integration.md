# 04. API 통합

## 🔌 API 통합 개요

STOM은 **다중 API 통합 아키텍처**를 통해 주식과 암호화폐 시장의 실시간 데이터를 처리하고 거래를 실행합니다. 각 API는 독립적으로 관리되면서도 통합된 인터페이스를 제공합니다.

### 지원 API 목록
```
📈 주식 API
└── 키움증권 OpenAPI (KOA Studio)

🪙 암호화폐 API
├── 업비트 API (REST + WebSocket)
├── 바이낸스 API (REST + WebSocket)
└── 김치프리미엄 모니터링
```

---

## 📈 키움증권 OpenAPI

### API 개요
- **공식명**: KOA Studio (Kiwoom Open API)
- **타입**: COM 기반 ActiveX 컨트롤
- **언어**: Python (win32com.client)
- **인증**: 공인인증서 + 계좌비밀번호

### 핵심 클래스 구조

#### 1. Kiwoom 래퍼 클래스 (`kiwoom.py`)
```python
class Kiwoom:
    """키움 OpenAPI 래퍼 클래스"""
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        
        # 이벤트 핸들러 연결
        self.ocx.OnEventConnect.connect(self.OnEventConnect)
        self.ocx.OnReceiveTrData.connect(self.OnReceiveTrData)
        self.ocx.OnReceiveRealData.connect(self.OnReceiveRealData)
        self.ocx.OnReceiveChejanData.connect(self.OnReceiveChejanData)
        self.ocx.OnReceiveConditionVer.connect(self.OnReceiveConditionVer)
        self.ocx.OnReceiveRealCondition.connect(self.OnReceiveRealCondition)
```

#### 2. 로그인 및 인증
```python
def CommConnect(self):
    """OpenAPI 로그인"""
    self.ocx.dynamicCall("CommConnect()")
    
def OnEventConnect(self, err_code):
    """로그인 이벤트 처리"""
    if err_code == 0:
        print("로그인 성공")
        self.account_num = self.GetLoginInfo("ACCNO")
        self.user_id = self.GetLoginInfo("USER_ID")
        self.user_name = self.GetLoginInfo("USER_NM")
    else:
        print(f"로그인 실패: {err_code}")
```

### 실시간 데이터 수신

#### 1. 체결 데이터 (`주식체결`)
```python
def OnReceiveRealData(self, code, realtype, realdata):
    """실시간 데이터 수신"""
    if realtype == '주식체결':
        # 체결시간, 현재가, 전일대비, 등락률, 거래량 등
        current_price = self.GetCommRealData(code, 10)
        volume = self.GetCommRealData(code, 15)
        change_rate = self.GetCommRealData(code, 12)
        
        # 데이터 처리 및 전송
        self.ProcessTickData(code, current_price, volume, change_rate)
```

#### 2. 호가 데이터 (`주식호가잔량`)
```python
def ProcessHogaData(self, code):
    """호가 데이터 처리"""
    hoga_data = {
        '매도호가1': self.GetCommRealData(code, 27),
        '매도잔량1': self.GetCommRealData(code, 28),
        '매수호가1': self.GetCommRealData(code, 51),
        '매수잔량1': self.GetCommRealData(code, 52),
        # ... 10단계 호가
    }
    return hoga_data
```

### 주문 실행

#### 1. 주문 전송
```python
def SendOrder(self, rqname, screen_no, acc_no, order_type, code, qty, price, hoga_gb, order_no):
    """주문 전송"""
    ret = self.ocx.dynamicCall(
        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
        [rqname, screen_no, acc_no, order_type, code, qty, price, hoga_gb, order_no]
    )
    return ret

# 주문 타입
ORDER_TYPE = {
    1: '신규매수',
    2: '신규매도', 
    3: '매수취소',
    4: '매도취소',
    5: '매수정정',
    6: '매도정정'
}
```

#### 2. 체결 확인
```python
def OnReceiveChejanData(self, gubun, item_cnt, fid_list):
    """체결 데이터 수신"""
    if gubun == "0":  # 주문체결
        order_no = self.GetChejanData(9203)
        code = self.GetChejanData(9001)
        order_qty = self.GetChejanData(900)
        chejan_qty = self.GetChejanData(911)
        chejan_price = self.GetChejanData(910)
        
        # 체결 처리
        self.ProcessOrderResult(order_no, code, chejan_qty, chejan_price)
```

### 조건검색

#### 1. 조건식 로드
```python
def GetConditionLoad(self):
    """조건검색식 로드"""
    ret = self.ocx.dynamicCall("GetConditionLoad()")
    return ret

def GetConditionNameList(self):
    """조건검색식 목록 조회"""
    data = self.ocx.dynamicCall("GetConditionNameList()")
    conditions = []
    for line in data.split(';'):
        if line:
            index, name = line.split('^')
            conditions.append([int(index), name])
    return conditions
```

#### 2. 실시간 조건검색
```python
def SendCondition(self, screen_no, cond_name, cond_index, search_type):
    """조건검색 실행"""
    ret = self.ocx.dynamicCall(
        "SendCondition(QString, QString, int, int)",
        screen_no, cond_name, cond_index, search_type
    )
    return ret

def OnReceiveRealCondition(self, code, type, cond_name, cond_index):
    """실시간 조건검색 결과"""
    if type == "I":  # 편입
        self.AddToWatchlist(code)
    elif type == "D":  # 이탈
        self.RemoveFromWatchlist(code)
```

---

## 🪙 업비트 API

### API 개요
- **공식명**: Upbit Open API
- **타입**: REST API + WebSocket
- **인증**: JWT 토큰 (Access Key + Secret Key)
- **제한**: 분당 요청 제한 (Public: 600회, Private: 200회)

### REST API 구조

#### 1. 인증 시스템
```python
import jwt
import hashlib
import uuid
from urllib.parse import urlencode

class UpbitAPI:
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.server_url = 'https://api.upbit.com'
    
    def generate_token(self, query=None):
        """JWT 토큰 생성"""
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }
        
        if query:
            query_string = urlencode(query).encode()
            m = hashlib.sha512()
            m.update(query_string)
            query_hash = m.hexdigest()
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'
        
        jwt_token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return jwt_token
```

#### 2. 시장 데이터 조회
```python
def get_ticker(self, markets):
    """현재가 조회"""
    url = f"{self.server_url}/v1/ticker"
    params = {'markets': ','.join(markets)}
    
    response = requests.get(url, params=params)
    return response.json()

def get_orderbook(self, markets):
    """호가 정보 조회"""
    url = f"{self.server_url}/v1/orderbook"
    params = {'markets': ','.join(markets)}
    
    response = requests.get(url, params=params)
    return response.json()

def get_candles_minutes(self, unit, market, count=1):
    """분봉 데이터 조회"""
    url = f"{self.server_url}/v1/candles/minutes/{unit}"
    params = {
        'market': market,
        'count': count
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

#### 3. 거래 API
```python
def place_order(self, market, side, volume, price, ord_type):
    """주문 생성"""
    url = f"{self.server_url}/v1/orders"
    
    data = {
        'market': market,
        'side': side,        # 'bid' or 'ask'
        'volume': str(volume),
        'price': str(price),
        'ord_type': ord_type  # 'limit', 'price', 'market'
    }
    
    jwt_token = self.generate_token(data)
    headers = {'Authorization': f'Bearer {jwt_token}'}
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def cancel_order(self, uuid):
    """주문 취소"""
    url = f"{self.server_url}/v1/order"
    data = {'uuid': uuid}
    
    jwt_token = self.generate_token(data)
    headers = {'Authorization': f'Bearer {jwt_token}'}
    
    response = requests.delete(url, params=data, headers=headers)
    return response.json()
```

### WebSocket 실시간 데이터

#### 1. WebSocket 연결
```python
import websocket
import json
import uuid

class UpbitWebSocket:
    def __init__(self, on_message_callback):
        self.ws_url = "wss://api.upbit.com/websocket/v1"
        self.on_message_callback = on_message_callback
        self.ws = None
    
    def connect(self):
        """WebSocket 연결"""
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever()
    
    def on_open(self, ws):
        """연결 성공"""
        print("업비트 WebSocket 연결됨")
        self.subscribe_ticker(['KRW-BTC', 'KRW-ETH'])
        self.subscribe_orderbook(['KRW-BTC', 'KRW-ETH'])
```

#### 2. 구독 메시지
```python
def subscribe_ticker(self, codes):
    """현재가 구독"""
    subscribe_data = [
        {"ticket": str(uuid.uuid4())},
        {
            "type": "ticker",
            "codes": codes,
            "isOnlySnapshot": False,
            "isOnlyRealtime": True
        }
    ]
    self.ws.send(json.dumps(subscribe_data))

def subscribe_orderbook(self, codes):
    """호가 구독"""
    subscribe_data = [
        {"ticket": str(uuid.uuid4())},
        {
            "type": "orderbook",
            "codes": codes,
            "isOnlySnapshot": False,
            "isOnlyRealtime": True
        }
    ]
    self.ws.send(json.dumps(subscribe_data))

def subscribe_trade(self, codes):
    """체결 구독"""
    subscribe_data = [
        {"ticket": str(uuid.uuid4())},
        {
            "type": "trade",
            "codes": codes,
            "isOnlySnapshot": False,
            "isOnlyRealtime": True
        }
    ]
    self.ws.send(json.dumps(subscribe_data))
```

#### 3. 데이터 처리
```python
def on_message(self, ws, message):
    """메시지 수신 처리"""
    try:
        # 바이너리 데이터 디코딩
        data = json.loads(message.decode('utf-8'))
        
        if data.get('type') == 'ticker':
            self.process_ticker_data(data)
        elif data.get('type') == 'orderbook':
            self.process_orderbook_data(data)
        elif data.get('type') == 'trade':
            self.process_trade_data(data)
            
    except Exception as e:
        print(f"메시지 처리 오류: {e}")

def process_ticker_data(self, data):
    """현재가 데이터 처리"""
    ticker_data = {
        'market': data['code'],
        'trade_price': data['trade_price'],
        'change': data['change'],
        'change_rate': data['change_rate'],
        'acc_trade_volume_24h': data['acc_trade_volume_24h'],
        'timestamp': data['timestamp']
    }
    self.on_message_callback('ticker', ticker_data)
```

---

## 🌐 바이낸스 API

### API 개요
- **공식명**: Binance API
- **타입**: REST API + WebSocket
- **인증**: HMAC SHA256 서명
- **제한**: 가중치 기반 요청 제한

### REST API 구조

#### 1. 인증 시스템
```python
import hmac
import hashlib
import time

class BinanceAPI:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = 'https://api.binance.com'
    
    def generate_signature(self, query_string):
        """HMAC SHA256 서명 생성"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_headers(self):
        """요청 헤더 생성"""
        return {
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }
```

#### 2. 시장 데이터 조회
```python
def get_ticker_24hr(self, symbol=None):
    """24시간 가격 변동 통계"""
    url = f"{self.base_url}/api/v3/ticker/24hr"
    params = {}
    if symbol:
        params['symbol'] = symbol
    
    response = requests.get(url, params=params)
    return response.json()

def get_depth(self, symbol, limit=100):
    """호가창 정보"""
    url = f"{self.base_url}/api/v3/depth"
    params = {
        'symbol': symbol,
        'limit': limit
    }
    
    response = requests.get(url, params=params)
    return response.json()

def get_klines(self, symbol, interval, limit=500):
    """캔들스틱 데이터"""
    url = f"{self.base_url}/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,  # 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        'limit': limit
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

#### 3. 거래 API
```python
def place_order(self, symbol, side, type, quantity, price=None):
    """주문 생성"""
    url = f"{self.base_url}/api/v3/order"
    
    params = {
        'symbol': symbol,
        'side': side,        # BUY, SELL
        'type': type,        # LIMIT, MARKET, STOP_LOSS, etc.
        'quantity': quantity,
        'timestamp': int(time.time() * 1000)
    }
    
    if price:
        params['price'] = price
        params['timeInForce'] = 'GTC'  # Good Till Cancel
    
    query_string = urlencode(params)
    signature = self.generate_signature(query_string)
    params['signature'] = signature
    
    headers = self.get_headers()
    response = requests.post(url, params=params, headers=headers)
    return response.json()
```

### WebSocket 스트림

#### 1. 개별 심볼 스트림
```python
class BinanceWebSocket:
    def __init__(self):
        self.base_ws_url = "wss://stream.binance.com:9443/ws/"
    
    def ticker_stream(self, symbol):
        """개별 심볼 현재가 스트림"""
        stream_url = f"{self.base_ws_url}{symbol.lower()}@ticker"
        return stream_url
    
    def depth_stream(self, symbol, speed="100ms"):
        """호가창 스트림"""
        stream_url = f"{self.base_ws_url}{symbol.lower()}@depth@{speed}"
        return stream_url
    
    def trade_stream(self, symbol):
        """체결 스트림"""
        stream_url = f"{self.base_ws_url}{symbol.lower()}@trade"
        return stream_url
```

#### 2. 멀티 스트림
```python
def create_multi_stream(self, streams):
    """다중 스트림 생성"""
    stream_names = '/'.join(streams)
    multi_stream_url = f"wss://stream.binance.com:9443/stream?streams={stream_names}"
    return multi_stream_url

# 사용 예시
streams = [
    'btcusdt@ticker',
    'ethusdt@ticker', 
    'btcusdt@depth@100ms',
    'ethusdt@depth@100ms'
]
ws_url = create_multi_stream(streams)
```

---

## 🔄 김치프리미엄 모니터링

### 김프 계산 시스템

#### 1. 가격 차이 계산
```python
class KimpCalculator:
    def __init__(self):
        self.upbit_prices = {}
        self.binance_prices = {}
        self.exchange_rate = 1300  # USD/KRW 환율
    
    def calculate_kimp(self, symbol):
        """김치프리미엄 계산"""
        upbit_symbol = f"KRW-{symbol}"
        binance_symbol = f"{symbol}USDT"
        
        if upbit_symbol in self.upbit_prices and binance_symbol in self.binance_prices:
            upbit_price = self.upbit_prices[upbit_symbol]
            binance_price_krw = self.binance_prices[binance_symbol] * self.exchange_rate
            
            kimp = ((upbit_price - binance_price_krw) / binance_price_krw) * 100
            return kimp
        
        return None
    
    def update_upbit_price(self, symbol, price):
        """업비트 가격 업데이트"""
        self.upbit_prices[symbol] = price
    
    def update_binance_price(self, symbol, price):
        """바이낸스 가격 업데이트"""
        self.binance_prices[symbol] = price
```

#### 2. 실시간 김프 모니터링
```python
class KimpMonitor:
    def __init__(self, callback):
        self.calculator = KimpCalculator()
        self.callback = callback
        self.symbols = ['BTC', 'ETH', 'XRP', 'ADA', 'DOT']
        
    def start_monitoring(self):
        """김프 모니터링 시작"""
        # 업비트 WebSocket 연결
        upbit_ws = UpbitWebSocket(self.on_upbit_message)
        upbit_ws.subscribe_ticker([f"KRW-{symbol}" for symbol in self.symbols])
        
        # 바이낸스 WebSocket 연결
        binance_streams = [f"{symbol.lower()}usdt@ticker" for symbol in self.symbols]
        binance_ws = BinanceWebSocket(self.on_binance_message)
        binance_ws.connect_multi_stream(binance_streams)
    
    def on_upbit_message(self, message_type, data):
        """업비트 메시지 처리"""
        if message_type == 'ticker':
            symbol = data['market']
            price = data['trade_price']
            self.calculator.update_upbit_price(symbol, price)
            self.check_kimp_alert(symbol.split('-')[1])
    
    def on_binance_message(self, data):
        """바이낸스 메시지 처리"""
        if 'data' in data:
            ticker_data = data['data']
            symbol = ticker_data['s']  # BTCUSDT
            price = float(ticker_data['c'])  # 현재가
            self.calculator.update_binance_price(symbol, price)
            
            base_symbol = symbol.replace('USDT', '')
            self.check_kimp_alert(base_symbol)
    
    def check_kimp_alert(self, symbol):
        """김프 알림 확인"""
        kimp = self.calculator.calculate_kimp(symbol)
        if kimp is not None:
            if abs(kimp) > 5.0:  # 5% 이상 차이
                alert_data = {
                    'symbol': symbol,
                    'kimp': kimp,
                    'timestamp': time.time()
                }
                self.callback('kimp_alert', alert_data)
```

---

## 🔧 API 통합 관리

### 통합 API 매니저

#### 1. API 팩토리 패턴
```python
class APIFactory:
    """API 팩토리"""
    
    @staticmethod
    def create_stock_api():
        """주식 API 생성"""
        return Kiwoom()
    
    @staticmethod
    def create_upbit_api(access_key, secret_key):
        """업비트 API 생성"""
        return UpbitAPI(access_key, secret_key)
    
    @staticmethod
    def create_binance_api(api_key, secret_key):
        """바이낸스 API 생성"""
        return BinanceAPI(api_key, secret_key)

class APIManager:
    """통합 API 관리자"""
    def __init__(self):
        self.apis = {}
        self.websockets = {}
        
    def initialize_apis(self, config):
        """API 초기화"""
        # 키움 API
        if config.get('kiwoom_enabled'):
            self.apis['kiwoom'] = APIFactory.create_stock_api()
        
        # 업비트 API
        if config.get('upbit_enabled'):
            self.apis['upbit'] = APIFactory.create_upbit_api(
                config['upbit_access_key'],
                config['upbit_secret_key']
            )
        
        # 바이낸스 API
        if config.get('binance_enabled'):
            self.apis['binance'] = APIFactory.create_binance_api(
                config['binance_api_key'],
                config['binance_secret_key']
            )
```

#### 2. 에러 처리 및 재연결
```python
class APIErrorHandler:
    """API 에러 처리"""
    
    def __init__(self, max_retries=3, retry_delay=5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def handle_api_error(self, api_name, error, retry_func):
        """API 에러 처리"""
        print(f"{api_name} API 오류: {error}")
        
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.retry_delay)
                retry_func()
                print(f"{api_name} API 재연결 성공")
                break
            except Exception as e:
                print(f"{api_name} API 재연결 실패 ({attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    print(f"{api_name} API 재연결 포기")

class RateLimiter:
    """API 요청 제한 관리"""
    
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def can_make_request(self):
        """요청 가능 여부 확인"""
        now = time.time()
        # 시간 윈도우 밖의 요청 제거
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
    
    def wait_time(self):
        """대기 시간 계산"""
        if not self.requests:
            return 0
        oldest_request = min(self.requests)
        return max(0, self.time_window - (time.time() - oldest_request))
```

### 데이터 정규화

#### 1. 통합 데이터 포맷
```python
class DataNormalizer:
    """데이터 정규화"""
    
    @staticmethod
    def normalize_ticker_data(source, raw_data):
        """현재가 데이터 정규화"""
        if source == 'kiwoom':
            return {
                'symbol': raw_data['code'],
                'price': float(raw_data['current_price']),
                'change': float(raw_data['change']),
                'change_rate': float(raw_data['change_rate']),
                'volume': int(raw_data['volume']),
                'timestamp': raw_data['timestamp']
            }
        elif source == 'upbit':
            return {
                'symbol': raw_data['market'],
                'price': raw_data['trade_price'],
                'change': raw_data['change'],
                'change_rate': raw_data['change_rate'],
                'volume': raw_data['acc_trade_volume_24h'],
                'timestamp': raw_data['timestamp']
            }
        elif source == 'binance':
            return {
                'symbol': raw_data['s'],
                'price': float(raw_data['c']),
                'change': float(raw_data['P']),
                'change_rate': float(raw_data['P']),
                'volume': float(raw_data['v']),
                'timestamp': raw_data['E']
            }
    
    @staticmethod
    def normalize_orderbook_data(source, raw_data):
        """호가 데이터 정규화"""
        # 각 거래소별 호가 데이터를 통일된 형태로 변환
        pass
```

---

## 📊 성능 모니터링

### API 성능 지표
```python
class APIPerformanceMonitor:
    """API 성능 모니터링"""
    
    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'error_count': 0,
            'response_times': [],
            'last_request_time': None
        }
    
    def record_request(self, response_time, success=True):
        """요청 기록"""
        self.metrics['request_count'] += 1
        self.metrics['response_times'].append(response_time)
        self.metrics['last_request_time'] = time.time()
        
        if not success:
            self.metrics['error_count'] += 1
    
    def get_statistics(self):
        """통계 조회"""
        response_times = self.metrics['response_times']
        return {
            'total_requests': self.metrics['request_count'],
            'error_rate': self.metrics['error_count'] / max(1, self.metrics['request_count']),
            'avg_response_time': sum(response_times) / max(1, len(response_times)),
            'max_response_time': max(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0
        }
```

---

*다음: [05. UI/UX 분석](../05_UI_UX/ui_ux_analysis.md)* 