"""Обработчики команды /start и главного меню."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

import state_manager
from keyboards import get_account_status_keyboard, get_main_menu_keyboard

router = Router(name="start")

START_TEXT = (
    "Мы предоставляем торговые сигналы по стратегии объёмов. "
    "Доступ получают пользователи, зарегистрированные у нашего партнёра InTradeBar."
)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Приветствие и главное меню."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "main")

    await message.answer(
        START_TEXT,
        reply_markup=get_main_menu_keyboard(),
    )


@router.message(F.text.casefold() == "получить доступ")
async def handle_get_access(message: Message) -> None:
    """Обработка нажатия кнопки «Получить доступ»."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "choose_account_status")

    await message.answer(
        "У вас уже есть аккаунт в InTradeBar?",
        reply_markup=get_account_status_keyboard(),
    )


@router.message(F.text.casefold() == "связаться с поддержкой")
async def handle_support(message: Message) -> None:
    """Обработка нажатия кнопки «Связаться с поддержкой»."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "awaiting_support_message")

    await message.answer("Напишите сообщение в свободной форме.")
