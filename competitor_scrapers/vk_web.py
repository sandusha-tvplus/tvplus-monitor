"""
Парсер публичных групп ВКонтакте через vk.com/{group}
Не требует VK API-ключа — только публичные группы.
"""
import logging
from .base import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)


class VKWebScraper(BaseScraper):
    BASE_URL = "https://vk.com/{group}"

    def scrape_group(self, competitor_key: str, competitor_name: str,
                     group: str) -> list:
        url = self.BASE_URL.format(group=group)
        soup = self.get(url)
        if soup is None:
            return []

        items = []
        posts = soup.select("div.post, div._post, div[class*='wall_post']")

        if not posts:
            logger.warning(f"VK {group}: посты не найдены (возможно JS-рендеринг)")
            return []

        for post in posts[:25]:
            text_el = post.select_one(
                ".wall_post_text, [class*='post_text'], [class*='wall_text']")
            if not text_el:
                continue
            text = text_el.get_text(" ", strip=True)
            if len(text) < 15:
                continue

            date_el = post.select_one(".post__date, time, [class*='date']")
            date_hint = date_el.get_text(strip=True) if date_el else ""

            link_el = post.select_one("a[href*='/wall']")
            if link_el and link_el.get("href", "").startswith("/"):
                post_url = "https://vk.com" + link_el["href"]
            else:
                post_url = url

            title = (text.split(".")[0][:80] if "." in text else text[:80]).strip()

            items.append(ScrapedItem(
                source_key=competitor_key,
                source_name=competitor_name,
                source_type="vk",
                source_url=url,
                text=text[:600],
                title=title,
                date_hint=date_hint,
                url=post_url,
            ))

        return items
