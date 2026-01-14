"""
ICOS & 분석 설정 버튼 클릭 핸들러.

백테스팅 결과 분석 및 ICOS 반복 최적화 설정 다이얼로그의 버튼 이벤트를 처리합니다.

새로운 구조:
- 백테스팅 결과 분석: Phase A(필터), ML, Phase C(세그먼트) 개별 설정
- ICOS 반복 최적화: 미구현 상태 (향후 개발)

작성일: 2026-01-12
수정일: 2026-01-13
브랜치: feature/enhanced-buy-condition-generator
"""

import json
from pathlib import Path
from multiprocessing import Process
from PyQt5.QtWidgets import QMessageBox
from utility.setting import ui_num


# ============================================================================
# 기본값 상수
# ============================================================================

# 백테스팅 결과 분석 기본값
ANALYSIS_DEFAULTS = {
    'enabled': True,

    # Phase A: 필터 분석
    'filter_analysis': {
        'filter_effects': True,           # 필터 효과 분석
        'optimal_thresholds': True,       # 최적 임계값 탐색
        'filter_combinations': True,      # 필터 조합 분석
        'filter_stability': True,         # 필터 안정성 검증
        'generate_code': True,            # 필터 조건식 생성
    },

    # ML 분석
    'ml_analysis': {
        'risk_prediction': True,          # ML 위험도 예측
        'feature_importance': True,       # ML 특성 중요도
        'mode': 'train',                  # 'train' or 'test'
    },

    # Phase C: 세그먼트 분석
    'segment_analysis': {
        'enabled': True,                  # 세그먼트 분석 활성화
        'optuna': True,                   # Optuna 최적화
        'template_compare': True,         # 템플릿 비교
        'auto_save': True,                # 분석 결과 자동 저장
    },

    # 알림 설정
    'notification': {
        'level': 'detailed',              # 'none', 'summary', 'detailed'
    },
}

# ICOS 반복 최적화 기본값 (미구현 - 설정값만 저장)
ICOS_DEFAULTS = {
    'enabled': False,
    'max_iterations': 5,
    'convergence_threshold': 5,           # %
    'optimization_metric': 0,             # 0=수익금
    'optimization_method': 0,             # 0=그리드서치
}


# ============================================================================
# 버튼 클릭 핸들러
# ============================================================================

def icos_button_clicked_01(ui):
    """ICOS 시작 버튼 - 더 이상 사용 안함.

    이 함수는 더 이상 사용되지 않습니다.
    새 워크플로우에서는 분석 설정을 먼저 지정하고,
    백테스트 버튼으로 실행합니다.

    Args:
        ui: 메인 UI 클래스
    """
    # 새 워크플로우 안내
    QMessageBox.information(
        ui.dialog_icos,
        '사용 안내',
        '새로운 백테스팅 분석 워크플로우:\n\n'
        '1. "분석 활성화" 체크박스로 분석 ON/OFF\n'
        '2. 원하는 분석 옵션을 선택하세요.\n'
        '3. 백테스트 스케줄러에서 조건식을 선택\n'
        '4. 백테스트 버튼 클릭으로 실행\n\n'
        '분석 비활성화 시: 기본 이미지 2개만 전송\n'
        '분석 활성화 시: 상세 분석 결과 전송'
    )


def icos_button_clicked_02(ui):
    """ICOS 중지 버튼 클릭 핸들러.

    실행 중인 ICOS 프로세스를 중지합니다. (미구현 상태)

    Args:
        ui: 메인 UI 클래스
    """
    if not hasattr(ui, 'proc_icos') or ui.proc_icos is None:
        QMessageBox.information(
            ui.dialog_icos,
            '알림',
            'ICOS가 실행 중이지 않습니다.\n'
            '(ICOS 반복 최적화는 아직 미구현 상태입니다.)'
        )
        return

    if not ui.proc_icos.is_alive():
        ui.proc_icos = None
        QMessageBox.information(
            ui.dialog_icos,
            '알림',
            'ICOS가 이미 종료되었습니다.'
        )
        return

    # 확인 대화상자
    reply = QMessageBox.question(
        ui.dialog_icos,
        'ICOS 중지',
        'ICOS 실행을 중지하시겠습니까?\n진행 중인 최적화가 취소됩니다.',
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

            ui.icos_textEditxxx_01.append(
                '<font color="#ffa500">ICOS가 사용자에 의해 중지되었습니다.</font>'
            )
            ui.windowQ.put((ui_num['백테스트'], '<font color=#ffa500>ICOS 중지됨</font>'))

        except Exception as e:
            QMessageBox.critical(
                ui.dialog_icos,
                '오류',
                f'ICOS 중지 실패: {str(e)}'
            )


def icos_button_clicked_03(ui):
    """설정 저장 버튼 클릭 핸들러.

    현재 다이얼로그 설정(Analysis + ICOS)을 파일로 저장합니다.

    Args:
        ui: 메인 UI 클래스
    """
    try:
        # 분석 설정 수집
        analysis_config = _collect_analysis_config(ui)

        # ICOS 설정 수집
        icos_config = _collect_icos_config(ui)

        # 통합 설정
        config_dict = {
            'analysis': analysis_config,
            'icos': icos_config,
            '_saved_at': str(Path.cwd()),
        }

        # 설정 파일 저장
        save_path = Path('./_database/icos_analysis_config.json')
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)

        ui.icos_textEditxxx_01.append(
            f'<font color="#7cfc00">설정 저장 완료: {save_path}</font>'
        )
        QMessageBox.information(
            ui.dialog_icos,
            '저장 완료',
            f'분석 및 ICOS 설정이 저장되었습니다.\n경로: {save_path}'
        )

    except Exception as e:
        QMessageBox.critical(
            ui.dialog_icos,
            '저장 오류',
            f'설정 저장 실패: {str(e)}'
        )


def icos_button_clicked_04(ui):
    """설정 로딩 버튼 클릭 핸들러.

    저장된 설정을 불러와 다이얼로그에 적용합니다.

    Args:
        ui: 메인 UI 클래스
    """
    # 새 경로와 기존 경로 모두 확인
    load_paths = [
        Path('./_database/icos_analysis_config.json'),  # 새 파일
        Path('./_database/icos_config.json'),           # 기존 파일
    ]

    loaded_path = None
    for path in load_paths:
        if path.exists():
            loaded_path = path
            break

    if loaded_path is None:
        QMessageBox.warning(
            ui.dialog_icos,
            '로딩 오류',
            '저장된 설정 파일이 없습니다.\n먼저 설정을 저장하세요.'
        )
        return

    try:
        with open(loaded_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)

        # 새 형식인지 확인
        if 'analysis' in config_dict:
            _apply_analysis_config(ui, config_dict.get('analysis', {}))
            _apply_icos_config(ui, config_dict.get('icos', {}))
        else:
            # 기존 형식 (ICOS만)
            _apply_icos_config(ui, config_dict)
            # Analysis는 기본값 적용
            _apply_analysis_config(ui, ANALYSIS_DEFAULTS)

        ui.icos_textEditxxx_01.append(
            f'<font color="#7cfc00">설정 로딩 완료: {loaded_path}</font>'
        )
        QMessageBox.information(
            ui.dialog_icos,
            '로딩 완료',
            '설정이 로딩되었습니다.'
        )

    except Exception as e:
        QMessageBox.critical(
            ui.dialog_icos,
            '로딩 오류',
            f'설정 로딩 실패: {str(e)}'
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
        '모든 설정을 기본값으로 복원하시겠습니까?',
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        _apply_analysis_config(ui, ANALYSIS_DEFAULTS)
        _apply_icos_config(ui, ICOS_DEFAULTS)
        ui.icos_textEditxxx_01.append(
            '<font color="#7cfc00">모든 설정이 기본값으로 복원되었습니다.</font>'
        )


# ============================================================================
# Analysis 설정 헬퍼 함수
# ============================================================================

def _collect_analysis_config(ui) -> dict:
    """다이얼로그에서 분석 설정값 수집.

    Args:
        ui: 메인 UI 클래스

    Returns:
        분석 설정값 딕셔너리
    """
    # ML 모드 매핑
    ml_mode_map = {0: 'train', 1: 'test'}

    # 알림 레벨 매핑
    notification_map = {0: 'detailed', 1: 'summary', 2: 'none'}

    return {
        'enabled': ui.analysis_checkBoxxx_00.isChecked(),

        # Phase A: 필터 분석
        'filter_analysis': {
            'filter_effects': ui.analysis_checkBoxxx_01.isChecked(),
            'optimal_thresholds': ui.analysis_checkBoxxx_02.isChecked(),
            'filter_combinations': ui.analysis_checkBoxxx_03.isChecked(),
            'filter_stability': ui.analysis_checkBoxxx_04.isChecked(),
            'generate_code': ui.analysis_checkBoxxx_05.isChecked(),
        },

        # ML 분석
        'ml_analysis': {
            'risk_prediction': ui.analysis_checkBoxxx_06.isChecked(),
            'feature_importance': ui.analysis_checkBoxxx_07.isChecked(),
            'mode': ml_mode_map.get(ui.analysis_comboBoxxx_01.currentIndex(), 'train'),
        },

        # Phase C: 세그먼트 분석
        'segment_analysis': {
            'enabled': ui.analysis_checkBoxxx_08.isChecked(),
            'optuna': ui.analysis_checkBoxxx_09.isChecked(),
            'template_compare': ui.analysis_checkBoxxx_10.isChecked(),
            'auto_save': ui.analysis_checkBoxxx_11.isChecked(),
        },

        # 알림 설정
        'notification': {
            'level': notification_map.get(ui.analysis_comboBoxxx_02.currentIndex(), 'detailed'),
        },
    }


def _apply_analysis_config(ui, config: dict):
    """분석 설정값을 다이얼로그에 적용.

    Args:
        ui: 메인 UI 클래스
        config: 분석 설정값 딕셔너리
    """
    # 기본값과 병합
    merged = {**ANALYSIS_DEFAULTS}
    if config:
        merged.update(config)
        if 'filter_analysis' in config:
            merged['filter_analysis'] = {
                **ANALYSIS_DEFAULTS['filter_analysis'],
                **config.get('filter_analysis', {})
            }
        if 'ml_analysis' in config:
            merged['ml_analysis'] = {
                **ANALYSIS_DEFAULTS['ml_analysis'],
                **config.get('ml_analysis', {})
            }
        if 'segment_analysis' in config:
            merged['segment_analysis'] = {
                **ANALYSIS_DEFAULTS['segment_analysis'],
                **config.get('segment_analysis', {})
            }
        if 'notification' in config:
            merged['notification'] = {
                **ANALYSIS_DEFAULTS['notification'],
                **config.get('notification', {})
            }

    # 메인 활성화
    ui.analysis_checkBoxxx_00.setChecked(merged.get('enabled', True))

    # Phase A: 필터 분석
    fa = merged.get('filter_analysis', ANALYSIS_DEFAULTS['filter_analysis'])
    ui.analysis_checkBoxxx_01.setChecked(fa.get('filter_effects', True))
    ui.analysis_checkBoxxx_02.setChecked(fa.get('optimal_thresholds', True))
    ui.analysis_checkBoxxx_03.setChecked(fa.get('filter_combinations', True))
    ui.analysis_checkBoxxx_04.setChecked(fa.get('filter_stability', True))
    ui.analysis_checkBoxxx_05.setChecked(fa.get('generate_code', True))

    # ML 분석
    ml = merged.get('ml_analysis', ANALYSIS_DEFAULTS['ml_analysis'])
    ui.analysis_checkBoxxx_06.setChecked(ml.get('risk_prediction', True))
    ui.analysis_checkBoxxx_07.setChecked(ml.get('feature_importance', True))
    ml_mode = ml.get('mode', 'train')
    ml_mode_idx = {'train': 0, 'test': 1}.get(ml_mode, 0)
    ui.analysis_comboBoxxx_01.setCurrentIndex(ml_mode_idx)

    # Phase C: 세그먼트 분석
    sg = merged.get('segment_analysis', ANALYSIS_DEFAULTS['segment_analysis'])
    ui.analysis_checkBoxxx_08.setChecked(sg.get('enabled', True))
    ui.analysis_checkBoxxx_09.setChecked(sg.get('optuna', True))
    ui.analysis_checkBoxxx_10.setChecked(sg.get('template_compare', True))
    ui.analysis_checkBoxxx_11.setChecked(sg.get('auto_save', True))

    # 알림 설정
    nt = merged.get('notification', ANALYSIS_DEFAULTS['notification'])
    level = nt.get('level', 'detailed')
    level_idx = {'detailed': 0, 'summary': 1, 'none': 2}.get(level, 0)
    ui.analysis_comboBoxxx_02.setCurrentIndex(level_idx)


# ============================================================================
# ICOS 설정 헬퍼 함수 (축소된 형태)
# ============================================================================

def _collect_icos_config(ui) -> dict:
    """다이얼로그에서 ICOS 설정값 수집.

    Args:
        ui: 메인 UI 클래스

    Returns:
        ICOS 설정값 딕셔너리
    """
    try:
        max_iterations = int(ui.icos_lineEdittt_01.text())
        if max_iterations < 1 or max_iterations > 20:
            max_iterations = 5
    except (ValueError, TypeError):
        max_iterations = 5

    try:
        convergence = float(ui.icos_lineEdittt_02.text())
        if convergence < 0 or convergence > 100:
            convergence = 5
    except (ValueError, TypeError):
        convergence = 5

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
        'enabled': ui.icos_checkBoxxx_00.isChecked(),
        'max_iterations': max_iterations,
        'convergence_threshold': convergence,
        'optimization_metric': metric_map.get(
            ui.icos_comboBoxxx_01.currentIndex(), 'profit'
        ),
        'optimization_method': method_map.get(
            ui.icos_comboBoxxx_02.currentIndex(), 'grid_search'
        ),
    }


def _apply_icos_config(ui, config: dict):
    """ICOS 설정값을 다이얼로그에 적용.

    Args:
        ui: 메인 UI 클래스
        config: ICOS 설정값 딕셔너리
    """
    # 기본값과 병합
    merged = {**ICOS_DEFAULTS}
    if config:
        merged.update(config)

    # ICOS 활성화
    ui.icos_checkBoxxx_00.setChecked(merged.get('enabled', False))

    # 최대 반복 횟수
    ui.icos_lineEdittt_01.setText(str(merged.get('max_iterations', 5)))

    # 수렴 기준값
    ui.icos_lineEdittt_02.setText(str(merged.get('convergence_threshold', 5)))

    # 최적화 기준
    metric = merged.get('optimization_metric', 'profit')
    if isinstance(metric, int):
        metric_idx = metric
    else:
        metric_idx = {
            'profit': 0, 'win_rate': 1, 'profit_factor': 2,
            'sharpe_ratio': 3, 'mdd': 4, 'composite': 5
        }.get(metric, 0)
    ui.icos_comboBoxxx_01.setCurrentIndex(metric_idx)

    # 최적화 방법
    method = merged.get('optimization_method', 'grid_search')
    if isinstance(method, int):
        method_idx = method
    else:
        method_idx = {
            'grid_search': 0, 'genetic': 1, 'bayesian': 2
        }.get(method, 0)
    ui.icos_comboBoxxx_02.setCurrentIndex(method_idx)


# ============================================================================
# 백테스트 연동 헬퍼 함수
# ============================================================================

def get_analysis_config(ui) -> dict:
    """현재 분석 설정을 반환하는 외부 호출용 함수.

    백테스트 실행 시 이 함수를 호출하여 설정값을 가져옵니다.

    Args:
        ui: 메인 UI 클래스

    Returns:
        분석 설정 딕셔너리
    """
    return _collect_analysis_config(ui)


def get_icos_config(ui) -> dict:
    """현재 ICOS 설정을 반환하는 외부 호출용 함수.

    Args:
        ui: 메인 UI 클래스

    Returns:
        ICOS 설정 딕셔너리
    """
    return _collect_icos_config(ui)


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


def _run_icos_process(windowQ, backQ, config_dict: dict, buystg: str,
                      sellstg: str, backtest_params: dict):
    """ICOS 백그라운드 프로세스 실행 함수.

    별도 프로세스에서 실행되어 ICOS 최적화를 수행합니다.
    SyncBacktestRunner를 사용하여 반복적 조건식 개선을 수행합니다.

    Args:
        windowQ: 윈도우 메시지 큐
        backQ: 백테스트 큐
        config_dict: ICOS 설정 딕셔너리
        buystg: 매수 조건식
        sellstg: 매도 조건식
        backtest_params: 백테스트 파라미터
    """
    import traceback
    from backtester.iterative_optimizer import IterativeOptimizer, IterativeConfig

    try:
        windowQ.put((ui_num['백테스트'],
            '<font color=#45cdf7>[ICOS] 초기화 중...</font>'))

        # 필수 파라미터 검증
        code_list = backtest_params.get('code_list', [])
        dict_cn = backtest_params.get('dict_cn', {})

        if not code_list and not dict_cn:
            windowQ.put((ui_num['백테스트'],
                '<font color=#ff0000>[ICOS] 오류: 백테엔진이 시작되지 않았습니다. '
                '먼저 백테엔진을 시작해주세요 (dict_cn 누락).</font>'))
            return

        if not code_list:
            code_list = list(dict_cn.keys())
            backtest_params['code_list'] = code_list

        windowQ.put((ui_num['백테스트'],
            f'<font color=#cccccc>[ICOS] 종목 {len(code_list)}개 대상으로 실행</font>'))

        # UI에서 전달받은 설정을 IterativeConfig 형식으로 변환
        icos_config = _convert_ui_config_to_icos_config(config_dict)

        config = IterativeConfig.from_dict(icos_config)
        optimizer = IterativeOptimizer(
            config=config,
            qlist=[windowQ, backQ],
            backtest_params=backtest_params
        )

        windowQ.put((ui_num['백테스트'],
            f'<font color=#7cfc00>[ICOS] 최적화 시작 (최대 {config.max_iterations}회 반복)</font>'))
        windowQ.put((ui_num['백테스트'],
            f'<font color=#cccccc>[ICOS] 수렴 기준: {config.convergence.threshold * 100:.1f}% 이하</font>'))

        result = optimizer.run(buystg, sellstg, backtest_params)

        if result.success:
            windowQ.put((ui_num['백테스트'],
                f'<font color=#7cfc00>[ICOS] 최적화 완료! '
                f'{result.num_iterations}회 반복, '
                f'개선율: {result.total_improvement:.2%}, '
                f'소요시간: {result.total_execution_time:.1f}초</font>'
            ))

            # 최종 조건식 출력
            if result.final_buystg != buystg:
                windowQ.put((ui_num['백테스트'],
                    f'<font color=#87ceeb>[ICOS] 조건식이 개선되었습니다.</font>'
                ))

        else:
            windowQ.put((ui_num['백테스트'],
                f'<font color=#ffa500>[ICOS] 종료: {result.convergence_reason}</font>'
            ))

    except Exception as e:
        error_trace = traceback.format_exc()
        windowQ.put((ui_num['백테스트'],
            f'<font color=#ff0000>[ICOS] 오류 발생: {str(e)}</font>'))
        windowQ.put((ui_num['백테스트'],
            f'<font color=#888888>[ICOS] 상세: {error_trace[:200]}</font>'))


def _convert_ui_config_to_icos_config(ui_config: dict) -> dict:
    """UI에서 전달받은 설정을 IterativeConfig 형식으로 변환.

    Args:
        ui_config: UI에서 수집된 ICOS 설정
            - enabled: bool
            - max_iterations: int
            - convergence_threshold: float (%)
            - optimization_metric: str
            - optimization_method: str

    Returns:
        IterativeConfig.from_dict()가 이해할 수 있는 딕셔너리
    """
    # 최적화 메트릭 매핑
    metric_map = {
        'profit': 'profit',
        'win_rate': 'win_rate',
        'profit_factor': 'profit_factor',
        'sharpe_ratio': 'sharpe',
        'mdd': 'mdd',
        'composite': 'combined',
    }

    # 최적화 방법 매핑
    method_map = {
        'grid_search': 'grid_search',
        'genetic': 'genetic',
        'bayesian': 'bayesian',
    }

    return {
        'enabled': ui_config.get('enabled', True),
        'max_iterations': ui_config.get('max_iterations', 5),
        'convergence': {
            'method': 'improvement_rate',
            'threshold': ui_config.get('convergence_threshold', 5) / 100,  # % → 비율
            'min_iterations': 2,
        },
        'filter_generation': {
            'target_metric': metric_map.get(
                ui_config.get('optimization_metric', 'profit'), 'combined'
            ),
        },
        'optimization': {
            'method': method_map.get(
                ui_config.get('optimization_method', 'grid_search'), 'none'
            ),
        },
        'verbose': True,
        'telegram_notify': False,
    }
