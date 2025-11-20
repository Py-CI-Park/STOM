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
```python
columns = [
    'index', '증권사', '주식리시버', '주식트레이더', '주식데이터저장', '거래소',
    '코인리시버', '코인트레이더', '코인데이터저장', '바이낸스선물고정레버리지',
    '바이낸스선물고정레버리지값', '바이낸스선물변동레버리지값', '바이낸스선물마진타입',
    '바이낸스선물포지션', '버전업', '리시버공유'
]
```

**sacc 테이블** - 주식 계정 정보 (암호화됨)
```python
columns = ["index", "아이디", "비밀번호", "인증서비밀번호", "계좌비밀번호"]
# 1~8번까지 최대 8개 계정 지원
```

**cacc 테이블** - 암호화폐 API 키 (암호화됨)
```python
columns = ["index", "Access_key", "Secret_key"]
# Upbit, Binance 등 거래소 API 키 저장
```

**stock 테이블** - 주식 거래 설정
```python
columns = [
    "index", "주식모의투자", "주식알림소리", "주식매수전략", "주식매도전략",
    "주식타임프레임", "주식평균값계산틱수", "주식최대매수종목수", "주식전략종료시간",
    "주식잔고청산", "주식프로세스종료", "주식컴퓨터종료", "주식투자금고정", "주식투자금",
    "주식손실중지", "주식손실중지수익률", "주식수익중지", "주식수익중지수익률", "주식경과틱수설정"
]
```

**coin 테이블** - 암호화폐 거래 설정
```python
columns = [
    "index", "코인모의투자", "코인알림소리", "코인매수전략", "코인매도전략",
    "코인타임프레임", "코인평균값계산틱수", "코인최대매수종목수", "코인전략종료시간",
    "코인잔고청산", "코인프로세스종료", "코인컴퓨터종료", "코인투자금고정", "코인투자금",
    "코인손실중지", "코인손실중지수익률", "코인수익중지", "코인수익중지수익률", "코인경과틱수설정"
]
```

**stockbuyorder/stocksellorder 테이블** - 주식 매수/매도 주문 설정
```python
# 매수 주문 설정: 주문구분, 분할횟수, 분할방법, 취소조건, 금지조건 등
# 매도 주문 설정: 손절수익률, 수익금 설정, 취소조건 등
```

##### 거래 DB 테이블 (`tradelist.db`) (`utility/database_check.py:244-318`)

**s_chegeollist / c_chegeollist** - 주식/코인 체결 내역
```python
query = 'CREATE TABLE "s_chegeollist" (
    "index" TEXT, "종목명" TEXT, "주문구분" TEXT, "주문수량" INTEGER,
    "체결수량" INTEGER, "미체결수량" INTEGER, "체결가" INTEGER,
    "체결시간" TEXT, "주문가격" INTEGER, "주문번호" TEXT
)'
```

**s_jangolist / c_jangolist** - 주식/코인 잔고 내역
```python
query = 'CREATE TABLE "s_jangolist" (
    "index" TEXT, "종목명" TEXT, "매입가" INTEGER, "현재가" INTEGER,
    "수익률" REAL, "평가손익" INTEGER, "매입금액" INTEGER, "평가금액" INTEGER,
    "보유수량" INTEGER, "분할매수횟수" INTEGER, "분할매도횟수" INTEGER, "매수시간" TEXT
)'
```

**c_jangolist_future** - 코인 선물 잔고 (바이낸스)
```python
query = 'CREATE TABLE "c_jangolist_future" (
    "index" TEXT, "종목명" TEXT, "포지션" TEXT, "매입가" REAL, "현재가" REAL,
    "수익률" REAL, "평가손익" INTEGER, "매입금액" INTEGER, "평가금액" INTEGER,
    "보유수량" REAL, "레버리지" INTEGER, "분할매수횟수" INTEGER,
    "분할매도횟수" INTEGER, "매수시간" TEXT
)'
```

**s_tradelist / c_tradelist** - 주식/코인 거래 내역
```python
query = 'CREATE TABLE "s_tradelist" (
    "index" TEXT, "종목명" TEXT, "매수금액" INTEGER, "매도금액" INTEGER,
    "주문수량" INTEGER, "수익률" REAL, "수익금" INTEGER, "체결시간" TEXT
)'
```

**s_totaltradelist / c_totaltradelist** - 총 거래 집계
```python
query = 'CREATE TABLE "s_totaltradelist" (
    "index" TEXT, "총매수금액" INTEGER, "총매도금액" INTEGER,
    "총수익금액" INTEGER, "총손실금액" INTEGER, "수익률" REAL, "수익금합계" INTEGER
)'
```

##### 전략 DB 테이블 (`strategy.db`) (`utility/database_check.py:166-241`)

**stockbuy/stocksell, coinbuy/coinsell** - 매매 전략 코드
```python
cur.execute('CREATE TABLE "stockbuy" ( "index" TEXT, "전략코드" TEXT )')
cur.execute('CREATE INDEX "ix_stockbuy_index" ON "stockbuy" ("index")')
```

**stockbuyconds/stocksellconds** - 매매 조건식
```python
cur.execute('CREATE TABLE "stockbuyconds" ( "index" TEXT, "전략코드" TEXT )')
```

**stockvars/coinvars** - 전략 변수
```python
cur.execute('CREATE TABLE "stockvars" ( "index" TEXT, "전략코드" TEXT )')
```

**stockoptibuy/stockoptisell** - 최적화용 전략
```python
query = 'CREATE TABLE "stockoptibuy" ( "index" TEXT, "전략코드" TEXT, "변수값" TEXT )'
```

##### 시장 데이터 DB 테이블 (동적 생성)

**moneytop 테이블** - 거래대금 순위 (모든 tick/min DB에 존재)
```python
# index: 시간 (YYYYMMDDHHMMSS)
# 거래대금순위: 세미콜론으로 구분된 종목코드/마켓 리스트
```

**[종목코드/마켓] 테이블** - 개별 종목 데이터 (동적 생성)
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
```python
elif '백테DB생성' in query[0]:
    # _database/stock_tick_20240101.db, stock_tick_20240102.db 등을
    # _database/stock_tick_back.db로 통합
```

**일자DB분리**: 당일 DB를 날짜별로 분리하여 저장
```python
elif '일자DB분리' in query[0]:
    # stock_tick.db에서 날짜별로 stock_tick_20240101.db, stock_tick_20240102.db로 분리
```

**지정시간이후삭제**: 특정 시간 이후 데이터 삭제 (디버깅/테스트용)
```python
elif '당일데이터지정시간이후삭제' in query[0]:
    # 예: 093000 이후 데이터 삭제
```

---

## 📡 실시간 데이터 수신

### 주식 데이터 수신 시스템

#### 1. Kiwoom 리시버 구조 (`stock/kiwoom_receiver_tick.py:41-118`)

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

```python
# 거래대금 상위 종목만 DB에 저장 (메모리/스토리지 최적화)
# 틱 모드: 거래대금 순위 30위 이후 종목만 저장
# 분봉 모드: 모든 거래대금 순위 종목 저장
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

### 데이터 정리 기능

- **지정시간이후삭제**: 특정 시간 이후 데이터 삭제 (테스트/디버깅용)
- **VACUUM**: SQLite DB 파일 크기 최적화

---

## 🔍 데이터 조회 및 활용

### 백테스팅 시스템 데이터 로딩

백테스팅 엔진(`backtester/backengine_*.py`)은 다음과 같이 데이터를 로딩합니다:

**종목별 분류 방식** (기본):
```python
# 각 종목의 전체 기간 데이터를 한 번에 로딩
con = sqlite3.connect(DB_STOCK_BACK_TICK)
df = pd.read_sql(f'SELECT * FROM "{code}" WHERE `index` LIKE "{day}%"', con)
```

**일자별 분류 방식** (메모리 효율적):
```python
# 각 날짜별로 모든 종목 데이터 로딩
con = sqlite3.connect(f'{DB_PATH}/stock_tick_{day}.db')
df = pd.read_sql(f'SELECT * FROM "{code}"', con)
```

### 실시간 데이터 활용

리시버 → 전략 → 트레이더로 데이터 전송:
```python
# 리시버: 실시간 데이터 수신 및 전처리
# ↓ Queue를 통해 전송
# 전략: 매매 시그널 생성
# ↓ Queue를 통해 전송
# 트레이더: 주문 실행
```

---

*다음: [07. 트레이딩 엔진](../07_Trading/trading_engine.md)* 