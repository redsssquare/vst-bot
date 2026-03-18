"""CRM меню — команда /crm и списки пользователей."""

import logging
import math

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import state_manager
from utils.admin_access import has_crm_access
from utils.format_helpers import format_datetime
from services import crm_service
from keyboards import get_crm_menu_keyboard, get_user_list_keyboard

router = Router(name="crm_menu")
logger = logging.getLogger(__name__)

CRM_MENU_TEXT = "CRM — панель менеджера"
ACCESS_DENIED_TEXT = "Доступ запрещён"


def _format_user_list(users: list[dict], header: str, emoji: str, total_count: int | None = None, page_offset: int = 0) -> str:
    """Форматирует список пользователей. total_count — для «Все пользователи» (общий count из Baserow)."""
    count = total_count if total_count is not None else len(users)
    lines = [f"{emoji} {header} ({count})", ""]
    for i, u in enumerate(users, 1):
        first_name = u.get("first_name") or "—"
        username = u.get("telegram_username") or ""
        broker_id = u.get("broker_id") or "—"
        status = u.get("status") or "—"
        created_at_raw = u.get("created_at") or ""
        created_at = format_datetime(created_at_raw) if created_at_raw else "—"
        num = page_offset + i
        lines.append(f"{num}. {first_name}")
        lines.append(f"@{username}" if username else "—")
        lines.append(f"Broker ID: {broker_id}")
        lines.append(f"Статус: {status}")
        lines.append(created_at)
        lines.append("")
    return "\n".join(lines).strip()


def _format_support_list(users: list[dict], header: str, emoji: str, total_count: int | None = None) -> str:
    """Формат списка поддержки: Имя, Username, Последнее сообщение."""
    count = total_count if total_count is not None else len(users)
    lines = [f"{emoji} {header} ({count})", ""]
    for i, u in enumerate(users, 1):
        first_name = u.get("first_name") or "—"
        username = u.get("telegram_username") or ""
        last_message = u.get("last_support_message") or "—"
        lines.append(f"{i}. {first_name}")
        lines.append(f"@{username}" if username else "—")
        lines.append(f"Последнее сообщение: {last_message}")
        lines.append("")
    return "\n".join(lines).strip()


@router.message(Command("crm"))
async def cmd_crm(message: Message) -> None:
    """Команда /crm: проверка доступа и показ меню."""
    user_id = message.from_user.id if message.from_user else 0
    if not await has_crm_access(message.bot, user_id):
        await message.answer(ACCESS_DENIED_TEXT)
        return
    logger.info("CRM: menu opened")
    counts = await crm_service.get_menu_counts()
    await message.answer(CRM_MENU_TEXT, reply_markup=get_crm_menu_keyboard(counts))


@router.callback_query(F.data == "crm_new_leads")
async def handle_crm_new_leads(callback: CallbackQuery) -> None:
    """Список «Новые пользователи (24ч)»."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return
    state_manager.set_crm_list_source(user_id, "new_leads")
    state_manager.set_crm_list_page(user_id, 0)
    state_manager.set_crm_list_users(user_id, users := await crm_service.get_new_leads_24h(limit=10, offset=0))
    total = await crm_service.get_new_leads_count()
    state_manager.set_crm_list_total(user_id, total)
    total_pages = max(1, math.ceil(total / 10))
    logger.info("CRM: users list loaded", extra={"list_type": "new_leads"})
    text = _format_user_list(users, "Новые пользователи (24ч)", "🆕", total_count=total)
    kb = get_user_list_keyboard(users, list_type="new_leads", page=0, total_pages=total_pages)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "crm_waiting")
async def handle_crm_waiting(callback: CallbackQuery) -> None:
    """Список «Ожидаем Broker ID»."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return
    state_manager.set_crm_list_source(user_id, "waiting")
    state_manager.set_crm_list_page(user_id, 0)
    state_manager.set_crm_list_users(user_id, users := await crm_service.get_waiting_broker_id(limit=10, offset=0))
    total = await crm_service.get_waiting_count()
    state_manager.set_crm_list_total(user_id, total)
    total_pages = max(1, math.ceil(total / 10))
    logger.info("CRM: users list loaded", extra={"list_type": "waiting"})
    text = _format_user_list(users, "Ожидаем Broker ID", "⏳", total_count=total)
    kb = get_user_list_keyboard(users, list_type="waiting", page=0, total_pages=total_pages)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "crm_ready")
async def handle_crm_ready(callback: CallbackQuery) -> None:
    """Список «Готовы к подключению»."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return
    state_manager.set_crm_list_source(user_id, "ready")
    state_manager.set_crm_list_page(user_id, 0)
    state_manager.set_crm_list_users(user_id, users := await crm_service.get_ready_to_connect(limit=10, offset=0))
    total = await crm_service.get_ready_count()
    state_manager.set_crm_list_total(user_id, total)
    total_pages = max(1, math.ceil(total / 10))
    logger.info("CRM: users list loaded", extra={"list_type": "ready"})
    text = _format_user_list(users, "Готовы к подключению", "✅", total_count=total)
    kb = get_user_list_keyboard(users, list_type="ready", page=0, total_pages=total_pages)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "crm_support")
async def handle_crm_support(callback: CallbackQuery) -> None:
    """Список «Поддержка»."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return
    state_manager.set_crm_list_source(user_id, "support")
    state_manager.set_crm_list_page(user_id, 0)
    state_manager.set_crm_list_users(user_id, users := await crm_service.get_support_requests(limit=10, offset=0))
    total = await crm_service.get_support_count()
    state_manager.set_crm_list_total(user_id, total)
    total_pages = max(1, math.ceil(total / 10))
    logger.info("CRM: users list loaded", extra={"list_type": "support"})
    text = _format_support_list(users, "Поддержка", "📨", total_count=total)
    kb = get_user_list_keyboard(users, list_type="support", page=0, total_pages=total_pages)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "crm_deposit")
async def handle_crm_deposit(callback: CallbackQuery) -> None:
    """Список «Ожидаем депозит»."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return
    state_manager.set_crm_list_source(user_id, "deposit")
    state_manager.set_crm_list_page(user_id, 0)
    state_manager.set_crm_list_users(user_id, users := await crm_service.get_waiting_deposit(limit=10, offset=0))
    total = await crm_service.get_waiting_deposit_count()
    state_manager.set_crm_list_total(user_id, total)
    total_pages = max(1, math.ceil(total / 10))
    logger.info("CRM: users list loaded", extra={"list_type": "deposit"})
    text = _format_user_list(users, "Ожидаем депозит", "💰", total_count=total)
    kb = get_user_list_keyboard(users, list_type="deposit", page=0, total_pages=total_pages)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "crm_clients")
async def handle_crm_clients(callback: CallbackQuery) -> None:
    """Список «Клиенты»."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return
    state_manager.set_crm_list_source(user_id, "clients")
    state_manager.set_crm_list_page(user_id, 0)
    state_manager.set_crm_list_users(user_id, users := await crm_service.get_clients(limit=10, offset=0))
    total = await crm_service.get_clients_count()
    state_manager.set_crm_list_total(user_id, total)
    total_pages = max(1, math.ceil(total / 10))
    logger.info("CRM: users list loaded", extra={"list_type": "clients"})
    text = _format_user_list(users, "Клиенты", "👑", total_count=total)
    kb = get_user_list_keyboard(users, list_type="clients", page=0, total_pages=total_pages)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "crm_leads")
async def handle_crm_leads(callback: CallbackQuery) -> None:
    """Список «Лиды»."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return
    state_manager.set_crm_list_source(user_id, "leads")
    state_manager.set_crm_list_page(user_id, 0)
    state_manager.set_crm_list_users(user_id, users := await crm_service.get_leads(limit=10, offset=0))
    total = await crm_service.get_leads_count()
    state_manager.set_crm_list_total(user_id, total)
    total_pages = max(1, math.ceil(total / 10))
    logger.info("CRM: users list loaded", extra={"list_type": "leads"})
    text = _format_user_list(users, "Лиды", "🎯", total_count=total)
    kb = get_user_list_keyboard(users, list_type="leads", page=0, total_pages=total_pages)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


def _render_list(
    source: str,
    users: list[dict],
    total: int,
    page: int,
    header: str,
    emoji: str,
    page_offset: int = 0,
) -> tuple[str, object]:
    """Формирует текст и клавиатуру для списка."""
    total_pages = max(1, math.ceil(total / 10))
    text = _format_user_list(users, header, emoji, total_count=total, page_offset=page_offset)
    kb = get_user_list_keyboard(users, list_type=source, page=page, total_pages=total_pages, page_offset=page_offset)
    return text, kb


@router.callback_query(F.data.regexp(r"^crm_(new_leads|waiting|ready|support|deposit|clients|leads)_page_(\d+)$"))
async def handle_crm_list_page(callback: CallbackQuery) -> None:
    """Переключение страницы списка: crm_{list_type}_page_{page}."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    match = callback.data.split("_page_")
    if len(match) != 2 or not match[1].isdigit():
        await callback.answer()
        return
    list_type = match[0].removeprefix("crm_")
    page = int(match[1])

    state_manager.set_crm_list_source(user_id, list_type)
    state_manager.set_crm_list_page(user_id, page)
    offset = page * 10

    if list_type == "new_leads":
        users = await crm_service.get_new_leads_24h(limit=10, offset=offset)
        total = await crm_service.get_new_leads_count()
        text, kb = _render_list(list_type, users, total, page, "Новые пользователи (24ч)", "🆕", page_offset=page * 10)
    elif list_type == "waiting":
        users = await crm_service.get_waiting_broker_id(limit=10, offset=offset)
        total = await crm_service.get_waiting_count()
        text, kb = _render_list(list_type, users, total, page, "Ожидаем Broker ID", "⏳", page_offset=page * 10)
    elif list_type == "ready":
        users = await crm_service.get_ready_to_connect(limit=10, offset=offset)
        total = await crm_service.get_ready_count()
        text, kb = _render_list(list_type, users, total, page, "Готовы к подключению", "✅", page_offset=page * 10)
    elif list_type == "support":
        users = await crm_service.get_support_requests(limit=10, offset=offset)
        total = await crm_service.get_support_count()
        total_pages = max(1, math.ceil(total / 10))
        text = _format_support_list(users, "Поддержка", "📨", total_count=total)
        kb = get_user_list_keyboard(users, list_type=list_type, page=page, total_pages=total_pages, page_offset=page * 10)
    elif list_type == "deposit":
        users = await crm_service.get_waiting_deposit(limit=10, offset=offset)
        total = await crm_service.get_waiting_deposit_count()
        text, kb = _render_list(list_type, users, total, page, "Ожидаем депозит", "💰", page_offset=page * 10)
    elif list_type == "clients":
        users = await crm_service.get_clients(limit=10, offset=offset)
        total = await crm_service.get_clients_count()
        text, kb = _render_list(list_type, users, total, page, "Клиенты", "👑", page_offset=page * 10)
    elif list_type == "leads":
        users = await crm_service.get_leads(limit=10, offset=offset)
        total = await crm_service.get_leads_count()
        text, kb = _render_list(list_type, users, total, page, "Лиды", "🎯", page_offset=page * 10)

    state_manager.set_crm_list_users(user_id, users)
    state_manager.set_crm_list_total(user_id, total)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
    logger.info("CRM: page switched", extra={"list_type": list_type, "page": page})


@router.callback_query(F.data == "crm_noop")
async def handle_crm_noop(callback: CallbackQuery) -> None:
    """Декоративная кнопка «Стр N/M» — только answer."""
    await callback.answer()


@router.callback_query(F.data == "crm_back_to_menu")
async def handle_crm_back_to_menu(callback: CallbackQuery) -> None:
    """Возврат в CRM меню из списка."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return
    counts = await crm_service.get_menu_counts()
    await callback.message.edit_text(CRM_MENU_TEXT, reply_markup=get_crm_menu_keyboard(counts))
    await callback.answer()


@router.callback_query(F.data == "crm_back_to_list")
async def handle_crm_back_to_list(callback: CallbackQuery) -> None:
    """Возврат из карточки пользователя в список."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer(ACCESS_DENIED_TEXT, show_alert=True)
        return

    source = state_manager.get_crm_list_source(user_id) or "leads"
    page = state_manager.get_crm_list_page(user_id)

    if source == "new_leads":
        total = await crm_service.get_new_leads_count()
        users = await crm_service.get_new_leads_24h(limit=10, offset=page * 10)
        total_pages = max(1, math.ceil(total / 10))
        text = _format_user_list(users, "Новые пользователи (24ч)", "🆕", total_count=total, page_offset=page * 10)
    elif source == "waiting":
        total = await crm_service.get_waiting_count()
        users = await crm_service.get_waiting_broker_id(limit=10, offset=page * 10)
        total_pages = max(1, math.ceil(total / 10))
        text = _format_user_list(users, "Ожидаем Broker ID", "⏳", total_count=total, page_offset=page * 10)
    elif source == "ready":
        total = await crm_service.get_ready_count()
        users = await crm_service.get_ready_to_connect(limit=10, offset=page * 10)
        total_pages = max(1, math.ceil(total / 10))
        text = _format_user_list(users, "Готовы к подключению", "✅", total_count=total, page_offset=page * 10)
    elif source == "support":
        total = await crm_service.get_support_count()
        users = await crm_service.get_support_requests(limit=10, offset=page * 10)
        total_pages = max(1, math.ceil(total / 10))
        text = _format_support_list(users, "Поддержка", "📨", total_count=total)
    elif source == "deposit":
        total = await crm_service.get_waiting_deposit_count()
        users = await crm_service.get_waiting_deposit(limit=10, offset=page * 10)
        total_pages = max(1, math.ceil(total / 10))
        text = _format_user_list(users, "Ожидаем депозит", "💰", total_count=total, page_offset=page * 10)
    elif source == "clients":
        total = await crm_service.get_clients_count()
        users = await crm_service.get_clients(limit=10, offset=page * 10)
        total_pages = max(1, math.ceil(total / 10))
        text = _format_user_list(users, "Клиенты", "👑", total_count=total, page_offset=page * 10)
    elif source == "leads":
        total = await crm_service.get_leads_count()
        users = await crm_service.get_leads(limit=10, offset=page * 10)
        total_pages = max(1, math.ceil(total / 10))
        text = _format_user_list(users, "Лиды", "🎯", total_count=total, page_offset=page * 10)

    state_manager.set_crm_list_users(user_id, users)
    state_manager.set_crm_list_total(user_id, total)
    kb = get_user_list_keyboard(users, list_type=source, page=page, total_pages=total_pages, page_offset=page * 10)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
