# 주식 틱데이터 데이터베이스 구조

이 문서는 STOM 주식 틱, 분 데이터를 SQLite3 형태로 수집했을 때 생성되는 데이터베이스의 구조를 설명합니다. 각 열은 주식 데이터의 다양한 측면을 나타내며, 데이터 타입은 `INTEGER` 또는 `REAL`입니다.

---

## 📋 목차

- [데이터베이스 스키마](#데이터베이스-스키마)
- [데이터베이스 접근 예제](#데이터베이스-접근-예제)
- [인덱스 정보](#인덱스-정보)
- [데이터 수집 주기](#데이터-수집-주기)
- [스토리지 관리](#스토리지-관리)
- [성능 최적화 팁](#성능-최적화-팁)

---

## 데이터베이스 스키마

### 주식 틱 데이터 (stock_tick)

| 열 이름 | 데이터 타입 | 설명 |
|---------|-------------|------|
| index | INTEGER | 데이터의 인덱스 번호 |
| 현재가 | REAL | 현재 주식 가격 |
| 시가 | REAL | 당일 시작 가격 |
| 고가 | REAL | 당일 최고 가격 |
| 저가 | REAL | 당일 최저 가격 |
| 등락율 | REAL | 가격 변동률 |
| 당일거래대금 | REAL | 당일 거래된 총 금액 |
| 체결강도 | REAL | 체결 강도 |
| 거래대금증감 | REAL | 거래 대금의 증감 |
| 전일비 | REAL | 전일 대비 가격 변화 |
| 회전율 | REAL | 주식 회전율 |
| 전일동시간비 | REAL | 전일 동일 시간 대비 |
| 시가총액 | REAL | 시가 총액 |
| 라운드피겨위5호가이내 | REAL | 라운드 피겨 위 5호가 이내 |
| 초당매수수량 | REAL | 초당 매수 수량 |
| 초당매도수량 | REAL | 초당 매도 수량 |
| VI해제시간 | REAL | VI 해제 시간 |
| VI가격 | REAL | VI 가격 |
| VI호가단위 | REAL | VI 호가 단위 |
| 초당거래대금 | REAL | 초당 거래 대금 |
| 고저평균대비등락율 | REAL | 고저 평균 대비 등락율 |
| 매도총잔량 | REAL | 매도 총 잔량 |
| 매수총잔량 | REAL | 매수 총 잔량 |
| 매도호가5 | REAL | 매도 호가 5 |
| 매도호가4 | REAL | 매도 호가 4 |
| 매도호가3 | REAL | 매도 호가 3 |
| 매도호가2 | REAL | 매도 호가 2 |
| 매도호가1 | REAL | 매도 호가 1 |
| 매수호가1 | REAL | 매수 호가 1 |
| 매수호가2 | REAL | 매수 호가 2 |
| 매수호가3 | REAL | 매수 호가 3 |
| 매수호가4 | REAL | 매수 호가 4 |
| 매수호가5 | REAL | 매수 호가 5 |
| 매도잔량5 | REAL | 매도 잔량 5 |
| 매도잔량4 | REAL | 매도 잔량 4 |
| 매도잔량3 | REAL | 매도 잔량 3 |
| 매도잔량2 | REAL | 매도 잔량 2 |
| 매도잔량1 | REAL | 매도 잔량 1 |
| 매수잔량1 | REAL | 매수 잔량 1 |
| 매수잔량2 | REAL | 매수 잔량 2 |
| 매수잔량3 | REAL | 매수 잔량 3 |
| 매수잔량4 | REAL | 매수 잔량 4 |
| 매수잔량5 | REAL | 매수 잔량 5 |
| 매도수5호가잔량합 | REAL | 매도수 5호가 잔량 합 |
| 관심종목 | REAL | 관심 종목 여부 |

---

## 데이터베이스 접근 예제

### 틱 데이터 조회

특정 종목의 틱 데이터를 조회하는 방법:

```sql
-- 삼성전자(005930) 틱 데이터 조회
SELECT
    index,
    현재가,
    시가,
    고가,
    저가,
    초당거래대금,
    체결강도
FROM stock_tick_005930
WHERE index BETWEEN 0 AND 1000
ORDER BY index ASC;
```

### 특정 시간대 데이터 조회

```sql
-- 장 시작 후 30분간 데이터 조회
SELECT
    index,
    현재가,
    초당거래대금,
    체결강도,
    등락율
FROM stock_tick_005930
WHERE index BETWEEN 0 AND 1800  -- 30분 = 1800초
ORDER BY index ASC;
```

### 고체결강도 구간 찾기

```sql
-- 체결강도가 150 이상인 시점 찾기
SELECT
    index,
    현재가,
    체결강도,
    초당거래대금,
    등락율
FROM stock_tick_005930
WHERE 체결강도 >= 150
ORDER BY index ASC;
```

### 분봉 데이터 집계

틱 데이터로부터 분봉 데이터를 집계하는 쿼리:

```sql
-- 1분봉 데이터 생성 (60초 단위 집계)
SELECT
    (index / 60) as minute,
    MIN(index) as start_index,
    MAX(index) as end_index,

    -- OHLC 데이터
    (SELECT 현재가 FROM stock_tick_005930
     WHERE index = MIN(t.index)) as open,
    MAX(고가) as high,
    MIN(저가) as low,
    (SELECT 현재가 FROM stock_tick_005930
     WHERE index = MAX(t.index)) as close,

    -- 거래량 데이터
    SUM(초당거래대금) as total_volume,
    AVG(체결강도) as avg_strength
FROM stock_tick_005930 t
GROUP BY (index / 60)
ORDER BY minute ASC;
```

### 호가창 분석

```sql
-- 매수/매도 호가 불균형 분석
SELECT
    index,
    현재가,
    (매수총잔량 - 매도총잔량) as 호가불균형,
    (매수총잔량 * 100.0 / (매수총잔량 + 매도총잔량)) as 매수비율,
    체결강도
FROM stock_tick_005930
WHERE ABS(매수총잔량 - 매도총잔량) > 10000
ORDER BY index ASC;
```

### 성과 분석 쿼리

```sql
-- 등락율 변화 추이 분석
SELECT
    (index / 60) as minute,
    MIN(등락율) as min_rate,
    MAX(등락율) as max_rate,
    AVG(등락율) as avg_rate,
    (MAX(등락율) - MIN(등락율)) as volatility
FROM stock_tick_005930
GROUP BY (index / 60)
HAVING volatility > 1.0
ORDER BY minute ASC;
```

---

## 인덱스 정보

STOM에서 사용하는 데이터베이스 인덱스 구조:

### 주요 인덱스

1. **PRIMARY KEY**: `(종목코드, index)`
   - 각 종목별로 독립적인 테이블 생성
   - index 컬럼이 기본 정렬 키

2. **index 컬럼 INDEX**
   - 시간순 조회 최적화
   - BETWEEN 쿼리 성능 향상

### 인덱스 생성 예제

```sql
-- 종목별 테이블 생성
CREATE TABLE IF NOT EXISTS stock_tick_005930 (
    index INTEGER PRIMARY KEY,
    현재가 REAL,
    시가 REAL,
    고가 REAL,
    저가 REAL,
    등락율 REAL,
    당일거래대금 REAL,
    체결강도 REAL,
    -- ... (나머지 컬럼)
);

-- 체결강도 인덱스 (자주 조회되는 경우)
CREATE INDEX IF NOT EXISTS idx_strength
ON stock_tick_005930(체결강도);

-- 등락율 인덱스
CREATE INDEX IF NOT EXISTS idx_rate
ON stock_tick_005930(등락율);
```

### 인덱스 최적화 팁

- **선택적 인덱스**: 자주 WHERE 절에 사용되는 컬럼만 인덱스 생성
- **복합 인덱스**: 여러 컬럼을 함께 조회하는 경우 복합 인덱스 고려
- **인덱스 크기**: 과도한 인덱스는 INSERT 성능 저하 유발

---

## 데이터 수집 주기

### 실시간 데이터 수집

| 데이터 종류 | 수집 주기 | 저장 방식 |
|------------|----------|-----------|
| 틱 데이터 | 실시간 (초당) | 메모리 → DB 배치 저장 |
| 분봉 데이터 | 1분마다 집계 | 직접 DB 저장 |
| 일봉 데이터 | 장 마감 후 | 집계 후 저장 |
| 호가 데이터 | 실시간 (변동 시) | 틱 데이터에 포함 |

### 데이터 수집 프로세스

1. **실시간 수신**: 키움 OpenAPI를 통해 실시간 데이터 수신
2. **메모리 버퍼링**: 큐(Queue)에 임시 저장
3. **배치 저장**: 일정 간격(예: 10초)마다 DB에 일괄 저장
4. **인덱스 업데이트**: 저장 후 자동으로 인덱스 갱신

### 데이터 무결성 확인

```python
# 데이터 무결성 체크 예제
def check_data_integrity(code, date):
    # 1. 틱 개수 확인 (장시간 6시간 30분 = 23,400초)
    expected_ticks = 23400
    actual_ticks = get_tick_count(code, date)

    # 2. 데이터 결측 확인
    missing_ranges = find_missing_index_ranges(code, date)

    # 3. 이상치 확인
    outliers = find_outliers(code, date)

    return {
        'expected': expected_ticks,
        'actual': actual_ticks,
        'completeness': actual_ticks / expected_ticks * 100,
        'missing': missing_ranges,
        'outliers': outliers
    }
```

---

## 스토리지 관리

### 예상 데이터 크기

| 항목 | 크기 |
|------|------|
| 1종목 1일 틱 데이터 | 약 10-15 MB |
| 1종목 1개월 틱 데이터 | 약 200-300 MB |
| 1종목 1년 틱 데이터 | 약 2.5-3.5 GB |
| 100종목 1년 틱 데이터 | 약 250-350 GB |
| 1종목 1년 분봉 데이터 | 약 50-100 MB |

### 데이터 보관 정책

| 데이터 종류 | 보관 기간 | 압축 여부 | 백업 주기 |
|------------|----------|----------|----------|
| 틱 데이터 | 최근 3개월 | 3개월 이후 압축 | 주 1회 |
| 분봉 데이터 | 최근 1년 | 1년 이후 압축 | 월 1회 |
| 일봉 데이터 | 영구 보관 | 압축 저장 | 월 1회 |
| 백테스트 결과 | 6개월 | 압축 저장 | 필요 시 |

### 데이터 아카이빙

```python
# 오래된 데이터 아카이빙 예제
def archive_old_data(days_threshold=90):
    """
    90일 이전 틱 데이터를 압축 아카이브
    """
    import sqlite3
    import gzip
    import pickle
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=days_threshold)

    # 1. 오래된 데이터 추출
    conn = sqlite3.connect('stock_tick.db')
    old_data = pd.read_sql(
        f"SELECT * FROM stock_tick WHERE date < '{cutoff_date}'",
        conn
    )

    # 2. 압축 저장
    with gzip.open(f'archive_tick_{cutoff_date}.pkl.gz', 'wb') as f:
        pickle.dump(old_data, f)

    # 3. 원본 데이터 삭제
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM stock_tick WHERE date < '{cutoff_date}'")
    conn.commit()

    # 4. VACUUM으로 DB 크기 최적화
    cursor.execute("VACUUM")
    conn.close()

    return len(old_data)
```

### 디스크 공간 관리

```sql
-- 데이터베이스 크기 확인
SELECT
    name,
    (page_count * page_size) / 1024 / 1024 as size_mb
FROM pragma_page_count(), pragma_page_size();

-- 테이블별 크기 확인
SELECT
    name,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as row_count
FROM sqlite_master m
WHERE type='table';
```

---

## 성능 최적화 팁

### 1. 배치 삽입 최적화

```python
# ❌ 비효율적: 한 번에 하나씩 삽입
for tick in tick_data:
    cursor.execute("INSERT INTO stock_tick VALUES (?,...)", tick)
    conn.commit()

# ✅ 효율적: 배치 삽입
cursor.executemany("INSERT INTO stock_tick VALUES (?,...)", tick_data)
conn.commit()
```

### 2. 트랜잭션 활용

```python
# 대량 데이터 삽입 시 트랜잭션 사용
conn.execute("BEGIN TRANSACTION")
try:
    cursor.executemany("INSERT INTO stock_tick VALUES (?,...)", large_dataset)
    conn.commit()
except Exception as e:
    conn.rollback()
    raise e
```

### 3. WAL 모드 활용

```python
# Write-Ahead Logging 모드 활성화 (동시 읽기/쓰기 성능 향상)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
```

### 4. 메모리 최적화

```python
# 대용량 데이터 조회 시 청크 단위 처리
def read_large_data(table_name, chunk_size=10000):
    offset = 0
    while True:
        query = f"""
        SELECT * FROM {table_name}
        LIMIT {chunk_size} OFFSET {offset}
        """
        chunk = pd.read_sql(query, conn)

        if len(chunk) == 0:
            break

        yield chunk
        offset += chunk_size
```

### 5. 쿼리 최적화

```sql
-- ❌ 비효율적: 전체 테이블 스캔
SELECT * FROM stock_tick WHERE 등락율 > 5;

-- ✅ 효율적: 인덱스 활용 + 필요한 컬럼만 선택
CREATE INDEX idx_rate ON stock_tick(등락율);
SELECT index, 현재가, 등락율 FROM stock_tick WHERE 등락율 > 5;
```

### 6. 연결 풀링

```python
# 데이터베이스 연결 재사용
class DBConnectionPool:
    def __init__(self, db_path, pool_size=5):
        self.pool = Queue(maxsize=pool_size)
        for _ in range(pool_size):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            self.pool.put(conn)

    def get_connection(self):
        return self.pool.get()

    def return_connection(self, conn):
        self.pool.put(conn)
```

---

## 참고 사항

### 관련 문서

- [틱 백테스팅 가이드라인](Back_Testing_Guideline_Tick.md)
- [분봉 백테스팅 가이드라인](Back_Testing_Guideline_Min.md)

### 데이터 활용 예제

실제 백테스팅 및 실시간 트레이딩에서 이 데이터베이스를 활용하는 방법은 백테스팅 가이드라인 문서를 참조하세요.

---

**작성일**: 2025-01-01
**최종 수정일**: 2025-11-17
**버전**: v2.0
