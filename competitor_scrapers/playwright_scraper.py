"""
Playwright-based scraper: рендерит JavaScript, затем парсит HTML.
Используется как замена requests+BS4 для сайтов с динамическим контентом.

Использование:
    with PlaywrightScraper() as scraper:
        items = scraper.scrape_url(key, name, url)
"""
import logging
from bs4 import BeautifulSoup
from .websites import WebsiteScraper

logger = logging.getLogger(__name__)


class PlaywrightScraper(WebsiteScraper):
    """
    Расширяет WebsiteScraper — использует Playwright (headless Chromium)
    для рендеринга JS-страниц. Всю логику извлечения данных берёт из родителя.
    """

    def __init__(self, timeout: int = 30):
        super().__init__(timeout=timeout)
        self._pw = None
        self._browser = None

    # ── контекстный менеджер ──────────────────────────────────────────────────

    def __enter__(self):
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            logger.info("🌍 Playwright Chromium запущен")
        except Exception as e:
            logger.warning(f"Playwright недоступен: {e} — будет использован requests")
        return self

    def __exit__(self, *_):
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
            logger.info("🌍 Playwright остановлен")
        except Exception:
            pass

    # ── основной метод ────────────────────────────────────────────────────────

    def scrape_url(self, competitor_key: str, competitor_name: str, url: str) -> list:
        """
        1. Пробуем быстрый requests (как раньше).
        2. Если получили 0 результатов — запускаем Playwright.
        """
        # быстрый путь
        items = super().scrape_url(competitor_key, competitor_name, url)
        if items:
            return items

        # Playwright-путь
        if self._browser is None:
            return []

        logger.info(f"      → Playwright (JS-рендеринг)…")
        html = self._render(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        url_lower = url.lower()

        if any(kw in url_lower for kw in
               ("tariff", "price", "plan", "subscription", "тариф", "подписк", "subscribe")):
            items = self._extract_tariff_items(soup, competitor_key, competitor_name, url)
        else:
            items = self._extract_news_items(soup, competitor_key, competitor_name, url)
            if not items:
                items = self._extract_tariff_items(soup, competitor_key, competitor_name, url)

        return items

    # ── вспомогательный рендеринг ─────────────────────────────────────────────

    def _render(self, url: str) -> str | None:
        """Открывает страницу в headless Chromium, ждёт networkidle, возвращает HTML."""
        try:
            ctx = self._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="ru-RU",
                extra_http_headers={"Accept-Language": "ru-RU,ru;q=0.9"},
            )
            page = ctx.new_page()
            page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
            # дополнительное ожидание для ленивой загрузки контента
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass  # networkidle может не случиться — не страшно
            html = page.content()
            page.close()
            ctx.close()
            return html
        except Exception as e:
            logger.warning(f"Playwright рендеринг {url}: {e}")
            return None
