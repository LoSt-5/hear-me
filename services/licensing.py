"""
Локальная лицензия PRO: проверка ключа и сохранение в профиле пользователя.

Ключи выдаются после оплаты (вручную или через ваш бэкенд / вебхук платёжки).
Генерация ключей: python tools/generate_license.py
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sys
from pathlib import Path

from paths import app_root

APP_DIR_NAME = "hear-me"
LICENSE_PRODUCT = "pro-v1"
_KEY_RE = re.compile(r"^HM[- ]?([A-Z2-7]{4})[- ]?([A-Z2-7]{4})[- ]?([A-Z2-7]{4})[- ]?([A-Z2-7]{4})$")

# Только для разработки. В продакшене задайте HEAR_ME_LICENSE_SECRET и генерируйте ключи им.
_DEV_SECRET = "hear-me-dev-change-before-release"


def _secret() -> bytes:
    return os.environ.get("HEAR_ME_LICENSE_SECRET", _DEV_SECRET).encode("utf-8")


def license_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    return base / APP_DIR_NAME


def license_path() -> Path:
    return license_dir() / "license.json"


def commerce_config_path() -> Path:
    return app_root() / "configs" / "commerce.json"


def load_commerce_config() -> dict:
    path = commerce_config_path()
    if not path.is_file():
        return {
            "payment_url": "",
            "support_email": "",
            "price_rub": 990,
        }
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _expected_key_digest() -> bytes:
    return hmac.new(_secret(), LICENSE_PRODUCT.encode("utf-8"), hashlib.sha256).digest()


def format_license_key(digest: bytes | None = None) -> str:
    raw = (digest or _expected_key_digest())[:8]
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    n = int.from_bytes(raw, "big")
    chars = []
    for _ in range(16):
        chars.append(alphabet[n % len(alphabet)])
        n //= len(alphabet)
    code = "".join(reversed(chars))
    return f"HM-{code[0:4]}-{code[4:8]}-{code[8:12]}-{code[12:16]}"


def normalize_license_key(key: str) -> str | None:
    cleaned = key.strip().upper().replace(" ", "")
    if cleaned.startswith("HM") and "-" not in cleaned and len(cleaned) >= 18:
        cleaned = f"HM-{cleaned[2:6]}-{cleaned[6:10]}-{cleaned[10:14]}-{cleaned[14:18]}"
    m = _KEY_RE.match(cleaned.replace(" ", ""))
    if not m:
        return None
    return f"HM-{m.group(1)}-{m.group(2)}-{m.group(3)}-{m.group(4)}"


def validate_license_key(key: str) -> bool:
    normalized = normalize_license_key(key)
    if not normalized:
        return False
    expected = format_license_key()
    return hmac.compare_digest(normalized, expected)


def read_license() -> dict | None:
    path = license_path()
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("product") != LICENSE_PRODUCT:
        return None
    key = data.get("key", "")
    if not validate_license_key(key):
        return None
    return data


def is_pro_licensed() -> bool:
    return read_license() is not None


def activate_license(key: str) -> tuple[bool, str]:
    normalized = normalize_license_key(key)
    if not normalized:
        return False, "Неверный формат ключа. Ожидается: HM-XXXX-XXXX-XXXX-XXXX"
    if not validate_license_key(normalized):
        return False, "Ключ не найден или недействителен. Проверьте ввод или обратитесь в поддержку."
    license_dir().mkdir(parents=True, exist_ok=True)
    payload = {
        "product": LICENSE_PRODUCT,
        "key": normalized,
    }
    try:
        with open(license_path(), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError as e:
        return False, f"Не удалось сохранить лицензию: {e}"
    return True, "Лицензия PRO активирована."


def deactivate_license() -> None:
    path = license_path()
    if path.is_file():
        path.unlink()
