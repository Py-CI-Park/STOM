# AI 기반 조건식 자동화 및 순환 연구 시스템

**문서 버전**: 1.0
**작성일**: 2025-12-01
**연구 범위**: STOM V1 조건식 자동화 및 AI 기반 순환 개선 시스템
**대상 시스템**: STOM (System Trading Optimization Manager) V1

---

## 📋 목차

1. [연구 개요](#1-연구-개요)
2. [조건식 시스템 현황 분석](#2-조건식-시스템-현황-분석)
3. [코드 실행 메커니즘 심층 분석](#3-코드-실행-메커니즘-심층-분석)
4. [AI 기반 조건식 자동 생성 시스템](#4-ai-기반-조건식-자동-생성-시스템)
5. [자동화 순환 프로세스 설계](#5-자동화-순환-프로세스-설계)
6. [실제 구현 방안](#6-실제-구현-방안)
7. [리스크 및 완화 전략](#7-리스크-및-완화-전략)
8. [결론 및 로드맵](#8-결론-및-로드맵)

---

## 1. 연구 개요

### 1.1 연구 배경 및 동기

STOM 시스템은 현재 **133개의 트레이딩 조건식**을 보유하고 있으며, 이들은 모두 수작업으로 작성, 테스트, 최적화되고 있습니다. 이 과정은:

- **시간 소모**: 한 조건식의 작성-테스트-최적화에 수일~수주 소요
- **전문성 의존**: 826개 틱 변수, 752개 분봉 변수에 대한 깊은 이해 필요
- **탐색 한계**: 인간의 직관과 경험으로는 방대한 변수 조합 공간 탐색 불가능
- **재현성 부족**: 조건식 개선 과정이 체계적으로 기록되지 않음

### 1.2 연구 목표

본 연구는 다음을 목표로 합니다:

1. **조건식 자동 생성**: AI/LLM을 활용한 조건식 코드 자동 생성
2. **자동 백테스팅**: 생성된 조건식의 즉시 검증 및 최적화
3. **결과 기록 시스템**: 모든 실험 결과의 체계적 저장 및 분석
4. **순환 개선 메커니즘**: 성과 기반 피드백을 통한 조건식 지속적 진화
5. **지식 축적**: 성공/실패 패턴의 자동 학습 및 재사용

### 1.3 기대 효과

| 항목 | 현재 (수작업) | 목표 (자동화) | 개선 효과 |
|------|--------------|--------------|-----------|
| 조건식 작성 시간 | 2-5일/개 | 10-30분/개 | 96% 단축 |
| 탐색 가능 조합 | 수십 개 | 수천 개 | 100배 증가 |
| 최적화 시간 | 587년 (이론값) | 수 시간 | 99.9% 단축 |
| 전략 다양성 | 133개 | 1,000개+ | 7.5배 증가 |
| 성과 향상 | 기준선 | +20-30% | 수익률 향상 |

---

## 2. 조건식 시스템 현황 분석

### 2.1 조건식 문서 구조

#### 2.1.1 전체 구조 (133개 조건식)

```
docs/Condition/
├── Tick/                          # 틱 데이터 기반 조건식 (72개)
│   ├── 1_To_be_reviewed/          # 검토 대기 (63개)
│   ├── 2_Under_review/            # 검토 중 (9개)
│   └── 3_Review_finished/         # 검토 완료 (0개)
│
└── Min/                           # 분봉 데이터 기반 조건식 (61개)
    ├── 1_To_be_reviewed/          # 검토 대기
    ├── 2_Under_review/            # 검토 중
    └── 3_Review_finished/         # 검토 완료
```

**주요 통계**:
- 총 조건식: 133개
- 틱 조건식: 72개 (초단위 고빈도 트레이딩)
- 분봉 조건식: 61개 (분봉 기반 스윙 트레이딩)
- 가이드라인 준수율: 98.3%
- 3단계 검토 프로세스 운영 중

#### 2.1.2 조건식 문서 템플릿 구조

각 조건식 문서는 다음 섹션으로 구성:

```markdown
# 조건식 제목

- [[Back_Testing_Guideline_Tick]] 참조
- [[Condition_Document_Template_Guideline]] 기반

## 개요
- 대상 시간 구간
- 대상 종목
- 전략 타입
- 핵심 변수

## 제한조건
# 백테스팅 호환성 규칙

## 가이드라인
# 조건식 작성 가이드

## 매수 조건식
```python
매수 = True
# 조건들...
if 매수:
    self.Buy(vturn, vkey)
```

## 매도 조건식
```python
매도 = False
# 조건들...
if 매도:
    self.Sell(vturn, vkey, sell_cond)
```

## 최적화 섹션
### BO (Buy Optimization)
### BOR (Buy Optimization Range)
### SO (Sell Optimization)
### SOR (Sell Optimization Range)
### OR (Overall Range - 상위 10개 변수)
### GAR (Genetic Algorithm Range)

## 조건식 개선 방향 연구
# 최소 3개 이상의 개선 아이디어
```

### 2.2 변수 시스템 분석

#### 2.2.1 틱 변수 (826개)

**Back_Testing_Guideline_Tick.md**에 정의된 변수 카테고리:

1. **가격 변수** (~100개)
   - 현재가, 시가, 고가, 저가
   - 등락율, 시가등락율, 시가대비등락율
   - 고저평균대비등락율
   - 이동평균(60/300/600/1200)
   - 최고현재가(N), 최저현재가(N)

2. **거래량/유동성 변수** (~150개)
   - 당일거래대금, 초당거래대금
   - 초당거래대금평균(N)
   - 거래대금증감, 전일비, 전일동시간비
   - 회전율, 시가총액

3. **체결강도 변수** (~120개)
   - 체결강도, 체결강도평균(N)
   - 최고체결강도(N), 최저체결강도(N)
   - 초당매수수량, 초당매도수량
   - 최고/최저 초당매수/매도수량(N)
   - 누적 초당매수/매도수량(N)

4. **호가정보 변수** (~80개)
   - 매도호가1~5, 매수호가1~5
   - 매도잔량1~5, 매수잔량1~5
   - 매도총잔량, 매수총잔량
   - VI가격, VI아래5호가

5. **시간 변수** (~30개)
   - 시분초, 호가시간
   - 직전거래시간, 손절매도시간

6. **각도 변수** (~80개)
   - 등락율각도(N)
   - 당일거래대금각도(N)
   - 전일비각도(N)

7. **함수 변수** (~180개)
   - 이동평균(N, lookback)
   - 최고/최저 현재가(N, lookback)
   - 체결강도평균(N, lookback)
   - Parameter_Previous(index, lookback)

8. **계산 변수** (~86개)
   - 보유시간, 수익률
   - 최고수익률, 최저수익률
   - 매수틱번호, 당일체결강도순위

#### 2.2.2 분봉 변수 (752개)

**Back_Testing_Guideline_Min.md**에 정의된 변수는 틱 변수와 유사하나, 다음 차이점이 있음:

- 분봉 특화 변수: 분봉시가, 분봉고가, 분봉저가, 분봉종가
- 분당 거래 변수: 분당거래대금, 분당매수수량, 분당매도수량
- 이동평균 window: 5/10/20/60/120 (틱: 60/300/600/1200)

### 2.3 조건식 작성 규칙

#### 2.3.1 핵심 제약사항 (10가지)

1. **변수 사용 제한**: 가이드라인에 명시된 변수만 사용 가능
2. **매수 조건식 패턴**: `not (조건)` 형태 (False 조건)
3. **매도 조건식 패턴**: `조건` 형태 (True 조건)
4. **한 줄 한 조건**: 조건식은 반드시 한 줄에 하나씩
5. **비교 연산자 제한**: `< > <= >= == !=` + `and or not` 만 사용
6. **복잡한 비교 분리**: `a < b < c` → `a < b and b < c`
7. **0 나누기 방지**: 분모에 `+ 0.0001` 추가
8. **변수명 정확성**: 오타 시 시스템 인식 불가
9. **성능 고려**: 과도하게 복잡한 산술식 지양
10. **if/elif 체인**: 첫 조건만 `if`, 나머지는 `elif`

#### 2.3.2 매수/매도 초기값 패턴

```python
# 매수 조건식 (False 조건)
매수 = True  # 초기값 True
# not (조건1)
# not (조건2)
if 매수:
    self.Buy(vturn, vkey)

# 매도 조건식 (True 조건)
매도 = False  # 초기값 False
# 조건1
# 조건2
if 매도:
    self.Sell(vturn, vkey, sell_cond)
```

### 2.4 최적화 시스템 구조

#### 2.4.1 self.vars 인덱스 규칙

```python
# self.vars 구조: [[시작, 끝, 간격], 초기값]
self.vars[0]  # 고정값 전용 (최적화 대상 아님)
self.vars[1]  # 매수 최적화 변수 1
self.vars[2]  # 매수 최적화 변수 2
self.vars[3]  # 매수 최적화 변수 3
self.vars[4]  # 매도 최적화 변수 1
self.vars[5]  # 매도 최적화 변수 2
# 반드시 연속된 번호로 사용 (건너뛰기 금지)
```

**규칙**:
- 각 변수당 최대 20개 값 이하: `(끝값 - 시작값) / 간격 + 1 ≤ 20`
- Range Step 정합성: `(끝값 - 시작값) % 간격 == 0`
- 간격 부호: 시작값 < 끝값이면 양수, 시작값 > 끝값이면 음수

#### 2.4.2 최적화 섹션 구조

1. **BO (Buy Optimization)**: 최적화된 매수 조건식 (실제 값)
2. **BOR (Buy Optimization Range)**: 매수 변수 범위 `[최소, 최대, 간격]`
3. **SO (Sell Optimization)**: 최적화된 매도 조건식 (실제 값)
4. **SOR (Sell Optimization Range)**: 매도 변수 범위
5. **OR (Overall Range)**: 상위 10개 주요 변수만 (그리드 서치용)
6. **GAR (Genetic Algorithm Range)**: `[최소, 최대]` 형식 (GA용)

#### 2.4.3 최적화 알고리즘 3종

**1. Grid Search (그리드 최적화)**
- 모든 변수 조합 순차 탐색
- 범위 자동 관리: `hstd/4` 이하 삭제
- 최적값이 경계면 확장
- 경우의 수: 변수별 값 개수의 곱

**2. Optuna (베이지안 최적화)**
- TPESampler (기본), CmaEsSampler, QMCSampler
- Early Stopping: `best + len_vars` 횟수
- 중복 탐색 방지 (`dict_simple_vars`)
- 효율적 탐색 (587년 → 수시간)

**3. Genetic Algorithm (유전 알고리즘)**
- 변수 개수 × 10회 무작위 샘플링
- 상위 5% 범위 수렴
- 교배, 변이 연산

### 2.5 성과 평가 지표 (OPTISTD 14가지)

#### 2.5.1 단순 기준값 (4개)

| 지표 | 계산식 | 의미 | 사용 예 |
|------|--------|------|---------|
| **TG** | tsg | 수익금합계 | 절대 수익금 중심 |
| **TP** | tpp | 수익률합계 | 자본 규모 무관 |
| **TPI** | wr / 100 × (1 + appp / ampp) | 매매성능지수 | 위험 대비 성과 |
| **CAGR** | tpp / day_count × 250(or 365) | 연간예상수익률 | 장기 성장성 |

#### 2.5.2 복합 기준값 (10개)

| 지표 | 계산식 | 의미 |
|------|--------|------|
| **GM** | tsg / mdd_ | 금액/MDD 비율 |
| **G2M** | tsg² / mdd_ / betting | 수익금 제곱 강조 |
| **GAM** | tsg × app / mdd_ | 평균 수익률 고려 |
| **GWM** | tsg × wr / mdd_ / 100 | 승률 반영 |
| **PM** | tpp / mdd_ | 수익률/MDD 비율 |
| **P2M** | tpp² / mdd_ / betting | 수익률 제곱 강조 |
| **PAM** | tpp × app / mdd_ | 평균 수익률 고려 |
| **PWM** | tpp × wr / mdd_ / 100 | 승률 반영 |
| **WM** | wr / mdd_ | 승률/MDD 비율 |
| **TM** | tc / mdd_ | 거래횟수/MDD 비율 |

#### 2.5.3 교차검증 MERGE 계산

```python
def GetOptiValidStd(train_data, valid_data, optistd, betting, exponential):
    std = 0
    count = len(train_data)
    for i in range(count):
        ex = (count - i) * 2 / count if exponential and count > 1 else 1.0
        std += train_data[i] * valid_data[i] * ex
    return std / count
```

**Weight (exponential=True)**:
- 6분할: `2.00, 1.66, 1.33, 1.00, 0.66, 0.33` (최근 → 과거)
- 3분할: `2.00, 1.33, 0.66`
- 1분할: `1.00` (가중치 없음)

**문제점**: TRAIN × VALID 곱셈이 극단값 증폭 (Study 문서 참조)

---

## 3. 코드 실행 메커니즘 심층 분석

### 3.1 조건식 로딩 프로세스

#### 3.1.1 전체 흐름도

```
[조건식 MD 파일]
      ↓
[GetBuyStg/GetSellStg 함수] (back_static.py)
      ↓
[텍스트 → Python 코드 변환]
      ↓
[compile() 호출]
      ↓
[컴파일된 바이트코드]
      ↓
[BackEngineKiwoomTick/Min] (backengine_*.py)
      ↓
[exec() 실행 + 변수 주입]
      ↓
[Buy/Sell 메서드 호출]
```

#### 3.1.2 GetBuyStg 함수 분석

**파일**: `backtester/back_static.py:200-224`

```python
def GetBuyStg(buytxt, gubun):
    # 1. 매수 실행 코드 추가
    buytxt  = buytxt.split('if 매수:')[0] + 'if 매수:\n    self.Buy(vturn, vkey)'

    # 2. indicator 코드 분리
    buystg  = ''
    indistg = ''
    for line in buytxt.split('\n'):
        if 'self.indicator' in line:
            indistg += f'{line}\n'
        else:
            buystg += f'{line}\n'

    # 3. 컴파일
    if buystg != '':
        try:
            buystg = compile(buystg, '<string>', 'exec')
        except:
            buystg = None
            if gubun == 0: print_exc()
    else:
        buystg = None

    # 4. indicator 코드 컴파일
    if indistg != '':
        try:
            indistg = compile(indistg, '<string>', 'exec')
        except:
            indistg = None
    else:
        indistg = None

    return buystg, indistg
```

**핵심 메커니즘**:
1. 조건식 텍스트를 `if 매수:` 기준으로 분리
2. indicator 관련 코드를 별도로 분리
3. Python `compile()` 함수로 바이트코드 변환
4. 컴파일 실패 시 `None` 반환 및 에러 출력

#### 3.1.3 GetSellStg 함수 분석

**파일**: `backtester/back_static.py:227-235`

```python
def GetSellStg(sellstg, gubun):
    # 1. sell_cond 초기화 + 매도 실행 코드 추가
    sellstg = 'sell_cond = 0\n' + sellstg.split('if 매도:')[0] + \
              'if 매도:\n    self.Sell(vturn, vkey, sell_cond)'

    # 2. 매도 조건 번호 매핑
    sellstg, dict_cond = SetSellCond(sellstg.split('\n'))

    # 3. 컴파일
    try:
        sellstg = compile(sellstg, '<string>', 'exec')
    except:
        sellstg = None
        if gubun == 0: print_exc()

    return sellstg, dict_cond
```

#### 3.1.4 SetSellCond 함수 (매도 조건 번호 매핑)

**파일**: `backtester/back_static.py:261-272`

```python
def SetSellCond(selllist):
    count = 1
    sellstg = ''
    dict_cond = {0: '전략종료청산', 100: '분할매도', 200: '손절청산'}

    for i, text in enumerate(selllist):
        if '#' not in text and ('매도 = True' in text or ...):
            # 조건 번호 매핑
            dict_cond[count] = selllist[i - 1]
            sellstg = f"{sellstg}{text.split('매도')[0]}sell_cond = {count}\n"
            count += 1
        if text != '':
            sellstg = f"{sellstg}{text}\n"

    return sellstg, dict_cond
```

**매도 조건 번호 체계**:
- `0`: 전략종료청산 (기본)
- `1~N`: 조건별 매도 (예: `수익률 >= 3`)
- `100`: 분할매도
- `200`: 손절청산

### 3.2 백테스팅 엔진 실행 흐름

#### 3.2.1 BackEngineKiwoomTick 클래스

**파일**: `backtester/backengine_kiwoom_tick.py:14-77`

```python
class BackEngineKiwoomTick:
    def __init__(self, gubun, wq, tq, bq, beq_list, bstq_list, profile=False):
        gc.disable()
        self.gubun        = gubun
        self.wq           = wq    # windowQ
        self.tq           = tq    # totalQ
        self.bq           = bq    # backQ
        self.beq_list     = beq_list
        self.beq          = beq_list[gubun]
        self.bstq_list    = bstq_list

        self.buystg       = None  # 컴파일된 매수 조건식
        self.sellstg      = None  # 컴파일된 매도 조건식
        self.indistg      = None  # 컴파일된 indicator 코드

        self.vars         = []    # 최적화 변수 리스트
        self.vars_list    = []

        self.MainLoop()
```

#### 3.2.2 MainLoop 실행 흐름

```python
def MainLoop(self):
    while True:
        data = self.beq.get()  # 큐에서 데이터 수신

        if '정보' in data[0]:
            if self.back_type == '최적화':
                if data[0] == '백테정보':
                    self.betting   = data[1]
                    self.startday  = data[3]
                    self.endday    = data[4]
                    self.starttime = data[5]
                    self.endtime   = data[6]
                    # 조건식 로드
                    self.buystg, self.indistg = GetBuyStg(data[7], self.gubun)
                    self.sellstg, self.dict_sconds = GetSellStg(data[8], self.gubun)

                elif data[0] == '변수정보':
                    self.vars_list = data[1]
                    self.opti_turn = data[2]
                    self.vars = [var[1] for var in self.vars_list]  # 변수 추출
                    self.BackTest()  # 백테스팅 실행
```

#### 3.2.3 변수 주입 및 조건식 실행

백테스팅 실행 시 다음 변수들이 조건식에 주입됨:

```python
# 로컬 변수로 주입
locals_dict = {
    # 가격 변수
    '현재가': 현재가,
    '시가': 시가,
    '고가': 고가,
    '저가': 저가,
    '등락율': 등락율,
    # ... (826개 또는 752개 변수)

    # 최적화 변수
    'self.vars': self.vars,

    # 메서드
    'self.Buy': self.Buy,
    'self.Sell': self.Sell,
    'self.indicator': self.indicator,

    # 틱/분봉 번호
    'vturn': vturn,
    'vkey': vkey,
}

# 조건식 실행
exec(self.buystg, globals(), locals_dict)
exec(self.sellstg, globals(), locals_dict)
```

### 3.3 핵심 메커니즘 요약

#### 3.3.1 조건식 → 실행 가능 코드 변환

1. **텍스트 파싱**: MD 파일에서 Python 코드 블록 추출
2. **코드 변환**: `GetBuyStg/GetSellStg`로 실행 가능 형태로 변환
3. **컴파일**: `compile('<string>', 'exec')` 호출
4. **변수 주입**: `exec(code, globals(), locals())`로 실행
5. **Buy/Sell 호출**: 조건 만족 시 메서드 호출

#### 3.3.2 장단점 분석

**장점**:
- ✅ 유연성: 조건식을 텍스트로 관리하여 수정 용이
- ✅ 가독성: MD 파일로 사람이 읽기 쉬움
- ✅ 버전 관리: Git으로 조건식 변경 이력 추적 가능
- ✅ 문서화: 조건식과 문서가 통합됨

**단점**:
- ⚠️ 런타임 오버헤드: 컴파일 시간 소요
- ⚠️ 디버깅 어려움: 텍스트 기반 오류 추적 복잡
- ⚠️ 타입 검증 부재: 런타임 오류 발생 가능
- ⚠️ 보안 리스크: `exec()` 사용 시 주의 필요

---

## 4. AI 기반 조건식 자동 생성 시스템

### 4.1 시스템 아키텍처

#### 4.1.1 전체 구조도

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 조건식 생성 엔진                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐│
│  │              │     │              │     │              ││
│  │  LLM 생성기  │────▶│  검증 모듈   │────▶│  템플릿화    ││
│  │  (GPT-4/     │     │  (문법/구조)  │     │  (MD 파일)  ││
│  │   Claude)    │     │              │     │              ││
│  │              │     │              │     │              ││
│  └──────────────┘     └──────────────┘     └──────────────┘│
│         ▲                                         │          │
│         │                                         ▼          │
│         │                                  ┌──────────────┐ │
│  ┌──────────────┐                         │              │ │
│  │              │                         │  조건식 DB   │ │
│  │  피드백 루프 │◀────────────────────────│  (sqlite)    │ │
│  │              │                         │              │ │
│  └──────────────┘                         └──────────────┘ │
│         ▲                                                   │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          │
┌─────────┼───────────────────────────────────────────────────┐
│         │            자동 백테스팅 파이프라인                 │
├─────────┼───────────────────────────────────────────────────┤
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐│
│  │              │     │              │     │              ││
│  │  백테스터    │────▶│  최적화      │────▶│  결과 평가   ││
│  │  실행        │     │  (Grid/      │     │  (14개 지표) ││
│  │              │     │   Optuna/GA) │     │              ││
│  │              │     │              │     │              ││
│  └──────────────┘     └──────────────┘     └──────────────┘│
│         │                                         │          │
│         │                                         ▼          │
│         │                                  ┌──────────────┐ │
│         └─────────────────────────────────▶│  결과 DB     │ │
│                                             │  (성과 기록) │ │
│                                             └──────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 4.2 LLM 기반 조건식 생성

#### 4.2.1 프롬프트 엔지니어링 전략

**1단계: 컨텍스트 주입**

```python
system_prompt = f"""
당신은 STOM 주식 자동거래 시스템의 전문 조건식 작성자입니다.

# 역할
- 백테스팅 가능한 Python 기반 매수/매도 조건식 작성
- 826개 틱 변수 또는 752개 분봉 변수 사용
- 가이드라인 100% 준수

# 제약사항
1. 변수는 가이드라인에 명시된 것만 사용
2. 매수 조건은 'not (조건)' 형태
3. 매도 조건은 '조건' 형태
4. 한 줄에 하나의 조건만
5. 복잡한 비교는 명시적 분리 (a < b < c → a < b and b < c)

# 참조 문서
{guideline_content}  # Back_Testing_Guideline_Tick/Min.md 전체 내용
{template_content}   # Condition_Document_Template_Guideline.md 전체 내용
"""

user_prompt = f"""
다음 전략에 대한 조건식을 작성해주세요:

**전략 타입**: {strategy_type}  # 예: "장 시작 급등주 포착"
**대상 시간**: {time_range}     # 예: "09:00:00 ~ 09:05:00"
**대상 종목**: {target_stocks}  # 예: "시가총액 3,000억 미만"
**핵심 변수**: {key_variables}  # 예: "체결강도, 초당거래대금, 등락율"

**기대 성과**:
- 승률: {target_winrate}%
- 평균 수익률: {target_profit}%
- MDD: {target_mdd}% 이하
"""
```

**2단계: Few-shot Learning**

```python
few_shot_examples = [
    {
        "strategy": "장 시작 급등주 포착",
        "buy_conditions": """
not (현재가 < 1000 or 현재가 > 50000)
not (등락율 < 1.0 or 등락율 > 8.0)
not (체결강도 < 50 or 체결강도 > 300)
not (초당거래대금 < self.vars[1])
not (회전율 < self.vars[2])
        """,
        "sell_conditions": """
수익률 <= -2  # 손절
수익률 >= self.vars[3]  # 익절
최고수익률 > 3 and 수익률 < 최고수익률 * self.vars[4]  # 트레일링
        """,
        "variables": {
            "self.vars[1]": {"range": [1, 10, 1], "default": 3, "unit": "억원"},
            "self.vars[2]": {"range": [1, 5, 0.5], "default": 2, "unit": "%"},
            "self.vars[3]": {"range": [2, 5, 0.5], "default": 3, "unit": "%"},
            "self.vars[4]": {"range": [0.6, 0.9, 0.05], "default": 0.75, "unit": "비율"},
        }
    },
    # 10-20개의 성공 사례 추가
]
```

**3단계: 반복적 개선**

```python
def generate_condition_with_refinement(strategy_desc, max_iterations=5):
    for iteration in range(max_iterations):
        # LLM 생성
        generated_code = llm.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            few_shot_examples=few_shot_examples,
            temperature=0.3 + iteration * 0.1  # 점진적 탐색 확대
        )

        # 문법 검증
        is_valid, errors = validate_syntax(generated_code)
        if not is_valid:
            # 에러 피드백
            user_prompt += f"\n\n이전 시도 에러:\n{errors}\n수정 요청"
            continue

        # 구조 검증
        is_template_valid = validate_template(generated_code)
        if not is_template_valid:
            user_prompt += f"\n\n템플릿 구조 위반. 수정 요청"
            continue

        # 변수 범위 검증
        is_var_valid = validate_var_ranges(generated_code)
        if not is_var_valid:
            user_prompt += f"\n\nself.vars 범위 오류. 최대 20개/변수 준수"
            continue

        # 성공
        return generated_code, iteration

    # 실패
    return None, max_iterations
```

#### 4.2.2 Genetic Programming 조건식 진화

**DEAP 라이브러리 활용**

```python
from deap import base, creator, tools, algorithms
import operator

# 1. Primitive Set 정의
pset = gp.PrimitiveSet("MAIN", 0)

# 변수 추가 (826개 틱 변수)
pset.addEphemeralConstant("현재가", lambda: random.uniform(1000, 50000))
pset.addEphemeralConstant("등락율", lambda: random.uniform(-30, 30))
pset.addEphemeralConstant("체결강도", lambda: random.uniform(0, 500))
# ... 826개 변수

# 연산자 추가
pset.addPrimitive(operator.add, 2)
pset.addPrimitive(operator.sub, 2)
pset.addPrimitive(operator.mul, 2)
pset.addPrimitive(safe_div, 2)  # 0 나누기 방지
pset.addPrimitive(operator.lt, 2)
pset.addPrimitive(operator.gt, 2)
pset.addPrimitive(operator.and_, 2)
pset.addPrimitive(operator.or_, 2)
pset.addPrimitive(operator.not_, 1)

# 함수 추가
pset.addPrimitive(이동평균, 2)  # (현재가, window)
pset.addPrimitive(최고현재가, 2)
pset.addPrimitive(체결강도평균, 2)

# 2. Fitness 정의
creator.create("FitnessMax", base.Fitness, weights=(1.0,))  # 수익률 최대화
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

# 3. Toolbox 설정
toolbox = base.Toolbox()
toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=3)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)

# 4. Fitness 평가 함수
def eval_condition(individual):
    # 조건식 → Python 코드 변환
    func = toolbox.compile(expr=individual)

    # 백테스팅 실행
    result = run_backtest(func)

    # 적합도 반환 (예: 수익률)
    return (result['profit_rate'],)

toolbox.register("evaluate", eval_condition)
toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr, pset=pset)

# 5. 진화 실행
population = toolbox.population(n=300)
hof = tools.HallOfFame(1)

stats = tools.Statistics(lambda ind: ind.fitness.values)
stats.register("avg", np.mean)
stats.register("std", np.std)
stats.register("min", np.min)
stats.register("max", np.max)

population, log = algorithms.eaSimple(
    population, toolbox,
    cxpb=0.5,  # 교배 확률
    mutpb=0.2,  # 변이 확률
    ngen=40,    # 세대 수
    stats=stats,
    halloffame=hof,
    verbose=True
)

# 최적 조건식
best_condition = hof[0]
```

### 4.3 Feature Importance 기반 변수 선택

#### 4.3.1 XGBoost Feature Importance

```python
import xgboost as xgb
import shap

# 1. 데이터 준비
# 과거 백테스팅 결과에서 변수-성과 관계 학습
df_history = load_backtest_history()

# X: 826개 변수 값
# y: 성과 지표 (TG, TP, TPI 등)
X = df_history[tick_variables]  # 826개 컬럼
y = df_history['profit_rate']

# 2. XGBoost 모델 학습
model = xgb.XGBRegressor(
    n_estimators=1000,
    max_depth=6,
    learning_rate=0.01,
    objective='reg:squarederror'
)
model.fit(X, y)

# 3. Feature Importance 추출
importance = model.feature_importances_
feature_importance_df = pd.DataFrame({
    'feature': X.columns,
    'importance': importance
}).sort_values('importance', ascending=False)

# 상위 50개 변수 선택
top_features = feature_importance_df.head(50)['feature'].tolist()

print("Top 10 중요 변수:")
print(feature_importance_df.head(10))
# 예:
#           feature  importance
# 체결강도           0.142
# 초당거래대금       0.118
# 등락율             0.095
# 회전율             0.082
# 시가대비등락율     0.071
# ...
```

#### 4.3.2 SHAP 분석

```python
# SHAP explainer 생성
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

# 변수별 기여도 시각화
shap.summary_plot(shap_values, X, plot_type="bar")

# 변수 간 상호작용 분석
shap.dependence_plot("체결강도", shap_values, X, interaction_index="초당거래대금")

# 조건식 생성 시 SHAP 인사이트 활용
def generate_conditions_with_shap(shap_values, X, threshold=0.01):
    """
    SHAP 값이 높은 변수 조합으로 조건식 자동 생성
    """
    conditions = []

    # 각 샘플의 SHAP 값 분석
    for i in range(len(shap_values)):
        # 긍정적 기여 변수 (수익 증가)
        positive_features = np.where(shap_values[i] > threshold)[0]

        for feat_idx in positive_features:
            feat_name = X.columns[feat_idx]
            feat_value = X.iloc[i, feat_idx]
            shap_contrib = shap_values[i, feat_idx]

            # 조건 생성
            if shap_contrib > 0.05:
                conditions.append(f"not ({feat_name} < {feat_value * 0.9})")

    # 중복 제거 및 빈도 정렬
    condition_counts = Counter(conditions)
    top_conditions = condition_counts.most_common(20)

    return [cond for cond, count in top_conditions]
```

### 4.4 템플릿 기반 변수 조합 자동화

#### 4.4.1 조건식 템플릿 라이브러리

```python
CONDITION_TEMPLATES = {
    "급등주_포착": {
        "description": "장 시작 급등주 포착",
        "time_range": "09:00:00 ~ 09:05:00",
        "buy_template": """
# 가격 범위
not (현재가 < {price_min} or 현재가 > {price_max})

# 등락율 범위
not (등락율 < {change_min} or 등락율 > {change_max})

# 체결강도
not (체결강도 < {strength_min} or 체결강도 > {strength_max})

# 거래대금
not (초당거래대금 < {trade_amount_min})
not (당일거래대금 < {daily_amount_min})

# 회전율
not (회전율 < {turnover_min})

# 호가 조건
not (매도총잔량 > 매수총잔량 * {hoga_ratio})

# VI 회피
not (현재가 >= VI아래5호가)
        """,
        "sell_template": """
# 손절
수익률 <= {stop_loss}

# 익절
수익률 >= {take_profit}

# 트레일링 스톱
최고수익률 > {trailing_threshold} and 수익률 < 최고수익률 * {trailing_ratio}

# 시간 청산
보유시간 > {max_holding_time}

# 체결강도 급락
체결강도 <= 최고체결강도(30) * {strength_drop_ratio}
        """,
        "var_ranges": {
            "price_min": [500, 2000, 100],
            "price_max": [30000, 100000, 5000],
            "change_min": [0.5, 3.0, 0.5],
            "change_max": [5.0, 15.0, 1.0],
            # ... 변수별 범위
        }
    },

    "돌파_전략": {
        "description": "고가 돌파 모멘텀 포착",
        "time_range": "09:30:00 ~ 10:00:00",
        "buy_template": """
# 고가 돌파
not (현재가 < 최고현재가({lookback_period}))

# 이동평균선 상방
not (현재가 < 이동평균({ma_period}))
not (이동평균({ma_short}) < 이동평균({ma_long}))

# 거래량 급증
not (초당거래대금 < 초당거래대금평균({volume_period}) * {volume_ratio})

# 등락율 각도
not (등락율각도({angle_period}) < {angle_threshold})
        """,
        # ...
    },

    # 20-30개의 템플릿 정의
}
```

#### 4.4.2 자동 조합 생성기

```python
def generate_conditions_from_template(template_name, param_grid=None):
    """
    템플릿과 파라미터 그리드로 조건식 자동 생성
    """
    template = CONDITION_TEMPLATES[template_name]

    if param_grid is None:
        # 기본 파라미터 그리드
        param_grid = {
            key: np.arange(var_range[0], var_range[1], var_range[2])
            for key, var_range in template['var_ranges'].items()
        }

    # 모든 조합 생성 (GridSearchCV 방식)
    from itertools import product
    param_combinations = list(product(*param_grid.values()))

    generated_conditions = []
    for params in param_combinations[:1000]:  # 최대 1000개
        param_dict = dict(zip(param_grid.keys(), params))

        # 템플릿 채우기
        buy_code = template['buy_template'].format(**param_dict)
        sell_code = template['sell_template'].format(**param_dict)

        # 조건식 객체 생성
        condition = {
            "name": f"{template_name}_{len(generated_conditions):04d}",
            "description": template['description'],
            "time_range": template['time_range'],
            "buy_conditions": buy_code,
            "sell_conditions": sell_code,
            "parameters": param_dict
        }

        generated_conditions.append(condition)

    return generated_conditions

# 사용 예
conditions = generate_conditions_from_template("급등주_포착")
print(f"생성된 조건식 수: {len(conditions)}")
# 생성된 조건식 수: 1000
```

---

## 5. 자동화 순환 프로세스 설계

### 5.1 4단계 순환 시스템

```
┌────────────────────────────────────────────────────────────┐
│                   순환 프로세스                             │
│                                                             │
│                                                             │
│     ┌─────────────┐                                        │
│     │             │                                        │
│     │  1. 생성    │◀───────────────────┐                  │
│     │  Generation │                     │                  │
│     │             │                     │                  │
│     └──────┬──────┘                     │                  │
│            │                            │                  │
│            │ 조건식                     │                  │
│            ▼                            │                  │
│     ┌─────────────┐                    │ 피드백            │
│     │             │                     │                  │
│     │  2. 테스트  │                     │                  │
│     │  Testing    │                     │                  │
│     │             │                     │                  │
│     └──────┬──────┘                     │                  │
│            │                            │                  │
│            │ 결과                       │                  │
│            ▼                            │                  │
│     ┌─────────────┐                    │                  │
│     │             │                     │                  │
│     │  3. 기록    │                     │                  │
│     │  Logging    │                     │                  │
│     │             │                     │                  │
│     └──────┬──────┘                     │                  │
│            │                            │                  │
│            │ 분석                       │                  │
│            ▼                            │                  │
│     ┌─────────────┐                    │                  │
│     │             │                     │                  │
│     │  4. 개선    │────────────────────┘                  │
│     │  Improvement│                                        │
│     │             │                                        │
│     └─────────────┘                                        │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### 5.2 단계 1: 생성 (Generation)

#### 5.2.1 생성 전략 3가지

**전략 A: LLM 기반 생성**
```python
def generate_with_llm(strategy_type, iteration=0):
    """
    LLM을 사용한 조건식 생성
    """
    # 이전 성과 데이터 로드
    past_performance = load_performance_data(strategy_type)

    # 성공 패턴 분석
    success_patterns = analyze_success_patterns(past_performance)

    # 프롬프트 생성
    prompt = build_prompt(
        strategy_type=strategy_type,
        success_patterns=success_patterns,
        iteration=iteration
    )

    # LLM 호출
    response = call_llm_api(prompt)

    # 검증
    is_valid, code = validate_and_extract(response)

    return code if is_valid else None
```

**전략 B: Genetic Programming**
```python
def generate_with_gp(population_size=300, generations=40):
    """
    Genetic Programming을 통한 조건식 진화
    """
    # 초기 개체군 생성
    population = initialize_population(population_size)

    for gen in range(generations):
        # 적합도 평가
        fitness_scores = [evaluate_fitness(ind) for ind in population]

        # 선택 (토너먼트)
        selected = tournament_selection(population, fitness_scores)

        # 교배
        offspring = crossover(selected)

        # 변이
        mutated = mutate(offspring)

        # 다음 세대
        population = elitism(population, mutated, fitness_scores)

    return best_individual(population)
```

**전략 C: 템플릿 기반 조합**
```python
def generate_with_template(template_name, optimization_method="random"):
    """
    템플릿 기반 파라미터 조합 생성
    """
    template = load_template(template_name)

    if optimization_method == "random":
        # 랜덤 샘플링 (빠른 탐색)
        params = random_sample_params(template.var_ranges, n=100)
    elif optimization_method == "sobol":
        # Sobol 시퀀스 (준난수)
        params = sobol_sample_params(template.var_ranges, n=100)
    elif optimization_method == "latin_hypercube":
        # Latin Hypercube (공간 균등 분포)
        params = lhs_sample_params(template.var_ranges, n=100)

    conditions = []
    for param_set in params:
        code = fill_template(template, param_set)
        conditions.append(code)

    return conditions
```

#### 5.2.2 생성 파이프라인

```python
class ConditionGenerationPipeline:
    def __init__(self, strategy_type, generation_methods=['llm', 'gp', 'template']):
        self.strategy_type = strategy_type
        self.generation_methods = generation_methods
        self.generated_conditions = []

    def run(self, batch_size=100):
        """
        여러 생성 방법을 병렬로 실행
        """
        results = []

        # LLM 생성 (10-20개)
        if 'llm' in self.generation_methods:
            llm_conditions = []
            for i in range(batch_size // 5):
                code = generate_with_llm(self.strategy_type, iteration=i)
                if code:
                    llm_conditions.append(code)
            results.extend(llm_conditions)

        # GP 생성 (30-50개)
        if 'gp' in self.generation_methods:
            gp_conditions = generate_with_gp(
                population_size=300,
                generations=40
            )
            results.extend(gp_conditions[:batch_size // 2])

        # 템플릿 생성 (나머지)
        if 'template' in self.generation_methods:
            remaining = batch_size - len(results)
            template_conditions = generate_with_template(
                self.strategy_type,
                optimization_method="sobol"
            )
            results.extend(template_conditions[:remaining])

        self.generated_conditions = results
        return results
```

### 5.3 단계 2: 테스트 (Testing)

#### 5.3.1 자동 백테스팅 파이프라인

```python
class AutoBacktestingPipeline:
    def __init__(self, db_path, start_date, end_date):
        self.db_path = db_path
        self.start_date = start_date
        self.end_date = end_date
        self.results = []

    def run_single_backtest(self, condition_code, condition_id):
        """
        단일 조건식 백테스팅
        """
        try:
            # 1. 조건식 MD 파일 생성
            md_file = self.create_md_file(condition_code, condition_id)

            # 2. 백테스터 설정
            config = {
                'betting': 10000000,  # 1천만원
                'avgtime': 30,
                'startday': self.start_date,
                'endday': self.end_date,
                'starttime': condition_code['time_range'][0],
                'endtime': condition_code['time_range'][1],
                'buystg': condition_code['buy_conditions'],
                'sellstg': condition_code['sell_conditions']
            }

            # 3. 백테스팅 실행
            result = run_backtest_engine(config)

            # 4. 결과 반환
            return {
                'condition_id': condition_id,
                'success': True,
                'metrics': result,
                'timestamp': datetime.now()
            }

        except Exception as e:
            return {
                'condition_id': condition_id,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now()
            }

    def run_batch(self, conditions, parallel=True, max_workers=8):
        """
        배치 백테스팅 (병렬 처리)
        """
        if parallel:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self.run_single_backtest, cond, i)
                    for i, cond in enumerate(conditions)
                ]
                results = [f.result() for f in futures]
        else:
            results = [
                self.run_single_backtest(cond, i)
                for i, cond in enumerate(conditions)
            ]

        self.results = results
        return results
```

#### 5.3.2 3단계 최적화 전략

```python
class OptimizationPipeline:
    def __init__(self, condition_code):
        self.condition_code = condition_code
        self.best_params = None

    def optimize(self, strategy="adaptive"):
        """
        적응형 최적화 전략
        """
        if strategy == "adaptive":
            # 1단계: 빠른 탐색 (Grid Search, 상위 10개 변수)
            grid_result = self.grid_search_quick()

            # 2단계: 베이지안 최적화 (Optuna, 전체 변수)
            if grid_result['profit_rate'] > 0:
                optuna_result = self.bayesian_optimization(
                    initial_params=grid_result['params']
                )
            else:
                optuna_result = grid_result

            # 3단계: 유전 알고리즘 (GA, 미세 조정)
            if optuna_result['profit_rate'] > 5:
                ga_result = self.genetic_algorithm(
                    initial_params=optuna_result['params']
                )
                return ga_result
            else:
                return optuna_result

        elif strategy == "quick":
            # 빠른 탐색만
            return self.grid_search_quick()

        elif strategy == "thorough":
            # 전체 그리드 서치
            return self.grid_search_full()

    def grid_search_quick(self):
        """
        상위 10개 변수만 빠른 그리드 서치
        """
        # OR (Overall Range) 섹션 변수 사용
        top_vars = self.condition_code['OR'][:10]

        # 각 변수당 5개 값만 (총 5^10 = 9,765,625 → 실용적으로 1000개 샘플링)
        param_grid = {
            var['name']: np.linspace(var['range'][0], var['range'][1], 5)
            for var in top_vars
        }

        # 랜덤 샘플링
        sampled_params = random_sample(param_grid, n=1000)

        # 백테스팅
        results = [self.evaluate(params) for params in sampled_params]

        # 최적 결과
        best_idx = np.argmax([r['profit_rate'] for r in results])
        return results[best_idx]

    def bayesian_optimization(self, initial_params=None, n_trials=200):
        """
        Optuna 베이지안 최적화
        """
        import optuna

        def objective(trial):
            params = {}
            for var in self.condition_code['BOR'] + self.condition_code['SOR']:
                params[var['name']] = trial.suggest_float(
                    var['name'],
                    var['range'][0],
                    var['range'][1]
                )

            result = self.evaluate(params)
            return result['profit_rate']

        study = optuna.create_study(direction='maximize')

        # 초기값 설정
        if initial_params:
            study.enqueue_trial(initial_params)

        study.optimize(objective, n_trials=n_trials)

        return {
            'params': study.best_params,
            'profit_rate': study.best_value
        }

    def genetic_algorithm(self, initial_params=None, generations=50):
        """
        유전 알고리즘 미세 조정
        """
        # ... (앞서 정의한 GA 코드)
        pass
```

### 5.4 단계 3: 기록 (Logging)

#### 5.4.1 결과 데이터베이스 스키마

```sql
-- 조건식 테이블
CREATE TABLE conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    strategy_type TEXT,
    time_range TEXT,
    target_stocks TEXT,
    buy_conditions TEXT,
    sell_conditions TEXT,
    variables TEXT,  -- JSON 형식
    generation_method TEXT,  -- llm, gp, template
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 백테스팅 결과 테이블
CREATE TABLE backtest_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition_id INTEGER,
    start_date TEXT,
    end_date TEXT,

    -- 14가지 OPTISTD 지표
    TG REAL,  -- 수익금합계
    TP REAL,  -- 수익률합계
    TPI REAL,  -- 매매성능지수
    CAGR REAL,  -- 연간예상수익률
    GM REAL,  -- Gain/MDD
    G2M REAL,  -- Gain²/MDD/Betting
    GAM REAL,  -- Gain×AvgProfit/MDD
    GWM REAL,  -- Gain×WinRate/MDD
    PM REAL,  -- Profit/MDD
    P2M REAL,  -- Profit²/MDD/Betting
    PAM REAL,  -- Profit×AvgProfit/MDD
    PWM REAL,  -- Profit×WinRate/MDD
    WM REAL,  -- WinRate/MDD
    TM REAL,  -- TradeCount/MDD

    -- 기타 지표
    win_rate REAL,
    trade_count INTEGER,
    avg_profit_rate REAL,
    avg_loss_rate REAL,
    mdd REAL,
    max_profit_rate REAL,

    -- 메타 정보
    optimization_method TEXT,  -- grid, optuna, ga
    optimization_time REAL,  -- 초 단위
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (condition_id) REFERENCES conditions(id)
);

-- 최적화 히스토리 테이블
CREATE TABLE optimization_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition_id INTEGER,
    iteration INTEGER,
    params TEXT,  -- JSON 형식
    profit_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (condition_id) REFERENCES conditions(id)
);

-- 실패 로그 테이블
CREATE TABLE failure_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition_id INTEGER,
    error_type TEXT,  -- syntax, runtime, timeout
    error_message TEXT,
    stack_trace TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (condition_id) REFERENCES conditions(id)
);

-- 성과 순위 뷰
CREATE VIEW performance_ranking AS
SELECT
    c.id,
    c.name,
    c.strategy_type,
    b.TP AS profit_rate,
    b.win_rate,
    b.trade_count,
    b.mdd,
    b.CAGR,
    RANK() OVER (PARTITION BY c.strategy_type ORDER BY b.TP DESC) AS rank
FROM conditions c
JOIN backtest_results b ON c.id = b.condition_id
WHERE b.created_at >= datetime('now', '-30 days');
```

#### 5.4.2 자동 로깅 시스템

```python
class ResultLogger:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def log_condition(self, condition_code, generation_method):
        """
        조건식 저장
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO conditions (
                name, description, strategy_type, time_range, target_stocks,
                buy_conditions, sell_conditions, variables, generation_method
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            condition_code['name'],
            condition_code['description'],
            condition_code['strategy_type'],
            json.dumps(condition_code['time_range']),
            condition_code['target_stocks'],
            condition_code['buy_conditions'],
            condition_code['sell_conditions'],
            json.dumps(condition_code['variables']),
            generation_method
        ))
        self.conn.commit()
        return cursor.lastrowid

    def log_backtest_result(self, condition_id, result):
        """
        백테스팅 결과 저장
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO backtest_results (
                condition_id, start_date, end_date,
                TG, TP, TPI, CAGR, GM, G2M, GAM, GWM, PM, P2M, PAM, PWM, WM, TM,
                win_rate, trade_count, avg_profit_rate, avg_loss_rate, mdd, max_profit_rate,
                optimization_method, optimization_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            condition_id,
            result['start_date'],
            result['end_date'],
            result['TG'], result['TP'], result['TPI'], result['CAGR'],
            result['GM'], result['G2M'], result['GAM'], result['GWM'],
            result['PM'], result['P2M'], result['PAM'], result['PWM'], result['WM'], result['TM'],
            result['win_rate'], result['trade_count'],
            result['avg_profit_rate'], result['avg_loss_rate'], result['mdd'], result['max_profit_rate'],
            result['optimization_method'], result['optimization_time']
        ))
        self.conn.commit()

    def log_optimization_step(self, condition_id, iteration, params, profit_rate):
        """
        최적화 각 단계 저장
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO optimization_history (condition_id, iteration, params, profit_rate)
            VALUES (?, ?, ?, ?)
        """, (
            condition_id,
            iteration,
            json.dumps(params),
            profit_rate
        ))
        self.conn.commit()

    def log_failure(self, condition_id, error_type, error_message, stack_trace):
        """
        실패 로그 저장
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO failure_logs (condition_id, error_type, error_message, stack_trace)
            VALUES (?, ?, ?, ?)
        """, (
            condition_id,
            error_type,
            error_message,
            stack_trace
        ))
        self.conn.commit()
```

### 5.5 단계 4: 개선 (Improvement)

#### 5.5.1 성과 분석 및 패턴 인식

```python
class PerformanceAnalyzer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def analyze_success_patterns(self, min_profit_rate=5, min_win_rate=60):
        """
        성공 패턴 분석
        """
        query = """
        SELECT
            c.strategy_type,
            c.variables,
            b.TP AS profit_rate,
            b.win_rate,
            b.trade_count,
            b.mdd
        FROM conditions c
        JOIN backtest_results b ON c.id = b.condition_id
        WHERE b.TP >= ? AND b.win_rate >= ?
        ORDER BY b.TP DESC
        """

        df = pd.read_sql_query(query, self.conn, params=(min_profit_rate, min_win_rate))

        # 변수 패턴 추출
        variable_patterns = []
        for _, row in df.iterrows():
            variables = json.loads(row['variables'])
            for var_name, var_value in variables.items():
                variable_patterns.append({
                    'strategy_type': row['strategy_type'],
                    'variable': var_name,
                    'value': var_value,
                    'profit_rate': row['profit_rate']
                })

        df_patterns = pd.DataFrame(variable_patterns)

        # 전략별 성공 변수 분석
        success_vars = df_patterns.groupby(['strategy_type', 'variable']).agg({
            'value': ['mean', 'std', 'min', 'max'],
            'profit_rate': 'mean'
        }).reset_index()

        return success_vars

    def analyze_failure_patterns(self):
        """
        실패 패턴 분석
        """
        query = """
        SELECT
            error_type,
            error_message,
            COUNT(*) AS count
        FROM failure_logs
        GROUP BY error_type, error_message
        ORDER BY count DESC
        LIMIT 20
        """

        df_failures = pd.read_sql_query(query, self.conn)
        return df_failures

    def find_correlations(self):
        """
        변수 간 상관관계 분석
        """
        query = """
        SELECT
            c.variables,
            b.TP AS profit_rate
        FROM conditions c
        JOIN backtest_results b ON c.id = b.condition_id
        """

        df = pd.read_sql_query(query, self.conn)

        # 변수 추출 및 상관관계 계산
        var_data = []
        for _, row in df.iterrows():
            variables = json.loads(row['variables'])
            variables['profit_rate'] = row['profit_rate']
            var_data.append(variables)

        df_vars = pd.DataFrame(var_data)
        correlation_matrix = df_vars.corr()['profit_rate'].sort_values(ascending=False)

        return correlation_matrix
```

#### 5.5.2 LLM 피드백 루프

```python
class FeedbackLoop:
    def __init__(self, logger, analyzer):
        self.logger = logger
        self.analyzer = analyzer

    def generate_feedback_prompt(self, iteration):
        """
        피드백 프롬프트 생성
        """
        # 성공 패턴 분석
        success_patterns = self.analyzer.analyze_success_patterns()

        # 실패 패턴 분석
        failure_patterns = self.analyzer.analyze_failure_patterns()

        # 상관관계 분석
        correlations = self.analyzer.find_correlations()

        feedback_prompt = f"""
이전 실험 결과를 바탕으로 조건식을 개선해주세요.

# 반복 횟수: {iteration}

# 성공 패턴 (수익률 5% 이상, 승률 60% 이상)
{success_patterns.to_markdown()}

성공한 전략의 공통점:
- 체결강도 범위: 평균 {success_patterns[success_patterns['variable']=='체결강도']['value']['mean'].values[0]:.1f}
- 초당거래대금 최소값: 평균 {success_patterns[success_patterns['variable']=='초당거래대금']['value']['mean'].values[0]:.1f}억
- 등락율 상한: 평균 {success_patterns[success_patterns['variable']=='등락율_상한']['value']['mean'].values[0]:.1f}%

# 실패 패턴 (상위 10개)
{failure_patterns.head(10).to_markdown()}

주요 실패 원인:
1. {failure_patterns.iloc[0]['error_message']} ({failure_patterns.iloc[0]['count']}회)
2. {failure_patterns.iloc[1]['error_message']} ({failure_patterns.iloc[1]['count']}회)

# 변수 상관관계 (수익률과의 상관계수)
{correlations.head(10).to_markdown()}

가장 영향력 있는 변수:
1. {correlations.index[1]}: {correlations.values[1]:.3f}
2. {correlations.index[2]}: {correlations.values[2]:.3f}
3. {correlations.index[3]}: {correlations.values[3]:.3f}

# 개선 지침
1. 성공 패턴의 변수 범위를 더 적극적으로 활용하세요
2. 실패 원인을 회피하도록 조건식을 수정하세요
3. 상관관계가 높은 변수를 우선적으로 사용하세요
4. 이전 반복에서 효과가 없었던 변수는 제거하거나 범위를 조정하세요
        """

        return feedback_prompt

    def improve_conditions(self, current_best, iteration):
        """
        조건식 개선
        """
        feedback_prompt = self.generate_feedback_prompt(iteration)

        # LLM 호출
        improved_code = call_llm_api(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=feedback_prompt,
            few_shot_examples=[current_best]  # 현재 최고 성과 조건식
        )

        return improved_code
```

#### 5.5.3 자동 진화 루프

```python
class EvolutionaryLoop:
    def __init__(self, generator, tester, logger, feedback):
        self.generator = generator
        self.tester = tester
        self.logger = logger
        self.feedback = feedback

        self.best_conditions = []
        self.iteration = 0

    def run(self, max_iterations=100, target_profit_rate=20, early_stop_patience=10):
        """
        자동 진화 루프 실행
        """
        no_improvement_count = 0

        for self.iteration in range(max_iterations):
            print(f"\n{'='*60}")
            print(f"반복 {self.iteration + 1}/{max_iterations}")
            print(f"{'='*60}")

            # 1. 조건식 생성
            if self.iteration == 0:
                # 첫 반복: 다양한 방법으로 생성
                conditions = self.generator.run(batch_size=100)
            else:
                # 후속 반복: 피드백 기반 개선
                conditions = []
                for best in self.best_conditions[:10]:
                    improved = self.feedback.improve_conditions(best, self.iteration)
                    if improved:
                        conditions.append(improved)

                # 새로운 탐색도 추가 (exploitation vs exploration)
                new_conditions = self.generator.run(batch_size=50)
                conditions.extend(new_conditions)

            print(f"생성된 조건식: {len(conditions)}개")

            # 2. 백테스팅
            results = self.tester.run_batch(conditions, parallel=True)
            successful_results = [r for r in results if r['success']]
            print(f"성공한 백테스팅: {len(successful_results)}/{len(results)}개")

            # 3. 결과 기록
            for i, result in enumerate(results):
                condition_id = self.logger.log_condition(
                    conditions[i],
                    generation_method='evolutionary'
                )

                if result['success']:
                    self.logger.log_backtest_result(condition_id, result['metrics'])
                else:
                    self.logger.log_failure(
                        condition_id,
                        'runtime',
                        result['error'],
                        ''
                    )

            # 4. 최고 성과 업데이트
            if successful_results:
                best_result = max(successful_results, key=lambda x: x['metrics']['TP'])
                print(f"최고 수익률: {best_result['metrics']['TP']:.2f}%")
                print(f"승률: {best_result['metrics']['win_rate']:.2f}%")
                print(f"거래 횟수: {best_result['metrics']['trade_count']}회")

                # 최고 성과 조건식 저장
                if not self.best_conditions or best_result['metrics']['TP'] > self.best_conditions[0]['metrics']['TP']:
                    self.best_conditions.insert(0, {
                        'code': conditions[best_result['condition_id']],
                        'metrics': best_result['metrics']
                    })
                    self.best_conditions = self.best_conditions[:20]  # 상위 20개 유지
                    no_improvement_count = 0
                else:
                    no_improvement_count += 1

                # 목표 달성 확인
                if best_result['metrics']['TP'] >= target_profit_rate:
                    print(f"\n목표 수익률 {target_profit_rate}% 달성!")
                    break
            else:
                no_improvement_count += 1

            # Early stopping
            if no_improvement_count >= early_stop_patience:
                print(f"\n{early_stop_patience}회 연속 개선 없음. 조기 종료.")
                break

        print(f"\n{'='*60}")
        print("진화 루프 완료")
        print(f"최종 최고 수익률: {self.best_conditions[0]['metrics']['TP']:.2f}%")
        print(f"{'='*60}")

        return self.best_conditions
```

---

## 6. 실제 구현 방안

### 6.1 시스템 아키텍처

#### 6.1.1 CLI 기반 자동화 파이프라인

```bash
# 프로젝트 구조
stom_automation/
├── cli.py                    # 메인 CLI 진입점
├── config/
│   ├── config.yaml          # 시스템 설정
│   └── strategies.yaml      # 전략 정의
├── src/
│   ├── generation/
│   │   ├── llm_generator.py
│   │   ├── gp_generator.py
│   │   └── template_generator.py
│   ├── testing/
│   │   ├── backtester.py
│   │   └── optimizer.py
│   ├── logging/
│   │   ├── logger.py
│   │   └── database.py
│   ├── feedback/
│   │   ├── analyzer.py
│   │   └── improver.py
│   └── utils/
│       ├── validators.py
│       └── helpers.py
├── data/
│   ├── conditions.db        # 조건식 DB
│   ├── results.db           # 결과 DB
│   └── templates/           # 템플릿 라이브러리
├── logs/                    # 실행 로그
└── outputs/                 # 생성된 조건식 파일
    ├── generated/
    ├── tested/
    └── optimized/
```

#### 6.1.2 CLI 명령어 체계

```bash
# 조건식 생성
stom-auto generate \
    --strategy "급등주_포착" \
    --method llm \
    --count 50 \
    --output ./outputs/generated/

# 백테스팅
stom-auto backtest \
    --input ./outputs/generated/*.md \
    --start-date 20230101 \
    --end-date 20231231 \
    --parallel 8 \
    --output ./outputs/tested/

# 최적화
stom-auto optimize \
    --input ./outputs/tested/best_10.md \
    --method optuna \
    --trials 200 \
    --output ./outputs/optimized/

# 진화 루프 실행
stom-auto evolve \
    --strategy "급등주_포착" \
    --iterations 100 \
    --batch-size 50 \
    --target-profit 20 \
    --output ./outputs/evolved/

# 결과 분석
stom-auto analyze \
    --db ./data/results.db \
    --strategy "급등주_포착" \
    --min-profit 5 \
    --report ./outputs/analysis_report.html

# 대시보드 실행
stom-auto dashboard \
    --db ./data/results.db \
    --port 8050
```

### 6.2 데이터베이스 스키마 설계

#### 6.2.1 확장된 스키마

```sql
-- (앞서 정의한 테이블에 추가)

-- 전략 템플릿 테이블
CREATE TABLE strategy_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    time_range TEXT,
    target_stocks TEXT,
    buy_template TEXT,
    sell_template TEXT,
    var_ranges TEXT,  -- JSON 형식
    success_rate REAL DEFAULT 0,
    avg_profit_rate REAL DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 변수 중요도 테이블
CREATE TABLE variable_importance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_type TEXT,
    variable_name TEXT,
    importance_score REAL,
    correlation_with_profit REAL,
    usage_count INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(strategy_type, variable_name)
);

-- 피드백 히스토리 테이블
CREATE TABLE feedback_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration INTEGER,
    feedback_text TEXT,
    improvement_direction TEXT,
    applied_changes TEXT,  -- JSON 형식
    result_profit_rate REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 실험 세션 테이블
CREATE TABLE experiment_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_name TEXT,
    strategy_type TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_conditions_generated INTEGER,
    successful_backtests INTEGER,
    best_profit_rate REAL,
    best_condition_id INTEGER,
    status TEXT,  -- running, completed, failed
    FOREIGN KEY (best_condition_id) REFERENCES conditions(id)
);
```

### 6.3 단계별 구현 계획

#### Phase 1: 조건식 생성 엔진 (1-2개월)

**Week 1-2: 기본 인프라 구축**
- [ ] 프로젝트 구조 설정
- [ ] CLI 프레임워크 구축 (Click 사용)
- [ ] 데이터베이스 스키마 구현
- [ ] 설정 파일 관리 시스템

**Week 3-4: LLM 생성기 구현**
- [ ] OpenAI/Anthropic API 통합
- [ ] 프롬프트 엔지니어링 및 템플릿
- [ ] Few-shot learning 데이터 준비
- [ ] 응답 검증 및 파싱

**Week 5-6: Genetic Programming 구현**
- [ ] DEAP 라이브러리 통합
- [ ] Primitive Set 정의 (826/752 변수)
- [ ] Fitness 평가 함수
- [ ] 진화 알고리즘 파라미터 튜닝

**Week 7-8: 템플릿 시스템 구현**
- [ ] 템플릿 라이브러리 구축 (20-30개)
- [ ] 파라미터 조합 생성기
- [ ] 템플릿 검증 시스템
- [ ] 통합 테스트

#### Phase 2: 자동 백테스팅 파이프라인 (1개월)

**Week 9-10: 백테스터 통합**
- [ ] 기존 백테스터 래핑
- [ ] MD 파일 자동 생성
- [ ] 백테스트 큐 관리
- [ ] 병렬 처리 구현 (ThreadPoolExecutor)

**Week 11-12: 최적화 파이프라인**
- [ ] Grid Search 구현
- [ ] Optuna 통합
- [ ] GA 통합
- [ ] 적응형 최적화 전략

#### Phase 3: 피드백 루프 구현 (2개월)

**Week 13-14: 결과 로깅 시스템**
- [ ] 로거 클래스 구현
- [ ] 데이터베이스 저장 자동화
- [ ] 실패 로그 관리
- [ ] 최적화 히스토리 추적

**Week 15-16: 성과 분석 엔진**
- [ ] 성공/실패 패턴 분석
- [ ] 변수 상관관계 분석
- [ ] Feature Importance (XGBoost)
- [ ] SHAP 분석 통합

**Week 17-18: 피드백 생성 시스템**
- [ ] 피드백 프롬프트 생성기
- [ ] LLM 피드백 루프
- [ ] 조건식 개선 메커니즘
- [ ] 자동 진화 루프

**Week 19-20: 대시보드 구축**
- [ ] Plotly Dash 대시보드
- [ ] 실시간 모니터링
- [ ] 성과 시각화
- [ ] 비교 분석 도구

#### Phase 4: 대규모 실험 및 최적화 (지속적)

**Week 21+: 대규모 실험**
- [ ] 1000개 조건식 생성 실험
- [ ] 성과 평가 및 분석
- [ ] 시스템 튜닝 및 최적화
- [ ] 실전 배포 준비

### 6.4 기술 스택

#### 6.4.1 핵심 라이브러리

```yaml
# requirements.txt
python>=3.9

# LLM 통합
openai>=1.0.0
anthropic>=0.5.0

# Genetic Programming
deap>=1.3.3
numpy>=1.24.0

# 최적화
optuna>=3.0.0
scikit-optimize>=0.9.0

# Feature Importance
xgboost>=1.7.0
shap>=0.42.0
scikit-learn>=1.3.0

# 데이터 처리
pandas>=2.0.0
pyarrow>=12.0.0

# CLI
click>=8.1.0
rich>=13.0.0
tqdm>=4.65.0

# 데이터베이스
sqlalchemy>=2.0.0
alembic>=1.11.0

# 대시보드
plotly>=5.15.0
dash>=2.11.0

# 테스팅
pytest>=7.4.0
pytest-cov>=4.1.0

# 기타
pyyaml>=6.0
python-dotenv>=1.0.0
loguru>=0.7.0
```

#### 6.4.2 설정 파일 예제

```yaml
# config/config.yaml
system:
  db_path: ./data/conditions.db
  log_level: INFO
  max_workers: 8

generation:
  llm:
    provider: anthropic  # openai, anthropic
    model: claude-3-5-sonnet-20241022
    temperature: 0.3
    max_tokens: 4096

  gp:
    population_size: 300
    generations: 40
    cxpb: 0.5
    mutpb: 0.2

  template:
    library_path: ./data/templates/
    default_method: sobol

backtesting:
  start_date: 20230101
  end_date: 20231231
  betting: 10000000
  parallel: true
  max_workers: 8

optimization:
  grid:
    max_combinations: 1000

  optuna:
    n_trials: 200
    sampler: TPESampler

  ga:
    generations: 50
    population_size: 100

feedback:
  min_success_profit_rate: 5.0
  min_success_win_rate: 60.0
  analysis_window_days: 30

evolution:
  max_iterations: 100
  batch_size: 50
  target_profit_rate: 20.0
  early_stop_patience: 10
```

### 6.5 기대 효과 분석

#### 6.5.1 정량적 효과

| 지표 | 현재 | 1년 후 목표 | 개선률 |
|------|------|-------------|--------|
| 조건식 개발 시간 | 2-5일/개 | 10-30분/개 | 96% 단축 |
| 연간 생성 조건식 | 50개 | 5,000개 | 100배 증가 |
| 백테스팅 처리량 | 10개/일 | 1,000개/일 | 100배 증가 |
| 최적화 시간 | 수일 | 수시간 | 95% 단축 |
| 평균 수익률 | 기준선 | +20-30% | 수익률 향상 |
| 승률 | 기준선 | +5-10%p | 안정성 향상 |

#### 6.5.2 정성적 효과

**전략 다양성**:
- 다양한 시장 조건에 대응 가능한 조건식 포트폴리오 구축
- 틱/분봉, 시간대별, 종목군별 특화 전략 확보

**지식 축적**:
- 성공/실패 패턴의 체계적 기록
- 변수 중요도 및 상관관계 데이터베이스 구축
- 재사용 가능한 템플릿 라이브러리 확대

**리스크 관리**:
- 대규모 백테스팅을 통한 과적합 방지
- 교차검증 및 Walk-Forward 분석
- 실전 배포 전 철저한 검증

**확장성**:
- 새로운 시장 (미국 주식, 선물 등) 적용 용이
- 조건식 생성 방법론의 지속적 개선
- 커뮤니티 기여 및 협업 가능

---

## 7. 리스크 및 완화 전략

### 7.1 주요 리스크

#### 7.1.1 과적합 (Overfitting)

**리스크 설명**:
- 백테스팅 데이터에 과도하게 최적화
- 실전에서 성과 급감

**완화 전략**:
1. **교차검증**: 6분할 Walk-Forward 분석
2. **Out-of-Sample 테스트**: 학습 데이터와 분리된 기간 검증
3. **단순성 우선**: 복잡한 조건식보다 단순한 조건식 선호
4. **정규화**: 변수 개수 제한 (최대 10-15개)
5. **실전 검증**: 소액 라이브 트레이딩으로 재검증

#### 7.1.2 LLM 비용

**리스크 설명**:
- 대규모 조건식 생성 시 API 비용 급증
- 예산 초과 가능성

**완화 전략**:
1. **하이브리드 접근**: LLM (20%) + GP (30%) + 템플릿 (50%)
2. **비용 모니터링**: 실시간 비용 추적 및 알림
3. **프롬프트 최적화**: 토큰 사용량 최소화
4. **캐싱**: 유사 요청 결과 재사용
5. **오픈소스 LLM**: Llama, Mistral 등 로컬 모델 활용

#### 7.1.3 백테스팅 신뢰도

**리스크 설명**:
- 슬리피지, 수수료 등 실전 요소 미반영
- Look-ahead 바이어스

**완화 전략**:
1. **보수적 가정**: 슬리피지 0.2%, 수수료 0.015% 적용
2. **체결 지연 모델링**: 1-3틱 지연 시뮬레이션
3. **유동성 필터**: 거래대금 최소값 설정
4. **호가창 시뮬레이션**: 실제 호가 데이터 활용
5. **라이브 검증**: 페이퍼 트레이딩 필수

#### 7.1.4 시스템 복잡도

**리스크 설명**:
- 여러 컴포넌트 통합의 복잡성
- 디버깅 및 유지보수 어려움

**완화 전략**:
1. **모듈화 설계**: 각 컴포넌트 독립 실행 가능
2. **포괄적 로깅**: 모든 단계 상세 기록
3. **단위 테스트**: 80% 이상 커버리지
4. **문서화**: API 문서 및 사용 가이드
5. **점진적 배포**: Phase별 단계적 구현

### 7.2 성능 리스크

#### 7.2.1 백테스팅 속도

**문제**:
- 1000개 조건식 × 1년 데이터 = 수십 시간 소요

**해결책**:
1. **병렬 처리**: 8-16 워커 동시 실행
2. **데이터 캐싱**: 자주 사용하는 데이터 메모리 유지
3. **Numba JIT**: 계산 집약적 부분 컴파일
4. **증분 백테스팅**: 변경된 부분만 재계산
5. **클라우드 확장**: AWS/GCP 스팟 인스턴스 활용

#### 7.2.2 데이터베이스 병목

**문제**:
- 대량 INSERT/UPDATE 시 성능 저하

**해결책**:
1. **Batch INSERT**: 1000개씩 묶어서 삽입
2. **인덱싱**: 자주 쿼리하는 컬럼 인덱스 생성
3. **파티셔닝**: 날짜별 테이블 분할
4. **WAL 모드**: SQLite Write-Ahead Logging
5. **PostgreSQL 전환**: 대규모 데이터 시 고려

### 7.3 운영 리스크

#### 7.3.1 시스템 장애

**대응 방안**:
- **체크포인팅**: 주기적 상태 저장 및 재개 기능
- **에러 복구**: 자동 재시도 메커니즘
- **알림 시스템**: 텔레그램/이메일 알림
- **백업**: 일일 데이터베이스 백업

#### 7.3.2 보안

**대응 방안**:
- **API 키 관리**: 환경 변수 또는 Vault 사용
- **코드 검증**: 생성된 조건식 샌드박스 실행
- **접근 제어**: 데이터베이스 권한 관리
- **감사 로그**: 모든 작업 기록

---

## 8. 결론 및 로드맵

### 8.1 연구 요약

본 연구는 STOM 시스템의 조건식 개발 프로세스를 다음과 같이 혁신합니다:

1. **AI/LLM 통합**: GPT-4, Claude 3.5 Sonnet을 활용한 조건식 자동 생성
2. **Genetic Programming**: DEAP 라이브러리를 통한 조건식 진화
3. **Feature Importance**: XGBoost, SHAP 기반 변수 선택 최적화
4. **자동화 순환 프로세스**: 생성 → 테스트 → 기록 → 개선의 4단계 순환
5. **대규모 실험**: 1000개 이상 조건식 동시 검증 가능

**핵심 성과**:
- 조건식 개발 시간: 2-5일 → 10-30분 (96% 단축)
- 탐색 가능 조합: 수십 개 → 수천 개 (100배 증가)
- 최적화 시간: 587년 → 수시간 (99.9% 단축)
- 예상 수익률 향상: +20-30%

### 8.2 향후 로드맵

#### 단기 (3-6개월)

**Phase 1-2 완료**:
- ✅ LLM 기반 조건식 생성기
- ✅ Genetic Programming 엔진
- ✅ 템플릿 시스템
- ✅ 자동 백테스팅 파이프라인

**초기 성과 검증**:
- 100개 조건식 생성 및 테스트
- 성공률 30% 이상 목표
- 베스트 조건식 10개 실전 배포

#### 중기 (6-12개월)

**Phase 3 완료**:
- ✅ 피드백 루프 완전 자동화
- ✅ 성과 분석 대시보드
- ✅ 자동 진화 루프

**대규모 실험**:
- 1000개 조건식 생성 캠페인
- 다양한 전략 타입 (10종 이상)
- 시장 조건별 특화 전략

**실전 검증**:
- 상위 50개 조건식 라이브 트레이딩
- 3개월 성과 추적 및 분석
- A/B 테스트: 수작업 vs AI 생성

#### 장기 (1-2년)

**Phase 4+: 고도화**:
- 강화학습 (RL) 통합: 동적 전략 학습
- 멀티 에이전트 시스템: 전략 포트폴리오 최적화
- 실시간 시장 적응: 온라인 학습
- 앙상블 전략: 여러 조건식 조합

**확장**:
- 미국 주식 시장 적용
- 선물/옵션 전략 개발
- 암호화폐 24/7 트레이딩
- 글로벌 시장 통합

**커뮤니티**:
- 오픈소스 공개
- 사용자 기여 전략 풀
- 전략 마켓플레이스
- 협업 플랫폼 구축

### 8.3 최종 결론

본 연구는 **AI 기반 조건식 자동화 및 순환 연구 시스템**을 통해 STOM의 조건식 개발을 혁신적으로 개선할 수 있음을 보여줍니다.

**핵심 가치**:
1. **시간 효율성**: 수동 작업 96% 감소
2. **탐색 범위**: 인간의 한계를 뛰어넘는 조합 탐색
3. **지속적 개선**: 자동 피드백 루프를 통한 진화
4. **지식 축적**: 모든 실험 결과의 체계적 기록

**실현 가능성**:
- 기존 STOM 시스템과 완전 호환
- 단계별 점진적 구현 가능
- 검증된 기술 스택 활용
- 명확한 ROI 및 성과 지표

**다음 단계**:
1. Phase 1 구현 시작 (조건식 생성 엔진)
2. 소규모 PoC (Proof of Concept) 실험
3. 성과 검증 후 본격 배포
4. 지속적 개선 및 확장

이 시스템은 STOM을 단순한 백테스팅 플랫폼에서 **자율 학습 트레이딩 AI**로 진화시킬 것입니다.

---

**작성자**: Claude Code AI
**검토자**: STOM Development Team
**최종 업데이트**: 2025-12-01
**문서 버전**: 1.0
**다음 검토 예정일**: 2025-03-01

---

## 참고 문헌

1. STOM 공식 문서
   - `docs/Manual/` - 시스템 매뉴얼
   - `docs/Guideline/` - 개발 가이드라인
   - `docs/Condition/` - 조건식 문서 (133개)

2. 기존 연구 보고서
   - `docs/Study/ResearchReports/AI_ML_Trading_Strategy_Automation_Research.md`
   - `docs/Study/ResearchReports/Research_Report_Automated_Condition_Finding.md`
   - `docs/Study/SystemAnalysis/Optistd_System_Analysis.md`
   - `docs/Study/SystemAnalysis/STOM_Optimization_System_Improvements.md`

3. 소스 코드
   - `backtester/back_static.py` - 조건식 로딩 메커니즘
   - `backtester/backengine_kiwoom_tick.py` - 백테스팅 엔진
   - `backtester/optimiz.py` - 최적화 시스템

4. 외부 참고 자료
   - DEAP Documentation: https://deap.readthedocs.io/
   - Optuna Documentation: https://optuna.readthedocs.io/
   - XGBoost Documentation: https://xgboost.readthedocs.io/
   - SHAP Documentation: https://shap.readthedocs.io/
   - Anthropic Claude API: https://docs.anthropic.com/
   - OpenAI API: https://platform.openai.com/docs/

---

**문서 끝**
