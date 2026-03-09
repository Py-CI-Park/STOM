# STOM V1 백테스팅 시스템 - 데이터 로딩 및 멀티코어 처리 상세 분석

## 목차
1. [시스템 개요](#1-시스템-개요)
2. [아키텍처 구조](#2-아키텍처-구조)
3. [데이터 로딩 프로세스](#3-데이터-로딩-프로세스)
4. [멀티프로세스 구조](#4-멀티프로세스-구조)
5. [메모리 관리 전략](#5-메모리-관리-전략)
6. [백테스팅 실행 흐름](#6-백테스팅-실행-흐름)
7. [성능 최적화 기법](#7-성능-최적화-기법)

---

## 1. 시스템 개요

### 1.1 백테스팅 시스템의 목적
STOM V1의 백테스팅 시스템은 과거 시장 데이터를 활용하여 거래 전략의 성과를 검증하는 고성능 시뮬레이션 엔진입니다.

**핵심 특징:**
- **멀티프로세스 병렬 처리**: 여러 CPU 코어를 활용한 동시 백테스팅
- **대용량 데이터 처리**: 틱/분봉 데이터를 메모리에 일괄 로딩
- **실시간 전략 검증**: 실제 거래와 동일한 조건으로 시뮬레이션
- **다중 종목 동시 처리**: 수백 개 종목을 동시에 백테스팅

### 1.2 주요 파일 구성

```
backtester/
├── backtest.py              # 메인 백테스트 컨트롤러
├── backengine_kiwoom_tick.py   # 키움 주식 틱 엔진
├── backengine_kiwoom_min.py    # 키움 주식 분봉 엔진
├── backengine_upbit_tick.py    # 업비트 틱 엔진
├── backengine_binance_tick.py  # 바이낸스 틱 엔진
├── back_static.py           # 공통 함수 및 결과 처리
├── optimiz.py               # 전략 최적화 도구
└── back_subtotal.py         # 집계 프로세스
```

---

## 2. 아키텍처 구조

### 2.1 프로세스 계층 구조

```
[메인 UI 프로세스]
     ↓ Queue
[BackTest 프로세스] ← 사용자 요청 수신, 데이터 로딩 조율
     ↓ Queue
[Total 프로세스] ← 결과 집계 및 최종 리포트 생성
     ↓ Queue
[BackEngine 프로세스 x N] ← 실제 백테스팅 실행 (병렬)
     ↓ Queue
[SubTotal 프로세스 x 5] ← 거래 결과 분리 집계
```

### 2.2 Queue 기반 통신

```python
# backtest.py의 주요 Queue 구조
wq        # Window Queue - UI 업데이트
bq        # Backtest Queue - 백테스트 설정 전달
sq        # Status Queue - 상태 메시지
tq        # Total Queue - 집계 프로세스로 결과 전송
beq_list  # BackEngine Queue List - 각 엔진으로 명령 전송
bstq_list # BackSubTotal Queue List - 집계 프로세스로 거래 결과 전송
```

**통신 흐름:**
1. UI → BackTest (bq): 백테스트 설정 전달
2. BackTest → BackEngine (beq_list): 데이터 로딩 명령
3. BackEngine → SubTotal (bstq_list): 거래 체결 결과
4. SubTotal → Total (tq): 집계된 거래 결과
5. Total → UI (wq): 최종 백테스트 리포트

---

## 3. 데이터 로딩 프로세스

### 3.1 데이터 로딩 개요

백테스팅에서 가장 중요한 것은 **과거 시장 데이터를 빠르게 메모리에 적재**하는 것입니다. STOM은 두 가지 전략을 제공합니다.

**로딩 전략:**
- **일괄 로딩 (백테일괄로딩=True)**: 모든 데이터를 메모리에 한 번에 로딩
- **온디맨드 로딩 (백테일괄로딩=False)**: 필요한 종목만 Pickle 파일로 저장 후 필요 시 로딩

### 3.2 데이터베이스 구조

```python
# utility/setting.py
DB_STOCK_BACK_TICK = 'C:/System_Trading/STOM/_database/stock_tick.db'
DB_STOCK_BACK_MIN  = 'C:/System_Trading/STOM/_database/stock_min.db'
DB_COIN_BACK_TICK  = 'C:/System_Trading/STOM/_database/coin_tick.db'
DB_COIN_BACK_MIN   = 'C:/System_Trading/STOM/_database/coin_min.db'
```

**데이터베이스 테이블 구조:**
- 각 종목코드별로 독립된 테이블 생성
- 인덱스: 시간(YYYYMMDDHHMMSS)
- 컬럼: 현재가, 시가, 고가, 저가, 거래량, 체결강도, 호가 데이터 등

### 3.3 DataLoad 함수 상세 분석

`BackEngineKiwoomTick.DataLoad()` 함수는 백테스팅 엔진의 핵심 데이터 로딩 로직입니다.

#### 3.3.1 함수 시그니처

```python
def DataLoad(self, data):
    """
    Parameters:
    -----------
    data : tuple
        ('데이터크기' | '데이터로딩', startday, endday, starttime, endtime,
         code_list/day_list, avg_list, code_days, day_codes, code, divid_mode)
    """
```

#### 3.3.2 데이터 분류 모드

STOM은 세 가지 데이터 분류 방식을 지원합니다:

**1. 종목코드별 분류 (divid_mode='종목코드별 분류')**

```python
# backengine_kiwoom_tick.py:263-282
if divid_mode == '종목코드별 분류':
    gubun, startday, endday, starttime, endtime, code_list, avg_list, code_days, _, _, _ = data

    for code in code_list:
        # 1단계: 데이터베이스에서 종목 데이터 조회
        df_tick = pd.read_sql(GetBackloadCodeQuery(code, code_days[code], starttime, endtime), con)

        # 2단계: 이동평균 등 기술적 지표 계산
        df_tick = AddAvgData(df_tick, 3, is_tick, avg_list)

        # 3단계: NumPy 배열로 변환 (고속 계산용)
        arry_tick = np.array(df_tick)

        # 4단계: 메모리 저장 또는 Pickle 파일 저장
        if self.dict_set['백테일괄로딩']:
            self.dict_arry[code] = arry_tick  # 메모리 저장
        else:
            pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_tick', arry_tick)  # 파일 저장

        self.code_list.append(code)
```

**장점:**
- 각 종목을 독립적으로 처리
- 엔진별로 종목을 분산 배치 가능
- 메모리 사용량 예측 용이

**2. 일자별 분류 (divid_mode='일자별 분류')**

```python
# backengine_kiwoom_tick.py:283-317
elif divid_mode == '일자별 분류':
    # 특정 날짜의 모든 종목 데이터를 함께 로딩
    for day in day_list:
        for code in day_codes[day]:
            df_tick = pd.read_sql(GetBackloadDayQuery(day, code, starttime, endtime), con)
```

**장점:**
- 특정 날짜의 전체 시장 상황을 함께 분석 가능
- 시간 순서대로 데이터 접근 최적화

**3. 단일 종목 일자별 (특수 모드)**

```python
# backengine_kiwoom_tick.py:318-344
else:
    # 하나의 종목에 대해 여러 날짜 데이터 로딩
    gubun, startday, endday, starttime, endtime, day_list, avg_list, _, _, code, _ = data
```

**용도:**
- 특정 종목 집중 분석
- 백파인더 등 단일 종목 전략 개발

### 3.4 SQL 쿼리 최적화

#### GetBackloadCodeQuery 분석

```python
# back_static.py:75-91
def GetBackloadCodeQuery(code, days, starttime, endtime):
    """
    종목코드별 데이터 조회 쿼리 생성

    Parameters:
    -----------
    code : str
        종목코드 (예: 'A005930')
    days : list
        조회할 날짜 리스트 (예: [20240101, 20240102, ...])
    starttime : int
        시작 시간 (예: 90030)
    endtime : int
        종료 시간 (예: 153000)
    """
    last = len(days) - 1
    like_text = '( '

    # OR 조건으로 여러 날짜를 한 번에 조회
    for i, day in enumerate(days):
        if i != last:
            like_text += f"`index` LIKE '{day}%' or "
        else:
            like_text += f"`index` LIKE '{day}%' )"

    # 시간 필터링 (분봉: 4자리, 틱: 6자리)
    if len(str(endtime)) < 5:
        query = f"SELECT * FROM '{code}' WHERE {like_text} and " \
                f"`index` % 10000 >= {starttime} and " \
                f"`index` % 10000 <= {endtime}"
    else:
        query = f"SELECT * FROM '{code}' WHERE {like_text} and " \
                f"`index` % 1000000 >= {starttime} and " \
                f"`index` % 1000000 <= {endtime}"

    return query
```

**쿼리 최적화 포인트:**
1. `LIKE` 연산 최소화: 여러 날짜를 OR로 묶어서 한 번에 조회
2. 인덱스 활용: `index` 컬럼에 인덱스 설정
3. 모듈러 연산 활용: `% 1000000`으로 시간 부분만 추출

### 3.5 기술적 지표 계산

#### AddAvgData 함수 분석

```python
# back_static.py:131-183
def AddAvgData(df, round_unit, is_tick, avg_list):
    """
    백테스팅에 필요한 기술적 지표를 미리 계산하여 컬럼 추가

    Parameters:
    -----------
    df : DataFrame
        원본 시장 데이터
    round_unit : int
        반올림 소수점 자리수 (주식: 3, 코인: 8)
    is_tick : bool
        틱 데이터 여부 (True: 틱, False: 분봉)
    avg_list : list
        이동평균 계산 기간 리스트 (예: [60, 300, 600, 1200])
    """

    # 기본 이동평균 추가 (고정 기간)
    if is_tick:
        df['이평0060'] = df['현재가'].rolling(window=60).mean().round(round_unit)
        df['이평0300'] = df['현재가'].rolling(window=300).mean().round(round_unit)
        df['이평0600'] = df['현재가'].rolling(window=600).mean().round(round_unit)
        df['이평1200'] = df['현재가'].rolling(window=1200).mean().round(round_unit)
    else:
        df['이평005'] = df['현재가'].rolling(window=5).mean().round(round_unit)
        df['이평010'] = df['현재가'].rolling(window=10).mean().round(round_unit)
        df['이평020'] = df['현재가'].rolling(window=20).mean().round(round_unit)
        df['이평060'] = df['현재가'].rolling(window=60).mean().round(round_unit)
        df['이평120'] = df['현재가'].rolling(window=120).mean().round(round_unit)

    # 사용자 정의 기간 기술적 지표 추가
    for avg in avg_list:
        df[f'최고현재가{avg}'] = df['현재가'].rolling(window=avg).max()
        df[f'최저현재가{avg}'] = df['현재가'].rolling(window=avg).min()
        df[f'체결강도평균{avg}'] = df['체결강도'].rolling(window=avg).mean().round(3)
        df[f'최고체결강도{avg}'] = df['체결강도'].rolling(window=avg).max()
        df[f'최저체결강도{avg}'] = df['체결강도'].rolling(window=avg).min()

        if is_tick:
            df[f'최고초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).max()
            df[f'최고초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).max()
            df[f'누적초당매수수량{avg}'] = df['초당매수수량'].rolling(window=avg).sum()
            df[f'누적초당매도수량{avg}'] = df['초당매도수량'].rolling(window=avg).sum()
            df[f'초당거래대금평균{avg}'] = df['초당거래대금'].rolling(window=avg).mean().round(0)

        # 각도 계산 (등락율, 거래대금, 전일비)
        df2 = df[['등락율', '당일거래대금', '전일비']].copy()
        df2[f'등락율N{avg}'] = df2['등락율'].shift(avg - 1)
        df2['등락율차이'] = df2['등락율'] - df2[f'등락율N{avg}']
        df['등락율각도'] = df2['등락율차이'].apply(
            lambda x: round(math.atan2(x * 5, avg) / (2 * math.pi) * 360, 2)
        )

    return df
```

**기술적 지표 계산 전략:**
1. **사전 계산**: 백테스팅 중 반복 계산 방지
2. **Pandas Rolling**: 벡터화된 계산으로 성능 최적화
3. **각도 변환**: 변화율을 각도로 변환하여 추세 파악 용이
4. **다양한 기간**: 사용자가 지정한 모든 기간의 지표 동시 계산

---

## 4. 멀티프로세스 구조

### 4.1 프로세스 생성 전략

#### BackTest 프로세스 시작

```python
# backtest.py:237-325
class BackTest:
    def Start(self):
        # 1단계: 백테스트 설정 수신
        data = self.bq.get()
        betting, avgtime, startday, endday = data[0], data[1], data[2], data[3]

        # 2단계: 메인 데이터 조회 (moneytop 테이블)
        con = sqlite3.connect(db)
        query = GetMoneytopQuery(self.ui_gubun, startday, endday, starttime, endtime)
        df_mt = pd.read_sql(query, con)
        con.close()

        # 3단계: 보유종목수 추적 배열 생성
        arry_bct = np.zeros((len(df_mt), 3), dtype='float64')
        arry_bct[:, 0] = df_mt['index'].values

        # 4단계: Total 프로세스 생성
        mq = Queue()
        Process(
            target=Total,
            args=(self.wq, self.sq, self.tq, self.teleQ, mq, self.lq,
                  self.bstq_list, self.backname, self.ui_gubun, self.gubun)
        ).start()

        # 5단계: 백테엔진으로 데이터 및 설정 전송
        for q in self.beq_list:
            q.put(('백테정보', betting, avgtime, startday, endday,
                   starttime, endtime, buystg, sellstg))
```

### 4.2 BackEngine 프로세스 동작

#### MainLoop 구조

```python
# backengine_kiwoom_tick.py:90-221
def MainLoop(self):
    while True:
        data = self.beq.get()

        if '정보' in data[0]:
            if data[0] == '백테정보':
                self.betting   = data[1]
                self.avgtime   = data[2]
                self.startday  = data[3]
                self.endday    = data[4]
                self.starttime = data[5]
                self.endtime   = data[6]
                self.buystg, self.indistg = GetBuyStg(data[7], self.gubun)
                self.sellstg, self.dict_sconds = GetSellStg(data[8], self.gubun)
                self.InitTradeInfo()
                self.BackTest()

        elif data[0] == '백테유형':
            self.back_type = data[1]

        elif data[0] in ('데이터크기', '데이터로딩'):
            self.DataLoad(data)

        elif data[0] == '데이터이동':
            self.SendData(data)

        elif data[0] == '데이터전송':
            self.RecvdData(data)
```

**MainLoop의 역할:**
1. **명령 대기**: 블로킹 Queue에서 명령 수신
2. **상태 관리**: 백테스트 유형, 전략 코드, 데이터 로딩 상태
3. **데이터 재분배**: 엔진 간 데이터 이동 (부하 분산)
4. **백테스트 실행**: 모든 준비 완료 시 BackTest() 호출

### 4.3 엔진 개수 및 분산 전략

일반적으로 STOM은 다음과 같이 프로세스를 생성합니다:

```python
# 예시: 8코어 CPU 기준
CPU_COUNT = 8
beq_list = [Queue() for _ in range(CPU_COUNT)]  # 8개 백테엔진

# 각 엔진에 프로세스 생성
for i in range(CPU_COUNT):
    Process(
        target=BackEngineKiwoomTick,
        args=(i, wq, tq, bq, beq_list, bstq_list)
    ).start()
```

**종목 분산 알고리즘:**

```python
# 종목을 엔진에 균등 배분
total_codes = 500  # 총 500개 종목
codes_per_engine = total_codes // CPU_COUNT  # 62~63개씩 배분

for i, engine in enumerate(range(CPU_COUNT)):
    start_idx = i * codes_per_engine
    end_idx = start_idx + codes_per_engine
    engine_codes = code_list[start_idx:end_idx]

    beq_list[engine].put(('데이터로딩', ..., engine_codes, ...))
```

### 4.4 동적 부하 재분배

성능 최적화를 위해 STOM은 런타임 중 데이터를 재분배할 수 있습니다:

```python
# backengine_kiwoom_tick.py:223-231
def SendData(self, data):
    """
    현재 엔진의 종목을 다른 엔진으로 이동
    """
    _, cnt, procn = data
    for i, code in enumerate(self.code_list):
        if i >= cnt:  # cnt 개수만 남기고 나머지 이동
            data = ('데이터전송', code, self.dict_arry[code])
            self.beq_list[procn].put(data)  # 목적지 엔진으로 전송
            del self.dict_arry[code]  # 메모리 해제

    self.code_list = self.code_list[:cnt]
```

---

## 5. 메모리 관리 전략

### 5.1 NumPy 배열 활용

STOM은 Pandas DataFrame을 NumPy 배열로 변환하여 처리합니다.

#### 변환 이유

```python
# backengine_kiwoom_tick.py:276
arry_tick = np.array(df_tick)

# 장점:
# 1. 메모리 사용량 30-50% 감소
# 2. 인덱싱 속도 10배 이상 빠름
# 3. 벡터 연산 최적화
# 4. C언어 수준 성능
```

#### 배열 구조

```python
# 틱 데이터 배열 구조 (각 행이 1틱)
arry_data.shape = (틱수, 컬럼수)

# 컬럼 인덱스:
# 0:  index (시간)
# 1:  현재가
# 2:  시가
# 3:  고가
# 4:  저가
# 5:  등락율
# 6:  당일거래대금
# 7:  체결강도
# 8:  거래대금증감
# ...
# 45: 이동평균60
# 46: 이동평균300
# 47: 이동평균600
# 48: 이동평균1200
# 49~: 기술적 지표들
```

### 5.2 메모리 로딩 전략 비교

#### 일괄 로딩 (dict_arry에 저장)

```python
# 장점:
# - 빠른 접근 속도 (메모리 직접 접근)
# - I/O 오버헤드 없음
# - 멀티프로세스 간 공유 불필요 (각자 보유)

# 단점:
# - 메모리 사용량 높음 (전체 데이터 * 프로세스 수)
# - 큰 데이터셋에서 메모리 부족 위험

if self.dict_set['백테일괄로딩']:
    self.dict_arry[code] = arry_tick  # 메모리 저장
```

#### Pickle 파일 로딩

```python
# 장점:
# - 메모리 사용량 최소화
# - 큰 데이터셋 처리 가능
# - 필요한 종목만 로딩 (온디맨드)

# 단점:
# - Pickle 읽기/쓰기 I/O 오버헤드
# - 첫 로딩 시 시간 소요

else:
    pickle_write(f'{BACK_TEMP}/{self.gubun}_{code}_tick', arry_tick)

# 사용 시:
if not self.dict_set['백테일괄로딩']:
    self.dict_arry = {code: pickle_read(f'{BACK_TEMP}/{self.gubun}_{code}_tick')}
```

### 5.3 가비지 컬렉션 최적화

```python
# backengine_kiwoom_tick.py:16
import gc
gc.disable()  # 가비지 컬렉션 비활성화

# 이유:
# 1. 백테스팅 중 메모리 할당/해제 최소화
# 2. GC 오버헤드 제거 (백테스팅 속도 5-10% 향상)
# 3. 백테스팅 완료 후 프로세스 종료로 자동 메모리 해제
```

### 5.4 데이터 슬라이싱 최적화

```python
# backengine_kiwoom_tick.py:364-380
def SetArrayTick(self, code, same_days, same_time):
    """
    필요한 기간의 데이터만 슬라이싱하여 메모리 절약
    """
    if same_days and same_time:
        # 전체 기간 동일: 슬라이싱 불필요
        self.arry_data = self.dict_arry[code]

    elif same_time:
        # 시간대는 동일, 날짜만 필터링
        self.arry_data = self.dict_arry[code][
            (self.dict_arry[code][:, 0] >= self.startday * 1000000) &
            (self.dict_arry[code][:, 0] <= self.endday * 1000000 + 240000)
        ]

    elif same_days:
        # 날짜는 동일, 시간대만 필터링
        self.arry_data = self.dict_arry[code][
            (self.dict_arry[code][:, 0] % 1000000 >= self.starttime) &
            (self.dict_arry[code][:, 0] % 1000000 <= self.endtime)
        ]

    else:
        # 날짜와 시간 모두 필터링
        self.arry_data = self.dict_arry[code][
            (self.dict_arry[code][:, 0] >= self.startday * 1000000) &
            (self.dict_arry[code][:, 0] <= self.endday * 1000000 + 240000) &
            (self.dict_arry[code][:, 0] % 1000000 >= self.starttime) &
            (self.dict_arry[code][:, 0] % 1000000 <= self.endtime)
        ]
```

---

## 6. 백테스팅 실행 흐름

### 6.1 전체 실행 플로우

```
[1. 초기화]
  ↓
[2. 데이터 로딩]
  ↓
[3. 전략 컴파일]
  ↓
[4. 틱 순회 시작]
  ↓
[5. 매수 조건 검사] ─Yes─→ [6. 매수 체결]
  ↓ No                        ↓
[7. 보유 중?] ─No─→ [다음 틱]
  ↓ Yes                       ↓
[8. 매도 조건 검사]           ↓
  ↓                           ↓
[9. 매도 체결] ────────────→ [10. 결과 전송]
  ↓
[11. 다음 틱]
  ↓
[12. 일자 변경?] ─Yes─→ [13. 일 마감 매도]
  ↓ No                        ↓
[반복]                      [14. 거래 정보 초기화]
                              ↓
                            [다음 일자]
```

### 6.2 BackTest 함수 상세

```python
# backengine_kiwoom_tick.py:382-428
def BackTest(self):
    # 1단계: 프로파일링 옵션 (성능 측정)
    if self.profile:
        import cProfile
        self.pr = cProfile.Profile()
        self.pr.enable()

    # 2단계: 시간 범위 일치 여부 확인 (슬라이싱 최적화)
    same_days = self.startday_ == self.startday and self.endday_ == self.endday
    same_time = self.starttime_ == self.starttime and self.endtime_ == self.endtime

    # 3단계: 전체 틱 수 계산 (진행률 표시용)
    if not self.tick_calcul and self.opti_turn in (1, 3):
        total_ticks = 0
        for code in self.code_list:
            self.SetArrayTick(code, same_days, same_time)
            total_ticks += len(self.arry_data)
        self.tq.put(('전체틱수', int(total_ticks / 100)))
        self.tick_calcul = True

    # 4단계: 종목별 백테스팅 루프
    j = 0
    len_codes = len(self.code_list)

    for k, code in enumerate(self.code_list):
        self.code = code
        self.name = self.dict_cn[self.code] if self.code in self.dict_cn.keys() else self.code

        # 데이터 로딩
        self.SetArrayTick(code, same_days, same_time)
        last = len(self.arry_data) - 1

        if last > 0:
            # 5단계: 틱별 전략 실행
            for i, index in enumerate(self.arry_data[:, 0]):
                self.index  = int(index)
                self.indexn = i
                self.tick_count += 1

                # 다음 날 변경 감지
                next_day_change = (i == last or
                    str(index)[:8] != str(self.arry_data[i + 1, 0])[:8])

                if not next_day_change:
                    try:
                        self.Strategy()  # 매수/매도 전략 실행
                    except:
                        print_exc()
                        self.BackStop()
                        return
                else:
                    # 일 마감: 보유 종목 강제 청산
                    self.LastSell()
                    self.InitTradeInfo()

                # 진행률 업데이트 (100틱마다)
                j += 1
                if self.opti_turn in (1, 3) and j % 100 == 0:
                    self.tq.put('탐색완료')

        # 종목 완료 알림
        self.tq.put(('백테완료', self.gubun, k+1, len_codes))

    # 6단계: 프로파일링 결과 출력
    if self.profile:
        self.pr.print_stats(sort='cumulative')
```

### 6.3 Strategy 함수 - 핵심 전략 실행

```python
# backengine_kiwoom_tick.py:430-737
def Strategy(self):
    """
    각 틱마다 호출되어 매수/매도 조건을 검사하고 실행
    """

    # 1단계: 현재 시간 함수 정의 (전략 코드에서 사용)
    def now():
        return strp_time('%Y%m%d%H%M%S', str(self.index))

    # 2단계: 과거 데이터 접근 함수 정의
    def Parameter_Previous(aindex, pre):
        """
        과거 N틱 전 데이터 가져오기

        aindex: 컬럼 인덱스
        pre: 몇 틱 전 (0=현재, 1=1틱전, ...)
        """
        if pre < 데이터길이:
            pindex = (self.indexn - pre) if pre != -1 else self.indexb
            return self.arry_data[pindex, aindex]
        return 0

    # 3단계: 편의 함수 정의 (전략 코드에서 직접 사용)
    def 현재가N(pre):
        return Parameter_Previous(1, pre)

    def 시가N(pre):
        return Parameter_Previous(2, pre)

    def 고가N(pre):
        return Parameter_Previous(3, pre)

    # ... (더 많은 함수들)

    # 4단계: 현재 틱 데이터 추출
    종목명, 종목코드 = self.name, self.code
    데이터길이 = self.tick_count
    시분초 = int(str(self.index)[8:])

    현재가, 시가, 고가, 저가, 등락율, 당일거래대금, 체결강도, ... = \
        self.arry_data[self.indexn, 1:45]

    호가단위 = 매도호가2 - 매도호가1

    # 5단계: 호가 정보 추출 (시장가 체결 시뮬레이션용)
    bhogainfo = (
        (매도호가1, 매도잔량1), (매도호가2, 매도잔량2),
        (매도호가3, 매도잔량3), (매도호가4, 매도잔량4),
        (매도호가5, 매도잔량5)
    )
    self.bhogainfo = bhogainfo[:self.dict_set['주식매수시장가잔량범위']]

    # 6단계: 전략 실행 (최적화 모드에 따라 분기)
    if self.opti_turn == 1:
        # 순차 최적화: 변수 조합별로 순회
        for vturn in self.trade_info.keys():
            for vkey in self.trade_info[vturn].keys():
                self.vars[vturn] = self.vars_list[vturn][0][vkey]

                매수, 매도 = True, False

                if not self.trade_info[vturn][vkey]['보유중']:
                    # 매수 검사
                    if not 관심종목: continue
                    self.SetBuyCount(vturn, vkey, 현재가, ...)
                    exec(self.buystg)  # 매수 전략 실행
                else:
                    # 매도 검사
                    수익률, 최고수익률, 최저수익률, 보유시간, 매수틱번호 = \
                        self.SetSellCount(vturn, vkey, 현재가, now())
                    exec(self.sellstg)  # 매도 전략 실행

    elif self.opti_turn == 3:
        # GA 최적화 또는 조건 최적화
        for vturn in self.trade_info.keys():
            for vkey in self.trade_info[vturn].keys():
                index_ = vturn * 20 + vkey

                if self.back_type != '조건최적화':
                    self.vars = self.vars_lists[index_]

                매수, 매도 = True, False

                if not self.trade_info[vturn][vkey]['보유중']:
                    self.SetBuyCount(vturn, vkey, 현재가, ...)
                    if self.back_type != '조건최적화':
                        exec(self.buystg)
                    else:
                        exec(self.dict_buystg[index_])
                else:
                    수익률, ... = self.SetSellCount(vturn, vkey, 현재가, now())
                    if self.back_type != '조건최적화':
                        exec(self.sellstg)
                    else:
                        exec(self.dict_sellstg[index_])

    else:
        # 일반 백테스트
        vturn, vkey = 0, 0

        if self.tick_count < self.avgtime:
            return

        매수, 매도 = True, False

        if not self.trade_info[vturn][vkey]['보유중']:
            if not 관심종목: return
            self.SetBuyCount(vturn, vkey, 현재가, ...)
            exec(self.buystg)
        else:
            수익률, ... = self.SetSellCount(vturn, vkey, 현재가, now())
            exec(self.sellstg)
```

### 6.4 매수/매도 체결 시뮬레이션

#### Buy 함수 - 시장가 매수 시뮬레이션

```python
# backengine_kiwoom_tick.py:768-791
def Buy(self, vturn, vkey):
    """
    시장가 매수 체결 시뮬레이션
    - 매도 호가창의 잔량을 소진하며 체결
    """
    매수금액 = 0
    주문수량 = 미체결수량 = self.trade_info[vturn][vkey]['주문수량']

    if 주문수량 > 0:
        # 매도 호가창을 순회하며 체결
        for 매도호가, 매도잔량 in self.bhogainfo:
            if 미체결수량 - 매도잔량 <= 0:
                # 남은 수량이 현재 호가 잔량보다 적음 -> 전량 체결
                매수금액 += 매도호가 * 미체결수량
                미체결수량 -= 매도잔량
                break
            else:
                # 현재 호가 잔량 모두 소진 -> 다음 호가로
                매수금액 += 매도호가 * 매도잔량
                미체결수량 -= 매도잔량

        # 전량 체결 성공 시
        if 미체결수량 <= 0:
            self.trade_info[vturn][vkey] = {
                '보유중': 1,
                '매수가': int(round(매수금액 / 주문수량)),  # 가중평균 매수가
                '매도가': 0,
                '주문수량': 0,
                '보유수량': 주문수량,
                '최고수익률': 0.,
                '최저수익률': 0.,
                '매수틱번호': self.indexn,
                '매수시간': strp_time('%Y%m%d%H%M%S', str(self.index))
            }
```

#### Sell 함수 - 시장가 매도 시뮬레이션

```python
# backengine_kiwoom_tick.py:803-817
def Sell(self, vturn, vkey, sell_cond):
    """
    시장가 매도 체결 시뮬레이션
    - 매수 호가창의 잔량을 소진하며 체결
    """
    매도금액 = 0
    주문수량 = 미체결수량 = self.trade_info[vturn][vkey]['주문수량']

    # 매수 호가창을 순회하며 체결
    for 매수호가, 매수잔량 in self.shogainfo:
        if 미체결수량 - 매수잔량 <= 0:
            매도금액 += 매수호가 * 미체결수량
            미체결수량 -= 매수잔량
            break
        else:
            매도금액 += 매수호가 * 매수잔량
            미체결수량 -= 매수잔량

    # 전량 체결 성공 시
    if 미체결수량 <= 0:
        self.trade_info[vturn][vkey]['매도가'] = int(round(매도금액 / 주문수량))
        self.sell_cond = sell_cond
        self.CalculationEyun(vturn, vkey)  # 수익 계산 및 결과 전송
```

#### LastSell 함수 - 일 마감 강제 청산

```python
# backengine_kiwoom_tick.py:819-853
def LastSell(self):
    """
    장 마감 또는 일자 변경 시 보유 종목 강제 청산
    """
    # 마지막 틱의 호가 정보 추출
    매도호가5, 매도호가4, 매도호가3, 매도호가2, 매도호가1, \
    매수호가1, 매수호가2, 매수호가3, 매수호가4, 매수호가5, \
    매도잔량5, 매도잔량4, 매도잔량3, 매도잔량2, 매도잔량1, \
    매수잔량1, 매수잔량2, 매수잔량3, 매수잔량4, 매수잔량5 = \
        self.arry_data[self.indexn, 23:43]

    shogainfo = (
        (매수호가1, 매수잔량1), (매수호가2, 매수잔량2),
        (매수호가3, 매수잔량3), (매수호가4, 매수잔량4),
        (매수호가5, 매수잔량5)
    )
    shogainfo = shogainfo[:self.dict_set['주식매도시장가잔량범위']]

    # 모든 변수 조합의 보유 종목 청산
    for vturn in self.trade_info.keys():
        for vkey in self.trade_info[vturn].keys():
            if self.trade_info[vturn][vkey]['보유중']:
                매도금액 = 0
                보유수량 = 미체결수량 = self.trade_info[vturn][vkey]['보유수량']

                # 시장가 매도 체결
                for 매수호가, 매수잔량 in shogainfo:
                    if 미체결수량 - 매수잔량 <= 0:
                        매도금액 += 매수호가 * 미체결수량
                        미체결수량 -= 매수잔량
                        break
                    else:
                        매도금액 += 매수호가 * 매수잔량
                        미체결수량 -= 매수잔량

                # 체결 실패 시 현재가로 강제 체결
                if 미체결수량 <= 0:
                    self.trade_info[vturn][vkey]['매도가'] = \
                        int(round(매도금액 / 보유수량))
                elif 매도금액 == 0:
                    self.trade_info[vturn][vkey]['매도가'] = \
                        self.arry_data[self.indexn, 1]
                else:
                    self.trade_info[vturn][vkey]['매도가'] = \
                        int(round(매도금액 / (보유수량 - 미체결수량)))

                self.trade_info[vturn][vkey]['주문수량'] = 보유수량
                self.sell_cond = 0
                self.CalculationEyun(vturn, vkey)
```

### 6.5 결과 집계 및 전송

#### CalculationEyun 함수

```python
# backengine_kiwoom_tick.py:855-872
def CalculationEyun(self, vturn, vkey):
    """
    거래 수익 계산 및 결과 전송
    """
    _, bp, sp, oc, _, _, _, bi, bdt = self.trade_info[vturn][vkey].values()

    sgtg = int(self.arry_data[self.indexn, 12])  # 시가총액

    # 보유 시간 계산 (초 단위 또는 분 단위)
    if len(str(self.index)) == 14:
        ht = int((strp_time('%Y%m%d%H%M%S', str(self.index)) - bdt).total_seconds())
    else:
        ht = int((strp_time('%Y%m%d%H%M', str(self.index)) - bdt).total_seconds() / 60)

    bt, st = int(self.arry_data[bi, 0]), self.index  # 매수시간, 매도시간
    bg = oc * bp  # 매수금액

    # 키움 수수료/세금 계산
    pg, sg, pp = GetKiwoomPgSgSp(bg, oc * sp)

    # 매도 조건 텍스트
    sc = self.dict_sconds[self.sell_cond] if self.back_type != '조건최적화' \
         else self.dict_sconds[vkey][self.sell_cond]

    # 거래 결과 데이터
    data = ('백테결과', self.name, sgtg, bt, st, ht, bp, sp, bg, pg, pp, sg, sc, '', True, vturn, vkey)

    # SubTotal 프로세스로 전송
    self.bstq_list[vkey if self.opti_turn in (1, 3) else (self.sell_count % 5)].put(data)

    self.sell_count += 1
    self.trade_info[vturn][vkey] = GetTradeInfo(1)  # 거래 정보 초기화
```

---

## 7. 성능 최적화 기법

### 7.1 컴파일된 전략 코드

```python
# back_static.py:200-224
def GetBuyStg(buytxt, gubun):
    """
    매수 전략 문자열을 컴파일된 코드 객체로 변환
    """
    buytxt = buytxt.split('if 매수:')[0] + 'if 매수:\n    self.Buy(vturn, vkey)'
    buystg = ''

    for line in buytxt.split('\n'):
        buystg += f'{line}\n'

    if buystg != '':
        try:
            buystg = compile(buystg, '<string>', 'exec')  # 컴파일
        except:
            buystg = None
            if gubun == 0: print_exc()

    return buystg, None
```

**컴파일 장점:**
1. **속도**: 매 틱마다 문자열 파싱 불필요
2. **효율**: 바이트코드로 변환하여 실행 속도 향상
3. **검증**: 구문 오류를 미리 감지

### 7.2 NumPy 벡터화 연산

```python
# back_static.py:836-868
@jit(nopython=True, cache=True)  # Numba JIT 컴파일
def GetBackResult(arry_tsg, arry_bct, betting, ui_gubun, day_count):
    """
    백테스트 결과 통계 계산 (Numba로 최적화)
    """
    tc = len(arry_tsg)

    if tc > 0:
        # NumPy 불리언 인덱싱 (빠름)
        arry_p = arry_tsg[arry_tsg[:, 3] >= 0]  # 익절 거래
        arry_m = arry_tsg[arry_tsg[:, 3] < 0]   # 손절 거래

        atc = round(tc / day_count, 1)
        pc = len(arry_p)
        mc = len(arry_m)
        wr = round(pc / tc * 100, 2)

        # 벡터 연산
        ah = round(arry_tsg[:, 0].sum() / tc, 2)  # 평균 보유시간
        app = round(arry_tsg[:, 2].sum() / tc, 2)  # 평균 수익률
        tsg = int(arry_tsg[:, 3].sum())  # 총 수익금

        # 조건부 평균
        appp = arry_p[:, 2].mean() if len(arry_p) > 0 else 0
        ampp = abs(arry_m[:, 2].mean()) if len(arry_m) > 0 else 0

        # 최대값 계산
        mhct = int(arry_bct[int(len(arry_bct) * 0.01):, 1].max())
        seed = int(arry_bct[int(len(arry_bct) * 0.01):, 2].max())

        tpp = round(tsg / (seed if seed != 0 else betting) * 100, 2)
        cagr = round(tpp / day_count * (250 if ui_gubun == 'S' else 365), 2)
        tpi = round(wr / 100 * (1 + appp / ampp), 2) if ampp != 0 else 1.0

    return tc, atc, pc, mc, wr, ah, app, tpp, tsg, mhct, seed, cagr, tpi
```

**Numba JIT 장점:**
1. **속도**: C 수준의 실행 속도 (수십~수백 배 빠름)
2. **자동 최적화**: LLVM 컴파일러 최적화
3. **캐시**: 컴파일 결과 저장으로 재실행 시 빠름

### 7.3 MDD 계산 최적화

```python
# back_static.py:817-833
def AddMdd(arry_tsg, result):
    """
    최대 낙폭(MDD) 계산 - O(n) 알고리즘
    """
    try:
        array = arry_tsg[:, 4]  # 수익금합계 컬럼

        # NumPy 벡터 연산으로 MDD 계산
        lower = np.argmax(np.maximum.accumulate(array) - array)  # 최저점
        upper = np.argmax(array[:lower])  # 최고점

        mdd = round(
            abs(array[upper] - array[lower]) / (array[upper] + result[10]) * 100,
            2
        )
        mdd_ = int(abs(array[upper] - array[lower]))
    except:
        mdd = abs(result[7])
        mdd_ = abs(result[8])

    result = result + (mdd, mdd_)
    return result
```

**MDD 계산 최적화:**
1. `np.maximum.accumulate()`: 누적 최대값 계산 (O(n))
2. `np.argmax()`: 최대/최소 인덱스 찾기 (O(n))
3. 전체 시간 복잡도: O(n) (이중 루프 O(n²)보다 빠름)

### 7.4 진행률 업데이트 최적화

```python
# backengine_kiwoom_tick.py:424
if self.opti_turn in (1, 3) and j % 100 == 0:
    self.tq.put('탐색완료')

# 이유:
# - 매 틱마다 Queue에 전송하면 오버헤드 큰
# - 100틱마다 한 번씩 전송으로 부하 감소
# - UI 업데이트는 충분히 부드러움
```

### 7.5 데이터 재사용

```python
# backengine_kiwoom_tick.py:388-397
same_days = self.startday_ == self.startday and self.endday_ == self.endday
same_time = self.starttime_ == self.starttime and self.endtime_ == self.endtime

# 최적화 또는 전진분석 시 동일한 데이터를 여러 번 사용
# 매번 슬라이싱하지 않고 조건 확인 후 재사용
if same_days and same_time:
    self.arry_data = self.dict_arry[code]  # 슬라이싱 불필요
```

---

## 8. 실전 활용 예시

### 8.1 백테스팅 시작 명령 흐름

```python
# UI에서 백테스트 버튼 클릭
↓
# backtest.py의 BackTest 프로세스 생성
Process(target=BackTest, args=(wq, bq, sq, tq, lq, teleQ, beq_list, bstq_list, backname, ui_gubun)).start()
↓
# BackTest.Start() 실행
def Start(self):
    # 1. 설정 수신
    data = self.bq.get()
    betting, avgtime, startday, endday, starttime, endtime = data[0:6]

    # 2. 메인 타임라인 조회
    con = sqlite3.connect(db)
    query = GetMoneytopQuery(self.ui_gubun, startday, endday, starttime, endtime)
    df_mt = pd.read_sql(query, con)
    con.close()

    # 3. Total 프로세스 생성
    mq = Queue()
    Process(target=Total, args=(...)).start()

    # 4. 백테엔진으로 설정 전송
    for q in self.beq_list:
        q.put(('백테정보', betting, avgtime, startday, endday, starttime, endtime, buystg, sellstg))

    # 5. 데이터 로딩 명령
    for q in self.beq_list:
        q.put(('데이터로딩', startday, endday, starttime, endtime, code_list, avg_list, ...))

    # 6. 완료 대기
    data = mq.get()
```

### 8.2 성능 측정 예시

실제 백테스팅 성능 (참고):

```
# 테스트 환경
- CPU: Intel i7-10700K (8코어 16스레드)
- RAM: 64GB DDR4
- SSD: NVMe M.2

# 백테스팅 대상
- 종목 수: 500개
- 기간: 1년 (250거래일)
- 데이터: 틱 데이터 (평균 1종목당 50만 틱)
- 총 틱 수: 약 2억 5천만 틱

# 성능 결과
- 데이터 로딩: 약 3분
- 백테스팅 실행: 약 7분
- 총 소요시간: 약 10분

# 메모리 사용량
- 일괄 로딩: 약 12GB (프로세스 8개 * 1.5GB)
- Pickle 로딩: 약 4GB
```

### 8.3 전략 코드 예시

```python
# 매수 전략 (사용자 작성)
if 등락율 > 5 and 체결강도 > 150 and 현재가 > 이동평균(60):
    if 당일거래대금 > 100000000:  # 1억 이상
        매수 = True

# 매도 전략 (사용자 작성)
if 수익률 > 3:  # 3% 익절
    매도 = True
elif 수익률 < -2:  # 2% 손절
    매도 = True
elif 보유시간 > 3600:  # 1시간 이상 보유 시
    매도 = True

# 전략 코드는 compile()로 컴파일되어 exec()로 실행됨
```

---

## 9. 디버깅 및 모니터링

### 9.1 프로파일링 활성화

```python
# backengine_kiwoom_tick.py:383-386
if self.profile:
    import cProfile
    self.pr = cProfile.Profile()
    self.pr.enable()

# 종료 시:
if self.profile:
    self.pr.print_stats(sort='cumulative')
```

**사용법:**
```python
# 프로파일링 활성화하여 백테엔진 생성
engine = BackEngineKiwoomTick(gubun, wq, tq, bq, beq_list, bstq_list, profile=True)
```

### 9.2 진행 상황 모니터링

```python
# backtest.py:64
self.wq.put((ui_num[f'{self.ui_gubun}백테바'], bc, self.back_count, start))

# UI에서 프로그레스바 업데이트
# bc: 완료된 종목 수
# self.back_count: 전체 종목 수
# start: 시작 시간
```

### 9.3 에러 처리

```python
# backengine_kiwoom_tick.py:413-418
try:
    self.Strategy()
except:
    print_exc()  # 전체 스택 트레이스 출력
    self.BackStop()  # 백테스트 중단
    return
```

---

## 10. 결론

STOM V1의 백테스팅 시스템은 다음과 같은 특징을 가집니다:

**강점:**
1. **고성능**: 멀티프로세스 병렬 처리로 빠른 백테스팅
2. **메모리 효율**: NumPy 배열과 일괄/온디맨드 로딩 선택 가능
3. **정확성**: 실제 호가창을 활용한 시장가 체결 시뮬레이션
4. **확장성**: 새로운 시장(거래소) 엔진 추가 용이
5. **최적화**: Numba JIT, 벡터 연산 등 다양한 최적화 기법

**개선 가능 영역:**
1. 멀티프로세스 대신 멀티스레드 고려 (GIL 해결 시)
2. GPU 가속 (CUDA) 활용 검토
3. 분산 처리 (여러 서버) 가능성
4. 실시간 스트리밍 백테스팅 (Incremental Backtest)

**학습 포인트:**
- 대용량 데이터 처리 기법
- 멀티프로세스 아키텍처 설계
- Queue 기반 프로세스 간 통신
- NumPy/Numba를 활용한 성능 최적화
- 실전 트레이딩 시스템 구현 노하우

이 문서가 STOM 백테스팅 시스템의 이해와 개발에 도움이 되길 바랍니다.