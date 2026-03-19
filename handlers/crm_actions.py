"""CRM действия — написать, доступ, отклонить, спам."""

import logging
import re

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import config
import state_manager
from utils.admin_access import has_crm_access
from utils.format_helpers import format_datetime
from services import crm_service, baserow
from keyboards import get_user_card_keyboard

router = Router(name="crm_actions")
logger = logging.getLogger(__name__)


async def _send_to_admin(bot, user_telegram_id: int, text: str) -> None:
    """Отправить уведомление в топик пользователя, если есть, иначе в General."""
    topic_id = await baserow.get_topic_id(user_telegram_id)
    await bot.send_message(
        config.ADMIN_CHAT_ID,
        text,
        message_thread_id=topic_id if topic_id else None,
    )


def _format_card_for_refresh(card: dict) -> str:
    """Форматирует карточку для обновления сообщения."""
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


def _chat_id_for_link(chat_id: int) -> str:
    """Для t.me/c ссылок: -100xxxxxxxxxx → xxxxxxxxxx, иначе abs(chat_id)."""
    s = str(chat_id)
    if s.startswith("-100"):
        return s[4:]
    return str(abs(chat_id))


@router.callback_query(F.data.startswith("crm_write_"))
async def handle_crm_write(callback: CallbackQuery, bot: Bot) -> None:
    """crm_write_{id}: получить/создать топик и показать ссылку для переписки."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    raw = callback.data.removeprefix("crm_write_")
    if not raw or not raw.isdigit():
        await callback.answer("Ошибка: неверный ID", show_alert=True)
        return

    target_id = int(raw)
    topic_id = await baserow.get_topic_id(target_id)

    if topic_id is None:
        row = await baserow.get_user_by_telegram_id(target_id)
        if row is None:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        card = await crm_service.get_user_card(target_id)
        first_name = (card.get("first_name") or "User") if card else "User"
        username = (card.get("telegram_username") or "no_username") if card else "no_username"
        topic_name = f"{first_name} (@{username}) | ID: {target_id}"

        try:
            result = await bot.create_forum_topic(
                chat_id=config.ADMIN_CHAT_ID,
                name=topic_name,
            )
            topic_id = result.message_thread_id
            await baserow.set_topic_id(row["id"], topic_id)
        except Exception as e:
            logger.warning("CRM: create_forum_topic failed target_id=%s: %s", target_id, e)
            await callback.answer("Не удалось создать топик", show_alert=True)
            return

    chat_id_for_link = _chat_id_for_link(config.ADMIN_CHAT_ID)
    url = f"https://t.me/c/{chat_id_for_link}/{topic_id}"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📩 Открыть топик", url=url)]]
    )
    await callback.message.answer("Откройте топик для переписки:", reply_markup=kb)
    await callback.answer()
    logger.info("CRM: crm_write topic link manager_id=%s target_id=%s", user_id, target_id)


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
    admin_text = f"✅ Доступ выдан\n👤 {user_line} | Broker ID: {broker_id}"
    await _send_to_admin(callback.bot, target_id, admin_text)

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
    admin_text = f"❌ Отклонён\n👤 {user_line} | Broker ID: {broker_id}"
    await _send_to_admin(callback.bot, target_id, admin_text)

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
    admin_text = f"🚫 Спам\n👤 {user_line} | Broker ID: {broker_id}"
    await _send_to_admin(callback.bot, target_id, admin_text)

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


@router.callback_query(F.data.startswith("crm_deposit_request_"))
async def handle_crm_deposit_request(callback: CallbackQuery) -> None:
    """crm_deposit_request_{id}: показать выбор суммы депозита."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    raw = callback.data.removeprefix("crm_deposit_request_")
    if not raw or not raw.isdigit():
        await callback.answer("Ошибка: неверный ID", show_alert=True)
        return

    target_id = int(raw)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3000 RUB", callback_data=f"crm_deposit_confirm_{target_id}_3000rub"),
                InlineKeyboardButton(text="30 USD", callback_data=f"crm_deposit_confirm_{target_id}_30usd"),
            ],
            [InlineKeyboardButton(text="⬅ Назад", callback_data=f"crm_user_{target_id}")],
        ]
    )
    await callback.message.edit_text(
        f"Выберите сумму депозита для пользователя {target_id}:",
        reply_markup=kb,
    )
    await callback.answer()
    logger.info("CRM: deposit_request initiated manager_id=%s target_id=%s", user_id, target_id)


DEPOSIT_MESSAGES = {
    "3000rub": (
        "Для активации аккаунта необходимо пополнение от 3000р\n\n"
        "Тестирование будет проходить на демо.\n\n"
        "После пополнения напишите сюда."
    ),
    "30usd": (
        "Для активации аккаунта необходимо пополнение от 30$\n\n"
        "Тестирование будет проходить на демо.\n\n"
        "После пополнения напишите сюда."
    ),
}


@router.callback_query(F.data.regexp(r"^crm_deposit_confirm_(\d+)_(3000rub|30usd)$"))
async def handle_crm_deposit_confirm(callback: CallbackQuery) -> None:
    """crm_deposit_confirm_{id}_{amount}: отправить запрос депозита пользователю и обновить статус."""
    user_id = callback.from_user.id if callback.from_user else 0
    if not await has_crm_access(callback.bot, user_id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    m = re.match(r"^crm_deposit_confirm_(\d+)_(3000rub|30usd)$", callback.data)
    if not m:
        await callback.answer("Ошибка разбора данных", show_alert=True)
        return

    target_id = int(m.group(1))
    amount = m.group(2)

    deposit_text = DEPOSIT_MESSAGES.get(amount, "Пожалуйста, внесите депозит.")
    try:
        await callback.bot.send_message(target_id, deposit_text)
    except Exception as e:
        logger.warning("CRM: deposit message send failed target_id=%s: %s", target_id, e)

    ok = await crm_service.set_waiting_deposit(target_id)
    if not ok:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    card = await crm_service.get_user_card(target_id)
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
    logger.info("CRM: deposit_confirmed manager_id=%s target_id=%s amount=%s", user_id, target_id, amount)
