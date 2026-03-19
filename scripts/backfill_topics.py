"""
Одноразовый скрипт: создать Telegram-топики для существующих пользователей Baserow.

Запуск из корня проекта:
    python scripts/backfill_topics.py

Требования:
- Бот должен быть администратором форум-группы ADMIN_CHAT_ID с правом manage_topics.
- .env должен содержать BASEROW_URL, BASEROW_TOKEN, BASEROW_TABLE_ID.
- Пропускает строки, у которых topic_id уже заполнен.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import aiohttp
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

import config
from config.crm import BASEROW_TABLE_ID, BASEROW_TOKEN, BASEROW_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("backfill")

_F_TELEGRAM_ID       = "field_3556"
_F_TELEGRAM_USERNAME = "field_3557"
_F_FIRST_NAME        = "field_3559"
_F_BROKER_ID         = "field_3560"
_F_STATUS            = "field_3561"
_F_CREATED_AT        = "field_3562"
_F_LAST_EVENT        = "field_3563"
_F_TOPIC_ID          = "field_7458"

ROWS_URL = f"{BASEROW_URL}/api/database/rows/table/{BASEROW_TABLE_ID}/"
HEADERS = {
    "Authorization": f"Token {BASEROW_TOKEN}",
    "Content-Type": "application/json",
}

# Пауза между созданием топиков (сек) — избегаем Telegram flood
DELAY_BETWEEN_TOPICS = 5.0


def _str(val) -> str:
    if val is None:
        return ""
    if isinstance(val, dict):
        return str(val.get("value", "") or "")
    return str(val)


async def fetch_all_rows(session: aiohttp.ClientSession) -> list[dict]:
    """Загрузить все строки из Baserow постранично."""
    rows = []
    page = 1
    page_size = 200
    while True:
        async with session.get(
            ROWS_URL,
            headers=HEADERS,
            params={"size": page_size, "page": page},
        ) as resp:
            if resp.status != 200:
                logger.error("Baserow error: %s %s", resp.status, await resp.text())
                break
            data = await resp.json()
            batch = data.get("results", [])
            rows.extend(batch)
            if len(batch) < page_size:
                break
            page += 1
    return rows


async def save_topic_id(
    session: aiohttp.ClientSession, row_id: int, topic_id: int
) -> bool:
    url = f"{ROWS_URL}{row_id}/"
    async with session.patch(
        url, headers=HEADERS, json={_F_TOPIC_ID: topic_id}
    ) as resp:
        if resp.status != 200:
            logger.warning(
                "Failed to save topic_id for row %s: %s", row_id, await resp.text()
            )
            return False
        return True


def build_card(row: dict) -> str:
    first_name = _str(row.get(_F_FIRST_NAME)) or "—"
    username = _str(row.get(_F_TELEGRAM_USERNAME))
    telegram_id = row.get(_F_TELEGRAM_ID) or "—"
    status = _str(row.get(_F_STATUS)) or "—"
    broker_id = _str(row.get(_F_BROKER_ID)) or "—"
    created_at = _str(row.get(_F_CREATED_AT)) or "—"
    last_event = _str(row.get(_F_LAST_EVENT)) or "—"

    username_str = f"@{username}" if username else "нет username"

    return (
        f"📋 Карточка пользователя\n"
        f"👤 {first_name} ({username_str})\n"
        f"🆔 ID: {telegram_id}\n"
        f"📌 Статус: {status}\n"
        f"🏦 Broker ID: {broker_id}\n"
        f"📅 Дата регистрации: {created_at}\n"
        f"🔔 Последнее событие: {last_event}\n"
        f"\n— данные из CRM на момент создания топика —"
    )


async def main() -> None:
    bot = Bot(token=config.BOT_TOKEN)

    async with aiohttp.ClientSession() as session:
        logger.info("Загружаю пользователей из Baserow...")
        rows = await fetch_all_rows(session)
        logger.info("Всего строк: %d", len(rows))

        without_topic = [
            r for r in rows
            if not r.get(_F_TOPIC_ID)
        ]
        logger.info("Без topic_id: %d", len(without_topic))

        if not without_topic:
            logger.info("Все пользователи уже имеют топик. Выход.")
            await bot.session.close()
            return

        created = 0
        failed = 0

        for row in without_topic:
            row_id = row["id"]
            telegram_id = row.get(_F_TELEGRAM_ID)
            first_name = _str(row.get(_F_FIRST_NAME)) or "Без имени"
            username = _str(row.get(_F_TELEGRAM_USERNAME))

            topic_name = f"{first_name}"
            if username:
                topic_name += f" (@{username})"
            topic_name += f" | ID: {telegram_id}"
            # Telegram ограничивает имя топика 128 символами
            topic_name = topic_name[:128]

            try:
                result = await bot.create_forum_topic(
                    chat_id=config.ADMIN_CHAT_ID,
                    name=topic_name,
                )
                topic_id = result.message_thread_id

                card = build_card(row)
                await bot.send_message(
                    chat_id=config.ADMIN_CHAT_ID,
                    message_thread_id=topic_id,
                    text=card,
                )

                saved = await save_topic_id(session, row_id, topic_id)
                if saved:
                    logger.info(
                        "OK  row=%d topic=%d user=%s", row_id, topic_id, telegram_id
                    )
                    created += 1
                else:
                    logger.warning(
                        "WARN topic создан (%d) но не сохранён для row=%d",
                        topic_id,
                        row_id,
                    )
                    failed += 1

            except TelegramAPIError as e:
                logger.warning("TG error row=%d: %s", row_id, e)
                failed += 1
            except Exception as e:
                logger.warning("Error row=%d: %s", row_id, e)
                failed += 1

            await asyncio.sleep(DELAY_BETWEEN_TOPICS)

    await bot.session.close()
    logger.info("Готово. Создано: %d, ошибок: %d", created, failed)


if __name__ == "__main__":
    asyncio.run(main())
