"""
ICOS (반복적 조건식 개선 시스템) 버튼 클릭 핸들러.

Iterative Condition Optimization System Button Click Handlers.

ICOS 설정 다이얼로그의 버튼 이벤트를 처리합니다.

개선된 워크플로우:
1. Alt+I로 ICOS 다이얼로그 열기
2. "ICOS 활성화" 체크박스 활성화
3. 필요한 설정 조정
4. 백테스트 스케줄러에서 조건식 선택
5. 백테스트 버튼 클릭 → ICOS 모드로 실행

작성일: 2026-01-12
수정일: 2026-01-13
브랜치: feature/iterative-condition-optimizer
"""

import json
from pathlib import Path
from multiprocessing import Process
from PyQt5.QtWidgets import QMessageBox
from utility.setting import ui_num


# ICOS 기본값 상수
ICOS_DEFAULTS = {
    'max_iterations': '5',
    'convergence_threshold': '5',
    'optimization_metric': 0,  # 수익금
    'max_filters_per_iteration': '3',
    'min_samples': '30',
    'use_segment_analysis': True,
    'optimization_method': 0,  # 그리드서치
    'optimization_trials': '100',
    'use_walk_forward': False,
    'walk_forward_folds': '5',
    'save_iterations': True,
    'auto_save_final': True,
    'verbose': False,
}


def icos_button_clicked_01(ui):
    """ICOS 시작 버튼 - 비활성화됨 (새 워크플로우 안내).

    이 함수는 더 이상 사용되지 않습니다.
    새 워크플로우에서는 ICOS 활성화 체크박스를 사용하고,
    백테스트 버튼으로 ICOS 모드를 실행합니다.

    Args:
        ui: 메인 UI 클래스
    """
    # 새 워크플로우 안내
    QMessageBox.information(
        ui.dialog_icos,
        'ICOS 사용법',
        '새로운 ICOS 워크플로우:\n\n'
        '1. "ICOS 활성화" 체크박스를 활성화하세요.\n'
        '2. 백테스트 스케줄러에서 조건식을 선택하세요.\n'
        '3. 백테스트 버튼을 클릭하면 ICOS 모드로 실행됩니다.\n\n'
        'ICOS가 활성화된 상태에서 백테스트를 실행하면\n'
        '자동으로 반복적 조건식 개선이 적용됩니다.'
    )


def icos_button_clicked_02(ui):
    """ICOS 중지 버튼 클릭 핸들러.

    실행 중인 ICOS 프로세스를 중지합니다.

    Args:
        ui: 메인 UI 클래스
    """
    if not hasattr(ui, 'proc_icos') or ui.proc_icos is None:
        QMessageBox.information(
            ui.dialog_icos,
            '알림',
            'ICOS가 실행 중이지 않습니다.\n'
        )
        return

    if not ui.proc_icos.is_alive():
        ui.proc_icos = None
        QMessageBox.information(
            ui.dialog_icos,
            '알림',
            'ICOS가 이미 종료되었습니다.\n'
        )
        return

    # 확인 대화상자
    reply = QMessageBox.question(
        ui.dialog_icos,
        'ICOS 중지',
        'ICOS 실행을 중지하시겠습니까?\n진행 중인 최적화가 취소됩니다.\n',
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        try:
            ui.proc_icos.terminate()
            ui.proc_icos.join(timeout=5)
            if ui.proc_icos.is_alive():
                ui.proc_icos.kill()
            ui.proc_icos = None

            ui.icos_textEditxxx_01.append('<font color="#ffa500">ICOS가 사용자에 의해 중지되었습니다.</font>')
            ui.windowQ.put((ui_num['백테스트'], '<font color=#ffa500>ICOS 중지됨</font>'))

        except Exception as e:
            QMessageBox.critical(
                ui.dialog_icos,
                '오류',
                f'ICOS 중지 실패: {str(e)}\n'
            )


def icos_button_clicked_03(ui):
    """설정 저장 버튼 클릭 핸들러.

    현재 다이얼로그 설정을 파일로 저장합니다.

    Args:
        ui: 메인 UI 클래스
    """
    try:
        config_dict = _collect_icos_config(ui)
        config_dict['_saved_at'] = str(Path.cwd())

        # 설정 파일 저장
        save_path = Path('./_database/icos_config.json')
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)

        ui.icos_textEditxxx_01.append(f'<font color="#7cfc00">설정 저장 완료: {save_path}</font>')
        QMessageBox.information(
            ui.dialog_icos,
            '저장 완료',
            f'ICOS 설정이 저장되었습니다.\n경로: {save_path}\n'
        )

    except Exception as e:
        QMessageBox.critical(
            ui.dialog_icos,
            '저장 오류',
            f'설정 저장 실패: {str(e)}\n'
        )


def icos_button_clicked_04(ui):
    """설정 로딩 버튼 클릭 핸들러.

    저장된 설정을 불러와 다이얼로그에 적용합니다.

    Args:
        ui: 메인 UI 클래스
    """
    load_path = Path('./_database/icos_config.json')

    if not load_path.exists():
        QMessageBox.warning(
            ui.dialog_icos,
            '로딩 오류',
            '저장된 설정 파일이 없습니다.\n먼저 설정을 저장하세요.\n'
        )
        return

    try:
        with open(load_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)

        _apply_icos_config(ui, config_dict)

        ui.icos_textEditxxx_01.append(f'<font color="#7cfc00">설정 로딩 완료: {load_path}</font>')
        QMessageBox.information(
            ui.dialog_icos,
            '로딩 완료',
            'ICOS 설정이 로딩되었습니다.\n'
        )

    except Exception as e:
        QMessageBox.critical(
            ui.dialog_icos,
            '로딩 오류',
            f'설정 로딩 실패: {str(e)}\n'
        )


def icos_button_clicked_05(ui):
    """기본값 복원 버튼 클릭 핸들러.

    다이얼로그 설정을 기본값으로 복원합니다.

    Args:
        ui: 메인 UI 클래스
    """
    reply = QMessageBox.question(
        ui.dialog_icos,
        '기본값 복원',
        '모든 설정을 기본값으로 복원하시겠습니까?\n',
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        _apply_icos_config(ui, ICOS_DEFAULTS)
        ui.icos_textEditxxx_01.append('<font color="#7cfc00">설정이 기본값으로 복원되었습니다.</font>')


# ============================================================================
# 헬퍼 함수들
# ============================================================================

def _collect_icos_config(ui) -> dict:
    """다이얼로그에서 ICOS 설정값 수집.

    Args:
        ui: 메인 UI 클래스

    Returns:
        설정값 딕셔너리

    Raises:
        ValueError: 설정값이 유효하지 않은 경우
    """
    try:
        max_iterations = int(ui.icos_lineEdittt_01.text())
        if max_iterations < 1 or max_iterations > 20:
            raise ValueError('최대 반복 횟수는 1-20 사이여야 합니다.')
    except (ValueError, TypeError):
        raise ValueError('최대 반복 횟수는 유효한 정수여야 합니다.')

    try:
        convergence_threshold = float(ui.icos_lineEdittt_02.text())
        if convergence_threshold < 0 or convergence_threshold > 100:
            raise ValueError('수렴 기준값은 0-100 사이여야 합니다.')
    except (ValueError, TypeError):
        raise ValueError('수렴 기준값은 유효한 숫자여야 합니다.')

    try:
        max_filters = int(ui.icos_lineEdittt_03.text())
        if max_filters < 1 or max_filters > 10:
            raise ValueError('최대 필터 수는 1-10 사이여야 합니다.')
    except (ValueError, TypeError):
        raise ValueError('최대 필터 수는 유효한 정수여야 합니다.')

    try:
        min_samples = int(ui.icos_lineEdittt_04.text())
        if min_samples < 10:
            raise ValueError('최소 샘플 수는 10 이상이어야 합니다.')
    except (ValueError, TypeError):
        raise ValueError('최소 샘플 수는 유효한 정수여야 합니다.')

    try:
        n_trials = int(ui.icos_lineEdittt_05.text())
        if n_trials < 10 or n_trials > 1000:
            raise ValueError('최적화 시도 횟수는 10-1000 사이여야 합니다.')
    except (ValueError, TypeError):
        raise ValueError('최적화 시도 횟수는 유효한 정수여야 합니다.')

    try:
        wf_folds = int(ui.icos_lineEdittt_06.text())
        if wf_folds < 2 or wf_folds > 20:
            raise ValueError('W-F 폴드 수는 2-20 사이여야 합니다.')
    except (ValueError, TypeError):
        raise ValueError('W-F 폴드 수는 유효한 정수여야 합니다.')

    # 최적화 메트릭 매핑
    metric_map = {
        0: 'profit',        # 수익금
        1: 'win_rate',      # 승률
        2: 'profit_factor', # 수익팩터
        3: 'sharpe_ratio',  # 샤프비율
        4: 'mdd',           # MDD
        5: 'composite',     # 복합점수
    }

    # 최적화 방법 매핑
    method_map = {
        0: 'grid_search',   # 그리드서치
        1: 'genetic',       # 유전알고리즘
        2: 'bayesian',      # 베이지안(Optuna)
    }

    return {
        'enabled': True,
        'max_iterations': max_iterations,
        'convergence': {
            'threshold': convergence_threshold / 100.0,  # % to ratio
        },
        'filter_generation': {
            'max_filters_per_iteration': max_filters,
            'min_samples': min_samples,
            'use_segment_analysis': ui.icos_checkBoxxx_01.isChecked(),
        },
        'optimization': {
            'enabled': True,
            'method': method_map.get(ui.icos_comboBoxxx_02.currentIndex(), 'grid_search'),
            'n_trials': n_trials,
            'metric': metric_map.get(ui.icos_comboBoxxx_01.currentIndex(), 'profit'),
        },
        'validation': {
            'use_walk_forward': ui.icos_checkBoxxx_02.isChecked(),
            'n_folds': wf_folds,
        },
        'storage': {
            'save_iterations': ui.icos_checkBoxxx_03.isChecked(),
            'save_final_condition': ui.icos_checkBoxxx_04.isChecked(),
        },
        'verbose': ui.icos_checkBoxxx_05.isChecked(),
    }


def _apply_icos_config(ui, config: dict):
    """설정값을 다이얼로그에 적용.

    Args:
        ui: 메인 UI 클래스
        config: 설정값 딕셔너리
    """
    # 기본값과 병합
    merged = {**ICOS_DEFAULTS, **config}

    # 기본 설정
    ui.icos_lineEdittt_01.setText(str(merged.get('max_iterations', ICOS_DEFAULTS['max_iterations'])))

    # 수렴 설정
    if 'convergence' in merged and isinstance(merged['convergence'], dict):
        threshold = merged['convergence'].get('threshold', 0.05) * 100
    else:
        threshold = float(merged.get('convergence_threshold', ICOS_DEFAULTS['convergence_threshold']))
    ui.icos_lineEdittt_02.setText(str(int(threshold)))

    # 최적화 메트릭
    ui.icos_comboBoxxx_01.setCurrentIndex(merged.get('optimization_metric', 0))

    # 필터 생성 설정
    if 'filter_generation' in merged and isinstance(merged['filter_generation'], dict):
        fg = merged['filter_generation']
        ui.icos_lineEdittt_03.setText(str(fg.get('max_filters_per_iteration', 3)))
        ui.icos_lineEdittt_04.setText(str(fg.get('min_samples', 30)))
        ui.icos_checkBoxxx_01.setChecked(fg.get('use_segment_analysis', True))
    else:
        ui.icos_lineEdittt_03.setText(str(merged.get('max_filters_per_iteration', ICOS_DEFAULTS['max_filters_per_iteration'])))
        ui.icos_lineEdittt_04.setText(str(merged.get('min_samples', ICOS_DEFAULTS['min_samples'])))
        ui.icos_checkBoxxx_01.setChecked(merged.get('use_segment_analysis', ICOS_DEFAULTS['use_segment_analysis']))

    # 최적화 알고리즘 설정
    if 'optimization' in merged and isinstance(merged['optimization'], dict):
        opt = merged['optimization']
        method = opt.get('method', 'grid_search')
        method_idx = {'grid_search': 0, 'genetic': 1, 'bayesian': 2}.get(method, 0)
        ui.icos_comboBoxxx_02.setCurrentIndex(method_idx)
        ui.icos_lineEdittt_05.setText(str(opt.get('n_trials', 100)))

        metric = opt.get('metric', 'profit')
        metric_idx = {'profit': 0, 'win_rate': 1, 'profit_factor': 2, 'sharpe_ratio': 3, 'mdd': 4, 'composite': 5}.get(metric, 0)
        ui.icos_comboBoxxx_01.setCurrentIndex(metric_idx)
    else:
        ui.icos_comboBoxxx_02.setCurrentIndex(merged.get('optimization_method', ICOS_DEFAULTS['optimization_method']))
        ui.icos_lineEdittt_05.setText(str(merged.get('optimization_trials', ICOS_DEFAULTS['optimization_trials'])))

    # 검증 설정
    if 'validation' in merged and isinstance(merged['validation'], dict):
        val = merged['validation']
        ui.icos_checkBoxxx_02.setChecked(val.get('use_walk_forward', False))
        ui.icos_lineEdittt_06.setText(str(val.get('n_folds', 5)))
    else:
        ui.icos_checkBoxxx_02.setChecked(merged.get('use_walk_forward', ICOS_DEFAULTS['use_walk_forward']))
        ui.icos_lineEdittt_06.setText(str(merged.get('walk_forward_folds', ICOS_DEFAULTS['walk_forward_folds'])))

    # 저장 설정
    if 'storage' in merged and isinstance(merged['storage'], dict):
        st = merged['storage']
        ui.icos_checkBoxxx_03.setChecked(st.get('save_iterations', True))
        ui.icos_checkBoxxx_04.setChecked(st.get('save_final_condition', True))
    else:
        ui.icos_checkBoxxx_03.setChecked(merged.get('save_iterations', ICOS_DEFAULTS['save_iterations']))
        ui.icos_checkBoxxx_04.setChecked(merged.get('auto_save_final', ICOS_DEFAULTS['auto_save_final']))

    # 상세 로그
    ui.icos_checkBoxxx_05.setChecked(merged.get('verbose', ICOS_DEFAULTS['verbose']))


def _get_current_buystg(ui) -> str:
    """현재 선택된 매수 조건식 가져오기.

    Args:
        ui: 메인 UI 클래스

    Returns:
        매수 조건식 문자열
    """
    # 스케줄러에서 첫 번째 활성화된 조건식 사용
    for i, checkbox in enumerate(ui.list_checkBoxxxxxx):
        if checkbox.isChecked():
            return ui.list_bcomboBoxxxxx[i].currentText()
    return ''


def _get_current_sellstg(ui) -> str:
    """현재 선택된 매도 조건식 가져오기.

    Args:
        ui: 메인 UI 클래스

    Returns:
        매도 조건식 문자열
    """
    # 스케줄러에서 첫 번째 활성화된 조건식 사용
    for i, checkbox in enumerate(ui.list_checkBoxxxxxx):
        if checkbox.isChecked():
            return ui.list_scomboBoxxxxx[i].currentText()
    return ''


def _collect_backtest_params(ui) -> dict:
    """백테스트 파라미터 수집.

    Args:
        ui: 메인 UI 클래스

    Returns:
        백테스트 파라미터 딕셔너리
    """
    # 스케줄러에서 첫 번째 활성화된 설정 사용
    for i, checkbox in enumerate(ui.list_checkBoxxxxxx):
        if checkbox.isChecked():
            return {
                'startday': ui.list_sdateEdittttt[i].date().toString('yyyyMMdd'),
                'endday': ui.list_edateEdittttt[i].date().toString('yyyyMMdd'),
                'starttime': ui.list_slineEdittttt[i].text(),
                'endtime': ui.list_elineEdittttt[i].text(),
                'betting': ui.list_blineEdittttt[i].text(),
                'avgtime': ui.list_alineEdittttt[i].text(),
            }
    return {}


def _run_icos_process(windowQ, backQ, config_dict: dict, buystg: str, sellstg: str, backtest_params: dict):
    """ICOS 백그라운드 프로세스 실행 함수.

    별도 프로세스에서 실행되어 ICOS 최적화를 수행합니다.

    Args:
        windowQ: 윈도우 메시지 큐
        backQ: 백테스트 큐
        config_dict: ICOS 설정 딕셔너리
        buystg: 매수 조건식
        sellstg: 매도 조건식
        backtest_params: 백테스트 파라미터
    """
    from backtester.iterative_optimizer import IterativeOptimizer, IterativeConfig

    try:
        windowQ.put((ui_num['백테스트'], '<font color=#45cdf7>[ICOS] 초기화 중...</font>'))

        config = IterativeConfig.from_dict(config_dict)
        optimizer = IterativeOptimizer(
            config=config,
            qlist=[windowQ, backQ],
            backtest_params=backtest_params
        )

        windowQ.put((ui_num['백테스트'], f'<font color=#7cfc00>[ICOS] 최적화 시작 (최대 {config.max_iterations}회 반복)</font>'))

        result = optimizer.run(buystg, sellstg, backtest_params)

        if result.success:
            windowQ.put((ui_num['백테스트'],
                f'<font color=#7cfc00>[ICOS] 최적화 완료! '
                f'{result.num_iterations}회 반복, '
                f'개선율: {result.total_improvement:.2%}, '
                f'소요시간: {result.total_execution_time:.1f}초</font>'
            ))
        else:
            windowQ.put((ui_num['백테스트'],
                f'<font color=#ffa500>[ICOS] 종료: {result.convergence_reason}</font>'
            ))

    except Exception as e:
        windowQ.put((ui_num['백테스트'], f'<font color=#ff0000>[ICOS] 오류 발생: {str(e)}</font>'))
