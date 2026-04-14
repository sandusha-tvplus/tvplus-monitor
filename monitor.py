"""
ТВ+ Агент конкурентной разведки
================================
Собирает с сайтов, Telegram и VK конкурентов:
  - изменения тарифов и цен
  - анонсы нового контента
  - новости компаний
  - акции и промо

Запуск:
  py monitor.py                  — обычный запуск (только новые события)
  py monitor.py --force          — показать всё найденное (игнорировать кэш)
  py monitor.py --no-ai          — без категоризации через Claude API
  py monitor.py --only telegram  — только Telegram-каналы
  py monitor.py --competitor megogo ivi  — только выбранные конкуренты

Результат: reports/дайджест_YYYY-MM-DD_HH-MM.txt
"""
import argparse
import io
import logging
import sys
import time
from datetime import datetime

# Фикс кодировки для Windows-консоли
if sys.stdout.encoding and sys.stdout.encoding.lower() in ("cp1251", "cp866"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import config_monitor as config
from competitor_scrapers.websites import WebsiteScraper
from competitor_scrapers.telegram_web import TelegramWebScraper
from competitor_scrapers.vk_web import VKWebScraper
from change_detector import ChangeDetector
from ai_categorizer import AICategorizer
from digest_builder import DigestBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

BANNER = """
+==============================================================+
|        TV+ AGENT KONKURENTNOY RAZVEDKI                       |
|        Sajty + Telegram + VKontakte => Dajdzhest            |
+==============================================================+
"""


def run(
    force: bool = False,
    no_ai: bool = False,
    only_source: str = "",
    competitors_filter: list = None,
) -> int:
    print(BANNER)
    run_dt = datetime.now()

    # Инициализация
    web_scraper = WebsiteScraper(timeout=config.REQUEST_TIMEOUT_SEC)
    tg_scraper  = TelegramWebScraper(timeout=config.REQUEST_TIMEOUT_SEC)
    vk_scraper  = VKWebScraper(timeout=config.REQUEST_TIMEOUT_SEC)
    detector    = ChangeDetector(state_dir=config.STATE_DIR)
    categorizer = AICategorizer(api_key=config.ANTHROPIC_API_KEY)
    builder     = DigestBuilder()

    # Фильтр конкурентов
    competitors = config.COMPETITORS
    if competitors_filter:
        competitors = {k: v for k, v in competitors.items() if k in competitors_filter}
        if not competitors:
            logger.error(f"Конкуренты не найдены: {competitors_filter}")
            return 1

    all_items = []
    logger.info(f"Конкурентов для мониторинга: {len(competitors)}")

    for key, comp in competitors.items():
        name = comp["name"]
        logger.info(f"\n{'─'*50}")
        logger.info(f"▶  {name}")

        # 1. Сайты
        if not only_source or only_source == "website":
            for url in comp.get("website_urls", []):
                logger.info(f"   🌐 Сайт: {url}")
                try:
                    items = web_scraper.scrape_url(key, name, url)
                    logger.info(f"      Найдено: {len(items)}")
                    all_items.extend(items)
                except Exception as e:
                    logger.warning(f"      Ошибка: {e}")
                time.sleep(config.REQUEST_DELAY_SEC)

        # 2. Telegram
        if not only_source or only_source == "telegram":
            for channel in comp.get("telegram_channels", []):
                logger.info(f"   ✈  Telegram: @{channel}")
                try:
                    items = tg_scraper.scrape_channel(key, name, channel)
                    logger.info(f"      Найдено: {len(items)}")
                    all_items.extend(items)
                except Exception as e:
                    logger.warning(f"      Ошибка: {e}")
                time.sleep(config.REQUEST_DELAY_SEC)

        # 3. VKontakte
        if not only_source or only_source == "vk":
            for group in comp.get("vk_groups", []):
                logger.info(f"   👥 VK: {group}")
                try:
                    items = vk_scraper.scrape_group(key, name, group)
                    logger.info(f"      Найдено: {len(items)}")
                    all_items.extend(items)
                except Exception as e:
                    logger.warning(f"      Ошибка: {e}")
                time.sleep(config.REQUEST_DELAY_SEC)

    logger.info(f"\n{'─'*50}")
    logger.info(f"Всего собрано элементов: {len(all_items)}")

    # 4. Фильтр изменений
    if force:
        new_items = all_items
        logger.info("--force: фильтр изменений отключён — показываю всё")
    else:
        logger.info("Фильтрую уже виденные элементы...")
        new_items = detector.filter_new(all_items)

    logger.info(f"Новых событий: {len(new_items)}")

    if not new_items:
        logger.info("✅ Новых событий не обнаружено.")
        text = builder.build([], run_dt)
        path = builder.save(text, config.REPORTS_DIR)
        logger.info(f"Пустой дайджест сохранён: {path.resolve()}")
        return 0

    # 5. Категоризация через Claude API
    if not no_ai and config.ANTHROPIC_API_KEY:
        logger.info(f"\nКатегоризация {len(new_items)} элементов через Claude API...")
        categorizer.categorize(new_items)
    else:
        if no_ai:
            logger.info("--no-ai: пропускаем категоризацию")
        else:
            logger.warning("ANTHROPIC_API_KEY не задан — добавьте ключ в config_monitor.py")
        for item in new_items:
            item.category = "OTHER"

    # 6. Статистика по категориям
    from collections import Counter
    cats = Counter(item.category for item in new_items)
    logger.info("\n📊 Категории:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        logger.info(f"   {cat}: {count}")

    # 7. Генерация дайджеста
    text = builder.build(new_items, run_dt)
    path = builder.save(text, config.REPORTS_DIR)
    logger.info(f"\n✅ Дайджест сохранён: {path.resolve()}")

    # Печатаем дайджест в консоль
    print("\n" + text)

    # 8. Отправка в Telegram (если настроен)
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_IDS:
        logger.info(f"Отправка в Telegram ({len(config.TELEGRAM_CHAT_IDS)} получателей)...")
        import json as _json
        import urllib.request as _urllib
        tg_url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        msg = text[:4000] + ("\n..." if len(text) > 4000 else "")
        for chat_id in config.TELEGRAM_CHAT_IDS:
            try:
                data = _json.dumps({"chat_id": chat_id, "text": msg}).encode()
                req = _urllib.Request(tg_url, data=data,
                                      headers={"Content-Type": "application/json"})
                with _urllib.urlopen(req, timeout=15) as resp:
                    logger.info(f"  → {chat_id}: {resp.status}")
            except Exception as e:
                logger.warning(f"  → {chat_id}: ошибка — {e}")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ТВ+ Агент конкурентной разведки",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Показать всё найденное (игнорировать кэш виденных элементов)"
    )
    parser.add_argument(
        "--no-ai", action="store_true",
        help="Не использовать Claude API (все элементы попадут в OTHER)"
    )
    parser.add_argument(
        "--only", choices=["website", "telegram", "vk"], default="",
        help="Мониторить только выбранный тип источника"
    )
    parser.add_argument(
        "--competitor", nargs="+", metavar="SLUG",
        help=f"Мониторить только выбранных конкурентов. Доступны: {', '.join(config.COMPETITORS.keys())}"
    )
    args = parser.parse_args()
    sys.exit(run(
        force=args.force,
        no_ai=args.no_ai,
        only_source=args.only,
        competitors_filter=args.competitor,
    ))
