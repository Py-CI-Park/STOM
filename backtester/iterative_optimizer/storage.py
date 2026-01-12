"""
반복적 조건식 개선 시스템 (ICOS) - 저장소.

Iterative Condition Optimization System - Storage.

이 모듈은 반복 최적화 과정의 결과를 저장하고 로드하는 기능을 제공합니다.

저장 형식:
- JSON: 메타데이터, 반복 결과, 설정
- TXT: 최종 조건식 코드
- CSV: 필터 적용 이력 (선택)

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import json
import csv

from .config import IterativeConfig


@dataclass
class StorageMetadata:
    """저장소 메타데이터.

    Attributes:
        session_id: 세션 고유 ID
        created_at: 생성 시각
        updated_at: 최종 업데이트 시각
        config_hash: 설정 해시 (변경 감지용)
        total_iterations: 총 반복 횟수
        status: 상태 ('running', 'completed', 'failed')
    """
    session_id: str
    created_at: datetime
    updated_at: datetime
    config_hash: str
    total_iterations: int
    status: str

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'config_hash': self.config_hash,
            'total_iterations': self.total_iterations,
            'status': self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StorageMetadata':
        """딕셔너리에서 생성."""
        return cls(
            session_id=data['session_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            config_hash=data['config_hash'],
            total_iterations=data['total_iterations'],
            status=data['status'],
        )


class IterationStorage:
    """반복 결과 저장소.

    반복 최적화 과정의 결과를 파일 시스템에 저장하고 로드합니다.

    디렉토리 구조:
        {base_path}/
        ├── metadata.json          # 세션 메타데이터
        ├── config.json            # ICOS 설정
        ├── iterations/
        │   ├── iteration_0.json   # 각 반복 결과
        │   ├── iteration_1.json
        │   └── ...
        ├── conditions/
        │   ├── buystg_0.txt       # 각 반복의 조건식
        │   ├── buystg_1.txt
        │   └── ...
        ├── final_buystg.txt       # 최종 조건식
        └── summary.json           # 최종 요약

    Attributes:
        config: ICOS 설정
        base_path: 저장 기본 경로

    Example:
        >>> storage = IterationStorage(config, Path('./output'))
        >>> storage.save_iteration(result)
        >>> loaded = storage.load_iteration(0)
    """

    def __init__(
        self,
        config: IterativeConfig,
        base_path: Optional[Path] = None,
    ):
        """IterationStorage 초기화.

        Args:
            config: ICOS 설정
            base_path: 저장 기본 경로 (None이면 설정에서 가져옴)
        """
        self.config = config

        # 기본 경로 설정
        if base_path is None:
            if config.storage.output_dir:
                base_path = Path(config.storage.output_dir)
            else:
                # 기본값: 프로젝트 루트의 _icos_results 디렉토리
                base_path = Path.cwd() / '_icos_results'

        self.base_path = base_path
        self._session_id: Optional[str] = None
        self._metadata: Optional[StorageMetadata] = None

        # 디렉토리 생성
        if config.storage.save_iterations:
            self._ensure_directories()

    def _ensure_directories(self) -> None:
        """필요한 디렉토리 생성."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / 'iterations').mkdir(exist_ok=True)
        (self.base_path / 'conditions').mkdir(exist_ok=True)

    def _generate_session_id(self) -> str:
        """세션 ID 생성."""
        return datetime.now().strftime('%Y%m%d_%H%M%S')

    def _get_config_hash(self) -> str:
        """설정 해시 생성."""
        import hashlib
        config_str = json.dumps(self.config.to_dict(), sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()[:8]

    def initialize_session(self) -> str:
        """새 세션 초기화.

        Returns:
            세션 ID
        """
        self._session_id = self._generate_session_id()
        self._metadata = StorageMetadata(
            session_id=self._session_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            config_hash=self._get_config_hash(),
            total_iterations=0,
            status='running',
        )

        # 설정 저장
        self._save_config()
        self._save_metadata()

        return self._session_id

    def _save_config(self) -> None:
        """설정 저장."""
        if not self.config.storage.save_iterations:
            return

        config_path = self.base_path / 'config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=2)

    def _save_metadata(self) -> None:
        """메타데이터 저장."""
        if not self.config.storage.save_iterations or self._metadata is None:
            return

        metadata_path = self.base_path / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self._metadata.to_dict(), f, ensure_ascii=False, indent=2)

    def save_iteration(
        self,
        iteration: int,
        metrics: Dict[str, float],
        buystg: str,
        sellstg: str,
        applied_filters: List[Dict[str, Any]],
        execution_time: float,
        analysis_summary: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """단일 반복 결과 저장.

        Args:
            iteration: 반복 번호
            metrics: 성과 지표
            buystg: 매수 조건식
            sellstg: 매도 조건식
            applied_filters: 적용된 필터 목록
            execution_time: 실행 시간 (초)
            analysis_summary: 분석 요약 (선택)

        Returns:
            저장된 파일 경로
        """
        if not self.config.storage.save_iterations:
            return Path()

        # 반복 결과 데이터
        iteration_data = {
            'iteration': iteration,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'applied_filters': [
                {
                    'condition': f.get('condition', ''),
                    'description': f.get('description', ''),
                    'source': f.get('source', 'unknown'),
                    'expected_impact': f.get('expected_impact', 0.0),
                }
                for f in applied_filters
            ],
            'execution_time': execution_time,
            'buystg_length': len(buystg),
            'sellstg_length': len(sellstg),
        }

        if analysis_summary:
            iteration_data['analysis_summary'] = analysis_summary

        # JSON 저장
        iteration_path = self.base_path / 'iterations' / f'iteration_{iteration}.json'
        with open(iteration_path, 'w', encoding='utf-8') as f:
            json.dump(iteration_data, f, ensure_ascii=False, indent=2)

        # 조건식 저장 (설정에 따라)
        if self.config.storage.save_iterations:
            condition_path = self.base_path / 'conditions' / f'buystg_{iteration}.txt'
            self._save_condition_file(condition_path, buystg, sellstg, iteration, metrics)

        # 메타데이터 업데이트
        if self._metadata:
            self._metadata.updated_at = datetime.now()
            self._metadata.total_iterations = iteration + 1
            self._save_metadata()

        return iteration_path

    def _save_condition_file(
        self,
        path: Path,
        buystg: str,
        sellstg: str,
        iteration: int,
        metrics: Dict[str, float],
    ) -> None:
        """조건식 파일 저장.

        Args:
            path: 저장 경로
            buystg: 매수 조건식
            sellstg: 매도 조건식
            iteration: 반복 번호
            metrics: 성과 지표
        """
        header = [
            f"# ICOS 반복 {iteration} 조건식",
            f"# 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# 세션 ID: {self._session_id or 'unknown'}",
            "",
            "# === 성과 지표 ===",
        ]

        for key, value in metrics.items():
            if isinstance(value, float):
                header.append(f"# {key}: {value:,.2f}")
            else:
                header.append(f"# {key}: {value}")

        header.extend([
            "",
            "# === 매수 조건식 ===",
            "",
        ])

        content = '\n'.join(header) + buystg

        if sellstg:
            content += '\n\n# === 매도 조건식 ===\n\n' + sellstg

        with open(path, 'w', encoding='utf-8-sig') as f:
            f.write(content)

    def load_iteration(self, iteration: int) -> Optional[Dict[str, Any]]:
        """단일 반복 결과 로드.

        Args:
            iteration: 반복 번호

        Returns:
            반복 결과 데이터 (없으면 None)
        """
        iteration_path = self.base_path / 'iterations' / f'iteration_{iteration}.json'

        if not iteration_path.exists():
            return None

        with open(iteration_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_all_iterations(self) -> List[Dict[str, Any]]:
        """모든 반복 결과 로드.

        Returns:
            반복 결과 리스트 (반복 번호 순)
        """
        iterations = []
        iterations_dir = self.base_path / 'iterations'

        if not iterations_dir.exists():
            return iterations

        for path in sorted(iterations_dir.glob('iteration_*.json')):
            with open(path, 'r', encoding='utf-8') as f:
                iterations.append(json.load(f))

        return iterations

    def load_condition(self, iteration: int) -> Optional[str]:
        """특정 반복의 조건식 로드.

        Args:
            iteration: 반복 번호

        Returns:
            조건식 문자열 (없으면 None)
        """
        condition_path = self.base_path / 'conditions' / f'buystg_{iteration}.txt'

        if not condition_path.exists():
            return None

        with open(condition_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        # 헤더 주석 제거하고 실제 조건식만 반환
        lines = content.split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            if line.startswith('# === 매수 조건식 ==='):
                in_code = True
                continue
            if line.startswith('# === 매도 조건식 ==='):
                break
            if in_code and not line.startswith('#'):
                code_lines.append(line)

        return '\n'.join(code_lines).strip()

    def save_final_result(
        self,
        final_buystg: str,
        final_sellstg: str,
        total_improvement: float,
        convergence_reason: str,
        total_execution_time: float,
    ) -> Path:
        """최종 결과 저장.

        Args:
            final_buystg: 최종 매수 조건식
            final_sellstg: 최종 매도 조건식
            total_improvement: 전체 개선율
            convergence_reason: 수렴/종료 사유
            total_execution_time: 총 실행 시간

        Returns:
            저장된 파일 경로
        """
        if not self.config.storage.save_iterations:
            return Path()

        # 최종 조건식 저장
        final_path = self.base_path / 'final_buystg.txt'
        header = [
            "# ICOS 최종 최적화 조건식",
            f"# 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# 세션 ID: {self._session_id or 'unknown'}",
            f"# 총 반복 횟수: {self._metadata.total_iterations if self._metadata else 0}",
            f"# 전체 개선율: {total_improvement:.2%}",
            f"# 수렴 사유: {convergence_reason}",
            f"# 총 실행 시간: {total_execution_time:.1f}초",
            "",
            "# === 매수 조건식 ===",
            "",
        ]

        content = '\n'.join(header) + final_buystg

        if final_sellstg:
            content += '\n\n# === 매도 조건식 ===\n\n' + final_sellstg

        with open(final_path, 'w', encoding='utf-8-sig') as f:
            f.write(content)

        # 요약 저장
        summary = {
            'session_id': self._session_id,
            'completed_at': datetime.now().isoformat(),
            'total_iterations': self._metadata.total_iterations if self._metadata else 0,
            'total_improvement': total_improvement,
            'convergence_reason': convergence_reason,
            'total_execution_time': total_execution_time,
            'final_buystg_length': len(final_buystg),
            'final_sellstg_length': len(final_sellstg),
        }

        summary_path = self.base_path / 'summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # 메타데이터 업데이트
        if self._metadata:
            self._metadata.status = 'completed'
            self._metadata.updated_at = datetime.now()
            self._save_metadata()

        return final_path

    def save_filter_history(
        self,
        filter_history: List[Dict[str, Any]],
    ) -> Path:
        """필터 적용 이력 CSV 저장.

        Args:
            filter_history: 필터 이력 리스트

        Returns:
            저장된 파일 경로
        """
        if not self.config.storage.save_iterations:
            return Path()

        csv_path = self.base_path / 'filter_history.csv'

        if not filter_history:
            return csv_path

        # 컬럼 추출
        columns = list(filter_history[0].keys())

        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(filter_history)

        return csv_path

    def load_metadata(self) -> Optional[StorageMetadata]:
        """메타데이터 로드.

        Returns:
            메타데이터 (없으면 None)
        """
        metadata_path = self.base_path / 'metadata.json'

        if not metadata_path.exists():
            return None

        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return StorageMetadata.from_dict(data)

    def load_config(self) -> Optional[Dict[str, Any]]:
        """설정 로드.

        Returns:
            설정 딕셔너리 (없으면 None)
        """
        config_path = self.base_path / 'config.json'

        if not config_path.exists():
            return None

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_summary(self) -> Optional[Dict[str, Any]]:
        """최종 요약 로드.

        Returns:
            요약 딕셔너리 (없으면 None)
        """
        summary_path = self.base_path / 'summary.json'

        if not summary_path.exists():
            return None

        with open(summary_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_session_path(self) -> Path:
        """현재 세션 경로 반환."""
        return self.base_path

    def session_exists(self) -> bool:
        """세션 존재 여부 확인."""
        return (self.base_path / 'metadata.json').exists()

    def get_iteration_count(self) -> int:
        """저장된 반복 수 반환."""
        iterations_dir = self.base_path / 'iterations'
        if not iterations_dir.exists():
            return 0
        return len(list(iterations_dir.glob('iteration_*.json')))

    def cleanup(self) -> None:
        """세션 정리 (임시 파일 삭제).

        주의: 이 메서드는 모든 저장된 데이터를 삭제합니다.
        """
        import shutil

        if self.base_path.exists():
            shutil.rmtree(self.base_path)
            self.base_path.mkdir(parents=True, exist_ok=True)
            self._ensure_directories()

        self._session_id = None
        self._metadata = None
