"""
checker.py
تست زنده بودن سرورها (TCP) و امتیازدهی کیفیت بر اساس ویژگی‌های کانفیگ.

نسخه‌ی فعلی: تست TCP ساده (مرحله‌ی ۱). این فقط تضمین می‌کنه پورت بازه،
نه اینکه پروتکل واقعاً کار می‌کنه یا کانفیگ فیلترشکنه. مرحله‌ی بعدی
(اجرای واقعی xray + درخواست HTTP از طریق پروکسی) بعداً جایگزین یا
تکمیل‌کننده‌ی این تست می‌شه.

⚠️ محدودیت شناخته‌شده: hysteria2/hy2 و tuic روی UDP کار می‌کنن، نه TCP.
تست TCP فعلی برای این پروتکل‌ها همیشه شکست می‌خوره (false negative).
فعلاً این‌ها رو صرفاً بر اساس امتیاز پروتکل عبور می‌دیم، بدون تست اتصال واقعی،
تا وقتی تست UDP اختصاصی اضافه بشه.
"""

import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from utils import get_host, get_port, decode_vmess

UDP_PROTOCOLS = ("hysteria2://", "hy2://", "tuic://")


def _check_tcp_alive(host: str, port: int) -> bool:
    """با یه اتصال TCP ساده بررسی می‌کنه سرور بالاست یا نه."""
    if not host or not port:
        return False
    try:
        with socket.create_connection((host, port), timeout=config.PING_TIMEOUT):
            return True
    except Exception:
        return False


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
    هر کانفیگ رو تست می‌کنه و در صورت زنده بودن، همراه با امتیاز کیفیتش
    برمی‌گردونه: [(config_line, score), ...] — مرتب‌شده نزولی بر اساس امتیاز.

    برای پروتکل‌های UDP-based (hysteria2/tuic) چون تست TCP معنی نداره،
    فعلاً بدون تست اتصال، فقط بر اساس امتیاز عبور داده می‌شن.
    """
    results: list[tuple[str, int]] = []

    tcp_candidates = [c for c in configs if not c.startswith(UDP_PROTOCOLS)]
    udp_candidates = [c for c in configs if c.startswith(UDP_PROTOCOLS)]

    with ThreadPoolExecutor(max_workers=config.PING_WORKERS) as executor:
        futures = {}
        for line in tcp_candidates:
            host, port = get_host(line), get_port(line)
            futures[executor.submit(_check_tcp_alive, host, port)] = line
        for future in as_completed(futures):
            line = futures[future]
            if future.result():
                score = _score(_detect_features(line))
                results.append((line, score))

    for line in udp_candidates:
        score = _score(_detect_features(line))
        results.append((line, score))

    results.sort(key=lambda item: item[1], reverse=True)
    return results
