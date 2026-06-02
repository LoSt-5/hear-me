#!/usr/bin/env python3
"""Генерация лицензионного ключа PRO (после оплаты)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.licensing import format_license_key  # noqa: E402


def main() -> None:
    key = format_license_key()
    print("Лицензионный ключ PRO (один на сборку при фиксированном секрете):")
    print(key)
    print()
    print("Переменная окружения для продакшена: HEAR_ME_LICENSE_SECRET")


if __name__ == "__main__":
    main()
