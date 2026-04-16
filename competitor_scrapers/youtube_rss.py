"""
YouTube RSS-парсер: забирает последние видео канала без API ключа.
YouTube бесплатно отдаёт Atom-фид для любого публичного канала.
URL фида: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
"""
import logging
import urllib.request
from datetime import datetime
from xml.etree import ElementTree as ET

from .base import ScrapedItem

logger = logging.getLogger(__name__)

YT_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
NS = {
    "atom":  "http://www.w3.org/2005/Atom",
    "yt":    "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}


class YouTubeRssScraper:
    """Scraper для YouTube-каналов через публичный Atom/RSS фид."""

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

    def scrape_channel(self, competitor_key: str, competitor_name: str,
                       channel_id: str) -> list:
        url = YT_FEED_URL.format(channel_id=channel_id)
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; TVplusBot/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                xml_bytes = resp.read()
        except Exception as e:
            logger.warning(f"YouTube RSS {channel_id}: ошибка загрузки — {e}")
            return []

        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            logger.warning(f"YouTube RSS {channel_id}: ошибка XML — {e}")
            return []

        items = []
        entries = root.findall("atom:entry", NS)

        for entry in entries[:20]:  # берём последние 20 видео
            title_el = entry.find("atom:title", NS)
            link_el  = entry.find("atom:link[@rel='alternate']", NS)
            pub_el   = entry.find("atom:published", NS)
            desc_el  = entry.find("media:group/media:description", NS)

            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            video_url = link_el.get("href", "") if link_el is not None else ""
            date_hint = ""
            if pub_el is not None and pub_el.text:
                try:
                    dt = datetime.fromisoformat(pub_el.text.replace("Z", "+00:00"))
                    date_hint = dt.strftime("%Y-%m-%d")
                except ValueError:
                    date_hint = pub_el.text[:10]

            description = ""
            if desc_el is not None and desc_el.text:
                description = desc_el.text.strip()[:300]

            if not title:
                continue

            text = description or title

            items.append(ScrapedItem(
                source_key=competitor_key,
                source_name=competitor_name,
                source_type="youtube",
                source_url=f"https://www.youtube.com/channel/{channel_id}",
                text=text,
                title=title,
                url=video_url,
                date_hint=date_hint,
            ))

        logger.debug(f"YouTube @{channel_id}: найдено {len(items)} видео")
        return items
