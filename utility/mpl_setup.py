from __future__ import annotations

from typing import Optional


def ensure_mpl_font(font_path: str = 'C:/Windows/Fonts/malgun.ttf',
                    set_monospace: bool = False) -> None:
    try:
        from matplotlib import pyplot as plt
        from matplotlib import font_manager
    except Exception:
        return

    try:
        font_manager.fontManager.addfont(font_path)
    except Exception:
        pass

    try:
        font_family = font_manager.FontProperties(fname=font_path).get_name()
    except Exception:
        font_family = 'Malgun Gothic'

    if not font_family:
        font_family = 'Malgun Gothic'

    plt.rcParams['font.family'] = font_family
    plt.rcParams['font.sans-serif'] = [font_family, 'Malgun Gothic', 'DejaVu Sans']
    if set_monospace:
        plt.rcParams['font.monospace'] = [font_family, 'Consolas', 'monospace']
    plt.rcParams['axes.unicode_minus'] = False
