# STOM 문서-코드 일치성 검증 가이드

## 📖 개요

이 가이드는 STOM 프로젝트의 매뉴얼 문서(`docs/Manual/`)가 실제 소스코드와 일치하도록 유지하기 위한 가이드입니다.

**작성일**: 2025-11-26
**최종 검증일**: 2025-11-26

---

## ✅ 검증 체크리스트

### 1. 파일 경로 및 존재 여부

- [ ] 문서에서 언급된 모든 파일 경로가 실제로 존재하는지 확인
- [ ] 디렉토리 구조가 실제와 일치하는지 확인
- [ ] 프로젝트 루트 경로가 올바른지 확인 (`STOM/`, `STOM_V1/` 아님)

**검증 방법**:
```bash
# 파일 존재 여부 확인
ls /home/user/STOM/stock/kiwoom.py

# 디렉토리 구조 확인
find /home/user/STOM -type d -maxdepth 2

# 특정 패턴의 파일 검색
find /home/user/STOM/coin -name "*.py" -type f
```

### 2. 클래스 및 메서드명

- [ ] 클래스 이름이 실제 코드와 일치하는지 확인
- [ ] 메서드 시그니처(파라미터, 반환값)가 정확한지 확인
- [ ] 상속 관계가 올바른지 확인 (예: Kiwoom은 Composition 패턴 사용)

**검증 방법**:
```bash
# 클래스 정의 찾기
grep -n "^class Kiwoom" /home/user/STOM/stock/kiwoom.py

# 메서드 정의 찾기
grep -n "def CommConnect" /home/user/STOM/stock/kiwoom.py
```

### 3. 코드 라인 번호 참조

- [ ] `**소스**: 파일명:라인번호` 형식의 참조가 정확한지 확인
- [ ] 라인 번호가 실제 코드 위치와 일치하는지 확인

**검증 방법**:
```bash
# 특정 라인 확인
sed -n '36,70p' /home/user/STOM/stock/kiwoom.py

# 또는 cat -n으로 확인
cat -n /home/user/STOM/stock/kiwoom.py | sed -n '36,70p'
```

### 4. 코드 스니펫 정확성

- [ ] 코드 예제가 실제 코드에서 추출되었는지 확인
- [ ] "예제 코드"로 표시된 부분이 실제 구현과 유사한지 확인
- [ ] 중요한 파라미터나 상수가 정확한지 확인

**검증 방법**:
```bash
# 특정 코드 패턴 검색
grep -A 10 "def OnReceiveRealData" /home/user/STOM/stock/kiwoom_receiver_tick.py
```

### 5. 설정 및 상수값

- [ ] DICT_SET, DB 경로 등 설정값이 최신인지 확인
- [ ] UI 번호, 큐 인덱스 등이 정확한지 확인

**검증 방법**:
```bash
# 설정값 확인
grep -A 30 "DICT_SET = {" /home/user/STOM/utility/setting.py

# 큐 리스트 확인
grep -A 20 "self.qlist = \[" /home/user/STOM/ui/ui_mainwindow.py
```

---

## 🔍 주요 검증 포인트

### 프로젝트 구조 (01_Overview/project_overview.md)

```bash
# 실제 프로젝트 구조 확인
tree -L 2 -d /home/user/STOM

# 또는
ls -la /home/user/STOM/
```

**주의사항**:
- ✅ 올바름: `STOM/`
- ❌ 잘못됨: `STOM_V1/`

### 시스템 아키텍처 (02_Architecture/system_architecture.md)

```bash
# qlist 큐 시스템 확인
grep -A 5 "self.qlist = \[" /home/user/STOM/ui/ui_mainwindow.py
```

**주의사항**:
- UI의 qlist는 주로 코인 거래용 (15개 큐)
- 주식 모듈은 별도의 독립적인 큐 시스템 사용

### 모듈 파일 구조 (03_Modules/*.md)

```bash
# stock 모듈 파일 목록
ls /home/user/STOM/stock/*.py

# coin 모듈 파일 목록 (서브폴더 없음!)
ls /home/user/STOM/coin/*.py

# ui 모듈 파일 개수 확인
ls /home/user/STOM/ui/*.py | wc -l  # 67개 파일
```

**주의사항**:
- coin/ 폴더에는 서브폴더 없음 (upbit/, binance/ 아님)
- ui/ 폴더에는 67개 Python 파일 존재

### 사용자 매뉴얼 (09_Manual/user_manual.md)

```bash
# 실행 파일 확인
ls /home/user/STOM/stom.py
ls /home/user/STOM/stom_stock.bat
ls /home/user/STOM/stom_coin.bat
```

**주의사항**:
- ✅ 올바름: `python64 stom.py`
- ❌ 잘못됨: `python main.py`

---

## 🛠 자동 검증 스크립트

### 파일 존재 여부 일괄 확인

```bash
#!/bin/bash
# verify_files.sh

# 문서에서 언급된 주요 파일 확인
FILES=(
    "stom.py"
    "stock/kiwoom.py"
    "stock/kiwoom_trader.py"
    "stock/kiwoom_receiver_tick.py"
    "coin/upbit_trader.py"
    "coin/upbit_websocket.py"
    "ui/ui_mainwindow.py"
    "utility/setting.py"
    "backtester/backtest.py"
)

echo "=== STOM 파일 존재 여부 확인 ==="
for file in "${FILES[@]}"; do
    if [ -f "/home/user/STOM/$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (없음)"
    fi
done
```

### 클래스 및 메서드 검증

```bash
#!/bin/bash
# verify_classes.sh

echo "=== Kiwoom 클래스 확인 ==="
grep -n "^class Kiwoom" /home/user/STOM/stock/kiwoom.py

echo "\n=== Kiwoom 주요 메서드 ==="
grep -n "def CommConnect\|def Block_Request\|def SetRealReg\|def SendOrder" \
     /home/user/STOM/stock/kiwoom.py
```

---

## 📝 문서 업데이트 프로세스

### 1. 코드 변경 시

코드를 수정한 후에는 반드시 관련 문서도 업데이트합니다:

1. **변경된 파일 확인**
   ```bash
   git diff --name-only
   ```

2. **영향받는 문서 찾기**
   ```bash
   grep -r "파일명" docs/Manual/
   ```

3. **문서 업데이트**
   - 파일 경로 수정
   - 클래스/메서드명 수정
   - 라인 번호 수정
   - 코드 스니펫 업데이트

4. **검증**
   - 위의 체크리스트 항목 확인
   - 실제 코드와 대조

### 2. 문서 작성 시

새로운 문서를 작성할 때:

1. **실제 코드 먼저 확인**
   ```bash
   cat /home/user/STOM/파일명.py
   ```

2. **코드에서 직접 추출**
   - 실제 클래스명 사용
   - 실제 메서드 시그니처 사용
   - 실제 파라미터명 사용

3. **"예제 코드" 최소화**
   - 가능한 한 실제 코드 스니펫 사용
   - 예제가 필요한 경우 명확히 `**참고**: 실제 코드와 다를 수 있음` 표시

4. **소스 참조 명시**
   - `**소스**: 파일명:라인번호` 형식 사용
   - 라인 번호는 근사값 사용 가능 (코드 변경 고려)

---

## 🔄 정기 검증 프로세스

### 분기별 검증 (권장)

**Q1, Q2, Q3, Q4마다**:

1. 모든 파일 경로 검증
2. 주요 클래스/메서드 시그니처 검증
3. 설정값 및 상수 검증
4. 실행 명령어 검증

### 주요 릴리스 전 검증 (필수)

**새 버전 출시 전**:

1. 전체 문서 리뷰
2. 모든 코드 스니펫 실제 코드와 대조
3. 사용자 매뉴얼 실행 테스트
4. 스크린샷 업데이트 (UI 변경 시)

---

## 📊 최근 검증 이력

| 검증일 | 검증자 | 주요 수정 사항 | 비고 |
|--------|--------|---------------|------|
| 2025-11-26 | Claude Code | STOM_V1→STOM 경로 수정, qlist 구조 수정, Kiwoom 클래스 구조 수정 등 8개 파일 수정 | 실제 코드와 대조 검증 완료 |

---

## 🎯 모범 사례

### ✅ 좋은 예

```markdown
**소스**: `stock/kiwoom.py:36-50`

```python
class Kiwoom:
    def __init__(self, user_class, gubun):
        self.dict_bool = {...}
        self.ocx = QAxWidget('KHOPENAPI.KHOpenAPICtrl.1')
```
```

### ❌ 나쁜 예

```markdown
**소스**: 예제 코드

```python
class Kiwoom(QAxWidget):  # 실제로는 상속 안 함
    def __init__(self):   # 실제로는 파라미터 있음
        super().__init__()
```
```

---

## 📞 문의

문서-코드 불일치 발견 시:
1. GitHub 이슈 등록
2. 해당 문서 파일명과 줄 번호 명시
3. 실제 코드와의 차이점 설명

---

**문서 버전**: v1.0
**최종 수정**: 2025-11-26
