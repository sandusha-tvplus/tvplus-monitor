"""
Построитель дайджеста конкурентной разведки.
Чистый, компактный формат — одна строка на событие.
"""
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CATEGORY_ICONS = {
    "ТАРИФ":   "💰",
    "АКЦИЯ":   "🎁",
    "КОНТЕНТ": "🎬",
    "НОВОСТЬ": "📰",
    "OTHER":   "📌",
}
CATEGORY_NAMES = {
    "ТАРИФ":   "ТАРИФЫ И ЦЕНЫ",
    "АКЦИЯ":   "АКЦИИ И ПРОМО",
    "КОНТЕНТ": "НОВЫЙ КОНТЕНТ",
    "НОВОСТЬ": "НОВОСТИ КОМПАНИЙ",
    "OTHER":   "ПРОЧЕЕ",
}
CATEGORY_ORDER = ["ТАРИФ", "АКЦИЯ", "КОНТЕНТ", "НОВОСТЬ", "OTHER"]
SOURCE_ICONS = {"website": "🌐", "telegram": "✈", "vk": "👥", "youtube": "▶️"}
MONTHS_RU = ["января","февраля","марта","апреля","мая","июня",
             "июля","августа","сентября","октября","ноября","декабря"]


class DigestBuilder:

    def build(self, items: list, run_dt: datetime) -> str:
        date_ru = f"{run_dt.day} {MONTHS_RU[run_dt.month-1]} {run_dt.year}"
        lines = []

        # ── Шапка ──────────────────────────────────────────────
        lines += [
            f"📊 ДАЙДЖЕСТ КОНКУРЕНТНОЙ РАЗВЕДКИ — ТВ+",
            f"📅 {date_ru}  |  Новых событий: {len(items)}",
            "",
        ]

        if not items:
            lines.append("Новых событий не обнаружено.")
            return "\n".join(lines)

        # ── Группировка по категориям ───────────────────────────
        by_cat: dict[str, list] = {cat: [] for cat in CATEGORY_ORDER}
        for item in items:
            cat = item.category if item.category in by_cat else "OTHER"
            by_cat[cat].append(item)

        for cat in CATEGORY_ORDER:
            group = by_cat[cat]
            if not group:
                continue

            icon = CATEGORY_ICONS[cat]
            name = CATEGORY_NAMES[cat]
            lines.append(f"{icon} {name} ({len(group)})")
            lines.append("─" * 40)

            for item in group:
                src_icon = SOURCE_ICONS.get(item.source_type, "•")
                # Дата — только дата без времени
                date_str = ""
                if item.date_hint:
                    date_str = f"  {item.date_hint[:10]}"

                # Название источника + иконка источника
                lines.append(f"{src_icon} {item.source_name}{date_str}")

                # Заголовок — одна строка, максимум 80 символов
                title = item.title.strip()
                if len(title) > 80:
                    title = title[:77] + "..."
                if title:
                    lines.append(f"   {title}")

                # Ссылка — только если есть
                if item.url:
                    lines.append(f"   🔗 {item.url}")

                lines.append("")  # пустая строка между событиями

        # ── Итог ───────────────────────────────────────────────
        counts = {cat: len(by_cat[cat]) for cat in CATEGORY_ORDER}
        parts = []
        if counts["ТАРИФ"]:   parts.append(f"💰 тарифов: {counts['ТАРИФ']}")
        if counts["АКЦИЯ"]:   parts.append(f"🎁 акций: {counts['АКЦИЯ']}")
        if counts["КОНТЕНТ"]: parts.append(f"🎬 контента: {counts['КОНТЕНТ']}")
        if counts["НОВОСТЬ"]: parts.append(f"📰 новостей: {counts['НОВОСТЬ']}")
        if counts["OTHER"]:   parts.append(f"📌 прочее: {counts['OTHER']}")

        lines += [
            "─" * 40,
            "  ".join(parts),
            f"⏰ {run_dt.strftime('%d.%m.%Y %H:%M')}",
        ]

        return "\n".join(lines)

    def save(self, text: str, reports_dir: str = "reports") -> Path:
        Path(reports_dir).mkdir(exist_ok=True)
        dt_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
        path = Path(reports_dir) / f"дайджест_{dt_str}.txt"
        path.write_text(text, encoding="utf-8")
        return path
