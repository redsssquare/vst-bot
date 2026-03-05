"""Обработчики команды /start и главного меню."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import state_manager
from keyboards import get_account_status_keyboard, get_main_menu_keyboard

router = Router(name="start")

START_TEXT = (
    "Neuro Option — система готовых торговых решений на основе анализа объёмов.\n\n"
    "Вы получаете:\n\n"
    "📍 готовые точки входа\n"
    "📊 структурированные сигналы\n"
    "🔄 регулярные обновления\n\n"
    "Чтобы продолжить — нажмите «Получить доступ»."
)

GET_ACCESS_SCREEN_TEXT = (
    "Мы работаем с брокером **Intrade Bar**.\n\n"
    "⚙️ Алгоритм системы настроен под эту площадку.\n\n"
    "У вас уже есть аккаунт?"
)
SUPPORT_WAIT_TEXT = "Напишите ваше сообщение — мы ответим в ближайшее время."


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    """Приветствие и главное меню."""
    user_id = message.from_user.id if message.from_user else 0
    state_manager.set_step(user_id, "main")

    await message.answer(
        START_TEXT,
        reply_markup=get_main_menu_keyboard(),
    )


@router.callback_query(F.data == "main:get_access")
async def handle_get_access(callback: CallbackQuery) -> None:
    """Обработка нажатия кнопки «Получить доступ»."""
    user_id = callback.from_user.id if callback.from_user else 0
    state_manager.set_step(user_id, "choose_account_status")

    await callback.message.answer(
        GET_ACCESS_SCREEN_TEXT,
        reply_markup=get_account_status_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "main:support")
async def handle_support(callback: CallbackQuery) -> None:
    """Обработка нажатия кнопки «Связаться с поддержкой»."""
    user_id = callback.from_user.id if callback.from_user else 0
    state_manager.set_step(user_id, "awaiting_support_message")

    await callback.message.answer(SUPPORT_WAIT_TEXT)
    await callback.answer()
