# 텔레그램 추가 차트 시스템 분석 문서

**문서 버전**: v1.0
**작성일**: 2025-12-09
**대상 브랜치**: `feature/backtesting_result_update`
**관련 파일**: `backtester/back_static.py`

---

## 1. 개요

### 1.1 목적

백테스팅 결과에서 매수/매도 시점의 상세 시장 데이터를 분석하여 다음 정보를 텔레그램으로 전송합니다:

1. **데이터 분석 차트**: 시간대별, 등락율별, 체결강도별 수익 분포 시각화
2. **필터 추천**: 손실 거래를 줄이기 위한 조건 필터 분석
3. **매수/매도 비교 차트**: 매수 시점과 매도 시점의 시장 상태 변화 분석

### 1.2 시스템 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                    백테스팅 엔진 (BackEngine)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  CalculationEyun()                                        │  │
│  │  • 매수 시점 시장 데이터 수집 (20개 컬럼)                    │  │
│  │  • 매도 시점 시장 데이터 수집 (16개 컬럼)                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    결과 처리 (back_static.py)                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  PltShow()                                                │  │
│  │  └─→ PltAnalysisCharts()    → 분석 차트 생성              │  │
│  │  └─→ RunFullAnalysis()      → 전체 분석 실행              │  │
│  │       ├─→ CalculateDerivedMetrics()  → 파생 지표 계산      │  │
│  │       ├─→ ExportBacktestCSV()        → CSV 파일 출력       │  │
│  │       ├─→ PltBuySellComparison()     → 비교 차트 생성      │  │
│  │       └─→ AnalyzeFilterEffects()     → 필터 효과 분석      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    텔레그램 전송 (teleQ)                         │
│  • 텍스트 메시지: "백테스트 완료" 알림                            │
│  • 이미지 1: {전략명}_analysis.png     (8개 서브차트)            │
│  • 이미지 2: {전략명}_comparison.png   (11개 서브차트)           │
│  • 텍스트: 필터 추천 메시지                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 데이터 수집 (BackEngine)

### 2.1 데이터 수집 위치

파일: `backtester/backengine_kiwoom_tick.py`
함수: `CalculationEyun(self, vturn, vkey)`

### 2.2 수집되는 데이터 구조

#### 매수 시점 데이터 (20개 컬럼)

```python
# 시간 분해 데이터
buy_date = bt_str[:8]                    # 매수일자 (YYYYMMDD)
buy_hour = int(bt_str[8:10])             # 매수시 (0-23)
buy_min = int(bt_str[10:12])             # 매수분 (0-59)
buy_sec = int(bt_str[12:14])             # 매수초 (0-59)

# 시장 데이터
buy_등락율 = self.arry_data[bi, 5]       # 전일 대비 등락률
buy_시가등락율 = (bp - buy_시가) / buy_시가 * 100  # 시가 대비 등락률
buy_당일거래대금 = self.arry_data[bi, 6] # 당일 누적 거래대금 (억원)
buy_체결강도 = self.arry_data[bi, 7]     # 체결강도 (매수/매도)
buy_전일비 = self.arry_data[bi, 9]       # 전일 거래량 대비 비율
buy_회전율 = self.arry_data[bi, 10]      # 상장주식 대비 거래량
buy_전일동시간비 = self.arry_data[bi, 11] # 전일 동시간 대비

# 가격 데이터
buy_고가 = self.arry_data[bi, 3]         # 당일 고가
buy_저가 = self.arry_data[bi, 4]         # 당일 저가
buy_고저평균대비등락율 = self.arry_data[bi, 17]

# 호가 데이터
buy_매도총잔량 = self.arry_data[bi, 18]  # 매도호가 1~5 잔량합
buy_매수총잔량 = self.arry_data[bi, 19]  # 매수호가 1~5 잔량합
buy_호가잔량비 = buy_매수총잔량 / buy_매도총잔량 * 100
buy_매도호가1 = self.arry_data[bi, 24]   # 최우선 매도호가
buy_매수호가1 = self.arry_data[bi, 25]   # 최우선 매수호가
buy_스프레드 = (buy_매도호가1 - buy_매수호가1) / buy_매수호가1 * 100
```

#### 매도 시점 데이터 (16개 컬럼)

```python
si = self.indexn  # 매도 시점 인덱스

sell_등락율 = self.arry_data[si, 5]
sell_시가등락율 = (sp - sell_시가) / sell_시가 * 100
sell_당일거래대금 = self.arry_data[si, 6]
sell_체결강도 = self.arry_data[si, 7]
sell_전일비 = self.arry_data[si, 9]
sell_회전율 = self.arry_data[si, 10]
sell_전일동시간비 = self.arry_data[si, 11]
sell_고가 = self.arry_data[si, 3]
sell_저가 = self.arry_data[si, 4]
sell_고저평균대비등락율 = self.arry_data[si, 17]
sell_매도총잔량 = self.arry_data[si, 18]
sell_매수총잔량 = self.arry_data[si, 19]
sell_호가잔량비 = sell_매수총잔량 / sell_매도총잔량 * 100
sell_매도호가1 = self.arry_data[si, 24]
sell_매수호가1 = self.arry_data[si, 25]
sell_스프레드 = (sell_매도호가1 - sell_매수호가1) / sell_매수호가1 * 100
```

### 2.3 데이터 전송 구조

```python
data = (
    '백테결과', self.name, sgtg, bt, st, ht, bp, sp, bg, pg, pp, sg, sc, abt, bcx, vturn, vkey,
    # 매수 시점 데이터 (20개)
    buy_date, buy_hour, buy_min, buy_sec,
    buy_등락율, buy_시가등락율, buy_당일거래대금, buy_체결강도,
    buy_전일비, buy_회전율, buy_전일동시간비,
    buy_고가, buy_저가, buy_고저평균대비등락율,
    buy_매도총잔량, buy_매수총잔량, buy_호가잔량비,
    buy_매도호가1, buy_매수호가1, buy_스프레드,
    # 매도 시점 데이터 (16개)
    sell_등락율, sell_시가등락율, sell_당일거래대금, sell_체결강도,
    sell_전일비, sell_회전율, sell_전일동시간비,
    sell_고가, sell_저가, sell_고저평균대비등락율,
    sell_매도총잔량, sell_매수총잔량, sell_호가잔량비,
    sell_매도호가1, sell_매수호가1, sell_스프레드
)
```

---

## 3. 데이터 분석 차트 (PltAnalysisCharts)

### 3.1 함수 개요

파일: `backtester/back_static.py:1042-1270`

```python
def PltAnalysisCharts(df_tsg, save_file_name, teleQ):
    """
    확장된 상세기록 데이터를 기반으로 분석 차트를 생성하고 텔레그램으로 전송

    Args:
        df_tsg: 확장된 상세기록 DataFrame (34개 컬럼)
        save_file_name: 저장 파일명
        teleQ: 텔레그램 전송 큐
    """
```

### 3.2 생성되는 8개 차트

#### Chart 1: 시간대별 수익금 분포 (gs[0, 0])

```python
# 목적: 어느 시간대에 매수한 거래가 수익성이 좋은지 분석
df_hour = df_tsg.groupby('매수시').agg({'수익금': 'sum', '수익률': 'mean'})
colors = [color_profit if x >= 0 else color_loss for x in df_hour['수익금']]
ax1.bar(df_hour['매수시'], df_hour['수익금'], color=colors)
```

**해석 방법**:
- 녹색 막대: 해당 시간대 총 수익이 양수
- 빨간색 막대: 해당 시간대 총 수익이 음수
- 막대 위 숫자: 총 수익금 (만원 단위)

#### Chart 2: 등락율별 수익금 분포 (gs[0, 1])

```python
# 목적: 매수 시점 등락율과 수익률의 관계 분석
bins = [0, 5, 10, 15, 20, 30, 100]
labels = ['0-5%', '5-10%', '10-15%', '15-20%', '20-30%', '30%+']
df_tsg['등락율구간'] = pd.cut(df_tsg['매수등락율'], bins=bins, labels=labels)
df_rate = df_tsg.groupby('등락율구간').agg({'수익금': 'sum', '종목명': 'count'})
```

**해석 방법**:
- 주황색 라인: 거래 횟수
- 막대: 해당 등락율 구간의 총 수익금
- 예: 20-30% 구간이 빨간색이면 고등락 종목 매수 시 손실 가능성 높음

#### Chart 3: 체결강도별 수익금 분포 (gs[1, 0])

```python
# 목적: 체결강도(매수세/매도세 비율)와 수익률의 관계 분석
bins_ch = [0, 80, 100, 120, 150, 200, 500]
labels_ch = ['~80', '80-100', '100-120', '120-150', '150-200', '200+']
df_tsg['체결강도구간'] = pd.cut(df_tsg['매수체결강도'], bins=bins_ch, labels=labels_ch)

# 승률 계산
win_rates = []
for grp in df_ch['체결강도구간']:
    grp_data = df_tsg[df_tsg['체결강도구간'] == grp]
    wr = (grp_data['수익금'] > 0).sum() / len(grp_data) * 100
    win_rates.append(wr)
```

**해석 방법**:
- 체결강도 100 미만: 매도세 우위
- 체결강도 100 초과: 매수세 우위
- 보라색 라인: 해당 구간의 승률(%)

#### Chart 4: 거래대금별 수익금 분포 (gs[1, 1])

```python
# 목적: 당일 거래대금 수준에 따른 수익성 분석
df_tsg['거래대금구간'] = pd.cut(df_tsg['매수당일거래대금'],
    bins=[0, 100, 500, 1000, 5000, 10000, float('inf')],
    labels=['~100억', '100-500억', '500-1000억', '1000-5000억', '5000억-1조', '1조+'])
```

**해석 방법**:
- 거래대금이 높을수록 유동성이 좋음
- 너무 낮은 거래대금: 슬리피지 위험

#### Chart 5: 시가총액별 수익금 분포 (gs[2, 0])

```python
# 목적: 종목 규모별 수익성 분석
df_tsg['시총구간'] = pd.cut(df_tsg['시가총액'],
    bins=[0, 1000, 3000, 10000, 50000, float('inf')],
    labels=['~1000억', '1000-3000억', '3000억-1조', '1-5조', '5조+'])
```

**해석 방법**:
- 소형주 vs 대형주 전략 적합성 확인
- 손실이 큰 구간은 필터링 고려

#### Chart 6: 보유시간별 수익금 분포 (gs[2, 1])

```python
# 목적: 보유 기간과 수익률의 관계 분석
df_tsg['보유시간구간'] = pd.cut(df_tsg['보유시간'],
    bins=[0, 60, 180, 300, 600, 1800, float('inf')],
    labels=['~1분', '1-3분', '3-5분', '5-10분', '10-30분', '30분+'])
```

**해석 방법**:
- 단타 전략: 1분 미만 구간 중요
- 스윙 전략: 10분 이상 구간 중요

#### Chart 7: 상관관계 히트맵 (gs[3, 0])

```python
# 목적: 변수 간 상관관계 파악
corr_columns = ['수익률', '매수등락율', '매수체결강도', '매수회전율', '매수전일비', '보유시간']
df_corr = df_tsg[corr_columns].corr()
im = ax7.imshow(df_corr.values, cmap='RdYlGn', aspect='auto', vmin=-1, vmax=1)
```

**해석 방법**:
- 녹색: 양의 상관관계 (함께 증가)
- 빨간색: 음의 상관관계 (반대로 움직임)
- 수치: 상관계수 (-1 ~ 1)

#### Chart 8: 등락율 vs 수익률 산점도 (gs[3, 1])

```python
# 목적: 매수 등락율과 수익률의 직접적 관계 시각화
ax8.scatter(df_tsg['매수등락율'], df_tsg['수익률'], c=colors, alpha=0.5)

# 추세선 추가
z = np.polyfit(df_tsg['매수등락율'], df_tsg['수익률'], 1)
p = np.poly1d(z)
ax8.plot(x_line, p(x_line), 'b--', linewidth=1, label='추세선')
```

**해석 방법**:
- 녹색 점: 이익 거래
- 빨간색 점: 손실 거래
- 파란 점선: 추세선 (기울기가 음수면 고등락 종목 불리)

### 3.3 출력 예시

```
파일: backtester/graph/{전략명}_analysis.png
크기: 16x20 인치 (1920x2400 픽셀)
```

---

## 4. 파생 지표 계산 (CalculateDerivedMetrics)

### 4.1 함수 개요

파일: `backtester/back_static.py:1275-1328`

```python
def CalculateDerivedMetrics(df_tsg):
    """
    매수/매도 시점 간 파생 지표를 계산합니다.

    Returns:
        DataFrame with added derived metrics
    """
```

### 4.2 생성되는 파생 지표

#### 변화량 지표 (매도 - 매수)

```python
df['등락율변화'] = df['매도등락율'] - df['매수등락율']
df['체결강도변화'] = df['매도체결강도'] - df['매수체결강도']
df['전일비변화'] = df['매도전일비'] - df['매수전일비']
df['회전율변화'] = df['매도회전율'] - df['매수회전율']
df['호가잔량비변화'] = df['매도호가잔량비'] - df['매수호가잔량비']
```

**해석**:
- 양수: 보유 기간 동안 해당 지표가 증가
- 음수: 보유 기간 동안 해당 지표가 감소

#### 변화율 지표 (매도 / 매수)

```python
df['거래대금변화율'] = df['매도당일거래대금'] / df['매수당일거래대금']
df['체결강도변화율'] = df['매도체결강도'] / df['매수체결강도']
```

**해석**:
- 1.0: 변화 없음
- 1.2: 20% 증가
- 0.5: 50% 감소

#### 추세 판단 지표

```python
df['등락추세'] = df['등락율변화'].apply(
    lambda x: '상승' if x > 0 else ('하락' if x < 0 else '유지'))

df['체결강도추세'] = df['체결강도변화'].apply(
    lambda x: '강화' if x > 10 else ('약화' if x < -10 else '유지'))

df['거래량추세'] = df['거래대금변화율'].apply(
    lambda x: '증가' if x > 1.2 else ('감소' if x < 0.8 else '유지'))
```

#### 위험 신호 지표

```python
# 급락 신호: 등락율 3% 이상 하락 AND 체결강도 20 이상 하락
df['급락신호'] = (df['등락율변화'] < -3) & (df['체결강도변화'] < -20)

# 매도세 증가: 호가잔량비 0.2 이상 감소
df['매도세증가'] = df['호가잔량비변화'] < -0.2

# 거래량 급감: 거래대금 50% 이하로 감소
df['거래량급감'] = df['거래대금변화율'] < 0.5
```

#### 위험도 점수 (0-100점)

```python
df['위험도점수'] = 0
df.loc[df['등락율변화'] < -2, '위험도점수'] += 20        # 등락율 2% 이상 하락
df.loc[df['체결강도변화'] < -15, '위험도점수'] += 20     # 체결강도 15 이상 하락
df.loc[df['호가잔량비변화'] < -0.3, '위험도점수'] += 20  # 호가잔량비 0.3 이상 감소
df.loc[df['거래대금변화율'] < 0.6, '위험도점수'] += 20   # 거래대금 40% 이상 감소
df.loc[df['매수등락율'] > 20, '위험도점수'] += 20        # 매수 시 등락율 20% 초과
```

**위험도 해석**:
- 0-20점: 낮은 위험
- 40-60점: 중간 위험
- 80-100점: 높은 위험 (손실 가능성 높음)

---

## 5. 필터 효과 분석 (AnalyzeFilterEffects)

### 5.1 함수 개요

파일: `backtester/back_static.py:1447-1560`

```python
def AnalyzeFilterEffects(df_tsg):
    """
    조건별 필터 적용 시 예상 효과를 분석합니다.

    Args:
        df_tsg: 파생 지표가 포함된 DataFrame

    Returns:
        list: 필터 효과 분석 결과
    """
```

### 5.2 분석되는 필터 조건

#### 시간대 필터

```python
for hour in df_tsg['매수시'].unique():
    filter_conditions.append({
        '필터명': f'시간대 {hour}시 제외',
        '조건': df_tsg['매수시'] == hour,
        '분류': '시간대'
    })
```

#### 등락율 필터

```python
filter_conditions.extend([
    {'필터명': '등락율 25% 이상 제외', '조건': df_tsg['매수등락율'] >= 25},
    {'필터명': '등락율 20% 이상 제외', '조건': df_tsg['매수등락율'] >= 20},
    {'필터명': '등락율 5% 미만 제외', '조건': df_tsg['매수등락율'] < 5},
])
```

#### 체결강도 필터

```python
filter_conditions.extend([
    {'필터명': '체결강도 80 미만 제외', '조건': df_tsg['매수체결강도'] < 80},
    {'필터명': '체결강도 200 이상 제외', '조건': df_tsg['매수체결강도'] >= 200},
])
```

#### 추세 변화 필터 (매도 데이터 있는 경우)

```python
filter_conditions.extend([
    {'필터명': '등락율하락 3% 이상 제외', '조건': df_tsg['등락율변화'] <= -3},
    {'필터명': '체결강도하락 20 이상 제외', '조건': df_tsg['체결강도변화'] <= -20},
    {'필터명': '거래대금 50% 이상 감소 제외', '조건': df_tsg['거래대금변화율'] < 0.5},
])
```

#### 위험 신호 필터

```python
filter_conditions.extend([
    {'필터명': '급락신호 발생 제외', '조건': df_tsg['급락신호'] == True},
    {'필터명': '위험도 60점 이상 제외', '조건': df_tsg['위험도점수'] >= 60},
    {'필터명': '위험도 40점 이상 제외', '조건': df_tsg['위험도점수'] >= 40},
])
```

#### 보유시간 필터

```python
filter_conditions.extend([
    {'필터명': '보유시간 30초 미만 제외', '조건': df_tsg['보유시간'] < 30},
    {'필터명': '보유시간 60초 미만 제외', '조건': df_tsg['보유시간'] < 60},
    {'필터명': '보유시간 30분 이상 제외', '조건': df_tsg['보유시간'] >= 1800},
])
```

#### 시가총액 필터

```python
filter_conditions.extend([
    {'필터명': '시가총액 1000억 미만 제외', '조건': df_tsg['시가총액'] < 1000},
    {'필터명': '시가총액 3000억 미만 제외', '조건': df_tsg['시가총액'] < 3000},
    {'필터명': '시가총액 1조 이상 제외', '조건': df_tsg['시가총액'] >= 10000},
])
```

### 5.3 필터 효과 계산 로직

```python
for fc in filter_conditions:
    # 필터 대상 거래 분리
    filtered_out = df_tsg[fc['조건']]      # 제외될 거래
    remaining = df_tsg[~fc['조건']]         # 남을 거래

    filtered_profit = filtered_out['수익금'].sum()   # 제외 거래 수익금
    remaining_profit = remaining['수익금'].sum()      # 잔여 거래 수익금

    # 수익 개선 효과 = 제외된 거래의 손실 (부호 반전)
    # 손실 거래가 제외되면 양수, 이익 거래가 제외되면 음수
    improvement = -filtered_profit

    filter_results.append({
        '분류': fc['분류'],
        '필터명': fc['필터명'],
        '제외거래수': len(filtered_out),
        '제외비율': len(filtered_out) / total_trades * 100,
        '제외거래수익금': filtered_profit,
        '잔여거래수': len(remaining),
        '잔여거래수익금': remaining_profit,
        '수익개선금액': improvement,
        '제외거래승률': (filtered_out['수익금'] > 0).mean() * 100,
        '잔여거래승률': (remaining['수익금'] > 0).mean() * 100,
        '적용권장': '★★★' if improvement > total_profit * 0.1 else
                   ('★★' if improvement > 0 else ''),
    })
```

### 5.4 적용 권장 기준

| 등급 | 조건 | 의미 |
|------|------|------|
| ★★★ | 수익개선금액 > 총수익금 × 10% | 강력 추천 |
| ★★ | 수익개선금액 > 0 | 권장 |
| (없음) | 수익개선금액 ≤ 0 | 비추천 (이익 거래도 제외됨) |

### 5.5 출력 예시 (CSV)

```csv
분류,필터명,제외거래수,제외비율,제외거래수익금,잔여거래수익금,수익개선금액,적용권장
시간대,시간대 14시 제외,45,8.2,-1250000,5250000,1250000,★★★
등락율,등락율 25% 이상 제외,23,4.2,-850000,4850000,850000,★★
체결강도,체결강도 80 미만 제외,12,2.2,-320000,4320000,320000,★★
```

---

## 6. 매수/매도 비교 차트 (PltBuySellComparison)

### 6.1 함수 개요

파일: `backtester/back_static.py:1563-1811`

```python
def PltBuySellComparison(df_tsg, save_file_name, teleQ=None):
    """
    매수/매도 시점 비교 분석 차트를 생성합니다.

    Args:
        df_tsg: 백테스팅 결과 DataFrame (파생 지표 포함)
        save_file_name: 저장 파일명
        teleQ: 텔레그램 전송 큐
    """
```

### 6.2 생성되는 11개 차트

#### Chart 1: 등락율 변화 vs 수익률 (gs[0, 0])

```python
# 목적: 보유 중 등락율 변화가 수익률에 미치는 영향
ax1.scatter(df_tsg['등락율변화'], df_tsg['수익률'], c=colors)
ax1.axhline(y=0, color='gray', linestyle='--')  # 손익 기준선
ax1.axvline(x=0, color='gray', linestyle='--')  # 등락율 변화 기준선
```

**사분면 해석**:
- 우상단: 주가 상승 + 이익 실현 ✓
- 좌상단: 주가 하락 + 이익 실현 (타이밍 좋음)
- 우하단: 주가 상승 + 손실 (너무 일찍 매도)
- 좌하단: 주가 하락 + 손실 (추세 반전 실패) ✗

#### Chart 2: 체결강도 변화 vs 수익률 (gs[0, 1])

```python
# 목적: 매수세 변화가 수익에 미치는 영향
ax2.scatter(df_tsg['체결강도변화'], df_tsg['수익률'], c=colors)
```

**해석**:
- 체결강도 증가(+) + 이익: 매수세 증가로 수익
- 체결강도 감소(-) + 손실: 매수세 약화로 손실

#### Chart 3: 매수 vs 매도 등락율 (gs[0, 2])

```python
# 목적: 매수 시점과 매도 시점의 등락율 관계
ax3.scatter(df_tsg['매수등락율'], df_tsg['매도등락율'], c=colors)
ax3.plot([min_val, max_val], [min_val, max_val], 'k--', label='변화없음')  # 대각선
```

**해석**:
- 대각선 위: 보유 중 등락율 상승
- 대각선 아래: 보유 중 등락율 하락
- 대각선 근처: 변화 없음

#### Chart 4: 위험도 점수별 수익금 분포 (gs[1, 0])

```python
risk_bins = [0, 20, 40, 60, 80, 100]
risk_labels = ['0-20', '20-40', '40-60', '60-80', '80-100']
df_tsg['위험도구간'] = pd.cut(df_tsg['위험도점수'], bins=risk_bins, labels=risk_labels)
risk_profit = df_tsg.groupby('위험도구간')['수익금'].sum()
```

**활용법**:
- 위험도 높은 구간(60-100)이 손실이면 해당 조건 필터링 고려

#### Chart 5: 등락추세별 수익금 (gs[1, 1])

```python
# 추세: 상승, 하락, 유지
trend_profit = df_tsg.groupby('등락추세')['수익금'].sum()
```

#### Chart 6: 체결강도추세별 수익금 (gs[1, 2])

```python
# 추세: 강화, 약화, 유지
ch_trend_profit = df_tsg.groupby('체결강도추세')['수익금'].sum()
```

#### Chart 7: 필터 효과 파레토 차트 (gs[2, :2])

```python
# 수익 개선 효과가 있는 필터 Top 15
filter_results = AnalyzeFilterEffects(df_tsg)
df_filter = pd.DataFrame(filter_results)
df_filter = df_filter[df_filter['수익개선금액'] > 0].nlargest(15, '수익개선금액')

# 파레토 차트: 막대 + 누적 비율 라인
ax7.bar(x_pos, df_filter['수익개선금액'], color=color_profit)
ax7_twin.plot(x_pos, cumsum_pct, 'ro-', markersize=4)  # 누적 비율
```

**파레토 원칙 적용**:
- 상위 20% 필터가 80%의 수익 개선 효과
- 빨간 라인이 80%에 도달하는 지점까지의 필터 적용 권장

#### Chart 8: 손실/이익 거래 특성 비교 (gs[2, 2])

```python
loss_trades = df_tsg[df_tsg['수익금'] < 0]
profit_trades = df_tsg[df_tsg['수익금'] >= 0]

compare_cols = ['매수등락율', '매수체결강도', '보유시간']
loss_means = [loss_trades[c].mean() for c in compare_cols]
profit_means = [profit_trades[c].mean() for c in compare_cols]

ax8.bar(x - width/2, loss_means, width, label='손실거래', color=color_loss)
ax8.bar(x + width/2, profit_means, width, label='이익거래', color=color_profit)
```

**활용법**:
- 손실 거래 평균 등락율이 높으면 → 고등락 제한 필터 추가
- 손실 거래 평균 체결강도가 낮으면 → 체결강도 하한 필터 추가

#### Chart 9: 추세 조합별 수익금 히트맵 (gs[3, 0])

```python
# 등락추세 × 체결강도추세 조합
pivot = df_tsg.pivot_table(values='수익금', index='등락추세',
                           columns='체결강도추세', aggfunc='sum', fill_value=0)
im = ax9.imshow(pivot.values, cmap='RdYlGn')
```

**해석**:
- 녹색: 수익 조합
- 빨간색: 손실 조합
- 최적 조합 식별 가능 (예: 상승+강화)

#### Chart 10: 시간대별 추세 변화 (gs[3, 1])

```python
hourly_change = df_tsg.groupby('매수시').agg({
    '등락율변화': 'mean',
    '체결강도변화': 'mean',
    '수익금': 'sum'
})
```

#### Chart 11: 거래대금 변화율별 수익금 (gs[3, 2])

```python
bins_vol = [0, 0.5, 0.8, 1.0, 1.2, 1.5, 100]
labels_vol = ['~50%', '50-80%', '80-100%', '100-120%', '120-150%', '150%+']
df_tsg['거래대금변화구간'] = pd.cut(df_tsg['거래대금변화율'], bins=bins_vol, labels=labels_vol)
```

### 6.3 출력 예시

```
파일: backtester/graph/{전략명}_comparison.png
크기: 20x16 인치 (2400x1920 픽셀)
```

---

## 7. 전체 분석 실행 (RunFullAnalysis)

### 7.1 함수 개요

파일: `backtester/back_static.py:1814-1861`

```python
def RunFullAnalysis(df_tsg, save_file_name, teleQ=None):
    """
    전체 분석을 실행합니다 (CSV 출력 + 시각화).

    Returns:
        dict: 분석 결과 요약
            - csv_files: (detail_path, summary_path, filter_path)
            - charts: [comparison_chart_path]
            - recommendations: [필터 추천 메시지 리스트]
    """
```

### 7.2 실행 흐름

```python
def RunFullAnalysis(df_tsg, save_file_name, teleQ=None):
    result = {
        'csv_files': None,
        'charts': [],
        'recommendations': []
    }

    try:
        # 1. 파생 지표 계산
        df_analysis = CalculateDerivedMetrics(df_tsg)

        # 2. CSV 파일 출력 (3개 파일)
        csv_paths = ExportBacktestCSV(df_analysis, save_file_name, teleQ)
        result['csv_files'] = csv_paths

        # 3. 매수/매도 비교 차트 생성
        PltBuySellComparison(df_analysis, save_file_name, teleQ)
        result['charts'].append(f"{GRAPH_PATH}/{save_file_name}_comparison.png")

        # 4. 필터 추천 생성 (★★ 이상만)
        filter_results = AnalyzeFilterEffects(df_analysis)
        top_filters = [f for f in filter_results if f.get('적용권장', '').count('★') >= 2]

        for f in top_filters[:5]:
            result['recommendations'].append(
                f"[{f['분류']}] {f['필터명']}: 수익개선 {f['수익개선금액']:,}원 예상"
            )

        # 5. 텔레그램 요약 전송
        if teleQ is not None and result['recommendations']:
            msg = "📊 필터 추천:\n" + "\n".join(result['recommendations'])
            teleQ.put(msg)

    except Exception as e:
        print_exc()

    return result
```

### 7.3 출력 파일 목록

| 파일명 | 내용 |
|--------|------|
| `{전략명}_detail.csv` | 전체 거래 상세 기록 (50개 컬럼) |
| `{전략명}_summary.csv` | 조건별 요약 통계 |
| `{전략명}_filter.csv` | 필터 효과 분석 결과 |
| `{전략명}_analysis.png` | 데이터 분석 차트 (8개) |
| `{전략명}_comparison.png` | 매수/매도 비교 차트 (11개) |

---

## 8. 호출 흐름 다이어그램

```
백테스팅 완료
     │
     ▼
PltShow() [back_static.py:615]
     │
     ├──→ 기존 차트 생성 (수익곡선, 부가정보)
     │    • {전략명}.png
     │    • {전략명}_.png
     │
     ├──→ teleQ.put() → 텔레그램 전송 (완료 메시지 + 기존 차트)
     │
     ├──→ PltAnalysisCharts() [1042]
     │    │
     │    ├── 데이터 그룹화 (시간대별, 등락율별, 체결강도별...)
     │    ├── 8개 서브차트 생성
     │    ├── 저장: {전략명}_analysis.png
     │    └── teleQ.put() → 텔레그램 전송
     │
     └──→ RunFullAnalysis() [1814]
          │
          ├── CalculateDerivedMetrics() [1275]
          │    └── 파생 지표 계산 (변화량, 변화율, 추세, 위험도)
          │
          ├── ExportBacktestCSV() [1331]
          │    ├── 상세 기록 CSV 저장
          │    ├── 요약 통계 CSV 저장
          │    └── 필터 분석 CSV 저장
          │
          ├── PltBuySellComparison() [1563]
          │    ├── 11개 서브차트 생성
          │    ├── 저장: {전략명}_comparison.png
          │    └── teleQ.put() → 텔레그램 전송
          │
          ├── AnalyzeFilterEffects() [1447]
          │    └── 필터별 수익 개선 효과 계산
          │
          └── 필터 추천 메시지 생성
               └── teleQ.put() → 텔레그램 전송
```

---

## 9. 텔레그램 전송 내용 요약

### 9.1 전송 순서

1. **텍스트**: `"{전략명} {날짜} 완료."`
2. **이미지**: `{전략명}_.png` (부가정보 차트)
3. **이미지**: `{전략명}.png` (수익곡선 차트)
4. **이미지**: `{전략명}_analysis.png` (데이터 분석 차트)
5. **이미지**: `{전략명}_comparison.png` (매수/매도 비교 차트)
6. **텍스트**: 필터 추천 메시지

### 9.2 필터 추천 메시지 예시

```
📊 필터 추천:
[시간대] 시간대 14시 제외: 수익개선 1,250,000원 예상
[등락율] 등락율 25% 이상 제외: 수익개선 850,000원 예상
[체결강도] 체결강도 80 미만 제외: 수익개선 320,000원 예상
[위험신호] 위험도 60점 이상 제외: 수익개선 280,000원 예상
[보유시간] 보유시간 30초 미만 제외: 수익개선 150,000원 예상
```

---

## 10. 활용 가이드

### 10.1 분석 결과 해석 순서

1. **데이터 분석 차트** (`_analysis.png`) 확인
   - 손실이 큰 구간 식별 (시간대, 등락율, 체결강도 등)
   - 상관관계 확인 (어떤 변수가 수익률에 영향?)

2. **매수/매도 비교 차트** (`_comparison.png`) 확인
   - 등락율 변화 vs 수익률 산점도로 패턴 파악
   - 필터 효과 파레토 차트로 우선순위 결정

3. **필터 추천 메시지** 검토
   - ★★★ 등급 필터 우선 적용 검토
   - CSV 파일로 상세 분석

### 10.2 전략 개선 프로세스

```
1. 백테스팅 실행
     │
     ▼
2. 텔레그램 차트 분석
     │
     ├── 손실 패턴 식별
     │    • 특정 시간대 손실?
     │    • 고등락 종목 손실?
     │    • 체결강도 낮을 때 손실?
     │
     ▼
3. 필터 추천 확인
     │
     ├── ★★★ 필터 적용 검토
     │    • 제외 비율 확인 (너무 많으면 거래 기회 감소)
     │    • 수익 개선 금액 확인
     │
     ▼
4. 조건식 수정
     │
     ├── 매수 조건에 필터 추가
     │    예: 매수등락율 < 25 and 매수체결강도 >= 80
     │
     ▼
5. 재백테스팅
     │
     ▼
6. 개선 효과 확인
```

### 10.3 조건식 적용 예시

필터 추천에서 "등락율 25% 이상 제외"가 ★★★ 등급이면:

```python
# 기존 매수 조건
if 매수조건1 and 매수조건2:
    매수 = True

# 개선된 매수 조건
if 매수조건1 and 매수조건2 and 등락율 < 25:
    매수 = True
```

---

## 11. 관련 파일 요약

| 파일 | 함수 | 역할 |
|------|------|------|
| `backengine_kiwoom_tick.py` | `CalculationEyun()` | 매수/매도 시장 데이터 수집 |
| `back_static.py` | `PltShow()` | 메인 차트 생성 및 분석 호출 |
| `back_static.py` | `PltAnalysisCharts()` | 데이터 분석 차트 (8개) |
| `back_static.py` | `CalculateDerivedMetrics()` | 파생 지표 계산 |
| `back_static.py` | `AnalyzeFilterEffects()` | 필터 효과 분석 |
| `back_static.py` | `PltBuySellComparison()` | 매수/매도 비교 차트 (11개) |
| `back_static.py` | `RunFullAnalysis()` | 전체 분석 실행 |
| `back_static.py` | `ExportBacktestCSV()` | CSV 파일 출력 |
| `utility/telegram_msg.py` | - | 텔레그램 이미지/텍스트 전송 |

---

## 부록 A: 데이터 컬럼 인덱스 참조표

`arry_data` 배열의 컬럼 인덱스:

| 인덱스 | 컬럼명 | 설명 |
|--------|--------|------|
| 0 | index | 타임스탬프 (YYYYMMDDHHMMSS) |
| 1 | 현재가 | 현재 체결가 |
| 2 | 시가 | 당일 시가 |
| 3 | 고가 | 당일 고가 |
| 4 | 저가 | 당일 저가 |
| 5 | 등락율 | 전일 대비 등락률 (%) |
| 6 | 당일거래대금 | 당일 누적 거래대금 |
| 7 | 체결강도 | 매수/매도 체결 비율 |
| 9 | 전일비 | 전일 거래량 대비 비율 |
| 10 | 회전율 | 상장주식 대비 거래량 비율 |
| 11 | 전일동시간비 | 전일 동시간 대비 거래량 |
| 12 | 시가총액 | 종목 시가총액 (억원) |
| 17 | 고저평균대비등락율 | 고저평균가 대비 등락률 |
| 18 | 매도총잔량 | 매도호가 1~5 잔량합 |
| 19 | 매수총잔량 | 매수호가 1~5 잔량합 |
| 24 | 매도호가1 | 최우선 매도호가 |
| 25 | 매수호가1 | 최우선 매수호가 |

---

*문서 끝*
