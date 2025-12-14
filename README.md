# STOM (System Trading Optimization Manager) V1

> 한국 주식시장 및 암호화폐 시장을 위한 전문가급 고빈도 트레이딩 시스템

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/license-Proprietary-red.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

---

## 📋 목차

- [개요](#개요)
- [주요 특징](#주요-특징)
- [시스템 요구사항](#시스템-요구사항)
- [빠른 시작](#빠른-시작)
- [프로젝트 구조](#프로젝트-구조)
- [핵심 기능](#핵심-기능)
- [문서](#문서)
- [이중 Python 아키텍처 전략](#이중-python-아키텍처-전략)
- [기술 스택](#기술-스택)
- [개발 환경](#개발-환경)
- [강화된 백테스팅 분석 시스템 (v2.0)](#강화된-백테스팅-분석-시스템-v20) ✨ **NEW**
- [라이선스](#라이선스)

---

## 개요

**STOM (System Trading Optimization Manager)**은 PyQt5로 구축된 멀티프로세스 실시간 트레이딩 플랫폼으로, 한국 주식시장(키움증권 연동)과 암호화폐 시장(업비트, 바이낸스)에서 고빈도 트레이딩을 수행합니다.

### 프로젝트 규모

- **Python 소스 파일**: 157개 (~70,000+ 라인)
- **마크다운 문서**: 175개 이상
- **트레이딩 조건 파일**: 133개 (98.3% 문서화 준수율)
- **SQLite 데이터베이스**: 15개 (데이터 분리 관리)
- **멀티프로세스 아키텍처**: 15개 프로세스 간 통신 큐

### 지원 시장

- **한국 주식**: 키움증권 OpenAPI 연동
- **암호화폐**: 업비트(Upbit), 바이낸스(Binance) REST API 및 WebSocket

---

## 주요 특징

### 🚀 고성능 트레이딩

- **멀티프로세스 아키텍처**: 15개 독립 프로세스를 통한 병렬 처리
- **실시간 데이터**: WebSocket 및 ZeroMQ를 통한 초저지연 데이터 스트리밍
- **고빈도 트레이딩**: 틱(초) 단위 및 분봉 단위 전략 지원
- **비동기 통신**: 큐 기반 프로세스 간 통신으로 논블로킹 실행

### 📊 포괄적인 백테스팅

- **과거 데이터 분석**: SQLite 기반 틱/분봉 데이터베이스
- **전략 최적화**: 그리드 서치, 유전 알고리즘(Optuna) 지원
- **멀티코어 병렬 처리**: CPU 효율적인 백테스팅 엔진
- **실시간 검증**: 백테스팅 결과를 실시간 트레이딩으로 즉시 전환

### 🎯 전문가급 전략

- **133개 검증된 전략**: 틱 72개, 분봉 61개
- **기술적 지표**: TA-Lib 통합 (MACD, RSI, Bollinger Bands, 등)
- **호가창 분석**: 매수/매도벽, 호가 불균형 감지
- **AI 전략**: GPT-5, Claude Opus 기반 전략 아이디어

### 🖥️ 직관적인 UI/UX

- **PyQt5 기반**: 멀티 모니터 지원, 다크 테마
- **실시간 차트**: pyqtgraph를 통한 고성능 차트 렌더링
- **종합 대시보드**: 체결/잔고/수익률 실시간 모니터링
- **텔레그램 알림**: 주요 이벤트 및 트레이딩 결과 푸시 알림

### 🔒 보안 및 리스크 관리

- **암호화된 인증정보**: cryptography.fernet 기반 API 키 저장
- **포지션 사이징**: 내장 리스크 관리 시스템
- **블랙리스트 관리**: 종목/코인 제외 기능
- **손절/익절**: 자동화된 리스크 통제

---

## 시스템 요구사항

### 필수 요구사항

- **운영체제**: Windows 10/11 (64-bit)
- **Python**: Python 3.11 (64-bit 필수, 32-bit 선택)
- **메모리**: 최소 8GB RAM (권장 16GB+)
- **저장공간**: 최소 10GB (데이터베이스 포함)
- **권한**: 관리자 권한 (키움 API 연동 시)

### Python 아키텍처 요구사항

STOM은 **이중 Python 아키텍처**를 사용합니다:

#### 64-bit Python (필수)
- **용도**: 메인 시스템, 암호화폐 트레이딩, 백테스팅, 최적화
- **설치 경로**: `C:\Python\64\Python3119\python.exe` (표준)
- **명령어**: `python` (기본 명령어)
- **TA-Lib**: `TA_Lib-0.4.25-cp311-cp311-win_amd64.whl`

#### 32-bit Python (선택 - 키움 전용)
- **용도**: 키움증권 OpenAPI (32-bit 전용)
- **설치 경로**: `C:\Python\32\Python3119\`
- **설정 방법**: `python.exe` → `python32.exe`로 파일명 변경
- **명령어**: `python32` (변경된 실행 파일 사용)
- **TA-Lib**: `TA_Lib-0.4.27-cp311-cp311-win32.whl`

**이유**: 키움증권 OpenAPI는 32-bit 전용이므로, 주식 트레이딩 사용 시 32-bit Python이 필요합니다. 암호화폐만 사용하는 경우 64-bit Python만으로 충분합니다.

**중요**: 64-bit Python을 표준 `python` 명령어로 사용하고, 32-bit Python은 `python.exe`를 `python32.exe`로 이름 변경하여 구분합니다.

### 주식 트레이딩 (키움증권)

- **키움 OpenAPI**: `C:/OpenAPI`에 설치 필요
- **키움증권 계좌**: 실전 또는 모의투자 계좌
- **인증**: API 인증키 (설정에서 암호화 저장)

### 암호화폐 트레이딩

- **업비트 계정**: API 키 및 시크릿 키
- **바이낸스 계정**: API 키 및 시크릿 키
- **네트워크**: 안정적인 인터넷 연결 (WebSocket)

---

## 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/your-org/STOM.git
cd STOM
```

### 2. 의존성 설치

STOM은 이중 Python 아키텍처를 지원합니다:

#### 옵션 A: 직접 설치 (비가상환경)

**64-bit Python (필수)**:
```bash
pip_install_64.bat
```
- NumPy, Pandas, PyQt5, TA-Lib (64-bit), Optuna, WebSocket 등
- 암호화폐 트레이딩 및 백테스팅에 필요한 모든 패키지

**32-bit Python (키움 사용 시)**:
```bash
pip_install_32.bat
```
- NumPy, Pandas, PyQt5, TA-Lib (32-bit), PyWin32 등
- 키움증권 OpenAPI 연동을 위한 필수 패키지

#### 옵션 B: 가상환경 사용 (권장)

**자동 설정** (64-bit + 32-bit 모두 생성):
```bash
setup_venv.bat
```
- `venv_64bit/` - 메인 시스템 (필수)
- `venv_32bit/` - 키움 API (선택, 32-bit Python이 있는 경우만)

가상환경 생성 후:
```bash
stom_venv.bat           # 통합 모드 (가상환경)
stom_venv_stock.bat     # 주식 전용 (가상환경)
stom_venv_coin.bat      # 암호화폐 전용 (가상환경)
```

### 3. 데이터베이스 초기화

```bash
python utility/database_check.py
```

### 4. 시스템 실행

**통합 모드** (주식 + 코인):
```bash
stom.bat
```

**주식 전용 모드**:
```bash
stom_stock.bat
```

**암호화폐 전용 모드**:
```bash
stom_coin.bat
```

**Python 직접 실행**:
```bash
python stom.py [stock|coin]
```

### 5. 첫 실행 설정

1. **API 인증정보 입력**: UI에서 키움/업비트/바이낸스 API 키 설정
2. **계좌 연동**: 실전 또는 모의투자 계좌 선택
3. **전략 선택**: 백테스팅된 전략 중 선택 또는 커스텀 전략 추가
4. **리스크 설정**: 최대 투자금액, 손절률, 익절률 설정
5. **시작**: 실시간 트레이딩 또는 백테스팅 시작

---

## 프로젝트 구조

```
STOM/
├── stom.py                    # 메인 애플리케이션 진입점
├── CLAUDE.md                  # AI 어시스턴트를 위한 프로젝트 가이드
├── requirements_64bit.txt     # Python 의존성 (64-bit)
├── pip_install_64.bat         # 의존성 자동 설치 스크립트
├── setup_venv.bat             # 가상환경 자동 구축 스크립트
│
├── stock/                     # 주식 트레이딩 모듈 (9개 파일, ~7,800 라인)
│   ├── kiwoom_manager.py      # 키움 프로세스 매니저
│   ├── kiwoom_strategy_tick.py # 주식 틱 전략 엔진
│   ├── kiwoom_trader.py       # 주문 실행 및 관리
│   └── ...
│
├── coin/                      # 암호화폐 트레이딩 모듈 (16개 파일, ~10,098 라인)
│   ├── upbit_receiver.py      # 업비트 WebSocket 수신기
│   ├── binance_receiver.py    # 바이낸스 WebSocket 수신기
│   ├── upbit_strategy_min.py  # 업비트 분봉 전략
│   └── ...
│
├── backtester/                # 백테스팅 시스템 (23개 파일, ~12,993 라인)
│   ├── backtest.py            # 백테스팅 오케스트레이터
│   ├── backengine_stock_tick.py # 주식 틱 백테스팅 엔진
│   ├── optimiz.py             # 그리드 서치 최적화
│   ├── optimiz_genetic_algorithm.py # 유전 알고리즘 최적화
│   └── ...
│
├── ui/                        # PyQt5 사용자 인터페이스 (70+ 파일, ~20,625 라인)
│   ├── ui_mainwindow.py       # 메인 윈도우 (1,083 라인)
│   ├── set_style.py           # 다크 테마 스타일
│   ├── ui_draw_*.py           # 차트 렌더링
│   ├── ui_button_clicked_*.py # 이벤트 핸들러
│   └── ...
│
├── utility/                   # 공유 기능 및 유틸리티 (24개 파일, ~3,419 라인)
│   ├── setting.py             # 전역 설정 및 데이터베이스 경로
│   ├── static.py              # 헬퍼 함수 (암호화, datetime, threading)
│   ├── query.py               # 큐 기반 데이터베이스 작업
│   ├── database_check.py      # 데이터베이스 무결성 검사
│   └── ...
│
├── docs/                      # 포괄적인 문서 (175+ 마크다운 파일)
│   ├── README.md              # 문서 저장소 개요
│   ├── Guideline/             # 개발 가이드라인 (13개 문서)
│   ├── Condition/             # 트레이딩 조건식 (133개 전략 문서)
│   ├── Manual/                # 시스템 매뉴얼 (10개 섹션)
│   └── CodeReview/            # 코드 리뷰 및 분석
│
├── lecture/                   # 교육 자료 및 성능 테스트
│   └── testcode/              # 성능 벤치마크 코드
│
├── icon/                      # 애플리케이션 아이콘
│
├── _database/                 # SQLite 데이터베이스 (15개, git 제외)
│   ├── setting.db             # 시스템 설정
│   ├── stock_tick.db          # 주식 틱 데이터
│   ├── coin_min.db            # 코인 분봉 데이터
│   └── ...
│
└── _log/                      # 애플리케이션 로그 (git 제외)
```

---

## 핵심 기능

### 1. 실시간 트레이딩

#### 멀티프로세스 아키텍처

```
메인 프로세스 (PyQt5 GUI)
├─→ 키움 매니저 (stock/kiwoom_manager.py)
│   ├─→ Receiver Tick (WebSocket/ZMQ 스트리밍)
│   ├─→ Receiver Min (분봉 데이터 집계)
│   ├─→ 전략 엔진 (신호 생성)
│   └─→ 트레이더 (주문 실행)
│
├─→ 코인 수신기 (coin/*_receiver.py)
│   ├─→ 업비트 WebSocket
│   ├─→ 바이낸스 WebSocket
│   ├─→ 전략 엔진
│   └─→ 트레이더
│
├─→ 쿼리 프로세스 (데이터베이스 작업)
├─→ 백테스터 프로세스 (병렬 최적화)
└─→ 차트 업데이트 스레드
```

#### 데이터 흐름

1. **거래소** → WebSocket/API → **수신기 프로세스**
2. **수신기** → 큐 → **전략 엔진**
3. **전략** → 신호 → **트레이더 프로세스**
4. **트레이더** → 주문 → **거래소 API**
5. **결과** → 데이터베이스 → **UI 업데이트**

### 2. 백테스팅 및 최적화

#### 백테스팅 엔진

- **12개 백테스팅 엔진**: 시장(주식/코인) × 시간프레임(틱/분) × 거래소
- **병렬 처리**: 멀티코어 CPU 활용
- **과거 데이터**: SQLite 데이터베이스에서 효율적 로딩
- **성과 분석**: 수익률, 승률, MDD, Sharpe Ratio

#### 최적화 방법

1. **그리드 서치** (`backtester/optimiz.py`):
   - 파라미터 범위 내 전수 탐색
   - 최적 조합 발견

2. **유전 알고리즘** (`backtester/optimiz_genetic_algorithm.py`):
   - Optuna 기반 베이지안 최적화
   - 대규모 파라미터 공간 효율적 탐색

#### 강화된 결과 분석 시스템 (v2.0) ✨

백테스팅 완료 시 **자동으로** 강화된 분석이 실행됩니다:

| 기능 | 설명 |
|------|------|
| **통계적 유의성 검증** | t-test, Cohen's d 효과 크기, 95% 신뢰구간 |
| **동적 임계값 탐색** | 백분위 기반 최적 필터 임계값 자동 탐색 |
| **필터 조합 분석** | 2-3개 필터 조합의 시너지 효과 분석 |
| **ML 특성 중요도** | Decision Tree 기반 변수 중요도 분석 |
| **기간별 안정성** | 5개 기간으로 분할하여 필터 일관성 검증 |
| **조건식 자동 생성** | 분석 결과 기반 적용 가능한 코드 자동 생성 |

상세 내용은 [강화된 분석 시스템 가이드](#강화된-백테스팅-분석-시스템-v20)를 참조하세요.

### 3. 전략 개발

#### 트레이딩 조건식 문서

모든 전략은 표준화된 문서 형식으로 관리:

- **BO (Buy Optimization)**: 최적화된 매수 조건
- **BOR (Buy Optimization Range)**: 매수 파라미터 범위
- **SO (Sell Optimization)**: 최적화된 매도 조건
- **SOR (Sell Optimization Range)**: 매도 파라미터 범위
- **OR (Overall Range)**: 주요 10개 변수
- **GAR (Genetic Algorithm Range)**: 유전 알고리즘 범위

#### 전략 카테고리

**틱 전략 (72개)**:
- 시간대별 전략: 장 초반, 오전장, 오후장
- 모멘텀 기반: 체결강도, 등락율, 급등 속도
- 거래량 기반: 초당거래대금, 거래량 폭발
- 호가창 기반: 매수/매도벽, 호가 불균형
- 갭/돌파/반전 전략

**분봉 전략 (61개)**:
- 기술적 지표: MACD, RSI, Bollinger Bands, MA
- 복합 지표: 다중 지표 융합
- 패턴 분석: 캔들 패턴, 지지/저항

### 4. 데이터베이스 관리

#### SQLite 데이터베이스 (15개)

| 데이터베이스 | 용도 |
|--------------|------|
| `setting.db` | 시스템 설정 및 암호화된 인증정보 |
| `stock_tick.db` | 주식 틱 데이터 |
| `stock_min.db` | 주식 분봉 데이터 |
| `coin_tick.db` | 코인 틱 데이터 |
| `coin_min.db` | 코인 분봉 데이터 |
| `tradelist.db` | 트레이딩 내역 및 성과 |
| `strategy.db` | 전략 및 파라미터 |
| `backtest.db` | 백테스팅 결과 |
| `optuna.db` | 최적화 결과 |

#### 데이터베이스 무결성 검사

```bash
python utility/database_check.py
```

시작 시 자동으로 실행되어 데이터 무결성 검증.

---

## 문서

### 📘 포괄적인 문서 (175+ 문서)

STOM 프로젝트는 **98.3% 문서화 준수율**을 자랑하며, 모든 전략과 시스템 구성요소가 체계적으로 문서화되어 있습니다.

#### 주요 문서 카테고리

1. **[Guideline](./docs/Guideline/)** - 개발 가이드라인 (13개)
   - 백테스팅 가이드 (Tick/Min)
   - 조건식 문서 템플릿
   - 데이터베이스 정보
   - 사용설명서 (1~4부)

2. **[Condition](./docs/Condition/)** - 트레이딩 조건식 (133개)
   - Tick 전략 72개
   - Min 전략 61개
   - AI 전략 아이디어 26개

3. **[Manual](./docs/Manual/)** - 시스템 매뉴얼 (10개 섹션)
   - 프로젝트 개요
   - 시스템 아키텍처
   - 모듈 분석
   - API 연동
   - UI/UX 분석
   - 데이터 관리
   - 트레이딩 엔진
   - 백테스팅 시스템
   - 사용자 매뉴얼
   - 부록 및 참고자료

4. **[CodeReview](./docs/CodeReview/)** - 코드 리뷰
   - 성능 최적화 분석
   - 멀티코어 데이터 로딩

#### 문서 활용

**신규 사용자**:
```
1. docs/Guideline/사용설명서/
2. docs/Manual/01_Overview/
3. docs/Manual/09_Manual/
```

**전략 개발자**:
```
1. docs/Guideline/Back_Testing_Guideline_*.md
2. docs/Condition/Tick/ 또는 docs/Condition/Min/
3. docs/Guideline/Condition_Document_Template_Guideline.md
```

**개발자**:
```
1. docs/Manual/README.md
2. docs/Manual/02_Architecture/
3. docs/Manual/03_Modules/
4. CLAUDE.md
```

자세한 내용은 **[docs/README.md](./docs/README.md)**를 참조하세요.

---

## 이중 Python 아키텍처 전략

STOM은 키움증권 OpenAPI의 32-bit 제약과 현대적인 데이터 처리 요구사항을 동시에 만족하기 위해 **이중 Python 아키텍처**를 채택했습니다.

### 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                        STOM V1 시스템                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐          ┌──────────────────┐          │
│  │  64-bit Python   │          │  32-bit Python   │          │
│  │    (python)      │          │   (python32)     │          │
│  ├──────────────────┤          ├──────────────────┤          │
│  │ • 메인 시스템    │          │ • 키움 API       │          │
│  │ • 암호화폐       │          │ • 주식 수신      │          │
│  │ • 백테스팅       │          │ • 주문 실행      │          │
│  │ • 최적화         │          │   (선택 사항)    │          │
│  │ • UI 렌더링      │          │                  │          │
│  └──────────────────┘          └──────────────────┘          │
│         ▲                               ▲                     │
│         │                               │                     │
│         └───────────────┬───────────────┘                     │
│                         │                                     │
│               ┌─────────▼──────────┐                          │
│               │  프로세스 간 통신   │                          │
│               │  (큐, ZMQ, DB)     │                          │
│               └────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘

**실행 파일 구분 방법**:
- 64-bit: `python.exe` (표준 이름 사용)
- 32-bit: `python.exe` → `python32.exe` (파일명 변경하여 구분)
```

### 실행 명령어 구분

| 구분 | 64-bit | 32-bit |
|------|--------|--------|
| **명령어** | `python` (표준) | `python32` (파일명 변경 후) |
| **설치 경로** | `C:\Python\64\Python3119\python.exe` | `C:\Python\32\Python3119\` |
| **실행 파일** | `python.exe` (원본 이름) | `python32.exe` (변경된 이름) |
| **가상환경** | `venv_64bit\Scripts\python.exe` | `venv_32bit\Scripts\python32.exe` |
| **설정 방법** | 표준 설치 | `python.exe` → `python32.exe` 이름 변경 |

### 패키지 차이

#### 64-bit 전용 패키지
```bash
# 고성능 컴퓨팅
numba                    # JIT 컴파일러

# 웹 통신
websockets               # 거래소 WebSocket
PyQtWebEngine            # 웹 뷰

# 최적화
optuna                   # 베이지안 최적화
optuna-dashboard         # 최적화 대시보드
cmaes                    # CMA-ES 알고리즘

# 시각화
matplotlib               # 차트
pyqtgraph                # 실시간 차트
squarify                 # TreeMap

# 트레이딩 API
pyupbit                  # 업비트
python-binance           # 바이낸스
```

#### 32-bit 전용 패키지
```bash
# 키움 API
pywin32                  # Win32 COM
```

#### 공통 패키지
```bash
# 데이터 처리
numpy==1.26.4
pandas==2.0.3

# GUI
PyQt5
pyzmq

# 기타
cryptography
psutil
python-telegram-bot==13.15
```

### 배치 파일 구조

#### 관리자 권한 획득 메커니즘

모든 배치 파일은 UAC(User Access Control) 프롬프트를 통해 자동으로 관리자 권한을 요청합니다:

```batch
@echo off
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

if '%errorlevel%' NEQ '0' (
    echo Requesting administrative privileges...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    set params = %*:"=""
    echo UAC.ShellExecute "cmd.exe", "/c %~s0 %params%", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
    # 실제 작업 시작
```

**이유**: 키움 API와 데이터베이스 작업에 관리자 권한이 필요합니다.

#### 실행 배치 파일

| 파일명 | Python | 내부 명령어 | 용도 |
|--------|--------|-------------|------|
| `stom.bat` | 64-bit | `python` | 통합 모드 (주식+코인) |
| `stom_stock.bat` | 64-bit | `python` | 주식 전용 |
| `stom_coin.bat` | 64-bit | `python` | 암호화폐 전용 |
| `stom_venv.bat` | 64-bit (venv) | `venv_64bit\Scripts\python.exe` | 통합 모드 (가상환경) |
| `stom_venv_stock.bat` | 32/64-bit (venv) | `venv_32bit\Scripts\python32.exe` | 주식 전용 (가상환경) |
| `stom_venv_coin.bat` | 64-bit (venv) | `venv_64bit\Scripts\python.exe` | 암호화폐 전용 (가상환경) |

#### 설치 배치 파일

| 파일명 | 대상 | 내부 명령어 | 실행 내용 |
|--------|------|-------------|-----------|
| `pip_install_64.bat` | 64-bit | `python` | TA-Lib (amd64), numba, websockets, optuna 등 |
| `pip_install_32.bat` | 32-bit | `python` | TA-Lib (win32), pywin32 등 |
| `setup_venv.bat` | 32/64-bit | 직접 경로 | 양쪽 가상환경 자동 생성 + 패키지 설치 |

**명령어 설명**:
- **64-bit Python**: `python` 명령어 사용 (표준 설치, `C:\Python\64\Python3119\python.exe`)
- **32-bit Python**: `python` 명령어 사용 (일부 배치 파일), 또는 `python32` (파일명 변경 후)

### TA-Lib Wheel 파일 차이

키움증권 연동을 위한 기술적 분석 라이브러리:

| 아키텍처 | Wheel 파일 | 위치 |
|----------|-----------|------|
| 64-bit | `TA_Lib-0.4.25-cp311-cp311-win_amd64.whl` | `utility/` |
| 32-bit | `TA_Lib-0.4.27-cp311-cp311-win32.whl` | `utility/` |

**주의**: TA-Lib는 컴파일된 C 확장이므로 아키텍처별로 다른 wheel 파일이 필요합니다.

### 사용 시나리오

#### 시나리오 1: 암호화폐만 트레이딩

```bash
# 64-bit Python만 설치
pip_install_64.bat

# 실행
stom_coin.bat
```

**필요**: 64-bit Python만

#### 시나리오 2: 주식만 트레이딩

```bash
# 32-bit Python 설치 (키움 API)
pip_install_32.bat

# 64-bit Python 설치 (메인 시스템)
pip_install_64.bat

# 실행
stom_stock.bat
```

**필요**: 32-bit + 64-bit Python 모두

#### 시나리오 3: 주식 + 암호화폐 통합

```bash
# 양쪽 Python 설치
pip_install_32.bat
pip_install_64.bat

# 또는 가상환경 자동 설정
setup_venv.bat

# 실행
stom.bat  # 또는 stom_venv.bat
```

**필요**: 32-bit + 64-bit Python 모두

### 프로세스 간 통신

64-bit와 32-bit 프로세스 간 데이터 교환:

1. **큐 기반** (multiprocessing.Queue): 메모리 공유
2. **ZeroMQ**: 네트워크 소켓 기반 IPC
3. **SQLite 데이터베이스**: 영구 저장 + 프로세스 간 공유
4. **파일 시스템**: 임시 파일을 통한 데이터 전달

---

## 기술 스택

### 핵심 기술

| 카테고리 | 기술 |
|----------|------|
| **언어** | Python 3.11 (64-bit) |
| **GUI** | PyQt5, PyQtWebEngine, pyqtgraph |
| **데이터베이스** | SQLite3 |
| **데이터 처리** | NumPy (1.26.4), Pandas (2.0.3), Numba |
| **기술적 분석** | TA-Lib (커스텀 wheel) |
| **최적화** | Optuna, Optuna-Dashboard, CMA-ES |
| **통신** | WebSocket, ZeroMQ (pyzmq) |
| **암호화** | cryptography (Fernet) |
| **알림** | python-telegram-bot (13.15), pyttsx3 |
| **트레이딩 API** | pyupbit, python-binance |
| **시각화** | matplotlib, squarify, pyqtgraph |
| **웹 통신** | BeautifulSoup4, lxml |
| **시스템** | psutil |

### 디자인 패턴

- **전략 패턴 (Strategy Pattern)**: 시장별 전용 전략 엔진
- **옵저버 패턴 (Observer Pattern)**: 큐/WebSocket 실시간 데이터 업데이트
- **팩토리 패턴 (Factory Pattern)**: 시장별 엔진 생성
- **싱글톤 패턴 (Singleton Pattern)**: 설정 및 데이터베이스 매니저
- **템플릿 메서드 패턴 (Template Method)**: 전략 클래스 상속 구조
- **커맨드 패턴 (Command Pattern)**: 큐 기반 프로세스 간 통신

### 성능 최적화

- **멀티프로세스**: Python multiprocessing (15개 프로세스)
- **멀티스레딩**: 논블로킹 UI 업데이트
- **ZeroMQ**: 고성능 메시지 큐
- **NumPy 벡터화**: 빠른 수치 계산
- **인덱싱된 DB 쿼리**: 효율적인 데이터 검색
- **비동기 WebSocket**: 실시간 데이터 스트리밍

---

## 개발 환경

### 개발 도구

```bash
# 코드 라인 수 통계
python utility/total_code_line.py

# 데이터베이스 업데이트
python utility/db_update_day.py
python utility/db_update_back.py

# 백테스팅 실행
python backtester/backtest.py

# 파라미터 최적화
python backtester/optimiz.py

# 유전 알고리즘 최적화
python backtester/optimiz_genetic_algorithm.py
```

**참고**: 명령줄에서는 표준 `python` 명령어를 사용하세요 (64-bit Python이 기본입니다).

### 가상환경 사용 (권장)

```bash
# 가상환경 자동 구축
setup_venv.bat

# 가상환경 활성화 후 실행
stom_venv.bat           # 통합 모드
stom_venv_stock.bat     # 주식 전용
stom_venv_coin.bat      # 암호화폐 전용
```

### 디버깅

- **로그 파일**: `_log/` 디렉토리에 프로세스별 로그 자동 생성
- **텔레그램 알림**: 실시간 이벤트 및 에러 알림
- **데이터베이스 검증**: `utility/database_check.py` 실행
- **성능 모니터링**: UI 내장 성능 대시보드

---

## 주요 명령어

### 설치 및 설정

```bash
# 의존성 설치 (Python 64-bit 필요)
pip_install_64.bat

# 가상환경 구축
setup_venv.bat

# 데이터베이스 무결성 검사
python utility/database_check.py
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

# 유전 알고리즘 최적화
python backtester/optimiz_genetic_algorithm.py

# 데이터베이스 작업
python utility/db_update_day.py
python utility/db_update_back.py
```

---

## 문제 해결

### 일반적인 문제

**관리자 권한 필요**:
- 모든 배치 파일이 자동으로 권한 상승 요청
- Windows UAC 프롬프트 승인 필요

**데이터베이스 잠금**:
- 멀티프로세스 작업 시 동시 접근 확인
- `database_check.py`로 무결성 검사

**API 연결 실패**:
- `setting.db`의 암호화된 인증정보 확인
- 키움 OpenAPI 설치 여부 확인 (`C:/OpenAPI`)
- 네트워크 연결 상태 확인

**메모리 사용량**:
- `psutil` 통합으로 메모리 모니터링
- 대용량 데이터셋 처리 시 주의

### 로그 및 디버깅

- **로그 위치**: `_log/` 디렉토리
- **텔레그램 알림**: 실시간 에러 및 이벤트 알림
- **성능 모니터링**: UI 내장 대시보드

### 지원

- **문서**: [docs/README.md](./docs/README.md)
- **매뉴얼**: [docs/Manual/09_Manual/user_manual.md](./docs/Manual/09_Manual/user_manual.md)
- **가이드**: [CLAUDE.md](./CLAUDE.md) (AI 어시스턴트용 상세 가이드)

---

## 강화된 백테스팅 분석 시스템 (v2.0)

### 개요

2025-12-10 업데이트로 백테스팅 결과 분석 시스템이 대폭 강화되었습니다. 백테스팅 완료 시 **자동으로** 실행되며, 별도의 조작이 필요 없습니다.

### 주요 모듈

```
backtester/
├── back_static.py              # 기존 분석 + 강화 분석 통합
└── back_analysis_enhanced.py   # 강화된 분석 모듈 (NEW)
```

### 새로운 출력 파일

백테스팅 완료 시 다음 파일들이 `_graph/` 폴더에 자동 생성됩니다:

| 파일명 패턴 | 내용 |
|-------------|------|
| `{전략명}_detail.csv` | 거래 상세 기록 (강화 분석 사용 시 강화 파생지표 포함) |
| `{전략명}_filter.csv` | 필터 분석 결과 (강화 분석 사용 시 통계 검정/효과크기 포함) |
| `{전략명}_optimal_thresholds.csv` | 동적 최적 임계값 탐색 결과 |
| `{전략명}_filter_combinations.csv` | 필터 조합 시너지 분석 |
| `{전략명}_filter_stability.csv` | 기간별 필터 안정성 검증 |
| `{전략명}_enhanced.png` | 필터 기능 분석 차트 (16개) |
| `{전략명}_report.txt` | 실행 산출물 리포트(파일/시간/조건/요약) |

### 새로운 파생 지표

#### 거래 품질 지표

| 지표명 | 범위 | 설명 |
|--------|------|------|
| **거래품질점수** | 0-100 | 체결강도, 호가잔량비, 시가총액 등 종합 평가 |
| **위험도점수** | 0-100 | 등락율 급변, 체결강도 하락, 호가 불균형 등 위험 신호 |
| **모멘텀점수** | -30~+30 | 등락율과 체결강도 기반 모멘텀 강도 |
| **리스크조정수익률** | 실수 | 위험 요소를 고려한 조정 수익률 |

#### 변화량 지표

| 지표명 | 산출 공식 | 용도 |
|--------|-----------|------|
| **등락율변화** | 매도등락율 - 매수등락율 | 보유 중 추세 변화 |
| **체결강도변화** | 매도체결강도 - 매수체결강도 | 수급 변화 감지 |
| **거래대금변화율** | 매도거래대금 / 매수거래대금 | 거래량 추세 |

### 결과 해석 가이드

#### 1. 통계적 유의성 해석

```
p-value 해석:
├── p < 0.01  : 매우 유의함 (★★★) - 실전 적용 강력 권장
├── p < 0.05  : 유의함 (★★) - 실전 적용 권장
├── p < 0.10  : 약간 유의함 (★) - 추가 검증 필요
└── p >= 0.10 : 유의하지 않음 - 적용 비권장
```

#### 2. 효과 크기 (Cohen's d) 해석

| Cohen's d | 해석 | 실전 의미 |
|-----------|------|-----------|
| < 0.2 | 무시 | 필터 효과가 거의 없음 |
| 0.2 - 0.5 | 작음 | 약간의 효과, 다른 필터와 조합 권장 |
| 0.5 - 0.8 | 중간 | 의미 있는 효과, 단독 적용 가능 |
| > 0.8 | 큼 | 강력한 효과, 적극 적용 권장 |

#### 3. 필터 안정성 등급

| 등급 | 일관성 점수 | 의미 |
|------|-------------|------|
| **안정** | 70+ | 모든 기간에서 일관되게 효과 발휘 |
| **보통** | 40-70 | 일부 기간에서 효과 변동 |
| **불안정** | < 40 | 기간별로 효과 편차 큼, 과적합 의심 |

#### 4. 필터 조합 시너지

```
시너지 비율 해석:
├── > 20%  : 강한 시너지 (★★★) - 조합 적용 강력 권장
├── > 0%   : 양의 시너지 (★★) - 조합 적용 권장
├── = 0%   : 시너지 없음 - 개별 적용과 동일
└── < 0%   : 음의 시너지 - 조합 비권장 (중복 제외 발생)
```

### 주의사항 ⚠️

#### 과적합(Overfitting) 방지

1. **안정성 등급 확인**: "안정" 등급 필터만 실전 적용
2. **기간별 검증**: `filter_stability.csv`에서 모든 기간 양수인지 확인
3. **효과 크기 확인**: Cohen's d > 0.5 필터 우선 적용
4. **조합 주의**: 3개 이상 필터 조합은 과적합 위험 높음

#### 통계적 해석 시 주의점

1. **표본 크기**: 거래 수가 30개 미만이면 통계 결과 신뢰도 낮음
2. **다중 비교 문제**: 많은 필터 중 일부는 우연히 유의할 수 있음
3. **실전 적용**: p-value와 효과 크기가 모두 좋아야 실전 적용 권장

#### 자동 생성 코드 사용 시

```python
# 자동 생성된 조건 코드 예시
# [등락율] 필터
# - 등락율 25% 이상 제외: 수익개선 150,000원, 제외율 8.5%

# 적용 예시:
# if 기존매수조건
#     and 등락율 < 25
#     매수 = True
```

- 생성된 코드는 **참고용**이며, 직접 검증 후 적용
- 임계값은 데이터에 따라 조정 필요
- 여러 필터 동시 적용 시 제외 비율 누적 확인

### 텔레그램 알림

강화된 분석 결과는 텔레그램으로 자동 전송됩니다:

```
📊 강화된 필터 분석 결과:

[통계적 유의] 등락율 25% 이상 제외: +150,000원 (p=0.012)
[통계적 유의] 체결강도 80 미만 제외: +85,000원 (p=0.034)
[조합추천] 등락율 25% 이상 + 시가총액 500억 미만: 시너지 +45,000원
[안정성] 매수등락율 >= 20: 일관성 82.5점

💡 자동 생성 필터 코드:
총 5개 필터
예상 총 개선: 380,000원
```

### 참고 문서

상세한 기술 문서는 다음을 참조하세요:
- [텔레그램 차트 분석 상세 문서](./docs/Study/SystemAnalysis/Telegram/Telegram_Charts_Analysis.md)
- [백테스팅 가이드라인](./docs/Guideline/Back_Testing_Guideline_Tick.md)

---

## 라이선스

이 프로젝트는 독점 소프트웨어입니다. 무단 복제, 배포, 수정을 금지합니다.

자세한 내용은 [_license.txt](./_license.txt)를 참조하세요.

---

## 기여

### 개발 패턴 및 규칙

전체 개발 가이드라인은 **[CLAUDE.md](./CLAUDE.md)**를 참조하세요.

#### 파일 명명 규칙

- `*_receiver_*.py` - 실시간 데이터 수집
- `*_strategy_*.py` - 트레이딩 로직 및 신호 생성
- `*_trader.py` - 주문 실행 및 포지션 관리
- `backengine_*_*.py` - 시장별 백테스팅 엔진
- `ui_*.py` - UI 구성요소 및 이벤트 핸들러

#### 문서화 표준

- **98.3% 준수율 유지**: 모든 전략은 표준 템플릿 준수
- **조건식 문서**: [Condition_Document_Template_Guideline.md](./docs/Guideline/Condition_Document_Template_Guideline.md) 따름
- **코드 주석**: 한국어 변수명 사용 (현재가, 시가, 고가, 저가 등)

### 기여 프로세스

1. **이슈 등록**: 버그 리포트 또는 기능 제안
2. **브랜치 생성**: `feature/your-feature` 또는 `fix/your-fix`
3. **코드 작성**: 개발 패턴 및 문서화 표준 준수
4. **테스트**: 백테스팅 엔진으로 검증
5. **Pull Request**: 코드 리뷰 요청

---

## 프로젝트 상태

**최종 업데이트**: 2025-12-10

**최근 완료 사항**:
- **v2.0 강화된 백테스팅 분석 시스템** 구현 (`back_analysis_enhanced.py`)
  - 통계적 유의성 검증 (t-test, Cohen's d, 95% 신뢰구간)
  - 동적 최적 임계값 탐색 (백분위 기반)
  - 필터 조합 시너지 분석 (2-3개 조합)
  - ML 기반 특성 중요도 분석 (Decision Tree)
  - 기간별 필터 안정성 검증 (5기간 분할)
  - 조건식 코드 자동 생성
- 텔레그램 차트 분석 상세 문서 작성 (`docs/Study/SystemAnalysis/Telegram/Telegram_Charts_Analysis.md`)
- README.md 강화된 분석 시스템 가이드 추가

**이전 완료 사항**:
- Phase 5: 119/121개 조건 파일 (98.3%) 문서화 준수
- 트레이딩 조건 자동화된 최적화 섹션 생성
- 매뉴얼 문서 코드 참조 검증 (138개 코드 블록)
- 문서 전반 경로 및 명령어 수정

**현재 초점**:
- 강화된 분석 시스템 실전 검증
- 문서-코드 정렬 유지
- 지속적인 전략 최적화
- 성능 벤치마킹 및 개선

---

## 감사의 말

이 프로젝트는 다음 기술과 커뮤니티의 도움으로 개발되었습니다:

- **PyQt5**: 강력한 GUI 프레임워크
- **TA-Lib**: 포괄적인 기술적 분석 라이브러리
- **Optuna**: 효율적인 하이퍼파라미터 최적화
- **키움증권**: 한국 주식시장 API 제공
- **업비트, 바이낸스**: 암호화폐 거래소 API 제공

---

**⚠️ 면책 조항**: 이 소프트웨어는 교육 및 연구 목적으로 제공됩니다. 실제 트레이딩에는 재정적 위험이 수반되므로, 사용자의 책임 하에 사용하시기 바랍니다. 개발자는 트레이딩 손실에 대해 책임지지 않습니다.

---

**🚀 STOM으로 스마트한 트레이딩을 시작하세요!**

자세한 문서는 **[docs/README.md](./docs/README.md)**를 참조하세요.
