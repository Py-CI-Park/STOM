"""
반복적 조건식 개선 시스템 (ICOS) - 공통 데이터 타입.

Iterative Condition Optimization System - Common Data Types.

이 모듈은 ICOS 전체에서 사용되는 공통 데이터 클래스를 정의합니다.
순환 import 문제를 방지하기 위해 별도 모듈로 분리되었습니다.

작성일: 2026-01-12
브랜치: feature/iterative-condition-optimizer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd


@dataclass
class FilterCandidate:
    """필터 후보.

    생성된 필터 조건의 정보를 담는 데이터 클래스입니다.

    Attributes:
        condition: 필터 조건 문자열 (Python 표현식)
        description: 필터 설명 (사람이 읽을 수 있는 형태)
        source: 필터 생성 소스 ('segment_analysis', 'loss_pattern', 등)
        expected_impact: 예상 영향도 (0.0 ~ 1.0)
        metadata: 추가 메타데이터
    """
    condition: str
    description: str
    source: str = "unknown"
    expected_impact: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IterationResult:
    """단일 반복 결과.

    하나의 반복 사이클 결과를 담는 데이터 클래스입니다.

    Attributes:
        iteration: 반복 번호 (0-indexed)
        buystg: 사용된 매수 조건식
        sellstg: 사용된 매도 조건식
        applied_filters: 적용된 필터 목록
        metrics: 백테스트 결과 지표
        df_tsg: 거래 상세 데이터프레임 (옵션)
        execution_time: 실행 시간 (초)
        timestamp: 완료 시각
    """
    iteration: int
    buystg: str
    sellstg: str
    applied_filters: List[FilterCandidate]
    metrics: Dict[str, float]
    df_tsg: Optional[pd.DataFrame] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화용)."""
        return {
            'iteration': self.iteration,
            'buystg': self.buystg[:200] + '...' if len(self.buystg) > 200 else self.buystg,
            'sellstg': self.sellstg[:200] + '...' if len(self.sellstg) > 200 else self.sellstg,
            'applied_filters': [
                {
                    'condition': f.condition,
                    'description': f.description,
                    'source': f.source,
                }
                for f in self.applied_filters
            ],
            'metrics': self.metrics,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat(),
        }
