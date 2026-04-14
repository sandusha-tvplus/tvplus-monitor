"""
Парсер публичных Telegram-каналов через https://t.me/s/{channel}
Не требует API-ключа — только публичные каналы.
"""
import logging
from .base import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)


class TelegramWebScraper(BaseScraper):
    BASE_URL = "https://t.me/s/{channel}"

    def scrape_channel(self, competitor_key: str, competitor_name: str,
                       channel: str) -> list:
        url = self.BASE_URL.format(channel=channel)
        soup = self.get(url)
        if soup is None:
            return []

        items = []
        posts = soup.select(".tgme_widget_message_wrap")

        if not posts:
            logger.warning(f"Telegram @{channel}: посты не найдены (канал закрыт или не существует)")
            return []

        for post in posts[:30]:
            text_el = post.select_one(".tgme_widget_message_text")
            if not text_el:
                continue
            text = text_el.get_text(" ", strip=True)
            if len(text) < 15:
                continue

            date_el = post.select_one("time")
            date_hint = date_el.get("datetime", "") if date_el else ""

            link_el = post.select_one(".tgme_widget_message_date")
            post_url = link_el.get("href", url) if link_el else url

            title = (text.split(".")[0][:80] if "." in text else text[:80]).strip()

            items.append(ScrapedItem(
                source_key=competitor_key,
                source_name=competitor_name,
                source_type="telegram",
                source_url=url,
                text=text[:600],
                title=title,
                date_hint=date_hint,
                url=post_url,
            ))

        return items
