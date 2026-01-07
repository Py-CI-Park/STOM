# exec() → 함수 생성 방식 전환 설계 문서

**작성일**: 2026-01-07
**상태**: 설계 단계 (장기 과제)
**우선순위**: 🟡 Medium

---

## 1. 현재 아키텍처 문제점

### 1.1 exec() 기반 실행의 한계

현재 백테스팅 엔진은 매수/매도 조건식을 `exec()`로 실행합니다:

```python
# backengine_kiwoom_tick.py L691
exec(self.buystg)
```

**문제점**:

| 문제 | 설명 | 영향도 |
|------|------|--------|
| **스코프 제한** | `locals()`가 읽기 전용일 수 있음 | 🔴 High |
| **디버깅 어려움** | 스택 트레이스가 불명확 | 🟠 Medium |
| **성능 오버헤드** | 매 틱/분봉마다 파싱 + 컴파일 | 🟠 Medium |
| **보안 위험** | 임의 코드 실행 가능 | 🟡 Low (내부 사용) |
| **IDE 지원 부재** | 자동완성, 타입 검사 불가 | 🟡 Low |

### 1.2 변수 스코프 이슈 상세

```python
def Strategy(self):
    # 로컬 변수 정의
    현재가, 시가, ... = self.arry_data[self.indexn, 1:45]
    
    # 함수 정의 (로컬 스코프)
    def 당일거래대금N(pre):
        return Parameter_Previous(6, pre)
    
    # exec() 실행 - locals()는 dict의 스냅샷
    exec(self.buystg, globals(), locals())
    
    # 문제: exec() 내에서 정의된 변수가 외부에서 접근 불가할 수 있음
    # Python 구현에 따라 다름 (CPython vs PyPy)
```

---

## 2. 목표 아키텍처

### 2.1 함수 생성 방식

조건식 문자열을 런타임에 함수로 컴파일하여 재사용:

```python
# 제안된 아키텍처
class CompiledStrategy:
    def __init__(self, buystg: str, sellstg: str):
        self._buy_func = self._compile_condition(buystg, 'buy')
        self._sell_func = self._compile_condition(sellstg, 'sell')
    
    def _compile_condition(self, code: str, name: str) -> callable:
        """조건식을 함수로 컴파일"""
        func_name = f"_condition_{name}"
        
        # 함수 정의 코드 생성
        func_code = f'''
def {func_name}(ctx):
    # 변수 언패킹 (컨텍스트에서)
    현재가 = ctx.현재가
    시가 = ctx.시가
    등락율 = ctx.등락율
    # ... (필요한 모든 변수)
    
    # 헬퍼 함수
    def 당일거래대금N(pre):
        return ctx.Parameter_Previous(6, pre)
    
    # 사용자 조건식
    매수 = True
{_indent(code, 4)}
    return 매수
'''
        
        # 컴파일 및 함수 추출
        local_ns = {}
        exec(func_code, {}, local_ns)
        return local_ns[func_name]
    
    def evaluate_buy(self, context) -> bool:
        return self._buy_func(context)
    
    def evaluate_sell(self, context) -> bool:
        return self._sell_func(context)
```

### 2.2 컨텍스트 객체

```python
@dataclass
class StrategyContext:
    """전략 실행 컨텍스트"""
    # 기본 변수
    현재가: float
    시가: float
    고가: float
    저가: float
    등락율: float
    체결강도: float
    # ... (93개 이상 변수)
    
    # 헬퍼 함수 참조
    Parameter_Previous: callable
    Parameter_PreviousN: callable
    # ...
    
    @classmethod
    def from_array(cls, array: np.ndarray, helper_funcs: dict) -> 'StrategyContext':
        """배열에서 컨텍스트 생성"""
        return cls(
            현재가=array[0],
            시가=array[1],
            # ...
            **helper_funcs
        )
```

---

## 3. 마이그레이션 전략

### 3.1 단계별 접근

| 단계 | 내용 | 예상 기간 |
|------|------|-----------|
| **Phase 1** | CompiledStrategy 클래스 프로토타입 | 1주 |
| **Phase 2** | 단일 엔진(kiwoom_tick)에 적용 | 1주 |
| **Phase 3** | 성능 벤치마크 및 버그 수정 | 1주 |
| **Phase 4** | 전체 엔진에 확대 적용 | 2주 |
| **Phase 5** | 기존 exec() 코드 제거 | 1주 |

### 3.2 하위 호환성 유지

```python
class BackEngine:
    def __init__(self, ...):
        self.use_compiled_strategy = False  # 플래그로 전환
    
    def execute_condition(self, code: str, context: dict):
        if self.use_compiled_strategy:
            return self.compiled_strategy.evaluate(context)
        else:
            # 기존 exec() 방식 (폴백)
            exec(code, globals(), context)
            return context.get('매수', False)
```

---

## 4. 예상 이점

### 4.1 성능 개선

| 항목 | exec() 방식 | 함수 방식 | 개선율 |
|------|-------------|-----------|--------|
| 첫 실행 | ~1ms | ~10ms (컴파일) | -900% |
| 반복 실행 | ~0.5ms | ~0.05ms | +900% |
| 1만 틱 | ~5초 | ~0.5초 | +900% |

### 4.2 개발 경험 개선

- **디버깅**: 명확한 스택 트레이스
- **테스팅**: 함수 단위 유닛 테스트 가능
- **IDE 지원**: 타입 힌트, 자동완성
- **코드 리뷰**: 생성된 함수 코드 검토 가능

---

## 5. 위험 요소 및 대응

### 5.1 위험 요소

| 위험 | 확률 | 영향 | 대응 |
|------|------|------|------|
| 기존 조건식 호환성 | 🟠 중 | 🔴 높음 | 폴백 메커니즘 유지 |
| 성능 회귀 | 🟡 낮음 | 🟠 중 | 벤치마크 자동화 |
| 변수 스코프 차이 | 🟠 중 | 🟠 중 | 포괄적 테스트 케이스 |

### 5.2 롤백 전략

```python
# 설정 기반 전환
STRATEGY_EXECUTION_MODE = os.getenv('STRATEGY_MODE', 'exec')  # 'exec' | 'compiled'

if STRATEGY_EXECUTION_MODE == 'exec':
    # 기존 방식
    exec(buystg)
else:
    # 새로운 방식
    result = compiled_strategy.evaluate_buy(context)
```

---

## 6. 구현 세부사항

### 6.1 변수 매핑 자동화

```python
# utility/strategy_variables.py
STRATEGY_VARIABLES = {
    # (배열 인덱스, 타입, 설명)
    '현재가': (0, float, '현재가'),
    '시가': (1, float, '시가'),
    '고가': (2, float, '고가'),
    '저가': (3, float, '저가'),
    # ... 93개 이상
}

def generate_context_class():
    """변수 정의에서 컨텍스트 클래스 자동 생성"""
    fields = []
    for name, (idx, typ, desc) in STRATEGY_VARIABLES.items():
        fields.append(f"    {name}: {typ.__name__}  # {desc}")
    
    return f'''
@dataclass
class StrategyContext:
{chr(10).join(fields)}
'''
```

### 6.2 조건식 파싱 및 검증

```python
import ast

def validate_condition_code(code: str) -> List[str]:
    """조건식 코드의 안전성 검증"""
    errors = []
    
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        errors.append(f"구문 오류: {e}")
        return errors
    
    # 위험한 호출 검사
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ('exec', 'eval', 'compile', '__import__'):
                    errors.append(f"위험한 함수 호출: {node.func.id}")
        
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            errors.append(f"import 문 사용 금지")
    
    return errors
```

---

## 7. 테스트 전략

### 7.1 호환성 테스트

```python
def test_exec_vs_compiled_compatibility():
    """exec()와 compiled 방식의 결과 일치 검증"""
    
    test_conditions = [
        "매수 = 등락율 > 5 and 체결강도 > 100",
        "매수 = 시가총액 >= 1000 and 시분초 >= 90000 and 시분초 < 100000",
        # ... 실제 조건식 샘플
    ]
    
    for code in test_conditions:
        context = create_test_context()
        
        # exec() 방식
        exec_result = execute_with_exec(code, context)
        
        # compiled 방식
        compiled_result = execute_with_compiled(code, context)
        
        assert exec_result == compiled_result, f"불일치: {code}"
```

### 7.2 성능 벤치마크

```python
def benchmark_execution_modes():
    """실행 모드별 성능 비교"""
    import timeit
    
    code = "매수 = 등락율 > 5 and 체결강도 > 100"
    context = create_test_context()
    
    # exec() 방식
    exec_time = timeit.timeit(
        lambda: execute_with_exec(code, context),
        number=10000
    )
    
    # compiled 방식 (초기 컴파일 후)
    compiled_func = compile_condition(code)
    compiled_time = timeit.timeit(
        lambda: compiled_func(context),
        number=10000
    )
    
    print(f"exec(): {exec_time:.4f}s")
    print(f"compiled: {compiled_time:.4f}s")
    print(f"개선율: {(exec_time / compiled_time - 1) * 100:.1f}%")
```

---

## 8. 일정 및 마일스톤

| 마일스톤 | 완료 기준 | 예상 날짜 |
|----------|-----------|-----------|
| **M1: 설계 완료** | 본 문서 리뷰 완료 | 2026-01-14 |
| **M2: 프로토타입** | CompiledStrategy 기본 동작 | 2026-01-21 |
| **M3: 단일 엔진 적용** | kiwoom_tick에서 동작 | 2026-01-28 |
| **M4: 벤치마크 통과** | 성능 목표 달성 | 2026-02-04 |
| **M5: 전체 적용** | 모든 엔진 마이그레이션 | 2026-02-18 |

---

## 9. 참고 자료

- [Python exec() 문서](https://docs.python.org/3/library/functions.html#exec)
- [AST 모듈](https://docs.python.org/3/library/ast.html)
- `backtester/backengine_kiwoom_tick.py` - 현재 구현
- `docs/Study/20260107_Enhanced_Backtesting_System_Complete_Analysis.md` - 시스템 분석

---

**문서 작성자**: AI Assistant
**최종 업데이트**: 2026-01-07
