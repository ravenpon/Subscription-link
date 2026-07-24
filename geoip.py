"""
geoip.py
تشخیص کشور هر سرور با سرویس رایگان ip-api.com، به‌همراه یه کش محلی
(geoip_cache.json) تا بین اجراهای پی‌درپی هر ۳۰ دقیقه، IPهای تکراری
دوباره کوئری نشن.

⚠️ نکته‌ی مهم: ip-api.com نسخه‌ی رایگانش محدودیت نرخ درخواست داره؛
اگه بین batch ها تاخیر نباشه، از یه جایی به بعد rate-limit می‌خوریم و
همون کانفیگ‌هایی که باید کشورشون پیدا بشه، بی‌دلیل به‌عنوان Unknown
برمی‌گردن. برای همین بین هر batch یک تاخیر کوتاه (GEOIP_BATCH_DELAY_SECONDS)
گذاشته شده.

همچنین برای هاست‌هایی که با ip-api جواب نگرفتن (چه به خاطر rate-limit،
چه خطای موقت شبکه)، یک بار دیگه با سرویس رایگان دوم (ipwho.is) به‌عنوان
fallback امتحان می‌شن، تا شانس پیدا کردن کشور واقعی بیشتر بشه.

خروجی: هر کانفیگ به‌صورت (line, score, country_code, country_name)
برمی‌گرده تا formatter.py بتونه هم دسته‌بندی کشوری کنه، هم بر اساس
امتیاز مرتب‌سازی نگه داره.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

import config
from utils import get_host

BATCH_SIZE = 100
REQUEST_TIMEOUT = 20


def _load_cache() -> dict:
    if not os.path.exists(config.GEOIP_CACHE_FILE):
        return {}
    try:
        with open(config.GEOIP_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    try:
        with open(config.GEOIP_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  ذخیره کش GeoIP ناموفق بود: {e}")


def _is_fresh(entry: dict) -> bool:
    age_days = (time.time() - entry.get("ts", 0)) / 86400
    return age_days < config.GEOIP_CACHE_TTL_DAYS


def _query_batch_ip_api(hosts: list[str]) -> dict:
    """یه دسته (حداکثر ۱۰۰ تا) هاست رو به‌صورت یک‌جا از ip-api.com می‌پرسه."""
    result = {}
    try:
        resp = requests.post(
            "http://ip-api.com/batch?fields=query,countryCode,country",
            json=[{"query": h} for h in hosts],
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        for item in resp.json():
            if item.get("countryCode"):
                result[item["query"]] = {
                    "code": item["countryCode"],
                    "name": item.get("country", item["countryCode"]),
                    "ts": time.time(),
                }
    except Exception as e:
        print(f"⚠️  خطا تو درخواست GeoIP (ip-api): {e}")
    return result


def _query_single_ipwhois(host: str) -> tuple[str, dict | None]:
    """
    یک هاست رو به‌صورت تکی از ipwho.is می‌پرسه (این سرویس batch نداره).
    فقط برای هاست‌هایی صدا زده می‌شه که ip-api جوابشون رو نداده.
    """
    try:
        resp = requests.get(f"https://ipwho.is/{host}", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success") and data.get("country_code"):
            return host, {
                "code": data["country_code"],
                "name": data.get("country", data["country_code"]),
                "ts": time.time(),
            }
    except Exception as e:
        print(f"⚠️  خطا تو درخواست GeoIP (ipwho.is) برای {host}: {e}")
    return host, None


def _query_fallback_ipwhois(hosts: list[str]) -> dict:
    """
    هاست‌های باقی‌مونده (که ip-api جوابشون رو نداده) رو با ipwho.is،
    به‌صورت موازی (با تعداد thread محدود) امتحان می‌کنه.
    """
    if not hosts:
        return {}

    print(f"🔁 GeoIP fallback: {len(hosts)} هاست با ipwho.is دوباره امتحان می‌شه.")
    result = {}
    with ThreadPoolExecutor(max_workers=config.GEOIP_FALLBACK_WORKERS) as executor:
        futures = [executor.submit(_query_single_ipwhois, h) for h in hosts]
        for future in as_completed(futures):
            host, entry = future.result()
            if entry:
                result[host] = entry
    return result


def _resolve_hosts(hosts: list[str]) -> dict:
    """
    کشور هر هاست رو برمی‌گردونه:
    ۱. اول از کش (اگه تازه باشه)
    ۲. برای بقیه، از ip-api.com (با تاخیر بین batch ها)
    ۳. برای هرچی که هنوز جواب نگرفته، fallback به ipwho.is
    """
    cache = _load_cache()
    unique_hosts = list(dict.fromkeys(hosts))

    to_query = [h for h in unique_hosts if h not in cache or not _is_fresh(cache[h])]
    from_cache = [h for h in unique_hosts if h in cache and _is_fresh(cache[h])]

    print(f"🗺️  GeoIP: {len(from_cache)} از کش، {len(to_query)} نیاز به کوئری جدید.")

    batches = [to_query[i:i + BATCH_SIZE] for i in range(0, len(to_query), BATCH_SIZE)]
    for i, batch in enumerate(batches):
        fresh_results = _query_batch_ip_api(batch)
        cache.update(fresh_results)
        # تاخیر بین batch ها برای رعایت rate-limit — بعد از آخرین batch لازم نیست
        if i < len(batches) - 1:
            time.sleep(config.GEOIP_BATCH_DELAY_SECONDS)

    # هرچی که هنوز (بعد از ip-api) جواب نگرفته، یک بار دیگه با ipwho.is امتحان می‌شه
    still_missing = [h for h in to_query if h not in cache]
    fallback_results = _query_fallback_ipwhois(still_missing)
    cache.update(fallback_results)

    _save_cache(cache)
    return cache


def detect_countries(scored_configs: list[tuple[str, int]]) -> list[tuple[str, int, str, str]]:
    """
    ورودی: [(config_line, score), ...]
    خروجی: [(config_line, score, country_code, country_name), ...]
    کانفیگ‌هایی که کشورشون پیدا نشه (حتی بعد از fallback)، با کد "XX"
    و اسم "Unknown" برمی‌گردن (تا توی formatter.py زیر دسته‌ی 🌍 All قرار بگیرن).
    """
    hosts = [get_host(line) for line, _ in scored_configs]
    cache = _resolve_hosts([h for h in hosts if h])

    output: list[tuple[str, int, str, str]] = []
    for (line, score), host in zip(scored_configs, hosts):
        entry = cache.get(host) if host else None
        if entry:
            output.append((line, score, entry["code"], entry["name"]))
        else:
            output.append((line, score, "XX", "Unknown"))

    return output
