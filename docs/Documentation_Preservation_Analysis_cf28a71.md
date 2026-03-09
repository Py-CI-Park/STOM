# STOM 문서 보존 분석 및 폴더별 결론

> 작성일: 2026-03-09
> 기준 커밋: `cf28a7109c7909ce17369e13f3c3a4fc42b3b923`
> 목적: 현재 `docs/` 전체를 우선 보관용으로 커밋하되, 추후 정리/삭제를 위해 폴더별 성격과 보존 우선순위를 기록한다.

---

## 1. 분석 기준

- 현재 로컬 코드베이스는 `cf28a7109c7909ce17369e13f3c3a4fc42b3b923` 기준이다.
- 이번 커밋의 목적은 **즉시 삭제가 아니라 보관용 스냅샷 기록**이다.
- 따라서 이번 문서는 `docs/` 전체를 버리지 않고 남겨 두되, 나중에 어떤 폴더부터 정리할지 판단할 수 있도록 작성한다.
- 판정 기준은 다음 네 가지다.
  - 현재 코드와 직접 연결되는가
  - 조건식/데이터베이스/백테스트 가이드로서 실무 가치가 있는가
  - 연구/아이디어/로그처럼 기록성 문서인가
  - 현재 커밋보다 이후 구조를 전제로 해 오해를 만들 가능성이 있는가

---

## 2. 폴더별 분석 표

| 폴더 | 대략 파일 수 | 성격 | 현재 코드와의 정합성 | 이번 커밋 판단 | 추후 정리 우선순위 | 비고 |
|---|---:|---|---|---|---|---|
| `docs/Guideline/` | 14 | 핵심 가이드라인 | 높음 | 전체 보관 | 낮음 | 조건식, 백테스트, DB 문서의 중심 축 |
| `docs/Condition/` | 다수 | 조건식 본문, 인덱스, 참조자료 | 중간 | 전체 보관 | 중간 | 이번엔 전체 보관, 이후 세부 선별 필요 |
| `docs/Condition/Tick/1_To_be_reviewed/` | 62 | 미검증 틱 전략 초안 | 중간 | 보관 | 높음 | 전략 자산 성격, 가이드 목적만 보면 과다 |
| `docs/Condition/Tick/2_Under_review/` | 12 | 검토 중 핵심 전략 | 높음 | 보관 | 낮음 | 대표 전략 예제로 가치 큼 |
| `docs/Condition/Min/1_To_be_reviewed/` | 45 | 미검증 분봉 전략 초안 | 중간 | 보관 | 높음 | 틱과 동일, 양이 많고 중복 가능성 큼 |
| `docs/Condition/Min/2_Under_review/` | 6 | 검토 중 분봉 전략 | 중간 | 보관 | 중간 | 대표 분봉 예제 선별 가능 |
| `docs/Condition/Min/Idea/` | 15 | 아이디어/실험안 | 낮음 | 보관 | 높음 | 실전 문서보다 아이디어 메모 성격이 강함 |
| `docs/Condition/Idea/Plan_from_GPT5/` | 14 | AI 생성 설계/계획 | 낮음 | 보관 | 높음 | 현재 코드보다 확장된 구상 포함 |
| `docs/Condition/Idea/Plan_from_claude_opus/` | 12 | AI 생성 설계/계획 | 낮음 | 보관 | 높음 | 가이드 중복 및 미래 구조 전제 다수 |
| `docs/Condition/Reference/PyTrader/` | 7 | 외부 조건식 참고자료 | 중간 | 보관 | 낮음 | 비교 기준과 아이디어 소스로 유용 |
| `docs/Condition/Reference/YouTube/` | 6 | 영상 기반 참고 메모 | 낮음 | 보관 | 높음 | 참고 메모 성격, 운영 문서 우선도 낮음 |
| `docs/Manual/` | 18 | 시스템 매뉴얼 | 혼합 | 보관 | 중간 | 일부는 유용하나 일부는 미래 구조 설명 |
| `docs/learning/` | 13 | 입문/학습용 문서 | 중간 | 보관 | 중간 | 요약본으로 유용하나 핵심 기준서는 아님 |
| `docs/Study/` | 21 | 연구/분석/검증 문서 | 낮음 | 보관 | 높음 | 미래 브랜치 구조 전제 문서 다수 포함 |
| `docs/Plan/` | 1 | 구현 계획서 | 낮음 | 보관 | 높음 | 기록용 가치는 있으나 운영 기준 문서는 아님 |
| `docs/update_log/` | 3 | 변경 이력 | 낮음 | 보관 | 높음 | 현재 커밋 이후 변경을 설명하는 문서 |
| `docs/Error_Log/` | 1 | 실행 로그 | 낮음 | 보관 | 매우 높음 | 보관 목적 외 실무 문서 가치는 거의 없음 |
| `docs/CodeReview/` | 1 | 백테스터 구조 분석 | 높음 | 보관 | 낮음 | 현재 `backtester/` 이해에 직접 도움 |
| `docs/가상환경구축연구/` | 1 | 환경 구축 연구 | 중간 | 보관 | 중간 | 보조 참고자료로는 가능하나 핵심은 아님 |

---

## 3. 폴더별 결론

### 3.1 강력 보관

다음 폴더는 현재 코드 기준에서도 의미가 분명하고, 추후 문서 정리 시에도 마지막까지 남겨둘 가능성이 높다.

- `docs/Guideline/`
- `docs/CodeReview/`
- `docs/Condition/Reference/PyTrader/`
- `docs/Condition/Tick/2_Under_review/`의 대표 전략 문서

핵심 이유:

- 조건식 작성 기준, 백테스트 사용법, 데이터베이스 구조 설명이 모두 여기에 모여 있다.
- 조건식 실제 작성/개선 시 재사용 가치가 높다.
- 현재 코드 구조를 이해하는 데 직접적이다.

### 3.2 선별 보관

다음 폴더는 전부 버릴 필요는 없지만, 후속 정리 시 핵심 파일만 남겨도 된다.

- `docs/Condition/`
- `docs/Manual/`
- `docs/learning/`
- `docs/Condition/Min/2_Under_review/`
- `docs/가상환경구축연구/`

핵심 이유:

- 유용한 설명과 예제가 있으나, 일부는 현재 코드보다 이후 구조를 설명한다.
- 요약/입문 문서가 기준 문서를 반복 설명하는 경우가 있다.
- 전략 문서 전체를 다 유지하지 않아도 대표 예제만으로 활용 가능하다.

### 3.3 추후 정리 우선 대상

다음 폴더는 이번에는 보관하되, 추후 삭제 후보를 검토할 때 가장 먼저 다시 볼 대상이다.

- `docs/Condition/Tick/1_To_be_reviewed/`
- `docs/Condition/Min/1_To_be_reviewed/`
- `docs/Condition/Min/Idea/`
- `docs/Condition/Idea/Plan_from_GPT5/`
- `docs/Condition/Idea/Plan_from_claude_opus/`
- `docs/Condition/Reference/YouTube/`
- `docs/Study/`
- `docs/Plan/`
- `docs/update_log/`
- `docs/Error_Log/`

핵심 이유:

- 대량의 미검증 전략 초안 또는 아이디어 메모다.
- 미래 브랜치 전용 구조를 전제한 문서가 섞여 있다.
- 연구/로그/변경이력 성격이라 운영 문서와 분리하는 편이 낫다.

---

## 4. 현재 커밋 시점의 보관 원칙

이번 커밋은 `docs/`를 정제된 최종판으로 확정하는 커밋이 아니다.

이번 커밋의 의미는 다음과 같다.

1. 원격 최신에서 가져온 `docs/` 전체를 현재 로컬 기준 브랜치에 보관한다.
2. 어떤 폴더가 핵심 기준 문서인지, 어떤 폴더가 후속 정리 대상인지 문서로 남긴다.
3. 이후 삭제/정리 작업은 이 문서를 기준으로 점진적으로 수행한다.

즉, 이번 커밋은 **보존용 아카이브 + 분류 기준 문서화** 커밋이다.

---

## 5. 후속 작업 제안

추후 실제 삭제 작업은 아래 순서가 가장 안전하다.

1. `docs/Error_Log/`, `docs/Plan/`, `docs/update_log/`
2. `docs/Condition/Idea/`, `docs/Condition/Min/Idea/`, `docs/Condition/Reference/YouTube/`
3. `docs/Study/`
4. `docs/Condition/Tick/1_To_be_reviewed/`, `docs/Condition/Min/1_To_be_reviewed/`
5. `docs/Manual/`, `docs/learning/`의 중복/미래구조 문서 선별 정리

이 순서는 핵심 가이드라인과 대표 전략 예제를 최대한 늦게 건드리도록 구성했다.
