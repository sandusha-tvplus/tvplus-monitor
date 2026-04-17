"""
Настройки агента конкурентной разведки.
Заполните ANTHROPIC_API_KEY и (опционально) Telegram-токен.
"""
import os

# ─── API ключи (задайте через переменные среды или впишите напрямую) ──────────
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY")  or "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"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or "7843475309:AAH_sU7iMVB_3RWuCI2phFK2yeQpZGeZWZg"

# Список получателей дайджеста (можно добавлять сколько угодно)
TELEGRAM_CHAT_IDS = [
    "376325725",   # Sandugash (@Doogash)
    "7051308076",  # @a_ru_ana
    "1063629300",  # @b_alright
]

# ─── Папки ───────────────────────────────────────────────────────────────────
STATE_DIR   = "state"    # JSON-файлы состояния (кэш виденных элементов)
REPORTS_DIR = "reports"  # Сохранённые дайджесты

# ─── HTTP параметры ───────────────────────────────────────────────────────────
REQUEST_DELAY_SEC   = 2.0  # пауза между запросами (вежливый краулинг)
REQUEST_TIMEOUT_SEC = 20

# ─── Конкуренты ──────────────────────────────────────────────────────────────
# Для каждого конкурента:
#   website_urls      — список URL (страницы тарифов и новостей)
#   telegram_channels — список username публичных Telegram-каналов
#   vk_groups         — список username публичных VK-групп
COMPETITORS = {
    "megogo": {
        "name": "Megogo KZ",
        "website_urls": [
            "https://megogo.net/kz/",
            "https://megogo.net/kz/subscriptions.html",
        ],
        "telegram_channels": ["megogonet"],
        "vk_groups": ["megogo"],
        "youtube_channels": [],
    },
    "ivi": {
        "name": "Ivi",
        "website_urls": [
            "https://www.ivi.ru/",
            "https://www.ivi.ru/subscribe/",
        ],
        "telegram_channels": ["ivi_official"],
        "vk_groups": ["ivi"],
        "youtube_channels": [],
    },
    "kinopoisk": {
        "name": "Кинопоиск HD",
        "website_urls": [
            "https://www.kinopoisk.ru/",
        ],
        "telegram_channels": ["kinopoisk"],
        "vk_groups": ["kinopoisk"],
        "youtube_channels": [],
    },
    "almaplus": {
        "name": "Alma Plus",
        "website_urls": [
            "https://almaplus.kz/",
            "https://almaplus.kz/ru/",
        ],
        "telegram_channels": ["almaplus_kz"],
        "vk_groups": [],
        "youtube_channels": [],
    },
    "unicoplay": {
        "name": "Unicoplay",
        "website_urls": [
            "https://unicoplay.kz/",
        ],
        "telegram_channels": ["unicoplay_kz"],
        "vk_groups": [],
        "youtube_channels": [],
    },
    "beeline_tv": {
        "name": "Beeline TV KZ",
        "website_urls": [
            "https://beeline.kz/",
        ],
        "telegram_channels": ["beeline_kz"],
        "vk_groups": ["beelinekazakhstan"],
        "youtube_channels": [],
    },
    "freedom": {
        "name": "Freedom Media",
        "website_urls": [
            "https://freedommedia.kz/news/",
        ],
        "telegram_channels": ["freedommediakz"],
        "vk_groups": [],
        "youtube_channels": [],
    },
    "start": {
        "name": "Start.ru",
        "website_urls": [
            "https://start.ru/",
        ],
        "telegram_channels": ["startru"],
        "vk_groups": ["startru"],
        "youtube_channels": [],
    },
    "wink": {
        "name": "Wink (Ростелеком)",
        "website_urls": [
            "https://wink.ru/",
            "https://wink.ru/news/",
        ],
        "telegram_channels": ["wink_ru"],
        "vk_groups": ["winkru"],
        "youtube_channels": [],
    },
    "qube": {
        "name": "Qube (Казахстан)",
        "website_urls": [
            "https://qube.kz/",
            "https://qube.kz/ru/",
        ],
        "telegram_channels": ["qube_kz"],
        "vk_groups": [],
        # YouTube: официальный канал Qube KZ
        "youtube_channels": ["UClmwE5HsBUxYwRSfRQgNr3Q"],
    },
    "amediateka": {
        "name": "Амедиатека",
        "website_urls": [
            "https://www.amediateka.ru/",
            "https://www.amediateka.ru/blog/",
        ],
        "telegram_channels": ["amediateka"],
        "vk_groups": ["amediateka"],
        "youtube_channels": [],
    },
}
