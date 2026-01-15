# ICOS 구현 실행 계획 v2 (개정판)

> **작성일**: 2026-01-15
> **개정 이유**: 기존 문서의 분석 오류 수정 및 실제 구현 상태 반영
> **참조 문서**: 20260115_ICOS_Pipeline_Analysis_and_Integration_Plan.md

---

## 1. 기존 문서의 오류 및 수정 사항

### 1.1 핵심 오류 수정

| 항목 | 기존 문서 기술 | 실제 확인 결과 |
|-----|--------------|--------------|
| `_execute_backtest()` | 빈 DataFrame 반환 (스켈레톤) | **SyncBacktestRunner 정상 호출됨** |
| `backtest_sync.py` | 미구현 | **680줄 완전 구현됨** |
| `SyncBacktestRunner` | 구현 필요 | **핵심 메서드 모두 구현됨** |

### 1.2 SyncBacktestRunner 실제 구현 현황 (680줄)

```
backtester/iterative_optimizer/backtest_sync.py
├── SyncBacktestRunner 클래스
│   ├── __init__() - 초기화 (52-96줄)
│   ├── run() - 백테스트 실행 (194-334줄) ✅ 구현완료
│   ├── _load_period_data() - 데이터 로드 (111-166줄) ✅ 구현완료
│   ├── _run_backengine_sync() - 백엔진 동기 실행 (336-405줄) ✅ 구현완료
│   ├── _strategy() - 전략 실행 (415-556줄) ✅ 구현완료
│   ├── Buy() - 매수 실행 (558-571줄) ✅ 구현완료
│   ├── Sell() - 매도 실행 (573-576줄) ✅ 구현완료
│   └── _calculation_eyun() - 수익 계산 (578-616줄) ✅ 구현완료
```

### 1.3 runner.py의 실제 연동 상태

```python
# runner.py:631-654 (실제 코드)
def _execute_backtest(self, buystg: str, sellstg: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """백테스트 실행. SyncBacktestRunner를 사용하여 동기식 백테스트를 실행합니다."""

    runner = SyncBacktestRunner(
        ui_gubun=ui_gubun,
        timeframe=timeframe,
        dict_cn=params.get('dict_cn', {}),
        verbose=self.config.verbose,
    )

    result = runner.run(buystg, sellstg, params)  # ← 실제로 호출되고 있음!
    return result
```

---

## 2. ICOS가 작동하지 않는 실제 원인

### 2.1 원인 분석 (수정된 결론)

**기존 분석**: `_execute_backtest()`가 스켈레톤이라서 ICOS가 작동 안 함
**실제 원인**: SyncBacktestRunner의 **지표 함수 부족**으로 조건식 실행 실패

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ★ 실제 문제점 ★                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SyncBacktestRunner._strategy() 지표 함수 현황                             │
│                                                                             │
│  BackEngine (44개+):              SyncBacktestRunner (15개):               │
│  ─────────────────                ──────────────────────                   │
│  ✓ 현재가N, 시가N, 고가N, 저가N    ✓ 현재가N, 시가N, 고가N, 저가N          │
│  ✓ 등락율N, 당일거래대금N         ✓ 등락율N, 당일거래대금N                 │
│  ✓ 체결강도N                      ✓ 체결강도N                              │
│  ✓ 이동평균, 최고현재가, 최저현재가  ✓ 이동평균, 최고현재가, 최저현재가    │
│  ✓ 등락율각도, 당일거래대금각도   ✓ 등락율각도, 당일거래대금각도          │
│                                                                             │
│  ✓ 거래대금증감N                  ✗ 미구현                                 │
│  ✓ 전일비N                        ✗ 미구현                                 │
│  ✓ 회전율N                        ✗ 미구현                                 │
│  ✓ 시가총액N                      ✗ 미구현                                 │
│  ✓ 거래량N                        ✗ 미구현                                 │
│  ✓ 매수호가총잔량N                ✗ 미구현                                 │
│  ✓ 매도호가총잔량N                ✗ 미구현                                 │
│  ✓ 호가잔량비율N                  ✗ 미구현                                 │
│  ✓ 외국인보유율N                  ✗ 미구현                                 │
│  ✓ 매도호가1~5                    ✗ 1단계만 구현                           │
│  ✓ 매수호가1~5                    ✗ 1단계만 구현                           │
│  ✓ 매도잔량1~5                    ✗ 1단계만 구현                           │
│  ✓ 매수잔량1~5                    ✗ 1단계만 구현                           │
│  ... (30개+ 추가 지표)            ✗ 미구현                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 영향 체인 (수정됨)

```
사용자 조건식에 미구현 지표 포함 (예: 거래대금증감N, 전일비N)
      │
      ▼
SyncBacktestRunner._strategy() 실행 중 NameError 발생
      │
      ▼
try-except에서 조용히 무시됨 (backtest_sync.py:548-550)
      │
      ▼
매수 조건이 항상 실패 → 거래 0건 → 빈 결과
      │
      ▼
★ ICOS가 빈 결과로 동작 → 의미 있는 개선 불가 ★
```

### 2.3 증거: 현재 try-except 구조

```python
# backtest_sync.py:544-556
if not 보유중:
    # 매수 조건 실행
    if 관심종목:
        try:
            exec(self.buystg)  # ← 여기서 NameError 발생 가능
        except:
            pass  # ← 예외 무시! 문제의 원인
else:
    # 매도 조건 실행
    try:
        exec(self.sellstg)
    except:
        pass  # ← 예외 무시!
```

---

## 3. 수정된 해결 방안

### 3.1 옵션 A: SyncBacktestRunner 지표 함수 완성 (권장)

**소요 시간**: 1-2일
**장점**: 기존 구현 활용, 점진적 개선 가능
**단점**: BackEngine과 동기화 유지 필요

```
구현 작업:
────────────────────────────────────────────────────────────────

1. 누락된 지표 함수 추가 (30개+)
   - 거래대금증감N, 전일비N, 회전율N, 시가총액N
   - 거래량N, 호가 관련 함수들
   - 기관/외국인/개인 관련 함수들

2. 5단계 호가 데이터 지원
   - 매도호가1~5, 매수호가1~5
   - 매도잔량1~5, 매수잔량1~5

3. 예외 처리 개선
   - try-except에서 예외 로깅 추가
   - 디버그 모드에서 상세 에러 표시
```

### 3.2 옵션 B: BackEngine CodeLoop 직접 호출

**소요 시간**: 2-3일
**장점**: 완전한 지표 호환성
**단점**: 멀티프로세스 우회 필요, 복잡성 증가

```
구현 작업:
────────────────────────────────────────────────────────────────

1. BackEngine 단일 인스턴스 생성
2. CodeLoop 직접 호출 래퍼 구현
3. 큐 통신 우회 로직 구현
```

### 3.3 옵션 C: 조건식 단순화 (빠른 검증용)

**소요 시간**: 0.5일
**장점**: 즉시 테스트 가능
**단점**: 일부 조건식만 지원

```
구현 작업:
────────────────────────────────────────────────────────────────

1. SyncBacktestRunner 지원 지표 목록 문서화
2. ICOS 테스트용 단순 조건식 준비
3. 예외 발생 시 지원 지표 안내 메시지 추가
```

---

## 4. 권장 해결 방안: 옵션 A (SyncBacktestRunner 완성)

### 4.1 이유

1. **기존 구현 활용**: 이미 680줄이 구현되어 있으며, 핵심 로직 완성됨
2. **명확한 범위**: 누락된 지표 함수만 추가하면 됨
3. **유지보수 용이**: BackEngine과 독립적, 단일 파일에서 관리
4. **테스트 용이**: 단일 프로세스이므로 디버깅 쉬움

### 4.2 구현 가이드

```python
# backtest_sync.py 수정 사항

def _strategy(self) -> None:
    """전략 실행."""

    # === 기존 함수들 (유지) ===
    def 현재가N(pre): ...
    def 시가N(pre): ...
    # ... (15개)

    # === 추가할 함수들 ===

    # 1. 거래량/거래대금 관련
    def 거래대금증감N(pre):
        """전틱 대비 거래대금 증감."""
        return Parameter_Previous(8, pre)  # 컬럼 인덱스 확인 필요

    def 전일비N(pre):
        """전일 대비 비율."""
        return Parameter_Previous(9, pre)

    def 회전율N(pre):
        """회전율."""
        return Parameter_Previous(10, pre)

    # 2. 호가 관련 (5단계)
    def 매도호가N(level, pre=0):
        """N단계 매도호가. level: 1~5"""
        col = 27 + (level - 1) * 2  # 컬럼 인덱스 계산
        return Parameter_Previous(col, pre)

    def 매수호가N(level, pre=0):
        """N단계 매수호가. level: 1~5"""
        col = 28 + (level - 1) * 2
        return Parameter_Previous(col, pre)

    # 3. 기관/외국인 관련
    def 외국인보유율N(pre):
        return Parameter_Previous(45, pre)

    # ... (계속)
```

### 4.3 예외 처리 개선

```python
# 기존 (문제):
try:
    exec(self.buystg)
except:
    pass  # ← 모든 예외 무시

# 개선:
try:
    exec(self.buystg)
except NameError as e:
    # 미지원 지표 사용 감지
    self._log(f"[경고] 미지원 지표 사용: {e}")
    if self.verbose:
        print(f"[SyncBacktest] 미지원 지표: {e}")
except Exception as e:
    self._log(f"[오류] 조건식 실행 실패: {e}")
    if self.verbose:
        print_exc()
```

---

## 5. 구현 체크리스트

### 5.1 Phase 1: 지표 함수 추가 (1일)

- [ ] BackEngine의 지표 함수 목록 추출
- [ ] SyncBacktestRunner에 누락된 함수 추가
- [ ] 컬럼 인덱스 매핑 검증
- [ ] 단위 테스트 작성

### 5.2 Phase 2: 호가 데이터 완성 (0.5일)

- [ ] 5단계 매도호가/매수호가 함수
- [ ] 5단계 매도잔량/매수잔량 함수
- [ ] 호가잔량비율 계산 함수

### 5.3 Phase 3: 예외 처리 개선 (0.5일)

- [ ] NameError 감지 및 로깅
- [ ] 지원 지표 목록 안내 메시지
- [ ] verbose 모드 상세 출력

### 5.4 Phase 4: 통합 테스트 (0.5일)

- [ ] 기본 조건식 ICOS 테스트
- [ ] 복잡 조건식 ICOS 테스트
- [ ] BackEngine 결과와 비교 검증

---

## 6. 추가 발견 사항

### 6.1 UI 연동은 정상 구현됨

```
ui/ui_button_clicked_sd.py:342-344
────────────────────────────────────────────────
# ICOS 모드 - 위에서 이미 확인된 icos_enabled 사용
if icos_enabled:
    _run_icos_backtest(ui, bt_gubun, buystg, sellstg, ...)
    return
```

**결론**: UI → ICOS 연동은 문제없음. 백테스트 버튼 클릭 시 `_run_icos_backtest()` 정상 호출됨.

### 6.2 ICOS 프로세스 실행 흐름

```
Alt+I → ICOS 활성화 체크 → 저장
     │
     ▼
백테스트 버튼 클릭 → _check_icos_enabled() → True
     │
     ▼
_run_icos_backtest() → ICOS 프로세스 시작
     │
     ▼
_run_icos_process() → IterativeOptimizer 실행
     │
     ▼
runner.run() → _execute_backtest() → SyncBacktestRunner.run()
     │
     ▼
★ 여기서 지표 함수 부족으로 거래 0건 발생 ★
```

---

## 7. 성공 기준 (수정됨)

### 7.1 기능적 기준

- [ ] 기본 지표만 사용하는 조건식으로 ICOS 정상 실행
- [ ] 거래가 1건 이상 발생하는 것 확인
- [ ] 반복 사이클에서 조건식 개선 관찰
- [ ] 모든 BackEngine 지표가 SyncBacktestRunner에서 지원됨

### 7.2 품질 기준

- [ ] 동일 조건식에서 BackEngine과 SyncBacktestRunner 결과 비교
- [ ] 오차율 5% 이내 (허용 오차: 부동소수점 차이)
- [ ] 예외 발생 시 명확한 에러 메시지 출력

---

## 8. 즉시 실행 가능한 검증 방법

### 8.1 현재 상태에서 ICOS 테스트 (지원 지표만 사용)

```python
# 테스트용 단순 조건식 (SyncBacktestRunner 지원 지표만)
test_buystg = """
# 현재가가 이동평균보다 높으면 매수
if 현재가N(0) > 이동평균(10):
    if 등락율N(0) > 1.0:
        매수 = True
"""

test_sellstg = """
# 수익률 2% 이상이면 매도
if 수익률 >= 2.0:
    매도 = True
    Sell(vturn, vkey, 1)
"""
```

### 8.2 디버그 모드 활성화

```python
# icos_analysis_config.json 수정
{
    "icos": {
        "enabled": true,
        "verbose": true  # 상세 로그 활성화
    }
}
```

---

**문서 개정 완료**: 2026-01-15
**개정 사유**: 실제 코드 분석 결과 반영, 오류 수정
**작성자**: Claude Code Assistant
**브랜치**: feature/iterative-condition-optimizer
