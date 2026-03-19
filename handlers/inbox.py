"""Inbox router: forwards user messages to forum topics and manager replies to users."""

import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatType, ContentType
from aiogram.types import Message

import config
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
    "crm_write",
}


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.content_type == ContentType.TEXT,
)
async def on_user_message(message: Message, bot: Bot) -> None:
    """
    Handle incoming text from users: create topic on first contact,
    forward each message to the corresponding forum topic.
    """
    user_id = message.from_user.id if message.from_user else 0

    if state_manager.get_step(user_id) in _REGISTRATION_STEPS:
        return

    row = await baserow.get_user_by_telegram_id(user_id)
    if row is None:
        logger.warning("inbox: user %s not found in Baserow", user_id)
        return

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
        except Exception as e:
            logger.warning("inbox: create_forum_topic failed for user %s: %s", user_id, e)
            return

    first_name = (message.from_user.first_name if message.from_user else "") or "User"
    username = (message.from_user.username if message.from_user else "") or "no_username"
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


@router.message(
    F.chat.id == config.ADMIN_CHAT_ID,
    F.message_thread_id.is_not(None),
    F.content_type == ContentType.TEXT,
    F.from_user.is_bot == False,
    F.from_user.is_not(None),
)
async def on_manager_reply(message: Message, bot: Bot) -> None:
    """
    Handle manager replies in forum topics: forward text to the user in private.
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
        await bot.send_message(chat_id=telegram_id, text=message.text or "")
    except Exception as e:
        logger.warning("inbox: send_message to user %s failed: %s", telegram_id, e)
