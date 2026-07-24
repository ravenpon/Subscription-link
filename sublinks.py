"""
sublinks.py
جمع‌آوری کانفیگ از لینک‌های Subscription (SUB_LINKS در config.py).
پشتیبانی می‌کنه از:
    - لینک‌هایی که محتواشون مستقیم Base64 کل ساب هست
    - لینک‌هایی که محتواشون متن ساده (هر خط یه کانفیگ) هست
    - لینک‌های Raw GitHub / فایل‌های TXT (که از نظر ما فرقی با بالا ندارن،
      چون در نهایت با یه GET ساده محتوای متنی برمی‌گردونن)
"""

import base64

import requests

import config
from utils import extract_configs_from_text

REQUEST_TIMEOUT = 15


def _looks_like_base64(text: str) -> bool:
    """
    تشخیص می‌ده که آیا محتوای دریافتی خودش یه بلاک Base64 از کل ساب هست
    یا از قبل متن ساده (شامل vless://, vmess:// و ...) هست.
    """
    stripped = text.strip()
    if stripped.startswith(config.VALID_PREFIXES):
        return False
    return True


def _decode_sub_content(text: str) -> str:
    """اگه محتوا Base64 بود دیکدش می‌کنه، وگرنه همون‌طور که هست برمی‌گردونه."""
    if not _looks_like_base64(text):
        return text
    try:
        padded = text.strip() + "=" * (-len(text.strip()) % 4)
        return base64.b64decode(padded).decode("utf-8", errors="ignore")
    except Exception:
        # اگه دیکد نشد، شاید از اول متن ساده بوده ولی فرمتش عجیب بود؛
        # متن خام رو برمی‌گردونیم تا extract_configs_from_text خودش تلاش کنه.
        return text


def fetch_from_sublinks(sub_links: list[str]) -> list[str]:
    """
    هر لینک ساب رو دانلود می‌کنه، دیکد (در صورت نیاز) و کانفیگ‌ها رو
    استخراج می‌کنه. تعداد کانفیگ گرفته‌شده از هر لینک به
    MAX_CONFIGS_PER_SUBLINK محدود می‌شه تا یه منبع بزرگ کل پول رو پر نکنه.
    اگه یه لینک خطا بده، از لینک بعدی ادامه می‌ده.
    """
    all_configs: list[str] = []

    for link in sub_links:
        try:
            resp = requests.get(link, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            decoded = _decode_sub_content(resp.text)
            found = extract_configs_from_text(decoded)

            limited = found[: config.MAX_CONFIGS_PER_SUBLINK]
            all_configs.extend(limited)
            print(f"✅ {len(limited)} کانفیگ از {link} (از {len(found)} تای موجود)")
        except Exception as e:
            print(f"⚠️  خطا تو لینک ساب {link}: {e}")

    return all_configs
