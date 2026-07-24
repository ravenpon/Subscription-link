"""
formatter.py
آخرین حلقه‌ی زنجیره: کانفیگ‌های امتیازدهی و کشورشناسی‌شده رو می‌گیره و:
    1. اسم هر کانفیگ رو به فرمت برند تغییر می‌ده
    2. بر اساس کشور دسته‌بندی می‌کنه (کشورهای اختصاصی جدا، بقیه زیر All)
    3. سقف تعداد هر فایل رو اعمال می‌کنه (بر اساس امتیاز، بهترین‌ها اول)
    4. کانفیگ پین‌شده رو همیشه ردیف اول هر فایل می‌ذاره
    5. همه‌ی فایل‌های خروجی رو می‌نویسه
"""

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


def _build_file_content(entries: list[tuple[str, int, str]], limit: int) -> str:
    """
    entries رو بر اساس امتیاز مرتب می‌کنه، به سقف limit محدود می‌کنه،
    اسم برند رو اعمال می‌کنه و کانفیگ پین‌شده رو ردیف اول می‌ذاره.
    """
    sorted_entries = sorted(entries, key=lambda e: e[1], reverse=True)[:limit]

    lines = [config.PINNED_NOTICE_CONFIG]
    for line, _score, country_name in sorted_entries:
        code = next(
            (c for c, n in config.DEDICATED_COUNTRIES.items() if n == country_name),
            "XX",
        )
        flag = _flag_emoji(code) if country_name != "All" else "🌍"
        lines.append(_rename_config(line, flag, country_name))

    return "\n".join(lines) + "\n"


def build_outputs(geo_configs: list[tuple[str, int, str, str]]) -> None:
    """فایل‌های خروجی نهایی (RVVPN_All + یکی به‌ازای هر کشور اختصاصی) رو می‌سازه."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    groups = _group_by_country(geo_configs)

    # فایل کلی: همه‌ی کانفیگ‌ها (از همه کشورها) با سقف MAX_CONFIGS_ALL
    all_entries = [entry for entries in groups.values() for entry in entries]
    all_content = _build_file_content(all_entries, config.MAX_CONFIGS_ALL)
    all_path = os.path.join(config.OUTPUT_DIR, config.OUTPUT_FILES["all"])
    with open(all_path, "w", encoding="utf-8") as f:
        f.write(all_content)
    print(f"📝 {all_path}: {len(all_content.splitlines())} خط نوشته شد.")

    # فایل‌های کشوری اختصاصی
    for code, country_name in config.DEDICATED_COUNTRIES.items():
        entries = groups.get(code, [])
        content = _build_file_content(entries, config.MAX_CONFIGS_PER_COUNTRY)
        path = os.path.join(config.OUTPUT_DIR, f"RVVPN_{country_name.replace(' ', '')}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📝 {path}: {len(content.splitlines())} خط نوشته شد.")
