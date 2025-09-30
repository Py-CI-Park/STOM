## 목적과 범위 (Version G)

- **최종 목표**: 조건식 변수(윈도우/임계값/조합)의 수익 기여를 정량화하고, 최소 모듈로 빠르게 반복 실험하여 “수익률/샤프 개선”이 재현되는 조합을 도출.
- **핵심 결과물**:
  - `research/` 최소 코드베이스(로더, 레이블, 피처, 백테스터 래퍼, 최적화, 모델, 평가)
  - 조건 파라미터-성과 매핑 및 중요도/해석 리포트
  - 워크포워드 OOS 기준을 통과한 조건식 초안 1~2개
- **범위(필수만)**:
  - DB 로딩(SQLite) → 피처 최소셋 → 레이블(수익>비용 분류) → XGBoost GPU 베이스라인
  - 백테스터 래퍼 연동 + Optuna 탐색(200~500 trials)
  - 워크포워드 3분할 + OOS 1분할 평가, 비용/슬리피지 반영
  - MLflow 기록, 간단 리포트 자동화
- **비범위(초기 제외)**: 복잡한 딥러닝 대회급 튜닝, 강화학습, 실시간 운영 자동화, 초정교 미체결/미끄러짐 모델링

### 성공 기준 (Exit Criteria)
- 워크포워드 평균 Sharpe ≥ 1.0, MDD/Turnover 제약 내에서 OOS 성능 유지(Sharpe ≥ 0.8)
- 동일 설정 재실행 시 ±10% 내 성능 변동(재현성)
- 1시간 내 200+ 트라이얼 최적화 완료(GPU 기준, 병렬화 4+)

### 참조
- [Condition_Survey_ML_DL_Plan.md](mdc:Idea/Condition_Survey_ML_DL_Plan.md)
- [Back_Testing_Guideline_Tick.md](mdc:Guideline/Back_Testing_Guideline_Tick.md)
- [Back_Testing_Guideline_Min.md](mdc:Idea/Back_Testing_Guideline_Min.md)
