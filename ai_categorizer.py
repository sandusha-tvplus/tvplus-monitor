"""
Категоризация находок через Claude API.
Использует claude-haiku (быстрый и дешёвый) для классификации по категориям.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"ТАРИФ", "КОНТЕНТ", "НОВОСТЬ", "АКЦИЯ", "OTHER"}

SYSTEM_PROMPT = """Ты — аналитик конкурентной разведки для казахстанского стримингового сервиса ТВ+.
Тебе дают список находок, собранных с сайтов, Telegram-каналов и VK-групп конкурентов.
Для каждой находки определи категорию:

ТАРИФ   — изменение тарифов, цен, планов подписки, стоимости
КОНТЕНТ — анонс нового контента: фильмы, сериалы, шоу, трансляции
НОВОСТЬ — корпоративная новость: партнёрства, руководство, финансы, технологии
АКЦИЯ   — акция, скидка, промокод, специальное предложение, розыгрыш
OTHER   — не подходит ни под одну из вышеперечисленных категорий

Верни ТОЛЬКО валидный JSON-массив вида:
[{"id": "...", "category": "ТАРИФ", "reason": "кратко на русском"}, ...]

Не добавляй никакого текста до или после JSON."""


class AICategorizer:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def categorize(self, items: list) -> list:
        """Категоризирует элементы батчами по 20. Изменяет .category на месте."""
        if not items:
            return items
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY не задан — категории не определяются (OTHER)")
            for item in items:
                item.category = "OTHER"
            return items

        BATCH_SIZE = 20
        for i in range(0, len(items), BATCH_SIZE):
            batch = items[i:i + BATCH_SIZE]
            logger.info(f"  Claude: батч {i // BATCH_SIZE + 1} ({len(batch)} эл.)")
            self._categorize_batch(batch)

        return items

    def _categorize_batch(self, batch: list) -> None:
        payload = [
            {
                "id": item.item_id,
                "source": item.source_name,
                "channel": item.source_type,
                "title": item.title[:120],
                "text": item.text[:300],
            }
            for item in batch
        ]

        user_msg = (
            "Категоризируй следующие "
            + str(len(batch))
            + " находок:\n\n"
            + json.dumps(payload, ensure_ascii=False, indent=2)
        )

        try:
            client = self._get_client()
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw = response.content[0].text.strip()
            # Убираем markdown-обёртку, если Claude добавил
            if raw.startswith("```"):
                parts = raw.split("\n", 1)
                raw = parts[1] if len(parts) > 1 else raw
                raw = raw.rsplit("```", 1)[0]
            results = json.loads(raw)
        except Exception as e:
            logger.warning(f"Claude API ошибка: {e} — ставлю OTHER для батча")
            for item in batch:
                item.category = "OTHER"
            return

        id_to_result = {r["id"]: r for r in results if isinstance(r, dict)}
        for item in batch:
            result = id_to_result.get(item.item_id, {})
            cat = result.get("category", "OTHER")
            item.category = cat if cat in VALID_CATEGORIES else "OTHER"
