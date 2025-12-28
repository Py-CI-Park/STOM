import re
from datetime import datetime
from typing import Optional


def _compact_text(text: Optional[str], max_len: int = 40) -> str:
    if text is None:
        return ''
    value = str(text).strip()
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + '...'


def _extract_run_datetime(save_file_name: Optional[str]) -> Optional[str]:
    if not save_file_name:
        return None
    tokens = re.findall(r'(\d{14}|\d{12})', str(save_file_name))
    if not tokens:
        return None
    value = tokens[-1]
    try:
        fmt = '%Y%m%d%H%M%S' if len(value) == 14 else '%Y%m%d%H%M'
        dt = datetime.strptime(value, fmt)
    except Exception:
        return None
    return dt.strftime('%Y-%m-%d %H:%M:%S' if len(value) == 14 else '%Y-%m-%d %H:%M')


def _format_date(value) -> Optional[str]:
    if value is None:
        return None
    text = re.sub(r'\D', '', str(value))
    if len(text) != 8:
        return None
    return f"{text[:4]}-{text[4:6]}-{text[6:8]}"


def _format_time(value) -> Optional[str]:
    if value is None:
        return None
    text = re.sub(r'\D', '', str(value)).zfill(6)
    if len(text) < 4:
        return None
    hh = text[:2]
    mm = text[2:4]
    ss = text[4:6] if len(text) >= 6 else None
    return f"{hh}:{mm}:{ss}" if ss else f"{hh}:{mm}"


def build_strategy_memo_text(buystg_name: Optional[str],
                             sellstg_name: Optional[str],
                             save_file_name: Optional[str],
                             startday=None,
                             endday=None,
                             starttime=None,
                             endtime=None) -> Optional[str]:
    buy = _compact_text(buystg_name or 'N/A')
    sell = _compact_text(sellstg_name or 'N/A')
    lines = [f"매수 조건식: {buy}", f"매도 조건식: {sell}"]

    run_dt = _extract_run_datetime(save_file_name)
    if run_dt:
        lines.append(f"테스트일시: {run_dt}")
    else:
        start_date = _format_date(startday)
        end_date = _format_date(endday)
        start_time = _format_time(starttime)
        end_time = _format_time(endtime)
        if start_date or end_date:
            date_part = f"{start_date or ''}~{end_date or ''}".strip('~')
            time_part = ""
            if start_time or end_time:
                time_part = f" {start_time or ''}~{end_time or ''}".strip()
            lines.append(f"기간: {date_part}{time_part}")

    memo = "\n".join([ln for ln in lines if ln])
    return memo if memo.strip() else None


def add_memo_box(fig, memo_text: Optional[str], fontsize: int = 8,
                 x: float = 0.985, y: float = 0.985) -> None:
    if fig is None or not memo_text:
        return
    fig.text(
        x,
        y,
        memo_text,
        ha='right',
        va='top',
        fontsize=fontsize,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.85),
    )
