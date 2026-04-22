#!/usr/bin/env python3
"""
파일 삭제 스크립트
- 스크립트와 동일한 폴더에 있는 _database 폴더의 DB 파일 삭제
- 삭제 성공, 실패, 파일 미존재 로그 출력
"""

from pathlib import Path
from typing import Iterable


def delete_files(file_paths: Iterable[Path]) -> None:
    """주어진 파일 경로 목록의 파일을 삭제합니다."""
    for path in file_paths:
        if path.exists():
            try:
                path.unlink()
                print(f"파일 '{path}'이(가) 성공적으로 삭제되었습니다.")
            except OSError as err:
                print(f"파일 삭제 중 에러 발생: {path}, 에러 메시지: {err}")
        else:
            print(f"파일 '{path}'이(가) 존재하지 않습니다.")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    database_dir = base_dir / "_database"

    files_to_delete = [
        database_dir / "stock_tick_back.db",
        database_dir / "stock_min_back.db",
    ]

    delete_files(files_to_delete)
