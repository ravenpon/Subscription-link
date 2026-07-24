"""
geoip.py
تشخیص کشور هر سرور با سرویس رایگان ip-api.com، به‌همراه یه کش محلی
(geoip_cache.json) تا بین اجراهای پی‌درپی هر ۳۰ دقیقه، IPهای تکراری
دوباره کوئری نشن.

خروجی: هر کانفیگ به‌صورت (line, score, country_code, country_name)
برمی‌گرده تا formatter.py بتونه هم دسته‌بندی کشوری کنه، هم بر اساس
امتیاز مرتب‌سازی نگه داره.
"""

import json
import os
import time

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


def _query_batch(hosts: list[str]) -> dict:
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
        print(f"⚠️  خطا تو درخواست GeoIP: {e}")
    return result


def _resolve_hosts(hosts: list[str]) -> dict:
    """کشور هر هاست رو برمی‌گردونه؛ اول از کش، بعد برای بقیه از ip-api.com."""
    cache = _load_cache()
    unique_hosts = list(dict.fromkeys(hosts))

    to_query = [h for h in unique_hosts if h not in cache or not _is_fresh(cache[h])]
    from_cache = [h for h in unique_hosts if h in cache and _is_fresh(cache[h])]

    print(f"🗺️  GeoIP: {len(from_cache)} از کش، {len(to_query)} نیاز به کوئری جدید.")

    for i in range(0, len(to_query), BATCH_SIZE):
        batch = to_query[i:i + BATCH_SIZE]
        fresh_results = _query_batch(batch)
        cache.update(fresh_results)

    _save_cache(cache)
    return cache


def detect_countries(scored_configs: list[tuple[str, int]]) -> list[tuple[str, int, str, str]]:
    """
    ورودی: [(config_line, score), ...]
    خروجی: [(config_line, score, country_code, country_name), ...]
    کانفیگ‌هایی که کشورشون پیدا نشه، با کد "XX" و اسم "Unknown" برمی‌گردن
    (تا توی formatter.py زیر دسته‌ی 🌍 All قرار بگیرن).
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
