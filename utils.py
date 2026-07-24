"""
utils.py
توابع کمکی مشترکی که چندین ماژول دیگه (checker.py, geoip.py, formatter.py)
بهشون نیاز دارن: استخراج کانفیگ از متن، دیکد vmess، گرفتن host/port،
و پاک‌سازی + حذف تکراری.
"""

import base64
import json
import re

import config

CONFIG_REGEX = re.compile(
    r"(?:vless|vmess|trojan|ss|ssr|hysteria2|hy2|tuic)://[^\s`\"'<>]+"
)


def extract_configs_from_text(text: str) -> list[str]:
    """کانفیگ‌ها رو از یه تکه متن دلخواه (پیام تلگرام یا محتوای لینک ساب) استخراج می‌کنه."""
    if not text:
        return []
    return CONFIG_REGEX.findall(text)


def decode_vmess(line: str) -> dict | None:
    """بخش JSON داخل یه لینک vmess:// رو دیکد می‌کنه."""
    try:
        b64 = line[len("vmess://"):]
        padded = b64 + "=" * (-len(b64) % 4)
        return json.loads(base64.b64decode(padded).decode("utf-8", errors="ignore"))
    except Exception:
        return None


def encode_vmess(data: dict) -> str:
    """دیکشنری vmess رو دوباره به فرمت لینک vmess:// برمی‌گردونه."""
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return "vmess://" + base64.b64encode(raw).decode("utf-8")


def get_host(line: str) -> str | None:
    """آدرس سرور رو از هر نوع کانفیگ استخراج می‌کنه."""
    scheme = line.split("://")[0]
    if scheme == "vmess":
        data = decode_vmess(line)
        return data.get("add") if data else None
    match = re.search(r"@([^:/?#]+)", line)
    return match.group(1) if match else None


def get_port(line: str) -> int | None:
    """پورت سرور رو از هر نوع کانفیگ استخراج می‌کنه."""
    scheme = line.split("://")[0]
    if scheme == "vmess":
        data = decode_vmess(line)
        try:
            return int(data.get("port", 443)) if data else None
        except (TypeError, ValueError):
            return None
    match = re.search(r"@[^:/?#]+:(\d+)", line)
    return int(match.group(1)) if match else None


def _dedupe_key(line: str) -> str:
    """
    کلید یکتا برای تشخیص تکراری بودن یه کانفیگ.
    عمداً فقط بخش قبل از # (تگ اسم) رو نادیده می‌گیریم، چون دو تا
    کانفیگ با سرور/تنظیمات یکسان ولی اسم متفاوت باید یکی حساب بشن.
    برای vmess چون همه‌چیز داخل base64 هست، از host+port+id به‌عنوان کلید استفاده می‌کنیم.
    """
    scheme = line.split("://")[0]
    if scheme == "vmess":
        data = decode_vmess(line)
        if not data:
            return line
        return f"vmess:{data.get('add')}:{data.get('port')}:{data.get('id')}"
    return line.split("#")[0]


def clean_and_dedupe(raw_configs: list[str]) -> list[str]:
    """
    پاک‌سازی اولیه‌ی لیست کانفیگ‌ها:
    - حذف فضای خالی اضافه
    - حذف کانفیگ‌هایی که پروتکل معتبر ندارن
    - حذف کانفیگ‌هایی که سرور (host) ندارن
    - حذف تکراری‌ها بر اساس کلید یکتا
    """
    seen: set[str] = set()
    cleaned: list[str] = []

    for line in raw_configs:
        line = line.strip()
        if not line.startswith(config.VALID_PREFIXES):
            continue

        host = get_host(line)
        if not host:
            continue

        key = _dedupe_key(line)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(line)

    return cleaned
