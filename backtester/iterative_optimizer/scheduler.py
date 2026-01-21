"""
반복적 조건식 개선 시스템 (ICOS) - 자동 스케줄러.

Iterative Condition Optimization System - Auto Scheduler.

이 모듈은 ICOS 실행을 자동으로 예약하고 관리하는 기능을 제공합니다.
주기적 실행, 조건부 실행, 스케줄 관리를 지원합니다.

Phase 6 구현: 자동 스케줄링
- 시간 기반 스케줄링
- 성과 기반 트리거
- 스케줄 관리 (추가, 제거, 조회)
- 텔레그램 알림 통합

작성일: 2026-01-20
브랜치: feature/icos-phase3-6-improvements
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, time as dt_time, timedelta
from enum import Enum
import threading
import json
from pathlib import Path
import time as time_module


class ScheduleType(Enum):
    """스케줄 유형."""
    DAILY = "daily"           # 매일 특정 시간
    WEEKLY = "weekly"         # 매주 특정 요일/시간
    INTERVAL = "interval"     # 일정 간격
    CONDITION = "condition"   # 조건 기반


class TriggerCondition(Enum):
    """트리거 조건."""
    TIME = "time"                           # 시간 기반
    PERFORMANCE_DROP = "performance_drop"   # 성과 하락 시
    TRADE_COUNT = "trade_count"             # 거래 횟수 달성 시
    MANUAL = "manual"                       # 수동 트리거


@dataclass
class Schedule:
    """스케줄 정의.

    Attributes:
        schedule_id: 스케줄 고유 ID
        name: 스케줄 이름
        schedule_type: 스케줄 유형
        trigger_condition: 트리거 조건
        strategy_name: 대상 전략 이름
        backtest_params: 백테스트 파라미터
        enabled: 활성화 여부
        last_run: 마지막 실행 시각
        next_run: 다음 실행 예정 시각
        run_count: 총 실행 횟수
        settings: 추가 설정 (시간, 요일, 간격 등)
    """
    schedule_id: str
    name: str
    schedule_type: ScheduleType
    trigger_condition: TriggerCondition
    strategy_name: str
    backtest_params: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'schedule_id': self.schedule_id,
            'name': self.name,
            'schedule_type': self.schedule_type.value,
            'trigger_condition': self.trigger_condition.value,
            'strategy_name': self.strategy_name,
            'backtest_params': self.backtest_params,
            'enabled': self.enabled,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'settings': self.settings,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schedule':
        """딕셔너리에서 생성."""
        return cls(
            schedule_id=data['schedule_id'],
            name=data['name'],
            schedule_type=ScheduleType(data['schedule_type']),
            trigger_condition=TriggerCondition(data['trigger_condition']),
            strategy_name=data['strategy_name'],
            backtest_params=data.get('backtest_params', {}),
            enabled=data.get('enabled', True),
            last_run=datetime.fromisoformat(data['last_run']) if data.get('last_run') else None,
            next_run=datetime.fromisoformat(data['next_run']) if data.get('next_run') else None,
            run_count=data.get('run_count', 0),
            settings=data.get('settings', {}),
        )


@dataclass
class ScheduleResult:
    """스케줄 실행 결과.

    Attributes:
        schedule_id: 스케줄 ID
        success: 성공 여부
        execution_time: 실행 시간
        result_summary: 결과 요약
        error_message: 에러 메시지
    """
    schedule_id: str
    success: bool
    execution_time: float
    result_summary: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ICOSScheduler:
    """ICOS 자동 스케줄러.

    ICOS 실행을 자동으로 예약하고 관리합니다.

    Attributes:
        schedules: 등록된 스케줄 목록
        is_running: 스케줄러 실행 중 여부
        icos_callback: ICOS 실행 콜백 함수
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        qlist: Optional[list] = None,
    ):
        """초기화.

        Args:
            config_path: 스케줄 설정 파일 경로
            qlist: 프로세스 간 통신 큐 리스트
        """
        self.config_path = config_path or Path('./_database/icos_schedules.json')
        self.qlist = qlist

        self._schedules: Dict[str, Schedule] = {}
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self._icos_callback: Optional[Callable] = None
        self._results: List[ScheduleResult] = []

        # 설정 파일 로드
        self._load_schedules()

    # =========================================================================
    # 스케줄 관리
    # =========================================================================

    def add_schedule(
        self,
        name: str,
        strategy_name: str,
        schedule_type: ScheduleType,
        backtest_params: Dict[str, Any],
        settings: Optional[Dict[str, Any]] = None,
    ) -> Schedule:
        """스케줄 추가.

        Args:
            name: 스케줄 이름
            strategy_name: 전략 이름
            schedule_type: 스케줄 유형
            backtest_params: 백테스트 파라미터
            settings: 추가 설정

        Returns:
            생성된 스케줄
        """
        schedule_id = f"icos_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._schedules)}"

        # 트리거 조건 결정
        if schedule_type == ScheduleType.CONDITION:
            trigger = TriggerCondition.PERFORMANCE_DROP
        else:
            trigger = TriggerCondition.TIME

        schedule = Schedule(
            schedule_id=schedule_id,
            name=name,
            schedule_type=schedule_type,
            trigger_condition=trigger,
            strategy_name=strategy_name,
            backtest_params=backtest_params,
            settings=settings or {},
        )

        # 다음 실행 시간 계산
        schedule.next_run = self._calculate_next_run(schedule)

        self._schedules[schedule_id] = schedule
        self._save_schedules()

        self._log(f"스케줄 추가됨: {name} ({schedule_id})")
        return schedule

    def remove_schedule(self, schedule_id: str) -> bool:
        """스케줄 제거.

        Args:
            schedule_id: 스케줄 ID

        Returns:
            성공 여부
        """
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            self._save_schedules()
            self._log(f"스케줄 제거됨: {schedule_id}")
            return True
        return False

    def enable_schedule(self, schedule_id: str) -> bool:
        """스케줄 활성화."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].enabled = True
            self._schedules[schedule_id].next_run = self._calculate_next_run(
                self._schedules[schedule_id]
            )
            self._save_schedules()
            return True
        return False

    def disable_schedule(self, schedule_id: str) -> bool:
        """스케줄 비활성화."""
        if schedule_id in self._schedules:
            self._schedules[schedule_id].enabled = False
            self._save_schedules()
            return True
        return False

    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """스케줄 조회."""
        return self._schedules.get(schedule_id)

    def get_all_schedules(self) -> List[Schedule]:
        """모든 스케줄 조회."""
        return list(self._schedules.values())

    def get_enabled_schedules(self) -> List[Schedule]:
        """활성화된 스케줄만 조회."""
        return [s for s in self._schedules.values() if s.enabled]

    # =========================================================================
    # 스케줄러 실행
    # =========================================================================

    def start(self, icos_callback: Callable) -> None:
        """스케줄러 시작.

        Args:
            icos_callback: ICOS 실행 콜백 함수
                callback(strategy_name, backtest_params) -> result
        """
        if self._is_running:
            self._log("스케줄러가 이미 실행 중입니다.")
            return

        self._icos_callback = icos_callback
        self._is_running = True
        self._stop_event.clear()

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        self._log("ICOS 스케줄러 시작됨")

    def stop(self) -> None:
        """스케줄러 중지."""
        if not self._is_running:
            return

        self._is_running = False
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=5)

        self._log("ICOS 스케줄러 중지됨")

    def is_running(self) -> bool:
        """실행 중 여부."""
        return self._is_running

    def _run_loop(self) -> None:
        """메인 스케줄러 루프."""
        while not self._stop_event.is_set():
            try:
                self._check_and_run_schedules()
            except Exception as e:
                self._log(f"스케줄러 오류: {e}")

            # 1분 간격으로 체크
            self._stop_event.wait(60)

    def _check_and_run_schedules(self) -> None:
        """스케줄 확인 및 실행."""
        now = datetime.now()

        for schedule in self.get_enabled_schedules():
            if schedule.next_run and schedule.next_run <= now:
                self._execute_schedule(schedule)

    def _execute_schedule(self, schedule: Schedule) -> None:
        """스케줄 실행.

        Args:
            schedule: 실행할 스케줄
        """
        if not self._icos_callback:
            self._log(f"ICOS 콜백이 설정되지 않았습니다: {schedule.name}")
            return

        self._log(f"스케줄 실행 시작: {schedule.name}")
        start_time = time_module.time()

        try:
            result = self._icos_callback(
                schedule.strategy_name,
                schedule.backtest_params,
            )

            execution_time = time_module.time() - start_time

            schedule_result = ScheduleResult(
                schedule_id=schedule.schedule_id,
                success=True,
                execution_time=execution_time,
                result_summary={
                    'strategy': schedule.strategy_name,
                    'improvement': result.total_improvement if hasattr(result, 'total_improvement') else 0,
                    'iterations': result.num_iterations if hasattr(result, 'num_iterations') else 0,
                },
            )

            self._log(
                f"스케줄 실행 완료: {schedule.name} "
                f"({execution_time:.1f}초)"
            )

            # 텔레그램 알림
            self._send_telegram_notification(schedule, schedule_result)

        except Exception as e:
            execution_time = time_module.time() - start_time
            schedule_result = ScheduleResult(
                schedule_id=schedule.schedule_id,
                success=False,
                execution_time=execution_time,
                result_summary={},
                error_message=str(e),
            )
            self._log(f"스케줄 실행 오류: {schedule.name} - {e}")

        # 결과 저장
        self._results.append(schedule_result)

        # 스케줄 업데이트
        schedule.last_run = datetime.now()
        schedule.run_count += 1
        schedule.next_run = self._calculate_next_run(schedule)
        self._save_schedules()

    # =========================================================================
    # 시간 계산
    # =========================================================================

    def _calculate_next_run(self, schedule: Schedule) -> Optional[datetime]:
        """다음 실행 시간 계산.

        Args:
            schedule: 스케줄

        Returns:
            다음 실행 시간
        """
        now = datetime.now()

        if schedule.schedule_type == ScheduleType.DAILY:
            # 매일 특정 시간
            run_time = schedule.settings.get('time', '09:00')
            hour, minute = map(int, run_time.split(':'))

            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        elif schedule.schedule_type == ScheduleType.WEEKLY:
            # 매주 특정 요일/시간
            weekday = schedule.settings.get('weekday', 0)  # 0=월요일
            run_time = schedule.settings.get('time', '09:00')
            hour, minute = map(int, run_time.split(':'))

            days_ahead = weekday - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7

            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return next_run

        elif schedule.schedule_type == ScheduleType.INTERVAL:
            # 일정 간격
            interval_minutes = schedule.settings.get('interval_minutes', 60)
            return now + timedelta(minutes=interval_minutes)

        elif schedule.schedule_type == ScheduleType.CONDITION:
            # 조건 기반 - 다음 체크 시간
            check_interval = schedule.settings.get('check_interval_minutes', 30)
            return now + timedelta(minutes=check_interval)

        return None

    # =========================================================================
    # 알림 및 저장
    # =========================================================================

    def _send_telegram_notification(
        self,
        schedule: Schedule,
        result: ScheduleResult,
    ) -> None:
        """텔레그램 알림 전송."""
        if not self.qlist or len(self.qlist) <= 3:
            return

        teleQ = self.qlist[3]

        if result.success:
            status = "✅ 성공"
            summary = result.result_summary
            message = f"""
═══ ICOS 스케줄 완료 ═══
스케줄: {schedule.name}
전략: {schedule.strategy_name}
상태: {status}

📊 결과
반복: {summary.get('iterations', 0)}회
개선율: {summary.get('improvement', 0):.1%}
실행시간: {result.execution_time:.1f}초

다음 실행: {schedule.next_run.strftime('%Y-%m-%d %H:%M') if schedule.next_run else '-'}
"""
        else:
            status = "❌ 실패"
            message = f"""
═══ ICOS 스케줄 실패 ═══
스케줄: {schedule.name}
전략: {schedule.strategy_name}
상태: {status}
오류: {result.error_message}
"""

        teleQ.put(('telegram', message.strip()))

    def _log(self, message: str) -> None:
        """로그 출력 및 UI 전송."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] [Scheduler] {message}"
        print(log_msg)

        if self.qlist and len(self.qlist) > 0:
            windowQ = self.qlist[0]
            windowQ.put((6, f'<font color="#45cdf7">[Scheduler] {message}</font>'))

    def _save_schedules(self) -> None:
        """스케줄 저장."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'schedules': [s.to_dict() for s in self._schedules.values()],
                'updated_at': datetime.now().isoformat(),
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"스케줄 저장 오류: {e}")

    def _load_schedules(self) -> None:
        """스케줄 로드."""
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for s_data in data.get('schedules', []):
                schedule = Schedule.from_dict(s_data)
                self._schedules[schedule.schedule_id] = schedule

            self._log(f"스케줄 {len(self._schedules)}개 로드됨")
        except Exception as e:
            self._log(f"스케줄 로드 오류: {e}")

    def get_results(self, limit: int = 10) -> List[ScheduleResult]:
        """최근 실행 결과 조회."""
        return self._results[-limit:]

    def get_status(self) -> Dict[str, Any]:
        """스케줄러 상태 조회."""
        return {
            'is_running': self._is_running,
            'total_schedules': len(self._schedules),
            'enabled_schedules': len(self.get_enabled_schedules()),
            'total_runs': sum(s.run_count for s in self._schedules.values()),
            'recent_results': len(self._results),
        }


def create_daily_schedule(
    scheduler: ICOSScheduler,
    name: str,
    strategy_name: str,
    run_time: str,
    backtest_params: Dict[str, Any],
) -> Schedule:
    """매일 실행 스케줄 생성 헬퍼.

    Args:
        scheduler: 스케줄러 인스턴스
        name: 스케줄 이름
        strategy_name: 전략 이름
        run_time: 실행 시간 (HH:MM 형식)
        backtest_params: 백테스트 파라미터

    Returns:
        생성된 스케줄
    """
    return scheduler.add_schedule(
        name=name,
        strategy_name=strategy_name,
        schedule_type=ScheduleType.DAILY,
        backtest_params=backtest_params,
        settings={'time': run_time},
    )


def create_weekly_schedule(
    scheduler: ICOSScheduler,
    name: str,
    strategy_name: str,
    weekday: int,
    run_time: str,
    backtest_params: Dict[str, Any],
) -> Schedule:
    """매주 실행 스케줄 생성 헬퍼.

    Args:
        scheduler: 스케줄러 인스턴스
        name: 스케줄 이름
        strategy_name: 전략 이름
        weekday: 요일 (0=월요일, 6=일요일)
        run_time: 실행 시간 (HH:MM 형식)
        backtest_params: 백테스트 파라미터

    Returns:
        생성된 스케줄
    """
    return scheduler.add_schedule(
        name=name,
        strategy_name=strategy_name,
        schedule_type=ScheduleType.WEEKLY,
        backtest_params=backtest_params,
        settings={'weekday': weekday, 'time': run_time},
    )
