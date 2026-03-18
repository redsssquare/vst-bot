"""CRM карточка пользователя."""

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import state_manager
from utils.admin_access import has_crm_access
from utils.format_helpers import format_datetime
from services import crm_service
from keyboards import get_user_card_keyboard

router = Router(name="crm_user_card")
logger = logging.getLogger(__name__)


def _format_user_card(card: dict) -> str:
    """Форматирует карточку пользователя."""
    first_name = card.get("first_name") or "—"
    username = card.get("telegram_username") or ""
    telegram_id = card.get("telegram_id") or "—"
    broker_id = card.get("broker_id") or "—"
    status = card.get("status") or "—"
    created_at = format_datetime(card.get("created_at"))

    lines = [
        f"👤 {first_name}",
        "",
        f"@{username}" if username else "—",
        "",
        "Telegram ID",
        str(telegram_id),
        "",
        "Broker ID",
        str(broker_id),
        "",
        "Статус",
        status,
        "",
        "Создан",
        created_at,
    ]
    return "\n".join(lines)


@router.callback_query(F.data.startswith("crm_user_"))
async def handle_crm_user_card(callback: CallbackQuery) -> None:
    """Показать карточку пользователя по callback crm_user_{telegram_id}."""
    answered = False

    async def _ensure_answer() -> None:
        nonlocal answered
        if not answered:
            try:
                await callback.answer()
                answered = True
            except Exception:
                pass

    try:
        user_id = callback.from_user.id if callback.from_user else 0
        if not await has_crm_access(callback.bot, user_id):
            await callback.answer("Доступ запрещён", show_alert=True)
            answered = True
            return

        raw = callback.data.removeprefix("crm_user_")
        if not raw or not raw.isdigit():
            await callback.answer("Ошибка: неверный ID", show_alert=True)
            answered = True
            return

        telegram_id = int(raw)
        card = await crm_service.get_user_card(telegram_id)
        if card is None:
            await callback.answer("Пользователь не найден", show_alert=True)
            answered = True
            return

        list_type = state_manager.get_crm_list_source(user_id)
        page = state_manager.get_crm_list_page(user_id)
        users = state_manager.get_crm_list_users(user_id)
        total = state_manager.get_crm_list_total(user_id)
        index_in_page = 0
        if users:
            for i, u in enumerate(users):
                if str(u.get("telegram_id")) == str(telegram_id):
                    index_in_page = i
                    break
            state_manager.set_crm_list_user_index(user_id, index_in_page)

        logger.info("CRM: user card opened", extra={"telegram_id": telegram_id})
        text = _format_user_card(card)
        kb = get_user_card_keyboard(
            telegram_id,
            list_type=list_type,
            page=page,
            index_in_page=index_in_page,
            total=total,
        )
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        answered = True
    except TelegramBadRequest:
        await _ensure_answer()
    except Exception:
        await _ensure_answer()
        raise


NEXT_LEAD_END_TEXT = "Список лидов завершён"


@router.callback_query(F.data == "crm_next_lead")
async def handle_crm_next_lead(callback: CallbackQuery) -> None:
    """Переход к следующему пользователю в списке."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    list_type = state_manager.get_crm_list_source(user_id)
    page = state_manager.get_crm_list_page(user_id)
    users = state_manager.get_crm_list_users(user_id)
    index = state_manager.get_crm_list_user_index(user_id)
    total = state_manager.get_crm_list_total(user_id)

    if list_type is None or users is None or index is None or total is None:
        await callback.answer("Контекст списка потерян", show_alert=True)
        return

    next_index = index + 1

    if next_index < len(users):
        next_user = users[next_index]
        state_manager.set_crm_list_user_index(user_id, next_index)
        telegram_id = next_user.get("telegram_id")
        card = await crm_service.get_user_card(telegram_id)
        if card is None:
            await callback.answer("Пользователь не найден", show_alert=True)
            return
        text = _format_user_card(card)
        kb = get_user_card_keyboard(
            telegram_id,
            list_type=list_type,
            page=page,
            index_in_page=next_index,
            total=total,
        )
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        return

    global_index = page * 10 + index + 1
    if global_index >= total:
        text = NEXT_LEAD_END_TEXT
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅ Назад к списку", callback_data="crm_back_to_list")],
            ]
        )
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        return

    next_page = page + 1
    offset = next_page * 10
    if list_type == "new_leads":
        users = await crm_service.get_new_leads_24h(limit=10, offset=offset)
    elif list_type == "waiting":
        users = await crm_service.get_waiting_broker_id(limit=10, offset=offset)
    elif list_type == "ready":
        users = await crm_service.get_ready_to_connect(limit=10, offset=offset)
    elif list_type == "support":
        users = await crm_service.get_support_requests(limit=10, offset=offset)
    elif list_type == "deposit":
        users = await crm_service.get_waiting_deposit(limit=10, offset=offset)
    elif list_type == "clients":
        users = await crm_service.get_clients(limit=10, offset=offset)
    elif list_type == "leads":
        users = await crm_service.get_leads(limit=10, offset=offset)
    else:
        users = []

    state_manager.set_crm_list_page(user_id, next_page)
    state_manager.set_crm_list_users(user_id, users)

    if not users:
        text = NEXT_LEAD_END_TEXT
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅ Назад к списку", callback_data="crm_back_to_list")],
            ]
        )
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer()
        return

    next_user = users[0]
    state_manager.set_crm_list_user_index(user_id, 0)
    telegram_id = next_user.get("telegram_id")
    card = await crm_service.get_user_card(telegram_id)
    if card is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    text = _format_user_card(card)
    kb = get_user_card_keyboard(
        telegram_id,
        list_type=list_type,
        page=next_page,
        index_in_page=0,
        total=total,
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()
