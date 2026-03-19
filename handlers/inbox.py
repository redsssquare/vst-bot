"""Inbox router: forwards user messages to forum topics and manager replies to users."""

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType, ContentType
from aiogram.filters import Command, or_f
from aiogram.types import Message

import config
from utils.format_helpers import format_datetime
import state_manager
from services import baserow

router = Router(name="inbox")
logger = logging.getLogger(__name__)

# Шаги, при которых пользователь вводит данные — inbox не должен перехватывать сообщение
_REGISTRATION_STEPS = {
    "choose_account_status",
    "awaiting_new_registration_id",
    "existing_account_options",
    "awaiting_existing_id",
    "reconnect_instruction",
    "awaiting_support_message",
}


_USER_CONTENT_TYPES = [
    ContentType.TEXT,
    ContentType.PHOTO,
    ContentType.VIDEO,
    ContentType.DOCUMENT,
    ContentType.VOICE,
    ContentType.AUDIO,
    ContentType.STICKER,
    ContentType.VIDEO_NOTE,
]


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.content_type.in_(_USER_CONTENT_TYPES),
    F.from_user.is_bot == False,
    F.from_user.is_not(None),
)
async def on_user_message(message: Message, bot: Bot) -> None:
    """
    Handle incoming messages from users: create topic on first contact,
    forward each message to the corresponding forum topic.
    Text: send formatted message. Media: copy_message with optional caption.
    """
    user_id = message.from_user.id if message.from_user else 0

    if state_manager.get_step(user_id) in _REGISTRATION_STEPS:
        return

    row = await baserow.get_user_by_telegram_id(user_id)
    if row is None:
        logger.warning("inbox: user %s not found in Baserow", user_id)
        return

    topic_id = await baserow.get_topic_id(user_id)
    topic_created_now = False
    if topic_id is None:
        topic_id = await baserow.get_topic_id(user_id)
        if topic_id is None:
            first_name = (message.from_user.first_name if message.from_user else "") or "User"
            username = (message.from_user.username if message.from_user else "") or "no_username"
            topic_name = f"{first_name} (@{username}) | ID: {user_id}"
            try:
                result = await bot.create_forum_topic(
                    chat_id=config.ADMIN_CHAT_ID,
                    name=topic_name,
                )
                topic_id = result.message_thread_id
                await baserow.set_topic_id(row["id"], topic_id)
                topic_created_now = True
            except Exception as e:
                logger.warning("inbox: create_forum_topic failed for user %s: %s", user_id, e)
                return

    first_name = (message.from_user.first_name if message.from_user else "") or "User"
    username = (message.from_user.username if message.from_user else "") or "no_username"

    if topic_created_now:
        if message.content_type == ContentType.TEXT:
            text = (message.text or "").strip() or "(пусто)"
            admin_text = f"👤 {first_name} (@{username})\nID: {user_id}\n\n{text}"
            try:
                await bot.send_message(
                    chat_id=config.ADMIN_CHAT_ID,
                    message_thread_id=topic_id,
                    text=admin_text,
                )
            except Exception as e:
                logger.warning("inbox: send_message failed for user %s: %s", user_id, e)
        else:
            copy_kwargs = {
                "chat_id": config.ADMIN_CHAT_ID,
                "from_chat_id": message.chat.id,
                "message_id": message.message_id,
                "message_thread_id": topic_id,
            }
            if not message.caption:
                copy_kwargs["caption"] = f"👤 {first_name} (@{username})"
            try:
                await bot.copy_message(**copy_kwargs)
            except Exception as e:
                logger.warning("inbox: copy_message failed for user %s: %s", user_id, e)
    else:
        try:
            await bot.copy_message(
                chat_id=config.ADMIN_CHAT_ID,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
                message_thread_id=topic_id,
            )
        except Exception as e:
            logger.warning("inbox: copy_message failed for user %s: %s", user_id, e)


def _format_info_card(user: dict) -> str:
    """Форматирует карточку пользователя для /info."""
    first_name = user.get("first_name") or "—"
    username = user.get("telegram_username") or ""
    telegram_id = user.get("telegram_id") or "—"
    status = user.get("status") or "—"
    broker_id = user.get("broker_id") or "—"
    created_at = format_datetime(user.get("created_at"))
    username_part = f" (@{username})" if username else ""
    return (
        f"👤 {first_name}{username_part}\n"
        f"🆔 Telegram ID: {telegram_id}\n"
        f"📌 Статус: {status}\n"
        f"🏦 Broker ID: {broker_id}\n"
        f"📅 Зарегистрирован: {created_at}"
    )


def _is_info_command(msg: Message) -> bool:
    """Проверка /info — Command или plain text (на случай если entity не распознан)."""
    text = (msg.text or "").strip()
    return text == "/info" or text.startswith("/info@") or (text.startswith("/info") and len(text) <= 10)


@router.message(
    F.chat.id == config.ADMIN_CHAT_ID,
    F.message_thread_id.is_not(None),
    or_f(Command("info"), _is_info_command),
)
async def on_info_command(message: Message, bot: Bot) -> None:
    """/info в топике: показать карточку пользователя."""
    topic_id = message.message_thread_id
    logger.warning("inbox: /info called, topic_id=%s, chat_id=%s", topic_id, message.chat.id)
    row = await baserow.get_user_by_topic_id(topic_id)
    if row is None:
        logger.warning("inbox: /info topic_id %s not found in Baserow", topic_id)
        await message.reply(f"Пользователь не найден для этого топика (thread_id={topic_id}).")
        return
    user = baserow.row_to_user_dict(row)
    card = _format_info_card(user)
    await message.reply(card)


@router.message(
    or_f(Command("info"), _is_info_command),
)
async def on_info_wrong_place(message: Message, bot: Bot) -> None:
    """/info вне топика — подсказка."""
    await message.reply("Используйте /info в топике пользователя в форум-группе.")


@router.message(
    F.chat.id == config.ADMIN_CHAT_ID,
    F.message_thread_id.is_not(None),
    F.from_user.is_bot == False,
    F.from_user.is_not(None),
)
async def on_manager_reply(message: Message, bot: Bot) -> None:
    """
    Handle manager replies in forum topics: forward message to the user in private
    via copy_message (works for text and media).
    """
    topic_id = message.message_thread_id
    row = await baserow.get_user_by_topic_id(topic_id)
    if row is None:
        logger.warning("inbox: topic_id %s not found", topic_id)
        return

    user = baserow.row_to_user_dict(row)
    telegram_id = user.get("telegram_id")
    if not telegram_id:
        logger.warning("inbox: topic_id %s row has no telegram_id", topic_id)
        return

    try:
        await bot.copy_message(
            chat_id=telegram_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
    except Exception as e:
        logger.warning("inbox: copy_message to user %s failed: %s", telegram_id, e)
