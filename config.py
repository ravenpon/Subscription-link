"""
config.py
همه‌ی تنظیمات ثابت پروژه اینجا نگه داشته می‌شن تا بقیه‌ی ماژول‌ها
منطق و عدد/رشته‌های ثابت رو داخل خودشون هاردکد نکنن.
"""

import os

# ---------------------------------------------------------------------------
# اطلاعات اتصال تلگرام (از GitHub Secrets خونده می‌شه)
# ---------------------------------------------------------------------------
TG_API_ID = int(os.environ["TG_API_ID"])
TG_API_HASH = os.environ["TG_API_HASH"]
TG_SESSION = os.environ["TG_SESSION"]

# ---------------------------------------------------------------------------
# منابع تلگرام
# ---------------------------------------------------------------------------
TELEGRAM_CHANNELS = [
    "UnlimitConfig", "persianvpnhub", "proxy_kafee", "YamYamProxy",
    "JavidanNet", "ConfigFast", "Zed_NetMeli", "erfanandroid",
    "configshere", "cpy_teeL", "MARAMBASHI", "meliproxyy",
    "SRCVPN", "anty_filter", "DailyV2Proxy", "TheFreeConfigs",
    "OpenVpnUser", "Proxy_Station", "GH_v2rayng", "Net2Ray",
    "FreakConfig", "configraygan", "V2RAYROZ", "G0Dv2ray",
    "YamYamProxy2", "chat_naakon", "chat_nakoni", "directvvbh",
    "prrofile_purple", "NPV_78", "vpnplusee_free", "v2ray_free_conf",
    "vpns", "canfigv2ray", "v2ray26", "filembad", "TAK_VPN12",
    "V2rayEnglishGP", "canfige", "OmegaGR", "Dr_Npv", "v2ray_proxyz",
    "Badangellll",
    # کانال‌های اضافه‌شده در مرحله بعد
    "vpnfail_v2ray", "v2raycollector", "surfboardv2ray", "daily_configs",
    "invoProxy", "GalaxyMVPN", "ConfigWireguard", "ConfigV2rayNG",
  "keyline_vless", "V2RayRootFree", "nvpnir", "VEGAAS_VPN", "V2boxnet",
    # دسته‌ی دوم
    "iproxy_Meli", "Diamond_grooup", "Confing_hupp", "proxyy_1404",
    "letsproxys1", "letsproxys2", "PROXIS_FREE", "chatnakonn", "VpnQavi",
    "configraygan_group", "qrmvasl", "LonUp_M", "v2ray_dalghak",
    "ShadowProxy66", "confiiing_chanel", "V2ray_official", "Kingnighttt",
    "GGVPNHOP", "Spotify_Porteghali", "Mrshahabx", "sorenab2",
    "v2rayngvpn", "Outline_Vpn", "configmax", "DarkHub_VPN", "NetAccount",
    "ProxyDotNet", "injector_1401Ehi", "Farsroid_Club",
    "outlinee_vpn",
    "EricVPN",
    "v2ray_youtube_group",
    "v2ray_outlineir",
    "v2rayfresh",
    "proxyconfigss",
    "OutlineVpnPremium",
    "sublinkAndroid",
    "outlinekeys_free",
    "FreeConfigV2ray_1",
    "ShadowsocksM",
    "TrojanL",
    "ShadowSocks_channel",
    "ShadowSocksT",
    "ConfigFreeTest",
    "Masyakata",
    "v2config2",
    "OutlineVpnOfficial",
    "bega_raftimmmm",
    "lenstablegh",
    "VIPVPNAMIR1",
    "hysteria2_panel",
    "hysteria_github",
    "superconfig2",
    "vpn_Click",
    "shadowsocks0",
    "vmessiraan",
    "AzadNet",
    "vaslshavim",
    "V2rayN5",
    "Ghostray_NG",
    "WhatsAppProxyd",
    "v2ray_youtube",
    "net_resan",
    "v2RayTunVPN",
    "V2ray686",
    "bardiav2ray",
    "MEHRAN_VPN",
    "Broz_time",
    "EquMind",
    "dailyv2rayCF",
    "divatoz",
    "polemoftie",
    "azadi55",
    "dev_in_ruby_colors",
    "v2raytun",
    "MraPanel2",
    "QuattroVPN_NEWS",
    "outlines_vpn",
    "V2ProxyIR",
]
MESSAGES_PER_CHANNEL = 80  # چند پیام آخر هر کانال بررسی بشه

# ---------------------------------------------------------------------------
# منابع Subscription
# فقط کافیه اینجا لینک اضافه کنی؛ بقیه کارها خودکاره.
# ---------------------------------------------------------------------------
SUB_LINKS: list[str] = [
    # "https://example.com/sub",
]

# ---------------------------------------------------------------------------
# پروتکل‌های معتبر
# ---------------------------------------------------------------------------
VALID_PREFIXES = ("vless://", "vmess://", "trojan://", "ss://", "ssr://", "hysteria2://", "hy2://", "tuic://")

# ---------------------------------------------------------------------------
# محدودیت تعداد کانفیگ در خروجی نهایی
# ---------------------------------------------------------------------------
MAX_CONFIGS_ALL = 500          # سقف فایل کلی (RVVPN_All)
MAX_CONFIGS_PER_COUNTRY = 100  # سقف هر فایل کشوری
MAX_CONFIGS_PER_SUBLINK = 100  # سقف تعداد کانفیگی که از هر لینک ساب برداشته می‌شه
RAW_POOL_SIZE = 2000           # قبل از تست کیفیت، این تعداد کاندید بررسی می‌شه

# ---------------------------------------------------------------------------
# تنظیمات تست کیفیت
# ---------------------------------------------------------------------------
PING_TIMEOUT = 3
PING_WORKERS = 40

# امتیاز اضافه برای هر ویژگی (هرچی بیشتر، بالاتر توی لیست قرار می‌گیره)
QUALITY_BONUS = {
    "reality": 30,
    "tls": 20,
    "grpc": 15,
    "hysteria2": 25,
    "tuic": 25,
}

# ---------------------------------------------------------------------------
# کشورهای اختصاصی؛ بقیه‌ی کشورها می‌رن زیر دسته "All"
# کلید = کد دو حرفی کشور (ISO 3166-1 alpha-2)
# ---------------------------------------------------------------------------
DEDICATED_COUNTRIES = {
    "DE": "Germany",
    "FR": "France",
    "TR": "Turkey",
    "US": "United States",
    "CA": "Canada",
    "AE": "UAE",
    "RU": "Russia",
    "AM": "Armenia",
    "IR": "Iran",
    "IT": "Italy",
}

# ---------------------------------------------------------------------------
# فرمت اسم برند
# ---------------------------------------------------------------------------
BRAND_FORMAT = "{flag} | RAV VPN • {country} ⚡️"

# این کانفیگ نمایشی هیچ‌وقت وصل نمی‌شه، فقط به‌عنوان یادآوری همیشه ردیف اول لیست می‌مونه
PINNED_NOTICE_CONFIG = (
    "vless://00000000-0000-0000-0000-000000000000@127.0.0.1:1"
    "?security=none&type=tcp"
    "#%E2%9A%A0%EF%B8%8F%20%D9%87%D8%B1%20%D9%86%DB%8C%D9%85%20%D8%B3%D8%A7%D8%B9%D8%AA"
    "%20%D8%A2%D9%BE%D8%AF%DB%8C%D8%AA%20%DA%A9%D9%86%DB%8C%D8%AF%20%E2%9A%A0%EF%B8%8F"
)

# ---------------------------------------------------------------------------
# مسیر فایل‌های خروجی
# ---------------------------------------------------------------------------
OUTPUT_DIR = "output"
OUTPUT_FILES = {
    "all": "RVVPN_All",
}
# فایل‌های کشوری به‌صورت خودکار از روی DEDICATED_COUNTRIES ساخته می‌شن:
# مثلاً RVVPN_Germany, RVVPN_France, ...

# ---------------------------------------------------------------------------
# کش GeoIP (برای جلوگیری از درخواست تکراری به ip-api.com بین اجراهای مختلف)
# ---------------------------------------------------------------------------
GEOIP_CACHE_FILE = "geoip_cache.json"
GEOIP_CACHE_TTL_DAYS = 7  # بعد از این مدت، IP دوباره چک می‌شه
GEOIP_BATCH_DELAY_SECONDS = 4  # تاخیر بین batch های ip-api برای رعایت rate-limit
GEOIP_FALLBACK_WORKERS = 8      # تعداد thread هم‌زمان برای fallback به ipwho.is

# ---------------------------------------------------------------------------
# تاریخچه‌ی کانفیگ‌های منتشرشده (برای جلوگیری از تکرار عین همان کانفیگ
# در دو اجرای پیاپی؛ فقط آخرین اجرا نگه داشته می‌شه، نه بیشتر)
# ---------------------------------------------------------------------------
PUBLISHED_HISTORY_FILE = "published_history.json"
