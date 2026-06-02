"""
Точка входа: PRO при активной лицензии, иначе Demo.
Запуск: python main.py
"""
import sys

from services.licensing import is_pro_licensed


def main() -> None:
    if is_pro_licensed():
        from pro import main as pro_main

        pro_main()
    else:
        from demo import main as demo_main

        demo_main()


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        print(e, file=sys.stderr)
        sys.exit(1)
