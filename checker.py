"""
checker.py
امتیازدهی کیفیت کانفیگ‌ها بر اساس ویژگی‌های پروتکل (بدون تست اتصال).

⚠️ این نسخه دیگر هیچ تست زنده‌بودنی (نه TCP، نه UDP) انجام نمی‌ده.
تست TCP قبلی حذف شد چون گمراه‌کننده بود: باز بودن پورت هیچ تضمینی
نمی‌داد که پروتکل واقعاً کار می‌کنه (مخصوصاً پشت CDN/reality که TCP
handshake موفق می‌شه ولی خود پروکسی جواب نمی‌ده)، و false negative
هم برای hysteria2/tuic (که UDP هستن) ایجاد می‌کرد.

نتیجه: همه‌ی کانفیگ‌های ورودی، بدون فیلتر، فقط بر اساس امتیاز پروتکل
(reality/tls/grpc/hysteria2/tuic از QUALITY_BONUS در config.py) مرتب
و برگردونده می‌شن. یعنی کانفیگ‌های کاملاً مرده/آفلاین هم ممکنه در خروجی
نهایی ظاهر بشن، تا وقتی یک تست اتصال واقعی (مثلاً با xray) جایگزینش بشه.
"""

import config
from utils import decode_vmess


def _detect_features(line: str) -> set[str]:
    """ویژگی‌های کانفیگ (reality/tls/grpc/...) رو برای امتیازدهی تشخیص می‌ده."""
    features: set[str] = set()
    scheme = line.split("://")[0]

    if scheme in ("hysteria2", "hy2"):
        features.add("hysteria2")
    if scheme == "tuic":
        features.add("tuic")

    lowered = line.lower()
    if "security=reality" in lowered or "reality" in lowered:
        features.add("reality")
    if "security=tls" in lowered or "tls=1" in lowered:
        features.add("tls")
    if "type=grpc" in lowered or "grpc" in lowered:
        features.add("grpc")

    if scheme == "vmess":
        data = decode_vmess(line)
        if data:
            if str(data.get("tls", "")).lower() in ("tls", "1", "true"):
                features.add("tls")
            if str(data.get("net", "")).lower() == "grpc":
                features.add("grpc")

    return features


def _score(features: set[str]) -> int:
    return sum(config.QUALITY_BONUS.get(f, 0) for f in features)


def check_quality(configs: list[str]) -> list[tuple[str, int]]:
    """
    هر کانفیگ رو صرفاً بر اساس ویژگی‌هاش امتیازدهی می‌کنه، بدون هیچ تست
    اتصالی. خروجی: [(config_line, score), ...] — مرتب‌شده نزولی بر اساس
    امتیاز. هیچ کانفیگی در این مرحله رد نمی‌شه.
    """
    results = [(line, _score(_detect_features(line))) for line in configs]
    results.sort(key=lambda item: item[1], reverse=True)
    return results
