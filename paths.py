import sys
from pathlib import Path


def app_root() -> Path:
    """Корень ресурсов: папка проекта или временная папка PyInstaller (_MEIPASS)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent
