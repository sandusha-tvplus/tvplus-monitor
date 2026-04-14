"""
Детектор изменений: сравнивает свежие находки с ранее виденными.
Состояние хранится в JSON-файлах (один файл на конкурента).
"""
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
MAX_SEEN_IDS = 500


class ChangeDetector:
    def __init__(self, state_dir: str = "state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)

    def filter_new(self, items: list) -> list:
        """Возвращает только элементы, не виденные в прошлых запусках."""
        by_competitor: dict[str, list] = {}
        for item in items:
            by_competitor.setdefault(item.source_key, []).append(item)

        new_items = []
        for key, group in by_competitor.items():
            state = self._load(key)
            seen = set(state["seen_ids"])
            fresh = [item for item in group if item.item_id not in seen]
            new_items.extend(fresh)

            # Обновляем состояние
            updated_seen = list(seen | {item.item_id for item in fresh})
            if len(updated_seen) > MAX_SEEN_IDS:
                updated_seen = updated_seen[-MAX_SEEN_IDS:]
            state["seen_ids"] = updated_seen
            state["last_run"] = datetime.now().isoformat()
            self._save(key, state)
            logger.info(f"  {key}: {len(group)} найдено, {len(fresh)} новых")

        return new_items

    def _load(self, key: str) -> dict:
        path = self.state_dir / f"{key}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"last_run": None, "seen_ids": []}

    def _save(self, key: str, state: dict) -> None:
        path = self.state_dir / f"{key}.json"
        path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
