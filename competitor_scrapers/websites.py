"""
Парсер сайтов конкурентов: тарифы, новости, анонсы.
"""
import logging
import re
from .base import BaseScraper, ScrapedItem

logger = logging.getLogger(__name__)

PRICE_RE = re.compile(r"\d[\d\s]*(?:тг|₸|руб|tenge|kzt)", re.IGNORECASE)

TARIFF_SELECTORS = [
    "[class*='tariff']", "[class*='plan']", "[class*='price']",
    "[class*='subscription']", "[class*='package']",
    "[class*='тариф']", "table",
]

NEWS_SELECTORS = [
    "article", "[class*='news']", "[class*='post']",
    "[class*='card']", "[class*='item']", "[class*='blog']",
]


class WebsiteScraper(BaseScraper):

    def scrape_url(self, competitor_key: str, competitor_name: str,
                   url: str) -> list:
        soup = self.get(url)
        if soup is None:
            return []

        url_lower = url.lower()
        if any(kw in url_lower for kw in ("tariff", "price", "plan",
                                           "subscription", "тариф", "подписк")):
            items = self._extract_tariff_items(soup, competitor_key, competitor_name, url)
        elif any(kw in url_lower for kw in ("news", "blog", "новост", "пресс")):
            items = self._extract_news_items(soup, competitor_key, competitor_name, url)
        else:
            items = self._extract_news_items(soup, competitor_key, competitor_name, url)
            if not items:
                items = self._extract_tariff_items(soup, competitor_key, competitor_name, url)

        return items

    def _extract_tariff_items(self, soup, key, name, url) -> list:
        results = []
        seen_texts = set()

        for selector in TARIFF_SELECTORS:
            try:
                blocks = soup.select(selector)
            except Exception:
                continue
            for block in blocks[:30]:
                text = block.get_text(" ", strip=True)
                if len(text) < 10:
                    continue
                if not PRICE_RE.search(text) and "тариф" not in text.lower():
                    continue
                text_key = text[:100]
                if text_key in seen_texts:
                    continue
                seen_texts.add(text_key)
                heading = block.find(["h1", "h2", "h3", "h4", "strong"])
                title = heading.get_text(strip=True) if heading else text[:60]
                results.append(ScrapedItem(
                    source_key=key, source_name=name,
                    source_type="website", source_url=url,
                    text=text[:500], title=title,
                ))
            if results:
                break

        return results

    def _extract_news_items(self, soup, key, name, url) -> list:
        results = []
        seen = set()

        for selector in NEWS_SELECTORS:
            try:
                blocks = soup.select(selector)
            except Exception:
                continue
            for block in blocks[:30]:
                heading = block.find(["h1", "h2", "h3", "h4"])
                if not heading:
                    continue
                title = heading.get_text(strip=True)
                if not title or len(title) < 5 or title in seen:
                    continue
                seen.add(title)
                text = block.get_text(" ", strip=True)[:500]
                link = block.find("a")
                item_url = ""
                if link and link.get("href"):
                    href = link["href"]
                    if href.startswith("http"):
                        item_url = href
                    elif href.startswith("/"):
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        item_url = f"{parsed.scheme}://{parsed.netloc}{href}"
                date_el = block.find(attrs={"class": lambda c: c and any(
                    w in str(c).lower() for w in ["date", "time", "дата", "число"])})
                date_hint = date_el.get_text(strip=True) if date_el else ""
                results.append(ScrapedItem(
                    source_key=key, source_name=name,
                    source_type="website", source_url=url,
                    text=text, title=title, url=item_url, date_hint=date_hint,
                ))
            if results:
                break

        return results
