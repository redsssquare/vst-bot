"""CRM Service — обёртки над Baserow для работы с пользователями."""

import asyncio
import logging

import config
from services import baserow

logger = logging.getLogger(__name__)


async def get_new_users(limit: int = 200, offset: int = 0):
    """Пользователи со статусом «Новый пользователь»."""
    return await baserow.get_users_by_status(config.STATUS_NEW, limit=limit, offset=offset)


async def get_waiting_broker_id(limit: int = 200, offset: int = 0):
    """Пользователи со статусом «Ожидаем Broker ID»."""
    return await baserow.get_users_by_status(config.STATUS_WAITING_BROKER_ID, limit=limit, offset=offset)


async def get_support_requests(limit: int = 200, offset: int = 0):
    """Пользователи со статусом «Сообщение в поддержку»."""
    return await baserow.get_users_by_status(config.STATUS_SUPPORT_MESSAGE, limit=limit, offset=offset)


async def get_ready_to_connect(limit: int = 200, offset: int = 0):
    """Пользователи со статусом «Broker ID получен» (Готовы к подключению)."""
    return await baserow.get_users_by_status(config.STATUS_BROKER_ID_RECEIVED, limit=limit, offset=offset)


async def get_new_leads_24h(limit: int = 10, offset: int = 0):
    """Пользователи, созданные за последние 24 часа."""
    return await baserow.get_users_created_after_24h(limit=limit, offset=offset)


async def get_new_leads_count() -> int:
    """Количество пользователей, созданных за последние 24 часа."""
    return await baserow.get_new_leads_count()


async def get_recent_users(limit: int = 20, offset: int = 0):
    """Последние пользователи по дате создания."""
    return await baserow.get_recent_users(limit, offset)


async def get_waiting_count() -> int:
    """Количество пользователей «Ожидаем Broker ID»."""
    return await baserow.get_count_by_status(config.STATUS_WAITING_BROKER_ID)


async def get_ready_count() -> int:
    """Количество пользователей «Broker ID получен» (Готовы к подключению)."""
    return await baserow.get_count_by_status(config.STATUS_BROKER_ID_RECEIVED)


async def get_new_count() -> int:
    """Количество пользователей «Новый пользователь»."""
    return await baserow.get_count_by_status(config.STATUS_NEW)


async def get_support_count() -> int:
    """Количество пользователей «Сообщение в поддержку»."""
    return await baserow.get_count_by_status(config.STATUS_SUPPORT_MESSAGE)


async def get_all_users_count() -> int:
    """Общее количество пользователей в таблице."""
    return await baserow.get_total_rows_count()


async def get_waiting_deposit(limit: int = 200, offset: int = 0):
    """Пользователи со статусом «Ожидаем депозит»."""
    return await baserow.get_users_by_status(config.STATUS_WAITING_DEPOSIT, limit=limit, offset=offset)


async def get_waiting_deposit_count() -> int:
    """Количество пользователей «Ожидаем депозит»."""
    return await baserow.get_count_by_status(config.STATUS_WAITING_DEPOSIT)


async def get_clients(limit: int = 200, offset: int = 0):
    """Пользователи со статусом «Доступ выдан» (клиенты)."""
    return await baserow.get_users_by_status(config.STATUS_ACCESS_GRANTED, limit=limit, offset=offset)


async def get_clients_count() -> int:
    """Количество клиентов (Доступ выдан)."""
    return await baserow.get_count_by_status(config.STATUS_ACCESS_GRANTED)


async def get_leads(limit: int = 200, offset: int = 0):
    """Лиды — все пользователи кроме клиентских и финальных статусов."""
    return await baserow.get_leads_users(limit=limit, offset=offset)


async def get_leads_count() -> int:
    """Количество лидов."""
    return await baserow.get_leads_count()


async def get_leads_broadcast_telegram_ids() -> list[int]:
    """Telegram ID лидов для рассылки (статусы: Новый пользователь, Начал регистрацию, Ожидаем Broker ID)."""
    return await baserow.get_leads_telegram_ids_for_broadcast()


async def set_waiting_deposit(telegram_id: int) -> bool:
    """Перевести пользователя в статус «Ожидаем депозит»."""
    row = await baserow.get_user_by_telegram_id(telegram_id)
    if row is None:
        return False
    ok = await baserow.update_status(row["id"], config.STATUS_WAITING_DEPOSIT)
    if not ok:
        return False
    await baserow.log_event(row["id"], "deposit_requested")
    logger.info("CRM: deposit_requested telegram_id=%s row_id=%s", telegram_id, row["id"])
    return True


async def get_menu_counts() -> dict[str, int]:
    """Counters для CRM меню: ready, waiting, deposit, support, clients, leads."""
    ready, waiting, deposit, support, clients, leads = await asyncio.gather(
        get_ready_count(),
        get_waiting_count(),
        get_waiting_deposit_count(),
        get_support_count(),
        get_clients_count(),
        get_leads_count(),
    )
    return {
        "ready": ready,
        "waiting": waiting,
        "deposit": deposit,
        "support": support,
        "clients": clients,
        "leads": leads,
    }


async def get_user_card(telegram_id: int) -> dict | None:
    """
    Получить карточку пользователя по telegram_id.
    Возвращает dict с id, telegram_id, telegram_username, first_name, broker_id, status, created_at.
    None если пользователь не найден.
    """
    row = await baserow.get_user_by_telegram_id(telegram_id)
    if row is None:
        return None
    return baserow.row_to_user_dict(row)


async def set_access_granted(telegram_id: int) -> bool:
    """Выдать доступ пользователю. True при успехе, False если пользователь не найден или обновление не удалось."""
    row = await baserow.get_user_by_telegram_id(telegram_id)
    if row is None:
        return False
    ok = await baserow.update_status(row["id"], config.STATUS_ACCESS_GRANTED)
    if not ok:
        return False
    await baserow.log_event(row["id"], "access_granted")
    logger.info("CRM: access_granted telegram_id=%s row_id=%s", telegram_id, row["id"])
    return True


async def set_rejected(telegram_id: int) -> bool:
    """Отклонить пользователя. True при успехе, False если пользователь не найден или обновление не удалось."""
    row = await baserow.get_user_by_telegram_id(telegram_id)
    if row is None:
        return False
    ok = await baserow.update_status(row["id"], config.STATUS_REJECTED)
    if not ok:
        return False
    await baserow.log_event(row["id"], "rejected")
    logger.info("CRM: rejected telegram_id=%s row_id=%s", telegram_id, row["id"])
    return True


async def set_spam(telegram_id: int) -> bool:
    """Пометить пользователя как спам. True при успехе, False если пользователь не найден или обновление не удалось."""
    row = await baserow.get_user_by_telegram_id(telegram_id)
    if row is None:
        return False
    ok = await baserow.update_status(row["id"], config.STATUS_SPAM)
    if not ok:
        return False
    await baserow.log_event(row["id"], "spam_marked")
    logger.info("CRM: spam_marked telegram_id=%s row_id=%s", telegram_id, row["id"])
    return True
