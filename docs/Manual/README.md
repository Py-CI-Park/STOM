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

### [04. API 연동 분석](04_API/api_integration.md)

### [05. UI/UX 분석](05_UI_UX/ui_ux_analysis.md)

### [06. 데이터 관리](06_Data/data_management.md)

### [07. 트레이딩 엔진](07_Trading/trading_engine.md)

### [08. 백테스팅 시스템](08_Backtesting/backtesting_system.md)

### [09. 사용자 매뉴얼](09_Manual/user_manual.md)

### [10. 결론](10_Conclusion/conclusion.md)

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

---

**작성일**: 2025-01-01
**최종 수정일**: 2025-11-17
**버전**: v1.1