"""CRM карточка пользователя — действия над пользователем."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_user_card_keyboard(
    telegram_id: int,
    list_type: str | None = None,
    page: int = 0,
    index_in_page: int = 0,
    total: int | None = None,
) -> InlineKeyboardMarkup:
    """Клавиатура действий для карточки пользователя.
    list_type, page, index_in_page, total — для кнопки «Следующий лид» (из контекста списка).
    """
    rows = [
        [InlineKeyboardButton(text="✉️ Написать", callback_data=f"crm_write_{telegram_id}")],
        [InlineKeyboardButton(text="✅ Доступ выдан", callback_data=f"crm_access_{telegram_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"crm_reject_{telegram_id}")],
        [InlineKeyboardButton(text="🚫 Спам", callback_data=f"crm_spam_{telegram_id}")],
    ]
    if list_type is not None and total is not None:
        rows.append([InlineKeyboardButton(text="➡ Следующий лид", callback_data="crm_next_lead")])
    rows.append([InlineKeyboardButton(text="⬅ Назад", callback_data="crm_back_to_list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
