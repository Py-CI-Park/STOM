# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path

def _normalize_text_for_hash(text) -> str:
    if text is None:
        return ''
    s = str(text)
    s = s.replace('\r\n', '\n').replace('\r', '\n')
    return s.strip()

def ComputeStrategyKey(buystg: str = None, sellstg: str = None) -> str:
    """
    매수/매도 전략 코드(전체 텍스트)를 바탕으로 전략 식별키를 생성합니다.
    - 가장 정확한 식별을 위해 sha256(매수코드 + 매도코드) 기반으로 생성
    """
    buy = _normalize_text_for_hash(buystg)
    sell = _normalize_text_for_hash(sellstg)
    payload = f"BUY:\n{buy}\n\nSELL:\n{sell}".encode('utf-8')
    return hashlib.sha256(payload).hexdigest()

def _extract_strategy_block_lines(code: str, start_marker: str, end_marker: str | None = None,
                                 max_lines: int = 12, max_line_len: int = 140) -> list[str]:
    """
    전략 문자열에서 특정 블록(예: 'if 매수:' ~ 'if 매도:') 라인 일부만 추출합니다.
    - 텔레그램/차트 표시 목적이므로, 너무 긴 라인은 잘라냅니다.
    """
    try:
        s = _normalize_text_for_hash(code)
        if not s:
            return []
        lines = s.splitlines()

        start_idx = None
        for i, ln in enumerate(lines):
            if start_marker in ln:
                start_idx = i
                break

        if start_idx is None:
            selected = lines[:max_lines]
        else:
            selected = lines[start_idx:]
            if end_marker:
                end_idx = None
                for j in range(1, len(selected)):
                    if end_marker in selected[j]:
                        end_idx = j
                        break
                if end_idx is not None:
                    selected = selected[:end_idx]
            selected = selected[:max_lines]

        out: list[str] = []
        for ln in selected:
            # 주석 제거(간단 버전)
            if '#' in ln:
                ln = ln.split('#', 1)[0]
            ln = ln.rstrip()
            if not ln.strip():
                continue
            if len(ln) > max_line_len:
                ln = ln[: max_line_len - 3] + "..."
            out.append(ln)
        return out
    except Exception:
        return []

def _safe_filename(name: str, max_len: int = 90) -> str:
    """
    Windows 경로 길이 이슈를 줄이기 위한 안전한 파일명 생성.
    - 너무 길면 앞부분 + 해시로 축약
    """
    s = str(name) if name is not None else 'run'
    s = s.replace('\\', '_').replace('/', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_') \
         .replace('<', '_').replace('>', '_').replace('|', '_')
    s = s.strip()
    if len(s) <= max_len:
        return s
    h = hashlib.sha1(s.encode('utf-8')).hexdigest()[:10]
    return f"{s[:max_len - 11]}_{h}"

def _write_json(path: Path, data: dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8-sig')
    except Exception:
        pass

def _append_jsonl(path: Path, data: dict):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('a', encoding='utf-8-sig') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        pass
