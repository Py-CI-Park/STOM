import sys
import os
import shutil
import ctypes
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QApplication
from utility.timesync import timesync
from ui.ui_mainwindow import MainWindow
from ui.set_style import color_bg_bc, color_fg_bc, color_bg_dk, color_fg_bk, color_fg_hl, color_bg_bk


def clear_pycache_on_dev():
    """개발 중 .pyc 캐시 자동 삭제 (STOM_DEV_MODE 환경 변수 설정 시).

    사용법:
        Windows: set STOM_DEV_MODE=1 && python stom.py
        Linux/Mac: STOM_DEV_MODE=1 python stom.py
    """
    if not os.environ.get('STOM_DEV_MODE'):
        return

    project_root = os.path.dirname(os.path.abspath(__file__))
    cleared_count = 0

    print("[STOM DEV] .pyc 캐시 자동 삭제 활성화...")

    for root, dirs, files in os.walk(project_root):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                cleared_count += 1
                print(f"[STOM DEV] 삭제됨: {pycache_path}")
            except Exception as e:
                print(f"[STOM DEV] 삭제 실패: {pycache_path} - {e}")

    print(f"[STOM DEV] 총 {cleared_count}개 __pycache__ 디렉토리 삭제 완료\n")


if __name__ == '__main__':
    # 개발 모드: .pyc 캐시 자동 삭제
    clear_pycache_on_dev()
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)
    auto_run = 0
    if len(sys.argv) > 1:
        if sys.argv[1] == 'stock':  auto_run = 1
        elif sys.argv[1] == 'coin': auto_run = 2
    timesync()
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, color_bg_bc)
    palette.setColor(QPalette.Background, color_bg_bc)
    palette.setColor(QPalette.WindowText, color_fg_bc)
    palette.setColor(QPalette.Base, color_bg_bc)
    palette.setColor(QPalette.AlternateBase, color_bg_dk)
    palette.setColor(QPalette.Text, color_fg_bc)
    palette.setColor(QPalette.Button, color_bg_bc)
    palette.setColor(QPalette.ButtonText, color_fg_bc)
    palette.setColor(QPalette.Link, color_fg_bk)
    palette.setColor(QPalette.Highlight, color_fg_hl)
    palette.setColor(QPalette.HighlightedText, color_bg_bk)
    app.setPalette(palette)
    mainwindow = MainWindow(auto_run)
    mainwindow.show()
    app.exec_()
