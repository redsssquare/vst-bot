"""CRM списки — клавиатуры со списками пользователей."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_user_list_keyboard(
    users: list[dict],
    list_type: str | None = None,
    page: int = 0,
    total_pages: int = 1,
    show_back: bool = True,
) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком пользователей.
    Каждый пользователь — кнопка с callback_data crm_user_{telegram_id}.
    list_type, page, total_pages — для пагинации (⬅ Назад | Стр N/M | ➡ Далее).
    """
    rows = []
    for u in users:
        first_name = u.get("first_name") or "—"
        username = u.get("telegram_username") or ""
        text = f"{first_name} (@{username})" if username else first_name
        if len(text) > 50:
            text = text[:47] + "..."
        rows.append([
            InlineKeyboardButton(
                text=text,
                callback_data=f"crm_user_{u['telegram_id']}",
            )
        ])
    nav_buttons = []
    if show_back:
        nav_buttons.append(InlineKeyboardButton(text="⬅ В меню", callback_data="crm_back_to_menu"))
    if list_type is not None:
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="⬅ Пред",
                    callback_data=f"crm_{list_type}_page_{page - 1}",
                )
            )
        nav_buttons.append(
            InlineKeyboardButton(text=f"Стр {page + 1}/{total_pages}", callback_data="crm_noop")
        )
        if page + 1 < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(
                    text="➡ Далее",
                    callback_data=f"crm_{list_type}_page_{page + 1}",
                )
            )
    if nav_buttons:
        rows.append(nav_buttons)
    return InlineKeyboardMarkup(inline_keyboard=rows)
