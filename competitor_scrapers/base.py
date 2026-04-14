"""
Базовый класс и структуры данных для всех парсеров конкурентов.
"""
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,kk;q=0.8",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Cookie": "remixlang=0",  # VK: русский язык без редиректов
}


@dataclass
class ScrapedItem:
    """Одна находка разведки — запись с сайта, Telegram или VK."""
    source_key: str       # slug конкурента, напр. "megogo"
    source_name: str      # название, напр. "Megogo KZ"
    source_type: str      # "website" | "telegram" | "vk"
    source_url: str       # URL страницы
    text: str             # текст находки
    title: str = ""       # заголовок (если найден)
    date_hint: str = ""   # строка даты, если есть рядом
    url: str = ""         # прямая ссылка на элемент
    item_id: str = ""     # SHA-256 хэш для дедупликации
    category: str = ""    # заполняется позже через Claude

    def __post_init__(self):
        if not self.item_id:
            raw = f"{self.source_key}|{self.source_type}|{self.title}|{self.text[:200]}"
            self.item_id = hashlib.sha256(raw.encode()).hexdigest()[:16]


class BaseScraper:
    def __init__(self, timeout: int = 20):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.timeout = timeout

    def get(self, url: str, **kwargs) -> Optional[BeautifulSoup]:
        try:
            resp = self.session.get(url, timeout=self.timeout, **kwargs)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
        except requests.RequestException as e:
            logger.warning(f"Ошибка запроса {url}: {e}")
            return None
