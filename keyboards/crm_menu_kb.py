"""CRM меню — главная клавиатура CRM панели."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_crm_menu_keyboard(counts: dict[str, int] | None = None) -> InlineKeyboardMarkup:
    """Клавиатура главного меню CRM. counts: ready, deposit, waiting, new_leads, support, clients, leads."""
    if counts is None:
        counts = {"ready": 0, "deposit": 0, "waiting": 0, "new_leads": 0, "support": 0, "clients": 0, "leads": 0}
    r = counts.get("ready", 0)
    d = counts.get("deposit", 0)
    w = counts.get("waiting", 0)
    nl = counts.get("new_leads", 0)
    s = counts.get("support", 0)
    c = counts.get("clients", 0)
    l = counts.get("leads", 0)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Готовы к подключению ({r})", callback_data="crm_ready")],
            [InlineKeyboardButton(text=f"💰 Ожидаем депозит ({d})", callback_data="crm_deposit")],
            [InlineKeyboardButton(text=f"⏳ Ожидаем Broker ID ({w})", callback_data="crm_waiting")],
            [InlineKeyboardButton(text=f"🆕 Новые пользователи (24ч) ({nl})", callback_data="crm_new_leads")],
            [InlineKeyboardButton(text=f"📨 Поддержка ({s})", callback_data="crm_support")],
            [InlineKeyboardButton(text=f"👑 Клиенты ({c})", callback_data="crm_clients")],
            [InlineKeyboardButton(text=f"🎯 Лиды ({l})", callback_data="crm_leads")],
        ],
    )
