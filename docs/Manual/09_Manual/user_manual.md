# 09. 사용자 매뉴얼

## 📖 STOM 사용자 가이드

STOM(System Trading Operation Manager)은 **고성능 시스템 트레이딩**을 위한 통합 플랫폼입니다. 이 매뉴얼은 초보자부터 전문가까지 STOM을 효과적으로 사용할 수 있도록 단계별 가이드를 제공합니다.

---

## 🚀 시작하기

### 시스템 요구사항

#### 최소 요구사항
- **OS**: Windows 10 이상
- **RAM**: 8GB 이상
- **CPU**: Intel i5 또는 AMD Ryzen 5 이상
- **저장공간**: 10GB 이상
- **네트워크**: 안정적인 인터넷 연결

#### 권장 요구사항
- **OS**: Windows 11
- **RAM**: 16GB 이상
- **CPU**: Intel i7 또는 AMD Ryzen 7 이상
- **저장공간**: SSD 50GB 이상
- **네트워크**: 광대역 인터넷 (100Mbps 이상)

### 설치 및 초기 설정

#### 1. 프로그램 설치
```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/STOM.git
cd STOM

# 2. 가상환경 생성
python -m venv venv
venv\Scripts\activate

# 3. 의존성 설치 (64비트 Python 사용)
pip_install_64.bat
# 또는
pip install -r requirements_64bit.txt

# 4. 데이터베이스 무결성 검사 (자동 실행됨)
python64 utility/database_check.py
```

#### 2. API 키 설정
STOM은 API 키를 암호화하여 데이터베이스에 저장합니다. GUI를 통해 설정하거나 `utility/setting.py`에서 관리됩니다.

**GUI를 통한 설정**:
1. 프로그램 실행 후 `설정` 탭 선택
2. 각 거래소별 API 키 입력
3. 키는 자동으로 암호화되어 `_database/setting.db`에 저장됨

**프로그래밍 방식 설정** (`utility/setting.py` 참조):
```python
# utility/setting.py에서 암호화된 형태로 관리
DICT_SET = {
    '증권사': '키움증권',
    '거래소': '업비트',
    # API 키는 암호화되어 데이터베이스에 저장
}
```

#### 3. 데이터베이스 초기화
```bash
# 데이터베이스 무결성 검사 및 자동 생성
python64 utility/database_check.py

# 과거 데이터 업데이트 (선택사항)
python64 utility/db_update_back.py
python64 utility/db_update_day.py
```

---

## 🖥️ 메인 인터페이스

### 프로그램 실행

#### 1. 배치 파일을 통한 실행 (권장)
```bash
# 기본 실행 (관리자 권한 필요)
stom.bat

# 주식 전용 모드
stom_stock.bat

# 암호화폐 전용 모드
stom_coin.bat
```

#### 2. Python 직접 실행
```bash
# 기본 실행
python64 stom.py

# 주식 자동 실행 모드
python64 stom.py stock

# 암호화폐 자동 실행 모드
python64 stom.py coin
```

**참고**: STOM은 64비트 Python이 필요하며, 관리자 권한으로 실행해야 합니다.

### 메인 화면 구성

#### 1. 상단 메뉴바
- **파일**: 설정 저장/불러오기, 프로그램 종료
- **거래**: 계좌 연결, 주문 관리, 포지션 확인
- **분석**: 차트 분석, 백테스팅, 성과 분석
- **도구**: 데이터 관리, 로그 확인, 시스템 모니터링
- **도움말**: 사용자 매뉴얼, 버전 정보

#### 2. 좌측 패널 - 종목 관리
```
📊 관심종목
├── 주식
│   ├── 삼성전자 (005930)
│   ├── SK하이닉스 (000660)
│   └── NAVER (035420)
├── 코인
│   ├── BTC-KRW
│   ├── ETH-KRW
│   └── XRP-KRW
└── 선물/옵션
    ├── KOSPI200 선물
    └── 달러 선물
```

#### 3. 중앙 패널 - 차트 및 분석
- **실시간 차트**: 캔들스틱, 거래량, 기술지표
- **호가창**: 실시간 매수/매도 호가
- **체결창**: 실시간 체결 내역
- **뉴스**: 종목 관련 뉴스 및 공시

#### 4. 우측 패널 - 거래 및 모니터링
- **주문 입력**: 매수/매도 주문
- **계좌 정보**: 잔고, 수익률, 포지션
- **전략 상태**: 실행 중인 전략 모니터링
- **로그**: 시스템 로그 및 거래 내역

---

## 📈 차트 분석 기능

### 차트 기본 조작

#### 1. 차트 확대/축소
- **마우스 휠**: 시간축 확대/축소
- **Ctrl + 마우스 휠**: 가격축 확대/축소
- **드래그**: 차트 이동
- **더블클릭**: 자동 맞춤

#### 2. 시간 프레임 변경
```python
# 지원하는 시간 프레임
timeframes = [
    '1분', '3분', '5분', '10분', '15분', '30분',
    '1시간', '4시간', '일봉', '주봉', '월봉'
]
```

#### 3. 기술지표 추가
```python
# 주요 기술지표
indicators = {
    '이동평균': ['SMA', 'EMA', 'WMA'],
    '오실레이터': ['RSI', 'MACD', 'Stochastic'],
    '밴드': ['Bollinger Bands', 'Envelope'],
    '거래량': ['Volume', 'OBV', 'Volume Profile']
}
```

### 차트 분석 도구

#### 1. 그리기 도구
- **추세선**: 지지/저항선 그리기
- **수평선**: 주요 가격대 표시
- **피보나치**: 되돌림/확장 분석
- **패턴**: 삼각형, 웨지, 채널 등

#### 2. 측정 도구
- **거리 측정**: 가격/시간 거리 측정
- **각도 측정**: 추세선 각도 계산
- **수익률 계산**: 구간별 수익률 분석

---

## 💰 거래 기능

### 수동 거래

#### 1. 주문 입력
```python
# 주문 입력 예시
order_info = {
    'symbol': '005930',      # 종목코드
    'order_type': 'BUY',     # 매수/매도
    'price_type': 'LIMIT',   # 지정가/시장가
    'quantity': 100,         # 수량
    'price': 75000          # 가격 (지정가의 경우)
}
```

#### 2. 주문 유형
- **지정가 주문**: 원하는 가격에 주문
- **시장가 주문**: 현재 시장가로 즉시 체결
- **조건부 주문**: 특정 조건 만족 시 주문
- **예약 주문**: 지정된 시간에 주문

#### 3. 주문 관리
- **주문 수정**: 가격/수량 변경
- **주문 취소**: 미체결 주문 취소
- **일괄 취소**: 모든 미체결 주문 취소

### 자동 거래 (전략)

#### 1. 전략 설정
```python
# 이동평균 전략 설정 예시
strategy_config = {
    'name': 'MA_Cross_Strategy',
    'symbol': '005930',
    'timeframe': '5m',
    'parameters': {
        'short_ma': 5,
        'long_ma': 20,
        'position_size': 0.1,  # 계좌의 10%
        'stop_loss': 0.02,     # 2% 손절
        'take_profit': 0.04    # 4% 익절
    }
}
```

#### 2. 전략 실행
```python
# 전략 시작
strategy_manager.start_strategy('MA_Cross_Strategy')

# 전략 중지
strategy_manager.stop_strategy('MA_Cross_Strategy')

# 전략 상태 확인
status = strategy_manager.get_strategy_status('MA_Cross_Strategy')
```

#### 3. 리스크 관리
```python
# 리스크 설정
risk_config = {
    'max_position_size': 1000000,    # 최대 포지션 크기
    'max_daily_loss': 100000,        # 일일 최대 손실
    'max_drawdown': 0.1,             # 최대 드로우다운 10%
    'position_limit': 5              # 최대 동시 포지션 수
}
```

---

## 🔍 백테스팅

### 백테스팅 설정

#### 1. 기본 설정
```python
backtest_config = {
    'start_date': '2023-01-01',
    'end_date': '2023-12-31',
    'initial_capital': 10000000,
    'commission': 0.0015,
    'slippage': 0.001
}
```

#### 2. 전략 백테스팅
```python
# 백테스팅 실행
from backtester.backengine import BacktestEngine

engine = BacktestEngine()
result = engine.run_backtest(
    strategy=my_strategy,
    symbol='005930',
    start_date='2023-01-01',
    end_date='2023-12-31'
)

# 결과 확인
print(f"총 수익률: {result['total_return']:.2%}")
print(f"샤프 비율: {result['sharpe_ratio']:.2f}")
print(f"최대 드로우다운: {result['max_drawdown']:.2%}")
```

### 성과 분석

#### 1. 수익률 분석
- **총 수익률**: 전체 기간 수익률
- **연율화 수익률**: 연간 기준 수익률
- **월별 수익률**: 월별 성과 분석
- **일별 수익률**: 일별 변동성 분석

#### 2. 리스크 분석
- **변동성**: 수익률의 표준편차
- **샤프 비율**: 위험 대비 수익률
- **최대 드로우다운**: 최대 손실 구간
- **VaR**: 위험가치 측정

#### 3. 거래 분석
- **총 거래 횟수**: 매매 빈도
- **승률**: 수익 거래 비율
- **평균 수익/손실**: 거래당 평균 손익
- **수익 팩터**: 총수익/총손실 비율

---

## 📊 데이터 관리

### 데이터 수집

#### 1. 실시간 데이터
```python
# 실시간 데이터 수집 시작
data_collector.start_real_time_collection([
    '005930',  # 삼성전자
    '000660',  # SK하이닉스
    'BTC-KRW', # 비트코인
    'ETH-KRW'  # 이더리움
])
```

#### 2. 과거 데이터
```python
# 과거 데이터 다운로드
data_downloader.download_historical_data(
    symbol='005930',
    start_date='2020-01-01',
    end_date='2023-12-31',
    timeframe='1d'
)
```

### 데이터베이스 관리

#### 1. 데이터 조회
```python
# 주식 데이터 조회
stock_data = db_manager.get_stock_data(
    symbol='005930',
    start_date='2023-01-01',
    end_date='2023-12-31',
    timeframe='1d'
)

# 코인 데이터 조회
coin_data = db_manager.get_coin_data(
    market='BTC-KRW',
    start_date='2023-01-01',
    end_date='2023-12-31',
    timeframe='1h'
)
```

#### 2. 데이터 정리
```python
# 중복 데이터 제거
db_manager.remove_duplicates()

# 오래된 데이터 아카이브
db_manager.archive_old_data(days=365)

# 데이터베이스 최적화
db_manager.optimize_database()
```

---

## ⚙️ 설정 및 커스터마이징

### 시스템 설정

#### 1. 일반 설정
```python
# config/settings.py
SETTINGS = {
    'ui': {
        'theme': 'dark',           # 테마 (dark/light)
        'language': 'ko',          # 언어 (ko/en)
        'auto_save': True,         # 자동 저장
        'save_interval': 300       # 저장 간격 (초)
    },
    'trading': {
        'confirm_orders': True,    # 주문 확인
        'auto_login': False,       # 자동 로그인
        'max_orders': 100,         # 최대 주문 수
        'order_timeout': 30        # 주문 타임아웃 (초)
    },
    'data': {
        'real_time': True,         # 실시간 데이터
        'save_tick_data': True,    # 틱 데이터 저장
        'compression': True,       # 데이터 압축
        'backup_interval': 3600    # 백업 간격 (초)
    }
}
```

#### 2. 알림 설정
```python
# 알림 설정
notification_config = {
    'email': {
        'enabled': True,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': 'your_email@gmail.com',
        'password': 'your_password'
    },
    'telegram': {
        'enabled': True,
        'bot_token': 'YOUR_BOT_TOKEN',
        'chat_id': 'YOUR_CHAT_ID'
    },
    'events': {
        'order_filled': True,      # 주문 체결 알림
        'strategy_signal': True,   # 전략 신호 알림
        'error_occurred': True,    # 오류 발생 알림
        'daily_report': True       # 일일 리포트 알림
    }
}
```

### 사용자 정의 전략

#### 1. 전략 템플릿
```python
# strategies/custom_strategy.py
from strategy_base import StrategyBase

class CustomStrategy(StrategyBase):
    def __init__(self, symbol, **params):
        super().__init__("Custom_Strategy", symbol, "5m")
        self.param1 = params.get('param1', 10)
        self.param2 = params.get('param2', 20)
        
    def calculate_signals(self, data):
        # 여기에 사용자 정의 로직 구현
        # 매수 신호: return 'BUY'
        # 매도 신호: return 'SELL'
        # 신호 없음: return None
        pass
        
    def on_tick(self, tick_data):
        # 틱 데이터 처리 로직
        pass
        
    def on_order_filled(self, order_info):
        # 주문 체결 시 처리 로직
        pass
```

#### 2. 지표 추가
```python
# indicators/custom_indicator.py
import numpy as np

def custom_indicator(data, period=14):
    """사용자 정의 지표"""
    # 지표 계산 로직 구현
    result = []
    for i in range(len(data)):
        if i >= period - 1:
            # 계산 로직
            value = np.mean(data[i-period+1:i+1])
            result.append(value)
        else:
            result.append(None)
    return result
```

---

## 🔧 문제 해결

### 일반적인 문제

#### 1. 연결 문제
**문제**: API 연결 실패
```
해결방법:
1. 인터넷 연결 확인
2. API 키 유효성 확인
3. 방화벽 설정 확인
4. 프로그램 재시작
```

**문제**: 데이터 수신 중단
```
해결방법:
1. 네트워크 상태 확인
2. 서버 상태 확인
3. 실시간 등록 재시도
4. 프로그램 재시작
```

#### 2. 성능 문제
**문제**: 프로그램 느림
```
해결방법:
1. 메모리 사용량 확인
2. 불필요한 프로세스 종료
3. 데이터베이스 최적화
4. 하드웨어 업그레이드 고려
```

**문제**: 높은 CPU 사용률
```
해결방법:
1. 실시간 등록 종목 수 줄이기
2. 차트 업데이트 주기 조정
3. 백그라운드 작업 최적화
4. 멀티코어 활용 설정
```

### 로그 확인

#### 1. 로그 파일 위치
```
logs/
├── system.log          # 시스템 로그
├── trading.log         # 거래 로그
├── error.log           # 오류 로그
└── strategy.log        # 전략 로그
```

#### 2. 로그 레벨 설정
```python
# config/logging_config.py
LOGGING_CONFIG = {
    'level': 'INFO',        # DEBUG, INFO, WARNING, ERROR
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'max_file_size': '10MB',
    'backup_count': 5
}
```

---

## 📞 지원 및 문의

### 기술 지원
- **이메일**: support@stom.com
- **전화**: 02-1234-5678
- **운영시간**: 평일 09:00-18:00

### 커뮤니티
- **공식 포럼**: https://forum.stom.com
- **Discord**: https://discord.gg/stom
- **GitHub**: https://github.com/stom-trading

### 업데이트 정보
- **공식 웹사이트**: https://www.stom.com
- **릴리즈 노트**: https://github.com/stom-trading/releases
- **블로그**: https://blog.stom.com

---

## 📚 추가 자료

### 학습 자료
- **초보자 가이드**: [링크]
- **전략 개발 튜토리얼**: [링크]
- **API 문서**: [링크]
- **비디오 강의**: [링크]

### 샘플 코드
- **기본 전략 예제**: [링크]
- **백테스팅 예제**: [링크]
- **데이터 분석 예제**: [링크]
- **커스텀 지표 예제**: [링크]

---

*이 매뉴얼은 STOM v1.0 기준으로 작성되었습니다. 최신 정보는 공식 웹사이트를 참조하세요.* 