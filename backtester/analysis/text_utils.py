import re

def _format_progress_logs(progress_logs):
    formatted = []
    last_ts = False
    for item in progress_logs:
        text = str(item).strip()
        if not text:
            continue
        if re.match(r'^\[\d{4}-\d{2}-\d{2} ', text):
            formatted.append(f"- {text}")
            last_ts = True
        else:
            prefix = "  - " if last_ts else "- "
            formatted.append(f"{prefix}{text}")
    return formatted


def _extract_strategy_block_lines(code: str, start_marker: str, end_marker: str = None,
                                 max_lines: int = 8, max_line_len: int = 140):
    """
    차트/텔레그램 표시용 전략 블록 라인 추출(간단 버전).
    """
    try:
        s = str(code) if code is not None else ''
        s = s.replace('\r\n', '\n').replace('\r', '\n').strip()
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

        out = []
        for ln in selected:
            if '#' in ln:
                ln = ln.split('#', 1)[0]
            ln = ln.rstrip()
            if not ln.strip():
                continue
            if len(ln) > max_line_len:
                ln = ln[: max_line_len - 3] + '...'
            out.append(ln)
        return out
    except Exception:
        return []


