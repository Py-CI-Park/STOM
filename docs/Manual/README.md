# STOM (System Trading Optimization Manager) 프로젝트 분석 보고서

## 📋 목차

### [01. 프로젝트 개요](01_Overview/project_overview.md)
- 프로젝트 소개
- 주요 기능
- 기술 스택
- 라이센스 정보

### [02. 시스템 아키텍처](02_Architecture/system_architecture.md)
- 전체 시스템 구조
- 모듈 간 의존성
- 데이터 플로우
- 프로세스 아키텍처

### [03. 모듈 분석](03_Modules/modules_analysis.md)
- [주식 모듈 (stock/)](03_Modules/stock_module.md)
- [암호화폐 모듈 (coin/)](03_Modules/coin_module.md)
- [UI 모듈 (ui/)](03_Modules/ui_module.md)
- [유틸리티 모듈 (utility/)](03_Modules/utility_module.md)
- [백테스터 모듈 (backtester/)](03_Modules/backtester_module.md)

### [04. API 연동 분석](04_APIs/api_integration.md)
- [키움증권 OpenAPI](04_APIs/kiwoom_api.md)
- [업비트 API](04_APIs/upbit_api.md)
- [바이낸스 API](04_APIs/binance_api.md)
- [실시간 데이터 처리](04_APIs/realtime_data.md)

### [05. UI/UX 분석](05_UI_Analysis/ui_analysis.md)
- [메인 윈도우 구조](05_UI_Analysis/main_window.md)
- [차트 시스템](05_UI_Analysis/chart_system.md)
- [사용자 인터페이스 플로우](05_UI_Analysis/ui_flow.md)
- [이벤트 처리](05_UI_Analysis/event_handling.md)

### [06. 데이터 관리](06_Data_Management/data_management.md)
- [데이터베이스 구조](06_Data_Management/database_structure.md)
- [데이터 수집 및 저장](06_Data_Management/data_collection.md)
- [성능 최적화](06_Data_Management/performance_optimization.md)

### [07. 트레이딩 엔진](07_Trading_Engine/trading_engine.md)
- [전략 실행 로직](07_Trading_Engine/strategy_execution.md)
- [주문 관리 시스템](07_Trading_Engine/order_management.md)
- [리스크 관리](07_Trading_Engine/risk_management.md)
- [포지션 관리](07_Trading_Engine/position_management.md)

### [08. 백테스팅 시스템](08_Backtesting/backtesting_system.md)
- [백테스팅 엔진](08_Backtesting/backtest_engine.md)
- [최적화 시스템](08_Backtesting/optimization_system.md)
- [성과 분석](08_Backtesting/performance_analysis.md)

### [09. 사용자 매뉴얼](09_Manual/user_manual.md)
- [설치 및 설정](09_Manual/installation_setup.md)
- [기본 사용법](09_Manual/basic_usage.md)
- [전략 개발 가이드](09_Manual/strategy_development.md)
- [트러블슈팅](09_Manual/troubleshooting.md)

### [10. 부록](10_Appendix/appendix.md)
- [코드 구조 다이어그램](10_Appendix/code_diagrams.md)
- [API 레퍼런스](10_Appendix/api_reference.md)
- [용어집](10_Appendix/glossary.md)
- [참고 자료](10_Appendix/references.md)

---

## 📊 프로젝트 통계

- **총 코드 라인 수**: 약 50,000+ 라인
- **주요 언어**: Python 3.x
- **GUI 프레임워크**: PyQt5
- **지원 거래소**: 키움증권, 업비트, 바이낸스
- **데이터베이스**: SQLite
- **실시간 처리**: WebSocket, ZeroMQ

## 🎯 분석 목적

이 분석 보고서는 STOM 프로젝트의 전체적인 구조와 작동 원리를 이해하고, 시스템 트레이딩 플랫폼의 구현 방법을 학습하기 위해 작성되었습니다.

## 📝 분석 방법론

1. **정적 코드 분석**: 소스코드 구조 및 의존성 분석
2. **동적 분석**: 실행 플로우 및 데이터 흐름 분석
3. **아키텍처 분석**: 시스템 설계 패턴 및 구조 분석
4. **성능 분석**: 병목 지점 및 최적화 방안 분석

---

*본 분석 보고서는 파이퀀트 강좌 수강생을 위한 학습 자료로 작성되었습니다.* 