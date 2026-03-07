"""Проверка доступа к CRM по членству в админ-чате."""

from aiogram import Bot

from config import ADMIN_CHAT_ID


async def has_crm_access(bot: Bot, user_id: int) -> bool:
    """
    Проверяет, есть ли у пользователя доступ к CRM (является ли членом админ-чата).
    Возвращает True для creator, administrator, member.
    Возвращает False для left, kicked или при ошибке.
    """
    try:
        member = await bot.get_chat_member(chat_id=ADMIN_CHAT_ID, user_id=user_id)
        return member.status in ("creator", "administrator", "member")
    except Exception:
        return False
