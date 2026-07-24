"""
main.py
نقطه‌ی شروع پروژه RAVVPN2.
این فایل فقط جریان کار (workflow) رو مدیریت می‌کنه؛ منطق هر بخش
توی ماژول اختصاصی خودش پیاده‌سازی می‌شه:

    telegram.py   -> جمع‌آوری کانفیگ از کانال‌های تلگرام
    sublinks.py   -> جمع‌آوری کانفیگ از لینک‌های Subscription
    utils.py      -> پاک‌سازی، حذف تکراری، استخراج host/port
    checker.py    -> تست زنده بودن و کیفیت سرورها
    geoip.py      -> تشخیص کشور سرورها (با کش)
    formatter.py  -> تغییر نام کانفیگ‌ها + دسته‌بندی کشوری + نوشتن خروجی‌ها
"""

import json
import os

import config
from telegram import fetch_from_telegram
from sublinks import fetch_from_sublinks
from utils import clean_and_dedupe
from checker import check_quality
from geoip import detect_countries
from formatter import build_outputs


def collect_raw_configs() -> list[str]:
    """کانفیگ خام رو از همه‌ی منابع (تلگرام + لینک‌های ساب) جمع می‌کنه."""
    configs: list[str] = []

    telegram_configs = fetch_from_telegram(config.TELEGRAM_CHANNELS)
    print(f"📥 {len(telegram_configs)} کانفیگ از تلگرام گرفته شد.")
    configs.extend(telegram_configs)

    sub_configs = fetch_from_sublinks(config.SUB_LINKS)
    print(f"📥 {len(sub_configs)} کانفیگ از لینک‌های ساب گرفته شد.")
    configs.extend(sub_configs)

    return configs


def load_published_history() -> set[str]:
    """
    کانفیگ‌های منتشرشده در اجرای قبلی رو می‌خونه (اگه فایلی وجود داشته باشه).
    فقط آخرین اجرا نگه داشته می‌شه؛ نبودن فایل یا خراب بودنش خطا محسوب نمی‌شه
    (مثلاً اولین اجرای پروژه) و صرفاً یک ست خالی برمی‌گردونه.
    """
    if not os.path.exists(config.PUBLISHED_HISTORY_FILE):
        return set()
    try:
        with open(config.PUBLISHED_HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        print("⚠️ فایل تاریخچه‌ی کانفیگ‌های منتشرشده خراب بود؛ نادیده گرفته شد.")
        return set()


def filter_previously_published(
    cleaned_configs: list[str], history: set[str]
) -> list[str]:
    """
    کانفیگ‌هایی که کل رشته‌شون دقیقاً با اجرای قبلی یکی باشه رو حذف می‌کنه
    (فیچر تنوع تاریخچه)، تا در دو اجرای پیاپی عین همون کانفیگ تکرار نشه.
    """
    if not history:
        return cleaned_configs
    filtered = [c for c in cleaned_configs if c not in history]
    removed = len(cleaned_configs) - len(filtered)
    if removed:
        print(f"🔁 {removed} کانفیگ چون عیناً در اجرای قبلی منتشر شده بود حذف شد.")
    return filtered


def main():
    raw_configs = collect_raw_configs()
    if not raw_configs:
        print("❌ هیچ کانفیگی از هیچ منبعی گرفته نشد. فایل‌های قبلی دست‌نخورده می‌مونن.")
        return

    cleaned_configs = clean_and_dedupe(raw_configs)
    print(f"🧹 بعد از پاک‌سازی: {len(cleaned_configs)} کانفیگ یکتا.")

    history = load_published_history()
    cleaned_configs = filter_previously_published(cleaned_configs, history)

    candidate_pool = cleaned_configs[: config.RAW_POOL_SIZE]
    print(f"🔎 در حال تست کیفیت {len(candidate_pool)} کانفیگ (از سقف {config.RAW_POOL_SIZE}).")

    scored_configs = check_quality(candidate_pool)
    print(f"💚 {len(scored_configs)} کانفیگ سالم و امتیازدهی‌شده باقی موند.")

    if not scored_configs:
        print("❌ هیچ کانفیگ سالمی پیدا نشد. فایل‌های قبلی دست‌نخورده می‌مونن.")
        return

    geo_configs = detect_countries(scored_configs)

    build_outputs(geo_configs)
    print("🎉 خروجی‌ها با موفقیت ساخته و ذخیره شدن.")


if __name__ == "__main__":
    main()
