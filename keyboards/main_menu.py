"""Главное меню и клавиатуры воронки доступа."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура главного меню."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Получить доступ")],
            [KeyboardButton(text="Связаться с поддержкой")],
        ],
        resize_keyboard=True,
    )


def get_account_status_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура выбора статуса аккаунта."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да, есть аккаунт")],
            [KeyboardButton(text="Нет, зарегистрироваться")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )


def get_new_registration_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура после регистрации."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Я зарегистрировался")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )


def get_existing_account_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для существующего аккаунта."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ввести ID")],
            [KeyboardButton(text="Помогите переподключить")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True,
    )
