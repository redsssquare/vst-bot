"""Главное меню и клавиатуры воронки доступа."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Тексты кнопок (с эмодзи) для использования в клавиатурах и в хендлерах
BTN_GET_ACCESS = "🚀 Получить доступ"
BTN_SUPPORT = "Поддержка"
BTN_YES_ACCOUNT = "✅ Да, есть аккаунт"
BTN_NO_REGISTER = "📝 Нет, зарегистрироваться"
BTN_BACK = "⬅️ Назад"
BTN_I_REGISTERED = "✅ Я зарегистрировался"
BTN_ENTER_ID = "✅ Да — ввести ID"
BTN_ENTER_ID_RECONNECT = "⌨️ Ввести ID"
BTN_RECONNECT = "⚙️ Нет — переподключить"
BTN_OPEN_LINK = "🔗 Открыть ссылку"


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_GET_ACCESS, callback_data="main:get_access")],
            [InlineKeyboardButton(text=BTN_SUPPORT, callback_data="main:support")],
        ],
    )


def get_account_status_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора статуса аккаунта."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_YES_ACCOUNT, callback_data="account:yes")],
            [InlineKeyboardButton(text=BTN_NO_REGISTER, callback_data="account:no")],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="account:back")],
        ],
    )


def get_new_registration_keyboard(affiliate_link: str) -> InlineKeyboardMarkup:
    """Клавиатура после регистрации."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_OPEN_LINK, url=affiliate_link)],
            [InlineKeyboardButton(text=BTN_I_REGISTERED, callback_data="register:done")],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="register:back")],
        ],
    )


def get_existing_account_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для существующего аккаунта."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_ENTER_ID, callback_data="existing:enter_id")],
            [InlineKeyboardButton(text=BTN_RECONNECT, callback_data="existing:reconnect")],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="existing:back")],
        ],
    )


def get_reconnect_instruction_keyboard(affiliate_link: str) -> InlineKeyboardMarkup:
    """Inline-клавиатура экрана 3e — инструкция по переподключению."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_OPEN_LINK, url=affiliate_link)],
            [InlineKeyboardButton(text=BTN_ENTER_ID_RECONNECT, callback_data="reconnect:enter_id")],
            [InlineKeyboardButton(text=BTN_BACK, callback_data="reconnect:back")],
            [InlineKeyboardButton(text=BTN_SUPPORT, callback_data="main:support")],
        ],
    )


def get_await_id_keyboard() -> InlineKeyboardMarkup:
    """Inline-клавиатура для экранов ожидания ID."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_BACK, callback_data="await_id:back")],
        ],
    )


def get_post_id_success_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после успешной отправки ID — только «Поддержка»."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=BTN_SUPPORT, callback_data="main:support")],
        ],
    )
