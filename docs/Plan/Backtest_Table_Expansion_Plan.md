# 백테스팅 상세기록 테이블 확장 및 데이터 분석 시각화 계획

**문서 버전**: v1.0
**작성일**: 2025-12-08
**상태**: 계획 단계

---

## 1. 프로젝트 개요

### 1.1 목적

백테스팅 상세기록 테이블을 확장하여 매수 시점의 상세 시장 데이터를 추가하고, 수집된 데이터를 시각화하여 텔레그램으로 전송함으로써 트레이딩 전략 분석 능력을 강화합니다.

### 1.2 현재 상태

**현재 테이블 컬럼 (14개)**:
```
종목명, 시가총액, 매수시간, 매도시간, 보유시간, 매수가, 매도가,
매수금액, 매도금액, 수익률, 수익금, 수익금합계, 매도조건, 추가매수시간
```

**관련 파일**:
| 파일 | 역할 | 위치 |
|------|------|------|
| `utility/setting.py:402-403` | `columns_bt`, `columns_btf` 정의 | 컬럼 정의 |
| `backtester/backengine_kiwoom_tick.py:869` | 백테결과 데이터 생성 | 데이터 수집 |
| `backtester/back_subtotal.py:83-100` | 데이터 집계 | 데이터 처리 |
| `backtester/back_static.py:615-828` | 차트 생성 (`PltShow`) | 시각화 |
| `ui/ui_update_tablewidget.py:100-105` | 테이블 업데이트 | UI 표시 |
| `utility/telegram_msg.py:97-105` | 텔레그램 이미지 전송 | 알림 |

---

## 2. 확장 계획

### 2.1 추가할 컬럼 목록

#### Phase 1: 시간 분해 컬럼 (4개)
매수시간을 분해하여 시간대별 분석을 용이하게 합니다.

| 컬럼명 | 타입 | 설명 | 추출 방법 |
|--------|------|------|-----------|
| `매수일자` | str | YYYYMMDD | `str(bt)[:8]` |
| `매수시` | int | HH (0-23) | `int(str(bt)[8:10])` |
| `매수분` | int | MM (0-59) | `int(str(bt)[10:12])` |
| `매수초` | int | SS (0-59) | `int(str(bt)[12:14])` |

#### Phase 2: 매수 시점 시장 데이터 (10개)
매수 시점의 시장 상황을 기록합니다.

| 컬럼명 | 타입 | 데이터베이스 컬럼 인덱스 | 설명 |
|--------|------|------------------------|------|
| `매수등락율` | float | `arry_data[bi, 5]` | 전일 대비 등락률 (%) |
| `매수시가등락율` | float | 계산 필요 | (현재가-시가)/시가*100 |
| `매수당일거래대금` | int | `arry_data[bi, 6]` | 당일 누적 거래대금 |
| `매수체결강도` | float | `arry_data[bi, 7]` | 체결강도 (매수/매도 비율) |
| `매수전일비` | float | `arry_data[bi, 9]` | 전일 거래량 대비 비율 |
| `매수회전율` | float | `arry_data[bi, 10]` | 상장주식 대비 거래량 비율 |
| `매수전일동시간비` | float | `arry_data[bi, 11]` | 전일 동시간 대비 거래량 |
| `매수고가` | int | `arry_data[bi, 3]` | 당일 고가 |
| `매수저가` | int | `arry_data[bi, 4]` | 당일 저가 |
| `매수고저평균대비등락율` | float | `arry_data[bi, 17]` | 고저평균 대비 등락률 |

#### Phase 3: 호가 및 거래 데이터 (6개)
매수 시점의 호가창 상태를 기록합니다.

| 컬럼명 | 타입 | 데이터베이스 컬럼 인덱스 | 설명 |
|--------|------|------------------------|------|
| `매수매도총잔량` | int | `arry_data[bi, 18]` | 매도호가 1~5 잔량합 |
| `매수매수총잔량` | int | `arry_data[bi, 19]` | 매수호가 1~5 잔량합 |
| `매수호가잔량비` | float | 계산 필요 | 매수잔량/매도잔량*100 |
| `매수매도호가1` | int | `arry_data[bi, 24]` | 최우선 매도호가 |
| `매수매수호가1` | int | `arry_data[bi, 25]` | 최우선 매수호가 |
| `매수스프레드` | float | 계산 필요 | (매도1-매수1)/매수1*100 |

### 2.2 확장된 컬럼 목록 (총 34개)

```python
columns_bt_extended = [
    # 기존 컬럼 (14개)
    '종목명', '시가총액', '매수시간', '매도시간', '보유시간',
    '매수가', '매도가', '매수금액', '매도금액', '수익률',
    '수익금', '수익금합계', '매도조건', '추가매수시간',

    # Phase 1: 시간 분해 (4개)
    '매수일자', '매수시', '매수분', '매수초',

    # Phase 2: 시장 데이터 (10개)
    '매수등락율', '매수시가등락율', '매수당일거래대금', '매수체결강도',
    '매수전일비', '매수회전율', '매수전일동시간비',
    '매수고가', '매수저가', '매수고저평균대비등락율',

    # Phase 3: 호가 데이터 (6개)
    '매수매도총잔량', '매수매수총잔량', '매수호가잔량비',
    '매수매도호가1', '매수매수호가1', '매수스프레드'
]
```

---

## 3. 데이터 시각화 계획

### 3.1 추가할 시각화 차트

#### Chart 1: 시간대별 수익 분포
```
목적: 어느 시간대에 매수한 거래가 수익성이 좋은지 분석
X축: 매수시 (09~15시)
Y축: 평균 수익률 / 총 수익금
유형: 막대 그래프 (이익: 녹색, 손실: 빨간색)
```

#### Chart 2: 등락율별 수익 분포
```
목적: 어느 등락율 구간에서 매수한 거래가 수익성이 좋은지 분석
X축: 매수등락율 구간 (0-5%, 5-10%, 10-15%, 15-20%, 20%+)
Y축: 평균 수익률 / 거래 횟수 / 승률
유형: 복합 차트 (막대 + 라인)
```

#### Chart 3: 체결강도별 수익 분포
```
목적: 체결강도와 수익률의 상관관계 분석
X축: 매수체결강도 구간 (50-100, 100-150, 150-200, 200+)
Y축: 평균 수익률 / 거래 횟수
유형: 막대 그래프 + 추세선
```

#### Chart 4: 거래대금별 수익 분포
```
목적: 거래대금 수준에 따른 수익성 분석
X축: 매수당일거래대금 구간 (로그 스케일)
Y축: 평균 수익률 / 승률
유형: 히스토그램 + 박스플롯
```

#### Chart 5: 시가총액별 수익 분포
```
목적: 시가총액 구간별 수익성 분석
X축: 시가총액 구간 (소형주, 중형주, 대형주)
Y축: 평균 수익률 / 거래 횟수
유형: 막대 그래프
```

#### Chart 6: 상관관계 히트맵
```
목적: 각 변수 간 상관관계 파악
변수: 매수등락율, 매수체결강도, 매수회전율, 매수전일비, 수익률
유형: 히트맵 (상관계수 색상 표시)
```

#### Chart 7: 스캐터 플롯 (산점도)
```
목적: 주요 변수와 수익률의 관계 시각화
서브플롯:
  - 매수등락율 vs 수익률
  - 매수체결강도 vs 수익률
  - 보유시간 vs 수익률
  - 매수거래대금 vs 수익률
유형: 산점도 (2x2 그리드)
```

### 3.2 시각화 파일 구조

```
backtester/graph/
├── {전략명}_{날짜}.png           # 기존: 수익곡선 그래프
├── {전략명}_{날짜}_.png          # 기존: 부가정보 차트
├── {전략명}_{날짜}_analysis.png  # 신규: 분석 차트 (Chart 1-5)
└── {전략명}_{날짜}_corr.png      # 신규: 상관관계 차트 (Chart 6-7)
```

---

## 4. 구현 상세

### 4.1 수정 대상 파일

#### 4.1.1 `utility/setting.py`
```python
# 위치: Line 402-403
# 변경 내용: columns_bt, columns_btf 확장

# 기존
columns_bt = ['종목명', '시가총액', ...]  # 14개

# 변경
columns_bt = ['종목명', '시가총액', ..., '매수스프레드']  # 34개
columns_btf = ['종목명', '포지션', ..., '매수스프레드']  # 34개 (포지션 포함)
```

#### 4.1.2 `backtester/backengine_kiwoom_tick.py`
```python
# 위치: Line 855-869 (CalculationEyun 메서드)
# 변경 내용: 추가 데이터 수집

def CalculationEyun(self, vturn, vkey):
    _, bp, sp, oc, _, _, _, bi, bdt = self.trade_info[vturn][vkey].values()
    sgtg = int(self.arry_data[self.indexn, 12])

    # 기존 계산
    ...

    # 추가 데이터 수집
    buy_date = str(bt)[:8]  # YYYYMMDD
    buy_hour = int(str(bt)[8:10])
    buy_min = int(str(bt)[10:12])
    buy_sec = int(str(bt)[12:14])

    buy_등락율 = float(self.arry_data[bi, 5])
    buy_시가 = float(self.arry_data[bi, 2])
    buy_시가등락율 = round((bp - buy_시가) / buy_시가 * 100, 2) if buy_시가 > 0 else 0
    buy_당일거래대금 = int(self.arry_data[bi, 6])
    buy_체결강도 = float(self.arry_data[bi, 7])
    buy_전일비 = float(self.arry_data[bi, 9])
    buy_회전율 = float(self.arry_data[bi, 10])
    buy_전일동시간비 = float(self.arry_data[bi, 11])
    buy_고가 = int(self.arry_data[bi, 3])
    buy_저가 = int(self.arry_data[bi, 4])
    buy_고저평균대비등락율 = float(self.arry_data[bi, 17])
    buy_매도총잔량 = int(self.arry_data[bi, 18])
    buy_매수총잔량 = int(self.arry_data[bi, 19])
    buy_호가잔량비 = round(buy_매수총잔량 / buy_매도총잔량 * 100, 2) if buy_매도총잔량 > 0 else 0
    buy_매도호가1 = int(self.arry_data[bi, 24])
    buy_매수호가1 = int(self.arry_data[bi, 25])
    buy_스프레드 = round((buy_매도호가1 - buy_매수호가1) / buy_매수호가1 * 100, 4) if buy_매수호가1 > 0 else 0

    # 확장된 데이터 튜플
    data = ('백테결과', self.name, sgtg, bt, st, ht, bp, sp, bg, pg, pp, sg, sc, abt, bcx, vturn, vkey,
            buy_date, buy_hour, buy_min, buy_sec,
            buy_등락율, buy_시가등락율, buy_당일거래대금, buy_체결강도,
            buy_전일비, buy_회전율, buy_전일동시간비,
            buy_고가, buy_저가, buy_고저평균대비등락율,
            buy_매도총잔량, buy_매수총잔량, buy_호가잔량비,
            buy_매도호가1, buy_매수호가1, buy_스프레드)
```

#### 4.1.3 `backtester/back_subtotal.py`
```python
# 위치: Line 83-100 (CollectData 메서드)
# 변경 내용: 확장된 데이터 처리

# 데이터 언패킹 확장
(_, 종목명, 시가총액또는포지션, 매수시간, 매도시간, 보유시간,
 매수가, 매도가, 매수금액, 매도금액, 수익률, 수익금, 매도조건, 추가매수시간,
 bcx, vturn, vkey,
 매수일자, 매수시, 매수분, 매수초,
 매수등락율, 매수시가등락율, 매수당일거래대금, 매수체결강도,
 매수전일비, 매수회전율, 매수전일동시간비,
 매수고가, 매수저가, 매수고저평균대비등락율,
 매수매도총잔량, 매수매수총잔량, 매수호가잔량비,
 매수매도호가1, 매수매수호가1, 매수스프레드) = data
```

#### 4.1.4 `backtester/back_static.py`
```python
# 위치: Line 834-851 (GetResultDataframe 함수)
# 변경 내용: 컬럼 매핑 확장

# 기존 columns_bt/columns_btf에 맞춰 DataFrame 컬럼 매핑 확장
```

```python
# 위치: Line 615-828 (PltShow 함수)
# 추가 내용: 분석 차트 생성 함수

def PltAnalysisCharts(df_tsg, save_file_name, teleQ):
    """
    확장된 상세기록 데이터를 기반으로 분석 차트를 생성하고 텔레그램으로 전송
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, axes = plt.subplots(3, 2, figsize=(14, 18))

    # Chart 1: 시간대별 수익 분포
    # Chart 2: 등락율별 수익 분포
    # Chart 3: 체결강도별 수익 분포
    # Chart 4: 거래대금별 수익 분포
    # Chart 5: 시가총액별 수익 분포
    # Chart 6: 상관관계 히트맵

    plt.tight_layout()
    analysis_path = f"{GRAPH_PATH}/{save_file_name}_analysis.png"
    plt.savefig(analysis_path, dpi=100, bbox_inches='tight')
    plt.close()

    teleQ.put(analysis_path)
```

#### 4.1.5 `ui/set_widget.py`
```python
# 위치: Line 453-458
# 변경 내용: 테이블 컬럼 너비 조정

elif columns == columns_bt:
    # 확장된 컬럼에 대한 너비 설정
    tableWidget.setColumnWidth(0, 87)   # 종목명
    tableWidget.setColumnWidth(1, 60)   # 시가총액
    # ... 기존 컬럼
    tableWidget.setColumnWidth(14, 70)  # 매수일자
    tableWidget.setColumnWidth(15, 40)  # 매수시
    tableWidget.setColumnWidth(16, 40)  # 매수분
    tableWidget.setColumnWidth(17, 40)  # 매수초
    tableWidget.setColumnWidth(18, 60)  # 매수등락율
    # ... 추가 컬럼
```

#### 4.1.6 `ui/ui_update_tablewidget.py`
```python
# 위치: Line 192-199
# 변경 내용: 추가 컬럼 포맷팅

# 숫자 포맷팅 적용 컬럼 확장
number_columns = ['수익률', '수익금', '수익금합계',
                  '매수등락율', '매수시가등락율', '매수체결강도',
                  '매수전일비', '매수회전율', '매수호가잔량비', '매수스프레드']
```

---

## 5. 구현 단계

### Phase 1: 데이터 수집 확장 (우선순위: 높음)

| 단계 | 작업 내용 | 파일 | 예상 라인 수정 |
|------|----------|------|---------------|
| 1.1 | `columns_bt` 확장 정의 | `utility/setting.py` | 2줄 |
| 1.2 | 백테스팅 엔진 데이터 수집 확장 | `backtester/backengine_kiwoom_tick.py` | 30줄 |
| 1.3 | 백테스팅 엔진 데이터 수집 확장 (tick2) | `backtester/backengine_kiwoom_tick2.py` | 30줄 |
| 1.4 | 데이터 집계 로직 확장 | `backtester/back_subtotal.py` | 20줄 |
| 1.5 | DataFrame 생성 로직 확장 | `backtester/back_static.py` | 15줄 |

### Phase 2: UI 표시 확장

| 단계 | 작업 내용 | 파일 | 예상 라인 수정 |
|------|----------|------|---------------|
| 2.1 | 테이블 컬럼 너비 설정 | `ui/set_widget.py` | 20줄 |
| 2.2 | 테이블 데이터 포맷팅 | `ui/ui_update_tablewidget.py` | 10줄 |
| 2.3 | 테이블 행 수 확장 (필요시) | `ui/set_sbtap.py`, `ui/set_cbtap.py` | 2줄 |

### Phase 3: 분석 차트 추가

| 단계 | 작업 내용 | 파일 | 예상 라인 추가 |
|------|----------|------|---------------|
| 3.1 | 분석 차트 생성 함수 구현 | `backtester/back_static.py` | 150줄 |
| 3.2 | 상관관계 차트 생성 함수 | `backtester/back_static.py` | 80줄 |
| 3.3 | PltShow 함수에서 분석 차트 호출 | `backtester/back_static.py` | 10줄 |
| 3.4 | 텔레그램 전송에 분석 차트 추가 | `backtester/back_static.py` | 5줄 |

### Phase 4: 암호화폐 백테스터 확장

| 단계 | 작업 내용 | 파일 |
|------|----------|------|
| 4.1 | 업비트 틱 엔진 확장 | `backtester/backengine_upbit_tick.py` |
| 4.2 | 업비트 틱2 엔진 확장 | `backtester/backengine_upbit_tick2.py` |
| 4.3 | 바이낸스 틱 엔진 확장 | `backtester/backengine_binance_tick.py` |
| 4.4 | 바이낸스 틱2 엔진 확장 | `backtester/backengine_binance_tick2.py` |
| 4.5 | 분봉 엔진들 확장 (6개 파일) | `backengine_*_min*.py` |

---

## 6. 데이터베이스 스키마 변경

### 6.1 backtest.db 테이블 구조 변경

기존 테이블은 동적으로 생성되며 (`df.to_sql`), 새로운 컬럼이 자동으로 추가됩니다.

**기존 테이블 마이그레이션**:
- 기존 백테스트 결과와의 호환성을 위해 기존 테이블은 그대로 유지
- 새로운 백테스트 결과만 확장된 컬럼을 포함
- 이전 결과 조회 시 누락된 컬럼은 `NaN` 또는 기본값 처리

```python
# back_static.py GetResultDataframe 함수에서 처리
def GetResultDataframe(df, gubun):
    # 컬럼 존재 여부 확인 후 없으면 기본값으로 채움
    for col in columns_bt_extended:
        if col not in df.columns:
            df[col] = np.nan
    return df
```

---

## 7. 테스트 계획

### 7.1 단위 테스트

| 테스트 항목 | 검증 내용 |
|------------|----------|
| 데이터 수집 | 모든 확장 컬럼이 올바르게 수집되는지 |
| 계산 정확성 | 시가등락율, 호가잔량비, 스프레드 계산 정확성 |
| 인덱스 범위 | arry_data 인덱스가 범위를 벗어나지 않는지 |
| None/0 처리 | 분모가 0인 경우 예외 처리 |

### 7.2 통합 테스트

| 테스트 항목 | 검증 내용 |
|------------|----------|
| 백테스트 실행 | 전체 백테스트가 오류 없이 완료되는지 |
| UI 표시 | 확장된 테이블이 올바르게 표시되는지 |
| 차트 생성 | 분석 차트가 정상 생성되는지 |
| 텔레그램 전송 | 모든 차트가 텔레그램으로 전송되는지 |

### 7.3 성능 테스트

| 테스트 항목 | 기준 |
|------------|------|
| 데이터 수집 오버헤드 | 기존 대비 10% 이내 |
| 차트 생성 시간 | 추가 3초 이내 |
| 메모리 사용량 | 기존 대비 20% 이내 증가 |

---

## 8. 롤백 계획

### 8.1 단계별 롤백

| 상황 | 롤백 방법 |
|------|----------|
| Phase 1 실패 | `columns_bt`를 원래대로 복원, 백테스터 코드 롤백 |
| Phase 2 실패 | UI 관련 변경만 롤백, 데이터 수집은 유지 |
| Phase 3 실패 | 분석 차트 함수 비활성화, PltShow 호출 제거 |

### 8.2 Git 브랜치 전략

```bash
# 기능 브랜치 생성
git checkout -b feature/backtest-table-expansion

# Phase 완료마다 커밋
git commit -m "feat: Phase 1 - 데이터 수집 확장"
git commit -m "feat: Phase 2 - UI 표시 확장"
git commit -m "feat: Phase 3 - 분석 차트 추가"

# 문제 발생 시 특정 Phase로 롤백
git revert <commit-hash>
```

---

## 9. 문서 업데이트 계획

### 9.1 업데이트 필요 문서

| 문서 | 업데이트 내용 |
|------|-------------|
| `docs/Guideline/Back_Testing_Guideline_Tick.md` | 새 컬럼 설명 추가 |
| `docs/Guideline/Stock_Database_Information.md` | 백테스트 결과 테이블 스키마 추가 |
| `docs/Manual/08_Backtesting/` | 분석 차트 사용법 추가 |
| `CLAUDE.md` | columns_bt 변경 사항 반영 |

### 9.2 코드 주석

모든 수정된 코드에 아래 형식으로 주석 추가:
```python
# [2025-12-08] 백테스팅 상세기록 테이블 확장
# 추가: 매수 시점 시장 데이터 수집
```

---

## 10. 참고 자료

### 10.1 데이터베이스 컬럼 인덱스 참조

`stock_tick_back.db` 컬럼 인덱스:

| 인덱스 | 컬럼명 | 인덱스 | 컬럼명 |
|--------|--------|--------|--------|
| 0 | index (시간) | 12 | 시가총액 |
| 1 | 현재가 | 17 | 고저평균대비등락율 |
| 2 | 시가 | 18 | 매도총잔량 |
| 3 | 고가 | 19 | 매수총잔량 |
| 4 | 저가 | 24 | 매도호가1 |
| 5 | 등락율 | 25 | 매수호가1 |
| 6 | 당일거래대금 | ... | ... |
| 7 | 체결강도 | | |
| 9 | 전일비 | | |
| 10 | 회전율 | | |
| 11 | 전일동시간비 | | |

### 10.2 관련 코드 스니펫

**현재 데이터 튜플 구조** (`backengine_kiwoom_tick.py:869`):
```python
data = ('백테결과', self.name, sgtg, bt, st, ht, bp, sp, bg, pg, pp, sg, sc, abt, bcx, vturn, vkey)
```

**PltShow 텔레그램 전송** (`back_static.py:826-828`):
```python
teleQ.put(f'{backname} {save_file_name.split("_")[1]} 완료.')
teleQ.put(f"{GRAPH_PATH}/{save_file_name}_.png")
teleQ.put(f"{GRAPH_PATH}/{save_file_name}.png")
```

---

## 11. 예상 결과물

### 11.1 확장된 테이블 예시

```
| 종목명 | 시총 | 매수시간 | ... | 매수일자 | 매수시 | 매수분 | 매수등락율 | 매수체결강도 | ... |
|--------|------|----------|-----|----------|--------|--------|-----------|-------------|-----|
| 삼성전자 | 3500 | 090125 | ... | 20251208 | 9 | 1 | 5.23 | 125.5 | ... |
| SK하이닉스 | 1200 | 101532 | ... | 20251208 | 10 | 15 | 12.45 | 180.2 | ... |
```

### 11.2 분석 차트 예시

```
┌────────────────────────────────────────────────────┐
│  백테스팅 분석 차트 - Strategy_20251208            │
├────────────────────┬───────────────────────────────┤
│  시간대별 수익분포  │    등락율별 수익분포          │
│   [막대그래프]     │     [막대그래프]              │
├────────────────────┼───────────────────────────────┤
│  체결강도별 분포   │    거래대금별 분포            │
│   [막대그래프]     │     [히스토그램]              │
├────────────────────┼───────────────────────────────┤
│  시가총액별 분포   │    상관관계 히트맵            │
│   [막대그래프]     │     [히트맵]                  │
└────────────────────┴───────────────────────────────┘
```

---

## 12. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| v1.0 | 2025-12-08 | Claude | 초안 작성 |

---

**다음 단계**: Phase 1 구현 시작 (데이터 수집 확장)
