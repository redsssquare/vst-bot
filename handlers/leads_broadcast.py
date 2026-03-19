"""Рассылка лидам — команда /leads_send и broadcast flow."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import state_manager
from utils.admin_access import has_crm_access
from services import crm_service

router = Router(name="leads_broadcast")
logger = logging.getLogger(__name__)

BROADCAST_PROMPT = "Введите сообщение для рассылки"
BROADCAST_CONFIRM_TEMPLATE = "Вы собираетесь отправить сообщение {count} пользователям.\nПодтвердите действие"
BROADCAST_DONE_TEMPLATE = "Рассылка завершена:\nОтправлено: {sent}\nОшибки: {errors}"
BROADCAST_CANCELLED = "Рассылка отменена"
ACCESS_DENIED = "Доступ запрещён"


@router.message(Command("leads_send"))
async def handle_leads_send_command(message: Message) -> None:
    """Команда /leads_send: начать flow рассылки."""
    user_id = message.from_user.id if message.from_user else 0
    if not await has_crm_access(message.bot, user_id):
        await message.answer(ACCESS_DENIED)
        return

    state_manager.set_step(user_id, "broadcast_text")
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="broadcast_cancel")],
        ]
    )
    await message.answer(BROADCAST_PROMPT, reply_markup=kb)
    logger.info("CRM: leads_send started manager_id=%s", user_id)


def _step_is_broadcast_text(msg: Message) -> bool:
    return msg.from_user is not None and state_manager.get_step(msg.from_user.id) == "broadcast_text"


@router.message(F.text, _step_is_broadcast_text)
async def handle_broadcast_text(message: Message) -> None:
    """Обработка текста в режиме broadcast_text: сохранить, показать подтверждение."""
    user_id = message.from_user.id if message.from_user else 0
    text = (message.text or "").strip()
    if not text:
        await message.answer(BROADCAST_PROMPT)
        return

    state_manager.set_broadcast_text(user_id, text)
    ids = await crm_service.get_leads_broadcast_telegram_ids()
    state_manager.set_step(user_id, "broadcast_confirm")

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Отправить", callback_data="broadcast_send"),
                InlineKeyboardButton(text="Отмена", callback_data="broadcast_cancel"),
            ],
        ]
    )
    await message.answer(
        BROADCAST_CONFIRM_TEMPLATE.format(count=len(ids)),
        reply_markup=kb,
    )
    logger.info("CRM: broadcast_text received manager_id=%s recipients=%s", user_id, len(ids))


@router.callback_query(F.data == "broadcast_send")
async def handle_broadcast_send(callback: CallbackQuery) -> None:
    """Подтверждение рассылки: отправить сообщение каждому получателю."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    text = state_manager.get_broadcast_text(user_id)
    if not text:
        await callback.answer("Текст рассылки не найден", show_alert=True)
        state_manager.set_step(user_id, "main")
        return

    ids = await crm_service.get_leads_broadcast_telegram_ids()
    sent = 0
    errors = 0

    for tg_id in ids:
        try:
            await callback.bot.send_message(tg_id, text)
            sent += 1
        except Exception as e:
            logger.warning("CRM: broadcast send failed tg_id=%s: %s", tg_id, e)
            errors += 1

    state_manager.clear_broadcast_text(user_id)
    state_manager.set_step(user_id, "main")

    result_text = BROADCAST_DONE_TEMPLATE.format(sent=sent, errors=errors)
    await callback.message.edit_text(result_text, reply_markup=None)
    await callback.answer()
    logger.info("CRM: broadcast completed manager_id=%s sent=%s errors=%s", user_id, sent, errors)


@router.callback_query(F.data == "broadcast_cancel")
async def handle_broadcast_cancel(callback: CallbackQuery) -> None:
    """Отмена рассылки."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    state_manager.clear_broadcast_text(user_id)
    state_manager.set_step(user_id, "main")

    await callback.message.edit_text(BROADCAST_CANCELLED, reply_markup=None)
    await callback.answer()
    logger.info("CRM: broadcast cancelled manager_id=%s", user_id)
