"""CRM действия — написать, доступ, отклонить, спам."""

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

import config
import state_manager
from utils.admin_access import has_crm_access
from services import crm_service
from keyboards import get_user_card_keyboard

router = Router(name="crm_actions")
logger = logging.getLogger(__name__)

CRM_WRITE_PROMPT = "Отправьте сообщение для пересылки пользователю"
CRM_WRITE_SENT = "Сообщение отправлено"


def _format_card_for_refresh(card: dict) -> str:
    """Форматирует карточку для обновления сообщения."""
    first_name = card.get("first_name") or "—"
    username = card.get("telegram_username") or ""
    telegram_id = card.get("telegram_id") or "—"
    broker_id = card.get("broker_id") or "—"
    status = card.get("status") or "—"
    created_at = card.get("created_at") or "—"
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


@router.callback_query(F.data.startswith("crm_write_"))
async def handle_crm_write(callback: CallbackQuery) -> None:
    """crm_write_{id}: перевести в режим отправки сообщения пользователю."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    raw = callback.data.removeprefix("crm_write_")
    if not raw or not raw.isdigit():
        await callback.answer("Ошибка: неверный ID", show_alert=True)
        return

    target_id = int(raw)
    state_manager.set_step(user_id, "crm_write")
    state_manager.set_crm_write_target(user_id, target_id)
    await callback.message.answer(CRM_WRITE_PROMPT)
    await callback.answer()
    logger.info("CRM: crm_write started manager_id=%s target_id=%s", user_id, target_id)


def _step_is_crm_write(msg: Message) -> bool:
    return msg.from_user is not None and state_manager.get_step(msg.from_user.id) == "crm_write"


@router.message(F.text, _step_is_crm_write)
async def handle_crm_write_message(message: Message) -> None:
    """Обработка текста в режиме crm_write: пересылка пользователю."""
    user_id = message.from_user.id if message.from_user else 0
    target_id = state_manager.get_crm_write_target(user_id)
    if target_id is None:
        state_manager.set_step(user_id, "main")
        return

    text = (message.text or "").strip()
    if not text:
        await message.answer(CRM_WRITE_PROMPT)
        return

    try:
        await message.bot.send_message(target_id, text)
    except Exception as e:
        logger.warning("CRM: crm_write send failed target_id=%s: %s", target_id, e)
        await message.answer("Не удалось отправить сообщение.")
    else:
        state_manager.clear_crm_write_target(user_id)
        state_manager.set_step(user_id, "main")
        await message.answer(CRM_WRITE_SENT)
        logger.info("CRM: crm_write sent manager_id=%s target_id=%s", user_id, target_id)


@router.callback_query(F.data.startswith("crm_access_"))
async def handle_crm_access(callback: CallbackQuery) -> None:
    """crm_access_{id}: выдать доступ, уведомить пользователя и админа."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    raw = callback.data.removeprefix("crm_access_")
    if not raw or not raw.isdigit():
        await callback.answer("Ошибка: неверный ID", show_alert=True)
        return

    target_id = int(raw)
    ok = await crm_service.set_access_granted(target_id)
    if not ok:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    card = await crm_service.get_user_card(target_id)
    broker_id = (card.get("broker_id") or "—") if card else "—"
    username = (card.get("telegram_username") or "") if card else ""

    user_line = f"@{username}" if username else "—"
    admin_text = f"Менеджер выдал доступ\n\nUser\n{user_line}\nBroker ID\n{broker_id}"
    await callback.bot.send_message(config.ADMIN_CHAT_ID, admin_text)

    if card:
        text = _format_card_for_refresh(card)
        kb = get_user_card_keyboard(
            target_id,
            list_type=state_manager.get_crm_list_source(user_id),
            page=state_manager.get_crm_list_page(user_id),
            index_in_page=state_manager.get_crm_list_user_index(user_id) or 0,
            total=state_manager.get_crm_list_total(user_id),
        )
        await callback.message.edit_text(text, reply_markup=kb)

    await callback.answer()
    logger.info("CRM: status updated", extra={"target_id": target_id, "action": "access_granted"})


@router.callback_query(F.data.startswith("crm_reject_"))
async def handle_crm_reject(callback: CallbackQuery) -> None:
    """crm_reject_{id}: отклонить пользователя, уведомить админа, обновить карточку."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    raw = callback.data.removeprefix("crm_reject_")
    if not raw or not raw.isdigit():
        await callback.answer("Ошибка: неверный ID", show_alert=True)
        return

    target_id = int(raw)
    ok = await crm_service.set_rejected(target_id)
    if not ok:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    card = await crm_service.get_user_card(target_id)
    broker_id = (card.get("broker_id") or "—") if card else "—"
    username = (card.get("telegram_username") or "") if card else ""

    user_line = f"@{username}" if username else "—"
    admin_text = f"Менеджер отклонил пользователя\n\nUser\n{user_line}\nBroker ID\n{broker_id}"
    await callback.bot.send_message(config.ADMIN_CHAT_ID, admin_text)

    if card:
        text = _format_card_for_refresh(card)
        kb = get_user_card_keyboard(
            target_id,
            list_type=state_manager.get_crm_list_source(user_id),
            page=state_manager.get_crm_list_page(user_id),
            index_in_page=state_manager.get_crm_list_user_index(user_id) or 0,
            total=state_manager.get_crm_list_total(user_id),
        )
        await callback.message.edit_text(text, reply_markup=kb)

    await callback.answer()
    logger.info("CRM: status updated", extra={"target_id": target_id, "action": "rejected"})


@router.callback_query(F.data.startswith("crm_spam_"))
async def handle_crm_spam(callback: CallbackQuery) -> None:
    """crm_spam_{id}: пометить как спам, уведомить админа, обновить карточку."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    raw = callback.data.removeprefix("crm_spam_")
    if not raw or not raw.isdigit():
        await callback.answer("Ошибка: неверный ID", show_alert=True)
        return

    target_id = int(raw)
    ok = await crm_service.set_spam(target_id)
    if not ok:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    card = await crm_service.get_user_card(target_id)
    broker_id = (card.get("broker_id") or "—") if card else "—"
    username = (card.get("telegram_username") or "") if card else ""

    user_line = f"@{username}" if username else "—"
    admin_text = f"Менеджер пометил как спам\n\nUser\n{user_line}\nBroker ID\n{broker_id}"
    await callback.bot.send_message(config.ADMIN_CHAT_ID, admin_text)

    if card:
        text = _format_card_for_refresh(card)
        kb = get_user_card_keyboard(
            target_id,
            list_type=state_manager.get_crm_list_source(user_id),
            page=state_manager.get_crm_list_page(user_id),
            index_in_page=state_manager.get_crm_list_user_index(user_id) or 0,
            total=state_manager.get_crm_list_total(user_id),
        )
        await callback.message.edit_text(text, reply_markup=kb)

    await callback.answer()
    logger.info("CRM: status updated", extra={"target_id": target_id, "action": "spam"})
