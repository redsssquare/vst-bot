"""Вспомогательные функции форматирования."""

from datetime import datetime


def format_datetime(raw: str | None) -> str:
    """Форматирует ISO datetime из Baserow в DD.MM.YYYY HH:MM."""
    if not raw:
        return "—"
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except (ValueError, TypeError):
        return raw
