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

#### 1. 데이터베이스 구조 (`utility/setting.py:31-49`)

**소스**: 예제 코드

```python
# 데이터베이스 경로 설정
OPENAPI_PATH       = 'C:/OpenAPI'
ICON_PATH          = './icon'
LOGIN_PATH         = './stock/login_kiwoom'
GRAPH_PATH         = './backtester/graph'
BACK_TEMP          = './backtester/temp'
DB_PATH            = './_database'
DB_SETTING         = './_database/setting.db'
DB_BACKTEST        = './_database/backtest.db'
DB_TRADELIST       = './_database/tradelist.db'
DB_STOCK_TICK      = './_database/stock_tick.db'
DB_STOCK_MIN       = './_database/stock_min.db'
DB_STOCK_BACK_TICK = './_database/stock_tick_back.db'
DB_STOCK_BACK_MIN  = './_database/stock_min_back.db'
DB_COIN_TICK       = './_database/coin_tick.db'
DB_COIN_MIN        = './_database/coin_min.db'
DB_COIN_BACK_TICK  = './_database/coin_tick_back.db'
DB_COIN_BACK_MIN   = './_database/coin_min_back.db'
DB_STRATEGY        = './_database/strategy.db'
DB_OPTUNA          = 'sqlite:///./_database/optuna.db'
```

**데이터베이스 파일 목록:**
- **설정 DB**: `setting.db` - 시스템 설정 및 암호화된 계정 정보
- **거래 DB**: `tradelist.db` - 체결, 잔고, 거래 내역
- **전략 DB**: `strategy.db` - 매매 전략 코드 및 조건식
- **백테스트 DB**: `backtest.db` - 백테스팅 결과 데이터
- **주식 데이터 DB**: `stock_tick.db`, `stock_min.db` - 실시간 주식 시장 데이터
- **암호화폐 데이터 DB**: `coin_tick.db`, `coin_min.db` - 실시간 암호화폐 시장 데이터
- **백테스트용 DB**: `stock_tick_back.db`, `stock_min_back.db`, `coin_tick_back.db`, `coin_min_back.db`
- **최적화 DB**: `optuna.db` - Optuna 최적화 결과

#### 2. 테이블 스키마 설계 (`utility/database_check.py`)

##### 설정 DB 테이블 (`setting.db`)

**main 테이블** - 시스템 주요 설정

**소스**: 예제 코드

```python
columns = [
    'index', '증권사', '주식리시버', '주식트레이더', '주식데이터저장', '거래소',
    '코인리시버', '코인트레이더', '코인데이터저장', '바이낸스선물고정레버리지',
    '바이낸스선물고정레버리지값', '바이낸스선물변동레버리지값', '바이낸스선물마진타입',
    '바이낸스선물포지션', '버전업', '리시버공유'
]
```

**sacc 테이블** - 주식 계정 정보 (암호화됨)

**소스**: 예제 코드

```python
columns = ["index", "아이디", "비밀번호", "인증서비밀번호", "계좌비밀번호"]
# 1~8번까지 최대 8개 계정 지원
```

**cacc 테이블** - 암호화폐 API 키 (암호화됨)

**소스**: 예제 코드

```python
columns = ["index", "Access_key", "Secret_key"]
# Upbit, Binance 등 거래소 API 키 저장
```

**stock 테이블** - 주식 거래 설정

**소스**: 예제 코드

```python
columns = [
    "index", "주식모의투자", "주식알림소리", "주식매수전략", "주식매도전략",
    "주식타임프레임", "주식평균값계산틱수", "주식최대매수종목수", "주식전략종료시간",
    "주식잔고청산", "주식프로세스종료", "주식컴퓨터종료", "주식투자금고정", "주식투자금",
    "주식손실중지", "주식손실중지수익률", "주식수익중지", "주식수익중지수익률", "주식경과틱수설정"
]
```

**coin 테이블** - 암호화폐 거래 설정

**소스**: 예제 코드

```python
columns = [
    "index", "코인모의투자", "코인알림소리", "코인매수전략", "코인매도전략",
    "코인타임프레임", "코인평균값계산틱수", "코인최대매수종목수", "코인전략종료시간",
    "코인잔고청산", "코인프로세스종료", "코인컴퓨터종료", "코인투자금고정", "코인투자금",
    "코인손실중지", "코인손실중지수익률", "코인수익중지", "코인수익중지수익률", "코인경과틱수설정"
]
```

**stockbuyorder/stocksellorder 테이블** - 주식 매수/매도 주문 설정

**소스**: 예제 코드

```python
# 매수 주문 설정: 주문구분, 분할횟수, 분할방법, 취소조건, 금지조건 등
# 매도 주문 설정: 손절수익률, 수익금 설정, 취소조건 등
```

##### 거래 DB 테이블 (`tradelist.db`) (`utility/database_check.py:244-318`)

**s_chegeollist / c_chegeollist** - 주식/코인 체결 내역

**소스**: 예제 코드

```python
query = 'CREATE TABLE "s_chegeollist" (
    "index" TEXT, "종목명" TEXT, "주문구분" TEXT, "주문수량" INTEGER,
    "체결수량" INTEGER, "미체결수량" INTEGER, "체결가" INTEGER,
    "체결시간" TEXT, "주문가격" INTEGER, "주문번호" TEXT
)'
```

**s_jangolist / c_jangolist** - 주식/코인 잔고 내역

**소스**: 예제 코드

```python
query = 'CREATE TABLE "s_jangolist" (
    "index" TEXT, "종목명" TEXT, "매입가" INTEGER, "현재가" INTEGER,
    "수익률" REAL, "평가손익" INTEGER, "매입금액" INTEGER, "평가금액" INTEGER,
    "보유수량" INTEGER, "분할매수횟수" INTEGER, "분할매도횟수" INTEGER, "매수시간" TEXT
)'
```

**c_jangolist_future** - 코인 선물 잔고 (바이낸스)

**소스**: 예제 코드

```python
query = 'CREATE TABLE "c_jangolist_future" (
    "index" TEXT, "종목명" TEXT, "포지션" TEXT, "매입가" REAL, "현재가" REAL,
    "수익률" REAL, "평가손익" INTEGER, "매입금액" INTEGER, "평가금액" INTEGER,
    "보유수량" REAL, "레버리지" INTEGER, "분할매수횟수" INTEGER,
    "분할매도횟수" INTEGER, "매수시간" TEXT
)'
```

**s_tradelist / c_tradelist** - 주식/코인 거래 내역

**소스**: 예제 코드

```python
query = 'CREATE TABLE "s_tradelist" (
    "index" TEXT, "종목명" TEXT, "매수금액" INTEGER, "매도금액" INTEGER,
    "주문수량" INTEGER, "수익률" REAL, "수익금" INTEGER, "체결시간" TEXT
)'
```

**s_totaltradelist / c_totaltradelist** - 총 거래 집계

**소스**: 예제 코드

```python
query = 'CREATE TABLE "s_totaltradelist" (
    "index" TEXT, "총매수금액" INTEGER, "총매도금액" INTEGER,
    "총수익금액" INTEGER, "총손실금액" INTEGER, "수익률" REAL, "수익금합계" INTEGER
)'
```

##### 전략 DB 테이블 (`strategy.db`) (`utility/database_check.py:166-241`)

**stockbuy/stocksell, coinbuy/coinsell** - 매매 전략 코드

**소스**: 예제 코드

```python
cur.execute('CREATE TABLE "stockbuy" ( "index" TEXT, "전략코드" TEXT )')
cur.execute('CREATE INDEX "ix_stockbuy_index" ON "stockbuy" ("index")')
```

**stockbuyconds/stocksellconds** - 매매 조건식

**소스**: 예제 코드

```python
cur.execute('CREATE TABLE "stockbuyconds" ( "index" TEXT, "전략코드" TEXT )')
```

**stockvars/coinvars** - 전략 변수

**소스**: 예제 코드

```python
cur.execute('CREATE TABLE "stockvars" ( "index" TEXT, "전략코드" TEXT )')
```

**stockoptibuy/stockoptisell** - 최적화용 전략

**소스**: 예제 코드

```python
query = 'CREATE TABLE "stockoptibuy" ( "index" TEXT, "전략코드" TEXT, "변수값" TEXT )'
```

##### 시장 데이터 DB 테이블 (동적 생성)

**moneytop 테이블** - 거래대금 순위 (모든 tick/min DB에 존재)

**소스**: 예제 코드

```python
# index: 시간 (YYYYMMDDHHMMSS)
# 거래대금순위: 세미콜론으로 구분된 종목코드/마켓 리스트
```

**[종목코드/마켓] 테이블** - 개별 종목 데이터 (동적 생성)

**소스**: 예제 코드

```python
# 주식 틱: index, 현재가, 시가, 고가, 저가, 등락률, 당일거래대금,
#          체결강도, 호가총잔량, 매수호가1~10, 매도호가1~10, 매수잔량1~10, 매도잔량1~10
# 코인 틱: index, 현재가, 시가, 고가, 저가, 등락률, 당일거래대금,
#          누적매수량, 누적매도량, 매수호가1~10, 매도호가1~10, 매수잔량1~10, 매도잔량1~10
# 분봉: index, 시가, 고가, 저가, 종가, 거래량, 거래대금
```

### 데이터베이스 연결 관리

#### 1. Query 프로세스 (`utility/query.py:12-89`)

STOM은 별도의 프로세스로 **Query** 클래스를 실행하여 모든 데이터베이스 작업을 처리합니다.

**소스**: 예제 코드

```python
class Query:
    def __init__(self, qlist):
        """
        멀티프로세스 환경에서 DB 작업을 전담하는 Query 프로세스
        - windowQ, queryQ 등의 큐를 통해 다른 프로세스와 통신
        """
        self.windowQ  = qlist[0]
        self.queryQ   = qlist[2]

        # 3개의 주요 데이터베이스 연결
        self.con1     = sqlite3.connect(DB_SETTING)     # 설정 DB
        self.cur1     = self.con1.cursor()
        self.con2     = sqlite3.connect(DB_TRADELIST)   # 거래 DB
        self.cur2     = self.con2.cursor()
        self.con3     = sqlite3.connect(DB_STRATEGY)    # 전략 DB
        self.cur3     = self.con3.cursor()

        self.dict_set = DICT_SET
        self.Start()

    def __del__(self):
        """프로세스 종료 시 모든 DB 연결 종료"""
        self.con1.close()
        self.con2.close()
        self.con3.close()

    def Start(self):
        """메인 루프: 큐에서 쿼리 요청을 받아 처리"""
        while True:
            query = self.queryQ.get()

            if query[0] == '설정변경':
                self.dict_set = query[1]

            elif query[0] == '설정디비':
                try:
                    if len(query) == 2:
                        # 직접 SQL 실행
                        self.cur1.execute(query[1])
                        self.con1.commit()
                    elif len(query) == 4:
                        # DataFrame을 SQL 테이블로 저장
                        # query[1]: DataFrame, query[2]: 테이블명, query[3]: 'append'/'replace'
                        query[1].to_sql(query[2], self.con1, if_exists=query[3], chunksize=1000)
                except Exception as e:
                    self.windowQ.put((ui_num['S로그텍스트'], f'오류 - Query 설정디비 {e}'))

            elif query[0] == '거래디비':
                try:
                    if len(query) == 2:
                        self.cur2.execute(query[1])
                        self.con2.commit()
                    elif len(query) == 4:
                        query[1].to_sql(query[2], self.con2, if_exists=query[3], chunksize=1000)
                except Exception as e:
                    ui_text = 'S로그텍스트' if 's_' in query[2] else 'C로그텍스트'
                    self.windowQ.put((ui_num[ui_text], f'오류 - Query 거래디비 {e}'))

            elif query[0] == '전략디비':
                try:
                    if len(query) == 2:
                        self.cur3.execute(query[1])
                        self.con3.commit()
                    elif len(query) == 4:
                        query[1].to_sql(query[2], self.con3, if_exists=query[3], chunksize=1000)
                except Exception as e:
                    self.windowQ.put((ui_num['S로그텍스트'], f'오류 - Query 전략디비 {e}'))

            elif query[0] == '백테디비':
                try:
                    con = sqlite3.connect(DB_BACKTEST)
                    cur = con.cursor()
                    cur.execute(query[1])
                    con.commit()
                    con.close()
                except Exception as e:
                    self.windowQ.put((ui_num['S로그텍스트'], f'오류 - Query 백테디비 {e}'))

            elif query == '프로세스종료':
                break

            self.windowQ.put((ui_num['DB관리'], 'DB업데이트완료'))
```

**사용 예시:**

**소스**: 예제 코드

```python
# 설정 DB에 데이터 저장
queryQ.put(('설정디비', df, 'codename', 'replace'))

# 거래 DB에 체결 내역 저장
queryQ.put(('거래디비', df_chegol, 's_chegeollist', 'append'))

# 직접 SQL 실행
queryQ.put(('전략디비', f"DELETE FROM stockbuy WHERE index='{strategy_name}'"))
```

#### 2. 데이터베이스 최적화 설정

SQLite 성능 최적화를 위한 PRAGMA 설정 (일반적으로 사용):

**소스**: 예제 코드

```python
conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
conn.execute("PRAGMA journal_mode=WAL")        # Write-Ahead Logging
conn.execute("PRAGMA synchronous=NORMAL")      # 동기화 모드
conn.execute("PRAGMA cache_size=10000")        # 캐시 크기
conn.execute("PRAGMA temp_store=MEMORY")       # 임시 저장소를 메모리에
```

#### 3. 데이터베이스 관리 기능 (`utility/query.py:87-256`)

Query 프로세스는 다음과 같은 DB 관리 기능을 제공합니다:

**백테DB생성**: 날짜별 DB 파일들을 하나의 백테스트용 DB로 통합

**소스**: 예제 코드

```python
elif '백테DB생성' in query[0]:
    # _database/stock_tick_20240101.db, stock_tick_20240102.db 등을
    # _database/stock_tick_back.db로 통합
```

**일자DB분리**: 당일 DB를 날짜별로 분리하여 저장

**소스**: 예제 코드

```python
elif '일자DB분리' in query[0]:
    # stock_tick.db에서 날짜별로 stock_tick_20240101.db, stock_tick_20240102.db로 분리
```

**지정시간이후삭제**: 특정 시간 이후 데이터 삭제 (디버깅/테스트용)

**소스**: 예제 코드

```python
elif '당일데이터지정시간이후삭제' in query[0]:
    # 예: 093000 이후 데이터 삭제
```

---

## 📡 실시간 데이터 수신

### 주식 데이터 수신 시스템

#### 1. Kiwoom 리시버 구조 (`stock/kiwoom_receiver_tick.py:41-118`)

**소스**: 예제 코드

```python
class KiwoomReceiverTick:
    """키움 틱 데이터 수신기 - 독립 프로세스로 실행"""

    def __init__(self, qlist):
        """
        qlist: [kwzservQ, sreceivQ, straderQ, sstgQs, ...]
        - kwzservQ: 메인 윈도우로 메시지 전송
        - sreceivQ: 내부 업데이트용 큐
        - straderQ: 트레이더 프로세스로 데이터 전송
        - sstgQs: 전략 프로세스들로 데이터 전송
        """
        app = QApplication(sys.argv)

        self.kwzservQ = qlist[0]
        self.sreceivQ = qlist[1]
        self.straderQ = qlist[2]
        self.sstgQs   = qlist[3]
        self.dict_set = DICT_SET

        # 데이터 저장용 딕셔너리
        self.dict_name   = {}  # {종목코드: 종목명}
        self.dict_code   = {}  # {종목명: 종목코드}
        self.dict_data   = {}  # {종목코드: 실시간 데이터}
        self.dict_mtop   = {}  # {시간: 거래대금 순위}

        # Kiwoom API 객체 생성 및 로그인
        self.kw = Kiwoom(self, 'Receiver')
        self.KiwoomLogin()

        # ZMQ 서버 시작 (리시버 공유 모드)
        if self.dict_set['리시버공유'] == 1:
            self.zmqserver = ZmqServ(self.recvservQ)
            self.zmqserver.start()

        # 업데이터 스레드 시작
        self.updater = Updater(self.sreceivQ)
        self.updater.signal.connect(self.UpdateTuple)
        self.updater.start()

        # 스케줄러 타이머
        self.qtimer = QTimer()
        self.qtimer.setInterval(1 * 1000)
        self.qtimer.timeout.connect(self.Scheduler)
        self.qtimer.start()

        app.exec_()

    def KiwoomLogin(self):
        """키움 로그인 및 초기 데이터 로드"""
        self.kw.CommConnect()  # 로그인
        qtest_qwait(5)
        self.kw.GetConditionLoad()  # 조건검색식 로드

        # 코스닥, 코스피, ETF 종목 리스트
        self.tuple_kosd = tuple(self.kw.GetCodeListByMarket('10'))
        list_code = (self.kw.GetCodeListByMarket('0') +    # 코스피
                     self.kw.GetCodeListByMarket('8') +    # ETF
                     list(self.tuple_kosd))                # 코스닥

        # 종목 구분 번호 (전략 분산용)
        self.dict_sgbn = {code: i % 8 for i, code in enumerate(list_code)}

        # 종목명 딕셔너리 생성
        self.dict_name = {code: self.kw.GetMasterCodeName(code) for code in list_code}
        self.dict_code = {name: code for code, name in self.dict_name.items()}

        # 다른 프로세스에 종목 정보 전송
        self.kwzservQ.put(('window', (ui_num['종목명데이터'],
                                      self.dict_name, self.dict_code, self.dict_sgbn, '더미')))
        self.straderQ.put(('종목구분번호', self.dict_sgbn))
        for q in self.sstgQs:
            q.put(('종목구분번호', self.dict_sgbn))
            q.put(('코스닥목록', self.tuple_kosd))

        # 종목명을 DB에 저장
        df = pd.DataFrame(self.dict_name.values(), columns=['종목명'],
                          index=list(self.dict_name.keys()))
        df['코스닥'] = [True if x in self.tuple_kosd else False for x in df.index]
        self.kwzservQ.put(('query', ('설정디비', df, 'codename', 'replace')))
```

**실시간 등록 및 데이터 처리:**

**소스**: 예제 코드

```python
# stock/kiwoom_receiver_tick.py:203-235
def OperationRealreg(self):
    """장 시작 시 실시간 데이터 등록"""
    self.dict_bool['리시버시작'] = True

    # 장운영시간 등록
    self.kw.SetRealReg([sn_oper, ' ', '215;20;214', 0])

    # 업종지수 등록
    self.kw.SetRealReg([sn_oper, '001;101', '10;15;20', 1])

    # 조건검색식으로 종목 검색 및 실시간 등록
    self.list_code = self.kw.SendCondition([sn_cond, self.list_cond[1][1],
                                            self.list_cond[1][0], 0])

    # 100개씩 묶어서 실시간 등록
    k = 0
    for i in range(0, len(self.list_code), 100):
        rreg = [sn_gsjm + k, ';'.join(self.list_code[i:i + 100]),
                '10;12;14;30;228;41;61;71;81', 1]
        self.kw.SetRealReg(rreg)
        k += 1

# stock/kiwoom_receiver_tick.py:295-320
def SaveData(self):
    """종료 시 데이터를 DB에 저장"""
    if len(self.dict_mtop) > 0:
        if self.dict_set['주식타임프레임']:
            codes = list(set(';'.join(list(self.dict_mtop.values())[29:]).split(';')))
        else:
            codes = list(set(';'.join(list(self.dict_mtop.values())).split(';')))

        # moneytop 테이블 저장
        df = pd.DataFrame({'index': list(self.dict_mtop.keys()),
                           '거래대금순위': list(self.dict_mtop.values())})
        con = sqlite3.connect(DB_STOCK_TICK if self.dict_set['주식타임프레임']
                              else DB_STOCK_MIN)
        df.to_sql('moneytop', con, index=False, if_exists='append', chunksize=1000)

        # 각 종목 데이터 저장
        last = len(codes)
        for i, code in enumerate(codes):
            if code in self.dict_data:
                df = pd.DataFrame(self.dict_data[code])
                df.to_sql(code, con, index=False, if_exists='append', chunksize=1000)
        con.close()
```

### 암호화폐 데이터 수신 시스템

#### 1. Upbit 리시버 구조 (`coin/upbit_receiver_tick.py:30-150`)

**소스**: 예제 코드

```python
class UpbitReceiverTick:
    """업비트 틱 데이터 수신기 - 독립 프로세스로 실행"""

    def __init__(self, qlist):
        """
        qlist: [windowQ, soundQ, queryQ, teleQ, chartQ, hogaQ, webcQ, backQ,
                creceivQ, ctraderQ, cstgQ, liveQ, kimpQ, wdzservQ, totalQ]
        """
        self.windowQ  = qlist[0]
        self.soundQ   = qlist[1]
        self.queryQ   = qlist[2]
        self.teleQ    = qlist[3]
        self.hogaQ    = qlist[5]
        self.creceivQ = qlist[8]  # WebSocket 수신용 큐
        self.ctraderQ = qlist[9]
        self.cstgQ    = qlist[10]
        self.dict_set = DICT_SET

        # 데이터 저장용 딕셔너리
        self.dict_tmdt   = {}  # {종목: 시간별 데이터}
        self.dict_data   = {}  # {종목: 실시간 데이터}
        self.dict_mtop   = {}  # {시간: 거래대금 순위}

        # 거래소 티커 정보 로드
        self.GetTickers()

        # WebSocket 시작
        self.WebSocketsStart(self.creceivQ)

        self.MainLoop()

    def MainLoop(self):
        """메인 루프: WebSocket에서 수신한 데이터 처리"""
        text = '코인 리시버를 시작하였습니다.'
        if self.dict_set['코인알림소리']: self.soundQ.put(text)
        self.teleQ.put(text)
        self.windowQ.put((ui_num['C단순텍스트'], '시스템 명령 실행 알림 - 리시버 시작'))

        while True:
            data = self.creceivQ.get()
            curr_time = now()

            if type(data) == tuple:
                # UI/트레이더/전략 프로세스로부터의 명령 처리
                self.UpdateTuple(data)

            elif type(data) == dict:
                # WebSocket으로부터 수신한 데이터
                if data['type'] == 'ticker':
                    try:
                        # UTC 시간을 한국 시간으로 변환 (-32400초 = -9시간)
                        dt   = int(strf_time('%Y%m%d%H%M%S',
                                             from_timestamp(int(data['timestamp'] / 1000 - 32400))))
                        if self.dict_set['코인전략종료시간'] < int(str(dt)[8:]): continue

                        code = data['code']         # KRW-BTC
                        c    = data['trade_price']  # 현재가
                        o    = data['opening_price']
                        h    = data['high_price']
                        low  = data['low_price']
                        per  = round(data['signed_change_rate'] * 100, 2)
                        tbids = data['acc_bid_volume']   # 누적매수량
                        tasks = data['acc_ask_volume']   # 누적매도량
                        dm   = data['acc_trade_price']   # 당일거래대금

                        self.UpdateTickData(code, c, o, h, low, per, dm, tbids, tasks, dt)

                    except Exception as e:
                        self.windowQ.put((ui_num['C단순텍스트'],
                                         f'시스템 명령 오류 알림 - 웹소켓 ticker {e}'))

                elif data['type'] == 'orderbook':
                    # 호가 데이터 처리
                    try:
                        dt   = int(strf_time('%Y%m%d%H%M%S',
                                             from_timestamp(int(data['timestamp'] / 1000 - 32400))))
                        code = data['code']
                        hoga_tamount = (data['total_ask_size'], data['total_bid_size'])
                        data = data['orderbook_units']

                        # 매도호가 10~1 (역순)
                        hoga_seprice = (data[9]['ask_price'], data[8]['ask_price'], ..., data[0]['ask_price'])
                        # 매수호가 1~10
                        hoga_buprice = (data[0]['bid_price'], data[1]['bid_price'], ..., data[9]['bid_price'])
                        # 매도잔량 10~1, 매수잔량 1~10
                        hoga_samount = (...)
                        hoga_bamount = (...)

                        self.UpdateHogaData(dt, hoga_tamount, hoga_seprice, hoga_buprice,
                                            hoga_samount, hoga_bamount, code, curr_time)

                    except Exception as e:
                        self.windowQ.put((ui_num['C단순텍스트'],
                                         f'시스템 명령 오류 알림 - 웹소켓 orderbook {e}'))

            elif data == '프로세스종료':
                self.SysExit()
                break

            # 1초마다 거래대금 순위 전송
            if curr_time > self.dict_time['거래대금순위전송']:
                self.UpdateMoneyTop()
                self.dict_time['거래대금순위전송'] = timedelta_sec(1)
```

**WebSocket 시작:**

**소스**: 예제 코드

```python
# coin/upbit_receiver_tick.py
def WebSocketsStart(self, creceivQ):
    """Upbit WebSocket 프로세스 시작"""
    codes = [x for x in self.dict_daym.keys()]  # 거래 가능한 종목 리스트
    self.proc_webs = Process(target=WebSocketReceiver, args=(creceivQ, codes), daemon=True)
    self.proc_webs.start()

# coin/upbit_websocket.py
class WebSocketReceiver:
    """Upbit WebSocket 전담 프로세스"""
    async def connect_websocket(self):
        uri = "wss://api.upbit.com/websocket/v1"
        async with websockets.connect(uri) as websocket:
            subscribe_msg = [
                {"ticket": "stom"},
                {"type": "ticker", "codes": self.codes},
                {"type": "orderbook", "codes": self.codes}
            ]
            await websocket.send(json.dumps(subscribe_msg))

            while True:
                data = await websocket.recv()
                data = json.loads(data.decode('utf-8'))
                self.recvQ.put(data)  # 메인 리시버로 데이터 전송
```

#### 2. Binance 리시버 구조 (`coin/binance_receiver_tick.py:31-100`)

**소스**: 예제 코드

```python
class BinanceReceiverTick:
    """바이낸스 선물 틱 데이터 수신기"""

    def __init__(self, qlist):
        self.windowQ  = qlist[0]
        self.creceivQ = qlist[8]
        self.ctraderQ = qlist[9]
        self.cstgQ    = qlist[10]
        self.binance  = binance.Client()  # 바이낸스 API 클라이언트

        # 거래 가능한 선물 종목 로드
        self.codes = self.GetTickers()

        # WebSocket 시작
        self.WebSocketsStart(self.creceivQ)
        self.MainLoop()

    def MainLoop(self):
        """메인 루프: WebSocket 데이터 처리"""
        while True:
            data = self.creceivQ.get()

            if type(data) == list:
                if data[0] == 'trade':
                    # 실시간 체결 데이터
                    code = data[1]['s']  # BTCUSDT
                    c = float(data[1]['p'])  # 체결가
                    # ... 데이터 처리 ...

                elif data[0] == 'depth':
                    # 호가 데이터
                    code = data[1]['s']
                    asks = data[1]['a']  # [[price, qty], ...]
                    bids = data[1]['b']
                    # ... 호가 처리 ...

            elif type(data) == tuple:
                self.UpdateTuple(data)

            elif data == '프로세스종료':
                self.SysExit()
                break
```

---

## 🔄 데이터 전처리 및 검증

STOM 시스템은 실시간 데이터 수신 시 자동으로 데이터 전처리와 검증을 수행합니다.

### 데이터 정제 및 필터링

**주식 데이터 전처리** (`stock/kiwoom_receiver_tick.py`):
- 가격 데이터 절댓값 변환
- VI(변동성완화장치) 발동 종목 처리
- 상한가/하한가 정보 계산 및 저장
- 거래정지 종목 필터링
- 블랙리스트 종목 제외

**암호화폐 데이터 전처리** (`coin/upbit_receiver_tick.py`, `coin/binance_receiver_tick.py`):
- UTC 시간 → KST 시간 변환 (-32400초)
- 소수점 정밀도 조정
- 거래량 0인 종목 필터링
- 거래 정지 마켓 제외

### 거래대금 순위 기반 필터링

**소스**: 예제 코드

```python
# 거래대금 상위 종목만 DB에 저장 (메모리/스토리지 최적화)
# 틱 모드: 거래대금 순위 30위 이후 종목만 저장
# 분봉 모드: 모든 거래대금 순위 종목 저장
```

### 데이터 검증 시스템 (학습용 예제)

실시간 데이터의 품질을 보장하기 위한 검증 시스템 예제입니다:

**소스**: 예제 코드

```python
class DataValidator:
    """데이터 검증 클래스 - 실시간 데이터 품질 관리"""

    def __init__(self):
        # 데이터 유형별 검증 규칙 정의
        self.validation_rules = {
            'stock_tick': {
                'current_price': {'min': 1, 'max': 1000000, 'type': int},
                'volume': {'min': 0, 'max': 999999999, 'type': int},
                'change_rate': {'min': -30.0, 'max': 30.0, 'type': float}
            },
            'coin_tick': {
                'trade_price': {'min': 0.0001, 'max': 1000000, 'type': float},
                'trade_volume': {'min': 0, 'max': 999999999, 'type': float},
                'change_rate': {'min': -50.0, 'max': 50.0, 'type': float}
            }
        }

    def validate_data(self, data_type, data):
        """데이터 검증 - 규칙 기반 유효성 확인"""
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
        """데이터 정제 - 비정상 데이터 보정"""
        if data_type == 'stock_tick':
            # 가격 데이터 절댓값 처리 (키움 API는 음수로 하락 표시)
            if 'current_price' in data:
                data['current_price'] = abs(data['current_price'])

            # 거래량 0 이하 값 처리
            if 'volume' in data and data['volume'] <= 0:
                data['volume'] = 0

            # 등락률 범위 제한
            if 'change_rate' in data:
                data['change_rate'] = max(-30.0, min(30.0, data['change_rate']))

        elif data_type == 'coin_tick':
            # 소수점 정밀도 조정 (비트코인 등은 8자리까지)
            if 'trade_price' in data:
                data['trade_price'] = round(data['trade_price'], 8)

            # 거래량 정밀도
            if 'trade_volume' in data:
                data['trade_volume'] = round(data['trade_volume'], 8)

        return data

# 사용 예시
validator = DataValidator()

# 주식 틱 데이터 검증
stock_data = {
    'code': '005930',
    'current_price': 75000,
    'volume': 1000000,
    'change_rate': 2.5
}
is_valid, errors = validator.validate_data('stock_tick', stock_data)
if is_valid:
    cleaned_data = validator.clean_data('stock_tick', stock_data)
    print("검증 통과:", cleaned_data)
else:
    print("검증 실패:", errors)
```

### 이상치 탐지 시스템 (학습용 예제)

통계적 방법을 사용한 이상치 탐지 예제입니다:

**소스**: 예제 코드

```python
from collections import deque
import numpy as np

class OutlierDetector:
    """이상치 탐지 클래스 - Z-score 기반"""

    def __init__(self, window_size=100):
        """
        Args:
            window_size: 이동 평균 계산 윈도우 크기
        """
        self.window_size = window_size
        self.price_history = {}  # {종목코드: 가격 히스토리}
        self.volume_history = {}  # {종목코드: 거래량 히스토리}

    def detect_price_outlier(self, symbol, current_price):
        """
        가격 이상치 탐지 - Z-score 방식

        Z-score = (X - μ) / σ
        - X: 현재 가격
        - μ: 평균 가격
        - σ: 표준편차

        일반적으로 |Z-score| > 3 이면 이상치로 판단
        """
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.window_size)

        history = self.price_history[symbol]

        # 최소 데이터 필요 (통계적 신뢰성)
        if len(history) < 10:
            history.append(current_price)
            return False, 0.0

        # 통계값 계산
        mean_price = np.mean(history)
        std_price = np.std(history)

        if std_price == 0:  # 표준편차가 0이면 모든 값이 동일
            history.append(current_price)
            return False, 0.0

        # Z-score 계산
        z_score = abs((current_price - mean_price) / std_price)

        # Z-score > 3이면 이상치로 판단 (99.7% 신뢰구간 초과)
        is_outlier = z_score > 3

        if not is_outlier:
            history.append(current_price)

        return is_outlier, z_score

    def detect_volume_spike(self, symbol, current_volume):
        """
        거래량 급증 탐지

        평균 거래량의 5배 이상이면 급증으로 판단
        (테마주, 뉴스 등의 영향)
        """
        if symbol not in self.volume_history:
            self.volume_history[symbol] = deque(maxlen=self.window_size)

        history = self.volume_history[symbol]

        if len(history) < 10:
            history.append(current_volume)
            return False, 0.0

        avg_volume = np.mean(history)

        if avg_volume == 0:
            history.append(current_volume)
            return False, 0.0

        # 거래량 배수 계산
        volume_ratio = current_volume / avg_volume

        # 평균의 5배 이상이면 급증
        is_spike = volume_ratio > 5.0

        history.append(current_volume)
        return is_spike, volume_ratio

# 사용 예시
detector = OutlierDetector(window_size=100)

# 실시간 데이터 처리
for tick in real_time_data:
    # 가격 이상치 검사
    is_outlier, z_score = detector.detect_price_outlier(
        tick['code'],
        tick['current_price']
    )
    if is_outlier:
        print(f"가격 이상치 감지: {tick['code']}, Z-score: {z_score:.2f}")

    # 거래량 급증 검사
    is_spike, ratio = detector.detect_volume_spike(
        tick['code'],
        tick['volume']
    )
    if is_spike:
        print(f"거래량 급증: {tick['code']}, 배수: {ratio:.2f}배")
```

---

## 📈 시계열 데이터 처리

### 틱/분봉 데이터 집계

STOM은 틱 데이터와 분봉 데이터를 별도로 수집하고 저장합니다.

**틱 데이터** (`주식타임프레임=1`, `코인타임프레임=1`):
- 실시간 체결 발생 시마다 데이터 저장
- 시간: YYYYMMDDHHMMSS (초 단위)

**분봉 데이터** (`주식타임프레임=0`, `코인타임프레임=0`):
- 1분마다 OHLCV 데이터 생성 및 저장
- 시간: YYYYMMDDHHMM00 (분 단위, 초는 00 고정)

**기술적 지표 계산**:
- 전략 프로세스(`*_strategy_*.py`)에서 필요한 지표 계산
- TA-Lib 라이브러리 활용
- 이동평균, RSI, MACD, 볼린저밴드 등

### OHLCV 데이터 집계 시스템 (학습용 예제)

틱 데이터를 시간프레임별 OHLCV 캔들로 집계하는 예제입니다:

**소스**: 예제 코드

```python
from datetime import datetime
from collections import defaultdict

class OHLCVAggregator:
    """OHLCV 데이터 집계기 - 틱을 캔들로 변환"""

    def __init__(self):
        self.tick_buffers = {}  # {종목: {시간프레임: [틱데이터]}}
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']

    def add_tick(self, symbol, tick_data):
        """
        틱 데이터 추가 및 집계 체크

        Args:
            symbol: 종목코드 또는 마켓
            tick_data: {'price': 가격, 'volume': 거래량, 'timestamp': 시간}
        """
        if symbol not in self.tick_buffers:
            self.tick_buffers[symbol] = {tf: [] for tf in self.timeframes}

        # 모든 시간프레임 버퍼에 틱 추가
        for timeframe in self.timeframes:
            self.tick_buffers[symbol][timeframe].append(tick_data)

        # 시간프레임별 집계 필요 여부 확인
        self.check_aggregation(symbol, tick_data['timestamp'])

    def check_aggregation(self, symbol, timestamp):
        """집계 시점 확인 및 실행"""
        for timeframe in self.timeframes:
            if self.should_aggregate(timeframe, timestamp):
                ohlcv = self.aggregate_ticks(symbol, timeframe)
                if ohlcv:
                    self.save_ohlcv(symbol, timeframe, ohlcv)
                    # 버퍼 클리어
                    self.tick_buffers[symbol][timeframe] = []

    def should_aggregate(self, timeframe, timestamp):
        """
        집계 필요 여부 판단

        Args:
            timeframe: 시간프레임 ('1m', '5m', etc.)
            timestamp: 현재 시간

        Returns:
            bool: 집계 필요 여부
        """
        if timeframe == '1m':
            # 분이 바뀌면 집계 (00초)
            return timestamp.second == 0

        elif timeframe == '5m':
            # 5분마다 집계 (0, 5, 10, 15, ... 분의 00초)
            return timestamp.minute % 5 == 0 and timestamp.second == 0

        elif timeframe == '15m':
            # 15분마다 집계
            return timestamp.minute % 15 == 0 and timestamp.second == 0

        elif timeframe == '1h':
            # 1시간마다 집계 (매 시 00분 00초)
            return timestamp.minute == 0 and timestamp.second == 0

        elif timeframe == '4h':
            # 4시간마다 집계 (0, 4, 8, 12, 16, 20시)
            return (timestamp.hour % 4 == 0 and
                    timestamp.minute == 0 and
                    timestamp.second == 0)

        elif timeframe == '1d':
            # 일봉 집계 (00:00:00)
            return (timestamp.hour == 0 and
                    timestamp.minute == 0 and
                    timestamp.second == 0)

        return False

    def aggregate_ticks(self, symbol, timeframe):
        """
        틱 데이터를 OHLCV로 집계

        Returns:
            dict: {'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume', 'timestamp'}
        """
        ticks = self.tick_buffers[symbol][timeframe]

        if not ticks:
            return None

        # 가격과 거래량 추출
        prices = [tick['price'] for tick in ticks]
        volumes = [tick['volume'] for tick in ticks]

        # OHLCV 생성
        ohlcv = {
            'symbol': symbol,
            'timeframe': timeframe,
            'open': prices[0],           # 첫 거래 가격
            'high': max(prices),          # 최고가
            'low': min(prices),           # 최저가
            'close': prices[-1],          # 마지막 거래 가격
            'volume': sum(volumes),       # 누적 거래량
            'timestamp': self.get_candle_timestamp(ticks[0]['timestamp'], timeframe)
        }

        return ohlcv

    def get_candle_timestamp(self, timestamp, timeframe):
        """
        캔들 타임스탬프 계산 - 시간프레임 시작 시간

        예: 09:03:45의 1분봉 타임스탬프 = 09:03:00
        """
        if timeframe == '1m':
            return timestamp.replace(second=0, microsecond=0)

        elif timeframe == '5m':
            # 5분 단위로 내림
            minute = (timestamp.minute // 5) * 5
            return timestamp.replace(minute=minute, second=0, microsecond=0)

        elif timeframe == '15m':
            minute = (timestamp.minute // 15) * 15
            return timestamp.replace(minute=minute, second=0, microsecond=0)

        elif timeframe == '1h':
            return timestamp.replace(minute=0, second=0, microsecond=0)

        elif timeframe == '4h':
            hour = (timestamp.hour // 4) * 4
            return timestamp.replace(hour=hour, minute=0, second=0, microsecond=0)

        elif timeframe == '1d':
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

    def save_ohlcv(self, symbol, timeframe, ohlcv):
        """OHLCV 데이터를 DB에 저장"""
        # 실제 구현에서는 DB 저장
        print(f"OHLCV 저장: {symbol} {timeframe} {ohlcv}")

# 사용 예시
aggregator = OHLCVAggregator()

# 실시간 틱 데이터 수신 시뮬레이션
sample_ticks = [
    {'price': 75000, 'volume': 100, 'timestamp': datetime(2024, 1, 1, 9, 0, 0)},
    {'price': 75100, 'volume': 150, 'timestamp': datetime(2024, 1, 1, 9, 0, 15)},
    {'price': 75200, 'volume': 200, 'timestamp': datetime(2024, 1, 1, 9, 0, 30)},
    {'price': 75050, 'volume': 180, 'timestamp': datetime(2024, 1, 1, 9, 0, 45)},
    {'price': 75150, 'volume': 120, 'timestamp': datetime(2024, 1, 1, 9, 1, 0)},  # 1분 경계
]

for tick in sample_ticks:
    aggregator.add_tick('005930', tick)
```

### 기술적 지표 계산 (학습용 예제)

주요 기술적 지표 계산 예제입니다:

**소스**: 예제 코드

```python
import numpy as np

class TechnicalIndicators:
    """기술적 지표 계산 클래스"""

    @staticmethod
    def simple_moving_average(prices, period):
        """
        단순 이동평균 (SMA - Simple Moving Average)

        SMA = (P1 + P2 + ... + Pn) / n

        Args:
            prices: 가격 리스트
            period: 기간

        Returns:
            float: SMA 값
        """
        if len(prices) < period:
            return None

        return sum(prices[-period:]) / period

    @staticmethod
    def exponential_moving_average(prices, period, alpha=None):
        """
        지수 이동평균 (EMA - Exponential Moving Average)

        EMA_today = α × Price_today + (1-α) × EMA_yesterday
        α = 2 / (period + 1)

        최근 데이터에 더 높은 가중치 부여

        Args:
            prices: 가격 리스트
            period: 기간
            alpha: 평활 계수 (기본값: 2/(period+1))

        Returns:
            float: EMA 값
        """
        if len(prices) < 1:
            return None

        if alpha is None:
            alpha = 2 / (period + 1)

        ema = prices[0]
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema

        return ema

    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        """
        볼린저 밴드 (Bollinger Bands)

        Middle Band = SMA(20)
        Upper Band = Middle Band + (2 × σ)
        Lower Band = Middle Band - (2 × σ)

        가격 변동성 측정 및 과매수/과매도 판단

        Args:
            prices: 가격 리스트
            period: 기간 (기본 20)
            std_dev: 표준편차 배수 (기본 2)

        Returns:
            tuple: (상단밴드, 중간밴드, 하단밴드)
        """
        if len(prices) < period:
            return None, None, None

        # 중간 밴드 (SMA)
        sma = TechnicalIndicators.simple_moving_average(prices, period)

        # 표준편차 계산
        std = np.std(prices[-period:])

        # 상단/하단 밴드
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)

        return upper_band, sma, lower_band

    @staticmethod
    def rsi(prices, period=14):
        """
        상대강도지수 (RSI - Relative Strength Index)

        RSI = 100 - (100 / (1 + RS))
        RS = 평균 상승폭 / 평균 하락폭

        과매수/과매도 판단:
        - RSI > 70: 과매수 (매도 신호)
        - RSI < 30: 과매도 (매수 신호)

        Args:
            prices: 가격 리스트
            period: 기간 (기본 14)

        Returns:
            float: RSI 값 (0-100)
        """
        if len(prices) < period + 1:
            return None

        # 가격 변화량 계산
        deltas = np.diff(prices)

        # 상승/하락 분리
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # 평균 상승/하락폭
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100  # 하락이 없으면 RSI = 100

        # RS와 RSI 계산
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def macd(prices, fast_period=12, slow_period=26, signal_period=9):
        """
        MACD (Moving Average Convergence Divergence)

        MACD Line = EMA(12) - EMA(26)
        Signal Line = EMA(MACD, 9)
        Histogram = MACD Line - Signal Line

        추세 전환 및 매매 신호 포착

        Args:
            prices: 가격 리스트
            fast_period: 빠른 EMA 기간
            slow_period: 느린 EMA 기간
            signal_period: 시그널 EMA 기간

        Returns:
            tuple: (MACD선, 시그널선, 히스토그램)
        """
        if len(prices) < slow_period:
            return None, None, None

        # 빠른/느린 EMA 계산
        fast_ema = TechnicalIndicators.exponential_moving_average(prices, fast_period)
        slow_ema = TechnicalIndicators.exponential_moving_average(prices, slow_period)

        if fast_ema is None or slow_ema is None:
            return None, None, None

        # MACD 선
        macd_line = fast_ema - slow_ema

        # 시그널 선 계산을 위한 MACD 히스토리 필요
        # 간단한 예제를 위해 현재 값만 반환
        # 실제로는 MACD 값들의 EMA를 계산해야 함

        return macd_line, None, None

# 사용 예시
prices = [75000, 75100, 75200, 74900, 75300, 75400, 75100, 75500,
          75600, 75400, 75700, 75800, 75600, 75900, 76000]

# SMA 계산
sma_5 = TechnicalIndicators.simple_moving_average(prices, 5)
print(f"SMA(5): {sma_5}")

# 볼린저 밴드
upper, middle, lower = TechnicalIndicators.bollinger_bands(prices, period=10)
print(f"볼린저밴드: 상단={upper:.0f}, 중간={middle:.0f}, 하단={lower:.0f}")

# RSI
rsi_value = TechnicalIndicators.rsi(prices, period=14)
print(f"RSI(14): {rsi_value:.2f}")
```

---

## 💾 데이터 백업 및 관리

### 날짜별 DB 분리 시스템 (`utility/query.py:343-383`)

STOM은 당일 거래 종료 후 데이터를 날짜별로 분리하여 저장합니다:

```
_database/stock_tick.db (당일 거래 데이터)
  ↓ 일자DB분리
_database/stock_tick_20240101.db
_database/stock_tick_20240102.db
_database/stock_tick_20240103.db
...
```

**백테DB생성** (`utility/query.py:222-256`):
날짜별 DB 파일들을 하나의 백테스트용 DB로 통합:
```
stock_tick_20240101.db + stock_tick_20240102.db + ...
  ↓ 백테DB생성
stock_tick_back.db (백테스트용 통합 DB)
```

### 데이터 압축 시스템 (학습용 예제)

오래된 데이터를 압축하여 저장 공간을 절약하는 예제입니다:

**소스**: 예제 코드

```python
import io
import pandas as pd
from datetime import datetime, timedelta

class DataCompressor:
    """데이터 압축 관리 - 저장 공간 최적화"""

    def __init__(self):
        # 데이터 유형별 압축 및 보관 규칙
        self.compression_rules = {
            'tick_data': {
                'retention_days': 30,           # 30일간 보관
                'compression_after_days': 7     # 7일 후 압축
            },
            'minute_data': {
                'retention_days': 365,          # 1년간 보관
                'compression_after_days': 30    # 30일 후 압축
            },
            'daily_data': {
                'retention_days': 3650,         # 10년간 보관
                'compression_after_days': 365   # 1년 후 압축
            }
        }

    def compress_old_data(self, data_type, db_manager):
        """
        오래된 데이터 압축

        Args:
            data_type: 데이터 유형 ('tick_data', 'minute_data', etc.)
            db_manager: 데이터베이스 관리자
        """
        rules = self.compression_rules.get(data_type)
        if not rules:
            return

        # 압축 대상 날짜 계산
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
        """
        데이터 청크 압축 - Parquet 포맷 + gzip

        Parquet 장점:
        - 컬럼 기반 저장 (SQL 쿼리 최적화)
        - 효율적인 압축
        - 메타데이터 포함
        """
        # pandas DataFrame으로 변환
        df = pd.DataFrame(data)

        # Parquet 형식으로 압축 (gzip)
        buffer = io.BytesIO()
        df.to_parquet(buffer, compression='gzip', engine='pyarrow')

        return buffer.getvalue()

    def decompress_data_chunk(self, compressed_data):
        """압축 데이터 해제"""
        buffer = io.BytesIO(compressed_data)
        df = pd.read_parquet(buffer)

        return df.to_dict('records')

    def mark_as_compressed(self, data_type, cutoff_date):
        """압축 플래그 설정"""
        query = f"""
        UPDATE {data_type}
        SET compressed = 1
        WHERE timestamp < ?
        """
        # DB 업데이트 실행

# 사용 예시
compressor = DataCompressor()

# 7일 이상된 틱 데이터 압축
compressor.compress_old_data('tick_data', db_manager)
```

### 데이터 아카이빙 (학습용 예제)

장기 보관을 위한 데이터 아카이빙 시스템 예제입니다:

**소스**: 예제 코드

```python
import os
from datetime import datetime
import pandas as pd

class DataArchiver:
    """데이터 아카이빙 관리 - 장기 보관"""

    def __init__(self, archive_path="archive/"):
        self.archive_path = archive_path
        self.ensure_archive_directory()

    def ensure_archive_directory(self):
        """아카이브 디렉토리 생성"""
        os.makedirs(self.archive_path, exist_ok=True)

    def archive_old_data(self, data_type, retention_days, db_manager):
        """
        오래된 데이터 아카이빙

        Args:
            data_type: 데이터 유형
            retention_days: 보관 기간 (일)
            db_manager: 데이터베이스 관리자
        """
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
            self.delete_archived_data(data_type, cutoff_date, db_manager)

    def group_by_month(self, data):
        """
        월별 데이터 그룹화

        Returns:
            dict: {month_key: data_list}
            month_key 형식: '2024_01', '2024_02', ...
        """
        grouped = {}

        for record in data:
            timestamp = record['timestamp']
            month_key = timestamp.strftime('%Y_%m')

            if month_key not in grouped:
                grouped[month_key] = []

            grouped[month_key].append(record)

        return grouped

    def save_archive_file(self, archive_file, data):
        """
        아카이브 파일 저장

        Args:
            archive_file: 저장할 파일 경로
            data: 저장할 데이터
        """
        df = pd.DataFrame(data)
        df.to_parquet(archive_file, compression='gzip', engine='pyarrow')
        print(f"아카이브 저장: {archive_file} ({len(data)} rows)")

    def restore_archived_data(self, data_type, start_date, end_date):
        """
        아카이빙된 데이터 복원

        Args:
            data_type: 데이터 유형
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            list: 복원된 데이터
        """
        restored_data = []

        # 해당 기간의 아카이브 파일 찾기
        archive_files = self.find_archive_files(data_type, start_date, end_date)

        for archive_file in archive_files:
            # 아카이브 파일 로드
            df = pd.read_parquet(archive_file)

            # 날짜 범위 필터링
            mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
            filtered_df = df[mask]

            restored_data.extend(filtered_df.to_dict('records'))

        return restored_data

    def find_archive_files(self, data_type, start_date, end_date):
        """
        아카이브 파일 검색

        Returns:
            list: 아카이브 파일 경로 리스트
        """
        archive_files = []

        # start_date ~ end_date 사이의 월 리스트 생성
        current = start_date.replace(day=1)
        while current <= end_date:
            month_key = current.strftime('%Y_%m')
            archive_file = f"{self.archive_path}/{data_type}_{month_key}.parquet.gz"

            if os.path.exists(archive_file):
                archive_files.append(archive_file)

            # 다음 달로 이동
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return archive_files

# 사용 예시
archiver = DataArchiver(archive_path="./archive")

# 1년 이상된 데이터 아카이빙
archiver.archive_old_data('tick_data', retention_days=365, db_manager=db_manager)

# 아카이빙된 데이터 복원
start = datetime(2023, 1, 1)
end = datetime(2023, 3, 31)
restored = archiver.restore_archived_data('tick_data', start, end)
print(f"복원된 데이터: {len(restored)} rows")
```

### 데이터 정리 기능

- **지정시간이후삭제**: 특정 시간 이후 데이터 삭제 (테스트/디버깅용)
- **VACUUM**: SQLite DB 파일 크기 최적화

**소스**: 예제 코드

```python
# VACUUM 예제
import sqlite3
conn = sqlite3.connect('database/stock_tick.db')
conn.execute('VACUUM')  # 삭제된 데이터 공간 회수
conn.close()
```

---

## 🔍 데이터 조회 및 활용

### 백테스팅 시스템 데이터 로딩

백테스팅 엔진(`backtester/backengine_*.py`)은 다음과 같이 데이터를 로딩합니다:

**종목별 분류 방식** (기본):

**소스**: 예제 코드

```python
# 각 종목의 전체 기간 데이터를 한 번에 로딩
con = sqlite3.connect(DB_STOCK_BACK_TICK)
df = pd.read_sql(f'SELECT * FROM "{code}" WHERE `index` LIKE "{day}%"', con)
```

**일자별 분류 방식** (메모리 효율적):

**소스**: 예제 코드

```python
# 각 날짜별로 모든 종목 데이터 로딩
con = sqlite3.connect(f'{DB_PATH}/stock_tick_{day}.db')
df = pd.read_sql(f'SELECT * FROM "{code}"', con)
```

### 고성능 데이터 조회 (학습용 예제)

인덱스 최적화와 캐싱을 활용한 고성능 조회 예제입니다:

**소스**: 예제 코드

```python
import sqlite3
from datetime import datetime, timedelta

class DataQueryOptimizer:
    """데이터 조회 최적화 - 인덱스와 캐싱 활용"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.query_cache = {}  # {cache_key: result}
        self.max_cache_size = 1000

    def get_ohlcv_data(self, symbol, timeframe, start_date, end_date, limit=None):
        """
        OHLCV 데이터 조회 - 캐싱 지원

        Args:
            symbol: 종목코드
            timeframe: 시간프레임 ('1m', '5m', '1h', etc.)
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 행 수

        Returns:
            list: [(timestamp, open, high, low, close, volume), ...]
        """
        # 캐시 키 생성
        cache_key = f"{symbol}_{timeframe}_{start_date}_{end_date}_{limit}"

        # 캐시 확인
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]

        # SQL 쿼리 (인덱스 활용)
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

        # 결과 캐싱 (최대 캐시 크기 제한)
        if len(self.query_cache) < self.max_cache_size:
            self.query_cache[cache_key] = result

        return result

    def get_latest_tick_data(self, symbols, limit=100):
        """
        최신 틱 데이터 조회 - Window Function 활용

        각 종목의 최신 N개 틱 데이터를 효율적으로 조회

        Args:
            symbols: 종목코드 리스트
            limit: 종목당 최대 행 수

        Returns:
            list: 틱 데이터
        """
        # IN 절을 위한 플레이스홀더
        placeholders = ','.join(['?' for _ in symbols])

        # Window Function을 사용한 ROW_NUMBER
        query = f"""
        SELECT * FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY code
                       ORDER BY timestamp DESC
                   ) as rn
            FROM stock_tick
            WHERE code IN ({placeholders})
        )
        WHERE rn <= ?
        ORDER BY code, timestamp DESC
        """

        params = symbols + [limit]
        return self.db_manager.execute_query(query, params)

    def get_volume_profile(self, symbol, start_date, end_date, price_bins=50):
        """
        거래량 프로파일 조회 - 가격대별 거래량 분석

        Args:
            symbol: 종목코드
            start_date: 시작 날짜
            end_date: 종료 날짜
            price_bins: 가격 구간 수

        Returns:
            list: [(price_level, total_volume, tick_count), ...]
        """
        # 가격 범위 조회
        price_query = """
        SELECT MIN(current_price) as min_price, MAX(current_price) as max_price
        FROM stock_tick
        WHERE code = ?
        """
        price_data = self.db_manager.execute_query(price_query, [symbol])
        min_price, max_price = price_data[0]

        # 가격 구간 크기 계산
        bin_size = (max_price - min_price) / price_bins

        # 거래량 프로파일 쿼리
        query = """
        SELECT
            ROUND(current_price / ?) * ? as price_level,
            SUM(volume) as total_volume,
            COUNT(*) as tick_count
        FROM stock_tick
        WHERE code = ? AND timestamp BETWEEN ? AND ?
        GROUP BY price_level
        ORDER BY price_level
        """

        params = [bin_size, bin_size, symbol, start_date, end_date]
        return self.db_manager.execute_query(query, params)

# 사용 예시
query_optimizer = DataQueryOptimizer(db_manager)

# OHLCV 데이터 조회
symbol = '005930'
timeframe = '1m'
start = datetime(2024, 1, 1, 9, 0, 0)
end = datetime(2024, 1, 1, 15, 30, 0)

ohlcv_data = query_optimizer.get_ohlcv_data(symbol, timeframe, start, end, limit=100)

# 최신 틱 데이터 조회 (여러 종목)
symbols = ['005930', '000660', '035720']
latest_ticks = query_optimizer.get_latest_tick_data(symbols, limit=10)

# 거래량 프로파일 조회
volume_profile = query_optimizer.get_volume_profile(
    symbol='005930',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    price_bins=50
)
```

### 데이터 분석 도구 (학습용 예제)

통계 분석 및 기술적 분석 도구 예제입니다:

**소스**: 예제 코드

```python
import numpy as np
from datetime import datetime, timedelta

class DataAnalyzer:
    """데이터 분석 도구 - 통계 및 기술적 분석"""

    def __init__(self, query_optimizer):
        self.query_optimizer = query_optimizer

    def calculate_volatility(self, symbol, timeframe, period_days=30):
        """
        변동성 계산 - 연율화 표준편차

        변동성(Volatility) = σ × √252
        - σ: 일일 수익률의 표준편차
        - 252: 연간 거래일수

        Args:
            symbol: 종목코드
            timeframe: 시간프레임
            period_days: 계산 기간 (일)

        Returns:
            float: 연율화 변동성 (%)
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # OHLCV 데이터 조회
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

        # 연율화 변동성 계산
        volatility = np.std(returns) * np.sqrt(252) * 100  # %로 표시

        return volatility

    def calculate_correlation(self, symbol1, symbol2, timeframe, period_days=30):
        """
        상관관계 계산 - 피어슨 상관계수

        상관계수:
        - +1: 완전 양의 상관관계
        -  0: 상관관계 없음
        - -1: 완전 음의 상관관계

        Args:
            symbol1: 첫 번째 종목
            symbol2: 두 번째 종목
            timeframe: 시간프레임
            period_days: 계산 기간

        Returns:
            float: 상관계수 (-1 ~ 1)
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # 두 종목의 OHLCV 데이터 조회
        data1 = self.query_optimizer.get_ohlcv_data(symbol1, timeframe, start_date, end_date)
        data2 = self.query_optimizer.get_ohlcv_data(symbol2, timeframe, start_date, end_date)

        # 공통 시간대 데이터 추출
        common_data = self.align_time_series(data1, data2)

        if len(common_data['data1']) < 10:
            return None

        # 종가 추출
        prices1 = np.array([row[4] for row in common_data['data1']])
        prices2 = np.array([row[4] for row in common_data['data2']])

        # 피어슨 상관계수 계산
        correlation = np.corrcoef(prices1, prices2)[0, 1]

        return correlation

    def align_time_series(self, data1, data2):
        """
        시계열 데이터 정렬 - 공통 타임스탬프 추출

        Returns:
            dict: {'data1': [...], 'data2': [...]}
        """
        # 타임스탬프로 딕셔너리 생성
        dict1 = {row[0]: row for row in data1}
        dict2 = {row[0]: row for row in data2}

        # 공통 타임스탬프
        common_timestamps = sorted(set(dict1.keys()) & set(dict2.keys()))

        # 공통 데이터 추출
        aligned_data1 = [dict1[ts] for ts in common_timestamps]
        aligned_data2 = [dict2[ts] for ts in common_timestamps]

        return {'data1': aligned_data1, 'data2': aligned_data2}

    def detect_support_resistance(self, symbol, timeframe, period_days=90, tolerance=0.02):
        """
        지지/저항선 탐지 - 가격 클러스터 분석

        Args:
            symbol: 종목코드
            timeframe: 시간프레임
            period_days: 분석 기간
            tolerance: 가격 허용 오차 (2% = 0.02)

        Returns:
            dict: {'support_levels': [...], 'resistance_levels': [...]}
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # OHLCV 데이터 조회
        data = self.query_optimizer.get_ohlcv_data(symbol, timeframe, start_date, end_date)

        # 고가/저가 추출
        highs = [row[2] for row in data]  # high_price
        lows = [row[3] for row in data]   # low_price

        # 지지선 (저점 클러스터)
        support_levels = self.find_price_clusters(lows, tolerance)

        # 저항선 (고점 클러스터)
        resistance_levels = self.find_price_clusters(highs, tolerance)

        return {
            'support_levels': support_levels,
            'resistance_levels': resistance_levels
        }

    def find_price_clusters(self, prices, tolerance=0.02):
        """
        가격 클러스터 찾기 - 비슷한 가격대 그룹화

        Args:
            prices: 가격 리스트
            tolerance: 허용 오차 비율

        Returns:
            list: [{'level': 평균가격, 'strength': 터치횟수, 'prices': [...]}, ...]
        """
        clusters = []
        sorted_prices = sorted(prices)

        if not sorted_prices:
            return clusters

        current_cluster = [sorted_prices[0]]

        for price in sorted_prices[1:]:
            # 현재 클러스터의 마지막 가격과 비교
            if abs(price - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                current_cluster.append(price)
            else:
                # 클러스터 완성 (최소 3회 터치)
                if len(current_cluster) >= 3:
                    clusters.append({
                        'level': np.mean(current_cluster),
                        'strength': len(current_cluster),
                        'prices': current_cluster.copy()
                    })
                current_cluster = [price]

        # 마지막 클러스터 처리
        if len(current_cluster) >= 3:
            clusters.append({
                'level': np.mean(current_cluster),
                'strength': len(current_cluster),
                'prices': current_cluster
            })

        # 강도(터치 횟수)순으로 정렬
        return sorted(clusters, key=lambda x: x['strength'], reverse=True)

# 사용 예시
analyzer = DataAnalyzer(query_optimizer)

# 변동성 계산
volatility = analyzer.calculate_volatility('005930', '1d', period_days=30)
print(f"30일 변동성: {volatility:.2f}%")

# 상관관계 계산 (삼성전자 vs SK하이닉스)
correlation = analyzer.calculate_correlation('005930', '000660', '1d', period_days=60)
print(f"상관계수: {correlation:.3f}")

# 지지/저항선 탐지
levels = analyzer.detect_support_resistance('005930', '1d', period_days=90, tolerance=0.02)
print(f"주요 지지선: {[l['level'] for l in levels['support_levels'][:3]]}")
print(f"주요 저항선: {[l['level'] for l in levels['resistance_levels'][:3]]}")
```

### 실시간 데이터 활용

리시버 → 전략 → 트레이더로 데이터 전송:

**소스**: 예제 코드

```python
# 리시버: 실시간 데이터 수신 및 전처리
# ↓ Queue를 통해 전송
# 전략: 매매 시그널 생성
# ↓ Queue를 통해 전송
# 트레이더: 주문 실행
```

---

*다음: [07. 트레이딩 엔진](../07_Trading/trading_engine.md)* 