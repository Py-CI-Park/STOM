# 유틸리티 모듈 (utility/)

## 📋 개요

유틸리티 모듈은 STOM 시스템의 **공통 기능**을 제공하는 핵심 라이브러리입니다. 설정 관리, 데이터베이스 연동, 통신 시스템, 데이터 처리 함수 등 모든 모듈에서 공통으로 사용되는 기능을 제공합니다.

---

## 🏗 모듈 구조

```
utility/
├── setting.py                    # 전역 설정 및 상수 관리
├── static.py                     # 정적 함수 모음
├── query.py                      # 데이터베이스 쿼리 프로세스
├── chart.py                      # 차트 데이터 처리
├── chart_items.py                # 차트 아이템 정의
├── hoga.py                       # 호가 데이터 처리
├── sound.py                      # 알림 소리 재생
├── telegram_msg.py               # 텔레그램 메시지 전송
├── webcrawling.py                # 웹 크롤링 유틸리티
├── timesync.py                   # 시간 동기화
├── syntax.py                     # 전략 구문 검증
├── database_check.py             # DB 무결성 검증
├── db_update_day.py              # 일간 데이터 업데이트
├── db_update_back.py             # 과거 데이터 업데이트
├── db_distinct.py                # 데이터 중복 제거
└── total_code_line.py            # 전체 코드 라인 수 계산
```

**참고**: ZeroMQ 통신은 `ui/ui_mainwindow.py`의 ZmqServ/ZmqRecv 클래스로 처리됩니다.

---

## ⚙️ 설정 관리 (setting.py)

### 전역 설정 딕셔너리

**소스**: 예제 코드 (실제: `utility/setting.py:93-200`)

```python
# 거래 설정
DICT_SET = {
    # 증권사/거래소
    '증권사': '키움증권',
    '거래소': '업비트',

    # 투자금
    '주식투자금': 10000000,        # 1,000만원
    '코인투자금': 1000000,         # 100만원

    # 프로세스 활성화
    '주식리시버': True,
    '주식트레이더': True,
    '주식전략': True,
    '코인리시버': True,
    '코인트레이더': True,
    '코인전략': True,
    '백테스터': False,

    # 거래 설정
    '주식자동거래': False,
    '주식모의투자': True,
    '코인자동거래': False,

    # 리스크 관리
    '주식손실중지': True,
    '주식손실중지수익률': -5.0,
    '코인손실중지': True,
    '코인손실중지수익률': -10.0,

    # 알림 설정
    '텔레그램': True,
    '소리알림': True,

    # 차트 설정
    '차트저장': True,
    '실시간차트': True,
}
```

### 데이터베이스 경로

**소스**: `utility/setting.py:31-49`

```python
# 데이터베이스 경로
BASE_DIR = 'C:/System_Trading/STOM/STOM_V1'

DB_SETTING = f'{BASE_DIR}/DB/setting.db'
DB_STRATEGY = f'{BASE_DIR}/DB/strategy.db'
DB_TRADELIST = f'{BASE_DIR}/DB/tradelist.db'
DB_BACKTEST = f'{BASE_DIR}/DB/backtest.db'
DB_OPTUNA = f'{BASE_DIR}/DB/optuna.db'

# 주식 데이터베이스
DB_STOCK_TICK = f'{BASE_DIR}/DB/stock_tick.db'
DB_STOCK_MIN = f'{BASE_DIR}/DB/stock_min.db'
DB_STOCK_DAY = f'{BASE_DIR}/DB/stock_day.db'

# 코인 데이터베이스
DB_COIN_TICK = f'{BASE_DIR}/DB/coin_tick.db'
DB_COIN_MIN = f'{BASE_DIR}/DB/coin_min.db'
DB_COIN_DAY = f'{BASE_DIR}/DB/coin_day.db'
```

### API 키 관리

**소스**: 예제 코드 (실제 암호화 기능: `utility/static.py:187-194`)

```python
from cryptography.fernet import Fernet

class APIKeyManager:
    """API 키 암호화 관리"""
    def __init__(self):
        # 암호화 키 로드 (또는 생성)
        self.key = self.load_or_create_key()
        self.cipher = Fernet(self.key)

    def load_or_create_key(self):
        """암호화 키 로드 또는 생성"""
        key_file = f'{BASE_DIR}/key.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def encrypt_api_key(self, api_key):
        """API 키 암호화"""
        encrypted = self.cipher.encrypt(api_key.encode())
        return encrypted

    def decrypt_api_key(self, encrypted_key):
        """API 키 복호화"""
        decrypted = self.cipher.decrypt(encrypted_key)
        return decrypted.decode()

    def save_api_keys(self, keys_dict):
        """API 키 저장"""
        encrypted_keys = {}
        for name, key in keys_dict.items():
            encrypted_keys[name] = self.encrypt_api_key(key)

        # 데이터베이스에 저장
        con = sqlite3.connect(DB_SETTING)
        cursor = con.cursor()
        for name, enc_key in encrypted_keys.items():
            cursor.execute(
                "INSERT OR REPLACE INTO api_keys (name, encrypted_key) VALUES (?, ?)",
                (name, enc_key)
            )
        con.commit()
        con.close()

    def load_api_keys(self):
        """API 키 로드"""
        con = sqlite3.connect(DB_SETTING)
        cursor = con.cursor()
        cursor.execute("SELECT name, encrypted_key FROM api_keys")
        rows = cursor.fetchall()
        con.close()

        keys_dict = {}
        for name, enc_key in rows:
            keys_dict[name] = self.decrypt_api_key(enc_key)

        return keys_dict
```

---

## 🔧 정적 함수 (static.py)

### 시간 관련 함수

**소스**: `utility/static.py:87-128`

```python
from datetime import datetime, timedelta
import time

def now():
    """현재 시간"""
    return datetime.now()

def strf_time(format_str='%Y%m%d%H%M%S'):
    """시간 문자열 변환"""
    return now().strftime(format_str)

def strp_time(format_str, time_str):
    """문자열을 시간으로 변환"""
    return datetime.strptime(time_str, format_str)

def timedelta_day(days):
    """일수 계산"""
    return now() - timedelta(days=days)

def int_time():
    """정수형 시간 (HHMMSS)"""
    return int(now().strftime('%H%M%S'))

def strf_ymdhm():
    """년월일시분 문자열"""
    return now().strftime('%Y%m%d%H%M')
```

### 수학 함수

**소스**: `utility/static.py:233-580` (GetHogaunit, GetVIPrice 등)

```python
import math

def roundfigure_upper5(x):
    """5원 단위 올림"""
    return math.ceil(x / 5) * 5

def roundfigure_lower5(x):
    """5원 단위 내림"""
    return math.floor(x / 5) * 5

def GetVIPrice(price):
    """VI 발동 가격 계산 (±10%)"""
    return int(price * 0.1)

def GetHogaunit(price):
    """호가 단위 계산"""
    if price < 1000:
        return 1
    elif price < 5000:
        return 5
    elif price < 10000:
        return 10
    elif price < 50000:
        return 50
    elif price < 100000:
        return 100
    elif price < 500000:
        return 500
    else:
        return 1000

def GetUpjongJisu(upjong_code):
    """업종 지수 계산"""
    # 업종 코드에 따른 지수 계산
    pass
```

### 데이터 변환 함수

**소스**: `utility/static.py:135-168` (change_format, comma2int, comma2float)

```python
def comma_format(x):
    """천단위 콤마 포맷"""
    return f"{x:,}"

def percent_format(x, decimal=2):
    """퍼센트 포맷"""
    return f"{x:.{decimal}f}%"

def timestamp_to_datetime(timestamp):
    """타임스탬프를 datetime으로 변환"""
    return datetime.fromtimestamp(timestamp / 1000)

def datetime_to_timestamp(dt):
    """datetime을 타임스탬프로 변환"""
    return int(dt.timestamp() * 1000)
```

### 종목 코드 관련

**소스**: 예제 코드

```python
def get_stock_name(code):
    """종목 코드로 종목명 조회"""
    # 데이터베이스에서 종목명 조회
    pass

def get_stock_code(name):
    """종목명으로 종목 코드 조회"""
    # 데이터베이스에서 종목 코드 조회
    pass
```

---

## 💾 데이터베이스 쿼리 (query.py)

### 쿼리 정의

**소스**: 예제 코드 (실제: `utility/query.py:12-32`)

```python
import sqlite3
from threading import Lock

class QueryManager:
    """데이터베이스 쿼리 관리"""
    def __init__(self):
        self.lock = Lock()

    def execute_query(self, db_path, query, params=None, commit=False):
        """쿼리 실행"""
        with self.lock:
            try:
                con = sqlite3.connect(db_path)
                cursor = con.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if commit:
                    con.commit()
                    result = cursor.rowcount
                else:
                    result = cursor.fetchall()

                con.close()
                return result

            except Exception as e:
                print(f"쿼리 실행 실패: {e}")
                return None

    def execute_many(self, db_path, query, data_list):
        """배치 쿼리 실행"""
        with self.lock:
            try:
                con = sqlite3.connect(db_path)
                cursor = con.cursor()
                cursor.executemany(query, data_list)
                con.commit()
                con.close()
                return True

            except Exception as e:
                print(f"배치 쿼리 실패: {e}")
                return False
```

### 주요 쿼리 정의

**소스**: 예제 코드

```python
# 틱 데이터 삽입
INSERT_TICK = """
INSERT OR REPLACE INTO tick_data
(code, timestamp, price, volume)
VALUES (?, ?, ?, ?)
"""

# 분봉 데이터 삽입
INSERT_CANDLE = """
INSERT OR REPLACE INTO candle_data
(code, timestamp, open, high, low, close, volume)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

# 거래 내역 삽입
INSERT_TRADE = """
INSERT INTO trade_list
(timestamp, code, name, side, quantity, price, amount, profit)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

# 잔고 조회
SELECT_BALANCE = """
SELECT code, quantity, avg_price
FROM balance
WHERE account = ?
"""

# 전략 파라미터 조회
SELECT_STRATEGY = """
SELECT * FROM strategy
WHERE strategy_name = ?
"""
```

---

## 🔍 데이터베이스 검증 (database_check.py)

### 무결성 검증

**소스**: 예제 코드 (실제: `utility/database_check.py:1-100`)

```python
class DatabaseChecker:
    """데이터베이스 무결성 검증"""
    def __init__(self):
        self.errors = []

    def check_all_databases(self):
        """모든 데이터베이스 검증"""
        databases = [
            DB_SETTING,
            DB_STRATEGY,
            DB_TRADELIST,
            DB_STOCK_TICK,
            DB_COIN_TICK,
        ]

        for db_path in databases:
            self.check_database(db_path)

        return len(self.errors) == 0

    def check_database(self, db_path):
        """개별 데이터베이스 검증"""
        if not os.path.exists(db_path):
            self.errors.append(f"데이터베이스 파일 없음: {db_path}")
            self.create_database(db_path)
            return

        # 무결성 검사
        con = sqlite3.connect(db_path)
        cursor = con.cursor()

        try:
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            if result[0] != 'ok':
                self.errors.append(f"무결성 오류: {db_path}")

            # 테이블 존재 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            if not tables:
                self.errors.append(f"테이블 없음: {db_path}")

        except Exception as e:
            self.errors.append(f"검증 실패 {db_path}: {e}")

        finally:
            con.close()

    def create_database(self, db_path):
        """데이터베이스 생성"""
        print(f"데이터베이스 생성 중: {db_path}")
        # 데이터베이스 스키마에 따라 테이블 생성
        pass

    def repair_database(self, db_path):
        """데이터베이스 복구"""
        print(f"데이터베이스 복구 중: {db_path}")
        # 백업에서 복구 또는 재생성
        pass
```

---

## 📡 ZeroMQ 통신

### ZeroMQ 서버 (zmq_server.py)

**소스**: `ui/ui_mainwindow.py:346-363`

```python
import zmq
from PyQt5.QtCore import QThread

class ZmqServ(QThread):
    """ZeroMQ 서버"""
    def __init__(self, queue, port_num=5555):
        super().__init__()
        self.queue = queue
        self.port_num = port_num
        self.is_running = True

    def run(self):
        """서버 실행"""
        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        socket.bind(f'tcp://*:{self.port_num}')

        while self.is_running:
            try:
                # 큐에서 메시지 수신
                msg, data = self.queue.get()

                # ZeroMQ로 전송
                socket.send_string(msg, zmq.SNDMORE)
                socket.send_pyobj(data)

            except Exception as e:
                print(f"ZMQ 서버 에러: {e}")

        socket.close()
        context.term()

    def stop(self):
        """서버 중지"""
        self.is_running = False
```

### ZeroMQ 클라이언트 (zmq_client.py)

**소스**: `ui/ui_mainwindow.py:366-410`

```python
class ZmqRecv(QThread):
    """ZeroMQ 클라이언트"""
    def __init__(self, qlist, port_num=5777):
        super().__init__()
        self.qlist = qlist
        self.port_num = port_num
        self.is_running = True

    def run(self):
        """클라이언트 실행"""
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        socket.connect(f'tcp://localhost:{self.port_num}')
        socket.setsockopt_string(zmq.SUBSCRIBE, '')

        while self.is_running:
            try:
                # 메시지 수신
                msg = socket.recv_string()
                data = socket.recv_pyobj()

                # 적절한 큐로 전달
                self.route_message(msg, data)

            except Exception as e:
                print(f"ZMQ 클라이언트 에러: {e}")

        socket.close()
        context.term()

    def route_message(self, msg, data):
        """메시지 라우팅"""
        if msg.startswith('stock'):
            self.qlist[8].put((msg, data))  # sreceivQ
        elif msg.startswith('coin'):
            self.qlist[11].put((msg, data))  # creceivQ
        elif msg.startswith('ui'):
            self.qlist[0].put((msg, data))  # windowQ
        else:
            self.qlist[14].put((msg, data))  # totalQ
```

---

## 📱 텔레그램 봇 (telegram_bot.py)

### 텔레그램 알림

**소스**: `utility/telegram_msg.py:7-143`

```python
import requests

class TelegramBot:
    """텔레그램 봇"""
    def __init__(self):
        self.token = self.load_token()
        self.chat_id = self.load_chat_id()
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, message):
        """메시지 전송"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data)
            return response.json()

        except Exception as e:
            print(f"텔레그램 전송 실패: {e}")
            return None

    def send_photo(self, photo_path, caption=''):
        """사진 전송"""
        try:
            url = f"{self.base_url}/sendPhoto"
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption
                }
                response = requests.post(url, data=data, files=files)
            return response.json()

        except Exception as e:
            print(f"사진 전송 실패: {e}")
            return None

    def send_trade_alert(self, trade_data):
        """거래 알림"""
        message = f"""
🔔 *거래 체결*
종목: {trade_data['종목명']}
구분: {trade_data['주문구분']}
수량: {trade_data['수량']:,}
가격: {trade_data['가격']:,}
금액: {trade_data['체결금액']:,}
시간: {trade_data['시간']}
"""
        self.send_message(message)

    def send_profit_alert(self, profit_data):
        """수익 알림"""
        message = f"""
💰 *수익 발생*
종목: {profit_data['종목명']}
수익률: {profit_data['수익률']:.2f}%
수익금: {profit_data['수익금']:,}원
"""
        self.send_message(message)
```

---

## 🔊 알림 소리 (sound.py)

### 소리 재생

**소스**: 예제 코드 (실제: `utility/sound.py:4-23`)

```python
from PyQt5.QtMultimedia import QSound

class SoundPlayer:
    """알림 소리 재생"""
    def __init__(self):
        self.enabled = True
        self.sounds = {
            'buy': QSound('sounds/buy.wav'),
            'sell': QSound('sounds/sell.wav'),
            'profit': QSound('sounds/profit.wav'),
            'loss': QSound('sounds/loss.wav'),
            'alert': QSound('sounds/alert.wav'),
        }

    def play(self, sound_type):
        """소리 재생"""
        if self.enabled and sound_type in self.sounds:
            self.sounds[sound_type].play()

    def play_buy(self):
        """매수 소리"""
        self.play('buy')

    def play_sell(self):
        """매도 소리"""
        self.play('sell')

    def play_profit(self):
        """수익 소리"""
        self.play('profit')

    def play_loss(self):
        """손실 소리"""
        self.play('loss')
```

---

## 📊 코드 통계 (total_code_line.py)

### 코드 라인 계산

**소스**: 예제 코드 (실제: `utility/total_code_line.py:1-51`)

```python
import os

class CodeCounter:
    """코드 라인 카운터"""
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.extensions = ['.py']
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
        }

    def count_all(self):
        """모든 파일 카운트"""
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if any(file.endswith(ext) for ext in self.extensions):
                    file_path = os.path.join(root, file)
                    self.count_file(file_path)

        return self.stats

    def count_file(self, file_path):
        """개별 파일 카운트"""
        self.stats['total_files'] += 1

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                self.stats['total_lines'] += 1
                line = line.strip()

                if not line:
                    self.stats['blank_lines'] += 1
                elif line.startswith('#'):
                    self.stats['comment_lines'] += 1
                else:
                    self.stats['code_lines'] += 1

    def print_stats(self):
        """통계 출력"""
        print("=" * 50)
        print("코드 통계")
        print("=" * 50)
        print(f"총 파일 수: {self.stats['total_files']:,}")
        print(f"총 라인 수: {self.stats['total_lines']:,}")
        print(f"코드 라인: {self.stats['code_lines']:,}")
        print(f"주석 라인: {self.stats['comment_lines']:,}")
        print(f"빈 라인: {self.stats['blank_lines']:,}")
        print("=" * 50)
```

---

*다음: [백테스터 모듈](backtester_module.md)*
*이전: [UI 모듈](ui_module.md)*
