"""Модуль для работы с Baserow API (CRM)."""

import json
import logging
from datetime import datetime

import aiohttp

import config
from config.crm import BASEROW_TABLE_ID, BASEROW_TOKEN, BASEROW_URL

logger = logging.getLogger(__name__)

# Маппинг полей таблицы 378
# GET /api/database/fields/table/378/ → id, name
_F_TELEGRAM_ID       = "field_3556"
_F_TELEGRAM_USERNAME = "field_3557"
_F_FIRST_NAME        = "field_3559"
_F_BROKER_ID         = "field_3560"
_F_STATUS            = "field_3561"
_F_CREATED_AT        = "field_3562"
_F_LAST_EVENT        = "field_3563"


def _row_to_user_dict(row: dict) -> dict:
    """Преобразовать строку Baserow в формат для CRM менеджера."""
    return {
        "telegram_id": row.get(_F_TELEGRAM_ID),
        "telegram_username": row.get(_F_TELEGRAM_USERNAME) or "",
        "first_name": row.get(_F_FIRST_NAME) or "",
        "broker_id": row.get(_F_BROKER_ID) or "",
        "status": row.get(_F_STATUS) or "",
    }


def _is_configured() -> bool:
    return bool(BASEROW_URL and BASEROW_TOKEN and BASEROW_TABLE_ID)


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Token {BASEROW_TOKEN}",
        "Content-Type": "application/json",
    }


def _rows_url() -> str:
    return f"{BASEROW_URL}/api/database/rows/table/{BASEROW_TABLE_ID}/"


def _row_url(row_id: int) -> str:
    return f"{_rows_url()}{row_id}/"


async def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    """
    Получить пользователя по telegram_id.
    GET с перебором результатов, возвращает первую найденную строку или None.
    """
    if not _is_configured():
        return None

    try:
        async with aiohttp.ClientSession() as session:
            params = {"size": 200}
            async with session.get(
                _rows_url(),
                headers=_headers(),
                params=params,
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Baserow get_user_by_telegram_id: status %s, body %s",
                        resp.status,
                        await resp.text(),
                    )
                    return None
                data = await resp.json()
                results = data.get("results", [])
                for row in results:
                    if str(row.get(_F_TELEGRAM_ID)) == str(telegram_id):
                        return row
                return None
    except Exception as e:
        logger.warning("Baserow get_user_by_telegram_id error: %s", e)
        return None


async def create_user(
    telegram_id: int,
    telegram_username: str,
    first_name: str,
    status: str = "Новый пользователь",
    last_event: str = "start",
    created_at: str | None = None,
) -> dict | None:
    """
    Создать пользователя в таблице users.
    POST с field_ID (не именами полей).
    """
    if not _is_configured():
        return None

    if created_at is None:
        created_at = datetime.utcnow().strftime("%Y-%m-%d")

    payload = {
        _F_TELEGRAM_ID:       telegram_id,
        _F_TELEGRAM_USERNAME: telegram_username or "",
        _F_FIRST_NAME:        first_name or "",
        _F_STATUS:            status,
        _F_LAST_EVENT:        last_event or "",
        _F_CREATED_AT:        created_at,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                _rows_url(),
                headers=_headers(),
                json=payload,
            ) as resp:
                body = await resp.text()
                if resp.status not in (200, 201):
                    logger.warning(
                        "Baserow create_user: status %s, body %s",
                        resp.status,
                        body,
                    )
                    return None
                try:
                    result = json.loads(body) if body else None
                    if result:
                        logger.info("CRM: user created %s", telegram_id)
                    return result
                except json.JSONDecodeError:
                    return None
    except Exception as e:
        logger.warning("Baserow create_user error: %s", e)
        return None


async def update_status(
    row_id: int,
    status: str,
    last_event: str | None = None,
) -> bool:
    """Обновить status и опционально last_event."""
    if not _is_configured():
        return False

    payload: dict = {_F_STATUS: status}
    if last_event is not None:
        payload[_F_LAST_EVENT] = last_event

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                _row_url(row_id),
                headers=_headers(),
                json=payload,
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Baserow update_status: status %s, body %s",
                        resp.status,
                        await resp.text(),
                    )
                    return False
                logger.info("CRM: status updated → %s", status)
                return True
    except Exception as e:
        logger.warning("Baserow update_status error: %s", e)
        return False


async def update_broker_id(row_id: int, broker_id: str) -> bool:
    """
    Обновить broker_id, status и last_event.
    После записи: status = "Broker ID получен", last_event = "broker_id_received".
    """
    if not _is_configured():
        return False

    payload = {
        _F_BROKER_ID: broker_id,
        _F_STATUS: config.STATUS_BROKER_ID_RECEIVED,
        _F_LAST_EVENT: "broker_id_received",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                _row_url(row_id),
                headers=_headers(),
                json=payload,
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Baserow update_broker_id: status %s, body %s",
                        resp.status,
                        await resp.text(),
                    )
                    return False
                logger.info("CRM: broker_id saved → %s", broker_id)
                return True
    except Exception as e:
        logger.warning("Baserow update_broker_id error: %s", e)
        return False


async def log_event(row_id: int, last_event: str) -> bool:
    """Обновить только last_event."""
    if not _is_configured():
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                _row_url(row_id),
                headers=_headers(),
                json={_F_LAST_EVENT: last_event},
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Baserow log_event: status %s, body %s",
                        resp.status,
                        await resp.text(),
                    )
                    return False
                logger.info("CRM: event logged → %s", last_event)
                return True
    except Exception as e:
        logger.warning("Baserow log_event error: %s", e)
        return False


async def get_users_by_status(status: str) -> list[dict]:
    """
    Получить пользователей по статусу.
    Для будущей CRM-панели менеджера.
    """
    if not _is_configured():
        return []

    try:
        async with aiohttp.ClientSession() as session:
            params = {"size": 200}
            async with session.get(
                _rows_url(),
                headers=_headers(),
                params=params,
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Baserow get_users_by_status: status %s, body %s",
                        resp.status,
                        await resp.text(),
                    )
                    return []
                data = await resp.json()
                results = data.get("results", [])
                users = [
                    _row_to_user_dict(row)
                    for row in results
                    if str(row.get(_F_STATUS) or "") == str(status)
                ]
                return users
    except Exception as e:
        logger.warning("Baserow get_users_by_status error: %s", e)
        return []
