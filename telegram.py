"""
telegram.py
جمع‌آوری کانفیگ از آخرین پیام‌های کانال‌های عمومی تلگرام با Telethon.
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

import config
from utils import extract_configs_from_text


def fetch_from_telegram(channels: list[str]) -> list[str]:
    """
    به تلگرام وصل می‌شه، آخرین پیام‌های هر کانال رو می‌خونه و کانفیگ‌ها
    رو استخراج می‌کنه. اگه یه کانال خطا بده (مثلاً حذف شده یا بلاک شده)،
    از کانال بعدی ادامه می‌ده و کل اجرا رو متوقف نمی‌کنه.
    """
    configs: list[str] = []

    with TelegramClient(
        StringSession(config.TG_SESSION), config.TG_API_ID, config.TG_API_HASH
    ) as client:
        for channel in channels:
            try:
                count = 0
                for message in client.iter_messages(channel, limit=config.MESSAGES_PER_CHANNEL):
                    if not message.text:
                        continue
                    found = extract_configs_from_text(message.text)
                    configs.extend(found)
                    count += len(found)
                print(f"✅ {count} کانفیگ از @{channel}")
            except Exception as e:
                print(f"⚠️  خطا تو کانال @{channel}: {e}")

    return configs
