# 11. 기타 - 최적화 편집기 보라색 버튼 가이드

## 대상 버튼
- 최적화 편집기(Alt+2) 진입 시 활성화되는 6개 버튼
  - 그리드 계열: 교차검증(최적화OVC), 검증(최적화OV), 그리드(최적화O)
  - 베이지안/Optuna 계열(보라색): 교차검증(최적화BVC), 검증(최적화BV), 베이지안(최적화B)
- 코인/주식 탭 공통으로 동일하게 동작 (`ui/set_cbtap.py`, `ui/set_sbtap.py`, `ui/ui_button_clicked_cvj.py`).

## 비교 요약
|버튼|데이터 분할|최적화 엔진|목적/장점|주의점|
|---|---|---|---|---|
|교차검증(그리드)|학습/검증 기간을 교차 분할, 폴드 수 = 학습주/검증주 + 1|모든 조합을 탐색하는 Grid Search|여러 시점에서 일반화 성능 확인, 변수 범위가 작을 때 신뢰도 높음|학습 주수가 검증 주수의 배수여야 함, 조합 수가 많으면 오래 걸림|
|검증(그리드)|학습→검증 단일 시계열 분할|Grid Search|교차검증보다 빠르며 기본적인 과적합 점검|단일 분할이라 데이터 구간에 민감, 과적합 가능|
|그리드|전체 학습 기간만 사용|Grid Search|가장 단순·완전 탐색, 범위가 작을 때 빠르게 기준값 확보|검증 없이 학습구간에 맞춰질 수 있음, 결과 해석 시 주의|
|교차검증(베이지안)|학습/검증 교차 분할, 폴드 수 = 학습주/검증주 + 1|Optuna(TPE 기본) 베이지안 최적화|넓은 검색공간에서도 적은 시도로 일반화된 최적값 도출|학습 주수가 검증 주수의 배수여야 함, 탐색결과가 샘플러 설정에 따라 달라짐|
|검증(베이지안)|학습→검증 단일 시계열 분할|Optuna 베이지안|중간 규모 변수 공간에서 빠른 수렴, 과적합 확인 용이|단일 분할이라 데이터 구간에 민감|
|베이지안|전체 학습 기간만 사용|Optuna 베이지안|검색공간이 넓을 때 그리드보다 빠르게 후보 탐색|검증이 없어 과적합 가능, optuna 설정 품질에 의존|

## 공통 입력·단축키
- 기간 설정: 교차검증/검증 버튼은 학습주(`weeks_train`)와 검증주(`weeks_valid`)를 사용하며, 교차검증은 학습주가 검증주의 배수가 아니면 실행이 막힙니다(`cvj_button_clicked_14`).
- 테스트 주(`weeks_test`)를 지정하면 테스트용 버튼(…T)이 별도로 존재하며, 여기서는 최적화용 6개 버튼만 다룹니다.
- 키 조합
  - `Alt`+클릭: 그리드 계열(O, OV, OVC)에서만 최적값 초기치를 랜덤화하여 탐색 시작.
  - `Ctrl`+`Shift`+클릭: 매수 변수만 최적화.
  - `Ctrl`+`Alt`+클릭: 매도 변수만 최적화.
- Optuna 설정: `optuna` 버튼으로 샘플러(TPESampler 기본), 고정 변수 번호, 실행 횟수(0이면 변수 수만큼 자동), 범위 간격 자동 스텝을 설정하며 베이지안 계열 세 버튼에 적용됩니다.

## 버튼별 사용 가이드
- **교차검증(그리드, 최적화OVC)**: 학습/검증 기간을 교차 분할해 모든 변수 조합을 평가합니다. 데이터 구간별 편향을 줄이고 안정적인 기준값이 필요할 때 사용하십시오. 조합 수가 많으면 실행 시간이 크게 증가하므로 변수 범위를 좁히고 실행 횟수(`최적화 횟수` 콤보)로 제한하세요.
- **검증(그리드, 최적화OV)**: 학습→검증 한 번만 분할하여 그리드 탐색합니다. 빠르게 기준값을 점검하거나 교차검증 전에 러프한 탐색이 필요할 때 적합합니다.
- **그리드(최적화O)**: 검증 분할 없이 전체 학습 기간으로 그리드 탐색을 수행합니다. 변수 범위가 작고 데이터가 안정적일 때 기준값을 빠르게 확보하거나, 이후 검증/테스트 단계의 초기값을 마련할 때 사용하십시오.
- **교차검증(베이지안, 최적화BVC)**: 동일한 교차 분할 방식을 베이지안(Optuna)으로 수행합니다. 변수 범위가 넓거나 연속형 비중이 높을 때 효율적으로 최적값을 찾으면서 일반화 성능을 확인할 수 있습니다.
- **검증(베이지안, 최적화BV)**: 단일 학습→검증 분할을 베이지안으로 탐색합니다. 그리드보다 빠르게 우수 후보를 찾고 싶을 때, 하지만 데이터 구간 편향은 여전히 고려해야 합니다.
- **베이지안(최적화B)**: 전체 학습 기간만으로 베이지안 탐색을 진행합니다. 변수 공간이 크거나 optuna 샘플러를 시험할 때 유용하지만 검증이 없으므로 결과를 바로 실전에 쓰기보다 테스트/전진분석으로 재확인하는 것을 권장합니다.

## 관련 소스코드 발췌 (경로:라인)
```python
# ui/set_cbtap.py:150-188 (코인 탭 최적화 버튼)
        self.ui.cvc_pushButton_06 = self.wc.setPushbutton('교차검증', box=self.ui.cs_tab, click=self.ui.cvjButtonClicked_14, cmd='최적화OVC', color=2, tip='...')
        self.ui.cvc_pushButton_07 = self.wc.setPushbutton('검증',     box=self.ui.cs_tab, click=self.ui.cvjButtonClicked_14, cmd='최적화OV',  color=2, tip='...')
        self.ui.cvc_pushButton_08 = self.wc.setPushbutton('그리드',   box=self.ui.cs_tab, click=self.ui.cvjButtonClicked_14, cmd='최적화O',   color=2, tip='...')
        self.ui.cvc_pushButton_27 = self.wc.setPushbutton('교차검증', box=self.ui.cs_tab, click=self.ui.cvjButtonClicked_14, cmd='최적화BVC', color=3, tip='...')
        self.ui.cvc_pushButton_28 = self.wc.setPushbutton('검증',     box=self.ui.cs_tab, click=self.ui.cvjButtonClicked_14, cmd='최적화BV',  color=3, tip='...')
        self.ui.cvc_pushButton_29 = self.wc.setPushbutton('베이지안', box=self.ui.cs_tab, click=self.ui.cvjButtonClicked_14, cmd='최적화B',   color=3, tip='...')
        self.ui.cvc_pushButton_36 = self.wc.setPushbutton('optuna',   color=3, box=self.ui.cs_tab, click=self.ui.cvcButtonClicked_11, tip='옵튜나 샘플러/대시보드')
```

```python
# ui/set_sbtap.py:181-186 (주식 탭 최적화 버튼)
        self.ui.svc_pushButton_06 = self.wc.setPushbutton('교차검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화OVC', color=2, tip='...')
        self.ui.svc_pushButton_07 = self.wc.setPushbutton('검증',     box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화OV',  color=2, tip='...')
        self.ui.svc_pushButton_08 = self.wc.setPushbutton('그리드',   box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화O',   color=2, tip='...')
        self.ui.svc_pushButton_27 = self.wc.setPushbutton('교차검증', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화BVC', color=3, tip='...')
        self.ui.svc_pushButton_28 = self.wc.setPushbutton('검증',     box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화BV',  color=3, tip='...')
        self.ui.svc_pushButton_29 = self.wc.setPushbutton('베이지안', box=self.ui.ss_tab, click=self.ui.svjButtonClicked_14, cmd='최적화B',   color=3, tip='...')
        self.ui.svc_pushButton_36 = self.wc.setPushbutton('optuna',   color=3, box=self.ui.ss_tab, click=self.ui.svcButtonClicked_11, tip='옵튜나 샘플러/대시보드')
```

```python
# ui/ui_button_clicked_cvj.py:750-851 (최적화 버튼 공통 핸들러)
def cvj_button_clicked_14(ui, back_name):
    # 단축키에 따른 플래그 설정
    randomopti = True if not (QApplication.keyboardModifiers() & Qt.ControlModifier) and (
                    QApplication.keyboardModifiers() & Qt.AltModifier) else False
    onlybuy  = True if (QApplication.keyboardModifiers() & Qt.ControlModifier) and (
                    QApplication.keyboardModifiers() & Qt.ShiftModifier) else False
    onlysell = True if (QApplication.keyboardModifiers() & Qt.ControlModifier) and (
                    QApplication.keyboardModifiers() & Qt.AltModifier) else False

    # 입력값 수집 및 교차검증 조건 검사 (학습주 % 검증주 == 0)
    weeks_train = ui.cvc_comboBoxxx_03.currentText()
    weeks_valid = ui.cvc_comboBoxxx_04.currentText()
    if 'VC' in back_name and weeks_train != 'ALL' and int(weeks_train) % int(weeks_valid) != 0:
        QMessageBox.critical(ui, '오류 알림', '교차검증의 학습기간은 검증기간의 배수로 선택하십시오.\n')
        return

    # Optuna 설정 포함하여 큐에 작업 전달
    ui.backQ.put((
        betting, starttime, endtime, buystg, sellstg, optivars, None, ccount, ui.dict_set['최적화기준값제외'],
        optistd, ui.back_count, False, None, None, weeks_train, weeks_valid, weeks_test, benginesday, bengineeday,
        optunasampl, optunafixv, optunacount, optunaautos, randomopti, onlybuy, onlysell
    ))

    # back_name에 따라 그리드/베이지안 프로세스 분기 실행
    if back_name == '최적화O':     ui.proc_backtester_o   = Process(target=Optimize, args=(...)); ui.proc_backtester_o.start()
    elif back_name == '최적화OV':  ui.proc_backtester_ov  = Process(target=Optimize, args=(...)); ui.proc_backtester_ov.start()
    elif back_name == '최적화OVC': ui.proc_backtester_ovc = Process(target=Optimize, args=(...)); ui.proc_backtester_ovc.start()
    elif back_name == '최적화B':   ui.proc_backtester_b   = Process(target=Optimize, args=(...)); ui.proc_backtester_b.start()
    elif back_name == '최적화BV':  ui.proc_backtester_bv  = Process(target=Optimize, args=(...)); ui.proc_backtester_bv.start()
    elif back_name == '최적화BVC': ui.proc_backtester_bvc = Process(target=Optimize, args=(...)); ui.proc_backtester_bvc.start()
```

## Grid Search vs Optuna (코드 차이와 이론적 차이)
- 코드 흐름
  - `Optimize.OptimizeGrid` (backtester/optimiz.py:668-739): 미리 정의된 격자(vars_[i][0])를 전부 탐색하며 기준값을 업데이트. `self.dict_set['범위자동관리']` 옵션으로 범위를 줄이거나 확장. 반복 횟수 `ccount`가 0이면 최적값이 더 이상 바뀌지 않을 때까지 반복.
  - `Optimize.OptimizeOptuna` (backtester/optimiz.py:780-870): Optuna trial 기반. `TPESampler` 기본(862-865), 기타 샘플러 선택 가능. `optuna_autostep`이 켜지면 step 없이 연속 구간을 탐색, 끄면 범위 간격(step)을 그대로 사용. `optuna_count`가 0이면 변수 수+1 만큼 자동 trial 수행, 아니면 지정 횟수로 제한. `StopWhenNotUpdateBestCallBack`(359-369)으로 일정 trial 동안 개선이 없으면 조기 종료.
- 탐색 특성 (이론)
  - Grid Search: 결정적·완전탐색. 변수 차원/격자 수가 커질수록 경우의 수 급증 → 실행 시간/자원 증가. 격자가 촘촘하면 세밀하지만 과적합 위험도 커짐.
  - Optuna(TPE 등): 확률적·연속 탐색. 중요 영역을 더 자주 샘플링해 동일 시간 대비 더 넓은 공간을 커버. 초기 샘플 품질과 샘플러 설정에 민감하며, 재실행마다 결과가 달라질 수 있음.
- 결과 해석 차이
  - Grid Search 결과는 동일 입력 시 재현 가능(랜덤 초기화 옵션 제외). 찾은 최적값이 격자 해상도에 종속.
  - Optuna 결과는 샘플러/시드에 따라 다를 수 있으며, 연속 변수는 격자보다 세밀한 값이 나올 수 있음. `optuna_autostep` ON 시 간격 무시로 더 부드러운 탐색이 가능하지만 실행 시간은 trial 수에 비례.
- 선택 가이드
  - 변수 범위·개수가 작고 재현성이 중요하면 Grid Search.
  - 변수 공간이 넓거나 연속형이 많고 시간 대비 효율이 중요하면 Optuna(TPE) → 교차검증(BVC)으로 일반화 성능 확인 권장.
