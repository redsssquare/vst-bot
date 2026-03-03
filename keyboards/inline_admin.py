"""Inline-клавиатуры для админ-действий."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_approve_reject_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    """Inline-клавиатура Approve/Reject для заявки пользователя."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Approve",
                    callback_data=f"approve:{telegram_id}",
                ),
                InlineKeyboardButton(
                    text="Reject",
                    callback_data=f"reject:{telegram_id}",
                ),
            ],
        ],
    )
