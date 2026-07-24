"""
formatter.py
آخرین حلقه‌ی زنجیره: کانفیگ‌های امتیازدهی و کشورشناسی‌شده رو می‌گیره و:
    1. اسم هر کانفیگ رو به فرمت برند تغییر می‌ده
    2. بر اساس کشور دسته‌بندی می‌کنه (کشورهای اختصاصی جدا، بقیه زیر All)
    3. سقف تعداد هر فایل رو اعمال می‌کنه (بر اساس امتیاز، بهترین‌ها اول)
    4. کانفیگ پین‌شده رو همیشه ردیف اول هر فایل می‌ذاره
    5. همه‌ی فایل‌های خروجی رو به‌صورت base64 می‌نویسه (فرمت استاندارد Subscription)
"""

import base64
import json
import os
from urllib.parse import quote

import config
from utils import decode_vmess, encode_vmess


def _flag_emoji(country_code: str) -> str:
    if not country_code or len(country_code) != 2 or country_code == "XX":
        return "🌍"
    code = country_code.upper()
    return chr(0x1F1E6 + ord(code[0]) - 65) + chr(0x1F1E6 + ord(code[1]) - 65)


def _rename_config(line: str, flag: str, country: str) -> str:
    tag = config.BRAND_FORMAT.format(flag=flag, country=country)
    scheme = line.split("://")[0]
    if scheme == "vmess":
        data = decode_vmess(line)
        if data is None:
            return line
        data["ps"] = tag
        return encode_vmess(data)
    base = line.split("#")[0]
    return f"{base}#{quote(tag, safe='')}"


def _group_by_country(
    geo_configs: list[tuple[str, int, str, str]]
) -> dict[str, list[tuple[str, int, str]]]:
    """
    ورودی رو بر اساس کشور دسته‌بندی می‌کنه.
    خروجی: {country_code_or_ALL: [(line, score, country_name), ...]}
    کشورهای غیر از DEDICATED_COUNTRIES همه زیر کلید "ALL" جمع می‌شن.
    """
    groups: dict[str, list[tuple[str, int, str]]] = {}

    for line, score, code, name in geo_configs:
        if code in config.DEDICATED_COUNTRIES:
            groups.setdefault(code, []).append((line, score, config.DEDICATED_COUNTRIES[code]))
        else:
            groups.setdefault("ALL", []).append((line, score, "All"))

    return groups


def _build_file_content(
    entries: list[tuple[str, int, str]], limit: int
) -> tuple[str, list[str]]:
    """
    entries رو بر اساس امتیاز مرتب می‌کنه، به سقف limit محدود می‌کنه،
    اسم برند رو اعمال می‌کنه و کانفیگ پین‌شده رو ردیف اول می‌ذاره.
    خروجی: (متن خامِ کانفیگ‌ها برای نوشتن در فایل, لیست raw config های
    اصلی/پیش از rename که در این فایل استفاده شدن — برای ثبت در تاریخچه).
    base64 کردن وظیفه‌ی تابع build_outputs هست، نه این تابع.
    """
    sorted_entries = sorted(entries, key=lambda e: e[1], reverse=True)[:limit]

    lines = [config.PINNED_NOTICE_CONFIG]
    raw_lines_used: list[str] = []
    for line, _score, country_name in sorted_entries:
        code = next(
            (c for c, n in config.DEDICATED_COUNTRIES.items() if n == country_name),
            "XX",
        )
        flag = _flag_emoji(code) if country_name != "All" else "🌍"
        lines.append(_rename_config(line, flag, country_name))
        raw_lines_used.append(line)

    return "\n".join(lines) + "\n", raw_lines_used


def _write_subscription_file(path: str, raw_content: str) -> None:
    """
    محتوای خام (لیست کانفیگ‌ها، هر خط یکی) رو به فرمت استاندارد
    Subscription (کل فایل base64-encode شده) تبدیل و ذخیره می‌کنه.
    بدون این مرحله، اکثر کلاینت‌ها (V2rayNG، NekoBox، Clash و...)
    قادر به پارس کردن لینک ساب نیستن.
    """
    encoded = base64.b64encode(raw_content.encode("utf-8")).decode("utf-8")
    with open(path, "w", encoding="utf-8") as f:
        f.write(encoded)


def _save_published_history(raw_configs: set[str]) -> None:
    """
    راو کانفیگ‌های (پیش از rename) استفاده‌شده در این اجرا رو ذخیره می‌کنه.
    فقط آخرین اجرا نگه داشته می‌شه؛ فایل هر بار کامل بازنویسی می‌شه، نه append.
    این فایل توسط main.py خونده می‌شه تا از تکرار عین همون کانفیگ در اجرای
    بعدی جلوگیری کنه.
    """
    with open(config.PUBLISHED_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(raw_configs), f, ensure_ascii=False, indent=2)


def build_outputs(geo_configs: list[tuple[str, int, str, str]]) -> None:
    """فایل‌های خروجی نهایی (RVVPN_All + یکی به‌ازای هر کشور اختصاصی) رو می‌سازه."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    groups = _group_by_country(geo_configs)
    all_raw_used: set[str] = set()

    # فایل کلی: همه‌ی کانفیگ‌ها (از همه کشورها) با سقف MAX_CONFIGS_ALL
    all_entries = [entry for entries in groups.values() for entry in entries]
    all_content, all_raw = _build_file_content(all_entries, config.MAX_CONFIGS_ALL)
    all_path = os.path.join(config.OUTPUT_DIR, config.OUTPUT_FILES["all"])
    _write_subscription_file(all_path, all_content)
    all_raw_used.update(all_raw)
    print(f"📝 {all_path}: {len(all_content.splitlines())} کانفیگ نوشته شد (base64).")

    # فایل‌های کشوری اختصاصی
    for code, country_name in config.DEDICATED_COUNTRIES.items():
        entries = groups.get(code, [])
        content, raw_used = _build_file_content(entries, config.MAX_CONFIGS_PER_COUNTRY)
        path = os.path.join(config.OUTPUT_DIR, f"RVVPN_{country_name.replace(' ', '')}")
        _write_subscription_file(path, content)
        all_raw_used.update(raw_used)
        print(f"📝 {path}: {len(content.splitlines())} کانفیگ نوشته شد (base64).")

    _save_published_history(all_raw_used)
    print(f"🗂️ {len(all_raw_used)} کانفیگ در تاریخچه‌ی این اجرا ثبت شد.")
