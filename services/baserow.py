"""Модуль для работы с Baserow API (CRM)."""

import json
import logging
from datetime import datetime, timedelta, timezone

import aiohttp

import config
from config.crm import (
    BASEROW_TABLE_ID,
    BASEROW_TOKEN,
    BASEROW_URL,
    BASEROW_LAST_SUPPORT_MESSAGE_FIELD_ID,
)

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
_F_TOPIC_ID          = "field_7458"
_F_LAST_SUPPORT_MSG  = BASEROW_LAST_SUPPORT_MESSAGE_FIELD_ID if BASEROW_LAST_SUPPORT_MESSAGE_FIELD_ID else None


def _field_to_str(val) -> str:
    """Baserow select/date fields can return dict (e.g. {value: 'x'}). Extract string."""
    if val is None:
        return ""
    if isinstance(val, dict):
        return str(val.get("value", "") or "")
    return str(val)


def row_to_user_dict(row: dict) -> dict:
    """Преобразовать строку Baserow в формат для CRM менеджера (публичный для crm_service)."""
    result = {
        "id": row.get("id"),
        "telegram_id": row.get(_F_TELEGRAM_ID),
        "telegram_username": _field_to_str(row.get(_F_TELEGRAM_USERNAME)),
        "first_name": _field_to_str(row.get(_F_FIRST_NAME)),
        "broker_id": _field_to_str(row.get(_F_BROKER_ID)),
        "status": _field_to_str(row.get(_F_STATUS)),
        "created_at": _field_to_str(row.get(_F_CREATED_AT)),
    }
    if _F_LAST_SUPPORT_MSG:
        result["last_support_message"] = _field_to_str(row.get(_F_LAST_SUPPORT_MSG)) or None
    else:
        result["last_support_message"] = None
    return result


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


async def get_user_by_topic_id(topic_id: int) -> dict | None:
    """
    Получить пользователя по topic_id.
    Перебирает все страницы результатов.
    """
    if not _is_configured():
        return None

    page_size = 200
    page_num = 1
    try:
        async with aiohttp.ClientSession() as session:
            while True:
                params = {"size": page_size, "page": page_num}
                async with session.get(
                    _rows_url(),
                    headers=_headers(),
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            "Baserow get_user_by_topic_id: status %s, body %s",
                            resp.status,
                            await resp.text(),
                        )
                        return None
                    data = await resp.json()
                    results = data.get("results", [])
                    # Логируем topic_id значения для диагностики (первая страница)
                    if page_num == 1:
                        sample = [row.get(_F_TOPIC_ID) for row in results[:5]]
                        logger.warning("Baserow get_user_by_topic_id: looking for %s, sample topic_ids=%s", topic_id, sample)
                    for row in results:
                        val = row.get(_F_TOPIC_ID)
                        if val is not None and val != "":
                            try:
                                if int(val) == int(topic_id):
                                    return row
                            except (ValueError, TypeError):
                                pass
                    if len(results) < page_size:
                        return None
                    page_num += 1
    except Exception as e:
        logger.warning("Baserow get_user_by_topic_id error: %s", e)
        return None


async def get_topic_id(telegram_id: int) -> int | None:
    """
    Получить topic_id по telegram_id.
    Вызывает get_user_by_telegram_id, возвращает int(row[_F_TOPIC_ID]) или None.
    """
    row = await get_user_by_telegram_id(telegram_id)
    if row is None:
        return None
    val = row.get(_F_TOPIC_ID)
    if val is None or val == "":
        return None
    try:
        val_int = int(val)
        return val_int if val_int > 0 else None
    except (ValueError, TypeError):
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


async def update_last_support_message(row_id: int, text: str) -> bool:
    """Сохранить текст последнего сообщения в поддержку. Работает только если задан BASEROW_LAST_SUPPORT_MESSAGE_FIELD_ID."""
    if not _F_LAST_SUPPORT_MSG or not _is_configured():
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                _row_url(row_id),
                headers=_headers(),
                json={_F_LAST_SUPPORT_MSG: (text or "")[:10000]},
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Baserow update_last_support_message: status %s, body %s",
                        resp.status,
                        await resp.text(),
                    )
                    return False
                logger.info("Baserow last_support_message saved for row %s", row_id)
                return True
    except Exception as e:
        logger.warning("Baserow update_last_support_message error: %s", e)
        return False


async def set_topic_id(row_id: int, topic_id: int) -> bool:
    """Обновить topic_id для строки."""
    if not _is_configured():
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(
                _row_url(row_id),
                headers=_headers(),
                json={_F_TOPIC_ID: topic_id},
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Baserow set_topic_id: status %s, body %s",
                        resp.status,
                        await resp.text(),
                    )
                    return False
                logger.info("CRM: topic_id saved → %s", topic_id)
                return True
    except Exception as e:
        logger.warning("Baserow set_topic_id error: %s", e)
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


async def get_total_rows_count() -> int:
    """
    Получить общее количество строк в таблице.
    Baserow возвращает count в ответе на list-запрос.
    """
    if not _is_configured():
        return 0

    try:
        async with aiohttp.ClientSession() as session:
            params = {"size": 1}
            async with session.get(
                _rows_url(),
                headers=_headers(),
                params=params,
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Baserow get_total_rows_count: status %s, body %s",
                        resp.status,
                        await resp.text(),
                    )
                    return 0
                data = await resp.json()
                return int(data.get("count", 0))
    except Exception as e:
        logger.warning("Baserow get_total_rows_count error: %s", e)
        return 0


async def get_count_by_status(status: str) -> int:
    """
    Количество строк с заданным статусом.
    Перебирает все страницы и считает совпадения в Python (Baserow не поддерживает
    server-side фильтр по полю select без явного filter__fieldN синтаксиса).
    """
    if not _is_configured():
        return 0

    page_size = 200
    page_num = 1
    total = 0

    try:
        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "size": page_size,
                    "page": page_num,
                }
                async with session.get(
                    _rows_url(),
                    headers=_headers(),
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            "Baserow get_count_by_status: status %s, body %s",
                            resp.status,
                            await resp.text(),
                        )
                        break
                    data = await resp.json()
                    results = data.get("results", [])
                    for row in results:
                        if _field_to_str(row.get(_F_STATUS)) == str(status):
                            total += 1
                    if len(results) < page_size:
                        break
                    page_num += 1
        return total
    except Exception as e:
        logger.warning("Baserow get_count_by_status error: %s", e)
        return 0


def _parse_created_at(val) -> datetime | None:
    """
    Парсит created_at из Baserow (date "YYYY-MM-DD" или datetime ISO).
    Возвращает datetime в UTC или None.
    """
    if val is None:
        return None
    raw = _field_to_str(val) if isinstance(val, dict) else str(val)
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        pass
    try:
        dt = datetime.strptime(raw[:10], "%Y-%m-%d")
        return dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


async def get_users_by_status(status: str, limit: int = 200, offset: int = 0) -> list[dict]:
    """
    Получить пользователей по статусу.
    ORDER BY created_at DESC. Фильтрация по status в Python.
    Пагинация: fetch все страницы, фильтр, slice[offset:offset+limit].
    """
    if not _is_configured():
        return []

    page_size = 200
    try:
        async with aiohttp.ClientSession() as session:
            all_results: list[dict] = []
            page_num = 1
            while True:
                params = {
                    "order_by": f"-{_F_CREATED_AT}",
                    "size": page_size,
                    "page": page_num,
                }
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
                        break
                    data = await resp.json()
                    page_results = data.get("results", [])
                    all_results.extend(page_results)
                    if len(page_results) < page_size:
                        break
                    page_num += 1
            users = [
                row_to_user_dict(row)
                for row in all_results
                if _field_to_str(row.get(_F_STATUS)) == str(status)
            ]
            return users[offset : offset + limit]
    except Exception as e:
        logger.warning("Baserow get_users_by_status error: %s", e)
        return []


async def get_users_created_after_24h(limit: int = 10, offset: int = 0) -> list[dict]:
    """
    Пользователи, созданные за последние 24 часа.
    ORDER BY created_at DESC. Фильтрация по дате в Python.
    Пагинация: перебираем все страницы API, затем применяем offset/limit.
    """
    if not _is_configured():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    page_size = 200
    page_num = 1
    filtered: list[dict] = []

    try:
        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "order_by": f"-{_F_CREATED_AT}",
                    "size": page_size,
                    "page": page_num,
                }
                async with session.get(
                    _rows_url(),
                    headers=_headers(),
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            "Baserow get_users_created_after_24h: status %s, body %s",
                            resp.status,
                            await resp.text(),
                        )
                        break
                    data = await resp.json()
                    results = data.get("results", [])
                    for row in results:
                        dt = _parse_created_at(row.get(_F_CREATED_AT))
                        if dt is not None and dt >= cutoff:
                            filtered.append(row_to_user_dict(row))
                        elif dt is not None and dt < cutoff:
                            # rows are DESC by created_at — no more matches possible
                            return filtered[offset : offset + limit]
                    if len(results) < page_size:
                        break
                    page_num += 1
        return filtered[offset : offset + limit]
    except Exception as e:
        logger.warning("Baserow get_users_created_after_24h error: %s", e)
        return []


async def get_new_leads_count() -> int:
    """Количество пользователей, созданных за последние 24 часа."""
    if not _is_configured():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    total = 0
    page_num = 1
    page_size = 200

    try:
        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "order_by": f"-{_F_CREATED_AT}",
                    "size": page_size,
                    "page": page_num,
                }
                async with session.get(
                    _rows_url(),
                    headers=_headers(),
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        break
                    data = await resp.json()
                    results = data.get("results", [])
                    if not results:
                        break
                    page_count = 0
                    for row in results:
                        dt = _parse_created_at(row.get(_F_CREATED_AT))
                        if dt is not None and dt >= cutoff:
                            page_count += 1
                        else:
                            return total + page_count
                    total += page_count
                    if len(results) < page_size:
                        break
                    page_num += 1
        return total
    except Exception as e:
        logger.warning("Baserow get_new_leads_count error: %s", e)
        return total


async def get_recent_users(limit: int = 20, offset: int = 0) -> list[dict]:
    """
    Получить последних пользователей по дате создания (для CRM-панели).
    ORDER BY created_at DESC. Поддержка пагинации.
    Baserow использует page (с 1), offset конвертируется в номер страницы.
    """
    if not _is_configured():
        return []

    page_num = (offset // limit) + 1 if limit > 0 else 1

    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "order_by": f"-{_F_CREATED_AT}",
                "size": limit,
                "page": page_num,
            }
            async with session.get(
                _rows_url(),
                headers=_headers(),
                params=params,
            ) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Baserow get_recent_users: status %s, body %s",
                        resp.status,
                        await resp.text(),
                    )
                    return await _get_recent_users_fallback(limit, offset)
                data = await resp.json()
                results = data.get("results", [])
                return [row_to_user_dict(row) for row in results]
    except Exception as e:
        logger.warning("Baserow get_recent_users error: %s", e)
        return await _get_recent_users_fallback(limit, offset)


_LEADS_EXCLUDE_STATUSES = {
    "Broker ID получен",
    "Ожидаем депозит",
    "Ожидаем Broker ID",
    "Сообщение в поддержку",
    "Доступ выдан",
    "Отклонен",
    "Спам",
}

_BROADCAST_LEAD_STATUSES = {
    "Новый пользователь",
    "Начал регистрацию",
    "Ожидаем Broker ID",
}


async def get_leads_telegram_ids_for_broadcast() -> list[int]:
    """Все telegram_id лидов для рассылки (без pagination limit)."""
    if not _is_configured():
        return []

    page_size = 200
    page_num = 1
    result: list[int] = []

    try:
        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "order_by": f"-{_F_CREATED_AT}",
                    "size": page_size,
                    "page": page_num,
                }
                async with session.get(
                    _rows_url(),
                    headers=_headers(),
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            "Baserow get_leads_telegram_ids_for_broadcast: status %s, body %s",
                            resp.status,
                            await resp.text(),
                        )
                        break
                    data = await resp.json()
                    results = data.get("results", [])
                    for row in results:
                        if _field_to_str(row.get(_F_STATUS)) in _BROADCAST_LEAD_STATUSES:
                            val = row.get(_F_TELEGRAM_ID)
                            if val is not None and val != "":
                                try:
                                    result.append(int(val))
                                except (ValueError, TypeError):
                                    pass
                    if len(results) < page_size:
                        break
                    page_num += 1
        return result
    except Exception as e:
        logger.warning("Baserow get_leads_telegram_ids_for_broadcast error: %s", e)
        return []


async def get_leads_users(limit: int = 200, offset: int = 0) -> list[dict]:
    """
    Лиды — все строки, чей статус не входит в список финальных/клиентских статусов.
    Пагинация: fetch все страницы по 200, фильтр в Python, slice[offset:offset+limit].
    """
    if not _is_configured():
        return []

    page_size = 200
    page_num = 1
    filtered: list[dict] = []

    try:
        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "order_by": f"-{_F_CREATED_AT}",
                    "size": page_size,
                    "page": page_num,
                }
                async with session.get(
                    _rows_url(),
                    headers=_headers(),
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            "Baserow get_leads_users: status %s, body %s",
                            resp.status,
                            await resp.text(),
                        )
                        break
                    data = await resp.json()
                    results = data.get("results", [])
                    for row in results:
                        if _field_to_str(row.get(_F_STATUS)) not in _LEADS_EXCLUDE_STATUSES:
                            filtered.append(row)
                    if len(results) < page_size:
                        break
                    page_num += 1
        return [row_to_user_dict(row) for row in filtered][offset : offset + limit]
    except Exception as e:
        logger.warning("Baserow get_leads_users error: %s", e)
        return []


async def get_leads_count() -> int:
    """Количество лидов (строки, не входящие в финальные/клиентские статусы)."""
    if not _is_configured():
        return 0

    page_size = 200
    page_num = 1
    total = 0

    try:
        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    "size": page_size,
                    "page": page_num,
                }
                async with session.get(
                    _rows_url(),
                    headers=_headers(),
                    params=params,
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            "Baserow get_leads_count: status %s, body %s",
                            resp.status,
                            await resp.text(),
                        )
                        break
                    data = await resp.json()
                    results = data.get("results", [])
                    for row in results:
                        if _field_to_str(row.get(_F_STATUS)) not in _LEADS_EXCLUDE_STATUSES:
                            total += 1
                    if len(results) < page_size:
                        break
                    page_num += 1
        return total
    except Exception as e:
        logger.warning("Baserow get_leads_count error: %s", e)
        return 0


async def _get_recent_users_fallback(limit: int, offset: int = 0) -> list[dict]:
    """Fallback: fetch 200 rows, sort by created_at desc, return slice."""
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
                    return []
                data = await resp.json()
                results = data.get("results", [])
                sorted_rows = sorted(
                    results,
                    key=lambda r: r.get(_F_CREATED_AT) or "",
                    reverse=True,
                )
                slice_rows = sorted_rows[offset : offset + limit]
                return [row_to_user_dict(row) for row in slice_rows]
    except Exception as e:
        logger.warning("Baserow get_recent_users fallback error: %s", e)
        return []
