# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소의 코드를 작업할 때 참고할 가이드를 제공합니다.

## 시스템 개요

STOM (System Trading Optimization Manager) V1은 한국 주식시장(키움증권 연동) 및 암호화폐 시장(업비트, 바이낸스)을 위한 전문가급 고빈도 트레이딩 시스템입니다. PyQt5로 구축된 멀티프로세스 실시간 트레이딩 플랫폼으로 포괄적인 백테스팅 기능을 갖추고 있습니다.

**프로젝트 통계** (2025-11-26 기준):
- Python 소스 파일 157개 (~70,000+ 라인)
- 마크다운 문서 175개 이상
- 트레이딩 조건 파일 133개 (98.3% 문서화 준수율)
- 데이터 분리를 위한 SQLite 데이터베이스 15개
- 15개의 프로세스 간 통신 큐를 갖춘 멀티프로세스 아키텍처

## 주요 명령어

### 설치 및 설정
```bash
# 의존성 설치 (Python 64-bit 필요)
pip_install_64.bat

# 데이터베이스 무결성 검사 (시작 시 자동 실행)
python ./utility/database_check.py
```

### 시스템 실행
```bash
# 메인 애플리케이션 (관리자 권한 필요)
stom.bat

# 주식 트레이딩 모드
stom_stock.bat

# 암호화폐 트레이딩 모드
stom_coin.bat

# Python 직접 실행
python stom.py [stock|coin]
```

### 개발 및 테스팅
```bash
# 백테스팅 실행
python backtester/backtest.py

# 파라미터 최적화
python backtester/optimiz.py

# 데이터베이스 작업
python utility/db_update_day.py
python utility/db_update_back.py
```

## 아키텍처 개요

### 핵심 구성요소

**멀티프로세스 아키텍처:**
- **메인 프로세스**: PyQt5 GUI (`ui/ui_mainwindow.py` - 1,083 라인)
- **데이터 수신기**: 실시간 시장 데이터 수집 (`*_receiver_*.py`)
- **전략 엔진**: 트레이딩 신호 생성 (`*_strategy_*.py`)
- **트레이더**: 주문 실행 및 관리 (`*_trader.py`)
- **백테스팅**: 과거 데이터 분석 및 최적화 (`backtester/`)
- **쿼리 프로세스**: 큐 기반 아키텍처를 통한 데이터베이스 작업
- **매니저 프로세스**: ZMQ 기반 통신을 위한 키움 매니저

**주요 모듈:**
- `/stock/` - 키움 API를 통한 한국 주식시장 트레이딩 (9개 파일, ~7,800 라인)
- `/coin/` - 업비트, 바이낸스 암호화폐 트레이딩 (16개 파일, ~10,098 라인)
- `/backtester/` - 과거 데이터 테스팅 및 최적화 (23개 파일, ~12,993 라인)
- `/ui/` - PyQt5 사용자 인터페이스 구성요소 (70개 이상 파일, ~20,625 라인)
- `/utility/` - 공유 기능 및 데이터베이스 관리 (24개 파일, ~3,419 라인)
- `/docs/` - 포괄적인 문서 (175개 이상 마크다운 파일)
- `/lecture/` - 교육 자료 및 성능 테스트

### 데이터베이스 구조

`/_database/` 내 SQLite 데이터베이스:
- `setting.db` - 시스템 설정 및 암호화된 인증정보
- `stock_tick.db` / `coin_tick.db` - 실시간 틱 데이터
- `stock_min.db` / `coin_min.db` - 분봉 데이터
- `tradelist.db` - 트레이딩 내역 및 성과
- `strategy.db` - 트레이딩 전략 및 파라미터
- `backtest.db` - 백테스팅 결과
- `optuna.db` - 최적화 결과

### 설정 관리

`utility/setting.py`를 통한 모든 설정 관리:
- 데이터베이스 경로 및 연결
- 트레이딩 파라미터 및 리스크 통제
- API 인증정보 (Fernet 암호화)
- 시장별 설정
- 종목/코인 블랙리스트 관리

## 개발 패턴

### 파일 명명 규칙
- `*_receiver_*.py` - 실시간 데이터 수집 (WebSocket/ZMQ)
- `*_strategy_*.py` - 트레이딩 로직 및 신호 생성
- `*_trader.py` - 주문 실행 및 포지션 관리
- `*_manager.py` - 프로세스/리소스 조율
- `backengine_*_*.py` - 시장별 백테스팅 (시장 × 시간프레임)
- `ui_*.py` - 인터페이스 구성요소 및 이벤트 핸들러
- `ui_button_clicked_*.py` - 이벤트 핸들러 (cvj=코인체결잔고, svj=주식체결잔고)
- `ui_update_*.py` - 데이터 표시 업데이트 (테이블, 텍스트, 진행상황)
- `ui_draw_*.py` - 차트 렌더링 (캔들, 실시간, TreeMap)
- `set_*.py` - UI 구성요소 설정 및 레이아웃
- `_database/` - SQLite 데이터베이스 (git에서 제외)
- `_log/` - 애플리케이션 로그 (git에서 제외)

### 주요 클래스 및 패턴

**디자인 패턴:**
- **전략 패턴(Strategy Pattern)**: 각 시장마다 전용 전략 엔진
- **옵저버 패턴(Observer Pattern)**: 큐/WebSocket을 통한 실시간 데이터 업데이트
- **팩토리 패턴(Factory Pattern)**: 시장별 엔진 (키움, 업비트, 바이낸스)
- **싱글톤 패턴(Singleton Pattern)**: 설정 및 데이터베이스 매니저
- **템플릿 메서드 패턴(Template Method)**: Receiver 클래스를 상속하는 Strategy 클래스
- **커맨드 패턴(Command Pattern)**: 모든 프로세스 간 통신을 위한 큐 기반 작업

**클래스 계층구조:**
- Stock 모듈은 Kiwoom 베이스 클래스를 상속
- Coin 모듈은 Upbit/Binance 베이스 클래스를 상속
- Tick 전략이 기본, Minute 전략이 파생
- Strategy 클래스는 훅 메서드와 함께 Template Method 패턴 사용

**코드 패턴:**
- 한국어 변수명 광범위하게 사용 (현재가, 시가, 고가, 저가, 등락율)
- 자기참조 인덱싱: N번째 변수 접근을 위한 `self.vars[N]`
- 딕셔너리 조회: 과거 데이터를 위한 `Parameter_Previous(index, lookback)`
- 데이터 파라미터 전달을 위한 튜플 언패킹
- 데코레이터: `@pyqtSlot`, `@thread_decorator`, `@error_decorator`

### 프로세스 간 통신

**큐 기반 아키텍처** (15개 큐):
```python
# 메인 큐 리스트 (qlist 인덱스)
qlist = [
    windowQ,    # 0  - 메인 윈도우 이벤트
    soundQ,     # 1  - 오디오 알림
    queryQ,     # 2  - 데이터베이스 작업
    teleQ,      # 3  - 텔레그램 알림
    chartQ,     # 4  - 차트 업데이트
    hogaQ,      # 5  - 호가 데이터
    webcQ,      # 6  - 웹 통신
    backQ,      # 7  - 백테스팅
    creceivQ,   # 8  - 코인 수신기
    ctraderQ,   # 9  - 코인 트레이더
    cstgQ,      # 10 - 코인 전략
    liveQ,      # 11 - 실시간 트레이딩 데이터
    kimpQ,      # 12 - 김치 프리미엄 (차익거래)
    wdzservQ,   # 13 - WebSocket ZMQ 서버
    totalQ      # 14 - 전체 통계
]
```

**통신 방법:**
- 순차 작업을 위한 Python multiprocessing 큐
- 고성능 실시간 데이터 스트리밍을 위한 ZeroMQ (ZMQ)
- 거래소 API를 위한 WebSocket 연결 (업비트, 바이낸스)
- 영구 저장 및 프로세스 간 데이터 공유를 위한 SQLite
- UI 업데이트 및 논블로킹 작업을 위한 Threading

## 중요 기술 세부사항

### 시장별 요구사항
- **키움 주식**: Windows 필요, `C:/OpenAPI`에 키움 OpenAPI 설치
- **암호화폐**: REST API + WebSocket 연결
- **실시간 데이터**: 초고빈도 트레이딩을 위한 틱 레벨 처리

### 성능 고려사항
- 고성능 데이터 처리를 위한 numpy/pandas 사용
- 기술적 분석을 위한 TA-Lib (`/utility/`의 커스텀 wheel)
- 실시간 차트 렌더링을 위한 pyqtgraph
- 인덱싱된 테이블로 최적화된 데이터베이스 쿼리

### 보안 기능
- cryptography.fernet을 사용한 암호화된 인증정보 저장
- `utility/static.py`를 통한 API 키 관리
- 리스크 통제를 위한 블랙리스트 관리
- 내장된 포지션 사이징 및 리스크 관리

### 의존성
주요 의존성 (`pip_install_64.bat` 참조):
- PyQt5 생태계 (GUI, WebEngine, pyqtgraph)
- 트레이딩 API (pyupbit, python-binance)
- 데이터 처리 (numpy==1.26.4, pandas==2.0.3)
- 기술적 분석 (TA-Lib 커스텀 wheel)
- 최적화 (optuna, cmaes)
- 통신 (websockets, pyzmq)

## 문서 구조

### 문서 아키텍처 (`/docs/`)

**Manual/** - 포괄적인 시스템 분석 (16개 파일):
- `01_Overview/` - 프로젝트 범위 및 기술 스택
- `02_Architecture/` - 시스템 설계 및 구성요소 상호작용
- `03_Modules/` - 상세 분석 (stock, coin, ui, utility, backtester)
- `04_API/` - 통합 패턴
- `05_UI_UX/` - 인터페이스 분석
- `06_Data/` - 데이터베이스 구조 및 관리
- `07_Trading/` - 실행 엔진
- `08_Backtesting/` - 테스팅 및 최적화
- `09_Manual/` - 사용자 가이드
- `10_Conclusion/` - 요약 및 참고문헌
- `DOCUMENTATION_GUIDE.md` - 검증 절차

**Guideline/** - 개발 표준:
- `Back_Testing_Guideline_Tick.md` (33KB, 826개 문서화된 변수)
- `Back_Testing_Guideline_Min.md` (25KB, 752개 문서화된 변수)
- `Condition_Document_Template_Guideline.md` - 트레이딩 조건 템플릿
- `Stock_Database_Information.md` (108/93 컬럼 문서화)
- `Manual_Generation_Guideline.md` - 매뉴얼 생성 프로세스
- `사용설명서/` - 사용자 매뉴얼 (한글, 8개 파일)

**Condition/** - 트레이딩 조건 (133개 파일, 98.3% 준수):
- `Tick/` - 72개 조건 파일 (초단위 전략)
- `Min/` - 61개 조건 파일 (분봉 전략)
- `Idea/` - AI 어시스턴트의 전략 아이디어
- `Reference/` - PyTrader, YouTube 참고자료

**CodeReview/** - 기술 분석:
- `Backtesting_Data_Loading_Multicore_Analysis.md`

### 트레이딩 조건 문서 패턴

각 조건 파일은 다음 구조를 따릅니다:
- **BO (Buy Optimization)** - 실제 값이 포함된 최적화된 매수 조건
- **BOR (Buy Optimization Range)** - 그리드 서치를 위한 변수 범위 `[최소, 최대, 단계]`
- **SO (Sell Optimization)** - 최적화된 매도 조건
- **SOR (Sell Optimization Range)** - 매도 파라미터 범위
- **OR (Overall Range)** - 상위 10개 주요 변수만
- **GAR (Genetic Algorithm Range)** - 유전 알고리즘을 위한 `[최소, 최대]` 형식

### 문서 검증

**최근 검증 (2025-11-26)**:
- 119/121개 조건 파일 (98.3%)이 문서화 가이드라인 준수
- 자동화된 최적화 섹션 생성 구현
- 코드-문서 추적성 확립
- 경로 수정: `STOM_V1/` → `STOM/`
- 명령어 업데이트: `python main.py` → `python stom.py`

**검증 프로세스**:
1. `DOCUMENTATION_GUIDE.md`를 통한 자동화 검사
2. 조건 파일에 대한 자체 검사 절차
3. 소스 파일에 연결된 코드 스니펫 참조
4. 복잡한 섹션에 대한 수동 검토

## 일반적인 개발 작업

### 새로운 트레이딩 전략 추가
1. 적절한 시장 디렉토리(`stock/` 또는 `coin/`)에 전략 파일 생성
2. 명명 패턴 준수: `{시장}_strategy_{시간프레임}.py`
3. 기존 기술적 지표를 사용하여 전략 로직 구현
4. `/docs/Condition/Tick/` 또는 `/docs/Condition/Min/`에 조건 문서 생성
5. 조건 문서 템플릿 준수 (BO, BOR, SO, SOR, OR, GAR 섹션)
6. UI 또는 직접 SQL 삽입을 통해 데이터베이스에 전략 추가
7. 실제 배포 전 백테스팅 엔진으로 테스트
8. 98.3% 문서화 가이드라인 준수 보장

### 데이터베이스 스키마 변경
1. 새 데이터베이스 경로를 위해 `utility/setting.py` 수정
2. 새 쿼리를 위해 `utility/query.py` 업데이트
3. 무결성 확인을 위해 `utility/database_check.py` 실행
4. 기존 데이터에 대한 마이그레이션 스크립트 고려

### UI 수정
1. `ui/set_*.py` 파일에서 레이아웃 변경
2. `ui/ui_*.py` 파일에서 이벤트 핸들러
3. `ui/set_style.py`에서 스타일링 업데이트
4. `ui/ui_draw_*.py`에서 차트 수정

### 성능 최적화
1. `utility/total_code_line.py` 및 타이밍 테스트를 사용한 프로파일링
2. `utility/query.py`에서 데이터베이스 쿼리 최적화
3. 계산을 위한 numpy 벡터화 고려
4. CPU 집약적 작업에 multiprocessing 사용
5. `/lecture/testcode/`의 성능 벤치마크 참조:
   - `numpyint_vs_pureint.py` - NumPy vs Python 정수
   - `pandas.at_vs_list.apd_to_df.py` - 데이터 접근 방법
   - `dict_insert_vs_update.py` - 딕셔너리 작업
   - `pickle_speed.py` - 직렬화 성능

### 테스팅 및 품질 보증

**테스팅 인프라**:
- `/lecture/testcode/`의 교육용 테스트 코드
- 최적화 결정을 위한 성능 비교 테스트
- ZMQ 통신 테스트 (`zmq_pub.py`, `zmq_sub1/2/3.py`)
- 패턴 인식 테스트 (`test_candle_pattern.py`)
- 수수료 계산 테스트 (`test_withdrawfee.py`)

**품질 검사**:
- `database_check.py` - 시작 시 자동 실행
- 애플리케이션 시작 시 데이터 무결성 검증
- 문서화 준수율 추적 (현재 98.3%)
- 코드-문서 정렬 검증

**백테스터 검증**:
- `back_code_test.py` - 조건 코드 검증
- `backfinder.py` - 전략 발견 및 테스팅

## 문제 해결

### 일반적인 문제
- **관리자 권한 필요**: 모든 배치 파일이 권한 상승 요청
- **데이터베이스 잠금**: 멀티프로세스 작업에서 동시 접근 확인
- **API 연결 실패**: 암호화된 저장소의 인증정보 확인
- **메모리 사용량**: 대용량 데이터셋에 대한 `psutil` 통합으로 모니터링

### 디버깅
- 시스템에서 자동 생성되는 로그 파일
- 실시간 알림을 위한 텔레그램 통합
- 시작 시 데이터베이스 무결성 검사
- UI를 통한 내장 성능 모니터링

### 개발 환경
- 키움 API 통합을 위해 Windows 필요
- 메모리 관리를 위해 Python 64-bit 필요
- 시스템 작업을 위해 관리자 권한 필요
- 트레이딩 인터페이스를 위해 멀티 모니터 권장

## 프로세스 흐름 및 실행 모델

### 멀티프로세스 실행 아키텍처

```
메인 프로세스 (PyQt5 GUI)
├─→ 키움 매니저 프로세스 (stock/kiwoom_manager.py)
│   ├─→ Receiver Tick 프로세스 (WebSocket/ZMQ 스트리밍)
│   ├─→ Receiver Min 프로세스 (분봉 데이터 집계)
│   ├─→ 전략 엔진 프로세스 (신호 생성)
│   └─→ 트레이더 프로세스 (주문 실행 및 관리)
│
├─→ 코인 수신기 프로세스
│   ├─→ 업비트 WebSocket (실시간 틱 데이터)
│   ├─→ 바이낸스 WebSocket (실시간 틱 데이터)
│   ├─→ 전략 엔진 (통합 또는 분리)
│   └─→ 트레이더 프로세스 (멀티 거래소 주문)
│
├─→ 쿼리 프로세스 (queryQ를 통한 데이터베이스 작업)
├─→ 백테스터 프로세스 (병렬화된 최적화)
├─→ Kimp 프로세스 (김치 프리미엄 차익거래 모니터링)
└─→ 차트 업데이트 스레드 (UI 렌더링)
```

### 데이터 흐름 패턴

**실시간 트레이딩 흐름**:
1. 거래소 → WebSocket/API → 수신기 프로세스
2. 수신기 → 큐 → 전략 엔진
3. 전략 → 신호 → 트레이더 프로세스
4. 트레이더 → 주문 → 거래소 API
5. 결과 → 데이터베이스 (queryQ를 통해) → UI 업데이트

**백테스팅 흐름**:
1. 과거 데이터 (데이터베이스) → BackEngine
2. BackEngine → 전략 로직 → 트레이딩 신호
3. 신호 → 시뮬레이션 주문 → 손익 계산
4. 결과 → 데이터베이스 → 최적화 엔진
5. 최적화 → 파라미터 튜닝 → 반복

**UI 업데이트 흐름**:
1. 프로세스 → 큐 (windowQ/chartQ/hogaQ) → 메인 프로세스
2. 메인 프로세스 → UI 스레드 → 디스플레이 업데이트
3. 사용자 액션 → 버튼 이벤트 → 프로세스 큐 → 워커 프로세스

## 핵심 파일 참조

### 진입점
- `stom.py` - 메인 애플리케이션 진입점 (모드 선택)
- `stom.bat` / `stom_stock.bat` / `stom_coin.bat` - 실행 스크립트

### 핵심 설정
- `utility/setting.py` (42KB) - 전역 설정, 15개 데이터베이스 경로, 암호화된 인증정보
- `utility/static.py` (16KB) - 헬퍼 함수 (threading, 암호화, datetime, UI)
- `utility/query.py` (24KB) - 큐 기반 데이터베이스 작업

### 프로세스 매니저
- `stock/kiwoom_manager.py` - 주식 트레이딩 프로세스 조율
- `ui/ui_mainwindow.py` (1,083 라인) - 메인 GUI 및 프로세스 조정

### 트레이딩 엔진
- `stock/kiwoom_strategy_tick.py` (42KB) - 주식 틱 전략
- `coin/upbit_strategy_min.py` / `coin/binance_strategy_min.py` - 암호화폐 전략
- `stock/kiwoom_trader.py` (46KB) - 주문 실행 및 포지션 관리

### 백테스팅
- `backtester/backtest.py` - 백테스팅 오케스트레이터
- `backtester/backengine_*_*.py` (12개 파일) - 시장별 엔진
- `backtester/optimiz.py` - 그리드 서치 최적화
- `backtester/optimiz_genetic_algorithm.py` - 유전 알고리즘 최적화

## AI 어시스턴트를 위한 중요 규칙

### 코드 수정 시

1. **편집 전 항상 파일 읽기** - 읽지 않은 코드에 변경 제안 금지
2. **한국어 변수명 보존** - 현재가, 시가, 고가, 저가 등 번역 금지
3. **큐 아키텍처 유지** - 모든 프로세스 간 통신은 큐를 통해
4. **명명 규칙 준수** - `*_receiver_*.py`, `*_strategy_*.py` 패턴 존중
5. **문서 업데이트** - 모든 코드 변경 시 해당 문서 업데이트 필요
6. **백테스터로 테스트** - 실제 배포 전 전략 변경사항 검증
7. **데이터베이스 스키마 확인** - 여러 데이터베이스에 걸친 변경사항 조율
8. **준수율 유지** - 조건 문서를 98.3%+ 준수율로 유지

### 기능 추가 시

1. **기존 패턴 사용** - Template Method, Strategy, Observer 패턴 준수
2. **프로세스 경계 존중** - 프로세스 유형 간 관심사 혼합 금지
3. **적절한 모듈에 추가** - Stock/Coin/UI/Utility/Backtester 분리
4. **철저한 문서화** - 새 전략에 대한 조건 문서 생성
5. **성능 고려** - `/lecture/testcode/` 벤치마크 참조
6. **큐 리스트 업데이트** - 필요 시 qlist에 새 큐 추가
7. **민감한 데이터 암호화** - 인증정보에 Fernet 암호화 사용

### 디버깅 시

1. **로그 확인** - `/_log/`에 프로세스별 로그 포함
2. **데이터베이스 검증** - `utility/database_check.py` 실행
3. **큐 통신 테스트** - 프로세스 간 큐 흐름 확인
4. **조건 코드 검증** - `back_code_test.py` 사용
5. **문서 정렬 확인** - 코드가 문서와 일치하는지 확인 (98.3% 목표)

## 최근 프로젝트 상태 (2025-11-26)

**완료된 이니셔티브**:
- Phase 5: 119/121개 조건 파일 (98.3%)이 이제 문서화 준수
- 트레이딩 조건을 위한 자동화된 최적화 섹션 생성
- 매뉴얼 문서 코드 참조 검증 (7개 파일, 138개 코드 블록)
- 문서 전반에 걸친 경로 및 명령어 수정

**현재 초점**:
- 문서-코드 정렬 유지
- 지속적인 전략 최적화
- 성능 벤치마킹 및 개선

**기술 부채**:
- 제한적인 공식 단위 테스트 (교육용 테스트 존재)
- 오래된 모듈의 일부 레거시 코드 패턴
- 여전히 100% 준수로 가져가고 있는 문서 (2개 파일 남음)
